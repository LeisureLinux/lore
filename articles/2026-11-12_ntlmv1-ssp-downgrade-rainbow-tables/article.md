---
title: "NTLMv1-SSP 降级破解：一个 1999 年的密码学问题，2026 年还能打穿域控"
date: 2026-11-12
slug: ntlmv1-ssp-downgrade-rainbow-tables
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：hun.io《Cracking downgraded NTLMv1 SSP hashes with rainbow tables》（2026-04-15）全文，含 NTLMv1/DES 计算、SSP 与 ESS 定义、Windows Server 2022 降级步骤、CT1/CT2/CT3 拆分、彩虹表还原 NT hash 与 secretsdump 链 ＋ Microsoft Learn《Network security: LAN Manager authentication level》官方 LmCompatibilityLevel 0–5 对照表与默认值 ＋ Google Cloud / Mandiant《Closing the Door on Net-NTLMv1: Releasing Rainbow Tables to Accelerate Protocol Deprecation》（Nic Losby，2026-01-15，含公开数据集、1999 年 cryptanalysis、2012 DEFCON、2016 Hashcat DES 支持、<600 美元消费级硬件 12 小时内恢复）＋ MS-NLMP 规范与 NTLM/SSP 微软文档条目"
original_date: 2026-04-15
original_url: "https://hunio.org/security/ntlmv1-ssp-cracking/"
description: "本文解读 hun.io 对 NTLMv1-SSP 降级哈希的复现，并用微软与 Mandiant 官方资料校正口径。先澄清术语：NTLMv1-SSP 不是一种独立协议，而是 Responder 对「由 NTLM 安全支持提供者（SSP，一个插入 LSA 的 DLL/认证包）处理 NTLMv1 认证」的显示标签。密码学根因在 1999 年就被分析过：NT hash 是口令 UTF-16LE 的 MD4（16 字节），NTLMv1 把服务器 8 字节 challenge 分别用三段 7 字节 DES 密钥加密，拼成 24 字节响应；三段加密的是同一明文，因此把 challenge 固定成 1122334455667788 就能预计算彩虹表反推密钥。ESS（扩展会话安全）加入客户端 challenge 破坏这个前提，但可在协商中被关掉。文章还原链路：Responder 设静态 challenge 并加 --disable-ess → PetitPotam 强制域控机器账户 DC01$ 发起认证 → 拿到 LM 与 NT 段相同的哈希（说明无客户端 challenge）→ 拆出 CT1/CT2/CT3 → 彩虹表查回三段密钥 → 拼接前两段加 CT3 前两字节还原 NT hash → 用该机器账户哈希做 DCSync。防守口径按微软官方表列全 LmCompatibilityLevel 0–5：0–2 允许 NTLMv1 从而可被降级，3 是最低要求（Send NTLMv2 response only），最强是 5（拒绝 LM 与 NTLM）；注册表位于 HKLM\\System\\CurrentControlSet\\Control\\Lsa\\LmCompatibilityLevel。也写出 Mandiant 2026-01 公开彩虹表的意图：让防守方用不到 600 美元的消费级硬件在 12 小时内演示风险，并提醒 GPO 之外还要监控 Net-NTLMv1 的实际使用（攻击者拿到本地管理权可临时改回脆弱配置再改回去）。边界：本文为防御性解读，不复现实验环境、不提供可直接照抄的攻击脚本，所有命令仅按原文用于说明因果。"
published: true
---

> 一手：hun.io 的复现原文；微软 `LmCompatibilityLevel` 官方文档；Mandiant 彩虹表发布公告
> 说明：本文是防御性解读，不复现实验环境，不提供可直接照抄的攻击脚本；文中命令只用于说明因果链
>
> 这条链路最刺眼的地方不是工具多巧，是它依赖的密码学缺陷1999 年就被分析过。

4 月 15 日 hun.io 发了篇 5 分钟阅读的短文：在 Windows Server 2022 域里，只要还允许 NTLMv1，就能把域控机器账户的认证降级成 NTLMv1，用彩虹表还原出 NT hash，再做 DCSync。原文给了完整命令与输出；本文不复述成操作手册，只把为什么成立、防守该改哪一格讲清楚。

## 一、先把名字拆开：`NTLMv1-SSP` 不是新协议

原文特意花一节解释 SSP（Security Support Provider）：它是插入 Windows 本地安全机构 LSA 的 DLL（也叫认证包），负责实现 Kerberos、NTLM 等认证协议，让系统既能当客户端也能当服务端。其中实现 NTLM 的那个就叫 NTLM SSP。

