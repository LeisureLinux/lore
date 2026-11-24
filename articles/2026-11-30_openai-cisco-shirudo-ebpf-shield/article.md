---
title: "OpenAI 开源 Shirudo：补丁没来，先用 AI 生成的盾牌挡漏洞"
date: 2026-11-30
slug: openai-cisco-shirudo-ebpf-shield
category: 技术/解读
author: FreeLAMP.com
original_source: "OpenAI 官方公告《OpenAI and Cisco introduce Shirudo》（2026-11-23）＋ 一手核对 Isovalent/Cisco 技术博客（含 Java4Shell 对 Elasticsearch 的完整演示与日志）、shirudo-dev/shirudo GitHub README（架构、许可证、系统要求）、docs.shirudo.dev Quickstart（签名/加载/TPM 验证全流程）＋ 本号 Java4Shell（CVE-2026-114938）文章交叉核对。"
description: "解读 OpenAI 与 Cisco 开源的 Shirudo（日语「盾」）：一个 eBPF 运行时安全平台，让防守方在补丁测试和部署的数天/数周窗口里，用临时 shield/upatch 保护仍在运行的 Linux 系统与工作负载而不重启。梳理四项核心能力（live protection、machine-speed defense、trusted deployment、hardware-backed verification）、架构（一次性 CLI、Tetragon 血统、签名 .bee/OCI 分发、TPM 测量、signed-loader ABI）、Codex 自动生成 Java 字节码盾牌拦截 Java4Shell 对 Elasticsearch 的实测（Base64 guard installed/rejected candidate 日志）、许可证（BSD-2-Clause，BPF 双 BSD/GPL）、预发布状态与硬件/内核要求，并辨析它和 live patch、WAF、杀硬机制的区别与边界。"
published: true
---

补丁从发布到装到每台机器上，往往要几天甚至几周。这段时间里，防守方能做什么？把有漏洞的系统调用整个禁掉，服务就下线了；不禁，就可能被打。OpenAI 和 Cisco 给出的答案叫 **Shirudo**——日语「盾」，一个 11 月 23 日开源的 eBPF 运行时安全平台：让 Agent 写出针对性的临时防护，签名后热加载到正在运行的系统上，**不重启、不打断负载**。

演示用的漏洞，正是本号写过的 **Java4Shell（CVE-2026-114938）**：Codex 生成的一段防护，拦住了一次针对运行中 Elasticsearch 的利用尝试。

## 一、为什么需要它：漏洞和补丁之间的那段真空

OpenAI 在公告里把问题说得很清楚：「找到 bug 不等于明天就能给每个系统打上补丁。」而临时防护难做，是因为**攻击请求和正常请求可能走的是同一条 Linux 操作路径**——你把那条路径堵死，服务也跟着停了。

Shirudo 的思路是「精准堵住暴露漏洞的那个分支，放行正常请求」。它的血统来自 Cisco 旗下 Isovalent 2022 年开源的 **Tetragon**（eBPF 运行时安全平台），也是 Cisco 现有 Live Protect 能力的基础。Isovalent 的博客打了个很好的比方：**eBPF 让操作系统像 JavaScript 让浏览器那样可编程**——不用更新或重启，就能加载小程序去观察、增强甚至替换系统行为；而内核的 verifier 会先检查每个 eBPF 程序的安全性。

## 二、四项核心能力

OpenAI 列的四条，基本就是这套系统的设计骨架：

1. **Live protection（在线防护）**：eBPF shield 可以在不重启系统的情况下阻断有漏洞的代码路径；在强制生效前，安全团队可以先观察这个 shield 会怎样影响应用。
2. **Defense at machine speed（机器速度的防护）**：Agent 拿到可编程的控制面，去调查漏洞、开发针对性 shield、并用真实利用和真实负载验证效果——**最终部署什么，由人来决定**。
3. **Trusted deployment（可信部署）**：shield 在加载前做密码学签名与验证；Linux 的 eBPF verifier 检查程序是否符合安全规则；内核安全控制限制未授权的改动。
4. **Hardware-backed verification（硬件支撑的验证）**：用 TPM 记录「防护被加载或移除」的可验证证据，运维方据此核对系统是否满足安全要求。

## 三、架构：一次性 CLI、签名 upatch、TPM 测量

从 GitHub README 和 Isovalent 博客拼出完整架构：

- **没有常驻 daemon**：Shirudo 是一次性 CLI——目标机器上不需要一直跑 agent，构建和分发签名包的运维机上也不需要。目标机上的控制面是**开机时加载进内核的 eBPF 程序**。
- **upatch（微补丁）**：要部署的防护叫 upatch——一小段逻辑自洽的程序，可以是 eBPF（内核 hook 处阻断），也可以是 **Java 字节码**（保护应用层代码）。打包成签名的 `.bee` 包，通过 **OCI registry** 分发；目标机 pull 下来，用 TPM 验证签名建立信任。
- **开机即强制**：生产目标上，`shirudo init` 从 initrd 阶段就挂上守卫，保护 Shirudo 自己的运行时和状态——**即使目标机上是 root，没有运维方的签名密钥也改不了**。
- **签名与密封**：BPF upatch 的加载/卸载只能由内核针对 sealed `.bpf` keyring 验证过的 loader 完成；Java upatch 在用户态验证，配置好的 JVM 启动时加载 agent。
- **TPM 测量**：每次 upatch 集合变化都会扩展一个按启动周期存在的 TPM 寄存器；`shirudo attest` 返回证据，运维方可以**离线验证**。Quickstart 里那串验证输出很能说明问题：nonce 匹配、AK/EK 密钥固定且签名有效、quote 覆盖 PCR、事件日志重放出预期的寄存器值……每一步都是可密码学验证的。

