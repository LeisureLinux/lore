# EXT4 Linux 7.3：IOmap 转换落地、并行 DIO 写、主 pull request 三件套叠在一起

> **原始出处**：Phoronix + LKML VFS pull request + EXT4 pull request
> **发布日期**：2026 年 8 月 19 日（合并窗口早期）
> **作者**：Christian Brauner（VFS iomap）、Ted Ts'o（EXT4 maintainer）
> **关键 PR**：
>   - VFS iomap：[GIT PULL 08/18 for v7.3] vfs iomap（Christian Brauner）
>   - EXT4：ext4: use iomap for regular file's buffered I/O path v5（Zhang Yi）
>   - EXT4 主 pull：EXT4 feature pull request for Linux 7.3（Ted Ts'o）
> **Phoronix 报道**：https://www.phoronix.com/news/EXT4-Linux-7.3
> **翻译/解读**：LeisureLinux
> **关键词**：EXT4 Linux 7.3、IOmap 并行 DIO、parallel direct I/O、ext4_mb_prefetch

## 引言：三件套叠在一起

EXT4 Linux 7.3 这一波的"性能提升"不是单一改动，而是 **三块独立的工作在合并窗口早期碰头**：

1. **VFS IOmap 重写**（Christian Brauner）：把 iomap 从 `iomap_begin/iomap_end` 双回调改成单一的 `iomap_next()`，彻底切换到 iterator 模型；并补上小 I/O 的简单 DIO 路径。
2. **EXT4 buffered I/O 切到 iomap**（Zhang Yi）：用 32 个 patch 把 EXT4 buffered read/write/writeback/mmap 路径从 buffer_head 搬到 iomap。
3. **EXT4 主 pull**（Ted Ts'o）：并行 DIO 写、`ext4_mb_prefetch()` 用 `fallocate()` 优化、overwrite 已 up-to-date folio 路径优化、若干稳定性修复。

三件叠加让 7.3 成为 EXT4 近几年性能收益最大的版本。但要理解每一块的"为什么"，得先回看 IOmap。

---

## 一、IOmap：VFS 层的"地图框架"

### 1.1 IOmap 是什么

IOmap（include/linux/iomap.h）是 VFS 子系统里一个通用的"逻辑文件偏移 → 物理磁盘位置"映射框架。它不归某个文件系统所有——EXT4 / XFS / Btrfs / EXT2 / EROFS / F2FS / GFS2 / HPFS / FUSE / exFAT / ZoneFS / NTFS / NTFS3 / block device mapping 全部用。

它的核心 API 是：

```c
struct iomap_ops {
    iomap_begin(...);  // 开始一段映射
    iomap_end(...);    // 结束一段映射
};
```

调用方 `iomap_iter()` 通过这两个回调走完一次映射迭代。

### 1.2 老设计的代价

老设计里 `iomap_iter()` 只把 `iomap_begin` / `iomap_end` 当**函数指针**用。每一步迭代都是一次间接调用，编译器**不能内联**。

Joanne Koong 把这一点改成了单一 `iomap_next()` 回调：

```c
struct iomap_ops {
    iomap_next(...);   // 完成上一段映射 + 产生下一段
};
```

调用方 `iomap_iter()` 现在能把 `->iomap_next` 作为**编译期常量**传进来，编译器能直接把它内联。**每次迭代省一次间接调用**，所有支持的文件系统都受益。

### 1.3 受益范围

VFS pull 列出的转换名单：

```
xfs, btrfs, ext4, ext2, erofs, f2fs, gfs2, hpfs,
 fuse, exfat, zonefs, ntfs, ntfs3, block device mapping
```

13 个文件系统 + 块设备层全部切换。commit 数与 diff 规模：

```
29 files changed, 569 insertions(+), 159 deletions(-)
```

净 +410 行——看着增加不多，但配合下面的 DIO 路径修改是大头。

---

## 二、小 I/O 简单 DIO 路径：把 1.92M → 2.19M IOPS

### 2.1 瓶颈来源

Bytedance 工程师 Fengnan Chang 发现：PCIe Gen5 NVMe 上跑 4K 随机读时，**单核 io_uring poll mode** 跑到：

- 裸块设备：~3.2M IOPS
- 经过 EXT4：~1.92M IOPS
- 经过 XFS：~1.92M IOPS

差距 1.28M IOPS。profile 显示 `__iomap_dio_rw()`、`iomap_iter()`、`iomap_dio_bio_iter()`、`kfree()` 在 top。

也就是说：**小块 DIO 路径上的开销，被 IOmap 的间接调用 + 多次 kfree + bio 分配路径放大**。

### 2.2 简单 DIO 路径

Fengnan Chang 加了一个**轻量级 DIO 路径**，触发条件：

- I/O size ≤ inode blocksize
- 文件未加密
- 一些列其他限制

满足时，bio 走专用 bioset，整段 cacheline 对齐单次分配，**完成回调 inline 运行**，没有 `kfree`、没有间接调用、没有状态机。

### 2.3 性能数据（fio 测试）

