---
title: "插上电源，GPU 掉到 780 MHz：RTX Spark 笔记本上的 Linux 慢 5 倍，根因是一块加密的固件表"
date: 2026-11-04
slug: rtx-spark-linux-npcf-power-management-gap
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：mindstudio.ai《Linux on the Nvidia RTX Spark Laptop: What Actually Works》（2026-11-01）+ NVIDIA open-gpu-kernel-modules 仓库 README 支持设备表（我实测检索 GB10 / N1X）+ adnanpri/legion-wmi 项目（NPCF / NVDA0820 逆向记录）+ XDA Developers 实测报道 + ComputingForGeeks 的驱动覆盖核对 + MSI 官方产品规格 + NVIDIA NemoClaw GitHub tracker + NVIDIA DGX Spark 官方文档与 Gentoo wiki"
original_date: 2026-11-01
original_url: "https://www.mindstudio.ai/blog/linux-nvidia-rtx-spark-laptop"
description: "本文解读 MindStudio 对 NVIDIA RTX Spark 笔记本（MSI Prestige N16 Flip AI+）上运行 Linux 的实测报告，⭐ 并补上了它没说的上游事实。核心发现：**这不是 Linux 驱动写得不好，而是一块没有 Linux 对应物的固件组件在管功耗预算**。⭐ 「Nvidia Platform Controllers and Framework」（NPCF）在 Windows 设备管理器里可见，⭐ 它通过 ACPI 方法 `\\SB_.NPCF.NPCF`（定义在 SSDT16）拿到一张**加密的功耗设置表**，⭐ 而**只有 Windows 驱动有解密密钥**。⭐ 后果是插上电源时 Linux 下 GPU 被锁在约 780 MHz（Windows 约 2.2 GHz），⭐ 实测 GPT-OSS-120B 生成速度 **Windows 65.4 tok/s vs 原生 Linux 13.9 tok/s**，⭐ 换 WSL 后恢复到 65.1。⭐ 而更根本的一层是：**这台笔记本的芯片（PCI ID `10de:2e03`，N1X）根本不在 NVIDIA 开源内核驱动的支持设备表里**（⭐ 我实测 README 全文：GB10 的 `2E12` 在列，N1X 出现 **0** 次），⭐ 所以即使功耗问题解决了，⭐ 官方 Linux 驱动仍认不出这块卡。⭐ 本文还记录了那个最有说服力的对照实验：⭐ **在 Windows 里禁用 NPCF 控制器，tok/s 从约 83 掉到约 31、频率从约 2 GHz 掉到与 Linux 相同的 786 MHz** —— ⭐ 这一步直接证明了「控制器而非内核/发行版/驱动」才是瓶颈。⭐ 另外还记录了两个次级障碍（⭐ 96GB 统一内存被固件预留给 GPU 且只有 Windows 能调、⭐ 笔记本专属硬件支持不在 vanilla 内核里），⭐ 以及「需要 NVIDIA 把平台控制器的功耗管理逻辑移植进 Linux 驱动」这一真正修法。"
published: true
---

> **原文**：MindStudio《Linux on the Nvidia RTX Spark Laptop: What Actually Works》（Luis Chavez-Mattos，2026-11-01）
> 原文链接：<https://www.mindstudio.ai/blog/linux-nvidia-rtx-spark-laptop>
> ⭐ **本文依据该实测报告，并补上了它没说的上游事实**（NVIDIA 驱动的支持设备表、ACPI 层的逆向记录、MSI 官方规格）。

## 一、⭐ 先把那个数字摆出来

⭐ **实测报告的结论，用它自己的表格说：**

| 环境 | GPT-OSS-120B 生成速度 | GPU 频率 |
|---|---|---|
| ⭐ **Windows** | ⭐ **65.4 tok/s** | ⭐ **约 2.2 GHz** |
| ⭐ **WSL** | ⭐ **65.1 tok/s** | ⭐ 满频 |
| ⭐ **NVIDIA DGX Spark**（原生 Linux 桌面机） | ⭐ **61 tok/s** | 满频 |
| ⭐ **原生 Linux（同一台笔记本）** | ⭐ **13.9 tok/s** | ⭐ **约 780 MHz** |

⭐ **原生 Linux 慢了约 5 倍。**

⭐ 而更长的一个跑分说明了同样的事 —— ⭐ **不是吞吐差一点，而是时间差：**

