---
title: "glibc malloc 到底在干什么：用一个玩具分配器量出 22.7 倍差距"
date: 2026-11-11
slug: glibc-malloc-bump-allocator-22x
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Ben M. Andrew《What is malloc doing, anyway?》（2026-11-08）全文、全部代码片段与测量数据 ＋ 作者公开的可复现代码仓库 benmandrew/malloc-snippets（v1 tag）＋ mallopt(3) 官方 man page（M_MMAP_THRESHOLD 动态阈值、M_TRIM_THRESHOLD / M_TOP_PAD 默认 128 KiB、M_MXFAST/fastbins）＋ brk(2)/sbrk(2)、mmap(2)、malloc_trim(3) man page ＋ glibc MallocInternals wiki（经 Anubis 拦截，改以 man page 与原文交叉核对）"
original_date: 2026-11-08
original_url: "https://benmandrew.com/articles/what-is-malloc-doing-anyway"
description: "本文解读 Ben M. Andrew 的教学长文，并对照 mallopt(3) 等官方 man page 核对机制。作者从『malloc 只是向内核要内存』这个直觉出发，用一个逐步改进的玩具分配器量出每一层优化的代价：strace 显示 1000 次 malloc(16) 只产生两次 brk，第一次就把堆推高 132 KiB；空系统调用 575.2 ns、sbrk(16) 610.1 ns、malloc(16) 26.9 ns，差 22.7 倍。随后逐层加回 chunk 头（请求+8 字节头、16 字节对齐、最小 32 字节）、空闲链表、拆分与合并、64 KiB 步进扩容、128 KiB 阈值触发 trim、以及 128 KiB 以上改用 mmap 独立映射。 demanda paging 实测：sbrk 出 1 GiB 后虚拟地址已涨到 1050916 KiB 而 RSS 仅 1308 KiB，每写 256 MiB 触发 65536 次缺页。最终性能对照表：玩具 bump 1.72 µs/step、freelist 5.12、trim 11.2、mmap 11.8，而 glibc 0.0789 µs/step —— 快 65 到 142 倍；代价是 glibc 全部 free 后仍保留 19.0 MiB 匿名 RSS。原因是 bins 按尺寸分链表、tcache 每尺寸缓存最多 7 块、以及动态 mmap 阈值：GLIBC_TUNABLES=glibc.malloc.tcache_count=0 后 step 变 0.121 µs 但全 free 只剩 0.250 MiB；把 mmap_threshold 钉在 128 KiB 后变 0.843 µs（慢 10.7 倍），因为每次大请求都要重新付系统调用与缺页。结论：malloc 用内存换的是『不进内核』，tcache 与动态阈值都是刻意让已释放内存留在用户态的证据；碎片化之所以在长跑进程里把 RSS 推高，也正源于只有堆顶能还回去。"
published: true
---

> 一手：一篇用可复现代码逐步造分配器的教学长文（2026-11-08）
> 官方：`mallopt(3)`、`brk(2)`/`sbrk(2)`、`mmap(2)`、`malloc_trim(3)` man page
>
> 文中所有数字均取自原文在 Intel Xeon E3-1230 v3 上的实测，本文未复现。

`malloc` 的接口简单到有点骗人：给一个字节数，返回一段连续内存的指针；`free` 掉，内存「消失」。Ben M. Andrew 11 月 8 日发了篇长文，把这句「消失」拆开 —— 方法很朴素：自己写一个分配器，一层一层加机制，每加一层就量一次。最后量出的结论比任何概念解释都直接：glibc 的 `malloc` 比每次直接调 `sbrk` 快 22.7 倍，比他自己写到最完整的玩具分配器快约 150 倍，而代价是内存还回去得不干脆。

## 一、先看见「系统调用去哪了」

作者用 `strace` 跟一个循环 `malloc(16)` 一千次的程序：

```
brk(NULL)           = 0x59faca231000
brk(0x59faca252000) = 0x59faca252000
```

两次 `brk`，都发生在第一次 `malloc` 里：第一次问 program break 在哪，第二次把堆一次性推高 132 KiB。剩下 999 次全在用户态从这块内存里切。

这里顺手理清两个常被混用的名字：`brk` 是系统调用，把 program break 设到给定地址；`sbrk` 是 libc 的便利包装，收的是增量。`mmap` 在后面才登场。

为什么非要批量拿？他量了百万次调用：

| 调用 | 每次耗时 |
|---|---|
| `syscall(SYS_getppid)`（空系统调用） | 575.2 ns |
| `sbrk(16)` | 610.1 ns |
| `malloc(16)` | 26.9 ns |

`sbrk(16)` 只比空系统调用贵 35 ns，而 `malloc(16)` 快 22.7 倍。这个 22.7 就是「用户态记账」存在的全部理由。

## 二、地址空间：虚拟很大，物理很小

