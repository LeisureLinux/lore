# 批驳「别再建 swap 分区了」：swap 文件和 swap 分区到底差在哪

> 针对 gist [joshenders/swap.md — Stop making swap partitions, use swap files instead](https://gist.github.com/joshenders/c4960cec9c63a7b7d68ffa9543356c43)

## 0. 先把话说明白

那个 gist 的核心论点是：

> Swap files have had the same performance characteristics as swap partitions for more than 20 years… They're better in every way.

**一半对，一半错。**

- 「性能相同」在 **ext4/xfs + 4K 页 + 预分配 + SSD** 这个限定条件下，基本成立。它不是玄学，内核注释白纸黑字写着。
- 但「better in every way」和「20 年没变」是错的。当前内核（6.x master）里，swap 文件和 swap 分区至少有 **5 处路径分叉**，其中一条是 **2024 年才合入、且只对块设备生效** 的能力，能带来几十个百分点的 swap 吞吐差距。
- **而这 5 条差异，在桌面 Linux 上基本都不触发**——所以「桌面用 swapfile 完全没毛病」这个实践结论是对的，只是理由不是「两者性能永远相同」，而是「桌面的负载模型根本踩不到那些分叉」。详见第 4 节。

下面按「它对在哪 → 它错在哪 → 差多少 → 桌面为什么没毛病 → 怎么选」来拆。

---

## 1. 它对的部分：为什么 swap 文件确实不慢

很多人的直觉是「文件在文件系统里，每次读写都要过 VFS、过 journal、过块分配器，肯定慢」。**这个直觉是 2002 年之前的正确认知，现在是错的。**

关键在 `swapon` 期间做的一次性预处理。内核源码 `mm/swapfile.c`：

```c
/*
 * Whether the swapdev is an S_ISREG file or an S_ISBLK blockdev, the swap
 * extent rbtree operates in PAGE_SIZE disk blocks.  Both S_ISREG and S_ISBLK
 * swapfiles are handled *identically* after swapon time.
 *
 * For S_ISREG swapfiles, setup_swap_extents() will walk all the file's blocks
 * and will parse them into a rbtree, in PAGE_SIZE chunks.  If some stray
 * blocks are found which do not fall within the PAGE_SIZE alignment
 * requirements, they are simply tossed out - we will never use those blocks
 * for swapping.
 * ...
 * The amount of disk space which a single swap extent represents varies.
 * Typically it is in the 1-4 megabyte range.  So we can have hundreds of
 * extents in the rbtree. - akpm.
 */
```

机制要点：

1. `swapon` 时，内核把 swap 文件**所有的物理块映射**一次性读出来，建成一棵 `swap_extent` 红黑树（`generic_swapfile_activate()`）。
2. 运行期 `swap_writepage()` / `swap_read_folio()` 只做两件事：用 `map_swap_page()` 把「swap slot 偏移」换算成「磁盘 LBA」，然后**直接向块设备发 bio**。
3. 这条路径 **不经过** VFS 写路径、不经过 page cache、不经过文件系统 journal、不触发块分配。

所以对 4K 页的读写来说，swap 文件和 swap 分区走的几乎是同一段代码。gist 引用的那段注释是真实的。

**但请注意注释的措辞**：`handled identically` 指的是 **swap extent 层**。这不是「所有路径都相同」的承诺，而下面这些地方内核是显式分叉的。

---

## 2. 它错的部分：内核里真实存在的 5 处分叉

### 2.1 大页换出：swap 文件根本拿不到 order > 0 的 slot（最重要）

这是最硬的一条，而且它**正好戳破「20 年没变」**——这项能力 2024 年才进主线。

当前 master `mm/swapfile.c`，`cluster_alloc_swap_entry()`：

```c
struct folio *folio = ...;
unsigned int order = likely(folio) ? folio_order(folio) : 0;
unsigned int offset = SWAP_ENTRY_INVALID, found = SWAP_ENTRY_INVALID;

/*
 * Swapfile is not block device so unable
 * to allocate large entries.
 */
if (order && !(si->flags & SWP_BLKDEV))
    return 0;
```

而 `SWP_BLKDEV` 只有块设备才会被置位：

```c
if (S_ISBLK(inode->i_mode)) {
    si->bdev = I_BDEV(inode);
    ...
    si->flags |= SWP_BLKDEV;
} else if (S_ISREG(inode->i_mode)) {
    si->bdev = inode->i_sb->s_bdev;   // 普通文件：没有 SWP_BLKDEV
}
```

**后果**：

- 现代内核默认开 mTHP（multi-size THP，常见 64K 匿名大页）。内存回收时，内核想把一个 64K folio **整体**换出，需要在 swap 里找 `order=4`（16 个连续 slot）的空间。
- 在 swap **分区**上，只要设备是非旋转设备（SSD/NVMe），分配器能给出连续 slot，大页整体落盘。
- 在 swap **文件**上，分配器直接返回 0 → 内核只能先 `split_huge_page()` 拆成 16 个 4K 页，再一页一页换出。

代价是什么？Ryan Roberts 在合入该系列（[PATCH v4 0/6 Swap-out mTHP without splitting](https://lwn.net/ml/linux-kernel/20240311150058.1122862-1-ryan.roberts@arm.com)，2024-03）时的实测数据，Ampere Altra / 8 vCPU / 35G 块设备做 swap，usemem 70 进程压测相对 4K 基线的提升：

| 分配粒度 | 改前（拆分） | 改后（不拆分） |
|---|---|---|
| 4K page | 0.0% | +1.4% |
| 64K mTHP | **−14.6%** | **+44.2%** |
| 2M THP | +87.4% | +97.7% |

也就是说：**用 swap 文件，你会长期停在「64K mTHP 反而更慢 15%」那一列，并且永远拿不到后面那 +44%**。因为换出时被拆散，换入时也就无法大页回填，TLB 效率、IO 合并、碎片度全部受损。

> 桌面视角：这条是唯一能造成几十个百分点差距的分叉，但**桌面通常踩不到**（默认 THP=madvise、khugepaged 合并率低、mTHP 基本不开）。详见 4.3。

这一条同时说明：gist 拿 2005 年的 LKML 邮件当「20 年无差别」的证据，逻辑上不成立——内核 swap 子系统这几年一直在动，而且**新动的方向恰好是「块设备独占」**。

### 2.2 物理布局与碎片：分区是 O(1) 且连续，文件是红黑树且可能散

- **分区**：`add_swap_extent(sis, 0, sis->max, 0)` —— 整个 swap 区是**一条 extent**。地址换算一次加法搞定，并且 LBA 天然连续。
- **文件**：extent 数量取决于文件系统当时能给你什么。上面那段 akpm 的注释自己就说了「typically 1-4MB range，可以有 hundreds of extents」。每次 IO 多一次红黑树查找（纳秒级，CPU 开销本身不值一提），**真正的问题是底层块是否连续**。

在一个用了 70% 的 ext4 上 `fallocate` 出来的 8G swap 文件，很可能被切成几十上百段。后果：

| 场景 | 顺序 vs 随机的实际差距（数量级） |
|---|---|
| HDD 顺序读 | 150–200 MB/s |
| HDD 4K 随机读 | 100–200 IOPS ≈ 0.4–0.8 MB/s |

swap 的访问模式本来是最怕随机的（缺页是同步的、延迟直接压在进程上）。内核的 swap readahead / cluster 机制能救一部分，但救不了物理块的随机分布。**在机械盘上，一个碎片化的 swap 文件和一个连续的 swap 分区，体感差距是倍数级，不是百分点级。**

顺带一提：swapon 时那些「不满足 PAGE_SIZE 对齐」的块会被直接丢弃（注释里的 "tossed out"）——碎片文件还会**白白损失一部分容量**。

自查命令：

```sh
sudo filefrag -e /swapfile     # 看 physical extents 数量
swapon --show=NAME,TYPE,SIZE,USED,PRIO
```

### 2.3 复杂文件系统上的约束与递归风险

这一类是「分区能做到、文件做不到或很危险」的硬边界：

- **btrfs**：有 `swap_activate` 回调（走 `SWP_ACTIVATED` 分支，不是通用路径）。它会 flush delalloc、锁 extent、**pin 住整个 block group**。约束：文件必须 `nocow`、不能压缩、不能有 reflink/快照、不能跨多设备 chunk。更麻烦的是：**`btrfs balance` / 碎片整理会移动物理块**，而内核 swapon 时缓存的块映射不会更新 → 写坏内存数据。所以规矩是「balance 前必须先 swapoff」。
- **ZFS**：**根本不支持 swapfile**（gist 评论区那位 FreeBSD committer / ZFS contributor 也确认了）。原因是 ZFS 没有稳定的 bmap，且 ARC 自身占内存，swap 页面换出到 ZFS 支持的文件时会和 ARC 抢内存，形成递归争用，严重时直接冻机。
- **overlayfs / loop 设备上的文件**：不支持或强烈不建议，因为没有稳定的底层块映射。
- **极端内存压力下的递归分配**：文件系统的元数据读写本身需要内存。内存见底时，「要回收内存 → 得换出 → 换出要走 FS 元数据路径 → 又需要内存」的回路，在 ext4/xfs 上已经用 mempool / `PF_MEMALLOC` 基本堵住，但在 ZFS、btrfs、多设备栈上依然是真实事故源。**swap 分区这条回路不存在。**

### 2.4 生命周期：可用时机、休眠、TRIM

| 维度 | swap 分区 | swap 文件 |
|---|---|---|
| 可用时机 | 可在 initramfs 阶段启用，早于根 FS 挂载 | 必须等文件系统挂载后，早期 OOM 窗口存在 |
| 休眠（hibernate） | 直接指定 resume 设备 | 需 `resume_offset`，加密/LVM 下配置繁琐 |
| discard/TRIM | 支持 `discard=once` / `discard=pages`，直接向设备发 discard | 依赖文件系统 discard 实现；且这些块在 FS 眼里长期「已占用」，SSD FTL 不知道内容已失效 → GC 效率下降、写放大上升 |
| 底层通知 | `swap_slot_free_notify` 只发给块设备（`if (si->flags & SWP_BLKDEV)`） | 不通知 |

TRIM 那条值得展开：swap 分区在启用时可以一次性把整个区域 discard 掉，SSD 立刻知道这些块是可擦除的空白；swap 文件占用的块在文件系统位图里是「已分配」，FTL 拿不到任何提示，只能等文件系统 trim 或文件删除。对长期重度使用 swap 的 SSD 服务器，这是**随时间累积**的性能衰减。

### 2.5 运维可见性

- `df` 里多出的几十 GB（gist 把它算成缺点，其实这是「容量被真实占用」的诚实表现）；
- 备份、`rsync`、快照、容器镜像打包时都要显式排除 swapfile；
- 快照（LVM/btrfs/虚拟机快照）会把 swap 内容一起冻进去，恢复后可能拿到一份和内存状态不一致的 swap 镜像。

---

## 3. gist 论证方式本身的问题

1. **诉诸时间而非事实。**「20 年前就一样了」不构成「现在也一样」。反例就在眼前：mTHP 不拆分换出是 2024 年合入的，且明确只对块设备生效。
2. **扩大解释了内核注释。**swap.h 里那句 `Apart from setup, they're handled identically` 限定在 swap extent 映射层；分配器（order > 0）、释放通知、discard、早期可用性这些地方内核是显式按 `SWP_BLKDEV` 分叉的。
3. **「better in every way」过于绝对。**ZFS 环境、overlayfs、机械盘、依赖 mTHP 的负载，至少这四类场景下它不成立。

当然，该给的也要给：**对绝大多数人——云主机、普通桌面、ext4/xfs、SSD、4G~8G 应急 swap——gist 的结论（用 swap 文件）是对的**，弹性、免分区表、易扩容的收益远大于那点理论差异。问题不在结论，在于把它写成了普适真理。

---

## 4. 为什么桌面 Linux 用 swapfile 基本没毛病

「用 ext4 + 4K 页 + SSD」只是一半的答案，而且是**次要的那一半**。真正的答案是**负载模型**：桌面的 swap 用法，恰好绕开了前面所有 5 条分叉的触发条件。

### 4.1 桌面的 swap 是「保险」，不是「带宽」

服务器上 swap 是持续工作的第二级存储：数据库 buffer pool、JVM heap 的冷页不停换进换出，吞吐和延迟直接进入 SLA。

桌面完全不是这样：

- **换出是异步的**：内存回收由 kswapd 在后台做，进程几乎不感知。真正同步的只有 swap-in（缺页）。
- **换出的是真冷页**：浏览器后台标签、开了一整天没再碰的 IDE 插件、库文件的匿名页。6.1+ 的 MGLRU 让「哪些页冷」判断得比以前准得多，桌面日常几乎不会把热页误换出去。
- **流量极小**：健康桌面的 `pswpout/s` 常年是 0，只在开大型工程/开几十个标签/临时压内存时burst 一下。一天可能就几百 MB。

一个「一天搬运几百 MB、且搬运时用户不会盯着延迟」的通道，你去纠结它 3% 还是 15% 的效率差，没有意义。

### 4.2 SSD/NVMe 把「随机 vs 顺序」的惩罚从 100 倍降到无感

第 2.2 条说碎片化会让顺序 IO 变随机——这话在机械盘上是致命的，在 SSD 上基本不成立。看**绝对延迟**而不是吞吐比：

| 介质 | 4K 随机读延迟（QD1，量级） | 换入 100MB 冷页的体感 |
|---|---|---|
| HDD | ~10 ms | 分钟级，窗口拖不动，明显卡死 |
| SATA SSD | ~0.1 ms | 一两秒， barely noticeable |
| NVMe | ~0.05–0.1 ms | 亚秒级，基本无感 |

同一份「碎片化 swapfile vs 连续分区」的物理布局差异，在 HDD 上体现为每次缺页多付 10ms（用户能数出来），在 NVMe 上体现为多付 0.05ms（没人感知得到）。**差异本身没变，是介质的绝对延迟把它稀释掉了。**

而且 SSD 还有个隐藏优势：FTL 本来就把 LBA 随机重映射到 NAND 物理页，「文件在逻辑上连不连续」对 NAND 来说没有物理意义——HDD 那个「顺序 = 磁头不跳」的前提在 SSD 上直接消失。

### 4.3 桌面基本碰不到大页 swap 的分叉（但要说准）

第 2.1 条是唯一能造成几十个百分点差距的，桌面为什么躲得过？

- 主流发行版默认 `/sys/kernel/mm/transparent_hugepage/enabled = madvise`。只有显式 `MADV_HUGEPAGE` 的程序（数据库、DPDK、部分 JVM 配置）才会去拿 THP，**浏览器、IDE、办公套件默认都不申请**。
- 即使 `always`，khugepaged 要在「内存规整成功 + 2M 对齐 + 访问模式稳定」时才合并成功。桌面进程的内存是碎的、生命周期是短的，实际 THP 覆盖率通常很低。
- 至于 mTHP（64K/16K），桌面发行版普遍没开（`hugepages-64kB/enabled` 多为 never/inherit 但实际少有匿名 mTHP）。

**但这里要给个诚实的边界**：如果你的桌面常年开 64K mTHP（部分发行版/调优脚本会开）、或者你在本机跑大模型推理、大型 C++ 编译、QEMU/KVM 虚机（这些会吃 THP），那么第 2.1 条的亏你照样会吃。判断方法很简单：

```sh
grep -E 'thp_swpout|thp_swpout_fallback|thp_split' /proc/vmstat
```

`thp_swpout_fallback` 长期非零增长，就说明大页在换出时被迫拆分了——那时就该考虑 swap 分区。

### 4.4 ext4/xfs + fallocate：让「碎片」这条也基本不成立

第 2.2 条成立的前提是「文件被切成很多段」。桌面规避起来很容易：

- 用 `fallocate`（不是 `dd`），并且在**系统刚装好、文件系统还很空**的时候建 → ext4 的多块分配器能一次给出 MB 级连续 extent。
- 内核注释说单条 extent 典型是 1–4MB，8G swapfile 落在几十条 extent 内完全正常 → 红黑树查找是纳秒级，相对 NVMe 的 0.1ms IO 延迟，噪声都算不上。
- 结果：走 `generic_swapfile_activate()` 建好 extent 表，运行期直发 bio，路径和分区一致。

反过来说，这也是唯一需要你**主动做对**的一步：在用了三年的满盘 ext4 上 `fallocate` 一个 16G 文件，段数可能上百，那才是真会痛的情况。

### 4.5 桌面的运维收益是压倒性的

理论差异趋近于零时，工程决策就看操作性：

| 维度 | swap 文件 | swap 分区 |
|---|---|---|
| 装机 | 不用预留、不用动分区表 | 必须提前规划，事后调整要 shrink/move |
| 改容量 | 两条命令，分钟级 | 需要空闲空间 + 分区工具，风险高 |
| 多系统/多发行版 | 各用各的文件，互不干扰 | 分区表争抢，容易误格 |
| 双系统 + Windows | 无影响 | 多一个 NTFS 看不懂的分区 |
| 休眠 | Ubuntu 等发行版默认就用 swapfile（配 `resume_offset`） | 可行但分区号要固定 |
| 云镜像/自动装机 | 镜像里塞一个文件即可，不用按盘大小算分区 | 需要按磁盘尺寸动态分区 |

桌面的核心诉求是**省事 + 可改**，swap 文件在这两点上是碾压的。

### 4.6 桌面 swapfile 的正确姿势

```sh
# 1) 预分配（关键：用 fallocate，别用 dd；尽量在文件系统较空时建）
sudo fallocate -l 8G /swapfile          # 或 mkswap --size 8G --file /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap defaults 0 0' | sudo tee -a /etc/fstab

# 2) 确认碎片程度：extents 数量越少越好
sudo filefrag -e /swapfile

# 3) 桌面推荐：zram 打头阵，磁盘 swap 只兜底
#    Fedora/openSUSE 默认开 zram；Ubuntu 可 sudo apt install zram-tools
#    zram 压缩比通常 2-3:1，且完全不碰磁盘 → 桌面卡顿的性价比最优解

# 4) 参数（桌面保守值）
sudo sysctl -w vm.swappiness=10          # SSD/NVMe 桌面；内存紧张可 20-60
sudo sysctl -w vm.watermark_boost_factor=1
```

避坑清单：

- **btrfs 桌面（openSUSE 等）**：swapfile 必须 `chattr +C`（nocow）、禁压缩、不能放在会被快照的子卷里；`btrfs balance` 前必须 `swapoff`。做不到就用分区。
- **别放在** LVM 快照源、网络文件系统、overlayfs、loop 设备、ZFS 上。
- **装了 64G+ 内存还开 32G swap**：没必要。桌面「少量内存 + zram + 2-8G 磁盘兜底」通常是最优组合。

### 4.7 桌面什么情况下还是该用分区

| 情形 | 原因 |
|---|---|
| 系统盘是机械盘 | 随机 IO 惩罚是 100 倍级，碎片 swapfile 会真的卡 |
| 内存 ≤ 4G 且重度依赖 swap | swap 变成主通道，任何百分比差异都会被放大 |
| 跑大模型 / 大编译 / 虚拟机 / 数据库 | 这些会吃 THP，第 2.1 条分叉真实触发 |
| btrfs + 要做 balance/快照 | 见 2.3 |
| 需要休眠且发行版没帮你配好 | 分区的 resume 配置更简单可靠 |

---

## 5. 怎么选

| 场景 | 建议 |
|---|---|
| 桌面 Linux（ext4/xfs + SSD/NVMe + swap 只当兜底） | **swap 文件**，理由见第 4 节（不是因为等价，是因为踩不到那些分叉） |
| 云主机 / 容器，ext4/xfs，SSD，swap 只是保险 | **swap 文件**，gist 的建议成立 |
| 需要频繁增减 swap 容量 | **swap 文件**（分区改大小要动分区表） |
| 机械盘 / 混合盘承重 swap | **swap 分区**（保证连续，避免碎片文件把顺序 IO 变随机） |
| 大量使用 THP / mTHP 的负载（数据库、大内存 JVM/编译农场） | **swap 分区**，且放在 SSD 上，否则大页换出全部退化成 4K |
| ZFS / btrfs（尤其要做 balance、快照） | **swap 分区**（ZFS 不支持 swapfile；btrfs 用 swapfile 前必须 nocow，且 balance 前 swapoff） |
| 内存吃紧、早期就可能 OOM | **swap 分区**（initramfs 阶段即可用） |
| 需要休眠到磁盘 | 两者都行，但**分区更简单可靠** |
| 长期重度 swap 的 SSD 服务器 | **swap 分区 + `discard=once`**，控制写放大 |
| 小内存机器 / 嵌入式 / 容器 | 先上 **zram / zswap**，比纠结文件还是分区收益大得多 |

---

## 6. 想自己量一量

```sh
# 1) 看 swap 文件碎片程度（extent 越多越糟）
sudo filefrag -e /swapfile

# 2) 看大页配置与拆分情况
cat /sys/kernel/mm/transparent_hugepage/hugepages-64kB/enabled
grep -E 'thp_split|thp_swpout' /proc/vmstat

# 3) 换页吞吐与延迟
vmstat 1                 # si/so 列
sar -B 1                 # pswpin/s pswpout/s

# 4) 直接量 swap 路径耗时
sudo bpftrace -e 'kprobe:swap_writepage { @s = hist(nsecs); }'

# 5) 对照实验：同样的压力，分别在 swap 文件 / swap 分区上跑，
#    比较 pswpout/s 与 pswpin/s 的稳态值，以及应用 P99 延迟
```

---

## 7. 一句话总结

> swap 文件和 swap 分区在「4K 页的直接 IO 路径」上确实几乎等价——但 swap 文件**拿不到大页 swap slot**（2024 年这条路径只对块设备开放）、**物理布局不保证连续**、**在 CoW/复杂 FS 上有额外约束和递归风险**、**可用时机更晚且 TRIM 语义更差**。
>
> **桌面 Linux 用 swapfile 没毛病**，不是因为两者在所有维度等价，而是因为：桌面 swap 只当保险（异步、冷页、流量极小）；NVMe/SSD 把随机 IO 的绝对延迟压到感知阈值以下（0.1ms vs HDD 的 10ms）；桌面默认拿不到 THP/mTHP，踩不到大页分叉；ext4 + `fallocate` 建在空盘上，extent 数量本来就少。四条叠加，理论差异全部落进噪声里，swapfile 在可运维性上的压倒性优势就成了决定性因素。
>
> gist 的结论对大多数场景是对的，但它给出的理由（「20 年没差别」）是错的，适用范围也被写成了「every way」。

---

## 参考

- 内核源码：`mm/swapfile.c`（`setup_swap_extents()` / `cluster_alloc_swap_entry()` / `swapon()` 中的 `SWP_BLKDEV` 分支）、`include/linux/swap.h`（`struct swap_extent` 注释、`SWP_*` 标志）
- Ryan Roberts, *[PATCH v4 0/6] Swap-out mTHP without splitting*, LKML, 2024-03
- Andrew Morton 关于 swap extent rbtree 的注释（原文见上）
- 内核文档：`Documentation/admin-guide/sysctl/vm.rst`（swappiness）、`Documentation/power/swsusp.rst`（休眠与 swap）
