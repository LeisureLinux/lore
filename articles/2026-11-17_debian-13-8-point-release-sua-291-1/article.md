---
title: "Debian 13.8 预告：上百个包里，真正该先看的是哪几类"
date: 2026-11-17
slug: debian-13-8-point-release-sua-291-1
category: 技术/解读
author: FreeLAMP.com
original_source: "原文：Debian Stable Updates Announcement SUA 291-1《Upcoming Debian 13 Update (13.8)》，Adam D. Barratt，2026-11-17，发往 debian-release@lists.debian.org；完整清单由用户提供，包含日期（11-21 周六）、trixie-proposed-updates 由所有官方镜像 carry、security.debian.org 的包不在清单里但会尽量纳入、部分更新已在 trixie-updates、 debian-installer 随点发布重建、bug 报 BTS 并抄送 debian-release 等说明。清单按包名与理由列出上百个条目：aide / bird2 / bird3 / btrfs-assistant / clamav / composer / glibc / grub2 与 grub-efi-{amd64,arm64,ia32}-signed / intel-microcode / kwin / libwww-perl / libxml-bare-perl / mariadb / modsecurity / mongo-c-driver / neovim / nghttp2 / openstack 家族（aodh, glance, gnocchi, ironic-python-agent, manila, nova, octavia, watcher, zaqar）/ openssl / parted / patch / proftpd-dfsg / rsync / smarty4 / spice-vdagent / sssd / sudo / tzdata / libdatetime-timezone-perl / wireless-regdb / xiphos / zsh 等，含大量 CVE 编号与 Rust/Docker/glibc/openssl/pcre2 rebuild。＋ 在线一手核对：release.debian.org 首页「Planned point releases」表（13.8 从 11-14 改到 11-21；13.9 从 1-9 改到 2027-01-16；13.10 3-13、13.11 5-8；Debian 13 trixie 于 2025-08-09 发布；日期可能变、确认日期由 debian-stable-announce 公告）＋ Debian 官网 News 13.7 发布公告（2026-09-12，第七次点发布，主要是安全修正与严重问题，不替换旧介质，经常装 security 更新的用户无需大量升级，13.7 的 debian-installer bump linux ABI 至 6.12.107+deb13）＋ Debian 13 errata 页（点发布列表 13.1–13.7、proposed-updates 的 sources.list 写法与 apt update / apt upgrade 步骤）＋ release.debian.org/proposed-updates/stable.html 队列页（多个包版本状态，如 base-files 13.8+deb13u8、tzdata 2026f-0+deb13u1、freetype 2.13.3+dfsg-1+deb13u2 等，队列状态随时变化，仅用于核对清单条目确实在流程中）"
original_date: 2026-11-17
original_url: "https://www.debian.org/"
description: "解读 Debian 13（trixie）13.8 点发布预告 SUA 291-1。先讲点发布机制：不是新版本、不用丢掉旧安装介质，security.debian.org 的包不在清单里但会尽量纳入，包已在 trixie-proposed-updates（官方镜像 carry），13.8 日期由 11-14 改到 11-21，13.9 也改到 2027-01-16。然后把上百条清单按风险域分组解读而非逐条翻译：① glibc 与编译器/ABI 连锁（buffer over-read、越界写、栈溢出、wordexp 状态、UTF-32 解码挂起、cpuid 缓存、tzfile；一堆 Rust/Docker/glibc/openssl/pcre2 rebuild 说明 ABI/Built-Using 连锁）；② GRUB 与 Secure Boot（grub2 + 三个 signed 包同批 UAF 拒绝服务、secure boot bypass CVE-2026-97876、SBAT revision 提升，升级固件/签名链要留恢复手段）；③ intel-microcode 新上游版带 12 个 CVE；④ OpenStack 家族十几个包的授权绕过/命令注入/跨租户问题，适合控制面与 API 网络暴露面复核；⑤ 网络与文件服务（bird2/bird3 FlowSpec 边界、BGP timer、认证键；proftpd TLS DoS、授权绕过、link-following；rsync 未认证资源耗尽；nghttp2 请求/响应走私；modsecurity 规则绕过；sssd UAF/提权/路径穿越）；⑥ 数据与脚本栈（mariadb 多个代码执行/SQL 注入/授权绕过、composer 路径穿越与 Perforce URL 命令注入、mongo-c-driver 大量 DoS/数据损坏/信息泄露、neovim 文件名命令注入、smarty4 代码注入、libwww-perl 跨域重定向剥 Authorization）；⑦ 时区与安装器（tzdata 2026f、Manitoba / Northwest Territories、爱尔兰/伊朗/哥伦比亚历史时间戳、古巴永久 DST、上游签名密钥更新；debian-installer bump ABI 到 6.12.117+deb13）。给出行动清单：保持 stable/security 源、别为抢先加 proposed-updates，测试机先升、关注 GRUB/SBAT 与微码、OpenStack 控制面、备份与恢复路径；并写清边界（清单是预告不是最终发布说明，CVE 数不自行相加，队列页状态随时变化，未安装升级任何包）。"
published: true
---

