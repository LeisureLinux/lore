---
title: "SUSE Agama 接入 MCP：AI 代理能装系统，但默认关着"
date: 2026-11-24
slug: suse-agama-mcp-ai-installer
category: 技术/解读
author: FreeLAMP.com
original_source: "Phoronix 报道（Michael Larabel，2026-11-24）＋ 一手核对 Agama 官方博客《The first AI-ready OS installer》（2026-11-24）与 agama-mcp README（工具清单、内核参数、token 隔离实现）。"
description: "解读 SUSE Agama 安装器从 26 版起内置的 MCP server：把硬件探测、配置校验、安装方案、执行与进度监控暴露成标准 MCP 工具，让 AI 代理驱动裸机部署。讲清两种模式（config 只允许看和改配置、full 才允许 commit_install/reboot）、四层确定性护栏（JSON Schema 校验、方案验证、专用 MCP token 隔离、可观测性）、11 个工具与 1 个资源、通过 inst.mcp=config/full 内核参数开启且默认关闭、token 只能走 /mcp 不能碰 /api、日志自动过滤密码，以及自签 TLS 要NODE_TLS_REJECT_UNAUTHORIZED=0 的坑。"
published: true
---

11 月 24 日，SUSE 的 Agama 安装器宣布从 **26 版**起内置 MCP（Model Context Protocol）server——Phoronix 称其为「第一个 AI-ready 的操作系统安装器」。AI 代理从此可以通过一组结构化工具，查看硬件、生成安装配置、计算方案、执行安装并监控进度。

好消息是：**它默认关闭**。

## 一、为什么是安装器，又为什么是 MCP

Agama 是 SUSE 新一代安装器，已经用于 SUSE Linux Enterprise，openSUSE Tumbleweed 和 Leap 也在切换。它从设计之初就强调「把安装过程集成进工作流」，能和 Uyuni、Ansible 这些工具配合。往 AI 方向延伸是顺理成章的一步。

官方博客给的例子很直观：一句自然语言——

> 装一台 openSUSE Tumbleweed，GNOME 桌面，NVMe 盘上用 Btrfs，建一个叫 tux 的用户，密码 nots3cr3t。

代理要自己推导出产品选择、面向 NVMe 的 Btrfs 存储方案、桌面 pattern 和用户定义——正是过去要在 UI 表单里手填的那些字段。

当然，AI 本来就能操作 Agama 的 Web UI 或 HTTP API。MCP 的价值在于提供一条**专用、更安全的接口**：一组为 AI 的实际工作方式设计的工具，在动作发生前先验validation，而不是指望模型自己点对按钮、拼对 HTTP 请求。

## 二、两种模式：config 和 full

MCP server 默认关闭，通过内核命令行参数激活：

- `inst.mcp=disabled` 或省略：关闭；
- `inst.mcp=config`：**只配置模式**——可以查硬件、取 schema、注入 profile、看 proposal，但 `commit_install` 和 `reboot` 返回 **403 Forbidden**，带 `scripts.pre`（预安装脚本）的配置也会被拒，防止任意命令执行。真正的安装要人在 Web UI 里审批和触发；
- `inst.mcp=full`：**完整模式**——AI 可以执行包括破坏性操作在内的一切动作，适合 Uyuni 这类外部编排器或自动化裸机流水线端到端接管，人类信任的是编排器而不是模型。

两种模式的区别只是「AI 被允许做什么」，下面这些护栏两种模式都生效。

## 三、四层确定性护栏：不信任模型，信任校验

操作系统安装天生是破坏性操作。语言模型会幻觉——包括幻觉出设备名——所以 Agama 不给 AI shell 权限，也不让它直接跑分区工具，所有交互都走确定性安全层：

1. **Schema 校验**：AI 提交的每一份 profile 都必须严格符合 Agama 的 JSON Schema，未知字段、类型错误立即拒绝；
2. **方案验证**：代理要的配置不合理（比如分配超过磁盘可用空间的容量），Agama 会回一个明确的错误说明，而不是让它带着错误继续；
3. **Token 隔离**：强制 AI 必须通过 MCP server 与 Agama 交互——专门的 MCP token **只认 `/mcp` 路由**，拿它去碰通用 REST API `/api/...` 会被 **401 Unauthorized** 拒绝。这一点很关键：否则代理可以读取自己配置里的 Bearer token，然后用 `curl` 绕过 MCP 的全部安全边界；
4. **可观测性**：提供针对性的诊断工具，让外部代理了解状态，又不把原始控制台输出灌爆它的上下文窗口。

