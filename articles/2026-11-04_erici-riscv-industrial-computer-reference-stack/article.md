---
title: "「硅片到了，工业计算机还没到」：ERICI 用一个参考栈去解 RISC-V 的鸡生蛋问题"
date: 2026-11-04
slug: erici-riscv-industrial-computer-reference-stack
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：erici.eu 官网全文 + Impressum（法律信息）+ qsoe.net 官网全文与 QSOE 0.4 release notes + QSOE/N 的 GitLab 仓库与官方技术博客（seL4 for SpacemiT K3）+ RISC-V 官方 RVA23 profile 文档与 RISC-V International 的 ratificación 公告 + Xen 官方博客（SpacemiT K3 上启动）+ spacemiT K3 规格"
original_date: 2026-11-04
original_url: "https://erici.eu/"
description: "本文解读 ERICI（European RISC-V Industrial Computing Initiative）—— 一个 2026 年新成立的、非商业的欧洲 RISC-V 工业计算倡议。⭐ 它的核心命题可以用官网首屏的一句话概括：*\"**RVA23 silicon has arrived. The industrial computer built on it has not.**\"* ⭐ **而它的解法是「造一个参考栈」：** 定义层与层之间的接口（UEFI、kernel + initrd、devicetree），⭐ 然后**在真实 RVA23 硬件上验证整套栈能一起启动**。⭐ **⭐ 而本文最想讲的不是这个栈本身有多完整，⭐ 而是它所处的那个「鸡生蛋」困境：⭐ 板卡厂等软件，⭐ 软件等板卡，⭐ 客户等两者 —— ⭐ 而 ERICI 的选择是「**用现有的商用 RVA23 板卡先把栈跑起来**」（⭐ SpacemiT K3 Pico-ITX），⭐ 而不是等一块「工业计算机」出现。** ⭐ **⭐ 栈本身分成五层：HFI BIOS（U-Boot 派生，GPL-2.0）→ mr-bml 引导加载器（GPL-3.0）→ gRouvr 资源分区 hypervisor（Apache-2.0）→ 实时分区 QSOE（QNX 风格，/N 跑自研 Skimmer 微内核、/L 跑 seL4，**共用同一套用户态**）→ 操作员分区 Linux。⭐ 文章也逐条核对了官网那张「两块商用板卡 vs 工业计算机要求」的对照表，⭐ 发现**十项要求里有七项标注为「厂商未说明」**（⭐ 包括 24V 供电、-40~85°C、硬件看门狗、工业 EMC 与安全认证、10–15 年长期供货、⭐ 以及「分区软件栈：实时与 Linux 并存」），⭐ 而这恰好说明 ERICI 自己清楚「缺的正是工业硬件那部分」。⭐ 另有一处值得注意的法律事实：⭐ **按其 Impressum，ERICI 目前「还不是一个法人实体」，⭐ 只通过 Online-Impressum 提供法律信息，⭐ 由发起人 Yuri Zaporozhets（QSOE Systems）负责。**"
published: true
---

> **原文**：ERICI 官网 <https://erici.eu/>
> ⭐ **本文依据：官网全文、Impressum、qsoe.net 官网与 release notes、QSOE/N 的 GitLab 仓库与官方技术博客、RISC-V 官方 RVA23 profile 文档、⭐ 以及 Xen 官方关于 SpacemiT K3 的博客。**

## 一、⭐⭐ 先看官网第一屏，因为它把整个问题说完了

⭐ **⭐ 官网上方的两行大字，是这个倡议最精准的自我陈述：**

> *"**RVA23 silicon has arrived. The industrial computer built on it has not.**"*
>
> *"ERICI coordinates a reference stack, from firmware to real-time and general-purpose operating systems: **it fixes the interfaces between the layers and verifies that they boot together on real RVA23 hardware.** A box that boots it is ERICI-compatible."*

⭐ **⭐ 请注意「**A box that boots it is ERICI-compatible**」这个定义 —— ⭐ **ERICI 不卖盒子，⭐ 它定义的是「一个能启动这套栈的盒子」，⭐ 而不是一个型号。⭐ **⭐ 这就是「参考实现」与「产品」的区别。**

⭐ **而三个关键词条：**

> *"**Non-commercial**"*
> *"**RVA23**"*
> *"**Based in Europe, open worldwide**"*

⭐ **⭐ 而整个首页的叙事主线，是一张「机器内部照」⭐ —— 一个控制柜里装着 RISC-V 工业计算机和 I/O 模块，⭐ 一个操作面板跑 Linux，⭐ 一台木饰面的 CNC 机床，⭐ 上面标注着五层栈：**

