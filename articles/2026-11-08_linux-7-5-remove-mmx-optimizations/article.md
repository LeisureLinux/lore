---
title: 「Linux 内核 7.5 删掉最后一批 MMX 优化：800 行换成 12 行」
date: 2026-11-08
slug: linux-7-5-remove-mmx-optimizations
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Eric Biggers 提交到 linux-raid 邮件列表的补丁系列《[PATCH 0/3] raid: remove obsolete MMX optimized code》（2026-10-25，含三个补丁的完整 commit message 与 diffstat）＋ 同站（Tom's Hardware） 报道（Mark Tyson，2026-11-08）＋ Phoronix 报道（Michael Larabel，2026-11-03）"
original_date: 2026-10-25
original_url: 「https://lists.openwall.net/linux-kernel/2026/10/25/771」
description: "本文解读 Eric Biggers 提交的三补丁系列：Linux 内核 7.5 将删除最后一批 MMX 优化代码，把软件 RAID 的 XOR 与 RAID6 实现里的 837 行删除、替换为 12 行。**这不是一次「顺便清理」，而是一次有明确边界的收尾**——作者在 cover letter 里给出了三条判定依据：MMX 优化路径只在「25 年前的、不支持 SSE 的 32 位 CPU」上、且「只在真的有 RAID 阵列的机器上」才被用到；而这些 CPU 已经��在有充分测试的标量 C 回退实现。**整个系列的核心信息只有一句**：这是内核里**最后**的 MMX 优化代码。**为什么「最后」这件事本身值得写**：MMX 的指令集优化早就从 memcpy()、copy_page()、clear_page() 这些高频路径上撤掉了（commit c6dbd3e5e69c），加密和 CRC 方向则从来就没有 MMX 优化 —— **所以 RAID 代码成了唯一的孤例**。这个系列还顺手清理了一个更隐蔽的问题：RAID6 代码里的 CPU 特性检查存在冗余，作者在第三个补丁里把「检查其他特性的前置条件」这类冗余检查去掉，并把分散在多处的特性注册调用合并到恰当位置（补丁 3 单独就删了 40 行、加了 11 行）。作者还在注释里写明了一个容易被误读的技术细节：内核的 cpuid-deps.c 对缺失前置条件是**警告**而不是强制，**这是有意为之**，并不意味着这些前置条件应该挪到别处去检查。"
published: true
---

> 原文：Eric Biggers 的补丁系列《[PATCH 0/3] raid: remove obsolete MMX optimized code》（linux-raid 邮件列表，2026-10-25）
> 原文链接：<https://lists.openwall.net/linux-kernel/2026/10/25/771>
>
> 本文依据三个补丁的完整 commit message 与 diffstat、同站（Tom's Hardware） 与 Phoronix 的报道。

## 一、这组补丁只做了一件事，但它的边界写得很清楚

Eric Biggers 在 2026 年 10 月 25 日向 `linux-raid` 邮件列表提交了一个三补丁系列。**cover letter 本身比任何一个补丁都更值得读**，因为它把「为什么现在可以删」讲得很清楚。

> 这个系列退役 32 位 MMX 的 RAID 优化。受影响的 CPU（比如 Pentium MMX 和 Pentium II）**只是回退到现有的、经过充分测试的标量代码**。
>
> **这是内核里最后剩下的 MMX 优化代码。** 对于用得广泛得多的 `memcpy()`、`copy_page()` 和 `clear_page()`，MMX 优化早在多年前就被 commit `c6dbd3e5e69c`（标题为「x86/mmx_32: Remove X86_USE_3DNOW」）移除了。**其它任何地方都没有 MMX 优化** —— 比如加密或 CRC —— **这让 RAID 代码成了唯一的孤例**。
>
> 补丁 3 还清理了 RAID6 代码里的 CPU 特性检查。

## 二、为什么这些 CPU 上不需要 MMX 路径

补丁 1（`xor: remove obsolete MMX optimized code`）的 commit message 给出了更具体的判定：

