---
title: "GDB 18.1 发布：Windows 原生目标大改、新增 MicroBlaze/AArch64 MinGW 目标、Python API 扩充"
date: 2026-09-26
slug: gdb-18-1-released
tags: [GDB, 调试器, Windows原生目标, AArch64 MinGW, Python API, CTF移除, 译文]
category: 开源/工具
author: FreeLAMP.com
original_source: "LWN.net"
original_author: "Andrew Burgess (GDB 公告)"
original_date: 2026-09-26
original_url: "https://lwn.net/Articles/1096897/"
description: "GDB 18.1 发布：Windows 原生目标获得 non-stop 模式/调度锁/TFLS/真彩支持，新增 GNU/Linux MicroBlaze 与 AArch64 MinGW 目标，Python API 大幅扩充，并移除 stabs/mdebug/CTF 等旧格式。"
published: true
---

> 原文：[GDB 18.1 released](https://lwn.net/Articles/1096897/)（LWN.net，2026-09-26，Andrew Burgess 发布的 GDB 公告）。本文为**译文 + 解读**，完整变更见 [gdb/NEWS](https://sourceware.org/git/gitweb.cgi?p=binutils-gdb.git;a=blob_plain;f=gdb/NEWS;hb=gdb-18.1-release)。

## 一句话结论

GDB 18.1（GNU 调试器）发布，面向 Ada/C/C++/Fortran/Go/Rust 等语言、可调试十几种架构。本期亮点：**Windows 原生目标获得大幅增强**（non-stop 模式、调度锁、线程局部存储、真彩与 UTF-8）、**新增两个目标**（GNU/Linux/MicroBlaze、AArch64 MinGW）、**Python API 大量扩充**，并**移除 stabs/mdebug/CTF 等旧调试格式**。

## 主要变更

**1. Windows 原生目标重大改进**
- 支持 **non-stop 模式**（需 Windows 10+）。
- **调度锁（`set scheduler-locking on`）** 现在可用。
- 支持**原生线程局部存储（TLS）** 变量。
- Windows Terminal 控制台下支持 **24 位真彩色**，在输出代码页为 65001 时支持 emoji 样式与 UTF-8 文本（host charset 自动设为 UTF-8）。
- 文件名**统一用正斜杠**展示（如 `C:/proj/src/main.c`），影响所有解释器（CLI/TUI/MI/DAP）。
- 适用所有解释器与 GDB 展示文件/目录名的地方。

**2. 索引与参数处理**
- 现在把**所有类型符号**写入 `.gdb_index` 段（修复依赖索引时找不到类型的问题；已有索引应重建）。
- 改进 inferior 参数处理：`set args`/`run`/`start`/`starti` 现在接受含换行符的引用参数；新增 `--no-escape-args`（gdbserver 同效）；连接支持 `qExecAndArgs` 包的远端时会把参数复制进自身 `args`。
- 连接 extended-remote 时，若远端未带可执行文件且用户未显式指定，可自动设置 `remote exec-file`。
- `add-inferior`/`clone-inferior`/MI `-add-inferior` 在连接不可共享时（如 core 文件、Windows 原生目标）会**警告并创建无连接的新 inferior**（此前会崩）。

**3. 新命令与能力**
- `info locals` 现在对**被遮蔽**的变量标注 `shadowed` 及位置信息。
- AArch64 支持 **FPMR（浮点模式寄存器）**。
- 支持 libipt v2.2 在 **FRED 系统**上源自 Event Tracing 的事件（以及 Trigger Tracing）。
- 支持任意（非标准）波特率（glibc 2.42+ 等接受的系统）。
- 新增 **`essential` 帮助命令类**，列出接近最小集的新手命令。
- 若干 `set/show` 与环境/历史/进度条/skip 相关的新命令（如 `local-environment`、`save history`、`save skip`、`save user`、`info proc environ`、`progress-bars enabled` 等）。

**4. 新目标**
- **GNU/Linux/MicroBlaze**（gdbserver，`microblazeel-*linux*`）。
- **AArch64 MinGW**（`aarch64-*-mingw*`）。

**5. Python API 增强**
- 新增 `gdb.Corefile` 类（含 `Inferior.corefile` 属性）、`gdb.CorefileMappedFile`/`gdb.CorefileMappedFileRegion` 类型。
- 新增 `gdb.Style`、`gdb.StyleParameterSet` 类与 `gdb.INTENSITY_*` 常量；`gdb.write()` 新增可选 `style` 参数。
- 新增 `gdb.events.selected_context` 与 `gdb.events.corefile_changed` 事件。
- 新增 `gdb.Symtab.source_lines` 方法；`Architecture.disassemble` 新增 `styling` 参数；新增 `gdb.Block.ranges` 属性。

**6. DAP / 远端协议变更**
- DAP：未处理 Ada 异常可用 `unhandled` 过滤器捕获；launch/attach 新增 `adaSourceCharset`、attach 新增 `coreFile` 参数；常量现在在作用域中返回。
- 远端协议：新增 `qExecAndArgs` 包；新增 `single-inf-arg` qSupported 特性。

**7. 不兼容变更（破坏性）**
- 移除 **stabs / mdebug** 调试信息格式与 **dbx** 二进制格式支持。
- 移除 **CTF（Common Trace Format）** 支持：trace 信息只存 GDB 自己的 `tfile` 格式，`target ctf` 命令消失，`tsave`/MI `-trace-save` 不再接受 `-ctf`，移除 `--with-babeltrace` 配置项。
- 移除 **version 7 以前**的 `.gdb_index` 段支持。
- 移除 **DWP（DWARF Package File）version 1** 支持。
- `record save` 的执行记录格式变更，旧格式不再支持。
- **Guile 最低版本提至 2.2**；移除废弃的内存端口缓冲大小过程（用 `setvbuf`）。
- 移除 `maint check psymtabs`/`maint info psymtabs`/`maint print psymbols`（GDB 不再内部使用部分符号表）。
- `maintenance info program-spaces` 不再显示 core 文件名（改用 `info inferiors`）。
- **不再支持 AIX 7.1**：最低 AIX 7.2 TL5，且 AIX 上仅支持 DWARF 调试信息。
- **s390 32 位目标（s390-\*）被弃用**，计划未来移除（configure 现直接报错，可用 `--enable-obsolete` 覆盖）；s390x 64 位仍支持。

## 解读

**1. Windows 原生目标的增强是本期最实在的「可用性」升级。** non-stop 模式、调度锁、TLS、真彩/UTF-8——这些是长期在 Windows 上调试时缺位的能力。对 Windows 平台上的 GDB 用户，这是从「能勉强用」到「接近第一梯队体验」的跨越。

**2. 旧格式清理是「减负式进步」。** 移除 stabs/mdebug/CTF/DWP-v1 等，短期会伤到仍依赖它们的老工具链，但长期让 GDB 的代码面更干净。注意 CTF 移除意味着**老的 CTF trace 文件无法再读**，有历史 trace 资产的团队要提前转存。

**3. Python API 持续膨胀。** Corefile 类、Style 类、selected_context/corefile_changed 事件——这些主要服务于**自动化调试脚本、IDE/编辑器集成（DAP）、自定义可视化**。对用 GDB Python 写工具链的人，这是持续红利。

**4. 新目标（MicroBlaze、AArch64 MinGW）扩展覆盖。** 尤其 AArch64 MinGW，意味着在 Windows 上交叉调试 AArch64 目标更顺。
