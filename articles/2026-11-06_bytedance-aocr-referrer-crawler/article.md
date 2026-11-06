---
title: "ByteDance 爬虫的假 Referer：aocr.org 引用的三层证据链"
date: 2026-11-06
slug: bytedance-aocr-referrer-crawler
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Tin Analytics《Getting traffic from aocr.org? That's ByteDance crawling your website》（Ege Demir，2026-10-29）全文，含其原始请求头、指纹对照组与网络归属数据；＋ 我用 APNIC RDAP 核对 AS132510 注册信息 ＋ 我在 ByteDance 开源的 lynx-family/lynx 仓库 develop 分支中定位到「forest」注释的原始代码 ＋ Oxylabs 官方文档核对端口 60000 ＋ Cloudflare 关于 AI 爬虫与未申报爬虫的公开报告"
original_date: 2026-10-29
original_url: "https://tin.computer/blog/aocr-org-referrer-bot"
description: "本文解读 Tin Analytics 于 2026 年 10 月 29 日发布的《Getting traffic from aocr.org? That's ByteDance crawling your website》：一个伪装成 Windows Chrome 146、用美国代理池轮换 IP、并伪造 www.aocr.org 作为来源引用的爬虫，如何被三层证据链钉在 ByteDance 的爬虫栈上。第一层是网络指纹：Tin 用 ClientHello 长度、HTTP/2 priority 权重、Accept 头三个特征同时比对，aocr.org 爬虫 199/199 请求全部命中，官方声明的 Bytespider 与 TikTokSpider 命中 57%，而其他所有流量只有 0.08%。第二层是浏览器内部字段：爬虫的会话录像里带 extensionTiming.forestResFrom、forestResLoadStart 与 htmlPredictorHit —— 我在 ByteDance 自己开源的 Lynx 仓库 develop 分支里找到了那行注释，确认「forest」确实是他们的资源加载器名。第三层是真实服务器位置：作者用一段只对该指纹生效的 WebRTC 探测代码，拿到 14 个 IPv6 地址（同一个 /64）与 2 个 IPv4，全部落在 AS132510 —— 我用 APNIC RDAP 核对确认该 AS 名称为 ShanXiMCC-IDC，注册实体是 China Mobile Communications Corporation，山西移动机房网络。作者还纠正了一个常见误读：可见的那 186 个美国地址是租来的代理池（184 次访问用了 186 个不同地址，端口只有 1180/40000/60000 开放，而 60000 正是 Oxylabs 文档里的专用数据中心代理端口），真实机器在中国。本文还记录了作者明确的边界：证明了「用了 ByteDance 的爬虫栈、服务器在中国」，但没证明「谁在运营」——可能是 ByteDance 团队，也可能是使用同一套浏览器技术的客户（原文举例火山引擎）。作者已于 10 月 29 日向 ByteDance 发出证据与三个问题，原文承诺会补充答复。"
published: true
---

> 原文：Tin Analytics《Getting traffic from aocr.org? That's ByteDance crawling your website》（2026-10-29，作者 Ege Demir）
> 原文链接：<https://tin.computer/blog/aocr-org-referrer-bot>
>
> 本文依据 Tin Analytics 原文全文（含其原始请求头与指纹对照组）、我用 APNIC RDAP 核对的 AS 注册信息、我在 ByteDance 开源 Lynx 仓库中定位到的原始代码注释、以及 Oxylabs 官方文档。

## 一、先说结论：三层证据链，但第三层是「未证明」

这是 Tin Analytics 的一篇技术调查报告，讲的是从 2026 年 9 月下旬开始，不少网站在分析工具里看到来自 `www.aocr.org` 的访问。

**aocr.org 是美国骨科放射学会（American Osteopathic College of Radiology）的官网，它跟这些流量没有任何关系。** 作者明确说：不要去联系 AOCR，他们不是流量来源。

原文把结论分成了「已确认」和「未证明」两栏，这个分栏本身就是全文最值得学的地方。而它对第一层的表述是：

> the crawler has the same network fingerprint as Bytespider, ByteDance's declared crawler. Only 0.08% of other traffic has it.

（这一句是全文我唯一想原样保留的英文 —— 因为它同时给出了「像谁」和「有多独特」两个关键信息，而后者才是让「像」这个结论站得住的东西。）

