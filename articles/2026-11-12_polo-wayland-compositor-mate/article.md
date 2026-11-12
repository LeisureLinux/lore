---
title: "Polo：把 Marco 搬进 Wayland，MATE 桌面不必再迁就通用合成器"
date: 2026-11-12
slug: polo-wayland-compositor-mate
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Phoronix《Polo Debuts As New Wayland Compositor For MATE Desktop》（Michael Larabel，2026-11-12；Polo 1.0 发布、基于 Weston 库、复用 Marco 策略/设置/主题、XWayland、桌面立方体与果冻窗口、作者 Kerem Söke）＋ GitHub KeremSoke/polo README（libweston 16、Vala+C、三合一角色、不认同 Wayfire 方案、MIT 无关、GPL-3.0-or-later、构建要求 Vala≥0.56/GLib≥2.80/Meson≥1.4/wayland-protocols≥1.46）＋ v1.0.0 release notes（polo --session 兼容 mate-session-manager 1.28 D-Bus API、autostart/inhibitors/Presence/logind/saved sessions/XSMP、DRM backend 热插拔与 monitors.xml、layer-shell、portal 截图与共享、私有安装 patched libweston 16.0.1、Fedora 的 mate-panel 仍是 X11 only、GTK 3.24 每关窗泄漏内存、Fedora 44/45 与 Debian 14/Ubuntu 26.04 编译依赖）＋ Ubuntu Discourse 作者帖（keremsoeke24，2026-11-12，已当日常桌面、招募多显示器测试）＋ GitHub API 元数据（仓库 2026-10-24 创建、v1.0.0 于 2026-11-12 发布、2 stars / 0 forks、GPL-3.0）＋ MATE 1.28 官方发布说明（2024-02-27，experimental Wayland session using Wayfire）＋ mate-desktop/mate-wayland-session README（Wayfire 会话、需 mate-settings-daemon 1.29.1+）＋ Phoronix 2017《MATE Developers Are Considering Mir-Over-Wayland》"
original_date: 2026-11-12
original_url: "https://www.phoronix.com/news/Polo-Wayland-Compositor-MATE"
description: "本文解读 Polo 1.0：一个由 MATE 用户 Kerem Söke 发起、基于 libweston 16 与 Vala/C 写成的 Wayland compositor，目标是把 Marco 的窗口管理行为整体搬到 Wayland，而不是继续把 MATE 塞进为别的桌面设计的 Wayfire 里。文章梳理技术形态：它同时是窗口管理器、compositor 与 session authority，自带 XWayland WM，polo --session 兼容 mate-session-manager 1.28 的 D-Bus API（autostart 阶段、inhibitors、Presence、注销/关机/重启、logind、saved sessions、XSMP），沿用 org.mate.Marco.* 设置与主题快捷键，新增 org.mate.polo.* 与效果（cube、wobbly windows、magic lamp、expo 等）；输出侧有 DRM backend、热插拔、monitors.xml、DPMS、gamma、输出缩放；桌面集成靠 layer-shell 供 mate-panel、xdg-desktop-portal 提供截图与屏幕共享。并把它放进 MATE 的迁移史：2017 年考虑 Mir，2024 年 1.28 官方给出实验性的 Wayfire 会话，2026 年 Polo 走第三条路——用 libweston 做地基、把 Marco 的策略与会话语义重新实现在合成器内部。同时写清边界：项目 2026-10-24 建库、19 天后发 1.0，仅 2 stars / 0 forks，作者自述已当日常驱动但测不全硬件；Fedora 的 mate-panel 与许多 MATE 包仍为 X11-only 构建，需自行编译带 Wayland 支持的版本；GTK 3.24 在 Wayland 下每关一个窗口泄漏少量内存，仅 polo-shell-ui 自身窗口有 workaround；官方 Wayfire 会话仍在，Polo 不是 MATE 组织项目、也没被宣布为默认。结论：这是 MATE 从「把桌面适配合成器」转向「让合成器适配桌面」的一次个人主导实验，方向比版本号更值得关注。"
published: true
---

> 一手：Phoronix 报道、GitHub 仓库 README 与 v1.0.0 release notes、Ubuntu Discourse 作者帖、MATE 1.28 官方发布说明、官方 Wayfire 会话仓库
>
> 一个 Wayland compositor 发布 1.0，通常只是一条版本新闻。Polo 值得多看两眼，是因为它选了一条跟官方路线相反的路：不改 MATE 去适配合成器，改合成器去适配 MATE。

11 月 12 日 Phoronix 报道，MATE 桌面多了一个原生 Wayland 选项：Polo 1.0。描述写得很克制 —— 给还留恋 GNOME 2 分支出来的 MATE、又想进原生 Wayland 世界的人，一个「新的 compositor 选项」。

我去把项目 README、v1.0.0 release notes、作者在 Ubuntu Discourse 的发帖、以及 MATE 官方那套已有的 Wayland 会话都读了一遍。发现 Phoronix 那几百字里最值得停一下的，是作者自己写的一句：Wayfire 不是为 MATE 设计的，我们却一直靠插件、workaround 和妥协把 MATE 塞进去。

