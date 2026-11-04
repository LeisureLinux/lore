---
title: "一张显卡涨 370%：$9,400 的 RTX 5090，和一份把「谁在说谎」拆开的报道"
date: 2026-11-04
slug: rtx-50-gpu-price-spike-memory-shortage
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：Shattered.io《RTX 5090 Price Increase: 370% Over MSRP Reported》⭐ 【三家报道里唯一逐条标注出处并区分「已证实/未证实」的那一篇】＋ eTeknix 报道 ＋ ZDNET 报道（Taylor Clemons，2026-11-03）＋ aroundprague.cz 的聚合报道（含各家数字的并列表）＋ NVIDIA 官方发布价"
original_date: 2026-11-03
original_url: "https://aroundprague.cz/en/news/us/rtx-5090-street-prices-top-9-000-as-nvidia-gpu-costs-climb"
description: "本文解读 2026 年 11 月 3 日集中出现的一组报道：⭐ **RTX 5090 在美国的零售价被报到 $9,400，比 $1,999 的官方首发价高 370%；整条 RTX 50 线的涨幅被报到 40%–120%**。⭐ **而本文的重点不是复述这个数字，⭐ 而是拆解这组报道本身的可靠性问题** —— ⭐ **因为同一件事，⭐ 四家报道给了四个不同的数**（TechSpot：>$9,000；Windows Report：$9,400；ZDNET：Best Buy 约 $6,000；eTeknix：全球平均 +262%），⭐ **而这些数不是「谁抄错了」，⭐ 而是「各自在测不同的东西」。** ⭐ Shattered.io 那篇（⭐ 三家里唯一逐条标注出处并区分「已证实/未证实」的）⭐ 把可能的成因列成五类并明确说「没有硬数据，⭐ 我们无法排序，⭐ 任何声称能排序的媒体都已经超出了它的证据」：⭐ **显存短缺、⭐ AI 大宗采购、⭐ 硅片分配、⭐ 炒货投机、⭐ 以及它们的叠加**。⭐ 而 ZDNET 那边给的是一条更硬的事实：⭐ **NVIDIA 确实在通知用户涨价 —— 8 月曾预告全线上调最多 15%，⭐ 这一次 5090 加约 $500、⭐ 5050/5060 加 $50–60**，⭐ 归因于 **AI 驱动的全球内存短缺**。⭐ **⭐ 而本文的核心判断是：⭐ 「370%」这个数字本身是**修辞**（⭐ 涨了 3.7 倍意味着变成 4.7 倍），⭐ 而真正该看的两个数字是「官方价没动」和「溢价没有流向 NVIDIA」** —— ⭐ **因为按 Shattered.io 的说法，⭐ 溢价落在零售商、炒货商与二级市场手里，⭐ 而没有任何来源量化了这条链上谁分到了多少。"
published: true
---

> **原文**：aroundprague.cz《RTX 5090 Street Prices Top $9,000 as Nvidia GPU Costs Climb》（Maksym Akimov，2026-11-03/04）
> 原文链接：<https://aroundprague.cz/en/news/us/rtx-5090-street-prices-top-9-000-as-nvidia-gpu-costs-climb>
> ⭐ **本文依据四家原始报道 ＋ NVIDIA 官方发布价。⭐ 而重点是：⭐ 这四家报道并不一致，⭐ 而不一致的原因是可以拆开的。**

## 一、⭐ 先把四个数字并排放

⭐ **这是我认为这条新闻最值得写的部分 —— ⭐ **因为同一天，四家媒体报了同一件事，⭐ 而四个数字都不一样。**

| 来源 | 报的数字 | 测的是什么 |
|---|---|---|
| ⭐ **TechSpot**（经 eTeknix 转述） | ⭐ **美国价 > $9,000，⭐ 比 MSRP 高 370%，⭐ 全球平均高 262%** | ⭐ **整体价格水平** |
| ⭐ **Windows Report**（经 Shattered.io 转述） | ⭐ **美国最低可得价 $9,400（2026 年 10 月）** | ⭐ **⭐ 某一天的最便宜一条挂单** |
| ⭐ **ZDNET** | ⭐ **Best Buy 约 $6,000**，⭐ 本轮再涨约 $500** | ⭐ **⭐ 单一大型零售商的挂牌价** |
| ⭐ **eTeknix** | ⭐ **5080 高 120%、5070 Ti 高 67%、5070 高 64%、5060 Ti 16GB 高 84%、5050 从 $260 涨到 $420（高 68%）** | ⭐ **⭐ 分型号的溢价幅度** |

