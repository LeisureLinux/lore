---
title: "Rex 开源 OSC 7577：一条转义序列，让终端程序跨重启原地复活"
date: 2026-11-25
slug: rex-osc-7577-program-resume-protocol
category: 技术/解读
author: FreeLAMP.com
original_source: "Superlogical 官方《Program Resume Protocol (OSC 7577)》规范与 Rex《Resume Rules》文档（superlogical.com/rex/docs/build/program-resume、/rex/docs/customize/resume-rules）＋ Mitchell Hashimoto 2026-11-25 发布帖（与 Herdr 协作、多家终端作者审阅）。"
description: "解读 Mitchell Hashimoto 今天开源的 OSC 7577 终端程序恢复协议与 Rex 的实现：最原始的 OSC 转义序列上报 argv/pid/time/mac，终端验证后存为 record，重启后按规则重跑命令。讲清 token（OSC7577_TOKEN）如何防住 cat 文件和 ssh 远程输出伪造恢复指令、SHA-256 mac 为何不是 HMAC、time 60 秒窗口与 pid 生命周期管理、argv 严格按数据传递不经 shell 解析、Rex 的 Lua 白名单（command/flags/dir）、内置 Claude Code/Codex/OpenCode 规则与一行关闭开关。也点明边界：恢复的是命令而非进程现场，环境变量、shell 状态、飞行中的工具调用都不回来。"
published: true
---

服务器重启了，那个跑了几个小时的 Claude Code 会话还能原地复活吗？

11 月 25 日，Ghostty 创作者 Mitchell Hashimoto 给出了一个新答案：他所在的 Superlogical 开源了 **OSC 7577（Program Resume Protocol）**——一条终端转义序列，让程序自己告诉终端「怎么把我重新启动」。Rex 已经内置 Claude Code 的支持，规范与 Herdr 协作完成，并经过多家终端模拟器和终端程序作者审阅。

## 一、不依赖任何私有通道，就是一条 OSC 序列

现有做法要么靠 tmux/screen 这种嵌套终端（嵌套终端自己结束时问题照旧），要么靠硬编码名单、进程名匹配、或者绕开 pty 的私有 RPC。OSC 7577 的路线是：**程序知道自己怎么恢复，那就由程序通过它本来就有的 pty 告诉终端**，终端决定是否在重启后照做。

一条典型的报告长这样（Neovim 存好 session 文件之后）：

```
ESC ] 7577 ; pid=74877:time=1795543200:argv=bnZpbQ==,LVM=,...:mac=9dbb99bf... ESC \
```

`argv` 的 base64 解码后是 `nvim`、`-S`、`/home/user/.local/state/nvim/sessions/8f2c1d.vim`。整条序列只有 `key=value` 对，用冒号分隔，值域排除了 `:` 和 `;`，所以不需要转义；最后一个键必须是 `mac`。

必填项是 `pid`（归属进程）、`time`（Unix 秒）、`mac`（校验值）；可选项包括 `argv`（恢复命令，base64 数组）、`cwd`（工作目录）、`clear`（撤销之前的记录）、`need`（声明终端必须支持的扩展键）。解析是**严格**的：值不合法、键重复、缺必填项、base64 解不开、解码后不是合法 UTF-8 或含控制字符，整条报告直接拒收。

## 二、安全是重点：token 让 `cat` 文件和 ssh 输出无法伪造恢复

终端程序恢复天生有个信任难题：终端弹出一条可执行命令，这条命令是本地程序说的，还是 `cat` 出来的某个文件里藏的转义序列？

规范的解法是**能力凭证**——终端在每个 pty 的第一个进程环境里注入一个随机 token：`OSC7577_TOKEN`（22～64 个字符，必须是密码学随机源生成，不能是计数器、时间或 PID）。程序计算 `mac` 时用它，但**永远不会把 token 发出去**：

```
mac = SHA256( 报告中 mac= 之前的全部原始字节 + ":" + token )
```

终端收到报告先算 hash 比对，不对就当没看见。这一下就把威胁模型的边界画清楚了：

- `cat` 一个文件、tail 日志、ssh 远端程序的输出——**都拿不到 token，注册不了恢复记录**；
- 会话录制工具录下的原始输出里没有 token，回放旧报告最多在原报告的 60 秒 `time` 窗口内生效，过期作废；
- 同一用户或 root 启动的程序能读到 token（Linux 上 `/proc/<pid>/environ`），规范**明确不防这个**——那本来就是用户已经信任要执行的代码。

故意不用 HMAC 也有讲究：规范说 HMAC 常用实现方式会把密钥放到命令行上被别的用户看到，而普通 SHA-256 配 `sha256sum` 走标准输入就行；token 放在末尾，是为了让知道一个 `mac` 的人推不出更长 body 的 `mac`。

