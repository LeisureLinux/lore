---
title: "一个 CA 说了「4」，一个 C 库对超长密钥返回「*」：OpenSSH 认证绕过如何在 Alpine 上凑齐"
date: 2026-11-05
slug: openssh-password-auth-bypass-musl-crypt
category: 技术/解读
author: FreeLAMP.com
original_source: "⭐ 一手核对：Alpine Linux 官方安全公告（2026-11-05）＋ OpenSSH 上游修复 commit 4353fdc43ef646c43a8dda7025cc1a898caf1482（Damien Miller，2026-11-04，「avoid password authn bypass」）及其父提交对比 ＋ musl libc 的 crypt_sha256.c / crypt_sha512.c / crypt_des.c 源码（KEY_MAX 256 与错误返回 \"*\"）＋ openssh-portable 的 openbsd-compat/xcrypt.c 修复前版本 ＋ Alpine 包站 openssh 10.6_p2-r0（build time 2026-11-05 09:05:19）＋ OpenSSH 10.6 release notes"
original_date: 2026-11-05
original_url: "https://alpinelinux.org/posts/2026-11-05-openssh-password-authentication-bypass/"
description: "本文解读 2026 年 11 月 5 日 Alpine Linux 官方公告的 **OpenSSH sshd 密码认证绕过**：⭐ **攻击者只要能连到你的 SSH 端口，不需要知道任何密码就能登录 —— 一次连接，必成功，无需重试**。⭐ 机理是一条由三个独立环节凑齐的链：⭐ **① 攻击者需要一个密码字段为 `*` 的账号（⭐ 无密码账号的正常表示）**；⭐ **② 机器上至少还要有另一个用 `$5$`/`$6$` 哈希的账号**（⭐ **一个带密码的用户，就让所有无密码账号变得可达**）；⭐ **③ 攻击者发送一个 257–1024 字节的超长密码** —— ⭐ **而真正的机关在 musl 的 `crypt()`：⭐ key 超过 256 字节时它返回字符串 `\"*\"` 作为错误指示，⭐ 而 `\"*\"` 恰好正是每个「无密码账号」存储字段的内容，⭐ 于是「哈希」与存储值相等，登录成功**。⭐ **本文还核对了 OpenSSH 上游的修复 commit（⭐ 「avoid password authn bypass」，⭐ 提交者的注释很关键：⭐「We do not consider the root cause to be within OpenSSH but we are well equipped to avoid it」），⭐ 逐行比对了修复前后的 `openbsd-compat/xcrypt.c`（⭐ 加了 `MIN_PASSWORD_HASH_LEN 4` 长度下限 ＋ `freezero` 清零 ＋ `xstrdup` 避免 double-free），⭐ 以及 Alpine 给出的逐分支修复版本表（⭐ 从 edge 的 `10.6_p2-r0` 一直到 3.16 的 `9.0_p1-r6`）⭐ 与「升级包不重启守护进程」这个必须强调的操作点。"
published: true
---

> **原文**：Alpine Linux《Security advisory: openssh-server password authentication bypass》（2026-11-05）
> 原文链接：<https://alpinelinux.org/posts/2026-11-05-openssh-password-authentication-bypass/>
> ⭐ **本文依据 Alpine 官方公告、⭐ OpenSSH 上游修复 commit 原文（及其父提交的比对）、⭐ musl libc 的 crypt 实现源码，⭐ 以及 Alpine 包站的实际构建信息。**

## 一、⭐⭐⭐ 先说它有多严重

⭐ **Alpine 公告的第一段，我认为是今年最值得记住的安全通告开头之一：**

> *"An attacker who can reach your SSH port **can log in without knowing any password**. **It takes one connection, works every time, and needs no retries.**"*

⭐ **⭐⭐ 请把这三个短句拆开看，⭐ **每一个都在否定一个通常成立的安全假设：**

| | 通常的假设 | 这条漏洞的实际情况 |
|---|---|---|
| ⭐ **「攻击者需要密码」** | ⭐ 暴力破解需要时间与算力 | ⭐ **⭐ 完全不需要密码** |
| ⭐ **「攻击者需要重试」** | ⭐ 失败可以靠重试累积 | ⭐ **⭐ 一次连接，必成功** |
| ⭐ **「无密码账号登录不了」** | ⭐ `root:*` 意味着锁死 | ⭐ **⭐ 反而成了被利用的条件** |

⭐ **⭐⭐ 而「一次成功」的含义要再往下推一层：⭐ **不需要暴力、不需要时序、⭐ 不需要任何预置条件。⭐ **⭐ 攻击者只要能连到 22 端口，⭐ **发一个 257 字节以上的密码，⭐ **就进去了。**

## 二、⭐⭐⭐ 机理：三个环节凑齐

⭐ **⭐⭐ Alpine 公告把触发条件写得很清楚，⭐ 而我认为把它拆成三个「必须同时成立」的环节，⭐ 是理解这条漏洞的关键。**

### ⭐ 环节一：攻击者需要一个「密码字段为 `*`」的账号

⭐ Alpine 公告：

> *"The attacker needs the name of an account whose password field is `*` (**an account with no password set, which is normal for key-only accounts**)."*

⭐ **⭐ 而这个 `*` 是什么？⭐ **它是 Unix 密码字段的约定：⭐ **一个 `!` 或 `*` 开头的字段表示「这个账号没有可用的密码哈希」。⭐ **⭐**

