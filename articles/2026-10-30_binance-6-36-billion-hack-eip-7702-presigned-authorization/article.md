---
title: "史上最大规模加密盗窃：63.6 亿美元、20 分钟、10 条链 —— 而 Binance 说私钥没泄露"
date: 2026-10-30
slug: binance-6-36-billion-hack-eip-7702-presigned-authorization
tags: [Binance, 加密货币盗窃, EIP-7702, Pectra, 热钱包, 预签名, 签名基础设施, TraderTraitor, 朝鲜, 链上取证, 稳定币冻结, 洗钱, 以太坊, 比特币, TRM, Chainalysis, Elliptic, 供应链安全, DevSecOps]
category: 安全/事件分析
author: FreeLAMP.com
original_source: "⭐ 一手核对：TRM Labs《North Korea Steals USD 6.36 Billion From Binance in the Largest Hack in History》（2026-10-30）+ Binance 官方声明（Richard Teng / Binance 官方 X 账号）+ Chainalysis、Elliptic、BleepingComputer、AP、CNBC、BBC 交叉验证"
original_date: 2026-10-30
original_url: "https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history"
description: "2026 年 10 月 29 日晚，63.6 亿美元加密资产在约 20 分钟内从 Binance 的 10 条链上被转走 —— 是史上最大规模加密盗窃，也是 Bybit 案的 4 倍。TRM 与 Chainalysis 高置信度归因给朝鲜 TraderTraitor。技术核心不是私钥泄露（Binance 明确否认），而是「签名能力」被拿到：攻击者在 Ethereum 上用 EIP-7702 批量预签 50 个连续 nonce 的授权，只要有一个命中就把热钱包变成攻击者的扫款器；而另外 9 条链上是普通签名转账，说明被攻破的是跨链签名基础设施本身。本文逐条核对了 TRM 原文的链上数据、各发行方的冻结时间线、以及攻击者「用 10% 折价甩卖 3.25 亿 USDT 抢在冻结前换 ETH」的洗钱时间差，并给出防守方清单：监控 7702 delegation、签名策略拒绝非预期授权、签名基础设施按链与钱包层级隔离。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[TRM Labs 官方报告](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)**（2026-10-30，链上数据、冻结时间线、洗钱路径）
> - **Binance 官方声明**（Richard Teng 与 Binance 官方 X 账号，经 BleepingComputer 完整引用）
> - **交叉验证**：Chainalysis（独立归因 TraderTraitor）、Elliptic（冻结金额核算 + DPRK 溯源）、AP / CNBC / BBC / CoinDesk / The Guardian / New Scientist
> ⚠️ **本文为**解读**。所有金额、时间点、地址数量均取自上述一手材料；第八节的判断与「对非加密行业的映射」为笔者补充。
> ⚠️ **安全边界**：本文只做事件分析与防守复盘，**不提供任何可操作的盗取手法**，也不给出被盗资产的追踪地址。

## 一句话结论

**63.6 亿美元，20 分钟，10 条链 —— 而最反直觉的一点是：失窃方 Binance 自己说，私钥没泄露。**

**⭐ 我认为这条新闻真正值得技术读者看的，不是金额，而是这个反差：**

> **「没有密钥泄露」与「63.6 亿美元被转走」这两件事，可以同时成立。**

**因为被偷走的不是密钥，是「让密钥替你签字的能力」。**

**而这条能力，从准备到变现，整条链路上暴露出来的每一个设计选择 —— 批量预签、nonce 连续性、跨链签名不隔离、冻结与洗钱的时间差 —— 都是可以在别的系统里复现的。**

## 一、事件轮廓：20 分钟，十条链

**TRM 的第一段「Key takeaways」把这个事件的骨架给全了：**

> **「On October 29, 2026, an attacker moved approximately USD 6.36 billion out of Binance wallets on ten blockchains, most of it in about 20 minutes starting at 20:05 UTC. That makes this the largest crypto theft on record, about four times the USD 1.5 billion Bybit hack of February 2025.」**

**⭐ 而随后的规模拆解是这样的：**