`time` 除了防重放，还有一层顺序保证：终端必须忽略同一 `pid` 时间戳早于已接受报告的报告。`pid` 则主要用于**生命周期**：进程正常退出后记录自动清除（但关机前一两秒的退出算「还在」，免得恢复不了），PID 被复用时靠进程启动时间识别。`need` 键给未来扩展留了门：终端不支持某个必需键就必须拒绝报告，而不是悄悄忽略后按旧语义恢复。

## 三、恢复时执行的是命令，不是「进程快照」

这一步的安全细节同样多：终端把 `argv` 的每个元素**原样**作为一个参数传给程序，绝不拼成 shell 源码重新解析——参数里的 `$(reboot)` 或 `a; b` 就是普通文本。临时把 shell 函数/内建（比如 `eval`）压过 PATH 里真程序的花招也要挡掉。恢复命令以**原用户身份**运行，用户变了就丢弃记录；保存记录文件和 shell 启动脚本一样敏感，其他用户不能读写。

关于「原样复活」的实际边界，规范写得很直白：

- 环境变量**不保存也不恢复**——恢复时拿到的是终端新起 shell 的环境，需要特定值的程序应当把它们写进 `argv`；
- 恢复的是一个全新进程，终端模式、alternate screen、鼠标/键盘模式等状态不会回来；shell 变量、历史、stopped jobs 都不恢复；
- 飞行中的工具调用和 socket 不会跟着复活——重启后只是把上报的 argv 在一个新 shell 里重跑，所以**恢复命令必须可以安全地跑第二次**；
- 工作目录按 `cwd` → 操作系统读到的进程目录 → OSC 7（无 token 保护，默认不信任，需 opt-in）→ 新 shell 默认目录的顺序取；`cwd` 指明的目录已不存在时，终端不应恢复。

## 四、Rex 的一侧：Lua 白名单，逐程序 opt-in

协议只定义了「程序如何声明自己可恢复」，「信不信」由终端自己决定。Rex 的做法是三层白名单，每条规则由三部分组成：

| 部分 | 作用 |
|------|------|
| `command` | 恢复命令的开头，如 `claude --resume <uuid>` |
| `flags` | 允许哪些参数、哪些参数在恢复时保留 |
| `dir` | 允许在哪些目录里恢复 |

Rex 拿程序上报的命令跟用户规则交叉核对，**以规则为准**，而且会做自己的检查：进程必须真是那条命令启动的程序（`claude` 和 `/opt/homebrew/bin/claude`、`node /opt/homebrew/bin/claude` 都算 claude，npm 装的 Claude Code 就是这样跑的），跑在 sandbox 之类的程序下面的不算——只恢复命令会把 sandbox 丢掉。

内置规则覆盖 Claude Code、Codex、OpenCode。Claude 规则保留 `--model`、`--permission-mode`、`--dangerously-skip-permissions` 这类塑造会话的参数，丢掉 `--continue` 这类「选会话或起任务」的参数（恢复由 `--resume` 负责）；用 `--print` 起的 Claude Code 不恢复。规则可以改，例如只允许在 `~/code` 下恢复：

```lua
rex.set("resume.trust.claude.dir", "~/code")
rex.set("resume.trust.codex", false)
```

一条 `rex.set("resume.defaults", false)` 就能关掉全部内置规则。Rex 还自带 Claude Code 支持——通过 session start hook 发出 OSC 7577 报告。

## 五、它和 OSC 7501 是同一个故事

这套设计延续了 Hashimoto 上个月发布的 **OSC 7501（Program Status Protocol）**：程序通过 pty 用转义序列告诉终端自己在忙、在等用户、已完成还是失败；Rex 把它显示成 tab 上的指示器。两个协议都是「终端原生、通用、无产品专有字段」，都从 libghostty 和 Rex 两侧实现过。

真正的价值不在某个终端多炫的功能，而在生态接口：程序只要几行代码发出一条转义序列，任何支持协议的终端都能恢复它。它不会让 tmux 消失——但至少，「服务器重启后程序还能不能回来」这个问题，第一次有了跨终端、跨程序的标准答案。

## 参考资料

- Superlogical 官方 OSC 7577 规范：https://www.superlogical.com/rex/docs/build/program-resume
- Rex Resume Rules 文档：https://www.superlogical.com/rex/docs/customize/resume-rules
- Mitchell Hashimoto 发布帖（2026-11-25）：https://x.com/mitchellh/status/2125713695233970521
- 此前 OSC 7501 协议介绍：https://mitchellh.com/writing/program-status-osc7501
