# Kernel Report 回归：Jonathan Corbet 在 Kernel Recipes 2026 谈内核社区的「加速变化」

> 来源与边界：本文是**新闻+背景梳理**，不是演讲全文翻译。新闻事实来自 LWN《The Kernel Report 2026 edition》（2026-09-24）与 Kernel Recipes 官方日程页（2026-09）；演讲摘要原文引自主办方页面。**演讲的详细内容目前只有 YouTube 视频，尚无文字稿**，因此本文不替演讲者转述其未公开的论点；涉及内核社区现状的**背景**，均明确标注来自公开报道（The Register、LWN、Dataconomy 等），与本次演讲的归属分开。编译整理：LeisureLinux。

Kernel Recipes 2026（第 13 届，巴黎，9 月 21–23 日）今年请到了 **Jonathan Corbet** 担任「patron」（荣誉教父）并参与编排议程——这是会议方给出的定位。而 Corbet 带来的，是**停办两年后回归的《The Kernel Report》**。

Corbet 的身份本身就说明了这份报告的份量：他是**内核文档 maintainer**、**LWN.net 联合创始人兼执行主编**，也是《Linux Device Drivers, 3rd Edition》的第一作者。**《The Kernel Report》是他多年用来「纵览内核开发社区」的招牌演讲**——按 Kernel Recipes 自己的说法，「距离 Corbet 上一次在 Kernel Recipes 讲 Kernel Report 已十年，距离该演讲上一次出现在议程上已两年」。这次回归，因此在圈内是个不大不小的事件。

## 演讲摘要说了什么（原文）

主办方页面上的摘要，全文只有三句：

> 「停办两年之后，《Kernel Report》回来了。**内核开发正经历一段加速变化（a period of accelerated change）的时期。**本演讲将审视内核社区正在发生什么、以及它可能走向何方，**并着眼于将于 10 月举行的 Maintainers Summit（维护者峰会）。**」

这就是目前公开的、关于本次演讲内容的**全部文字**。其余内容需看视频。

## 背景：2026 年内核社区到底在「加速变化」什么

摘要里那句「accelerated change」不是修辞。把 2026 年的公开报道串起来，内核社区今年确实被几股力量同时推着走——**以下均为公开发布的事实，标注来源，不归于本次演讲**：

**1. AI 生成的补丁把 maintainer 压到过载。** 网络子系统 maintainer **Jakub Kicinski** 在 Linux 7.3 的 pull request 里直言：「我们**完全被淹没了**（completely overwhelmed）。」他给的数据是：net 与 net-next 各合并了 **632 / 648** 个补丁，而「net-next 里**三分之一到一半**看起来是 AI 驱动的低优先级修复、清理和澄清」。（Dataconomy、Hardware Busters，2026-08）

**2. Torvalds 把它定义为「新常态」。** 2026 年 8 月，Linus 在 7.2-rc7 的公告里说那个 rc「很大」，是「多年来最大的 rc6（按提交数）」，「**我不太高兴这个规模**」——但「这就是现实：**新常态**，大量修复，其中很多是各种 AI 工具审查出来的」。他区分得很清楚：**AI 用在「审查」而非「写代码」**，补丁仍由人撰写、经子系统 maintainer 流程提交。（The Register、TechRadar，2026-08）

**3. 社区把 AI 规则写进了文档。** 2026 年 4 月，内核在长期辩论后落地 **`coding-assistants.rst`**：若 AI 参与撰写或审查补丁，需用 **`Assisted-by:`** 标签声明；AI 系统**不能**使用带法律效力的 `Signed-off-by`——**提交补丁的人承担全部责任**（bug、安全、许可）。（byteiota 等，2026-08）

**4. 一个叫 Sashiko 的 AI 审查系统被正式引入。** 由 Google 的 **Roman Gushchin** 打造的 agentic 代码审查器 **Sashiko**（2026 年 3 月发布），用 Gemini 3.1 Pro 审阅提交到 LKML 等的每个补丁，Greg Kroah-Hartman 公开背书。它**也出现在本届 Kernel Recipes 议程上**（Roman Gushchin 主讲「The Sashiko review system」）。（byteiota；Kernel Recipes 日程）