11 月 17 日，Debian 发布团队发出 SUA 291-1：Debian 13「trixie」的第八次点发布 13.8 定于 11 月 21 日（周六）。清单长得吓人 —— 上百个包、密密麻麻的 CVE 编号。

但点发布不是「Debian 13.2 之类的新版本」。官方说得很清楚：「There is no need to throw away old "trixie" media.」—— 不用丢掉旧安装介质，安装的机器通过镜像升级即可；经常从 `security.debian.org` 装更新的用户，到时不会需要补很多包，因为多数安全更新会纳入点发布；安全源里发布的包不在这份清单里，但会尽量纳入。

我不想把上百行逐条翻译成中文 —— 那既不帮助判断，也很快过时。下面按风险域分组，挑出真正值得运维先看的部分。

## 一、先把时间线和方法说准

Debian 官网的「计划中的点发布」表显示：

- 13.8 从 11 月 14 日改到 11 月 21 日；
- 13.9 从 2027 年 1 月 9 日改到 1 月 16 日；
- 13.10 / 13.11 分别在 2027-03-13 / 05-08；
- 日期随时可能再变，最终日期以 `debian-stable-announce` 的正式公告为准。

13.7 是 2026-09-12 发布的上一版，那一版的 `debian-installer` 把内核 ABI 提到 `6.12.107+deb13`；这次 13.8 的安装器会 bump 到 `6.12.117+deb13`。

清单里的包已进入 `trixie-proposed-updates`，所有官方镜像都会 carry。公告特别提醒：发现 bug 请报 Debian BTS，并抄送 `debian-release@lists.debian.org` —— 对想帮忙测试的人来说，这是明确的反馈路径。但普通生产机不必为了抢先而手动加 `proposed-updates` 源：errata 页给了方法，也隐含了「你自己承担风险」的前提。

## 二、glibc 与 ABI 连锁：最值得整包升级的一组

`glibc` 这一条几乎是一份小型安全综述：

- buffer over-read（CVE-2026-6238 / 97399）、越界写（5435 / 19542）、栈溢出（6791 / 89092 / 95818）；
- `wordexp` 的 `WRDE_APPEND` 在非 NOSPACE 错误时应保留状态（6368）；
- buffer overflow（19499 / 18374）；UTF-32 解码挂起（77117 / 80489）；断言失败（8674）、竞态（86805）；
- 附带行为变化：`ld.so` 为 Intel CPU 缓存 cpuid 结果、`zic` 生成 TZif 时保留必要的新类型过渡。

这类底层库升级的风险不在「装不装」，而在连锁：清单里一大串 `Rebuild with updated rustc / docker.io / glibc / openssl / pcre2`（atuin、bpftop、btm、cosign、crowdsec、dar、docker.io、zsh……）说明 ABI 与 `Built-Using` 元数据必须跟着重做。对运维的含义是：这些包要作为同一批更新落下，不要只挑其中一两个升。