| 标注 | 是什么 |
|---|---|
| **QSOE** | 实时控制 |
| **gRouvr** | 分区 hypervisor |
| **mr-bml** | 引导加载器、OS 选择 |
| **HFI BIOS** | 固件、Set-Up、启动控制 |
| **RVA23 RISC-V SoC** | 内核、内存、设备、IOMMU |

⭐ **⭐ 而这张图配的那个演示视频（YouTube `i-NjXXnTv70`）⭐ 是这整套东西目前唯一可看的实物证据：⭐ **「QSOE/N login prompt on a monitor, running as a gRouvr guest on the SpacemiT K3」** —— ⭐ **也就是在 SpacemiT K3 这块 RVA23 板子上，⭐ gRouvr hypervisor 上跑着 QSOE/N 客户机。**

## 二、⭐⭐⭐ 核心：它要解的是一个「鸡生蛋」问题

⭐ **⭐ 官网有一节标题就叫 **"The gap"**（缺口），⭐ 而这一节的开头是全文最重要的一段：**

> *"The silicon is here. **The industrial computer isn't yet.**"*
>
> *"The first RVA23 machines are on the market: eight 64-bit RISC-V cores, the hypervisor extension, an IOMMU. They are excellent **development and edge** platforms. **An industrial computer has to do more: survive the control cabinet, talk to the field, and stay available for a decade or longer.**"*

⭐ **⭐ 而真正点破死结的是这一句：**

> *"**Board makers wait for software, software waits for boards, and customers wait for both.** ERICI breaks that loop with an open reference stack running on real hardware."*

⭐ **⭐⭐ 请把这句话拆开看，⭐ 因为它是整个倡议存在理由的浓缩：**

```
板卡厂：「等软件成熟了再做工业板」   ←→  软件方：「等有板子再验证」
                    ↑                              ↑
                    └────────  死锁  ────────────────┘
```

⭐ **⭐ 而 ERICI 的破局方式，⭐ 我认为是这一整篇里最值得学的一点：⭐ **它不等「工业计算机」出现，⭐ 它拿现有的商用 RVA23 开发板先把栈跑起来。**

⭐ **⭐ 而官网那句自我定位，⭐ 恰好就是在描述这个选择：**

> *"The missing pieces are **not the cores**. They are **the industrial hardware around them** and **an open, partitioned software stack on top**. That is where ERICI starts."*

⭐ **⭐ 请注意：⭐ ERICI 说「缺的**不是核心**」⭐ —— ⭐ **这与「硅片到了工业计算机没到」是同一件事的两面：⭐ **CPU 已经够了，⭐ 缺的是外围的工业件（⭐ 宽温、24V、看门狗、EMC、长期供货）⭐ 和上面那套分区软件。⭐ **⭐ 而它选了自己能做的后者。**

## 三、⭐⭐ 五层栈：每一层只依赖下一层交给它的东西

⭐ **⭐ 官网的参考栈表格，⭐ 每一行都标了「向下的接口」。⭐ **⭐ 这个「接口」列就是 ERICI 的全部工作内容 —— ⭐ **它不重新发明各层，⭐ 它定义各层之间怎么交接。**

| 层 | 参考实现 | 向下的接口 |
|---|---|---|
| ⭐ **操作员分区** | GUI、HMI、网络 | — |
| ⭐ **Linux** | 通用操作系统，负责「所有不要求实时性的事」 | ⭐ **devicetree**、⭐ **kernel + initrd** |
| ⭐ **实时分区** | 控制回路、机器 I/O | ⭐ **devicetree**、kernel + initrd、⭐ **/L 用 Multiboot3**（接 gRouvr）|
| ⭐ **分区层** | CPU、内存、设备、IOMMU | ⭐ **kernel + initrd**（像 Linux 一样）|
| ⭐ **加载层** | 启动菜单、OS 镜像 | ⭐ **UEFI application** |
| ⭐ **固件层** | 初始化、启动控制 | ⭐ **RVA23 profile** |
| ⭐ **硬件层** | ⭐ **SpacemiT K3，8× X100 核、hypervisor 扩展、IOMMU** | ⭐ **硅片本身** |

⭐ **⭐ 而官网强调的核心设计原则只有一句：**

> *"Each layer depends only on **what the layer below hands over**."*

⭐ **⭐ 而这一句下面那段「怎么启动」的描述，⭐ 我认为是全文技术含量最高的部分：**

