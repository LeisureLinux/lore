---
title: "NPU 终于能用 PyTorch 跑了：Mesa 接下这件事，靠的是一条被 AI 加速行业忽略的捷径"
date: 2026-10-14
slug: mesa-torx-yolox-pytorch-npu
tags: [Mesa, NPU, Torx, ExecuTorch, PyTorch, Teflon, Gallium, NIR, DRM, accel, Ethos-U, i.MX93, Etnaviv, Rocket, 边缘AI, 开源驱动, 逆向工程, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "Phoronix / Mesa 官方文档 / Tomeu Vizoso 博客"
original_author: "Michael Larabel（Phoronix）；Tomeu Vizoso；Rob Herring（Arm）"
original_date: 2026-10-13
original_url: "https://www.phoronix.com/news/Mesa-Torx-YOLOX-PyTorch"
description: "Mesa 的 Torx 后端合并了 YOLOX 支持，意味着可以用 PyTorch / ExecuTorch 把神经网络跑到 NPU 上，实测在 NXP i.MX93 的 Arm Ethos-U65 上以 17 毫秒一帧运行 YOLOX-Nano。这件事的技术内核是：图形驱动栈和 AI 加速器驱动的形状是一样的（编译图、配置硬件、提交任务、管理缓冲），所以 Mesa 的 Gallium 抽象、NIR 中间表示和 DRM/accel 子系统可以被复用。而 Torx（ExecuTorch 后端）与 Teflon（TensorFlow Lite 委托）并列，共用同一个 Gallium ML API。本文拆解这条技术路线的来龙去脉，以及它为什么比各家自己的 NPU SDK 更有希望。"
published: true
---

> 主要来源：[Phoronix：Mesa Expands NPU Capabilities With Support For YOLOX With PyTorch](https://www.phoronix.com/news/Mesa-Torx-YOLOX-PyTorch)（2026-10-13，Michael Larabel）
> 一手材料：[Mesa 官方文档：ExecuTorch backend（Torx）](https://docs.mesa3d.org/torx.html)、[Tomeu Vizoso：Ethos-U NPU update 2: Executorch support](https://blog.tomeuvizoso.net/2026/10/ethos-u-npu-update-2-executorch-support.html)（2026-10-01）、[Ethos-U NPU update 1：走向生产可用的主线驱动](https://blog.tomeuvizoso.net/2026/07/ethos-u-npu-update-1-journey-to.html)（2026-07-14）、[Etnaviv NPU update 22: YOLOX support](https://blog.tomeuvizoso.net/2026/08/etnaviv-npu-update-22-yolox-support.html)（2026-08-22）
> 本文为**译文 + 解读**。第二、三节对「图形栈为什么适合接管 NPU」与「AOT 才是关键」的分析，第四节的判断，是笔者补充的部分。

## 一句话结论

**Mesa 的 Torx 代码合并了 YOLOX 支持**。**Torx 是 Mesa 里的 ExecuTorch 后端**，**作用是给机器学习模型提供一条用 NPU 来编译与执行的路径**。**合并之后，用户可以用 PyTorch 配合 Mesa 里的 NPU 驱动来运行 YOLOX**，**目前已经在 NXP i.MX93 SoC 的 Arm Ethos-U NPU 上测试通过**，**代码进入了 Mesa 26.3**。

**实际效果是**：**YOLOX-Nano，416×416 输入，量化成 8 位整数，在一块 i.MX93 开发板上跑，单帧推理 17 毫秒**。

**而这件新闻里我认为最值得记的，是它暴露的一条捷径**：**图形驱动栈和 AI 加速器驱动的形状是完全一样的**，**所以 Mesa 那套为 GPU 攒了十几年的抽象（Gallium、NIR、DRM/accel）可以直接拿来跑神经网络**。**而对做边缘 AI 的人来说，这条路径的意义在于**：**它让「PyTorch 模型跑在自己的 NPU 上」这件事，不再需要等厂商写一个专用 SDK。**

## 一、先说清 Torx 是什么，以及它和 Teflon 的关系

**Mesa 的官方文档对 Torx 的定义很简短**：

> **Torx 是 Mesa 的 ExecuTorch 后端：它可以利用 NPU 来加速机器学习推理，实现为 ExecuTorch 这个端侧 AI 框架的一个自定义后端。**

**而 Tomeu Vizoso（这条技术路线的核心开发者）在自己的博客里把位置关系说清楚了**：

> **Torx 坐在 Teflon 旁边，也就是已有的 TensorFlow Lite 委托旁边，两者使用同一个 Gallium ML API。** **今天 Torx 与 ethosu 驱动配合工作。Torx 实现了 ExecuTorch 提供的后端 API，用于把模型图的一部分运行在 NPU 或 GPU 这类专用硬件上。然后它使用 Gallium ML API 在可用硬件上编译并执行这些部分。**

**也就是说，这块的架构是三层**：

| 层次 | 组件 | 职责 |
|---|---|---|
| **框架对接层** | **Teflon**（TensorFlow Lite 委托）／**Torx**（ExecuTorch 后端） | **把框架的图切出一部分交给硬件** |
| **共用中间层** | **Gallium ML API** | **编译与执行，屏蔽具体硬件** |
| **硬件驱动层** | **ethosu**（Arm Ethos-U）／**etnaviv**（Vivante）／**rocket**（Rockchip）／**thames**（TI C7x DSP） | **把模型翻译成硬件命令** |

**这个结构里我认为最值得注意的是「共用中间层」这一格。** 因为**它意味着每加一个 NPU，只需要写硬件驱动部分，而不需要重新对接框架**。**而反过来也一样**：**每加一个框架（TFLite → PyTorch），上层的硬件驱动不用改。**

**这是 Mesa 能同时推进多条 NPU 路线的结构性原因。** **而这些驱动也确实来自不同来源**：**ethosu 是 Arm Ethos 系列**、**etnaviv 是 Vivante/VIP 系列**（**用在 NXP i.MX 8M Plus 和 Amlogic A311D 上**）、**rocket 是逆向工程出来的 Rockchip NPU**（**主线内核 6.18 起支持**）、**thames 面向德州仪器 C7x DSP**（**用在 BeagleY-AI 这类板子上**）。

**而 kernel 侧是另一条线**。**Tomeu 在 7 月的文章里说明了主线驱动的来历**：

> **Rob Herring，因为在设备树基础设施上的工作而为 Linux 社区熟知，他在一年多前于 DRM/Accel 子系统里开始了一个全新的内核驱动，这个驱动会直接从主 CPU 驱动 Ethos-U，绕过 Cortex-M，从而绕过对固件的需要。该驱动使用 DRM 既有的实践来定义 UAPI，并重用 DRM 子系统的代码，例如 GEM 和 gpu-drm-scheduler。这个驱动被合并进了 Linux 内核的 6.19 版本，从一开始就支持 NXP 的 i.MX93 SoC。**

**这句话里有两个设计决策值得单独指出**：**第一，绕过 Cortex-M**；**第二，重用 DRM 的 GEM 与调度器**。**第二个正是我上一节说的那条捷径的具体形态**：**NPU 驱动的内核侧，本质上就是「管理缓冲 + 调度任务」，而 DRM 子系统已经把这套东西做好十年了。**

## 二、图形栈为什么适合接管 NPU

**我认为这条技术路线值得写，是因为它的成立原因很「物理」，而不是「顺手」**。

**把一个加速器接进操作系统并提供给上层框架，需要四件事**：

| 需要做的事 | GPU 领域的成熟答案 | AI 加速器需要的 | 是否同构 |
|---|---|---|---|
| **用户态驱动** | **Gallium 驱动** | **把模型图翻译成硬件命令** | ✅ **同构**（都是编译一张图到硬件指令） |
| **中间表示与优化** | **NIR**（Mesa 的 IR） | **算子融合、布局转换、量化降低** | ✅ **同构** |
| **内存与缓冲管理** | **GEM / dumb buffers** | **输入输出张量、权重、中间特征图** | ✅ **同构** |
| **任务提交与调度** | **DRM scheduler** | **把推理任务投给 NPU 队列** | ✅ **同构** |

**四件事里有四件同构，所以复用不是巧合，而是「抽象层次刚好对上了」。**

**而 NIR 这条线尤其能说明问题**。**Phoronix 在报道 XDC2025 上 Tomeu 的演讲时，记下了他 2026 年的计划**：**「PyTorch/ExecuTorch 支持，以及用 NIR 做优化 pass 和把模型降低到硬件。」** **NIR 原本是 Mesa 用来统一图形驱动的中间表示**，**现在它在 AI/ML 上「获得了越来越多的曝光」**。

**我认为这件事有一个更大的含义**：**一个编译器中间表示的价值，取决于有多少种硬件需要被降低到。** **Mesa 面对的是十几家 GPU 厂商、几十代架构**，**这套 IR 就是被这种多样性逼出来的**。**而 AI 加速器领域的现状恰好是「硬件极度碎片化、每家一套 SDK」**，**这正是 NIR 能派上用场的地方。**

**而这条线不是突然出现的，它有一个可以追溯的时间轴**：

| 时间 | 事件 |
|---|---|
| **2024-01** | **Teflon 合并进 Mesa 24.1**：作为 Gallium3D 前端，供 TensorFlow **加载并委托网络中算子的执行**；最初是为 Etnaviv 驱动做的，目的是在 Vivante NPU 上跑推理 |
| **2025-10** | **Arm Ethos NPU 的 Gallium3D 驱动合并**（进入 Mesa 25.3），**复用 Teflon 框架**；同期 Arm 的主线 `accel` 驱动仍在审查 |
| **2026-01** | **Thames**：面向德州仪器 C7x DSP 的 DRM accel 驱动 + 配套 Gallium3D 驱动（**走 Teflon**） |
| **2026-03** | **Ethos U85 NPU 支持进入 Mesa 26.1**（U85 宣传上比 U55/U65 能效高 20%，可扩展 128 到 2048 个 MAC 单元） |
| **2026-07** | **主线 Ethos-U 驱动合并进 Linux 6.19**（**Rob Herring**，绕过 Cortex-M） |
| **2026-08** | **YOLOX 在 Etnaviv 驱动上跑通**（**Vivante VIP 系列**，含 i.MX 8M Plus、A311D） |
| **2026-10** | **Torx 合并 YOLOX 支持**（**即本条新闻，进入 Mesa 26.3**） |

**从这个时间轴能看出一个节奏**：**这条路线走了将近三年，从「用 TFLite 跑分类模型」推进到「用 PyTorch 跑目标检测」，而每一步都是「补齐一部分算子 + 打通一条新硬件或新框架」。** **它没有一次性的突破，而是一条持续叠加的线。**

## 三、真正的技术看点是 AOT：编译在别处，执行在这里

**Tomeu 的博客里有一段我认为是整条新闻里最重要的技术信息**：

> **与 TensorFlow Lite 不同，ExecuTorch 把模型的编译与执行分成两个独立的步骤。因此模型可以在与目标设备不同的机器上编译，在那些机器上应用比边缘级硬件能跑得起的更昂贵的优化是可行的。**

**这句话值得展开，因为它说明的不是「性能提升」，而是「一条被浪费掉的可能」。**

**把两种模式对比一下**：

| | **运行时编译**（TFLite 委托的典型形态） | **提前编译（AOT）**（ExecuTorch 的做法） |
|---|---|---|
| **编译发生在哪** | **目标设备上，或至少由目标设备的工具链完成** | **可以在一台完全不同的、算力更强的机器上** |
| **优化预算** | **受限于边缘设备的算力与内存** | **可以跑昂贵的优化**（更激进的算子融合、布局、量化策略） |
| **目标硬件是否需要它** | **不需要**（编译好的产物直接投给硬件） | **不需要** |
| **对开发流程的影响** | 模型 → 设备 | **模型 → 构建机 → 产物 → 设备** |

**这意味着**：**边缘设备的算力限制，本来不应该限制「模型能被优化到什么程度」**：**因为优化这件事可以在别处做完。** **而把编译从执行里拆出来，恰好打开了这个空间。**

**这也解释了 Torx 为什么要实现 ExecuTorch 那套「后端 API」**：**它的职责是「在可用硬件上编译并执行那些被切出来的部分」**，**而编译被视为一个独立的、可以提前完成的步骤。**

**而这个设计有一个实际的开发体验后果**，**Mesa 文档里的两个细节能说明**：

**第一，测试是怎么做的**：

> **Torx 测试套件把单个神经网络算子与 CPU 参考实现做对比。用于测试的模型从另一个仓库获取。测试时，test_torx 直接跑在 NPU 板子上，在 NPU 上执行每个 .pte，并把结果与 CPU 参考做比较。**

**第二，当整个模型精度不对时，怎么定位**：

> **`split_torx_tests.py --ranges` 把一个模型切成累积的前缀子图 `[0..0]` 到 `[0..N-1]`，而不是切成本个算子。用同一条流水线编译并运行这些前缀，可以让一个「整模型精度失败」被二分定位到引入问题的那个算子，同时为每一个前缀复现真实的分区决策。**

**我认为第二点是这篇文档里最精巧的一处工程**。**因为它同时解决了两个问题**：**「定位到是哪个算子出错」（二分）** 以及 **「保证复现真实的分区决策」**：**后者是关键，因为如果把模型拆成单个算子分别测，算子之间的分区与融合就不会发生，测试就不再反映真实执行路径。** **用「累积前缀」而不是「单个算子」，正是为了保留这个上下文。**

**而这恰好对应了我经常提到的那条判断**：**真实的负载会暴露你在单元测试里根本想不到的问题。** **这里是它的一个正向应用**：**测试设计必须保留真实执行路径的结构，否则测出来的通过率是假的。**

## 四、我的判断

**第一，这条新闻表面上是「又支持了一个模型」，实质上是「Mesa 从 GPU 库变成加速器运行时」，而后者才是值得关注的趋势。**

**Phoronix 那条报道的措辞是**：**「虽然 Mesa 主要用于 GPU 驱动，但开源开发者 Tomeu Vizoso 持续在推进 Mesa 驱动栈里 NPU 的能力。」** **这句话的语法很有意思**：**「虽然 Mesa 主要用于 GPU 驱动」是一个让步状语**，**说明连报道者都意识到这里有个范畴变化。**

**而我认为这个变化是合理的、甚至是必然的**。**因为决定性因素不是「Mesa 想不想做 AI」，而是「NPU 驱动和 GPU 驱动的工程形状是同构的」**（见第二节那张表）。**当一个抽象层正好覆盖了另一类硬件的需求时，接管它只是时间问题。**

**而这对开源 AI 加速的意义很大**：**过去每家 NPU 厂商的做法是提供一个闭源或半闭源的专用 SDK**，**于是「支持某个 NPU」就等于「用 PyTorch 跑不了，除非厂商写了适配」**。**而 Mesa 这条路线把问题变成了「给一个已有中间层写一个后端」**：**这是一个小得多的工程量，而且结果对所有框架同时生效。**

**第二，AOT 那段是我认为最该被单独记住的技术点，因为它指出了一个被普遍浪费的空间。**

**边缘 AI 的部署流程里，长期存在一个不对称**：**推理必须在设备上跑（因为算力/延迟/功耗/数据的约束），但优化不必须在设备上做。** **而很多运行时把这两件事绑在一起了**，**结果是「设备越弱 → 编译时的优化预算越少 → 模型效率越差 → 更容易超过设备能力」** 这样一个自我强化的循环。

**把编译与执行拆开，就打开了这个循环**。**而我觉得这里有一个可以推广的判断**：**当一个系统的性能瓶颈来自「执行环境太弱」时，先问一句「这件事必须在那个环境里做吗？」** **很多时候，把准备工作搬到别处，比在现场挤性能更有效。**

**第三，那些限制条件需要被诚实列出，因为它们划出了这条路线当前的真实边界。**

**Phoronix 和官方材料都给了明确的说明**：

- **目前 Torx 只在 Arm EthosU 驱动上工作**，测试用的是 **NXP i.MX93**(**该 SoC 里的 Ethos U-65 标称 0.5 TOPS，640 KB SRAM**)；
- **Etnaviv（Vivante NPU）驱动「应该已经支持所有算子」，但仍缺少配合 Torx 使用所需的基础设施工作**；
- **性能目前很低**：**Tomeu 在 2025 年 10 月介绍 ethosu 驱动时自己说的是「对于目前已实现的算子，功能相当完整，但由于缺乏任何优化，性能目前非常低」**；
- **一块模型不是整个跑在 NPU 上**：**YOLOX 的卷积层全部跑在 U65 上，而最后的解码步骤需要浮点运算，所以跑在 CPU 上**；
- **其他 NPU 驱动要等到支持 Gallium ML API 的「提前编译扩展」之后，才能从 ExecuTorch 使用。**

**最后一条尤其重要**，**因为它说明这条路线有一个前进的条件**：**它不是自动对所有 hardware 生效的，每个驱动都需要实现那个 AOT 扩展。** **换句话说，「PyTorch 支持」目前是一个驱动一个驱动地加出来的，而这正是第三层（硬件驱动层）需要持续投入的原因。**

**第四，数据本身值得记住，因为它是这条路线可行性的最直接证据。**

**17 毫秒一帧这个数字，在语境里才看得清**：**一块面向嵌入式、标称 0.5 TOPS、只有 640 KB SRAM 的微 NPU，跑一个 416×416 的目标检测模型，每秒约 59 帧。** **而这个模型是 8 位量化过的**。

**而 Tomeu 对这类「微 NPU」的观察我认为也值得记下来**：

> **Arm 把它们叫做微 NPU，而它们确实包含较少的计算单元，但在我的测试中，它们可以匹配计算单元数量多达六倍的 NPU 的性能。在我看来，这是因为架构非常干净，不同子模块之间配合得很好，以及软件栈优秀，允许相当不错的占用率。**

**「计算单元少六倍但性能相当，原因是架构干净和占用率」这个观察，其实是在说一件事**：**NPU 的实际吞吐更取决于「能不能喂饱它」，而不是「它有多少计算单元」。** **而这也解释了为什么软件栈（编译器、调度、驱动）在这个领域如此关键**：**因为大部分性能是从「让硬件不闲下来」里挤出来的，而不是从峰值算力里。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 事件 | **Mesa 的 Torx 代码合并 YOLOX 支持**（2026-10-13 报道，作者 Michael Larabel） |
| **Torx 是什么** | **Mesa 的 ExecuTorch 后端**：**利用 NPU 加速机器学习推理，实现为 ExecuTorch 这个端侧 AI 框架的自定义后端** |
| **实际效果** | **可以用 PyTorch 配合 Mesa 里的 NPU 驱动来运行 YOLOX** |
| **已测试的硬件** | **Arm EthosU NPU，使用 NXP i.MX93 SoC** |
| **性能实测** | **YOLOX-Nano，416×416 输入，8 位整数量化，i.MX93 + Ethos-U65 上单帧推理 17 毫秒**（约 59 帧/秒） |
| **计算分布** | **YOLOX 的卷积层全部跑在 U65 上**；**最后的解码步骤需要浮点运算，所以跑在 CPU 上** |
| **进入版本** | **Mesa 26.3** |
| **⚠️ 其他驱动状态** | **Etnaviv（Vivante NPU）驱动「应该已支持所有算子」，但仍缺少配合 Torx 的基础设施工作**；**其他 NPU 驱动需等支持 Gallium ML API 的「提前编译扩展」后才能从 ExecuTorch 使用** |
| **兄弟组件** | **Torx 坐在 Teflon（已有的 TensorFlow Lite 委托）旁边，两者使用同一个 Gallium ML API** |
| **架构分层** | **框架对接层**（Teflon / Torx）→ **共用中间层 Gallium ML API** → **硬件驱动层**（ethosu / etnaviv / rocket / thames） |
| **关键技术差异** | **与 TensorFlow Lite 不同，ExecuTorch 把编译与执行分成独立的两步**，**因此模型可以在与目标不同的机器上编译，从而应用边缘硬件跑不起的昂贵优化** |
| **协作方** | **Tomeu Vizoso**（Mesa 侧）；**Rob Herring（Arm）**（内核侧）；**YOLOX 的 Etnaviv 工作与 Ideas On Board 合作** |
| **内核侧** | **Rob Herring 在 DRM/Accel 子系统写了新驱动，直接从主 CPU 驱动 Ethos-U，绕过 Cortex-M 从而绕过固件**；**使用 DRM 实践定义 UAPI，重用 GEM 与 gpu-drm-scheduler**；**合并进 Linux 6.19**，**从一开始支持 i.MX93** |
| **⚠️ 绕开 Cortex-M 的原因** | **与 SoC 厂商交流后得知：Cortex-M 的中介使得 ML 模型无法在 CPU 与 NPU 上高效协同执行，而且客户部署新模型很麻烦** |
| **另一个推动因素** | **Arm 的 Ethos-U 软件栈虽然开源，但没有预集成进厂商使用的 Linux 发行版，也缺少像成熟的多厂商上游项目那样的标准回贡路径** |
| **测试方法** | **Torx 测试套件把单个算子与 CPU 参考实现对比**；**test_torx 直接跑在 NPU 板子上，执行每个 .pte 并对比 CPU 参考**；**测试模型来自独立的 npu-model-zoo 仓库** |
| **调试工具** | **`split_torx_tests.py --ranges` 把模型切成累积前缀子图 `[0..0]`～`[0..N-1]`**，**用于二分定位引入精度问题的算子，同时复现每个前缀的真实分区决策** |
| **构建方式** | **`meson setup build -Dgallium-drivers=ethosu -Dvulkan-drivers= -Dtorx=true`**；**需要 ExecuTorch 的 nightly 构建**（因为只有 nightly wheel 带 Torx 需要的 `executorch.pc`） |
| **NIR 的角色** | **NIR 原本是统一图形驱动的中间表示，现在在 AI/ML 上获得越来越多的曝光**；**Tomeu 在 XDC2025 提到 2026 年计划包括用 NIR 做优化 pass 与把模型降低到硬件** |
| **微 NPU 的性能观察** | **「它们确实包含较少的计算单元，但在我的测试中，它们可以匹配计算单元多达六倍的 NPU 的性能」**，**原因是架构干净 + 软件栈优秀带来的良好占用率** |
| **⚠️ 性能现状** | **ethosu 驱动在 2025-10 的官方描述是「功能相当完整，但性能目前非常低，因为缺乏任何优化」** |
| **相关历史节点** | **Teflon 合并进 Mesa 24.1（2024-01，TFLite 委托）**；**Arm Ethos Gallium3D 驱动合并（2025-10，Mesa 25.3）**；**Thames 面向 TI C7x DSP（2026-01）**；**Ethos U85 进入 Mesa 26.1（2026-03）**；**主线 Ethos-U 驱动进入 Linux 6.19（2026-07）**；**YOLOX 在 Etnaviv 上跑通（2026-08）** |
| **硬件背景** | **i.MX93 里的 Ethos U-65 标称 0.5 TOP/s、640 KB SRAM**；**U85 宣传上比 U55/U65 能效高 20%，可扩展 128–2048 个 MAC 单元** |
| **已在 Mesa 里的 NPU 驱动** | **ethosu（Arm Ethos-U）**、**etnaviv（Vivante，含 i.MX 8M Plus、A311D）**、**rocket（Rockchip，逆向工程，主线内核 6.18 起）**、**thames（TI C7x DSP，可用在 BeagleY-AI 这类板子上）** |

## 延伸阅读

- [Phoronix：Mesa Expands NPU Capabilities With Support For YOLOX With PyTorch](https://www.phoronix.com/news/Mesa-Torx-YOLOX-PyTorch)
- [Mesa 官方文档：ExecuTorch backend（Torx）](https://docs.mesa3d.org/torx.html)
- [Tomeu Vizoso：Ethos-U NPU update 2: Executorch support](https://blog.tomeuvizoso.net/2026/10/ethos-u-npu-update-2-executorch-support.html)
- [Tomeu Vizoso：Etnaviv NPU update 22: YOLOX support](https://blog.tomeuvizoso.net/2026/08/etnaviv-npu-update-22-yolox-support.html)
- [本站：zram 重构读写流：读不再被写挡住](/articles/2026-10-06_zram-streams-rework/)
- [本站：Asterinas 0.19：用 Rust 重构内核的另一种思路，是「不减少地址空间，只减少 unsafe」](/articles/2026-10-13_asterinas-0-19-framekernel/)
- [本站：Linux 桌面不是给专家用的：这句话被引用了二十年，现在它该被拆开了](/articles/2026-10-09_linux-desktop-not-expecting-experts/)