| | 结论 |
|---|---|
| 已确认 | 爬虫与 ByteDance 声明的爬虫有**相同的网络指纹**，其他流量中只有 0.08% 命中 |
| 已确认 | 它的浏览器上报带有 ByteDance 资源加载器名字的内部计时字段，原版 Chrome 没有这些字段 |
| 已确认 | 它的**真实服务器**在山西省一个中国移动机房网络里，是装中文字体的 Linux 服务器，却对外声称自己是 Windows |
| **未证明** | **谁在运营它**。可能是 ByteDance 的团队，也可能是使用 ByteDance 技术的客户 |

所以严格说，这篇文章证明的是「**这个爬虫用了 ByteDance 的爬虫栈、服务器在中国**」，而不是「**ByteDance 在爬你的网站**」。这两句话的差别，在归因上很要紧 —— 原文举的例子是火山引擎这类使用同一套浏览器技术的客户。

而这三条证据链，本身就是这篇报告最值得学的地方。让我逐条拆开。

## 二、第一层证据：三个特征同时命中，而不是只看 User-Agent

绝大多数「某某爬虫是谁」的文章靠 User-Agent 字符串判断 —— 这基本没有价值，因为 UA 随便写。

Tin 的做法是**三个网络层特征同时比对**，数据取自 2026 年 9 月 20 日到 10 月 29 日：

| 特征 | aocr.org 爬虫 | 官方声明的 Bytespider / TikTokSpider | 其他所有流量 |
|---|---|---|---|
| 三项全中 | **199 / 199（100%）** | 646 / 1,142（57%） | 115 / 137,964（**0.08%**） |

三个特征具体是：

1. **TLS ClientHello 长度**：1722、1754、1786 或 1818 字节；
2. **HTTP/2 priority**：weight 256、exclusive；
3. **Accept 头**里含 `image/heif,image/avif`。

**0.08% 这个数字是整份报告最有说服力的一行。** 它说明这个指纹在真实互联网流量里几乎不存在 —— 所以它不是「某种常见的爬虫风格」，而是「某个特定实现的独有特征」。

而且作者给了一组很干净的对照：**真实的 Chrome 146 到 157 全都不一样** —— 它们会发 client hints（`Sec-CH-UA`），HTTP/2 priority weight 是 16，ClientHello 长度是 1714/1746/1778/1810（每个都少 8 字节），Accept 头里**没有** `image/heif`。

而这个爬虫的 UA 声称自己是：

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
```

**它声称自己是 Chrome 146，但它的网络栈和真 Chrome 146 逐项对不上。** 屏幕尺寸报 800 × 600、时区报 Asia/Shanghai、client hints 一个不发 —— 一套精心伪装成「一台普通 Windows 电脑」的参数。

还有一处细节值得注意：官方声明的 Bytespider 和这个爬虫**只有一个差别** —— Accept-Language 的值不同。原文特意说明「那是一个设置，不是栈的一部分」。这句话的方法论价值很高：**你要证明两个东西同源，就得找出它们唯一不同的地方，并说明那个不同为什么无关。**

## 三、第二层证据：浏览器内部字段泄露了「forest」这个名字

这是我认为整份报告里最漂亮的一层证据。

作者用 Tin Analytics 的会话录像功能回放爬虫的页面计时数据，发现每个爬虫条目里都有**原版 Chrome 不存在的字段**：

- `extensionTiming` 里带 `forestResFrom` 和 `forestResLoadStart`；
- 以及 `htmlPredictorHit`。

作者检查了 37 份真实访客的录像 —— Chrome、Edge、Safari、Firefox、微信、以及其它中国浏览器 —— **没有一个有这些字段**。而每一个爬虫条目都有。

**「forest」是什么？**

作者指出：ByteDance 开源的 Lynx 代码里提到过一个「类似 forest 的定制资源加载器」，所以这个爬虫很可能用的是 ByteDance 的 Chromium 定制版。作者还补了一句：他们没有找到任何使用这些字段名的公开代码。

### 我去核对了这一条

我在 ByteDance 开源的 `lynx-family/lynx` 仓库（`develop` 分支）里找到了那行注释，位置在 `platform/darwin/common/lynx/public/base/LynxResourceFetcher.h`：

```objc
/*!
 Resolve resource origin url to url for different environment
 @param url: string for current source url
 @param completionBlock: the block to provide resolved resource url and customized resource loader
 like forest
 */
