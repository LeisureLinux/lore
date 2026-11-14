---
title: "Kitesurf 开源：跑在 Workers 上的 agent 浏览器"
date: 2026-11-14
slug: cloudflare-kitesurf-open-source-agent-browser
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Cloudflare 官方博客《Kitesurf is now open source》（Celso Martinho、Rui Figueira、Bernardo Pereira、Luís Duarte，2026-11-13 20:20 UTC；8 月首发、9 月 WebMCP 更新、兑现开源承诺、Apache 2.0、Workers 上解析 HTML/CSS/JS 与截图、CDP 支持 Puppeteer、目标是比 Chromium 更省 CPU/内存、依赖 Blitz/Stylo/Boa/Linebender/Krilla、三大部件 Engine/PageScript/PageRenderer、本地 pnpm run dev 与 127.0.0.1:8787、部署需 Workers Paid 因 Dynamic Workers、贡献需先开 issue 并获 maintainer vouch、WPT 与 benchmarks 页）＋ Cloudflare Developers Changelog《Kitesurf is now open source》（2026-11-12；明确 experimental、under heavy development、无内置认证需用 Cloudflare Access 或其他认证层保护部署、Workers Paid 要求、兼容性/渲染保真度/性能仍在改进）＋ GitHub cloudflare/kitesurf README 与仓库 API 元数据（Apache-2.0、TypeScript、2026-09-30 建库、375 commits、614 stars / 24 forks / 35 open issues、默认分支 main、homepage kitesurf.dev、topics agents/browser-automation；README 明写「without Chrome or a browser container」、Blitz MIT OR Apache-2.0 / Stylo MPL-2.0 / Boa Unlicense OR MIT、Boa 仅在无法在 Dynamic Workers 里跑 JS 时兜底、CDP 端点未认证时拿到 URL 即可浏览网页或接 Puppeteer、SECURITY.md）＋ Phoronix《Cloudflare Open Sources Kitesurf: Their Web Browser For AI Agents》（Michael Larabel，2026-11-13 04:07 PM EST；引用官方动机原话与 kitesurf.dev 链接）＋ Phoronix 3 月 Domicile Desktop 报道（Chromium 改版 + Rust 平铺合成器，作同类对照）＋ Cloudflare 8 月首发公告与 9 月 Kitesurf update 的引用（经开源博客转述）"
original_date: 2026-11-13
original_url: "https://www.phoronix.com/news/Cloudflare-Kitesurf-Open-Source"
description: "解读 Cloudflare 开源 Kitesurf。它不是 Chromium fork，也不是给人的浏览器，而是一台跑在 Cloudflare Workers 上的「无状态、给 AI agent 用的浏览器引擎」：解析 HTML、套用 CSS、执行页面 JavaScript、渲染截图，全程没有 Chrome 或浏览器容器；对外只通过 Chrome DevTools Protocol 说话，Puppeteer 或 agent harness 连上 WebSocket 就能用。文章拆解仓库里的三层结构（Engine 管会话与客户端连接、PageScript 跑页面与 JS、PageRenderer 画结果）与开源依赖栈（Blitz 提供 DOM/布局/绘制，Stylo 做 CSS，Boa 在 WebAssembly 里兜底执行 JS，Linebender 做文本与 2D 图形，Krilla 生成 PDF；各依赖保留各自许可证，NOTICE 记录第三方声明）。也写清设计取舍与边界：之所以省 CPU/内存，是因为不为人类交互维护完整浏览器；Dynamic Workers 为页面做隔离，因此部署到自己的 Cloudflare 账户必须 Workers Paid；引擎没有内置认证，官方文档明确要求用 Cloudflare Access 或其他认证层保护，否则拿到 URL 的人就能浏览网页、接 CDP 客户端。时间线为 8 月首发、9 月加 WebMCP/新 API、11 月 12–13 日按承诺开源（Apache 2.0）。项目状态如实标注：experimental、under heavy development，官方把精力放在 Web Platform Tests 兼容性、渲染保真度与性能上，贡献需先开 issue 并获 maintainer vouch；仓库 2026-09-30 建、375 commits、614 stars。并与 2026 年 3 月 Phoronix 报过的 Domicile Desktop（把 Chromium 当 DOM 渲染器）做对照，指出两条「为 agent/自定义桌面造浏览器」的路子差异。结论：Kitesurf 值得关注的不是「又一个开源浏览器」，而是把浏览器能力拆成可按需调用的无状态服务，同时把兼容性与认证责任明确交回给使用者。"
published: true
---

