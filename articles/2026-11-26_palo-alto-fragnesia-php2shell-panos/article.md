---
title: "Palo Alto 防火墙被 Fragnesia 打穿：web shell 到 root"
date: 2026-11-26
slug: palo-alto-fragnesia-php2shell-panos
category: 技术/解读
author: FreeLAMP.com
original_source: "CSO Online 报道（Gyana Swain，2026-11-26）＋ 一手核对 Palo Alto 官方公告 PAN-SA-2026-0015（2026-11-25）、CVE-2026-109618 PHP2Shell 公告、Zellic 的 Fragnesia 披露与 Dream Security 攻击链报告。"
description: "解读 Palo Alto Networks 确认的攻击链：攻击者利用 PHP2Shell（CVE-2026-109618/109619，CVSS 4.0 9.2）在PAN-OS 管理界面拿 web shell，再用 Fragnesia（CVE-2026-46300，Linux 内核本地提权）提权 root，隧道进内网窃取凭证、私钥、网络拓扑。内核漏洞 5 月 13 日由 Zellic 的 William Bowling 用 V12 AI 审计 agent 发现并公开 PoC（含 Metasploit 模块），Fedora 次日就修，PAN-OS 拖了 195 天才在 11-25 的 PAN-SA-2026-0015 修复（覆盖 10.2–12.2 全分支），但公告标为 Informational、不给 CVSS。讲清补丁链、为何只打 PHP2Shell 不算根治、Check Point 的类似遭遇，以及 CISO 应把安全设备当面向互联网的特权服务器来评估。"
published: true
---

11 月 25 日，Palo Alto Networks 在安全公告 **PAN-SA-2026-0015** 中确认：攻击者利用 Linux 内核漏洞 **Fragnesia（CVE-2026-46300）**，在暴露于互联网的 PAN-OS 管理界面上，通过 PHP2Shell 漏洞拿下防火墙的 root 权限。CSO Online 11 月 26 日报道了这件事。

一个刺眼的时间差：**Linux 内核 5 月就修好的漏洞，PAN-OS 拖了 195 天**。

## 一、攻击链：从 web shell 到 root

这条链分两步，都是已公开的漏洞：

1. **PHP2Shell（CVE-2026-109618 / 109619）**：PAN-OS 管理 Web 界面背后 PHP 运行时的两个严重漏洞，CVSS 4.0 **9.2**。Palo Alto 在 10 月 25–29 日之间发布了修复，公告覆盖 PA 系列、VM 系列防火墙和 Panorama，明确写着「已观察到在野利用」；
2. **Fragnesia（CVE-2026-46300）**：Linux 内核的本地提权漏洞，允许本地已认证的**低权限攻击者提权到 root**。10 月下旬，Dream Security 的研究者报告攻击者把两者串起来：先用 PHP2Shell 以 web 服务账号执行代码，再用内核漏洞提权到 root。

拿到 root 之后呢？据 Dream 的报告：攻击者**隧道进入内部网络，窃取凭证、私钥和网络拓扑数据**——防火墙从"防护者"变成了"据点"。

Palo Alto 在公告里说，所有观察到的攻击都针对「管理界面暴露在互联网上」的设备——而这正是它的最佳实践明确反对的配置。

## 二、195 天的补丁时差

Fragnesia 本身不是新漏洞：

- **2026-05-13**：Zellic 研究员 William Bowling 披露该漏洞，附带 PoC 和上游内核补丁。有意思的是，他是借助 Zellic 的 **V12 AI 审计 agent** 发现它的；
- **次日**：Fedora 就发布了修复内核；
- **2026-11-25**：Palo Alto 才在 PAN-SA-2026-0015 里把修复带到 PAN-OS，覆盖 10.2 到 12.2 的所有受支持分支（10.2.7-h41、11.1.4-h40、12.1.4-h15 等一长串 hotfix 及后续版本）。

**195 天**。而且此时公开的 PoC 里已经有 **Metasploit 模块**。