**5. Maintainers Summit（10 月）是摘要点名的落点。** 摘要特意提到「着眼于 10 月的 Maintainers Summit」。与之呼应，内核文档里有一份 **《Linux kernel project continuity》**（项目连续性）文档，规定了在极端情况下如何就「顶层内核仓库的持续管理」召集最近一届 Maintainers Summit 的受邀者与 LF TAB 讨论——**这是在为一个「分布式项目 + 中心化终审」的结构准备延续性方案**。（kernel.org 文档）

**6. 同场议程本身就是一份「加速变化」的清单。** 本届 Kernel Recipes 的其他议题包括：Steven Rostedt 讲《Futex: The good, the bad and the ugly》、SeongJae Park 讲《DAMOS: The Smart Cruise Control for RAM》、Greg KH 讲《Security in the LLM age》、Miguel Ojeda 讲《Rust for Linux》、Kairui Song 讲《Swap and Memory Reclaim》、Arnd Bergmann 讲《Large scale kernel build testing on a desktop》等——**内存回收、Rust、LLM 安全、大规模构建测试**，几乎每一条都对应着维护成本或技术栈的迁移。（Kernel Recipes 日程）

## 解读：为什么「Kernel Report 回归」值得记一笔

**1. 这份报告的价值不在「新消息」，而在「maintainer 视角的年度体检」。**

《The Kernel Report》不是发布产品，而是 Corbet 以**文档 maintainer + LWN 主编**的双重视角，对「社区正在发生什么」做一次系统性梳理。它的稀缺性来自这个**视角**：多数内核新闻是「某个补丁/某个版本」的碎片，而 Kernel Report 把它们收拢成「社区在往哪走」。停办两年后回归，本身就说明——**社区到了一个需要「重新纵览」的节点**。

**2.「加速变化」的核心，是维护者负载与 AI 补丁的张力。**

把背景串起来看，2026 年最尖锐的矛盾不是某个技术争论，而是**「AI 让产出变快」与「维护带宽固定」的错配**：Kicinski 的「完全被淹没」、Torvalds 的「新常态」、Sashiko 的引入、`coding-assistants.rst` 的落地，本质都是同一个问题的不同侧面——**当生成补丁的成本趋近于零，审查补丁的成本并没有同步下降**。摘要说「着眼 Maintainers Summit」，指向的正是这层结构性问题。

**3. 它把「治理」重新拉回视野。**

内核长期的形象是「技术自治、BDFL 终审、邮件列表文化」。但 `coding-assistants.rst`（责任归属）、`Assisted-by/Signed-off-by` 的区分（法律边界）、以及项目连续性文档（极端情况下的延续机制），说明社区正在**为「人的责任」建制度**——在 AI 参与度上升的背景下，**「谁为这行代码负责」成了治理的第一性问题**。这是比任何单个补丁都更值得跟踪的长期线索。

**4. 对读者的现实含义。**

如果你是内核/发行版的工程实践者，这次「回归」提示的是：**上游的节奏与规则正在变**（AI 署名、审查流程、维护者过载），这会向下游传导——正如同一批内核新闻里「内核因 AI 模糊测试机器人产生不实用 bug 报告而引入新 taint」所暗示的，**上游正在为「AI 参与」重新设定边界**。跟准 Kernel Report 里 maintainer 的关切，比追单个 CVE 更能预判未来的摩擦点。

一句话收尾：《The Kernel Report》停办两年后回归，摘要只有三句话，但那句「内核开发正经历一段加速变化」——配上 2026 年 Kicinski 的「完全被淹没」、Torvalds 的「新常态」和 Sashiko 的入场——已经足够说明这次回归为什么是**一个需要停下来纵览的时刻**：内核社区正同时消化 AI 补丁、维护者带宽和治理规则三件事，而 10 月的 Maintainers Summit，会是下一个观察点。
