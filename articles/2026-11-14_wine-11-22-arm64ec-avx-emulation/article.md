---
title: "Wine 11.22：给 ARM64EC 补上 AVX，12.0 前的倒数第二个开发版"
date: 2026-11-14
slug: wine-11-22-arm64ec-avx-emulation
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：WineHQ 官方新闻《Wine 11.22 Released》（2026-11-13，六项 What's new：Unicode CLDR 49 locale 数据、ARM64 上 x86 模拟路径的 AVX 支持、地址空间随机化、Tahoma 字形度量改进、MSXML 中 DTD 校验重写、常规 bug 修复）＋ Wine GitLab release wine-11.22（Phoronix 与 Linuxiac 均引其为详情来源；GitLab 页面受 Anubis 反爬保护，本文未逐条读取 34 个 Bugzilla 条目）＋ Phoronix《Wine 11.22 Introduces x86 AVX Emulation On ARM64》（Michael Larabel，2026-11-13 08:35 PM EST；双周开发版、逼近 12.0 稳定版准备、34 个已知 bug 修复、Logos Bible Software / Guild Wars 2 / Star Citizen 等、引用 MR 12610「initial NTDLL for AVX on ARM64EC」与 MR 12683「XState handling」）＋ Linuxiac《Wine 11.22 Adds AVX Support on ARM64, Fixes 34 Bugs》（2026-11-13，Vulkan D24X8 深度格式、RGB565 swapchain 回退、Black Mirror II/III、Notepad++ 菜单栏、WinSCP About 对话框回归、ECDSA 密钥导入等具体修复）＋ WineHQ 新闻 RSS 与 WineHQ 11.21/11.20/11.19/11.18/11.17/11.16/11.15/11.14 官方发布摘要（双周节奏与近期主线：WoW64 OpenGL、Voice Capture DSP、Relay debugging for ARM64EC、CDROM 移到 Mount Manager、Wayland Vulkan 色彩管理、DNS 查询缓存、Unicode 18、Mono 11.3.0 含 ARM64 支持、VA-API 硬件解码）＋ Phoronix 近期 Wine 系列标题（11.21 Better WoW64 OpenGL Performance、Mesa MESA_map_buffer_client_pointer、11.19 Wayland Color Management For Vulkan、Wine-Staging 11.18）＋ Wine 项目 GitLab releases 页（11.x 源码 tar.xz 与 changes since 格式）"
original_date: 2026-11-13
original_url: "https://www.phoronix.com/news/Wine-11.22-Released"
description: "解读 Wine 11.22。这是 11.x 双周开发版序列中的一版，官方六项更新里最值得看的是「ARM64 上的 x86 模拟路径支持 AVX」：配合此前合入的 NTDLL AVX/ARM64EC 基础与 XState 处理改动，让越来越多默认假设 CPU 有 AVX 的现代 Windows 程序，在 ARM64EC 构建里不再直接失败。文章把这条放进 Wine 2026 年的 ARM64EC/WoW64 主线里看：11.15 Mono 引擎加 ARM64、11.16 VA-API 硬解与 ARM64EC 异常处理、11.20 ARM64EC relay debugging、11.21 WoW64 OpenGL 性能，都指向「在非 x86 主机上跑 x86 Windows 程序」这条链路。其余更新逐项说明：locale 数据升到 Unicode CLDR 49、加入地址空间随机化、Tahoma 字形度量改进、MSXML 的 DTD 校验重写。修复方面按官方与媒体口径写 34 个已知问题，覆盖 Logos Bible Software、Guild Wars 2、Star Citizen 以及 Vulkan 渲染器、Notepad++、WinSCP 等；同时标明 GitLab release 页受反爬保护，本文未逐条核对 Bugzilla ID。文章也写清版本节奏：11.x 每两周一个开发版，社区普遍预期 11 月底到 12 月转入 12.0 RC、2027 年初出 12.0 稳定版，但这属于节奏推断而非官方公告；WineHQ 只写「development release」。结论：单看版本号是常规小更新，放在架构线上是 ARM64EC 兼容性拼图又补了一块。"
published: true
---

