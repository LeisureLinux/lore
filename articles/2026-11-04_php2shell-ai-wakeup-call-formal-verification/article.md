---
title: "「40 年技术债要还了」：PHP2Shell 为什么被 IEEE Spectrum 称为 AI 安全的一次警钟"
date: 2026-11-04
slug: php2shell-ai-wakeup-call-formal-verification
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：IEEE Spectrum《The PHP2Shell Vulnerability Heralds Cybersecurity Hell》（Dina Genkina，2026-11-02）＋ Anthropic 官方《LLMs are making formal software verification feasible at a much larger scale》（2026-10-22，Frontier Red Team）＋ Calif Research《PHP2Shell by Calif Research》（Ryan Austin）＋ OpenAI《Patch the Planet》公告 ＋ PHP 官方 advisory 与 Wiz 研究"
original_date: 2026-11-02
original_url: "https://spectrum.ieee.org/ai-in-cybersecurity-php2shell-vulnerability"
description: "本文解读 IEEE Spectrum 2026-11-02 的《The PHP2Shell Vulnerability Heralds Cybersecurity Hell》，⭐ 并补上它提到的、但没展开的那条主线 —— **防守方一侧的 AI**。⭐ 三个受访者各说了半句：⭐ **Tolmo 的 Matt Suiche**：*\"all the legacy software that was written by humans over the last 40 years is being exposed… Now it is time for the technical debt to be paid off.\"* ⭐ **哥伦比亚大学 Suman Jana**：*\"It's just that it's a lot of very specific reasoning that is painful to do. And AI, I think, has done a very good job at that.\"* ⭐ **约翰霍普金斯 Matthew Green**（最不乐观）：*\"Nobody's going to fix this problem until something really bad happens… **PHP2Shell wasn't bad enough to be really bad.** So when something really happens, which is going to be maybe sometime in early 2027… then suddenly people will start doing this. We're going to fund everything.\"* ⭐ 而 Jana 提到的「防御侧的不对称」，⭐ 在 IEEE 那篇里被点出但没展开：⭐ 「找 bug 和修 bug 有一个根本的不对称」⭐ **—— 修的时候你必须确认攻击链的每一段都被关上、⭐ 且不破坏任何现有功能。⭐ **⭐ 本文把 Anthropic 10-22 那份 123 个库 / 239 个 fuzz 入口的形式化验证工作补上，⭐ 因为它正是「修的一侧」的最新答案：⭐ 把 fuzz 测试「翻译」成规范、⭐ 让 LLM 生成证明、⭐ 再由**外部**证明检查器（Rocq）机械核验，⭐ 而「唯一不由 LLM 做的，是证明检查器，因为有人得检查证明，因为 LLM 会幻觉」。⭐ 而 Anthropic 自己列的三条限制（⭐ 证明针对的是 musl + 单线程静态 RISC-V 二进制，⭐ 大多数人跑的是 x86/ARM + glibc；⭐ ASan 本身不检测所有内存安全 bug；⭐ 「形式化验证过」不等于「无 bug」，⭐ 因为证明检查器无法判断你的规范是否匹配现实）⭐ 才是这件事真正的边界。"
published: true
---

> **原文**：IEEE Spectrum《The PHP2Shell Vulnerability Heralds Cybersecurity Hell》（Dina Genkina，2026-11-02）
> 原文链接：<https://spectrum.ieee.org/ai-in-cybersecurity-php2shell-vulnerability>
> ⭐ **本文依据 IEEE 原文 ＋ Anthropic 2026-10-22 的官方研究文章原文 ＋ Calif Research 的原始披露 ＋ OpenAI 的 Patch the Planet 公告。**

## 一、⭐⭐ 先说清楚：这不是第四篇 PHP2Shell

⭐ **本号此前已写过六篇 PHP2Shell 相关的文章（⭐ 根因与发行版跟进、⭐ 纯 HTTP 的 ASLR 绕过、⭐ 空 webroot 的实验室、⭐ Wiz 的在野利用尝试、⭐ Fragnesia → 域控、⭐ 以及 AI 辅助攻击打域控），⭐ 所以这篇的定位必须说清楚。**

| 本号此前写的 | 覆盖 |
|---|---|
| ⭐ 根因与发行版跟进（10-21） | longjmp() 导致的请求状态提前发布、390 个文件的补丁、Debian/Ubuntu/Red Hat 跟进版本 |
| ⭐ 纯 HTTP 的 ASLR 绕过（10-23） | 无需任何反代头就能利用的那条路径 |
| ⭐ 空 webroot 实验室（10-23） | 漏洞可达性的实验室复现 |
| ⭐ Wiz 在野利用尝试（10-27） | 全球暴露面日降幅 67%、攻击者瓶颈是「worker 复用」 |
| ⭐ Fragnesia → 域控（10-30） | 内核提权串成单请求链、横向移动到域控 |
| ⭐ AI 辅助攻击打域控（10-30） | 攻击者工具箱里的 Claude Code / DeepSeek / Kimi |
| ⭐ **本文** | ⭐ **防守方一侧：AI 把「修 bug」这件事的成本降下来了，⭐ 以及为什么现在还轮不到你我** |

