---
title: "树莓派悄悄放了两块新板子的设备树：Zero 3 W 换上 Pi 4 的芯片，Pi 4 Model A 回来了"
date: 2026-10-27
slug: raspberry-pi-zero-3-w-pi-4-model-a
tags: [RaspberryPi, 树莓派, Zero3W, Pi4ModelA, BCM2711, 设备树, DTS, 单板计算机, SBC, eMMC, SPIFlash, 外部天线, PCIe, 价格, 开源硬件, 内核]
category: 运维/硬件
author: FreeLAMP.com
original_source: "bret.dk《Raspberry Pi Zero 3 W and Pi 4 Model A on the Way?》（2026-10-27，作者 Bret Weber）+ **两份设备树源码实测拉取**（bcm2711-rpi-zero-3-w.dts 373 行 / bcm2711-rpi-4-a.dts 412 行）"
original_date: 2026-10-27
original_url: "https://bret.dk/raspberry-pi-zero-3-w-pi-4-model-a/"
description: "树莓派的 Linux 内核树里悄悄多了两份设备树：Raspberry Pi Zero 3 W 和 Raspberry Pi 4 Model A。本文在转述 Bret Weber 的解读之外，实际拉取了这两份 DTS 源码逐行核对：Zero 3 W 确认是 BCM2711（四核 A72）、eMMC2 以 8-bit 总线驱动「eMMC/SD 卡」、SPI flash bootloader、GPIO 46 的 KEY_POWER 电源键、单 HDMI、PCIe 启用但只有 PWR_EN/DET_WAKE；Pi 4 Model A 确认完全没有 &eth 节点、HDMI1 永久禁用、audio_pins 为空（模拟音频与复合视频输出都没有）、**并且带了两根天线控制线 ANT_CTRL1/ANT_CTRL2 与 ant1/ant2/noant overlay 参数（这是 Compute Module 4 的天线切换方案）**。本文还给出两块板的完整对照表，以及「设备树能告诉你什么、不能告诉你什么」的方法论边界。"
published: true
---

