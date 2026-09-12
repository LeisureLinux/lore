> **译文来源**：[*google.com/goto: Google's anti-scraping update*](https://www.autom.dev/blog/google-search-goto-links)，作者 Autom Team，发布于 2026-08-27，站点 Autom（autom.dev，搜索 API 提供商）。以下为译文 + 解读。

# google.com/goto：Google 的反爬虫新招

如果你最近从 Google 搜索结果里抓过链接，会发现一个不显眼但很关键的变化：搜索结果的 `href` 不再是目标网页的 URL，而是 `google.com/goto?url=...` 这种重定向壳。点过去 Google 才会把你转到真正的目的地。这件事，Autom 在博客里把它叫做 **Google 的反爬虫更新**——意图很明确：让「光爬 SERP HTML 不再能拿到目的地 URL」这件事变得更贵、更慢、更可观测。

## 一、发生了什么

Google Search 现在把有机结果的链接改写成 `google.com/goto?url=...`，而不是在 HTML 里直接暴露目标 URL。

点结果时，Google 会把你重定向到真实页面。`url` 参数用的是一种 Google 自有的编码——不是普通 base64，**离线解不出来**。看起来像是 Google 索引记录里的某个不透明引用。

到 2026 年 8 月下旬，这种格式在登出状态 / 隐私模式下已经稳定出现。仍然可能是实验，但已经不再局限于一小部分 SERP。

## 二、和 `google.com/url` 不是一回事

Google 之前就用过重定向包装壳，老格式是 `google.com/url?q=[URL 编码的目标]`，目标 URL 在查询串里直接可读。

新的 `goto` 格式不一样：

- 结果的 `href` 是 `/goto`，不是目的地
- 你**离线解码不了** `url=` 那坨 blob
- 真实 URL 出现在 `/goto` 的 **`Location` 响应头**里。**用 HEAD 请求读那个头，不要跟着重定向走到底**

Google 自己画 SERP 还需要目的地（用来显示域名、favicon、署名），所以页面 HTML 里仍有目的地 URL 的副本。这跟读 `Location` 头是两件事，不能混。Autom 给了具体做法：[google.com/goto: read Location with HEAD](https://www.autom.dev/blog/google-goto-url-fix)。

这个转变对任何**用 SERP 数据建索引**的项目影响都很大。

## 三、Google 为什么这么做

这跟 Google 一贯的反 SERP 收割动作是一致的——尤其是反 AI 爬虫和 SEO 爬虫批量抓结果 URL 来建自己的索引。

明文链接时代，一个爬虫可以从 HTML 里直接解析几千个 URL，根本不用再回 Google 一趟。换 `goto` 之后，**每个结果都得回 Google 一次才能知道目的地**。你读 `Location`，不跟到底。这样更慢、更有噪声，也给 Google 一个清晰的信号：当同一个客户端连续解析几百个链接，那就是爬虫。

配合之前撤掉 `&num=100`、收紧 BotGuard/SearchGuard 这些动作，Google 一直在稳定抬升「天真式 SERP 抓取」的成本。

## 四、Autom 这边看到了什么

最初 Autom 是在一小部分 SERP 上看到 `goto` 链接的。在那个覆盖率下，做「对所有人都不破」的兼容补丁很难。

到 2026 年 8 月下旬，登出 / 隐私模式下 `goto` 已经非常一致——这些会话下的 Google Search 结果 URL **事实上都是 `goto`**。

Autom 一直在盯这次 rollout 并做对抗测试。

## 五、Autom 的更新

**已经更新了 Google Search 管道**，能解析 `google.com/goto` 链接（读 `Location` 头，不跟到底），并在 API 响应里按用户现有的结构化字段返回最终目的地 URL。

也就是说：如果你在调 Autom 的 Google Search 接口，**不用改自己的集成**，继续拿到可用的目的地 URL。如果 Google 的重定向格式再变，他们也会跟。

---

## 我的解读

这篇 Autom 写得克制，但里面藏了三个值得记住的点。

**第一，Google 的反爬升级已经形成「组合拳」。** 撤掉 `&num=100`（一次拿 100 条结果的隐藏参数）、收紧 BotGuard/SearchGuard、现在再加 `goto` 把 URL 离线解码堵死——这三招叠加，意味着 SERP 抓取从「纯 HTML 解析」必须升级到「对每个结果都打一次 Google」。对任何想拿搜索结果建索引的项目（包括但不限于 SEO 工具、学术数据集、AI 训练用的 query→URL 对），**单位成本至少上一个数量级**。这不是单一动作，是一个长期方向。

**第二，HEAD 请求读 Location 是个被低估的工程技巧。** `Location` 头不是只在浏览器重定向时才有用——很多中间环节（CDN、网关、反爬壳）都依赖它来**说明**目的地而不强制跟随。养成「先 HEAD 看 Location，需要时再 GET」的习惯，能省掉很多无谓的下载，也能避开一些会污染统计的重定向（302/307 链尾）。这是被 Go 的 `http.Client.CheckRedirect` 和 curl 的 `--max-redirs` 反复验证过的模式。

**第三，「页面里仍有目的地副本」是 Google 故意留的缝。** SERP 要渲染就必须有目的地（域名/favicon/署名），所以 HTML 里仍有明文。这就给了反反爬虫一方一个低成本通道：用浏览器渲染 / DOM 解析直接从渲染树里读 `cite`、链接文本、`data-*` 属性等带 URL 的副本，不必去打 `goto`。**但这条路对正经客户端更贵、更慢、也更容易触发 Google 的反爬阈值**——也就是说，「免费的破解」不存在了，剩下的只是「更贵、更慢、更像人」的破解。

**对运维/工程同学的实际建议**：

1. **别再用 `&num=100`**——早就失效了，写在文档里只会误导新人。
2. **任何「从 SERP 建索引」的脚本都要准备好退路**：`google.com/goto` 之外，还有 Bing/DDG/Startpage 备用；多源融合是常态，单押 Google 不再现实。
3. **真要 Google，走 API**（Programmable Search、Knowledge Graph、Google Trends 等官方通道），别自己爬 SERP——这次更新只是把门槛又抬高一截，下次只会更高。
4. **如果你做的是浏览器自动化/agent 类产品**，注意 `goto` 重定向链对纯 headless 的影响——很多自动化工具默认跟着重定向走完，很容易被 `goto` 误伤或被 Google 当成爬虫。

一句话：Google 没打算封死所有人，但打算把所有「不用付 API 费」的捷径持续抬高到不划算的水位。这是商业策略，不是技术对抗——理解这一点，比背技术细节更重要。