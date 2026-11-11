---
title: "GNU Automake 1.20：两个月内第二个版本，还把许可证换成了 GPLv3+"
date: 2026-11-11
slug: gnu-automake-1-20-jobserver-gplv3
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：GNU Automake 官方发布公告《automake 1.20 [stable]》（Kamila Szewczyk，2026-11-07 15:18 +0100，lists.gnu.org/archive/html/automake/2026-11/msg00004.html）全文，含 NEWS 完整变更列表、104 次提交 / 3 位贡献者、源码包大小与 SHA256/SHA3-256 ＋ 1.19.92 / 1.19.94 两个 alpha 公告（80 次提交 / 49 天）＋ GNU make 官方手册 Job Slots 章节（jobserver 协议、MAKEFLAGS --jobserver-auth、槽位归还规则）＋ GCC 官方 Optimize Options（-flto=jobserver 与父 Makefile 需 `+` 前缀）＋ FSF 许可证推荐页 ＋ Phoronix《Automake 1.20 Brings New Features》（Michael Larabel，2026-11-07）＋ 本站 2026-09-11 的 Automake 1.19 旧文"
original_date: 2026-11-07
original_url: "https://www.phoronix.com/news/GNU-Automake-1.20"
description: "本文以 GNU 官方 1.20 发布公告与 NEWS 全文为主，Phoronix 报道只作对照。核心事实：2026-11-07 发布的 1.20 距 1.19 仅 58 天、104 次提交（Kamila Szewczyk 99 / Karl Berry 4 / Paul Eggert 1），而 1.19 是 15 个月来的第一版且只有一个新功能；这次一次给了三个新功能（--enable-jobserver、delete-on-error、print-distfiles）、distcheck 默认不再跑 make dvi 因而不再需要 TeX、并把许可证从 GPLv2+ 升到 GPLv3+。官方明确说明：分发支持文件的既有例外保留，生成的 Makefile.in 许可不变，也不要求使用 Automake 的项目改用 GPL。--enable-jobserver 对应 bug#45756，让编译器与链接器继承 GNU make 的管道 jobserver（如 GCC -flto=jobserver），GNU make 手册要求工具解析 MAKEFLAGS 里的 --jobserver-auth 并在退出前归还槽位，GCC 文档要求父 Makefile 给命令加 `+` 前缀；dry-run/question/touch 模式仍不执行这些命令。delete-on-error 生成 .DELETE_ON_ERROR 特殊目标，避免 recipe 失败后留下被截断的目标被后续 make 当成最新；该选项对其他 make 实现无效。NEWS 里还有两条容易被忽略的供应链加固：configure 现在拒绝含 `< > ( )` 以及 `; |` 的 $srcdir 路径（可能被 shell 解释为重定向或语法），以及 dist-zstd 正确识别数字 ZSTD_CLEVEL、VPATH 构建里 lex/yacc 输出的 #line 路径、非递归 Vala 构建、uninstall 残留符号链接等长年问题。维护者在公告里写明目标是「让 GNU 构建系统重新成为新软件项目的首选」，Phoronix 评论称在 CMake/Meson 的采用速度下这是 stretch goal。本文的判断：这版真正的变化不是三个功能，而是发布节奏与维护意图从「维护模式」转向「主动追赶」，而 GPLv3+ 的主要意义是与 Autoconf 对齐、消除工具链内部许可证不一致。"
published: true
---

> 一手：GNU 官方 1.20 发布公告与 NEWS 全文、两个 alpha 预告、GNU make 与 GCC 官方文档
> 对照：Phoronix 报道、本站 9 月写的 1.19 旧文
>
> 媒体把重点放在「新功能 + GPLv3」，但公告里更有信息量的是节奏。

Phoronix 11 月 7 日报道了 GNU Automake 1.20，标题是「带来新功能，想重新确立 GNU 作为主流构建系统」，末尾加了一句：考虑 CMake 和 Meson 如今的采用速度，这会是个 stretch goal。

我去读了 GNU 官方发布公告和完整 NEWS，觉得这句话该放在一个更具体的背景里看：两个月前，1.19 还是「15 个月来的第一个版本、只有一个新功能」（本站 9 月写过，那版最出名的修复是一个 2012 年报的 `make dist-bzip2 dist-xz` bug）。而 1.20 距 1.19 只有 58 天、104 次提交，一次给了三个新功能，还换了许可证。维护者在公告里把意图写得很直白。

## 一、先看节奏：从维护模式到主动追赶