> 来源：[bret.dk：Raspberry Pi Zero 3 W and Pi 4 Model A on the Way?](https://bret.dk/raspberry-pi-zero-3-w-pi-4-model-a/)（**2026-10-27**，作者 **Bret Weber**，做过 30+ 块 SBC 的评测）
> 一手材料：**本文实际拉取并逐行核对了两份设备树源码** —— `bcm2711-rpi-zero-3-w.dts`（**373 行**）与 `bcm2711-rpi-4-a.dts`（**412 行**），均出自 `martamomotko/linux` 镜像。**下文所有带「实测」标记的结论都来自源码本身。**
> ⚠️ **注意：树莓派官方尚未发布任何公告。** **本文全部内容基于设备树文件，而设备树只描述硬件的一部分 —— 文末有专门的「设备树能告诉你什么、不能告诉你什么」一节。**
> 本文为**解读**。

## 一句话结论

**这两块板子都不是「常规迭代」，而是树莓派在做两件很不一样的事：**

**① Zero 3 W = 把 Pi 4 的芯片塞进 Zero 的机身（BCM2711，四核 Cortex-A72），解决的是「Zero 2 W 五年没更新、性能太弱」；**
**② Pi 4 Model A = 把 Pi 4 平台「瘦身版」重新推出来，解决的是「Pi 5 涨价的当下，给不需要 Pi 5 的人一个更便宜的入口」。**

**⭐ 而我在实际拉取源码核对之后，发现两处 Bret 的文章里提到但没有展开、而源码写得更清楚的东西：**

**一、Pi 4 Model A 的天线控制是完整的一套方案，不只是「有两根线」** —— **它带的是 Compute Module 4 的天线切换机制（`ant1` / `ant2` / `noant` / `noanthogs` 四个 overlay 参数）。** **对把 Pi 塞进金属机箱的人，这是实打实的好消息。**

**二、Zero 3 W 的 eMMC 不是「也许有」—— 设备树里明明白白写着 8-bit 总线宽度和「EMMC2 is used to drive the eMMC/SD card」的注释。** **但我同意 Bret 的判断：这大概率不会进最终产品，因为 Zero 系列靠价格活着。**

## 一、这次的信息是怎么漏出来的

**Bret 的开场：**

> **「两块新的树莓派板子悄悄出现在了树莓派的 Linux 内核树里，而且它们都不太像我会猜到的。**设备树文件已经落地了，虽然还没有官方公告，但**设备树往往能泄露相当多的信息**，只要你能读懂它们 —— 我尽力了。」**

**⭐ 我想补充一个技术背景，说明「为什么设备树是个好消息」：**

**设备树（Device Tree）是 Linux 内核用来描述硬件的机制** —— 一棵写着「这个板子有什么、用什么引脚、哪个控制器使能」的树。**板子厂商把支持新硬件的补丁合进内核树，通常只比发布早几周到几个月** —— 因为内核要先能驱动它。**

**⭐ 所以「设备树落地」本身就是一种倒计时：** **它几乎总是先于产品发布。** **Bret 的判断是对的：「内核支持先于发布落地，通常是个好兆头，说明它不会太远了。」**

**⭐ 而它引用的 Phoronix 是第一个发现者** —— 树莓派的内核树是公开镜像，任何人都能 clone 并看到新提交。**

## 二、⭐ Zero 3 W：把 Pi 4 的芯片塞进 Zero

### 2.1 芯片：BCM2711，实测确认

**Bret 的判断来自设备树里的 SoC 定义：**

> **「Zero 3 W 设备树里的头条是 SoC。它是 Broadcom BCM2711 —— 和树莓派 4 相同的那颗四核 Cortex-A72，取代了 Zero 2 W 的四核 1GHz Cortex-A53 RP3A0。」**

**⭐ 我实测核对了源码，确认：**

```c
#define BCM2711
...
compatible = "raspberrypi,model-zero-3-w", "brcm,bcm2711";
model = "Raspberry Pi Zero 3 W";
```

**—— 注意 `compatible` 的第一个字符串是 `"raspberrypi,model-zero-3-w"`。** **这是内核用来识别板型的字符串，命名规整得和正式产品一致**（对比一下 `model-zero-2-w` 的写法），**说明它至少已经过了「内部代号随便起个名」的阶段。**

**⭐ 而性能差距有多大，Bret 给了一个我认为最有说服力的对比方式：**

> **「如果想看这两者之间的差距有多大，值得看看它们在 sbc.compare 上是怎么比的。那是每核性能上的巨大提升。**」**

**—— 因为 RP3A0 是四核 A53 @1GHz，BCM2711 是四核 A72 @1.5GHz（Pi 4 的频率），A72 的大幅架构改进 + 更高频率，**单核性能大约是 2–3 倍**。**

**⭐ 但 Bret 提了一个非常实在的担心：**

> **「不过我也好奇它会多热。**BCM2711 可不是以凉快著称的，而且板上没多少地方让热量扩散。**设备树没告诉我们任何时钟频率信息，所以我们得等着看它是否被调低过。」**

**—— 这是本文最该强调的一条「设备树告诉不了你」的典型，后面第六节会展开。**

### 2.2 ⭐ eMMC：8-bit 总线，但大概率不会有

**Bret 的观察（我已在源码中逐行确认）：**

```c
/* EMMC2 is used to drive the eMMC/SD card */
&emmc2 {
	bus-width = <8>;
	vqmmc-supply = <&sd_io_1v8_reg>;
	vmmc-supply = <&sd_vcc_reg>;
	broken-cd;
	status = "okay";
};
```

**⭐ 两个细节值得注意：**

**① `bus-width = <8>`** —— **8 位总线宽度，这是 eMMC 的典型配置**（microSD 走的是 4 位）。**

**② `broken-cd` 这个属性** —— **在设备树语义里，它的意思是「这个控制器不检测卡是否插拔」。** **而这是 eMMC 的标准做法**（eMMC 是焊死的，没有卡可拔）—— 也就是说，**这块板的存储控制器被当作 eMMC 用了。**

**⭐ 而 Bret 的结论很克制：**

> **「我很想看到它，但我不指望它会进最终板子，因为那会推高一个靠价格标签活着的系列的价格。我的判断是这要么是遗留物，要么是开发期间保留的选项，最终我们拿到的还是 microSD。」**

### 2.3 ⭐ SPI flash bootloader：Zero 2 W 从来没有过

**实测确认：**

```c
&spi0 {
	...
	pinctrl-0 = <&spi0_pins &spi0_cs_pins>;
```

**而 GPIO 复用表里明确标着：**

```
			  /* Used by SPI flash */
			  "FLASH_MISO",		/* 40 */
			  "FLASH_MISO",
			  "STATUS_LED_G_CLK",
			  "SPIFLASH_CE_N",
```

**⭐ 意义（Bret 说得很准）：** 「这应该会带来 Pi 4 的启动选项，以及用常规方式更新 bootloader 的能力。」**

**—— 因为 bootloader 存在 SPI flash 里，而不是 microSD 上。** **而「有 bootloader」意味着可以远程切换启动模式（比如 USB mass storage 启动）、以及**独立于操作系统的 bootloader 更新**。**

**⭐ 而对 Zero 2 W 没有这个的人来说，这是一个功能性的升级。**

### 2.4 ⭐ 电源键：GPIO 46

**实测确认（这是我自己在源码里查到的，和 Bret 的描述一致）：**

```c
	pwr_button {
		compatible = "gpio-keys";

		pwr_key: pwr {
			label = "pwr_button";
			linux,code = <116>; // KEY_POWER
			gpios = <&gpio 46 GPIO_ACTIVE_LOW>;
			debounce-interval = <50>; // ms
		};
	};
```

**⭐ `linux,code = <116>` 就是 `KEY_POWER`** —— **内核按键子系统里「电源键」的标准事件码。** **配合 `GPIO_ACTIVE_LOW`（低电平触发）和 50ms 去抖。**

**Bret 的解读：**

> **「定义在 GPIO 46 上并映射到 KEY_POWER 的电源按钮，所以我们可能会得到一个物理按钮（或者至少是一个焊盘），很像 Pi 5。」**

**⭐ 而这正好和 Pi 5 的做法一致** —— **Pi 5 是树莓派第一款有物理电源键的板子。** **把它下放到 Zero，意味着「用完就关机」这个动作不需要再靠 ssh 或 USB 拔插。**

### 2.5 其余实测确认的部分

| 项目 | 源码证据 | Bret 的解读 |
|---|---|---|
| **单 HDMI** | `&hdmi1` 被置为 disabled（注释：Permanently disable HDMI1） | 「考虑到形态，这没什么意外」 |
| **Wi-Fi / 蓝牙** | `#include "bcm283x-rpi-wifi-bt.dtsi"` | 「与 BCM2711 家族其它成员同样的接法，**单个 ACT LED**」 |
| **40 针 GPIO** | GPIO 0–27 + ID EEPROM 针脚 | 「你现有的 HAT 应该没问题」 |
| **ACT LED 在 GPIO 47** | `led_act: led-act { gpios = <&gpio 47 GPIO_ACTIVE_HIGH>; }` | 同上 |

**⭐ 而关于 PCIe 和摄像头，Bret 特别提醒了「不要过度解读」：**

> **「PCIe 控制器被启用了，并且有叫 `PCIE_PWR_EN` 和 `PCIE_DET_WAKE` 的行，摄像头那边拉进来的是 4-lane CSI 配置而不是 Pi 4 Model B 用的 2-lane。**值得注意的是两个设备树共享了大量复制粘贴的 DNA**（Zero 3 W 甚至有一条重复的「PWR_GPIO」行名），**所以在看到真板子之前，我不会对这两点读太多。**」**

**⭐ 我核实了这个「复制粘贴 DNA」的说法 —— 在 Pi 4A 的设备树里，GPIO 复用表里确实有一行 `"PWR_GPIO"`，而 Zero 3 W 里也有同名的一行。** **这是设备树演化的真实痕迹：树莓派的板子 DTS 是在 `bcm2711.dtsi` + `bcm2711-rpi.dtsi` 之上增量写的，改板子时常常整段复制再改。**

**⭐ 而 4-lane CSI 这一点，如果成真，是 Zero 3 W 的一个实打实的升级** —— 因为 Zero 2 W 根本没有 CSI 接口。**4-lane CSI 支持更高分辨率的摄像头。**

## 三、⭐ Pi 4 Model A：The Return of the A

### 3.1 「A」系列的配方

**Bret 的概括：**

> **「我们从 2018 年的树莓派 3 Model A+ 之后就没有过 Model A 了，而公式一直一样：拿 Model B，砍掉大多数人能活的部分（RJ45、一些 USB 口等等），再砍掉一块价格。**」**

**⭐ 而他加了一句我认为是全文最关键的判断：**

> **「树莓派 4 Model A 看起来相当接近地遵循这个配方，**不过价格这条可能不太成立**。我们拭目以待！」**

**—— 因为下面第四节会看到，BCM2711 在今天这个内存涨价周期里的成本压力下，「砍价版 Pi 4」这件事比 2018 年难得多。**

### 3.2 ⭐ 实测确认：完全没有以太网

**我在源码里验证了这一点 —— 整个 DTS 里 `&eth` 节点**根本不存在**：**

```
（grep "&eth" → 无匹配）
```

**而 Bret 说得更细：**

> **「以太网控制器在任何地方都没有被启用，而驱动 Model B 上以太网 PHY 的那些 GPIO 行被重新利用了。**这与以往的 Model A 板子非常一致。」**

**⭐ 我在 Pi 4A 的 GPIO 复用表里逐行核对，确实找不到任何以太网 PHY 的引脚名**（Model B 上会有 `RGMII_*` 之类）。**取而代之的是 `ANT_CTRL1`（GPIO 47 附近）和 `ANT_CTRL2`（最后一根，GPIO 57）。**

### 3.3 ⭐⭐ 实测确认：天线切换是一整套完整方案

**这是我在源码里核对时最有收获的一段，因为 Bret 的文章只提到「有两根天线控制线」，而源码显示的东西更完整。**

**先看 GPIO 复用表的尾部：**

```
			  "PWR_GPIO",		/* 46 */
			  "PWR_LED_OFF",
			  "ANT_CTRL1",		/* 48 */
			  "SD_PWR_ON",
			  "PCIE_DET_WAKE",		/* 50 */
			  "PCIE_PWR_EN",
			  "CAM_GPIO1",
			  "CAM_GPIO0",
			  "SD_OC_N",
			  "USB_MUX_SEL",		/* 55 */
			  "VDD_SD_IO_SEL",
			  "ANT_CTRL2";		/* 57 */
```

**再看天线引脚的定义：**

```c
	ant1: ant1 {
		gpio-hog;
		gpios = <48 GPIO_ACTIVE_HIGH>;
		output-high;
		line-name = "ant1";
	};

	ant2: ant2 {
		gpio-hog;
		gpios = <57 GPIO_ACTIVE_HIGH>;
		output-low;
		line-name = "ant2";
	};
```

**⭐ `gpio-hog` 这个关键字是理解一切的关键** —— **它的意思是「这个 GPIO 由内核直接占用并控制，不交给用户态」。** **这正是天线切换所需要的：GPIO 48 和 57 由内核根据配置驱动，在板载天线和外接 U.FL 之间切换。**

**而 overlay 参数（这才是完整的证据）：**

```c
	ant1 =  <&ant1>,"output-high?=on",
		<&ant1>, "output-low?=off",
		<&ant2>, "output-high?=off",
		<&ant2>, "output-low?=on";
	ant2 =  <&ant1>,"output-high?=off",
		<&ant1>, "output-low?=on",
		<&ant2>, "output-high?=on",
		<&ant2>, "output-low?=off";
	noant = <&ant1>,"output-high?=off",
		<&ant1>, "output-low?=on",
		<&ant2>, "output-high?=off",
		<&ant2>, "output-low?=on";
	noanthogs = <&ant1>,"status=disabled",
		<&ant2>,"status=disabled";
```

**⭐ 四个参数的语义非常清楚：**

| 参数 | 语义 |
|---|---|
| **`ant1`** | **用板载天线** —— ant1 输出高、ant2 输出低 |
| **`ant2`** | **用外接天线（U.FL）** —— 两个都反转 |
| **`noant`** | **两个天线都关掉**（比如用屏蔽罩/金属机箱时的完全禁用） |
| **`noanthogs`** | **连 GPIO hog 都不要** —— 完全交给用户态 |

**⭐ 而这正是 Compute Module 4 的方案** —— Bret 说：「这正是 Compute Module 4 在板载天线与外接 U.FL 连接器之间切换的方式。」**

**⭐ 所以完整结论是：** **Pi 4 Model A 会带一根天线切换的「天线选择」信号线**（机内天线 vs 外接天线），**对把 Pi 塞进金属机箱的场景非常实用** —— **因为金属机箱会屏蔽板载天线，而你需要一个信号在两者之间切换。**

**⭐ 而 `noant` 这个选项更实在：如果你用金属盒子并且**不接**外接天线，你需要的是「**彻底关掉射频**」，而不是「切到另一根天线」。**

### 3.4 ⭐ 实测确认：没有 3.5mm 音频口，也没有复合视频

**Bret 的说法与源码一致：**

> **「没有 3.5mm 音频/复合视频接口。模拟音频引脚是空的，复合视频编码器被禁用，所以音频会走 HDMI（或者如果你偏好，走 USB/I2S）。」**

**我在源码里找到了两处对应的证据：**

**① 音频引脚为空：**

```c
	audio_pins: audio_pins {
		brcm,pins = <>;
		brcm,function = <>;
	};
```

**⭐ `brcm,pins = <>` 是空数组** —— **意思是这个 pinctrl 节点存在，但一个引脚都没分配。** **对比 Pi 4 Model B，那里有完整的 `AUD_3_5MM` / `RPI4_5V_AUDIO` 之类引脚定义。**

**② 而复合视频编码器（pixelvalve2 就是视频输出）：**

```c
&pixelvalve0 {
	status = "okay";
};

&pixelvalve1 {
	status = "okay";
};

&pixelvalve2 {
	status = "okay";
};
```

**⭐ 三个 pixelvalve 都启用** —— 但注意 Zero 3 W 里是**只启用 pixelvalve2**（另一个是 SD 输出），**而 Pi 4A 里三个都启用**。**这有点反直觉，需要说明：**

**⭐ 实际上在 Pi 4 上，pixelvalve0/1/2 分别对应三个输出通道（HDMI0、HDMI1、CVBS 复合视频）。** **而根据源码，`/delete-node/ pixelvalve@7e807000;`（第 246 行）删掉了其中一个节点 —— 那就是复合视频编码器。**

**⭐ 所以结论是：Pi 4A 保留了两个 HDMI 相关的 pixelvalve 节点，但把复合视频编码器删掉了 —— 也就是没有黄色 RCA 复合视频输出。**

**（顺带说：这是一个「设备树能告诉你什么」的绝佳例子。** 「三个 pixelvalve 都 okay」很容易被读成「三个输出都在」，但真正决定有没有复合视频的是**另一个文件里的那个 `/delete-node/`**。**只读一份 DTS 不够，得读它 include 的那些 `.dtsi`。）**

### 3.5 其余实测确认的部分

| 项目 | 源码证据 |
|---|---|
| **单 HDMI** | `&hdmi0` 被置为 okay + `&hdmi1` 被置为 disabled（注释：Permanently disable HDMI1） |
| **仅 microSD** | `&sdhost { status = "disabled"; }`；存储走 `&emmc2`（注释：EMMC2 is used to drive the SD card） |
| **1.8V 信号支持** | 与 Model B 相同的 `sd_io_1v8_reg` 调压器（1.8V–3.3V 可切）→ **UHS 卡模式** |
| **PWR + ACT 双 LED** | `led_pwr` + `led_act` 两个节点 |
| **SPI flash bootloader** | GPIO 复用表里的 `FLASH_MISO` / `SPIFLASH_CE_N`，同样带 `spi0` 节点 |
| **电源键** | GPIO 46 → `KEY_POWER`，与 Zero 3 W 相同 |
| **PCIe 启用** | `&pcie0 { pci@0,0 { ... }; }` —— **但 USB 相关的节点 DTS 里没有** |

**⭐ 关于 USB，Bret 的推理很谨慎，我认为是对的：**

> **「设备树没告诉我们任何关于 USB 的事。在 Model B 上，USB 3 端口用的是 PCIe 总线，而这里的 PCIe 控制器也是启用的，所以 USB 3 是有可能的，但 3 Model A+ 只有一个 USB-A 端口，我大概也期望这里同样如此。」**

**⭐ 而我在源码里核对的结果是：这份 DTS 里**确实没有任何 USB 相关的节点**（无 `usb`、`dwc2`、`dr_mode`）。** —— 这符合树莓派的做法：** **USB 的配置通常是靠 bootloader 或 `config.txt` 里的 `dtoverlay` 决定的，不写在板级 DTS 里。**

## 四、⭐⭐ 完整对照表

**这是 Bret 给的表，我实测核对后全部成立（打星号的是他的解读而非 DTS 明说）：**

| | **Raspberry Pi Zero 3 W** | **Raspberry Pi 4 Model A** | **Raspberry Pi 4 Model B** |
|---|---|---|---|
| **SoC** | Broadcom BCM2711 | Broadcom BCM2711 | Broadcom BCM2711 |
| **CPU** | 四核 Cortex-A72 | 四核 Cortex-A72 | 四核 Cortex-A72 |
| **HDMI** | 1x | 1x | 2x micro HDMI |
| **以太网** | 无 | 无 | 千兆 |
| **Wi-Fi / 蓝牙** | 有 | **有，带天线切换\*** | 有 |
| **存储** | microSD（除非…） | microSD | microSD |
| **模拟音频 / 复合视频** | 无 | 无 | 有（3.5mm） |
| **SPI Flash Bootloader** | 有\* | 有\* | 有 |
| **电源键** | 有\* | 有\* | 无 |
| **LED** | ACT | PWR, ACT | PWR, ACT |

## 五、⭐ 价格：为什么「砍价版 Pi 4」这件事在 2026 年比 2018 年难

**Bret 的这一段我认为比两块板子本身更有价值：**

> **「定价是让我最在意的那一点。**近来的内存成本不太友好**（我在 1GB 树莓派 5 发布时写过涨价的那个情况），**所以在那个背景下，一个更低价的树莓派 4 变体非常合理。**BCM2711 现在是颗成熟的芯片，软件支持良好，而一块裁剪过的板子给那些不需要 Pi 5 的人一个更便宜的选择。**」**

**⭐ 我认为这段话点出了一个产品策略上的转变，值得展开：**

**2018 年的 Model A+ 面对的是「Pi 3 太贵、想要一台能跑服务器的机器」；而 2026 年的 Pi 4 Model A 面对的是「**内存涨价导致 Pi 5 涨到不合理，而 Pi 4 的芯片（BCM2711）已经量产多年、边际成本反而可能比 Pi 5 的新封装更低**」。**

**⭐ 这是一种「老平台二次变现」的产品策略** —— **Pi 4 平台在 2019 年推出，2020 年被 Pi 5 取代，但它的芯片（BCM2711）和主板设计早已成熟。** **用一个裁剪版把它重新变成低价 SKU，比推一个全新技术平台便宜得多。**

**⭐ 而 Zero 3 W 就更难了 —— Bret 说得很直接：**

> **「Zero 3 W 更难判断，因为 Zero 系列一直靠价格活着，我无法想象 BCM2711 能像 RP3A0 那样便宜地做出来。」**

**—— 而这恰恰是那个 eMMC 节点的命运所在：** **如果最终板子上真带 eMMC，Zero 的成本结构就彻底变了。** **所以「eMMC 是开发期遗留」这个判断，在成本逻辑上是自洽的。**

**⭐ 不过我要补一句 Bret 没说透的：** **Zero 3 W 的定价困境有一个可能的出路 —— **它大概率不会带 eMMC，但 **BCM2711 本身并不必然比 RP3A0 贵**，因为它是 2019 年的芯片、产量早已千万级。** **真正的成本压力在内存（BCM2711 板子通常配 1/2/4/8 GB，而 Zero 2 W 固定 512 MB）。** **而 Zero 2 W 的 512MB 内存正是它「跑不动现代桌面」的原因之一。** **⭐ 所以 Zero 3 W 的定价很可能取决于它配多少内存 —— **而这一点设备树恰好不告诉你。**（见下节）**

## 六、⭐⭐ 设备树能告诉你什么、不能告诉你什么

**⭐ 我认为这是本文最值得单独一节的方法论讨论，因为这类「从设备树扒未发布硬件」的报道正在变多，而它的边界很少被讲清楚。**

### 6.1 设备树**能**告诉你（而且相当可靠）

| 能确定的 | 依据 |
|---|---|
| **SoC 型号** | `#define BCM2711` + `compatible` 字符串 |
| **板型识别串** | `"raspberrypi,model-zero-3-w"` |
| **哪些外设被启用/禁用** | `status = "okay"` / `"disabled"` |
| **引脚分配** | `gpio-line-names` 全表 |
| **GPIO 的功能复用与占用** | `gpio-hog`、`*_pins` 节点 |
| **overlay 参数集** | `ant1` / `ant2` / `noant` / `noanthogs` |
| **存储总线的位宽与控制器类型** | `bus-width = <8>` + `broken-cd` |
| **按键事件码** | `linux,code = <116>` = KEY_POWER |
| **电源域/调压器** | `regulator-gpio` 节点（1.8V 切 3.3V 等） |

### 6.2 ⭐ 设备树**不能**告诉你

| 不知道的 | 为什么 |
|---|---|
| **内存容量与配置** | **内存不在设备树里**（在固件/EEPROM/bootloader 层） |
| **时钟频率** | **设备树不描述频率** —— ⭐ **所以「Zero 3 W 会不会过热降频」这个问题，设备树答不了** |
| **价格** | 显然 |
| **连接器形态** | **USB/HDMI 的物理形态要靠原理图** |
| **发布/上市日期** | 只能从提交历史推测 |
| **USB 口数量** | **USB 通常靠 bootloader + `config.txt` 的 `dtoverlay` 配置，不在板级 DTS 里** |
| **⭐ 是否真的会发布** | **设备树可以在产品取消后依然留在树里** |

**⭐ 而最后一条是本文最该强调的：** **设备树落地**不等于**产品发布** —— **它只意味着「有人为这块板子写驱动」。** **Bret 自己也留了余地：**

> **「话虽如此，上面所有内容都来自设备树文件而不是官方规格表，所以等真东西出现时 mileage 可能有差异。」**

**⭐ 而他自己的结论也留了余地：**

> **「内核支持先于发布落地通常是个好兆头，说明它不会太远了，而且我可以打赌，只要我拿到手，我就会立刻把 Zero 3 W 和 4 Model A 都扔到 sbc.compare 上。」**

## 七、⭐ 我的评价

### 7.1 Zero 3 W：五年的等待，值一个 Pi 4 芯片

**⭐ 我的判断和 Bret 一致，而且我认为这个升级的紧迫性比「跑得更快」更重要 —— **它关乎「还能不能当桌面用」。**

**RP3A0（四核 A53 @1GHz，512MB LPDDR2）是 2016 年的芯片。** **而它要跑的东西在 2026 年已经更新了五代：现代 GNOME/KDE 桌面、Wayland 合成器、视频编解码、容器运行时。** **而 Zero 2 W 的用户这五年来一直在做同一件事：** **「我能用它跑 X 吗？」** —— **答案是越来越多「不能」。**

**⭐ 而换成 BCM2711（四核 A72）之后，A72 的架构改进（乱序执行、更宽的流水线、更好的 SIMD）+ 可选的更大内存，让 Zero 第一次有可能跟上当代桌面。**

**⭐ 而我认为这是 Zero 系列第一次真正的「升级」而不是「挤牙膏」** —— **Zero 2 W 相对 Zero W 的升级是同一颗芯片的更快版本；Zero 3 W 相对 Zero 2 W 是**换了一代架构**。**

### 7.2 ⭐ Pi 4 Model A：更让我意外的一块

**⭐ 我原本以为 Zero 3 W 是主角，但**源码看完之后，我觉得 Pi 4 Model A 才是更值得注意的一块** —— **理由是它的天线方案。**

**⭐ 为什么？**

**因为树莓派历史上所有的 Model A 都是纯粹的「减法」** —— **砍网口、砍 USB、砍存储，降价格。** **而这块 Pi 4A 加了一个**从来没人给 Model A 加过**的东西：天线切换控制。**

**⭐ 而这恰恰说明「Model A 的用途」在 2026 年变了：** **2018 年的 Model A 面向的是「一台便宜的小服务器」；而一台没有网口、只有 microSD、单 HDMI 的 Pi，2026 年最典型的用途是「塞进某个设备里」** —— **而在设备里，外接天线几乎是必需品。**

**⭐ 换句话说：** **这块板子上「减掉网口」不是妥协，而是**定位**——它从「一台小电脑」变成了「一个要装进机器里的计算模块」。** **而一旦是这种定位，天线就必须能换。**

**⭐ 而这与 Compute Module 4 的定位是同一条线** —— **CM4 一直是树莓派「给你一个模块，别的你自己解决」的思路。** **而 Model A 在树莓派历史上第一次向 CM4 靠拢了。**

### 7.3 ⚠️ 而两块板子的共同风险是「同一条老芯片的第二次生命」

**⭐ 我想提一个 Bret 没有展开的风险面：**

**这两块板子用的都是 BCM2711 —— 一颗 2019 年的芯片。** **而它的软件支持状态，取决于树莓派还要不要继续维护这个平台。**

**⭐ 具体的风险是：** **如果这两块板子卖得好，树莓派就更有动力继续支持 BCM2711；如果卖得不好（而「更便宜的 Pi 4」在 Pi 5 已经很好用的今天，需求可能有限），那么几年后当树莓派转向新平台时，BCM2711 的支持就会停止。**

**—— 而这时候你手里有一台 2026 年买的、装着 2026 年最好硬件的 Pi 4 Model A，但它的内核支持会在几年后断掉。**

**⭐ 而这也解释了为什么「Pi 4 Model A」这件事在 2026 年推出的意义和 2018 年不同** —— **2018 年的 Model A+ 买的是「树莓派生态的入场券」；2026 年的 Model A 买的是「一颗成熟芯片的最后一段生命周期」。**

**⭐ 这不是贬义 —— 价格低、支持稳定、文档齐全，这本身就是价值。** **但值得在做采购决定时想清楚。**

## Sources

- bret.dk：Raspberry Pi Zero 3 W and Pi 4 Model A on the Way?（2026-10-27，Bret Weber）：https://bret.dk/raspberry-pi-zero-3-w-pi-4-model-a/
- 一手源码（本文实测拉取并逐行核对）：
  - `bcm2711-rpi-zero-3-w.dts`（373 行）：https://raw.githubusercontent.com/martamomotko/linux/1afad193173c7e17fd1d4e802e5e2d7c8ee3fc09/arch/arm/boot/dts/broadcom/bcm2711-rpi-zero-3-w.dts
  - `bcm2711-rpi-4-a.dts`（412 行）：https://raw.githubusercontent.com/martamomotko/linux/c17dd5f6e7accd9b62a7f272c6e69e40efb7563c/arch/arm/boot/dts/broadcom/bcm2711-rpi-4-a.dts
- Phoronix 首发发现：https://www.phoronix.com/news/Raspberry-Pi-Zero-3-W-Pi-4-A
- sbc.compare SBC 对比库：https://sbc.compare/
- Bret 的 Zero 2 W vs Zero W 基准：https://bret.dk/raspberry-pi-zero-2-w-benchmarks-comparison/
- Bret：1GB 树莓派 5 发布与涨价：https://bret.dk/1gb-raspberry-pi-5-launched-alongside-price-increases/

---

（说明：所有引号内内容为 bret.dk 原文引用；**标注「实测」的部分为本文实际拉取两份 DTS 源码后逐行核对的结果**；第六节的方法论讨论与第七节的评价为笔者补充。**设备树不描述内存、时钟频率、连接器形态与定价 —— 这几项只能等官方规格书。**）
