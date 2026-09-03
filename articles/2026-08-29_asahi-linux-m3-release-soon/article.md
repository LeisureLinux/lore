# Asahi Linux M3 支持即将发布：M3 / M3 Pro / M3 Max 全覆盖，M4 / M5 紧跟

> **原始出处**：Asahi Linux 官方进展报告（7.2 Progress Report）+ Phoronix + AppleInsider
> **发布日期**：2026 年 8 月 29 日（更新日志）
> **作者**：Asahi Linux 团队（Alyssa Rosenzweig 等核心贡献者）
> **官方进展报告**：https://asahilinux.org/2026/08/progress-report-7-2/
> **M3 特性支持文档**：https://asahilinux.org/docs/platform/feature-support/m3/
> **Phoronix 报道**：https://www.phoronix.com/news/Asahi-Linux-M3-Release-Soon
> **翻译/解读**：LeisureLinux
> **关键词**：Asahi Linux、Apple M3、Linux on Apple Silicon、linux-asahi、M4 bring-up

## 引言：苹果硅 Linux 走到 M3 这一步

Asahi Linux 是把 Linux 带到 Apple Silicon 硬件的开源项目。8 月 29 日的进展报告（"Linux 7.2"周期）公布了三件事：

1. **M3 / M3 Pro / M3 Max 支持即将正式发布**，目标"几周内"。
2. **M3 系列已覆盖**：PCIe、NVMe 存储、键盘 / 触控板、SMC RTC、reboot 控制器、内置麦克风、完整 webcam 支持（M3 Max 的初始化修复已就位）。
3. **M4 / M5 bring-up 持续推进**：早期内核初始化崩溃被修掉、idle 循环与 cpuidle 配置参数落地、存储 / CPU sleep / 硬件视频解码 / 共享 display buffer 都有进展，`m1n1` bootloader 与 Apple 更新安全架构保持兼容。

如果 Asahi Linux 在过去几年是"先把 M1 跑起来"的阶段，这次更新是"把所有 Mac 用户都覆盖到"——M3 全覆盖意味着 Apple Silicon Mac 的 Linux 支持跨过了大多数用户的门槛。M4 / M5 在路上。

---

## 一、Asahi Linux 当前节奏

Asahi Linux 的开发节奏有两条线：

- **`linux-asahi` 分支**：所有稳定 / 用户可用特性先在这里落地。
- **主线（upstream）**：每批稳定特性向后回推到 Linus 的主线内核。

当前状态：

- M1 / M2 系列：长期稳定，用户可在 `linux-asahi` 安装。
- **M3 系列：即将正式发布**。
- M4 / M5：active development，未达用户可用。

进展报告（"Linux 7.2"）对应上游内核 7.2 合并窗口周期。

---

## 二、M3 支持细节

### 2.1 覆盖的硬件

| 硬件组件 | 状态 |
|---------|------|
| **CPU 核心** | ✅ 全系（M3 / M3 Pro / M3 Max） |
| **PCIe** | ✅ |
| **NVMe 存储** | ✅ |
| **键盘 / 触控板** | ✅（MacBook 全系） |
| **SMC RTC** | ✅（基于 SMC 的实时时钟） |
| **Reboot 控制器** | ✅（基于 SMC） |
| **内置麦克风** | ✅ |
| **Webcam** | ✅ 全覆盖（含 M3 Max 的初始化修复） |
| **GPU** | ⚠️ 部分（详见下文） |
| **显示** | ⚠️ 基础（framebuffer） |

GPU 是 Asahi Linux 一直啃的硬骨头——Apple Silicon GPU 是自研架构，没有公开规范，需要逆向 + 开源驱动（Asahi 团队的 AGX Gallium 驱动）。M3 上的 GPU 用户态驱动还在持续打磨。

### 2.2 关键技术挑战

Asahi Linux 在 M3 上需要解决的几个核心问题：

- **SMC 依赖**：Apple Silicon 的电源 / 时钟 / 风扇都通过 SMC（System Management Controller）控制。Linux 必须通过 SMC 驱动才能完整管理硬件。
- **DCP / ASC**：Apple 的 display coprocessor / audio coprocessor 需要驱动对接。
- **安全架构**：Apple Silicon 的 Secure Boot 链 + `m1n1` 一级引导 + u-Boot / GRUB 的二级引导必须保持兼容。
- **GPIO / PIN 复用**：MacBook 内部的键盘、触控板、麦克风、摄像头 sensor 都走 GPIO，需要 pin 复用的精细配置。

