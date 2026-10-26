---
title: "Linux 7.4 存储栈：EXT4 换掉 buffer_head，大写入最高快一倍；而不受维护的 HPFS 被一次性删掉 6969 行"
date: 2026-10-27
slug: linux-7-4-storage-ext4-iomap-hpfs-removal
tags: [Linux内核, Linux7.4, EXT4, IOmap, buffer_head, HPFS, BFS, XFS, Btrfs, 文件系统, 存储, 性能优化, FIO, CVE-2026-97486, Wayland]
category: Linux/内核
author: FreeLAMP.com
original_source: "Phoronix 报道 + EXT4 v6 cover letter 原文（lore.kernel.org）+ HPFS 移除 patch 原文 + XFS/Btrfs/Block pull 摘要"
original_author: "Michael Larabel（Phoronix）；Zhang Yi（华为）；Ted Ts'o（ext4 维护者）；Breno Rodrigues Alves（HPFS 移除）；Christian Brauner（VFS/iomap）；Carlos Maiolino（XFS）；David Sterba（SUSE，Btrfs）"
original_date: 2026-10-26
original_url: "https://www.phoronix.com/news/Linux-7.4-EXT4"
description: "Linux 7.4 合并窗口里，存储栈同时发生两件方向相反的事：EXT4 引入了可选的 buffered IOmap 路径，把常规文件的缓冲 I/O 从 buffer_head 换成 iomap，华为的 Zhang Yi 给出的 FIO 数据里大写入最高 +105%；而另一边，无人维护的 HPFS（IBM 与微软为 OS/2 开发）被一个补丁从内核里整块删除，6969 行、23 个文件，理由包括 SMP/PREEMPT 上早已不可用和 CVE-2026-97486。本文逐条拆解这两条线，并补上 XFS 校验和的 lazy bounce buffering、Btrfs 的 Zstd 与 extent map 锁、block 层里的 Apple M4 NVMe 与软驱修复。"
published: true
---

