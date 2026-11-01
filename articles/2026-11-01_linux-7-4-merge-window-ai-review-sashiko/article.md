---
title: "两万个提交创纪录之后：内核里的 AI 从「写补丁」转向了「审补丁」"
date: 2026-11-01
slug: linux-7-4-merge-window-ai-review-sashiko
tags: [Linux内核, 内核开发, 合并窗口, AI代码评审, LLM, Sashiko, ChrisMason, RomanGushchin, AndrewMorton, Kicinski, JohannesBerg, OverlayFS, 信息泄漏, UAF, 内核治理, 维护者, 供应链安全, 自动化]
category: Linux/内核
author: FreeLAMP.com
original_source: "⭐ 一手核对：Phoronix《The Linux 7.4 Merge Window Is Easily The Largest In Kernel History》与《Linux 7.4 Merge Window Saw Nearly 20k Commits》（Michael Larabel，2026-11-01）+ LWN《The role of LLMs in patch review》《Toward a policy for machine-learning tools in kernel development》《Development tools: Sashiko, b4 review, and API specification》+ Jakub Kicinski 的 LKML 原文 + Chris Mason 的 [RFC] AI review prompt updates"
original_date: 2026-11-01
original_url: "https://www.phoronix.com/news/Linux-7.4-Merge-Window"
description: "Linux 7.4 合并窗口以 19,671 个提交成为内核史上最大的合并窗口，比 7.3 的 16,267 个高出 21%，源码树逼近 4,200 万行。而这个「暴涨」和 AI 直接相关 —— 前提是你先读懂它涨在哪儿：真正暴涨的不是功能，而是「AI 生成的、逐个维护者都在重新筛的低价值修复」。Jakub Kicinski 给出的一手数据是：9 天内 net 树 405 个补丁、net-next 687 个，37% 是修复类，「而这大概还是低估，因为 LLM 研究者更常在不知道该打标签的情况下就发修复」。本文把 Phoronix 的提交量数据、LWN 的 Sashiko/治理讨论、以及 Chris Mason 的 AI 评审发现 OverlayFS 真实安全漏洞（信息泄漏、UAF、NULL 解引用，且多个可被非特权用户触发）串起来，指出内核里 AI 的角色已经发生了一次性质变化：从「写补丁（被拒）」转向「审补丁（在被认真对待）」，而 Andrew Morton 与 Lorenzo Stoakes 那场争论说明真正的难点不是技术，是「一个每秒能产出一堆意见的第三方机器人，凭什么进流程的必经之路」。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Phoronix：The Linux 7.4 Merge Window Is Easily The Largest In Kernel History](https://www.phoronix.com/news/Linux-7.4-Massive-Window)** 与 **[Linux 7.4 Merge Window Saw Nearly 20k Commits](https://www.phoronix.com/news/Linux-7.4-Merge-Window)**（Michael Larabel，**2026-11-01**，含 3.1 → 7.4 全部合并窗口的提交数原始数据）
> - **[Phoronix：Linux 7.3 Network Changes Merged But Developers "Completely Overwhelmed"](https://www.phoronix.com/news/Linux-7.3-Networking)**（含 **Jakub Kicinski 的 LKML 原文引用**）
> - **[Phoronix：OverlayFS Sees Many Fixes Thanks To AI Code Review](https://www.phoronix.com/news/OverlayFS-Many-Fixes)**（含 Amir Goldstein 的 pull request 说明）
> - **[LWN：The role of LLMs in patch review](https://lwn.net/Articles/1064830/)**（Daroc Alden，2026-03-31，Andrew Morton vs Lorenzo Stoakes 之争的完整记录）
> - **[LWN：Toward a policy for machine-learning tools in kernel development](https://lwn.net/Articles/1049830/)**（Jonathan Corbet，2025-12-11，2025 维护者峰会记录）
> - **[LWN：Development tools — Sashiko, b4 review, and API specification](https://lwn.net/Articles/1063303/)**（2026-03-19）
> - **[Chris Mason：[RFC] AI review prompt updates](https://lkml.iu.edu/2601.3/10069.html)**（2026-01-30）
> ⚠️ **本文是本号此前那篇《Linux 7.3 是一个「全方位纪录」》的续篇** —— 那篇讲的是「**AI 参与写代码**」，**本文讲的是「AI 参与审代码」**，而这两件事的性质完全不同。
> ⚠️ **本文为**解读**。

## 一句话结论

**⭐ 19,671 个提交 —— 这是内核史上最大的合并窗口，比 7.3 高出 21%。**

**⭐ 而如果只把这个数字当成「内核开发速度加快」，你会完全看错它涨在哪儿。**

**因为真正暴涨的不是功能，是「**逐个维护者都在重新筛的低价值修复**」—— 而这部分的主要来源，正是 AI。**

**⭐ 而更有意思的是：在同一周，Chris Mason 用 AI 评审在 OverlayFS 里挖出了**真实的安全漏洞**（信息泄漏、UAF、NULL 解引用，多个可被非特权用户触发），并已合入 7.4 且标记回移 stable。**

**—— 所以内核里的 AI，同时在做两件相反的事：**

| | 在做什么 | 状态 |
|---|---|---|
| **一端** | ⭐ **大批量生产低价值补丁，淹没维护者** | ⭐ **「completely overwhelmed」** |
| **另一端** | ⭐ **在人类评审漏掉的地方找出真 bug** | ⭐ **已合入、已回移、已被 CVE 关注** |

**⭐ 我认为这是 2026 年内核生态里最值得注意的一件事 —— 而它不是「AI 写代码」的故事，是「AI 审代码」的故事。**

## 一、⭐⭐ 数字：19,671 与 15 年的曲线

**⭐ Phoronix 把 Linux 3.1 以来每个合并窗口的提交数都列了出来。**

**⭐ 而最有信息量的不是绝对值，是**形状**：**

| 版本 | 提交数 | 版本 | 提交数 |
|---|---|---|---|
| 3.1（2011） | 7,620 | **6.7** | **16,203** |
| 3.10 | 12,715 | 6.10 | 12,402 |
| 4.9 | 15,095 | 6.18 | 12,910 |
| 5.8 | 15,086 | 6.19 | 13,229 |
| 5.10 | 14,770 | 7.0 | 12,468 |
| 5.13 | 15,069 | 7.1 | 13,963 |
| 6.0 | 14,378 | 7.2 | 14,395 |
| 6.7 | 16,203 | **7.3** | **16,267** |
| | | **7.4** | **19,671** |

**⭐ 我把这条曲线读出了三个阶段：**

```
2011（3.1）    ████████                        7,620
2012-2015     ██████████████                 9,400 ~ 12,700
2016-2024     ████████████████               12,400 ~ 15,100
2025（6.7）   █████████████████              16,203   ← 第一次突破 16k
2026（7.3）   █████████████████              16,267
2026（7.4）   █████████████████████          19,671   ← 史上最高
```

**⭐ 而 Phoronix 的判断是：**

> **「The Linux 7.4 merge window **by far** is the largest merge window ever in terms of commits/patches. Nearly 20k! **The upward trend has continued building the past several kernel releases.** Typically the merge windows saw 13~14k commits or less and now we are pushing 20k.」**

**⭐ 注意他强调的：13~14k 是「典型值」，而 7.3 的 16,267 已经是异常值，7.4 的 19,671 是**连续第七个季度维持在 16k 以上**后的新高**。**

### 1.1 ⭐ 而源码树的规模

| | 总行数 | 空行 | 注释 | 代码（cloc） |
|---|---|---|---|---|
| **v7.3** | 41,019,555 | 5,138,701 | 4,918,548 | 30,962,306 |
| **7.4-rc1 前** | **41,605,120** | 5,193,578 | 4,993,604 | **31,417,938** |

**⭐ 而 Phoronix 算出的净增：**

> **「Or nearly **half a million lines of code added** during the Linux 7.4 merge window, ignoring comments and blank lines.」**

**⭐ 而他顺带给出的预测：**

> **「it's likely that by the time of Linux 7.5 in the new year it will be **past 42 million lines**.」**

### 1.2 ⭐⭐ 而整个周期 vs 合并窗口的对比，才是关键

**⭐ Phoronix 指出了一个很多人会忽略的对比：**

> **「Linux 7.3 was the first time breaching 20k commits for an entire kernel cycle (20,260 commits from v7.2 to v7.3). **Now with Linux 7.4 we're seeing nearly that much just during the merge window.**」**

**⭐ 我把这个对比做成一个更直观的说法：**

| | 整个周期 | 合并窗口 |
|---|---|---|
| **7.3** | 20,260 | 16,267（**占 80%**） |
| **7.4** | （7.3 周期那么多） | **19,671（**几乎等于整个 7.3 周期**）** |

**—— 换句话说：⭐ 「**一个合并窗口的提交量，已经等于上一个完整周期的提交量**」。**

**⭐ 而这个压缩比例，正是「人类维护者能在两周内审完的东西」与「实际涌进来的东西」之间缺口越来越大的直接体现。**

## 二、⭐⭐ 「完全被淹没」：一手数据

**⭐ 而要理解 19,671 这个数字涨在哪，必须看网络子系统维护者的一手数据。**

**⭐ Phoronix 引用的 Jakub Kicinski（net/net-next 维护者）原话：**

> **「In the last 9 days there were **405 postings explicitly tagged with [PATCH net]**, vs **687 with [PATCH net-next]**. **37% of posted patches being fixes is pretty crazy**, and that's likely undercounting because **LLM "researchers" more often post fixes without knowing to tag the patches** for specific trees.」**
>
> **「I don't have historic data. In any case, **we keep adjusting the criteria. The next PR will be smaller.**」**

**⭐ 我把这几个数字拆开：**

| | |
|---|---|
| **9 天内的补丁量** | **405 + 687 = 1,092 个** |
| **其中修复类的比例** | **37%** |
| **Phoronix 的补充** | ⭐ **「some weeks seeing **double the count** of typical patches for the networking area」** |

**⭐ 而「9 天 1,092 个」这个数字意味着什么，我算一下：**

> **≈ 每天 121 个网络子系统补丁。**
> **而其中 37% 是「修复」—— 也就是约每天 45 个「修 bug」的补丁。**

**⭐ 这就是「淹没」的具体形态 —— 而 Kicinski 那句「we keep adjusting the criteria. **The next PR will be smaller.**」透露出一个残酷的事实：**

**—— 他们唯一能做的，是**收紧合并标准**来减少进入主线的量。而这意味着，那些补丁不是被修好了，是被**挡在门外**了。**

### 2.1 ⭐⭐ 而 Kicinski 在 7.3 合并时说了更重的话

**⭐ 那是本次事件里最著名的一段引述：**

> **「We are completely overwhelmed, of course. The glimmer of hope is that **we secured sufficient LLM budget and access (thank you Meta!)** to run reviews with multiple frontier models on each patch. **This eliminates some hallucinations.** That said, in terms of review, the LLMs can only do so much. **The sad truth is that our APIs (especially for rare events like PCIe errors, timeouts etc.) have always been racy, and now LLMs don't let us ignore that.**」**
>
> **「I expect our direction for the next release will be to **tweak the reviews a little bit more, but start shifting focus to letting the LLMs take care of the busy work** - managing patchwork, automating common process complaints, editing commit messages, and maybe applying patches which already got "reviewed-by" tags from people we trust...」**

**⭐ 我认为这段话里有三个层次的信息，而且每一层都值得单独说：**

**① 「completely overwhelmed」—— 而他们**已经用上了 AI 评审**（多个前沿模型并行跑）**

**⭐ 这一点的顺序很重要：⭐ 他们不是「还没用 AI 所以被淹没」，而是「**已经用上了 AI 评审，还是被淹没**」。**

**② 「thank you Meta!」—— 算力是别人给的**

**⭐ 而这引出了 LWN 那篇讲的关键结构性问题（后面第六节详述）：**

> **「the Sashiko service depends on some generous benefactor being willing to make the LLM time it needs available. **That is happening now, while the AI bubble remains pretty well inflated** … At some point, though, that generosity seems likely to come to an end.」**
>
> **「Google is nicely donating LLM time for Sashiko now, but remember that **the company once freely handed out Nexus One phones to developers. Now those developers are expected to buy their own toys.**」**

**③ 「the sad truth is that our APIs have always been racy, and now LLMs don't let us ignore that」**

**⭐ 这一句我认为是整段引文里最有技术含量的一句 —— 而且它指向一个很少被讨论的机制：**

**—— 内核里那些「罕见事件路径」（PCIe 错误、超时）的 API 历来就有竞态，而因为罕见所以一直没人管。**

**—— 现在 LLM 在批量地翻这些代码，**把这些「一直存在但没人注意」的竞态翻出来了**。**

**⭐ 而他们的应对是 —— 让 LLM 去干「busy work」：**

> **「managing patchwork, automating common process complaints, editing commit messages, and maybe applying patches which already got "reviewed-by" tags from people we trust」**

**⭐ 也就是说：⭐ 让人来审，机器来干体力活 —— 而且只碰「已经有人签了 reviewed-by」的补丁。**

## 三、⭐⭐⭐ 而另一端：AI 评审挖出了真的安全漏洞

**⭐ 这一节是我认为全文最重要的部分 —— 因为它和第二节形成了一组极强的对照。**

### 3.1 OverlayFS：Chris Mason 的 AI 评审

**⭐ Amir Goldstein 在 OverlayFS 更新 pull request 里的说明（原文）：**

> **「- Fixes for bugs found by Chris Mason's AI review, several of them **reachable by unprivileged users**: an **info leak**, **use-after-free** and **NULL deref** bugs, an **RCU walk stall with remote layers** and **data loss with nfs_export**」**
>
> **「- Fix copy up of files with an **empty security.capability xattr**, which any user could set to block copy up」**
>
> **「- Fix a regression from v6.16 with the override_creds mount option」**
>
> **「- Two casefold fixes」**

**⭐ 我把这批发现整理成一张表，因为它们的性质值得看：**

| 发现 | 性质 | 谁能触发 |
|---|---|---|
| **信息泄漏** | ⭐ **数据泄漏** | ⭐ **非特权用户** |
| **UAF** | ⭐ **内存安全** | ⭐ **非特权用户** |
| **NULL 解引用** | 崩溃 | ⭐ **非特权用户** |
| **RCU walk stall（远程层）** | ⭐ **可远程触发的停滞** | 远程 |
| **nfs_export 数据丢失** | 数据完整性 | — |
| **`security.capability` 空 xattr 阻塞 copy up** | ⭐ **任何用户可设置** | ⭐ **任何用户** |

**⭐ 而这些补丁的命运是：**

> **「Merged this weekend for Linux 7.4 and **also marked for back-porting to current stable kernel versions**」**
>
> **「There ended up being **more than a dozen patches to OverlayFS in the past week** from Chris Mason after uncovering these issues in the code.」**

**⭐ 我想强调「**more than a dozen**」这个措辞 —— 因为它说明这不是一两个撞见的，而是「持续翻出来」的。**

### 3.2 ⭐⭐ 而这条线的历史，比 7.4 早得多

**⭐ 事实上 Chris Mason 做 AI 评审不是 7.4 才开始的。** **我核对了时间线：**

| 时间 | 事件 |
|---|---|
| **2025-10-16** | ⭐ **LWN《Large language models for patch review》** —— Corbet 报道 Chris Mason 在内核峰会讨论组发起「用 LLM **评审**补丁」的讨论，「**instead of create them**」 |
| **2026-01-30** | ⭐ **Chris Mason 发布 [RFC] AI review prompt updates** —— 把评审拆成**单任务分块**，用 Python 脚本预先抽取改动的函数、类型、调用图，**降低 token 消耗** |
| **2026-02** | 评审提示公开为 GitHub 仓库 `masoncl/review-prompts`（内核 + systemd） |
| **2026 年初** | ⭐ **sched_ext（可扩展调度器）因 AI 评审而出现一批 bug 修复** —— Phoronix 报道「这些修复有些甚至追溯到好几个内核周期之前」 |
| **2026-03-17** | ⭐ **Sashiko 正式发布**（Roman Gushchin） |
| **2026-11-01** | ⭐ **OverlayFS 的信息泄漏 / UAF / NULL 解引用等被合入 7.4 并标记回移 stable** |

**⭐ 而 Mason 那份 RFC 的核心思路，我认为是整件事里最值得学的工程细节：**

> **「Using tasks allows us to **break up large diffs into smaller chunks, and review each chunk individually**. This ends ...」**
>
> **「而为了分块做的批量处理，用 Python 脚本预先抽取改动的函数、类型和调用图 → **token 消耗进一步降低**；**也不需要 AI 自己去发现同样的信息**，提示就能专注在评审本身。」**

**⭐ 我把这个思路抽象一下 —— 它其实是一条通用的成本工程原则：**

> **⭐⭐ **「**不要把整个 diff 丢给模型让它自己找线索**。**
> **⭐ **先用确定性工具（脚本、解析器、调用图）把「它需要知道的东西」准备好，再让模型做「它擅长的事」—— 判断。**

**—— 而这正好对应 LWN 引用的一句：**

> **「While the ability of LLMs to **generate** kernel code is unproven at best, **their ability to find obscure problems in code written by humans** has been reasonably well demonstrated.」**
>
> **「LLM **生成**内核代码的能力尚未得到证明，但它们**在人类写的代码里找出隐蔽问题**的能力，已经被相当好地演示过了。」**

## 四、⭐⭐ Sashiko：53% 与那 100% 的人类漏检

**⭐ 而 Sashiko 是这条线上第一个**产品化**的工具。**

**⭐ 它的作者 Roman Gushchin 给出的实测数据（LWN 引用）：**

> **「In my measurement, Sashiko was able to find **53% of bugs** based on a **completely unfiltered set of 1,000 recent upstream issues** using "Fixes:" tags (using **Gemini 3.1 Pro**). Some might say that 53% is not that impressive, but **100% of these issues were missed by human reviewers**.」**

**⭐ 我把这组数字拆开 —— 而我认为**最有冲击力的不是 53%，是那个 100%：**

| | |
|---|---|
| **样本** | ⭐ **1,000 个近期上游 issue（用 「Fixes:」 标签筛的，完全未过滤）** |
| **AI 找到的** | **53%** |
| **⭐ 人类评审漏掉的** | ⭐ **100%** |
| **模型** | **Gemini 3.1 Pro** |

**⭐ 而 Gushchin 自己那句「有些人会说 53% 不算 impressive」也值得注意 —— 因为这正是一个**双重标准**的时刻：**

**—— 用 AI 找 bug 的时候，人们拿 53% 和「完美」比；**
**—— 用 AI 写 bug 的时候，人们拿它的错误率和「完美」比。**

**⭐ 而 Sashiko 的架构也值得说，因为它体现了「怎么让 LLM 做评审」这个问题的答案：**

**⭐ LWN 引用 Chris Mason 的提示是基础，但 Sashiko 用了：**

> **「a different **multi-stage review protocol**, which somewhat **mimics the human review process** and **forces the LLM to look at the proposed change from different angles**」**

**⭐ 我认为「模仿人类评审流程 + 强迫模型从不同角度看」这个设计，正是上一节 Mason 那套「分块 + 预抽取」思路的延伸 —— 而它解释了为什么 Sashiko 的效果比朴素地丢 diff 进去好。**

**⭐ 而它的形态与归属：**

| | |
|---|---|
| **访问方式** | 现阶段**只有 Web 界面**；计划是能通过邮件发出评审 |
| **开源** | **「fully open-source」**，GitHub `sashiko-dev/sashiko`，**Apache-2.0** |
| **代码归属** | ⭐ **已交给 Linux Foundation** |
| **⚠️ 底座** | ⭐ **「built on a proprietary foundation (the Gemini model), so it is **not truly a free-software solution**」** |
| **算力** | ⭐ **Google 捐赠的 LLM 时间** |

**⭐ 而 LWN 那篇文章的收尾评论，我认为是关于「可持续性」最清醒的一段话：**

> **「Since Sashiko depends on its underlying LLM, the Sashiko service depends on **some generous benefactor** being willing to make the LLM time it needs available. That is happening now, while the **AI bubble remains pretty well inflated** and the purveyors of LLMs are trying to create dependencies on those models wherever they can. **At some point, though, that generosity seems likely to come to an end.**」**
>
> **「Google is nicely donating LLM time for Sashiko now, but remember that **the company once freely handed out Nexus One phones to developers. Now those developers are expected to buy their own toys.** One hopes that, when that history repeats itself in the LLM context, **the community will not have let the ability to do its own reviews atrophy entirely.**」**

**⭐ 我把这段的警告翻译成一句：**

> **⭐⭐ **如果内核社区把「评审能力」外包给 donated LLM time，那么当捐赠停止时，社区可能已经丧失了独立评审的能力。**

**—— 这和本号此前写过的那些「我们把关键能力交给某个免费/赠送的外部服务」的故事，是同一个模式。**

## 五、⭐⭐⭐ 而真正的难题不是技术，是社会

**⭐ 我认为这一节是整篇文章最重要的一节 —— 因为它说明了「AI 评审」卡在哪里。**

### 5.1 事件：一次内存管理补丁集的争论

**⭐ LWN《The role of LLMs in patch review》记载的导火索（LWN 引用）：**

**⭐ Andrew Morton（内存管理维护者）的提议：**

> **「the current way Sashiko integrates into the memory-management workflow isn't working. He merges patches to his tree, and "**then half a day later a bunch of potential issues are identified.**"」**
>
> **「Morton stated that he was going to **further increase the lag** between seeing a patch set on the mailing list and merging it to his tree, **to give Sashiko time to produce feedback and patch authors time to respond to it**.」**

**⭐ 而他的理由，我认为是整个争论里最有说服力的一段：**

> **「Look, I know people are busy. **If checking these reports slows us down and we end up merging less code and less buggy code then that's a good tradeoff.**」**
>
> **「**That's a really high hit rate!** How can we possibly not use this, if we care about Rule #1?」**

**⭐ 他引用的实测数据也很具体：**

> **「Out of about **35 emails**, **22 received replies indicating that alterations were definitely needed**, with the rest being more ambiguous, being false reports, or not being responded to.」**

**⭐ 而他的结论：**

> **「I expressed the opinion that such a hit rate of finding actual problems in patches **was worth the pain** of figuring out how to integrate Sashiko into the process.」**

### 5.2 ⭐⭐ 而 Lorenzo Stoakes 的反对理由更狠

**⭐ 而他的那条消息，我认为是整场讨论里最清醒的一段：**

> **「Andrew, for crying out loud. **Please don't do this.** 2 of the 3 series I respun on Friday, working a 13 hour day to do so, don't apply to Sashiko, but do apply to the mm tree. **I haven't the faintest clue how we are supposed to factor a 3rd party experimental website applying or not applying series into our work?**」**

**⭐ 而他给出的三个条件，我认为是这场争论的实际落点：**

| | |
|---|---|
| **①** | ⭐ **把「要不要用、怎么用」的决定权**下放给各子维护者** |
| **②** | ⭐ **不要要求补丁必须能被 Sashiko 干净地 apply 才接受** |
| **③** | ⭐ **不要要求它提出的每一条都必须被回应** |

**⭐ 而他反复强调的一个技术观察，Morton 的解读与之相反：**

> **Stoakes：「those 22 emails indicate cases where the tool was correct **in at least one individual observation**. Since it **normally sends multiple suggestions and questions per review**, the actual rate of false positives for individual comments **must be substantially worse** than that.」**

**⭐ 而他最担心的是「量」而不是「质」：**

> **「given its **inexhaustible ability to produce new reviews that require human attention**」**
>
> **「Incorporating the tool in its present state, as anything other than a simple advisory, **would increase the workload on the already overworked memory-management maintainers**.」**

### 5.3 ⭐ 而 Pedro Falcato 提出了第三条路

**⭐ 而我认为 Falcato 的提议被低估了 —— 它才是唯一「两边都不否定」的方案：**

> **「Avoiding bugs is important, Falcato agreed, but: '**I simply don’t think either contributors or maintainers will be particularly less stressed with the introduction of obligatory AI reviews.**' He suggested that **simply codifying the memory-management review process** (as the netdev review process has been) **would be more helpful than mandating the use of Sashiko**.」**
>
> **「Falcato also pointed out that **Sashiko is experimental, untested software**, and it should probably not be made critical to the process yet on those grounds.」**

**⭐ 我把三方的立场整理成一张表：**

| | 主张 | 核心理由 |
|---|---|---|
| **Morton** | ⭐ **把 Sashiko 评审变成必答项**，并延长合并前的等待期 | **命中率高（35 封邮件里 22 封确认需要改）→「不值得吗？」** |
| **Stoakes** | ⭐ **别强制，最多当参考** | ⭐ **「它能无限量产出需要人关注的评审」→ 只会增加工作量** |
| **Falcato** | ⭐ **先把人类评审流程本身规范化**，别急着强制 AI | ⭐ **「强制 AI 评审不会让人更轻松」；而且它是未测试的实验性软件** |

**⭐ 而 LWN 那篇文章的结论段，我认为是全文最精准的一句概括：**

> **「the problem posed by the use of Sashiko is **a social one, not a technical one**: how much extra reading, hallucinated problems, delays in the review process, robotic gatekeeping, and reliance on proprietary models is acceptable in order to make sure the kernel accepts less buggy code? It's a question that will eventually touch every subsystem of the kernel and beyond, not just the memory-management code, and **one that undoubtedly deserves a lot of discussion. There are no easy answers.**」**

**⭐ 我把它翻译一下：**

> **⭐⭐ **「难的不是 AI 能不能找出 bug，而是「一个每秒能产出一堆意见的第三方机器人，凭什么进流程的必经之路」。**
> **⭐ **而这个问题最终会碰到内核的每一个子系统，以及内核之外的所有开源项目。**

## 六、⭐⭐ 而治理层面的共识：2025 维护者峰会

**⭐ 而在争论之前，2025 年的维护者峰会其实已经就一个更根本的问题达成了一致。**

**⭐ Sasha Levin 总结的共识（LWN 记录）：**

> **「human accountability for patches is critical, and **use of a large language model in the creation of a patch does not change that**. **Purely machine-generated patches, without human involvement, are not welcome.** Maintainers must retain the authority to accept or reject machine-generated contributions as they see fit. And, he said, there is agreement that **the use of tools should be disclosed in some manner**.」**

**⭐ 我把这四条列出来 —— 它们划定了「AI 写代码」的边界：**

| 共识 | 内容 |
|---|---|
| **① 人类担责** | ⭐ **用了 LLM 写补丁，不改变「人对补丁负责」这件事** |
| **② 不欢迎纯机器补丁** | ⭐ **「Purely machine-generated patches, without human involvement, are not welcome.」** |
| **③ 维护者保留裁量权** | ⭐ **接受还是拒绝，由维护者决定** |
| **④ 工具使用要披露** | ⭐ **「in some manner」** |

**⭐ 而关于第 ④ 条，讨论的结果很有意思 —— 最终「没有硬规则」：**

> **Torvalds：「there does not need to be a tag at all. The information could just be put into the changelog instead.」**
>
> **Torvalds：「Torvalds accused the group of **over-thinking** the problem, saying that **it was better to experiment and see what works.**」**
>
> **Levin：「Levin said that he would post a documentation patch asking LLM tools to add an Assisted-by tag, **but would not make an effort to enforce the rule**.」**

**⭐ 而 Linus 对「用 LLM 写代码」这件事的判断，一直很清醒：**

> **「Linus Torvalds jumped in to say that he thought the conversation was **overly focused on the use of LLMs to write code**, but **there has not, yet, been much of that happening for the kernel**. So any problems around LLM-written code are **purely hypothetical**.」**

**⭐ 但他对「用 LLM 审代码」的判断完全相反 —— 而且我认为这才是关键：**

> **「But these tools **are** being used for other purposes, **including identifying CVE candidates and stable-backport candidates, and for patch review**. Andrew Morton, Torvalds said, had recently shown an example of a machine-reviewed patch that was "**stunning**"; it found **all of the complaints that Torvalds had raised** with the patch in question, **and a few more as well**.」**
>
> **「Torvalds, though, pointed out that **developers have long been complaining about a lack of code review; LLMs may just solve that problem.** **They are not writing code at this point**, though that will likely happen at some point too. **Once these systems start submitting kernel code, we will truly need automated systems to review all that code**, he said.」**

**⭐ 我认为这几句里有一个很重要的因果链：**

```
今天：AI 审代码 → 缓解「代码评审不够」这个老问题
     ↓
将来：如果 AI 开始写代码并提交
     ↓
那就真的需要自动化系统来评审那批代码
     （而这批代码的数量，会是今天 AI 产出量的平方级）
```

**⭐ 而这正好解释了为什么内核社区现在愿意接受 AI 评审 —— ⭐ 因为他们已经在为「AI 写的代码」做准备了。**

**⭐ 而 Alexei Starovoitov 补充了一个很实用的观察（LWN 记录）：**

> **「he loves the reviews that the BPF community gets from the LLM systems. **They ask good questions even when the reviews are wrong.** Even better, **developers respond to the questions, despite the fact that they are answering a bot**; those answers can be used to help the models learn to do better in the future.」**

**⭐ 「即使评审是错的，它提出的问题也往往是好问题」—— 这句话我认为是对 AI 评审最准确的定位：**

**⭐⭐ **它的价值不在「结论对」，而在「把人类没想问的问题摆出来」。**

## 七、⭐⭐⭐ 我的评价

### 7.1 ⭐⭐⭐ 而这个事件最该被记住的，是「同一件事的两面」

**⭐ 我想先把这个对照摆清楚，因为它是我认为全文的核心：**

| | **AI 生成补丁（7.3 → 7.4）** | **AI 评审补丁（7.4）** |
|---|---|---|
| **谁在做** | ⭐ **外部 LLM 研究者、机器人** | ⭐ **内核内部的维护者（Chris Mason）** |
| **产物** | ⭐ **1,092 个补丁 / 9 天，37% 是修复** | ⭐ **十几个 OverlayFS 补丁，含信息泄漏 / UAF / NULL 解引用** |
| **维护者反应** | ⭐ **「completely overwhelmed」；唯一手段是**收紧合并标准**** | ⭐ **合并 + 标记回移 stable** |
| **技术含量** | ⭐ **低 —— 大量是「低价值修复、清理、措辞澄清」** | ⭐ **高 —— 挖出了非特权用户可触发的安全 bug** |
| **人力代价** | ⭐ **逐个重新筛** | ⭐ **只处理它标出来的那几条** |
| **社区态度** | ⭐ **Johannes Berg：设定「三秒规则」直接忽略** | ⭐ **Morton：希望强制回应；Stoakes：只能当参考** |

**⭐ 我认为这个对照说明了什么：**

> **⭐⭐ **「AI 在内核里有没有用」这个问题问错了。**
> **⭐ **真正的问题是「**谁在用 AI**」—— 而这两行的答案是完全相反的。**

**⭐ 而 Johannes Berg 那条「三秒规则」我认为是整篇材料里最实用的一条：**

> **「I'm going to state, for the record, that I'm going to make judicious use of ability to ignore patches, and apply it to pretty much all syzbot-AI-generated patches **unless a 3-second review says "obviously right"**.」**
>
> **「In particular, I will absolutely *not* "comment on the patches as usual" and argue with an LLM that **can bulls*** out code faster than another computer can even deliver it to me by email.」**

**⭐ 我把这条规则的精髓提炼出来：**

> **⭐⭐ **它不要求你看懂 AI 的推理，只要求你在三秒内判断「这明显是对的」。**
> **⭐ **「三秒」是关键 —— 它把评审成本压到了「扫一眼」这个量级，从而**可规模化**。**

**—— 而这恰好是它能落地的原因。而 Sashiko 那种「每条都要回应」的方案，恰恰相反：它的成本是「不可规模化」的。**

**⭐ 而值得注意的是 Berg 还澄清了一件容易被误解的事：**

> **「it was clarified that **every AI-generated patch by Syzbot is pre-reviewed and approved by a human**. Syzbot also does not send automatic replies and does not automatically submit newer versions of patches.」**

**⭐ 也就是说：⭐ 「AI 生成的补丁」和「AI 评审的补丁」是完全不同的两回事 —— 而公众讨论经常把它们混为一谈。**

### 7.2 ⭐⭐ 而第二件事：19,671 这个数字该怎么读

**⭐ 我认为如果只记住「内核提交量创纪录」，会得出一个完全错误的结论。**

**⭐ 我的解读是：**

```
19,671 个提交
    ↓
其中相当大的一部分是「AI 批量产出的低价值修复/清理/澄清」
    ↓
这些补丁对内核的净价值接近零（甚至为负 —— 它们消耗了维护者的时间）
    ↓
而真正有价值的部分，藏在另一个数字里：
    ↓
Chris Mason 的 AI 评审 → 十几个 OverlayFS 安全补丁（已回移 stable）
```

**⭐ 所以我认为正确的读法是：**

> **⭐⭐ **7.4 的 19,671 提交，**不是「内核开发效率提升了 21%」，而是「**内核评审能力被稀释了**」的一个指标。**
> **⭐ **而同一周发生的 OverlayFS 那批补丁，才是这个版本真正值得记住的东西。**

**⭐ 而这也解释了 Phoronix 那个略带保留的措辞：**

> **「It will be interesting to see **what practical production implementations** ultimately come out of this interesting research work.」**（本号另一篇里引过）

**—— 「研究工作」和「生产实现」之间的落差，正是当前状态的准确描述。**

### 7.3 ⭐⭐⭐ 而第三件事：这整件事暴露了一个「能力 atrophy」风险

**⭐ 我想把 LWN 那段「Nexus One」的类比展开，因为我认为它比任何技术讨论都更值得警惕：**

**⭐ LWN 的原文：**

> **「One hopes that, when that history repeats itself in the LLM context, **the community will not have let the ability to do its own reviews atrophy entirely.**」**

**⭐ 我把这个担忧翻译成一个更具体的问题：**

| | 现状 | 风险 |
|---|---|---|
| **AI 评审的能力** | ⭐ **内核社区自己拥有**（Mason 的 prompts、Sashiko 的代码在 LF 名下、b4 review 在集成） | ✅ |
| **AI 评审的算力** | ⭐ **Google / Meta 捐赠** | ⚠️ **取决于捐赠者的商业可持续性** |
| **底座模型** | ⭐ **Gemini 3.1 Pro（专有）** | ⚠️ **不是自由软件方案** |

**⭐ 而第三行是我最在意的 —— 因为它和本号此前写过的那些故事同型：**

**⭐ **当社区把「评审」这个核心能力建立在「别人免费提供的算力 + 别人的专有模型」之上时，它就同时把「不再需要自己评审」的种子埋了下去。**

**⭐ 而 Andrew Morton 那句「如果这让我们合并更少代码、但 bug 更少，那是好交易」，其实已经默认了「人类评审时间不够」这个前提 —— 而这个前提本身是可以被改变的（只要上游少产出低价值补丁）。**

### 7.4 ⭐⭐ 而最后：我认为这个事件对所有开源项目都有借鉴价值

**⭐ 我把「Btrfs 之父给内核做 AI 评审」这个案例，与本号此前写过的那些供应链事件放在一起看：**

**⭐ 有一个共同模式：**

> **⭐⭐ **问题的根源从来不是「代码写得对不对」，而是「**有多少东西需要人来审**」。**
> **⭐ **而 AI 恰好在这个维度上既是最大的放大器（产出垃圾），也是最有效的减负器（替你筛）。**

**—— 所以我的建议很朴素：**

**⭐ **对于任何有「评审瓶颈」的开源项目，值得同时做两件事：**
**⭐ **① 用 AI 评审去捞那些「人类懒得看但机器能发现」的问题（像 Mason 那样）；**
**⭐ **② 用「三秒规则」这类明确门槛去挡住那些「机器能产但人不该看」的东西（像 Berg 那样）。**

**—— 而这两件事必须**同时做**。只做 ①，你会得到 19,671 个提交和一个 overwhelmed 的维护者；只做 ②，机器的算力就白捐了。**

## Sources

- ⭐ 一手：[Phoronix — The Linux 7.4 Merge Window Is Easily The Largest In Kernel History](https://www.phoronix.com/news/Linux-7.4-Massive-Window)（2026-11-01，含 Linux 3.1→7.4 全部合并窗口提交数原始数据）
- ⭐ 一手：[Phoronix — Linux 7.4 Merge Window Saw Nearly 20k Commits, Source Tree Approaching 42 Million Lines](https://www.phoronix.com/news/Linux-7.4-Merge-Window)（2026-11-01，cloc 统计与全周期对比）
- ⭐ 一手：[Phoronix — Linux 7.3 Network Changes Merged But Developers "Completely Overwhelmed" Due To AI/LLMs](https://www.phoronix.com/news/Linux-7.3-Networking)（含 Jakub Kicinski 的 LKML 原文）
- ⭐ 一手：[Phoronix — Linux Networking Continues Being Bombarded With AI Patches](https://www.phoronix.com/news/Linux-Net-Bombarded-AI-Patches)（含 9 天 405/687 与 37% 的原始数据）
- ⭐ 一手：[Phoronix — Linux Wireless Maintainer Takes Firm Stance Against AI/LLM Generated Slop Patches](https://www.phoronix.com/news/Linux-WiFi-Strict-AI-Slop-Patch)（含 Johannes Berg 的「三秒规则」原文）
- ⭐ 一手：[Phoronix — OverlayFS Sees Many Fixes Thanks To AI Code Review](https://www.phoronix.com/news/OverlayFS-Many-Fixes)（含 Amir Goldstein 的 pull request 说明）
- ⭐ 一手：[LWN — The role of LLMs in patch review](https://lwn.net/Articles/1064830/)（Daroc Alden，2026-03-31；Morton / Stoakes / Falcato / Gushchin 争论全文）
- ⭐ 一手：[LWN — Toward a policy for machine-learning tools in kernel development](https://lwn.net/Articles/1049830/)（Jonathan Corbet，2025-12-11；2025 维护者峰会记录，含 Linus、Starovoitov 的发言）
- ⭐ 一手：[LWN — Development tools: Sashiko, b4 review, and API specification](https://lwn.net/Articles/1063303/)（含 Sashiko 的 53%/100% 数据与「能力 atrophy」警告）
- ⭐ 一手：[LWN — Large language models for patch review](https://lwn.net/Articles/1041694/)（2025-10-16，Mason 发起评审讨论）
- ⭐ 一手：[Chris Mason — [RFC] AI review prompt updates](https://lkml.iu.edu/2601.3/10069.html)（2026-01-30）
- 一手：[Chris Mason 的评审提示仓库 `masoncl/review-prompts`](https://github.com/masoncl/review-prompts)｜[Sashiko](https://sashiko.dev/)｜[sashiko-dev/sashiko](https://github.com/sashiko-dev/sashiko)
- 本号此前：Linux 7.3 是一个「全方位纪录」（2026-10-19）、sched_ext 因 AI 评审而出现一批修复（2026-07）

---

（说明：所有引号内内容、提交数与百分比均来自上述一手材料；**第七节的两面对照分析、「评审能力 atrophy」的风险判断与「两件事必须同时做」的建议为笔者观点**。）
