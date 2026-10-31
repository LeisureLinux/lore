---
title: "攻击者的工具箱里装着 Claude Code、DeepSeek 和 Kimi：一次把 PHP2Shell 打到域控的 AI 辅助攻击"
date: 2026-10-30
slug: php2shell-ai-assisted-attack-roots-25-servers
tags: [PHP2Shell, Fragnesia, CVE-2026-109618, CVE-2026-109619, CVE-2026-46300, AI辅助攻击, ClaudeCode, DeepSeek, Kimi, FOFA, PaloAltoNetworks, PAN-OS, ActiveDirectory, LDAP, 横向移动, 国家支持, 中国, 归因, 事件响应, 凭据喷洒]
category: 安全/事件分析
author: FreeLAMP.com
original_source: "⭐ 一手核对：Dream Security《Chained PHP2Shell Exploit Roots 25 Servers, including US Government Servers》（2026-10-29）+ The Hacker News《PHP2Shell Attack Roots 25 Servers, Breaches U.S. Government-Affiliated Network》（Ravie Lakshmanan，2026-10-28）+ Flare 报道"
original_date: 2026-10-30
original_url: "https://thehackernews.com/2026/10/php2shell-attack-roots-25-servers.html"
description: "Dream Security 捕获了一次真实的在野攻击：攻击者把 PHP2Shell（自研非公开版本）与内核提权 CVE-2026-46300（Fragnesia）串成单请求利用链，用 FOFA 从 19000 台暴露的 PAN-OS 筛到 240 台，批量 root 了 24 台 —— 其中 22 台只植入 103 字节 webshell 停着不动；随后专攻 2 台有价值的，建立 8 端口反向 SSH 隧道进入内网，root 后 90 分钟内拿下防火墙管理服务器，解密 LDAP 服务账号密码，对 Active Directory 发起用户枚举、密码喷洒与后门账号创建尝试。而 THN 报道补上了一个关键细节：攻击基础设施里安装了 Anthropic 的 Claude Code，并配置了 FOFA 的 API key 以及一个名为 aiscan 的 AI 驱动攻防平台（挂 DeepSeek 与 Kimi 的 LLM）；近 40 个脚本的代码结构、注释风格与一致性都指向 AI 辅助开发。本文梳理完整攻击链、版本画像机制、防御分层表，并讨论「AI 辅助攻击」这个信号该如何解读 —— 以及为什么「22 台停放」比「25 台被 root」更值得防守方警惕。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Dream Security：Chained PHP2Shell Exploit Roots 25 Servers, including US Government Servers](https://dreamgroup.com/blog/chained-php2shell-exploit-roots-25-servers)**（2026-10-29，含完整攻击链、版本画像表、十步时间线、攻击路径图）
> - **[The Hacker News：PHP2Shell Attack Roots 25 Servers, Breaches U.S. Government-Affiliated Network](https://thehackernews.com/2026/10/php2shell-attack-roots-25-servers.html)**（Ravie Lakshmanan，**2026-10-28**，含 **AI 辅助工具链的证据**与 Dream 的国家背景归因引述）
> - **[Flare 报道](https://thehackernews.com/2026/10/php2shell-attack-roots-25-servers.html)**（经 THN 引述，含 XSS 论坛研究者对 PoC 可用性的评价）
> - 背景：本号此前的 PHP2Shell 系列（2026-10-21 根因 / 10-23 ASLR 绕过 / 10-27 一周实测）
> ⚠️ **本文为**解读**。**只做防守方视角的事件分析，不转载可运行的利用代码。**

## 一句话结论

**⭐ 而这一篇最值得记的，是 THN 报道里那句几乎被淹没的话：**

> **「The links to AI-assisted tooling stem from evidence pointing to **the installation of Anthropic's Claude Code in the attack infrastructure**, along with the presence of **API keys for FOFA** and an **AI-powered offensive security platform called aiscan** configured with large language models (LLMs) from **DeepSeek and Kimi**.」**

**⭐ 换句话说：这次攻击的「工具箱」里，装着 Claude Code、DeepSeek 和 Kimi。**

**⭐ 而我认为这条信息的价值不在于「AI 又被用来做坏事了」这种泛泛的惊讶，而在于一个更具体的问题：**

> **当攻击基础设施里出现 AI 工具时，防守方该怎么读这个信号？**

## 一、事件轮廓

### 1.1 关键事实

| | |
|---|---|
| **发现方** | **Dream Security**（以色列公司） |
| **发现时间** | **2026-10-25** |
| **公开** | **2026-10-29**（Dream 报告）；**2026-10-28**（THN 报道） |
| **受影响资产** | ⭐ **PAN-OS 防火墙与管理服务器**（未点名厂商） |
| **地理** | ⭐ **美国、日本、台湾、韩国** |
| **被 root 的设备** | **24 台**（批量）+ 1 台（管理服务器）= **25 台** |
| **其中美国政府关联环境** | ⭐ **3 台** |
| **利用链** | **PHP2Shell（CVE-2026-109618 / 109619，CVSS 9.2）+ Fragnesia（CVE-2026-46300，CVSS 7.8）** |
| **目标行业** | ⭐ **「特定大型厂商的防火墙软件」**（厂商名未披露） |

**⭐ 而 Dream 报告里有一句对「谁做的」的判断很值得注意：**

> **「On October 25, Dream researchers uncovered artifacts of what appeared to be a **Chinese AI-assisted campaign** that rooted 25 servers, including systems in a US government-affiliated environment.」**

**⭐ 而 THN 引述了 Dream 的更完整表述：**

> **「Since [the] U.S., Japan, Taiwan, and South Korea are the four primary strategic adversaries and intelligence targets for Chinese state-aligned cyber operations in the Pacific theater, **this indicates potential nation-state adversary efforts**.」**

**⭐ 我要谨慎对待这个归因 —— 理由在第七节。**

### 1.2 时间线

| 日期 | 事件 |
|---|---|
| **10-08** | 攻击者准备：获取 PAN-OS 固件、**解密固件**、提取 PHP 库、构建内存画像 |
| **10-08** | ⭐ **Stage 1：全球发现** —— FOFA 识别约 **19,000 台**暴露管理界面的 PAN-OS |
| — | Stage 2：存活检测 → 约 **5,000 台** |
| — | Stage 3：地理 + 版本过滤 → **240 台** |
| — | Stage 4：批量利用 → **24 台 root** |
| **10-23 18:14 UTC** | 第一台被 root，随后崩溃（疑因约 900MB 利用流量），再未上线 |
| — | ⭐ Stage 5：**22 台「停放」** —— 只留 webshell |
| **10-24 10:09 UTC** | ⭐ 另起专门活动，攻破第二台 |
| **10-24 11:35 UTC** | ⭐ root 后 **90 分钟内**拿下防火墙管理服务器 |
| **10-24 当天** | 从管理服务器发起 AD 攻击 |
| **10-25** | Dream 发现攻击痕迹 |
| **10-27** | ⭐ **CISA 将 CVE-2026-46300 加入 KEV，限期 10-31** |
| **10-28** | THN 报道（含 AI 工具链证据） |
| **10-29** | Dream 完整报告；Palo Alto Networks Unit 42 独立验证并发布修复版本 |

## 二、⭐⭐⭐ AI 辅助的证据链：这是本篇最该被讨论的部分

**⭐ 我把 THN 报道里的原话完整列出，因为这是全文最关键的一段：**

> **「The links to AI-assisted tooling stem from evidence pointing to **the installation of Anthropic's Claude Code in the attack infrastructure**, along with the presence of **API keys for FOFA** and an **AI-powered offensive security platform called aiscan** configured with large language models (LLMs) from **DeepSeek and Kimi**.」**
>
> **「What's more, the code structure, commenting style, and consistency across **nearly 40 scripts** suggest the use of AI to augment the development process.」**

**⭐ 我把这三类证据分开看，因为它们的证明力不同：**

| 证据类型 | 具体内容 | 证明力 |
|---|---|---|
| **⭐ 基础设施里的工具** | **安装了 Claude Code** | ⭐ **强** —— 这是硬事实：攻击者的机器上装了它 |
| **⭐ API 凭据** | **FOFA 的 API key**（资产搜索引擎的付费 API） | ⭐ **强** —— 能大规模自动化的直接证据 |
| **⭐ AI 攻防平台** | **名为 `aiscan` 的平台，挂 DeepSeek 与 Kimi 的 LLM** | ⭐ **强** —— 一个专门配置的 AI 攻击平台 |
| **代码特征** | ⭐ **近 40 个脚本的「代码结构、注释风格、一致性」** | ⚠️ **中** —— 是主观判断，但样本量不小 |

**⭐ 我认为第四项值得多说一句 —— 因为「代码风格的一致性」是一个有意思的取证方法：**

**—— 40 个脚本，如果风格高度一致（同样的注释习惯、同样的错误处理模式、同样的命名），那要么是同一个人写的，要么是**同一套 AI 辅助流程**写的。**

**⭐ 而对攻击者来说，这其实是个「暴露面」：** **AI 辅助开发会提高代码质量的一致性，而一致性本身就是一种指纹。**

**⭐ 我认为这一点对防守方（和情报分析方）是有实际价值的 —— 它意味着「代码风格分析」在归因中可能比以往更有用。**

### 2.1 ⭐ 而「Claude Code 在攻击基础设施里」这一条，需要仔细读

**⭐ 我想强调它的精确含义，避免过度解读：**

| | |
|---|---|
| **它**说明** | 攻击者（或其背后的人）**在攻击基础设施里部署了 Claude Code** |
| **它**不说明** | Claude Code 本身是攻击工具 |
| **它**不说明** | Claude 是这次攻击的「作者」 |

**⭐ 而我认为更可能的解读是：**

**—— Claude Code 是一个「**通用开发代理**」。** **它能读代码库、写脚本、跑测试。** **攻击者用它来加速那 40 个脚本的开发，是极其自然的用法。**

**⭐ 而 aiscan 那个东西更有意思 —— 「AI 驱动的攻防平台」意味着这不只是一次性的辅助，而是**把 AI 接进了攻击流程本身**。**

**⭐ 我认为这里有一个值得深究的问题，但目前证据不足：**

**—— 40 个脚本里，有多少是 AI 写的？有多少是人写的、AI 改的？**
**—— 「代码风格一致」是「AI 写的」的证据，还是「AI 统一改写过的」的证据？**

**⭐ 这两个解释对防守启示的含义完全不同**，而公开材料目前无法区分。**

## 三、⭐⭐ 攻击链：从 19000 台到域控

**⭐ 这一节我压缩了技术细节（完整版在 Fragnesia 那篇里），只保留对理解「形状」必需的部分。**

### 3.1 漏斗

```
19,000 台  FOFA 发现的暴露面
    ↓ 存活检测
 5,000 台
    ↓ 地理（美/日/台/韩）+ 版本（PHP 8.0.30）
   240 台  批量利用目标
    ↓ 5 台并发，单台 1800 秒超时
    24 台  root 成功
    ↓ 其中 22 台只留 webshell
     2 台  真正深挖
     1 台  管理服务器（经隧道）
─────────────────────────────
    25 台  被利用总数
```

**⭐ 而「24 → 22 停放 + 2 深挖」这个分布，是我认为整个事件最值得警惕的信号（详见第六节）。**

### 3.2 利用链的两段

**⭐ 第一段（PHP2Shell）—— 自研非公开版本：**

> **「The implementation we recovered is a **custom, non-public build**, not a copy of any known public exploit.」**
>
> **「The vulnerability targets PHP's `session.upload_progress` mechanism on the firewall's appweb management server. **The firewall OS uses PHP 8.0.30 with a high memory limit** that enables the memory corruption stages of the attack.」**

**⭐ 第二段（Fragnesia）—— 从 `nobody` 到 root：**

**—— SELinux 的 `httpd_t` 域不允许改系统文件，所以需要第二个漏洞：用页缓存写入覆盖 `/etc/pam.d/su`，换成 `pam_permit.so`。**

**⭐ 而 Dream 的一句话点出了这条链的效率：**

> **「Both exploits run in a single B2 HTTP request. The total chain — from unauthenticated HTTPS connection to persistent root webshell — completes in **under 15 minutes**.」**

### 3.3 ⭐ 而版本画像，解释了「为什么不是扫描即得」

**⭐ Dream 的版本画像矩阵：**

| PAN-OS 分支 | PHP | 画像数 | 说明 |
|---|---|---|---|
| **11.1** | 7.4.33 | 2 个暂定 | **整链未标定** |
| **12.1, 12.2** | 8.0.30 | **1 个已标定 + 8 个暂定** | 基础画像完整实验室验证，其余继承几何布局 |

**⭐ 而 Dream 描述的准备工作量：**

> **「the attacker invested significant effort into vulnerability research — **obtaining PAN-OS firmware, decrypting it, extracting PHP libraries, building precise memory profiles for 9 different software versions, and calibrating exploit geometry through lab testing**.」**

**⭐ 而这一段正好解释了 XSS 论坛研究者那句尖刻的评价（经 Flare 转述）：**

> **「In practice it's **unexploitable crap**. To exploit real targets you need the **offsets from libphp.so, which are unique to every build and impossible to brute-force**. You can reproduce it on your own test bench, or **if you already have access to the target's file system**.」**

**⭐ 我认为这句话对防守方极有价值 —— 它精确说明了「为什么 PoC 不能直接用」：**

**—— `libphp.so` 的偏移量**每个构建都不同**，而攻击者要么有目标文件系统（要先拿下别的什么），要么得为每个版本做实验室标定。**

**⭐ 而这正是「24 台 vs 240 台」这个数字差距的原因 —— 也是为什么攻击者需要提前几周准备。**

## 四、⭐⭐ 从防火墙到域控

**⭐ 这一段 Dream 写得非常具体，我按时间顺序整理。**

### 4.1 ⭐ 反向 SSH 隧道（8 端口）

**⭐ 转发的目标：**
- **域控（LDAP / LDAPS / RDP）**
- **防火墙管理服务器**
- **GlobalProtect VPN 基础设施**
- **⭐ 一个 SOCKS5 代理**（用于任意内网访问）

**⭐ 而持久化方式值得记：**

> **「The tunnel was wrapped in a **systemd service and an `rc.local` boot hook**, both launching scripts from **`/usr/local/lib/.panops/`** — it survives reboots and automatically reconnects.」**

**⭐ `/usr/local/lib/.panops/` —— 点目录、模仿 Palo Alto 的运维命名。** **又一个「命名伪装」实例。**

### 4.2 ⭐ 90 分钟：第三台

**⭐ 10-24 11:35 UTC（root 第二台后 90 分钟内）：**

**用同一条链打穿了只能经隧道访问的「防火墙管理服务器」—— 而这台机器集中管理该组织的全部防火墙。**

**⭐ 我想指出这个「同一条链被复用」的机制：**

**⭐ 隧道把一台原本不可达的机器，变成了「可直达的资产」** → **然后同一套工具直接打它** → **拿到它的权限** → **它管理的所有东西都归你了。**

### 4.3 ⭐ AD 攻击

| 状态 | 动作 |
|---|---|
| ✓ | **解密 LDAP 服务账号密码**（配置里加密存储，root 有主密钥） |
| ✓ | **枚举域内全部用户与组** |
| ? | **对每个用户做密码喷洒**（用组织相关主题的密码） |
| ? | **创建后门用户账号与机器账号** |
| ? | **从 Keycloak IdP 配置提取 SAML 签名密钥** |

**⭐ 而「喷洒」能成立的前提是一个域控设置：**

> **「The domain had `lockoutThreshold=0` — meaning **no account lockout**, allowing unlimited spray attempts.」**

**⭐ 以及 SAML 那一侧的弱配置：`validate-idp-certificate: no`。**

### 4.4 ⚠️ 而一个必须说清楚的不确定性

**⭐ THN 的报道里有一句很克制的表述：**

> **「It's unclear if the activity allowed the threat actor to **successfully find valid credentials or create backdoor accounts**. As a result, **the full extent of the compromise remains indeterminate**.」**

**⭐ 我认为这个「不确定」应该被完整保留 —— 因为它是这类事件分析里最容易被省略、也最重要的部分。**

## 五、⭐ 攻击者手里现在有什么

**⭐ 这张表可以直接当防守方的自查清单：**

| 资产 | 状态 |
|---|---|
| **对内网的持久访问** | ⭐ **反向隧道 + SOCKS 代理，「likely still active」** |
| **3 台设备上的 root webshell** | ⭐ **「likely still active」** |
| **完整 AD 用户与组列表** | ⭐ **「一份完整的组织蓝图」** |
| **解密的 LDAP 服务账号凭据** | ⭐ **可随时直接查询 AD** |
| **收割的私钥** | ⭐ **HA 复制密钥、SSL/TLS 证书密钥、设备认证密钥** |
| **完整网络拓扑** | ⭐ **每个 IP、主机名、子网、服务器角色、VPN 网关** |
| **SAML IdP 配置** | ⭐ **`validate-idp-certificate: no`** |
| **22 台停放的防火墙** | ⭐ **美/日/台/韩，随时可再用** |
| **⭐ 19,000 个已指纹化目标** | ⭐ **随着画像完善可随时再来** |

**⭐ 而 Dream 报告的最后一句，是我认为最该被引用的：**

> **「Palo Alto Networks device telemetry shows **continued exploitation attempts** against exposed PAN-OS devices.」**

**—— 攻击还在继续。**

## 六、⭐⭐ 我的评价

### 6.1 ⭐⭐⭐ 而「22 台停放」比「25 台被 root」更值得警惕

**⭐ 我反复回到这一点，因为它揭示的东西比技术细节深。**

```
大多数攻击的形态：打进去 → 拿 shell → 挖数据 → 走人
这次的攻击形态：打进去 → 拿 shell → 什么都不做 → 停着
```

**⭐ 我认为这说明了三件事：**

**① 攻击者要的是「组织级访问」，不是「数据」。**

**—— 枚举域用户、拿 LDAP 凭据、建后门账号，这是**身份系统**级别的目标。**

**② 那 22 台是「未来的期权」。**

**—— 它们随时可以成为入口。而对防守方来说，**被入侵后看起来完全正常的设备**，是最难发现的一类。**

**③ ⭐ 而这暴露了一个真实的检测盲区：**

**—— 一个只留了 webshell、没有任何异常进程、没有外连的设备，在监控上是「静默」的。** **除非你做主动 hunt（比如检查 `authorized_keys`、检查 `~/.config` 下的隐藏文件），否则它不会自己举手。**

**⭐ 而这正好接上了本号此前写的那篇「php2shell 一周实测」的一个结论：**

| | 10-27 的 Wiz 实测 | 10-29 的 Dream 发现 |
|---|---|---|
| **暴露面** | 下降 47.9% | — |
| **利用尝试** | 全球仅 10% 组织 | ⭐ **240 台目标批量利用** |
| **端到端成功** | ⭐ **「尚未观察到」** | ⭐ **24 台 root** |

**⭐ 而「为什么没观察到」的答案现在清楚了：**

**—— 因为攻击者用的是**自研非公开版本**，且**目标筛选极窄**（4 国 + 特定版本分支）。**
**—— 在「总体比例」这个尺度上完全看不见，但在「那 240 台」的尺度上极其密集。**

**⭐ 所以暴露面下降 47.9% 是好事，但它衡量的是「有多少设备暴露」，**不衡量「有多少设备正在被针对性攻击」** —— 后者要看的是「针对你这个版本、你这个地区」的定向扫描。**

### 6.2 ⭐⭐ 而「AI 辅助」这个信号，该怎么读

**⭐ 我想给一个比「AI 又被用来做坏事了」更有用的解读。**

**⭐ 我认为有三层：**

**第一层：这不是新东西，但规模变了。**

**—— 把 LLM 当「通用开发代理」来用加速脚本开发，早就有人做。** **但这次的差别在量级：近 40 个脚本，加上一个专门配置的 AI 攻防平台（`aiscan` + DeepSeek + Kimi）。**

**⭐ 我认为真正的变化不是「AI 能不能写漏洞利用」，而是这个：**

> **⭐⭐ 「从 PoC 到可靠的攻击向量」这道坎，被 AI 跨过去了。**

**⭐ 因为 XSS 论坛那位研究者说得非常清楚 —— PHP2Shell 的 PoC「unexploitable crap」，因为 `libphp.so` 的偏移量每个构建都不同。**

**—— 而 AI 擅长的恰恰是「大量重复的标定工作」。** **给 9 个版本各建一份画像、在实验室里反复校准堆布局几何参数 —— 这正是 LLM 最擅长的批量体力活。**

**第二层：⭐ 而「基础设施里装着 Claude Code」这件事，本身是一个新的可观测信号。**

**⭐ 我认为这一点对防守方有实际价值：**

| | |
|---|---|
| **传统归因难点** | 攻击工具是通用的（Metasploit、定制脚本） |
| **⭐ 现在的归因新线索** | ⭐ **攻击基础设施里可能有 AI 代理工具的安装痕迹、API 凭据、模型配置文件** |

**—— 「攻击者的机器上装了 Claude Code」是一个**可以被取证的特征**。** 而它比「代码风格像 AI 写的」硬得多。**

**⭐ 而我觉得这可能是一个正在形成的取证方向：** **未来的事件响应里，「AI 代理工具的使用痕迹」可能会像今天的「Cobalt Strike beacon」一样，成为一类标准指标。**

**第三层：⭐⭐ 而我要提醒的是 —— 不要把「AI 辅助」当成「AI 自主」的证据。**

**⭐ Dream 的原话是「**suggest** the use of AI to augment the development process」—— 「augment」，增强，不是取代。**

**⭐ 而这批攻击的**规划**部分极其专业：**
- **先解密固件、提取 PHP 库**
- **为 9 个版本建画像**
- **筛 4 个国家、2 个版本分支**
- **22 台停放、只挑 2 台深挖**
- **优先打管理服务器（价值最高）**
- **域控 `lockoutThreshold=0` 的利用**

**—— 这些判断，不是「让 AI 试 1000 次」能得到的。** **这是「知道自己要什么」的人才做得出的决策。**

**⭐ 所以我认为最准确的表述是：**

> **⭐⭐ **AI 把「执行」变快了，但「决策」仍然来自人。**
> **而这恰恰是这类攻击最值得担心的形态 —— 因为**人类的判断力 + AI 的吞吐量**，比两者单独任何一个都更难防。**

### 6.3 ⭐⭐ 而国家背景的归因，要保留余地

**⭐ Dream 说「Chinese AI-assisted campaign」，THN 引述了「美/日/台/韩是四个主要战略对手」的推理。**

**⭐ 我认为这个推理的结构是：**
```
目标国家选择 → 指向国家行为体
```
**⭐ 而这个推理的强度，取决于一个前提：** —— **「这四个国家是主要目标」这个判断本身有多可靠。**

**⭐ 而 Dream 的报告里，其实给出了两个更硬的证据，比地理推断更扎实：**

| 证据 | 强度 |
|---|---|
| **⭐ 攻击基础设施里装了 Claude Code、FOFA API key、aiscan + DeepSeek/Kimi** | ⭐ **强**（工具链本身） |
| **⭐ 使用 FOFA**（中国资产搜索引擎） | ⭐ **中** —— 常用工具，不是归属证据 |
| **目标国家恰好是美/日/台/韩** | ⚠️ **弱** —— 恰好是暴露面最大的发达经济体 |

**⭐ 所以我认为最稳妥的表述是：**

> **⭐ 「工具链特征与目标选择**指向**国家支持的行为体」—— 而这是**评估**，不是定论。**

**⭐ 而一个具体的、更能说明问题的旁证是 Dream 报告里的这句：**

> **「the code structure, commenting style, and consistency across nearly 40 scripts suggest the use of AI to augment the development process.」**

**—— 注意 Dream 自己也只用了「suggest」。**

### 6.4 ⭐⭐ 而最后，关于「防御分层」的一张表

**⭐ 我在 Fragnesia 那篇里做过这张表，这里再收一次，因为它是这个攻击最可复用的部分：**

| 环节 | 本可以拦住它的控制点 | 实际 |
|---|---|---|
| **找到目标** | 管理界面不应暴露公网 | ❌ 19,000 台暴露 |
| **利用 PHP** | 打 PHP 补丁 | ❌ 未打 |
| **从 nobody 到 root** | ⭐ **SELinux 域限制** | ✅ **拦住了** —— 所以才需要 Fragnesia |
| **Fragnesia 提权** | 不加载 esp4/esp6 / 打内核补丁 | ❌ |
| **写 `/etc/pam.d/su`** | PAM 文件不可被页缓存写 | ❌ 内核层绕过 |
| **持久隧道** | 出站流量检测 / 段隔离 | ❌ |
| **解密 LDAP 密码** | 加密存储 + 密钥隔离 | ❌ root 拿到主密钥 |
| **⭐ AD 密码喷洒** | ⭐ **域账号锁定策略** | ❌ **`lockoutThreshold=0`** |

**⭐ 整条链 8 个环节，7 个需要补丁或架构调整，只有 1 个是改一个域控设置 —— 而攻击者走完全程，恰恰因为那一个也没做。**

## Sources

- ⭐ 一手：[Dream Security — Chained PHP2Shell Exploit Roots 25 Servers, including US Government Servers](https://dreamgroup.com/blog/chained-php2shell-exploit-roots-25-servers)（2026-10-29，含完整攻击链、版本画像表、十步时间线、攻击路径图、AI 辅助开发证据）
- ⭐ 一手：[The Hacker News — PHP2Shell Attack Roots 25 Servers, Breaches U.S. Government-Affiliated Network](https://thehackernews.com/2026/10/php2shell-attack-roots-25-servers.html)（Ravie Lakshmanan，**2026-10-28**，含 Claude Code / FOFA API key / aiscan + DeepSeek & Kimi 的证据，以及 Dream 的国家背景引述）
- ⭐ 一手（Flare 转述）：XSS 论坛研究者 c0d3x 对 PoC 可用性的评价（「unexploitable crap」与 libphp.so 偏移量问题）
- 一手：[CISA KEV — CVE-2026-46300](https://www.cisa.gov/known-exploited-vulnerabilities-catalog?field_cve=CVE-2026-46300)（加入 2026-10-28，限期 10-31）
- 一手：[NVD — CVE-2026-46300](https://nvd.nist.gov/vuln/detail/cve-2026-46300)（CVSS 7.8）
- 一手：[Palo Alto Networks Unit 42 独立验证](https://www.csoonline.com/article/4242454/php2shell-plus-fragnesia-a-dangerous-new-route-from-web-server-to-root.html)（经 Dream 报告引述）
- 本号此前：php2shell 根因与发行版打补丁（2026-10-21）、纯 HTTP ASLR 绕过（2026-10-23）、一周实测（2026-10-27）、CVE-2026-46300 Fragnesia 详解（2026-10-30）

---

（说明：所有引号内内容、时间线与数字均来自上述一手材料；**第三、四节的攻击链还原为依据 Dream Security 报告所做的整理，不含可运行的利用代码**；**第六节的「AI 辅助信号解读」与「归因保留余地」的分析为笔者观点**。）
