---
title: "钓鱼防御打错了层级：域名封不过来，但服务器藏不住"
date: 2026-10-09
slug: phishing-server-layer-aitm
tags: [钓鱼, AiTM, 会话劫持, MFA, Microsoft 365, 威胁狩猎, 域名劫持, CAA, 证书透明度, Chrome, 译文]
category: 安全
author: FreeLAMP.com
original_source: "CSO Online / Google Security Blog"
original_author: "Yanky Wilson（CSO Online）；Chrome Secure Web and Networking Team（Google）"
original_date: 2026-10-08
original_url: "https://www.csoonline.com/article/4231923/we-are-fighting-phishing-at-the-wrong-layer.html"
description: "两篇相隔两天的文章讲透了同一件事：防御方花最多精力的域名层，恰恰是攻击者成本最低、也最容易被别人掀翻的层。CSO Online 一线分析师演示了 AiTM 钓鱼套件如何把 Microsoft 观察到的源站 IP 写进 cookie 送给受害者，从而顺藤摸出整个攻击资产；Google 则披露 .gh/.sl/.as 三个 ccTLD 注册局被劫持，浏览器只能事后封证书。本文把两件事合起来读，给出直接可执行的检测与应急清单。"
published: true
---

> 原文一：[We are fighting phishing at the wrong layer](https://www.csoonline.com/article/4231923/we-are-fighting-phishing-at-the-wrong-layer.html)（CSO Online，2026-10-08，作者 Yanky Wilson）
> 原文二：[Chrome's Response to Recent ccTLD Registry Hijacks](https://blog.google/security/chromes-response-to-recent-cctld-registry-hijacks/)（Google Security Blog，2026-10-06，Chrome Secure Web and Networking Team）
> 本文为**两文合读 + 解读**，技术细节以作者公开的 [GitHub 仓库](https://github.com/yankywilson/m365-bec-estate-2026)为准。

## 一句话结论

防御方花最多精力的**域名层**，恰恰是攻击者成本最低的层：一个域名 1 美元，24 分钟就能完成注册到上线收割页的全流程，被封了随时换新的。真正有成本、有留存、藏不住的是**服务器层**。CSO Online 的作者用一个非常朴素的漏洞（AiTM 代理把上游服务的 cookie 原样透传给受害者，cookie 里写着代理自己的 IP）端掉了一整个经营六个月的钓鱼资产。而 Google 那篇从另一个角度证明了同一件事：连域名层的地基（ccTLD 注册局）都会被人整块掀走，浏览器只能事后擦屁股。

## 一、24 分钟：域名层的攻防根本不在一个成本量级

作者 Yanky Wilson 计时过一个攻击者的操作：**从注册域名，到完成解析、签发证书、上线一个活的凭证收割页，全程不到 24 分钟，其中 12 分钟在等 nameserver 生效**。

然后是我们熟悉的那套防御：把域名喂给邮件网关、DNS 过滤器、威胁情报平台，统计封了多少条，写进给管理层的报告。数字很好看。问题是，**被封的那个东西，攻击者花 1 美元、20 分钟就能换一个**。

作者的说法很直白：

> 域名是攻击者拥有的最便宜的东西，也是大多数防御项目唯一看得见的东西。

攻防双方在这个层级的成本根本不对称。防御的每一次封禁都是一次性的、逐域的；攻击的每一次更换是批量的、廉价的。**在一个对方成本趋近于零的层级上打消耗战，赢不了。**

### 现代钓鱼套件已经不是假登录页

现在主流的钓鱼套件是 **AiTM（adversary-in-the-middle，中间人）代理**。它不再伪造登录页，而是把受害者的流量**实时中转**到真实的 Microsoft 登录服务：受害者看到的是真页面，完成的是真的 MFA 提示，代理在流量经过时把凭证和会话 token 一起截走。攻击者拿到的是一个**活着的已登录会话**，而不是一个密码。

微软在 2022 年记录过单次此类战役波及 [超过 10,000 个组织](https://www.microsoft.com/en-us/security/blog/2022/07/12/from-cookie-theft-to-bec-attackers-use-aitm-phishing-sites-as-entry-point-to-further-financial-fraud/)，此后这套模式只变得更加商品化。

独立分析也证实了多数人不愿接受的那个事实：通过这类套件被攻破的账号里，**绝大多数本来就开着 MFA**（[Obsidian Security 的分析](https://www.obsidiansecurity.com/blog/aitm-phishing-attacks-bypass-mfa)）。MFA 挡的是密码重放，挡不住实时中转。

### 服务器为什么藏不住又舍不得换

把 AiTM 代理藏到 CDN 后面，服务器确实会「消失」。作者上个月就碰到了：证书透明度日志里只有 CDN 的证书；被动 DNS 显示域名从未解析到别处；全网扫描平台返回空结果。

这里有一个值得单独强调的认知纠偏：

> 对着主机名门禁的服务器扫出空结果，不等于那里没有服务器。只说明你敲门的语言不对。把这两件事划等号，是一次狩猎过早收场的标准方式。

那台源站在半秒内丢弃所有不带预期主机名的连接，一个字节都不回。扫描平台没扫到，不是因为没有东西，而是因为对方拒绝回答。

但服务器和域名有两个本质区别：**服务器要花钱、要花时间配置**，重建很麻烦，所以会跨战役复用；**服务器是共享的**，一台机器上往往挂着整个运营的其他部分。找到服务器，你得到的不是一个 IOC，而是整个攻击资产。

## 二、破局：代理把自己的回信地址写在了信封上

作者试了十条路，全部碰壁。最后起作用的是一个 cookie。

机制简单到有点好笑：

1. AiTM 代理替受害者向 Microsoft 发起登录，于是 **Microsoft 看到的客户端是代理**，不是受害者；
2. Microsoft（和很多服务一样）会 set 一个 cookie，**记录它观察到的这个客户端的来源 IP**，也就是代理服务器的 IP;
3. 代理把响应原样中转回受害者的浏览器，cookie 原封不动带着。没有人去改写响应头，因为没人配置过这件事。

结果就是：**受害者的浏览器里躺着一个 cookie，里面写着攻击者中转服务器的 IP 地址。代理在信封上写好了自己的回信地址，然后亲手交给了它正在抢劫的人。**

作者是在过滤解密流量抓包中、按「钓鱼站点 set 过的 cookie」筛查时发现的：这个值既不是 Microsoft 的地址，也不是自己沙箱的地址，而是来自一家收加密货币的小型主机转售商。

### 方法论：一条线索不是结论

作者的处置方式比发现本身更值得学。他没有把第一条线索当结论，而是**花了一个小时试图推翻自己的发现**：

- 最有力的竞争解释是这个 cookie 抓到的是自己 detonation 环境的出口 IP。他查了那个地址：一家低价 VPS 转售商，没有任何商业沙箱会从那里出网。这削弱了替代解释，但没有关闭它；
- 真正闭环的是**来自第一个观察无法影响的另一条独立线索**，两边对上了。这时他才允许自己写下「origin」这个词；
- 如果独立线索对不上，这条记录就只作为「未验证」留在笔记里，照样发出来。

> 未证实的结果也是结果。下一个分析师从一句明确的「我不确定」里得到的东西，比从一个自信的猜测里多得多。

这也是威胁情报项目能不能长期拿到预算的分水岭：发出去的东西被证伪一次，信用的损失要用十次正确的判断来补。

## 三、一封举报邮件，撬出一个六个月的攻击资产

顺着那个服务器 IP，作者完成了教科书式的 pivot：

| 步骤 | 发现 |
|---|---|
| 服务器 IP | 一台低成本 VPS，主机名门禁 |
| 被动 DNS 反查 | 第二个域名，已静默指向该服务器数月、从未对外服务 |
| 注册商查询 | 一个该运营者没有在别处用过的注册商账号 |
| 解析剩余域名 | 十几个仿冒域名收敛到**少数几台机器** |
| 关键交叉 | 其中两台机器同时挂着**分属不同云身份租户**的域名 |

最后一条是整个案子的突破口。那几个租户表面上毫无关联，枚举任何一个都发现不了其他几个。运营者在身份层面做了认真的隔离，却在托管上省了钱，**共享的基础设施暴露了被隔离的身份刻意隐藏的东西**。

一封举报钓鱼邮件，最终变成一张完整的资产地图：数十个仿冒真实制造商、猎头公司和垃圾清运商的域名，花了六个月耐心搭建，目的是对它们的客户发起**发票欺诈（BEC）**。

这一切从域名层看不见，从服务器层一览无余。

## 四、同一件事反转过来：查你自己的租户日志

这篇文章对安全运营者最有价值的部分不是研究技巧，而是那个反转，而且**它不依赖攻击者犯错**：

> 如果代理是 Microsoft 看到的客户端，那代理就是你的日志里记录的登录者。你的员工被 AiTM 套件钓到的那一刻，租户里那条「成功登录」记录携带的是代理的地址，不是你员工的地址。

在一次其他所有控制都显示绿灯的攻击里，这是极少数可靠的检测信号之一。怎么用：

- **查托管商和 VPS 网段**。你的员工没有业务理由从这些网络登录，而这些正是中转服务器所在的地方。把已知云服务商和住宅 ASN 之外、明显属于低价托管的 IP 段列出来，对着成功登录事件做狩猎；
- **别只查交互式登录**。这类套件会替你点掉「保持登录」，token 是持久的，攻击者后续的活动以 **refresh token 事件**而不是新的交互式登录呈现。**只查交互式登录的狩猎，能找到沦陷的那一刻，然后错过之后的一切**。作者见过这样的案例；
- **响应顺序不可协商**。攻击者手里是会话，不是密码。**先吊销所有会话，再重置凭证**。顺序反了，入侵者拿着还有效的会话继续干活，而所有人都以为事件已经关闭。

作者把完整的技术拆解、IOC 和检测规则放在了公开仓库 [m365-bec-estate-2026](https://github.com/yankywilson/m365-bec-estate-2026)，欢迎其他人复现验证。

## 五、Google 那篇：域名层的地基也会被人整块掀走

几乎同一时间，Google 披露了另一起事件，恰好从另一个方向证明了「域名层不可靠」：

**.gh（加纳）、.sl（塞拉利昂）、.as（美属萨摩亚）三个 ccTLD 的注册局被第三方劫持**。攻击者不是抢某个域名，而是篡改了权威 DNS 记录，给包括 Google 域名在内的多个组织签发了未授权的 HTTPS 证书。Google 明确说这批 CA 本身没有做错什么：域名控制权验证在 DNS 被劫持的状态下「正常」通过了。

Chrome 的应急动作：

- 用 [CRLSets](https://www.chromium.org/Home/chromium-security/crlsets/) 第一时间在浏览器内封掉未授权证书，用户无需任何操作；
- 联动签发 CA 吊销证书，覆盖非 Chrome 用户；
- 用证书透明度（CT）日志反查，主动发现并封锁了**其他被同一波攻击影响的组织**，包括若干全球性品牌，并逐个通知。

Google 同时把话说得很诚实：

> 浏览器侧的干预不能被当作可以依赖的防线。DNS 劫持情况复杂，我们无法保证识别出了每一个受影响的域名，Chrome 的干预也保护不了非 Chrome 用户。

### 给域名持有者的两条硬要求

1. **对全部域名持续监控 CT 日志**。凡是 Chrome 默认信任的证书都必须进公开 CT 日志，所以监控 CT 等于对「有人给你的域名签证书」设置了近实时告警。重点：**监控范围要覆盖整个域名组合，包括停放的域名和区域性的 ccTLD 域名**。如果你在 .gh/.sl/.as 下有域名，立刻去查近期的 CT 记录；
2. **发布严格的 CAA 记录（带 ACME 账号绑定）**。CAA（RFC 8659）声明哪些 CA 有权给你的域名签证书。Google 特别点破了一个时间差：**CAA 拦不住正在进行的 DNS 劫持**（攻击者控制 DNS 时可以正常通过验证），但它是**劫持结束后的关键保险**。因为 CA 允许缓存并复用已通过的域名控制验证（DCV），如果不加限制，攻击者可以利用劫持期间缓存的验证状态在事后继续签发新证书。用 [RFC 8657](https://www.rfc-editor.org/info/rfc8657/) 的 accounturi 和 validationmethods 把签发权限收紧到特定 ACME 账号和验证方式，才能堵死这条路。

Google 给出的长期方向是缩短证书有效期和 DCV 复用期（CA/Browser Forum 的 [SC-081v3 投票](https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/)），以及抗量子的 Chrome Root Program。方向对，但对今天的防御者来说，CT 监控和 CAA 是当下就能做的。

## 六、两件事放在一起读

| | 域名层 | 服务器层 |
|---|---|---|
| 攻击者成本 | 约 1 美元，24 分钟上线，可无限更换 | 真金白银，重建麻烦，倾向复用 |
| 防御可见性 | 大家都在这里封禁，指标好看 | 几乎没人系统性地狩猎 |
| 被动一处 | 一个域名只值一个 IOC | 一台服务器带出整个资产 |
| 地基风险 | ccTLD 注册局可被整块劫持（.gh/.sl/.as） | 相对稳固，需 CDN + 主机名门禁才藏得住 |

两篇文章指向同一个结论：**在对方成本最低的层级打消耗战，同时在最贵、藏得最深的层级视而不见，是当前钓鱼防御的结构性错配。** 对个人运营者，落地动作就是三件：CT 日志监控铺满全部域名、发布带 ACME 绑定的严格 CAA、在租户登录日志里对着托管网段和 refresh token 事件做一次狩猎。

## 延伸阅读

- [AiTM 钓鱼与 MFA 绕过：Obsidian Security 的分析](https://www.obsidiansecurity.com/blog/aitm-phishing-attacks-bypass-mfa)
- [微软 2022 年 AiTM 战役技术报告](https://www.microsoft.com/en-us/security/blog/2022/07/12/from-cookie-theft-to-bec-attackers-use-aitm-phishing-sites-as-entry-point-to-further-financial-fraud/)
- [作者公开的完整 IOC 与检测规则仓库](https://github.com/yankywilson/m365-bec-estate-2026)
- [RFC 8659：Certification Authority Authorization](https://datatracker.ietf.org/doc/html/rfc8659)
- [本站：被遗忘的 DNS 记录，正在给骗局开路：Hazy Hawk 子域名劫持全拆解](/articles/2026-08-04_hazy-hawk-dns-subdomain-hijack/)
- [本站：Chrome 都两周一个大版本了，信创浏览器还停在 120](/articles/2026-09-29_xinchuang-browser-kernel-lag/)
