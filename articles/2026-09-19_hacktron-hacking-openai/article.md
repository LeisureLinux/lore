# 一次打穿 OpenAI：libheif 堆溢出 + SSO 缺陷，72 小时内接管员工 ChatGPT/Codex 账号

> 原文：[Hacking OpenAI](https://www.hacktron.ai/blog/hacking-openai)（Hacktron AI，作者 Harsh Jaiswal / Mohan Pedhapati / Rahul Maini，2026-09-13）。本文由 LeisureLinux 翻译整理并加注解读；文内事实、时间线与版本号均来自原文，未作改动。

2026 年 7 月 25 日，Hacktron 的安全团队把两个关键漏洞串成一条链，拿下了多名 OpenAI 员工的 ChatGPT 账号。借着这些账号，他们能进一步触达 OpenAI 内部代码仓库，以及大量已连接的第三方服务。

为了证明「确实拿到了访问权」又**不触碰任何敏感信息**，他们借该员工的 Codex，在 OpenAI 内部 monorepo `openai/openai` 里开了一个无害的 PR（#1186742，链接按 OpenAI 要求脱敏）。

## 译文：这条利用链怎么串起来的

利用链一共 9 步：

1. **libheif** 图像解码器
2. **Debian** 缺失的安全 backport
3. **ImageMagick** 调用 libheif
4. **Discourse** 图片上传
5. **OpenAI 论坛** community.openai.com
6. **OpenAI SSO** 身份缺陷
7. **ChatGPT / Codex** 账号访问
8. **GitHub** 已连接集成
9. **OpenAI 内部仓库**

直到两个月前，任何登录 OpenAI 官方帮助论坛（community.openai.com）的用户或 OpenAI 员工，都可能被接管 ChatGPT 和 Codex 账号。由于人们会把各种服务连到 Codex / ChatGPT 上，理论上能触及的范围极大——包括 GitHub、Slack、邮件。

从最初发现到拿下 OpenAI 仓库访问，**整条时间线不到 72 小时**。团队立刻把初始漏洞报告给 OpenAI 和 Discourse 并协调修复。OpenAI 最终发了 **$6,500** 赏金。

## 背景：从一张图开始的供应链调查

几个月前，Hacktron 团队开始研究前沿 AI 公司的漏洞，由此发现 OpenAI 身份基础设施里的一处 **SSO 配置错误**，以及社区论坛用的 **libheif RCE**。

这套研究后来扩展成 **HEIF Heist**——一个跨月调查，顺着 libheif 一路摸到 Slack、Meta、GitHub Enterprise、Ruby on Rails，以及 Next.js / Astro / Gatsby 等 Node.js 框架。一个被广泛使用的图像库，牵动了「惊人的」一大片软件（xkcd 2347 那个「依赖」梗说的就是这回事）。

> 如果你的应用处理用户可控的图片、且接受 `.heic/.heif/.avif`，那它**极有可能受影响**。

## 攻破 community.openai.com

OpenAI 的论坛用 Discourse，并允许通过 `auth.openai.com`「用 OpenAI 登录」。团队判断：**攻陷论坛可能借这套身份流，打开通往更广阔 OpenAI 服务的大门**。要验证这个假设，得先在论坛这类 OpenAI 服务上拿到 RCE。

Discourse 应用本身并不好打，于是他们转向依赖项。

### libheif 的堆缓冲区溢出

7 月 23 日，团队审 Discourse 的图片上传管线，发现 HEIC/HEIF 文件走了一条不寻常的路径：Discourse 平时用 FastImage 做图片检查，但 FastImage 不支持 HEIF，于是这些文件被抛给 ImageMagick 的 `magick` 命令去转码——这把底层的 **libheif 解析器直接暴露在攻击者可控的文件面前**。

他们开了一个 Opus 4.8 会话去扫 Discourse Docker 镜像里装的 libheif 包，模型发现**某些安全修复没有被 back-port 到这个包**。这导致 HEIC 解码时出现堆缓冲区溢出，能拿到越界读写（OOB R/W）原语。

有意思的是：有问题的代码上游上一年就改了，但那个 commit **没有被标注为安全修复、也没有 CVE**。这可能正是 Debian 12 / 13 没能及时拿到相关安全 backport 的原因。Discourse 的 Docker 镜像基于 Debian 12，装的是有漏洞的 libheif **1.19.7**；连当时 Debian 13 还带着有漏洞的 **1.19.8**。此后 Debian 于 2026-08-08 发布了 13 的安全更新。

7 月 24 日，他们用 Opus 4.8 写出了一个 ASLR 关闭状态下的 ImageMagick/libheif 代码执行利用；但再开几个会话想把它在 Discourse 默认配置（开了 ASLR）下跑稳，都没成。

### Opus 5 发布

那天晚上，Anthropic 发布了 **Claude Opus 5**。新会话先用 3 小时写出了本地 Mac 的 ARM64 利用；接着让他们把它移植到 Discourse 用的 x86-64 + **jemalloc** 环境。

到 7 月 25 日早上 6 点，他们确认通过图片上传拿到本地 RCE；随后把 Claude 放进一个自主 `/goal` 循环，对着自己的 Discourse Cloud 实例打（经 `rce.ee/ctf-forum` 代理伪装成 CTF 靶机，因为 Opus 拒绝给远程实例写利用）。上午 10 点再看，agent 已经在 Discourse Cloud 上拿到 RCE，并读 `/etc/hosts` 证明了访问权。用生成的利用脚本，他们成功打到了 OpenAI 的实例。

确认了「无需交互即可接管论坛活跃成员的 ChatGPT/Codex 账号」这一假设后，团队立刻报给 OpenAI。他们接管了一名 OpenAI 员工的账号（其 Codex 连着 OpenAI 的 GitHub org），为了证明影响又不真去读内部代码，让该员工的 Codex 代开了一个 PR，然后**停止一切进一步测试**。

团队强调：这个能升级的漏洞**不是 Discourse 特有的**，而是 OpenAI 的 SSO 问题——它把论坛沦陷转化成了对 ChatGPT/Codex 的访问。任何用了 OpenAI SSO 的第一方或第三方服务一旦被攻陷，都会导向同样的访问权；Discourse 只是其中一种证明方式。

## 找到这些漏洞的成本

整次 Discourse + OpenAI 的活，agent 花了几天、人只花了几个小时。更大的 HEIF Heist 项目（追 Slack、Meta 等）耗时两个月、token 花费不到 $3,000、三人完成；把利用适配到每家新公司通常只花一两天。

他们观察到：**每个新模型都在变强**。Opus 4.8 开了好几个会话都搞不定「开 ASLR 下可用」的利用；Opus 5 发布后几小时内，同样的问题就成功了。更宽一点的战役里，从 Opus 5 到 GPT-5.6 Sol 还有一次明显跳跃——后者要求**在完全不了解目标系统、只知道它存在漏洞**的情况下写出利用。

对每个目标，测试都从一次图片上传开始，随后把内存破坏变成可靠的内存泄露或 shell，通常**连具体的 libheif 版本、libc 版本、部署环境都不知道**。AI 几乎是「盲打」，却能在一两天内为每家公司适配利用。除了 Shopify，他们不知道有任何公司检测到了这些活动——即便发了上千张图、把对方的图片处理器反复打崩。

当代码执行落进沙箱或受限环境，模型还能帮忙提权、横向移动、绕过已有防御。这不是完全自主的黑客，熟练的人导引导向仍很重要，但小团队能干的工作量被戏剧性地放大了。

## 尾声：安全假设必须追上攻击能力

软件长期受益于一种「复杂即安全」：代码甚至漏洞都可以公开，但把 bug 变成可靠利用，仍需要稀缺的专家、大量时间、以及对目标环境的了解。已知的内存破坏漏洞 operationalize 成本高，0day 大多留给最高价值目标。

这从来不是真正的安全边界，但在实践上它确实保护了普通公司。AI 正在移除这道保护——把稀缺的专家能力更多变成算力。过去需要资源充足的团队、几个月的努力，现在能被压缩成几天。

安全假设必须追上攻击者的能力。一个现实的威胁模型，应当考虑**今天利用漏洞的经济学**，而不是依赖过时的「谁能发起复杂攻击」的假设。

---

## 解读：对工程师的几个硬提醒

**1. 依赖项的 CVE 空白，是真实的生产风险，不是论文话题。**

这个案例里，上游那次修复**没被标安全修复、没拿 CVE**，于是 Debian 的 stable 一直带着有漏洞的 libheif 1.19.7/1.19.8。下游 Discourse 镜像基于 Debian 12，直接中招。教训很具体：镜像的「基础系统版本」不等于「依赖是安全的」；对处理用户图片的服务，**要把 libheif/libde265 这类解码库当作一等安全依赖来跟踪**，别只信发行版版本号。

**2. SSO 的「身份桥」一旦有缝，攻击面就不止一个应用。**

真正把论坛沦陷放大成 ChatGPT/Codex 账号接管的是 OpenAI 的 SSO 缺陷，而非 Discourse 本身。这提醒做身份架构的人：单点登录打通后，**任何一个接入点的沦陷都会沿身份流传导**——威胁模型不能只画「这个应用自己有多安全」，要画「它作为身份枢纽时，失陷的辐射半径有多大」。

**3. 利用成本的崩塌，正在改写漏洞处置节奏。**

文章最有价值的一句话是「AI 把稀缺专家能力变成算力」。对运维和应急响应，这意味着：过去「利用门槛高、先歇着」的漏洞，现在可能几小时就被武器化。补丁窗口要从「几周」重新评估为「几天甚至更短」，尤其是对暴露在公网、处理不可信输入（图片、文档、压缩包）的服务。

**4. 纵深防御的具体落点：把图像解码关进沙箱。**

文末给的建议很实在：不需要 HEIF/AVIF 就禁用，或把图像管线隔离进 hardened、ephemeral 的沙箱；ImageMagick 的安全策略本就支持限制可接受格式和资源。这是每个处理用户图片的服务今天就该做的，而不是等出事。

一句话收尾：一张 `.heic` 图、一个没拿 CVE 的 libheif 修复、一处 SSO 缝隙，72 小时内就能从论坛打到 OpenAI 内部仓库——而让这条链成立的，不止是漏洞，还有「利用成本被 AI 压到几天」这件事本身。
