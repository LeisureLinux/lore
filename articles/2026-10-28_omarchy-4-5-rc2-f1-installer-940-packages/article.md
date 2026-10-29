---
title: "Omarchy 4.5-RC2：安装器不再一个一个装包了，而是把 940 个包烤成一张镜像直接写进硬盘"
date: 2026-10-28
slug: omarchy-4-5-rc2-f1-installer-940-packages
tags: [Omarchy, Arch Linux, btrfs, zstd, installer, F1, Limine, Hyprland, 性能优化, Linux装机, 发行版, DHH, 浮动工作区, 每显示器工作区, 通知系统, 中国镜像, 安全, 凭据管理]
category: Linux/运维
author: FreeLAMP.com
original_source: "⭐ 一手核对：Omarchy v4.5.0-rc2 官方发布说明（GitHub Releases，2026-10-27 23:07 UTC）+ omacom/omarchy-iso 仓库的 builder/build-root-image.sh、builder/omarchy-image-write.c、orchestrator/phases_impl.py 三份源码 + 相关 PR 原文"
original_date: 2026-10-28
original_url: "https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2"
description: "Omarchy 4.5-RC2 最值得说的不是那些新应用，而是安装器架构的改变：F1 安装器不再用 pacstrap 逐个安装约 940 个包，而是在构建期把这份「对所有人都一样」的包集烤成一张 btrfs 镜像，用 zstd 的 seekable format 切成 256 KiB 独立帧、打上 seek table，安装时由一个自研 C 程序 omarchy-image-write 多线程并行解码并用 O_DIRECT 直接 pwrite 到目标分区，然后给它一个全新 fsid、扩容到整个分区，再做一次小规模 pacstrap 补上每台机器的差异。本文逐行核对了这三份源码，还记录了 RC2 相对 RC1 的真实增量（74 条 Fixes、10 条 Security、7 条 Deprecations）、Limine 超时从 6 秒降到 1 秒这个破坏性变更、以及 Omarchy 官方实测的中国镜像延迟数据。"
published: true
---

> ⭐ **本文核对的一手材料**（不是转述，是逐行读过的源码）：
> - **[Omarchy v4.5.0-rc2 官方发布说明](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2)**（GitHub Releases，**2026-10-27 23:07 UTC**，prerelease）
> - **`omacom/omarchy-iso`** 仓库三份源码：
>   - `builder/build-root-image.sh`（455 行，**构建期**烤镜像）
>   - `builder/omarchy-image-write.c`（535 行，**安装期**并行写盘）
>   - `orchestrator/phases_impl.py`（3892 行，**安装编排**）
> - 相关 PR 原文：#15966（Kernel 菜单）、#16256（中国镜像）、#16071/#16072（快捷键迁移）、#14484（Limine timeout，已关闭）
> - 仓库元信息实测：**`omacom/omarchy`**，**45,896 stars / 5,777 forks**，MIT，Shell，创建于 2025-06-01
> - ⚠️ **RC1 的解读见本号 2026-10-20 那篇**（aarch64 / Snapdragon X / N1X）—— 本文不重复，只讲 RC2 的增量
> 本文为**解读**。第三、四节的源码分析与第八节的判断为笔者补充。

## 一句话结论

**RC2 的发布说明里，最重要的一句话藏在最不起眼的位置：**

> **「The new F1 installer unpacks a prebuilt root image and adds this machine's packages on top, instead of installing about 940 packages one by one.」**

**⭐ 而我去翻了实现它的源码 —— 它比发布说明讲的有意思得多。**

**因为它的做法不是「打个 tar 解开」，而是一套相当讲究的镜像格式工程：**

| 环节 | 做法 |
|---|---|
| **构建期** | 用 pacstrap 把「对所有机器都一样」的那份包集烤进一张 **btrfs** 文件系统，**`compress-force=zstd:15`** |
| **打包** | 切成 **256 KiB 独立 zstd 帧** + **seek table**（zstd seekable format） |
| **安装期** | 自研 C 程序 **omarchy-image-write** 多线程并行解码，用 **`O_DIRECT` + `pwrite()`** 直接写进目标分区 |
| **落地后** | `btrfstune -m` 给一个**全新 fsid**（只改 superblock）→ `resize max` 撑满分区 → 重塑成 `@` / `@home` / `@log` / `@pkg` 布局 |
| **补差** | 一次**小规模 pacstrap** 补上每台机器不同的东西（音频固件、Tailscale、T2 内核等） |

**⭐ 我认为这才是 Omarchy 4.5 真正的分水岭 —— 它把「装系统」这件事从「跑 940 个包管理器事务」变成了「复制一张文件系统镜像」。**

## 一、RC2 相对 RC1 到底加了什么：先做个诚实的对比

**⭐ 我先把 RC1 和 RC2 的发布说明都拉下来做了逐条 diff —— 因为我不想重复写 RC1 已经讲过的东西。**

**结果发现 RC2 的发布说明结构完全重写了：**

