---
title: "Asahi Linux 改 GPL：官方没提 Omarchy，DHH 说「什么都没变」"
date: 2026-11-10
slug: asahi-linux-gpl-license-omarchy-dhh
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Asahi Linux 官方《Progress Report: Linux 7.3》（James Calligeros，2026-11-07）全文 + 官方 Generative AI (LLM) Policy + 官方 Copyright/clean-room policy + Omarchy 官方《Introducing Omarchy M》（DHH，2026-09-11）+ DHH 于 2026-11-08 的 X 发言存档（Omarchy Archive / EtherNinja 索引）+ It's FOSS 报道（2026-11-08）+ OpenBSD 开发者 Bryan Steele 的公开评论 + Hacker News 讨论"
original_date: 2026-11-07
original_url: "https://asahilinux.org/2026/11/progress-report-7-3/"
description: "本文查实一件被标题党简化成「Asahi Linux 因 Omarchy 把 MIT 改成 GNU」的事。核对官方《Progress Report: Linux 7.3》（James Calligeros，2026-11-07）原文后可以确定：①改动是真的 —— 所有仓库开始迁移到 GPL v2 or later，今后只用强 copyleft；②理由也是真的 —— 有人从开发者个人 fork 里直接搬走尚在开发的功能代码、不署名发布、或用 LLM 懒改写以掩盖来源，而 MIT 明确允许、没有针对恶意行为者的例外；③**但官方全文没有出现 Omarchy、DHH 或任何项目名**，且把理由放进了一个历史类比：WINE 原本也是 MIT，2002 年因商业化专有 fork 改用 LGPL；④改许可证的动机被写成两件事 —— 前沿 AI 实验室对高质量训练数据的贪求，以及对自由软件社区的敌意，而不是某个发行版。本文也核对了 Asahi 的生成式 AI 政策（因 clean-room 逆向工程的法律风险而「广泛禁止」生成式 AI 用于实质贡献）与 DHH 的四组发言：quote 该政策后加🙄、说「Asahi 改 GPLv2 什么都没变，Linux 内核本来就是 GPLv2、Omarchy 本身是 MIT」、说 Omarchy 用 agent 加速扩展了 Asahi 的工作但「Asahi 拒绝 upstreaming」、以及「Omarchy 永远免费、没有变现计划」。同时如实记录第三方指出的问题：It's FOSS 说报告没有点名任何人也没说明历史贡献者是否同意 relicense；OpenBSD 开发者 Bryan Steele 批评此举「看似未经所有既往贡献者同意」；GPL 也拦不住已经无视 MIT 的人，它改变的是商业化收益。落点：把「没点名」写成「点名」是媒体推断；真正值得讨论的是 permissive license 在 AI 改写时代的处境，以及「贡献者同意」这个开源治理难题。"
published: true
---

> 一手来源：Asahi Linux《Progress Report: Linux 7.3》（James Calligeros，2026-11-07）
> 原文链接：<https://asahilinux.org/2026/11/progress-report-7-3/>
>
> 本文依据官方报告全文、官方 LLM 政策、DHH 发言存档、Omarchy 官方公告与第三方报道逐条核对。

## 一、先给查实结论：改动是真的，「因 Omarchy」是推断

| 说法 | 查实结果 |
|---|---|
| Asahi Linux 从 MIT 改成 GNU GPL | **真**。官方 2026-11-07 宣布，所有仓库开始迁移到 **GPL v2 or later**，今后只用强 copyleft |
| 理由是有人用 AI 洗代码 | **真**。官方原文写明「从个人 fork 里直接搬走尚在开发的功能代码，不署名发布，或用 LLM 辅助懒改写以掩盖来源」 |
| 「因 Omarchy 而改」 | **官方没说**。《Progress Report: Linux 7.3》全文**没有出现 Omarchy、DHH 或任何项目名** |
| DHH 回应了 | **真**。他 11-08 在 X 上说「改 GPLv2 什么都没变」，并引用了 Asahi 的 AI 政策加了个翻白眼 emoji |

**所以准确说法是**：Asahi 因「permissive license 被恶意利用」改许可证；媒体把 Omarchy / DHH 放进标题，是**基于时间线与公开争议的关联推断**，不是官方归因。