⭐ **⭐ 而 IEEE 这篇的价值恰恰在这里：⭐ **它问的不是「PHP2Shell 怎么被打的」，⭐ 而是「这件事对整个安全产业意味着什么」。⭐ **⭐**

## 二、⭐⭐⭐ 三个人，三句各说了一半的话

⭐ **⭐ IEEE 这篇的结构很妙：⭐ **它没有让一个专家说完整个故事，⭐ 而是让三个人各持一角，⭐ 而那三句话拼起来才是完整判断。**

### ⭐⭐ 第一句：Matt Suiche（Tolmo，AI 安全研究负责人）

> *"One of the things we're witnessing now is that **all the legacy software that was written by humans over the last 40 years is being exposed**… Now it is time for **the technical debt to be paid off**."*

⭐ **⭐ 请注意「being exposed」这个词的时态与被动语态：⭐ **不是「正在被攻击」，⭐ 而是「正在被暴露」。⭐ **⭐ 这两个说法的差别很大：**

- ⭐ **「被攻击」** —— ⭐ 攻击者已经用它干了坏事
- ⭐ **「被暴露」** —— ⭐ **它一直都在那儿，⭐ 只是现在被照出来了**

⭐ **⭐ 而「40 年技术债」这个说法更值得拆开：⭐ **PHP 诞生于 1994 年，⭐ 而 PHP2Shell 的根因（⭐ 用 longjmp() 处理内存耗尽导致请求状态提前发布）⭐ 是这门语言早期设计的一部分。⭐ **⭐ 也就是说，⭐ **这不是「某个版本引入了 bug」，⭐ 而是「三十年前的一个设计决定，⭐ 一直在那里」。⭐ **⭐**

⭐ **⭐ 而 IEEE 那篇里有一句补充，⭐ 我觉得是全文最具体的：**

> *"The Linux kernel — one of the most well-tested pieces of software today, deployed on billions of devices worldwide — **recently had over 1,000 vulnerabilities disclosed**."*

⭐ **⭐ 请把这个数字和「最被充分测试过的软件之一」放在一起：⭐ **一个被测试了三十年的内核，⭐ 在一年内公开了 1000+ 个漏洞。⭐ **⭐ 这就是「技术债」最冷的形态 —— ⭐ **不是「可能有 bug」，⭐ 而是「测试了三十年的地方，⭐ 依然有这么多」。**

### ⭐⭐ 第二句：Suman Jana（哥伦比亚大学计算机科学副教授）

> *"If you look at any at any point of time, there will be a bunch of bug reports that are waiting to be fixed, which are just crashes. **Most people don't take them very seriously.**"*

⭐ **⭐ 而这一段是全文对「为什么一个 OOM 崩溃会躺两年」最精准的解释：**

> *"**It's just that it's a lot of very specific reasoning that is painful to do.** And AI, I think, has done a very good job at that."*

⭐ **⭐ 请注意「很具体的推理」这个词：⭐ **把「PHP 在内存耗尽时用 longjmp() 提前发布未填完的请求状态」⭐ 变成一个可利用的 RCE，⭐ 需要的不���是「知道怎么写 exploit」，⭐ 而是「⭐ 精确推理出内存布局、⭐ 搞清哪几个字节在什么顺序下被覆盖才能拿到控制权」。⭐ **⭐**

⭐ **⭐ 而这是本号此前那篇《纯 HTTP 的 ASLR 绕过》讲过的东西的另一个说法：⭐ **⭐ 攻击链的瓶颈从来不是「找到漏洞」，⭐ 而是「把漏洞变成可利用」。⭐ **⭐**

### ⭐⭐ 第三句：Matthew Green（约翰霍普金斯大学信息安全研究所副教授）—— 最不乐观的那句

> *"**Nobody's going to fix this problem until something really bad happens.** And **PHP2Shell wasn't bad enough to be really bad.** So when something really happens, which is going to be maybe sometime in early 2027, something bad that normal people are upset by, then suddenly people will start doing this. **We're going to fund everything.**"*

⭐ **⭐⭐ 这一句是全文最刺耳的，⭐ 而我认为它也是最准的：**

