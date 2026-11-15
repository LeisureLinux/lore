---
title: "ASUS Ascent QN10：X2 Elite 迷你机的 Linux 设备树"
date: 2026-11-15
slug: asus-ascent-qn10-snapdragon-x2-elite-linux
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Phoronix《ASUS Ascent QN10 Mini PC Powered By Snapdragon X2 Elite Seeing Linux Support》（Michael Larabel，2026-11-15 06:01 AM EST；Qualcomm 工程师周末贴出 bring-up 补丁、QN10 能启动 Linux 且关键功能已起来、SoC 为 Snapdragon X2 Elite + Adreno X2 GPU、最多 32GB LPDDR5x-9600、双 SSD、最多四路 4K、体积小于 0.7 升、2026 年定价基础款 1699 美元、引 LKML 补丁系列并希望赶 Linux 7.5；文中引用补丁描述：18 核 Oryon CPU / Adreno X2-90 / Hexagon NPU、16 或 32GB LPDDR5x、两个 M.2 NVMe、Wi-Fi 7、蓝牙 6.0、2.5GbE、三个 USB-C、四个 USB-A、HDMI 由 eDP 经 PS195 转换、USB-A 挂在 GL3590 hub、以太网挂 PCIe）＋ LKML 补丁原文（Bjorn Andersson <bjorn.andersson@oss.qualcomm.com>，`[PATCH 0/3] arm64: dts: qcom: glymur: Add ASUS Ascent QN10`，Message-ID 20261113-qn10-v1-0-e09b2aa7ccbe@oss.qualcomm.com，2026-11-13 22:28 -0600 / 11-14 04:28 UTC；3 个补丁：dt-bindings 加 asus,ascent-qn10 兼容串、新增 670 行 glymur-asus-ascent-qn10.dts 并加进 Makefile、qcom_scm.c 的 qseecom allowlist 加该板以通过 uefisecapp 访问 EFI 变量；合计 4 文件 673 行插入；DTS 细节含 compatible = \"asus,ascent-qn10\", \"qcom,glymur\"、chassis-type = desktop、Parade PS185HDM eDP→HDMI 桥、PCIe6 接 RTL8125BP 2.5GbE、ADSP/CDSP remoteproc 固件路径指向 ASUSTeK/QN10、GPU/GMU 使能、gpio-reserved-ranges 标注 EC Secure / OOB UART / TPM / EC reset / Board ID；review 状态：Krzysztof Kozlowski 对 1/3 给 Acked-by，Abel Vesa 对 2/3 给 Reviewed-by 但要求把 regulator 节点移到 remoteproc_soccp 下、把 gpu/gmu 节点顺序对调，对 3/3 给 Reviewed-by；线程共 7 条消息）＋ ASUS 官方 Ascent QN10 产品页（2026-09-21；号称首款 80 TOPS NPU AI Mini PC，18 核第三代 Oryon 最高 4.7GHz、Adreno GPU、Hexagon NPU 最高 80 TOPS、板载不可升级 LPDDR5x 最高 32GB 8533MHz、双 M.2 2280 PCIe Gen4 512GB/1TB、四路 4K（1 HDMI 2.1 + 3 USB4）、7 个 USB 口、Wi-Fi 7 / 蓝牙 6.0 / 2.5G LAN、130×130×40mm、620g、<0.7L、fTPM 2.0 / Microsoft Pluton / Snapdragon Guardian、Copilot+ PC 与 Qualcomm AI Hub、面向 SOHO/SMB/创作者/边缘 AI；FAQ 明确 Windows 11 Pro 与 Copilot+ 语境）＋ Phoronix 2026-09-23《Qualcomm Talks Up Linux On Snapdragon X2 Laptops》与本工作区旧文（X2 的 Linux 早期开发者预览、Debian 13 用户态、Freedreno/Turnip 与 Hexagon NPU 仍在推进、HP/华硕承诺 2027 H1 官方支持）＋ Phoronix《Experimental Patches Get Nouveau+NVK Working On NVIDIA DGX Spark GB10》与 NVIDIA DGX Spark / ASUS Ascent GX10 官方页（用于区分同系列里 GB10 那条产品线）＋ 本工作区旧文《为了让这台 128GB 的 RTX Spark 笔记本跑 Linux…》（Arm Linux 上 ACPI 覆盖、固件与驱动落地的对照）"
original_date: 2026-11-15
original_url: "https://www.phoronix.com/news/ASUS-Ascent-QN10-Linux"
description: "解读高通工程师为 ASUS Ascent QN10 提交的 Linux 启用补丁。先纠清产品线：QN10 是 Snapdragon X2 Elite（Glymur）迷你机，不是同系列 Ascent GX10 / NVIDIA GB10 那条 DGX Spark 线；华硕官方页把它定位为 Windows 11 Copilot+ 的 80 TOPS NPU 迷你机。补丁本身是 Bjorn Andersson 的 3 个 patch / 673 行插入：加 dt-bindings 兼容串、新增 670 行设备树并在 Makefile 里启用 dtb、把该板加进 qseecom allowlist 以经 uefisecapp 访问 EFI 变量。设备树把板级接线写得很实：eDP 经 Parade PS185HDM 转 HDMI、四个 USB-A 经 GL3590 hub、2.5GbE（RTL8125BP）挂 PCIe6、Type-C 经 pmic-glink、ADSP/CDSP remoteproc 指向 QN10 专用固件路径、GPU/GMU 使能、保留 EC/TPM/Board ID 等 GPIO。文章解释为什么「能启动 Linux」主要靠设备树而非新驱动：Glymur SoC 基础支持此前已在推进，这次是把一台具体整机的引脚、桥片、电源、固件路径告诉内核；并列出仍需的前提（闭源固件、Adreno 走 Freedreno/Turnip、NPU 与官方支持时间表）。也写清状态：这是 v1 补丁、尚未合入，Phoronix 只是希望赶上 Linux 7.5；review 里 Krzysztof 给了 Acked-by、Abel Vesa 给了 Reviewed-by 但要求两处节点顺序调整。规格按出处分开：华硕写 32GB LPDDR5x-8533、Phoronix 写 9600；官网 620g / 130×130×40mm，媒体给 1699 美元起。结论：值得关注的不是「又一台 Arm 迷你机」，而是高通把 X2 Elite 的 Linux 支持从笔记本扩展到台式形态、且由 SoC 厂商亲自 upstream 板级描述；对想买来跑 Linux 的人，仍要等补丁合入、固件与 GPU/NPU 栈成熟。"
published: true
---

