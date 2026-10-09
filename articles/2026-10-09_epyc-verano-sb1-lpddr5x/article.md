---
title: "一个散热器页面泄露的 EPYC Verano：72 核不难，24 通道 LPDDR5X 才是真信号"
date: 2026-10-09
slug: epyc-verano-sb1-lpddr5x
tags: [AMD, EPYC, Verano, Zen 6, Venice, SB1, SP7, SOCAMM2, LPDDR5X, JEDEC, 服务器CPU, AI主机, 内存带宽, 半导体, 译文]
category: 硬件
author: FreeLAMP.com
original_source: "Tom's Hardware / Dynatron 产品页 / JEDEC / ServeTheHome"
original_author: "Tom's Hardware；Dynatron 产品页（经 InstLatX64 发现）"
original_date: 2026-10-08
original_url: "https://www.tomshardware.com/pc-components/cpus/amds-epyc-verano-ai-host-cpu-will-reportedly-use-a-special-sb1-socket-zen-6-chip-pairs-72-cores-with-a-24-channel-lpddr5x-memory-subsystem"
description: "散热器厂商 Dynatron 的产品页上出现「支持 Socket SB1 上的 AMD EPYC Verano」，据此曝出 AMD 面向 AI 主机的 EPYC 9006 Verano：最高 72 个 Zen 6 核、5 GHz、24 通道 LPDDR5X、可更换 SOCAMM2 模块、全新 SB1 插槽，2027 下半年上市。本文先严格区分「据报」与「已确认」，再讲这条线索的真正含义：这是 EPYC 首次用 LPDDR 做主内存，而 24 通道 LPDDR5X 的带宽量级已经开始逼近 HBM 的地界。"
published: true
---