| | RC1（2026-10-20） | RC2（2026-10-27） |
|---|---|---|
| **章节结构** | Headline Features / Performance / Aesthetics / Desktop / New Apps & Defaults / AI & Agents / Languages & Input / Hardware / System & Updates / Removed / Security / Fixes / New Contributors | **Breaking changes** / Highlights / Features / Improvements / Fixes / Security / Deprecations / Compatibilities |
| **条目数** | 约 200 条（含 78 位新贡献者） | **约 196 条**（Fixes 74 + Improvements 54 + Features 40 + Compatibilities 11 + Security 10 + Deprecations 7 + Breaking 10） |

**⭐ 而逐条对比的结果是 —— 大部分「新增」条目其实是 RC1 就有、只是 RC2 改了措辞或拆分了条目。真正的净增量是：**

| 分类 | 净新增 | 说明 |
|---|---|---|
| **Breaking changes** | **10 条（全新章节）** | ⭐ RC1 根本没有这个章节 |
| **Fixes** | **42 条** | RC1 已有 32 条，RC2 变成 74 条 |
| **Security** | **1 条** | RC1 的 9 条全部保留 |
| **Deprecations** | **7 条（全新章节）** | RC1 叫「Removed」 |
| **Compatibilities** | **11 条（全新章节）** | RC1 叫「Hardware」 |

**⭐ 而那 10 条「破坏性变更」我认为是最该被单独拿出来讲的东西 —— 因为它们会直接打断你的肌肉记忆。**

## 二、⭐⭐ 破坏性变更：快捷键的大规模重排

**⭐ 我把这 10 条完整列出来，因为这不是「更新后按一下就行」，而是「你的手要先重新学一遍」。**

### 2.1 启动菜单从 6 秒变 1 秒

> **「Limine waits 1 second instead of about 6 and boots quietly, so most of the time you won't see the menu at all.」**

**⭐ 我去查了实际配置，`omacom/omarchy` 仓库 `default/limine/limine.conf` 当前确实是：**

```
timeout: 1
quiet: yes
default_entry: 2
```

**—— 而这里有个值得说的细节。** 我查了 PR #14484（`limine: ship an active 3 s menu timeout in the template`），它的正文里写得很清楚：

> **「The template has carried the line commented (`#timeout: 3`) since 923d5fb (2026-01-05). Anything that copies this template over a machine's ESP menu leaves the menu with no `timeout:` line, and Limine then falls back to its built-in 5000 ms.」**

**—— 也就是说：那个 `#timeout: 3` 曾经被注释掉了整整大半年，所以实际生效的一直是 Limine 内置的 5000 ms。** **而 RC2 直接把 `timeout: 1` 打开了，并且加上了 `quiet: yes`。**

**⭐ 而发布说明给的使用方式也很体贴：**

> **「When you need a different entry or a snapshot, keep tapping any key (the down arrow works) while the machine starts and it'll stop at the menu. To keep the menu up longer for good, set your own `timeout:` in `/boot/limine.conf` (for example `timeout: 5`); updates leave a timeout you set alone.」**

**—— 「**按任意键**停下来」「**自己设的 timeout 不会被更新覆盖**」，这两个设计决定都值得点赞。**因为「把启动菜单藏起来」这件事，最容易出的问题就是「用户进不去 BIOS」和「更新把我的配置冲掉」。**

### 2.2 ⭐ 快捷键冲突被系统性地拆开

**⭐ 而这一组改动最值得看的，是它背后的设计思路 —— 我把它整理成一张表：**

| 功能 | 旧 | 新 |
|---|---|---|
| Calculator | `Super + Ctrl + Q` | **`Super + Shift + Q`** |
| Activity | `Super + Ctrl + T` | **`Super + Shift + T`**（`Super + Ctrl + T` 改为打开主题） |
| Network | `Super + Ctrl + W` | **`Super + Ctrl + N`**（`Super + Ctrl + W` 改为打开背景） |
| Nightlight | `Super + Ctrl + N` | **⭐ 无快捷键了**（挪到 `Trigger > Toggle`） |
| 关闭通知 | `Super + Alt + Comma` | **`Super + Alt + Comma`**（含义变为「关掉最后一张」） |
| 静音通知 | `Super + Ctrl + Comma` | **`Super + Ctrl + Alt + Comma`** |
| 打开通知历史 | `Super + Ctrl + Comma` | **`Super + Ctrl + Comma`**（现在给键盘控制权） |
| Apps | —— | **`Super + Alt + Space`**（从菜单改为 dock） |

**⭐ 我看出来的规律是：**

**① `Ctrl` 这一层被「腾」出来了 —— 改后的映射里，`Super + Ctrl + X` 几乎全部让位给「面板 / 主题 / 背景」这类系统级功能。**

