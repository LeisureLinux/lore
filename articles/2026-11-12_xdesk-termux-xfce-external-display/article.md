---
title: "XDesk：把 Termux 的 XFCE 搬上外接屏，手机当触摸板"
date: 2026-11-12
slug: xdesk-termux-xfce-external-display
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Reddit r/termux 帖《XDesk: run your Termux XFCE desktop on a monitor, a Mac or a browser, with the phone as touchpad (no root)》（u/EnvironmentOld6483，帖 ID 1xsrqz7，网页版正文；`.json` 接口返回 403，评论区未取到）＋ XDesk 官网 n2ray.github.io/xdesk（中英双语；三步上手、USB-C 显示器 / Mac / 另一台 Android / 浏览器 / 车机五种目标、Termux 安装命令、15–20 ms USB 到 Mac 自测、无线与网页不加密、shell 权限注入服务、作者与 Claude 分工、GPL-3.0）＋ GitHub n2ray/xdesk README（默认分支 xdesk、GPL-3.0、Java、2026-11-02 建库、1269 commits、11 stars / 1 fork、17 个 release 最新 v0.5.1 于 2026-11-11；Quick start 需 Android 11+、无线调试配对码或 Shizuku、小米需 USB 调试（安全设置）、DisplayPort Alt Mode、重启后重新激活；Linux 桌面部分基于 Termux:X11，装到官方应用旁边但两者都用 `:1` 不能同时跑；支持 Termux / proot-distro / 普通 proot / chroot，Adreno 上 Termux 走 zink+Turnip，proot/chroot 默认软件渲染；声音经 PulseAudio null sink 到 127.0.0.1:4713，PULSE_COOKIE 与匿名端口回退；无线显示 H.264 约 12 Mbit/s@1080p、端口 47140、mDNS 发现、4 位配对码；网页显示端口 47150、WebCodecs 或 MSE；Mac 版为 Apple silicon 自签名 Rust/SDL2 应用；How it works 架构图与 InjectorService / LorieView / CursorOverlay 说明；Limitations 逐条）＋ GitHub API 仓库与 releases 元数据 ＋ `xdesk/install.sh` 脚本原文（curl | bash；检查 xrandr/pulseaudio/flock/setsid/sha256sum/pgrep 依赖、从 releases 拉 xdesk / loader.apk / xdesk.apk / SHA256SUMS 并校验、装到 $PREFIX/bin/xdesk、loader.apk 置 400、APK 落到 ~/ 或 /sdcard/Download、自动执行 xdesk setup）＋ SECURITY.md（仅指向 termux.dev/security 上游策略）＋ Reddit 帖内官网与仓库链接 ＋ 本工作区旧文《Termux 跑 Debian 13 桌面：难点是不被 Android 杀掉》作对照 ＋ Termux:X11 官方 README（:1 启动 xfce4-session、proot 需 --shared-tmp、后台 CPU 调度降级）"
original_date: 2026-11-12
original_url: "https://www.reddit.com/r/termux/comments/1xsrqz7/xdesk_run_your_termux_xfce_desktop_on_a_monitor_a/"
description: "本文核对 r/termux 上的 XDesk 项目。先纠一个容易读反的地方：Reddit 标题把焦点放在「Termux XFCE 上大屏」，但 XDesk 本体是把 Android 应用全屏投到外接显示器、手机当触摸板与键盘的工具，Termux/XFCE 只是可选的一层，Linux 桌面底层基于 Termux:X11。技术实现拆成三条链路：显示侧由 upstream MainActivity / LorieView 在外接屏画 X11，X server 跑在 Termux 里、占用 display :1；输入侧 XDeskActivity 在手机屏幕上直接调用 sendMouseEvent / sendKeyEvent / sendTextEvent，Android 应用则靠无线调试配对或 Shizuku 启动一个 shell 用户身份的 InjectorService 读 /dev/input 并 injectInputEvent（重启后需重新激活，Termux 会话不需要）；声音经 PulseAudio null sink 与 127.0.0.1:4713 回传，proot/chroot 需带 PULSE_COOKIE。文章列出五种显示目标：USB-C DisplayPort Alt Mode 显示器、Apple silicon Mac（USB 或 Wi-Fi，自测 15–20 ms）、另一台 Android 的 XDesk Receiver（H.264 约 12 Mbit/s@1080p）、任意浏览器（端口 47150）、实验性的 Android Auto 车机。并写清安装与代价：官网给的是 curl | bash，脚本会校验 SHA256SUMS、装 xdesk 到 $PREFIX/bin、把 loader.apk 设为 400、自动跑 xdesk setup；无 root 的代价是每次重启重新激活、依赖 shell 权限服务、Termux 与 XDesk 都必须存活、不能与官方 Termux:X11 同时运行（都用 :1）。重点标出官方承认的安全边界：无线显示、Mac over Wi-Fi 与网页模式全部明文 HTTP，配对码/令牌/画面/声音不加密，只可在可信网络用；SECURITY.md 仅转向上游 Termux 策略。项目状态也如实写：2026-11-02 建库、10 天 1269 commits / 17 个 release、11 stars，作者自述大部分代码与文档由 Claude 写、自己负责决策与真机测试，且只在一台欧版小米 15 Ultra 与一台 M4 Mac 上验证过，国行同型号未测。结论：与本站前一篇「把 Debian 13 桌面保活」形成对照，XDesk 解决的是显示与输入链路，而非 Linux 发行版本身；它是一台把手机当主机的桌面外壳，早期个人项目，别当成熟方案。"
published: true
---

