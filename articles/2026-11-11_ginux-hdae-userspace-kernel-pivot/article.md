---
title: "Ginux：11 天造出内核之后，作者把内核冻结了"
date: 2026-11-11
slug: ginux-hdae-userspace-kernel-pivot
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：gmkurtzer/ginux 仓库当前 main 分支 README 全文（userspace kernel 规格、gVisor/seccomp/UML 对照、安全边界与局限、HDAE 说明）＋ bootable-kernel 分支 README（2026-11-04 冻结公告）＋ 分支与 tag API 核实（refs/heads/bootable-kernel = 4d4a53bbcc09、refs/tags/bootable-kernel-final = 7fb7407103cf）＋ 论文 LaTeX 源码 docs/paper/ginux-ai-systems-report.tex（仓库规模表、375 个系统调用分类、sysbench 数据、Threats to Validity、Code is not the moat）＋ Zenodo DOI 10.5281/zenodo.23682548 记录页 ＋ 作者 2026-10-27 / 10-29 / 11-05 三则 X 帖 ＋ It's FOSS 2026-10-27 报道 ＋ GitHub API 仓库元数据（2026-11-11 查询：531 stars / 61 forks / 28 issues / Apache-2.0）"
original_date: 2026-10-27
original_url: "https://github.com/gmkurtzer/ginux"
description: "本文核对 gmkurtzer/ginux 仓库与 Zenodo 技术报告，指出媒体标题「Rocky Linux 创始人 11 天用 AI 造出 Linux 兼容内核」只讲了故事的前半段：作者 Gregory Kurtzer 在 11 月 4 日冻结了那个独立 UEFI 内核、把 main 分支转向 userspace kernel，并明说代码是「可丢弃的证据」，实验对象其实是 HDAE（人类定架构/约束/验收关卡，智能体实现/运行/诊断/迭代）这套开发方法。论文 LaTeX 源码校正了二手报道的数字：11 个日历日、1,037 次提交、261 个跟踪文件、63 个 Rust 源文件、保留非生成实现与测试代码 138,790 行（含生成载荷为 174,736 行）、Markdown 文档 13,074 行、API 调用作者自估约 8,000 美元；Linux 6.12 x86-64 的 375 个系统调用号全部被分类为 82 Complete / 245 Partial / 48 Policy-denied，而不是「实现了 82 个」；sysbench 三项单 vCPU 负载在跨架构 QEMU TCG 下达到近似持平，论文自己标注为诊断性证据而非通用性能结论，且无匹配对照、无独立复现、无独立安全审计。当前 main 分支的 Ginux 是跑在 Linux 宿主上的普通进程，用 ptrace/解释器拦截受管系统调用，按版本化实例契约选择 Emulate / Mediate / Deny，把 Linux 必须维护的广 ABI 换成每个实例可审查的小契约；README 直言「Linux 不能破坏用户态，Ginux 则刻意、有选择地打破完整 Linux ABI 保证」。文章也列出新方向的能力与边界：digest-pinned OCI root、虚拟 /proc /sys/cgroup v2、Rocky Linux 10 systemd 到达 multi-user.target、4% 原生性能预算与 Gate 15 三路对照、以及它尚非生产级 agent 沙箱。"
published: true
---

> 一手：`gmkurtzer/ginux` 当前 `main` 与 `bootable-kernel` 两个分支的 README、论文 LaTeX 源码、Zenodo 记录、作者本人三则说明
> 核对：GitHub API 的分支/tag/仓库元数据（2026-11-11 查询）
>
> 媒体标题停在十月，仓库已经走到十一月。本文把两个时点分开写。

十月底有一串很抓眼的标题：CentOS 与 Rocky Linux 的创始人 Gregory Kurtzer 用 AI 在 11 天里造出一个 Linux 兼容内核，能跑 Rocky Linux 10 到 systemd，约 13.9 万行代码。故事到这儿就停了。

但把仓库今天打开，第一条就是一句 IMPORTANT：那个能直接从 UEFI 启动的独立内核，研究阶段已经结束，最终源码永久保留在 `bootable-kernel` 分支和 `bootable-kernel-final` tag，活跃开发已转向一个跑在 Linux 上的 userspace kernel。作者 11 月 5 日在 X 上说得更直白：11 天做出来的内核，「大约一周后我把它杀了」，代码是可丢弃的，实验对象是开发过程，内核只是证据。

