---
title: "一个邮箱地址就能拿到 root：GNU Savannah 被攻破，他们本可以给 Bash 推一个后门"
date: 2026-11-01
slug: gnu-savannah-hacktron-backdoor-bash
tags: [GNUSavannah, Savane, Bash, FSF, 供应链安全, 命令注入, Shell注入, OverlayFS, GameOverLay, CVE-2023-2640, CVE-2023-32629, USN-8255-1, Hacktron, 授权绕过, 私有文件访问, 邮件列表管理, xz后门, 后门植入, 安全研究, 负责任披露]
category: 安全/事件分析
author: FreeLAMP.com
original_source: "⭐ 一手核对：Hacktron《Securing Internet-Critical Software: How We Could Have Backdoored Bash》（2026-10-30）+ FSF 官方事件报告 savannah-20260807.pdf（2026-08-07）+ LWN.net 报道（2026-10-31）+ NVD 的 CVE-2023-2640 / CVE-2023-32629 + Ubuntu USN-8255-1"
original_date: 2026-11-01
original_url: "https://lwn.net/Articles/1104262/"
description: "2026 年 3 月 7 日发布的 Savane 3.17-c369 里有一个命令注入漏洞：它把用户账户的邮箱地址拼进一条交给 gpg 的 shell 命令字符串里，于是注册一个邮箱叫 `touch${IFS}/tmp/x`@attacker.example 的账号，再点一下「测试 GPG 密钥」，命令就会以 web 服务用户身份在服务器上执行。Hacktron 用它拿到了超级用户、冒充了 Bash 维护者、确认可以把带 push 权限的 SSH 密钥加进上游 Bash 仓库 —— 然后停手了。提权那一步用的是 2023 年的两个 OverlayFS 漏洞（CVE-2023-2640 / CVE-2023-32629），而 Savannah 跑的 Trisquel 11 的 5.15 内核直到 2026-05-07 才拿到修复 —— 比报告早 4 天。本文核对了 FSF 的官方事件报告全文，还发现一个耐人寻味的细节：FSF 复核后把 Hacktron 报的 8 个问题中，有 2 个判定为误报（XSS），且明确表示「既未发现敏感项目数据或凭据被访问，也不认为软件供应链被破坏」。"
published: true
---