> 来源：[Phoronix：EXT4 Lands Optional Buffered IOmap For Significant Performance Win With Large Writes](https://www.phoronix.com/news/Linux-7.4-EXT4)（**Michael Larabel，2026-10-26 05:53 EDT**）、[HPFS Is The Latest File-System Facing Possible Removal](https://www.phoronix.com/news/HPFS-For-Linux-Removal)（**2026-10-23**）、[BFS Removed With Linux 7.4](https://www.phoronix.com/news/BFS-Removed-With-Linux-7.4)（**2026-10-20**）、[XFS 小优化](https://www.phoronix.com/news/Linux-7.4-XFS)、[XFS Checksumming](https://www.phoronix.com/news/Linux-7.4-XFS-Checksumming)、[Btrfs](https://www.phoronix.com/news/Linux-7-4-Btrfs)、[Block 层](https://www.phoronix.com/news/Linux-7.4-Block)
> 一手材料：**[EXT4 v6 cover letter 全文](https://lore.kernel.org/all/20260903123543.2302999-1-yi.zhang@huaweicloud.com/)**（含完整 FIO 写/读性能表与 31 个补丁清单）、**[HPFS 移除 patch 全文](https://lore.kernel.org/lkml/20261023151850.96475-1-breno3011alves@gmail.com/)**（含 23 个文件的 diffstat）。
> 本文为**解读**。第三、四节的判断是笔者补充。

## 一句话结论

**同一个 7.4 合并窗口里，存储栈朝两个相反方向同时动了：**

> **往前的那个：EXT4 把常规文件的缓冲 I/O 从 `buffer_head` 换成 `iomap`，华为的 Zhang Yi 给出的 FIO 数据里，大写入场景最高提升 105%。**
>
> **往后的那个：HPFS —— IBM 和微软为 OS/2 开发的文件系统 —— 被一个补丁从内核里整块删除，6969 行、23 个文件。**

**而我认为这两件事其实是同一件事的两面：内核的存储栈正在「把 1990 年代的设计替换掉」，而替换的方式是「让新的先可选、旧的先出局」。**

**具体说：**

- **EXT4 的新路径不是默认开启** —— 因为它还不支持在线碎片整理、内联数据、fsverify、fscrypt、非 extent inode 和 `data=journal` 模式；**遇到这些特性会自动回落到老路径**；
- **HPFS 则已经没有「可开启」的价值了** —— **它在 SMP / PREEMPT 内核上早已不可用**，而且最近还出了一个 CVE。

**所以这不是「新换旧」，是「新路先修好，旧路再拆掉」。**

## 一、EXT4 到底换了什么：buffer_head vs iomap

**先把这两个概念说清楚，因为整篇文章的重量都压在这里。**

**Phoronix 的表述：**

> **「IOmap is the modern Linux framework for mapping file offsets to device blocks compared to the older buffer_head approach. The IOmap usage is more efficient and better integrated with Linux's folios while also not having some of the high memory overhead of buffer heads.」**

**拆开就是三层：**

| | `buffer_head`（旧） | `iomap`（新） |
|---|---|---|
| **做什么** | 把「文件偏移 → 设备块」的映射结果包在一个 `struct buffer_head` 里 | 把映射直接表达成「一个设备范围 + 一个逻辑块偏移」的描述 |
| **和 folio 的关系** | **额外的一层结构**，每个 buffer head 都要和 folio 打交道 | **原生集成 folio**，不需要中间结构 |
| **内存开销** | **每个 buffer head 都有固定开销** | 省掉这部分 |

**而这里有一个非常关键的历史包袱，藏在 patch 集本身里：**

**Zhang Yi 的 cover letter 里明确写了这一条：**

> **「HPFS uses buffer_heads, which don't handle block size > PAGE_SIZE well. Without this, mounting will hit the `BUG_ON(offset >= folio_size(folio));` in `folio_set_bh` on the first `__bread_gfp` call.」**

**——这正是 HPFS 那个 CVE-2026-97486 的成因。**

**也就是说：`buffer_head` 这个抽象已经老到会在现代 folio 语义下直接踩 `BUG_ON` 的程度。** **一个为 OS/2 写的文件系统，在 2026 年会因为「块大小超过 PAGE_SIZE」这种基础假设而在挂载时直接崩掉。**

**这就是「整块删除」这条新闻的真正技术底色：它不是「有人不喜欢 HPFS」，是「HPFS 依赖的那个抽象本身已经站不住了」。**

## 二、官方给出的性能数据：全表

**我回读了 v6 cover letter 里的完整 FIO 表（这是上游原文，不是二手报道）。测试环境：4 核虚拟机，Intel Xeon Platinum 8380，150GB RAM-backed virtual-io 块设备。**

**写测试（MiB/s）：**

| 配置 | BS | ext4+bh | ext4+iomap | delta |
|---|---|---|---|---|
| **只写 page cache，不回写** | 1k | 41.8 | 42.0 | ~0% |
| | 4k | 170 | 176 | +4% |
| | 64k | 1816 | 1981 | +9% |
| | **1m** | **4295** | **5780** | **+35%** |
| **触发回写**（dirty_background_bytes=100MB, dirty_bytes=200MB） | 1k | 42.6 | 43.2 | +2% |
| | 4k | 137 | 140 | +2% |
| | 64k | 734 | 957 | +30% |
| | **1m** | **1460** | **1683** | **+15%** |
| **RWF_DONTCACHE** | 1k | 14.6 | 15.0 | +3% |
| | 4k | 67.9 | 61.9 | **-9%** |
| | 64k | 415 | 698 | **+68%** |
| | **1m** | **1404** | **2883** | **+105%** |
| **Sync=1（每次写后 fsync）** | 1k | 0.71 | 0.60 | **-15%** |
| | 4k | 2.04 | 1.89 | **-7%** |
| | 64k | 32.6 | 32.4 | -1% |
| | 1m | 253 | 277 | +10% |
| **覆盖已有块（OW=1）** | 1k | 19.1 | 21.0 | +10% |
| | 4k | 164 | 179 | +9% |
| | 64k | 1776 | 1867 | +5% |
| | 1m | 4105 | 4879 | +19% |

**读测试（MiB/s）：**

| 场景 | BS | ext4+bh | ext4+iomap | delta |
|---|---|---|---|---|
| **READ HOLE**（读空洞） | 1k | 46.6 | 47.1 | +1% |
| | 4k | 189 | 198 | +5% |
| | 64k | 2011 | 2116 | +5% |
| | 1m | 4538 | 4684 | +3% |
| **READ DATA**（冷读） | 1k | 44.6 | 50.4 | **+13%** |
| | 4k | 178 | 182 | +2% |
| | 64k | 741 | 768 | +4% |
| | 1m | 1143 | 1210 | +6% |
| **READ PRECACHED**（热读） | 1k | 50.8 | 50.7 | ~0% |
| | 4k | 179 | 173 | **-3%** |
| | 64k | 2009 | 1989 | **-1%** |
| | 1m | 6296 | 6294 | ~0% |

**作者自己的总结句是：**

> **「Large I/O scenarios show significant write performance improvement, while small I/O in synchronous and non-cached scenarios experience a slight regression. Read performance shows no significant difference.」**

**把这张表读透，我看到三件事，而 Phoronix 的标题只说了第一件：**

### 2.1 「显著提升」的真正条件是「块尺寸够大」

**注意所有正收益几乎都出现在 64k 和 1m 上，1k 几乎全线持平甚至倒退。**

**而这两个值不是随便选的：**

- **64 KiB 是 `max_sectors_kb` 的常见上限附近，也是 NVMe 一次传输的典型规模；**
- **1 MiB 是现代 NVMe 固态盘在队列深度足够时的单次 I/O 规模。**

**换句话说：只有在「一次写很大一块」的场景里，iomap 的优势才显现。** **而这恰恰是**大文件顺序写**（复制大视频、tar 解包、数据库批量写入、容器镜像导入）的形态。

**所以如果你问「我这个场景会不会变快」，答案是：写大文件会，变小文件批量写不会。**

### 2.2 最刺眼的一个数字：+105%，而它的邻居是 -9%

**`Sync=0 OW=0 Dnc=1` 这一行：**

- **1m 块：`1404 → 2883`，+105%**
- **4k 块：`67.9 → 61.9`，-9%**

**同一个配置项（`RWF_DONTCACHE`，绕过 page cache 直接写设备），仅仅是块尺寸从 4k 变成 1m，收益就从「倒退 9%」翻到「翻倍」。**

**而 `RWF_DONTCACHE` 正是现代数据库（尤其 LSM 树系）和 NVMe 直写场景的常用标志。** **这意味着在这类工作负载上，iomap 路径的价值比普通「大文件顺序写」要大得多。**

**至于为什么 4k 会退 9%，cover letter 没有给出解释。** **我的推测（未经验证）：小尺寸下 iomap 的地址空间操作建立/销毁开销占比更高，而每次 I/O 的实际数据量太小，摊不薄。** **这是一个诚实的空白，值得上游继续查。**

### 2.3 唯一明确退化的场景：`fsync()` 密集的小写入

**`Sync=1 OW=0 Dnc=0` 这一行是全表唯一一片系统性下降：1k **-15%**、4k **-7%**、64k -1%、1m +10%。**

**而这个场景的现实对应是：小文件频繁落盘 —— 比如把一堆小文件 `fsync` 进目录、`git commit`、把 SQLite 的 journal 刷盘。**

**换句话说：如果你在 ext4 上跑「小文件 + 强持久性」的工作负载（比如某些 CI 系统、某些数据库的 WAL 刷写），这一版**可能**让你变慢。**

**不过有一个缓解事实：默认不开启。** **这个选项是 opt-in 的。**

## 三、为什么默认不开：不只是「还没写完」

**Ted Ts'o 在 ext4 pull request 里的说明写得很完整：**

> **「Add support for buffered iomap support in ext4. This is not enabled by default, but requires the `buffered_iomap` mount option, as this mode does not support online defragmentation, inline data, fsverify, fscrypt, non-extent inodes, and `data=journal` mode. If `buffered_iomap` is enabled, ext4 will fall back to the original I/O code path automatically if necessary. Large writes show significant performance improvements when buffered iomap is enabled.」**

**他列的「不支持」清单，我逐条翻译一下严重程度：**

| 不支持项 | 意味着什么 | 严重吗 |
|---|---|---|
| **online defragmentation**（在线碎片整理） | 用 iomap 的 inode 不能在线整理碎片 | **中等** —— 可以靠 `fstrim`/定期重建代替 |
| **inline data**（内联数据） | 小文件内联存储的特性不能用 | 低 —— 属于优化特性 |
| **fsverify** | 文件系统一致性校验工具不能用 | **中等偏高** —— 调试/取证场景会受限 |
| **fscrypt** | **加密文件系统不能用** | **高** —— 大量企业部署依赖它 |
| **non-extent inodes** | 非 extent 格式的老 inode 不能用 | 低 —— 现代 ext4 很少产生 |
| **`data=journal` 模式** | 整个文件写进 journal 的模式不能用 | **高** —— 极端安全场景会依赖 |

**而「会自动回落」这句是关键的可用性保证：**

> **「ext4 will fall back to the original I/O code path automatically if necessary」**

**也就是说，你可以在不逐个检查特性的情况下直接加这个 mount option，遇到不支持的场景会自动退回老路径。** **这大幅降低了「开错」的代价。**

### 3.1 ⭐ 但有一个更隐蔽的代价：`data=ordered` 也不能用了

**这一条不在 Ts'o 的列表里，但在 Zhang Yi 的原始 cover letter 里，而且它是「Key considerations」的第一条：**

> **「1. Lock ordering difference — The lock ordering of folio lock and transaction start in the iomap path is the opposite of that in the buffer_head path.」**
>
> **「2. `data=ordered` mode is not used — Two main reasons: a) The lock ordering of folio lock and transaction start for `data=ordered` mode is opposite to the iomap path, which would cause a deadlock. b) The iomap writeback path does not support partial folio submission (required by `data=ordered` mode when block size < folio size...)」**

