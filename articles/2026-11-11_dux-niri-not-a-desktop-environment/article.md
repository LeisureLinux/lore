---
title: "Dux Shell 与 Niri：所谓「不是桌面环境的桌面环境」到底替代了什么"
date: 2026-11-11
slug: dux-niri-not-a-desktop-environment
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：MakeUseOf《The best Linux desktop environment isn't a desktop environment at all》（Dipan Saha，2026-11-07，经 Tux Machines 全文归档与搜索摘要重建）＋ Dux Labs 官方站 duxlabs.dev（DMS 2.1 Stormborn 与组件清单）＋ duxlabs-dev/dux-shell 官方 README（Quickshell + Go、替代 waybar/swaylock/mako 等）＋ Dux 官方文档 Overview & Architecture（2.0）＋ heise / It's FOSS / Linuxiac 关于 DMS 2.0 改名与 2.1 的报道 ＋ 本号 2026-09-09 / 09-22 / 09-28 三篇 Niri+DMS→Noctalia 实测记录 ＋ 本机只读状态核对（不安装、不测试）"
original_date: 2026-11-07
original_url: "https://www.makeuseof.com/the-best-linux-desktop-environment-isnt-a-desktop-environment-at-all/"
description: "解读 MakeUseOf 2026-11-07 那篇《最好的 Linux 桌面环境根本不是桌面环境》，并纠正一个容易滑过去的分类错误：作者说的「不是桌面环境」，指的是 Niri（滚动式平铺合成器）+ Dux Shell（原 DankMaterialShell / DMS）这套组合，不是某个新 DE。文章按三层核对：①外媒观点层 —— 作者从 KDE/GNOME/MATE/Cinnamon 说到平铺 WM「极度裸机、要自己一块块拼」，而 2026 年出现的 compositor shell 把这一步补齐了；他试的 Niri shell 很快取代了 KDE Plasma，但个人留在 DMS 1.6、把 2.0 的 Material 3 Expressive 改版视为灾难，结论「Dux 客观优于 KDE Plasma」是个人措辞不是评测。②官方事实层 —— Dux Labs 当前是 DMS 2.1 Stormborn（新系统监控、视频壁纸、重做媒体播放器、界面密度、dux files 增强）；2.0 Heisenberg 才把 DankMaterialShell 改名 Dux Shell、Dank Linux 改名 Dux Labs，并新增 Dux Files；官方 README 明说它用 Quickshell + Go，替代 waybar/swaylock/swayidle/mako/fuzzel/polkit 等一整套拼件，支持 niri/Hyprland/Sway/labwc/Miracle 等；官方文档把它类比 GNOME Shell / KDE Plasma 的「统一界面」，但强调它是壳不是合成器。③本机证据层 —— 本机 2026-09 已从 DMS 1.6 迁到 Noctalia 5.4.1：旧包 dms 1.6.0db1 / dgop / danksearch / matugen 仍在，但 dms.service 为 masked，~/.config/niri/config.kdl 用 spawn-at-startup noctalia --daemon 并 include noctalia.kdl，kitty.conf include themes/noctalia.conf，cycle-palette 依赖 noctalia msg color-scheme-set；迁移实测记录过 Quickshell v4→v5 彻底重写、D-Bus 激活绕过 systemd 导致 mako 复活、必须用 GetNameOwner 查通知名真正持有者、以及 niri 模板的 mustache 占位符需运行后渲染。明确遵守用户要求：不在宿主机安装或测试 duxlabs.dev / DMS 2.1；想试 2.1 要进干净 Debian 13 VM。结论：这类壳解决的是「拼桌面」的劳动，不解决「合成器怎么管窗口」；把 Niri 换成壳、或把壳当成 DE，都是把两层混成一层。"
published: true
---

> 原文：Dipan Saha《The best Linux desktop environment isn't a desktop environment at all》，MakeUseOf，2026-11-07
> 原文链接：<https://www.makeuseof.com/the-best-linux-desktop-environment-isnt-a-desktop-environment-at-all/>
>
> 本文依据 Tux Machines 全文归档、Dux Labs 官方站与仓库、以及本号三篇本机实测记录逐条核对。

## 一、先把这句话拆开：「不是桌面环境」到底在说什么

MakeUseOf 那篇标题玩了个文字游戏，但内容其实很朴素。作者的开场是：Linux 桌面环境选择太多 —— KDE、GNOME 这些成熟的，MATE、Cinnamon 这些至今仍维护良好的小众选项。然后是另一类，「通常被归进平铺窗口管理器」：**平铺 WM 本身极度 bare bones，你得一块一块自己把桌面拼出来**。

