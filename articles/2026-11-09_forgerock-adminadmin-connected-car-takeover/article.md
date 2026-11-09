---
title: "ForgeRock 默认口令 admin:admin：车门和引擎就这样被远程打开"
date: 2026-11-09
slug: forgerock-adminadmin-connected-car-takeover
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Sam Curry 与 Shubham Shah 的原始技术文章《Hacking Two Automakers via ForgeRock Path Confusion, RCE, and Remote Vehicle Access》（2026-11-07）＋ Shubham Shah 的澳大利亚链路文章《unlocking any car from X brand in most of the world》（2026-11-07）＋ The Hacker News 报道（Swati Khandelwal，2026-11-09）＋ Ping Identity 的 OpenIDM / IDM 生产加固指南"
original_date: 2026-11-07
original_url: "https://samcurry.net/forgerock"
description: "本文解读 Sam Curry 与 Shubham Shah 于 2026 年 11 月 7 日公布的研究：两家车企的手机 App 登录体系可被完全接管，进而对联网车辆执行解锁车门、启动引擎等远程指令。**而整条链的起点是一个荒诞到近乎滑稽的东西：ForgeRock OpenIDM 内置的 Apache Felix 管理控制台仍在用文档里的默认口令 admin:admin。** 这不是产品漏洞——**没有 CVE、没有厂商公告**——而是部署配置的失误，且 Ping Identity 自己的生产加固指南多年来一直明确要求「上线前移除该控制台或改掉口令」。全文最值得学的是那条 WAF 绕过：**边界与 Java 后端对同一个 URL 的解析不一致**——研究者用编码斜杠、点段与分号路径参数，让边界把请求判成无害的静态文件，而 servlet 容器把它归一化成 `/system/console`。进控制台后用内置的调度器运行 Groovy 脚本，在存放客户记录的身份服务器上拿到命令执行，改掉目标账号的邮箱和密码，再通过正常 App 登录拿到与真实用户相同的 token。**但比技术链更值得写的是研究者的边界感**：完整链路只在美国账户/车辆上测过、车辆指令只在自己拥有或获得同意的车上执行、测试后把真实邮箱改回去；两篇 write-up 都没有说是否有人在修复前发现或使用过这条路径。**第二条链路（澳大利亚）更说明问题**：那个环境的入口不是默认口令，而是**嵌在 App JavaScript bundle 里的测试用 admin 凭据**，且 MFA 可通过 ROPC 流程整体跳过；研究者还让 GPT-5.6 Sol Ultra 花了约六小时找到了 `/static%2f..%2fopenidm/` 这个未被 WAF 覆盖的路径。**两家车企在报告后约两小时内修复并轮换了凭据。** 本文给出防守方该做的两项检查（查 `/system/console`、不要依赖边界/WAF 的路径规则来藏管理页），并说清一个常被误读的点：品牌名字被隐去、且研究者明确说明不具名是应对方要求。"
published: true
---

> 原文：两位研究者于 2026-11-07 发布的技术文章（英文标题见文末 Sources）
> 原文链接：<https://samcurry.net/forgerock>
> 第二篇：<https://shubs.io/unlocking-any-car-from-x-brand-in-most-of-the-world/>
>
> 本文依据两篇原始技术文章、相关媒体报道与厂商加固指南。

## 一、先把结论摆清楚：这不是「车被黑了」

标题党会写成「黑客远程开走你的车」。**但这两位研究者从一开始就说清楚了：他们破的是 Web 与身份基础设施，不是车本身。**

Shubham Shah 在澳大利亚那篇里写得很直白：

> 提到车黑客，人们很容易跳到硬件那一侧，**但我的背景很明确是在攻陷面向互联网的 Web 应用与基础设施**。不管那些硬件零件是什么，**它们最终都要连回某个按设计就必须能从互联网访问的服务**。

> Regardless of all the hardware bits and bobs, it all connects back to some service that, by design, has to be reachable from the internet.

（**不管那些硬件零件是什么，它们最终都要连回某个按设计就必须能从互联网访问的服务。** 这一句是全文我唯一想原样保留的英文 —— 因为它是整件事的钥匙：联网汽车的所有远程能力，最终都要经过一套「必须公开可达」的身份系统，而这次被打穿的正是那里。）

**而那套身份系统，就是这次被打穿的地方。**

