---
title: "Termux 跑 Debian 13 桌面：难点是不被 Android 杀掉"
date: 2026-11-11
slug: termux-s26-ultra-debian13-proot-dex
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Reddit r/termux 原帖《I turned my S26 Ultra into a true, rock-solid Linux Workstation》（u/dex-linux-dev，2026-11-05，含全部评论与 r/SamsungDex  crosspost 数据）＋ 作者 GitHub 仓库 thecbr600/dex-linux-workstation 的 README、setup.sh、addon/install-gpu.sh 全文与 commit 时间线 ＋ 作者演示视频 YouTube oEmbed 元数据 ＋ Termux 官方 termux-app README（Android 12+ phantom process killer 公告）＋ termux/proot-distro README「Limitations」全节 ＋ PRoot 官方机制说明 ＋ Debian 官方 releases 页（13/trixie 发布时间）＋ Samsung 2019-10-18 停用 Linux on DeX 的官方邮件报道（9to5Google / Android Police）＋ Termux 官方关于 Google Play 版本弃用的 Discussion #4000"
original_date: 2026-11-05
original_url: "https://www.reddit.com/r/termux/comments/1xor5fv/i_turned_my_s26_ultra_into_a_true_rocksolid_linux/"
description: "本文核对 Reddit r/termux 上「把 Galaxy S26 Ultra 变成真正的 Linux 工作站」一帖，逐行读作者 GitHub 仓库的 setup.sh 与 install-gpu.sh，并与 Termux 官方、PRoot 官方文档对照。结论：这套方案的技术含量不在装 Debian，而在三处绕开 Android 的约束 —— PRoot 用 ptrace 做路径翻译以避开 root、Termux-X11 取代 VNC 直连 Android 图形层、PulseAudio TCP 桥把容器声音送回 Android；再加上 termux-wake-lock、关闭 phantom process killer、Chromium 渲染进程数限制与 dpkg-divert 保护包装脚本，才让桌面会话不中途消失。同时如实拆掉几处夸大：帖子标题写「未剪辑两分钟单镜头演示」，正文当时是 video is coming（视频 11-04 才首发、r/termux 帖 11-05）；README 称 Debian 13 是 testing branch，但 Debian 官网写明 13/trixie 是 2025-08-09 发布的 stable，13.7 更新于 2026-09-12；「性能对标 Apple M1」「70% 锁频完全消除降频」「25+ 小时续航」均为作者自述口径，无第三方基准；PRoot 官方明确 ptrace 会让编译/包管理明显慢于原生、无 systemd、无 cgroups/namespaces、无真 root、/proc 统计是固定快照。也记录安全代价：curl | bash 安装、Chromium --no-sandbox 且用 --test-type 隐藏警告条、PulseAudio TCP 匿名监听 127.0.0.1:4713、termux-x11 :0 -ac 关闭访问控制。评论区唯一实质反馈恰好指出 phantom process killer 与 DeX 显示切换导致 aaudio sink 悬挂两个隐患，作者承认后者在动态插接场景值得注意。"
published: true
---

> 一手：Reddit r/termux 原帖及全部评论（2026-11-05）｜作者 GitHub 仓库的安装脚本与说明
> 官方：Termux 项目公告、PRoot 发行版文档、Debian 发行页、三星 2019 年停用公告
>
> 本文据脚本原文与官方文档逐条核对，帖子里的宣传口径与可验证事实分开写。

11 月 5 日，r/termux 出现一个标题很满的帖子，原文写的是「I turned my S26 Ultra into a true, rock-solid Linux Workstation」：把 Galaxy S26 Ultra 变成一台完整可用的 Linux 工作站，Debian 13、不 root、Termux-X11、PulseAudio，还能和 Samsung DeX 同时跑。帖子里列了硬件、锁定 70% CPU 的省电策略、音频桥、防进程被杀的一整套配置，最后附了「未剪辑两分钟单镜头演示」和 GitHub 仓库。

容易读成「手机上装了个 Linux」。把作者仓库里两个安装脚本逐行读完，再看 Termux 和 PRoot 官方文档，会发现真正做出来的事是另一件：在 Android 这个不打算让你跑桌面会话的宿主上，把显示、声音、进程存活三条链路分别接起来，并且不让系统在几分钟后把整个环境悄悄杀掉。 装 Debian 反而是最简单的一步，`proot-distro install debian` 一行就完了。

## 一、先看清这套栈的每一层

作品来自 GitHub 仓库 `thecbr600/dex-linux-workstation`，2026-11-01 建库，GPL-3.0，帖子发出时 4 个 star、0 fork、0 issue。作者自述硬件是 Galaxy S26 Ultra / 16 GB RAM，系统 100% 原厂 Android、未 root、Knox 0x0  intact。

`setup.sh` 一共五步，把架构摊得很清楚：

