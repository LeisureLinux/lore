---
title: "Brush 0.5：Rust 写的 Bash 兼容 shell，跑通 96% 上游测试"
date: 2026-11-26
slug: brush-0-5-rust-bash-shell
category: 技术/解读
author: FreeLAMP.com
original_source: "Phoronix 报道（Michael Larabel，2026-11-26）＋ 一手核对 Brush GitHub 仓库与 crates.io 的 brush-shell/brush-parser 0.5.0 页面、官方 brush.sh 发布说明与安装文档。"
description: "解读 Rust 编写的 Bash/POSIX 兼容 shell Brush 0.5：通过超过 96% 的上游 bash-completion 测试套件，兼容性测试从上一版 2100 增到 3600+；多数 Bash 脚本不改就能跑。本轮改进含更可靠的管道与作业控制、组合 shell 特性处理、对现有工具（fzf/atuin/starship/zoxide/mise）的支持、交互式 shell 增强、预编译 Windows 二进制和性能提升。介绍其模块化 crate（brush-core/parser/builtins/interactive/shell）、读取 .bashrc 与可编程补全、测试体系（矩阵覆盖 Linux x86_64/aarch64/macOS 及多发行版容器）、可验证发布（签名 provenance + SHA-256），以及它和 uutils/coreutils、nushell 等 Rust 重写系统工具潮流的意义。"
published: true
---

11 月 26 日，Phoronix 报道：用 Rust 编写的 Bash/POSIX 兼容 shell **Brush** 发布了 0.5 版本——**通过超过 96% 的上游 bash-completion 测试套件**，大多数 Bash 脚本不用改就能在它上面跑。

## 一、0.5 的核心数字：从 2100 到 3600+ 测试

这一版最硬的指标是测试覆盖率：

- **超过 96%** 的上游 bash-completion 测试套件通过；
- 端到端兼容性测试从上一版的 **2,100 个增加到 3,600+ 个**。

按项目官方说明，这套兼容性测试的做法是：**同一段脚本分别在 brush 和 Bash 下运行，比较 stdout、stderr、退出码和文件系统副作用**。每个 PR 都会在 Linux（x86_64 和 aarch64）、macOS 上跑，还会进入 Arch Linux、Debian、Fedora、NixOS、openSUSE、Azure Linux 等容器里跑。

除了测试套件，还有"真实工具、真实测试"：端到端测试用 fzf、atuin、starship、zoxide、mise 这些大家常和 shell 搭配的工具来跑 brush。测试体系里还包括 CodeQL、依赖审计、每次 PR 的基准测试，以及解析器和高亮器的 fuzz 目标。

## 二、0.5 改了什么

这个版本是过去六个月的工作积累，主要改进：

- **更可靠的管道（pipelines）和作业控制（jobs）**——这是 shell 最容易出兼容性问题的地方；
- 更好地处理**组合的 shell 特性**（多种语法/选项一起用时），以及对现有工具更好的支持；
- **交互式 shell 增强**；
- **预编译的 Windows 二进制**首次提供（此前主要是 Linux/macOS）；
- 性能提升及其他一系列改动。

## 三、它怎么用：配置跟着走，补全照常工作

Brush 的定位是"**Bash-compatible. Embeddable. Extensible.**"——既能当日常 shell，也能被嵌入别的 Rust 程序。

作为日常 shell，它读取和 Bash 一样的启动文件：`.bashrc`、`.bash_profile`、别名、函数、`PS1`、`PROMPT_COMMAND`，以及 starship 这类提示符工具都照常工作；可编程补全会用你已装的 `bash-completion` 包，所以 git、docker、systemctl 的补全和以前一样。它还加了现代 shell 的小福利：基于历史的自动建议（默认开，由 reedline 驱动）和实时语法高亮（`brush --enable-highlighting` 或 TOML 配置里开）。

作为可嵌入组件，它拆成了几个 crate：

| crate | 作用 |
|-------|------|
| `brush-core` | 运行时：展开、执行、作业、补全与 Shell API，嵌入从这里开始 |
| `brush-parser` | Bash/POSIX 语法的 tokenizer 和 parser，可独立使用，带可选 serde AST |
| `brush-builtins` | 标准 builtins 集合 |
| `brush-interactive` | 基于 reedline 的行编辑、高亮、建议与补全 UI |
| `brush-shell` | 可执行文件和命令行，依赖以上全部 |

## 四、安装与"可验证发布"

安装方式有几种：

```
curl --proto '=https' --tlsv1.2 -fsSL brush.sh/install.sh | sh   # 官方脚本
brew install brush                                             # Homebrew
cargo install --locked brush-shell                             # 从 crates.io 编译
cargo binstall brush-shell                                     # 预编译二进制
```
（Arch、Fedora、MSYS2、Nix 等发行版也都有打包。）

值得称道的是它对**供应链安全**的处理：二进制由发布工作流构建、带签名的 build provenance；安装脚本会校验每个下载的 SHA-256，并在有 GitHub CLI 时检查 attestation。这在这个"包管理器投毒"频发的年代算是把这事儿做对了。

## 五、怎么定性：Rust 重写系统工具的又一块拼图

Brush 不是孤例。本号前面写过 uutils/coreutils 的差分测试、Rust 写的各种核心工具——用内存安全的语言重写 Unix 基础设施，正在从实验走向可用。shell 是这个清单里最难的一块：它不只是解析命令，还要精确复刻几十年积累的 bash 语义、陷阱和怪癖。

96% 的 bash-completion 通过率说明它已经跨过了"能玩玩"的门槛，多数日常脚本应该没有问题——但那 4% 和"多数脚本"的措辞也提醒我们：**如果你的生产流程依赖某些刁钻的 bash 行为，切换前先跑一遍自己的测试**。

它在 Windows 上提供预编译二进制这点也挺有意思：一个 Bash 兼容 shell，可能是 Windows 上想要 POSIX 脚本体验的人的又一个选择。

## 参考资料

- Phoronix 报道：https://www.phoronix.com/news/Brush-0.5-Released
- Brush GitHub 仓库：https://github.com/reubeno/brush
- v0.5.0 Release：https://github.com/reubeno/brush/releases/tag/brush-shell-v0.5.0
- crates.io brush-shell 0.5.0：https://crates.io/crates/brush-shell
- 官方站与安装说明：https://brush.sh/