所以 Responder 抓到的哈希显示为 `NTLMv1-SSP`，含义是「这次 NTLMv1 认证由 NTLM SSP 处理」，不是「冒出了一种叫 SSP 的新哈希格式」。这类标签误读在应急里很常见，值得先正名。

## 二、密码学根因：三段 DES 加密的是同一个明文

按原文与微软 NTLM 相关文档的口径：

1. NT hash = 口令按 UTF-16LE 编码后取 MD4，得到 16 字节；
2. 服务器发 8 字节 challenge；
3. 客户端把 16 字节 NT hash 拆成三段 7 字节 DES 密钥（DES 有效密钥 56 位），各自加密同一个 challenge；
4. 得到三个 8 字节密文 CT1 / CT2 / CT3，拼起来就是 24 字节 NTLMv1 响应。

关键在第 3 步：三段加密的明文相同。于是只要把 challenge 固定成一个已知值（`1122334455667788`），所有可能的密文都能预计算、反查回产生它的密钥 —— 这就是彩虹表能成立的全部理由。原文还点了一个常被忽略的算术细节：第三段密钥实际只有 2 字节有效（16 字节 NT hash 拆成 7+7+2），所以还原完整 NT hash 时取 CT1 + CT2 + CT3 反推结果的前两字节即可。

ESS（Extended Session Security） 本来就是为堵这个洞加的：它在服务器 challenge 之外再引入一个客户端 challenge，响应不再只由已知明文决定，彩虹表失效；NTLMv2 原生就带这层。问题在于 ESS 是协商出来的 —— 客户端若支持标准 NTLMv1，服务端可以在 `NTLMSSP_CHALLENGE` 里表示不支持 ESS，把这个过程「谈掉」。原文 `Why this works` 一节抓包展示的正是：`DC01$` 在 `NEGOTIATE` 里请求 ESS，Responder 用 `--disable-ess` 在 `CHALLENGE` 里不认，最终用标准 NTLMv1 认证；判别信号是 Lan Manager Response 与 NTLM Response 两段完全相同（没有客户端 challenge 参与）。

## 三、链路：从「强制认证」到「域控机器账户的哈希」

原文的因果顺序（本文只做机制说明）：

| 环节 | 作用 |
|---|---|
| Responder 设静态 challenge + `--disable-ess` | 制造「已知明文、无 ESS」的认证服务端 |
| PetitPotam 触发域控发起认证 | 认证方向是反的：DC01$ 是客户端，Responder 是服务端 |
| 捕获 `NTLMv1-SSP` 哈希 | LM 段与 NT 段相同 → 确认降级成功 |
| 拆 CT1/CT2/CT3 → 彩虹表反查 | 三段密钥分别还原 |
| 拼回 NT hash → `secretsdump -just-dc-user krbtgt` | 用机器账户的哈希做 DCSync |

这里最值得防守方盯住的是谁在认证：被发起认证的是域控机器账户 `DC01$`。Mandiant 2026 年 1 月的公告把后果写得更直白：拿到 DC 机器账户的口令哈希后，攻击者可获得 DCSync 权限，进而危及 AD 里任意账户 —— 这是「一次认证降级 → 整个域」的放大点。

## 四、这不是新洞，是「已知洞还没关」

把时间线摆开，会比单看一次复现更有说服力：

| 时间 | 事件 |
|---|---|
| 1999 | 对底层协议的密码分析已公开（Schneier 收录的 MS-CHAP/相关 DES 结构分析） |
| 2012 | DEFCON 20  presentation 使 Net-NTLMv1 的不安全性广为人知 |
| 2016-08 | Hashcat 加入「已知明文破解 DES 密钥」支持，门槛进一步降低 |
| 2026-01-15 | Mandiant / Google Cloud 主动公开完整 Net-NTLMv1 彩虹表数据集，明确目的是「加速协议弃用」：不到 600 美元的消费级硬件、12 小时内恢复密钥，让防守方低成本自证风险 |
| 2026-04-15 | hun.io 在 Windows Server 2022 上复现完整降级链，证明新版 SMB / ESS 并未自动关掉这条路 |

Mandiant 说得很不客气：这个协议「已弃用且公认不安全二十多年」，但顾问在现网里仍持续发现它被使用，原因是惯性与「没有即时风险被演示出来」。所以公开彩虹表本身是防守动作 —— 把「理论上可破」变成「任何人都能在预算内演示」。

## 五、防守：把那个 GPO 值从 0–2 挪到 3 以上

hun.io 与微软官方给的是同一个开关，位于：

```
计算机配置 > Windows 设置 > 安全设置 > 本地策略 > 安全选项 >
网络安全: LAN Manager 身份验证级别
```

对应注册表 `HKLM\System\CurrentControlSet\Control\Lsa\LmCompatibilityLevel`。微软官方 0–5 完整表（这是最容易配错的地方）：

