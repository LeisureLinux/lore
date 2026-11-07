---
title: "Vercel 接入 DBSC：浏览器开始证明「是我这台机器」"
date: 2026-11-07
slug: vercel-dbsc-device-bound-session
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Chrome 官方文档《Device Bound Session Credentials (DBSC)》的完整实现规范与回退行为说明 ＋ TechRepublic《Vercel Introduces DBSC: How It Protects Against Cookie Theft》（Joseph Ofonagoro，2026-11-06）＋ Google 官方博客《Protecting Cookies with Device Bound Session Credentials》（2026-04-09，Chrome 146 Windows 公开可用）＋ Vercel CTO Malte Ubl 的 X 公告（2026-11-03）＋ W3C WebAppSec DBSC 规范"
original_date: 2026-11-06
original_url: "https://www.techrepublic.com/article/news-vercel-dbsc-session-cookie-theft-protection/"
description: "本文解读 Vercel 于 2026 年 11 月 3 日宣布接入 Device Bound Session Credentials（DBSC），并结合 Chrome 官方实现规范讲清楚这件事到底做了什么、以及它的边界在哪里。会话 cookie 被窃取后重放，是当前最有效也最无解的账号接管路径 —— infostealer 偷走 cookie，攻击者在另一台设备导入，就完全跳过了密码和多因素认证。DBSC 的做法是给浏览器发一对密钥，私钥存在硬件里（TPM 或 Secure Enclave），会话改成短时效 cookie，每次续期都要用私钥签名证明「我还是原来那台设备」。攻击者偷到 cookie 却没有私钥，服务端就能拒绝续期。**但这篇报道里最容易被跳过的三个限定，都在 Chrome 官方文档里写得很清楚**：①**DBSC 只保护 cookie 的续期，不保护注册那一刻**——官方明确写着「如果恶意软件在会话注册期间就在设备上，它可能能够提取私钥」，只是说这种攻击「比标准的 cookie 窃取复杂得多且更容易被发现」；②**Chrome 会静默跳过 DBSC 操作并回退到长时效 cookie**，触发条件包括刷新端点不可达、TPM 忙或签名出错（因为 TPM 是全系统进程共享的，过于频繁的刷新可能超出它的速率限制）、以及 DBSC 管理的短时效 cookie 属于第三方 cookie 而用户屏蔽了第三方 cookie——**这个回退只有在你同时保留长时效和短时效两个 cookie 时才有效**；③**DBSC 只适用于 HTTPS 页面，不支持 Partitioned cookie，也不保护 HTTP 请求**。Vercel 的实现跟随 Chrome 在 Windows 上的 Chrome 146 与 macOS 上的 Chrome 148，目前只支持 Chrome，且正在逐步放量。这件事真正值得注意的地方在于它代表的方向：现代安全措施越来越依赖硬件能力而不只是软件更新——Windows 11 安装已要求 TPM 2.0，BitLocker 与 Windows Hello 也依赖它。对没有兼容硬件的旧设备，这些新保护直接缺席。"
published: true
---

> 原文：TechRepublic《Vercel Introduces DBSC: How It Protects Against Cookie Theft》（Joseph Ofonagoro，2026-11-06）
> 原文链接：<https://www.techrepublic.com/article/news-vercel-dbsc-session-cookie-theft-protection/>
>
> 本文依据 Chrome 官方 DBSC 实现文档、Google 的发布博客、Vercel CTO 的公告，以及 W3C WebAppSec 的 DBSC 规范。

## 一、先说清楚：DBSC 解决的是哪一步

先把攻击链摆出来，文章后面才不会绕。

会话 cookie 之所以是当前最有效的账号接管路径，是因为它**同时绕过了密码和多因素认证**：

1. infostealer 感染开发者的电脑，偷走 Vercel 的会话 cookie；
2. 攻击者把这个 cookie 导入另一台浏览器；
3. 服务端看到有效 cookie，**直接放行** —— 没有密码，没有 MFA。

TechRepublic 原文的表述是：攻击者可以「把那个 cookie 导入另一个浏览器来访问开发者的账号，无需输入密码，**也无需再次通过 MFA**」。

**DBSC 针对的正是第 3 步。**

它的做法是：给设备发一对密钥，私钥存在硬件里，会话 cookie 改成短时效的，每次续期都要用私钥签名证明「我还是原来那台设备」。

Chrome 官方文档的描述更精确：