⭐ **⭐⭐ 而 Alpine 特别指出一个极其常见的现实情况：**

> *"This includes **root**, which ships as `root:*` in the base image **since about Alpine 3.16**."*

⭐ **⭐⭐ 请停一下：⭐ **⭐ Alpine 的基础镜像里，⭐ **root 的密码字段默认就是 `*`。⭐ **⭐ 这意味着几乎每一台 Alpine 机器上，⭐ **都有这个「被利用的前提条件」躺在那儿。**

⭐ **⭐⭐ 而 Alpine 还列出了一整串同类账号：**

- ⭐ **任何用 `adduser` 不设密码创建的 key-only 用户，⭐ 或用 `usermod -p '*'` 的**
- ⭐ **通过 musl-nscd（nslcd、winbind、sssd）从目录服务来的用户 —— ⭐ **「since they have no shadow entry」**
- ⭐ **官方 tiny-cloud 镜像里的 `alpine` 用户**

### ⭐⭐ 环节二：机器上至少还要有另一个带密码的账号

⭐ Alpine 公告：

> *"…and needs the machine to have **at least one other account with a `$5$` or `$6$` password hash**. … **One user with a password is enough: it makes every account without one reachable.**"*

⭐ **⭐⭐ 而这一条是整条链里最反直觉的：⭐ **⭐ 一个跟你毫无关系的、⭐ 甚至你不知道存在的用户有密码，⭐ **就会让所有无密码账号变得可被利用。⭐ **⭐**

### ⭐⭐⭐ 环节三：攻击者发送一个 257–1024 字节的超长密码

⭐ Alpine 公告：

> *"The attacker then sends **a very long password (257 to 1024 bytes)**."*

⭐ **⭐⭐ 而这个数字区间，⭐ **恰好由两个边界夹出来：**

```
257 字节  ← musl 的 KEY_MAX 是 256，所以 257 就超了
1024 字节 ← OpenSSH 自己的 MAX_PASSWORD_LEN
```

⭐ **⭐⭐ 而 1024 这个上限的来源，⭐ 我在上游源码里找到了 —— ⭐ **就在同一个 commit 里：**

```c
+#define MIN_PASSWORD_HASH_LEN	4
 #define MAX_PASSWORD_LEN	1024
```

⭐ **⭐⭐ 注意这两个宏现在是**相邻**的：⭐ **一个是「密码最长多少」，一个是「哈希最少多长」。⭐ **⭐ 而修复加上去的，正是后者。**

### ⭐⭐⭐⭐ 真正的机关：musl 的 `crypt()` 对超长密钥返回 `"*"`

⭐ **⭐⭐ 这是全文的核心，⭐ 而 Alpine 公告的表述非常精确：**

> *"When sshd is built **without PAM**, it checks a password by hashing the attempt with `crypt()` (the C library function that turns a password into its stored hash) and comparing the result to the stored password field. **For an account whose stored field is too short to contain a salt** (the random prefix of a hash), **sshd borrows the salt of another account.**"*
>
> *"**musl's `crypt()` returns the string `*` as an error indicator when the key is over 256 bytes long.** `*` is also exactly what the stored field contains for every account with no password, **so the "hash" matches and the login succeeds.**"*

⭐ **⭐⭐⭐ 我把 musl 的源码调出来核对了这个说法，⭐ **完全属实。**

**⭐ musl `src/crypt/crypt_sha512.c`（`$6$` 路径）：**

```c
/* key limit is not part of the original design, added for DoS protection. */
#define KEY_MAX 256
...
	/* reject large keys */
	for (i = 0; i <= KEY_MAX && key[i]; i++);
	if (i > KEY_MAX)
		return 0;
```

**⭐ musl `src/crypt/crypt_sha256.c`（`$5$` 路径）完全一致**，而 `crypt_des.c` 里有一行注释更直白：

```c
 * on error "*" is returned
```

⭐ **⭐⭐⭐ 而 `crypt_des.c` 的返回语句是：**

```c
	return (setting[0]=='*') ? "x" : "*";
```

⭐ **⭐⭐⭐⭐ 请注意这个「机关」的完整形状，⭐ **它是三个事实的乘积：**

```
① musl 的 crypt() 在 key > 256 字节时，错误指示符是字符串 "*"
        ×
② 无密码账号在 /etc/shadow 里存的密码字段，恰好就是 "*"
        ×
③ OpenSSH 拿 crypt() 的返回值，与存储字段做 strcmp 比较
        ↓
   "*"  ==  "*"   →  认证通过
```

⭐ **⭐⭐⭐⭐ 而这整件事之所以能发生，⭐ **是因为一个几乎人人都忽略的实现细节：⭐ **⭐ 「对于密码字段太短、装不下 salt 的账号，⭐ **sshd 会借用另一个账号的 salt」。⭐ **⭐**

⭐ **⭐⭐⭐⭐ **而这正是为什么「至少要有一个带密码的账号」是必要条件：⭐ **⭐⭐ 因为你得有一个账号，⭐ **它的 salt 格式（`$5$`/`$6$`）能让 sshd 借到，⭐ **⭐ 然后超长密码触发 musl 的错误路径，⭐ **⭐ 而错误路径的返回值 `*` 恰好等于目标账号的存储字段。⭐ **⭐**