| 层 | 用的东西 | 解决什么 |
|---|---|---|
| 容器 | `proot-distro install debian` | 不需要 root 拿到一套 Debian 13 arm64 用户态 |
| 桌面 | `xfce4` + `xfce4-goodies` + Chromium / GIMP / LibreOffice / mpv | 常规桌面应用 |
| 显示 | `termux-x11 :0`（`--shared-tmp` 挂 `$PREFIX/tmp/.X11-unix`） | 不用 VNC，X client 直接画到 Android 图形层 |
| 声音 | PulseAudio `module-native-protocol-tcp`，容器内 `PULSE_SERVER=tcp:127.0.0.1:4713` | 把容器里的声音送回 Android 扬声器/蓝牙 |
| 保活 | `termux-wake-lock` + 关闭 phantom process killer + Chromium 包装脚本 | 不让会话被内核休眠和 LMK 干掉 |

启动脚本 `~/desktop` 和 `~/mobile` 只差一个 `-dpi 240`（手机屏缩放），其余一样：先 `pkill` 掉残留的 `termux-x11` / `pulseaudio`、清掉 X11 锁文件，起 PulseAudio TCP，拉起 Termux-X11 的 Android Activity，然后 `proot-distro login debian --shared-tmp -- bash -c "export PULSE_SERVER=...; export DISPLAY=:0; dbus-launch --exit-with-session startxfce4"`。

README 里另有一步 GPU 插件：`install-gpu.sh` 装 `virglrenderer-android`，在容器里设 `GALLIUM_DRIVER=virpipe`、`MESA_GL_VERSION_OVERRIDE=4.0`，关掉 XFCE 合成器，启动脚本里多跑一个 `virgl_test_server_android`。也就是说，基础版 Chromium 是 `--disable-gpu` 的纯软件渲染，3D 加速是后加的第二阶段，而 Reddit 帖子正文并没有提这个插件。

## 二、真正的技术活：跟 Android 的三条约束较劲

### 显示：Termux-X11 取代 VNC

作者在开头点名了社区方案的老毛病 —— VNC  viewer 卡顿、音频不同步、Android 后台清理干掉 PRoot 会话。Termux-X11 的解法是不走网络帧缓冲：X server 作为独立 Android App 运行，用 `--shared-tmp` 把 `$PREFIX/tmp/.X11-unix` 挂进容器，X client 通过本地 UNIX socket 直连。X11 的 XRandR 扩展让旋转屏幕、改分辨率时客户端不用重启，这是帖子说「实时改分辨率而不用重启 X 客户端」的由来。

### 声音：TCP 环回，不是直通

音频没有反过来走「Android 把设备给容器」，而是 Termux 侧起一个 PulseAudio 守护进程，加载 TCP 模块并允许本机匿名连接；容器内只设 `PULSE_SERVER=tcp:127.0.0.1:4713`。Android 侧的 sink 仍在 Termux 进程里，浏览器和桌面应用发出的音频经 TCP 回环交给它，再由它送到扬声器或蓝牙。

这条链路有个真实的软肋，评论区唯一那条实质反馈就指在这里：`smarthoushai` 说 Termux 的 PulseAudio 构建坐在 `module-aaudio-sink` 上，DeX 显示切换可能把 sink 挂住，结果是静音，得重新加载 sink 而不必重启整个守护进程。作者回复承认「动态插接场景值得注意」，但强调自己日常固定工位下 TCP over PulseAudio 一直稳定、无掉音无延迟。两边说的其实是两种使用条件，都对。

### 保活：phantom process killer 才是那一关

Android 12 起系统会杀掉超过 32 个的 phantom（后台子）进程，还会处理 CPU 占用过高的进程。Termux 官方 README 顶部至今挂着 NOTICE 原话：可能看到 `[Process completed (signal 9) - press Enter]`，而 shell 其实不是自己退出的，并指向 issue #2366。对一个跑着 Chromium 多标签、编译器、XFCE、PulseAudio 的 PRoot 会话来说，这几乎是必然触发。

仓库 README 给了两条路：开发者选项里开「禁用子进程限制」并把 Termux / Termux-X11 电池设为不受限；或者一次性 ADB：

```bash
adb shell "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"
adb shell settings put global settings_enable_monitor_phantom_procs false
```

再加上 `termux-wake-lock` 挡深度休眠。评论者补了 `device_config get activity_manager max_phantom_processes` 用来确认上限，说 Shizuku 无数据线也能做。作者回复直接用了「mandatory」这个词 —— 不关掉，重后台任务就是静默消失。

