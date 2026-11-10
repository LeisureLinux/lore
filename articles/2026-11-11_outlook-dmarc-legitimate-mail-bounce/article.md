---
title: "Outlook 误拒商务邮件：DMARC 没公告就成了硬门槛"
date: 2026-11-11
slug: outlook-dmarc-legitimate-mail-bounce
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Computerworld《Microsoft's email security is unexpectedly blocking legitimate business mail》（Taryn Plumb，2026-11-09）＋ Microsoft Support《Fix NDR error 550 5.7.515 in Outlook.com》（2025-05-02，官方高容量发件人规则）＋ Microsoft Learn《Fix NDR error 5.7.23 in Exchange Online》／《Troubleshoot email authentication in Microsoft 365》＋ Microsoft Q&A「SPF VAlidation issue」（2026-11-09，事件号 EX1540236 / AS9031519）＋ Microsoft 365 服务健康事件页（IsDown 镜像）＋ MailRoute / EasyDMARC / dmarkoff / Windows Report / Windows Latest 的社区与厂商复核"
original_date: 2026-11-09
original_url: "https://www.computerworld.com/article/4246562/microsofts-email-security-is-unexpectedly-blocking-legitimate-business-mail.html"
description: "解读 Computerworld 2026-11-09 报道：自 11 月 5 日起，发往 Outlook / Hotmail / Live / MSN 等微软消费者邮箱的正常商务邮件被间歇性退回，NDR 报 550 5.7.1 或 550 5.7.23，提示缺少 SPF/DKIM/DMARC 认证（AS9031519）。微软没有发布政策变更公告、没有 postmaster 通知、没有服务健康条目或博客，只有社区版主称其为「service degradation」正在调查；Q&A 里管理员提到事件号 EX1540236。关键点：微软自 2025 年 5 月起的官方规则只要求「每天向消费者邮箱发送 5000 封以上、且同一 5322.From 域」的高容量发件人补齐 SPF+DKIM+DMARC 并对齐（错误码 550 5.7.515）；而这次被拒的多是小型普通发件人，甚至有域名 SPF/DKIM/DMARC 都正常仍被退回，且同一批邮件有的送达有的退 —— 说明「政策变更」与「bug」可能同时在场。本文按五层拆解：现象与错误码、官方规则与这次的落差、DMARC/SPF/DKIM 三层认证各自管什么、 quietly failing 的危害（发件人看到一堆缩写以为偶发，收件人根本不知道有信、发票/密码重置/预约确认/录用通知丢失）、以及防守方清单（dig +short TXT _dmarc.example.com 自查；补 v=DMARC1; p=none 监控记录；M365 自定义域开 DKIM；别因为退信甩锅 SPF 就重写 SPF；搜日志里的「缺少邮件认证记录」退信，先重发时效性事务邮件；记录完整 NDR 交给微软调查；最终目标仍是 p=reject，并盘点所有替你发信的 CRM/账单/HR/营销平台）。如实标注：没有官方根因公告，部分社区复测显示 11/9 同域名已恢复接收，事件仍在演进；本文不构成配置建议的替代，DNS 变更请以本域实际情况与厂商文档为准。"
published: true
---

> 原文：Taryn Plumb《Microsoft's email security is unexpectedly blocking legitimate business mail》，Computerworld，2026-11-09
> 原文链接：<https://www.computerworld.com/article/4246562/microsofts-email-security-is-unexpectedly-blocking-legitimate-business-mail.html>
>
> 本文依据原文全文、微软官方支持文档与社区/厂商复核逐条标注。

## 一、发生了什么：11 月 5 日起，正常邮件开始被退

自 **2026-11-05** 起，发往微软消费者邮箱 —— **Outlook、Hotmail、Live、MSN** —— 的部分商务邮件开始被退回。发件人收到的 NDR（未送达报告）写着：

- `550 5.7.1` —— 提示消息缺少 SPF/DKIM/DMARC 认证记录（社区报告里带 `AS9031519`）
- `550 5.7.23` —— 提示 SPF 校验失败