11 月 15 日 Phoronix 报了一条 Arm 硬件侧的小新闻：高通工程师给华硕 Ascent QN10 提交了 Linux 启用补丁，这台基于 Snapdragon X2 Elite 的迷你机现在能启动 Linux，关键功能被带了起来。

这类消息最容易写成「又一台 Arm 迷你机支持 Linux 了」。把 LKML 补丁和华硕官方页翻一遍，会发现更有意思的是「支持」到底由什么构成：这次几乎没有新驱动，主体是一份 670 行的设备树，加上两个各一行的白名单改动。

## 一、先别和 GX10 搞混

华硕 Ascent 这个名字下有两条完全不同的产品线：

| | Ascent QN10（本文） | Ascent GX10 |
|---|---|---|
| 芯片 | Qualcomm Snapdragon X2 Elite（代号 Glymur） | NVIDIA GB10 Grace Blackwell |
| 定位 | Windows 11 Copilot+ 迷你机、80 TOPS NPU | DGX Spark 级桌面 AI 超算，预装 DGX OS（基于 Ubuntu） |
| Linux 现状 | 这次刚有上游设备树补丁 | 出厂即 Linux，另有 Nouveau/NVK 实验补丁 |

所以 QN10 并非「换壳的 DGX Spark」：它是高通把 X2 Elite 从笔记本塞进 0.7 升小盒子；Linux 侧此前官方语境是 Windows 11 Pro + Copilot+，这次补丁属于厂商工程师主动补上游。

## 二、三个补丁，673 行

LKML 上这系列是 Bjorn Andersson（Qualcomm）在 11 月 13 日晚发的 `[PATCH 0/3] arm64: dts: qcom: glymur: Add ASUS Ascent QN10`，共 4 个文件、673 行插入。补丁对平台的定性是「a compact desktop computer based on the Qualcomm Snapdragon X2 Elite (Glymur) platform」：

