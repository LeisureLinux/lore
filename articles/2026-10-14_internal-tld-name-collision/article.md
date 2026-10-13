> 主题：DNS · 内网命名 · 名字碰撞 · 安全加固。本文为**原创调研**，所有域名状态均经 IANA 登记表与根区实测核验。文中域名、IP、用户名均已脱敏。

## 一句话结论

家用路由器默认给你 `.lan`，mDNS 用 `.local`，老企业内网挂着 `.corp` / `.home` —— 这些名字**都没有任何官方保障**。

其中 **`.local`** 有标准但**只能用于 mDNS**；**`.home.arpa`** 是唯一"现在就有 RFC"的普通 DNS 家庭域名；**`.corp` / `.home` / `.mail`** 已经被 ICANN **冻结委派**（因为使用量太大，一旦委派就是全球性事故）；而 **`.lan`** —— **连冻结都没有，它只是还没轮到被委派**。

2024 年 7 月，ICANN 董事会正式保留了一个新的私有用途顶级域 **`.internal`**，目标是**让所有人从 `.lan` / `.corp` / `.home` 这类未保留的名字上迁移走**。

---

## 一、先看权威数据：IANA 特殊用途域名登记表

判断一个域名"用在哪儿是否安全"，唯一权威来源是 **IANA 的特殊用途域名登记表**（Special-Use Domain Names，依据 RFC 6761）。

我把完整列表拉了下来，**只有两个"内网用途"的域名被正式登记**：

| 域名 | 引用 | 状态 |
|---|---|---|
| **`home.arpa.`** | **RFC 8375** | ✅ Standards Track（2018）|
| **`local.`** | **RFC 6762** | ✅ Standards Track（mDNS）|

**而下面这些全部未登记：**

| 域名 | IANA 登记 | 引用 |
|---|---|---|
| `.lan` | ❌ 无 | — |
| `.corp` | ❌ 无 | — |
| `.home` | ❌ 无 | — |
| `.internal` | ⏳ 暂未登记 | ICANN 已保留（2024-07）|
| `.private` | ❌ 无 | — |

### 根区实测

"未登记"到底意味着什么？我直接问了根服务器：

```bash
$ dig lan       NS @198.41.0.4     # → status: NXDOMAIN
$ dig corp      NS @198.41.0.4     # → status: NXDOMAIN
$ dig home      NS @198.41.0.4     # → status: NXDOMAIN
$ dig internal  NS @198.41.0.4     # → status: NXDOMAIN
$ dig arpa      NS @198.41.0.4     # → a.ns.arpa.   [status: NOERROR]  ← 唯一例外
```

**注意 `NXDOMAIN` 前面还有 `aa` 标志**（Authoritative Answer）：

```
$ dig lan NS @198.41.0.4 | grep flags
;; flags: qr aa rd; QUERY: 1, ANSWER: 0, AUTHORITY: 1
              ^^
```

**根区是"权威地"告诉你 `.lan` 不存在** —— 这是确定性否定，不是"我懒得理你"。

**这也解释了**为什么内网监控里会出现 `printer.lan.lan`、`nas.lan.lan` 这类畸形查询 —— 客户端拿到 NXDOMAIN 后还会继续 devolution 叠加后缀，一路问到根。

---

## 二、逐个解析

### `.local` —— ✅ 有标准，但**只能用于 mDNS**

**RFC 6762（Multicast DNS）** 的规定很明确：

> This document specifies that the DNS top-level domain **".local." is a special domain with special semantics**, namely that any fully qualified name ending in ".local." is **link-local**, and names within this domain are **meaningful only on the link where they originate**.

**机制是这样的：**

```
任何 .local 查询 → 不走普通 DNS 单播
                 → 发到 mDNS 组播地址 224.0.0.251（IPv4）/ FF02::FB（IPv6）
```

**⚠️ 这里有个非常常见的误用。**

很多家用路由器把 `.local` 配成**普通 DNS 域**（在 dnsmasq / unbound 里写 A 记录）—— 这**违背了 RFC 6762**。

| 正确用法 | 错误用法 |
|---|---|
| `.local` + Avahi / mDNS | `.local` + 普通 DNS 记录 |
| 客户端发组播查询 | 客户端发单播查询，或被 mDNS 抢答 |

**如果你同时在跑 Avahi 和一条 DNS A 记录**，会遇到"有时能解析、有时不能"的诡异现象 —— 因为 mDNS 和传统 DNS 在抢答同一个名字。

