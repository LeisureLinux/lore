---
title: "gputaskman：一个 GPU 任务管理器，看清那 15GB 显存被谁吃了"
date: 2026-11-08
slug: gputaskman-gpu-vram-task-manager
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Scott Hanselman 的开源项目 shanselman/gputaskman 官方 README（含各平台可测指标矩阵、容器 PID 配对算法、WSL 跨命名空间方案与 AMD 驱动路径的实测记录）＋ Tom's Hardware 报道（Mark Tyson，2026-11-08，含作者实测 RTX 4060 的截图观察）＋ Windows Central 报道（2026-11-06）"
original_date: 2026-11-03
original_url: "https://github.com/shanselman/gputaskman"
description: "本文解读微软开发者 Scott Hanselman 于 2026 年 11 月 3 日开源的 gputaskman —— 一个跨 Windows / Linux / WSL / macOS 的终端式 GPU 任务管理器。它的起点是一个很朴素的问题：任务管理器说「用了 15 GB」，那**是谁**用掉的？模型权重？KV cache？浏览器？桌面合成器？以及为什么这么多 GPU 内存跑在系统 RAM 里？**但这个工具真正值得写的不是它的功能，而是它对「不确定」的处理方式。** 它的 README 里反复出现一个词：**estimate**（估算）——「设备与进程计数器是**测量值**，而分类与 GGUF 推导出的分解是**估算**」，并且明确列出它**做不到**的事：「一个 PyTorch/CUDA 的 DLL 本身无法标识模型，也无法证明在训练；一个被映射的文件不能证明该模型驻留在 GPU 上或正在被使用。」**这是工具作者对可信度边界的罕见坦诚。** 更值得学的还有三处工程细节：①**容器里的 PID 配对** —— NVML 报的是**宿主机** PID，在容器里毫无意义，而容器也看不到自己进程的宿主机 PID；gputaskman 的办法是把 NVML 未解析的 PID 与「已映射 libcuda.so」的容器进程配对（因为 nvidia-smi 这类纯 NVML 工具会打开同样的设备文件但从不加载 libcuda），**两个 PID 命名空间都按创建顺序编号，所以按顺序配对**，计数吻合时标 *、NVML 列出更多计算进程时标 ?；②**「未知」用 null 而不是 0** —— 「JSON 用 null 表示不可用的计数器，而不是测得的零」；③**Linux 上 Spill 与 Paged 留空而非显示 0** —— 「Linux 没有 WDDM 共享内存或 commit 计数器的等价物，所以 Spill 和 Paged 留空而不是显示零」。本文还记录了作者在 Tom's Hardware 那篇报道里的实测观察：他启动时**没有任何任务在用独显**，于是跑了个 Unigine Valley 把 RTX 4060 叫醒 —— 这个细节本身就说明了工具的实用场景。"
published: true
---

> 原文：Scott Hanselman 的开源项目 shanselman/gputaskman（2026-11-03 发布）
> 原文链接：<https://github.com/shanselman/gputaskman>
>
> 本文依据官方 README 全文（含各平台可测指标矩阵、容器 PID 配对算法、WSL 跨命名空间方案与 AMD 路径的实测记录），以及 Tom's Hardware 与 Windows Central 的报道。

## 一、它要回答的问题很朴素

Hanselman 在社交媒体上写下了起因：

> **「我的 GPU 里发生着很多事。我要做一个 GPU Taskman，来搞清楚我的 GPU 内存都去哪了。」**

工具自己的 README 把这个问题说得更精确：

> **任务管理器说「用了 15 GB」。这个工具想回答：被谁用掉了？模型权重？KV cache？你的浏览器？桌面合成器？以及为什么这么多 GPU 内存跑在系统 RAM 里？**

一句话概括定位：**「一个 GPU 版的 htop，不只是看它有多满，而是看里面有什么。」**

它做的是**终端 UI**（TUI），把「每进程的 GPU 内存和引擎活动」与「已加载的运行时、模型文件、LLM 缓冲区分解」连起来看。

## 二、跨平台，但「能测什么」取决于平台

这是这个工具设计上最诚实的一部分 —— **它不假装在所有平台上都能测同样的东西，而是在界面上直接告诉你现在处于哪种模式。**