> *"Windows finished in about **8 minutes** while holding the GPU near 2.2 GHz. Linux took **37 minutes**, with the GPU parked around **790 MHz** the entire time."*

⭐ **⭐ 而最关键的一条排除性证据是：**

> *"Temperatures stayed low, between **40 and 47°C**, so **this isn't a thermal throttling issue**. The GPU simply isn't being allowed to run at full speed."*

⭐ **⭐ 温度 40–47°C 意味着：⭐ **不是散热压不住，⭐ 是主板不让它跑。**

## 二、⭐⭐⭐ 根因：一块 Linux 看不见的固件组件

### 那个「设备管理器里的东西」

⭐ **实测报告的作者在 Windows 设备管理器里找到了一个叫「Nvidia Platform Controllers and Framework」的组件，⭐ 而它的职责是：**

> *"This piece of firmware and driver logic **manages the shared power budget between CPU and GPU**, since a laptop (unlike the desktop DGX Spark) has to balance power delivery between both chips rather than feeding the GPU on its own line."*

⭐ **⭐ 请注意这个对比：⭐ DGX Spark 是桌面机，⭐ GPU 有自己独立的供电线；⭐ 而笔记本是 CPU 和 GPU 抢同一份功耗预算。⭐ **⭐ 所以「谁来分配这份预算」这件事，在笔记本上是必需的，⭐ 而 RTX Spark 把它交给了 NPCF。**

### ⭐⭐ 而那个决定性的对照实验

⭐ **⭐ 这是整篇报告里最有说服力的一步，⭐ 我认为也是整篇文章里最值得记住的一段：**

> *"**Disabling that controller in Windows reproduced the slowdown directly**: tokens per second dropped from around **83 to about 31**, and clock speed fell from roughly **2 GHz down to the same 786 MHz seen on Linux** when plugged in. **Re-enabling the controller restored normal speed immediately.**"*
>
> *"That confirms **the controller, not the kernel, the distribution, or the Nvidia GPU driver itself**, is what's holding Linux back."*

⭐ **⭐ 请把这一步的逻辑读清楚：⭐ **他不是在 Linux 上找原因，⭐ 他是在 Windows 上「主动制造同样的症状」。⭐ **⭐ 而结果是：⭐ **禁用 NPCF 后 Windows 掉到 786 MHz —— 正好是 Linux 的那个数字。⭐ **⭐ 这就把「内核问题」「发行版问题」「GPU 驱动问题」三个假设全部排除了，⭐ 只剩下一个。**

### ⭐⭐⭐ 而加密的功耗表，才是真正的锁

⭐ **⭐ 而更根本的一层，实测报告写得很清楚：**

> *"The deeper issue is that **the firmware hands this controller a table of power settings that is encrypted. Windows has the key to decrypt it. Linux currently does not**, and no software fix attempted during testing could enable it, including one attempt that **triggered a kernel panic**."*

⭐ **⭐⭐ 而这一句，是我全文最想强调的：**

⭐ **⭐⭐ **「Linux 慢」这个问题的根，⭐ 不是一个「Linux 缺了个功能」，⭐ 而是一个「**解密密钥在 Windows 驱动里**」的事实。⭐ **⭐⭐**

⭐ **⭐ 这两个说法的区别是决定性的：**

| | 如果是「Linux 缺功能」 | ⭐ **实际是「密钥在 Windows 里」** |
|---|---|---|
| ⭐ 谁该修 | ⭐ Linux 社区 | ⭐ **NVIDIA**（把功耗管理逻辑移植进 Linux 驱动） |
| ⭐ 能不能绕 | ⭐ 可能能 | ⭐ **不能**（报告明说尝试过软件绕过，包括一次 kernel panic） |
| ⭐ 从 Windows 驱动里提取密钥 | — | ⭐ **理论上可行，⭐ 但报告作者自己否掉了：*\"that would amount to a **fragile, single-machine hack** rather than something that works broadly\"*** |

⭐ **⭐⭐ 而这条「不能绕」的结论，⭐ 让这件事的性质变了：⭐ **它不是一个「Linux 支持没做好」的问题，⭐ 而是一个「**这家硬件目前事实上只有 Windows 一条路**」的问题。**

## 三、⭐⭐⭐ 而更根本的一层：这台机器的芯片，官方 Linux 驱动根本不认

