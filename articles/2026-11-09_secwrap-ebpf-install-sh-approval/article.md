---
title: "secwrap 审 curl | sh：eBPF 比 strace 多做了什么"
date: 2026-11-09
slug: secwrap-ebpf-install-sh-approval
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：noboruma/secwrap v0.4.1 源码（netmon.bpf.c / filemon.bpf.c / execmon.bpf.c / secwrap.bpf.c 的 SEC hook 声明、ask.go / freeze.go / caps.go 的实现注释、README 的 Requirements 与 attach 局限）＋ 官方 release 二进制的 SHA256 校验 ＋ 本机实测（内核 7.2.15-x64v3-xanmod1、BTF、BPF LSM、cgroup v2，sudo 下依次跑 cap / --log-only / --net deny）＋ Reddit r/linuxadmin 原帖与 r/eBPF 原帖 ＋ 调研报告 research-work/REPORT-zh.md"
original_date: 2026-11-09
original_url: "https://www.reddit.com/r/linuxadmin/comments/1xqyiew/secwrap_run_your_binary_securely_by_leveraging/"
description: "本文以 secwrap（noboruma/secwrap v0.4.1）为引子，讲清楚一件事：把 eBPF 当「交互式防火墙」用，到底比 strace 这类 ptrace 包装多做了什么。作者在 r/eBPF 的原帖里把动机写得很直白：很多方案是「把进程隔离起来」，但这在很多场景不方便，而不方便的时候人们就放弃了，直接跑程序听天由命 —— 于是「那个 ./install.sh 真的安全吗？」就成了 secwrap 的起点：拦截网络、文件、exec，暂停进程问你，或者记录下来事后审计，或者直接拒绝。本文逐条核对了源码里的 SEC hook：网络观测用 kprobe/tcp_connect、kretprobe/inet_csk_accept、kprobe/udp_sendmsg 与 udpv6_sendmsg；阻断用 cgroup/connect4,6、cgroup/sendmsg4,6 与 cgroup_skb/egress,ingress；文件与 exec 用 BPF LSM 的 lsm/file_open 与 lsm/bprm_creds_for_exec；进程树跟踪用 tp_btf/sched_process_fork 与 sched_process_exit。ask 模式的机制是 seccomp filter 把 connect/sendto/sendmsg/sendmmsg 变成 SECCOMP_RET_USER_NOTIF 挂起，再用 cgroup v2 的 cgroup.freeze 冻住整个进程树（不发 SIGSTOP、shell 里不显示 Stopped），答案进 BPF allow map 后由 cgroup hook 在内核里执行 —— ask.go 的注释还诚实写明：TOCTOU 改写 sockaddr、io_uring、32 位/x32 syscall 拿不到提问，但它们同样到不了未被允许的 peer。**这是与 strace 的根本分野：strace 是「观察并转述」，eBPF hook 是「在内核里执行判定」**，所以静态二进制、裸 syscall、io_uring 都覆盖。本文附本机实测（cap 四维全可用；--log-only 记录到 printf 的 exec 与动态链接器 open；--net deny 把 DNS 的 4 次 UDP 查询与 1 次 TCP 连接全部拦成 EPERM），并如实列出局限：要 root、≥5.19 + cgroup v2 才能 ask、BPF LSM 才能管文件与 exec、attach 的 ask 在这版没接线、允许写立即写入不可撤销、3 星单人项目。"
published: true
---

> 原帖：r/linuxadmin《secwrap: run your binary securely by leveraging eBPF observability》（作者 u/noboruma，2026-11-09）
> 原帖链接：<https://www.reddit.com/r/linuxadmin/comments/1xqyiew/secwrap_run_your_binary_securely_by_leveraging/>
> 原文（r/eBPF 首发帖）：<https://www.reddit.com/r/eBPF/comments/1xqwlox/secwrap_run_your_binary_securely_by_leveraging/>
>
> 本文依据 v0.4.1 源码、官方 release 二进制的校验和、本机实测输出，以及调研报告。

## 一、这个项目的起点是「不方便，所以干脆不设防」

作者在 r/eBPF 的首发帖里把动机写得很朴素：

