---
title: "OpenBSD 把 Wine 移植回来了：而打开大门的关键，是一套手写的 x86 指令解码器"
date: 2026-10-27
slug: openbsd-wine-port-gs-emulation
tags: [OpenBSD, Wine, 移植, x86_64, gsbase, SWAPGS, Spectre, CVE-2019-1125, seccomp, TLS, TEB, ntdll, vkd3d, clang-pe, 安全设计, 侧信道]
category: Linux/内核
author: FreeLAMP.com
original_source: "openbsd/ports 仓库 emulators/wine 的实际提交与 44 个 patch 原文 + openbsd-ports 与 openbsd-tech 邮件列表原始讨论"
original_author: "Thomas Frohwein（maintainer）、Andrii Yukhymchak（%gs 模拟实现）、Bryan Steele、Martijn van Duren、Stuart Henderson、Story、Neth Iafin"
original_date: 2026-10-19
original_url: "https://marc.info/?l=openbsd-ports&m=179236125692175"
description: "OpenBSD 的 ports 在 2011 年删掉 Wine 之后，2026 年 10 月 19 日把它重新 import 回来了，10 月 22 日已更新到 Wine 11.20。真正的门槛不是 Wine 本身，而是 OpenBSD 出于 SWAPGS 侧信道防护（性能与稳定性）拒绝在用户态设置 %gs base —— 而 Windows x64 代码大量使用 %gs:0x30 访问 TEB。Andrii Yukhymchak 的解法是一套手写的 x86 指令解码器 + 三级回退策略（原位改写 / rel32 跳转 stub / SIGSEGV 陷阱），配 44 个 patch。本文逐行解读这套实现，并顺带讲清 %gs、TEB、TLS slot、stub 生成、跨进程线程信号等每个环节。"
published: true
---