1. `dt-bindings: arm: qcom: Add ASUS Ascent QN10` —— 在 `qcom.yaml` 里加一行 `asus,ascent-qn10` 兼容串；
2. `arm64: dts: qcom: glymur: Add ASUS Ascent QN10` —— 新增 670 行的 `glymur-asus-ascent-qn10.dts`，并在 Makefile 里挂上 dtb；
3. `firmware: qcom: Allow QSEECOM on ASUS Ascent QN10` —— 在 `qcom_scm.c` 的 qseecom allowlist 里加一行，让这台机器能经 `uefisecapp` 访问 EFI 变量。

第三条很小但很关键：UEFI 变量访问不通，系统启动、引导项、某些固件交互都会缺一块。把它写进白名单，说明补丁作者处理的不只是「屏幕亮起来」。

## 三、设备树里写的是「这台机器怎么接的线」

670 行 DTS 的价值，是把 SoC 之外的板级事实告诉内核。几个具体节点值得摘出来：

- `compatible = "asus,ascent-qn10", "qcom,glymur"`，`chassis-type = "desktop"` —— 明确是台式形态；
- HDMI 不是原生：eDP0 输出经 Parade PS185HDM 桥片转成 HDMI（补丁说明里写 PS195，DTS 里 compatible 是 `parade,ps185hdm`）；
- 四个 USB-A 挂在 GL3590 USB Hub 上，再接到某个 USB MP 端口；
- 2.5GbE 走 PCIe：DTS 注释点名 PCIe6 接 RTL8125BP 控制器；两个 M.2 NVMe 也各有 PCIe 通道描述；
- 三个 USB-C 通过 `pmic-glink` 描述 Type-C 连接器与 USB/DisplayPort 通路；
- `remoteproc_adsp` / `remoteproc_cdsp` 的 `firmware-name` 指向 `qcom/glymur/ASUSTeK/QN10/...` 专用固件，`gpu` 与 `gmu` 置为 okay；
- `gpio-reserved-ranges` 标注了 EC Secure、OOB UART、TPM、EC reset、Board ID 等被固件/安全部件占用的引脚。

换句话说，这是一次板级 bring-up，不是 SoC 移植：Glymur 平台基础、Adreno 图形栈、X2 Elite 笔记本的 DTS 此前已在推进，这次是把 QN10 这台整机的桥片、hub、网卡、电源、固件路径与保留 GPIO 补上。Phoronix 说「能启动 Linux 并把关键功能带起来」，落点就在这里。

顺带一个很内核社区的细节：这还是 v1。Krzysztof Kozlowski 对 1/3 给了 Acked-by；Abel Vesa 对 2/3 给了 Reviewed-by，但要求把一段 regulator 节点挪到 `remoteproc_soccp` 下、把 `gpu` / `gmu` 两个节点顺序对调；3/3 给了 Reviewed-by。也就是说已有评审、尚需修订，还没合入。Phoronix 也只是「希望及时赶上 Linux 7.5」，不是已排入。

## 四、规格按出处分开读

华硕官方页（2026-09-21）与补丁/Phoronix 的口径有一处对不上，照例不替它统一：

| 项 | 华硕官网 | 补丁 / Phoronix |
|---|---|---|
| 内存 | 最高 32GB LPDDR5x-8533，板载不可升级 | 16 或 32GB LPDDR5x；Phoronix 写 LPDDR5x-9600 |
| 存储 | 双 M.2 2280 PCIe Gen4，512GB / 1TB | 两个 M.2 NVMe 插槽 |
| 显示 | 1× HDMI 2.1 + 3× USB4，最多四路 4K | HDMI 输出（经 eDP 桥） |
| 网络 | Wi-Fi 7、蓝牙 6.0、2.5G LAN | 同，另注明网卡挂 PCIe |
| 体积/重量 | 130×130×40mm、620g、<0.7L | <0.7L；Phoronix 给基础款 1699 美元 |
| 定位 | 18 核 Oryon 最高 4.7GHz、Adreno GPU、Hexagon NPU 最高 80 TOPS、Copilot+ PC | 18 核 Oryon / Adreno X2-90 / Hexagon NPU |

官网全篇是 Windows 11 Pro、Copilot+、Pluton、Qualcomm AI Hub 与 OpenClaw/Hermes Agent 的语境；Linux 补丁来自高通上游，二者不是同一份承诺。

## 五、离「买回来装 Linux」还有多远

