---
title: "Unbound 与 DNS 隐私：换提供商只是换谁拿着完整清单"
date: 2026-11-14
slug: unbound-dns-privacy-recursive-qname-minimization
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：MakeUseOf《I stopped handing my browsing history to Google, Cloudflare, and my ISP, and the fix wasn't another provider》（Afam Onyimadu，2026-11-14 09:30 EST；作者自述过去一有更私密的 DNS 提供商就切换、后来意识到只要仍由一家公司处理全部查询就只是换了持有者；Cloudflare 1.1.1.1 截断 IP 末段、25 小时内删除截断 IP 与 resolver 日志、请四大会计所审计并公开报告、采样至多 0.05% 数据包用于排障/DoS 缓解、可无限期保留聚合域名统计；Google 保留含完整 IP 的日志 24–48 小时后仅留城市级数据；加密 DNS 只挡 ISP、不挡对端；给出四种 setup 对照表；Unbound 两种跑法、完整递归从根跟随 referral、QNAME minimization 逐层少给信息、转发模式下对方仍拿到完整请求；缓存命中本地答；作者用 1.24.2，Windows Smart App Control 拦未签名安装包后改用 WSL；权衡：SNI/ECH、递归查询多为明文、权威服务器看到自家公网 IP、失去公共解析器的 crowd cover；Pi-hole/OPNsense/pfSense/OpenWrt 支持但默认不同）＋ Cloudflare 官方《1.1.1.1 Public DNS Resolver》隐私承诺（不出售/不用于广告、非易失存储不留源 IP、IPv4 截末段 / IPv6 截后 80 位且 25 小时内删除、Public Resolver Logs 25 小时内删、0.05% 随机采样包仅排障与 DoS、与 APNIC 研究合作、四大会计所审计、聚合数据可无限期保留；并明确 resolver 向权威服务器发出的子请求日志里含 subrequest.queryName）＋ Google 官方《Your Privacy | Public DNS》（临时日志同时含设备 IP 与 DNS 查询、24–48 小时删除、DoH 另记 Content-Type 与 Accept 头、安全/滥用场景可超过 48 小时；永久日志抽样去掉 IP 换成城市/区域级位置，含域名、请求类型、ASN、时间戳、ECS 前缀长度等）＋ NLnet Labs Unbound 官方 About（开源 validating recursive resolver、校验 DNSSEC、缓存；支持直接走 DNS 层次或转发选定查询；通过 QNAME minimisation 减少不必要的查询信息披露）＋ RFC 7816 QNAME minimisation 与 RFC 8020 NXDOMAIN cut 的背景（用于解释「遇坏应答会回退多发细节」）＋ 作者自建 Unbound/Adhole 相关开源电子书《DNS 的加密和隐私防护——从如何加固 Unbound 说起》公开大纲与 llms.txt（仅借概念框架：存根/缓存/转发/递归四种角色、DNSSEC 与 DoT/DoH 分工、QMIN 严格模式与 CDN 兼容、多个 forward-addr 是并发竞速而非主备；不写入本地路径与项目内部细节）"
original_date: 2026-11-14
original_url: "https://www.makeuseof.com/unbound-private-dns-without-trusting-another-provider/"
description: "解读 MakeUseOf 那篇「不再把浏览历史交给 Google / Cloudflare / ISP」的核心论点：加密 DNS 只把查询从 ISP 手里挪到所选提供商手里，换提供商只是换谁持有完整清单。文章用 Cloudflare 1.1.1.1 与 Google Public DNS 的官方隐私文档核了媒体口径：前者 IPv4 截末段 / IPv6 截后 80 位、截断 IP 与 resolver 日志 25 小时内删除、0.05% 采样排障、四大审计、聚合域名统计可无限期保留，且官方明写向权威服务器发出的子请求日志含 queryName；后者临时日志同时含完整 IP 与查询、24–48 小时删除、安全滥用可延长、永久日志改城市级位置。重点解释 Unbound 的完整递归：从根开始跟随 referral，配合 QNAME minimization，让根只听到要找 com、.com 只听到要找 example.com、只有权威站才听到完整名字；缓存命中则本地答，因此没有任何单一公司拿到全量列表。并强调转发模式的边界：即使 Unbound 自己也做 QMIN，只要把完整请求转给上游，对方仍看到全名。文章补上原作者列出的三个代价：无 ECH 时 SNI 仍暴露站点名、递归查询多为明文且 ISP 可主动抓包、权威服务器看到你的公网 IP 从而失去大解析器的群体掩护。也用 Unbound 官方文档与公开电子书大纲把四个角色（存根/缓存/转发/递归）、DNSSEC 与传输加密各管什么、QMIN 严格模式遇不良应答会回退多发细节、多上游并发竞速等工程边界讲清。结论：自建递归不是「DNS 隐身」，而是把「信任一家公司的隐私政策」换成「把可见性拆散到 DNS 层次里」；读者可据此判断要不要在家跑 Unbound，以及何时该选加密转发。"
published: true
---

