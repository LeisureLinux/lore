---
title: "BSD 的代码流进了哪里：你以为它是小众，但它可能就在你的游戏机、路由器和 NAS 里"
date: 2026-10-21
slug: bsd-code-in-proprietary-products
tags: [BSD, FreeBSD, macOS, XNU, Darwin, Junos, Juniper, ONTAP, NetApp, Netflix, Open Connect, PlayStation, Orbis OS, Nintendo Switch, Windows NT, EULA 归属声明, BSD 许可证, 闭源, 基础设施]
category: 系统/硬件
author: FreeLAMP.com
original_source: "Netflix Open Connect 官方页面 + Juniper 官方文档 + FreeBSD 项目文档 + 各产品的许可证归属与公开资料"
original_author: "Netflix Open Connect 团队；Juniper；NetApp；Sony；Nintendo；Apple"
original_date: 2026-10-21
original_url: "https://openconnect.netflix.com/en/appliances"
description: "一篇讲「BSD 的代码实际流进了哪些产品」的调查。核心是区分三种程度：有的是整块内核（PS4/PS5 的 Orbis OS 基于 FreeBSD 9/11）、有的只是部分子系统（macOS 的 XNU 只拿了 BSD 的 VFS、网络栈和部分用户态；早期 ONTAP 只用了 BSD 的网络栈和启动代码；Nintendo Switch 用许可证归属能证明的只是「含 FreeBSD 代码」）、有的是深度改造后几乎不再是原物（Junos 把 FreeBSD 内核逐行审查后重写成自己的内核）。而 Netflix 那条线不一样：它跑的几乎就是 FreeBSD-current 的 head，并且把改进全数上游回馈。"
published: true
---

