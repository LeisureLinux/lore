---
title: "S2 为什么弃用 Route53 自建 DNS：当记录数变成无限"
date: 2026-11-17
slug: s2-route53-custom-authoritative-dns-server
category: 技术/解读
author: FreeLAMP.com
original_source: "原文：S2.dev 博客《It's always DNS, so why are we running our own?》，作者 Cristian Caciuc，2026-10-16，分类 distsys，URL https://s2.dev/blog/dns-server。全文要点：S2 决定给客户提供无限 basins（basin 是流的顶层命名空间，原本每账户上限 100），每个 basin 是一个子域 my-basin.b.s2.dev，由 CNAME 指向架构中正确的 cell；需要无限 DNS 记录且强一致（创建后立即可解析，避免等缓存 NXDOMAIN 过期）。Route53 当时约 5 UPSERT/s 的 API 限流在恶意 actor 快速创建数万 basin 时打满配额，积压数小时，正常 DNS 更新被卡；GCP Cloud DNS / Cloudflare / Azure DNS 类似。于是自建权威 DNS：Go + miekg/dns（团队是 Rust shop，但为 Spanner/GCP 工具链选 Go），直接对 Cloud Spanner 做实时 SELECT 把 DNS 当数据库的一个 caller；支持 A/AAAA/NS/CNAME/SOA，自己构造响应；单元测试 + Ferret RFC 合规测试（发现于 NSDI 2022 论文 SCALE）+ 上线 smoke test；ACME DNS-01 不自己服务，用 CNAME delegation 甩到单独 Route53 zone。AI 规划会不断加 coalescing/negative caching/throttling/rate limiting/DNS cookies；NXDOMAIN 攻击（随机不存在查询每次都查库）最令其害怕，in-app 防御无效。最终选 Cloudflare DNS Firewall 作 DNS 反向 Proxy：源站只放行 Cloudflare IP；SOA/NS 应答必须返回 Cloudflare IP 而非 LB IP，加 ns-leak-test 防源 IP 泄漏。HA：两个 GKE 集群（不同 region、靠近 Spanner）各多副本在 TCP/UDP LB 后；告警 runbook 与培训是上线关键；delegation chain 复杂（Cloudflare 主区 → delegate basin 子域给 DNS Firewall → GKE，另有 Route53 证书 zone）。TODO：缓存调优、客户端/防火墙/DNS 应用之间优化、DNSSEC。上线数周稳定，客户创建数千 basin 立即可用，commit 多为 CVE 修复/依赖升级/省钱。＋ 在线核对：AWS Route53 限流官方文档显示新口径为 token bucket、每账户 100 changes/s 持续 + 1500 突发、UPSERT 计 2 token、变更按 API 动作聚合；原文注明文档最近改过、限制可能更高。USENIX NSDI 2022 SCALE 论文与 Ferret GitHub 确认工具用形式化语义+符号执行生成区域文件与查询、测过 BIND/PowerDNS/Knot/NSD 等 8 个实现、13000+ 测试 62% 有差异、30 个新 bug（含 BIND 可远程崩溃）。Cloudflare DNS Firewall 官网确认其位于递归 resolver 与权威 NS 之间，提供限流、边缘缓存兜底（源挂了仍答 stale）、隐藏源 IP。"
original_date: 2026-10-16
original_url: "https://s2.dev/blog/dns-server"
description: "解读 S2.dev 为何弃用 Route53 自建权威 DNS 服务器。场景：客户 basin（流的顶层命名空间）要从每账户 100 个放开到无限，每个 basin 是子域 my-basin.b.s2.dev 用 CNAME 指向正确 cell，需要无限 DNS 记录且强一致（创建即可解析，不等缓存 NXDOMAIN 过期）。Route53 当时约 5 UPSERT/s 的 API 限流被打满（恶意 actor 建数万 basin），积压数小时；GCP/Azure/Cloudflare 托管 DNS 类似。自建方案：Go + miekg/dns（团队 Rust shop 但为 Spanner/GCP 生态选 Go），直接查 Cloud Spanner 做实时 SELECT，DNS 变成强一致账户库的新 caller；支持 A/AAAA/NS/CNAME/SOA 并自己构造响应；测试用单测 + Ferret（NSDI 2022 SCALE 工具，测过 8 个实现、13000+ 测试、62% 有差异、30 个新 bug）+ 线上 smoke；ACME DNS-01 用 CNAME delegation 甩到单独 Route53 zone。安全：AI 建议 coalescing/negative caching/throttling/DNS cookies 等一堆防护，NXDOMAIN 攻击（随机不存在查询每次查库）最可怕、in-app 防不住；最终在权威 NS 前放 Cloudflare DNS Firewall 作反向代理，源站只放行 Cloudflare IP，SOA/NS 应答必须返回 Cloudflare IP 并加 ns-leak-test 防源 IP 泄漏。HA：两个异地 GKE 集群多副本在 TCP/UDP LB 后，告警/runbook/培训是重点；delegation 链复杂（Cloudflare 主区→DNS Firewall→GKE，另有 Route53 证书 zone）。现状稳定、客户创建数千 basin 立即可用；TODO 缓存调优、DNSSEC。边界：只讲权威 DNS 非递归解析；Route53 限流数字原文注明已变，AWS 现文档为 token bucket 100 changes/s + 1500 burst、UPSERT 计 2 token；未自建/未压测、未验证其线上稳定性；厂商博客按主张与可核事实分开写。"
published: true
---

