---
title: "16 岁少年用 AI 助手攻破微软内部分析库：170 亿行数据、JWT 不验签，赏金 5000 美元"
date: 2026-09-28
slug: microsoft-titan-analytics-jwt-flaw
tags: [Microsoft, Titan Analytics, JWT, alg-none, 认证绕过, ClickHouse, 漏洞赏金, AI助手, Antares, 安全, 译文]
category: 安全/漏洞
author: FreeLAMP.com
original_source: "Tom's Hardware / Rescana"
original_author: "Tom's Hardware（报道）；Rescana（技术分析）"
original_date: 2026-09-28
original_url: "https://www.tomshardware.com/tech-industry/cyber-security/teenager-hacks-open-microsoft-database-with-17-trillion-total-rows-and-25-000-user-accounts-custom-ai-bot-and-lack-of-jwt-token-validation-yields-a-fruitful-trove-earns-usd5-000-bug-bounty"
description: "16 岁研究者 Faav 借 AI 助手 Antares 发现微软内部 Titan Analytics 的 JWT 不验签缺陷（alg:none），可伪造管理员身份执行任意 SQL，触及约 17.3 万亿行、17 个 ClickHouse 库、25,000 用户账号；微软 5 天内部署修复，发放 5,000 美元赏金。"
published: true
---

> 原文：[Tom's Hardware 报道](https://www.tomshardware.com/tech-industry/cyber-security/teenager-hacks-open-microsoft-database-with-17-trillion-total-rows-and-25-000-user-accounts-custom-ai-bot-and-lack-of-jwt-token-validation-yields-a-fruitful-trove-earns-usd5-000-bug-bounty)（2026-09-28）；技术细节另据 [Rescana 的 CVE 分析](https://www.rescana.com/post/critical-jwt-authentication-vulnerability-in-microsoft-titan-analytics-exposed-17-trillion-internal-records-cve-analysis)与研究者原始博客（blog.faav.net，《How I Could've Accessed 17 Trillion Microsoft Records》）。本文为**译文 + 技术解读**。
>
> **来源边界**：Tom's Hardware 正文在抓取中仅返回标题与导语，下文技术细节主要来自 Rescana 对同一事件的分析与研究者公开博客，已逐项标注；不将二手转述伪装成 TH 原文。

## 一句话结论

一名 **16 岁**安全研究者 **Faav**，借助自建 **AI 黑客助手 Antares**，发现微软**内部**分析平台 **Titan Analytics** 的 API **只校验 JWT 里的 claims、不校验签名**——攻击者可构造 **`alg: none`、空签名**的令牌，把 `upn` 伪造成管理员，进而**执行任意 SQL**，理论上可触达约 **17.3 万亿行**内部记录。微软受理后**约 5 天**完成修复，发放 **5,000 美元**赏金。漏洞**仅存在于内部服务**，不影响任何商用/面向客户的产品。

## 技术细节

**目标**：**Microsoft Titan Analytics**——一个托管在 **Azure** 上的微软**内部**分析平台。该服务暴露了一个**公开 API 端点**，并通过一个可访问的 **Swagger** 界面做了文档化。

**根本缺陷：JWT 只验 claims、不验签名**
- 认证依赖 **JSON Web Token（JWT）**。
- 但后端实现**没有对 JWT 签名做密码学校验**，**只检查令牌里的 claims**（tenant ID、audience、application ID、用户身份等）。
- 关键点：服务**接受 `alg: none` 头 + 空签名**的令牌——这是一个**著名的反模式（anti-pattern）**，等于**彻底关闭签名验证**。

**利用链**
- 构造一个 `alg: none` 的 JWT，把 **`upn`（User Principal Name）claim 设为 `admin`**，即可**冒充管理员账号**。
- 后端把这个 claim 映射到**本地用户 ID 1**——而 **ID 1 通常保留给管理员权限**。
- 于是攻击者获得 Titan Analytics 后端的**完整管理权限**，可对底层 **ClickHouse** 数据库**执行任意 SQL 查询**。

**暴露规模**
- 总量约 **17.3 万亿行**，跨 **17 个 ClickHouse 分析数据库**、**9,863 张唯一表**、**30 条活跃 API 路由**。
- 涉及约 **25,000 个用户账号**。

**时间线**
| 时间 | 事件 |
|------|------|
| 2026-08-25 | Faav 用 AI 助手 Antares 发现漏洞 |
| 2026-09-05 | 报告给 **MSRC**，case 编号 **144051** |
| 2026-09-09 | 微软**封堵**脆弱 API 端点（约 4–5 天修复） |
| 2026-09-28 | 事件经 Tom's Hardware / Rescana 公开 |

**影响范围（重要）**
- 受影响的是**内部 Microsoft Titan Analytics 服务**，**截至 2026-09-09 的所有构建/部署**。
- **不存在于任何商用或面向客户的微软产品**中；涉及的 API 端点是组织内部的。

**MITRE ATT&CK 映射**：T1078（Valid Accounts）、T1552（Unsecured Credentials）、T1190（Exploit Public-Facing Application）、T1606（Forge Web Credentials）。

**失陷指标（IoC）**
- 来自**非内部 IP** 对 **`/v2/Query`** 路由的异常访问；
- 后端**接受 `alg: none` + 空签名** 的 JWT。

## 解读

**1.「不验签」是教科书级反模式，但依然反复出现。** `alg: none` /「只信 claims 不信签名」在 JWT 安全里是老问题，理论上人人都知道危险，却仍出现在大厂内部服务里。原因常是：内部服务默认「内网可信」，把认证降级成「解析 token 取字段」，签名校验被省略或写成「可绕过」。

**2. AI 辅助把「发现门槛」压得更低。** 16 岁研究者 + 自建 AI 助手 Antares 的组合，是本仓那条「AI 让攻击性安全工作成本崩塌」主线（Hacktron 攻破 OpenAI、DeepSeek 红队、Enclave 基准）的又一个数据点。真正值钱的不是「AI 会打」，而是「AI 让**不会打的人也能系统性探测**」——包括对 Swagger 文档化的公开端点做自动化尝试。

**3. 内部 ≠ 安全。** 这次没造成实际泄露（研究者负责任披露、微软快速修复、无 APT 利用证据），但暴露了一个结构性事实：**内部服务的攻击面常被低估**——它们往往有公开可达的端点（哪怕需要内网或特定条件），且安全审查弱于产品线。对做内网平台/数据中台的团队，「内部」不能作为豁免密码学校验的理由。

**4. 赏金经济学。** 5,000 美元对「可能触达 17.3 万亿行的管理员级访问」而言并不高——这也侧面说明微软把它定性为**内部服务、无客户数据受影响**的低影响面事件。对研究者，价值更多在公开写作（blog.faav.net）与信誉。

**5. 防御建议（基于原文与安全惯例）**
- **强制校验 JWT 签名**，**拒绝 `alg: none` 与空签名**，**限制可接受算法**为安全默认值；
- 对**所有**认证令牌做严格密码学校验，**不因「内网」而降级**；
- 内部 API 也纳入 **Swagger/OpenAPI 暴露面盘点**，避免「有公开文档 = 易探测」；
- 监控 `/v2/Query` 之类查询路由的**非内部来源访问**。

> 来源边界：Tom's Hardware 报道（标题/导语）+ Rescana 技术分析 + 研究者公开博客。具体行数/表数/时间线以研究者原文与官方披露为准；本文不含任何利用代码。