**② Nightlight 被移出快捷键这件事最有意思。** **为什么？因为它原来占的 `Super + Ctrl + N` 和新的 Network 撞了。** **而它的解决方式不是「换一个键」，是「**干脆不给快捷键**」** —— 因为 Nightlight 是个「偶尔开一次」的功能，给它一个全局快捷键的收益本来就低，而它占的键位是有价值的。

**⭐ 我认为这是个好取舍 —— 快捷键是稀缺资源，不是越多越好。**

### 2.3 通知的键盘模型被重新设计

**⭐ 这一组是 RC2 里我最欣赏的改动，因为它把「通知」这个交互模型重新想了一遍。**

> **「`Super + Comma` acts on the newest card (dismisses it, opens it, or presses its one button) instead of only dismissing it.」**

**⭐ 「同一个键，根据卡片状态做不同的事」—— 这是一个真正的交互设计决策，而不是堆快捷键。**

**然后是这套完整的键盘模型：**

| 按键 | 作用 |
|---|---|
| `Super + Comma` | 作用于**最新**那张卡：关掉它 / 打开它 / 按它唯一的按钮 |
| `Super + Ctrl + Comma` | 直接跳到通知中心，**交出键盘控制权** |
| 数字键 | 按卡片上的按钮 |
| `Enter` | 点击卡片 |
| 方向键 | 在卡片之间移动 |
| `Super + Alt + Comma` | 关掉**最后一张**（原来是打开历史） |
| `Super + Shift + Alt + Comma` | 找回**过去一天**的通知 |

**⭐ 我注意到一个细节：`Super + Ctrl + Comma` 的语义从「打开历史」变成了「**交出键盘控制权**」。** **这意味着通知系统从「一个只能关掉的横幅」升级成了「一个可以用键盘操作的面板」** —— 而这是我认为 RC2 通知重做里最有价值的一步。

### 2.4 还有两个「容易撞车」的新默认键

> **「New defaults that could collide with bindings of your own: `Super + Q` (close window, alongside `Super + W`), `Super + A` (select all), `Super + M` (minimize to the dock), `Super + Grave` and `Super + Shift + Grave` (Quake console), `Super + Alt + L` (previous layout), `Super + Shift + Ctrl + Arrows` (move a window to another monitor), `Super + Ctrl + Alt + C` (screenshot), `Super + Ctrl + Alt + E` (world clock), `Super + Ctrl + Alt + F` (full screen desktop), and holding `Right Alt` for push-to-talk dictation.」**

**⭐ 而这一整段其实是 Omarchy 第一次在发布说明里明确写出「**这些键可能和你自己的绑定冲突**」** —— 这是一个诚实度上的进步。**

## 三、⭐⭐⭐ F1 安装器：我去读了它的源码

**⭐ 这是全文我最想写的部分。而它之所以值得单开一节，是因为发布说明只用了一句话，而源码里的信息量大概是那句话的五十倍。**

### 3.1 设计前提：先想清楚「什么是不变的」

**`builder/build-root-image.sh` 的开头注释把这个思路讲得非常清楚：**

> **「The target install is the same ~900 packages for everyone; only audio firmware, Tailscale and the T2 kernel vary per machine.」**

**⭐ 换句话说，设计者先做了一次「差异分析」：**

| | 内容 |
|---|---|
| **不变的部分** | **约 900~940 个包**（对所有人一样） |
| **变的部分** | **音频固件、Tailscale、T2 内核**（每台机器不一样） |

**—— 而这正是「可以烤成镜像」的充要条件。** **如果每台机器要装的东西差异很大，这个方案根本不成立。**

### 3.2 构建期：pacstrap → btrfs → zstd:15

```
IMAGE_COMPRESS="compress-force=zstd:15"
```

**⭐ 这里有个很容易被忽略但很讲究的细节，注释里专门解释过：**

> **「Forced zstd at a higher level than the installer's own compress=zstd (level 3): btrfs's incompressibility heuristic declines a lot of data in this tree that zstd handles fine, and the level only costs build time. **The image is written to the target as it is, so neither choice affects install speed**; the installed system writes new data at its own mount option either way.」**

**⭐ 我觉得这段注释值得展开，因为它体现了一种很成熟的取舍思维：**

**—— 「构建期慢一点无所谓，压缩率高一点是白赚的」。** **而且它明确指出「镜像原样写到目标盘，所以这个选择不影响安装速度」** —— 这解释了为什么敢用 level 15。

**⭐ 而 `compress-force` 这个选项本身也很关键：**

**普通 btrfs 的 `compress=zstd` 有个「可压缩性启发式」** —— 它会先采样数据，觉得「这块压不动」就**放弃压缩**。**而 `compress-force=zstd:15` 绕过了这个启发式** —— 对这个包集来说，btrfs 的判断经常是错的，而 zstd 15 压得动。

**—— 这是一个「上游默认行为不适合你的具体场景」的典型案例。**

### 3.3 ⭐ 打包格式：zstd seekable format

**⭐ 而这是整套设计里最漂亮的部分。**

**`builder/omarchy-image-write.c` 的开头注释：**