⭐ **⭐⭐⭐⭐ **换句话说：⭐ **⭐⭐ **「借 salt」这个功能，⭐ 本意是让没有密码哈希的账号也能走一次正常的哈希比较流程，⭐ **⭐ 而 musl 的错误返回值恰好也是 `*`，⭐ **⭐ 两者撞在一起，⭐ **⭐ 就成了一个「无密码账号可被任意密码登录」的后门。⭐ **⭐**

## 三、⭐⭐ 上游修复：提交者说「根因不在 OpenSSH，但我们有能力避开它」

⭐ **⭐ 这条 commit 是 Damien Miller（OpenSSH 核心开发者）于 2026-11-04 21:18 UTC 提交的，⭐ SHA `4353fdc43ef646c43a8dda7025cc1a898caf1482`，标题只有六个字：**

> **"avoid password authn bypass"**

⭐ **⭐⭐ 而 commit message 里的第二句，是全文最值得引用的一句：**

> *"This bypass affects some configurations and runtime configurations. **We do not consider the root cause to be within OpenSSH but we are well equipped to avoid it.**"*

⭐ **⭐⭐ 请把这句话读两遍。⭐ **它的意思是：⭐ **⭐ 根因在 musl 的 `crypt()` 错误返回值与「无密码账号的存储字段」恰好相同，⭐ **⭐ 而 OpenSSH 选择在自己这一侧堵住，⭐ **⭐ 而不是等 musl 改。⭐ **⭐**

⭐ **⭐⭐ 而这个「根因不在我们这」的责任划分，⭐ **⭐ 与本号此前写过的 eMudhra 那篇形成了有趣的对照：⭐ **⭐ 那里是「根因在 CA 那一侧（脚本写错），⭐ 但没人为此负责」；⭐ **⭐ 而这里是「根因在 libc 那一侧，⭐ 但有明确的责任主体去规避它」。⭐ **⭐**

### ⭐⭐⭐ 修复的三个改动

⭐ **⭐⭐ 我把修复前后的 `openbsd-compat/xcrypt.c` 逐行比对了，⭐ 三个改动：**

**① 长度下限检查（⭐ 这是真正堵住漏洞的那一行）：**

```c
+#define MIN_PASSWORD_HASH_LEN	4
...
-	return encrypted_password != NULL &&
+	ret = encrypted_password != NULL &&
+	    strlen(pw_password) >= MIN_PASSWORD_HASH_LEN &&
 	    strcmp(encrypted_password, pw_password) == 0;
+	freezero(pw_password, strlen(pw_password));
+	return ret;
```

⭐ **⭐⭐⭐ 请注意这个检查的对象：⭐ **⭐ 检查的是 **`pw_password`（存储字段）的长度**，⭐ **而不是 `encrypted_password`（计算结果）的长度。⭐ **⭐**

⭐ **⭐⭐⭐ 而这为什么是对的？⭐ **⭐ 因为合法的哈希字段至少要 4 个字符（⭐ `$5$`/`$6$` 加 salt 加哈希，⭐ 远不止 4）。⭐ **⭐ 而 `*` 只有 1 个字符。⭐ **⭐**

⭐ **⭐⭐⭐ **换句话说：⭐ **⭐ 这一行的意思是「⭐ **存储字段短到不可能是任何真实哈希，⭐ 那就不接受它**」。⭐ **⭐ 这是一个纯粹的「防御性断言」，⭐ 而不是「检测 musl 的错误值」。⭐ **⭐**

**② `xstrdup` 避免 double-free：**

```c
-	char *pw_password = authctxt->valid ? shadow_pw(pw) : pw->pw_passwd;
+	char *pw_password = authctxt->valid ?
+	    shadow_pw(pw) : xstrdup(pw->pw_passwd);
```

⭐ **⭐⭐ 而 `shadow_pw()` 本身也被改成总是返回一份新拷贝：**

```c
-	return pw_password;
+	return pw_password == NULL ? NULL : xstrdup(pw_password);
```

⭐ **⭐⭐ 因为修复引入了 `freezero(pw_password, ...)`，⭐ **所以必须确保这个指针归 `sys_auth_passwd` 所有，⭐ **而不是指向 `pw->pw_passwd` 这种结构体成员。⭐ **⭐**

**③ `freezero` 清零敏感数据：**

```c
+	freezero(pw_password, strlen(pw_password));
```

⭐ **⭐⭐ 而 `freezero`（⭐ 相比 `free` 多清零内存）⭐ **是 OpenSSH 自己的一个小工具，⭐ **它也被顺手用在了 `pick_salt()` 里那个遍历所有账号的循环上：**

```c
 	while ((pw = getpwent()) != NULL) {
+		if (passwd != NULL)
+			freezero(passwd, strlen(passwd));
 		if ((passwd = shadow_pw(pw)) == NULL)
```

⭐ **⭐⭐⭐ 请注意这一处的意义：⭐ **⭐ `pick_salt()` 会**遍历系统上的每一个账号**，⭐ **读取它们的密码哈希来找一个能借的 salt。⭐ **⭐ 而在这个循环里，⭐ **每个读到的哈希之前都会留在内存里。⭐ **⭐ 加上 `freezero` 之后，⭐ **它们用完即焚。⭐ **⭐**

