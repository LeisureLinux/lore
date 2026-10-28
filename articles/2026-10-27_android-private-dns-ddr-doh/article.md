---
title: "安卓其实早就有系统级 DoH，只是被藏在一个 feature flag 后面"
date: 2026-10-27
slug: android-private-dns-ddr-doh
tags: [Android, PrivateDNS, DoH, DoT, DDR, RFC9462, SVCB, HTTP3, QUIC, NextDNS, AdGuard, Cloudflare, Quad9, Shizuku, ADB, device_config, CloudflareWorker, DNS加密, 移动网络]
category: 运维/网络
author: FreeLAMP.com
original_source: "Reddit r/nextdns《You can actually do system-wide DNS-over-HTTPS with Android's Private DNS!》（u/Timely-Skill4263，2026-10）+ ⭐ 实测拉取该帖作者的工具项目 eyalm2000/loophole（MIT，2026-10-24 创建）的完整 README"
original_date: 2026-10-27
original_url: "https://www.reddit.com/r/nextdns/comments/1xe03ic/you_can_actually_do_systemwide_dnsoverhttps_with/"
description: "安卓的「私人 DNS」（Private DNS）一直只能走 DNS-over-TLS（853 端口），这在封 853 的校园网/酒店/机场会直接失败。Reddit 上一个用户翻安卓源码后发现：系统其实完整实现了 RFC 9462（DDR，Discovery of Designated Resolvers），可以把 Private DNS 自动升级成 HTTP/3 上的 DoH —— 只是被一个 feature flag 挡着。实测拉取他配套的开源工具 loophole（Cloudflare Worker + 文档）后发现关键现实：Android 硬编码支持的只有 Google 与 Cloudflare，需要开 flag 的只有 Quad9 等极少数，而 NextDNS / AdGuard / Control D 等几乎所有主流服务都不发布 DDR 记录 —— 所以「原生支持」这条路对绝大多数用户实际上走不通，而 workaround 恰恰是它最大的价值。本文梳理完整原理、四条 flag、Cloudflare Worker + SVCB 记录的搭建方法、以及一个必须知道的安全代价（DoH 端点按设计是开放的）。"
published: true
---

