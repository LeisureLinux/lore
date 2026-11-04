---
title: "kitty 0.50.0：把窗口「停靠」成状态栏，以及一个终端模拟器半年内的 13 条安全公告"
date: 2026-11-04
slug: kitty-0-50-0-docked-windows
tags: [kitty, 终端模拟器, 0.50.0, DockedWindows, 停靠窗口, 状态栏, SessionRestore, Wayland, 触摸支持, 自定义着色器, CustomShaders, 图形协议, GraphicsProtocol, OSC7501, ProgramStatusProtocol, 垂直标签页, 安全公告, GHSA, CVE, 认证绕过, 命令注入, 远程控制, 文件传输, 符号链接, 性能优化, SIMD, AVX512, HarfBuzz, ShellIntegration, OSC133, RISC-V, 技术解读]
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：kitty 官方 changelog 全文（docs/changelog.rst，master 分支原文）+ GitHub Release v0.50.0（2026-11-03 13:56:09Z）+ GitHub Security Advisories API（13 条，含逐条 affected/patched 版本区间）+ GitHub Releases API 版本时间线"
original_date: 2026-11-03
original_url: "https://sw.kovidgoyal.net/kitty/changelog/"
description: "本文解读 kitty 0.50.0（2026-11-03 发布）—— 一个以「快」为卖点的 GPU 终端模拟器，⭐ 半年内连发 12 个版本。⭐ **而本文最想讲的不是新功能，是它的安全记录。** 通过 GitHub Security Advisories API 逐条核对，kitty 共有 **13 条安全公告**，⭐ 覆盖范围横跨「未认证远程 RCE」（GHSA-w98g-hpvr-r332，`@kitty-edit` DCS + `--color=geninclude`）、**命令注入**（GHSA-ccp2-q4v6-rw94 / CVE-2026-72913、GHSA-5gmr-9gwg-hhq6 / CVE-2026-54057、GHSA-p64q-59hq-5q65）、**认证绕过**（GHSA-wpff-qjx2-fw8r）、**任意文件覆盖与任意文件写**（GHSA-r892-cv7q-fw8x / CVE-2026-54056、GHSA-q446-x7q6-vcxh / CVE-2026-54055）、**未认证任意目录删除**（GHSA-2c4w-h24w-q7gg）以及一条 **critical** 级别的整数溢出堆读写（GHSA-qfgm-2c64-6x3x / CVE-2026-33642）；⭐ **其中「远程控制认证绕过」与「文件传输确认提示绕过」两条恰好在 0.49.2 与 0.50.0 这两个最新版本里修复** —— ⭐ **本文据此整理出完整的「哪个版本修了什么」对照表，说明一个「用户信任的终端」的攻击面恰恰在于它那套「让远程程序控制终端」的扩展协议上。** 另一半讲 0.50.0 的功能：⭐ 窗口停靠（docked windows）、注销后恢复会话、Wayland 客户端侧装饰对齐 GNOME、触摸屏支持、OSC 7501 程序状态协议、以及图形协议的索引色图像格式。"
published: true
---

> **原文**：kitty 官方 changelog（`docs/changelog.rst`，master 分支原文）
> 原文链接：<https://sw.kovidgoyal.net/kitty/changelog/>
> **本文依据的是 kitty 仓库里的 changelog 原文 + GitHub Release API + GitHub Security Advisories API，⭐ 不是我装了什么版本后试出来的。**

## 零、先说清楚：kitty 是什么，以及本文为什么这么写

⭐ **kitty 是 Kovid Goyal 用 C + Python 写的 GPU 加速终端模拟器**，⭐ 官方首页一句话概括：*"a feature-rich, cross-platform, fast, GPU based terminal"*。

⭐ **而我在动手读它的 changelog 之前，先做了一件事：⭐ 查它的 GitHub Security Advisories。**