## 四、11 个工具与 1 个资源

`agama-mcp` 把 Agama 的能力通过 HTTP SSE 上的标准 MCP 工具暴露出来：

- **读**：`get_config_schema(section?)` 取安装 profile 的 JSON Schema（可按 storage/software/network/user 等分节过滤）；`get_system(resource?)` 查硬件探测（存储、网络、硬件、软件，可过滤以免撑爆上下文）；`get_logs(log_type?, lines?)` 从 `journalctl` 取日志，默认 100 行、最多 1000 行，支持 installer/system/zypp 或具体 systemd unit；
- **写**：`set_config(config)` 注入并校验 profile，替换当前配置；
- **算**：`get_proposal()` 让 Agama 计算最终安装方案，返回方案差异或无解原因；
- **执行**：`commit_install()` 锁状态机、触发格式化和安装（config 模式禁用）；`reboot()` 重启进新系统（config 模式禁用，重启后 MCP 会话直接终止，日志要提前取）；
- **监控**：`get_progress()` 返回结构化状态（阶段、后台任务、待回答问题）；`wait_progress(timeout_seconds?)` 是事件驱动的等待——挂起直到后台任务结束、出现需要人回答的问题、安装完成/失败或超时（默认 60 秒），省掉轮询；
- **问答**：`get_questions()` 取待回答问题（如磁盘解密、GPG key 导入、包重试）；`answer_question(id, action, value?)` 按 ID 回答，解除阻塞。

另有一个资源 `agama://schema/config.json`，是完整的无人值守安装 profile JSON Schema。

日志工具有个细节：密码类敏感参数（`live.password`、`inst.mcp.token`）以及 URL 里的密码会被过滤成 `<FILTERED>`。

## 五、上手与两个坑

MCP 服务随 Agama 26 发布；等不及的可以用 nightly 镜像。配置客户端时，token 可以用 `inst.mcp.token=<SECRET>` 在内核命令行预置，或从目标机的 `/run/agama/mcp-token`（权限 0400）读取：

```json
{
  "mcpServers": {
    "agama-baremetal": {
      "url": "https://<agama-ip>/mcp",
      "headers": { "Authorization": "Bearer <DEDICATED_MCP_TOKEN>" }
    }
  }
}
```

**坑一**：Agama 默认用自签 HTTPS 证书。基于 Node.js 的客户端（Gemini CLI、Claude）会拒连自签证书，需要 `NODE_TLS_REJECT_UNAUTHORIZED=0 gemini` 或 `NODE_TLS_REJECT_UNAUTHORIZED=0 claude` 启动——注意这等于给该进程全局关掉了证书校验，生产环境别这么裸奔。

**坑二**：`commit_install` 之后状态机就锁定了， irreversible；而 `reboot()` 一旦执行，MCP server 和安装会话立即终止——需要留存的日志必须在重启前用 `get_logs` 取完。

## 六、怎么定性

把 MCP 塞进安装器，本质上是给「基础设施即代码」补上了 AI 这一环：从 Ansible/Uyuni 的声明式编排，走到自然语言描述 + 结构化校验的执行链。真正值得关注的不是「AI 会装系统了」，而是 Agama 的设计选择——**不给 shell、只给经过 schema 校验和 token 隔离的工具集**，把模型当成会犯错、会幻觉的输入源来设防。

这个思路，和我们在 OSC 7577 里看到的「终端恢复命令必须经过白名单交叉核对」是同一个方向：AI 能力的扩张，最后都要落回确定性的权限边界上。

## 参考资料

- Phoronix 报道：https://www.phoronix.com/news/SUSE-Agama-Adding-AI-MCP
- Agama 官方博客《The first AI-ready OS installer》：https://agama-project.github.io/blog/2026/11/24/first-ai-ready-os-installer
- agama-mcp README：https://github.com/agama-project/agama/tree/master/rust/agama-mcp