11 月 13 日，Cloudflare 兑现了 8 月首发时留下的承诺：Kitesurf 以 Apache 2.0 开源。Phoronix 当天也做了报道。

容易被标题带偏的一点是：这不是 Chromium 的另一个 fork，也不是给人点网页用的浏览器。它是一台给 AI agent 用的无状态浏览器引擎，整个跑在 Cloudflare Workers 上。

## 一、它到底是什么

按官方博客与仓库 README 的定义，Kitesurf 在 Workers 里完成四件事：解析 HTML、套用 CSS、执行页面 JavaScript、渲染截图 —— without Chrome or a browser container，既没有 Chrome 进程，也没有浏览器容器。

对外接口只有一个，官方文档那句「It supports the Chrome DevTools Protocol (CDP)」点明了它为什么能被现成工具接管：Chrome DevTools Protocol（CDP）。这意味着 Puppeteer 这类现成客户端可以直接连，AI harness 也可以把本地 CDP 端口当浏览器接管。官方给的示例几乎和普通 Puppeteer 脚本一样：连 `ws://127.0.0.1:8787/devtools/browser`，`newPage()`、`goto()`、`screenshot()`，然后断开。

Cloudflare 给的动机很直白：让 agent 有一台轻量、能加载网页、能跑 JS、能交互的浏览器，用比完整 Chromium 更少的 CPU 与内存，并借 Workers 全球网络按需伸缩。这个省资源的说法有前提 —— 它不为人类交互维护完整浏览器状态；代价是兼容性还在补。

## 二、仓库里有什么

代码分成三块：

- Engine：管理浏览器会话与客户端连接；
- PageScript：跑页面及其 JavaScript；
- PageRenderer：把结果画出来。

底下是一组编译到 WebAssembly 的 Rust 开源项目，官方逐个点名致谢：

| 组件 | 职责 | 许可证 |
|---|---|---|
| Blitz（DioxusLabs） | HTML 解析、DOM、布局、绘制 | MIT OR Apache-2.0 |
| Stylo（Servo） | CSS 解析、层叠、计算样式 | MPL-2.0 |
| Boa | 在 WASM 里执行 JS | Unlicense OR MIT |
| Linebender 系列 | 文本排版与 2D 图形 | 各自许可 |
| Krilla | 生成 PDF | 各自许可 |

两个细节值得记：Boa 只是兜底 —— 官方写的是「只有在无法把 JavaScript 放进 Dynamic Workers 运行时才用 WASM 里的 Boa」；以及这些依赖保留各自许可证，仓库用 `NOTICE` 记录第三方声明，不是简单一句 Apache 2.0 就能概括整棵依赖树。

所有包、Rust 核心、DOM shims、renderer 与 `kitesurf-cli` 都在 `packages/` 下分目录放着。命令也简单：`pnpm install --frozen-lockfile`、`pnpm run dev`，首次构建要编译 Rust 核心，之后 Wrangler 起本地服务在 `127.0.0.1:8787`。

## 三、两条容易被忽略的边界

其一，部署不是「免费自托管」。 官方文档明确写：Kitesurf 用 Dynamic Workers 为页面创建隔离的 Worker，而 Dynamic Workers 属于 Workers Paid 计划，所以部署到自己的 Cloudflare 账户需要付费计划；本地 `wrangler dev` 不受此限。

其二，它没有内置认证。 这条比第一条更要紧。Changelog 专门加了 Important 提示：部署后要用 Cloudflare Access 或其他认证层保护；README 说得更具体 —— 谁拿到 URL，谁就能打开 DevTools 通过这个引擎浏览网页、接上 Puppeteer 或其他 CDP 客户端。对一个能替你访问任意站点的浏览器引擎来说，这是实打实的 SSRF / 代理滥用面，不是文档里随手一提的注意事项。