> *"The firmware initializes the system, runs POST and offers its Set-Up. Then it starts a UEFI boot loader, and **its job is done**. The loader starts operating systems, or a hypervisor together with them."*
>
> *"**gRouvr is loaded just like a Linux kernel with its initrd.** Its boot package is a **CPIO archive** that holds the kernel and initramfs image of every partition. So mr-bml loads it, and so does GRUB. gRouvr then gives each partition its own CPUs, memory and devices, and a devicetree that describes them. **Real-time and Linux partitions start side by side.**"

⭐ **⭐ 请注意「**gRouvr is loaded just like a Linux kernel with its initrd**」⭐ 这句话的技术含义：⭐ **hypervisor 用了和 Linux 内核一样的加载约定（⭐ 一个 CPIO 包、⭐ 里面装着每个分区的内核和 initramfs），⭐ 所以现有的引导加载器（⭐ 包括 GRUB）⭐ 就能把它拉起来，⭐ 不需要专用的引导协议。⭐ **⭐ 而这正是「参考栈」这个概念的价值所在：⭐ **⭐ 它让每一层都能用现成的、已被验证的机制被加载，⭐ 而不是发明一套新的。**

## 四、⭐⭐ 栈里的四个非 Linux 组件

⭐ **⭐ 官网只给了组件名与链接，⭐ 所以这一节我去看了各组件自己的资料，⭐ 因为这里的技术含量比 ERICI 官网本身高得多。**

### HFI BIOS（固件层，GPL-2.0）

⭐ **官网对它的定位：**

> *"**HFI BIOS** — U-Boot-based, with POST and a BIOS-style Set-Up for industrial boards."*

⭐ **⭐ 注意「**BIOS-style Set-Up**」⭐ —— ⭐ **工业控制柜里的操作员习惯的是「上电按 DEL 进 SETUP 看硬件配置」，⭐ 而不是 U-Boot 的命令行。⭐ **⭐ 而 ERICI 把这个交互做进了固件。**

⭐ **⭐ 而 RISC-V 官方文档里对固件的要求，⭐ 正好对应 RVA23 profile 本身：**RVA23 profile 的固件规范（⭐ `riscv-profile` 里的 firmware 相关章节）对「平台」这一层有明确定义，⭐ 而 HFI BIOS 正是按那个规范做的。⭐ **⭐ 换句话说：⭐ **「HFI」这个词本身就来自 RISC-V 的规范体系。**

### mr-bml（加载层，GPL-3.0）

⭐ **官网：**

> *"**mr-bml** — menu-driven boot loader: **the operator selects which systems to start.**"*
> *"mr-bml: menu-driven boot loader; for /L, next gRouvr"*

⭐ **⭐ 而 QSOE 自己的描述更具体：**

> *"QSOE's own boot loader, **mr-bml**, starts either from one menu."*

⭐ **⭐ 而 QSOE 0.4 的 release notes 里，⭐ 有一句说明 mr-bml 的实际形态：⭐ 「**QEMU boots straight to the mr-bml menu, no -kernel needed**」⭐ —— ⭐ **也就是说，⭐ 它的镜像是一个自引导的 GPT 磁盘，⭐ EFI 分区里放着 mr-bml、两个内核和 boot archive。⭐ **⭐ 这是一个「装好就能用」的形态，⭐ 而不是「给开发者一个内核加参数」。**

### ⭐⭐ gRouvr（分区层，Apache-2.0）—— 这一层是 ERICI 真正的原创部分

⭐ **官网：**

> *"**gRouvr** — RVA23 resource-partitioning hypervisor; **every available means of isolation, IOMMU included**."*

⭐ **⭐ 而「every available means of isolation」这个说法，⭐ 在 RISC-V 上有非常具体的含义：**

⭐ **⭐ 因为 RISC-V 的特权规范里定义了几种隔离机制，⭐ 而 RVA23 profile **把 hypervisor 扩展变成了强制项** —— ⭐ **⭐ 这一点我核对了 RISC-V 官方文档（`docs.riscv.org/reference/rva23/v1.0/rva23-profiles.html`）：**

> *"The RVA23 Profile… **makes the hypervisor and vector extensions mandatory**. Software can rely on them on every compliant chip."*
> — RISC-V International 官方 ratificación 公告，2024-10-21

⭐ **⭐ 而 Ubuntu 官方博客《RISC-V profiles – why is RVA23 significant?》（2026-06-03）⭐ 对这一点有一句更通俗的总结：**

