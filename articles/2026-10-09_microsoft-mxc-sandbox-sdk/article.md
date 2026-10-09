---
title: "微软把「跑不可信代码」做成了一个 SDK 依赖：九个沙箱后端与一份说清边界的文档"
date: 2026-10-09
slug: microsoft-mxc-sandbox-sdk
tags: [Microsoft, MXC, 沙箱, 代码执行隔离, Bubblewrap, Seatbelt, AppContainer, WFP, MicroVM, Nanvix, Hyperlight, Windows Sandbox, 供应链安全, 译文]
category: 安全
author: FreeLAMP.com
original_source: "microsoft/mxc GitHub 仓库（README 与 docs/）"
original_author: "Microsoft MXC 团队"
original_date: 2026-10-09
original_url: "https://github.com/microsoft/mxc"
description: "微软开源的 MXC（Microsoft eXecution Container）把 Windows/Linux/macOS 上九种隔离后端统一在一套 deny-by-default 策略模型后面，以 SDK 依赖形式嵌进应用，用于运行模型输出、插件与工具等不可信代码。本文梳理它的定位与三档 SDK、方向性网络契约的设计规则、九个后端的成本与前提，以及文档里主动标出的能力边界：bubblewrap 会拒绝做不到的请求、identity-less host proxy 被点名为更弱部署、一次性 VM 拆除是尽力而为、--audit 会关闭全部沙箱安全。"
published: true
---

