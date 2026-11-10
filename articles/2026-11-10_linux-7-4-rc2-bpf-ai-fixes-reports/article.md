---
title: "Linux 内核 7.4-rc2：BPF 修复跑赢报告，Linus 没说「大部分靠 AI」"
date: 2026-11-10
slug: linux-7-4-rc2-bpf-ai-fixes-reports
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Linus Torvalds《Linux 7.4-rc2》LKML 公告（2026-11-08 19:47 EST，lkml.iu.edu / lore.kernel.org 原文，含完整 diffstat 描述与 shortlog）＋《Linux 7.4-rc1》LKML 公告（2026-11-01，lists.openwall.net 镜像）＋《Linux 7.1-rc4》LKML 公告（2026-05-17，LWN 镜像）＋ 内核官方 Documentation/process/coding-assistants.rst 与 generated-content.rst（master 分支原文）＋ docs-7.4 合并提交 14c897740388（移除 Assisted-by 强制要求、新增 AGENTS.md）＋ Phoronix 7.4-rc1 / 7.4-rc2 / 合并窗口统计 / TAINT_FORCED_BIND 回滚四篇 ＋ Tom's Hardware（Bruno Ferreira，2026-11-10）＋ The Register（Simon Sharwood，2026-11-09）"
original_date: 2026-11-08
original_url: "https://www.tomshardware.com/software/linux/linus-torvalds-says-that-ai-fixes-drove-most-of-the-progress-in-latest-linux-kernel-bpf-saw-more-ai-written-fixes-than-bug-reports-possibly-indicating-a-tidal-shift-for-open-source-maintainers-tired-of-flood-of-junk-reports"
description: "本文核对 Tom's Hardware《Linus Torvalds says that AI fixes drove most of the progress in latest Linux kernel》一文的标题与正文，回到 11 月 8 日的 7.4-rc2 公告、11 月 1 日的 7.4-rc1 公告、5 月 17 日的 7.1-rc4 公告，以及内核官方 AI 贡献政策文档。结论：标题里的「大部分进展」「AI 写的修复」「多于 bug 报告」三层都被放大了。Linus 原话是「much of this was driven by various AI fixes」，说的是 rc2 那份 diffstat 的构成；他同时明确说 rc2 体积主要由自动化的 Coccinelle 脚本更新撑大，且「以后不再重复提及 AI，可以当作默认事实」。BPF 那条来自 Alexei Starovoitov 的转述，原文是「claims」「if true」，Linus 自己加了「别屏住呼吸」。真正值得读的是政策链条：5 月安全邮件列表被 AI 报告冲到「几乎无法管理」，7.1-rc4 要求「发现 bug 就必须自己写补丁」；官方 coding-assistants.rst 把复现器、编译验证、checkpatch、Fixes 标签、不得由 AI 代签 DCO、不得由 AI 自己发信写成九步硬流程；generated-content.rst 明说维护者带宽是稀缺资源。10 月 docs-7.4 又移除了强制的 Assisted-by 标签，改为在 cover letter 里说明。11 月 rc1 说「AI 修复进入合并窗口比挤在 rc 稳定期更健康」，rc2 才出现 BPF 修复跑赢报告的苗头。这不是模型突然变强，是入口规则改了：把「报告」和「修复」绑在一起， Bot 的产能才第一次变成维护者的产能。"
published: true
---

> 一手：Linus《Linux 7.4-rc2》LKML 公告（2026-11-08）｜《Linux 7.4-rc1》（2026-11-01）｜《Linux 7.1-rc4》（2026-05-17）
> 政策：内核 `Documentation/process/coding-assistants.rst`、`generated-content.rst`、docs-7.4 合并提交 `14c897740388`
> 报道：Tom's Hardware（Bruno Ferreira，2026-11-10）｜Phoronix｜The Register
>
> 本文据 LKML 原始公告与内核仓库里的政策文档逐条核对，标题里被放大的地方会单列出来。

11 月 10 日 Tom's Hardware 发了一条很提气的标题：AI 修复推动了最新 Linux 内核的大部分进展，BPF 那边 AI 写的修复比 bug 报告还多，开源维护者被垃圾报告淹了半年，潮水终于要转向了。