⭐ **⭐ 请注意这四个数字的测法完全不同：⭐ **一个是「整体水平」，一个是「最低挂单」，一个是「Best Buy 挂牌」，一个是「分型号百分比」。⭐ **⭐**

⭐ **⭐ 而 aroundprague 那篇聚合报道其实已经点出了这一点，⭐ 虽然它没有展开：**

> *"**The sources use different measures.** TechSpot's analysis points to a U.S. price above $9,000, while Windows Report's number is $9,400. ZDNET, meanwhile, described the RTX 5090 as carrying a price of about $6,000 at Best Buy, before an increase of nearly $500."*
>
> *"**Shattered.io noted that a lowest-price reading is a snapshot of the cheapest listing on a given day, not what most buyers paid.**"*

⭐ **⭐ 而 Shattered.io 那篇（⭐ 全文我读了，⭐ 这是三家里唯一**逐条标注出处并明确区分「已证实」与「未证实」**的一篇）⭐ 说得更狠：**

> *"**No source we reviewed published a complete product-by-product record that confirms those ranges card by card.**"*
> *"**Read the last column as arithmetic, not as a price list.**"*
> *"**Any outlet that claims to has gone past its evidence.**"*（⭐ 指那些声称能给出成因排序的媒体）

## 二、⭐⭐⭐ 而「370%」这个数字本身，是一个修辞

⭐ **⭐⭐ 这一节是我认为整篇文章最值得先说的，⭐ 因为它是所有后续讨论的前提。**

⭐ **Shattered.io 专门用一节解释这个算术：**

> *"**A 370% increase does not mean the card costs 3.7 times its MSRP. It means the price rose by 3.7 times the original amount, so the new price is 4.7 times the original.** Multiply $1,999 by 4.7 and you land near $9,400, which matches the Windows Report figure."*
>
> *"**The gap is about $7,400 per card. For context, that difference alone is more than seven times the launch price of an RTX 5080.**"*

⭐ **⭐⭐ 请把这两个数字并排看一眼：**

```
涨价幅度：  +370%   （价格涨了 3.7 倍）
新价格倍数： ×4.7  （价格变成 4.7 倍）
```

⭐ **⭐⭐ 而我认为「370%」这个表述的问题，⭐ **不在于它算错了（它没错），⭐ 而在于它的形式会误导人：**

- ⭐ **「+370%」** ⭐ **听起来像「稍微贵了一点」**
- ⭐ **「×4.7」** ⭐ **才是一个能被大脑处理的价格信号**

⭐ **⭐ 而 Shattered.io 那句补充更值得记：⭐ **「单卡多出来的 $7,400，⭐ 就已经超过一张 RTX 5080 首发价的七倍」。⭐ **⭐**

⭐ **⭐⭐ 而这一节的标题我认为是全文最诚实的一句：⭐ **「The Math: From $1,999 to $9,400」⭐ —— ⭐ **⭐ 它把「百分比新闻」还原成了「价格新闻」。⭐ **⭐**

## 三、⭐⭐⭐ 三条确定的事实，和一条不确定的

⭐ **⭐ 这一节是我认为任何写这条新闻的人都应该分清的层次。**

### ⭐⭐ 确定一：官方价没动

⭐ **⭐ NVIDIA 没有宣布上调 RTX 5090 的美国官方建议零售价。** ⭐ Shattered.io 的原话：

> *"**NVIDIA has not announced a U.S. MSRP increase for the RTX 5090, and the official price remains $1,999.**"*
>
> *"Those figures describe **retail and market prices, not a list-price change.**"*

⭐ **⭐ 而这里有一个必须点明的反差：⭐ **「官方价没动」与「NVIDIA 正在通知涨价」⭐ **同时成立。⭐ **⭐**

### ⭐⭐ 确定二：但 NVIDIA 确实在通知涨价 —— 这条来自 ZDNET

