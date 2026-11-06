---
title: "白宫网络成了 28 家住宅代理的出口，但最该读的是那句「我们没有通知任何人」"
date: 2026-11-05
slug: white-house-network-residential-proxy-exit
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Layer3 Intel《Residential Proxies Detected on White House Network》（2026-11-04）与 Residential Proxy Observatory / AS2650 上下文页、ARIN RDAP（autnum/AS2650 与 ip/165.119.253.253、ip/204.68.207.1 的注册记录）、RuntimeWire 独家专访（Layer3 创始人 Sergiy Usatyuk，2026-11-04/05）、Synthient《A Broken System Fueling Botnets》（Kimwolf 报告）"
original_date: 2026-11-04
original_url: "https://layer3intel.com/blog/residential-proxies-white-house-network"
description: "本文解读 Layer3 Intel 于 2026 年 11 月 4 日发布的《Residential Proxies Detected on White House Network》，并补上公告本身没说的两件关键事。事实层：2026-10-05 至 11-03 期间，Layer3 的住宅代理枚举管道有 236 次从白宫网络出口，来自 6 个地址、30 天中的 26 天，且有 28 家不同的住宅代理服务能从中转出。我用 ARIN RDAP 独立核对了归属：AS2650（EOP-ASN）注册实体为 Executive Office Of The President，其下的 165.119.0.0/16（EOP-B）与 204.68.207.0/24（EOP-C）均为 DIRECT ALLOCATION，而非运营商转售，五个前缀全部可核实。而官方 IP Intel 页面自己写着「None of it is anonymizer space」——即这些前缀本身不是代理出口段，它们只是「代理流量从这里出去」的那个网络的地址段。这是整件事里最容易被误读、也最需要说清的一层。而第二件更关键：RuntimeWire 的独家专访披露，Layer3 创始人 Sergiy Usatyuk 明确表示公司不会公开那 6 个具体地址、也没有就此通知任何人。而 Layer3 自己的措辞极其克制：「Our data shows the exits, not the device or the person behind them.」本文逐层拆解了这个案子的证据边界：哪些是已确证的（出口、地址、网络归属、时间分布）、哪些是推断的（「有人晚上常驻 + 设备装了代理 SDK」）、哪些完全没有证据（设备被入侵 vs 用户主动安装、攻击者是否进入内网、归因到具体人）。并给出调查者真正需要的日志清单。"
published: true
---

> 原文：Layer3 Intel《Residential Proxies Detected on White House Network》（2026-11-04）
> 原文链接：<https://layer3intel.com/blog/residential-proxies-white-house-network>
>
> 本文依据 Layer3 官方博客与其 Observatory 上下文页、我用 ARIN RDAP 独立核对的注册记录、RuntimeWire 的独家专访，以及 Synthient 的 Kimwolf 原始报告。

## 一、先说结论：三层，一层比一层弱

这条新闻最需要小心的，是它的证据强度在三层之间是断崖式下降的。而大多数转述都只讲了第一层。

| 层 | 内容 | 证据强度 |
|---|---|---|
| 第 1 层：已确证 | 236 次住宅代理出口从白宫网络出，涉及 6 个地址、28 家代理服务 | 有第三方（Spur、Synthient）独立交叉验证 |
| 第 2 层：合理推断 | 「有人晚上常驻、设备上装了代理 SDK」 | 官方明确标注为「suggests」，时间分布只是佐证而非证据 |
| 第 3 层：无证据 | 「设备被入侵」「攻击者进入了内网」「是某个具体的人」 | 官方原文明确说没有；而社区里流传的截图版本比这强得多 |

我这一篇要做的第一件事，就是把这三层分开。

## 二、第 1 层：已确证的部分

### 观测数据

Layer3 官方博客的原文数据：

> "Our residential proxy enumeration pipeline exited through the White House network **236 separate times**."
> "Those exits came from **6 addresses**, on **26 of the 30 days**."
> "**28 separate residential proxy services** were able to exit through this network."
>
> 时间窗口：2026-10-05 至 2026-11-03

我要强调「28 家」这个数字的含义。

这不是一家代理商的系统被渗透，而是 28 家互不相干的商业服务，都能让流量从白宫网络出。

换句话说：只要白宫网络里有 6 台（或 6 个 NAT 后面的）设备装了代理 SDK，那么全世界几乎所有主流住宅代理服务商，都能从白宫网络里取到出口。

而这不是理论可能——因为住宅代理服务的商业模式，本来就是「从大量真实设备里征集出口」。

