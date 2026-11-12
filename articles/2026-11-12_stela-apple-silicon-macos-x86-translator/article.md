---
title: "Stela：把 Apple Silicon 版 macOS 翻译到 x86 PC 上"
date: 2026-11-12
slug: stela-apple-silicon-macos-x86-translator
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：GitHub 仓库 tylertms/Stela 的 README 全文、NOTICE 许可清单、.gitmodules、Cargo.toml、rust-toolchain.toml 与完整文件树（GitHub API，2026-11-12 查询：840 stars / 33 forks / 7 open issues / Rust / GPL-2.0 / 6956 个文件）＋ GitHub Releases API（v0.1.0 11-11、v0.2.0 11-11、v0.3.0 11-12 三个版本）＋ Issues API（RTL8125 安装卡住、AX210 驱动、存储分区、AMI 主板 ECAM、GTX 1060 请求等）＋ 作者在 r/hackintosh 的技术说明帖 ＋ Apple 官方《About the Rosetta translation environment》与《Rosetta 2 on a Mac with Apple silicon》＋ 日媒 すまほん!! 2026-11-12 报道（Ryzen 7 9800X3D + RTX 5080 演示、Tahoe 26 是 Intel Mac 最后一版）"
original_date: 2026-11-11
original_url: "https://github.com/tylertms/Stela"
description: "本文解读 Stela：一个从 PC 的 UEFI 启动、把未经修改的 Apple Silicon 版 macOS 跑在 x86-64 机器上的实验项目。它不是一个模拟器也不是传统 Hackintosh，而是四层拼起来的「Apple Silicon 兼容层」：AOT+JIT 的 arm64e→x86-64 翻译器（覆盖 3000+ AArch64 指令编码、寄存器映射与翻译缓存，要求 x86-64-v2）、把 Metal 的 AIR 着色器 IR 直接编译成 Mesa NIR 的 NVIDIA 驱动（GTX 16 / RTX 20 及更新，支持 Metal3 与 Apple7 GPU family）、Apple Silicon 硬件行为模型（当前模拟 Mac mini M2、跑 macOS 27）、以及自研 UEFI 引导与 Linux/Mesa/LLVM 驱动栈。硬件要求写得很硬：x86-64-v2、关 Secure Boot、8GB 内存、NVIDIA Turing 及更新独显、8GB U 盘、60GB 空 GPT 分区、安装时联网下载 macOS；安装器会清空 U 盘。文章对照 Rosetta 2（Apple 官方：x86_64→arm64、只翻应用层、不翻 kext 与虚拟机、AOT 与 JIT 两条路径），指出 Stela 是反向且更底层的翻译：翻的是整个内核与驱动面，还要伪造 SoC 与 GPU，难度与法律面都不同。也如实写出状态：README 顶部 WARNING「当前能启动的概率很低」、v0.1.0 自述慢且需大量测试、Cargo.toml 已到 0.3.0、三天连发三个版本、issues 里全是启动卡死与驱动缺失报告。法律与许可单独成节：仓库不含 Apple 软件、用户自负 Apple SLA 合规责任；NOTICE 把各产物按 GPL-2.0-only / GPL-3.0-or-later 分得很细，并列出 Linux 7.2.12、Mesa 26.2.5、LLVM 23.1.4、XNU、libdrm、smoltcp 等第三方组件。结论：技术价值在跨 ISA 全栈翻译与开源驱动复用，不是「黑苹果复活」；想试的人要按仓库的硬件条件与警告来。"
published: true
---

> 一手：Stela 仓库 README、NOTICE 许可清单、`.gitmodules`、`Cargo.toml`、Releases 与 Issues API
> 对照：作者在 r/hackintosh 的说明、Apple 官方 Rosetta 文档、同期媒体报道
>
> 这个项目最容易被写错的一句，是把它叫成「新版黑苹果」。

11 月 11 日，GitHub 上出现了一个叫 Stela 的项目（`tylertms/Stela`），一句话描述是：在 x86-64 PC 上启动未经修改的 Apple Silicon 版 macOS。到 11 月 12 日我查的时候是 840 stars、33 forks、6,300 commits、6,956 个文件、主语言 Rust、GPL-2.0；三天内连发了 v0.1.0、v0.2.0、v0.3.0。

中文转述很容易写成「Hackintosh 复活了」。但把 README、NOTICE 和仓库结构读完，会发现它做的事和传统黑苹果方向相反、层级也深得多。

## 一、它不是模拟器，也不是黑苹果

传统 Hackintosh 的前提是：Intel 版 macOS 与 PC 是同一种 CPU，活儿主要在伪造 EFI/设备属性、补 kext、骗过系统完整性检查。而 Apple 已经把 macOS Tahoe 26 定为 Intel Mac 的最后一个版本，往后 macOS 27 只有 arm64 版 —— 这条路自然就断了。

Stela 换了个思路：既然只剩 Apple Silicon 版 macOS，那就把 arm64 的整个系统翻译到 x86-64 上跑。仓库描述写的是「面向 x86-64 PC 的通用 Apple Silicon 层」，作者自己在 r/hackintosh 里强调：没有 OpenCore、没有 kext、不拼 x86 内核残片，启动的是一个自研 EFI 应用，直接引导未经修改的 arm64 macOS。

