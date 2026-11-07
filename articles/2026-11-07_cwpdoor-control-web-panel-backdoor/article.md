---
title: "Control Web Panel 后门 cwpdoor：cwpsrv 里的静默通道"
date: 2026-11-07
slug: cwpdoor-control-web-panel-backdoor
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：奇安信 XLab《CWPdoor: The Invisible Backdoor Living Inside Control Web Panel》（2026-11-05）的技术分析与 IOC 清单 ＋ The Hacker News 报道（2026-11-06，Swati Khandelwal）＋ BleepingComputer 关于加密与签名机制的细节 ＋ ThreatDefence 的独立 VirusTotal 复查 ＋ webhosting.today 引述的 XLab 暴露面统计 ＋ 本文对照 CWP 官方 changelog 核对的修复版本时间线"
original_date: 2026-11-05
original_url: "https://thehackernews.com/2026/11/hackers-hide-linux-backdoor-in-control.html"
description: "本文解读奇安信 XLab 于 2026 年 11 月 5 日披露的 cwpdoor：一个不是独立恶意程序、而是**被重新编译进 cwpsrv 源码里**的 Linux 后门。Control Web Panel（CWP，原 CentOS Web Panel）是广泛用于廉价 VPS 和转售账户的免费主机管理面板，它的后端 web 服务器 cwpsrv 就是攻击者的目标。攻击者把恶意代码插入 cwpsrv 源码、重新编译、替换掉合法文件，于是这个文件「表现得像一个正常的 cwpsrv」—— 直到收到带有特定自定义 header 的请求才激活。三个设计让 XLab 形容它「异常隐蔽」（exceptionally stealthy）：其一，触发命令走 X-Ngx-Integrity 系列 header，命令与输出用 AES-256-CBC 加密，时间戳被限制在正负 300 秒窗口内且必须通过 RSA 签名校验，改动时间戳或密文任一字段都会使签名失效，从而同时获得重放保护和授权控制；其二，后门会干扰服务器的日志模块，把触发请求从 access log 里抹掉；其三，安装脚本在替换文件后会把文件时间戳改回原值，所以 ls 和 stat 看起来一切正常。更反直觉的是：安装器只支持 cwpsrv 1.15.10 与 1.24.0 两个版本，需要 root 权限，而攻击者**如何拿到 root 至今未知** —— XLab 明确说这是未解之谜。暴露面方面，XLab 基于自有 Hunter 平台统计过去一个月暴露在互联网上的 CWP 实例超过 34 万个，并把它们全部描述为潜在目标。本文给出 XLab 的三条检测命令（socket / 文件 / 进程）、完整 IOC 清单（3 个 MD5、1 个 IP、3 个 URL），以及清理步骤，并指出两个容易被忽略的现实：那台「开放端口看起来正常」的机器 socket 检查却查出了后门，以及安装器会在替换成功后删除自己的备份，导致 XLab 建议的恢复手段可能根本不存在。"
published: true
---

> 原文：奇安信 XLab《CWPdoor: The Invisible Backdoor Living Inside Control Web Panel》（2026-11-05）
> 报道链接：<https://thehackernews.com/2026/11/hackers-hide-linux-backdoor-in-control.html>
>
> 本文依据奇安信 XLab 原始技术分析与 IOC 清单、多家媒体的报道、ThreatDefence 的独立 VirusTotal 复查，以及本文对照 CWP 官方 changelog 核对的修复时间线。

## 一、先说清楚一件事：它不是一个程序

这是理解 cwpdoor 的关键，也是它与绝大多数 Linux 后门最大的不同。

**cwpdoor 不是一个独立的恶意文件。** XLab 的原话是：攻击者把恶意代码插入 cwpsrv 的**源码**，然后**重新编译**，替换掉服务器上那个合法的文件。

所以后门不是一个「多出来的文件」，而是「本来就在那里的那个文件，被改过了」。

这带来一个直接后果：**基于文件清单的检测会失效。** 你在 `/usr/local/cwpsrv/bin/` 目录里看到的 `cwpsrv` 是存在的、版本号是对的、大小可能也差不多 —— 因为它确实是 cwpsrv，只是不再完全是。

XLab 描述的整个安装流程是：

1. 伪装成版本更新的 shell 脚本（`cwpsrv_update.sh`）；
2. 检查本地 cwpsrv 版本，下载对应版本的二进制，校验版本号匹配；
3. 备份原文件；
4. 停掉 cwpsrv 服务；
5. 用恶意二进制覆盖 `/usr/local/cwpsrv/bin/cwpsrv`；
6. 重启服务；
7. 检查 master、worker、helper 进程是否都在运行。