⭐ **因为一个终端模拟器的攻击面有一个特别之处：⭐ 它不像普通 GUI 应用那样只处理「用户自己打开的文件」，⭐ 它还要处理「**远端机器上任意程序发来的字节流**」。⭐ **而在 kitty 这里，这个字节流不只是被渲染 —— ⭐ 它还能触发一整套 kitty 自己的扩展协议。**

⭐ **结果是：⭐ kitty 在 GitHub 上有 13 条安全公告。⭐ 我把每一条的 affected / patched 版本区间都拉了出来，⭐ 并且发现了一个很有意思的规律。⭐ **下面先讲这个，再讲功能。**

## 一、⭐⭐⭐ 13 条安全公告：一张「哪个版本修了什么」的表

⭐ **这是本文的核心。以下全部来自 GitHub Security Advisories API 的原始数据。**

| GHSA | 严重度 | CVE | 问题 | 受影响 | 修复于 |
|---|---|---|---|---|---|
| **GHSA-qfgm-2c64-6x3x** | ⭐ **critical** | CVE-2026-33642 | ⭐ **`compose_rectangles` 边界检查的整数溢出导致堆越界读写** | ≤ 0.46.2 | **0.46.3** |
| **GHSA-j68c-v8x4-269g** | high | CVE-2026-33633 | Kitty 图形协议处理器的**堆缓冲区溢出** | ≤ 0.46.2 | **0.46.3** |
| **GHSA-w98g-hpvr-r332** | high | CVE-2026-42851 | ⭐ **`@kitty-edit` DCS + `--color=geninclude` 组合导致未认证的进程内 RCE** | ≤ 0.46.2 | **0.47.0** |
| **GHSA-p64q-59hq-5q65** | high | CVE-2026-42850 | **Shell 命令注入** | < 0.47.0 | **0.47.0** |
| **GHSA-q446-x7q6-vcxh** | medium | CVE-2026-54055 | ⭐ **文件传输协议的符号链接竞态导致任意文件写** | ≤ 0.47.1 | **0.47.2** |
| **GHSA-r892-cv7q-fw8x** | high | CVE-2026-54056 | ⭐ **`kitten dnd` 远程 drop 暂存区跟随符号链接导致任意文件覆盖** | 0.47.0 – 0.47.1 | **0.47.2** |
| **GHSA-5gmr-9gwg-hhq6** | high | CVE-2026-54057 | **未过滤的 OSC 21 查询回复导致命令注入** | ≤ 0.47.2 | **0.47.3** |
| **GHSA-ccp2-q4v6-rw94** | high | CVE-2026-72913 | ⭐ **链式 `@kitty-echo` + `@kitty-ssh` DCS 转义序列导致子 shell 命令注入** | ≤ 0.48.1 | **0.48.2** |
| **GHSA-2c4w-h24w-q7gg** | high | — | ⭐ **`@kitty-edit` 转义序列导致未认证的任意目录删除** | ≤ 0.48.2 | **0.49.0** |
| **GHSA-qw6v-xf9p-8349** | low | — | **`--single-instance` 的抽象 socket 接受任意本地进程的命令** | ≤ 0.48.2 | **0.49.0** |
| **GHSA-2cmm-wgmm-8jjr** | high | — | ⭐ **未设置密码时，文件传输可绕过用户确认提示** | ≤ 0.49.1 | **0.49.2** |
| **GHSA-86c2-9jg7-6v94** | medium | — | **OSC 133 带引号字符串的缓冲区下溢** | ≤ 0.49.1 | **0.49.2** |
| **GHSA-wpff-qjx2-fw8r** | high | — | ⭐ **远程控制认证绕过（`cancel_async` + `async_id`）** | < 0.50.0 | **0.50.0** |

### ⭐⭐ 而这张表最值得看的地方，是**修复版本的分布**

⭐ **请注意最后三行的修复版本：0.49.2 与 0.50.0 —— ⭐ 也就是说，⭐ 这 13 条公告里的**最后两条，是在这个版本刚发布时修掉的**。**

⭐ **而这不是巧合 —— ⭐ 它是一个可以被验证的规律：**

