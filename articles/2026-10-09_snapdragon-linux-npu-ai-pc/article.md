---
title: "骁龙笔记本的 AI PC 叙事，在 Linux 上还缺最关键的那一环"
date: 2026-10-09
slug: snapdragon-linux-npu-ai-pc
tags: [Qualcomm, Snapdragon X2, Linux, NPU, Hexagon, AI PC, fastRPC, QNN, OpenVINO, 端侧AI, Debian, Ubuntu, Arm笔记本, 译文]
category: 电脑与硬件
author: FreeLAMP.com
original_source: "MakeUseOf / Qualcomm 开发者博客 / Canonical 博客 / Linux 内核文档"
original_author: "Brady Snyder（MakeUseOf）；Qualcomm；Canonical"
original_date: 2026-10-09
original_url: "https://www.makeuseof.com/qualcomm-snapdragon-laptops-linux/"
description: "高通把 Snapdragon X2 的 GPU 和 NPU 驱动上游化，为 Linux 提供早期开发者预览，Debian 年底支持、Ubuntu 2027 上半年跟进，HP/华硕/HUMAIN 也计划在 2027 上半年提供 Linux 支持。MakeUseOf 因此说这是「移除购买骁龙笔记本的最大障碍之一」。本文核对事实后指出一个被普遍忽略的问题：在这套「AI PC」叙事里，NPU 在 Linux 上恰恰是成熟度最低的一环，内核侧的 fastRPC 通道在落地，但用户空间仍依赖 QNN SDK，HTP 后端只支持量化模型，而 ONNX Runtime 的 QNN 提供程序官方只列了 Android 和 Windows。"
published: true
---