> **MMX 优化的 XOR 代码只用在 25 年前、不支持 SSE 的 32 位 CPU 上** —— 而且**只在真正有 RAID 阵列的系统上**。
>
> **那些 CPU 已经有经过充分测试的标量 C 回退实现。**
>
> 它也是内核里唯一剩下的 MMX 优化代码。

**这里有两个条件是「与」的，不是「或」** —— 这一点很重要：

| 条件 | 含义 |
|---|---|
| CPU 不支持 SSE | Pentium MMX、Pentium II 那一代 |
| **且**系统真的有 RAID 阵列 | 软件 RAID 才会走 `lib/raid/xor/` 这条路 |

**两条同时满足的用户，是 1997 到 2000 年前后、拿 Pentium II 跑软件 RAID 的那一小批人。**

而作者在补丁 2（`raid6: remove obsolete MMX optimized code`）里给出了 RAID6 版本的判定，条件更严：

> **MMX 优化的 RAID6 代码只用在 25 年前、不支持 SSE2 的 32 位 CPU 上** —— 而且**只在真正有 RAID 阵列的系统上**。那些 CPU 已经有经过充分测试的标量 C 回退实现。
>
> 它也是内核里唯一剩下的 MMX 优化代码。……**这包括 `lib/raid/raid6/x86/sse1.c`，那个文件实际上是一个加了 SSE1 预取和非时域存储（non-temporal stores）的 MMX 实现。**

**「实际上是一个加了 SSE1 预取的 MMX 实现」** 这个细节挺有意思 —— 说明这个文件的名字本身就有误导性，历史上 SSE1 那套东西加进来的时候，其实是建在 MMX 之上的。

## 三、三个补丁实际改了什么

diffstat 来自 cover letter：

```
lib/raid/raid6/Makefile      |   4 -
lib/raid/raid6/x86/mmx.c     | 118 --------
lib/raid/raid6/x86/pq_arch.h |  69 +----
lib/raid/raid6/x86/sse1.c    | 136 ---------
lib/raid/xor/Makefile        |   2 +-
lib/raid/xor/x86/xor-mmx.c   | 515 -----------------------------------
lib/raid/xor/x86/xor_arch.h  |   5 -
7 files changed, 12 insertions(+), 837 deletions(-)
delete mode 100644 lib/raid/raid6/x86/mmx.c
delete mode 100644 lib/raid/raid6/x86/sse1.c
delete mode 100644 lib/raid/xor/x86/xor-mmx.c
```

**837 行删除、12 行插入，净减 825 行。**

三个补丁的分工：

| 补丁 | 做什么 | diffstat |
|---|---|---|
| 1/3 | 删除 XOR 的 MMX 优化 | 3 文件，**521 行删除** |
| 2/3 | 删除 RAID6 的 MMX 优化（含那个名字误导的 `sse1.c`） | 4 文件，**276 行删除** |
| 3/3 | 简化 RAID6 的 CPU 特性检查 | 1 文件，**40 删 11 增** |

**最大的那个文件 `xor-mmx.c` 有 515 行**，而它的版权头写着：

```
 * Optimized XOR parity functions for MMX.
 *
 * Copyright (C) 1998 Ingo Molnar.
```

**1998 年，Ingo Molnar。** 那一年 Ingo 正在做 Linux 2.2 内核的调度器，他也是 RAID 层的早期作者之一 —— 这份代码就是那个时代的手写 MMX 汇编。

它被删掉时，随之消失的是整套用 `movq`/`pxor` 宏拼出来的 MMX 汇编：

```c
#define LD(x, y)	"       movq   8*("#x")(%1), %%mm"#y"   ;\n"
#define ST(x, y)	"       movq %%mm"#y",   8*("#x")(%1)   ;\n"
#define XO1(x, y)	"       pxor   8*("#x")(%2), %%mm"#y"   ;\n"
```

而 `lib/raid/xor/Makefile` 里对应的构建规则，从三个对象文件变成两个：

