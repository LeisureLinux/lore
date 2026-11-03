---
title: "FreeRDP 3.33：RDP 跑进浏览器，以及一个开源项目被 AI PR 淹没的现场"
date: 2026-11-03
slug: freerdp-3-33-wasm-ai-prs
tags: [FreeRDP, RDP, WebAssembly, WASM, Emscripten, SDL3, RemoteApp, RAILS, UDP, 多传输, ShadowServer, 剪贴板, macOS, VideoToolbox, WebCodecs, Opus, AI代码, 开源治理, LinuxFoundation, AIslop, 安全公告, GHSA, CVE, CVSS, OpenSSH, MITRE, 技术解读]
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：FreeRDP 官方 GitHub Release 3.33.0（2026-11-02）+ freerdp.com 官方发布博客 + 仓库 ChangeLog + GitHub API 提交/比较/安全公告数据 + Phoronix 原文"
original_date: 2026-11-02
original_url: "https://www.phoronix.com/news/FreeRDP-3.33"
description: "本文解读 FreeRDP 3.33（2026-11-02 发布）的两条主线：一条是技术上的 —— RDP 客户端第一次可以编译成 WebAssembly 跑在浏览器里（SDL3 客户端 + Emscripten + WebCodecs 解 AV1/H.264 + Web Audio 麦克风 + 浏览器剪贴板 + WebAssembly SIMD），以及 UDP 直连、Unicode 键盘管道、Windows shadow server 复活、macOS 免 FUSE 文件剪贴板；另一条是治理上的 —— 官方发布公告罕见地写下「PR 和 bug 反馈的涌入非常大，很快会发一个补丁版」，这是 AI 生成 PR 淹没开源维护者的一手现场证据。文中用 GitHub API 实测数据做交叉验证：3.33.0 距上一版 3.32.2 有 748 个 commit（对比 3.31.0→3.32.0 是 476、3.32.1→3.32.2 是 290），新增 20 位首次贡献者，仓库内 Assisted-by 标记仅 2 处。本文明确标注：发行说明列出的 13 条 GHSA 安全公告在官方发布当天尚未公开（GitHub 与 freerdp.com 都注明「Advisories will be published days/weeks after the release, so links are 404 until then」），因此**不列 CVE 编号、不评严重度**，并用同期已公开的 FreeRDP CVE 做背景对照（CVE-2026-110837 / CVE-2026-111880 / CVE-2026-109242）。"
published: true
---

> **原文**：Phoronix《FreeRDP 3.33 Released With WebAssembly Support, Huge Influx Of Activity Due To AI》，Michael Larabel，2026-11-02
> 原文链接：<https://www.phoronix.com/news/FreeRDP-3.33>
> **本文不是新闻转述** —— 下面每个数字都来自一手核对：FreeRDP 官方 GitHub Release 3.33.0、freerdp.com 官方发布博客、仓库 `ChangeLog`、以及 GitHub API 的提交/比较/安全公告端点。

## 先说结论

1. **FreeRDP 3.33 是一个「大功能」版本**，官方原话是 *"Major feature release, accompanied by the usual bugfix and CVE fixes"*。七项主要变化里，**WebAssembly 支持是最大的一条** —— RDP 客户端第一次可以编译成 WASM 跑在浏览器里。
2. **但真正值得单独一篇文章的，是公告最后那一句**：*"The influx of pull requests and feedback for bugs/regressions/... was huge, so we will do a patch release with all the papercuts and bug still in the backlog soon."* —— ⭐ **这是 AI 生成 PR 淹没开源维护者的一手现场证据，而且它出现在项目自己的官方公告里。**
3. **13 条安全公告在发布当天全部未公开**。GitHub 与 freerdp.com 都明确说明：*"Advisories will be published days/weeks after the release, so links are 404 until then."* ⭐ **因此本文不列 CVE 编号、不评严重度 —— 那些信息此刻客观上不存在。**
4. **发布密度本身就能佐证「涌入」这个说法**：3.33.0 距上一版 3.32.2 只有 **21 天**，中间还夹着 3.32.1 和 3.32.2。

## 一、WebAssembly：RDP 终于进了浏览器

官方公告的第一条就是它：

> *webassembly support, now can run from within your browser*

### 这不是「把 GUI 编译到 WASM」那么简单

⭐ 但要说清这件事的份量，得先看它背后的工程量 —— 因为 FreeRDP 为了这一天铺了好几年。

