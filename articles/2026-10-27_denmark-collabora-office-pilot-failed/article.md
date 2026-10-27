---
title: "丹麦的 Collabora 试点静默收场：38 个人、6 个月、没有一个正式评估"
date: 2026-10-27
slug: denmark-collabora-office-pilot-failed
tags: [Collabora, LibreOffice, ODF, OOXML, 文档格式, 数字主权, 丹麦政府, cBrain, F2, 修订标记, 字体, 迁移, 政府采购, 开源软件]
category: 运维/商业
author: FreeLAMP.com
original_source: "Tom's Hardware / TechSpot / Neowin / Windows Forum / Bytes Europe 报道 + cBrain 官方公告 + Collabora 官方文档《About Converting Microsoft Office Documents》+ 丹麦工程媒体 Ingeniøren 报道（经由二手引述）"
original_date: 2026-10-26
original_url: "https://www.tomshardware.com/software/microsoft-office/denmarks-bid-to-ditch-microsoft-office-for-open-source-alternative-collabora-collapses-in-under-six-months-employees-cite-issues-with-style-formatting-and-tracking-changes"
description: "丹麦数字部 2025 年 6 月启动的 Collabora 试点（38 名员工，把 Collabora 集成进 cBrain 的 F2 案卷系统）已经静默结束：没有正式评估、没有重启计划。Ingeniøren 通过信息公开申请拿到的内部邮件显示，测试者遇到的具体问题包括：模板里的隐藏样式无法隐藏、Collabora 根本没有 Georgia 字体、补上字体后随机字符变粗体、意外换行、财务部的文件打开全空白、Ctrl+P 打印的是整个窗口而非文档。本文逐条拆解这些症状对应的格式转换根因（ODF vs OOXML、字体替换、修订标记、表格与文本框），并强调一个被多数报道模糊掉的关键点：现有证据无法证明技术问题是取消的原因，且项目从未做过评估。"
published: true
---

