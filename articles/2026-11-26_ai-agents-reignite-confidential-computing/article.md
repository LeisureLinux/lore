---
title: "Intel TDX 被 AI Agent 重新点着：模型只回答，Agent 会动手"
date: 2026-11-26
slug: ai-agents-reignite-confidential-computing
category: 技术/解读
author: FreeLAMP.com
original_source: "Computerworld《AI agent security concerns kick-start confidential computing》（Agam Shah，2026-11-23，6 分钟分析）＋ 一手核对：Intel Newsroom《Confidential Computing - Growing Momentum, Sharpened Focus》（Mike Ferron-Jones，2026-10-09）、Fortanix 新闻稿《Confidential AI on CNCF Confidential Containers (CoCo)》（2026-10-18）、Apple Security Research《Expanding Private Cloud Compute》（2026-06-08）＋ 本号此前三篇机密计算文章交叉核对。"
description: "解读 Computerworld 分析：AI Agent 失控事件频发，让「保护使用中数据」的机密计算重新升温。核心论点来自 Greyhound Research 的 Sanchit Vir Gogia：「模型只回答，Agent 会动手」「没有权限的 Agent 是话多的实习生，权限失控的 Agent 是一份正等着你的事故报告」。梳理 TEE 的工作原理与采用障碍（速度、成本、复杂度、排障困难）、Intel 把路线图收敛到 TDX 并用 Diamond Rapids 送走 SGX（2027，支持到 2030 年代初）、Fortanix Confidential AI 支持 CNCF CoCo 与 Intel/AMD CPU + NVIDIA Blackwell/Vera Rubin、Apple PCC 扩展到 Google Cloud（NVIDIA GPU + Intel TDX + Titan 芯片，双独立信任根与仅追加账本）、ServiceNow 内部实践与成本现实，并辨析「机密计算保的是机密性，不是行为正确性」这一边界。"
published: true
---

机密计算（confidential computing）这个概念提出很多年了，一直不温不火。Computerworld 11 月 23 日的一篇分析给出了一个新的解释：过去阻碍它落地的不是信念，而是**成本、稀缺的技能，以及一个尴尬的事实——保护最敏感的工作负载，会让日常排障变难**。而现在，AI Agent 正在改写这笔账。

## 一、一句话说清为什么是 Agent

这篇分析里最值得记住的，是 Greyhound Research 首席分析师 Sanchit Vir Gogia 的两句话：

> 「AI 改变了威胁模型。模型只回答，Agent 会动手。」

> 「没有权限的 Agent 是个话多的实习生；权限失控的 Agent，是一份正礼貌地等在走廊里的事故报告。」

这个区分是整篇文章的支点。传统大模型的安全讨论聚焦在「它会不会说错话」——幻觉、越狱、提示注入泄露上下文；而 Agent 的语境是**它会调用工具、改数据、发请求、动钱**。一个能行动的实体，配上不受控的权限，风险评估就完全不一样了。Gogia 的原话是：Agent 让机密计算的采用计算式发生了变化。

这正是本号此前写过的那条线索的延续：从 GitBook 被 AI agent 定向攻击、Postman Desktop 自动安装 agent 插件、到各种「agent 越权」事件——**Agent 的安全问题已经从「模型输错」转向「行动失控」**，而机密计算试图回答的是：当 Agent 不得不在别人的机器、别人的云上处理敏感数据时，怎么让数据连基础设施运营者都看不到。

## 二、TEE 到底是什么，为什么以前没人用

机密计算的核心是把数据放进一个叫**可信执行环境（TEE）**的保险箱：由硬件和软件共同保护，外部无法干预；保险箱只有在通过密码学证明「没被篡改」之后才拿到密钥解锁。模型待在保险箱里处理用户查询，只把答案送出来。

传统加密保护传输中和静止的数据，**但不保护正在使用中的数据**——推理时模型权重和提示内容必须在 CPU/GPU 内存里解密，那里对特权管理员、云运营商、能碰到基础设施的人是可见的。TEE 补的就是这个缺口。

Gogia 那句评价很实在：「问题从来不是信不信，而是运营成本、技能稀缺，以及保护最敏感负载会让普通排障变难。」密码学上成立，不等于运维上可落地——这是过去十年 TEE 叫好不叫座的根本原因。

## 三、2026 年的三股推力

