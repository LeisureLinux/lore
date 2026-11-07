---
title: "Barracuda ESG 预认证 root 链：一个改错的返回语句和一个硬编码密钥"
date: 2026-11-07
slug: barracuda-esg-preauth-root-chain
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：watchTowr Labs《Barracuda Networks is your new best friend》（Sina Kheirkhah，2026-11-05）的补丁 diff 逐行分析与漏洞链复现 ＋ Barracuda 官方安全公告（2026-11-05，含六个受影响产品的补丁编号与「Authentication Required」字段的修订说明）＋ The Hacker News 报道（2026-11-06，Swati Khandelwal）＋ SecurityWeek 与 BleepingComputer 的评分与细节 ＋ 本文对照厂商公告核对的受影响产品范围与修复固件版本"
original_date: 2026-11-06
original_url: "https://thehackernews.com/2026/11/experts-demonstrate-barracuda-email.html"
description: "本文解读 Barracuda Email Security Gateway 的预认证 root 链式利用，以及 watchTowr Labs 对其补丁的逐行分析。这条链由两个漏洞构成，而**每个漏洞单独看都不致命，串起来才是 root** —— 这正是它值得单独写的原因。**第一个 CVE-2026-116606（授权绕过，CVSS 9.3）**：设备处理改密码请求时，如果改密失败（ERROR_PASSWD_CHANGE），修复前的代码返回的是当前会话的 role 对象而不是终止信号，于是「一个被拒绝的认证操作」并没有真正中止请求流程 —— 未认证的攻击者由此得到了一个低权限角色的会话。而设备本身把管理界面暴露在边界上、且以精确且仅必需的权限运行，login-screen 角色因此就有价值了。厂商在补丁里加的那行注释把这个 bug 说得很直白：「返回 userrole 会让 response() 继续执行 module handlers」。**第二个 CVE-2026-111560（命令注入，CVSS 8.6）**：备份恢复流程里有一个把时区值拼进 sed 命令的 sink，Perl 反引号会先构造字符串再交给 shell，所以看起来「有单引号包裹就安全」其实是错的 —— 单引号只是生成命令里的字符，不是 Perl 侧的安全边界。修复后厂商把时区值当作不可信输入，要求它先解析成 /usr/share/zoneinfo/ 下的真实文件，并把命令执行改写成纯 Perl 的读写。这条 sink 通过 sudo 执行 fix_tz.pl，因此**最终以 root 身份运行**。而两个漏洞之间的桥是备份恢复：备份里的时区值会被恢复进配置，然后被上面那个 sink 读到。**最值得记的一处细节**：备份文件的校验和算法是 md5(文件字节 + 硬编码密钥 + \".\")，而那个密钥就明文写在代码里 —— 所以「有校验和」这个防护在设计上是失效的。本文还记录了三个容易被忽略的现实：厂商公告里「Authentication Required」字段在发布当天被改过（从「Yes, administrative access」改成「No (Administrative UI Access Required)」—— 因为无需登录，只需管理界面可达）；补丁文件里注释的 CVSS 9.8 与厂商公告的 9.3 不一致（watchTowr 判断 9.8 大概是把两个漏洞合起来算的）；以及修复固件版本在厂商公告与媒体报道之间有 9.4.0.029 与 9.4.0.030 的差异。"
published: true
---

> 原文：watchTowr Labs 的分析文章（2026-11-05，作者 Sina Kheirkhah）
> 报道链接：<https://thehackernews.com/2026/11/experts-demonstrate-barracuda-email.html>
>
> 本文依据原分析者的补丁 diff 逐行分析、Barracuda 官方安全公告、多家安全媒体的报道，以及本文对照厂商公告核对的受影响产品范围。

## 一、这条链为什么值得单独写

两个漏洞，单独看都不致命：

| CVE | 类型 | CVSS | 单独看能干什么 |
|---|---|---|---|
| CVE-2026-116606 | 预认证授权绕过 | 9.3 Critical | 拿到一个**低权限角色**的会话 |
| CVE-2026-111560 | OS 命令注入 | 8.6 High | 以 root 执行命令，**但需要管理员权限** |

**第一个给你一个没登录的会话，第二个需要管理员权限。** 单看都是「还好」，串起来就是「不用登录直接拿 root」。

而这两个漏洞的设计意图，也正好说明它们为什么能串起来：**第一个的产物（一个低权限会话）正好是第二个的前置条件**，而第二个的注入点（备份恢复里的时区值）又恰好能被第一个的会话触达。

