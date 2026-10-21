---
title: "BSD 家族全表：四个正统、一个桌面发行版，以及「UNIX 认证」这件事的真相"
date: 2026-10-21
slug: bsd-family-2026-freebsd-openbsd-netbsd-ghostbsd
tags: [BSD, FreeBSD, OpenBSD, NetBSD, DragonFly BSD, GhostBSD, macOS, XNU, pfSense, OPNsense, TrueNAS, CheriBSD, UNIX 认证, Open Group, 浪潮 K-UX, 华为 EulerOS, 4.4BSD-Lite]
category: 系统/硬件
author: FreeLAMP.com
original_source: "FreeBSD/OpenBSD/NetBSD/DragonFly/GhostBSD 官网 + Open Group 官方注册表与合规声明书"
original_author: "各 BSD 项目；The Open Group"
original_date: 2026-10-21
original_url: "https://www.freebsd.org/where/"
description: "BSD 这一层是 Unix 家族里活得最健康的一批，但它们的区别经常被敷衍过去。本文把四个正统（FreeBSD 要通用、NetBSD 要硬件覆盖、OpenBSD 要安全、DragonFly 要可伸缩性）加 GhostBSD 摆在一起对比，补上真正被大量部署的专用发行版（pfSense、TrueNAS、CheriBSD），并揭开「UNIX 认证」的真相：浪潮 K-UX 和华为 EulerOS 这两个 RHEL 衍生版拿到了 UNIX 03 认证，而真正有 AT&T 血统的 FreeBSD 没买。"
published: true
---