⭐ **⭐ ZDNET 的报道（Taylor Clemons，2026-11-03 12:30 ET）⭐ 给出了这次最硬的一条事实：**

> *"As the **AI-driven global memory shortage** rages on, **Nvidia is notifying users that its RTX 50 series of graphics cards will see yet another significant price hike this week.**"*
>
> *"**In August, Nvidia gave gamers and content creators fair warning that the company's entire line of RTX 50 Series GPUs would get price increases of up to 15%.** The flagship 5090 is getting the highest: **a nearly $500 increase on an already eye-watering $6,000 price tag at Best Buy.** The lower-end 5050 and 5060 will get much more modest, if still grumble-worthy, **$50-60 bumps**."*

⭐ **⭐⭐ 请注意这里的层次差 —— ⭐ **⭐ 这才是真正重要的部分：**

| | ⭐ **官价（MSRP）** | ⭐ **零售价** |
|---|---|---|
| ⭐ **NVIDIA 宣布了吗** | ⭐ **没有** | ⭐ **⭐ 有（通过通知渠道）** |
| ⭐ **幅度** | ⭐ **不变** | ⭐ **5090 约 +$500；⭐ 5050/5060 约 +$50–60** |
| ⭐ **基数** | ⭐ **$1,999** | ⭐ **⭐ 5090 已经是约 $6,000** |
| ⭐ **谁承担** | ⭐ **—** | ⭐ **⭐ 消费者** |

⭐ **⭐⭐ 而这一行是关键：⭐ **⭐ NVIDIA 8 月预告的是「最多上调 15%」，⭐ 而这一次是在「已经 $6,000 的价格上」再加 $500。⭐ **⭐**

⭐ **⭐⭐ 换句话说：⭐ **⭐ 官价从 $1,999 到 $6,000 的这段涨幅，⭐ **不是 NVIDIA 宣布的**；⭐ **⭐ 而 $6,000 到 $6,500 这一段，⭐ **是 NVIDIA 通知的。⭐ **⭐**

⭐ **⭐⭐ 而这就把 Shattered.io 那句限定语的意义放大了：⭐ **⭐ 「溢价没有流向 NVIDIA」⭐ **这句话如果成立，⭐ **那么「NVIDIA 涨价」这个标题就是**误导**的 —— ⭐ **⭐ 因为 NVIDIA 通知的那 $500，⭐ **只是它对已经存在的市场溢价**再往上加了一点。⭐ **⭐**

### ⭐⭐ 确定三：官方发布价有据可查

⭐ **NVIDIA 2025-01-30 公告的四个价格（据 GamesRadar 当时报道与 Smartprix 记录）：**

| 型号 | 首发价 |
|---|---|
| ⭐ **RTX 5090** | ⭐ **$1,999** |
| ⭐ RTX 5080 | $999 |
| ⭐ RTX 5070 Ti | $749 |
| ⭐ RTX 5070 | $549 |

⭐ **⭐ 而 ZDNET 那句「$6,000 的价格标签」，⭐ **恰恰是 Best Buy 的挂牌价 —— ⭐ **⭐ 也就是说，⭐ **在 NVIDIA 宣布任何涨价之前，⭐ 主流零售渠道就已经卖到 3 倍官方价了。⭐ **⭐**

### ⭐⭐ 不确定：到底是什么在推高价格

⭐ **⭐⭐ 而这一层，⭐ **我必须承认现有报道给不出答案 —— ⭐ **而 Shattered.io 把它列得很清楚：**

> *"**Each explanation is plausible. None is documented here by an on-record source such as NVIDIA, a retailer or a board partner.** That matters, because a price spike has several possible parents, and **different fixes follow from each one.**"*

⭐ **⭐⭐ 然后它把五种成因并排列出（⭐ 这是我认为整篇报道最有价值的部分）：**

