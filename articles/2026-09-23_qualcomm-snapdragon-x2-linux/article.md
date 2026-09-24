# 高通在夏威夷谈 Snapdragon X2 的 Linux：早期开发者预览，Debian 13 用户态，HP/华硕承诺 2027 H1 官方支持

> 原文：[Qualcomm Talks Up Linux On Snapdragon X2 Laptops](https://www.phoronix.com/news/Qualcomm-Talks-Up-X2-Linux)（Phoronix，Michael Larabel，2026-09-23）。本文由 LeisureLinux 翻译整理并加注解读；文内事实来自原文。

在高通于夏威夷举办的 Snapdragon Summit 上，官方开始**高调谈 Snapdragon X2 系列笔记本的 Linux 支持**。

## 译文：X2 的 Linux 进展

Larabel 注意到，近几个月高通工程师向上游提交 X2 Elite Linux 支持、为不同 X2 机型做 Device Tree 支持的活动明显增多——围绕 Snapdragon X2 的 Linux/开源活跃度，相比 X1 系列有显著提升。大量工作仍在落地、各种问题在解决中，但确实是明确的改善。

今天高通在 Summit 上**固化了 X2 的 Linux 动作**：展示了 Linux bring-up，并宣布 **Snapdragon X2 的 Linux 早期开发者预览（early developer preview）**。他们用一套**定制 Linux 内核 + Debian 13 用户态**。大量初始使能已经上游化，更多工作围绕 **Hexagon NPU**、以及 Mesa 里走 **Freedreno / Turnip** 驱动的 Adreno GPU 支持（甚至 **Rusticl**）展开。电源、散热、可靠性方面也还有更多工作要做。

在另一篇高通博客里，他们点出了这句耐人寻味的话：

> 「Linux 是整个行业都能在其上构建的基石——而这只是开始。我们的合作伙伴 HP、ASUS 与 HUMAIN 计划在 2027 年上半年提供 Snapdragon X2 的 Linux 支持，让他们的设备在新操作系统上交付用户期待的出色体验。」

如果 HP 和华硕能在 2027 上半年正式支持 X2 硬件上的 Linux，那会是很棒的事。Larabel 表示会持续关注 X2 的 Linux 支持进展，并最终看它相对 AMD Ryzen、Intel Core Ultra 笔记本在 Linux 上的电源/性能表现如何——他也希望能拿到评测样机做 Phoronix 的实测，不过鉴于硬件定价吃紧与网络出版/广告业困境，像当年自购初代 Snapdragon X 那样自掏腰包测已难再现。

## 解读：Arm 笔记本的 Linux，终于从「能启动」走向「能承诺」

**1. 这次的定性变化：从社区 hack 到厂商 early preview + 伙伴承诺。**

初代 Snapdragon X 的 Linux 是靠社区（aarch64 爱好者、Freedreno/Turnip 驱动作者、内核主线搬运）一点点啃出来的，厂商态度暧昧。X2 这波不同：高通自己发 early developer preview、用定制内核+Debian 13 用户态、把 bring-up 当正式动作展示，且点名 HP/华硕/HUMAIN 在 2027 H1 提供官方 Linux 支持。这是「Arm 笔记本 Linux」从**能启动**迈向**厂商敢承诺**的关键一步——承诺意味着固件/驱动/电源管理的长期维护责任，而非一次性 PoC。

**2. 技术栈值得记：AVF/pKVM 之外，这里是定制内核 + Debian 13 + Mesa 开源驱动。**

X2 的 Linux 使能走的是正统开源路线：内核上游化、Debian 13 用户态、Adreno GPU 用 Freedreno/Turnip（开源）、甚至 Rusticl（Rust 写的 OpenCL 实现）。Hexagon NPU 还在补。这和 Google 在 Android 16 里用 AVF/pKVM 跑 Debian 虚拟机（我们这批若发的 Android 变桌面那篇）是两条线：一条是**笔记本原生 Linux**（高通/Debian），一条是**手机里跑 Linux VM**（Google/AVF）。两者共同说明——Arm 上的 Linux 生态正在从「勉强能跑」变「有正统发行版兜底」。

**3. 真正的考题仍是电源/散热/可靠性，而非「能不能亮」。**

高通自己也说电源、散热、可靠性还有更多工作。这正是 Arm 笔记本 Linux 历史的老难点：能把桌面点亮容易，难的是**闲置功耗、S3/s2idle 睡眠、风扇曲线、长续航**这些日常体验。Debian 13 用户态 + 上游内核给了好底子，但 s2idle、PCIe ASPM、调制解调器/Wi-Fi 固件这些「最后一公里」还要逐个啃。等 HP/华硕 2027 H1 真出官方支持机型，才有可下结论的实测数据。

**4. 对读者的意义：2027 可能是「买 Arm 笔记本装 Linux」第一次接近无脑。**

如果你在等「一台续航长、能正经跑 Linux 的 Arm 笔记本」，X2 + Debian 13 的路线图把时间点指向 2027 上半年。在此之前，想玩可走早期开发者预览，但别指望日常可靠。可类比的参照是我们写过的富士通 MONAKA 144 核（Arm 服务器）、以及 Apple Silicon 的 Asahi——Arm 上的 Linux 正从「勇气测试」变成「产品选项」。

一句话收尾：高通这次不是「又演示了个能亮的 Linux」，而是把 X2 的 Linux 抬到了 early developer preview + 伙伴承诺的层级——Arm 笔记本的 Linux，离「买来就能装」可能就差 2027 上半年这一批机型了。