M3 支持里，**M3 Max 的初始化修复**是这次的细节亮点——M3 Max 的某个外围控制器在初始化时序上与 M3 / M3 Pro 不同，需要专门 workaround。

---

## 三、M4 / M5 bring-up 进展

### 3.1 M4 上的内核初始化崩溃

M4 芯片在早期 bring-up 时遇到一个怪问题：**内核启动时崩溃**，但崩溃发生在 cpuidle 驱动加载之前。M3 / M2 / M1 都没这个问题。

Asahi 团队定位后引入了一个**内核命令行参数**，让 cpuidle 接管前显式配置 idle 循环和 core parking——绕过 Apple SMC 的 cpuidle 路径，避免早期崩溃。

这种"内核命令行参数 workaround"是 bring-up 阶段的典型手法：等硬件支持稳定后才会切换到更优雅的实现。

### 3.2 共享 display buffer / 硬件视频解码

M4 / M5 上的两项重要进展：

- **共享 display buffer**：多进程共享 GPU 显示缓冲区的支持。这是 macOS 上 GUI 应用能高效协同的基础。
- **硬件视频解码**：Apple Silicon 的媒体引擎（AME）在 macOS 上提供 H.264 / HEVC / ProRes 硬件解码。Linux 上要对接需要逆向 + 编写新的驱动（社区项目：Asahi Video）。

### 3.3 m1n1 bootloader 兼容 Apple 新安全架构

`m1n1` 是 Asahi Linux 的一级 bootloader（由 Alyssa Rosenzweig 等人开发）。它必须与 Apple 持续更新的安全架构保持兼容——每次 Apple 推送 iBoot / SecureROM 更新，m1n1 都可能需要跟进。

这次报告里提到**保持与 Apple 更新安全架构的兼容**——意味着 m1n1 还在主动维护。

### 3.4 存储 / CPU sleep 状态

M4 / M5 上 NVMe 控制器与 Apple 自研 SSD 控制器的 power state 管理更复杂。需要更多 CPU idle state（`cpuidle`）调优，避免进入 sleep 后无法唤醒。

---

## 四、Asahi Linux 与苹果硅生态

### 4.1 为什么 M3 是"门槛"

Apple Silicon Mac 从 M1 到 M3 Pro/Max，硬件复杂度逐代上升。但对 Linux 来说：

- **M1 / M2**：基本稳定，用户群体包括开发者、研究人员、Linux 极客。
- **M3**：覆盖到大多数 Apple Silicon Mac 用户——M3 Pro / Max 是高端 MacBook Pro / Mac Studio 的主选。
- **M4 / M5**：跟随苹果节奏，未来一年内陆续到位。

Asahi Linux 把 M3 跑稳意味着：如果你今天买一台 M3 MacBook Air / Pro，**几周后就有 Linux 可装**，日常使用覆盖 CPU / 存储 / 输入 / 音频 / 摄像头，体验接近 macOS（除了 GPU）。

### 4.2 GPU 的硬骨头

Apple Silicon GPU 没有公开规范，是项目最大的硬骨头：

- **AGX Gallium 驱动**：Asahi 团队自研的开源 Mesa 驱动，对应 macOS Metal API。
- **状态**：M1 / M2 上基本可用，M3 部分可用，**M4 / M5 还在写**。
- **应用场景**：日常 GPU 加速（浏览器、视频、基础图形）可用；专业 3D / ML 加速仍在追赶。

### 4.3 项目组织

Asahi Linux 是**完全开源**项目，核心贡献者：

- **Alyssa Rosenzweig**（主要 GPU 逆向 + Mesa 驱动）
- **Hector Martin**（"marcan"，项目创始人，2024 年因 burnout 退出日常维护）
- **Dougall Johnson**（早期 Apple Silicon bring-up）
- **James Callahan**、**Martin Povišer** 等

资金来源：社区捐赠 + 部分企业赞助。Apple 本身**没有官方支持**这个项目。

---

## 五、对 Linux on Apple Silicon 用户的影响

### 5.1 M1 / M2 用户

- 已经在用 Asahi Linux 的用户继续享受稳定升级。
- `linux-asahi` 仓库与上游主线的回推进度持续推进。
- 7.2 周期内拿到若干 bug fix。

### 5.2 M3 用户（即将可用）