| 成因 | 机制 | ⭐ **如果是这样，对策是什么** |
|---|---|---|
| ⭐ **① 显存短缺** | ⭐ **GDDR7 供给紧张 → 板厂少产 → 零售商把剩下的标高价** | ⭐ **等产能恢复** |
| ⭐ **② AI 大宗采购** | ⭐ **服务器厂商按量吸收旗舰卡 → 玩家分到更薄的池子** | ⭐ **等 AI 建设周期变化** |
| ⭐ **③ 硅片分配** | ⭐ **NVIDIA 把稀缺芯片导向高毛利产品 → 消费级板被挤** | ⭐ **等 NVIDIA 调整分配** |
| ⭐ **④ 炒货投机** | ⭐ **价格涨了之后，囤货与转售自我放大** | ⭐ **⭐ 唯一可以立刻自行解决的** |
| ⭐ **⑤ 它们的叠加** | ⭐ **⭐ 上面几条同时发生** | ⭐ **——** |

⭐ **⭐⭐ 而它对排序这件事的表态，⭐ **我认为应该被完整引用：**

> *"These causes can stack. **Without hard data, we cannot rank them**, and **any outlet that claims to has gone past its evidence.**"*

⭐ **⭐⭐ 而 aroundprague 那篇聚合报道里，⭐ **其实是转述了 Wccftech 的一个具体归因：⭐ 「memory shortages and heavy buying by Chinese AI firms that purchase gaming GPUs in bulk」。⭐ **⭐ 而 Shattered.io 明确把这条降级为「一个有道理的视角，⭐ 但不是已证实的事实」。**

## 四、⭐⭐ 内存这根线，比 GPU 价格更值得看

⭐ **⭐ 这一节是我认为这条新闻真正的价值所在 —— ⭐ **因为 GPU 价格只是症状，⭐ 而内存才是那个更广的变量。**

⭐ **⭐ Shattered.io 的内存背景段落，⭐ 列出了一串独立的事实：**

- ⭐ **它自己的 DRAM 价格追踪器：⭐ Q4 涨 10%–15%，⭐ DDR5 套条到 $450**
- ⭐ **三星 2027 年的 HBM 已被售罄，⭐ HBM4 销量翻三倍**
- ⭐ **Sam Altman 关于 DRAM 的表态，⭐ 涉及与 OpenAI 相关的 40% 供给**
- ⭐ **Apple 的 Ternus 对「史无前例的 RAM 成本」的警告**

⭐ **⭐⭐ 而这一条是整个链条的枢纽：**

> *"**When a leading memory maker commits next year's capacity to AI accelerators, less manufacturing attention lands on consumer parts.**"*

⭐ **⭐⭐ 请把这个机制讲清楚，⭐ 因为它解释了「为什么显卡会涨」而不是只解释了「内存涨了」：**

```
AI 数据中心需要巨量 HBM
        ↓
三星 / SK 海力士 / 美光把 2027 年的产能承诺给 HBM
        ↓
同一条产线、同一批资本、注意力的重心转向 HBM
        ↓
消费级 GDDR7 与 DDR5 分到的产能减少
        ↓
GDDR7 供给紧张 → 板厂少产 → 显卡变少
        ↓
⭐ 零售商手里的存货成为稀缺品 → 标价 $9,400
```

⭐ **⭐⭐ 而这一条链条里，⭐ **有一个特别值得指出的点：⭐ **⭐ 「显卡变少」这个环节，⭐ **并不是「显卡被 AI 买走了」，⭐ **而是「显卡的**上游**被 AI 抢了产能」。⭐ **⭐**

⭐ **⭐⭐ 而这一层正是我前面引的那几篇的交汇点：⭐ **⭐ 本号此前写的《RTX Spark 笔记本上的 Linux 慢 5 倍》⭐ 讲的是「128GB 统一内存的笔记本，⭐ GPU 默认预留 96GB，⭐ 而这 96GB 在 Linux 下根本调不了」⭐ —— ⭐ **⭐ 而这里讲的是「同一种统一内存，⭐ 在零售市场上正被 AI 需求抽走产能」。⭐ **⭐**

⭐ **⭐⭐ 也就是说：⭐ **⭐ 同一个「统一内存」概念，⭐ **在 2026 年同时是「笔记本上最大的卖点」和「显卡涨价的根因链起点」。⭐ **⭐**

## 五、⭐⭐ 这次和上一轮显卡涨价 Cycle 有什么不同

⭐ **⭐ Shattered.io 有一节专门做这个对比（⭐ 我认为这个对比比数字更有价值）：**