## 三、GRUB 与 Secure Boot：需要留恢复路径

`grub2` 与 `grub-efi-amd64-signed`、`grub-efi-arm64-signed`、`grub-efi-ia32-signed` 四个条目内容一致：

- 一组 use-after-free 拒绝服务（CVE-2025-54770 / 54771 / 61661–61664）；
- Secure Boot 绕过 CVE-2026-97876；
- 提高 SBAT revision；
- 修 riscv64 上的崩溃。

SBAT 提升意味着固件侧可能拒绝旧版 shim / GRUB 的回滚 —— 这是安全设计，但对双启动、自定义启动项、依赖旧安装介质的环境来说，升级前要确认有可恢复的启动路径和固件设置入口。这类包值得在测试机上先升一轮。

## 四、微码与硬件可信

`intel-microcode` 新上游版本带上 12 个 CVE（CVE-2024-24853、CVE-2025-31648 / 31936 / 31938 / 35973 / 35979、CVE-2026-20707 / 20713 / 20716 / 20760 / 20901 / 20917）。微码更新通常需要重启才生效；结合上面 GRUB/SBAT 一起看，这次点发布后的一次重启，实际上同时刷新了启动链与 CPU 微码 —— 建议在维护窗口内做，并留出回滚时间。

## 五、OpenStack 与控制面：授权类问题扎堆

清单里 OpenStack 家族几乎是整组出现：`aodh`（alarm queries 的 project scope 强制、CVE-2026-76878、授权绕过）、`glance`（无限制镜像下载、经 image import / HTTP location 访问内部服务、DNS rebinding、旧导入任务 URI 过滤）、`gnocchi`（不当访问控制）、`ironic-python-agent`（命令注入 43003、命令执行 66138、凭据提取 54422）、`manila`（未授权资源锁搜索、公共 share 策略）、`nova`（创建服务器时剥离内部 scheduler hints、WebSocket Origin 白名单污染与无限增长）、`octavia`（跨租户 QoS 策略授权、HAProxy 配置注入）、`watcher`（强制 oslo.policy）、`zaqar`（认证绕过与跨队列项目访问）。

共同点是授权边界与输入校验，不是简单的崩溃 bug。对跑 OpenStack 的组织，这次应把控制面 API 的网络暴露面、租户隔离策略与审计日志一起复核，而不只是打完包了事。

## 六、网络、文件服务与脚本栈

几类容易低估的：

- 路由与 BGP：`bird2` / `bird3` 修 FlowSpec 解码边界与校验、认证密钥处理、BGP timer 计算与校验、零长度参数处理；bird3 还修路由显示、hostentry 剥离、日志轮转、资源清理与 RCU journal 同步 —— 对跑 BGP 的机器属于「升级后要观察会话状态」的一类。
- 文件与传输服务：`proftpd-dfsg` 修 TLS 远端 DoS、授权绕过（119147）与 link-following（119364）；`rsync` 修未认证资源耗尽（119741）；`nghttp2` 修 HTTP 请求/响应走私（58055）；`modsecurity` 修规则绕过（52747 / 52761）；`sssd` 修 UAF（12610）、提权（2025-11561）、越界读、DoS、路径穿越与信息泄露。
- 数据与脚本：`mariadb` 新上游稳定版修多个代码执行、SQL 注入、授权绕过与路径穿越；`composer` 修路径穿越与恶意 Perforce URL 命令注入；`mongo-c-driver` 一口气修大量 DoS / 数据损坏 / 信息泄露；`neovim` 修文件名命令注入；`smarty4` 修代码注入；`libwww-perl` 在跨域重定向时剥掉 Authorization 头并默认拒绝不安全降级；`libxml-bare-perl` 修 C 解析器死循环与堆溢出。

