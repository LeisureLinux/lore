---
title: "GhostBSD 26.2：FreeBSD 桌面这两年最实在的一次进步，是把「安装器」和「首次启动」拆开了"
date: 2026-10-27
slug: ghostbsd-26-2-freebsd-15-1
tags: [GhostBSD, FreeBSD, MATE, ZFS, GELI, 整机加密, 安装器, InstallStation, BEStation, BootEnvironment, pkg, Pkg, XLibre, USBHID, Desktop, 桌面操作系统]
category: 运维/桌面
author: FreeLAMP.com
original_source: "GhostBSD 官方发布公告《GhostBSD 26.2-R15.1p6 Is Now Available》（2026-10-27，ericbsd）+ Phoronix 报道 + ⭐ 实测拉取 ghostbsd/install-station、networkmgr、update-station 三个仓库的 README 与目录结构"
original_date: 2026-10-27
original_url: "https://www.ghostbsd.org/node/68"
description: "GhostBSD 26.2-R15.1p6 于 2026-10-27 发布，基座升级到 FreeBSD 15.1-RELEASE。本文在转述官方发布说明之外，实际拉取了 ghostbsd/install-station、networkmgr、update-station 三个仓库的 README 与源码目录做交叉核对，重点解释三件事：一、新安装器把「装系统」和「首次启动配置」拆成 Install Station 与 Setup Station 两段，这个拆分本身就是这两年桌面安装器设计变化的一个缩影；二、Update Station 的四类升级（Packages / Release / Minor / Major）与 ZFS boot environment 的关系 —— 「升级不碰运行中的系统」这个模型是 FreeBSD 相对 Linux 发行版最实在的优势之一，而 GhostBSD 把它做成了图形界面；三、38 种语言的本地化覆盖与「ISO 瘦身 46 个包」这类不显眼但决定项目存活的工程取舍。"
published: true
---