### 影响范围（按原文措辞）

| 项 | 原文 |
|---|---|
| 受影响对象 | 两家车企（**主动不具名**，称 Automaker #1 / #2） |
| 能被做什么 | 为受影响部署上的**任意客户账号**创建有效会话 |
| 有联网车时 | 获得与车主 App 相同的远程能力：位置与遥测、**门锁/解锁、远程启动与停止引擎** |
| 地区 | 两篇合起来覆盖**澳大利亚、美国、加拿大** |
| 完整链路测试范围 | **只在美国账户与车辆上测过** |
| 车辆指令测试范围 | **只在自己拥有或获得明确同意的车上执行** |
| 修复时间 | Automaker #1 **报告后约两小时**修复并轮换了凭据 |
| 品牌名 | 应对方要求隐去 |

**「两小时」这个数字值得单独盯一下** —— 它说明问题不在「厂商不重视」，而在「这个配置从来没被检查过」。一个改口令或删控制台的动作，两小时就能做完。

## 二、正常流程长什么样

两位研究者下载了两家车企的 Android App、反编译、并排追踪认证流程。结论是：**两个 App 看起来是品牌专属入口，背后其实是同一套身份平台。**

- Automaker #1：`login.automaker1.example`，认证树 `MobileAppSignIn`
- Automaker #2：`login.automaker2.example`，认证树 `AppSignIn_v2`
- 两者共用：`consumer-native` realm、`mobileappsdkclient` OAuth 客户端、同一个回调 URI、**服务端驱动的 callback 模型**

正常登录的第一次请求是**一个空的 JSON 对象** —— 不含用户名密码，只是问服务器「第一步要什么」：

```
POST /json/realms/root/realms/consumer-native/authenticate?... HTTP/2
Host: login.automaker1.example
X-Make: A
X-Market: US
{}
```

ForgeRock 回一个 `authId` 加一个 `NameCallback`，App 填好再把整份文档发回去，服务器返回下一个 callback。**整条登录旅程由服务端控制**（账号、设备、验证、OTP 各步）。

**这个「服务端驱动的 callback 模型」后面会变得很重要** —— 因为它意味着登录流程的每一步都由身份服务器定义，而拿到身份服务器的控制权，就等于拿到整个流程。

## 三、链条的第一环：那个 admin:admin

ForgeRock 分两部分：

| 组件 | 作用 |
|---|---|
| **AM**（Access Management） | 跑 callback 旅程、签发登录会话 |
| **IDM / OpenIDM** | **存放 AM 在那段旅程中使用的客户记录** |

而 OpenIDM 的 Java 服务以 **OSGi bundle** 形式跑在 **Apache Felix** 里。Felix 的 Web Console 按惯例位于 `/system/console`，其中：

- `/system/console/bundles` 列出进程里加载的代码；
- `/system/console/configMgr` **编辑运行中的 OSGi 服务配置**。

**关键点**：Ping Identity（ForgeRock 现归属方）自己的生产加固指南**多年来一直建议移除或保护这个控制台**，并明确指出它**独立于 IDM 单独做认证** —— 也就是说它有自己的一套口令，改了主系统口令不影响它。

**而在这些服务器上，控制台还在，而且用的还是文档里的默认值：用户名和密码都是 `admin`。**

### 为什么默认口令这件事比听起来严重

因为它的认证是**独立的**。

一个团队可能认真改了所有 LDAP/AD 口令、配了 MFA、上了 SSO —— **却完全没有意识到这个 Felix 控制台用的是另一套口令，而且从没动过。**

**这正是「配置面」与「认证面」不一致的典型危险**：你以为自己检查了所有入口，其实有一个入口不在你的清单上。

## 四、第二环：边界和后端读的是同一个 URL，但读出了两个东西

控制台**没有直接暴露在公网** —— 边界（WAF/edge）挡住了 `/system/console`、`/openidm/managed/user` 这些路径。直接请求会被拦，重复几次连 IP 都会在这些管理路径上被拒。

**但研究者发现了一件事：边界和 Java 后端对同一个 URL 的解析不一致。**

Sam Curry 的文章里写得很清楚：