这点必须写在最前面 —— 你让我「查实一下」，查实的结果恰恰是：**这层因果是媒体加的**。

## 二、官方到底怎么说的

报告里那一节的标题是 **「以史为鉴」**，作者 James Calligeros，日期 2026-11-07，正文以 CC BY-SA 4.0 发布。

### 它先讲了一段 WINE 的历史

> 可能有人会惊讶：**WINE 最初也是 MIT 许可**。90 年代和 2000 年代，宽松许可的项目被科技公司视为可以随意攫取和利用的「免费地产」。WINE 也没能幸免，各种不良行为者把**商业化的专有 fork** 拿去营销和销售。WINE 团队越来越担心这些 fork（虽然它们的存在完全合法）最终会让生态碎片化到 WINE 本身难以为继。**2002 年 WINE 改用 LGPL**，以阻止更多专有 fork 出现，并鼓励直接向上游贡献。

**这段类比是整篇报告的骨架** —— 而且它正好接上了本号上一篇 Darling 那篇里 WINE 的位置：那个项目同样是兼容层、同样被拿来当参照。

### 然后讲 Asahi 自己

> Asahi Linux 启动时，本意是为 Apple Silicon 平台建立一个自由软件生态。**为了方便并鼓励 BSD 朋友们及其它自由软件操作系统参与**，我们尽可能把自家代码放在宽松的 MIT 许可下。
>
> 不幸的是，这已经不再可行。**90 年代与 2000 年代的恶意做法又抬头了**，这次在很大程度上由两件事驱动：**前沿 AI 实验室对高质量训练数据的无尽胃口**，以及**对自由软件社区的激进敌意**。

### 接着是那句最关键的事实陈述

> 一段时间以前，我们得知**多次有人试图利用我们的宽松许可来劫持我们的工作**，直接目标是**取代这个项目、并把 Apple Silicon 上的 Linux 激进变现**。在极端案例里，**尚在开发中的功能代码被直接从我们的个人 fork 里搬走**，不署名发布，或者**用 LLM 辅助懒改写以掩盖来源**。**MIT 许可明确允许这样做，也没有针对恶意行为者的例外条款。**

最后是决定：

> 我们做出了艰难的决定，开始把**所有仓库迁移到 GNU GPL 第 2 版或更新版本**。今后所有 Asahi Linux 代码**只使用强 copyleft 许可**。不从历史中学习的人，注定要重蹈覆辙。

**逐句核对下来，被点名的是「行为」而不是「人」**：搬个人 fork 里的未发布代码、不署名、LLM 改写掩盖来源、意图取代项目并变现。全文没有一个项目名。

### 顺带一个容易被忽略的点

报告里还有一句：**「我们一直以尽可能透明的方式做事 —— 财务公开、开发分支公开、进度报告公开、IRC/Matrix 房间对任何有兴趣的人开放」**。而抱怨的正是**「开发中的功能代码从个人 fork 被搬走」** —— 这两句放一起才看出刺痛在哪：** openness 本身成了被利用的入口**。这和「只要有足够多的眼睛，所有 bug 都浅显」那句乐观假设，是两种很不同的经验。

## 三、Asahi 的 AI 政策：不是「讨厌 AI」，是 clean-room 的法律风险

DHH 引用并翻白眼的那份，是官方 **Generative AI (LLM) Policy**。我读了全文，它给的理由很具体：

官方政策的大意是：Asahi Linux 依赖**净室逆向工程**来确保工作合法，对二进制反汇编与反编译有严格护栏，并**绝对禁止使用泄露材料**。LLM 与版权相关的一般问题虽未定论，但 **LLM 对逆向工程项目构成独特法律风险**：这些系统很可能违反净室要求并**污染最终代码**；「agentic」做法会放大风险，因为人可能根本不知道逆向工程过程是怎么发生的。**在逆向工程与科学里，知识「如何获得」与知识本身同样重要。**

于是：

> 由于这些法律与伦理问题，我们**广泛禁止（broadly forbid）把生成式 AI 工具用于对 Asahi Linux 的实质贡献**。执行力度视违规严重程度而定：用 LLM 起草的 GitHub issue 可能直接按政策关闭；用 LLM 解读 m1n1 trace 的贡献者会收到**第一次也是最后一次警告**；**隐瞒大量 LLM 使用的贡献者会被立即封禁**，尤其当ta可能接触过未发布的 Apple 材料时。