⭐ **⭐ 请注意它的论证结构 —— ⭐ **不是「这个漏洞不够严重」，⭐ 而是「**这个漏洞不够严重到能让决策者动**」。⭐ **⭐**

⭐ **⭐ 而「PHP2Shell wasn't bad enough to be really bad」这句话有一个具体的对照：⭐ **IEEE 原文自己说了，⭐ 「包括 NASA、维基百科、白宫，⭐ 以及所有跑在 WordPress 或 Drupal 上的站点」⭐ **都处在风险中**—— ⭐ **而它被解掉了，⭐ 因为「漏洞是由网络安全研究者发现、⭐ 报告给了 PHP 基金会、⭐ 而补丁在坏演员拿到利用代码之前就发布了」。⭐ **⭐**

⭐ **⭐⭐ 而 Green 说的「something really bad」⭐ 大概是指：⭐ **⭐ 一次让普通人感到愤怒的事件 —— ⭐ **比如某个大医院、⭐ 某个银行、⭐ 某次选举的基础设施被勒索软件加密。⭐ **⭐**

⭐ **⭐ **而这正好接上了 IEEE 那篇引用的另一条评论（@eichin 在 HN 上的说法，我此前在 GitBook 那篇里引过）：⭐ **「应对这类事件曾经是『吃蔬菜』式的准备，⭐ 而在过去几个月里变成了『对我来说只是平常一天』」。⭐ **⭐**

## 三、⭐⭐⭐ 核心：找 bug 和修 bug 的「根本不对称」

⭐ **⭐ 这一点 IEEE 那篇只点了一句，⭐ 而我认为它是整篇文章的技术核心 —— ⭐ **而且它直接对应了 Anthropic 10-22 那份工作的意义。**

⭐ Jana 的原话：

> *"**There is a fundamental asymmetry in finding bugs and fixing bugs.** Because when you're fixing bugs you have to make sure that you know **all parts of that attack are closed**, and also that **you don't break any existing functionality**."*

⭐ **⭐⭐ 我想把这个不对称拆得更具体一点，⭐ 因为它是可量化的：**

| | ⭐ **找 bug** | ⭐ **修 bug** |
|---|---|---|
| ⭐ **成功判据** | ⭐ **找到一个崩溃输入** —— ⭐ **二值、可自动判定** | ⭐ **「所有攻击路径都关上了」⭐ **且「没有破坏现有功能」** —— ⭐ **无法用单个测试判定** |
| ⭐ **工作量** | ⭐ **可以并行、⭐ 可以暴力、⭐ 可以交给机器** | ⭐ **需要全局理解、⭐ 需要回归测试、⭐ 需要人来判断「够不够」** |
| ⭐ **失败形态** | ⭐ **「没找到」** —— ⭐ **明确、可量化** | ⭐ **「以为修好了」** —— ⭐ **沉默、⭐ 不可量化** |
| ⭐ **本例中** | ⭐ **Calif 用 GPT-5.6 Sol 在两周内从 2024 年的 OOM 报告里挖出了 RCE** | ⭐ **PHP 基金会 + OpenAI + Wiz + Cloudflare 团队，⭐ ⭐ **两个月**才修完** |

⭐ **⭐⭐ 而「修」这一侧的成本，⭐ IEEE 那篇给了一个具体的对照：⭐ **⭐ 「四个工程师，⭐ 花了两个月开发补丁」。⭐ **⭐**

⭐ **⭐⭐ 而我要指出这个不对称的一个隐蔽后果：⭐ **⭐ 「修复」这一侧，⭐ **至今没有出现一个「AI 能自动做」的证明。⭐ **⭐**

⭐ **⭐ 事实上，⭐ 情况正好相反 —— ⭐ **⭐ 攻击侧已经有了可复现的 AI 流水线（⭐ Calif 用 GPT-5.6 Sol、⭐ Wiz 用 Gemini 4 Argon 与 Wiz Atlas agent），⭐ **而防守侧还停留在「AI 帮我们找得更快，⭐ 但修复还是要人来做」。⭐ **⭐**

⭐ **⭐⭐ 而这正好是接下来那件事的背景。**

## 四、⭐⭐⭐⭐ 补上 IEEE 没展开的那半边：10-22 的形式化验证

⭐ **⭐⭐ IEEE 那篇在最后一段提了一句：⭐ **「Jana is also optimistic that formal verification tools to automate the patching side of the equation are also advancing quickly, including a new release from Anthropic on 22 October.」⭐ **⭐**

⭐ **⭐ 我把 Anthropic 那篇原文调出来看了，⭐ 而它比 IEEE 的转述有价值得多。⭐ **⭐**

### ⭐⭐ 官方原话

