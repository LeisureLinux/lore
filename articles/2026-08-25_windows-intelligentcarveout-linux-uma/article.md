# Windows 给统一内存"划地盘"：IntelligentCarveout 原文、解读与 Linux 内核路线分歧

> **原始报道**：[Windows 11 to Get Unified Memory Control Options Ahead of RTX Spark Launch](https://www.techpowerup.com/351881/windows-11-to-get-unified-memory-control-options-ahead-of-rtx-spark-launch) — TechPowerUp, 2026-08-24
> **首发挖掘**：[Windows Latest](https://www.windowslatest.com/2026/08/21/windows-11-will-let-you-decide-how-much-memory-goes-to-graphics-and-ai-on-pcs-with-unified-memory/)（Abhijith M B，2026-08-21，最早在 NVIDIA 内部文档中发现线索，经 phantomofearth 在系统镜像中确认，XenoPanther 放出截图）
> **微软官方背景**：[Introducing a powerful new chapter for Windows PCs, accelerated by NVIDIA RTX Spark](https://blogs.windows.com/windowsexperience/2026/05/31/introducing-a-powerful-new-chapter-for-windows-pcs-accelerated-by-nvidia-rtx-spark/) — Windows Experience Blog, 2026-05-31 / 06-03
> 本文为基于原始报道与微软官方博客的二次解读，非逐字翻译；涉及"微软官方说法"的部分做了明确区分。

一条流传的新闻说：微软在 Windows 11 build 29648.1000 里藏了个叫 **IntelligentCarveout** 的功能，可以给加速器、显卡和 AI 预留统一内存，用户能手动分配，预留出来的内存对其他应用不可见。

这话大体没错，但有一个关键前提必须先说清楚——**微软自己从没正式宣布过 IntelligentCarveout。** 这个功能是从一个隐藏的特性开关（feature flag）里逆向挖出来的。所以你要么拿到"微软关于统一内存的官方表述"（那是另一件事），要么拿到"报道方的英文原文"（这才是 IntelligentCarveout 本身）。下面把两条线都给你摆清楚。

---

## 先澄清：微软的"官方说法"其实说的是另一件事

IntelligentCarveout 本身在微软的 release notes 里**只字未提**。它出现在 Windows 11 的 **"Experimental Future Platforms"** 实验通道（build 29648.1000，2026-08-17 发布），而这个通道的官方定位就是"提前很多年测试平台级改动"，微软明言里面的功能"可能改变，也可能彻底消失"。换句话说：这是一个**未官宣、可能永不发布**的功能。

微软真正公开讲过、和这件事沾边的，是 Computex（2026-05-31）那篇为 NVIDIA RTX Spark 站台的官方博客，里面有一节叫 **"Unified memory optimizations"（统一内存优化）**。注意，它讲的是"**抬高 GPU 可访问的系统内存上限**"，而不是"预留一块对其他应用不可见的内存"。原文是这样说的：

> To realize the potential of up to 128GB of unified memory on RTX Spark, we have focused on improving how Windows supports unified memory systems, starting with a new higher, smarter limit on total system memory accessible by the GPU. This updated limit increases the memory available to the GPU on high-memory systems, unlocking the ability to load larger local AI models or render more complex projects.
>
> — Microsoft, Windows Experience Blog（2026-05-31）

同一节还有一句常被引用的补充：

> In addition to increasing the memory available to the GPU, we are also enhancing how Windows manages page sizes in shared memory regions on unified memory systems. These changes ensure that larger memory pages are available for greater performance on heavier workloads, while giving developers the flexibility to optimize for the needs of their memory workloads between CPU and GPU.

所以，**微软的官方表态 = "我们抬高了 GPU 能用的系统内存上限，并优化了共享内存区域的页大小"**。至于"用户可手动划出一块对别的应用不可见的统一内存"，那是媒体从隐藏 flag 里读出来的，微软一个字都没认。

---

## 一、报道方的英文原文（TechPowerUp 为主线）

TechPowerUp 的报道把这件事的来龙去脉讲得最清楚，下面是它的核心原文（节选，未改动）：

> Microsoft is working on providing processors with unified memory dedicated control parameters in Windows 11, as indicated by the recent Windows 11 build 29648.1000. This build, originally released on August 17, includes a hidden feature called IntelligentCarveout. This feature will allow the system to manage unified memory in SoCs like NVIDIA's upcoming RTX Spark, AMD Ryzen Halo, and other APU-like chips that integrate the CPU and GPU into a single package. These are connected to external LPDDR5X memory, which acts as a unified pool for both the CPU and GPU. With the new feature, we will see specialized controls that allow settings to be configured for independent partitions of this unified memory.
>
> — TechPowerUp（2026-08-24）

它接着点出了要解决的真实痛点——**统一内存池里的"抢地盘"问题**：

> For example, NVIDIA's RTX Spark combines a single GPU with up to 6,140 CUDA cores and a 20-core Arm CPU into a single unified SoC, which is connected directly to a 128 GB pool of LPDDR5X memory. This means that applications often consume as much memory capacity as they deem necessary, without regard for the other accelerator. For instance, applications requiring large CPU capacity often end up using a large portion of the unified memory, leaving the GPU with a smaller share.
>
> — TechPowerUp（2026-08-24）

文章结尾的展望也值得原样保留：

> The Windows 11 OS will become more flexible, providing developers with greater control and giving customers of systems like DGX Spark much more control over memory partitioning.
>
> — TechPowerUp（2026-08-24）

### 从系统镜像里挖出来的"实锤"

除了 TechPowerUp 的综述，首发方 Windows Latest 还列出了镜像中的具体字符串与文件，这些是功能真实存在的最硬证据：

- **特性 ID**：`61121285`（可用 ViVeTool 解锁：`vivetool /enable /id:61121285`）
- **新增文件**：`SettingsHandlers_UnifiedMemory.dll`
- **界面位置**：`设置 > 系统 > 高级 > 统一内存（Unified memory）`
- **界面文案字符串**：
  - `"Reserved memory for accelerators"`（为加速器预留的内存）
  - `"Memory for graphics and AI acceleration"`（用于图形与 AI 加速的内存）
  - `"Let Windows reserve additional unified memory for graphics and AI intensive games and applications. Reserved memory is not available for other applications."`（让 Windows 为图形与 AI 密集型游戏/应用额外预留统一内存。**预留出的内存对其他应用不可用。**）
- **可选档位**：`Custom`（自定义）、`Recommended`（推荐）、`High`（高）、`Maximum`（最大）、`Don't allow`（不允许）

一句话概括报道方口径：**微软在为一类"CPU+GPU 封进同一颗 chip、共享一片 LPDDR5X"的 SoC 做准备，打算让用户在操作系统层面手动把统一内存池切成几块，其中一块专门留给显卡/AI，且对别的应用不可见。**

---

## 二、具体解读：IntelligentCarveout 到底在改什么

### 1. 先搞懂"统一内存（UMA）"为什么突然成了热点

传统独显电脑把内存劈成两半：**系统 RAM 给 CPU，独立显存（VRAM）给 GPU**，两者井水不犯河水。统一内存（Unified Memory Architecture，UMA）则是**一片高带宽内存（典型如 LPDDR5X）被 CPU、GPU、NPU 共享**。

这件事之所以突然重要，是三个趋势叠在一起：

- **本地大模型**：跑一个 70B 甚至 120B 的模型，需要的显存远超绝大多数独显的 24GB VRAM；但一块 128GB 的统一内存池能轻松装下。MacBook 的 M 系列正是靠这个被反复拿来和"只有 24GB 显存的 RTX 5090 笔记本"对比（虽然那是个不公平的对比）。
- **APU 化**：NVIDIA RTX Spark（底层是 **GB10 Grace Blackwell** 超级芯片）、AMD Ryzen AI Max "Halo"（Strix Halo）、以及各类 Arm/ x86 APU，都在把 CPU 和 GPU 焊进同一个封装，外挂一片共享 LPDDR5X。
- **异构计算常态化**：图形、AI、通用计算越来越在同一台机器上同时跑，它们开始**争抢同一池内存**。

### 2. 它真正想解决的：共享池里的"饿死"问题

TechPowerUp 那句"CPU 密集型应用吃掉一大块统一内存，留给 GPU 的就更少"就是核心矛盾。当所有加速器共享一个池子、又没有任何保留机制时，**谁先抢到谁就用得多**，GPU 可能被 CPU 侧的大负载挤到没米下锅。IntelligentCarveout 的本质，就是给 GPU/AI 一个**有保证的、别人碰不到的份额**。

### 3. 它和三种"既有方案"的区别——这点最关键

| 方案 | 是否预留 | 是否对其他应用不可见 | 谁来设 | 何时生效 |
|---|---|---|---|---|
| **现在的 Shared GPU Memory**（任务管理器里那个） | 否，只是**上限（ceiling）** | 否，是动态共享 | 系统/驱动/BIO S | 运行时 |
| **苹果 macOS 的统一内存** | 否 | 否 | 用户**无直接控制** | — |
| **固件级 UMA 帧缓冲（BIOS 里调）** | 是 | 是（e820 标记为 reserved） | BIOS/UEFI | **需重启** |
| **IntelligentCarveout（计划中）** | 是 | 是 | **操作系统/用户**，可动态调整 | 运行时，免重启 |

注意两个微妙但重要的区分：

- 它**不是**今天 Windows 已有的 "Shared GPU Memory"。那个只是"GPU 最多能用多少系统内存"的**天花板**，是动态共享而非硬预留。IntelligentCarveout 是真正的**硬预留**——划出去就再也回不来给普通应用。
- 它也**不是**苹果那种"纯统一内存"。macOS 不给用户任何调节入口；而 Windows 这次是**主动把池子切开并交给用户调**，某种程度上是在"统一"里**重新引入分区**。

### 4. 为什么是现在？硬件与调度器的双重欠账

报道里点名的目标硬件很明确：**RTX Spark（GB10，最高 128GB LPDDR5X、6144 个 Blackwell CUDA 核心、20 个 Arm 核心）、AMD Ryzen AI Max "Halo"、其他 APU**。这些机器计划 2026 年秋季由 Surface、华硕、戴尔、惠普、联想、微星等推出。

微软在官方博客里还顺带承认，它已经为 RTX Spark 改了**工作负载画像调度（Workload Profile Scheduling, WPS）**、共享内存区域的页大小管理、以及 Prism 模拟器。这说明一个事实：**Windows 传统的调度器与内存管理器，本来就不是为"CPU+GPU 共享 coherent 内存的超级芯片"设计的。** IntelligentCarveout 是这套补课里的又一块拼图。

另外有个有意思的对照：AMD 其实**已经**通过 Adrenalin 驱动给 Ryzen AI Max 提供了类似的 **Variable Graphics Memory（可变显存）**，让用户调"系统内存分给核显多少"。也就是说，微软这次更像是把各家驱动里零散的旋钮，**收编成 Windows 系统级的一个统一机制**。

---

## 三、Linux 内核会采用"同样的类 UMA 统一架构"吗？

这是你最关心的问题。我的结论先放在前面：**Linux 大概率不会去克隆 Windows 这个用户态的"统一内存划块滑块"，但它其实早就站在那个架构之上了。** 下面拆开讲。

### 1. 第一步纠偏：Linux 的内存模型"本来就是统一的"

很多人一听"统一内存"，会以为这是个 Windows 缺、Linux 也缺、需要新造的东西。其实反过来——**Linux 从第一天起就是把所有物理 RAM 当作一个统一池来管的**：内核的伙伴分配器（buddy allocator）管理全部系统内存，设备通过 DMA / IOMMU 直接访问这块内存。

对加速器，Linux 早就有一整套机制：

- **DRM/GEM/TTM**：Linux 图形内存框架，内核文档原话就是它"支持 UMA 设备，也支持带独立显存的离散显卡"（*supporting both Unified Memory Architecture (UMA) devices and devices with dedicated video RAM*）。
- **HMM（Heterogeneous Memory Management，异构内存管理）**：让 GPU 等设备内存接入常规内核路径，并支持 **SVM（共享虚拟内存）**——内核文档定义它是"让设备能以与 CPU 一致的方式透明访问程序地址，CPU 上任何合法指针对设备也是合法指针"。这正是"统一内存编程模型"的内核级实现。
- **NUMA**：对"CPU 和 GPU 是两颗 coherent 的芯片"这种拓扑，Linux 直接当成**两个 NUMA 节点**来管。

所以，在"统一内存"这个苹果/Mac 意义上的概念上，Linux **默认就是**，谈不上"要不要采用"。

### 2. "carve-out（切出一块）"这个概念，Linux 也早就有——只是它在固件层

真正和 IntelligentCarveout 行为对等（预留 + 对其他应用不可见）的东西，Linux 上一直存在，叫 **"stolen memory"（被偷走的内存）/ UMA 帧缓冲**：

- 集成显卡开机时，BIOS/UEFI 会**预先**从系统内存里切出一块给 GPU 当帧缓冲/显存，并通过 e820 内存图把它标成 `reserved`。这块内存在内核启动前就被拿走了，**对 OS 完全不可见**，性质上和 IntelligentCarveout 说的"reserved memory is not available for other applications"一模一样。
- 在 AMD APU 上，这块大小本就能在 BIOS 里从 **64MB 调到 16GB**（社区里 Framework 笔记本用户为此专门向厂商请愿加 BIOS 选项）。

区别在于：**固件级 carve-out 是静态的、要重启才能改**；IntelligentCarveout 想做的是**操作系统层、运行时、可动态调整**的。所以 Windows 的新意在于"把固件干的事搬进 OS 并做成滑块"，而不是发明了"预留"本身。

### 3. 真正的"纯统一内存、零分区"——Linux 其实已经做到了

TechPowerUp 评论区里有人（Wirko）说了一段很到位的话：

> To me, unified memory means unified memory. The kind that allows the CPU, GPU and NPU to simultaneously access the same pages of memory, managed by a common MMU, without any partitioning.

这恰恰是 **Apple Silicon 上的 Asahi Linux** 的现状：M 系列本就是真·统一内存，GPU 和 CPU 共享全部 RAM，**根本没有 carve-out**。Linux 上去就当一整块内存用。NVIDIA 的 Grace（GH/GB 超级芯片）在 Linux 下也被当成两个 NUMA 节点，靠 NVLink-C2C（900 GB/s、硬件 cache 一致）实现**无需页迁移**的互相访问——NVIDIA 自己的文档说："From an OS perspective, the Grace CPU and Hopper GPU are just two separate NUMA nodes"，首次访问（first touch）决定物理落点是 LPDDR5X 还是 HBM，且可迁移。

换句话说，**最"纯粹"的统一内存形态，Linux 已经在苹果和 Grace 平台上跑着了**。那恰恰是 IntelligentCarveout 想往回走一步（重新分区）的反方向。

### 4. 那 Linux 会不会也来一个"动态 carve-out 滑块"？

我的判断：**核心内核不会，但驱动/运行时层大概率会有体验上的改进。** 理由逐条：

- **需求已被两路覆盖**：需要静态预留的，BIOS 里的 UMA 设置已经给了；需要灵活共享的，HMM/SVM 的"按需增长共享内存"已经给了。再在 OS 里造一个动态硬预留，等于重复固件机制，还会重新引入分区——而硬件趋势（cache 一致互连、统一内存编程模型）恰恰在**消除**对静态分区的需求。
- **Linux 的设计哲学是给原语，不给魔法滑块**：cgroups（限制某类应用的内存，给 GPU 留余量）、`CMA`（大块连续内存）、`mem=`/`hugetlbfs`、`numactl`（NUMA 内存策略）这些**原语早就齐了**。想要"给 GPU 保证 N GB、对 CPU 应用不可见"，今天用 cgroup + GPU 驱动自身的 GTT/共享内存上限就能近似实现，不需要新造核心特性。
- **目标硬件 Linux 已经能跑**：GB10/RTX Spark 在 Linux 下就是 NUMA 节点；若真想要"保证池"，cgroup/CMA/numactl 即可，无需内核新增 carve-out 子系统。
- **社区共识是"修运行时，不是加静态分区"**：Framework 那篇长帖里，懂行的回复者明确反对"为了 ROCm/PyTorch 在 Linux 上要更大静态 UMA 缓冲"而搞 OS 级动态切分，理由很实在——PC 是多用户多进程的，静态切分要么保守到浪费、要么撑爆触发 OOM；正解是让软件用**动态共享内存**。这正是 ROCm/CUDA 朝 HMM/SVM 演进的方向。

### 5. 真实的痛点与 Linux 可能的演进点

也要公平：TechPowerUp 指出的"CPU 重负载饿死 GPU"是真实存在的，而 Linux **没有一个"一键预留 N GB 对别人不可见"的开关**。如果严格按 Windows 的提法，Linux 确实没有逐字对应的功能。Linux 的应对是"给原语 + 让 GPU 驱动动态扩张共享内存 + cgroups 限 CPU 侧"，而不是"在 OS 里再造一个 carve-out"。

所以最可能的演进是**驱动/运行时层面**，而非核心 MM：

- AMD `amdgpu` / ROCm 针对 Strix Halo 之类的 APU 更好地**自动按需扩张 GTT/共享内存**，而不是逼用户去 BIOS 调大 UMA；
- NVIDIA 的 UVM 运行时对 GB10 这类 coherent 芯片更好地利用 first-touch / 迁移；
- 也许某个 GPU 驱动会经 sysfs 暴露一个"建议预留量"旋钮（类似 Framework 用户用 `efivar` 直接改 BIOS 变量的民间玩法被官方化）。

| 维度 | Windows（IntelligentCarveout） | Linux 现状 / 预测 |
|---|---|---|
| 核心内存模型 | 历史上"分治"，正补课后统一 | **本就统一**（伙伴分配器 + NUMA） |
| 静态 carve-out | 无（过去靠 BIOS） | **已有**（stolen memory / UMA，固件级、需重启） |
| 动态、OS 级、用户态滑块 | 计划中要加 | **核心内核大概率不加**；靠 cgroup/CMA/numactl 原语 |
| 对 GPU 的 coherent 访问 | 靠新调度器 + 抬高上限补课 | HMM/SVM + NUMA + 硬件一致互连，**已具备** |
| 真正演进方向 | 在统一里重新引入可调分区 | 驱动/运行时层体验改进，趋向**消除**静态分区 |

---

## 四、结语：这场戏的真正主角不是 Windows，也不是 Linux

把两边放一起看，有个挺反讽的落点：**微软正在往一个"统一的内存池"里重新切出分区、并做成滑块交给用户调；而 Linux（以及 macOS）本来就住在这个统一池子里。** Windows 这次更像是在补课——补它历史上"系统内存 / 独立显存分治"遗留下来的账，以及传统调度器没为 coherent 超级芯片设计的事实。

真正推动两边一起重新思考内存的，是**硬件**：GB10 Grace Blackwell、Strix Halo 这类"CPU+GPU 共享一片高带宽内存、还带 cache 一致互连"的芯片，第一次把"统一内存"从苹果的营销词变成了 x86/Arm 阵营的量产现实。

所以，回答你的问题——**Linux 内核不需要"采用和 Windows 同样的类 UMA 统一架构"，因为它本来就站在那个架构之上；它要补的，是应用和运行时对动态共享内存的利用，而不是在操作系统里再雕一个 carve-out。** 等哪天 ROCm、PyTorch、CUDA 全都天然用 HMM/SVM 干活，连固件级的静态 UMA 都会显得多余。到那时，微软那个滑块，说不定也会悄悄退场。

---

## 参考文献

- TechPowerUp — [Windows 11 to Get Unified Memory Control Options Ahead of RTX Spark Launch](https://www.techpowerup.com/351881/windows-11-to-get-unified-memory-control-options-ahead-of-rtx-spark-launch)（2026-08-24，报道方英文原文）
- Windows Latest — [Windows 11 will let you decide how much memory goes to graphics and AI on PCs with unified memory](https://www.windowslatest.com/2026/08/21/windows-11-will-let-you-decide-how-much-memory-goes-to-graphics-and-ai-on-pcs-with-unified-memory/)（Abhijith M B，2026-08-21，首发挖掘与字符串）
- Microsoft Windows Experience Blog — [Introducing a powerful new chapter for Windows PCs, accelerated by NVIDIA RTX Spark](https://blogs.windows.com/windowsexperience/2026/05/31/introducing-a-powerful-new-chapter-for-windows-pcs-accelerated-by-nvidia-rtx-spark/)（2026-05-31，唯一相关官方表述 "Unified memory optimizations"）
- VideoCardz — [Windows 11 prepares unified memory controls ahead of NVIDIA RTX Spark PCs](https://videocardz.com/newz/windows-11-prepares-unified-memory-controls-ahead-of-nvidia-rtx-spark-pcs)（2026-08-24，对比 AMD Variable Graphics Memory）
- Pureinfotech — [Windows 11 is getting a new setting to control Unified Memory for AI and graphics](https://pureinfotech.com/windows-11-unified-memory-setting-ai-graphics/)（2026-08-22，ViVeTool 命令与档位细节）
- Linux 内核文档 — [Heterogeneous Memory Management (HMM)](https://www.kernel.org/doc/html/latest/mm/hmm.html)（SVM / 设备内存接入内核路径）
- Linux 内核文档 — [DRM Memory Management (TTM/GEM)](https://docs.kernel.org/gpu/drm-mm.html)（UMA 与独立显存统一管理）
- NVIDIA Developer Blog — [NVIDIA Grace Hopper Superchip Architecture In-Depth](https://developer.nvidia.com/blog/nvidia-grace-hopper-superchip-architecture-in-depth)（NVLink-C2C、NUMA 视角、无需页迁移的 coherent 访问）
- Framework Community — [BIOS Feature Request: Add ability to specify UMA size on AMD APUs](https://community.frame.work/t/bios-feature-request-add-ability-to-specify-uma-size-on-amd-apus/41930)（Linux 上 ROCm/PyTorch 依赖 UMA 缓冲、社区对静态/动态分配的争论）