**这一条值得单独拎出来，因为它触及的是 ext4 最核心的语义保证。**

**`data=ordered` 是 ext4 的默认挂载模式，它保证的是：写是按序到达设备的，但**数据块**先于**元数据块**落盘。** 这个保证的用途是：即使发生掉电，文件系统也不会出现「元数据说这个块有效，但数据是旧的」这种不一致。**

**而 iomap 路径因为锁序相反，无法实现这个语义 —— patch 集里专门有一个补丁叫 `ext4: do not use data=ordered mode for inodes using buffered iomap path`。**

**这意味着：** **开了 `buffered_iomap` 的 inode，掉电时的持久性保证弱于默认的 ext4。**

**⚠️ 但我要说清楚一个技术细节，避免过度解读**：这个降级是**按 inode** 生效的（有专门的状态位和 tracepoint），而不是整个文件系统一刀切。**而且这个取舍是「用持久性换吞吐」的显式选择，不是 bug。**

**我的建议是：**

- **个人机器、数据可重生成**（开发环境、CI 跑容器、下载解压大文件）→ **值得开**；
- **数据库、备份存储、有强持久性要求** → **先别开**，或者至少别在内网服务器上贸然全盘开；
- **fscrypt 用户** → **完全不要开**（直接不支持）。

**开启方式：**

