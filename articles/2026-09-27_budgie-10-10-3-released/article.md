---
title: "Budgie 10.10.3 发布：Budgie Menu 终于支持收藏夹，Labwc 桥接与 oo7 密钥服务跟进"
date: 2026-09-27
slug: budgie-10-10-3-released
tags: [Budgie, 桌面环境, Linux桌面, Wayland, Labwc, oo7, Secret Service, 译文]
category: Linux Distributions
author: FreeLAMP.com
original_source: "Phoronix"
original_author: "Michael Larabel"
original_date: 2026-09-27
original_url: "https://www.phoronix.com/news/Budgie-10.10.3-Released"
description: "Budgie 10.10.3 桌面点发布：Budgie Menu 新增收藏夹、Labwc 桥接改进（按键绑定/多媒体启动键/可靠性）、可指定主显示器、桌面图标自由摆放，并加入 oo7 Secret Service 支持。"
published: true
---

> 原文：[Budgie 10.10.3 Released With Favorites In Budgie Menu, Labwc Bridge Improvements](https://www.phoronix.com/news/Budgie-10.10.3-Released)（Phoronix，2026-09-27）。本文为**译文 + 背景解读**。

## 一句话结论

**Budgie 10.10.3** 是 Budgie 桌面的最新点发布，最受关注的是 **Budgie Menu 终于支持「收藏夹（Favorites）」**——可以把应用加入收藏。此外 **Labwc 桥接**得到多项改进、可指定主显示器、桌面图标可自由摆放，并加入 **oo7 Secret Service** 支持以对齐新的密钥服务提供者。

## 主要变更

**1. Budgie Menu 新增「收藏夹」**
这是本版最显著的改动：**终于可以给 Budgie Menu 里的应用加收藏夹**。在此之前，Budgie Menu 缺少这个被多数桌面视为基本功能的入口。

**2. Labwc 桥接改进**
Budgie 10.10 推荐搭配 **Labwc**（一个 Openbox 式的 Wayland 合成器）使用，而 Budgie 与 Labwc 之间的 **Labwc bridge** 在本版得到增强：
- **按键绑定（keybinding）** 改进；
- **多媒体 / 启动器按键（multimedia/launcher key）** 处理改进；
- **可靠性** 改进。

**3. 可指定主显示器**
新版本新增**指定主显示器（primary monitor）**的能力。

**4. 桌面图标可自由摆放**
本版允许把**桌面图标摆放在桌面任意位置**（此前摆放能力受限）。

**5. oo7 Secret Service 支持**
Budgie 10.10.3 加入 **oo7 Secret Service** 支持，以对齐这个新出现的密钥服务提供者。

更多细节见 [Buddies of Budgie 官方博客](https://buddiesofbudgie.org/blog/budgie-10-10-3-released)；下载见 [GitHub 发布页](https://github.com/BuddiesOfBudgie/budgie-desktop/releases/tag/v10.10.3)。

## 背景与解读

**1. Budgie 是什么，谁在做**
Budgie 是一个以简洁、现代为取向的 Linux 桌面环境，最早由 **Solus** 项目发起；如今由社区组织 **Buddies of Budgie** 维护。它的定位接近「传统布局但现代观感」的桌面，与 GNOME 的激进方向保持距离。

**2. Labwc 路线是 Budgie 的 Wayland 答案**
Budgie 10.10 起明确推荐搭配 **Labwc**（Openbox 风格的 Wayland 合成器）而非自己造一个完整合成器。本次桥接改进（按键绑定、多媒体键、可靠性）说明这条「Budgie 面板/壳 + Labwc 合成器」的 Wayland 路线仍在打磨可用性——尤其多媒体键和启动器键是日常体验的硬需求，此前这类桥接往往有疏漏。

**3. oo7 出现在 Budgie，呼应更大的桌面密钥服务迁移**
`oo7` 是一个较新的 Secret Service 实现。值得注意：在前面本仓覆盖的 **Fedora 45 Beta** 里，`oo7` 已成为 **GNOME/KDE 共同的默认 Secrets Service**。Budgie 10.10.3 跟进 `oo7 Secret Service` 支持，是桌面生态**向同一新密钥服务提供者对齐**的一个小信号——这类「基础组件收敛到同一实现」的动向，往往比单个桌面的小特性更值得记。

> 边界说明：Budgie 与 oo7 / Fedora 45 的关联，是基于本仓已发文章的合理观察，非 Phoronix 原文内容；Budgie 官方博客是更完整的变更来源。

**4. 版本定位**
10.10.3 是 10.10 系列的小点发布，主题是「补齐基础体验」（收藏夹、主显示器、桌面图标自由摆放）+「巩固 Wayland/Labwc 路线」+「对齐密钥服务」。没有架构级大改，但对日常使用的完整度提升是实打实的。