Chrome 在登录时生成这对密钥，并在可用时把私钥存进安全硬件（比如 TPM）。**会话使用短时效 cookie；其中之一过期时，Chrome 会在刷新它们之前证明私钥的持有。**

所以攻击者的处境变成了：**cookie 偷到了，私钥没偷到。** 服务端在续期环节拒绝他，会话就断了。

Vercel CTO Malte Ubl 在 X 上宣布这件事时，说的也是同一件事：浏览器在续期会话前必须证明持有私钥。

## 二、完整流程：注册、挑战、签名、续期

Chrome 官方文档给了完整的四步交互，我按原文梳理：

### 第 1 步：登录后返回长时效 cookie + 一个特殊 header

```
HTTP/1.1 200 OK
Secure-Session-Registration: (ES256 RS256); path="/StartSession"
Set-Cookie: auth_cookie=session_id; max-age=2592000; Domain=example.com; Secure; SameSite=Lax
```

### 第 2 步：Chrome 把公钥送到会话注册端点

如果设备支持安全密钥存储，Chrome 会带一个 **JWT 格式的公钥**去请求 `/StartSession`。服务端要做三件事：把公钥关联到该用户会话、下发会话配置、**把长时效 cookie 换成短时效的**。

短时效 cookie 示例里 `Max-Age=600`，也就是 **10 分钟**。

### 第 3 步：续期时来一轮「挑战—签名」

这是整个机制的核心，四次往返：

```
1. Chrome 暂缓原始请求，发起刷新请求
   POST /RefreshEndpoint HTTP/1.1
   Sec-Secure-Session-Id: session_id

2. 服务端下发挑战
   HTTP/1.1 403 Forbidden
   Secure-Session-Challenge: "challenge_value"

3. Chrome 用存储的私钥签署挑战，重试请求
   POST /RefreshEndpoint HTTP/1.1
   Sec-Secure-Session-Id: session_id
   Secure-Session-Response: <JWT proof>

4. 服务端校验签名证明，下发新的短时效 cookie
   HTTP/1.1 200 OK
   Set-Cookie: auth_cookie=short_lived_grant; Max-Age=600; ...
```

**第 2 步那个 403 是刻意设计的** —— 它不是错误，是挑战。服务端用 403 + `Secure-Session-Challenge` 把挑战递过去，Chrome 签完再重试。

而攻击者卡在第 3 步：**他没有私钥，签不出那个 JWT proof。**

## 三、三个容易被跳过的限定

这一节是我认为整篇文章最该被读到的部分 —— 因为**媒体报道基本只讲了「cookie 偷了也没用」，而这三个限定恰恰划出了它的真实边界**。而它们全都写在 Chrome 官方文档里。

### 限定一：它不保护注册那一刻

官方文档里有一句很克制的警告（Caution）：

> If malware is present on the device during session registration, **it may be able to extract the private key.** This could enable session hijacking similar to other styles of cookie theft. However, attacks involving malware during registration or TPM driver modification are **significantly more complex and detectable** than standard attacks.

（**这一段是全文我唯一想原样保留的英文** —— 因为它是整个机制最关键的一处边界，也是媒体报道基本没提的那一处：**如果恶意软件在会话注册期间就在设备上，它可能能够提取私钥**；但涉及注册期间恶意软件或 TPM 驱动修改的攻击，比标准攻击**复杂得多且更容易被发现**。）

**这是整个机制最关键的一处边界**：DBSC 防的是「cookie 被偷走后在别处重放」，**不防「在设备上当面偷私钥」**。

也就是说，如果一台机器已经被彻底拿下了，攻击者可以在受害者登录的那一刻就把新生成的私钥一起导走 —— 那 DBSC 对他就无效了。

**但注意后半句**：官方说这种攻击「复杂得多且更容易被发现」。这不是一个零成本绕过，而是一个**成本与可发现性都更高**的攻击路径。安全机制很少能做到「不可绕过」，能做到「绕过代价更高、可被发现」已经是实质性的提升。

### 限定二：Chrome 会静默回退，而且回退可能让你以为保护生效了

这是最容易被忽略、也最值得单独拎出来的一条。官方文档列了三种 Chrome 会**跳过 DBSC 操作**、直接发不带 DBSC 短时效 cookie 的情况：

| 情况 | 说明 |
|---|---|
| 刷新端点因网络错误或服务端问题不可达 | 静默跳过 |
| **TPM 忙或签名出错** | 「因为 TPM 是全系统进程共享的，过于频繁的刷新可能超出它的速率限制」 |
| DBSC 短时效 cookie 属于第三方 cookie，而用户屏蔽了第三方 cookie | 浏览器设置导致 |