| 值 | 策略 | 客户端发送 | DC 接受 |
|---|---|---|---|
| 0 | Send LM & NTLM responses | LM + NTLM | LM / NTLM / NTLMv2 |
| 1 | Send LM & NTLM – use NTLMv2 session security if negotiated | LM + NTLM | LM / NTLM / NTLMv2 |
| 2 | Send NTLM responses only | NTLMv1 | LM / NTLM / NTLMv2 |
| 3 | Send NTLMv2 responses only | NTLMv2 | LM / NTLM / NTLMv2 |
| 4 | Send NTLMv2 only. Refuse LM | NTLMv2 | NTLM / NTLMv2 |
| 5 | Send NTLMv2 only. Refuse LM & NTLM | NTLMv2 | 仅 NTLMv2 |

读法：0–2 允许 NTLMv1，就是降级链能成立的条件；原文说的「最低设置」是 3（Send NTLMv2 response only），「最强配置」是 5。微软文档也把 3 列为反制措施，并注明 Server 2008 R2 之后的有效默认值已是 3 —— 也就是说，一旦现网出现 0–2，通常意味着被 GPO 显式改弱、或存在遗留系统兼容例外。

Mandiant 给的处置第一句是「Organizations should immediately disable the use of Net-NTLMv1」，并补了一条 GPO 之外的关键提醒：这些是本机配置，攻击者若已拿到本地管理权限，可以临时把配置改成脆弱状态、打完再改回去。因此除了设值，还需要监控与告警 Net-NTLMv1 的实际使用（以及 ESS 被协商掉、静态 challenge 出现这类信号），不能只做一次基线核查就收工。微软文档同样提醒潜在影响：不支持 NTLMv2 的老客户端将无法认证 —— 这往往是组织迟迟不升到 3/5 的真实原因，需要单独盘点而不是硬切。

## 六、事实边界

- 本文为防御性技术解读，未在实验环境复现 Responder / PetitPotam / 彩虹表 / secretsdump 任一环节；文中命令与哈希片段仅引自原文用于说明因果，不构成可执行操作指引。
- 「NTLMv1-SSP 是 SSP 标签而非独立协议」、ESS 可协商掉、LM 与 NT 段相同作为判别信号，均据 hun.io 原文与微软 SSP/MS-NLMP 文档。
- `LmCompatibilityLevel` 0–5 取值、默认值与反制建议以 Microsoft Learn 官方页为准；原文只提 0–2 / 3 / 5，完整表为本文补充。
- 彩虹表数据集、1999/2012/2016 时间线、<600 美元 / 12 小时、DCSync 后果与「临时改配置」提醒取自 Mandiant 2026-01-15 公告。
- 原文测试环境为 Windows Server 2022 域（含域控 10.0.1.40 等实验地址），本文未验证其它 Windows 版本或第三方 SMB 实现的行为；具体版本差异以厂商公告为准。
- 本文不构成对任何真实系统的安全评估或入侵建议。

## 七、结论

这条链路上没有一项是新技术：DES 三段同明文的问题 1999 年就被分析过，ESS 是后来补的协商层，PetitPotam 类强制认证与彩虹表也早已公开。2026 年真正变化的是门槛 —— Mandiant 把彩虹表做成公开数据集，让「不安全」从论文结论变成消费级硬件 12 小时内可演示的事实；而 hun.io 证明这个演示在新版 Windows Server 上仍然有效。

所以该写的结论很朴素：去查 `LmCompatibilityLevel` 是不是被留在 0–2，把它推到 3 以上、能上 5 就上 5，然后开始监控 Net-NTLMv1 的实际使用。 一个 2017 年文档里就写好的 GPO 值，到 2026 年仍然是这条攻击链唯一的终点。

## Sources

- hun.io《Cracking downgraded NTLMv1 SSP hashes with rainbow tables》（2026-04-15）：<https://hunio.org/security/ntlmv1-ssp-cracking/>
- Microsoft Learn《Network security: LAN Manager authentication level》：<https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/security-policy-settings/network-security-lan-manager-authentication-level>
- Google Cloud / Mandiant《Closing the Door on Net-NTLMv1: Releasing Rainbow Tables to Accelerate Protocol Deprecation》（2026-01-15）：<https://cloud.google.com/blog/topics/threat-intelligence/net-ntlmv1-deprecation-rainbow-tables/>
- 微软 MS-NLMP 规范：<https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-nlmp/b38c36ed-2804-4868-a9ff-8dd3182128e4> ｜ SSP 包说明：<https://learn.microsoft.com/en-us/windows/win32/secauthn/ssp-packages-provided-by-microsoft>
