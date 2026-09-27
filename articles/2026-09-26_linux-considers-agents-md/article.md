---
title: "Linux 考虑引入 AGENTS.md：给 AI/LLM 代理一份内核贡献指南"
date: 2026-09-26
slug: linux-considers-agents-md
tags: [Linux内核, AGENTS.md, AI代理, AI补丁, 内核治理, Sasha Levin, 译文]
category: Linux/运维
author: FreeLAMP.com
original_source: "Phoronix"
original_author: "Michael Larabel"
original_date: 2026-09-26
original_url: "https://www.phoronix.com/news/Linux-Considers-AGENTS-MD"
description: "Linux 内核考虑引入 AGENTS.md——一份面向 AI/LLM 代理的内核贡献指引。Sasha Levin 提案，目前仅链接 README，并非所有人都赞成。"
published: true
---

> 原文：[Linux Kernel Developers Consider Adding AGENTS.md To Help Guide AI/LLM Agents](https://www.phoronix.com/news/Linux-Considers-AGENTS-MD)（Phoronix，2026-09-26）。本文为**译文 + 解读**。

## 一句话结论

面对 AI/LLM 代理**持续轰炸（bombarded）** 内核邮件列表的补丁，内核至今没带一份面向 AI 代理的 `AGENTS.md` 指引文件。一个**补丁系列**提议终于引入它——但**目前内容只是链接到 README**，而且**并非所有人都买账**。

## 提案细节

- **提案人/线程**：补丁由 **Sasha Levin** 发出，LKML 线程：`20260924134945.3095661-1-sashal@kernel.org`。
- **做什么**：在内核仓库中加入一个 `AGENTS.md`，用来给 AI/LLM 代理**说明贡献规范**——也就是「如果你是个自动化代理，想给内核提补丁，请先读这个」。
- **当前形态**：这个初版**只是链接到内核的 README 文件**，并没有写出一套独立的、针对代理的细则。换句话说，它现在是一个「占位 + 方向」，而非一份成型的指南。
- **争议**：Phoronix 明确写道「**not all are in favor at this point**」——至少部分内核开发者对引入 `AGENTS.md` 持保留态度。具体反对理由原文未展开。

## 背景：为什么这件事会浮出水面

这与本仓此前多篇「内核 + AI」线索同源：

- 网络子系统 maintainer **Jakub Kicinski** 在 Linux 7.3 pull request 里直言 net/net-next 被 AI 驱动的低优先级补丁「**完全淹没**」；
- 内核已在 2026 年落地 **`coding-assistants.rst`**：AI 参与须用 `Assisted-by:` 标签声明，AI 不能用具有法律效力的 `Signed-off-by`；
- Jonathan Corbet 在 Kernel Recipes 2026 的《The Kernel Report》里把「**accelerated change**」与「着眼 10 月 Maintainers Summit」并列提出。

`AGENTS.md` 是这套「**把 AI 贡献者纳入可被机器读取的规范**」努力的延续——`coding-assistants.rst` 是给人/maintainer 看的责任边界，`AGENTS.md` 则试图让**代理本身**在动手前先读到规则。

## 解读

**1. 它的象征意义大于当前内容。** 一个只链接 README 的 `AGENTS.md` 当下不产生硬约束，但它标志着内核社区在认真考虑「**让自动化代理成为可被文档引导的一类贡献者**」。

**2. 争议点很可能是「该不该为代理单列一份文件」。** 反对者或许认为：规则已经写在 `coding-assistants.rst` / `SubmittingPatches` 里，再搞一份 `AGENTS.md` 是重复，甚至是在「承认」代理是理应被特殊对待的一等公民。这与 `coding-assistants.rst` 当年「声明但不优待」的克制立场是一致的张力。

**3. 与上游 AGENTS.md 风潮对齐。** 2025-2026 年 `AGENTS.md` 在开源仓库里迅速普及（类比 `README`/`CONTRIBUTING`），作为给编码代理的机器可读指引。内核的讨论是这股风潮蔓延到**规模最大、流程最严格**的 C 项目之一。

**4. 边界提醒。** 本篇是**新闻 + 提案解读**，非最终结论：补丁**尚未合并**，且存在反对声音。是否真进主线、内容是否会从「链接 README」扩展成实质指南，需看后续 LKML 讨论与 10 月 Maintainers Summit。