> *"Most software is riddled with bugs, **which AI can now easily find and exploit**. The standard defenses against cyberattacks are no longer sufficient: **we need ways to prove that code is free of bugs.**"*
>
> *"In a collaboration with **Theorem**, however, we show this is no longer the case: **LLMs can now produce formal proofs at large scale**, enabling new software development workflows that include proven security guarantees."*
>
> *"Using Claude, we proved security properties **at the assembly code level (RISC-V)** in over 100 real-world open-source software libraries. **To our knowledge, this represents the first large-scale effort to use AI to apply formal verification to production software at the assembly code level.**"*
>
> *"While writing the proofs, **Claude also discovered bugs that had eluded detection for years, despite trillions of test runs.**"*

⭐ **⭐⭐ 而这句「发现了尽管有万亿次测试运行也从未暴露的 bug」，⭐ **和 IEEE 那篇里 PHP2Shell 的形态是同一个：⭐ **一个被测试了无数遍的地方，⭐ 依然藏着只有在「证明」这个视角下才看得见的缺陷。⭐ **⭐**

### ⭐⭐⭐ 它的方法：把 fuzz 测试「翻译」成规范

⭐ **⭐ 这一段是整个工作里最漂亮的一步，⭐ 我详细说：**

⭐ **⭐ 传统的形式化验证困境在于「规格」（spec）难写：⭐ **一个 PNG 解码器可以清楚地写出「正确」是什么（⭐ 按 RFC 2083 解码），⭐ 但「一个文本编辑器或浏览器正确是什么意思」⭐ 就没有答案了。⭐ **⭐**

⭐ **⭐ 而 Anthropic 的解法绕开了这个问题：⭐ **它不去猜「正确」是什么，⭐ 而是把开发者已经写好的 fuzz 测试套件自动转成规范 —— ⭐ **编码的规则是「这个测试套件总是通过」。**

⭐ 原文：

> *"To address this for the code in the open-source libraries that we sought to prove, we take the approach of **automatically converting their preexisting compilable test suites into a spec** by encoding the rule '**this test suite always passes**', using a general model of what it means to execute any RISC-V-compiled binary on Linux."*
>
> *"**If Claude can prove this spec, the fuzz test on RISC-V becomes superfluous: fuzzing that entry point will never find any bugs.**"*

⭐ **⭐⭐ 请注意最后那句的力度：⭐ **不是「fuzz 测试更少发现 bug」，⭐ 而是「fuzz 测试永远不会再发现任何 bug」。⭐ **⭐**

⭐ **⭐⭐ 而这才是「找」和「修」之间那个不对称被真正填上的地方：**

```
 fuzz 测试（暴力、无保证）
        ↓  自动转成规范：「这个测试套件总是通过」
 形式化规范（在 RISC-V 汇编层面）
        ↓  LLM 生成证明
 机器可检查的证明（由外部证明检查器核验）
        ↓
 结论：对某个入口点，在给定假设下，崩溃不会发生
```

⭐ **⭐⭐ 而这里最关键的一环是「**外部**证明检查器」—— ⭐ **⭐ 这正是 Jana 在 IEEE 那篇里说的那句话的落点：**

> *"**The patch is LLM-generated, and then an LLM generates the proof that the patch is correct.** The only thing not done by an LLM is **the proof checker**, because **somebody has to check the proof, because LLMs hallucinate.** So, you want something that is **formal**."*

⭐ **⭐⭐ 请把这句话拆开：⭐ **⭐ 「LLM 生成证明」⭐ **不是「LLM 说它对」，⭐ 而是「LLM 产出一个可被机械核验的证明对象，⭐ 再由一个确定性的检查器去核验」。⭐ **⭐**

⭐ **⭐⭐ 而这一条恰好是形式化验证这门学科存在了一辈子的那个根本性质：⭐ **⭐ 「相信的不是写证明的人，⭐ 而是检查器」。⭐ **⭐**

### ⭐⭐ 规模与边界

⭐ **⭐ 具体的数字（据官方原文与附录）：**

| 项 | 数字 |
|---|---|
| ⭐ **库** | ⭐ **123 个开源库** |
| ⭐ **fuzz 入口点** | ⭐ **239 个**（⭐ **公开的只是子集：⭐ 「60 entry points in 25 libraries have proofs」**）|
| ⭐ **证明语言 / 规模** | ⭐ **Rocq**，⭐ 约 **1.8 亿行** |
| ⭐ **信任基** | ⭐ **RISC-V 与 Linux 进程模型、⭐ 定理陈述、⭐ 以及检查器本身** |
| ⭐ **覆盖范围** | ⭐ **123 个 Google OSS-Fuzz 库** |
| ⭐ **前提假设** | ⭐ **单线程、⭐ 静态链接、⭐ musl libc、⭐ RISC-V、⭐ Linux、⭐ 固定内存预算、⭐ 输入 < 64 MB** |