一个打印各段地址的小程序给出：

```
main (text)          0x59c0791d7149
initialised (data)   0x59c0791da020
uninitialised (bss)  0x59c0791da028
malloc(16) (heap)    0x59c0903182b0
program break        0x59c090338000
printf (libc)        0x711dcf7c15b0
local (stack)        0x7ffff86c45ec
```

break 和 libc 里的 `printf` 相差约 23.4 TiB，是这台机器 15.6 GiB 内存的约 1530 倍。中间几乎全是未映射的空洞，不要钱。这个观察是理解后面 demand paging 的前提：地址空间的大小和占用的物理内存毫无关系。

## 三、四级玩具分配器，每一级解决什么

① bump allocator。 每次 `sbrk` 直接推 break，返回旧地址；`my_free` 什么事都不做。它每次请求都进内核，而且完全无法复用 —— `free(b)` 之后 `d` 还是排在 `c` 后面。

② chunks 与头部。 `malloc` 实际分配得比你请求的多。作者读 `((size_t*)p)[-1]` 这个头部，得到：

| 请求 | 实际 chunk |
|---|---|
| 1 | 32 |
| 24 | 32 |
| 25 | 48 |
| 1000 | 1008 |

规则是「请求 + 8 字节头，向上取整到 16 的倍数，最小 32」。16 字节对齐对应 x86-64 的 `max_align_t`，保证返回的指针适合任何 C 类型；32 字节下限是为了给释放之后要塞进去的链表指针留地方。glibc 也很省：释放后把 `next` 指针直接写在用户原来放数据的那块内存里。低三位恒为零（尺寸是 16 的倍数），于是被拿来当标志位用。

③ 空闲链表 + 拆分合并 + 步进扩容。 玩具版按首次适配找够大的块，`grow_heap` 用 `sbrk` 以 64 KiB 步进扩容。玩具的头部是完整 `chunk_t`（16 字节，比 glibc 的 8 字节胖），所以 `my_malloc(100)` 要 128 字节而 glibc 只要 112。

④ trim 与 demand paging。 这里有两个很值得记住的实测。

`trim` 在堆顶空闲块达到 128 KiB 时下调 break，但保留 64 KiB 免得下次立刻又推上去。一个先分配 1 MiB 再在它上面放 16 字节、并写满 1 MiB 每页的程序显示：释放掉 1 MiB 后 break 仍停在 1088 KiB、匿名 RSS 1124 KiB —— 因为那个 16 字节小块还活着，只有堆顶能还回去。等它也释放，trim 把 break 降到 64 KiB，匿名 RSS 掉到 160 KiB。活块下面那些空洞就一直占着物理内存，长跑进程里这就是碎片化把 RSS 推到被 OOM 杀掉的路径。

demand paging 的量表更直观：`sbrk` 出 1 GiB 后虚拟大小已是 1050916 KiB，RSS 才 1308 KiB；此后每写 256 MiB 触发 65536 次缺页（每 4 KiB 一页），RSS 每档涨约 256 MiB。写满 1 GiB 时 RSS 1049968 KiB。

⑤ 大块走 mmap。 128 KiB 及以上的请求（含头部）改用 `MAP_PRIVATE|MAP_ANONYMOUS` 单独映射，头部里用一个 M 标志记着，`my_free` 见到就 `munmap`，立刻把整块还给内核，不管旁边是谁。这解决了「堆顶被一个小块钉住」的问题：玩具版释放 1 MiB 后匿名 RSS 从 1128 KiB 掉到 100 KiB。

那为什么不全部 mmap？作者给了两条：独立映射之间地址不保证连续，块跨不过这些空洞做合并；而堆上被释放的块页仍驻留，复用时不缺页，新映射每次写每页都要重新缺页。glibc 自己确实用 `mmap` 建额外 heap（arena）把线程摊开、避开主堆锁争用，但主路径仍是 `sbrk` 那块连续区域。

## 四、最终对照表：快，是要花内存买的

工作负载是维持 4000 个活块，每步随机释放一块、分配随机尺寸的新块并写满每页，跑 50 万步、`-O2`、每轮新进程；90% 请求 16–512 字节，9% 到 16 KiB，1% 在 128–256 KiB。结束时活块共 10.3 MiB。

| 分配器 | 每步 µs | 活块时匿名 RSS | 全释放后 |
|---|---|---|---|
| bump | 1.72 | 1425 MiB | 1425 MiB |
| freelist | 5.12 | 17.8 MiB | 17.8 MiB |
| +trim | 11.2 | 14.5 MiB | 0.188 MiB |
| +mmap | 11.8 | 11.2 MiB | 0.188 MiB |
| glibc | 0.0789 | 19.0 MiB | 19.0 MiB |