> 我在网络安全这行做了一段时间，一直对「可观测性与安全缺乏简单工具」感到沮丧。eBPF 自然是现在补这个缺口的东西。
>
> **很多方案是把进程隔离起来跑**，这当然有用，但有很多场景并不方便。**而人们在不方便的时候会怎么做？他们放弃，然后直接跑程序、听天由命。**
>
> 比如说，那个 `./install.sh` 真的安全吗？**在运行这类命令之前，能不能切进「控制狂模式」？**

这就是 secwrap 要解决的：拦截网络、文件、执行三种动作，**暂停进程问你**、或记录供事后审计、或直接拒绝。用法是：

```sh
secwrap -- ./install.sh          # 默认 ask：每遇到新连接/写/exec 就暂停问
secwrap --log-only -- make       # 全记录不打断（适合 CI）
secwrap --net deny --fs off --exec off -- ./untrusted
```

**「不方便，所以干脆不设防」这句话，比这个工具本身更值得记。** 它解释了为什么「静态沙箱」这条路在很多场景里推不动 —— Firejail、bubblewrap、Landlock 都是**事前定策略**，而人面对一个来路不明的安装脚本时，既没有策略也不知道该定什么。

**secwrap 赌的是另一条路：不要求你事先知道，只要求你在它发生的那一秒点个头。**

## 二、先看门槛：一台机器能不能跑，是内核说了算

我把官方 v0.4.1 的静态二进制下下来校验了 SHA256（与 release 的 `.sha256` 一致），然后在这台机器上跑 `secwrap cap` —— **这是唯一不需要 root 的子命令**：

```
Linux 7.2.15-x64v3-xanmod1 (x86_64)
  network     log ask deny
  filesystem  log ask deny
  exec        log ask deny
  sbom        yes
```

逐条核对背后的内核条件：

| 条件 | 本机实测 | 为什么需要 |
|---|---|---|
| 内核 ≥5.10 + **BTF** | 7.2.15，`/sys/kernel/btf/vmlinux` 6.4 MB | CO-RE 重定位，eBPF 才能跨内核版本加载 |
| **cgroup v2** + ≥5.19 | `cgroup2fs` | `ask` 要用 `cgroup.freeze` 冻结进程树 |
| **BPF LSM** | `/sys/kernel/security/lsm` = `capability,landlock,lockdown,yama,bpf` | 文件与 exec 的 hook 挂在 LSM 上 |
| `CONFIG_BPF_LSM=y` / `BPF_JIT=y`（ALWAYS_ON）/ `DEBUG_INFO_BTF=y` / `CGROUP_BPF=y` | 全部 `y` | BPF LSM 程序需要 64 位内核带 JIT trampoline |
| **root** | 需要 | 加载 eBPF |

**这里有个容易踩的细节**：`secwrap` 自己会调 `sudo` 提权加载 eBPF，而**被运行的命令仍以你自己的 uid/组/环境跑**（除非你自己 `sudo secwrap`）。我这次直接用 `sudo /tmp/secwrap`，所以实测事件里的 `uid` 是 0 —— 这是调用方式决定的，不是工具的默认行为。

**还有一个实测发现**：连 `secwrap --version` 都会触发 sudo。只有 `cap` 和 `--help` 是纯免 root 的。对一个想「先看一眼再决定要不要装」的人来说，这个边界值得知道。

**而 README 里的 `cap` 示例是一台 armv7l 降级机器**（fs/exec/sbom 全 unavailable，只能管网络）—— 把它和本机输出并排看，正好说明了这套能力**完全由内核配置决定，不由工具决定**。

## 三、源码里的 hook 表：三层观测、一层执行

我逐个读了 `internal/monitor/*.bpf.c` 的 `SEC()` 声明。这是全文最硬的部分：