```
0.46.2  →  0.46.3   修了 2 条（其中 1 条 critical）
0.47.0  →  0.47.0   修了 2 条
0.47.1  →  0.47.2   修了 2 条
0.47.2  →  0.47.3   修了 1 条
0.48.1  →  0.48.2   修了 1 条
0.48.2  →  0.49.0   修了 2 条
0.49.1  →  0.49.2   修了 2 条
0.49.2  →  0.50.0   修了 1 条
```

⭐ **⭐ 半年（2026-03 到 2026-11），12 个版本，13 条安全公告 —— ⭐ 平均每个版本带一条。⭐ 而 2026 年的发布节奏是：⭐ 3.16（0.46.1）、3.21（0.46.2）、5.19（0.47.0）、5.28（0.47.1）、6.07（0.47.2）、6.12（0.47.3）、6.15（0.47.4）、7.18（0.48.0）、7.24（0.48.1）、7.30（0.48.2）、9.21（0.49.0）、9.24（0.49.1）、10.01（0.49.2）、11.03（0.50.0）。**

⭐ **⭐ 而我要说的是：⭐ 这个节奏本身，⭐ 就是这些公告最值得注意的地方 —— ⭐ **不是「kitty 有很多漏洞」，⭐ 而是「kitty 的安全响应速度很快」。**

⭐ **因为看每一条公告的 `patched` 版本：⭐ 几乎全都是**下一个补丁版本就修掉**，⭐ 而不是攒着。⭐ 0.46.3、0.47.0、0.47.2、0.47.3、0.48.2、0.49.0、0.49.2、0.50.0 —— ⭐ **这是一个「发现即修」的节奏。**

⭐ **⭐ 而这也解释了为什么 kitty 的更新策略是「有安全更新就立刻升级」而不是「等大版本」。⭐ 因为在这个项目上，⭐ **「落后一个小版本」就可能意味着「带着一条 high 级别的远程代码执行漏洞」。**

### ⭐⭐ 而攻击面集中在哪？—— kitty 自己的扩展协议

⭐ **⭐ 请仔细看上面那张表里的一列：⭐ 有多少条的触发条件是「**远端程序发来的转义序列**」？**

| 机制 | 公告 |
|---|---|
| ⭐ **`@kitty-edit` DCS 转义序列** | GHSA-w98g-hpvr-r332（未认证进程内 RCE）、GHSA-2c4w-h24w-q7gg（未认证任意目录删除） |
| ⭐ **`@kitty-echo` + `@kitty-ssh` DCS 链** | GHSA-ccp2-q4v6-rw94（子 shell 命令注入） |
| ⭐ **OSC 21 查询回复** | GHSA-5gmr-9gwg-hhq6（命令注入） |
| ⭐ **OSC 133 shell integration 字符串** | GHSA-86c2-9jg7-6v94（缓冲区下溢） |
| ⭐ **文件传输协议** | GHSA-q446-x7q6-vcxh（符号链接竞态任意文件写）、GHSA-2cmm-wgmm-8jjr（确认提示绕过） |
| ⭐ **图形协议** | GHSA-j68c-v8x4-269g（堆溢出）、GHSA-qfgm-2c64-6x3x（整数溢出堆读写） |
| ⭐ **远程控制（remote control）** | GHSA-wpff-qjx2-fw8r（认证绕过）、GHSA-qw6v-xf9p-8349（本地任意进程） |

⭐ **⭐ 而这些机制有一个共同点：⭐ **它们都是 kitty 自己加的、用来「让远端程序更好地控制终端」的扩展。⭐ **换句话说：⭐ **kitty 的核心渲染循环本身是安全的，⭐ 它的攻击面来自它主动赋予远端程序的能力。**

⭐ **⭐ 我认为这是本文最值得记住的一条判断：⭐ **当一个终端模拟器开始支持「远程程序可以调用本地动作」时，⭐ 它实际上就把自己变成了一个**远程过程调用框架**—— ⭐ **而 RPC 框架的安全边界，取决于最弱的那些方法。**