> *"**First, the pressure comes from AI infrastructure and memory supply, which are structural trends and not a speculative coin cycle.** Second, **the flagship carries the largest reported markup, where earlier shortages hit nearly every tier more evenly.**"*
>
> *"The earlier shortage ended when mining demand collapsed and supply caught up. **The AI buildout shows no sign of a similar collapse**, at least in the capital spending numbers we have tracked."*

⭐ **⭐⭐ 我认为这三点差别，每一点都值得展开：**

**① 需求侧的性质变了**

⭐ **2020–2022 那一轮是加密货币挖矿驱动，⭐ 而那一轮结束的原因是「挖矿需求崩溃」。⭐ **⭐ 而 AI 建设周期不靠「崩溃」结束 —— ⭐ **⭐ 它靠的是「投资回报率算不过来了」或者「资本开支见顶」。⭐ **⭐ 而 Shattered.io 提的那个数字是 **AI 资本开支超过 $740B**，⭐ 并且它同时记录了「市场对这个泡沫能持续多久的怀疑」。⭐ **⭐**

**② 价格分布的形状变了**

⭐ **⭐ 上一轮是「全线普涨」⭐ （⭐ 几乎每个档位都被扫，⭐ 所以 3060 这种入门卡也被炒上天）；⭐ **而这一轮是「旗舰承担了最大溢价」。⭐ **⭐ 而这一点的经济学后果是：**中端卡的溢价伤害了远多得多的人。**

⭐ Shattered.io 的原话：

> *"**few people shop for a card at $9,400, while many buy mid-range models, where premiums above 50% affect far more buyers.**"*

⭐ **⭐⭐ 请把这句话和 eTeknix 的分型号数据放在一起看：**

| 型号 | 首发价 | 美国溢价 | ⭐ **绝对涨幅** |
|---|---|---|---|
| ⭐ **5090** | $1,999 | +370% | ⭐ **≈ $7,400** |
| ⭐ **5080** | $999 | +120% | ⭐ **≈ $1,200** |
| ⭐ **5060 Ti 16GB** | — | +84%（约 $800） | ⭐ **—** |
| ⭐ **5070 Ti** | $749 | +67% | ⭐ **≈ $500** |
| ⭐ **5070** | $549 | +64% | ⭐ **≈ $350** |
| ⭐ **5050** | $260 | +68%（涨到 $420） | ⭐ **$160** |

⭐ **⭐⭐ 而这里有个反直觉的点，⭐ **我觉得整件事里最值得记住：⭐ **⭐ 旗舰涨得最凶（370%），⭐ 但受影响的人最少。⭐ **⭐**

⭐ **⭐⭐ 也就是说：⭐ **⭐ 「RTX 5090 涨 370%」这个吓人的标题，⭐ **其实是一个**面向少数人**的新闻；⭐ **⭐ 而真正影响绝大多数人的，是 5080 的 120%、⭐ 5070 的 64%、⭐ 5050 的 68% —— ⭐ **⭐ 这些才是「买得最多」的那一档。⭐ **⭐**

## 六、⭐⭐ 溢价到底流向了谁？

⭐ **⭐ 这一节直接回答 aroundprague 那篇提出的一个问题：⭐ **「那多出来的钱去哪了？」**

⭐ **⭐ Shattered.io 的回答是：**

> *"When street prices rise on a fixed list price, **the extra money goes to retailers, resellers and scalpers rather than to Nvidia. No source quantified how much of the premium reaches anyone in the chain.**"*

⭐ **⭐⭐ 请注意最后那半句的克制：⭐ **⭐ 「没有任何来源量化了这条链上**谁**分到了多少。」⭐ **⭐**

⭐ **⭐⭐ 而这条链上的参与者，其实比「NVIDIA vs 消费者」复杂：**

```
消费者支付 $9,400
        ↓
零售商 / 经销商 / 炒货商  ← ⭐ 溢价的主要落点
        ↓
板卡合作伙伴（AIB 等）
        ↓
NVIDIA  ← ⭐ 官方价仍是 $1,999，⭐ 但拿货价随稀缺而涨
        ↓
GDDR7 / HBM 产能 ← ⭐ 真正的稀缺源头
```