| 链 | 金额 | 占 63.6 亿比例 | 备注 |
|---|---|---|---|
| **Ethereum** | **约 37.9 亿** | **约 60%** | 200,630 ETH + 185 种代币；含 18.75 亿 USDT、8.23 亿 USDC、8,850 万 RLUSD |
| **Bitcoin** | **约 14.7 亿** | 约 23% | **18,270 BTC** |
| **Tron** | 约 6.28 亿 | 约 10% | 6.127 亿 USDT + 4,640 万 TRX |
| **XRP Ledger** | 约 2.96 亿 | 约 5% | 2.3346 亿 XRP |
| **Solana** | 约 9,600 万 | 约 1.5% | 970,500 SOL |
| Arbitrum / Optimism / Base | 约 3,900 万 | — | 含 Arbitrum 上 7,460 万 ARB |
| Avalanche | 约 2,800 万 | — | — |
| Polygon | 约 1,000 万 | — | — |

**⭐ 而时间线是压缩的：**

| UTC 时刻 | 事件 |
|---|---|
| **10-28 上午** | 攻击者运营钱包从 Tornado Cash 收到 3 笔小额提现 —— **准备开始** |
| **10-29 清晨** | 部署第一版攻击代码，在**两个**钱包上测试 |
| **10-29 当天晚些** | 在**第三个**钱包上**彩排最终版**，然后把测试资金转回自己 |
| **20:05** | ⭐ **XRP Ledger 第一个动手** —— 5 个 Binance 钱包转出 2.3346 亿 XRP |
| **20:09 前** | 每个钱包只留最低余额 |
| **20:10 后** | Solana、Optimism 跟上 |
| **20:20** | ⭐ **Bitcoin 热钱包转出 18,270 BTC**，在同一区块内拆成 1,000 BTC 和 100 BTC 的整数块（**peel chain**，剥洋葱式拆分） |
| **20:20** | ⭐ **Ethereum 上提交一笔含 50 个授权的交易** |
| **20:23:24** | ⭐ **委托生效后 3 分 24 秒，攻击者指示热钱包把全部余额转走** —— 一笔交易带走 167,464 ETH + 63 种代币（含 16.15 亿 USDT） |
| **20:41 / 20:59 / 21:04 / 21:44 / 22:39 / 23:56** | 新资金到达热钱包，**被反复扫走 6 次** |
| **23:05** | 第二波：Avalanche 与 Polygon |
| **23:35** | Binance 公告：已冻结 25.4 亿美元 |

**⭐ 而准备期有多长？TRM 明确说：**

> **「Preparation began at least 36 hours before the theft.」**

**—— 至少 36 小时。** **这和「20 分钟完成」放在一起看，才是这个事件真正的形状：**

| | 时间 |
|---|---|
| **准备** | **≥ 36 小时** |
| **执行** | **约 20 分钟** |

**⭐ 我认为这个 36 小时 : 20 分钟的比例，比 63.6 亿这个数字更能说明问题 —— 后面第五节会展开讲。**

## 二、⭐⭐ 核心机理：EIP-7702 与那 50 个预签名

**⭐ 这是全文最值得技术读者细读的部分，而且 TRM 的原文讲得非常清楚。**

### 2.1 EIP-7702 是什么

> **「EIP-7702, introduced in Ethereum's Pectra upgrade in May 2025, allows an ordinary wallet to hand control of its behavior to a smart contract by signing an authorization. From then on, every call to the wallet runs that contract's code, and the arrangement stays in place until the wallet signs a new one.」**

**用大白话说：**

**一个普通以太坊钱包（EOA），签一份授权，就能「把自己变成一个合约的钱包」** —— 从此以后，任何对它的调用都会执行某个智能合约的代码。**而这个安排会一直生效，直到钱包签一份新的授权把它撤销。**

### 2.2 ⭐ 为什么 50 个授权就够

**TRM 的这段解释是整个事件的技术核心：**