> 来源：[Reddit r/nextdns：You can actually do system-wide DNS-over-HTTPS with Android's Private DNS!](https://www.reddit.com/r/nextdns/comments/1xe03ic/you_can_actually_do_systemwide_dnsoverhttps_with/)（作者 **u/Timely-Skill4263**，约 2026-10-24）
> ⭐ **本文实测拉取了该帖作者配套的开源项目 [eyalm2000/loophole](https://github.com/eyalm2000/loophole)（MIT 许可，2026-10-24 创建，5 个 commit）的完整 README 与文档**做交叉核对，并梳理了帖子全部热门评论。
> ⚠️ **本文含可执行的操作步骤（adb / Shizuku / DNS 记录配置）。** **这些操作会修改你手机的网络行为，请在充分理解后自行决定是否使用。**
> 本文为**解读**。

## 一句话结论

**安卓系统里其实早就完整实现了「用 DNS 发现 DoH 端点」（RFC 9462 DDR），只是被一个 feature flag 挡着 —— 而这解释了为什么你用 Private DNS 在校园网/酒店/机场会莫名其妙地失败。**

**⭐ 但真正重要的不是这个发现本身，而是它揭示的一个现实：**

**—— 「原生支持 DoH」这条路上，Android 硬编码支持的只有 Google 和 Cloudflare，需要开 flag 的只有 Quad9 等极少数，而 NextDNS、AdGuard、Control D、OpenDNS、CleanBrowsing、Mullvad 这些几乎所有主流服务**都不发布 DDR 记录**。**

**⭐ 也就是说：** **对绝大多数用户，这条路是走不通的 —— **而正因为走不通，那个 workaround（自建一个 Cloudflare Worker 当 DoH 端点）才成为唯一解，也才值得单独成篇。**

## 一、先讲清楚原来为什么坏

**帖子的开场（作者原话）：**

> **「安卓 Private DNS 这个功能最大的限制一直是：自定义主机名被锁定在 DNS-over-TLS 上。这意味着在封掉那个 TCP 端口的网络上 —— 比如大学 Wi-Fi、酒店、机场等等 —— 你的连接会彻底失败。」**

**⭐ 这个问题很多人遇到过但没想清楚原因：**

**—— Private DNS（私人 DNS）的协议强制是 DoT（DNS over TLS，跑在 853/TCP）。** **而很多企业/公共网络的策略是「封 853，只放行 443」。** **这时候系统设置里明明写了你的 DNS 服务器，域名却完全解析不了 —— 而且错误提示往往很模糊。**

**⭐ 而 DoH（DNS over HTTPS）跑在 443 上** —— **那个端口几乎不可能被封。**

**所以「Private DNS 支持 DoH」这件事的价值是：让系统级加密 DNS 在「只放行 443」的网络里也能用。**

## 二、⭐ 原理：DDR 是什么，为什么它能解决这个问题

**⭐ 这是全文的技术核心，而它其实是一个相当优雅的机制设计。**

**作者的解释（原文）：**

> **「在翻安卓源码之后，我发现 OS 其实完整支持 **Discovery of Designated Resolvers**（RFC 9462 DDR）来自动把 Private DNS 升级成 HTTP/3 DNS-over-HTTPS！**它就藏在那个 feature flag 后面。**」**

**⭐ 我把 loophole 的 README 里的机制描述抄下来，因为它讲得最清楚（原文）：**

> **「开了 flag 之后，安卓通过 DDR 自行发现 DoH 端点：**它在连接前会查询一条名为 `_dns.<hostname>` 的特殊 SVCB DNS 记录，如果该记录通告了一个 DoH 路径，安卓就会跳过 853 端口，改走 DoH，通常跑在 HTTP/3 上。**」**

**⭐ 换句话说，整个流程是：**

```
你在 Private DNS 里填 "dns.quad9.net"
        ↓
安卓先查一条 DNS 记录：_dns.dns.quad9.net
        ↓
这条记录（SVCB 类型）里写着："DoH 在 https://dns.quad9.net/dns-query，走 h3"
        ↓
安卓于是跳过 853，改用 DoH（HTTP/3 / QUIC，443/UDP）
```

**⭐ 我认为这个设计的优雅之处在于：** **它把「如何知道 DoH 端点在哪」的问题，**用 DNS 自己的扩展机制（SVCB/HTTPS 记录）来回答** —— 而不需要任何客户端额外配置。**

**—— 而且它复用了已有的「DoT 主机名」作为入口：** **你仍然填 `dns.quad9.net`，只是多了一次 SVCB 查询。**

## 三、⭐⭐ 关键现实：哪些服务真的支持 DDR

**⭐ 这一节是本文最实用的部分，因为原帖作者和 loophole 的 README 都强调了这一点。**

**loophole README 给的完整分类表（原文照录）：**

| 分组 | 服务商 | 在封 853 的网络上 |
|---|---|---|
| **硬编码进安卓** | Google（`dns.google`）、Cloudflare（`cloudflare-dns.com`） | ⭐ **DoH 可用，不需要 flag** |
| **不需要 flag 就能用** | 所有提供 DoT 端点的服务商（原生 Private DNS） | **只在 853 开放时可用；被封就失效** |
| **需要 flag** | **Quad9（`dns.quad9.net`）** 和其他支持的服务 | ⭐ **通过 DDR 走 DoH** |
| **不支持** | **NextDNS、AdGuard DNS、Control D、OpenDNS、CleanBrowsing、Mullvad DNS，以及其它大多数** | **即使开了 flag 也失败；需要 worker** |

**⭐ 作者在原帖里也说了同样的话：**

> **「我测了一堆，**唯一发布 DDR 记录的公开服务是 Google、Cloudflare 和 Quad9**。NextDNS 和 AdGuard，以及其它大多数流行服务商**连记录都没有**。🫠」**

**⭐ 而 loophole README 里有一句更精确的补充：**

> **「在主要 DNS 服务中，Quad9 是唯一一个支持 DDR 且需要打开 flag 的。Google 和 Cloudflare 不需要它，因为它们是硬编码的。」**

**—— 也就是说，「需要开 flag」这个能力，**目前几乎只有 Quad9 一家真正用上了**。**

### 3.1 ⭐ 而评论区最尖锐的一个问题，恰好指向了它为什么难普及

**Reddit 上一条评论（u/NegativePerformer788）：**

> **「DDR 对一个广告拦截型 DNS 服务商来说会很难实现。它也许能把连接升级到加密，**但它怎么知道该分配哪个 profile？**」**

**⭐ 我认为这是全文最重要的一条评论，因为它点出了这个机制的商业困境：**

**DDR 的 SVCB 记录是「**按域名**」发布的**（`_dns.<hostname>`）。** **而 NextDNS 这类服务的核心卖点是「**按用户**」的 profile**（每个用户有自己的配置 ID，对应一个不同的 DoH 端点 URL）。**

**—— 所以问题不是「技术上做不到」，而是「**DNS 记录是全域共享的，而 profile 是每用户私有的**」。** **你没法在 `dns.nextdns.io` 的公共 DNS 记录里告诉全世界「这个用户要用 profile abc123」。**

**⭐ 这也解释了为什么 NextDNS 官方没有跟进 —— 它需要的是一个「**用户专属的 DNS 记录**」，而 DDR 的模型是「**服务侧的公共记录**」。**

**⭐ 而 Google 和 Cloudflare 能做，是因为它们提供的是「**公共的、无状态的**」DoH 端点** —— 对应到用户是谁不重要。**

## 四、⭐⭐ 所以 workaround 是怎么做的：自己造一个 DoH 端点

**⭐ 而这正是 loophole 这个项目存在的意义 —— README 的「Why a gateway is needed」一节写得非常清楚：**

> **「loophole 给安卓的 Private DNS 一个它能自己发现的 DoH 端点，这样系统级加密 DNS 在封 853 端口的网络上仍然可用。它是一个你部署到自己账号的 Cloudflare Worker，加上让发现机制能工作的安卓 flag 文档。**不需要 VPN，不需要 root。**」**

**⭐ 我认为这个设计非常巧，因为它把「服务商不支持 DDR」这个死结，绕开了：**

**—— 你自己提供一个「公共的、无状态的」DoH 端点**（一个 Cloudflare Worker），**它转发到你真正的 NextDNS profile。** **这样 DDR 的「公共记录」模型就成立了。**

**README 的原话：**

> **「你的过滤服务自己**不需要**支持 DDR。」**

### 4.1 三条上手路径

**loophole README 给了三条路径，我按门槛排序：**

| 路径 | 需要什么 | 适用场景 |
|---|---|---|
| **① 引导式部署（推荐）** | **Worker + Android 16+ + 自有域名** | 大多数人 |
| **② 只开 flag** | **Android 16+**，服务商自己支持 DDR | ⭐ **用 Quad9 的话根本不需要 Worker** |
| **③ 自建 DoH 端点 / DNS** | **DoH 端点 + 你自己域名的 DNS 控制权** | 已有 DoH 的人 |

**⭐ 注意路径 ② 的存在 —— 这是最容易被忽略但最省事的一条：**

**⭐ 如果你不依赖广告拦截、只是想要「加密的系统 DNS」，** **那么直接用 Quad9 + 两条命令就够了，不需要 Worker、不需要域名、不需要 Cloudflare 账号。**

### 4.2 路径 ③ 的 DNS 记录长什么样

**README 给的记录（原文）：**

| 字段 | 值 |
|---|---|
| Type | **SVCB** |
| Name | **`_dns.<你的主机名>`**（填进 Private DNS 的那个主机名，前面加 `_dns.`） |
| Priority | 1 |
| TTL | Auto |
| Target | `<你的 DoH 主机名>.`（**带尾点**） |
| Parameters | **`alpn="h3" dohpath="/dns-query{?dns}"`** |

**⭐ 而 README 还给了调整说明：**

> **「按你的服务器调整两件事：如果它不提供 HTTP/3，用 `alpn="h2"`（或 `alpn="h2,h3"` 如果两种都提供）；如果你的 DoH 路径不是 `/dns-query`，把你的路径放进 `dohpath` 里。如果你的端点跑在 443 以外的端口上，在参数里加 `port=<数字>`。」**

**⭐ 而 `alpn="h3"` 这点值得单独说：** **它指的是 QUIC（HTTP/3 over UDP/443）。** **这正是 DoH 相对 DoT 的另一个优势 —— **QUIC 在丢包环境下通常比 TCP 表现更好，而且**首次连接不需要额外往返**。**

### 4.3 要开的 flag 只有两条

**⭐ 这是最漂亮的部分 —— 整个功能只需要两个 flag：**

```
adb shell device_config put connectivity dns_ddr_version 1
adb shell device_config put connectivity networkmonitor_async_privdns_resolution 1
```

**而 README 强调了一个非常容易踩的坑：**

> **「必需的最后一步：打开飞行模式，等几秒，然后关掉。安卓只在重连之后才应用这个改动。**不做这一步，设置就不会生效。**」**

**⭐ 而评论区有人实测了这个流程，并补充了更完整的命令集（u/Masterflitzer 在 Galaxy S23 Plus / Android 17 / OneUI 9.0 上验证）：**

```
settings put global private_dns_mode hostname
settings put global private_dns_specifier one.one.one.one

device_config put connectivity resolver_dns_over_http3_enabled true
device_config put connectivity resolver_discovery_of_designated_resolvers_enabled true

device_config put connectivity networkmonitor_async_privdns_resolution 1
device_config put connectivity dns_ddr_version 1

device_config put com_android_networkstack com.android.networkstack.flags.network_monitor_dns_ddr true

device_config put netd_native doh 1
```

**⭐ 他的实测结论：**

> **「一开始不工作，但跑了这些命令并重启手机之后它终于работа了」**
>
> **「我用的是 Cloudflare 帮助站的测试域名 `one.one.one.one` 和 `cloudflare-dns.com` 来测试，**因为只有后者在安卓的硬编码白名单里** —— 在做这个之前前者显示 `dot`（DoT）而后者显示 `doh`，现在跑完这些命令并重启手机后**两个都显示 doh**，所以说明它生效了。」**

**⭐ 「dot vs doh」这个显示差异是个很好的验证方法** —— **因为系统设置界面会直接告诉你当前 Private DNS 是走的 DoT 还是 DoH。**

## 五、⭐⭐⭐ 必须知道的安全代价

**⭐ 这一节是本文我最想强调的部分，因为 README 自己把它放在 FAQ 的前几条，而且它是**设计上无法避免**的。**

### 5.1 DoH 端点按设计是开放的

**README 原文：**

> **「网关的 `/dns-query` 端点**按设计是开放的**。DDR 要求安卓**在无需认证的情况下**访问它，所以任何找到你网关 URL 的人都可以通过它发查询，**而你的上游 profile 会看到他们的流量**。**除非你接受这一点，否则不要公开你的网关域名。**」**

**⭐ 我想解释一下这个代价的准确形态，因为容易被误解：**

| 谁 | 能看到什么 |
|---|---|
| **看到你的 DNS 查询**（域名） | **你的上游服务商**（NextDNS profile 的所有者）—— 这是本来就会发生的 |
| **⭐ 用你的网关查询** | **任何知道 URL 的人** —— 他们的查询会被算在**你的** profile 上，可能触发你的配额/规则误触发 |

**⭐ 而 README 明确说了 PIN 锁不住它：**

> **「为什么 DNS 端点是开放的？不能拿 PIN 锁住吗？不能。DDR 要求安卓**在无需认证的情况下**访问端点，所以端点无法被锁。**PIN 只保护 dashboard。**」**

**⭐ 这一点值得反复强调 —— 因为很多人在自建 DoH 时会本能地加上鉴权，然后发现 DDR 发现失败。** **不是配置错了，是 DDR 的模型就是「无认证发现」。**

### 5.2 ⭐ 而「你的域名就是你的钥匙」

**⭐ 所以 README 的建议是：「除非你接受这一点，否则不要公开你的网关域名。」**

**⭐ 而这在实践中意味着：** **你的 Worker 域名（如果是 `xxx.workers.dev`）或者你自己域名下的那个主机名，本质上是一个「公开的秘密」。** **谁拿到它就能借用你的 DNS 配置。**

**⭐ 现实影响评估：** **这和「公开的 DNS over HTTPS 端点」是同一类东西 —— 而 Cloudflare/Google 的公共 DoH 端点本来就是公开的。** **真正的风险不是「别人能用你的 DoH」，而是「别人能用你的 NextDNS profile，从而让**你的**规则集被别人的查询触发**，或者消耗你的配额。**

### 5.3 ⭐ 而「不需要 root / 不耗电 / 可以随时撤销」这三点是真实优势

**README 的 FAQ（原文）：**

> **「需要 root 吗？不需要。loophole 通过 Shizuku 或 ADB 管理系统设置。**」**
>
> **「会耗电或后台运行吗？不会。**设置完成后手机上没有任何东西在运行。Private DNS 是一个系统设置，不是一个 app，也不是 VPN，所以没有后台服务，也没有电量开销。**」**

**⭐ 而原帖作者补充了他做这个项目的直接动机：**

> **「这意味着像 RethinkDNS 那样吃电的后台 VPN app 不再必要了（我一直很讨厌那种后台 VPN，所以这对我来说意义重大😅）。**」**

**⭐ 我认为这一点值得展开，因为「用 VPN app 做 DoH」和「用系统级 Private DNS 做 DoH」的差别，比表面看起来大：**

| | **后台 VPN app**（RethinkDNS 等） | **系统 Private DNS + DDR** |
|---|---|---|
| **拦截范围** | **需要 VPN 模式 → 全部流量走隧道** | **⭐ 只有 DNS 查询** |
| **电量** | **常驻，耗电** | **⭐ 无后台进程** |
| **绕 VPN 的坑** | ⭐ **会和银行的 app 冲突** | **⭐ **不影响任何其他流量** |
| **能自定义 DNS 服务器** | 可以 | **⭐ 可以** |

## 六、⭐ 几个操作细节与坑

**⭐ 我把 README 和评论区的细节汇总成一份清单：**

### 6.1 需要 Android 16+（不是 15）

**⭐ 注意作者自己修正过一次：**

> **「这个设置自己搞需要 ~~Android 15+~~（编辑：我说错了，**16+**）**」**

### 6.2 不开 root，用 Shizuku 或 ADB

**README：**

> **「Shizuku：在手机上安装 Shizuku，通过无线调试配对，然后装 aShell You 并允许它访问 Shizuku。在那里逐条运行下面的命令。**」**
>
> **「ADB：从电脑装 Android Platform Tools，开启开发者选项和 USB 调试，USB 连接，跑 `adb devices` 确认手机出现。**」**

**⭐ 所以手机本地也能做，不需要电脑 —— 这对很多用户是关键。**

### 6.3 ⭐ flag 会被重置 —— 而这有个「副作用开关」

**README 有一段很多人会忽略但很实用的内容：**

> **「如果这些设置一直重置，这会禁用整机的 DeviceConfig 同步。**只在需要时使用：**」**
>
> ```
> adb shell device_config set_sync_disabled_for_tests persistent
> ```
>
> **「恢复：** `adb shell device_config set_sync_disabled_for_tests none`**」**

**⭐ 这一点很重要 —— 因为 DeviceConfig 的设置是从 Google 服务端同步的，**如果你只改了本地，OTA 更新或同步可能把它冲掉。** **而「禁用同步」这个开关是官方提供的、专门给这类场景用的测试接口。**

### 6.4 检查是否生效

```
adb shell device_config get connectivity dns_ddr_version
adb shell device_config get connectivity networkmonitor_async_privdns_resolution
```

**⭐ 两个都应返回 `1`。** **而更直观的验证是：** **看系统设置里 Private DNS 的状态显示 —— 如果显示 `doh` 而不是 `dot`，说明 DDR 生效了。**

### 6.5 ⭐ 不需要自定义域名的情况

**README 的一个 FAQ：**

> **「不用自定义域名能用吗？部分能。基础 DoH 和 dashboard 在 `workers.dev` 地址上能用，但**安卓的主机名发现需要自定义域名和它的 SVCB 记录。没有域名，Private DNS 无法发现网关。**」**

**⭐ 也就是说：** **Worker 本身可以挂在 `workers.dev` 上，但 **SVCB 记录必须在你自己的域名下** —— 因为 `_dns.<hostname>` 这条记录需要一个你能控制的 zone。**

## 七、⭐ 我的评价

### 7.1 ⭐ 这个发现的价值，比「又一个 DoH 技巧」大

**⭐ 我认为这个帖子的价值在于它揭示了一个**被忽视的、一直在那里的**能力：**

**—— 安卓完整实现了 RFC 9462，代码在树里，只差一个开关。** **而这个开关之所以没打开，很可能就是因为「开了也没用」：**

**⭐ 因为能从中受益的服务商，几乎只有 Google、Cloudflare（不需要开）和 Quad9（需要开）。** **而 2026 年的主流 DNS 服务商（NextDNS、AdGuard、Control D…）全都不发布 DDR 记录 —— 对它们来说，DDR 在商业上不成立。**

**⭐ 所以这个 flag 大概率会永远关着 —— 除非有人解决评论区提出的那个问题：**

> **「它怎么知道该分配哪个 profile？」**

**—— 而那需要的是「用户专属的 DNS 记录」，而不是现有的 DDR 模型。**

### 7.2 ⭐ 而 workaround 之所以有价值，恰恰是因为原生路走不通

**⭐ 我认为这是本文最值得记住的一层因果：**

**因为 NextDNS / AdGuard 都不支持 DDR，所以「支持 DDR 的下一个 Android 版本」这个愿望对它们没有意义。** **而对用户来说，唯一的出路就是自己架一个转发 Worker。**

**—— 于是形成了一个有点讽刺的格局：** **系统里有能力，但商业上没人用；用户有需求，但系统能力用不上；最后是两个人自己搭桥。**

### 7.3 ⭐ 而这个案例本身，是「源码阅读 + 实验」能产出真实价值的一个好例子

**⭐ 原帖作者的原话：**

> **「在翻安卓源码之后，我发现 OS 其实完整支持 RFC 9462 DDR……」**

**⭐ 而他做这件事的路径是：遇到一个「封 853 就完全不能用」的实际痛点 → 去翻源码 → 发现有一个被藏起来的能力 → 验证它 → 写出来 → 顺手做成开源工具。**

**—— 这比任何「隐私技巧」文章都更有价值，因为它给出了一个**可复用的方法论**（症状 → 源码 → feature flag → 验证），而不是一个配方。**

### 7.4 ⚠️ 而必须提醒的边界

**⭐ 三条：**

**① 不要公开你的网关域名。** **（README 原文警告）**

**② 这个方案对「已经用 VPN app 做 DoH」的用户收益最大**（省电 + 不干扰其他流量）；**如果你已经用 AdGuard/NextDNS 的 app 且不介意耗电，收益没那么大。**

**③ ⭐ 它只解决 DNS 加密，不解决 DNS 泄漏以外的隐私问题** —— **DNS-over-HTTPS 保护的是「谁看到你的查询」，不是「你访问了什么」。**

**⭐ 而值得加一句：** **原帖评论区里有人提到 FortiGate 用户在防火墙上直接屏蔽 DoH（「yeah. im blocking DoH within the firewall. nice try, maybe next time 😄 Fortigate FTW」）—— **企业网络管理员对 DoH 的封锁，本身就是这个方案在企业环境里的最大障碍。**

## Sources

- Reddit r/nextdns：You can actually do system-wide DNS-over-HTTPS with Android's Private DNS!（u/Timely-Skill4263）：https://www.reddit.com/r/nextdns/comments/1xe03ic/you_can_actually_do_systemwide_dnsoverhttps_with/
- ⭐ 一手：[eyalm2000/loophole](https://github.com/eyalm2000/loophole)（MIT，2026-10-24 创建，5 commits）—— README 与完整文档
- RFC 9462：Discovery of Designated Resolvers（https://datatracker.ietf.org/doc/html/rfc9462）
- Shizuku：https://shizuku.rikka.app/download/
- aShell You：https://github.com/DP-Hridayan/aShellYou
- Android Platform Tools：https://developer.android.com/tools/releases/platform-tools

---

（说明：所有引号内内容为 Reddit 原帖、评论区与 loophole README 原文引用；**第四节与第六节的操作细节为原文与评论区的汇总，未做任何改动**；**第五节的三条代价分析、第七节的评价为笔者补充**。**Reddit 评论区用户的实测机型为 Galaxy S23 Plus / Android 17 / OneUI 9.0。**）
