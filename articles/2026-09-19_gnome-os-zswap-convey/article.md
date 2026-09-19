# GNOME OS 默认开启 zswap 治 OOM，邮件客户端 Geary 的 GTK4 复刻 Convey 登陆 Flathub

> 原文：[GNOME OS Turns To Zswap To Deal With OOM Issues, Progress On Geary Email Client Fork](https://www.phoronix.com/news/GNOME-OS-Goes-Zswap)（Phoronix，Michael Larabel，2026-09-19）。本文由 LeisureLinux 翻译整理并加注解读；文内事实均来自原文。

除了本周发布的 **GNOME 51**，桌面圈这周还有几件值得记一下的进展——其中两件和「内存」与「老软件续命」有关。

## 译文：两条主线

### GNOME OS 用 zswap 治 OOM

GNOME OS 现在多了一个**文档站**（[gnome-build-meta docs](https://gnome.pages.gitlab.gnome.org/gnome-build-meta/docs/index.html)），给想试 GNOME OS 的人提供上手与配置指引。

更实用的是：GNOME OS 现在启用了 **zswap**，目的是即便机器内存不多，也能保持系统「快而跟手」。对于那些在 GNOME OS 上遇到过内存耗尽（OOM）问题的人，这个改动应该能改善体验——zswap 被设为**默认开启**。

具体实现上，GNOME OS 依赖一个 **Rust 写的 `zswap-generator`** 脚本来生成正确的 systemd 配置；它会在内核命令行上**尊重 `zswap.enabled=0`**，也就是你照样可以一行参数把它关掉。

### 第三方应用：Geary 的复刻 Convey 上了 Flathub

第三方 GNOME 应用这边，**Convey** 作为 **Geary 邮件客户端的复刻（fork）** 首次登陆 [Flathub](https://flathub.org/en/apps/net.donnybeelo.Convey)。它在 Geary 基础上加了 **Microsoft 365 支持**、移植到 **GTK4** 工具集，并带了一堆修复和 UI/UX 改进。

更多本周 GNOME 动态见 [This Week in GNOME #266](https://thisweek.gnome.org/posts/2026/09/twig-266/)。

## 解读：两个动作背后的工程信号

**1. zswap 不是 swap，是「压缩后先攒着」——它治的是「假 OOM」。**

很多人把 zswap 和 swap 混为一谈，其实不一样：zswap 是**内存里的压缩写回缓存**——页被换出时先压缩、暂存在内存的一块池子里，只有池子满了才真正落盘到 backing swap。对内存紧张但不是真的没盘可换的机器，它的价值是**用一点 CPU 压缩换「不触发 OOM、不卡到换页风暴」**。GNOME OS 面向的是试玩/笔记本/小内存设备，默认开 zswap 是很贴场景的选择。

值得注意的实现细节：**用 Rust 写的 systemd generator 来落地 zswap 配置**，而非硬编码。generator 在启动早期由 systemd 调用、生成临时 unit，好处是配置可以和内核命令行交互——`zswap.enabled=0` 仍能一键关。这延续了近年「**以前用 shell 脚本/unit 干的事，正迁移到内存安全的 Rust 小工具**」的趋势（ubuntu 的 rust-coreutils、mold 重写 Rust 都是同一条线）。

**2. Convey 说明：GTK4 迁移的「长尾」里，fork 在替社区补位。**

Geary 是 GNOME 阵营老牌的轻量邮件客户端，但长期停在 GTK3、维护乏力。Convey 这种 fork 做的事很典型：把老项目**抬到 GTK4**（这是 GNOME 生态当前的事实基线，不搬就会被新版桌面慢慢边缘化），再补上最被企业用户念叨的 **Microsoft 365 支持**。这既是「社区维护跟不上、外部贡献者另起炉灶」的缩影，也是开源自我修复的一种姿势——代码在，就总有人能接着跑。

一句话收尾：GNOME 这边一手用 zswap 给小内存设备兜底 OOM、一手让 Convey 把老邮件客户端续上 GTK4，两个动作都不性感，但都落在「让桌面真的能在更多机器上、更久地用下去」这种实处。