| 指标 | 原生 Linux | WSL（interop 开） | WSL（interop 关 / `--no-host`） |
|---|---|---|---|
| 设备总量、负载、温度、功耗、频率 | NVML | NVML | NVML |
| **每进程 VRAM** | NVML 测量（容器内按属主匹配 `*` 或 `?`） | 从 Windows 主机匹配，标 `*` 或 `?` | **不适用** |
| 每进程 GPU 负载 | NVML（SM / 编码器 / 解码器） | NVML | **Linux 进程不适用** |
| Spill / Paged | **不可用（留空）** | 仅 Windows 行 | 不可用 |
| WSL VM 总量 + Windows 应用 | — | Windows 主机计数器 | — |
| 运行时、模型文件、LLM 分解 | `/proc/<pid>/maps` + 命令行 | 同左 | 同左 |

**几个格子里的「不适用」和「留空」，是这个项目最有信息量的部分。** 下面会具体说。

而 Windows / macOS 上也不是简单照搬：

- **Windows** 走 WDDM，能拿到每进程 VRAM、spill、paged 与引擎负载；
- **macOS** 只支持 Apple Silicon；
- **原生 Linux 的 AMD** 走 `amdgpu` 驱动，**不需要 ROCm、AMD SMI 或任何额外包**——「内核已经暴露了需要的东西」。

## 三、我认为这个工具最值得学的地方：它对「不确定」的诚实

**这是我读完 README 后印象最深的部分，而且它恰恰是这个工具与其它 GPU 监控工具拉开差距的地方。**

README 开头就把这件事说清楚了：

> **早期、实验性的软件。设备与进程计数器是*测量值*；分类与 GGUF 推导出的分解是*估算*。**
>
> **这个工具不会倾倒 VRAM，也不会枚举游戏的纹理。**

### 它明确说自己做不到什么

> **一个 PyTorch/CUDA 的 DLL 本身无法标识模型，也无法证明在训练；一个被映射的文件不能证明该模型驻留在 GPU 上或正在被使用。**

**这两句是整份 README 里最有分量的技术表述。** 它们划出了一条很多工具会含糊过去的线：

**「检测到 llama-server 进程」和「检测到 Qwen3-0.6B 模型正在占用 3.95 GB」是两件强度完全不同的事。**

前者是观察，后者是推断。而 GPU 监控工具的读者 —— 尤其是那些据此做采购或调度决策的人 —— **最需要的恰恰是知道哪一条是哪一种。**

### 「未知」用 null，而不是 0

这条在 JSON 输出格式里：

> **JSON 用 `null` 表示不可用的计数器，而不是测得的零。**

**这是数据可视化的一个基本功，但很多工具做不对。**

区别在于：一个填 0 的计数器，在图表上会画成一条「这条路径没用任何 GPU 内存」的线；而 `null` 会被画成「**这里没有数据**」。

**前者会误导，后者只是缺失。**

而 Linux 上的 Spill 与 Paged 甚至连 `null` 都不给，而是直接留空：

> **Linux 没有 WDDM 共享内存或 commit 计数器的等价物，所以 Spill 和 Paged 留空而不是显示零。**

### AMD 路径上的 n/a 也标得很清楚

> 一个 **ROCm/HIP 进程**（标记为 `HIP`）的 VRAM 在 fdinfo 里和其它进程一样。**但它的 GPU% 不是**：HIP 通过 `/dev/kfd` 上的用户态队列提交计算，而**内核不按进程计时**，所以一个持有 `/dev/kfd` 的进程，引擎会显示为 `n/a`（JSON 里是 `null`），**而不是一个看起来像实测值的 0**。
>
> 设备的 AMD gfx 负载**是**包含这部分工作的。

**「而不是一个看起来像实测值的 0」** —— 这句话是整个 README 的写作风格缩影。

作者还给出了为什么这么设计的理由：**如果 HIP 进程显示 0，用户会以为它没在用 GPU，而实际上它可能正在跑 103 tok/s 的推理。** 一个假的 0 比一个诚实的 n/a 危险得多。

## 四、容器里的 PID 配对：一个很巧的解法

这是整个项目里技术含量最高的一段。

### 问题

> **容器**（Docker、Kubernetes、租来的 GPU 盒子）需要额外一步：**NVML 报告的是宿主机 PID**，在容器的 `/proc` 里毫无意义，而容器也看不到自己进程的宿主机 PID。