```sh
# 只在本次挂载生效
sudo mount -o remount,buffered_iomap /mnt

# 想关掉
sudo mount -o remount,nobuffered_iomap /mnt
```

**（`nobuffered_iomap` 是 Zhang Yi 在原始 cover letter 里明确提到的对应开关。）**

## 四、HPFS 被删：6969 行、23 个文件

**这条比 EXT4 短，但它的信息量在「理由」而不是「动作」里。**

**patch 的作者是 Breno Rodrigues Alves，收件人抄送了 `linux-fsdevel`、`linux-kernel`，以及 Mikulas Patocka（红帽）和 Alexander Viro。** **后两位是文件系统领域的老手 —— 这不是一个无名小卒的随手提交。**

**原文说明：**

> **「The HPFS filesystem driver has been orphaned and unmaintained for a long time. An RFC on linux-fsdevel stated that HPFS is about to be removed as it has no remaining users and is no longer supported on SMP or PREEMPT kernels. Recent vulnerabilities (e.g., CVE-2026-97486) further highlight the lack of maintenance.」**
>
> **「This patch removes the driver along with its Kconfig entry, documentation, and CREDITS entries. The `HPFS_SUPER_MAGIC` value in `include/uapi/linux/magic.h` is kept for userspace ABI compatibility, and defconfig cleanups will be sent separately to the respective architecture maintainers.」**

**几个要点：**

1. **「orphaned and unmaintained for a long time」** —— 孤儿驱动，Linux 内核对「无人维护」的判定标准就是没有 MAINTAINERS 且长期无实质性提交；
2. **「no longer supported on SMP or PREEMPT kernels」** —— **这才是致命的**：HPFS 不支持 SMP/PREEMPT 内核，而现代 Linux 早就没有单处理器配置了，**所以它实际上已经不能工作**；
3. **CVE-2026-97486 加持** —— 那个 `BUG_ON(offset >= folio_size(folio))` 的崩溃；
4. **`HPFS_SUPER_MAGIC` 保留** —— **userspace ABI 兼容性**：老工具（比如 `mount`、libblkid）里硬编码的 magic number 不变，避免破坏 ABI。**这是一个很典型的、只有内核开发者才会关心的细节。**

