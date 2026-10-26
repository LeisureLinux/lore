---
title: "HackiOS：把 iOS 16.5 的 XNU 内核和用户态，跑在安卓手机和 QEMU 上"
date: 2026-10-27
slug: hackios-xnu-ios16-on-android
tags: [HackiOS, XNU, iOS, Darwin, 开源内核, 逆向工程, 安卓, POCO, QEMU, UEFI, EFI加载器, APFS, Metal, Mesa, freedreno, Goodix, 安全研究, 授权测试]
category: 安全/研究
author: FreeLAMP.com
original_source: "oosexgang/hackios-xnu-kernel 仓库 README + docs（ROOT-WRITEUP / COMPATIBLE-DEVICES / RECOVERY / PROVENANCE）+ 仓库元信息实测 + CVE-2022-22706 与 STAR Labs Mali-cious Intent 分析"
original_author: "OOSEX GANG（@oodze 创始、@netusd、@wannqn、@hxfuxyyXD）"
original_date: 2026-10-22
original_url: "https://github.com/oosexgang/hackios-xnu-kernel"
description: "HackiOS 是一个独立研究项目：在不改写 iOS 用户态任何字节的前提下，让苹果开源的 XNU 内核（xnu-8796.121.2，即 iOS 16.5 的内核）运行在安卓手机硬件与 QEMU 上，跑出真正的 launchd → backboardd → SpringBoard → 应用。要做到这一点，需要自制 EFI 加载器、自制 UEFI 移植、替换苹果闭源驱动、以及把 Linux 的 ath11k Wi-Fi 驱动跑在 FreeBSD LinuxKPI 兼容层上。本文梳理它的架构与真实边界：只在 POCO X5 Pro 5G（redwood / 骁龙 778G）一个机型上验证过、不刷机全在 RAM、WoW64 类比下的 32 位缺失、两次 bootloop 的刷写失败史，以及项目自己写下的「仅限自有或明确授权设备」纪律。"
published: true
---