| 文件 | Hook | 管什么 |
|---|---|---|
| `netmon.bpf.c` | `kprobe/tcp_connect` | TCP 主动连接观测 |
| | `kretprobe/inet_csk_accept` | TCP 被动接受观测 |
| | `kprobe/udp_sendmsg`、`kprobe/udpv6_sendmsg` | UDP 发送（含 DNS、QUIC） |
| | `cgroup/connect4`、`cgroup/connect6` | **阻断** inet connect |
| | `cgroup/sendmsg4`、`cgroup/sendmsg6` | **阻断** UDP send |
| | `cgroup_skb/egress`、`cgroup_skb/ingress` | 兜底丢包（原始套接字、ICMP、入站） |
| `filemon.bpf.c` | **`lsm/file_open`** | 每次文件 open |
| `execmon.bpf.c` | **`lsm/bprm_creds_for_exec`** | 每次 execve |
| `secwrap.bpf.c` | `tp_btf/sched_process_fork`、`sched_process_exit` | 跟踪整个进程树 |

**注意这里有个很干净的分工**：`kprobe` 负责**看**，`cgroup/*` 与 `cgroup_skb/*` 负责**拦**。而 `lsm/*` 这两个是 **BPF LSM** —— 不是探测点，是内核安全模块里的**决策点**，返回值直接决定这次 open/exec 能不能过（execmon 里 `ret = -1` 就是 `-EPERM`）。

源码注释里还有一句很实在的边界说明：

源码注释的大意是：deny 模式挂在 secwrap 自己的 deny cgroup 上，**里面只装被监控的进程**；每一次 inet connect / UDP send 都被拒绝（syscall 返回 EPERM），其它报文（原始套接字、ICMP、入站）只要不是与已放行 peer 通信，就丢弃并计数。

**「只挂在装着被监控进程的 cgroup 上」** —— 这解释了为什么它不会误伤同一台机器上的其它进程。而 `deny` 的实现是把进程挪进 `secwrap-deny-<pid>` 这个子 cgroup，创建在它原本所在的 cgroup 之下，**所以原有的容器或 systemd unit 资源限制仍然生效**。

## 四、`ask` 是怎么把 syscall「挂起」的

这是整个工具最巧的一块，也是它和 strace 拉开差距的地方。

`internal/monitor/ask.go` 的头部注释写得很清楚：

`ask.go` 的头部注释大意：ask 就是「deny 模式 + 在出站网络 syscall 上加一个交互式断点」。目标进程装上一个 **seccomp filter，把 `connect`、`sendto`、`sendmsg`、`sendmmsg` 变成 `SECCOMP_RET_USER_NOTIF`**；**调用线程会一直阻塞在内核里，直到我们给出回答** —— 允许就把该 peer 写进 BPF allow map 并让 syscall 继续，拒绝就返回 EPERM。

**关键词是 `SECCOMP_RET_USER_NOTIF`**：这是 seccomp 的用户态通知机制，内核把 syscall 挂起、交给用户态的 supervisor 决定。线程**停在内核里**，不是被信号暂停。

然后 `freeze.go` 解释为什么还要 cgroup v2 freeze：

`freeze.go` 的注释大意：在终端上弹出问题的这段时间里，把被启动命令的整棵进程树冻住 —— **在得到回答之前，树里没有任何东西能读键盘、或对 secwrap 接管终端作出反应**。而 cgroup v2 freezer **对进程及其父进程是不可见的：不发 SIGSTOP，shell 里也不会出现一个 Stopped job**；被冻结的阻塞读在解冻后会重新开始。

**这一句解释了两个设计的必要性**：

1. 被挂起的线程停在内核里，但**同一进程树的其它线程还在跑** —— 它们可能来抢终端、刷屏、甚至读键盘。所以要把整棵树冻住。
2. 用 `cgroup.freeze` 而不是 `SIGSTOP`，是因为 SIGSTOP 会让 shell 显示一个 Stopped job，而且对进程的父进程可见 —— 太吵。

`caps.go` 里的判定也很直白，把两个必要条件写死了（注释还特意说明「不提供只挂起不冻结的 ask」）：

```go
// canAsk: ask pauses the call with seccomp and freezes the command while
// the question is up. Asking without freezing isn't offered.
case !c.SeccompNotif:  return false, "no seccomp user notifications"
case !c.Freeze:        return false, "ask needs cgroup v2 and Linux 5.19+ to freeze the command"
```

