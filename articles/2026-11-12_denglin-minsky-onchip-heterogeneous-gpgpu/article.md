---
title: "登临科技 Minsky 架构：一颗芯片里塞进 SIMT、张量核与片上内存"
date: 2026-11-12
slug: denglin-minsky-onchip-heterogeneous-gpgpu
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：苏州登临科技股份有限公司港交所招股书（股份代号 9917，2026-10-30，中文版 PDF）业务章节「我们的基础架构 — GPU+ (Minsky™) 片内异构架构」、概要、技术脚注与产品代际表 ＋ 登临科技联合创始人王平 2022-07 量子位分享（GPU+ 设计动机、暗硅、片上网络、软件管理片上内存、xU 扩展、自研 IP）＋ 创始人李建文 2021-07 WAIC 演讲报道（软件定义片内异构、调度引擎、高吞吐数据交换网络、Hamming 工具链、3–10 倍能效早期口径）＋ 36 氪项目库（李建文曾任图芯科技副总裁、GPU/GPGPU IP 客户名单）＋ 券商招股概要与媒体报道（2025 年份额 1.0%、KS 系列占比、财务数据）＋ 国外对照：NVIDIA Volta Tensor Core 官方技术博客与 A100 白皮书、Google 第一代 TPU 官方架构说明（24MB Unified Buffer / MXU）、NVIDIA Jetson Orin DLA 官方技术简报与开发者文档、AMD HSA/hUMA 2013 资料、TPU/DSA 学术源流与 2024 年 ICPP 片上 scratchpad 管理论文"
original_date: 2026-10-30
original_url: "https://www.hkexnews.hk/listedco/listconews/sehk/2026/1030/2026103000024_c.pdf"
description: "本文按技术视角解读登临科技 GPU+（Minsky™）片内异构架构，并回答「架构从哪来、国外有没有同类」。先正名：这是 GPGPU/AI 加速芯片架构，不是 CPU 架构。招股书脚注定义 GPU+ 为「软件定义的片内异构专有计算框架」，把基于 SIMT 的可编程通用计算单元、面向 AI 优化的专用张量引擎、高带宽片上内存子系统集成进单颗芯片；架构图含 TU/CUs/xUs 集群、L2、MC、SPM、DMA，配套瀚铭（Hamming®）软件栈含驱动、CUDA 等效库与 AI 推理工具链。文章拆解三处实质区别：异构层级从板级下沉到片内、执行模型从单一 SIMT 变成按算子分派、软件栈承担翻译与调度双重职责；并用三代参数（256/512/560 TOPS INT8、239/192/819.2 GB/s、55/95/130 W）算出每瓦算力并非单调上升、II 代带宽低于 I 代，说明不能把代际数字当架构效率曲线。架构来源分两层：团队血统（创始人李建文曾任图芯科技 Vivante 副总裁，GPU/GPGPU IP 曾卖给飞思卡尔、英特尔、Marvell、Google、三星等；核心 IP 全自研）与产业/学术源流（DSA 领域专用架构、Dark Silicon 暗硅、HSA/hUMA 统一内存、scratchpad 近存计算）。国外同类不是单一产品而是三条线：NVIDIA Volta 起在 SIMT 的 SM 内加入 Tensor Core 并共享 L1/Shared Memory（Blackwell/Thor 已是可配置统一 256KB）、Google TPU 的 MXU + 24MB Unified Buffer 脉动阵列、NVIDIA Jetson Xavier/Orin 的 GPU 旁挂固定功能 DLA（TensorRT 统一调度、cuDLA 收进 CUDA 编程模型）。文章指出 Minsky 更接近「DLA 思路反向做进 GPGPU 单片 + CUDA 等效层」：差异不在三件套本身，而在保留 CUDA 编程面、把固定功能引擎与软件管理片上内存绑进统一调度、以及面向 55–130W 企业边缘/私有云而非训练集群。也如实标注边界：CUDA 等效非原生、效率对比均为厂商口径无第三方基准、2025 年份额 1.0%、18C 未商业化公司仍累计亏损。"
published: true
---