把 LKML 原始公告翻出来读一遍，会发现这三层意思每层都往前多走了一步。Linus 在 11 月 8 日发 7.4-rc2 时说的话，比标题谨慎得多，也比标题有意思得多。他没有宣布 AI 赢了，他宣布的是一件更枯燥的事：内核把「报 bug」的入口改了，改了半年，BPF 这块的队列第一次开始变短。

## 一、先把 7.4-rc2 那封邮件读回原样

公告开头 Torvalds 在解释一份看起来很吓人的 diffstat：

> 这次 rc2 很大，配得上史上最大的 rc1。但 diffstat 看着还算 benign，主要是一些自动化的 coccinelle 更新撑起来的 —— 合并窗口期间就收到了，我压到 rc2 才处理，因为当时在路上不想碰（老实说回来之后也不太有动力碰）。

接着他自己把这份「大」拆掉了：那些脚本化更新基本都是一两行的改动，「所谓主导了 diffstat，只是因为摊得太开、噪声太多」。把噪声遮掉之后，形状就正常了 —— 三分之一驱动（GPU、网络、声音为主），三分之一网络加 BPF，三分之一其余（文件系统、内存管理、架构更新）。

然后才是被各家媒体反复引的那段：

> And yes, much of this was driven by various AI fixes. I think I'll stop repeating that, and we can just take it for granted.

紧跟着是 BPF 那句：

> 但这一次 Alexei 说，至少在 BPF 这边，修复进来的速度已经快过新报告了，如果属实，听着挺好。

再往下两句几乎没人引：

> 我觉得其它大多数领域还没到那一步，不过这至少是个迹象，说明潮水或许开始转了。
> 别屏住呼吸，也许可以交叉手指，盼着不用太远的将来能到那儿。

三处限定词值得标出来。`claims` 是转述，不是 Linus 自己统计的；`if true` 是他自己加的免责；`most other areas haven't reached that point yet` 直接把范围缩回 BPF 一个子系统。Tom's 标题里的「大部分进展」「AI 写的修复」「修复多于报告」，对应到原文分别是 `much of this`、含糊的 `AI fixes`、`fixes ... faster than the new reports` —— 量级、 authorship、比较对象都换了。

还有个容易被漏掉的动作：「以后不再重复提这件事，可以当作默认事实」。这不是在庆祝 AI，是在说 AI 参与的修复已经常规到不值得每周单独提一次了。同一周 Phoronix 报道 rc2 时用的说法是「看似没完没了的 AI/LLM 补丁与报告流」，也没有把它写成里程碑。

顺手核一下 shortlog：rc2 的提交列表里 389 位作者、913 个提交，Alexei Starovoitov 一个人 40 个，其中 25 条是 `bpf:` 修复、12 条是配套的 `selftests/bpf:` 测试，外加 `s390/bpf`、`libbpf` 各一条。BPF 相关提交全篇 58 条。这 40 条里大量是「修一个边界条件 + 补一个 selftest」的成对结构，正好对上后面要说的政策要求。至于「AI 写的」—— 这批补丁的 commit message 里没有统一的 AI 标记，Linus 也没有逐个标注，媒体那句「AI-written fixes」是从 `AI fixes` 推出来的，不是公告里数出来的。

## 二、标题里被放大的三处

| 媒体说法 | LKML 原文 | 差在哪 |
|---|---|---|
| AI 修复推动了「大部分进展」 | 原话是「这份 diffstat 里很大一部分由各种 AI 修复驱动」，用的是 `much of` | `much of` 不是 `most of`；`this` 指 rc2 的 diffstat 构成，不是整个版本的进展 |
| BPF 出现「更多 AI 写的修复」 | 原话是「修复进来的速度现在快过新报告」 | 比的是速率，不是数量；且未标注这些修复由 AI 撰写 |
| 「修复多于 bug 报告」 | 同上，主语是 BPF，来源是 Alexei 的转述，Linus 加了「如果属实」 | 不是全内核，不是已验证结论，是「据说」 |

Tom's 正文其实比标题老实，写了他把改动拆成三块，也说这只是「他立场的又一次强调」。问题在于传播时只剩标题。The Register 11 月 9 日那篇的落点更准：他看到的是「AI 触发的补丁洪峰可能见顶的迹象」，不是洪峰变成了生产力。