**作者明确不提供「只挂起不冻结」的模式** —— 挂起与冻结被绑成一个不可拆的组合。

### 我认为最值得记的是 ask.go 里的这段边界说明

> **seccomp only pauses the call.** The cgroup BPF hooks (deny.go) still enforce the decision on the address the kernel copied. **A thread that rewrites the `sockaddr` after we read it (TOCTOU), io_uring, or 32-bit/x32 syscalls get no prompt, but they still cannot reach a peer that was not allowed.**

（**这是全文我唯一想原样保留的英文** —— 因为它一句话讲清了整个安全模型：seccomp 只负责**把调用挂起来问人**，cgroup BPF hook 才在内核实际拷贝的地址上**执行判定**。所以改写 sockaddr 的 TOCTOU、io_uring、32 位/x32 syscall **拿不到提问，但同样到不了未被允许的 peer**。文件侧同理：`open/openat/openat2/creat` 被 trap，答案写进 BPF `file_rules` map，最终由 **LSM `file_open`** 在真正被打开的那个文件上强制执行。）

**「拿不到提问，但同样到不了未被允许的 peer」** —— 这句话是整个安全模型的关键。

它承认了一件事：**seccomp 通知不是一个可靠的强制点**（TOCTOU 可以绕过它读到的地址，io_uring 根本不走被 trap 的 syscall，32 位 ABI 也不在 filter 里）。所以作者把**提问**和**强制**分成了两层：

- **提问层**（seccomp user notif）：负责「让人有机会说 yes/no」，可以漏，漏了就按默认拒绝处理；
- **强制层**（cgroup BPF + BPF LSM）：在内核里对**实际发生的动作**执行判定，不可绕过。

**这是「用户体验」和「安全边界」解耦的一个很好的例子。** 很多工具会把两者混在一个 hook 上，结果要么漏了强判，要么问答体验很差。

## 五、这就是「eBPF 比 strace 多做了什么」

标题里那个问题的答案，现在可以完整回答了。

`strace` 走的是 **ptrace**：它 attach 到进程，在每次 syscall 的进出各停一次，然后把参数和返回值**转述**给用户。它的性质是**观察**。

而 secwrap 的 hook 在**内核里**：

| 维度 | strace（ptrace） | secwrap（eBPF hook） |
|---|---|---|
| 谁停下来的 | 被跟踪进程被信号式暂停在 syscall 边界 | 线程被 `SECCOMP_RET_USER_NOTIF` 挂在内核里 |
| 能不能改结果 | **不能**，只能看 | **能**：`allow` map / `EPERM` / 丢包 |
| 静态二进制 | 能看（syscall 层） | 能看也能拦 |
| **裸 syscall** | 能看 | 能拦（kprobe 在内核函数上） |
| **io_uring** | 看不到（没有 syscall 边界） | **拿不到提问，但 cgroup hook 仍拦得住** |
| 32 位 / x32 ABI | 能看 | 拿不到提问，仍拦得住 |
| 进程树覆盖 | 需要 `-f` 逐个跟 | `sched_process_fork` 自动跟 |
| 判定在哪执行 | **用户态（观察后转述）** | **内核态（hook 里直接返回 EPERM / drop）** |

**最本质的差别是最后一行：strace 把信息搬到用户态给你看，eBPF hook 在内核里就把结果定了。**

而 `ask` 模式的巧妙在于：它**用 seccomp 把「问人」这件事搬回用户态**（因为问人必须在用户态），但**把「执行判定」留在内核里**。这就是上一节那段 TOCTOU 说明在讲的事。

**顺带一个实测里能看到的现象**：`--net deny` 那条测试里，curl 的 **DNS 查询被拦了 4 次**。strace 当然也能看到这 4 次 `sendto`，但它只能告诉你「发生了」；而 `cgroup/sendmsg4` 直接让它们全部失败。

## 六、本机实测：cap → --log-only → deny

按你要求的顺序，我在这台机器上依次跑了三步（eBPF 加载需要 root，由你在终端提供 sudo）：

### ① `cap`（免 root）

