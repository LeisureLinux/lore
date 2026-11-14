---
title: "Cursor 安全事件复盘：一把供应商密钥，怎样走到 5000 台开发机"
date: 2026-11-14
slug: cursor-security-incident-fireworks-claude-code-extension
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Cursor《An update on our recent security incident》（Cursor Team，2026-11-13；10-29 首报、两周调查、攻击链五步、Fireworks 暴露的 access key、只读桶里 2025 年非 Privacy Mode 的 coding agent traces、未脱敏凭证、少于 0.01% 客户 API 凭证暴露、非 Privacy Mode 用户中少于 0.05% 的 traces 暴露、10-29 Cache 投毒、最多 5000 用户 / 约 11 小时、11-01 最后一次被阻断的攻击者活动、未受影响清单、七项整改、道歉与 security@cursor.com）＋ Cursor《Security notice — malicious version of Anthropic.claude-code (2.1.312 and 2.1.313) identified in the Cursor VS Code Extension Marketplace》（2026-10-29，10-30 11:30 PT 更新 IOC；2:27am–1:35pm PT 窗口、Windows/macOS、恶意行为、svc-telemetry 公钥与指纹、134.209.82.225:8099/beacon、macOS LaunchAgent com.apple.sysmond.plist / Windows 计划任务 SysMon / Linux cron @reboot、卸载扩展不足、检测与整改脚本、四个 VSIX SHA-256）＋ Fireworks AI 安全公告两篇（2026-10-09/10 首发：10-06 发现内部凭证被滥用、evaluation jobs 环境变量中的 API keys/tokens、ZDR、通知与轮换时间线、给客户的四条动作；2026-11-09 更新：通知执法机关并请 Palo Alto Unit 42 取证、涉及账户/账单信息、部分账户的 secrets/datasets/未完成模型、归因于以倒卖 LLM tokens 为目的的 LLMJacking 团伙、10-23 第三方云厂商事故导致 10-24 开发机被触达、10-25 后未再发现成功未授权访问、四类加固、暂停自助数据集上传下载）＋ The Hacker News《Official Claude Code Extension on Cursor Marketplace Trojanized with Persistent SSH Backdoor》（2026-10-30；OpenSourceMalware 的 66 行 loader、Anthropic 官方渠道与 Open VSX / 微软市场 / npm 未受影响、Anthropic 与微软独立声明、Socket 复核、2.1.314 为官方最新）＋ Expel《Fake Claude Code extension in Cursor: How to find the backdoor》（2026-10-30；四起真实事件、其中一起首次恶意活动在窗口关闭约 8 小时后、非管理员机器上隧道仍外连、只查 svc-telemetry 会漏、MITRE ATT&CK 映射、检测清单）＋ Dark Reading / Ars Technica / Field Effect 的同期报道作时间线与「SolarWinds 式微型翻版」定性交叉验证"
original_date: 2026-11-13
original_url: "https://cursor.com/blog/security-incident-update"
description: "解读 Cursor 11 月 13 日的安全事件复盘。文章把攻击链拆成五段：起点是 Cursor 发给推理供应商 Fireworks 的 access key 被 Fireworks 侧暴露，攻击者据此复制一个只读共享桶里 2025 年、非 Privacy Mode 且允许用于训练的 coding agent traces；少量 traces 里残留未脱敏凭证，成为进入 Cursor 所用 SaaS 工具的跳板，进而触达归档的非生产源码仓库、有限客服与邮件数据、用量指标与联系方式、部分会话摘要、以及用户发给支持团队的凭证；10-29 攻击者用偷来的凭证把冒牌 Claude Code 扩展直接放进 Cursor VS Code 扩展市场的服务缓存，最多 5000 名请求特定缓存版本的用户可能拿到恶意构建，存活约 11 小时。文章把厂商口径与可验证事实分开：Cursor 称生产系统、Privacy Mode 数据、官方 App 与发布签名密钥、客户代码仓库、Open VSX / 微软市场 / npm 均未受影响，非 Privacy Mode 中少于 0.05% 用户的 traces 暴露、少于 0.01% 客户 API 凭证暴露；Anthropic 与微软独立确认官方渠道未被污染。也写清 10-29 通告里的可执行细节：受影响版本 2.1.312/2.1.313、svc-telemetry 公钥、134.209.82.225 的 SSH 隧道与 beacon、三平台持久化、以及「卸载扩展不够、必须单独清 key 与持久化并从可信机器轮换凭证」。重点标出一处口径冲突：Cursor 说多数非管理员机器上登录步骤会失败，Expel 在四起真实事件里却观察到窗口关闭 8 小时后仍有隧道外连、且存在本地管理员或远程登录本就开启的机器。Fireworks 侧公告则给出另一条背景线：10-06 首报、10-23 其云厂商再出事、归因于倒卖 LLM tokens 的 LLMJacking 团伙。结论：这不是「Claude Code 有漏洞」，而是一次从供应商密钥 → 历史训练数据残留密钥 → 内部 SaaS → 分发缓存的完整凭据链攻击；值得抄进 runbook 的是密钥最小权限、训练数据脱敏、缓存与源站一致性校验、扩展自动更新延迟放行，以及事件通报里的百分比要配合绝对动作一起读。"
published: true
---

