---
title: "Intel NPU 驱动 1.39.1：15 行补丁铺垫一年，Nova Lake 正式可用"
date: 2026-11-21
slug: intel-npu-driver-1-39-1-nova-lake
category: 技术/解读
author: FreeLAMP.com
original_source: "Phoronix《Intel Linux NPU Driver 1.39.1 Released With Nova Lake Support》（Michael Larabel，2026-11-21）＋ Intel linux-npu-driver v1.39.1 GitHub Release Notes（2026-11-19）＋ 2025-10-21 IVPU 新增 NPU6 支持的邮件列表补丁（Maciej Falkowski）＋ 本号此前骁龙 NPU、Mesa Torx 两篇文章交叉核对。"
description: "解读 Intel Linux NPU Driver 用户态 1.39.1 版本：唯一新增功能是正式支持 Nova Lake 平台（第 6 代 NPU / NPU60xx），依赖此前已合入主线的 IVPU 内核驱动支持。梳理内核态 IVPU 与用户态 linux-npu-driver 的分工、15 行代码添加 PCI ID 与 NPU6 固件的过程、release notes 里的验证配置矩阵（Meteor/Arrow/Lunar/Panther/Wildcat/Nova Lake、内核 7.0.0-38、OpenVINO 2026.4.1 与尚未发布的 2026.5）、Level Zero 1.34.0 与固件版本要求，并说明这一代 NPU6 在架构上仍与 NPU5 同路径，功能差异有限。"
published: true
---

Intel 的 Linux NPU 用户态驱动更新到了 1.39.1，内容不多——**唯一的新增功能就是正式支持 Nova Lake 平台**。但这条看似平淡的点版本发布，背后是从去年秋天就开始的一整条上游化链条：先有 15 行内核补丁把第 6 代 NPU 塞进 IVPU 驱动，再有内核支持合入主线，最后才是用户态驱动跟上。

这正好是一个观察 Linux 硬件支持如何落地的标准样本，值得拆开看。

## 一、先把两层驱动分清楚

很多人看「NPU 驱动」是一个东西，其实在 Linux 上它是分层的：

- **内核态**：`intel_vpu` / IVPU 加速器驱动，在内核里管理设备、内存、任务提交，对外暴露 `/dev/accel/accel0` 这样的设备节点；
- **用户态**：`intel/linux-npu-driver` 这个仓库，提供 Level Zero 运行时、NPU 固件加载、tools 等，供 OpenVINO 这类 AI 框架调用。

硬件要真正可用，两层都得到位。Phoronix 这篇报道里那句「用户态更新依赖上游的 IVPU 内核驱动支持」，说的就是这个关系：光有用户态 1.39.1，内核不认识你的 NPU，照样没用。

## 二、15 行代码开启第 6 代 NPU

时间倒回 2025 年 10 月 21 日。Intel 的 Maciej Falkowski 往 dri-devel 邮件列表发了一个补丁，标题直白：「Add support for NPU6 generation that will be present on Nova Lake CPUs」。补丁内容只有 15 行：加一个新的 PCI 设备 ID（识别为 Intel NPU 60xx 系列），以及一个新的固件 blob 名字 `pu_60xx_v1.bin`。

补丁说明里最关键的一句是：**「和前几代一样，保持兼容性，所以没有大的功能变化」**。也就是说，NPU6 在驱动层面走的是和 NPU5（Panther Lake、Wildcat Lake 上的第 5 代）完全一样的代码路径。这与同期 Nova Lake 的其他上游化动作形成对照——Xe3P 图形支持、Clang 22 编译器目标、以及其他早期硬件使能，那些是真正的新架构；NPU 这边目前更像「新 ID + 新固件」。

当时的报道留了个悬念：NPU6 后续会不会暴露新特性，还是就此和 NPU5 差不多？从 1.39.1 的 release notes 看，至少现阶段答案是后者——没有提到任何新的 NPU6 专属功能，只有平台支持。

## 三、1.39.1 到底带来了什么

v1.39.1 于 11 月 19 日发布，GitHub Release Notes 写得很清楚：

**Highlights**：新增 Nova Lake 平台支持；并特别提示——**Nova Lake 的 NPU 推荐使用尚未发布的 OpenVINO 2026.5**。这是一句值得留意的预告：你现在用 2026.4.1 也许能跑，但 Intel 自己推荐等下一版工具包。

**验证配置矩阵**（Lists 都基于 Ubuntu 24.04 LTS 与 26.04 LTS、内核 `7.0.0-38-generic`）：

| 平台 | NPU 系列 / 固件标识 |
|------|------|
| Meteor Lake | MTL_CLIENT_SILICON-NVR+NN-deployment |
| Arrow Lake | 同 Meteor Lake 的固件串 |
| Lunar Lake | NPU40xx |
| Panther Lake | NPU50xx |
| Wildcat Lake | NPU50xx |
| **Nova Lake** | **NPU60xx** |