⭐ **⭐⭐ 而 Anthropic 自己列的三条限制，⭐ **我认为比成果列表更有价值**，⭐ 因为它们精确地划出了「这不等于什么」：**

> ⭐ **①** *"Our proofs are about single-threaded, static RISC-V binaries linked against musl libc. However, **most people run these libraries on x86 or ARM and dynamically link them against glibc.**"*
>
> ⭐ **②** *"**ASan doesn't detect all memory safety bugs**, and we didn't verify all the entry points for each library. Even if we had, **the whole library wouldn't be covered by verifying all entry points** (especially if there is dead code). Additionally, **real programs might misuse the library**, leading to memory corruption in the caller."*
>
> ⭐ **③** *"**'Formally verified' does not mean 'bug-free.'** Claude can write a proof showing that a compiled program's behavior satisfies the requirements of a formal spec (which is verified by an external proof checker). **However, a proof checker can't tell you whether your spec matches reality.**"*

⭐ **⭐⭐ 而第 ③ 条是这一整篇里最该被反复引用的一句：⭐ **「形式化验证过」不等于「没有 bug」。⭐ **⭐**

⭐ **⭐ **因为证明检查器只能验证「程序符合规范」，⭐ 而不能验证「规范符合现实」。⭐ **⭐ 而当被验证的代码里真的出现 bug 时，⭐ **原因一定是「规范」或「机器的假设语义」与现实不符 —— ⭐ **⭐ 而这其实是个好消息：⭐ **因为它把「剩下的 bug 在哪」这件事，⭐ 从「不知道」变成了「知道」。⭐ **⭐**

⭐ **⭐⭐ 而这与本号此前写的 CVE-2026-98432 那篇形成了一个有意思的对照：⭐ **⭐ 那条漏洞的根因是「RCU 读者还在读、⭐ 而析构函数用普通 kfree() 释放了对象」—— ⭐ **⭐ 而这类「内存序/生命周期」缺陷，⭐ **恰恰是 fuzz 测试最难覆盖、⭐ 而形式化证明最擅长的那一类。⭐ **⭐**

## 五、⭐⭐⭐⭐ 那么，回到「40 年技术债」：这条线到底怎么收？

⭐ **⭐ 我把 IEEE 那篇、Anthropic 那篇、Calif 那篇和本号此前写的几篇拼起来，⭐ 试着给出一条完整的路径。**

### ⭐⭐ 阶段一：暴露（已发生）

⭐ **⭐ 这一阶段的工具是 AI agent，⭐ 而效果是压倒性的：**

| 谁 | 用什么 | 发现了什么 |
|---|---|---|
| ⭐ **Calif** | ⭐ **OpenAI 的 GPT-5.6 Sol**（⭐ 在 OpenAI「Patch the Planet」计划下） | ⭐ **CVE-2026-109618** |
| ⭐ **Wiz** | ⭐ **Wiz Atlas 安全 AI agent、⭐ Google 的 Gemini 4 Argon、⭐ 以及 GPT-5.6 Sol** | ⭐ **独立发现了两个漏洞**（⭐ 含 CVE-2026-109619）|
| ⭐ **Calif 自己**（⭐ 官方博客原话） | ⭐ —— | ⭐ *"We were not expecting to find anything critical — **everyone and every lab had already done extensive AI assisted audits of this target.** But, only a few days after starting t…"* |

⭐ **⭐⭐ 请特别注意最后那句：⭐ **⭐ 「我们本没指望找到什么严重的东西 —— ⭐ **因为所有人、每一个实验室都已经对这个目标做过大量 AI 辅助审计了。**」⭐ **⭐**

⭐ **⭐⭐ **这句话比任何数字都更能说明 2026 年的处境：⭐ **⭐ 当「AI 已经把所有能做的都做了一遍」成为常态，⭐ **而那个目标**仍然**藏着一个能打穿 NASA、维基百科和白宫的 RCE，⭐ **⭐ 那么「已经审过」这件事本身，⭐ **⭐ 就不再提供任何保证。⭐ **⭐**

### ⭐⭐ 阶段二：修（正在被 AI 改变）

⭐ **⭐ 而这一阶段的成本，⭐ 全部集中在 IEEE 那篇点出的那个「不对称」上：⭐ **两个月、四名工程师、⭐ 390 个文件（⭐ 本号此前的文章核对过这个数字）。**

⭐ **⭐ 而 Anthropic 的工作在做的，⭐ 是把这个「不对称」的防守侧成本曲线往下压。**

