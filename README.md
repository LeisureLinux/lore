# 📜 LeisureLinux Lore

> Linux 底层机制、DevSecOps 安全加固与基础架构深度技术知识库

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-059669)](https://freelamp.com)
[![License](https://img.shields.io/badge/license-CC%20BY--SA%204.0-blue)](https://creativecommons.org/licenses/by-sa/4.0/)
[![LLMs.txt](https://img.shields.io/badge/LLMs-txt-8B5CF6)](https://freelamp.com/llms.txt)
[![RSS](https://img.shields.io/badge/RSS-feed-FF6600)](https://freelamp.com/rss.xml)

**LeisureLinux Lore** 是一份面向 **Linux 内核工程师、SRE、DevSecOps 从业者** 的深度技术写作存档。内容覆盖 Linux 内核机制、TLS/PKI 信任链、网络协议栈安全、CVE 漏洞分析、DevOps 工具链与 AI 安全运营。

每篇文章提供 **生产级配置、诊断命令与架构级分析**，适合高级工程师直接参考落地。

---

## 📖 最新文章

| 日期 | 标题 | 领域 |
|------|------|------|
| 2026-08-06 | [被放弃的 p7zip，终于换上了官方 7-Zip：Debian LTS 的 DLA-4719-1 安全公告解读](https://freelamp.com/articles/2026-08-06_dla-4719-1-p7zip-7zip/) | CVE · Debian LTS · 供应链安全 |
| 2026-08-05 | [能力逼近前沿、护栏却可剥除：SaferAI 对 GLM-5.2 的独立风险评估解读](https://freelamp.com/articles/2026-08-05_glm52-saferai-risk-eval/) | AI 安全 · 开源权重模型 · 风险评估 |
| 2026-08-05 | [Google 用 AI 修了 1072 个漏洞，还把 Chrome 改成每周更新——企业的变更管理还跟得上吗？](https://freelamp.com/articles/2026-08-05_chrome-ai-patch-1072/) | 变更管理 · Chrome · AI 安全 |
| 2026-08-04 | [被遗忘的 DNS 记录，正在给骗局开路——Hazy Hawk 子域名劫持全拆解](https://freelamp.com/articles/2026-08-04_hazy-hawk-dns-subdomain-hijack/) | DNS · 子域名劫持 · 威胁情报 |
| 2026-08-04 | [别急着给 AI 排岗位——读完麦肯锡《Rewired》我的一点不同意见](https://freelamp.com/articles/2026-08-04_rewired-dont-hire-agent-managers/) | AI · 组织管理 · 管理幅度 |
| 2026-08-04 | [你的下一个下属，是个 AI——麦肯锡《Rewired》的答案](https://freelamp.com/articles/2026-08-04_rewired-agent-managers/) | AI · 组织管理 · 智能体 |
| 2026-08-01 | [一文讲透 Linux TLS 信任库：从 OpenSSL 到 Java/Go/Python/Node.js 的证书链校验全景](https://freelamp.com/articles/2026-08-01_tls-trust-store/) | Linux · TLS · PKI · 国密 |
| 2026-08-01 | [这个开源项目让 GitHub .deb 安装从 5 步变成 1 步](https://freelamp.com/articles/2026-08-01_ghdeb-deb-installer/) | Debian · CLI · 包管理 |
| 2026-07-30 | [微软的安全AI不拼参数了：小模型编排打赢 GPT 5.4](https://freelamp.com/articles/2026-07-30_microsoft-multi-model-cyber-stack/) | AI · 网络安全 · 多模型编排 |
| 2026-07-26 | [CVE-2026-53921：DHCPv6 拿下 Root 权限](https://freelamp.com/articles/2026-07-26_dhcpv6-slaac-vuln/) | CVE · DHCPv6 · OpenWrt |

👉 [**查看全部文章 →**](https://freelamp.com)

---

## 🏗️ 仓库结构

```
lore/
├── articles/                    # Markdown 源文件（唯一事实源）
│   └── YYYY-MM-DD_slug/
│       ├── article.md           # 文章正文
│       └── metadata.yaml        # 元数据（标题、标签、SEO 描述）
├── docs/                        # GitHub Pages 静态站点（自动生成）
│   ├── index.html               # 文章列表首页
│   ├── sitemap.xml              # 搜索引擎站点地图
│   ├── robots.txt               # 爬虫规则
│   ├── llms.txt                 # LLM 语义索引（GEO 优化）
│   └── articles/
│       └── YYYY-MM-DD_slug/
│           └── index.html       # 文章页面（含 JSON-LD 结构化数据）
├── build.py                     # 静态站点构建脚本
├── llms.txt                     # LLM 语义索引源文件
└── README.md
```

## 📝 发布流程

```
写 Markdown → 提交到 articles/ → GitHub Actions 自动构建 → 发布到公众号 + GitHub Pages
```

构建命令（本地预览）：

```bash
pip install pyyaml
python build.py
# 生成的站点位于 docs/ 目录
```

## 🤖 LLM / AI 集成

本仓库提供 [`llms.txt`](https://freelamp.com/llms.txt) 语义索引文件，遵循 [llmstxt.org](https://llmstxt.org) 规范，方便 LLM 应用（ChatGPT、Perplexity、Claude 等）快速索引和引用本仓库的技术内容。

同时提供 RSS 订阅源：**[`rss.xml`](https://freelamp.com/rss.xml)**，配合浏览器 RSS 插件或阅读器即可订阅文章更新。

## 🏷️ 技术标签

`linux-kernel` · `tls` · `pki` · `devsecops` · `network-security` · `cve-analysis` · `sysadmin` · `infrastructure` · `ebpf` · `systemd` · `openssl` · `debian` · `ai-security`

---

## ✍️ 作者

**LeisureLinux** — 大智若愚，精通 Linux 底层架构。

- 📧 albertxu@freelamp.com
- 🐙 [GitHub](https://github.com/LeisureLinux)

---

*本文以 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 协议开源。*
