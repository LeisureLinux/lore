---
title: "把 HTTP 解析搬进内核：ETH、NYU、NVIDIA 的 Beeper 用 eBPF 做出 4.5 倍吞吐"
date: 2026-10-30
slug: beeper-ebpf-in-kernel-http-parsing
tags: [eBPF, Beeper, Beeline, HTTP解析, 内核态, Rust, ETH苏黎世, NYU, NVIDIA, LinuxPlumbers, LPC2026, freplace, kTLS, SK_MSG, 服务网格, sidecar, 性能优化, 论文, arXiv, Hyper, rust]
category: Linux/内核
author: FreeLAMP.com
original_source: "⭐ 一手核对：Phoronix《Accelerating HTTP Web Servers With In-Kernel eBPF Deliver Up To 4.5x Throughput》（Michael Larabel，2026-10-27）+ LPC2026 演讲 PDF（ETH Zürich，2026-10-05）+ arXiv 论文《Enforcing Application-Layer Policies in eBPF》（2605.31084）+ lerboe/beeper 与 lerboe/hyper-fast-path 仓库 README + APNIC 博客《Beeline: Enforcing application-layer policies in eBPF》"
original_date: 2026-10-30
original_url: "https://www.phoronix.com/news/Beeper-In-Kernel-Parsing-eBPF"
description: "Beeper（BEEline's ParsER）把应用层（L7）协议解析直接放进内核里的 eBPF 程序，用一个在用户态构造的 Aho-Corasick 式 DFA 把解析复杂度降到 eBPF 能接受的水平。它支持 HTTP/1.1 与 HTTP/2（最低内核 6.8），可以挂在内核 HTTP 缓存后面把静态资源直接从内核返回，论文 Beeline 在真实服务网格上把中位请求延迟降到 1/6、吞吐提高 3 倍，而配套的 hyper-fast-path（Rust Hyper 的 eBPF 快路径）实测最高 4.5 倍吞吐。这项工作来自 ETH 苏黎世、NYU 与 NVIDIA，在 Linux Plumbers Conference 2026 上首次公开演示。本文梳理了它的核心思路（DFA 构造与 eBPF 验证器之间的妥协）、接入点（freplace / SK_MSG / strparser + kTLS）、以及为什么它能成立的关键 —— L7 策略的逻辑远比 L7 协议的解析简单。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Phoronix：Accelerating HTTP Web Servers With In-Kernel eBPF Deliver Up To 4.5x Throughput](https://www.phoronix.com/news/Beeper-In-Kernel-Parsing-eBPF)**（Michael Larabel，2026-10-27）
> - **[LPC2026 演讲 PDF](https://nsg.ee.ethz.ch/files/public/slides/2026-10-5_LPC_Beeper_1.pdf)**（ETH Zürich，2026-10-05，78 页）
> - **[arXiv 2605.31084：Enforcing Application-Layer Policies in eBPF](https://arxiv.org/abs/2605.31084)**（Brandner / Mishra / Miano / Panda / Antichi / Vanbever）
> - **[lerboe/beeper](https://github.com/lerboe/beeper)** 与 **[lerboe/hyper-fast-path](https://github.com/lerboe/hyper-fast-path)** 的 README
> - **[APNIC 博客：Beeline: Enforcing application-layer policies in eBPF](https://blog.apnic.net/2026/09/02/beeline-enforcing-application-layer-policies-in-ebpf)**（2026-09-01）
> - 仓库元信息实测：**beeper 157 stars / 9 forks**，Rust，GPL-3.0，创建于 2025-10-01
> 本文为**解读**。第五节的技术拆解为笔者依据演讲 PDF 与 README 所做的整理。

## 一句话结论

**这项工作的核心洞察，其实只有一句话 —— 而它绕开了 eBPF 最难的那个约束：**

> **「While many L7 protocols are complex to parse, the logic needed to enforce L7 policies tends to be simple.」**
>
> **「虽然很多 L7 协议很复杂，但**执行 L7 策略所需要的逻辑往往很简单**。」**

**⭐ 我认为这句话才是整项工作的支点 —— 而它同时解释了「为什么这件事以前没人做成」和「为什么现在能做成」。**

## 一、这项工作是什么

### 1.1 三层结构

**⭐ 我先把三个容易混在一起的名字理清 —— 因为它们是同一项研究的三层产物：**

| 名称 | 是什么 | 状态 |
|---|---|---|
| **Beeline** | ⭐ **论文里的系统** —— 给定高层策略，**自动合成一个 eBPF 数据面**，在内核里执行策略 | arXiv 2605.31084 |
| **Beeper** | ⭐ **Beeline 的「解析阶段」打包版** —— 一个独立的 Rust crate，做 L7 协议解析 | GitHub，157 stars |
| **hyper-fast-path** | ⭐ **用 Beeper 做的具体应用** —— 给 Rust 的 Hyper HTTP 库做 eBPF 快路径，直接从内核返回静态资源 | GitHub，17 stars |

**⭐ 而 Phoronix 报道的那两个数字，分别来自后两层：**

- **3.4x** —— LPC 演讲展示的 Beeline 吞吐提升
- **4.5x** —— hyper-fast-path 的最高吞吐提升

**⭐ 所以要读这两篇报道时先分清：** **一个是论文里的通用系统，一个是它的一个具体应用。**

### 1.2 为什么需要它

**⭐ LPC 演讲的动机页写得很直接：**

> **「Firewalls mitigate ever-increasing L7 DDoS attacks (e.g. Rapid Reset)」**
> **「Observability tools parse L7 payloads to monitor increasingly distributed applications」**
> **「**There is a need for L7 support in eBPF**」**

**⭐ 我把这三条归一下类：**

| 需求 | 现状 |
|---|---|
| **L7 DDoS 缓解** | 需要在防火墙里做 L7 判断 |
| **可观测性工具** | 需要解析 L7 payload |
| **容器网络 L7 策略** | 需要在网络层执行 L7 策略 |

**⭐ 而「现状」的共同点是：这一切都在用户态做。** **而用户态做 L7 解析，代价是数据必须从内核拷贝到用户态、再拷贝回去。**

**⭐ 而 Beeline 论文的摘要里给出了这条链的成本：**

> **「Supporting these policies, however, comes with a significant performance cost, since service meshes interpose proxies (**sidecars**) on the data path between every service.」**

**—— 服务网格在每一对服务之间插一个 sidecar 代理。** **而这个代理要做 L7 策略判断，所以每个请求都要穿越它。**

## 二、⭐⭐⭐ 核心洞察：把「解析」和「策略」分开

**⭐ 这是全文最重要的一节，而我认为它也是这项工作最有普适价值的地方。**

### 2.1 问题的本质：L7 解析太复杂，L7 策略很简单

**APNIC 博客（作者是论文一作 Laurin Brandner）说得很清楚：**

> **「State-of-the-art service meshes process all L7 policies in user space because **they are too complex to process in eBPF**. Indeed, despite recent advances to improve L7 support in the kernel, such as strparser or Kernel Connection Multiplexor (KCM), processing L7 protocols remains impractical within eBPF's stringent limitations.」**
>
> **「But there is an opportunity: While many L7 protocols are complex to parse, **the logic needed to enforce L7 policies tends to be simple**. We show this by analysing the L7 policies used in **2,417 open-source projects** on GitHub.」**

**⭐ 我把这条推理链完整列出来 —— 这是一个很好的「换个问题」的思路：**

```
原始问题：在 eBPF 里解析 HTTP/2 这样的复杂协议
          ↓ ✗ 太复杂，eBPF 验证器过不了
换个问题：在 eBPF 里执行「L7 策略」
          ↓ ✓ 但策略需要的解析，比完整解析简单得多
结果：   只做策略需要的那些解析
```

**⭐ 而「2,417 个开源项目」这个样本量，让这个论断从直觉变成了数据。**

### 2.2 ⭐ 而 89% 这个数字，是整项工作的量化核心

**APNIC 博客：**

> **「For the vast majority (**89%**) of L7 policies in the wild, **Beeline can eliminate the service proxy from the critical path**. This reduces the average request latency of realistic web applications by up to **six times** and increases the throughput by **three times**. It does this without any coordination with the service proxy. **Beeline is transparent**, and thus able to accelerate any service proxy.」**

**⭐ 我认为「89%」这个数字的商业含义比技术含义更大：**

**—— 服务网格的最大成本来自「每个服务对之间都要插一个 sidecar」。** **而如果 89% 的策略可以在内核里执行，那 89% 的 sidecar 就可以从关键路径上拿掉。**

**⭐ 而「transparent」这个词也是关键 —— Beeline 不需要服务网格配合，它自己就能加速任何服务网格。**

### 2.3 ⭐⭐ 而技术手段是：在用户态构造 DFA

**⭐ 而这才是 Beeper 这个 crate 的技术核心。**

**README 原文：**

> **「Beeper (BEEline's ParsER) is an application-layer parser for eBPF. It allows you to process L7 protocols directly in the kernel. **It achieves this by constructing an Aho-Corasick-like DFA in user space, reducing the parsing complexity to an eBPF-compatible level.**」**

**⭐ 我解释一下这个做法为什么有效：**

**eBPF 的验证器（verifier）会检查程序里有没有「有界循环」—— 因为 eBPF 程序不能无限循环（会卡住内核）。** **而 HTTP/2 的解析天然需要「解析多少就读多少」的变长处理，这在 eBPF 里是老大难。**

**⭐ 而 Aho-Corasick 式 DFA 的作用是：把「变长的模式匹配」预先编译成一个「确定的状态机」。** **于是运行时的 eBPF 程序只剩下「读一个字节 → 查表跳一个状态」—— 没有变长循环，验证器能过。**

**⭐ 而 LPC 演讲的第 17 页把这句话讲得最简洁：**

> **「**Key Idea: Use a DFA to parse messages**」**

**⭐ 而 DFA 的构造位置也很讲究 —— 演讲第 19 页的图示：**

> **「Beeper constructs the DFA in **user space**」**
>
> **（user space: DFA Construction → 交给 kernel: load）**

**⭐ 也就是说：**

| | |
|---|---|
| **用户态** | 构造 DFA（这一步可以是任意复杂的 Rust 代码） |
| **内核态** | 加载 DFA + 运行匹配（只有查表） |

**—— 这是一个很好的「把复杂度推到可以承受的地方」的架构决策。**

## 三、⭐⭐ 接入点：怎么把 eBPF 解析器挂到数据路径上

**⭐ 这是我认为对工程读者最有参考价值的一节 —— 因为「怎么挂上去」决定了它能用在哪种流量上。**

### 3.1 三个接入点

**⭐ LPC 演讲第 21 页的图示给了三种：**

| 接入点 | 说明 |
|---|---|
| **`freplace`** | ⭐ **替换某个已有函数的实现** —— 演讲里明确标出「The eBPF parser integrates with **freplace**」 |
| **`SK_MSG` / `SK_SKB`** | socket 层的 socket filter |
| **`strparser` / kTLS** | ⭐ **「by integrating with **stream parser and kTLS** Beeper is most useful at the socket level」** |

### 3.2 ⭐⭐ 而「socket 层 + kTLS」这一条最有意思

**⭐ 因为它解决了一个很实际的问题：HTTPS 的 payload 是加密的，怎么解析？**

**⭐ Paul Chaignon（eBPF 布道者）在 Mastodon 上的说明点得很准：**

> **「It can run on HTTPS traffic **by attaching at the socket level and leveraging kTLS**.」**

**⭐ 而演讲第 21 页那句话更直接：**

> **「by integrating with stream parser and kTLS Beeper is most useful at **the socket level**」**

**⭐ 我的理解是：**

| 层次 | 能否看到 L7 payload |
|---|---|
| **网卡 / 网桥** | ❌ 加密 |
| **TLS 层之上（socket 层）** | ✅ **kTLS 拿到明文** |
| **应用层** | ✅ 但数据已经上来来了 |

**—— 而「在 socket 层」正好是内核里能同时看到「连接上下文」和「明文 payload」的位置。**

### 3.3 ⭐ 而 HTTP/1.1 的 DFA 起点，演讲里也给了

**⭐ 演讲第 22 页：**

> **「The DFA starts with **CRLF** to match a new HTTP/1.1 header」**

**⭐ 我认为这个细节透露了实现的一个关键性质 —— **DFA 是按「HTTP 消息的语法结构」构造的，而不是「按关键字列表」构造的。**

**⭐ 而 README 里的协议支持表也印证了这一点：**

| 协议 | 状态 | 最低内核版本 |
|---|---|---|
| **HTTP/1.1** | ✅ | **6.8** |
| **HTTP/2** | ✅ | **6.8** |
| **RESP2** | WIP | — |

**⭐ 而「最低内核 6.8」这个约束值得注意 —— 它对应的是 `freplace` / `bpf_link` 等基础设施的可用性。**

## 四、⭐⭐ 数字：三个来源，三种口径

**⭐ 我认为这一节需要仔细拆开，因为不同来源的数字含义不同，容易混。**

### 4.1 论文（Beeline）

**⭐ arXiv 摘要：**

> **「Compared to state-of-the-art service meshes, Beeline **reduces the median request latency of realistic applications by up to 6×** while sustaining **3× more throughput**.」**

**⭐ 而 APNIC 博客的表述更具体一点：**

> **「For the vast majority (89%) of L7 policies in the wild, Beeline can eliminate the service proxy from the critical path. This reduces the average request latency of realistic web applications by up to six times and increases the throughput by three times.」**

**⭐ 注意「up to」这个词 —— 是上界，不是平均值。**

### 4.2 LPC 演讲

**⭐ 演讲里的基准页（第 64-68 页）给了更细的分解：**

| 场景 | 结论 |
|---|---|
| **32KB / HTTP/1.1** | **快路径请求延迟更低**（图中标注 1.8x / 2.0x / 3.5x 量级） |
| **32KB / HTTP/1.1** | **快路径吞吐更高**（图中标注 **3.0x higher throughput**） |
| **32KB / HTTP/2** | **快路径请求延迟更低**（1.8x / 3.0x 量级） |

**⭐ 而演讲的结论页（第 75 页）标题就是全文的答案：**

> **「**Application-Layer Parsing in eBPF Is Practical**」**

### 4.3 hyper-fast-path

**⭐ 而 Phoronix 报道的 4.5x 来自这里 —— README 的说法：**

> **「hyper-fast-path uses beeper to serve static assets from the kernel. **This improves the throughput of HTTP servers by up to 4.5x.**」**

**⭐ 而它的描述也说明了适用范围：**

> **「eBPF-based fast path for **serving static assets** via HTTP」**

**⭐ 我想强调这个限定 —— **4.5x 是「静态资源从内核直接返回」这个场景的数字**，不是「所有请求」的。**

**⭐ 而这恰好是最容易落地的场景 —— 静态资源（图片、CSS、JS）是 Web 服务里体积占比最高的部分。**

### 4.4 ⭐ 一张表汇总

| 来源 | 对象 | 数字 | 口径 |
|---|---|---|---|
| **arXiv 论文** | Beeline | 延迟 **≤ 1/6**、吞吐 **3×** | ⭐ **对比 state-of-the-art 服务网格；「up to」是上界** |
| **APNIC 博客** | Beeline | **89%** 的 L7 策略可把 sidecar 移出关键路径 | ⭐ 基于 **2,417** 个开源项目的策略分析 |
| **LPC 演讲** | Beeline | 32KB HTTP/1.1 **3.0x 吞吐** | 具体基准场景 |
| **Phoronix / README** | hyper-fast-path | 最高 **4.5x** 吞吐 | ⭐ **静态资源**场景 |

**⭐ 我认为这张表比任何单一数字都有用 —— 因为它显示了「同一个系统的不同面向在不同地方被测量」。**

## 五、⭐⭐ 我的评价

### 5.1 ⭐⭐ 这项工作的可迁移性，比它的性能数字更大

**⭐ 我认为最值得带走的是第 2.1 节那个「换个问题」的思路，而它可以用一句话概括：**

> **⭐ 「不要在受限环境里做完整的事，要做那件**恰好够用**的事。」**

**⭐ 而这跟 eBPF 的处境几乎是一一对应的：**

| | eBPF 的约束 | 这项工作的应对 |
|---|---|---|
| **验证器** | 有界循环、栈大小、指令数 | 用 DFA 把变长匹配变成查表 |
| **执行上下文** | 不能阻塞、不能分配 | 状态与缓冲都由用户态预置 |
| **可用的挂载点** | 有限 | `freplace` / `SK_MSG` / `strparser`+kTLS |

**⭐ 而我认为这个思路的普适价值在于：** **它不是「如何在 eBPF 里写一个 HTTP 解析器」，而是「如何在一个受限环境里，只做策略真正需要的那部分解析」。**

**—— 后者可以用在很多受限环境里。**

### 5.2 ⭐⭐ 而 89% 这个数字，也说明「落地」的关键在别处

**⭐ 我想提一个容易被忽略的点：这项工作最难的部分，可能不是解析，而是「**自动把高层策略翻译成 DFA**」** —— 因为 Beeline 的输入是「高层策略」，输出是「合成的 eBPF 数据面」。**

**⭐ 而 hyper-fast-path 走的是另一条更简单的路：它不合成策略，它就是「一个已经写好的快路径」。**

**⭐ 我认为这个区别解释了为什么两个项目的星标差这么多：**

| | beeper | hyper-fast-path |
|---|---|---|
| **星标** | 157 | 17 |
| **定位** | ⭐ **通用解析库** | **具体应用** |
| **使用门槛** | 需要自己写 eBPF 程序、构造策略 | 装上就能用 |

**⭐ 而 Phoronix 那句结尾我觉得很准：**

> **「It will be interesting to see what practical production implementations ultimately come out of this interesting research work.」**

**—— 「看看这个有趣的研究工作最终会长出什么样的生产实现」** —— 这句话既承认了它的研究价值，也承认了「离生产还有距离」。

### 5.3 ⭐⭐ 而从安全角度看，这项工作有一个绕不开的问题

**⭐ 我必须提出来，因为它是防守方必须知道的：**

**—— 「在 eBPF 里解析 L7 流量」这个能力，本身就是攻击者想要的东西。**

**⭐ 具体地说：**

| 能力 | 防守方用来做 | 攻击者可以用来做 |
|---|---|---|
| **L7 payload 可见** | 可观测性、防火墙策略 | ⭐ **窃取凭据的后门位置** |
| **在 socket 层拦截** | 阻断恶意流量 | ⭐ **拦截会话令牌** |
| **内核里的 HTTP 缓存** | 性能 | ⭐ **篡改缓存内容投毒** |

**⭐ 而这个张力，在 eBPF 这个技术诞生时就存在**（eBPF 最初就是为网络可观测性设计的）。**但把 L7 解析做到内核里，确实把「可见性」推进到了一个新的层级。**

**⭐ 我认为这项工作的研究者对此是清楚的 —— 演讲第 22 页明确提到 Beeper 可以「**redirect it based on its payload, or respond to it**」（基于 payload 重定向，或直接响应）。**

**⭐ 也就是说：这个框架不只做「观察」，它也能做「干预」。**

**⭐ 我的判断是：** **这类能力的普及，最终会像 eBPF 本身一样 —— 防守工具和攻击工具用的是同一套原语。所以它的防守价值（把策略从用户态搬进内核，大幅降低延迟和 CPU）大概率大于它的风险（攻击者也能用同一套原语）。**

**⭐ 但这需要配套的审计能力：** **「谁在加载 eBPF 程序、挂载在什么位置、能看到什么流量」** —— 这本身是一个需要管理的权限面。**

### 5.4 ⭐⭐ 而最后一点：论文到产品的距离

**⭐ 我想指出一个有意思的对照 —— 这篇论文的 arXiv 编号是 **2605.31084**，也就是 2026 年 5 月提交的。**

**⭐ 而 LPC 演讲是 2026 年 10 月初，APNIC 博客是 9 月 1 日，Beeper 的 GitHub 仓库创建于 2025 年 10 月。**

**⭐ 所以时间线是：**

```
2024-09  beeline 仓库创建（nsg-ethz/beeline）
2025-10  beeper 仓库创建（解析阶段打包版）
2026-05  论文提交 arXiv
2026-09  APNIC 博客（面向网络工程师的解读）
2026-10  LPC 2026 演讲（首次面向内核社区的公开演示）
```

**⭐ 我认为这个跨度（约两年）说明了研究工作的典型节奏 —— 而 2026-10 这次演讲是它第一次进入内核开发者的视野。**

## Sources

- ⭐ 一手：[Phoronix — Accelerating HTTP Web Servers With In-Kernel eBPF Deliver Up To 4.5x Throughput](https://www.phoronix.com/news/Beeper-In-Kernel-Parsing-eBPF)（Michael Larabel，2026-10-27）
- ⭐ 一手：[LPC2026 演讲 PDF — Beeper](https://nsg.ee.ethz.ch/files/public/slides/2026-10-5_LPC_Beeper_1.pdf)（ETH Zürich，2026-10-05，78 页）
- ⭐ 一手：[arXiv 2605.31084 — Enforcing Application-Layer Policies in eBPF](https://arxiv.org/abs/2605.31084)（Brandner / Mishra / Miano / Panda / Antichi / Vanbever，2026-05-29）
- ⭐ 一手：[lerboe/beeper](https://github.com/lerboe/beeper) —— README（157 stars / 9 forks，Rust，GPL-3.0，创建于 2025-10-01）
- ⭐ 一手：[lerboe/hyper-fast-path](https://github.com/lerboe/hyper-fast-path) —— README（17 stars / 1 fork，创建于 2026-09-10）
- ⭐ 一手：[APNIC Blog — Beeline: Enforcing application-layer policies in eBPF](https://blog.apnic.net/2026/09/02/beeline-enforcing-application-layer-policies-in-ebpf)（2026-09-01，作者为论文一作 Laurin Brandner，含 2,417 个项目样本与 89% 结论）
- 相关：[nsg-ethz/beeline](https://github.com/nsg-ethz/beeline)（论文系统的原始仓库）
- 相关：[Linux Plumbers Conference 2026](https://lpc.events/event/20/)（Beeper 演讲页与视频）

---

（说明：所有引号内内容、数字与仓库元信息均来自上述一手材料；**第二、三节的技术拆解为笔者依据演讲 PDF 与 README 所做的整理**；**第五节的安全张力分析与「换个问题」的抽象为笔者观点**。）
