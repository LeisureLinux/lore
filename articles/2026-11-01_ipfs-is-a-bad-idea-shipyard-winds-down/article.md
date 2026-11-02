---
title: "「IPFS 是个坏主意」：一个 Reddit 帖子，和它背后那场刚刚结束的退场"
date: 2026-11-01
slug: ipfs-is-a-bad-idea-shipyard-winds-down
tags: [IPFS, Filecoin, 去中心化存储, 内容寻址, CID, DHT, 固定pinning, 网关gateway, Shipyard, ProtocolLabs, libp2p, Kubo, Helia, Boxo, BadBitsDenylist, inbrowserlink, 技术主权, 开源治理, 供应链, 分布式系统, 加密货币]
category: 技术/架构
author: FreeLAMP.com
original_source: "⭐ 一手核对：Reddit r/ipfs《IPFS is a bad idea.》（2026-11）+ Shipyard 官方公告《The end of IPFS at Shipyard》（2026-08-24）+ Protocol Labs 官方《IPFS is moving beyond the sponsored gateways》（2026-08-25）+ Netcraft 分析（2026-09-29）+ CryptoBriefing 报道（2026-08-25）+ Filecoin Onchain Cloud 主网上线公告（2026-08-12）"
original_date: 2026-11-01
original_url: "https://www.reddit.com/r/ipfs/comments/1xld8y2/ipfs_is_a_bad_idea/"
description: "一个 Reddit 帖子的核心论断是：「IPFS 什么都没解决，我猜某人只是想把他 2021 年 100 欧元的 Filecoin 砸盘套现。」而这个帖子出现的时机，恰好在 IPFS 生态的一次结构性退场之后 —— 2026 年 8 月 24 日，核心维护方 Shipyard 宣布因 Protocol Labs 不续约经费而将于 9 月 30 日全面停止 IPFS 相关工作，Kubo、Helia、Boxo、Rainbow、IPFS Desktop 一夜之间失去专职维护者，ipfs.io / dweb.link / 引导节点 / Wikipedia-on-IPFS 等公共基础设施同时停运。本文逐条核对了那个帖子的四个论断（匿名性、比 HTTP/BitTorrent 更快、比云存储便宜、消除单点故障），指出其中哪些成立、哪些混淆了不同层次的「去中心化」；并梳理了退场的完整时间线与三个关键转折（Shipyard 当初成立的原因恰恰是「避免维护依赖单一组织的预算决定」、libp2p 已于 2025 年 9 月先一步移交社区、而 Protocol Labs 转向「超越受资助网关」的新资助模型），最后给出我自己的判断：IPFS 真正的价值从来不是「更便宜的 CDN」，而是内容寻址提供的「可独立验证」，而这个价值恰好正被另一种商业模式接住 —— Filecoin Onchain Cloud 于 2026-08-12 在主网上线，用「数据持有证明」把「谁替你保存」也变成了可验证的。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Reddit r/ipfs：IPFS is a bad idea.](https://www.reddit.com/r/ipfs/comments/1xld8y2/ipfs_is_a_bad_idea/)**（2026-11）
> - ⭐ **[Shipyard 官方：The end of IPFS at Shipyard](https://ipshipyard.com/blog/2026-the-end-of-ipfs-at-shipyard/)**（**2026-08-24**）
> - ⭐ **[Protocol Labs 官方：IPFS is moving beyond the sponsored gateways](https://blog.ipfs.tech/2026-08-beyond-sponsored-gateways/)**（**2026-08-25**）
> - **[Netcraft：As Shipyard Winds Down, IPFS Phishing Enters a New Phase](https://www.netcraft.com/blog/as-shipyard-winds-down-ipfs-phishing-enters-a-new-phase)**（2026-09-29，含钓鱼面分析与 Bad Bits Denylist 前景）
> - **[CryptoBriefing：Shipyard winds down IPFS work as Protocol Labs ends funding](https://cryptobriefing.com/shipyard-ipfs-protocol-labs-funding-ends/)**（2026-08-25）
> - **[Filecoin Onchain Cloud 主网上线](https://www.tradingview.com/news/coinmarketcal:26e555e98094b:0-filecoin-onchain-cloud-goes-live-on-mainnet-12-aug-2026/)**（2026-08-12）
> ⚠️ **本文为**解读**。第四节的逐条核对为笔者对原帖论断的分析；第七节「三个层次的去中心化」为笔者提出的框架。

## 一句话结论

**⭐ 那个帖子的四个论断，有三个是错的、一个是半对的 —— 但它挑的时间点，比它的论证更有价值。**

**⭐ 因为它出现的时候，IPFS 生态刚发生了一次真正的退场：**

> **2026 年 8 月 24 日，Shipyard 宣布因 Protocol Labs 不续约经费，将于 9 月 30 日全面停止 IPFS 相关工作。**

**⭐ 而这一次的讽刺性，Shipyard 自己在公告里写了出来 —— 而且是在为成立原因做总结时说的：**

> **「Protocol Labs created Shipyard specifically to avoid the scenario where IPFS maintenance depended on a single organization's budget decisions. **Two years later, a single organization's budget decision is exactly what killed the arrangement.**」**
>
> **（CryptoBriefing 语）**

**⭐ 我认为这一句是这篇解读该从这里开始的原因 —— 而不是在讨论 IPFS 好不好用。**

## 一、那个帖子说了什么

**⭐ 原帖的正文很短，我原样引用：**

> **「IPFS doesn't solve any issue at all, i think someone just wanted to sell and dump their filecoins when they were 100 euros each in 2021.」**
>
> **「* Anonymous file sharing? No.**
> **\* Faster file sharing than HTTP or BitTorrent (DHT)? No.**
> **\* Do i pay less than a traditional cloud subscription for storage? Absolutely not.**
> **\* Does it solve centralized architecture (SPOF)? No, a centralized service must keep existing or even being paid to keep the content pinned inside the network.」**

**⭐ 而它的核心指控是最后一行的逻辑：**

**—— 既然还需要「中心化服务把内容 pin 在网络里」，那 IPFS 就没有解决中心化架构问题，只是把中心化搬到了别处。**

**⭐ 而这个指控，坦白说，**在它自己的层次上是成立的**。**

**⭐ 但问题在于 —— 它把三层不同的「去中心化」混成了一层来评判。**

## 二、⭐⭐ 而它挑的时间点：一次刚刚结束的退场

**⭐ 在评价那四个论断之前，先把背景摆清楚 —— 因为这才是这个帖子真正的信息量。**

### 2.1 ⭐ 时间线

| 日期 | 事件 |
|---|---|
| **2024 年初** | ⭐ **Shipyard 成立** —— 由 Protocol Labs 孵化，**目的正是「把 IPFS 网关的维护从单一组织手里拿走」** |
| **2024** | Shipyard 接手两大公共网关 **`ipfs.io`** 与 **`dweb.link`**，以及 IPFS 相关的核心实现 |
| **2025-09** | ⭐ **`libp2p` 维护权移交给社区维护者**（Shipyard 参与，2025 年 9 月完成）—— **这是可复制的模板** |
| **2026-05** | **`ipfs.io` 与 `dweb.link` 开始重定向到 `inbrowser.link`**（基于 Service Worker 的浏览器内网关）** |
| **2026-08-12** | ⭐ **Filecoin Onchain Cloud 主网上线** —— 用「数据持有证明」（Proof of Data Possession）把「谁替你保存数据」变成可验证的** |
| **2026-08-24** | ⭐⭐ **Shipyard 宣布 9 月 30 日全面停止 IPFS 相关工作** |
| **2026-08-25** | ⭐ **Protocol Labs 发布「IPFS is moving beyond the sponsored gateways」，说明新的资助模型** |
| **2026-09-29** | Netcraft 发布钓鱼面分析：**随着 Shipyard 退场，攻击者获得新的试探空间** |
| **2026-09-30** | ⭐ **Shipyard 正式终止运营** —— 引导节点等公共基础设施停运 |

### 2.2 ⭐⭐ 而「停了哪些东西」才是重点

**⭐ Shipyard 官方公告里列的清单（原文）：**

**失去专职维护者的项目：**
> **「Kubo, Helia, Boxo, Rainbow, IPFS Desktop, IPFS Companion, Someguy, Service Worker Gateway, IPFS Check, and others.」**

**⭐ 而我对这几个做一个定位说明 —— 因为它们不是「周边工具」，而是这个生态的骨架：**

| 项目 | 是什么 | 谁在用 |
|---|---|---|
| **Kubo** | ⭐ **IPFS 的参考实现** —— 「大多数节点运营者跑的那个版本」 | 绝大多数 IPFS 节点 |
| **Helia** | ⭐ **JavaScript 实现** —— 浏览器与 Node.js 应用依赖它 | 前端 / Node 生态 |
| **Boxo** | ⭐ **给 Go 开发者的可复用 IPFS 构件** | Go 生态项目 |
| **Rainbow** | ⭐ **IPFS Desktop** | 桌面用户 |
| **Service Worker Gateway** | ⭐ **浏览器内网关**（`inbrowser.link`）| **浏览器直接访问 IPFS** |

**⭐ 而停运的公共基础设施（原文）：**
> **「ipfs.io, dweb.link, check.ipfs.network, delegated-ipfs.dev, **the IPFS bootstrap nodes**, collaborative cluster infrastructure such as **Wikipedia-on-IPFS**, and related services.」**

**⭐ 我想强调「**bootstrap nodes**」这一条 —— 因为它的技术含义比看起来严重：**

**⭐ 新加入 IPFS 网络的节点，需要先从引导节点（bootstrap node）拿到网络里的其他节点地址，才能开始 DHT 查找。**

**—— 引导节点没了，新节点就「找不到路」。**

**⭐ 而 Netcraft 的分析正是针对这一点：**

> **「The loss of Shipyard's public infrastructure used in IPFS will affect the ability of in-browser service worker gateways when **hardcoded bootstrap nodes disappear** and infrastructure is not reliably available for routing.」**

### 2.3 ⭐⭐⭐ 而「谁来维护」的讽刺，比技术问题更值得看

**⭐ 我认为这是整个事件里最值得记的一层 —— CryptoBriefing 的表述非常准确：**

> **「There is a certain irony in what happened here. **Protocol Labs created Shipyard specifically to avoid the scenario where IPFS maintenance depended on a single organization's budget decisions. Two years later, a single organization's budget decision is exactly what killed the arrangement.**」**

**⭐ 而 Protocol Labs 自己的公告，把这件事的逻辑说完整了 —— 我把关键的两段引用出来：**

> **「While IPFS started with two canonical implementations and free public gateways, there are now **more than a dozen active implementations** and community-driven libraries: Javascript nodes that run in a browser tab, modular libraries that make content addressing work with a wider variety of network topologies, service worker gateways that fetch and verify content client-side, mature self-hosted gateways, and paid pinning and retrieval providers.」**
>
> **「As the IP Shipyard team winds down their work, IPFS is shifting toward **what keeps an open protocol healthy: specs, conformance tests, implementation diversity, grants to maintainers and builders, migration guides**, and more agile support for the most-used libraries and tools.」**
>
> **「**What's not changing is that IPFS is still IPFS**: open protocols for storing, verifying, routing, and sharing data across distributed networks. You should still be able to **verify data yourself, move between providers**, and use IPFS building blocks to create systems that don't fall over when one server or one company goes away.」**

**⭐ 而最后那句是 Protocol Labs 对「IPFS 还有意义吗」的回答：**

> **「As AI makes code cheap and endless, **the scarce thing is no longer software but agreement**: the protocols that let independently built systems work together, and the people who coordinate and apply them to solve real-world problems. **Protocols encode who holds power**, which is why we'll continue work at that layer.」**

**⭐ 我把这段话的转变提炼出来 —— ⭐ 这是一次「资助对象」的根本性转移：**

| | 2024 年成立 Shipyard 时 | 2026 年退场后 |
|---|---|---|
| **资助目标** | ⭐ **运行具体的网关与实现**（服务）** | ⭐ **规范、一致性测试、实现多样性、迁移指南**（标准）** |
| **隐含假设** | 「IPFS 是**产品**」 | ⭐ 「IPFS 是**协议**」 |
| **风险** | ⭐ **服务挂了就挂** | ⭐ **标准还在，实现可以换** |

## 三、⭐⭐ 退场带来的直接后果：钓鱼面

**⭐ 而 Netcraft 那篇（2026-09-29）讲的是退场的**副作用**，而这一面很少被讨论。**

**⭐ 核心机制：**

> **「As other Protocol Labs services wind down, the IPFS ecosystem is expected to shift toward **other gateway providers who may not have the same content policy maturity** and may choose not to enforce the **Bad Bits Denylist**.」**
>
> **「This creates the opportunity for **threat actors to test other gateway providers with trusted domains that are expected to become more familiar.**」**

**⭐ 我来解释这个攻击面是怎么被打开的：**

```
IPFS 上的钓鱼内容，本身由 CID 内容寻址保证「拿到什么就是什么」
        ↓
但用户实际访问的是「网关域名 + CID」—— 而域名是可以指向任意内容的
        ↓
所以「ipfs.io/某个可疑CID 是不是钓鱼」这道防线
        ↓
实际上靠的是 网关自己 挂的 Bad Bits Denylist（恶意 CID 黑名单）
        ↓
⭐ 而网关换人 → 黑名单策略可能不执行 → 这道防线失效
```

**⭐ 而 Netcraft 提到的第二层风险更微妙：**

> **「threat actors using IPFS fronting will likely see a mix of opportunities and **infrastructure loss**.」**

**—— 而这里的「infrastructure loss」指的是：⭐ 钓鱼站点用 IPFS 做前端托管时，如果引导节点没了、DHT 路由不稳，那钓鱼站点本身的可达性也会下降。**

**⭐ 换句话说：⭐ 这次退场对攻击者是双向的 —— 既多了新机会（网关政策不严），也少了基础设施（钓鱼站自己更难稳定上线）。**

**⭐ 而 Netcraft 还追了一条线：**

> **「Protocol Labs is expected to continue maintaining the **Bad Bits Denylist** … Netcraft is in contact with someone involved in the Bad Bits Denylist pipeline who plans to modernize it.」**

**⭐ 我认为「谁来维护那份黑名单」是这件事最值得追踪的后续 —— 因为它是 IPFS 网关生态里唯一的「内容审核」机制，而它完全是自愿的、单点的。**

## 四、⭐⭐ 逐条核对原帖的四个论断

**⭐ 现在回到那四个论断。我用一手材料逐条核对。**

### 4.1 「匿名文件分享？No」

**⭐ 原帖把它当成一个功能主张来否定。而这里需要先分清 IPFS 提供了什么：**

**⭐ IPFS 提供的是**内容寻址**（content addressing）—— 一个 CID 是内容的哈希。**

**⭐ 而「匿名」这个属性，其实来自**取 CID 的方式**，不是来自 IPFS 协议本身：**

| 获取 CID 的方式 | 匿名性 |
|---|---|
| **从公开渠道拿到**（网关、搜索引擎、DHT 爬取） | ⭐ **不匿名** —— 内容可被关联到发布者 |
| **通过 Tor / onion 服务发布** | ⭐ **强匿名** —— 而这正是 Shipyard 公告里列为「未竟事业」的一项：「pseudonymous hosting and retrieval through **Tor and onion services**」 |

**⭐ 所以我的核对结论是：**

> **⭐ **这个论断「方向对、表述不准」。** IPFS 本身不提供匿名，但**它允许你匿名** —— 而「允许」和「提供」之间的差别，在架构讨论里很关键。
> **⭐ **而且更有意思的是：那个让 IPFS 具备匿名能力的能力（Tor + onion），恰恰是 Shipyard 退场时「没来得及做完」的那个。**

### 4.2 「比 HTTP 或 BitTorrent(DHT) 更快？No」

**⭐ 这个论断我要分成两半看：**

**⭐ ① 「比 HTTP 快」—— 这是在比不同的东西。**

**⭐ IPFS 协议层是**内容寻址 + 分块 + DHT 查找 + （可选）Bitswap 交换**。而 HTTP 是**应用层协议**。**

**—— 严格说，IPFS 可以**跑在 HTTP 之上**（这正是 Shipyard 公告里说的「Advancing HTTP-native approaches to IPFS」）。**

**⭐ ② 「比 BitTorrent 快」—— 这里有一个真实的、值得说的技术点：**

**⭐ BitTorrent 的核心机制是「**你下到什么，就能从谁那里拿**」（swarm 交换）。而 IPFS 的核心机制是「**你找谁，就从谁那里拿**」（DHT 查找 + unicast）。**

**⭐ 而这个差异在实践中常常体现为：**

| | BitTorrent | IPFS |
|---|---|---|
| **热门内容** | ⭐ **越多人下，种子越多、越快** | ⭐ **找到谁就从谁拿（可能是慢节点）** |
| **长尾内容** | 需要 seed 在线 | ⭐ **需要「有人还留着」**（pinning 问题）** |
| **节点发现** | tracker（中心）** | ⭐ **DHT（无中心，但需要引导节点）** |

**⭐ 所以我的核对结论是：**

> **⭐ **这个论断「基本不成立，但问错了问题」。** IPFS 的设计目标从来不是「比 BitTorrent 快」，而是「**不需要 tracker**」—— 那是在 2001 年 tracker 中心化背景下出发的设计目标。
> **⭐ **而今天真正的对比对象不是 BitTorrent，是「**HTTP + CDN**」—— 而在这个对比里，IPFS 输在延迟和缓存命中（浏览器没有 IPFS 缓存、每次都要做内容协商），赢在可验证性与不依赖单一服务商。**

### 4.3 「比云订阅便宜？Absolutely not」

**⭐ 这一条是四个里最实的，而且**原帖说对了**。**

**⭐ 证据在官方自己的文档里 —— Protocol Labs 公告里列出了付费 pinning / retrieval 服务商：**

> **「paid pinning and retrieval providers (Pinata, Filebase, Lighthouse & more)」**

**⭐ 而 Filecoin Foundation 自己五周年回顾里那段话，等于是对这条论断的官方确认：**

> **「Without economic incentives and cryptographic guarantees, IPFS content only lasted as long as someone, somewhere, kept hosting it out of goodwill or individual interest. **Over time, centralized pinning services emerged to serve demand for IPFS persistence but this created central failure points and vendor lock-in.**」**
>
> **「Filecoin was designed to answer the question: **"Who keeps the data in IPFS around?"**」**

**⭐ 我的核对结论是：**

> **⭐ **这条完全成立，而且比原帖说得更严重 —— 因为不只是「不便宜」，而是「**你必须付钱，才能得到『不消失』这个属性**」。**
> **⭐ **IPFS 给你的是「**内容寻址 + 可选的可持久性**」，而后者是要单独买的 —— 这不是缺陷，是它被设计成的样子。**

### 4.4 「消除中心化架构（SPOF）？No」

**⭐ 而这一条是**最需要拆解**的，因为它混了三个完全不同的「中心化」。**

**⭐ 我把这三个层次列出来（这个框架是我自己的归纳）：**

| 层次 | 内容 | IPFS 的状态 | 原帖的混淆 |
|---|---|---|---|
| **① 协议层** | 内容寻址、CID、签名验证、路由算法 | ⭐ **完全去中心化，且是 IETF/IETF 标准化的一部分** | |
| **② 基础设施层** | 网关、引导节点、固定服务、索引 | ⭐ **⭐ 高度集中 —— 而这次退场正好证明了这点** | ⭐ **原帖说的「SPOF」主要指这一层，而它是对的** |
| **③ 商业层** | 谁替你保存数据、付多少钱 | ⭐ **⭐ 已变成市场 —— Filecoin Onchain Cloud 就是答案** | |

**⭐ 而原帖的问题在于：它用 ② 的失败来否定 ① 的价值。**

**⭐ 而我核对的结果是：**

> **⭐⭐ **原帖在基础设施层的判断是对的**（这次 Shipyard 退场就是最强证据），**但在协议层和商业层的结论是错的**。
> **⭐ **而 ① 恰恰是 IPFS 唯一无可替代的东西 —— 也是这次退场唯一没有受损的东西。**

**⭐ 而这一层有非常硬的证据 —— IPFS Foundation 自己的年度回顾：**

> **「Content addressing has many uses, but two salient ones include **trusting that you're getting the data you really want** and ensuring that **data can be independently verified without relying on the power of a centralized authority**.」**

## 五、⭐⭐ 而真正接住「谁保存数据」这个问题的，是 Filecoin

**⭐ 而这一节是本文最关键的补充 —— 因为原帖（以及很多批评）都以为 IPFS 的答案是「没人负责保存数据」。**

**⭐ 而 2026-08-12 的 Filecoin Onchain Cloud 主网上线，正是对这个问题的正式回答：**

> **「The launch makes verifiable storage available as a live Filecoin capability. **Preserving existing CIDs while adding onchain proof of data possession** can support applications moving away from centralized pinning services without requiring their content references to change.」**
>
> **「The announcement establishes availability, but it **does not by itself demonstrate adoption** by applications or storage providers.」**

**⭐ 我把这个机制讲清楚 —— 因为它正好补上了 IPFS 二十年来的那块空缺：**

```
IPFS 原本的状态：
  内容寻址 ✅（内容不可变、可验证）
  但「谁替你保管这份内容」—— 靠 pin，或者靠别人好心
        ↓
Filecoin Onchain Cloud（2026-08-12 主网）：
  ⭐ 存储服务商必须周期性提交「数据持有证明」（Proof of Data Possession）
        ↓
  ⭐ 而这个证明是**链上可验证**的
        ↓
  ⭐ 而 CID **不变**（不需要改内容引用）
```

**⭐ 我认为这个设计有一个很值得学的地方：⭐ 它没有重新发明寻址，而是**在既有的 CID 体系上增加了一层可验证的持久性保证**。**

**—— 这意味着：从 IPFS 迁到 Onchain Cloud，内容的 CID 不变，应用的引用不用改。**

**⭐ 而这恰好回答了 CryptoBriefing 提出的那个问题：**

> **「For the Filecoin ecosystem specifically, Filecoin's storage network relies on IPFS addressing for content retrieval, and **any degradation in IPFS tooling could create friction for Filecoin-based applications**.」**

**—— ⭐ 也就是说：⭐ IPFS 生态的这次动荡，**直接关系到 Filecoin 这条线的可靠性**。而这也让「谁在维护 Kubo / Helia」从「开源社区事务」变成了「有商业 stakes 的事」。**

**⭐ 而这一层我认为是这次退场**唯一可能带来实际改善**的地方：**

**—— 当「维护 Kubo」从「Protocol Labs 的预算决定」变成「Filecoin 网络的商业需求」，⭐ 它的资金来源会比此前更稳定。**

## 六、⭐⭐ 那到底谁在说什么？

**⭐ 我觉得这个帖子最值得讨论的一点，是它揭示了生态内部一种真实的分裂 —— 而这分裂本身是有信息量的。**

**⭐ 我按「IPFS 给了什么」把生态里的声音分成三类：**

| 立场 | 核心主张 | 代表 |
|---|---|---|
| **协议派** | ⭐ **「IPFS 是内容寻址 + 可验证性，这个价值不会因为谁维护网关而消失」** | IPFS Foundation（Robin Berjon）；Protocol Labs 新公告 |
| **产品派** | ⭐ **「要的是可用性和成本，不是协议纯洁度」** | 托管服务商（Pinata / Filebase / Lighthouse）；以及那个 Reddit 帖子的立场 |
| **⭐ 基础设施派** | ⭐ **「公共基础设施必须有长期资金，否则『去中心化』只是叙事」** | Shipyard 自己的公告 |

**⭐ 而我认为这个帖子的立场属于第二类 —— 而它**并不是无知**，而是**优先级不同**。**

**⭐ 而且我要指出一个不对称：**

**⭐ 原帖把 IPFS 描述成「**什么都没解决**」，这个判断是关于**产品体验**的；而它用来支撑这个判断的证据是**关于架构层次**的（pinning 需要有人付费）。**

**⭐ 这就是它论证上的裂缝 —— ⭐ 也是这类批评最常见的一种形态：**

> **⭐⭐ **用一个层次的失败，去否定另一个层次的价值。**

**⭐ 而如果换成产品派的语言，同样的事实会变成完全不同的结论：**

**⭐ **「IPFS 让『内容可验证』这件事变成了基础设施；而『谁来保证它长期可用』这个问题，被市场（Filecoin）解决了。」**

**⭐ 而我认为这才是这个帖子在 2026 年 11 月出现、并且配着一次退场，最值得被讨论的原因：**

**⭐ **因为它问的问题，恰好是这两年 IPFS 生态用最贵的方式验证过的：⭐ 「你说你去中心化 —— 那你把维护者撤走试试？」**

## 七、⭐⭐⭐ 我的判断：三个层次的「去中心化」

**⭐ 我想用一个自己的框架来收尾 —— 因为我认为它是理解这件事最有用的工具。**

**⭐ 任何「去中心化系统」的宣传，都应该同时回答三个问题：**

| 层次 | 问题 | IPFS 的答案 | 这次退场的影响 |
|---|---|---|---|
| **① 协议** | ⭐ **「规则本身谁能改？」** | ⭐ **开放规范 + 多实现** | ⭐ **无影响** |
| **② 基础设施** | ⭐ **「今天谁在跑公共设施？」** | ⭐ **曾经是 Shipyard → 现在是 Protocol Labs + 社区** | ⭐ **⭐ 剧烈变化**（引导节点停运、网关换手）** |
| **③ 经济** | ⭐ **「谁为持久性买单、谁赚这个钱？」** | ⭐ **⭐ 已经是市场**（pinning 服务 + Filecoin）** | ⭐ **⭐ 反而更清晰了** |

**⭐ 我认为把这三层分开看，就能得出几个不那么容易错的结论：**

**① ⭐ 「IPFS 什么都没解决」是错的 —— 它解决的是 ① 层的问题，而这个层没有人能拿走。**

**⭐⭐ 而这次退场恰恰证明了 ① 层的韧性：⭐ 协议、规范、CID 生态、甚至 Filecoin 的链上存储，都还在。**

**—— 掉的是 ② 层的公共基础设施，而 ② 层从来就是「谁来付钱」的问题，不是「能不能」的问题。**

**② ⭐ 原帖说的 SPOF 是真的 —— 而且刚刚被验证了。**

**⭐ 而这恰恰说明「去中心化」这个标签需要被拆解成上面三层：**

> **⭐⭐ **IPFS 去中心化的是「内容寻址与验证」；**
> **⭐ **它从来没声称去中心化「谁替你保存文件」—— 那部分从第一天起就是 ③ 层的问题。**

**③ ⭐⭐ 而我认为最有意思的一点是 —— 这次退场让三个层次同时被「显影」了：**

```
① 协议     → 完好（IPFS 仍是 IPFS）
② 基础设施 → 剧变（引导节点停运、网关换手、黑名单政策存疑）
③ 经济     → 清晰（Filecoin Onchain Cloud 接管「谁保证持久」）
```

**⭐ 而原帖那个「IPFS 什么都没解决」的判断，**恰好在 ② 层是对的、在 ① 和 ③ 层是错的** ——**

**⭐ 而我最后想说的是 ⭐ 这件事对**做技术选型的人**最实际的启示：**

> **⭐⭐ **选 IPFS 不是选「一个更便宜的 CDN」，也不是选「一个更快的 BitTorrent」。**
> **⭐ **你选的是「**内容寻址 + 可独立验证**」这个属性，以及你**愿意为持久性单独付费**这个前提。**
> **⭐ **如果你的需求只是「便宜地存静态文件」，那这个帖子说得对 —— 你在用一套复杂的协议解决一个 CDN 就能解决的问题。**
> **⭐ **而如果你需要的是「**十年后这个链接还能取到，而且取到的还是它」** —— 那 IPFS 的核心价值恰恰在，而这次退场也没有伤到它。**

## Sources

- ⭐ 一手：[Reddit r/ipfs — IPFS is a bad idea.](https://www.reddit.com/r/ipfs/comments/1xld8y2/ipfs_is_a_bad_idea/)（2026-11）
- ⭐ 一手：[Shipyard — The end of IPFS at Shipyard](https://ipshipyard.com/blog/2026-the-end-of-ipfs-at-shipyard/)（2026-08-24，含失去维护者的项目清单与停运的公共基础设施清单）
- ⭐ 一手：[Protocol Labs / IPFS Blog — IPFS is moving beyond the sponsored gateways](https://blog.ipfs.tech/2026-08-beyond-sponsored-gateways/)（2026-08-25，新的资助模型与网关形态变化）
- ⭐ 一手：[Netcraft — As Shipyard Winds Down, IPFS Phishing Enters a New Phase](https://www.netcraft.com/blog/as-shipyard-winds-down-ipfs-phishing-enters-a-new-phase)（2026-09-29；Bad Bits Denylist 前景与钓鱼面变化）
- 一手：[CryptoBriefing — Shipyard winds down IPFS work as Protocol Labs ends funding](https://cryptobriefing.com/shipyard-ipfs-protocol-labs-funding-ends/)（2026-08-25；治理悖论的表述）
- 一手：[Filecoin Onchain Cloud 主网上线公告](https://www.tradingview.com/news/coinmarketcal:26e555e98094b:0-filecoin-onchain-cloud-goes-live-on-mainnet-12-aug-2026/)（2026-08-12；Proof of Data Possession 与 CID 保持不变）
- 一手：[Filecoin Foundation — Five Years of Filecoin](https://fil.org/blog/five-years-filecoin-what-we-ve-built-and-what-s-next)（2025-10-15；「谁保存 IPFS 数据」这个问题的官方由来）
- 一手：[IPFS Foundation — Content-Addressing: 2025 In Review](https://ipfsfoundation.org/content-addressing-2025-in-review/)（Robin Berjon，2026-01-15；内容寻址两个核心用途）
- 一手：[Shipyard — Keep Web3 Online（75M 月活）](https://ipshipyard.com/blog/2026-the-end-of-ipfs-at-shipyard/)

---

（说明：所有引号内内容与时间线均来自上述一手材料；**第四节的逐条核对、第六节的「协议/产品/基础设施」立场分类、以及第七节「三个层次的去中心化」框架为笔者观点**。）
