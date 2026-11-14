---
title: "QEMU 内存分层：先让虚拟机别被自己的迁移线程骗了"
date: 2026-11-14
slug: qemu-vm-memory-tiering-kvm-forum-2026
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Phoronix《Red Hat Working To Improve Memory Tiering For QEMU VMs To Save RAM》（Michael Larabel，2026-11-14 08:12 AM EST；Red Hat 工程师在评估几条路线，目标是内存涨价背景下让 QEMU VM 更多用 NVMe SSD 省 DRAM；Peter Xu 在温哥华 KVM Forum 2026 演讲；列出新 maccess() 系统调用、QEMU 全用户态分层、用现有内核 API 迁移冷热三条路线，称最后一条目前领先、无需改内核且 QEMU 改动小，另有补 MADV_PAGEOUT 局限的内核补丁）＋ KVM Forum 2026 官方议程页《QEMU memory tiering》（talk QPSFWD，2026-11-12 15:45–16:15，Harbour B，Peter Xu / Red Hat；摘要全文：AI 部署推高内存价格、SSD/CXL 作慢层、Linux 用 swap 提供两级层次已有几十年、可用 memcg 做 per-VM、QEMU 可把分层逻辑完全卸载给内核并搭 MGLRU 便车；但 QEMU 不感知分层，live migration 等操作会引发严重性能问题；探索新 syscall 让用户态做 tier-aware 访问、或让 QEMU 自己用 idle page tracking / userfaultfd 做全量分层，代价是重复跟踪冷热页、缺页处理效率下降、特性冲突；最终介绍基于现有接口 mincore()+MADV_PAGEOUT 的方案，以及可能的 MADV_PAGEOUT_FULL「几乎解决整个问题」，会提供对比数字并征求意见）＋ Peter Xu 在 LKML 2026-04-24 关于 `[RFC, PATCH 00/12] userfaultfd: working set tracking for VM guest memory` 的两封回信（A-bit 作为内核并发消费者不可靠、PG_idle 与 MGLRU 兼容问题、per-mm 跟踪思路；明确写出 Plan A＝提 maccess() 给 QEMU 迁移用、继续依赖内核跟踪冷热与回收，Plan B＝在 QEMU 里实现 swap、主要挑战是 MGLRU 兼容）＋ 2026-02-10 LSF/MM/BPF 议题提案「Userspace-driven memory tiering」（经搜索摘要确认 Peter Xu 提出该讨论主题，正文未完整取得）＋ MADV_COLD / MADV_PAGEOUT 的 2019 年原始补丁说明（`MADV_PAGEOUT` 立即回收私有页的非破坏性提示）＋ 2026-10 Meta 工程师 Gregory Price 的 `mm/madvise: refactor cold and pageout page table walks` 与 selftests 补丁（说明 MADV_PAGEOUT 的页表遍历、THP/大 folio 处理仍在被重构，属当前内核活跃区）＋ arXiv《Efficient Memory Tiering in a Virtual Machine》（GPAC，2506.06067v2；宿主机大页下热点基页分散/偏斜会让 host-level tiering 误判整个大页为热，guest 侧整合可降近端内存 50–70%、多 VM 性能提升 4–11%，作为学术对照）＋ QEMU 官方 guest-memfd 文档（guest_memfd 现状与 hugetlb/THP 限制，作为「别混为一谈」的边界）"
original_date: 2026-11-14
original_url: "https://www.phoronix.com/news/QEMU-VM-Memory-Tiering"
description: "解读 KVM Forum 2026 上 Peter Xu 的 QEMU memory tiering 演讲。先把状态说清：这是 Red Hat 在评估的几条路线，不是已合并特性；`MADV_PAGEOUT_FULL` 目前只在议程摘要里出现，未检到公开补丁。背景是 AI 部署推高内存价格，目标是让 QEMU VM 更多使用相对便宜的 NVMe SSD / CXL 作慢层、把 DRAM 留给热页。现成基础是 Linux 用 swap 做了几十年的两级内存层次，加 memcg 可做到 per-VM，QEMU 能把分层逻辑完全交给内核并搭 MGLRU 的便车；问题在于 QEMU 不感知分层，live migration 这类操作会顺序读遍 Guest RAM，把冷页全部误标成热页、换回 DRAM，造成严重性能抖动。文章对比三条路线：① 新增 maccess() 之类的系统调用，让 QEMU 迁移时用「不提升热度」的方式访问页；② QEMU 全用户态分层，靠 idle page tracking / userfaultfd 自己跟踪与换页，代价是冷热跟踪与缺页处理在用户态和内核重复、且与 MGLRU 等特性冲突；③ 用现成的 mincore() + MADV_PAGEOUT，无需改内核、QEMU 改动小，是目前领先方案，再用可选的 MADV_PAGEOUT_FULL 补齐 MADV_PAGEOUT 行为局限。补上 2026-04 LKML 里 Peter Xu 自述的 Plan A / Plan B 与 A-bit、PG_idle、MGLRU 兼容讨论，说明这不是临时起意。也写清边界：演讲称会给出数字，但议程页与 Phoronix 报道均未刊出可复现基准；MADV_PAGEOUT 的页表遍历与 THP 处理 2026-10 仍在内核重构；guest-memfd、CXL/NUMA 分层、GPAC 学术方案是相关但不同的线。结论：这次最值得记的不是「用 SSD 替内存」，而是虚拟化里最便宜的冷热信号会被 hypervisor 自己的维护操作污染；先让迁移线程别骗过内核的 LRU，才谈得上省 DRAM。"
published: true
---