> **「`zstdcat image.zst | dd oflag=direct` is one thread that decodes, copies and writes. Here the image is a sequence of independent zstd frames of FRAME_SIZE bytes each, followed by a seek table listing every frame's compressed and decompressed size (zstd's seekable format, as in the zstd tree's contrib/seekable_format).」**
>
> **「From the table alone the target offset of every frame is known before anything is decoded, and N threads can each take the next frame, decode it into their own buffer and pwrite() it with O_DIRECT.」**
>
> **「The seek table sits in a skippable frame, so the file stays an ordinary zstd file — `zstdcat` still works on it.」**

**⭐ 我把这套机制拆开讲，因为它的设计非常漂亮：**

```
omarchy-root.img.zst 的内部结构：

┌─────────────────────────────────────────┐
│  Frame 0  (256 KiB 解压后)              │  ← 独立 zstd 帧
├─────────────────────────────────────────┤
│  Frame 1  (256 KiB 解压后)              │  ← 独立 zstd 帧
├─────────────────────────────────────────┤
│  ...                                     │
├─────────────────────────────────────────┤
│  Frame N  (256 KiB 解压后)              │
├─────────────────────────────────────────┤
│  ★ SEEK TABLE（放在一个 skippable frame）│  ← 每帧的压缩/解压尺寸
└─────────────────────────────────────────┘
```

**⭐ 而这样设计换来三个东西：**

**① 完全并行。** **因为帧与帧之间没有依赖，N 个线程可以各自取下一帧、独立解码、独立 `pwrite()`。** **而传统的 `zstdcat | dd` 是单线程的 —— 解码、拷贝、写入串行。**

**② 定位精确。** **「从表里就知道每一帧的目标偏移」** —— 所以写入是**按目标偏移直接 `pwrite()`**，而不是顺序追加。**

**③ 仍然是普通 zstd 文件。** **因为 seek table 放在 skippable frame 里，`zstdcat` 照样能解开整个文件。** **—— 这是一个很克制的设计：为了并行而增加的元数据，没有破坏文件的通用性。**

**⭐ 我还注意到一个细节 —— 稀疏写入的优化：**

```c
/* a write leaves frames that decode to all zeros unwritten, as dd conv=sparse */
```

**—— 解压出来全是零的帧就**不写**。** **在文件系统镜像里这意味着大量「稀疏区域」不必落盘。**

**⭐ 另外它的写入路径有两条：**

```c
with _time_step("F1.image_write (parallel frames, O_DIRECT)"):   # 多线程 + O_DIRECT
with _time_step("F1.dd (zstdcat | dd oflag=direct)"):            # 退路：传统管道
```

**—— 主路径是多线程并行写；失败了退到传统的 `zstdcat | dd`。** **这是很典型的工程稳健性做法。**

### 3.4 落地：全新 fsid、扩容、重塑布局

**⭐ 而写完之后还有几步，每一步都有讲究：**

**① 给一个全新的 fsid**

```python
# -m sets a fresh fsid via the METADATA_UUID feature (kernel 5.0+) by
# writing the superblocks only; -u rewrites every metadata block of the
# 4.5 GB image, which takes 0.8-2.0 s. The visible UUID (blkid, fstab,
# snapper) is the new one either way; two installs from the same image
# are distinct filesystems to the kernel because they differ in fsid.
with _time_step("F1.btrfstune -m (new fsid via metadata_uuid)"):
```

**⭐ 这一段我反复读了三遍，因为它体现的是「对 btrfs 语义理解到位」的细节：**

**—— 用 `-m`（只改 superblock）而不是 `-u`（重写每个 metadata block）。** **因为后者在 4.5 GB 的镜像上要 **0.8~2.0 秒**。**

**—— 而更要紧的是最后那句：** 「两次从同一镜像装出来的机器，**在内核看来是不同的文件系统，因为它们的 fsid 不同**」。**

**⭐ 我认为这一句才是这个 `-m` 存在的真正理由。** **因为镜像可以多台机器共用，如果 fsid 相同，内核会认为它们是同一个文件系统 —— 那就麻烦了。**

**② 扩容到整个分区** —— `btrfs resize max`，然后重塑成 `@` / `@home` / `@log` / `@pkg` 的子卷布局。

**③ 把预构建的 UKI 搬到 ESP** —— 这一步也在源码里有专门说明：

> **「Build the UKI here, once, so the installer copies it to the ESP and skips the ~4 s of mkinitcpio, ukify and limine-entry-tool on the target.」**

**⭐ —— 又省下约 4 秒。**

**④ 最后补差** —— 一次小规模 `pacstrap`，装上这台机器特有的东西。

### 3.5 ⭐⭐ 而且它还防住了「坏安装介质」

**⭐ 这一条是我在源码里发现的、发布说明完全没提的东西 —— 我认为它比「快」更重要。**

**`omarchy-iso` 仓库 README 里有一个集成测试场景叫 `corrupt-image`：**

