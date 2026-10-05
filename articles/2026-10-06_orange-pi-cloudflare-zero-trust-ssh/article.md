> 主题：零信任 · 隧道 · 身份认证 · 基础架构。本文为**原创架构复盘**，是《万物皆隧道》的续集。上一篇解决了「在家和在外用同一份配置」，这一篇解决一个更硬的约束：**你的公网 IPv4 根本不归你**。文中域名、IP、账号均已脱敏。

## 一句话结论

承接上一篇，我给香橙派又加了一条路：**Cloudflare 零信任隧道 + SSH 短时证书**。

结果是这样：同一台机器，三条路并存，分别对应三个场景。

```
ssh pi-ssh.example.net    → Cloudflare 隧道 + 短时证书   （IPv4 / 任意网络）
ssh pi6.example.net       → IPv6 直通                    （快，不经 CF）
ssh pi.lan                → 局域网直连                    （不走隧道）
```

而最关键的一点是：**每个访问端有自己的证书，有效期 3 分钟，自动轮换，没有可以长期偷走的凭据。**

## 为什么上一篇的架构还不够

上一篇的结论是「服务只听 127.0.0.1，隧道来拉」。那套东西在 **IPv6 直通**的前提下工作得很好。

但它有一个隐含假设：**你的服务有个能被外面访问到的入口**。而我家的入口是 IPv6 —— 只有 AAAA 记录。这意味着：

- **纯 IPv4 网络下连不上**（很多公共 Wi-Fi、公司网络、手机热点）
- 出门在外，能不能用完全看对方网络给不给 IPv6

于是很自然想到：那就给 IPv4 也加一条路，用 DDNS 把公网 IPv4 同步到 A 记录。

**结果发现这条路根本不存在。**

## 第一步：先确认你的公网 IPv4 到底是谁的

这个调查是整个故事的转折点。我登进光猫看 WAN 状态，看到的是：

```
INTERNET  PPPoE  已连接   IP地址 100.64.12.34   网关 100.64.0.1
```

`100.64.12.34` 这个地址落在 **`100.64.0.0/10`**，也就是 RFC 6598 定义的**运营商级 NAT（CGNAT）**地址段。

再看一个旁证就很清楚了：

```
光猫 WAN 地址  : 100.64.12.34     ← 运营商给你的，私网
实际出口地址   : 203.0.113.88    ← 互联网看到的
                   ↑ 两者不同 = 上游还有一层你无权配置的 NAT
```

**这是三重 NAT：**

```
香橙派(10.20.30.40) → 家用路由(10.20.30.1) → 光猫WAN(100.64.12.34)
                                                ↑ CGNAT，不属于你
                                                └→ 运营商NAT → 出口(117.x) → 互联网
```

结论很硬：**你在自己设备上做任何端口映射，都到不了公网**，因为那个"公网" IP 本身在运营商的私网里。

所以：

- ❌ DDNS 更新 A 记录：无意义，映射不进来
- ❌ 光猫/JD 路由上做端口转发：白做
- ✅ 只有一条路：**让内网主动往外连**

## 第二步：为什么不选 mTLS

你（本文的读者）可能会想：既然要"每个访问端独立证书"，那不就是 **mTLS（双向 TLS）**吗？

我认真试了，**三个硬约束让它走不通**：

| 约束 | 实测结果 |
|---|---|
| **套餐** | Cloudflare 官方文档明确：「Access mTLS 仅 Enterprise / pay-as-you-go，**不含 Free**」。我的账号实测是 `teams_free` |
| **客户端** | `cloudflared access ssh` 的参数里**没有任何客户端证书选项**（只有 header / service-token-id / service-token-secret） |
| **语义** | mTLS 是给 HTTP(S) 握手用的，而 SSH 隧道走 WebSocket 升级 |

也就是说：即使你花钱升级套餐拿到 mTLS，客户端 `cloudflared` 也不会在 SSH 流里带上那张客户端证书。