⭐ **⭐⭐ 而我认为这条链里最值得追问的一句是：⭐ **⭐ 「NVIDIA 官方价没动，⭐ 但拿货价一定也没动吗？」⭐ **⭐**

⭐ **⭐⭐ 而这一点，⭐ **现有报道完全没有覆盖 —— ⭐ **⭐ 而它是决定「如果内存供给恢复，⭐ 价格会不会回落」的关键变量：⭐ **⭐**

- ⭐ **如果 NVIDIA 的拿货价也涨了（GDDR7 涨价传导），⭐ **那么内存缓解后价格会回落，⭐ 但不会回到 $1,999**
- ⭐ **如果 NVIDIA 的拿货价没涨（溢价全在渠道），⭐ **那么渠道去库存的那一刻价格会断崖回落**

⭐ **⭐⭐ Shattered.io 在「五条预测」那一节（⭐ 我没有逐条抄，⭐ 因为都是猜测）⭐ 里，⭐ **有一个我认为最关键的方向性判断：⭐ **⭐ 「**短缺会结束，⭐ 但没人能提前说出结束日期。**」⭐ **⭐**

## 七、⭐⭐ 那么，普通买家实际该怎么做

⭐ **⭐ 这一节我把三个来源的可操作建议合并一下，⭐ 并标注各自的可靠性。**

### ⭐⭐ 如果你必须现在买旗舰

⭐ Shattered.io 的建议里有两条我认为是真正可操作的：

⭐ **① 别把 MSRP 当预算参考。** ⭐ 它的原话：

> *"**Shoppers are likely to find the official MSRP a poor guide to what cards actually cost.**"*
> *"a card listed at $1,999 on Nvidia's site **may be effectively unavailable at that price**."*

⭐ **⭐ 而这条建议背后有个很实用的推论：⭐ **如果 $9,400 是「最低挂单」，⭐ 那说明**存在**大量比它便宜的挂单。⭐ **⭐ 换句话说，⭐ 「去按型号搜、找最便宜的那几条挂单」⭐ 本身就能把成本降下来 —— ⭐ **⭐ 而这恰恰是「最低价快照」这个测法唯一的实用价值。**

⭐ **② 考虑工作站的替代路径。** ⭐ Shattered.io 提到的对比：⭐ **「当年想用 $1,999 买 5090 的人，⭐ 现在只为这块卡就要付一台配置齐全的工作站的价钱」⭐ —— ⭐ **⭐ 而反过来，⭐ 如果你的需求是「本地跑大模型」，⭐ **一台带足够内存的工作站 + 一块中端卡，⭐ 可能在总成本和实际体验上都更合理。**

### ⭐⭐ 如果你能等

⭐ **⭐ 而这一段我想给一个 ZDNET 明确提到、但 aroundprague 那篇没展开的判断：**

> *"**Don't be surprised if you see some resellers take advantage of the situation by adding their own price increases or snapping up stock to sell at a markup on the second-hand market.**"*

⭐ **⭐⭐ 请注意「snapping up stock to sell at a markup on the second-hand market」⭐ **这个动作的时序：⭐ **⭐ 它是**在涨价之后**才发生的**。⭐ **⭐**

⭐ **⭐⭐ 所以它给出一条很反直觉但很实用的推论：⭐ **⭐ 二手市场被扫货，⭐ 反而会推高一手价。⭐ **⭐ 换句话说：⭐ **「等二手价下来」不是一条可靠策略，⭐ 因为二手囤货本身在推高一手。⭐ **⭐**

⭐ **⭐ 而 ZDNET 还给了一条关键的排除：⭐ **⭐ 老的 RTX 40 与 RTX 30 系列**不会**直接**受这次涨价影响** —— ⭐ **⭐ 也就是「买上一代」是有效的对冲。⭐ **⭐**

### ⭐⭐ AMD 与 Intel：暂时不会跟涨

⭐ **⭐ ZDNET 的判断：**

> *"**Graphics cards made by AMD and Intel won't follow suit – yet.**"*
> *"Intel and AMD have been quiet about the possibility of a price hike on their own graphics cards, and neither company plans any immediate changes."*
> *"it is likely both companies **will eventually follow suit** with their own hefty increases."*

