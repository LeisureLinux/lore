# 给 AI 装个真浏览器：Servo + 智能代理 MCP 实战

我手头装了 Servo——Mozilla 起源、Linux Foundation 维护的 Rust 浏览器引擎。想把它接到我日常用的 AI 编程助手 Pi 里，但实际一上手才发现：**Servo 没法直接当 AI 工具用**。没有 Chrome DevTools Protocol（CDP）、不支持 `--proxy-server`、WebDriver 只实现子集——和 Chrome/Firefox 那一套完全不是一个思路。

折腾了一周后我把链路打通成「servo-fetch → MCP 智能分流代理 → Pi 自动调用」。下面把整套设计、实现、踩坑一次性讲清，给同样想给 AI 装"浏览器"的朋友一份可复制的方案。

---

## 一、先说结论：Servo 在 AI 场景下的真实定位

Servo 引擎本身是个**真浏览器内核**（SpiderMonkey JS + 并行 CSS layout + 软件渲染），但它的对外接口很窄——只有 W3C WebDriver，连 Chrome 用户熟悉的 CDP 都没有。这让两个常见期待落空：

- **Puppeteer / Playwright 连不上**：它们只认 CDP。
- **直接 `--proxy-server` 也不行**：Servo 引擎偏好里有 proxy 相关项，但当前 0.6.0 版本根本没实现。