Computerworld 点了几件具体的事，我用一手材料核对了一遍，都站得住：

### Intel：路线图收敛到 TDX，SGX 进入倒计时

Intel 平台安全与完整性负责人 Mike Ferron-Jones 在 10 月 9 日的博客里说得很清楚：**Intel 的机密计算路线图聚焦 TDX**。原因是行业已经向「虚拟机隔离」这类技术收敛——它在可扩展性、部署便利性和运维模型上更适合大规模采用。

具体的时间表是本号 10 月 12 日那篇《Intel 让 SGX 在 Diamond Rapids 之后退场》的核心：**Diamond Rapids（2027）是最后一代包含 SGX 的 Xeon**，但已有 SGX 平台会继续得到支持和安全更新到 2030 年代初。这不是「SGX 失败了」，而是「边界选错了」——进程级 enclave 的运维代价太高，VM 级隔离才是云和企业的共同语言。

新的东西是：TDX 已经进了 Microsoft Azure、Alibaba Cloud、Google Cloud、IBM Cloud（以及 Volcano Cloud）；Red Hat、Canonical、VMware 的软件平台也在加 TDX 支持；Intel 还在做 TDX Connect（可信 I/O）、后量子密码和增强证明。Ferron-Jones 引用 Intel 与 NVIDIA 的合作，强调 CPU 与 GPU 的机密计算要**协同**，才能把保护延伸到整条 AI 流水线。他还有一句直接对着欧盟说的：对当地组织而言，问题不再只是「数据在哪」，而是「谁能在什么权威下、用什么技术控制访问它」——这是数据主权叙事的核心。

### Fortanix：把 Agent 塞进容器化的 TEE

Fortanix 在 10 月 18 日宣布其 Confidential AI 支持 **CNCF Confidential Containers（CoCo）**：在 Kubernetes 里跑 AI 工作负载，放进基于硬件的 TEE，覆盖机密 CPU 和 GPU；容器比 VM 更快建立和更新。支持名单里有 Intel、AMD、NVIDIA（Blackwell，Vera Rubin 即将支持）、Red Hat、HPE、Dell、CrowdStrike 等一大串。

产品侧的细节值得记：

- 每个环境在解锁任何数据或模型前都要经过**证明（attestation）**；密钥释放被设计成高可用，不成为单点故障；
- AUR 式的供应链审查思路也在这里出现——Fortanix 的容器方案强调在放开数据前验证环境；
- 部署形态覆盖 SaaS、本地、乃至**完全空气隔离**的环境，面向主权云和监管行业；
- 客户 Deepgram 用它保护语音 AI 模型；其基础设施与物理 AI 合作负责人 Abhishek Arora 说，语音 Agent「不只是转录，还会推理、调工具、拉数据——每一步都碰到敏感信息」。

Fortanix 首席产品官 Anuj Jaiswal 的说法点出了覆盖面的扩展：「我们看的是整条 AI 流水线的流程，包括护栏、Agent、专有模型。」——也就是说，TEE 保护的对象从「一段数据」扩展到了「一整套 Agent 工作流」。

### Apple：PCC 走出自家数据中心

Apple 的 Private Cloud Compute 在 2024 年发布时，只在自己的数据中心、只跑 Apple Silicon。Computerworld 说它「是这项技术的突破」——现在它走出了这个边界。

Apple 在 6 月 8 日的《Expanding Private Cloud Compute》里写：为了支持「agentic tool-use 和复杂推理」这类最 demanding 的任务，与 Google 和 NVIDIA 合作，把 PCC 扩展到 Google Cloud 上使用 NVIDIA GPU 的系统。实现层面的组合是：**NVIDIA Confidential Computing with NVIDIA GPUs + Intel CPU 的 TDX + Google 的 Titan 芯片**。

几个很 Apple 的细节（也是 TEE 工程化的教科书）：

- 核心要求不变：无状态计算、可强制保证、无特权运行时访问、不可定向攻击、可验证透明；
- 硬件供应链防护：维护一份**密码学可验证的仅追加账本**，记录 PCC 机队里的所有 Google Cloud 硬件；
- 对「被攻破就能外泄用户数据」的组件，软件证明根植于**至少两个来自独立厂商的信任根**；
- 网络数据解析放在独立命名空间的独立进程里；共享推理软件短 TTL 回收；证明过的密钥放在与外部输入隔离的独立机密 VM 里；
- 二进制全部公开供检查，提供研究工具，并通过 Security Bounty 让研究者访问 live PCC 节点。