设备本身的角色让这条链格外值钱。Barracuda ESG 是挡在组织邮件前面的那个设备 —— 它决定哪些邮件是垃圾邮件、哪些带恶意软件、哪些放行。watchTowr 的描述很到位：**「又一个住在边界上、检查一切、以精确且仅必需的权限运行来拦截一封骂你博客的邮件的设备。」**

而且这台设备**已经因为 CVE-2023-2868 被 UNC4841 当作零日利用过**，那次的结果是**物理更换硬件**。

## 二、第一个漏洞：一次被拒绝的改密，没有真正中止请求

### 修复前的那段代码

watchTowr 在补丁 diff 里翻出了 `Index.pm` 的完整函数。核心是这段（原始行号 383–407）：

```perl
if (defined($params->{new_password}) && defined($params->{retype_password}) && ! (-e "/tmp/bypass_password")) {
    my $password_change_status = 0;
    my $message = "";
    ($password_change_status, $message, $user) = Login::change_admin_password($params);
    if ($password_change_status == 1 && $user) {
        # 成功路径
        ...
        return bailout();
    }
    else {
        if ($password_change_status == $Login::status_codes{ERROR_PASSWD_CHANGE}->{val}) {
            $params->{json_authenticate} = {
                success => 'true',
                message => ...,
                status => ...,
            };
            $self->audit("failed_password_change", $params->{user});
            return $userrole;          # ← 问题在这里
        }
```

**关键在于两条路径的返回值不同：**

- 改密**成功** → `return bailout();` —— 而 `bailout()` 是「我们结束了，到此为止」的信号；
- 改密**失败** → `return $userrole;` —— 返回的是**当前会话的角色对象**。

那 `$userrole` 是什么？watchTowr 的解释是：「只是」当前会话的角色对象，**对于我们这个未认证的请求，那就是低权限的登录界面角色**。

### 为什么返回 role 对象就是漏洞

因为调用链是这样的：

```perl
sub response {
    ...
    $self->_process_params($env, $params);      # ← 这里返回了 $userrole
    $self->_update_variables($env, $params);
    Barracuda::Hooks::run_hooks("after write config");
```

`_process_params` 在第 593 行返回，**把 `$userrole` 原样交回 `response`** —— 而这个 return **没有带任何错误指示**，于是函数照常继续往下走。

**用 watchTowr 自己的话说**：修前的代码虽然返回了一段 verbose 的 JSON 声明「改密失败」，**但它并没有真正停止执行**。

### 厂商自己写下的注释

Barracuda 在补丁里留了一行提示，我觉得这句注释比任何解读都清楚：

```
+    # Send the error and stop here. Returning a userrole
+    # would let response() run module handlers.
```

（**把错误发出去并在这里停下。返回一个 userrole 会让 `response()` 继续执行 module handlers。**）

修复方式就是把它改成一个真正会中止的调用：

```diff
-            return $userrole;
+            return $self->_bailout_with_json_login_response(
+                $env, $params, {
+                success => 'true',
+                message => ...,
+                status => ...,
+            });
```

### 触发方式

向 `/cgi-mod/index.cgi` 发一个 POST，带上 `new_password` 和 `retype_password` 两个参数：

```
POST /cgi-mod/index.cgi HTTP/1.1
Content-Type: application/x-www-form-urlencoded

user=admin&new_password=one&retype_password=two
```

设备返回 HTTP 200，JSON 体声明改密失败：

```json
{"message":"Error: Password Change: ","no_ajax_redirect":"true",
 "redirect":"/cgi-mod/password_change.cgi?auth_type=Local&locale=en_US&user=admin&error=...",
 "success":"true"}
```

**注意 `success: "true"`** —— 这是「改密流程成功走完了」的意思，不是「你登录成功了」。

**而这才是关键所在**：watchTowr 那段带黑色幽默的追问值得原样记住 ——

> 「但等等，」你会说，「一个被拒绝的认证操作 surely 会阻止后续任何特权操作发生？登录界面角色有什么用？」

**答案是：它的用处在于给第二个漏洞开门。** 因为认证绕过本身拿不到什么权限，但**它拿到的是一个「已认证但权限很低」的会话** —— 而这个会话足以触达备份恢复接口。

## 三、第二个漏洞：看起来有单引号包裹，其实没有安全边界

### 那个 sink

修复前的 `Backup2.pm` 里有一段：

```perl
if( -f "/home/product/code/config/tz" ) {
    my $system_timezone = Barracuda::Config::get('system_timezone');
    `sed -i 's=.*=$system_timezone#' /home/product/code/config/tz`;
}
```

**这是 Perl 的反引号（backtick），也就是命令替换。** watchTowr 指出关键：