11 月 14 日 Phoronix 报了一条虚拟化侧的动向：Red Hat 工程师在给 QEMU 虚拟机做内存分层，目标很现实 —— AI 部署把内存价格推得太高，想让相对便宜的 NVMe SSD 在更多场景里替下 DRAM，同时别把 VM 性能拖垮。

消息源自 Peter Xu 在温哥华 KVM Forum 2026（11 月 12 日 15:45–16:15，Harbour B）的 30 分钟演讲《QEMU memory tiering》。我顺手把议程摘要、4 月 LKML 的相关讨论和 `MADV_PAGEOUT` 的内核现状都对了一遍，发现这条新闻真正有意思的地方，不在「拿 SSD 当内存」，而在一个很朴素的误判：虚拟机最便宜的冷热信号，会被 hypervisor 自己污染。

先把状态钉死：这是方案探讨与几条候选路线，不是已合并的 QEMU/KVM 特性；Phoronix 也说 Red Hat 还在评估几种可能路线。演讲摘要提到会给出对比数字，但议程页与报道都没刊出可复现基准，本文不替它编数字。

## 一、现成的地基：Linux 的 swap 本来就是两级层次

摘要第一层论证很稳：Linux 用 swap 做了几十年的两级内存层次，热页留在 DRAM、冷页换到慢设备；再借 memcg 很容易做到 per-VM 的分层。这样一来 QEMU 可以把整个分层逻辑卸载给内核，还顺便吃到内核后续的所有改进 —— 摘要点名了 MGLRU（multi-gen LRU）。

这条路的好处是几乎不用 QEMU 做什么：Guest RAM 在宿主机看来就是 QEMU 进程的匿名内存，内核的 LRU、回收、swap 路径照常工作。

坏处也正来自这里：QEMU 不知道哪些页被换出去了。

## 二、问题出在 live migration

QEMU 做热迁移时，要按顺序把 Guest RAM 逐页读出来发到目标主机。对内核的 LRU 来说，这是一次「全内存顺序扫描」：原本躺在 swap/NVMe 上的冷页被依次缺页换入、访问位被置起，看起来全变成了热页。