社区里一条典型退信是这样的（Computerworld 引用微软社区论坛）：

> 你的邮件无法投递到 `<redacted>@hotmail.com`。hotmail.com 无法确认这封邮件是从受信任位置发出的。

另一个用户说得更具体：「有些邮件正常，有些返回 SPF failed。」**而更让人困惑的是：部分被退的域名，SPF、DKIM、DMARC 都是齐的、能查到的。**

微软方面的公开信息少得反常：

- **没有宣布政策变更**
- **没有 postmaster 通知**
- **没有服务健康条目**
- **没有博客文章**

只有一位微软外部员工版主在社区称其为「**service degradation**（服务降级）」，正在主动调查。Microsoft Q&A 里管理员提到事件号 **EX1540236**，并说 `AS9031519` 没有单独公开的文档定义；微软的 AI 回答也提醒：**别只凭退信里出现 AS9031519 就认定自己的租户在事件范围内**，要去 Service health 查。

Computerworld 引 Dickson Research 的 Frank Dickson 判断：这次**可能是政策变更与 bug 同时在场**。他有一句概括值得原样留下：

> **Requiring every sending domain to prove it is who it says it is makes email safer. Doing it without notice, with an error message that points at the wrong problem, makes a mess.**

（要求每个发信域证明自己是自己，能让邮件更安全；但不打招呼就做、还用一个指向错误问题的报错，就会变成一团乱。）

**「指向错误问题的报错」是整件事最坑的地方**：退信写 SPF 失败，但有人 SPF/DKIM/DMARC 全过；写缺 DMARC，但微软官方规则里 DMARC 只该管高容量发件人。

## 二、落差在哪：官方规则只管 5000 封/天，这次管到了小发件人

微软不是没有 DMARC 规则。**有，而且写得很清楚** —— 见 Microsoft Support《Fix NDR error "550 5.7.515" in Outlook.com》（2025-05-02）：

| 官方规则 | 内容 |
|---|---|
| 适用对象 | 每天向微软消费者邮箱发送 **5000 封及以上**、且所有邮件使用**同一 `5322.From` 域**的发件人 |
| 错误码 | `550 5.7.515 Access denied, sending domain does not meet the required authentication level` |
| 要求 1 | 发布 SPF 与 DKIM，且**两项检查都通过** |
| 要求 2 | 发布 DMARC 记录（官方示例就是 `v=DMARC1; p=none`） |
| 要求 3 | SPF 和/或 DKIM **至少一项与 `5322.From` 域对齐** |

也就是说，**2025 年 5 月至今，官方口径是「大发件人必须补齐，小发件人暂不强制」**。Computerworld 也写了这一点。

而这次被退的恰恰是**小型、普通发件人**：Dickson 点名的画像很具体 —— SMB、非营利组织、学校，以及律所、会计师事务所、诊所这类「域名是多年前有人设好、之后没人碰过」的专业机构。大组织也不轻松：营销与账单平台用的**二级域名、区域域名、子域名**经常漏配 DMARC；原因也很现实 —— **DNS 没有明确 owner，而且大家怕改了会把第三方发的正常邮件弄坏**。

所以这里出现一个很本号的问题：**「规则写了」和「规则实际怎么执行」不是一回事。** 官方规则说 5000 封/天，实际过滤却打到了一天发几十封的小域；官方错误码是 5.7.515，实际退信是 5.7.1 / 5.7.23。**配置 ≠ 生效**，反过来也成立：**没配置 ≠ 不会被强制**。

## 三、先把三层认证拆开（否则退信看不懂）

这三条缩写常被一起念，但各管一段：

| 机制 | 管什么 | 不管什么 |
|---|---|---|
| **SPF** | 发信服务器的 **IP** 是否被该域授权 | 不管邮件头里的 From 是谁 |
| **DKIM** | 用**密码学签名**证明消息没被改、确实属于签名域 | 不管读者看到的 From 域 |
| **DMARC** | 把前两者与**读者实际看到的 `5322.From` 域**做**对齐**检查，并告诉收件方如何处理伪造 | 自己不产生认证，只消费 SPF/DKIM 的结果 |

