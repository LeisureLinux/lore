---
title: "输入邮箱和密码，服务器自己找上来：给自建邮件域做一套 autoconfig"
date: 2026-10-22
slug: mail-autoconfig-thunderbird-k9-zero-touch-setup
tags: [邮件自动配置, autoconfig, Thunderbird, K-9 Mail, SRV 记录, Let's Encrypt, nginx, fail2ban, RFC 6186, Cloudflare]
category: 运维/实践
author: FreeLAMP.com
description: "自建邮件服务器最烦的不是搭，是每换一台设备都要手填四个服务器字段，还经常被客户端自动探测猜错。本文用 SRV 记录 + autoconfig XML + Let's Encrypt 扩域三件套，让手机客户端只输邮箱和密码就能配好。文末附一个真实的踩坑：fail2ban 把运维者自己的 IP 封了，而排查过程中给出的三个错误结论，全都是因为测试方法不可靠。"
published: true
---

> **一句话结论**：邮件客户端自动配置不是玄学，是三条标准通道的叠加——**SRV 记录（DNS 层）**、**autoconfig XML（HTTP 层）**、**证书覆盖面（TLS 层）**。缺任何一条，客户端就会退回手动配置。而判断「哪条生效了」的唯一可靠方法，是看客户端界面；端口探测工具给出的结论经常是错的（本文有血例）。

## 术语速查

| 术语 | 含义 |
|---|---|
| **autoconfig** | Mozilla 主导的邮件客户端配置发现协议，客户端按固定 URL 拉一份 XML |
| **autodiscover** | 微软同名协议，Outlook 系用 |
| **SRV 记录** | DNS 服务记录，能声明「某服务在某主机某端口」 |
| **RFC 6186** | 用 SRV 记录发现邮件提交/收取服务的标准 |
| **ISPDB** | Mozilla 维护的配置库，`autoconfig.thunderbird.net` |
| **EMAILLOCALPART** | autoconfig XML 里的占位符，指 `@` 前那段（本文的关键点） |
| **STARTTLS** | 先明文连再升级 TLS，通常 587 端口 |
| **隐式 TLS** | 连接即 TLS，通常 993 / 465 端口 |

## 一、问题：为什么手动配置总是出岔子

自建邮件服务器的人都有一个共同经历：**每台新设备都要填四个字段**——收件服务器、收件端口、发件服务器、发件端口。

更要命的是客户端「自动探测」经常猜错。实测一台 Android 手机配 Thunderbird，自动探测失败后进入手动配置页，界面里被预填了这些值：

```
服务器   .example.com         ← 丢了主机名前缀
端口     465                  ← 猜的，实际用 587
用户名   user@example.com     ← 服务器要的是 user，不带 @
```

三个字段全错。这三个错各有各的成因，正好对应本文要解决的三层问题。

### 客户端到底怎么「自动探测」的

主流客户端（Thunderbird、K-9、iOS Mail、Outlook）按大致相同的顺序尝试：

1. **猜常见主机名**：`imap.<domain>`、`mail.<domain>`、`pop3.<domain>`、`smtp.<domain>`，配常见端口
2. **查 SRV 记录**（RFC 6186）：`_imaps._tcp.<domain>`、`_submissions._tcp.<domain>`
3. **拉 autoconfig XML**：`https://autoconfig.<domain>/mail/config-v1.1.xml`
4. **查 Mozilla ISPDB**：`https://autoconfig.thunderbird.net/v1.1/<domain>`
5. 全失败 → 退回手动配置

**第 1 步是绝大多数「猜错」的来源**，因为它对 `imap.<domain>` 这类名字是硬编码猜测，不校验真实性。

## 二、第一层：SRV 记录（最容易，但未必够）

RFC 6186 定义了用 SRV 记录声明邮件服务位置：

```dns
; 收件：IMAP over TLS
_imaps._tcp.example.com.        IN SRV 0 1 993 mail.example.com.
; 发件：submission（客户端提交）
_submissions._tcp.example.com.  IN SRV 0 1 587 mail.example.com.
; 兼容旧写法
_submission._tcp.example.com.   IN SRV 0 1 587 mail.example.com.
```

参数含义：`优先级 权重 端口 目标`。

Cloudflare 上通过 API 添加（SRV 记录不能用通配符代理，必须 `proxied=false`）：

```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "SRV",
    "name": "_imaps._tcp.example.com",
    "ttl": 300,
    "data": {
      "service": "imaps", "proto": "tcp", "name": "@",
      "priority": 0, "weight": 1, "port": 993,
      "target": "mail.example.com."
    }
  }'
```

验证：

```bash
dig +tcp +short SRV _imaps._tcp.example.com @1.1.1.1
# 0 1 993 mail.example.com.
```

> **⚠️ 一个陷阱**：`dig` 的 UDP 查询在丢包时会静默返回空结果，看起来像「记录不存在」。**判断 SRV 是否生效请加 `+tcp`**，或者直接查权威 NS。

### 但 SRV 未必被读取

本文实测：K-9 Mail 24.0 在**只有 SRV 记录**的情况下，自动配置**依然失败**，界面显示「未找到配置」。

加了 autoconfig XML 之后，同一个客户端立刻显示「找到配置」。

**结论：SRV 记录是加分项，不是充分条件。** 对 Android 上的 K-9 / Thunderbird，真正起决定作用的是 autoconfig XML。

## 三、第二层：autoconfig XML（真正管用的那一层）

### 3.1 客户端会去哪里拉

按优先级：

```
https://autoconfig.<domain>/mail/config-v1.1.xml?emailaddress=user@domain
https://<domain>/.well-known/autoconfig/mail/config-v1.1.xml?emailaddress=...
http://autoconfig.<domain>/mail/config-v1.1.xml          ← 有些客户端先试 80
```

### 3.2 XML 长什么样

```xml
<?xml version="1.0" encoding="UTF-8"?>
<clientConfig version="1.1">
  <emailProvider id="example.com">
    <domain>example.com</domain>
    <displayName>Example Mail</displayName>
    <displayShortName>Example</displayShortName>
    <incomingServer type="imap">
      <hostname>mail.example.com</hostname>
      <port>993</port>
      <socketType>SSL</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILLOCALPART%</username>
    </incomingServer>
    <outgoingServer type="smtp">
      <hostname>mail.example.com</hostname>
      <port>587</port>
      <socketType>STARTTLS</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILLOCALPART%</username>
    </outgoingServer>
    <documentation url="https://example.com/">
      <descr lang="en">Example mail service</descr>
    </documentation>
  </emailProvider>
</clientConfig>
```

### 3.3 最关键的一行：`%EMAILLOCALPART%` vs `%EMAILADDRESS%`

这是本文最有价值的一个细节。两个占位符：

| 占位符 | 替换结果 |
|---|---|
| `%EMAILADDRESS%` | `user@example.com`（完整地址） |
| `%EMAILLOCALPART%` | `user`（只有 @ 前那段） |

**大多数教程写 `%EMAILADDRESS%`**，因为多数邮件服务商用完整地址登录。但自建 Dovecot 常见的配置是**用系统用户名登录**，不带域名。

本文实测的服务器就是这种情况：

```
用户输入：user@example.com
服务器要：user
```

写错这一行的后果，就是手动配置时那个「用户名被预填成完整邮箱」然后认证失败的现象。

**如果你不确定服务器要哪种，看 Dovecot 的 `auth_username_format`，或者直接用 `doveadm auth test <user>` 试。**

### 3.4 socketType 取值

| 值 | 含义 | 常见端口 |
|---|---|---|
| `SSL` | 隐式 TLS，连接即加密 | 993 / 465 |
| `STARTTLS` | 先明文再升级 | 143 / 587 |
| `plain` | 不加密（别用） | — |

## 四、第三层：证书必须覆盖 autoconfig 这个域名

这一层最容易被忽略，而且**失败时是静默的**。

客户端拉 `https://autoconfig.example.com/...` 时，会做**标准 TLS 证书校验**。如果服务器证书里没有 `autoconfig.example.com` 这个 SAN，客户端直接放弃——**不会回退到「忽略证书错误」**。

本文实测踩到的就是这个：源站证书只有 `CN=mail.example.com`，把 `autoconfig` 指过去之后：

```
$ curl -v https://autoconfig.example.com/mail/config-v1.1.xml
* TLS verify error: certificate subject name does not match
```

而用 `openssl s_client` 看证书：

```
X509v3 Subject Alternative Name:
    DNS:mail.example.com          ← 只有这一个
```

### 扩域：certbot 一行命令

如果已经用 Let's Encrypt + DNS 验证，加一个域名非常轻量（**不需要停服务、不需要 80 端口**）：

```bash
certbot certonly --expand --cert-name mail.example.com \
  -d mail.example.com -d autoconfig.example.com \
  --authenticator dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 30 \
  --non-interactive --agree-tos
```

验证：

```bash
openssl x509 -in /etc/letsencrypt/live/mail.example.com/cert.pem \
  -noout -subject -ext subjectAltName -enddate
```

输出应当同时包含两个域名：

```
X509v3 Subject Alternative Name:
    DNS:autoconfig.example.com, DNS:mail.example.com
notAfter=Jan 20 12:15:21 2027 GMT
```

> **注意 `--expand` 是累加，不是替换。** 它会保留原有域名并加入新的。续期配置也会自动更新，之后 `certbot renew` 会带上新域名。

## 五、DNS：通配符会遮住你的 autoconfig

如果域名有一条通配符记录（用于防扫描，让随机子域都指向黑洞）：

```dns
*.example.com   A     127.0.0.1
*.example.com   AAAA  ::1
```

那么 `autoconfig.example.com` 会命中通配符，解析到 `127.0.0.1`——**客户端连的是自己本身**。

必须加**独立记录**覆盖通配符：

```dns
autoconfig.example.com   A      <源站 IPv4>
autoconfig.example.com   AAAA   <源站 IPv6>
```

DNS 里**精确匹配优先于通配符**，所以这个覆盖是可靠的。

验证：

```bash
dig +short A    autoconfig.example.com @1.1.1.1
dig +short AAAA autoconfig.example.com @1.1.1.1
```

## 六、nginx 配置：把 XML 直接内联

不必单独放一个 XML 文件，用 nginx 的 `return 200` 直接吐内容，少一个文件路径要维护：

```nginx
server {
    server_name autoconfig.example.com;
    listen 443 ssl;
    listen [::]:443 ssl;

    ssl_certificate     /etc/letsencrypt/live/mail.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mail.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location = /mail/config-v1.1.xml {
        default_type application/xml;
        add_header Access-Control-Allow-Origin "*" always;
        add_header Cache-Control "public, max-age=3600" always;
        return 200 '<?xml version="1.0" encoding="UTF-8"?>
<clientConfig version="1.1">
  <emailProvider id="example.com">
    <domain>example.com</domain>
    <incomingServer type="imap">
      <hostname>mail.example.com</hostname>
      <port>993</port>
      <socketType>SSL</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILLOCALPART%</username>
    </incomingServer>
    <outgoingServer type="smtp">
      <hostname>mail.example.com</hostname>
      <port>587</port>
      <socketType>STARTTLS</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILLOCALPART%</username>
    </outgoingServer>
  </emailProvider>
</clientConfig>
';
    }

    location = /.well-known/autoconfig/mail/config-v1.1.xml {
        return 302 /mail/config-v1.1.xml;
    }

    location / { return 404; }
}

# 80 端口也提供一份：有些客户端先试 http
server {
    server_name autoconfig.example.com;
    listen 80;
    listen [::]:80;

    location = /mail/config-v1.1.xml {
        default_type application/xml;
        # 同一份 XML
        return 200 '...';
    }

    location / { return 301 https://$host$request_uri; }
}
```

要点：

- `location =`（精确匹配）优先于前缀匹配，不会和其它 location 抢
- `add_header ... always` 保证非 2xx 也带 CORS 头
- **80 端口也放一份**，因为部分客户端会先试 http 再升级
- `.well-known` 路径用 302 转发，避免维护两份 XML

### 验证服务端确实正常

```bash
curl -q -sS --max-time 15 \
  "https://autoconfig.example.com/mail/config-v1.1.xml?emailaddress=user@example.com"
```

`-q` 会禁用 `~/.curlrc`。如果环境里有 `https_proxy`，curl 会走代理，输出里会多一行 `HTTP/1.1 200 Connection Established`——这是正常的。

## 七、为什么用 nginx 而不是 Cloudflare Worker

Worker 方案看起来更干净（不用碰源站），但有两个前提：

1. **API Token 必须有 Workers 写权限**。本文实测一个只开了 DNS 权限的 Token，调用 `PUT /accounts/{id}/workers/scripts/{name}` 返回 `{"message": "No access to the specified resource."}`
2. **`autoconfig` 子域不能用 Worker 路由绑定的橙云代理**，否则 SRV 类的记录冲突

如果源站已经有 nginx + Let's Encrypt，扩证书 + 加 server block 反而更简单，而且不引入新依赖。

## 八、最终验证：只看客户端界面

这是本文最想强调的一点。

**DNS 通了、证书对了、curl 拿得到 XML，都不代表客户端会自动配置成功。** 唯一可靠的验证是在一台没配过的设备上输入邮箱地址，看是否出现「找到配置」。

本文实测对比：

| 配置方式 | 客户端表现 |
|---|---|
| 仅 SRV 记录 | 「未找到配置」，进手动配置页 |
| 加了 autoconfig XML | **「找到配置」**，用户名自动推断正确，并识别到 `Sent` / `Junk` / `Trash` 文件夹 |

第二行的差别不只是「少填四个字段」——客户端还自动发现了发件箱文件夹，而这个在手动配置时经常被漏掉。

## 九、踩坑附录：fail2ban 把自己封了

这一段值得单独写，因为它是一个非常典型的「诊断方法本身制造了故障」。

### 现象

配好 autoconfig 后，想验证发信端口是否可用，用了几种传统探测手法：

```bash
openssl s_client -connect mail.example.com:587
nc -w 5 mail.example.com 587 < /dev/null
echo > /dev/tcp/mail.example.com/587
```

结果全部是：

```
connect:errno=111        # Connection refused
```

但**同一时刻，手机上的邮件客户端发信是成功的**——服务器日志里有完整记录：

```
postfix/submission/smtpd: connect from unknown[<客户端 IP>]
  sasl_method=PLAIN, sasl_username=<user>
  disconnect ... ehlo=2 starttls=1 auth=1 mail=1 rcpt=1 data=1 quit=1
```

`auth=1 mail=1 rcpt=1 data=1` 说明整条发信流程走完了。

### 根因

服务器的 fail2ban 有一个 jail 叫 `postfix-scanners`，filter 规则是：

```
failregex = ...
            ^...disconnect from ...\[<HOST>\] commands=0/0$
```

**「TCP 连上，但不发任何 SMTP 命令就断开」= 判定为扫描器。**

而 `openssl s_client`、`nc -w`、`/dev/tcp` 这三种探测手法，行为**恰好就是连上不说话就关**。每试一次算一次违规，`maxretry=3` 之后：

```
fail2ban: [postfix-scanners] Found <IP>
fail2ban: [postfix-scanners] Ban   <IP>
```

封禁动作是 iptables 的 `REJECT --reject-with icmp-port-unreachable`——`icmp-port-unreachable` 映射到用户态就是 **`errno=111 Connection refused`**。

于是形成了一个完美的自我欺骗闭环：**探测工具被自己的行为封掉，然后把「被封」误读成「端口不通」。**

更讽刺的是：解封之后立刻又跑了一遍同样的探测，**又被封了一次**。

```
21:06:33  Unban  <PC IP>
21:06:48  Found  <PC IP>     ← 解封后 15 秒
21:06:52  Ban    <PC IP>
```

### 教训

**第一，`Connection refused` 和「端口关闭」不是同一件事。** 防火墙 `REJECT` 也会产生 refused。区分方法是看服务端有没有收到连接——如果服务端日志显示「连上了」，那 refused 一定来自中间环节。

**第二，端口探测要模拟真实协议**。正确的探测方式：

```bash
python3 - <<'PY'
import socket
s = socket.create_connection((host, 587), timeout=8)
f = s.makefile('rwb', 0)
print(f.readline().decode())          # 220 banner
f.write(b"EHLO probe.local\r\n")
while True:
    line = f.readline().decode()
    if not line or line[3:4] == ' ': break
    print(line)
f.write(b"QUIT\r\n")
s.close()
PY
```

能看到 `220 ... ESMTP` 和 `250-STARTTLS` 才算真的通。

**第三，给自家网络加 fail2ban 白名单**。IPv6 隐私地址会轮换，但运营商分配的 `/64` 前缀稳定，按前缀豁免即可：

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1
           <你的 IPv6 /64 前缀>
           192.168.0.0/16
           <服务器自己的公网 IP>
```

验证各 jail 都继承了：

```bash
fail2ban-client get postfix-scanners ignoreip
```

**第四，`commands=0/0` 这条规则本身偏激进。** 它对正常客户端也会误伤——TLS 握手失败、网络抖动导致的中断都会命中。考虑把 `maxretry` 提到 5，或缩短 `findtime`。

### 一个方法论层面的反思

排查过程中我给过三个结论，全部是错的：

1. 「客户端走了代理」——实测无 tun 设备、无 VPN 连接
2. 「云厂商封了发信端口」——控制台防火墙显示 25/465/587 全部放行
3. 「服务器自己都连不上，所以是云厂商限流」——服务器自己的 IP 也在 fail2ban 黑名单里

三个错误的共同原因是：**把一个间接信号（探测工具的返回码）当成了一手证据，而没有去看服务端日志**。服务端日志从头到尾都写着 `connect` 和 `auth=1`，只要看一眼就能推翻所有猜测。

## 十、检查清单

部署 autoconfig 时按这个顺序排查：

| 步骤 | 命令 | 通过标准 |
|---|---|---|
| 1. DNS 覆盖通配符 | `dig +short A autoconfig.<domain>` | 返回真实 IP，不是 `127.0.0.1` |
| 2. 证书含 SAN | `openssl x509 -ext subjectAltName` | 包含 `autoconfig.<domain>` |
| 3. nginx 能吐 XML | `curl -q -sS https://autoconfig.<domain>/mail/config-v1.1.xml` | HTTP 200，XML 完整 |
| 4. HTTP 80 也可用 | `curl -q -sS http://autoconfig.<domain>/mail/config-v1.1.xml` | HTTP 200 |
| 5. `%EMAILLOCALPART%` 正确 | 看 Dovecot `auth_username_format` | 与实际登录名一致 |
| 6. **客户端真实测试** | 新设备只输邮箱地址 | 出现「找到配置」 |

前五步全是间接验证。**第六步才是结论。**

---

**本文所有域名、IP、用户名为脱敏后的占位值。** 配置方法本身可直接套用到任何自建邮件域。

---

*本文同步发布于微信公众号「LeisureLinux」与 B站「LeisureLinux」（视频版）。*