于是分层失效：该留在慢层的冷页被抬回 DRAM，宿主内存压力陡增、迁移本身也变慢。议程摘要的原话是 QEMU「isn't tier-aware」，某些操作（点名 live migration）会造成严重性能问题，并说会在演讲里给数字。

这是虚拟化里挺典型的一类坑：测量行为本身改变了被测对象。内核通过「谁访问了这页」判断冷热，而 hypervisor 出于维护目的的遍历，在数据面上和 Guest 真的用这页没有区别。类似情况还有备份、快照、脏页位图扫描、某些模拟 DMA 路径 —— 4 月 LKML 里 Peter Xu 还专门讨论过 vhost/模拟 DMA 碰过的页「该算热」，唯独迁移该排除。

## 三、三条路线怎么取舍

摘要列了三条，Phoronix 概括为「新 `maccess()` 系统调用 / QEMU 全用户态分层 / 用现有内核 API 迁移冷热」，并说第三条目前领先。把 4 月的 LKML 回信叠起来看，取舍就更清楚：

| 路线 | 做法 | 代价 |
|---|---|---|
| A. 新 syscall（maccess / swap_access） | 给 Linux 加一个「tier-aware 访问」接口：QEMU 迁移时用这个 API 读页，内核知道这类访问不该把页提升为热；冷热跟踪与回收继续完全交给内核 | 要改内核 UAPI，得说服 mm 社区；只能覆盖 QEMU 主动改用新接口的那几处访问 |
| B. QEMU 自己管分层 | 用 idle page tracking 跟踪热度、用 userfaultfd 管缺页，QEMU 自己拥有一层慢速内存并实现换入换出 | 摘要直说会「重复劳动、效率更低、特性冲突」：用户态和内核都要跟踪冷热、都要处理缺页；Peter Xu 4 月还点名 MGLRU 兼容性是主要挑战 |
| C. 现有接口组合（领先） | `mincore()` 看哪些页还在内存 / 已被换出，`MADV_PAGEOUT` 把误抬回 DRAM 的冷页再压回慢层；不改内核、QEMU 改动小 | 依赖 `MADV_PAGEOUT` 现有语义，摘要说其行为有局限；于是再提一个可选的 `MADV_PAGEOUT_FULL`，称「几乎解决了整个问题」 |

4 月 24 日 Peter Xu 在 LKML 上其实已经把前两条写成过 Plan A / Plan B：

> Plan A：提 `maccess()` 并给 QEMU 迁移用，继续依赖内核做冷热跟踪和回收，「考虑到用户态与内核两边，目前最好也最简单」；
> Plan B：若 A 走不通，就在 QEMU 里实现 swap，主要难点是 MGLRU 兼容。

同一批讨论还解释了为什么不能直接拿页表 Accessed 位当信号：A-bit 是内核自己在并发消费的，回收路径清位、缺页路径置位，用户态读到的并不等于 Guest 的真实访问；`PG_idle` 那套在旧 LRU 上还能配合，到了 MGLRU 就对不上了。所以最终回到「让内核继续做它擅长的事，只把迁移这类伪访问摘出去」，逻辑上是自洽的。

## 四、`MADV_PAGEOUT_FULL` 现在到哪一步了

必须标清：`MADV_PAGEOUT_FULL` 目前只在 KVM Forum 议程摘要里作为「possible new」出现，我没有检到对应的公开补丁或合入记录。Phoronix 说的是「可以通过一个新内核补丁解决 `MADV_PAGEOUT` 的行为局限」，同样属于提案语气。

`MADV_PAGEOUT` 本身不新：2019 年 Minchan Kim 的补丁把它定义为「非破坏性地立即回收私有页」的 `madvise` 提示，和 `MADV_COLD` 一起补足 `MADV_DONTNEED` / `MADV_FREE`。而 2026 年 10 月 Meta 的 Gregory Price 还在发 `mm/madvise: refactor cold and pageout page table walks` 与一批 selftests，处理 THP、PTE-mapped 大 folio、folio 拆分与延迟回收的遍历逻辑 —— 说明这条路径的内核实现至今仍是活跃区，「只改一个 madvise 标志」并没有听起来那么轻。

