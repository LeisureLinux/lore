# rsync 3.5.0 发布公告

**发布日期**: 2026年8月13日

## 概述

rsync 3.5.0 在数月的开发后正式发布。本版本共修复 **33 个安全漏洞**，重点加固了路径处理和 daemon 协议，并附带了大量健壮性改进与回归测试。

## 主要变化

### 安全修复

- **链接跟踪 (CWE-59/61)**：本地用户可植入符号链接，令特权 rsync 误跟随，可能导致任意文件读取或通过 symlinked 输入进行传输塑形。已分配 CVE‑2026‑53802 (HIGH)。
- **过滤合并中的符号链接攻击**：rsync 可能跟随 `--filter` 合并文件（含 per‑directory merges 和 `-C` `.cvsignore`）中植入的符号链接。
- **Daemon 协议加固**：多项协议层面的漏洞被修复，并增加了鲁棒性硬化措施。

每个修复都随附一次在未修复树上会失败的回归测试，CVE 编号由 VulnCheck (CNA) 按照。

### 贡献者致谢

特别感谢以下人员加入 rsync 管理组，协助issue triage、开发新测试、审阅 PR 并制定“安全问题 vs 预期行为”的界线：

- Zen Dodd (Tao)
- Omar Elsayed (seks99x)
- Will Sargeant
- Paul Mackerras
- Aleksa Sarai
- Leonid Bugaev (buger)

 additionally, 感谢 Trail of Bits 的 **Filipe Casal** 通过 “Patch the Planet” 项目提供大量测试与安全报告。此外感谢 **Greg Kroah‑Hartman** 与 **Stuart Inglis** 的安全报告与测试工作。

### 其他改进

- 多项健壮性硬化，提升整体稳定性。
- 针对用户提交的大量 Bug Report 进行了跟进与致谢。

## 获取 rsync 3.5.0

官方发布源：[https://download.samba.org/pub/rsync/](https://download.samba.org/pub/rsync/)