> 一手：Reddit 原帖网页正文、XDesk 官网与中文页、GitHub README、`install.sh` 与仓库元数据
> 对照：本工作区前一篇 Termux/DeX 稿、Termux:X11 官方说明
>
> `.json` 接口被 Reddit 挡了（403），所以评论区没取到；下面所有功能与安全说明以项目官网和仓库 README 为准。

11 月 12 日 r/termux 出现一个帖子：XDesk，标题写的是把 Termux 的 XFCE 桌面放到显示器、Mac 或浏览器上，手机当触摸板，不需要 root。

帖子很短，但顺着里面的官网与 GitHub 链接读下去，会发现一件跟标题不太一样的事：XDesk 本体管的是「Android 应用怎么全屏到另一块屏幕」，Termux/XFCE 是后加上去的可选一层。作者自己写的是早期个人项目，只在一台欧版小米 15 Ultra 上日常用。

## 一、先把定位摆正

官网首页第一句就是「把手机里的应用搬上大屏」：装一个 APK、激活一次、接上屏幕，手机上已有的 Android 应用在大屏全屏跑，手机变成触摸板和键盘，外接屏还有收藏应用网格与底部 dock。

Linux 桌面在网站里排在第二屏，标着 Optional / 可选，要装 Termux：装好 Termux 后跑一行安装命令，桌面会话才会出现在 XDesk 启动器里。README 也明说「Android apps need none of it」—— 安卓应用那一半完全不依赖 Termux。

所以准确的层级是：

| 层 | 作用 |
|---|---|
| 外接显示与输入 | XDesk 本体（基于 Termux:X11 的 X server 与 LorieView 渲染） |
| Android 应用全屏 | 需要 shell 权限的注入服务 |
| XFCE / Linux 桌面 | 可选，跑在 Termux、proot-distro、普通 proot 或 chroot 里 |

Reddit 标题把第三层当主语，容易让人以为是「又一个 Termux 桌面脚本」。它更像是把手机当成一台主机的桌面外壳：显示、输入、声音三件事被重新接了一遍。

## 二、三条链路怎么接起来

README 里那张架构图很值钱，拆开说就是三条链路。

显示。外接屏上跑的是 upstream 的 `MainActivity` 与 `LorieView`，负责把 X 画面画出来；X server 本身跑在 Termux 里，由一段为这个 app id 编的 loader 启动，占用 `DISPLAY=:1`。手机这侧的 `XDeskActivity` 与它在同一进程，直接调用 `sendMouseEvent` / `sendKeyEvent` / `sendTextEvent`，所以触摸板输入不用绕网络。README 特别提醒：XDesk 装在官方 Termux:X11 旁边、不改动它，但两者都用 `:1`，不能同时跑，否则会报显示 `:1` 已被另一个 X server 占用。

输入。这里是无 root 方案的关键，也是最容易被「no root」四个字带过的地方。Android 不允许普通应用给别的应用注入键鼠事件，于是 XDesk 通过无线调试配对码（Android 11+）或 Shizuku 启动一个以 shell 用户身份运行的 `InjectorService`：它读 `/dev/input`、用 `injectInputEvent` 注入事件，`CursorOverlay` 画指针。代价写得明明白白：激活时需要连 Wi-Fi、小米还要额外开「USB 调试（安全设置）」、手机重启后要重新激活；Termux 会话不需要这套服务。