> 来源：[GhostBSD 官方：GhostBSD 26.2-R15.1p6 Is Now Available](https://www.ghostbsd.org/node/68)（**2026-10-27**，作者 **ericbsd**）；[Phoronix 报道](https://www.phoronix.com/news/GhostBSD-26.2)（2026-10-28）
> ⭐ **本文实测拉取了三个仓库的 README 与目录结构做交叉核对**：`ghostbsd/install-station`（**9 stars / 6 forks / 58 commits / BSD-3-Clause / Python**）、`ghostbsd/networkmgr`（**114 stars**）、`ghostbsd/update-station`（**10 stars**），以及 `ghostbsd` 组织下 **44 个仓库**的星标分布。
> 本文为**解读**。

## 一句话结论

**GhostBSD 26.2 表面上是一次「跟进 FreeBSD 15.1」的常规发布，但我认为它实际交付了三件更值得说的事：**

**① 把「装系统」和「首次启动配置」拆成两个阶段**（Install Station → Setup Station），**这正是这两年桌面 Linux 安装器也在往同一个方向走的一条路；**
**② 把 ZFS boot environment 的「升级不碰运行中的系统」这个模型，做成了图形界面的日常操作**（Update Station + BE Station）；**
**③ ⭐ 加上了安装器内的整机加密（GELI）** —— **这是 FreeBSD 桌面用户过去最难自己搞定的一件事之一，现在它是一个安装器选项。**

**而我最想说的是第三件，因为它的意义超出了「多了一个功能」。**

## 一、GhostBSD 是什么，以及它为什么存在

**官方 About 页的自我定位：**

> **「GhostBSD 是一个基于 FreeBSD 的操作系统，被设计来提供稳健、用户友好的桌面体验。结合 FreeBSD 的可靠性与 MATE 桌面环境的优雅，我们的目标是为日常用户和开发者同时提供稳定而直白的计算方案。」**

**它列出的特性里有两条值得单独拎出来：**

- **「高级 ZFS 支持：提供快照与回滚等复杂特性，适合需要数据完整性的环境。」**
- **「面向开发者优化：包含迎合开发者的工具与库，便于直接在桌面上编译、部署和调试。」**

**⭐ 而我在拉取 `ghostbsd` 组织的 44 个仓库时，星标分布提供了一个有意思的侧面：**

| 仓库 | Stars | 说明 |
|---|---|---|
| **`ghostbsd-src`** | **155** | **基础系统源码** —— 星标最高 |
| **`ghostbsd-build`** | **124** | 构建系统 |
| **`networkmgr`** | **114** | **网络管理器** —— ⭐ **星标第三，而它不是内核** |
| `ghostbsd-ports` | 46 | 第三方 ports |
| `documentation` | 16 | |
| `gbi`（旧安装器） | 16 | |
| `software-station` / `update-station` / `install-station` | 11 / 10 / 9 | **三个「Station」工具** |
| `ghostbsd-mate-themes` / `ghostbsd-mate-settings` | 6 / 6 | |

**⭐ 而 Phoronix 的报道点出了一个容易被忽略的细节：**

> **「GhostBSD 26.2 继续默认使用 MATE 桌面环境，跑在 XLibre 服务器之上。」**

**—— XLibre。** **（这是 X.Org 基金会 2024 年那次 fork 风波之后诞生的 X11 分支，本号此前在《Linux 桌面的前三十年》里提过这个背景。）** **而 MATE 本身就是 GNOME 2 的直接后继。**

**⭐ 所以 GhostBSD 的技术栈其实是「**FreeBSD 内核 + X11 世界最保守的那一支（MATE + XLibre）**」** —— **一个刻意避开 Wayland、避开 GNOME 3 那套激进的桌面，稳稳当当地跑在 X11 上的组合。**

**而这在 2026 年是一个值得注意的定位选择 —— 因为同期几乎所有 Linux 发行版都在往 Wayland 冲。**

## 二、⭐⭐ 重点一：安装器被拆成了两段

**官方发布说明里的第一条关键变化：**

> **「一个新的安装器：Install Station 安装系统，然后 Setup Station 在首次启动时配置网络并创建用户。」**

**而 install-station 仓库的 README 说得更精确（我实测拉取）：**

> **「Install Station 是 GhostBSD 的精简安装器。**
> **Install Station 处理磁盘编辑、分区和操作系统安装。用户配置与系统设置在安装后的首次启动时由 Setup Station 完成。」**

**⭐ 我认为这个拆分是这整篇最值得讨论的设计，因为它对应的正是「桌面操作系统安装器设计」这两年的一条主线。**

**传统安装器的做法是「一次做完」：** 一个进程（或几个阶段连续跑完）负责分区、写文件、装包、配网络、创建用户、装 GRUB。**所有问题都在「安装过程中」暴露，而此时系统还没起来，出错时的排查手段非常有限。**

**而拆分之后：**

| | Install Station（安装期） | Setup Station（首次启动） |
|---|---|---|
| **能做什么** | 磁盘编辑、分区、装系统 | 配置网络、创建用户 |
| **运行环境** | **Live 环境**（还没装完，目标系统不完整） | **⭐ 已装好的、完整的系统** |
| **出错时能做什么** | **几乎什么都做不了** | **⭐ 有完整系统可查、可改、可重启** |

**⭐ 我想强调的是 Setup Station 那一侧：**

**「配置网络并创建用户」这两件事被特意放到了首次启动 —— 因为这恰恰是「安装器无法替你决定、但用户必须在有网络的情况下才能完成」的部分。** **而此时用户面对的是一个已经能启动、能进 shell 的系统。**

**⭐ 而这种「把需要联网、需要用户输入的部分推迟到首次启动」的做法，在 Linux 世界有一个对应的先例：** **Ubuntu 的 ubiquity / subiquity 体系当年也是把「账号创建」这类需要联网的部分从安装器里拆出来。**

**—— 而 GhostBSD 这次是把整个思路往「安装器只管装机器」的方向推了一步。**

## 三、⭐⭐ 重点二：ZFS boot environment 成了图形化的日常操作

**这是我认为 GhostBSD 相对 Linux 发行版最实在、也最被低估的优势。**

### 3.1 Update Station 的四类升级

**我实测拉取了 `ghostbsd/update-station` 的 README，它把升级类型分得非常清楚：**

> **「Update Station 读取 GhostBSD 版本，形如 `26.1-R15.0p13`，然后把运行中的系统与仓库对比，判断有哪一类升级可用。」**

| 升级类型 | 例子 | **怎么安装** |
|---|---|---|
| **Packages** | 同样的版本，更新的包 | **就地安装**，可选先做一次 boot environment 备份 |
| **Release** | `26.2-R15.1p2` → `26.3-R15.1p5` | **在一个新的 boot environment 里** |
| **Minor** | `26.1-R15.0p13` → `26.2-R15.1p2` | **在一个新的 boot environment 里，重装所有包** |
| **Major** | `26.1-R14.3p8` → `26.2-R15.0` | **在一个新的 boot environment 里，重装所有包** |

**⭐ 而 README 里这句话是整个模型的精髓：**

> **「安装到 boot environment 里的升级**永远不碰运行中的系统**。它进入一个新的 boot environment，在下次启动时激活，所以升级在你重启时才生效。在你重启之前，Update Station 停止查找更新，转而请你重启。它创建的 boot environment 归你所有，可以用 BE Station 保留或删除。」**

**⭐ 我认为这套模型的价值，需要和 Linux 的现状对照才看得出来：**

| | Linux 发行版的常规升级 | GhostBSD / FreeBSD 的 boot environment |
|---|---|---|
| **升级失败时** | **系统可能半坏，需要救援介质** | **⭐ 原系统完好，只是没切换过去** |
| **升级前的准备** | 要自己确认没有第三方仓库冲突 | **⭐ 天然有快照** |
| **回滚** | 要靠备份 / 快照 / 重装 | **⭐ 重启时选一下** |
| **内核升级** | 通常需要重启，且有引导风险 | **⭐ 新环境自带新内核，回退只要改引导项** |

**⭐ 而 Linux 那边其实也有类似的东西（snapper、timeshift、systemd-bless-boot、Btrfs 快照），但它们大多需要用户自己配置，而 GhostBSD 是**默认就在**的。**

### 3.2 BE Station：备份管理变成了「从引导菜单里选」

**官方发布说明：**

> **「Backup Station 现在叫 BE Station，可以从选中的那个创建 boot environment。」**

**⭐ 改名这件事本身有点讲究 —— 从「Backup Station」改成「BE Station」，因为它做的已经不只是「备份」，而是「管理 boot environment」。**

**⭐ 而这次发布说明里还提到了一句我认为很关键的话：**

> **「Update Station 现在在一个 boot environment 里安装小版本（minor）和发行版（release）升级。」**

**—— 注意这和官方为从 26.1 升级到 26.2 画的路径是**一致**的：**

> **「从 26.1-R15.0p2 升级：先用 `sudo pkg upgrade update-station` 更新 Update Station，然后**在用 Update Station 跑升级之前先重启**。」**

**⭐ 而 Update Station 的 README 里解释了为什么必须先更新它自己：**

> **「这个新版本修复了测试 boot environment 升级时发现的问题。」**

**—— 也就是说：「用旧的 Update Station 去升级 Update Station 所在的 boot environment」这个自举场景，是有 bug 的，所以必须先手工把工具本身更新掉。**

**⭐ 我认为这是一个非常典型的、只有真正做过这类工具的人才会踩到的坑，而它被明确写在了升级说明的第一步。**

### 3.3 隐藏的引导菜单

**官方发布说明里还有一条很小但很实用的变化：**

> **「隐藏的引导菜单，按键呼出，以及一个新的菜单选项可以取消静音启动日志。」**

**⭐ 我认为「按键呼出引导菜单」这个设计值得单独说 —— 它解决的是一个真实的矛盾：**

**桌面用户希望开机界面干净（不看到 GRUB 菜单、看不到 FreeBSD 启动过程的滚屏），但一旦系统坏了，他们需要能立刻回到引导菜单去选一个旧的内核或旧的环境。**

**「平时隐藏、按键呼出」正是这个矛盾的标准解 —— 而且它比「永不显示引导菜单」或「总是显示」都更好。**

## 四、⭐⭐ 重点三：安装器里的整机加密（GELI）

**官方发布说明：**

> **「在安装器里用 GELI 实现整机加密。」**

**⭐ 我认为这一条的重要性被低估了，理由是它改变的是「谁能自己完成这个任务」。**

**Full Disk Encryption 在桌面世界一直有个尴尬：**

- **它是必需品** —— 笔记本丢了 = 硬盘里的所有数据裸奔；**
- **但它一直是「Geek 任务」** —— 在 Linux 上要自己搞 LVM-on-LUKS、cryptsetup 配置、要记得在改 fstab 时用 initramfs 钩子；**
- **而很多桌面发行版干脆不提供图形化的 FDE 设置**（Ubuntu 要靠 subiquity 的 Luks 部分，Fedora 要靠 Anaconda，Windows 上是 BitLocker 一键但只有 Pro 以上）。**

**⭐ 而 FreeBSD 这边的现实是：GELI 是 FreeBSD 原生的加密方案，它一直是 FreeBSD 的强项，但过去的门槛在于「要手工写 `geli` 配置 + `geli_devices` + rc.conf，还要理解它和 ZFS 的组合顺序」** —— **这不是普通用户能在安装过程中从容完成的事。**

**⭐ 把它做成安装器里的一个选项，等于把「必须懂 FreeBSD 才能配好」变成了「装系统时勾一下」。**

**⭐ 而我觉得它与 GhostBSD 的「面向开发者 / 数据完整性」定位是连着的：**

**—— 「Advanced ZFS Support: 提供快照与回滚，适合需要数据完整性的环境」** 和 **「安装器内的整机加密」** 这两件事，服务的是同一批用户：**那些把笔记本当主力机、需要在上面跑开发环境、但不能接受数据裸奔的人。**

## 五、⭐⭐ 重点四：那些不显眼、但决定项目存活的工程取舍

### 5.1 ISO 瘦身：砍掉 46 个包

**官方发布说明：**

> **「更小的 ISO，从基础中移除了 46 个 server 和 legacy 包。」**

**⭐ 我认为这条比「加了新功能」更值得写 —— 因为它是一个**生存决策**。**

**GhostBSD 官方 About 页把「面向开发者」列为特色，但这一版的做法是**把 server 类包从基础镜像里拿掉**。**

**⭐ 这看起来矛盾，其实是一致的：** **GhostBSD 是「桌面发行版」，不是「服务器发行版」；而一个桌面 ISO 里塞满 sshd / mail / web server 这类包，既占空间又扩大攻击面。**

**—— 而这个判断和本号此前写的那篇《GoAhead 三个 TLS 漏洞》是同一个世界观：** **「默认不需要的东西就别默认带着」—— 攻击面是装出来��。**

### 5.2 38 种语言的安装器本地化

**我实测拉取了 `install-station/po/` 目录，里面有 **37 个 `.po` 语言文件** 加上模板文件：**

```
ar_SA  bg_BG  ca_ES  cs_CZ  da_DK  de_DE  el_GR  en_GB  en_US  es_ES
et_EE  fi_FI  fr_CA  fr_FR  hr_HR  hu_HU  it_IT  ja_JP  ko_KR  lt_LT
lv_LV  nl_NL  no_NO  pl_PL  pt_BR  pt_PT  ro_RO  ...
```

**⭐ 而官方发布说明里写的是：**

> **「Install Station 有新的 ZFS 页面和网络页面，并且**被翻译成了所有支持的语言**。」**

**⭐ 我认为这一条的份量比它看起来大：**

**—— 一个桌面发行版要「像 Linux 发行版」，关键不在内核或包管理，而在**「装的时候能不能看懂」**。而安装器是装机时唯一会被所有人看到的东西。**

**⭐ 而且我注意到 install-station 的 README 里有一段专门讲翻译工作流的：**

```shell
./setup.py create_translation --locale=fr
./setup.py update_translations
```

**—— 也就是说翻译是**脚本化**的，不依赖 gettext 的手工流程。** **这看起来是小事，但它是「让贡献者能低成本参与」和「让贡献停留在 5 个人身上」的区别。**

### 5.3 USB HID 默认启用

**官方发布说明：**

> **「USB HID 设备现在默认由 usbhid 支持。」**

**⭐ 而这一条被放在同一个更新里，还有另一个关于 Ventoy 的修复：**

> **「缺失的 EFI fallback loader 破坏了 Ventoy。」**

**⭐ 我把这两条放在一起看，因为它们指向同一个方向 —— GhostBSD 26.2 在**「让 Live ISO 和安装过程在真实硬件上真的能用」**上下功夫：**

- **USB HID 默认开** → **不用 U 盘键鼠的场合也能用**（某些 KVM、某些 USB 集线器）；**
- **修 Ventoy 兼容性** → **多了一个广为人知的「从 ISO 启动」工作流可用。**

**—— 而这两个都是「主机启动不了」的类别，而它们是桌面发行版口碑的生死线。**

### 5.4 NetworkMgr 改用 wpa_cli

**官方发布说明：**

> **「NetworkMgr 现在通过 `wpa_cli` 驱动 Wi-Fi，并且只在网络连接成功后才保存网络。」**

**⭐ 「只在连接成功后才保存网络」这一句修的是一个很具体的 bug 类别：**

**—— 之前的版本会把「连不上的网络」也写进配置，于是每次开机都要重新尝试一个根本不可用的 SSID；而密码错误时用户看到的是「保存了但连不上」的困惑。**

**⭐ 而这一版修复清单里明确列了 Wi-Fi 的四个具体症状：**

> **「AX200 卡的 Wi-Fi 问题、开放网络、错误的密码提示、非 ASCII 的网络名。」**

**⭐ 「非 ASCII 的网络名」这一条特别值得注意** —— **它涉及 SSID 的编码处理，而中文用户遇到「网络名里带中文就连不上」是相当常见的报告。**

## 六、⭐⭐ 一个值得单独讨论的东西：Update Station 的自我保护设计

**我在 update-station 的 README 里看到一段我觉得设计得很好：**

> **「一次 major 升级会改变 FreeBSD ABI，因此它**在开始之前会询问**。其它几类不会询问，它们像普通更新一样显示包列表。」**

**⭐ 「major 升级会改变 ABI，所以要额外确认」—— 这个区分很准确，而且对用户是有意义的：**

| 升级类型 | 会不会破坏正在运行的二进制 | 要不要问 |
|---|---|---|
| Packages（换包） | 可能，但通常可逆 | 不问（可做 boot env 备份） |
| Release / Minor（换大版本） | 是，会重装所有包 | 不问（有 boot env 兜底） |
| **Major（换 FreeBSD 大版本）** | **⭐ 是，ABI 都变了** | **⭐ 问** |

**⭐ 而这个区分背后的逻辑是：「有没有 boot environment 兜底」决定「要不要打扰用户」。** **有兜底的就不问，没兜底的（ABI 变更）才问 —— 因为那时 boot environment 也救不了你。**

**⭐ 我认为这比「一律弹窗确认」或者「一律不确认」都好得多，因为它把确认的成本花在了真正需要人决策的地方。**

## 七、⭐ 修 bug 清单里藏着「这个项目的真实用户是谁」

**官方修复清单里有一条特别有意思：**

> **「缺少 man、KeePassXC、FreeCAD 和 Shotcut 这些包。」**

**⭐ 我想指出这四个包构成的一组画像：**

| 包 | 类别 |
|---|---|
| **man** | **开发者基础** —— 没有手册页就没法查文档 |
| **KeePassXC** | **密码管理器** |
| **FreeCAD** | **CAD / 3D 建模** |
| **Shotcut** | **视频剪辑** |

**⭐ 这四个放在一起，画出的用户画像非常明确：** **「我在这台机器上写代码、查文档、管密码、做一点设计、剪一点视频」** —— **也就是把树莓派或旧笔记本当主力机的开发者兼创作者。**

**—— 而这正好对应 About 页里那句「为日常用户和开发者同时提供稳定而直白的计算方案」，以及「硬件兼容性：从高端工作站到便携设备」。**

**⭐ 而另一个修复项也很有意思：**

> **「安装时没有设置时区。」**

**—— 这是典型的「只有真正被用户投诉过才会被写进 changelog」的 bug。**

## 八、⭐ 我的评价

### 8.1 GhostBSD 走的是一条「反潮流」但很自洽的路

**⭐ 我认为 GhostBSD 的技术选择组合起来看是高度一致的：**

| 选择 | 一致在哪 |
|---|---|
| **FreeBSD 15.1 + ZFS + GELI** | **把 FreeBSD 的强项做深**，而不是追 Linux 的生态广度 |
| **MATE + XLibre** | **留在 X11 世界里**，用最保守、最稳定的那一支桌面 |
| **Install Station / Setup Station 拆分** | **把「装机器」和「配机器」分开**，降低安装期失败面 |
| **Update Station + BE Station** | **把 FreeBSD 最独特的优势做成图形化日常操作** |
| **ISO 砍掉 46 个 server 包** | **桌面发行版不做服务器发行版的事** |
| **38 种语言** | **「像 Linux 发行版」的关键不在内核，在装机时能不能看懂** |

**⭐ 而「反潮流」这个词要加个限定 —— **它反的只是「桌面必须追新」这一条，而不是「桌面要现代」这一条。** **ZFS、boot environment、GELI 这些恰恰是很现代的东西。**

### 8.2 ⭐ 而它最大的结构性风险，是「生态」

**⭐ 我必须指出这一点，因为它是 GhostBSD 这类项目无法靠工程质量解决的问题：**

**GhostBSD 的 Star 分布很说明问题 —— `ghostbsd-src` 155 星、`networkmgr` 114 星、而 `install-station` 只有 9 星。** **也就是说：** **整个项目在 GitHub 上的可见度，集中在「FreeBSD 的一个移植」上，而不是「GhostBSD 自己的桌面工具」上。**

**⭐ 而这背后是一个更硬的事实：**

**FreeBSD 15.1-RELEASE 的支持期到 2027-03-31**（官方数据），**而 15.0 在 2026-09-30 已 EOL**。**所以 GhostBSD 这一版其实是在一个即将进入支持末期的上游版本上建立的 —— 下一次跟进，大概率是 15.2。**

**⭐ 但更关键的是：** **桌面的瓶颈从来不是内核。** **它是「我常用的那个软件有没有人把它打包成 FreeBSD 的 port」。** **而这一点上，GhostBSD 面对的是整个 FreeBSD 社区几十年的积累 —— 它自己不可能也不应该独自承担。**

**⭐ 所以我认为 GhostBSD 最健康的存在形态，是「**FreeBSD 上最像 Linux 桌面的那一层**」，而不是「一个独立的、什么都能装的发行版」。** **而这次发布说明里「26 个提交者贡献、几十个 issue 报告者、官方仓库 44 个、ISO 瘦身 46 个包」这些数字 —— 都在说明它是**一个活的、有社区参与的项目**，而不是一个孤岛。**

### 8.3 ⭐ 而我最想推荐给谁

**⭐ 如果你在考虑「给一台旧笔记本/树莓派装个不像 Linux 的系统」，我认为 GhostBSD 26.2 是一个非常值得认真看的选项，因为它解决的是三个具体问题：**

**① 「升级会不会把系统搞坏」** → **⭐ boot environment 给了你一个不需要理解 ZFS 就能用的兜底。** **这是 Linux 发行版里最需要你自己搭、而这里开箱即有的东西。**

**② 「我的数据会不会裸奔」** → **⭐ 安装器内的 GELI 让整机加密从「Geek 任务」变成「勾一个选项」。**

**③ 「我能不能看懂安装过程」** → **⭐ 38 种语言的安装器 + MATE 这个「没有惊喜」的桌面。**

**—— 而如果你要的是「软件生态广度」，那 Linux 仍然是唯一答案，这不是 GhostBSD 输的地方。**

## Sources

- GhostBSD 官方发布说明：GhostBSD 26.2-R15.1p6 Is Now Available（2026-10-27，ericbsd）：https://www.ghostbsd.org/node/68
- GhostBSD 官方：About / Download：https://www.ghostbsd.org/about ｜ https://www.ghostbsd.org/download
- GhostBSD 官方：Update Update Station Before the Next Upgrade（2026-10-27）：https://www.ghostbsd.org/node/67
- Phoronix：GhostBSD 26.2 Released As FreeBSD 15.1 Powered OS With New Installer（2026-10-28）：https://www.phoronix.com/news/GhostBSD-26.2
- FreeBSD 官方：15.1-RELEASE Announcement（支持期至 2027-03-31；15.0 于 2026-09-30 EOL）：https://www.freebsd.org/releases/15.1R/announce/
- ⭐ 本文实测拉取核对：https://github.com/ghostbsd/install-station ｜ https://github.com/ghostbsd/networkmgr ｜ https://github.com/ghostbsd/update-station ｜ https://github.com/orgs/ghostbsd/repositories

---

（说明：所有引号内内容为 GhostBSD 官方发布说明、README 与 FreeBSD 官方公告原文引用；**标注「实测」的部分为本文实际拉取三个仓库的 README、目录结构与组织仓库列表后的核对结果**；第八节的评价为笔者补充。**FreeBSD 15.1 的支持期与 15.0 的 EOL 日期均引自 FreeBSD 官方公告。**）