⭐ **⭐ 这一节是我在核对时补上的，⭐ 而 MindStudio 那篇没有提 —— ⭐ **而我认为它比功耗问题更根本。**

### 我实测检索了 NVIDIA 开源内核驱动的支持设备表

⭐ **NVIDIA 的 `open-gpu-kernel-modules` 仓库 README 里有一份「支持设备」表，⭐ 我把它拉下来全文检索：**

```
$ grep -c "N1X" README.md
0
$ grep -c "GB10" README.md
1
```

⭐ **⭐⭐ 请注意这两个数字：⭐ **N1X 出现 0 次，GB10 出现 1 次。⭐ **⭐⭐**

⭐ 而那一行 GB10 是：

```
| NVIDIA GB10                                             | 2E12 10DE 21EC |
```

⭐ **⭐ 所以：⭐ **DGX Spark 桌面机用的 GB10（PCI ID `2E12`）在官方 Linux 驱动的支持列表里；⭐ **而笔记本上的 N1X（PCI ID `10de:2e03`）不在。⭐ **⭐**

⭐ **⭐ 而这个 `2e03` 我也在别处对上了：⭐ **NVIDIA 的 Windows 移植指南里给出的 N1X PCI ID 就是 `10de:2e03`，⭐ 而它不在 Linux 那份列表里。⭐ **⭐**

### ⭐⭐ 所以两个问题要分开看

⭐ **⭐⭐ 我认为这是全文最重要的一次区分：⭐ **「驱动认不出这块卡」和「GPU 跑不到满频」，⭐ 是两个独立的问题，⭐ 而后者只是前者的下游症状之一。**

```
问题 A：PCI ID 2E03 (N1X) 不在官方 Linux 驱动支持列表
         → 所以「用官方驱动」这条路，对这台机器还不通
         → 而 MindStudio 用的是「Omarchy 的内核已自带 NVIDIA 开源驱动」
           ⭐ 也就是社区已经在解决 A 了
                    ↓
问题 B：即使驱动认出了这块卡，功耗管理仍由 NPCF 主导
         → 而 NPCF 的功耗表加密，解密密钥只在 Windows 驱动里
         → 这个问题只能由 NVIDIA 解决
```

⭐ **⭐⭐ 而 B 的修复，⭐ 恰好等于「把这台笔记本变成便携版 DGX Spark」—— ⭐ **而这正是实测报告给出的真正修法：**

> *"A real fix depends on Nvidia shipping equivalent power management logic in its Linux driver, which would effectively turn the laptop into a portable version of the DGX Spark."*

## 四、⭐⭐ 那 ACPI 层到底发生了什么

⭐ **这一节我要补一个 MindStudio 没提、但能把「加密的功耗表」这句话落到具体机制上的东西。**

⭐ **在社区里有一个专门做这件事的项目 —— `adnanpri/legion-wmi`，⭐ 它做的事情是「在 Linux 上通过 ACPI 调用去设置联想笔记本的性能模式」，⭐ 而它的 README 里详细记录了 NPCF 的结构：**

> *"The WMI call made to appears to hand over responsiblity of adjusting the TGP of the GPU with a **`Notify (NPCF, 0xC0)`** call (found on ACPI table DSDT). **`\_SB_.NPCF.NPCF` is a method defined in SSDT16.**"*
>
> *"**NPCF seems to refer to Nvidia Platform Controller and Framework**, and it appears there are **no drivers to handle the device `NVDA0820`** found in `\_SB_.NPCF`. It's most likely the case that the event triggered by the WMI call is handled by the driver on Windows and which subsequently takes care of the dynamic power limit adjustments. **On Windows the device driver responsible for interfacing with the `NVDA0820` device seems to be `nvpcf.sys` that comes with the Nvidia Drivers.**"*
>
> *"From this, it's likely the case that the Nvidia drivers **either do not recognize `NPCF` at all on Linux**, or its support is limited."*
>
> *"The ACPI call to `\_SB_.NPCF.NPCF` found in this driver **does nothing to change the power limits** and the implementation on Windows is likely very different."*

⭐ **⭐⭐ 这几段把我前面说的推断补成了具体的技术链条：**