声音。桌面音频走 PulseAudio 的 null sink，经 Termux 私有目录里的 socket 交给 App 用 `AudioTrack` 播放，好处是能选输出设备（手机扬声器 / HDMI / 蓝牙 / USB）而不申请特殊权限。proot 与 chroot 里的程序连 `127.0.0.1:4713` 并带 `PULSE_COOKIE`；README 还留了个匿名端口回退开关，同时警告那样手机里任何应用都能录制桌面声音。

Linux 桌面侧的环境支持也列得细：Termux 原生、proot-distro、普通 proot、chroot 各有接法；GPU 加速只给 Adreno 上的 Termux 配了 zink + Turnip，proot / chroot 里默认是软件渲染，作者自己说「调试够用，别拿来打游戏」。

## 三、不止 USB-C 显示器

按官网与 README，显示目标一共五类：

- USB-C 显示器 / 便携屏 / 扩展坞：要求手机支持 DisplayPort Alt Mode，判断方法是插上显示器能镜像手机画面；延迟最低。
- Apple silicon Mac：装自签名的 XDesk Mac 应用（Rust + SDL2），USB 连上走数据线、拔线自动切 Wi-Fi，Mac 键鼠直接可用；作者自测 USB 下约 15–20 ms，按 `Control+Option+D` 看实时数据。首次打开要在「隐私与安全性」里点「仍要打开」并给辅助功能权限，没有 Windows / Linux 版。
- 另一台 Android 设备：装 `xdesk-receiver.apk`（Android 5.0+），经 mDNS 发现、4 位码配对，H.264 视频约 12 Mbit/s@1080p、长边封顶 1920，画面与声音一起过去；投到平板上还能反过来操作手机。
- 任意浏览器：iPad、笔记本、智能电视都行，页面在 47150 端口，WebCodecs 不可用时退回 Media Source Extensions。
- Android Auto 车机：实验功能，明确写「只能停车时用」，DRM 视频可能黑屏。

手机当触摸板支持移动、点按、拖动、滚动；官网还提到在 Linux 桌面里能直接用手机输入法打中文。应用启动器支持搜索、双开应用与固定常用项，Android 应用和 Linux 桌面可以来回切，两边都保持运行。

## 四、安装脚本到底做了什么

官网给的一行命令是 `curl -fsSL .../xdesk/install.sh | bash`。这类命令值得先看再跑，我把脚本读了：

- 检查 `xrandr` / `pulseaudio` / `flock` / `setsid` / `sha256sum` / `pgrep`，缺什么就 `pkg install`，并启用 `x11-repo`；
- 从 GitHub releases 拉 `xdesk`、`loader.apk`、`xdesk.apk` 与 `SHA256SUMS`，用 `sha256sum -c` 校验三个文件；
- 把 `xdesk` 装到 `$PREFIX/bin/xdesk`，`loader.apk` 放到 `~/.local/libexec/xdesk/` 并 `chmod 400`（Android 拒绝加载可写的 dex），APK 落到主目录或 `/sdcard/Download`；
- 自动执行 `xdesk setup`，提示装 APK、接屏、选桌面。没有桌面的话再来一句 `pkg install xfce4 xfce4-terminal && xdesk setup`。

官网自己也写了「运行前建议先看看脚本」。比常见的裸 `curl | bash` 多了哈希校验，但本质仍是从 latest release 直接拉二进制执行，风险口径不因为加了校验就消失。仓库 `SECURITY.md` 只有一句转向上游 Termux 安全策略，没有独立的安全说明。

## 五、必须写清的安全边界

这是我认为最该从 README 里搬进正文的一段：无线与网页模式不加密。

- XDesk Receiver 的无线显示：配对码、配对后下发的令牌、画面和声音都明文传输；配对只防「别的手机误投」，不防能读网络流量的人。协议写在 `receiver/PROTOCOL.md`。
- Mac 版走 Wi-Fi 时同样不加密；网页显示是纯 HTTP，令牌、画面、声音、输入全在明文里。官网在浏览器那一栏直接标了「只在信得过的网络里用」。
- shell 权限的注入服务只有 XDesk 能调用（README 口径），但它确实是这套「无 root」方案换来的特权通道；重启后需要重新激活，激活期间无线调试必须开着。
- PulseAudio 的匿名端口回退会被手机上任何应用用来录音与控制，官方建议优先用 cookie 方式。

再加一组运维层面的限制：一次只能有一个全屏应用或桌面占用显示器；Termux 与 XDesk 都得活着，激进的系统清理工具会杀掉它们；无线显示一个接收端只接一台手机；网页显示与无线显示共用机制，同一时间只能有一个浏览器或接收器。