> **「Each was signed by the Binance hot wallet, and each pointed it to a sweeper contract that accepts instructions only from the operator. Every wallet keeps a running count of its transactions, called a nonce, and an authorization works only at the count the wallet has reached at the moment it executes. The Binance hot wallet processes a steady flow of withdrawals, so its count keeps moving forward. By preparing signatures for 50 consecutive counts, the attacker guaranteed that one would still be valid when the transaction executed. One matched, which was all the attacker needed. The signatures were produced in advance as a batch.」**

**⭐ 我把这段拆成三个可以迁移到任何系统的知识点：**

**① 授权是「绑定 nonce」的**

**每个钱包维护一个交易计数（nonce）。授权只在该计数上有效。** **而热钱包的提现流水是持续推进的 —— 所以攻击者不能指定「第 100 号授权」，只能「准备一批，赌一个命中」。**

**② 连续 50 个 nonce 覆盖了一个时间窗口**

**Binance 热钱包每笔提现都推进 nonce。** **准备 50 个连续计数的签名，就等于覆盖了「50 笔提现」的时间窗。** **只要有一个在交易上链的时刻恰好对得上，就够了。**

**③ ⭐ 批量预签 = 一次拿下一整段窗口的钥匙**

**「The signatures were produced in advance as a batch.」** —— 这是攻击链里最关键的一句话。**攻击者不是「偷了一次签名」，而是「一次性预签了一批签名」。**

**⭐ 我认为这一点值得反复强调，因为它揭示了一个系统性的设计风险：**

> **批量签名能力，本质上等于「未来一段时间的任意签名能力」。**

**只要 nonce 空间是连续且可预测的，批量预签就把「一次授权」变成了「一段区间的授权」。**

### 2.3 委托之后：可以反复扫

**TRM 接下来的描述解释了为什么损失这么大：**

> **「The delegation remained in place. As new funds reached the Binance hot wallet, the operator swept them again at 20:41, 20:59, 21:04, 21:44, 22:39 and 23:56 UTC. The wallet also served as the executor of a separate Binance smart account, which gave the attacker the ability to pull 823 million USDC from it.」**

**⭐ 而这也解释了一件事：为什么「撤销授权」是防守方的第一优先级 —— 撤销之后，新到的钱才不会被继续扫走。** Binance 官方声明里确实提到了「revoked authorizations for the affected address」。

### 2.4 ⭐⭐ 而最关键的一步：不是钓鱼，是签名基础设施

**⭐ 这一节是 TRM 报告里我认为最有价值的一段推理，因为它是「排除法」得出的结论。**

**TRM 先说了一个最初的假设：**

> **「Early indicators on the Ethereum activity suggested the attacker had phished the authorizations. That explanation covers Ethereum and leaves the other chains unexplained.」**

**—— 钓鱼能解释以太坊那条链，但解释不了另外九条。**

**然后 TRM 给出了关键观察：**

> **「In the same window, five Binance wallets on the XRP Ledger, Binance wallets on Arbitrum, Avalanche, Optimism and Base, a Binance Bitcoin hot wallet, a Binance hot wallet on Tron and a Binance wallet on Solana sent funds to the attacker through standard signed transfers. Another Binance hot wallet on Ethereum sent 28,006 ETH, 55.7 million USDT and 25.9 million RLUSD the same way, without any delegation.」**

**⭐ 请注意这句：**

**「through standard signed transfers」—— 普通签名转账，连 EIP-7702 委托都没用。**

**而且这些钱包：**

| 维度 | 情况 |
|---|---|
| **链** | 完全不同 |
| **密钥类型** | 完全不同 |
| **签名方案** | 完全不同 |

**TRM 的结论：**

> **「All of them produced valid signatures for the attacker within about half an hour. In TRM’s assessment, the most likely explanation is that the attacker gained the ability to make Binance’s hot wallet signing system sign transactions of its choosing across chains.」**

**⭐ 而那份 50 个预签的批次，就是这个判断的关键旁证：**

> **「The batch of 50 pre-signed authorizations suggests the access may have been limited in time, or that signatures had to be requested through a system. Binance has yet to publish a root cause.」**