### 归属：我用 ARIN RDAP 独立核对了

这一节我做了原报道没有做的事——去注册库里逐条核对，而不是引用二手转述。

AS2650 的 ARIN RDAP 记录：

```
handle: AS2650 | name: EOP-ASN
registrant: Executive Office Of The President
technical:  EOP Tech     (org: Executive Office of the President)
abuse:      EOP Security (org: Executive Office of the President)
```

Layer3 列出的 5 个前缀，我逐个查了 RDAP：

| 前缀 | RDAP name | 类型 | 注册实体 |
|---|---|---|---|
| `165.119.0.0/16` | EOP-B | DIRECT ALLOCATION | Executive Office Of The President |
| `165.119.250.0/24` | （同 /16） | — | — |
| `165.119.252.0/24` | （同 /16） | — | — |
| `165.119.253.0/24` | （同 /16） | — | — |
| `204.68.207.0/24` | EOP-C | DIRECT ALLOCATION | Executive Office Of The President |

作为对照，我查了一个普通 IP（1.1.1.1）：

```
name: APNIC-LABS | type: ASSIGNED PORTABLE | handle: 1.1.1.0 - 1.1.1.255
```

请注意这组对比：白宫的两个前缀是 DIRECT ALLOCATION（直接分配），而 1.1.1.1 是 ASSIGNED PORTABLE（可携带指派）。前者是「这个段直接属于该机构」，而后者的段会从一个更大的块里临时切出来。

所以「白宫网络」这个说法，在注册层面是站得住的。

### Layer3 自己写的那句话，是整件事最容易被误读的地方

官方博客里有一句很短的话，但它其实给出了最重要的限定：

> "**This is public access. Anybody can obtain it by signing up to a public residential proxy service, paying a few dollars and sending requests through it. We did not selectively target this network or try to make our probes exit from it. We caught this by chance, simply by requesting global rotating access through these services.**"

而更关键的一句，藏在他们自己的 IP Intel 上下文页上：

> "AS2650 — Executive Office Of The President — Announces **65,792** addresses in 5 prefixes. **None of it is anonymizer space.**"
>
> "Residential-proxy exposure: **Providers — 28 — selling exits here**"

请注意最后那句：「None of it is anonymizer space」。

这句话的意思是：AS2650 的这 65,792 个地址本身，不是「代理出口段」（也就是说，不是那种专门被租来当代理出口的 IP 池）。

而它是「代理流量的出口恰好从这里出去」的那个网络。

这个区分极重要，因为如果不做这个区分，很容易读成「白宫有一个 65,792 个 IP 的代理网络」——而事实是：白宫网络的某个（些）设备被当成了代理出口，而 AS2650 只是一台「恰好被选中的路由器」的地址段。

打个比方：这就像「某栋楼的门牌号出现在了快递单上」，而不是「这栋楼是一家快递公司」。

## 三、第 2 层：时间分布——是最好的线索，也是最弱的证据

官方博客说：

> "Most of the activity happens in the evening, Eastern time: **about half of it falls between 5 p.m. and midnight, and almost none happens in the early morning.** That pattern **suggests** a person rather than a public guest Wi-Fi network: **someone regularly on the White House network late into the evening, whose device is infected with a proxy SDK.**"

而这里我必须做一件 Layer3 自己在博客里没做的事——给这个推断称重。

**支持「是人」的部分很清楚：**

| 观察 | 指向 |
|---|---|
| 约一半在 17:00–24:00 | 符合人的作息 |
| 清晨几乎没有 | 不符合公共访客 Wi-Fi（那类热点通常是全天有人用） |
| 30 天里有 26 天出现 | 符合「每天同一台设备在用」，而不符合「随机撞上」 |

**但它证明不了什么，关键在于三点：**

**① 时间分布可以由任何「有作息的东西」产生。**

家庭宽带、固定工位、服务器集群的定时任务、IoT 设备的回传窗口——都可能呈现类似的曲线。要区分「某个人晚上在用」和「某个自动化系统在跑」，需要的是设备侧的日志，不是出站流量的时间直方图。

**② 观测管道的采样周期本身有节奏。**

Layer3 说它是「请求全球轮换出口」时被撞见的。这意味着「哪一天有没有命中」并不完全独立于他们的探测调度。26/30 这个数字里，有多少是网络的性质，有多少是管道的性质，从公布的数字上分不开。