**这是个真实的死结**：NVML 说「PID 12345 用了 1.12 GB」，但容器里 `/proc/12345` 可能根本不存在（或者更糟，是另一个无关进程）。

### 解法

> gputaskman 把 **NVML 未解析的 PID** 与**容器里映射了 `libcuda.so` 的进程**配对。

**关键洞察在于 `libcuda.so` 的加载方式：**

> （NVML-only 工具如 `nvidia-smi` 会打开同样的设备文件，但**从不加载 libcuda**。）

**也就是说：加载了 `libcuda.so` 的进程，就是真正在用 CUDA 的进程。** 而 `nvidia-smi` 之类只是打开设备文件，不算。

### 为什么按顺序配对是对的

> **两个 PID 命名空间都按创建顺序编号，所以配对是按顺序的**：`*` 表示计数吻合，或者进程在 gputaskman 运行期间启动从而被钉住；`?` 表示 NVML 列出的计算进程比容器里有的多（同一 GPU 上还有另一个容器）。

**「两个 PID 命名空间都按创建顺序编号」** —— 这个性质让「按序配对」从一个 heuristic 变成了有依据的做法。

### 实测验证

作者在 Vast.ai 的一个 Docker 容器上做了实测（Ubuntu 22.04、RTX 3060 Ti、驱动 580.82.09）：

> 启动时已在跑的两个 PyTorch 任务、一个在观察期间启动的、一个被 kill 的，**全部被正确匹配到对应的容器 PID**，并给出了各自的 NVML 大小（1.12、2.52 和 1.59 GB）与实时 GPU%。
>
> 一个 Ollama 的 `qwen3:0.6b` runner 被检测到并从 Ollama 的 store 里**以 `api+mapped+cmdline` 证据命名**，展示了它的权重 / KV-cache / compute 分解，TUI 也渲染出来了。

**注意 `api+mapped+cmdline` 这个三重证据标注** —— 这又是同一个原则：**结论的强度要能被看出来。**

而剩下对不上的进程会显示成 `H:<pid>`，意思是「**这个容器之外**」（比如宿主机的显示服务器），并且**绝不在本地去查它**。

## 五、WSL：一个更麻烦的场景

WSL 之所以特殊，是因为 **GPU 归 Windows 管**。

> WSL 不同，因为 GPU 归 Windows 所有。**Linux 看不到自己的进程用了多少 VRAM**：
>
> - `nvidia-smi` 不列出任何进程；
> - NVML 的每进程采样携带的是 **Windows PID**（在 Linux 的 `/proc` 里永远查不到）；
> - **Windows 把所有 Linux 的 GPU 内存都算在 VM worker 进程 `vmwp.exe` 头上。**

### 解法：借一个常驻的 PowerShell

> 当 WSL interop 启用时（`/proc/sys/fs/binfmt_misc/WSLInterop` 读出 `enabled`），gputaskman 会启动**一个常驻的 `powershell.exe`**，通过与 Windows 后端相同的 **PDH array API** 读取 Windows GPU 计数器，并**每秒回传一次**。

（**这一段是全文我唯一想原样保留的英文** —— 因为它解释了一件很反直觉的事：**为什么一个 Linux 工具要常驻一个 PowerShell 进程。** 答案不是偷懒，而是 **WSL 场景下 GPU 归 Windows 所有**，Linux 侧的 NVML 只能看到 Windows PID，看不到自己进程的显存用量 —— 所以唯一的出路就是**借用宿主机的计数器接口**，而且必须用**同一套 PDH array API**，否则数字对不上。）

**复用了与 Windows 后端同一套 PDH array API** —— 这个细节说明它不是自己重新实现了一套采集，而是**用了同一套底层**，所以数字对得上。

然后：

> **WSL VM（`vmwp.exe`）是 Linux GPU 内存的精确总量** —— 跨所有发行版、WSLg 和 Docker Desktop。
>
> **Windows 应用**以 `W:<pid>` 行出现，带它们的 VRAM、spill、paged 与引擎负载。
>
> **Windows 和 Linux 的 PID 是不同的命名空间，所以前缀能把它们分开。**

### 但「Linux 行」的 VRAM 还是个难题

因为 Linux 进程的内存全被记在 `vmwp.exe` 头上，**要拆回每个 Linux 进程，还是得靠配对**：

作者的做法是**把 `vmwp.exe` 的 GPU 上下文与 Linux 进程匹配**（下面那个容器算法同样适用）。