> The single quotes around the value look protective, but they are only characters in the generated command, not a Perl safety boundary.

（**值外面的单引号看起来像是防护，但它们只是生成命令里的字符，不是 Perl 侧的安全边界。** 这一句是全文我唯一想原样保留的英文 —— 它点出了整个漏洞最反直觉的那一层。）

一个形如下面的值就能改写 shell 语法：

```
Region#';<attacker-command>;#
```

**第一个单引号闭合了原本的 `sed` 表达式，分号开启一条新命令，`#` 把剩下的都注释掉。**

### 修复后的做法

厂商的修复有两个动作，第二个更根本：

```diff
-    `sed -i 's=.*=$system_timezone#' /home/product/code/config/tz`;
+    if ($system_timezone && -f "/usr/share/zoneinfo/$system_timezone") {
+        open my $in, '<', '/home/product/code/config/tz' or die $!;
+        my @lines = <$in>;
+        close $in;
+        open my $out, '>', '/home/product/code/config/tz' or die $!;
+        for my $line (@lines) {
+            $line =~ s/^TZ=.*/TZ=$system_timezone/ if $line =~ /^TZ=/;
+            print $out $line;
+        }
+        close $out;
+    } else {
+        warn "Skipping tz restore: invalid system_timezone='$system_timezone'\n";
+    }
```

1. **把时区值当作不可信输入** —— 要求它先解析成 `/usr/share/zoneinfo/` 下的一个真实文件；
2. **把命令执行换成纯 Perl 的读—改—写** —— 根本不进 shell 了。

`fix_tz.pl` 里是同一个故事，加了一道存在性检查：

```diff
+if (! -f "/usr/share/zoneinfo/$system_timezone") {
+    warn "Invalid timezone: $system_timezone\n";
+    exit 1;
+}
```

**这才是正确的修法** —— 不是在拼接时做转义，而是**根本不把不可信数据交给 shell**。

### 为什么这条 sink 是 root

有两个 sink：`Backup2::finalize_restore` 写产品时区文件，`fix_tz.pl` 写操作系统时钟文件。而调用方是这样的：

```perl
if( -f "/home/product/code/firmware/current/bin/fix_tz.pl" ) {
    system('/usr/bin/sudo',
           '/home/product/code/firmware/current/bin/fix_tz.pl');
}
```

**它用 `sudo` 执行。** 所以：

**这不是什么普通的 OS 命令注入，而是一条以 root 执行的。**

## 四、两个漏洞之间的桥：备份恢复

第二个漏洞的注入点是时区值，而时区值能被攻击者控制 —— 靠的是备份恢复。

备份文件是个 tar 包，里面有一个 `backup.xml` 列出各个组件。watchTowr 构造的示例：

```xml
<backup>
  <component name="Spam_Config">
    <file id="mysql" checksum="[generated integrity value]" path="mysql-poc.gz" />
  </component>
  <info filename="poc.bak" firmware_version="9.4.0.020"
        model="V300" platform="5" product="emailswitch" type="manual_backup">
    ...
  </info>
</backup>
```

**注意 `Spam_Config` 这个名字** —— 它正是第一个漏洞的补丁注释里提到的那个组件。

恢复 `Spam_Config` 时，设备会加载一个 MySQL dump 并把里面的数据恢复到本地数据库。而**其中一行就是 `system_timezone`**。

于是链路合上了：

1. **第一个漏洞** → 拿到低权限会话，能触达备份上传/恢复接口（`bayesian_upload.pm` 里的上传处理器）；
2. **上传一个伪造的备份**，其中 `Spam_Config` 的 MySQL dump 里 `system_timezone` 的值被改成带 shell 注入的值；
3. **恢复流程**把那个值写进配置；
4. **`finalize_restore`** 读到这个值，交给 `sed` 反引号；
5. **以 root 执行**。

## 五、最值得记的一处：那个「有校验和」的防护在设计上是失效的

备份里的每个文件都有一个 `checksum` 字段，恢复函数会** diligently 校验它** —— 读文件字节、算自己的校验和、对不上就拒绝整个备份。

watchTowr 的第一反应是：「所以往这些字段里随便敲数字是没用的。」

**但他们接着发现：**

```
CHECKSUM_SECRET = b"Barracuda Networks is your new best friend"
```

而校验和算法就是：

```
md5(文件字节 + CHECKSUM_SECRET + b".")
```

**那个密钥是硬编码在代码里的常量。** 所以「有校验和」这个防护，在设计层面就等于没有 —— 任何人都能自己算出合法校验和。

