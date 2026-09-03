# Armbian 26.8 发布：内核全面升到 Linux 7.1、安装器重写、标准化 UEFI ISO、新增 6+ 款 SBC 支持

> **原始出处**：Armbian 26.8 官方公告 + 文档 + Phoronix
> **发布日期**：2026 年 8 月 30 日
> **作者**：Armbian 社区（官方公告未列个人作者）
> **官方公告**：https://blog.armbian.com/armbian-release-26-8/
> **官方文档**：https://docs.armbian.com/releases/26.8/
> **Phoronix 报道**：https://www.phoronix.com/news/Armbian-26.8-Released
> **翻译/解读**：LeisureLinux
> **关键词**：Armbian 26.8、Linux 7.1 SBC、UEFI ISO、armbian-install 重写、Armbian Imager 2.0

## 引言：SBC 玩家等了一年的大版本

Armbian 是 Debian/Ubuntu 衍生的 ARM / RISC-V 单板计算机（SBC）发行版。8 月 30 日发布的 26.8 是 2026 年的第二个大版本，对 SBC 玩家来说是个"等了一年"的更新：

- **内核基线**全面升到 **Linux 7.1 stable**，部分 edge 分支追到 **7.2-rc**。
- **armbian-install 完全重写**，作为单元测试覆盖的 `armbian-config` 模块交付。
- **Armbian Imager 2.0**：新增 QDL 和 UFS 烧录工具。
- **标准化 UEFI ISO**：桌面版 / minimal 版都能直接用 ISO 镜像部署。
- **新增 6+ 款 SBC**：Anbernic RG DS / RG Vita Pro、Luckfox Nova、LubanCat 5IO、KICKPI K3B、Seeed reComputer RK3576/RK3588 等。
- **CI 流水线**：从主仓库迁出，迁到基于 Debian Trixie 的独立 CI 基础设施。

这些改动里，"安装器重写 + UEFI ISO + Linux 7.1"三件套最值得展开——它们一起把 Armbian 从"开发者专用发行版"进一步推向"通用 SBC 操作系统"。

---

## 一、整体改动一览

| 维度 | Armbian 26.8 |
|------|-------------|
| **内核基线** | Linux 7.1 stable（全平台） |
| **edge 分支内核** | Linux 7.2-rc（rockchip64 / meson64 / mvebu64 / sunxi / bcm2711） |
| **U-Boot** | v2026.04 / v2026.07（数十款板） |
| **安装器** | armbian-install 重写 → armbian-config 模块，单元测试覆盖 |
| **Imager** | Armbian Imager 2.0，新增 QDL + UFS 烧录 |
| **ISO 镜像** | 标准化 UEFI ISO（桌面 + minimal） |
| **新板支持** | Anbernic RG DS / RG Vita Pro、Luckfox Nova、LubanCat 5IO、KICKPI K3B、Seeed reComputer RK3576/RK3588 等 |
| **CI 基础设施** | 主仓库迁出 → 独立 CI（Debian Trixie） |

---

## 二、内核与固件：全面升到 Linux 7.1

### 2.1 Mainline baseline

Armbian 26.8 把所有平台的 mainline baseline 推进到 **Linux 7.1 stable**。这意味着：

- 拿到 7.0 → 7.1 之间的所有 bug fix 与性能优化（包括 EXT4 / IOmap / NFS 等多个子系统的累积改进——如果读过前面几篇应该熟悉）。
- 之前 edge 分支上跑的较新内核改动现在进入 mainline，**降低使用 edge 的风险**。

### 2.2 Edge 分支：5 平台追到 7.2-rc

edge 分支在以下 5 个平台已经追到 **Linux 7.2-rc**：

- **rockchip64**：Rockchip RK35xx / RK3588 系列。
- **meson64**：Amlogic S905/S922 系列。
- **mvebu64**：Marvell Armada 370/380/385/7K/8K。
- **sunxi**：Allwinner 系列。
- **bcm2711**：树莓派 4 / 5。

这些平台的 early adopters 能更早看到 7.2 的新特性（性能调度、文件系统、驱动更新等），但**稳定性需要自行评估**——7.2 还没出 stable。

### 2.3 U-Boot 升级

U-Boot 升到 **v2026.04 / v2026.07**，覆盖板子包括 Rockchip RK35xx、Amlogic、i.MX6、Espressobin 等数十款。U-Boot 升级通常伴随 SPI/eMMC/NVMe 启动路径的修正，对新板支持意义重大。

---

## 三、armbian-install 重写：从"脚本拼盘"到"模块化工具"

### 3.1 老安装器的问题

Armbian 老安装器（`armbian-install`）是 shell 脚本 + 命令行工具的拼盘，覆盖了：

- eMMC / NVMe / USB 目标写入。
- SPI / MTD 启动目标设置。
- 双启动 / UEFI 兼容路径。
- 网络引导（NFS / TFTP）。
- 调试 / 诊断输出。

但脚本风格的代码有几个**长期积累的问题**：