> Shubham 变换 URL 编码、HTTP 方法和路径分隔符，得到了不同的响应 —— 这说明**边界是在 Java 应用完成解释之前就匹配了危险路径模式**。
>
> 站点正常 `/static` 前缀下的请求仍能到达后端，于是 Shubham 开始把这个前缀与**编码斜杠、点段、分号路径参数**组合起来。我们要的是：**边界继续看到一个静态请求，而 Java 后端把它归一化成某个被拦的路由**。
>
> 结果表明三层在读同一个 URL 的不同形式：**边界**决定要不要放行传入路径，**servlet 容器**解码出另一种形式来选择 OSGi servlet，而**被选中的应用还能再解析一次**。

**「三层读同一个 URL 的三种形式」** —— 这是整篇文章技术含量最高的一句话。

这不是某个产品的 bug，而是**多层架构的固有缝隙**：只要「谁来判断危险」和「谁来执行请求」不是同一层，且两层对路径的归一化规则不同，就存在这类错位。

而 The Hacker News 的概括更简洁：

> 通过加入编码斜杠和额外字符，研究者让边界把请求当成无害的静态文件，而服务器把它当成通往控制台的路径；**剩下的工作由默认口令完成**。

### 澳大利亚那条链路上，这个绕过被验证得更细

Shubham 在澳洲环境里试过 `/XUI/..%2fopenidm/endpoint`，能拿到 admin JWT，但 **OpenIDM 的路由机制不认带 traversal 的路径**（「没有 servlet 或资源注册在含路径穿越的路径上」），所以请求报错。

**他们被这个「甚至可能不是安全设计」的路由怪癖卡了几天。**

最后找到 `/static%2f..%2fopenidm/` 没被 WAF 覆盖，且不会引发 servlet 混淆。而这里有个很值得记的细节：

> 我们抓了最接近被测版本的 OpenIDM 源码，**让 GPT-5.6 Sol Ultra 在这上面花了大约六小时**。
>
> 它成功了。虽然 Sam 和我都花时间手动尝试绕过这个限制，但**我们没有试过每一种组合**。
>
> 我们试 `/XUI%2f..%2fopenidm/` 时得到硬 403，作为人，我们**假设这个结论适用于所有前缀**。而 GPT-5.6 发现的是 `/static%2f..%2fopenidm/` 根本不在 WAF 覆盖范围内。

**「作为人，我们假设这个结论适用于所有前缀」** —— 这句话是 AI 辅助安全研究里少见的、诚实的自我复盘。

它说明 AI 在这里的价值不是「更聪明」，而是**不知疲倦地枚举组合** —— 人类会从一个 403 归纳出一条通用规则，而模型会继续试下一个前缀。

**这和本号上周写的 OpenAI 那篇（17,600 次认证测试找出 SSHole）是同一个道理**：这类工作的瓶颈是「组合空间太大，人不愿意试完」，而不是「人不懂得怎么试」。

## 五、第三环：从控制台到命令执行

进入 `/system/console/configMgr` 之后，链条就变得直接了：

> OpenIDM 的**调度器可以调用内联脚本**，而它的**脚本服务支持 Groovy**。
>
> 如果 ConfigMgr 暴露了 OpenIDM 的 schedule factory，一个控制台配置就能在身份进程里运行 Groovy。

**于是：改 OSGi 服务配置 → 注册一个调度任务 → 调度器执行 Groovy → 在存放客户记录的服务器上拿到命令执行。**

The Hacker News 的描述是：

> 在控制台里，研究者用内置的调度器运行小脚本，在身份服务器上执行自己的代码。这给了他们**一台存放两家品牌登录客户记录的机器上的命令提示符**。

**注意这一步的性质**：它不是缓冲区溢出，不是反序列化漏洞 —— **它是一个本就该存在的功能（调度器 + 脚本）被一个本不该能进来的人使用了**。

这类攻击链最难防，因为每一环单独看都是「正常功能」：

| 环节 | 单独看 | 问题 |
|---|---|---|
| Felix 控制台 | 运维工具 | 默认口令没改 |
| 边界路径规则 | 正常防护 | 与后端解析不一致 |
| ConfigMgr | 正常配置界面 | 不该对公网可达 |
| 调度器 | 正常自动化功能 | 不该被外部触发 |
| Groovy 脚本 | 正常扩展机制 | 被用来起 shell |