**diffstat 也很说明问题：**

```
 fs/hpfs/alloc.c     |  582 --------------
 fs/hpfs/anode.c     |  498 ------------
 fs/hpfs/dnode.c     | 1095 ---------------------------
 fs/hpfs/namei.c     |  621 ---------------
 fs/hpfs/super.c     |  789 -------------------
 ...
 23 files changed, 6969 deletions(-)
```

**最大的一块是 `dnode.c`（1095 行）—— 那是 HPFS 的目录树实现。** **这个文件本身就是 HPFS 的历史：它是 IBM 和微软为 OS/2 写的那套「目录节点（dnode）」结构。**

### 4.1 一个有意思的注脚：删的是 HPFS，留的是 magic number

**我核对了 CVE-2026-97486 的 CVE 记录**，描述确实如上：

> **「hpfs uses buffer_heads, which don't handle block size > PAGE_SIZE well. Without this, mounting will hit the `BUG_ON(offset >= folio_size(folio));` in `folio_set_bh` on the first `__bread_gfp` call.」**

**而值得单独记一笔的是另一个 CVE —— CVE-2026-63954（HPFS 的另一个崩溃，CVSS 3.1 打分 7.8 High）：**

> **「If `hpfs_map_dnode_bitmap` fails, the code would call `hpfs_brelse4` on uninitialized quad buffer head, causing a crash.」**

**红帽的描述还补了一条：「If the uninitialized pointer is used in a read operation, an attacker might be able to read sensitive portions of memory.」**

**也就是说：一个近 20 年没人维护的驱动，在 2026 年一年里被披露了至少两个 CVE。**

**而 oss-sec 上有人做了一个 CVE 批量分诊，对 HPFS 的结论是：「HPFS mount-time crash requires a privileged mount; denial of service only; already fixed upstream.」—— **需要特权挂载、只有 DoS。**

**这正是「删除」比「继续修」更合理的场景：暴露面窄到几乎为零，但维护成本真实存在。**

### 4.2 HPFS 的来历，和 Unix 史上另一段故事的呼应

**Phoronix 的背景说明：**

> **「The High Performance File-System (HPFS) was developed by IBM and Microsoft for OS/2.」**
> **「HPFS development began nearly 40 years ago for OS/2 and hasn't really been relevant for many years.」**

**而几乎同时被删的另一个：**

> **「This removes bfs, the filesystem UnixWare uses for its boot partition. It only supports contiguous files and has no subdirectories. The only data on such a partition are kernels and bootloader settings so there is no reason to access it from Linux anymore. The uapi header stays.」** —— Christian Brauner

**这两个删除放在一起，是 Linux 内核 2026 年的一段缩影：**

| | HPFS | BFS |
|---|---|---|
| **出身** | IBM + 微软，为 OS/2 | SCO，为 UnixWare |
| **年代** | 约 1989 年起 | 1990 年代末 |
| **在 Linux 上的角色** | 读取 OS/2 分区（当年有人双系统） | UnixWare 的引导分区 |
| **今天还有人用吗** | 几乎无 | 几乎无 |
| **保留了什么** | `HPFS_SUPER_MAGIC`（uapi 头） | uapi 头 |
| **删除规模** | 6969 行 / 23 文件 | 1.2k 行 |

**两个 uapi 头都保留了 —— 这说明内核开发者在「删代码」和「不破坏 ABI」之间的分寸拿捏得很一致。**

**而关于 SCO 那一段历史，本号此前写过两篇：《Unix 为什么会分裂成两个阵营》和《商业 Unix 只剩一个还在开发》—— **UnixWare 属于那条线的末端（SCO → Caldera → Novell → 2001 年 SCO Group 破产），所以 BFS 的删除，其实是那段诉讼史在代码里的最后一块残片被清掉。**

## 五、同窗口里其他三条存储线

**EXT4 和 HPFS 是头条，但同一个 7.4 窗口里还有三条值得记。**