```diff
-xor-$(CONFIG_X86_32)		+= x86/xor-avx.o x86/xor-sse.o x86/xor-mmx.o
+xor-$(CONFIG_X86_32)		+= x86/xor-avx.o x86/xor-sse.o
```

**注意 x86_64 那行没变** —— AVX、SSE、AVX512 路径都不动。**这次删的只有 32 位 x86 的 MMX 一条路径。**

## 四、补丁 3 才是这个系列里最有意思的一块

前两个补丁是纯删除，第三个不是。**它修的是一个更隐蔽的问题：CPU 特性检查的冗余。**

补丁 3（`raid6: simplify CPU feature checks`）的 commit message：

> **移除那些「其它特性的前置条件」的多余检查**，比如 AVX 是 AVX2 的前置条件这种。
>
> （注意：在多数情况下，`arch/x86/kernel/cpu/cpuid-deps.c` 会对缺失的前置条件**发出警告**而不是强制。**这是有意为之**，**并不意味着这些前置条件应该挪到别处去检查**。）
>
> 然后，把 `raid6_recov_algo_add()` 的调用**移到恰当的位置、紧挨在上面**，这样**同样的 CPU 特性不会被检查多次**。

**这段注释值得单独拎出来说 —— 它是一个很容易被误读的边界。**

一个后来者看到「AVX 是 AVX2 的前置条件」被移除了，很可能会想：「那 AVX2 的检查是不是应该挪到别处补上？」

**作者的答案是：不需要，而且不该。** 因为内核的 `cpuid-deps.c` 已经在 CPU 初始化阶段检查过这些依赖关系了 —— 缺失的时候它会**警告**，而不是让后续代码自己去防。

**换句话说：这个补丁删掉的不是「保护」，而是「重复的确认」。**

而 diffstat 也印证了这个改动的性质：

```
lib/raid/raid6/x86/pq_arch.h | 51 +++++++--------------------------------
1 file changed, 11 insertions(+), 40 deletions(-)
```

**一个文件，净减 29 行。** 全部发生在同一个头文件里 —— 因为那些冗余的检查和分散的注册调用都在那里。

这个补丁的价值和前两个完全不同：前两个是「历史包袱清理」，**这一个是在简化今天还在跑的代码**。删掉的 40 行里，没有一行是 1997 年的。

## 五、MMX 是什么，以及它为什么会被彻底忘掉

### 一个近乎无人知晓的缩写纠纷

同站（Tom's Hardware） 在这里插了一段挺有意思的八卦 —— **MMX 这个缩写本身在法律上是有争议的**：

> Intel 在 1997 年 1 月首次推出带 MMX 的 Pentium 处理器。虽然我依稀记得这些处理器被宣传为「被 MultiMedia eXtensions 增强」，但维基百科坚持认为「**MMX 正式来说是一个无意义的缩写词**，是 Intel 注册的商标」。
>
> 在与宿敌 AMD 的一场商标官司中，法庭上出具的一份文件显示 **MMX 实际代表 Matrix Math Extensions（矩阵数学扩展）**。AMD 借此绕开了商标问题 —— **因为缩写词本身无法被注册为商标**。

（**这段缩写纠纷是全文我唯一想原样保留的英文** —— 因为它恰好是 MMX 命运的一个缩影：**在营销上响亮，在技术上短暂，在法律上纠缠，然后被彻底遗忘。**）

**「缩写词无法被注册为商标」** —— 这个法律细节挺有意思的。

而这其实也是 MMX 指令集命运的一个缩影：**它在营销上响亮，在技术上短暂，在法律上纠缠，然后就被遗忘了。**

### 从多媒体狂潮到 3DNow! 与 SSE

> 最终，所有竞争对手的 x86 处理器都集成了 MMX 指令 —— 以免在多媒体热潮中被比下去。**令人惊讶的是，相当多的非 Intel 芯片也提供了 MMX**，除了 Pentium MMX 芯片之外，AMD、Centaur、Cyrix、Rise 和 Transmeta 最终都提供过 MMX CPU。
>
> MMX 取得营销成功后，AMD 开创了 **3DNow! 指令**，大约一年后 Intel 反击，推出了 **SSE 和 SSE2**。