所以这篇不该写成「AI 又干成了什么」，更该写成作者那句「Ginux wasn't the product. The development process was the experiment. The kernel was the evidence.」—— 一个被自己的成功结论推翻的项目，最后留下了什么。

## 一、先把两个时点分开

| | 十月：独立内核（已冻结） | 十一月：userspace kernel（活跃） |
|---|---|---|
| 形态 | 单个 `GINUX.EFI`，UEFI 直接启动，无需 Linux 宿主 | 宿主机上的一个普通非特权 Linux 进程 |
| 目标 | 验证 AI 能否造出能跑 Linux 用户态的内核 | 给每个实例一份更小、版本化、可审查的内核契约 |
| 状态 | 研究目标达成，2026-11-04 后不再接受新 PR/issue | 仍在提交（2026-11-11 还有 Gate 15 基准合并） |
| 保留 | `bootable-kernel` 分支 + `bootable-kernel-final` tag | `main` 分支 |

我核了 GitHub API：两个 ref 都真实存在（`4d4a53bbcc09` 与 `7fb7407103cf`），`bootable-kernel` 分支 README 顶部挂着 11 月 4 日太平洋时间 23:59 的冻结公告，写明「独立内核完成了它被创建来测试的研究目标，上游不会继续这个方向」。仓库当前 531 stars、61 forks、28 个 open issues，Apache-2.0，主语言 Rust。

名字也是个玩笑：README 说 Ginux 混合了 Linux、GPT 和 Greg，但「为了让作者的自我控制在配置好的资源限额内，`G` 官方代表 GPT」。作者后来还专门补了一句发音：`Jin-uks`。

## 二、11 天到底产出了什么：以论文源码为准

媒体数字都是从作者的 X 帖转的，而仓库里存着论文的 LaTeX 源码，数字更细，也更克制。评估对象是提交 `d11c126a...`，日期 2026-10-23：

| 指标 | 论文表格值 |
|---|---|
| 开发区间 | 11 个日历日 |
| 提交数 | 1,037 |
| 跟踪文件 | 261 |
| Rust 源文件 | 63 |
| 实现/测试代码（含生成载荷） | 174,736 行 |
| 保留的非生成实现/测试代码 | 138,790 行 |
| Markdown 文档 | 13,074 行 |
| API 调用成本 | 作者自估约 8,000 美元 |

几个常被写错的点：

- 「13.9 万行」是保留的非生成代码（138,790），不是全部产物；
- 提交数是 1,037，不是某些二手报道的 1,097；
- 8,000 美元是作者自报，论文自己声明客户端可能更新过、provider 的 token 总量未归档、对话轨迹无法精确复现，且这个数字不衡量等效人力或代码质量。

最容易被误读的是系统调用覆盖。二手稿常写成「375 个里实现了 82 个」，论文原文是：兼容性账本把 Linux 6.12 x86-64 的 375 个系统调用号全部分类 —— 82 Complete、245 Partial、48 Policy-denied。「没有漏号」不等于「都实现了」；只有 82 个被记为 complete。跑通选定的 Alpine 程序、把 Rocky Linux 10 的 systemd 带到 `multi-user.target`，按论文的说法只意味着「被测程序观察到了足够符合预期的 ABI」，不代表发行版级支持、完整系统调用一致性或完整 Linux 兼容。

性能那部分也留了很诚实的边界：在跨架构 QEMU TCG、三个窄的单 vCPU 负载下，通过 HDAE 循环修掉了严重缺陷后达到近似持平（论文举例：线程中位数从 0.078 提到 309.732 events/s，内存吞吐从 48.390 提到 620.580 MiB/s，起因之一是补上 Linux 兼容的 vDSO/vvar 计时）。但作者明写这些是诊断性证据、不是通用内核性能结果：执行环境并不等价（Linux 侧是 GenericCloud，Ginux 侧是最小 root）、样本少、未归档原始数据、没有匹配对照，也没有独立复现与独立安全审计。CPU 那 15.2% 的差异「可能只是 TCG 波动或后台工作不同」，不能读成 Ginux 更快。

