---
title: "内核编译时间砍掉 36%：而这 21 个补丁的第一作者承认，AI 写的代码「大部分很难看」"
date: 2026-10-21
slug: linux-7-4-kbuild-build-speedup-ai-assisted
tags: [Linux, Linux 7.4, Kbuild, 内核编译, 构建速度, Lorenzo Stoakes, Arm, kallsyms, modpost, objtool, mksysmap, pigz, Rust, 增量编译, no-op 构建, allmodconfig, defconfig, EPYC, Threadripper, Assisted-by, LLM, 补丁系列]
category: 内核/开发
author: FreeLAMP.com
original_source: "Linux 内核邮件列表原始补丁系列 cover letter（Lorenzo Stoakes，ARM）+ Phoronix 报道与实测"
original_author: "Lorenzo Stoakes（ARM，Linux MM 开发者）；Michael Larabel（Phoronix）"
original_date: 2026-10-21
original_url: "https://www.phoronix.com/news/Linux-7.4-Kbuild"
description: "Linux 7.4 正在合入一组把内核编译时间砍掉三分之一的补丁。它们的作者是 ARM 工程师 Lorenzo Stoakes，而他在 cover letter 里写了一段罕见诚实的话：AI 写出了大量代码，其中大部分很难看，他逐个审计并重写了。本篇给出原始 benchmark 表格、逐个补丁的技术拆解、验证做到了什么程度，以及同一周内核社区正在讨论取消 Assisted-by 标签这件事。"
published: true
---