他给出的转折是 2026 年的变化：

> 平铺 WM 历来要么功能缺失、要么从零配置极难。现在不一样了，合成器出现了一批「壳」（shells）。我试了一个给 Niri 用的壳，它很快就把我的 KDE Plasma 彻底替掉了。

**所以「不是桌面环境的桌面环境」= 合成器 + 壳**，不是某个新 DE，也不是 Niri 自己变成了桌面环境。这个区分是全文的地基，后面三层核对都围着它转。

## 二、外媒观点层：作者实际说了什么，以及哪些是个人措辞

MUO 原文直连拿不到（多次 000 / HTTP2 协议错误），本文按 Tux Machines 2026-11-08 的全文归档 + 搜索摘要 + 官方资料重建。把能确认的和不能确认的分开：

**能确认的**：
- 作者是 Dipan Saha，2026-11-07 发布；他此前几个月写过多篇「从平铺 WM 回到 KDE」「四个平铺 WM 对比」「让 Claude 定制 Linux 桌面」，所以这篇是长期桌面折腾的一个结论，不是一次性评测。
- 被替换掉的是 **KDE Plasma**；替代者是 **Niri + 一个 Quickshell 系的壳**。
- 文章副标题本身就是「A love-hate relationship with Quickshell-based desktops」—— **爱恨交加**，不是无脑吹。

**按此前核对过的细节**（来自本号 11 月上旬对该文的整理）：作者**留在 DMS 1.6**，把 **2.0 的 Material 3 Expressive 改版视为灾难**；结尾那句「Dux 客观优于 KDE Plasma」是**个人措辞**，不是可复现的评测结论。

**必须标出来的边界**：
- 「客观优于」四个字没有对照实验、没有量化指标，是作者自己的判断。本号不替它背书。
- 他待在 1.6 而不是 2.0/2.1 —— 这意味着文章描述的是**旧版体验**，拿它去判断今天的 DMS 2.1 会错位。
- Tux Machines 只转载了开头四段并附「Read On!」，所以中段那些具体组件名、配置细节，本文一律以**官方资料**为准，不把媒体转述当事实。

## 三、官方事实层：Dux / DMS 现在到底是什么

这里最容易张冠李戴，因为项目在两个月里改了两次名。按官方站与仓库逐条核：

| 时间 | 变化 |
|---|---|
| 2026-07（DMS 1.5「The Wolverine」） | 加 Frame Mode、窗口规则管理器（Hyprland/Niri/MangoWM） |
| 2026-10-21 前后（**DMS 2.0「Heisenberg」**） | **DankMaterialShell → Dux Shell**（缩写仍叫 DMS）；**Dank Linux → Dux Labs**；组织从 AvengeMedia 迁到 duxlabs-dev；Material 3 Expressive 重设计；新增独立文件管理器 **Dux Files**、Dux Dot、锁屏自定义等 |
| 2026-11（**DMS 2.1「Stormborn」**） | 官方站当前展示的版本：新系统监控、**视频壁纸**、重做的媒体播放器、界面密度、**dux files 增强** |

**组件清单也全改了名**（官方首页）：Dux Modular Shell、Dux Files、Dux GOP（系统/进程监控）、Dux Greeter（greetd 登录器）、Dux Search、Dux Calendar（Google / Microsoft / CalDAV / iCloud）。另外 `dank16` 算法生成 16 色终端与语法高亮调色板，自动给 GTK3/GTK4/Qt 应用配色。

**它是壳，不是合成器。** 官方 README 写得很直白：Dux Shell 用 **Quickshell + Go** 构建，支持 niri、Hyprland、MangoWC、Sway、labwc、Scroll、Miracle WM 等，**替代 waybar、swaylock、swayidle、mako、fuzzel、polkit 以及你平时要拼起来的其它一切**。官方文档《Overview & Architecture》把它类比 GNOME Shell / KDE Plasma 的「统一界面」（启动器、托盘、通知、网络、VPN、蓝牙、音频、电源、亮度、锁屏），但明确说它建在 **Wayland compositor 之上** —— 窗口怎么摆、怎么滚动，是 Niri 的事，不是壳的事。

所以 MUO 那个标题成立的前提是：**壳把「拼桌面」的劳动吃掉了，但「合成器管窗口」这一层没被替代。** 把两层混成一层，就会得出「Niri 变成桌面环境了」这种错话。

**还有一条值得记**：官方安装是 `curl -fsSL https://install.duxlabs.dev | sh` 一键装全套。这类脚本本号的态度一贯是「先看清再跑」—— 本号 11 月写过 secwrap 审 `curl | sh` 的那篇实测，正好是这个话题。