## 一、Polo 到底是什么

按 README 的定义，Polo 是「把 Marco 的行为与窗口管理策略移植到 Wayland」，用 libweston 16 做地基，Vala 和 C 写成。它同时承担三个角色：

- 窗口管理器（window manager）
- Wayland compositor
- 会话权威（session authority）

第三点最容易被忽略。X11 时代的 MATE 是分层的：`mate-session-manager` 管会话，`mate-settings-daemon` 管设置，Marco 在 Xorg 之上管窗口。Wayland 合成器天然要把更多职责收进自己体内 —— 官方 `mate-wayland-session` 的 README 也承认「Wayfire 在 Wayland 下承担了 Marco、mate-session-manager 和 mate-settings-daemon 在 X11 下的很多事」。

Polo 的做法是把这层收编做得更彻底、也更贴近 MATE 原样：

- `polo --session` 直接当会话管理器用，兼容 mate-session-manager 1.28 的 D-Bus API：autostart 阶段、inhibitors、Presence、注销/关机/重启对话框、logind、saved sessions，连旧 X11 程序用的 XSMP 都留着；
- 应用继续用同一套 MATE session D-Bus 接口和同一套 GSettings/dconf 键，`org.mate.Marco.*` 的窗口规则、主题、快捷键照常生效，Polo 自己的新设置另放 `org.mate.polo.*`；
- 自带独立的 XWayland 窗口管理器，X11 程序由它接管，Marco 的策略照样套上去；
- `mate-settings-daemon` 仍在 XWayland 下跑，但只在 Polo 会话里把无法在 Wayland 工作的插件（xrandr、键盘、鼠标、媒体键、辅助键盘、背景）关掉。

换句话说，它把 MATE 应用的既有预期逐项接住，工作量落在兼容层而不是壳上。README 里那张对照表很直白：X11 侧是 Marco + session-manager + settings-daemon 三件套，Polo 侧把窗口规则、会话管理、设置与渲染都放进合成器里，`libweston` 只负责 compositor 地基。

## 二、1.0 已经做了什么

Release notes 列得比新闻细，按类整理：

窗口与效果 —— Marco 的策略/设置/主题/快捷键，Alt+Tab 切换器、窗口菜单、对话框与 OSD 由 `polo-shell-ui` 绘制并交给屏幕阅读器播报；按键与拖拽平铺（带预览）、工作区；效果在 `org.mate.polo.effects` 下，包括果冻窗口、一堆最小化/最大化动画、桌面立方体。作者帖里还列了 fade、zoom、zap、spin、squeemize、magic lamp、expo —— 基本是 Compiz 时代那套 GNOME 2 经典效果被整套搬了回来。

会话 —— 上节那套 mate-session-manager 1.28 兼容层，加上「还有程序在运行」的拦截对话框与倒计时。

输出与输入 —— DRM backend、热插拔、保存的屏幕布局写在 `~/.config/mate/polo/monitors.xml`，DPMS、gamma、输出缩放；空闲通知与抑制、指针手势、光标形状、显式同步（explicit synchronisation）。

桌面集成 —— 通过 `xdg-desktop-portal` 做截图与屏幕共享，配 `polo-screenshot` 和共享选择器；layer-shell 供 `mate-panel` 与其他 shell 组件停靠。Discourse 帖里还提到 clipboard / clipman、多显示器与显示缩放、热插拔都能用。

打包 —— 它会把打过补丁的 libweston 16.0.1 私有安装到 `$libdir/polo`，不跟系统 Weston 抢；附 Fedora spec；源码包 `polo-1.0.0.tar.xz` 约 4.4 MB。构建门槛写得很明确：Vala ≥ 0.56、GLib ≥ 2.80、Meson ≥ 1.4、wayland-protocols ≥ 1.46（Weston 16 的最低要求），装好后从 LightDM 里选「MATE (Polo)」。

许可 GPL-3.0-or-later，从外部引入的代码保留各自兼容许可。

## 三、把它放进 MATE 的迁移史，才看得出分量

MATE 的 Wayland 之路拖了很久，路线换过几次：

- 2017 年，MATE 开发者 Martin Wimpress 公开说在跟 Mir 团队谈，想借 Mir 当 Wayland compositor 走捷径。原话是团队太小、按当时速度自己实现 Wayland 要「好几年」。
- 2024 年 2 月，MATE 1.28 的官方发布说明把「加强 Wayland 支持」列为主线：Caja 能在 Wayland 管桌面图标与壁纸、控制面板可用、多数面板小程序以 in-process 方式工作、传统托盘图标因 Xembed 不被支持而缺席。其中 `mate-wayland-session` 被明确标成「实验性的、基于 Wayfire 的 MATE Wayland 会话」。
- 这套官方会话至今仍在维护（README 已要求 `mate-settings-daemon` ≥ 1.29.1），但 README 自己写了：Wayfire 是「重新实现 Compiz 观感的可扩展合成器」，不是 MATE 窗口管理器；MATE 会话靠一个启动脚本、Wayfire 配置和一层兼容支持拼起来；主题要在 dconf 里同时给 MATE 与 GNOME 两套键设一遍，才能让 Wayland 与 XWayland 应用看起来一致。