还有两个工程细节值得记：

> 第一次主机采样要花约 2.5 秒；在此之前 TUI 显示 `starting`，而 `--once` 会等它。
>
> **主机适配器与 NVML 设备是按内存用量配对的**，因为 WSL 的适配器 LUID 与主机的不同。

**「按内存用量配对」** 这个做法有点粗糙但很实用 —— 因为在 WSL 场景下，能对上的只有「谁占了多少显存」这个信号。

## 六、AMD 路径：靠内核，不靠额外包

> **原生 Linux 上的 AMD GPU**（`amdgpu` 驱动）**不需要 ROCm、AMD SMI 或任何额外包**：内核已经暴露了需要的东西。

具体来源：

| 数据 | 来源 |
|---|---|
| 设备 VRAM、GTT、负载、温度、功耗、频率、风扇、PCIe 链路 | `/sys/class/drm/card*/device` 及其 `hwmon` |
| 每进程 VRAM 与 GTT | `drm-resident-vram` / `drm-resident-gtt`（老内核是 `drm-memory-*`）与 `/proc/<pid>/fdinfo/<fd>` 的 `drm-shared-*` |
| 每进程引擎负载（gfx / compute / video） | `drm-engine-*` 的 busy time，**采样两次** |

**「采样两次」这个限制很有意思** —— 因为 `drm-engine-*` 的 busy time 是累计值，**要算增量至少需要两个采样点**。所以工具在只有一个样本时，引擎负载显示 `n/a`（「直到新客户端有两个样本之前都是 n/a」）。

### 一个 APU 的特殊处理

> **GTT 是 GPU 可访问的系统 RAM**，所以它会填满 SPILL 列（以及设备的 shared），就像 WDDM 的 non-local 用量。
>
> 在 **APU**（集成显卡，通过 amdgpu 不报告 VRAM vendor 来检测，这是一个在一块 APU 上验证过的启发式）上，**GTT 就是 GPU 的正常内存，而「VRAM」只是一块 RAM  carve-out**，所以 GTT 仍然显示，但**永远不会被标记为 spill**，而一个 LLM 的内存是它的 VRAM **加上** GTT。

**「一个 LLM 的内存是它的 VRAM 加上 GTT」** —— 这条对做本地推理的人很实用，因为 APU 上跑小模型的显存占用经常被算错。

**而「通过 amdgpu 不报告 VRAM vendor 来检测 APU，这是一个在一块 APU 上验证过的启发式」** —— 作者把启发式方法和它的验证范围一起写出来了，这是很负责的表述。

### 作者的实测

> 裸机 Arch Linux（内核 7.2.15，amdgpu），Radeon RX 9070 系列（Navi 48）加一块 Radeon 610M 集显：**两张卡都被找到、命名并读取**；用 ffmpeg 做 VAAPI HEVC 编码和解码，各自显示为 ~95-100% 的 video 负载；在 RX 9070 上两者都被记到 amdgpu 的统一 enc 环上，所以显示为 `video` 而不拆分。
>
> **桌面进程的 VRAM 加起来小于显卡报告的已用 VRAM**，多出来的那部分是合成器导入的窗口，被列为 shared。

**「桌面进程的 VRAM 加起来小于显卡报告的已用 VRAM」** —— 这正是这个工具的价值所在：**它把差额指出来了，而且告诉你差额在哪（shared）。**

还有一个更硬的验证：

> llama.cpp 的 ROCm 服务器镜像（Qwen3-4B-Instruct-2507 Q4_K_M，`-ngl 99 -c 8192`，与一个正在运行的游戏并行）显示为一个 `LLM` 行，标记 `llama.cpp+ggml+HIP`，**3.95 GB VRAM** —— 与 **2.49 GB 权重 + 1.21 GB f16 KV cache + 计算缓冲**的加总吻合，也与 KFD 在 `/sys/class/kfd/kfd/proc/<pid>/vram_*` 报告的 **4.11 GB** 相符。

**三个独立来源的数字互相印证** —— 权重分解、fdinfo 归属、KFD 报告。**这才是让一个估算值变得可信的方式。**

## 七、还有一类情况：无法归属

工具还有一整类「说不清归属」的状态，我挑几个：

