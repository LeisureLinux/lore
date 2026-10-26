---
title: "Emaki：一个把「桌面不该需要你配置」做成产品的 Arch + niri 桌面"
date: 2026-10-27
slug: emaki-arch-niri-desktop-intro
tags: [Emaki, Arch, niri, Wayland, Quickshell, 平铺, 滚动平铺, SecureBoot, btrfs, 快照, AUR, Flathub, Linux发行版, 桌面环境, 像素艺术, 单一作者]
category: Linux/运维
author: FreeLAMP.com
original_source: "emaki.sh 官网 + GitHub 仓库 emakish/emaki（README、PLANS.md、9 个 release notes）+ 实测仓库元信息"
original_author: "Artur Yakymenko（Yakyman，Emaki 作者与唯一贡献者）"
original_date: 2026-10-24
original_url: "https://www.emaki.sh/"
description: "Emaki 0.12.0 是一个基于 Arch Linux、围绕 niri 滚动平铺 Wayland 合成器构建的完整桌面。作者 Artur Yakymenko 一个人做了它，13 天发了 9 个版本。它的核心主张是「装好即用，之后不再碰配置」：默认配置打包成一个独立文件、你的改动在另一个文件里、他们从不写你的文件；btrfs 下每次包变更前自动快照、可以从 GRUB 菜单回滚；Secure Boot 保持开启并提供 MOK 证书；还做了一个 Programs & Updates 图形程序管理器覆盖 Arch/Flathub/AUR。本文逐条拆解它的设计取舍、四个原则、发布节奏、已知问题，以及那个专门给 AI agent 用的 sudo key 包。"
published: true
---