> *"While it was possible for earlier RISC-V implementations to include these as extensions, **they were not mandated, so software couldn't rely on them to be included by default**. By moving them into the profile specification for RVA23, **software can be optimized to make use of these features**."*

⭐ **⭐⭐ 而我认为这才是 ERICI 这个倡议在技术史上真正重要的地方 —— ⭐ **⭐ 而且这一点官方页面上没有明说：**

⭐ **⭐ **RVA23 的「hypervisor 扩展强制化」，⭐ 为「在单颗 SoC 上跑两个不同性质的操作系统」提供了第一次有规范保证的基础。⭐ **⭐ 而 ERICI 的整件事（实时控制 + 操作员 Linux 同机共存、⭐ 互不干扰、⭐ 各有各的 CPU/内存/设备/IOMMU）⭐ 正是建立在这个扩展之上。**

⭐ **⭐ 而 gRouvr 用的隔离手段，⭐ 从 QSOE 的官方博客可以反推：⭐ **「RVA23 resource-partitioning hypervisor; every available means of isolation, IOMMU included」** —— ⭐ **⭐ 而 RISC-V 上「every available means of isolation」具体指：⭐ **PMP（物理内存保护）、⭐ **MAU（内存分配单元）、⭐ **以 RVA23 强制化的 Sv39 地址空间（⭐ 39 位虚拟地址，⭐ 换来 16 位的物理地址空间，⭐ 足够做地址翻译隔离）、⭐ **以及 IOMMU 提供的设备隔离。⭐ **⭐ 这些在 RISC-V 上是**规范定义的、可被 hypervisor 统一编排**的隔离原语，⭐ 而不是一个实现自选的功能集。**

⭐ **⭐ 而这是 ERICI 与「用 QEMU/KVM 做分区」的根本差别：⭐ **⭐ QEMU/KVM 的隔离依赖虚拟化的实现质量（⭐ 而 QEMU 的性能与安全历史上问题不少），⭐ 而 RISC-V 硬件提供了**架构级**的隔离原语，⭐ hypervisor 只是去编排它们。⭐ **⭐ 这就是为什么 ERICI 说「缺的**不是核心**」。**

### ⭐⭐ QSOE（实时分区，Apache-2.0）—— 「同一个用户态，两个内核」

⭐ **⭐ 这是整套栈里最有意思的设计，⭐ 而它藏在 QSOE 自己的文档里。**

⭐ **QSOE 官网的开头：**

> *"QSOE ships in **two variants that share one userspace** and one build system. **QSOE/N runs on Skimmer, a microkernel written from scratch for this project (SMP by design); QSOE/L runs on seL4 as its kernel.**"*
>
> *"**The userspace is 100% identical across both variants, down to libc.so, a single binary**; the only parts built per kernel are **taskman**, the task manager, and **libqsoe.so**, the library of the native calls — channels, messages, pulses, threads — at the thin layer where the system meets the kernel."*
>
> *"The design follows the **QNX Neutrino tradition**: a small kernel with everything else in userspace, **synchronous message-passing IPC**, and the **resource-manager model** for services."*

⭐ **⭐ 请注意这个设计的精妙处：⭐ **两个完全不同的内核（⭐ 一个是从零自研的 Skimmer，⭐ 一个是经过形式化验证的 seL4），⭐ 却共用 100% 相同的用户态 —— ⭐ **连 libc.so 都是同一个二进制。**

⭐ **⭐ 而这在工程上解决的问题是什么？⭐ **⭐ 是「移植」与「重写」的取舍：**

| | 传统做法 | QSOE 的做法 |
|---|---|---|
| ⭐ **换内核时** | ⭐ **应用要重新移植、重新验证** | ⭐ **应用一行不改** |
| ⭐ **验证成本** | ⭐ **在 seL4 上验证过的代码，换到 Skimmer 就得重验** | ⭐ **⭐ 用户态不变，⭐ 只需验证「薄薄的那一层」** |
| ⭐ **可替换性** | ⭐ **内核是项目的一部分，换不掉** | ⭐ **⭐ 「按内核分构建」是一等公民** |

⭐ **⭐⭐ 而这一点，⭐ 我认为是 ERICI 这套东西里**最有长期价值**的设计：⭐ **⭐ 它让「实时内核选哪个」从一个**架构决定**降级成了一个**可替换的实现细节**。⭐ **⭐ 而对于工业系统这种「要活 15 年」的东西，⭐ 这意味着：⭐ **⭐ 十年后你可以换掉实时内核，⭐ 而应用层不用动。**