### ⭐⭐ 而 10.6p2 的发布说明还有一段值得单独说

⭐ **⭐ 我在 OpenSSH 的 10.6 release notes 里找到了一段，⭐ **⭐ 它与本号此前写的 PHP2Shell 那篇正好呼应：**

> *"Recently the OpenSSH team have received **a large number of security bug reports, many of which are findings from AI models or made with AI assistance.**"*
>
> *"**We have seen a number of cases where a security bug identified by AI tools is subsequently independently discovered by a different researcher.** This suggests that adversaries who do not report bugs to OSS projects are likely to be able to discover these bugs too. Given this, **the OpenSSH team will, for now, be making more frequent releases to get bugfixes into users' hands more quickly** rather than batching them until the next planned release."*

⭐ **⭐⭐⭐ 而这条新闻本身，⭐ **并不是 AI 找出来的 —— ⭐ **报告者是 Özgün Kültekin（Wakefield）。⭐ **⭐**

⭐ **⭐⭐⭐ 但我要指出一个更精确的事实，⭐ **⭐ 免得把这条新闻讲歪：⭐ **⭐ 这条漏洞的「技术核心」在 musl，⭐ **⭐ 而 musl 的 `crypt()` 那个 `KEY_MAX 256` 上限，⭐ **⭐ 是当年**为了 DoS 防护**而加的（⭐ 源码注释原文：*「key limit is not part of the original design, added for DoS protection」*）。⭐ **⭐**

⭐ **⭐⭐⭐ **换句话说：⭐ **⭐⭐ 一个为了「防止 DoS」而设的长度上限，⭐ **⭐⭐ 在另一个语义（哈希错误指示符）下，⭐ **⭐⭐ 恰好等于「无密码账号」的存储字段。⭐ **⭐⭐ **⭐ 这不是「AI 找出来的 bug」，⭐ **⭐⭐ 而是一个二十年前的防御性设计，⭐ **⭐⭐ 在另一个维度上撞上了另一个二十年前的约定。⭐ **⭐**

## 四、⭐⭐ 谁受影响、谁不受影响

⭐ **⭐ Alpine 公告的这份清单，⭐ **⭐ 我认为是这类公告里写得最清楚的一份，⭐ **⭐ 因为它没有含糊地写「某些配置可能受影响」，⭐ **⭐ 而是逐条列出了判定条件。**

### ⭐⭐ 受影响（⭐ 三个条件同时成立）：

| 条件 | 说明 |
|---|---|
| ⭐ **① sshd 未用 PAM** | ⭐ **跑 Alpine 的 `openssh-server` 包（⭐ 不带 PAM 构建），⭐ **或跑 `openssh-server-pam` 但设了 `UsePAM no`** |
| ⭐ **② `PasswordAuthentication yes`** | ⭐ **OpenSSH 默认值（⭐ 除非你改过）** |
| ⭐ **③ 存在密码字段为 `*` 的账号** | ⭐ **⭐ 包括 root（⭐ 自 Alpine 3.16 起基础镜像就是 `root:*`）、⭐ `adduser` 不设密码的用户、⭐ `usermod -p '*'`、⭐ musl-nscd 目录服务来的用户、⭐ tiny-cloud 镜像里的 `alpine` 用户** |
| ⭐ **④ 至少一个 `$5$`/`$6$` 账号** | ⭐ **⭐ 一个带密码的用户，就让所有无密码账号变得可达** |

⭐ **⭐⭐ 而 Alpine 还给了一个重要的细节，⭐ **⭐ 关于 `PermitRootLogin`：**

> *"OpenSSH's default `PermitRootLogin prohibit-password` protects root, so **root is only reachable if `PermitRootLogin yes` is set. That does not help if another account that can log in is able to become root, for example through `doas`.**"*

⭐ **⭐⭐ 请注意最后半句：⭐ **⭐ 就算 root 本身受 `PermitRootLogin` 保护，⭐ **⭐ 而一个能登录的普通账号能通过 `doas` 变 root，⭐ **⭐ 那么防护等于零。⭐ **⭐**

### ⭐⭐ 不受影响

| | 说明 |
|---|---|
| ⭐ **容器** | ⭐ **不在容器里跑 `sshd` 的 Docker 等用户** |
| ⭐ **`PasswordAuthentication no`** | ⭐ **⭐ 直接关闭密码认证** |
| ⭐ **`openssh-server-pam` + `UsePAM yes`** | ⭐ **⭐ **PAM 路径不走这段代码** |
| ⭐ **锁定账号** | ⭐ **密码字段为 `!`（⭐ 行首 `user:!:`）⭐ —— ⭐ **⭐ 注意区别：`!` 安全，`*` 中招** |
| ⭐ **没有任何 `$` 风格哈希的机器** | ⭐ **⭐ 没有可借的 salt，⭐ **整个前提不成立** |
| ⭐ **cloud-init 配置的云镜像** | ⭐ **⭐ cloud-init 默认写 `PasswordAuthentication no`** |

⭐ **⭐⭐ 而最后一行的对比，⭐ **⭐ 特别值得注意：⭐ **⭐ **cloud-init 配出来的云镜像，⭐ **⭐ 因为 cloud-init 主动写了 `PasswordAuthentication no`，⭐ **⭐ 反而是安全的。⭐ **⭐ 而手工装的、⭐ **甚至官方 tiny-cloud 镜像（⭐ Alpine 自己的官方云镜像）⭐ **⭐ 是不安全的。⭐ **⭐**