11 月 14 日 MakeUseOf 有篇标题很长的文章，论点却干脆：作者过去一遇到宣传更隐私的 DNS 提供商就切换，后来发现只要仍由某家公司处理全部 DNS 查询，就只是换了谁持有完整清单。

这句话值得从运维视角展开，因为它把「DNS 隐私」里最常被混在一起的三件事分开了：谁在传输路上能看见、谁替你做递归、以及每一站究竟听到了多少。我核了 Cloudflare、Google 与 Unbound 的官方文档，顺手用一份公开的 Unbound 中文电子书大纲校准了几个工程边界。

## 一、换提供商解决的是「信任对象」，不是「集中持有」

先看两家公共解析器自己怎么写。

Cloudflare 1.1.1.1 的官方承诺：不出售公共解析器用户数据、不用于广告定向；非易失存储里不留源 IP，IPv4 截掉末段、IPv6 截掉后 80 位，截断后的地址与 Public Resolver Logs 都在 25 小时内删除；最多 0.05% 的随机采样包仅用于排障与 DoS 缓解；请四大会计所之一审计并公开报告；与 APNIC 有研究合作但只给匿名数据的有限查询权限。聚合数据（按区域、数据中心统计的域名请求计数等）可以无限期保留。

有个媒体没强调的细节：Cloudflare 明写 resolver 向权威服务器发出的子请求日志里含 `subrequest.queryName`、查询类型、应答码、记录数据等字段 —— 即「对外递归那一跳」同样在日志口径内，只是同样 25 小时内删除。

Google Public DNS 的官方页则写：临时日志是唯一同时保存「设备 IP + DNS 查询」的地方，24–48 小时内删除；DoH 还记 Content-Type 与 Accept 头；为处理安全与滥用可保留超过 48 小时。永久日志是临时日志的抽样，去掉 IP、换成国家/区域/城市级位置，保留域名、请求类型、ASN、时间戳、ECS 前缀长度等。

MakeUseOf 那张对照表因此成立：ISP 解析器、1.1.1.1、8.8.8.8 三者的日志政策确实不同，但留存期内，那一家公司仍能看到你查过的所有站点。加密 DNS（DoH / DoT）把查询从 ISP 眼皮底下挪走，却没有改变「对端是唯一全量持有者」这个结构。

## 二、Unbound 的完整递归：把清单拆散到 DNS 层次里

文章给的第三条路是在家跑 Unbound 做完整递归。按 NLnet Labs 官方定义，Unbound 是开源的 validating、recursive、caching resolver：校验 DNSSEC、缓存应答；既能直接走 DNS 层次解析，也能把选定查询转发给别的解析器 —— 这两种跑法做的事完全不同。

完整递归时没有公共递归商在中间：

1. Unbound 从 DNS 根开始，跟随 referral 一层层往下；
2. 配合 QNAME minimization（QMIN），每一站只给完成这一跳必需的名字标签；
3. 文中那个简化例子：根只被问到 `com`，`.com` 服务器只被问到 `example.com`，只有该域自己的权威服务器才听到完整的 `www.example.com`；
4. TTL 未过期时，重复查询直接由本地缓存回答，不产生任何外发流量。

于是没有任何单一公司拿到全量列表：根、TLD、各权威服务器各看到碎片，完整清单只在你自己的缓存里。Unbound 官方把这点表述为「reduce unnecessary disclosure of query information through QNAME minimisation」。

转发模式的边界必须写死：如果 Unbound 被配成把查询转给某个上游，那个上游收到的仍是完整请求。转发器自己也可以用 QMIN，但它与上游之间那一跳已经把全名交出去了；「装了 Unbound」不等于「摆脱了单一持有者」。

工程上还有两个容易被科普文略过的点。其一，QMIN 是「尽量少给」，不是绝对：实际查询会随缓存与委派方式变化，遇到不合规或坏应答时 Unbound 会回退多发一些标签（QMIN 严格模式撞上不遵循 NXDOMAIN cut 的 CDN 区就是典型）。其二，若给转发器配多个上游，常见实现是并发竞速取最快，不是主备 —— 这既影响隐私边界，也会让基于「只走某一个上游」的过滤策略失效。

## 三、代价：这不是 DNS 隐身

原作者没有把 Unbound 写成银弹，这几条恰好是架构师最该先算的账：