Intel 那篇博客也确认：Apple PCC 在 Google Cloud 上用的正是 Intel TDX trust domains 跑在 Xeon 基础设施上。一家最讲究垂直整合的公司，为了 AI 算力打破了自己的硬件传统——这件事本身比任何市场报告都更能说明算力需求的量级。

## 四、成本是绕不开的现实

ServiceNow 是一个已经把机密计算和 AI Agent 用在内部的例子：用 Agent 回答销售人员的佣金查询、分析保密调查数据；员工 PII 留在保险箱里，Agent 流量不离开加密环境，每个 Agent 动作都经过密码学验证。首席数字信息官 Kellie Romack 的说法很务实：「一次泄露是不可接受的。我务实，也讲战术。」

但她也点出了那个老问题：**机密计算不便宜，跑在 GPU 上尤其贵**——GPU 本身就贵，TEE 再叠一层成本。这也是为什么本号 10 月 6 日那篇《机密计算落地看这四种模式》会说：能证明「环境可信」，不等于能证明「它不会乱来」。TEE 守住的是机密性和完整性，不保证 Agent 的行为正确、不保证提示注入不会诱导它做坏事——那是策略、护栏和审计的事。

如果你想更深入地看 TEE 本身的软肋，本号 10 月 19 日写过那篇《TEE 的漏洞清单已经长得能写进一篇博客》：TEE.fail、WireTap、BadRAM、DDRop 这些攻击说明「打断一台等于打断全部」的顾虑并非杞人忧天。把 Agent 放进 TEE，不等于把风险归零。

## 五、怎么读这轮「重新升温」

把时间线放在一起看：

- **2024**：Apple 发布 PCC，把机密计算带进公众视野；
- **2025–2026 上半年**：Canonical/Red Hat/VMware 等软件栈铺开、云厂商陆续上线 TDX 服务（本号 10 月 12 日写过 SGX 让位 TDX 的决策）；
- **2026 下半年**：Fortanix 把 TEE 做进 Kubernetes 容器，Apple 把 PCC 扩到 Google Cloud，**Agent 安全事故密集出现**——Computerworld 这篇分析就是在说：是最后这件事，把前两件的技术成熟度转化成了采购动力。

所以「AI Agent 重新点燃机密计算」这个标题，方向是对的，但要补两句限定：

1. **TEE 不是 Agent 安全的全部**。它解决「谁可以看到数据和模型」，不解决「Agent 该不该做这个动作」。别忘了 Gogia 那句话的另一半：失控的权限才是事故报告。
2. **采用的主要障碍从「信不信」变成了「值不值」**。硬件有了、软件栈有了、云上也开了，剩下的是成本与复杂度——用 Gogia 的话说，保护最敏感负载会让排障变难，这笔账每家都要自己算。

真正的趋势判断是：**当 Agent 开始替人动手，数据使用时的保护就从「合规加分项」变成了「上线前置条件」**。这也是为什么一家做语音的公司、一家做 IT 服务的公司、和一家最重视隐私的手机厂商，会在同一个季度里往同一个方向加注。

## 参考资料

- Computerworld 原文（Agam Shah，2026-11-23）：https://www.computerworld.com/article/4245310/ai-agent-security-concerns-kick-start-confidential-computing.html
- Intel Newsroom《Confidential Computing - Growing Momentum, Sharpened Focus》（Mike Ferron-Jones，2026-10-09）：https://www.intel.com/content/www/us/en/newsroom/opinion/confidential-computing-growing-momentum-sharpened-focus.html
- Fortanix 新闻稿《Confidential AI ... on CNCF Confidential Containers (CoCo)》（2026-10-18）：https://www.fortanix.com/company/pr/2026/10/fortanix-announces-confidential-ai-for-enterprise-grade-kubernetes-workloads-on-cncf-confidential-containers-coco
- Apple Security Research《Expanding Private Cloud Compute》（2026-06-08）：https://security.apple.com/blog/expanding-pcc
- 本号前序：《Intel 让 SGX 在 Diamond Rapids 之后退场》《机密计算落地看这四种模式》《TEE 的漏洞清单已经长得能写进一篇博客》