而这个安装器**只支持两个版本**：cwpsrv 1.15.10 和 1.24.0。

## 二、三个让它「异常隐蔽」的设计

XLab 用了一个很不客气的评价：**exceptionally stealthy**（异常隐蔽）。看完技术分析，我觉得这个评价站得住 —— 因为它不是靠某一种单一技术，而是三层叠加。

### 第一层：触发通道藏在 HTTP header 里，且命令是加密的

后门给 cwpsrv 加了两个函数：`ngx_http_integrity_init` 和 `ngx_http_integrity_check`。

正常运行时它什么都不做。只有当请求里带着**有效的时间戳和签名**（放在以 `X-Ngx-Integrity` 开头的自定义 header 里），它才会执行请求携带的命令。

而命令本身的保护有三层（BleepingComputer 补充了细节）：

| 机制 | 作用 |
|---|---|
| **AES-256-CBC** 加密命令与输出 | 命令不以明文出现在请求里 |
| **RSA 签名** | 改时间戳或改密文**任一字段**都会让签名失效 |
| **±300 秒时间窗口** | 防止重放 |

XLab 自己的总结是：

> **By binding the three fields together and enforcing a ±300-second time window, the mechanism provides replay protection and authorization control.**

（把三个字段绑定在一起、再强制一个正负 300 秒的时间窗，这个机制同时提供了重放保护和授权控制。）

**这三个字段绑定的设计值得单独说一句。** 如果只校验签名不绑时间戳，攻击者截获一次合法请求就能无限重放；如果只校验时间窗不签内容，中间人改一下密文就能塞进任意命令。**必须同时满足**才能触发 —— 这是一个相当扎实的工程设计。

而这也意味着：**攻击者自己也无法伪造触发请求**。除非他手里有对应的私钥。

### 第二层：触发请求不进 access log

后门会**干扰服务器的日志模块**，把触发请求从访问日志里抹掉。

XLab 的技术分析提到，实现方式是遍历 `ngx_modules` 数组，定位并缓存日志模块的索引，用于后续的日志抑制。

**这一层的杀伤力在于：它让「事后查日志」这条路直接断掉。**

普通的入侵排查，起点几乎都是「查访问日志看看有没有异常请求」。而这个后门的设计前提就是：**你来查的时候，什么都不会留下。**

### 第三层：文件时间戳被改回原值

安装器在替换 cwpsrv 文件之后，**把文件的日期改回原值**，所以 `ls` 和 `stat` 看起来一切正常。

这一层是给第二层兜底的：即使你去查文件系统（而不是日志），时间戳也不会暴露替换发生过。

## 三、检测：三条命令，和一个反直觉的结果

XLab 给了三条检测命令，分别对应三层隐蔽。

| 层 | 命令 | 期望结果 |
|---|---|---|
| **Socket** | `ss -axp \| grep integrity` | 出现名为 `ngx_http_integrity_helper` 的 Unix socket 即为感染 |
| **文件** | `strings /usr/local/cwpsrv/bin/cwpsrv \| grep X-Ngx-Integrity` | 出现后门专有的 header 名即为感染 |
| **进程** | `ps aux \| grep cwpsrv` | 查找 cwpsrv 启动的可疑 helper 子进程 |

**这里有个我觉得整份报告里最值得记的细节。**

XLab 在他们的示例环境里，那台服务器的**开放端口列表看起来完全正常** —— 但 socket 检查查出了后门。

这个反差说明了什么？**说明「看端口」这种检查思路对这个后门无效。**

因为后门**不开新端口、不连新地址、不改防火墙规则**。它复用的是 cwpsrv 本来就在监听的 HTTP/HTTPS 端口，触发通道就是普通的 Web 请求。你在端口层面看到的，和一台干净的 CWP 服务器没有任何区别。

这也解释了为什么 ThreatDefence 在他们的操作建议里专门加了一条：**给托管服务器装 EDR** —— 理由写得很直接，「进程和文件事件才是抓住这个后门的东西，而面板服务器通常没有 EDR」。

**换句话说，这类攻击的检测能力边界，就等于你在主机上有没有进程和文件层面的可见性。** 只看流量和端口的主机，对这个后门是瞎的。

### 但也要说清楚这三条命令的局限

XLab 自己在结论里提醒了：这些检查针对的是**已知的 cwpdoor 指标**，所以「检查通过并不能排除其它变体或其它威胁」。

