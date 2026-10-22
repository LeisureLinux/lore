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
| 2026-10-22 | [输入邮箱和密码，服务器自己找上来：给自建邮件域做一套 autoconfig](https://freelamp.com/articles/2026-10-22_mail-autoconfig-thunderbird-k9-zero-touch-setup/) | 邮件自动配置 · autoconfig · SRV 记录 · Thunderbird · K-9 Mail · Let's Encrypt · nginx · fail2ban · RFC 6186 · Cloudflare · Dovecot · 邮件服务器 |
| 2026-10-21 | [一个 LLM 网关的发布管道被攻破：攻击者用官方签名发出了一个专门偷你密钥的包](https://freelamp.com/articles/2026-10-21_litellm-1-107-0-supply-chain-compromise/) | LiteLLM · 供应链攻击 · PyPI · Docker · .pth · 凭证窃取 · 后门 · Trusted GitHub Publishers · GitHub CLI OAuth · Claude Code · 轮换凭证 · IoC |
| 2026-10-21 | [内核编译时间砍掉 36%：而这 21 个补丁的第一作者承认，AI 写的代码「大部分很难看」](https://freelamp.com/articles/2026-10-21_linux-7-4-kbuild-build-speedup-ai-assisted/) | Linux · Linux 7.4 · Kbuild · 内核编译 · 构建速度 · Lorenzo Stoakes · Arm · kallsyms · modpost · objtool · mksysmap · pigz · Rust · 增量构建 · Assisted-by |
| 2026-10-21 | [一年 48,185 个漏洞，而「全打补丁」是最糟的策略：LiteLLM 事件把答案摆在了桌面上](https://freelamp.com/articles/2026-10-21_patch-apocalypse-48k-cves-risk-prioritization/) | 补丁管理 · 漏洞管理 · CVSS · 风险优先级 · 供应链安全 · LiteLLM · php2shell · CVE · 利用窗口 · 资产清单 · KEV · 依赖清单 |
| 2026-10-21 | [补丁还没发布，攻击就已经开始了：一个在 PHP 里躺了二十年的缺陷，让你写的 Hello World 也能被一击拿下](https://freelamp.com/articles/2026-10-21_php2shell-cve-2026-109618-109619-root-cause-distro-patching/) | PHP · php2shell · CVE-2026-109618 · CVE-2026-109619 · longjmp · OOM · CWE-416 · UAF · mod_php · PHP-FPM · Wiz · Debian · Ubuntu · Red Hat · RHSA · DSA · USN · memory_limit · 缓解措施 |
| 2026-10-21 | [网络设备的底层用什么内核？国外厂商公开写 FreeBSD，而国内厂商大多只说「自研」](https://freelamp.com/articles/2026-10-21_network-appliance-underlying-os-bsd-linux-domestic/) | 网络设备 · 防火墙 · 底层内核 · FreeBSD · pfSense · OPNsense · IPSO · NetScaler · Junos · F5 TMOS · H3C Comware · 深信服 · 山石 StoneOS · 信创 |
| 2026-10-21 | [BSD 的代码流进了哪里：你以为它是小众，但它可能就在你的游戏机、路由器和 NAS 里](https://freelamp.com/articles/2026-10-21_bsd-code-in-proprietary-products/) | BSD · FreeBSD · macOS · XNU · Junos · NetApp ONTAP · Netflix Open Connect · PlayStation Orbis · Nintendo Switch · BSD 许可证 · 闭源 |
| 2026-10-21 | [Unix 为什么会分裂成两个阵营：而答案不在技术里，在 1956 年的一份反垄断同意令里](https://freelamp.com/articles/2026-10-21_unix-history-origins-system-v-bsd-split/) | Unix · 贝尔实验室 · AT&T · 同意令 · System V · BSD · TCP/IP · Unix 战争 · SCO · Novell · 版权诉讼 · 操作系统历史 |
| 2026-10-21 | [商业 Unix 只剩一个还在开发：HP-UX 刚刚断线，而它死于一枚停产的 CPU](https://freelamp.com/articles/2026-10-21_commercial-unix-2026-aix-hpux-solaris-status/) | Unix · AIX · HP-UX · Solaris · illumos · OpenIndiana · Xinuos · OpenServer · UnixWare · Xenix · Itanium · 生命周期 · EOL |
| 2026-10-21 | [BSD 家族全表：四个正统、一个桌面发行版，以及「UNIX 认证」这件事的真相](https://freelamp.com/articles/2026-10-21_bsd-family-2026-freebsd-openbsd-netbsd-ghostbsd/) | BSD · FreeBSD · OpenBSD · NetBSD · DragonFly · GhostBSD · macOS · pfSense · TrueNAS · UNIX 认证 · 浪潮 K-UX · 华为 EulerOS |
| 2026-10-21 | [PingCAP 被窃 10.6 TB：而真正的问题不是「数据被拿走」，是「凭证就写在自家的仓库和自己的工单里」](https://freelamp.com/articles/2026-10-21_pingcap-tidb-cloud-breach-fulcrumsec/) | PingCAP · TiDB Cloud · FulcrumSec · 数据泄露 · 供应链安全 · 硬编码密钥 · 多租户隔离 · Jira 工单 · 明文 API Key · 事件响应 · 解读 |
| 2026-10-20 | [Omarchy 4.5-RC1 开始支持 aarch64：而这次真正的进展不是「多了一个架构」，是三个完全不同来源的 ARM 笔记本同时跑起来了](https://freelamp.com/articles/2026-10-20_omarchy-4-5-rc1-aarch64-snapdragon-n1x/) | Omarchy · Arch Linux ARM · aarch64 · Snapdragon X · NVIDIA N1X · Apple Silicon · Hyprland · 解读 |
| 2026-10-20 | [加密 DNS 确实比 VPN 划算：但它藏住的是「你查了哪个域名」，不是「你连了哪个 IP」](https://freelamp.com/articles/2026-10-20_encrypted-dns-providers-adguard-controld/) | 加密DNS · DoH · DoT · DoQ · DNSCrypt · AdGuard DNS · Control D · Windscribe · SNI · ECH · EDNS Client Subnet · 解读 |
| 2026-10-20 | [Omarchy 4.5-RC1 开始支持 aarch64：而这次真正的进展不是「多了一个架构」，是三个完全不同来源的 ARM 笔记本同时跑起来了](https://freelamp.com/articles/2026-10-20_omarchy-4-5-rc1-aarch64-snapdragon-n1x/) | Omarchy · Arch Linux ARM · aarch64 · Snapdragon X · NVIDIA N1X · Apple Silicon · Hyprland · Limine · 每显示器工作区 · 国际化 · 解读 |
| 2026-10-20 | [PwnEscape 的补丁已经发了，而真正的教训是：KVM 逃逸出来的地方，不是 hypervisor，是主机内核的最低层](https://freelamp.com/articles/2026-10-20_pwnescape-kvm-escape-broader-attack-surface/) | PwnEscape · CVE-2026-99999 · KVM · VM 逃逸 · OpenShift · AWS · Januscape · Edera · 虚拟化隔离 · AI agent · 解读 |
| 2026-10-20 | [nginx 三个 9.2 分漏洞：而真正决定你危不危险的，不是版本号，是你的配置文件里有没有那几个组合](https://freelamp.com/articles/2026-10-20_nginx-three-critical-flaws-config-dependent/) | nginx · F5 · CVE-2026-15176 · CVE-2026-97205 · CVE-2026-93479 · CVSS 9.2 · UAF · 配置审计 · ASLR · AIO · SSI · map · 应急补丁 · 解读 |
| 2026-10-20 | [三百万张显卡的订单，英伟达只能交付 5%：而 84GB 显存的那张卡为什么成了唯一的出口](https://freelamp.com/articles/2026-10-20_rtx-pro-5500-china-orders-export-compliant/) | Nvidia · RTX Pro 5500 · 出口管制 · B300 · H200 · RTX 6000D · 字节跳动 · 阿里巴巴 · 腾讯 · 推理 · 显存 · Rubin · 供应链 · 解读 |
| 2026-10-20 | [PHP 明天要发两个 CVSS 9.2 的漏洞补丁：而这次真正的问题不是「有多严重」，是「你根本不知道你跑的是什么版本」](https://freelamp.com/articles/2026-10-20_php-critical-security-release-oct-21-2026/) | PHP · 安全更新 · CVE-2026-109618 · CVE-2026-109619 · CVSS 9.2 · RCE · PHP Foundation · 补丁日 · 生命周期 · EOL · 提前公告 · 解读 |
| 2026-10-20 | [OpenBSD 8.0 发了：而这次最值得看的不是漏洞修复清单，是内核虚拟地址空间从 4G 跳到 512G](https://freelamp.com/articles/2026-10-20_openbsd-8-0-release-kernel-address-space/) | OpenBSD · 内核地址空间 · pmap · DRM · Linux 6.18.53 · Intel Arc · OpenSSH 10.6 · LibreSSL 4.4.0 · pledge · unveil · arm64 休眠 · loongson 退役 · 发布解读 |
| 2026-10-20 | [Magento 六周内第二个满分漏洞：而真正的分水岭不在 CVSS 10.0，在「Adobe 的 priority 1 只留给正在被打的洞」](https://freelamp.com/articles/2026-10-20_magento-blockstrap-cve-2026-103849-priority-2/) | Magento · Adobe Commerce · BlockStrap · CVE-2026-103849 · StyleSmuggler · CVSS 10.0 · RCE · 模板注入 · 补丁优先级 · Mage-OS · AI辅助逆向 · 解读 |
| 2026-10-20 | [Secure Boot 证书到期：真正的问题不是「证书过期」，而是「更新信任的钥匙，锁在被更新的那把锁里」](https://freelamp.com/articles/2026-10-20_secure-boot-certificate-expiration-2026-kek-gating/) | Secure Boot · UEFI · 证书到期 · KEK · db · dbx · PK · Windows UEFI CA 2023 · shim · BitLocker · PCR7 · CVE-2026-8863 · 解读 |
| 2026-10-19 | [ACPI 覆盖到底怎么做：从作者的仓库里拆出完整流程，以及哪些部分能迁移到你自己的笔记本](https://freelamp.com/articles/2026-10-19_acpi-table-override-guide-initrd-cpio/) | ACPI · DSDT · SSDT · 覆盖 · initrd · cpio · acpiview · iasl · ACPICA · AML · _OSI · EFI描述符 · memblock · 笔记本 · 技术指南 |
| 2026-10-19 | [为了让这台 128GB 的 RTX Spark 笔记本跑 Linux，她自己写了 ACPI 覆盖和触控板补丁](https://freelamp.com/articles/2026-10-19_rtx-spark-laptop-arch-linux-arm-nvidia/) | RTX Spark · NVIDIA · N1X · Grace CPU · Arch Linux ARM · aarch64 · 统一内存 · CUDA · vLLM · 7-Zip · ACPI override · 本地推理 · 解读 |
| 2026-10-19 | [二十五年的「NSA 后门」疑云解开了：而答案是一个 Unix 时间戳加上一个 1990 年代的随机数生成器](https://freelamp.com/articles/2026-10-19_nist-ecdsa-curve-seeds-lrand48-timestamp/) | ECDSA · 椭圆曲线 · NIST · lrand48 · P-256 · 种子 · Claude · LLL算法 · FreeLIP · Jerry Solinas · 密码学 · 解读 |
| 2026-10-19 | [Gentoo 给 Chromium 做了「临终祷告」：而杀死这个打包的是一句「这太荒唐了」](https://freelamp.com/articles/2026-10-19_gentoo-chromium-last-rites-maintainer-burnout/) | Gentoo · Chromium · 打包 · ebuild · 维护者倦怠 · LWN · Sam James · 开源治理 · 浏览器 · USE标签 · 解读 |
| 2026-10-19 | [同一个活，两种引擎：一个 100GB 的教训，把 OLTP 换成 lakehouse 到底换掉了什么](https://freelamp.com/articles/2026-10-19_innodb-vs-iceberg-olap-migration-internals/) | InnoDB · Iceberg · OLTP · OLAP · lakehouse · MySQL · Spark · Polaris · Parquet · MVCC · 列式存储 · 数据建模 · 解读 |
| 2026-10-19 | [想下载一个 ISO，最后写了个内核漏洞利用程序：而他只需要往两个 sysfs 文件里写两个零](https://freelamp.com/articles/2026-10-19_tplink-eap770-dma-cache-bug-kernel-exploit/) | TP-Link · EAP770 · 高通 · IPQ9574 · DMA · 缓存一致性 · SFE · PPE · CVE-2022-0185 · modprobe_path · 内核利用 · 闭源固件 · 解读 |
| 2026-10-19 | [TEE 的漏洞清单已经长得能写进一篇博客：而作者最狠的一句是「打断一台等于打断全部」](https://freelamp.com/articles/2026-10-19_tee-attestation-forgery-threat-model/) | TEE · SGX · TDX · SEV-SNP · Nitro · 远程证明 · PCK · 侧信道 · 物理攻击 · TEE.fail · WireTap · BadRAM · 机密计算 · 威胁模型 · 解读 |
| 2026-10-19 | [机器凭据轮换只是买时间：ZSP 的关键不在「换密码」，在「有没有人负责关掉它」](https://freelamp.com/articles/2026-10-19_zero-standing-privilege-machine-identities/) | 零常驻特权 · ZSP · 机器身份 · NHI · OAuth · 令牌重放 · Salesloft Drift · UNC6395 · PAM · 工作负载身份联合 · OIDC · DPoP · 评论解读 |
| 2026-10-19 | [PwnEscape：一个 17 年的内核 bug，AI 用 3 天找到，而修复只堵了 5 个消费点](https://freelamp.com/articles/2026-10-19_pwnescape-cve-2026-99999-linux-networking-vm-escape/) | PwnEscape · CVE-2026-99999 · Linux内核 · 虚拟机逃逸 · KVM · Vercel Sandbox · 校验和卸载 · sk_buff · TOCTOU · AI辅助研究 · 解读 |
| 2026-10-19 | [「Flatpak 是一团安全噩梦」：原文写于 2023 年，而 2026 年的两个证据它都没等到](https://freelamp.com/articles/2026-10-19_flatpak-sandbox-security-debate-flatkill-rebuttal/) | Flatpak · 沙箱安全 · flatkill · Flathub · Portals · 静态权限 · CVE-2026-34078 · 桌面Linux · 应用分发 · 解读 |
| 2026-10-19 | [Linux 7.3 是一个「全方位纪录」：两万多个提交、三千多名开发者，而 Phoronix 特意提到了 AI 带来的代码变动](https://freelamp.com/articles/2026-10-19_linux-7-3-release-record-commits-ai-churn/) | Linux内核 · 7.3 · LWN · Phoronix · AI/LLM · 提交量 · sched_ext · failfs · 译文 |
| 2026-10-19 | [为了省下 62 毫秒，Omarchy 用 Claude Code 重写了一个 XDG 脚本：这个数字比它看起来重要](https://freelamp.com/articles/2026-10-19_omarchy-browser-launch-xdg-optimization/) | Omarchy · Arch Linux · Hyprland · DHH · Claude Code · xdg-settings · 微优化 · 译文 |
| 2026-10-19 | [闰秒要在 2027 年 5 月 20 日退役了：而 Linux 已经为此准备了十四年](https://freelamp.com/articles/2026-10-19_leap-second-retired-2027-linux-clocks/) | 闰秒 · BIPM · CGPM · UTC · TAI · CLOCK_TAI · NTP · chrony · smearing · 译文 |
| 2026-10-18 | [从「能免费在车里唱歌」出发，我为什么会撞上三种歌词格式](https://freelamp.com/articles/2026-10-18_lrc-ttml-karaoke-formats/) | LRC · LRC A2 · Enhanced LRC · TTML · TTML2 · DFXP · W3C · 歌词格式 · 卡拉OK · 逐词歌词 · SPL · YRC · QRC · KRC · 私有格式 · 加密 · LRCLIB · Musixmatch · Gramophone · Steve · CarPlay · Android Auto · 免费软件 |
| 2026-10-17 | [GNOME 这个 AI 聊天应用最值得看的不是功能，而是它把「哪些数据会出去」写成了可核对的句子](https://freelamp.com/articles/2026-10-17_moose-0-6-gnome-ai-chat-privacy/) | Moose · GNOME · GTK4 · Rust · Ollama · 本地AI · Local-Only · keyring · 隐私设计 · 译文 |
| 2026-10-16 | [不到两周，X.Org 又发了 17 个 CVE：而这一次全在客户端库里，威胁模型反过来了](https://freelamp.com/articles/2026-10-16_xorg-17-cves-client-libraries/) | X.Org · libX11 · libXi · libXrender · CVE · XIM · XKB · 威胁模型 · XWayland · 越界读写 · 译文 |
| 2026-10-16 | [Starling 又用 Claude 写出了一个办公套件：而它和同一周那批 AI 政策，正好指向相反的方向](https://freelamp.com/articles/2026-10-16_starling-office-ai-generated-suite/) | Starling · Swift · Wayland · 办公套件 · Claude Code · Apache-2.0 · Flutter · OOXML · 开源治理 · 译文 |
| 2026-10-16 | [MIPS 与龙芯的三十年：一家公司放弃了自己的指令集，而一家中国公司在那一年离开了它](https://freelamp.com/articles/2026-10-16_mips-loongson-loongarch-history/) | MIPS · 龙芯 · LoongArch · LoongISA · 芯联芯 · RISC-V · 自主可控 · 仲裁 · 编译生态 |
| 2026-10-16 | [Libreboot 26.10 把「反 AI 政策」列为本次发布最重要的变更，然后才是完整 UEFI 支持](https://freelamp.com/articles/2026-10-16_libreboot-2610-uefi-edk2-anti-ai-policy/) | Libreboot · coreboot · EDK2 · UEFI · Chromebook · AGENTS.md · 反AI政策 · 自由固件 · 译文 |
| 2026-10-16 | [当补丁变得廉价，开源协作的两种新答案：一个说「关掉 PR」，一个说「Rust 更适合」](https://freelamp.com/articles/2026-10-16_remix-model-vs-agentic-rust/) | 开源治理 · remix · Nix · Rust · agentic coding · 类型系统 · 证明系统 · Verus · 译文 |
| 2026-10-16 | [Windows 桌面测试为什么难自动化：因为一个容器里没有登录会话，而人得先登进去](https://freelamp.com/articles/2026-10-16_windows-desktop-automation-disposable-vms/) | QA Wolf · Windows · UI Automation · Appium · WebRTC · GCE · Kubernetes · VM · 测试基础设施 · 译文 |
| 2026-10-16 | [Timescale 把向量索引做进了 PostgreSQL 的 C 内核里](https://freelamp.com/articles/2026-10-16_pg-vectorsearch-prism-index-timescale/) | PostgreSQL · pgvector · 向量搜索 · PRISM · RaBitQ · HNSW · Timescale · 索引 · SIMD · 译文 |
| 2026-10-16 | [三十五年后重读《Why I Wrote PGP》：它讲的不是加密，而是「一次变更由谁发起」](https://freelamp.com/articles/2026-10-16_why-i-wrote-pgp-revisited/) | PGP · Phil Zimmermann · 加密 · 隐私 · 密码战争 · Senate Bill 266 · Clipper · CALEA · 译文 |
| 2026-10-16 | [RPKI 覆盖涨到 70%，而它没能拦住的恰恰是一次真实劫持：因为那次攻击是「RPKI 有效」的](https://freelamp.com/articles/2026-10-16_rpki-70-percent-coverage-hetzner-hijack/) | RPKI · ROA · BGP · 路由劫持 · maxLength · RFC 9319 · ASPA · Hetzner · Virtualizor · 译文 |
| 2026-10-16 | [自托管 28 个服务的清单，与一个 €25 买断的文档工具：它们在做同一个选择](https://freelamp.com/articles/2026-10-16_self-hosting-list-and-buyout-local-tools/) | 自托管 · Jellyfin · Immich · Podman · 本地优先 · BYOK · MarkItDown · 迷你主机 · 译文 |
| 2026-10-16 | [同一份 AdFection 报告，这篇多给了企业一份可执行清单：而清单里最有效的一条，是「别把你的广告 ID 交出去」](https://freelamp.com/articles/2026-10-16_adfection-enterprise-defense-checklist/) | AdFection · 广告标识符 · MDM · DNS拦截 · 企业安全 · Frank Dickson · 零点击 · 译文 |
| 2026-10-16 | [systemd v262 那 35 条改动，真正的主线是把「启动信任」变成一条可以逐段签名的链](https://freelamp.com/articles/2026-10-16_systemd-v262-trust-chain-varlink/) | systemd · 可信启动 · TPM · NvPCR · UKI · dm-verity · Varlink · 机密计算 · 译文 |
| 2026-10-16 | [Ubuntu 26.10 用 Sequoia 换掉 GnuPG 签名：发行版第一次把「量子威胁」写进了自己的包管理器](https://freelamp.com/articles/2026-10-16_ubuntu-26-10-stonking-stingray/) | Ubuntu · Sequoia PGP · 后量子 · APT · GNOME 51 · dbus-broker · TPM · RISC-V · 译文 |
| 2026-10-16 | [用 AI 逆向工程硬件驱动：Red Hat 工程师把一台扫描仪和一个摄像头修好了](https://freelamp.com/articles/2026-10-16_ai-reverse-engineer-linux-hardware-drivers/) | AI · Claude Code · 逆向工程 · 驱动开发 · hw-harness · usbmon · SANE · libcamera · 译文 |
| 2026-10-16 | [两个「隐含假设」的修正：CPU boost 该不该默认开，复用缓冲区能不能只拷最新那帧](https://freelamp.com/articles/2026-10-16_cppc-boost-default-mutter-damage-tracking/) | ACPI · CPPC · cpufreq · Mutter · 多GPU · damage tracking · Wayland · 译文 |
| 2026-10-16 | [微软把 Defender 装到了 Linux 桌面上：它卖的不是杀毒，而是「别让开发机成为可见性盲区」](https://freelamp.com/articles/2026-10-16_microsoft-defender-linux-desktop-preview/) | Microsoft · Defender · Linux桌面 · EDR · 开发机 · 企业安全 · 可见性 · 译文 |
| 2026-10-15 | [广告不是图片，是可执行代码：AdFection 用「先验身份、再发载荷」把实时竞价变成了一条零点击投毒通道](https://freelamp.com/articles/2026-10-15_adfection-zero-click-spyware-targeted-ads/) | AdFection · Citizen Lab · 零点击 · 间谍软件 · 恶意广告 · RTB · NOAS · ADINT · 供应链安全 · 译文 |
| 2026-10-15 | [无头浏览器做微信视频号自动化：最坑的不是「无头」，是一个屏幕尺寸参数](https://freelamp.com/articles/2026-10-15_headless-wechat-channels-automation/) | BrowserSkill · bsk · 浏览器自动化 · 无头浏览器 · headless Chromium · CDP · Chrome 扩展 · wujie · shadow DOM · Vue · 微前端 · Ozone · 微信视频号 · 扫码登录 · 故障排查 · 运维 · 原创 |
| 2026-10-15 | [同一周里，四个开源项目对 AI 贡献给出了四种答案：分歧不在技术，而在「声明」到底有什么用](https://freelamp.com/articles/2026-10-15_open-source-ai-contribution-policies-compared/) | GCC · Linux内核 · Debian · Flathub · LLVM · AI治理 · 开源治理 · Assisted-by · DCO · 译文 |
| 2026-10-15 | [KDE 选在自己 30 岁生日当天退役 X11：这不是告别，而是一次刻意的对齐](https://freelamp.com/articles/2026-10-15_kde-plasma-6-8-x11-retirement/) | KDE · Plasma · Wayland · X11 · 桌面环境 · 无障碍 · Union · HDR · 译文 |
| 2026-10-15 | [GNU Boot 加入 FSF 财政赞助：这一步解决的是「谁替你收钱」，但没解决「我的笔记本能不能用」](https://freelamp.com/articles/2026-10-15_gnu-boot-fsf-fiscal-sponsorship/) | GNU Boot · FSF · Libreboot · coreboot · 固件 · 自由软件 · 财政赞助 · 可复现构建 · 译文 |
| 2026-10-15 | [Cloud Hypervisor 54 承诺「前两个版本可迁移」：把一条口头保证变成了可执行的承诺](https://freelamp.com/articles/2026-10-15_cloud-hypervisor-54-live-migration/) | Cloud Hypervisor · 虚拟化 · VMM · Rust · 热迁移 · VFIO · SEV-SNP · ARM SMMUv3 · 译文 |
| 2026-10-15 | [RISC-V 最尴尬的一个问题终于要解决了：怎么知道「我这台机器符不符合 RVA23」](https://freelamp.com/articles/2026-10-15_riscv-rva23-hwprobe-detection/) | RISC-V · RVA23 · hwprobe · Linux内核 · glibc · 二进制分发 · 发行版 · LPC · 译文 |
| 2026-10-15 | [红帽的两篇新文章，讲的其实是同一件事：当 AI 让「发现漏洞」变便宜之后](https://freelamp.com/articles/2026-10-15_red-hat-lightwell-backport-netops-as-code/) | Red Hat · Lightwell · IBM · Ansible · 回移补丁 · 供应链安全 · SBOM · VEX · 自动化 · 译文 |
| 2026-10-15 | [Nothing OS 5 开始推送：真正该看的不是「我能升级吗」，而是「大版本和补丁是两条时间线」](https://freelamp.com/articles/2026-10-15_nothing-os-5-android-17-rollout/) | Nothing · CMF · Android 17 · 固件更新 · 安全补丁 · 支持周期 · 企业移动管理 · 译文 |
| 2026-10-14 | [Firefox 要进企业市场，但它的赌注押在一个不确定的假设上：欧洲真的会为「不依赖美国」付钱](https://freelamp.com/articles/2026-10-14_firefox-enterprise-digital-sovereignty/) | Mozilla · Firefox · 企业浏览器 · 数字主权 · Gecko · Chromium · DORA · NIS2 · AI治理 · 商业模式 · 译文 |
| 2026-10-14 | [NPU 终于能用 PyTorch 跑了：Mesa 接下这件事，靠的是一条被 AI 加速行业忽略的捷径](https://freelamp.com/articles/2026-10-14_mesa-torx-yolox-pytorch-npu/) | Mesa · NPU · Torx · ExecuTorch · PyTorch · Gallium · NIR · Ethos-U · Etnaviv · Rocket · 边缘AI · 开源驱动 · 译文 |
| 2026-10-13 | [npm 拿「名字」而不是「ID」验证发布者：SlugFest 让 1500 个包的发布权可以被继承](https://freelamp.com/articles/2026-10-13_npm-trusted-publishing-slugfest/) | npm · 供应链安全 · Trusted Publishing · OIDC · 开源治理 · AI代理 · 依赖管理 · provenance · 译文 |
| 2026-10-13 | [Asterinas 0.19：用 Rust 重构内核的另一种思路，是「不减少地址空间，只减少 unsafe」](https://freelamp.com/articles/2026-10-13_asterinas-0-19-framekernel/) | Asterinas · Rust · 操作系统 · 内核 · framekernel · 微内核 · 内存安全 · OSTD · DRM · AArch64 · Kata Containers · hypervisor · 译文 |
| 2026-10-14 | [内网域名没有一个是安全的：.lan / .local / .home / .corp 的真实状态，以及 ICANN 给出的 .internal](https://freelamp.com/articles/2026-10-14_internal-tld-name-collision/) | DNS · 内网命名 · 名字碰撞 · ICANN · IANA · home.arpa · .internal · mDNS · Active Directory · 安全加固 · 原创 |
| 2026-10-12 | [Linus 用 Claude Code 改内核：这份 commit message 比那个性能数字更值得读](https://freelamp.com/articles/2026-10-12_linus-torvalds-claude-code-kernel/) | Linux内核 · Linus Torvalds · Claude Code · AI辅助开发 · folio · 页缓存 · RCU · 内存管理 · 译文 |
| 2026-10-12 | [Ubuntu 的本地语音输入 Myna 进技术预览：它明确说「这不是语音助手」](https://freelamp.com/articles/2026-10-12_ubuntu-myna-speech-to-text-preview/) | Ubuntu · Myna · 语音识别 · Whisper · Parakeet · FunASR · 本地推理 · 隐私 · IBus · Snap · 原创 |
| 2026-10-12 | [红帽的混沌工程复盘：四个客户案例里，我最在意的是「保存实验」这一条](https://freelamp.com/articles/2026-10-12_red-hat-chaos-engineering-lessons/) | 混沌工程 · Krkn · OpenShift · SLO · SLA · GameDay · 韧性 · 数据完整性 · 虚拟化 · 运维 · 译文 |
| 2026-10-12 | [Intel 让 SGX 在 Diamond Rapids 之后退场：这不是失败，是「边界选错了」](https://freelamp.com/articles/2026-10-12_intel-sgx-phaseout-tdx-pivot/) | Intel · SGX · TDX · 机密计算 · Trusted I/O · TDX Connect · 后量子密码 · TEE · 虚拟化 · 译文 |
| 2026-10-12 | [数据中心挨打这件事，现在能在互联网测量数据里读出来](https://freelamp.com/articles/2026-10-12_yandex-data-centers-bot-traffic-collapse/) | Yandex · 数据中心 · Cloudflare · NetBlocks · 互联网测量 · 基础设施韧性 · 单点故障 · 译文 |
| 2026-10-11 | [解锁 Bootloader 不等于 Root：Android 刷机链的每一层到底在解什么锁](https://freelamp.com/articles/2026-10-11_android-bootloader-unlock-root-chain/) | Android · Bootloader · Root · Magisk · KernelSU · APatch · AVB · dm-verity · Play Integrity · Widevine · TEE · LineageOS · 系统安全 · 原创 |
| 2026-10-11 | [用 Claude 造 Office 替代品：ROADMAP 自己写着完成度约 50%，而仓库里的 CLAUDE.md 才是重点](https://freelamp.com/articles/2026-10-11_artcraft-office-clones-claude/) | ArtCraft · GridCraft · WordCraft · DeckCraft · Claude · AI辅助开发 · clean-room · Rust · OOXML · LibreOffice · MCP · 开源许可 · 原创 |
| 2026-10-11 | [LineageOS 24 一次把 174 个设备搬上 Android 17：而它同时宣布了一条硬底线](https://freelamp.com/articles/2026-10-11_lineageos-24-changelog-32/) | LineageOS · Android 17 · 第三方 ROM · WebUSB · eBPF · 内核 · 设备支持 · AOSP · 可维修性 · 译文 |
| 2026-10-11 | [「很难」是过去时：一个人 8 天写出微内核操作系统，以及为什么 unikernel 又回来了](https://freelamp.com/articles/2026-10-11_unikernels-veda-agentic-os/) | unikernel · Veda · 微内核 · Rust · 操作系统 · AI辅助开发 · agentic OS · MirageOS · seL4 · 攻击面 · 设计债 · 译文 |
| 2026-10-10 | [LTS 在 AI 时代过时了？补丁洪流是真的，但「改用滚动发布」是个假二选一](https://freelamp.com/articles/2026-10-10_lts-vs-rolling-release-genai/) | Linux · LTS · 滚动发布 · GenAI · 补丁洪流 · Linux内核 · 网络子系统 · LPC2026 · AI slop · 嵌入式 · 译文 |
| 2026-10-09 | [SQLite 3.54 终于放弃 Windows XP：一个数据库引擎的兼容性债，还了二十多年](https://freelamp.com/articles/2026-10-09_sqlite-3-54-released/) | SQLite · 嵌入式数据库 · Windows XP · SRWL · 性能优化 · 查询计划器 · O_TMPFILE · 兼容性债 · 译文 |
| 2026-10-09 | [三条来自 LWN 的时间线：Python 3.15、Let's Encrypt 的 64 天证书、systemd 的自我交代](https://freelamp.com/articles/2026-10-09_lwn-python-315-letsencrypt-systemd/) | Python · Python 3.15 · Let's Encrypt · 证书生命周期 · ACME · ARI · systemd · All Systems Go · JIT · 运维 · 译文 |
| 2026-10-09 | [骁龙笔记本的 AI PC 叙事，在 Linux 上还缺最关键的那一环](https://freelamp.com/articles/2026-10-09_snapdragon-linux-npu-ai-pc/) | Qualcomm · Snapdragon X2 · Linux · NPU · Hexagon · AI PC · fastRPC · QNN · OpenVINO · 端侧AI · 译文 |
| 2026-10-09 | [Windows Update 换证书：Win7 早就没补丁了，Win10 却还有个到 2027 年 10 月的活口](https://freelamp.com/articles/2026-10-09_windows-update-certificate-rotation-2027/) | Windows Update · 证书轮换 · Windows 7 · Windows 10 · ESU · 生命周期 · Secure Boot · 0patch · Linux 迁移 · 运维 · 译文 |
| 2026-10-09 | [Deno 团队加入 Cloudflare：runtime 一年后停更，Deploy 六个月后关停](https://freelamp.com/articles/2026-10-09_deno-joins-cloudflare/) | Deno · Cloudflare · Workers · Durable Objects · celld · workerd · Ryan Dahl · Kenton Varda · 开源可持续性 · 供应商锁定 · 译文 |
| 2026-10-09 | [Snapdragon X 笔记本的 Linux HDR 支持来了：静态 HDR10，补丁是 LLM 辅助写的](https://freelamp.com/articles/2026-10-09_qualcomm-msm-drm-hdr/) | Qualcomm · Snapdragon X · MSM驱动 · HDR · HDR10 · BT.2020 · DisplayPort · eDP · ARM笔记本 · 译文 |
| 2026-10-09 | [ext4 弃用 data=journal：最「安全」的那个挂载模式，2028 年要走了](https://freelamp.com/articles/2026-10-09_ext4-deprecates-data-journal/) | ext4 · 文件系统 · data=journal · 日志 · 数据完整性 · O_DIRECT · 延迟分配 · 运维 · 译文 |
| 2026-10-09 | [Linux swap 子系统要删掉那张「交换映射表」：省下的是 1TB 交换文件里的 256MB](https://freelamp.com/articles/2026-10-09_linux-swap-table-removing-swap-map/) | Linux内核 · swap · 内存管理 · swap table · folio · zram · 内核补丁 · 译文 |
| 2026-10-09 | [Google 开放 SynthID 检测器：它的价值不在「能不能识破 AI」，而在「阳性意味着什么」](https://freelamp.com/articles/2026-10-09_google-synthid-detector-public/) | SynthID · AI水印 · 内容溯源 · C2PA · 合成内容检测 · 数字取证 · 原创 |
| 2026-10-09 | [Rembrandt：10 天做出一个 Lightroom 替代品，而它的 README 自己交代了原型来自 darktable](https://freelamp.com/articles/2026-10-09_rembrandt-photo-editor-github/) | Rembrandt · 照片编辑 · Lightroom · darktable · RAW · GPL · AI生成代码 · WebGPU · 原创 |
| 2026-10-09 | [「Linux 桌面永远成功不了」这句话，2026 年该改口了：但作者抱怨的那些事是真的](https://freelamp.com/articles/2026-10-09_linux-desktop-not-expecting-experts/) | Linux桌面 · 可用性 · GNOME · KDE Plasma · 分数缩放 · Statcounter · Steam Deck · 原创 |
| 2026-10-09 | [「我们可能会失去公钥密码学」：Green 那条推文背后到底在说什么](https://freelamp.com/articles/2026-10-09_green-public-key-cryptography-ai/) | 密码学 · 公钥加密 · 后量子密码 · MLWE · ECDLP · AI密码分析 · HAWK · 译文 |
| 2026-10-09 | [452 倍是真的，但它在等一块还不存在的内存条：Meta 的 CRAM 提案](https://freelamp.com/articles/2026-10-09_meta-cram-compressed-ram/) | CRAM · 内存压缩 · zram · zswap · NUMA · Meta · Linux内核 · LPC2026 · CXL · 缺页异常 · 页表 · 内存层级 · 译文 |
| 2026-10-09 | [Cloudflare 让 1.1.1.1 免于罚款：赢在程序，而 Quad9 可能因为同一个理由退出法国](https://freelamp.com/articles/2026-10-09_cloudflare-1111-france-piracy-blocking/) | Cloudflare · 1.1.1.1 · Quad9 · DNS · 域名封禁 · 版权执法 · ARCOM · Canal+ · UPC Telekabel · 欧盟DSA · 译文 |
| 2026-10-09 | [一个散热器页面泄露的 EPYC Verano：72 核不难，24 通道 LPDDR5X 才是真信号](https://freelamp.com/articles/2026-10-09_epyc-verano-sb1-lpddr5x/) | AMD · EPYC · Verano · Zen 6 · Venice · SB1 · SOCAMM2 · LPDDR5X · JEDEC · 服务器CPU · AI主机 · 内存带宽 · 译文 |
| 2026-10-09 | [54% 掉到 22%：抗量子准备度这个指标，量错了层](https://freelamp.com/articles/2026-10-09_pqc-edge-quantum-readiness/) | 后量子密码学 · PQC · 量子安全 · TLS 1.3 · CDN · Cloudflare · 证书管理 · CBOM · NIST · PKI · 译文 |
| 2026-10-09 | [ICANN 收到 1,615 份新顶级域申请和约 3.67 亿美元：但 55% 的申请注定撞在别人身上](https://freelamp.com/articles/2026-10-09_icann-2026-new-gtld-round/) | ICANN · gTLD · 新顶级域 · DNS · 域名圈地 · AI域名 · agent · agi · Anguilla · 互联网治理 · 译文 |
| 2026-10-09 | [Quick Share 什么都好，除了它没有 Linux 客户端：手机与 PC 互传的四种走法](https://freelamp.com/articles/2026-10-09_quickshare-linux-android-file-transfer/) | Quick Share · Nearby Share · 文件传输 · Android · Linux · Packet · rquickshare · LocalSend · KDE Connect · Wi-Fi Direct · 互传联盟 · AirDrop |
| 2026-10-09 | [微软把「跑不可信代码」做成了一个 SDK 依赖：九个沙箱后端与一份说清边界的文档](https://freelamp.com/articles/2026-10-09_microsoft-mxc-sandbox-sdk/) | Microsoft · MXC · 沙箱 · 代码执行隔离 · Bubblewrap · Seatbelt · AppContainer · WFP · MicroVM · Nanvix · Hyperlight · Windows Sandbox · 供应链安全 · 译文 |
| 2026-10-09 | [钓鱼防御打错了层级：域名封不过来，但服务器藏不住](https://freelamp.com/articles/2026-10-09_phishing-server-layer-aitm/) | 钓鱼 · AiTM · 会话劫持 · MFA · Microsoft 365 · 威胁狩猎 · 域名劫持 · CAA · 证书透明度 · Chrome · 译文 |
| 2026-10-08 | [一支 AI 代理「机群」被追踪到抓取高德地图：但「署名 claude」暴露了归因的脆弱](https://freelamp.com/articles/ai-agent-fleet-amap-tencent/) | AI代理 · Agent安全 · 高德地图 · 腾讯 · 混元 · Claude · 模型归因 · 抓取 · 开源情报 · 产业分析 |
| 2026-10-08 | [Anthropic 给安全团队开了「降低护栏」的口子：三层访问与一份厂商自测数据](https://freelamp.com/articles/anthropic-cyber-verification-program/) | Anthropic · Claude · AI安全 · 红队 · CVP · Glasswing · 护栏 · 代理治理 · 译文 |
| 2026-10-08 | [Gartner 新增的 ISOC 类别：定义本身没问题，但解读它的人可能卖的就是它](https://freelamp.com/articles/gartner-isoc-category/) | Gartner · ISOC · SIEM · SOC · XDR · 安全运营 · TDIR · 厂商立场 · 采购决策 · 译文 |
| 2026-10-08 | [OpenSSH 10.6：AI 把漏洞报告推高之后，他们改了发布节奏](https://freelamp.com/articles/openssh-10-6-ai-bug-reports/) | OpenSSH · 安全 · AI辅助审计 · 漏洞报告 · 后量子密码 · ML-DSA · SSH · 开源治理 · 译文 |
| 2026-10-08 | [树莓派桌面终于出了 x86-64 版：但它的目标用户可能不是你](https://freelamp.com/articles/raspberry-pi-desktop-x86-64/) | Raspberry Pi · Raspberry Pi OS · Debian · Trixie · LXDE · 轻量桌面 · 教育 · 译文 |
| 2026-10-08 | [Ubuntu 26.10 的安全清单：GRUB 瘦身、coreutils 全 Rust、OpenSSL 4.0 与 upki 吊销检查](https://freelamp.com/articles/ubuntu-26-10-security/) | Ubuntu · 安全加固 · GRUB · Secure Boot · TPM · Rust · uutils · OpenSSL · upki · CRLite · dbus-broker · 译文 |
| 2026-10-08 | [华为 Peerium：新闻稿说「突破」冯·诺依曼，论文说「延续」冯·诺依曼](https://freelamp.com/articles/2026-10-08_huawei-peerium-lingqu-hc2026/) | 华为 · Peerium · 灵衢 · UnifiedBus · 昇腾 · Atlas950 · 超节点 · 冯诺依曼 · BSP · 国产算力 · 产业分析 |
| 2026-10-08 | [LibreOffice 说「没有 AI」是个功能：但真正的价值是它给了六条验收标准](https://freelamp.com/articles/2026-10-08_libreoffice-no-ai-feature/) | LibreOffice · The Document Foundation · AI · 开源办公套件 · ODF · 隐私 · 本地推理 · Ollama · 供应商锁定 · 遥测 · 译文 |
| 2026-10-06 | [机密计算落地看这四种模式：但证明「环境可信」不等于证明「它不会乱来」](https://freelamp.com/articles/2026-10-06_confidential-computing-use-cases/) | 机密计算 · Intel TDX · TEE · 远程证明 · 隐私计算 · 联邦学习 · 数据主权 · 安全架构 · 译文 |
| 2026-10-06 | [红帽把零信任拆成 5 步：Ansible 自动化之路，以及它没说的三件事](https://freelamp.com/articles/2026-10-06_ansible-zero-trust-network/) | 零信任 · ZTNA · Ansible · Event-Driven Ansible · 网络自动化 · OPA · 策略即代码 · NIST · 安全架构 · 译文 |
| 2026-10-06 | [zram 重构读写流：内存省下「几十到几百 KB」，但真正的看点是消除优先级反转](https://freelamp.com/articles/2026-10-06_zram-streams-rework/) | Linux内核 · zram · 内存压缩 · zcomp · 内核补丁 · 优先级反转 · zstd · lz4hc · swap · 译文 |
| 2026-10-06 | [一个布尔值把内网服务变成了公网服务：把通配监听收回内网（socat 桥模式）](https://freelamp.com/articles/2026-10-06_wildcard-listen-to-lan-only/) | 网络安全 · 暴露面收敛 · socat · systemd · IPv6 · 通配监听 · 安全加固 · 原创 |
| 2026-10-06 | [万物皆隧道（续）：给香橙派接上 Cloudflare 零信任 SSH，每个访问端一张 3 分钟证书](https://freelamp.com/articles/2026-10-06_orange-pi-cloudflare-zero-trust-ssh/) | 零信任 · Cloudflare Tunnel · Access · SSH · 短时证书 · CGNAT · 内网穿透 · 安全加固 · 原创 |
| 2026-10-05 | [国庆回老家，万物皆隧道：把家里所有服务收敛到只剩一个 SSH 端口](https://freelamp.com/articles/2026-10-05_all-services-over-one-ssh-tunnel/) | SSH 隧道 · 内网收敛 · 端口转发 · DNS · 代理 · 远程桌面 · RustDesk · systemd · 安全加固 · 原创 |
| 2026-10-03 | [Ubuntu 正在给 Debian 的 APT 加 SHA3：为 SHA2 万一被攻破提前十年铺路](https://freelamp.com/articles/2026-10-03_ubuntu-sha3-apt/) | Ubuntu · Debian · APT · SHA3 · SHA2 · 密码学 · 包管理 · 供应链安全 · 密码敏捷性 · 译文 |
| 2026-10-02 | [Ubuntu 把 OpenPGP 也换成 Rust：Sequoia PGP 进入 26.10，未来或取代 GnuPG](https://freelamp.com/articles/2026-10-02_ubuntu-sequoia-pgp/) | Ubuntu · Sequoia PGP · OpenPGP · GnuPG · Rust · uutils · 内存安全 · 26.10 · 译文 |
| 2026-10-01 | [从 PSK 提取到私有引擎逆向：一次 Goodix 27c6:501d 指纹 Linux 适配的完整失败复盘](https://freelamp.com/articles/2026-10-01_goodix-501d-linux-fingerprint-postmortem/) | Goodix · 指纹 · libfprint · 逆向工程 · Wine · 虚拟化 · TLS-PSK · DPAPI · WBDI · 驱动适配 · 原创 |
| 2026-10-01 | [Vite+ 1.0 发布：一个 vp 命令接管运行时、包管理器和前端工具链](https://freelamp.com/articles/2026-10-01_vite-plus-1-0-released/) | Vite · Vite+ · VoidZero · Rolldown · Oxc · Vitest · 前端工具链 · Rust · 译文 |
| 2026-10-01 | [TP-Link 首款 Wi-Fi 8 路由开启全球预售，美国被排除在名单外](https://freelamp.com/articles/2026-10-01_tplink-wifi-8-router-us-ban/) | TP-Link · Wi-Fi 8 · 802.11bn · 路由器 · FCC · 出口管制 · 供应链 · Broadcom · 译文 |
| 2026-10-01 | [Qt 6.12 LTS 发布：QML 热重载进内核，StyleKit 试点，HarmonyOS 支持](https://freelamp.com/articles/2026-10-01_qt-6-12-lts-released/) | Qt · Qt6 · LTS · QML · 热重载 · StyleKit · HarmonyOS · Canvas Painter · QRhi · 译文 |
| 2026-10-01 | [Gitea 28.0.0 发布：版本号去掉 1. 前缀，出网访问默认收紧](https://freelamp.com/articles/2026-10-01_gitea-28-0-0-released/) | Gitea · 自托管 · Git · DevOps · 版本发布 · 出网控制 · Actions · 审计日志 · 译文 |
| 2026-10-01 | [ESP32 的五种 Wi-Fi 配网方式，以及怎么把它们全部自动化测试](https://freelamp.com/articles/2026-10-01_esp32-wifi-commissioning-testing/) | ESP32 · ESP-IDF · Wi-Fi 配网 · 嵌入式 · 自动化测试 · CI · SmartConfig · WPS · BLE · 硬件在环 · 译文 |
| 2026-10-01 | [它曾是金融权力的象征：彭博终端简史](https://freelamp.com/articles/2026-10-01_bloomberg-terminal-history/) | 彭博终端 · 金融科技 · 科技史 · 人机交互 · 键盘 · 史密森尼 · 市场数据 · 译文 |
| 2026-10-01 | [Google 一个畸形配置包，让成千上万 iOS 应用集体闪退：Firebase 事故复盘](https://freelamp.com/articles/2026-10-01_firebase-ios-crash-incident/) | Firebase · Google · iOS · SDK · 事故复盘 · 第三方 SDK 依赖 · 移动开发 · 译文 |
| 2026-10-01 | [Plex 关掉了最后一个免费漏洞：远程串流自己的电影，现在必须付费](https://freelamp.com/articles/2026-10-01_plex-remote-streaming-paywall/) | Plex · 媒体服务器 · 自托管 · Tailscale · Infuse · Jellyfin · 订阅制 · 远程访问 · 译文 |
| 2026-09-29 | [Google 确认 ChromeOS 2034 年退场：10 年支持承诺照旧，但较新 Chromebook 可迁移到 Googlebook OS](https://freelamp.com/articles/2026-09-29_chromeos-phase-out-2034-googlebook/) | ChromeOS · Googlebook · Google · Chromebook · Android · Aluminum OS · 操作系统 · 译文 |
| 2026-09-29 | [Chrome 都两周一个大版本了，信创浏览器还停在 120：内核版本碎片化才是信创的真难题](https://freelamp.com/articles/2026-09-29_xinchuang-browser-kernel-lag/) | 信创 · 国产操作系统 · UOS · 统信 · 浏览器 · Chromium · Ungoogled-Chromium · glibc · 国产替代 · 原创 |
| 2026-09-29 | [Ubuntu 内核改成每周更新：废掉 4/2 模型、启用重叠双周流水线，CVE 暴涨逼出来的](https://freelamp.com/articles/2026-09-29_ubuntu-weekly-kernel-updates/) | Ubuntu · Linux内核 · SRU · CVE · Canonical · 内核更新 · 发行版 · 译文 |
| 2026-09-28 | [NetScaler ADC/Gateway 两个 9.5 分在野 0day：Citrix 催补，CISA 当日拉入 KEV](https://freelamp.com/articles/2026-09-28_netscaler-adc-gateway-zero-day-cve-2026-88771/) | NetScaler · Citrix · ADC · Gateway · CVE-2026-88771 · CVE-2026-88772 · 0day · RCE · KEV · CISA · 安全运维 · 应急 · 译文 |
| 2026-09-28 | [16 岁少年用 AI 助手攻破微软内部分析库：170 亿行数据、JWT 不验签，赏金 5000 美元](https://freelamp.com/articles/2026-09-28_microsoft-titan-analytics-jwt-flaw/) | Microsoft · Titan Analytics · JWT · alg-none · 认证绕过 · ClickHouse · 漏洞赏金 · AI 助手 · Antares · 安全 · 译文 |
| 2026-09-28 | [Noctalia 5.2.0 发布：窗口切换器重做、面板启动器、日历事件提醒与锁屏过渡](https://freelamp.com/articles/2026-09-28_noctalia-5-2-0-released/) | Noctalia · Wayland · 桌面壳 · Linux 桌面 · Umbriel · 窗口切换器 · CalDAV · 插件 · 译文 |
| 2026-09-28 | [在 Linux 上原生跑安卓应用：Waydroid 实操与边界（不是模拟器，是容器化 LineageOS）](https://freelamp.com/articles/2026-09-28_android-native-on-linux-waydroid/) | Waydroid · Android · Linux 桌面 · Wayland · LineageOS · binder · Zen 内核 · 容器化安卓 · 原创 |
| 2026-09-27 | [Budgie 10.10.3 发布：Budgie Menu 终于支持收藏夹，Labwc 桥接与 oo7 密钥服务跟进](https://freelamp.com/articles/2026-09-27_budgie-10-10-3-released/) | Budgie · 桌面环境 · Linux 桌面 · Wayland · Labwc · oo7 · Secret Service · 译文 |
| 2026-09-26 | [为 DRBD 9 进主线铺路：LINBIT 发出重构内核 DRBD 8.4 代码的准备补丁](https://freelamp.com/articles/2026-09-26_linux-patches-toward-drbd-9/) | DRBD · LINBIT · 分布式复制块设备 · 内核主线 · 高可用 · 存储 · 译文 |
| 2026-09-26 | [逼近 10 秒的 Linux 内核构建：双路 EPYC 9575F + Kbuild 并行化补丁，defconfig 22→15 秒](https://freelamp.com/articles/2026-09-26_near-10-sec-kernel-build/) | Linux 内核 · 内核构建 · Kbuild · Lorenzo Stoakes · AMD EPYC 9575F · 并行构建 · 编译性能 · 译文 |
| 2026-09-26 | [Samba 4.25 发布：实验性 SMB3 持久句柄，朝透明故障转移迈出一步](https://freelamp.com/articles/2026-09-26_samba-4-25-released/) | Samba · SMB3 · 持久句柄 · 文件服务 · Ceph RGW · 域加密 · 译文 |
| 2026-09-26 | [Linux 考虑引入 AGENTS.md：给 AI/LLM 代理一份内核贡献指南](https://freelamp.com/articles/2026-09-26_linux-considers-agents-md/) | Linux 内核 · AGENTS.md · AI 代理 · AI 补丁 · 内核治理 · Sasha Levin · 译文 |
| 2026-09-26 | [ReactOS 把 Wine 10.0 的 DirectX 栈整体搬进来了：解锁上百款游戏](https://freelamp.com/articles/2026-09-26_reactos-wine-directx-10/) | ReactOS · Wine 10.0 · DirectX · Vulkan · OpenGL · 兼容层 · 游戏兼容 · 译文 |
| 2026-09-26 | [GDB 18.1 发布：Windows 原生目标大改、新增 MicroBlaze/AArch64 MinGW 目标、Python API 扩充](https://freelamp.com/articles/2026-09-26_gdb-18-1-released/) | GDB · 调试器 · Windows 原生目标 · AArch64 MinGW · Python API · CTF 移除 · 译文 |
| 2026-09-24 | [在 Linux 上给 iPod Nano 6 加歌：libgpod 的「Unsupported checksum type」是怎么被绕过去的](https://freelamp.com/articles/2026-09-24_ipod-nano6-linux-sync/) | iPod · iPod Nano · libgpod · hashAB · SQLite · iTunesDB · iTunesCDB · gtkpod · rhythmbox · ipodsync · Linux · 故障排查 · 原创 |
| 2026-09-24 | [Kernel Report 回归：Jonathan Corbet 在 Kernel Recipes 2026 谈内核社区的「加速变化」](https://freelamp.com/articles/2026-09-24_kernel-report-2026-returns/) | Linux 内核 · Kernel Report · Jonathan Corbet · Kernel Recipes · Maintainers Summit · AI 补丁 · Sashiko · 内核治理 · 编译 |
| 2026-09-24 | [文件通知攻击：Linux / Windows / macOS 的文件监控子系统正在泄漏你的操作](https://freelamp.com/articles/2026-09-24_file-notification-attacks-sidechannel/) | 侧信道 · 文件通知 · inotify · FSEvents · 操作系统安全 · 击键时序 · 网站指纹 · 隐私 · 论文解读 |
| 2026-09-24 | [F-Droid 2.0 发布：十年最大改版，重写为 Kotlin Compose，安装体验终于追上系统商店](https://freelamp.com/articles/2026-09-24_fdroid-2-0-release/) | F-Droid · Android · 开源应用商店 · Kotlin · Jetpack Compose · DMA · 侧载 · 隐私 · Nearby · 译文 |
| 2026-09-24 | [当软件订阅变成公共政策：一座城市的 70 万美元软件账单](https://freelamp.com/articles/2026-09-24_software-subscriptions-public-policy/) | 软件订阅 · SaaS · 公共政策 · 供应商锁定 · 数据可移植性 · 退出计划 · 自主可控 · 开源 · 政府采购 · 译文 |
| 2026-09-24 | [WordPress 修补一个严重级漏洞：未认证 RCE，补丁发布数小时内即被利用](https://freelamp.com/articles/2026-09-24_wordpress-critical-rce-cve-2026-87902/) | WordPress · CVE-2026-87902 · RCE · 未认证 · pearcmd · 补丁管理 · 应急响应 · 攻击面 · EASM · 安全运维 · 译文 |
| 2026-09-24 | [Adobe 全家桶的免费替代：Photoshop→GIMP、Lightroom→darktable、Illustrator→Inkscape、Premiere→Kdenlive](https://freelamp.com/articles/2026-09-24_adobe-free-alternatives-switch/) | 开源替代 · Adobe · GIMP · Krita · darktable · Inkscape · Kdenlive · 创意软件 · 订阅制 · 本地优先 · 译文 |
| 2026-09-24 | [Mir 2.30 发布：Rust 从可选变硬性依赖，Canonical 首次公开 Mir 路线图](https://freelamp.com/articles/2026-09-24_mir-2-30-released/) | Mir · Canonical · Wayland · 合成器 · Rust · Ubuntu 26.04 · wl_fixes · 路线图 · 译文 |
| 2026-09-24 | [国产打印机厂商全景：谁在造整机、谁在做主控，A3 与彩色花落谁家](https://freelamp.com/articles/2026-09-24_domestic-printer-vendors-map/) | 国产打印机 · 信创 · 主控芯片 · 龙芯 · 极海微 · 众诺北辰 · 奔图 · 汉光 · 立思辰 · 得力 · A3 · 彩色打印 · 产业梳理 · 原创 |
| 2026-09-24 | [Linux 把本地 mp3 推到 HomePod：从 atvremote 到 mpv 到 PipeWire 升级的完整排障](https://freelamp.com/articles/2026-09-24_linux-airplay-homepod-pipewire/) | PipeWire · HomePod · AirPlay · RAOP · mpv · atvremote · pyatv · raop_play · 音频 · Debian · 故障排查 · 原创 |
| 2026-09-23 | [声卡整个消失了：一行 rm 删掉 .tplg，SOF 驱动找不到文件的全过程](https://freelamp.com/articles/2026-09-23_sof-tplg-missing-no-soundcard/) | Linux · 内核 · ALSA · SOF · 声卡 · firmware · dmesg · Debian · 故障排查 · 运维 · 原创 |
| 2026-09-23 | [rspamd 把 46% 的合法邮件丢进了垃圾箱：一次从配置文件体系开始的排查](https://freelamp.com/articles/2026-09-23_rspamd-false-positive-tuning/) | rspamd · postfix · dovecot · 反垃圾邮件 · 邮件网关 · DKIM · SPF · DMARC · Sieve · Debian · 运维 · 原创 |
| 2026-09-22 | [DMS 换 Noctalia：niri 桌面壳迁移实录，以及两者的真实差别](https://freelamp.com/articles/2026-09-22_dms-to-noctalia-niri-shell/) | niri · Wayland · Noctalia · DankMaterialShell · DMS · Quickshell · Debian · Linux桌面 · 桌面壳 |
| 2026-09-23 | [Debian 上线「推理门户」：Scaleway 出资，给 Debian 开发者免费跑 DeepSeek V4 Flash / GLM-5.2](https://freelamp.com/articles/2026-09-23_debian-inference-portal/) | Debian · Inference Portal · Scaleway · DeepSeek V4 Flash · GLM-5.2 · Salsa · 开放权重 · AI 公用事业 · 译文 |
| 2026-09-23 | [高通在夏威夷谈 Snapdragon X2 的 Linux：早期开发者预览，Debian 13 用户态，HP/华硕承诺 2027 H1 官方支持](https://freelamp.com/articles/2026-09-23_qualcomm-snapdragon-x2-linux/) | 高通 · Qualcomm · Snapdragon X2 · Arm 笔记本 · Linux · Debian 13 · Freedreno · Turnip · s2idle · 译文 |
| 2026-09-22 | [阿里云砸 300 万美元给 Omarchy：把 Arch 系桌面做成「理想 agentic OS」，默认调通 Qwen](https://freelamp.com/articles/2026-09-22_omarchy-alibaba-3m/) | Omarchy · Arch · 桌面发行版 · agentic OS · 阿里云 · Qwen · 独立科技媒体 |
| 2026-09-22 | [systemd 262 正式发布：内嵌兜底 unit、LUO 热更新会话，还带一只「AI 提交金丝雀」](https://freelamp.com/articles/2026-09-22_systemd-262-released/) | systemd · PID 1 · LUO · AI canary · 机密计算 · 静态二进制 · Linux init |
| 2026-09-22 | [SPECviewperf 15 终于出 Linux 原生版：x86_64 / AArch64 都有，但只给 OpenGL 4.5](https://freelamp.com/articles/2026-09-22_specviewperf-15-0-1-linux/) | SPECviewperf · 显卡基准 · 工作站 · Linux · OpenGL 4.5 · AArch64 · 专业图形 |
| 2026-09-21 | [CPO 的下一站，可能是一块玻璃：共封装光学走向「玻璃集成平台」](https://freelamp.com/articles/2026-09-21_cpo-glass-integration-platform/) | 半导体 · 先进封装 · CPO · 共封装光学 · 玻璃基板 · TGV · 异质集成 · 3D IC |
| 2026-09-19 | [一次打穿 OpenAI：libheif 堆溢出 + SSO 缺陷，72 小时接管员工账号](https://freelamp.com/articles/2026-09-19_hacktron-hacking-openai/) | 安全 · 漏洞 · OpenAI · SSO · libheif · ImageMagick · 堆溢出 · RCE · 供应链安全 · AI安全 |
| 2026-09-21 | [Linux perf script 命令大改：甩掉内嵌 Python/Perl，3.7 秒变 0.1 秒](https://freelamp.com/articles/2026-09-21_linux-perf-python-module/) | Linux · perf · 性能分析 · Python · C扩展 · 内核工具 · Ian Rogers · Google |
| 2026-09-21 | [GNU Wget2 2.3 发布：多了 --progress=dot，修了几个内存泄漏](https://freelamp.com/articles/2026-09-21_gnu-wget2-23/) | GNU · Wget2 · 下载工具 · HTTP/2 · 内存泄漏 · OS/2 |
| 2026-09-20 | [Gzip 1.15 发布：修了几个「自诞生起就存在」的 bug，其中一个是文件删除竞态](https://freelamp.com/articles/2026-09-20_gzip-115-bugfixes/) | gzip · GNU · 压缩工具 · 内存安全 · 缓冲区溢出 · TOCTOU · 数据损坏 · 安全运维 |
| 2026-09-19 | [有人把 Firefox 里的 AI 代码整个删了：Base Browser 与「硬分叉」运动](https://freelamp.com/articles/2026-09-19_base-browser-firefox-hardfork/) | 开源社区 · Firefox · Base Browser · 硬分叉 · Mozilla · 浏览器 · AI集成 · 独立web · Codeberg |
| 2026-09-19 | [DeepSeek V4.1 Flash 成 Enclave 最强「黑客模型」：11/11 拿下只花 4.65 美元](https://freelamp.com/articles/2026-09-19_deepseek-v41-flash-best-hacking-model/) | DeepSeek · AI安全 · 红队 · 自动化红队 · LLM Agent · 基准测试 · Grafana · Jenkins · Nextcloud · 漏洞利用 |
| 2026-09-19 | [CISA 要停掉每周漏洞通报：一句「BOD 26-04」说得通吗？](https://freelamp.com/articles/2026-09-19_cisa-ends-vuln-bulletin/) | CISA · 漏洞管理 · BOD 26-04 · KEV · 漏洞优先级 · CVSS · 安全运营 · 美国政府 |
| 2026-09-19 | [守住你的「AI 机群」：16 款治理/护栏/红队平台速览](https://freelamp.com/articles/2026-09-19_ai-fleet-governance-tools/) | AI治理 · AI安全 · 护栏 · 红队 · LLM · Agent · 合规 · 工具盘点 |
| 2026-09-19 | [GNOME OS 默认开启 zswap 治 OOM，邮件客户端 Geary 的 GTK4 复刻 Convey 登陆 Flathub](https://freelamp.com/articles/2026-09-19_gnome-os-zswap-convey/) | GNOME · GNOME OS · zswap · OOM · systemd generator · Rust · Convey · Geary · GTK4 · Flathub · Linux桌面 |
| 2026-09-19 | [Neovim 有个 ~80 万美元的比特币捐款，从 2023 年躺到现在没动过](https://freelamp.com/articles/2026-09-19_neovim-untouched-bitcoin/) | 开源社区 · Neovim · 比特币 · 加密货币 · 密钥管理 · Shamir · 门限签名 · FROST · 开源治理 |
| 2026-09-18 | [systemd 那个绿色 [ OK ]，是怎么变成 logo 的](https://freelamp.com/articles/2026-09-18_systemd-brand-ok-logo/) | systemd · Linux init · 品牌 · 开源文化 · GNOME · CC BY-SA 4.0 |
| 2026-09-18 | [长鑫（CXMT）要在北京做 3D NAND：DRAM 一哥，开始踩 YMTC 的 NAND 地盘](https://freelamp.com/articles/2026-09-18_cxmt-3d-nand-rd-beijing/) | CXMT · 长鑫 · 3D NAND · YMTC · 长江存储 · 存储 · SSD · DRAM · 半导体 · 国产存储 |
| 2026-09-18 | [Wine 11.18 继续补全 NTOSKRNL：Windows 内核驱动在 Linux 上跑得越来越真](https://freelamp.com/articles/2026-09-18_wine-11.18-ntoskrnl/) | Wine · NTOSKRNL · 兼容层 · Windows · Linux · 内核驱动 · PnP · 游戏兼容 |
| 2026-09-18 | [Ubuntu 26.10 改主意了：内核从 7.2 跳到 7.3，十月前吃上最新主线](https://freelamp.com/articles/2026-09-18_ubuntu-2610-linux-73/) | Ubuntu · 26.10 · Linux 7.3 · 内核 · 发行版 · Canonical · 译文 |
| 2026-09-18 | [Git 2.56 发布，3.0 要把 SHA-256 设为默认：reftable、强制 Rust 与大小写 ID 清除](https://freelamp.com/articles/2026-09-18_git-256-and-30/) | Git · 版本控制 · SHA-256 · reftable · Rust · 兼容性破坏 · LWN |
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