**⭐ 我把 TRM 这段推理的逻辑链完整列出来，因为它示范了「怎么从链上行为反推入侵路径」：**

```
现象：10 条链、密钥类型各异、都在半小时内产出了有效签名
  ↓ 排除：钓鱼（只解释 1 条链）
 排除：私钥泄露（不同密钥类型 + 官方否认）
 排除：某条链的智能合约漏洞（普通签名转账不需要）
  ↓ 剩余解释：跨链签名基础设施被攻破
旁证：50 个预签的批次 —— 像是「通过某个系统批量请求签名」，而不是「偷了密钥」
```

**—— 而 Binance 自己的声明，与这个推断是吻合的：**

> **「the attackers appear to have gained access to the software that requests withdrawals, potentially allowing…」**（New Scientist 引述 Binance）
>
> **「The access let attackers submit unauthorized withdrawal transactions after they accessed a service container, and it hasn't yet found evidence of a leaked wallet private key.」**（BleepingComputer）
>
> **「To be clear: the attacker did not simply use one engineer's permissions, and this was not a single 'one-click' action. It involved a more complex attack process. Our investigation has not attributed responsibility to any individual.」**（Richard Teng）

**⭐ 而 BBC 的转述补上了最关键的一句：**

> **「while initial checks suggested an engineer's laptop had been compromised, allowing an attacker to make unauthorised withdrawals, 'our subsequent investigation has uncovered additional points of breach'」**

**⭐ 我的判断是：这条时间线（工程师笔记本 → 后续发现更多突破点）说明攻击是分阶段的，而「签名基础设施」这一层 —— 也就是能把请求「批量转成签名」的那个系统 —— 才是真正被攻破的东西。**

## 三、⭐ 冻结与洗钱：一场 6 小时的赛跑

**⭐ 我认为这一节是整个事件里最有戏剧性、也最有防守启示的部分。**

### 3.1 冻结名单

**TRM 统计的链上冻结总额约 27 亿美元：**

| 机构 | 冻结内容 | 首次冻结时刻 |
|---|---|---|
| **Tether** | 约 17.7 亿 USDT | **21:01**（主扫之后仅 37 分钟） |
| **Circle** | 约 8.25 亿 USDC | **21:04**（与执法部门协调） |
| **Ripple** | 4,050 万 RLUSD | **22:01** |
| **World Liberty Financial** | 2,780 万 USD1 | **22:10** |
| **Arbitrum 安全委员会** | 8,426 ETH + 7,460 万 ARB | **00:08** |

**⭐ 而 Tether 的冻结动作有个细节很有意思：**

> **「Tether froze 971.1 million USDT in the main receiving wallet at 21:01 UTC, 37 minutes after the main sweep. Later sweeps landed in the frozen wallet, which now holds 1.175 billion USDT.」**

**—— 主钱包被冻之后，后续的扫款直接落进了那个已被冻结的钱包。** **累计 11.75 亿 USDT 卡在那里出不去。**

**⭐ 而 Arbitrum 安全委员会的动作是另一条路径 —— 不是冻结，是「强制转账」：**

> **「At 00:08 UTC, it used those powers to force two transfers out of the attacker's wallet on Arbitrum, moving 8,426 ETH and 74.6 million ARB, about USD 30 million, out of the attacker's reach.」**

**⭐ 注意这个措辞：「force two transfers out of the attacker’s wallet」—— 是把攻击者钱包里的钱「推出去」，而不是「锁住」。** **这是链上治理的一种非常规手段。**

### 3.2 ⭐⭐ 而攻击者的应对：10% 折价甩卖

**⭐ 这是我认为整篇报告最值得记的一个数字：**

> **「About 325 million USDT was sold to professional fillers and market makers through UniswapX and other intent-based contracts in exchange for about 122,300 ETH. That implies a price near USD 2,650 per ETH when ETH traded around USD 2,300 to 2,350, a discount of more than 10%.」**

**⭐ 我把这个算式写出来：**