>
> 一个双周开发版通常没什么可写的。Wine 11.22 值得停一下，是因为六项更新里有一项落在架构链路上，而非单纯修 bug。

11 月 13 日，WineHQ 发布 Wine 11.22。官方说明只有六行：locale 数据更新到 Unicode CLDR 49、ARM64 上 x86 模拟路径支持 AVX、加入地址空间随机化、改进 Tahoma 字形度量、MSXML 里重写 DTD 校验，以及常规 bug 修复。Phoronix 补了一句节奏判断：这是最新的双周开发版，已经相当接近 Wine 12.0 稳定版的准备工作。

## 一、重点：ARM64EC 上的 AVX

标题里那句「ARM64 上 x86 模拟路径的 AVX 支持」，得拆开才看得出分量。

Wine 在 ARM64 主机上跑 x86 Windows 程序有两条相关技术：ARM64EC（Windows 定义的一种「模拟兼容」ABI，允许同一进程里混合原生 ARM64 代码与 x86 代码）与 WoW64（32 位 x86 程序跑在 64 位 Windows 环境里的兼容层，Wine 把它扩展成新 WoW64 模式）。AVX 是 x86 的 256 位向量指令集，问题在于越来越多现代 Windows 软件直接假设 CPU 支持它：启动时不检测、或检测结果只分「有 / 没有」，没有就崩、就退、就直接报错。

以前在 ARM64 上模拟 x86，遇到这类指令往往没有干净答案。11.22 把 AVX 接进模拟路径，Phoronix 指出它承接了此前两组改动：

- MR 12610：NTDLL 里为 ARM64EC 加 AVX 基础；
- MR 12683：XState 处理（AVX 的 YMM 寄存器状态属于 XState，上下文切换、异常展开都要能保存恢复，不然「支持指令」只是半截）。

换句话说，这次把寄存器状态的生命周期一并补齐了，工作量远不止几条指令翻译。官方措辞很克制，只写「AVX support in x86 emulation on ARM64」；「让现代 Windows 软件不再因假设 AVX 而失败」是 Phoronix 的解读，本文按出处分开标注。

## 二、放进 2026 年的主线看

把 WineHQ 最近几个版本的官方摘要排在一起，方向就很清楚：

| 版本 | 官方列出的相关项 |
|---|---|
| 11.14 | FreeBSD 上的新 WoW64 模式 |
| 11.15 | Mono 引擎升到 11.3.0，含 ARM64 支持 |
| 11.16 | VA-API 硬件视频解码；ARM64EC 异常处理改进 |
| 11.17 | 若干 DirectSound 格式转换与 BCrypt 算法 |
| 11.18 | 继续搭建 NTOSKRNL 实现 |
| 11.19 | Wayland 下 Vulkan 色彩管理协议、DNS 查询缓存、Unicode 18 |
| 11.20 | ARM64EC 的 relay debugging、XML 校验改进、CDROM 移到 Mount Manager |
| 11.21 | WoW64 OpenGL 性能（`map_buffer_client_pointer` 扩展）、Voice Capture DSP 初版 |
| 11.22 | ARM64EC/x86 模拟的 AVX、地址空间随机化、CLDR 49 |

半年下来，ARM64EC、WoW64、异常展开、调试、图形性能、指令集状态，一块块往里填。11.22 的 AVX 属于「拼图又补一块」，而不是突然冒出来的孤立特性。

顺带一提，Phoronix 同期还报过 Wine 合入 Mesa 的 `MESA_map_buffer_client_pointer` 来改善 32 位 OpenGL 性能 —— 这类改动的共同点是：兼容层的瓶颈往往不在「能不能翻译 API」，而在跨架构时那些没人愿意重写的状态与内存路径。

## 三、另外五项更新