> 一手：港交所招股书业务与架构章节、创始团队公开演讲
> 对照：Volta / A100 官方资料、TPU 架构说明、Jetson DLA 技术简报、HSA / hUMA 资料
>
> 先正名：这是 GPGPU / AI 加速芯片架构，不是 CPU 架构。材料里「通用 GPU」的「通用」指通用计算，不是通用中央处理器。

招股书里最有技术含量的一段，藏在「业务」章节的脚注里，原文把那个「+」解释为「retain the programmability and flexibility of GPGPU, while adding and tightly integrating dedicated tensor acceleration」：

> 「GPU+」指基于软件定义的片内异构专有计算框架 Minsky™，把基于 SIMT 并行处理模型的可编程通用计算单元、针对 AI 工作负载优化的专用张量计算引擎、高带宽片上内存子系统集成在单一芯片内；「+」表示保留 GPGPU 的可编程与灵活性，添加并紧密集成专用张量加速功能。

这句话比「完全兼容 CUDA」「更高计算效率」这类宣传语精确得多。本文就按它展开，并回答你问的两件事：这套架构从哪来，国外有没有同架构产品。

## 一、架构本体：三件套 + 一张片上网络

招股书给的架构示意是按集群（cluster-0 … cluster-n）重复的结构，每个集群里能看到：

```
TU  CUs  xUs
L2  MC  SPM  DMA
```

- CUs：通用计算单元，走 SIMT（单指令多线程）—— 这是 GPGPU 的「通用」部分，负责不规则算子、自定义算子、以及非 AI 的并行负载；
- xUs / TU：可扩展的专用引擎（媒体/第三方报道里称张量加速单元，联合创始人王平提到「扩展 xU」用于加速行业共性计算）；
- L2 / MC / SPM / DMA：片上二级缓存、内存控制器、软件管理的暂存存储器（scratchpad）与 DMA 引擎，加上自研的高吞吐片内数据交换网络。

软件侧是统一的 瀚铭（Hamming®）软件栈：底层驱动、CUDA 等效库、AI 推理工具链，负责把算子分派到合适的引擎上。所以「软件定义」不是修辞 —— 硬件只提供多种算力池，谁跑哪一段由软件栈决定。

## 二、和普通架构的三处实质区别

| | 传统 GPGPU | 专用 ASIC/NPU | Minsky GPU+ |
|---|---|---|---|
| 计算引擎 | 一套 SIMT 通用核心跑所有算子 | 固定功能矩阵/卷积单元 | SIMT + 专用张量引擎同片并存 |
| 异构层级 | 板级（CPU + 独立 GPU 卡 + 可能的 FPGA） | 单芯片但无通用编程面 | 片内异构，走片内网络与 SPM |
| 内存 | 强依赖片外 HBM/GDDR 往返 | 大片上统一缓冲 | 高带宽片上内存子系统 + 软件管理 SPM，降低对外存依赖 |
| 编程面 | CUDA / OpenCL 原生 | 自建生态、迁移成本高 | CUDA 等效层 / 深度兼容层 |

① 把「板级搬运」换成「片内搬运」。 招股书明确把「依赖外部组件（CPU、GPU、FPGA）的传统离散异构系统」列为对照物。跨芯片走 PCIe 的数据往返是功耗与延迟大头；把三类单元放进一颗 die、中间走片内网络与 SPM，省的是这段。2021 年李建文在 WAIC 的说法更直接：「调度引擎可以在高维度控制算力分配，这些引擎既可并行也可独立工作，另外还有自主研发的高吞吐数据交换网络」。

② 按算子分派，而非一种引擎通吃。 王平 2022 年把设计动机讲得很清楚：AI 计算传的是 Tensor、算子大多结构化，所以给结构化部分配高密度专用单元；中密度并行计算仍交给 GPU 单元；再让软件栈只对需要加速的算子做特别处理。他还点名 Dark Silicon（暗硅）：传统片上堆大量中等效率核没法同时全开，于是选「高、中、低不同效率核各司其职」。这是典型的 DSA（领域专用架构）思路，只是落点选在「保留 GPU 编程面」这一侧。