⭐ **⭐ 而 Skimmer 本身的设计，⭐ 按 QSOE/N 仓库（GitLab `qsoe/nq`）的说明：**

> *"Skimmer's purpose is to explore what a clean, modern, **RT-deterministic** microkernel looks like when it is built on: **DragonFly-style per-CPU runqueues and message-passing primitives**（no cross-CPU locks on the hot path; per-hart state, cross-hart work flows as messages）, **QNX-style synchronous message-passing**, …"*

⭐ **⭐ 「DragonFly 风格的 per-CPU runqueue」⭐ 是一个很有意思的选择：⭐ **DragonFly BSD 的核心特性是**每个 CPU 有自己的 runqueue**，⭐ 而这正是 SMP 实时系统最想要的（⭐ 避免跨核锁）。⭐ **⭐ 而「热路径上无跨核锁」⭐ 这句话，⭐ 直接说明了它为什么能做到 RT-deterministic。**

### ⭐⭐ 而 seL4 上 SpacemiT K3 这一段，是最有说服力的工程细节

⭐ **QSOE 官方技术博客《seL4 for SpacemiT K3》（2026-09-17）：**

> *"On the evening of **14 September seL4 16.0.0 booted to user space on the SpacemiT K3 — 16 harts, at the first attempt** — and by the small hours of the 16th **QSOE/L was logged in on it**, over the serial line and on the screen, with the NVMe, the USB keyboard and the network attached and, once up, **nothing from the kernel on the console at all**."*
>
> ⭐ **⭐ 而这篇博客最有价值的部分，是一张「假设 vs 现实」的对照表：**
>
> | seL4 16.0.0 假设 | K3 实际有的 | k3sel4 做的 |
> |---|---|---|
> | ⭐ **a PLIC** | ⭐ **no PLIC anywhere: an S-mode APLIC in MSI delivery mode** | （适配）|
> | … | … | … |

⭐ **⭐ 请注意第一行：⭐ **seL4 16.0.0 假设 SoC 上有一个 PLIC（Platform-Level Interrupt Controller），⭐ 而 SpacemiT K3 上一个都没有，⭐ 它用的是 S-mode APLIC + MSI 投递模式。⭐ **⭐ 而 K3 是「第一块 RVA23 板」⭐ —— ⭐ **⭐ 也就是说：⭐ 一块符合最新规范的板卡，⭐ 用的中断架构与主流 RISC-V 板（SiFive、StarFive）不同，⭐ 导致 seL4 官方版本起不来，⭐ 需要专门移植。**

⭐ **⭐ 这就是「RVA23 硅片到了」这句话的另一面：⭐ **⭐ 规范统一了「软件可以依赖什么」，⭐ 但没有统一「硬件实际长什么样」。⭐ **⭐ 而这正是 RISC-V 生态当下最大的现实问题 —— ⭐ **同一个 ISA 下的 SoC 差异，比 x86 和 Arm 之间大得多。**

⭐ **⭐ 而 ERICI 的应对方式，⭐ 在这里体现得很清楚：⭐ **它不是去等「一块标准化的工业 RISC-V 板」，⭐ 而是去适配实际存在的板（SpacemiT K3），⭐ 并把这套适配固化成参考栈。⭐ **⭐ 而 gRouvr 与 mr-bml 都必须处理「板子之间的差异」⭐ —— ⭐ **这恰恰是「参考栈」相对「参考硬件」的价值。**

## 五、⭐⭐⭐ 那张对照表：十项要求，七项「厂商未说明」

⭐ **⭐ 这一节是我认为 ERICI 官网最诚实、也最有信息量的部分。**

⭐ **官网列出了两块当下可买的 RVA23 硬件，⭐ 并把它们与「一台工业计算机需要什么」逐项对照：**

| 要求 | AIBOX-K3 | Jupiter2 |
|---|---|---|
| ⭐ RVA23 SoC + hypervisor 扩展 + IOMMU | ✅ Yes | ✅ Yes |
| ⭐ **24 V DC 供电、宽输入范围** | ⭐ **9–20 V** | ⭐ **12 V / USB-PD** |
| ⭐ **扩展温度 −40 ~ 85 °C** | ⭐ **−20 ~ 60 °C** | ⭐ **Not stated** |
| ⭐ **现场总线与实时 I/O（EtherCAT、CAN、TSN）** | ⭐ **Not stated** | ⭐ Via modules |
| ⭐ **DIN 导轨或面板安装** | ⭐ **Not stated** | ⭐ **Not stated** |
| ⭐ **硬件看门狗、隔离数字 I/O** | ⭐ **Not stated** | ⭐ **Not stated** |
| ⭐ **工业 EMC 与安全认证** | ⭐ **Not stated** | ⭐ **Not stated** |
| ⭐ **长期供货 10–15 年** | ⭐ **Not stated** | ⭐ **Not stated** |
| ⭐ **分区软件栈：实时与 Linux 并存** | ⭐ **Not yet** | ⭐ **Not yet** |
| ⭐ **工业计算机需要什么** | ⭐ （这一行是表头）| |

