# Fedora 47 拟改用 Thin LTO：构建更快更省内存，还留了全量推广的伏笔

> 译文来源：Phoronix《Fedora 47 Considering Use Of Thin LTO Compiler Optimizations》，Michael Larabel，2026-09-04。原文：<https://www.phoronix.com/news/Fedora-47-Considers-Thin-LTO>

## 事件：Thin LTO 变更提案进入 Fedora 47 流程

Fedora 47 的一份变更提案正在推进：把链接时优化（LTO）从传统的 **Fat LTO 切换到 Thin LTO**，并借此让更多此前完全没有启用 LTO 的 Fedora 软件包也能享受到链接时优化。

Thin LTO（ThinLTO）比传统的"fat"链接时优化**更快、更省内存**：扩展性更好，同时保留全量 LTO 模式的大部分性能收益。编译器侧只需一个 `*``-flto=thin``*` 旗标即可启用。

## 提案怎么落地

按 [变更提案](https://fedoraproject.org/wiki/Changes/Thin-LTO-Build-Flag) 的设计：

| 要点 | 内容 |
|---|---|
| 落地机制 | 引入新的 RPM macro，启用 thin objects 的 LTO，降低采用门槛 |
| 采用方式 | 不强制任何包使用 LTO——打包者自愿决策 |
| 决策路径 | 打包者可以把 ThinLTO 加进现有包，或从 Full LTO 切换过来，对比构建时间与性能收益 |
| 后续空间 | 全系统范围的强制启用，留给未来的后续变更提案 |

这个 Fedora 47 变更提案还需要 Fedora 工程与指导委员会（**FESCo**）投票通过。

## 我们的解读：宏先行、强制殿后

**Thin 与 Fat 的差别在工程账本上。** Fat LTO 把 LLVM IR 塞进每个目标文件，链接时才做全程序优化——产物更肥、链接更慢；Thin LTO 用索引 + 并行后端的方式拆分优化，构建时间和内存占用大幅下降，性能收益保留大头。对动辄上万个包的发行版档案来说，这不是"快一点"，是**可承担与不可承担**的区别。

**"新宏 + 不强制"是 Fedora 式渐进主义。** 一上来就全量强制必然在 FESCo 上挨批；先给宏、让打包者自己算账，等采用率上来了再提系统级变更——提案正文里已经明确给强制化留了伏笔。这条路径与 Fedora 历史上别的编译旗标推广（如 `-O2`/`-fno-plt` 类调整）的节奏一致。

**对终端用户的直接影响有限，间接影响实在。** 包的性能收益取决于打包者是否跟进；但构建资源省下来的账最终反映在 koji 的构建队列和 Fedora 的 CI 时间上。对维护大量包的打包者，从 Full LTO 切 Thin 是纯赚：链接时间降、内存降、性能基本不掉。

**横向对比：** Arch 社区做过 Thin LTO 的包批量实验，Gentoo 用户手册里 LTO 与 ThinLTO 并列多时；Fedora 作为企业级上游（RHEL 的孵化器），如果 FESCo 放行且后续强制化，x86_64-v3（RHEL 10 已强制）+ Thin LTO 的组合会进一步抬高企业发行版的构建基线——这和本周 Ubuntu amd64v3 的动作是同一张拼图的两块。

**判断**：提案技术风险低、争议面小，FESCo 通过概率高；真正的看点是后续那份"系统级强制"提案何时出现。

---

*参考：[Phoronix 原文](https://www.phoronix.com/news/Fedora-47-Considers-Thin-LTO) · [Fedora Change Proposal: Thin-LTO-Build-Flag](https://fedoraproject.org/wiki/Changes/Thin-LTO-Build-Flag)*