同一层还有两个针对性补丁。一是 Chromium 包装脚本：`--renderer-process-limit=2`、`--js-flags="--max-old-space-size=512"`、缓存上限、关掉后台网络和组件更新，全是为了不让 LMK 有借口；脚本用 `dpkg-divert --add --rename --divert /usr/bin/chromium.real /usr/bin/chromium` 把包装器占住 `/usr/bin/chromium`，避免 `apt upgrade` 把它覆盖回去，另外写一条 Chromium 企业策略 `CommandLineFlagSecurityWarningsEnabled: false` 去隐藏 `--no-sandbox` 的黄色警告条。二是启动脚本每次先 `pkill` 并清 `$PREFIX/tmp/.X11-unix`、`.X*-lock`、`pulse-*`，等于用「每次干净重启」代替会话恢复。

## 三、它不是「真正的 Linux」：PRoot 的边界要讲清

标题里那句「真正的 Linux」最容易误导。PRoot 不是虚拟机，也不是容器运行时。Termux 官方 proot-distro README 写得很直白：它是 `chroot`、`mount --bind`、`binfmt_misc` 的用户态实现，靠 Linux 的 `ptrace` 拦截 guest 进程的系统调用、实时改写文件路径，所以不需要 root。用的是 Android 自己的内核，Debian 只提供用户态。

官方列出的限制，和这套「工作站」定位直接相关：

- `proot` 通过 `ptrace` 拦截每一个系统调用，编译、包管理这类文件系统密集型负载明显慢于原生执行；
- 没有真 root，UID/GID 是映射出来的，`mount` 真实文件系统、`iptables`、需要内核态权限的程序会失败；
- 没有 cgroups / namespaces，`systemd` / OpenRC 这类 init 系统不在范围内，只能跑单个长生命周期进程；
- 依赖内核模块的特性（FUSE、特定 iptables target、自定义 cgroup）不工作；
- Android 封锁部分 `/proc`，容器里 `top`、`uptime` 看到的是固定替身快照，不是实时数字；
- 不能嵌套 proot。

最后一条值得单独拎出来：作者 README 那张「~3.4%/小时、25+ 小时续航、<35°C」的功耗表，是在一个 `/proc/stat` 都是固定值的环境里给的工作量估算，没有第三方基准，也没有可比机型对照。同理，帖子说 70% 锁频「完全消除热降频、性能对标 2020 年 Apple M1」，是作者的主观体感，不是跑分。把这两句当实测数据引用就过头了。

顺带一处好查的事实错误：README 说 Debian 13 基于「较新的 testing 分支」，但 Debian 官网 releases 页写明 13 / trixie 是 2025-08-09 发布的当前 stable，最新点版本 13.7 发布于 2026-09-12；testing 是另一条线。这不影响脚本能跑，但说明文档写得比较赶。

## 四、演示视频与「rock-solid」的成色

帖子正文有一节标题是「未剪辑两分钟单镜头演示」，下面紧跟着的却是「视频稍后奉上」和「你将在视频里看到的内容（今天晚些时候发第二段）」，列了省电模式状态栏、`./mobile` 启动 XFCE、Chromium 四个重标签加 Lo-Fi 音频、物理旋转手机、GIMP 打开高分辨率素材、LibreOffice 加载系统规格文档、三应用满负载切换 —— 这些在发帖时都还是「将要展示」的清单，不是已经展示的结果。

视频链接后来由作者在评论区补上。YouTube 公开元数据给出的标题大意为「三星桌面模式上的免 root 十三代 Debian，七成处理器频率节能压测」，频道 the_rider，页面标注首发 2026-11-04、约 150 次观看；本文核对时 YouTube 对无登录请求返回 「登录以确认你不是机器人」，所以没有逐帧核验画面内容。帖子本身在 r/termux 只有 23 分、2 条评论，crosspost 到 r/SamsungDex 是 23 分、13 条评论；唯一的技术评论还是提隐患的那条。

「rock-solid」因此更准确的说法是：在一台固定摆放、外接显示、已关掉 phantom killer 的旗舰机上，作者把日常工作流跑通了。 它不是一个经过多机型、动态插拔、长时编译验证的通用结论。作者自己在 README 里也写了这是「有明确取向的概念验证与部署蓝图」，并把 PRoot 开销、virgl 桥接、后台同步列进未来工作 —— 那个措辞比 Reddit 标题克制得多。

## 五、想照着做，先看清代价

这套方案把「不 root」做成了卖点，但换来的是几处需要自己承担的取舍：

