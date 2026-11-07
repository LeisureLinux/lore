---
title: "HyprBSD：给 FreeBSD 装上 Hyprland 桌面，Steam 也跑起来了"
date: 2026-11-07
slug: hyprbsd-freebsd-hyprland-desktop
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：HyprBSD 官方站点（hyprbsd.org，含 rc1/rc2 发布说明、当前限制、硬件说明与 SHA256）＋ Phoronix 报道（Michael Larabel，2026-11-07）＋ 作者 Sam Sheridan 的公开发布说明 ＋ 我对照官方 release notes 核对的版本与限制条目"
original_date: 2026-11-07
original_url: "https://www.phoronix.com/news/HyprBSD"
description: "本文解读 HyprBSD —— 一个 2026 年 10 月底开始出现的 FreeBSD 桌面发行版，用 Hyprland 合成器做 Wayland 桌面，并通过 FreeBSD 的 Linux 兼容层让 Steam 直接可玩。作者是 IT 顾问、25 年以上 FreeBSD 管理员 Sam Sheridan，他做这件事的直接起因是「受够了 FreeBSD 开箱即用的桌面体验，尤其是 NVIDIA 显卡驱动那一块」。本文的重点不是「又一个 BSD 桌面发行版」，而是三件更值得说的事。**第一，它和 FreeBSD 官方桌面计划是什么关系**：官方一直在改善桌面与笔记本体验，但那部分工作「尚未以已发布的形式进入安装器」；历史上也有 PC-BSD / TrueOS、helloSystem 和仍在进行中的 GhostBSD 等尝试 —— **HyprBSD 是这条路上的又一个节点，而不是官方的替代品**，官方站点明确写着「HyprBSD 与 FreeBSD 项目、FreeBSD 基金会、Hyprland 开发方均无隶属或背书关系」。**第二，它揭示了 FreeBSD 桌面体验真正的痛点不是「没有桌面环境」，而是「显卡驱动」**：Phoronix 转述作者的话说得很直接 —— 受挫点尤其在 NVIDIA 显卡驱动周围；而 HyprBSD 的做法是「预配置好一切」，包括对 FreeBSD 本身的若干修改。**第三，一个必须说清的边界**：官方发布说明写着「**源代码尚未发布**，将托管在项目的 Forgejo 实例上，公开链接稍后提供」—— 也就是说，**这个发行版目前只有 ISO，没有源码可审**。这对一个以「更顺滑的开箱体验」为卖点的项目来说是个值得记的点。当前版本是 **HyprBSD 15.1-rc2**（2026-11-05 发布，基于 FreeBSD 15.1，amd64，UEFI 引导，ISO 3.7GB，SHA256 d1a7e29e2b49...），RC1 是 2026-10-27。官方列出的当前限制有五条，其中两条最关键：**只支持 UEFI 安装**（即使 ISO 是用 BIOS 引导的，装出来的系统也走 UEFI），以及**没有任何 ISO 签名**（只提供 SHA256 校验和文件）。"
published: true
---

> 原文：Phoronix《HyprBSD Provides Wayland-Based Desktop Built Atop FreeBSD, Complete With Steam Gaming》（Michael Larabel，2026-11-07）
> 原文链接：<https://www.phoronix.com/news/HyprBSD>
>
> 本文依据 HyprBSD 官方站点（发布说明、当前限制、硬件说明与校验和），以及作者 Sam Sheridan 的公开发布说明。

## 一、它是什么，以及它不是什么

HyprBSD 是**一个从单个 ISO 安装的 FreeBSD 桌面发行版**，桌面用 Hyprland 合成器。

官方站点对它的定位一句话说完：**「FreeBSD. 一个 Hyprland 桌面。」**

技术规格很简洁：

| 项 | 值 |
|---|---|
| 当前版本 | **HyprBSD 15.1-rc2**（2026-11-05 发布） |
| 基础系统 | FreeBSD 15.1 |
| 架构 | amd64 |
| 桌面 | Hyprland（Wayland） |
| 引导方式 | UEFI |
| ISO 大小 | 3.7 GB |