```
攻击者卖出：约 3.25 亿 USDT
换回：约 12.23 万 ETH
隐含单价：约 2,650 USDT/ETH
当时市价：约 2,300 ~ 2,350 USDT/ETH
折价：> 10%
```

**⭐ 也就是说：攻击者为了在冻结生效前把「可冻结资产」换成「不可冻结资产」，**心甘情愿付了超过 10% 的溢价**（对他来说是折价卖出）。**

**为什么值得记？因为这是「时间」被明确定价的时刻。**

**⭐ 而 TRM 说这是常态化的洗钱方式：**

> **「the attacker converted freezable stablecoins into assets beyond any issuer's reach, at steep cost.」**
>
> **「the attacker raced the freezes by selling USDT to market makers and borrowing ETH against USDT on Aave.」**

**⭐ 而第二条路径更有意思 —— 借贷而不是卖出：**

> **「A second attacker wallet supplied 60 million USDT to the lending protocol Aave and borrowed about 19,760 ETH against it, after which Aave froze the affected markets.」**

**—— 抵押 USDT 借出 ETH，**不需要卖掉 USDT**（避免了折价），拿到的 ETH 也不在 USDT 发行方能冻结的范围内。** 随后 Aave 冻结了受影响的市场。**

**⭐ 我认为这两条路径合起来说明了一件事：**

> **发行方冻结只能锁住「发行方能冻的资产」。**
> **一旦资产换成 ETH、BTC 这类「没有任何发行方能冻」的形态，冻结机制就完全失效。**

**⭐ 而这就是为什么 TRM 在结尾写：**

> **「It now holds more than 420,000 ETH and 18,270 BTC, about USD 2.4 billion in assets beyond any issuer's reach.」**

### 3.3 ⚠️ 但冻结并没能全部追回

**⭐ 而 Elliptic 的独立核算给出了一个更保守、也更值得警惕的数字：**

> **「Elliptic has verified $2.84 billion of frozen funds, 44% of the theft, almost all of it USDT and USDC. The attacker is swapping the rest into ETH and other assets that cannot be frozen.」**

**—— 44%。** **超过一半的资金，攻击者已经换成了追不回的形态。**

**⭐ 而 Binance 官方说法是「约 30 亿已冻结」，并承诺：**

> **「Binance will cover all losses from the SAFU fund and the company's funds. User funds are safe. We will also publish an updated Proof of Reserves once the remediation is complete.」**
>
> **「Binance said it worked with blockchain partners to freeze roughly $3 billion in affected assets. It said Friday that it was beginning to recover assets for users.」**（AP）

**—— 用户资金由 SAFU 基金和公司资金兜底。** **这句话本身就是一个很大的信号：** **一个「私钥没泄露」的签名基础设施事故，最终的兜底成本是 63.6 亿里的未冻结部分。**

## 四、⭐ 归因：朝鲜 TraderTraitor

**⭐ TRM 的归因是「high confidence」，而且给了具体的比对依据：**

> **「TRM attributes this attack to TraderTraitor, North Korea's elite hacking unit, based on robust on and off-chain intelligence. We make this judgment with high confidence.」**

**⭐ 而它列出的「与此前朝鲜系攻击的共同特征」很有说服力：**

> **「Several features of this attack match earlier North Korea-linked heists, including the Bybit hack and the KelpDAO hack in April 2026: small Tornado Cash withdrawals funding an operator wallet, staging that began well before the theft, and signatures obtained in advance then executed in one burst.」**

**⭐ 我把这三条特征单独列出来，因为它们都是「准备期」的外在表现：**

| 特征 | 本案表现 |
|---|---|
| **小额 Tornado Cash 提现资助运营钱包** | 10-28 上午，3 笔小额提现 |
| **远早于盗窃的铺垫（staging）** | ≥ 36 小时 |
| **提前取得签名，然后一次性爆发执行** | 50 个预签授权，一次提交 |

**⭐ 而 Chainalysis 独立给出了同样的结论：**