### ⭐⭐ 阶段三：⭐⭐⭐ 但真正的约束不是技术，是「钱从哪来」

⭐ **⭐⭐ 而这一层，⭐ IEEE 那篇反而是全文最清醒的。⭐ 它引了两句关键的话：**

⭐ **⭐ Suman Jana：**

> *"Maintaining open-source projects that don't have clear revenue streams despite being widely used is a long-standing challenge that **precedes AI hacking tools**. But those tools **make the issue more pressing than ever**."*
>
> *"One way to stay ahead of such issues going forward is to **empower the defenders with more money and access to frontier cybersecurity AI models**. 'These frontier labs are donating some of their token budgets to look into these bugs, which I think is great. **I think that should happen more, either through some concerted effort or through donations.**'"*

⭐ **⭐⭐ 请注意第一个转折句：⭐ **⭐ 「开源项目缺乏清晰收入来源、⭐ 尽管被广泛使用，⭐ 这是个长期挑战，⭐ **它早于 AI 攻击工具**」。⭐ **⭐**

⭐ **⭐⭐ 这句话极其重要，⭐ **因为它把因果关系摆正了：⭐ **⭐ 「技术债要还」这个结论本身，⭐ **是**旧**结论（⭐ 二十年来一直这么说）；⭐ **⭐ 而 AI 做的事是**把还债的账单提前送到你桌上**，⭐ **而不是让账单变新。⭐ **⭐**

⭐ **⭐⭐ 而 Jana 给的解法，⭐ 我认为也是全文最实际的一句：⭐ **⭐ 「让防守方拿到更多的钱、⭐ 以及前沿网络安全 AI 模型的可访问性。」⭐ **⭐**

⭐ **⭐⭐ 「前沿实验室正在捐出**一部分 token 预算**去查这些 bug，⭐ 我觉得这很好，⭐ **我认为这应该更多发生 —— 要么通过某种协同努力，⭐ 要么通过捐赠。**」⭐ **⭐**

⭐ **⭐⭐ 换句话说：⭐ **⭐ 「让防守方也能用上 GPT-5.6 Sol 这种级别的模型」，⭐ **本质上是**算力补贴**问题，⭐ **而不是模型能力问题。⭐ **⭐**

### ⭐⭐⭐⭐ 而 Green 那句冷话，⭐ 恰好是这个循环的启动条件

⭐ **⭐⭐ 我把 Green 的两句和 Jana 的两句放在一起，⭐ 会看到一个完整的循环：**

```
① AI 让攻击变便宜（Jana：AI 让「很具体的推理」不痛苦了）
        ↓
② AI 让防守也变便宜，但需要前沿模型和算力（Jana：应该捐 token 预算）
        ↓
③ 但防守方的钱在防守侧（Green：Nothing's going to fix this until something really bad happens）
        ↓
④ 所以要等一次「让普通人愤怒」的事件（Green：maybe sometime in early 2027）
        ↓
⑤ 然后资金才会到来（Green：then suddenly people will start doing this. We're going to fund everything）
```

⭐ **⭐⭐ 而这个循环的第 ④ 步，⭐ **是全文最冷、也最不该被跳过的一句：⭐ **⭐**

⭐ **⭐⭐ 「只有当发生了**足够糟**、⭐ **糟到让普通人感到愤怒**的事情，⭐ **人们才会开始修。」⭐ **⭐⭐**

⭐ **⭐⭐ 而这句话的结构，⭐ **和 Philip K. Dick 那句著名的「The living are getting stronger」⭐ 是一个形状 —— ⭐ **⭐ 它说的是同一件事：⭐ **⭐ 系统不会因为「正确」而改变，⭐ **只会因为「疼」而改变。⭐ **⭐**

⭐ **⭐⭐ 而 PHP2Shell 之所以没成为那个时刻，⭐ **IEEE 那篇自己给了答案：⭐ **「漏洞是被研究者发现的、⭐ 报告给了 PHP 基金会、⭐ 而补丁在坏演员拿到利用代码之前就发布了」⭐ —— ⭐ **⭐ 也就是说，⭐ **⭐ 「白帽子先找到」这件事救了它。⭐ **⭐**

⭐ **⭐⭐ 而 Jana 的收尾，⭐ 恰好是这件事的题眼：**

> *"**It's just who finds it. Hopefully, the white-hat hackers find it first, like this one.**"*

⭐ **⭐⭐ 而我要补一句：⭐ **⭐ 「谁先找到」这件事，⭐ **⭐ 在 2026 年已经不再是一个道德问题，⭐ **⭐ 而是一个**算力分配**问题。⭐ **⭐**

⭐ **⭐⭐ 因为现在：**