③ 软件栈是架构的一部分，不是附属品。 招股书写「集成底层驱动程序、CUDA 等效库及 AI 推理工具链」，另一处写「深度 CUDA 兼容层」。你给的材料写「完全兼容 CUDA 及 OpenCL」，招股书部分段落确有「完全兼容」措辞，但更准确的口径是等效库 / 深度兼容：它并非英伟达 CUDA 的实现，提供的是等价编程接口，让既有代码迁移过来。这中间的距离取决于算子覆盖、框架版本与工具链成熟度 —— 招股书没给兼容覆盖率或迁移实测，所以「客户代码不必推倒重写」是厂商主张，不宜读成零成本无缝。

## 三、三代参数里，哪些不能当效率曲线读

| | Minsky I (2020) / Goldwasser I | Minsky II (2022) / Goldwasser II | Minsky III (2024→2025) / KS 系列 |
|---|---|---|---|
| INT8 | 256 TOPS | 512 TOPS | 560 TOPS |
| FP16 | 64 TFLOPS | 256 TFLOPS | 280 TFLOPS |
| FP32 | 16 TFLOPS | — | — |
| 内存 | 8–64 GB | 32–128 GB | 8–128 GB |
| 带宽 | 239 GB/s | 192 GB/s | 819.2 GB/s |
| 功耗 | 55 W | 95 W | 130 W |

按这些数字自己算一下：

- INT8 每瓦：4.65 → 5.39 → 4.31 TOPS/W；FP16 每瓦：1.16 → 2.69 → 2.15 TFLOPS/W。绝对算力逐代涨，但每瓦算力并不单调上升，III 代比 II 代低。这与「相同制程下比传统 GPU 更高效率」不矛盾（比较基准是传统 GPU，不是自家上一代），但说明代际数字不是架构效率曲线。
- 带宽 239 → 192 → 819.2 GB/s：II 代反而低于 I 代，III 代才数量级跃升。更像不同产品定位/内存配置的结果，也提示「依赖外部带宽」这个痛点是在 KS 系列才被重点解决。
- III 代不再标 FP32 峰值，宣传重心明显转向 AI 推理；Goldwasser 系列另称支持 FP32/TF32/BF16，那是产品线多精度能力，不等于每代都给 FP32 峰值。
- 时间线以招股书为准：正文写 2023 年升级 Minsky II / 推出 Goldwasser II、2025 年推出基于 Minsky III 的 KS 系列（另有处标 2024 升级 Minsky III）；你给的 2022/2024 属摘要口径。

## 四、架构来源：团队血统 + 产业源流

团队血统是第一条硬线索。 36 氪项目库记载：创始人李建文在 GPU 领域有二三十年从业经历，曾任图芯科技（Vivante，2004 年创立）副总裁，他负责的 GPU/GPGPU IP 产品曾卖给飞思卡尔、英特尔、Marvell、Google、三星、诺基亚等；招股书/券商资料也提到三位创始人出自图芯系。图芯是移动/嵌入式 GPU IP 供应商（后被芯原 VeriSilicon 收购）—— 这解释了两个设计取向：对面积/功耗极度敏感（嵌入式 GPU IP 出身），以及把可编程图形/计算 IP 与专用加速块做进同一颗 SoC 的工程习惯。王平 2022 年那句「核心 IP 全自研，架构、微架构、算术单元、SoC 架构每行代码自主编写」，是这支团队把 IP 授权经验转成自研产品路的自我陈述。

第二条是产业与学术源流，按时间排：