**顺带排除了另一个方案：Access Service Token。**

Service Token 也能做到"每端独立、可单独吊销"，而且 Free 可用。但它是**长期凭据**，我试着创建时默认有效期就是 `8760h`（一年）。一旦泄露，在有效期内一直能用。

**而短时证书的凭据……只有 3 分钟。**

## 第三步：整条链路长什么样

先看全景：

```
                    Internet
                        │
            ┌───────────┴────────────┐
            │  Cloudflare Edge        │
            │  · TLS 终止             │
            │  · Access 策略校验 JWT   │
            │  · 隧道接入点            │
            └───────────┬────────────┘
                        │  ①隧道主动外连（QUIC/HTTP2）
                        │   出口-only，不开任何入站端口
                        │
                 ┌──────┴───────┐
                 │  香橙派       │
                 │  cloudflared │
                 │      ↓       │
                 │  sshd :22    │  ← ②这里校验 CF 签发的短时证书
                 └──────────────┘

客户端：cloudflared（ProxyCommand）→ 现场申请证书 → 认证
```

**关键点：出口-only。** 香橙派从不接受入站连接，它主动连到 Cloudflare。所以 NAT 在第几层、有没有 CGNAT，**完全不重要**。

## 第四步：搭隧道的路上踩的坑

### 坑一：API token 权限不够，而且我不打算去求它

我一开始想用 Cloudflare API 脚本化创建隧道，结果：

```
POST /accounts/<id>/cfd_tunnel
→ {"code": 10000, "message": "Authentication error"}
```

我的 token 有 Tunnel 的**读**权限，但没有**写**权限（缺 `Cloudflare Tunnel: Edit`）。

**更优雅的解法**：`cloudflared` 自己带了一套免 API token 的流程。

```bash
cloudflared tunnel login      # 打开浏览器授权，生成 cert.pem
cloudflared tunnel create  pi-ssh
cloudflared tunnel route dns pi-ssh pi-ssh.example.net
```

`tunnel login` 会给你一个 URL，浏览器里点一下"授权这个域名"，认证信息就落到 `cert.pem`。此后 `create` / `route dns` 全由 cloudflared 自己完成。

**这条路更好，不只是因为绕开了权限**：凭据天然只存在那台机器上，而且整个流程可以完全在没有 API token 的环境里跑。

### 坑二：ingress 里两个"不写就不通"的配置

隧道建好后，第一次连接卡在这里：

```
Connection timed out during banner exchange
```

TCP 握手是通的（能连到 Cloudflare），但 SSH 协议根本走不起来。两个原因：

**① service 必须写 `ssh://`，不是 `tcp://`**

```yaml
ingress:
  - hostname: pi-ssh.example.net
    service: ssh://localhost:22        # ← ssh:// 而不是 tcp://
```

`ssh://` 会让 cloudflared 讲 SSH 的 WebSocket 协议，并在任何字节到达 sshd 之前先校验 Access 的 JWT。

**② 必须声明 `originRequest.access.audTag`**

```yaml
    originRequest:
      access:
        required: true
        teamName: myteam
        audTag:
          - <你的 Access 应用的 aud>
```

`audTag` 告诉隧道"只接受这个 Access 应用的 JWT"。**不写它，Access 保护的非 HTTP 路由会卡死在 banner exchange**。这个症状非常有误导性，看起来像网络问题，其实是鉴权没配完。

### 坑三：dashboard API 的读写行为不一致

创建 Access 应用和 SSH CA 时发现一个规律：

```
GET  /api/v4/...   → 可用（带浏览器 cookie 或 API token 都行）
POST /api/v4/...   → 常常 403，且返回 text/html 而不是 JSON
```

最后发现**最可靠的方式是用 dashboard 的 UI 按钮**：

```
Zero Trust → Access controls → Service credentials → SSH
  → Generate certificate → 选对应的 Access 应用
```