11 月 13 日，Cursor 发了两周前那起安全事件的复盘。10 月 29 日大家先看到的是「扩展市场里出现冒牌 Claude Code 扩展」，当时的公开信息止于一个 11 小时窗口、两个版本号和一个 SSH 后门。这次复盘把前面半条链补上了：起点不在扩展市场，在一把给供应商的密钥。

这篇文章值得按运维视角读，因为它几乎把「凭据链攻击」的每一环都演示了一遍，而且官方通报里的几个百分比很容易被误读成「没事」。

## 一、把攻击链按时间摆开

Cursor 给出的五步，配上 Fireworks 与 10-29 通告的日期，可以排成一条完整时间线：

| 时间 | 事件 | 出处 |
|---|---|---|
| 2026-10-06 | Fireworks 发现内部凭证被未授权使用，部分客户 evaluation jobs 的环境变量（含 API keys/tokens）被读取 | Fireworks 10-09 公告 |
| 2026-10-09/10 | Fireworks 首发公告，轮换员工 API key 与服务账号 token | Fireworks |
| 2026-10-23/24 | Fireworks 的第三方云厂商出事，攻击者触达 Fireworks 开发机并跑未授权工作负载；10-25 后未再发现成功入侵 | Fireworks 11-09 更新 |
| 期间 | 攻击者拿到 Cursor 发给 Fireworks 的 access key（Cursor 称由 Fireworks 暴露），复制双方共享的只读存储桶 | Cursor 11-13 |
| 2026-10-29 02:27–13:35 PT | 冒牌 `Anthropic.claude-code` 2.1.312 / 2.1.313 出现在 Cursor VS Code 扩展市场缓存，约 11 小时 | Cursor 10-29 |
| 2026-10-29 | Cursor 发首份安全通告，下线整个扩展市场、轮换密钥、重建市场 | Cursor |
| 2026-10-30 11:30 PT | 通告更新：补上 2.1.312 并修正 IOC | Cursor / Expel |
| 2026-11-01 | Cursor 看到的最后一次攻击者活动，被阻断 | Cursor 11-13 |
| 2026-11-09 | Fireworks 更新归因与扩展影响（账单信息、部分 secrets/datasets/未完成模型、LLMJacking） | Fireworks |
| 2026-11-13 | Cursor 发布完整复盘 | Cursor |

链条本身很清楚：供应商密钥 → 只读桶里的历史训练 traces → traces 里没脱敏的凭证 → 内部 SaaS 工具 → 归档源码/客服数据/更多凭证 → 扩展市场服务缓存投毒 → 开发者机器。

这不是「Claude Code 有漏洞」。Anthropic 没发布这个包，Open VSX 作为市场源从未带毒，微软确认 Visual Studio Marketplace 与 npm 上的 `@anthropic-ai/claude-code` 均未被污染；The Hacker News 引 OpenSourceMalware 的分析说，恶意代码是插在合法扩展主 bundle 前的 66 行 loader，却仍挂在 `anthropic.claude-code` 这个合法 ID 与版本号下 —— 所以「扩展名对得上」在缓存被投毒时并不构成验证。

## 二、被拿走的到底是什么

Cursor 的桶里装的是有限 coding agent traces，主要来自 2025 年、未开启 Privacy Mode、且允许用于模型训练的会话。问题出在「少量 traces 里含有未脱敏的凭证」。这一步把一次数据暴露升级成了横向移动：

- 从这些凭证出发，攻击者进了 Cursor 使用的部分 SaaS 工具；
- 从那里触达归档的非生产源码仓库（部分含商务联系人信息）、有限的客服数据与邮件对话、产品用量指标与联系方式、部分 coding agent 会话摘要，以及用户发给 Cursor 支持团队的凭证；
- 10-29 再用其中偷来的凭证，把恶意 VSIX 直接放到服务扩展市场的缓存上（不是源站）。

Cursor 给的两个数字要按原句读：

- 非 Privacy Mode 用户中，traces 被暴露的少于 0.05%，已逐一通知；没收到通知即不在其中；
- 少于 0.01% 客户有 API 凭证暴露，管理员收到需要轮换的具体 key 列表，Cursor 也请签发方吊销。