| 年份 | 来源 | 贡献了什么 |
|---|---|---|
| 2012–2014 | AMD HSA / HSA Foundation、hUMA、hQ（Kaveri APU） | CPU 与 GPU 共享统一虚拟地址空间、双向一致性、免显式拷贝；「把异构从板级拉进片内 + 统一编程模型」的早期产业尝试 |
| 2017 | Hennessy & Patterson「DSA 黄金时代」、Google TPU v1 | 领域专用架构的理论化；TPU 用 65536 个 8-bit MAC 的 MXU + 24MB Unified Buffer（SRAM 当寄存器） 证明「大片上缓冲 + 专用矩阵单元」能压过通用 GPU |
| 2017–2018 | NVIDIA Volta Tensor Core | 在 SIMT 的 SM 内加入专用张量核，FP16 乘、FP32 累加；A100 白皮书进一步写清「数据先经 L1→寄存器→shared memory 再喂 Tensor Core」的搬运链，以及用 L2 常驻 ping-pong buffer 避免写回 DRAM |
| 2018 起 | NVIDIA Jetson Xavier / Orin DLA（NVDLA） | GPU 旁挂固定功能推理核，增大本地缓冲以降低 DRAM 带宽；TensorRT 统一调度 GPU/DLA，`cuDLA` 把它收进同一 CUDA 编程模型 |
| 2020s | scratchpad 近存计算研究（如 ICPP 2024 统一 SPM 管理可减最多 80% 片外访存） | 为「软件管理片上内存 + 编译期分派」提供学术依据 |

所以 Minsky 属于把这些已有思路收敛到一颗面向企业 AI 的 GPGPU 里：HSA 的统一内存思想、TPU 的大片上缓冲、Volta 的 SIMT+张量共存、DLA 的固定功能卸载，各自取一块。招股书自称「首创片内异构」，更准确的说法是在中国企业 AI GPGPU 这个细分产品形态上的首创，不是体系结构原理层面的首创。

## 五、国外有没有「同架构」产品？

严格一一对应：没有。但把三件套拆开，每一件都有成熟对照物，最接近的是下面三条线的交汇处。

| 国外产品 | 与 Minsky 的三件套对照 | 关键差异 |
|---|---|---|
| NVIDIA Volta / Ampere / Blackwell（Tensor Core） | SIMT CUDA cores + 专用张量核 + 片上 L1/Shared Memory 层级；Blackwell/Thor 已是可配置统一 256KB L1+Shared Memory，第五代 Tensor Core 支持 INT8/FP8/FP6/FP4 | 张量核在每个 SM 内部，不是独立集群；CUDA 是原生生态；面向全场景训练+推理，功耗量级远高于 55–130W |
| Google TPU v1（及后续） | MXU 脉动阵列 + 24MB Unified Buffer 片上 SRAM | 放弃通用 SIMT 编程面，是纯 ASIC；不做 CUDA 兼容，靠 XLA/编译器 |
| NVIDIA Jetson Xavier / Orin（DLA） | GPU 与固定功能 DLA 同 SoC 并存，TensorRT 统一分派、支持 GPU fallback，Orin 的 DLA 2.0 增大本地缓冲降低 DRAM 带宽 | 这是最接近工程形态的一个：同片异构 + 软件栈分派 + 推理卸载。差别是 DLA 是 GPU 之外的独立核、编程面仍是 CUDA/TensorRT 原生，且面向嵌入式边缘 |
| AMD Kaveri APU / HSA | CPU+GPU 同片 + hUMA 统一内存 | 异构对象是 CPU 与图形 GPU，不含 AI 张量专用引擎，目标是通用计算而非 AI 推理能效 |

一句话定位：Minsky 更像「把 Jetson DLA 那种固定功能加速思路反向做进一颗 GPGPU，并用 CUDA 等效层把编程面补回来」。它和三件套本身都不新鲜；差异集中在三点：

1. 编程面选择：国外三条线里，只有 NVIDIA 系有 CUDA 原生生态；Minsky 用等效库去够这个生态，这是国产替代场景下的现实约束，也是它最大的持续成本。
2. 调度粒度：招股书强调「细粒度软硬件协同」「软件定义」，配合软件管理 SPM 与 xU 可扩展单元；对照 Volta 是硬件 SM 内耦合、TPU 是编译器静态排布、DLA 是 TensorRT 层分派。Minsky 把更多分派责任放到了自家软件栈。
3. 功耗/场景带：55W → 130W、智慧城市 / 工业质检 / 企业私有云 / 边缘推理，不是万卡训练集群。招股书里 2026 年前四个月企业私有云占收入 83.0%、KS 系列占 GPGPU 收入 82.9%，落的正是这段；对照 Volta/A100 是数据中心、TPU 是 Google 内部集群、DLA 是 Jetson 边缘。

## 六、取舍与边界（必须自己补上的部分）