还有个小陷阱：SSH CA 的 API 端点是**按应用**的：

```
POST /accounts/<id>/access/apps/<app_id>/ca     ← 正确
POST /accounts/<id>/access/gateway_ca           ← 报 Authentication error
```

后者是账号级的另一个东西，不是我们要的。

## 第五步：每个访问端一张证书

这是本文最想讲的部分。

### 生成 CA，让服务器信任它

Cloudflare 会为你的 Access 应用生成一对 SSH CA 密钥：

```
CA 公钥: ecdsa-sha2-nistp256 AAAA... open-ssh-ca@cloudflareaccess.org
```

私钥在 Cloudflare 手里（它负责签发证书），公钥你装到服务器上（服务器用它验证签名）。**你手上没有 CA 私钥**，这正是零信任的意义：签发权不在你的基础设施上，即使服务器被攻破，攻击者也签不出新证书。

### 服务器端：让 sshd 信任这个 CA

在香橙派上放一个 drop-in：

```ini
# /etc/ssh/sshd_config.d/10-cloudflare-access-ca.conf
TrustedUserCAKeys /etc/ssh/cf_access_ca.pub
AuthorizedPrincipalsFile /etc/ssh/authorized_principals/%u
```

### 一个必须处理的身份不匹配

**这是整个流程里最容易卡住的地方。**

Cloudflare 签发证书时，**principal 固定取邮箱的本地部分**。我的邮箱是 `me@example.net`，所以：

```
证书 Key ID    : "me@example.net"
证书 Principals: me
```

但香橙派上的登录用户叫 **`myuser`**。而 sshd 的默认行为是：**证书里的 principal 必须等于你登录的那个用户名**。`me` ≠ `myuser`，认证直接失败。

**解法：`AuthorizedPrincipalsFile`。** 用一个文件声明"哪些 principal 可以登录这个账号"：

```
# /etc/ssh/authorized_principals/myuser
me
```

这样 Cloudflare 发来的 `me` 就能登进 `myuser` 账号，**不需要为此新建一个用户**。

（认证成功后的实测输出：`id -un` 返回 `myuser`。）

### 客户端：连之前现场领证书

客户端配置（`cloudflared access ssh-config --short-lived-cert` 能直接生成）：

```sshconfig
Match host pi-ssh.example.net exec "cloudflared access ssh-gen --hostname %h"
    ProxyCommand cloudflared access ssh --hostname %h
    IdentityFile ~/.cloudflared/%h-cf_key
    CertificateFile ~/.cloudflared/%h-cf_key-cert.pub
```

`Match ... exec` 的意思是：**每次连接前先跑 `ssh-gen`**，现场向 Cloudflare 申请一张新证书。然后 `ProxyCommand` 用这张证书走隧道进去。

### 3 分钟到底有多短？

实测一张证书：

```
Type       : ecdsa-sha2-nistp256-cert-v01@openssh.com user certificate
Key ID     : "me@example.net"
Valid      : from 2026-10-06T00:11:51 to 2026-10-06T00:15:51   ← 4 分钟
Principals : me
Extensions : permit-port-forwarding, permit-pty
```

Cloudflare 官方博客的原话是 **3 分钟**，并且特意解释了这个设计：

> "The 3-minute time window on the SSH certificate **only applies to the time window during which the user has to authenticate** to the target server; it does not apply to the length of the SSH session, **which can be arbitrarily longer than 3 minutes**."

**这句话是理解整个方案的关键：**

```
├─ 0s        你敲 ssh pi-ssh.example.net
├─ 0–3min    证书有效期窗口 ← 只有认证阶段
│            ssh-gen 现场签发 → 拿去认证
├─ 认证成功  证书使命完成（作废也无所谓）
└─ 之后      会话可以一直开着，几小时、几天都行
```

3 分钟这个数字的选择理由也很讲究：**够短**，降低证书被窃风险；**够长**，覆盖慢网络下的认证延迟，别让用户网络一慢就认证超时。