⭐ **⭐ 而 13 条公告里至少 7 条的触发方是「远端或本地能发字节流的一方」，⭐ 这不是巧合。**

### ⭐⭐ 两条最新修复的具体机制

**⭐ ① 远程控制认证绕过（GHSA-wpff-qjx2-fw8r，0.50.0 修复）**

⭐ changelog 原文：

> *"Remote control: Fix a **crafted request being able to bypass password based remote control authentication by masquerading as a cancellation of an asynchronous request**."*

⭐ **⭐ 请注意这个措辞：⭐ 「通过**伪装成一次异步请求的取消**来绕过基于密码的远程控制认证」。⭐ **这是一个协议状态机上的混淆：⭐ 攻击者构造一个请求，⭐ 让它看起来像是在取消某个先前发起的异步操作，⭐ 从而走上一条不做密码校验的代码路径。**

⭐ **⭐ 而这条的意义在于：⭐ **kitty 的 remote control 是给脚本用的（⭐ 比如让一个 IDE 或工具去控制 kitty 窗口），⭐ 它支持密码认证，⭐ 而这条漏洞让密码形同虚设。⭐ **⭐ 而远程控制能做到的事包括 `action`、`send-key`、`run`、`set-colors` —— ⭐ **换句话说，⭐ 绕过它意味着「能在你的终端里执行命令」。**

**⭐ ② 文件传输确认提示绕过（GHSA-2cmm-wgmm-8jjr，0.49.2 修复）**

⭐ changelog 原文：

> *"File transfer: Fix a **security issue where a malicious program on the remote machine could bypass the transfer confirmation prompt** when no `file_transfer_confirmation_bypass` password is set."*

⭐ **⭐ 请注意两个限定条件：⭐ 一是「**远端机器上的恶意程序**」，⭐ 二是「**在未设置 `file_transfer_confirmation_bypass` 密码时**」。**

⭐ **⭐ 而这两个限定条件组合起来，构成了一个很清楚的攻击模型：⭐ **你在 SSH 到一台机器上，那台机器上跑着一个恶意程序；⭐ 它可以通过 kitty 的文件传输协议往你本地传文件，⭐ 而默认情况下你不会看到确认提示。**

⭐ **⭐ 而 0.50.0 里与文件传输相关的一个改动，⭐ 恰好也在这条线上（⭐ 不过它是安全修复而非新功能）：**

> *"Transfer kitten: When receiving files, replace existing symbolic and hard links at the destination instead of overwriting the files they point to, and write to a temporary file that is renamed into place…"*

⭐ **⭐ 注意：⭐ 「**写到临时文件再重命名**」⭐ 和 「**替换掉目标处的符号链接本身，而不是覆盖它指向的文件**」⭐ —— ⭐ **这两条正是 0.49.2 里那条「符号链接竞态任意文件写」（GHSA-q446-x7q6-vcxh）的结构性修复。**

⭐ **⭐ 而且 0.50.0 还顺手修了一条同族的问题：⭐ 拖放 kitten 「拒绝把目录复制或移动到它自己或它的子目录里，⭐ 以及移动到一个指向其内部的符号链接里，⭐ 那会删掉被移动的文件」。**

### ⭐⭐ 而 0.50.0 里那些「非安全」的内存安全修复

⭐ **⭐ 顺便说一句：⭐ 这一版的 changelog 里，⭐ 还有一批不带「security」标签、但同样是内存安全问题的修复：**

> *"Fix various terminal emulation bugs, including in origin mode cursor position reports, erasing multicell characters, the CHT escape code and copying text containing tabs, wide characters being drawn on the wrong row after colliding with scaled text, emoji sequences being split into multiple cells when wrapped, text typed into a new window before the program is ready sometimes being garbled, as well as a **heap buffer overflow, an out of bounds write and a use-after-free when reloading the config**."*

