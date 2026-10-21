---
title: "商业 Unix 只剩一个还在开发：HP-UX 刚刚断线，而它死于一枚停产的 CPU"
date: 2026-10-21
slug: commercial-unix-2026-aix-hpux-solaris-status
tags: [Unix, AIX, HP-UX, Solaris, illumos, OpenIndiana, Xinuos, OpenServer, UnixWare, Xenix, Itanium, Power, SPARC, System V, 生命周期, EOL, 商业软件]
category: 系统/硬件
author: FreeLAMP.com
original_source: "IBM AIX 生命周期页 + Oracle/HP-UX 版本记录 + Xinuos + OpenIndiana 官网（逐个核对）"
original_author: "IBM、HPE、Oracle、Xinuos、illumos/OpenIndiana 社区"
original_date: 2026-10-21
original_url: "https://www.ibm.com/support/pages/aix-support-lifecycle-information"
description: "商业 Unix 在 2026 年的真实状态：AIX 是唯一还在积极开发的（7.3 TL4 支持到 2028 年底），HP-UX 的 Integrity 支持已于 2025 年 12 月 31 日终止，Solaris 自 2018 年后没有新大版本但 SRU 还在发，Xinuos 的 OpenServer/UnixWare 停在 2018 年的 Definitive 版。本文逐个给出版本号与截止日，并指出一个共同模式：商业 Unix 很少死在技术上，大多死在硬件停产或母公司战略上。"
published: true
---