这一组提醒的是：点发布里大量 CVE 不在你以为的「网络服务」里，而在开发工具、模板引擎、Perl 模块和数据库驱动中 —— 它们往往藏在 CI 与运维脚本的依赖树里。

## 七、时区、安装器与桌面小修

- `tzdata` 更新到 2026f：Manitoba 与 Northwest Territories、爱尔兰/伊朗/哥伦比亚历史时间戳、古巴永久 DST、上游签名密钥更新、巴西与乌克兰历史变更；`libdatetime-timezone-perl` 同步；`wireless-regdb` 更新监管信息。
- `debian-installer` 随点发布重建，内核 ABI 到 `6.12.117+deb13`。
- 桌面侧：`kwin` 修 Wayland 色彩管理与拔显示器时的 NULL 输出解引用；`btrfs-assistant` 防止在 Wayland 下覆盖用户 `xdg-runtime-dir`；一批 Thunderbird 插件（`allow-html-temp`、`mailmindr`、`xnote`）确保与 Thunderbird 153 兼容。
- `base-files` 为点发布更新 —— 它决定 `/etc/debian_version` 之类的版本标识，升级后看到「13.8」是正常的。

## 八、该怎么做

1. 保持 `stable` + `security` 源更新即可，不要为了抢先临时加 `trixie-proposed-updates` 到生产机。
2. 先在可牺牲的测试机上整批升级，重点观察 glibc 连锁包、GRUB / SBAT、微码重启后的启动链，以及 BGP / OpenStack 控制面。
3. 维护窗口内重启一次：微码与内核 ABI 变化都要重启才生效。
4. GRUB / Secure Boot 升级前留恢复路径：确认固件设置、备用启动项与恢复介质可用。
5. 备份与回滚点：尤其是数据库（mariadb）与安装器相关变更。
6. 想帮忙测试：按公告把发现的问题报 BTS 并抄送 `debian-release@lists.debian.org`。

## 九、边界

- 这份清单是 11-17 的预告（SUA 291-1），不是 11-21 最终发布说明；最终包列表以正式公告与镜像为准，可能增删。
- `security.debian.org` 发布的包不在这份清单里，公告只说会尽量纳入；本文未把任何 CVE 计数相加当作「本次修复总数」。
- `proposed-updates` 队列页状态随时变化，某些条目可能被更新版本取代；本文仅用它核对清单条目确实在流程中，不拿它当最终版本表。
- 未安装、未升级、未测试任何 13.8 包；升级建议基于清单理由与 Debian 官方机制，不构成对具体环境的兼容性承诺。
- 用户提供的清单与 Debian 官网的日期/机制交叉核对一致；13.8 日期来自 release.debian.org 的计划表，正式日期以发布公告为准。

## 十、结论

13.8 的价值不在「第 8 次点发布」这个编号，而在三件事：glibc 及其 ABI 连锁一次落地、GRUB / Secure Boot / 微码同批更新需要一次有准备的重启、OpenStack 与服务端组件的授权类修复扎堆。把清单按风险域读完，比盯着上百个 CVE 编号有用得多。

点发布是 Debian 把半年安全更新打包成「可整体验证的一次升级」的机制 —— 你仍然应该及时装安全更新，但趁点发布做一次完整回归与重启，是把「已打补丁」变成「真的可用」的机会。

## Sources

- SUA 291-1（Adam D. Barratt，2026-11-17，用户提供的完整公告与清单）＋ Debian release 邮件列表：<https://lists.debian.org/debian-release/>
- Debian Release 官网计划表：<https://release.debian.org/> ｜ proposed-updates 队列：<https://release.debian.org/proposed-updates/stable.html>
- Debian 官网 13.7 公告（2026-09-12）：<https://www.debian.org/News/2026/20260912> ｜ errata 与点发布列表：<https://www.debian.org/releases/stable/errata>
- Debian 安全公告：<https://www.debian.org/security/>