- 安装方式是 `curl | bash`。 README 的一行安装直接从 raw.githubusercontent.com 拉 `setup.sh` 管道给 bash，第二步 GPU 插件同理。仓库 11-01 建、11-10 还在改脚本（commit 时间线里有多次 `Update setup.sh`、`Add files via upload`），意味着你执行的内容随仓库当前状态变化。想用就先把两个脚本读一遍，别只复制那一行。
- Chromium 是 `--no-sandbox`。 渲染进程沙箱被关掉，并用 `--test-type` 和企业策略把那条黄色警告条藏起来，理由是「UI 干净、适合日用」。这在 PRoot 里是常见的兼容做法，但它是明确的安全降级：浏览器渲染侧少了一层隔离，而包装脚本还主动抹掉了本该提醒你的视觉信号。
- PulseAudio TCP 监听 `127.0.0.1:4713` 且 `auth-anonymous=1`。 限本机回环加 `auth-ip-acl=127.0.0.1` 已经收窄了面，但容器内任何进程都能匿名连上这个音频服务；GPU 插件的启动脚本还给 Termux-X11 加了 `-ac`（关闭 X 访问控制）。在单用户手机上风险有限，别把它当成多用户主机上的配置模板。
- Termux 必须从 F-Droid 或 GitHub Releases 装。 这条 README 写对了：Termux 官方 Discussion #4000 明确 Play 商店版本仍是 deprecated、属于 unofficial/forked 发布源，与 F-Droid / GitHub 版签名不同、不能覆盖安装。
- `curl | bash` 会改容器里的 `/usr/bin/chromium`。 `dpkg-divert` 保护的是包装脚本不被升级覆盖，代价是 Chromium 的真实二进制被挪到 `chromium.real`，以后排查浏览器问题要记得看的是哪个文件。

还有个历史背景值得放在结尾：Samsung 2019-10-18 发邮件给测试者宣布终止 Linux on DeX beta，明确 Android 10 及以后不再支持，且升级后无法回滚到 Pie；当年官方镜像只有 Ubuntu 16.04。作者 README 说这个项目称这个项目实现了当年官方曾承诺的能力，指的是这个空档。官方停掉的是一条需要厂商配合内核与系统镜像的路，社区填的是纯用户态那条路 —— 两者能跑的应用范围、性能与稳定性并不等价，但这套方案确实不需要解锁、不碰 Knox、也不求厂商点头。

## 六、事实边界

- 帖子与评论数据取自 2026-11-11 通过已登录 Chrome 读取的 Reddit 页面；`video is coming...` 为发帖正文原文，视频链接来自作者评论区回复，oEmbed 元数据为公开接口，视频画面未逐帧核验。
- 功耗、温度、续航、「对标 M1」「完全消除热降频」均为作者自述口径，无第三方基准；`/proc` 固定快照的限制来自 proot-distro 官方 README。
- PRoot 限制清单、phantom process killer 的 32 进程上限与 signal 9 现象，取自 Termux 官方 README 与 proot-distro README；ADB 命令取自作者仓库 README。
- Debian 13 发布时间与 testing 定义取自 debian.org/releases；Linux on DeX 停用日期与邮件内容取自 2019-10-18 的 9to5Google / Android Police 报道。
- 本文未实机复现该方案，也未验证 `install-gpu.sh` 的 VirGL 桥接在其它 Adreno 机型上的表现。

## 七、结论

这套东西值得看的不是「手机跑 Debian」，而是它把 Android 上跑 Linux 桌面的三个老问题拆开处理了：显示走 Termux-X11 的本地 socket 而不是 VNC，声音走 PulseAudio TCP 环回而不是等设备直通，进程存活靠 wake-lock 加关掉 phantom process killer 而不是祈祷后台别被清理。`dpkg-divert` 保住 Chromium 包装脚本、`pkill` 清锁文件代替会话恢复，都是被实际运维逼出来的细节。

它同时是一个边界清楚的演示：PRoot 共享 Android 内核、每次系统调用都要过 ptrace、没有 systemd 和真 root、`/proc` 是静态替身；浏览器为了不崩关了沙箱还藏起警告；安装靠 `curl | bash`。把标题里那句「真正的、坚如磐石的 Linux」 换成「在特定条件下可日用的一套用户态桌面」，信息的准确度会高很多，工程价值其实一点没少。

## Sources

- Reddit r/termux 原帖及评论（u/dex-linux-dev，2026-11-05）：<https://www.reddit.com/r/termux/comments/1xor5fv/i_turned_my_s26_ultra_into_a_true_rocksolid_linux/>
- 作者仓库 README / `setup.sh` / `addon/install-gpu.sh`：<https://github.com/thecbr600/dex-linux-workstation>
- 演示视频（oEmbed 元数据）：<https://www.youtube.com/watch?v=3X4EliaiAoY>
- Termux 官方 README（Android 12+ phantom process killer 公告）：<https://github.com/termux/termux-app>
- termux/proot-distro README「Limitations」：<https://github.com/termux/proot-distro>
- Termux 官方关于 Play 商店版本弃用的 Discussion #4000：<https://github.com/termux/termux-app/discussions/4000>
- Debian 官方 releases 页：<https://www.debian.org/releases/>
- Linux on DeX 停用报道（2019-10-18）：9to5Google、Android Police