> 来源：[emaki.sh 官网](https://www.emaki.sh/)（安装、理念、文档、FAQ）、[GitHub emakish/emaki](https://github.com/emakish/emaki)（README、PLANS.md、9 个 release notes）
> 实测仓库元信息（2026-10-27 抓取）：**`emakish/emaki`**，**GPL-3.0-or-later**，创建于 **2026-10-04**，主语言标记为 Python，**4 stars / 0 fork / 0 open issue**，**贡献者只有 1 人（Yakyman，35 次提交）**，仓库共 **35 个 commit**，9 个 release 从 **0.6.0（2026-10-11）** 到 **0.12.0（2026-10-24）**。
> 附加背景：[Phoronix：New Wayland Protocol Proposed For VNC/Remote Software](https://www.phoronix.com/news/Wayland-ext-transient-output)（**2026-10-25**，Wayland 开发者 Simon Ser 提出的 `ext-transient-output` 协议），本文第六节会说明它与 Emaki 这类远程场景的关系。
> 本文为**解读**。第四、五节的评价与第八节的判断是笔者补充。

## 一句话结论

**Emaki 是一个由**一个人**做出来的、基于 Arch + niri 的完整桌面，而它最值得看的不是「又一个 tiling 桌面」，是它把「桌面环境」这件事重新定义成了「**一个你不需要理解的产品**」。**

**官网原话：**

> **「A complete desktop built around niri, the scrollable-tiling Wayland compositor. Set up once at installation, never touched again.」**
>
> **「A complete niri desktop that sets up your config once, at installation, and never touches it again. The decisions are already made — bar, launcher, dock, lock screen, keybindings, the lot — so you install it and start working instead of reading twelve wikis.」**

**注意最后那半句：「instead of reading twelve wikis」（而不是去读十二个 wiki）。**

**这是一个非常明确的产品定位声明 —— 而且它针对的正是 Linux 桌面的真实痛点。** **Arch 的用户知道自己要什么；Emaki 的目标用户显然不是他们。**

## 一、先把「这是什么」说清楚

**README 的第一句：**

> **「Emaki is an Arch-based desktop built around `niri-emaki`, a fork of the niri scrollable-tiling Wayland compositor, and its own Quickshell shell.」**

**拆成三层：**

| 层 | 是什么 | 说明 |
|---|---|---|
| **底座** | **Arch Linux** | **不 fork、不扣留包、滚动发行版就明说滚动发行版** |
| **合成器** | **`niri-emaki`** | **niri 26.04 + 14 个补丁的 fork**（niri 是滚动平铺 Wayland 合成器） |
| **Shell** | **自有 Quickshell shell** | **面板、dock、启动器、通知、锁屏、登录屏** |

**「Quickshell shell」是理解 Emaki 的关键 —— 因为这意味着它不是「niri + 某个现成桌面」，而是自己在 niri 上写了一整套 shell。**

**README 里列的 14 个 niri 补丁，我挑几个能说明性质的：**

> **「niri-emaki（`packaging/niri-emaki/`）—— niri 26.04 加上十四个补丁：活体壁纸、shell 的玻璃捕获、从登录屏的无缝衔接、动画概览背景、分数缩放下的清晰光标，以及在无法创建 GPU 渲染器时给出不同的退出状态；再加上锁定会话的捕获保护、静态模糊遮蔽计数、为映射的 shell 层保留键盘焦点，以及带合成器输入隔离和物理 Ctrl+Alt+Delete 证明动作的可信认证连接、会话期间其他程序无法更改的安全键绑定、被标记为 shell 自身的屏幕录制、位于可见面板下方的全屏窗口，以及窗口切换器图片的平铺窗口位置。」**

**这一串读下来能感觉到一件很具体的事：作者在做的事情，是**把「niri 从一个极客工具变成一个普通用户能用的桌面」所缺的那一层补丁，全部补齐**。**

**比如「全屏窗口从可见面板下方开始」「分数缩放下清晰的光标」「无法创建 GPU 渲染器时给出不同的退出状态」—— 这些都不是「更炫」的功能，是「不这么做就会烦」的细节。**

## 二、⭐ 四个原则：Emaki 真正卖的是什么

**官网有一节叫 Principles，列了四条。我逐条展开，因为这是整个项目最有价值的部分。**

### 2.1 「Your changes are yours」—— 配置分成两个文件

**原文：**

> **「我们的默认值是单独一个文件，属于软件包。你的改动放在你自己的文件里，它 include 了我们的，并在 niri 允许后设置胜出的地方覆盖它：键绑定、间隙、键盘和触控板块。我们从不写你的文件；你也永远不需要编辑我们的。因此更新不会与你的自定义冲突。」**

**这条设计解决的是一个非常具体的痛点。**

**回顾一下 tiling 桌面的一般状况：用户去改 `config.kdl`，改着改着，系统升级了，配置文件被新版本重写或者不再被接受，用户要么迁就要么重来。** **而 Emaki 的做法是：**

```
/etc/emaki/          ← 属于软件包，升级时跟着升级
~/.config/niri/      ← 属于你，Emaki 从不写这里
```

**你的文件 include 官方的文件，只在「后设置者胜出」的地方覆盖 —— 这正是 niri 配置的 include 语义。**

**结果就是官网那句：「Updates therefore cannot conflict with your customisations.」（所以更新不会和你的自定义冲突。）**

**这一条我认为比任何花哨功能都重要，因为它解决的是「不敢升级」这个心理障碍 —— 而不敢升级是所有桌面发行版流失用户的头号原因。**

### 2.2 「Your disk, your call」—— 文件系统不替你决定

> **「文件系统由你选。如果安装时你选 btrfs，Emaki 会为你配置快照工具：每次包变更前一个快照，以及从启动菜单回去的路。如果你选 ext4，你得到 ext4。这里没有什么是强加给你的。」**

**对应到实际安装器：**

- **btrfs（推荐）**：snapper 风格的快照，**GRUB 菜单里可以直接启动某个快照**；
- **ext4**：没有系统快照，**但仍然可以选 `linux-lts` 内核**，出问题就换内核。

**注意 ext4 的降级路径设计得很实在：** 官网说「没有快照。如果新内核是问题所在，在启动菜单里选 `linux-lts` 那一项。否则从缓存里用 `sudo pacman -U` 重装之前的包。如果桌面起不来，`Ctrl` `Alt` `F3` 打开文本控制台。」

**——最后那句「还有文本控制台兜底」，是那种只有真的想过「用户会搞砸系统」的人才会写进文档的话。**

### 2.3 「Arch underneath」—— 滚就明说

> **「Emaki 底下是 Arch。我们不 fork 它，我们不扣留包，我们不假装滚动发行版是别的东西。当 Arch 坏掉时，Arch 就是坏掉。其他一切都是 Arch，我们大声说出来。」**

**这一条在 2026 年的 Linux 发行版生态里几乎是一种宣言。**

**背景是：** 过去几年不少「用户友好」的 Arch 衍生发行版会**冻结包、扣留包、改包** —— 而这些行为会让 Arch 的滚动更新保证失效。**Emaki 明确拒绝这么做。**

**后果是可见的：官网的 FAQ 里有一条是「休眠功能」——「请暂时不要使用它。安装器没有配置它。」以及已知问题里「在测试的 MacBook 上，休眠后会话无响应」。**

**——一个「我们不假装」的代价是：上游的问题会直接砸到用户脸上。** **而 Emaki 的对策是两条：**

1. **更新前自动快照 + 启动菜单回滚**（btrfs）；
2. **两个内核并存**（`linux` 与 `linux-lts`）。

**这是我认为 Emaki 的架构里最聪明的一处：它没有试图「修好 Arch」，它只是给了 Arch 一个安全网。**

### 2.4 「Made to be read」—— 没有黑魔法

> **「一个设置只存在于一个地方。没有东西在你背后被重新生成。每一块状态都能从终端查询，每一个设置都能从终端更改。」**

**这一条是对 niri 生态的直接回应 —— 很多桌面发行版会在后台偷偷改配置文件，或者用脚本生成配置。** **Emaki 的承诺是「不」。**

**而它有一个配套的杀手锏：`emaki` 命令。** **README 里写：「The `emaki` command — system map and state, and niri window/workspace commands from the terminal.」**

**「system map and state」—— 这是一个「打印系统状态图」的命令。** **对于一个宣称「每个状态都能从终端查询」的项目，这是最自然的落地方式。**

## 三、⭐ Programs & Updates：把 Arch 的三套包源收进一个窗口

**这是 Emaki 最有野心的一个功能，也是 v0.8.0 才开始做的东西（v0.7.0 的主题就是它）。**

**官网的描述：**

> **「程序用一个按钮安装：找一个，按 Install。不用终端。更新在同一个窗口里，在 btrfs 上还有回到更新前系统的路。」**

**v0.8.0 的 release notes 补充了细节：**

> **「新的 Programs & Updates 窗口有四个标签页：Browse、AUR、Installed 和 Updates，各有各的搜索。Browse 从一个起始屏打开：Emaki 挑选的、Popular 和 New 及已更新，加上分类；最小安装之后它还会提供完整安装本会添加的程序。目录在安装后立即可用，在第一次更新之前。」**
>
> **「评分和评论。程序显示来自开放评分服务的星级和评论，GNOME Software 和 KDE Discover 也用同一个，你也可以写自己的。AUR 程序显示它们的投票数。」**
>
> **「AUR，在 Programs & Updates 自己的标签页里。它只在一句明确的警告之后打开：任何人都可以在那里发布，没人检查它，Emaki 也不检查，Arch 也不检查。」**

**这里有一个细节值得单独拎出来 —— 关于 AUR 的那句警告。**

**「任何人都可以在那里发布，没人检查它，Emaki 也不检查，Arch 也不检查。」**

**这句话出现在一个把 AUR 整合进 GUI 的产品里，是相当诚实且罕见的态度。** **AUR 是 Arch 生态里最大的用户风险来源之一（包是任意用户写的构建脚本，运行时以你的身份执行）。** **大多数衍生发行版会悄悄提供 AUR 支持，或者用一条模糊的免责声明带过。** **Emaki 把它单独放在一个标签页里，加一句明确的警告，还说明「密码提示会写明来源是 AUR」。**

**另一个值得记的设计是「Undo this install」：**

> **「从 Programs & Updates 安装的程序可以用一个按钮收回。它安装时加了什么就删掉什么，你的文件留着。如果这次安装改动了已经存在的包，Undo 会把系统恢复到这次安装前做的快照。」**

**——「安装可撤销」这件事，在 GUI 包管理器里很少见。**

**而在 v0.8.0 里，Programs & Updates 的目录「在安装后立即可用，在第一次更新之前」—— 这说明它是靠发行版内置的完整包索引工作的，而不是靠联网抓取。**

**⚠️ 而官网的 release notes 里也有一条很实在的修复记录：「Programs & Updates 在目录很大时不再卡死，重新打开时保留目录，并安静地刷新它。」** —— **一个 GUI 包管理器在几千个包上卡死，然后被修掉，这个过程本身就是这个功能难度的证明。**

## 四、⭐ 那个专门给 AI agent 用的包：`emaki-sudo-key`

**这是我认为整篇文章里最值得单独一节的东西 —— 因为它指向一个正在发生的、几乎没人正面处理的问题。**

**v0.6.0 的 release notes 原文：**

> **「sudo key，一个可选的包，给使用 AI agent 的人。不用为每条命令都输入密码，而是你给一个 agent 管理员权限，限时若干分钟、若干轮对话，或整个会话。面板指示器显示每一个活跃的 key，Super+Ctrl+Esc 一次性结束它们全部。」**

**把这三条拆开看：**

| 维度 | 传统 sudo | Emaki 的 sudo key |
|---|---|---|
| **粒度** | 每条命令、每次输入密码 | **一次授权，覆盖 N 分钟 / N 轮 / 整个会话** |
| **撤销** | 命令结束即失效 | **面板指示器可见，`Super+Ctrl+Esc` 一次性全撤** |
| **可见性** | 输入密码时的提示框 | **面板上有常驻指示器** |

**为什么这件事重要？**

**因为 AI agent 的工作模式和 sudo 的授权模型在结构上不兼容。** **一个 agent 跑 50 条命令，传统的做法是 50 次密码输入 —— 这在自动化流程里根本没法用；而一次性给永久 root，又太宽松。**

**Emaki 的答案是「限时 + 可视 + 一次撤销」。** **而这三个词正好对应 agent 授权的三个真实需求：时间边界、状态可见、紧急刹车。**

**而同期它还做了另一件相关的事 —— 一个「你只能相信的密码提示框」：**

> **「一个你能信任的密码提示。当程序请求管理员权限时，Emaki 显示一个只有系统本身能绘制的提示。在它打开时按 Ctrl+Alt+Delete，会出现一个其他程序无法伪造的标记。」**

**「按 Ctrl+Alt+Delete 时出现一个无法伪造的标记」—— 这是**物理证明动作（proof action）**机制：截屏软件能伪造画面上的任何东西，但伪造不了「你在物理上按了某个键」这件事。** **这是 DRM 里用了二十年的老招数，被搬到了 Linux 提权提示上。**

**同一个 release 里还有一条：「给 Claude Code 和 Codex 的一份规则模板，告诉它们 Emaki 是怎么布局的。」**

**——所以 Emaki 对 AI agent 的态度不是「排斥」，而是「专门做支持」。** **这对 2026 年的 Linux 桌面来说是个很新的方向。**

## 五、Secure Boot：一个「先开着再说」的少见选择

**大多数 Linux 发行版在 ISO 里默认关掉 Secure Boot。Emaki 默认开着。**

**官网的说明：**

> **「ISO 以 Secure Boot 开启的状态启动。第一次启动时，计算机必须学会 Emaki 的密钥一次：** 
> **1. U 盘显示『Verification failed: (0x1A) Security Violation』，选 OK。** 
> **2. 蓝色『Shim UEFI key management』屏幕（MokManager）倒数 10 秒，按任意键。** 
> **3. 选『Enroll key from disk』→ `EMAKI` → `emaki.cer`。** 
> **4. 选『View key』，把 SHA-1 指纹和发布页上那个对比。然后『Continue』→『Enroll the key(s)?』『Yes』→『Reboot』。不需要密码。」**

**而且它把密钥指纹直接印在官网上：**

| 项 | 值 |
|---|---|
| **MokManager 显示的 SHA-1** | `D5:69:0F:44:91:14:4D:FF:EC:8B:F6:77:CC:BE:06:0A:39:5F:2F:26` |
| **emaki.cer 的 SHA-256** | `0E:BC:6E:A4:01:CF:16:0C:76:32:E3:4F:54:BD:F7:B8:9E:60:BB:E3:24:DE:10:B2:E4:AE:06:27:A8:96:D5:D6` |
| **ISO 的 SHA-256** | `6ef90109741e807df59aaacb67c7c40c5a2c8a51864f40c13e52798408cd932d` |

**——「View key 然后对比指纹」这个步骤，很多发行版只说「去 MokManager 选 Enroll」，不会告诉你该对比什么。Emaki 给了指纹，还告诉你怎么比对。**

**这背后是一个更根本的判断 —— README 里的一句：**

> **「Secure Boot 可以保持开启，如果固件信任微软的第三方 UEFI 证书（2011 或 2023）；如果两个都不信任，就在固件设置里打开那个选项。」**

**也就是说：Emaki 的 Secure Boot 方案是建立在「微软第三方 UEFI CA」之上的，而不是自己维护一条 shim 信任链。** **这和 Fedora、openSUSE 那套「自己签 shim、自己维护 CA」的路线不同 —— 代价小得多，但依赖微软的证书继续被固件信任。**

**（README 里提到 `emaki-shim-signed` 这个包，说明它确实还是带了 shim 的，只是信任链的顶端落在微软的第三方 CA 上。）**

**而 GPG 签名也做了：** 官网给出 `.sig` 和签名公钥 `.asc`，让你 `gpg --verify`，并写明「期望看到『Good signature from Emaki Package Signing』」。**另外每个镜像旁边还有 `SOURCES-ISO.txt`，列出镜像里每一个 Emaki 包的源码出处** —— 这个做法比大多数发行版认真。

## 六、⭐ niri 的工作方式：为什么「滚动平铺」值得单独一节

**Emaki 的桌面交互完全建立在 niri 上，而 niri 的模型和 i3/Sway 那类平铺窗口管理器有本质区别。**

**官网「niri for normal people」一节：**

> **「大多数桌面把窗口挤进屏幕里。niri 不是。你的窗口并排坐在一条很长的带子上，屏幕只是这条带子的一段视图。新窗口开在当前窗口右边；其他什么都不变小。」**
>
> **「用 Super ← / → 沿带子移动。放不下的窗口在边缘露出一部分，所以你总能看见还有更多。」**
>
> **「带子像楼层一样堆叠：Super ↑ / ↓ 在它们之间移动。Super O 缩小并一次显示全部。」**
>
> **「窗口宽度是你的：Super R 在三分之一、一半和三分之二之间循环。」**

**这个模型对「屏幕小」的场景特别友好 —— 而这恰好是「旧硬件」和「笔记本」这两类最需要它的场景。**

**而且它有一个和 Emaki 的产品主张呼应的性质：** **因为窗口从不缩小、只横向排布，所以「你的布局」是一个「有序的、有逻辑的位置序列」，而不是一堆堆叠的矩形。** **在滚动平铺里，「我刚才把那个终端放哪了」这个问题基本不存在。**

**顺便提一句相关的行业动态 —— 这也和 Emaki 这类远程使用场景直接相关：**

**Phoronix 在 2026-10-25 报道了 Wayland 开发者 Simon Ser 提出的新协议 `ext-transient-output`：**

> **「瞬态输出协议可以被特权客户端用来创建独立的虚拟输出，当客户端销毁对象时这些输出会从合成器移除。该协议用于配合诸如 `ext_output_image_capture_source_manager_v1` 这样的输出捕获协议，以支持远程使用场景。本协议创建的 `wl_output` 全局不绑定到任何特定硬件设备。」**

**它对应的是 `ext-transient-seat` 的输出版本 —— 后者让特权客户端可以动态创建独立的 seat，配合虚拟键鼠协议，服务于远程桌面 / VNC 软件。**

**为什么这个协议重要？** **因为在 Wayland 下做远程桌面（VNC/RDP 转发屏幕给远程客户端）一直很别扭 —— 合成器不提供「创建一个虚拟显示器让我抓」的正规途径，只能靠 hack。** **有了 `ext-transient-output`，VNC 服务器就可以创建一个虚拟输出，用标准捕获协议抓它，销毁客户端对象时输出自动消失。**

**而且它的设计取舍也很有意思 —— MR 描述里 Simon Ser 自己列了三个「设计决定」：**

- **「内置输出配置」**：不依赖 `wlr-output-management` 这类外部协议，而是直接在协议里配置 —— 理由是「协议是独立的」「虚拟输出有硬件输出没有的怪癖（没有固定模式列表、没有固定帧节奏）」「输出创建时就带着想要的配置，中间没有默认配置状态」；
- **「缩放配置」**：留给未来的扩展；
- **「Commit ACK」**：客户端没有一个事件表示 commit 请求已被处理 —— 作者自己问「这合适吗？有什么用例？需要序列号做匹配吗？」

**——一个协议设计者把「我还没想清楚的地方」写进 MR 描述里，这种写法本身值得记一笔。**

**而 wlroots 侧已有实验实现（MR 5490）。**

## 七、⚠️ 已知问题：作者自己列的那些

**Emaki 的 README 有一整节叫「Known issues in 0.12.0」，我完整摘出来 —— 因为这比任何宣传都更能说明项目的成熟度。**

- **休眠**：在测试的 MacBook 上，休眠恢复后会话无响应。**请不要用休眠。**
- **与 Windows 并存时**：只要 Windows 没完全关机，Emaki 就不会安装/更新/删除系统包。**如果 Windows 处于睡眠（休眠或 Fast Startup），Emaki 会在改动任何东西之前停下，并告诉你怎么关掉它。**
- **旧更新地址**：还在用旧 GitHub 地址更新的机器，在迁移到 `pkgs.emaki.sh` 后会打印一次「emaki: missing required signature」，下一次更新就正常了。
- **应用启动器在非英语下只能按英文名「Settings」找到设置程序。**
- **安装器里，大多数键盘布局在任何语言下都只显示短代码（如「al」），但按英文名搜仍然找得到。**
- **已安装系统的启动菜单在任何语言下都保持英文。**

**官网 FAQ 里还有几条：**

- **NVIDIA**：「还没在真实硬件上配合 Secure Boot 测试过。」
- **Windows + BitLocker**：「带自己的启动分区可以。**把 BitLocker 恢复密钥存在电脑外面** —— 带 BitLocker 和 Secure Boot 的 Windows 还没在真实 PC 上试过。」
- **休眠**：「请暂时不要用。安装器没有配置它。」

**官网的「What we tested」一节也写得很克制：**

> **「Emaki 是后期 alpha。每个版本都在虚拟机里以多种屏幕尺寸、在两台真实电脑上安装和更新：一台 AMD 笔记本和一台 MacBook。** 
> **还没测试：真实硬件上的 NVIDIA 显卡，以及与 Emaki 并存的带 BitLocker 的 Windows。」**

**而最诚实的一句在 FAQ 附近：**

> **「如果你在真实硬件上装了 Emaki？我们最需要来自我们没测过的电脑的报告：带 Secure Boot 的 NVIDIA 显卡，或者带 BitLocker 的 Windows 并存于 Emaki 旁边。告诉我们什么能用、什么不能用。」**

**——「我最需要的是坏消息」这种写法，比任何 changelog 都更能说明作者的心态。**

## 八、⭐ 节奏与现状：13 天，9 个版本

**实测的 release 序列：**

| 版本 | 日期 | 主题 |
|---|---|---|
| 0.6.0 | 10-11 | 密码提示框、**sudo key**、截图录屏、设置页 |
| 0.7.0 | 10-12 | **Programs & Updates** 登场 |
| 0.8.0 | 10-14 | Programs & Updates 完整版、评分评论、**AUR 标签页**、**与 Windows 并存安装** |
| 0.8.1 | 10-14 | 打磨 |
| 0.9.0 | 10-17 | **Secure Boot 完成**、网站、源码随镜像发布 |
| 0.9.1 | 10-19 | 修 bug |
| 0.10.0 | 10-20 | **Emaki Notes**、日历事件、闲置内存下降 |
| 0.11.0 | 10-21 | **西班牙语、葡萄牙语**、时钟与 What's new 窗口 |
| **0.12.0** | **10-24** | **德语、法语、俄语**、Super+K 命令菜单、emoji、截屏取字与读二维码、**开发者工具包**、Firefox 站点即应用 |

**⭐ 但我要特别指出 v0.7.0 的 release notes，因为它是整个项目最诚实的一次自我批评：**

> **「我们在 0.6.0 和 0.7.0 上犯了错误。** 
> **在 0.6.0 上，真实硬件测试发现安装器里一个 bug：它停在时区那一步。我们修了，但没有发布修好的 0.6.0 镜像，打算把修复放进 0.7.0 镜像一起发。** 
> **在 0.7.0 上我们犯了更大的错：我们发布了它，并把它移到了 stable 频道，而没有在真实硬件上测试。每个版本在进 stable 之前都要经过那个测试，而这一版跳过了。我们不会事后测试 0.7.0，所以这一版也没有安装镜像：请安装 0.5.0 然后更新。这不会再发生。」**

**——「这不会再发生」，并把 0.7.0 的镜像撤掉。** **这是一个人做的项目，但我见过的团队发布纪律不如这个清楚。**

**而 PLANS.md 说明了 0.12 之后的方向：**

> **「0.12 是最后一个 alpha。第一个 beta，1.0，从 Emaki 早就需要的东西开始：它会变轻。在加更多东西之前，我会先测量每一部分单独的开销 —— 玻璃、动态壁纸、面板的每一块、后台跑的助手 —— 然后要么把贵的部分做便宜，要么让你不需要时能关掉它们。」**

**以及为什么现在转 beta：**

> **「直到最近 Emaki 只跑在我自己的机器上，计划很简单：一旦它在别人的电脑上跑起来，它就不再是 alpha了。这已经发生了。我们的更新服务器显示，在大约十个国家里有十多套系统，是别人安装的，并且持续检查更新。服务器只统计请求，对你的事一无所知。到目前为止没有人回来报一个坏掉的系统。alpha 是为了走到这里。beta 是为了找出在我没见过的硬件上还会坏什么。」**

**⭐ 「服务器只统计请求，对你的事一无所知」—— 这句隐私承诺的写法值得记。**

**而发布阶段定义也很清楚：**

- **0.x — alpha**：「最原始的阶段，给构建 Emaki 的人。更新之间可能坏东西，数据可能丢失。**不要装在你要依赖的电脑上**；想试就用备用机并保持备份。」
- **1.x — beta**：「适合日常使用。粗糙的边角还在，更新会持续修它们；有不对就报 issue。」
- **2.0 及以后** —— 不再贴标签。

## 九、我的评价：它解决了什么，和它的天花板在哪

### 9.1 它真正解决的问题

**Linux 桌面有一个长期的结构性问题：** **「桌面环境」这个词在 2026 年仍然意味着「一堆需要你调的东西的集合」** —— GNOME 扩展、KDE 主题、Sway 配置、字体、终端配色、输入法……**每一个发行版都把这份工作推给了用户，而绝大多数用户不想做。**

**Emaki 的回应是：把这份工作做完，然后交付一个成品。**

**而它给出的四条原则（配置分离、磁盘自选、Arch 不打折、状态可查询）合起来构成一个很清晰的立场：**

> **「我替你做决定，但我尊重你的所有权，并且我保证你能反悔。」**

**这比「可定制」更激进 —— 可定制说的是「你什么都能改」，Emaki 说的是「**你什么都不用改，但如果你要改，也不会被更新冲掉**」。**

### 9.2 它的天花板也很清楚

**我要说三个我认为的限制：**

**① 单一贡献者 + 极新 = 巴士因子。** **实测：** 仓库只有 1 个贡献者、35 个 commit、4 stars、0 fork。**作者本人在 PLANS.md 里用第一人称写「我是 Arthur，Emaki 是我做的」** —— 这很诚实，但也意味着**如果他不继续做，这个项目就没有第二个人。** **而且它建立在两个上游之上：niri 和 Quickshell —— 任何一个上游的大改动都可能让它需要大量跟改。**

**② 「不扣留包」的代价是真实的。** **「当 Arch 坏掉时，Arch 就是坏掉。」** **这句话在哲学上很对，但它意味着用户的体验直接受 Arch 上游影响。** **Emaki 的对冲手段只有两个（快照 + 双内核），而快照只在 btrfs 上有。**

**③ 它解决的痛点，可能不是最大众的痛点。** **「十二个 wiki」这个痛点最强烈地出现在「刚接触 Linux、但又不想装 Arch」的人身上 —— 而这部分人群的规模，Emaki 自己的数据给不出答案（只有「十多个国家十多套系统」这个数字）。** **相比之下，Linus 说的「Chromebook 和 Android 才是通往桌面的路」，指的是另一个量级的入口。**

### 9.3 但有一件事值得单独说

**我觉得 Emaki 最值得借鉴的，不是它的任何具体功能，而是它对「发布纪律」的态度：**

- **0.7.0 因为没做真实硬件测试就撤掉了镜像，并且公开写下「我们犯了错」；**
- **README 里有一整节「Known issues」，包括「请不要用休眠」这种级别的坦白；**
- **PLANS.md 里说「我测不了每一台电脑，在我没见过的硬件上还是会坏」；**
- **AUR 标签页上写「没人检查它，Emaki 也不检查，Arch 也不检查」。**

**在一个大部分发行版把 release notes 当成营销素材的环境里，这种写法本身就是一种差异化。**

## 十、如果你想试

```sh
# 下载 ISO（4.8 GiB，x86_64，UEFI）
# https://dl.emaki.sh/iso/0.12.0/emaki-0.12.0-x86_64.iso

# 校验完整性
sha256sum -c emaki-0.12.0-x86_64.iso.sha256

# 校验签名（更强）
gpg --import emaki-signing-key.asc
gpg --verify emaki-0.12.0-x86_64.iso.sig emaki-0.12.0-x86_64.iso

# 写入 U 盘（8GB 以上，⚠️ 整盘被擦除）
sudo dd if=emaki-0.12.0-x86_64.iso of=/dev/sdX bs=4M oflag=sync status=progress

# Windows/macOS 用 balenaEtcher 或 Rufus（DD Image 模式）
```

**⚠️ 官网反复强调的一点：先从 U 盘启动试试。** **「U 盘启动的是完整的 Emaki 桌面。在写入磁盘之前，你能看到 Emaki 在你电脑上跑起来是什么样。」** —— **而这也是它给自己定的规矩：「它（U 盘）启动一个完整的 Emaki 桌面。在安装之前先试试。」**

**如果它是你的机器（NVIDIA + Secure Boot，或 Windows + BitLocker），官网的建议是明确的：先从 U 盘试，然后备份，再装。**

**社区：** [GitHub](https://github.com/emakish) / [Discord](https://discord.gg/JW5JdU8rW3) / [r/emaki](https://www.reddit.com/r/emaki/) / [YouTube](https://www.youtube.com/@emaki_sh)
**安全问题：** security@emaki.sh（不要发到公开 issue）

## Sources

- 官网（安装/理念/文档/FAQ）：https://www.emaki.sh/
- GitHub 仓库：https://github.com/emakish/emaki
- README 全文：https://raw.githubusercontent.com/emakish/emaki/main/README.md
- PLANS.md：https://raw.githubusercontent.com/emakish/emaki/main/PLANS.md
- Release notes（9 个版本）：https://github.com/emakish/emaki/releases
- 仓库元信息（stars/forks/贡献者/提交数）：https://api.github.com/repos/emakish/emaki
- Phoronix：ext-transient-output 协议（2026-10-25）：https://www.phoronix.com/news/Wayland-ext-transient-output
- wayland-protocols MR 546（Simon Ser）：https://gitlab.freedesktop.org/wayland/wayland-protocols/-/merge_requests/546
- wlroots MR 5490（实验实现）：https://gitlab.freedesktop.org/wlroots/wlroots/-/merge_requests/5490

---

（说明：所有引号内内容均为官网/README/release notes 原文引用；第六节的 niri 工作方式解读、第九节的评价与第十节的操作建议为笔者补充。官网与仓库均为 2026-10-27 抓取，版本为 0.12.0。）