S2.dev 这篇博客的标题有点玩笑——「总是 DNS 的锅，那我们为什么不自己跑一个？」但内容很硬：他们把 AWS Route53 换成了自建权威 DNS 服务器，背后是一个被记录数量与一致性逼出来的架构决定。

先厘清一件事：这是权威 DNS（authoritative DNS）的故事，不是递归解析器，也不是「自建 1.1.1.1」。

## 一、为什么 Route53 不够用

S2 的产品里有个叫 basin 的概念：流的顶层命名空间，类似 S3 的 bucket。每个 basin 是一个子域 `my-basin.b.s2.dev`，DNS 记录是一条 CNAME，把客户端路由到架构中正确的 cell。

他们决定把 basin 从「每账户 100 个」放开到无限——那就需要无限条 DNS 记录。而且这些记录要强一致：basin 一创建，地址必须立即可解析，否则客户端就得干等一条被缓存的 NXDOMAIN 过期。

 Route53 本身看起来能承载无限记录，但API 限流卡住了：原文写的是当时约每秒 5 次 UPSERT（作者特意注明「AWS 限流文档最近改过，现在可能更高」）。他们吃过一次亏：一个恶意 actor 快速创建了数万个 basin，打满了整个 Route53 记录配额，产生数小时积压——正常 DNS 更新被卡住，一边在删记录一边在加记录。

批处理？会破坏「立即可用」的目标；而且即使用批处理，「无限」仍然不成立，合法流量也可能撞限。GCP Cloud DNS、Cloudflare、Azure DNS 同样有 API 侧的强限制。结论：自建权威 DNS 服务器。

> 口径提醒：AWS 现在的限流文档已经换成 token bucket 模型——每账户持续每秒 100 次变更、突发 1500，UPSERT 计 2 个 token，按 API 动作聚合。S2 的「5 UPSERT/s」是他们当时的经历，不能直接套到今天。

## 二、自建方案：让 DNS 直接查账户库

需求被压缩成一句话：收到任意 DNS 请求，查一份能装无限记录、且始终最新的 zone map，回一个对应响应。

他们的做法很干脆——不复刻一套数据、不再加一个同步环节，DNS 记录直接来自现有 basin 数据库：对 Cloud Spanner 做一次实时 `SELECT`，把 DNS 变成这个强一致账户库的一个新 caller。

技术选型有个反直觉点：团队是 Rust shop，却用 Go 写了这个 DNS 服务，理由是 Spanner 工具链和 GCP 生态在 Go 侧更成熟。DNS 库选了 miekg/dns，看中文档质量与支持的 RFC 数量。A、AAAA、NS、CNAME、SOA 都要支持，因为用的是库而非现成服务器，响应要自己构造。

正确性测试下了本钱：单测之外，用 Ferret 做 RFC 合规测试，上线后再用真实流量做 smoke test。Ferret 来自 NSDI 2022 的 SCALE 论文——用形式化语义与符号执行自动生成 zone 文件和查询，论文里测了 BIND、PowerDNS、Knot、NSD 等 8 个实现，13000 多个测试文件中 62% 出现实现间差异，找出 30 个新 bug，其中包括 BIND 里一个可被远程利用、能崩掉解析器与权威服务器的严重漏洞。拿这种工具测自写 DNS 服务，是这篇博客里最硬核的一段。

证书环节他们没有硬上：basin 区用通配符证书，ACME DNS-01 挑战不由自己的服务器提供，而是通过 CNAME delegation 甩到一个单独的 Route53 zone——省得改证书续期系统，也避免在自家 DNS 上服务动态 TXT 记录。

## 三、真正吓人的不是写代码，是暴露在公网

他们和 AI 做了几轮设计讨论。设计本身清楚，但 AI 不断往里加东西：coalescing、negative caching、throttling、rate limiting、DNS cookies……对一个直接面对公网的权威 DNS 来说，这些防护并非多余，但堆起来让人越想越怕。