> **「`corrupt-image` proves a bad install medium is refused before the disk is touched. It copies the ISO and flips one byte a megabyte into the root image stream itself — addressed from the extent xorriso reports out of the ISO9660 directory records, so the damage lands in the shipped bytes and nowhere else — then autoinstalls from that copy: `omarchy-root-image-verify.service` (which hashes the image at boot, while a user would be in the configurator) must fail, the install must halt in its pre-flight phase with the "re-flash" advice on screen, and the target disk must still have no partition table.」**

**⭐ 我把这条测试的逻辑拆开：**

| 环节 | 做法 |
|---|---|
| **注入损坏** | 复制 ISO，**每兆字节翻转一个字节**，且**用 xorriso 从 ISO9660 目录记录里算出偏移**，确保破坏落在真正出货的字节上 |
| **验证时机** | `omarchy-root-image-verify.service` **在启动时就开始哈希**，而那时用户还在配置界面里 —— **也就是说验证和用户的等待时间重叠了** |
| **失败行为** | 安装必须**在预检阶段就中止**，屏幕上给出「请重新烧录」的提示 |
| **⭐ 关键保证** | **「目标磁盘必须仍然没有分区表」** |

**⭐ 我认为「目标磁盘仍然没有分区表」这一条是整个设计里最重要的安全属性。**

**因为镜像方案天然带来一个新风险：** **传统 pacstrap 装到一半失败，你可以重跑；但如果「写镜像 + 写 fsid + 扩容 + 重塑子卷」这套流程做了一半失败，磁盘上就是一个半成品 —— 而且它看起来像是装好了。**

**—— 而「失败时磁盘一个分区都没有」这个保证，把这个问题彻底消掉了：要么成功，要么磁盘没被动过。**

**⭐ 我认为这是这个 F1 设计里最值得学习的一点 —— 而且它只写在测试 README 里，发布说明一个字都没提。**

### 3.6 ⭐ 那句「安装时间减半」到底怎么来的

**⭐ 老实说，发布说明只说了「installs in about half the time」，但我在源码里没找到具体的秒数基准。**

**我找到的是 `bin/omarchy-iso-installer` 里一个预览用的模拟脚本，它列出了 11 个阶段的时长估算：**

```
"Starting installation"           0.5
"Preparing live environment"      0.8
"Preparing install target"        0.3
"Installing Arch + Omarchy"       5.0      ← 这一项被 940 个包吃掉了
"Configuring hibernation"         0.4
"Configuring system"              1.2
"Finalizing Limine boot"          1.0
"Finalizing user"                 1.0
"Configuring login"               0.6
"Configuring DNS resolver"        0.3
"Validating boot setup"           0.8
```

**⭐ 而这个「5.0」就是被 F1 替换掉的那一项。** **注意这是**预览模拟**用的假数据**（脚本自己会 `mkdir` 一堆假包目录来喂进度条），不是实测 —— 但它至少印证了「安装系统」这一阶段在旧流程里占了总时长的大头。**

**⚠️ 而我要诚实地说明：** **源码里我确实没找到「减半」这个数字的实测出处，所以这个「大约一半」我只能按官方说法转述，不做独立背书。**

## 四、⭐⭐ 除了安装器，RC2 还有两条我认为分量很重的线

### 4.1 ⭐ 中国镜像 —— 而且它带实测数据

**⭐ 这是 RC2 里我觉得对一个中文读者最有实际价值的一条：**

> **「Download packages from Omarchy's China mirrors on installs in China by @emirb, @xdanger in #16256」**

**⭐ 而 PR #16256 的正文里带着**实测数据**，这在发行版 PR 里并不常见：**

> **「Packages reach mainland China slowly from the `.org` servers: from 20 Globalping probes in mainland China, `pkgs.omarchy.org` answered in 909 ms median, 1,440 ms worst, and its China replica `pkgs.omarchy.cn` in 364 ms and 1,181 ms.」**

| 源站 | 中位延迟 | 最差 |
|---|---|---|
| `pkgs.omarchy.org` | **909 ms** | 1,440 ms |
| `pkgs.omarchy.cn` | **364 ms** | 1,181 ms |

**⭐ 我把这两组数字放在一起看，能读出两件事：**

**① 中位延迟差了 2.5 倍** —— 这在装 940 个包时会累积成非常明显的等待。

**② 但最差值只差 259 ms** —— **这说明 `.cn` 副本并没有完全避开拥堵，只是把「典型情况」变快了。**

**⭐ 而 PR 里还说明了实现方式：**

> **「This puts Omarchy's China replicas first on installs in China, with the `.org` servers kept as the fallback.」**
>
> **「One renderer for pacman's files. `omarchy-apply-pacman` builds `pacman.conf` and the mirrorlist from the platform's channel templates, then this machine's regional additions.」**

**—— 关键在于它不是「二选一」，而是「**中国源优先，官方源兜底**」，且**所有 pacman 配置文件由同一个 renderer 生成**（避免两套逻辑漂移）。**

