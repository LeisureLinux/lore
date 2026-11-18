---
title: "Infisical：AD 时代结束了吗？机器身份的边界正在从目录转向联邦"
date: 2026-11-16
slug: infisical-active-directory-machine-identity
category: 技术/解读
author: FreeLAMP.com
original_source: "原文：Infisical 博客《The Active Directory Era Is Finally Over》，2026-11-13，https://infisical.com/blog/active-directory-machine-identity （web_fetch 取得全文，含 llms.txt 索引）；作者自述曾长期维护 AD 目录，开篇引语是自己编的。核心论点分三段：Visibility and attestation（AD 诞生于人工加入长生命周期物理机的时代，现代云里测试库/K8s pod/CI runner 短生命周期，靠 admin token 自动入域等于把权威外包，统一目录只剩纸面）、Scope（AD 时代身份边界尽量大，SQL Server 用 Windows auth 把 perimeter 撑大；如今每个 API key / DB string / token 都是一个微边界，zero trust 让机器间互认次数暴涨，Notion token 泄漏可在里面翻到更多凭据，云的泄漏凭据可从任意笔记本使用；.env 明文与硬编码仍然普遍）、The new paradigm（identity federation：OIDC 让 AWS 为 EC2 签 token 访问 Azure PostgreSQL，Entra 联邦凭据信任 EC2 workload；brokering：凭据放在 Infisical 这类 secrets manager，机器向 broker 认证、拿到运行时注入的凭据，形成 meta-perimeter；三者对应 AD 曾回答的三个问题：有哪些身份、谁背书、在哪里有效）。例子含公开 Lambda 策略 iam:* 可给任意攻击者提 superadmin、K8s pod service account token、Azure IMDS 发 OAuth token。厂商主张明确：broker 由 Infisical 这类工具承担。＋ 一手对照：Microsoft Learn 官方文档（gMSA 240 字节随机密码、OS 托管；sMSA 单服务器；Windows Server 2025 dMSA 把认证绑定设备身份、自动轮换密钥、禁用原服务账号密码以防 kerberoasting；dMSA 有迁移前置条件，如 SD 修改后至少两个票证生命周期/14 天，建议四个/28 天，且不能从 gMSA 迁到 dMSA；Entra 官方建议本地服务优先 gMSA）＋ Infisical 自身文档（machine identity 按权限而非按机器计数、短期 token、Universal Auth / AWS IAM / Kubernetes / Azure / GCP 等多种认证方法、service token 已弃用）＋ Infisical 同站 2026-10-05《Machine Identity Attestation for Bare Metal and Virtualised Systems》的 TPM / EK 硬件根信任线索"
original_date: 2026-11-13
original_url: "https://infisical.com/blog/active-directory-machine-identity"
description: "解读 Infisical 的厂商观点文《The Active Directory Era Is Finally Over》。先定边界：「AD 时代结束」是作者论点，不是行业事实；微软在 AD 体系内持续加固机器身份 —— gMSA 用 240 字节随机密码由 OS 托管，Windows Server 2025 的 dMSA 把服务账号认证绑定设备身份、自动轮换密钥、禁用原账号密码以对抗 kerberoasting，Entra 官方仍建议本地服务优先 gMSA。文章按原文三段展开：① 可见性与 attestation —— AD 诞生时机器是人工登记的长生命周期物理机，如今 K8s pod、EC2、测试数据库、CI runner 由开发者随时创建销毁，自动入域常用 admin token（甚至硬编码），等于没人真能背书每台机器；作者直言即便把每个 pod 都同步进 AD 也是 security theater，目录在纸面上统一却无权威。② 边界变化 —— AD 追求尽量大的身份边界（SQL Server 选 Windows auth 就是这个逻辑），现在每个 API key / 连接串 / token 都是一个微边界；零信任让机器互认暴涨，Notion token 泄漏后攻击者还能翻到更多凭据，云上泄漏凭据可从任意笔记本使用；文中公开 Lambda 配 iam:* 的例子说明机器身份失控的后果。③ 新范式 —— OIDC 联邦（AWS 为 EC2 签 token 访问 Azure PostgreSQL，Entra 联邦凭据信任该 workload）与凭据代理（凭据存 secrets manager，机器向 broker 认证、按权限拿短期凭据并在运行时注入，形成 meta-perimeter）；对应 AD 曾回答的三问：有哪些身份、谁背书、在哪有效。也写清厂商主张：broker 位置明确指向 Infisical 自家产品；其 docs 里 machine identity 按权限而非按机器计数、service token 已弃用；并补 TPM/EK 硬件根信任作为裸机/虚拟化的另一条路。边界：本文为解读而非背书，未实测任何产品；gMSA/dMSA 的版本、迁移窗口与限制按微软官方文档；原文的极端表述与具体客户例子按作者自述标注。"
published: true
---