按 9 月 Snapdragon Summit 的公开口径，X2 的 Linux 还是早期开发者预览：定制内核 + Debian 13 用户态，Adreno 走 Freedreno / Turnip，Hexagon NPU 支持仍在推进，HP/华硕承诺的官方支持是 2027 上半年。放到 QN10 上，至少有几层前提：

- 补丁要按 review 修订、被 maintainer 收进树，才有主线 dtb；
- ADSP/CDSP  remoteproc 需要专有固件文件，DTS 只是写了路径；
- GPU/GMU 节点使能不等于用户态 3D/计算栈完备，Adreno X2-90 的 Mesa 支持另算；
- 80 TOPS NPU 在 Linux 下能不能用、怎么用，补丁没有回答；
- EFI 变量、USB-C DisplayPort、四屏输出、2.5GbE 这些「描述进 DTS」之后仍需实际验证。

本站 10 月写过另一台 Arm 机器跑 Linux 的实测：ACPI 覆盖、触控板补丁、签名固件一样都不能少。设备树流派少了 ACPI 那套折磨，但固件与用户态的账并没有消失。

## 六、边界

- 本文的补丁细节依据 LKML 归档（lore.kernel.org 被 Anubis 反爬挡，改用 lkml.iu.edu / openwall / gnuweeb 镜像复核）；review 结论为 2026-11-14 线程内状态，不代表最终合入结果。
- 未在 QN10 上实机启动 Linux、未验证 HDMI/四屏/2.5GbE/NPU；功能表述来自补丁说明与 Phoronix 报道。
- 8533 与 9600 的内存频率差异、1699 美元定价按各自出处标注，不替厂商裁决。
- 「官方支持 2027 H1」来自 9 月 Phoronix 对本工作的旧文转述，属峰会口径，不是这次补丁的内容。
- 同系列 GX10 / GB10 仅用于区分产品线，其 Linux 状态不并入 QN10 结论。

## 七、结论

这条新闻的分量不在硬件参数，而在谁在提交、提交了什么：Snapdragon X2 Elite 的 Linux 支持此前主要围绕笔记本，这次由高通工程师把一台 0.7 升的台式整机、连同 HDMI 桥片、USB hub、PCIe 网卡、专有固件路径与 EFI 变量白名单，一并用上游设备树描述出来。Phoronix 那句「希望赶上 Linux 7.5」听着轻，背后是 Arm 整机支持从「能跑」走向「每台机器都有人负责」。

但请把它读成 v1 补丁 + 已评审待修订，不是「QN10 已官方支持 Linux」。真要拿它当 Linux 小主机，等三件事：补丁进主线、linux-firmware 里 QN10 固件齐备、Mesa/NPU 栈跟上。到那时，这台 18 核、80 TOPS 的小盒子才谈得上从 Windows Copilot+ 机器变成一台能用 Linux 的边缘开发机。

## Sources

- Phoronix《ASUS Ascent QN10 Mini PC Powered By Snapdragon X2 Elite Seeing Linux Support》（2026-11-15）：<https://www.phoronix.com/news/ASUS-Ascent-QN10-Linux>
- LKML 补丁系列（Bjorn Andersson，2026-11-13/14）：<https://lkml.iu.edu/2611.1/21256.html> ｜ 2/3 设备树全文：<https://lists.openwall.net/linux-kernel/2026/11/14/417> ｜ 线程与 review：<https://lore-kernel.gnuweeb.org/lkml/20261113-qn10-v1-3-e09b2aa7ccbe@oss.qualcomm.com/T/>
- ASUS 官方产品页：<https://www.asus.com/displays-desktops/mini-pcs/ascent-series/asus-ascent-qn10/>
- Phoronix 9 月 X2 Linux 预览：<https://www.phoronix.com/news/Qualcomm-Talks-Up-X2-Linux> ｜ 本工作区旧文：<https://freelamp.com/articles/2026-09-23_qualcomm-snapdragon-x2-linux/>
- 产品线对照：Phoronix GB10 Nouveau/NVK <https://www.phoronix.com/news/Experiment-Nouveau-NVIDIA-GB10> ｜ ASUS Ascent GX10 <https://www.asus.com/us/networking-iot-servers/desktop-ai-supercomputer/ultra-small-ai-supercomputers/asus-ascent-gx10/>
- 本工作区对照旧文：<https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/>