| 标记 | 含义 |
|---|---|
| **Shared client**（fd 传递、fork） | 「一组计数器，而没有任何东西说明是哪个进程在用」——GPU% 也是 `n/a` |
| **Shared buffers**（合成器导入的窗口、视频帧） | `drm-shared-*` 按缓冲区**倾向**住在哪里计数，`drm-resident-*` 按**实际**在哪里计数，**所以 resident 减 shared 不是私有内存，而且永远不会被计算** |
| **Primary node**（`/dev/dri/card*`，通常是合成器） | 「root 拥有的 logind 保留着该 fd 的一个副本，普通用户看不到，因此无法证明单一持有者」 |
| **Legacy** | 老内核的 amdgpu fdinfo 缺少 `drm-shared-vram`/`drm-shared-gtt` |
| **Incomplete** | 该进程的部分 fd 或 fdinfo 读不到 |
| **Partial scan** | 「TUI 的 50 ms 列举预算用完了，所以它跳过的某个进程可能持有同一个 client」 |

**「Shared buffers」那一条特别值得说**，因为它是一个容易算错的地方：

> **`drm-shared-*` 按缓冲区*偏好*住在哪里计数，而 `drm-resident-*` 按缓冲区*实际*在哪里计数，所以 resident 减 shared 不是私有内存，而且永远不会被计算。**

**「resident 减 shared」这个看起来很自然的减法，其实是不成立的。** 工具明确拒绝做这个计算。

**而 Partial scan 那一条是我最喜欢的** —— 它把一个「工具自己的性能限制」也暴露给了用户：

> **TUI 的 50 ms 列举预算用完了**，所以它跳过的某个进程可能持有同一个 client（GPU% 也是 n/a）。预期在桌面上很少见（约 8000 个 fd 需 ~9 ms，但这条规则下还没重新测量过）；**一次性输出总是完整扫描**。

**「约 8000 个 fd 需 ~9 ms，但这条规则下还没重新测量过」** —— 作者连自己的性能估算的验证状态都标出来了。

## 八、作者自己的实测观察

Tom's Hardware 的作者 Mark Tyson 拿到了 v0.3.0 的 Windows 便携版并试了：

> **启动时我发现没有任何任务在用我笔记本的独显** —— 于是我跑了老伙计 Unigine Valley 这个 GPU 基准测试，**把 RTX 4060 从沉睡中叫醒**。
>
> 我注意到**实时图表（GPU 负载、VRAM 使用、温度等）比 Hanselman 的示例截图里更突出**。也许他截的是这个工具的更早版本。

**这个细节本身就说明了工具的典型用法场景** —— 你装上它，先发现「咦，我的独显在 idle」，然后才开始处理真正的问题。

而 Hanselman 自己的截图里，最吃显存的应用是：

> **他的 RTX 4080S 系统上，最吃 VRAM 的应用是桌面窗口管理器。**

**这个观察挺有意思**：一个 4080S 的显存大头是桌面合成器，不是 AI 模型。**而这正好解释了 gputaskman 为什么要把「桌面合成器」和「模型权重」放在同一张表里** —— 因为对很多人来说，真正占着显存的是前者。

## 九、几个值得单独记的细节

### 它的定位是「早期、实验性软件」

README 原话：**「早期、实验性的软件。」** 而且作者在社交媒体评论里暗示，**扩展的 GPU 监控能力可能会成为 Windows 的标准功能**。

**所以它的定位更像是「一个探路者」而不是「一个产品」。**

### MIT 许可证 + PyPI 分发 + 便携版三件套

- **MIT 许可证**，「实验性软件」共享；
- **在 PyPI 上**，`uv tool install gputaskman` 或 `pipx install gputaskman`，也提供更短的 `gtm` 命令。**不需要克隆仓库**；
- **Windows 便携 ZIP** 分 Intel/AMD x64 与原生 ARM64 两个**独立的原生构建**（不是通用可执行文件），**不需要 Python、uv、CUDA Toolkit、模型下载或任何安装**。

Linux 侧也有便携 tar.gz（x64 / arm64），要求 glibc 2.35+（Ubuntu 22.04、Debian 12 或更新）。

**「不需要 CUDA Toolkit」这一条对想快速看一眼的人很关键** —— 因为大部分 GPU 监控工具都需要那套几 GB 的东西。

### 但便携版有个明确的短板

> **构建目前是未签名的**；代码签名和安装程序**不属于这次初始分发的一部分**。每个 ZIP 都附带许可证和一个 `.zip.sha256` 伴随文件**用于完整性检查**。