> **「Chainalysis investigators assess the $6.4 billion hack of Binance … to be the work of North Korean cybercrime group TraderTraitor. This group has repeatedly targeted the cryptocurrency industry, exchanges, DeFi protocols, and investors, to raise funds for the regime.」**
>
> **「Chainalysis confirmed TRM Labs' findings, stating with 'a high degree of confidence' that TraderTraitor is responsible.」**

**⭐ 而 Elliptic 走的又是另一条路径 —— 不是行为特征，而是**资金同源**：**

> **「Elliptic has confirmed that some of the stolen funds have reached the same address as proceeds of the suspected DPRK exploit of Bitge…」**

**⭐ 我认为「三家机构用三条独立路径得出同一结论」这件事本身值得强调：**

**TRM 靠行为特征、Chainalysis 靠链上行为、Elliptic 靠资金同源。** **三条路径互相独立，结论一致 —— 这个归因的可信度远高于单一来源。**

## 五、⭐⭐ 我的判断：这个事件的形状，以及它能教给非加密行业什么

### 5.1 ⭐ 真正的形状是「36 小时 vs 20 分钟」

**⭐ 我认为这条新闻最该被记住的数字组合，不是 63.6 亿，而是这个：**

```
准备：≥ 36 小时（跨 3 个钱包、2 轮测试、一次彩排）
执行：约 20 分钟（10 条链、6.36 亿美元）
```

**⭐ 为什么这个比例重要？因为它把「防守窗口」的位置完全改变了。**

| 防守动作 | 在这个事件里能不能救回来 |
|---|---|
| **在 20 分钟内发现并冻结** | ⭐ **不可能** —— 20 分钟跨 10 条链 |
| **在 36 小时内发现签名基础设施被滥用** | ⭐ **有机会** —— 这是唯一的窗口 |
| **撤销 EIP-7702 授权** | ⭐ **有机会** —— 能止住后续 6 次扫款 |
| **签名策略拒绝非预期授权** | ⭐ **有机会** —— 批量 50 个跨 nonce 的授权本该被拒 |

**⭐ 而 Binance 的时间线告诉我们它卡在哪里了：**

**发现是在 20:05 之后（第一笔 XRP 转出之后）。** **而 TRM 说攻击者在 36 小时前就开始了准备。**

**—— 也就是说：防守方是在「执行阶段」才发现的，而攻击方已经用 36 小时把「准备阶段」做完了。**

### 5.2 ⭐⭐ 而这条教训，映射到任何「用密钥签名」的系统

**⭐ 我认为这才是本文对非加密行业读者最有价值的部分 —— 因为 EIP-7702 的机制，本质上是一个**通用的密钥管理问题**：**

> **「一个系统能不能在不持有私钥的前提下，替用户签出一批有有效期的授权？」**

**⭐ 而 TRM 那 50 个预签的失败模式，在任何签批系统里都能找到对应物：**

| 加密世界的形态 | 非加密世界的对应物 |
|---|---|
| **连续 nonce 的批量预签** | 连续序号的批量审批 / 连续工单的批量签批 |
| **授权绑定「计数」** | 令牌绑定序列号 / 版本号 / 计数器 |
| **50 个签名的批次** | 一次批量导出 50 张凭证 |
| **委托在撤销前一直有效** | 一次授权长期有效，撤销要单独走流程 |
| **签名系统跨链不隔离** | 同一套签批服务管所有业务线 |

**⭐ 我想强调其中两条：**

**① 「批量预签」= 一次拿下一整段窗口的钥匙**

**任何「批量导出凭证」的功能，都应该被问一个问题：这批凭证的有效期跨度是多久？** **如果是连续编号的 50 个，那它覆盖的是「未来 50 次操作」—— 而不是「现在这一次」。**

**② 「撤销」必须比「签发」更容易**

**本案里，委托生效后攻击者又扫了 6 次。** **如果撤销委托是秒级的、批量级的，那 6 次里有 0 次会成功。** **而如果撤销要走「人工审批 + 逐个作废」的流程 —— 那这 6 次全都躲过去了。**

### 5.3 ⭐ 而 TRM 给防守方的建议，其实就是这四条