政策开头还列了它认为 LLM 伤害的几根支柱：软件自由、开源社区、开放的互联网、环境、数字隐私、用户同意、软件开发者本身，并指向 SourceHut 的政策作为延伸阅读。

**这和本号刚写过的 Darling `AGENTS.md` 形成了极有意思的对照**：两个项目都在做 Apple 平台的 clean-room 重实现，**都把「反汇编与写代码隔离」写成硬规则** —— 但 Darling 选择「允许 AI + 11 节约束」，Asahi 选择「广泛禁止」。**同一个法律风险，两种完全相反的治理答案。**

**所以「那个 AI 拒绝挺傻的」这句（DHH 引用的 steipete 语）如果只当作「守旧」，会漏掉它背后的法律论证。** 当然，这个论证是否成立、是否过度，是另一回事 —— 下面会写争议。

## 四、Omarchy 这边：DHH 到底说了什么

先看背景。Omarchy 是 DHH（David Heinemeier Hansson）做的、以 Arch/Hyprland 为底的 Linux 发行版，**本身是 MIT 许可**。2026-09-11 的官方公告《Introducing Omarchy M》里，DHH 写得非常直白：

公告的大意是：苹果硬件很棒，很多来到 Omarchy 的人来自 Mac，他们想**留下机器、换掉操作系统**，所以 Omarchy 要**「完成 Asahi 开创的事业」**：让 Omarchy 优雅地跑在 Apple Silicon 上，安装尽量不折腾。

公告里列出了团队与成果：原生 Mac 安装器、Omarchy Mac（M1/M2 已维护一年、800+ 人社群）、M3 Air 显示控制器、Try Omarchy 等。**这是「Omarchy 在 Apple Silicon 上扩展 Asahi 工作」的官方版本**，时间是 9 月 11 日，比许可证改动早了近两个月。

### 11-08 的四组 X 发言（按存档核对）

**① 引用 Asahi 的 AI 政策，加🙄**

DHH 引用了政策里那句「LLM 伤害软件自由、开源社区、开放互联网、环境、数字隐私、用户同意与开发者本身……我们广泛禁止生成式 AI」，跟了一个翻白眼 emoji。原帖是纯文本。

**② 「什么都没变」**（同一串回复里）

> **Asahi changing to GPLv2 changes nothing, btw. The Linux kernel is already GPLv2!** We make all the source changes we have against the Linux kernel available, as we do with anything based on Asahi. **Omarchy itself is MIT**, the most permissible license. Enjoy!

（**这一句是全文我唯一想原样保留的英文** —— 因为它是整场争议里最精炼、也最容易被断章取义的一句。译文：Asahi 改 GPLv2 什么都没变 —— **Linux 内核本来就是 GPLv2**！我们所有针对内核的源码改动、以及任何基于 Asahi 的东西，都公开了。Omarchy 本身是 MIT，最宽松的许可。Enjoy!）

**③ 「agent 加速 + Asahi 拒绝 upstreaming」**

> 我感谢 Asahi 在 Apple Silicon 上做的工作，本着最好的开源精神，我们一直在扩展它：TouchID、M3 GPU、USB-C 上的 DisplayPort、deep sleep、MacBook Neo。**但多亏 agent 加速，Asahi 拒绝 upstreaming** 🤷

这条是**引用了 steipete 的帖**：对方说「Asahi 项目本来就是关于把封闭受限的东西打开」「加新限制让别的项目更难在其上构建，不是正道；那个 AI 拒绝挺傻的」。DHH 在引号外补了自己的判断。

**④ 「Omarchy 永远免费」**

他另一条帖的大意是：Omarchy 永远免费，没有变现计划，**「我已经很有钱了」**，Omacom Foundation 是资金充足的非营利机构；唯一的幕后动机就是让 Linux 在桌面赢、做一台人人可享受的完美可塑的电脑。

**这一条要单独看**：因为 Asahi 报告里最刺人的指控正是「**把 Apple Silicon 上的 Linux 激进变现**」这项指控。DHH 这句「没有变现计划、我已经很有钱了、Omacom 是有充足资金的非营利基金会」，**在字面上正好是对那项指控的否认** —— 但 **Asahi 从未说那个人是 DHH**，所以这不算「回应指控」，只能算「对舆论场的回应」。这个区别很重要。

