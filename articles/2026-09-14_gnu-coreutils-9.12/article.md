# GNU coreutils 9.12 发布：修了一个折磨人多年的 -R 竞态，uname 多了结构化输出

> 原文：[GNU Coreutils 9.12 Released With Performance Optimizations, New uname Option](https://www.phoronix.com/news/GNU-Coreutils-9.12)（Phoronix，作者 Michael Larabel，2026-09-14 13:45 EDT 发布）。本文由 LeisureLinux 翻译整理并加注解读；关键变更已对照 coreutils 上游 NEWS 文件核对。文中命令与版本号均来自原报道与上游发行说明。

GNU coreutils 9.12 今天发布，带来一批修复、若干新选项，以及对这套最常用系统工具的性能改进。对我们刚拆完的**那 105 个命令**而言，这是发布周期里一次值得记一笔的小版本。

---

## 译文：Phoronix 报道要点

**首先，9.12 修掉了一个"老毛病"。**
以往当你用递归 `-R` 遍历目录层级时，如果遍历过程中有文件被**并行删除**，`chcon`、`chgrp`、`chmod`、`chown`、`du` 和 `ls` 会直接失败。这个存在已久的 bug，在 9.12 里被修好了。

**其次，`stat` 和 `tail` 支持了两种新的文件系统类型。**
9.12 中，`stat` 和 `tail` 新增了对 **FailFS 和 NULLFS** 文件系统类型的支持（对照上游 NEWS：`stat -f -c%T` 现在能报告该文件系统类型，`tail -f` 也会对 nullfs 走 inotify）。

**`uname` 多了 `-A` / `--all-labeled` 选项。**
新选项会把所有输出**逐项打标签、每行一项**——比起 `uname -a` 那行用空格捏在一起的结果，机器解析友好得多。

**其他修复。**
包括避免 `factor` 一处可能的缓冲区越读（buffer over-read），以及若干 Solaris 特有的 bug。9.12 可在 GNU.org 获取。

---

## 解读：四个工程师该知道的点

**1. 那个 `-R` 并行删除的修复，是日常最容易撞上的。**
想想场景：你在一个活跃目录上跑 `chmod -R` 或 `du -sh`，同时 CI、日志轮转或别的进程在往下删文件。旧版 coreutils 在 `stat` 之后、`fchmodat`/`openat` 之前发现目标没了，就 abort 整个遍历。这不是理论问题——容器构建、日志清理并发的目录上经常触发。9.12 让递归遍历对"途中消失的条目"变得健壮，这正是运维脚本最该升级的理由。

**2. `uname -A` 是为自动化而生的。**
`uname -a` 的输出是 `Linux host 7.2.4-x64v3-xanmod1 ...` 这样一行挤在一起，脚本里多半要靠 `awk` 切字段、还容易因顺序变化翻车。`--all-labeled` 把内核名、节点名、release、version、machine 等**逐项带标签、每行一条**，直接 `grep`/`cut` 即可，可移植性强太多。如果你写过"按内核版本分流"的初始化脚本，这个值得替换掉老写法。

**3. 性能主题仍在延续——但别把 9.11 的数字算到 9.12 头上。**
Phoronix 标题写了"performance optimizations"，具体的大数字其实落在 9.11（2026-04-20）：`cat` 在 Linux 上走零拷贝 I/O，Power10 上吞吐从 12.9 GiB/s 提到 81.8 GiB/s（约 6×）；`wc` 单次最小读取从 16 KiB 提到 256 KiB，缓存文件下 `wc -l` 约快 10%；`cut` 新增 `-w/--whitespace-delimited`、`-O`、`-F` 几个选项以兼容 BSD/macOS。9.12 是在这条"更稳更快"主线上继续补丁。顺带一个值得注意的行为变更：`cksum`/`md5sum`/`sha*sum` 不再通过 configure 的 `--with-linux-crypto` 走 Linux AF_ALG 内核加密 API——该 API 将在 Linux 7.2 废弃，且实测不如 OpenSSL 快。

**4. 和上一篇 Ubuntu Rust coreutils 形成对照。**
我们刚聊过 Ubuntu 26.10 把 coreutils 换成 Rust 实现（uutils）。有意思的是，uutils 0.11.0 的发行说明里**同样列了 `uname -A/--all-labeled` 作为"GNU 兼容"新增选项**——说明 Rust 版在紧跟 GNU 的语义。你在 Ubuntu 26.10 上敲 `uname -A`，得到的应该和 9.12 的 GNU 版一致。两套实现在同一选项上收敛，正是"drop-in 兼容"被当硬指标的结果。

---

## 关键变更速查

| 类别 | 内容 |
|------|------|
| 修复（重要） | `chcon/chgrp/chmod/chown/du/ls` 递归 `-R` 遍历时遇并行删除不再失败 |
| 新文件系统支持 | `stat`/`tail` 支持 FailFS、NULLFS（`tail -f` 走 inotify） |
| `uname` 新选项 | `-A` / `--all-labeled`：逐项打标签、每行一项 |
| 其他修复 | `factor` 缓冲区越读；Solaris 特有 bug |
| 上游背景 | 9.11 已落地 `cat` 零拷贝（约 6×）、`wc` 大块读（约 10%）、`cut` 新选项 |
| 行为变更 | 移除 `--with-linux-crypto`（AF_ALG 将废弃，慢于 OpenSSL） |

---

> 如果你在升级到 9.12 后，发现 `chmod -R` 在某些并发目录上的行为和老版本不同——那不是回归，是它终于不再因为"文件中途消失"而 abort 了。欢迎留言说说你踩过的相关坑。