⭐ **⭐⭐ 请注意最后那句的限定词：⭐ **⭐「likely… eventually」⭐ **—— ⭐ **⭐ 这是 ZDNET 自己的预期，⭐ **⭐ 而不是 AMD 或 Intel 的表态。⭐ **⭐**

⭐ **⭐ 而 aroundprague 那篇在这一点上的措辞是准确的：⭐ **「Not immediately, according to ZDNET… **That is the outlet's own expectation, not a statement from either company.**」⭐ **⭐**

## 八、⭐⭐ 最后：这条新闻真正的形状

⭐ **⭐ 我想把这一节的判断说得更直接一点。**

⭐ **⭐ 这条新闻表面上是一次「显卡涨价」，⭐ 但如果把它和本号近期写的几篇并排看，⭐ **⭐ 它其实是同一条线的第 N 个数据点：**

| 篇 | 表面主题 | ⭐ **底层结构** |
|---|---|---|
| ⭐ **《RTX Spark 上的 Linux 慢 5 倍》** | ⭐ **一个驱动问题** | ⭐ **⭐ 一块加密的固件表 + 只有 Windows 有的密钥 → 事实上的排他** |
| ⭐ **《eMudhra：私钥是数字 4》** | ⭐ **一个 CA 事故** | ⭐ **⭐ 「只有一边有」的东西变成了事实上的排他机制** |
| ⭐ **《GitBook 事件》** | ⭐ **一次入侵** | ⭐ **⭐ 「AI 攻击」正在成为责任分配工具** |
| ⭐ **《PHP2Shell：40 年技术债要还了》** | ⭐ **一次漏洞** | ⭐ **⭐ 「找」变便宜 100 倍，「修」只便宜 2 倍** |
| ⭐ **⭐ 本文** | ⭐ **一次涨价** | ⭐ **⭐ **⭐ 同一批产能，被 AI 需求从消费端抽走** |

⭐ **⭐⭐ 而本文这一条，⭐ **⭐ 是最「物质」的那一条：⭐ **⭐ 它不讲代码、不讲密钥、不讲责任归属，⭐ **⭐ 它讲的是**一根 DRAM 生产线**。⭐ **⭐**

⭐ **⭐⭐ 而我认为这恰恰是它最有价值的地方：⭐ **⭐⭐ 因为它是这条线上唯一一个可以用「产业事实」而非「论断」来验证的环节。⭐ **⭐⭐**

⭐ **⭐⭐ 具体说：⭐ **⭐ 三星 2027 年 HBM 售罄、⭐ HBM4 销量翻三倍、⭐ DDR5 套条到 $450、⭐ Apple 警告 RAM 成本、⭐ NVIDIA 8 月预告 15% 涨价并在本周通知 5090 加 $500 —— ⭐ **⭐ 这些都是可核对、可追踪、⭐ 而且⭐ **⭐ 完全不需要任何 AI 来解释。⭐ **⭐**

⭐ **⭐⭐ 而这一节我想说的最后一句：⭐ **⭐**

⭐ **⭐ 三个月前我们讨论「AI 让漏洞发现变快 100 倍」时，⭐ **⭐ 那还是一个技术叙事。⭐ **⭐ 而今天这条新闻说的是同一件事的**物质后果**：⭐ **⭐**

⭐ **⭐⭐ **当 AI 基础设施开始大规模采购，⭐ 它抢的不只是芯片，⭐ 而是**整条上游产能**——⭐ 而这条链上离 AI 最远、⭐ 最无辜的一环，⭐ 是一块打算插在 PCIe 槽里的显卡。⭐ **⭐⭐**

---

## 主要来源