这套东西的威胁模型很明确：**假设目标机器本身可能被攻陷**，所以防护状态不能靠机器自己说了算，要靠 TPM 证据和外部验证。

## 四、Java4Shell 实战：Codex 生成盾牌，挡住对 Elasticsearch 的攻击

这是整套叙事里最硬的部分。Isovalent 博客记录了全过程：

1. 把 Java4Shell 的漏洞信息喂给以 Codex 为控制面的 Agent；
2. Agent 自动生成**漏洞复现**、验证利用、评估最有效的缓解点（eBPF？Java runtime？）、生成并验证缓解代码——不成功就重复；
3. 缓解代码被签名、滚动部署到受影响节点，持续监控应用健康度；
4. 部署后，shield 的「hit 计数」就代表针对该漏洞的**实际利用尝试**。

对 Java4Shell，Agent 生成的不是 eBPF 程序，而是**Java 字节码修改**：注入到任意 Java 应用，在 `java.util.Base64$Decoder.decode0` 上加输入校验，防止那个越界覆盖。他们在运行中的 **Elasticsearch 9.5.5** 上做了演示——shield 直接 attach 到运行中的进程，然后发起利用；攻击失败，日志里留下了证据：

```
"message": "Base64 guard installed on java.util.Base64$Decoder.decode0 (classfile)"
"message": "Base64 guard rejected candidate: length=65, padding=1, remainder=1, alphabet=standard"
```

还记得 Java4Shell 的触发条件吗？**64 个 A 加一个 `=`**——正好是日志里那个 `length=65, padding=1`。盾牌精准地卡在那个位置上，Elasticsearch 全程没重启。

证明「Agent 可以写 eBPF / 字节码级别的缓解」这件事，比这次具体挡住哪个漏洞更重要。Isovalent 说得很直白：Agent 不介意逆向几百万行汇编代码，所以与其把 Agent 限制在人类可读的策略语言里，不如让它**用代码以机器速度生成缓解**。

## 五、现状与边界：别急着上生产

几个必须说清的限定：

- **Shirudo 是 pre-release**。README 写明：生产目标需要带 signed-loader ABI 的 Linux 内核 **和 Shirudo 自己的内核补丁**，外加 **TPM 2.0**。这不是 `apt install` 一下就能用的东西。
- **架构支持有限**：CI 在 x86-64 上跑全部测试层、arm64 上跑 host 测试，测试 VM 本地也能在 arm64 启动；**riscv64 的目标验证还在进行中**。运维机和目标机可以不同架构。
- **Quickstart 用软件 TPM**（swtpm），跑在带 KVM 的 Linux 主机上，要求 `/dev/kvm` 可读写、`ulimit -l` 为 unlimited——这是让你在 VM 里走完「签名→加载→TPM 验证→卸载」全流程的实验环境，不是生产配置。
- **它不是 WAF，也不是 live patch**。eBPF 版本更接近「内核 hook 处的行为过滤 + 用户态字节码注入」的组合；覆盖面取决于能不能找到那个既挡攻击又不伤正常流量的检查点。OpenAI 自己也把它定位为「补丁推出前的临时防护」，不是永久修复。
- **谁来担保 shield 本身？** 签名和 verifier 保证「加载的是授权方签过的代码」，但不自动保证这段 Agent 生成的代码逻辑正确。OpenAI 的设计里，Agent 要自己反复验证缓解是否有效，最终由人批准部署——这道人工关卡是整套信任链的关键。

## 六、把它放进这份清单里看

从这一年的漏洞潮看，Shirudo 是对「补丁节奏跟不上漏洞发现节奏」的直接回应：AI 让挖洞变快（本号写过的 APT 砍功能、Zstd 提前发版都是例证），那么防守侧也要用 AI 把**缓解**的速度提上去。OpenAI 的长期目标写得很完整：让防守方和 AI Agent 快速定位受影响系统、验证防护、部署 eBPF shield 阻断利用而不打断负载；应用只拥有所需权限，由自动生成和维护的策略治理；再加上硬件支撑的证明与独立网络控制，即使单机被攻陷也能恢复到一个经过验证的已知良好状态。

这个愿景很宏大，但眼下的第一步很具体：BSD-2-Clause 许可证（BPF 程序双 BSD/GPL）、代码开在 GitHub、附 Quickstart VM 和 Isovalent 的自助实验环境。对想验证这套思路的人，最短路径是照 Quickstart 走一遍——它会带你把一个挂 `do_nanosleep()` 的空 upatch 一路签名、加载、用 TPM 验证、再卸载。

> 公告原文里 Greg Brockman 那句话很能概括动机：「我们给防守方更好的模型和工具，更快发现和修复漏洞——但今天发现一个 bug，不意味着明天就能给每个系统打上补丁。」

## 参考资料

- OpenAI 官方公告：https://openai.com/index/introducing-shirudo/
- Cisco/Isovalent 技术博客（架构与 Java4Shell 实战）：https://isovalent.com/blog/post/cisco-openai-shirudo/
- GitHub 仓库（README、架构、许可证）：https://github.com/shirudo-dev/shirudo
- 官方文档 Quickstart：https://docs.shirudo.dev/start/quickstart.html
- LPC 2026 技术演讲：https://lpc.events/event/20/contributions/2437/
- Java4Shell（CVE-2026-114938）Calif 研究：https://calif.io/java4shell
- 本号相关阅读：《Java4Shell：OpenJDK Base64 解码器的 AVX-512 溢出》