freelist 与 trim 比 glibc 慢 65 倍和 142 倍，原因是每步要多次遍历一条长长的空闲链表（找适配、插回时找邻居、trim 找链尾）。glibc 用的是按尺寸分桶的 bins，请求直接去对应尺寸的链表；再加一层 tcache，每个尺寸最多缓存 7 个最近释放的块，同尺寸的下一次请求直接拿到手。

而最值得琢磨的是最后一列：glibc 全部释放后仍留着 19.0 MiB，比它自己最完整的玩具版多两个数量级。这不是泄漏，是设计。作者用 `GLIBC_TUNABLES` 做了两组对照：

| 配置 | 每步 µs | 活块 RSS | 全释放后 |
|---|---|---|---|
| 默认 glibc | 0.0789 | 19.0 MiB | 19.0 MiB |
| `glibc.malloc.tcache_count=0` | 0.121 | 17.4 MiB | 0.250 MiB |
| `glibc.malloc.mmap_threshold=131072` | 0.843 | 12.1 MiB | 5.85 MiB |

关掉 tcache，全释放后只剩 0.250 MiB，代价是每步慢 1.5 倍 —— 缓存的块在堆眼里算「在用」，只要有一个靠近堆顶，就挡住了 break 下调。把 mmap 阈值钉死在 128 KiB 更贵：每步 0.843 µs，慢 10.7 倍，因为每个大请求都要重新付系统调用和缺页。默认跑法里 glibc 全程只调了 51 次 `mmap`，玩具版调了 5040 次。

这背后是 `mallopt(3)` 里写明的动态 mmap 阈值：初始 128 KiB；当大于当前阈值、又不超过 `DEFAULT_MMAP_THRESHOLD_MAX`（64 位上是 32 MiB）的块被释放时，阈值会上调到该块的尺寸，于是之后的大请求改从堆上拿。同一份 man page 还说明 `M_TRIM_THRESHOLD` 与 `M_TOP_PAD` 默认都是 128 KiB，且一旦显式设置 `M_MMAP_THRESHOLD` 等参数，动态调整就关闭 —— 正好对上作者把阈值钉死后性能崩掉的结果。`M_MXFAST`/fastbins 也在那里：同尺寸小块不合并、直接复用，用碎片换速度。

所以这张表能读出的结论比「优化得好」具体得多，原文那句「malloc spends memory to stay away from the kernel」正是这个意思：malloc 花内存买的是「不进内核」。tcache、动态阈值、堆顶留白，都是让已释放内存尽量留在用户态、随时能再发出去的机制；而 `free` 之后 RSS 不降，通常先该怀疑这些机制，再怀疑泄漏。

## 五、事实边界

- 所有计时、RSS、缺页与 `mmap` 次数均取自原文在 Intel Xeon E3-1230 v3、`-O2`、50 万步工作负载下的实测；本文未在本机复现，不同 glibc 版本、内核与 CPU 会得到不同数字。
- 原文的玩具分配器是教学简化版（例如头部为 16 字节、无 bins/tcache/arena、无线程支持），性能对照只用于说明机制代价，不是分配器评测。
- glibc 官方 MallocInternals wiki 本次被反爬挑战页拦截，bin/tcache/arena 的机制描述以原文、`mallopt(3)` 与 `brk(2)` 等 man page 交叉核对为准。
- 原文代码在 `benmandrew/malloc-snippets` 的 `v1` tag 可复现；本文未下载运行。

## 六、结论

把「`malloc` 向内核要内存」这句话改成准确的版本，需要四层：批量向内核拿（`brk` 132 KiB 一步到位）、在用户态切块（16 字节对齐的 chunk 头）、分尺寸复用（bins + tcache）、按大小决定还法（堆顶 trim 或 `munmap`）。作者用四个越来越完整的玩具分配器，把每层带来的速度与内存变化都量成了数。

最反直觉、也最有用的一条是：默认 glibc 全部 `free` 之后仍留 19 MiB，而关掉 tcache 只剩 0.250 MiB、每步却慢 1.5 倍。你以为在观察内存泄漏，其实是在观察一台为了少进内核而故意不舍得还内存的机器。 长跑服务里 RSS 一路涨，得先分清是碎片（活块钉住堆顶，还不回去）还是缓存（留着等下次发），两者的处理方式完全不同。

## Sources

- Ben M. Andrew《What is malloc doing, anyway?》（2026-11-08）：<https://benmandrew.com/articles/what-is-malloc-doing-anyway>
- 可复现代码：<https://github.com/benmandrew/malloc-snippets/tree/v1>
- `mallopt(3)`：<https://man7.org/linux/man-pages/man3/mallopt.3.html> ｜ `brk(2)`：<https://man7.org/linux/man-pages/man2/brk.2.html> ｜ `mmap(2)`：<https://man7.org/linux/man-pages/man2/mmap.2.html>
- glibc MallocInternals：<https://sourceware.org/glibc/wiki/MallocInternals>