> 来源：本文的版本号与日期**逐个回到官方页面核对**：[FreeBSD 发布页](https://www.freebsd.org/where/)与[发布工程排期](https://www.freebsd.org/releng/)、[OpenBSD 官网](https://www.openbsd.org/)、[NetBSD 官网](https://www.netbsd.org/)、[DragonFly BSD 官网](https://www.dragonflybsd.org/)、[GhostBSD 官网](https://www.ghostbsd.org/news)、[Open Group 的 UNIX 认证注册表](https://www.opengroup.org/openbrand/register)与 [Inspur 的合规声明书](https://www.opengroup.org/openbrand/register/brand3617.htm)。
> 这是「Unix 家族史」的**第三篇**（原第三篇的商业 Unix 部分已独立成篇）。第一篇讲起源与分裂，第二篇讲商业 Unix 的现状。**⚠️ 所有版本号与日期均以官方页面为准。**
> 本文为**解读**。第三节关于「UNIX 认证证明什么」的分析、第五节的判断是笔者补充的部分。

## 一句话结论

**如果把「Unix 系」按血统和认证分成四层，BSD 这一层是最容易混淆、但活得最健康的**：

| 层 | 判定标准 | 这一篇讲谁 |
|---|---|---|
| **① 有 AT&T 源码血统 + 有 Open Group UNIX 认证** | **法律和血统双重的「真 Unix」** | **macOS（认证真实，但血统混合）** |
| ⚠️ **② 有认证但血统是 Linux** | **浪潮 K-UX、华为 EulerOS** | **它们是最反直觉的一批：基于 RHEL 却拿到了 UNIX 商标** |
| ⭐ **③ 有血统但无认证** | **BSD 四家 + GhostBSD 等衍生版** | **本篇主体：FreeBSD / NetBSD / OpenBSD / DragonFly / GhostBSD** |
| **④ Unix-like（按接口实现，无血统无认证）** | **Linux 系** | **不在本篇范围** |

**而我认为这张表最该被看的是第二层，因为它是「认证」这件事最大的漏洞**：**浪潮的 K-UX 和华为的 EulerOS 都是 RHEL 衍生版，而它们都拿到了 UNIX 03 认证，因此有权使用 UNIX 商标。** **这一条直接把「认证」和「血统」切开，而它是我们讨论「谁更 Unix」时最容易忽略的事实。**

## 一、四个正统加一个桌面发行版：这一层活得最健康

**这一节我要先讲一个判定框架，因为 BSD 这一层最容易被混为一谈。**

### FreeBSD：15.1 是当前生产版，而 16.0 排在 2027 年 12 月

**FreeBSD 的版本策略是三档并行，官方页面写得很清楚**：

| 档位 | 当前版本 | 发布日期 |
|---|---|---|
| ⭐ **Production（生产）** | **FreeBSD 15.1-RELEASE** | **2026 年 6 月 16 日** |
| **Legacy Production** | **15.0**（2025-12-02）、**14.5**（2026-09-08）、**14.4**（2026-03-10） | — |
| **Upcoming** | **14.6**、**15.2** | — |

**而发布工程页给了未来的排期，这一条很值得看**：

| 时间 | 事件 |
|---|---|
| **2026 年 12 月** | **FreeBSD 15.2** |
| **2027 年 3 月** | **FreeBSD 14.6** |
| **2027 年 6 月** | **FreeBSD 15.3** |
| ⭐ **2027 年 12 月** | **FreeBSD 16.0** |
| **2028 年 12 月** | **FreeBSD 16.2** |

**「16.0 排在 2027 年 12 月」。** **也就是说 FreeBSD 的大版本节奏是「约两年一个」，而小版本是「约半年一个」。**

**而 15.0 那次发布的技术内容值得记一笔，因为它是「认证等级」的东西**：

> **「FreeBSD 现在有了原生的 inotify 实现」**
> **「OpenZFS 升级到 2.4.0-rc4」**
> **「OpenSSL 升级到最新的长期支持版 3.5.4，它包含对 QUIC 的支持，以及现在标准化的抗量子算法 ML-KEM、ML-DSA 和 SLH-DSA」**

**「ML-KEM、ML-DSA、SLH-DSA」。** **这三个都是 NIST 在 2024 年标准化的后量子算法。** **所以 FreeBSD 在 2025 年底就已经把后量子密码学放进了基础系统，而这个节奏比很多商业发行版都快。**

### OpenBSD：61 个版本，和一句「三十多年只有两个远程漏洞」

**OpenBSD 8.0 是 2026 年 10 月 20 日发布的，第 61 个版本。**

**而 Theo de Raadt 的那句话是这一节的核心**（**IPv6.net 引述他在公告邮件列表里的说法**）：

> **「我们为 OpenBSD 的记录感到自豪：三十多年里，默认安装只有两个远程漏洞。」**

**「三十多年里，默认安装只有两个远程漏洞」。** **这句话的分量需要理解它的限定词**：**「默认安装」意味着「不装任何额外服务」，**而那个限定条件是关键的，**因为 OpenBSD 一旦跑起 httpd、smtpd 这些，攻击面就变了。**

**而 8.0 的技术内容我在另一篇里详细写过，这里只列关键几条**：

- **amd64 内核虚拟地址空间从 4G 提到 512G**（**允许映射超过 4GB 的显存**）
- **Intel Arc A 系列（DG2/Alchemist）显卡支持**
- ⭐ **arm64 加入休眠支持**
- **新增 RPKI 到路由器的守护进程 `rtrd(8)`**
- **RISC-V：内核支持 'V' 向量扩展、支持高级中断架构**
- **每 guest 最多 64 个虚拟 CPU**
- **LibreSSL 4.4.0、OpenSSH 10.6**

**而 OpenBSD 官网有一句自我定位，我认为值得原样引用**：

> **「OpenBSD 项目产出一个免费的、多平台的、基于 4.4BSD 的类 UNIX 操作系统。我们的努力强调可移植性、标准化、正确性、主动安全和集成密码学。」**
>
> **「作为一个 OpenBSD 影响力的例子：流行的 OpenSSH 软件来自 OpenBSD。」**

**「OpenSSH 来自 OpenBSD」。** **这句话是 OpenBSD 最实在的遗产**：**今天全世界每一台 Linux 服务器上的 sshd，源头都在这里。**

### NetBSD：11.0 是 2026 年 7 月，而它的定位是「可移植」**

**NetBSD 官网的公告**：**「NetBSD 项目高兴地宣布 NetBSD 11.0，NetBSD 的第十九个大版本。NetBSD 11.0，2026 年 7 月 30 日发布。」**

**而近期版本线**：

- **11.0**：**2026 年 7 月 30 日**
- **10.2**：**2026 年 9 月 15 日**
- **9.5**：**而 netbsd-9 分支在 2026 年 8 月 31 日 EOL**

**「19 个大版本」。** **而从 1993 年到现在，33 年 19 个版本，平均不到两年一个。**

**NetBSD 的定位和另外两家不同，而我认为它最该被理解的一句话是它的口号**：**「Of course it runs NetBSD」。** **而这句话背后的技术事实是：NetBSD 支持非常多的 CPU 架构**，**这既是它的骄傲，也是它资源分散的原因。**

### macOS：版本号改成年份制了，而 Intel 正在退场

**这一条是 BSD 层里商业上最成功的，而它的版本号变化很容易让人困惑。**

**macOS 版本历史页的关键记录**：

> **「2025 年，Apple 统一了所有产品的版本号，包括它的其他操作系统，改为以 WWDC 宣布之后的年份来命名，从 macOS 26 Tahoe 开始，它于 2025 年 9 月 15 日发布。」**

**也就是说：macOS 的版本号从 15 Sequoia 直接跳到了 26 Tahoe。** **这不是笔误，是刻意的「车型年式」式命名。**

**而 26 Tahoe 的两条要点**：

> **「Tahoe 是最后一个支持 Intel 处理器的 macOS 版本。」**

**而下一个版本**：

> **「macOS 27 Golden Gate 在 WWDC26（2026 年 6 月 8 日）宣布，2026 年 9 月 14 日发布。它要求 M 系列处理器（macOS 27 不支持 Intel 处理器）。」**

**「macOS 26 是最后一个支持 Intel 的版本，而 27 要求 M 系列」。** **这是 Apple 从 2020 年宣布转向自研芯片以来，六年后的最后一步。**

**而 macOS 的 Darwin 版本号对应关系，对做兼容性判断的人有用**：

| macOS | Darwin |
|---|---|
| **macOS 14 Sonoma** | **23** |
| **macOS 15 Sequoia** | **24** |
| **macOS 26 Tahoe** | **25** |
| **macOS 27 Golden Gate** | **27** |

**注意 26 对应 25，而 27 对应 27。** **这个错位是因为 macOS 26 跳号时 Darwin 没跟着跳。** **所以「Darwin 23 = macOS 14」这个映射不能线性外推，**这一点在写脚本判断系统版本时是个坑。**

### ⚠️ 「UNIX 认证」确实存在，而它证明的东西比你想象的少

**前面几节里我们反复提到「Open Group 认证」，而这个问题需要单独讲清楚，因为它最容易被神化。**

**认证真的存在，而且有官方公开的注册表。** **The Open Group 的原话是**：

> **「UNIX 认证为识别开放操作系统提供了一个厂商中立、高度受认可、全球性的基准。只有完全符合并通过 Single UNIX Specification 认证的系统，才有资格使用 UNIX 商标。」**

**注册表是公开可查的（`opengroup.org/openbrand/register`），而它现在的条目很少**。**我读了注册表，UNIX 03 和 UNIX V7 两个档位下的产品加在一起，主要就是这几家**：

- **IBM：AIX 7（7.2 TL5 或更新）、AIX 7.1 TL5 / 7.2 TL2、AIX 6.1.2、AIX 5L 5.3**
- **IBM：z/OS 3.1 与 z/OS V2R1**
- **HPE：HP-UX 11i V3（B.11.31）on HP Integrity**
- **The SCO Group：UnixWare 7.1.3、SCO OpenServer 5 与 6**
- **Apple：OS X 10.11 El Capitan 等**

**而这里就是最重要的发现**。

### 那个认证最反直觉的例子：两家中国公司的「Unix」

**注册表里有一条记录，它彻底说明了「认证」和「血统」是两件事**：

> **公司名：Inspur Co., Ltd**
> **产品名：Inspur K-UX 3.0**
> **环境：on Inspur TS K1 system**
> **注册日期：2016 年 2 月 3 日**
> **有效期至：2019 年 2 月 3 日**

**浪潮（Inspur）的 K-UX，拿到了 UNIX 03 认证。**

**而它是什么？** **The Open Group 2013 年的新闻稿说得很清楚**：

> **「The Open Group 今天宣布，浪潮，中国领先的云计算解决方案提供商，成为第一家拥有通过 The Open Group UNIX 03 标准认证产品的中国公司。」**
>
> **「该公司开发了一个专有操作系统，设计为符合 UNIX 03 标准，用于高端服务器。」**

**「专有操作系统」。** **而技术事实是**：**K-UX 是基于 Red Hat Enterprise Linux 的 Linux 发行版。**

**而这件事的证据不在传闻里，在 Open Group 自己的**合规声明书**（Conformance Statement）里**。**K-UX 2.0 的那份声明列了它满足的四个强制标准，而其中第三条是**「C Language V2」**，**而声明里注明标准 C 编译器来自 GCC。**

**「标准 C 编译器来自 GCC」加「Red Hat 家族树里的 Linux 发行版」。** **所以结论是明确的**：**一个 RHEL 衍生版，通过了 UNIX 03 认证，因此有权使用 UNIX 商标。**

**而这不是孤例。华为的 EulerOS 也做了同样的事**。**Huawei 2016 年 9 月 9 日的新闻稿标题就是**：**「华为昆仑 EulerOS 2.0 操作系统通过 UNIX 认证」**。**而 EulerOS 同样是基于 RHEL 的企业 Linux 发行版。**

**所以现在我们能回答那个问题了**：

**「Unix 认证」是真的，但它的含义是「这个产品通过了一套一致性测试，因此有权使用 UNIX 商标」，而不是「这个产品含有 AT&T 的代码」。**

**这两件事的区别，用浪潮 K-UX 和华为 EulerOS 就能一句话说清**：**两个 RHEL 衍生版通过努力实现 POSIX/SUS 接口，拿到了 UNIX 商标使用权。** **而反过来，FreeBSD 那种真正有 AT&T 代码血统的系统，没有买这个认证。**

### 那这个认证重要吗：分三种人回答

**我认为它的重要性完全取决于你是谁，而这一点很少被说清。**

**① 对采购方：在特定招标里有意义。** **Open Group 自己就是这么定位的**：**「这使买方能够在采购中指定 UNIX 符合性。」** **而这一条在中国市场尤其真实**：**浪潮和华为去做这个认证，最直接的动机就是「在政府采购和金融、电信招标里可以说自己是 Unix」。** **因为招标文件里可能就写着「要求 UNIX 操作系统」。**

**② 对开发者：几乎没有意义。** **因为你要的东西（POSIX 接口、shell 行为、命令语义）是靠**测试套件**保证的，而实际使用中你测的是行为，不是证书。** **一个没认证的系统可能比认证过的更符合你的需要。**

**③ 对「Unix 血统」这个话题：完全无意义，而且会误导。** **因为认证只测接口，不测代码来源。** **所以用认证来判断「谁更 Unix」，会得到浪潮 K-UX 比 FreeBSD 更 Unix 这种荒谬结论。**

**而我认为这一节最该被记住的是那个机制**：**认证是一份**有时间期限的商标许可**（K-UX 3.0 的有效期是 2016-02-03 到 2019-02-03，三年），**而代码血统是永久的**。** **所以「认证」会过期，「血统」不会。** **这两件事的性质完全不同，而把它们混在一起讨论，是「Unix 是不是死了」这类争论混乱的根源。**

### BSD 之间的区别：这一层最容易被敷衍过去

**这一节要讲的是：BSD 这一层的家族比「FreeBSD/OpenBSD/NetBSD」三家要复杂，而它们的区别是有实际后果的。**

**先把「四个正统」的分工说清**：

| 项目 | 起始 | 它要解决的问题 | 结果 |
|---|---|---|---|
| **FreeBSD** | **1993** | **在 PC 上做一个完整、通用的 Unix 系统** | **份额最大，生态最全，商业采用最多**（**Netflix、WhatsApp 都用过它做网络栈**） |
| **NetBSD** | **1993** | **「尽可能多的硬件平台」** | ⭐ **口号是「Of course it runs NetBSD」，支持极多 CPU 架构** |
| **OpenBSD** | **1995**（**从 NetBSD 分叉**） | **「正确性和主动安全」** | ⭐ **「三十多年里，默认安装只有两个远程漏洞」**；**OpenSSH 的源头** |
| **DragonFly BSD** | **2004-07-12**（**从 FreeBSD 4.8 分叉**） | ⭐ **「从完全不同的方向生长」**（**官方原话**），**追求最大可伸缩性** | **6.4.2（2025-05-09）**；**HAMMER2 文件系统、NVMM 虚拟化** |

**DragonFly 的分叉动机值得单独说，因为它是一次真正的技术分歧**：**它由 Matt Dillon 从 FreeBSD 4.x 分出来，核心争议是「SMP 和内核并发模型该怎么设计」。** **而它官方那句自我定位很坦诚**：「**DragonFly 为 BSD 基础提供了一个从 FreeBSD、NetBSD 和 OpenBSD 系列所走方向完全不同的方向生长的机会。**」

**然后是那个我们漏掉的：GhostBSD。**

**GhostBSD 最新版本是 26.1-R15.0p2，2026 年 4 月 18 日发布。** **而它的官方公告说得很直接**：

> **「这个版本标志着一个重要里程碑，因为 GhostBSD 迁移到 FreeBSD 15.0-RELEASE，带来了最新的上游改进，包括增强的硬件支持、安全更新和内核进步。」**

**它的定位是**：**「基于 FreeBSD 的 Unix-like 操作系统，为 x86-64 架构，以 MATE（此前是 GNOME）为默认桌面环境，另有基于 Xfce 的社区版本。它致力于易于安装、开箱即用、易于使用。」**

**而它的历史有一段反复，我认为很有教育意义**：

> **「在 GhostBSD 18.10 之前，这个项目基于 FreeBSD。2018 年 5 月宣布，操作系统的未来版本将基于 TrueOS。2020 年，随着 TrueOS 停止，GhostBSD 切换回 FreeBSD。」**

**「基座换了两次」。** **18.10 到 21.01.20 之间它跑在 TrueOS 上，而 TrueOS 在 2020 年停止，于是它又回到 FreeBSD。** **而这件事的教训是**：**一个「桌面发行版」的命运，取决于它选择的底层项目是否还活着。** **GhostBSD 活得下来的原因是它及时退回了 FreeBSD，而不是继续跟着 TrueOS 沉下去。**

**而它现在的版本号里藏着基座信息**：**「26.1-R15.0p2」里的 `R15.0` 就是 FreeBSD 15.0-RELEASE。** **这个命名方式我认为很聪明，因为它让你一眼知道它跑在哪个 FreeBSD 上，而这决定了它的安全更新节奏跟谁走。**

**除了 GhostBSD，BSD 这一层还有一批「专用发行版」，而它们说明了 BSD 最实际的用途**：

| 项目 | 基座 | 用途 |
|---|---|---|
| **pfSense** | **FreeBSD** | **防火墙/路由器**（**最知名的 BSD 商业应用之一**） |
| **OPNsense** | **FreeBSD** | **防火墙/路由器**（**pfSense 的分叉**） |
| **HardenedBSD** | **FreeBSD** | **安全加固的 FreeBSD 分叉** |
| **BSDRP** | **FreeBSD** | **BSD Router Project，开源路由器发行版** |
| **FreeNAS / TrueNAS** | **FreeBSD** | **存储设备** |
| **OS108** | **NetBSD** | **带图形桌面的 NetBSD** |
| **helloSystem** | **FreeBSD** | **「像 macOS 一样」的桌面** |
| **CheriBSD** | **FreeBSD** | **剑桥大学，为 CHERI 能力硬件做的研究系统** |

**而这里有一个数据值得记住，因为它是「BSD 的实际份额分布」**：**一份 BSD 调查显示，「约 77% 的受访者使用 FreeBSD，33% 使用 OpenBSD，16% 使用 NetBSD，2.6% 使用 DragonFly，6.6% 使用其他系统」（可多选）。** **⚠️ 而这份调查的原始说明里有免责声明：「注意没有对照组，也没有对受访者做预筛。」**

**所以 BSD 这一层的真实图景是**：**FreeBSD 是主力，OpenBSD 是安全领域的据点，NetBSD 是硬件覆盖的据点，DragonFly 是小众但技术上有独特方向，而真正在商业上被大量部署的 BSD，往往是那些「用户不知道自己在用 BSD」的产品（防火墙、存储、网络设备）。**


## 我的判断

**第一，BSD 这一层最值得羡慕的不是技术，是治理结构。** **因为 FreeBSD、OpenBSD、NetBSD 三家都有自己的基金会或核心团队，而它们的版本节奏是可预测的（FreeBSD 的排期表已经排到 2028 年 12 月）。** **而商业 Unix 的节奏取决于母公司的战略会议。** **这个差别的实际后果是**：**一个企业可以基于 FreeBSD 的路线图做五年规划，但基于 HP-UX 做五年规划，在 2025 年 12 月之后就没有意义了。**

**第二，「UNIX 认证」这件事最值得记的不是它证明什么，而是它暴露了「Unix」这个词的三重含义。** **因为「Unix」现在同时指三件事**：**① 一段具体代码的血统（4.4BSD-Lite / System V）；② 一个商标的授权（The Open Group 的认证）；③ 一套接口标准（POSIX / Single UNIX Specification）。** **而浪潮 K-UX 和华为 EulerOS 恰好证明了 ② 和 ① 可以完全脱钩：两个 RHEL 衍生版拿到了 UNIX 商标，而真正有 AT&T 血统的 FreeBSD 没买。**

**第三，GhostBSD 换基座两次这件事，是「桌面 BSD 发行版」这个品类的缩影。** **它 18.10 到 21.01.20 基于 TrueOS，而 TrueOS 在 2020 年停止，于是它退回 FreeBSD。** **而它活下来的原因恰恰是「及时退回」，而不是「坚持原路线」。** **我认为这对任何做发行版的人都有参考价值**：**当你选一个基座时，你赌的不只是它的技术质量，还有它的存活概率。**

**第四，真正被大量部署的 BSD，往往不是那四个正统，而是那些「用户不知道自己在用 BSD」的产品。** **pfSense、OPNsense、TrueNAS、Juniper 的 Junos、NetApp 的 ONTAP，这些在数据中心里随处可见的东西，底层都有 BSD 的代码。** **所以「BSD 份额小」这个说法在桌面语境下成立，在基础设施语境下完全不成立。**

**第五，关于「BSD 会不会消失」，我认为不会，但理由和很多人想的不一样。** **不是因为「还有人在用」，而是因为它们已经变成了**基础设施的默认选项之一**：**当一个网络设备厂商要做一套稳定的系统，BSD 的许可证（允许闭源修改）比 GPL 更有吸引力。** **所以 BSD 的未来不在桌面，在网络设备和存储设备里。而这个位置很稳，因为那里没有 Linux 那样的竞争压力。**


## 关键事实速查

### BSD 家族

| 系统 | 最新版本 | 发布日期 | 备注 |
|---|---|---|---|
| ⭐ **FreeBSD** | **15.1-RELEASE**（生产版） | **2026-06-16** | **15.0 → 2026-09-30 到期**；**15 系列支持到 2029-12-31** |
| **FreeBSD 未来排期** | **15.2（2026-12）**、**14.6（2027-03）**、**15.3（2027-06）**、⭐ **16.0（2027-12）**、**16.2（2028-12）** | — | **大版本约两年一个** |
| **FreeBSD 15.0 亮点** | **原生 inotify**；**OpenZFS 2.4.0-rc4**；**OpenSSL 3.5.4（含 QUIC + ML-KEM/ML-DSA/SLH-DSA）** | **2025-12-02** | **后量子密码学已进基础系统** |
| ⭐ **OpenBSD** | **8.0** | **2026-10-20** | **第 61 个版本** |
| **OpenBSD 定位** | **「三十多年里，默认安装只有两个远程漏洞」** | — | **「流行的 OpenSSH 软件来自 OpenBSD」** |
| **OpenBSD 8.0 要点** | **amd64 内核地址空间 4G→512G**；**Intel Arc 支持**；**arm64 休眠**；**`rtrd(8)`**；**RISC-V V 扩展**；**每 guest 64 vCPU** | — | **LibreSSL 4.4.0、OpenSSH 10.6** |
| ⭐ **NetBSD** | **11.0** | **2026-07-30** | **第 19 个大版本** |
| **NetBSD 版本线** | **10.2（2026-09-15）**；⚠️ **9.5，netbsd-9 于 2026-08-31 EOL** | — | — |
| ⭐ **macOS** | **26 Tahoe**（**2025-09-15**） | — | ⭐ **最后一个支持 Intel 的版本** |
| **macOS 27** | **Golden Gate** | **2026-09-14** | ⭐ **要求 M 系列，不支持 Intel** |
| **版本号规则** | **2025 年起改用年份制**（**WWDC 后的年份**） | — | **15 Sequoia → 26 Tahoe** |
| **Darwin 映射** | **macOS 14 → Darwin 23**；**15 → 24**；**26 → 25**；**27 → 27** | — | ⚠️ **26→25 是错位，不能线性外推** |

### 「UNIX 认证」的真相

| 问题 | 答案 |
|---|---|
| **认证存在吗** | **存在，The Open Group 有公开注册表 `opengroup.org/openbrand/register`** |
| ⭐ **注册表现有产品** | **IBM：AIX 7（7.2 TL5+）、AIX 7.1 TL5 / 7.2 TL2、AIX 6.1.2、AIX 5L 5.3**；**IBM：z/OS 3.1 与 V2R1**；**HPE：HP-UX 11i V3（B.11.31）on Integrity**；**SCO Group：UnixWare 7.1.3、OpenServer 5 与 6**；**Apple：OS X 10.11 El Capitan 等** |
| ⭐⭐ **最反直觉的条目** | **Inspur（浪潮）K-UX 3.0，on Inspur TS K1 system，注册 2016-02-03，有效期至 2019-02-03** |
| ⭐ **K-UX 是什么** | **基于 Red Hat Enterprise Linux 的 Linux 发行版**；**合规声明里注明标准 C 编译器来自 GCC**；**1.0 曾过 LSB 4.0 认证（2012），编译为 IA-64** |
| ⭐ **Open Group 的官方说法** | **「The Open Group 今天宣布，浪潮……成为第一家拥有通过 UNIX 03 标准认证产品的中国公司。」** |
| ⭐ **华为也做了同样的事** | **Huawei 2016-09-09 新闻稿：「华为昆仑 EulerOS 2.0 操作系统通过 UNIX 认证」**；**EulerOS 同样是 RHEL 系企业 Linux** |
| ⭐ **认证的真正含义** | **「这个产品通过了一套一致性测试，因此有权使用 UNIX 商标」，而不是「这个产品含有 AT&T 的代码」** |
| ⚠️ **认证会过期** | **K-UX 3.0 有效期只有三年（2016-02-03 至 2019-02-03）**；**血统是永久的，认证不是** |
| **对采购方有意义吗** | **有。Open Group：「这使买方能够在采购中指定 UNIX 符合性。」** |
| **对开发者有意义吗** | **几乎没有，你测的是行为不是证书** |
| **对「血统」话题有意义吗** | **完全没有，而且会误导**（**用认证判断会得出「浪潮 K-UX 比 FreeBSD 更 Unix」这种荒谬结论**） |

### BSD 家族的区别

| 项目 | 起始 | 要解决的问题 | 结果 |
|---|---|---|---|
| **FreeBSD** | **1993** | **PC 上完整通用的 Unix** | **份额最大、生态最全、商业采用最多** |
| **NetBSD** | **1993** | **尽可能多的硬件平台** | **口号「Of course it runs NetBSD」，支持极多 CPU 架构** |
| **OpenBSD** | **1995（从 NetBSD 分叉）** | **正确性与主动安全** | **「三十多年里默认安装只有两个远程漏洞」；OpenSSH 源头** |
| **DragonFly BSD** | **2004-07-12（从 FreeBSD 4.8 分叉）** | **「从完全不同的方向生长」，追求最大可伸缩性** | **6.4.2（2025-05-09）；HAMMER2、NVMM** |
| ⭐ **GhostBSD** | **2010-03（1.0）** | **FreeBSD 的易用桌面版** | **26.1-R15.0p2（2026-04-18），迁到 FreeBSD 15.0-RELEASE** |
| **GhostBSD 的教训** | **18.10–21.01.20 曾基于 TrueOS，2020 年 TrueOS 停止后切回 FreeBSD** | — | ⭐ **「桌面发行版的命运取决于底层项目是否还活着」** |
| **GhostBSD 命名法** | **版本号里的 `R15.0` 就是 FreeBSD 15.0-RELEASE** | — | **一眼看出安全更新跟谁走** |

### BSD 的「专用发行版」（真正被大量部署的那批）

| 项目 | 基座 | 用途 |
|---|---|---|
| **pfSense** | **FreeBSD** | **防火墙/路由器** |
| **OPNsense** | **FreeBSD** | **防火墙/路由器（pfSense 分叉）** |
| **HardenedBSD** | **FreeBSD** | **安全加固分叉** |
| **BSDRP** | **FreeBSD** | **开源路由器发行版** |
| **FreeNAS / TrueNAS** | **FreeBSD** | **存储设备** |
| **OS108** | **NetBSD** | **带图形桌面的 NetBSD** |
| **helloSystem** | **FreeBSD** | **「像 macOS 一样」的桌面** |
| **CheriBSD** | **FreeBSD** | **剑桥大学，为 CHERI 能力硬件做的研究系统** |

### 三个判定维度（更新版）

| 问题 | 答案 |
|---|---|
| ⭐ **「Linux 是 Unix 吗」** | **血统：不是；商标：Linux 本身不是，但浪潮 K-UX 和华为 EulerOS 这些 RHEL 衍生版**是**；接口：是** |
| ⭐ **「FreeBSD 是 Unix 吗」** | **血统：是（4.4BSD-Lite）；认证：不是（没买认证）** |
| ⭐ **「macOS 是 Unix 吗」** | **血统：混合（Mach + BSD）；认证：**是**（真的买了）** |
| ⭐ **「浪潮 K-UX 是 Unix 吗」** | **血统：不是（RHEL 衍生）；认证：**曾经是**（2016-2019）** |
| **「UNIX」商标归属** | **The Open Group**（**1993 年 Novell → X/Open，1996 年随 OSF 合并进入 Open Group**） |

## 延伸阅读

- [Unix 为什么会分裂成两个阵营：而答案不在技术里，在 1956 年的一份反垄断同意令里](https://freelamp.com/articles/2026-10-21_unix-history-origins-system-v-bsd-split/)
- [商业 Unix 只剩一个还在开发：HP-UX 刚刚断线，而它死于一枚停产的 CPU](https://freelamp.com/articles/2026-10-21_commercial-unix-2026-aix-hpux-solaris-status/)
- [OpenBSD 8.0 发了：而这次最值得看的不是漏洞修复清单，是内核虚拟地址空间从 4G 跳到 512G](https://freelamp.com/articles/2026-10-20_openbsd-8-0-release-kernel-address-space/)
- [Linux 7.3 发布：一万八千个提交、三千名开发者，而两篇报道各说一半](https://freelamp.com/articles/2026-10-19_linux-7-3-release-record-commits-ai-churn/)
- [FreeBSD 官方发布页（一手）](https://www.freebsd.org/where/)
- [Open Group 的 UNIX 认证注册表（一手）](https://www.opengroup.org/openbrand/register)