RC1 是 2026-10-27，那是第一个候选版本。官方在 rc2 的发布说明里写：**「RC2 的很多改动在 RC1 机器上就已经通过包更新到达了，RC2 是第一个从一开始就全部包含它们的 ISO。」**

而**它不是什么**，官方站点说得非常明确：

> HyprBSD **与 FreeBSD 项目、FreeBSD 基金会、Hyprland 开发方均无隶属或背书关系**。

它用的是 Hyprland 的软件，遵循 BSD 3-Clause 许可证；项目本身由 Sam Sheridan 开发，由 Sheridan Computers 赞助。

### 它在 FreeBSD 桌面版图里的位置

Phoronix 的背景交代得很好：

> FreeBSD 一直在努力改善桌面和笔记本体验，但**那部分工作尚未以已发布的形式进入安装器和其它持续进行的工作中**。

而历史上的同类尝试已经有过一串：**PC-BSD / TrueOS、helloSystem，以及仍在进行中的 GhostBSD。**

**所以 HyprBSD 是这条路上的又一个节点，而不是 FreeBSD 官方的替代品。** 这个区别很重要 —— 很多人看到「FreeBSD 桌面发行版」会以为是官方出品。

## 二、为什么会有这个东西

Phoronix 转述了作者 Sam Sheridan 的动机：

> **IT 顾问、25 年以上 FreeBSD 管理员 Sam Sheridan 对 FreeBSD 开箱即用的桌面体验感到沮丧 —— 尤其是在 NVIDIA 显卡驱动周围 —— 于是他创建了 HyprBSD，来获得一个像样的开箱即用体验。**

而在作者自己的公开发布说明里（他 2026-10-14 那条帖子），起因更直白：**「在抱怨 FreeBSD 基金会的桌面状态之后，我决定自己做点什么。」**

**这条线索指向的是 FreeBSD 桌面体验真正的痛点。**

一个反直觉的事实是：**FreeBSD 的桌面体验问题从来不是「没有桌面环境」**。它有 Lumina、CDE、XFCE、还有通过 Linux 兼容层跑 GNOME/KDE 的各种方案。

**真正的痛点是显卡驱动。** 特别是 NVIDIA —— 这是一个在 Linux 社区里已经战斗了二十年的老大难问题，而 FreeBSD 的 NVIDIA 驱动支持长期落后于 Linux。

**而 HyprBSD 的应对方式是「预配置好一切」**：官方站点说得很清楚 ——

> HyprBSD 从单个 ISO 安装 FreeBSD 与预配置好的 Hyprland 桌面。**基础系统、驱动和桌面软件包都包含在内，所以安装可以离线完成。**

这句话里有两个信息量很大的点：**「包含驱动」** 和 **「可以离线安装」**。

Phoronix 还提到：**「作为这项新计划的一部分，也对 FreeBSD 本身做了各种修复，以进一步提升桌面上的 FreeBSD。」**

**也就是说，HyprBSD 不只是打个包 —— 它还在往上游推 FreeBSD 的桌面改进。** 这和「用 ISO 装个桌面」是两种不同性质的工作。

## 三、Steam 是怎么跑起来的

这是整个 HyprBSD 最抓眼球的卖点，也是 FreeBSD 桌面上最出人意料的成就。

Phoronix 的原话：

> HyprBSD 通过 FreeBSD 的 **Linux 兼容层**让 Steam 跑起来，并且已验证可与**多种游戏**一起工作，**包括受 BattlEye 保护的游戏**。

**「包括受 BattlEye 保护的游戏」这一句是分量最重的。**

BattlEye 是很多商业游戏的反作弊客户端，而**反作弊通常要求在内核层面工作** —— 而 Linux 兼容层（FreeBSD 的 Linux 兼容层）本身就是在 FreeBSD 内核之上模拟 Linux ABI。

**在这样的兼容层里让一个需要内核级反作弊的游戏跑起来，技术难度是相当高的。** 这说明 HyprBSD 在兼容层之上做的那些「修改」不是简单打个补丁。

而作者自己的发布说明（2026-11-03那条）写得更直接：**「包含 Steam 的下一个 HyprBSD 版本已经准备好发布了（以及大量修复、变通方案和补丁）。」**