另一个反向证据也在同一封邮件里：rc2 的「大」恰恰不是 AI 撑的，是 Coccinelle 脚本。Linus 专门花了两段解释这批自动化转换只是摊得开、噪声多，遮掉之后「看着并不反常」。把这份 diffstat 当成 AI 产能的战报，方向就反了。

## 三、真正改了的是入口，不是模型

把时间线拉开，这件事的因果就清楚了。

2026 年 5 月 17 日，7.1-rc4。 Linus 在公告里专门点了一段文档更新，措辞是这半年最重的一次：

> 持续涌入的 AI 报告，基本把安全邮件列表搞得几乎无法管理，重复量巨大 —— 不同的人用同一批工具找到了同样的东西。大家的时间全花在转交给对的人，或者回一句「这个一周前／一个月前就修了」并贴上公开讨论链接。这全是毫无意义的 churn。

他给的判断很硬：AI 找到的 bug 按定义就不算秘密，放在私有列表里处理既浪费所有人时间，还因为报告者互相看不见而加剧重复。「AI 工具很好，但得真的帮上忙，而不是制造不必要的痛苦和装模作样的无用功」。最后落到一句操作指令：如果你用 AI 找到了 bug，别人大概率也找到了；想真有价值，就读文档、把补丁也写出来，在 AI 之上加点实在的东西。别做那种「随手甩一份没真弄懂的报告」的人。

政策文档把这句话写成了流程。 内核仓库里 `Documentation/process/coding-assistants.rst` 现在有一节叫「发现并修复 bug 的流程」，九步，几条是硬约束：

- AI 代理不得添加 `Signed-off-by`，只有人能依法签署 DCO，提交者要对全部 AI 生成代码负全责；
- 非 trivial 的 bug 必须先做复现器验证看起来是真的，「缺少它可能导致报告被忽略，因为发给维护者的很多未验证报告恰好是无效的」，看着不对就到此为止；
- 写修复这一步不是可选的 —— 文档原话是「除了极少数罕见情况，能找到 bug 的 AI 助手就能修它」，还建议在同一会话里连着做，因为推理上下文还在；
- 必须编译并验证修复有效（用复现器或重跑完整分析），不能引入构建警告，要过 `checkpatch.pl`；
- commit message 要写清问题、方案、`Fixes` 标签；用 `get_maintainer.pl` 找对人和列表；
- 做不到的部分必须明说（没能编译、没能测试、没做出复现器），理由是「维护者目前在分析未验证报告和未测试修复上浪费了太多时间」；
- 最后一条最狠：助手永远不能自己把任何东西发出去，结果交回报人复核。

配套的 `generated-content.rst` 把动机写得更直白：维护者和审阅者的带宽是稀缺资源，工具生成的内容要透明说明来源、输入、提示词、受影响部分和测试方式；维护者可以照常处理、直接拒绝、加严审查、降低优先级，或者要求提交者解释模型怎么训练的；「如果你不能理解并捍卫你提交的每一行，就别提交」，硬提交了维护者有权不做详细 review 就整包拒掉。

10 月 23 日，docs-7.4 合并。 这次改动反而移除了强制的 `Assisted-by` 标签要求，改成在 cover letter / changelog 里说明 AI 使用情况，同时加了一个顶层 `AGENTS.md` 软链，把编码代理指到既有规范上。DCO 和「提交者负全责」没动。别把这读成放松 —— 是把「贴标签」换成「说清楚」，重点从来不在标记，在谁对代码负责。

11 月 1 日，7.4-rc1。 合并窗口收在 19,671 个提交（Phoronix 逐版本数过，7.3 是 16,267，平常约 15,000），shortlog 2.4 万行、1.2 MB，源码树 41,605,120 行。Linus 的说法是「这理由现在已经很明显了，但我把它当成好信号」：

> 我更乐意看到 AI 触发的工作洪峰进合并窗口，而不是主要在 rc 阶段以追加修复的形式出现。希望这次窗口偏大，说明 AI 修复正在变成正常开发的一部分，而不是灌满整个稳定期的修复洪水。我觉得这个模型健康得多。