### ⭐⭐ 受影响版本

> *"Affected releases: **every Alpine release we checked, 3.21 through 3.24 and edge**, and the older releases that no longer receive regular updates (**3.16 to 3.20**)."*

⭐ **⭐⭐ 请注意这条的措辞有多重：⭐ **⭐ 「every Alpine release **we checked**」⭐ **⭐ —— ⭐ **⭐ 也就是说，⭐ **⭐ 这不是「所有 Alpine 都有漏洞」，⭐ **⭐ 而是「我们检查过的每一个都有」。⭐ **⭐**

⭐ **⭐⭐ 而这个范围还有一个值得注意的延伸，⭐ **⭐ 关于官方云镜像：**

> *"The official **tiny-cloud** images (the qcow2, VHD and AMI artifacts) from **3.18.11 through 3.24.3** ship an `alpine` user with a `*` password field and **passwordless `doas`**."*
>
> *"**They are safe on first boot. They become exploitable as soon as any `$6$` hash exists on the machine**, for example when an admin sets a console password, or **user-data adds a user with `hashed_passwd`**. An attacker then gets a shell as `alpine` and **can use `doas` to become root.**"*

⭐ **⭐⭐⭐ 这一段我认为是全文最值得单独拿出来讲的一段，⭐ **⭐ 因为它描述的是一个「按时间点引爆」的漏洞：**

⭐ **⭐⭐ **出厂时是安全的，⭐ **⭐⭐ 因为还没有任何 `$6$` 哈希。⭐ **⭐⭐ 而当管理员设了一个控制台密码、⭐ **⭐⭐ 或者 cloud-init 的 user-data 里加了一个带 `hashed_passwd` 的用户，⭐ **⭐⭐ **它就变成可被利用的。⭐ **⭐**

⭐ **⭐⭐⭐ **换句话说：⭐ **⭐⭐ **这台机器上「多设一个密码」这个完全无害的管理动作，⭐ **⭐⭐ 就是把它推进可被利用状态的动作。⭐ **⭐⭐**

## 五、⭐⭐ 修复与操作

### ⭐⭐ 逐分支修复版本（Alpine 公告原表）

| 分支 | 修复版本 |
|---|---|
| ⭐ **edge** | ⭐ **`10.6_p2-r0`** |
| ⭐ 3.24 | `10.3_p1-r2` |
| ⭐ 3.23 | `10.2_p1-r1` |
| ⭐ 3.22 | `10.0_p1-r11` |
| ⭐ 3.21 | `9.9_p2-r1` |
| ⭐ 3.20 | `9.7_p1-r6` |
| ⭐ 3.19 | `9.6_p1-r3` |
| ⭐ 3.18 | `9.3_p2-r4` |
| ⭐ 3.17 | `9.1_p1-r7` |
| ⭐ 3.16 | `9.0_p1-r6` |

⭐ **⭐⭐ 而公告给的新版分支号是：⭐ **Alpine 3.21.10、3.22.8、3.23.8、3.24.4** —— ⭐ **⭐ 这四个是「包含修复包的点版本」。⭐ **⭐**

⭐ **⭐⭐ 我顺手核了一下 Alpine 包站：⭐ **edge 分支当前就是 `openssh 10.6_p2-r0`，⭐ **构建时间 2026-11-05 09:05:19，⭐ **⭐ 维护者 Natanael Copa。⭐ **⭐**

### ⭐⭐⭐ 而操作上最重要的一句

⭐ **⭐⭐⭐ Alpine 公告第一段就强调了这个，⭐ **⭐ 而我认为这是整份公告里最该被记住的一句操作提醒：**

> *"**Upgrading the package alone does not replace the running daemon.** If you run `sshd` on Alpine Linux, **update openssh now and restart sshd**."*

⭐ **⭐⭐ **「升级包不会重启正在运行的守护进程。」⭐ **⭐**

⭐ **⭐⭐ 而这正是很多人在其它发行版上会踩的坑：⭐ **在 Debian/Ubuntu 上 `apt upgrade` 会触发服务重载，⭐ **而 Alpine 的 `apk upgrade` 不会。⭐ **⭐**

⭐ **⭐⭐ 具体命令：**

```bash
apk upgrade -U -a
rc-service sshd restart
```

### ⭐⭐⭐ 不能立刻更新时的临时缓解

⭐ **⭐⭐ 而 Alpine 给出��这套缓解命令，⭐ **⭐⭐ 我认为它值得完整抄下来，⭐ **⭐⭐ 因为它是本号见过的、⭐ **⭐ **少数把「配置文件里所有变体」都考虑到的缓解方案：**

```bash
# 先确保 SSH 密钥登录可用，并保持当前会话不要断开，直到你验证过新登录

mkdir -p /etc/ssh/sshd_config.d
echo 'PasswordAuthentication no' > /etc/ssh/sshd_config.d/00-no-passwords.conf
sed -i.bak -e '1i PasswordAuthentication no' \
  -e 's/^\(\s*PasswordAuthentication[^y#]*\)yes/\1no/i' \
  /etc/ssh/sshd_config
sshd -t && rc-service sshd restart
sshd -T | grep -i passwordauthentication
```