| 代价 | 含义 |
|---|---|
| SNI 仍暴露站点名 | 没有 ECH（且站点也支持）时，即使 DNS 全程加密，ISP 仍能从 TLS 握手读到站点名；Unbound 改变的是「谁处理 DNS」，不是「所有上网痕迹都消失」 |
| 递归查询多为明文 | 完整递归是直接与根/TLD/权威服务器通信，通常没有 DoH/DoT 包裹；ISP 不能再从自己的解析器日志里读，但可以主动抓包 |
| 权威服务器看到你的公网 IP | 用大公共解析器时，权威侧看到的是解析器 IP；自建递归等于拿自己的出口 IP 去问，放弃了群体掩护 |
| 运维归属回到自己 | 缓存、DNSSEC 信任锚、失败回退、日志与排障都由自己承担；文中 Windows 上还遇到 Smart App Control 拦未签名安装包，最后改用 WSL |

作者给的取舍很清楚：担心 ISP 抓 DNS 明文，就把 Unbound 配成加密转发，代价是重新接受「某家提供商能看到完整历史」；不想把全量清单交给任何一家，就用完整递归，代价是上面三条。Pi-hole、OPNsense、pfSense、OpenWrt 都能配 Unbound，但默认各不相同，值得先看路由器/网关到底把查询交给了谁。

顺带把术语边界摆正（这也是那份公开 Unbound 电子书大纲里反复强调的）：存根、缓存、转发、递归是四种角色；DNSSEC 管的是数据完整性与来源认证，DoT/DoH 管的是传输加密与链路隐私，两者不互相替代；本地过滤表（`local-zone` 一类）在递归/转发之前生效，属于另一层。把这些层分开，才不会把「我开了 DoH」误当成「没人知道我查了什么」。

## 四、边界

- 本文依据 MakeUseOf 原文与 Cloudflare / Google / NLnet Labs 官方文档；未安装或实测 Unbound、未抓包验证 QMIN 行为，文中 `www.example.com` 的逐层示例是原文给出的简化说明，实际查询随缓存与委派变化。
- 文中 1.24.2 版本号、WSL 安装经历、各网关默认配置差异均为原作者自述。
- Cloudflare 的 25 小时、0.05%、聚合统计无限期，Google 的 24–48 小时与「安全滥用可延长」均取自两家官方页；政策可能更新，读时以官方页为准。
- 概念框架参考了公开的 Unbound 中文电子书大纲（四种角色、DNSSEC 与传输加密分工、QMIN 严格模式与多上游竞速），未引用其任何本地文件、路径或项目内部细节。
- 加密 DNS 与 ECH 的覆盖范围按原文口径标注；ECH 需要浏览器与站点双方支持。

## 五、结论

这篇文章真正值得记住的是一个结构判断，而非「快去装 Unbound」：只要有一台递归解析器替你跑完全部查询，它就天然持有完整清单。换提供商、开 DoH、挑一家承诺删日志更快的，都是在改善「持有者是谁、留多久」，没有改变「有人持有全部」。

自建完整递归做的事不同 —— 它把可见性按 DNS 层次拆开，让根、TLD、权威各拿到碎片，完整列表只留在自己的缓存里。换来的是明文外发、权威侧看到自家 IP、以及运维责任回到自己手上。

对读者来说，判断顺序可以是：先确认现在是谁在回答你的查询；再想清楚最介意的是 ISP、公共解析器，还是「任何单一公司」；最后才决定要加密转发，还是在家跑一台从根开始问的 Unbound。DNS 隐私没有「全关掉」的开关，只有把信任放在哪一层的选择。

## Sources

- MakeUseOf《I stopped handing my browsing history to Google, Cloudflare, and my ISP, and the fix wasn't another provider》（Afam Onyimadu，2026-11-14）：<https://www.makeuseof.com/unbound-private-dns-without-trusting-another-provider/>
- Cloudflare《1.1.1.1 Public DNS Resolver》隐私承诺：<https://developers.cloudflare.com/1.1.1.1/privacy/public-dns-resolver/>
- Google《Your Privacy | Public DNS》：<https://developers.google.com/speed/public-dns/privacy>
- NLnet Labs《Unbound - About》：<https://nlnetlabs.nl/projects/unbound/about/> ｜ 文档：<https://unbound.docs.nlnetlabs.nl/en/latest/>
- RFC 7816（QNAME minimisation）：<https://www.rfc-editor.org/rfc/rfc7816> ｜ RFC 8020（NXDOMAIN cut）：<https://www.rfc-editor.org/rfc/rfc8020>
- 概念框架参考（公开电子书）：<https://github.com/LeisureLinux/ebook-unbound> ｜ 在线阅读：<https://leisurelinux.github.io/ebook-unbound/>