**「未签名」+「只有 SHA256」** —— 这个组合我在前一篇 Barracuda 那篇里刚讨论过：**SHA256 证明「下载的东西没被改坏」，但不证明「它确实是作者发布的」。** 这里也一样。

而 **NVIDIA 的驱动会自带 NVML，AMD ADL 由受支持的 AMD Windows 驱动提供** —— 也就是说它不打包任何厂商 SDK，只是调用系统里已有的。

### 它的忠实性在哪儿

> 「只有在你能检查的进程才会被列出；其它用户的进程需要 `sudo`。」而且**表头和 JSON（`process_status`）会说明有多少个没能检查到**，加了 `sudo` 就把其它用户的也包含进来。

**「说明有多少个没能检查到」** —— 又是一次「把不确定性显式化」。

### 关于「加速」的说法

README 里有一句很有意思的话：

> **CPU-only、NPU-only 和云端工作负载不在范围内。**

**而工具的整体思路是「加速」** —— 它不只报告数字，还**解释数字**（哪些是模型权重、哪些是 KV cache、哪些是 shared）。

**在一个所有人都在喊「用了多少 VRAM」但没人说「这些 VRAM 到底在干什么」的时代，这个方向是对的。**

---

## Sources

- shanselman/gputaskman 官方 README（含各平台可测指标矩阵、容器 PID 配对算法、WSL 跨命名空间方案、AMD 驱动路径实测）: <https://github.com/shanselman/gputaskman>
- Tom's Hardware, *Free open-source GPU task manager reveals exactly what's eating your VRAM*（Mark Tyson，2026-11-08，含作者实测 RTX 4060 的观察）: <https://www.tomshardware.com/pc-components/gpus/open-source-gpu-task-manager-reveals-exactly-whats-eating-your-vram-microsoft-vps-new-gpu-taskman-tool-reveals-every-process-using-your-gpu-how-much-memory-each-uses-and-breaks-down-ai-and-llm-workloads>
- Windows Central, *This free app explains where your GPU memory actually goes*（Sean Endicott，2026-11-06）: <https://www.windowscentral.com/hardware/gpus/this-free-app-explains-where-your-gpu-memory-actually-goes-and-it-comes-from-a-microsoft-engineer>
- Scott Hanselman 的发布说明（LinkedIn，2026-11-03）: <https://www.linkedin.com/posts/shanselman_theres-a-lot-going-on-in-my-gpu-im-making-activity-75>
- shanselman/gputaskman Releases（v0.3.0 起，含 Windows 便携版）: <https://github.com/shanselman/gputaskman/releases>

### 事实边界说明

- 各平台可测指标矩阵、容器 PID 配对算法与 `*`/`?`/`H:<pid>` 标记语义、WSL 的 `powershell.exe` + PDH array API 方案、AMD 的 `/sys/class/drm` 与 `drm-*` fdinfo 路径、APU 的 GTT 启发式、六种「无法归属」状态、以及各处「n/a 而不是 0」的表述：**全部引自官方 README**。
- Vast.ai 容器实测（RTX 3060 Ti、1.12/2.52/1.59 GB 匹配、Ollama qwen3:0.6b）、裸机 Arch 实测（RX 9070 + 610M、llama.cpp ROCm 的 3.95 GB 与 2.49 GB 权重 + 1.21 GB KV cache 的吻合、KFD 报告 4.11 GB）：均引自官方 README 的 live check 记录。
- Tom's Hardware 作者的实测观察（启动时无任务占用独显、跑 Unigine Valley 唤醒 RTX 4060、实时图表比示例截图更突出）：引自该报道。
- Hanselman 截图里「RTX 4080S 上最吃 VRAM 的是桌面窗口管理器」：引自 Tom's Hardware 报道。
- 「工具在 Windows/Linux/WSL/macOS 的定位」「MIT 许可证」「PyPI 分发」「便携 ZIP 未签名」「作者暗示 GPU 监控能力可能进入 Windows 标准功能」：均引自官方 README 与社交媒体说明。
- 本文对「这个工具的核心价值在于把不确定性显式化」的判断是本文的解读，README 未用此措辞，但其对 estimate/measurement 的区分与各处 n/a 说明支持这一读法。
- 本文只做工具解读与使用场景讨论，不构成对任何 GPU、驱动或产品的推荐。