**然后是最关键的一句**：

**在这些情况下，如果长时效 cookie 还在，Chrome 会回退到使用它。这个回退只有在你同时实现了长时效和短时效两个 cookie 时才有效。否则，Chrome 会不带 cookie 发送请求。**

**这段话对防守方极其重要，因为它意味着：**

**如果你的实现只发短时效 cookie**（不保留长时效那个），那么回退的结果是「请求不带 cookie」→ 用户被登出。这虽然吵，但至少不是静默降级。

**但如果你同时保留了两个 cookie**（官方推荐的「替代集成模式」，为了提高韧性），那么回退的结果是「静默退回长时效 cookie」—— **而用户和运维都不会收到任何提示**。

也就是说，**DBSC 在这种情况下可能完全没有生效，而从外面看不出来。**

官方推荐的「替代集成模式」原文是：

官方推荐的「替代集成模式」是：**在短时效 cookie 旁边再加一个非 DBSC 的长时效 cookie**，后者只用来签发新的短时效令牌，并帮助区分「真正未认证的请求」与「DBSC 的临时故障」。

这个模式本身是好的设计，但它与回退机制叠加起来，就产生了上面那个「静默降级」的结果。

**所以 IT 团队真正该做的核对动作是**：Chrome 文档里 Cloudflare Zero Wire 在分析 SSHole 那类问题时也强调过类似的态度 —— **别假设浏览器端的安全特性一定开着，要去实测确认**。而 TechRepublic 原文也提到了这一点，说 IT 团队应当「确认自己管理的设备是否支持 DBSC，以及随着 Vercel 逐步放量该功能是否真的对用户生效」。

### 限定三：只适用于 HTTPS，不支持 Partitioned cookie

官方文档的 Note 写得很短但很硬：

**DBSC 只适用于 HTTPS 页面，不支持 Partitioned cookie。**虽然 DBSC 不强制要求 cookie 带 `Secure` 属性，但 **HTTP 请求不受 DBSC 保护**。

这一条的实际影响是：**如果你的站点还有 HTTP 入口（比如强制跳转前的那个 301 页面、或者 API 的 http:// 版本），那些流量不受任何保护。**

## 四、Vercel 这边的具体情况

| 项 | 值 |
|---|---|
| 宣布时间 | 2026-11-03（Vercel CTO Malte Ubl 在 X 上发布） |
| 分析文章 | TechRepublic，2026-11-06，作者 Joseph Ofonagoro |
| 浏览器支持 | 目前**仅 Chrome**；跟随 Chrome 在 Windows 上的 146 版、macOS 上的 148 版 |
| 硬件要求 | Windows 用 TPM；macOS 用 Apple Secure Enclave |
| 放量方式 | 正在向 Vercel 用户逐步放量 |

TechRepublic 原文特别点出了 Chrome 版本号的来源：**「Vercel 的实现跟随 Google 在 Chrome 146（Windows）和 Chrome 148（macOS）中引入的 DBSC 支持。」**

而这个特性本身的时间线是：Google 在 2026 年 4 月 9 日的官方博客里宣布 DBSC **对 Windows 上的 Chrome 146 用户公开可用**，并说 macOS 支持将在后续的 Chrome 版本中跟进。

**所以 Vercel 是这批平台里动作比较快的一批** —— Chrome 的公开可用是 4 月，Vercel 到 11 月初才宣布接入，中间隔了七个月。这个时间差本身也说明：**DBSC 的普及速度取决于服务端改造意愿，而不是浏览器支持进度。**

因为服务端要做的事并不少：

1. 改登录流程，加 `Secure-Session-Registration` header；
2. 加一个会话注册端点（关联公钥、下发配置、切换短时效 cookie）；
3. 加一个刷新端点（处理挑战、校验签名证明、下发新 cookie）。

而**收益是渐进的** —— 只有当用户已经注册过 DBSC 会话之后，cookie 重放才被挡住。

## 五、硬件门槛这件事，值得单独说

DBSC 需要安全密钥存储，而这就带来了一个硬件依赖。TechRepublic 原文的判断是：

**没有兼容 TPM 的机器、TPM 对 Chrome 不可用的机器，可能享受不到 DBSC。**（原文的表述是：硬件要求可能限制谁从 Vercel 的新保护中受益。）

这一条不是 Vercel 的问题，是整个现代安全趋势的一个缩影。TechRepublic 把它和更广的转变联系了起来：

