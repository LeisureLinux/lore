---
title: "Ubuntu 把 OpenPGP 也换成 Rust：Sequoia PGP 进入 26.10，未来或取代 GnuPG"
date: 2026-10-02
slug: ubuntu-sequoia-pgp
tags: [Ubuntu, Sequoia PGP, OpenPGP, GnuPG, Rust, uutils, 内存安全, 26.10, 密码学, 译文]
category: Linux Distributions
author: FreeLAMP.com
original_source: "Phoronix / OMG! Ubuntu / Ubuntu Discourse"
original_author: "Michael Larabel（Phoronix）；Joey Sneddon（OMG! Ubuntu）；richard-scott-mcnew（Ubuntu Discourse）"
original_date: 2026-10-02
original_url: "https://www.phoronix.com/news/Ubuntu-Rust-Sequoia-PGP"
description: "Ubuntu 26.10 把 Sequoia PGP（Rust 实现的 OpenPGP）纳入默认安装并移入 main 仓库，提供 sq/sqv 对应 gpg/gpgv；未来版本可能取代 GnuPG 成为默认 OpenPGP 工具链。同期 Rust Coreutils 过渡在 26.10 达成 100%，cp/mv/rm 也切换到 uutils。本文梳理 Sequoia 的现状、边界与决策点。"
published: true
---

