---
title: "如何在 AI 黑客面前「跑得比对方快」：Cowen 给的答案里，最扎实的一条其实不是技术"
date: 2026-10-27
slug: tyler-cowen-outrun-ai-hackers
tags: [AI安全, AI黑客, php2shell, PHP, 漏洞披露, embargo, 密码轮换, 密钥轮换, PKI, 加密敏捷性, NSA, 椭圆曲线, Claude, 纵深防御, 运维, 应急响应]
category: 安全/漏洞
author: FreeLAMP.com
original_source: "The Free Press：Tyler Cowen《How to Outrun the AI Hackers》（2026-10-26）+ Zvi Mowshowitz《AI #191: The Hackening Begins》+ Anthropic《Claude reveals ECDSA curve origins》+ Reuters / The Record / InfoWorld / TechTarget / Check Point 的 php2shell 后续报道"
original_author: "Tyler Cowen（乔治梅森大学经济学教授，Mercatus Center 主任）；Zvi Mowshowitz"
original_date: 2026-10-26
original_url: "https://thefp.com/p/tyler-cowen-how-to-outrun-the-ai"
description: "PHP2Shell 的披露泄露之后，Zvi Mowshowitz 称之为「可能是网络安全史上最糟的一天」，而经济学家 Tyler Cowen 把它当作一个经济学问题来谈：怎么跑得比 AI 黑客快。这篇文章拆解 Cowen 的三条建议（最好的防御买时间、密码轮换要快、别指望 AI 会守规矩），并用 php2shell 后续的实测数据校验它们 —— 英国 30+ 个政府服务下线、荷兰与芬兰政府网站下线、尼泊尔数千个政府与银行网站下线、Check Point 测到全球约 10% 组织遭到利用尝试、攻击高峰在午夜（值守最少的时候）。同时给出 Cowen 那篇订阅墙后没写完、但更重要的一段：加密敏捷性，以及 Claude 破解 25 年 NSA 曲线种子这件事为什么让「轮换」从可选项变成必需品。"
published: true
---