- 没有单元测试，重构风险大。
- 参数解析分散在各处，用户脚本兼容性脆弱。
- 错误处理不一致，失败时不易定位。
- 新功能（QDL / UFS 烧录）难以直接复用基础路径。

### 3.2 新安装器架构

26.8 把安装器**完全重写**，作为 `armbian-config` 的一个模块交付：

- **单元测试覆盖**：每个功能路径都有对应测试。
- **统一参数接口**：旧 flag 仍然兼容（但警告迁移到新 flag）。
- **模块化**：QDL / UFS 烧录、bootloader flashing、SPI/MTD targeting 都能复用基础路径。
- **改进诊断**：UEFI / dual-boot 路径输出更清晰。
- **支持拆分的 eMMC / NVMe 安装流**：bootloader 在 eMMC、rootfs 在 NVMe 这种"混合启动"配置更可靠。

### 3.3 兼容性与迁移

- **继续支持旧 flag**，但会在输出里提示"建议改用新 flag"。
- **依赖旧 armbian-install 行为的脚本**可能需要小幅修改——特别是用到了已废弃 flag 的自动化工具。
- **新装机用户**不会有感知，安装流程体验更顺。

---

## 四、Armbian Imager 2.0：QDL + UFS 烧录

### 4.1 是什么

Armbian Imager 是 Armbian 提供的图形化镜像烧录工具（与树莓派 Raspberry Pi Imager 类似）。2.0 版本是**功能性大版本更新**：

- **QDL 烧录**：Qualcomm 高通平台的特定烧录协议。Qualcomm 设备不像 Rockchip / Amlogic 那样有通用 fastboot，QDL 是少数几个能烧录 Qualcomm SoC 的工具链。
- **UFS 烧录**：UFS（Universal Flash Storage）烧录工具，针对现代移动设备存储。
- **板卡识别改进**：自动识别连接的板卡型号，减少手动选择。

### 4.2 实战意义

对 SBC 玩家来说，2.0 解决的"烧录最后一公里"问题：

- 之前想给 Qualcomm SoC 板（如部分工业 SBC）烧 Armbian，得用 QPST / Sahara 这类 Qualcomm 专用工具。
- 现在 Imager 2.0 内置 QDL，**一条命令解决**。
- UFS 烧录同理，对使用 UFS 存储的设备更友好。

---

## 五、标准化 UEFI ISO

### 5.1 为什么 UEFI ISO 重要

之前 Armbian 用户部署 SBC 通常是：

1. 烧 SD 卡镜像。
2. 用 armbian-install 写入 eMMC / NVMe。
3. 重启进入系统。

这种流程对**桌面 / 服务器用户**不友好——他们习惯 ISO 镜像 + U 盘 + 直接启动安装程序。Armbian 26.8 起，**提供标准化的 UEFI ISO 镜像**，覆盖桌面版和 minimal 版。

### 5.2 实战场景

- **PVE / VMware / VirtualBox 跑 Armbian VM**：直接挂 ISO 安装，不再依赖特殊镜像。
- **直接 U 盘启动 Armbian 桌面**：对习惯 Linux 桌面 / 服务器镜像的用户零学习成本。
- **CI 自动化**：用 ISO 引导 + preseed 风格的自动化安装。

注意：**UEFI ISO** 主要针对**通用架构**（x86_64 / 部分 aarch64 仿真）。具体到每款 SBC 是否支持 ISO 启动，还要看板子的 U-Boot / UEFI 固件支持情况。

---

## 六、新增 SBC 支持

26.8 落地了多款新 SBC 支持，覆盖游戏机、工业、物联网场景：

| 板子 | 厂商 | 场景 |
|------|------|------|
| **Anbernic RG DS** | Anbernic | 游戏掌机（复古 DS 风格） |
| **Anbernic RG Vita Pro** | Anbernic | 游戏掌机（Vita 风格） |
| **Luckfox Nova** | Luckfox | 物联网 / 边缘计算 |
| **LubanCat 5IO** | LubanCat | 工业 / 5 IO 扩展 |
| **KICKPI K3B** | KICKPI | 工业 / 多媒体 |
| **Seeed reComputer RK3576** | Seeed | 工业 / AI 边缘 |
| **Seeed reComputer RK3588** | Seeed | 工业 / AI 边缘 |

新板支持通常是 Armbian 社区与厂商合作完成的——厂商提供硬件资料与 boot loader，社区负责内核配置、Armbian build framework 适配、文档。

---

## 七、CI 流水线：从主仓库迁出

### 7.1 为什么迁

Armbian 主仓库（GitHub: armbian/build）之前承担双重角色：

1. 配置文件、脚本、文档（给用户看、给社区改）。
2. CI 流水线（每次 PR 自动构建 + 测试所有 SBC 镜像）。

这种"代码 + CI 同仓"的模式有几个问题：

- CI 配置改动频繁，污染主仓库的 commit 历史。
- 用户 clone 主仓库时会拉下大量 CI 相关文件（虽然 .github/ 通常忽略）。
- CI 失败时的 debug log 占据大量仓库空间。