⭐ **⭐ 而这三条（堆溢出、越界写、重载配置时的 use-after-free）⭐ 都是**本地**问题 —— ⭐ **触发方是本地用户自己（重载配置），而不是远端。⭐ **⭐ 所以它们的严重度低于上面那批，但值得注意：⭐ **配置重载是一个「用户自己会频繁做的动作」，⭐ 而它当时带着一个 use-after-free。**

## 二、⭐⭐ 0.50.0 的功能：窗口停靠，与三个「把状态存起来」的设计

⭐ 好，功能部分。⭐ **0.50.0 的 49 条变更里，最有代表性的是第一条。**

### ⭐⭐ Docked windows：把窗口「焊」在另一个窗口边缘

⭐ changelog 原文：

> *"Allow **docking kitty windows to the edges of other windows or of the tab**, for status bars, file trees, etc. Create them with `launch --type=window-dock` or `launch --type=tab-dock`."*

⭐ 官方文档里的描述更完整：

> *"Docked windows are **placed outside the layout**, making them perfect for **status bars, file trees or a shell kept next to your editor**. A dock attached to a window **follows it around, moving with it to other tabs and closing when it closes**."*

⭐ **⭐ 请注意最后那一句：⭐ 「**跟着它走 —— 移到别的标签页时一起移，它关闭时也一起关闭**」。⭐ **⭐ 这就是「停靠」与「并列窗口（split）」的本质区别：⭐ split 是布局里的一个格子，⭐ 而 dock 是**布局之外**的一块附属物，⭐ 它的生命周期绑在宿主上。**

⭐ **⭐ 而这个设计正好对应了终端用户一个长期的痛点：⭐ **状态栏、文件树、常驻 shell 这三样东西，⭐ 在传统终端里要么用 tmux 的额外 pane 挤占空间，⭐ 要么用 neovim 插件，⭐ 要么干脆放弃。⭐ **⭐ 而 kitty 的做法是：⭐ **它给你一个「不属于布局」的位置。**

⭐ **⭐ 而我认为这个设计里最值得学的是那条生命周期规则 —— ⭐ 「**跟着宿主走、随宿主关闭而关闭**」。⭐ **⭐ 因为这正是让 dock 敢被信任的原因：⭐ 它不会变成一个你忘了关、还留在那里吃 CPU 的僵尸窗口。**

### ⭐⭐ Restore after logout：连滚动缓冲都一起恢复

⭐ changelog 原文：

> *"A new option `restore_session_after_logout` to **save the state of every kitty instance, including scrollback**, when logging out, restarting or shutting down and restore it the next time kitty starts. **On macOS, the state is encrypted with a key in the keychain. On Linux, it requires the Inhibit desktop portal.**"*

⭐ **⭐ 请注意这里的两处平台差异 —— ⭐ **这不是偷懒，而是各个平台能提供的最佳机制不同：**

| 平台 | 机制 | 为什么是这个 |
|---|---|---|
| ⭐ **macOS** | ⭐ **钥匙串里的密钥加密** | ⭐ **macOS 有系统级钥匙串，⭐ 而保存会话状态需要写一个受保护的文件；⭐ 钥匙串是唯一能让「别的进程读不到」的地方** |
| ⭐ **Linux** | ⭐ **需要 Inhibit desktop portal** | ⭐ **Linux 没有等价的系统密钥串；⭐ 而 Inhibit portal 是 XDG 桌面门户里唯一能拿到用户授权的通道，⭐ 恰好用于「阻止注销前的挂起序列」** |

⭐ **⭐ 而我认为这个差异本身说明了问题：⭐ **「会话状态」在 Linux 上之所以要走 portal，⭐ 是因为 Linux 桌面缺少一个「应用私有的受保护存储」。⭐ **⭐ 这是一个很 Linux 的问题。**

⭐ **⭐ 而且「including scrollback」这一条值得单独提：⭐ **会话恢复如果只恢复标签页和窗口，恢复出来的是个空壳 —— ⭐ **而滚动缓冲才是你「昨天看到那儿」的那个位置。⭐ **⭐ 恢复一个没有 scrollback 的会话，等于让你重新找一遍。**

