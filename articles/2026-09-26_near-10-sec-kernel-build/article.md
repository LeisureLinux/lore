---
title: "逼近 10 秒的 Linux 内核构建"
date: 2026-09-26
slug: near-10-sec-kernel-build
tags: [Linux内核, 内核构建, Kbuild, Lorenzo Stoakes, AMD EPYC 9575F, 编译性能, 并行构建, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "Phoronix"
original_author: "Michael Larabel"
original_date: 2026-09-24
original_url: "https://www.phoronix.com/review/near-10-sec-kernel-build"
description: "Phoronix 实测：双路 AMD EPYC 9575F + Lorenzo Stoakes 的 Kbuild 并行化补丁，把 x86_64 defconfig 内核构建从 22 秒压到 15 秒。10 秒是下一代 Venice 的预期目标，目前仍是「逼近」。本文还原硬件、软件、实测数字与技术边界。"
published: true
---

> 原文：[Approaching A 10 Second Linux Kernel Build](https://www.phoronix.com/review/near-10-sec-kernel-build)（Phoronix，Michael Larabel，2026-09-24），两页评测。本文为**译文 + 技术拆解**，重点还原「如何逼近 10 秒」的硬件与软件账，并明确一个边界：**10 秒目前是预期目标而非已达成数字**。

## 一句话结论

在**双路 AMD EPYC 9575F（128 核 / 256 线程）+ 库存 Ubuntu 26.04 LTS** 上，叠加 **Lorenzo Stoakes 的 Kbuild 并行化补丁 v4**，x86_64 **defconfig** 内核的**干净构建**从约 **22 秒降到 15~17 秒**，最快一次 **15 秒**。文章标题的「10 秒」是 Michael Larabel 对未来 **AMD EPYC 9686F（Venice）** 的预期赌注——**当前最快是 15 秒，10 秒仍未达成**。

## 背景：内核构建为什么值得单独做基准

编译 Linux 内核是 Phoronix 跑了 22 年的保留基准。有意思的现象是：内核代码量在 AI/LLM 时代持续膨胀，但**构建时间反而逐年下降**——这靠的是「更猛的 CPU」与「更聪明的构建系统」两条腿。

软件侧的关键变量，是 **Linux MM 开发者 Lorenzo Stoakes** 的一组优化内核构建时间的补丁系列：他**借助 AI/LLM** 定位了 Kbuild 里大量**削弱并行度**的瓶颈（即构建过程本可并行却被串行化卡住的地方）。此前已有两波收益：

- **Linux 7.4** 的 Kbuild 改进：干净构建快约 **36%**，增量构建快约 **70%**（对应 `Faster-Kernel-Builds-AI-v2` 与 `Linux-Kbuild-Faster-v3` 两篇）。
- 本次实测基于 **v4 补丁系列**（2026-09-23 发到 LKML：`20260923-build-speedup-v4-0-73128809a4a4@kernel.org`）。

Stoakes 的补丁说明里给过一个参照：在一台**双路 AMD EPYC 9754（Bergamo）** 服务器上用 GCC，defconfig 构建时间从 **28 秒降到 20 秒**。

## 硬件账：这次实测用了什么

Phoronix 在**双路 EPYC 9575F** 上跑了实测，配置相当克制——**没有用 RAM 盘（TMPFS）、没有做任何激进调优**，就是库存 Ubuntu 26.04 LTS：

| 项 | 规格 |
|----|------|
| CPU | 双路 **AMD EPYC 9575F**（每路 64 核 / 128 线程） |
| 频率 | 单核 boost **5.0 GHz**，全核 boost **4.5 GHz** |
| L3 | 每路 **256 MB**（共 512 MB） |
| 内存 | **24 × 64 GB DDR5-6400 = 1.5 TB** |
| 存储 | 单块 **Samsung PM1743 3.84 TB PCIe Gen5 NVMe SSD**，EXT4 |
| 系统 | 库存 **Ubuntu 26.04 LTS** |

为什么是 9575F 而不是核心数更高的型号？文章点出一个反直觉事实：**只要编译器还不能并行编译单个源文件，最高的核心数未必最适合构建服务器**。GCC 早年有过 `-fparallel-jobs` 的尝试，但多年过去仍未落地。所以构建瓶颈在**构建编排的并行度**，而非裸核心数——9575F 的高频率 + 128 线程在此比「堆核心」更划算。

（文中也预告了更猛的** EPYC 9686F（Venice）**：96 核 / 192 线程、5.0 GHz boost、384 MB L3、配 MRDIMM-12800 与 PCIe Gen6 存储——这正是 Larabel 赌「能跨过 10 秒」的硬件。）

## 软件账：Kbuild 补丁做了什么

补丁系列本身没有公开逐行细节，但文章给出了它的**性质与目标**：

1. **定位 Kbuild 的并行瓶颈**：内核构建是一棵巨大的依赖树，很多环节传统上被串行化（如某些递归 make、依赖探测、生成头文件的前置步骤），补丁把其中可并行却被卡住的部分解开。
2. **AI 辅助找瓶颈**：Stoakes 明确借助 LLM 来发现这些「降低并行潜力」的代码路径——人写的补丁，AI 找靶点。
3. **收益与 CPU 无关**：文章强调，这套 pending 补丁**无论你用什么 CPU、干净构建还是增量构建，都能成比例地缩短时间**——它是构建系统的普适改进，不是某颗 CPU 的特例。

## 实测数字

Phoronix 在 EPYC 9575F 2P 上用 `Timed Linux Kernel Compilation` 基准（pts/build-linux-kernel）跑了 defconfig 与 allmodconfig 两种配置，并对比了「默认频率」与「AMD power determinism 模式」：

- **defconfig（x86_64 默认配置）**：
  - 基线（库存 Ubuntu 26.04，无补丁）：约 **20 秒**（9575F 2P 在 openbenchmarking 上长期是 defconfig 最快平台，通常 ~20 秒）。
  - 叠加 v4 补丁：从 **22 秒降到 15~17 秒**。
  - 再开 **AMD power determinism 模式**（一种把各核心拉到一致、可预测频率的调优）：最快一次 **15 秒**——一个**干净的 x86_64 defconfig 内核，15 秒编完**。
- **allmodconfig（编进所有 x86_64 相关模块）**：
  - 这套 pending 补丁砍掉了 **30 秒以上**的构建时间；在高端服务器上，**allmodconfig 终于逼近 2 分钟**。

## 边界与解读

**1. 标题的「10 秒」是预期，不是成绩。** 当前实测最好成绩是 15 秒；文章把 10 秒押在尚未上市的 EPYC 9686F + MRDIMM + PCIe Gen6 上。所以准确说法是「**逼近 10 秒**」，而非「达成 10 秒」。这也呼应了前作《Linux 7.4 内核构建或快 36%》里 AI 找瓶颈、人写补丁的主线——构建系统的边际收益还在持续释放。

**2. 收益结构是「编排并行度」而非「堆硬件」。** 这篇文章最有价值的工程启示是：当编译器还不能把一个 `.c` 并行化成多份时，**构建时间的第一杠杆是 Kbuild 的并行化质量**，而不是无脑加核心。9575F 选高频率而非最高核心数，正是这个判断的体现。

**3. 对内核开发者的实际意义。** defconfig 15 秒、allmodconfig 逼近 2 分钟，意味着 bisect 回归、反复干净构建的迭代成本大幅下降——尤其是 allmodconfig 省下的 30+ 秒，对需要全模块编译验证的维护者来说是直接的生产力。而这是**软件补丁**带来的，会向下游发行版普适传播。

**4. 为什么值得记。** 内核在变大，但构建在变快——这个反直觉现象的根因（Kbuild 并行化 + 高频率多核 CPU + AI 辅助定位瓶颈）本身就是 2026 年「AI 用于审查/优化、而非写代码」叙事的一块硬证据，与同期 `coding-assistants.rst`、Sashiko 等主线同源。