**「大量修复、变通方案和补丁」** —— 这个措辞很诚实。它承认了跑通这件事背后的工作量。

另一个配套的东西是 **XWayland**，Phoronix 提到它也在工作 —— 用来跑依赖 X11 的软件。

**这两个加在一起，意味着 HyprBSD 想做的是「桌面能日常用 + 游戏能玩」这个完整闭环**，而不只是「能启动一个 Wayland 会话」。

### 但这里有个必须说清的前提

Phoronix 在同一篇报道里也写了一句：

> **这些修改中的许多也可以在一个原版 FreeBSD 安装上完成**，但这里的意图是提供一个更顺滑、更打磨过的开箱即用体验。

**这句话把「HyprBSD 提供了什么」这个问题回答得很清楚**：它的价值不在于「这些改动 FreeBSD 做不到」，而在于「**这些改动 FreeBSD 做不到，但有人替你做完了并打包好了**」。

**这是「发行版」这个形态存在的全部意义** —— 不是造新东西，是把散落的补丁整合成一个可安装、可更新、可回滚的整体。

## 四、当前限制：官方列了五条，其中两条最关键

官方发布说明里的「当前限制」清单，我原样列出来（英文原文见文末 Sources）：

| 限制 | 说明 |
|---|---|
| **候选版本** | RC2 仅供测试与反馈 |
| **仅 UEFI 安装** | **装出来的系统使用 UEFI，即使 ISO 是用 BIOS 引导的** |
| **图形** | 显卡与 QEMU 设置见硬件说明 |
| **网络** | Wi-Fi 支持因适配器而异 |
| **启动介质** | 直接把镜像写入 USB；多系统启动 USB 工具未经测试 |

### 限制一：只支持 UEFI 安装，这条有实际影响

**「即使 ISO 是用 BIOS 引导的，装出来的系统也使用 UEFI。」**

这条对一个特定人群影响最大：**装在比较老的机器上的用户。** 比如 2015 年前后的笔记本 —— 很多只支持传统 BIOS 引导，而 UEFI 需要 GPT 分区布局。

**所以「FreeBSD 15.1 + Hyprland 桌面」这个组合有一个隐含的硬件门槛：你的机器得支持 UEFI。**

而 HyprBSD 明确说自己面向的是「笔记本体验」的改进 —— 这就产生了一个矛盾：**想改善笔记本桌面体验的发行版，自身却排除了相当一部分老笔记本。**

### 限制二：没有任何 ISO 签名

官方原文：

> 一个匹配的校验和确认下载到的字节与已发布的镜像一致。**发布签名是另一项检查；目前没有列出任何 ISO 签名。**

**这句话值得单独拎出来说。**

它的意思是：**你可以确认「你下载的东西没被改坏」，但不能确认「这东西确实是 HyprBSD 项目发布的」。**

区别在于：

- **SHA256** 保护的是**传输完整性** —— 防止下载损坏、防止中间人替换（因为校验和文件也在同一个站点上，所以严格说它防不住能同时替换两者的攻击者）；
- **签名（GPG）** 保护的是**来源真实性** —— 只有持有私钥的项目方能签出这个镜像。

**而 HyprBSD 的 SHA256 校验和文件与 ISO 在同一个下载站、由同一个人发布** —— 这意味着一个能入侵该站点的攻击者可以同时替换 ISO 和校验和文件，SHA256 校验会「通过」。

**对一个定位为「让 FreeBSD 桌面更好用」的项目来说，源码未发布 + ISO 未签名这两点叠加，使得它目前更像一个「值得关注的实验」而不是「可以放心装在生产机上」的东西。**

### 而最要紧的那一条，Phoronix 报道里根本没提

官方站点首页写着：

> **The source has not been released yet.** It will be hosted on the project's Forgejo instance; public links will be added when available.

（**源代码尚未发布。** 它将被托管在项目的 Forgejo 实例上；公开链接稍后提供。**这一句是全文我唯一想原样保留的英文** —— 因为它是整篇文章最该被读者知道、而媒体报道里恰恰没有的那一条。）

**这是整篇文章里我认为最该被读者知道的一条事实 —— 而 Phoronix 的报道里没有它。**

这一条的重量在于：