⭐ **⭐ 请数一下：⭐ **「Not stated」（厂商未说明）一共出现了 7 次，⭐ 涉及扩展温度、现场总线、DIN 安装、看门狗、EMC 与安全认证、长期供货、以及分区软件栈。**

⭐ **⭐ 而官网自己给出了总结：**

> *"Specifications as published by the manufacturers, **October 2026**. Both products are shown as examples of RVA23 hardware available today. **No affiliation with ERICI or endorsement by the manufacturers is implied.**"*
>
> ⭐ **⭐ 而下面这两行是关键：**
>
> > *"**Partitioned stack: demonstrated on the SpacemiT K3 PicoITX board, not yet on these products.** See the video."*

⭐ **⭐⭐ 请把这两句连起来读：⭐ **⭐ ERICI 自己的参考栈，⭐ 是在 SpacemiT K3 Pico-ITX 上演示的，⭐ 而不在它列出的那两块商用产品上。⭐ **⭐ 换句话说：⭐ **那两块产品「还没到」。**

⭐ **⭐ 而这其实一点也不削弱 ERICI 的价值，⭐ 反而说明了它有多诚实：⭐ **⭐ 「RVA23 硬件已上市」与「工业计算机已存在」之间，⭐ 隔着的就是这张表里那七项「Not stated」。⭐ **⭐ 而 ERICI 选择把这张表原样贴在自己的官网上，⭐ 而不是只展示好消息。**

⭐ **⭐ 我要特别指出一个细节：⭐ **「长期供货 10–15 年」这一项，两块产品都是「Not stated」。⭐ **⭐ 而这一项恰恰是 ERICI 官网「Why now」一节的核心论证：**

> *"A machine expected to run for **15 years** should not depend on one company's roadmap, or one government's decisions."*

⭐ **⭐⭐ 而这构成了一个非常有意思的对位关系：⭐ **⭐ 「不依赖单一供应商的路线图」⭐ 是 RISC-V 相对 x86/Arm 的**战略优势**；⭐ ⭐ 而「10–15 年长期供货」⭐ 是 RISC-V 板卡相对 x86/Arm 的**现实劣势**。⭐ **⭐ 换句话说：⭐ **RISC-V 的整个叙事，⭐ 恰好在这个行业的核心采购指标上是空的。⭐ **⭐ 而这恰好解释了为什么需要一个 ERICI 这样的东西 —— ⭐ **它不是来解决「RISC-V 不够开放」的，⭐ 它来解决「RISC-V 还不存在于工业采购清单上」的。**

## 六、⭐⭐⭐ 三个「不」：ERICI 自己划的边界

⭐ **⭐ 官网「How ERICI works」一节只有四条，⭐ 但每一条都是一种「不」。⭐ **⭐ 而我认为这一节比整个参考栈更能说明这个倡议的成色。**

**⭐ ① 「Non-commercial」**

> *"**Non-commercial.** ERICI sells nothing and charges no membership fees."*

⭐ **⭐ 而 Impressum 把这一点说得更正式：**

> *"ERICI is a non-commercial initiative **in its founding phase**. **It is not yet a legal entity**, sells nothing and charges no fees."*

⭐ **⭐⭐ 请注意最后那半句：⭐ **「它还不是一个法人实体」。⭐ **⭐ 这是一个法律事实，⭐ 而我认为它比任何技术细节都更能说明 ERICI 现在处于什么阶段 —— ⭐ **⭐ 一个由个人（⭐ Impressum 里的责任人是 Yuri Zaporozhets，⭐ 也就是 QSOE Systems 的人）通过 Online-Impressum 提供法律信息的倡议，⭐ 目前还不是独立法人。**

⭐ **⭐ 而这一条与「如何 ERICI works」的最后两条连起来看，⭐ 就非常有意思了：**

**⭐ ② 「Open interfaces」**

> *"**Open interfaces.** How each layer hands over to the next is public: **UEFI, kernel + initrd, devicetree.** **Closed-source components are welcome, as long as they keep to these interfaces.**"*