⭐ **⭐⭐⭐ 而公告对这段命令的解释，⭐ **⭐⭐ 逐条说明了它处理了哪些情况：**

| 命令片段 | 处理的情况 |
|---|---|
| ⭐ `mkdir -p /etc/ssh/sshd_config.d` ＋ `echo 'PasswordAuthentication no' > .../00-no-passwords.conf` | ⭐ **⭐ 创建一个 drop-in 文件；⭐ **Alpine 从 **3.19 起**的默认 `sshd_config` 会读这个目录，⭐ **更老的版本会忽略它** |
| ⭐ `sed -i.bak -e '1i PasswordAuthentication no'` | ⭐ **⭐ 在文件开头插入一行 —— 处理「原本就没有这一行」的情况** |
| ⭐ `sed -i.bak -e 's/^\(\s*PasswordAuthentication[^y#]*\)yes/\1no/i'` | ⭐ **⭐ 把**每一行** `PasswordAuthentication` 的 `yes` 改成 `no` —— ⭐ **⭐ 「无论空格多少，⭐ 包括 `Match` 块内部的行」** |
| ⭐ `-i.bak` | ⭐ **⭐ 把原文件备份为 `/etc/ssh/sshd_config.bak`** |
| ⭐ `sshd -t` | ⭐ **⭐ 先测配置语法，⭐ 再重启** |
| ⭐ `sshd -T \| grep -i passwordauthentication` | ⭐ **⭐ 打印**生效后**的实际配置，⭐ 应该输出 `passwordauthentication no`** |

⭐ **⭐⭐⭐ 而我要特别指出 `sed` 那条正则里的 `[^\y#]*`：⭐ **⭐⭐ 它排除的是 `y` 和 `#` —— ⭐ **⭐⭐ 也就是说：⭐ **「PasswordAuthentication yes」会被改，⭐ **⭐⭐ 而「PasswordAuthentication no」和「#PasswordAuthentication yes」（注释）⭐ **⭐⭐ 不会被误伤。⭐ **⭐**

⭐ **⭐⭐ 而撤销方法公告也写了：⭐ **删掉那个 drop-in 文件，⭐ 并把 `sshd_config.bak` 拷回去。**

### ⭐⭐ 「查不到就当被攻破」

⭐ **⭐⭐ Alpine 给的排查方法，⭐ **⭐⭐ 最后一句最重：**

> *"Look in `/var/log/messages` for `sshd` lines reading **`Accepted password for` an account that has no password** (`alpine`, `root`, or any key-only user)."*
>
> *"Review `doas` use and recently created users, files and authorized keys on exposed machines. **If you cannot rule out a login, treat the machine as compromised.**"*

⭐ **⭐⭐⭐ **请注意这个检测特征的设计有多好：⭐ **⭐⭐ 它不要求你去判断「这条登录是否合法」，⭐ **⭐⭐ 而是**去看「这条登录用了一个本来不可能用密码登录的账号」** —— ⭐ **⭐⭐ 因为对那些账号来说，⭐ **⭐⭐ **任何一次 `Accepted password` 都必然是攻击。⭐ **⭐**

## 六、⭐⭐⭐⭐ 最后：这条漏洞的三层结构，和本号此前的几条线

⭐ **⭐⭐ 这一节是我的判断，⭐ **⭐ 但我认为这条漏洞特别适合拿来做一次总结，⭐ **⭐ 因为它的每一层都恰好对应一个更普遍的问题。**

### ⭐⭐ 第一层：这是一个「错误返回值语义冲突」的经典案例

⭐ **⭐⭐ 回头看整件事的技术核心，⭐ **⭐⭐ 它其实是三个字符串约定在同一个点上相撞：**

```
/etc/shadow 里 "*"      =  这个账号没有密码（Unix 传统约定）
musl crypt() 的 "*"     =  哈希计算失败（musl 的错误指示符）
sshd 的比较逻辑         =  strcmp(crypt结果, 存储字段) == 0
```

⭐ **⭐⭐⭐ 而 OpenSSH 的修复，⭐ **⭐⭐ 是**不碰这三个约定中的任何一个**，⭐ **⭐⭐ 只是加了一条「存储字段至少 4 个字符」的长度断言。⭐ **⭐**

⭐ **⭐⭐ **这是一个非常值得学的修法：⭐ **⭐⭐ 当你无法修改约定的一方（libc）或不愿破坏它（`*` 的语义），⭐ **⭐⭐ **就在你自己的比较逻辑上加一个「这不可能是合法值」的判据。⭐ **⭐**

### ⭐⭐ 第二层：而「无密码账号」与「有密码账号」的组合才能引爆，⭐ 这是一个很反直觉的耦合

⭐ **⭐⭐ **大多数人会以为「把 root 锁掉」就安全了。⭐ **⭐ 而这条漏洞恰恰说明：⭐ **⭐⭐ **「你的机器上有没有任何一个别的用户用密码」，⭐ **⭐⭐ 会改变「你的无密码账号是否可被利用」。⭐ **⭐**

⭐ **⭐⭐ **而 Alpine 公告里那一条最刺眼的推论是：⭐ **⭐⭐**

> *"**They are safe on first boot. They become exploitable as soon as any `$6$` hash exists on the machine** — for example when an admin sets a console password, or user-data adds a user with `hashed_passwd`."*