### 5.1 XFS 校验和：从「每次都拷贝」改成「出错才拷贝」

**这条是 VFS iomap pull request 里带进来的，Christian Brauner 的描述非常清楚：**

> **「The bulk is lazy bounce buffering for checksummed reads. XFS bounce buffers every direct read on a device that requires stable pages for checksumming so that userspace modifying the buffer while the read is in flight can't corrupt the data and fail the checksum. That burns DRAM bandwidth and CPU for copies that are almost never needed and, since the bounce buffer was a `bio_vec`, produced smaller and unaligned I/Os with 4k pages, i.e. 1 MB minus 4k. Now the read goes to the user buffer first and only a checksum failure allocates a bounce buffer and reads again. Integrity verification moves out of iomap into the filesystem so it can handle errors its own way.」**

**翻译一下这个「之前 vs 之后」：**

- **之前**：XFS 对每个 direct read 都先分配一个 bounce buffer，把数据拷进去（为了保证读飞行期间用户空间改不动这块内存），**然后才做校验和**；
- **之后**：**先把数据读进用户缓冲区，只有校验和失败时才分配 bounce buffer 重读一次。**

**而旧实现还有一个被顺带修掉的隐藏缺陷：**

> **「since the bounce buffer was a `bio_vec`, produced smaller and unaligned I/Os with 4k pages, i.e. 1 MB minus 4k」**

**——因为 bounce buffer 是 `bio_vec` 结构，用 4k 页拼出来的 1MB 其实是「1MB 减去 4k」，既小一点又不对齐。** **所以每次带校验和的 direct read，I/O 都是碎的。**

**这是一个典型的「为了一个几乎不发生的场景，付出每次都付的代价」的设计，被改成了「先乐观，出事再悲观」。**

**Phoronix 也诚实标注了：「On the patch series I didn't see any numbers for quantifying the resulting impact.」—— 没有量化数据。**

### 5.2 XFS 本身：这一轮基本是修 bug

**Carlos Maiolino 的总结很坦白：**

> **「The bulk of this are bug fixes, cleanups and code refactoring, lots of them. Majority of those bug fixes are targeting scrub and online repair code. There are no real new features here but lots of prep code for future work. There are also some small performance optimizations but nothing major.」**

**「大部分修的是 scrub 和在线修复代码」「没有真正的新特性，只有大量为未来工作的准备代码」** —— **这是典型的「主版本前的铺垫轮」描述。**

### 5.3 Btrfs：三个具体的小改进

- **Zstd 解压快约 8 MB/s**（对开启透明压缩的用户）；
- **降低了 inode extent map 锁的争用** —— **「当 Btrfs 的 shrinker 处理没有 extent map 的 inode 时，耗时减少 10–20%」**；
- **reflink 速度提升**（通过重排锁和 flush，针对更常见的情况优化）。

**这三条都不大，但方向一致：都在减少锁争用和重复拷贝。**

### 5.4 Block 层：从软驱到 Apple M4

**这一轮的 pull request 里最有意思的对照，是「新旧硬件同框」：**

**旧的一侧 —— 软盘驱动：**

> **Denis Efremov（Oracle）修复了 KASan 报告的软盘驱动栈越界问题；还修了一个「可以追溯到 2017 年一次代码重构」的回归 —— 现在软驱结构体的标志位应该被正确处理。**
>
> **Cen Zhang 在软盘驱动里发现了若干数据竞争，被「我们自己的工具」（Phoronix 委婉地写：presumably are around AI tooling）找出。**

**新的一侧 —— Apple M4：**

> **Apple M4 T8132 ANS2 NVMe 支持被合入。**

**而中间还有一个很动人的细节：**

> **「SWIM（Sander Woz Integrated Machine）驱动 —— 也就是老 Apple Macintosh 的软盘控制器 —— 的修复来自 Linux m68k 社区的 Finn Thain，缘于他最近需要用到这个驱动，却发现它『bug 多到没用』。总共处理了 33 个修复，并在 Mac Quadra 650、Mac LC III、Mac Quadra 700 和 Mac IIvx 上成功测试。」**

**——一个 1990 年代 Macintosh 的软驱驱动，在 2026 年被一个 m68k 社区的人救活了，而且是在真实硬件上测的。**

**这和 HPFS 被删放在一起，是同一条曲线的两端：一个太偏门所以出局，一个够偏门但还有人真在用所以留下。**