### ⭐⭐ Wayland：客户端侧装饰终于像原生 GNOME 了

⭐ changelog 原文：

> *"Wayland: The **client side window decorations** used on compositors such as GNOME now **look like native GNOME decorations and follow the desktop titlebar font, text scaling, button layout and titlebar click action settings**."*

⭐ **⭐ 这里的技术背景值得说明：⭐ **在 Wayland 下，客户端（kitty）自己绘制窗口装饰；⭐ 而 GNOME Mutter 会为应用提供「服务端侧装饰（CSD）」，⭐ 也就是让 GNOME 替应用画标题栏。⭐ **⭐ 而 0.50.0 做的，是让 kitty 画的装饰**完全遵循 GNOME 的主题设置** —— 字体、缩放、按钮布局、点击行为。**

⭐ **⭐ 而这背后还有 0.34 那条更早的说明：⭐ 「*With this release kitty's Wayland support is now **on par with X11**, provided you use a decent Wayland compositor.*」⭐ **⭐ 所以到 0.50.0，kitty 的 Wayland 支持已经从「能用」走到「细节对齐」。**

⭐ **⭐ 而且这一版还加了触摸屏支持，⭐ 交互定义得很克制：**

> *"Wayland: Support touchscreens. **A tap is a click, a finger that moves scrolls with momentum, and a finger held still before it moves selects text**."*

⭐ **⭐ 请注意这个三分法：⭐ **点 = 点击｜动 = 带动量的滚动｜按住不动 = 选文本。⭐ **⭐ 这与移动端文本选择的手势语义（长按 = 选择）完全一致，⭐ 而与移动端点击（点 = 打开）不一致 —— ⭐ **而 kitty 的选择是「终端优先」的，⭐ 因为终端里「点一下」几乎总是意味着「把焦点给我」。**

## 三、⭐⭐ 三个协议层的新东西

⭐ **0.50.0 加了三个协议相关内容，⭐ 我挑最有意思的两个讲。**

### ⭐⭐ OSC 7501：程序可以报告「我在干活 / 我卡住了」

⭐ changelog 原文：

> *"Support the **Program Status Protocol (OSC 7501)** that lets programs report whether they are **working, finished, failed or blocked waiting on the user**. Shown in the tab bar via a new `tab.program_status` field for `tab_title_template`."*

⭐ **⭐ 请注意这四个状态里最有价值的一个：⭐ **「blocked waiting on the user」。**

⭐ **⭐ 而这个能力解决的问题非常具体：⭐ **一个跑了很久的命令，⭐ 现在正卡在等输入（密码、确认、选择），⭐ 而你的标签页标题不会告诉你这件事 —— ⭐ 你只会看到标题停住了，⭐ 分不清是在算还是在等。**

⭐ **⭐ 而它实现的方式也很「终端」：⭐ **不是弹一个通知，⭐ 而是让程序往标签页标题里塞一个字段，⭐ 由 `tab_title_template` 渲染。⭐ **⭐ 这意味着 —— ⭐ **如果你的标题模板没用这个字段，⭐ 这个能力对你就是不可见的。⭐ **⭐ 而这恰恰是 kitty 的一贯做法：⭐ **提供原语，不替你决定。**

⭐ **⭐ 而我想到的一个有意思的推论：⭐ **这个协议的意义是**「把等待变成可见的」**，⭐ 而这恰恰是自动化工具最难处理的状态 —— ⭐ **一个 agent 驱动一个卡在提示符上的命令，⭐ 如果它不知道对方在等输入，⭐ 它就只能超时。⭐ **⭐ 而「卡住等用户」这个状态，⭐ 是最难被自动化框架正确处理的。**

### ⭐⭐ 图形协议：索引色图像 + 特性探测

⭐ changelog 原文：

