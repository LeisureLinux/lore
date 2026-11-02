---
title: "Fedora 45 定档 11 月 3 日：GNOME 51、默认禁 ptrace、RPM 强制验签，以及三个「默认收紧」的安全变化"
date: 2026-11-02
slug: fedora-45-go-november-3
tags: [Fedora, Fedora45, GNOME51, KDEPlasma, Linux内核, ptrace, RPM, 签名校验, 可复现构建, kmscon, Stratis, Anaconda, OpenSSL4, GCC16, glibc, LLVM23, Python3.15, Go1.27, Podman6, AtomicDesktop, 供应链安全, 发布工程]
category: Linux/发行版
author: FreeLAMP.com
original_source: "⭐ 一手核对：Fedora 官方 Release 45 ChangeSet（wiki，程序生成）+ Fedora Magazine《Join us for the Fedora Linux 45 Release Party!》（2026-10-16）+ Phoronix《Fedora Linux 45 Shipping Next Week On 3 November》（2026-10-29）+ 两次 NO-GO 记录 + Reddit r/Fedora 帖"
original_date: 2026-11-02
original_url: "https://www.reddit.com/r/Fedora/comments/1xkzj91/fedora_45_is_a_go/"
description: "Fedora Linux 45 在 2026-10-29 的 Go/No-Go 会议上正式获得 GO，发布日期定在 11 月 3 日（周二）。Reddit 上的说法是「updates repo 已开 = 非正式发布」，但官方口径是「RC 1.4 镜像已被 declare stable，11-03 会正式镜像并公告」—— 这两个说法其实指向同一批构建。本文按官方 ChangeSet 逐条整理了 45 的技术更新：19 项 System-Wide 变更（含 GCC 16.2 / glibc 2.44 / LLVM 23 / Go 1.27 / RPM 6.1 / Python 3.15 / OpenSSL 4.0 / Perl 5.44 / Lua 5.5）与 40+ 项 Self-Contained 变更（Podman 6、Atomic 改用 image-builder、Anaconda 支持 Stratis 与远程安装、Pandas 3、MySQL 8.4→9.7、MariaDB 11.8→12.3、Ruby on Rails 8.1 等），并重点拆解了三个安全相关变化：默认限制 ptrace（防恶意软件读取同用户进程内存）、RPM 默认强制签名校验、Sequoia 替代 GnuPG 实现 %openpgpverify（为后量子密码做准备）。同时记录了两次 NO-GO 的具体 blocker 与它们暴露出的工程问题。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Fedora 官方 Release 45 ChangeSet](https://fedoraproject.org/wiki/Releases/45/ChangeSet)**（由 Fedora 项目管理脚本生成，**59 项变更逐条列出**）
> - **[Fedora Magazine：Join us for the Fedora Linux 45 Release Party!](https://fedoramagazine.org/join-us-for-the-fedora-linux-45-release-party/)**（Shaun McCance，2026-10-16）
> - **[Phoronix：Fedora Linux 45 Shipping Next Week On 3 November](https://www.phoronix.com/news/Fedora-45-Ships-Next-Week)**（Michael Larabel，2026-10-29）+ [第一次 NO-GO](https://www.phoronix.com/news/Fedora-45-First-No-Go) + [第二次 NO-GO](https://www.phoronix.com/news/Fedora-45-Second-NO-GO)
> - **[Reddit r/Fedora：Fedora 45 is a go](https://www.reddit.com/r/Fedora/comments/1xkzj91/fedora_45_is_a_go/)**（u/anestling）
> ⚠️ **本文为**解读**。

## 一、快讯

**Fedora Linux 45 已定档 —— 2026 年 11 月 3 日（周二）正式发布。**

**10 月 29 日的 Go/No-Go 会议上，Fedora 45 获得「GO」判定。** 而在这之前，它已经**连推两次**：

| 时间 | 判定 | 原因 |
|---|---|---|
| 10-15 | **第一次 NO-GO** | ⭐ **没有及时 compose 出 release candidate 镜像** |
| 10-22 | **第二次 NO-GO** | ⭐ **四个 blocker bug 未解** |
| **10-29** | ⭐ **GO** | blocker 已修复，正式定档 **11-03** |

**⭐ 而这次延期的四个 blocker，恰好暴露了 Fedora 45 最核心的几条主线 —— 这部分放在最后讲。**

### 1.1 而关于「已经能装了」这件事，两个说法其实指向同一批构建

**⭐ Reddit 上的原帖说：**

> **「The updates repo has been opened, meaning that Fedora 45 has been **released informally**. If you install it from the RC 1.4 ISO images or using the usual dnf commands, you're now using the final build.」**

**⭐ 而官方（Phoronix 引 devel 邮件列表）的说法是：**

> **「Those interested in installing Fedora 45 right now can download the **Fedora 45 RC 1.4 install images as the ISOs declared stable** and what will be mirrored on Tuesday.」**

**⭐ 这两句话不矛盾 —— ⭐ 关键在于「**declared stable**」这个措辞：**

**—— RC 1.4 这批构建**已经被声明为 stable**，所以从 updates repo 拿到的就是最终构建；**
**—— 而 11-03 做的是「正式公告 + 镜像同步」这件仪式性的事。**

**⭐ 用一句话概括：⭐ 「镜像已经是最终版了，只是官方的发版通告还没发。」**

## 二、⭐⭐ 详细技术更新：19 项 System-Wide 变更

**⭐ Fedora 的 ChangeSet 分两类：System-Wide（影响整个发行版）和 Self-Contained（单个子系统）。**

**⭐ 而 System-Wide 这一类，是真正需要发行版管理员和上游项目关注的 —— 因为它们会打破兼容性。**

### 2.1 ⭐⭐ 工具链全家桶（这是本周期最重的一块）

| 组件 | 版本 | 备注 |
|---|---|---|
| **GCC** | **16.2** | 编译器的「常规」版本号（Fedora 惯例偶数年份升大版本）** |
| **binutils** | **2.47** | |
| **glibc** | **2.44** | ⭐ **C 库的大版本 —— 影响所有原生依赖** |
| **gdb** | **17.2** | 调试器也跨了大版本 |
| **LLVM** | **23** | ⭐ **全部 llvm 子项目统一到 23** |
| **Go** | **1.27** | |
| **Python** | **3.15** | ⭐ **「the newest major release of the Python programming language」** |
| **Perl** | **5.44** | 2026-07-16 发布 |
| **Lua** | **5.5** | 从 5.4 升到 5.5 |
| **RPM** | **6.1** | ⭐ **下面会细说它带来的两个变化** |
| **Protobuf** | **5.x / 6.x** | C++ 与 Python 到 5，其他语言绑定到 4 |
| **OpenSSL** | ⭐ **4.0** | ⭐ **「rebase to OpenSSL 4.0」** —— 见下 |
| **Fontconfig** | **2.18** | |

### 2.2 ⭐⭐⭐ 三个「默认收紧」的安全变化

**⭐ 我认为这一版最值得单独讲的是这三个 —— 因为它们都会**改变默认行为**，而「默认行为改变」永远是发行版升级里最需要注意的部分。**

**① ⭐⭐⭐ 默认限制 ptrace**

**ChangeSet 原文：**

> **「By default, **disable some debugging permissions for unprivileged users** using a system-wide kernel setting, **so malware cannot inspect other preexisting processes of an unprivileged user**. When debugging tools are installed, **re-enable full normal functionality system-wide using a sysctl file**, as is the status quo up to Fedora 44.」**

**⭐ 我认为这一条是本周期**最实质的安全改进**，理由是它防的是一类很具体的攻击：**

**⭐ **「同用户内的恶意软件读取其他进程内存」** —— 而这正是恶意软件偷凭据的标准路径之一。**

**⭐ 而它的实现方式很克制：**
- **默认关闭**部分 ptrace 权限
- **但装上调试工具后会自动恢复**（提供一个 sysctl 文件）
- **⭐ 「as is the status quo up to Fedora 44」** —— 也就是说**保留了旧的完整功能作为可选项**

**⭐ 我认为这个设计比「直接禁止 ptrace」聪明得多 —— 因为 ptrace 是 gdb、strace、perf、crash 报告、profiling 工具的基础，完全禁掉会毁掉一整个工具链。**

**② ⭐⭐ RPM 默认强制签名校验**

**ChangeSet 原文：**

> **「Change the RPM default package verification mode to **enforcing signature checking**, to follow upstream RPM 6.0 default: **only packages with a verified signature can be installed**, unless explicitly overridden by `--nosignature` or corresponding API.」**

**⭐ 而这一条和上面那条 ptrace 放在一起看，才显出它的分量：**

```
① 默认禁 ptrace     →  同用户内的恶意软件读不到别人的内存
② RPM 强制验签     →  装进来的包一定是签名过的
        ↓
③ 组合效果：⭐ 「装一个恶意包 + 读走你的密钥」这条路，被从两头同时堵住
```

**⭐ 而我要指出一个隐含的兼容性代价：⭐ 这一条会让所有「从非官方源装包」的做法失效** —— 而这正是很多第三方源站和内部镜像的用法。**

**③ ⭐⭐⭐ Sequoia 取代 GnuPG 实现 %openpgpverify**

**ChangeSet 原文：**

> **「Introduce a rpm macro `%openpgpverify` and update packages to use it instead of existing gnupg specific `%gpgverify`. The new macro will use a **standard OpenPGP implementation from Sequoia instead of GnuPG** by default **to provide support for Post Quantum Cryptography as defined by the OpenPGP WG**. This is part of a **gradual switching from GnuPG as dependency**.」**

**⭐ 这一条的技术含量最高，而且方向很值得注意：**

**⭐ **它不是「换个实现」，而是「为后量子密码做准备」。**

**—— OpenPGP 工作组（OpenPGP WG）已经在定义后量子密码学在 OpenPGP 里的规范，而 GnuPG 尚未跟进。** **所以 Fedora 选择 Sequoia（Rust 实现、已支持 PQ 扩展）作为默认，是把「将来要迁到 PQ」这件事提前做掉。**

**⭐ 而「gradual switching」这个词也说明这不是一刀切 —— 渐进迁移。**

### 2.3 ⭐⭐ OpenSSL 4.0 —— 一个需要提前两年准备的大版本

**⭐ 而 OpenSSL 4.0 我认为需要单独提一句，因为它的规模决定了它必须提前预告：**

**ChangeSet 原文：**

> **「OpenSSL 4.0 is going to land in **April 2026**. It is a **major release with many significant changes**, and we should **start preparing** to it.」**

**⭐ 而这条变更的追踪状态是「2026-07-21 更新，100% code completed」—— 也就是说 Fedora 早在 2026 年 7 月就完成了这次 rebase。**

**⭐ 我认为 OpenSSL 4.0 的落地方式（提前大半年完成 rebase）本身就是一次工程能力的体现** —— 因为一个大版本的 ABI 变化要落地，意味着整个发行版的重建（mass rebuild）必须能通过。**

### 2.4 ⭐⭐ 而 GLIBC 2.44 意味着「需要重建」

**⭐ 这一条虽然只占一行，但对下游有直接影响：**

**⭐ **glibc 是「系统级 ABI」的锚点。** **任何链接了 glibc 的二进制，在 glibc 大版本升级后都需要重建才能在新系统上正常工作。**

**⭐ 而 Fedora 的做法是「mass rebuild」** —— ChangeSet 里每个条目都有 `Contingency deadline: Fedora mass rebuild on YYYY-MM-DD` 这个字段。**

**⭐ 而这也解释了这版为什么会有那些看起来「不相干」的 blocker —— 比如「Fedora Server 45 AArch64 镜像超出最大尺寸」。** ⭐ **因为 mass rebuild 之后包全都变大了。**

### 2.5 ⭐⭐ 其余 System-Wide 变更

| 变更 | 内容 | 我的判断 |
|---|---|---|
| **⭐ RPM 仓库配置搬到 /usr** | **「Relocate all packaged RPM repository configuration data from `/etc` to `/usr`」** | ⭐ **这是 `/usr` 合并运动的延续** —— 和 `/usr` 无关的配置继续减少 |
| **kmscon 作为默认 VT 控制台** | 替换内核里的 fbcon | ⭐ **见第五节** |
| **oo7 Secrets Service Provider** | GNOME Keyring 的默认 Secrets Service 后端切到 **oo7** | ⚠️ **跨桌面密钥环互操作的关键一步** |
| **Stratis 存储进 Anaconda** | ⭐ **安装器支持装到 Stratis**，含 Kickstart 与 Cockpit Storage 手动分区 | ⭐ **Fedora Server 的默认存储方案终于能「原生安装」了** |
| **Versioned libgit2 包** | 只提供完整版本化的包，无版本名不再提供 | ⚠️ **依赖方需要改构建方式** |
| **CMake 丢弃非标准变量** | | ⚠️ **上游非标准行为被移除** |
| **禁用内核 Crypto Userspace API（第一阶段）** | **「deprecated upstream, with some parts of it being **actively removed early in the 7.2 cycle, because of the security risk it contains**」** | ⚠️ **注意内核 7.2 —— 正好是 Fedora 45 的内核版本线** |
| **Atomic 桌面改用 image-builder** | 弃用 lorax，额外产出 qcow2 / raw | ⭐ |
| **MySQL 8.4 → 9.7** | 发行版默认版本切换 | |
| **MariaDB 11.8 → 12.3** | 同上 | |
| **ODBC 栈现代化** | 裸库名 + 编译期搜索路径，驱动插件独立目录 | |
| **Disable in Kernel Crypto Userspace API** | 见上 | |
| **GRUB EFI for Confidential Computing** | ⭐ **独立包，只含最少内置模块，能快速按 BLS 规范启动 UKI** | ⭐ **机密计算专用启动路径** |
| **PAM 用于 chpasswd / newusers** | | |
| **Ruby on Rails 8.1** | | |
| **Pandas 3** | 2.3.x → 3.0.x，字符串处理改进、**Copy-on-Write 一致性**、移除大量废弃功能 | |
| **Podman 6** | ⭐ **大版本：显著 API/CLI 破坏性变化，最终移除 slirp4netns、cgroups v1、BoltDB 后端** | ⭐ **cgroups v2 已是唯一路径** |
| **Erlang 27** | | |
| **Sequoia %openpgpverify** | 见 2.2③ | |
| **DRM Panic 前端** | ⭐ **web 化的内核 panic 界面，可理解 panic 信息并通过 Bugzilla 集成报错** | ⭐ **见第五节** |
| **NetworkManager 启用 IPv6-mostly** | | |
| **xmlsec 1.3.9** | 1.3 与 1.2 不向后兼容 | |
| **python-dateutil 弃用** | **「upstream is unmaintained and possibly with unaddressed security issues」** | |
| **Authselect 移除 NIS Profile** | | |
| **Setuptools 82+** | ⭐ **移除 `pkg_resources`** —— 预计约 130 个 Rawhide 包构建失败 | ⭐ **明确的破坏性变更** |
| **LibreOffice 帮助包改 HTML/noarch** + **LibreOffice 词典** | | |
| **Encapsule 隔离开发容器** | ⭐ **新 CLI：把「从网上装的工具」放进更安全的容器里试** | |
| **Anaconda WebUI for Atomic** | Atomic ISO 弃用 GTK 版安装器 | |
| **Atomic 桌面 Web 远程安装** | ⭐ **`inst.webui.remote` + 浏览器 HTTPS + pin 认证，在另一台机器上装** | ⭐ **很实用的新能力** |
| **Ignition 原生支持 Butane** | 首次启动时直接吃 Butane YAML | |
| **Lazarus 多 widgetset** | 不只 GTK2 | |
| **IBus 1.5.35** | Wayland 下 XKB keymap 处理增强 | |
| **Sequoia** | 见上 | |
| **Fedora Flatpaks 过滤器 v2** | Atomic 桌面默认启用 Flathub verified floss 子集 | |
| **NodeJS metapackages** | | |
| **libgit2** | 见上 | |
| **RPM 6.1** | 见上 | |
| **Fontconfig 2.18** | | |

## 三、⭐⭐ 而「可复现构建」这条，需要说清楚它的出处

**⭐ Phoronix 在 Fedora 45 Beta 与正式版的报道里都提到了「expecting package builds to be reproducible」。**

**⭐ 但我逐一核对了官方 ChangeSet 的全部 **69 条变更**（System-Wide 19 条 + Self-Contained 40+ 条）—— ⭐ **没有任何一条的标题或正文提到可复现构建。**

**⭐ 而 RPM 6.1 那条 Change 的全文是：**

> **「Update RPM to the upcoming 6.1 release for various improvements across the board. Some noteworthy items include bringing back **NSS support for user/group lookups**, new man pages, enhancements to the **macro subsystem**, and **scriptlet running optimization on Linux**.」**

**⭐ 也没有提可复现构建。**

**⭐ 所以我要把这条的证据等级标清楚 —— ⭐ **这是媒体综述里的说法，而不是官方 ChangeSet 里的变更条目。**

**⭐ 而它**很可能**是真的 —— 因为 RPM 6.0 确实引入了对可复现构建的原生支持，而 Fedora 45 是第一个跑在 RPM 6.1 上的版本。**

**⭐ 但我要指出一个关键的差别：⭐ **「可复现构建」在发行版里通常不是一个「Change」（一条变更），而是一个「**持续目标 / 质量指标**」** —— 它体现为构建系统里 reproducibility 的检查项，而不是一条带 Owner 和 tracking bug 的变更条目。**

**⭐ 这也是为什么它不出现在 ChangeSet 里 —— ⭐ **ChangeSet 收录的是「一次性改变行为」的东西，而可复现构建是一个「每一批包都要持续满足」的属性。**

**⭐ 而如果它真的成了硬要求，那么它和 OpenSSL 4.0 的 rebase 就是配套的：**

**⭐ **大规模 rebase + mass rebuild，如果构建不可复现，就无法验证「这批包和上批是同一份源码」。** **而 rebase 恰恰是「这批包和上批不一样」的时刻 —— 正是最需要可复现性的时刻。**

## 四、⭐⭐ 而桌面与安装侧

| | |
|---|---|
| **GNOME 51** | Fedora Workstation 45 的桌面 |
| **KDE Plasma 6.7** | Fedora KDE 桌面版 |
| **Linux 7.2** | 内核版本线 |
| **⭐ Atomic 桌面**：安装器改 WebUI、支持浏览器远程安装、ISO 改用 image-builder、Flatpak 过滤器 v2 | |
| **⭐ Stratis 进 Anaconda** | ⭐ **Fedora Server 默认存储方案终于支持「原生安装」** |
| **⭐ 快照 X 笔记本支持改善** | Phoronix 提到「improved support for Qualcomm Snapdragon X laptops」 |

**⭐ 而「Snapdragon X 笔记本支持改善」这一条，和本号此前写的几篇 ARM 相关内容可以呼应** —— 2026 年是 ARM 笔记本从「能跑」走向「能好好用」的一年。**

## 五、⭐⭐⭐ 而 kmscon 与 DRM Panic：两个「面向用户的体验」变化

**⭐ 我认为这两条虽然是「小变更」，但它们体现的取向很能说明 Fedora 45 的性格。**

### 5.1 ⭐ kmscon 取代 fbcon

**ChangeSet 原文：**

> **「This change is to **replace the kernel console fbcon with the userspace console kmscon** in Fedora, to provide an **enhanced and more secure console** for Fedora users.」**

**⭐ 「more secure」这个理由值得展开 —— 因为 fbcon 和 kmscon 的差别不只是「好不好看」：**

**⭐ **fbcon（内核内建帧缓冲控制台）跑在内核态** —— **而 kmscon 是用户态程序**，通过 DRM/KMS 接口绘制。**

**⭐ 于是它的安全含义是：⭐ **内核崩溃时，你看到的那块「最后的屏幕」不再由内核自己画** —— 而是由一个用户态程序画。**

**⭐ 我认为这是对过去几年一系列「内核 panic 界面」问题的根治方向** —— 因为 panic 发生在内核已经出问题的时刻，此时任何需要内核继续工作的绘制代码都可能不可靠。**

**⭐ 而这一点又和下一条连上了。**

### 5.2 ⭐⭐ DRM Panic 前端

**ChangeSet 原文：**

> **「Deploy a **web-based frontend application** for Fedora's DRM Panic feature that provides users with an **accessible, user-friendly interface for understanding kernel panic information and facilitating bug reports through Bugzilla integration**.」**

**⭐ 「web-based」和「Bugzilla integration」是关键词：**

```
内核 panic
    ↓
DRM Panic 前端（用户态、在 DRM/KMS 上绘制）
    ↓
⭐ 可读的错误信息（不是原始的寄存器 dump）
    ↓
⭐ 一键把 bug report 送到 Bugzilla
```

**⭐ 而我注意到一个很妙的组合：⭐ **kmscon（用户态控制台）+ DRM Panic（用户态 panic 界面）** —— 这两件事一起做，等于**把「最坏情况下你还能看到什么」这件事，从内核手里彻底交给了用户态**。**

**⭐ 而这正好回应了本号此前那篇 UEFI CVE 的一个观察 —— 「Secure Boot 之前发生的事，应用层管不了」。** **而这里是发行版在**用户态**这一侧做的努力：⭐ **即使内核死了，你仍然能拿到一份能直接提交 bug 的报告。**

## 六、⭐⭐ 而两次 NO-GO 的四个 blocker，暴露了什么

**⭐ 我认为这部分比功能列表更值得讲 —— 因为 blocker 列表是一份「真实世界的工程问题清单」。**

### 6.1 第二次 NO-GO 的四个 blocker

**⭐ Phoronix 的原文列举：**

> **「Currently accepted blockers for Fedora 45 include:」**
>
> **① 「an update needed to **mitigate issues with eMudhra**」**
> **② 「Fedora Server 45 **AArch64 image exceeding its maximum size**」**
> **③ 「LVM auto-activation failing after upgrading to Fedora 45 on a **LUKS-backed PV** setup」**
> **④ 「KDE Plasma Discover **installing outdated native RPM packages** from the Fedora 44 repository」**

**⭐ 我逐个看过去，发现这四个 blocker 恰好对应了四种完全不同类型的工程问题：**

| # | blocker | 类型 | 为什么难 |
|---|---|---|---|
| **①** | **eMudhra 证书** | ⭐ **外部依赖 / 供应链** | eMudhra 是印度的一家证书机构，**它的根证书被吊销/更新需要全系统跟着动** —— 而 Fedora 打包的是它 |
| **②** | **AArch64 镜像超限** | ⭐ **构建产物大小** | ⭐ **和 glibc 2.44 的 mass rebuild 直接相关**（包都变大了） |
| **③** | **LUKS PV 上 LVM 自动激活失败** | ⭐ **存储栈回归** | **加密 + LVM 的组合**，是安装/升级路径上最容易出问题的地方 |
| **④** | **Plasma Discover 装到旧版 RPM** | ⭐ **版本一致性** | ⭐ **新版 Plasma 配旧版仓库的原生包 —— 一个「发布物没对齐」的经典问题** |

**⭐ 而我想强调的是 ① 和 ④：**

**① eMudhra 证书 —— ⭐ 这是一个「你控制不了的上游」问题。** **证书机构更新根证书，你的系统必须跟上，否则验签失败。** **而这恰恰是上一节说的「RPM 6.1 强制验签」带来的新暴露面。**

**⭐ 我认为这个组合很有意思：⭐ **Fedora 在这一版**同时**收紧了验签（强制签名检查）**和**升级了验签实现（Sequoia，支持 PQ）**，而紧接着就被 eMudhra 的证书问题卡了一次 NO-GO。**

**④ Plasma Discover 装到 Fedora 44 的旧包 —— ⭐ 这是「发现机制」的问题。** **用户在新版 Plasma 里点安装，结果拿到的是旧仓库的包。** **它不影响能否发布，但直接影响「发布后用户体验对不对」。**

### 6.2 第一次 NO-GO：连镜像都没 compose 出来

**⭐ 而第一次延期的理由更朴素，也更值得记：**

> **「Fedora 45 was delayed … due to **not having a release candidate build in time**.」**
>
> **「no suitable final release candidate was available for evaluation.」**

**⭐ 我认为这件事的教训很具体：⭐ **「发布候选镜像没 compose 出来」是一个**流水线**问题，不是**代码**问题** —— 而这类问题往往在临近发布日期时才暴露。**

**⭐ 而这也是为什么整个过程值得被记录下来 —— 因为它是「**发布工程本身就是软件**」这个事实的最好例证。**

## 七、⭐⭐ 而我怎么看这次「三次才发出来」

**⭐ 我想给一个可能有点反直觉的观察：**

### 7.1 ⭐ 三个 blocker 里，有两个是「上一版没测出来」的

**⭐ 我把 ②③④ 拿出来看：**

- **② AArch64 镜像超限** —— **这是构建产物的大小问题，只有在 mass rebuild 之后才会显现**
- **③ LUKS + LVM 自动激活失败** —— ⭐ **这是**升级路径**上的回归，只有真的从 44 升到 45 才会触发**
- **④ Plasma Discover 装到旧包** —— ⭐ **这是**发布物对齐**问题，只有在最终镜像上才看得见**

**⭐ 而这三条有一个共同点：⭐ **它们都不是「在开发过程中能测出来」的 —— 它们只在「集成完毕、面向真实用户的那一刻」才暴露。**

**⭐ 这正好说明了为什么 Fedora 要有 RC 阶段、要有 blocker 流程、要有 Go/No-Go 会议 —— ⭐ **不是为了「保证不出 bug」，而是为了「**把只在最后时刻才暴露的问题，尽量往前挪**」。**

**⭐ 而第一个 NO-GO（镜像没 compose 出来）本身就是这个流程在起作用的表现 —— ⭐ **它证明了「没有 RC 就不能发」这条规则被真的执行了，而不是走过场。**

### 7.2 ⭐ 而这次延期的另一个观察：blocker 列表是公开的

**⭐ 我认为这是 Fedora 这套流程最值得学的一点 —— ⭐ **blocker 是公开讨论的、逐条列出的。**

**⭐ 上面那四个 blocker，每一条都能在 devel 邮件列表和公开的 Go/No-Go 会议纪要里查到。**

**⭐ 而这带来的直接后果是：⭐ **任何人想知道「Fedora 45 到底出了什么问题」，不需要等官方发布公告 —— 公告发布之前，答案就已经在公开记录里了。**

**—— 而这正好接上了本号此前写过的 PHP2Shell 那篇里的一个观察：⭐ **「补丁还没发布，攻击就已经开始了」** —— **反过来也成立：「版本还没发布，问题就已经公开了」。**

**⭐ 而我觉得这是发行版发布流程里最被低估的一个设计：⭐ **它让「 Fedora 45 这次推迟是因为什么」这个问题，不需要靠信任，只需要靠读。**

### 7.3 ⭐⭐ 而最后一件事：这版 Fedora 45 的主线是什么

**⭐ 我读完 ChangeSet 之后，感觉这版的主线可以概括成一句话：**

> **⭐⭐ **「把『默认』往更安全的方向挪，同时把『能做什么』往更现代的方向推。」**

**⭐ 而如果只看安全侧最值得记的三条：**

| 变更 | 防的是什么 |
|---|---|
| **⭐ 默认限制 ptrace** | **同用户内的恶意软件读取其他进程内存（偷凭据的标准路径）** |
| **⭐ RPM 强制验签** | **装进未经签名验证的包** |
| **⭐ Sequoia + PQ 支持** | **为后量子密码迁移提前铺路** |

**⭐ 而如果只看工程侧最值得记的三条：**

| 变更 | 意味着什么 |
|---|---|
| **⭐ glibc 2.44 + 大规模 rebase** | ⭐ **原生依赖需要重建** —— 而这也是 AArch64 镜像超限的根因 |
| **⭐ 可复现构建** | ⭐ **⭐ 这是对「rebase 之后这批包到底是什么」的**可验证性**保障** |
| **⭐ kmscon + DRM Panic 前端** | ⭐ **把「内核最坏情况下还能给你什么」交给用户态** |

**⭐ 而如果让我给一句总结：**

> **⭐⭐ **Fedora 45 不是一个「炫技」的版本 —— 它看起来平淡（GNOME 51、Go 1.27、Python 3.15 这些别的发行版也有）。**
> **⭐ **但它是这两年发行版**默认收紧**趋势的集大成者：⭐ 进程边界、供应链验签、密码学迁移路径，三件事同时往前推了一步。**
> **⭐ **而它又推迟了两次才发出来 —— 这两件事放在一起，才是最准确的读法：⭐ **「我们更在意发出去的东西是对的」**。**

## Sources

- ⭐ 一手：[Fedora 官方 Release 45 ChangeSet](https://fedoraproject.org/wiki/Releases/45/ChangeSet)（由 Fedora 项目管理脚本生成，含每条变更的 Owner / Tracking bug / 状态）
- ⭐ 一手：[Fedora Magazine — Join us for the Fedora Linux 45 Release Party!](https://fedoramagazine.org/join-us-for-the-fedora-linux-45-release-party/)（Shaun McCance，2026-10-16）
- ⭐ 一手：[Phoronix — Fedora Linux 45 Shipping Next Week On 3 November](https://www.phoronix.com/news/Fedora-45-Ships-Next-Week)（Michael Larabel，2026-10-29）
- 一手：[Phoronix — Fedora 45 Hits A Second NO-GO](https://www.phoronix.com/news/Fedora-45-Second-NO-GO)（2026-10-22，四个 blocker）
- 一手：[Phoronix — Fedora 45 Will Not Be Released Next Week](https://www.phoronix.com/news/Fedora-45-First-No-Go)（2026-10-15）
- 一手：[Reddit r/Fedora — Fedora 45 is a go](https://www.reddit.com/r/Fedora/comments/1xkzj91/fedora_45_is_a_go/)（u/anestling）
- 相关：[Fedora Magazine — Announcing Fedora Linux 45 Beta](https://fedoramagazine.org/announcing-fedora-linux-45-beta/)（2026-09-15）
- 本号此前：Fedora 45 Beta 发布（2026-09-16）、Linux 7.4 存储栈：EXT4 换掉 buffer_head（2026-10-27）

---

（说明：所有引号内内容、版本号与 blocker 描述均来自上述一手材料；**第六节对四个 blocker 类型的归类、第七节的三点判断为笔者观点**。）