Dickson 的解释很到位：没有 DMARC，**冒充你的域名很容易**，大量钓鱼与商务邮件欺诈（BEC）就从这里开始。

**「对齐」是关键词**：SPF 过了、DKIM 过了，还可能 DMARC 不过 —— 因为签名域或信封域与 From 域不一致。这也解释了为什么「我记录都齐了还被退」不一定矛盾：可能是第三方平台代发时对齐没做好。但这次事件里，**连记录齐全且对齐的域也被间歇退回**，那就不是配置能解释的了，得算到过滤侧。

## 四、真正的危害：它安静地失败

MailRoute 与 Dickson 都强调同一点 —— **危险不在退信，在不一致**。

- 发件人收到一封「全是缩写的退信」，**以为是偶发故障，翻篇了**；
- 收件人（客户、患者、求职者）**根本不知道有一封信存在**；
- 丢的偏偏是最不该丢的那类：**发票、密码重置、预约确认、录用通知**；
- 结果是客户以为「对方不理我」，而不是「邮件没送到」。

Dickson 原话是这「quietly failing」是邮件营销者的**existential bane**。这跟本号反复写的那条线是同一个：**没报错的系统故障，比报错的更难发现**。这里甚至不是没报错 —— 是**报了错，但错指向了错误的地方**，于是人主动忽略了它。

## 五、防守方现在该做什么（按原文与微软文档整理）

以下按 Computerworld 原文 + MailRoute + 微软官方文档整理，**不是本文的独立建议**；DNS 变更请以本域实际情况为准。

**① 先查有没有 DMARC 记录。** MailRoute 给的自查命令：

```bash
dig +short TXT _dmarc.example.com
```

返回以 `v=DMARC1` 开头＝有记录；**无返回＝没有**。（把 `example.com` 换成自己的域名。）

**② 缺了就补一条最小监控记录：**

```text
v=DMARC1; p=none
```

`p=none` 的意思是：声明这个域使用 DMARC、请收件方发报告，但**对失败不采取行动**。MailRoute 说这能在「不改变其它方如何处理你的邮件」的前提下止住这类退信 —— **前提是 SPF 或 DKIM 与 From 域对齐**。微软官方的 5.7.515 文档里，示例也是这条。

**③ 别因为退信写了 SPF 就重写 SPF。** Dickson 明确说：**Do not rewrite SPF just because the bounce blames it.** 记录本来干净却还被退的，把**完整 NDR** 交给微软，让它进调查流程。

**④ M365 自定义域把 DKIM 打开。** 微软官方文档里，自定义域的 DKIM 需要在 M365 侧配置；很多组织一直没开。

**⑤ 搜日志、先补发。** 在邮件日志、平台的 bounce 报告、helpdesk 工单里搜「缺少邮件认证记录」这类退信条目，**时间范围从 11 月 5 日起**；把**时效性事务邮件优先重发**（密码重置、预约、发票、offer）。每一次拒绝都产生一封退信、退信都有日志 —— 这是好消息。

**⑥ `p=none` 是一垒，不是本垒。** Dickson 说目标是 `p=reject`（让收件方拒绝任何冒充你名字的邮件）。而到那一步之前，必须先**盘点所有替你发信的服务**：CRM、账单系统、HR 平台、营销工具。「大多数组织拿不出这份名单」，他的结论是：**你不知道谁在替你说话，就保护不了这个域。**

## 六、方向没有疑问，问题在 rollout

Dickson 给的行业时间线很清楚：

- **2024-02**：Google 与 Yahoo 开始要求批量发件人做 DMARC；
- **2025-05**：微软跟进（5000 封/天门槛，错误码 5.7.515）；
- **2026-11-05**：这次无公告、不一致、打到小发件人的过滤。