| 队列深度 | libaio | io_uring | io_uring poll（QD 256） |
|---------|--------|---------|------------------------|
| **提升** | 4%（QD ≥ 64） | 约 5% | 最高 10% |

EXT4 从 1.92M → **2.19M IOPS**（单核 io_uring poll，4K 随机读）。

注意这只是单核、单工作负载，**多核线性扩展后差距会更大**。配合下一节的 EXT4 buffered I/O 切 iomap，提升进一步叠加。

---

## 三、EXT4 buffered I/O 切到 iomap：32 patch 系列

### 3.1 为什么这次切换重要

EXT4 一直是 buffer_head 路径的老用户——EXT3 时代就是这样设计的。但内核整体已经迁移到 iomap 框架，EXT4 是少数剩下的"异类"。Zhang Yi 在 v5 patch 系列里把 buffer_head 路径全部换成 iomap：

```
Patch 01-03: 简化 truncate，drop 掉 EOF 零块时不必要的 ordered I/O
Patch 04-21: 扩展 ext4_map_blocks()，实现 iomap buffered read/write/writeback/mmap/部分块零
Patch 22-30: 处理 unaligned EOF 文件扩展时 zeroing 与 i_disksize 更新的顺序
Patch 31-32: 启用 iomap buffered I/O 路径
```

### 3.2 实测数据

测试环境：4 核 VM（Intel Xeon Platinum 8380），150GB RAM-backed virtual-io 块设备。

**写性能**（MiB/s）节选：

| 配置 | ext4+bh | ext4+iomap | delta |
|------|---------|-----------|-------|
| 异步 4k | 170 | 176 | +4% |
| 异步 64k | 1816 | 1981 | +9% |
| 异步 1m | 4295 | 5780 | **+35%** |
| 异步 64k + writeback | 734 | 957 | **+30%** |
| 异步 1m + writeback | 1460 | 1683 | +15% |
| 异步 64k + RWF_DONTCACHE | 415 | 698 | **+68%** |
| 异步 1m + RWF_DONTCACHE | 1404 | 2883 | **+105%** |
| 异步 64k + OW（覆盖写） | 1776 | 1867 | +5% |
| 异步 1m + OW | 4105 | 4879 | +19% |

**读性能**（MiB/s）节选：

| 场景 | BS | ext4+bh | ext4+iomap | delta |
|------|----|---------|-----------|-------|
| READ HOLE | 64k | 2011 | 2116 | +5% |
| READ DATA（无 page cache） | 64k | 741 | 768 | +4% |
| READ DATA | 1m | 1143 | 1210 | +6% |

**关键结论**：大块 I/O 显著提升（部分场景 +105%），小块同步/非缓存场景轻微回退（-7%~-15%），读性能差异不大。

### 3.3 已观察到的稳定性结论

xfstests-bld 在 `-g auto / fast_commit / 64k` 三种配置下：

- **无新增失败**。
- 仅一个 known issue：`generic/127` 偶发失败，根因在 MM 大 folio 拆分逻辑（另修）。

这意味着切 iomap 的**兼容性已经过 xfstests 验证**，剩下的只是优化空间。

---

## 四、EXT4 主 pull：并行 DIO + 多块分配器 + overwrite

EXT4 主 feature pull request 由 Ted Ts'o 提交。三件性能改进 + 一批稳定性修复：

### 4.1 并行 direct I/O 写

```plaintext
"Allowing parallel direct I/O writes where previously were being 
too conservative when checking if it was safe to avoid requiring 
an exclusive lock."
```

老逻辑里 EXT4 在判断"是否需要独占锁"时过于保守，导致并行 DIO 写被序列化。新逻辑放宽判断，让真正能并发的写并行执行——**对数据库、Docker volume、VM image 这些 DIO 重负载是直接收益**。

### 4.2 ext4_mb_prefetch() 用 fallocate() 优化

`ext4_mb_prefetch()` 是 EXT4 多块分配器的预取逻辑，目的是减少分配时的锁竞争。新逻辑：**当 fallocate() 已经预留空间时，跳过预取**。

实测里 fallocate() 路径下能省掉一批不必要的预取扫描，对预分配大文件的场景（如数据库 table space）有可见收益。

### 4.3 Overwrite to up-to-date folio

EXT4 之前在处理"覆盖一个已经 up-to-date 的 folio"时走了完整 mballoc 路径。新逻辑识别这种 case 提前返回，避免冗余扫描。

### 4.4 稳定性

- 避免可能的 soft lockup 与 RCU stall 条件。
- 若干 bug fix（包括 `ext4_da_map_blocks()` stale delalloc extent、短 iomap buffered write 路径、`data_error=abort` 边缘 case、`punch hole` 与 writeback 竞态等）。

---

## 五、对文件系统生态的整体影响

EXT4 切 iomap 后，剩下的"buffer_head 异类"已经不多了。Linux 文件系统基本全面 iomap 化。这意味着：

- **新文件系统**（EROFS、ZoneFS 等）从第一天起就走 iomap，性能基线更高。
- **新硬件优化**（PCIe Gen5、CXL、新型内存）只需要在 iomap 层做一次，所有文件系统受益。
- **bug 修复**一次生效全栈，不用每个 fs 单独修。