**⭐ PR 还提到这只是更大工作的一部分：**

> **「This is the first part of @xdanger's #13690, split out so it can be reviewed and merged on its own.」**

**—— 所以中国的 Omarchy 支持还在推进中。**

### 4.2 ⭐ Update > Kernel 菜单

**⭐ 这是 RC2 新增的一个功能，我觉得它解决的是一个真实存在的痛点。**

**PR #15966 的正文：**

> **「When more than one kernel is installed, a new **Update > Kernel** menu sits under Channel. It lists the installed kernels, puts a ✓ next to the one Limine boots by default, and uses the wide layout Fonts uses so long names like `linux-omarchy-bore-o3-exp` fit. Picking one switches the default with a single pkexec prompt.」**

**⭐ 而实现方式（`omarchy-kernel get`）的描述透露了一个细节：**

> **「Config files are read in limine-entry-tool's precedence, so `/etc/default/limine` wins over drop-ins. Each pattern is matched against the installed kernels' `pkgbase`. If a wildcard matches several kernels, only `/boot/limine.conf` (root-only) k…」**

**—— 它复用 Limine 的配置优先级模型来解析「当前默认内核」，并且明确区分了「用户能改的」和「只有 root 能改的」。**

**⭐ 我为什么觉得这个功能重要？** **因为「装多个内核」是 Arch 系用户的常规操作**（比如你正在测试新内核，或者需要某个特定内核支持你的硬件）。**但「切默认内核」这件事以前要么要手改 `limine.conf`，要么要重装。**

**—— 而在这个版本之前，还有一条相关的 bug 修复：**

> **「Fix the kernel migration stopping on machines that boot with GRUB or systemd-boot by @manuaudio in #14188」**

**⭐ 也就是说，「换内核」这个动作此前在 GRUB / systemd-boot 的机器上是会卡住的** —— 而那正是「传统 bootloader 用户」。

## 五、⭐⭐ 74 条 Fixes 里，有几条值得单独点名

**⭐ RC2 的 Fixes 从 RC1 的 32 条涨到 74 条。** **而我挑出来的这几条，共同点是「它们影响的是「升级能不能顺利走完」这条主线」：**

| 修复 | 为什么重要 |
|---|---|
| **「Fix upgrades that could leave a kernel image without its `root=` parameter」** | ⭐ **升级后开不了机** —— 而且是内核镜像级损坏 |
| **「Fix switching from edge to stable or RC leaving the machine on an old build」** | ⭐ **换通道不生效** —— 看着是新版本，跑的是旧的 |
| **「Fix the kernel migration stopping on machines that boot with GRUB or systemd-boot」** | ⭐ **换内核在非 Limine 机器上卡住** |
| **「Fix the Quattro upgrade resetting the default browser to Chromium」** | ⭐ **升级把用户的浏览器设置冲掉了** |
| **「Fix a failed mise tool download stopping the rest of a system update」** | ⭐ **一个工具下载失败，整个系统更新中断** |
| **「Fix the FIDO2 migration being marked done before it was resolved」** | ⭐ **迁移被误标为已完成** |
| **「Fix the Quattro upgrade stopping on background names with non-ASCII characters」** | ⭐ **非 ASCII 字符导致升级中断** |
| **「Fix free-space installs that could take an existing partition for a new one」** | ⚠️ **⚠️ 安装可能占用已有分区** |
| **「Fix an install next to another Omarchy removing that install's boot entry」** | ⚠️ **装第二台 Omarchy 会破坏第一台的启动项** |
| **「Fix factory reset erasing other systems' boot entries」** | ⚠️ **恢复出厂设置会抹掉别的系统的启动项** |

**⭐ 我认为这几条共同勾勒出 RC2 的主线 —— 它在做一件很不「炫」但极有价值的事：**

**⭐ 让「升级」这件事在各种非标准环境里都能走通。**

**而这恰恰是 RC1 那一大堆新功能（大模型、浮动工作区、通知系统）落地之后必须补的功课** —— **因为再多的新功能，用户也得先能顺利升上来。**

## 六、⭐ Deprecations：被移除的东西，和被替换的东西

**⭐ RC2 新增了 `Deprecations` 章节（RC1 叫 `Removed`），7 条里最有意思的是这条：**

> **「Replace the Gemini coding agent with Antigravity by @sanjyay in #6900」**

**⭐ 加上另外几条替换：**

| 被替换 | 换成 |
|---|---|
| **Gemini coding agent** | **Antigravity** |
| **Xournal++**（PDF 标注） | **Signed** |
| **Disk Usage TUI** | **Disktree** |
| **Lazydocker** | （新安装不再带） |
| **OBS Studio / Kdenlive** | （新安装不再带） |
| **clang** | （只在 Rust 开发环境里装，不再人人装） |
| **Azerbaijani 键盘布局** | （移除，因为它实际装的是法文 AZERTY） |

**⭐ 我认为最后这一条特别能说明这个项目现在的品味：**

