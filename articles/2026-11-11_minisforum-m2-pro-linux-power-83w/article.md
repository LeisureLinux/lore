---
title: "Minisforum M2 Pro 跑 Linux：闲置 8.4 W，满载 83 W"
date: 2026-11-11
slug: minisforum-m2-pro-linux-power-83w
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：LinuxLinks《Minisforum M2 Pro Mini PC running Linux – Power Consumption》（Steve Emms，2026-11-09）全 4 页正文、图表说明与两张电费表 ＋ 系列 Introduction / Benchmarks 篇的硬件规格 ＋ 站点 Minisforum 标签页发布时间线 ＋ 本文按原文电价 26.32p/kWh 对全部 22 个电费数值逐项算术复核（含 8h/日 与 24h 闲置两种口径）＋ Intel Core Ultra X7 358H / Panther Lake / Arc B390 规格与 PL1/PL2 功耗墙机制对照"
original_date: 2026-11-09
original_url: "https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-power-consumption/"
description: "本文解读 LinuxLinks 对 Minisforum M2 Pro（Core Ultra X7 358H，16 核 16 线程 Panther Lake，Arc B390 核显，32 GB LPDDR5X）在 Ubuntu GNOME 下的功耗实测，并逐项复核其电费表。核心数据：闲置 8.4 W（双显示器关闭）/ 9.8 W（双显示器开启）、完全拔掉显示器 6.7 W；日常轻负载 15.6 W；CPU 满载在 BIOS Performance Mode 下 83 W，切到 Ubuntu Power Saver 立刻降到 23 W，BIOS Balance Mode 下从初始 82.9 W 回落到 58.9 W。同一台机器从 23 W 到 83 W 相差 3.6 倍，原因是两个 BIOS 预设的 PL2 都是 65 W，但 Performance 把持续功耗墙 PL1 也设成 65 W，Balance 只给 45 W，所以持续负载后读数会掉约 24 W。文章指出这篇评测最容易被误读的地方：把「8.4 W 低功耗」当成机器属性，而它其实是「BIOS 预设 × Ubuntu 电源档 × 显示器连接状态 × 负载类型」四个变量的组合；以及 £19.37/年这个数字只在英国 26.32p/kWh、全年 24 小时闲置、双显示器连接但关闭的口径下成立，按每天 8 小时轻负载算是 £11.99/年，按中国居民电价 0.55 元/kWh 换算 24 小时闲置约 40.5 元/年。也记录 12 台对照机的完整排序与两个重要干扰项：Core i5-12400F 台式机的 RTX 3060 Ti 单独闲置就吃约 11 W（双显示器开时 21 W），Minisforum MS-02 Ultra 的 25GbE 网卡单独约 10 W。结论：M2 Pro 日常与自家 M2 接近，压力测试才拉开差距；真正该看的是满载时 PL1 设了多少，以及评测有没有把显示器、独显、附加网卡的功耗算进主机。"
published: true
---

> 一手：一台 mini PC 的功耗实测，全 4 页正文与两张电费表（2026-11-09）
> 复核：本文按原文电价把 22 个电费数值逐项重算，并换算了另一种电价口径
>
> 评测里的功率数字，离开测试条件就是没有意义的。

Steve Emms 11 月 9 日发了 Minisforum M2 Pro 系列的第三篇，专测功耗。机器是 Core Ultra X7 358H（16 核 16 线程 Panther Lake）、Arc B390 核显、32 GB LPDDR5X，跑 Ubuntu + GNOME，用电表在市电插座量整机功率（不含显示器自身耗电）。对照阵容挺全：1 台 mini 工作站、8 台 mini PC、2 台台式机。

如果只看结论，容易记成「M2 Pro 闲置 8.4 W，很省电」。但把四页读完，最值得记住的其实是另一个数字：同一台机器在 CPU 满载时可以是 23 W，也可以是 83 W。

## 一、四个场景，四个数量级

