---
title: "Rust 版 coreutils 兼容性：Behave 拿 GNU 当基准撞出几十个缺陷"
date: 2026-11-24
slug: behave-differential-testing-uutils-coreutils
category: 技术/解读
author: FreeLAMP.com
original_source: "GitHub emirmrkaljevic/behave README 与 upstream-findings 清单（MIT，2026-10-13 建库，持续更新）＋ Emir Mrkaljević 的 Rust 用户论坛帖《Behave: black-box differential tests for CLI rewrites》（2026-11-13：40 个上游 bug 报告 / 47 个修复 PR / 33 个已合并）＋ 其 DEV 系列文章（10-14 / 11-06 / 11-09 / 11-10）＋ uutils/coreutils README 与 0.12.0/0.13.0 发布说明＋ Ubuntu Discourse 26.04 rust-coreutils 状态更新＋ 本号 2026-09-14 Ubuntu 26.10 文章交叉核对。"
description: "解读 Emir Mrkaljević 开源工具 Behave：它把 GNU coreutils 当黄金基准，从 --help/man 自动生成覆盖标志、标志对、取值边界、stdin、缺文件、尾斜杠路径等用例，记录 stdout/stderr/退出码为 YAML spec，再逐字节重放到 uutils 实现上找差异。澄清几处常见误传：Behave 是 Go 写的（不是 Rust），主要比对 stdout/stderr/退出码（不是完整文件系统副作用 diff），缺陷数随进度变化（11-13 口径为 40 报告/47 PR/33 合并）。梳理真实案例（cp f/、mv -n z z、sort --check --merge、seq -inf）、方法论要点（锁定 GNU 9.12 基准、每个用例跑 3 次标 flaky、normalizer、CI/JUnit、MCP server）与对「AI 重写基础设施」的启示。"
published: true
---

Ubuntu 26.10 把 `cp`、`mv`、`rm` 也换成了 Rust 版 uutils——这是本号 9 月份写过的《Ubuntu 26.10 完成 coreutils 的 Rust 化》的后续。当时留下的那个问题现在摆到了桌面上：重写后的 Rust 工具，面对成千上万种诡异参数与边缘输入，行为能和原版 C 代码 100% 一致吗？

Emir Mrkaljević 给出的答案是：**别靠猜，把 GNU 当 Oracle 对撞**。他开源的工具 Behave 用自动化黑盒差分测试，在 uutils 上撞出了一长串真实的上游缺陷。不过在展开之前，先纠正几处流传很广的误传——原始材料比二手转述更精确，也更有意思。

## 一、先澄清：Behave 是 Go 写的，比对的是「三件套」

你看到的一些介绍会说「开发者用 Rust 编写了 Behave」——**不对**。Behave 本身是一个 **Go 编写的单文件 CLI（外加 MCP server）**，MIT 许可证。用 Go 只是因为它是单二进制、好分发；它对被测双方用什么语言完全不挑——GNU 那侧是 C，uutils 那侧是 Rust，它一视同仁当成黑盒。

还有一处夸张：说它比对「文件系统副作用」。准确的说法是：Behave 在**每次运行前创建全新的临时目录、固定环境变量**，记录的是每个用例的 **stdout、stderr 和退出码**，存成一条条 YAML 规格。它确实会准备文件参数（缺文件、尾斜杠、破损符号链接那类），也确实会把整个进程的运行过程放进受控环境；但核心比对是「三种输出」，不是对两个文件树做逐字节 diff。理解这一点，才知道它的边界在哪。

## 二、Behave 怎么工作：从 --help 自动生成用例，然后重放

它的流程是三步，很像给 CLI 做「录音—回放」：

```bash
behave probe sort        # 录：读 --help / man，生成几百个用例，记录 GNU sort 的真实行为
behave run behave-sort   # 验证：同一份 spec 在 GNU 上回放是否稳定
behave diff behave-sort --impl ./target/release/sort   # 对撞：把同一批用例喂给 Rust 版
```

**`probe`** 读 `--help` 和 man page，枚举：每个标志单独、标志两两组合、帮助里列出的每个枚举值、边界值（`0`、`-1`、`abc`、空值、缺失值）、stdin 样本（空、Unicode、CRLF、5000 字符长行、无结尾换行）、把这些样本当文件参数、未知标志、不存在的文件。