## 六、项目状态：AI 写码、真机验收

仓库元数据（2026-11-12 查询）：`n2ray/xdesk`，2026-11-02 建库，GPL-3.0，Java，默认分支 `xdesk`，1269 commits、11 stars / 1 fork、0 open issue，已有 17 个 release，最新 `v0.5.1` 发布于 11-11。`master` 分支跟踪上游 Termux:X11，构建走 GitHub Actions，tag 触发签名发布。

官网与 README 末尾都有一段少见的坦白：作者 n2ray 说 XDesk 是他和 Claude 一起做的，自己决定做什么并在真实手机、显示器、投影、车机、Mac 上测试，大部分代码与文档由 AI 写。

验证范围则窄得多：README 的 Status 写明只在一台欧版小米 15 Ultra（25010PN30G，骁龙 8 Elite，HyperOS 3，Android 16，未解锁 bootloader）上日常使用，连国行同型号都没试过；Mac 版只在一台 M4 Mac 上测过。官网写着欢迎其他设备反馈，Android 11+ 是要求但「只在 Android 16 上测过」。

这跟本站前面写过的几条「AI 大规模产出 + 人工真机验收」是同一类信号：10 天出 17 个版本、上千提交，速度很吓人；但兼容性结论仍然只覆盖一台机器。读者能复用的应当是架构与思路，别把「作者日用」当成「你的手机能用」。

## 七、和前一天那篇稿子的分工

昨天写的《Termux 跑 Debian 13 桌面：难点是不被 Android 杀掉》，核心是 PRoot + Termux:X11 + PulseAudio 桥 + 一整套保活措施，跟 Android 的后台清理较劲。

XDesk 处理的是另一半：把已经跑起来的桌面送到另一块屏幕，并把输入送回来。它自己也不解决保活 —— README 明说 Termux 与 XDesk 都必须存活，系统清理工具照样能杀。两篇放一起看，正好是「手机当 Linux 工作站」这件事的两个不同瓶颈。

## 八、边界

- Reddit `.json` 接口 403，评论区未获取；帖子里的分数、评论数、发帖时间未核实，本文只用网页版正文与作者给的官网/仓库链接。
- 本文未安装 XDesk、未在任何手机上实测，也没验证 15–20 ms 延迟、12 Mbit/s 码率、GPU 加速与 Android Auto；这些均为作者自述或 README 口径。
- 部分中文表述取自官网中文页，英文技术细节取自 README；两者措辞不一致时以 README 为准。
- 版本号、star 数、release 数、设备清单均为 2026-11-12 查询时点，项目迭代很快，读时请以仓库为准。
- 官网/仓库未给出独立安全审计；`curl | bash` 与明文传输是官方自述的边界，本文不替项目做安全背书。

## 九、结论

XDesk 的技术含量不在「又装了一个 XFCE」，而在把 Android 的显示、输入、音频三条链路重新接到一块外接屏上：X server 留在 Termux 里、手机屏幕变成触摸板、shell 权限服务换掉 root、PulseAudio 把声音送回 App。再往外长出 Mac 接收端、Android 接收端、浏览器与车机。

但它是一个刚满 10 天、只在一台手机上验证、大部分代码由 AI 写的早期个人项目，无线与网页模式明文传输，还得每次重启重新激活。想尝鲜，先确认手机支持 USB-C 视频输出，读一遍 `install.sh`，并且只在可信网络里用无线功能；想当生产力方案，等更多机型的反馈更稳妥。

## Sources

- Reddit r/termux 原帖：<https://www.reddit.com/r/termux/comments/1xsrqz7/xdesk_run_your_termux_xfce_desktop_on_a_monitor_a/>
- XDesk 官网（中英双语）：<https://n2ray.github.io/xdesk/> ｜ 中文 README：<https://github.com/n2ray/xdesk/blob/xdesk/README.zh-CN.md>
- GitHub 仓库与 README：<https://github.com/n2ray/xdesk> ｜ releases：<https://github.com/n2ray/xdesk/releases/latest>
- 安装脚本：<https://github.com/n2ray/xdesk/blob/xdesk/xdesk/install.sh> ｜ 无线协议：<https://github.com/n2ray/xdesk/blob/xdesk/receiver/PROTOCOL.md>
- 上游 Termux:X11：<https://github.com/termux/termux-x11>
- 本工作区对照文章：<https://freelamp.com/articles/2026-11-11_termux-s26-ultra-debian13-proot-dex/>