### DHH 那句「什么都没变」，技术上对不对？

**对，但只在他划定的范围内。** 我核了一下：

| 层 | 许可 | 改 GPL 影响 |
|---|---|---|
| Linux 内核 | **本来就是 GPLv2** | 无影响 |
| Omarchy 自身脚本 / 发行版配置 | MIT | 无影响 |
| 针对内核的源码改动 | 受内核 GPLv2 约束 | 无影响 |
| **Asahi 自家的用户态代码 / m1n1 / 驱动 / 工具** | **MIT → GPLv2+** | **这才是变动所在** |

所以「内核本来就是 GPLv2」这句是事实，但它**没有覆盖 m1n1 bootloader、Asahi 的用户态组件、安装器、驱动配套代码** —— 而报告写的正是「**所有仓库**」「今后**所有 Asahi Linux 代码**只用强 copyleft」。EtherNinja 的整理也点明了：法理上他没错（内核与 Omarchy 自身都不变），**真正的战场是 AI 写的代码能不能被上游接受**。

**换句话说：DHH 说的是「对我没影响」，不是「这改动没有意义」。** 这两个命题不能互换。

## 五、争议：改许可证这件事本身，也不是没有代价

这部分媒体标题基本不提，但 It's FOSS 和 OpenBSD 那边讲得很清楚，我如实列：

**① 既往贡献者同意问题。** It's FOSS 明确写：报告**没有点名任何人**，也**没有说明历史贡献将如何 relicense、或是否每一位既往贡献者都同意了**。OpenBSD 开发者 Bryan Steele 说得更重：

> 看到 Asahi 无缘无故烧桥真让人难过……把 m1n1 和驱动 relicense 到 GPL2-or-later，**看似没有取得所有既往贡献者的同意**，还打着「防御 AI 不良行为者」的旗号，看起来完全不诚恳、也被误导了。

**这是开源治理里最硬的一道题**：MIT 代码理论上可以被重新许可（版权持有人或持有全部贡献者授权时），但一个志愿者项目若真要「所有仓库」统一改，**逐仓库的贡献者授权是否齐备**，是个实打实的法律与信任问题。**Asahi 报告没回答它。**

**② BSD 侧被直接波及。** Asahi 当年选 MIT 的**首要理由**就是「方便 BSD 朋友们参与」；而 **OpenBSD 的 Apple Silicon 支持依赖 Asahi 的 m1n1 bootloader**。GPLv2+ 对 BSD 分支的可用性，是这次改动最直接的外部成本。Bryan Steele 的comment 之所以刺眼，正因为批评者来自当年被「特意照顾」的那一方。

**③ GPL 也拦不住已经无视 MIT 的人。** It's FOSS 自己就问了：如果问题是有人本来就不遵守 MIT，为什么会遵守 GPL？答案是 **GPL 改变的是商业化收益**：MIT 下你可以拿走代码、闭源、卖产品（只要保留版权声明）；GPL 下分发修改版必须同许可开源，**无法合法做一个闭源的付费 Apple Silicon 发行版**，而且源码必须公开 → **抄袭更容易被发现**。但它不是技术防线。

**④ 关于「不署名」有个法理细节值得记**：MIT 唯一实质条件就是**保留版权声明**，所以「剥掉署名」本身**已经违反 MIT**。Hacker News 上有人据此质疑「换成 GPL 怎么会更有用」—— 这个质疑成立，但 It's FOSS 给的回应也成立：**实际变化不在「能不能抄」，在「能不能闭源变现」**。

**⑤ 报告没有点名的两个 fork，媒体自己补了上下文**：It's FOSS 提到 **Aurora Silicon / Borealis**（Asahi HoneyKrisp Vulkan 驱动的 fork，自己注册了 `VK_DRIVER_ID_AURORA_BOREALIS`、留在自家 Mesa fork 而不上游）与 **Gravity Linux**（因 LLM 分歧从 Asahi 分出的 Fedora 系发行版，开源、不卖东西、公开标注 AI 使用、还计划驱动上游后 sun-set）。It's FOSS 特别注明：**Asahi 报告没有点名这两者**，而且 Gravity「不是报告描述的那种不良行为者」。