- ⭐ **⭐ 攻击方有前沿模型**（⭐ 虽然未必有 GPT-5.6 Sol 这个级别，⭐ 但有代理化的工具链）
- ⭐ **⭐ 防守方**（⭐ 开源维护者、⭐ 小型安全团队、⭐ 有资源的基础设施维护者）⭐ **往往连前沿模型都负担不起**
- ⭐ **⭐ 而前沿实验室捐 token 预算这件事，⭐ **⭐ **是「碰巧有人愿意」，⭐ 而不是「有制度保障」**

⭐ **⭐⭐ **所以真正的杠杆，⭐ 我认为不是「让 AI 更强」，⭐ 而是「**让防守方也能用上**」—— ⭐ **⭐ 这正是 Jana 那句「empower the defenders with more money and access to frontier cybersecurity AI models」的实质。⭐ **⭐**

## 六、⭐⭐⭐⭐ 一点观察：把这件事和本号此前的几条线并排看

⭐ **⭐ 这一节是我的判断，⭐ 但我认为它能把这一轮几条新闻串成一条线。**

⭐ **⭐ 过去两周里，⭐ 本号写的这几篇表面上毫不相干：**

| 篇 | 表面主题 | ⭐ **底层问题** |
|---|---|---|
| ⭐ **PHP2Shell（IEEE 篇）** | 一个漏洞的故事 | ⭐ **⭐ AI 让「找」变便宜，⭐ 而「修」的成本没同步下降** |
| ⭐ **Canonical 的新 SRU 策略** | 内核为什么开始每周发 | ⭐ **⭐ AI 让漏洞发现变自动化，⭐ 而修复产能是固定的** |
| ⭐ **FreeRDP 3.33 的 AI PR 潮** | 一个项目被 PR 淹没 | ⭐ **⭐ AI 让「产出」变便宜，⭐ 而「审查」没跟上** |
| ⭐ **Anthropic 的形式化验证** | 一次研究成果 | ⭐ **⭐ **⭐ 它试图直接攻击「修复成本」这一环** |
| ⭐ **GitBook 事件** | 一次入侵 | ⭐ **⭐ 「AI 攻击」正在成为一个责任分配工具** |
| ⭐ **NIST 的小企业指南** | 给一人公司的清单 | ⭐ **⭐ 防守能力的分布，⭐ 极不均匀** |

⭐ **⭐⭐ 而把这六个排在一起，⭐ **我看到的结论是：⭐ **⭐⭐ **AI 的能力增长是均匀的，⭐ 而它作用于防守与攻击两侧的速度是**不均匀**的。⭐ **⭐⭐**

⭐ **⭐⭐ 具体说：**

```
「找」的成本：↓↓↓↓（Calif 两周挖出藏了两年的 RCE）
「审」的成本：↓↓（FreeRDP 的 748 commit 潮）
「做」的成本：→（生成本身没变便宜）
「修」的成本：↓↓（Anthropic 的形式化验证，目前仅限汇编层的 no-crash 性质）
「拿到前沿模型」的成本：→（这是唯一没被 AI 改变的环节，⭐ 而它是瓶颈）
```

⭐ **⭐⭐⭐ 而最后那一行，⭐ **就是本号这六篇文章共同指向的结论：⭐ **⭐⭐ **当「找」便宜 100 倍而「修」只便宜 2 倍时，⭐ **⭐ **整个系统的瓶颈会从「发现能力」转移到「修复能力」，⭐ 而修复能力的上限，⭐ 是由「能不能用上好模型」决定的。⭐ **⭐⭐**

⭐ **⭐⭐⭐ 而这就把一个技术问题，⭐ **⭐ **变成了一个分配问题。⭐ **⭐⭐**

⭐ **⭐⭐⭐ 而 Green 那句冷话，⭐ **⭐ **恰好是这个分配问题在现实中的样子：⭐ **⭐ **「Nothing's going to fix this problem until something really bad happens.」⭐ **⭐⭐**

⭐ **⭐⭐⭐ **而如果我是 IEEE 那篇文章的编辑，⭐ **⭐ 我会在标题里加上「The PHP2Shell Vulnerability Heralds Cybersecurity Hell」⭐ 之后，⭐ **⭐ 再加一句：⭐ **⭐ 「and the bill is coming due for whoever can't pay.」⭐ **⭐⭐**

---

## 主要来源