watchTowr 博客的标题也在这里变成了双关：**「Barracuda 网络是你最好的朋友」** —— 因为这个密钥字符串本身，就是那句友好的话（英文原文）。

### 这个设计缺陷比漏洞本身更值得记

一个「有校验和」的备份机制，听起来比「没校验和」安全得多。**但如果密钥是硬编码在客户端可读的代码里，那它提供的只是「防止意外损坏」的保护，不是「防止篡改」的保护。**

这是我在整篇文章里最想留下的一条：**校验和的安全性完全取决于密钥的保密性，而硬编码在二进制里的密钥不保密。** 它防的是「网盘传坏了」，不是「有人改内容」。

同样的道理也适用于第一个漏洞 —— 那个「pre-authentication bypass」名字听起来像是一道认证关卡被整体绕过，但实际上被绕过的只是**一个分支没返回中止信号**，剩下的流程还照常跑。

## 六、厂商公告里的三处细节，值得单独看

### ① 「Authentication Required」字段在发布当天被改过

Barracuda 官方公告顶部有一行更新说明：

**2026 年 11 月 5 日 14:30 EST 的公告更新**：CVE-2026-116606 的「需要认证」字段已从「是，需要管理权限」改为「否（但需要管理界面可达）」。**不需要认证就能利用这个漏洞；但利用的前提是管理界面对攻击者可达。**

这个修订很关键，因为它把两种不同的部署姿势区分开了：

- **「需要认证」** 意味着只有已经持有凭据的人能利用 —— 风险是有凭据的内部人员或已泄露的凭据；
- **「管理界面可达」** 意味着**任何能连到管理界面端口的人都能利用** —— 不需要任何凭据。

**后者严格更危险。** 所以如果你在看公告，别只看「9.3 Critical」，要看这个字段。

### ② 补丁文件注释里的 CVSS 是 9.8，公告里是 9.3

watchTowr 在 Patch-1 的安装器注释里看到的是：

```
# Pre-authentication authorization bypass permits
# arbitrary Spam_Config restore
# CVSS 9.8 Critical
```

而 Barracuda 公告里 CVE-2026-116606 的评分是 **9.3**。watchTowr 自己的判断是：

**我们猜 9.8 是把两个漏洞合起来算的分数（CVSS 专家会立刻认出这属于一种罪行），而不是这里发生了什么见不得人的事。**

这个观察本身挺有意思 —— **补丁文件的注释和 CVE 记录的评分不一致**，说明这个 9.8 并不是走正式流程的评分。

### ③ 修复固件版本：公告与媒体报道有差异

这里我要说明一处**核对结果**，因为不同来源写的版本号不一样：

| 来源 | 写的版本 |
|---|---|
| The Hacker News（11-06） | Email Security Gateway 修复于 **9.4.0.030** 及之后 |
| watchTowr Labs（11-05） | 两个漏洞均修复于 **9.4.0.029** |
| Barracuda 官方公告 | ESG 的补丁编号为 **BNSF-40425（9.4.017+）** 与 **BNSF-40430（<9.4.017）** |

**我以厂商公告为准**（它是第一手来源，且给出了按版本区间划分的两个补丁编号）。但如果你在媒体上看到 9.4.0.029 和 9.4.0.030 两个数字，不必怀疑自己眼花了 —— **实务上建议直接对照 Barracuda 公告里那两个补丁编号（BNSF-40425 / BNSF-40430）确认**，因为公告是按「9.4.017 之前/之后」划分的，比单一版本号更不容易出错。

watchTowr 自己的测试环境用的版本是：**有漏洞的 9.4.0.027** vs **不同的 9.4.0.029**。

## 七、受影响范围：六个产品，但只有一个能被预认证打通

Barracuda 公告列出的受影响产品矩阵：

| 产品 | CVE-2026-116606（授权绕过） | CVE-2026-111560（命令注入） | 补丁 |
|---|---|---|---|
| **Email Security Gateway (ESG)** | **是** | **是** | BNSF-40425（9.4.017+）、BNSF-40430（<9.4.017） |
| Load Balancer ADC | 否 | 是 | BNADC-16586 |
| Message Archiver (BMA) | 否 | 是 | BNMA-32468 |
| WAF Control Center (WCC) | 否 | 是 | BNWF-60060 |
| Web Application Firewall (WAF) | 否 | 是 | BNADC-16586 |
| Web Security Gateway (WSG) | 否 | 是 | BNYF-24789 |

**注意第一列只有 ESG 是「是」。** 这一点 watchTowr 特别强调过：

**单独看的话，用很英式的说法，两个都只是「不太理想」。但串起来就更糟了。**