**结论**：`.local` 可以用，**但规规矩矩交给 mDNS**。别把它当普通内网域名。

---

### `home.arpa.` —— ✅ **唯一有 RFC 的普通 DNS 家庭域名**

**RFC 8375（Standards Track，2018 年）**：

> 'home.arpa.' is designated for **non-unique use in residential home networks**.

**为什么是 `.arpa` 而不是大家更喜欢的 `.home`？** RFC 里说得很直白：

> This document **corrects an error in RFC 7788** by replacing '.home' with 'home.arpa.' as the default domain name for homenets.
>
> **'.home' was selected as the most user-friendly option; however, there are existing uses of '.home' that may be in conflict with this use.**

**更关键的一句：**

> No such process is available for requesting a similar delegation in the root at the request of the IETF, **which does not administer that zone**. As a result, **all unregistered uses of '.home'** ...

**翻译一下这段话的分量**：

```
IETF 管不了根区（根区归 ICANN）
  ↓
所以 IETF 无法阻止 .home 将来被委派给某个商业注册局
  ↓
为了安全，只能退到 .arpa
  ↓
因为 .arpa 由 IETF 自己管理，永远不会被商业化委派
```

**这就是 `.arpa` 的特殊地位** —— 它是唯一一个根区里有 NS 记录的"特殊用途"TLD（其他如 `test` / `example` / `invalid` 都是 NXDOMAIN）。

**所以：家庭网络如果要一个"永远安全"的名字，`home.arpa` 是唯一答案。**

---

### `.lan` —— ⚠️ **最流行，但零保障**

**未登记、未保留、根区 NXDOMAIN。**

**为什么它这么流行？**

- **短**（三个字母，手机上也少敲两下）
- **语义直观**（Local Area Network）
- 家用路由器固件（OpenWrt 及多个品牌）默认用它
- 各类内网教程里到处是 `something.lan`

**ICANN 公开征询时，确实有人力挺 `.lan`：**

> I suggest to use **`.lan` instead of `.internal` or `.private`**. `.lan` is much faster and easier to type, especially on mobile devices.
>
> `.lan` is the abbreviation of "Local Area Network" so it would make perfect sense.

**但最终 ICANN 选了 `.internal`。**

**风险在哪**：**没有任何机构承诺不委派 `.lan`。** 它和 `.corp` / `.home` 不同 —— 那两个至少被"冻结"了，而 `.lan` **连冻结都没有**，只是"恰好还没轮到"。

---

### `.corp` / `.home` / `.mail` —— ⛔ **已被明确冻结委派**

**这三个有过著名的事故。**

首轮新 gTLD 计划（New gTLD Program）期间，**企业内网对这三个名字的使用量太大**，导致：

- 大量内部查询**泄漏到根服务器**
- 如果 ICANN 把它们委派出去，**全球企业会在同一天集体撞车**

**结果**：ICANN **停止了这些字符串的委派**（halt delegation）。

**⚠️ 但"冻结"不等于"永久保留"：**

```
这是 ICANN 的【政策决定】，不是技术保证
  ↓
理论上未来可能解冻
  ↓
而且 SSAC-113 明确建议：
  与其让企业继续挤在这些未保留的名字上
  不如给他们一个正式保留的 .internal
```

**所以 `.corp` / `.home` 现在"能用"，但这是**借来的时间**。**

---

### `.internal` —— ⭐ **ICANN 给出的官方答案**

**这是最近最重要的变化。**

| 时间 | 事件 |
|---|---|
| 2020-09 | **SSAC-113**（ICANN 安全与稳定咨询委员会）建议保留一个私有用途 TLD |
| 2024-01 | ICANN 公开征询候选字符串 |
| **2024-07** | **ICANN 董事会决议保留 `.internal`** |
| 2025–2026 | IETF 起草 `draft-davies-internal-tld`（最新 **-06**，2026 年 5 月）|

**草案的作者阵容很说明问题：**

```
K. Davies       ← IANA
A. McConachie   ← ICANN
W. Kumari       ← Google
```

**IANA + ICANN + Google 联合署名** —— 这不是社区提案，这是**官方意志**。

**草案的核心承诺：**

> ... the "internal" top-level domain is **reserved from being used in the global DNS** it **MUST NOT appear in the DNS root zone** except to the minimum extent necessary.