「少于 0.01%」听着极小，但它对应的是凭证，不是日志行 —— 一个未轮换的 key 就够走完上面整条链。这里该读的是绝对动作（有没有收到通知、有没有要轮换的 key），不是百分比。

未受影响的清单同样要按厂商口径标注：Privacy Mode 下的 prompt 与代码、当前实时流量、生产系统、官方 App 与客户端/云端发布代码（发布走另一套代码托管、签名密钥未暴露）、客户代码仓库、其他扩展、Cloud Agents / Grok Bot 等。这些是 Cursor 的自述，Anthropic 与微软的独立声明确认了「官方渠道未被污染」那部分。

## 三、开发者这一端：卸载扩展远远不够

10-29 通告里最该抄进 runbook 的是这段。

冒牌扩展在 VS Code 启动或 webview 打开时加载，做的事包括：收集主机名、用户名、OS、架构、家目录路径、环境变量名、工作目录、Git email、公网 IP 并 POST 到攻击者服务器；把标签为 `svc-telemetry` 的 ed25519 公钥写进 `authorized_keys`；尝试开启本地 SSH 服务、建立到 `134.209.82[.]225` 的反向隧道；按平台装持久化：

| 平台 | 持久化 |
|---|---|
| macOS | `~/Library/LaunchAgents/com.apple.sysmond.plist`（伪装成 Apple 组件） |
| Windows | 计划任务 `SysMon`（尝试 SYSTEM）+ Startup 脚本回退 |
| Linux | `cron @reboot /bin/sh ~/.config/.smt` |

后台脚本约每 60 秒重试隧道。Cursor 明写「Uninstalling the extension may not be sufficient」：卸载或更新扩展不会移除写在安装目录之外的持久化产物，必须单独清 key、脚本、启动项，并从可信机器轮换该机器能触达的凭证与会话；官方给了 macOS/Windows 的检测一行命令与整改脚本，以及四个 VSIX 的 SHA-256、`svc-telemetry` 公钥指纹、`extension.js` 哈希等 IOC。

这里有一处厂商口径与实测冲突，值得单独标出。 Cursor 说开启本地 SSH 需要管理员权限，多数 macOS/Windows 主机上这一步会失败、攻击者无法经隧道登录；但 Expel 在四起真实客户事件里观察到：

- 其中一起的首次恶意活动出现在官方 11 小时窗口关闭约 8 小时后（下载发生在窗口内、Cursor 下次启动才执行）；
- 一台非管理员 Mac 上隧道照样向外连接；
- 四起里至少有一台是本地管理员，且远程登录可能本来就开着；
- 有机器上隧道在跑、却找不到 `svc-telemetry` key —— 只跑那一条 grep 会漏。

所以排查范围不能只框在「10-29 那 11 小时内安装过」，也不能只查一个 key 标签；Expel 的建议是查所有跑 Cursor 的机器、查到 `134.209.82[.]225` 的连接、`tunnel@` 与 `-R *:0:localhost:22` 命令行、`.stk_<10 hex>` 临时文件、`.smt`/`.smtk`、`com.apple.sysmond.plist` 与文件哈希。

## 四、Fireworks 那一边不是一句「供应商背锅」

Cursor 的归因是该密钥由 Fireworks 侧暴露。把 Fireworks 自己的两份公告读一下，会发现这是同一起更长的事件链，而不是单点失误：

- 10-09 首报：10-06 发现内部凭证被滥用，部分客户 evaluation jobs 的环境变量（含 API keys/tokens）被读取；平台默认 ZDR，当时未发现模型/数据集/训练数据/推理流量被访问；给了客户四条动作，其中特别强调「删掉存起来的 secret 不等于吊销底层凭证，必须去找签发方」。
- 11-09 更新：已通知执法机关并请 Palo Alto Networks Unit 42 取证；后续发现账户与账单信息、部分账户的 secrets / datasets / 未完成模型权重也受影响；证据指向以倒卖 LLM tokens 到 illicit routing gateways 为动机的 LLMJacking 团伙（并引 Google Threat Intelligence / Mandiant 11-02 的报告）；10-23 其第三方云厂商出事，10-24 被用来触达 Fireworks 开发机；10-25 后未再发现成功未授权访问。整改包括凭证与服务账号轮换、去掉多余高权限、网络隔离、收紧数据存储访问、加固日志，并暂停自助数据集上传下载。

也就是说，Cursor 这次是下游受害者之一。两家公告合起来看，值得记的是同一个教训：给第三方的数据共享桶、评估任务里的环境变量、服务商侧的开发机，全都是你自己的攻击面。

## 五、值得抄进 checklist 的五件事