他同时留了两个非 AI 解释：7.4 可能被当成下一个 LTS，以及三分之一的 diff 是 AMD GPU 寄存器头文件（「忽略这些噪声」）。所以他明说，未必只是 AI 补丁洪峰的功劳。关于 authorship 他也说得很细：「全是 AI 发现的问题的修复，而且越来越多补丁本身也是 AI 建议的，尽管它们经常被重写」。

11 月 8 日，7.4-rc2。 「别再重复提 AI 了，当作默认事实」＋ BPF 修复跑赢报告（据 Alexei 说，如果属实）。

半年下来变的是三件事：报告入口从「谁都能甩一份」变成「发现就得连修带测」；AI 参与从需要单独标注变成默认背景；工作从 rc 稳定期前移到合并窗口。BPF 队列变短，是这套约束先在一个边界清楚、复现器好写、selftest 基础设施成熟的子系统里跑通了 —— 不是模型突然会修内核了。Tom's 自己也提了一句「内核的代码门槛比别处高、triage 人手也多」，但这句放在了文章末尾，没进标题。

## 四、为什么偏偏是 BPF

BPF 不是随机抽中的样本。

它是内核里少数自带形式化验证器的子系统：程序加载前 verifier 会逐路径检查寄存器状态、指针边界、内存访问，一个「发现」往往能直接映射到一条具体的不变量被破坏。rc2 里 Starovoitov 那 40 条就是这种形态 —— `Refuse to map an arena at address 0`、`Don't let bpf_arena_free_pages() see a half-set user range`、`Invalidate a dynptr slice when its stack buffer is written`，每条几乎都跟着一个 `selftests/bpf:` 回归用例。复现器、修复、测试三件套在同一个 patch series 里闭环，正好是 `coding-assistants.rst` 第 3 到第 5 步要的东西。

对比一下别的领域就知道这有多特殊：GPU 驱动的一堆问题依赖具体硬件和固件版本，文件系统的问题要靠负载和时序碰，内存管理的 UAF 常常得 KASAN 加长跑。这些地方「做个复现器」不是一两条 selftest 能交差的。Linus 那句「其它大多数领域还没到那一步」，说的是这个，不是模型能力分布不均。

还有一层治理差异：BPF 的维护者梯队相对集中，进入 `bpf-next` 的门禁统一。政策文档里「维护者各有裁量权」那条，在 BPF 这边能落到同一套标准上；换个松散子系统，同一个 AI 报告可能被三个维护者按三种尺度处理。`TAINT_FORCED_BIND` 那次回滚是个现成的反例：Greg Kroah-Hartman 想给 sysfs bind/unbind 加 taint，好让维护者一眼识别 syzbot 把随机设备绑到随机驱动产生的假报告，结果合进去才发现 VFIO 正常流程就靠这个接口做设备直通，只能撤掉，他自己管 VFIO 叫「crazy beast」。想用一条内核级开关滤掉噪声，很容易切到真实工作流。

## 五、别把「一个子系统的苗头」读成「全行业的转向」

Tom's 标题后半段说，这可能是被垃圾报告拖累的开源维护者盼来的潮汐转变。这个外推要更小心。

内核能扛住这波，靠的是几个别的项目多半没有的条件：几千人规模的 triage 梯队、regzbot 那套回归追踪、syzbot 多年积累的自动化复现、`get_maintainer.pl` 这种把补丁路由到对的人的工具，以及现在这份把「报告必须带修复」写死的政策。Tom's 自己在文末也承认「内核的 bug 分拣团队比一般项目大得多」。curl 那边被 AI 报告逼到调整漏洞赏金、Google 冻结开源赏金计划应对无效提交，成因不是他们没用上 AI，是没有等价的分拣带宽和入口规则。

换句话说，能抄的不是「多用 AI 修 bug」，是那九步流程里的三件事：报之前先复现、报的时候连补丁一起、做不到就明说做不到。这三件不需要大模型，也不需要维护者额外买什么工具，只要求把提交门槛从「有发现」抬到「有验证过的修复」。内核花半年把这句话从 7.1-rc4 的一顿脾气，写进了 `coding-assistants.rst`、`generated-content.rst` 和 `AGENTS.md`，才在 BPF 看到队列缩短。