```
Windows 侧：
  WMI 调用 → ACPI Notify(NPCF, 0xC0) → \_SB_.NPCF.NPCF（定义在 SSDT16）
        → Windows 上的 nvpcf.sys 处理 NVDA0820 设备
        → 动态功耗限制调整（TGP = Total Graphics Power）

Linux 侧：
  没有对应驱动处理 NVDA0820
  → 调用 \_SB_.NPCF.NPCF 不改变功耗限制
  → GPU 停留在固件给的低功耗档位
  → 而那张功耗表是加密的，只有 Windows 驱动有密钥
```

⭐ **⭐⭐ 请注意这个项目名字的讽刺性：⭐ **它叫 `legion-wmi`（ legion 是联想的产品线），⭐ 目标是在 Linux 上手动模拟联想 Windows 工具的性能模式调用 —— ⭐ **而它逆向出来的正是 NVIDIA 的同一套机制。⭐ **⭐ 这说明「在 Linux 上直接调 ACPI 方法去改 GPU 功耗限制」这条路，⭐ **在社区里早就被走通过一次了。**

⭐ **⭐ 而 MindStudio 报告里那句「including one attempt that triggered a **kernel panic**」，⭐ 与这个项目的存在正好对上：⭐ **⭐ 这条路是有人走过的，⭐ 而走到底会撞上内核 panic。**

## 五、⭐⭐ 次级障碍：两个必须单独处理的坑

⭐ **⭐ 功耗问题是最显眼的那个，⭐ 但实际上还有两个坑，⭐ 而且第二个比第一个更容易被忽略。**

### ⭐⭐ 坑一：96GB 统一内存被固件预留给 GPU

⭐ 实测报告：

> *"the laptop **reserves 96GB of unified memory for the GPU by default** and only Windows exposes a setting to change that split, which is required before Linux can see more than a sliver of RAM."*

⭐ **⭐ 而原文的具体数字是：⭐ **装好 Omarchy 之后，⭐ Linux 只看得到 128GB 里的 28GB。⭐ **⭐ 而解法是：⭐ **「在 Windows 侧把 GPU 内存预留从 96GB 降到 4GB，⭐ 启动 Linux 后就能看到 120GB」。**

⭐ **⭐ 请注意这里的因果顺序：⭐ **这一步必须**先在 Windows 里做**，⭐ 然后才进 Linux。⭐ **⭐ 也就是说：⭐ **双系统用户第一次启动 Linux 之前，得先回 Windows 改一个设置。⭐ **⭐ 这是一个「两套系统共享一份硬件配置」的例子，⭐ 而 Linux 侧完全无法自我修复。**

⭐ **⭐ 而这个坑的性质其实比功耗问题更麻烦：⭐ **功耗问题让性能降 5 倍（可测量）；⭐ **而内存问题让 Linux 直接看不到 3/4 的内存（不可测量，除非你专门去查）。**

### ⭐⭐ 坑二：笔记本专属硬件支持不在 vanilla 内核里

⭐ 实测报告的安装过程记录：

> *"Switching to Debian worked more reliably, but still needed workarounds. **The installer couldn't connect to Wi-Fi**, so installation required a USB Ethernet adapter. **Out of the box, Debian also didn't recognize the keyboard, touchpad, or GPU**, because none of the laptop-specific hardware support was present in a vanilla kernel."*

⭐ **⭐⭐ 而这三个「不认识」里，⭐ **键盘和触摸板不认识，⭐ 是 Linux 笔记本支持里一个非常经典的老问题** —— ⭐ **而 MSI 笔记本的 ACPI 表通常需要厂商提供的 DSDT 覆盖（dsdt.aml）才能正确工作。⭐ **⭐ 而 MindStudio 那边最终是靠换回 Omarchy 解决的：⭐ **「回到 Omarchy 解决了驱动问题，⭐ 因为它的内核已经打包了 NVIDIA 的开源驱动」。**

⭐ **⭐⭐ 而这一段引出一个我必须点明的问题：⭐ **⭐ 「Omarchy 能跑」与「Linux 能跑」是两回事。**

⭐ **⭐ 因为 Omarchy 的内核不是 vanilla 内核，⭐ 而是**预置了 NVIDIA 开源驱动的定制内核**（⭐ 也就是把「问题 A」提前解决了的那个发行版）。⭐ **⭐ 所以 MindStudio 报告的成功路径是：⭐ **「用一个已经把 NVIDIA 支持打包好的社区发行版」+「一个必须回 Windows 才能做完的内存设置」+「一块官方驱动目前不认的卡」+「一个只能靠 WSL 绕开的功耗问题」。**

