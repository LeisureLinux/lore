# Ubuntu 26.10 的 amd64v3 镜像来了：Daily ISO 直接可装，不用再折腾 APT 换源

> 译文来源：Phoronix《Ubuntu 26.10 amd64v3 Daily ISOs Now Being Published》，Michael Larabel，2026-09-07。原文：<https://www.phoronix.com/news/Ubuntu-26.10-amd64v3-Daily>

## 事件：amd64v3 ISO 进入日常构建

Ubuntu 26.10（代号 **"Stonking Stingray"**）有了个值得关注的进展：从 **9 月 4 日**开始的 daily ISO，正式把 **amd64v3 镜像**纳入日常发布——与通用 amd64 镜像、arm64 和 riscv64 镜像并列出现在下载目录里。

这标志着 Canonical 对 amd64v3 的态度正在升级。此前 [Ubuntu 26.10 的 amd64v3 软件包实验](https://www.phoronix.com/news/Ubuntu-26.10-amd64v3-Packages) 中，想用上优化包得先装通用 amd64 镜像，再手动调整 APT 源、升级到 amd64v3 包。现在直接装 ISO 即可，体验顺滑得多。

## x86_64-v3 是什么水平

x86_64-v3 是 x86-64 微架构特性级别（microarchitecture feature levels）的第三档，默认假设 CPU 具备：

| 特性 | 说明 |
|---|---|
| AVX / AVX2 | 256 位向量运算，性能提升主力 |
| FMA | 融合乘加 |
| BMI2 | 位操作加速 |
| MOVBE | 字节序交换指令 |

这一档大致对应 **2013 年以来的 CPU**：Intel Haswell（四代酷睿）到 AMD Excavator 及更新。**Red Hat Enterprise Linux 10 已经强制要求 x86_64-v3**，Ubuntu 的路子更保守——把 amd64v3 做成档案库里的**独立架构**，2013 年前的老系统照旧用通用 amd64 的 x86_64 包，两条线并行、互不强迫。

## 为什么这事有信号意义

Daily ISO 开始构建 amd64v3 镜像，被 Phoronix 视为 Canonical **可能在 26.10 正式提升 amd64v3 地位**的信号。如果 26.10 正式转正，Ubuntu 将成为继 RHEL 10 之后又一个把 x86_64-v3 推到台前的主流发行版——区别在于：RHEL 是一刀切强制，Ubuntu 是可选并行。

Phoronix 表示近期会发布一轮 Ubuntu amd64 与 amd64v3 的**新鲜基准测试**，量化这档优化到底能榨出多少性能。感兴趣的可以现在就去 [cdimages.ubuntu.com](https://cdimages.ubuntu.com/ubuntu/stonking/daily-live/current/) 拿最新的 26.10 daily live ISO。

## 我们的解读：基线抬升的"温和派"样本

**微架构级别是发行版的减负术。** 编译器默认按 v3 基线生成代码，意味着一个发行版档案里所有包的向量化路径、指令调度都按现代 CPU 优化，而不用为十几年前的指令集做保守妥协。RHEL 10 选择强制（老硬件用户被推给 RHEL 9 或社区版），Ubuntu 选择并行——代价是档案翻倍、构建资源加倍，好处是不动刀就能让新版用户受益。

**独立架构是聪明的过渡设计。** 把 amd64v3 当成一个新架构（类似 arm64 之于 amd64）而不是 apt 源里的变体，意味着包依赖、镜像构建、云镜像流水线都能干净地分叉。这比 Fedora 当年 v3 试点的"单包多变体"方案（ Simultaneous Multi-arch 更复杂的那条路）要简单直接。

**2013 年分界线的现实意义。** Haswell 是 2013 年的 CPU，十三年寿命作为发行版基线相当宽厚——今天还在服役的 pre-Haswell 机器，大概率也不适合跑最新桌面发行版了。真正的争议在嵌入式与服务器老旧集群：那些还在跑 v2 及以下 CPU 的机器，还得靠通用 amd64 包续命，Ubuntu 保留了这条路。

**对国产信创侧的提醒：** x86 侧 v3 化的同时，arm64、riscv64 镜像照常发布——发行版的算力版图正在按 ISA 并行推进，x86 内部再按 v1/v3 分层。做 x86 信创整机或私有化交付的，选型时留心目标环境的 CPU 是否达到 v3，否则装了 v3 ISO 轻则无法启动、重则 SIGILL 直接崩。

**判断**：amd64v3 ISO 进 daily 是转正前的最后一步彩排。等 26.10 正式发布见分晓，性能差距看 Phoronix 的基准测试。

---

*参考：[Phoronix 原文](https://www.phoronix.com/news/Ubuntu-26.10-amd64v3-Daily) · [Ubuntu 26.10 daily live ISO](https://cdimages.ubuntu.com/ubuntu/stonking/daily-live/current/)*