> 原文：[Ubuntu's Next Rust Effort May See OpenPGP Replaced By Sequoia PGP](https://www.phoronix.com/news/Ubuntu-Rust-Sequoia-PGP)（Phoronix，2026-10-02，作者 Michael Larabel）；[Ubuntu 26.10 adds Rust-based Sequoia PGP to default install](https://www.omgubuntu.co.uk/2026/10/ubuntu-rust-pgp-sq)（OMG! Ubuntu，2026-10-01，作者 Joey Sneddon）；[Rust on Ubuntu 2026-09](https://discourse.ubuntu.com/t/rust-on-ubuntu-2026-09/87047)（Ubuntu Discourse，richard-scott-mcnew）。本文为**译文 + 解读**。

## 一句话结论

Canonical 工程师 **Richard Scott McNew** 发布了 Ubuntu 26.10 的 Rust 进展状态更新：**Sequoia PGP（用 Rust 写的现代、内存安全的 OpenPGP 实现）已进入 Ubuntu 26.10「Stonking Stingray」**，提供 **`sq` 和 `sqv`** 作为 **GNU Privacy Guard 的 `gpg` / `gpgv`** 的对应命令。**26.10 里默认仍是 OpenPGP（GnuPG）**，但官方明确表示：**未来版本中 Sequoia PGP「可能」成为 Ubuntu 的默认 OpenPGP 工具链**，在保持 OpenPGP 互操作性的同时迁移到现代的内存安全实现。同期，**Rust Coreutils 的过渡在 26.10 达成 100%**，`cp`、`mv`、`rm` 也切到了 Rust 版。

## 一、这条更新里说了什么

据 Phoronix 对 Ubuntu Discourse 帖子的转述，Discourse 原文这样描述 Sequoia PGP：

> 「**Ubuntu 26.10『Stonking Stingray』的另一项新内容是 Sequoia PGP**——一个用 Rust 编写的现代、内存安全的 OpenPGP 实现。Sequoia PGP 提供 **`sq` 和 `sqv`** 命令，作为 GNU Privacy Guard 的 **`gpg` 和 `gpgv`** 的对应物。**未来，Sequoia PGP 可能成为 Ubuntu 的默认 OpenPGP 工具链**，在迁移到现代的内存安全实现的同时，保持 OpenPGP 互操作性。」

**当前状态一句话**：**26.10 里默认的还是 GnuPG（OpenPGP）**，Sequoia 是**并列提供**；官方的措辞是「**可能**」（may）成为默认，**没有给出时间表**。

## 二、OMG! Ubuntu 补充的关键细节

Joey Sneddon 的报道把几个工程事实补齐了：

**1. 不只是「进仓库」，而是「进了默认安装集」。**
> Sequoia PGP 被纳入「Stonking Stingray」的**默认 seed（即预装）**，Canonical 还把 **`rust-sequoia-sq` 包移到了 `main` 仓库**，以便为它提供**官方支持**。

> ⚠️ 注意这里的分量：Ubuntu 的仓库分 `main`（Canonical 官方支持）与 `universe`（社区维护）。**移入 `main` 意味着这个包从「社区附带品」升格为「Canonical 承诺支持的组件」**——这是判断发行版认真程度的最硬指标之一。

**2. 但它现在还不是默认。**
> **`gpg` 仍然调用 GnuPG**，而 **`sq`**（或配置为使用 Sequoia 库的应用）才走 Sequoia。

**3. 官方的动机表述。**
> Canonical 表示，采用 Sequoia 能让 Ubuntu **在提供 OpenPGP 互操作性的同时**，受益于 Rust 版本「**更可维护、内存安全的基础**」。

**4. 怎么试。**
> 新版本可以**直接从命令行跑 `sq sign` 或 `sq verify`** 来体验。

**5. 这不是孤立的 Rust 变化。**
> Ubuntu 26.10 **开箱即用一整套 Rust 核心工具**，完成了从 25.10 开始的工作。**GNU 版的 `cp`、`mv`、`rm` 现在由 `uutils` 提供。**

## 三、背景：为什么是「100% Rust Coreutils」之后轮到 PGP

这条新闻不是孤立的，把它放进 Ubuntu 这两年的 Rust 路线里看才完整：

| 时间 | 事件 |
|------|------|
| **2025-10（25.10）** | Ubuntu **首次**默认携带 Rust 核心工具集；**Rust 版 sudo（sudo-rs）成为默认** |
| **2026-04（26.04 LTS）** | `cp` / `mv` / `rm` **因 TOCTOU（time-of-check to time-of-use）问题被扣在 GNU 版**；这些问题正是 Canonical 委托的 uutils 安全审计发现的 |
| **2026-09 上游** | TOCTOU 问题在 uutils 修复；**Rust Coreutils 0.12 发布** |
| **2026-09-16** | Ubuntu 26.10 草案发布 notes 更新为 **Rust Coreutils 过渡 100% 完成** |
| **2026-10-15** | **26.10「Stonking Stingray」正式发布** |
| **2026-10（本条）** | **Sequoia PGP 进入 26.10 默认安装、移入 `main`；未来或成默认 OpenPGP 工具链** |

**几个值得记住的细节**：

- **`cp`/`mv`/`rm` 的「拖后腿」不是闲话**：26.04 LTS 是 LTS，保守是应该的。**审计发现问题 → 修上游 → LTS 保持 GNU → 非 LTS 的 26.10 先切**，这个节奏本身是健康的工程流程。
- **审计带来了正外部性**：OSNews 评论里提到，uutils 团队**给 GNU coreutils 贡献了更多测试**，「uutils 通过的 GNU 测试比一年前 GNU 自己的测试还多」。**重写工作的副产品是整个生态的测试覆盖变厚**，这惠及 GNU、busybox、BSD 各家。
- **资金与治理**：Canonical 不只用了人家的代码。它是 **Trifecta Tech Foundation 的金牌赞助商**（每年 4 万欧元资助其 Rust 软件工作），还在 26.04 前**出资对 uutils 做了安全审计**。

## 四、Sequoia PGP 是什么：和 GnuPG 的关系

**Sequoia PGP 是 OpenPGP 的另一个实现**，不是新协议。两者关系可以用「**同一套协议，两套实现**」来理解：

| | **GnuPG（GPG）** | **Sequoia PGP** |
|---|---|---|
| 语言 | **C** | **Rust** |
| 命令 | `gpg` / `gpgv` | **`sq` / `sqv`** |
| 架构特点 | 多功能套件（加密/签名/密钥管理/agent 等） | **模块化的库 + CLI**（可嵌入其他程序） |
| 内存安全 | 传统 C，历史漏洞面较大 | **内存安全**（Rust 所有权模型在编译期挡住一整类漏洞） |
| 互操作性 | OpenPGP（RFC 4880/9580） | **同为 OpenPGP**（互操作是设计目标） |

**关键认知：`sq` 不是 `gpg` 的换皮，互操作靠的是协议而不是代码兼容。** OpenPGP 是开放标准，GnuPG 和 Sequoia 各自实现同一套协议，所以密钥、签名、加密消息可以互通。**发行版换默认实现，理论上不需要用户换密钥。**

> **为什么密码学组件对「内存安全」特别敏感**：GnuPG 处理的是**不可信输入**（别人发来的密钥、签名、加密邮件），历史上一整类 CVE（如 2018 年的 Libgcrypt/Enigmail 相关漏洞、CVE-2021-40530 等）都源于 C 的内存处理错误。**Rust 在编译期挡掉 use-after-free、越界、数据竞争这一类问题**——对「处理敌意输入的守护组件」来说，这是结构性收益。

## 五、解读

**1. Ubuntu 的 Rust 化是「按组件渐进替换」，不是「重写发行版」。**

把这两年的动作连起来看，模式非常清晰：**sudo-rs（25.10 默认）→ coreutils 全套（26.10 完成）→ Sequoia PGP（26.10 进入、未来默认）**。每一步都是**选一个边界清晰、有成熟上游的项目，先并存、后切换**。**没有一次性大爆炸**，而且每个组件都选在「有独立上游、有测试基线、可回退」的位置。

**这是发行版做大规模语言迁移的教科书节奏**。对比「重写整个桌面」那种路线，Ubuntu 选的是**从系统最底层的基础设施（sudo、coreutils、PGP）往上走**。

**2. 「进入 main 仓库」比「进入默认安装」更重要。**

很多发行版的 Rust 工具只是躺在 `universe` 里供人选用。**`rust-sequoia-sq` 移入 `main` 意味着 Canonical 把它纳入了官方支持与安全维护承诺**，LTS 安全更新、CVE 响应、发布工程都覆盖它。**这是「试验」与「路线」的分界线。**

**3. 「互操作」是这类替换能成立的前提，也是它最脆弱的环节。**

GnuPG 不只是一个命令行工具，它周边有一个**庞大的生态**：`gpg-agent`、`gpgme`、各邮件客户端的集成、`apt` 的签名链、keyserver 生态、smartcard/HSM 支持等。**Sequoia 替换的只是 `sq`/`sqv` 这层 CLI 入口；生态依赖的是 GnuPG 的库与 agent 体系。**

**所以现实的替换路径大概率是「按场景分批」**：先覆盖「验证签名 / 校验 deb 包」这类简单场景（`sqv` 对应 `gpgv`，这正是 `apt` 用的形态），再逐步处理 agent、密钥管理这类复杂场景。**「未来版本成为默认」这句话里，默认的范围是什么（仅 CLI？含 agent？含 apt 链？）比时间点更值得关注。**

**4. 对运维的实际影响：现在几乎没有，未来要留意三件事。**

- **现在**：26.10 上 **`gpg` 行为不变**，`sq` 多了个可用的替代；**脚本、CI、apt 全都不受影响**。
- **未来切换时要盯的三处**：
  1. **`gpgv` → `sqv`**：如果 `sqv` 成为 apt 验签路径，**验证失败的报错形态、exit code 是否与 GnuPG 完全一致**，CI 和自动化对这两点最敏感；
  2. **密钥与 agent 迁移**：`gpg-agent` 的 socket、缓存、passphrase 交互方式是否保持；
  3. **LTS 与中间版的差异**：LTS 大概率最后切，**跨 LTS/非 LTS 的行为差异会持续几个周期**。
- **建议**：**现在就可以在 26.10 的测试环境里跑 `sq sign` / `sq verify` / `sqv` 与 `gpg` 交叉验证**，把自己的密钥环互操作验证一遍。**等它真成默认时，你就有了现成的兼容性清单**。

**5. 更大的图景：Ubuntu 在赌「内存安全是可运营的工程目标」。**

从 sudo-rs 到 coreutils 再到 PGP，Ubuntu 选的都是**安全审计已完成、上游测试体系成熟、且与 GNU 版可互换**的项目。**它不是在追「用 Rust」的时髦，而是在执行一个可验证的替换清单**：每换一个组件，就少一类内存漏洞。**对一个服务器装机量极大的发行版来说，这是防守型安全的复利**。

**测试的正外部性值得单独一提**：uutils 给 GNU 补的测试最终**惠及所有实现**。这类迁移如果做对，**产出物不只是 Rust 版本，还有更厚的协议级测试基线**，这可能是这波 Rust 重写潮里最被低估的价值。

> 来源边界：本文基于 Phoronix（2026-10-02）、OMG! Ubuntu（2026-10-01）、Ubuntu Discourse《Rust on Ubuntu 2026-09》（richard-scott-mcnew，2026-08-31 发布、持续更新）以及 Phoronix/OMG! Ubuntu 对 Rust Coreutils 过渡的历史报道。**「未来成为默认 OpenPGP 工具链」是官方的意向表述（may），无时间表**；本文对其替换路径的分析（按场景分批、先 `sqv` 后 agent）为**基于生态结构的推断，非 Canonical 官方计划**。Sequoia PGP 与 GnuPG 的对比基于两者的公开架构资料，具体行为以实测为准。