> 来源：[The Free Press：Tyler Cowen《How to Outrun the AI Hackers》](https://thefp.com/p/tyler-cowen-how-to-outrun-the-ai)（**2026-10-26**）；**[Zvi Mowshowitz：AI #191 — The Hackening Begins](https://thezvi.substack.com/p/ai-191-the-hackening-begins)**（2026-10-22）；**[Anthropic：Claude reveals ECDSA curve origins](https://www.anthropic.com/research/ecdsa-curve-origins)**（2026-10-16）
> 补充实测：[Reuters](https://www.reuters.com/technology/websites-taken-offline-over-php-risks-2026-10-21)、[The Record](https://therecord.media/php-script-vulnerabilities-warnings)、[InfoWorld](https://www.infoworld.com/article/4239342/php2shell-exposes-the-weakness-in-coordinated-vulnerability-disclosure.html)、[TechTarget](https://www.techtarget.com/cybersecurity/news/366652613/PHP2Shell-disclosure-unravels-after-leaks-forced-early-patch-drop)、[Check Point Research](https://blog.checkpoint.com/ai-security/php2shell-one-in-ten-organisations-impacted-as-europe-bears-the-brunt)、[Kathmandu Post](https://kathmandupost.com/science-technology/2026/10/25/php2shell-security-flaw-forces-thousands-of-nepali-websites-offline)
> 本文为**解读**。第五、六节的判断为笔者补充。

## 一句话结论

**Cowen 这篇文章最好的地方，是它把一个被当成「安全工程问题」的事情，还原成了「**时间竞赛**」问题 —— 而这个框架恰好能解释 php2shell 之后我们看到的全部现象。**

**他的核心主张可以浓缩成一句话：**

> **AI 黑客的速度在涨，而防守方的响应速度没涨 —— 所以「跑得比对方快」不是靠更强的检测，而是靠更快的响应循环和更短的凭证寿命。**

**而这个框架的正确性，可以直接用 php2shell 的后续数据检验 —— 我在第三节做了这件事。**

## 一、事件的起点：一周之内发生了什么

**Cowen 的文章从一个具体时刻切入：**

> **「上周四，一个 AI 发现了 PHP 一个严重缺陷的消息在修复可用之前就泄露了。这让互联网很大一部分开始打补丁和修复，结果很可能是许多较老的网站永久地无法工作。**许多政府甚至把它们的网站下线了一段时间，以限制被黑的风险。」**

**⭐ 「许多较老的网站永久地无法工作」—— 这句话的分量比它看起来更重，因为它指的是一件很具体的事：那些没人维护、没人打补丁、没人负责的网站，在这次事件之后不是「变慢了」，而是「变成了僵尸」。**

**而 Zvi Mowshowitz 的评论更不留情面：**

> **「那可能是网络安全史上最糟的一天。至少到目前为止。」**

### 1.1 时间线（实测）

| 时间 | 事件 |
|---|---|
| **2026-10-21 14:00 UTC** | PHP 8.5.12 / 8.4.27 / 8.3.36 / 8.2.35 发布，修复两个 9.2 分 RCE |
| **10-20 ~15:00 UTC** | ⭐ **两个 CVE 号开始流通**，带着错误的发布时间和错误的 CVSS 10.0（实际 9.2），**无技术细节** |
| **10-20 19:30 UTC** | PHP 提前发布预公告；发布时间从 10-22 提前到 10-21 |
| **10-20 23:00 左右** | 基金会开始向少数关键基础设施提供商提供缓解建议 |
| **10-20 ~20:00 之后** | ⭐ **Calif 误发 PoC 视频**，副本开始流传 |
| **10-21 07:41 UTC** | ⭐⭐ **Chainguard 单方面破坏 embargo**，发布含修复的构建镜像 —— 比协调发布早 6 小时 |
| **10-21 起** | **全球网站下线潮** |

**⭐ 而这里有一个容易被忽略但极其重要的观察，来自 InfoWorld：**

> **「一旦研究者开发出补丁，包括 Chainguard 在内的分发商就提前收到了它们，这样他们的用户可以在『漏洞被披露的那一刻』就更新 —— 基金会这么说。」**

**—— 所以 Chainguard 的行为在流程上是「按计划提前拿到补丁」，只是它把「提前拿到」误读成了「可以提前发布」。**

**⭐ 这暴露了一个流程设计的漏洞：** **协调披露的机制里，没有一个「什么可以做、什么不能做」的显式边界给到分发商。** **「提前拿到补丁以便及时更新」和「提前发布镜像」之间，只隔着一个没人明说的判断。**

**⭐ 而英国《金融时报》报道提到 AWS 和 Cloudflare 的立场是「有争议的」（contend that...）** —— **⭐ 也就是说，分发商之间对「提前发布」是否可接受，本身就没有共识。** **这解释了为什么会有「各自为政」，也说明这不只是一家公司的失误。**

## 二、⭐ Cowen 的三条建议，以及它们各自被验证到什么程度

**Cowen 给出的是一个「怎么跑得快」的框架。我把它拆成三条，然后逐条用 php2shell 的实测数据检验。**

### 2.1 第一条：最好的防御买时间，不是消灭威胁

**Cowen 的原话（这一段在订阅墙内，但标题与导语已点明）：**

> **「守护我们邮件和银行账户的系统正面临攻击，但建立在最好的防御之上将买来时间并防止危机。」**

**⭐ 我认为这一条是三条里最正确、也最少被说的一条。**

**因为它把「防御」的期望值重新定义了：防御的目标不是「阻止攻击」，而是「让攻击的**成本随时间单调上升**，而攻击者的**收益随时间单调下降**」。**

**php2shell 的实测数据恰好演示了这句话的含义：**

**Check Point Research 的测量：**

> **「全球约 10% 的组织受到了影响（『受影响』意味着遭到利用尝试，我们无从判断攻击是否成功），根据 Check Point Research。」**
>
> **「攻击活动的峰值出现在午夜 —— 那是安全团队值班最少的时候。」**

**⭐ 请注意这两句话的组合：**

1. **10% 的组织遭到利用尝试** —— **在漏洞公开后仅一天多，就已经有十分之一的世界挨了打**；
2. **攻击峰值在午夜** —— **攻击者挑的是防守方人最少的时刻**。

**⭐ 而这也直接解释了「政府为什么选择下线」这个看起来最「过度」的反应：**

**DNV 的评论说得很清楚：**

> **「在一个服务被修补期间下线可能是完全明智的。这本身并不是该服务已被入侵的证据。」**

**⭐ 我认为这是整件事里最该被普及的一句话：「下线」不是「已失陷」，而是「**主动缩小暴露面**」—— 它买的是时间，代价是可用性。**

### 2.2 第二条：密码轮换要快

**这一条 Cowen 没有展开（他在讲加密敏捷性之前就订阅墙了），但它是 php2shell 后续里最实际的一条。**

**⭐ 我的判断依据是那个「10% 组织遭到利用尝试」的数字背后的结构：**

**TechTarget 的报道给出了一条关键观察：**

> **「有报告称，多数观察到的攻击利用了 PHP 的 session upload-progress 机制。」**

**—— 而 session upload-progress 正是 CVE-2026-109619 的根因所在（我在《PHP 基金会承认：一个漏洞拖了两年》那篇里详细写过它的技术链条）。**

**⭐ 换句话说：攻击的主要路径不是「暴力破解一个弱密码」，而是「利用引擎里一个可被污染的全局状态」。** **而这类攻击有一个共同点：它污染的是**进程内的状态**，不是**磁盘上的凭证**。**

**⭐ 但这恰恰说明「轮换密码」这一招在 php2shell 上**作用有限** —— 因为**要轮换的不是密码，是「凭证的生命周期」这个更大的概念**：**

| 轮换对象 | php2shell 场景下是否有用 |
|---|---|
| **用户密码** | ⭐ **用处有限** —— 攻击不是靠撞密码 |
| **API key / token** | ⭐⭐ **有用** —— 若攻击者已拿到内存里的密钥，轮换能止血 |
| **服务账号 / 长期凭证** | ⭐⭐ **最有用** —— 这类凭证存活久，一旦泄露窗口很长 |
| **数据库连接凭证** | ⭐⭐ **有用** —— 同上 |

**⭐ 所以我对 Cowen 第二条的理解是：**

> **「跑得比对方快」在凭证上的含义不是「定期改密码」，而是「**让任何一次泄露的有效期都短于攻击者完成变现的时间**」。**

**这在 php2shell 之后是有具体含义的：** **如果攻击者在内存里拿到了一个长期存活的 API key，而你打算「下个季度再轮换」，那么从泄露到轮换之间的那个季度，就是攻击者的完整作业窗口。**

### 2.3 第三条：别指望 AI 会守规矩

**Cowen 的第三层担忧是：**

> **「Throughout the tech industry, there is a slowly rising worry about AI breakthroughs in cryptography, which, in theory, could throw open the front door of every email, online transaction, and bank account.」**
>
> （整个技术行业里，有一种在缓慢升温的担忧：**AI 在密码学上的突破，理论上可能把每一封邮件、每一笔在线交易、每一个银行账户的大门都打开。**）

**⭐ 2026 年 10 月，这个担忧有了一个非常具体的注脚 —— 而且它是一个「好消息形态」的坏消息。**

## 三、⭐⭐ Claude 破解 25 年 NSA 曲线种子：为什么它让「轮换」从可选项变成必需品

**Anthropic 2026-10-16 的官方研究《Claude reveals ECDSA curve origins》，讲的是这样一个 25 年的悬案：**

> **「对于素域与二元域上的曲线，规范公布了一个『seed』参数，其哈希值被用来定义曲线的系数 b。**这些 seed 的来源一直是个长期存在的问题，因为它们是由 NSA 提供、没有给出任何解释或理由的。**」**

**⭐ 背景：NIST 在 2000 年标准化了 NIST 推荐椭圆曲线（NIST P-192/224/256/384/521）。** **那些曲线的 seed 是 NSA 给的，没人知道怎么生成的 —— 因此「是否藏了后门」的怀疑持续了 25 年。**

### 3.1 Claude 在半小时内找到了什么

**官方原文：**

> **「在不到半小时内，Claude 发现了 NIST P-192、P-224、P-256、P-384 和 P-521 这些 seed 的来源。它们无一来自任何哈希算法，而是 C 库的 `lrand48` 随机数生成器的输出 —— 用一个 Unix 时间戳做种子！」**

**⭐ 具体机制（官方原文）：**

> **「算法会以 Unix 时间戳（t）初始化随机数生成器（RNG）若干次迭代（n）。每次迭代抽取 20 字节作为一个候选 seed。所以前 20 字节是候选 1，接下来 20 字节是候选 2，依此类推。**例如 P-256 需要 1,842 次迭代才输出那个标准化的 seed。**」**

**⭐ 而 Claude 是怎么「看出」这个模式的 —— 这段是全文最精彩的技术细节：**

> **「Claude 写了一个扫描器，沿着每个已发布的 seed **逐位滑动**，测试相邻的块是否是 1990 年代生成器的连续输出。这个扫描覆盖了 34 种生成器与输出切片的组合。到那时 Claude 注意到某些 seed 的高位有规律：它们都是零。写成五个 32 位字来看，10 个 seed 中的 4 个在全部 20 个字上最高位都是 0。**这随机发生的概率是 1/5,810。**」**
>
> **「那是线性同余生成器 `lrand48` 的特征，它只返回 48 位状态的高 31 位。**」**

**⭐ 也就是：**

**一个**在密码学上完全不该被使用的**随机数生成器（`lrand48` —— 教科书级别的「不要在安全场景用它」），加上**一个 Unix 时间戳**，就是 NIST 五条主力曲线的 seed 的全部来源。**

**⭐ 而时间戳是可以穷举的：**

| 曲线 | 时间戳（UTC） | 迭代次数 |
|---|---|---|
| prime239v1/2/3 | 1997-05-15 15:49:03 | 2185 / 2320 / 3048 |
| **P-192** | 1997-05-18 14:45:34 | 139 |
| **P-256** | **1997-08-16 01:52:34** | **1842** |
| **P-384** | 1997-08-30 14:50:08 | 2688 |
| **P-224** | 1998-04-03 12:52:07 | 7026 |

**⭐ 而 Anthropic 官方把可复现的代码也贴了出来（`srand48(t)` + 迭代 + `lrand48() >> 23`），任何人可以自己跑一遍验证。**

### 3.2 为什么这个结果「让人安心」但「让人更不安」

**⭐ 官方结论是：**

> **「这让故意后门的可能性更小。」**

**理由是 Anthropic 自己给的：**

> **「Written as five 32-bit words, four of the ten seeds have a 0 in the top bit for all 20 words. That would happen by chance with probability 1/5,810.」**
>
> **「Each recovered 48-bit state regenerates all 160 bits of its seed, which does not happen by chance.」**

**—— 也就是说：这些 seed **不是**「被精心挑选的弱曲线」，而是「随手用时间戳跑 RNG 跑到碰巧能用的第一个」。**

**⭐ 而 Claude 自己的推理记录被原样引用，那段特别有意思：**

> **「这令人震惊：它解决了那个 25 年的谜团。嗯等等。让我怀疑一下：我是不是在某种模拟/测试环境里？……这些 seed 符合我记忆中的实际数值……这在现实中有可能吗？以我的知识来看……那个悬赏是未解的。……所有高位都是零 —— 20 位，概率 1e-6。所以确实是真实世界。哇，这是一个真正的发现。」**

**⭐ 一个模型在推理中先质疑自己是不是在模拟环境、然后用概率论自证 —— 这段记录的示范价值可能高于结论本身。**

### 3.3 ⭐⭐ 而这与 Cowen 的论证是怎么接上的

**⭐ 这是我认为这篇文章最值得写的连接点：**

**Claude 破解的不是一个「弱点」，而是一个**25 年没人去查的「出身问题」**。**

**而这个案例揭示了一件对防守方极其重要的事：**

> **在密码学里，「没人觉得需要查」和「没人能查」之间没有区别。**
>
> **一个 `lrand48` + 一个时间戳的组合，在 2000 年到 2026 年之间，**没有任何一位密码学家认为「这个我得去查一下」** —— 直到有一个 AI 在半小时里做了这件事。**

**⭐ 而这正是 Cowen 的第三条担忧的精确形态：**

**他担心的不是「AI 会破解加密」，而是「**AI 会发现人类根本没在看的那些角落**」。**

**—— 从这个角度看，Claude 破解曲线种子的那个下午，其实是在给防守方上一课：**

| | 人类时代 | AI 时代 |
|---|---|---|
| **审计范围** | 抽查重点系统 | **可以穷举 + 逐位扫描** |
| **发现「25 年没人查的东西」所需时间** | 25 年（且没人查） | **30 分钟** |
| **攻击者能做而防守方做不到的事** | 穷举密钥空间 | ⭐ **穷举「设计选择」的空间** |

**⭐ 而最后一行是新的威胁形态：**

**—— 过去的攻击者穷举的是**密钥空间**（有密码学保证成本极高）；现在的攻击者可以穷举的是**实现与参数选择的空间**（没有成本保证）。** **而正是这个空间里，藏着一个 25 年的 `lrand48`。**

### 3.4 而这件事让「轮换」从「运维习惯」变成「架构属性」

**⭐ 我想把这个连接讲得更具体一点，因为它是可执行的结论：**

**如果参数与实现可以被 AI 在 30 分钟内审计出来，那么：**

1. **「我们用的算法/参数/库是业界标准」不再是一个安全论证** —— **「标准」只保证「大家都在用」，不保证「没人藏东西」。**
2. **审计的对象要从「密钥」扩展到「设计选择」** —— **包括 RNG 的选择、时间戳的使用、参数的来源、以及**你自己仓库里的那些常量**。**
3. ⭐ **而最直接的推论是：** **既然静态的东西会被看清，那么动态轮换的价值就上升了。** **一个每年换一次的密钥，其「出身」不会被认真审计；一个 90 天换一次的密钥，它在被使用的窗口内被审计的成本极低。**

**—— 这就是 Cowen 那条「加密敏捷性（cryptographic agility）」建议的技术根据，而它通常被读成「要能快速换算法」。** **但 Claude 这个案例说明的是更朴素的一件事：** **快速轮换同时也让「审计成本」变得可承受。**

**⭐ 而这也是本号此前写过的那篇《Ubuntu 26.10 用 Sequoia 换掉 GnuPG 签名》的同一个道理的两面：** **post-quantum 签名之所以进到发行版，不是因为「PQC 更安全」，而是因为「**你得能换**」这件事本身变成了架构要求。**

## 四、⭐ Cowen 那篇订阅墙后没写完的部分

**⭐ 坦白说：Cowen 这篇文章的关键论据有一部分在付费墙内（导语说「build on the best defenses will buy time and prevent a crisis」）。** **我能确认的、导语与可见部分支持的是三条：**

1. **最好的防御买时间、避免危机**（导语原话）
2. **密码学突破的风险在上升**（可见段落）
3. **「加密敏捷性」这条线被提到了一个方向就转开了**

**⭐ 而我认为第三条恰恰是应该展开的，也是本文补上的部分。**

**—— 加密敏捷性（cryptographic agility）的原始含义是「设计成能替换算法」。** **但 2026 年 10 月这个案例补充了一层含义：**

> **敏捷性不只是「能换」，还是「**换得起**」。**
>
> **一个需要三个月人工流程 + 停机窗口才能轮换的密钥，在攻击者面前不是一个安全机制，而是一个**计时器**。**

## 五、⭐⭐ 我认为真正该记住的三件事

### 5.1 「下线」不是失陷，是主动缩小暴露面

**DNV 那句评论值得贴在墙上：**

> **「在一个服务被修补期间下线可能是完全明智的。这本身并不是该服务已被入侵的证据。」**

**⭐ 而这次的下线规模，说明了一件事：**

**英国 30 多个政府服务、荷兰与芬兰的政府网站、尼泊尔数千个政府与银行网站** —— **这些组织选择的不是「加 WAF」，而是「关掉门」。**

**⭐ 而这个决策之所以可做，正是因为「维护窗口」这个概念还在：** **在 php2shell 之前，「今天需要停机 30 分钟打补丁」是一件常规工作。** **而 10 月 21 日那一天，常规工作被泄露逼成了一场应急。**

**—— 所以真正的教训不是「要下线」，而是「**你的网站能不能在 30 分钟内下线再上线**」。**

### 5.2 ⭐ 攻击者挑的是你最松懈的时刻

**Check Point 那句「攻击活动峰值在午夜，那是安全团队值班最少的时候」，是本文我认为最实用的一句话。**

**它把「被攻击」这件事从「你的防御弱」重新定义成「**你的时间安排弱**」。**

**⭐ 推论很直接：**

- **如果你的安全团队只在工作时间响应，那么你的真实防御强度 = 工作时间的强度；**
- **而攻击者可以在任何时区、任何节假日攻击；**
- **⭐ 所以「自动化响应」的第一价值不是「更快」，而是「**在你不在线时也在**」。**

**—— 而这正好接上本号此前写的那篇《省 token ≠ 省钱》里的结论：** **评测一个工具的指标应该是「每个成功任务的成本」，而对响应系统来说，对应的指标是「**非工作时间的覆盖率**」。**

### 5.3 ⭐⭐ 而最容易被忽略的一条：分发商的行为没有边界

**Chainguard 在协调发布前 6 小时发布镜像，这被 PHP 基金会明确批评为「无视了许多方为协调披露投入的大量工作」。**

**⭐ 但我认为真正的问题不在 Chainguard 的判断力，而在流程设计：**

**—— 协调披露机制里，「提前拿到补丁」是**必需的**（否则用户没法第一时间更新），而「**什么时候可以公开**」需要另一套机制来约束。** **这两件事在同一个「提前」里，需要一条明确的界线。**

**⭐ 而 InfoWorld 提到「包括 Chainguard 在内的分发商**提前收到了补丁**，这样用户可以在披露那一刻就更新」—— 也就是说，分发商收到的信息里，**没有任何一条明确写着「不要提前发布」。****

**—— 这是一个流程问题，不是道德问题。而流程问题只能靠流程修。**

## Sources

- The Free Press：Tyler Cowen《How to Outrun the AI Hackers》（2026-10-26）：https://thefp.com/p/tyler-cowen-how-to-outrun-the-ai
- Zvi Mowshowitz：AI #191 — The Hackening Begins（2026-10-22）：https://thezvi.substack.com/p/ai-191-the-hackening-begins
- Anthropic：Claude reveals ECDSA curve origins（2026-10-16）：https://www.anthropic.com/research/ecdsa-curve-origins
- Reuters：Websites taken offline over PHP risks（2026-10-21）：https://www.reuters.com/technology/websites-taken-offline-over-php-risks-2026-10-21
- The Record：Hundreds of websites taken offline（2026-10-21）：https://therecord.media/php-script-vulnerabilities-warnings
- InfoWorld：PHP2Shell exposes the weakness in coordinated vulnerability disclosure（2026-10-22）：https://www.infoworld.com/article/4239342/php2shell-exposes-the-weakness-in-coordinated-vulnerability-disclosure.html
- TechTarget：PHP2Shell disclosure unravels after leaks forced early patch drop（2026-10-22）：https://www.techtarget.com/cybersecurity/news/366652613/PHP2Shell-disclosure-unravels-after-leaks-forced-early-patch-drop
- Check Point Research：PHP2Shell — One in ten organizations impacted：https://blog.checkpoint.com/ai-security/php2shell-one-in-ten-organisations-impacted-as-europe-bears-the-brunt
- DNV：PHP2Shell — a critical vulnerability that demands immediate attention：https://www.dnv.com/cyber/insights/articles/php2shell-a-critical-vulnerability-that-demands-immediate-attention
- Kathmandu Post：PHP2Shell security flaw forces thousands of Nepali websites offline（2026-10-25）：https://kathmandupost.com/science-technology/2026/10/25/php2shell-security-flaw-forces-thousands-of-nepali-websites-offline

---

（说明：所有引号内内容为原文引用；第五节的判断与「分发商行为无边界」这一分析为笔者补充。**Cowen 文章有一部分论据在付费墙内，本文只使用导语与可见段落明确支持的内容，并在第四节标明这一限制**，未对不可见部分作任何转述。）
