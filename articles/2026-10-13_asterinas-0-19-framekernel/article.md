---
title: "Asterinas 0.19：用 Rust 重构内核的另一种思路，是「不减少地址空间，只减少 unsafe」"
date: 2026-10-13
slug: asterinas-0-19-framekernel
tags: [Asterinas, Rust, 操作系统, 内核, framekernel, 微内核, 宏内核, 内存安全, unsafe, OSTD, DRM, AArch64, Kata Containers, TDX, hypervisor, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "LWN.net / Asterinas 官方发布公告 / The Asterinas Book"
original_author: "LWN（Jonathan Corbet）；Hongliang Tian（Asterinas 社区）"
original_date: 2026-10-13
original_url: "https://lwn.net/Articles/1100055/"
description: "Asterinas 0.19.0 发布，这是一个用 Rust 从零构建的操作系统内核。它采用自创的 framekernel 架构：整个 OS 仍在同一个地址空间里（像宏内核），但被划分为两个部分，只有享有特权的 Framework 允许使用 Rust 的 unsafe 特性，而其余部分包括所有外设驱动都必须是安全 Rust。这让「整个内核的内存安全」被归约为那个最小框架的安全。本次发布的七个重点包括：能跑 Xorg 与 OpenGL 游戏的新 DRM 子系统、AArch64 成为第四个架构、作为 Kata 式容器 guest 内核的加固、OSTD 的 hypervisor 支持（约 2000 行 unsafe 支撑起用安全 Rust 写的完整 hypervisor）、类型系统强制约束的设备模型、一个基于编码规范的 AI 代码审查 skill，以及自举成功。"
published: true
---

> 来源：[LWN：Asterinas 0.19.0 released](https://lwn.net/Articles/1100055/)（2026-10-13，Jonathan Corbet）、[Asterinas 官方发布公告](https://asterinas.github.io/2026/10/13/announcing-asterinas-0.19.0.html)（作者 Hongliang Tian）、[The Asterinas Book](https://asterinas.github.io/book/)
> 数据说明：仓库指标（stars、forks、创建时间）为笔者于 2026-10-13 通过 GitHub API 实测。
> 本文为**译文 + 解读**。第一节对「framekernel 在解什么问题」的拆解、第四节的判断是笔者补充的部分。

## 一句话结论

**Asterinas 是一个用 Rust 从零构建的操作系统内核，0.19.0 于 2026 年 10 月发布**。它采用的架构叫 **framekernel**，而我认为它的思路值得从这个角度理解：**它没有试图通过「拆分地址空间」来获得安全性（那是微内核的路），而是让整个 OS 留在同一个地址空间里（像宏内核），同时把「允许使用 `unsafe`」的权限限制在一个很小的框架内。**

**官方对这种架构的表述是**：

> **宏内核的速度，微内核的安全性。**

**而它的核心承诺是可度量的**：**在 Asterinas 里，所有 unsafe Rust 代码都被限制在 `ostd` 里，而内核的其余部分，包括所有外设的驱动，全部由安全 Rust 代码组成。**

## 一、framekernel 到底在解什么问题

**先说清它面对的两难。** 一个操作系统的内核架构，在安全与性能之间长期是一个二选一：

| 架构 | 地址空间 | 性能 | 安全边界 |
|---|---|---|---|
| **宏内核**（Linux） | **单一地址空间** | **快**（组件间是函数调用） | **任何一处内存破坏都可能影响全内核** |
| **微内核**（seL4、QNX） | **组件各自独立地址空间** | **慢**（组件间要走 IPC） | **单组件失陷的影响被隔离** |

**微内核的安全性来自隔离，而隔离的代价是 IPC 开销。** 而**宏内核的性能来自「不用 IPC」，代价是「没有隔离」。**

**framekernel 的做法是引入一个第三个维度**：**不改地址空间，改「谁能用 unsafe」。**

**官方描述的分区方式是**：

> **在 framekernel 架构里，整个 OS 驻留在同一个地址空间（像宏内核），并且要求用 Rust 编写。但有一个转折：内核被划分成两半，享有特权的 Framework（类似微内核）和没有特权的 Services。** **只有享有特权的 Framework 允许使用 Rust 的 unsafe 特性，而没有特权的 Services 必须完全用安全 Rust 编写。**
>
> **整个内核的内存安全性被归约到 Framework 的安全性上，而 Framework 是一个最小、表达力强且稳固的基础。** **因为驻留在同一地址空间，内核的其余部分能以最高效的方式与 Framework 通信。**

**我需要把这个论证的强度说清楚，因为它是一个有条件的论证**：

- **它成立的前提是「安全 Rust 真的是安全的」**，这依赖编译器与语言保证，是整个论证的地基；
- **它成立的前提是「`unsafe` 确实被框住了」**：**这是一个可以用工具度量的事实**（见下节）；
- **它不解决逻辑漏洞**：**一个用安全 Rust 写成的驱动仍然可能把数据写错**，它只是不会造成内存破坏。

**所以 framekernel 的准确表述不是「这个内核是安全的」，而是「这个内核的内存破坏风险被归约到了一个小的、可审查的范围内」。** 而**这个归约有一个重要的实际收益**：**它把「审什么东西」这件事从「整个内核」缩小到了「一个框架」。**

## 二、这次的规模数据，以及那个可度量的承诺

**发布公告开头给了两个里程碑**：

> **已经有超过 100 人向 Asterinas 仓库贡献过代码，代码库超过了 25 万行，其中约 20 万行是 Rust。** **在这些贡献者中，55 人参与了这次发布，其中 31 人是第一次参与。**

**而仓库的实测指标是**：**创建于 2022-05-17，4,946 stars，390 forks，341 个未关闭 issue，主语言 Rust，MPL-2.0 许可**。**发布节奏是每两到三个月一个版本**（v0.18.0 在 2026-06-03，v0.18.1 在 08-18，v0.19.0 在 10-12）。

**而关于那个「unsafe 被框住」的承诺，本次发布给了一个具体的数字**（在虚拟化那一节）：

> **所有需要 `unsafe` 的代码都住在 OSTD 的虚拟化模块里，今天大约 2000 行**，**所以它之上的一切，直到一个完整的 hypervisor，都可以是安全 Rust。**

**我认为「2000 行」这个数字是整篇里最有价值的信息之一。** 因为它把一个通常只能定性讨论的安全主张，**变成了一个可以追踪、可以比较、可以对它设目标的数字**。

**这带来一个我之前在别处讨论过的判断标准**：**衡量一个安全设计，不看它宣称保护了什么，而看它把需要被信任的代码缩小到了多少。** **「unsafe 行数」就是一个这样的指标**：**它不完美（unsafe 的风险还取决于它做了什么，而不只是行数），但它可度量、可追踪、且随每次提交变化。**

**而对一个内核项目来说，这个指标还有一个特殊的价值**：**它给「新贡献者能安全地改哪部分」划了界**。**在上面写代码的人是安全 Rust，审阅者不需要判断指针生命周期；而改动 OSTD 就需要另一套审查标准。** **这个区分对本次发布里「31 位首次贡献者」这件事是有直接帮助的。**

## 三、本次发布的七个重点

**发布公告列了七项，我按「对读者的实际意义」重新组织**。

### ① 图形：Xorg 与 OpenGL 游戏跑起来了

**这是最直观的一项**。**Asterinas NixOS 现在能在标准的 `modesetting` 驱动上跑 Xorg，上面再叠 Mesa 的软件 OpenGL**，**而不再依赖传统的 framebuffer（fbdev）接口**。

**背后是一个新的 DRM（Direct Rendering Manager）子系统**：新的 `aster-drm` 组件提供 **DRM 核心、`/dev/dri` 下的设备节点、GEM dumb buffers（CPU 绘制的帧缓冲，用户空间可以 `mmap`）、以及配置显示的 KMS（内核模式设定）对象**。

**为什么这件事重要**：**DRM 是现代 Linux 图形栈赖以建立的核内接口**，**能跑 Xorg + OpenGL 意味着这个内核已经能承载一个真实的图形用户空间**，而不只是一个 framebuffer 上的终端。**而 demo 视频里跑的是两个 3D 游戏**（用的是软件渲染，不是 GPU 加速）。

### ② AArch64 成为第四个架构，Arm 机器也能当开发主机

**Asterinas 现在支持四个 CPU 架构**：**x86-64、RISC-V、LoongArch，以及新加入的 AArch64**。**官方对这次移植的定性是「最小但可用」**（minimal but usable）：

> **在 QEMU 的 `virt` 机器上，它带起了 GICv3 中断控制器、通用定时器、PL031 RTC、PL011 UART 和 virtio-mmio 设备，并运行 BusyBox shell，包含 vDSO。**

**AArch64 以「Tier 2 平台」身份进入，CI 覆盖仍在增长。**

**而同样值得注意的是「Arm 作为开发主机」这件事**：**Docker 镜像现在同时发布 `linux/arm64` 与 `linux/amd64`**，**新的 Nix 开发 shell 支持 `aarch64-linux`**，**所以一台 Arm 笔记本或服务器可以构建并运行这个内核，而不需要一台 x86 机器**。

**这一条的实际意义容易被低估**：**一个内核项目能不能在 Arm 上开发和测试，直接决定了有多少 Arm 开发者会参与。** 而对做 Arm 平台的人来说，**「能在自己的机器上构建和跑」是参与的入门条件。**

### ③ 安全容器：作为 Kata 式 VM 的 guest 内核

**这一项我认为是 Asterinas 最有商业说服力的方向。** 官方论证很直接：

> **Asterinas 很适合做基于 VM 的容器（例如 Kata Containers 和 Confidential Containers）的 guest 内核。** **一个内存安全的 guest 内核从沙箱里移除了一整类可被利用的 bug。**

**这个论证的逻辑是**：**Kata 这类方案的隔离依赖一个「轻量 VM」**，**而那个 VM 里跑的 guest 内核通常是完整 Linux**：**也就是说，沙箱的可信计算基（TCB）里包含一个大型 C 内核。** **如果那个内核换成内存安全的，沙箱的攻击面就被显著缩小。**

**而本次发布做的四件事，每一件都是「补齐 guest 内核的必需能力」**：

| 改动 | 为什么容器需要它 |
|---|---|
| **重写 overlayfs** | 容器镜像是层叠的，overlayfs 把多层呈现为单一文件系统。**新实现让它在 xfstests（标准 Linux 文件系统测试套件）里通过的用例翻倍** |
| **mount propagation 与新的 mount API** | 挂载现在可以是 shared / slave / private / unbindable；**基于 fd 的 `fsopen` 系列系统调用可用**。**容器运行时和较新的 systemd 都用这两个机制来搭建沙箱的挂载** |
| **virtio-fs 成熟** | **该驱动新增 `mmap`、`O_DIRECT`、重命名、符号链接与更快的多页 I/O**，**且 xfstests 现在会在 CI 里跑它** |
| **PVH 引导与 Firecracker** | **通过 PVH（QEMU、Cloud Hypervisor、Firecracker 使用的直接引导协议）启动**，**并可作为 Firecracker microVM 的 guest 内核运行** |
| **更快的 TDX 引导** | **在 Intel TDX guest 里，每一页内存在内核能用它之前都必须先被 accept。** **Asterinas 现在把这个工作分散到所有 vCPU 上，而不是在一个 vCPU 上做**，**显著加快了 TDX 上的引导** |

**把这五项放在一起看，会发现它们都指向同一个目标**：**让 Asterinas 成为一个「可以被容器运行时直接使用」的 guest 内核**。而**其中「xfstests 通过用例翻倍」和「xfstests 现在在 CI 里跑 virtio-fs」这两条，是少见的、可核对的成熟度信号**：**它比「支持 virtio-fs」这种表述有信息量得多。**

### ④ 虚拟化：OSTD 里的 hypervisor 支持

**这一项是本次发布里架构上最讲究的部分**，因为它明确划分了「机制」与「策略」：

> **[RFC-0003](https://asterinas.github.io/book/rfcs/0003-hypervisor-support.html) 定了设计。OSTD 拥有机制：虚拟化硬件状态、二级地址转换和 guest-host 切换。内核拥有策略：VM 与 vCPU 生命周期、内存槽、中断控制器、设备模拟，以及最终一个兼容 KVM 的 `/dev/kvm`。** **所有需要 `unsafe` 的代码都住在 OSTD 的虚拟化模块里，今天大约 2000 行**，**所以它之上的一切，直到一个完整的 hypervisor，都可以是安全 Rust。**

**而它给出的动机对比很值得引用**：

> **像 Xen 这样的裸机（Type 1）hypervisor 保持自己的核心很小，但依赖一个完整的 OS（通常是 dom0 里的 Linux）来提供驱动和管理。** **Linux + KVM 很方便，但把一个大 C 内核放进了每一个 VM 的可信基。**

**这正好是我在上面第三节里说的那个问题**：**虚拟化的隔离强度，取决于 hypervisor 本身有多大、由什么语言写成。** **Asterinas 的目标不是做一个更快的 hypervisor，而是做一个「能放进 TCB 而不心虚」的 hypervisor 基础。**

**而本次交付的是 Intel VMX 的基础**：**VMX 生命周期、VMCS、基于 EPT 的 guest 内存、guest CPU 状态、以及把每次 VM exit 返回给调用者的 guest 执行**。**而 The Book 里给了一个很直观的验收标准**：

> **The Book 展示了如何用这些 API 在约 100 行安全 Rust 里写一个最小 hypervisor。**

**我去看了那份示例**：**它跑一个 16 位汇编的 Hello World guest，guest 循环把字符通过 `out` 指令写到 COM1**。**而支撑它的是三个 OSTD 抽象**：`GuestPhysMemSpace`（用 EPT 把 guest 物理地址映射到 OSTD 管理的内存帧）、`GuestContext`（访问 guest CPU 状态）、`GuestMode`（用前两者运行 guest）。

**「100 行安全 Rust 写出一个能跑 guest 的 hypervisor」这个演示是有说服力的**，因为它把一个通常需要大量 `unsafe` 的工作，压缩成了三个抽象加一段策略代码。

### ⑤ 驱动：一个用类型系统强制约束的设备模型

**官方的论证起手很实在**：

> **一个成熟内核里的大部分代码是设备驱动，所以内核架构必须在处理设备这件事上可扩展。** **用户空间也在意：systemd、udev 以及 `lsblk` 这类工具是从 `/sys` 和 `/dev` 了解存在什么硬件的。**

**本次发布带入了设备模型的核心**：新的 `aster-device` 组件，**全部用安全 Rust 写成**，**是 Linux driver core 的 Rust 原生对应物**。**它把总线、类、驱动、设备定义为有类型的抽象，于是类型系统强制了 Linux 靠约定来强制的东西**：

| 抽象 | 类型系统的约束 |
|---|---|
| **总线与驱动** | **一个 `Driver<B>` 只能注册到总线 `B` 上**，**它的 `on_probe` 收到的是 `BusDevice<B>`，可以解引用到该总线自己的设备类型** |
| **类与类设备** | **`ClassDevice<C>` 把它的类带在类型里**，**所以 `ClassObserver<C>` 只会听到类 `C` 的设备**。**一个扫描新磁盘分区的块设备类观察者，永远不会被交给一个终端** |
| **属性** | **sysfs 属性是一个 `Attr<D>`，声明在它所属的设备类型 `D` 上**，**回调收到的是 `&D`**。**一个类的属性无法挂到另一个类的设备上，也没有回调需要向下转型一个泛型设备指针** |

**最后那句「没有回调需要向下转型一个泛型设备指针」是我认为最实际的一点。** **因为「向下转型」正是 C 内核里错误最常见的来源之一**（转错了类型，而编译器无法发现）。**把它从「靠约定」变成「类型不允许」，等于把一整类 bug 变成了编译错误。**

**而注册一个设备仍然是一次调用**：**模型把它匹配到驱动并 probe，正确的条目出现在 `/sys/` 下，设备节点出现在 `/dev` 里**（借助新的 devtmpfs）。

### ⑥ AI 代码审查：一个基于项目规范的 skill

**这一节的开头两句我认为是整篇公告里最锋利的话**：

> **代理让代码变得便宜。人类审阅才是留下来成为瓶颈的那一环。**

**为了缓解这个瓶颈，本次发布带了一个 `aster-code-review` skill**，**让编码代理去审查一个 Git 变更或一组文件**。**而它要回答的问题被定义得很准**：

> **`aster-code-review` skill 试图回答一个问题：怎么让 AI 审查得像一个维护者？**

**而它把维护者的判断分成两类，并分别处理**：

> **维护者做客观判断，那些明确的 bug；也做主观判断：这个改动符合项目的约定吗？** **两个特性让这个 skill 两者都能做**：
>
> **① 基于规范。** **每一个主观判断都引用 Coding Guidelines**：**这次发布把规范围绕五个审阅者角色重组成了 81 条，并给了稳定的短名**。**skill 为每个角色跑一遍，并试图在保留每条评论之前先反驳它。**
>
> **② 针对基准优化。** **一套 58 个审查问题、138 个预期缺陷的测试集，几乎全部从 Asterinas 自己的历史中挖掘，用来度量召回率。每一次漏检都会驱动对规范或 skill 的改动。**

**我认为这一节里有三个可以推广的做法**：

- **「每个主观判断都要引用一条规范」** 解决的是 AI 审查最常见的问题：**给出听起来合理但无法追溯的意见**。**要求引用，等于把意见变成可审计的**；
- **「先试图反驳每条评论，再决定保留」** 是一个具体的降噪机制。**AI 审查的另一个常见问题是意见太多、真假混杂**，而**这个步骤把「先说出口」改成「先自己否一遍」**；
- **用「58 个问题 / 138 个预期缺陷」这样的基准来度量召回率，并且让每次漏检都变成规范或 skill 的改动**：**这把「AI 审查好不好用」从一个主观评价变成了一个可以迭代的指标**。**而「缺陷从项目自己的历史里挖」这个取材方式尤其聪明**：**它保证测试集里的问题都是真实发生过的类型。**

**而我也想指出这一节的定位**：**它不是在说「AI 能替代维护者」，而是在说「维护者这个瓶颈需要用工具缓解」。** **官方的措辞是「让代码变便宜的是代理，留下来成为瓶颈的是人类审阅」**：**这个区分恰好对应了我前几天写过的那场讨论**：**当补丁量因 AI 而暴增时，真正的约束在审阅带宽，而不在生成能力。**

### ⑦ 自举：Asterinas 构建 Asterinas

> **能构建自己是操作系统的一个成人礼，而 Asterinas 0.19.0 通过了它。**

**步骤是**：**在 VM 里启动 Asterinas NixOS → 在里面克隆仓库 → 进入 Nix 开发 shell → 运行 `make kernel` → 在一个嵌套的 QEMU VM 里启动新构建的内核**。

**而官方对这件事的价值的说明我认为是最该引用的一句**：

> **Nix、Cargo、rustc 和 QEMU 一路都在 Asterinas 上运行，这使得一次自举构建成为这个内核被施压过的最大的真实负载之一。**

**「自举是最大的真实负载之一」这个说法很准确。** **自举的价值不在于「能编译自己」这个仪式本身，而在于它把一个大型、真实的软件构建过程压到了被测内核上**：**而这正好是我在别处反复见到的那条判断：真实的负载会暴露你在测试里根本想不到的问题。**

**同版本还新增了 Nix flake**（作为 Docker 的替代），**工具链、QEMU 与固件都在 Cachix 上预构建**，**装了 Nix 之后三条命令就能从新克隆到启动内核**：`nix develop`、`make kernel`、`make run_kernel`。**加上支持 `aarch64-linux`，这意味着在 Arm 开发机上也能走同一条路径。**

## 四、我的判断

**第一，framekernel 是一个把「安全」变成「可度量预算」的架构选择，这是它最有价值的地方。** **宏内核与微内核的争论持续了几十年，而争论的焦点一直是「隔离 vs 性能」。** **framekernel 换了一个轴**：**它不减少地址空间，而是减少「需要被信任的代码」。** **而它的好处是这一步可以被量化**：**「OSTD 的虚拟化模块约 2000 行 unsafe」是一个可以追踪、可以对它设目标的数字。**

**我认为这个可度量性是关键**：**安全设计最常见的失败模式是「宣称了一个无法验证的属性」**。**而「unsafe 收敛在一个模块里，且这个模块有 N 行」是一个任何人可以自己核对的陈述**（`unsafe_code = "deny"` 之类的机制可以强制它）。

**第二，本次发布里我认为最能说明成熟度的不是图形，而是那几处「用测试套件说话」的地方。** **「overlayfs 在 xfstests 里通过的用例翻倍」**、**「xfstests 现在在 CI 里跑 virtio-fs」**：**这两条比任何功能列表都有信息量**，**因为它们引用的是一个外部的、标准的测试套件，而不是自己的达标声明。**

**这个判断标准值得复用**：**当一个项目说「我们支持 X」时，要看它是否引用了第三方标准测试；说「我们改进了 X」时，要看它是否给出了可对比的基线。**

**第三，那个 AI 代码审查 skill 值得单独记，因为它把一个通用难题具体化了。** **「代理让代码变便宜，人类审阅成为瓶颈」** 是目前所有被 AI 加速的开源项目共同面对的状况。**而 Asterinas 给了一个完整的答案结构**：**把规范拆成可引用的条目（81 条、有稳定短名）→ 让每个主观判断引用一条 → 先反驳再保留 → 用从自身历史挖出的基准（58 问题 / 138 缺陷）度量召回 → 每次漏检回写规范。**

**这一套里我认为最聪明的两点是**：**「引用规范」让意见变得可审计**（AI 审查最大问题是无法追溯），**「从项目自己的历史挖测试集」保证了测试集里的问题是真实发生过的类型**（很多自建基准的通病是脱离实际）。

**第四，关于它离「生产级替代 Linux」还有多远，我倾向于保持谨慎。** **官方定位是「生产级 Linux 替代品」，而这个目标的门槛不在内核能不能跑起来，而在生态的另一侧**：**驱动覆盖、文件系统成熟度、性能特征、以及长期维护承诺**。**本次发布的信号是正向的**（Xorg + OpenGL、四个架构、xfstests、自举），**但 341 个未关闭 issue 和「AArch64 的 CI 覆盖仍在增长」这类表述，说明它仍在早期。**

**不过我认为有一个方向是它可能先落地的**：**作为 Kata / Confidential Containers 的 guest 内核**。**因为那个场景的需求边界比通用 OS 窄得多**（不需要支持几千种外设、不需要兼容全部 Linux 语义），**而对「TCB 要小且内存安全」的需求又特别强**。**从「替代 Linux」改成「替代容器沙箱里的那个 Linux」，是一个合理得多的切入点。**

**第五，把这条新闻放进这段时间的脉络里，会看到一个共同点。** **Asterinas 的 framekernel（把 unsafe 收敛到一个框架）、Meta 的 CRAM（把解压挪到硬件）、Linus 那份用 AI 写的补丁（把「AI 做了什么、人做了什么」写清楚）、Intel 的 SGX→TDX（把保护边界选在能规模化的那一层）**：**它们讨论的都不是「更强」，而是「把边界划在哪里」。** **而划边界这件事之所以重要，是因为它决定了你能否说清「我保证什么、不保证什么」。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 版本 | **Asterinas 0.19.0**（发布公告 2026-10-13；GitHub release 标记 2026-10-12） |
| 项目定位 | **用 Rust 从零构建的操作系统内核**，目标是**生产级的 Linux 替代品**（内存安全、高性能） |
| 仓库（实测） | **asterinas/asterinas：创建 2022-05-17，4,946 stars，390 forks，341 个未关闭 issue，Rust，MPL-2.0** |
| 发布节奏 | **v0.18.0（2026-06-03）→ v0.18.1（08-18）→ v0.19.0（10-12）** |
| 规模 | **100+ 人贡献过代码；代码库超 25 万行，其中约 20 万行 Rust；本次发布 55 人参与，其中 31 人首次** |
| **架构** | **framekernel**：整个 OS 在**同一地址空间**（像宏内核），但划分为**享有特权的 Framework**（类似微内核，**唯一允许用 `unsafe`**）与**没有特权的 Services**（**必须全部安全 Rust**）。定位是**「宏内核的速度，微内核的安全性」** |
| **核心承诺** | **所有 unsafe Rust 都被限制在 `ostd` 里；内核其余部分包括所有外设驱动全部是安全 Rust** |
| **可度量的 unsafe 预算** | **所有需要 `unsafe` 的代码住在 OSTD 的虚拟化模块里，约 2000 行** |
| ① 图形 | **Asterinas NixOS 可在标准 `modesetting` 驱动上跑 Xorg + Mesa 软件 OpenGL**（不再依赖 fbdev）；新的 **`aster-drm`** 提供 **DRM 核心、`/dev/dri` 设备节点、GEM dumb buffers、KMS 对象**；**demo 跑两个 3D 游戏** |
| ② AArch64 | **第四个架构**（此前为 x86-64、RISC-V、LoongArch）；**「最小但可用」**：QEMU `virt` 上带起 **GICv3、通用定时器、PL031 RTC、PL011 UART、virtio-mmio**，跑 BusyBox shell 含 **vDSO**；**Tier 2 平台，CI 覆盖仍在增长** |
| ② Arm 开发主机 | **Docker 镜像同时发布 `linux/arm64`**；**Nix 开发 shell 支持 `aarch64-linux`** |
| ③ 安全容器 | 定位为 **Kata Containers / Confidential Containers 的 guest 内核**（「内存安全的 guest 内核移除了一整类可被利用的 bug」）；**重写 overlayfs（xfstests 通过用例翻倍）**、**mount propagation + `fsopen` 系列**、**virtio-fs 成熟（`mmap`、`O_DIRECT`、重命名、符号链接、多页 I/O；xfstests 进 CI）**、**PVH 引导 + 可作 Firecracker microVM guest**、**TDX 引导分摊到所有 vCPU** |
| ④ 虚拟化 | **RFC-0003** 定设计：**OSTD 拥有机制**（虚拟化硬件状态、二级地址转换、guest-host 切换），**内核拥有策略**（VM/vCPU 生命周期、内存槽、中断控制器、设备模拟、最终兼容 KVM 的 `/dev/kvm`）；**本次交付 Intel VMX 基础**（VMX 生命周期、VMCS、EPT guest 内存、guest CPU 状态、guest 执行返回 VM exit）；**Book 有「约 100 行安全 Rust 写一个最小 hypervisor」的示例** |
| ④ 动机 | **Xen 类 Type 1 保持核心小但依赖 dom0 的 Linux 提供驱动与管理；Linux + KVM 方便，但把一个大 C 内核放进每个 VM 的可信基** |
| ⑤ 设备模型 | 新的 **`aster-device`**（全部安全 Rust，Linux driver core 的 Rust 原生对应物）：**`Driver<B>` 只能注册到总线 `B`**；**`ClassDevice<C>` 把类带在类型里，`ClassObserver<C>` 只听到类 `C`**；**`Attr<D>` 声明在设备类型 `D` 上，回调收到 `&D`，无需向下转型泛型指针** |
| ⑥ AI 代码审查 | **`aster-code-review` skill**；原文：**「代理让代码变得便宜。人类审阅才是留下来成为瓶颈的那一环。」**；**Coding Guidelines 围绕 5 个审阅者角色重组为 81 条并给稳定短名**；**每个主观判断引用一条规范**；**每个角色跑一遍并先试图反驳每条评论**；**基准：58 个审查问题 / 138 个预期缺陷，几乎全部从项目自身历史挖掘，每次漏检驱动规范或 skill 改动** |
| ⑦ 自举 | **通过**：在 VM 里启动 Asterinas NixOS → 克隆仓库 → Nix 开发 shell → `make kernel` → 嵌套 QEMU VM 启动新内核；**Nix、Cargo、rustc、QEMU 一路都跑在 Asterinas 上**，官方称这是**「这个内核被施压过的最大的真实负载之一」** |
| ⑦ Nix 生态 | **新增 Nix flake 作为 Docker 替代**，工具链/QEMU/固件在 **Cachix** 预构建；**三条命令**：`nix develop`、`make kernel`、`make run_kernel` |
| 许可 | **MPL-2.0**（官方表述为「弱 copyleft」，确保项目对全人类自由且永远如此） |
| 支持方 | **蚂蚁集团、复旦大学、Intel、北京大学、南方科技大学、TLAIC** |

## 延伸阅读

- [LWN：Asterinas 0.19.0 released](https://lwn.net/Articles/1100055/)
- [Asterinas 官方发布公告](https://asterinas.github.io/2026/10/13/announcing-asterinas-0.19.0.html)
- [The Asterinas Book](https://asterinas.github.io/book/)（含 [约 100 行安全 Rust 写 hypervisor](https://asterinas.github.io/book/ostd/a-100-line-hypervisor.html) 的示例）
- [GitHub：asterinas/asterinas](https://github.com/asterinas/asterinas)
- [本站：「很难」是过去时：一个人 8 天写出微内核操作系统，以及为什么 unikernel 又回来了](/articles/2026-10-11_unikernels-veda-agentic-os/)
- [本站：Linus 用 Claude Code 改内核：这份 commit message 比那个性能数字更值得读](/articles/2026-10-12_linus-torvalds-claude-code-kernel/)
- [本站：LTS 在 AI 时代过时了？补丁洪流是真的，但「改用滚动发布」是个假二选一](/articles/2026-10-10_lts-vs-rolling-release-genai/)