> *"Graphics protocol: Add two new **indexed color image formats** whose pixels are **indices into the terminal color palette**, so that images **change color along with the color scheme**… and allow clients to **detect support for individual protocol features**, such as animation and Unicode placeholders, via the new `e` query key."*

⭐ **⭐ 「索引色图像」这个特性，⭐ 解决的是一个很实在的问题：⭐ **你想在终端里显示一个图标，⭐ 但那个图标的颜色应该跟着你的配色方案走（⭐ 深色主题下浅一点、浅色主题下深一点）。⭐ **⭐ 如果你只能发 PNG，⭐ 它的颜色是写死的；⭐ 而索引色格式发的只是「调色板下标」，⭐ 颜色由终端决定。**

⭐ **⭐ 而第二个 —— 「按特性探测」—— 是协议设计的常识，但很多协议做不到：⭐ **一个客户端想用「动画」或「Unicode 占位符」，⭐ 需要先知道对面支不支持。⭐ **⭐ `e` 查询键就是干这个的：⭐ **客户端可以逐项问，而不是一次性开一堆开关然后靠猜。**

⭐ **⭐ 而这两条合起来，⭐ 指向同一个设计哲学：⭐ **协议要能协商，而不是只能开或关。**

## 四、⭐⭐ 性能：这一版的 7 项优化里，有 3 项是 SIMD

⭐ **0.49 的 changelog 里有一段专门的性能说明，⭐ 我觉得它比 0.50.0 的功能列表更有信息量。⭐ 官方说：**

> *"Real world effective throughput should see a **15-35% improvement** depending on workload."*

⭐ **⭐ 而 7 项具体优化里，⭐ 第 3、5、6 项全部是 SIMD 向量化：**

> *"**Speed up SIMD UTF-8 decoding: ~20% faster for ASCII and ~50% faster for multi-byte text on both x86 and ARM**, by processing pairs of vectors of plain ASCII text at a time and compacting decoded codepoints within 128-bit lanes, **avoiding expensive cross-lane operations**. Also add an **AVX-512 based decoder, another ~75% faster for multi-byte text**, used automatically on CPUs that support it (**Intel Ice Lake+, AMD Zen 4+**)."*

⭐ **⭐ 请注意这里的技术细节：⭐ 「**在 128-bit lane 内压缩解码后的码点，避免昂贵的跨 lane 操作**」⭐ —— ⭐ **这句话解释了为什么 SIMD 解码难做：⭐ **你不能简单地「向量化」，⭐ 因为 UTF-8 的变长编码意味着输出位置与输入位置不对齐，⭐ 而在 SIMD 里跨越 lane 搬数据是性能杀手。⭐ **⭐ 而「先处理成对的纯 ASCII 向量」是绕开这个问题的办法。**

⭐ **⭐ 而第 7 项也很有意思：**

> *"**Cache HarfBuzz results for repeated short runs (≤32 cells)** so redraws of the same on-screen text are not reshaped."*

⭐ **⭐ 「≤32 cells」这个阈值很说明问题：⭐ **因为终端里绝大多数文本 run 都很短（一个词、一行），⭐ 而 HarfBuzz 的整形（shaping）开销在小规模时占比很高。⭐ **⭐ 所以缓存小 run 的整形结果，⭐ 而不是缓存大 run，⭐ 才是针对终端真实负载的优化。**

⭐ **⭐ 而且第 6 项：⭐ 「图形协议图像与动画帧的 alpha 混合用 SIMD 向量化后快 **2–3.5 倍**，⭐ 字形 alpha 掩码也用同样的向量化原语合成到画布上」。⭐ **⭐ 这是一条跨越「文字」与「图形」两条渲染路径的统一优化。**

## 五、⭐⭐ 一点观察：这个项目的节奏说明了一件关于终端的事

⭐ **⭐ 最后我想说一个把安全和功能放在一起看的观察。**