ThreatDefence 的独立复查还补了两个数据点：

- 1.15.10 那个样本在 VirusTotal 上**至今仍是零检出**（11-06 复查）；
- 1.24.0 的样本**根本不在 VirusTotal 上**。

而 XLab 公布的数据是：**63 个引擎，零检出。**

顺带说，XLab 提到 VirusTotal 上那个压缩包是从**巴西**上传的（文件名 `evidencia.tgz`），里面有两个文件 —— 一个 Ebury 组件，一个标着 `cwpsrv.suspeito`。而 Ebury 是那个至少从 2009 年就活跃的 OpenSSH 后门和凭据窃取器，**杀毒软件对它的检出率很高**。

**XLab 明确表示不知道这两者是否相关，并说很可能是不同攻击者在同一台服务器上分别植入了它们。** 这一点很重要 —— 看到 Ebury 不等于只中了 Ebury。

## 四、IOC 清单

XLab 公布的指标（只给了 MD5，没给 SHA256）：

| 类型 | 值 | 说明 |
|---|---|---|
| MD5 | `e505d4ffa21cf494a5dc2d7c8f4f1236` | 安装脚本 `cwpsrv_update.sh` |
| MD5 | `965aea67fb40de1bab5169ada993349f` | 被植入后门的 cwpsrv 1.15.10（EL7） |
| MD5 | `d3f4e95113d49ab3991b45e457bda75b` | 被植入后门的 cwpsrv 1.24.0 |
| IP | `136.0.141.71` | 下载服务器 |
| URL | `http://136.0.141.71/static/cwpsrv_update.sh` | 安装脚本 |
| URL | `http://136.0.141.71/static/cwpsrv_1.15.10` | 后门二进制 |
| URL | `http://136.0.141.71/static/cwpsrv_1.24.0` | 后门二进制 |

注意三个 URL **都是明文 HTTP**，没有 TLS。

## 五、清理：以及一个可能让你无路可退的坑

XLab 给的三步清理：

1. **恢复原文件。** 从安装器创建的备份恢复，文件名以 `cwpsrv.prev-` 开头、以日期时间结尾（格式是 `cwpsrv.prev-$(date +%Y%m%d-%H%M%S)`），位置在 `/usr/local/cwpsrv/bin`。
2. **升级到最新版本**，然后确认 `ss -axp | grep integrity` 不再返回任何结果。
3. **立即轮换所有控制面板凭据**，并把整台服务器当作已被攻陷，检查其它威胁。

### 第 1 步可能根本做不了

XLab 在安装器分析里写了一句：**安装器在替换成功后，会删除「临时文件和备份」。**

所以第一步要用的那个 `cwpsrv.prev-*` 备份，**很可能已经不存在了**。

这一条把清理路径切成了两半：

- **备份还在** → 恢复 + 升级 + 换凭据；
- **备份没了** → **只能升级**（前提是升级后的版本不含这个后门），加上换凭据、封 IOC、以及假设机器已被完全攻陷。

而 CWP 官方的修复时间线是（ThreatDefence 引用 CWP changelog 核对）：

- **2026-11-03**：CWP 1.30.1 作为安全更新发布；
- **2026-11-05**：XLab 发布 CWPdoor 分析。

也就是说，**官方补丁比后门曝光早了两天**。如果这台机器在 11-03 之后升过级，那么被替换的 `cwpsrv` 已经不是最新版了 —— 但**被植入后门的那个文件可能仍然在跑**，因为它替换的是文件而不是包。

### 第 3 步为什么是「换所有凭据」

因为这个后门「能执行任意命令」（the backdoor can run any command）。

它不是偷走一个 cookie 或者一个密码 —— 它是**一个能执行任意命令的 root shell**。所有在这个面板里配置过的凭据、API key、数据库口令、部署密钥、SSH 私钥，都必须视为已泄露。

而对托管服务商来说，范围还要更大：托管在这个面板下的**客户网站**、客户 DNS、客户邮件 —— 全都在影响范围内。CWP 有合作伙伴主机列表（XLab 没有点名任何具体受影响的托管商）。

## 六、两个未知，和一个数字

XLab 明确留了两个空白：

**① 攻击者是怎么拿到 root 的？** 不知道。安装需要 root 权限，所以攻击者**已经**控制了服务器 —— 但那个「已经」是怎么来的，研究者还没查清。

**② 有多少台被感染了？** 不知道。9 月 30 日那个 VirusTotal 压缩包说明「真实受害者已经存在于野外」（real victims already exist in the wild），但**没有给出感染数量**。

