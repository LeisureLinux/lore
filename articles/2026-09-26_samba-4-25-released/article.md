---
title: "Samba 4.25 发布：实验性支持 SMB3 持久句柄，朝透明故障转移迈出一步"
date: 2026-09-26
slug: samba-4-25-released
tags: [Samba, SMB3, 持久句柄, 文件服务, Ceph RGW, 域加密, 译文]
category: 开源/工具
author: FreeLAMP.com
original_source: "Phoronix"
original_author: "Michael Larabel"
original_date: 2026-09-26
original_url: "https://www.phoronix.com/news/Samba-4.25-Released"
description: "Samba 4.25 带来实验性 SMB3 Persistent Handles（朝透明故障转移）、新 Ceph RGW VFS 模块、JSON 审计日志改进与默认 AES 域加密。"
published: true
---

> 原文：[Samba 4.25 Released With Experimental SMB3 Persistent Handles](https://www.phoronix.com/news/Samba-4.25-Released)（Phoronix，2026-09-26）。本文为**译文 + 解读**。

## 一句话结论

Samba 4.25（连接 Linux/Windows 的文件与打印共享服务的最新稳定版）最亮眼的特性是**实验性引入 SMB3 Persistent Handles**——这是朝**透明故障转移（transparent failover）** 能力迈进的一环。代价是每次 open/update/lease/close 都要**双份存储**，性能开销「显著」。

## 主要变更

**1. 实验性 SMB3 Persistent Handles（持久句柄）**
这是面向透明故障转移的关键能力。有了持久句柄，**SMB 客户端能在服务器重启或宕机后重新连接，并保留它此前持有的有效文件句柄**——也就是「不间断的文件访问」。代价很直接：每个 open/update/lease/close 操作都要做**双份存储（double storage）**，因此带来「significant」性能成本。Phoronix 原话定性为实验性，意味着默认未必开启、生产需评估。

**2. 新的 Ceph RGW VFS 模块**
4.25 新增一个 **Ceph Object Gateway（RGW）VFS 模块**，可以把 Ceph 对象网关的 bucket 直接以 **SMB 共享**的形式导出——把对象存储挂进 SMB 世界，对混合对象/文件访问的场景有用。

**3. JSON 审计日志改进**
审计日志（audit logging）的 JSON 输出得到增强，便于日志采集与 SIEM 接入。

**4. 域加密类型默认改为 AES**
域（domain）相关的加密类型（encryption types）**默认改为 AES**，跟上现代 Kerberos 加密套件基线。

**5. 其他更新**
随发布说明一并带来若干常规更新，完整清单见 [Samba.org](https://www.samba.org/) 的 v4.25 release notes。

## 解读

**1. 持久句柄是「高可用 SMB」拼图的一块。** 真正的透明故障转移（客户端几乎无感地切换到备节点）需要服务端支持持久句柄 + 底层共享存储 + 集群故障切换协同。Samba 这一步把**句柄在故障后仍有效**这个前提补上了，但「双份存储」的开销提示：它解决的是**可用性**，不是**零成本**——在 IO 敏感的共享上要权衡。

**2. Ceph RGW VFS 模块把对象与文件打通。** 对已经跑 Ceph 的团队，能直接用 SMB 把对象 bucket 暴露给 Windows 客户端，省掉一层网关节点。

**3. 默认 AES 是安全基线收敛。** 与业界把 Kerberos 加密往 AES 收的节奏一致，减少弱加密类型的暴露面。

**4. 值得记的点。** Samba 这条线常被忽略，但它恰恰是「Linux 服务器 ↔ Windows 客户端」文件共享事实上的桥梁；持久句柄 + Ceph 模块显示它在往**高可用 + 对象存储融合**方向演进。