至于「潮水转向」，Linus 自己给的时间尺度是「别屏住呼吸，交叉手指，盼着不用太远的将来」。一个 rc 的信号，rc3 一波新报告就能翻回去。7.4 按计划 12 月底发布，还有好几个 rc 要跑。真要观察，接下来每个 rc 里修复与新增报告的比例能不能在 BPF 之外也站住。

## 六、事实边界

- `claims` / `if true` / `most other areas haven't reached that point yet` 三处限定均出自 7.4-rc2 原文；BPF 的修复/报告比例没有公开统计口径，本文未把「跑赢」当作已验证事实。
- rc2 的 913 个提交、389 位作者、Starovoitov 40 条（25 条 `bpf:` + 12 条 `selftests/bpf:`）由公告附的 shortlog 本地统计得出；其中哪些由 AI 建议、哪些被人工重写，公告未逐条标注。
- 19,671 / 16,267 / 41,605,120 行来自 Phoronix 的 git 与 cloc 统计；「史上最大 rc1」是 Linus 在 rc2 里的原话。
- 官方政策文档取自 torvalds/linux master 分支当前内容；docs-7.4 的 `Assisted-by` 变更依据合并提交 `14c897740388`。文档会继续演进，引用以仓库为准。
- `TAINT_FORCED_BIND` 回滚据 Phoronix 与 Greg KH 的 revert patch；该机制针对 fuzzing 产生的无效配置报告，与 rc2 的 BPF 结论是两件事，本文只用来说明「一刀切滤噪」的代价。

## 七、结论

7.4-rc2 值得记的不是「AI 修复了大部分内核」，是 Linus 说以后不用再特意提 AI 了。一个技术从争议点变成背景噪声，通常不是因为它突然变强，是因为围绕它的流程终于定型：谁发现、谁复现、谁修、谁测、谁签字、谁负责，全写清楚了。

BPF 修复第一次跑赢新报告，发生在这些规则落地半年之后、一个 verifier 和 selftest 都最成熟的子系统里。它证明的是入口设计有效，不是垃圾报告问题解决了。把这个读成「开源维护者可以松口气」，恰好会把那半年真正做对的事漏掉。

## Sources

- Linus Torvalds《Linux 7.4-rc2》LKML，2026-11-08：<https://lkml.iu.edu/2611.1/01530.html> ／ <https://lore.kernel.org/lkml/CAHk-=wgAHC=GJMQm7DM0iJgUCsaMpYJ1zO2FW_+FQLcGzfYZzg@mail.gmail.com/T/#u>
- Linus Torvalds《Linux 7.4-rc1》LKML，2026-11-01：<https://lists.openwall.net/linux-kernel/2026/11/01/932>
- Linus Torvalds《Linux 7.1-rc4》LKML，2026-05-17：<https://lwn.net/Articles/1073192/>
- 内核官方 `Documentation/process/coding-assistants.rst` / `generated-content.rst`：`torvalds/linux` master；在线版 <https://docs.kernel.org/process/coding-assistants.html>
- docs-7.4 合并提交 `14c897740388216acd59477a382de327d5e27ba4`：<https://github.com/torvalds/linux/commit/14c897740388216acd59477a382de327d5e27ba4>
- Phoronix：《Linux 7.4-rc1 Released》《Linux 7.4-rc2 Released》《Linux 7.4 Merge Window Saw Nearly 20k Commits》《New Linux 7.4 Feature For Reducing AI Noise Already Reverted》
- Tom's Hardware（Bruno Ferreira，2026-11-10）：<https://www.tomshardware.com/software/linux/linus-torvalds-says-that-ai-fixes-drove-most-of-the-progress-in-latest-linux-kernel-bpf-saw-more-ai-written-fixes-than-bug-reports-possibly-indicating-a-tidal-shift-for-open-source-maintainers-tired-of-flood-of-junk-reports>
- The Register（Simon Sharwood，2026-11-09）：<https://www.theregister.com/security/2026/11/09/linus-torvalds-sees-signs-ai-prompted-patch-flood-has-peaked/>