- **没有源码，就无法审计。** 你不知道那个 ISO 里除了 Hyprland 桌面配置之外还改了什么 —— 尽管官方说「包含了驱动和桌面包」且「对 FreeBSD 本身做了各种修复」。
- **没有源码，就没有可复现构建。** 别人无法从零构建出同一个系统。
- **没有源码，就没有社区审查。** 而 FreeBSD 生态的核心价值恰恰是「每个人都能看到每一行」。

**这不是说 HyprBSD 有问题** —— 它明确标注了「活跃开发中」，作者也在积极公开发布进展（10-14、10-27、10-28、11-03、11-05 都有帖子）。**源码公开是一个待办事项，而不是隐瞒。**

但**读者有权知道这件事**，尤其是在考虑把它装到主力机器上的时候。

## 五、其它值得一提的技术细节

### ZFS 与 boot environment

官方站点提到：

> HyprBSD 使用 **ZFS**、FreeBSD 的 pkg 工具，以及一份你可以修改的桌面配置。**更新会保存一个 boot environment，让你能够回到之前的系统。**

**「更新会保存 boot environment」这一句是 FreeBSD 特有的能力**，而且在桌面场景下格外有用 —— 桌面用户比服务器用户更需要「更新出问题了能退回去」。

（FreeBSD 的 boot environment 是 ZFS 上的一个机制：每次系统升级前创建一个快照式的环境，出问题可以 `bectl` 切回去。）

### 离线安装

**「基础系统、驱动和桌面包都包含在内，所以安装可以离线完成。」**

对一个桌面发行版来说，离线安装能力有实际价值 —— 意味着装系统不依赖网络状态，也意味着可以在网络不通的环境里部署。

### 图形支持

官方发布说明说「显卡与 QEMU 设置见硬件说明」，Phoronix 的报道则说 **AMD、Intel 和 NVIDIA 都受支持**。

而支撑这个结论的正是前面提到的那个改动 —— 官方说这次「对 FreeBSD 本身做了各种修复」。

**在 FreeBSD 上把 NVIDIA 支持做可用，本身就是一个有难度的活**（NVIDIA 的专有驱动在 BSD 上的移植长期滞后于 Linux）。作者在 LinkedIn 上发的那条抱怨正是冲着这个来的。

### 桌面本身的配置

官方站点给的第一分钟体验说明挺实在：

> 一个平铺桌面，带终端、浏览器、文件管理器和应用启动器。按 `Super` + `K` 查看快捷键。

其它快捷键也是常规 Hyprland 那一套：`Super+C` / `Super+V` 复制粘贴、`Super+Ctrl+V` 打开剪贴板历史、通知里直接截图标注或录制窗口。

顶栏能点开网络设置、控制音量、查看通知，**点 CPU 或内存占用会打开 btop**。

## 六、三个值得单独记的点

### ① 官方桌面计划与社区发行版是并行而非替代关系

Phoronix 提到 FreeBSD 官方「一直在改善桌面和笔记本体验，但那部分工作尚未以已发布的形式进入安装器和其它持续进行的工作中」。

**而 HyprBSD 官网则明说自己与 FreeBSD 项目和基金会无隶属关系。**

这两句放在一起，说的其实是同一件事的两面：

- **官方的桌面工作还在推进中，但没进安装器**；
- **社区用 HyprBSD 这个形态先把体验做出来，同时把修改反馈回上游。**

**「先在社区里跑通，再回灌上游」** —— 这在 FreeBSD 生态里是有先例的路径。

### ② 「不受官方背书」这句话在 BSD 生态里不新鲜

FreeBSD 生态里有过一整串同类项目：PC-BSD、TrueOS、helloSystem、GhostBSD（我之前写过 GhostBSD 26.2 的发布）。

**但每一次新项目出现，都会重新引发同一个问题**：「这会不会分裂生态 / 会不会让用户困惑」。

**HyprBSD 官网主动把这句话写在首页最显眼处**（免责声明、商标声明、许可证说明），而不是藏在 footer 里 —— 这个做法本身值得肯定。

### ③ 「赞助商」模式是这个项目的一部分

官网首页写着：