## 四、本机证据层：我们三个月前已经从 DMS 迁走了

用户这次明确要求：**不要在宿主机安装或测试 duxlabs.dev / DMS 2.1**。所以本文对本机只做只读核对，结论全部来自 9 月那次真实迁移的记录。

**当前状态（2026-11-11 只读）**：

| 项 | 值 |
|---|---|
| 旧包仍在 | `dms 1.6.0db1`、`dgop 1.6.0`、`danksearch 1.6.0`、`matugen 4.0.0` |
| 当前壳 | `noctalia 5.4.1-1+deb13u1`（+ `noctalia-data`、`fonts-noctalia-tabler`） |
| `dms.service` | **masked** |
| `~/.config/niri/config.kdl` | `spawn-at-startup "noctalia" "--daemon"`；`include "noctalia.kdl"`；锁屏/面板/设置快捷键都走 `noctalia msg …` |
| `~/.config/kitty/kitty.conf` | `include themes/noctalia.conf` |
| `~/.local/bin/cycle-palette` | 依赖 `noctalia msg color-scheme-set`，注释写明这是唯一的切换 API |
| 回退包 | `~/dms-backup-20260922-073520.tar.gz` 仍在 |

**这组配置把「谁是 owner」写得很清楚**：kitty 的颜色由 Noctalia 管，niri 的启动项与 IPC 命令也全指向 Noctalia，`dms.service` 被 masking 防双会话。DMS 旧包只是没卸载，**不参与运行**。

**9 月那次迁移留下的三条硬教训**，比任何对比文章都实在：

1. **「两个壳并列」是过时说法。** Noctalia v4 确实用 Quickshell，但官方明确废弃了 v4（文档写 *v4 (Quickshell) is no longer maintained*），**v5 是彻底重写**：直接建在 Wayland + OpenGL ES 上，无 Qt/GTK 依赖，配置从 QML/JSON 换成 TOML，`ldd /usr/bin/noctalia | grep -ciE "qt|gtk"` 返回 0。两者不共享运行时、不争同一个进程。
2. **D-Bus 激活会绕过 systemd。** 当时 `pkill mako` 后通知守护总被自动拉起，原因在 `/usr/share/dbus-1/services/fr.emersion.mako.service`；`systemctl --user mask mako.service` 没用，得在 `~/.local/share/dbus-1/services/` 放覆盖文件。更关键的是 `GetNameOwner` 一查：`org.freedesktop.Notifications` 真正持有者其实是 **DMS 内置通知中心**，mako 只是冗余备份。**别假设「通知守护 = mako」。**
3. **模板占位符不能直接 include。** Noctalia 的 niri 模板里是 `{{colors.*}}` mustache 占位符，要先写静态色版本跑起来，再用 `noctalia msg templates-apply` 渲染真实调色板；直接 include 会让 niri 校验失败。

还有个小发现挺说明问题：当时 DMS 生成了 `dms/colors.kdl`，但 `~/.config/niri/` 里**没有任何地方 include 它** —— 那个主题色文件是孤儿，一直没生效。「程序自动接管你的配置目录」这种模式，出问题时不容易察觉。

## 五、所以要不要试 DMS 2.1？

**这次不动宿主机。** 理由不是保守，是上面那张表：当前 niri 启动项、kitty 主题、快捷键、调色板切换脚本全绑在 Noctalia 上，`dms.service` 又已 masked。真在宿主机跑一遍 `install.duxlabs.dev`，等于把三个月前刚理顺的 owner 关系再搅一次，而且一键脚本装的依赖不止一个包。

**要看 2.1 的正确姿势是干净 VM**：Debian 13 虚机里装，别挂宿主机的 `~/.config`，重点看三件事 —— Quickshell 与 niri 的 IPC 是否还抢通知名、`dank16` 生成的调色板是否真被 GTK/Qt/kitty 吃到、以及视频壁纸与 2.0 M3 Expressive 的资源占用。这三件事在宿主机上测都会污染现有配置。

**另外提醒一个时间差**：MUO 作者留在 1.6、嫌 2.0 是灾难；官方现在已经是 2.1 Stormborn。**拿一篇基于 1.6 的个人体验去判断 2.1，和拿 2.1 的官网去反驳那篇体验，都是错位。** 两个陈述各自成立于自己的版本。

## 六、把三篇旧文和这一篇串起来