⭐ **⭐⭐⭐ **「多设一个控制台密码」⭐ **⭐⭐ 这个动作在正常心智模型里是**提高**安全性的，⭐ **⭐⭐ 而在这里它是**降低**安全性的。⭐ **⭐⭐ **⭐ 这就是耦合关系的可怕之处。**

### ⭐⭐⭐ 第三层：⭐⭐ 而这条新闻和本号此前写的几篇，⭐ **⭐⭐ 组成了一个完整的「防御纵深」图景**

| | 本号此前写的 | 这条漏洞体现的层次 |
|---|---|---|
| ⭐ **《CVE-2026-98432》** | ⭐ **内核 UAF，⭐ **且官方明确说「**不是 MPTCP 的问题**」 | ⭐ **⭐ 漏洞有明确的边界，⭐ **而缓解措施必须针对边界** |
| ⭐ **《eMudhra：私钥是数字 4》** | ⭐ **CA 私钥是「4」，⭐ **流程失效** | ⭐ **⭐ 一个「本该最不容易出错」的环节，⭐ **因为流程失效而失效** |
| ⭐ **《CVE-2026-109518（APT）》** | ⭐ **重试时重开了可能是别人也在用的硬链接** | ⭐ **⭐ **「我以为我独占」这个朴素假设失效** |
| ⭐ **《RTX Spark 的 NPCF》** | ⭐ **功耗表加密，⭐ **而解密密钥只在 Windows 侧** | ⭐ **⭐ **「只有一边有」的东西变成事实上的排他** |
| ⭐ **⭐ 本文** | ⭐ **⭐ **musl 的错误指示符 `*` 恰好等于无密码账号的存储字段** | ⭐ **⭐⭐ **三个各自合理的约定，在同一个点上相撞** |

⭐ **⭐⭐⭐ 而把这五篇放在一起，⭐ **⭐⭐⭐ 我看到的最后一个观察是：⭐ **⭐⭐**

⭐ **⭐⭐⭐ **上面这五个案例里，⭐ **⭐⭐ **有一个共同点值得警惕：⭐ **⭐⭐ **它们都不是「有人写了一段错误的代码」，⭐ **⭐⭐ **而都是「**几个各自正确的部分，⭐ **⭐⭐ **在没有人整体审视过的地方相撞**」。⭐ **⭐⭐**

⭐ **⭐⭐⭐ 而这一类问题的特点是：⭐ **⭐⭐ **单看任何一处都挑不出毛病，⭐ **⭐⭐ **而攻击只需要找到一个交点。⭐ **⭐**

⭐ **⭐⭐⭐ **所以，⭐ **⭐⭐⭐ 在这个意义上，⭐ **⭐⭐⭐ **OpenSSH 这次那行 `strlen(pw_password) >= MIN_PASSWORD_HASH_LEN` 的价值，⭐ **⭐⭐⭐ 远大于它的代码量：⭐ **⭐⭐⭐ 它承认了「我的比较逻辑可能撞上别人的约定」这件事本身，⭐ **⭐⭐⭐ 然后在自己这一侧加了一道断言。⭐ **⭐**

⭐ **⭐⭐⭐ **而 Alpine 公告的最后一段，⭐ **⭐⭐⭐ 我觉得是这类通告最好的结尾方式 —— ⭐ **⭐⭐⭐ 它没有说「请尽快更新」，⭐ **⭐⭐⭐ 而是说：⭐ **⭐⭐⭐**

> *"**If you cannot rule out a login, treat the machine as compromised.**"*

⭐ **⭐⭐⭐ **「如果你无法排除一次登录的可能，⭐ **⭐⭐⭐ 就把这台机器当作已被攻破。」⭐ **⭐⭐**

⭐ **⭐⭐⭐ **⭐ **在一条「一次连接必成功」的攻击面前，⭐ **⭐⭐⭐ 这不是过度反应，⭐ **⭐⭐⭐ 而是唯一负责任的默认态度。⭐ **⭐**

---

## 主要来源