**没有一环是漏洞 —— 合起来是完整接管。** 这也是为什么这次**没有 CVE**：The Hacker News 写得很清楚，「两家车企的失误在于怎么运行 ForgeRock，不是产品里的新 bug，所以没有 CVE，也没有厂商公告可追」。

## 六、第四环：改邮箱和密码，拿到和真实用户一样的 token

拿到服务器上的命令执行之后：

> 客户记录就在控制台同一道拦截后面，但研究者的代码**从服务器内部**够到了它们。
>
> 他们改掉目标账号的**邮箱地址和密码**，通过正常 App 以该客户身份登录，并拿到了**与真实 App 使用的相同的访问令牌**。

**「相同的访问令牌」是这句里最重要的部分** —— 因为他们没有伪造 token，也没有绕过车控 API 的鉴权，而是**走完了完全正常的登录流程**。

从车控服务那边看，这就是一次合法的用户会话。

**而这也是为什么「车主几乎察觉不到」：**

> 改邮箱和密码**不会把车主从 App 里登出去**，而研究者可以把账号的告警**导向自己的手机**，让它们不出现在车主手机上。
>
> 测试后他们把真实邮箱改了回去。

**两篇 write-up 都没有说是否有别人在被修复之前发现或用过这条路径。**

Shubham 在澳洲那篇的链条总结更完整（也更吓人）：

```
车牌 → VIN → Subscriber GUID → JS bundle 里的 OpenIDM admin 凭据
→ 路径穿越绕过 WAF → 经 ROPC 流程跳过 MFA
→ 铸造消费者 App token → 远程指令 API
```

**「车牌 → VIN」这一步值得单独说**：在澳大利亚，通过各州的注册查询站点，从车牌拿到 VIN「相当容易」，而 Shubham 明确写了：

> **这本身不算安全缺陷。** 想拿 VIN 有很多正当理由，比如买二手车前查真实的维修与保险记录。

**从「公开可得的车牌」到「任意车辆的远程指令」** —— 中间靠的全是身份系统这一侧的配置失误。

## 七、澳大利亚那条链路：入口完全不同，结论一模一样

**这一条最容易被媒体漏掉，但它其实是全篇最有普遍意义的观察。**

澳洲环境的入口**不是**默认口令，而是：

> 一个 `admintool.redacted-telematics.com.au` 子域，页面标题就叫 TEST HARNESS。
>
> 大部分单页应用即使只需要渲染一个登录页，也会把**整份 JavaScript bundle** 发出去 —— 于是他们可以翻这个 bundle，弄清这个「admin tool」到底能做什么。
>
> 结果：它有丰富的 API，能让车企员工**几乎不受限制地与客户账号和生产车辆交互**，而且不少 API **除了硬编码在 JS bundle 里的 API key 之外不需要任何认证**。

更要命的是：

> 翻 `*.redacted-telematics.com.au` 下的 JS 文件时，我们撞见了一份**极其糟糕的厂商 JS bundle，里面嵌着 OpenIDM 的 admin 凭据** 😱
>
> 尽管这些凭据**本来是给 staging 环境用的**，但以我们目前看到的卫生状况，我们相当确定它们在生产环境也能用。

**「本来是给 staging 用的」** —— 这句话值得所有做配置管理的人抄下来。

而澳洲环境还有一个独立的失误：**MFA 可以被整体跳过**，通过 Resource Owner Password Credentials（ROPC）grant 换取 id_token，再经两步交换拿到移动 App 的 access token。

**所以两条链路的起点不同（默认口令 vs 硬编码凭据），路径不同（Groovy RCE vs PATCH 密码 + 跳过 MFA），但终点相同：铸造一个合法的消费者 App token，然后对车辆发指令。**

**这说明问题不在「某一个默认口令」，而在「身份系统被放在公网、且没有按加固指南收口」这一类部署实践。**

## 八、防守方该做什么

The Hacker News 给的两条检查，我认为值得原样保留：

**① 查 `/system/console`。**

> 找 Apache Felix 控制台（在 `/system/console`），**移除它，或改掉默认口令**。
>
> 控制台和它的默认口令**已经被文档记录多年**，而厂商的**生产加固指南**早就告诉运维：上线前移除控制台或改口令。

**② 不要指望边界或 WAF 的路径规则能藏住管理页。**

> 一条边界与服务器读法不同的路径，可以溜过规则 —— 就像这次发生的那样。