他的判断：**「要求从大发件人开始，然后变成所有人的地板。这次 rollout 搞砸了，但终点没有问题。」** 补一句更狠的：**「没人应该从一封退信里得知一条新规则。」**

**注意这里的边界**：截至 Computerworld 发稿，微软**没有公布根因**。dmarkoff 的复测显示，11 月 7 日同一无 DMARC 域 16/16 被拒，**11 月 9 日 15:09 UTC 同样发送 16/16 被接受**（进垃圾箱，SPF/DKIM 通过、DMARC 为 none）—— 说明它**在波动、可能已部分恢复**。所以「这是政策变更」还是「这是 bug」，目前**不能下结论**，只能说两者都可能有份。

## 七、事实边界

- **本文依据 Computerworld 原文全文 + 微软官方支持/Q&A/服务健康镜像 + 社区与厂商复核**。微软**没有发布根因公告、postmaster 通知或官方博客**；「service degradation」出自社区版主，事件号 `EX1540236` 出自管理员帖，`AS9031519` 无公开文档定义。
- **`550 5.7.515` 规则**（5000 封/天、SPF+DKIM+DMARC+对齐）来自 Microsoft Support 官方文档，与本次退信的 `5.7.1 / 5.7.23` **是不同错误码**，本文不混用。
- **「记录齐全仍被退」**来自 Computerworld 与多家社区报道，本文未自行实测投递。
- **波动/可能恢复**：dmarkoff 11/9 复测是单一测试者的结果，不代表全局已修复；事件仍在演进。
- **自查命令与 `p=none` 记录**是原文引述 MailRoute / 微软文档的做法，本文按报道转述；**DNS 改动请以本域实际情况与厂商文档为准，本文不构成配置或运维建议的替代**。
- 本文只做事件解读与防守方信息整理，不提供任何绕过邮件认证的方法。

## 八、结论

> **这次事件的重点不是「DMARC 又收紧了」，而是「一条没有公告的规则，用一个指错方向的报错，安静地丢掉了别人的发票和录用通知」。**

把三层拆开看：官方规则写在纸上（5000 封/天），实际过滤打到了小发件人，退信指向 SPF 却有人三项全过，而且同一批邮件时通时不通。**配置对不对，和过滤侧怎么执行，是两件事** —— 这跟本号写 Secure Boot、写「配置了 ≠ 生效了」用的是同一把尺子。

方向其实没人反对：**DMARC 终会成为所有发件人的地板**。真正该被记住的是那句：**没人应该从一封退信里得知一条新规则。**

---

## Sources

- Computerworld, Taryn Plumb, *Microsoft's email security is unexpectedly blocking legitimate business mail*（2026-11-09）: <https://www.computerworld.com/article/4246562/microsofts-email-security-is-unexpectedly-blocking-legitimate-business-mail.html>
- Microsoft Support, *Fix NDR error "550 5.7.515" in Outlook.com*（2025-05-02，高容量发件人规则）: <https://support.microsoft.com/en-us/outlook/fix-ndr-error-550-5-7-515-in-outlook-com>
- Microsoft Learn, *Fix NDR error 5.7.23 in Exchange Online* ｜ *Troubleshoot email authentication in Microsoft 365*: <https://learn.microsoft.com/en-us/troubleshoot/exchange/email-delivery/ndr/fix-error-code-5-7-23-in-exchange-online> ｜ <https://learn.microsoft.com/en-us/defender-office-365/email-authentication-troubleshoot>
- Microsoft Q&A, *SPF VAlidation issue*（2026-11-09，`EX1540236` / `AS9031519`）: <https://learn.microsoft.com/en-us/answers/questions/6065440/spf-validation-issue>
- Microsoft 365 服务健康事件镜像（IsDown）: <https://isdown.app/status/microsoft365/incidents/683964-some-users-may-be-intermittently-unable-to-send-email-messages-to-outlook-com-hotmail-com-or-live-com-email-addresses>
- MailRoute / EasyDMARC / dmarkoff（11/7 与 11/9 复测）/ Windows Report / Windows Latest 复核