> 来源：本文的每一个具体说法都回到官方页面或原始资料核对：[Netflix Open Connect 官方公告页](https://openconnect.netflix.com/en/appliances)（**一手，明确写了「Operating System: FreeBSD -CURRENT (HEAD)」**）、[Juniper 官方文档的 Junos OS 概述](https://www.juniper.net/documentation/us/en/software/junos/junos-install-upgrade/topics/topic-map/junos-os-overview.html)、[FreeBSD Journal 的 Netflix 案例研究](https://freebsdfoundation.org/wp-content/uploads/2021/03/Netflix-Open.pdf)、[Netflix 工程师在 FOSDEM/BSDCan 的演讲](https://papers.freebsd.org/2019/BSDCan/looney-Netflix_and_FreeBSD.files/looney-Netflix_and_FreeBSD.pdf)、[FreeBSD 版本历史](https://en.wikipedia.org/wiki/FreeBSD_version_history)、[ONTAP 记录](https://en.wikipedia.org/wiki/ONTAP)。
> 这是「Unix 家族史」的**第四篇**（前三篇：起源与分裂 / 商业 Unix / BSD 家族全表）。**⚠️ 本文特别注意区分「整块内核」「部分子系统」「许可证归属能证明的范围」三种不同性质，请勿混用。**
> 本文为**解读**。第二节的「三档分类」框架、第四节的判断是笔者补充的部分。

## 一句话结论

**「BSD 是小众系统」这句话在桌面语境下成立，在基础设施语境下完全不成立。**

**但它容易被讲成一种夸大：把「某个产品的许可证声明里提到 FreeBSD」说成「这个产品跑在 FreeBSD 上」。这两件事差别很大。**

**所以我按「BSD 代码参与的程度」把它们分成三档，而每一档的证据强度完全不同**：

| 档位 | 含义 | 代表 |
|---|---|---|
| ⭐ **第一档：整块内核就是 FreeBSD** | **改动主要在用户态和驱动，内核本身还是 FreeBSD** | **PS4 / PS5 的 Orbis OS（基于 FreeBSD 9 / 11）**；**Netflix 的 Open Connect Appliance（几乎就是 FreeBSD-current）** |
| **第二档：只拿了部分子系统** | **内核是别的，但网络栈/VFS/用户态来自 BSD** | ⭐ **macOS 的 XNU（Mach + BSD 混合）**；**早期 ONTAP（专有内核 + BSD 网络栈）**；**Nintendo Switch（许可证归属能证明的只是「含 FreeBSD 代码」）** |
| **第三档：深度改造，几乎不再是原物** | **逐行审查重写后拥有自己的内核** | ⭐ **Juniper 的 Junos（FreeBSD 内核被改成「不再是 FreeBSD」）** |

**而我认为这张表最该被记住的是「证据强度」这件事**：**第一档有一手证据（官方文档、演讲、版本号），第三档有厂商自己的技术说明，而第二档里最模糊的就是 Nintendo Switch**，**因为它的证据只有「系统软件的许可证归属里出现了 FreeBSD 的版权声明」。** **而这只能证明「含 FreeBSD 代码」，不能证明「跑在 FreeBSD 上」。**

## 一、第一档：内核真的就是 FreeBSD

### PS4 和 PS5：Orbis OS

**这一条是「整块内核」档里最明确的。**

**FreeBSD 的版本历史页写得很直接**：

> **「PlayStation 4 电子游戏机使用 FreeBSD 9.0 的一个衍生版本，Sony Computer Entertainment 称之为 Orbis OS。」**

**而 PS5 的情况，公开资料的说法是它把基座升到了 FreeBSD 11。** **⚠️ 而这里我要标注：PS4 用 FreeBSD 9.0 这一点有 FreeBSD 官方版本历史页作为依据；而「PS5 用 FreeBSD 11」这个说法我核到的是第三方整理，没有找到 Sony 或 FreeBSD 官方的对应声明。**

**而 Sony 为什么选 FreeBSD，有一个很直接的理由，而它和许可证有关**：**BSD 许可证允许修改后闭源分发，不要求你把改动公开。** **所以 Sony 可以给 Orbis OS 加自己的 GPU 调度、DRM、安全沙箱，而不需要发布这些代码。**

**而也有反过来的证据说明它不是「随便改改」**：**Sony 的一些改进曾经回流到 FreeBSD 内核**，**这说明当年它确实是在 FreeBSD 的内核上做工作，而不是另起炉灶。**

### Netflix 的 Open Connect：这一档里最特殊的一个

**Netflix 这一条之所以特殊，是因为它不只是「用了 FreeBSD」，而是「和 FreeBSD 项目深度互相依赖」。**

**Netflix 官方公告页的表述没有含糊**：

> **「操作系统：FreeBSD -CURRENT (HEAD)」**
>
> **「FreeBSD 因其稳定性与特性的平衡、强大的开发社区以及团队的专业能力而被选中。所有的代码改进、功能增加和 bug 修复都通过我们团队里的 FreeBSD committer 直接贡献回开源社区。」**
>
> **「我们也努力站在 FreeBSD 开发流程的前沿，让我们与其他社区和伙伴开发者保持紧密的反馈闭环。」**

**而「跑 head 分支」这件事有多激进，Netflix 工程师自己讲得很清楚**（**BSDCan 2019 演讲**）：

> **「Netflix 做的稍微不寻常的一点是，它的 OCA 操作系统代码紧密跟踪 FreeBSD 的 head 分支（他们的开发分支）。事实上，一个提交到上游 FreeBSD 开发分支的改动，通常会在 5 到 15 周内完整部署到 Netflix 的 CDN 上。」**

**「5 到 15 周内完整部署到 Netflix 的 CDN 上」。** **这个数字意味着：Netflix 的变更部署速度比很多企业的「测试环境」还快。**

**而这一条最值得记的技术事实是性能数据，因为它很具体**：

> **「使用 FreeBSD 和商用部件，我们在一颗 Intel 6122 CPU、1RU、96GB RAM、16TB NVMe 附加闪存上，以约 55% 的 CPU 占用实现了 90 Gb/s 的 TLS 加密连接服务。」**

**「90 Gb/s，55% CPU，1RU 机器」。** **而 FreeBSD Journal 那篇案例研究还给了另一组数字**：**「Kernel TLS 性能：90Gb/s，68% CPU（软件），35% CPU（T6 加速卡）。」**

**而规模上，FreeBSD 基金会 2021 年的案例研究写的是**：**「Netflix 报告其全球 Open Connect 网络在峰值时推送超过 100 Tb/s 的流量。根据 Sandvine，这在 2019 年代表了整个互联网流量的约 15%。」**

**「互联网流量的约 15%」。** **而这里我必须标注一个重要的时效性**：**这是 2019 年的数据。** **而我在 2026 年没有核到更新的同口径数字**，**所以任何「今天仍是 15%」的说法都是不该做的推断。**

**而 Netflix 对 FreeBSD 的贡献清单，是这一档里最有说服力的部分**（**OpenFest 2023 的演讲**）：

> **「异步 sendfile、unmapped mbufs、内核 TLS、CAM IO 调度器、RACK 和 BBR TCP、TCP HPTS（TCP pacing）、NUMA 性能增强。」**
>
> **「还有：用于高效防火墙包处理的 pfil 内存指针钩子、大量可扩展性修复、用于 arm64 和 amd64 的 kboot（从 Linux 内核 kexec 启动 FreeBSD）。」**

**「内核 TLS 花了大约 5 年才上游。」** **这句话说明「把企业改动回流上游」这件事的成本**：**它不是「提交一个 PR」，而是「让一个改动达到上游的质量标准」，而那个过程可能需要几年。**

## 二、第二档：只拿了部分子系统，而这一档最容易讲错

### macOS：XNU 是混合内核，不是 FreeBSD

**这是最需要精确表述的一条，因为「macOS 基于 BSD」这个说法既对又不完全对。**

**准确的说法是**：**macOS 的内核叫 XNU，它是一个混合内核，由 Mach 微内核 + BSD 组件 + I/O Kit 组成。** **而它从 BSD 拿的**不是整个内核**，是几块具体的东西**：**虚拟文件系统层（VFS）、网络栈、以及相当一部分 POSIX 兼容的用户态。**

**而 Apple 自己怎么表述这件事？** **Apple 的 Open Source 页面说**：**「开源软件是 Apple 平台和开发者工具的核心。Apple 与全世界的开发者合作，创建、贡献并发布开源代码。」** **而它列出的「重点项目」是 Swift、Container、WebKit，而不是 XNU。**

**⚠️ 所以关于 XNU 的具体成分，我认为最准确的表述是**：**它是 Mach 与 BSD 的混合体，BSD 部分提供的是一套内核服务（进程模型、VFS、网络、POSIX 语义），而不是「macOS 跑在 FreeBSD 上」。** **而「Apple 历史上从 FreeBSD 5.x 及更后版本拉过各种子系统更新」这个说法，我核到的是第三方整理，没有找到 Apple 的逐项公开说明。**

**而这一条有一个反直觉的后果**：**就是我们在上一篇讲过的，macOS 的 UNIX 认证是真的，而它的血统是混合的**。**所以「BSD 血统」和「BSD 内核」是两个不同强度的说法。**

### ONTAP：早期版本只用了 BSD 的网络栈和启动代码

**NetApp 的 ONTAP 是一个「容易被夸大」的例子，而记录本身写得很精确**：

> **「ONTAP 最初的版本有一个专有的非 UNIX 内核，而它的 TCP/IP 协议栈、网络命令、以及底层启动代码来自 BSD Net/2 和 4.4BSD-Lite。」**

**「专有的非 UNIX 内核」加「网络栈、网络命令、启动代码来自 BSD」。** **这就是典型的第二档：内核是自己的，但网络那一层是 BSD 的。**

**而 ONTAP GX 那条支线不一样**：

> **「Data ONTAP GX 基于从 Spinnaker Networks 收购的网格技术，它从 FreeBSD 引导，作为一个独立的内核态模块运行，并使用 FreeBSD 的一些功能（例如它使用一个命令解释器和驱动栈）。」**

**而 FreeBSD 的维基百科条目给了更简的概括**：**「NetApp 的 Data ONTAP 8.x 以及已被取代的 ONTAP GX（只作为专有内核态模块的加载器）。」**

**「只作为加载器」（only as a loader）。** **这个限定很重要，因为它说明 ONTAP GX 里 FreeBSD 的角色是「引导和加载」，而不是「整个系统」。**

### Nintendo Switch：这一条的证据最弱，而它最常被说成第一档

**这一条我要特别谨慎，因为它是最容易讲错的一个。**

**有一种说法是「Nintendo Switch 运行 FreeBSD」**，**而 2017 年 OSnews 那篇报道的标题就是这个。** **但同一页的评论区里就有人提出了反对，而那些反对意见我认为是对的**：

> **「他们在文档里有一个『FreeBSD Kernel』BSD 版权声明，这可能只意味着产品包含了 FreeBSD 内核的一部分，比如网络子系统的头文件。这不意味着它基于运行 FreeBSD 内核。」**
>
> **「我们不知道 Switch 运行 FreeBSD。我们只从公开信息知道它使用了 FreeBSD 内核的代码。」**
>
> **「注意，微软在 Windows NT 3.5 之前也在 Windows NT 里用过 FreeBSD 内核代码，而没有人因此说 Windows 电脑运行 FreeBSD。」**

**而还有人指出了版权声明的具体年份**：**「这些版权声明的日期是 1995-1996，以及 Jean-loup Gailly 和 Mark Adler，所以大概是压缩相关的。」**

**我认为这个讨论很有价值，因为它给出了判定的方法论**：**许可证归属声明只能证明「代码在二进制里」，不能证明「哪个部分占主导」。** **而「1995-1996 的版权 + zlib 作者的名字」这个细节更有意思，因为 zlib 是压缩库，而如果归属声明主要覆盖的是压缩代码，那么它能支撑的结论就更弱了。**

**⚠️ 所以关于 Switch，我的结论是**：**「它的系统软件含 FreeBSD 的代码」这个说法有依据（许可证归属），而「它运行 FreeBSD」这个说法超出了证据能支撑的范围。** **而更流行的说法是「它用了 FreeBSD 的网络栈」，但这个说法同样需要更硬的证据。**

## 三、第三档：改造到几乎不再是原物

### Juniper 的 Junos

**这一档里最清楚的是 Junos，而它的清楚不是因为「用了 BSD」，而是因为「改造的过程被公开描述过」。**

**而 Juniper 官方文档现在写得非常直接**：

> **「Junos OS 包括以下架构变体：在裸金属上的 Junos OS FreeBSD 10 或更新版本。这是基于升级后的 FreeBSD 内核的 Junos OS。大多数基于 Junos OS 的硬件平台运行带升级 FreeBSD 的 Junos OS。」**

**「基于升级后的 FreeBSD 内核」。** **而改造的深度，Network World 2008 年那篇文章描述得最具体**：

> **「Juniper 的开发者从逐行审查 FreeBSD 代码开始，把 FreeBSD 内核变成 JUNOS 内核，移除所有不需要的组件和驱动。一些代码被重写以符合 Juniper 内部的风格指南，代码按需加上注释。然后加上 Juniper 特有的『钩子』。」**
>
> **「这个过程（当 Juniper 决定把 FreeBSD 更新纳入 JUNOS 时会偶尔重复）产生一个内核，它虽然基于 FreeBSD，但已经不再是 FreeBSD。它现在是一个 JUNOS 内核，并且像任何其他内部代码一样被同样的管理和变更控制流程处理。」**

**「虽然基于 FreeBSD，但已经不再是 FreeBSD。」** **我认为这句话是这一档的定义**：**它不是「拿来用」，而是「拿来之后逐行改写」，改到厂商自己认为它已经是一个自有内核。**

**而 Junos 的模块化架构也值得记**：**「各种功能组件被分成模块，称为守护进程。例如有一个运行所有路由协议的路由协议守护进程（RPD）、一个控制所有接口的设备控制守护进程（DCD）、一个控制机箱硬件的机箱守护进程等等。每个模块运行在自己的受保护内存空间里，没有模块能使用另一个模块的内存。」**

**「每个模块运行在自己的受保护内存空间里」。** **这个设计对网络设备特别重要**，**因为一个路由协议的 bug 不该让整个设备崩掉。**

### 还有一个被引用了很多年的案例：Windows NT

**这一条我在上面那个 Switch 的讨论里看到了，而它值得单独说，因为它说明「用 BSD 代码」这件事的历史比很多人想的要早。**

**那个讨论里的原话是**：**「注意，微软在 Windows NT 3.5 之前也在 Windows NT 里用过 FreeBSD 内核代码，而没有人因此说 Windows 电脑运行 FreeBSD。」**

**⚠️ 而我必须标注：这个具体说法（哪个版本、用了哪部分）我没有核到微软的官方确认。** **所以更安全的表述是**：**「早期 Windows NT 曾在网络栈部分借用过 BSD 的代码」这个说法在技术史圈里流传已久，而我未核到微软官方文档确认其具体范围。** **而它作为「反例」的价值不依赖细节：** **它说明「二进制里有 BSD 代码」和「这个系统是 BSD」是两件事。**

## 四、为什么是 BSD 而不是 Linux：一个许可证问题

**这一节我认为是理解「为什么这些公司选 BSD」的关键，而它的答案很直接：许可证。**

**Netflix 那句话把这件事说得最精炼**（**BSDCan 2019 演讲**）：

> **「我们为许可证而来。我们为效率而留。」**
>
> **（We came for the license. We stay for the efficiency.）**

**「为许可证而来」。** **而 BSD 许可证（以及它的变体）的核心特征是**：**它允许你修改、闭源、商业分发，而不要求你把改动公开。** **对比 GPL：GPL 要求衍生作品也以 GPL 发布。**

**而这个区别对三类公司有实际意义**：

| 公司类型 | 为什么 BSD 重要 |
|---|---|
| **游戏机厂商（Sony）** | **可以深度改造内核加 DRM 和安全沙箱，而不必公开这些改动** |
| **网络/存储设备厂商（Juniper、NetApp）** | **可以做出产品差异化，而不必把内核改动给竞争对手** |
| **内容分发（Netflix）** | ⚠️ **这一条不一样：Netflix 不是因为要闭源，而是因为「许可证不构成障碍」这件事降低了法务和管理成本** |

**而 Netflix 这一条值得单独说，因为它是「用 BSD 但不闭源」的样本**：**它跑的几乎是原版 FreeBSD-current，而它把改进全数上游。** **所以它选 BSD 的理由，与其说是「可以闭源」，不如说是「没有额外义务」。**

**而这也解释了 FreeBSD 维基百科里那句话的背景**：**「今天，FreeBSD 被许多 IT 公司用于构建他们的产品，例如 IBM、Nokia、Juniper Networks 和 NetApp。Apple 的 macOS 操作系统的某些部分基于 FreeBSD。」**

**「某些部分」（Certain parts）。** **注意这个措辞，它是维基百科对一个有争议说法的最谨慎表述，而我认为它恰好是我们这一篇的核心：** **「某些部分」和「整个系统」之间，隔着一整档的距离。**

## 五、我的判断

**第一，这篇最该被记住的不是「BSD 用得多广」，而是「怎么判断一个产品到底用了多少 BSD」。** **因为这类说法最常见的错误是把「许可证归属里出现 FreeBSD」直接升格成「跑在 FreeBSD 上」。** **而正确的判定顺序应该是**：**① 有没有厂商官方文档明确说内核是什么（Netflix、Juniper 都有）？② 有没有工程师在公开演讲里讲过架构（Netflix 有）？③ 有没有第三方技术分析（Junos 有 Network World 那篇）？④ 如果只有许可证归属声明，那么它能证明的只是「含代码」，不能证明「哪个部分占主导」。**

**第二，Netflix 那一条是「开源协作」的少见样本，而它最反直觉的地方是「跑 head 分支」。** **因为大多数企业用户会选稳定版，而 Netflix 选开发分支，理由是「5 到 15 周就能把上游修复部署到全网」加上「早期使用能给上游提供大规模验证」。** **而这件事能成立的前提是 FreeBSD head 的质量足够高**，**Netflix 自己的说法是**：**「head 的质量如此之高，以致 bug 的余波是可控的。」** **我认为这个判断对任何维护大型系统的人都有参考价值**：**「开发分支不稳定」这个常识，在某些项目上是不成立的，而判断依据应该是「这个项目的开发分支质量有多高」，而不是「它是开发分支」。**

**第三，Junos 那一档说明了一件容易被忽略的事：「基于 BSD」可以是一个法律描述，而不是一个技术描述。** **因为 Juniper 拿到 FreeBSD 代码之后逐行改写、移除、重写、加钩子，最终产出一个「虽然基于 FreeBSD 但已经不再是 FreeBSD」的内核。** **所以「Junos 是 FreeBSD」这个说法在**法律上**成立（因为它源自 BSD 代码），在**技术上**已经有距离。** **而这和我们在前一篇讲的「血统 vs 认证」是同一个问题的另一面**：**血统可以很远，而法律义务可以很实在。**

**第四，关于 Nintendo Switch 那一条，我认为保留「不确定」比给一个确定答案更有价值。** **因为它的证据只有许可证归属，而那个归属甚至可能主要覆盖的是压缩库。** **所以正确的表述是「系统软件含 FreeBSD 代码」，而「运行 FreeBSD」是需要更强证据的说法。** **我认为在处理这类「听起来很酷」的技术说法时，主动标注不确定性比给一个漂亮的结论更有用**，**因为前者的读者可以自己去核，而后者的读者会把错误传下去。**

> **最后一点，关于「基础设施语境」，我想补一个我在核实过程中意识到的区分**：**「BSD 在基础设施里无处不在」这个说法，有一部分是靠**产品**（Juniper、NetApp、pfSense、TrueNAS），有一部分是靠**服务**（Netflix），而这两类的影响力不一样。**
>
> **产品的影响是「你不知道你在用 BSD」，而服务的影响是「你知道你在用这个服务，但不知道它跑在 BSD 上」。**
> **而后者在传播上更弱势：因为用户不会去查一个视频网站用什么操作系统。所以「BSD 份额小」这个印象，很大程度上是「BSD 的成功是不可见的」造成的。**

## 关键事实速查

### 第一档：整块内核

| 产品 | BSD 参与程度 | 证据 |
|---|---|---|
| ⭐ **PS4（Orbis OS）** | **使用 FreeBSD 9.0 的衍生版本** | **FreeBSD 版本历史页：「PlayStation 4 电子游戏机使用 FreeBSD 9.0 的一个衍生版本，Sony Computer Entertainment 称之为 Orbis OS。」** |
| **PS5（Orbis OS）** | ⚠️ **公开资料说升到 FreeBSD 11 基座** | **⚠️ 此为第三方整理，未找到 Sony 或 FreeBSD 官方对应声明** |
| **Sony 为什么选 BSD** | **BSD 许可证允许闭源修改分发** | **可以加 GPU 调度、DRM、安全沙箱而不必公开** |
| **反向证据** | **Sony 的一些改进曾回流 FreeBSD 内核** | 说明确实在 FreeBSD 内核上工作 |
| ⭐ **Netflix Open Connect** | **「操作系统：FreeBSD -CURRENT (HEAD)」** | **Netflix 官方公告页，一手** |
| **Netflix 的部署速度** | **「上游提交通常会在 5 到 15 周内完整部署到 CDN」** | **BSDCan 2019 演讲** |
| **Netflix 的性能** | **「90 Gb/s 的 TLS 加密连接，约 55% CPU，Intel 6122，1RU，96GB RAM，16TB NVMe」** | **官方公告页 + FOSDEM 2019** |
| **Kernel TLS 性能** | **「90Gb/s，68% CPU（软件），35% CPU（T6 加速卡）」** | **FreeBSD Journal 2021 案例研究** |
| ⚠️ **Netflix 的流量占比** | **「峰值超过 100 Tb/s」；「据 Sandvine 在 2019 年约占整个互联网流量 15%」** | ⚠️ **是 2019 年数据，未核到更新的同口径数字** |
| **Netflix 的贡献清单** | **异步 sendfile、unmapped mbufs、内核 TLS、CAM IO 调度器、RACK 与 BBR TCP、TCP HPTS、NUMA 性能增强、pfil 指针钩子、kboot** | **OpenFest 2023 演讲** |
| **上游成本** | **「内核 TLS 花了大约 5 年才上游」** | 说明回流的真实成本 |

### 第二档：部分子系统（最容易讲错）

| 产品 | BSD 参与程度 | 证据强度 |
|---|---|---|
| ⭐ **macOS（XNU）** | **混合内核：Mach + BSD 组件 + I/O Kit**；**BSD 部分提供 VFS、网络栈、相当一部分 POSIX 用户态** | **Apple 官方承认开源，但未逐项说明 XNU 成分** |
| **macOS 的正确表述** | **「部分子系统来自 BSD」，不是「跑在 FreeBSD 上」** | — |
| **早期 ONTAP** | ⭐ **「专有的非 UNIX 内核，而它的 TCP/IP 协议栈、网络命令、以及底层启动代码来自 BSD Net/2 和 4.4BSD-Lite」** | **记录明确** |
| **Data ONTAP GX** | **从 FreeBSD 引导，作为独立内核态模块运行，使用 FreeBSD 的命令解释器和驱动栈** | **「只作为专有内核态模块的加载器」** |
| ⚠️ **Nintendo Switch** | ⚠️ **只能说「系统软件含 FreeBSD 代码」** | ⚠️ **只有许可证归属声明；且有人指出版权年份是 1995-1996、作者是 zlib 的 Gailly/Adler，可能主要覆盖压缩代码** |
| **Switch 的反对意见（值得记）** | **「这可能只意味着产品包含了 FreeBSD 内核的一部分，比如网络子系统的头文件。这不意味着它基于运行 FreeBSD 内核。」**；**「我们只从公开信息知道它使用了 FreeBSD 内核的代码。」** | — |

### 第三档：改造到几乎不再是原物

| 产品 | BSD 参与程度 | 证据 |
|---|---|---|
| ⭐ **Juniper Junos** | **「在裸金属上的 Junos OS FreeBSD 10 或更新版本。这是基于升级后的 FreeBSD 内核的 Junos OS。」** | **Juniper 官方文档，一手** |
| ⭐ **改造深度** | **「逐行审查 FreeBSD 代码，移除所有不需要的组件和驱动，一些代码被重写以符合内部风格指南，然后加上 Juniper 特有的钩子」** | **Network World 2008** |
| ⭐ **厂商自己的定性** | **「虽然基于 FreeBSD，但已经不再是 FreeBSD。它现在是一个 JUNOS 内核。」** | **同上** |
| **Junos 架构** | **模块化，组件分为守护进程（RPD、DCD、机箱守护进程等），每个运行在自己的受保护内存空间** | **一个路由协议的 bug 不该让整机崩掉** |
| **Evolved 变体** | **另有 Junos OS Evolved** | **Juniper 官方文档** |

### 许可证这个理由

| 项目 | 内容 |
|---|---|
| ⭐ **Netflix 的原话** | **「我们为许可证而来。我们为效率而留。」（We came for the license. We stay for the efficiency.）** |
| **BSD 许可证的核心特征** | **允许修改、闭源、商业分发，不要求公开改动** |
| **GPL 的对比** | **要求衍生作品也以 GPL 发布** |
| **游戏机厂商（Sony）** | **可以深度改造加 DRM 与沙箱而不必公开** |
| **设备厂商（Juniper、NetApp）** | **可以做产品差异化，不必把内核改动给对手** |
| **Netflix 的特殊性** | ⚠️ **不是因为要闭源，而是「许可证不构成障碍」降低了法务与管理成本；它跑的几乎是原版，改动全数上游** |
| **FreeBSD 维基百科的措辞** | **「FreeBSD 被许多 IT 公司用于构建产品，例如 IBM、Nokia、Juniper Networks 和 NetApp。Apple 的 macOS 操作系统的**某些部分**基于 FreeBSD。」** |

### 判断方法论

| 步骤 | 问题 | 强度 |
|---|---|---|
| **①** | **有没有厂商官方文档明确说内核是什么？** | **最强**（Netflix、Juniper 都有） |
| **②** | **有没有工程师在公开演讲里讲过架构？** | **强**（Netflix 有） |
| **③** | **有没有第三方技术分析？** | **中**（Junos 有 Network World） |
| ⚠️ **④** | **如果只有许可证归属声明** | **最弱：只能证明「含代码」，不能证明「哪个部分占主导」** |

## 延伸阅读

- [BSD 家族全表：四个正统、一个桌面发行版，以及「UNIX 认证」这件事的真相](https://freelamp.com/articles/2026-10-21_bsd-family-2026-freebsd-openbsd-netbsd-ghostbsd/)
- [商业 Unix 只剩一个还在开发：HP-UX 刚刚断线，而它死于一枚停产的 CPU](https://freelamp.com/articles/2026-10-21_commercial-unix-2026-aix-hpux-solaris-status/)
- [Unix 为什么会分裂成两个阵营：而答案不在技术里，在 1956 年的一份反垄断同意令里](https://freelamp.com/articles/2026-10-21_unix-history-origins-system-v-bsd-split/)
- [OpenBSD 8.0 发了：而这次最值得看的不是漏洞修复清单，是内核虚拟地址空间从 4G 跳到 512G](https://freelamp.com/articles/2026-10-20_openbsd-8-0-release-kernel-address-space/)
- [Netflix 官方 Open Connect Appliance 页面（一手）](https://openconnect.netflix.com/en/appliances)
- [Juniper 官方 Junos OS 架构文档（一手）](https://www.juniper.net/documentation/us/en/software/junos/junos-install-upgrade/topics/topic-map/junos-os-overview.html)