| | 1.19（2026-09-10） | 1.20（2026-11-07） |
|---|---|---|
| 距上一版 | 15 个月 | 58 天 |
| 提交数 / 贡献者 | 一年多的修复 | 104 次 / 3 人（Szewczyk 99、Karl Berry 4、Paul Eggert 1） |
| 新功能 | 1 个（`AM_OPTIONAL_AUTOMAKE`） | 3 个 |
| 预发布 | — | 1.19.92（49 天 80 提交）、1.19.94 两个 alpha |
| 许可证 | GPLv2+ | GPLv3+ |

alpha 阶段还有一条实测反馈：Fedora rawhide 上用 1.19.92 重建了 1294 个依赖 Automake 的包，无失败报告。这说明这版不是仓促发出来的。

维护者 Kamila Szewczyk 的原话：

> 我对整个 GNU 构建系统（autotools）有相当多的计划……我的最终目标是让它重新成为新软件项目的首选构建系统，同时继续简化存量用户的维护与可移植性。

Phoronix 那句 stretch goal 是对这个目标的评价，不是对三个功能的评价。把两者分开读，才不会误判这版的性质。

## 二、三个新功能，各自补的是什么坑

① `--enable-jobserver`（bug#45756）。 让编译器和链接器继承 GNU make 的管道 jobserver，典型用途是 GCC 的 `-flto=jobserver`。

这件事的机制比「加个编译选项」复杂。GNU make 手册的 Job Slots 章节写明：`make` 通过 `MAKEFLAGS` 环境变量把 jobserver 信息传给子进程，工具要解析其中 `--jobserver-auth=`；每条命令启动时已经隐式占了一个槽位，工具额外拿到的槽位必须在退出前如数归还（出错也要还），否则顶层 make 会在构建结束时报错。GCC 文档补充：`-flto=jobserver` 要求父 Makefile 给对应 recipe 加 `+` 前缀，且基本只在 `MAKE` 是 GNU make 时有效。

换句话说，Automake 这个选项解决的是「并行度预算怎么穿过 `make → gcc → lto1` 这一整条链」的问题 —— 没有它，LTO 并行线程数容易和 make 的 `-j` 各算各的，整机构建超订。公告也注明 dry-run、question、touch 三种模式仍不执行这些命令。

② `delete-on-error`。 生成的 `Makefile.in` 里会带 `.DELETE_ON_ERROR` 特殊目标，让 GNU make 在 recipe 失败且已改动目标时删掉目标。官方给的例子很实在：

```
foo.h: gen.sh; ./gen.sh > $@
```

如果 `gen.sh` 中途失败，重定向已经创建了一个残缺的 `foo.h`；不删掉它，下次 `make` 会认为这个头是最新的，直接拿半个文件继续编。这属于「让失败如实地失败」，和 1.19 修的「`make dist` 遇 tar 失败却报成功、产出截断归档」是同一类问题 —— 本站 9 月那篇就特别标过这一点。公告也如实提醒：其它 make 实现不支持 `.DELETE_ON_ERROR`，该选项对它们无效。

③ `print-distfiles`。 列出 `make dist` 会分发哪些文件，属于发布归档的可检查性。配合 NEWS 里另两条（`dist-zstd` 现在正确识别数字 `ZSTD_CLEVEL`、不再把它当输入文件名；`distcheck` 现在会检出 uninstall 之后残留的符号链接，含悬空链接），方向都是「发布包到底装了什么、卸完还剩什么」要能被验证。

顺带一个减负：`distcheck` 默认不再跑 `make dvi`，于是检查含 Texinfo 手册的发行包不再需要 TeX（bug#79053）。需要检查文档构建的项目，可用 `AM_DISTCHECK_DVI_TARGET` 显式设成 `dvi` / `pdf` / `html`。

## 三、GPLv3+：换了什么，没换什么

公告写得很清楚，这部分最容易被标题党带偏：

- Automake 本体从 GPLv2 或更新 改为 GPLv3 或更新，与 Autoconf 对齐，并遵循 FSF 的许可证推荐；
- 分发支持文件的既有例外继续保留；
- 生成的 `Makefile.in` 的许可不变；
- 不要求使用 Automake 的项目采用 GPL。

Phoronix 把这说成「与 Autoconf 和 FSF 推荐对齐」，是对的。但真正值得注意的是它没说的那半句：这次变更是工具链内部的一致性整理，不是给下游项目加义务。GPLv2 → GPLv3 对 Automake 这种「生成代码的工具」格外敏感，所以公告才专门列了三条「不变」。如果只写「Automake 换 GPLv3」，很容易让维护者误以为自己项目的许可证要跟着改。