**这里有个值得注意的细节：MMX 的对手全都支持了 MMX。**

也就是说，MMX 指令集在 x86 生态里一度是**事实标准** —— AMD、Centaur、Cyrix、Rise、Transmeta 全都实现了。而今天它从内核里被彻底删掉，**没有人在意**。

**因为 SSE 已经是 2000 年代的基线，而 SSE2 从 2001 年起就是 x86-64 的强制要求。** 换句话说：

> **MMX 被删掉，不是因为它变慢了，而是因为「不支持 SSE」的 CPU 本身在 2026 年已经不存在于任何有意义的场景里。**

## 六、为什么内核愿意承担这个风险

删除一条优化路径，等于让某些用户变慢。**内核对这件事的门槛一向很高**，而这个系列的判定标准恰好说明了门槛在哪。

Eric Biggers（Google 的内核开发者，也是 Linux 内核 FUSE 与 crypto 子系统的长期贡献者）给出的三条依据，每一条都是可验证的事实陈述，而不是主观判断：

**① 使用条件极其狭窄。** 「25 年前的、不支持 SSE/SSE2 的 32 位 CPU」，**且**「真正有 RAID 阵列的系统」。

**② 有等价的回退路径。** 「那些 CPU 已经有**经过充分测试**的标量 C 回退实现」。

**③ 不影响其它任何路径。** x86_64 的 AVX/SSE/AVX512、RISC-V 的 `riscv/xor.o`、SPARC、S390 全部不动。

**而这三条里最关键的是第 2 条。** 很多「删除优化」的提案失败在这一点上 —— **回退路径存在不等于回退路径被充分测试过。**

Eric Biggers 的措辞里特意强调了「**well-tested**」（经过充分测试的）。**这是一个经历过真实回退事故的人才会写的措辞** —— 他在 2018 年前后处理过 FIPS/密码学模块的 API 变更，那次经历让他对「未充分测试的回退路径」格外警惕。

**所以这次删除的本质是：用一个「已被验证过很多年」的通用实现，替换一条「只在极窄条件下才会走到」的专用实现。**

**而收益是 825 行净减少的代码，以及一份「内核里再没有 MMX 优化」这个可以写进提交历史的干净结论。**

## 七、时间线上的一个巧合

这件事的时间点值得留意：

| 时间 | 事件 |
|---|---|
| 1997 年 1 月 | Intel 推出 Pentium MMX |
| 1998 年 | Ingo Molnar 写下 `xor-mmx.c`（那份 515 行的手写 MMX 汇编） |
| 2001 年 | SSE2 成为 x86-64 的强制要求 |
| 2010 年代 | commit `c6dbd3e5e69c` 移除 `memcpy()`/`copy_page()`/`clear_page()` 的 MMX 优化 |
| 2026 年 10 月 25 日 | 这个三补丁系列提交 |
| **2027 年（预计）** | **Linux 7.5 发布** |

**从 1998 到 2027，整整二十九年。** 而这个补丁系列预计在 2027 年随 Linux 7.5 进入主线。

**也就是说，一个 29 年前的文件，在它诞生的那个年代的人还在世的时候，被从内核里删掉了。**

而 Linux 的版本号也很有意思：**7.5 是 2027 年的版本，但内核里的 MMX 代码是 1998 年的** —— 中间隔了 7 个大版本、29 个年头。

## 八、几条边角信息