> 来源：**[openbsd/ports 仓库 emulators/wine](https://github.com/openbsd/ports/tree/master/emulators/wine)** 的实际提交与 44 个 patch 原文（实测拉取）、**[openbsd-ports 邮件列表原始讨论](https://marc.info/?l=openbsd-ports&m=179236125692175)**（Thomas Frohwein，2026-10-18）、[回复](https://marc.info/?l=openbsd-ports&m=179236426893591&w=2)（Bryan Steele）、[回复](https://marc.info/?l=openbsd-ports&m=179240622622831&w=2)（Martijn van Duren）、[回复](https://marc.info/?l=openbsd-ports&m=179240650723110&w=2)（Stuart Henderson）、[openbsd-tech 的 %gs 提问](https://marc.info/?l=openbsd-tech&m=179067466617674&w=2) 与 [回复](https://marc.info/?l=openbsd-tech&m=179069358537094&w=2)
> ⚠️ **实测的 ports 提交序列**（`path=emulators/wine`）：**2026-10-19 `e441aff3` re-import emulators/wine** → `fd10d99c` resolve merge conflicts → 10-20 `6a68fef3` → 10-22 `b38148f0` use clang headers from llvm distfile → `6086ce08` update distinfo → **`4a90c8df` update to wine 11.20** → 10-25 `71cac71b` hidden dep on linux/input.h → 10-26 `fef9ec33` disable linux/input.h header in autoconf。**再往前一次提交是 2011-07-06 `70ca2b7e` "Remove the wine port."**
> 本文为**解读**。所有 patch 代码与提交记录为实测一手材料。

## 一句话结论

**OpenBSD 的 Wine 移植，最难的部分不是 Wine，是 OpenBSD 有一条「用户态不许设 `%gs` base」的安全政策 —— 而 Windows x64 代码把 `%gs:0x30` 当作访问线程块（TEB）的标准手段。**

**Andrii Yukhymchak 的解法，是写了一个手写的 x86-64 指令解码器，在运行时把 `%gs:` 前缀的访存指令逐条翻译成 OpenBSD 的 `%fs:` 等价形式 —— 必要时就地改写指令，不够长就跳到一段自己生成的 stub，再不够就用 SIGSEGV 陷阱兜底。**

**而我认为这整件事最有价值的地方，不在于「Wine 能在 OpenBSD 上跑了」，在于它把一个抽象的安全决策，翻译成了一个具体的工程约束 —— 并且没有通过削弱安全决策来解决它。**

## 二、起点：一个被搁置了 15 年的问题

### 2.1 邮件列表里的那个提问

**2026 年 9 月 29 日，Neth Iafin（也就是 Andrii Yukhymchak 自己的化名）在 openbsd-tech 上问：**

> **「我想知道为什么 OpenBSD 在用户态没有设置 `%gs` 的能力？这是为了避免 swapgs 漏洞吗？还是别的原因？」**
>
> **「我理解支持 wine 在 OpenBSD 的优先级大概是低于 0，但我好奇 `%gs` 被锁给内核的理由。」**
>
> **「我假设设置 `%gs` 作为 syscall 回来的可能性是零？」**

**一个半小时后，Story 回复：**

> **「让进程设置自己的 GS.base 会暴露经典的 SWAPGS 推测性侧信道那一类 bug（CVE-2019-1125 之类）。把 GS 保持在内核的独占控制下，去掉了这个攻击面，也让进入/退出路径保持简单。」**
>
> **「我不是专家，我还在读 man page，但我知道没有计划为此加 syscall。」**

**⭐ 注意两件事：**

1. **这条回复的定性非常准。** **CVE-2019-1125 是 Linux 上非常著名的 SWAPGS 缓解副作用 —— 在 64 位系统上用 `swapgs` 恢复 GS 寄存器时，如果攻击者能控制 `mov %gs` 后的指令字节，会造成推测执行窗口。** **OpenBSD 是 FreeBSD 血统，而 FreeBSD 从来就没提供用户态设 GS base 的接口 —— 所以这条是继承来的。**

2. **⭐ Story 在 18 分钟后自己发了一条更正：**

   > **「更正：我在猜测原因，我不知道开发者的意图。」**
   > **「我跳进来太早了。」**

**—— 这两封邮件合起来，恰好是这个故事最好的开场：一条「安全决策」的公开解释，和它随后被作者自己标注为「猜测」的诚实。**

### 2.2 而 Thomas Frohwein 的第一句话就是「今年最令人惊讶的移植提案」

**2026 年 10 月 18 日 22:08 UTC，Thomas Frohwein 在 openbsd-ports 发出提案：**

> **「在可能是今年最令人惊讶的移植提案里，我自豪地呈现一个新的 wine 移植提案。**
>
> **这是集体努力的结果，源于在 %gs/gsbase 这个问题上的一些推动（见讨论串）。**
>
> **大门是随着 Andrii 针对 %gs 问题的软件方案打开的 —— 他向我解释为：『不能设 gsbase，所以我们在命令上模拟 %gs 前缀』。**
>
> **总的来说重活是 Andrii 和 Fabien 干的 —— 致谢。**
>
> **结果是对 wine 的兴趣出现了一股浪潮，和 5-10 年前不一样，因为很多 Windows 软件已经转向 64 位了。」**

**⭐ 注意这个措辞：「**在命令上模拟 %gs 前缀**」—— 这就是全部魔法的十一个字的摘要。**

## 三、⭐ 问题的实质：为什么 x64 Windows 离不开 `%gs:0x30`

**要理解这个移植，必须先理解 `%gs` 在 Windows x64 里到底干什么。**

**从 Andrii 的 patch 注释里能直接读到答案（`patch-dlls_ntdll_unix_gs_openbsd_c`，974 行新增代码）：**

```
(1) In place - this is NtCurrentTeb() call. It always compiles into
    mov %gs:0x30, %r for this to work, since we have ref to teb in our
    teb_tls_offset, we can just replace few values in the command itself
    for example
 65 48 8b 04 25 30 00 00 00          mov %gs:0x30, %rax
 64 48 8b 04 25 xx xx xx xx          mov %fs:teb_tls_offset, %rax
                        --- where teb_tls_offset is negative
```

**⭐ 翻译一下：**

- **Windows x64 的线程块指针（TEB）固定存放在 `GS:0x30`**；
- **`NtCurrentTeb()` 在任何编译器下都编译成 `mov %gs:0x30, %rax`**；
- **而 Wine 的 POSIX 后端要访问同样语义的东西，只能走 `%fs:` —— 因为 OpenBSD 的 TLS 机制在 `%fs` 上。**

**所以问题的本质是：** **Wine 的 ntdll 需要把「`%gs:0x30`」这个语义，翻译成「`%fs:teb_tls_offset`」（一个负偏移，位于 OpenBSD 的 threadblock 之下）。**

**而这不是「加一个偏移量」就能解决的 —— 因为 `%gs` 和 `%fs` 是两个不同的段寄存器，编码在指令前缀里（`0x65` vs `0x64`）。**

**⭐ 更加要命的是：编译器并不只生成一条 `mov %gs:0x30,%rax`。** **它是生成一大类。** **Andrii 的 patch 里有一整个 `get_gs_opcode_info()` 函数在做 opcode 表 —— 覆盖 `add/or/adc/sbb/and/sub/xor/cmp` 带寄存器、group1 的立即数形式、`mov` 的各种宽度、`movzx/movsx`、`cmovcc` 全家桶……**

## 四、⭐⭐ Andrii 的三级回退策略

**这是整个移植的技术核心，而它的设计逻辑非常清晰。**

**patch 顶部的注释原文：**

```
Whenever we have a page fault, we need to see if the fault was caused by %gs
being pinned to 0 in OpenBSD. For this we parse the command assuming %gs was 0
(fault was at "zero-page"), find if it is really %gs command and then rewrite
it without %gs. Sometimes another thread will already rewrite gs to fs/jmp and
we just need a retry.

Following approaches are implemented:
(1) In place - this is NtCurrentTeb() call. ...
(2) Generic Stub
    for this to work, the instruction has to be 5 bytes or longer. If it is,
    and we find a spot to park a stub in rel32 we can replace it with a jmp rel32
    command to a stub that rewrites the command without %gs.
    This can be done with ANY command that is 5 bytes or longer. If command is
    less than 5 bytes, we don't have enough space to replace it. I will have to
    be handled by case 3, but commands like that are rare. This replacement is
    stable but we have to specifically handle case when thread is being stopped
    inside of the stub.

(3) SIGSEGV on every trap over that instruction
    Same as 2 but there was not enough space to replace it with a JMP REL
    (5 bytes). We pay signal round trip every time but at least it works.
    The stub is basically the same but we are replacing a "replaced instruction"
    with a hash table that points that for this SIGSEGV on this instruction we
    jump to that Stub.
```

**⭐ 三个策略的取舍逻辑非常清楚：**

| 策略 | 条件 | 代价 | 稳定性 |
|---|---|---|---|
| **① 原位改写** | 指令是已知的 `NtCurrentTeb()` 形式 | **零开销** | 最好 |
| **② rel32 跳 stub** | 指令 **≥ 5 字节** | 一次跳转 | 好（但要处理「线程停在 stub 里」的边界情况） |
| **③ SIGSEGV 陷阱** | 指令 **< 5 字节**（放不下 jmp rel32） | **每次都付一次信号往返** | 最差，但「至少它能用」 |

**⭐ 而触发机制的巧妙之处在于：它不是主动扫描代码，而是「等它出错」。**

**在 OpenBSD 上 `%gs` 被钉在 0，所以任何 `%gs:xxx` 访存都会去访问「零页」→ 触发 SIGSEGV → 信号处理器拿到出错时的 PC → 反汇编那几条字节 → 判断「这真的是一条 `%gs` 指令吗」→ 是的话就改写掉。**

**⭐ 这是一个「懒的、零扫描成本」的方案 —— 而它的代价就是策略 ③ 那种「每次付一次信号往返」。**

## 五、⭐⭐ stub 的生成：手写的机器码

**这是整个方案里最硬核的部分 —— 因为它要在运行时**生成**机器码。**

**patch 里的 stub 格式注释：**

```
The form of the stub for 64-bit addressing is
 mov %S,%fs:slot+8           save the scratch register S
 mov %fs:slot, %S            S = TEB
 lea 0(%base, %S, 1), %S     S = TEB + base , if base register
 <the instruction>           [S + index*scale + disp32] instead of %gs:...
 mov %fs:slot+8, %S          restore S
 jmp *0(%rip)                back to next instruction
 .quad site + len

Slot is our offset (negative) below OpenBSD's threadblock.
Slot contains TEB at *slot, and scratch register at *slot+8
32-bit addressing uses a second scratch register at *slot+16.
%S scratch register is any register that is not used in the instruction.
There are up to 3 registers that can be used in the instruction, so we
always have a one of 7 (not you %rsp) registers free.
```

**⭐ 逐句读这个 stub：**

1. **`mov %S, %fs:slot+8`** —— 把一个「临时寄存器」S 的值存到 TLS slot 里（因为 stub 要用 S 改写地址，但得先保存原值）；
2. **`mov %fs:slot, %S`** —— 取出 TEB 指针到 S；
3. **`lea 0(%base, %S, 1), %S`** —— 加上基址（对应原指令里的 base 寄存器或 disp32）；
4. **`<the instruction>`** —— **原样插入那条原始指令，只是现在它的内存操作数是 `[S + index*scale + disp32]`，而不是 `%gs:...`**；
5. **`mov %fs:slot+8, %S`** —— 恢复 S；
6. **`jmp *0(%rip)` + `.quad site + len`** —— **跳回原指令的下一条**。

**⭐ 而「7 个可用临时寄存器」这个细节非常关键：**

> **「%S 临时寄存器是指任何未被该指令使用的寄存器。一条指令最多能用 3 个寄存器，所以我们总能从 7 个（不含 `%rsp`）里挑出一个空闲的。」**

**—— x86-64 有 16 个通用寄存器，扣掉 `%rsp` 和指令自身占用的，最多 3 个，剩下至少 7 个可用。** **这保证了「找一个不冲突的临时寄存器」永远做得到。**

**⭐ 而且 32 位寻址模式还多了一个 scratch 槽（`slot+16`）** —— patch 里对应 `two_scratch` 标志。

### 5.1 TLS slot 放在 loader 里（而不是 ntdll）

**这是另一个很见功力的细节，来自 `patch-loader_main_c`：**

> **「给 loader 加一个 32 字节的 TLS slot。它位于 `%fs` 线程指针正下方，保存 TEB 指针以及用于 `%gs` 修补的两个 scratch 槽。**
>
> **这个 slot 必须放在 loader 里，因为 ld.so 拒绝 `dlopen()` 的库（比如 ntdll.so）使用静态 TLS。」**"

**⭐ 翻译：** **静态 TLS（TLS model 里的 initial-exec / local-exec）只有可执行文件本体能用，动态加载的共享库不行。** **而 ntdll 是 `dlopen` 进来的。** **所以那个必须被所有线程共享的 TEB 指针槽，只能放在 loader 里 —— 而 Wine 的 loader 是 `wine/loader` 那个静态可执行文件。**

**⭐ 这个约束的连锁反应很大：TLS slot 的位置必须是「OpenBSD threadblock 下方的一个固定负偏移」，而且必须所有线程一致 —— 所以 patch 里才有 `teb_tls_offset` 这个全局变量，在 `gs_init_process()` 里通过 `dlsym(RTLD_DEFAULT, "__wine_teb_tls_offset")` 拿到。**

### 5.2 还有一个「伪装」机制

**patch 里还有一条我认为很有意思的设计：**

> **「另一个值得注意的方法是 `gs_leave_stub`，它允许我们在 SIGSEGV 和 SIGUSR1 上离开 stub，所以在外面它永远看起来我们不在 stub 里。这有助于调试、信号处理和一般的合理性检查。」**

**⭐ 翻译：** **stub 里的执行状态会让调试器和信号处理器困惑（栈上的返回地址不对、看起来像在 Wine 内部某处）。** **所以他加了一个「退出 stub」的机制 —— 让执行流在特定信号下看起来已经回到正常代码路径。**

**这是一个纯工程上的「让系统看起来正常」的设计 —— 而它的存在本身说明了问题的复杂度：你在一个完全陌生的 ABI 上模拟另一个 OS 的内存模型。**

### 5.3 ⚠️ 一个值得注意的细节：指令列表由 LLM 生成

**patch 注释里有一段必须引用：**

> **「大部分代码基于 64 位规范构建，以及开源（Copyleft 且免费）编译器为 Windows 生成 TEB 块访问的指令列表。这段代码是根据 LLM 生成的指令解码图**手工**编写的。指令列表由 LLM 提供，并**用规范人工核对**过。支持 0x67 前缀（32 位寻址模式），但 moffs 指令除外。其他不支持的前缀未被检测到会与 `%gs` 一起由已审阅的编译器生成。」**

**⭐ 我认为这段注释的写法非常值得学习 —— 它同时说清了三件事：**

1. **用了 LLM**（不藏着）；
2. **「根据 LLM 生成的解码图手工编写」** —— 不是直接用 LLM 的输出；
3. **「用规范人工核对过」** —— 有人对着 Intel/AMD 的架构手册逐条核过。

**—— 而且它还诚实地划出了边界：「支持 0x67 前缀，但 moffs 指令除外。其他不支持的前缀未被检测到会与 `%gs` 一起由已审阅的编译器生成。」**

**这最后半句是安全审计里最该有的一句话：「我没找到反例」和「我证明了没有反例」是两回事。**

**⭐ 而这里有一个非常有意思的上下文：Hacker News 上讨论这个移植时，有评论者说：**
> **「我也尊重 Wine 和 OpenBSD 以及他们「不在 repo/ports 里放任何 LLM 代码」的规则。」**

**（OpenBSD 的 `README`/端口惯例里有明确要求，ports 里不放 AI 生成的代码。）**

**⭐ 而 Andrii 的处理方式，恰好给出了这条规则下一个可行的范式：** **LLM 参与「资料整理与初稿」，但最终产物是**手工编写**的、**人工核对过**的、且**明确标注了覆盖边界**的代码 —— 而且它没有进 ports 树，而是先以「移植提案」的形式在邮件列表里公开征求意见。**

**（最终 44 个 patch 里，`gs_openbsd.c` 的版权头明确写着 `Copyright (C) 2026 Andrii Yukhymchak`，是 LGPL-2.1+ 的原创代码。）**

## 六、⭐ 44 个 patch：不只是 `%gs`

**实测 `emulators/wine/patches/` 目录，共 44 个 patch。分类看：**

| 类别 | 文件 | 说明 |
|---|---|---|
| **`%gs` 核心** | `patch-dlls_ntdll_unix_gs_openbsd_c`（**44844 字节**，新增 974 行）、`..._gs_openbsd_h` | 指令解码器 + stub 生成器 |
| **信号处理** | `patch-dlls_ntdll_unix_sig_openbsd_c`、`..._sig_openbsd_h`、`patch-server_sig_openbsd_c`、`..._sig_openbsd_h`、`patch-dlls_ntdll_unix_signal_x86_64_c`（16597 字节） | 见第七节 |
| **进程/线程模型** | `patch-server_process_c/h`、`patch-server_thread_c`、`patch-server_ptrace_c`、`patch-dlls_ntdll_unix_process_c`、`..._unix_thread_c` | |
| **Unix 环境** | `patch-dlls_ntdll_unix_env_c`、`..._unix_file_c`、`..._unix_server_c`、`..._unix_system_c`、`..._unix_virtual_c`、`..._unix_unix_private_h` | |
| **API 差异** | `patch-dlls_dnsapi_*`、`patch-dlls_iphlpapi_*`、`patch-dlls_nsiproxy_*`、`patch-dlls_msvcrt_handler4_c`、`patch-dlls_crypt32_unixlib_c`、`patch-dlls_dxgi_output_c`、`patch-include_wine_server_protocol_h` | |
| **X11 / 图形** | `patch-dlls_winex11_drv_keyboard_c`、`..._drv_x11drv_main_c`、`patch-dlls_winebus_sys_bus_sdl_c` | |
| **音频** | `patch-dlls_winepulse_drv_pulse_c` | |
| **其他** | `patch-loader_main_c`、`patch-server_Makefile_in`、`patch-server_fd_c`、`patch-server_sock_c`、`patch-server_unicode_c`、`patch-server_protocol_def`、`patch-tools_tools_h`、`patch-libs_vkd3d_libs_vkd3d_utils_c`、`patch-dlls_wpcap_Makefile_in`、`patch-patch-configure_ac` | |

### 6.1 Makefile 里那些 `--without-` 每一个都是一条「OpenBSD 没有这个」的注脚

**实测的 `emulators/wine/Makefile`（4754 字节）：**

```makefile
ONLY_FOR_ARCHS =	amd64
COMMENT =		compatibility layer to run Windows applications
DISTNAME =		wine-11.20
REVISION =		1
MAINTAINER =		Thomas Frohwein <thfr@openbsd.org>, \
			Andrii Yukhymchak <NethIafin-obsd@proton.me>
CONFIGURE_ARGS =	--enable-archs=x86_64 --with-mingw
```

**⭐ 注意 `ONLY_FOR_ARCHS = amd64` —— 这个 port 只在 amd64 上存在。** **而 Mail 列表里 Bryan Steele 的测试确认也正是「port builds on amd64 (tested on Intel 11th Gen w/ IBT)」。**

**而那一长串 `--without-`，每一个后面都有注释解释为什么：**

```makefile
# GSSAPI: Kerberos SSP support needs adaptation to security/heimdal.
# krb5: Kerberos authentication also needs adaptation to security/heimdal.
# USB: devel/libusb1 lacks hotplug support. wineusb aborts initialization.
# V4L2: libv4l2 is found, but linux/videodev2.h is missing.
# Wayland: untested
CONFIGURE_ARGS+=	--without-gssapi --without-krb5 --without-usb \
			--without-v4l2 --without-wayland
```

**⭐ 我认为这五条注释本身就是一份「Windows 世界 → Unix 世界」的对照表：**

| Windows 需要 | OpenBSD 的情况 |
|---|---|
| **Kerberos（SSP + krb5）** | 需要适配 OpenBSD 的 **Heimdal** 而非 MIT Kerberos |
| **USB 热插拔** | `devel/libusb1` 缺少 hotplug 支持，wineusb 会 abort 初始化 |
| **V4L2 视频设备** | libv4l2 存在，但缺 `linux/videodev2.h` |
| **Wayland** | **untested**（尚未测试） |
| **ALSA / CoreAudio / OSS / udev / hwloc / OpenCL** | 全部 `--without` |

**—— 注意 Wayland 那条：OpenBSD 的 Wayland 支持本身还不完善，所以 Wine 只能走 X11。**

### 6.2 Linux 特有的头文件依赖：两次提交解决一个依赖

**实测提交序列里有两个连续的、看起来很小但很有代表性的提交：**

- **2026-10-25 `71cac71b`**：`hidden dep on linux/input.h; found by naddy@`
- **2026-10-26 `fef9ec33`**：`Better: disable linux/input.h header in autoconf. Similar to how it is ...`

**对应 Makefile 里这一行：**

```makefile
# prevent linux/input.h detection: evdev keycodes don't match OpenBSD XFree86.
CONFIGURE_ENV+=		ac_cv_header_linux_input_h=no
```

**⭐ 这个注释是整个移植里信息量最大的一句：**

**「阻止 `linux/input.h` 的探测：evdev 的键码与 OpenBSD 的 XFree86 不匹配。」**

**—— 也就是说：** **Wine 的输入层抽象建立在 **Linux evdev** 的键码编号之上，而 OpenBSD 的 XFree86 用的是另一套键码编号。** **所以这个「伪装成 Linux 有这个头文件」的开关，不只是让 configure 过，而是**必须在 configure 阶段就掐掉**，否则会编译出键码错乱的输入处理。**

**⭐ 而这两天的两连提交，说明这个依赖是在 port 已经在树里之后才被发现的 —— 由 naddy@ 报出。** **这正是 OpenBSD ports 流程的一个特点：port 先合并，问题在 CI 与用户测试中暴露，再补提交。**

### 6.3 libpcap 的 `.pc` 文件名差异

```makefile
# Wine requests libpcap.pc; the OpenBSD port instead provides libepcap.pc
# and installs its headers/libraries outside the default search paths.
CONFIGURE_ENV+=		INOTIFY_LIBS="-L${LOCALBASE}/lib/inotify -Wl,-rpath,${LOCALBASE}/lib/inotify -linotify" \
			PCAP_CFLAGS="-I${LOCALBASE}/include/libpcap" \
			PCAP_LIBS="-L${LOCALBASE}/lib/libpcap -Wl,-rpath,${LOCALBASE}/lib/libpcap -lpcap"
```

**⭐ 而 `inotify` 那条更典型：OpenBSD 的 inotify 是独立 port（`lib/inotify`），装在非标准路径下，所以要手工给 `-L` 和 `-rpath`。**

## 七、⭐ 第二个硬骨头：跨进程线程信号

**这是除了 `%gs` 之外的另一个大工程，而它的成因非常 OpenBSD。**

**`patch-dlls_ntdll_unix_sig_openbsd.c` 的注释原文：**

> **「从 wineserver 发给客户端线程的信号总是要跨越进程边界。**
>
> **在 OpenBSD 上你不能从另一个进程给一个线程发信号。`thrkill()` 只在同一进程内有效。**
>
> **绕过它的办法是：用 SIGUSR2 把整个进程杀掉，然后内核把它投递给一个活跃线程。那个线程用 `thrkill()` 把每个排队的信号发给它的目标线程。**
>
> **Chromium/Electron 主动使用这个机制来做采样 profiler 和 hang watcher。」**

**⭐ 翻译一下这个「绕法」：**

1. **wineserver 想给客户端的某个线程发信号**（Wine 的架构里，wineserver 是「会话管理器」，客户端进程通过它受控）；
2. **正常做法是 `tkill(tid, tid, sig)` 或 `thrkill()`；**
3. **⭐ 但 OpenBSD 的 `thrkill()` 只允许同进程内调用（这是 OpenBSD 特有的安全收紧 —— 防止跨进程操纵线程）；**
4. **所以改成：给整个进程发 `SIGUSR2` → 内核把它投递给某个「活跃线程」 → 那个线程醒来，用 `thrkill()`（现在同进程了）把排队的信号转发给真正的目标线程。**

**⭐ 而最后那句「Chromium/Electron 主动使用这个机制来做采样 profiler 和 hang watcher」非常关键 —— 因为它意味着这条路径**不是 Wine 特有的**，而是一个通用的、会被大量现代应用用到的机制。**

**—— 换句话说：如果没有这个 patch，Wine 里的 Chromium/Electron 应用（VS Code、Slack、各种 Electron 桌面应用）的采样器和 hang watcher 都会失效。**

**而 `patch-server_ptrace_c` 里还配套改了一处：**

```c
 void finish_process_tracing( struct process *process )
 {
+#ifdef __OpenBSD__
+    finish_process_signal_targets( process );
+#endif
 }
```

**—— 进程追踪结束时，必须把排队的信号目标清掉，否则会残留。**

**⭐ 官方明确要求双向同步：**

> **「这里的任何改动都必须同步反映到 server 的 `sig_openbsd`。」**

**（`server/sig_openbsd.c` 也在 44 个 patch 里。）**

## 八、⭐ 移植的实际效果：能跑什么，不能跑什么

**Thomas Frohwein 的原始提案给了一张表，我把它完整转述并加上解读：**

### 8.1 能跑的

| 项目 | 细节 |
|---|---|
| **锁屏、滑动解锁、主页（两页图标）、原版 iOS 16 壁纸** | — |
| **系统手势**：上滑（主页 / 应用切换）、边缘滑动（返回）、控制中心 | |
| **应用**：设置、时钟、日历、照片、备忘录、Safari 等；小组件（天气、日历） | |
| **触摸**：Goodix GT9916，多点触控，触摸唤醒；真实电源键与音量键 | |
| **8 个 CPU 核心**（`cpus=8`），大核 2.4 GHz，**约 20 秒到锁屏** | |
| **Adreno 642L GPU 通过 Mesa/freedreno**（`gpu=1`，OpenGL ES for CoreAnimation） | |
| **Wi-Fi**（WCN6750，ath11k）：从设置里连接、Wi-Fi 下 Safari，**55–90 Mbit/s** | |
| **声音**（扬声器、主麦克风）、相机（前/后、预览、对焦、HEIC 照片） | |
| **数据在重启后保留**（`var_store=1 ufs_write=1`）；iOS 根卷在手机 flash 上 | |
| **Sileo + Procursus**（dpkg、apt）、tweaks、SSH | |

### 8.2 不能跑的

| 项目 | 细节 |
|---|---|
| **蜂窝网络、蓝牙** | |
| **在我们内核下充电**（手机只放电） | |
| **应用的 Metal**（进行中：456 个系统 shader 里 **293 个**已在 Adreno 上跑通） | |
| **App Store 内容与 Apple ID 登录**（**无 Secure Enclave**；FairPlay daemon 退出） | |
| **视频与 Live Photo 录制** | |

### 8.3 ⭐ 最重要的两条限制

**① 「WoW64 doesn't work, so 32bit Windows software is still a no-op.」**

**⭐ 这是整个移植**最大**的功能缺口 —— 而它的原因恰好又回到了 `%gs`：**

**因为 WoW64 是「在 64 位 Windows 里跑 32 位 x86 代码」，而 32 位 x86 代码用的是完全不同的 TLS 访问模型（`%fs:0x30` 而非 `%gs:0x30`）。** **也就是说，32 位路径需要另一套模拟实现，而 Andrii 的这套是为 64 位设计的。**

**② 「The builtin-tests are disabled for now.」**

> **「启用它们相当麻烦，因为它们需要访问 X server，而且多个测试仍然会挂起 —— 尽管在用不少游戏做的真实生活测试中并没有观察到这一点。这仍在处理中。」**

**⭐ 我认为这条值得单独说：** **Wine 自带的测试套件被关掉了，理由是「需要 X server」且「多个测试仍然会挂起」。**

**—— 也就是说，这个 port 目前是「靠人的手工验证」支撑的，没有自动化回归测试。** **而 Bryan Steele 的回复里那句「虽然有些粗糙的地方，但没有什么是不能在树内清理的」，正是从「测试关着」这个状态下得出的。**

**⭐ 而 Stuart Henderson 的回复把真正的问题指向了维护成本：**

> **「我很担心这一点。真的需要一些关于如何生成它们的信息，最好是一个能从 llvm/clang 源码 tarball 自动运行、并作为 emulators/wine 构建一部分的方法，这样 wine 就不会挡住每次 lang/clang 更新。**'
>
> **「如果不能自动，至少要有一个能从 make target 运行的东西。」**
>
> **「（如果不是构建时自动的，那 BUILD_DEPENDS 就得锁到精确版本……）」**
>
> **「这些大的补丁集有可能被合入上游吗？」**
>
> **「有些 `#ifdef __OpenBSD__` 补丁看起来可以用对特定事物的检查（至少 xattrs 是，我不确定还有没有别的）来代替对 OpenBSD/非 OpenBSD 的条件判断。」**

**⭐ 这三条评论，每一条都指向 ports 生态的真实痛点：**

1. **⭐ 「wine 会不会挡住每次 lang/clang 更新」** —— **这是 ports 最经典的「port 拖累整个树」问题。** **因为 clang 的 PE 头文件（`clang/lib/Headers/*.h`）是 Windows 目标代码编译必需的，而 LLVM 每次升级都会动它们。**

2. **⭐ 那个 clang-pe 头文件问题的解法很巧妙** —— 实测 Makefile：

   ```makefile
   CLANG_PE_RESOURCE =	${WRKDIR}/clang-pe
   LLVM_PREFIX =		${LOCALBASE}/llvm${MODCLANG_VERSION}
   CLANG_RESOURCE =	${LLVM_PREFIX}/lib/clang/${MODCLANG_VERSION}
   pre-configure:
   	${INSTALL_DATA_DIR} ${CLANG_PE_RESOURCE}/include
   	cp ${WRKDIR}/devel/llvm/*/*/clang/lib/Headers/*.h \
   		${CLANG_PE_RESOURCE}/include/
   	cp -R ${CLANG_RESOURCE}/include/. ${CLANG_PE_RESOURCE}/include/
   ```

   **⭐ 结合 Thomas Frohwein 邮件里贴的那句注释：**
   > **「# keep this in sync with MODCLANG_VERSION」**
   > **「# source for updates/new releases: https://thfr.gothub.org/wine-clang-pe-headers」**

   **—— 也就是说：** **Andrii/Thomas 在自己的 got hub 上维护了一份从 LLVM 提取出来的 clang PE 头文件（实测当前 tag 是 `22.1.8`，来自 `llvm 22.1.8`），并且在 Makefile 里用 `:patch` target 从 LLVM distfile 里自动提取（提交 `b38148f0` 干的就是这件事）。**

   **⭐ 这是一个「既自动又可手工」的折中：** **自动提取保证能跟上 LLVM 版本，外部仓库保证在提取失败时有个可用的兜底。**

3. **⭐ 「这些大的补丁集有可能被合入上游吗？」** —— **这是最要紧的一条。** **44 个 patch 里，`gs_openbsd.c` 那两个（44844 + 2244 字节）是最有上游价值的 —— 因为它们解决的是「Unix-like OS 上跑 Windows x64 代码」这个**通用**问题，不只是 OpenBSD 的问题。**

**而 Thomas 在后续提交里做了一件很 OpenBSD 的事：**

**2026-10-20 `6a68fef3`：`add OpenBSD to #ifdefs for parse_mount_entries`**

**—— 把 OpenBSD 加进上游代码里的 `#ifdef` 列表。** **⭐ 这是「向上游靠拢」的实际动作：让上游代码知道有 OpenBSD 这个平台存在，而不是把 OpenBSD 特有的逻辑全塞进 patch 里。**

## 九、⭐⭐ 十四年的距离

**这一节我想单独讲，因为它是我在实测提交历史里发现的最有冲击力的一个事实。**

**`path=emulators/wine` 的完整提交历史（实测）：**

```
2026-10-26 fef9ec33 Better: disable linux/input.h header in autoconf...
2026-10-25 71cac71b hidden dep on linux/input.h; found by naddy@
2026-10-22 4a90c8df update to wine 11.20. Tested by Andrii and me.
2026-10-22 6086ce08 update distinfo
2026-10-22 b38148f0 use clang headers from llvm distfile, extracted via a :patch target
2026-10-20 6a68fef3 add OpenBSD to #ifdefs for parse_mount_entries
2026-10-19 fd10d99c resolve merge conflicts by re-reading previously removed files
2026-10-19 e441aff3 re-import emulators/wine
─────────────────────── 15 年前 ───────────────────────
2011-07-06 70ca2b7e Remove the wine port.
2011-05-01 8be917e7 Use proper AUTOCONF_VERSION, from Brad.
2010-11-15 a14bf26c new depends
2010-10-24 ff07e285 Remove USE_X11.
2010-10-23 ec8f9886 revision/lib_depends
2010-10-19 ae27646c this port is unfinished, add a comment to make it even more obvious
```

**⭐ 注意 2010-10-19 那一条提交信息：**

> **`this port is unfinished, add a comment to make it even more obvious`**
>
> （**这个 port 还没完成，加一条注释让它更明显**。）

**—— 也就是说：上一次尝试（2010）不是被「技术不行」否掉的，而是被「做不完」否掉的 —— 作者自己加了个注释让所有人都知道这是个半成品，然后在半年后（2011-07）把它删了。**

**⭐ 而 2026 年这一次，它被「re-import」了。**

**Thomas 在邮件里用了「re-import」这个词，而实测提交 `fd10d99c` 的说明是「resolve merge conflicts by re-reading previously removed files」** —— **⭐ 这说明这次不是从零开始，而是把 2010 年那个半成品 port 的文件重新拉回来，然后在上面继续。**

**—— 换句话说：十五年前那位作者留下的骨架，被两个人接力完成了。**

**⭐ 而我认为这件事对 OpenBSD 社区的意义，比「Wine 能跑了」更大：**

**2010 年那次失败的原因是「做不完」—— 一个人、业余时间、面对一个巨大的代码库。** **而 2026 年这次成功的原因是：一个人写出了那个「最难的部分」（`%gs` 模拟），另一个人把它接进 ports 体系并处理掉所有工程细节（构建系统、依赖、CI、上游配合）。**

**—— 这是「个人技术突破」与「集体工程能力」叠加的典型案例，而 15 年的时间差，正好是这两者之间的差距。**

## 十、⭐⭐ 我认为这个故事最值得学的东西

### 10.1 「安全决策」不是「不能逾越的墙」，而是「一个需要翻译的约束」

**⭐ 这是我认为整件事的核心洞察。**

**OpenBSD 的 `%gs` 政策是对的 —— 它消除了一整类推测性侧信道攻击面。** **而通常的做法是「所以这个 port 做不了」。**

**但 Andrii 做的是：把这条安全决策的**语义**提取出来，然后在不违反它的前提下重新实现它需要的功能。**

**—— 具体来说：** **OpenBSD 说不许用户态设 GS base，那么 Windows 的「TEB 在 GS:0x30」这个语义就必须在**已经固定**的 GS 下模拟出来。** **既然 GS 永远是 0，那访问 `%gs:0x30` 就是访问零页 → 必然触发页错误 → 而页错误处理器是一个完美的「我在这里」的信号源。**

**⭐ 换句话说：** **「GS 恒为 0」这个安全约束，非但没有阻止移植，反而提供了一个可靠的陷阱信号，让「运行时指令重写」成为可能。**

**这是我在这个故事里看到的最漂亮的一次「把约束变成机会」。**

### 10.2 三级回退是一种「成本可预测」的工程方法

**⭐ Andrii 的三级策略（改写 / stub / SIGSEGV）本质上是一套「按指令形态选择最便宜实现」的机制：**

- **最常见的形态**（`NtCurrentTeb()`）→ **零成本改写**；
- **绝大多数 5 字节以上的指令** → **一次跳转**；
- **极少数短指令** → **付一次信号往返**。

**—— 这不是「先做个能跑的版本」，而是一个从一开始就**按成本分档**的设计。** **这在移植工作里特别重要，因为它让你知道「最坏情况有多坏」。**

### 10.3 ⭐ 而「报告覆盖边界」是这个故事里最该被学走的习惯

**Andrii 的 patch 注释里那几句：**

> **「支持 0x67 前缀（32 位寻址模式），但 moffs 指令除外。**'
> **「其他不支持的前缀未被检测到会与 `%gs` 一起由已审阅的编译器生成。」**

**⭐ 以及那句：**

> **「这段代码是根据 LLM 生成的指令解码图手工编写的。指令列表由 LLM 提供，并用规范人工核对过。」**

**—— 三句话分别做了三件事：** **说清支持什么、说清不支持什么、以及**明确区分「我没找到反例」和「我证明了没有反例」**。**

**⭐ 而这一点和 NVIDIA OpenShell 的 policy prover 恰好形成一组对照：**

**—— 两天之内，本号要写的两篇文章，一个是「我检查不了的东西会明确报 `unsupported`」，一个是「我覆盖的边界会明确写下来」。**

**⭐ 而这两个项目、两种风格、两种领域，却共享同一个内核品质：**

> **明确说出「我不知道」比假装「我都覆盖了」更有价值。**

## Sources

- openbsd/ports：emulators/wine（Makefile、44 个 patch、提交历史）：https://github.com/openbsd/ports/tree/master/emulators/wine
- openbsd-ports 邮件列表原始讨论（Thomas Frohwein 的移植提案，2026-10-18）：https://marc.info/?l=openbsd-ports&m=179236125692175
- 回复 1（Bryan Steele）：https://marc.info/?l=openbsd-ports&m=179236426893591&w=2
- 回复 2（Martijn van Duren，列出可运行的游戏）：https://marc.info/?l=openbsd-ports&m=179240622622831&w=2
- 回复 3（Stuart Henderson，关于 clang 头文件与上游合并）：https://marc.info/?l=openbsd-ports&m=179240650723110&w=2
- openbsd-tech：Question - %gs support on OpenBSD（2026-09-29）：https://marc.info/?l=openbsd-tech&m=179067466617674&w=2
- openbsd-tech：Re（Story 的解释与自我更正）：https://marc.info/?l=openbsd-tech&m=179069358537094&w=2
- clang PE 头文件仓库：https://thfr.gothub.org/wine-clang-pe-headers
- Discover BSD 转载：New OpenBSD Port Proposed for Wine：https://discoverbsd.com/p/b82c0a61ca
- OSnews 转载：Wine ported to OpenBSD, runs modern Windows games：https://www.osnews.com/story/146195/wine-ported-to-openbsd-runs-modern-windows-games/

---

（说明：所有 patch 代码、提交信息、Makefile 内容、邮件列表引述均为实测一手材料；第 5.3 节引用的 patch 注释中关于 LLM 参与的表述为 Andrii Yukhymchak 原文；第九节「十四年的距离」一节依据的是实测的 ports 提交历史；第十节的三点归纳为笔者观点。）