- Unicode CLDR 49：locale 数据升级。影响的是日期、货币、排序、语言标签这类本地化行为，不显眼，但对非英语环境很实在。
- 地址空间随机化：让 Wine 进程的内存布局更不可预测，属于加固类改动。官方没有给出实现范围与开关细节，本文不替它推断等价于 ASLR 的完整程度。
- Tahoma 字形度量改进：Tahoma 是大量老 Windows 程序默认的界面字体，度量差一点就会出现按钮文字截断、对话框错位。
- MSXML 的 DTD 校验重写：DTD（Document Type Definition）校验在 MSXML 里被重新实现，与此前 11.20 的「XML 校验改进」是同一条线。
- 常规 bug 修复：Phoronix 给出 34 个 已知修复，点名 Logos Bible Software、Guild Wars 2、Star Citizen。Linuxiac 补了更细的条目：Vulkan 渲染器不支持 D24X8 深度格式、缺 RGB565 swapchain 回退导致崩溃、Black Mirror II/III 的角色模型与动画、Notepad++ 菜单栏显示异常、WinSCP 打开「关于」对话框崩溃（11.11 引入的回归）、ECDSA 密钥导入等。

这里有个必须标清的边界：Wine 的 GitLab release 页受 Anubis 反爬保护，我没能逐条读取 34 个 Bugzilla 条目与完整变更数，所以游戏/应用名称来自 Phoronix 与 Linuxiac 的转述，不冒充逐条核对。

## 四、版本节奏：别把开发版读成稳定版

WineHQ 每次都写的是 development release。11.x 保持约两周一个版本：11.19 在 10 月 2 日、11.20 在 10 月 16 日、11.21 在 10 月 30 日、11.22 在 11 月 13 日，节奏很整齐。

社区与媒体普遍预期接下来会转入 12.0 的 RC 阶段（历史上是年底每周一个 RC，次年年初出稳定版），Phoronix 也说 11.22 已相当接近 12.0 稳定版的准备工作。但 WineHQ 官方没有发布 12.0 时间表；本文把「11 月底至 12 月转 RC、2027 年初稳定」明确标为节奏推断，不当成承诺。

对使用者的实际含义：想稳定就用 Wine 11.0 稳定分支或发行版/Proton 带的版本；想追 ARM64EC、Wayland、新指令集支持才上 11.x 开发版。11.22 的 AVX 是给「在 ARM 机器上跑 Windows 程序」的人准备的，x86 桌面用户多半感觉不到变化。

## 五、结论

Wine 11.22 单看版本号，是六项更新加 34 个修复的常规小版本。放到 2026 年这条 ARM64EC / WoW64 主线上，它补的是一块很难绕过去的拼图：当 Windows 软件默认假设 AVX 存在时，模拟层不仅要能执行向量指令，还得管好 XState 那一整套寄存器状态。

12.0 之前大约还有一两个开发版。到那时回头看，这一串 11.1x / 11.2x 大概会被记成「Wine 把非 x86 主机跑 Windows 程序这条路铺平」的一段，而不是几十条零散的 release notes。

## Sources

- WineHQ《Wine 11.22 Released》（2026-11-13）：<https://www.winehq.org/news/2026111301> ｜ release 详情：<https://gitlab.winehq.org/wine/wine/-/releases/wine-11.22>
- Phoronix《Wine 11.22 Introduces x86 AVX Emulation On ARM64》：<https://www.phoronix.com/news/Wine-11.22-Released>
- Linuxiac《Wine 11.22 Adds AVX Support on ARM64, Fixes 34 Bugs》：<https://linuxiac.com/wine-11-22-adds-avx-support-on-arm64-fixes-34-bugs/>
- WineHQ 新闻 RSS（11.14–11.21 官方摘要）：<https://www.winehq.org/news/rss> ｜ GitLab releases：<https://gitlab.winehq.org/wine/wine/-/releases>
- 相关 Phoronix 报道：11.21 <https://www.phoronix.com/news/Wine-11.21-Released> ｜ 11.19 <https://www.phoronix.com/news/Wine-11.19-Released> ｜ 11.20 <https://www.phoronix.com/news/Wine-11.20-Released>
