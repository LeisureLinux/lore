---
title: "Bash 并发命令队列：用 mkfifo 加 xargs -P 造一个线程池"
date: 2026-11-14
slug: bash-concurrent-shell-command-queues
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Christian Emmer《Concurrent Shell Command Queues》（emmer.dev，页面标注 2026-11-07 / 正文 Nov 6, 2026，10 min read；含 queue_start / queue_submit / queue_wait / _queue_stop 四个函数完整源码与逐行注释、Postman Echo 的 5 个并发 curl+jq 示例及输出、Known issues 五条、Why not just xargs -P 章节标题）＋ 文中引用的 man7 mkfifo(1) 与 GNU xargs 语义 ＋ 相关背景：GNU Parallel、Bash job control、FIFO/PIPE_BUF 行为（本文按通用 Unix 语义说明，未另引第三方资料）"
original_date: 2026-11-06
original_url: "https://emmer.dev/blog/concurrent-shell-command-queues/"
description: "解读 Christian Emmer 的《Concurrent Shell Command Queues》：如何在 Bash/Zsh 里做一个可随时提交命令、限制并发数的线程池，而且不需要事先知道全部命令。文章拆四个函数：queue_start 校验并行度为正整数、在 3–9 里找空闲文件描述符、用 mktemp -d 建私有临时目录并 mkfifo 出队列文件、用 ps 取当前 shell 名、后台起 xargs -0 -n1 -P N 读 NUL 分隔命令、把 stderr 经 fd 副本转给 xargs 的真实 stderr、关掉 job control 隐藏 job 消息、打开写端等待读端就绪后立刻删目录、注册 EXIT/HUP/INT/TERM trap；queue_submit 用 env printf '%s\\0' 把命令写进 fd，交互 shell 前台写、非交互后台写再 wait，以免满队列时延迟信号 trap；queue_wait 关写端、轮询 kill -0 等 xargs 退出；_queue_stop 递归 pgrep -P 找后代，先 STOP 再递归 TERM 最后 CONT，保证 zsh 行为接近 bash。解释几个精妙点：命令输出先捕获再打印以避免交错、把非零退出码统一压成 1 因为 255 会让 xargs 停下、FIFO 两端都打开后即可 unlink、写端被子进程继承使 subshell 也能提交。也原样列出作者自认的五条 Known issues：一个 shell 只能有一个队列、输出不流式且超过 PIPE_BUF 仍可能交错、queue_wait 不返回任务失败、必须等 queue_start 之后启动的进程都关掉写端、_queue_stop 会无差别杀掉其他后台任务。给 Postman Echo 的 5 并发示例，并写明作者自己的忠告：用 Python 之类语言通常更合适，做这个纯属喜欢 Bash 与挑战。结论：这是一份难得的「防御式 shell 编程」样本，价值在于把 fd 生命周期、信号、进程树、退出码这些边界显式处理了一遍；生产环境应优先用成熟工具。"
published: true
---

11 月 6 日 Christian Emmer 发了篇很「 不必要但漂亮」的文章：能不能在 Bash 里做一个线程池？要求还挺具体 —— 命令不必事先全知道，可以随用随提交；同时并发数要受控。

他自己先把话说在前面：Bash 的并发控制很弱，这事儿「用 Python 之类语言通常更合适」，做它纯粹因为喜欢 Bash、想挑战一下。然后给出了一份百来行、写满防御性注释的实现。我觉得值得拆的正是这些注释。

## 一、要解决的到底是什么

普通做法有两种，都不合需求：

- `&` 一串全扔后台，简单但没有并发上限，几千个 curl 能把机器打满；
- `xargs -P N` 很适合限制并发，但它通常要求一次性把输入喂完，不适合「跑着跑着再追加几条命令」的场景。

作者要的是第三条：一个常驻的队列 + 一个固定大小的消费者池，随时 `queue_submit`，最后 `queue_wait` 收尾。

## 二、四个函数怎么配合

`queue_start N` 负责起整套东西，步骤最密：

1. 校验 `$1` 是正整数（用 `[[ =~ ^[1-9][0-9]*$ ]]`），否则报错返回 1；
2. 若本 shell 已有 `_queue_fd`，先关掉旧写端、清变量 —— 保证一个 shell 不残留两套；
3. 在 fd 3 到 9 里找第一个没被占用的（注释说明 9 是 zsh 重定向上限），找不到就报错；
4. `mktemp -d` 建私有临时目录，`mkfifo` 在里面造队列文件；
5. 用 `ps -o comm= -p $$` 拿到当前 shell 的名字，好让 `xargs` 用同一个 shell 执行每条命令；
6. 把该 fd 先 `>&2` 复制一份作 stderr 通道，然后 `set +m` 关掉 job control，后台启动：

```
xargs -0 -n 1 -P N "$shell" -c '...' _ < "$dir/queue"
```

`-0` 读 NUL 分隔、`-n 1` 每次一条、`-P N` 就是并发上限。命令体里把输出先 `out=$(eval -- "$1" </dev/null 2>&1)` 捕获再打印，避免多个任务的输出逐行交织；并把所有非零退出码统一压成 1 —— 注释点破原因：255 会让 xargs 直接停下，不能让一条失败命令把整个队列带崩。

7. 关键一步：`exec ${fd}>"$dir/queue"` 打开写端。FIFO 的 open 会阻塞到读端（xargs）也打开为止；两端都打开之后目录就可以 `rm -rf` 了，队列仍通过已打开的 fd 活着。这比留个临时文件再清理干净得多。
8. 注册 `EXIT` / `HUP` / `INT` / `TERM` trap；对 zsh 额外 `setopt localoptions posixtraps`，让它行为接近 bash。