> ⭐ **本文核对的一手材料**：
> - **[Hacktron：Securing Internet-Critical Software: How We Could Have Backdoored Bash](https://www.hacktron.ai/blog/hacking-gnu-savannah)**（**2026-10-30**，含完整利用链、9 步链条图、26 个漏洞清单、披露时间线）
> - ⭐ **FSF 官方事件报告**：[savannah-20260807.pdf](https://static.fsf.org/nosvn/security/savannah-20260807.pdf)（**2026-08-07**，全文核对 —— 含对每个 finding 的逐条复核结论）
> - **[LWN.net：How We Could Have Backdoored Bash](https://lwn.net/Articles/1104262/)**（corbet，2026-10-31）
> - [NVD — CVE-2023-2640](https://nvd.nist.gov/vuln/detail/CVE-2023-2640) / [CVE-2023-32629](https://nvd.nist.gov/vuln/detail/CVE-2023-32629)（均 7.8 High）
> - [Ubuntu USN-8255-1](https://ubuntu.com/security/notices/USN-8255-1)（5.15.0-177.187 为首个修复版本）
> ⚠️ **本文为**解读**。**不提供可运行的利用代码** —— 文中出现的邮箱 payload 仅为说明漏洞机理，且**该漏洞已被修复**。

## 一句话结论

**⭐ 而这个事件最值得记的，不是「GNU 被黑了」，而是这个链条的形状：**

> **一个邮箱地址 → 一条 shell 命令 → web 服务用户 → 一个 2023 年的 OverlayFS 漏洞 → root → 一个备份服务器 → 而从 root 到「给 Bash 推后门」，只差往一个 SSH 密钥页面里贴一个公钥。**

**⭐ 中间每一步都「普通」得不像攻击 —— 而这正是它可怕的地方。**

## 一、为什么是 Savannah

**⭐ 而「为什么挑 Savannah」这个问题，Hacktron 自己的回答就点到了要害：**

> **「Savannah is where much of the GNU userland lives, including **Bash and Coreutils**, which provides commands such as `ls`, `cp`, and `rm`. **It holds the repositories, the maintainer accounts, and the SSH keys that decide who can push.**」**
>
> **「Code that lands there gets packaged by distributions and installed on millions of machines, and the **xz backdoor** showed what one compromised link in that chain can do.」**

**⭐ 我把这条链拆开 —— 因为它精确地定义了「供应链攻击」的最小必要条件：**

```
① 仓库（代码落地的地方）
② 维护者账号（身份）
③ SSH 密钥（授权凭证）
   ↓ 三者合一 =
可以以维护者身份推送的权限
   ↓
下游发行版打包 → 装机量以亿计
```

**⭐ 而「xz 后门」那个类比，我认为是最有说服力的一个参照 —— 因为它证明这条路是**真实走过**的。**

## 二、⭐⭐ 漏洞本体：邮箱地址被拼进 shell 命令

### 2.1 那个邮箱地址

**⭐ 而 Hacktron 展示的那行注册信息，是全文最直观的一行：**

```
a`touch${IFS}/tmp/savane-rce-proof`@attacker.example
```

**⭐ 而他们自己的解说只有一句：**

> **「You know where this is going, right?」**

**⭐ 我解释一下这三个部件各自的作用：**

| 部件 | 作用 |
|---|---|
| **反引号 `` ` ``** | ⭐ **命令替换** —— shell 会先执行反引号里的内容，再把结果当作命令的一部分 |
| **`${IFS}`** | ⭐ **IFS（内部字段分隔符，通常是空格）** —— 用参数展开绕开「不能有空格」的校验，展开后等价于一个空格 |
| **整个邮箱** | ⭐ **必须看起来像一个合法邮箱** —— 因为它会出现在 GPG 密钥的 UID 里，会被用来校验密钥归属 |

**⭐ 而「`${IFS}` 绕开空格校验」这个技巧，是这类绕过里最有教学价值的一处：**

**—— 校验器检查的是「字符串里有没有空格」，而攻击者要的是「shell 展开后有空格」。** **`${IFS}` 是一个变量展开，展开发生在 shell 里，不在校验器眼里。**

### 2.2 ⭐ 完整的四步

**⭐ Hacktron 给的利用步骤非常清晰：**

> **「Exploiting it takes four steps:」**
>
> **1. Register with the payload above as your email address, or change an existing account's email address to it. The app accepts it.**
> **2. Open `/my/admin/change.php?item=gpgkey`.**
> **3. Paste any GPG key and click "Test GPG keys".**
> **4. The command inside the email runs on the server as the web server user.**

**⭐ 我把这条攻击路径画出来：**

```
① 注册（邮箱带 payload）
        ↓
② 打开「管理 GPG 密钥」页面
        ↓
③ 点「Test GPG keys」—— 这是完全正常的功能
        ↓
④ 服务器拿你的邮箱去跟 gpg 交互 → shell 执行反引号里的命令
```

**⭐ 而第 3 步值得特别指出 —— **攻击者触发的是一个完全正常的管理功能。** **没有任何「恶意请求」的痕迹，Web 应用日志里看到的就是一次普通的密钥测试。**

### 2.3 ⭐⭐ 而 sink 在哪里：数据被当成了代码

**⭐ 这一段是全文技术价值最高的部分，因为 FSF 官方报告也独立确认了它：**

**Hacktron 的描述：**

> **「The email is appended to `$options` as plain text, `$options` is concatenated into `$cmd`, and `utils_run_proc()` hands that string to `proc_open()`. **With a string command, PHP runs it through `/bin/sh`.** The shell sees our backticks and runs whatever is between them before `gpg` even starts.」**

**⭐ 我把这条数据流拆成四步，每一步都是一次「类型退化」：**

| 步骤 | 状态 |
|---|---|
| ① 用户填的邮箱 | **数据** |
| ② 追加到 `$options` | **仍是数据**（但已与其它选项文本拼接） |
| ③ 拼进 `$cmd` | ⭐ **变成代码的一部分** |
| ④ 交给 `proc_open()` | ⭐ **PHP 用字符串命令 → 走 `/bin/sh` → shell 解释** |

**⭐ 而 FSF 官方报告的表述更精确：**

> **「HCK-001 did not compromise the integrity of the GPG key itself, instead demonstrating that an attacker could **append an arbitrary email address to the command savane used when checking the GPG key**. **That email address was not handled safely by savane as a separate command argument**, allowing special characters in the address to be interpreted by the system shell.」**
>
> **「The fix for HCK-001 was to **treat the email address as data passed safely to the GPG process rather than as text assembled into a shell command string**.」**

**⭐ 我想把这句 fix 的描述单独拎出来，因为它就是**这类漏洞的通用修法**：**

> **⭐ 「把数据当作数据传，而不是拼进命令字符串。」**

**—— 而这本质上就是 shell 注入的经典对策：不要用字符串命令，用参数数组。**

### 2.4 ⭐ 而漏洞窗口：两个月

**⭐ 这是我认为最该被记住的一个数字：**

**FSF 官方报告：**

> **「The first part required a vulnerable entry path in GNU Savannah that was **introduced in the March 7, 2026 release of savane (version 3.17-c369)** and affected both **savannah.gnu.org** and **savannah.nongnu.org**, so **the window was about two months**.」**

**⭐ 而「同时影响 savannah.gnu.org 与 savannah.nongnu.org」这一条也值得记 —— 因为这说明**一个公共 forge 平台被攻破，影响面是它托管的所有项目**，不只是它自己那个域名。**

## 三、⭐⭐ 从 shell 到超级用户

**⭐ 而这一段的每一步都值得单独讲，因为它们各自代表一类「典型失误」。**

### 3.1 第一步：反向 shell

**⭐ 而拿到 web 服务用户之后，Hacktron 做的第一件事是：**

> **「To see how far it went, we swapped the payload for a **reverse shell** and landed on the backend as the web server user.」**

### 3.2 ⭐⭐ 第二步：数据库凭据是明文可读的

**⭐ 而这一步是整条链里最「简单」也最值得警惕的一步：**

> **「The web server user can read Savane's configuration, which includes the **database credentials, so there was nothing to crack**.」**

**⭐ 「nothing to crack」—— 没有加密，没有哈希，什么都不用破解。**

**⭐ 而我把这归为一个通用模式：**

> **⭐ 攻击链上最容易被忽略的一环，往往不是「最难攻破」的那个，而是「**配置文件的权限设得太宽**」的那个。**

**—— 一个能读配置文件的低权限用户，等于拿到了数据库的完整权限。而数据库里存着用户资料、邮件列表、SSH 密钥关联、会话……**

### 3.3 ⭐ 第三步：把自己设成 superuser

**⭐ 而接下来这一步，简单到有点难以置信：**

> **「We set the `superuser` flag on our own account, `harshjaiswal`, and reloaded the page.」**
>
> **「Logged in as superuser on savannah.gnu.org」**

**⭐ 我想指出这里的形态 —— **不是「提权」，是「**改一个字段**」。**

**⭐ 而这个字段显然来自客户端可提交的数据 —— 因为它就存在自己的账户记录里。**

**⭐ 这引出 FSF 复核时的一个独立发现（HCK-002）：**

> **「HCK-002 concerned GNU Savannah group configuration. The concern was that **an authorization check could be skipped for the site-wide administrative group**, allowing a normal authenticated user to reach configuration logic intended for privileged users.」**

**⭐ 注意 FSF 对它的定性：「**This primarily affected data integrity**」** —— 主要影响是**数据完整性**，而不是直接的权限提升。**

## 四、⭐⭐ 冒充 Bash 维护者：只差贴一个公钥

**⭐ 这是全文最惊心动魄的一段，而它的可怕之处在于「差多少」。**

### 4.1 维护者的 SSH 密钥页面

**⭐ Hacktron 的描述：**

> **「That's his SSH key page, with an **empty slot for one more**. **Savannah's Git hosting is keyed off these entries**, so adding a key here grants push access to `bash.git` as the maintainer.」**

**⭐ 我把这三句话拆开：**

| 事实 | 含义 |
|---|---|
| **「his SSH key page」** | ⭐ **维护者账号的 SSH 密钥设置页** |
| **「with an empty slot for one more」** | ⭐ **页面上就有一个「再加一个公钥」的输入框** |
| **「Savannah's Git hosting is keyed off these entries」** | ⭐ **仓库的 push 权限直接绑定这些条目** |

**⭐ 而最关键的一句：**

> **「**We confirmed the page accepted edits and stopped there. We did not add a key and we did not touch the repository.**」**

**⭐ 我想请读者注意这个「停手」的位置 —— 因为它是全文最精确的一处克制：**

**—— 他们确认了「这个页面可以被编辑」（漏洞存在且可利用），但没有真的加密钥。**

**⭐ 而 Hacktron 明确写出了这意味着什么：**

> **「An attacker in this position could have pushed a commit to upstream Bash under Chet's name and **done the same to Coreutils or any other project on Savannah**.」**

**⭐ 「under Chet's name」** —— ⭐ **以 Chet 的名义推送提交。** **而 Bash 与 Coreutils 的维护者身份意味着签名可信。**

### 4.2 ⭐⭐ 而这一步与 xz 的对照

**⭐ 我把 xz 后门的链条拿来对照，会发现两者惊人地相似：**

| | **xz 后门（2024）** | **本次（2026，未遂）** |
|---|---|---|
| **入口** | ⭐ **上游压缩库 tarball 的构建脚本** | ⭐ **forge 的 GPG 密钥测试功能** |
| **中间跳板** | ⭐ **构建时注入 → 落到发行版** | ⭐ **RCE → 超级用户 → root** |
| **终点** | ⭐ **发行版打包的 liblzma** | ⭐ **能 push 到上游 Bash 仓库** |
| **谁批准了代码** | ⭐ **上游发布者本人** | ⭐ **（如果实施）同样会是上游维护者本人** |

**⭐ 而我认为最值得注意的差别是 —— xz 那次是「上游自己放进去的」（社会工程学路径），而这次是「**攻击者能冒充上游**」。**

**—— 也就是说：这次路径绕过了 xz 那套「需要说服上游」的门槛，直接攻击了**授权本身**。**

## 五、⭐⭐ Root：靠一个 2023 年的 OverlayFS 漏洞

**⭐ 而提权这一步，是我认为全文最有意思的「时间巧合」。**

### 5.1 漏洞组合

**⭐ FSF 官方报告：**

> **「The second part of the exploit involved privilege escalation via **two vulnerabilities in OverlayFS, CVE-2023-2640 and CVE-2023-32629**.」**

**⭐ 而这两个漏洞的 CVSS 都是 7.8 High（`AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H`）—— 我实测核对了 NVD。**

**CVE-2023-2640 的描述：**

> **「an unprivileged user may **set privileged extended attributes on the mounted files, leading them to be set on the upper files without the appropriate security checks**.」**

**CVE-2023-32629 的描述：**

> **「Local privilege escalation vulnerability in Ubuntu Kernels overlayfs `ovl_copy_up_meta_inode_data` **skip permission checks** when calling `ovl_do_setxattr`.」**

**⭐ 而这两个漏洞合起来被称为 GameOver(lay) —— Hacktron 引用了 Wiz 的分析。**

### 5.2 ⭐⭐ 而最关键的：修复的时间差

**⭐ 而这一段的时间线，我认为比漏洞本身更值得记：**

**FSF 官方报告：**

> **「Canonical addressed the affected **5.19 and 6.2 kernel series in 2023**, but the **5.15 kernel shipped with Ubuntu 22.04 LTS was not marked fixed until USN-8255-1 on May 7, 2026**, which gives **5.15.0-177.187 as the first fixed version**.」**

**⭐ 而 Hacktron 的时间线更完整：**

> **「2026-05-07 | Canonical publishes USN-8255-1, fixing GameOver(lay) in the 5.15 kernel」**
> **「2026-05-11 | We report RCE, root access, and access to the Bash repository」**
> **「2026-05-14 | FSF installs the fixed kernel and removes our account」**

**⭐ 我把这个时间差算出来：**

```
2023 年      Canonical 修了 5.19 与 6.2
              ↓ 5.15（Ubuntu 22.04 LTS 的默认内核）没修
              ↓
2026-03-07   Savane 3.17-c369 发布，引入命令注入
              ↓
2026-05-07   Canonical 终于修 5.15（USN-8255-1，5.15.0-177.187）
              ↓
2026-05-11   Hacktron 报告（距 Canonical 修复 4 天）
              ↓
2026-05-14   FSF 装上修复内核 + 移除账号（距报告 3 天）
```

**⭐ 而 FSF 报告里有一句，把这个时间差讲得非常到位：**

> **「We installed the corresponding fixed kernel, **5.15.0-177.187+11.0trisquel31, on May 14, 2026, three days after receiving the report, and one week after Canonical published its fix.**」**

**⭐ 我想指出的关键点：**

**—— 那个 2023 年的 OverlayFS 漏洞之所以还能用，是因为 **Ubuntu 22.04 的 5.15 LTS 内核在 2026 年 5 月之前一直没拿到修复**。**

**⭐ 而这跟本号前几天写的 MPTCP 那篇恰好形成了一个漂亮的对照：**

| | **MPTCP（2026-10-30）** | **GameOver(lay)（本次）** |
|---|---|---|
| **漏洞引入** | 2015 年 | 2023 年 |
| **修复 upstream** | 2026-10-01 | 2023 年（5.19/6.2） |
| **⭐ 但 LTS 分支** | ⭐ **backport 到各 stable** | ⭐ **5.15 LTS 拖到 2026-05-07** |
| **被利用的窗口** | ⭐ **11 年** | ⭐ **约 2.5 年（5.15 未修期间）** |

**⭐ 而更值得警惕的是这个模式：**

**—— 同一个漏洞，在新版本上修好了，而 LTS 分支上没跟上，于是 LTS 用户继续暴露。**

**—— 而 Savannah 跑的正是 **Ubuntu 22.04 的 5.15**。**

### 5.3 ⭐ 从 root 到备份服务器

**⭐ 而最后一步，是我认为这个事件的「终局」所在：**

**Hacktron：**

> **「As root, we found a key that let us SSH to a **GNU backup host** as the `gnubackup` user.」**
>
> **「At that point, we had **root on the forge**, **access to its backups**, and **the ability to act as any maintainer**. **We stopped doing recon and wrote the report.**」**

**⭐ 我注意到「access to its backups」这七个字 —— 因为备份服务器上放着什么，不言自明。**

**⭐ 而「ability to act as any maintainer」—— 这句话把前面所有的步骤汇总成了一个结论。**

## 六、⭐⭐ 剩下的 Savane：26 个漏洞

**⭐ 而 RCE 只是冰山一角 —— 这才是整个报告最惊人的部分。**

**⭐ Hacktron 的做法：**

> **「After the initial report, we kept Hacktron running on the Savane codebase, **which descends from the 2001 SourceForge code**. It produced **33 findings**; we threw out **7 false positives** and sent the FSF the remaining **26 (2 critical, 6 high, 16 medium, 2 low)** with file paths, line numbers, and reproduction steps.」**

**⭐ 而「descends from the 2001 SourceForge code」这个背景解释了为什么漏洞密度这么高 —— **这是一份二十多年前的老代码。**

### 6.1 严重的几个

**⭐ Hacktron 的清单里，前几个我原样列出：**

| ID | 严重度 | 问题 |
|---|---|---|
| **HCK-001** | **Critical** | ⭐ **通过 GPG 密钥测试的邮件地址做命令注入 → RCE** |
| **HCK-002** | **Critical** | ⭐ **站点级管理员组配置的授权绕过**（`siteadmin/triggercreation.php`）** |
| **HCK-003** | High | ⭐ **任何组成员都能删除该组的邮件列表** |
| **HCK-004** | High | ⭐ **任何用户都能更改任何组的 tracker 通知地址** |
| **HCK-006** | High | ⭐ **任何组成员都能重置邮件列表管理员密码** |
| **HCK-008** | High | ⭐ **私有文件访问信任请求里的 `file_uid` 参数，而不是会话** |
| **HCK-010** | Medium | ⭐ **会话劫持：跨域 SSO 把 `session_uid` 和 `session_hash` 放在 URL 里传** |
| **HCK-012** | Medium | ⭐ **密码重置与邮件变更的确认哈希永不过期** |
| **HCK-017** | Medium | ⭐ **真实名字字段的存储型 XSS（该字段只剥离 `<`）** |

### 6.2 ⭐ 而 FSF 的复核结论，比报告本身更有价值

**⭐ 这是我认为 FSF 那份官方报告最值得读的部分 —— 因为它对每个 finding 都给了自己的判断，而且不完全认同 Hacktron 的评级。**

**① 两个 XSS 被判定为误报：**

> **「HCK-005 and HCK-007 were reported as cross-site scripting issues, but **review by FSF staff determined them to be false positives**. The reported payloads did not execute because the relevant inputs were **sanitized elsewhere in the savane codebase** before being processed by the web application or server.」**

**② 而对「自动化扫描得出的发现」，FSF 说得更直接：**

> **「When automated software scans source code repositories, it often **makes assumptions about the configuration of the software and the live systems it runs on that are untrue in practice**. In multiple cases, FSF staff were **either unable to reproduce the vulnerabilities** reported to us or **were able to identify them as false positives**.」**

**⭐ 而即便对那些确实存在的漏洞，FSF 也在调整影响评估 —— 比如 HCK-006：**

> **「The practical impact of HCK-006 was **more conditional than the original severity label suggested**, because triggering a password reset **does not necessarily give an attacker control of the mailing list**, unless the attacker can access the recipient inbox or change where the password reset notice is sent.」**

**⭐ 我认为这个「**实际影响比原标签更有限**」的表述很专业 —— 它没有说「你们报错了」，而是说「**触发条件比标签暗示的更多**」。**

**③ 而对 HCK-008（私有文件访问），FSF 的定性更值得注意：**

> **「This does not mean every private file was necessarily accessed, but it was an important authorization flaw **because the server was trusting information supplied by the requester instead of checking the relevant access controls**.」**

**⭐ 「**信任请求方提供的信息，而不检查访问控制**」—— 这是 IDOR 类漏洞的标准描述。**

### 6.3 ⭐ 而修复方式：重构，不是逐个打补丁

**⭐ 这一点我觉得是整个事件里对其他 forge 运营者最有参考价值的：**

**FSF 官方报告：**

> **「GNU volunteers worked to review and **rewrite** the affected code, **fixing multiple issues reported by the researchers at once by refactoring the savane software**.」**
>
> **「The authorization bugs were fixed through a **refactor rather than individual patches**.」**

**⭐ 而 Hacktron 那边也确认了这一点：**

> **「The FSF treated it as a full compromise: it patched the kernel, audited access controls, databases, and logs, and warned the operator of the other public Savane instance. **The authorization bugs were fixed through a refactor rather than individual patches.**」**

**⭐ 我认为「逐个修 vs 重构」这个选择，反映了对问题本质的判断：**

| | 逐个打补丁 | 重构 |
|---|---|---|
| **处理的问题** | 个别 bug | ⭐ **「授权检查依赖了什么」这个模式** |
| **遗留风险** | 同类问题可能还在别处 | ⭐ **模式本身被消除** |
| **成本** | 低 | 高 |

**—— 而 26 个漏洞里一大半是「授权检查该用会话、却用了请求参数」这一类模式，所以重构是对的。**

### 6.4 ⭐ 而 FSF 还做了一件超出报告范围的事

**⭐ 这一条我觉得很值得单独提：**

**FSF 官方报告：**

> **「We also **contacted the operator of another known public savane instance** so that its maintainers could review their environment and apply any necessary patches.」**

**⭐ 而 Hacktron 那边的表述：**

> **「it patched the kernel, audited access controls, databases, and logs, and **warned the operator of the other public Savane instance**.」**

**⭐ 我认为这一条体现了 FSF 的处理超出了「自己没事就行」：**

**—— 漏洞在 Savane 这个**软件**里，所以**其它部署同样受影响**。**FSF 主动通知了另一个公开实例的运营方。**

## 七、⭐⭐ FSF 的最终结论：没有供应链被破坏

**⭐ 而这一节我认为对读者判断风险等级同样重要 —— 因为标题党容易让人以为「Bash 被投毒了」。**

**FSF 官方报告（原文）：**

> **「We have completed a detailed internal inspection of **access controls, databases, and logs** and **believe that neither sensitive project data nor credentials were accessed, nor that Savannah's software supply chain was compromised**.」**
>
> **「The initial vulnerability was serious and the exploit demonstrated risk. We believe we took the proper steps to address the security issues disclosed to us and protect our community of GNU developers as well as free software users around the world.」**

**⭐ 而「internal inspection of access controls, databases, and logs」这三个词，说明他们**真的查了日志**—— 这不是一句套话。**

**⭐ 而 FSF 报告的标题也值得注意：「**Update on** GNU Savannah security issue」** —— 它是一份「更新」，而不是「入侵通报」。**

**⭐ 而 2026-06-19 发布的初步声明（FSF 官方报告里提到）也在网上 —— 那份更早。**

**⭐ 所以完整的时间线是：**

| 日期 | 事件 |
|---|---|
| **2026-03-07** | ⭐ **Savane 3.17-c369 发布，引入漏洞** |
| **2026-05-07** | Canonical 发布 USN-8255-1，修 5.15 内核的 GameOver(lay) |
| **2026-05-11** | ⭐ **Hacktron 报告**（RCE + root + Bash 仓库访问） |
| **2026-05-12** | Savannah 管理员 Corwin Brust 当晚回应，确认 30 天披露窗口 |
| **2026-05-14** | ⭐ **FSF 装上修复内核 + 移除研究者的账号**（报告后 3 天） |
| 2026-05 月 | Hacktron 提交余下 25 个发现 |
| **2026-06-19** | FSF 发布初步声明 |
| **2026-08-07** | ⭐ **FSF 发布完整事件报告 + Savane 补丁** |
| **2026-10-30** | Hacktron 发布完整技术分析 |
| **2026-10-31** | LWN 报道 |

**⭐ 而我注意到一个细节 —— 05-12 确认 30 天披露窗口、05-14 就装补丁删账号，而完整补丁到 08-07 才发布。** **这个「先止血、后详查」的顺序是对的。**

## 八、⭐⭐ 我的评价

### 8.1 ⭐⭐ 而这个事件最该被记住的，是「链条的每一环都很普通」

**⭐ 我想先说清楚为什么这个事件值得写 —— 因为它的技术成分其实不高。**

| 环节 | 技术难度 |
|---|---|
| 命令注入 | ⭐ **经典手法**（反引号 + `${IFS}` 绕空格校验）** |
| 数据库凭据 | ⭐ **明文可读** |
| 提权 | ⭐ **两个公开的 2023 年内核漏洞** |
| 冒充维护者 | ⭐ **一个「加公钥」的表单** |

**⭐ 而我把这四个环节并排放，是想说明一件事：**

> **⭐⭐ **攻击链的强度取决于「最弱那一环」乘上「链条长度」，而不是取决于任何一环的技术含量。**
> **⭐ 而在这个案例里，每一环都是「任何读过一点安全资料的人都知道的」—— 但串起来就是 root + 可以给 Bash 推后门。**

### 8.2 ⭐⭐ 而第二件事：这个漏洞是**新引入**的，不是老代码遗留

**⭐ 我认为这一点特别值得注意，因为它反直觉：**

**—— 「Savane 继承自 2001 年的 SourceForge 代码」这个背景，会让人以为漏洞是历史包袱。**

**⭐ 但 HCK-001 是 2026 年 3 月 7 日引入的。** **而两个 OverlayFS 漏洞是 2023 年的。**

**⭐ 而 FSF 的修复方式是「重构」—— 这意味着：** ⭐ **这次的教训不是「老代码要审计」，而是「**新代码也会引入同类问题**」。**

**⭐ 我把这句话说得更具体一点：**

**—— 一个 25 年的老项目，在 2026 年做了一次例行发布，就引入了一个能让任何人拿到 root 的漏洞，而且这个漏洞是「命令注入」这种教科书级别的类型。**

**⭐ 而它能被引入的直接原因，是一个非常普通的技术选择：**

> **⭐ 把「数据」拼进「命令字符串」。**

**⭐ 而这正好接上本号此前写过的几篇 —— 从 PHP2Shell 的 `longjmp()`、到 TeamViewer 的 32 位乘法、到 MPTCP 的 `kfree()` vs `kfree_rcu()`：**

**⭐ 我发现这几篇有一个共同点，而这个共同点比任何单个漏洞都更值得记住：**

> **⭐⭐ **所有这些漏洞，触发它们的都是一次「本该是数据的东西被当成了代码/指令/尺寸」。**
> **⭐ 而它们的共同解法也一致：**
> **⭐ 「**让它待在它该在的类型里**」** ——
> **⭐ 邮件地址当参数传、长度按 64 位算、指针按 RCU 约定释放。**

**⭐ 而这三个案例的修复难度差异极大：**

| | 修复成本 |
|---|---|
| **Savane HCK-001** | ⭐ **改一处拼接方式** |
| **TeamViewer** | ⭐ **改两个 `kfree()` 为 `kfree_rcu()`** |
| **MPTCP** | ⭐ **改两个 `kfree()` 为 `kfree_rcu()`** |

**—— 而攻击链的长度，是完全不同的量级。**

### 8.3 ⭐⭐ 而第三件事：我认为「停手」这个细节，比技术细节更值得学

**⭐ 我想回到 4.1 节那个「停手」的位置 —— 因为我认为它是整个事件里最有教学价值的一处。**

**Hacktron 确认了：**
- ✅ **「We confirmed the page accepted edits」** —— 漏洞存在且可利用
- ❌ **「We did not add a key and we did not touch the repository」** —— 没有真的加密钥

**⭐ 而 FSF 的配合同样值得看：**

> **「Corwin Brust, a Savannah administrator, **replied the same night**.」**
>
> **「We thank the Hacktron researchers for bringing these issues to our attention and for **continuing to work with FSF staff and GNU volunteers** as we investigated and addressed their findings.」**

**⭐ 我想指出这个「同夜回复」的含义 —— 因为它决定了后面五个月整个流程的基调：**

**—— 从「收到报告当夜就有人回应」，到「3 天后装补丁删账号」，到「接受对方继续审计以找出更多问题」，到「发完整报告并致谢」。**

**⭐ 而对比一下另一种可能的处理方式（现实中更常见）：**

**—— 把报告当作「攻击事件」处理、先追责、先封锁讨论。** **那样的话，剩下那 25 个漏洞不会存在。**

**⭐ 我认为这个案例真正证明了「负责任披露」的价值不在于漏洞本身有多严重，而在于：**

> **⭐ **一个愿意把发现分享出来的研究者，和一个愿意配合的维护者，能一起把 26 个问题变成 26 个修复。**
> **⭐ 如果其中任何一环是防御性的，剩下的 25 个就会留在那里。**

### 8.4 ⭐ 而最后：对自建 forge 运营者的三条具体建议

**⭐ FSF 报告的最后一段其实是给运营者的建议，我把它单独提出来：**

> **「Operators of self-hosted savane instances should update to the latest release and may direct questions about upgrading, mitigation, or reviewing their systems to the Savannah Hackers Public mailing list.」**

**⭐ 而我把 FSF 与 Hacktron 的材料综合起来，给三条更普适的：**

**① 「命令拼接」是自建 Web 系统的头号漏洞来源。**

**⭐ 而 HCK-001 的修复思路就是通用答案：把数据当数据传。** **如果你的代码里有任何「把用户输入拼进一条命令字符串」的地方，它就是一个待爆的雷 —— 而这个雷不需要复杂利用就能触发。**

**② ⭐ 检查 LTS 分支的补丁同步。**

**⭐ 这个案例里，2023 年的 OverlayFS 漏洞在 5.15 LTS 上拖了两年多。** **而如果你的系统跑的是某个 LTS 基线，那个基线上的补丁状态才是真正决定你安全与否的东西 —— 而不是「上游最新版修了没有」。**

**⭐ 而这跟本号前两天写的 CVE-2026-98432 那篇的结论完全一致：**

> **⭐ 「There is no single upstream version string that accurately labels every vendor kernel.」**

**③ ⭐ 审计「谁能改配置」和「谁能加密钥」。**

**⭐ HCK-002、HCK-003、HCK-004、HCK-006、HCK-008 全部是这一类：授权检查用了「请求里的参数」而不是「会话里的身份」。**

**⭐ 而 FSF 用「重构」而不是逐个打补丁来修 —— 这本身就说明了**问题的规模**：不是几个洞，是一类模式。**

## Sources

- ⭐ 一手：[Hacktron — Securing Internet-Critical Software: How We Could Have Backdoored Bash](https://www.hacktron.ai/blog/hacking-gnu-savannah)（2026-10-30，含完整利用链、9 步链条、26 个漏洞清单、披露时间线）
- ⭐ 一手（全文核对）：[FSF 官方事件报告 savannah-20260807.pdf](https://static.fsf.org/nosvn/security/savannah-20260807.pdf)（2026-08-07，含对每个 finding 的逐条复核结论与「未发现供应链被破坏」的结论）
- ⭐ 一手：[LWN.net — How We Could Have Backdoored Bash](https://lwn.net/Articles/1104262/)（corbet，2026-10-31）
- ⭐ 一手（实测）：[NVD — CVE-2023-2640](https://nvd.nist.gov/vuln/detail/CVE-2023-2640) / [CVE-2023-32629](https://nvd.nist.gov/vuln/detail/CVE-2023-32629)（均 7.8 High，OverlayFS 权限检查跳过）
- ⭐ 一手（实测）：[Ubuntu USN-8255-1](https://ubuntu.com/security/notices/USN-8255-1)（2026-05-07，5.15.0-177.187 为首个修复版本）
- 一手：[Wiz — Ubuntu OverlayFS vulnerability（GameOver(lay)）](https://www.wiz.io/blog/ubuntu-overlayfs-vulnerability)
- 一手：[NVD — CVE-2023-32629 关联的 xz 后门背景](https://www.openwall.com/lists/oss-security/2024/03/29/4)
- 相关：FSF 2026-06-19 的初步声明（经 2026-08-07 报告引用）

---

（说明：所有引号内内容与时间线均来自上述一手材料；**第八节的「数据当数据」归纳、与本号此前几篇漏洞的横向对照、以及「停手这个细节更值得学」的判断为笔者观点**。**本文不提供可运行的利用代码** —— 文中出现的邮箱 payload 仅用于说明漏洞机理，且该漏洞已被修复。）
