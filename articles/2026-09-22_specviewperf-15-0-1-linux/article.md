# SPECviewperf 15 终于出 Linux 原生版：x86_64 / AArch64 都有，但只给 OpenGL 4.5

> 原文：[SPEC Releases SPECviewperf 15.0.1 For Linux](https://www.phoronix.com/news/SPECviewperf-15.0.1-Linux)（Phoronix，Michael Larabel，2026-09-22）。本文由 LeisureLinux 翻译整理并加注解读；文内事实来自原文。

SPEC 在 **2025 年 5 月**推出 SPECViewPerf 15 作为这款业界标准工作站显卡基准的最新大版本。可惜 Linux 支持再次落后——SPECViewPerf 15 首发只在 Microsoft Windows 上。今天 Linux 终于追上：SPEC 发布了 SPECViewPerf 15.0.1 的 **Linux 原生构建**。

## 译文：15.0.1 有什么

SPECViewPerf 15.0.1 相比上一个 Linux 版本（SPECViewPerf 2020）是一次大更新。这个 Linux 构建同时提供 **x86_64 和 AArch64** 工作站版本。

不过有个刺眼的差：Windows 版的 SPECViewPerf 15 已经加了 **DirectX 12 和 Vulkan** 图形 API 支持，而 Linux 版的 15.0.1 **只支持 OpenGL 4.5**。

想了解细节可看 [SPEC.org](https://gwpg.spec.org/benchmarks/benchmark/specviewperf-15-linux-edition/)。Larabel 表示会跑一些 15.0.1 的 Linux 测试，用于后续的工作站 GPU 与驱动评测。

## 解读：补上了「Linux 平等」，但留了 API 代差

**1. 工作站图形基准的 Linux 短板，终于被补上——但仍是「二等公民」。**

SPECViewPerf 是 CAD / DCC / 科学可视化领域的标准显卡基准（视图集覆盖 Maya、SolidWorks、CATIA、SNX、Creo、medical、energy 等）。Linux 版从 2020 直接跳到 15.0.1，对长期只在 Linux 上做图形评测的人是个迟到的补丁。但 Windows 已经 DX12 + Vulkan，Linux 还停在 **OpenGL 4.5**——这意味着同一张卡在两种 OS 上跑的视图集渲染路径不同，**跨平台数字不能直接比**，评测时要显式标注 API 口径，否则会得出误导性结论。

**2. AArch64 支持是实打实的好消息。**

Arm 工作站（Ampere、富士通 MONAKA 144 核这类）之前做专业图形性能评测没有官方基准可用；Apple Silicon 通过 Asahi/Linux 或虚拟机也是同理。官方 AArch64 构建让「Arm 工作站跑标准图形负载」从凑合变成可复现。

**3. Linux 为什么总慢半拍：视图集依赖 Windows 工作站应用。**

SPECViewPerf 的视图集本质是回放 ISV 应用（Maya/SolidWorks/CATIA…）的真实渲染流，而这些专业应用重心仍在 Windows。Linux 版要做重新适配与等效实现，自然滞后。这恰恰反映一个硬现实：**专业图形生态的重心还在 Windows**，Linux 在桌面创作/工程软件上仍是配角——基准的代差只是这个结构的表象。

**4. 对谁有用：GPU 厂商的 Linux 驱动验证工具。**

普通用户和游戏玩家基本无感（游戏有 3DMark/游戏内 benchmark）。但对 NVIDIA / AMD / Intel 在 Linux 驱动上的**工作站性能验证**与回归测试，这是必要且权威的工具——尤其 AArch64 让 Arm 平台的驱动团队有了对标基准。

一句话收尾：Linux 版的 SPECViewPerf 15 来了，AArch64 是惊喜，但 OpenGL 4.5 这道天花板提醒我们——专业图形的跨平台平等，还远没到。