**TRM 在「What exchanges and compliance teams should do now」里给的建议，我认为是全文最可以直接抄走的部分：**

> **「Treasury teams should monitor Ethereum-compatible wallets for EIP-7702 delegations, which appear as code at an address that should have none. Any such delegation on a treasury wallet should trigger an immediate alert. Teams should keep a tested, pre-approved method for signing a revocation.」**
>
> **「Signing policies should reject EIP-7702 authorizations unless they are expected. A request for many authorizations across a range of transaction counts should be treated as an indicator of compromise. Signing infrastructure and approval paths should be separated by chain and wallet tier. In this incident, a single actor obtained valid signatures for wallets on ten chains within hours.」**

**⭐ 我把这四条翻译成通用语言：**

| TRM 的建议 | 通用化 |
|---|---|
| 监控「本不该有代码的地址出现了代码」 | ⭐ **监控「本不该有状态的对象出现了状态」** —— 这是最便宜的一类检测 |
| 准备好预批准的撤销流程 | ⭐ **撤销必须比签发快** |
| 拒绝非预期的授权 | ⭐ **白名单而不是黑名单** —— 默认拒绝对���非预期操作 |
| 按链与钱包层级隔离签名基础设施 | ⭐ **⭐ 签名能力按域隔离** —— 10 条链共用一套签名系统是根本问题 |

**⭐ 而我认为最后一条是最关键的：**

> **「In this incident, a single actor obtained valid signatures for wallets on ten chains within hours.」**

**—— 一个攻击者，几小时内，在 10 条链上拿到了有效签名。**

**这不是 10 次入侵，这是一次入侵打穿了 10 个隔离。**

## 六、⭐ 数字速查

| 项目 | 数值 |
|---|---|
| **被盗总额** | **约 63.6 亿美元**（按被盗时价格计）；当前价约 62.3 亿 |
| **链上时间** | 2026-10-29 20:05 UTC 起，约 20 分钟内完成大部分 |
| **准备期** | **至少 36 小时** |
| **涉及链** | **10 条**：Ethereum、Bitcoin、Tron、XRP Ledger、Solana、Arbitrum、Avalanche、Optimism、Base、Polygon |
| **Ethereum 占比** | 约 37.9 亿（约 60%），200,630 ETH + 185 种代币 |
| **Bitcoin** | 18,270 BTC（约 14.7 亿） |
| **EIP-7702 授权数** | **50 个连续 nonce**，命中 1 个即够 |
| **首笔 Ethereum 扫款** | 委托生效后 **3 分 24 秒** |
| **后续扫款** | 20:41 / 20:59 / 21:04 / 21:44 / 22:39 / 23:56（**共 6 次**） |
| **已冻结** | 约 27 亿（TRM）/ **28.4 亿（Elliptic，占 44%）** / Binance 称约 30 亿 |
| **冻结方** | Tether（17.7 亿 USDT）、Circle（8.25 亿 USDC）、Ripple（4,050 万 RLUSD）、World Liberty Financial（2,780 万 USD1）、Arbitrum 安全委员会（8,426 ETH + 7,460 万 ARB） |
| **攻击者仍持有** | **> 42 万 ETH + 18,270 BTC ≈ 24 亿美元**（超出任何发行方冻结能力） |
| **洗手折价** | 3.25 亿 USDT 换约 12.23 万 ETH，**隐含价约 2,650 vs 市价 2,300~2,350（折价 >10%）** |
| **借贷路径** | 6,000 万 USDT 抵押 Aave 借出约 19,760 ETH |
| **归因** | **TraderTraitor（朝鲜）** —— TRM / Chainalysis / Elliptic 三方独立一致 |
| **对比** | Bybit 案（2025-02）15 亿美元的 **4 倍以上** |
| **Binance 官方** | 私钥**未**泄露；疑为 DevOps 工程师笔记本 + 服务容器被攻破；「发现了额外的突破点」；SAFU 基金兜底全部损失 |

## 七、证据边界

**⭐ 我认为这篇报道有几处需要明确区分「已确认」与「推断」的地方：**