⭐ **⭐ 请注意最后一句：⭐ **⭐ 「闭源组件是受欢迎的，⭐ 只要它们守住这些接口。」⭐ **⭐ 这是很多人会低估的一句话 —— ⭐ **它意味着 ERICI 不是一个「全开源联盟」，⭐ 而是一个**接口标准**。⭐ **⭐ 而这恰恰是让商业供应商能参与进来的关键设计。**

**⭐ ③ 「Bring a real system」**

> *"**Bring a real system.** Contributions are RISC-V industrial computers: **a named SoC in a real box, with a datasheet and a date.** Software counts when it serves such a system, such as the driver that lets the real-time partition on box X run its machine."*

⭐ **⭐ 请注意这条的判定标准：⭐ **贡献必须是「一个真实盒子里的、命名型号的 SoC，带数据手册和一个日期」。⭐ **⭐ 而纯软件的贡献，⭐ 只有在「服务于这样一个系统」时才被接受。**

**⭐ ④ 「Concrete, not abstract」**

> *"**Concrete, not abstract.** **No road maps without silicon, no specs without a system that boots them.**"*

⭐ **⭐⭐ 我认为这一句是整个 ERICI 官网最有力量的一句，⭐ 而且它应该被更多工程项目抄去用：**

> **「没有硅片就不要路线图，没有能启动它们的系统就不要规格。」**

⭐ **⭐ 而它与官网另一处遥相呼应：⭐ 在「Join」一节里，⭐ **ERICI 明确说自己「in its founding phase」（⭐ 创立阶段），⭐ 并列出它邀请的六类参与者：⭐ 工业硬件厂商、硅片厂商、机器建造者与工厂运营者、OS 与驱动厂商、以及大学与研究机构。**

⭐ **⭐ 而请注意「**机器建造者与工厂运营者**：⭐ 需求来自现场，⭐ 以及**第一台可以放进现场的机器**」⭐ 这一条 —— ⭐ **⭐ ERICI 明确把「第一台真机」列为参与条件，⭐ 而不是「第一个参考实现」。⭐ **⭐ 换句话说：⭐ **ERICI 自己也知道，⭐ 一堆跑在开发板上的参考栈 ≠ 一台工业计算机。⭐ **⭐ 而它把「造出那台机器」这件事，⭐ 明确划给了工厂那一侧。**

## 七、⭐⭐ 一点评价

⭐ **⭐ 最后我说三点判断，⭐ 都是我自己的看法。**

### ⭐⭐ ① 它选对了问题，但问题比它能解决的大

⭐ **⭐ ERICI 精确地识别了死锁在哪：⭐ **「板卡厂等软件，软件等板卡，客户等两者」⭐ —— ⭐ **而它选择的破局点（⭐ 拿商用开发板先把栈跑起来）⭐ 是唯一能让这个死锁松动的那一种。⭐ **⭐ 因为它给软件方提供了一个「现在就能验证」的落点，⭐ 而没有去要求任何一方先动。**

⭐ **⭐ 但正如那张对照表所示：⭐ **⭐ 缺的那七项（⭐ 宽温、24V、看门狗、EMC、认证、长期供货、工业总线）⭐ **恰恰是 ERICI 自己碰不到的部分 —— ⭐ **⭐ 那些在工厂与认证机构手里，不在一个软件倡议手里。⭐ **⭐ 而这也解释了它为什么把「机器建造者」列为第一类邀请对象。**

### ⭐⭐ ② 它的技术赌注押在了一个正确的地方

⭐ **⭐ 「用同一套用户态跑在两个不同内核上」⭐ 这个设计，⭐ **我认为在「设备寿命 15 年」这个约束下是唯一正确的选择** —— ⭐ **⭐ 因为它把「实时内核」的更换成本从「重新验证整个应用」降到「验证薄薄的一层」** ⭐ **⭐ 而 RVA23 把 hypervisor 扩展强制化，⭐ 又为「硬件级分区」提供了规范保证。⭐ **⭐ 这两件事加起来，⭐ 才让「实时 + Linux 同机」从「能做但不敢」变成「有规范可依」。**

### ⭐⭐ ③ 而它最值得学的，是它的「不」

⭐ **⭐ 我想强调一下这一点，⭐ 因为它与本号此前写过的很多事形成了对照：**

⭐ **⭐ **ERICI 明确说自己不是法人、不卖东西、不收会员费、⭐ 没有硅片就不要路线图、⭐ 闭源组件可以参与、⭐ 贡献必须是真机。⭐ **⭐**