结果见第二节：四维全部 `log ask deny`，`sbom yes`。内核条件全部满足。

### ② `--log-only`（只记录，不打断）

```
NETWORK:    LOG
FILESYSTEM: LOG
EXEC:       LOG
SBOM:       OFF
Session 20261109-223255-printf: http://127.0.0.1:9000/...
ok[exec] 22:32:55.466 pid=4069985 secwrap  /usr/bin/printf
secwrap: session recorded in ~/.local/state/secwrap/20261109-223255-printf
```

**注意终端只打印了一行 `[exec]`，但落盘的 `events.jsonl` 远不止这些**：

```json
{"kind":"open","path":"/usr/bin/printf","exec":true}
{"kind":"exec","path":"/usr/bin/printf","exec":true}
{"kind":"open","path":"/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2","exec":true}
{"kind":"open","path":"/etc/ld.so.cache"}
{"kind":"open","path":"/usr/lib/x86_64-linux-gnu/libc.so.6"}
```

**一个 `printf ok` 就记下了 execve、动态链接器、ld.so.cache、libc 四层 open** —— 这就是 `--fs` 挂 `lsm/file_open` 之后能看到的东西。终端输出是「摘要」，落盘 JSONL 才是全量。

### ③ `--net deny`（只拦联网，其余 off）

```
NETWORK:    DENY
FILESYSTEM: OFF
EXEC:       OFF
[deny] curl  udp connect -> <内网 DNS>:53 BLOCKED   ×4
[deny] curl  tcp connect -> 127.0.0.1:443 BLOCKED   ×1
curl: (7) Failed to connect to example.com:443 after 0 ms
```

（内网地址已按脱敏要求隐去。）

对应的 `summary.txt`：

```
== network summary: [/usr/bin/curl -sS --max-time 5 https://example.com] (2 endpoints) ==
  outbound udp  <内网 DNS>:53      x4     curl  BLOCKED
  outbound tcp  127.0.0.1:443      x1     curl  BLOCKED
  deny mode: 5 connection/send attempts blocked; other packets dropped: 0 out, 0 in
```

**这里有两个值得说的细节**：

1. **DNS 先被拦，TCP 还没开始就结束了。** 4 次 UDP 到 53 端口全 BLOCKED，说明 `cgroup/sendmsg4` 在解析阶段就生效了 —— 而不是等 connect 才拦。这也解释了为什么 curl 报的是「无法连接」而不是超时。
2. **TCP 目标是 `127.0.0.1:443`**，而不是 example.com 的地址 —— 这是本机透明代理链路的出口，被 `cgroup/connect4` 一起拦了。这类「本机代理」场景恰好是**主机防火墙容易放行、而 secwrap 按进程 cgroup 照样拦**的例子。

**`ask` 模式这次没有跑完整交互链**（需要交互终端逐条回答）；它的机制我按 `ask.go` / `freeze.go` / `caps.go` 的源码逐条核对，上文的描述均出自源码注释，不是推测。这一点在文末如实标注。

## 七、它和同类工具的分工，不在「谁更安全」

README 自己列了一张对照表，我按机制重新整理：

| 工具 | 机制 | 定位 |
|---|---|---|
| Firejail / bubblewrap / Landlock | 静态沙箱，**事前定策略** | 你得先知道要放什么 |
| Tetragon / Falco | 全主机 / 集群监控 | 面向规模，不面向「一条命令」 |
| OpenSnitch | 只管网络 | 单维 |
| **sandlock**（Landlock + seccomp-notify） | 最接近，但**无需 root**、需 6.12、回调里刻意不暴露路径（防 TOCTOU） | 不能让被监控程序提权，有 CoW 工作目录可 dry-run 撤销 |
| **secwrap** | kprobe + cgroup + BPF LSM + seccomp + cgroup v2 freeze | 逐条审批**单条命令** |

**差异化其实是三条**：

1. **能跑真的需要 root 的安装脚本**（`sudo secwrap -- ./install.sh`）—— 内核 hook 跟**进程树**，不跟 uid；
2. 事件带**真实路径 / PID / UID**，可审计也可实时决策；
3. 能 `attach` 已运行进程、能当 login shell。

