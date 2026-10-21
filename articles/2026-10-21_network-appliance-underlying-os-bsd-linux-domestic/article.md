---
title: "网络设备的底层用什么内核？国外厂商公开写 FreeBSD，而国内厂商大多只说「自研」"
date: 2026-10-21
slug: network-appliance-underlying-os-bsd-linux-domestic
tags: [网络设备, 防火墙, 底层内核, FreeBSD, BSD, Linux, pfSense, OPNsense, Check Point IPSO, IronPort AsyncOS, NetScaler, Junos, OneFS, F5 TMOS, PAN-OS, H3C Comware, 深信服 Sangfor OS, 山石 StoneOS, 天融信 TopOS, 锐捷 RGOS, 迪普 ConPlat, 信创]
category: 系统/硬件
author: FreeLAMP.com
original_source: "各厂商官方文档、开源合规声明、技术白皮书、Wikipedia 的 FreeBSD 产品清单"
original_author: "Netgate、Deciso、Check Point、Cisco、Citrix、Juniper、EMC/Dell、F5、Palo Alto、H3C、深信服、山石网科"
original_date: 2026-10-21
original_url: "https://en.wikipedia.org/wiki/List_of_products_based_on_FreeBSD"
description: "把网络设备、防火墙、存储和 CDN 的底层内核按厂商和产品类型列成表。国外厂商有一个共同点：它们普遍会公开开源合规文档，所以底层的 BSD 血统可以被反推出来（Citrix 直接有一份叫「FreeBSD-based Products」的文件，Cisco IronPort 的文档写明「基于 FreeBSD 内核」，Juniper 官方确认「基于升级后的 FreeBSD 内核」）。而国内厂商普遍不发布这类文档，所以深信服、山石、天融信、锐捷、迪普都只能说「官方称自研，内核未披露」。唯一的例外是 H3C，它的官方文档直接写「Comware V7 是一个基于 Linux 的通用开放系统」。"
published: true
---

