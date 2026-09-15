# Ubuntu 26.10 完成 coreutils 的 Rust 化：你天天敲的 ls/cp/rm 底层换引擎了

> 原文：[Ubuntu 26.10 completes transition to Rust-based coreutils](https://www.omgubuntu.co.uk/2026/09/ubuntu-2610-rust-coreutils-complete)（OMG! Ubuntu，作者 Joey Sneddon，2026-09-13 发布、约 18 小时后更新）。本文由 LeisureLinux 翻译整理并加注解读；文内命令名、数字与引语均来自原报道。

**Ubuntu 26.10 完成了发行版向 Rust 版核心工具的迁移——此前因安全问题被暂缓的几个命令，现在也换成了内存安全的版本。**

`cp`、`mv` 和 `rm` 在 Ubuntu 26.04 LTS 上被留在 GNU 版本，原因是 `uutils`（Rust 版 coreutils）里有一批 **TOCTOU（time-of-check to time-of-use，检查到使用之间的竞态）** 漏洞需要先修掉。这些漏洞在上游修复之后，Ubuntu 26.10 把剩下的活干完了。代号"**Stonking Stingray**"的这个版本，随附一整套 Rust 核心工具，涵盖 `ls`、`cat`、`chmod`、`du` 这些日常命令。

> Canonical 每年捐 €40k，资助 Rust 软件的开发。

Canonical 的工程师从 **2025 年**开始"氧化（oxidising）"这个发行版——用 Rust 替代品替换基础软件。他们看中的是安全收益：Rust 在**编译期**就能抓住内存 bug，而 C 编译器做不到。Ubuntu 25.10 是第一个默认搭载 Rust 工具的版本，并且把 **Rust 版 sudo（sudo-rs）设为默认**。

迁移并非一路顺滑，但 Canonical 做得很细致。在 26.04 之前，他们委托第三方对 `uutils` 做了一次**安全审计**（由 Zellic 执行），正是那次审计发现了让以上三个命令暂留 GNU 版本的问题。

Canonical 还是 **Trifecta Tech Foundation** 的白金赞助方，每年出资 €40,000 资助其 Rust 软件工作。这家非营利基金会正在用 Rust **重写网络时间协议（NTP）**，而 Ubuntu 计划到 **27.10** 把它作为默认的时间同步客户端。

这里要强调：coreutils 迁移的完成对终端用户**几乎没有功能差异**。Rust 版 `uutils` 的目标是**无缝兼容** GNU 版本，把任何偏离都当作 bug 来修——这是设计使然，重点在于安全性提升，而非换体验。

Ubuntu 26.10「Stonking Stingray」的 beta 将于本月晚些时候到来，**稳定版在 2026 年 10 月 15 日**发布。

---

## 解读：为什么这件事和上一篇 coreutils 手册直接有关

上一篇我们刚把 GNU coreutils 的 **105 个命令**逐个拆了一遍——那套命令的 C 实现，是过去 30 多年 Linux 的事实标准。现在 Ubuntu 正在把它整批替换成 Rust 实现（项目代号 **uutils**，也叫 `coreutils-rs`）。几个值得工程师注意的点：

**1. 被"暂缓"的 cp/mv/rm，暴露的是同一类老问题：TOCTOU。**
原报道提到的 TOCTOU（检查到使用之间的竞态），经典场景就是 `cp`/`mv`/`rm` 这类"先 stat 判断、再操作"的命令：攻击者可以在你 `stat` 之后、`open` 之前，把目标替换成别的东西（比如一个符号链接），从而越权或破坏。C 语言里处理这类竞态要靠 `O_NOFOLLOW`、`fstat` 而非 `stat`、或用 `openat` 等一整套纪律；稍有不慎就是漏洞。Rust 版重写把这类问题在更底层用类型与 API 约束收口——这正是 Canonical 愿意砸钱的根本原因。

**2. "drop-in 兼容"是硬指标，不是口号。**
uutils 把"与 GNU 行为有任何偏离都当 bug"作为设计原则。这对我们上一篇手册里写的那些示例意味着：**你照着 GNU man 手册敲的命令，在 Ubuntu 26.10 上行为应该一致**。但保险起见——如果你写的是跨发行版的脚本，在 Ubuntu 26.10 上跑之前，最好确认 `ls -lhtS`、`join -o 0,1.2,2.2`、`numfmt --to=iec` 这类带 GNU 扩展参数的用法，uutils 是否真的都覆盖了（uutils 的 GNU 兼容性已相当高，但长尾选项偶有差异）。

**3. 更大的图景：从 sudo-rs 到 NTP，基础软件正被逐个"氧化"。**
sudo-rs 在 25.10 已成默认，coreutils 在 26.10 收尾，NTP 重写要在 27.10 接班。Canonical 每年 €40k 赞助 Trifecta Tech Foundation，本质是在给"内存安全的 Linux 基础层"下注。对内核/系统工程师来说，信号很明确：**未来几年，你工作环境里越来越多底层工具会是 Rust 写的**，而它们的 CLI 表面不变，变的是出内存越界/竞态类 CVE 的概率。

**4. 一个清醒的提醒。**
Rust 消除的是内存安全类 bug，不消除逻辑 bug、不消除配置错误、也不消除 TOCTOU 之外的新攻击面。迁移是安全上的净增益，但不该被解读成"换 Rust 就安全了"。

---

## 关键事实速查

| 项目 | 内容 |
|------|------|
| 版本 | Ubuntu 26.10「Stonking Stingray」 |
| 动作 | 完成 coreutils 的 Rust（uutils）化 |
| 此前暂缓的命令 | `cp`、`mv`、`rm`（因 uutils 的 TOCTOU 漏洞） |
| 起点 | Canonical 2025 年起"氧化"发行版 |
| 默认 Rust 化里程碑 | 25.10 首搭载，sudo-rs 成默认 |
| 安全审计 | 26.04 前委托 Zellic 审计 uutils |
| 赞助 | €40k/年 给 Trifecta Tech Foundation |
| 后续 | NTP 的 Rust 重写计划 27.10 成默认 |
| 时间表 | beta 本月内；稳定版 2026-10-15 |

---

> 如果你在 Ubuntu 26.10 beta 上跑我们上一篇那 105 个命令的示例时撞到行为差异，欢迎留言——这些边角案例，正是 GNU 与 uutils 兼容性最值得记录的地方。