| 场景 | M2 Pro | 备注 |
|---|---|---|
| 闲置，双显示器连接且关闭 | 8.4 W | BIOS 选 Silent Mode |
| 闲置，双显示器连接且开启 | 9.8 W | 显示器自身耗电已排除 |
| 闲置，完全拔掉显示器（headless） | 6.7 W | 比「连着但关掉」再省 1.7 W |
| 日常轻负载 | 15.6 W | Ubuntu Balanced 档；浏览、邮件、办公、编译、视频、音乐、虚拟机 |
| CPU 满载，BIOS Performance + Ubuntu Balanced/Performance | 83 W | 用 s-tui 加压 |
| CPU 满载，BIOS Performance + Ubuntu Power Saver | 23 W | 同一个 BIOS 预设，只换系统电源档 |
| CPU 满载，BIOS Balance | 82.9 W → 58.9 W | 初始读数，持续负载后回落约 24 W |

从 8.4 W 到 83 W 是近 10 倍；从 23 W 到 83 W 是 3.6 倍 —— 而后者没换硬件、没换负载，只改了 Ubuntu 的电源档。

原文给了解释：两个 BIOS 预设把短时功耗墙 PL2 都设成 65 W，差别在持续功耗墙 PL1 —— Performance Mode 的 PL1 也是 65 W，Balance Mode 只给 45 W。所以 Balance 下刚开始也能冲到 82.9 W，跑一阵 PL1 生效，就落到 58.9 W（降约 29%）。这解释了一个常见困惑：为什么烤机时功率计先高后低。那不是机器「降频坏了」，是功耗墙按设计在切换。

顺带说一处测试条件变化：闲置测试用的是 BIOS Silent Mode，轻负载篇作者明确写「我在闲置测试之后改了 BIOS 预设」。所以 8.4 W 和 15.6 W 不是同一套 BIOS 设置下的读数，直接相减要小心。

## 二、横向对照：差距出现在哪一段

闲置（双显示器连接、关闭）：

- M2 Pro 8.4 W；自家 Minisforum M2 8.1 W、9.2 W（双显示器开）更低一点；
- BOSGAME VTA-439 6.4 W / 7.4 W，是这组里闲置最省的一台；
- M2 Pro 比 BOSGAME M7、Minisforum MS-02 Ultra 都低。

日常轻负载：M2 Pro 15.6 W，比 M2 高 2.1 W、比 VTA-439 低 0.3 W；只有 M2 和 DreamQuest N100 比它更省。BOSGAME M6 17.4 W、Minisforum UM890 Pro 17.9 W、ASRock NUC BOX-255H 25.1 W 都在它之上。

CPU 满载（BIOS Performance 档）：M2 Pro 83 W，夹在 M2 的 64 W 与 VTA-439 的 94 W 之间。原文自己的总结很克制：M2 Pro 在日常使用中与 M2 接近，差距是在 CPU 压力测试里拉开的；VTA-439 相对 M2 Pro 最明显的优势在闲置，轻负载时两者基本持平。

这里有两个不该算到主机头上的干扰项，原文特意列在图表说明里：

- Core i5-12400F 台式机带一张 ASUS RTX 3060 Ti，`nvidia-smi` 显示单卡闲置就约 11 W（双显示器开时 21 W）；
- Minisforum MS-02 Ultra 的读数含一张 25GbE 网卡，单独约 10 W。

所以那两张台式机/工作站在榜尾的高功耗，一部分是扩展卡而不是 CPU 平台。原文也提醒：硬件配置、电源设置、内核版本、发行版都会影响闲置功耗。

## 三、£19.37 一年，到底怎么算出来的

原文第 4 页给了两张电费表，单价 26.32p/kWh，只算主机用电。我把 22 个数值全部按公式重算了一遍，逐项吻合：

| 口径 | 公式 | 抽样复核 |
|---|---|---|
| 每天 8 小时轻负载，全年 | W ÷ 1000 × 2920 h × 0.2632 | 15.6 W → £11.99；12.9 W → £9.91；64.5 W → £49.57 |
| 24 小时闲置，全年 | W ÷ 1000 × 8760 h × 0.2632 | 8.4 W → £19.37；6.4 W → £14.76；37.3 W → £86.00 |

两种口径别混：£11.99 是「每天只用 8 小时」，£19.37 是「一年到头不关机的闲置」，后者更高是因为小时数多了三倍，尽管功率更低。headless 的 6.7 W 对应 £15.45/年，比连着显示器的闲置省 £3.92。M2 Pro 的 24 小时闲置比 M2 多 69p、比 VTA-439 多 £4.61；MS-02 Ultra 是 £64.10，其中那张 25GbE 网卡约占 10 W。