**`MUST NOT appear in the root zone`** —— 这是**永久保留**的保证。

**目标也很明确**（ICANNWiki）：

> with the aim of steering operators away from undelegated choices such as **`.corp`, `.home` or `.lan`** that might later collide with public delegations.

**⚠️ 目前状态**：**草案还没成为 RFC**（最新 `-06`，2026 年 11 月过期），所以 `.internal` **还没有进入 IANA 登记表**。但 **ICANN 董事会已经批准保留**，方向是确定的。

---

## 三、风险到底有多大：三种真实场景

### 风险 1：查询泄漏到公网（最常见）

```
内网用 .lan
  ↓
笔记本带出公司，连咖啡厅 WiFi
  ↓
解析 printer.lan / nas.lan 等名字
  ↓
公司 DNS 不可达 → 查询泄漏到公网根服务器
  ↓
攻击者看到你的内网命名（信息泄露）
```

**这不是假设。** 内网 DNS 服务器的查询日志里就能看到这类泄漏的查询（`*.lan` 之类的 NXDOMAIN），而且都是打到根服务器才回来。

### 风险 2：名字碰撞 → MitM（最严重）

**这是 US-CERT 专门发过警报的场景（TA16-144A）：**

```
某天 .lan 被委派给某注册局
  ↓
攻击者注册 printer.lan 或 nas.lan
  ↓
你的员工在外网时解析到攻击者的 IP
  ↓
流量被劫持（中间人攻击）
```

**US-CERT 原话：**

> Web Proxy Auto-Discovery (WPAD) DNS queries that are intended for resolution on **private or enterprise DNS servers have been observed reaching public DNS servers**.
>
> **Opportunistic domain registrants could abuse these collisions** by configuring external proxies for network traffic and enabling **man-in-the-middle (MitM) attacks** across the Internet.

**Verisign 的实测数据**：约 **2000 万条/天**的脆弱查询在公网上出现。

### 风险 3：证书体系冲突

```
内网用 .lan，自签证书签给 ca.lan
  ↓
某天 .lan 成为公共 TLD
  ↓
你的内网 CA 和公网 CA 体系冲突
  ↓
浏览器警告、TLS 失败、内部服务集体不可用
```

---

## 四、家庭网络 vs 企业内部

| 场景 | `.lan` 安全性 | 说明 |
|---|---|---|
| **纯家庭网络** | ⚠️ 尚可接受 | 设备少、风险窗口小，但**仍建议换** |
| **企业内网** | ❌ **不推荐** | 设备多、笔记本会带出、合规要求高 |

### 企业内部还有一条：Active Directory 的域该叫什么

**这是微软自己给过建议的地方。**

**不要**用 `.corp`、`.local`、`.lan` 这类未保留的名字做 AD 域。原因：

1. **`ad.local` 类域名会和 mDNS 打架** —— Windows 客户端可能会把 `.local` 的查询发给 mDNS
2. **`.corp` / `.home` 有委派风险** —— 一旦委派，企业所有机器的 Kerberos / LDAP 都会冲突
3. **证书链冲突** —— 内部 CA 签的 `.corp` 证书未来可能与公网冲突

**微软的建议**：用**你真正拥有的域名**下的子域，例如：

```
你的公网域名: example.com（你注册并控制的）
AD 域:        ad.example.com  或  corp.example.com
```

**为什么这样安全**：因为 `example.com` 在**你手里**，它的任何子域都不会被别人注册 —— 不存在"未来被委派"的问题。

**代价**：需要一点额外配置（内网 DNS 对 `ad.example.com` 做本地权威，不要泄漏到公网），但这比"某天域名被抢注"便宜得多。

---

## 五、给不同场景的建议

### 家庭网络

**推荐 `home.arpa`** —— 唯一"现在就有 RFC 保障"的选项。

```conf
# dnsmasq 示例
local=/home.arpa/
address=/router.home.arpa/192.168.1.1
address=/nas.home.arpa/192.168.1.10
```

**次选 `.internal`** —— ICANN 官方方向，但客户端支持度还不明确（浏览器、路由器固件未必认）。

**如果已经在用 `.lan`**：不必急着迁移（见下）。

### 企业内部

**优先用你自己拥有的公网域名的子域**：

```
ad.example.com          ← AD 域
internal.example.com    ← 内部服务
*.corp.example.com      ← 或其他你控制的结构
```