**确定性**是这套东西能用的前提：每个用例**跑三遍**，结果不一致的（比如 `sort --random-sort`）自动标成 `flaky` 跳过；比较前还会跑 normalizer，抹掉程序名、临时路径、时间戳、ANSI 颜色、十六进制地址、PID、耗时这些噪声，也支持在 `behave.yaml` 里写自己的正则规则。超时会杀掉整个进程组。

**spec 就是可提交、可 review 的 YAML 目录**，一个用例一个文件，比如那个著名的 `0135-flag-output-delimiter-value-1-arg-f1.yaml`。`run` / `diff` 在失败时返回非 0，能直接塞进 CI；`--junit` 出报告；`coverage` 会告诉你「27 个用例只覆盖了 12 个文档标志里的 7 个」，低于阈值就挂。还有 `behave mcp`，把 `behave_exec` / `behave_probe` / `behave_add_case` / `behave_diff` 等能力通过 MCP 暴露给编码助手——改一行代码就让 agent 回放一遍规格，而不是靠它「觉得应该没问题」。

## 三、撞出了什么：从「错误消息少个文件名」到静默数据丢失

原始材料里的数字是流动的，得说清口径：截至 **2026-11-13** 作者在 Rust 用户论坛的帖子是 **40 个上游 bug 报告、47 个修复 PR、33 个已合并**；仓库 README 较早的快照（11-06）是 30/37/21。所以「40 个」是报告数，不是同时存在的未修 bug 数——大部分已经修了。

用例的价值在于它们都是「没人会手写测试去覆盖」的角落：

**尾斜杠探测**（v0.1.7 加的：把一个普通文件写成 `f/` 传进去）几乎每次都能挖出点什么：
- `cp f/ dest` 打 `Not a directory (os error 20)`，GNU 是 `cannot stat 'f/': Not a directory`（#15691）；
- `mv a missing/b` 只打裸 OS 错误，GNU 会说 `cannot move 'a' to 'missing/b': ...`（#15721）；
- `ln f/ link` 把错归到链接名上，而不是来源（#15713）。

**退出码与模式优先级**：
- `sort --check --merge` 时 uutils 让 `--merge` 赢了，GNU 是 `--check` 赢（#15380）——不崩，只是悄悄跑错模式；
- `sort` 用法错误退出 1 而不是 GNU 的 2（脚本里 `if [ $? -eq 2 ]` 就会踩）；
- 裸 `tail -c` 和 obsolete `tail +NUM` 不认 `_POSIX2_VERSION`（#15528）。

**选项值以 `-` 开头**：`cut --output-delimiter -1 -f1`、`tac -s -1`、`xargs -a -foo` 全被当成新标志；GNU 会把它们当该选项的值。这是最典型的一类「happy path 全对、边角全错」。

**静默行为差异**（比崩溃更危险）：
- `mv -n z z`：GNU 因为本来就不覆盖，直接跳过并退出 0；uutils 报 `'z' and 'z' are the same file` 然后失败（#15824）；
- `base64 -d` 遇到非法输入，GNU 把出错前解出的字节照常输出，uutils 什么都不打；
- `sort -c dir` 直接退出 0 且无提示，而不是报告读错误（#15615）——脚本会以为校验通过；
- `seq -inf 1` 把看起来像选项的参数当数字，导致无限打印 `-inf`（#16114）。

**一个数字陷阱**：`tail` 把不存在的文件名 `007` 打印成 `7`（#15533）。同一个 bug 后来在 `tac`、`nl`、`md5sum`、`cksum`、`sort`、`shred` 里被逐个发现、逐个修——这就是「差分测试发现的边界问题，往往不是一处而是整类」。

同一套方法推广到 uutils 的其它重写也有效：findutils 的 `xargs -I` 默认命令打印输入项（GNU 打空行）、procps 的 `sysctl -o kernel.ostype` 吞掉键名、`pmap -XX` 被当成重复 `-X`——都是几行代码能修、但手写测试不会想到的事。

## 四、方法论：为什么单元测试守不住这种兼容

这件事的核心不是「Rust 不行」或「C 永远对」，而是**测试策略的差别**。

作者在他的系列文章里总结了几条很实在的经验：