**③ Layer3 自己用了「suggests」，而我在核对时发现社区转述普遍把 suggest 升级成了 assert。**

原始那篇 X 帖（Reddit 安全负责人 Matt Johansen 发布）说的是「有人在白宫被入侵了设备，或者设备在给僵尸网络提供住宅代理访问」。Johansen 后来自己也软化了措辞，改成「提供住宅代理访问的设备」。而 Layer3 的措辞更窄：住宅代理出口活动，外加「有代理 SDK 存在」这个推断。

三个版本，一个比一个强，但没有一个是官方版本。

**这一层的结论是：时间分布让「设备被征用」成为一个合理假设，但它不能排除「用户自己装了个来路不明的 App」。** 而这两种情况的处置方式完全不同：前者是事件响应，后者是终端合规问题。

## 四、第 3 层：完全没有证据的三件事

### 4.1 「设备被入侵」

Layer3 的报告里**没有**说设备是被入侵的。他们说的是「residential proxy exit activity」。

住宅代理软件进入设备的路径至少有三条：

1. 用户主动安装了一个披露不清的应用或 SDK；
2. 用户主动安装了伪装成 VPN / 加速器 / 清理工具的代理客户端；
3. 设备被真正入侵（弱口令、暴露的 ADB、未修补的漏洞等）。

第 1、2 条属于合规与产品设计问题，第 3 条才属于安全事件。**从出站流量模式里，你分不出这三条。**

### 4.2 「攻击者进入了内网」

Layer3 的原文明确说了：报告里没有任何证据显示代理客户触及了白宫的内网系统、扫描了内网地址，或发生了横向移动。

已观测到的事实是：**通过该网络地址段发生的出站出口活动。**

Synthient 的 Kimwolf 报告确实说明了「防护不当的代理 SDK 可能导致内网可达与横向移动」这一风险路径——Kimwolf 高置信度评估其感染设备超过 200 万台，主要是运行着暴露的 ADB 服务的 Android 设备。但 Layer3 用的是条件句：如果这个网络上的某个 SDK 有同类缺陷，那么买代理访问权的人就能用它去够内网系统。

**前提句不能被读成结论句。** 这是这类报道里最常见的滑坡。

### 4.3 「是某个人 / 某台设备」

一个自治系统号（AS）识别的是宣布这些公网地址的网络。它本身并不指名 NAT 后面那台手机、笔记本、电视盒子还是路由器。

6 个公网地址在一个月里可以代表很多台设备；而一个活跃的代理出口，就足以让外部流量看起来来自白宫网络。

## 五、真正更值得警惕的一件事：没有通知任何人

这是我在核对过程中发现的、官方博客里没有、但后续报道里最重要的一条。

RuntimeWire 在 2026-11-04/05 拿到了 Layer3 创始人 Sergiy Usatyuk 的独家专访，其中他明确表示：

- 公司**不会公开**那 6 个具体地址，理由是发现的敏感性；
- 公司**没有就此通知任何人**。

Layer3 创始人的原话被 RuntimeWire 概括为：这个发现涉及出口地址，但**不涉及设备，也不涉及人**；找出是哪台设备、代理软件是怎么上去的，责任落在网络运营方身上。

这件事的技术意义小于它的**处置意义**，但处置意义很大：

一份完整的「某敏感网络上有 6 个地址在给 28 家商业代理服务当出口」的报告，如果既不通知被影响的运营方、又不公开地址，那么：

- 被影响方**无法自查**（他们不知道该去查哪 6 个地址、什么时间窗、什么协议）；
- 社区**无法复核**（第三方拿不到地址，无从验证 236 次这个数字）；
- 而这个出口在 Layer3 发布之后，**并不会自动消失**——只要设备上的代理 SDK 还在跑，流量就会继续。

换句话说，**这是一个被公开描述、但未被公开处置的暴露面**。而这类暴露面的存续时间，取决于设备什么时候被重装、代理 SDK 什么时候被卸载、网络方什么时候偶然做了一次出站流量审计。

我认为这才是这条新闻真正的落点：**问题不在于「白宫网络被黑」，而在于「一个已经被人看见的暴露面，被看见之后依然没人去处理」。**

## 六、防护建议：给企业与政府网络运营者

按「先能查、再能挡」的顺序排列。

### 6.1 先解决「能不能看见」

排查住宅代理出口，核心是看**出站**流量，而不是入站：

