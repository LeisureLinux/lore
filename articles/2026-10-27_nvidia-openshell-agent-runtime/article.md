---
title: "NVIDIA OpenShell：给 AI agent 造一个「默认不给权限」的运行时，而它最狠的一招是形式化验证"
date: 2026-10-27
slug: nvidia-openshell-agent-runtime
tags: [OpenShell, NVIDIA, AIagent, 沙箱, 策略, 形式化验证, SMT, Landlock, seccomp, 凭证, Provider, 网关, Gateway, Kubernetes, Docker, Podman, vkd3d, 供应链安全]
category: 安全/架构
author: FreeLAMP.com
original_source: "NVIDIA/OpenShell 官方仓库 README + docs.nvidia.com 官方文档（Architecture / Policy Prover / Policy Advisor / Sandboxes / Providers）+ 仓库元信息实测"
original_date: 2026-10-24
original_url: "https://github.com/NVIDIA/OpenShell"
description: "NVIDIA 开源了 OpenShell —— 一个「面向自主 AI agent 的安全、私密运行时」。它的核心不是又一个容器沙箱，而是两件事的组合：内核级强制（Landlock + seccomp user notification + 网络围栏 + 凭证不出沙箱），以及在策略变更生效**之前**用 SMT 求解器做形式化验证，把「新可达的主机 / 新的 HTTP 方法 / 云元数据地址」变成必须人工审批的发现。本文拆解它的架构（gateway / supervisor / sandbox 三段式）、Sandbox Protocol、fail-closed 设计、以及 prover 的四种结论（within_boundary / exceeds_boundary / unsupported / inconclusive）—— 并指出它最大的未解问题：形式化验证覆盖的是模型里的东西，模型之外的一切都是「unsupported」。"
published: true
---