### 7.2 新 CI 基础设施

26.8 起，**CI 流水线迁出主仓库**，独立部署在新基础设施：

- **基础系统**：Debian Trixie。
- **目标**：加快构建速度、提高稳定性、便于多平台扩展（未来可能上 ARM64 CI runner）。
- **影响**：用户 clone 主仓库体积变小、CI 失败时去专门仓库查 log。

---

## 八、对 SBC 用户的影响

### 8.1 普通玩家（桌面 / 媒体中心）

- **强烈升级**：拿到 Linux 7.1 + Armbian 26.8 安装器改进 + Imager 2.0 全部福利。
- **注意**：如果用 ISO 启动 + UEFI 路径，先确认你的 SBC U-Boot / 固件支持 UEFI 引导。

### 8.2 工业 / IoT 部署

- **重点评估安装器重写**：自动化脚本可能因 flag 变更需要调整。
- **UFS / QDL 烧录**：如果是 Qualcomm 或 UFS 存储设备，Imager 2.0 是直接收益。
- **新板支持**：6+ 款新 SBC 让工业选型更有余地。

### 8.3 开发者

- **新内核基线（7.1）**：内核模块如果依赖特定内核版本（如自定义 GPIO、传感器驱动），需要重新编译。
- **Edge 分支（7.2-rc）**：早期采用者能拿到性能调度改进，但稳定性需自行评估。
- **CI 基础设施变化**：提交 PR 时注意 CI 跑在新基础设施，构建速度可能与之前不同。

### 8.4 升级路径建议

```bash
# 1. 备份
mkdir -p /root/armbian-backup-26.8
armbian-config --backup  # 如果支持

# 2. SD 卡用户
dd if=/dev/mmcblk0 of=/root/armbian-backup-26.8/sd-card.img.bz2 bs=4M status=progress

# 3. eMMC / NVMe 用户：用 armbian-config 里的 backup 功能
armbian-config
# 选 "Backup" → 选目标设备

# 4. 升级
apt update && apt upgrade -y
# 或重新下载 26.8 镜像烧录

# 5. 验证
uname -r  # 应显示 7.1.x
cat /etc/armbian-release  # 应显示 26.8
```

---

## 九、关注下一个版本

Armbian 26.8 落地后，下一步看点：

- **Imager 2.0 后续版本**是否加入更多 SoC 烧录协议（如 MediaTek、Allwinner 等）。
- **标准化 UEFI ISO**是否能扩展到更多 SBC（特别是游戏掌机类设备）。
- **Linux 7.2 stable 发布后**是否会作为 26.9 或 27.x 的 mainline baseline。
- **CI 基础设施**未来是否会对外开放（让社区贡献者跑相同 CI）。

---

## 十、Armbian 在 SBC 生态里的位置

最后说一句背景。Armbian 不是唯一做 SBC 操作系统的项目，但它有几个独特优势：

- **覆盖广**：Rockchip / Amlogic / Allwinner / Marvell / 树莓派 / 高通……Armbian 是覆盖 ARM + RISC-V SBC 最多的社区发行版。
- **Debian/Ubuntu 基础**：包管理与文档生态成熟，新用户学习成本低。
- **社区驱动**：相比厂商官方系统（如 FriendlyCore、Armbian 的某些分支），Armbian 更新更频繁、bug 修复更快。
- **可定制**：用户能用 Armbian build framework 自己编译定制镜像。

但它也有局限：

- **不绑定特定硬件**：很多 SBC 厂商同时提供官方系统 + Armbian 支持，Armbian 是"通用选项"而非"最优选项"。
- **新板支持滞后**：新 SBC 出来后，厂商官方系统可能立即支持，Armbian 需要等社区适配（通常数周到数月）。
- **文档分散**：Armbian 的文档在多个地方（docs.armbian.com、论坛、GitHub wiki），新手容易迷路。

Armbian 26.8 这一波**安装器重写 + UEFI ISO + 7.1 内核**三件套，是在补"通用选项"的体验短板。对 SBC 用户来说，是个值得升级的版本。

---

**参考资料**：

1. Armbian 26.8 官方公告：https://blog.armbian.com/armbian-release-26-8/
2. Armbian 26.8 文档：https://docs.armbian.com/releases/26.8/
3. Armbian 8 月 newsletter：https://blog.armbian.com/armbian-newsletter-august-2026/
4. Phoronix 报道：https://www.phoronix.com/news/Armbian-26.8-Released
5. Armbian 主仓库：https://github.com/armbian/build
6. Linux 7.1 内核：https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

---

*本文基于 Armbian 26.8 官方公告、官方文档、Phoronix 报道与社区资料整理，旨在为中国 SBC 玩家与工业部署团队提供快速理解和参考。*

*作者观点不代表任何厂商立场，仅供技术讨论参考。Linux 7.1 / 7.2-rc 内核基线、armbian-install 重写后的 flag 兼容性、Imager 2.0 的 QDL/UFS 烧录支持范围，建议以官方文档为准。*