| 本号文章 | 在这条线上管什么 |
|---|---|
| 2026-09-09《Niri + DMS》 | 为什么这套组合好用：all-in-one、锁屏内嵌虚拟键盘（niri 不支持在锁屏上叠虚拟键盘） |
| 2026-09-22《DMS 换 Noctalia》 | 真实替换：Quickshell v4→v5、D-Bus 抢名、模板占位符、配置 owner 迁移 |
| 2026-09-28《Noctalia 5.2.0》 | 新壳自己的演进，与 DMS 无关 |
| 2026-11-09《secwrap 审 curl \| sh》 | 一键安装脚本该怎么先看再跑 |
| 本篇 | 外媒那句「不是桌面环境的桌面环境」到底指哪两层，以及 2.1 现状与本机边界 |

**一条线**：**桌面环境是「合成器 + 壳 + 一堆拼件」的打包；Quickshell 系壳吃掉的是拼件，不是合成器。** 换壳能改掉 80% 的日常体验，但 niri 怎么管窗口、D-Bus 名字归谁、kitty 颜色由谁生成 —— 这些是配置层的 owner 问题，换哪个壳都得自己理。

## 七、事实边界

- **MUO 原文未直连取得**：多次返回 000 / HTTP2 PROTOCOL_ERROR / SSL EOF。本文依据 Tux Machines 2026-11-08 全文归档（转载开头四段）、搜索摘要、以及本号此前对该文的整理重建。**中段细节未经原文逐字复核**，涉及具体组件与版本一律以 Dux Labs 官方站/仓库为准。
- 「作者留在 1.6、视 2.0 M3 Expressive 为灾难」「Dux 客观优于 KDE Plasma」属媒体观点/个人措辞，本文按此前核对结果转述，不背书、不当作评测结论。
- **DMS 2.1 的功能清单来自 duxlabs.dev 首页**，本文未安装、未运行、未实测；2.0 改名与组件变化依据 heise / It's FOSS / Linuxiac 报道与官方站。
- **本机状态为 2026-11-11 只读核对**（包版本、service 状态、配置文件 grep），未执行任何安装、启动或配置修改。9 月迁移的三条教训来自本号当时已发布的实测记录。
- 「干净 Debian 13 VM 里试 2.1」是本文建议，**本文没有实施**。
- 本文只做分类辨析与事实核对，不构成桌面选型或安装建议。

## 八、结论

> **「不是桌面环境的桌面环境」不是悖论，是两层被打包卖了：Niri 管窗口，Dux Shell 管面板/通知/锁屏/配色/启动器。壳把「拼桌面」的劳动吃掉了，但没吃掉合成器。**

MUO 那篇的价值是把这个组合推到更多人眼前，代价是标题容易让人以为出现了新 DE。而对本号这台机器，答案更具体：**它三个月前已经把壳换成了 Noctalia 5.4.1**，旧 DMS 包还在但 service masked，kitty 与 niri 的 owner 都写进了配置里。2.1 Stormborn 值不值得看，得去干净 VM 里看 —— 宿主机不动。

---

## Sources

- MakeUseOf, Dipan Saha, *The best Linux desktop environment isn't a desktop environment at all*（2026-11-07）: <https://www.makeuseof.com/the-best-linux-desktop-environment-isnt-a-desktop-environment-at-all/>
- Tux Machines 全文归档（2026-11-08，转载开头并附 Read On）: <http://news.tuxmachines.org/n/2026/11/08/The_best_Linux_desktop_environment_isn_t_a_desktop_environment_.shtml>
- Dux Labs 官方站（DMS 2.1 Stormborn、组件清单、dank16）: <https://duxlabs.dev/>
- duxlabs-dev/dux-shell 官方 README（Quickshell + Go、替代拼件、支持 compositor 列表）: <https://github.com/duxlabs-dev/dux-shell>
- Dux 官方文档《Overview & Architecture》(2.0): <https://duxlabs.dev/docs/2.0/dms/overview>
- heise《DMS 2.0: DankMaterialShell becomes Dux Shell》（2026-10-23）: <https://www.heise.de/en/news/Linux-desktop-DMS-2-0-DankMaterialShell-becomes-Dux-Shell-11497553.html>
- It's FOSS / Linuxiac 关于 2.0 改名与 1.5 的报道
- 本号：<https://freelamp.com/articles/2026-09-09_niri-dms-linux-desktop/> ｜ <https://freelamp.com/articles/2026-09-22_dms-to-noctalia-niri-shell/> ｜ <https://freelamp.com/articles/2026-09-28_noctalia-5-2-0-released/> ｜ <https://freelamp.com/articles/2026-11-09_secwrap-ebpf-install-sh-approval/>
