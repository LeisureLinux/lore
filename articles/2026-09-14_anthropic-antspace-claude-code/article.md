> **译文来源**：《Anthropic's Hidden Vercel Competitor "Antspace"》—— AprilNEA（ArcBox Labs 创始人），aprilnea.me，2026-03-18，许可 CC BY-NC-SA 4.0。
> 原文：https://aprilnea.me/en/blog/reverse-engineering-claude-code-antspace
> 本文在原文基础上做了技术补全与解读（引用了 WEEX、aiadvances.org 等转述与作者的 GitHub 仓库分析文件），观点以「解读」段落单独标注。

# 逆向 Claude Code，挖出 Anthropic 藏着没说的「Vercel 竞品」Antspace

2026 年 3 月，一位做全栈平台的开发者 AprilNEA 在他的 Claude Code Web 会话里，随手打了句 `strace -p 1`，本想看看运行环境长啥样，结果一路挖下去，撬开了 Anthropic 一个**从未公开披露**的部署平台——代号 **Antspace**。整篇分析没有用任何漏洞、没有提权、没有网络攻击，全靠在会话内部跑标准 Linux 工具（`strace` / `strings` / `objdump` / `go tool objdump`）完成。

更妙的（也更让人皱眉的）是：那颗 27MB 的 Go 二进制，**没剥离调试符号**，完整保留了 Anthropic 私有仓库的包结构和函数名。作者原话：「把一个带着完整调试符号、没剥离的二进制发到生产环境，是个……选择。」

下面把这场逆向考古的骨架拆给你看。

## 一、起点：一个没剥离的 Go 二进制

AprilNEA 团队在做的 ArcBox，定位和 Railway、E2B 类似——本地桌面到云端的全栈平台，核心理念是「本地-云端一致性」。当他们发现几乎所有 Coding Agent 平台都在底层用 Firecracker 时，作为同行，好奇心驱使他们钻进 Claude Code 的运行环境。

一切从 `strace -p 1` 开始，最终变成一场完整的逆向，挖出了 Anthropic 尚未公开的部署基础设施，包括一个**完全无文档的应用托管平台**。

所有发现都来自在 Claude Code 会话内部运行的标准 Linux 工具。没有利用任何漏洞，没有提权，没有网络攻击。那颗二进制就明晃晃地躺在那儿，没剥离，带着完整调试符号。

## 二、运行环境：Firecracker MicroVM

Claude Code Web 跑在一台 **Firecracker 微虚拟机**里，规格相当实在：

- **4 vCPU**（Intel Xeon Cascade Lake @ 2.8GHz）
- **16GB 内存**
- **252GB 磁盘**
- **Linux 内核 6.18.5**

进程树极简到近乎苛刻：**PID 1 不是 systemd**，而是一个自定义 init 二进制 `/process_api`，它同时兼任 WebSocket 网关（监听 2024 端口）。没有 sshd，没有 cron，没有 journald——只保留了运行 Claude 环境所需的「裸金属」。

`/process_api` 本身是一个 3.1MB 的 Rust/tokio 程序（作者在 GitHub 仓库里用 Ghidra 反编译了它，3599 个函数、44.6 万行 C 伪代码），负责进程产生/生命周期、cgroup 管理、OOM killer、mount/pivot_root 初始化、控制 HTTP 服务，以及面向会话的 WebSocket 协议（JWT 鉴权 → ProcessConnection → CreateProcess / stdin·stdout·stderr 二进制帧 / SendSignal / Resize / Detach / KeepAlive）。

## 三、Layer 2：没剥离的 Go 二进制与完整包结构

容器里核心二进制 `/usr/local/bin/environment-runner` 是一颗 **27MB 的 Go 可执行文件，未剥离调试符号**，完整保留了来自 Anthropic 私有仓库 `github.com/anthropics/anthropic/api-go/environment-manager` 的包结构与函数名。

`go version -m` 一把梭出全部构建元数据：模块路径、`(devel)` 单仓标记、版本串 `staging-68f0dff496`、Go 1.25.7，以及完整依赖清单。因为没剥离，`objdump -t` 直接给出全限定函数名——过滤 `environment-manager/internal/` 就重建出整棵架构树：

