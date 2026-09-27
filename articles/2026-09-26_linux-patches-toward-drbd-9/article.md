---
title: "为 DRBD 9 进主线铺路：LINBIT 发出重构现有内核 DRBD 8.4 代码的准备补丁"
date: 2026-09-26
slug: linux-patches-toward-drbd-9
tags: [DRBD, LINBIT, 分布式复制块设备, 内核主线, 高可用, 存储, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "Phoronix"
original_author: "Michael Larabel"
original_date: 2026-09-26
original_url: "https://www.phoronix.com/news/Linux-Patches-Toward-DRBD-9"
description: "LINBIT 开发者发出准备补丁，把内核里现有的 DRBD 8.4 目标代码重构成 DRBD 9 状态，为把约 15 年树外 DRBD 改动 upstream 进主线内核铺路。"
published: true
---

> 原文：[New Patch Series Working Toward DRBD 9 Support In The Linux Kernel](https://www.phoronix.com/news/Linux-Patches-Toward-DRBD-9)（Phoronix，Michael Larabel，2026-09-26）。本文为**译文 + 背景解读**。

## 一句话结论

LINBIT 的开发者本周发出一组**准备（prep）补丁**，目标是把 Linux 内核里**现有的 DRBD 8.4 目标代码**更新到 **DRBD 9 状态**——为把 LINBIT 约 **15 年**积累的 DRBD（Distributed Replicated Block Device，分布式复制块设备）树外改动 **upstream 进主线内核**铺路。这批补丁本身**不是 DRBD 9 主体**，而是「先对齐代码组织、抬高上限」，后续真正的 DRBD 9 补丁预计「不会太远」。

## 背景：DRBD 是什么，为什么这事值得记

**DRBD** 是 Linux 上成熟的**分布式复制块设备**——它把两台（或多台）机器的块设备通过网络实时镜像，构成同步复制的「网络 RAID 1」，是大量**高可用（HA）集群**的存储底座（常配合 Pacemaker/Corosync，承载数据库、虚拟化存储等）。DRBD 的用户态工具 `drbd-utils` 与内核模块长期并存：用户态早已演进到 **DRBD 9**（支持多副本、更灵活的复制拓扑），但**内核主线里的代码仍停留在 DRBD 8.4 时代**。

之所以出现「主线旧、树外新」的断层：LINBIT（DRBD 的商业背后公司）持续维护着**树外（out-of-tree）内核驱动**，而主线里的 DRBD 代码**停滞不前**。于是主线内核自带的 DRBD 与 LINBIT 实际发布的 DRBD 9 之间，积累了约 **15 年**的功能落差。把这段历史代码 upstream 进主线，是这个项目的长期目标——今年早些时候 LINBIT 就启动了这项工作（Phoronix 此前报道过「15 年代码改动」的 upstreaming 目标）。

## 本周补丁系列做了什么

- **发起方/署名**：补丁由 **LINBIT 的 Christoph Böhmwalder** 发出（LKML 线程：`20260923140608.1116713-1-christoph.boehmwalder@linbit.com`）。
- **性质**：**prep 准备补丁**，还不是 DRBD 9 的功能主体。
- **内容**：
  1. **重构现有内核 DRBD 8.4 代码**，使其代码组织**对齐 LINBIT 的树外 DRBD 9 代码**；
  2. **抬高各项限制（limits）**，使其取值**匹配 DRBD 9** 的参数范围（例如资源/连接/设备等上限，以贴合 9 代的多副本能力）。
- **目的**：先做这些准备性改动，让后续「真正的 DRBD 9 补丁」在主线上的合入路径更顺——Phoronix 原话：「希望这些 prep 之后，剩余的 DRBD 9 补丁不会太远（hopefully the rest of the DRBD 9 patches for mainline won't be too far behind）。」

## 状态与边界

- **当前状态**：这批 prep 补丁**已在 LKML 发出供评审**，但**整个 DRBD 9 主线化的大更新尚未合入**。
- **边界提醒**：本文是**短新闻 + 背景**，不是「DRBD 9 已进入主线」。实际进展取决于 prep 补丁的评审反馈，以及后续 DRBD 9 主体补丁能否被主线 maintainer 接受。是否最终进主线、时间线如何，需跟 LKML 与后续 Phoronix 报道。
- **对运维者的现实意义**：若 DRBD 9 最终进主线，意味着**不用再装树外 DKMS 模块**就能用上现代 DRBD 9 能力（多副本、更灵活的复制），HA 存储栈的部署与内核升级摩擦会下降。但眼下，生产环境仍应以 LINBIT 的树外 DRBD 9 驱动 / 发行版打包为准。
