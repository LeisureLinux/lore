# Wine 11.18 继续补全 NTOSKRNL：Windows 内核驱动在 Linux 上跑得越来越真

> 原文：[Wine 11.18 Continues Building Out Its NTOSKRNL Implementation](https://www.phoronix.com/news/Wine-11.18-Released)（Phoronix，2026-09-18，作者 Michael Larabel）。本文由 LeisureLinux 翻译整理并加注解读；文内事实均来自原文，未作改动。

Wine 11.18 今天发布，是这个开源兼容层（在 Linux、macOS 等平台跑 Windows 游戏和软件）最新的双周开发版。这一版的重点，是把 **NTOSKRNL 的实现继续往前推**。

## 译文：这一版到底改了什么

**NTOSKRNL** 是 Windows 操作系统的主内核可执行文件，是内核层与执行体层（kernel and executive layers）的核心。它负责硬件抽象、进程管理、内存管理，以及其它基础必需件。Wine 11.18 里，围绕 NTOSKRNL 的工作集中在三块：

- **PnP 设备启用（PnP device enablement）**——即插即用设备的启用路径；
- **容器 ID（container IDs）**；
- **一批必需函数的实现**。

与此同时，Wine NTOSKRNL 代码的**测试覆盖率**也在同步补齐。

除此之外，Wine 11.18 还包含：一批**代码正确性修复**、**标准 C 头文件里的兼容性修复**，以及 **21 个已知 bug 修复**。这些 bug 修复覆盖面很杂——从 **Adobe Creative Cloud** 的修复，到《刺客信条：叛变》（Assassin's Creed Rogue）等游戏的修复，都有。

下载与更多信息见 [WineHQ.org](https://www.winehq.org/news/2026091801)。

---

## 解读：NTOSKRNL 这条线，为什么值得写

**1. 补全 NTOSKRNL，是在啃 Wine 最难、也最关键的一块。**

Wine 长期的做法是「在用户态模拟 Win32 API」，但很多 Windows 驱动和底层软件会直接调 NTOSKRNL 里的内核接口。过去这些要么跑不了、要么靠各种 hack 绕过。现在 Wine 把 PnP 启用、容器 ID、必需函数一个个实出来，意味着**原本只能靠「假装」或干脆放弃的内核态交互，正被认真建模**。这对依赖内核驱动的老软件、专业工具、甚至某些 DRM/反作弊之外的老游戏，是实质性的可用度提升。

**2. 「测试覆盖率同步补齐」这句话，比看起来重要。**

NTOSKRNL 是内核级代码，行为错一点点，崩溃就是整个进程乃至 Wine 前缀一起完蛋。Wine 过去在这块缺测试，意味着改动极易引入回归。现在实现和测试「in-step」（同步）推进，说明这条路不是临时补丁，而是**按可持续维护的方式在搭地基**——对长期稳定性是好事。

**3. 21 个 bug 修复里，Adobe 和游戏修复最影响普通用户体验。**

对大多数人，NTOSKRNL 的进度是「看不见的底层」；真正每天能感知的是这些具体修复：Adobe Creative Cloud 这类专业软件装得上、用得动，《刺客信条：叛变》这类游戏能跑。Wine 的价值从来都是「让某一个你离不开的 Windows 程序在 Linux 上活下来」，这一版延续了这个务实路线。

一句话收尾：Wine 11.18 表面是又一个双周版，但 NTOSKRNL 这条暗线的持续推进，正在悄悄把「在 Linux 上跑 Windows 内核态代码」这件难事，做成越来越可信的事。