> 原文：[AMD's EPYC Verano AI host CPU will reportedly use a special SB1 socket](https://www.tomshardware.com/pc-components/cpus/amds-epyc-verano-ai-host-cpu-will-reportedly-use-a-special-sb1-socket-zen-6-chip-pairs-72-cores-with-a-24-channel-lpddr5x-memory-subsystem)（Tom's Hardware，2026-10-08）
> 补充来源：[ServeTheHome 对 EPYC 9006 Venice 的报道](https://www.servethehome.com/amd-takes-the-lid-off-of-next-gen-epyc-9006-venice-as-zen-6-comes-to-servers)、AMD EPYC 9006 系列产品页、[JEDEC JESD328（SOCAMM2）](https://www.jedec.org/standards-documents/docs/jesd328)
> 本文为**解读**。第二节明确区分「据报」与「已确认」，第三节的带宽计算标注为本文计算。

## 一句话结论

这条消息的源头**不是 AMD，是散热器厂商 Dynatron 的产品页**：它列出了「支持 Socket SB1 上的 AMD EPYC Verano」，由 InstLatX64 发现。据报的规格是 **72 个 Zen 6 核、5 GHz、24 通道 LPDDR5X、可更换 SOCAMM2 模块、全新 SB1 插槽，2027 下半年上市**。72 核本身不稀奇，**真正值得注意的信号是 24 通道 LPDDR5X**：这是 EPYC 第一次用 LPDDR 做主内存，而按 9.6 Gb/s 的 LPDDR5X 链路速率算，24 通道的带宽量级已经开始逼近 HBM 的地界。

## 一、先把信源强度摆清楚

这条新闻最该先说的不是规格，是**它的证据从哪里来**，因为决定了你能拿它做什么。

| 环节 | 内容 |
|---|---|
| 原始线索 | 散热器厂商 **Dynatron 的产品页**列出「AMD EPYC Verano on Socket SB1」 |
| 发现者 | **InstLatX64** |
| 报道方 | Tom's Hardware，**标题自带 reportedly** |
| AMD 官方 | **未发布该产品，未确认上述任何参数** |

**几处需要谨慎对待的细节，原文自己也标了：**

- **SB1 里的「B」可能指 BGA 封装**（焊在板上），但原文明确说这是**「基于名字的猜测，没有任何官方依据」**；
- **那个散热器的参数可能只是占位值**。Dynatron 的 SB1-4U-ACTIVE 标注为「TBD」，**最大功耗标成 TBD**，而它的尺寸 **128.05 × 106.6 × 130.7 mm 与 Dynatron 给 SP7 的 J26 散热器完全相同**。尺寸一模一样这件事，更像是还没定稿时沿用旧参数，而不是巧合；
- **产品名未定**。产品页上写的是「SB1-4U-ACTIVE (TBD)」。

所以合理的读法是：**「AMD 在 2027 年有一款面向 AI 主机的 EPYC，会用一个与现有服务器插槽不同的新插槽」这件事可信度较高**（散热器厂商通常比公众更早拿到插槽规格，否则无法备料）；**具体到核心数、通道数、频率这些数字，应当视为待验证**。

## 二、据报的规格

| 项目 | 内容 |
|---|---|
| 产品 | EPYC 9006 系列 **Verano**，定位 **AI 主机 CPU** |
| 核心 | 最高 **72 个 Zen 6 核** |
| 频率 | 最高 **5 GHz** |
| 内存 | **24 通道 LPDDR5X** |
| 内存形态 | 可更换的 **SOCAMM2** 模块 |
| 插槽 | 全新 **SB1**，**比 SP7 / SP8 更小** |
| 散热 | 需要与现有 EPYC 不同的散热方案 |
| Dynatron 散热器 | SB1-4U-Active，128.05 × 106.6 × 130.7 mm，**均热板 + 热管 + 双滚珠轴承风扇，最高 6,000 RPM**，功耗标 TBD |
| 上市时间 | **2027 下半年** |

## 三、真正值得看的信号：24 通道 LPDDR5X 意味着什么

把传闻剥掉，这条线索里有一个**方向性判断**是有独立证据支持的。

### 证据一：这不是空穴来风，AMD 的路线图里本来就有它

ServeTheHome 在 2026 年 9 月底实机报道 EPYC 9006 Venice 时就写了：

> 除了最新的 Zen 6 CPU 架构，AMD 还带来了新的 I/O die、**大幅加快的内存支持**、全新的插槽（所有型号都换）、3D 堆叠 L3 缓存的回归，以及**在 2027 年晚些时候推出的一款面向 AI、带 LPDDR 支持的芯片，这是 AMD EPYC 处理器的首次**。

**「带 LPDDR 支持」和「2027 年晚些时候」两个特征，与 Verano 的传闻完全吻合。** 这不是巧合，而是两条独立来源指向同一件事。

### 证据二：AMD 自己的产品页已经在用「AI Host Node」这个框架

AMD 的 EPYC 9006 系列页面上，把产品按用途分了档，其中明确出现 **「Host Node for AI」**，底下挂着 **「AMD EPYC 9006 LP Server CPU」**。同一页面上还有一句关于 Venice 的定位是「高核心密度与领先性能，帮助高效扩展 agentic 工作负载、虚拟机和 **AI host nodes**」。

**`LP` 强烈暗示 Low Power**，这与 Verano 的 LPDDR5X 描述方向一致。**所以 Verano 很可能就是这款 EPYC 9006 LP**（这是我从 AMD 官方页面推的推断，不是官方确认）。

另外注意 AMD 在 9006 系列里还并列了 `SP7` 和 `SP8` 两个插槽，而 Verano 据报用第三套 **SB1**。**一个产品线里给 AI 主机单独切一套插槽，说明它的物理形态（内存走线、供电、散热）与通用服务器确实不同**，这也解释了为什么 Dynatron 需要单独做散热器。

### 证据三：SOCAMM2 标准刚定下来，时间点对得上

Verano 要用可更换的 LPDDR5X 模块，这个模块类别是有正式标准的：

- **JEDEC 在 2025 年 10 月预告了 JESD328（SOCAMM2）标准**，明确说是「**专为数据中心 AI 应用开发的低矮型 LPDRAM 模块**」，用于 **AI CPU 服务器**与加速计算平台；
- **JESD328 于 2026 年 6 月正式发布**（Version 1.00），定义为「在数据中心、AI 服务器等系统中作为主内存使用」；
- 标准预期的数据率上限是 **9.6 Gb/s per pin**（在平台信号完整性允许的前提下）；
- **Rambus 在 2026 年 4 月就出货了 SOCAMM2 芯片组**，含 SPD Hub（负责模块识别、配置与遥测）和 12A/3A 电压调节器。

**为什么这件事重要**：SOCAMM2 解决了 LPDDR 最大的商用障碍。过去 LPDDR 要么焊死在板上（省电但不可维护、不可扩展容量），要么用非标准形态。SOCAMM2 把它做成**可拔插、可维护、带遥测的服务器模块，同时保留 LPDDR 的低电压信号与能效**，而且**平躺在主板上以最大化信号完整性**。

### 粗算一下带宽（本文计算，依赖假设，仅供参考）

这是我认为最该算的一笔账，但必须先把假设说清楚：

- 若按 **9.6 Gb/s** 的 LPDDR5X 链路速率（JEDEC 给出的上限）；
- **通道位宽按 32 位算**：24 通道 × 9.6 Gb/s × 32 bit ÷ 8 ≈ **0.92 TB/s**；
- **通道位宽按 64 位算**：≈ **1.8 TB/s**。

**对照 EPYC Turin 的 12 通道 DDR5-6400**（64 位通道）：12 × 6400 MT/s × 8 Byte ≈ **614 GB/s**。

也就是说，24 通道 LPDDR5X 相对 Turin 的 12 通道 DDR5，**带宽大约是 1.5 倍到 3 倍，具体取决于通道位宽怎么算**。**这个量级已经开始跨过 DDR5 的地界、向 HBM 的低端靠拢**——而这正是「AI 主机」这个词的物理含义：**在 GPU 旁边那台负责供数据、跑 agent 调度、做预处理和后处理的 CPU，它的瓶颈往往不在算力，而在喂得饱不饱。**

**必须强调**：以上是建立在「24 通道 + 9.6 Gb/s」两个传闻数字上的估算，**通道位宽也没有官方口径**。如果实际通道位宽是 32 位，那就是接近 1 TB/s 的量级；如果是 64 位，才到 1.8 TB/s。**这笔账的意义在于量级判断，不在于具体数字。**

## 四、LPDDR 进服务器，动机是什么

把上面的证据串起来，能看出 AMD 这条路线在解决什么问题。

**传统服务器内存（DDR5 RDIMM/MRDIMM）的强项是容量与可维护性，弱项是能效**。它靠 RCD、PMIC 那一整套模块化设计来保证信号完整性，代价是每比特的功耗与成本都更高。**LPDDR 的强项恰好相反**：低电压、低功耗、单位带宽的能效好，但传统形态不可维护。

**当「AI 主机 CPU」成为一类独立产品时，需求结构变了**：

- **它不需要 1TB 以上的巨量内存**。ServeTheHome 的报道里提到一个很实在的观察：**很多工作负载根本不需要接近 1TB 的内存，但如果你想在双路系统上跑 32 通道的 12800 MRDIMM，那个容量似乎就是最低门槛**——「哪怕每个插槽只给 2GB 也会很受欢迎」；
- **它需要的是带宽/功耗比**。在机架功率预算固定的前提下，把内存功耗降下来，可以直接换成更多 GPU 或更高密度；
- **它需要可维护性**（这正好是 SOCAMM2 解决的问题）。

**所以 Verano 的定位可以概括成一句话**：**在一块不需要超大内存容量、但极度在乎带宽密度和能效的位置上，用 LPDDR5X 换掉 DDR5。** 而 JEDEC 为这个场景专门立了 SOCAMM2 标准，Rambus 已经在卖配套芯片组，AMD 的产品页上已经有「AI Host Node CPU」这一档——**产业链的三段都已经就位了。**

## 五、对从业者的实际含义

**如果你想在 2027 年前后采购或规划 AI 主机节点**，这条消息给出的几个前置提醒是有用的：

1. **插槽和散热要重新规划**。SB1 比 SP7/SP8 **更小**（据报），且需要**不同散热方案**。对已经在用 SP5/SP6 机架和散热模组的数据中心，这意味着**不能沿用现有平台规划**。散热器尺寸与 SP7 的 J26 相同这件事，也提示最终功耗规格**可能尚未冻结**；
2. **内存不再是你熟悉的采购项**。如果 SOCAMM2 真的进入这个平台，那你买的将是一种**新形态的内存模块**，需要关注供应情况、模块容量阶梯、以及 SPD/遥测在你现有监控体系里的接入方式（Rambus 的芯片组已把 SPD Hub 和温度传感做进去了）；
3. **别把这条消息当采购依据，但要当路线图信号**。规格未官方确认、产品名带 TBD、上市时间在 2027 下半年。**合理的动作是把它记进平台生命周期规划，而不是现在做容量或机型决策**；
4. **值得观察的反向压力**。LPDDR 做主内存意味着**内存容量上限和可扩展性会有取舍**，而你今天的很多虚拟化、内存数据库、缓存类工作负载恰恰吃容量。**同一个机架里可能需要「容量型」和「带宽型」两类节点**，这会反过来影响你未来的调度与编排策略（按内存规格给节点打标签、给工作负载做分级调度）。

## 六、我的判断

把传闻和已确认的分开之后，这条消息里**最有价值的部分不是那 72 个核**。

**72 核 5 GHz 的 Zen 6 本身没有惊喜**：Venice 的 dense 配置据 ServeTheHome 报道可以有比高频率配置**多达 2.66 倍的核心数**（对比 Turin 时代 dense 相对高频率的 1.5 倍优势），72 核放在这个背景下完全在预期之内。

**真正有信息量的是内存子系统的形态变化**，因为它同时说明三件事：

- **AMD 在为「AI 宿主 CPU」定义一个新的产品类别**，而不是把通用服务器 CPU 调一调就拿过来用（新插槽、新散热、新内存形态、独立的产品页分类）；
- **内存墙正在被正面处理**。当 GPU 侧的 HBM 已经堆到很高的量级，主机侧的 12 通道 DDR5（约 614 GB/s）会成为数据供应的瓶颈。把 24 通道 LPDDR5X 放到主机上，是把「供得上吗」这个问题的答案从「将就」改成「够用」；
- **JEDEC 与上游芯片厂商已经为这条路铺好了标准**。这不是某一家公司的私有方案，而是有 JESD328、有 Rambus 芯片组、有 SPD 遥测规范的开放路线。**开放标准意味着这条路会有第二家、第三家跟上来**，也意味着它会进入你的采购清单。

**最后留一句谨慎**：散热器厂商的产品页是比「知情人士透露」更硬的线索（因为涉及备料和模具），但它仍然是**间接证据**。等 AMD 官方公布时，值得重点核对三个数字：**SOCAMM2 的实际通道位宽、内存容量上限、以及 SB1 到底是 BGA 还是可插拔**。这三个数字会决定它究竟是一款「带宽特化的 AI 主机 CPU」，还是「把 LPDDR 硬塞进服务器的过渡产物」。

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 信源 | Dynatron 产品页列出「AMD EPYC Verano on Socket SB1」，InstLatX64 发现，Tom's Hardware 报道（标 reportedly） |
| 产品 | EPYC 9006 系列 Verano，定位 AI 主机 CPU；**AMD 未官方确认** |
| 据报规格 | 最高 **72 核 Zen 6**、最高 **5 GHz**、**24 通道 LPDDR5X**、可更换 **SOCAMM2** |
| 插槽 | 全新 **SB1**，比 SP7/SP8 更小；「B」可能指 BGA（**原文明确说是猜测**） |
| ⚠️ 存疑细节 | 散热器最大功耗标 TBD；尺寸与 SP7 的 J26 完全相同，参数可能是占位值 |
| 上市 | **2027 下半年**（据报） |
| SOCAMM2 标准 | JEDEC **JESD328**，2025 年 10 月预告、**2026 年 6 月正式发布**；LPDDR5X 数据率上限 **9.6 Gb/s** |
| 配套芯片 | Rambus SOCAMM2 芯片组 2026 年 4 月出货，含 SPD Hub 与 12A/3A 稳压器 |
| 带宽估算（本文计算） | 24 通道 @9.6 Gb/s：按 32 位算约 **0.92 TB/s**，按 64 位算约 **1.8 TB/s**；对照 Turin 12 通道 DDR5-6400 约 **614 GB/s** |
| 旁证一 | ServeTheHome 报道 Venice 时就提到 2027 年晚些推出「带 LPDDR 支持」的芯片，为 EPYC 首次 |
| 旁证二 | AMD 官方 EPYC 9006 页面已有「Host Node for AI」分类与「EPYC 9006 LP Server CPU」 |

## 延伸阅读

- [Tom's Hardware 原文（标 reportedly）](https://www.tomshardware.com/pc-components/cpus/amds-epyc-verano-ai-host-cpu-will-reportedly-use-a-special-sb1-socket-zen-6-chip-pairs-72-cores-with-a-24-channel-lpddr5x-memory-subsystem)
- [ServeTheHome：AMD Takes the Lid off of Next-Gen EPYC 9006 Venice](https://www.servethehome.com/amd-takes-the-lid-off-of-next-gen-epyc-9006-venice-as-zen-6-comes-to-servers)
- [JEDEC JESD328：SOCAMM2 标准](https://www.jedec.org/standards-documents/docs/jesd328)
- [Rambus：面向 AI 服务器的 SOCAMM2 芯片组](https://www.rambus.com/rambus-enables-power-efficient-ai-platforms-with-socamm2-server-module-chipset)
- [本站：华为 Peerium：新闻稿说「突破」冯·诺依曼，论文说「延续」冯·诺依曼](/articles/2026-10-08_huawei-peerium-lingqu-hc2026/)
- [本站：逼近 10 秒的 Linux 内核构建：双路 EPYC 9575F + Kbuild 并行化补丁](/articles/2026-09-26_near-10-sec-kernel-build/)