它由四层拼起来：

| 层 | 做什么 | 仓库里的对应物 |
|---|---|---|
| UEFI 引导 | 从 U 盘启动、接管机器 | `crates/stela-boot`、`stela-boot-core`、`stela-loader` |
| 指令翻译 | arm64e → x86-64 的 AOT + JIT | `crates/stela-compiler`、`stela-engine`、`stela-runtime` |
| GPU | Metal → NVIDIA | `crates/stela-driver-gpu`（内含 `metal/input`）、`stela-mesa` |
| SoC 模型 | 伪造 Apple Silicon 硬件行为 | `crates/stela-soc`、`stela-soc-data`、`stela-fingerprint` |

配套还有 audio / net / storage 驱动 crate、TLS、crypto、formats 等 —— 26 个 crate，加上 `third_party/` 里的 Linux、Mesa、LLVM、libdrm、XNU 五个子模块。这已经是一个小型操作系统工程，不是一个引导补丁。

## 二、翻译器：方向反过来的 Rosetta

README 给的规格：

- AOT + JIT 并用，覆盖 3,000+ 条 AArch64 指令编码；
- guest 寄存器映射到 host 寄存器、缓存翻译结果；
- 要求 x86-64-v2 CPU（约 2011 年以后），Intel / AMD 都行；
- 翻译对象是 arm64e（带指针认证的 arm64 变体），不是普通 arm64 用户态程序。

拿 Apple 官方 Rosetta 文档对照，差别很清楚：

| | Rosetta 2 | Stela |
|---|---|---|
| 方向 | x86_64 → arm64（在 Apple Silicon 上跑 Intel 应用） | arm64e → x86-64（在 PC 上跑 Apple Silicon 系统） |
| 翻译范围 | 应用层整个进程，含动态加载模块 | 内核 + 驱动 + 应用，整套系统 |
| 不翻的东西 | kext、虚拟化 x86_64 的 VM | 全部都要处理，还要自己造驱动 |
| 硬件前提 | Apple SoC、Apple GPU | 任意 x86-64-v2 + NVIDIA 独显 |
| AOT/JIT | 两者皆有，AOT 结果不随系统分发、按需重建 | AOT + JIT，带寄存器映射与翻译缓存 |

Rosetta 只解决「旧应用怎么在新芯片上跑」，内核还是原生的；Stela 得让一个以为自己跑在 M2 上的 XNU 内核，在 Intel/AMD 的页表、中断、APIC、定时器上正常工作。作者在 Reddit 里把目标写成「希望最终达到 Rosetta 2 级别的翻译应用速度」，也等于承认现在远没到。

## 三、Metal 驱动：AIR 直接编译到 NIR

这是全项目最巧的一块。Apple Silicon 版 macOS 只认 Metal，而 PC 上插的是 NVIDIA 卡。Stela 的做法不是把 Metal 转成 SPIR-V 再走通用路径，而是把 Metal 的着色器中间表示 AIR 直接编译成 Mesa 的 NIR，复用 Mesa 的 NVK / NAK Vulkan 运行时落到 NVIDIA 硬件上。支持 Metal3 与 Apple7 GPU family，显卡门槛是 GTX 16 / RTX 20 系列及更新（Turing 起）。

作者在同一帖里提到这条路线「不如 nullmoth 的成熟」—— 后者走 SPIR-V，另有 Liberator 项目拼 x86 内核残片；他选直接 AIR→NIR 是赌 Apple 未来把 x86 残留彻底删掉后，自己这条路还能活。NOTICE 里能看到 Mesa 26.2.5、libdrm 2.4.133、LLVM 23.1.4 都被编进 `stela.efi`，等于把一个 Mesa 图形栈塞进了 UEFI 应用。

其余硬件也得自己造：`stela-driver-net` / `-audio` / `-storage` 对应 Wi-Fi、蓝牙、声卡、NVMe；NOTICE 里点了 FreeBSD e1000、MediaTek mt76、Asahi Linux 的 hci_bcm4377 等驱动移植。这也解释了为什么当前 issues 里全是「RTL8125 网卡装到一半卡住」「AX210 驱动没加载」「存储打不开：找不到分区」—— 卡点几乎全在外设，不在 CPU 翻译。

## 四、硬件条件与真实状态

README 的要求写得不含糊：

- x86-64-v2 CPU（约 2011 年后）、UEFI 关闭 Secure Boot、8 GB 内存；
- NVIDIA GTX 16 / RTX 20 及更新独显（当前不支持 AMD/Intel 核显，作者把更多驱动列为后续目标）；
- 8 GB 以上 U 盘、至少 60 GB 的空 GPT 分区、安装时联网下载 macOS；
- 安装器 `sudo ./stela setup` 会清空所选 U 盘；
- 当前模拟 Mac mini (M2)，跑 macOS 27。

