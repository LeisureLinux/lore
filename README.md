# 📜 LeisureLinux Lore

> 技术传说，记录于此。

LeisureLinux 的技术写作存档——公众号文章源文件 + GitHub Pages 博客。

## 📖 文章列表

| 日期 | 标题 | 标签 |
|------|------|------|
| 2026-08-01 | [一文讲透 Linux TLS 信任库](https://leisurelinux.github.io/lore/articles/2026-08-01_tls-trust-store/) | Linux · TLS · Java · 国密 |
| 2026-07-26 | [CVE-2026-53921：DHCPv6 拿下 Root](https://leisurelinux.github.io/lore/articles/2026-07-26_dhcpv6-slaac-vuln/) | CVE · DHCPv6 · SLAAC · OpenWrt |

## 🏗️ 仓库结构

```
lore/
├── articles/                    # Markdown 源文件（唯一事实源）
│   └── YYYY-MM-DD_slug/
│       ├── article.md           # 文章正文
│       └── metadata.yaml        # 元数据（标题、标签、发布时间）
├── docs/                        # GitHub Pages 静态站点
│   ├── index.html               # 文章列表首页
│   └── articles/
│       └── YYYY-MM-DD_slug/
│           └── index.html       # 文章页面
└── README.md
```

## 📝 发布流程

```
写 Markdown → 提交到 articles/ → GitHub Actions 自动构建 → 发布到公众号 + Pages
```

## ✍️ 作者

**LeisureLinux** — 大智若愚，精通 Linux 底层架构。

---

*本文以 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 协议开源。*