**这一条恰好印证了开头的结论**：连认真做报道的媒体，都得分两段写「官方说了什么」和「我们补的背景是什么」。**把两段揉成一句标题，就成了「因 Omarchy 而改」**。

## 六、把两条时间线放一起看

| 时间 | 事 |
|---|---|
| 2002 | WINE 从 MIT 改 LGPL（官方报告引用的先例） |
| 2012 | Darling 创立（另一条线，本号昨日写过） |
| 2021– | Asahi Linux 起步，选 MIT 以便 BSD 参与 |
| 2026-09-11 | Omarchy 官方《Introducing Omarchy M》：「完成 Asahi 开创的事业」 |
| 2026-11-07 | **Asahi《Progress Report: Linux 7.3》宣布全仓库转 GPLv2+，全文不点名** |
| 2026-11-08 | It's FOSS 报道；DHH 四组 X 发言（quote AI 政策🙄 / 什么都没变 / 拒绝 upstreaming / 永远免费） |
| 2026-11-09 | 多家媒体把标题写成「Asahi 对 Omarchy」；EtherNinja 明确写「报告没有点名任何人，也没提 Omarchy」 |

**关键就在 11-07 到 11-08 这 24 小时**：官方写的是「以史为鉴」加行为描述，DHH 主动接话，媒体把「接话」读成了「被指」。**一个不点名的公告 + 一个主动的回应，被拼成了因果。**

## 七、那真正值得讨论的是什么

不是「谁对谁错」，是三件事：

**① permissive license 在 AI 改写时代还成不成立。**

报告那句「**MIT 明确允许这样做，也没有针对恶意行为者的例外条款**」是整个事件的支点。MIT 的设计前提是「拿走没关系，保留声明就行」；而 LLM 让「改写以掩盖来源」的成本塌到接近零。It's FOSS 的判断是：**这可能是第一次有大型开源项目专门因为「AI 辅助的代码洗白」而转向 copyleft** —— 以往 relicense 多半是为了防云厂商转售。是否会有更多硬件使能/逆向工程项目跟进，值得盯。

**② 同一法律风险，两种治理答案。**

Asahi 用 **clean-room 法理**论证「广泛禁止生成式 AI」；Darling 用**同一套 clean-room 关切**写出 11 节 `AGENTS.md`，却选择「允许 AI + 隔离反汇编 + 人对每行负责」。**没有哪一方在否认风险，分歧在于「能不能把风险管住」**。

而 DHH 那边代表的是第三种：**agent 加速是新生产力**（他说「进入门槛与协作壁垒正在被摧毁」，还引用过 M4 MacBook Pro 由社区用 agent 独立 bring-up 的进度：10 核满频、GPU、120Hz 10-bit 原生显示、Wi-Fi、蓝牙、6 扬声器、硬解）。

**三种立场都自洽，冲突发生在「上游接不接受」这个具体接口上** —— 也就是 DHH 那句「Asahi 拒绝 upstreaming」。EtherNinja 说得很准：**法理之争其实不大，真正的故事是 AI 写的代码能否以 Asahi 接受的形式落进上游。**

**③ 开源项目的「开放」边界。**

Asahi 一边说「财务、分支、进度、聊天室全公开是自由软件的理想」，一边因为**个人 fork 里的未发布代码被搬走**而收紧许可。**这不是虚伪，是一个真实的张力**： openness 让协作成为可能，也让「还没准备好发布的工作」暴露在可被复制的位置。而 GPL 能缓解闭源变现，缓解不了「从公开的个人分支搬代码」—— 后者只能靠贡献规范、LLM 政策、以及社区信任。

## 八、结论

回到你那句「针对 omarchy 而改变 license」：

> **改动是真的，理由是真的（AI 洗代码 + 意图取代并变现），但「针对 Omarchy」是媒体与社区补上的因果，官方报告全文没点名。DHH 确实接了话，而且他的「什么都没变」在内核与 Omarchy 自身这两层上成立，却没覆盖 Asahi 自家用户态代码这个真正变动的地方。**

这篇文章我更想留下的不是站队，是那条方法论：