顺带把容易混的线划开：QEMU 官方文档里的 guest-memfd 是给 KVM 更紧密管理 Guest 私有内存用的（机密计算起家，目前实验性，还不支持 hugetlb 与 THP），跟这次「用 swap/NVMe 做冷热分层」不是同一件事。CXL/NUMA 那类「把慢速内存挂成另一个 NUMA 节点」的方案，以及学术界 GPAC（把 Guest 里分散的热点基页归拢，让宿主机大页级分层别误判，论文报近端内存降 50–70%、多 VM 性能提升 4–11%）也都是相邻但不同的题目，本文不把它们的数字安到 Red Hat 这条方案上。

## 五、边界

- 演讲摘要说会提供数字并比较方案，但议程页与 Phoronix 报道均未给出具体基准；本文不引用任何性能百分比归因于该演讲。
- `maccess()`、`MADV_PAGEOUT_FULL` 均为提案/构想；`maccess()` 在 4 月 LKML 里也还是「等它准备好再说」的措辞，未检到已合入的 UAPI。
- LSF/MM/BPF 2026 的「用户态驱动内存分层」议题提案我只取到搜索摘要，正文未完整读取，仅作为「该方向年初已在社区提出」的背景。
- 「C 路线领先」是 Phoronix 对演讲口径的转述加上议程摘要的落脚顺序，不是社区决议；摘要结尾明确写「comments will be more than welcomed」，欢迎社区提意见。
- 本文未编译内核、未跑 QEMU、未复现迁移抖动；`MADV_PAGEOUT` 现状依据 2019 原始补丁与 2026-10 内核邮件。

## 六、结论

这条新闻容易被读成「QEMU 要用 SSD 省内存了」，但分层本身 Linux 早就有了，memcg 也能按 VM 切。真正的增量是：当 hypervisor 自己为了迁移而扫一遍内存时，内核的冷热判断会被骗，于是才需要 `maccess()` 这样的新接口，或者 `mincore()` + `MADV_PAGEOUT` 这样的事后纠偏。

从「给内核加新系统调用」退到「用现成接口、小改 QEMU」，再留一个 `MADV_PAGEOUT_FULL` 补丁补缺口，是一个挺务实的收敛：先不碰 UAPI，把最吵的那类伪访问处理掉。至于能不能真省下 DRAM、省多少，得等幻灯片/视频里的基准，以及后续补丁进 linux-mm 之后的讨论。

## Sources

- Phoronix《Red Hat Working To Improve Memory Tiering For QEMU VMs To Save RAM》（2026-11-14）：<https://www.phoronix.com/news/QEMU-VM-Memory-Tiering>
- KVM Forum 2026 议程《QEMU memory tiering》（talk QPSFWD，Peter Xu）：<https://pretalx.com/kvm-forum-2026/talk/QPSFWD/> ｜ 大会：<https://kvm-forum.qemu.org/>
- Peter Xu，LKML 2026-04-24 关于 userfaultfd working-set tracking 的两封回信：<https://lkml.iu.edu/2604.3/01093.html> ｜ <https://lkml.iu.edu/2604.3/01112.html>
- `MADV_COLD` / `MADV_PAGEOUT` 原始补丁（2019）：<https://lore.kernel.org/lkml/20190610111252.239156-1-minchan@kernel.org/> ｜ 2026-10 重构：<https://patchew.org/linux/20261014183024.2075709-1-gourry@gourry.net/>
- QEMU 官方 guest-memfd 文档：<https://www.qemu.org/docs/master/system/guest-memfd.html>
- 学术对照：GPAC《Efficient Memory Tiering in a Virtual Machine》：<https://arxiv.org/html/2506.06067v2>