```
internal/
├── api/                  # API 客户端（会话入口、任务轮询、重试）
├── auth/                 # GitHub App token 提供方
├── claude/               # Claude Code 安装、升级、执行
├── config/               # 会话模式（new/resume/resume-cached/setup-only）
├── envtype/
│   ├── anthropic/        # Anthropic 托管环境
│   └── byoc/             # Bring Your Own Cloud 环境
├── gitproxy/             # Git 凭据代理服务器
├── input/                # Stdin 解析 + 密钥处理
├── manager/              # 会话管理器、MCP 配置、skill 抽取
├── mcp/
│   └── servers/
│       ├── codesign/     # 代码签名 MCP 服务器
│       └── supabase/     # Supabase 集成 MCP 服务器
├── orchestrator/         # 轮询循环、hooks、whoami
├── podmonitor/           # Kubernetes lease 管理器
├── process/              # 进程执行 + 脚本运行器
├── sandbox/              # 沙箱运行时配置
├── session/              # 活动记录器
├── sources/              # Git 克隆 + 源码分类
├── tunnel/               # WebSocket 隧道 + 动作处理器
│   └── actions/
│       ├── deploy/       # ← 最精彩的地方
│       ├── snapshot/     # 文件快照
│       └── status/       # 状态上报
└── util/                 # Git 辅助、重试、流尾部读取
```

从二进制里提取的关键依赖：

| 依赖 | 用途 |
|---|---|
| `github.com/anthropics/anthropic/api-go` | 内部 Anthropic Go SDK |
| `github.com/gorilla/websocket` | 到 API 的 WebSocket 隧道 |
| `github.com/mark3labs/mcp-go v0.37.0` | Model Context Protocol |
| `github.com/DataDog/datadog-go v5` | 指标上报 |
| `go.opentelemetry.io/otel v1.39.0` | 分布式追踪 |
| `google.golang.org/grpc v1.79.0` | gRPC（会话路由） |
| `github.com/spf13/cobra` | CLI 框架 |

## 四、最精彩的部分：tunnel/actions/deploy/ 里的两套部署客户端

在 `tunnel/actions/deploy/` 包里，作者发现了**两套部署客户端**：

- 已知的 **`VercelClient`**（Vercel 部署客户端）
- 此前从未出现过的 **`AntspaceClient`**（Anthropic 自家部署平台）

`AntspaceClient` 实现了一套**完整的三阶段部署协议**：

1. **创建部署**（create deployment）
2. **上传 `tar.gz` 构建产物**（upload tar.gz build artifact）
3. **流式 NDJSON 状态推送**（stream NDJSON status）

版本串前缀是 `staging-`，说明还在早期/内部阶段。但整个部署协议已经成熟、达到生产级。全网搜「Antspace」——Anthropic 官网、博客、GitHub、招聘页，**零记录**。

## 五、连带挖出的：Baku 与 BYOC

同一份二进制还泄露了另一个内部代号 **Baku**——claude.ai 网页版的应用构建器，使用 **Vite + React + TypeScript** 模板，自动提供 **6 个 Supabase MCP 工具**（按需建库、迁移管理、Edge Function 部署等），**默认部署目标正是 Antspace 而不是 Vercel**。

代码里还存在企业级 **BYOC（Bring Your Own Cloud）** 环境支持：允许企业在自己的基础设施里跑 `environment-runner`，同时由 Anthropic API 做会话编排。

## 六、安全护栏：该有的都有，但二进制没藏住

逆向揭示出的运行时安全护栏（部分来自 dmesg、部分来自二进制字符串与运行期取证）：

| 措施 | 目的 |
|---|---|
| `init_on_free=1` | 会话之间清零已释放内存页 |
| 丢弃 `CAP_SYS_RESOURCE` | 初始化后限制 PID 1 的能力 |
| CRNG 重新播种 | 防止快照 fork 后随机数可预测 |
| `--block-local-connections` | 阻断 localhost WebSocket 访问 |
| JWT 鉴权 | WebSocket 连接校验 |
| Token 擦除 | 使用后从配置里移除密钥 |

另外，Firecracker 的 **Snapstart 模式**也被还原出来：先用极简模板 VM（只有 proc/sys/dev/net）做快照，恢复时热插拔块设备。dmesg 证明模板启动（2026-03-16）与本次会话恢复（2026-03-18）之间存在 **48.5 小时**时间差；恢复后才 drop caches、重挂 devtmpfs、挂 ext4+squashfs、pivot_root、clock_settime。

块设备分配：`vda`=ext4 可写 rootfs，`vdb`=squashfs（claude-code），`vdc`=squashfs（env-runner）。

## 七、方法论：七步把「生产环境」逆向了个底朝天

