---
title: "CachyOS 十一月版：给 EAC 游戏一套独立签名内核"
date: 2026-11-25
slug: cachyos-november-2026-eac-recovery
category: 技术/解读
author: FreeLAMP.com
original_source: "Phoronix《CachyOS November 2026 Released With EAC Linux v2 Support, New Recovery Tool》（Michael Larabel，2026-11-22）＋ CachyOS 官方博客《CachyOS November 2026 Release》（2026-11-22，含完整特性/修复清单与 ISO 下载）＋ Phoronix《CachyOS Package Installer 2.0》（2026-11-22）＋ 本号 2026-11-07 CachyOS/Omarchy 跑分文章交叉核对。"
description: "解读 CachyOS 2026 十一月 ISO（年内第六版）：为 Easy Anti-Cheat Linux v2 提供独立的 linux-cachyos-eac 内核与同一密钥签名的 systemd-boot、eac-setup/eac-status 脚本（支持 systemd-boot/Limine/rEFInd，GRUB 实验性）；新增 cachyos-recovery 自包含恢复环境（UEFI 直接启动、Btrfs 快照可写试启再回滚、约 70MB ESP、支持 LUKS、独立于 Snapper）；cachyos-drm-awaiter 取代 early KMS 与 nvidia-module-loader；安装器迁移到 gucc 共享库；Package Installer 2.0 加 AUR/Flatpak/AppImage（opt-in）与 PKGBUILD 静态分析；内核 Linux 7.3.5、NVIDIA 620.73.04、Mesa 26.3.1、Rust Binder 与 ThinLTO、提供 WSL 镜像。并给现有用户的升级注意事项（pacman -Syu 后 chwd -a -f 重装驱动配置）。"
published: true
---

CachyOS 的十一月 ISO 出来了，这是它今年**第六次**发布。Phoronix 的标题只点了三件事：EAC Linux v2 支持、新的恢复工具、内核升到 7.3.5。但官方公告里的完整清单要厚得多——而且其中好几项是真正意义上的工程决策，不只是版本号更新。

## 一、Easy Anti-Cheat：为游戏单独准备一条启动链

最值得写的，是它怎么处理 Epic 的 Easy Anti-Cheat Linux v2。

EAC 在 Linux 上要求的不只是「装个驱动」：游戏启动时必须能验证系统**怎么启动的**——Secure Boot 开启、内核由 Epic 信任的密钥签名、TPM 2.0、IOMMU 打开，而且内核要处于 lockdown 模式，只加载签名模块。这套要求意味着你不能简单把自己的日常内核签一下就完事——lockdown + 只加载签名模块，会直接挡住 DKMS 那套东西。

CachyOS 的解法是**给 EAC 单独做一个内核 `linux-cachyos-eac`**，用 CachyOS 的密钥签名，配一把同样密钥签名的 systemd-boot。关键点在于：**它有自己的启动项，你平时的启动项原样保留**——只有想玩 EAC 游戏时才 reboot 进那个内核。配套的：

- `eac-setup` / `eac-status` 脚本放进 `cachyos-settings`，负责建立和验证 Secure Boot 链；支持 systemd-boot、Limine、rEFInd，GRUB 是实验性支持；
- `cachyos-eac-signing-key`、`systemd-boot-cachyos-signed`、`cachyos-eac-grub-hook` 三个包；
- DKMS 模块在 EAC 内核上不能用，所以 NVIDIA（open 和 580xx）、ZFS、r8125 改成预构建的 `linux-cachyos-eac-*` 包提供；
- `sbctl-batch-sign` 会跳过已经被 CachyOS 签过的文件；官方文档还写了怎么从已有的 Secure Boot 配置迁移过来。

这个设计很聪明的地方在于**把兼容性和日常使用的取舍隔离开**：你不必为了一个游戏把整个系统的安全策略降级，也不必放弃自定义内核模块——只是玩 EAC 游戏时重启到一条干净、可验证的链上。顺带一提，`eac-status` 这次还修了一个细节：`intel_iommu=on` 只在 Intel CPU 上才要求，失败信息也更清楚了。

## 二、cachyos-recovery：不用 Live USB 的回滚环境

第二个大件是 `cachyos-recovery`，一个**自包含的恢复环境**，可以从 bootloader 启动，也可以在 UEFI 里直接启动——**回滚一个坏掉的系统不再需要找 Live USB**。

工作流做得很完整：从菜单里选任意 Btrfs 快照，先以**可写 root**（通过 overlayfs）启动试一下，确认没问题再永久回滚——入口可以是桌面的通知，也可以直接在恢复菜单里操作。回滚时会自动为还原的快照重新生成内核、initramfs 和 bootloader 配置；如果你用 sbctl 配了 Secure Boot，还会自动签名。

其它细节：

- **独立于 Snapper**；支持 LUKS 加密安装；
- UEFI 系统上以 UKI 形式提供，占 ESP 大约 **70 MB**；BIOS 系统用 `cachyos-recovery-legacy`；
- 通过 pacman hook 安装（`sudo pacman -S cachyos-recovery`），会自动加 UEFI 启动项、Limine 项（UEFI/BIOS 都有）、BIOS 上的 GRUB 项；
- 恢复镜像在配置了 sbctl 时也会签名。

对一个滚动发行版来说，这个东西的价值很实际：系统更新坏了，开机就能回滚，不用翻箱倒柜找 U 盘。

## 三、显示栈与安装器的底层重构