### 我认为还应该加三条（基于两篇原文）

**③ 审计「独立认证面」。** Felix 控制台的口令是**独立于 IDM 的** —— 这类「不在主认证清单上」的入口（管理控制台、调试端点、staging 工具）才是这类事故的高发区。**改主系统口令不会覆盖它们。**

**④ 审计前端 bundle 里的凭据。** 澳洲那条链的入口是**嵌在 JS 里的 staging admin 凭据**。任何会发到浏览器的东西，都要按「已经公开」来对待。

**⑤ 检查 ROPC 与 MFA 的实际可达性。** 澳洲环境能整体跳过 MFA，不是因为 MFA 算法被破，而是因为**有一条 grant 路径绕过了它**。这类「正常登录走 MFA，但另一条 OAuth grant 不走」的缝隙，在复杂身份部署里并不罕见。

## 九、几件必须说清的事

**① 品牌名被隐去，是研究者主动的选择。**

Sam Curry 在原文里专门加了一条注释解释：

> 显然，**他们要求不被具名**；虽然通常我们会争取把公司名字写进去，但现在是安全领域的忙季，**我不希望他们因为担心这次披露而分流资源**。

**这个分寸值得记** —— 它和「负责任披露」是同一件事的两面：既把技术说清楚，又不制造不必要的舆论压力。

**② 没有利用代码被公开。** 两篇 write-up 都给出了**脱敏后的请求样例**（域名、token、VIN、凭据全部 REDACTED），并把品牌和端点隐去。本文同样只做机制解读，不提供任何可复用的请求构造。

**③ 两篇都没说「是否有人先于我们发现」。** 原文明确写：「两篇 write-up 都没有说明是否有人在修复前发现或使用了这条路径。」**这不是疏漏，是一个不该被推测填上的空白。**

**④ 修复很快，但那恰恰是问题所在。** Automaker #1 在报告后约两小时修复并轮换凭据 —— 说明这是个**改配置就能解决**的问题。**一个两小时能修好的东西，在生产环境里存在了多久？这个问题原文没有回答，也不该由我们替它回答。**

**⑤ 这类工作的背景。** 两位研究者此前已在 Honda、Acura、Nissan、Infiniti、Hyundai、Genesis、Ford、Porsche、Kia、Subaru 上展示过远程车辆访问，2023 年还有一项覆盖 16 个品牌的行业研究。**他们破的一直是 Web 与身份系统，不是车载硬件。** 这条脉络本身说明：联网汽车的安全瓶颈，很大程度上仍在传统的 Web/身份基础设施上。

---

## Sources

- Sam Curry & Shubham Shah, *Hacking Two Automakers via ForgeRock Path Confusion, RCE, and Remote Vehicle Access*（2026-11-07）: <https://samcurry.net/forgerock>
- Shubham Shah, *unlocking any car from X brand in most of the world*（2026-11-07，澳大利亚链路）: <https://shubs.io/unlocking-any-car-from-x-brand-in-most-of-the-world/>
- The Hacker News, *Default 'admin:admin' Server Password Helps Researchers Hack Two Automakers, Unlock and Start Cars*（Swati Khandelwal，2026-11-09）: <https://thehackernews.com/2026/11/default-adminadmin-server-password.html>
- Ping Identity, *IDM production hardening guide — remove development tools*: <https://docs.pingidentity.com/pingidm/7.2/security-guide/security-remove-dev-tools.html>

### 事实边界说明

- 两条攻击链的技术细节、受影响能力、测试范围、修复时间、品牌不具名的原因、以及「两篇 write-up 都没有说明是否有人先于我们发现」：均引自两篇原始技术文章。
- 「没有 CVE、没有厂商公告」「控制台与默认口令已被文档记录多年」「生产加固指南要求上线前移除或改口令」「防守方两条检查」：引自 The Hacker News 报道与 Ping Identity 加固指南。
- **本文补充的三条检查（审计独立认证面、审计前端 bundle 凭据、检查 ROPC/MFA 实际可达性）是基于两篇原文事实的推断**，原文未这样归纳。
- **本文不包含任何可直接复用的请求构造、凭据或端点**；所有请求样例均按原文的脱敏形式引用。
- 品牌名按研究者与报道的处理保持不具名；本文未做任何归因推测。
- 本文只做防守方视角的解读。