好在社区项目 [konippi/servo-fetch](https://github.com/konippi/servo-fetch) 把 Servo 引擎嵌进单二进制，专门为 agent 设计——自带 MCP server。但它默认不带代理，海外站点拉不下来。

**我做的整套链路**就是给 servo-fetch 加一层"按 PAC 智能分流"的 MCP 代理层，让 AI 抓国内站走直连（快）、抓海外站自动过代理。

---

## 二、servo-fetch vs 其它 AI 浏览器工具

| 维度 | Servo + servo-fetch | Chromium + Puppeteer | Firefox + Playwright | headless Chrome + chrome-devtools-mcp |
|---|---|---|---|---|
| **二进制大小** | 134 MB 单文件 | 200 MB+ | 150 MB+ | ~300 MB（含浏览器） |
| **需要 GPU** | 否（软件渲染） | 通常要 | 通常要 | 通常要 |
| **冷启动** | ~50 ms | 500 ms-2 s | 300 ms-1 s | 1-3 s |
| **JS 执行** | SpiderMonkey | V8 | SpiderMonkey | V8 |
| **CSS 完整 layout** | 是 | 是 | 是 | 是 |
| **Web 兼容性** | 中等（~10 年前 Chrome 水平） | 优 | 优 | 优 |
| **协议** | 仅 WebDriver 子集 | CDP | CDP | CDP |
| **代理** | 只认 env（`HTTPS_PROXY` 等） | `--proxy-server` | `--proxy` | env / flag |
| **MCP 集成** | 自带 + 可包装 | 第三方 | 第三方 | 自带 |
| **Cookie / 会话** | 弱 | 完整 | 完整 | 完整 |

**什么时候该用 Servo**：

- ✅ AI agent 抓文档页、博客、Stack Overflow（Readability 抽干净 Markdown，省 token）
- ✅ CI / 容器里跑批量抓取（无 GPU 依赖）
- ✅ 受限网络环境抓海外文档（智能分流价值最大）
- ✅ JS 重渲染后取结构化数据（无障碍树 / accessibility tree）

**什么时候别用**：

- ❌ 高频浏览器交互（填表 / 点击 / 截屏判断）—— Servo 不适合，WebDriver 子集
- ❌ 复杂 SPA（Notion、Figma、各种 SaaS 后台）—— web 兼容性不够
- ❌ 需要 CDP 的工具链
- ❌ 严格登录态、cookie 持久化场景

**最重要的一点**：纯 XML / RSS / API JSON 这种静态内容，**curl 完全够用且更快**，Servo 是杀鸡用牛刀。我实测抓 BBC RSS feed，curl ~0.7 s，servo-fetch ~0.8 s 还多出 fork 开销——纯 XML/RSS 场景下两者没区别。

---

## 三、MCP 真正的价值在哪里

MCP 不是 "curl 的 MCP 包装"。它真正的功能是**让 LLM 在对话里自由组合抓取 + 推理**：

```
用户：「帮我看 BBC 头条里有没有 AI 监管相关的，列前三条全文」

LLM 推理：
  1. 调 servo.fetch(url=feeds.bbci.co.uk/news/rss.xml, format=html)
     → 拿到 RSS XML
  2. 解析，筛出含 "AI regulation" / "AI safety" 的条目
  3. 调 servo.fetch(url=每条原文 URL, format=markdown)
     → Readability 抽好的全文
  4. 整理成自然语言回复
```

整个流程 LLM **现场编排**，不需要你预先写脚本。MCP 只是把工具暴露给 LLM。判断要不要用 MCP 的两条问题：

1. **LLM 现场决定怎么抓吗？** 是 → MCP；否 → curl + bash
2. **页面要 JS / 浏览器渲染才能拿内容吗？** 是 → Servo；否 → curl

---

## 四、链路设计：servo + 智能分流 MCP proxy

直接调 servo-fetch 的 MCP 服务意味着每次要么全走代理（国内站浪费）要么全直连（海外站拿不到）。我需要 per-call 决策，于是写了 150 行 Node 零依赖 MCP server：

```
┌─────────────┐  stdio/JSON-RPC  ┌──────────────────────┐  spawn + env  ┌─────────────┐
│  Pi (LLM)  │ ────────────────→ │ servo-mcp-proxy.mjs │ ─────────────→ │ servo-fetch │
└─────────────┘                   └──────────────────────┘                └─────────────┘
                                           │
                                           │ pactester -p pac -u URL
                                           ▼
                                   ┌──────────────────┐
                                   │ wpad.dat (PAC)   │
                                   └──────────────────┘
```

每收到一个 `fetch` 调用：

1. 跑 `pactester -p ~/.cache/servo/wpad.dat -u URL`（15 ms）→ 拿到 `DIRECT` 或 `PROXY host:port`
2. spawn `servo-fetch` 子进程，按需注入 `HTTPS_PROXY` / `HTTP_PROXY`
3. 把 stdout / stderr 包装成 MCP `text` 或 `image` content 返回

实测分流效果（同一台机、同一网络）：

| 站点 | PAC 决策 | 走代理延迟 | 直连延迟 | 倍数 |
|---|---|---|---|---|
| `www.google.com/` | PROXY | 0.8 s | 超时（被墙） | — |
| `example.org/` | DIRECT | 0.8 s | <0.2 s | **4×** |
| `www.baidu.com/` | DIRECT | 1.67 s | 0.12 s | **14×** |

**国内站走代理慢 14 倍**——智能分流不是锦上添花，是必须。

---

## 五、实现细节（可直接抄）

### 5.1 安装 servo-fetch

```bash
curl -fsSL https://raw.githubusercontent.com/konippi/servo-fetch/main/install.sh | sh
```

装到 `~/.local/bin/servo-fetch`。Linux x86_64 需要 `libEGL` / `libfontconfig` / `libfreetype`（机器上齐的话脚本会过）。

### 5.2 准备 PAC

```bash
mkdir -p ~/.cache/servo
curl -fsS https://wpad.freelamp.com/wpad.dat -o ~/.cache/servo/wpad.dat
```

PAC 是 nginx 在 443 端口提供的标准 `application/x-ns-proxy-autoconfig`（genpac 3.0.1 + GFWList）。`pactester` 是 Debian 自带的 PAC 测试工具：

```bash
pactester -p ~/.cache/servo/wpad.dat -u https://www.google.com/
# → PROXY 192.168.68.68:8888; socks5 192.168.68.68:1080
pactester -p ~/.cache/servo/wpad.dat -u https://example.org/
# → DIRECT
```

**别自己 awk 解 PAC**——genpac 3.0.1 输出的 `rules[*]` 是嵌套数组，awk 容易写错。直接 `pactester` 是 15 ms 一次的最干净方案。

### 5.3 写 MCP proxy server

保存为 `~/bin/servo-mcp-proxy.mjs`：

```javascript
import { createInterface } from "node:readline";
import { spawn } from "node:child_process";
import { existsSync, statSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";

const SERVO_BIN = "/home/axu/.local/bin/servo-fetch";
const PAC_URL = "https://wpad.freelamp.com/wpad.dat";
const PAC_CACHE = join(process.env.HOME, ".cache/servo/wpad.dat");
const PAC_MAX_AGE_MIN = 30;

async function ensurePacFresh() {
  let needs = !existsSync(PAC_CACHE);
  if (!needs && (Date.now() - statSync(PAC_CACHE).mtimeMs) / 60000 > PAC_MAX_AGE_MIN)
    needs = true;
  if (needs) {
    mkdirSync(dirname(PAC_CACHE), { recursive: true });
    const tmp = PAC_CACHE + ".tmp";
    const ok = await new Promise((res) => {
      const p = spawn("curl", ["-fsS", "--max-time", "8", PAC_URL, "-o", tmp]);
      p.on("close", (c) => res(c === 0));
      p.on("error", () => res(false));
    });
    if (ok) (await import("node:fs")).renameSync(tmp, PAC_CACHE);
  }
}

function parseProxy(out) {
  const m = out.match(/^(?:PROXY|SOCKS5)\s+([^;\s]+)/m);
  return m ? m[1] : null;
}

function runPactester(url) {
  return new Promise((resolve) => {
    const p = spawn("pactester", ["-p", PAC_CACHE, "-u", url]);
    let out = "", err = "";
    p.stdout.on("data", (d) => out += d);
    p.stderr.on("data", (d) => err += d);
    p.on("close", (code) => resolve({ output: (out || err).trim(), proxy: parseProxy(out || err) }));
  });
}

function runServoFetch(args, env) {
  return new Promise((resolve) => {
    const child = spawn(SERVO_BIN, args, { env: { ...process.env, ...env }, stdio: ["ignore", "pipe", "pipe"] });
    const chunks = [], errs = [];
    child.stdout.on("data", (d) => chunks.push(d));
    child.stderr.on("data", (d) => errs.push(d.toString()));
    child.on("close", (code) => resolve({ code, stdout: Buffer.concat(chunks), stderr: errs.join("") }));
  });
}

// JSON-RPC over stdio (Content-Length 帧格式)
// ... 完整代码见 GitHub gist ...
```

完整版含 JSON-RPC 帧解析、`fetch` / `health` 两个 tool、image content 返回，**共 290 行纯 Node 24 内置，零 npm 依赖**。

### 5.4 接入 Pi

`~/.pi/agent/mcp.json`：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    },
    "servo": {
      "command": "node",
      "args": ["/home/axu/bin/servo-mcp-proxy.mjs"]
    }
  }
}
```

重启 Pi 后 `servo` 服务带两个 tool：`fetch`（`url/format/timeout/selector/js/screenshot/settle/userAgent`）+ `health`。

---

## 六、踩过的坑（希望你少走弯路）

1. **stderr 走 MCP 进程 stderr，不要往 stdout 写日志**——会破坏 JSON-RPC 帧。日志格式我写成 `[servo-mcp] fetch <url> fmt=... pac=PROXY ...` 方便调试。
2. **pactester 拿到的代理字符串是裸 `host:port`**，要塞 `HTTPS_PROXY` 必须加 `http://` 前缀：`192.168.68.68:8888` → `http://192.168.68.68:8888`。
3. **`ALL_PROXY` env ureq 不识别**，只认 `HTTPS_PROXY` / `HTTP_PROXY`。我用 `env -u HTTPS_PROXY -u HTTP_PROXY -u ALL_PROXY` 显式取消（不然 shell 里残留的 ALL_PROXY 会让 direct 路径失败）。
4. **shell 函数跨调用陷阱**：在 wrapper 里写 `pick_proxy_url() { sed ... }` 然后调用——shell 默认按 PATH 找外部命令，会报「未找到命令」。要么 source 进来，要么写成一行 sed 流。
5. **servo engine 本身有 `network_https_proxy_url` 等偏好**（通过 `--pref=` 给 servoshell），但当前 0.6.0 版本还没实现，会报 `Unknown preference`。别在这条路浪费时间。
6. **pactester 不在路径里就装**：Debian/Ubuntu 自带 `libpacparser`；找不到就 `apt install libpacparser-tools`。