> 来源：本文的技术数据全部来自一手材料：[Lorenzo Stoakes 的补丁系列 cover letter（v2，Linux 内核邮件列表）](https://lists.infradead.org/pipermail/linux-riscv/2026-September/098647.html)、[v4 版本（22 个补丁）](https://lore.kernel.org/lkml/20261018035817.GA2365306@ax162/)、[Phoronix 10 月 21 日的合入报道](https://www.phoronix.com/news/Linux-7.4-Kbuild)、[Phoronix 的「逼近 10 秒内核编译」实测](https://www.phoronix.com/review/near-10-sec-kernel-build)、以及[内核社区关于取消 `Assisted-by` 标签的讨论](https://www.phoronix.com/news/Linux-Dropping-Assisted-By-Req)。
> 本文为**技术解读**。第六节的判断是笔者补充的部分。

## 一句话结论

**内核编译时间在 Linux 7.4 里被砍掉了三分之一（allmodconfig 最多 -36%，增量最多 -70%，no-op 最多 -90%），而这件事的特别之处不在速度，在于它的作者把「AI 参与到了什么程度」写得比大多数团队都清楚。**

**Lorenzo Stoakes（ARM，Linux MM 开发者）在 cover letter 里专门开了一节叫 `LLM usage`，原话是**：

> **「An LLM was used to first determine where the bottlenecks were then to figure out how to improve them. It generated a lot of code, much of it hideous. I extensively audited and rewrote a lot of it, and heavily edited commit messages, the cover letter and comments. The LLM has also orchestrated build runs, testing, debugging and analysis. I have manually checked for correctness in both build and running kernels generated with this series applied. Performance improvements were also verified manually. Since an LLM was used extensively, each commit carries an Assisted-by tag.」**

**翻成中文**：

> **「LLM 首先被用来确定瓶颈在哪里，然后 figuring out 如何改进它们。它生成了大量代码，其中很多很难看。我广泛地审计并重写了其中很大一部分，并重度编辑了 commit message、cover letter 和注释。LLM 还编排了构建运行、测试、调试和分析。我手工检查了打上这个系列之后生成的内核在构建和运行两方面的正确性。性能提升也做了手工验证。因为 LLM 被大量使用，每个 commit 都带 Assisted-by 标签。」**

**「It generated a lot of code, much of it hideous」**。**这句话的分量，比后面所有的性能数字都重。**

**而时间点很微妙**：**这个系列正在合入内核的同一周，内核社区正在讨论取消 `Assisted-by` 标签的强制要求。** **一边是「每个 commit 都带 Assisted-by」，一边是「这个标签不要了」。**

## 术语速查

| 缩写 / 术语 | 含义 |
|---|---|
| **Kbuild** | Linux 内核的构建系统，取代老式 Makefile 体系 |
| **vmlinux** | **未压缩、未剥离符号的内核 ELF 可执行文件**，链接的最终产物 |
| **System.map** | 内核符号名到地址的映射表 |
| **kallsyms** | 内核对自身符号表的运行时表示，导给用户空间（`/proc/kallsyms`） |
| **mksysmap** | 历史上**用 shell 脚本**从 `nm` 输出生成 System.map 的工具 |
| **modpost** | 模块构建阶段，读 `.modpost` 做符号解析与版本检查 |
| **objtool** | 校验并标注 x86 指令，做 ORC（运行时重定位）分析 |
| **modinfo** | 内嵌在模块里的元信息段 |
| **allmodconfig** | 构建配置：**所有内核模块都编**，最重的配置 |
| **defconfig** | 构建配置：默认的最小功能集，最常见的配置 |
| **增量构建（incremental）** | 改一个文件后重新构建 |
| **no-op 构建** | `make` 跑一遍但**什么都要做**（所有目标都是最新的） |
| **pigz** | gzip 的并行实现 |
| **KBUILD_RUST_THREADS** | 让 rustc 前端多线程运行的构建变量 |
| **CPU 秒** | 所有核心的 CPU 时间之和，和墙钟时间不同 |
| **单线程瓶颈** | 整个构建里**没法并行**的那一段（串行尾巴） |
| **Assisted-by** | 内核用于标注「AI 参与」的 trailer |

## 一、这不是「AI 帮内核写代码」的故事

**先把一个容易产生的误解纠正掉：这不是「AI 给内核写了个新功能」的故事。**

**这组补丁在做的事情非常朴素：把构建过程里那些卡在单线程上的部分找出来，并行化或者加速。** **作者在 cover letter 第一句就说**：

> **「A typical kernel build consists of a frustratingly large amount of time spent stuck in single-threaded bottlenecks.」**
>
> **「一次典型的内核构建，有令人沮丧的大量时间卡在单线程瓶颈上。」**

**而这整件事的起点，发生在 2026 年 9 月初**：Phoronix 当时报道的标题相当刺眼：**「AI Made A Lot Of 'Hideous' Code But Found Major Bottlenecks For Faster Linux Compilation」**（AI 写出了大量「很难看」的代码，但找出了加速 Linux 编译的主要瓶颈）。

**注意这个标题的因果关系**：**AI 写的代码很难看，但 AI 找瓶颈这件事本身成了整个工作的关键。**

**而作者自己在 cover letter 里的定位也和这个标题一致**：

> **「Fundamentally the series improves build times by parallelising single-threaded tasks as much as possible and improving the efficiency of code used in the build process.」**
>
> **「这个系列从根本上是通过尽可能并行化单线程任务、并提升构建过程所用代码的效率，来改善构建时间的。」**

**并且他明确划了边界**：

> **「There are further improvements that could be made, but they would either by very invasive (large scale C header changes) or generate diminishing returns.」**
>
> **「还有进一步的改进空间，但它们要么会非常侵入性（大规模 C 头文件改动），要么收益递减。」**

**这句话的诚实程度和那个 `LLM usage` 段落一样：它告诉你这个系列没有做完，也告诉你为什么没做完。**

## 二、原始数据：三张表

**这是我最想给读者的部分，因为它是作者的原始 benchmark，没有经过任何中间人的转述。**

**测试机器（作者自己列的）**：

- **Threadripper**：AMD Threadripper 9980X，64 核 128 线程
- **EPYC**：双路 EPYC 9754，256 核 512 线程
- **M2**：2022 款 M2 MacBook Pro，8 核（4 性能 + 4 能效）

**⚠️ 而作者同时给出了一个很重要的前置条件，很多转述会略过它**：

> **「Performance numbers are based on a build which: Has these series applied (as these supersede changes from a previous version of this series) ... Runs `make KBUILD_RUST_THREADS=8 -j $(nproc) ...`. Runs with the pigz tool installed locally.」**
>
> **「性能数字基于的构建满足：应用了这个系列（它们取代了本系列前一个版本的一些改动）……以 `make KBUILD_RUST_THREADS=8 -j $(nproc) ...` 运行。本地安装了 pigz 工具。」**

**所以这些数字不是「默认配置下的改进」，而是「应用了这个系列 + 开了 Rust 多线程 + 装了 pigz」的组合结果。** **这一点在评估时不能忽略。**

### 全量构建（allmodconfig FULL build）

| 机器 | 编译器 | before | after | delta |
|---|---|---|---|---|
| Threadripper | gcc | 344.2s | 278.6s | **-65.6s（-19%）** |
| Threadripper | clang | 342.6s | 266.8s | **-75.8s（-22%）** |
| **EPYC** | **gcc** | **188.0s** | **121.1s** | ⭐ **-66.9s（-36%）** |
| EPYC | clang | 259.5s | 184.6s | -74.9s（-29%） |

### 增量构建（allmodconfig INCREMENTAL build）

**这一组数字对日常内核开发者最有价值，因为它对应的是「我改了一行代码，然后等构建」的那个循环。**

| 机器 | 编译器 | before | after | delta |
|---|---|---|---|---|
| Threadripper | gcc | 40.1s | **15.4s** | **-24.7s（-62%）** |
| Threadripper | clang | 40.3s | 15.6s | -24.8s（-61%） |
| EPYC | gcc | 70.9s | 24.3s | -66%（-46.6s） |
| EPYC | clang | 70.4s | 24.3s | -65%（-46.1s） |

### no-op 构建（什么都没改，直接 make）

**这一组是最夸张的**：

| 机器 | 编译器 | before | after | delta |
|---|---|---|---|---|
| Threadripper | gcc | 15.3s | **1.4s** | **-13.9s（-91%）** |
| Threadripper | clang | 16.2s | 1.8s | -14.4s（-89%） |
| EPYC | gcc | 30.6s | **1.5s** | **-95%** |
| EPYC | clang | 32.3s | 2.2s | -93% |

**「什么都没改，构建时间从 30.6 秒降到 1.5 秒」。** **这就是那个「反复探测编译器/链接器选项」的开销被彻底消掉之后的直接结果。**

**而 defconfig（最常见的配置）的数字要保守一些**：

| 机器 | 编译器 | before | after | delta |
|---|---|---|---|---|
| Threadripper | gcc | 32.5s | 26.3s | -19% |
| Threadripper | clang | 34.5s | 27.2s | -21% |
| **EPYC** | **gcc** | **28.7s** | **20.6s** | **-28%** |
| EPYC | clang | 39.8s | 32.2s | -19% |
| **M2** | **gcc** | **519.3s** | **512.4s** | ⚠️ **-1%** |
| M2 | clang | 634.5s | 569.4s | -10% |

**⚠️ 注意 M2 的 defconfig gcc 只有 1% 的提升，而 clang 有 10%。** **这个 10 倍差异作者没有解释，但从数据上看，这说明 M2 上 defconfig 的时间被别的东西主导了**（大概率是 Rust 部分或架构特定代码），**而不是被这个系列瞄准的「串行尾巴」主导**。**这一点值得记住：不是所有配置都同等受益。**

## 三、21 个补丁到底改了什么

**cover letter 里作者自己列的清单，我逐条翻译并说明它解决什么。**

### kbuild (1)：把 `.modinfo` 做成 INFO 段

> **「kbuild (1): Make .modinfo an INFO section.」**

**`.modinfo` 是内核模块里内嵌的元信息（许可证、作者、依赖、版本等）。** **而这个补丁把它从 vmlinux 里挪走了**，也就是说，**链接最终 vmlinux 的时候不再需要为它分配空间**。**这就是 Phoronix 报道里第一条「avoiding allocating .modinfo in vmlinux」的来源。**

### kallsyms (2, 3)：用缓存换效率

> **「kallsyms (2, 3): Some efficiency improvements through use of a cache.」**

### kbuild (4, 5)：不排序 nm 输出、kallsyms 试链接不带重定位

> **「kbuild (4, 5): Don't sort nm output unnecessarily, do not include relocations in the kallsyms trial links.」**

**「不必要地排序 nm 输出」这一条对应 Phoronix 报道里的「unnecessary sorting」。**

**而「kallsyms 试链接不带重定位」这条是纯技术优化**：**kallsyms 需要做一次试链接来估算符号表大小，而如果这次试链接带了重定位信息，它要处理的 DWARF 数据量会大得多。**

### elf-parse (6)：为下一个补丁铺路

> **「elf-parse (6): Section flags, symbol binding and a read-only mapping, for the next patch.」**

**这是一个铺垫型补丁**：**先让 elf-parse 能读段标志、符号绑定类型，并且支持只读映射（mmap 出来的 ELF 可以直接只读打开，不用复制）。**

### kallsyms (7)：不再用 nm，直接读 ELF 符号表

> **「kallsyms (7): Don't use nm, read the ELF symbol table directly.」**

**⭐ 这一条是整个系列里最有意思的技术改动。**

**原来的做法是：调用 `nm` 工具去 dump 符号，然后处理 `nm` 的文本输出。** **新做法是：直接用 C 代码解析 ELF 文件的符号表。**

**这为什么快？** **因为 `nm` 是一个外部进程，而且它的输出是文本格式，需要被文本解析器重新解析。** **而直接读 ELF 符号表，跳过了「起进程 + 文本序列化 + 文本解析」这一整条链。** **这也正好呼应了后面第 21 号补丁（把 mksysmap 用 C 重写）的思路。**

**而且这一条还顺带消灭了「shell 脚本版 mksysmap」**：

> **「for arm64, arm, s390 and loongarch the System.map is identical to what the previous shell mksysmap produces for the same vmlinux.」**
>
> **「对 arm64、arm、s390 和 loongarch 来说，生成的 System.map 与之前那个 shell 版 mksysmap 对同一个 vmlinux 产生的结果完全一致。」**

**「用 C 重写 mksysmap」**，这就是 Phoronix 报道里那条「re-implementing mksysmap in C code」。

### kbuild (8, 9)：对象缓存 + 更高效的依赖时间戳检查

> **「kbuild (8, 9): Implement a cache to track objects, check dependency timestamps more efficiently.」**

### kbuild (10)：把工具链检查拆成独立的 Kconfig 文件

> **「kbuild (10): Move the toolchain checks into their own Kconfig file.」**

### kbuild (11)：⭐ 只在构建顶部探测一次编译器和链接器选项

> **「kbuild (11): Probe compiler, linker flags once at top of build.」**

**⭐ 这一条是 no-op 构建能从 30.6 秒掉到 1.5 秒的元凶。**

**原来的行为是：每次 `make` 都要重新探测一遍编译器和链接器的选项**（试各种 flag 看能不能过）。**而这些探测结果对同一个工具链来说是不变的。** **新做法是：探测一次，记下来（每个工具链记一份），后续复用。**

**这对应 Phoronix 报道里的「caching more cc-option and ld-option results」。**

**而这里有一个我觉得很值得琢磨的点**：**「探测一次然后缓存」这个思路本身非常朴素，朴素到有点「这也需要写补丁？」的程度。** **但它就是 no-op 构建提速 91% 的原因。** **这说明构建系统的性能问题，有很大一部分根本不是算法问题，而是「重复做没有意义的事」。**

### modpost (12)：用缓存提升性能

> **「modpost (12): Improve performance through use of a cache.」**

### modules (13, 14)：⭐ 把模块描述符从 C 改成汇编

> **「modules (13, 14): Emit module descriptors as assembly (*.mod.S) rather than C (*.mod.c), reducing CPU seconds taken by 10x to perform the task. Also shard module finalisation rather than running 10's of thousands of tiny runs.」**

**⭐ 这一条是我认为整个系列里最漂亮的一个改动。**

**问题在于**：**模块描述符（`.mod.c`）是一个自动生成的 C 文件，里面只有一堆结构体赋值。** **问题在于：编译一个只含赋值的 C 文件，本身要跑完整的编译流程。** **而模块多了之后，这是成百上千次这样的编译。**

**解法**：**改用汇编（`.mod.S`）。** **因为汇编不需要编译成中间表示再优化，汇编器直接处理，速度快得多。** **结果是 CPU 时间降到 1/10。**

**而「shard module finalisation」（把模块收尾工作分片）解决的是另一个问题**：**原来收尾阶段是「跑几万次小任务」，也就是几万次进程启动。** **分片之后，这些可以并行。**

**这一条同时命中了「单线程瓶颈」和「无意义的重复工作」两个靶心。**

### objtool (15-17)：不让 DWARF 重定位淹没哈希表

> **「objtool (15-17): Avoid polluting the reloc hash with millions of DWARF relocations, size the instruction hash to the code rather than hard-code it, and decode large objects over multiple threads.」**

**三条：**

1. **「避免用数百万个 DWARF 重定位污染重定位哈希表」**，哈希表被灌满之后，查找会退化
2. **「按代码大小而不是硬编码来定指令哈希表尺寸」**，硬编码的尺寸对大对象不合适
3. **「多线程解码大对象」**，又是一处并行化

### rust (18-20)：让 rustc 前端多线程

> **「rust (18-20): Optionally run the rustc front end on several threads, set correct dependencies and build crates in parallel with C code, retaining the requirement that rust/ crates are built first.」**

**「让 rustc 前端跑在多个线程上」，并且「修好依赖关系，让 Rust crate 能和 C 代码并行构建，同时保留「rust/ crate 必须先构建」这个要求」。**

**这一条是 Linux 7.4 时代特有的问题**：**Rust 代码进入内核后，Rust 工具链的前端（rustc 的前端分析阶段）本身是单线程的**，**这会在有大块 Rust 代码的内核上形成一个新的串行瓶颈。** **而 `KBUILD_RUST_THREADS=8` 这个变量就是为此存在的。**

**⚠️ 顺便说明：这也是为什么上面那张 benchmark 表有前置条件。** **不开 `KBUILD_RUST_THREADS`，Rust 部分还是串行的。**

### kbuild (21)：⭐ 默认用 pigz

> **「kbuild (21): Default to using a parallel implementation of gzip (pigz) if available on the system.」**

**如果系统里有 pigz，就默认用它。** **这是唯一一个「配置改默认行为」的补丁，其余 20 个都是纯性能改动。**

**⚠️ 而它同时也是那份 benchmark 的前置条件之一**（作者要求「本地安装了 pigz」），**换句话说，pigz 这个补丁本身贡献的那部分收益，在那张表里已经被算进去了。**

## 四、验证做到了什么程度

**这一节是我认为比性能数字更重要的部分。** **因为「一个 AI 参与的补丁系列被合进内核」这件事，读者最该问的问题是「你怎么知道它是对的」。**

**作者的 `Testing` 段落写得相当扎实**：

> **「Beyond x86, allmodconfig was built with the series for arm64, arm, riscv, powerpc64, s390 and loongarch, and for arm64, arm, s390 and loongarch the System.map is identical to what the previous shell mksysmap produces for the same vmlinux.」**
>
> **「除了 x86 之外，还用这个系列为 arm64、arm、riscv、powerpc64、s390 和 loongarch 构建了 allmodconfig；并且对 arm64、arm、s390 和 loongarch，生成的 System.map 与之前 shell 版 mksysmap 对同一个 vmlinux 的结果完全一致。」**

> **「Also tested were parisc64 and m68k build as far as mainline lets them (a driver's static assertion and an undefined-symbol check on parisc, gcc 16 internal compiler errors on m68k, none of it from this series).」**
>
> **「也测试了 parisc64 和 m68k 构建，测试到主线允许的程度（parisc 上有一个驱动的静态断言和一个未定义符号检查，m68k 上有 gcc 16 的内部编译器错误，都不是这个系列引入的）。」**

**⚠️ 请注意最后那半句：「都不是这个系列引入的」。** **作者明确把「构建失败」和「我的补丁无关」区分开了，而不是含糊过去。**

> **「Kernels for x86, arm64, arm, riscv, loongarch, powerpc64, s390, m68k and parisc64 all boot under qemu, every text symbol of System.map is in /proc/kallsyms at the relocated address, and a module loads and unloads.」**
>
> **「x86、arm64、arm、riscv、loongarch、powerpc64、s390、m68k 和 parisc64 的内核全部能在 qemu 下启动，System.map 里的每一个文本符号都能在 /proc/kallsyms 里以重定位后的地址找到，且模块能加载和卸载。」**

**⭐ 「每一个文本符号都能在 `/proc/kallsyms` 里以重定位后的地址找到」**。**这一条特别关键，因为这个系列改的正是 kallsyms。** **它验证的不是「能编译」，是「符号表本身是对的」，而且是在 9 个架构上验证的。**

> **「The s390, arm and loongarch kernels also pass the kallsyms selftest.」**
>
> **「s390、arm 和 loongarch 的内核还通过了 kallsyms 自测。」**

**再补两条**：

- **「An x86 kernel with CONFIG_MODVERSIONS, CONFIG_EXTENDED_MODVERSIONS and CONFIG_MODULE_SRCVERSION_ALL boots, loads and unloads modules.」**（带模块版本校验和源码版本校验的配置也测了）
- **「External modules build against both in-tree and O= builds, and every commit builds on x86 defconfig.」**（外部模块、O= 分离输出目录、以及「每一个 commit 单独都能构建」都测了）

**最后这一条「every commit builds on x86 defconfig」值得单独说**：**它保证了 bisect 友好。** **如果系列中间有任何一个 commit 单独构建不过，bisect 就会在那个 commit 上卡住。**

## 五、这些数字在真实硬件上是什么样子

**Phoronix 9 月 25 日做了一次独立实测（不是复现 Stoakes 的 benchmark，而是在自己的机器上用真实发行版跑）**：

**机器配置**：

- **AMD EPYC 9575F 2P**（双路），**24 × 64GB DDR5-6400**，**Samsung PM1743 3.84TB PCIe Gen 5.0 NVMe SSD**
- **Stock Ubuntu 26.04 LTS**，**EXT4**，**没有用 TMPFS**，**也没有把内核构建放在内存里**

**⚠️ 这一点我特别想强调**：**Phoronix 明确说自己没有把构建放在 TMPFS 上，「没有在 RAM 里构建内核或其他激进设置来把构建时间推得更高」。** **这让这个数字更可信，因为很多「极速构建」的宣传都是靠内存盘。**

**结果**：

- **defconfig 全量构建：从 22 秒降到 15 到 17 秒**（**配合 AMD 的 power determinism 模式**）
- **allmodconfig：削掉 30 多秒，逼近两分钟**
- **在所有 x86 defconfig 构建基准里，AMD EPYC 9575F 2P 稳定排第一**，通常在 20 秒左右

**而 Phoronix 自己的评论也点出了这次变化的真正价值**：

> **「The Kbuild improvements also deliver even more dramatic wins for relative performance for those doing more common incremental builds of the kernel when working on Linux kernel changes, bisecting kernel regressions, etc.」**
>
> **「Kbuild 的改进对于做更常见的增量构建（改内核代码、二分查找回归等）的人，带来了更显著的相对性能提升。」**

**⭐ 「二分查找回归」**，**这才是内核构建时间真正的意义所在。** **一个内核开发者 bisect 一次可能要做几十次构建，每次几分钟。** **把增量构建从 40 秒降到 15 秒，直接决定了他今天能不能把那个 bug 定位完。**

**而 Phoronix 有一个说法我觉得很值得记下来**：

> **「The coffee window is closing.」**
>
> **「喝咖啡的时间窗口正在关闭。」**

**以及那句更直白的**：

> **「Absolutely mind boggling to think compiling a defconfig x86 Linux kernel build in a matter of seconds」**
>
> **「想到编译一个 defconfig 的 x86 Linux 内核只需要几秒钟，简直不可思议。」**

**而 Phoronix 还留了个悬念**：

> **「Now any bets if AMD's upcoming Venice CPUs like the recently announced EPYC 9686F + MRDIMMs + PCIe Gen6 storage will be able to cross the 10 second mark for a default Linux 7.4+ kernel build?」**
>
> **「那么 AMD 即将发布的 Venice 系列（比如刚公布的 EPYC 9686F + MRDIMM + PCIe Gen6 存储）能不能把默认的 Linux 7.4+ 内核构建压到 10 秒以下，我们来赌一把？」**

**而 Phoronix 的作者 Michael Larabel 在 10 月 21 日那篇里说，他会在 7.4-rc1 打标之后跑一轮新的 benchmark**。**也就是说，本文引用的这些数字都是「系列部分合入」时的状态，完整合入后的数字还没出来。**

**⚠️ 这一点必须标注：7.4-rc1 当时尚未打标，已合入的只是「初始的一批改动」。**

## 六、同一周，内核社区在讨论取消「AI 参与」标签

**这件事的时间点太巧了，所以我想单独说。**

**Phoronix 10 月 13 日报道**：

> **「Currently there is a policy requirement for Linux kernel patches where AI tools contributed, they should be documented with an 'Assisted-by:' tag to make clear AI was used in the creation of said patch. But Linux kernel developers are now looking at dropping this requirement amid the rampant use of AI/LLMs.」**
>
> **「目前内核补丁有一个政策要求：如果 AI 工具参与了创作，就应当用 'Assisted-by:' 标签注明，以明确说明这个补丁里用了 AI。但内核开发者们现在正在考虑取消这个要求，因为 AI/LLM 的使用已经泛滥。」**

**而变化的过程是**：

- **「A patch removing the Assisted-by requirement was recently posted to the Linux kernel mailing list.」**（有人提了移除这个要求的补丁）
- **「At the Linux Maintainers Summit last week in Prague, there was reportedly consensus on deprecating this requirement.」**（上周在布拉格的内核维护者峰会上，据说达成了「弃用这个要求」的共识）
- **「Not all are in favor of this decision... the LKML thread resulting in mixed views」**（不是所有人都同意，邮件列表上意见不一）

**⚠️ 而那个移除补丁的动机是「因为 AI/LLM 的使用已经泛滥」。** **这是一个非常坦白的理由，它承认的不是「AI 参与是不好的」，而是「AI 参与太普遍了，标注已经没有信息量」。**

**那么把这两件事放在一起看，会得到一个挺有意思的结论**：

**一边是一个 AI 深度参与的补丁系列合入了内核，而它的作者用一种近乎坦白的措辞描述了 AI 参与到了什么程度，逐个 commit 挂 `Assisted-by` 标签，并且说「AI 生成的代码大部分很难看，我重写了其中很大一部分」。**

**另一边是内核社区在决定取消这个标签。**

**⚠️ 我的判断是：这两件事不矛盾，反而是同一个问题的两面。**

**`Assisted-by` 标签的设计目的，本来是给读者一个「这份代码有多少是人写的」的信号。** **而 Stoakes 的 cover letter 恰恰说明了为什么这个信号会失效：**

**当一个补丁系列里，AI 负责「找瓶颈」和「生成初版」，而人类负责「审计、重写、验证」时，「这个补丁有没有用 AI」这个二元问题就不够了。** **真正有价值的信息是「AI 参与到了哪一步」**。**而 `Assisted-by` 这个 trailer 恰好把这个问题压缩成了一个是/否。**

**Stoakes 的处理方式我认为比「打标签」和「不贴标签」都更好**：**他不是不打标签，他是**用 cover letter 写清楚 AI 参与了哪几个环节、人做了什么、哪些部分是 AI 生成后被重写的**。** 这比一个 trailer 承载的信息量大得多。

**⚠️ 但我也要说清楚一点：这也是一个「幸存者偏差」样本。** **一个能把 AI 产出审计到「System.map 与之前完全一致」并在 9 个架构上验证的作者，和一个只把 AI 生成的代码直接提交上去的作者，是完全不同的两回事。** **而内核社区讨论取消标签，某种程度上也是在回应后者那一类情况。** **所以我倾向于认为结论不是「取消标签是对的」，而是「标签的粒度不够，需要的是更细的披露方式」。**

## 七、我的判断

**第一，这件事最值得学的不是「AI 能加速内核构建」，而是「AI 找瓶颈、人做验证」这个分工形态。** **因为回顾整个工作流：AI 做的事是「在几千行构建脚本里找出哪些是单线程的」，这恰好是 AI 擅长的（大规模模式识别 + 大量试错）；而人做的事是「判断这个改动对不对」「这个架构上符号表还准不准」，这恰好是人擅长的（语义理解 + 责任承担）。** **分工的边界画得很自然，不是我事后总结的，是这个系列实际跑出来的形态。**

**第二，`LLM usage` 那一段应该成为行业范本。** **它做了三件很少有人做的事**：**明确说「AI 生成了大量很难看的代码」**（不掩饰）；**明确说「我审计并重写了其中很大一部分」**（不模糊）；**明确说「正确性我手工检查过」**（不甩锅）。** 我认为这比任何「我们用 AI 提升了效率 40%」的营销话术都有说服力，因为它给出了可以被人质疑的细节。** **而它同时也给了社区一个可以据此判断「该不该取消 Assisted-by」的依据**：**取消的理由是「泛滥」，但这个系列说明，即使 AI 深度参与，有一份这样的披露就足以让读者判断风险。**

**第三，那个 91% 的 no-op 构建提速，是一个比 36% 全量构建更重要的数字，但它不会出现在任何新闻标题里。** **因为「什么都没做所以快了」听起来没有说服力。** **但它的含义是：** **在这个系列之前，你每次 `make` 都要为「重新探测工具链」付 15 到 30 秒。** **这是纯粹的浪费，而且浪费了很多年。** **我认为这提醒了一件事：构建系统的性能问题，很大一部分根本不是算法复杂度问题，而是「反复做结果不会变的事」。** **而这类问题之所以长期存在，恰恰是因为它「不痛」：没人会因为构建慢 15 秒而报 bug。**

**第四，关于 Linux 7.4 的合并进度，本文引用的数字需要打折看。** **10 月 21 日 Phoronix 报道的是「初始的一批改动」合入，而 7.4-rc1 尚未打标。** **完整合入后的 benchmark 还没出来。** **所以上面那些百分比，应该理解成「这个系列合完之后能达到的上限」，而不是「7.4 用户现在就能拿到的收益」。**

**第五，最后一个我觉得很有意思但还无法下结论的观察**：**M2 上 defconfig gcc 只有 1% 提升，而 clang 有 10%。** **这 10 倍差异在作者的 cover letter 里没有解释。** **我的猜测是 M2 上 defconfig 的时间被 Rust 部分（或者别的架构特定的东西）主导了，而 GCC 那条路径恰好撞上了某个别的串行点。** **但这只是猜测。** **如果 M2 上的内核开发者有相关体感，值得去邮件列表问一声。**

## 关键事实速查

### 事件基本信息

| 项目 | 内容 |
|---|---|
| **补丁系列** | **`[PATCH v2 00/21] kbuild: significantly speed up kernel builds`**；v4 增加到 22 个补丁 |
| **作者** | **Lorenzo Stoakes（ARM，Linux MM 开发者）**，邮箱 `ljs@kernel.org` |
| **合入版本** | **Linux 7.4**（2026-10-21 报道称「初始的一批改动」已合入，**7.4-rc1 当时尚未打标**） |
| **改动范围** | **kbuild、kallsyms、modpost、objtool、mksysmap、rust 构建系统** |
| **合入 PR** | **`lore.kernel.org/lkml/20261018035817.GA2365306@ax162/`** |
| **起点** | **2026 年 9 月初**：AI 找构建瓶颈；v1 于 2026-09-08，v2 于 2026-09-14 |

### 性能数字（作者原始 benchmark）

| 项目 | 内容 |
|---|---|
| ⭐ **全量构建** | **allmodconfig 最多 -36%**（EPYC + gcc：188.0s → 121.1s）；Threadripper -19%（gcc）/ -22%（clang）；EPYC + clang -29% |
| ⭐ **增量构建** | **allmodconfig 最多 -66%**（EPYC + gcc：70.9s → 24.3s）；Threadripper -62%（gcc） |
| ⭐ **no-op 构建** | **最多 -95%**（EPYC + gcc：30.6s → **1.5s**）；Threadripper -91% |
| **defconfig 全量** | EPYC + gcc -28%（28.7s → 20.6s）；Threadripper -19%；⚠️ **M2 + gcc 仅 -1%**，M2 + clang -10% |
| **defconfig 增量** | -45% 到 -56%（M2 也达 -45%/-55%） |
| **测试机** | **Threadripper 9980X**（64c/128t）、**双路 EPYC 9754**（256c/512t）、**M2 MacBook Pro 2022**（8c） |
| ⚠️ **前置条件** | **必须应用本系列 + `KBUILD_RUST_THREADS=8` + 本地装 pigz**；**数字不是「默认配置下的改进」** |

### 21 个补丁做了什么

| 编号 | 做什么 | 解决什么 |
|---|---|---|
| 1 | `.modinfo` 改成 INFO 段 | **链接 vmlinux 时不再为它分配空间** |
| 2, 3 | kallsyms 用缓存 | 减少重复工作 |
| 4, 5 | 不排序 nm 输出；kallsyms 试链接不带重定位 | 避免无意义排序；减少 DWARF 处理量 |
| 6 | elf-parse：段标志、符号绑定、只读映射 | 为 7 号补丁铺路 |
| ⭐ **7** | **kallsyms 不再用 nm，直接读 ELF 符号表** | **跳过「起进程 + 文本序列化 + 文本解析」整条链；顺带消灭 shell 版 mksysmap** |
| 8, 9 | 对象缓存 + 更高效的依赖时间戳检查 | 减少重复扫描 |
| 10 | 工具链检查拆成独立 Kconfig 文件 | 结构整理 |
| ⭐ **11** | **只在构建顶部探测一次编译器和链接器选项** | **⭐ no-op 构建提速 91% 的元凶** |
| 12 | modpost 用缓存 | 减少重复解析 |
| ⭐ **13, 14** | **模块描述符从 `*.mod.c` 改成 `*.mod.S`（汇编）** | **CPU 时间降到 1/10**；并把模块收尾**分片**，替代「几万次小进程」 |
| 15-17 | objtool：不让 DWARF 重定位污染哈希表、按代码大小定哈希表尺寸、多线程解码大对象 | 消除退化和串行点 |
| 18-20 | rustc 前端多线程；修依赖让 crate 与 C 并行 | 消除 Rust 特有的串行瓶颈 |
| 21 | 默认用 pigz（若系统里有） | 唯一改默认行为的补丁 |

### 验证做到了什么程度

| 项目 | 内容 |
|---|---|
| **架构覆盖** | **allmodconfig 额外构建了 arm64、arm、riscv、powerpc64、s390、loongarch**；**parisc64、m68k 测到主线允许的程度** |
| ⭐ **符号表等价性** | **arm64、arm、s390、loongarch 的 System.map 与之前 shell 版 mksysmap 的结果完全一致** |
| ⭐ **符号可定位** | **9 个架构（x86/arm64/arm/riscv/loongarch/powerpc64/s390/m68k/parisc64）全部在 qemu 启动；System.map 每个文本符号都能在 `/proc/kallsyms` 以重定位后地址找到；模块能加载和卸载** |
| **自测** | **s390、arm、loongarch 通过 kallsyms selftest** |
| **模块版本** | **x86 + `CONFIG_MODVERSIONS` + `CONFIG_EXTENDED_MODVERSIONS` + `CONFIG_MODULE_SRCVERSION_ALL` 通过** |
| **外部模块** | **对 in-tree 和 `O=` 两种输出都验证过** |
| ⭐ **bisect 友好** | **「every commit builds on x86 defconfig」** |
| **失败归因** | **parisc 的静态断言/未定义符号检查、m68k 的 gcc 16 ICE，作者明确写了「都不是这个系列引入的」** |

### AI 参与程度（作者原话）

| 项目 | 内容 |
|---|---|
| **AI 做了什么** | **先确定瓶颈在哪里，然后 figuring out 如何改进；生成了大量代码；编排了构建运行、测试、调试和分析** |
| **人做了什么** | **「广泛地审计并重写了其中很大一部分」，重度编辑 commit message / cover letter / 注释；**手工检查构建与运行两方面的正确性；手工验证性能提升** |
| ⭐ **原话** | **「It generated a lot of code, much of it hideous.」** |
| **标签** | **每个 commit 都带 `Assisted-by` 标签** |

### 同期背景

| 项目 | 内容 |
|---|---|
| **AI 找瓶颈的起点** | **Phoronix 2026-09 初报道，标题《AI Made A Lot Of "Hideous" Code But Found Major Bottlenecks For Faster Linux Compilation》** |
| ⭐ **同周的政策动向** | **2026-10-13 报道：内核社区在讨论取消 `Assisted-by` 强制要求**；**布拉格 Linux Maintainers Summit 上据说达成「弃用」共识**，**但 LKML 上意见不一** |
| **取消的理由** | **「因为 AI/LLM 的使用已经泛滥」** |
| **Phoronix 独立实测** | **EPYC 9575F 2P（24×64GB DDR5-6400，PM1743 3.84TB PCIe Gen5 NVMe，Ubuntu 26.04 LTS，EXT4，未用 TMPFS）**：**defconfig 22s → 15 到 17s**（配合 AMD power determinism）；**allmodconfig 削掉 30 多秒，逼近两分钟** |
| **Phoronix 的评价** | **「喝咖啡的时间窗口正在关闭」**；**增量构建和二分查找回归是最大的实际受益者** |

## 延伸阅读

- [Linux 7.3 破纪录与 AI churn：而真正的问题不是「有多少 commit」，是「这些 commit 是怎么来的」](https://freelamp.com/articles/2026-10-19_linux-7-3-release-record-commits-ai-churn/)
- [Linus Torvalds 亲手删掉 `__get_user()`：而这次又是 AI 参与，只是这次是他自己审的](https://www.phoronix.com/news/Linus-Kills-Get-Put-User-Linux)
- [补丁时代结束了？2025 年的 48,185 个 CVE 和「全打补丁」这个错误答案](https://freelamp.com/articles/2026-10-21_patch-apocalypse-48k-cves-risk-prioritization/)
- [Phoronix 原始报道：Linux 7.4 Begins Landing Patches To Speed Up The Kernel Build Process](https://www.phoronix.com/news/Linux-7.4-Kbuild)
- [Phoronix 实测：Approaching A 10 Second Linux Kernel Build](https://www.phoronix.com/review/near-10-sec-kernel-build)
- [原始 cover letter（v2，含完整 benchmark 表格）](https://lists.infradead.org/pipermail/linux-riscv/2026-September/098647.html)