- 在出口路由器或边界防火墙上，按**目标端口**（常见 1080、3128、8080、9050、8888 等 SOCKS/HTTP 代理端口）与**非常规目的地地址**做统计；
- 关注**大量小包、长连接、目的地高度分散**的出站会话——这是代理转发的典型特征，与正常浏览（目的地集中、连接稀疏）差别明显；
- 做**长期基线**。住宅代理的出口是离散的、时有时无的，单日快照很容易漏掉；
- 把 `AS2650` 这类「政府与大型机构自有 ASN」纳入出站异常的观察名单。它们的公网地址**不应该**出现在代理服务商的可选出口列表里。

### 6.2 再解决「从哪进来」

- 清点终端上的 VPN / 代理类软件清单，尤其是 Android 设备上通过侧载安装的应用；
- 检查暴露的调试接口：ADB（5555/tcp）、以及各类「手机远程控制」类工具的默认开放；
- 审查应用 SDK 的第三方清单：不少免费应用（尤其是免费 VPN、清理类、浏览器类）会内置住宅代理 SDK。

### 6.3 关于「用户主动安装」这条路

如果结论是用户自己装了个来路不明的 App，那这不是一次入侵事件，而是一次**内部 IT 与采购流程的失败**。可行的做法：

- 在终端管理（MDM）里把未授权的 VPN/代理类应用列入黑名单；
- 对员工设备明确说明公司对「个人 VPN 客户端」的政策，因为员工完全可能出于「访问境外服务」的正当诉求去装它——而这类应用恰恰是住宅代理 SDK 的主要来源；
- 定期做一次出站流量审计作为兜底，而不是等第三方来报告。

## 七、结论与事实边界

三条已确证：

1. 2026-10-05 至 11-03，Layer3 的枚举管道有 236 次从白宫网络出口，涉及 6 个地址、30 天中的 26 天、28 家住宅代理服务。
2. 这些出口地址属于 AS2650，注册实体是 Executive Office Of The President；`165.119.0.0/16` 与 `204.68.207.0/24` 均为该实体的直接分配。
3. 这些地址被 Spur、Synthient 等第三方独立识别为住宅代理出口。

一条合理推断：

4. 时间集中在美东时间 17:00–24:00，指向一台长期在网、有人作息的设备上存在代理 SDK。

明确没有证据：

5. 设备是被入侵的；
6. 攻击者进入或扫描了白宫内网；
7. 可以归因到任何具体的人或设备。

一条被忽略的处置事实：

8. Layer3 创始人称，公司不会公开具体地址，也**未通知任何人**。这个暴露面在被公开之后，依然处于未处置状态。

---

### Sources

- Layer3 Intel, *Residential Proxies Detected on White House Network* (2026-11-04): <https://layer3intel.com/blog/residential-proxies-white-house-network>
- Layer3 Intel, AS2650 context page: <https://layer3intel.com/context/AS2650>
- Layer3 Intel, *What is a residential proxy*: <https://layer3intel.com/what-is-a-residential-proxy>
- RuntimeWire, *EXCLUSIVE: Layer3 has not told the White House about 236 proxy exits from its network, founder says* (2026-11-04, updated 2026-11-05): <https://runtimewire.com/article/residential-proxy-traffic-white-house-network-236-exits>
- ARIN RDAP, AS2650: <https://rdap.arin.net/registry/autnum/AS2650>
- ARIN RDAP, `165.119.253.253`: <https://rdap.arin.net/registry/ip/165.119.253.253>
- ARIN RDAP, `204.68.207.1`: <https://rdap.arin.net/registry/ip/204.68.207.1>
- ARIN RDAP, `1.1.1.1` (对照): <https://rdap.arin.net/registry/ip/1.1.1.1>
- Synthient, *A Broken System Fueling Botnets* (Kimwolf): <https://synthient.io/blog/a-broken-system-fueling-botnets>

### 事实边界说明

- 236 次出口、6 个地址、26/30 天、28 家服务：引自 Layer3 官方博客原文。
- AS2650 及两个前缀的归属：本文用 ARIN RDAP 独立核对，与 Layer3 的表述一致。
- 「没有通知任何人」「不会公开地址」：引自 RuntimeWire 对 Layer3 创始人 Sergiy Usatyuk 的独家专访，属第三方媒体的一手引述，非 Layer3 官方博客内容。
- 「设备被入侵」「内网被触及」：公开材料中**没有**任何证据支持，本文亦未做此推断。
- Kimwolf 的 200 万台规模引自 Synthient 原文，用于说明该风险路径在别处已有先例，**不可**类推到本案。