**代价也很明确**：要 root 和 BPF LSM，而且**允许写就是立即写入、不能回滚**。sandlock 的 CoW 工作目录能 dry-run 撤销，secwrap 不能。

**所以这不是「谁更安全」的比较，而是「你要在哪个时刻做决定」**：静态沙箱要求你事前知道，secwrap 让你在发生的那一秒知道。**后者更贴合 `./install.sh` 这类「我不知道它会干什么」的场景**，但代价是你必须一直在场。

## 八、局限：这些必须写清楚

按你的要求逐条如实列出：

**① 要 root。** 加载 eBPF 需要 root。工具会自己 `sudo` 一次，但**被运行的命令仍以你的 uid 跑**（除非你自己 `sudo secwrap`）。这次实测用了直接 `sudo`，所以事件里的 uid 是 0。

**② `ask` 需要 ≥5.19 + cgroup v2。** 老内核只能 `log` / `deny`，必须显式给模式（`--net log`）或 `--log-only`。`caps.go` 里写死了 `Asking without freezing isn't offered`。

**③ 文件与 exec 需要 BPF LSM。** 检查 `/sys/kernel/security/lsm` 里有没有 `bpf`；没有的话 `--fs` / `--exec` / `--sbom` 会在启动时被拒绝，只有网络还能管（因为网络走 cgroup + kprobe，不走 LSM）。另外 BPF LSM 程序还需要 64 位内核带 BPF JIT trampoline —— **32 位 x86/arm/mips 内核只能管网络**。

**④ `attach` 的 `ask` 在这版没接线。** README 明确写着：`--allow-ask` 被接受并校验，但**暂停运行中进程的 syscall 在本构建里没实现**。而且 attach 后想开 ask，必须给进程永久设 `NO_NEW_PRIVS` —— 从此 `sudo` / setuid 对它和它的子进程全部失效，这是不可逆的。attach 的 `log` / `deny` 可用。

**⑤ 允许写就立即写入，不可撤销。** 这是与 sandlock 最实质的差别。你点了「允许」，文件就写了，没有 dry-run、没有 CoW、没有回滚。

**⑥ `deny` 的 cgroup 可能残留。** `deny` 是靠把进程挪进 `secwrap-deny-<pid>` cgroup 实现的；如果 secwrap 被 `kill -9`，内核会随程序卸载而解除阻断，**但那个 cgroup 会留在原地**，需要手工把 PID 写回父 cgroup 的 `cgroup.procs`。

**⑦ 敏感读不是完整文件审计。** 默认只覆盖「所有写 + 7 类敏感读」（家目录、`/root`、`/etc/shadow`、`/etc/sudoers*`、`/etc/ssh/` 等），`--sensitive` 最多再加 9 条。**普通读既不问也不拦**，只有 `log` 模式才全记。

**⑧ 3 星单人项目、v0.4.1、20 commits、7 个 tag。** 2026-11-05 建，Reddit 两个帖分别是 2 分 0 评论 / 0 分 0 评论。作者写了 `make vmtest`（在 QEMU 里起真内核跑端到端测试），工程态度不错，但这仍是一个四天大的新项目。**本文把它当引子，不是评测。**

**⑨ 隐私边界**：只有哈希会离开机器，且仅当你在网页 UI 里主动点 VirusTotal 链接时。

## 九、和「AI Agent 跑 shell」这件事的关系

报告里把 secwrap 定位在三个支柱的交叉点，我认为最值得展开的是第三个。

**Agent 跑 shell 的审批，现在主流做法是「命令级」**：模型给出一条命令，人点同意/拒绝。但一条 `./install.sh` 里面可能有几十次联网、几百次文件写、若干次 exec —— **你在命令级点的那一次头，覆盖不了它内部发生的任何一次动作**。

secwrap 提供的是另一种粒度：**动作级**。它不是审「这条命令该不该跑」，而是审「它此刻想连这个地址、想写这个文件、想起这个程序，行不行」。