**也就是说：那五个产品上的命令注入需要管理员账号，风险等级完全不同；只有 ESG 这一台能被「无需登录」这条链打通。**

不过厂商公告的 Guidance 段还是给了通用建议，我一并列出：

1. 给每个受影响产品打上对应补丁，或升级到公告里列出的修复固件；
2. **如果不能马上打补丁，把设备的管理界面限制到可信的内网**；
3. 如果你关掉了自动打补丁，把它打开。

第 2 条值得注意 —— 既然真正的门槛是「管理界面可达」，那么**把管理界面收到内网，就等于把这个链的第一步堵死**。这是一个不改一行代码就能拿到的缓解。

## 八、目前的利用状态：没有

两个漏洞目前都**没有**出现在 CISA 的 KEV 目录里，也**没有**公开报告把它们与任何攻击关联。

watchTowr **发布了检测工具**（在他们的 GitHub 上），可以检查设备是否受影响，但**没有发布利用代码**。

而 watchTowr 这篇博客的性质需要说清楚：他们的定位是「在野利用之前主动验证并缓解暴露面」，所以他们的研究和厂商公告是**几乎同一天**发布的（11-05），但**厂商的补丁比 watchTowr 的分析更早**（11-03 周一）。补丁先行、分析随后，这是负责任的披露顺序。

不过有一个历史阴影值得提：这台 ESG **在 2023 年被 UNC4841 用 CVE-2023-2868 当零日打过**，那次是**物理更换硬件**。watchTowr 在博客里直接用了「机架服务器的物理驱魔」这个说法。

**同一台设备、同一类攻击者、四年前后两个零日** —— 这个事实本身就说明，这类边界设备的价值不只在它今天跑什么补丁，还在于**它已经被盯上了**。

---

## Sources

- watchTowr Labs, *Barracuda Networks is your new best friend (Barracuda Email Security Gateway Pre-Auth Remote Root RCE CVE-2026-116606 / CVE-2026-111560)*（Sina Kheirkhah，2026-11-05）: <https://labs.watchtowr.com/barracuda-networks-is-your-new-best-friend-barracuda-email-security-gateway-pre-auth-remote-root-rce-cve-2026-116606-cve-2026-111560/>
- Barracuda Networks, *Pre-Authentication Authorization Bypass and Command Injection Vulnerabilities in Certain Barracuda Products*（2026-11-05，含当日 14:30 EST 的修订说明）: <https://trust.barracuda.com/security/pre-authentication-authorization-bypass-command-injection>
- The Hacker News, *Experts Demonstrate Barracuda Email Security Gateway Chain to Run Commands as Root Without Login*（2026-11-06, Swati Khandelwal）: <https://thehackernews.com/2026/11/experts-demonstrate-barracuda-email.html>
- SecurityWeek, *Barracuda ESG Authentication Bypass Flaw Opens Path to Root*（2026-11-04）: <https://www.securityweek.com/barracuda-email-security-gateway-authentication-bypass-opens-path-to-root/>
- BleepingComputer, *Barracuda warns of critical flaws allowing root access to devices*（2026-11-03）: <https://www.bleepingcomputer.com/news/security/barracuda-warns-of-critical-flaws-allowing-root-access-to-devices/>
- watchTowr Labs 检测工具（GitHub）: <https://github.com/watchtowrlabs/watchTowr-vs-Barracuda-RCE-CVE-2026-116606-CVE-2026-111560>

### 事实边界说明

- 两个漏洞的机理、补丁 diff、校验和算法与硬编码密钥、备份格式、复现请求结构：均引自 watchTowr Labs 原始分析。
- 受影响产品矩阵、补丁编号、以及「Authentication Required」字段的修订说明：引自 Barracuda 官方公告。
- **修复固件版本号的来源差异（公告的 BNSF-40425/40430 与 watchTowr 的 9.4.0.029、THN 的 9.4.0.030）：本文以厂商公告为准，并说明了差异存在。**
- 「补丁注释里的 CVSS 9.8 与公告的 9.3 不一致」及 watchTowr 对此的猜测（可能是把两个漏洞合起来算）：引自 watchTowr 原文。
- 未列入 CISA KEV、无公开攻击关联、watchTowr 发布了检测工具但未发布利用代码：引自 The Hacker News 报道。
- 2023 年 UNC4841 用 CVE-2023-2868 攻击 ESG 并导致物理更换硬件：引自 watchTowr 引用的 Mandiant 报告。
- 本文只做防守方视角的分析，不包含任何用于构造利用请求的 payload 或绕过方法。