> 来源：[microsoft/mxc](https://github.com/microsoft/mxc)（MIT，2026-02-06 开源，最后提交 2026-10-09）
> 本文依据仓库 README 与 `docs/` 下的后端指南、schema、遥测与生命周期文档整理。

## 一句话结论

微软开源了 **MXC（Microsoft eXecution Container）**：一个**给「跑不可信代码」用的沙箱执行系统**，把 Windows、Linux、macOS 上九种隔离后端统一在一套 **deny-by-default 的策略模型**后面，并以 **SDK 依赖**形式嵌进你自己的应用，而不是一个你要去运维的服务。真正让它值得读的不是「沙箱又多了一个」，而是它在文档里**主动标出了每个后端能保证什么、不能保证什么**，以及一个统一抽象必须具备的**拒绝语义**。

## 一、定位：它是库，不是服务

仓库描述写得很直白：**Policy-driven, layered isolation and containment**（策略驱动的分层隔离与围堵）。README 的第一句画了它的边界：

> MXC 是一个**构建进你应用的 SDK 依赖**。

调用关系只有三步：应用给出**容器类型 + 围堵规则 + 工作负载命令**，MXC 校验请求、选择后端、把工作负载放进容器里跑起来。没有常驻控制面，没有要先起的代理。

| 形态 | 内容 |
|---|---|
| SDK | Rust `mxc-sdk`（crates.io）／.NET `Microsoft.Mxc.Sdk`（NuGet）／Node `@microsoft/mxc-sdk`（npm） |
| 非 SDK | 平台执行器二进制 `wxc-exec.exe`（Windows）、`lxc-exec`（Linux）、`mxc-exec-mac`（macOS），吃 JSON 配置 |
| 公共 API | 全部挂在版本化命名空间下：`mxc_sdk::v1` / `Microsoft.Mxc.Sdk.V1` / `@microsoft/mxc-sdk/v1` |
| 构建 | Rust 固定 1.93（`src/rust-toolchain.toml`），Node 24+ |

一个细节值得注意：**Node 包的根路径不导出任何 API**，必须显式从 `/v1` 导入。这是刻意的，避免以后加 v2 时又变成「根路径到底指向谁」的经典问题。同理，**SDK 的公开接口与原生 wire 契约是独立版本化的**。

服务器端一行代码的调用长这样（Node 示例）：

```ts
import { spawn, type ContainerRequest } from '@microsoft/mxc-sdk/v1';

const request: ContainerRequest = {
  command: 'node -e "console.log(\'hello from container\')"',
  network: { egress: { default: 'deny' } },
  timeoutMs: 30_000,
};

const child = await spawn(request);
```

**注意那个 `default: 'deny'`**。这不是示例里随手加的安全装饰，下面会看到它是整个设计的默认前提。

## 二、策略模型：默认全拒，方向分开

MXC 的配置是一份 JSON，有**稳定 schema（1.0.0）**和**开发 schema（1.1.0-alpha）**两条线，稳定版给生产用，dev 版包含实验特性且「可能随时变」。

策略分三块：

### 文件系统

`readonlyPaths`、`readwritePaths`、`deniedPaths` 三档，语义直白。

### 网络：方向性（directional）契约

这是最近的设计重心。新契约把 **egress 和 ingress 分开**，各自有独立的 `default`：

```json
{
  "version": "0.9.0-alpha",
  "network": {
    "egress": {
      "default": "deny",
      "allow": [{
        "to": [{ "cidr": "140.82.112.0/20" }],
        "ports": [{ "protocol": "tcp", "port": 443 }]
      }]
    },
    "ingress": {
      "default": "deny",
      "hostLoopback": "deny"
    }
  }
}
```

几条设计规则值得单独拎出来：

- **省略就是拒绝**。`network`、`network.egress`、`network.egress.default` 任何一个省略，`egress.default` 解析为 `deny`；两个 ingress 控制项同样默认 `deny`；
- **`hostLoopback` 独立于 `ingress.default`**。要访问宿主 loopback 必须**显式申请**，不会因为放开了别的就被顺带打开；
- **两种出网模型不能混用**。要么用 CIDR + 协议 + 端口的直连规则（后端支持的话），要么用 `runtimeConfig.networkProxy` 指定一个你自己管理的 HTTP/S 代理端点（此时由代理负责目标过滤）。同时给两个是**非法配置**；
- **旧字段被显式拒绝**。`0.9.0-alpha` 之前的 `defaultPolicy`、`enforcementMode`、host lists、`allowLocalNetwork`、`network.proxy` 在新契约下**直接报错**，文档还专门写了一句：**只改版本号不等于迁移策略**。

### Windows 后端怎么落实这套策略

ProcessContainer 在 OS 级强制路径上给每个容器两个原语，都按容器 SID 作用域，**每次启动不需要 UAC 弹窗**：

- **WFP 出网过滤**：默认阻断，再按 IP/网段、协议、端口放行或阻断（IPv4/IPv6 都支持），**显式阻断永远优先于放行**，规则只作用于该容器；
- **按容器的 WinHTTP 代理**：把 WinHTTP 栈（含 Chromium 栈）指向一个调用方提供的 loopback 代理容器，同时为依赖环境变量的运行时设置 `HTTP_PROXY`/`HTTPS_PROXY` 及其小写形式。文档有一句提醒：`NO_PROXY` 是绕过列表，**不携带代理端点**。

而 Windows 的 AppContainer 有个 OS 限制：`privateNetworkClientServer` 是**双向**能力。所以想访问私网就必须 `ingress.default: "allow"`，而这一开**同时**允许了私网的入向服务流量。文档没有含糊，直接列了四象限矩阵：

| egress 默认 | ingress 默认 | AppContainer 能力 | 结果 |
|---|---|---|---|
| deny | deny | 无 | 公网与私网流量全拒 |
| allow | deny | `internetClient` | 公网出向放行；私网拒绝 |
| deny | allow | `privateNetworkClientServer` | PSEC 用 WFP 阻断出向，允许私网入向；**AppContainer 回退路径会拒绝这个组合**，因为该能力是双向的 |
| allow | allow | 两个能力 | 公网出向 + 私网双向 |

最后一行的那句「回退路径会拒绝这个组合」很关键，它体现的是下一节要讲的拒绝语义。

## 三、九个后端：从进程沙箱到硬件虚拟化

MXC 把同一份策略映射到九个后端，范围横跨「一个进程树」到「一台轻量虚拟机」。

| 运行平台 | 默认后端 | 其他后端 |
|---|---|---|
| Windows 11 x64 / ARM64 | `processcontainer` | `windows_sandbox`\*、`wslc`、`microvm`\*、`hyperlight`\*、`isolation_session` |
| Linux x64 / ARM64 | `bubblewrap` | `lxc`、`microvm`、`hyperlight` |
| macOS ARM64 / x64 | `seatbelt` | 无 |

\* 标记的是**实验性**后端，需要 `--experimental`。

**Linux 默认 Bubblewrap**：不依赖 root，也不需要容器运行时，用 Linux user namespace 造隔离环境。有个硬性版本底线：因为基线策略要用 `--ro-bind-try`（bwrap 0.3.1+）和 `--clearenv`（bwrap 0.5.0+），所以**要求 bwrap 0.5.0 或更新**；平台探测会跑 `bwrap --version`，低于底线就把后端报为不可用**并带上探测到的版本号**。探测本身有 5 秒超时和每路输出 64 KB 上限，超时会**用 SIGKILL 结束整个进程组**，防止包装脚本和后代进程把探测吊住。

**macOS Seatbelt**：跑在 Apple 内核强制的沙箱里，也就是 Mac App Store 应用用的同一套框架。要求 macOS 15（Sequoia）以上，**不需要 root、不需要守护进程、不需要安装**。实现上把 JSON 策略翻译成 Seatbelt profile，在 `fork()` 和 `exec()` 之间用 `sandbox_init()` 应用，profile 以**字符串**传入，不落临时文件。沙箱的寿命等于被包裹进程树的寿命。

**硬件虚拟化档（实验性）**：

| 后端 | 机制 | 开销 |
|---|---|---|
| `microvm`（Nanvix） | Windows 走 WHP，Linux 走 KVM | **~100 ms** 进程启动到 guest 代码执行，常驻内存 **~100 MB** |
| `hyperlight` | Hyperlight 微虚拟机启动 Unikraft unikernel，由 `hyperlight-unikraft` crate 在进程内驱动 | 每次运行从**热快照**恢复 guest，Linux/Windows 共用一条代码路径 |
| `windows_sandbox` | Windows Sandbox 提供的 VM 级隔离 | 一次性模式每次调用都起一台全新的一次性 VM |

Nanvix 那份文档里有两个诚实的注脚：**热启动快照是 Windows 专属**，Linux 每次调用都通过 KVM 冷启动；构建时默认会去下载 Nanvix 的 release 资产，**气隙/密闭构建**要用 `NANVIX_BIN` 指向预取的二进制目录。

## 四、最有价值的部分：它写清了哪些约束真能强制

这是我认为这份文档最值得同行学习的地方。统一抽象最大的风险是**静默降级**：上层以为配了，下层其实没做。MXC 用几种不同手段把这个风险摆到明面上。

### 1. 做不到就拒绝，而不是假装接受

Bubblewrap 那份指南写得很直接：**Bubblewrap 会在创建容器之前，拒绝那些「看起来可强制、但它无法兑现」的请求**，例如 `ingress.default: "allow"`，或者把直连出网规则和 runtime proxy 混在同一个请求里。对比一下 Windows 的 AppContainer 回退路径同样拒绝 `deny/allow` 组合。**「拒绝语义」是抽象层能不能被信任的分界线。**

### 2. 把「更弱的选择」标出来，而不是让它们长得一样

策略文档里有一句容易被跳过的说明：**identity-less host proxy 是一条更弱的开发/测试部署路径**，它把宿主 loopback 的两个方向都打开，且不把访问限制在指定的代理 peer 上，**不强制「仅代理」的 host-loopback 例外**。而 identity-scoped 的配置要求非空的 `allowedProxyPeer` 并保持 `hostLoopback: "deny"`。同一个功能，两种配置，安全强度不同，文档直接用「更弱」这个词告诉你。

### 3. 明确否认「兼容路径等价于强路径」

ProcessContainer 文档在列完 WFP + WinHTTP 两个原语之后加了一句：**AppContainer 兼容行为在文档第 2 节说明，它与这些保证并不等价**。不靠读者自己推断。

### 4. 一次性 VM 的拆除是「尽力而为」

Windows Sandbox 的一次性模式是每次调用起一台全新的一次性 VM、跑一条命令、返回前拆掉。文档写明：**拆除是尽力而为，不是内核保证的**，启动器被强杀可能留下卡死的孤儿 VM，并给出了 `--force-reclaim` 的处理入口。这种话通常没人愿意写进 README。

### 5. `--audit` 会关掉全部沙箱安全

为了帮策略作者定位 access denied、反推一个可信工具实际需要哪些文件和能力，MXC 提供了 audit 模式。README 对此的排版是**警告框**：

> `--audit` 会**关闭被分析工作负载的全部沙箱安全**。**永远不要用它运行不可信代码。**

同时它给了更安全的替代路径：**deny-and-record** 式的「记录被拒绝的访问」，既拿到策略线索又不打开沙箱。

### 6. 平台能力的门槛是显式探测，不是假定

Bubblewrap 的 Rust 侧把**成功的**探测结果按进程生命周期缓存，**失败的不缓存**，而且执行前会再探一次，理由是防止 PATH 指向的目标在两次之间被换掉、复用旧的探测结论。Node SDK 侧则把 `getPlatformSupport()` 的完整结果（**包含失败**）缓存到模块生命周期，所以文档会提醒你：**修好宿主环境后要重启 Node 进程**。这些细节说明作者想过「探测结果被缓存后失去时效」的攻击面。

## 五、遥测：管理员只能封禁，不能替用户同意

这部分设计得比多数同类项目清楚，值得单列：

| 项 | 值 |
|---|---|
| 范围 | **仅 Windows**（MXC 只在 Windows 收集遥测；Linux/macOS 上无事可受限） |
| 策略位置 | `HKLM\SOFTWARE\Policies\Mxc`，值名 `AllowTelemetry`，类型 `REG_DWORD`，机器级 |
| 取值 | 缺失 = 由用户自己的选择决定；`0`（Security/Off）或 `1`（Required/Basic）= **阻断，MXC 不收集任何数据** |
| 明确不认 | 文档写明**刻意不认**每用户级的 `HKCU` 等价项 |

它的核心表述是「**这是个天花板，从来不是一份授权**」（ceiling, never a grant）。也就是说管理员可以收紧，但**不能替用户给出同意**。默认路径上，遥测需要四个条件同时成立：单次运行主动 opt-in、Windows 用户明确同意、管理员策略允许收集、你的应用在请求里打开遥测开关。另外：**本地开源构建不配置向微软上报遥测**，且非 Windows 平台上遥测是 no-op。

## 六、读完之后值得带走的四条

1. **统一的隔离抽象，必须带拒绝语义。** 一个策略层的价值，取决于它在后端兑现不了的时候会不会报错。MXC 把「bwrap 在创建前拒绝做不到的请求」写进文档，这是整套设计里最扎实的一处。
2. **默认值就是产品。** 省略即 `deny`、`hostLoopback` 独立申请、显式阻断优先于放行，这几条决定了使用者「忘了配」时的实际安全水位。
3. **能力差异不能靠读者猜。** 「更弱的部署」「不等价于保证」「尽力而为的拆除」这些句子，比任何安全宣传都更有价值，因为它们直接决定了你该在什么场景下用哪个后端。
4. **帮人调试的功能，最容易变成安全漏洞。** `--audit` 关掉全部沙箱保护这件事，作者选择用警告框正面写出来，并同时提供 deny-and-record 这条安全路径。这是处理这类「开发者体验 vs 安全」张力的正确姿势。

这跟上一篇谈钓鱼防御的结论是同一条：**安全设计的关键不是宣称强度，而是把这一层到底保证什么、不保证什么讲清楚。** MXC 在这一点上做得比它的功能列表更值得看。

## 关键事实速查

| 项目 | 内容 |
|---|---|
| 项目 | Microsoft eXecution Container（MXC），MIT |
| 时间线 | 2026-02-06 创建，2026-10-09 最近提交，490 commits |
| 热度 | 2,050 stars / 113 forks / 52 open issues |
| 定位 | SDK 依赖，不是常驻服务；应用内嵌后拉起沙箱 |
| SDK | Rust `mxc-sdk` / .NET `Microsoft.Mxc.Sdk` / Node `@microsoft/mxc-sdk` |
| 执行器 | `wxc-exec.exe`（Win）/ `lxc-exec`（Linux）/ `mxc-exec-mac`（macOS） |
| 后端数 | 9（ProcessContainer、Windows Sandbox、LXC、Bubblewrap、Seatbelt、MicroVM/Nanvix、Hyperlight、IsolationSession、WSLC） |
| 默认后端 | Windows `processcontainer` / Linux `bubblewrap` / macOS `seatbelt` |
| Schema | 稳定 1.0.0；dev 1.1.0-alpha；方向性网络契约自 0.9.0-alpha；更早契约直接拒绝 |
| 默认策略 | egress/ingress 省略即 deny；`hostLoopback` 需显式申请；显式阻断优先 |
| MicroVM 开销 | ~100 ms 冷启动（Windows 热快照）、~100 MB 常驻 |
| 遥测 | 仅 Windows；需 run opt-in + 用户同意 + 策略允许；管理员不能代用户同意 |
| ⚠️ 注意 | `--audit` 关闭全部沙箱安全，绝不可用于不可信代码；Windows Sandbox 拆除是尽力而为 |

## 延伸阅读

- [microsoft/mxc 仓库](https://github.com/microsoft/mxc)
- [Bubblewrap 后端指南](https://github.com/microsoft/mxc/blob/main/docs/backends/bwrap/bubblewrap-backend.md)
- [Seatbelt 后端指南](https://github.com/microsoft/mxc/blob/main/docs/backends/seatbelt/seatbelt-backend.md)
- [Nanvix MicroVM 后端](https://github.com/microsoft/mxc/blob/main/docs/backends/nanvix/nanvix.md)
- [配置 schema 与方向性网络契约](https://github.com/microsoft/mxc/blob/main/docs/schema.md)
- [本站：钓鱼防御打错了层级：域名封不过来，但服务器藏不住](/articles/2026-10-09_phishing-server-layer-aitm/)
- [本站：守住你的「AI 机群」：16 款治理/护栏/红队平台速览](/articles/2026-09-19_ai-fleet-governance-tools/)