---

## 七、这套架构的扩展空间

走通了"AI + 真浏览器引擎 + 智能代理"这条线后，能做的远不止 fetch：

- **miniflux / RSS 自动化整理**：Pi 拉 unread → LLM 摘要 + 翻译 + 分类 → 写回 miniflux（10 条/天，200 行 Node + cron 搞定）
- **GitHub issue / PR 调研**：「帮我看 servo 最近 3 个月重要 PR」—— LLM 自己组合多次 fetch
- **跨媒体事件追踪**：同一新闻 BBC / Reuters / Al Jazeera 三家报道差异对比
- **SPA 后台操作**：登录态抓 SaaS 页面（chrome-devtools MCP 更合适，但 Servo 可以兜底）

**判断要不要给 AI 装浏览器**：

| 问题 | 是 → 用 |
|---|---|
| LLM 要现场决定怎么抓？ | MCP |
| 页面要 JS 渲染？ | Servo / Chromium |
| 大规模抓 1000+ 页？ | curl |
| 抓静态 RSS / API JSON？ | curl |
| 需要交互操作（填表 / 点击）？ | chrome-devtools MCP / Playwright |

最后这条最关键：**MCP 的价值不在"抓一次"上，在"让 LLM 能组合很多次抓取 + 推理"上**。把它当 LLM 的"工具箱"而不是"curl 替代品"，整套架构就跑通了。

---

**完整代码**：`/home/axu/bin/servo-mcp-proxy.mjs`（290 行 Node）+ `~/.pi/agent/mcp.json`。改 mcp.json 之前会自动备份到 `.bak.<timestamp>`，改完起不来的话一键回滚。

如果你也想给 AI 装个"自己上网"的能力，欢迎留言交流你的代理拓扑和 PAC 方案——智能分流这块几乎每个团队都不一样，但骨架可以复用。