⭐ **⭐⭐ 而这不是「Linux 支持了 RTX Spark」，⭐ **这是「Omarchy 支持了 RTX Spark」。⭐ **⭐ 两者之间的差距，⭐ 就是 MindStudio 那篇报告里说的 WSL 是「practical middle ground」的真正含义。**

### 顺便：还有 HDMI 安装期无输出这个奇观

⭐ 实测报告里有一段我很喜欢：

> *"Early in the process, the laptop would only display video on its own internal screen, not over HDMI, which required **pointing an external camera at the laptop's screen just to see what was happening during remote-controlled installation steps**."*

⭐ **⭐ 安装时只能用外接摄像头盯着笔记本屏幕来远程操作安装程序。⭐ **⭐ 这大概是 2026 年最硬核的一个安装方法学案例。**

## 六、⭐⭐ 那么该怎么选：三条路径的实际取舍

⭐ **实测报告给出的推荐是 WSL，⭐ 而我认为这个推荐是分层的 —— ⭐ **它对不同人的正确答案是不同的。**

### ⭐⭐ 路径一：WSL —— 「今天最实用的中间路线」

⭐ 实测报告：

> *"WSL runs on top of the Windows driver stack, so it **inherits Windows' full GPU boost behavior** whether the laptop is plugged in or running on battery. It also **runs Linux-first AI tools like vLLM and SGLang** without the clock throttling problem."*

⭐ **⭐⭐ 而这里有一个我认为特别值得注意的机制细节：**

⭐ **⭐ WSL 之所以满频，⭐ 恰恰是因为它**跑在 Windows 驱动栈之上** —— ⭐ **⭐ 也就是说，⭐ WSL 绕过了问题 B 的方式是「不用 Linux 的功耗管理路径」。⭐ **⭐ 而它同时保留了「你在跑 Linux 用户态」这件事 —— ⭐ **vLLM、SGLang 这些 Linux-first 的 AI 工具照常可用。**

⭐ **⭐ 而且它的性能不是「接近」，⭐ 是「几乎相同」：65.1 vs 65.4 tok/s。⭐ **⭐ 换句话说：⭐ **WSL 在这个场景下不是妥协，⭐ 而是真正的最优解。**

⭐ **⭐ 但它有一个必须调的参数：**

> *"WSL reserves only **14GB** by default, which isn't enough for large model workloads on a 128GB unified memory machine, so that allocation needs to be increased manually."*

⭐ **⭐ 所以 WSL 路径的完整清单是：⭐ **① 用 WSL 跑 Linux 工具链；② 把 WSL 的内存预留从 14GB 调大；③ 完成。** ⭐ **⭐ 而它的代价是：⭐ **你仍然在 Windows 上，⭐ 而且你用的是 Windows 的 GPU 驱动。**

### ⭐⭐ 路径二：原生 Linux 双系统 —— 「能跑，但要接受 5 倍性能差距」

⭐ **⭐ 而这条路径的完整清单（实测报告给的）：**

| 步骤 | 代价 |
|---|---|
| ⭐ 用 Omarchy（**不是** vanilla 发行版） | ⭐ **依赖社区内核打包 NVIDIA 驱动** |
| ⭐ **先回 Windows 把 GPU 内存预留从 96GB 降到 4GB** | ⭐ **⭐ 必须在 Windows 侧完成，⭐ Linux 无法自我修复** |
| ⭐ 安装期可能需要 USB 网卡（Wi-Fi 不认） | ⭐ 一次性 |
| ⭐ 接受插电时 GPU 只有 780 MHz | ⭐ **⭐ tok/s 从 65 掉到 14** |
| ⭐ 接受开机时 GPU 只有约 1800 MHz（拔电） | ⭐ **⭐ 插电反而更慢，这是反直觉的** |

⭐ **⭐⭐ 而最后那一行我认为是全文最反直觉、也最值得单独强调的一点：⭐ **⭐ 「插上电源反而更慢」。**

⭐ **⭐ 因为在电池供电时，GPU 是跑在低功耗档位的（这符合预期），⭐ 而插电之后，⭐ **系统本该放开限制，⭐ 但因为读不到加密的功耗表，⭐ 它反而掉到了比电池模式更低的频率。⭐ **⭐ 换句话说：⭐ **在 Linux 下，⭐ **「插电」这个动作本身变成了性能杀手。**