**读这类新闻时，先把「官方原文说了什么」和「媒体/社区补了什么」拆开。** 这次拆开之后会看到：一个用 WINE 2002 年历史做类比的许可证决定、一份基于 clean-room 法理的 AI 禁令、一个 MIT 发行版作者的主动回应、以及 BSD 侧关于「贡献者同意」的合理质疑 —— **四件事，被一个标题压成了一件。**

至于 GPL 能不能挡住 LLM 洗代码：It's FOSS 的答案我认同 —— **它挡不住复制，它改变的是「复制之后能不能合法闭源卖钱」**。而 Asahi 自己那句收尾也不像在宣称胜利，更像在承认代价：**「不从历史中学习的人，注定要重蹈覆辙。」**

---

## Sources

- Asahi Linux, *Progress Report: Linux 7.3*（James Calligeros，2026-11-07，正文 CC BY-SA 4.0）: <https://asahilinux.org/2026/11/progress-report-7-3/>
- Asahi Linux, *Generative AI (LLM) Policy*: <https://asahilinux.org/llm-policy/>
- Asahi Linux, *Copyright policy*（clean-room 说明）: <https://asahilinux.org/copyright>
- Omarchy, *Introducing Omarchy M*（DHH，2026-09-11）: <https://omarchy.org/news/2026/09/introducing-omarchy-m/>
- DHH 发言存档（2026-11-08，含 X 原帖链接）: <https://omarchyarchive.com/posts/dhh-asahi-work-expanded-gplv2-changes-nothing/> ｜ <https://omarchyarchive.com/posts/dhh-asahi-linux-llm-policy-quote/> ｜ <https://omarchyarchive.com/posts/dhh-omarchy-forever-free-no-monetization/>
- EtherNinja, *Update: DHH Says Asahi's GPL Move 'Changes Nothing' for Omarchy*（2026-11-09，明确写「报告没有点名任何人、也没提 Omarchy」）: <https://etherninja.org/update-dhh-says-asahis-gpl-move-changes-nothing-for-omarchy/>
- It's FOSS, *Asahi Linux Drops MIT and Goes Full GPL After AI Tools Were Used to Steal Unreleased Code*（Abhishek Prakash，2026-11-08）: <https://itsfoss.com/news/asahi-linux-drops-mit-for-gpl/>
- OpenBSD 开发者 Bryan Steele 的公开评论（2026-11-07，经 It's FOSS 引用）: <https://x.com/canadianbryan/status/2119165376764276869>
- Hacker News 讨论: <https://news.ycombinator.com/item?id=50401867>

### 事实边界说明

- 许可证改动（MIT → GPL v2 or later、所有仓库、只用强 copyleft）、WINE 2002 类比、MIT 选择的初衷（方便 BSD 参与）、「个人 fork 未发布代码被搬走 / 不署名 / LLM 懒改写掩盖来源 / 意图取代项目并激进变现」、以及 AI 实验室训练数据需求与社区敌意这两项动机：**全部引自 Asahi 官方报告原文**。
- **官方报告全文未出现 Omarchy、DHH 或任何被指控项目名** —— 这是本文核对后的明确结论，并得到 It's FOSS 与 EtherNinja 两处独立确认。
- DHH 的四组发言、Omarchy M 公告内容、Omarchy 自身 MIT：引自官方公告与 X 发言存档（存档为第三方社区索引，非官方目录，本文按其提供的原帖链接标注）。**「Asahi 拒绝 upstreaming」是 DHH 本人的表述（That's his characterization，EtherNinja 原话），Asahi 未回应**，本文按「一方说法」处理，未当作事实。
- 「什么都没变」的适用范围分析（内核本就 GPLv2 / Omarchy 自身 MIT / Asahi 用户态代码才是变动处）是本文基于许可结构的分析，非任何一方原话。
- 既往贡献者是否同意 relicense、BSD 侧影响、GPL 改变的是商业化收益而非阻止复制、Aurora Silicon / Gravity Linux 的上下文：引自 It's FOSS 报道与 Bryan Steele 公开评论；**It's FOSS 明确注明报告未点名这两个 fork，且 Gravity 不是报告描述的那种不良行为者**，本文保留该限定。
- 与 Darling `AGENTS.md` 的对照是本文的解读，两个项目均未作此对比。
- 本文只做事实核对与治理分析，不对任何一方作动机推断或立场背书；「因 Omarchy 而改」按媒体推断处理，未作为结论。
