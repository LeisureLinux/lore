---
title: "「邮件加密」到底在防谁：一篇厂商科普背后，是四层保护与四个不能同时满足的目标"
date: 2026-11-01
slug: email-encryption-threat-model-dane-mta-sts
tags: [邮件加密, 端到端加密, TLS, STARTTLS, MTA-STS, DANE, DNSSEC, PKI, 证书透明度, SMTP, IMAP, PGP, S/MIME, 零访问加密, ProtonMail, Tuta, Fastmail, 威胁模型, 中间人攻击, 可用性, 侧信道, 邮件安全, 隐私]
category: 安全/科普
author: FreeLAMP.com
original_source: "⭐ 一手核对：Fastmail《Understanding email encryption》（Neil Jenkins，2025-12-17）+ Whitten & Tygar《Why Johnny Can't Encrypt》原文（1999，O’Reilly 版 PDF 全文核对）+ Cloudflare《When DNSSEC goes wrong: how we responded to the .de TLD outage》（2026-05-06）+ RFC 8314 / RFC 7646 / RFC 8767 / RFC 8914"
original_date: 2026-11-01
original_url: "https://www.fastmail.com/blog/email-encryption/"
description: "「邮件加密」听起来只有一件事，实际上是四件：连接到你邮箱服务器的 TLS、服务器之间的传输加密、静态存储加密、以及端到端加密 —— 而它们各自防的是完全不同的威胁，也各有各的代价。本文以 Fastmail 的这篇科普为骨架，但补了三处它没说的东西：① DNSSEC 的可用性风险在 2026 年又验证了一次 —— 5 月 5 日 DENIC 给 .de 域发了错误的 DNSSEC 签名，导致数百万域名返回 SERVFAIL，Cloudflare 用 RFC 7646 负信任锚 + RFC 8767 serve stale 才缓解，这比 Fastmail 引用的 2023 年 Cloudflare 1.1.1.1 事故更严重；② 核对了 1999 年《Why Johnny Can't Encrypt》原文，Fastmail 说的「12 人中只有 4 人」准确 —— 原文结论是「只有三分之一」，而失败的根因不是加密算法，是「公钥模型」和「信任验证」这两个概念没传达给用户；③ 零访问加密的四条边界（新入邮件仍可被截获、部分元数据不加密、只防只读服务器入侵、发件人那里有明文副本）。而全篇最核心的一句判断来自作者自己的诚实承认：这四层保护没有一个能同时满足保密性、可用性和防滥用。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Fastmail：Understanding email encryption](https://www.fastmail.com/blog/email-encryption/)**（Neil Jenkins，首席产品官，**2025-12-17**）
> - ⭐ **[Whitten & Tygar：Why Johnny Can't Encrypt](https://www.cs.berkeley.edu/~tygar/papers/Why_Johnny_Cant_Encrypt/OReilly.pdf)**（1999，**O’Reilly 版全文核对** —— 12 名参与者的逐人结果）
> - ⭐ **[Cloudflare：When DNSSEC goes wrong — the .de TLD outage](https://blog.cloudflare.com/de-tld-outage-dnssec/)**（**2026-05-06**，含时间线、RFC 7646 负信任锚、RFC 8767 serve stale 的实测数据）
> - 规范：[RFC 8314](https://datatracker.ietf.org/doc/html/rfc8314)（Cleartext Considered Obsolete）｜[RFC 7646](https://datatracker.ietf.org/doc/html/rfc7646)（NTA）｜[RFC 8767](https://datatracker.ietf.org/doc/html/rfc8767)（serve stale）｜[RFC 8914](https://datatracker.ietf.org/doc/html/rfc8914)（EDE）
> ⚠️ **本文是**解读**。核心内容来自 Fastmail 的科普，但我补了三处它没覆盖或说得不准的地方 —— 尤其第一处，因为它恰好发生在 Fastmail 发文之后。**

## 一句话结论

**⭐ 而这篇科普最值得注意的，不是它讲了什么，而是它敢讲什么 —— 作者是邮件服务商的产品负责人，却在文章里说：**

> **「Here's the honest truth: if you are a journalist trying to protect a source, or face nation-state adversaries, **you probably shouldn't use email** — use an encrypted messaging app instead.」**

**⭐ 我认为这句话比整篇文章的任何技术细节都值钱 —— 因为一个卖邮箱的公司告诉你「我们的产品不适合这个场景」。**

**⭐ 而更重要的是：它把「邮件加密」这个笼统的说法拆成了四件互不替代、代价各异的事 —— 而它们的共同点是，没有一个能同时满足你要的所有目标。**

## 一、先问威胁模型：你在防谁

**⭐ 而 Fastmail 开篇第一段就做了这件事，我认为这个顺序比后面所有技术细节都重要：**

**⭐ 对大多数人，现实的威胁是这四个：**

| 威胁 | 说明 |
|---|---|
| **账号被盗** | ⭐ **钓鱼或密码复用 → 攻击者拿到你的账号** |
| **误判垃圾邮件** | ⭐ **重要邮件被当成 spam 弄丢** |
| **恶意软件** | ⭐ **通过邮件链接或附件中招** |
| **误删** | ⭐ **人为失误丢失重要数据** |

**⭐ 而「网络窃听」「数据泄露」「设备被偷」这三个，Fastmail 标为「少见但也重要」。**

**⭐ 而对于一小部分人 —— 保护消息来源的记者、在敌对国家的活动者、面对有组织的对手 —— 威胁模型还包括：**

> **「**insider threats at providers** and **legal compulsion by governments**」**

**⭐ 我认为这个分类本身就很有价值 —— 因为它直接决定了后面该选哪一层：**

**⭐ **「账号被盗」是最大的现实威胁，而端到端加密对它的帮助几乎为零** —— 因为攻击者是用**你的凭据**登进来的，**你的私钥就在你的机器上**。**

**⭐ 而「服务商内部人员」和「政府法律强制」，才是零访问加密和端到端加密唯一能真正应对的。**

**—— 换句话说：⭐ 那些「最强」的加密方案，防的恰恰是那些「最少发生」的威胁。**

## 二、⭐⭐ 四层保护，四种代价

**⭐ 而 Fastmail 的框架是这整篇文章最实用的部分 —— 我把它整理成一张表：**

| 层 | 位置 | 防什么 | 代价 |
|---|---|---|---|
| **① 传输加密（客户端↔你的服务商）** | 网络上 | ⭐ **WiFi / ISP / 中间人** | 几乎没有 |
| **② 传输加密（服务器↔服务器）** | 网络上 | ⭐ **中间人** | **可能被降级**（见第四节） |
| **③ 静态加密** | 服务商磁盘 | ⭐ **物理盗窃 /  decommission 硬盘** | **服务商持有密钥** |
| **④ 零访问加密** | 服务商磁盘 | ⭐ **服务商内部人员 / 法律强制** | **⭐ 功能大幅受限** |
| **⑤ 端到端加密** | 全程 | ⭐ **最强内容保护** | **⭐ 实际上不可用（见第六节）** |

**⭐ 而 Fastmail 自己对每一层的描述，我只删减不改写地摆出来：**

### 2.1 第一层：连接到你邮箱服务器的 TLS

> **「This protects you from eavesdroppers on your local WiFi network, your ISP, and anyone monitoring network traffic between you and your email service.」**
>
> **「Fastmail fully supports the latest TLS 1.3 standard. We also use HTTP Strict Transport Security (HSTS) to ensure browsers never try connecting to us without TLS. Similarly, we ensure the ports for unencrypted IMAP/POP/SMTP are closed on our servers, so email apps do not try to connect without encryption (this is why we have always preferred "implicit" TLS over STARTTLS, which is also now the recommendation of the IETF).」**

**⭐ 而 RFC 8314（Cleartext Considered Obsolete）的推荐与之一致：**

> **「Connections to Mail Submission Servers and Mail Access Servers be made using "Implicit TLS" … **in preference to** connecting to the "cleartext" port and negotiating TLS using the STARTTLS command.」**

**⭐ 而这里有个容易被忽略的安全点 —— PKI 与证书透明度（CT）：**

> **「When you connect to Fastmail or Gmail, the server presents a certificate that's been digitally signed by a trusted Certificate Authority (CA) like Let's Encrypt. Your browser or email client checks this signature against its built-in list of trusted CAs. **This prevents attackers from intercepting your connection by pretending to be your email provider — even if they can redirect your traffic, they can't obtain a valid certificate for a domain they don't control.**」**
>
> **「The system was strengthened significantly with the introduction of Certificate Transparency (CT) logs: **public, append-only records of every certificate issued by participating CAs**. Domain owners can monitor these logs to detect if someone fraudulently obtains a certificate for their domain, and **browsers now require certificates to be logged before trusting them**.」**

### 2.2 第二层：服务器之间的传输加密

**⭐ 而这一层的核心机制叫「机会式 TLS」（opportunistic TLS）：**

> **「Server-to-server encryption relies on "opportunistic TLS", meaning servers attempt encryption but fall back to unencrypted delivery if the receiving server doesn't support it. Fastmail has supported this for inbound mail since April 2009 and for outbound mail since January 2010.」**

**⭐ 而它的两个根本局限，Fastmail 说得很直白：**

**① 可被主动攻击者降级：**

> **「The fundamental limitation is that opportunistic TLS can be defeated by active attackers, commonly referred to as a man-in-the-middle (MITM) attack. **A sophisticated adversary positioned between mail servers can strip the STARTTLS command from the initial handshake, forcing an unencrypted connection.**」**

**⭐ 「剥离 STARTTLS 命令」—— 这是个很具体的攻击手法：MITM 站在中间，看到客户端发 STARTTLS 就不回应，服务器以为对方不支持，于是明文传输。**

**② 服务器默认不验证证书：**

> **「Additionally, **servers don't verify certificates by default**. They accept any valid-looking certificate without confirming it actually belongs to the destination server. **This is because verifying the certificate adds no security when an active attacker could just fall back to an unencrypted connection.**」**

**⭐ 我认为这条推理很值得注意 —— 它是一个「因为攻击太彻底所以防御无意义」的自证式循环：**

**⭐ **如果 MITM 能把连接降级成明文，那验证证书也拦不住他 —— 所以服务器干脆不验证了。**

## 三、⭐⭐ MTA-STS 与 DANE：补上那两个漏洞

**⭐ 而这一节是全文技术含量最高的部分 —— 而 Fastmail 的结论相当保守。**

### 3.1 MTA-STS

**⭐ 它的机制：**

> **「MTA-STS (Mail Transfer Agent Strict Transport Security) lets domains declare they support and require STARTTLS encrypted connections, including a valid certificate, when receiving email for addresses at that domain. **Senders can check this policy and must refuse to send mail if they are unable to establish an encrypted connection with a valid certificate for the receiving domain.**」**

**⭐ 而它的部署成本（这决定了它为什么没普及）：**

> **「MTA-STS is reasonably straightforward to deploy: it requires only a DNS record and a policy file hosted over HTTPS. **If something goes wrong, the worst case is that some incoming mail gets delayed or bounced — it cannot affect websites or other uses of the domain.**」**

**⭐ 最后那半句是关键 —— 它解释了 MTA-STS 相对 DANE 最大的优势：坏了只影响邮件，不会影响网站。**

### 3.2 DANE

> **「DANE (DNS-Based Authentication of Named Entities) takes a different approach, publishing TLS certificate information directly in cryptographically-signed DNS records via DNSSEC. **This eliminates dependence on certificate authorities and the "trust on first use" weakness of MTA-STS** — but at significant operational cost.」**

### 3.3 ⭐⭐ 而 Fastmail 拒绝 DANE 的理由 —— 这是全文最值得学的一段

**⭐ Fastmail 先讲了 DNSSEC 的可用性风险，而且说得很具体：**

> **「DNSSEC is not supported by all domains (it depends on the registry for the top-level domain). More importantly, **DNSSEC's deployment complexity significantly increases the likelihood of a serious outage**. Unlike most system failures, **DNSSEC errors are uniquely unforgiving**: when there's a routing problem, you fix it and service is restored immediately, but when there's a DNSSEC problem, **broken records can persist in caches across the internet for hours or days**.」**

**⭐ 而它举的两个例子：**

> **「In October 2023, Cloudflare's 1.1.1.1 resolver — one of the world's most popular DNS services — experienced hours of failures when DNSSEC signatures in their cached root zone expired. In May 2023, New Zealand's .nz country-code TLD triggered a multi-day availability incident during a routine DNSSEC key rollover.」**

**⭐ 而最后是那个明确的技术判断：**

> **「At Fastmail we know **security is not just about confidentiality** (no one else can read your email). **Availability (you can read your email) and integrity (your email cannot be corrupted or modified by others) are just as important.** For this reason, we don't currently consider the confidentiality benefits of DANE over MTA-STS to be worth the trade-off against increased availability risk. **Other major providers such as Google and Yahoo have made similar choices, favouring MTA-STS over DANE.**」**

**⭐ 我把这段翻译成一句话：**

> **⭐ **「没人能读你的邮件」只是三件重要的事之一 —— 另外两件是「你能读到」和「你的邮件不会被篡改」。**

**—— 而 DNSSEC 提升的是「更难伪造证书」，代价却可能是「整个域名解析不了」。**

**⭐ 而这正好呼应了 Fastmail 引用的那句 RFC 8314 的话：**

> **「The recommendations in this memo **do not replace the functionality of, and are not intended as a substitute for, end-to-end encryption of electronic mail.**」**

## 四、⭐⭐⭐ 而这三年里，DNSSEC 的可用性风险又验证了一次 —— 而且更严重

**⭐ 这一节是我要补的第一处 —— 因为 Fastmail 发文于 2025 年 12 月，而它引用的最新例子是 2023 年 5 月。**

**⭐ 而 2026 年 5 月发生了一件事，比它举的两个例子都严重。**

### 4.1 ⭐ 2026-05-05，.de 域挂了

**⭐ Cloudflare 的复盘（2026-05-06）写得非常详细：**

> **「On May 5, 2026, at roughly 19:30 UTC, DENIC, the operator for the `.de` TLD, started publishing **incorrect DNSSEC signatures** for the `.de` zone. Any validating resolver receiving these records was **required by the DNSSEC specification to reject them and return SERVFAIL** to clients, including 1.1.1.1.」**
>
> **「**.de is one of the largest on the Internet.** An outage at this level of the DNS hierarchy has the potential to make **millions of domains unreachable**.」**

**⭐ 而事故扩大的机制很有意思：**

> **「After the immediate spike in SERVFAILs at 19:30 UTC, **it climbed steadily over the following three hours as cached records slowly started expiring**. As each domain's cached records expired and resolvers went back to DENIC for fresh copies, they got back broken signatures and started failing.」**

**—— 也就是说：不是立刻全挂，而是**随着缓存逐个过期，挂了的面越来越大**。**

**⭐ 而 DENIC 自己的说明（Cloudflare 引述）：**

> **「The outage is linked to a **routine, scheduled key rollover**. During this process, **non-validatable signatures were generated and distributed**. As a precautionary measure, **future rollovers have been suspended** until the exact technical causes have been identified.」**

**⭐ 一次「例行的密钥轮换」导致数百万域名不可达。**

### 4.2 ⭐⭐ 而 Cloudflare 的缓解手段，正是 Fastmail 担心的那套

**⭐ 而这一点最值得注意 —— Cloudflare 做的事分两层：**

**① serve stale（RFC 8767）—— 把「还活着」的旧缓存继续发出去：**

> **「But many `.de` records were still sitting in cache from before the incident began. Rather than immediately discarding those and returning SERVFAIL to users, 1.1.1.1 continued serving them past their TTL. **This significantly cushions the impact of an upstream outage, buying time for operators to respond.**」**
>
> **「**Without stale-served responses, the NOERROR rate drops steadily from 19:30 onward.** These represent queries that users received good answers for only because their record was still in cache.」**

**② 负信任锚（RFC 7646）—— 直接把这个域当「未签名」处理：**

> **「An NTA is an explicit exception. It tells the resolver to **treat a specific zone as if it were unsigned**, bypassing validation for names under that zone.」**
>
> **「**Continuing to return SERVFAIL in that situation provides no security value: the failure is already known, public, and being fixed.**」**

**⭐ 而 Cloudflare 部署 NTA 的时间是 22:17 UTC —— 而事故始于 19:30 UTC：**

> **「We rolled out our mitigation at **22:17 UTC**, which marked the end of impact for 1.1.1.1.」**

**⭐ 我把这段时间线整理出来：**

| 时刻 | 事件 |
|---|---|
| **19:30 UTC** | DENIC 开始发布错误的 DNSSEC 签名 |
| 19:30 起三小时 | SERVFAIL 率**随缓存过期持续攀升** |
| **22:17 UTC** | Cloudflare 部署 NTA，**1.1.1.1 的影响结束**（约 **2 小时 47 分钟**） |

**⭐ 而 Cloudflare 的那句内部事故室原话，我认为是全文最精彩的一句：**

> **「*There is no user of 1.1.1.1 resolving a .de name right now who would prefer a SERVFAIL over an unvalidated response*」**
>
> **「现在没有任何一个用 1.1.1.1 解析 .de 域名的人，会更希望收到 SERVFAIL 而不是未经验证的响应。」**

**⭐ 而他们也明确承认了这是「故意绕过 DNSSEC」：**

> **「The decision to bypass DNSSEC is a deliberate tradeoff. **Without DNSSEC validation, `.de` domains become vulnerable to genuine attacks for the duration of the incident.** During incidents like this, we weighed this as acceptable because the signing failure was widespread, publicly confirmed, and affected every validating resolver on the Internet equally.」**

### 4.3 ⭐⭐⭐ 而这对 DANE vs MTA-STS 的争论意味着什么

**⭐ 我认为这一节是本文最值得读者自己判断的地方 —— 因为 Cloudflare 这次的处置，恰好演示了 Fastmail 那个担忧的具体形态：**

**⭐ **注意 Cloudflare 做的不是「DANE 式的证书验证」，而是「NTA —— 干脆不验证」。**

**—— 也就是说，在一次真实的 TLD 级 DNSSEC 故障里，验证链被绕过了，而不是被修复了。**

**⭐ 而 Cloudflare 自己在结尾也承认了这个结构性事实：**

> **「This incident highlights a structural reality of the DNS hierarchy: **when a registry at the TLD level fails, every domain under that TLD is affected simultaneously**, regardless of where it's hosted or which resolver is used. **This isn't unique to DNSSEC**; the same is true if a TLD's nameservers become unreachable. **The hierarchy that makes the global DNS work is also what makes failures at the top propagate downward.**」**
>
> **「There is no simple fix for this. What the industry can do is **respond quickly and consistently** when it happens. **In this incident, resolver operators across the Internet independently applied Negative Trust Anchors within an hour**, restoring resolution while DENIC worked to fix the zone.」**
>
> **「Operational practices, industry communication channels like DNS-OARC, and features like serve stale all reduce the impact, even if they can't eliminate the underlying dependency.」**

**⭐ 而对 Fastmail 那篇文章的读者，我的结论是：**

> **⭐ **Fastmail 选择 MTA-STS 而非 DANE，理由是「可用性风险」—— 而 2026 年 5 月的 .de 事故，是这个理由最有力的一次实地验证。**
> **⭐ **而那场事故还额外揭示了一层：即使你部署了 DANE，真正的故障时运营者做的第一件事往往是「NTA」—— 也就是放弃验证。**

## 五、⭐⭐ 静态加密与零访问加密：两条不同的路

**⭐ 而这一节是 Fastmail 讲得最坦诚的部分。**

### 5.1 静态加密

> **「Encryption at rest protects it while stored on disk. This typically means full-disk encryption using technologies like BitLocker, LUKS, or ZFS dataset encryption, using keys held by the email provider.」**
>
> **「This architecture protects against specific threats. **If someone physically steals a hard drive from a data center, or if decommissioned drives aren't properly wiped, the data remains unreadable.**」**
>
> **「**As the email service holds the keys, legal requests backed by valid court orders can compel providers to decrypt and hand over data.** And **if attackers gain full control of a server, encryption at rest provides no protection because the keys are already loaded.**」**

**⭐ 我注意到 Fastmail 提到自己的做法时用了「加密密钥仅由我们控制」这个措辞 —— 而这正好落在下一段要讨论的争议点上。**

### 5.2 ⭐⭐ 零访问加密的四条边界

**⭐ 而 Fastmail 对 Proton Mail / Tuta 这类零访问加密的分析，我认为是最有价值的部分 —— 因为它没有简单说「更好」或「更差」，而是逐条列清了。**

**⭐ 首先是它保护什么：**

> **「zero-access encryption, where **encryption keys are derived from your password on your device**, meaning **even the provider cannot decrypt** your stored email. **When you log in, your password decrypts the key locally; the server never sees it.**」**
>
> **「It can provide real protection against insider attacks, data breaches, and limit the data handed over in response to court orders.」**

**⭐ 然后是它**不**保护什么 —— 而这一段我认为每个考虑零访问加密的人都应该读：**

**① 新邮件仍会被截获**

> **「**New mail can still be intercepted.** Unless the email is end-to-end encrypted, the provider **will have access to the unencrypted version before encrypting it** with the user's public key. **An interception court order or rogue employee could still take a copy at this point.**」**

**⭐ ② 不是所有数据都被加密**

> **「**Not all data is encrypted.** Email addresses, timestamps, and in Proton Mail's case, **subject lines**, stay unencrypted. **Who you're talking to, when, how often, and the summary of what it's about is often more important than the contents of the email itself.**」**

**⭐ 我认为这一条最容易被低估 —— 「你在跟谁通信、什么时候、多频繁」这个元数据，往往比正文更重要。**

**③ 只防只读的服务器入侵**

> **「**Only protects against read-only server compromise.** Most people access their email through the browser. The code that decrypts the email is therefore **loaded on demand from the provider's server** — if the server is compromised, **the code can be modified to capture your password**.」**

**⭐ 而这一条是「零访问」这个概念的一个根本矛盾：**

**—— 浏览器访问意味着「解密代码在服务商的服务器上」，而服务商声称「我们看不到你的数据」。这两句话只有在「服务商被攻破」的前提下才都成立。**

**④ 别处还有明文副本**

> **「**An unencrypted copy exists elsewhere.** Even if your copy is encrypted, **the senders likely retain a fully readable copy of every message you receive.**」**

**⭐ 这一点我想强调 —— 因为它说明了一个常被忽略的事实：**

> **⭐ **端到端加密保护的是「传输与存储」，不是「通信内容的生命周期」。你收到的每封信，发件人的邮箱里都有一份明文。**

### 5.3 ⭐ 而零访问加密的功能代价

**⭐ Fastmail 列了四条：**

| 代价 | 说明 |
|---|---|
| **密码丢了就数据丢了** | ⭐ **「Forget your password without a recovery phrase, and your email is gone forever. **There's no "reset password" in the traditional sense.**」** |
| **搜索能力受限** | ⭐ **服务端看不到内容 → 无法索引；客户端搜索要**把全部邮件下载到每台设备**（几十 GB 的邮箱往往不现实）** |
| **标准邮件客户端不能用** | ⭐ **「Zero-access encryption prevents the provider directly offering standard IMAP or JMAP protocols. This also makes **migrating to another provider difficult — it's the ultimate vendor lock-in.**」** |
| **客服支持受限** | ⭐ **「Because the provider cannot access your mail even with your permission, many issues become impossible to help with.」** |

**⭐ 而「忘了密码 = 数据永久丢失」这一条，我认为是最需要被认真对待的：**

**—— 因为 Fastmail 自己也说：** 「**Many years of experience have taught us that people forget or lose their password all the time. Even sophisticated users who swear it would never happen to them have found themselves locked out.**」**

## 六、⭐⭐⭐ 端到端加密：为什么它「一直存在却没人用」

**⭐ 而这一节是全文最核心的部分 —— 而 Fastmail 的分析非常到位。**

**⭐ 首先是历史：**

> **「True end-to-end encryption, where only the sender and recipient can read the message, **has existed for email since the 1990s through S/MIME and OpenPGP**. Yet **neither has achieved meaningful consumer adoption despite decades of availability**.」**

### 6.1 ⭐⭐ 而 PGP 的失败，根源在 1999 年那篇论文

**⭐ Fastmail 的引用：**

> **「The seminal 1999 study "Why Johnny Can't Encrypt" found that **only 4 of 12 participants** could properly encrypt email with PGP **within 90 minutes**. Follow-up studies in **2006 and 2019** found users still struggling with "finding and verifying other people's public encryption keys." **Even PGP inventor Phil Zimmermann had difficulty decrypting an email in 2015 due to version incompatibility.**」**

**⭐ 我去核对了那篇论文的原文（O’Reilly 版 PDF），想确认这个数字 —— 而原文的结论比「4/12」更具体：**

**⭐ 论文摘要：**

> **「The user test demonstrated that **when our test participants were given 90 minutes in which to sign and encrypt a message using PGP 5.0, the majority of them were unable to do so successfully**.」**

**⭐ 而结论段的原文：**

> **「**Our 12 test participants were generally educated and experienced at using email, yet only one-third of them were able to use PGP 5.0 to correctly sign and encrypt an email message when given 90 minutes in which to do so.**」**

**⭐ 所以 Fastmail 的「4 of 12」是准确的 —— 原文说「三分之一」，而逐人数据是：**

> **「**Four participants (P6, P8, P10, and P12) eventually managed to send correctly encrypted email to the team members**（P3 sent a correctly encrypted email to the campaign manager, but not to the whole team）。」**

**⭐ 而我认为比数字更有价值的是原文对**失败原因**的分析 —— 因为它证明这不是「算法太难」：**

**① 不是不会加密 —— 是不懂「公钥模型」：**

> **「Among the 11 participants who figured out how to encrypt, **failure to understand the public key model was widespread**. **Seven participants (P1, P2, P7, P8, P9, P10, and P11) used only their own public keys to encrypt email to the team members.**」**

**⭐ 而这一条最讽刺 —— P5 的做法是：**

> **「One of the 11 (P5) **so completely misunderstood the model that he generated key pairs for each team member rather than for himself**, and then attempted to send the secret in an email encrypted with the five public keys he had generated.」**

**② 有三个人把秘密**明文**发了出去：**

> **「**Three of the twelve test participants (P4, P9, and P11) accidentally emailed the secret to the team members without encryption.** Two of the three (P9 and P11) realized immediately that they had done so, but **P4 appeared to believe that the security was supposed to be transparent to him and that the encryption had taken place.**」**

**⭐ 而这一条最值得记 —— P4 用的是自己刚生成的公钥，所以「系统告诉他加密成功了」，但内容根本没加密。**

**③ 而「用户界面误导」的证据也很有说服力：**

> **「The quill pen icon, which is not very keylike about it, **may even lead them to think that, along with the key objects that they use to encrypt, they also have quill pen objects that they use to sign.**」**
>
> **「**Signature verification is not represented visually**, which is a shame because it would be easy for people to overlook it altogether.」**

**⭐ 我把这三点归纳一下 —— 它们解释了为什么「加密能力都在，但就是没人用」：**

> **⭐⭐ **失败的根源不是密码学，是「用户没被教会公钥这个模型」。**
> **⭐ 而 PGP 的界面还 actively 误导 —— 图标选错、把「验证签名」藏在「解密」按钮里、用户以为自己加密了其实没有。**

**⭐ 而这正好呼应了论文自己的结论：**

> **「it is clear that there is a need to **communicate an accurate conceptual model of the security to the user as quickly as possible**. **The smaller and simpler that conceptual model, the more plausible it will be that we can succeed in doing so.**」**

### 6.2 ⭐⭐ 而更根本的障碍：密钥分发与轮换

**⭐ 而 Fastmail 的分析点出了那个「原理上就无解」的问题：**

> **「A fundamental challenge for any end-to-end system is **key distribution and rotation**. To send an end-to-end encrypted message to someone, you first need to **obtain their public key (and be absolutely sure it's theirs!)**. **There is no infrastructure for doing this at the moment**, let alone for rotating keys regularly in accordance with cryptographic best practice. **Without key rotation, a compromised key or password means all previously intercepted email can be decrypted.**」**

**⭐ 我把这一段拆成三个层次：**

| 层次 | 问题 | 现状 |
|---|---|---|
| **① 获取** | ⭐ **「拿到对方的公钥」** | 没有基础设施 |
| **② 确认** | ⭐ **「并绝对确定那是他的」** | 没有基础设施 |
| **③ 轮换** | ⭐ **「按密码学最佳实践定期轮换」** | 没有基础设施 |

**⭐ 而第三个层次的后果最严重：「没有轮换 → 密钥或密码泄露 → 之前所有被截获的邮件都能解」** —— 也就是说，**端到端加密的长期安全性完全依赖轮换，而轮换恰恰是最缺基础设施的那一环。**

### 6.3 ⭐⭐ 而与 Signal / WhatsApp 的对比，揭示了「联邦架构」的根本困境

**⭐ 这一段我认为是全文最有洞察力的一段：**

> **「Contrast all this with Signal or WhatsApp, where encryption works automatically **because a single organisation controls the full software stack** rather than using open protocols. They generate keys automatically when you install the app, **discover contacts through phone numbers**, and update security protocols universally. **Email's federated architecture — where any client can talk to any server — makes this unified approach impossible.**」**

**⭐ 我把这段的结构提炼出来：**

| | Signal / WhatsApp | 邮件 |
|---|---|---|
| **软件栈** | ⭐ **单一组织全控** | **任何客户端 ↔ 任何服务器** |
| **密钥生成** | ⭐ **装应用时自动** | 用户手动 |
| **联系人发现** | ⭐ **通过电话号码** | ⭐ **没有任何对应机制** |
| **协议升级** | ⭐ **统一推送** | **各服务器各自实现** |

**⭐ 而关键在最后一句 —— 「联邦架构让这种统一做法变得不可能」。**

**⭐ 我认为这一条其实点出了一个更深的矛盾：**

> **⭐ **邮件的联邦性正是它「能用」的���因 —— 任何客户端都能连任何服务器，这正是开放互联网的价值所在。**
> **⭐ **而端到端加密需要「一个统一管全部的实体」—— 这与联邦性直接冲突。**
> **⭐ **换句话说：⭐ 邮件做不到 Signal 的样子，不是工程师不够好，而是**这两件事本质上互斥**。**

### 6.4 ⭐⭐ 而 E2EE 与邮件的功能需求也直接冲突

**⭐ Fastmail 列了四条：**

| 冲突 | 说明 |
|---|---|
| **服务端搜索** | ⭐ **服务器读不了内容 → 无法搜索** —— 而「只是保存一份可搜索的归档本身就与安全最佳实践相悖」** |
| **钓鱼检测与恶意软件扫描** | ⭐ **「**两个最大的安全风险！**」需要检查邮件内容** |
| **多设备访问** | ⭐ **需要跨设备同步私钥 —— 而这是一个安全风险** |
| **⭐ 邮件头** | ⭐ **「email headers including To, From, and Date **cannot be encrypted without breaking email's basic functionality**」** |

**⭐ 而最后那一条是结构性的 —— 因为邮件头正是 5.2 节里说的「未加密元数据」。**

**⭐ 而密碼学家 Bruce Schneier 的总结被引用的那句，我认为是全文最好的一句总结：**

> **「The things we want out of e-mail, and an e-mail system, are **not readily compatible with encryption**.」**
>
> **「我们想要邮件提供的那些东西，和一个邮件系统，**与加密并不容易兼容**。」**

## 七、⭐⭐ 隐私与反滥用：那个无法两全的权衡

**⭐ 而这一节是全文最「诚实」的部分 —— 它讲的是一个服务商每天都在做的真实取舍。**

**⭐ Fastmail 的表述：**

> **「There's an inherent tension between strong privacy protections and the ability to combat abuse. **Spam filters, phishing detection, and malware scanning all require reading email content**, or at least work more effectively when they can. **A provider that truly cannot see your messages cannot protect you as effectively from threats within them.**」**
>
> **「With server-side content inspection, providers can identify phishing attempts by analysing links and sender patterns. They can quarantine malware before it reaches your inbox. They can detect account compromise by recognising unusual behaviour patterns. **These protective capabilities are reduced or eliminated with end-to-end encryption.**」**

**⭐ 而我在想一个更尖锐的问题 —— 这不只是「隐私 vs 安全」，而是三个目标的三角：**

```
            保密性
           （服务商读不了）
              ▲
             ╱ ╲
            ╱   ╲
    可用性 ◄─────► 完整性
  （你能读到）   （邮件不会被篡改）
```

**⭐ 而 Fastmail 明确说了后两个同样重要：**

> **「**Availability** (you can read your email) and **integrity** (your email cannot be corrupted or modified by others) are just as important.」**

**⭐ 而这一点在第四节的 .de 事故里得到了完美印证 —— 那场事故里被牺牲的正是「可用性」，而 Cloudflare 最后放弃了「完整性」来换回它。**

**⭐ 我认为这才是全文真正的主题：**

> **⭐⭐ **「邮件加密」不是一个可以「打开」的开关，而是一组互斥的目标之间的取舍。**
> **⭐ **而任何一方的宣传都倾向于只讲自己那一个目标。**

## 八、⭐⭐ Fastmail 自己的最终立场

**⭐ 而结尾这一段，我觉得是全文最诚实的地方：**

> **「For highly sensitive communications, dedicated messaging apps like Signal offer much stronger guarantees than any email solution can provide. For everyday email, **transport encryption combined with encryption at rest provides meaningful protection against the most likely threats** while preserving the searchability, spam filtering, and convenience that make email useful.」**
>
> **「Here's the honest truth: **if you are a journalist trying to protect a source, or face nation-state adversaries, you probably shouldn't use email — use an encrypted messaging app instead.** But for the vast majority of communications, modern email security offers substantial protection while maintaining the features that make email indispensable.」**

**⭐ 而他们讲自己公司的定位时，也用了同样的诚实：**

> **「Fastmail has been doing email for over 25 years. We know that **email is your electronic memory** and keeping your messages accessible, private and secure are our top priorities.」**
>
> **「We keep your email accessible by concentrating on **rock-solid reliability**, with full multi-data center redundancy, and a lightning-fast interface with powerful search.」**

**⭐ 注意这里的排序 —— 「accessible（可访问）」被放在「private（私密）」前面，而且用了「rock-solid reliability」这种完全非安全词汇。**

## 九、⭐⭐ 我的评价

### 9.1 ⭐⭐⭐ 而这篇文章最值得学的，是它的「威胁模型优先」结构

**⭐ 我想先说这篇文章在方法上做对了什么 —— 因为这一点比它讲的任何技术都更重要：**

**⭐ **它开篇不谈任何加密技术，而是先问「你在防谁」。**

**⭐ 而这个顺序带来一个直接后果 —— 很多看起来「显然应该开」的选项被排除了：**

| 威胁 | 首选手段 | 端到端加密有用吗 |
|---|---|---|
| **账号被盗（最大现实威胁）** | 强认证 + 异地登录提醒 | ⭐ **没用** —— 私钥就在被攻破的机器上 |
| **误判垃圾邮件 / 恶意软件** | 服务端内容检查 | ⭐ **反而有害** —— 会关掉防护 |
| **物理盗窃硬盘** | 静态加密 | ⭐ 部分有用 |
| **服务商内部人员 / 法律强制** | 零访问加密 | ⭐ **这才有用** |

**⭐ 而这直接推出一个反直觉的结论：**

> **⭐⭐ **那个「最强」的选项，防的恰恰是那些「最少发生」的威胁。**
> **⭐ **而对大多数人最可能遇到的威胁，端到端加密提供的保护**约等于零**。**

**⭐ 我认为这才是「加密宣传」最大的问题 —— 它从不先问你防谁。**

### 9.2 ⭐⭐ 而「零访问加密的四条边界」值得单独拿出来说

**⭐ 因为我认为这是本文最容易被跳过、也最该被读的部分。**

**⭐ 把它和第三层的「静态加密」对照着看：**

| | **静态加密（服务商持钥）** | **零访问加密（用户密码派生）** |
|---|---|---|
| **防物理盗窃** | ✅ | ✅ |
| **防服务商内部人员** | ❌ | ✅ |
| **防法律强制** | ❌ | ✅（部分） |
| **⭐ 防只读服务器入侵** | ❌ | ⚠️ **浏览器场景下不完全成立** |
| **⭐ 新邮件的中间态** | ❌ | ⚠️ **服务商仍能看到未加密的原始邮件** |
| **⭐ 元数据** | ❌ | ❠️ **收件人、地址、时间戳（Proton 还有主题）仍是明文** |
| **⭐ 发件人那边的副本** | — | ⚠️ **明文** |
| **忘记密码** | ⭐ 可重置 | ⭐ **永久丢数据** |
| **服务端搜索** | ✅ | ❌ |
| **标准客户端 / 迁移** | ✅ | ⭐ **无法迁移 —— 终极锁定** |

**⭐ 我认为最反直觉的是第三行和第四行：**

**—— 「零访问」听起来是「连服务商都读不到」，但在浏览器访问的场景下，**解密代码本身就在服务商的服务器上**，服务商可以改它来偷你的密码。**

**⭐ 而这是 2026 年最现实的攻击场景 —— 因为绝大多数人就是用浏览器看邮件的。**

### 9.3 ⭐⭐ 而 2026-05 的 .de 事故，给了 DANE vs MTA-STS 一个实地答案

**⭐ 我把这个补上，是因为它恰好发生在 Fastmail 发文之后，而 Fastmail 引用的最新例子是 2023 年 5 月。**

**⭐ 我想强调的是这次事故的三个性质：**

**① 触发原因是「例行的密钥轮换」** —— **不是攻击，不是配置错误。**

**② 影响是 TLD 级的** —— **`.de` 之下所有域名同时受影响，不管托管在哪、用哪个解析器。**

**③ 而运营者的实际处置是「NTA」** —— **也就是绕过验证，而不是修复验证链。**

**⭐ 而 Cloudflare 自己给出了那个结构性结论：**

> **「**The hierarchy that makes the global DNS work is also what makes failures at the top propagate downward.**」**
>
> **「让全球 DNS 运转的那个层级结构，也是让顶层故障向下传播的原因。」**

**⭐ 所以我对 Fastmail 那个判断的评价是：**

> **⭐⭐ **Fastmail 选择 MTA-STS 而非 DANE，理由是可用性风险。**
> **⭐ **而 2026 年 5 月的 .de 事故，是这个理由最硬的一次实地验证 —— 因为它同时证明了「DNSSEC 故障能有多大」和「真出事时运营者会做什么」。**

### 9.4 ⭐⭐ 而最后一件事：这篇科普为什么值得写

**⭐ 我想用一个观察收尾：**

**⭐ Fastmail 是邮件服务商。他们的商业模式建立在「用户信任我们能安全地保管邮件」这件事上。**

**⭐ 而这篇文章的核心内容，实际上是在说：**

> **⭐⭐ **「我们在很多方面确实保护你，但在最敏感的那个场景下，**我们建议你别用我们**。」**

**⭐ 我认为这才是可信度的基础 —— 而不是「我们的加密有多强」。**

**⭐ 而这也回答了第六节那个问题：** **为什么端到端加密在邮件里没能普及？**

**⭐ —— 不完全是技术问题，也不完全是可用性问题。**

**⭐ **是「最强的保护」和「最重要的商业利益」在结构上不兼容：**

**—— 服务商的商业模式要求它「能读你的邮件」（为了搜索、为了反滥用、为了客服），而端到端加密要求它「不能读你的邮件」。**

**⭐ 而 1999 年那篇论文之所以重要，不是因为它证明了 PGP 不好用 —— 而是因为它证明了**27 年后，依然没有人能把这个矛盾解决**。**

## Sources

- ⭐ 一手：[Fastmail — Understanding email encryption](https://www.fastmail.com/blog/email-encryption/)（Neil Jenkins，2025-12-17）
- ⭐ 一手（全文核对）：[Whitten & Tygar — Why Johnny Can't Encrypt: A Usability Evaluation of PGP 5.0](https://www.cs.berkeley.edu/~tygar/papers/Why_Johnny_Cant_Encrypt/OReilly.pdf)（1999；结论段原文「only one-third of them were able to …」，以及逐人结果 P1–P12）
- ⭐ 一手：[Cloudflare — When DNSSEC goes wrong: how we responded to the .de TLD outage](https://blog.cloudflare.com/de-tld-outage-dnssec/)（2026-05-06；19:30 UTC 事故开始、22:17 UTC 部署 NTA、RFC 7646 / RFC 8767 / RFC 8914 EDE 33）
- 一手：[DENIC 关于 .de 事故的说明](https://blog.denic.de/en/technical-issue-with-de-domains-resolved/)（经 Cloudflare 引述：「routine, scheduled key rollover … non-validatable signatures were generated」）
- 规范：[RFC 8314](https://datatracker.ietf.org/doc/html/rfc8314)（Cleartext Considered Obsolete）｜[RFC 7646](https://datatracker.ietf.org/doc/html/rfc7646)（Negative Trust Anchors）｜[RFC 8767](https://datatracker.ietf.org/doc/html/rfc8767)（serve stale）｜[RFC 8914](https://datatracker.ietf.org/doc/html/rfc8914)（Extended DNS Errors）｜[RFC 7672](https://datatracker.ietf.org/doc/html/rfc7672)（SMTP DANE）
- 相关：[Wikipedia — Email encryption](https://en.wikipedia.org/wiki/Email_encryption)（2006 与 2019 两项后续研究的出处）
- 本号此前：TLS 信任库（2026-08-01）、GoAhead 三个 TLS 漏洞（2026-10-27）、为什么我又写 PGP（2026-10-16）

---

（说明：所有引号内内容与数据均来自上述一手材料；**第四节的 .de 事故为笔者补充的实证材料**（Fastmail 发文于 2025-12，其引用的最新 DNSSEC 例子是 2023 年）；**第九节的分析与评价为笔者观点**。）