作者在 r/hackintosh 的原话是「现在还不建议试」，README 顶部挂着 WARNING：「Your current chances of it booting are low」，v0.1.0 说明里写「macOS 和大多数应用能启动，但很慢，还需要大量测试」。这不是谦辞 —— 我查 Releases 时，11-11 到 11-12 三天发到 v0.3.0，issues 里同时有「Ryzen 7 5700X 上修好启动、装到首次进系统」的外部 PR 与多个失败报告；日媒报的演示机是 Ryzen 7 9800X3D + RTX 5080，跑 macOS 27.2，属于特定高端配置下的成功案例。

还有个版本口径要标一下：README 正文仍写「as of v0.1.0」，但 `Cargo.toml` 的 `workspace.package.version` 已是 0.3.0。仓库迭代极快，任何「支持哪些硬件/系统」的结论都要按当天 release 重看。

## 五、法律与许可，别跳过

README 的 Legal 只有两行，但分量很重：Stela 不含任何 Apple 软件，遵守 Apple 软件许可协议与使用条款是使用者自己的责任；Stela 自身代码 GPL-2.0-or-later。换句话说，安装时联网下载的那份 macOS 从哪来、能不能装在这台机器上，项目不替你回答。

`NOTICE` 比一般开源项目严谨得多，把每个产物的许可单独列了：

| 产物 | 许可 |
|---|---|
| `stela.efi` | GPL-2.0-only（含 Linux 代码） |
| `stela` CLI | GPL-3.0-or-later（链接 Apache-2.0 crates，不含 GPL-2.0-only 代码） |
| `Stela.app` / `StelaGPU.kext` / `StelaGPU.bundle` / `stela-gpu-maintenance` | GPL-2.0-or-later |

它还说明了两个容易踩坑的点：CLI 里聚合了一份 `stela.efi`（只写入 U 盘、不链接不运行），以及再分发二进制必须同时提供同 revision 的仓库 + 各子模块 pin 的 commit + `third_party/patches/` 里的补丁 + 构建脚本。第三方清单列了 Linux kernel 7.2.12、Mesa 26.2.5、LLVM 23.1.4、XNU、libdrm、smoltcp、Mbed TLS、BLAKE3、Spleen 字体、Arm AARCHMRS 数据等，并逐项标了许可证与用途。对做合规或打包的人，这份 NOTICE 比 README 更值得读。

## 六、事实边界

- 本文以 2026-11-12 查询的仓库状态为准：840 stars / 33 forks / 7 open issues、6,300 commits、Rust、GPL-2.0、README 仍写 v0.1.0、`Cargo.toml` 为 0.3.0、Releases 到 v0.3.0。数字会变。
- 所有功能与硬件要求来自 README、NOTICE、`Cargo.toml`、`.gitmodules` 与作者在 r/hackintosh 的说明帖；本文未下载 Stela、未在任何机器上尝试安装或启动，未验证「macOS 与大多数应用能启动」这一说法。
- 演示配置（Ryzen 7 9800X3D + RTX 5080 / macOS 27.2）来自同期媒体报道与社区截图，属个例，不代表兼容列表。
- Rosetta 2 的 AOT/JIT、不翻 kext 与 VM、翻译整个进程等描述取自 Apple 官方文档；Stela 与 Rosetta 的对照为本文分析，非官方比较。
- 法律部分仅转述仓库声明，不构成对 Apple 许可协议适用性的判断或建议。

## 七、结论

把 Stela 叫「Hackintosh 复活」，会漏掉它真正难的地方：传统黑苹果是同架构下骗过系统，Stela 是跨 ISA 把整个内核、驱动、图形栈、SoC 行为翻译一遍，还顺手把 Mesa / LLVM / Linux 驱动塞进一个 UEFI 应用里。Rosetta 是 Apple 自己在新芯片上兼容旧应用；Stela 是社区在旧芯片上兼容新系统 —— 方向反着，难度也不在一个量级。

但就当前状态，它离「可用」还很远：README 自己说启动概率低、慢、需大量测试，issues 里全是外设卡死，作者也不建议现在就试。值得跟的是它的架构思路与那 26 个 crate 的开源实现，以及三天三个版本的迭代速度 —— 而不是把它当成能装来日常用的 macOS。

## Sources

- GitHub 仓库：<https://github.com/tylertms/Stela> ｜ README：<https://raw.githubusercontent.com/tylertms/Stela/main/README.md> ｜ NOTICE：<https://raw.githubusercontent.com/tylertms/Stela/main/NOTICE>
- Releases：<https://github.com/tylertms/Stela/releases> ｜ Issues：<https://github.com/tylertms/Stela/issues>
- 作者在 r/hackintosh 的说明：<https://www.reddit.com/r/hackintosh/comments/1xt9bhp/stela_a_generalpurpose_apple_silicon_layer_for_pc>
- Apple 官方《About the Rosetta translation environment》：<https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment>
- Apple 官方《Rosetta 2 on a Mac with Apple silicon》：<https://support.apple.com/guide/security/rosetta-2-on-a-mac-with-apple-siliconsecebb113be1/1/web/1>
- すまほん!!《普通のPCでmacOS 27が起動？「Stela」公開》（2026-11-12）：<https://smhn.info/202611-stela-apple-silicon-macos-on-x86-pc>