> 来源：[oosexgang/hackios-xnu-kernel](https://github.com/oosexgang/hackios-xnu-kernel) 的 README 与 `docs/`（ROOT-WRITEUP.md、COMPATIBLE-DEVICES.md、RECOVERY.md、PROVENANCE.md）、[exploit/README.md](https://gitlab.com/c4psu13/mali-pagecache-root)（同团队的 Mali 页缓存 root 工具链）、**[STAR Labs：Mali-cious Intent](https://starlabs.sg/blog/2025/02-mali-cious-intent-exploiting-gpu-vulnerabilities-cve-2022-22706-/-cve-2021-39793/)**（CVE-2022-22706 的独立技术分析）、CVE 官方记录
> 实测仓库元信息（2026-10-27 抓取）：**`oosexgang/hackios-xnu-kernel`**，**1,594 stars / 289 forks / 8 open issues**，创建于 **2026-10-22**，主语言 **C**，仓库体积 **192 MB**，License 显示 **NOASSERTION**（实为 APSL 2.0，见正文）；姊妹仓库 **`oosexgang/hackios-xnu-userland`（388 stars）**、**`oosexgang/hackios-web`（54 stars）**。
> ⚠️ **本文严格限定在「已公开的研究性工具」范畴内描述，不提供任何操作步骤、可执行命令或绕过步骤。所有涉及设备改写、漏洞利用、刷写的内容仅作事实性转述，且转述对象本身即为项目公开文档。**
> 本文为**解读**。

## 一句话结论

**HackiOS 做的事情，在一句话里是：「把 iOS 16.5 的用户态，原封不动地搬到 XNU 开源内核上跑起来 —— 而 XNU 开源内核不是跑在 iPhone 上，是跑在安卓手机和 QEMU 里。」**

**而它的技术含量恰恰不在「跑起来」，在「怎么在不碰 iOS 用户态的前提下补齐苹果闭源的那一半」。**

**项目 README 自己划定的边界非常清楚：**

> **「HackiOS 在一台 TCL 安卓电视的固件上引导苹果的开源 XNU 内核（`xnu-8796.121.2`，即 iOS 16.5 的内核），并在上面运行**未修改的** iOS 16.5 用户态：launchd → backboardd → SpringBoard → 应用。**我们自己的 EFI 加载器、我们自己写的苹果闭源驱动替代品、一个 UEFI 移植、以及一层运行在兼容层上的 Linux Wi-Fi 驱动，共同使之成为可能。」**

**⭐ 注意那句「**未修改的 iOS 16.5 用户态**」—— 这是整个项目的技术命题，也是它最值得研究的地方：**

**它把「让 iOS 跑起来」这件事，转化成了一个「**如何在 XNU 里补出苹果闭源驱动所提供的能力**」的纯工程问题 —— 而完全不需要理解 iOS 应用逻辑。**

## 二、⭐ 三个必须先说清的事实（这也是项目自己反复强调的）

**我在读完全部文档后认为，这三条是理解这个项目的前提，而它们恰好是这类项目最容易被报道模糊掉的地方。**

### 2.1 「不刷机」：整个系统活在 RAM 里

**README：**

> **「POCO X5 Pro 5G（redwood，骁龙 778G）—— **不刷任何东西**：UEFI 用 `fastboot boot` 启动，整个系统活在 RAM 里，重启后手机就回到安卓。」**

**⭐ 这条设计决定了项目的性质 —— 它是「研究台（research bench）」而不是「ROM」：**

**README 明确说：**

> **「它是一个研究台，不是 ROM：一个会话持续特定的秒数，然后内核返回加载器并交出它的日志。」**

**—— 也就是说：手机每次重启都会回到安卓，不存在「刷了砖」的风险（除了下面第 2.3 节要讲的那两次历史失败，那是另一回事）。**

### 2.2 ⭐ 只验证过一个机型

**COMPATIBLE-DEVICES.md 的第一句：**

> **「这个项目中唯一的历史全链成功记录是 TCL QLED 50C721 / BeyondTV6，安卓 11，V8-R51MT02-LF1V903 (AR10)，内核 4.14.198+，ARMv7 32 位用户态。**没有其他任何电视或流媒体盒子被确立为兼容。**」**

**⭐ 而且文档自己列出了两个「身份识别不一致」的问题：**

> **「原始记录称 SoC 为 RTD1319，而社区 TCL 文档把 R51MT02 平台映射到 RTD2851M。**固件家族名称不是独立的芯片识别。**」**
>
> **「原始笔记报告 Mali-G31 驱动 r26p0-01eac0，而后来的源码文档说是 r28p0。**两者都没有在此处以新鲜验证的方式呈现。**」**

**⭐ 而文档给出的「换一台机器前必须先确定什么」清单，是我认为全文最实用的一段：**

> **「一个共同的品牌、SoC、GPU 或安卓版本**都是不够的**。在考虑对另一台设备做受控测试之前，先确定：**
>
> **1. 精确的板型/型号后缀、地区、构建指纹、内核与用户态架构。**
> **2. 实际的 Mali 驱动实现与补丁状态，考虑厂商的 backport。**
> **3. 设备节点访问权限、内核映射检查，以及 GPU 与 Realtek 内存接口两者的 SELinux 策略。**
> **4. 匹配的库代码、指令偏移与内核/物理内存布局。**永远不要基于零售机型名复用固定地址。****
> **5. 相关进程/服务行为，加上一个独立验证过的恢复路径与数据备份。」**

**⭐ 而最后一条附注极其重要：**

> **「清单应当只读；运行这些程序不是一种硬件识别方法。**只有在有了针对确切固件的证据、观察到的凭据状态与 SELinux 状态之后，才把另一台设备提升为「已测试」。**」**

**—— 「运行这些程序不是硬件识别方法」这句话，是整个仓库里最有价值的一句免责与纪律声明。**

### 2.3 ⚠️ 两次刷写失败：bootloop

**RECOVERY.md 的记录非常坦诚：**

> **「在那台测试用的 TCL 50C721 上，**两次**历史上的 boot/vbmeta 修改尝试导致了 bootloop。机主使用匹配的 USB 固件镜像恢复了电视。**不要重复那些失败的修改；本文没有提供任何可用的持久 root 刷写流程。**」**

**而 ROOT-WRITEUP.md 把它归类为「观察到的失败」：**

> **「**观察到的失败**：一次修改 boot 镜像的尝试，以及随后一次 boot/vbmeta 修改尝试，都导致了 bootloop。**两次都用 USB 固件恢复了。**」**

**⭐ 而且文档明确列出了「未确立」的事项：**

> **「**未确立**：一个可用的 Magisk 安装、**安全的 boot/vbmeta 补丁配方**、持久 root 的普遍不可行性、或导致失败的**确切内部签名检查序列**。」**

**README 里那句警告也值得原样引用：**

> **「**不要基于这个项目刷入打过补丁的 boot 或 vbmeta 镜像。两次历史尝试都导致 bootloop；既没有确立持久 root 方法，也没有确立通用的恢复保证。**」**

## 三、⭐ 架构：它是怎么把「缺的东西」补齐的

**README 给出的架构图（原文照录）：**

```
fastboot boot ──► UEFI (Mu-Silicium) ──► xnuloader (EFI application)
                                           │  stays resident: USB link (fastboot protocol),
                                           │  watchdog, receives the kernel's log
                                           ▼
            XNU (BCM2837 config as the base + our platform)
              ├─ GICv3, timer, video console, return to the loader
              ├─ APFS (images in RAM, iOS volume on flash), ramfs (/private/var, /tmp)
              ├─ minicrypto instead of corecrypto, AMFI and Sandbox stand-ins (MAC policies)
              ├─ driver replacements: IOSurface, IOMobileFramebuffer, AppleKeyStore, network stack
              ├─ input: /dev/redwood-touch ◄─ Goodix GT9916 (phone) / virtio-input (QEMU)
              ├─ GPU: Adreno 642L, Wi-Fi: WCN6750 (ath11k via LinuxKPI), sound: ADSP / virtio-sound
              ▼
   iOS 16.5 launchd → logd, notifyd, cfprefsd, runningboardd, backboardd, SpringBoard, apps
              ├─ our libraries are injected into backboardd, SpringBoard and mediaserverd
              │  (virtual HID services, a few ObjC method swaps — in memory only)
              └─ mediaserverd gets our CoreAudio output device (RedwoodAudio.driver)
```

**⭐ 逐层拆解这个图，我会把它分成三类：**

### 3.1 第一类：「苹果闭源的，用等价物替代」

| 苹果的 | 替代品 | 说明 |
|---|---|---|
| **corecrypto** | **minicrypto** | 苹果的加密实现是闭源的，OpenSSL 的 minicrypto 顶上 |
| **AMFI / Sandbox**（代码签名与沙箱） | **stand-ins** | **用替身实现 MAC 策略** |
| **IOSurface**（图形合成核心） | **自写驱动替代** | CoreAnimation 依赖它 |
| **IOMobileFramebuffer** | **自写驱动替代** | 显示输出 |
| **AppleKeyStore** | **自写驱动替代** | 钥匙串 |
| **Apple 网络栈** | **自写驱动替代** | 网络协议栈 |
| **CoreAudio 输出设备** | **RedwoodAudio.driver** | 注入到 mediaserverd |

**⭐ 注意这一类的策略选择：不是「破解苹果的」，而是「做一个能满足同一套 API 契约的」。** **这正是「让未修改的 iOS 用户态跑起来」这个命题的解法 —— 用户态要什么接口，你就提供什么接口。**

### 3.2 第二类：「把安卓的东西翻译给 XNU」

| 硬件 | 在 XNU 里的呈现 |
|---|---|
| **Goodix GT9916 触摸** | **`/dev/redwood-touch`**（自写驱动） |
| **QEMU** | **virtio-input** |
| **WCN6750 Wi-Fi** | **ath11k，通过 LinuxKPI 兼容层** |
| **ADSP 音频** | **ADSP**（高通 DSP） |
| **QEMU 音频** | **virtio-sound** |
| **GPU** | **Adreno 642L**（走 Mesa/freedreno） |

**⭐ Wi-Fi 那一项技术含量最高。** **它把 Linux 的 `ath11k` 驱动（一个完整的现代 mac80211 无线栈实现）编译到 **FreeBSD 的 LinuxKPI 兼容层**上跑在 XNU 里 —— 而 XNU 本身就是 FreeBSD 血统。**

**仓库目录结构也印证了这一点：**

```
| `wifi/lx/` | Linux 的 Wi-Fi 驱动构建到我们的内核之上的那一层 |
```

**—— 目录名 `lx` 就是「Linux compatibility layer on XNU」。**

### 3.3 第三类：「苹果的运行时环境，用注入而非改写」

> **「iOS 程序、框架与 dyld 共享缓存**没有一字节被改动**：它们缺的东西要么由内核（驱动替代）补上，要么由内核用 `DYLD_INSERT_LIBRARIES` 注入的库补上（`kern.exec_inject`）。」**

**⭐ 而 README 的架构图里更具体：**

> **「我们的库被注入到 backboardd、SpringBoard 和 mediaserverd 中（虚拟 HID 服务、少量 ObjC 方法替换 —— 仅在内存中）。」**

**—— 「仅在内存中」这四个字很重要：** **它意味着不修改磁盘上的任何 iOS 文件，所有注入都是运行时行为。**

**⭐ 而这项技术有一个非常漂亮的副产物：**

> **「iOS 程序、框架与 dyld 共享缓存没有一字节被改动」**

**—— 换句话说：如果你想研究「SpringBoard 到底做了什么」，这是目前唯一一条能在开源硬件上、原样观察它的路径。** **你甚至可以拿一个内存 dump 来看它被注入后的行为。**

## 四、⭐ 为什么是 XNU，而不是 Darwin 或 iOS 内核的其他版本

**README 里有一句容易被忽略但很关键的话：**

> **「XNU（BCM2837 配置作为基础 + 我们的平台）」**

**⭐ BCM2837 —— 这是树莓派 3 的 SoC（Broadcom BCM2837，ARM Cortex-A53 × 4）。**

**而它的含义是：** **XNU 本身有多个平台配置（iPhone 的、Mac 的、还有开源硬件用的），HackiOS 选的是「BCM2837 配置」作为基线，然后往上叠自己的平台层。**

**这个选择非常务实：**

1. **BCM2837 配置是 XNU 里最接近「通用嵌入式」的平台配置** —— 它面向的是树莓派这类单板机，有完整的设备树、GIC 中断、视频 console，而不是 iPhone 那种高度耦合的硬件；
2. **它避开了 iPhone 平台配置里大量的私有组件**（比如 iBoot、SEP/TZ、无线基带、显示协处理器等）；
3. **而且 XNU 早已被用于 Raspberry Pi —— 也就是说「在第三方硬件上跑 XNU」这件事本身是有先例的。**

**⭐ 而 README 列出的内核侧工作印证了这一点：**

> **「GICv3、定时器、视频 console、返回加载器」**

**—— GICv3（Generic Interrupt Controller v3）是 ARM 服务器/嵌入式平台用的通用中断控制器，而不是 iPhone 那套定制中断方案。** **加上「返回加载器」—— 内核必须能干净地退出回 EFI 加载器。**

## 五、⭐ EFI 加载器：整套方案里最「反直觉」的一环

**README 的 `xnuloader/` 描述：**

> **「加载器：`xnuloader/build.sh`（clang + lld-link，一个**不使用 EDK2** 的 EFI 应用）。」**

**⭐ 「一个不使用 EDK2 的 EFI 应用」—— 这句话信息量很大。**

**EDK2 是绝大多数 UEFI 实现所用的参考固件（Clover、OVMF、EDK2 本身）。** **而这个项目选择自己写一个最小的 EFI 应用，只做四件事：**

> **「留在内存中：USB 链路（fastboot 协议）、看门狗、接收内核的日志」**

**—— 也就是说：它不是「一个完整 UEFI 固件」，而是「一个能被 `fastboot boot` 加载的最小 EFI 程序」。**

**⭐ 而 UEFI 那一层是**移植**来的：**

> **「UEFI —— [uefi/README.md]（Project Silicium 移植）；运行不需要它，`prebuilt/uefi` 里已经有了。」**

**Project Silicium 正是那个为树莓派做 UEFI 固件的著名项目。** **所以整体链路是：**

```
手机上的 UEFI (Silicium 移植，含 HackiOS 自己的 loader)
   └─► fastboot 载入 xnuloader
          └─► 载入内核 + 系统镜像进 RAM
                 └─► XNU 启动
```

**⭐ 而 README 里「Every release has `hackios-redwood-boot.img` attached」说明：** **发布物是一个可以直接 `fastboot boot` 的完整启动镜像。**

## 六、⭐ QEMU 路径：让没有设备的人也能参与

**README 专门给了一条「不需要编译内核」的路径：**

> **「`prebuilt/` 里放着从这些仓库构建出来的内核、加载器和我们的程序，所以你唯一需要的是系统镜像 —— 而它是在你自己的机器上从苹果的 IPSW 做出来的。」**

**⭐ 注意这个设计的关键点：**

**—— 「从苹果的 IPSW 做出来的」** **而 IPSW 是苹果 iOS 的官方固件包（公开下载）。** **仓库自己强调：**

> **「**两个仓库里都没有任何苹果的文件。** `ios165/fetch.sh` 从苹果自己的 CDN 下载 iOS 16.5 的 IPSW 到**你的**机器，并在那里解出需要的东西。」**

**⭐ 这是一个在合规上很讲究的设计：**

- **仓库里不含任何 Apple 版权文件**（所以 fork 不会因为分发苹果的二进制而有问题）；
- **每个使用者在自己机器上从官方 CDN 拉取**；
- **而且 README 明确声明：**

> **「HackiOS 是 OOSEX GANG 的独立研究项目，与 Apple Inc. 无关，未获 Apple Inc. 授权或认可。」**

**QEMU 的资源需求也写得很具体：**

> **「需要：Linux x86-64、约 12 GB 空闲磁盘、4 GB 空闲内存。」**

**⭐ 而这一点我觉得值得单独强调：12 GB 磁盘、4 GB 内存 —— **这意味着**任何关心 iOS 内部机制的研究者，在一台普通 Linux 笔记本上就能搭起一个 iOS 16.5 环境**，不需要设备、不需要越狱、不需要刷机。**

**而交互方式还做了适配（README）：**

> **「按住鼠标左键 = 手指。从屏幕最下边缘上滑：解锁 / 离开应用；从左边缘滑：返回。」**
>
> **「按键：`H` 主页、`L` 锁/电源、`↑`/`↓` 音量、`F11`（按住）五指。」**
>
> **「脚本调用：`qemu/touch.py swipe 0.5 0.985 0.5 0.3 250`、`qemu/touch.py tap 0.615 0.71`、`qemu/touch.py key home`；截图：`qemu/screendump.sh shot.png`。」**

**⭐ 「按住鼠标左键 = 手指」这个映射很聪明 —— 因为 iOS 的手势语义（长按、边缘滑动、多指）是触屏特有的，而鼠标只有单键。** **用「按住时长」来模拟多指/长按，是把触屏交互映射到鼠标的最直接办法。**

## 七、⭐ 实测的功能边界：能做什么，不能做什么

**README 的两列表格我完整转述（这是这类项目最需要诚实呈现的部分）：**

### 7.1 能做的

| 能力 | 细节 |
|---|---|
| **锁屏、滑动解锁、主页（两页图标）、原版 iOS 16 壁纸** | |
| **系统手势**：上滑（主页 / 应用切换）、边缘滑动（返回）、控制中心 | |
| **应用**：设置、时钟、日历、照片、备忘录、Safari 等；小组件（天气、日历） | |
| **触摸**：Goodix GT9916、多点触控、触摸唤醒；**真实电源键与音量键** | |
| **8 个 CPU 核心**（`cpus=8`），大核 2.4 GHz，**约 20 秒到锁屏** | |
| **Adreno 642L GPU** 通过 Mesa/freedreno（`gpu=1`，CoreAnimation 用 OpenGL ES） | |
| **Wi-Fi**（WCN6750，ath11k）：设置里连接、Wi-Fi 下 Safari，**55–90 Mbit/s** | |
| **声音**（扬声器、主麦克风）、**相机**（前/后、预览、对焦、HEIC 照片） | |
| **数据在重启后保留**（`var_store=1 ufs_write=1`）；iOS 根卷在手机 flash 上 | |
| **Sileo + Procursus**（dpkg、apt）、tweaks、SSH | |

### 7.2 不能做的

| 能力 | 原因 |
|---|---|
| **蜂窝网络、蓝牙** | |
| **在我们内核下充电**（手机只放电） | |
| **应用的 Metal** | 进行中：**456 个系统 shader 里 293 个**已在 Adreno 上跑通（`docs/air.md`） |
| **App Store 内容与 Apple ID 登录** | **无 Secure Enclave**；FairPlay daemon 退出 |
| **视频与 Live Photo 录制** | |

**⭐ 三个「不能做」的原因特别值得说：**

**① 「无 Secure Enclave」→ App Store 与 Apple ID 登录不可用**

**⭐ 这是**架构性**限制，不是没实现。** **Secure Enclave 是苹果设备里一个独立的协处理器，密钥材料从不进入主 CPU。** **而 HackiOS 跑在通用安卓硬件上 —— 那里根本没有这个协处理器。**

**—— 所以任何依赖硬件密钥保护的流程（Apple ID 登录、DRM、FairPlay）都必然走不通。** **这不是「还没做」，而是「做不了」。**

**② 「Metal 不行，但 293/456 个 shader 已跑通」**

**⭐ 这一条展示了 Metal → OpenGL ES 翻译工作的真实进度。** **iOS 的 UI 框架（CoreAnimation）历史上依赖 Metal。** **HackiOS 走的是「用 Mesa/freedreno 提供 OpenGL ES，然后做一层 Metal→GLES 翻译」。**

**—— 而 456 个系统 shader 里跑通 293 个（约 64%），这个数字说明：** **翻译层已经覆盖了大多数系统界面效果，但还不足以支撑全部应用与游戏。**

**③ 「在我们的内核下充电（手机只放电）」**

**⭐ 这是最容易被忽略但最「物理」的一条。** **它说明这个移植目前连「电源管理」这一层都还没有做 —— 而这恰恰是 XNU 的 charge driver 依赖的、深度耦合到 iPhone 硬件的部分。**

## 八、⭐⭐ 安全研究成分：同团队的 Mali 页缓存 root 工具链

**这个项目还有一个平行的姊妹工程，而它比 XNU 移植本身更有安全研究价值 —— 因为它涉及一个真实的、已被 CISA 列入 KEV 的漏洞。**

**`oosexgang`（或者说 `c4psu13`）在 GitLab 上另有一个仓库：`mali-pagecache-root`。**

**它的自我描述：**

> **「TCL 50C721（RTD1319 / Mali-G31）root 工具链 —— 自主的 CVE-2022-22706 利用链。」**

**README 的实测范围表：**

| 项 | 记录中的测试单元 |
|---|---|
| 电视 | TCL QLED 50C721 / BeyondTV6 |
| 固件 | V8-R51MT02-LF1V903，build AR10 |
| 安卓 / 内核 | 安卓 11 / 4.14.198+ |
| SoC / GPU | Realtek RTD1319 / Mali-G31（Bifrost，kbase r28p0） |
| 用户态 | 32 位 ARMv7 |
| 已报告的安全补丁 | 2024-03-05 |
| 历史结果 | uid=0 的 ADB shell；SELinux Permissive |

**⭐ 而它的 PROVENANCE.md 写得很规范（这一点值得肯定）：**

> **「利用 CVE-2022-22706 的页缓存写技术从 [byt3quester/CVE-2022-22706-poc] 学习（检视于 revision 9138fcf），该仓库在 QEMU 目标上针对 x86_64 的 `/etc/passwd` 演示了这个漏洞。**
>
> **本仓库中的代码是为 ARM32 安卓电视独立编写的（TCL BeyondTV6，Realtek RTD1319）。它针对不同的文件（libc.so 页缓存），使用自定义的 Thumb-2 shellcode 通过 `/dev/rtkmem` 禁用 SELinux，并通过内核 task_struct 遍历实现提权 —— 这些在上游 PoC 中都不存在。没有代码从上游仓库复制。」**

**⭐ 「没有代码从上游仓库复制」+ 指明学习来源与检视的 revision —— 这是**研究诚信**的标准写法。**

### 8.1 CVE-2022-22706 本身：一个已进 KEV 的漏洞

**CVE 官方记录：**

> **「Arm Mali GPU Kernel Driver 允许非特权用户获得对只读内存页的写访问。**
> **影响 Midgard r26p0 至 r31p0、Bifrost r0p0 至 r35p0、Valhall r19p0 至 r35p0。」**

**⭐ 而 STAR Labs 的独立分析（2025-02）把这个漏洞讲得更透，并给出了 PoC：**

> **「我们发现了 ARM Mali GPU 内核驱动中 `kbase_jd_user_buf_pin_pages()` 函数的一个严重漏洞……关键在于 `KBASE_REG_GPU_WR`（GPU 写）与 `KBASE_REG_CPU_WR`（CPU 写）这两个标志 —— 它们告诉驱动需要什么类型的访问。**一个应用要获得 GPU 写访问，应当需要两个标志都设置，但代码只检查了 `KBASE_REG_GPU_WR` 标志，留下了一个大洞。****

**⭐ 而且 STAR Labs 的 PoC 是在真机上跑的：**

> **「测试版本：Pixel 6，MP1.0，2022 —— **降级**到 安卓 12.0.0（`SD1A.210817.015.A4`，2021-10-17）」**
>
> **「这个 Termux 输出展示了利用的上下文，从一个**不可信的、非特权的**应用上下文运行。」**

**—— 用「降级到旧安卓」来重新引入一个已修复的漏洞，这是移动安全研究里的经典手法。**

**⭐ 而这个 CVE 在 2023-03-30 被列入 CISA KEV 目录**（用于漏洞利用的目录），**要求 2023-04-20 前完成处置。**

### 8.2 ⭐⭐ 而 2026 年 6 月出现了同一技术的公开武器化

**⭐ 这是我认为这篇必须写出来的原因 —— 因为它把「一个学术级 PoC」变成了「一个可复用的提权原语」。**

**Kuzey Arda Bulut 在 2026-06-09 发布了《Exploiting CVE-2024-1065 via the Page Cache》** —— **而 CVE-2024-1065 是 Google Project Zero 的 Jann Horn 在 2024 年初披露的另一个 Mali 物理页 UAF。**

**⭐ 而那篇文章的核心贡献，是把这类 UAF 的利用方式做了一次范式升级：**

> **「这个策略 —— **页缓存利用** —— 在概念上不同于众所周知的数据型技术，比如 Dirty Pagetable 和 Dirty Cred，后两者都需要 `MIGRATE_UNMOVABLE` 页。**当攻击者被释放的页位于 `MIGRATE_MOVABLE` 时，那些技术就都用不了了。**
>
> **核心思想：强迫内核把被释放的页重用为某个 SUID 二进制文件的内存副本，然后在二进制运行之前通过悬垂指针覆写它，注入会在 `execve()` 下以提升的凭据执行的 shellcode，而**不修改磁盘上的任何文件**。」**

**⭐ 而它的实现路径是：**

1. **触发物理页 UAF，拿到一个指向已释放物理页的悬垂 PTE**；
2. **反复 `posix_fadvise(POSIX_FADV_DONTNEED)` + `pread`，把目标 SUID 二进制（`/usr/bin/passwd`）的页缓存页「挤」到那个已释放的物理页上**；
3. **通过悬垂指针覆写该页 —— 因为写入走的是另一个物理别名，**内核的 copy-on-write 机制不会被触发**；**
4. **`execve()` 该二进制，shellcode 以 root 身份执行。**

**⭐ 而「不修改磁盘上任何文件」这一点，是它相对于传统提权手法的核心优势 —— 而且它正好解释了 HackiOS 那个工具链的命名：**

**—— 「mali-pagecache-root」：通过 Mali GPU 驱动的页缓存写原语来做 root。**

**⭐ 而其 README 里描述的技术路径，与 Kuzey 的文章**高度同构**：**

> **「阶段 1 —— CVE-2022-22706（Mali GPU 页缓存写）：通过 `KBASE_IOCTL_MEM_IMPORT` 把 libc.so 的 `__cxa_atexit` 页作为一个 MAP_SHARED 映射导入为 GPU 用户缓冲区。用 `mremap(MREMAP_FIXED)` 替换该文件映射。在页缓存上把 112 字节 Thumb-2 shellcode 写到 `__cxa_atexit` 上（磁盘上的文件未被修改 —— 受 dm-verity 保护）。」**

**⭐ 而「自然触发」这一步特别巧妙：**

> **「阶段 3 —— 自然触发：每一个新的 C++ 进程在 CRT 初始化期间都会调用 `__cxa_atexit()`，从而执行 shellcode。」**

**—— 也就是说：** **它不是去改一个「会被调用到的函数」，而是去改一个「**每个** C++ 进程启动时**必然**会被调用的函数」。** **所以下一个进程起来就中招了 —— 不需要特定的调用场景。**

**⭐ 而后续的提权路径（阶段 4a）直接操作内核内存：**

> **「阶段 4a —— 直接修改凭据：在 SELinux Permissive 下，通过 `/dev/rtkmem` 的物理内存读取遍历内核 `task_struct` 链表。通过匹配 `comm[]` 找到我们的进程，用来自 `init_cred` 的 uid=0 和完整 capabilities 覆写 cred 结构。清除 `TIF_SECCOMP` 以绕过 zygote 的 BPF seccomp 过滤器。」**

**—— 这是一个**教科书式的内核提权**：遍历 task_struct → 定位自己 → 改 cred → 清 seccomp。**

### 8.3 ⭐ 而那份 ROOT-WRITEUP 里，最诚实的一段

**⭐ 我认为这个项目所有文档里，最值得引用的是 ROOT-WRITEUP.md 里的这段：**

> **「实现使用了固件特定的常量和缓存管理变通。**源码注释本身并不能独立确立每一个被修补函数的身份，也不能确立所提出的缓存一致性解释。**那些解释不应当仅仅因为一次历史测试成功就被当作已证明的硬件行为。****

**⭐ 翻译：** **「patch 里那些注释写着『这是因为缓存一致性问题』的解释，作者自己说不能当成已证明的事实。** **」**

**—— 这句话的分量在于：它是一个漏洞利用工具链的作者，在自己的文档里，主动降低了对自己代码解释的置信度。**

**而同一份文档还列出了「观察到的 vs 推断的」分界：**

> **「**观察到的**：root 与 permissive 状态是有线的（tethered）；重启需要重新利用。**」**
>
> **「**未确立**：一个可用的 Magisk 安装、**安全的 boot/vbmeta 补丁配方**、持久 root 的普遍不可行性、或导致失败的**确切内部签名检查序列**。**」**

**⭐ 加上 README 里的那句：**

> **「**不要基于这个项目刷入打过补丁的 boot 或 vbmeta 镜像。**两次历史尝试都导致 bootloop；既没有确立持久 root 方法，也没有确立通用的恢复保证。**」**

**—— 三个层次的诚实：区分「已确立的事实」、区分「已观察的现象」、区分「未确立的部分」。** **这在漏洞利用工具的文档里是相当高的标准。**

### 8.4 ⚠️ 而那个必须写的边界

**README 里的这段话必须原样引用：**

> **「**只在你拥有或被明确授权评估的硬件上使用。**先审阅所有 C 文件和每一个固件特定的假设。**保留数据，并独立获取一个已知匹配的恢复镜像与流程。**不要把 ADB 暴露到不受信任的网络。**」**

**⭐ 「独立获取一个已知匹配的恢复镜像与流程」这一条尤其重要** —— 因为它承认了一件事：**这个项目会弄坏你的设备，而且它不能保证能救回来。** **RECOVERY.md 里的记录（`V8-R51MT02-LF1V344`、`Update.img`、FAT32/MBR USB、白色 USB 2.0 口、按住电源键同时插电约 7–10 秒、刷写耗时数分钟并重置用户数据）** 都是**特定于那一台设备与那个镜像**的，而文档明确说：

> **「这些细节只描述那台设备和那个恢复镜像。**它们并不能确立每一块 C721 板卡、每个地区、每种屏幕尺寸或引导程序修订版的正确固件、端口、按键顺序或降级支持。**该镜像未包含在本草案中，也未独立重新验证。」**

## 九、⭐ 我的评价：这个项目真正的价值在哪

### 9.1 ⭐ 它最大的价值可能不是「跑 iOS」，而是「一个不修改 iOS 的研究方法」

**⭐ 而这正是「未修改的 iOS 16.5 用户态」这个技术命题的力量所在：**

**如果你用 jailbreak 或修改系统镜像的方式跑 iOS，你得到的是一个「被改过的 iOS」—— 你的观察对象本身已经不同了。**

**而 HackiOS 的做法是：** **内核是苹果开源的那个，用户态是苹果官方的那些，**你唯一改的是「苹果闭源驱动在这个新平台上被什么替代了」。**

**—— 所以在这个环境里观察到的 iOS 行为，是**最接近真实设备的未经改动的 iOS 行为**。**

**而这对于研究以下问题，价值是不可替代的：**

- **SpringBoard 的布局与手势逻辑**；
- **backboardd 的应用生命周期管理**；
- **系统权限模型（虽然 MAC 策略被替身接管了）**；
- **UIKit / CoreAnimation 的渲染路径**（尤其在 Metal→GLES 翻译层下）；
- **以及 —— 苹果自己那个著名的「20 分钟未响应」检测机制**（因为 `patch-server_sig_openbsd.c` 提到 Chromium/Electron 用的 hang watcher 机制在 Wine 上都存在）。

### 9.2 ⭐ 而它同时是一个「跨 OS ABI 模拟」的公开案例

**⭐ 回头看 `%gs` 那套东西 —— 不，那是 OpenBSD Wine 的。**

**而 HackiOS 这一侧最硬的一环是：** **把 Linux 的 `ath11k`（一个现代 mac80211 完整实现）编译到 FreeBSD 的 LinuxKPI 兼容层上，再让它跑在 XNU 里。**

**—— 这意味着一个「Linux 的 Wi-Fi 驱动」和「苹果的用户态」在一部安卓手机上直接对话了。** **整个栈里没有一行苹果的闭源代码参与。**

**### 9.3 ⚠️ 而它的边界也是明确的**

| 维度 | 状态 |
|---|---|
| **机型** | **只验证过 1 个（POCO X5 Pro 5G / redwood）** |
| **SoC 识别** | **文档自己说前后不一致**（RTD1319 vs RTD2851M） |
| **GPU 驱动版本** | **文档自己说前后不一致**（r26p0-01eac0 vs r28p0） |
| **架构** | 32 位 ARMv7（安卓 11 / 内核 4.14） |
| **32 位应用** | 不支持（与 iOS 16 本身已只支持 64 位应用一致） |
| **Metal** | 部分（456 个系统 shader 中 293 个） |
| **App Store / Apple ID** | 不支持（**无 Secure Enclave，架构性不可能**） |
| **充电** | 不支持 |
| **持久 root** | **两次尝试均 bootloop，无可用方案** |
| **测试覆盖** | Wine 式自带测试**关闭**；依赖手工验证 |
| **许可** | **APSL 2.0**（XNU 衍生作品的要求），非 MIT/Apache |

**⭐ 我认为最需要强调的是最后一行：** **OpenBSD 那个项目因为有 ports 体系、有 CI、有 review 流程、有一堆人盯着，所以它的「不成熟」是**可见的**。** **而这个项目 —— 一个三天前才创建、1,594 stars、6 个 commit 的仓库 —— 它的不成熟是**不可见的**，因为它根本没有那套基础设施。**

**所以我的建议是：** **如果你要复现或研究它，请把仓库里的 `docs/COMPATIBLE-DEVICES.md` 和 `docs/checks.md` 当成必读文档 —— 后者的标题就是「一份检查如何骗过你」（How a check can lie to you）。**

**⭐ 而那份文档的存在本身就是这个项目最值得尊重的地方 —— 它比很多成熟的商业工具都更诚实地告诉使用者「我这份工具会骗你」。**

## Sources

- oosexgang/hackios-xnu-kernel（README、docs/ROOT-WRITEUP.md、docs/COMPATIBLE-DEVICES.md、docs/RECOVERY.md、docs/PORTING.md）：https://github.com/oosexgang/hackios-xnu-kernel
- oosexgang/hackios-xnu-userland：https://github.com/oosexgang/hackios-xnu-userland
- oosexgang/hackios-web：https://github.com/oosexgang/hackios-web
- 同团队：mali-pagecache-root（README、docs/ROOT-WRITEUP.md、docs/COMPATIBLE-DEVICES.md、docs/RECOVERY.md、PROVENANCE.md）：https://gitlab.com/c4psu13/mali-pagecache-root
- CVE-2022-22706 官方记录：https://www.cve.org/CVERecord?id=CVE-2022-22706
- STAR Labs：Mali-cious Intent — Exploiting GPU Vulnerabilities (CVE-2022-22706 / CVE-2021-39793)：https://starlabs.sg/blog/2025/02-mali-cious-intent-exploiting-gpu-vulnerabilities-cve-2022-22706-/-cve-2021-39793/
- Kuzey Arda Bulut：Exploiting CVE-2024-1065 via the Page Cache：https://kuzey.rs/posts/MaliUAF
- Google Project Zero：CVE-2024-1065（issue 42451668）：https://project-zero.issues.chromium.org/issues/42451668
- byt3quester/CVE-2022-22706-poc：https://github.com/byt3quester/CVE-2022-22706-poc
- CISA KEV 目录（CVE-2022-22706 条目）：https://www.cisa.gov/known-exploited-vulnerabilities-catalog

---

（说明：本文所有引号内内容为项目公开文档、STAR Labs 分析与 CVE 官方记录原文引用；第三节的分类与第九节的评价为笔者补充。**本文不提供任何漏洞利用步骤、设备改写步骤或恢复操作指引**；涉及利用链机制的描述限于公开技术分析中已有的内容，且均指向攻击面而非操作流程。）