XFS 在这次 IOmap 迭代里也完成切换。Btrfs、NTFS、NTFS3 一并完成。F2FS / GFS2 / HPFS / FUSE / exFAT / ZoneFS / EXT2 / block device mapping 都跟进。

---

## 六、性能数据横向对比

Phoronix 测试 + Zhang Yi 实测综合：

| 工作负载 | 7.2 性能 | 7.3 性能 | 提升来源 |
|---------|---------|---------|---------|
| 4K 随机读（单核 io_uring poll，Gen5 NVMe） | 1.92M IOPS | 2.19M IOPS | 简单 DIO 路径 |
| 大块顺序写（异步） | 1816 MiB/s | 1981 MiB/s | iomap + buffered I/O 切换 |
| 大块顺序写 + writeback | 734 MiB/s | 957 MiB/s | 同上 |
| 大块 RWF_DONTCACHE | 415 MiB/s | 698 MiB/s | 同上 |
| 并行 DIO 写 | 串行化 | 并行化 | 主 pull |
| 多块预取（fallocate 场景） | 全跑 | 跳过冗余 | 主 pull |

> 注：上面数据来自不同测试（Phoronix + Zhang Yi），并非同一硬件；只是看出趋势。

---

## 七、对运维的影响

### 7.1 该不该升级

**值得升级的场景**：
- 数据库 / VM image / Docker volume 跑在 PCIe Gen5 NVMe 上。
- 用 DIO 写（很多 DBMS 默认就是 O_DIRECT）。
- 大块顺序写密集（备份、视频处理）。
- 想用 xfstests 验证过的稳定性。

**观望场景**：
- 小块随机写（罕见性能回退）。
- 极特殊 sync 路径（极少数 -7%~-15% 的回退）。

### 7.2 升级前要做的事

```bash
# 1. 备份 + snapshot
btrfs subvolume snapshot / /snap-ext4-pre73

# 2. xfstests 验证（如果你有环境）
xfstests-bld -g auto,fast_commit,64k

# 3. 关注 dmesg 中的 EXT4 警告
dmesg -w | grep -i ext4

# 4. 性能基线对比
fio --name=before --rw=randread --bs=4k --iodepth=256 --ioengine=io_uring --filename=/dev/nvme0n1 --runtime=60
```

### 7.3 回滚路径

7.3 是 mainline，未合入任何稳定分支。如果用 mainline + 自编译，建议保留：

- 原内核 .config + bzImage 备份
- 原 initramfs 备份
- 启动器（grub / systemd-boot）保留 old entry

万一性能回退明显，切回上一个稳定内核即可。

---

## 八、为什么这次性能收益这么大？

回头看，EXT4 Linux 7.3 不是"一个大特性"，而是**几代增量改进碰到一起**：

| 改动 | 单独价值 | 叠加价值 |
|------|---------|---------|
| **IOmap iterator 模型** | 消除间接调用 | 全栈受益 |
| **简单 DIO 路径** | 单核 +14% IOPS | Gen5 NVMe 用户立即看到 |
| **buffered I/O 切 iomap** | 大块写 +35%~+105% | 与 DIO 路径叠加 |
| **并行 DIO** | DIO 写并行化 | 数据库场景受益 |
| **fallocate 跳过预取** | 减少扫描 | 预分配场景受益 |

这种"积少成多"是 Linux 内核最常见也最难预测的版本——单独看每一个都不惊人，叠在一起就让 EXT4 跨了一档。

---

## 九、关注下一个版本

EXT4 切 iomap 后，下一步看点：

- **ext4_iomap + writeback 路径**进一步优化（小块同步场景的回退需要补回）。
- **data=ordered mode** 在 iomap 路径下的完整支持（v5 系列暂时 always queue ioend worker 简化逻辑，未来还要补）。
- **新 ioend 基础设施**：Zhang Yi 在 patch 16 已经为新 ioend 框架迁移铺路。

预计 7.4 / 7.5 会看到更彻底的 iomap 化收益。

---

**参考资料**：

1. Phoronix EXT4 Linux 7.3：https://www.phoronix.com/news/EXT4-Linux-7.3
2. Phoronix IOmap Linux 7.3：https://www.phoronix.com/news/IOmap-Linux-7.3-Faster
3. Phoronix Faster Small Direct Linux 7.3：https://www.phoronix.com/news/Linux-7.3-Faster-Small-Direct
5. LKML VFS iomap pull：[GIT PULL 08/18 for v7.3] vfs iomap
4. LKML ext4 iomap v5：ext4: use iomap for regular file's buffered I/O path v5
5. Linux 7.3 源码：https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
6. xfstests-bld：https://github.com/tytso/xfstests-bld

---

*本文基于 Phoronix 报道、LKML VFS iomap pull request、Zhang Yi ext4 iomap v5 系列与社区资料整理，旨在为中国开发者提供快速理解和参考。*

*作者观点不代表任何厂商立场，仅供技术讨论参考。性能数据基于公开测试，不同硬件 / 文件系统 / 工作负载配置可能有所差异。*