对本仓库这类用 Automake 的存量项目，实际影响是：升级工具版本时不需要重审产品许可证，但打包脚本里若把 Automake 自身文件一并再分发，得按新的 GPLv3+ 处理。

## 四、NEWS 里两条容易被漏掉的加固

完整 NEWS 比媒体报道长得多，其中两条有供应链意味：

- `$srcdir` 路径字符过滤。 `configure` 现在拒绝含 `<` `>` `(` `)` 的源码目录路径 —— 这些字符在编译器命令里可能被当成 shell 重定向或语法，潜在后果是覆写构建目录里的文件；对 `;` `|` 也报「不安全的源码目录取值」（此前对 `$` `&` 已如此）。这些字符在 `$srcdir` 为 `.` 时仍被接受。
- VPATH / lex-yacc / Vala 的老问题。 从 VPATH 构建分发的 lex/yacc 输出不再带指向构建期 srcdir 的 `#line` 指令（如 `../src/parse.y`），改为指向旁边的源文件（bug#39666）；lex/yacc 规则先建输出目录，修好 out-of-tree + `subdir-objects` + `--disable-dependency-tracking` 的组合（bug#27188）；非递归 Vala 构建现在能通过 distcheck（bug#76527）。另有重叠 Automake 条件里的重复目标声明不再产生伪重定义警告（bug#13940）、`LIBADD`/`LDADD` 里对其它目标对象的依赖跟踪不再受处理顺序影响（bug#60508）。

一份「minor release」的 NEWS 里塞进这么多带 bug 编号的历史遗留项，和 1.19 那「攒了一年多、修一个 14 年 bug」的画风确实不同。这比三个新功能更能说明维护意图变了。

## 五、事实边界

- 本文以 GNU 官方 `automake 1.20 [stable]` 公告（2026-11-07 15:18 +0100）与其附带 NEWS 为准；Phoronix 报道仅作对照。公告给出的源码包为 `automake-1.20.tar.gz` 2,549,281 字节 / `.tar.xz` 1,694,140 字节，并附 SHA256、SHA3-256 与 GPG 签名指纹，本文未下载校验。
- 104 次提交 / 3 位贡献者、58 天间隔，以及 1.19.92 的 80 次提交 / 49 天，均取自官方公告与 alpha 预告；Fedora rawhide 1294 次重建无失败为测试者邮件反馈，非官方基准。
- jobserver 协议细节取自 GNU make 手册 Job Slots 章节，`-flto=jobserver` 的 `+` 前缀要求取自 GCC 官方 Optimize Options；本文未在本机构建 LTO 项目验证 `--enable-jobserver`。
- 「CMake / Meson 采用速度」为 Phoronix 的评论，本文未提供市场份额数据；「重新成为首选」是维护者自述目标，不是已达成的结论。
- 1.19 的对照数据取自本站 2026-09-11 旧文与 Phoronix 1.19 报道。

## 六、结论

这版真正的变化落在发布节奏与维护意图上：15 个月一版、只加一个便利功能的节奏，在 58 天里变成了 104 次提交、两个 alpha、三个功能、一批长年 bug 和一次许可证对齐，再配上一句「重新成为新项目的首选」。

至于能不能追上 CMake / Meson，公告里那句「slowly dragging it into the future」其实已经给了答案的尺度：这是把老工具的可信度一点点补回来，不是靠一次发版翻盘。对存量用户，最该立刻用上的大概是 `delete-on-error` 和 `print-distfiles` —— 它们治的是「构建看起来成功了」这类最不容易被发现的问题。

## Sources

- GNU 官方发布公告《automake 1.20 [stable]》（含完整 NEWS，2026-11-07）：<https://lists.gnu.org/archive/html/automake/2026-11/msg00004.html>
- 1.19.92 alpha 公告与 Fedora 测试反馈：<https://lists.gnu.org/archive/html/automake/2026-11/msg00002.html>
- Phoronix《Automake 1.20 Brings New Features》（Michael Larabel，2026-11-07）：<https://www.phoronix.com/news/GNU-Automake-1.20>
- GNU make 手册 Job Slots：<https://www.gnu.org/software/make/manual/html_node/Job-Slots.html>
- GCC Optimize Options（`-flto=jobserver`）：<https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html>
- 本站旧文《GNU Automake 1.19 发布》：<https://freelamp.com/articles/2026-09-11_automake-1.19-released/>