## 为什么这个方案值得做

把所有约束和结果放在一起看：

| | 传统 SSH 密钥 | Service Token | **短时证书** |
|---|---|---|---|
| 存在形式 | 长期私钥文件 | 长期 ID+Secret | **每次连接现签** |
| 泄露后果 | 一直可用 | 有效期内可用 | **3 分钟后失效** |
| 每端独立 | 是（但你得管 N 个密钥） | 是 | 是 |
| 手工轮换 | 要 | 要 | **不要** |
| 需要入站端口 | 要 | 要 | **不要** |
| CGNAT 下可用 | 否 | 否 | **是** |
| 免费套餐 | — | 是 | 是 |

一句话：**它把"凭据管理"这件事从你的待办清单上删掉了。** 没有长期密钥要生成、分发、备份、轮换、吊销。攻击者即使拿到证书，3 分钟后它自己就死了。

而且因为走的是**出口-only 隧道**，你的服务器上没有开放任何入站端口，攻击面比"开个 22 端口 + 防火墙规则"小得多。

## 遇到的三个非技术坑

写下来是因为它们跟 Cloudflare 无关，但会让你多花几小时：

**① 本机的 Go 二进制出网被拦**

`cloudflared` 的 WebSocket 连接一直卡住不返回。一开始我以为是 DNS 超时，查了半天。

真相是：**这台机器上有个设备级出网过滤器，专门拦 Go 编译的二进制**。同环境下 `python` 和 `curl` 一切正常，唯独 Go 程序连不上任何外部 TCP。

关掉那个过滤器（我本机是 OpenSnitch 应用防火墙没给 cloudflared 放行）之后，WebSocket 立刻升级成功（`HTTP/1.1 101 Switching Protocols`）。

**教训**：排查"某个程序连不上网"时，先做一个对照实验：**换一个非同类实现试同一个目标**。如果 `python` 通而 Go 不通，那问题八成不在网络层，而在这个程序本身被区别对待了。

**② 首次连接需要一次浏览器授权**

`cloudflared access ssh` 第一次会打印一个 URL：

```
A browser window should have opened at the following URL:
https://pi-ssh.example.net/cdn-cgi/access/cli?aud=...
```

浏览器里完成一次登录，JWT 就缓存到 `~/.cloudflared/`，之后连接免交互。

**③ 别让本机做代理**

这个坑是我自己犯的：我一开始想用本机的代理去跑 Cloudflare API，但那既多余又会绕远。**隧道就该在那台服务器上建、在那台服务器上跑**，一条命令的事，还省掉一整层依赖。

## 最终的形态

回头看，这条路径解决的是一个**所有权**问题，而不只是连通性问题：

| | 上一篇（IPv6 直通） | 这一篇（CF 零信任） |
|---|---|---|
| 入口 | 必须有公网可达地址 | **主动外连，不需要任何入口** |
| CGNAT | 不受影响（走 v6） | **完全无关** |
| 纯 IPv4 网络 | ❌ 连不上 | ✅ 可用 |
| 认证 | SSH 密钥 | **短时证书 + Access 策略** |
| 凭据管理 | 自己管 | **没有凭据要管** |

所以最后是三条路并存，各管一个场景：

```
pi-ssh.example.net    → CF 隧道 + 短时证书   （最通用，IPv4/IPv6 都行）
pi6.example.net       → IPv6 直通            （最快，但对方得有 v6）
pi.lan                → LAN                  （在家，不走隧道）
```

**如果你也发现自己家宽是 CGNAT，别在端口映射上浪费时间了。** 让内网主动往外连，用零信任网关做认证，这条路才是通的。

---

*本文涉及的域名、IP、账号、隧道/应用/CA 标识符均已脱敏替换为保留示例值。基于一次真实的三重 NAT 环境下的零信任改造整理。*
