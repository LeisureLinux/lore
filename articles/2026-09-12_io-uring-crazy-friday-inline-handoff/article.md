> 译自 Phoronix：*Linux's IO_uring Sees Some "Crazy" Patches That Deliver Very Nice Improvements*  
> 作者：Michael Larabel  
> 日期：2026-09-11  
> 原文：https://www.phoronix.com/news/Linux-IO-uring-Crazy-Friday

# io_uring 的「疯狂星期五」：把阻塞操作 Inline 执行，用「身份切换」换掉线程唤醒

io_uring 的作者、Linux block 子系统维护者 Jens Axboe 又在周五放出「疯狂补丁」。这次不是改 ring buffer，也不是加新 opcode，而是直接动摇了 io_uring 处理「可能阻塞的系统调用」的核心假设：

> 既然这些操作大多数根本不阻塞，为什么要一上来就付出代价把它们 punt 到 io-wq？

Axboe 的答案是：**先 inline 执行；如果它真的阻塞了，就让 io-wq worker 穿上提交者的「身份外衣」返回用户态，原任务则转身去当 io-wq worker。**

这个做法足够「疯狂」，以至于 Axboe 自己在 X 上称之为 *crazy patches*，但初步基准测试结果也确实非常诱人。

---

## 1. 问题：io_uring 太「谨慎」了

io_uring 的设计目标之一，是避免 submitter 在内核里阻塞。它的策略是：

- 能走非阻塞路径的 opcode，直接在 `io_uring_enter()` 里 inline 完成；
- 不能走非阻塞路径的，统统 punt 到 io-wq 后台线程，让 worker 去慢慢做，做完再通过 `task_work` 通知原任务。

这套机制在真正会阻塞的 IO（大文件读、fsync 刷盘）上没问题。但 Axboe 指出，有很多操作**在常见场景下根本不会阻塞**，却被无条件地异步化：

- `fsync` / `fdatasync` 命中 page cache、没有脏页时；
- `statx` 命中 dcache，不需要下盘；
- `openat` 带 `O_TMPFILE`，不需要真正创建文件；
- `renameat`、`fadvise`、xattr 等元数据操作。

这些操作本可以几微秒 inline 完成，却要先唤醒 io-wq worker、上下文切换、再 `task_work` 回调一圈。Axboe 的原话是：*Sad story.*

---

## 2. 方案：Inline + Identity Handoff

RFC 补丁系列的核心思路可以拆成两步：

1. **不再无条件 punt**：对这些「被迫异步」的 opcode，先在内核里 inline 执行。
2. **真的阻塞时再换身份**：如果执行过程中阻塞了，提交任务已经深陷内核，请求栈都在它身上，没法再把工作搬到另一个线程。那能搬的是什么？是**身份**。

具体机制大致是：

- 当 inline 执行遇到阻塞时，一个空闲的 io-wq worker 接管提交任务的「用户可见身份」——tid、信号状态、credentials、调度属性、cgroup、用户寄存器状态；
- 这个 worker 继续完成 `io_uring_enter()`，从 syscall 返回用户态，用户程序看到同一个 tid 回来，无感知；
- 原来的提交任务则被「转换」成 io-wq worker，继续在内核里把剩下的 IO 做完，然后加入 worker pool。

Axboe 提到，大约 20 年前内核圈里有过类似尝试。当时没成，现在借着 io_uring 的成熟路径再次拿出来试。

---

## 3. 数据：QD1 延迟大幅下降，元数据吞吐数倍提升

测试环境是 virtme-ng guest，8 vCPU，non-debug x86 config，基于 7.3-rc2。

### 3.1 QD1 单操作延迟

| 操作 | 原 punt 到 io-wq | 新 inline + handoff | 降低 |
|---:|---:|---:|---:|
| fsync (ext4) | 32 µs | 4 µs | -87% |
| statx (ext4) | 35 µs | 8 µs | -77% |
| fadvise (ext4) | 32 µs | 6 µs | -82% |
| openat (ext4) | 181 µs | 88 µs | -51% |
| renameat (ext4) | 115 µs | 72 µs | -38% |
| renameat (tmpfs) | 61 µs | 21 µs | -66% |
| openat (tmpfs) | 54 µs | 22 µs | -60% |

最显眼的是 `fsync` / `fadvise` / `statx` 这一类「命中缓存就不会阻塞」的操作：它们以前被 io-wq 的线程切换和回调拖成了几十微秒，现在 inline 后只剩个位数微秒。

### 3.2 吞吐：tmpfs 上更夸张

在内存文件系统（tmpfs）上，没有真实块设备延迟，线程切换的 overhead 被放大得最厉害：

- `fsync (tmpfs)` QD1：从 28K IOPS 涨到 221K IOPS，提升约 681%；
- `statx (tmpfs)` QD1：从 24K IOPS 涨到 117K IOPS，提升约 378%；
- `openat O_TMPFILE (tmpfs)` QD1：从 13K IOPS 涨到 43K IOPS，提升约 222%；
- `renameat (tmpfs)` QD1：从 15K IOPS 涨到 49K IOPS，提升约 223%。

这组数字说明：当后端本身非常快时，io_uring 的「异步化税」原本比「实际 IO 税」还高。inline + handoff 把这些税基本省掉了。

### 3.3 但并非所有场景都赢

高队列深度下，某些重负载出现了回落（红色柱表示 inline+handoff 比 punt 还慢）：

- `fsync (ext4)` QD32：比原方案慢 65%（15K vs 42K IOPS）；
- `openat O_TMPFILE (ext4)` QD8 / QD32：分别慢 44% / 49%；
- `statx (ext4)` QD32：慢 29%；
- `renameat (tmpfs)` QD8：慢 15%。

Axboe 把这套补丁标为 **RFC**，原因之一就是这些高 QD 下的 regression 还需要调。Identity handoff 在「单个操作阻塞概率低」时非常赚，但在高并发、真的会阻塞的场景，线程切换的税可能换了一种形式回来。

---

## 4. 为什么值得认真读

对 Linux 用户和开发者来说，这件事的意义不只是几张 benchmark 图：

1. **它可能把 io_uring 的适用范围再扩大一圈**。现在 fsync、statx、openat 等 opcode 因为「必走 io-wq」而在很多高性能场景里被避开。如果 inline 路径稳定，数据库、容器、构建系统、文件同步工具的代码会少写很多绕路。

2. **「阻塞就换身份」是个通用思路**。它不一定只服务于 io_uring。内核里凡是「大概率不阻塞但万一阻塞」的系统调用，都可以考虑类似技巧。这会改变我们对 sync syscall 性能天花板的认知。

3. **它提醒你 io_uring 还在快速演进**。这个框架诞生没多久，仍然在以不兼容默认行为的方式自我重写。Linux 7.4  cycle 如果能合入，又会有一批 benchmark 重新洗牌。

---

## 5. 落地预期

Axboe 说目标是争取在 **Linux v7.4** 周期进入主线。目前仍是 RFC， regressions 没修完，代码审查也刚开始。对生产环境来说，**现在观望即可**；但如果你是内核开发者、做存储/数据库性能工作，或者就是 io_uring 的爱好者，这组补丁的演进值得盯紧。

简单一句话：**io_uring 正在学会「赌一把」——赌这些操作不会阻塞；赌输了，就优雅地把身份交给 worker，自己继续干活。** 这个赌法，看起来像是未来的方向。