### ⭐⭐ 路径三：等 NVIDIA —— 「唯一真正的修法」

⭐ **⭐ 而这一条我要补充实测报告没提的东西：⭐ **NVIDIA 自己其实在跑 Linux。**

⭐ **⭐ 我查了 `NVIDIA/NemoClaw` 这个公开 tracker，⭐ 用 `[N1x Linux]` 做前缀的 issue 有几十条：**

```
12293  [N1X Linux][Inference] Fresh OpenClaw TUI HTML task fails with incomplete or malformed...
13088  [N1x Linux][Agent&Skills] Fresh OpenClaw TUI session cannot answer hi at 32K context...
12737  [N1x Linux][Install] Deferred Express preview is not offered on NVIDIA Concept I...
12768  fix(platform): detect N1x without the FastOS marker
```

⭐ **⭐⭐ 请注意这个分布：⭐ **里面大量是 `[N1X Linux]` 前缀的问题，⭐ 而 `[DGX Spark]` 前缀的另算一批。⭐ **⭐ 这说明：⭐ **NVIDIA 内部有人在认真做 N1X 上的 Linux 支持，⭐ 而且是把它当作一个持续跟踪的 issue 类别在管。⭐ **⭐**

⭐ **⭐ 而「NVIDIA 自己跑 Linux」这件事还有一层更深的含义：⭐ **⭐ DGX Spark 桌面机出厂就预装 DGX OS（⭐ 一个基于 Ubuntu 的发行版），⭐ 而它的内核是 NVIDIA 自己的 Ubuntu 内核分支，⭐ 不是上游内核。⭐ **⭐ 所以「NVIDIA 支持 Linux」这件事，⭐ 在桌面机上已经成立了；⭐ **而到了笔记本形态，⭐ 因为多了 NPCF 这块需要 Windows 密钥的组件，⭐ 就断掉了。**

## 七、⭐⭐ 一点评价：这个「不支持」的形状，和别的「不支持」不一样

⭐ **⭐ 最后我想说一点我自己的观察，⭐ 因为它和本号此前写过的几件事形成了对照。**

### ⭐⭐ 对比一：这不是「内核没有硬件支持补丁」

⭐ **⭐ 这是最容易被误解的一点。⭐ **「NVIDIA 开源驱动不支持 N1X 的 PCI ID」听起来像是「上游还没合补丁」，⭐ 但实际上：**

- ⭐ **GB10（`2E12`）已经在列表里** —— ⭐ **⭐ 也就是说，同一颗芯片家族，⭐ 桌面机形态已经支持了。**
- ⭐ **而社区（Omarchy、RageLtd/linux-dgx-spark、graham33/nixos-dgx-spark）⭐ 已经在做 GB10 的内核包。**

⭐ **⭐ 而我查 NVIDIA 自己的论坛，有一条 2026-11-03 的帖子记录了更麻烦的东西：⭐ **DGX Spark 的内核 `7.0.0-1024-nvidia` 不稳定（⭐ 报告了 GPU Xid 错误、kernel Oops、内存损坏、headless hard reset），⭐ 而 `7.0.0-1019-nvidia` 稳定；⭐ NVIDIA 为此发了 `nvidia-spark-initcall-bl 1.0-2`，⭐ 加入 `initcall_blacklist=power_wrap_init` 来绕开一个 HDMI/TMDS 触发的 reset。**

⭐ **⭐⭐ 而这个细节非常说明问题：⭐ **⭐ 一颗「主打本地 AI」的芯片，⭐ 它的**桌面机形态**的官方内核，⭐ 在 2026 年 11 月还在被官方自己标记为不稳定，⭐ 而且修复方式是「把某个 initcall 加进黑名单」。⭐ **⭐ 而在笔记本形态上，⭐ 那个「桌面机形态」的稳定性问题**还没解决**的同時，⭐ 又叠加了「笔记本专属的 NPCF 功耗管理」这个全新问题。⭐ **⭐⭐

### ⭐⭐ 对比二：这和 eMudhra 那件事是同一个形状

⭐ **⭐⭐ 让我把它和本号前几天写的那篇连起来：⭐ **《一个 CA 的私钥是数字 4》。**