此外官方把它标成 experimental、under heavy development，当前重心是 Web Platform Tests 兼容性、渲染保真度与效率，`kitesurf.dev/wpt` 和 `/benchmarks` 公开进度。贡献规则也不宽松：先开 issue 附最小复现或方案、获得 maintainer vouch，再提 PR；小而聚焦、带测试与证据的改动优先，大重写和无关清理不受欢迎 —— 这跟最近一系列开源项目被 AI 生成 PR 淹没后的收紧动作是同一类信号。

## 四、时间线与仓库状态

| 时间 | 事件 |
|---|---|
| 2026-08 | Agents Week 期间首发 Kitesurf：跑在 Workers 上的无状态 agent 浏览器 |
| 2026-09 | 更新：WebMCP 支持、新 API、兼容性改进；两次都承诺会开源 |
| 2026-09-30 | `cloudflare/kitesurf` 仓库创建 |
| 2026-11-12 | Cloudflare Developers Changelog 记录开源 |
| 2026-11-13 | 官方博客正式宣布，Apache 2.0；Phoronix 同日报道 |

GitHub API 查询（2026-11-14）：TypeScript、Apache-2.0、375 commits、614 stars / 24 forks / 35 open issues，默认分支 `main`，主页 `kitesurf.dev`。仓库很年轻，但迭代密度不低。

顺带一个同类对照：2026 年 3 月 Phoronix 报过 Domicile Desktop，那条路线是改 Chromium，把原生 Wayland 窗口表示成 DOM 元素，再用 HTML/CSS 组织桌面；Kitesurf 反过来，不碰 Chromium，用 Rust/WASM 组件重新拼一个够 agent 用的最小浏览器。一个保留完整 Web 兼容性但背着 Chromium 的重量，一个丢掉大量兼容性换无状态与低成本。两条路都叫「为 agent 造浏览器」，取舍几乎相反。

## 五、事实边界

- 本文未编译 Kitesurf、未部署 Workers、未跑 WPT 或 benchmark；性能与兼容性表述均来自官方博客/文档，官方自己也说仍在改进。
- 「比 Chromium 省 CPU/内存」是 Cloudflare 的设计目标，官方未在开源公告里给出可复现的对比数字。
- 8 月首发与 9 月 WebMCP 更新的细节，本文依据 11-13 开源博客的回顾转述，未逐字核对那两篇原文。
- 仓库数字为 2026-11-14 查询时点；Changelog 日期（11-12）与博客 JSON-LD 日期（11-13 20:20 UTC）不同，本文按各自出处标注，不强行统一。
- 安全边界（无内置认证、CDP 端点暴露后果、Dynamic Workers 付费要求）来自 Cloudflare 官方文档与 README，不是第三方推测。

## 六、结论

Kitesurf 值得关注的点，不在「Cloudflare 又开源了一个浏览器」，而在它把浏览器能力拆成可按需调用的无状态服务：不要窗口、不要人类交互、不要常驻容器，只留 HTML/CSS/JS/截图与一个 CDP 端口。对批量跑网页任务的 agent 来说，这个模型比给每个任务起一个 Chromium 干净得多。

但开源不等于开箱即用。Workers Paid 是部署门槛，兼容性仍在追 WPT，认证要自己加，贡献还要先过 vouch。官方把这三件事都写在了文档里 —— 读公告时别只带走 Apache 2.0 那一行。

## Sources

- Cloudflare《Kitesurf is now open source》（2026-11-13）：<https://blog.cloudflare.com/kitesurf-open-source/>
- Cloudflare Developers Changelog（2026-11-12）：<https://developers.cloudflare.com/changelog/post/2026-11-12-kitesurf-open-source/>
- GitHub 仓库与 README：<https://github.com/cloudflare/kitesurf> ｜ 项目站：<https://kitesurf.dev/> ｜ WPT：<https://kitesurf.dev/wpt> ｜ 基准：<https://kitesurf.dev/benchmarks>
- Phoronix《Cloudflare Open Sources Kitesurf: Their Web Browser For AI Agents》：<https://www.phoronix.com/news/Cloudflare-Kitesurf-Open-Source>
- Browser Run 文档：<https://developers.cloudflare.com/browser-run/kitesurf/> ｜ Dynamic Workers：<https://developers.cloudflare.com/dynamic-workers/>
- 对照：Phoronix《Domicile Desktop Brings Web Technologies To Building Wayland Desktops》：<https://www.phoronix.com/news/Domicile-Desktop-Wayland>