> 来源：[Tom's Hardware](https://www.tomshardware.com/software/microsoft-office/denmarks-bid-to-ditch-microsoft-office-for-open-source-alternative-collabora-collapses-in-under-six-months-employees-cite-issues-with-style-formatting-and-tracking-changes)（**2026-10-26**）、[TechSpot](https://www.techspot.com/news/114327-denmark-gives-up-replacing-microsoft-office-now.html)、[Neowin](https://www.neowin.net/news/denmark-has-abandoned-plans-to-ditch-microsoft-office-after-technical-problems)、[Windows Forum](https://windowsforum.com/news/denmark-ends-collabora-office-pilot-without-evaluation-lessons-for-microsoft-alternatives.449913)、[Bytes Europe](https://www.byteseu.com/2477734/)
> 一手/官方材料：**[cBrain 试点公告](https://www.cbrain.com/post/the-ministry-of-digitalization-launches-a-pilot-project-on-digital-sovereignty)**（**2025-06-19**）、**[Collabora 官方文档：About Converting Microsoft Office Documents](https://help.collaboraoffice.com/latest/he/text/shared/guide/ms_import_export_limitations.html)**
> ⚠️ **重要取数说明**：丹麦工程媒体 **Ingeniøren** 通过信息公开申请（records request）拿到了内部邮件与笔记，本文的症状细节主要来自 TechSpot/Bytes Europe 对该报道的引述，**原始邮件未直接获取**。
> 本文为**解读**。

## 一句话结论

**丹麦数字部（现研究与教育及数字化部）的 Collabora 试点已经静默收场 —— 而且收场的方式，比大多数报道写的更难看：**

**它不是「试点失败、宣布回退」，而是「试点根本没做评估，然后随着大选换政府就消失了」。**

**Windows Forum 的措辞我认为最准确：**

> **「一个部委结束了 Collabora 试点而没有完成它的评估。这留下的证据不足以判断这个替代品在那个环境里是否合适，也不足以判断更大规模迁移是否可行。」**

**而 Ingeniøren 拿到的内部邮件里，那些症状非常具体、非常可复现 —— 它们不是「用户不会用」，而是文档格式转换层的真实缺陷。**

## 一、事情本身：时间线与规模

### 1.1 起点比 headlines 里的小得多

**2025 年 6 月 19 日**，丹麦数字部启动试点。**cBrain 的官方公告写得很清楚：**

> **「作为丹麦减少对大型科技巨头依赖努力的一部分，数字事务部启动了一个试点项目，测试 Microsoft Office 的开源替代品 Collabora（基于 LibreOffice），直接集成到 cBrain 的 F2 案卷管理系统中。」**
>
> **「从 2025 年 6 月 19 日起，一组选定的部委员工将试用新方案，在 F2 内使用 Collabora 代替 Microsoft Office 套件。试点旨在评估这个开源平台能否满足核心功能需求，例如模板兼容性、文档格式、修订标记、表格，以及与 Word 格式的无缝双向转换。」**

**⭐ 注意这个设计上的一个关键点：Collabora 不是被当成「一个替代的 Word」来试的，而是被嵌进了一套现有的案卷管理系统（F2）。**

**TechSpot 的报道补充了技术细节：**

> **「丹麦软件公司 cBrain 把它接进了 F2 —— 部委员工已经在用它撰写和归档文件的案卷处理系统。」**

**这个架构选择是对的：它把「格式兼容」的问题从「日常办公」转移到了「一个受控的文档工作流」上。** **而即便如此，问题还是爆了。**

### 1.2 规模：38 人

**TechSpot：**

> **「早期报道说整个部委要在 2025 年底前弃用 Microsoft Office，但 6 月 19 日真正启动的东西要小得多 —— 一个来自该部门的 38 名志愿者组成的试点。」**

**⭐ 38 人。** **而接下来的事更说明问题：**

**2025 年 10 月**，原本要举行一次评估工作坊。**内部备忘录列出了四种可能结果，从「全面转向 Collabora」到「认定它还不够成熟」。**

**—— 结果是：测试者就这么一直用着，用到了下一年。**

### 1.3 结束：没有评估，没有重启

**TechSpot 引述现任部长的新闻发言人：**

> **「对于如今的研究、教育和数字化部的一名新闻官员来说，[Ingeniøren 报道称]试点从未按计划得到评估。」**

**Neowin 的表述：**

> **「一位发言人证实，实验已经结束，也不会再恢复。他们也证实，没有进行过将 Collabora 性能与 Microsoft Office 做基准对比的评估。」**

**Windows Forum 的补充更直接：**

> **「虽然这次试点没有进行评估，但去年年底有报道称，官员们遇到了格式问题，例如在 Collabora 中打开 Office 文档时出现空白页，反之亦然。」**

**⭐ 而「试点被终止」的直接原因是：**

**Neowin：「当今年早些时候举行大选时，这个试点被终止了。」**
**TechSpot：「今年春天，丹麦宣布大选、带来新政府之后，这个项目被草草结束。」**

## 二、⭐ 内部邮件里的症状清单：每一个都指向一个具体的技术原因

**这是整篇文章最有价值的部分 —— 因为这些症状是可以逐条映射到格式转换的具体机制的。**

**TechSpot 转述 Ingeniøren 拿到的内部邮件和笔记：**

> **「测试者几乎立刻就遇到了麻烦。拿到访问权限一小时内，其中一人就在问怎么隐藏她的 Word 模板一直藏起来的一堆额外文本样式。」**
>
> **「深挖下去发现了一个更大的缺口 —— 因为 Collabora 根本没有 Georgia，而她的模板依赖这个字体。」**
>
> **「即使 cBrain 补上了它，随机的字母还是会变粗体。意外换行也总是往文档里钻。财务部的几个文件打开完全空白。按 Ctrl+P 打印出来的是整个窗口而不是文档。到 9 月，一位测试者写道，她因为花太多时间修样式而『头发都白了』。」**

**我们把这七条症状逐条对照 Collabora 官方文档，看它们分别对应什么。**

### 2.1 「怎么隐藏一堆额外文本样式」→ 样式集的处理差异

**Collabora 官方文档列出的「Word 转换可能出问题的特性」里，第一条就是 AutoShapes，第二条是修订标记，但**样式（styles）本身是更基础的东西：**

> **「Collabora Office 能自动打开 Microsoft Office 97/2000/XP 文档。然而，一些更复杂的 Microsoft Office 文档中的布局特性和格式属性，在 Collabora Office 中处理方式不同或不受支持。因此，转换后的文件需要一定程度的手动重新格式化。」**
>
> **「预期的重新格式化量，与源文档结构和格式的复杂度成正比。」**

**⭐ 关键在于最后那半句：官方自己说的是「与复杂度成正比」。**

**而一个部委的 Word 模板 —— 那是整份文档的**全部**排版契约 —— 恰好是「复杂度最高」的那一类。**

**「隐藏样式」这个具体症状还有一个更技术的解释：Word 的模板里那些「半隐藏」的样式（`semiHidden` / `unhideWhenUsed`），在 ODF 的样式模型里没有完全对应的概念。** **所以它们会「冒出来」变成一长串可见的样式列表 —— 而这正是那位测试者一小时内就发现的问题。**

### 2.2 「Collabora 根本没有 Georgia」→ 字体替换，不是格式 bug

**⭐ 这是整组症状里最简单、也最无法辩解的一条。**

**LibreOffice 系（Collabora 是它的下游）不做字体捆绑（除少数例外），所以一台没装 Georgia 的 Linux 机器上，Georgia 会被替换成默认的衬线字体（通常是 Liberation Serif 或 DejaVu Serif）。**

**而替换的后果不是「看起来有点不一样」，是：**

- **字符宽度变了 → 每行的字符数变了 → 换行位置全部变了；**
- **行高和字距变了 → 分页位置变了 → 表格和图文框的位置全乱；**
- **⭐ 而「随机字母变粗体」是这条链上的第二级效应** —— 因为 Word 模板里常有用「加粗」表达的强调，如果字体替换导致某些字符落到不同的 fallback 链上，渲染结果就会不一致。

**⭐ 所以「补上 Georgia 之后随机字母还是变粗」这一条特别说明问题：**

**因为它意味着问题**不在字体本身**，而在模板与文档里「哪些文字该加粗」的判定逻辑**。** 这是格式语义层面（style inheritance）的差异，不是渲染层面。**

**⚠️ 而这里有一个必须点明的现实**：**服务器/瘦客户端场景下字体缺失是常态，而不是意外。** **而在 Windows 上，Georgia 是随系统字体包分发的。** **这意味着「从 Windows 迁到 Linux 桌面」这件事，字体是**第一个**会咬人的地方，而且它的影响远不止「不好看」—— 它会直接破坏分页，从而破坏所有「页码、目录、交叉引用、打印布局」相关的东西。**

### 2.3 「财务部的几个文件打开完全空白」→ 这才是 ODF/OOXML 的核心问题

**⭐ 而这一条，和 Neowin 提到的那种症状，是同一个东西的两面。**

**Neowin 的表述：**

> **「这并不特别令人意外，因为 Collabora 使用的是开放文档格式（ODF），而不是微软的专有 OOXML 规范。」**

**TechSpot 的表述更具体：**

> **「几个来自财务部的文件完全空白地打开。」**

**⭐ 我认为这里需要做一个重要的澄清，因为很多二手报道把它简化成了「Collabora 打不开 OOXML」：**

**事实是 —— Collabora Office 是能读写 OOXML 的。官方文档明确说：**

> **「Collabora Office 的最新版本可以加载和保存 Microsoft Office Open XML 文档格式，带 docx、xlsx、pptx 扩展名。」**

**所以「空白页」不是「不支持格式」，而是「转换过程中丢了东西，而丢的东西恰好是内容」。**

**这正是官方那句警告的精确含义：**

> **「下列列表给出了 Microsoft Office 特性可能造成转换困难的一般性概览。这些不会影响你使用或处理转换后文档的内容。」**
>
> **「Microsoft Word：1. AutoShapes　2. 修订标记　3. OLE 对象　4. 某些控件和 Office 表单域　5. 索引　6. 表格、框架和多栏格式　7. 超链接和书签　8. WordArt 图形　9. 动画字符/文本」**

**⭐ 关键在这句限定：「这些不会影响你使用或处理转换后文档的内容」。**

**—— 而丹麦试点里发生的正是相反的事：内容没了。**

**为什么「官方说不影响内容」却真的影响了？**

**我认为有两个可能，而且第二个更可能：**

1. **渲染 vs 存储的分离**：Collabora 可能正确地读入了 OOXML 的**内容模型**，但在**布局引擎**（排版）环节出了错 —— 比如某个 OLE 对象、AutoShape 或表格宽度约束没被正确解释，导致渲染出空白。**「内容在、页面空」正是典型的布局失败而非解析失败。**
2. **域/引用无法求值**：如果文件里有 `INCLUDETEXT`、`LINK`、或指向别处的 `REF`，在缺少源文件的环境里它们会渲染为空。**在部委场景里，「一份归档文档引用了另一份归档文档」是常态。**

**⚠️ 无论哪种，这都指向一个结论：**

> **「支持 OOXML」和「OOXML 文档在无 Windows、无 Office、无完整字体环境的机器上正确渲染」是两件事。** **前者是格式读写，后者是应用行为。**

### 2.4 「按 Ctrl+P 打印出来的是整个窗口而不是文档」→ 打印路径的集成问题

**这一条与其他所有症状都不同质。**

**⭐ 因为它**不是格式转换问题，而是打印子系统与嵌入模式（embedded）的问题** —— Collabora 被嵌在 F2 里运行时，打印走的是宿主应用的打印路径而不是 LibreOffice 自己的。**

**TechSpot 的说法：「Pressing Ctrl+P printed the entire window rather than the document.」**

**而这条最值得注意的地方在于：它是一个**架构选择的直接后果** —— 把 Collabora 作为 embedded component 而不是独立应用嵌入业务系统，就必然遇到「快捷键、打印、文件对话框、剪贴板」这些「宿主与被嵌组件的边界」问题。**

**⭐ 而这一条恰好也是整个试点最容易被修、也最有可能被「先试点再修」策略抓到的一类 —— 也就是说，试点本该在这里发挥它的作用。**

### 2.5 「到 9 月，一位测试者写道，她因为花太多时间修样式而『头发都白了』」

**⭐ 我认为这是整组证据里最重要的一条，因为它把技术问题转化成了成本问题。**

**而这一条，恰好指向了官方那句警告的经济含义：**

> **「预期的重新格式化量，与源文档结构和格式的复杂度成正比。」**

**⭐ 关键在于「成正比」这三个字。**

**一个部门的 Word 模板是整个机构多年积累的排版资产 —— 标题样式、编号体系、表格规范、图文框布局、封面页。** **而这些恰恰是「复杂度最高」的部分。**

**所以「修样式」的工作量不是常数，而是**正比于这个组织过去十年在 Word 上积累的格式化债务**。** 一个从零开始的文档不会有问题；一份三年里被三十个人改过的部委模板会有。**

**—— 这是一个「迁移成本与被迁移组织的年龄成正比」的问题。而丹麦数字部正好是一个高度模板化、文档密集的部委。**

## 三、⭐ 最容易被忽略的一点：现有证据无法证明因果

**我要特别强调这一点，因为几乎所有英文报道（Tom's Hardware、Neowin、Bytes Europe）的标题都把它写成「因为技术问题而失败」。**

**Windows Forum 的分析我认为是最克制的，也是最正确的：**

> **「有报道称员工遇到了文档格式和修订跟踪问题，但现有报道**并未确立**这些困难导致了取消，**也没有确立**丹麦政府曾把 Collabora 与 Microsoft Office 做基准对比。」**

**所以严谨的表述应该是三条，而不是一句「因为格式问题失败了」：**

| 能确认的 | 不能确认的 |
|---|---|
| 试点已结束，不会重启 | ⭐ **结束的原因是技术问题，还是大选换政府** |
| 从未做过计划中的评估 | ⭐ **Collabora 到底能不能胜任这个场景** |
| 测试者遇到了具体且严重的格式问题 | ⭐ **这些问题是否「不可修复」** |
| 38 人规模，无人今天在用它 | ⭐ **更大规模迁移是否可行** |

**⭐ 而「从未做过评估」这件事，比「试点失败」更值得讨论 —— 因为它意味着：**

> **丹麦政府实际上没有拿到任何可以用来决策的数据。** **不是数据难看，是数据不存在。**

**TechSpot 提到的那份内部备忘录 —— 列了四种可能结果的备忘录 —— 最终一份都没用上。**

**⭐ 这是一个比「试点失败」严重得多的问题，因为它意味着下一次有人想做这件事时，**没有人能引用任何经验**。** **这正是 Neowin 说的那句：「本来，一次评估可以为其他政府设立一个有意思的先例和学习经验，但看起来这完全不会发生了。」**

## 四、⭐ 这次试点其实试出了有价值的东西

**我认为如果只把它当成「丹麦失败了」来读，就浪费了这些内部邮件。**

**因为它们其实构成了一份非常具体的技术清单，可以直接转化为任何类似迁移项目的风险清单。**

### 4.1 「字体」是第一个会咬人的地方，而且后果远超美观

**⭐ 一句话结论：在服务器/瘦客户端/VDI 环境下，字体缺失不是一个外观问题，而是一个**排版正确性**问题。**

**因为字体替换会改变行宽 → 改变换行 → 改变分页 → 改变所有跨页引用、目录、页码、图文框锚点、表格跨页断裂。**

**操作建议（任何 Office→LibreOffice/Collabora 迁移都适用）：**

1. **先盘点模板依赖的全部字体**（`fc-list` 与模板实际用到的字体名求差集）；**
2. **把缺失字体作为正式依赖装进镜像，而不是指望 fallback**；
3. **⭐ 而且必须验证「替换后分页是否变化」—— 因为这才是文档「还能用」的判据。**

### 4.2 「样式」是第二大坑，而且它的成本是「正比于历史积累」的

**⭐ 所以任何这类迁移的正确做法不是「先迁移再修」，而是：**

**先找出组织内最常用的 10~20 份模板，把它们「在目标环境下打开 → 逐页对比 → 固化」当作独立项目做完，再谈推广。**

**—— 而丹麦的试点恰恰没走这一步（或者走了但没做完）。**

### 4.3 「嵌入 vs 独立应用」是一个架构决定，不是一个配置选项

**⭐ 因为一旦决定把办公套件作为 embedded component 嵌进业务系统，打印、快捷键、剪贴板、文件对话框、OLE 对象这五类问题就全部变成「你必须自己解决」的。**

**如果只是让人「打开一个桌面应用编辑文件」，这些复杂度会低得多。**

**—— 而这一点恰恰说明：** **「Collabora 是 ODF 原生、Microsoft 是 OOXML 原生」这个格式层面的差距不是主要障碍；「嵌不嵌入、字体全不全、模板复不复杂」这些工程细节才是。**

### 4.4 ⭐ 而修订标记这一项，官方自己就列在「会出问题的特性」里

**官方 Word 清单的第 2 条就是「Revision marks」。**

**⭐ 而丹麦试点**明确把「修订标记」列为了要评估的核心功能之一**（cBrain 公告里：「模板兼容性、文档格式、修订标记、表格，以及与 Word 格式的无缝双向转换」）。**

**—— 也就是说，这一条是**事先明确列出的验收项**，而它在实践中是出问题的。**

**一个有意思的观察**：**对于一个「政府部」的场景，修订标记恰恰是最重要的功能之一 —— 因为公文的审签流程依赖它。**

## 五、更广的背景：数字主权叙事的代价

**TechSpot 提到的一句话点出了这件事的真正语境：**

> **「当丹麦的数字部长去年夏天宣布她自己的员工将开始弃用 Microsoft Office 时，这条新闻远远超出了丹麦媒体的传播范围。她的部委本应先行，向其他公共机构展示离开美国软件是可行的。」**

**Neowin 补充了动机：**

> **「然而，丹麦的考量是，它想减少对美国供应商的依赖，也不想受制于一届善变的特朗普政府。」**

**⭐ 而我认为这个背景让失败的性质变了：**

**这不是一次「部门选型试错」，而是一次**国家级叙事**的第一次实地验证。**

**而第一次实地验证的结果是：38 人、6 个月、一个没做的评估。**

**—— 那么「向其他公共机构展示这是可行的」这个目标，连第一个演示案例都没有产生。**

**⭐ 这一点让我想起本号此前写过的另一件事：** **Open Group 把 macOS 从 UNIX 认证注册表上移除。** **两件事的共同点是：** **「合规/认证」与「实际可用」是两个独立维度，而只有后者能撑起生产环境。**

**丹麦这次至少还有一份内部邮件记录了真实症状 —— 这比「官员说它很好用」要诚实得多。** **而 Open Group 那边连一个字的说明都没给。**

## 六、给任何要做类似迁移的人：一份可直接用的清单

**综合这次试点暴露的问题、Collabora 官方文档的「转换困难特性清单」，以及所有类似项目的通用经验：**

### 阶段一：评估（不要跳过）

1. **先只做一件事：把组织内最常用的 10~20 份模板在目标环境下打开，逐页对比。** **这一步的成本，是后面所有成本的 90%。**
2. **列清楚「会出问题的特性」你到底用不用**：AutoShapes、修订标记、OLE 对象、某些表单域、索引、表格/框架/多栏、超链接与书签、WordArt、动画字符。**（Collabora 官方清单）**
3. **统计字体依赖，并确认「替换后分页是否变化」。**

### 阶段二：格式策略

4. **决定你的「内部格式」是 ODF 还是 OOXML。** **⚠️ 这一条是根因级的**：Collabora 原生 ODF，Microsoft 原生 OOXML。**「双向转换」不是免费的，它每次都要付一次「正比于复杂度」的代价。**
5. **⭐ 认真考虑「单向 + 边界」策略**：内部编辑用 ODF，**在明确的边界上**（提交/归档/对外发布）转一次 OOXML。**这比「全程双向」更可控 —— 因为转换点少、每次都能人工确认。**
6. **注意加密格式支持范围**：官方文档明确列出了支持的加密方式（AES128 可开，其他不支持；Word 97/2000 兼容加密、弱 XOR 等可开）。**如果你的存量文档有非 AES128 的密码保护，需要单独处理。**
7. **VBA**：Collabora **不能运行** Visual Basic 脚本（可以加载供你分析），但**部分 Excel VBA 脚本在开启 `Load/Save - VBA Properties` 后可以运行**。**如果你的流程依赖 Excel 宏，这一条要单独验证。**

### 阶段三：架构

8. **决定「嵌入业务系统」还是「独立应用」**，并据此把打印、快捷键、剪贴板、文件对话框、OLE 对象列为验收项。**（丹麦试点在「打印整个窗口」上栽了。）**
9. **⭐ 保留一个「退回路径」**：不是「换不换 Office」，而是「用 Office 只做必须用 Office 的那部分」。**Danish 的试点事实上走了这条路（虽然是非计划的），而这条路的成功率远高于全面替换。**
10. **⭐ 做评估，并且把评估写下来。** **丹麦最大的失败不是遇到格式 bug，而是「内部备忘录列了四种结果，最后一种也没用上」。**

## Sources

- Tom's Hardware：Denmark's bid to ditch Microsoft Office for Collabora collapses in under six months（2026-10-26）：https://www.tomshardware.com/software/microsoft-office/denmarks-bid-to-ditch-microsoft-office-for-open-source-alternative-collabora-collapses-in-under-six-months-employees-cite-issues-with-style-formatting-and-tracking-changes
- TechSpot：Denmark gives up on replacing Microsoft Office, for now（2026-10-26）：https://www.techspot.com/news/114327-denmark-gives-up-replacing-microsoft-office-now.html
- Neowin：Denmark has abandoned plans to ditch Microsoft Office after technical problems（2026-10-24）：https://www.neowin.net/news/denmark-has-abandoned-plans-to-ditch-microsoft-office-after-technical-problems
- Windows Forum：Denmark Ends Collabora Office Pilot Without Evaluation（2026-10-25）：https://windowsforum.com/news/denmark-ends-collabora-office-pilot-without-evaluation-lessons-for-microsoft-alternatives.449913
- Bytes Europe（2026-10-26）：https://www.byteseu.com/2477734/
- cBrain 官方公告（2025-06-19）：https://www.cbrain.com/post/the-ministry-of-digitalization-launches-a-pilot-project-on-digital-sovereignty
- Collabora 官方文档：About Converting Microsoft Office Documents：https://help.collaboraoffice.com/latest/he/text/shared/guide/ms_import_export_limitations.html
- Discover BSD 转载：New OpenBSD Port Proposed for Wine（相关联）/ New OpenBSD Port for Collabora 报道转载

---

（说明：所有引号内内容为各报道与官方文档原文引用；第二节对七个症状的逐条技术归因，除官方文档明确列出的「转换困难特性」清单外，其余为笔者基于格式转换机制的推断，已在文中标注；第三节对因果关系的谨慎表述采自 Windows Forum 的原文立场；第六节清单为笔者归纳。）