- ⭐ **IEEE Spectrum《The PHP2Shell Vulnerability Heralds Cybersecurity Hell》（Dina Genkina，2026-11-02）**：⭐ **Matt Suiche（Tolmo）**「all the legacy software that was written by humans over the last 40 years is being exposed… Now it is time for the technical debt to be paid off」；⭐ **Suman Jana（哥伦比亚大学）**「a lot of very specific reasoning that is painful to do. And AI, I think, has done a very good job at that」⭐ 与「**a fundamental asymmetry in finding bugs and fixing bugs**」；⭐ **Matthew Green（约翰霍普金斯）**「**Nobody's going to fix this problem until something really bad happens. And PHP2Shell wasn't bad enough to be really bad.**」⭐ 与「maybe sometime in early 2027」；⭐ 「四个工程师、两个月开发补丁」；⭐ **「the Linux kernel… recently had over 1,000 vulnerabilities disclosed」**；⭐ 「frontier labs are donating some of their token budgets to look into these bugs… I think that should happen more」；⭐ 「It's just who finds it. Hopefully, the white-hat hackers find it first, like this one.」
- ⭐ **Anthropic《LLMs are making formal software verification feasible at a much larger scale》（2026-10-22，Frontier Red Team，合作方 Theorem）**：⭐ 123 个开源库、239 个 fuzz 入口点、⭐ **Rocq 约 1.8 亿行证明**、⭐ **信任基为 RISC-V 与 Linux 进程模型 + 定理陈述 + 检查器本身**；⭐ **「把既有可编译测试套件自动转成规范：'this test suite always passes'」**；⭐ **「If Claude can prove this spec, the fuzz test on RISC-V becomes superfluous」**；⭐ 「Claude also discovered bugs that had eluded detection for years, despite trillions of test runs」；⭐ **三条限制（musl + 单线程静态 RISC-V 二进制 vs 实际 x86/ARM + glibc、⭐ ASan 不检测所有内存安全 bug、⭐ 「Formally verified does not mean bug-free」—— 证明检查器无法判断规范是否匹配现实）**；⭐ **seL4 的对比数字：实现 2 人年、形式化验证 20 人年**
- ⭐ **Calif Research《PHP2Shell by Calif Research》（Ryan Austin，2026-10-21）**：⭐ 「discovered by Calif, OpenAI and Wiz」；⭐ 2026-08-01 发现时间线；⭐ 「We were not expecting to find anything critical - everyone and every lab had already done extensive AI assisted audits of this target」
- ⭐ **OpenAI《Patch the Planet: global response coordination as agents uncover critical vulnerabilities》（2026-10-21）**：⭐ 「Calif identified a critical flaw using GPT-5.6 Sol as part of our Patch the Planet initiative, with Wiz also independently discovering and reporting both vulnerabilities」；⭐ 修复版本 PHP 8.5.12 / 8.4.27 / 8.3.36 / 8.2.35
- CNBC《'PHP2Shell' vulnerability: What is it, and is your data at risk?》（2026-10-22）：⭐ **「Calif's researchers used OpenAI's GPT-5.6 Sol, while the Wiz team used its Wiz Atlas security AI agent, Google's Gemini 4 Argon, and GPT-5.6 Sol」**；⭐ Matt Suiche：*"this level of urgency is very new… the reason there is that sense of urgency now is really because everyone has AI-augmented capabilities, not only defenders but also attackers"*
- TechCrunch《PHP armageddon: OpenAI, Google's Wiz find ancient holes, panicking the internet》（2026-10-21）；phpnews.net（Eric L. Barnes）关于修复版本与协调过程
- ⭐ 本号此前写的相关分析：⭐ 《补丁还没发布，攻击就已经开始了：一个在 PHP 里躺了二十年的缺陷》、⭐ 《php2shell 一周实测：全球暴露面掉了 47.9%》、⭐ 《攻击者的工具箱里装着 Claude Code、DeepSeek 和 Kimi》、⭐ 《CVE-2026-98432 的补丁公告里两个容易被读错的地方》（⭐ 那一篇里的 RCU / 生命周期缺陷正是形式化证明最擅长的类型）

---

（说明：本文依据 IEEE Spectrum 原文、⭐ **Anthropic 2026-10-22 官方研究文章全文（我直接读取其页面正文与 Limitations 一节）**、⭐ **Calif Research 原始披露**、⭐ **OpenAI 的 Patch the Planet 公告**、⭐ 以及 CNBC / TechCrunch / phpnews.net 的报道撰写。**第五节的三方对比表格与「六篇文章的横向对比」⭐ 全部为笔者自行整理的判断，⭐ 不代表任何一方立场。** **文中所有引号内的英文原文均直接取自上述来源；⭐ 关于「防御侧 AI 流水线目前仍只有 2024 年 bug 报告 + 代理化审计」这一判断，⭐ 是笔者根据 Anthropic 与 Calif 官方材料所给信息做的推断，⭐ 原文未以此措辞表述。**）