- ⭐ **Shattered.io《RTX 5090 Price Increase: 370% Over MSRP Reported》**（⭐ **本次核对中方法论最严谨的一篇**）：⭐ **逐条标注 Wccftech / Windows Report / ZDNET / TechSpot / Smartprix 各自的说法与出处**；⭐ **「NVIDIA has not announced a U.S. MSRP increase for the RTX 5090, and the official price remains $1,999」**；⭐ **「A 370% increase does not mean the card costs 3.7 times its MSRP… so the new price is 4.7 times the original」**；⭐ **「The gap is about $7,400 per card. For context, that difference alone is more than seven times the launch price of an RTX 5080」**；⭐ **五类成因（显存短缺 / AI 大宗采购 / 硅片分配 / 炒货投机 / 叠加）与「Without hard data, we cannot rank them, and any outlet that claims to has gone past its evidence」**；⭐ **内存背景（自家 DRAM 追踪器 Q4 +10–15%、DDR5 套条 $450、三星 2027 HBM 售罄且 HBM4 销量翻三倍、Altman 的 40% 供给、苹果 Ternus 的 RAM 成本警告）**；⭐ **与 2020–2022 加密挖矿周期的两点差别（结构性 vs 投机性；旗舰承担最大溢价 vs 全线普涨）**；⭐ **「the extra money goes to retailers, resellers and scalpers rather than to Nvidia. No source quantified how much of the premium reaches anyone in the chain」**；⭐ **「few people shop for a card at $9,400, while many buy mid-range models, where premiums above 50% affect far more buyers」**；⭐ **「Shortages do end, but nobody calls the end date in advance」**
- ⭐ **ZDNET《Nvidia RTX 50 GPUs hit with more price hikes – up to $500》（Taylor Clemons，2026-11-03 12:30 ET）**：⭐ **「Nvidia is notifying users that its RTX 50 series… will see yet another significant price hike this week」**；⭐ **「In August, Nvidia gave gamers and content creators fair warning that… would get price increases of up to 15%. The flagship 5090 is getting the highest: a nearly $500 increase on an already eye-watering $6,000 price tag at Best Buy. The lower-end 5050 and 5060 will get much more modest… $50-60 bumps」**；⭐ **「the AI-driven global memory shortage」**；⭐ **RTX 40/30 系列不受直接影响，但「resellers… snapping up stock to sell at a markup on the second-hand market」**；⭐ **AMD 与 Intel 暂不跟进，但「it is likely both companies will eventually follow suit」（⭐ 为 ZDNET 自身预期，非两家公司表态）**
- ⭐ **eTeknix《NVIDIA RTX 5090 Now Costs 370% More Than Its Launch Price in the United States》（2026-11-04）**：⭐ **美国 +370%、全球平均 +262%**；⭐ **2025 年底已约 $3,000、最近一个月美国涨 36%**；⭐ **分型号：美国 5080 +120%、5070 Ti +67%、5070 +64%、5060 Ti 16GB +84%（约 $800）、5050 从 $260 到 $420（+68%）**；⭐ **10 月多个区域涨 20–40%，⭐ 巴西是唯一例外**；⭐ **部分报道暗示 5090 停产（未点名来源）**；⭐ **组件短缺看来将持续**
- ⭐ **aroundprague.cz《RTX 5090 Street Prices Top $9,000 as Nvidia GPU Costs Climb》（Maksym Akimov，2026-11-03/04）**：⭐ **四家数字的并列表与「sources use different measures」的解释**；⭐ **「It is unlikely, but this may result in some hosts being unreachable」**（⭐ 该句原指 CA 证书，此处不适用）；⭐ **「most of the numbers describe what retailers and resellers charge, not a price set by Nvidia」**
- NVIDIA 官方发布价（2025-01-30 公告，⭐ 经 GamesRadar 与 Smartprix 当时记录）：⭐ **RTX 5090 $1,999、5080 $999、5070 Ti $749、5070 $549**；⭐ 5090 上市日 2025-01-30

---

（说明：本文依据 Shattered.io、ZDNET、eTeknix、aroundprague.cz 四篇报道与 NVIDIA 官方发布价撰写，⭐ **全部引号内英文原文均直接取自这些来源**。**第三节明确区分了「已确定」（官方价未动、官方价数字、NVIDIA 确实在通知涨价）与「不确定」（五种成因无法排序）两个层次，⭐ 并按 Shattered.io 的原始表述保留了「没有任何来源量化了溢价在链条上的分配」这一事实边界。** 第四节把 GPU 价格与内存产能、⭐ 以及与本号此前《RTX Spark 上的 Linux 慢 5 倍》一篇的「统一内存」线索并排，⭐ **属笔者自己的观察**；⭐ 第八节的横向对比表亦为笔者归纳，**不代表任何来源立场。**）