- ⭐ **Alpine Linux《Security advisory: openssh-server password authentication bypass》（2026-11-05）**：⭐ **「An attacker who can reach your SSH port can log in without knowing any password. It takes one connection, works every time, and needs no retries.」**；⭐ **三个环节（`*` 账号 / 至少一个 `$5$`/`$6$` 账号 / 257–1024 字节超长密码）；⭐ **「musl's `crypt()` returns the string `*` as an error indicator when the key is over 256 bytes long. `*` is also exactly what the stored field contains for every account with no password, so the "hash" matches and the login succeeds.」**；⭐ **「For an account whose stored field is too short to contain a salt, sshd borrows the salt of another account.」**；⭐ **完整受影响/不受影响清单（含 `PermitRootLogin` 与 `doas` 的说明、musl-nscd 目录服务用户、tiny-cloud 镜像的「按时间点引爆」）；⭐ **逐分支修复版本表（edge `10.6_p2-r0` 至 3.16 `9.0_p1-r6`）与点版本 3.21.10 / 3.22.8 / 3.23.8 / 3.24.4**；⭐ **「Upgrading the package alone does not replace the running daemon」**；⭐ **完整的临时缓解命令与逐条解释；⭐ **「If you cannot rule out a login, treat the machine as compromised.」**；⭐ **致谢 Özgün Kültekin（Wakefield）、Damien Miller、Darren Tucker、Timo Teräs、Natanael Copa** —— <https://alpinelinux.org/posts/2026-11-05-openssh-password-authentication-bypass/>
- ⭐ **OpenSSH 上游修复 commit `4353fdc43ef646c43a8dda7025cc1a898caf1482`**（Damien Miller，2026-11-04T21:18:18Z，⭐ 标题 **"avoid password authn bypass"**）：⭐ **「We do not consider the root cause to be within OpenSSH but we are well equipped to avoid it.」**；⭐ **三个文件 改动 —— `auth-passwd.c`（+13 −4）、`openbsd-compat/port-uw.c`（+8 −8）、`openbsd-compat/xcrypt.c`（+13 −5）**；⭐ **新增 `#define MIN_PASSWORD_HASH_LEN 4`、⭐ `strlen(pw_password) >= MIN_PASSWORD_HASH_LEN` 断言、⭐ `xstrdup` 避免 double-free、⭐ `freezero` 清零敏感数据（⭐ 包括 `pick_salt()` 遍历全系统账号的循环）** —— <https://github.com/openssh/openssh-portable/commit/4353fdc43ef646c43a8dda7025cc1a898caf1482>
- ⭐ **修复前的 `openbsd-compat/xcrypt.c` 与 `port-uw.c`（同一 commit 的父提交 `4353fdc43^`）**：⭐ **「Just use the supplied fake password if authctxt is invalid」→ `pw->pw_passwd`（无拷贝，⭐ 这就是 `freezero` 需要 `xstrdup` 的原因）**；⭐ **「Encrypt the candidate password using the proper salt」→ `salt = (pw_password[0] && pw_password[1]) ? pw_password : "xx";`；⭐ **「Authentication is accepted if the encrypted passwords are identical.」→ `strcmp(xcrypt(password, salt), pw_password) == 0`**；⭐ **`pick_salt()` 遍历 `getpwent()` 借用他人 salt 的逻辑**
- ⭐ **musl libc 源码（我逐行核对）**：⭐ **`src/crypt/crypt_sha512.c` 与 `crypt_sha256.c`：**`#define KEY_MAX 256`＋ 注释 *「key limit is not part of the original design, added for DoS protection」*＋`for (i = 0; i <= KEY_MAX && key[i]; i++); if (i > KEY_MAX) return 0;`；⭐ **`src/crypt/crypt_des.c`：** 注释 *「on error \"*\" is returned」*＋ `return (setting[0]=='*') ? "x" : "*";`；⭐ **`src/crypt/crypt_r.c`：** `__crypt_r` 按 salt 前缀分派 `$1$`/`$2$`/`$5$`/`$6$`/DES；⭐ **`src/crypt/crypt.c`：** `crypt()` 转发到 `__crypt_r`
- ⭐ **Alpine 包站 `openssh`（edge/main/x86_64）**：⭐ **Version `10.6_p2-r0`、Build time 2026-11-05 09:05:19、Maintainer Natanael Copa、⭐ `so:libc.musl-x86_64.so.1` 依赖** —— <https://pkgs.alpinelinux.org/package/edge/main/x86_64/openssh>
- ⭐ **OpenSSH 10.6 release notes**：⭐ **「a large number of security bug reports, many of which are findings from AI models or made with AI assistance」；⭐ 「We have seen a number of cases where a security bug identified by AI tools is subsequently independently discovered by a different researcher. This suggests that adversaries who do not report bugs to OSS projects are likely to be able to discover these bugs too. Given this, the OpenSSH team will, for now, be making more frequent releases to get bugfixes into users' hands more quickly.」** —— <https://www.openssh.com/txt/release-10.6>
- 本号此前写的相关分析：⭐ 《CVE-2026-98432 的补丁公告里两个容易被读错的地方》、⭐ 《一个 CA 的私钥是数字 4：eMudhra 事件里最该被读懂的，不是「证书被吊销了」》、⭐ 《签名验证过了，然后被换掉：APT 自己的 CVE-2026-109518》、⭐ 《插上电源，GPU 掉到 780 MHz：RTX Spark 笔记本上的 Linux 慢 5 倍》、⭐ 《「40 年技术债要还了」：PHP2Shell 为什么被 IEEE Spectrum 称为 AI 安全的一次警钟》

---

（说明：本文依据 Alpine Linux 官方安全公告、⭐ **OpenSSH 上游修复 commit 原文及其父提交的比对**、⭐ **musl libc 的 crypt_sha256.c / crypt_sha512.c / crypt_des.c / crypt_r.c 源码**、⭐ **Alpine 包站的实际构建信息** 与 OpenSSH 10.6 release notes 撰写。**第四节所有引号内的英文原文均直接取自上述来源。** **第六节的三层结构分析、⭐ 「三个各自正确的约定在同一点相撞」这一判断、⭐ 以及与本号此前五篇的横向对照，⭐ 均为笔者观点，⭐ 不代表 Alpine、OpenSSH 或 musl 的立场。** **本文不包含任何利用代码或可武器化的 payload；⭐ 文中给出的 sed / grep 命令仅用于**检测与缓解自身系统**，⭐ 而「攻击者发送一个 257 字节以上的密码」这一描述转述自官方公告的成因说明，⭐ 不含任何实现细节。**）