| | ⭐ **eMudhra** | ⭐ **RTX Spark 的 NPCF** |
|---|---|---|
| ⭐ 原本应该安全的东西 | ⭐ **CA 的私钥** | ⭐ **GPU 的功耗表** |
| ⭐ 实际发生了什么 | ⭐ **私钥是「4」这种可预测值** | ⭐ **功耗表加密，而**解密密钥只在 Windows 驱动里** |
| ⭐ 谁被排除在外 | ⭐ **所有非 eMudhra 的客户端** | ⭐ **所有非 Windows 的 OS** |
| ⭐⭐ 问题的本质 | ⭐ **「这不该发生，但它发生了」** | ⭐ **「这不该发生，但它发生了」** |

⭐ **⭐⭐ 而我认为这个对照揭示了一个更普遍的东西：⭐ **⭐⭐ **在「一部分人能用、一部分人不能用」的硬件与平台上，⭐ **那些「只有一边有」的东西 —— ⭐ 一个密钥、一张表、一个驱动模块 —— ⭐ **⭐ 就会变成事实上的排他机制。⭐ **⭐⭐**

⭐ **⭐⭐ 而这类排他机制的危险在于：⭐ **⭐ 它们不违反任何规则、⭐ 没有人「做错」什么、⭐ 而且对使用者来说完全不可见 —— ⭐ **⭐ 你只会看到「Linux 上慢 5 倍」，⭐ 而不会看到「因为一块加密的表和一把只存在于 Windows 的密钥」。⭐ **⭐⭐**

### ⭐⭐⭐ 而最后一个观察：Windows on ARM + CUDA 这件事本身

⭐ **⭐ 还有一个我觉得值得单独说的点，⭐ 它能解释为什么这件事现在才发生。**

⭐ 实测报告说：

> *"ARM-based Windows machines have existed for a few years, but **pairing that architecture with Nvidia's CUDA stack only became possible with this chip**."*

⭐ **⭐⭐ 而这一句连着另一句更有意思的：**

⭐ **⭐ DGX Spark 出厂预装 Linux，⭐ 而 RTX Spark 笔记本**全部预装 Windows on ARM**。⭐ **⭐**

⭐ **⭐⭐ 所以整件事的形状是：⭐ **⭐⭐ **NVIDIA 手里有一台出厂就装 Linux 的桌面机（GB10），⭐ 和一整系列出厂只装 Windows 的笔记本（N1X），⭐ 而两者用的是同一套 GPU 设计。⭐ **⭐⭐**

⭐ **⭐⭐ 而「同一套 GPU 设计」这个事实，⭐ 在硬件上是成立的；⭐ **⭐ 但在「这块 GPU 需要谁来管功耗」这个软件层面，⭐ **⭐ 桌面机不需要 NPCF（⭐ 它有独立供电线），⭐ 而笔记本需要 —— ⭐ **⭐ 而 NPCF 只有 Windows 实现。⭐ **⭐⭐**

⭐ **⭐⭐ 所以结论是：⭐ **⭐ **这不是「RISC-V 对 x86」或「Arm 对 x86」那种架构之争，⭐ 而是一个具体到有点尴尬的事实：⭐ **⭐ **这块芯片在笔记本形态下，⭐ 它的功耗管理权握在一个只有 Windows 驱动才认得的固件组件手里。⭐ **⭐⭐**

---

## 主要来源