> 原文：[Qualcomm is fixing one of the biggest reasons to avoid Snapdragon laptops](https://www.makeuseof.com/qualcomm-snapdragon-laptops-linux/)（MakeUseOf，2026-10-09，作者 Brady Snyder）
> 补充来源：[Qualcomm：Announcing Linux on Snapdragon X2 Series Early Developer Preview](https://www.qualcomm.com/developer/blog/2026/09/announcing-linux-on-snapdragon-x2-series-early-developer-preview)、[Qualcomm：Snapdragon Summit 2026 总结](https://www.qualcomm.com/news/onq/2026/09/snapdragon-summit-agentic-ai-pcs-linux)、[Canonical：Ubuntu coming soon to Snapdragon X2 Series platforms](https://canonical.com/blog/ubuntu-coming-soon-to-qualcomm-snapdragon-x2-series-platforms)、[Linux 内核 accel 子系统文档](https://kernel.org/doc/html//next/accel/index.html)、[ONNX Runtime QNN 执行提供程序](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html)
> 本文为**解读**。第三节关于 NPU 在 Linux 上成熟度的分析、第四节对 AI PC 叙事的判断是笔者重点补充的部分。

## 一句话结论

高通把 **Snapdragon X2 的 GPU 与 NPU 驱动上游化**，给出 Linux 早期开发者预览，**Debian 年底支持、Ubuntu 2027 上半年跟进**，**HP、华硕、HUMAIN 也计划在 2027 上半年提供 Linux 支持**。原文说这是「移除购买骁龙笔记本的最大障碍之一」，**这个判断大体成立，但它自己也在文末承认还有三个理由**。而我要补充一个原文完全没提的问题：**在这套「AI PC」叙事里，NPU 在 Linux 上恰恰是成熟度最低的一环**。内核侧的通道在落地，**但用户空间仍然依赖厂商 SDK，且只支持量化模型**。**换句话说，「Arm + Linux + AI PC」目前是一个承诺，不是一个现货。**

## 一、先把事实对齐

原文的核心信息我核对了一遍，和官方来源一致：

| 项目 | 内容 |
|---|---|
| 开放范围 | **仅 Snapdragon X2 系列笔记本**；**不支持初代 X 系列**，**也不支持基于骁龙芯片的台式机** |
| 上游化的驱动 | **Hexagon NPU**（经 fastRPC）与 **Adreno GPU**（经 Freedreno、Turnip、Rusticl） |
| 参考用户态 | **Debian 13 「Trixie」** + 定制内核 |
| 镜像获取 | [qualcomm-linux/qcom-deb-images](https://github.com/qualcomm-linux/qcom-deb-images)（实测：2025-03 建仓，**58 stars，129 个未关闭 issue**，仓库今天仍在更新） |
| 官方发行版时间表 | **Debian：2026 年底**；**Ubuntu：2027 上半年**（Canonical 认证镜像） |
| OEM 承诺 | **HP、华硕、HUMAIN 计划 2027 上半年提供 Linux 支持** |
| 明确的定位 | **面向内核/驱动开发者、发行版维护者、硬件使能团队**，**不是给终端用户的成品** |

**一个必须说清的边界**：原文写「You can try Linux on Snapdragon X2 laptops today」（今天就可以在 X2 笔记本上试 Linux），这是对的，**但它的含义是「你可以自己编译内核刷进去」，而不是「下载个 ISO 双击安装」**。Issues 里那 129 个未关闭条目，就是这句话的真实成本。

## 二、原文的判断，以及它自己的反证

原文的论点是**高通正在移除购买骁龙笔记本的最大障碍之一**。这个判断我认为**大体成立**：把驱动上游化、让发行版主动认证，确实比「社区从 Windows 镜像里手动抠固件」高了一个层次的承诺。

**但有意思的是，原文在结尾自己列了三条仍然不该买骁龙笔记本的理由**：

> **2026 年有几个跳过骁龙笔记本的理由。** 有些用户依赖只能在 x86 芯片组上运行的软件。游戏玩家会发现能用（且跑得好）在 Arm 芯片上的游戏库仍然相当有限。**而且到目前为止，那些比起 Windows 更喜欢 Linux、想要开箱即用切换操作系统方案的人，还是得坚持 Intel。**

**最后那句是致命的**，因为它正好否定了标题。**「Linux 支持」改善的是长期前景，不是当下的开箱即用体验**，而这恰恰是那句「你要坚持 Intel」的意思。

**这是一个很典型的科技报道结构**：标题给一个强判断，正文补足限定，结尾把限定说透。**读的时候如果只看标题，你会得到和前一段完全相反的印象。**

## 三、我认为这才是关键：AI PC 叙事在 Linux 上缺的那一环（本文重点）

原文那句关于 NPU 的话非常轻，我原文引用：

> **本地 AI 工作负载最终将能够使用 Snapdragon X2 系列的 NPU 进行推理工作负载，据高通说。**（Local AI workloads will eventually be able to use the Snapdragon X2 series' NPU for inference workloads, according to Qualcomm.）

**「eventually」（最终）和「according to Qualcomm」（据高通说）这两个限定词，是整篇里最诚实、也最容易被读者跳过的部分。** 而它指向的正是你关心的那个问题：**所谓 AI PC，在 Linux 上到底能不能用上 NPU？**

**我把这一层的现状拆开看。**

### 内核侧：通道在落地，但只是「通道」

Linux 内核确实有专门的算力加速器子系统（`accel`），目前文档里列出的驱动包括：

| 驱动 | 归属 | 说明 |
|---|---|---|
| `accel/amdxdna` | **AMD NPU** | 集成在 AMD 客户端 APU 上的多用户 AI 推理加速器，基于 XDNA 架构 |
| `accel/qaic` | Qualcomm Cloud AI | **注意：这是数据中心产品**，不是笔记本里的 Hexagon |
| `accel/rocket` | Rockchip NPU | RK3588 等 SoC |
| `intel_vpu` | Intel NPU | 在内核 `drivers/accel` 树里，同时有独立的 [intel/linux-npu-driver](https://github.com/intel/linux-npu-driver)（MIT 许可） |

**高通的 Hexagon 走的是 fastRPC 路径**（NPU 实际跑在计算 DSP 上，应用处理器经 FastRPC 抵达）。**上游化这件事是真的，也是必要的**，没有它，任何发行版都没法把 NPU 当一等公民对待。

**但内核驱动只解决「运输问题」，不解决「怎么用」。**

### 用户空间：这里才是真正的门槛

**要在高通 NPU 上跑推理，你需要 QNN（Qualcomm AI Engine Direct）SDK。** 它的后端是这样的：

| 后端库 | 目标 | 支持的模型精度 |
|---|---|---|
| `libQnnCpu.so` | CPU（参考实现） | FP32 |
| `libQnnGpu.so` | Adreno GPU | FP32 / FP16 |
| **`libQnnHtp.so`** | **Hexagon NPU（HTP）** | **仅量化模型（INT8 / INT16）** |

**这三行合起来说明了几件事**：

- **NPU 那条路只吃量化模型**。也就是说，你手上一个现成的 FP16 模型不能直接扔给 NPU，**得先走量化流程**，而量化本身要工具链、要调参、要验证精度损失；
- **SDK 的获取是有门槛的**。高通的 Hexagon SDK 是登录后下载并附带许可协议的（虽然它确实提供 Windows 和 Linux 两个版本）；
- **推理框架的官方支持清单里没有 Linux 桌面**。这一点最值得注意：[ONNX Runtime 的 QNN 执行提供程序的文档](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html)明确写着，**它可用于「搭载高通骁龙 SoC 的 Android 和 Windows 设备」**，预编译包只有 Windows（ARM64 用于推理，x64 用于量化），Python 包 `onnxruntime-qnn` 的依赖里写的也是「Windows ARM64（用于在本地设备上用高通 NPU 推理）」。

**把这三条放在一起，得到的结论是**：**今天在 Linux 上使用骁龙 NPU，你需要自己搞定内核驱动、自己拿到并适配 QNN SDK、自己处理量化，而且推理框架的官方文档可能根本不覆盖你这个平台。** 这与「AI PC 出厂就能跑本地大模型」是两回事。

### 对比一下 Intel，就能看出差距在哪

**Intel 的 NPU 在 Linux 上走的是另一条路**：

- 内核驱动 `intel_vpu` 在主线内核的 `accel` 树里，**并且有公开的 sysfs 接口**（从内核 6.11 的 `npu_busy_time_us`，到 6.15 的 `npu_memory_utilization`，到 **7.2 新增的频率控制** `hw_max_freq`/`set_max_freq` 等）；
- 用户态驱动**托管在 GitHub 上、MIT 许可**（[intel/linux-npu-driver](https://github.com/intel/linux-npu-driver)，461 stars）；
- **配套的推理栈是 OpenVINO**，而 OpenVINO **有专门的 NPU 插件，并且 Linux 驱动是有文档的**。

**需要注意的分寸**：**这不等于 Intel 的 Linux NPU 就成熟了**。它的文档里同样有「NPU 编译器库是 2026.0 才作为预览特性引入」这样的说明，**也还在演进中**。**但两条路的性质不同**：Intel 那边是**开源用户态 + 开源推理栈 + 公开文档**，高通这边是**登录下载的 SDK + 只支持量化的后端 + 文档未覆盖 Linux 桌面**。

**所以对「AI PC 上跑 Linux」这件事，我的判断是**：

> **NPU 是这套叙事里最后落地的一环，而不是最先落地的一环。** 高通上游化 fastRPC 是必要的第一步，但**从「通道可用」到「你能用 Ollama 或 llama.cpp 调用它」，中间隔着量化工具链、SDK 许可、以及推理框架的适配**。原文用了「eventually」这个词，是准确的。

## 四、原文没提的另外两件事

### 第一，Canonical 那边其实给了很具体的企业承诺

原文提到「Canonical 可能为普通用户推出一个一键安装器」，这是猜测。**而 Canonical 官方博客里那段其实具体得多，也更值得关注**：

- **认证的 Ubuntu 镜像**，在 X2 硅片上经过验证，**「不需要手动调内核或集成驱动」**；
- **Ubuntu Pro 提供最长 15 年的安全维护**、内核实时补丁、以及 **FIPS 与 DISA-STIG 合规覆盖**；
- **Landscape** 用于规模化管理 Linux 笔记本机队；
- 强调**「在云数据中心里用 Linux 开发、微调、部署的 AI 模型，可以原生地迁移到骁龙 X2 的 Linux 笔记本上」**；
- 硬件侧规格：**最多 18 个 Oryon 核、最高 5.0 GHz、NPU 最高 80 TOPS、LPDDR5x 最高 228 GB/s、48 GB 容量**；
- 安全上提到 **Qualcomm SPU**（安全处理单元）提供芯片到云的安全、Wi-Fi 7、可选 5G。

**「15 年安全维护 + FIPS/DISA-STIG + Landscape」这套组合，说明 Canonical 瞄准的是企业采购，而不是个人折腾者。** 这比「一键安装器」的想象更实在，也更能解释为什么这件事能持续推进，**因为它有明确的付费客户画像（企业 Linux 笔记本机队）**。

### 第二，「三个桌面操作系统」这个格局值得单独看

原文提到不久之后会有 **Windows 11、Linux、Googlebook OS** 三个基于 Arm 的选择。**这个格局的确立比「Linux 支持」本身更重要**：

- **Googlebook OS 用 Android 技术栈 + Linux 子系统**，高通和 Google 合作把 Snapdragon X Elite 带到 Googlebook 笔记本上，Dell 和 HP 都是伙伴；
- **这让骁龙的 Linux 内核支持有了除「个人爱好」之外的商业理由**：Googlebook OS 本身就依赖 Linux 内核；
- **对用户来说，真正的变化是「Arm 笔记本不再等于 Windows 笔记本」**。这个前提下，Linux 支持就不是可选项，而是必须项。

**原文说得对**：Googlebook 这条线让整件事「更有意思了」，**因为它意味着高通支持 Linux 内核的动力不再取决于 Linux 桌面用户的数量。**

## 五、给关注 NPU / AI PC 的人的判断框架

你说要持续关注骁龙笔记本特别是 AI PC 方向，我建议**把「能不能用 NPU」拆成四个可验证的问题**，而不是看厂商给的 TOPS 数字：

| 问题 | 为什么关键 | 怎么验证 |
|---|---|---|
| **① 内核驱动进主线了吗？** | 决定发行版能否开箱支持 | 查该硬件在主线内核的 `accel`/`drm` 树里有没有驱动 |
| **② 用户态组件是开源的吗？** | 决定你能不能自己修、发行版能不能打包 | 开源的去 GitHub 看；要登录下载 + 许可协议的，长期依赖厂商 |
| **③ 你常用的推理框架支持它吗？** | **这是最实际的检验** | 去 ONNX Runtime / OpenVINO / llama.cpp 的文档里查**有没有列你这个平台**。列了 Android 和 Windows 而没有 Linux，就是没支持 |
| **④ 是否需要量化？量化流程成熟吗？** | 决定精度损失和上手成本 | 看后端支持哪些精度；只支持 INT8/INT16 意味着必须先做量化 |

**我的提示是**：**问 ③ 是最省时间的**。厂商的博客会讲「上游化 NPU 驱动」，**但不会告诉你「Ollama 在你的平台上默认调不动 NPU」**。而推理框架的文档不会撒谎，**它列了哪些平台，就是真的能用哪些平台。**

**另外，关于「80 TOPS」这个数字**（Snapdragon X2 Elite 的 NPU 规格），值得说一句：**TOPS 是硬件能力上限，不是你能拿到的性能**。要把它变成实际收益，你需要模型能跑在那个后端上、精度匹配、且框架支持。**在 Linux 上这一整条链目前还没走通**，所以现在讨论「80 TOPS 在 Linux 上能干什么」为时过早。

## 六、我的判断

**第一，这件事的意义我认同，但它是「窗口打开」而不是「门槛消失」。** 把驱动上游化、让 Debian 和 Ubuntu 主动认证、拿到 HP/华硕/HUMAIN 的承诺，**这些是真实且必要的进展**。但原文自己在结尾说「想要开箱即用切换系统的还是得坚持 Intel」**：这句话定义了当下的真实状态**。**2027 年上半年之前，它改善的是「值得关注」，不是「可以下手」。**

**第二，最该被纠正的是 AI PC 的宣传与 Linux 现实之间的落差。** 厂商在讲 agentic AI、80 TOPS、本地推理；**而在 Linux 上，NPU 恰恰是整条链里最靠后的一环**。**内核通道刚落地、用户态依赖登录下载的 SDK、HTP 后端只吃量化模型、推理框架的官方支持清单里还没有 Linux 桌面。** 我不怀疑它会变好，**fastRPC 上游化正是为这件事铺路**，但今天把「骁龙 + Linux + AI PC」当成既成事实，是不成立的。

**第三，我认为最值得记住的一点来自 Intel 的对照**：**同一个功能，两条路径的差别不在硬件，而在「用户态是否开源、文档是否覆盖你这个平台」**。内核驱动进主线是必要条件，但它只解决「硬件能被操作系统识别」。**真正决定你能不能用的，是上面那层有没有人替你打包、有没有框架愿意适配。** 这也是为什么我建议关注 Canonical 那段「认证镜像 + 15 年维护 + FIPS/DISA-STIG」**：那才是从「能启动」走到「能采购」的关键一步。**

**第四，如果你在等一个行动时机**，我会给三个观察点：

1. **Debian 年底的镜像是不是「可安装」而不只是「可启动」**：看 `qcom-deb-images` 的 issue 关闭速度（现在 129 个未关闭）；
2. **Ubuntu 2027 上半年那个「认证镜像」是否真的做到 Canonical 承诺的「不需要手动调内核或集成驱动」**：这一条如果兑现，性质就变了；
3. **NPU 那边最先出现的信号不是 TOPS 提升，而是推理框架的文档里多出一行 `Linux`**。看到 ONNX Runtime 或 OpenVINO 的支持平台清单里出现骁龙 Linux，那才是 AI PC 在 Linux 上真正成立的时刻。

**在那之前，我的结论很简单**：**这次进展值得记进「值得关注的硬件」，但不值得作为「现在就买骁龙笔记本装 Linux 跑本地 AI」的理由。**原文那句「你要坚持 Intel」虽然出现在一篇正面报道的末尾，却是全文最实用的一句。

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 事件 | 高通发布 **Snapdragon X2 系列 Linux 早期开发者预览**，并把 GPU 与 NPU 驱动上游化 |
| 上游化内容 | **Hexagon NPU**（经 fastRPC）、**Adreno GPU**（Freedreno / Turnip / Rusticl） |
| 参考环境 | **Debian 13 「Trixie」** + 定制内核 |
| 镜像仓库 | [qualcomm-linux/qcom-deb-images](https://github.com/qualcomm-linux/qcom-deb-images)：2025-03 建仓，**58 stars，129 个未关闭 issue**，仍在更新 |
| 发行版时间表 | **Debian：2026 年底**；**Ubuntu：2027 上半年**（Canonical 认证） |
| OEM 承诺 | **HP、华硕、HUMAIN：2027 上半年**提供 Linux 支持 |
| ⚠️ 覆盖范围 | **仅 X2 系列笔记本**；**不支持初代 X 系列**，**不支持骁龙台式机** |
| 定位 | 面向开发者与发行版维护者，**非终端用户成品** |
| X2 Elite 规格 | 最多 **18 个 Oryon 核**（最高 5.0 GHz）、**NPU 最高 80 TOPS**、**LPDDR5x 最高 228 GB/s**、48 GB |
| ⚠️ NPU 用户态现状 | 依赖 **QNN / Hexagon SDK**（登录下载 + 许可协议）；**HTP 后端仅支持量化模型（INT8/INT16）** |
| ⚠️ 推理框架支持 | **ONNX Runtime 的 QNN 提供程序官方仅列 Android 与 Windows**；预编译包与 Python 包依赖均指向 Windows ARM64 |
| Intel 对照 | 内核 `intel_vpu` 在主线 `accel` 树（**7.2 新增频率控制 sysfs**）；用户态驱动 [MIT 开源](https://github.com/intel/linux-npu-driver)（461 stars）；**OpenVINO 有 Linux NPU 插件与文档** |
| 其他内核 accel 驱动 | `amdxdna`（AMD NPU）、`qaic`（**Qualcomm Cloud AI，数据中心**）、`rocket`（Rockchip） |
| Canonical 的企业承诺 | 认证镜像（**无需手动调内核/集成驱动**）、**Ubuntu Pro 最长 15 年安全维护**、内核实时补丁、**FIPS / DISA-STIG**、Landscape 机队管理、Qualcomm SPU 芯片到云安全 |
| 三系统格局 | Windows 11 / Googlebook OS / Linux；Googlebook OS 用 Android 技术栈 + Linux 子系统 |
| ⚠️ 原文的自我反证 | 文末列了 2026 年仍不该买的三条理由，最后一条是「想要开箱即用切换系统的人还得坚持 Intel」 |

## 延伸阅读

- [MakeUseOf 原文：Qualcomm is fixing one of the biggest reasons to avoid Snapdragon laptops](https://www.makeuseof.com/qualcomm-snapdragon-laptops-linux/)
- [Qualcomm：Linux on Snapdragon X2 Series 早期开发者预览](https://www.qualcomm.com/developer/blog/2026/09/announcing-linux-on-snapdragon-x2-series-early-developer-preview)
- [Canonical：Ubuntu coming soon to Snapdragon X2 Series platforms](https://canonical.com/blog/ubuntu-coming-soon-to-qualcomm-snapdragon-x2-series-platforms)
- [ONNX Runtime：QNN 执行提供程序（注意支持平台清单）](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html)
- [本站：Snapdragon X 笔记本的 Linux HDR 支持来了：静态 HDR10，补丁是 LLM 辅助写的](/articles/2026-10-09_qualcomm-msm-drm-hdr/)
- [本站：高通在夏威夷谈 Snapdragon X2 的 Linux：早期开发者预览，Debian 13 用户态，HP/华硕承诺 2027 H1 官方支持](/articles/2026-09-23_qualcomm-snapdragon-x2-linux/)
- [本站：一个散热器页面泄露的 EPYC Verano：72 核不难，24 通道 LPDDR5X 才是真信号](/articles/2026-10-09_epyc-verano-sb1-lpddr5x/)
