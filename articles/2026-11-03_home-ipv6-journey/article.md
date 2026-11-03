---
title: "我的全屋无污染 IPv6 之旅：把 RA、RDNSS、RIO、FakeIP 逐个拆开"
date: 2026-11-03
slug: home-ipv6-journey
tags: [IPv6, RA, Router Advertisement, RS, Router Solicitation, ND, NDP, 邻居发现, SLAAC, DAD, PIO, RDNSS, RIO, SLLAO, DNSSL, ULA, GUA, 链路本地地址, DAD, RFC4861, RFC8106, RFC4191, RFC4193, RFC6724, RFC4862, RFC8201, DNS64, NAT64, CLAT, PLAT, 464XLAT, RFC6877, FakeIP, TPROXY, 透明代理, 前缀漂移, prefix rotation, 源地址选择, 地址寿命, valid_lft, preferred_lft, iOS, Android, IpClient, accept_ra, 光猫, ONT, 路由器广告, DNS 污染, DoT, DoH, PMTU, PTB, MSS, ICMPv6, 家庭网络, 网络工程, 术语表]
category: 技术/网络
author: FreeLAMP.com
description: "一次把家庭 IPv6 的三个顽症拆开：上游光猫在 RA 里硬广告自己当解析器、iPhone 单独拿不到地址、运营商换前缀后整晚断网。全文以术语为骨架 —— GUA/ULA/LLA 的区别、RS/RA/NS/NA 五种报文、PIO 的 L/A 两个比特、RDNSS 与 RIO 的用途与移动端天花板（accept_ra_rt_info_max_plen=64）、SLLAO 与 hop limit 255 为何是 iOS 的硬门槛、DNS64/NAT64 与 CLAT/PLAT 的分工、FakeIP 如何让纯 IPv6 客户端访问只有 A 记录的站点，以及 RFC 6724 源地址选择如何把流量送进旧前缀的黑洞。附完整缩写-全称-中文-RFC 对照表与十条复盘清单。"
published: true
---

> 一次把 DNS 污染、前缀漂移、iOS/Android 差异和 v4-only 站点可达性逐个拆开的实践记录。
> 文中所有地址、域名、主机名均已替换为示例值（`2001:db8::/32`、`203.0.113.0/24` 等文档专用段）。

---

## 一、起因：三件看起来不相干的事

1. **解析结果不可信**：家里设备明明配了干净的解析器，查某些域名却返回明显错误的结果。
2. **只有 iPhone 不行**：同一张 Wi-Fi 下，Android、Linux 全都正常拿到了 IPv6 地址，iPhone 一点都拿不到。
3. **整晚断网**：运营商换了 IPv6 前缀，之后所有远端链路全部失效，而本机 `ping` 网关却一切正常。

这三个问题的根因分别是：**上游光猫（ONT）在 RA 里硬广告自己当 DNS**、**iOS 对 RFC 4861 的校验比 Linux/Android 严格得多**、**旧前缀地址残留在网卡上导致源地址选择踩进黑洞**。

而解决问题的过程，本质上就是把 IPv6 的每一个缩写、每一条 RFC 弄清楚的过程。

---

## 二、术语总表

### 2.1 地址与文本格式