## 六、怎么用，以及值不值得开

### 6.1 EXT4：三个使用前提

**要开 `buffered_iomap`，你得同时满足：**

1. **文件系统没有用 `data=journal`**（`data=ordered` 是默认，会被自动降级）；
2. **没有依赖 fscrypt**（加密文件系统直接不支持）；
3. **能接受「小 I/O 密集 + fsync 密集」场景可能变慢 7–15%**。

**验证是否真的走上了新路径：**

```sh
# 挂载选项
mount | grep ' / ' | tr ',' '\n' | grep buffered_iomap

# 内核侧有专门的 tracepoint，可以在 tracefs 里确认走的是哪条路径
# ext4: ext4_iomap_disksize_pending / ext4_iomap_end_bio 等
```

**（README 里同时提到 `nobuffered_iomap` 可以显式关掉，用来对照测试。）**

### 6.2 我的实际建议

| 你的场景 | 建议 |
|---|---|
| **开发机 / 大文件下载解压 / 容器镜像导入** | **值得开** —— 这正是收益最大的场景 |
| **CI 跑构建、跑测试** | **值得试** —— 收益大且数据可重生成 |
| **数据库服务器（WAL / LSM 树）** | **谨慎** —— `RWF_DONTCACHE` + 大 I/O 收益最大，但持久性语义有变化 |
| **备份盘 / 归档存储** | **别开** —— 收益小、风险不对称 |
| **fscrypt 加密卷** | **不能开** |
| **`data=journal` 卷** | **不能开** |

**而最重要的一句是：** **因为默认不开、且不支持时会自动回落，所以「先在非关键卷上试一个下午」几乎没有风险。** **这才是这个特性值得关注的真正原因 —— 它不是「你必须升级」，而是「你可以试」。**

### 6.3 HPFS / BFS：不需要做任何事

**除非你真的在挂载 OS/2 或 UnixWare 分区 —— 而那种场景在 2026 年基本只存在于博物馆和怀旧用途。**

**唯一需要注意的是：如果你自己编译内核且带 `CONFIG_HPFS=y`，7.5 之后这个符号会消失。** **而发行版的 defconfig 清理是「另外单独发送」的**，所以**你可能会在某个版本看到「HPFS 突然不在 Kconfig 里了」**，那就是这个补丁的尾巴。

## Sources

- Phoronix：EXT4 buffered IOmap 落地（2026-10-26）：https://www.phoronix.com/news/Linux-7.4-EXT4
- Phoronix：EXT4 引入 IOmap 缓冲 I/O 路径（2026-10-12）：https://www.phoronix.com/news/EXT4-iomap-Buffered-IO
- Phoronix：HPFS 可能被移除（2026-10-23）：https://www.phoronix.com/news/HPFS-For-Linux-Removal
- Phoronix：BFS 随 7.4 被移除（2026-10-20）：https://www.phoronix.com/news/BFS-Removed-With-Linux-7.4
- Phoronix：XFS 小优化（2026-10-21）：https://www.phoronix.com/news/Linux-7.4-XFS
- Phoronix：XFS 校验和性能（2026-10-20）：https://www.phoronix.com/news/Linux-7.4-XFS-Checksumming
- Phoronix：Btrfs 优化（2026-10-19）：https://www.phoronix.com/news/Linux-7.4-Btrfs
- Phoronix：Block 层（2026-10-24）：https://www.phoronix.com/news/Linux-7.4-Block
- 一手：EXT4 v6 cover letter（含完整 FIO 表）：https://lore.kernel.org/all/20260903123543.2302999-1-yi.zhang@huaweicloud.com/
- 一手：HPFS 移除 patch：https://lore.kernel.org/lkml/20261023151850.96475-1-breno3011alves@gmail.com/
- CVE-2026-97486（hpfs set_blocksize）：https://www.cve.org/CVERecord?id=CVE-2026-97486
- CVE-2026-63954（hpfs dnode bitmap）：https://nvd.nist.gov/vuln/detail/cve-2026-63954
- 内核文档：HPFS 官方 Read/Write 文档（https://www.kernel.org/doc/html//next/filesystems/hpfs.html）

---

（说明：性能表格、patch 说明、diffstat 均为上游原文直接引用；第六节的场景分类与建议为笔者判断，其中 4k 块退化的原因推测已明确标注为未经验证。）
