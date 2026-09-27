---
title: "ReactOS 把 Wine 10.0 的 DirectX 栈整体搬进来了：解锁上百款游戏"
date: 2026-09-26
slug: reactos-wine-directx-10
tags: [ReactOS, Wine 10.0, DirectX, Vulkan, OpenGL, 兼容层, 游戏兼容, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "Phoronix"
original_author: "Michael Larabel"
original_date: 2026-09-26
original_url: "https://www.phoronix.com/news/ReactOS-Updated-Wine-DirectX"
description: "ReactOS 合并了基于 Wine 10.0 的 DirectX 栈大更新：新增 49.8 万行、删除 11.9 万行，可用 Vulkan/OpenGL 翻译 DirectX，解锁上百款游戏，DX10/11/12 兼容在望。"
published: true
---

> 原文：[ReactOS Lands Significant DirectX Stack Update From Wine For Enabling More Games](https://www.phoronix.com/news/ReactOS-Updated-Wine-DirectX)（Phoronix，2026-09-26）。本文为**译文 + 解读**。

## 一句话结论

ReactOS（致力于二进制兼容 Windows 应用/游戏/驱动的开源项目）合并了一次**重大 DirectX 栈更新**——把 **Wine 10.0 状态的 DirectX 代码**搬了进来。代价是开发者 **Justin Miller 累计 230+ 小时**的工作，结果是：**新增 49.8 万行、删除 11.9 万行旧代码**，并可借 **Vulkan / OpenGL 翻译 DirectX**，解锁**上百款游戏**，DX10/11/12 兼容已在路上。

## 这次更新做了什么

- **来源**：从 **Wine 10.0** 借来的 DirectX 实现，替换 ReactOS 原有的、带大量 hack 的旧栈。Pull request：[reactos/reactos#9352](https://github.com/reactos/reactos/pull/9352)。
- **规模**：合并代码 **49.8 万行新增、11.9 万行删除**——一个量级惊人的「重写式更新」。
- **翻译路径**：新栈让 ReactOS 能**用 OpenGL 与 Vulkan 来翻译 DirectX**（Vulkan 当前需 custom branch 或 mesa 软件渲染器才能跑）。
- **副作用**：清掉了 ReactOS 内部大量先前的 DirectX **hack**，并改善了该 DirectX 栈**在 Windows 自身上**的工作能力。
- **游戏收益**：Miller 在 PR 里说，这个 PR 配合其他待合并 PR，解锁的游戏数量在 **100 量级（hundreds）**。ReactOS 开发者在 X 上表示，**DX10 / 11 / 12 的游戏兼容**即将在 ReactOS 上成为可能。

## 解读

**1. 这是「站在 Wine 肩上」的典型胜利。** ReactOS 自己重写一套 DirectX 没意义，直接吸收 Wine 已经做好的、与上游同步的实现，是最省力的追赶路径。Wine 10.0 的 DX 栈被整体借入，等于 ReactOS 一次性补齐了多年差距。

**2. Vulkan/OpenGL 翻译是关键转折。** 能用 Vulkan/OpenGL 做 DX 翻译，意味着 ReactOS 不必原生实现每一代 DirectX——它借宿主的图形 API 做后端。这与 Wine/DXVK/VKD3D 的思路一致：**用现代图形 API 当翻译层**，而不是逐代复刻。

**3. 游戏兼容是 ReactOS 最被期待的能力。** 二进制兼容 Windows 的「圣杯」就是能跑 Windows 游戏。这次更新把目标从「能进桌面」推向「能跑 DX 游戏」，是项目吸引力的实质跃升——尽管 DX10/11/12 仍标着「即将」。

**4. 边界提醒。** 这是**合并进主干的大更新**，但「解锁上百款游戏」是开发者在原 PR 的预估，且依赖其他仍在 review 的 PR；DX10/11/12 是「即将」而非「已可用」。实际能跑哪些游戏，需等社区实测沉淀。