> 来源：[NVIDIA/OpenShell 仓库](https://github.com/NVIDIA/OpenShell)（README 全文）、[官方文档 Architecture](https://docs.nvidia.com/openshell/latest/about/architecture)、[Policy Prover](https://docs.nvidia.com/openshell/latest/how-it-works/policies/prover)、[Policy Advisor](https://docs.nvidia.com/openshell/latest/how-it-works/policies/advisor)、[Manage Sandboxes](https://docs.nvidia.com/openshell/latest/how-it-works/sandboxes/overview)、[Providers](https://docs.nvidia.com/openshell/latest/how-it-works/providers/overview)
> 实测仓库元信息（2026-10-27 抓取）：**`NVIDIA/OpenShell`**，**Apache-2.0**，创建于 **2026-02-24**，**20,015 stars / 1,978 forks / 583 open issues**，主语言 **Rust**，最近推送 **2026-10-26**。
> 本文为**解读**。第七、八节的评价为笔者补充。

## 一句话结论

**OpenShell 不是一个「新沙箱」，而是一个「agent 权限治理系统」，而它最值得学的设计是：** **不要在策略生效之后才检查它有没有越界，而是在生效之前就用 SMT 求解器证明它不会越界。**

**官方原话：**

> **「OpenShell 通过两种方式治理 agent 能做什么：它在运行时插桩内核，在每一次文件访问、系统调用和网络连接上强制执行策略；它用形式化验证在策略变更被应用之前检查它会允许什么。」**

**而我认为这两件事的组合，恰好补上了 2025–2026 年 agent 安全领域最大的两个缺口：**

| 缺口 | 现有做法 | OpenShell 的做法 |
|---|---|---|
| **agent 能碰到什么** | 容器 + 挂载 + 网络策略，**靠配置正确** | **内核级强制（Landlock/seccomp）+ 每次出网都要过策略检查** |
| **策略本身是否安全** | 靠人肉 review diff | **SMT 求解器给出反例（counterexample）** |

## 一、先看它的自我定位

**README 的第一句：**

> **「OpenShell is the safe, private runtime for fleets of autonomous AI agents.」**
>
> **「Agents are most useful when they can read files, install packages, call APIs, and use credentials. OpenShell gives them that capability without giving them unrestricted access to your data, secrets, or network. You declare what each agent can touch in a policy, and OpenShell enforces it.」**

**⭐ 注意「fleets（舰队）」这个词。** **它不是给个人跑一个 Claude Code 用的，是给「成群结队的自主 agent」用的。**

**而它的设计目标里最关键的一句在架构文档：**

> **「The **gateway** is the control plane... When you create a sandbox, its **compute driver** provisions a **workload** and a separate **supervisor**, establishes their protected channel, and builds the isolation boundary; the **supervisor** confirms that boundary before starting the **agent** and then connects back to the gateway for policy, credentials, logs, and interactive sessions.」**

**⭐ 「the supervisor confirms that boundary before starting the agent」—— 这一句就是 fail-closed 的全部秘密，后面第五节展开。**

## 二、⭐ 三段式架构：谁在边界里，谁在边界外

**这是整个设计里最值得学的一段，因为它解决了一个「容器沙箱做不到」的经典问题。**

### 2.1 问题：agent 和策略引擎必须在边界两侧

**架构文档说得很直接：**

> **「The **supervisor** and **sandbox** sit on opposite sides of the boundary. The **supervisor** is trusted and makes the decisions. The **sandbox** shares the boundary with the untrusted agent, so it never makes policy decisions. It reports what the agent is trying to do and lets the **supervisor** decide.」**

**⭐ 这句话解决了一个非常实际的困境：**

**如果你把策略引擎和 agent 放在同一个沙箱里（很多「policy agent」的做法），那么 agent 就有可能改掉策略引擎、或者读走策略里的凭证 —— 哪怕那个沙箱是用 rootless 容器做的。**

**OpenShell 的切法是：** **agent 那一侧只有一个「报告者」（sandbox），所有决策都在边界外（supervisor）做。**

### 2.2 官方组件表（原文照录）

| 组件 | 职责 |
|---|---|
| **Sandbox** | **在边界内、与 agent 同侧**。拥有 agent 的进程，知道是哪个程序发起的每个请求，执行进程控制，把 TCP 与 DNS 流量转发给 supervisor。 |
| **Outer network fence** | **拒绝来自 workload 的全部网络出口**，除了到 supervisor 的受保护连接。每个 runtime 用自己的原生工具构建。 |
| **Supervisor** | **在边界的可信侧**。对照策略检查请求、发放凭证、解析 DNS、打开被批准的连接、维持到 gateway 的链路。 |
| **Policies** | 描述 agent 能碰什么：文件、进程、网络目的地、API 调用，以及 provider 凭证可以去哪。 |
| **Providers** | 把「服务名」与「存储的凭证」关联起来。**supervisor 只在策略允许的地方把它交出去。** |
| **Policy prover** | **跑在 gateway 里，用形式化验证检查 agent 提出的网络规则。** |
| **Gateway** | **确认你是谁，并记住关于你所有 sandbox 的一切。** 投递策略与设置、挂载 provider、决定谁能做什么、协调进 sandbox 的连接。 |
| **Compute runtime** | 创建 sandbox、启动 supervisor 与 workload、建立两者之间的私有通道、构建网络围栏。 |

**⭐ 注意最后两行的分工：**

> **「The runtime's job is to build the boundary and prove it's in place. It never decides whether a request is allowed.」**
>
> （runtime 的职责是构建边界并**证明它已就位**。它**从不**决定一个请求是否被允许。）

**—— 这就是「同一套策略在任何地方行为一致」的原因。**

### 2.3 每个 runtime 用自己的原生工具建边界

**这张表是官方给的，我完整照录，因为它说明了「可移植」是怎么做到的：**

| Runtime | supervisor 跑在哪 | 怎么和 sandbox 通信 | 怎么挡住直连出口 |
|---|---|---|---|
| **Docker** | 它自己的容器 | driver 拥有的卷上的认证 Unix socket | **workload 容器关闭网络** |
| **Podman** | 它自己的容器 | driver 拥有的卷上的认证 Unix socket | **workload 容器关闭网络** |
| **Kubernetes** | 它自己的 pod | 带 mTLS 的私有 service | **NetworkPolicy 只允许 supervisor service** |
| **VM** | host 上的一个进程 | 认证 vsock | **guest 没有网络设备** |

**⭐ 关键在于「**The runtime's job is to build the boundary and prove it's in place**」—— 它不是「实现策略」，它是「实现隔离」。**

## 三、⭐ 内核级强制：Landlock + seccomp user notification

**架构文档对当前 Linux backend 的描述非常具体：**

> **「In the current Linux backend, the workload uses one non-root identity and no Linux capabilities. Landlock limits filesystem access; seccomp user notification stages network operations. The **sandbox** identifies the calling executable from trusted process observations.」**

**⭐ 拆开这三个技术选择，每一个都是有意的：**

### 3.1 Landlock：文件系统访问控制

**Landlock 是 Linux 5.13 引入的 LSM 子系统，专门做「路径只降不升」的沙箱化。** **用它而不是 AppArmor/SELinux 的理由是粒度与范围：它管的是「能访问哪些路径」，不涉及 MAC 策略语言与策略载入顺序。**

**⭐ 而且它和「无 capabilities、无 root」组合起来，构成的是一层非常干净的最小权限：进程不是 root，没有 CAP_SYS_ADMIN 之类的东西，文件访问还要再过一遍 Landlock。**

### 3.2 ⭐ seccomp user notification：把「网络连接」变成可拦截事件

**这是整套设计里最关键、也最漂亮的一处。**

**传统做法是 seccomp BPF 直接 `SECCOMP_RET_ERRNO` 或 `SECCOMP_RET_KILL` —— 也就是说，系统调用在过滤器的 BPF 程序里被判定，然后直接返回一个错误码给 agent。**

**而 `SECCOMP_USER_NOTIF` 换了一种玩法：过滤器不自己决定，而是把这次系统调用「挂起」，交给一个在用户空间里的 supervisor 进程去处理 —— supervisor 可以返回任意结果，也可以放行。**

**⭐ 所以 OpenShell 的做法是：** **agent 的每一次 `connect()` 和每一次 DNS 查询，都会变成一个「事件」送到 supervisor 那里，由 supervisor 对照策略决定放行还是拒绝。**

**这正是「every network connection passes through a policy check before it leaves the sandbox」这句话的实现方式。**

### 3.3 ⭐ 从可信 `/proc` 识别「是哪个程序发起的」

**这是我认为整套设计里最容易被低估、但安全价值极高的一处：**

> **「Identifies the calling executable from trusted `/proc` data.」**
> **「The real program behind each request, not a path the agent claims.」**
>
> （从可信的 `/proc` 数据识别调用方可执行文件 —— 是请求背后**真实的那个程序**，而不是 agent 声称的路径。）

**⭐ 因为策略的粒度是「按程序授权」而不是「按请求授权」：**

**官方在 Sandbox 的能力列表里写得很清楚：`--gpu`、`--cpu`、`--memory` 之外，还有 —— 策略里可以限定「**某个二进制**可以访问某主机某端口」。**

**Advisor 文档里也是这个措辞：「A proposal is a network rule scoped to the host, port, and binary that need access.」**

**—— 而如果这个「binary」是 agent 自己报上来的，那它就可以直接撒谎**（「我假装我是 `/usr/bin/curl`」）。**所以这个身份必须从内核侧可信地取 —— 这就是 `/proc` 的作用。**

**⭐ 这是整套设计里「防 agent 欺骗」做得最扎实的一处，而且它没有任何魔法，就是老老实实读 `/proc`。**

## 四、⭐ Sandbox Protocol：一条连接，多路流

**通信层的设计也值得看：**

> **「The **supervisor** and **sandbox** talk over the OpenShell Sandbox Protocol: one mutually authenticated HTTP/2 connection that carries many independent streams. The compute driver picks the transport: a Unix socket for Docker and Podman, TCP for Kubernetes, or vsock for MicroVM. Authentication and protocol behavior are the same on all of them.」**

**⭐ 也就是说：传输层随 runtime 变，但协议与认证行为完全一致。**

**而流的设计有一个很实际的理由：**

> **「Each TCP connection gets its own stream with its own backpressure, so a slow download can't block DNS, exec, or process control.」**
>
> （每条 TCP 连接有自己独立的流和独立的背压，所以**一个慢速下载不会阻塞 DNS、exec 或进程控制**。）

**—— 这是一个被很多同类系统忽略的细节：agent 正在下载一个 10GB 文件时，你仍然要能 exec 进沙箱去打断它。**

**⭐ 而一次网络请求的完整旅程（官方五步）值得逐字记住：**

> **「1. The agent opens a TCP connection or makes a DNS lookup.
> 2. The **sandbox** identifies the calling program.
> 3. The request travels over the Sandbox Protocol to the **supervisor**.
> 4. The **supervisor** checks it against policy and adds any credentials policy allows.
> 5. If allowed, the **supervisor** opens the real connection and relays traffic.」**

## 五、⭐ fail-closed：三条「保证」

**架构文档给了一张我认为非常值得抄的表 —— 它把「安全保证」和「由谁提供」明确对应起来：**

| 保证 | sandbox 怎么提供 | supervisor 得到什么 |
|---|---|---|
| **进程所有权** | 把 agent 作为**受管的子进程**运行，保留其进程与终端状态。 | 可以等待、附加、发信号、exec、停止 agent 的句柄。 |
| **程序身份** | 从可信 `/proc` 数据识别调用程序。 | 请求背后**真实的程序**，而不是 agent 声称的路径。 |
| **网络中介** | 用 seccomp 拦截 TCP open 与 DNS 查询并上交。 | **在去往任何地方之前，先等待一个策略决定**。 |
| **Fail closed** | **在 supervisor 确认之前不放行启动；连接断开时冻结 agent。** | 一个短暂的重连窗口，或者一个已停止的 workload。 |

**⭐ 第四行是整套设计的安全基石。官方给了一句总结：**

> **「Together these mean the agent can't run before its controls are confirmed, signals and exec reach only this sandbox's processes, and the agent can't get around TCP or DNS mediation.」**

**而且关于断连，官方写得更狠：**

> **「If the **supervisor** disconnects, the **sandbox** freezes the agent. Only the same **supervisor** process can reconnect and resume it. A new **supervisor** can't take over a running sandbox, even with valid credentials.」**
>
> （supervisor 断开时，sandbox **冻结** agent。**只有同一个 supervisor 进程**能重连并恢复它。**一个新的 supervisor 即使拿着有效凭证也不能接管一个正在运行的 sandbox。**）

**⭐ 最后半句值得反复读：它意味着「拿到凭证」和「能接管」是两件事 —— 一个被攻破的 supervisor 凭证无法横向接管别人的 sandbox。**

## 六、⭐⭐ Policy Prover：形式化验证的那一半

**这是我认为 OpenShell 最值得写的部分，也是它的「杀手级差异」。**

### 6.1 它做什么

**官方文档：**

> **「The policy prover is OpenShell's policy verification engine. It uses an SMT solver to check whether policies satisfy specified properties, such as staying within an allowed access boundary. Its guarantees apply to the policy features and behavior represented by its model. OpenShell is actively extending the model to cover more policy features.」**
>
> **「它使用一个 SMT 求解器检查策略是否满足指定的属性，比如「保持在允许的访问边界内」。**它的保证只适用于其模型所表示的策略特性与行为。OpenShell 正在积极扩展模型以覆盖更多策略特性。**」**

**⭐ 注意最后一句 —— 官方自己承认了保证的边界。** **这一句是整篇文章里最重要的免责声明，我会在第八节展开。**

**它有两个检查：**

| 检查 | 回答的问题 | 触发方式 |
|---|---|---|
| **边界检查（boundary check）** | **候选策略是否允许了超过边界策略的访问？** | 手动跑 `openshell-prover` CLI |
| **提案风险检查（proposal risk check）** | **这个新加的网络规则是否引入了风险访问？**（例如触达云元数据地址，或为 provider 凭证新增了目的地） | **每次 agent 提案时自动运行** |

**边界检查覆盖的范围：**

> **「The check covers filesystem access, process identity, Landlock settings, network connections, and REST requests. If a policy uses anything else, such as GraphQL or MCP rules, the prover reports that it cannot check the policy instead of ignoring those rules.」**
>
> （检查覆盖文件系统访问、进程身份、Landlock 设置、网络连接和 REST 请求。**如果策略用了别的东西，比如 GraphQL 或 MCP 规则，prover 会报告它无法检查这个策略，而不是忽略这些规则。**）

**⭐ 最后半句是整个设计里最值得学的一个小细节 —— 见下文 6.4。**

### 6.2 输出格式：给出反例，而不是给出结论

**CLI 的输出长这样：**

```
result: exceeds_boundary
coverage: domains=filesystem,network_l4,network_rest,process,landlock
counterexample: filesystem write /tmp
```

**⭐ `counterexample` 这一行是灵魂：「你的策略允许了边界不允许的 `filesystem write /tmp`」。**

**而退出码是分级的：**

| 结果 | 退出码 | 含义 |
|---|---|---|
| `within_boundary` | 0 | 候选策略在 prover 检查的范围内没有超出边界 |
| `exceeds_boundary` | 1 | 候选策略允许了边界不允许的访问，**并给出反例** |
| `error` | 2 | 检查无法运行（文件缺失、策略非法等） |
| `unsupported` | 3 | **策略用到了 prover 无法检查的东西** |
| `inconclusive` | 3 | **prover 没能跑完**（超时、策略太大） |

**⭐ 这是一个设计得非常好的退出码约定，因为它让「不知道」和「安全」在 CI 里可以被区别对待。** **在 CI 里，`exceeds_boundary`（1）和 `inconclusive`（3）应该都导致流水线失败 —— 但它们的处置方式完全不同。**

### 6.3 两种检查不可互相替代

**官方明确说了这一点，而且我认为这是文档里最重要的一句：**

> **「The two checks answer different questions, so passing one does not imply passing the other. A proposed rule that passes the proposal risk check can still exceed your boundary, and a policy that passes the boundary check can still contain access that the proposal risk check would flag.」**
>
> （两个检查回答的是不同的问题，**所以通过一个并不意味着通过另一个**。通过了提案风险检查的规则，仍可能超出你的边界；通过了边界检查的策略，仍可能包含提案风险检查会标记的访问。）

**⭐ 这个「两个检查互相独立」的架构很聪明，因为它把两类不同的问题分开了：**

- **边界检查 = 「你有没有超出你自己的上限」**（一个**纵向**的问题：agent 能不能突破父 agent / 组织的上限）；
- **提案风险检查 = 「这次新增的访问本身危不危险」**（一个**横向**的问题：新目的地是不是云元数据、是不是通配符）。

### 6.4 ⭐⭐ 「报告无法检查」而不是「忽略」

**我上面提的那句细节，我认为值得单独放大：**

> **「the prover reports that it cannot check the policy instead of ignoring those rules」**

**⭐ 这是一个极其正确、而且极其容易被做错的设计选择。**

**绝大多数「安全检查」工具在遇到不认识的东西时，会**忽略**它 —— 因为忽略最省事，而且不会「误报」。** 但在安全工具里，「忽略」意味着「我以为我检查过了」。**

**OpenShell 的选择是：** **遇到不能检查的东西，明确返回 `unsupported`（退出码 3）。**

**⭐ 而它的直接后果是文档里那句警告：**

> **「Its guarantees apply to the policy features and behavior represented by its model.」**
>
> **「The prover does not add provider rules itself.」**（检查 sandbox 的有效策略时，**必须自己把 provider 加进去**，prover 不会替你加。）

**—— 也就是说：你以为 prover 帮你检查过了，实际上它没有。** **而这个事实被明明白白写在了文档里。**

### 6.5 ⭐ 它还能被 agent 用来自我约束

**这是我觉得最巧妙的一处设计：**

> **「You run a boundary check with the `openshell-prover` CLI, which is primarily intended for agents. For example, a parent agent can check that a policy it writes for a subagent stays within the parent's own maximum allowed policy.」**
>
> （`openshell-prover` CLI **主要是给 agent 用的**。例如，**父 agent 可以检查它为子 agent 写的策略是否仍在父 agent 自己的最大允许策略之内**。）

**⭐ 也就是说：这不是一个「管理员在事后检查」的工具，而是一个 **agent 可以在写策略时自我调用**的验证器。**

**而官方还补了一句：CLI 读本地策略文件，不需要 gateway，也不应用或批准策略。**

**—— 这意味着它可以放进 CI，也可以放进 agent 的工具循环。**

## 七、⭐ Policy Advisor：把「agent 被卡住」变成一个可审批的工作流

**如果只有 prover 而没有 advisor，那 OpenShell 会在实践中被绕开 —— 因为 agent 被网络策略挡住之后，除了放弃没别的办法。**

**Advisor 解决的问题正是这个：**

> **「Without the policy advisor, an agent whose request is blocked usually cannot finish its task until someone changes the policy by hand. With it, the agent can request the access it needs.」**
>
> **「The policy advisor is off by default. When you enable it, OpenShell gives the agent instructions and a local HTTP API for submitting proposals. A proposal never changes the policy on its own. By default, every proposal waits for your review.」**

**⭐ 五个步骤（官方原文）：**

> **「1. 沙箱里一个进程发出被策略拒绝的网络请求。OpenShell 在拒绝一个被检查的 HTTP 请求时，响应里会说明什么被挡住了，并告诉 agent 如何申请访问。**
> **2. agent 阅读沙箱里的 policy advisor 指南，查看当前策略，提交一个提案。提案是一个网络规则，限定到需要访问的 host、port 和 binary，对 HTTP API 还限定 method 和 path。**
> **3. OpenShell 验证提案并用两种方式检查它新增的风险：policy prover 运行提案风险检查，比较「有这条规则」和「没有这条规则」时沙箱分别能到达什么；OpenShell 还标记常被列为风险的目的地，比如私有网络地址和通配符主机。然后把提案和两项检查的结果加进 sandbox 的待处理提案。**
> **4. 你批准或拒绝。开启自动批准时，通过风险检查的提案会被直接批准。**
> **5. agent 等待决定。批准后 sandbox 载入新规则，agent 重试请求；被拒绝时 agent 收到你的理由，可以提交一个更窄的提案。」**'

**⭐ 而设计上有两个「防滥用」的细节：**

1. **「A proposal can add a network rule, but it cannot remove rules or change filesystem, Landlock, or process settings.」**
   —— **提案只能「加」，不能「减」。** **agent 不能通过提案来放宽自己的文件访问或进程权限。**

2. **⭐ 而且 advisor 关着的时候，OpenShell 也会自动起草提案：**
   > **「OpenShell also drafts proposals on its own from connections that it blocks, in every sandbox, whether or not the policy advisor is enabled.」**
   > **「Each draft allows one binary to reach one host and port.」**

   —— **而且被挡住的请求「保持被拒绝状态」，要等批准并载入规则后才能重试。**

**⭐ 我认为这一条是整个 advisor 设计里最漂亮的地方：它把「被拒绝」变成了一个**持续存在的事实**，而不是一个瞬时错误。** **agent 不会因为一次失败就以为「这条路走不通了」然后放弃或换招 —— 它必须等你批准。**

### 7.1 沙箱里给 agent 放了什么

> **「A guide at `/etc/openshell/skills/policy_advisor.md`... an agent skill at `/etc/openshell/skills/policy-advisor/SKILL.md` and, if the image does not already have one, `/AGENTS.md`.」**
>
> **「The `policy.local` API, which the agent uses to read the current policy and recent denials, submit proposals, and wait for decisions. OpenShell serves it at `http://policy.local`, which is reachable only from inside the sandbox and needs no network rule or proxy setting.」**

**⭐ 注意 `http://policy.local` 这个设计：它只在沙箱内可达，不需要网络规则、不需要代理设置。** **—— 也就是说，「申请权限」这条通道本身永远不会被策略挡住。** **这在设计上很重要：否则 agent 会陷入「连申请都发不出去」的死锁。**

## 八、⭐ 我的评价：它解决了什么，以及它最大的未解问题

### 8.1 它真正解决的问题

**⭐ 我认为 OpenShell 的贡献有三个层次，重要性递减：**

**① 架构层：「决策者必须在边界外」**

**这一条本身就可以写一篇论文。** **因为它把「agent 沙箱」这个问题的重心，从「怎么把 agent 关起来」转成了「怎么让 agent 看不见策略和凭证」。**

**② 机制层：seccomp user notification 作为网络中介**

**它让「按程序、按目的地授权」成为可能，而且不需要写 BPF 也不需要 root 特权。**

**③ 方法层：形式化验证作为审批前的关卡**

**⭐ 这一层是范式级的。** **「不要问『这个策略看起来合理吗』，要问『能不能证明这个策略不越界』」—— 而 SMT 求解器给出的答案是带反例的。**

### 8.2 ⭐ 但它最大的未解问题，是「模型之外」

**官方文档里那两句话，必须和任何关于 OpenShell 的宣传一起读：**

> **「Its guarantees apply to the policy features and behavior represented by its model.」**
>
> **「If a policy uses anything else, such as GraphQL or MCP rules, the prover reports that it cannot check the policy instead of ignoring those rules.」**

**⭐ 我的判断是：**

**在 2026 年这个时间点，**  **`unsupported` 这个出口覆盖的，恰恰是最要紧的那部分策略。****

**为什么？因为今天 agent 用的最多的两类工具访问方式，恰好是 prover 覆盖不到的两类：**

- **MCP（Model Context Protocol）** —— agent 调工具的主流通道；
- **GraphQL** —— 一大堆现代 API 的主流形态。

**而 REST 是 prover 覆盖得最好的那一种 —— 恰恰是相对最容易做结构化匹配、也相对最容易「猜对」的那一种。**

**⭐ 所以真正诚实的表述应该是：**

> **OpenShell 形式化验证的，是「agent 能不能连到某个 host 的某个 path、带着某个凭证」这类问题。**
> **而「agent 能不能通过 MCP 工具调用做某件事」—— 这个在 2026 年才是权限治理的主要战场 —— 目前只能靠人工审批（advisor），不能靠自动证明。**

**而这恰恰说明 OpenShell 的 advisor 设计是对的：把不能形式化验证的部分，交给人；但把**能**验证的部分，从人手里拿走。**

### 8.3 另一个我认为值得提的观察：它的整个设计是「把 agent 当成不可信」

**从架构到认证，每一处都在做同一件事：假设 agent 会说谎、会试图越权、会试图冒充别的程序。**

**三个具体的例子：**

1. **程序身份来自 `/proc`，不是 agent 的自述；**
2. **agent 那一侧没有 gateway 签名密钥、没有 gateway JWT、没有 provider 凭证** —— 官方原文：「The **sandbox** holds nothing worth stealing」；
3. **sandbox JWT 只含 gateway 的公钥** —— 官方原文：「The **sandbox** holds only the gateway's public key, so it can verify the token but can never create one.」

**⭐ 而我最欣赏的一句在架构文档结尾：**

> **「It can verify that it's talking to the right **supervisor**, but it can't impersonate one.」**
>
> （它能验证自己在跟**对的** supervisor 说话，但**它无法冒充一个 supervisor**。）

### 8.4 ⭐ 一个我特别想指出的对比：它和 Emaki 的 `sudo key`

**本号此前写过 Emaki（一个基于 Arch + niri 的完整桌面），里面有一个专门给 AI agent 用的 `emaki-sudo-key` 包：给 agent 限时、可见、可一次撤销的管理员权限。**

**⭐ 把这两个东西放在一起看，会发现它们在解决**同一个问题的两端**：**

| | **Emaki 的 sudo key** | **NVIDIA 的 OpenShell** |
|---|---|---|
| **核心问题** | agent 要执行特权命令 | agent 要访问文件/网络/凭证 |
| **粒度** | 时间 / 轮数 / 整个会话 | **按 host + port + binary + method + path** |
| **可见性** | 面板指示器 | gateway 的提案列表 |
| **撤销** | `Super+Ctrl+Esc` 一次全撤 | 拒绝提案 / 删除 sandbox |
| **审批** | 人工发起 | **agent 提案 → 自动风险检查 → 人工/自动批准** |
| **⭐ 形式化验证** | 无 | **有（SMT prover）** |

**—— 而我认为 OpenShell 补上了 Emaki 那一侧最缺的东西：** **Emaki 的 sudo key 是「粗粒度的临时提权」，OpenShell 是「细粒度的、带形式化检查的按资源授权」。** **前者适合「让 agent 跑个脚本」，后者适合「让 fleet 里的 agent 长期在生产环境干活」。**

**（顺带一提：OpenShell 的 README 里有一节专门叫「Agent Skills」，教 agent 怎么用 OpenShell CLI、写沙箱策略、调试 gateway 和推理路由 —— 这和 Emaki 那种「往沙箱里塞 SKILL.md」的思路是同一个方向。）**

### 8.5 ⚠️ 也要说清楚它的边界

**① 20,015 stars、583 open issues、创建于 2026-02-24（八个月）** —— **这是一个非常年轻、非常快的项目。** **README 里那句「New in OpenShell 0.1.x: a stable release cadence」以及反复出现的 `experimental` 标记，说明它还在快速变动。**

**② 形式化验证的模型在扩展中** —— 官方明说「OpenShell is actively extending the model to cover more policy features」。**所以今天你拿到的 prover 保证范围，取决于你用的版本。**

**③ 它不替代你现有的容器编排** —— 它是**套在** Docker/Podman/Kubernetes/VM **之上**的一层。**如果你的底层 runtime 本身被攻破，OpenShell 的保证就无从谈起（虽然 supervisor 在边界外这一点能缓解一部分）。**

**④ 遥测默认开启**（可关）：官方说只收集「运营类别的计数」，不收集 sandbox 名、主机名、文件路径、提示词、凭证、provider 或模型名、用户内容。**并且「你也可以完全把遥测编译掉」。**

## 九、如果要试

```sh
# 安装（CLI + 本地 gateway）
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh

# 建一个沙箱
openshell sandbox create --name demo

# 跑一个真实 agent（官方示例：OpenCode + 免费 OpenRouter 模型）
# 见 Run Your First Agent

# 给 agent 装官方 skills（教它怎么写策略、怎么调试）
npx skills add NVIDIA/OpenShell

# 把 prover 放进 CI：对边界跑一次检查
openshell-prover --help
```

**需求：** **Linux、macOS on Apple Silicon、或 Windows with WSL 2（实验性）**，外加 **Docker、Podman 或宿主虚拟化**。

**⭐ 如果你是做 CI 的：**

**`openshell-prover` 的 CLI 不需要 gateway，也不需要应用策略 —— 它只读本地策略文件。** **所以把它做成一条流水线检查（"候选策略是否在边界内"）是最省事的接入方式。** **而退出码 3（`unsupported` / `inconclusive`）应当按失败处理 —— 否则你就重蹈了「以为检查过了」的覆辙。**

## Sources

- NVIDIA/OpenShell 仓库（README）：https://github.com/NVIDIA/OpenShell
- 官方文档 Architecture：https://docs.nvidia.com/openshell/latest/about/architecture
- 官方文档 Policy Prover：https://docs.nvidia.com/openshell/latest/how-it-works/policies/prover
- 官方文档 Policy Advisor：https://docs.nvidia.com/openshell/latest/how-it-works/policies/advisor
- 官方文档 Manage Sandboxes：https://docs.nvidia.com/openshell/latest/how-it-works/sandboxes/overview
- 官方文档 Providers：https://docs.nvidia.com/openshell/latest/how-it-works/providers/overview
- 官方文档 0.1.0 升级指南：https://docs.nvidia.com/openshell/latest/upgrade/0-1-0
- 仓库元信息：https://api.github.com/repos/NVIDIA/OpenShell
- 官方文档站：https://docs.nvidia.com/openshell/latest/index.html

---

（说明：所有引号内内容为官方文档/README 原文引用；第七、八节的评价、8.4 节的 Emaki 对照、以及第九节的 CI 建议为笔者补充。第八节 8.2 关于「MCP/GraphQL 恰在覆盖之外」这一判断，依据的是官方文档列出的覆盖范围与 `unsupported` 语义，属笔者推断，官方未就 MCP 做此评价。）