- 固定功能硅的双刃剑：张量单元省电，但 AI 算子一变（新注意力结构、稀疏、FP8/FP4），它不像 SIMT 能靠软件兜住。Volta 之后的演进恰恰是不断给 Tensor Core 加新数据类型与稀疏支持；Minsky 的应对是 xU 扩展与软件栈迭代，招股书未给算子演进的兼容数据。
- CUDA 等效 ≠ 原生：生态兼容是持续工程，不是一次性声明；招股书未披露覆盖率或第三方迁移实测。
- 效率对比全是厂商口径：「相同制程节点下更高计算效率与密度」、2021 年演讲里「同工艺 3–10 倍计算效率」「40W 输出 128TOPS」都出自登临一方，招股书未给与具体 NVIDIA 型号的同负载第三方基准。
- 商业坐标要放回表里：按 2025 年收入计中国企业 AI GPGPU 市场第三、份额 1.0%，前两名合计约 95.4%（券商摘要口径）；公司是 18C 章未商业化公司，2023–2025 年累计亏损，2026 年前四个月经调整利润才转正。技术叙述别脱离这个坐标。
- 本文依据招股书与公开演讲，未拿到芯片或板卡实测，所有算力/带宽/功耗均为厂商披露值。

## 七、结论

把「CPU 架构」换回「GPGPU 架构」之后，这套东西其实很好概括：普通 GPU 是一种通用引擎 + 靠外部显存喂数据；ASIC 是一种专用引擎 + 生态锁死；Minsky 是把 SIMT 通用单元、张量专用单元、软件管理的片上内存塞进一颗芯片，靠软件栈按算子分派。

它的「来源」有两层：团队来自图芯（Vivante）的嵌入式 GPU IP 谱系，方法来自 2012 年以来 HSA、DSA/暗硅、TPU 统一缓冲、Volta Tensor Core、Jetson DLA 这条共同的技术史；它的「同类」是这几条线在同一颗 die 上的交汇，很难对应到某一款国外芯片。真正属于登临自己的选择，是在 55–130W 的企业边缘/私有云功耗带里，用 CUDA 等效层换迁移成本、用片内异构换能效 —— 这个取舍是否成立，最终要看工具链能不能跟上算子演进，而不是看 560 TOPS 那个数字。

## Sources

- 登临科技港交所招股书（9917.HK，2026-10-30）：<https://www.hkexnews.hk/listedco/listconews/sehk/2026/1030/2026103000024_c.pdf>
- 量子位《登临科技联合创始人王平：创新+自研"双核"驱动，GPU+赋能AI落地生根》（2022-07-25）：<https://www.qbitai.com/2022/07/36338.html>
- 机器之心/WAIC 2021 李建文演讲报道（2021-07-16）：<https://news.qq.com/rain/a/20210716A03IZJ00>
- 36氪项目库（创始团队图芯/Vivante 背景）：<https://pitchhub.36kr.com/project/1679647607902982>
- NVIDIA《Volta Tensor Core GPU Achieves New AI Performance Milestones》：<https://developer.nvidia.com/blog/tensor-core-ai-performance-milestones> ｜ A100 架构白皮书（PDF）：<https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf>
- Google Cloud《An in-depth look at Google's first TPU》：<https://cloud.google.com/blog/products/ai-machine-learning/an-in-depth-look-at-googles-first-tensor-processing-unit-tpu>
- NVIDIA DLA 开发者页：<https://developer.nvidia.com/deep-learning-accelerator> ｜ Jetson AGX Orin 技术简报（PDF）：<https://www.nvidia.com/content/dam/en-zz/Solutions/gtcf21/jetson-orin/nvidia-jetson-agx-orin-technical-brief.pdf>
- Ars Technica《AMD's heterogeneous Uniform Memory Access coming this year in Kaveri》(2013)：<https://arstechnica.com/information-technology/2013/04/amds-heterogeneous-uniform-memory-access-coming-this-year-in-kaveri>
- ICPP 2024《Scratchpad Memory Management for Deep Learning Accelerators》：<https://research.chalmers.se/publication/542648/file/542648_Fulltext.pdf>