最让他们担心的是 NXDOMAIN 攻击：每一个随机的、不存在的域名查询，都会触发一次全新的数据库查询。他们试过在应用内做防御，但作者的原话大意是——这是最糟糕的 DDoS，真的没什么能挡住。

于是去找「DNS 反向代理防火墙」，符合「无限记录 + DNS 防火墙」要求的只有 Cloudflare 和 Akamai，最后选了 Cloudflare DNS Firewall：自家 DNS 源站只允许 Cloudflare 的已知 IP 访问，典型的「Cloudflare 在前、谁也别想直连源站」部署。Cloudflare 官网对这类产品的定位正是位于递归 resolver 与权威 NS 之间，提供限流、边缘缓存兜底（源站挂了还能用 stale 答案顶一阵）和隐藏源 IP。

一个容易踩的细节：作为权威服务器必须回答 SOA 和 NS 查询，而这些记录指向 nameserver IP。他们特别确保返回的永远是 Cloudflare 的 IP，而不是自己的负载均衡器 IP，并加了 `ns-leak-test` 回归测试防止源 IP 泄漏。

## 四、最终架构与运维账

高可用上，DNS 服务跑在两个不同区域的 GKE 集群里（尽量靠近 Spanner），每个集群多副本，前面挂 TCP 和 UDP 负载均衡器。

可观测性和培训被作者特别点出来：用 Route53 时没人专门监控它、托管服务是别人的 pager；换成自建后，告警、runbook、半夜起来恢复的流程都得自己建。

委托链也变得绕：主域在 Cloudflare 的常规 zone → 把 basin 子域委托给 Cloudflare 的 DNS Firewall（一个 service，不是一个 zone）→ 再连到 GKE；另外还有一个 Route53 zone 专门给证书。作者自嘲「理解整条 delegation chain 挺好笑的」。

上线几周后状态稳定：客户已经能创建数千个 basin 且立即可用于流；提交历史 mostly 是 CVE 修复、依赖升级和省钱。内部 TODO 还有缓存调优、客户端/DNS Firewall/DNS 应用之间的优化，以及 DNSSEC。作者的收尾很妙：「I think we’re now in a place where we can blame DNS in one of our post-incident reviews.」—— 现在终于有资格在某次事故复盘里怪 DNS 了。

## 五、这件事能复用什么

1. 先算清楚瓶颈在哪。 S2 的瓶颈落在托管 DNS 的 API 写入限流上，与 DNS 协议本身或记录容量无关；它和托管 DNS 的 API 写入限流与业务「无限 + 立即可用」要求的冲突。如果你的记录是静态的或低频变更，Route53 之类的托管服务依然省心得多。
2. 强一致需求决定了数据不能复制。 「DNS 直接读账户库」之所以成立，是因为他们接受一次实时 `SELECT` 的代价，换掉一整套同步链路。这是权衡，不是普适最佳实践。
3. 自写协议服务器，要用工具对 RFC 做差分测试。 Ferret 这类工具的存在本身就是提醒：DNS 的边界情况比想象中多，连 BIND 都被测出过可远程崩溃的 bug。
4. 暴露在公网的服务，防护往往比核心逻辑更贵。 让方案真正能落地的，是前面那层 DNS Firewall，以及围绕 SOA/NS 泄漏做的一批细节；那段 Go 代码反而是较容易的部分。
5. 别低估运维账单。 告警、runbook、培训、复杂的委托链——这些在托管服务里是「别人替你操心」的部分，自建后全变成自己的。

## 六、边界

- 原文是厂商博客（S2.dev，2026-10-16），讲的是 S2 自己的选择与经历；「稳定」「数周」等是作者自述，本文未独立验证其线上指标。
- 这是权威 DNS的决策，不是递归解析器、DNS-over-HTTPS 或公共 DNS 的替代方案；别把它读成「大家都该自建 DNS」。
- Route53 限流数字已随 AWS 文档更新而变化，原文也注明；本文把「当时的 5 UPSERT/s」与「现在的 token bucket 口径」分开写，未把两者混用。
- 本文未自建、未压测任何 DNS 服务，也未验证 Cloudflare DNS Firewall 的实际防护效果；相关产品描述来自其官网。
- 文中的「AI 建议加了一堆防护」是作者叙事情节，不代表 AI 工具的普遍行为结论。

## Sources

- S2.dev 博客原文（Cristian Caciuc，2026-10-16）：<https://s2.dev/blog/dns-server>
- AWS Route53 API 限流文档：<https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/throttling-api-requests.html>
- SCALE / Ferret（NSDI 2022）：<https://www.usenix.org/conference/nsdi22/presentation/kakarla> ｜ <https://github.com/dns-groot/Ferret>
- Cloudflare DNS Firewall：<https://www.cloudflare.com/dns/dns-firewall/>
