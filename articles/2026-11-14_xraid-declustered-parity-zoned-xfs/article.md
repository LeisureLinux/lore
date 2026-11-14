---
title: "XRAID：给 XFS 带来 declustered parity"
date: 2026-11-14
slug: xraid-declustered-parity-zoned-xfs
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：LWN《Announcing XRAID: declustered parity RAID for zoned XFS》（jzb，2026-11-13；引 Christoph Hellwig 公告摘要、FOSSY 2026 演讲与幻灯片 raid-sucks.pdf、评论区 RaitoBezarius 指出未与 ZFS dRAID 比较）＋ LWN 邮件列表归档的原文 `[ANNOUNCE] XRAID - declustered parity RAID for (zoned) XFS`（Christoph Hellwig <hch@lst.de>，2026-11-13 12:29:13 +0100，Message-ID 20261113112913.GA31748@lst.de，发往 linux-raid / linux-xfs，抄送 linux-fsdevel / linux-kernel / xraid 列表；含全部设计段落、20 倍写性能口径、零到两重 parity、SnapRAID 实验、三个 git 仓库与 xraid 工具、Zonar 扩展）＋ Hellwig 的 FOSSY 2026 演讲页与幻灯片链接（经 LWN 转述，幻灯片本文未逐页读取）＋ OpenZFS dRAID Howto（评论区提出的对照对象，本文仅作概念说明未展开性能对比）"
original_date: 2026-11-13
original_url: "https://lwn.net/Articles/1107473/"
description: "解读 Christoph Hellwig 于 2026-11-13 公布首个公开版 XRAID：集成进 XFS 的 declustered parity RAID。文章按公告原文逐层拆解：它建在 zoned allocator 之上，用 RT subvolume 把文件数据与元数据分开，只对文件数据做 parity RAID，元数据冗余交给 MD RAID 镜像等现有堆叠驱动；RAID 层位于 Zoned XFS I/O 路径之下，把底层设备的物理 zone 聚合为 logical zone，供 Zoned XFS 当 realtime group 使用。解释 declustered RAID 的定义（D+P 的数据与校验块分布到多于 D+P 块盘的池里，所有盘参与读写与重建、 spare 容量分散），以及由此带来的快速重建：可重建到所有有空闲容量的设备、顺序动态、优先修多重冗余丢失的 zone、先数据 zone 后 parity zone 以降低降级读开销。官方口径：两个目标是支持 SMR 等 zoned 设备上的 parity RAID、提供没有固有数据完整性问题的快速 RAID；在传统硬盘与 SSD 上也能跑，未针对 SSD 优化但写入最高比 mdraid 快 20 倍。状态边界写清：开发一年半、明确「离上游提交还很远」，当前只支持 0 到 2 重 parity，用 SnapRAID parity 库做过 3 重以上实验但未纳入；xfsprogs 分支带 mkfs 支持与新的 xraid 工具，Zonar 可视化工具已扩展显示逻辑 zone 到物理 zone 的映射；三个 git 仓库在 git.infradead.org。也标注 LWN 评论区对未提 ZFS dRAID 的质疑、以及 20 倍是作者自述且本文未跑基准。结论：XRAID 值得关注不在版本号，而在它把「文件系统知道数据放在哪些 zone」这一信息用于 RAID 布局，让 SMR 的顺序写约束与校验 RAID 不再互相打架。"
published: true
---

11 月 13 日，LWN 转发了一条内核存储侧的公告：Christoph Hellwig 公布 XRAID 的首个公开版本 —— 集成进 XFS 的 declustered parity RAID。这条消息短，但信息密度高，值得按公告原文逐层拆。

先把最重要的状态说在前面：作者原话是「we aren't anywhere near ready for an upstream submission」，即离上游提交还很远，现在征求更广泛反馈与测试。所以这不是「Linux 要合并新 RAID 了」，是一个一年半工作的公开预览。

## 一、两个目标

公告开头给了两条：

1. 让 parity RAID 能跑在 zoned 设备上，例如 SMR 硬盘；
2. 做一个没有固有数据完整性问题的快速 RAID 实现。

XRAID 和 zoned XFS 一样，在传统硬盘、SSD 上也能用；只是没针对 SSD 做优化。即便如此，作者给的口径是写入最高比 mdraid 快 20 倍 —— 这是公告里的自述，LWN 未附基准，本文也没跑，读的时候请当厂商侧数字。

第二条里的「固有数据完整性问题」指向传统 RAID 的老麻烦（写洞、掉电时校验不一致一类），公告没有展开具体机制，本文不替它补论证。

## 二、为什么必须和 zoned XFS 绑在一起

关键在 zoned allocator。它用 XFS 的 RT（realtime）subvolume 把文件数据与元数据分开存放：只有文件数据落到要求顺序写的 zone 上，元数据放在常规设备或常规 zone 里。

XRAID 借这个分工做了一个很聪明的切分：

- 只对文件数据做 parity RAID —— parity RAID 在大块顺序写场景下效率最好；
- 元数据冗余交给现有堆叠驱动（例如 MD RAID 镜像）—— 小对象、原地更新更适合镜像，而不是校验条带。

实现位置上，RAID 层坐在 Zoned XFS I/O 路径下方，类似一个堆叠块驱动：把底层各设备的物理 zone 聚合成逻辑 zone，再交给 Zoned XFS 当作 realtime group 使用。