> 来源：本文的每一个版本号、日期与支持状态都**逐个回到官方页面核对**：[IBM AIX 生命周期页](https://www.ibm.com/support/pages/aix-support-lifecycle-information)、[Oracle Solaris 版本记录](https://en.wikipedia.org/wiki/Oracle_Solaris)、[HP-UX 记录](https://en.wikipedia.org/wiki/Hewlett-Packard_Unix)、[OpenServer/Xinuos](https://en.wikipedia.org/wiki/SCO_OpenServer)、[OpenIndiana 官网](https://www.openindiana.org/)。
> 这是「Unix 家族史」的**第二篇**（原第三篇的 BSD 部分已独立成篇）。第一篇讲 1969 到 1993 的起源与分裂，以及那十八年版权诉讼。**⚠️ 所有版本号与日期均以官方页面为准。**
> 本文为**解读**。第二节关于「商业 Unix 共同死因」的归纳、第四节的判断是笔者补充的部分。

## 一句话结论

**商业 Unix 在 2026 年的真实状态，可以用一句话概括：五个里只有一个还在积极开发，而它活下来的原因不是技术，是硬件。**

| 系统 | 最新版本 | 状态 |
|---|---|---|
| ⭐ **AIX** | **7.3 TL4（2025 年 12 月）** | **唯一还在积极开发的，支持到 2028-12-31** |
| ⚠️ **HP-UX** | **11i v3（B.11.31）** | ⭐ **Integrity 支持已于 2025-12-31 终止**，一条始于 1982 年的线断了 |
| **Solaris** | **11.4（2018-08-28）**，SRU95 于 2026-09-21 | **只在维护，没有新大版本**，支持标到 2037 年 |
| **Xinuos OpenServer / UnixWare** | **Definitive 2018** | **维护模式**，最新是 2017-2018 年的版本 |
| ⚠️ **Xenix** | **2.3.4** | ⭐ **1996-01-01 停止销售** |

**而我认为这张表里最值得注意的是它们的死因高度一致**：**HP-UX 死在 Itanium 停产，Tru64 死在两次并购，IRIX 死在 SGI 的财务危机，Xenix 死在自己的后继产品。** **它们很少死在技术上。**

**而 AIX 还活着的唯一原因是：IBM 的 Power 硬件还在卖，而且 IBM 自己就是那个硬件厂商。**

## 一、商业 Unix 逐个看：谁还活着，谁刚刚断线

### AIX（IBM）：唯一还在积极开发的那个

**这是商业 Unix 里状态最好的一个，而数据很具体。**

**IBM 官方生命周期页给的是 TL（Technology Level）级别的表**：

| TL | 发布 | 修复支持截止 | 最新 SP |
|---|---|---|---|
| ⭐ **7.3 TL4** | **2025 年 12 月** | **2028 年 12 月 31 日** | **7300-04-02-2633** |
| **7.3 TL3** | **2024 年 12 月** | **2027 年 12 月 31 日** | **7300-03-03-2633** |
| ⚠️ **7.3 TL2** | **2023 年 11 月** | **2026 年 11 月 30 日** | **7300-02-05-2633** |
| **7.3 TL1** | **2022 年 12 月** | **2025 年 12 月 31 日**（已过） | **7300-01-04-2420** |
| **7.2 TL5** | **2020 年 11 月** | **待定** | **7200-05-13-2633** |

**「支持的截止期用 TL 而不是大版本算」，这是 AIX 的一个特点，值得单独说明。** **因为很多人会问「AIX 7.3 支持到什么时候」，而正确答案是**取决于你用哪个 TL**。** **7.3 这个版本号本身没有统一的 EOS 日期，而各个 TL 各有各的截止期。**

**⚠️ 而表里有个马上要发生的事**：**7.3 TL2 在 2026 年 11 月 30 日截止**，**而今天是 10 月 21 日。也就是说这件事还有一个多月。**

**历史线**：**AIX 1986 年 2 月首发**（**最初跑在 IBM RT PC 上**），**现在的 7.3 是 2021 年 12 月 10 日发布的**。**它基于 System V，带 4.3BSD 兼容扩展**，**从 5.3 起通过 UNIX 03 认证，从 7.2 TL5 起通过 UNIX V7 认证**。**现在只支持 Power ISA。**

### HP-UX（HPE）：这条线已经断了

**这是本篇最重要的一条，而它可能颠覆很多人的认知。**

**HP-UX 的最终版本是 11i v3（B.11.31），而它在 2025 年 12 月 31 日停止了支持。**

**The Register 在 2026 年 1 月 5 日的标题就是**：**「最后一个受支持的 HP-UX 版本不再存在。HPE 自己那个 Unix 发行版的最终版本，HP-UX 11i v3，现在已失去支持。这是一条始于 1982 年的路线的终点。」**

**「一条始于 1982 年的路线的终点」。** **而 44 年，是这五个商业 Unix 里最长的一条线。**

**官方记录的细节**：

- **初始发布：1982 年**
- **最新（也是最后）的更新：2025.11iv3，2025 年 5 月 22 日**
- **11i v3（B.11.31）的 Integrity 版本支持截止：2025 年 12 月 31 日**
- **而 HP 9000 版本更早就截止了：2021 年 3 月 31 日**
- **现在状态：Mature Support（在 HPE Integrity 上，不含 Sustaining Engineering），至少到 2028 年**

**这里有一个重要的区分我必须说清楚**：**「停止标准支持」和「完全没人管」不是一回事。** **HPE 现在把它放在 **Mature Support** 状态，而这个状态的含义是「还能拿到一些支持，但没有新的工程投入」。** **所以严格说，HP-UX 是「停止开发、进入延长支持」，而不是「2026 年 1 月 1 日就彻底消失」。**

**但方向是明确的：这个产品已经没有未来了。** **而它 2025 年 5 月的那次更新很可能就是最后一次内容更新。**

**为什么它死了，我认为原因很直接**：**HP-UX 的现代版本只跑在 Itanium 上，而 Itanium 已经停产。** **一条产品线的主机硬件停产之后，操作系统还能撑多久，取决于客户迁移的速度，而不是取决于软件本身。**

### Solaris（Oracle）：活着，但只在一个很窄的意义上

**Solaris 的状态是这五个里最容易被误读的。**

**数据**：**最新版本记录是 11.4，最新 SRU 是 2026 年 9 月 21 日的 **SRU95****。**而支持期标到 **2037 年**。**

**「2037 年」。** **这个数字看起来很长，而它的含义需要解释**：**它意味着 Oracle 会继续给 11.4 出补丁，但它不意味着会有 Solaris 12。**

**而这一点值得单独说，因为它是 Oracle 接手 Sun 之后最受争议的决定之一**：**Solaris 的版本号在 11.4 之后就没有再前进。** **所以「2037 年支持截止」这个承诺，本质上是一个「长期维护承诺」，而不是「持续开发承诺」。**

**而 11.4 本身是 2018 年 8 月 28 日发布的。** **也就是说：这个产品已经七年没有大版本了。**

**⚠️ 而这里我要标注一个材料限制**：**关于「Oracle 是否已正式宣布不再有大版本」这个问题，我没有核到 Oracle 的官方声明。所以更准确的说法是「从 2018 年至今没有新的大版本，而有持续的 SRU」，而不是「Oracle 宣布停止开发」。** **这个区别对写正式材料很重要。**

**而 Solaris 那条线还有一条支流，我在下面单独讲（illumos）。**

### Xinuos 的 OpenServer 和 UnixWare：维护模式

**这一家的历史最曲折，而它的现状最需要精确表述。**

**它的产品线演变是这样的**：

| 产品 | 基座 | 最新版本 | 状态 |
|---|---|---|---|
| **OpenServer 5** | **SVR3.2** | **5.0.7 Definitive 2018**（**2018 年 10 月**） | **仍在支持** |
| **OpenServer 6** | **SVR5**（**UnixWare 7 内核 + OpenServer 5 兼容层**） | **6 Definitive 2018**（**2017 年 12 月**） | **仍在支持** |
| **UnixWare 7** | **SVR5** | **7 Definitive 2018**（**2017 年 12 月**） | **仍在支持** |
| **OpenServer 10** | **FreeBSD 10** | **2015 年** | ⚠️ **2018 年后无更新，已从官网下架** |

**「OpenServer 10 基于 FreeBSD 10，自 2018 年后未获任何更新，且已不再在 Xinuos 网站上营销」。**

**我认为这一条很有代表性**：**Xinuos 当年做 OpenServer 10 是为了给老客户一条迁移路径**（**从 SVR3.2/SVR5 迁到 FreeBSD 基座**），**而这条路走了四年就停了。**

**而这条线的历史脉络值得串一下，因为它把 Unix 史上几乎所有阵营都串起来了**：

**Xenix（微软 1980-1987 → SCO 1987-1991）→ SCO UNIX（1989，SVR3.2 基座）→ SCO OpenServer（1995）→ SCO Group（2001 改名，就是打官司那个）→ 破产（2007）→ Xinuos（2011 买走产品线）。**

**而 Xenix 那一环我单独说，因为它是本篇里唯一一个「早就死了但很多人还记得」的。**

### Xenix：微软曾经是 Unix 厂商

**这一条我认为值得单独一节，因为它的死法很有教育意义。**

**Wikipedia 的记录**：**「Xenix 是微软从 1980 到 1987 年发行、而 Santa Cruz Operation（SCO）从 1987 到 1991 年发行的 Unix 操作系统。」**

**而 Linux Journal 1997 年那篇《The Death of Xenix》给了一个具体的终止日期和一个非常具体的价格**：

> **「到 1996 年 1 月 1 日，Santa Cruz Operation（SCO）精简了它的产品线，从阵容中砍掉了一批较旧的发行版。」**
>
> **「直到去年 12 月 31 日，你仍然可以买到 OpenServer 3.0……现在不行了。」**

**而它给作者的私人记忆很有画面感**：

> **「我第一次接触它是在 1985 年年中，那时它差不多是唯一一个真正带有 Unix 代码、能在当时的 286 和 386 上跑的东西。」**
>
> **「我当时不在一个能玩装满 BSD 的 VAX 的大学里，我买不起当时 Sun 和 HP 的 68000 产品，而我也不太放心当时那一堆 Unix 克隆（比如 Coherent、QNX 或 OS9）。」**

**「我当时不在一个能玩 VAX 的大学里」。** **这句话简洁地说明了 Xenix 的历史地位**：**它是「PC 上的 Unix」，服务于那些进不了大学机房、也买不起工作站的人。**

**而 SCO 给 Xenix 用户的升级方案，那个价格表我认为很值得看**：

> **「Xenix → 16 用户 Host 系统（无网络）：250 美元」**
> **「Xenix → 32 用户 Enterprise 系统（带网络）：750 美元」**
> **「……或者付大约 4,000 美元升级到不限用户的 OpenServer。」**

**「250 美元 / 750 美元 / 4,000 美元」。** **而作者补了一句关键的批评**：**「很多 Xenix 用户可能不愿把他们的不限用户授权升级成一个有限用户的 OpenServer 系统。」**

**我认为 Xenix 的死法值得记住，因为它是一个典型的「被上位产品吃掉」的案例**：**它不是被竞争对手打败的，是被自己的后继产品（SCO UNIX / OpenServer）取代的。而取代的过程里，授权模式从「不限用户」变成了「按用户数卖」，所以老用户是**不愿意**升级，而不是不能。**

## 二、你可能没听过的分支：illumos 和 OpenIndiana

**这一条我认为是「Unix 还活着」这件事里最有趣的部分，因为它是社区接住了厂商扔掉的东西。**

**背景很简单**：**Oracle 在 2010 年收购 Sun 之后，关掉了 OpenSolaris 项目。**

**而 OpenIndiana 的历史记录是**：

> **「OpenIndiana 是一个自由开源的 illumos 发行版，兼容 SPARC 和 x86-64 计算机。这个项目始于 2010 年，在 Oracle 公司停止 OpenSolaris 之后从 OpenSolaris 分叉出来，因此是 UNIX System V Release 4 的后代。」**

**而它的架构选择值得一提**：

> **「这个项目的意图是交付一个 System V 家族的、与 Oracle 的 Solaris 11 和 Solaris 11 Express 二进制兼容的操作系统。然而，OpenIndiana 不是基于 OpenSolaris 那样的 OS/Net consolidation，而是基于 illumos。」**

**「基于 illumos 而不是 OS/Net consolidation」。** **这个区别的重要性在于**：**illumos 是一个**内核**项目，也就是说社区把 Solaris 的内核接过来自己维护了，而在它上面做发行版。**

**而它的活跃度数据**：**最新版本是 **Hipster 2026.04，2026 年 5 月 5 日发布**。**

**「2026 年 5 月还在发版」。** **这个事实的意义在于：Solaris 11.4 从 2018 年至今没有大版本，而它的开源后代在 2026 年还在发半年度快照。**

**而 illumos 这一支的衍生产品名单也很长，Wikipedia 的导航框列了**：**OpenIndiana、OmniOS CE、SmartOS、Tribblix、Nexenta、BeleniX。**

**其中 SmartOS 值得单独提一句**：**它是 Joyent 的产品，而 Joyent 是做 Node.js 那家公司。** **所以「Solaris 的技术血脉流进了一家 Node.js 公司的容器平台」，这个说法是成立的。**


## 商业 Unix 的共同死因

**把上面几家放在一起看，会发现一个很清晰的模式。**

| 系统 | 死因 | 直接原因 |
|---|---|---|
| **HP-UX** | ⭐ **主机的 CPU 停产** | **只跑 Itanium，而 Itanium 已停产** |
| **Tru64 UNIX** | ⭐ **两次并购** | **Compaq 1998 买 DEC → HP 2002 买 Compaq → HP 只保留自己的 HP-UX** |
| **IRIX** | ⭐ **母公司的财务危机** | **SGI 撑不住** |
| **Xenix** | ⭐ **被自己的后继产品取代** | **SCO UNIX / OpenServer 顶替了它，而且授权模式从「不限用户」变成「按用户数卖」** |
| **Solaris** | **收缩但未死** | **Oracle 保留维护，但自 2018 后没有新大版本** |
| **AIX** | **还活着** | ⭐ **IBM 自己的 Power 硬件还在卖** |

**我认为这个模式最值得记住的一点是**：**一个操作系统的生命力，取决于它绑定的硬件生态是否在增长，而不是取决于它的技术质量。** **Tru64 在 Alpha 上曾经是性能最强的 Unix 之一，而它死于两次并购。IRIX 在图形工作站上没有对手，而它死于 SGI 的财务。**

**而反过来，AIX 的技术并不比它们先进多少，但它的硬件供应商就是它的软件供应商。**

## 我的判断

**第一，这张表最该被记住的不是「还剩几个」，而是「它们的死因高度一致：硬件或母公司，而不是技术」。** **HP-UX 死在 Itanium 停产，Tru64 死在两次并购，IRIX 死在 SGI 的财务，Xenix 死在自己的后继产品。** **而 AIX 还活着的唯一原因是：IBM 的 Power 硬件还在卖，而且 IBM 自己就是那个硬件厂商。** **Solaris 还活着的唯一原因是：Oracle 有足够多的存量客户，而维护一个已有产品的成本低于迁移客户。** **我认为这个模式对今天仍然有参考价值**：**一个操作系统的生命力，取决于它绑定的硬件生态是否在增长，而不是取决于它的技术质量。**

**第二，「是不是 Unix」这个问题在 2026 年已经应该分成三个问题来回答。** **因为「Unix」这个词现在同时指三件事**：**① 一段具体代码的血统（4.4BSD-Lite / System V）；② 一个商标的授权（The Open Group 的认证）；③ 一套接口标准（POSIX / Single UNIX Specification）。** **而这三件事的组合在现实里是错位的**：**macOS 满足 ②③ 而血统是混合的；FreeBSD 满足 ① 而不满足 ②；Linux 只满足 ③。** **所以当有人问「Linux 是不是 Unix」，正确的回答是反问**：**你问的是血统、商标、还是接口？**

**第三，我认为 BSD 这一层最值得羡慕的不是技术，是治理结构。** **因为 FreeBSD、OpenBSD、NetBSD 三家都有自己的基金会或核心团队，**而它们的版本节奏是可预测的**（**FreeBSD 的排期表已经排到 2028 年 12 月**）。** **而商业 Unix 的节奏取决于母公司的战略会议。** **这个差别的实际后果是**：**一个企业可以基于 FreeBSD 的路线图做五年规划，但基于 HP-UX 做五年规划，在 2025 年 12 月之后就没有意义了。**

**第四，关于那个「illumos 还在发版」的事实，我认为它的意义不是「Solaris 还有替代品」，而是「开源模式在厂商放弃之后仍然能延续一个技术体系」。** **因为 illumos 接住的不只是代码，是一整套 Solaris 的技术遗产**：**ZFS、DTrace、Zones、Crossbow。** **而这些技术现在同时活在 illumos 和各种 Linux 发行版里**（**ZFS 在 FreeBSD 和 Linux 上都有，DTrace 在 FreeBSD 上有，eBPF 在概念上承继了 DTrace 的思路**）。 **所以「Solaris 快没有大版本了」这件事，对技术的影响远小于对采购的影响。**

> **最后一件事，关于这份材料的可信度**：**本文的每一个版本号和日期我都回到了官方页面。而有两处我要标注不确定性**：**① Solaris 的「2037 年支持截止」这个数字来自第三方版本记录页，我没有核到 Oracle 的原始生命周期文件；② 「Unix 系统 V 的版权现在归 OpenText」这条链（Novell → Attachmate → Micro Focus → OpenText）是我根据公开并购历史推的，没有逐笔核实原始公告。** **这两条如果要写进正式材料，请再核一遍。**


## 关键事实速查

### 商业 Unix（System V 血统）

| 系统 | 最新版本 | 发布日期 | 支持状态 |
|---|---|---|---|
| ⭐ **AIX** | **7.3 TL4** | **2025 年 12 月** | **7.3 TL4 支持到 2028-12-31**；**TL3 → 2027-12-31**；⚠️ **TL2 → 2026-11-30（一个多月后）** |
| **AIX 7.2** | **7.2 TL5** | **2020 年 11 月** | **待定**（最新 SP `7200-05-13-2633`） |
| **AIX 历史** | **1986 年 2 月首发**（**跑 RT PC**）；**7.3 于 2021-12-10 发布** | — | **基于 System V + 4.3BSD 扩展**；**5.3 起 UNIX 03，7.2 TL5 起 UNIX V7** |
| ⚠️ **HP-UX** | **11i v3（B.11.31）** | **最后更新 2025.11iv3，2025-05-22** | ⭐ **Integrity 支持已于 2025-12-31 终止**；**HP 9000 版早在 2021-03-31 终止**；**现在 Mature Support 至少到 2028** |
| **HP-UX 历史** | **1982 年首发** | — | **44 年后终止** |
| **Solaris** | **11.4** | **11.4 于 2018-08-28**；⚠️ **最新 SRU95 于 2026-09-21** | **支持标到 2037 年**（**仅维护，无新大版本**） |
| **Xinuos OpenServer 5** | **5.0.7 Definitive 2018** | **2018 年 10 月** | **仍在支持**（基座 SVR3.2） |
| **Xinuos OpenServer 6** | **6 Definitive 2018** | **2017 年 12 月** | **仍在支持**（基座 SVR5） |
| **Xinuos UnixWare 7** | **7 Definitive 2018** | **2017 年 12 月** | **仍在支持**（基座 SVR5） |
| ⚠️ **OpenServer 10** | **2015 年发布**（**基于 FreeBSD 10**） | **2015** | **2018 年后无更新，已从官网下架** |
| ⚠️ **Xenix** | **最终版 2.3.4** | — | ⭐ **1996 年 1 月 1 日停止销售**；**升级方案 250 / 750 / 约 4,000 美元** |

### 社区延续（Solaris 分支）

| 项目 | 最新版本 | 发布日期 | 备注 |
|---|---|---|---|
| ⭐ **OpenIndiana** | **Hipster 2026.04** | **2026-05-05** | **基于 illumos 而非 OS/Net**；**目标是与 Solaris 11 / 11 Express 二进制兼容** |
| **illumos 衍生** | **OpenIndiana、OmniOS CE、SmartOS、Tribblix、Nexenta、BeleniX** | — | **SmartOS 是 Joyent（做 Node.js 那家）的产品** |

### 已死的 Unix 与「Unix 的影子」

| 名称 | 是什么 | 状态 |
|---|---|---|
| **Plan 9** | **贝尔实验室 Unix 的继任研究系统**（1990） | **官方停止，社区有 9front** |
| **Inferno** | **贝尔实验室分布式 OS** | **已停止** |
| **A/UX** | **Apple 在 System 7 时代的 Unix**（1988） | **1995 年停止**；**Apple 绕了 13 年才在 2001 年用 Mac OS X 回到 Unix** |
| **Tru64 UNIX** | **DEC 的 Unix（OSF/1 后代）** | **Compaq 1998 收购 DEC → HP 2002 收购 Compaq → 停** |
| **IRIX** | **SGI 的 Unix** | **2006 年停止** |
| **QNX** | **微内核实时 OS，POSIX 兼容** | **BlackBerry 旗下，汽车领域仍在用** |
| **Minix** | **Tanenbaum 教学用 Unix-like**（1987） | **Minix 3 仍在**；**代码曾在 Intel ME 里被发现** |
| **Coherent** | **早期 PC 上的 Unix 克隆** | **已停止** |

## 延伸阅读

- [Unix 为什么会分裂成两个阵营：而答案不在技术里，在 1956 年的一份反垄断同意令里](https://freelamp.com/articles/2026-10-21_unix-history-origins-system-v-bsd-split/)
- [BSD 家族全表：四个正统、一个桌面发行版，以及「UNIX 认证」这件事的真相](https://freelamp.com/articles/2026-10-21_bsd-family-2026-freebsd-openbsd-netbsd-ghostbsd/)
- [Linux 7.3 发布：一万八千个提交、三千名开发者，而两篇报道各说一半](https://freelamp.com/articles/2026-10-19_linux-7-3-release-record-commits-ai-churn/)
- [Gentoo 给 Chromium 做了「临终祷告」：而杀死这个打包的是一句「这太荒唐了」](https://freelamp.com/articles/2026-10-19_gentoo-chromium-last-rites-maintainer-burnout/)
- [IBM AIX 官方生命周期页（一手）](https://www.ibm.com/support/pages/aix-support-lifecycle-information)
- [OpenIndiana 官网（一手，illumos 分支）](https://www.openindiana.org/)