不过 XLab 给了暴露面的量级：基于自有 Hunter 平台统计，**过去一个月暴露在互联网上的 CWP 实例超过 34 万个**，并把它们全部描述为潜在目标。

**34 万这个数字要和「零检出、零日志」放在一起看。** 一个不新增端口、不留日志、杀毒全绿的载荷，落在 34 万个潜在目标上 —— 这个组合意味着**发现周期完全取决于目标自己有没有做进程/文件层面的监控**，而不是取决于攻击者有多小心。

## 七、修复时间线与版本对照

我把相关时间点整理一下：

| 时间 | 事件 |
|---|---|
| 2026-06-29 | XLab 捕获安装器（伪装成版本更新的 shell 脚本） |
| 2026-09-30 | 巴西有人把含后门的压缩包上传到 VirusTotal |
| 2026-11-03 | CWP 1.30.1 作为安全更新发布 |
| 2026-11-05 | XLab 发布 CWPdoor 技术分析 |
| 2026-11-06 | 媒体报道；ThreatDefence 独立复查（1.15.10 样本仍零检出） |

**这里有一个对防守方很实用的判断**：安装器只支持 **1.15.10** 和 **1.24.0** 两个版本。

这意味着**版本本身就是筛查条件** —— 如果你的 CWP 不在这两个版本上，这个特定安装器跑不起来。这不代表你安全（可能有变体），但能帮你快速缩小排查范围。

而 XLab 也说了：**报告没有给 CVE、没有 CVSS 评分、没有厂商补丁版本号**。这是因为从技术上讲它不是「某个版本的漏洞」，而是「攻击者替换了文件」—— 没有一个版本是「有漏洞的」，只有一台机器是「被改过的」。

---

## Sources

- 奇安信 XLab, *CWPdoor: The Invisible Backdoor Living Inside Control Web Panel*（2026-11-05）: <https://blog.xlab.qianxin.com/cwpdoor-the-invisible-backdoor-living-inside-control-web-panel>
- The Hacker News, *Hackers Hide Linux Backdoor in Control Web Panel Server to Execute Commands Without Logs*（2026-11-06, Swati Khandelwal）: <https://thehackernews.com/2026/11/hackers-hide-linux-backdoor-in-control.html>
- BleepingComputer, *Hackers backdoor Linux servers using trojanized CWP web server*（2026-11-05）: <https://www.bleepingcomputer.com/news/security/hackers-backdoor-linux-servers-using-trojanized-cwp-web-server>
- ThreatDefence, *CWPdoor in Control Web Panel: Detecting the Backdoored cwpsrv, Hunting Hidden Commands and Cleaning Up*（2026-11-06，含独立 VirusTotal 复查与 CWP changelog 时间线）: <https://threatdefence.com/article/cwpdoor-control-web-panel-cwpsrv-backdoor-hunting>
- webhosting.today, *CWPdoor Replaces Control Web Panel's Web Server and Hides Attack Commands From Logs*（2026-11-06，引述 XLab 的 34 万暴露面统计）: <https://webhosting.today/2026/11/06/cwpdoor-replaces-control-web-panels-web-server-and-hides-attack-commands-from-logs/>
- Control Web Panel 官方 changelog: <https://control-webpanel.com/changelog>

### 事实边界说明

- 后门机制、安装流程、检测命令、IOC 清单、清理步骤、以及「攻击者如何拿到 root 未知」「感染数量未知」：引自奇安信 XLab 原始技术分析。
- **AES-256-CBC 加密、RSA 签名、±300 秒时间窗，以及「改任一字段即签名失效」**：引自 BleepingComputer 对 XLab 报告的细节复述与 XLab 原文引用。
- **63 个引擎零检出、1.15.10 样本在 11-06 复查仍零检出、1.24.0 样本不在 VirusTotal 上**：引自 ThreatDefence 的独立复查。
- **34 万暴露面（CWP 实例数）**：引自 webhosting.today 引述 XLab 的 Hunter 平台统计。
- **CWP 1.30.1 于 2026-11-03 发布、1.15.10 样本对应 EL7**：引自 ThreatDefence 引用 CWP 官方 changelog 的对照。
- 关于 VirusTotal 上传的压缩包来自巴西、含 Ebury 组件、以及 XLab 认为两者可能无关：引自 XLab 与媒体引述。
- 本文只做防守方视角的分析，不包含任何可用于构造触发请求或植入后门的实现细节。