**第一步：让 winpr 和 libfreerdp 能编译成 Emscripten。**

据 FreeRDP 社区讨论 #13626（2026-10-07）的梳理，这条路是分两步走的：

> *winpr and libfreerdp compile with Emscripten (feat(emscripten): add support for emscripten compilation #8208), and the pollset yields so socket events get through ([winpr,synch] Yield after a poll timeout in emscripten #11929, [winpr,synch] Fix starvation in pollset_poll caused by emscripten_sleep #11962).*

⭐ **注意 `#11929` 和 `#11962` 这两个编号** —— 分别是 11929 和 11962，远早于本轮 13xxx 的 PR 序列。**换句话说，「能不能在浏览器里跑」这件事本身，FreeRDP 从三年前就开始铺路了。**

而且那位社区成员在 2026-10-07 明确写道：

> *There is no client front end, build script, documentation or CI for the Emscripten target in the tree.*

⭐ **所以 3.33.0 真正带来的，是把这套「已经能编译」的东西补齐成「有前端、有构建脚本、有文档、有 CI」的产品。**

### 第二步：浏览器里缺的每一块都要自己补

⭐ **这一段是整篇文章里我最想展开的技术细节 —— 因为它解释了「为什么 RDP 进浏览器」比「跑个 WASM demo」难得多。**

⭐ 浏览器不是操作系统。它缺的东西，FreeRDP 一个一个补齐了：

| 缺什么 | FreeRDP 的解法 | 对应 PR |
|---|---|---|
| **窗口渲染** | SDL3 支持 Emscripten，渲染到 canvas | #13728（Emscripten CI job）|
| **视频解码** | 走浏览器原生 **WebCodecs**，AV1 与 H.264 各一个后端 | #13731（AV1）、#13812（H.264）|
| **麦克风** | **Web Audio** 后端 | #13811 |
| **音频播放** | **Web Audio** 后端 | #13732 |
| **剪贴板** | 浏览器剪贴板 API | #13733 |
| **多显示器** | 页面可把 canvas 切成多个显示器区域 | #13865 |
| **同步原语** | 用 `MessageChannel` 向浏览器让出执行权 | #13864 |
| **计算加速** | 用 **WebAssembly SIMD** 跑 primitives | #13893 |
| **NAL 解析加固** | 加固 emscripten NAL parser | #13941 |

⭐ **而这里最值得单独说的是 WebCodecs 那两笔。**

⭐ 因为按社区成员 #13626 的说法，他原本的设想是「在 `libfreerdp/codec/av1.c` 里加一个 WebCodecs 后端」，但他实测之后改了主意 —— **因为浏览器自己就有解码器，根本不需要把解码器也编进 wasm**：

> *I tested Chrome 154 on Windows with real AV1 keyframes: 4:2:0 decodes to `I420` and 4:4:4 (High profile) decodes to `I444` with exact chroma, so `/gfx:AV1:i444` would work in the browser with no decoder shipped in wasm.*

⭐ **这是一个很漂亮的架构判断**：**不要把浏览器已经有的东西重新塞进 wasm。**

⭐ 而且这一笔还顺手修了一个已有的 bug —— PR #13561「[codec,av1] fix colours of decoded YUV444 frames」，正是为 4:4:4 色彩修复。

### 第三步：那个绕不开的「浏览器不能开 TCP」

⭐ 这是整件事最实际的约束，而且**官方仓库没有解决它** —— 解决它的是社区。

据 `congzhangzh/freerdp-web`（2026-10-31）的说明：

> *A browser cannot open TCP connections, so the page talks to the RDP server through a WebSocket gateway, websockify.*

⭐ **也就是说：FreeRDP 3.33 给你的是「能编译成 WASM 的客户端」，而不是「一个能用的浏览器远程桌面」。** 真正的产品形态还需要一个 WebSocket-to-TCP 网关。

⭐ 而这个社区项目还顺手解决了一个我没想到的问题 —— **WASM 的执行模型**：

> *Where the browser has WebAssembly's JavaScript Promise Integration (JSPI, Chrome and Edge 137+), the page runs a build of the client made for it; other browsers get the Asyncify build. Asyncify rewrites nearly every function so the stack can be unwound and rewound around each wait; JSPI suspends inside the engine and leaves the code as compiled.*

⭐ **Asyncify 会重写几乎每一个函数，让栈能被展开和卷回；JSPI 则是在引擎内部挂起，代码保持编译后的形态。** 同一个 FreeRDP，两种链接方式，除此之外什么都不差。

⭐ **这是 WebAssembly 生态目前最实质的一个性能分歧 —— 而它会随着浏览器普及慢慢消失。**

### 顺带一提：Android MediaCodec 也来了

⭐ PR #13915「[codec,video] add android mediacodec support」和 #13706「[codec,channels] guard new Android MediaCodec/AAudio APIs behind their introduced-in level」—— ⭐ **同一个思路：能用平台原生能力就别自己实现。**

⭐ 这与 WebCodecs 那笔是同一个哲学，只是从浏览器换到了 Android。

## 二、其余六项功能，逐条说清边界

⭐ 我按官方公告的顺序来，但**每条都补上「它到底意味着什么」**，因为公告本身的措辞非常克制。

### 1. SDL 客户端 RAILS 改进

> *improved SDL client RAILS*

⭐ **RAILS = RemoteApp**（RemoteApp Integrated Locally Software），微软的「远程应用」技术：远程服务器上跑的是完整应用，不是桌面，客户端只拿到一个窗口。

⭐ 3.33 里的 RAILS 改动量非常大，看 PR 列表就能感受到 —— 这几乎是重写了一遍：

- **Windows 客户端支持 RemoteApp**（#13855）—— ⭐ **在此之前 RemoteApp 基本是 Windows 服务器 + Windows 客户端的事，这一笔把跨平台客户端打开了**
- 窗口位置、大小、最小化修复（#13897）
- 多显示器下的 RemoteApp 修复（#13857）
- 把激活点击传给 RemoteApp 窗口（#13853）
- 保留非激活的 RAIL 弹窗为弹窗（#13758）
- 延迟执行 RemoteApp 前先初始化客户端状态（#13696）
- 永远不激活 `WS_EX_NOACTIVATE` 窗口（#13977）
- 父窗口消失时保留弹窗（#13914）

⭐ **而 PR #13729 和 #13745 更有意思：SDL 客户端把「连接对话框」搬回来了，还允许把它关掉。** ⭐ 换句话说，SDL 客户端从「一个纯命令行玩具」向「一个正经 GUI 客户端」演进。

### 2. UDP 直连（实验性）

> *experimental UDP support for direct (without gateway) RDP connections*

⭐ **这是微软 RDP 的 UDP 传输通道（也叫「RDP UDP transport」），10 月 2018 年随 Windows 10 1809 引入**，作用是：在丢包网络里，把图形/视频流从 TCP 挪到 UDP 上，用前向纠错（FEC）重传，从而把「花屏」变成「轻微模糊」。

⭐ 3.33 里对应的 PR 是 #13608「[core,multitransport] client side UDP multitransport」。

⭐ 而配套的 #13823 值得单独说：

> *[core,multitransport] UDP multitransport is opt-out with /multitransport:tcp-only*

⭐ **默认开启，但可以一行参数退回纯 TCP。** ⭐ 我认为这个默认值是对的 —— 因为 UDP 多传输在丢包网络里确实能显著改善体验，而在干净网络里它带来的额外握手开销几乎不可见。

⭐ **而「direct (without gateway)」这个限定词很重要**：⭐ **这条 UDP 通道只在直连时可用；走 RD Gateway 时用不了。** 这是一条容易被媒体标题掩盖的边界。

### 3. Unicode 键盘输入管道（所有客户端）

> *unicode keyboard input pipe now supported by all clients (on systems that support mkfifo unix style pipes)*

⭐ 这个功能的技术形态是：**用一个 unix FIFO 把按键事件喂给客户端。**

⭐ **而它为什么重要，看看这几个 PR 就明白了：**

- #13842「Common unicode from pipe」—— ⭐ **这就是「所有客户端」的含义：把 Unicode 输入从某个特定客户端的实现，提升为通用能力**
- #13851「Unified unicode kbd」
- #13846「winpr/input: Add API to check whether keyboard type is supported」
- #13715「[client,x11] Send Backspace and Delete as scancodes in Unicode mode」
- #13707 / #13739 / #13742「deferred alt forwarding」—— ⭐ **Alt 键的「延迟转发」：在 X11 下按 Alt 会触发窗口管理器菜单，所以客户端改成延迟一小会儿再转发给远端**
- #13825「[libfreerdp, locale] Fix incorrect XKB key name for the Korean Hanja key」

⭐ **我最喜欢 #13825 这个例子** —— ⭐ 一个 Unicode 键盘管道的副作用，是修了一个「韩文 Hanja 键的 XKB 键名写错了」这种极其具体的 bug。**这类 bug 只有在真正把 Unicode 输入走通之后才会暴露出来。**

### 4. Windows Shadow Server 复活（实验性）

> *experimental windows shadow server support. It is back from the dead!*

⭐ **Shadow Server 是 FreeRDP 的服务端实现：把本机屏幕抓成 RDP 画面流给客户端，用于远程协助、演示、监控。**

⭐ 官方文档描述它的能力：

> *Captures the host display (X11, Windows, macOS) using a platform-specific subsystem; Encodes frames using RemoteFX, H.264, or GFX; Streams to one or more simultaneous RDP clients; Forwards client keyboard and mouse input back to the host; Supports a lobby mode while waiting for the first viewer; Optionally requires authentication (SAM database or PAM).*

⭐ **而 3.33 的 Windows 后端改动量非常可观：**

- #13892「Win backend: crash fixes found in production, capture cadence and GFX dirty-region encoding」—— ⭐ **「在生产环境中发现的崩溃修复」这句话信息量很大：说明这个后端已经被真实用过了**
- #13894「win_shadow_enum_monitors: use the first attached display adapter」
- #13907「follow encoder preferred fps in capture loop」
- #13932「use AuthenticateEx in the WDS client」
- #13933「DXGI capture: a build option, and follow the secure desktop」—— ⭐ **「跟随安全桌面」意味着它能抓到 UAC 提权对话框**
- #13931「make SHADOW_MSG_OUT refCount a LONG」
- #13923「fix memory leak about s in rdpdr_send()」

⭐ **而「It is back from the dead!」这句话是官方自己写的** —— 说明这个后端曾经被移除过。**「复活」意味着它还不该被信任到生产用，但已经从「不可用」进到「可以试」。**

### 5. macOS 文件剪贴板免 FUSE

> *mac OS file clipboard support without FUSE (all clients)*

⭐ 对应 PR #13591「[client,sdl] file copy and paste between the macOS Finder and the server」。

⭐ **而这背后是 FreeRDP 的一整条「逐步摆脱 FUSE」路线：**

- #13633「[winpr,client,sdl] Windows clipboard: image conversion, BMP layout, UTF-8 text」
- #13714「[winpr,clipboard] fix FileGroupDescriptorW to file list conversions」
- #13734「fix HTML synthesizer destination format checks」
- #13930「tolerate a malformed FAIL response」

⭐ **为什么摆脱 FUSE 值得单独说**：⭐ **FUSE 是用户态文件系统，通常需要额外的内核扩展授权（macOS 上则是第三方驱动）。** 对一个要在 macOS 上做企业远程桌面的工具来说，「免 FUSE」意味着**不再需要用户装驱动、不再需要系统重启、不再触发安全审批**。⭐ 这是从「能用」到「能部署」的差别。

### 6. 消息翻译的初步支持

> *Initial support for translation of messages*

⭐ 对应 PR #13367「[winpr] add optional translation helpers」，还有 #13902「Cf locale clip」。

⭐ **注意官方用词是 "Initial"（初步）** —— 这是一个基础设施性的 PR，翻译机制刚落地，具体语言包还在路上。⭐ **而对中文用户来说，这条值得持续关注：⭐ RDP 客户端的界面文本翻译，一直是「远程桌面能用但不好用」的一个真实痛点。**

## 三、⭐⭐ 真正的新闻：官方公告自己承认被 PR 淹了

⭐ 现在说这一篇里我认为最重要的部分。

### 官方原话

FreeRDP 3.33.0 的发布公告，在列完七项功能之后，写了这么一段：

> *The influx of pull requests and feedback for bugs/regressions/... was **huge**, so we will do a patch release with all the papercuts and bug still in the backlog soon.*

⭐ **注意几个用词**：**"influx"（涌入）、"huge"（巨大）、"papercuts"（小毛病）、"bug still in the backlog"（还堆在 backlog 里）**。

⭐ **这是一个项目维护者在自己的官方公告里，公开承认「我们被送来的东西淹了」。** ⭐ 我认为这在开源项目的发布公告里相当罕见 —— 通常这种话会出现在私下的 issue 讨论、或者维护者的博客里，而不是发布博客。

### 用 GitHub API 实测：这次发布到底有多大

⭐ 我不打算只引用这句话，而是用 GitHub API 把数据拉出来对比：

| 版本区间 | 区间跨度 | commit 数 | 数据来源 |
|---|---|---|---|
| 3.31.0 → 3.32.0 | 28 天 | **476** | `compare/3.31.0...3.32.0` |
| 3.32.0 → 3.32.1 | 5 天 | **112** | `compare/3.32.0...3.32.1` |
| 3.32.1 → 3.32.2 | 14 天 | **290** | `compare/3.32.1...3.32.2` |
| **3.32.2 → 3.33.0** | **21 天** | **748** | `compare/3.32.2...3.33.0` |

⭐ **748 个 commit，是上一次大版本（476）的 1.57 倍，是中间那个补丁版（290）的 2.58 倍。**

⭐ 而 3.33.0 的 release note 里，**"New Contributors" 一节列了 20 位首次贡献者**：

> *@huangzheng2016 … @consolomets … @espentveit … @wpyoga … @jlabrous … @himamaheswarreddy … @veZuk … @ruimya … @jgrulich-rh … @jb-alvarado … @diogochaves … @golinku … @justussc … @giladchen-dev … @murrant … @w4ffl35 … @caomengxuan666 … @skynit … @Syh-Xiong … @nootone*

⭐ **「首次贡献者占 PR 数量的比例」，是判断「PR 涌入」最直接的指标之一。** 一个维护稳定多年的 C 项目，在一次大版本里出现 20 位新面孔，本身就说明提交门槛被大幅拉低。

### 但我要小心：不能把「AI 导致」当成已证事实

⭐ **这是本文最需要克制的地方。** ⭐ 官方公告说的是「PR 涌入很大」，**并没有说这是 AI 造成的**。⭐ 事实上，同一天 Phoronix 还有另一篇文章《Radeon RADV Vulkan Driver Adopts An LLM Policy》，讲的是 Mesa 的 RADV 驱动开始写自己的 LLM 贡献规范 —— ⭐ **两件事发生在同一天，这不是巧合，但也不是因果证明。**

⭐ **所以我只能说：⭐ FreeRDP 的公告没有点名 AI，而同期 Linux Foundation 的调研给出了行业层面的量化背景。**

### Linux Foundation 的行业数据（2026-10-20 发布）

⭐ Linux Foundation Research 发布的《Navigating Open Source Software Development in the Generative AI Era》报告里：

- **平均 25% 的 incoming PR 被认为是 low-quality "AI slop"**（低质量 AI 生成贡献）
- **大型项目这一比例达到 31%**
- **64% 的维护者报告审查周期延长，并把 burnout（倦怠）列为首要担忧**
- 59% 的维护者报告 AI 带来的贡献量在增长
- GenAI 让 OSS 各类开发任务的编码时间**最多减少 50%**
- 71% 的维护者认为 GenAI 降低了参与门槛
- 只有 **35%** 的项目有正式允许 GenAI 使用的政策，**32%** 完全没有政策或没打算制定

⭐ **而 FreeRDP 这件事，恰好是这份报告里那三个数字的完美注脚：**

| LF 报告的发现 | FreeRDP 3.33 的对应 |
|---|---|
| 25% PR 是 AI slop | 21 天 748 commit、20 位首次贡献者 |
| 64% 维护者审查周期延长、倦怠 | 官方公告自己写「很快会发补丁版清 backlog 里的小毛病」 |
| 只有 35% 项目有 AI 政策 | ⭐ **FreeRDP 全仓库 `Assisted-by` 标记只有 2 处** |

### ⭐ FreeRDP 自己的 AI 标记只有 2 处 —— 这才是问题所在

⭐ 我用 GitHub commit search 查了 FreeRDP master 分支的 `assisted-by`：

```
5854cbaeb  [client,sdl] stop drawing when update queue is empty, helps CPU   2026-07-30
1f9e8a8a1  [channels,rdpecam] fix DeviceAdded notification for non-ASCII …  2026-07-03
```

⭐ **整个仓库只有 2 个 commit 带 `Assisted-by:` 标签。** ⭐ 而同期 Linux 内核那边，**2026-10-14 有个 commit 把 `Assisted-by` 的要求从内核文档里删掉了**（据 P.K. Sharma 的核查）。

⭐ **对比一下这个数字：**

- **748 个 commit 的发布周期**
- **20 位首次贡献者**
- **2 处 `Assisted-by` 标记**

⭐ **我的判断是：⭐ 涌入是真的，但是否主要由 AI 生成，现有公开证据无法判定。** ⭐ 而「2 处标记」这个事实本身提示了另一种可能 —— ⭐ **如果贡献者真的用了 AI 辅助却没人标注，那问题就不是「AI slop」，而是「无法区分」。**

⭐ 而这恰恰是 RADV 那份新政策在试图解决的问题 —— Samuel Pitoiset（Valve）写得很清楚：

> *LLM-assisted MRs require a good understanding of the codebase, and reviewing them has a real cost. Reviewers/maintainers may close such MRs at their discretion. LLM-written issues are discouraged: they tend to be verbose and hard to read. Please describe the issue in your own words. LLM-generated reproducers are fine as long as you have reviewed them and they demonstrate the bug.*

⭐ **注意最后一句的分寸**：⭐ **复现程序（reproducer）可以用 LLM 生成，只要你自己验证过它确实复现了这个 bug。** ⭐ **这才是关键 —— 要的不是「不许用 AI」，而是「用的人要对结果负责」。

⭐ **而 Mesa 上层的政策是同一个方向**：⭐ 允许 AI 生成的代码，但提交者必须理解并为之负责（2025-09-19 的 Mesa Contributor Guidelines）。

## 四、⭐ 关于 13 条安全公告：本文不列 CVE，也不评严重度

⭐ **这一节我必须写得很克制，因为这是事实边界最容易滑过去的地方。**

### 官方说法

3.33.0 的 release note 列出了 13 条 GitHub Security Advisory 链接。⭐ **但这些链接在发布当天全部 404。**

⭐ 而且官方在 3.32.0 的发布博客里就已经预先打过招呼：

> *Note: Advisories will be published days/weeks after the release, so links are 404 until then.*

⭐ 我实测确认了这一点：

- `https://github.com/FreeRDP/FreeRDP/security/advisories/GHSA-hhfh-fvm7-7w65` → **HTTP 404**
- GitHub API `repos/FreeRDP/FreeRDP/security-advisories`（翻完 5 页 500 条）→ **13 个 GHSA ID 一个都没有**
- 全局 advisories API `api.github.com/advisories/GHSA-...` → **同样 Not Found**

⭐ **所以此刻客观存在的事实只有：⭐「3.33.0 修复了 13 条已被内部确认的安全问题，具体是什么、有多严重，尚未公开。」**

⭐ **不写 CVE 编号、不写 CVSS、不评「高危/中危」—— 因为那些数字此刻并不存在。** ⭐ **这不是谨慎过头，而是事实边界：把「未公开的 13 条」渲染成「13 个高危 CVE」，是二手报道最常见的一种失真。**

### 但同期已公开的 FreeRDP CVE，能说明这个项目的攻击面有多大

⭐ 作为背景对照（**这些是 3.32.0 / 3.32.1 / 3.32.2 修复的，不是 3.33.0 的**），我从 NVD 拉到了三条：

| CVE | CVSS | CWE | 一句话描述 |
|---|---|---|---|
| **CVE-2026-111880** | 7.4 HIGH | CWE-787 | 服务端 NTLM 路径未校验 MIC offset，导致堆越界写。**未认证攻击者**可发构造的 AUTHENTICATE_MESSAGE |
| **CVE-2026-110837** | 7.1 HIGH | CWE-122 | `WITH_LAME=ON` 且 `WITH_DSP_FFMPEG=OFF` 构建时，`freerdp_dsp_decode_mp3` 里右声道 PCM 指针偏移量按 short 计算，堆溢出 |
| **CVE-2026-109242** | 7.1 HIGH | CWE-908 | progressive tile 的 `tile->current` 缓冲区分配时未清零，**恶意 RDP 服务器**可让客户端渲染未初始化的堆内存 |

⭐ **这三条有一个共同点值得注意：⭐ 攻击面主要在「服务端 / 恶意服务器 → 客户端」这个方向。**

⭐ **而这跟 3.33.0 恰好有一个尴尬的对照：⭐ 这一版主推的是「让更多客户端去连更多服务端」—— ⭐ 包括浏览器里的客户端。⭐ 而 FreeRDP 自己的历史 CVE，反复证明的正是「客户端连上恶意服务端」这条路径。**

⭐ **我没有要危言耸听的意思** —— ⭐ 我只是想说：⭐ **一个 RDP 实现的价值，很大程度上取决于它在「面对恶意对端」时是否稳固；而 3.33 恰好把「能连多少种对端」大幅扩张了。** ⭐ **扩功能与加固，两件事必须同时做 —— 而 FreeRDP 在这一点上有做得很好的历史记录（3.32.0 那次发布就带了 60 条安全公告链接）。**

### 顺带：发布密度本身是安全响应的信号

⭐ 我注意到 FreeRDP 最近四次的发布节奏：

| 版本 | 发布日期 | release note 里的安全公告链接数 |
|---|---|---|
| 3.31.0 | 2026-08-26 | — |
| 3.32.0 | 2026-09-23 | **60** |
| 3.32.1 | 2026-09-28 | **6** |
| 3.32.2 | 2026-10-12 | **45** |
| **3.33.0** | **2026-11-02** | **13** |

⭐ **⭐ 四次发布、124 条安全公告、40 天。** ⭐ 3.32.0 的官方博客有一句话：

> *There have also been lots of issues addressed to harden against protocol violations/exploits, thanks to all the people doing in depth code reviews and security reports.*

⭐ **「感谢所有做深入代码审查和安全报告的人」** —— ⭐ 而 3.32.2 的 ChangeLog 写得更直白：

> *We've been under close scrutiny by various security researchers. Addressing their findings we've hardened the code base considerably against malicious client and/or server messages.*

⭐ **「we've been under close scrutiny」—— 被密切审查。** ⭐ **这个措辞说明 FreeRDP 已经成为安全研究者的密集目标。**

⭐ **而这带出一个很实际的部署建议：⭐ 如果你在生产环境用 FreeRDP，⭐ 3.33.0 不该是「尝鲜版」，而应该是「跟着 3.32.2 一起等补丁版」—— 因为官方已经明说会有一个清 backlog 的补丁版。**

## 五、⭐⭐ 回到标题：两件事其实是同一件事

⭐ 我在开头说 3.33 有两条主线。写到这儿我认为它们比看起来更同源。

⭐ **看这个组合：**

| | 浏览器里跑 RDP | 维护者被 PR 淹没 |
|---|---|---|
| **表面** | 技术能力扩张 | 治理负担上升 |
| **实际** | ⭐ **把门槛从「装个客户端」降到「打开网页」** | ⭐ **把提交门槛从「会写 C、懂协议」降到「会描述问题」** |
| **后果** | ⭐ **对端类型大增（浏览器、SDL3、Android、iOS、Windows 客户端…）** | ⭐ **PR 数量激增（21 天 748 个）** |
| **风险** | ⭐ **面对恶意对端的攻击面扩大** | ⭐ **审查成本激增、倦怠、维护者流失** |

⭐ **⭐ 而 Linux 内核和 Mesa 在同一个月给出的答案，是同一个：⭐ 「可以用 AI，但要标注、要负责、要让评审的成本可接受。」**

⭐ **我特别想指出 FreeRDP 那个 `Assisted-by` 只有 2 处的事实 —— ⭐ 它和 Mesa 的 RADV 新政策、Mesa 上层的 Contributor Guidelines、LLVM 早一年的 "human-in-the-loop" 声明，构成了一条清晰的时间线：**

```
2025 年       LLVM：human-in-the-loop —— 你可以用 AI，但你必须复核并标注
2025-09       Mesa：允许 AI 生成代码，但提交者必须理解并负责
2026-10       RADV：写明细规则 —— LLM 辅助的 MR 要真懂代码，reviewer 可以直接关掉
2026-11       FreeRDP：748 个 commit / 20 位新贡献者 / 2 处 Assisted-by
2026-11-02    同日，RADV 的新政策发布
```

⭐ **⭐ 而我认为 FreeRDP 3.33 最值得记住的，恰恰是这个「2」。**

⭐ **因为一个项目的 AI 政策如果只剩 2 个标记，那它其实还没有政策 —— 它只有默认（默认不标注）。⭐ 而默认不标注，意味着维护者无法区分「一个用心写的 PR」和「一个机器吐出来的 PR」—— ⭐ **这才是 21 天 748 个 commit 背后真正的成本。**

⭐ **FreeRDP 的维护者用一句「the influx was huge」和一个即将到来的补丁版，处理了这个问题。⭐ 而 RADV 用一份成文规则处理了同一个问题。⭐ **谁的做法能撑得更久，答案大概在接下来几个月里。**

## 六、给不同角色的一句话

⭐ **如果你在用 FreeRDP 客户端：** ⭐ 3.33.0 的 WASM 构建目前还不是「开箱即用」的浏览器远程桌面 —— ⭐ 你还需要一个 WebSocket-to-TCP 网关。⭐ 而如果你是**服务端**，⭐ 3.33.0 值得上，但**要等那个补丁版**，因为官方已经预告 backlog 里还堆着 bug。

⭐ **如果你在维护开源项目：** ⭐ 抄 RADV 那份政策 —— ⭐ **重点不是「禁止 AI」，而是「别让 reviewer 替 contributor 做验证工作」。** ⭐ 具体三条：⭐ 允许标注、要求自证复现、reviewer 有权直接关闭。

⭐ **如果你在选 RDP 客户端：** ⭐ FreeRDP 是开源实现里唯一同时在推 WASM、SDL3 GUI、Android/iOS 客户端和 Shadow Server 的。⭐ 而它这四个月的发布节奏（124 条安全公告 / 40 天）说明两件事：⭐ **它在被密集审查，也有人在认真回应。**

---

## 主要来源

- FreeRDP 官方发布博客（3.33.0，2026-11-02，Armin Novak）：<https://www.freerdp.com/2026/11/02/3_33_0-release>
- FreeRDP GitHub Release 3.33.0（含完整 PR 列表与 13 条 GHSA 链接）：<https://github.com/FreeRDP/FreeRDP/releases/tag/3.33.0>
- FreeRDP 仓库 `ChangeLog`：<https://github.com/FreeRDP/FreeRDP/blob/master/ChangeLog>
- FreeRDP 官方发布博客（3.32.0，2026-09-23）：<https://www.freerdp.com/2026/09/23/3_32_0-release>
- FreeRDP 社区讨论 #13626「Browser client: SDL3 + Emscripten, with AV1 through WebCodecs?」（2026-10-07）：<https://github.com/FreeRDP/FreeRDP/discussions/13626>
- FreeRDP 社区讨论 #8710「Is there a freerdp web client?」（2026-10-22 更新）：<https://github.com/FreeRDP/FreeRDP/discussions/8710>
- `congzhangzh/freerdp-web`（JSPI vs Asyncify 实测，2026-10-31）：<https://github.com/congzhangzh/freerdp-web>
- Linux Foundation Research《Navigating Open Source Software Development in the Generative AI Era》（2026-10-20）：<https://www.linuxfoundation.org/hubfs/Research%20Reports/Navigating-Open-Source-Software-Development-in-the-Generative-AI-Era.pdf>
- Linux Foundation 新闻稿（2026-10-20）：<https://www.linuxfoundation.org/press/new-lf-research-survey-shows-generative-ai-cuts-open-source-coding-time-in-half-but-25-of-incoming-pull-requests-are-considered-ai-slop>
- Phoronix《Radeon RADV Vulkan Driver Adopts An LLM Policy》（2026-11-02）：<https://www.phoronix.com/news/RADV-Adopts-LLM-Policy>
- Phoronix《Mesa Adds Contributor Guidelines》（2025-09-19）：<https://www.phoronix.com/news/Mesa-Contributor-Guidelines>
- NVD：CVE-2026-111880 / CVE-2026-110837 / CVE-2026-109242
- GitHub REST API：`repos/FreeRDP/FreeRDP/compare/...`、`repos/FreeRDP/FreeRDP/security-advisories`、`search/commits?q=assisted-by`
- 原文：<https://www.phoronix.com/news/FreeRDP-3.33>

---

（说明：本文所有版本对比、commit 数、贡献者名单、`assisted-by` 计数与公告链接可用性，均为笔者通过 GitHub REST API 与官方页面实测；**13 条安全公告在本文写作时（2026-11-03）尚未公开，故本文不列 CVE 编号、不评严重度**。第三、四节中提及的三条 CVE 属同期已公开的 3.32.x 系列修复，文中已明确标注，不应与 3.33.0 的 13 条混为一谈。）