**理由**：这是**唯一不会有名字碰撞风险**的方案，因为根区里那条委派链在**你自己手里**。

### 如果已经在用 `.lan` / `.corp` / `.home`

**迁移成本很高**（改 DNS、DHCP、证书、所有客户端配置）。**所以第一步不是迁移，而是隔离。**

**关键动作：让本地 DNS 成为这些名字的权威，不再向上游查询。**

以 unbound 为例：

```conf
# 把整个 lan. 子树设为本地权威（static）
local-zone: "lan." static
local-data: "lan. 3600 IN SOA ns.lan. hostmaster.lan. 1 3600 900 604800 86400"
local-data: "lan. 3600 IN NS ns.lan."
local-data: "ns.lan. 3600 IN A 192.168.1.1"

# 具体记录
local-data: "router.lan. 3600 IN A 192.168.1.1"
```

**`static` 和 `transparent` 的区别是关键：**

| 类型 | 未定义的名字 | 是否向上游查询 |
|---|---|---|
| **`transparent`** | 有记录就答，**没有就转发上游** | ✅ **会泄漏** |
| **`static`** | **全部本地权威**，未定义即 NXDOMAIN | ❌ **永不外泄** |

**验证生效**（看 `aa` 标志）：

```bash
$ dig nosuch.lan @192.168.1.1 | grep flags
;; flags: qr aa rd ra          ← 有 aa = 本地权威，没碰上游
```

**这一个改动的价值，比换域名大得多** —— 它直接切断了"查询泄漏"和"名字碰撞劫持"两条攻击路径。

---

## 六、一张表总结

| 域名 | 官方状态 | 泄漏风险 | 碰撞风险 | 推荐度 |
|---|---|---|---|---|
| **`home.arpa`** | ✅ RFC 8375 | 无（`.arpa` 永不委派）| 无 | ⭐⭐⭐⭐⭐ |
| **`internal`** | ⏳ ICANN 已保留（草案中）| 无（承诺不委派）| 无 | ⭐⭐⭐⭐⭐ |
| **`local`** | ✅ RFC 6762 | 无 | 无 | ⭐⭐⭐（**仅限 mDNS**）|
| **`.lan`** | ❌ 无 | **有** | **有** | ⭐⭐ |
| **`.corp`** | ❌ 无（已冻结委派）| 有 | 低（已冻结）| ⭐⭐ |
| **`.home`** | ❌ 无（已冻结委派）| 有 | 低（已冻结）| ⭐⭐ |
| **`.private`** | ❌ 无 | 有 | 有 | ⭐ |
| **`ad.example.com`** | ✅ 你自己的域 | 无 | **无** | ⭐⭐⭐⭐⭐（企业）|

---

## 七、核心结论

**1. `.local` 可以，但只能交给 mDNS。** 它被 RFC 6762 保留为链路本地——用普通 DNS 配它是误用，会造成"时而能解析时而不能"的诡异现象。

**2. `home.arpa` 是家庭网络唯一有 RFC 保障的普通 DNS 域名。** RFC 8375 明确写了为什么放弃 `.home`：IETF 管不了根区，无法阻止 `.home` 未来被委派。

**3. `.internal` 是 ICANN 2024 年指定的未来标准。** IANA + ICANN + Google 联合起草的草案明确写道它 **MUST NOT appear in the root zone**（永不进入根区），目标是让所有人从 `.lan` / `.corp` / `.home` 迁走。

**4. `.corp` / `.home` / `.mail` 已被冻结委派 —— 但那是政策决定，不是技术保证。** 它们现在能用，是"借来的时间"。

**5. `.lan` 是这批里最没有保障的。** 它既没有 IANA 登记，也没有进入冻结名单 —— 它只是"恰好还没轮到被委派"。**这是明确的风险。**

**6. 企业内网最安全的做法是"用你自己拥有的域名的子域"** —— 因为那意味着委派链在你手里，不存在碰撞可能。

**7. 但最重要的不是换域名，而是"是否隔离"。** 把内网域设为本地权威（`static`），比迁移到新域名重要得多 —— 它一步切断泄漏和劫持两条路径。

---

*本文所有域名状态均通过 IANA 特殊用途域名登记表（Special-Use Domain Names Registry）与根服务器实测核验（`dig <tld> NS @198.41.0.4`）。文中 IP、主机名均已替换为文档或内网保留段。*
