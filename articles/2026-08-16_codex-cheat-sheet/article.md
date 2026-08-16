# Codex 速查手册：命令、安全模型、模型选择、推理档位与 AGENTS.md 的实用指南

> 原文：[The Codex Cheat Sheet](https://littlemight.co/writing/codex-cheat-sheet)（littlemight.co，2026-04-05 发布，2026-04-13 更新），作者 Cathryn Lavery。本文由 LeisureLinux 翻译整理，英文命令、参数与配置保留原样。

如果你还在翻旧帖子学 Codex，这篇速查手册值得先读——它覆盖了当前 GPT-5.4 时代的模型选择、五档推理力度、安全模式以及那些真正值得记住的命令。以下要点全部来自当前 Codex CLI 的官方指引。

## CLI 基础

最核心的几条命令：

- `codex` —— 启动交互式会话
- `codex "task"` —— 带着一个开局任务进入交互式会话
- `codex exec "task"` —— 非交互式运行（脚本、CI）
- `codex --full-auto "task"` —— 在 workspace 沙箱内自主运行（这就是"Yolo 档位"，但它仍然跑在沙箱里）

```bash
codex
codex "Run the test suite and report what fails"
codex exec "Fix the failing tests, run the formatter, and summarize the diff"
codex --full-auto "Refactor the billing module and verify tests pass"
```

值得记住的常用标志：

```bash
codex -m gpt-5.4 "Summarize the security model of this repo"
codex -m gpt-5.4-mini "Rename these components and clean up imports"
codex -c 'model_reasoning_effort="high"' "Explain the architecture of this monorepo"
codex -i screenshot.png "What's wrong with this component?"
codex --search "Check the latest Next.js docs before changing this config"
```

容易混淆的只有一件事：`codex "task"` 会启动一个交互式会话，`codex exec "task"` 则完全非交互。自动化流程请用后者。

---

## 安全模型：三个开关，别搞混

现在的 Codex 由两件事**分别控制**安全：

- `--sandbox` —— 控制 shell 命令能读写哪些位置
- `--ask-for-approval` —— 控制什么时候停下来问你要不要批准
### 沙箱模式：`--sandbox`

| 模式 | 含义 |
|-----|------|
| `read-only` | 可以看代码，但不能改代码或改 Git 状态 |
| `workspace-write` | 可以编辑 workspace 目录里的文件，但不能动 Git 状态或装包 |
| `danger-full-access` | 不设沙箱限制 |

三个开关，按从安全到放开的顺序：

- `--sandbox read-only`
- `--sandbox workspace-write`
- `--sandbox danger-full-access`（注意这个标志的名字是"危险"）

### 审批策略：`--ask-for-approval`

- `untrusted` —— 只有可信的安全命令可以直接跑，涉及已装包或其他风险的操作都会问一遍
- `on-request` —— 沙箱允许的操作直接跑，超出范围的问一遍
- `never` —— 不问，失败就原样抛回给模型

### 三种最常用预设

1. **只读检查（read-only inspect）**：`--sandbox read-only --ask-for-approval untrusted`
2. **标准自主编码（standard autonomous coding）**：`--full-auto`
3. **YOLO（yolo）**：`--sandbox danger-full-access --ask-for-approval never`

```bash
# 安全检查：只读
codex --sandbox read-only --ask-for-approval untrusted "Inspect this repo for security issues and report findings"

# 日常自主编码：full-auto
codex --full-auto "Refactor this module and keep the tests passing"

# 完全自主：无沙箱、无审批（yolo）
codex exec --sandbox danger-full-access --ask-for-approval never "Run the migration and fix anything it breaks"
```

`--full-auto` **不是** `--yolo`。前者只是简写：`--sandbox workspace-write --ask-for-approval on-request`——它仍然在沙箱内，并且该问的时候会问；后者是把审批和沙箱**全部**关掉。

只想多给一个可写目录？用 `--add-dir`，不要上 `danger-full-access`：

```bash
codex --add-dir ../shared "Update the shared API client and this repo's UI"
```

**记住的核心标志：`--sandbox`、`--ask-for-approval`、`--full-auto`、`--add-dir`。**

有用的非交互选项：`codex exec --json`（机器可读的输出流）、`-o FILE`（把最终答案写到文件里）。

还有其他值得记住的子命令：

- `codex review` —— 跑一次代码审查
- `codex resume` —— 恢复上一次交互式会话
- `codex resume --last` —— 恢复最近一条线程
- `codex fork <name>` —— 基于既有会话开一条分支
- `codex mcp add -- stdbuf -oL -eL npx @some/mcp-server` —— 注册新的 MCP 服务器（`stdio`）
- `codex mcp add <name> -- npx pkg --port 8080 --type http` —— 注册 `http` 类型的 MCP 服务器
- `codex mcp list` —— 列出已配置的服务器
---

## 模型与推理：默认用 GPT-5.4

一句话版：大多数人直接用 **GPT-5.4 家族**就够了，日常快任务用 `gpt-5.4-mini`，慢但重要的任务用 `gpt-5.4`。

```bash
# 深度审查（慢，值得）
codex -m gpt-5.4 "Review the architecture risks in this refactor"

# 常规执行（快）
codex -m gpt-5.4-mini "Rename these components and fix imports"

# 超快迭代（Codex 调优）
codex -m gpt-5.3-codex-spark "Quick pass: fix the obvious type errors"
```

| 模型 | 速度 | 定位 |
|------|------|------|
| `gpt-5.4` | 慢 | 质量优先，Codex 的默认模型 |
| `gpt-5.4-mini` | 快 | 保持节奏的日常工作 |
| `gpt-5.3-codex-spark` | 超快 | Codex 调优模型，延迟比深度更重要时用 |

还有一个容易踩的点：**Codex 调优模型是单独的一条产品线**，不是通用模型的小号。在 Codex CLI 里你用的是产品默认路由的那些模型；但如果你基于 API 自己搭系统，Codex 调优系列（`gpt-5.5-codex`、`gpt-5.5-codex-spark`、`gpt-5.3-codex-spark`、`gpt-5.1-codex-max`、`gpt-5.1-codex-mini`）是为围绕 Responses API 构建自主编码代理的构建者准备的，有自己的计费，通常按 token 计。

GPT-5.4 家族的定位（Codex 默认走 `gpt-5.4`）：

- `gpt-5.4` —— 质量优先的通用前沿模型，默认选择
- `gpt-5.4-mini` —— 保持流动性的快速循环
- `gpt-5.3-codex-spark` —— 当延迟比深度更重要时用，可以把重模型留给真正需要的任务

---

## 推理力度（reasoning effort）

GPT-5.4 支持可配置的五档推理力度，这实际上取代了过去"到底用哪个模型"的大部分讨论：

- `none` —— 直接给答案，不做额外思考
- `minimal` —— 只处理明确简单的任务
- `low` —— 快，适合清理和范围明确的任务
- `medium` —— 大多数编码会话的默认档位
- `high` —— 大型重构、深度调试、架构级任务
- `xhigh` —— 只给最难的问题，代价是更慢和更贵

```bash
codex -m gpt-5.4 -c 'model_reasoning_effort="low"' "Clean up this lint debt"
codex -m gpt-5.4 -c 'model_reasoning_effort="medium"' "Implement this feature"
codex -m gpt-5.4 -c 'model_reasoning_effort="high"' "Debug this intermittent race condition"
codex -m gpt-5.4 -c 'model_reasoning_effort="xhigh"' "Design the long-term storage migration"
```

默认思路：

- 日常：`gpt-5.4-mini` + `medium`
- 影响面大的改动：`gpt-5.4` + `high`
---

## AGENTS.md：效果提升最大的一处投入

AGENTS.md 仍然是那件能真正改变结果的事。Codex 会自动从 `~/.codex` 以及仓库路径加载并注入它。

# 根 AGENTS.md —— 仓库级全局约定
```markdown
# AGENTS.md

Use pnpm, not npm.
Run tests with `pnpm test --watch=false`.
Keep API handlers in src/api.
Do not modify generated proto files.
```

# 嵌套 AGENTS.md（更近的路径优先级更高）
```markdown
# docs/AGENTS.md

Treat docs/*.mdx as the source of truth.
Do not rename exported page components.
```

嵌套目录里的 AGENTS.md 会覆盖更上层的约定，适合把局部规则和全局规则分开管理。实践建议：

1. 根 AGENTS.md 写仓库级约定；
2. 每个子目录用嵌套 AGENTS.md 加局部规则；
3. 明确列出"绝不"清单——对自动跑（`--full-auto`）来说这最重要；
4. 如果你在提示里反复重复同一条指令，就该把它挪进 AGENTS.md。

---

## config.toml：一次写好，到处受益

Codex CLI 现在完全由配置驱动，官方文档里能配置的东西远比旧帖子多。常用项：

```toml
# config.toml
model = "gpt-5.4"
model_reasoning_effort = "medium"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.deep]
model = "gpt-5.4"
model_reasoning_effort = "high"

[profiles.safe]
sandbox_mode = "read-only"
approval_policy = "untrusted"
```

用 `-p` 快速切换 profile：

```bash
# 深度审查：合并前把关
codex exec -p deep "Review this refactor for architectural risk"

# 安全检查：只读
codex exec -p safe "Scan for secrets and unsafe shell usage"
```
---

## Headless 与 CI 最佳实践

CI 里不要用交互命令。用 `codex exec`，配 `--json` 或 `-o FILE` 捕获输出，然后把日志接进流水线。

```yaml
# CI (ci.yml)
- name: "Codex: test and fix"
  run: |
    codex exec --json -o codex-out.txt \
      "Run tests, diagnose failures, apply the smallest safe fix, re-run tests" \
      | tee codex.log
- name: "Show final answer"
  run: cat codex-out.txt
```

只有在**完全隔离**的运行环境（一次性容器、CI 沙箱）里才开 `--dangerously-bypass-approvals-and-sandbox`。如果你的 CI 跑在外部沙箱里，直接用它的原生沙箱就好。

---

## 真正有效的提示模式

给 Codex 一个完整的闭环（发现 → 修复 → 验证）：

```plain
"Find the root cause of the failing payment tests, fix it,
 run the focused test suite, and summarize the change."
```

明确说清不能碰什么：

```plain
"Only touch files under src/payments/. Do not change UI copy,
 DB schema, or generated API types."
```

模型够强时，先加推理力度，别急着换模型：

```plain
"Think through the concurrency implications before
 touching these queues."
```

把固定约束写进 AGENTS.md（包管理器、测试命令、架构规则、禁区文件），别在提示里每次重复。

需要最新资讯时用 `--search`：

```plain
"Check the latest Cloudflare docs before refactoring
 this edge routing setup."
```

高影响面改动，先让它做计划：

```plain
"Inspect the codebase, propose a plan, list the files you would touch,
 identify risks, and define the verification steps before changing
 anything. Ask if the plan looks wrong."
```

这仍然是最干净的防止自主跑飞的方式。
---

## 速查表（cheat sheet）

常用的就这些：

```bash
codex
codex "task"
codex exec "task"
codex --full-auto "task"
codex exec --sandbox danger-full-access --ask-for-approval never "task"
codex -m gpt-5.4 "task"
codex -m gpt-5.4-mini "task"
codex -m gpt-5.4 -c 'model_reasoning_effort="high"' "task"
codex --search "task"
codex exec -p deep "task"
codex --add-dir ../shared "task"
codex -i screenshot.png "task"
codex review
codex resume
```

## 记住三句话就够

1. 先把 AGENTS.md 写好——约束要放在前面。
2. 分清 `--full-auto` 和 `--yolo`。
3. 推理力度比盲目换模型更常用——需要"更深思考"时，用 `model_reasoning_effort`，而不是换模型。

---

*原文出处：[The Codex Cheat Sheet — Cathryn Lavery](https://littlemight.co/writing/codex-cheat-sheet)，littlemight.co，2026-04-05 发布，2026-04-13 更新。*