独立 DFIR 分析师 Rahul Karne 的评论很直接：设备厂商维护跨多种硬件型号的定制内核，有一定延迟是正常的，但"当利用代码已经公开时，195 天太长了"。他认为客户应该在一周内知道自己是否受影响、大约 30 天内拿到修复。「防火墙拿到安全修复的速度，不应该比它保护的服务器还慢。」

## 三、"Informational" 争议：只打 PHP2Shell 够不够

Palo Alto 把这份公告标为 **Informational（信息性）**，没有给 CVSS 分数。它的逻辑是：

- 已知的唯一利用路径，要求攻击者**先利用 PHP2Shell**；
- 如果你已经装了 CVE-2026-109618 公告里的修复版本，你就受保护了；
- 管理界面限制在可信内网 IP 的设备，风险显著降低，建议"下次维护窗口"升级即可；
- 管理界面（或带 management profile 的数据面接口）能从互联网访问的，**立即升级**并限制访问来源。

IDC 的 Duncan Brown 认为这种"打断攻击链"的做法在链式漏洞里是可以接受的：「只打一个能有效切断链条的补丁是可以接受的。理想情况下所有漏洞都应尽早修复，但很多情况下这不现实。」

Karne 则抓住了关键词——**"known"（已知）**。他说，把 PHP2Shell 打上补丁是合理的短期措施，但它挡住的是"已知的入口"，并没有修复内核漏洞本身：Fragnesia 的公开利用代码在手，设备上**任何**别的代码执行漏洞都能让这个内核 bug 重新变得可用。

Gartner 的 Niyati Daftary 说得更重：CISO 应该把这件事当作**对安全设备信任模型的弱点**，而不只是补丁问题。「一台跑着 Linux、PHP 和其他第三方组件的防火墙，必须用和任何面向互联网的特权服务器一样的严谨程度来评估。像『Informational』这样的厂商标签，在漏洞可以串起来打到 root 时，绝不应该盖过企业的风险分析。」

她还提醒：**在攻击窗口内暴露过的设备，光打 hotfix 不等于重建信任**——要审查管理访问、轮换凭证和证书、猎杀持久化，在无法排除 root 被攻陷时，从已知良好的镜像重建设备。

Palo Alto 对被问及"为什么内核修复花了六个月、Panorama 是否受影响"，表示"除了公告内容外没有更多信息可分享"。

## 四、防火墙成为据点：不是孤例

Palo Alto 不是唯一被这样打穿的厂商。11 月，**Check Point** 说"几十家"客户在攻击者把 PHP2Shell 和 Gaia OS 的一个提权漏洞串起来、接管网关并部署擦除器（wiper）后受影响。

两起事件指向同一个趋势：**边界设备本身就是高价值目标**。它们跑着通用操作系统和第三方组件（Linux、PHP），管理界面面向互联网，一旦被拿下就是进入内网的完美跳板。

## 五、对企业的实际建议

- **管理界面绝不要暴露在互联网**——这是所有厂商的最佳实践，也是这两起事件里攻击者的共同入口；
- 已打 PHP2Shell 补丁的设备，在下次维护窗口也应升级到含内核修复的版本；
- 对暴露期内可能被碰过的设备，按"可能已被 root"处理：轮换凭证/证书、检查持久化、必要时重建；
- 把防火墙、VPN、网关这类设备纳入和普通服务器一样的漏洞管理与严谨评估，别被厂商的风险标签带偏。

## 参考资料

- CSO Online 原文：https://www.csoonline.com/article/4253600/palo-alto-confirms-fragnesia-exploitation-against-firewalls-in-php2shell-attacks.html
- Palo Alto 官方公告 PAN-SA-2026-0015：https://security.paloaltonetworks.com/PAN-SA-2026-0015
- PHP2Shell 公告 CVE-2026-109618：https://security.paloaltonetworks.com/CVE-2026-109618
- Zellic Fragnesia PoC：https://github.com/v12-security/pocs/tree/main/fragnesia
