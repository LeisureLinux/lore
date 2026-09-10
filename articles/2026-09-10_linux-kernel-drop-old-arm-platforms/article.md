# Linux 内核准备删掉约 5.5 万行老旧 ARM 平台代码

> 译文来源：Phoronix《The Linux Kernel Planning To Remove Around ~55k Lines Of Old ARM Platform Code》，Michael Larabel，2026-09-08。原文：<https://www.phoronix.com/news/Linux-Dropping-Old-ARM-Ahead>

## 事件：13 个补丁，一次砍掉 5.5 万行

在当前的 Linux 7.3 内核中，[大量老旧的 32 位 ARM 平台已被标记为 deprecated](https://www.phoronix.com/news/Linux-7.3-SoC)，与之相伴的是数百个只为这些过时平台服务的驱动被连带"孤儿化"。被弃用代码的移除，计划在下一个或下下个内核周期内完成。

2026 年 9 月 8 日，Arnd Bergmann（SoC/platform 子系统维护者）发出了一组 **13 个补丁**，正式删除这些已被弃用的 ARM 平台，释放超过 **5.5 万行代码**和相应数量的设备树（Device Tree）文件。这批平台移除之后，那些被孤儿化的驱动也可以陆续清退，代码瘦身还会继续。

## 被移除的平台清单

这次上"断头台"的老平台包括：

| 平台 | 出身备注 |
|---|---|
| SA1100 | Intel StrongARM，手持设备的上古豪杰 |
| Footbridge | DEC/NetWinder 时代的 21285 主桥 |
| RISCPC | Acorn RISC PC，ARM 的"祖籍"机器 |
| Orion / Dove / MV78xx0 | Marvell 早期 SoC 家族 |
| OMAP24xx | TI OMAP2，诺基亚时代的试验田 |
| i.MX31 | Freescale i.MX3 系列 |
| 无 MMU 的 i.MX 目标 | 走 ARM7TDMI/无 MMU 路线的变体 |
| LPC18xx | NXP LPC 系列 MCU |
| STM32F4/F7/H7 | ST 的 MCU 线（内核里跑 MCU，属于平台代码维护负担） |
| Versatile MPS2 | ARM 官方仿真/验证平台 |
| AT91 SAMV7 | Microchip（Atmel）SAMV7 MCU |
| Axxia | LSI/Amdox 通信 SoC |
| 传统 PXA 板级文件 | Marvell PXA 逐板 board file 遗留部分 |

## 为什么现在砍

Arnd 在 [补丁说明](https://lore.kernel.org/lkml/20260908152808.3928630-1-arnd@kernel.org/) 里给出的节奏是：这些补丁本可以赶在 **Linux 7.4** 合入，但他更倾向于放到 **Linux 7.5**，理由有二：

1. **保持依赖关系简单**——7.4 周期里的交叉依赖（尤其是那些孤儿化驱动的连带清理）不值得赶工；
2. **越过今年的 LTS 内核版本**——避免刚发布的 LTS 还要背着一堆即将蒸发的历史包袱进入长期支持窗口。

推迟到 7.5 也给了仍在使用这些平台的用户一个**申诉窗口**：如果有人真的还在 mainline 内核上跑这些古董，现在正是站出来举证的最佳时机。

至于动机，Phoronix 的判断很直白：这些陈旧的内核代码已经成为上游开发者继续做代码清理和交付新特性的**绊脚石**。而 2026 年还在跑这些远古 32 位 ARM 平台、且用的是 mainline 内核的用户，"概率可能非常渺茫"。

## 我们的解读：这是一次教科书式的平台退役

**「deprecated → orphaned → removed」是内核处理僵尸平台的完整三段式。** 7.3 先把平台标弃用（用户还能看到显眼的启动警告和移除时间表），再等一到两个周期做实际删除。对发行版维护者来说，这个窗口足够把受影响的旧设备从支持列表里摘掉。

**删除是乘法而不是加法。** 5.5 万行平台代码只是明面上的数字；真正的大头是那几百个只被这些平台引用的驱动——平台一删，`depends on` 链条断了，驱动就成了永远编译不进内核的死代码，下一轮清理自然轮到它们。ARM 平台代码过去十年从"每板一个 board file"演进到"设备树 + 少量 machine 描述符"，这次清理正是把最后一批没完成 DT 化改造的钉子户拔掉。

**MCU 平台进内核的教训。** STM32F4/F7/H7、SAMV7、LPC18xx 这类 MCU 平台当年进入 mainline，靠的是"上游化总比下游分叉好"的逻辑。但一旦维护者失去兴趣、硬件退出市场，它们在内核树里就成了纯负担。这次连它们一起退役，说明社区对"内核该背多少历史硬件"的容忍度在收紧。

**对国产/嵌入式生态的提醒。** 国内不少老款工控机、开发板还压着这些平台（尤其是 OMAP、i.MX31、PXA 一系）。如果你的产品线还依赖 mainline 直持的这些 SoC，7.5 之后要么维护 downstream 分支，要么迁移到现役平台。反向操作——把仍在量产的老 SoC 重新"认领"回内核——理论上可行，但需要有人长期接手维护，这在 Arnd 的申诉窗口关闭之后难度会大得多。

**时间线小结：** Linux 7.3 标弃用 → 7.4 窗口处理依赖 → 7.5（预计 2026 年底/2027 年初）正式删除。在此之前，任何平台都有被"捞回来"的理论可能。

---

*参考：[Phoronix 原文](https://www.phoronix.com/news/Linux-Dropping-Old-ARM-Ahead) · [Arnd 的补丁序列](https://lore.kernel.org/lkml/20260908152808.3928630-1-arnd@kernel.org/)*