`queue_submit` 提交命令 用 `env printf '%s\0' "$1" >&${_queue_fd}` 往 fd 写一条 NUL 结尾的记录。两个细节：用 `env printf` 是为了「万一 xargs 已经退出，被 SIGPIPE 干掉的是 printf 而不是当前 shell」；交互 shell 前台写、非交互 shell 后台写再 `wait $!`，因为队列满时前台写会延迟 HUP/INT/TERM trap。

`queue_wait` 关掉写端（`exec ${fd}>&-`），然后每 0.1 秒 `kill -0 $_queue_pid` 轮询，等 xargs 把手上任务跑完退出，最后清掉变量。作者注明这一步可选：`queue_submit` 一提交，命令其实就开始跑了。

`_queue_stop` 是最硬核的一段：递归 `pgrep -P` 找后代进程，对每个先 `kill -STOP` 冻结（防止它继续 fork）、递归处理它的子进程、再 `TERM`、最后 `CONT` 让它能响应终止。目的是在脚本退出时把后台链条清干净 —— 否则这些进程忽略 Ctrl-C、收不到 TERM。

## 三、跑起来是什么样

作者原本的场景是批量发 Web 请求，示例用 Postman Echo 发 5 个 POST 并用 jq 取回显：

```
queue_start 3
for n in 1 2 3 4 5; do
  queue_submit "set -o pipefail; \
    curl -sS --fail-with-body --max-time 10 -X POST -H 'Content-Type: application/json' \
      -d '{\"request\": ${n}}' \
      https://postman-echo.com/post | \
    jq -c .json"
done
queue_wait
```

输出是 5 行 `{"request":1}` 到 `{"request":5}`，最多 3 个并发。注意 `set -o pipefail` 写在提交的命令里 —— 队列只负责编排，正确性还是靠提交者自己保证。

## 四、作者自己列的五条已知问题

这部分比代码更该读，因为它划清了「能用到什么程度」：

1. 一个 shell 只能有一个队列（支持多个的额外复杂度不值得）；子 shell 可以有自己的队列。
2. 输出刻意不流式，为的是不交错；但超过 `PIPE_BUF` 的输出仍可能交错 —— 原子写只保证到那个长度。
3. `queue_wait` 不返回是否有任务失败；要做就得加临时文件或第二个 fd，代码复杂度上升。
4. `queue_wait` 得等 `queue_start` 之后启动的所有进程：那些进程会继承写端 fd（也正是 subshell 能提交的原因），只要还有一份没关，xargs 就看不到 EOF。
5. `_queue_stop` 无差别杀后代：在 `queue_start` 之前就启动的后台任务也会被一起 TERM。

作者最后还坦白：「我有把握它仍存在难以预测或难以避免的失效模式。」写 shell 的人看到这句大概都会会心一笑。

## 五、为什么值得读

这份代码的价值不在「以后大家都用 Bash 写线程池」—— 作者自己都劝你换语言。它更像一份防御式 shell 编程清单，把平时容易糊过去的边界全显式处理了：

- fd 从哪来、何时复制、何时关、为什么可以提前 unlink；
- FIFO 两端打开的同步语义；
- job control 消息、后台进程收不到终端信号、zsh 与 bash 的 trap 差异；
- 进程树递归终止时先 STOP 再 TERM 再 CONT 的顺序；
- xargs 对 255 退出码的特殊反应、`PIPE_BUF` 与输出交错；
- 写端被继承既是特性（subshell 可提交）也是坑（EOF 迟迟不来）。

真要上生产，成熟工具更稳：简单批处理用 `xargs -P`，需要排队、重试、结果汇总、超时控制的用 GNU Parallel 或直接用 Python 的 `concurrent.futures` / asyncio，作业编排交给 CI 系统或任务队列。但在「一台机器上临时加速一批命令、又不想引入依赖」的场景里，这一百来行确实能跑，而且把该踩的坑都写在了注释里。

## 六、边界

- 本文依据作者博客原文与其中代码注释；未在本机复现该脚本、未测试 Postman Echo 示例，也未验证 zsh 下的 `posixtraps` 行为。
- 页面元数据显示 2026-11-07、正文标注 Nov 6, 2026，本文按正文日期标 `original_date`，两者差异按出处保留。
- 「Why not just `xargs -P`?」在抓取内容里只出现章节标题，正文未完整取得，因此本文对该节的解读属于基于其余代码的归纳，不冒充作者原话。
- `PIPE_BUF`、`mkfifo`、xargs 退出码等按通用 Unix 语义解释，未逐条引 man page 原文。

## 七、结论

一句话概括：用 `mkfifo` 当可追加的命令管道，用 `xargs -P` 当固定大小的工人池，用 fd 生命周期与 trap 把清理做干净。想法本身不复杂，难的是作者把「满队列时信号会不会被延迟」「255 会不会让队列停摆」「zsh 的 EXIT trap 会不会不一样」「写端被子进程继承后 EOF 还来不来」这些边角全想到了。

喜欢 Bash 的人会享受这篇文章；要上线的人，请听作者那句劝。

## Sources

- Christian Emmer《Concurrent Shell Command Queues》：<https://emmer.dev/blog/concurrent-shell-command-queues/>
- `mkfifo(1)`：<https://man7.org/linux/man-pages/man1/mkfifo.1.html>
- Postman Echo 文档（示例服务）：<https://www.postman.com/postman/published-postman-templates/documentation/631643-f695cab7-6878-eb55-7943-ad88e1ccfd65>