11 月 13 日，Infisical 发了篇标题很硬的博客：《The Active Directory Era Is Finally Over》。先说边界：这是厂商观点文，「AD 时代结束」是作者的论点，不是行业一致结论。更准确的说法是 —— 机器身份的权威来源与有效边界，正在从「一本统一目录」转向「联邦 + 代理」。

而且微软自己也在 AD 体系内加固机器身份：gMSA 用 240 字节随机密码、由 OS 托管；Windows Server 2025 引入的 dMSA 按微软官方文档的说法「Authentication for dMSA is linked to the device identity」—— 把认证绑定设备身份，密钥自动轮换、原账号密码被禁用，专门用来防 kerberoasting；Entra 官方仍建议本地服务优先用 gMSA。所以「AD 完了」与「AD 在演进」是两件同时发生的事。

## 一、原文的问题意识：AD 回答的三个问题还成立吗

作者承认 AD 架构其实很朴素：LDAP 目录存身份 + Kerberos 实现认证，包一层不错的用户体验和持续更新。它统一回答三个问题：

| 问题 | AD 的答案 |
|---|---|
| 有哪些身份？ | 目录记录每个用户与机器 |
| 谁为身份背书？ | 域控制器基于管理员凭据批准认证 |
| 身份在哪儿有效？ | AD 域架构映射公司基础设施 |

安全策略如果答不出这三问就无从谈起 —— 自动发证书（AD CS）、批量组策略，全都依赖目录准确。作者当年花很多时间维护这份目录，因为下游一切都指着它。

问题在于：现代云架构里，把每个身份收进同一本目录几乎不可能。AD 有一整套生态 —— 安全产品、密码轮换、同步插件 —— 能让它现代化，但改不了上一个时代的架构选择。作者的判断很直接：AD 是新的大型机——当年很棒，今天没人会从零选它；又因为太深而替不掉。

## 二、机器身份为什么最难

原文的核心论证在「机器怎么进域」这件事上：

1. 目录里创建一个对象（machine account）；
2. 更新 DNS、签发证书（前提是开了 AD CS autoenrollment）；
3. 签发 Kerberos ticket，机器才能声明身份；
4. 机器登录时向 DC 认证，DC 因为目录里有它而信任 —— 但它得先被放进目录。

AD 诞生时，「先放进去」意味着人工添加：物理服务器送到办公室、装进机房、管理员登记。今天这套完全不成立：开发者随手创建和销毁测试数据库、K8s 集群、CI runner，没有人能知道每个 EC2 实例、PostgreSQL 数据库或 CI runner 的存在。

现代 AD 实现的做法是下放权威：拿一个 admin token（有时还是硬编码的）自动把新身份加进域。作者认为这等于否定了原本的意义 —— 管理员批准的前提是「人能说出每台被信任的设备是什么」，而现在既没人做得到，系统却默认批准短生命周期的云资源。AD 是为人工批准长生命周期基础设施设计的，如今却常被用来自动批准短生命周期云资源。

所以作者那句最刺眼的话是：就算你把每个测试库和 K8s pod 都自动化同步进 AD，那也是 security theater —— 目录在纸面上统一了，却没有权威。

对照微软官方文档能看得更清楚：AD 体系自己也在补这一课 —— gMSA 让 OS 托管 240 字节随机密码；dMSA 更进一步，用 Credential Guard 把认证绑定到设备身份，自动轮换密钥、禁用原账号密码，防的是传统服务账号最典型的 kerberoasting。dMSA 的迁移还有明确前置条件：修改安全描述符后至少等两个票证生命周期（14 天），官方建议四个（28 天），且不能从 gMSA 直接迁到 dMSA。这说明微软也承认「服务账号绑设备」是必要方向 —— 只是实现仍在 AD 框架内。

## 三、边界变了：从「大围墙」到「无数小围墙」

AD 时代的理想是身份边界尽量大：目录越完整，权威性越强。例子是 SQL Server 既支持 Windows 认证（AD 身份）也支持 SQL 认证（用户名密码），AD 管理员会选 Windows auth，就是为了把边界撑大。目录外的叫「shadow identity」—— 能用、但没被身份管理统计到。

如今正相反：每个 API key、数据库连接串、auth token 都是一个独立边界，因为它是只代表某个服务的凭据。GitHub 自动化要 PAT 或私钥，根本不认目录身份。零信任架构又让机器之间不断互认，凭据数量和边界数量一起暴涨。