1. 共享桶按「会泄露」设计：只读不等于无害；训练/分析用的历史 traces 出口前必须做 secret scanning 与脱敏，且保留可审计的脱敏失败率。Cursor 事后才「在所有代码仓库加 secret scanning 并扩展到内部数据源」，这一步本该在桶之前。
2. 供应商密钥最小化：按数据集/用途/来源 IP 限定，能短期就别长期；Cursor 事后补的正是「扩展服务商网络访问限制，让被盗凭证不能在预期位置之外使用」。
3. 缓存必须与源站做一致性校验：这次被投毒的是服务缓存，Open VSX 源站干净、官方发布渠道干净，所以按源站校验、按签名校验才有意义；只信扩展 ID 与版本号不够。
4. 扩展自动更新延迟放行：The Hacker News 与 Expel 都提到自动更新是最容易中招的路径；对开发者工具可考虑新版本延迟数天放行，并保留可回滚的安装清单。
5. 通报里的百分比要配绝对动作：收到通知 → 查具体 key 列表 → 从可信机器轮换 → 查机器侧持久化 → 保留证据/必要时重建。没收到通知不等于可以跳过资产盘点，尤其有自动更新的机器。

## 六、边界

- 本文的攻击链、比例、未受影响清单与整改措施来自 Cursor 两份官方公告；Fireworks 侧时间线、归因与数据类别来自其两份安全公告；两家的调查都仍在进行，Cursor 称若有新信息会直接通知客户，Fireworks 明写「调查可能揭示更多信息」。
- 「由 Fireworks 暴露」是 Cursor 的归因表述；Fireworks 公告未逐字确认这一具体 key 的暴露路径，本文按各自出处标注，不替任何一方判定责任。
- 第三方技术细节（66 行 loader、非管理员隧道外连、窗口后 8 小时首次活动、MITRE 映射）来自 OpenSourceMalware / Expel / 微软 / Socket 等独立分析，与厂商口径并列呈现。
- 本文未下载 VSIX、未运行整改脚本、未连接任何 IOC 地址；IOC 仅作为检测项转述，具体值请以 Cursor 10-29 通告（10-30 更新版）为准。
- 10-29 通告自身在 10-30 修正过受影响版本与 IOC，引用旧版哈希或只查 2.1.313 会漏。

## 七、结论

这起事件最该被记住的是那条从一把供应商密钥走到开发者机器的完整凭据链，而非「最多 5000 台机器装了冒牌扩展」：历史训练数据里残留的 secret、内部 SaaS 的横向可达、分发缓存的可写权限，每一环单看都不致命，串起来就是一次供应链投毒。

Cursor 的处置算完整 —— 撤 key、全量轮换、下线市场、重建、迁走推理流量、加 secret scanning、重部署生产、请外部取证、逐一通知；Fireworks 也把 LLMJacking 归因与硬化措施公开了。但对读者更有用的，是把这份复盘当成一次自查：你的共享桶里有没有没脱敏的历史数据，你的第三方凭证能不能在别处使用，你的缓存有没有和源站做签名校验，以及你的开发机在卸载一个扩展之后，还留着什么。

## Sources

- Cursor《An update on our recent security incident》（2026-11-13）：<https://cursor.com/blog/security-incident-update>
- Cursor《Security notice — malicious version of Anthropic.claude-code (2.1.312 and 2.1.313)》（2026-10-29，10-30 更新）：<https://cursor.com/blog/claude-code-extension-security-notice>
- Fireworks AI《October 2026 security incident》：<https://fireworks.ai/security/bulletins/october-2026-security-incident> ｜《Update on October 2026 security incident》：<https://fireworks.ai/security/bulletins/october-2026-security-incident-update> ｜ 索引：<https://fireworks.ai/security/bulletins>
- The Hacker News《Official Claude Code Extension on Cursor Marketplace Trojanized with Persistent SSH Backdoor》：<https://thehackernews.com/2026/10/official-claude-code-vs-code-extension.html>
- Expel《Fake Claude Code extension in Cursor: How to find the backdoor》：<https://expel.com/blog/blog-fake-claude-code-extension-cursor-ssh-backdoor>
- 微软安全博客（经 THN 转述）：<https://www.microsoft.com/en-us/security/blog/2026/10/30/inside-malicious-claude-code-branded-cursor-extension-persistent-ssh-backdoor/> ｜ Socket 分析：<https://socket.dev/blog/claude-code-extension-compromise>
- Dark Reading：<https://www.darkreading.com/cyberattacks-data-breaches/devs-trojanized-claude-code-extension-cursor> ｜ Field Effect：<https://fieldeffect.com/blog/trojanized-claude-code-extension-distributed-cursor-marketplace>
