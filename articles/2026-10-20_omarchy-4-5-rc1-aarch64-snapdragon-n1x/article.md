---
title: "Omarchy 4.5-RC1 开始支持 aarch64：而这次真正的进展不是「多了一个架构」，是三个完全不同来源的 ARM 笔记本同时跑起来了"
date: 2026-10-20
slug: omarchy-4-5-rc1-aarch64-snapdragon-n1x
tags: [Omarchy, Arch Linux ARM, aarch64, Snapdragon X, NVIDIA N1X, Apple Silicon, Omarchy Mac, Hyprland, Limine, 每显示器工作区, 浮动工作区, 通知系统, 国际化, DHH, 发行版]
category: Linux/运维
author: FreeLAMP.com
original_source: "Phoronix 报道 + Omarchy v4.5.0-rc1 官方发布说明（GitHub Releases）+ GitHub 仓库元信息"
original_author: "Michael Larabel（Phoronix）；David Heinemeier Hansson 及 Omarchy 贡献者"
original_date: 2026-10-20
original_url: "https://www.phoronix.com/news/Omarchy-4.5-RC1"
description: "Omarchy 4.5-RC1 发布，第一次把 aarch64 变成正式支持的架构。而我认为值得写的不是「多了个架构」，是它同时让三个完全不同来源的 ARM 平台跑起来：高通的 Snapdragon X（联想 Yoga Slim 7x 与 ThinkPad T14s）、NVIDIA N1X（ASUS ProArt P14 与 Dell XPS 16）、以及通过合并 Omarchy Mac 为 Apple Silicon 铺路。这三种机器的 bootloader、固件来源、GPU 驱动全不一样。附 4.5 的其他改动：每显示器独立工作区、浮动工作区加 dock、重做的通知系统、50 种语言、启动时间从 6 秒降到 1 秒。"
published: true
---