| 缩写 | 英文全称 | 中文 | 说明 |
|---|---|---|---|
| **IPv6** | Internet Protocol version 6 | 互联网协议第 6 版 | 128 位地址，[RFC 8200](https://www.rfc-editor.org/rfc/rfc8200) |
| **GUA** | Global Unicast Address | 全球单播地址 | `2000::/3` 范围，公网可路由，运营商下发的就是它 |
| **ULA** | Unique Local Address | 唯一本地地址 | `fc00::/7`，类比 IPv4 私网地址，但**不做 NAT**，只在站点内路由；[RFC 4193](https://www.rfc-editor.org/rfc/rfc4193) |
| **LLA** | Link-Local Address | 链路本地地址 | `fe80::/10`，只在同一二层链路内有效，**不出网关**；所有 IPv6 接口必备 |
| **Prefix** | Network Prefix | 网络前缀 | `/48`、`/64`、`/128` 表示前多少位是网络部分 |
| **Documentation Prefix** | Documentation Prefix | 文档专用前缀 | `2001:db8::/32`，[RFC 3849](https://www.rfc-editor.org/rfc/rfc3849)，写文档/示例时必须用它 |
| **NAT64 Prefix** | NAT64 Prefix | NAT64 前缀 | `64:ff9b::/96`，[RFC 6052](https://www.rfc-editor.org/rfc/rfc6052)，把 IPv4 地址嵌进 IPv6 |
| **`::`** | Zero Compression | 零压缩 | [RFC 4291](https://www.rfc-editor.org/rfc/rfc4291) §2.2：连续的全零组可用一对冒号代替，**全地址只能出现一次** |

> 关于地址缩写：`fd66:1::68` 实际是 `fd66:0001:0000:0000:0000:0000:0000:0068`。**省略前导零**和**压缩连续零组**是两条独立规则，混用时的唯一硬性约束是 `::` 不能出现两次。

### 2.2 发现与自动配置

| 缩写 | 英文全称 | 中文 | 说明 |
|---|---|---|---|
| **ND / NDP** | Neighbor Discovery Protocol | 邻居发现协议 | IPv6 的「ARP + 路由器发现 + 重定向」三合一，[RFC 4861](https://www.rfc-editor.org/rfc/rfc4861) |
| **RS** | Router Solicitation | 路由器请求 | ICMPv6 类型 **133**；主机刚接入网络时喊一声「有没有路由器」 |
| **RA** | Router Advertisement | 路由器通告 | ICMPv6 类型 **134**；路由器周期性（或应答 RS）广播「我在这、前缀是这个、网关用我、DNS 是它」 |
| **NS** | Neighbor Solicitation | 邻居请求 | 类型 **135**；「这个地址的 MAC 是谁？」（≈ IPv4 的 ARP 请求） |
| **NA** | Neighbor Advertisement | 邻居通告 | 类型 **136**；「是我，MAC 是这个」 |
| **Redirect** | Redirect | 重定向 | 类型 **137**；「下一跳别走我，走它更近」 |
| **SLAAC** | Stateless Address Autoconfiguration | 无状态地址自动配置 | [RFC 4862](https://www.rfc-editor.org/rfc/rfc4862)；主机自己用「前缀 + 接口标识」拼出地址，**不需要 DHCP 服务器** |
| **DAD** | Duplicate Address Detection | 重复地址检测 | SLAAC 配好地址后先发 NS 问「有人在用吗」，没人应答才正式启用 |
| **DHCPv6** | Dynamic Host Configuration Protocol for IPv6 | IPv6 动态主机配置协议 | [RFC 8415](https://www.rfc-editor.org/rfc/rfc8415)；**Android 不支持用它分配地址**（只认 SLAAC） |
| **M / O flag** | Managed / Other Configuration flag | 管理 / 其他配置标志 | RA 头里的两个比特：M=1 表示「地址去问 DHCPv6」，O=1 表示「其他参数去问 DHCPv6」 |

### 2.3 RA 里的选项（本文的核心战场）

| 缩写 | 英文全称 | 中文 | 类型 | RFC |
|---|---|---|---|---|
| **PIO** | Prefix Information Option | 前缀信息选项 | 3 | [RFC 4861](https://www.rfc-editor.org/rfc/rfc4861) |
| **SLLAO** | Source Link-Layer Address Option | 源链路层地址选项 | 1 | RFC 4861 |
| **MTU** | Maximum Transmission Unit Option | 最大传输单元选项 | 5 | RFC 4861 |
| **RIO** | Route Information Option | 路由信息选项 | 24 | [RFC 4191](https://www.rfc-editor.org/rfc/rfc4191) |
| **RDNSS** | Recursive DNS Server Option | 递归 DNS 服务器选项 | 25 | [RFC 8106](https://www.rfc-editor.org/rfc/rfc8106) |
| **DNSSL** | DNS Search List Option | DNS 搜索列表选项 | 31 | RFC 8106 |

**PIO 里的两个比特（最容易搞混）：**

- **L flag**（On-Link）：这个前缀是「本地直连」的 → 主机装一条 on-link 路由
- **A flag**（Autonomous）：允许主机用这个前缀做 **SLAAC** 生成地址
- `L=1, A=0` → 只建路由不发地址；`L=1, A=1` → 建路由 + 自动配地址

**路由器偏好与寿命：**

| 字段 | 英文 | 中文 | 作用 |
|---|---|---|---|
| **Prf** | Default Router Preference | 默认路由器偏好 | RFC 4191；High(01) / Medium(00) / Low(11)。**多路由器共存时靠它决定谁是首选** |
| **Router Lifetime** | Router Lifetime | 路由器寿命 | RFC 4861；0 表示「别把我当默认网关」，非 0 才是候选网关 |
| **valid_lft / preferred_lft** | Valid / Preferred Lifetime | 有效 / 首选寿命 | 地址还剩多久可用 / 还能不能用于**新建**连接（`preferred_lft=0` 即 deprecated，不应用于新连接） |

### 2.4 地址选择与路径

| 缩写 | 英文全称 | 中文 | 说明 |
|---|---|---|---|
| **RFC 6724** | Default Address Selection for IPv6 | IPv6 默认地址选择 | 决定「发往某个目的地时用哪个源地址」；**前缀漂移事故就是它挑错了源** |
| **PMTU** | Path Maximum Transmission Unit | 路径最大传输单元 | [RFC 8201](https://www.rfc-editor.org/rfc/rfc8201) |
| **PTB** | Packet Too Big | 数据包过大 | ICMPv6 类型 **2**；路径上某跳 MTU 变小就回它，让发送方缩小或分片 |
| **MSS** | Maximum Segment Size | 最大报文段长度 | TCP 层协商，夹在 TCP 头里；**MSS clamping**（钳制）是常见的兜底手段 |
| **ICMPv6** | Internet Control Message Protocol for IPv6 | IPv6 互联网控制消息协议 | RA / RS / NS / NA / PTB 全都是它 |

### 2.5 转换与代理

| 缩写 | 英文全称 | 中文 | 说明 |
|---|---|---|---|
| **DNS64** | DNS Extension for NAT64 | NAT64 的 DNS 扩展 | [RFC 6147](https://www.rfc-editor.org/rfc/rfc6147)；域名只有 A 记录时，合成一条 `64:ff9b::<v4>` 的 AAAA |
| **NAT64** | Network Address and Protocol Translation from IPv6 to IPv4 | IPv6→IPv4 网络地址与协议转换 | [RFC 6146](https://www.rfc-editor.org/rfc/rfc6146)；把发往合成地址的连接翻译成真实 IPv4 连接 |
| **CLAT** | Customer-side Translator | 客户端侧转换器 | [RFC 6877](https://www.rfc-editor.org/rfc/rfc6877)；终端内部的 v6→v4 转换器，让「只认 IPv4 的应用」在纯 v6 网络上照常工作 |
| **PLAT** | Provider-side Translator | 运营商侧转换器 | RFC 6877；464XLAT 里**服务端那一半**，通常就是一个 NAT64 —— CLAT 把应用发出的 IPv4 报文改写成 `64:ff9b::/96` 的 IPv6，PLAT 在运营商侧再翻译回真实 IPv4 发往互联网。**CLAT 在终端、PLAT 在网络**，两者合起来才叫 464XLAT |
| **464XLAT** | 464 XLAT | 464 转换架构 | RFC 6877；CLAT + PLAT 组合，运营商纯 v6 接入网的标准做法 |
| **FakeIP** | Fake IP Address | 伪 IP 地址 | **非 RFC**，是代理软件的一种技术（见第六节） |
| **DoT** | DNS over TLS | 基于 TLS 的 DNS | [RFC 7858](https://www.rfc-editor.org/rfc/rfc7858)，端口 853 |
| **DoH** | DNS over HTTPS | 基于 HTTPS 的 DNS | [RFC 8484](https://www.rfc-editor.org/rfc/rfc8484) |
| **TPROXY** | Transparent Proxy | 透明代理 | Linux netfilter 特性；用 `IP_TRANSPARENT` 套接字 + `fwmark` 策略路由，**不改客户端配置**就把流量导入用户态进程 |

---

## 三、RFC 速查表

| RFC | 标题 | 本文用到的部分 |
|---|---|---|
| [8200](https://www.rfc-editor.org/rfc/rfc8200) | Internet Protocol, Version 6 (IPv6) Specification | 报文结构、Next Header、hop limit |
| [4291](https://www.rfc-editor.org/rfc/rfc4291) | IP Version 6 Addressing Architecture | 地址文本表示、`::` 零压缩 |
| [4193](https://www.rfc-editor.org/rfc/rfc4193) | Unique Local IPv6 Unicast Addresses | ULA（`fc00::/7`）定义 |
| [3849](https://www.rfc-editor.org/rfc/rfc3849) | IPv6 Address Prefix Reserved for Documentation | `2001:db8::/32` |
| [4861](https://www.rfc-editor.org/rfc/rfc4861) | Neighbor Discovery for IP version 6 | RS/RA/NS/NA、PIO、SLLAO、hop limit=255、Router Lifetime |
| [4862](https://www.rfc-editor.org/rfc/rfc4862) | IPv6 Stateless Address Autoconfiguration | SLAAC、DAD、valid/preferred lifetime |
| [4191](https://www.rfc-editor.org/rfc/rfc4191) | Default Router Preferences and More-Specific Routes | Router Preference、**RIO** |
| [8106](https://www.rfc-editor.org/rfc/rfc8106) | IPv6 Router Advertisement Options for DNS Configuration | **RDNSS**、DNSSL、**寿命为 0 表示删除** |
| [6724](https://www.rfc-editor.org/rfc/rfc6724) | Default Address Selection for IPv6 | 源地址选择规则 |
| [8201](https://www.rfc-editor.org/rfc/rfc8201) | Path MTU Discovery for IP version 6 | PMTU、PTB |
| [8415](https://www.rfc-editor.org/rfc/rfc8415) | Dynamic Host Configuration Protocol for IPv6 | DHCPv6、M/O flag |
| [6052](https://www.rfc-editor.org/rfc/rfc6052) | IPv6 Addressing of IPv4/IPv6 Translators | NAT64 前缀 `64:ff9b::/96` |
| [6146](https://www.rfc-editor.org/rfc/rfc6146) / [6147](https://www.rfc-editor.org/rfc/rfc6147) | NAT64 / DNS64 | 地址与协议翻译、AAAA 合成 |
| [6877](https://www.rfc-editor.org/rfc/rfc6877) | 464XLAT | **CLAT + PLAT** |
| [7858](https://www.rfc-editor.org/rfc/rfc7858) / [8484](https://www.rfc-editor.org/rfc/rfc8484) | DoT / DoH | 加密解析 |

---

## 四、我们的架构（脱敏）

```
终端 ──IPv6──> 旁路网关（Linux 小主机）──┬─ 国内 v6 ──> 直连
                                        └─ 境外 v6 ──隧道(IPv6)──> 远端出口 ──> 目标
```

关键设计决策四条：

1. **旁路网关同时是「首选 v6 路由器」**：RA 里 `Router Lifetime=9000`、`Prf=HIGH`，压过光猫（默认 Medium），于是终端的 v6 默认路由指向网关。
2. **ULA 做稳定解析器地址**：光猫只肯下发 `/64`（无法再委派子网），运营商前缀又会变；`fd66:1::/64` 这个 ULA 是永久不变的，把解析器绑在 `fd66:1::68` 上，终端拿到的 DNS 地址就永远有效。
3. **隧道传输走 IPv6**：到远端出口的 TCP RTT 从 ~207ms 降到 **14ms**（同城 v4 到该机房绕路严重）。
4. **所有「压制」都只用标准选项**，不搞私有协议。

---

## 五、压制光猫的广告：三种手法，两种失败

光猫在 RA 里除了 PIO，还会硬广告 **RDNSS = 它自己**。问题在于：光猫的 v6 地址和终端**同处一个 /64**，属于 **on-link**（本地直连），终端的查询直接发给光猫，**根本不经过网关**，所以网关上的任何拦截规则都看不见它。

我们试了三层手段：

### 手法一：RDNSS lifetime = 0（最终主力，成功）

RFC 8106 规定 RDNSS 选项带一个寿命字段，**寿命为 0 表示「立即从解析器列表里删除这个地址」**。

于是我们的 RA 里同时携带两条 RDNSS：

```
RDNSS fd66:1::68            lifetime=9000   ← 保留我们的
RDNSS 2409:xxxx:xxxx::1     lifetime=0      ← 让终端删掉光猫的
```

**但它是场拉锯战**：光猫每 ~30 秒重广告一次（lifetime=300），会把它加回来。所以必须**事件驱动**——收到光猫的 RA 就立刻回一条压制包（限速 2 秒内只回一次），把「污染解析器可用」的窗口压到接近 0。周期 RA 也从 20 秒缩短到 **6 秒**作为兜底。

实测：Android 的解析器列表从 `[光猫, 我们v6, 我们v4]` 稳定收敛到 `[我们v6, 我们v4]`。

### 手法二：/128 RIO（失败，但值得记录）

RIO 是 RFC 4191 定义的「路由信息选项」，可以告诉终端「某个前缀走我」。思路是：给光猫的 DNS 地址发一条 **`/128` 更具体路由**，用**最长前缀匹配**压过 on-link 的 `/64`，把查询骗进网关。

Linux 上确实生效了（`ip -6 route` 里能看到那条 /128，查询也变干净了）。但手机上完全没用，原因在 Linux 内核的两个 sysctl：

```
accept_ra_rt_info_min_plen = 48    ← RIO 前缀长度下限
accept_ra_rt_info_max_plen = 64    ← RIO 前缀长度上限
```

**`/128 > 64`，直接被忽略。** Android 和 iOS 都卡在这一条。

> 这条经验后来写进了脚本的开关里（默认关闭），因为它在移动端没有价值，反而会在 Linux 上带来副作用（访问路由器自身的 v6 管理地址会被绕道）。

### 手法三：从源头让光猫的答案变干净（收尾）

真正的根治不是「删掉它」，而是**让它答得对**——把光猫自己的上游 DNS 指向我们的解析器（管理页里「上网 / WAN 的 DNS」设置，注意**不是** LAN/DHCP 那一栏）。这样即使终端仍保留光猫那个地址，拿到的也是干净结果。

三条合起来：**源头干净 + 列表清理 + 事件驱动压制**，才彻底稳定。

---

## 六、iOS 与 Android 的差异：为什么「只有 iPhone 不行」

这是整件事里最有意思的一段。我们的 RA 早期版本在 Linux 和 Android 上一切正常，iPhone 却**完全忽略**——不是「用了旧值」，是**整条 RA 被丢弃**。

原因有两个，都是 RFC 4861 的强制要求：

### 差异一：组播 RA 必须携带 SLLAO

RFC 4861 §4.2：**组播 RA 必须包含源链路层地址选项（SLLAO，type 1）**。

缺了它，Linux 宽容放过，**iOS 直接丢掉整条 RA**。补上 8 个字节后，iPhone 立刻拿到了地址。

### 差异二：RA 的 hop limit 必须是 255

RFC 4861 §6.1.2 / §7.1.1：RA 的 hop limit **必须**是 255（这是防重定向攻击的校验）。

原始实现只设了 `IPV6_UNICAST_HOPS=255`，而**组播**走的是另一个套接字选项 `IPV6_MULTICAST_HOPS`，默认值 **1**。所以单播 RA 合规、组播 RA 全被 iOS 丢弃。

```python
tx.setsockopt(IPPROTO_IPV6, IPV6_UNICAST_HOPS, 255)
tx.setsockopt(IPPROTO_IPV6, IPV6_MULTICAST_HOPS, 255)   # ← 这行是关键
```

### 差异三：Android 的 RA 由用户态处理

Android 的内核里 `accept_ra = 0`，乍看像「禁用 RA」，其实 RA 由用户态组件 **IpClient** 处理后再通过 netlink 下发。这带来两个坑：

- **假死状态**：IPv6 明明配不出来，但 `/proc/net/snmp6` 里的 `Icmp6InRouterAdvertisements` 计数在涨（说明包到了）。这种「包到了但没生效」的情况下，重连 Wi-Fi（`svc wifi disable/enable`）通常立刻恢复 —— 服务端配置是对的，不用改。
- **固定 MAC 的副作用**：iPhone 的「私有 Wi-Fi 地址」设为**固定**时，它不常重连、也就很少发 RS；一旦它在网关邻居表里的条目过期，**单播 RA 就发不出去了**。所以「收到 RS 立刻回一条 RA」（而不是等周期）对 iOS 特别重要 —— RFC 4861 本来就要求及时响应。

### 差异四：对 RDNSS lifetime=0 的配合度

| 行为 | Android | iOS |
|---|---|---|
| 接受 ULA 前缀做 SLAAC | ✅ | ✅ |
| 忽略组播 RA（缺 SLLAO / hop≠255） | ❌ 不受影响 | ✅ 会忽略 |
| 遵守 RDNSS lifetime=0 删除解析器 | ✅ 很快 | ✅ 遵守，但时序更敏感 |
| 支持 DHCPv6 分配地址 | ❌ 不支持 | ❌ 不支持 |
| 需要 RS 及时应答 | 一般 | **很需要** |

---

## 七、FakeIP 与纯 IPv6：v4-only 站点是怎么「可达」的

### 7.1 先问一个问题：纯 v6 客户端能访问只有 A 记录的网站吗？

**按协议本身：不能。** 没有 AAAA，客户端就无从建立 v6 连接。

这正是 **DNS64 + NAT64** 存在的理由：

```
DNS64：域名只有 A → 合成 AAAA = 64:ff9b::<那个v4地址>
NAT64：客户端连 64:ff9b::203.0.113.10  → 翻译器发出真实的 v4 连接
```

在运营商的 464XLAT 方案里，这套职责被拆成两端：**终端里的 CLAT** 负责把应用发出的 IPv4 报文改写成 v6，**网络侧的 PLAT** 负责翻译回真实 IPv4。

### 7.2 我们用了一个等价但更轻的方案：FakeIP

**FakeIP**（伪 IP，不是 RFC 概念）是代理软件里的一种技术：解析器对所有域名都返回一个**保留段里的占位地址**，并把它与域名的映射记下来。

```
客户端问 A/AAAA →
   DNS 返回占位地址（v4 用 198.18.0.0/15，v6 用自定义 /48）
客户端连这个占位地址 →
   网关查表还原出域名 →
   按域名重新解析（拿到真实 A 或 AAAA）→ 用合适的地址族连出去
```

**和 DNS64/NAT64 的本质区别：**

| | DNS64 + NAT64（含 CLAT/PLAT） | FakeIP |
|---|---|---|
| 是否改写地址 | 需要（嵌入 v4 到 `64:ff9b::/96`） | 不需要，网关直接按域名建连 |
| 需要专门转换器 | 需要（CLAT 在终端、PLAT 在网络） | **不需要**，代理进程本身就能做 |
| 对客户端透明 | 是 | 是 |
| 局限 | 需要部署 + 内核支持 | 只能处理**有域名的连接**；纯 IP 直连无法还原 |

### 7.3 实施过程中的三个坑

**坑 1：占位段和「本地地址」冲突**

我们的防火墙对 `fc00::/7`（ULA 网段）有「不做透明代理」的放行规则，而 FakeIP 默认的 v6 段恰好是 `fc00::/18` —— 结果占位地址被当成「本地地址」直接放过，永远到不了代理。

→ 把 FakeIP 的 v6 段改到 ULA 之外（用了 `2001:db8:1::/48` 这类文档段），流量就能被正常接管。

**坑 2：search domain 产生的怪名字**

Android 会带 DHCP 下发的搜索域来查，例如 `www.example.com.lan` —— 这个名字根本不存在。但 FakeIP 对**任何**查询都返回占位地址，于是客户端拿到一个「不存在的域名的占位地址」，连上去后网关还原出 `www.example.com.lan`，解析失败，连接瞬间被重置。

→ 把 FakeIP 规则**排在 `.lan / .local / .home.arpa / .internal` 这些本地后缀规则之后**。本地后缀走正常解析（正确返回 NXDOMAIN），其余才走 FakeIP。

**坑 3：域名还原后，路由规则还是按 IP 匹配**

FakeIP 还原出的是**域名**，而分流规则（比如「国内直连、其余走远端」）依赖 **IP 归属**。域名匹配不到 geoip，就会落到默认出口。

→ 在路由规则里插入一条 **`resolve`（解析）**：先把域名解析成真实 IP，后续的 IP 类规则才能正常匹配。

### 7.4 实测结果：纯 IPv6 客户端（IPv4 完全禁用）

| 目标类型 | 示例 | 结果 |
|---|---|---|
| 双栈站点（国内） | `www.example-cn.com` | **200**，走直连 |
| 双栈站点（境外） | `www.example-intl.com` | **200**，走隧道 |
| 社交类（境外） | `www.example-social.com` | **200** |
| **v4 单栈站点** | `www.example-v4only.net` | **200** |
| **v4 单栈站点** | `blog.example-v4only.org` | **301** |

最后一类是关键：**它们只有 A 记录，纯 v6 客户端照样访问成功** —— 客户端只做了 v6 连接，v4 的转换完全发生在网关。

> 顺带一个观察：配置正确的 FakeIP 下，双栈站点也一律走占位地址，等于把「选哪个地址族」的决定权从终端收回到网关。这对一致性和可观测性反而是好事。

---

## 八、前缀漂移：那个让整晚断网的坑

### 8.1 现象

运营商把委派前缀从 A 换成了 B。本机 `ping` 网关正常、解析隧道正常、IPv4 全通，但所有走 IPv6 的远端链路全部卡死，`ss` 里一片 `SYN-SENT`。

### 8.2 根因

```
1. 光猫仍在 RA 里广告旧前缀 A（valid_lft 还剩 ~2.7 小时）
2. 主机因此保留着 A 前缀的地址
3. RFC 6724 的源地址选择在两个 /64 之间打平（都是临时地址、同样长度前缀）
4. 内核挑中了 A 前缀的地址
5. 运营商已不再路由 A 前缀 → 出包黑洞
```

**最迷惑人的一点**：TCP 握手看起来「成功」——因为那是网关的透明代理**代答**的，不是远端服务器。真正的链路早就黑了。

### 8.3 修法：定期清理非当前前缀的地址

关键洞察：**「当前前缀」可以从地址寿命里推断出来** —— 光猫会让旧前缀的 `valid_lft` 逐渐衰减，而当前前缀会被持续续期。于是：

```
按前缀分组，取每组的 max(valid_lft)
最大者 = 当前前缀
比它小超过 600 秒的前缀 → 判定为陈旧 → 删掉其地址
```

两个必须注意的边界：

- **自己管理的 ULA 前缀必须排除**：它的寿命（9000s）天然比运营商前缀（43200s）短，否则会被误判成陈旧（第一次 dry-run 就抓到了这个误判）。
- **只碰 `scope global` 的 IPv6**：不碰 ULA、不碰 link-local、不碰 IPv4。

这套逻辑做进了本来就常驻的 RA 守护进程里（它已经带着 `CAP_NET_RAW`，再加一个 `CAP_NET_ADMIN` 就能删地址），**没有额外引入新服务**。

### 8.4 一个附带的 bug：为什么告警会「横跳」

清理逻辑之外，那晚还修了一个解析 bug：接收路径**没有校验 IPv6 头的 Next Header 字段**。任意 TCP/UDP 数据包，只要偏移 54 的字节碰巧等于 `134`（RA 的类型号），就会被误当成 RA 去解析，进而算出一个随机垃圾前缀。

```
真实前缀 2001:db8:aaaa::  ←→  垃圾 2001:db8:ffff::
```

修法是一条前置校验：

```python
def is_icmpv6(frame):
    return (frame[12:14] == b"\x86\xdd"     # 以太类型 = IPv6
            and frame[14] >> 4 == 6          # IP 版本 = 6
            and frame[20] == 58)             # Next Header = ICMPv6
```

> 教训：**解析网络报文，任何一个偏移量都要有协议层的前置校验**，否则「看起来能用」的代码会在低概率下产出垃圾数据。

---

## 九、复盘清单

如果重做一遍，这十条会提前写好：

1. **先用标准选项，再考虑私货**。RDNSS lifetime=0 是 RFC 8106 给的正当手段，不需要发明协议。
2. **RA 的合规性是硬门槛**。SLLAO + hop limit 255 缺一不可，否则 iOS 整条丢弃 —— 而 Linux 全都能过，所以这个坑只会在 iPhone 上暴露。
3. **警惕 on-link**。和目标同处一个 /64 的地址，流量不经过网关，网关上的任何规则都无效。这类问题只能从「对端行为」或「源头配置」下手。
4. **`accept_ra_rt_info_max_plen=64` 决定了 RIO 在移动端的天花板**。`/128` 再优雅也没用。
5. **周期广告不够，要事件驱动**。对手 30 秒重广告一次，你 20 秒才回一次，窗口就是 2/3 的时间。
6. **前缀漂移必然发生**，必须预设清理机制，且要用「寿命衰减」而不是「硬编码前缀」来判定新旧。
7. **TCP 握手成功不代表链路通** —— 透明代理会代答。诊断必须看**应用层**是否拿到数据。
8. **解析器的 search domain 会制造大量假名字**，任何「对所有查询都作答」的机制都要给本地后缀留出口。
9. **移动端 DNS 缓存很顽固**，改完解析策略后必须让设备重连（或重启）才能看到真实效果。
10. **不要用朴素命令行工具探测会被安全策略判定的服务**：某些防护会对「返回 4xx + 特定 User-Agent」的请求累计计数并临时封禁来源 IP，一旦把自己封掉，症状和「网络故障」一模一样（`Connection reset` / `Connection refused`）。

---

## 十、一句话总结

> IPv6 的世界里，**「地址」是 SLAAC 给的，「网关」是 RA 选的，「解析器」是 RDNSS 塞的，「走哪条路由」是 RIO 和最长前缀匹配决定的**。
> 把这四个环节各自的 RFC 弄清楚，家里的每一台设备就会各安其位；剩下的所有问题，都是这四件事的排列组合。