> 来源：本文的每一个结论都标注了证据来源。**国外厂商部分**依据厂商官方文档与开源合规声明：[Citrix 的 FreeBSD Third Party Notices](https://www.citrix.com/content/dam/citrix/en_us/documents/downloads/netscaler-adc/NetScaler_ADC_ADM_FreeBSD_13.1_Third_Party_Notices.pdf)、[Juniper 官方 Junos OS 架构文档](https://www.juniper.net/documentation/us/en/software/junos/junos-install-upgrade/topics/topic-map/junos-os-overview.html)、[Cisco IronPort AsyncOS 用户指南](https://www.cisco.com/c/dam/en/us/td/docs/security/wsa/wsa6-5/user_guide/WSA_6-5-0_UserGuide.pdf)、[F5 的 TMOS 白皮书](https://cdn.studio.f5.com/files/k6fem79d/production/6dcf11c95e4fc14e72c62ca49b458dc022279cce.pdf)、[PAN-OS 的 OSS 清单](https://docs.paloaltonetworks.com/oss-listings/pan-os-oss-listings/pan-os-12-1-open-source-software-oss-listing)、[Wikipedia 的 FreeBSD 产品清单](https://en.wikipedia.org/wiki/List_of_products_based_on_FreeBSD)。**国内厂商部分**依据其技术白皮书与官方公告：[H3C Comware V7 官方页面](https://www.h3c.com/en/Products_and_Solutions/InterConnect/Operating_System/Comware_V7)、[深信服 NGAF 技术白皮书](https://download.sangfor.com.cn/91b888ae9f7e4f50bb05265ddbbaf961.pdf)、[山石网科 2024 年年度报告摘要](http://star.sse.com.cn/disclosure/listedinfo/announcement/c/new/2025-03-28/688030_20250328_34G1.pdf)、[StoneOS Cookbook](https://netmarket.oss-cn-hangzhou.aliyuncs.com/365828b6bbfb4a52acd927a90d23e719.stoneos%E5%85%B8%E5%9E%8B%E9%85%8D%E7%BD%AE%E6%A1%88%E4%BE%8Bv5.5r10.pdf)。
> 这是「Unix 家族史」的**第五篇**（前四篇：起源与分裂 / 商业 Unix / BSD 家族 / BSD 代码流进了哪里）。
> 本文为**解读**。第三节关于「两种产品策略」的分析、第五节的判断是笔者补充的部分。

## 一句话结论

**把国外和国内放在一起看，会发现它们的差别不在技术上，而在**信息透明度**上。**

**国外厂商有一个共同习惯：它们会公开开源合规文档（Third Party Notices、OSS Listing）。** **而这个习惯有一个副作用：**它让我们能从法律声明反推底层内核**：

- **Citrix 有一份文件，标题直接就是「Third Party Notices for FreeBSD-based Products」，里面列着 `FreeBSD 11.4`。**
- **Cisco 的 IronPort AsyncOS 文档写着：「IronPort AsyncOS 内的某些软件依据 FreeBSD, Inc. 等的软件许可协议条款分发。」**
- **Juniper 官方文档写着：「在裸金属上的 Junos OS FreeBSD 10 或更新版本。这是基于升级后的 FreeBSD 内核的 Junos OS。」**
- **Palo Alto 的 PAN-OS OSS 清单里是 `bash`、`busybox`、RPM 体系，而这是典型的 RPM 系 Linux。**

**而国内厂商普遍不发布这类文档。** **所以对深信服、山石、天融信、锐捷、迪普，我们能得到的只有「官方称自研操作系统」，而**内核是什么，官方没有公开**。**

**唯一的例外是 H3C。** **它的官方页面直接写**：

> **「开放性：Comware V7 是一个通用的、基于 Linux 的开放系统。」**

**所以这一篇的结构是**：**先按产品类型把国外厂商的底层列清楚（有证据的才列），然后说国内的情况，最后解释为什么这个信息差存在。**

## 一、防火墙：BSD 最密集的一块

| 产品 | 厂商 | 底层 | 证据 |
|---|---|---|---|
| ⭐ **pfSense** | **Netgate** | **FreeBSD 14.x** | **厂商自己的产品定义** |
| ⭐ **OPNsense** | **Deciso** | **FreeBSD**，**2015 年从 pfSense 分叉** | **厂商自己的产品定义** |
| ⭐ **m0n0wall** | 社区（已停止） | **FreeBSD**，**是 pfSense 和 OPNsense 的共同祖先** | **Wikipedia 清单** |
| ⭐ **Check Point IPSO** | **Nokia → Check Point** | **FreeBSD 6 的分叉，带大量加固特性** | **Wikipedia + Check Point 发布说明** |
| **Cisco IronPort AsyncOS** | **Cisco** | **基于 FreeBSD 内核** | **Cisco 官方文档的许可证声明原文** |
| **McAfee SecurOS**（Firewall Enterprise / Sidewinder） | **McAfee** | **FreeBSD** | **Wikipedia 清单** |
| **Borderware 系列** | Borderware | **基于 FreeBSD 内核** | **Wikipedia 清单** |
| **Blue Coat 网络设备** | Blue Coat（现 Symantec） | **基于 FreeBSD** | **Wikipedia 清单** |

**而 IPSO 这一条有两个值得说的细节。**

**第一，它的血统可以追溯到很早**：**IPSO SB 最早是 Ipsilon Networks 从 `FreeBSD 2.1-STABLE` 派生的，然后在 `FreeBSD 2.2.6-RELEASE` 和 `3.5-RELEASE` 上交叉编译。** **而 IPSO 的「IP」指的是 Ipsilon Networks，那是一家做 IP 交换、1997 年被 Nokia 收购的公司。**

**第二，它有一个被埋没的技术首创**：**Wikipedia 列出的 IPSO 特性里有一条：「第一个走出 beta 测试的商业 IPv6 路由器（早于 Cisco 和 Juniper Networks）。」**

**⚠️ 而「Check Point 防火墙是 BSD」这个说法需要限定年代**：**IPSO 最后一版 6.2MR6 是 2017 年 2 月，而 Check Point 现在的主力是 Gaia，Gaia 是 RHEL 基座。** **所以这条线是「曾经是 BSD」，不是「现在是 BSD」。**

## 二、应用交付与负载均衡

| 产品 | 厂商 | 底层 | 证据 |
|---|---|---|---|
| ⭐ **NetScaler MPX / SDX** | **Citrix / Cloud Software Group** | **FreeBSD 11.4** | ⭐ **官方文档标题就是「Third Party Notices for FreeBSD-based Products」** |
| **Coyote Point GX 系列** | Coyote Point（后被 Fortinet 收购） | **FreeBSD** | **Wikipedia 清单** |

**NetScaler 这一条我认为是本文最硬的证据**，**因为厂商把「FreeBSD-based」写进了文件名。**

**⚠️ 但有一处必须精确化**：**NetScaler 有不同的形态，而 `BLX`（裸金属）形态「作为 Linux 进程运行」**，**官方文档列的支持系统是 CentOS、Oracle Linux、Ubuntu、RHEL、Amazon Linux。** **所以「NetScaler 是 FreeBSD」这句话对 MPX/SDX 硬件形态成立，对 BLX 不成立。**

## 三、网络设备与路由

| 产品 | 厂商 | 底层 | 备注 |
|---|---|---|---|
| ⭐ **Junos** | **Juniper** | **FreeBSD，且版本可逐代对应** | **见下表** |
| **LynxOS** | Lynx Software | **使用 FreeBSD 的网络栈** | **不是整块内核** |

**Junos 的版本演进线我认为很值得单独看，因为它是「一个厂商持续跟上游」的完整记录**：

| Junos 版本 | 基于 |
|---|---|
| **5.0 之前** | **FreeBSD 2.2.6** |
| **5.0 到 7.2** | **FreeBSD 4.2** |
| **7.3 起** | **FreeBSD 4.10** |
| **8.5** | **FreeBSD 6.1** |
| **15.1** | **FreeBSD 10** |
| **18.1** | **FreeBSD 11** |

**而 Juniper 现在的官方文档说「基于升级后的 FreeBSD 内核」，并把它列为一个独立的架构变体**：

> **「Junos OS 包括以下架构变体：在裸金属上的 Junos OS FreeBSD 10 或更新版本。这是基于升级后的 FreeBSD 内核的 Junos OS。大多数基于 Junos OS 的硬件平台运行带升级 FreeBSD 的 Junos OS。Junos OS 带升级 FreeBSD 也可以作为 guest 虚拟机跑在 Linux VM 宿主上。」**

**「也可以作为 guest 虚拟机跑在 Linux VM 宿主上」。** **这一句说明了一件有意思的事：Linux 和 BSD 在这个产品里不是竞争关系，而是分层关系。**

## 四、存储、CDN 与其他

| 产品 | 厂商 | 底层 | 备注 |
|---|---|---|---|
| **Isilon OneFS** | **EMC / Dell** | **FreeBSD** | **集群存储** |
| **Dell Compellent** | **Dell** | **FreeBSD** | **所有 64 位版本** |
| **Panasas** | Panasas | **FreeBSD** | **并行网络存储** |
| ⚠️ **TrueNAS CORE**（原 FreeNAS） | **iXsystems** | **FreeBSD** | ⚠️ **但已被放弃（abandoned），继任者 TrueNAS Scale 是 Debian 基座** |
| **QNAP QES** | **QNAP** | **FreeBSD** | — |
| **Spectra Logic nTier Verde** | Spectra Logic | **FreeBSD** | **备份设备** |
| **Sandvine 网络策略产品** | Sandvine | **FreeBSD** | — |
| ⭐ **Netflix Open Connect** | **Netflix** | **FreeBSD-CURRENT (HEAD)** | **官方公告页一手** |
| **Symmetricom 授时方案** | Symmetricom | **FreeBSD** | — |
| ⭐ **Panasonic Viera 电视** | **Panasonic** | **FreeBSD** | **用在电视接收机里** |
| **The Weather Channel IntelliStar** | TWC | **FreeBSD** | **本地天气预报计算机** |

**TrueNAS 那一条值得单独提示**：**它是「BSD 在存储领域退潮」的一个标志。** **因为 TrueNAS CORE（FreeBSD 基座）被放弃，而继任者 TrueNAS Scale 换成了 Debian Linux。** **所以这个品类里最有名的开源产品，已经从 BSD 转向 Linux 了。**

## 五、反例：几个常被误认为 BSD 的

**这一节我认为比列清单更重要，因为搞混的人很多。**

| 产品 | 实际底层 | 为什么容易搞混 |
|---|---|---|
| ⚠️ **F5 BIG-IP（TMOS）** | ⭐ **F5 自己的 TMOS**。**设备上确实跑着一个 Linux，但它只管命令行和 Web GUI** | **F5 白皮书专门澄清过** |
| **Palo Alto PAN-OS** | **Linux** | **OSS 清单里是 `bash`、`busybox`、RPM 体系** |
| **Fortinet FortiOS** | **Linux**（社区普遍认为） | **官方只说「FortiOS 是 Fortinet 的操作系统」，不披露内核** |
| **Cisco ASA** | **Linux**（一般认为） | — |
| **Xinuos OpenServer 10** | ⭐ **FreeBSD 10** | **这个**是** FreeBSD，但自 2018 年后无更新** |

**F5 那一条的澄清值得完整引用，因为它是最典型的坑**：

> **「许多人注意到，一台基于 TMOS 的设备上有一种运行着 Linux 的形式，用命令行管理设备时就能看到。重要的是，这个 Linux 系统不参与任何流经 TMOS 的流量。」**
>
> **「TMOS 有自己的专用 CPU、内存和系统总线来访问外围设备。当一台基于 TMOS 的设备收到数据包时，从网线到系统总线、从网络子系统到内存管理子系统，全部完全自包含在 TMOS 内部。Linux 从不参与也不知道这一切；连 Linux 内核都不参与。这个 Linux 系统只用于管理任务，比如命令行或 Web GUI。」**

**「Linux 从不参与也不知道这一切；连 Linux 内核都不参与。」** **所以 F5 的架构是「管理面用 Linux，数据面完全自研」。** **而这一点恰好和 H3C Comware V7 相反，我在下面会比较。**

## 六、国内厂商：普遍不披露，而 H3C 是例外

### H3C Comware V7：唯一一个官方直接写「基于 Linux」的

**这是国内厂商里最透明的一个，而证据来自 H3C 自己的英文技术页面**：

> **「开放性：Comware V7 是一个通用的、基于 Linux 的开放系统。」**
>
> **「基础设施平面提供基本的 Linux 服务和 Comware 支持功能。基本的 Linux 服务包括基本的 Linux 功能、C 语言库函数、数据结构操作和标准算法。」**
>
> **「Comware V7 基于 Linux 实现了完全的模块化。所有软件特性在不同空间里作为独立进程运行。一个进程失败不影响其他进程。Linux 线程使用的抢占式调度让 Comware V7 能够提供高速服务。」**
>
> **「此外，Linux 支持多核、多 CPU 和对称多处理（SMP）技术，可以最大化多 CPU 性能。」**

**而 H3C 的中文页面说得更直白，而且给出了演进史**：

> **「Comware V7 采用多进程的实现方式，实现了完全的模块化。使用 Linux 操作系统，使得网络操作系统从一个封闭的专用系统向更加通用、开放转变。」**
>
> **「Comware 发展到 V5 版本已经是一个非常完善的单进程多任务的网络操作系统，在非常广泛的网络设备上得到了应用。要更进一步发展，就是要实现完全的模块化，以解决单进程无法解决的问题；同时提高系统的开放性。Comware V7 就是为了解决这些问题开发的全新系统。」**

**「从一个封闭的专用系统向更加通用、开放转变」。** **这句话是 H3C 对自己 V5 到 V7 演进的定义**：**V5 是「单进程多任务的自研网络操作系统」，而 V7 是「基于 Linux 的多进程模块化系统」。** **所以这次转变不只是技术升级，也是把「封闭自研」换成了「Linux 底座 + 自研上层」。**

**而它的四平面划分说明了 Linux 在其中的位置**：**管理面、控制面、数据面、基础设施面**，**而 Linux 是基础设施面。**

**⚠️ 但要注意它和 F5 的区别**：**F5 是「Linux 只管管理，数据面完全自包含」；而 Comware V7 是「Linux 是底座，Comware 的各个功能（包括数据面）作为独立进程跑在 Linux 之上」。** **而这个差别意味着：Comware 的数据转发要经过 Linux 内核提供的基础设施（虽然可能是它改造过的），而 F5 的数据转发完全不经过 Linux。**

**而 H3C 还强调了另外两个基于 Linux 才成立的能力**：

> **「开放的接口：基于 Linux，Comware V7 为用户开发自己的功能提供开放的 API。」**
>
> **「TCL 脚本：Comware V7 内嵌了 TCL。」**

**「基于 Linux，提供开放的 API」。** **这句话说明「开放」这个卖点是 Linux 底座直接带来的**：**如果内核是封闭自研的，提供 API 的成本会高得多。**

### 深信服 Sangfor OS：自研并行操作系统，不披露内核

**深信服的白皮书对自己的架构描述得很具体，但完全没提内核是什么**：

> **「深信服下一代防火墙构筑在 64 位多核并发、高速硬件平台之上，采用自主研发的并行操作系统（Sangfor OS），将转发平面、安全平面并行运行在多核平台上。多平面并发处理，紧密协作，极大的提升了网络数据包的安全处理性能。」**

**而它给的架构细节是**：**控制平面**（**负责整个系统各平面、各模块间的监控和协调工作，包括配置存储、配置下发、控制台 UI、数据中心**）**和转发平面**（**「不仅采用了多核的硬件架构，在计算指令设计上还采用了先进的无锁并行处理技术，能够实现多流水线同时处理」**）。

**而它还有两个技术点值得记**：

> **「深信服 NGAF 采用单次解析架构实现报文的一次解析一次匹配……实现单次解析技术的一个关键要素就是软件架构设计实现网络层、应用层的平面分离，将数据通过『0』拷贝技术提取到应用平面上实现威胁特征的统一解析和统一检测。」**

> **「深信服利用多年积累的应用识别技术，在内核驱动层面通过私有协议将所有经过下一代防火墙的数据包都打上应用的标签。」**

**「在内核驱动层面通过私有协议……」这句话说了「内核驱动层面」，说明它有自己的内核驱动层，但它没有说是哪个内核。**

**而深信服的另一个公开动作间接透露了它的技术底子**：**2023 年 12 月，它向 openEuler 捐赠了一个工具 `Sangfor chaosArsenal`，而官方描述是「一款在 Linux 系统下通用的可靠性测试工具」。** **⚠️ 但这一点只能说明深信服有 Linux 技术积累，不能证明 Sangfor OS 的内核是 Linux。**

**所以准确的结论是**：**深信服明确说自己是「自主研发的并行操作系统」，而它没有公开内核来源。** **从「多核无锁并行」「平面分离」这些特征看，它的形态更像「自研转发引擎 + 某种通用内核（可能是 Linux，可能是改造过的）」，但这一点我无法证实。**

### 山石网科 StoneOS：自研，2007 年诞生，不披露内核

**山石的年报公告里的表述很明确**：

> **「Stone OS 自研软件持续更新；陆续发布 Stone OS 5.5R11 系列等 27 个版本」**

**而它的宣传材料说**：「**山石网科正式发布 自研安全操作系统新版本-StoneOS 5.5R12**」，**以及「StoneOS 自2007年诞生以来，历经近二十载打磨」。**

**而 StoneOS 的配置手册里有两个细节值得注意，但它们都不能证明内核**：

**① 它支持用 Linux 上的 NETCONF 客户端连设备**：**Cookbook 里的例子是「在 Linux 中启动 `netopeer2-cli` 客户端连接 StoneOS 设备」。** **这只是说明它实现了标准 NETCONF 协议。**

**② 它的调优命令暗示了多核转发架构**：**Cookbook 里有「使用 `flow-core-num` 命令，指定系统数据层面占用 CPU 核的数量」，以及「将日志处理进程和数据库存储进程绑定至 Core MAX（系统中最大编号的 CPU 核）」。** **这种「数据面独占核 + 管理进程绑最后一个核」是典型的 DPDK/多核转发调优方式，而这种架构在 Linux 上最常见，但它同样可以在自研内核上实现。**

**而山石的「信创」动作值得单独说，因为它解释了「自研」这个标签为什么重要**：

> **「持续布局信创市场；新增发布信创分布式防火墙 K20803，盒式信创防火墙 K7680、K7280 和 K6680，依托 Hillstone Mars（FPGA 芯片）硬件加速引擎」**

**「信创分布式防火墙」「信创款型」。** **而在信创的语境里，「自研 OS」这个表述的价值高于「基于 Linux 改造」。**

### 其他三家：证据更少

| 厂商 | OS 名称 | 官方口径 | 内核 |
|---|---|---|---|
| **天融信** | **TopOS / TOPSEC** | 宣传材料提「智能策略编排、全流量威胁检测引擎，支持AI驱动的未知威胁防御」 | **未披露** |
| **锐捷** | **RGOS**（锐捷通用操作系统） | ⚠️ **「模块化设计、高可用性和开放性」「对硬件平台透明，兼容性高」，11.x 平台** | **未披露** |
| **迪普科技** | **ConPlat** | 材料极少，只提「自研」 | **未披露** |

**⚠️ 锐捷那两条出处是搜狐和 CSDN 的自媒体与博客，不是锐捷官方文档，所以我对它们的引用要打折扣。** **而迪普我基本没查到任何官方技术文档，所以不能给判断。**

## 七、为什么会有这个信息差

**我认为这不是技术问题，是三个结构性原因叠加的结果。**

**① 开源合规是法律要求，而它只对「用了 GPL/BSD 代码并对外分发」的厂商构成压力。** **国外厂商（Citrix、Cisco、Juniper、Palo Alto）都发布了 Third Party Notices 或 OSS Listing，因为这些是它们法务流程的一部分。** **而国内厂商普遍没有发布这类文档的习惯**，**而没有这类文档，就无法从法律声明反推内核。**

**② 「自研」这个标签在特定市场里有独立的商业价值。** **山石反复强调「自研安全操作系统」，而它的信创产品线把「自研」和「自主可控」绑在一起。** **在这个语境下，「我用 Linux 改的」会削弱叙事**，**而「基于 Linux 的通用开放系统」这种表述（H3C 的路线）在另一个市场（运营商、互联网）反而是优势。**

**③ 技术保密。** **数据面转发引擎的架构是这类产品的核心竞争点，而披露「内核是什么」会连带暴露「哪些是自己做的、哪些是拿来的」。**

**而我认为值得注意的是**：**这三条里，只有第一条是「透明度」问题，后两条是「策略」问题。** **所以「国内厂商不披露内核」不等于「它们藏了什么」，更可能是「披露对它没有好处」。**

## 八、我的判断

**第一，这一篇最该被记住的不是清单，而是「证据强度分级」这件事。** **因为同一句「某产品基于 FreeBSD」，可能有三种完全不同的支撑**：**① 厂商官方文档直接写明（Citrix、Juniper、Cisco）；② 厂商的开源合规文档间接透露（PAN-OS 的 OSS 清单）；③ 第三方清单收录而无厂商确认（Wikipedia 上那些）。** **⚠️ 而 Wikipedia 那份清单里，有几条明确标了 `[citation needed]`（比如 KACE 和 Spectra Logic），说明连维基都不确定。** **所以引用这类清单时，「谁说的」比「说了什么」更重要。**

**第二，H3C 那条路线值得单独表扬，因为「承认用 Linux」在国内是个需要勇气的表述。** **因为它在营销上会失去「完全自研」的叙事，而它换来的是**：**开放 API、TCL 脚本、多核 SMP 调度、进程隔离**。 **H3C 的官方表述是「从一个封闭的专用系统向更加通用、开放转变」，而我认为这个表述是准确的：它没有说「我们自研了一个更好的内核」，它说的是「我们把底座换成了通用的，把力气花在上层」。** **这个取舍我认为是诚实的，而且技术上也更可持续**，**因为内核那部分的维护成本可以随 Linux 主线分摊，而厂商自己的力气集中在网络功能上。**

**第三，F5 和 H3C 的对比，是这一篇里最有技术含量的一处。** **两者都是「Linux + 自研」，但**Linux 的位置完全相反**：**F5 的 Linux 只管管理面，数据面完全自包含在 TMOS 里；H3C 的 Linux 是底座，连数据面也是跑在它上面的进程。** **而这两种设计的后果不同**：**F5 的数据面不受 Linux 内核任何限制（也不受它的 bug 影响），但代价是完全自研；H3C 的数据面可以复用 Linux 的基础设施（驱动、内存管理、多核调度），但代价是要跟内核的演进节奏。** **我认为这个对比比「谁的内核是什么」更有信息量，因为它是「同一个技术选择在两种位置下的两种后果」。**

**第四，关于国内厂商，我想给出一个诚实的结论，而不是一个猜测。** **我能确认的只有一件事：它们**没有公开**内核来源。** **而「没有公开」和「不是 Linux」是两件不同的事。** **从技术常识看，一个从头写内核、还要支持多核无锁转发、还要兼容大量网络协议栈的系统，其工程量远超一般厂商的投入能力**，**所以「改造过的 Linux + 自研转发引擎」是更可能的形态。** **⚠️ 但这是推断，不是我核实的结论，我在正文里也一直标注「内核未披露」。**

**第五，关于「信创」这个角度，我想避免一个常见的推断错误**：**「信创」不等于「自研内核」。** **麒麟、统信这些国产操作系统的内核也都是从 Linux 主线派生的（它们是发行版，不是新内核）。** **而网络设备厂商的 OS 同理**：**即使它叫「自研 OS」，内核层也很可能是 Linux 或改造过的 Linux。** **所以「自主可控」在这个语境里的真实含义，通常是「代码可审计、供应链不受制于单一国外厂商」，而不是「从零写了一个内核」。**

> **最后一个实操建议，关于「怎么自己验证」**：**如果你能拿到一台这类设备的 shell（有些设备提供受限 CLI，有些则完全没有），三条命令就能给出答案**：
>
> **① `uname -a`**、**② `cat /proc/version`**、**③ `ls /proc/config.gz`（如果有，`zcat` 出来就是内核配置）**。
>
> **而 `/proc` 这个目录本身的存在，就是「内核是 Linux（或类 Linux）」的强证据**，**因为 `/proc` 是 Linux 特有的伪文件系统设计。** **而如果一台设备上完全没有 `/proc`，那它大概率不是 Linux。**
>
> **这个做法在授权测试里是标准的。而我要提醒的是：在没有授权的情况下探测这类命令，可能违反设备的使用条款。**

## 关键事实速查

### 防火墙（BSD 最密集的一块）

| 产品 | 厂商 | 底层 | 证据强度 |
|---|---|---|---|
| ⭐ **pfSense** | **Netgate** | **FreeBSD 14.x** | **厂商定义** |
| ⭐ **OPNsense** | **Deciso** | **FreeBSD**，**2015 从 pfSense 分叉** | **厂商定义** |
| **m0n0wall** | 社区（已停止） | **FreeBSD**，**pfSense 与 OPNsense 的共同祖先** | **第三方清单** |
| ⭐ **Check Point IPSO** | **Nokia → Check Point** | **FreeBSD 6 的分叉，带大量加固** | **Wikipedia + 发布说明** |
| **Cisco IronPort AsyncOS** | **Cisco** | **基于 FreeBSD 内核** | ⭐ **官方文档许可证声明** |
| **McAfee SecurOS** / Sidewinder | McAfee | **FreeBSD** | **第三方清单** |
| **Borderware 系列** | Borderware | **基于 FreeBSD 内核** | **第三方清单** |
| **Blue Coat 设备** | Blue Coat / Symantec | **FreeBSD** | **第三方清单** |

**IPSO 补充**：**IPSO SB 最早由 Ipsilon Networks 从 `FreeBSD 2.1-STABLE` 派生，在 `FreeBSD 2.2.6-RELEASE` 与 `3.5-RELEASE` 上交叉编译**；**最后一版 IPSO 6.2MR6 是 2017 年 2 月**；**⚠️ 现在 Check Point 主力是 Gaia，而 Gaia 是 RHEL 基座**；**IPSO 有个首创：「第一个走出 beta 测试的商业 IPv6 路由器，早于 Cisco 和 Juniper」**。

### 应用交付

| 产品 | 厂商 | 底层 |
|---|---|---|
| ⭐ **NetScaler MPX / SDX** | **Citrix / Cloud Software Group** | **FreeBSD 11.4**（⭐ **官方文档标题即「Third Party Notices for FreeBSD-based Products」**） |
| **Coyote Point GX** | Coyote Point → Fortinet | **FreeBSD** |

**⚠️ NetScaler 的 `BLX`（裸金属）形态不同**：**「作为 Linux 进程运行」，支持 CentOS / Oracle Linux / Ubuntu / RHEL / Amazon Linux**。

### 网络与路由

| Junos 版本 | 基于 |
|---|---|
| **5.0 之前** | **FreeBSD 2.2.6** |
| **5.0 到 7.2** | **FreeBSD 4.2** |
| **7.3 起** | **FreeBSD 4.10** |
| **8.5** | **FreeBSD 6.1** |
| **15.1** | **FreeBSD 10** |
| **18.1** | **FreeBSD 11** |

**Juniper 官方现行表述**：**「在裸金属上的 Junos OS FreeBSD 10 或更新版本……基于升级后的 FreeBSD 内核」**；**「也可以作为 guest 虚拟机跑在 Linux VM 宿主上」**。**LynxOS 只用了 FreeBSD 的网络栈，不是整块内核。**

### 存储 / CDN / 其他

| 产品 | 厂商 | 底层 |
|---|---|---|
| **Isilon OneFS** | **EMC / Dell** | **FreeBSD** |
| **Dell Compellent** | **Dell** | **FreeBSD**（所有 64 位版本） |
| **Panasas** | Panasas | **FreeBSD** |
| ⚠️ **TrueNAS CORE**（原 FreeNAS） | **iXsystems** | **FreeBSD，但已放弃；继任 TrueNAS Scale 是 Debian** |
| **QNAP QES** | QNAP | **FreeBSD** |
| **Spectra Logic nTier Verde** | Spectra Logic | **FreeBSD**（清单标 `[citation needed]`） |
| **Sandvine** | Sandvine | **FreeBSD** |
| ⭐ **Netflix Open Connect** | **Netflix** | **FreeBSD-CURRENT (HEAD)** |
| **Symmetricom** | Symmetricom | **FreeBSD** |
| ⭐ **Panasonic Viera 电视** | **Panasonic** | **FreeBSD** |
| **TWC IntelliStar** | The Weather Channel | **FreeBSD** |

### 反例：不是 BSD 的

| 产品 | 实际底层 | 关键证据 |
|---|---|---|
| ⚠️ **F5 BIG-IP（TMOS）** | ⭐ **F5 自研 TMOS；Linux 只管管理面** | **F5 白皮书：「Linux 从不参与也不知道这一切；连 Linux 内核都不参与。」** |
| **Palo Alto PAN-OS** | **Linux** | **OSS 清单是 `bash`/`busybox`/RPM 体系** |
| **Fortinet FortiOS** | **Linux**（社区共识） | **官方不披露内核** |
| **Cisco ASA** | **Linux**（一般认为） | — |
| **Xinuos OpenServer 10** | ⭐ **FreeBSD 10** | **但 2018 年后无更新** |

### 国内厂商

| 厂商 | OS 名称 | 官方口径 | 内核 |
|---|---|---|---|
| ⭐ **H3C** | **Comware V7** | ⭐ **「Comware V7 是一个通用的、基于 Linux 的开放系统」** | ✅ **Linux（官方明示）** |
| **H3C 的演进** | **V5 → V7** | **「V5 是非常完善的单进程多任务网络操作系统」→ V7「使用 Linux 操作系统，使得网络操作系统从一个封闭的专用系统向更加通用、开放转变」** | — |
| **H3C 的架构** | **四个平面** | **管理面、控制面、数据面、基础设施面**（**Linux 是基础设施面**） | — |
| **H3C 的能力** | — | **多进程模块化、进程隔离、抢占式调度、多核/多 CPU/SMP、开放 API、内嵌 TCL** | — |
| **深信服** | **Sangfor OS** | **「自主研发的并行操作系统」** | ⚠️ **未披露** |
| **深信服架构** | — | **控制平面 + 转发平面；「无锁并行处理技术」「多流水线同时处理」；「单次解析架构」「0 拷贝」「内核驱动层面通过私有协议打标签」；Sangfor Regex 引擎** | — |
| **深信服的旁证** | — | **2023-12 向 openEuler 捐赠 `Sangfor chaosArsenal`，「一款在 Linux 系统下通用的可靠性测试工具」**（⚠️ **只证明 Linux 积累，不证明内核**） | — |
| **山石网科** | **StoneOS** | **「自研安全操作系统」**，**2007 年诞生** | ⚠️ **未披露** |
| **山石的版本** | — | **2024 年发布 5.5R11 系列等 27 个版本**；**5.5R12 于 2025-10 发布** | — |
| **山石的旁证** | — | **Cookbook 里用 Linux 上的 `netopeer2-cli` 连设备（NETCONF）**；**`flow-core-num` 与 Core MAX 绑定（多核转发调优）** | — |
| **山石的信创** | — | **信创分布式防火墙 K20803、盒式 K7680/K7280/K6680**；**依托 Hillstone Mars FPGA** | — |
| **天融信** | **TopOS / TOPSEC** | **提智能策略编排、全流量威胁检测** | ⚠️ **未披露** |
| **锐捷** | **RGOS** | **「模块化设计、高可用性、开放性」「对硬件平台透明」，11.x 平台**（⚠️ **出处是自媒体/博客，非官方**） | ⚠️ **未披露** |
| **迪普科技** | **ConPlat** | **材料极少** | ⚠️ **未披露** |

### 为什么有信息差

| 原因 | 说明 |
|---|---|
| **① 开源合规是法律要求** | **国外厂商把 Third Party Notices 当法务流程，而这恰好让底层可被反推；国内厂商普遍不发布** |
| **② 「自研」在特定市场有商业价值** | **山石反复强调「自研」，而信创语境下「自主可控」与「自研」绑定** |
| **③ 技术保密** | **数据面架构是核心竞争点，披露内核会连带暴露「哪些是自研、哪些是拿来的」** |

### 自己验证的方法

| 命令 | 为什么有效 |
|---|---|
| **`uname -a`** | **直接给内核名与版本** |
| **`cat /proc/version`** | **同上的另一条路径** |
| **`ls /proc/config.gz`** | **有的话 `zcat` 出来就是内核配置** |
| ⭐ **`/proc` 目录本身存在与否** | **`/proc` 是 Linux 特有的伪文件系统；完全没有 `/proc` 的设备大概率不是 Linux** |
| ⚠️ **前提** | **只能在授权测试中使用，未授权探测可能违反使用条款** |

## 延伸阅读

- [BSD 的代码流进了哪里：你以为它是小众，但它可能就在你的游戏机、路由器和 NAS 里](https://freelamp.com/articles/2026-10-21_bsd-code-in-proprietary-products/)
- [BSD 家族全表：四个正统、一个桌面发行版，以及「UNIX 认证」这件事的真相](https://freelamp.com/articles/2026-10-21_bsd-family-2026-freebsd-openbsd-netbsd-ghostbsd/)
- [商业 Unix 只剩一个还在开发：HP-UX 刚刚断线，而它死于一枚停产的 CPU](https://freelamp.com/articles/2026-10-21_commercial-unix-2026-aix-hpux-solaris-status/)
- [Unix 为什么会分裂成两个阵营：而答案不在技术里，在 1956 年的一份反垄断同意令里](https://freelamp.com/articles/2026-10-21_unix-history-origins-system-v-bsd-split/)
- [H3C Comware V7 官方技术页面（一手）](https://www.h3c.com/en/Products_and_Solutions/InterConnect/Operating_System/Comware_V7)
- [Citrix 的 FreeBSD Third Party Notices（一手）](https://www.citrix.com/content/dam/citrix/en_us/documents/downloads/netscaler-adc/NetScaler_ADC_ADM_FreeBSD_13.1_Third_Party_Notices.pdf)