> 来源：[Phoronix：Omarchy 4.5 Expanding To AArch64 World With Snapdragon X & NVIDIA N1X Laptops](https://www.phoronix.com/news/Omarchy-4.5-RC1)（**Michael Larabel，2026-10-20 07:52 EDT**）
> 一手材料：本文的功能细节、硬件支持范围、ISO 与 SHA256 全部来自 **Omarchy v4.5.0-rc1 的官方发布说明**（GitHub Releases，**2026-10-20 08:54 UTC**）。仓库元信息实测：**`omacom/omarchy`**，**45,355 stars / 5,608 forks**，主语言 Shell，MIT，创建于 2025-06-01。⚠️ 注意仓库已从 `basecamp/omarchy` 迁到 **`omacom/omarchy`**。
> 本文为**解读**。第二节关于「三个 ARM 平台差异」的分析、第五节的判断是笔者补充的部分。

## 一句话结论

**Phoronix 的标题落在「扩展到 AArch64 世界」，而我认为真正的信息藏在它列举的那些机器型号里。**

**因为那些型号来自三个完全不同的芯片与固件生态**：

> **「Omarchy 4.5-RC1 在 NVIDIA N1X 支持方面是在 Dell XPS 16 和 ASUS ProArt P14 上测试的。高通 Snapdragon X 笔记本的测试是在 Lenovo Yoga Slim 7x 和 Lenovo ThinkPad T14s 上完成的。」**

**再加上发布说明里那条关于 Apple Silicon 的**：

> **「Omarchy Mac 过去是一个独立的 fork。它共享的硬件和桌面支持现在活在 Omarchy 本身里，所以 Apple Silicon Mac 跑的是和其他所有机器一样的 Omarchy，只有它们的启动设置留在 Omarchy Mac 的包里。」**

**所以这一版同时让三个生态跑起来**：

| 生态 | 芯片 | 测试机型 | 启动/固件来源 |
|---|---|---|---|
| **高通** | **Snapdragon X** | **Lenovo Yoga Slim 7x、ThinkPad T14s** | **需要从 Windows 分区拉取固件** |
| **NVIDIA** | **N1X（Grace + Blackwell）** | **ASUS ProArt P14、Dell XPS 16** | **NVIDIA 开源驱动 + Omarchy 的 aarch64 内核** |
| **Apple** | **Apple Silicon** | **（为 M 系列铺路）** | **启动设置留在 Omarchy Mac 包里** |

**我认为「三个生态」这个说法不是修辞**：**因为 ARM 笔记本最大的麻烦从来不是「内核能不能跑」，而是「每台机器的固件、设备树、GPU 驱动都不一样」。** **x86 上有一个相对统一的 ACPI + UEFI + PCIe 的抽象，所以在 x86 上「装一个 Linux 发行版」是一个通用流程。** **而 ARM 上，这三样东西都还没有统一到那个程度。**

**所以一个发行版「支持 aarch64」在 2026 年的实际含义，不是「编一个 aarch64 版本」，而是「针对每一类机器做一遍移植」。** **而这一版做了三类。**

## 一、三类机器，三种完全不同的麻烦

**这一节我想把发布说明里那几条展开，因为它们各自代表一种不同的技术问题。**

### Snapdragon X：固件得从 Windows 里挖

**发布说明写得很具体**：

> **「像 Lenovo Yoga Slim 7x 和 ThinkPad T14s 这样的 Snapdragon X 笔记本，在它自己的 aarch64 内核上跑 Omarchy。安装程序从 Windows 里拉取 GPU 和 DSP 固件，在启动时挑正确的设备树，并让摄像头在桌面和 Chromium 里工作，同时在 mpv 和 Chromium 里做硬件视频解码。」**

**而 Phoronix 补了一句更直白的话**：

> **「Snapdragon 支持和其他 Linux 发行版一样，对大多数笔记本型号而言依赖于从 Windows 分区拉取固件。」**

**「从 Windows 里拉取 GPU 和 DSP 固件」。**

**我认为这是 ARM 笔记本上最反直觉的一个环节**：**你的 Linux 安装程序需要一台装了 Windows 的同型号机器（或者至少是同一台机器的 Windows 分区）来获取固件。** **而这些固件（GPU、DSP）恰恰是「能不能用」的关键**：**没有 GPU 固件，就没有硬件加速；没有 DSP 固件，摄像头和音频可能都不能用。**

**而发布说明里那句「在启动时挑正确的设备树」说明了第二个麻烦**：**ARM 机器没有 ACPI 那样的统一硬件描述，而是用设备树（DTB）。而不同型号的设备树不同，所以「一个镜像支持多台机器」意味着「镜像里要带多个设备树，并在启动时决定用哪个」。**

**而「摄像头在桌面和 Chromium 里工作」这条值得单独注意**：**因为摄像头在 ARM Linux 上一直是个难题**（它涉及 ISP 和复杂的管线），**所以「能用」这件事本身就是进展。**

### NVIDIA N1X：这次的上游支持相对好

**发布说明**：

> **「带 NVIDIA N1x 的 ASUS ProArt P14 和 Dell XPS 16 在 aarch64 的 Omarchy 内核和 NVIDIA 的开源驱动上跑 Omarchy。」**

**「NVIDIA 的开源驱动」（NVIDIA's open driver）。**

**这一条和我几天前写过的那台 RTX Spark 笔记本是同一类机器**。**而我当时的结论可以直接搬过来**：**NVIDIA 的官方驱动 README 写明「Blackwell 及之后的架构只被开源内核模块支持」**，**所以 N1X 用开源驱动不是选择，是唯一路径。**

**而这个「唯一路径」恰恰降低了移植难度**：**因为开源内核模块能跟内核 API 一起改，而不像闭源模块那样要等厂商适配。**

**但要注意：这台机器仍然需要「Omarchy 的 aarch64 内核」**，**也就是说它不是一个「发行版自带的内核就能跑」的情形**，**而是「发行版需要维护自己的内核」。** **这是 ARM 支持的实际成本。**

### Apple Silicon：合并 fork，但上游还不行

**发布说明对这一条写得很乐观，而 Phoronix 加了一个必要的限定**：

> **「Omarchy 也在把目光投向 Apple Silicon 支持，随着独立的 Omarchy Mac fork 被并入 Omarchy 本体。但上游的 Apple Silicon Linux 支持对较新的 M 系列硬件仍然差得远。」**

**「上游的 Apple Silicon Linux 支持对较新的 M 系列硬件仍然差得远。」**

**我认为这个限定很重要，因为它区分了两件事**：**「Omarchy 自己的代码准备好了」和「Linux 上游对 Apple Silicon 的支持够用了」。** **前者是发行版的工作，后者是内核社区（尤其是 Asahi Linux 项目）的工作。** **而后者不是 Omarchy 能决定的。**

**所以这条的正确读法是**：**「当上游准备好了，Omarchy 不需要再维护一个 fork」**，**而不是「Apple Silicon 现在能用了」。**

## 二、x86 侧的改动里，有三条我认为改变了日常体验

**这一版不只有架构扩展。我从发布说明里挑出三条我认为对日常使用影响最大的。**

### 启动时间：从 6 秒到 1 秒

> **「Limine 的菜单等待从大约六秒降到一秒，启动是静默的，而 binfmt 注册不再拖慢启动。启动时按任意键可以进入菜单。」**

**「菜单等待从约六秒降到一秒」。**

**这一条值得注意，因为它是「默认值就是个错误」的典型案例**：**六秒的菜单等待，绝大多数用户每次开机都在等它，而他们从来不用那个菜单。** **而改法很聪明**：**把等待降到一秒，但保留「按任意键进菜单」**，**所以需要菜单的人不受影响，而不需要的人省了五秒。**

**而「binfmt 注册不再拖慢启动」这条指向一个具体的技术细节**：**binfmt_misc 是内核里那个「按文件头决定用什么解释器」的机制**（**比如让 ARM 二进制在 x86 上通过 qemu 跑**）。**而注册 binfmt 处理器要写 `/proc/sys/fs/binfmt_misc/`，这个过程在启动时可能涉及等待。** **所以「不再拖慢」意味着他们找到了那个等待的来源。**

### 每显示器独立工作区

> **「`Super + 1-0` 现在会去你所在那个显示器的工作区，而每个显示器的 bar 只显示自己的。一个显示器每次插上都会拿回同样的工作区。」**

**「每个显示器每次插上都会拿回同样的工作区」（A monitor gets the same workspaces back every time it's plugged in）。**

**我认为这一条是纯实用改进，而它解决的问题很多人都有**：**在多显示器环境下，工作区编号到底是全局的还是每屏的？** **而 Hyprland 的默认行为是全局的，所以「切到工作区 3」在多屏下会产生歧义。** **改成每屏独立之后，`Super + 3` 的含义变得明确。** **而「插上后拿回同样的工作区」这一条解决的是另一个问题**：**拔掉再插上显示器时，工作区不要重排。**

### 通知系统重做，而它来自一个插件

> **「通知现在按发送者堆叠，你可以把它们延后（snooze）、打开勿扰（Do Not Disturb）、并回看历史。操作按钮、验证码和链接可以直接从卡片上工作，卡片跟随你的主题。来自同一发送者的相同通知会折叠成一个。这从 Omapager 插件长出来，而它现在是 Omarchy 内置的。」**

**「这从 Omapager 插件长出来，而它现在是 Omarchy 内置的」（This grew out of the Omapager plugin, which is now built into Omarchy）。**

**我认为这个演化路径值得单独指出**：**一个第三方插件被吸收成内置功能。** **这在发行版里是一种健康的模式**（**先让社区试，验证了再内置**），**而它的条件是这个发行版有一个活跃的插件生态。**

**而「验证码可以直接从卡片上工作」这条很具体**：**它意味着通知系统能识别「这条通知里有一个 OTP」，并提供一个复制按钮。** **这是个很小的功能，但它说明开发者自己在日常使用这个系统。**

## 三、50 种语言这一条，值得单独说

**发布说明把「Omarchy in 50 languages」列为第一个 highlight，而我认为这个排序是有道理的。**

> **「在 **Setup > Language** 下选一个语言，或者运行 `omarchy language <code>`。菜单、桌面和 Omarchy 的通知会立即切换，而系统 locale 在下次登录时跟上。」**

**「菜单、桌面和 Omarchy 的通知会立即切换，而系统 locale 在下次登录时跟上」。**

**这个「立即 vs 下次登录」的区分我认为很重要，因为它是一个诚实的技术界限**：**Omarchy 自己的部分（菜单、bar、通知）可以在运行时切换，因为它们是自己代码。** **而系统 locale 是 glibc 和环境变量的事，它需要重新登录才能完全生效**（**因为很多程序在启动时读取 locale 并缓存**）。

**而发布说明里没有说「支持 50 种语言」就完了**，**它在 Features 列表里补了两条具体的**：

> **「从安装程序加入日文、中文、韩文输入法」**
> **「改进日文、中文、韩文的设置」**

**「输入法」这一条我认为是关键**：**因为「界面翻译成中文」和「能输入中文」是两件完全不同的事**，**而后者需要 fcitx/ibus 这类输入法框架，以及在 Wayland 下正确配置。** **所以「从安装程序加入 CJK 输入法」意味着新用户装完就能输中文，而不是装完再去找教程配输入法。**

**而这个改动对中文用户的实际意义，比「界面有中文」大得多。**

## 四、一个我认为值得单独提的名字：omacom

**这一节不是技术内容，但我认为它值得记一笔。**

**Phoronix 的报道里链接到 `github.com/omacom/omarchy`，而我实测确认仓库确实从 `basecamp/omarchy` 迁到了 `omacom/omarchy`**（**`full_name` 现在是 `omacom/omarchy`，stars 45,355，forks 5,608**）。

**「omacom」这个组织名的含义我认为是很清楚的：Omarchy 从 Basecamp 的项目变成了一个独立的组织。** **而这是一个发行版成熟的标志之一**：**当一个项目从「某公司的内部项目」变成「一个有自己的组织名的项目」时，它的治理结构变了。**

**而这对用户的实际影响是**：**它降低了「这个发行版会不会因为某公司的商业决定而消失」这个风险。** **而 Omarchy 之前的定位是「DHH 的 Arch 配置」，而这个转向说明它已经超出了那个定位。**

**顺带说一句仓库数据**：**45,355 stars、5,608 forks、主语言 Shell、MIT 许可、2025-06-01 创建。** **一个一年半的项目做到这个量级，而它的主语言是 Shell**（**因为它的核心是一堆配置脚本，不是编译出来的软件**）。**这个组合本身就说明了这类「配置型发行版」的传播力。**

## 五、我的判断

**第一，这一版最值得学的不是「支持了 aarch64」，而是「它怎么处理 aarch64 的碎片化」。** **因为 ARM 笔记本的根本问题是：每台机器的固件、设备树、GPU 驱动都不同，所以「支持一个架构」在实践中等于「支持一批具体型号」。** **而 Omarchy 的做法是「维护一个自己的 aarch64 内核 + 每类机器一套适配逻辑」**：**Snapdragon 走「从 Windows 拉固件 + 启动时选设备树」，N1X 走「NVIDIA 开源驱动」，Apple Silicon 走「合并 fork + 等上游」。** **这三种做法的共同点是：它们都不是「通用的」，而是「针对性的」。**

**第二，「三个生态同时跑起来」这件事的技术含量，比 Phoronix 那篇报道呈现的更高。** **因为 Phoronix 的篇幅有限，它只列了机型。而实际的差异是**：**高通那两台需要固件提取和设备树选择；NVIDIA 那两台需要开源内核模块和自维护内核；Apple Silicon 需要等上游。** **这三条路上的每一步都需要有人实际在硬件上测试，而发布说明里明确写了测试机型**，**这意味着这些不是「理论上支持」，是「测过」。**

**第三，我认为这版里对普通用户影响最大的是那条「启动从 6 秒到 1 秒」，而它最容易被忽略。** **因为架构扩展是「新闻」，而启动速度是「体验」。** **而六秒到一秒这个改动有一个很聪明的设计**：**它没有删掉菜单，而是把「等待」改成「按任意键」。** **也就是说，它假设「绝大多数人不需要菜单」，同时不牺牲「需要菜单的人」。** **而这类改动的价值在于它每天生效**，**而不是像架构支持那样只在买新机器时才相关。**

**第四，关于「要不要试」，发布说明自己的警告写得比我说的都好，我直接引用**：

> **「**⚠️ 这是一个发布候选版，不是最终版本。** 预期会有 bug、粗糙的边缘，以及偶尔直接坏掉的东西。在一台测试机上跑它，或者在升级一台你依赖的机器之前，确保你有一个能用的备份（或者一个你知道怎么回滚的快照）。」**

**「一个你知道怎么回滚的快照」（a snapshot you know how to roll back to）。** **这个括号里的限定比前半句更重要**：**「有备份」和「知道怎么回滚」是两件事。** **而在一台跑着滚动发行版的机器上，后者才是真正的保险。**

**而 RC 的试用路径也给了，我认为这个设计值得注意**：

> **「在已有的机器上试用：`Update > Channel > RC`，然后 `Update > Omarchy`。」**

**也就是说：它把「切到 RC 频道」做成了一个可逆的开关**，而不是「重新装一遍」。**这降低了试用的成本**，**而这是「让用户帮你测」的正确做法。**

> **最后一个观察，关于这次发布的 ISO**：**它给了两个架构的 ISO 和各自的 SHA256**：
>
> **x86_64**：`omarchy-4.5.0rc1.iso`，SHA256 `fd8e39f6eca395315328dd12208cc0c324aaf067dc391aa2b476c166ed0f8718`
> **aarch64**：`omarchy-4.5.0rc1-aarch64.iso`，SHA256 `c5ef83d04cad34deb074583b53b3cce9c5c42e8f18e0f6ab78313e30916adb28`
>
> **而这里有一个我认为值得注意的细节：aarch64 的 ISO 是一个，而不是三个。** **也就是说：同一个镜像要覆盖 Snapdragon、N1X、Apple Silicon 这三类机器。** **而这意味着那个镜像里必须包含多套设备树和多个 GPU 驱动，并在启动时决定用哪一套。** **这就是「一个 ISO 支持三类 ARM 机器」在工程上真正意味着什么。**

## 关键事实速查

| 项目 | 内容 |
|---|---|
| **版本** | **Omarchy 4.5.0-rc1**，**2026-10-20 08:54 UTC** 发布，**prerelease = true** |
| **定位** | **「自 Quattro 以来的第一个特性版本」**（the first feature release since Quattro） |
| ⭐ **仓库已迁移** | **从 `basecamp/omarchy` 迁到 `omacom/omarchy`**；**45,355 stars / 5,608 forks**；主语言 **Shell**；**MIT**；创建于 **2025-06-01** |
| ⭐ **AArch64 支持的三类机器** | **① Snapdragon X：Lenovo Yoga Slim 7x、ThinkPad T14s**；**② NVIDIA N1X：ASUS ProArt P14、Dell XPS 16**；**③ Apple Silicon：合并 Omarchy Mac 铺路** |
| ⭐ **Snapdragon X 的实现细节** | **「安装程序从 Windows 里拉取 GPU 和 DSP 固件，在启动时挑正确的设备树」**；**摄像头在桌面与 Chromium 里工作**；**mpv 与 Chromium 里硬件视频解码** |
| **Snapdragon 的固件限制** | **「对大多数笔记本型号而言依赖于从 Windows 分区拉取固件。」**（Phoronix） |
| **NVIDIA N1X 的实现** | **「在 aarch64 的 Omarchy 内核和 NVIDIA 的开源驱动上跑」** |
| **Apple Silicon 的现状** | **「Omarchy Mac 过去是一个独立 fork。它共享的硬件和桌面支持现在活在 Omarchy 本身里」**；**「只有它们的启动设置留在 Omarchy Mac 的包里」** |
| ⚠️ **Apple Silicon 的限定** | **「上游的 Apple Silicon Linux 支持对较新的 M 系列硬件仍然差得远。」**（Phoronix） |
| ⭐ **启动时间** | **「Limine 的菜单等待从大约六秒降到一秒，启动是静默的，而 binfmt 注册不再拖慢启动。启动时按任意键可以进入菜单。」** |
| ⭐ **每显示器工作区** | **「`Super + 1-0` 现在会去你所在那个显示器的工作区，而每个显示器的 bar 只显示自己的。一个显示器每次插上都会拿回同样的工作区。」** |
| ⭐ **通知系统重做** | **按发送者堆叠、可延后、勿扰模式、历史回看**；**操作按钮、验证码、链接可直接从卡片工作**；**相同通知折叠**；**「这从 Omapager 插件长出来，而它现在是内置的」** |
| **浮动工作区与 dock** | **`Super + L` 在 dwindle 平铺、滚动、浮动之间循环**；**bar 显示每个工作区用哪种布局**；**浮动工作区里窗口带标题栏 + dock 显示固定应用与全部应用**；**`Super + M` 最小化到 dock** |
| ⭐ **国际化** | **「Omarchy in 50 languages」**；**`Setup > Language` 或 `omarchy language <code>`**；**「菜单、桌面和 Omarchy 的通知会立即切换，而系统 locale 在下次登录时跟上」** |
| **CJK 相关** | **「从安装程序加入日文、中文、韩文输入法」**；**「改进日文、中文、韩文的设置」** |
| **新内置应用** | **Elsewhen（世界时钟，`Super + Ctrl + Alt + E`）**；**视频壁纸与主题开场动画**（由 OWE 播放）；**Quake 风格控制台**（`Super + Grave`） |
| **其他值得注意的功能** | **Kimi 与 Ori 加入默认编码 agent**；**可在多个 Claude 与 Codex 订阅之间切换**；**安装器内置 Slack 与 Microsoft 365 网页应用**；**`Super + Shift + S` 截图**；**可选 SSH Agent 服务** |
| **性能改进** | **主题切换大幅加速**；**菜单、面板、媒体键加速**；**桌面改为响应变化而非轮询**；**bash 提示符提前约 30 ms** |
| ⭐ **RC 警告（官方原文）** | **「这是一个发布候选版，不是最终版本。预期会有 bug、粗糙的边缘，以及偶尔直接坏掉的东西。在一台测试机上跑它，或者在升级一台你依赖的机器之前，确保你有一个能用的备份（或者一个你知道怎么回滚的快照）。」** |
| **试用方式** | **已有的机器：`Update > Channel > RC`，然后 `Update > Omarchy`** |
| **ISO（x86_64）** | **`omarchy-4.5.0rc1.iso`**；SHA256 **`fd8e39f6eca395315328dd12208cc0c324aaf067dc391aa2b476c166ed0f8718`** |
| **ISO（aarch64）** | **`omarchy-4.5.0rc1-aarch64.iso`**；SHA256 **`c5ef83d04cad34deb074583b53b3cce9c5c42e8f18e0f6ab78313e30916adb28`** |
| **上一个稳定版** | **v4.0.6**（2026-10-19）；**v4.0.5**（2026-10-18） |

## 延伸阅读

- [为了省下 62 毫秒，Omarchy 用 Claude Code 重写了一个 XDG 脚本：这个数字比它看起来重要](https://freelamp.com/articles/2026-10-19_omarchy-browser-launch-xdg-optimization/)
- [为了让这台 128GB 的 RTX Spark 笔记本跑 Linux，她自己写了 ACPI 覆盖和触控板补丁](https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/)
- [ACPI 覆盖到底怎么做：从作者的仓库里拆出完整流程](https://freelamp.com/articles/2026-10-19_acpi-table-override-guide-initrd-cpio/)
- [OpenBSD 8.0 发了：而这次最值得看的不是漏洞修复清单，是内核虚拟地址空间从 4G 跳到 512G](https://freelamp.com/articles/2026-10-20_openbsd-8-0-release-kernel-address-space/)
- [Phoronix 原文（一手）](https://www.phoronix.com/news/Omarchy-4.5-RC1)
- [Omarchy v4.5.0-rc1 发布说明（一手，含完整功能列表）](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc1)