这个数字有明显的地域与用法依赖。按中国居民电价约 0.55 元/kWh 做同样的算术（仅示意，不含阶梯电价与税费）：

| 状态 | 24×7 一年的电费 |
|---|---|
| 8.4 W 闲置 | 约 ¥40.5 |
| 15.6 W 轻负载 | 约 ¥75.2 |
| 23 W（Power Saver 满载） | 约 ¥110.8 |
| 58.9 W（Balance 满载稳定值） | 约 ¥283.8 |
| 83 W（Performance 满载） | 约 ¥399.9 |

也就是说，真正决定一年电费上限的，是你会不会让这台机器长时间跑在 PL1 65 W 的档位上，而不是那个 8.4 W 的闲置值。把「£19.37/年」当成产品标签，会漏掉满载那一段近 10 倍的摆幅。

## 四、这类评测该怎么读

三点方法上的提醒，比记住某个瓦数有用：

1. 原文图表说明里那句「Hardware configurations, power settings, kernel versions and Linux distributions can all affect idle power draw」正是这个意思：功率是配置的函数，不是硬件的常量。 BIOS 预设（Silent / Balance / Performance）、Ubuntu 电源档（Power Saver / Balanced / Performance）、显示器连接状态、负载类型，四个变量任意换一个，读数就能变几倍。看到一个 W 值，先找它对应的那一行条件。
2. 看持续值，也看初始值。 Balance 模式 82.9 → 58.9 W 的回落是 PL1 生效；只记「峰值 83 W」或只记「稳定 58.9 W」都不完整。
3. 把附加设备的功耗拆出来。 独显 11–21 W、25GbE 网卡 10 W，在低功耗 mini PC 的对比里足以改变排序；原文把它们单列在图表说明里，是这份评测做得比较扎实的地方。

还有一处诚实边界：轻负载那一段作者自己写了「功率随任务切换和后台进程起伏」，给的是单一代表值 15.6 W，不是时间加权平均；闲置测试与轻负载测试的 BIOS 预设还不同。这些都不构成缺陷，但决定了数字不能当精密基准用。

## 五、事实边界

- 全部功率与电费数据取自 LinuxLinks 该系列的功耗篇（2026-11-09，4 页）；本文按 26.32p/kWh 对全部 22 个电费数值逐项算术复核，均吻合。
- 中国电价换算采用 0.55 元/kWh 的示意值，仅用于说明量级，不代表任何地区实际电价、阶梯计价或税费。
- 本文未持有 M2 Pro 硬件，未复现 s-tui 加压、BIOS 预设切换或电表读数；性能与基准部分（Introduction / Benchmarks 两篇）未在本文展开。
- 对照机器的功耗读数含各自扩展卡差异（RTX 3060 Ti、25GbE 网卡），原文已在图表说明中标注；跨机型比较不宜直接当作 CPU 能效排名。
- 原文未给出电表型号、采样间隔、环境温度与 Ubuntu 具体版本/内核，故数值精度以原文口径为准。

## 六、结论

M2 Pro 的成绩单可以一句话说完：日常用起来和自家 M2 差不多（15.6 W 对 13.5 W），闲置比 VTA-439 略高（8.4 W 对 6.4 W），压力测试才把差距拉开（83 W，介于 M2 的 64 W 与 VTA-439 的 94 W 之间）。 按英国电价全年闲置 £19.37，按每天 8 小时轻负载 £11.99 —— 数字都不大。

但这篇文章真正的用处，是提醒读者「低功耗」从来不是一个可以直接抄的规格：同一台机器，电源档一换就能从 23 W 跳到 83 W；拔掉两块显示器又省下 1.7 W；别人榜尾的高功耗里可能藏着一张独显或一块 25GbE 网卡。看功耗评测，先读测试条件那一栏，再读数字。

## Sources

- LinuxLinks《Minisforum M2 Pro Mini PC running Linux – Power Consumption》（Steve Emms，2026-11-09，全 4 页）：<https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-power-consumption/>
- 分页：轻负载 <https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-power-consumption/2/> ｜ CPU 负载 <https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-power-consumption/3/> ｜ 电费 <https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-power-consumption/4/>
- 系列：Introduction <https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-introduction/> ｜ Benchmarks <https://www.linuxlinks.com/minisforum-m2-pro-mini-pc-running-linux-benchmarks/>