作者把全过程公开成了标准 Linux 工具七步法：

1. **识别 hypervisor**：`dmesg | grep FIRECK`——ACPI 表带 OEM ID，直接指纹出 Firecracker（OEM ID `FIRECK`、creator ID `FCAT`）。
2. **识别 PID 1**：`cat /proc/1/cmdline`——露出自定义 init `/process_api`，`--firecracker-init` 标志确认。
3. **提取 Go 构建元数据**：对 environment-runner 跑 `go version -m`，得到 Go 版本、模块路径、`(devel)` 单仓标记、完整依赖。
4. **从符号恢复包结构**：因为没剥离，`objdump -t` 给全限定函数名；过滤 `environment-manager/internal/` 提取唯一路径，得到完整架构树。
5. **定向字符串提取**：Go 二进制里裸 `strings | grep` 很吵（链接器把所有字符串字面量拼一起）。更优做法——已知模式搜索（扫特定字节序列如 `dist.tar.gz`、`application/x-ndjson`）+ 结构体 tag 提取（Go 把 struct 字段 tag 当字符串字面量嵌入，搜 `json:"status"` 这类能还原出线协议格式）。
6. **符号表驱动的功能映射**：`objdump -t binary | grep 'deploy\.'` 给出每个组件的方法清单——Vercel 和 Antspace 两个客户端就是这么带着完整方法签名被发现的。
7. **运行期观察**：`strace -p 1 -e trace=epoll_pwait,read,write -f` 确认 epoll 事件循环、子进程监控、WebSocket 通信模式。

| 技术 | 揭示了什么 |
|---|---|
| `dmesg` ACPI OEM ID | 虚拟机监控器身份 |
| `go version -m` | 工具链、依赖、单仓结构 |
| 符号表（`objdump -t`） | 包布局、类型名、方法签名 |
| 结构体 tag 字符串 | 线协议 / JSON 格式 |
| 定向字节搜索 | 错误信息、状态串、流程逻辑 |
| PID 1 上的 `strace` | 运行期行为、IPC 模式 |

**为什么能成**：① 二进制没剥离（最大单一因素，剥离了就得上 Ghidra）；② Go 的构建元数据嵌入等于免费依赖清单；③ Go 的字符串拼接模型保留了 struct tag 和错误串；④ VM 内的 root 权限允许对 PID 1 跑 `strace`。

## 八、解读：这事儿到底意味着什么

**1. 「安全优先」实验室的运维反讽。** Anthropic 对外主打「安全优先」、发布责任扩展政策、天天谈生存性风险；可它把整套内部架构以可读明文发到每个用户会话里。aiadvances.org 的评论很到位：对一个声称最在乎安全的公司，这……认真吗？当然，作者也指出攻击者没拿到任何东西——这些信息本来就在用户自己的会话进程空间里可见，不算泄露漏洞。但「把私有仓库路径、内部代号、部署协议完整暴露」确实是工程纪律上的低级失误，尤其对一个以稳健著称的团队。

**2. 垂直整合闭环已成雏形。** Antspace + Baku + BYOC 拼起来，是从**模型 → 运行时 → 托管**的完整闭环：Claude 写代码（Claude Code），Baku 用 Supabase MCP 把全栈应用拼出来，Antspace 直接托管上线，BYOC 再补上「企业想自己跑」的场景。这正是 Vercel / Netlify、Replit、Supabase 各自的饭碗——Anthropic 一家全包了。作者判断：无论最终是作为公开产品发布，还是只服务于 Claude 的网页体验，Anthropic 的野心早已超出「只做 LLM 和 Agent 公司」。

**3. 给 AI 工程与信创场景的启示。** 这场逆向最值得抄作业的，其实是它的**沙箱设计**：Firecracker MicroVM + 极简 PID 1（Rust/tokio，3.1MB）+ 严格能力裁剪 + 内存清零 + CRNG 重播种 + 快照恢复。对需要在不可信输入（AI 生成代码、Agent 自动执行）下保证隔离强度的场景——无论是国内信创桌面里的「AI 助手沙箱」，还是云端 Coding Agent 平台——这是一份现成的、生产级的可参考架构。反过来说，它也是个反面教材：**产物分级与符号剥离**这种基本功，在面向用户的二进制上不能省。

一句话收尾：Anthropic 想拥有「应用被说出来的那一刻起」的每一层栈——而一份没剥离的二进制，让他们想藏的那层先被看穿了。