| 结论 | 状态 |
|---|---|
| 63.6 亿美元、10 条链、时间线 | ⭐ **TRM 链上数据，已确认** |
| 各发行方冻结金额与时刻 | ⭐ **链上已确认** |
| 归因 TraderTraitor | ⭐ **三方独立一致，高置信度**（但仍是情报判断，非法律定论） |
| EIP-7702 是以太坊路径的接管方式 | ⭐ **链上已确认** |
| **「签名基础设施被攻破」** | ⚠️ **TRM 的评估** —— 原文写「In TRM’s assessment」 |
| **Binance 的根因** | ⚠️ **官方尚未公布** —— 原文：「Binance has yet to publish a root cause」 |
| **具体入侵路径** | ⚠️ **未知** —— 只知「DevOps 工程师笔记本」+「服务容器」+「额外突破点」 |

**⭐ 而 TRM 自己在文末也留了一句：**

> **「The story is still developing, and the figures here reflect what TRM saw onchain as of October 30 at 00:30 UTC.」**

**—— 所有数字截至 10-30 00:30 UTC 的链上状态。** **洗钱还在进行，最终损失可能还会变。**

## Sources

- ⭐ 一手：[TRM Labs — North Korea Steals USD 6.36 Billion From Binance in the Largest Hack in History](https://www.trmlabs.com/resources/blog/north-korea-steals-usd-6-36-billion-from-binance-in-the-largest-hack-in-history)（2026-10-30）
- ⭐ 一手（归因交叉验证）：[Chainalysis — The $6.4 Billion Binance Exploit: Tracing the North Korea Link](https://www.chainalysis.com/blog/binance-exploit-latest-findings-and-response/)（2026-10-30）
- ⭐ 一手（冻结核算 + 资金同源）：[Elliptic — The largest theft in history: DPRK behind the $6.4 billion Binance hack](https://www.elliptic.co/insights/binance-largest-hack-in-history/)（2026-10-30）
- 一手（Binance 官方声明）：[BleepingComputer — Binance links $6.3 billion crypto theft to compromised DevOps laptop](https://www.bleepingcomputer.com/news/security/binance-links-63-billion-crypto-theft-to-compromised-devops-laptop/)（含 Richard Teng / Binance 官方 X 引述）
- 报道：[AP — Blockchain firms link North Korea to $6.3B hack on Binance](https://apnews.com/article/binance-cryptocurrency-security-hack-north-korea-550e9b876550f71f07098494fe735beb)（2026-10-30）
- 报道：[BBC — Crypto giant Binance hit by hack suspected to be largest in history](https://www.bbc.com/news/articles/cwg7xp8kx4v5o)（2026-10-30）
- 报道：[CNBC — Binance’s $6.3 billion hack: What we know and what comes next](https://www.cnbc.com/2026/10/30/billions-in-crypto-frozen-in-binance-hack-heres-what-happens-next-.html)
- 报道：[The Guardian — North Korean group blamed for $6.3bn Binance hack in biggest ever crypto heist](https://www.theguardian.com/business/2026/oct/29/binance-crypto-exchange-hack)
- 报道：[CoinDesk — Binance loses over $6 billion in the largest crypto hack to date](https://www.coindesk.com/business/2026/10/29/potential-multi-billion-binance-hack-hitting-crypto-markets)
- 报道：[New Scientist — Binance: How did the biggest crypto heist in history just happen?](https://www.newscientist.com/article/2596706-how-did-the-biggest-crypto-heist-in-history-just-happen/)
- 规范：[EIP-7702 — Set Code for EOAs](https://eips.ethereum.org/EIPS/eip-7702)（Ethereum Pectra 升级，2025-05）

---

（说明：所有引号内内容与数字均来自上述一手材料与权威报道；**第二节的机制拆解为笔者依据 TRM 原文所做的通俗化整理**；**第五节「对非加密行业的映射」与全部判断为笔者观点**。**本文不含任何可操作的盗取手法，也不提供被盗资产追踪地址** —— 事件分析的目的是让防守方理解威胁形态。）