> **「Remove the Azerbaijani keyboard choice, which installed French AZERTY by @dhh in #14877」**

**⭐ 一个存在了挺久的 bug —— 「阿塞拜疆键盘布局」实际装的是法文 AZERTY** —— 被直接删掉了，而不是去修。**

**—— 而删掉它比修它更正确的理由是：** **「阿塞拜疆语用拉丁字母」是 1991 年之后的标准（AL 字母表），AZERTY 是 1980 年代的方案。** **所以旧的那个选项本来就是过时的。**

**⭐ 我注意到三条替换都不是「换皮」，而是**换了产品定位**：**

| 旧工具 | 定位 | 新工具 | 定位 |
|---|---|---|---|
| Xournal++ | 通用 PDF 标注 | **Signed** | **签字场景**（放签名、文本、日期，存签字副本） |
| Disk Usage TUI | 文本界面 | **Disktree** | **treemap 可视化**，按类型着色，**特别标出可再生缓存** |
| Tensaku | 截图 | **Omasnap** | 截图 + 通知里直接带「打开 / 编辑」按钮 |

**⭐ 而 Disk Usage TUI → Disktree 那条改动里有个细节值得提：**

> **「Disktree replaces the Disk Usage TUI with a treemap of what fills a disk, colored by kind, with the regenerable caches worth a look called out, so you can mark what should go and remove it.」**

**—— 「**特别标出可再生的缓存**」这个设计很聪明。** 因为磁盘占用的分析里，真正的痛点不是「什么占了空间」，而是「**哪些是删了也无所谓、哪些删了要出事**」。** 工具帮你做这个区分，比单纯列个目录有用得多。**

## 七、⭐ 10 条 Security：值得单独看的两条

**⭐ RC2 的 Security 章节有 10 条，其中 RC1 已有 9 条，新增 1 条：**

> **「Remove fingerprints from the reader's own storage when removing them by @scottjones in #16403」**

**⭐ 而我更想说的是它和另一条放在一起看，形成了一个完整的思路：**

> **「Remove saved fingerprint templates for the invoking user on reset by @AFOliveira in #13049」**

**—— 两条合起来讲的是同一件事的闭环：**

**① 恢复出厂时，要删掉**为这个用户保存的**指纹模板；**
**② 删除指纹这个动作本身，要真的从**指纹读取器自己的存储**里删掉，而不是只从系统的记录里删。**

**⭐ 我认为这正是指纹/密钥这类「硬件绑定凭据」最容易出问题的地方 —— 系统说「删了」，但硬件里还留着。**

**⭐ 而其它几条 Security 改动也有一条共同线索 —— 全都是「权限提升的边界」：**

| 改动 | 修的是什么 |
|---|---|
| **「Pin factory-reset elevation to the packaged command」** | ⭐ **恢复出厂的提权被固定到打包的那个命令** —— 而不是任意命令都能借这个提权 |
| **「Bind update inhibitor cleanup to the process that created it」** | ⭐ **更新抑制器的清理动作，绑定到创建它的那���进程** |
| **「Refuse hook and state names that are paths」** | ⚠️ **拒绝把路径当作 hook / 状态名** —— 防止通过路径穿越注入 |
| **「Defer to system-auth in the polkit stack written by fingerprint and FIDO2 setup」** | ⭐ **指纹/FIDO2 配置写入的 polkit 规则，交回给 system-auth 处理** |
| **「Isolate OCaml cleanup authorization」** | 隔离 OCaml 清理的授权 |
| **「Move screen-recording state out of world-writable /tmp」** | 录屏状态移出全局可写的 `/tmp` |
| **「Keep the Windows VM password out of the RDP client's arguments」** | ⭐ **Windows VM 的密码不出现在 RDP 客户端的命令行参数里**（命令行在 `ps` 里人人可见） |
| **「Harden passwordless sudo expiry across suspend」** | 免密 sudo 的过期时间跨休眠要算对 |

**⭐ 我认为「Windows VM 密码不进命令行参数」这一条，是最值得中国用户注意的安全实践 —— 因为 `ps aux` 在多用户机器上是可以被看到的。**

## 八、⭐ 我的评价

### 8.1 ⭐⭐ F1 安装器是这一代最重要的一次架构转变

**⭐ 我认为，如果只看功能列表，RC2 好像只是 RC1 的「bug 修复 + 几个新应用」。** **但读完源码之后我的判断完全不同。**

**因为「烤镜像 + 并行写盘」这件事，改变的是 Omarchy 作为「装机工具」的定位：**

| | 旧做法 | F1 |
|---|---|---|
| **本质** | 跑 940 个包管理器事务 | **复制一张文件系统镜像** |
| **速度瓶颈** | 包下载 + 解包 + 脚本执行 | **磁盘写入带宽** |
| **失败模式** | 中途失败，留半个系统 | ⭐ **失败则磁盘没被动过** |
| **差异化** | 每个包都现场决策 | **烤好基础镜像 + 小规模补差** |