**这个粒度的价值，和缺点是同一个东西**：它让你第一次看见命令内部到底发生了什么（实测里一个 `printf ok` 都有 4 层 open），代价是你必须一直在场回答。所以 `--log-only`（全记录不打断）在 CI / Agent 场景里可能比 `ask` 更实用 —— **先拿到完整的动作清单，再决定要不要给这类命令开白名单**。

而 `ask.go` 那段「拿不到提问但仍拦得住」的设计，恰恰是给自动化场景准备的：**即使没有人在场回答，默认拒绝仍然生效**。

## 十、结论：把机制当主角

这个工具有 3 个 star，四天大，单人维护。**它值不值得装，我不知道，也不该由这篇文章回答。**

但它把几样平时分散在内核文档里的东西，串成了一条能亲手摸到的链路：

- `kprobe` 看、`cgroup/*` 拦、`cgroup_skb` 兜底；
- `lsm/file_open` 与 `lsm/bprm_creds_for_exec` 是**决策点**而不是观测点；
- `SECCOMP_RET_USER_NOTIF` 把线程挂在内核里等一个用户态回答；
- `cgroup.freeze` 让整棵进程树安静下来，且不发 SIGSTOP；
- **提问层可以漏，强制层不能漏** —— 这两件事被刻意分开了。

**这才是 `curl | sh` 那个问题的技术答案**：不是「找个工具替你审」，而是「内核里本来就有可以下判定的位置，只是以前没人把它接成一个问答」。

最后留一个问题给你：如果一个 `printf ok` 都能记下 execve、动态链接器、`ld.so.cache`、libc 四层 open —— **你敢让 AI Agent 直接跑 shell 吗？**

---

## Sources

- noboruma/secwrap v0.4.1 源码（本报告逐条核对 `internal/monitor/*.bpf.c` 的 `SEC()` 声明、`ask.go` / `freeze.go` / `caps.go` 注释、README 的 Requirements 与 attach 局限）: <https://github.com/noboruma/secwrap>
- 官方 release v0.4.1 二进制与 `.sha256`: <https://github.com/noboruma/secwrap/releases/tag/v0.4.1>
- r/linuxadmin 原帖《secwrap: run your binary securely by leveraging eBPF observability》: <https://www.reddit.com/r/linuxadmin/comments/1xqyiew/secwrap_run_your_binary_securely_by_leveraging/>
- r/eBPF 首发帖（含作者动机说明）: <https://www.reddit.com/r/eBPF/comments/1xqwlox/secwrap_run_your_binary_securely_by_leveraging/>
- Ping Identity / Linux 内核文档所述 BPF LSM、cgroup v2 freezer、seccomp user notification 机制（本文按 secwrap 源码注释引述）

### 事实边界说明

- **本机实测**：官方二进制 SHA256 校验通过；`secwrap cap` 输出、内核条件（7.2.15-x64v3-xanmod1、BTF 6.4 MB、`lsm` 含 `bpf`、四项内核 CONFIG、`cgroup2fs`）、`--log-only` 的终端输出与落盘 `events.jsonl`、`--net deny` 的终端输出与 `summary.txt`，均为本机实际运行结果。**内网 DNS 地址已按脱敏要求隐去。**
- **`ask` 模式本次未跑完整交互链**（需要交互终端逐条回答）。本文对 seccomp 挂起、cgroup freeze、allow map、TOCTOU/io_uring/32 位边界的描述，全部出自 `ask.go` / `freeze.go` / `caps.go` 的源码注释与实现，非实测推断。
- hook 表、门槛、attach 局限、deny cgroup 残留、敏感读范围、项目规模：引自 v0.4.1 源码与 README。
- 作者动机引自 r/eBPF 原帖 selftext。
- 「与 strace 的对比」是本文基于两者机制的分析，非原文表述；`strace` 行为按 ptrace 的通用语义描述。
- 「动作级 vs 命令级审批」是本文的解读，secwrap 文档未用此措辞。
- 本文只做防守方视角的机制解读，不构成对该工具的安装或安全背书；**未在一次性 VM 中做隔离验证，加载 eBPF 属会改内核状态的操作，请自行评估后再试。**