**比如说，微软的 Windows 11 安装本身就要求 TPM 2.0**，部分原因是它的若干安全能力依赖这项技术来做安全密钥存储、加密和设备完整性检查。**BitLocker 和 Windows Hello** 之类的功能也用 TPM 能力来强化数据与身份保护。

而原文的结论句是：

**Vercel 的这个保护，是「现代安全措施越来越依赖硬件能力而非仅靠软件更新」的又一个例子。** 因此，使用较旧或不受支持硬件的用户，可能会错过这些专为保护账号安全而设计的新防护。

**我觉得这个观察比 DBSC 本身更值得记。** 因为它的含义是双向的：

- **好的一面**：DBSC 对**已经在用现代硬件、且跑 Chrome 146/148 的人**是实打实的提升；
- **不好的一面**：攻击者的目标会自动转向**那些没有 TPM 的机器**（老旧服务器、IoT、被盗的 VPS、容器），以及**那些绕过了注册阶段的人**。

**所以「用了 DBSC 就安全了」是个错误的推论。** 它的正确表述是：「**目标设备上、且攻击者没能接触到私钥的那部分会话**，重放不再可行。」

## 六、剩下的三个洞

TechRepublic 原文没有回避这一点，我觉得也应该原样列出来：

**① 它不消除 infostealer 本身的威胁。** 攻击者仍然可以偷走密码、API token 和其它敏感凭据。

**② 已经在被入侵的设备上是另一个问题。** 运行在被攻陷设备上的恶意软件仍然是独立的问题。

**③ 最终效果取决于三个变量**：浏览器兼容性、设备支持、以及**服务端有多一致地执行设备绑定的会话续期**。

第三点最容易被忽略 —— 因为如果服务端实现得含糊（比如某些路径没强制走 DBSC 续期），那么保护就是参差不齐的。

文章末尾给出的常规建议仍然适用，而且没有因为 DBSC 而改变：

- 继续强制多因素认证
- 监控可疑的账号活动
- 保持浏览器和设备更新
- 限制对敏感开发环境的访问

**以及 IT 团队该做的一件具体事**：确认自己管理的设备是否支持 DBSC，以及随着 Vercel 逐步放量，这个特性是否真的对用户生效了。

---

## Sources

- Chrome for Developers, *Device Bound Session Credentials (DBSC)*（完整实现规范、回退行为与告警说明）: <https://developer.chrome.com/docs/web-platform/device-bound-session-credentials>
- Google Security Blog, *Protecting Cookies with Device Bound Session Credentials*（2026-04-09，Chrome 146 Windows 公开可用）: <https://blog.google/security/protecting-cookies-with-device-bound-session-credentials/>
- TechRepublic, *Vercel Introduces DBSC: How It Protects Against Cookie Theft*（Joseph Ofonagoro，2026-11-06）: <https://www.techrepublic.com/article/news-vercel-dbsc-session-cookie-theft-protection/>
- W3C WebAppSec, *Device Bound Session Credentials (DBSC) specification*: <https://w3c.github.io/webappsec-dbsc/>
- The Hacker News, *Google Rolls Out DBSC in Chrome 146 to Block Session Theft on Windows*（2026-04-10）: <https://thehackernews.com/2026/04/google-rolls-out-dbsc-in-chrome-146-to.html>

### 事实边界说明

- **DBSC 的完整工作流程、四个交互步骤、密钥存储方式、三种静默回退情况、以及「注册期间恶意软件可能提取私钥」这一告警：均引自 Chrome 官方开发文档**，而非媒体报道。
- Vercel 的宣布时间、浏览器支持范围（Chrome 146 Windows / 148 macOS，仅 Chrome）、逐步放量、TPM 与 Secure Enclave 的硬件要求、以及「剩下的三个洞」：引自 TechRepublic 原文。
- Chrome 146 对 Windows 用户公开可用、macOS 后续跟进：引自 Google 官方博客（2026-04-09）与 Chrome 官方文档。
- Windows 11 要求 TPM 2.0、BitLocker 与 Windows Hello 依赖 TPM：引自 TechRepublic 原文。
- **「如果只保留短时效 cookie 则回退会导致登出；如果两个都保留则静默降级到长时效 cookie」这一推论，是我依据 Chrome 文档中「这个回退只有在你同时实现了长时效和短时效两个 cookie 时才有效」那句做出的**，文档本身没有用「静默降级」这个说法。
- 本文只做防守方视角的分析，不包含任何用于窃取会话或绕过 DBSC 的方法。