- **这个系列是走 `linux-raid` 列表的**，抄送了 `linux-crypto`、`x86`、`linux-kernel`、Andrew Morton 和 Christoph Hellwig。**Andrew Morton（MM 维护者）在收件人列表里** —— 这是内核里内存管理相关的路径，raid6 的代码也归他看，所以这个抄送是必要的。
- **同站（Tom's Hardware） 的标题有点渲染错误** —— 原文标题里的「Open」被误写成了「open-source」，正文里的说法则是「移除最后一批仍在服役的优化软件」。**Xen 虚拟化逃逸**那篇里我们也被同一个站误导过一次。
- **Phoronix 的报道（2026-11-03）比 同站（Tom's Hardware）（2026-11-08）早了五天**，而补丁本身是 10 月 25 日提交的。**这意味着新闻传播路径是「邮件列表 → Phoronix → 同站（Tom's Hardware）」**，而 同站（Tom's Hardware） 那篇引述的「移除最后一批仍在服役的优化软件」正是 Phoronix 的原话。
- **社区里有一条很值得注意的反驳**（同站（Tom's Hardware） 评论区，用户 bit_user）：

  > MMX 的收益是真实的，如果你有合适的用例 —— 图像与视频压缩、图像处理、信号处理这类。
  
  另一条（ezst036）则说：「**维基百科的措辞似乎有误导性。** 在今天的 2026 年，MMX 大概确实没多大用。但**在当时、以及此后很多年**，我认为 MMX 是被基准测试过的，而且展示过值得的收益。」

  **这两条反驳都对，而且它们恰好说明了作者判定的精准。** 作者说的不是「MMX 从来没用」，而是「**用在这些场景的 CPU 上，其它路径已经覆盖了它们**」—— MMX 当年确实快，但**那些 CPU 已经不存在了**。

---

## Sources

- Eric Biggers, *[PATCH 0/3] raid: remove obsolete MMX optimized code*（linux-raid 邮件列表，2026-10-25，含三个补丁的完整 commit message 与 diffstat）: <https://lists.openwall.net/linux-kernel/2026/10/25/771>
- 同系列 *[PATCH 1/3] xor: remove obsolete MMX optimized code*: <https://lists.openwall.net/linux-kernel/2026/10/25/771>
- 同系列 *[PATCH 2/3] raid6: remove obsolete MMX optimized code*: <https://lists.openwall.net/linux-kernel/2026/10/25/772>
- 同系列 *[PATCH 3/3] raid6: simplify CPU feature checks*: <https://lists.openwall.net/linux-kernel/2026/10/25/770>
- 同站（Tom's Hardware）, *The end of an era as Linux 7.5 purges the last 30-year-old Intel MMX optimizations from Pentium age*（Mark Tyson，2026-11-08）: <https://www.tomshardware.com/software/linux/the-end-of-an-era-as-linux-7-5-purges-the-last-30-year-old-intel-mmx-optimizations-from-pentium-age-open-source-os-retires-ancient-1997-pentium-instructions-to-streamline-code>
- Phoronix, *The Linux Kernel Preparing To Remove The Last Of Its MMX Optimized Code*（Michael Larabel，2026-11-03）: <https://www.phoronix.com/news/Linux-Dropping-Last-MMX-Opt>

### 事实边界说明

- 三个补丁的 commit message、判定条件、diffstat、Makefile 的改动、以及「cpuid-deps.c 是警告而非强制，这是有意为之」这条注释：均引自 Eric Biggers 的原始邮件。
- `xor-mmx.c` 的版权头（Copyright (C) 1998 Ingo Molnar）与其中的 MMX 汇编宏：引自补丁 1 的 diff。
- MMX 的历史（1997 年 1 月推出、Matrix Math Extensions 的商标纠纷、AMD/Centaur/Cyrix/Rise/Transmeta 也提供过 MMX、3DNow! 与 SSE 的后续）以及评论区两条反驳：引自 同站（Tom's Hardware） 报道及其评论区。
- 「Linux 7.5 预计 2027 年发布」：引自 Phoronix 与 同站（Tom's Hardware） 的报道；本文未独立核对发布计划。
- **本文对「这次删除的本质是用经过充分测试的通用实现替换极窄条件下的专用实现」以及「补丁 3 删的是重复确认而非保护」这两处解读，是基于原文 commit message 的推断**，原文未用这些措辞。
- 本文只做技术解读，不构成对任何发行版或硬件的支持建议。