- **几周内**可以在 M3 / M3 Pro / M3 Max 设备上装 Linux。
- 覆盖：CPU + NVMe + 输入设备 + 音频 + 摄像头 + 基础显示。
- **不覆盖**：GPU 全功能、Thunderbolt 完整特性、FaceTime / Continuity 等苹果专属功能。
- **建议**：当作日常 Linux 工作机可用；当作 macOS 替代品（专业视频 / 3D）不行。

### 5.3 M4 / M5 用户

- 持续观望，每 2-3 个月 Asahi 会更新一次进展报告。
- 可以关注 `linux-asahi` 仓库的早期 commit，但**不建议在生产设备上尝试**未发布支持。

### 5.4 苹果硅外的开发者

- **借鉴意义**：Asahi Linux 把 ARM SoC 上的 reverse-engineering + 上游回推做到极致。其他 ARM 平台（高通 / 联发科）也可参考这条路径。
- **GPU 驱动范式**：AGX 是开源 GPU 驱动的标杆，未来 RISC-V / ARM GPU 都可能走类似路径。

---

## 六、关注下一阶段

### 6.1 GPU 驱动

M3 GPU 用户态驱动的打磨是当前最重的工作。M3 上 AGX Gallium 驱动在持续改善——预计未来 6-12 个月会有显著可用性提升。

### 6.2 上游回推

Asahi Linux 团队持续把稳定特性回推到 Linus 主线。Linux 7.2 周期已经合并了一部分，未来几个版本会有更多 Asahi 贡献的代码进入主线——这对其他 ARM 平台也是收益。

### 6.3 M4 / M5 时间表

Apple Silicon 的更新节奏大约是一年一代。Asahi Linux 的 bring-up 通常落后 6-12 个月。M4 大概率在 2026 年底 - 2027 年上半年达到用户可用；M5 在 M4 之后 6-12 个月。

### 6.4 周边生态

- **Fedora Asahi Remix**：官方推荐的发行版。
- **Arch Linux ARM**：社区支持的发行版。
- **Ubuntu**：早期有计划，但官方支持不稳。
- **NixOS**：社区支持 ARM64，可以装。

如果想做 M3 上 Linux 的"日常用机"，**Fedora Asahi Remix** 是最稳的入口。

---

## 七、Asahi Linux 的开源意义

Asahi Linux 不只是"在 Mac 上装 Linux"——它的更大意义：

### 7.1 平台独立性

Apple Silicon 的 macOS 与 iOS / iPadOS 越来越收紧，第三方系统安装空间被压缩。Asahi Linux 是少数能让用户**完全掌控**自己硬件的开源项目——这对软件自由、设备长期可用性、用户数据主权都有意义。

### 7.2 上游 Linux 的收益**

Asahi Linux 把很多 ARM SoC 的支持反向贡献到 Linux 主线（包括但不限于 Apple Silicon 专有部分）：

- SMC 驱动框架
- GPIO / PIN 复用抽象
- 电源管理子系统改进
- ARM64 early console

这些改进对其他 ARM 平台（高通、联发科、未来 RISC-V）也是直接收益。

### 7.3 开源 GPU 范式

AGX Gallium 是**第一个**为 Apple Silicon GPU 编写的开源 Mesa 驱动。它证明了逆向 GPU + 开源驱动是可行的——这对未来苹果硅外的开源 GPU 生态有范式意义。

---

**参考资料**：

1. Asahi Linux 进展报告 7.2：https://asahilinux.org/2026/08/progress-report-7-2/
2. Asahi Linux M3 特性文档：https://asahilinux.org/docs/platform/feature-support/m3/
3. Phoronix 报道：https://www.phoronix.com/news/Asahi-Linux-M3-Release-Soon
4. AppleInsider 报道：https://appleinsider.com/articles/26/08/29/asahi-linux-nears-m3-support-release-m4-and-m5-are-on-the-way
5. linux-asahi 仓库：https://github.com/AsahiLinux/linux-asahi
6. m1n1 bootloader：https://github.com/AsahiLinux/m1n1
7. Fedora Asahi Remix：https://asahilinux.org/distros/

---

*本文基于 Asahi Linux 7.2 进展报告、Phoronix 报道、AppleInsider 报道与官方文档整理，旨在为中国 Linux on Apple Silicon 爱好者与开发者提供快速理解和参考。*

*作者观点不代表任何厂商立场，仅供技术讨论参考。M3 支持"即将发布"为 Asahi 团队表述，最终发布时间、覆盖范围与具体功能以官方公告与文档为准。*