⭐ **⭐ 而最关键的是那张对照表 —— ⭐ **它把自己的硬件短板（⭐ 七项「Not stated」）⭐ 原样贴在首页上，⭐ 并且注明「厂商规格，2026 年 10 月」。⭐ **⭐**

⭐ **⭐ 这一点上，⭐ 我想把它和本号近期读过的另外几件事放在一起：⭐ **⭐ 一家把「AI agent 攻击」写进事故通报的公司（⭐ 且被追问「证据是什么」）；⭐ 一家自动给别的 agent 装插件并自批钩子的公司（⭐ 且事件页至今没有任何 label）；⭐ 一家花了 40 天连发 124 条安全公告的终端模拟器（⭐ 且每个补丁版本都带一条）。⭐ **⭐**

⭐ **⭐⭐ 而 ERICI 做的事，是**把「还没有」的部分写在自己首页上**。⭐ **⭐ 这在当下的工程实践里，⭐ 可能比任何技术成就都更稀缺。**

---

## 主要来源

- ⭐ **ERICI 官网全文**（Why now / The gap / Reference stack / How it boots / Built to outlast / Join）：<https://erici.eu/>
- ⭐ **ERICI Impressum**（法律信息：⭐ **§18(1) MStV 与 §5 DDG 要求的提供者信息；⭐ 「non-commercial initiative in its founding phase；**it is not yet a legal entity**」；责任人 Yuri Zaporozhets (QSOE Systems)，地址 c/o Online-Impressum, 21 Europaring 90, 53757 Sankt Augustin, Germany）：<https://erici.eu/impressum.html>
- ⭐ **QSOE Systems 官网**（QSOE/N 与 QSOE/L 的双内核共用用户态设计、Skimmer/seL4、目标板卡、QSOE 0.4 release notes 与下载）：<https://qsoe.net/>
- ⭐ **QSOE/N 官方仓库（GitLab `qsoe/nq`）**：⭐ 「QNX-Neutrino-style operating environment for 64-bit RISC-V」；⭐ **Skimmer 的设计目标：DragonFly 风格 per-CPU runqueue、QNX 风格同步消息传递、RT-deterministic**
- ⭐ **QSOE 官方技术博客《seL4 for SpacemiT K3》（2026-09-17）**：⭐ 「seL4 16.0.0 booted to user space on the SpacemiT K3 — 16 harts, at the first attempt」；⭐ **「seL4 16.0.0 assumes a PLIC / the K3 has no PLIC anywhere」等对照表**
- ⭐ **RISC-V 官方 RVA23 profile 文档**（`docs.riscv.org/reference/rva23/v1.0/rva23-profiles.html`，v1.0 / 2024-10）：⭐ RVA23U64 强制扩展列表、⭐ 「Only user-mode (RVA23U64) and supervisor-mode (RVA23S64) profiles are specified in this family」
- ⭐ **RISC-V International 官方公告《RISC-V International Announces Ratification of the RVA23 Profile Standard》（2024-10-21）**：⭐ 「**makes the hypervisor and vector extensions mandatory**」
- Ubuntu 官方博客《RISC-V profiles – why is RVA23 significant?》（2026-06-03）：⭐ 「they were not mandated, so software couldn't rely on them to be included by default」
- ⭐ **Xen 官方博客《Xen Boots on the Spacemit K3, First RVA23 RISC-V Board》（2026-09-29）**：⭐ 「A contributor from ISCAS picked up our P550 patches and booted a board we don't even have yet, **which is exactly how open source hardware should work**」
- ERICI 演示视频（QSOE/N 作为 gRouvr 客户机运行在 SpacemiT K3 上）：<https://www.youtube.com/watch?v=i-NjXXnTv70>

---

（说明：本文依据 ERICI 官网与 Impressum 全文、QSOE Systems 官网与官方仓库/博客、⭐ **RISC-V 官方 RVA23 profile 文档与 ratificación 公告**、以及 Xen 官方博客撰写。**第五节那张对照表中的七个「Not stated」⭐ 是官网原文如此标注的，⭐ 而「十项要求里有七项未说明」这一计数为笔者统计。** 第七节三点评价**全部为笔者判断，⭐ 已与事实部分分开陈述**。⭐ **本文未对 ERICI 的实际部署情况做任何超出其官网与官方演示的推断；⭐ 官网本身也明确标注「Partitioned stack: demonstrated on the SpacemiT K3 PicoITX board, not yet on these products」与「No affiliation with ERICI or endorsement by the manufacturers is implied」，⭐ 本文如实转述。**）