⭐ **看这个版本序列：⭐ 0.46.3（3 月，修了 1 条 critical + 1 条 high）→ 0.47.0（5 月，2 条）→ 0.47.2（6 月，2 条）→ 0.47.3（6 月，1 条）→ 0.48.2（7 月，1 条）→ 0.49.0（9 月，2 条）→ 0.49.2（10 月，2 条）→ 0.50.0（11 月，1 条）。**

⭐ **⭐ 每一个版本都带着安全修复，⭐ 而 0.50.0 这个「大功能版本」⭐ **同样带着一条 high 级别的认证绕过修复**。**

⭐ **⭐ 我认为这件事说明了终端模拟器这个软件类别的一个特殊处境：**

⭐ **⭐ 第一，⭐ **终端是「执行不可信输入」的程序。⭐ **而浏览器也有这个问题，⭐ 但浏览器里跑的是 JS，⭐ 而终端里跑的是 shell —— ⭐ **shell 的能力边界远大于 JS。⭐ **⭐ 所以一个终端的转义序列处理漏洞，⭐ 后果通常比浏览器严重。**

⭐ **⭐ 第二，⭐ **终端扩展协议是「主动增加攻击面」的行为。⭐ **而 kitty 在这一点上比大多数终端走得更远（⭐ 图形协议、多光标、文本缩放、远程控制、拖放、文件传输、shell integration…），⭐ **所以它的安全维护压力必然更大。⭐ **⭐ 而它用「每个补丁版本都带安全修复」来承担这个压力 —— ⭐ **这比「攒到大版本再发」要好得多。**

⭐ **⭐ 第三，⭐ **也是我认为最实用的一条：⭐ **对你来说，这条实践建议只有一个 —— ⭐ **如果你的 kitty 版本落后了一个补丁版本，⭐ **升级的理由不是「有新功能」，⭐ 而是「你在带着一条 high 级别的远程代码执行漏洞」。**

⭐ **⭐ 而检查方法很简单：⭐ **跑一次 `kitty --version`，⭐ 然后对照上面那张表的最后一列。**

---

## 主要来源

- ⭐ **kitty 官方 changelog 原文（`docs/changelog.rst`，master 分支）**：<https://raw.githubusercontent.com/kovidgoyal/kitty/master/docs/changelog.rst>；⭐ **渲染版：<https://sw.kovidgoyal.net/kitty/changelog/>**
- kitty GitHub Release **v0.50.0**（2026-11-03T13:56:09Z）与 v0.49.2 / v0.49.1 / v0.49.0 / v0.48.2 / v0.48.1 / v0.48.0 / v0.47.4 / v0.47.3 / v0.47.2 / v0.47.1 / v0.47.0 / v0.46.2 / v0.46.1 的发布日期
- ⭐ **GitHub Security Advisories API**（`repos/kovidgoyal/kitty/security-advisories`）：⭐ **13 条公告的 summary / severity / cve_id / affected 版本区间 / patched 版本，逐条核对**
- kitty 官方文档：*Docked windows*（`layouts`）、*Restoring kitty after logging out*（`sessions`）、*Custom Shaders*、*Graphics Protocol*、*Reporting the status of a program*（`misc-protocol`）、*Program Status Protocol (OSC 7501)*
- kitty 上游 commit：`67d337794`「Remote control: Harden authorization of stream continuations」（2026-11-03）
- kitty 官方首页：<https://sw.kovidgoyal.net/kitty/>

---

（说明：本文依据 kitty 仓库 changelog 原文、GitHub Release API 与 GitHub Security Advisories API 撰写。**13 条安全公告的严重度、CVE 编号、affected 与 patched 版本区间均直接取自 GitHub Advisory Database 的原始记录，未做二次推断。** 文中对攻击面「集中在 kitty 自有扩展协议」这一判断，⭐ 是笔者根据 13 条公告的触发机制归纳的统计性结论，**不代表任何一条公告的技术细节**，⭐ 具体机制请以各条 advisory 原文为准。**本文不包含任何利用代码、payload 构造或可武器化的步骤。**）