**⭐ 而「失败则磁盘没被动过」这一条，我认为才是这个设计真正的价值 —— 它比「快」重要得多。**

**因为一个「快但会把你的磁盘搞成半成品」的安装器，比一个「慢但要么成功要么没动过」的安装器糟糕得多。**

### 8.2 ⭐ 而「坏介质拒绝」这个设计，是我认为最值得抄的

**⭐ 我还想单独强调一遍 `corrupt-image` 那个测试，因为它体现的是一种很少见的思路：**

**⭐ 「**在用户还在配置界面里的时候，就把整个镜像哈希校验跑完**」** —— 这把校验时间和用户的等待时间重叠了起来。**

**⭐ 而「校验不过就不许碰磁盘」这个硬保证，比任何事后提示都可靠。**

**—— 我认为这个「先验证、后动手」的结构，比任何具体的加速技巧都更值得其它发行版借鉴。**

### 8.3 ⭐ 至于那 10 条破坏性变更，我的态度是：值得，但要有准备

**⭐ 我不认为这些快捷键改动是「折腾用户」。** **因为它们背后是一次系统性的重排** —— 把 `Ctrl` 层让给系统级功能，把「偶尔用一次」的功能（Nightlight）移出快捷键，把通知系统升级成可键盘操作的模型。

**⭐ 但我要给一个实际的建议：**

**⭐ 如果你从 RC1 升到 RC2，**升级前先花两分钟把这张表打印出来贴在手边** —— 因为 `Super + Ctrl + N` 这种键现在有完全不同的含义（Network），而 `Super + Ctrl + Comma` 从「打开历史」变成了「交出键盘控制权」。**

**—— 而 `Super + Ctrl + N` 这一条尤其危险：它在旧版是 Nightlight（无害），在新版是 Network 面板。**

### 8.4 ⭐ 最后：Omarchy 正在从「DHH 的个人桌面」变成「有工程纪律的发行版」

**⭐ 这是我读完这些 PR 和源码之后的一个整体判断。**

**证据是这三条：**

**① 它给安装器写了集成测试，而且测试用例的名字就叫 `corrupt-image`** —— **专门去证明「坏介质会被拒绝」。** **这不是「加个功能顺手写点测试」，这是「把安全属性当成功能来测」。**

**② 它在发布说明里第一次主动列出「这些快捷键可能和你自己的绑定冲突」。** **—— 一个「坦诚自己会破坏什么」的项目，和一个「什么都不说」的项目，长期可信度完全不同。**

**③ 它的中国镜像 PR 带着 20 个 Globalping 探针的实测数据，而不是一句「我们加了个国内源」。**

**⭐ 而 `macom/omarchy` 这个仓库名（从 `basecamp/omarchy` 迁过来）、以及 `omarchy-iso` 独立成仓库的做法，也说明它已经过了「一个人的脚本集合」阶段。**

## Sources

- ⭐ 一手：[Omarchy v4.5.0-rc2 发布说明](https://github.com/omacom/omarchy/releases/tag/v4.5.0-rc2)（2026-10-27 23:07 UTC）
- ⭐ 一手：[omacom/omarchy-iso](https://github.com/omacom/omarchy-iso) —— `builder/build-root-image.sh`、`builder/omarchy-image-write.c`、`orchestrator/phases_impl.py`、`bin/omarchy-iso-installer`、仓库 README
- ⭐ 一手：[PR #16256](https://github.com/omacom/omarchy/pull/16256) 中国镜像（含 Globalping 实测数据）
- ⭐ 一手：[PR #15966](https://github.com/omacom/omarchy/pull/15966) Update > Kernel 菜单
- ⭐ 一手：[PR #16071](https://github.com/omacom/omarchy/pull/16071) / [#16072](https://github.com/omacom/omarchy/pull/16072) 快捷键迁移
- ⭐ 一手：[PR #14484](https://github.com/omacom/omarchy/pull/14484) Limine timeout（已关闭，但正文解释了模板里的 `#timeout: 3` 为何长期未生效）
- 一手：[PR #14426](https://github.com/omacom/omarchy/pull/14426) Disktree 取代 Disk Usage TUI / [#14962](https://github.com/omacom/omarchy/pull/14962) 移除 OBS/Kdenlive / [#14877](https://github.com/omacom/omarchy/pull/14877) 移除阿塞拜疆键盘布局
- 一手：`default/limine/limine.conf`（当前 `timeout: 1` + `quiet: yes`）
- 仓库元信息：`omacom/omarchy`，45,896 stars / 5,777 forks，MIT

---

（说明：所有引号内内容为官方发布说明、源码注释与 PR 原文引用；**第三、四节的源码分析为笔者依据实测拉取的 omarchy-iso 三份源码所写**；**第八节的评价为笔者观点**。**「安装时间减半」这一说法来自官方发布说明，笔者在源码中未找到对应实测基准，故仅作转述、不作独立背书。**）