也就是说，它不是「在块设备层硬套一层 RAID，再让文件系统往里写」，而是文件系统知道数据放在哪些 zone，RAID 跟着这个布局走。SMR 的顺序写约束与 parity 条带因此不必互相打架 —— 这是整份公告最值钱的一点。

## 三、declustered 到底改了什么

公告给的定义：传统 RAID 的每组条带固定在 D 块数据盘 + P 块校验盘上；declustered RAID 把 D+P 的数据与校验块散布到一个成员盘数量多于 D+P 的存储池里，于是：

- 所有盘都参与读、写与重建，不再有「一块热备盘闲着、其余盘累死」；
- 空闲容量分散在所有盘上，而不是集中成专用 spare。

由此带来的重建优势，公告列了四条：

- 可重建到任何还有空闲容量的设备；
- 重建顺序是动态的：先修有多重冗余丢失的 zone，降低再次故障的风险；
- 先重建数据 zone，再重建 parity zone，以减少降级读的开销；
- 整体重建时间比传统 RAID 快得多，也更容易把大量磁盘放进同一个存储池。

LWN 评论区有人立刻指出：公告没提 ZFS 的 dRAID，也没做对比或致谢。这个质疑成立 —— 两者都属于 declustered 思路的不同实现，但本文未展开性能或设计差异，只把这条读者反馈记在这里。

## 四、当前能做什么、不能做什么

| 项 | 状态（公告原文） |
|---|---|
| 开发时长 | 一年半 |
| 上游提交 | 明确「远未准备好」，现在征集反馈与测试 |
| parity 数量 | 当前 0 到 2 重 |
| 3 重及以上 | 用 SnapRAID parity 库做过实验，未纳入当前版本；代码已为此预留，未来计划支持 |
| xfsprogs | 分支里带 mkfs 支持与新的 `xraid` 工具（管理设备、检查 XRAID 文件系统） |
| 可视化 | 扩展了 Zonar（zoned 文件系统可视化工具），显示每个逻辑 zone 如何映射到各设备的物理 zone |
| 代码 | `linux-xraid.git`、`xfsprogs-xraid.git`、`xfstests-xraid.git`，三个仓库都在 git.infradead.org 的 hch 用户下，分支 `xfs-raid` |
| 社区 | `xraid@lists.infradead.org` 邮件列表 |
| 资料 | FOSSY 2026 八月演讲（含 zoned 与常规设备基准），幻灯片 `raid-sucks.pdf`；LWN 说视频尚不可用 |

注意「0 parity」也在支持范围内 —— 相当于只做条带/聚合而不带校验，这点容易被「parity RAID」这个名字盖过去。

## 五、边界

- 本文依据 LWN 新闻与其邮件列表归档的公告全文；Hellwig 的 FOSSY 幻灯片与视频未逐页观看，20 倍写性能、具体基准数字均为公告自述。
- 公告未给出与 mdraid、ZFS dRAID、传统 RAID5/6 的可复现对比方法，也未说明测试硬件、盘数、zone 配置，本文不做性能推断。
- 「无固有数据完整性问题」是作者的目标表述，公告未展开实现细节或形式化论证。
- XRAID 目前是外部 git 仓库里的实验代码，不在主线内核、也不在任何发行版默认 xfsprogs 中；本文未编译、未部署、未跑 xfstests。
- LWN 新闻页正文有省略号截断，本文引用的完整段落以邮件列表原文为准。

## 六、结论

XRAID 值得记的地方在它把文件系统的布局知识下放到 RAID 层，而非又多一个 RAID 实现：zoned allocator 已经把数据与元数据分开、把数据按 zone 组织好，RAID 只需要顺着这个结构把物理 zone 聚成逻辑 zone，顺便只对适合的大块数据做校验。

这样，SMR 的顺序写要求、parity 的效率前提、以及元数据的小块原地更新，三者各得其所。再加上 declustered 布局带来的动态重建顺序，思路上比「在块层再堆一层 mdraid」干净不少。

但它离能用还早：一年半开发、明确不准备上游、最多两重 parity、性能数字只有作者口径。现在适合读代码、跑测试、提反馈，不适合规划生产存储。

## Sources

- LWN《Announcing XRAID: declustered parity RAID for zoned XFS》（2026-11-13）：<https://lwn.net/Articles/1107473/>
- 公告原文（LWN 邮件列表归档）：<https://lwn.net/ml/all/20261113112913.GA31748%40lst.de/>
- FOSSY 2026 演讲页：<https://2026.fossy.ca/schedule/presentation/451/> ｜ 幻灯片：<https://verein.lst.de/~hch/raid-sucks.pdf>
- 代码仓库：<https://git.infradead.org/users/hch/linux-xraid.git/shortlog/refs/heads/xfs-raid> ｜ <https://git.infradead.org/users/hch/xfsprogs-xraid.git/shortlog/refs/heads/xfs-raid> ｜ <https://git.infradead.org/users/hch/xfstests-xraid.git/shortlog/refs/heads/xfs-raid>
- 对照参考：OpenZFS dRAID Howto <https://openzfs.github.io/openzfs-docs/Basic%20Concepts/Pool%20Structure/dRAID%20Howto.html>