- (void)resolveResourceURL:(NSString *)url completion:(LynxResourceResolveHandler)completionBlock;
```

注释里那句 `like forest` 确实存在。

而且不止这一处 —— 同一仓库里还有两处提到 forest：

```
platform/darwin/common/lynx/base/LynxResourceServiceFetcher.mm:42:
  // Network requests should not be made on the main thread, so async method of forest are always ...

platform/darwin/common/lynx/public/resource/LynxResourceRequest.h:52:
  // Only for LynxResourceFetcher use. Return the full request parameters for forest.
```

**所以「forest 是 ByteDance 内部资源加载器的名字」这个论断是有源码依据的，而不是推测。** 原文作者说「ByteDance 的开源 Lynx 代码提到过一个类似 forest 的定制资源加载器」，这个表述准确。

**这一层的价值在于：它是不可伪造的。** UA 可以随便写，但 `extensionTiming` 里的内部字段名是构建这个 Chromium 分支的人自己起的 —— 除非你真的用了 ByteDance 那套构建，否则你的浏览器不会吐出 `forestResFrom` 这个字段名。这和「UA 写了 Chrome 146」是完全不同性质的东西。

## 四、第三层证据：用 WebRTC 绕过代理，拿到真实地址

这一层是整份报告里技术手法最高明的一段。

问题的难点在于：你看到的源 IP 是**代理**，不是真实服务器。常规办法拿不到真身。

作者的做法是：在 clawmessenger.com 上加一段**只对这个爬虫指纹生效**的检查代码，通过 WebRTC 询问浏览器的网络地址 —— 因为 **WebRTC 流量不总是走代理**。

结果（前 7 次爬虫访问）：

- 14 个 IPv6 地址，全在**同一个 /64** 网络里；
- 2 个 IPv4 地址；
- 全部落在 **AS132510**。

### 我核对了这个 AS

用 APNIC RDAP 查 AS132510：

```
name:     ShanXiMCC-IDC
handle:   AS132510
registrant: China Mobile Communications Corporation
```

**注册实体是 China Mobile Communications Corporation（移动通信集团），名称直接写着「山西 IDC」。** 这与原文说的「山西省一个中国移动机房网络」完全一致。

而服务器本身的特征也自洽：Linux x86_64、4 核、32 GB 内存、装了中文字体（Noto Sans CJK SC 和文泉驿），**但对外声称自己是 Windows 电脑 + Mac 显卡**。

原文还提到一个旁证：一个社区路由列表把该 /64 旁边的地址标注为 ByteDance 和抖音流量；而 ByteDance 确实在山西建有 AI 数据中心。**但作者同时明确指出：AS132510 这个网络属于中国移动，别的公司也在用。** 这个限定很重要 —— 它解释了为什么不能直接把这个 ASN 当成 ByteDance 的资产。

## 五、最容易被误读的一层：那些美国地址是租来的

这是原文里我特别想单独拿出来讲的一段，因为它是一个**看起来像结论、实际上是干扰项**的观察。

在 clawmessenger.com 上，187 次爬虫访问来自 **186 个不同的地址**。前 163 次分布在这些网络：

| 网络 | ASN | 访问次数 |
|---|---|---|
| Datacamp (CDN77) | AS212238 | 54 |
| Web2Objects | AS62874 | 32 |
| Ace Data Centers | AS11798 | 17 |
| EGIHosting | AS18779 | 13 |
| M247 | AS9009 | 10 |
| NET3 (Contact Consumers) | AS46635 | 10 |
| FDCservers | AS30058 | 9 |
| 其它网络 | — | 18 |

而这些地址**大部分只有 1180、40000、60000 三个端口开放**。

原文指出：**60000 正是 Oxylabs 文档里为专用数据中心代理记录的端口。**

我也核对了这一点 —— Oxylabs 官方文档（`developers.oxylabs.io`）在多个集成示例里都写着：

```
Port: 60000
```

**所以结论是：这个爬虫很可能租了一个商业代理池。** 而这类池子，别的客户也能用 —— 也就是说，**从源 IP 追不到运营方，因为 IP 是共享的、每次访问都换。**

这也是为什么作者最终给出的是「未证明谁在运营」而不是「证明了字节跳动在爬」。**IP 层的数据从一开始就不指向任何具体主体**，它只用来证明「真实机器在中国、可见地址是租来的」。

## 六、伪造的来源引用：一个 header 就露馅

「aocr.org 是假来源」这个判断，原文给的是一个很干脆的证据 —— `Sec-Fetch-Site` 这个 header。

浏览器在两种情况下发这个值：用户**直接输入地址**，或者**程序发起请求**。

这个 header 的值是 `none`。

而从 aocr.org **真实点击**过来的请求，应该是 `cross-site`。

**爬虫发的是 `none`。** 所以它是自己写了这个 Referer，不是从 aocr.org 跳过来的。

原文还提到，其他站点所有者也公开了同样的请求头（GitHub 上有对应的 issue 和 PR：GitHub issue 里的完整请求头、GitHub PR 里「一天 2768 个 aocr.org 会话」的记录、以及 blackmoreops 关于 aocr.org 引荐垃圾流量影响 Google Analytics 的说明）。

作者还排查掉了两种可能的「无辜牵连」：

- **aocr.org 没有被黑** —— 没有发现任何入侵迹象；
- **域名选择没有原因** —— 它是一个固定值，从不变化。

**所以这个引荐来源是完全凭空构造的。** 而它的作用很简单：**在分析工具里制造一个看起来很值钱的引荐来源**。Tin 观察到的情况是：每次访问只打开一个页面然后就停，跳出率接近 100%。

这里有个值得学的手法：**用一个域名当 Referer，比伪造 User-Agent 有效得多。** UA 只能影响「它是不是爬虫」这一层判断，而 Referer 直接进入你的分析工具、你的推荐渠道计算、你的「哪些来源带来了流量」报表。**你在 GA4 里看到的引荐来源，直接就是爬虫写进去的字符串。**

## 七、为什么现在出现，以及为什么之前没被发现

原文的「为什么是现在」这一节，我觉得是全文最有洞察力的部分。

作者把时间线拆开：

**不是新的**：

- 这个栈至少从 2024 年就在用 —— ByteDance 的 Bytespider 一直在用；
- 公开日志里从 2024 年起就有带这个栈的**假手机 UA**；
- ByteDance 的 Bytespider 页面承诺遵守 robots.txt，但**不给出用途、不给 IP 段、也不提供任何验证请求归属的方法**。

**是新的（2026 年 9 月下旬起）**：

1. **Windows Chrome 146 的伪装**；
2. **美国代理池**；
3. **每个页面等待 28 秒并滚动**；
4. **伪造 Referer**。

而第 4 点是**让它变得可见**的原因：

> 以前的爬虫不发 Referer，看起来就像直接流量。新出现的引荐来源会直接排在你报表的最上面，很容易被发现。

**这其实是反侦察的一个经典权衡**：不发 Referer 安全但隐形；发 Referer 能污染报表（可能是有意为之，为了让某些人相信流量来自真实引荐），但也让自己暴露在「引荐来源排行」里。

另外还有一个背景数据：按 Cloudflare 的测量，**官方声明的 Bytespider 流量在 2024 到 2025 年间，从 AI 爬虫流量的 42% 跌到了 7%**。而官方页面从不说明 IP 段、不提供验证方法 —— 于是「冒用 Bytespider 名字的undeclared 爬虫」既没有成本，也无法被识别。

原文还提了一个先例：2025 年 Cloudflare 展示过 **Perplexity 使用未申报爬虫**，用的是通用 Chrome UA 和轮换网络。

## 八、怎么拦：按指纹，别按 IP

原文的处置建议分四种情况，但核心只有一句：

> **不要封 IP 地址。** 这个爬虫每次访问都用新地址。而且要预期它会变。**指纹大概率会在 Referer 改变后保留下来。**

具体做法：

**Cloudflare（按指纹）** —— 一条 WAF 自定义规则：

```
any(http.request.headers["accept"][*] contains "image/heif,image/avif")
and not any(lower(http.request.headers.names[*])[*] == "sec-ch-ua")
```

动作设为 Managed Challenge。原文特别提醒：**这条规则也会拦掉官方声明的 Bytespider**，并且**建议先跑 Log 模式**。

**Cloudflare（按 Referer）** —— 第二条规则：`http.referer contains "aocr.org"`。

**GA4** —— 建一个 segment，排除 session source 为 aocr.org 的会话。

**PostHog** —— 排除 `$referring_domain` 为 `www.aocr.org` 的事件。**关键补充**：为了在爬虫改掉 Referer 之后还能找到它，可以同时筛 `$timezone = Asia/Shanghai` 加上 `$screen_width = 800`。

**Plausible、Umami、Fathom** —— 在过滤器里排除 referrer `www.aocr.org`。

**把「指纹优先于 IP」这条当通用原则看**：这类爬虫的 IP 是租来的、每次都换、还可能是多人共享的池子。按 IP 封禁要么无效，要么误伤 —— 因为你封的地址，明天是另一个客户在用。而指纹（UA + header 组合 + TLS 特征 + 行为特征）稳定得多。

原文还有一句提醒值得抄：**指纹大概率会在 Referer 改变后保留下来** —— 也就是说，即使它换了域名、换了伪装身份，网络栈和内部字段名大概率还在。

## 九、几个必须说清的边界

- **证明了「用了 ByteDance 的爬虫栈、服务器在中国」，没证明「字节跳动在爬你」。** 原文明确列为「未证明」，并举例：可能是 ByteDance 团队，也可能是使用同一套浏览器技术的客户（如火山引擎）。
- **作者已于 2026 年 10 月 29 日向 ByteDance 发出证据和三个问题**，原文承诺会补充答复。**本文写作时未见回复。**
- **那 0.08% 的「其它流量」里，大部分是更多未申报爬虫** —— 它们声称自己是 iPhone 或 Android，来源在北京的数据中心，其中一些**使用与 aocr.org 爬虫相同的代理网络**。
- **AS132510 属于中国移动，不是 ByteDance 的资产** —— 别的公司也在用这个网络。原文自己在引用社区路由列表的标注时也强调了这一点。
- **涉及的域名 aocr.org 未被入侵**，请不要去联系 AOCR。
- 本文只做防守方视角的分析，**不包含任何用于伪装浏览器指纹或规避爬虫检测的技术细节**。

---

## Sources

- Tin Analytics, *Getting traffic from aocr.org? That's ByteDance crawling your website* (2026-10-29, Ege Demir): <https://tin.computer/blog/aocr-org-referrer-bot>
- APNIC RDAP, AS132510（作者核对用）: <https://rdap.apnic.net/autnum/132510>
- lynx-family/lynx，`platform/darwin/common/lynx/public/base/LynxResourceFetcher.h`（含 `like forest` 注释，本文核对用）: <https://github.com/lynx-family/lynx>
- ByteDance, *What is Bytespider*: <https://www.bytedance.com/en/tech/robots.txt>
- Oxylabs, *Dedicated Datacenter Proxies* 文档（端口 60000）: <https://developers.oxylabs.io/products/proxies/dedicated-datacenter-proxies/enterprise/making-requests>
- Cloudflare, *From Googlebot to GPTBot: who's crawling your site* (2025-07): <https://blog.cloudflare.com/from-googlebot-to-gptbot-whos-crawling-your-site/>
- Cloudflare, *Perplexity is using stealth, undeclared crawlers* (2025-08): <https://blog.cloudflare.com/perplexity-is-using-stealth-un-declared-crawlers-to-track-netflix/>
- Fortune, *ByteDance's Bytespider scrapes 25 times faster than GPTBot* (2024-10): <https://fortune.com/2024/10/19/bytedance-ai-crawler-bytespider-scrapes-web-faster-than-openai-gptbot/>
- GitHub issue / PR（其他站主的请求头与「一天 2768 会话」记录）: <https://github.com/lynx-family/lynx/issues>

### 事实边界说明

- 全部指纹数据、请求头、对照组统计、WebRTC 探测结果、处置建议：引自 Tin Analytics 原文。
- **AS132510 的注册信息为本文用 APNIC RDAP 独立核对**：名称 `ShanXiMCC-IDC`，注册实体 `China Mobile Communications Corporation`，与原文描述一致。
- **「forest」注释为本文在 ByteDance 开源的 lynx-family/lynx 仓库 develop 分支中定位到的原始代码**：`LynxResourceFetcher.h` 的 `like forest`，另有两处 `LynxResourceServiceFetcher.mm` 与 `LynxResourceRequest.h` 提到 forest。原文表述「提到过一个类似 forest 的定制资源加载器」准确。
- **端口 60000 为本文核对 Oxylabs 官方文档所得**（`developers.oxylabs.io` 的集成示例中列明 `Port: 60000`），与原文一致。
- **「谁在运营」明确标注为未证明**，原文与本文均未做此归因。
- **ByteDance 的回复截至本文写作时未见**；原文承诺补充后会在文中更新。