一张表把 Intel 近几代 NPU 的代号序列摆得很清楚：MTL → NPU4（Lunar Lake）→ NPU5（Panther/Wildcat Lake）→ NPU6（Nova Lake）。这里能看出 Intel 的 NPU 命名和 CPU 代号并不是一一对应的——Meteor Lake 是第一代、Arrow Lake 复用其固件串，Lunar Lake 才是 NPU4，别被数字搞混。

**配套组件版本**：Level Zero v1.34.0、OpenVINO 2026.4.1、NPU 编译器 `npu_ud_2026_44_rc1`（基于 OpenVINO 的 `88f8c6b` 提交）、GPU 驱动 26.40.40196.15（来自 `ppa:kobuk-team/intel-graphics`）。注意这套配置里 GPU 驱动来自 PPA，说明当前的 NPU 开发栈整体还偏「开发/验证」色彩，不是开箱即用的稳定发行版组合。

**安装步骤**也透露出同样的信号：把用户加进 `render` 组（`sudo gpasswd -a ${USER} render`）、`newgrp render`、可选重启，然后检查 `/dev/accel/accel0` 和 `dmesg` 里的 `intel_vpu` 信息——这是文档里给开发者/早期采用者的流程，不是普通桌面用户点几下就好的东西。

## 四、怎么读这条新闻：小版本，大链条

Phoronix 把它写成一条短新闻是可以理解的——1.39.1 从功能角度确实只有一个 Nova Lake 支持。但把时间线连起来看，它讲的是一个很典型的 Linux 硬件支持故事：

1. **2025 年 10 月**：Intel 发 15 行内核补丁，给 IVPU 驱动加 NPU6 的 PCI ID 和固件名；
2. **随后**：补丁合入主线，成为 Intel IVPU 加速器驱动的一部分；
3. **2026 年 11 月**：稳定内核里带上 IVPU 支持（验证配置用的是 7.0.0-38），用户态 1.39.1 发布，正式宣布 Nova Lake 可用；
4. **下一步**：等尚未发布的 OpenVINO 2026.5 给出官方推荐的工具链。

从「芯片有这个 IP」到「用户态驱动说支持」，中间隔了大约一年。这段时间花在让内核认识新设备、让固件和编译器对上号、让 OpenVINO 能正确调用上——这就是 Linux 上硬件支持落地的真实速度，也解释了为什么本号此前写骁龙笔记本时会说「NPU 是 AI PC 叙事里 Linux 上成熟度最低的一环」：内核通道打通只是第一步，用户态工具链和框架支持往往还要再等一轮。

对比一下 Mesa 的 Torx 路线就更有意思了：那条路试图用统一的 Gallium ML / NIR 抽象，让同一个 PyTorch/ExecuTorch 程序跑到不同厂商的 NPU 上；而 Intel 这条是典型的「厂商全栈」——自己的 IVPU 内核驱动、自己的用户态驱动、自己的编译器、推荐自己的 OpenVINO 版本。两条路线各有各的道理，但前者想解决的是「NPU 生态碎片化」，后者解决的是「让自家芯片尽快能用」。对普通用户来说，短期内能用的还是后者。

## 五、给准备上手 Nova Lake NPU 的人

如果你手上真有 Nova Lake、想在 Linux 上用 NPU，按 release notes 的要求过一遍清单：

- **内核**：确认 `intel_vpu` / IVPU 支持已进内核，验证矩阵用的是 `7.0.0-38-generic` 这一类版本；
- **固件**：需要对应 NPU60xx 的固件（`Oct 28 2026*NPU60xx*...` 这一串），旧固件不行；
- **用户态**：装 v1.39.1 或更新版本；
- **工具链**：Level Zero 1.34.0、OpenVINO 2026.4.1 是当前验证组合；如果 Intel 推荐的 2026.5 已发布，优先用它；
- **权限与设备节点**：把用户加进 `render` 组，`ls /dev/accel/accel0` 确认设备存在，`dmesg | grep intel_vpu` 看驱动初始化信息。

一句话总结：1.39.1 本身是个小版本，但它标志着 Nova Lake 的 NPU 从「内核里有补丁」走到了「用户态正式支持」。第 6 代 NPU 在代码层面目前仍是 NPU5 的近亲，真正值得期待的，是还没发布的 OpenVINO 2026.5 会不会带来更多 NPU6 专属能力。

## 参考资料

- Phoronix 原文：https://www.phoronix.com/news/Intel-LInux-NPU-Driver-1.39.1
- Intel linux-npu-driver v1.39.1 Release Notes：https://github.com/intel/linux-npu-driver/releases/tag/v1.39.1
- 2025-10-21 NPU6 内核补丁（Maciej Falkowski，dri-devel）：https://lore.kernel.org/dri-devel/20251021141948.2216735-1-maciej.falkowski@linux.intel.com/
- Phoronix 2025 年报道《Intel Nova Lake To Feature 6th Gen NPU》：https://www.phoronix.com/news/Intel-Nova-Lake-6th-Gen-NPU