理论上线索小了、爆炸半径也小：偷了 Notion session token 就该只能访问 Notion。实际上攻击者可能在 Notion 里翻到更多凭据，横向扩大；而云时代防火墙与物理边界也消失了 —— 泄漏的凭据可以从任何人的笔记本上使用。原文还举了个反面案例：某人发现一个公开暴露的 Lambda，其策略是 `iam:*`，等于可以让任意攻击者把自己加成 superadmin。

这也解释了为什么「给人类用 SSO、教团队安全处理明文机器凭据」这种常见回应不够：大量团队仍把敏感凭据明文堆在 `.env` 或硬编码在配置里。AD 对这些问题基本无能为力。

## 四、新范式：联邦 + 代理

原文给了两条主线，都不是「再建一本更大的目录」：

1. 身份联邦（identity federation）：一个平台信任另一个平台对 worklaod 的背书。三大云都支持。用 OIDC，AWS 可以为某个 EC2 实例签 token，去访问 Azure 里的 PostgreSQL；Entra 的 federated credentials 原生支持这种用法，信任该 EC2 workload。这里的假设是：机器一创建就能自助拿到身份，且身份范围很窄 —— 和 K8s 的 service account token、Azure IMDS 自动为机器签 OAuth token 是同一个思路。

2. 凭据代理（brokering）：凭据不落在机器手里，而是放进 secrets manager；机器先向 broker 证明身份，broker 按权限把运行时需要的凭据注入给它。作者把这种关系称为围绕所有微边界的 meta-perimeter。

两者合起来，正好重新回答 AD 当年那三问：有哪些身份（谁在认证、做了什么）、谁背书（workload 来自哪里、为什么可信，不靠人逐个批准）、在哪有效（key / token / 连接串天然自带边界）。

必须点明厂商立场：这个 broker 位置被明确指向 Infisical 自家产品。其文档里的 machine identity 按权限集而非按机器计数 —— 多台机器权限相同就共用一个身份（类似多个 EC2 共担一个 IAM role），用 Auth method（Universal Auth / AWS IAM / Kubernetes / Azure / GCP）换短期 token；旧的 service token 已标弃用。同站另一篇文章则给出裸机与虚拟化的硬件根信任路径：TPM 里烧录的 endorsement key（EK）作 attestation 链的根 —— 说明「机器身份」不只是云上 OIDC 的话题。

## 五、边界与判断

- 这是一篇厂商观点文，不是行业调查报告；「AD 时代结束」是作者论点，本文不替它确认。原文开头那句怀旧引语是作者自己编的，也照实标注。
- 微软官方文档显示 AD 机器身份仍在演进（gMSA、dMSA、Credential Guard），「AD 原地不动」不是事实；原文对 AD 的描述更像「不再适合作为唯一统一目录」。
- 原文的 Lambda `iam:*` 例子与会议轶事是作者自述，本文未独立核实。
- 未实测 Infisical 或任何竞品；产品能力描述依据其官方博客与文档，属厂商自述。
- dMSA 的可用版本、迁移窗口与限制按 Microsoft Learn 官方文档；具体环境是否可用需自行验证。
- 原文提到的 K8s pod token、Azure IMDS、OIDC 联邦都是公开标准与产品能力，不构成本文独立测评。

## 六、结论

把厂商立场剥掉，这篇文章提出的问题是成立的：当机器身份由代码按秒创建和销毁时，「由人批准、写进一本目录」的权威模型就跟不上了。AD 当年回答的那三个问题仍然必须回答，但答案正在变成「平台联邦背书 + broker 按权限发短期凭据」，而不是「所有东西都进 LDAP」。

与此同时，微软的 gMSA / dMSA 说明另一个方向也在推进 —— 把 AD 自己的机器身份做扎实。两者并不互斥：企业的现实大概是人用目录、机器各依其平台，中间靠联邦与代理对齐。至于这本目录最终是慢慢退居人类身份系统，还是继续作为机器身份的根，取决于 dMSA 这类绑定设备身份的机制能不能跟得上云的速度。

## Sources

- Infisical《The Active Directory Era Is Finally Over》（2026-11-13）：<https://infisical.com/blog/active-directory-machine-identity>
- Infisical machine identities 文档：<https://infisical.com/docs/documentation/platform/identities/machine-identities> ｜ 身份总览：<https://infisical.com/docs/documentation/platform/identities/overview>
- Infisical《Machine Identity Attestation for Bare Metal and Virtualised Systems》（2026-10-05）：<https://infisical.com/blog/machine-identity-attestation-bare-metal>
- Microsoft Learn：dMSA 概览 <https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/delegated-managed-service-accounts/delegated-managed-service-accounts-overview> ｜ 服务账号总览 <https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-service-accounts> ｜ gMSA 安全指南 <https://learn.microsoft.com/en-us/entra/architecture/service-accounts-group-managed>