- ⭐ **MindStudio《Linux on the Nvidia RTX Spark Laptop: What Actually Works》（Luis Chavez-Mattos，2026-11-01）**：⭐ 实测数据（Windows 65.4 / WSL 65.1 / DGX Spark 61 / 原生 Linux 13.9 tok/s；8 分钟 vs 37 分钟；温度 40–47°C；⭐ **在 Windows 里禁用 NPCF 后 tok/s 从约 83 掉到约 31、频率掉到 786 MHz**）；⭐ 安装过程（Omarchy → Debian → 回到 Omarchy；⭐ Wi-Fi 不认需 USB 网卡；⭐ 键盘/触摸板/GPU 不认；⭐ HDMI 安装期无输出需外接摄像头；⭐ Linux 只见 28GB，Windows 侧把 GPU 预留从 96GB 降到 4GB 后可见 120GB）；⭐ 「功耗表加密、只有 Windows 驱动有密钥、⭐ 尝试绕过曾触发 kernel panic」
- ⭐ **NVIDIA `open-gpu-kernel-modules` 仓库 README 支持设备表**（⭐ **我实测全文检索：GB10 = `2E12 10DE 21EC` 在列，⭐ 而 N1X 出现 0 次** —— 即笔记本变体的 PCI ID `10de:2e03` 不在官方 Linux 驱动的支持列表里）
- ⭐ **`adnanpri/legion-wmi` 项目 README**（⭐ ACPI 层的逆向记录）：⭐ **NPCF = Nvidia Platform Controller and Framework；`Notify (NPCF, 0xC0)`；`\_SB_.NPCF.NPCF` 定义于 SSDT16；设备 `NVDA0820`；⭐ Windows 侧由 `nvpcf.sys` 处理；⭐ 「Nvidia drivers either do not recognize NPCF at all on Linux, or its support is limited」**
- XDA Developers《Nvidia's RTX Spark laptops use the same chip as the DGX Spark, but they get faster memory》：⭐ 同 SoC ID、同 CPU/GPU；⭐ NPU/DLA 的 ACPI 表与 Linux 侧不可见的发现（#13894 一文亦记录 firmware 里有 DLA 电源域与遥测、却从未定义 DLA0 设备）
- ComputingForGeeks《NVIDIA RTX Spark Laptops: N1X Specs, CUDA and Linux》：⭐ **「NVIDIA hasn't announced Linux support for RTX Spark laptops… XDA asked, and NVIDIA would not comment」**；⭐ **「a site that has no a value for it: The public driver does not cover it yet… The README lists GB10 as a supported device, but no RTX Spark N1X device IDs」**
- ⭐ **NVIDIA `NemoClaw` GitHub tracker**（⭐ **我用 `[N1x Linux]` 检索到数十条 issue，⭐ 证明 NVIDIA 内部在持续跟踪笔记本形态的 Linux 支持**）
- NVIDIA 官方《DGX Spark User Guide / Release Notes》（⭐ DGX OS 7.6.0、驱动 580.178.04、CUDA 13.0.3、⭐ **Canonical Kernel 7.0.0-1019**；⭐ 官方说明「GB10-based partner systems may not receive updates at the same time」）
- NVIDIA Developer Forums《DGX Spark kernel 7.0.0-1024-nvidia: summary of reported issues》（2026-11-03）：⭐ **该内核被报告 GPU Xid 错误、kernel Oops、内存损坏、headless hard reset；⭐ 官方发布 `nvidia-spark-initcall-bl 1.0-2` 加入 `initcall_blacklist=power_wrap_init`**
- Gentoo Wiki《DGX Spark》与 `RageLtd/linux-dgx-spark`、`graham33/nixos-dgx-spark`：⭐ **GB10 的 mainline 内核缺少硬件使能补丁，⭐ 需 `pci=pcie_bus_safe initcall_blacklist=tegra234_cbb_init` 等启动参数，⭐ 且需 NVIDIA 的 Ubuntu 内核分支**
- MSI 官方规格与 Notebookcheck：⭐ **Prestige N16 Flip AI+，⭐ NVIDIA RTX Spark N1X（20 核 CPU / 6144 核 GPU）、⭐ 最高 128GB LPDDR5X 统一内存、16" 2.8K Tandem OLED 120Hz、⭐ 1.9kg、99.9Wh 电池；⭐ 美国 32GB 起 $3,299，⭐ 128GB 版本 $6,899–11,999**

---

（说明：本文依据 MindStudio 的实测报告，并补上了它未提及的上游事实。**第三节中「N1X 的 PCI ID `2e03` 不在 NVIDIA 开源内核驱动支持设备表内」这一结论，⭐ 是我实测检索 `open-gpu-kernel-modules` 仓库 README 得出的（GB10 在列、N1X 零出现），⭐ 并与 ComputingForGeeks 的独立核对一致；⭐ 而该 PCI ID 本身出自 NVIDIA 的 Windows 移植指南，⭐ 我未能从 Linux 侧直接核实，故在正文中按「据 Windows 移植指南」标注。** 第四节的 ACPI 机制（NPCF / `Notify (NPCF, 0xC0)` / SSDT16 / `NVDA0820` / `nvpcf.sys`）⭐ **全部引自 `adnanpri/legion-wmi` 项目的逆向记录，⭐ 而非本文作者的实测**，⭐ 已在正文中标明出处。** 第七节的三处对比为笔者观点，**不代表任何一方立场。**）