方法本身叫 HDAE（Human-Directed Agentic Engineering）：外部循环由人定愿景、架构与约束、验收关卡，审查观察到的行为、改优先级或决定停止；内部循环由智能体实现、在 QEMU 里构建运行、测量分析故障、修订回归。一个持续运行的 Codex 任务（GPT-5.6 Sol）承担几乎全部实现。Kurtzer 提供的是目标、架构、Linux 兼容性目标、故障解读和停止决定 —— 他有 CentOS、Rocky Linux、Singularity/Apptainer、Warewulf 与生产基础设施的背景。论文把这点写进「效度威胁」那一节：这是单个成功观察性案例，作者既提供架构又判断结果是否可接受，存在评估者偏差；没有人类对照组、没有换模型跑一遍、没有独立重建。

## 三、为什么要自己把内核砍掉

`main` 分支 README 第一段就给了答案，而且比媒体转述锋利得多：

> Linux 必须维护一个宽泛的用户态 ABI；用 Linus 的话说，就是「我们绝不破坏用户态」。Ginux 可以坐在 Linux 之上，故意给每个受管实例一份更小的契约。

README 甚至把这句话加粗成结论：Linux 不能破坏用户态；Ginux 被设计成刻意、有选择地打破完整的 Linux ABI 保证。每个实例只拿到批准的工作负载所需的能力与接口行为，每一次偏离都是显式、带版本、可审查、可测试的，而不是偶然的兼容缺口。

具体机制是：Ginux 作为宿主机普通进程运行，宿主的 systemd 才是真正的 PID 1；它监管原生 x86-64 程序，在受管系统调用产生宿主效果之前拦截，中央分发器按实例契约三选一 —— Emulate（完全用 Ginux 自有状态应答）、Mediate（校验并转换后执行一个很窄的宿主操作）、Deny（返回配置好的 Linux 兼容错误或终止任务）。`selective` 是默认模式，只有契约允许且版本化目录独立判定为「可直达」的调用才直接落到宿主；`paranoid` 则把所有系统调用都送进分发器。

这套东西和现有方案的关系，README 自己列了对照表：seccomp 是过滤现有 ABI，UML 是在宿主进程里再跑一个完整 Linux 内核，gVisor 是用户态 application kernel（最接近），Gramine 用 manifest + library OS，Proxos 让系统调用界面上的信任放置可配置；Ginux 的差别是把声明的契约、虚拟状态、设备、资源与生命周期当成一个可审查的边界。README 明确写「不承诺完整 Linux ABI，兼容性声明只适用于具名契约、工作负载与可执行证据」。

还有个很当下的用途：把它当作 AI agent 的遏制边界。不是给 agent 宿主的完整 Linux ABI，而是把它的进程树放进一个只暴露任务所需操作与虚拟资源的实例里 —— 允许读时间、查看自己的进程、改一个指定工作区，拒绝改时钟、访问宿主文件系统、未批准的网络监听和无关设备，并记录契约决策。README 紧接着自己泼冷水：这是活跃的验证目标，不是「Ginux 现在就是生产级 agent 沙箱」的声明，契约清单、可配策略、对抗测试、性能成本与逃逸边界都还挂在 HDAE gates 上。

工程状态也比「玩具」扎实：digest-pinned OCI root、不可变文件系统索引与有界 overlay、虚拟的设备/进程/凭证/信号/同步/定时器模型、有界的虚拟 `/proc` `/sys` cgroup v2 mount namespace 视图；固定 Rocky Linux 10 systemd 基线能到 `multi-user.target`、完成受管控制台登录、通过 Rocky 仓库更新并干净关机。`make bench-compare` 每行都对着 4% 原生预算检查，Gate 15 做 native / selective / paranoid 三路对照。安全模型则如实列出：宿主内核、硬件、Ginux 可执行文件与批准配置、启动链、操作者目前都在可信范围，native backend 仍依赖宿主做 ELF 加载、地址空间、缺页、信号、调度与 ptrace —— 那些仍是宿主内核攻击面。