第三组变化不那么吸睛，但影响更基础。

**`cachyos-drm-awaiter` 取代 early KMS 和 `nvidia-module-loader`**。新包会等 GPU 驱动加载完再启动 display manager——而且**对任何驱动都有效，不只是 NVIDIA**；如果驱动加载失败，会显示一个二维码（便于扫码查排障信息）。`chwd` 和安装器都跟着改了，initramfs 里不再默认加 `kms` hook，Plymouth 改用 simpledrm 显示启动画面。

**安装器在往共享后端迁移**：Calamares 现在用 CLI installer 那套共享库（gucc）来处理 initramfs、machine-id 和安装后步骤；CLI installer 本身也做了一次大重构，换成带类型的 installer state，LUKS/LVM 的 bootloader 处理重写（尽量用 `rd.luks.uuid=`），硬件时钟默认 UTC，initramfs 只生成一次。根分区默认用 `SD_GPT_ROOT_X86_64` 分区类型，Plymouth 变成可选的，rEFInd + AI SDK 这个启动器选项被删了（AI SDK 以后可以 `chwd -a --ai_sdk` 单独装）。

**`cachyos-settings`** 把 systemd-oomd 配置带回来并默认启用——按 swap 使用情况杀进程、忽略用户 session；sysctl 现在用 dirty ratios，在慢盘和 USB 设备上限制 writeback；默认允许 REISUB；`game-performance` 加了 tlpctl 支持；`cachyos-bugreport` 会对 SSID、IPv6、MAC、UUID 和 `file://` 路径做脱敏——最后这条对公开提 bug 的人很实用。

## 四、Package Installer 2.0：从 pacman 前端到「应用商店」

CachyOS Package Installer 升级到 2.0.0，UI 完全重做，功能也扩了一圈：

- **AUR 支持（opt-in）**：构建前先在应用里展示 PKGBUILD 和安装脚本，并用静态分析标出可疑行；更新时会显示与已装版本的 diff；已装 AUR 包也能更新。
- **Flatpak 支持（opt-in）**。
- **AppImage 支持（opt-in）**：本地文件会生成菜单项和图标；也能从 GitHub 项目 URL 安装并追踪更新；用 Shelly 或 Gear Lever 加过的 AppImage 可以直接接管。
- 新设置页提供多个配色主题，还有一个调用 `cachyos-rate-mirrors` 的镜像测速按钮。

对不想碰命令行的新用户，这基本就是「应用商店」体验了。而静态分析那一步，算是把 Arch 社区多年来「装 AUR 包前先看 PKGBUILD」的规矩做进了 GUI。

## 五、版本与配套：内核 7.3.5，还给了 WSL 镜像

基础包版本：

- **Linux 7.3.5**（LTS 6.18.64）；内核现在可以用 **Rust + ThinLTO** 一起构建，并启用了 **Rust Binder**；server 内核默认 THP 改成 `madvise`；
- **NVIDIA 620.73.04**；`nvidia-580xx` 模块为自家内核预构建；
- **Mesa 26.3.1**；mutter 带上 tearing 补丁；
- Limine 12.10.0；LLVM/Clang 改成统一 PKGBUILD，加了 `llvm-bolt` 和 `clang-libs`；
- 新增 bpftune-gaming、pahole，移除了 Void editor。

另外，CachyOS 现在提供 **WSL 镜像**（Windows 11 的 Windows Subsystem for Linux），安装见官方 wiki；Docker 也加了 `cachyos/distrobox` 镜像。镜像站新增韩国、印度、瑞士（init7）和两个美国东部节点。

## 六、给现有用户：有一条手动操作别漏

如果你是已有用户而不是重装，官方明确写了：**因为 `cachyos-drm-awaiter` 取代了 early KMS 和 `nvidia-module-loader`，更新系统后要用 chwd 重装一遍驱动配置**：

```bash
sudo pacman -Syu
sudo chwd -a -f
```

（官方公告里这两条写在一行，实际执行请分开跑。）不做这一步，显示管理器的启动顺序可能还停留在旧的 early KMS 逻辑上。

顺带一提，本号 11 月 7 日写过的那篇 CachyOS/Omarchy/Arch 跑分，用的是当时的 7.3 内核与 Mesa 26.2；这次 11 月 ISO 带的是 7.3.5 与 Mesa 26.3.1，加上这次重构的 GPU 驱动等待逻辑，那篇的结论只能当作那个时间切片的参考，不能直接外推到这版。

## 结语

把这份发布说明从头读到尾，能看出 CachyOS 的迭代重心：一边在游戏兼容（`linux-cachyos-eac`）和灾难恢复（`cachyos-recovery`）上补关键能力，一边把安装器、驱动初始化这些「看不见的管道」往共享库和统一后端上收。对一个滚动发行版来说，后者往往比新功能更能决定长期体验——它决定了下次更新会不会又把你卡在启动阶段。

## 参考资料

- Phoronix 原文：https://www.phoronix.com/news/CachyOS-November-2026
- CachyOS 官方十一月发布公告（完整清单与下载）：https://cachyos.org/blog/2611-november-release/
- Phoronix：CachyOS Package Installer 2.0：https://www.phoronix.com/news/CachyOS-Package-Installer-2.0
- CachyOS WSL wiki：https://wiki.cachyos.org/virtualization/wsl/
- ISO 下载（CDN）：https://iso.cachyos.org/desktop/261122/cachyos-desktop-linux-261122.iso