> 由 **Sheridan Computers** 赞助。
>
> **支持我们 —— 每月 5 英镑支付下载托管和测试硬件。**

**「每月 5 英镑」这个定价，和「支付下载托管和测试硬件」这个用途说明**，把项目的经济模型摆在明处。

对比一下：Sam Sheridan 同时是 Sheridan Computers 的 CEO（他自己 LinkedIn 资料里写的）。**所以这是一个创始人用自己的公司赞助自己做的开源项目的模式** —— 这在 BSD 生态里很常见（比如 FreeBSD 基金会自己的 Several 项目模式、NetBSD 基金会的赞助模式）。

**从工程角度看这意味着项目有真实的资金支持和真实的硬件测试能力**，而不是「个人业余时间做做」。

## 七、结论

**HyprBSD 值得关注，但理由不是「又一个 BSD 桌面版」。**

真正值得记的三点：

1. **它证明了 FreeBSD 的桌面体验痛点是显卡驱动，不是桌面环境本身** —— 而这个问题在 Linux 世界战斗了二十年仍未完全解决。FreeBSD 走的是另一条路（Linux 兼容层 + 预配置），而不是重复 Linux 的战斗。
2. **它是「社区先行、反馈上游」这条路径的一次新实践** —— 官方桌面计划还没进安装器时，先用发行版形态把体验做出来，同时把 FreeBSD 本身的修复往上推。
3. **它当前的诚实度值得肯定**：官网把「源码未发布」「无 ISO 签名」「仅 UEFI」「Wi-Fi 因适配器而异」全部写在最显眼处，还附了 SHA256 校验和文件、专门的硬件测试记录页和「如何报告问题」的入口。

**但对想上手的人来说，有三件事必须先知道**：**没有源码可审、ISO 没有签名（只有 SHA256）、只支持 UEFI 安装。**

前两条决定了这东西现在更适合「在 spare 机器上试试」，第三条决定了它不适合在不支持 UEFI 的老机器上折腾。

---

## Sources

- HyprBSD 官方站点（首页，含定位、桌面说明、源码未发布声明与免责声明）: <https://hyprbsd.org/>
- HyprBSD Releases（rc1/rc2 版本信息、SHA256、当前限制、ISO 签名说明）: <https://hyprbsd.org/releases/>
- HyprBSD Getting started（安装、快捷键、校验方法）: <https://hyprbsd.org/getting-started/>
- HyprBSD Hardware notes（显卡、QEMU、网络适配器的实测记录）: <https://hyprbsd.org/hardware/>
- Phoronix, *HyprBSD Provides Wayland-Based Desktop Built Atop FreeBSD, Complete With Steam Gaming*（Michael Larabel，2026-11-07）: <https://www.phoronix.com/news/HyprBSD>
- Sam Sheridan 的公开发布说明（LinkedIn）: <https://www.linkedin.com/posts/ssheridan_the-next-hyprbsd-release-which-includes-steam-activity-7523486161655283712-IS1t>

### 事实边界说明

- **版本、规格、SHA256、当前限制五条、UEFI 说明、ISO 未签名说明、源码未发布声明、ZFS 与 boot environment、赞助与定价、免责声明：全部引自 HyprBSD 官方站点**，本文逐条核对。
- **RC1 是首个候选版本、RC2 相对 RC1 的差异说明**：引自官方 rc2 发布说明。
- 作者动机（对 FreeBSD 开箱桌面体验的沮丧，尤其 NVIDIA 驱动周围；25 年以上 FreeBSD 管理员、IT 顾问身份）：引自 Phoronix 转述。
- **Steam 通过 Linux 兼容层运行、已验证含 BattlEye 保护的游戏、XWayland 可用、AMD/Intel/NVIDIA 图形支持、对 FreeBSD 本身的修复**：引自 Phoronix 报道。
- 「这些修改许多也能在原版 FreeBSD 上完成，意图是提供更打磨的开箱体验」：引自 Phoronix 原文。
- **「源代码尚未发布」这一条 Phoronix 报道中未提及**，本文据官方站点首页补入，并明确指出这是官方声明而非推测。
- 本文只做技术解读与选型参考，不构成对任何项目安全性的背书。