## 四、论文真正的结论：代码不是护城河

标题那一节直译就是「代码不是护城河」。原文的推理值得完整复述：造出一个能跑的小内核，是有界问题；维持一个生产级内核，意味着支撑多样的硬件与负载、保持接口稳定、修缺陷、协调贡献者与厂商、维持可靠的发布节奏。代码相对容易；工作流、兼容性、维护、社区才难。

作者 10 月 29 日那条 X 帖几乎是把这句话喊出来：「我没造另一个内核来和 Linux 竞争，那太蠢了……Ginux 不是产品，开发过程才是实验，内核是证据。」他还提到发布后有人开始找出 bug 和安全问题，「太棒了」—— 这恰好是社区才提供的东西。11 月 5 日那条则补了转折的动机：热度不是他的目的，把实验结果里真正有价值的部分带进更好的设计，才是。

这也解释了这次转向为什么不算「项目失败」：AI 让「可丢弃但可执行」的原型变得便宜，于是可以先用 11 天做一个极端实验去摸边界，摸到之后不背着一个半成品内核的维护债，而是把结论（每个实例应该有自己更小的契约）搬到一个不需要重写硬件生态、不需要对抗几十年 ABI 兼容承诺的位置。README 原话：原型是证据，不是把每个实验都变成产品的义务。

论文最后那句判断，比 13.9 万行代码更值得记住：AI 已经能写系统栈深处的代码，但基础设施的核心价值来自兼容性、硬件支持、审查、社区信任与长期责任；AI 扩大了「谁能造」，人决定「什么值得信」。

## 五、事实边界

- 本文所有数字取自仓库内论文 LaTeX 源码（评估提交 `d11c126a...`，2026-10-23）与当前 README；Zenodo 记录页发布于 2026-10-27，DOI `10.5281/zenodo.23682548`，PDF 直链本机返回 403，故以仓库内 tex 源码为准。
- 仓库元数据（531 stars / 61 forks / 28 issues / Apache-2.0 / Rust / pushed 2026-11-11）为 2026-11-11 查询快照，会变化。
- 本文未下载或运行 Ginux，未复现任何基准与 systemd 启动；性能与兼容性结论均为论文自报口径。
- 「82 Complete / 245 Partial / 48 Policy-denied」是论文对 Linux 6.12 x86-64 系统调用号的分类，不代表 82 个「已实现」或 375 个「已支持」。
- `main` 分支仍在活跃开发（2026-11-11 仍有 Gate 15 相关提交），本文描述的是该时点状态。

## 六、结论

十月的标题问的是「AI 能不能在 11 天里造个内核」，答案已经写进 `bootable-kernel` 分支：能，但那只是验收用例。十一月仓库给出的答案更耐读 —— 当造一个内核变得便宜，值钱的就不再是内核本身，而是知道该把边界划在哪里。

Kurtzer 把能跑 Rocky Linux 10 的独立内核冻结、转去做一个跑在 Linux 上的「小契约」层，不是认输，是把实验结论兑现了：Linux 的护城河从来不是源代码，是几十年攒下的接口稳定、硬件矩阵、审查与社区。AI 能压缩的是前者，不能压缩的是后者。

## Sources

- 仓库（当前 `main`，userspace kernel）：<https://github.com/gmkurtzer/ginux>
- 独立内核冻结分支：<https://github.com/gmkurtzer/ginux/tree/bootable-kernel> ｜最终 tag：<https://github.com/gmkurtzer/ginux/tree/bootable-kernel-final>
- 技术报告（Zenodo，2026-10-27）：<https://doi.org/10.5281/zenodo.23682548> ｜仓库内 LaTeX 源码：`docs/paper/ginux-ai-systems-report.tex`（`bootable-kernel` 分支）
- HDAE 方法仓库：<https://github.com/gmkurtzer/hdae>
- 作者说明：X `@gmkurtzer` 2026-10-27、2026-10-29、2026-11-05 三帖
- 媒体报道对照：It's FOSS《Rocky Linux Creator Built a New "Not Linux" Kernel in 11 Days Using AI》（2026-10-27）