于是 Polo 走的是第三条路：用 libweston 当地基，把 Marco 的策略、窗口规则和 MATE 的会话语义重新实现在合成器内部。README 里那句「MATE already has a coherent desktop architecture on X11」是全篇的立论 —— 既然 X11 上的架构本来就自洽，那就搬架构，别改桌面。

这也解释了为什么作者要在 README 里专门画一张「MATE 配 Wayfire」的架构图：他要论证的是「为一个不是 MATE 设计的合成器写插件和 workaround，方向本身拧着」，并没有否定 Wayfire 本身。

## 四、边界：这是个刚起步的个人项目

热闹归热闹，几处口径要标清，免得读成「MATE 官方换 Wayland 合成器了」：

- 不是 MATE 组织项目。仓库在个人账号 `KeremSoke/polo` 下；官方组织里仍是 `mate-desktop/mate-wayland-session`（Wayfire）。Phoronix 把它称作「一个新的合成器选项」，作者发帖也是以个人工作口吻介绍，没有任何官方采纳公告。
- 非常年轻。GitHub API 显示仓库 2026-10-24 创建，v1.0.0 于 2026-11-12 03:03 UTC 发布，中间 19 天；当前 2 stars、0 forks、0 open issues，release 源码包下载 4 次。README 自己写着项目仍在活跃开发中，文档部分还留着「测试与 Marco 对照文档正在编写、架构与维护 wiki 尚在计划」这类未完成说明。
- 作者自述的验证范围有限。Discourse 帖里说作者已把 Polo 当日常桌面用，但一个人测不全所有硬件配置、应用和工作流，专门请 Ubuntu MATE 用户试，尤其多显示器场景。这是招募测试者，不是稳定性承诺。
- 生态还没跟上。Release notes 明写：Fedora 的 `mate-panel` 和许多 MATE 包仍是 X11-only 构建，需要带 Wayland 支持的版本；作者建议合并 mate-panel 的两个 PR；还指出 GTK 3.24 在 Wayland 下每关闭一个窗口会泄漏少量内存，目前只有 `polo-shell-ui` 自己的窗口做了 workaround。Discourse 帖也建议「编译最新的、带 Wayland 支持的 MATE 组件」才能获得完整体验。
- 本文未实测。没有装 Polo、没有跑 `meson test`、没有验证多显示器或效果；所有功能清单来自 release notes、README 与作者帖，版本与数字为 2026-11-12 时点状态。

顺带一个容易被忽略的细节：Phoronix 说它构建在 Wayland 的 Weston 库之上，README 说基于 `libweston`，release notes 说私有安装 patched libweston 16.0.1。也就是说它用的是 Weston 的库化 compositor 地基，并且自己带了补丁，不是直接跑系统的 `weston` 命令。

## 五、结论

Polo 1.0 值得记的地方在提问方式换了：官方的 Wayfire 会话早就有，只是实验性；Polo 问的是与其让 MATE 去迁就一个通用合成器，不如让合成器把 MATE 的窗口规则、主题、快捷键和会话 D-Bus 语义原样接住。效果甚至包括桌面立方体和果冻窗口，这不只是怀旧，是在证明「行为一致」可以做到什么粒度。

但它现在仍是个人主导、19 天出 1.0、星标个位数的项目，MATE 组件也还没普遍完成 Wayland 构建。把它看作一条被认真实现出来的技术路线，比看作一个可以替换现有桌面的成品更准确。接下来值得盯两件事：MATE 上游会不会把这套「Marco 策略进合成器」的思路收编，以及多显示器与 X11-only 组件的兼容性能不能靠社区测试补上。

## Sources

- Phoronix《Polo Debuts As New Wayland Compositor For MATE Desktop》（Michael Larabel，2026-11-12）：<https://www.phoronix.com/news/Polo-Wayland-Compositor-MATE>
- GitHub 仓库与文档：<https://github.com/KeremSoke/polo> ｜ v1.0.0 release notes：<https://github.com/KeremSoke/polo/releases/tag/v1.0.0>
- Ubuntu Discourse《Introducing Polo - a MATE Wayland compositor》（keremsoeke24，2026-11-12）：<https://discourse.ubuntu.com/t/introducing-polo-a-mate-wayland-compositor/91698>
- MATE 1.28 发布说明（2024-02-27）：<https://mate-desktop.org/blog/2024-02-27-mate-1-28-released/> ｜ 官方 Wayfire 会话：<https://github.com/mate-desktop/mate-wayland-session>
- Phoronix《MATE Developers Are Considering Mir-Over-Wayland》（2017-06-27）：<https://www.phoronix.com/news/MATE-Mir-Possibilities>
