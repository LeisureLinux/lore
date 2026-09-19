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
| 2026-09-19 | [一次打穿 OpenAI：libheif 堆溢出 + SSO 缺陷，72 小时接管员工账号](https://freelamp.com/articles/2026-09-19_hacktron-hacking-openai/) | 安全 · 漏洞 · OpenAI · SSO · libheif · ImageMagick · 堆溢出 · RCE · 供应链安全 · AI安全 |
| 2026-09-19 | [GNOME OS 默认开启 zswap 治 OOM，邮件客户端 Geary 的 GTK4 复刻 Convey 登陆 Flathub](https://freelamp.com/articles/2026-09-19_gnome-os-zswap-convey/) | GNOME · GNOME OS · zswap · OOM · systemd generator · Rust · Convey · Geary · GTK4 · Flathub · Linux桌面 |
| 2026-09-19 | [Neovim 有个 ~80 万美元的比特币捐款，从 2023 年躺到现在没动过](https://freelamp.com/articles/2026-09-19_neovim-untouched-bitcoin/) | 开源社区 · Neovim · 比特币 · 加密货币 · 密钥管理 · Shamir · 门限签名 · FROST · 开源治理 |
| 2026-09-18 | [systemd 那个绿色 [ OK ]，是怎么变成 logo 的](https://freelamp.com/articles/2026-09-18_systemd-brand-ok-logo/) | systemd · Linux init · 品牌 · 开源文化 · GNOME · CC BY-SA 4.0 |
| 2026-09-18 | [长鑫（CXMT）要在北京做 3D NAND：DRAM 一哥，开始踩 YMTC 的 NAND 地盘](https://freelamp.com/articles/2026-09-18_cxmt-3d-nand-rd-beijing/) | CXMT · 长鑫 · 3D NAND · YMTC · 长江存储 · 存储 · SSD · DRAM · 半导体 · 国产存储 |
| 2026-09-18 | [Wine 11.18 继续补全 NTOSKRNL：Windows 内核驱动在 Linux 上跑得越来越真](https://freelamp.com/articles/2026-09-18_wine-11.18-ntoskrnl/) | Wine · NTOSKRNL · 兼容层 · Windows · Linux · 内核驱动 · PnP · 游戏兼容 |
| 2026-09-18 | [Ubuntu 26.10 改主意了：内核从 7.2 跳到 7.3，十月前吃上最新主线](https://freelamp.com/articles/2026-09-18_ubuntu-2610-linux-73/) | Ubuntu · 26.10 · Linux 7.3 · 内核 · 发行版 · Canonical · 译文 |
| 2026-09-16 | [Nextcloud 推出 Euro-Office 桌面端：补齐对标微软 Office 的最后一环](https://freelamp.com/articles/2026-09-16_nextcloud-euro-office-desktop-app/) | Nextcloud · Euro-Office · 开源办公 · 主权软件 · OnlyOffice · OOXML · ODF · 协同办公 |
| 2026-09-16 | [RVA23 之后，RISC-V 往哪走：CFI、矩阵扩展与 RVA23.1](https://freelamp.com/articles/2026-09-16_riscv-after-rva23/) | RISC-V · 指令集 · CFI · 矩阵扩展 · 工具链 · Canonical |
| 2026-09-16 | [iocost 的七年之约：把 IO 成本模型交给 BPF](https://freelamp.com/articles/2026-09-16_blk-iocost-bpf-cost-model/) | Linux 内核 · BPF · struct_ops · iocost · cgroup · IO 调度 · 块层 |
| 2026-09-16 | [Fedora 45 Beta 发布：默认限制 ptrace、kmscon 换掉 fbcon、Anaconda 原生装 Stratis](https://freelamp.com/articles/2026-09-16_fedora-45-beta/) | Fedora · 发行版 · ptrace · kmscon · Stratis · 供应链安全 |
| 2026-09-16 | [一个月从零写出 GPU 驱动：LLM 逆出 Apple AGX，Minecraft 跑 200fps](https://freelamp.com/articles/2026-09-16_llm-written-gpu-driver-m4/) | GPU 驱动 · 逆向工程 · LLM · Apple Silicon · AGX · Mesa · 内核 · 译文 |
| 2026-09-16 | [Hugging Face 给 OpenAI 开了张发票：公开全部智能体轨迹，外加 1 亿美元算力](https://freelamp.com/articles/2026-09-16_huggingface-bills-openai-100m/) | AI 安全 · 智能体 · 沙箱逃逸 · Hugging Face · OpenAI · 执行轨迹 · 开源权重 · 事件响应 |
| 2026-09-14 | [GNU coreutils 9.12 发布：修了一个折磨人多年的 -R 竞态，uname 多了结构化输出](https://freelamp.com/articles/2026-09-14_gnu-coreutils-9.12/) | GNU · coreutils · 9.12 · uname · TOCTOU · 性能优化 · 系统运维 |
| 2026-09-14 | [Ubuntu 26.10 完成 coreutils 的 Rust 化：你天天敲的 ls/cp/rm 底层换引擎了](https://freelamp.com/articles/2026-09-14_ubuntu-2610-rust-coreutils/) | Ubuntu · 26.10 · Rust · coreutils · uutils · 内存安全 · TOCTOU · Canonical |
| 2026-09-14 | [Linux 7.4 内核构建或快 36%，增量构建快 70%：AI 找出瓶颈，人写的补丁](https://freelamp.com/articles/2026-09-14_linux-74-faster-builds/) | Linux · 7.4 · 内核构建 · 性能优化 · AI · kbuild · Rust 前端 |
| 2026-09-14 | [把 eBPF 安全代理的内核 CPU 开销砍掉 90%：靠的是记忆化，不是 AI](https://freelamp.com/articles/2026-09-14_ebpf-memoization-90-percent/) | eBPF · LSM · 性能优化 · 记忆化 · 内核缓存 · 硬链接 · 系统运维 |
| 2026-09-14 | [Oracle 新一轮裁员：6 点清晨邮件、28 亿美元重组，以及 13% 的年度失血](https://freelamp.com/articles/2026-09-14_oracle-layoffs-2-8b-restructuring/) | Oracle · 裁员 · 重组 · 28亿美元 · 科技行业 · AI投资 |
| 2026-09-14 | [GNU coreutils 9.7 全命令手册：105 个命令逐个拆解（附实机示例）](https://freelamp.com/articles/2026-09-14_gnu-coreutils-105-commands/) | GNU coreutils · Linux · Debian · trixie · CLI · man 手册 · shell · 运维 |
| 2026-09-08 | [dpkg 1.23.8 上手解析——半年一发的累积版本，进入 unstable](https://freelamp.com/articles/2026-09-08_dpkg-1.23.8-accepted-unstable/) | dpkg · Debian · unstable · Sid · 包管理 |
| 2026-09-08 | [Debian 13 "trixie" 13.7 Point Release 即将发布——9 月 12 日上线，上百项修复 + 90+ CVE 安全补丁](https://freelamp.com/articles/2026-09-08_debian-13-point-release-13.7-sua-286-1/) | Debian · trixie · Point Release · CVE |
| 2026-09-02 | [LWN 时隔近五年再次涨价：9 月 15 日生效，四档订阅平均上浮约 20%](https://freelamp.com/articles/2026-09-02_lwn-subscription-price-increase/) | LWN · 独立媒体 · 订阅制 · 通胀 · 爬虫对抗 |
| 2026-08-31 | [Debian 11 "bullseye" LTS 正式 EOL：今天之后没有安全更新了，老系统何去何从？](https://freelamp.com/articles/2026-08-31_debian-11-bullseye-lts-eol/) | Debian · LTS · EOL · 升级路径 · bookworm |
| 2026-08-26 | [LibreOffice 26.8 正式发布：206 位贡献者合力，重点死磕排版质量、复杂文字与文档交换](https://freelamp.com/articles/2026-08-26_libreoffice-26-8-release/) | LibreOffice · 排版器 · 双向文本 · OOXML · 零 AI |
| 2026-08-26 | [systemd 262-rc1 发布：嵌入兜底 unit、PID 1 静态容器、TPM/SEV-SNP/TDX 全栈机密计算加码](https://freelamp.com/articles/2026-08-26_systemd-262-rc1/) | systemd · PID 1 · NUMA · TPM · SEV-SNP · TDX · 机密计算 |
| 2026-08-08 | [OpenAI Astra 触发《准备度框架》"关键级"红线：被强按暂停键的下一代网络安全前沿模型](https://freelamp.com/articles/2026-08-08_openai-astra-critical-cyber/) | AI 安全 · Critical 阈值 · Daybreak · 漏洞利用链 |
| 2026-08-08 | [GRR：谷歌开源的远程取证与应急响应框架——Flow / Hunt / osquery 一篇讲清](https://freelamp.com/articles/2026-08-08_grr-rapid-response/) | 应急响应 · 取证 · osquery · 开源 |
| 2026-08-06 | [181 个 CVE 一起修：Debian LTS 的 Linux 5.10.262-1 更新，和它告诉我们的内核稳定性真相](https://freelamp.com/articles/2026-08-06_dla-4717-1-linux-kernel-5.10/) | CVE · Linux Kernel · LTS |
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

本仓库使用 GitHub Pages **legacy 模式**（source = `main` 分支的 `docs/` 目录）：
线上 [freelamp.com](https://freelamp.com) 内容**直接来自 main 分支的 `docs/` 产物**，
push 到 main 后由 GitHub 自动重建发布。

```bash
# 1) 写文章：articles/YYYY-MM-DD_slug/{article.md, metadata.yaml}
# 2) 本地生成静态站点（会清空并重建 docs/）
pip install pyyaml
python build.py
# 3) 提交产物并推送
git add docs/
git commit -m "publish: <文章标题>"
git push origin main      # GitHub 自动从 docs/ 重建 Pages
```

> ⚠️ 注意：
> - 只提交 `articles/*.md` 源文件**不会**上线，必须同时提交 `docs/` 产物。
> - `.github/workflows/deploy.yml` 里的 `actions/deploy-pages` 在 legacy 模式下不生效，仅用于校验构建是否报错。
> - 站点根目录静态文件（`jd_root.txt` / `googlec29651f57d804644.html` / `favicon.ico` 等）以仓库根为源，由 `build.py` 的 `static_files` 列表复制到 `docs/`。

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