1. **锁定参考版本**。GNU 9.7 和 9.12 的 `tail -v` 头部引号都不一样；拿系统里随便一个 coreutils 当基准，得到的差异是 GNU 自己的版本变化，不是重写 bug。spec 里要记下 `--version` 行，跑的时候并排显示。
2. **让 probe 遍历帮助文本**。枚举值、标志对、废弃写法，正是优先级 bug 的藏身处——手工测试只会测「正常用法」。
3. **断言 stderr 的形状，不只是退出码**。`cannot move 'a' to 'b'` 这样的上下文词是**用户可见的 API**，脚本和日志都会依赖它。
4. **报 bug 时带上失败用例**。上游维护者看到「PR 不打补丁就挂、打了就过」时，动作会快很多——这 47 个 PR 里的绝大多数都是几行代码加一个测试。
5. **保持数字诚实**。作者在 README 里反复更新计数，因为报告数、PR 数、合并数一直在变。「40 个 bug」是某个时间点的快照，不是永恒事实。

还有一个容易被忽略的点：uutils 自己的项目目标就写着「**与 GNU 的差异视为 bug**」「精确匹配 stdout、退出码」。也就是说，这不是「Rust 重写要不要完美兼容」的争论——项目自己就是这么定义的，而 Behave 是把这个目标变成可执行验证的那块拼图。

## 五、对「用 AI / 现代语言重写基础设施」的启示

这半年本号写的安全事件里，有一类 recurring pattern：Xen 的性能优化在十一年后被推翻，APT 的下载代码因复杂度被砍功能，Ruby 的 ß 在标准库里躺了九年——老代码里的假设，被新的审计方式逐个翻出来。Behave 讲的是硬币的另一面：**当你主动重写时，怎么证明新东西没丢掉老东西那些「没人记得、但有人依赖」的行为**。

常规单元测试回答的是「作者想到的情况对不对」；差分测试回答的是「原版做过的每一件事，新版是否也做了」。后者才是 drop-in replacement 这个承诺的验证方式。而对 AI 参与生成的代码，这一点只会更重要——AI 特别擅长写出「看起来对」的实现，恰恰是那些退出码 1 vs 2、文件名 `007` vs `7`、错误消息少个上下文词的差异，最容易被「看起来对」掩盖。

当然，差分测试也有边界：它只能覆盖能枚举的输入空间；参考实现自身的怪癖会被原样继承（GNU 的某些行为本身可能是 bug）；版本漂移需要持续维护基准。但它守住的是底线——**在你敢把 `rm` 换成另一个实现之前，至少知道有哪些地方不一样**。

从 Ubuntu 25.10 默认换掉大部分工具、26.04 因 TOCTOU 留下 cp/mv/rm、到 26.10 全部切换，再到 Behave 这类工具把兼容性差异逐个变成 PR——这条链挺完整：审计发现安全问题，移植补上安全问题，差分测试补上行为兼容。三层加在一起，才让「100% Rust coreutils」从口号变成一件可以讨论的事。

## 参考资料

- Behave 仓库（README、upstream-findings、examples、MCP 说明）：https://github.com/emirmrkaljevic/behave
- Rust 用户论坛发布帖（2026-11-13，40 报告 / 47 PR / 33 合并口径）：https://users.rust-lang.org/t/behave-black-box-differential-tests-for-cli-rewrites-found-40-bugs-in-uutils/143662
- DEV 系列：首篇差分测试 https://dev.to/emirmrkaljevic/i-diffed-gnu-coreutils-against-its-rust-rewrite-with-auto-generated-tests-2ocl ；错误消息专题 https://dev.to/emirmrkaljevic/the-error-messages-a-rust-rewrite-got-subtly-wrong-what-a-black-box-probe-found-in-uutils-coreutils-2hlo ；27 个合并 PR 的经验 https://dev.to/emirmrkaljevic/what-27-merged-prs-taught-me-about-testing-a-rust-rewrite-as-a-black-box-4je4
- uutils/coreutils 仓库（项目目标、Ubuntu 默认状态）：https://github.com/uutils/coreutils
- uutils 0.12.0 / 0.13.0 发布说明：https://github.com/uutils/coreutils/releases
- Ubuntu Discourse《An update on rust-coreutils》（Zellic 审计与 26.10 计划）：https://discourse.ubuntu.com/t/an-update-on-rust-coreutils/80773
- 本号前序文章：《Ubuntu 26.10 完成 coreutils 的 Rust 化》
