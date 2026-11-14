---
title: "Buildroot 25 年：不用等 LWN，git 历史自己会讲话"
date: 2026-11-14
slug: buildroot-25-years-git-history
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：LWN Articles/1103395《25 years of Buildroot》当前为订阅墙内容，页面写明 2026-12-03 免费开放，本文不绕过付费墙、正文内容未取用；改由项目自身公开资料完成核实。＋ GitLab 官方仓库 https://gitlab.com/buildroot.org/buildroot/ 项目元数据与 commit API（首个 commit `ffde94bd2ca21542ae0b4518348f8e986b9d92e0`，2001-12-22T00:56:11Z，Eric Andersen <andersen@codepoet.org>，`Initial revision`；官方仓库 2017-02-06 建于 GitLab、最后活动 2026-11-14、master 分支；tags 含 2026.11-rc1 于 2026-11-14、2026.08.1、2025.02.19 等）＋ GitHub 镜像 buildroot/buildroot 元数据（明示「this is not the official repository, but only a mirror」，3699 stars / 2900 forks，2013 建，2026-11-14 仍有推送）＋ Buildroot 邮件列表《20th anniversay of Buildroot》（Yann E. MORIN，2021-12-12；给出首个 commit 的完整 diffstat：10 files、1166 insertions、Makefile/boa.mk/busybox.mk/boa.conf/linux-uml.config 等，并称 20 年间 60324 个非 merge commit）＋《Request for testimonals from users for Buildroot 25y talk》（Peter Korsgaard，2026-09-13；为 10 月 9 日布拉格 ELC Europe 演讲征集用户案例）＋ OSS+ELC EU 2026 议程（2026-10-09 14:00 CEST，South Hall 3 B，Peter Korsgaard / Barco，《Buildroot at 25: A Quarter Century of Making Embedded Linux Easy》）＋ Linux Foundation 官方 YouTube 视频与自动转录（qGq6TkomhFU，2026-11-02 发布；演讲者自述：2001 圣诞前首个 commit、当时用 CVS 而非 Git、2.4 内核时代、比 OpenEmbedded 更早故为最老的嵌入式 Linux 构建系统、起初是 uClibc 子项目托管在 buildroot.uclibc.org、只支持 uClibc + BusyBox；作者约 2006 年因 ethtool 包参与、2009 年初因无活跃维护者/no releases 提出接管并改为每年 2/5/8/11 月四次时间制发布；维护者团队 2012 Thomas、2017 Arnout、2019 Yann（2024 退下）、Roman/Julien、2026 Marcus/Fiona，共 7 人；2017 因性能迁 GitLab；2012 Luca 加 license compliance；2015 有人问 LTS 政策、后做 1 年 LTS、2024 起改为 3 年支持且每两年一版、2025.02 为首个；统计：25 年约 85000 commits、约 1600 位贡献者、近年约每年 5000 改动 / 每天 9–10 个、80% 日子有活动、约 60 万行代码 / 15000 文件、近 300 次发布、包数从 2009.02 的 624 到最近 3341；用户案例含 Home Assistant OS 自 2018 用 Buildroot、约 200 万安装，Tomato64 用 BR2_EXTERNAL；未来倾向成熟项目不做激进变更，并明确「Yocto 用得开心就继续用」；Q&A 里 BR2 前缀从首个 commit 就在、原因已不可考）＋ Buildroot 官网首页 / news / download / lts 页（定位：用交叉编译生成嵌入式 Linux 系统，含工具链、rootfs、内核、bootloader；kernel-like menuconfig，15–30 分钟构建基础系统；只依赖 Makefile；2009-01-16「新维护者 Peter Korsgaard」、2009-03-27 自有 logo、2009-05-14 获赠 buildroot.org 域名、2009-09 首次 Developer Day；下载页 2026.08.1 稳定、2026.05.3 旧稳定、2025.02.19 LTS 支持至 2028-03；LTS 页：自 2025.02 起奇数年首个发布为 3 年 LTS、非 LTS 每 3 个月一版、每周由受赞助的 stewards 挑选 backport、security.buildroot.org 跟踪漏洞、提供 SBOM/许可证材料）＋ Arm 社区《25 years of Buildroot》（Julien Olivain，2026-10-13；独立工程主导项目、从 32 位 Arm 到 AArch64、BeagleBone / Raspberry Pi / QEMU 配置、SBOM/CycloneDX、legal-info、漏洞跟踪、3 年 LTS）＋ 2026-11-05 Buildroot LinkedIn 提示两场 OSS 演讲视频已上线（含同场《Buildroot LTS in the CRA Era》）"
original_date: 2026-11-13
original_url: "https://lwn.net/Articles/1103395/"
description: "不绕 LWN 订阅墙，用项目自己的公开材料写 Buildroot 25 周年。核心事实全部可核：GitLab 官方仓库首个 commit `ffde94bd`，2001-12-22 00:56:11 UTC，Eric Andersen，标题 `Initial revision`，10 个文件 1166 行，含 Makefile、boa.mk、busybox.mk 与一份 UML 内核配置 —— 一个 uClibc 子项目、只支持 uClibc + BusyBox，比 OpenEmbedded 更早，因此是现存最老的嵌入式 Linux 构建系统。文章按 Peter Korsgaard 在 OSS+ELC EU 2026 的公开演讲转录梳理 25 年：2006 年因 ethtool 包参与，2009 年项目无活跃维护者、无发布，他发信接管并改为 2/5/8/11 月四次时间制发布；2012 加 license compliance、2017 因性能迁 GitLab、维护者从一人扩到 7 人；LTS 从「没有政策」到 1 年、再到 2025.02 起 3 年支持且每两年一版。给出演讲者自报的规模数字：约 85000 commits、约 1600 贡献者、近年每年约 5000 改动、约 60 万行代码 / 15000 文件、近 300 次发布、包数 624→3341、Home Assistant OS 自 2018 使用约 200 万安装。也写清现状：官网下载页 2026.08.1 稳定、2025.02.19 LTS 支持到 2028-03；官网强调只依赖 Makefile、menuconfig、15–30 分钟出基础系统，而 Arm 社区纪念文补上 SBOM/CycloneDX、legal-info、漏洞跟踪与 AArch64 板级支持。边界：YouTube 自动转录有错字与口语，数字按演讲者口径标注；LWN 正文未读、12-03 解禁；GitHub 只是镜像，官方仓库在 GitLab。结论：25 年没换目标，只把「简单」从 1166 行 Makefile 维护成一套带 SBOM、CVE 跟踪、付费 LTS steward 的工程体系；Peter 那句「Yocto 用得开心就继续用」恰好说明了这个项目为什么活得久。"
published: true
---

之前把 LWN《25 years of Buildroot》放进暂缓队列，理由是订阅墙要等到 12 月 3 日。这个判断太偷懒了：Buildroot 是开源项目，25 年历史本来就不该等一篇付费报道来转述。真去翻 git 历史、邮件列表、官网和大会议程，材料比一篇综述还硬 —— 连 2001 年那个 `Initial revision` 的 commit hash 都能在 GitLab API 里直接验。

先把边界说清：LWN 那篇正文我没有读、也没有绕过付费墙，下面全部来自项目自己的公开资料与演讲者公开视频。

## 一、起点可以精确到秒

官方仓库在 GitLab（`gitlab.com/buildroot.org/buildroot`），GitHub 上那个 3699 星的 `buildroot/buildroot` 只是镜像，仓库描述里直接标明「this is not the official repository」。用 GitLab commit API 查第一个提交：

| 项 | 值 |
|---|---|
| commit | `ffde94bd2ca21542ae0b4518348f8e986b9d92e0` |
| 时间 | 2001-12-22 00:56:11 UTC |
| 作者 | Eric Andersen `<andersen@codepoet.org>` |
| 标题 | `Initial revision` |
| 规模 | 10 个文件、1166 行插入 |

2021 年 Yann E. MORIN 在邮件列表纪念 20 周年时，把这份 diffstat 全文贴了出来：`Makefile`、`README`、`boa.mk`、`busybox.mk`、`boa.conf`、`device_table.txt`、`linux-uml.config`、`mime.types`、`skel.tar` …… 一个很小的壳，把交叉工具链、BusyBox 用户态、Boa web 服务器和一份 UML 内核配置串起来。同一封邮件还给出当时的累计数字：60324 个非 merge commit。

Peter Korsgaard 在 25 周年演讲里补了几个 git 看不出来的背景：那时用的是 CVS 不是 Git（现在看到的 Git commit 是后来导入的），跑的是 2.4 内核，Siemens SL5500 还没在欧洲上市，OpenEmbedded 也还不存在 —— 所以他称 Buildroot 是「现存最老的嵌入式 Linux 构建系统」。项目最初是 uClibc 的子项目，托管在 `buildroot.uclibc.org`，与 uClibc 共用服务器和版本控制，只支持 uClibc 作 C 库、BusyBox 作用户态。

顺带一个可爱的考据：问答环节有人问为什么所有变量都以 `BR2_` 开头，Peter 答「第一个 commit 里就有，我不知道为什么，也不会改成 BR3」—— 25 年后的命名，源头已经不可考，但没人打算动它。

## 二、真正让项目活下来的，是 2009 年那封邮件

一个 2001 年的 Makefile 集合，不等于今天这个每季度发版、有 LTS 和 SBOM 的项目。转折点在 Peter 自己的讲述里很清楚：

- 约 2006 年：他因为需要一个配置网络的小工具，提交了 `ethtool` 包，开始参与；
- 之后一段时间项目「没有活跃维护者、没有发布」，补丁堆积；
- 2009 年初，他发邮件问「要不我来接手？」并提了一个关键制度：时间制发布，每年 2、5、8、11 月各一版。官网新闻页至今留着 2009-01-16 那条「发布候选与新维护者（Peter Korsgaard）」。

演讲转录里有一张贡献曲线：2009 年之前活动很低，接管后开始爬升，之后长期稳定。这套节奏延续至今 —— 官网下载页当前是 `2026.08.1` 稳定版、`2026.05.3` 旧稳定，LTS 是 `2025.02.19`；GitLab 上 `2026.11-rc1` 的 tag 时间是 2026-11-14。演讲说已经发了近 300 次 release。

同一条线上还有几步工程化：2012 年 Luca 加许可证合规支持、2017 年因性能把 git 托管迁到 GitLab（官方仓库创建时间正好是 2017-02-06）、2010 年起办 Developer Day（2025 年 2 月还在布鲁塞尔 FOSDEM 后开过三天）。维护者从一个人扩到演讲时的 7 人：2012 Thomas、2017 Arnout、2019 Yann（2024 退下）、Roman / Julien，2026 年又加入 Marcus 与 Fiona。Peter 特意说这点的意义是「我可以去度假，项目不会因为我离开几天就停」。

## 三、从「能编译」到「敢量产」

官网首页那句定位 25 年没变：用交叉编译生成嵌入式 Linux 系统，涵盖工具链、rootfs、内核镜像与 bootloader，靠类内核的 `menuconfig` 配置，只依赖 Makefile 语言，基础系统 15–30 分钟构建完。

变的是「简单」二字的成本。Arm 社区 10 月 13 日的纪念文与 Peter 的演讲合起来看，今天的 Buildroot 还得提供：

- 包规模：演讲给的数字是 2009.02 的 624 个包 → 最近版本 3341 个；官网 LTS 页另写「集成 2000+ 开源包」（口径不同，按各自出处标注）；
- 一致性基础设施：早期每个包自己写下载/解压/打补丁/配置/构建/安装，现在按构建系统（autotools、CMake、Meson 等）抽了共享 infra；
- 合规与供应链：`legal-info` 收许可证与源码信息、CycloneDX SBOM、`security.buildroot.org` 跟踪已知漏洞、运行时测试；
- BR2_EXTERNAL：把厂商自己的包/配置/板级支持放在 Buildroot 树外，演讲说它「清楚区分什么是 Buildroot、什么是你自己的」，最重要的是升级 Buildroot 版本更容易；
- 板级覆盖：从早期 32 位 Arm 到 Armv7 / AArch64，官方配置含 BeagleBone、多代 Raspberry Pi 与 QEMU 虚拟 Arm 目标。

Peter 自报的项目规模：25 年约 85000 commits、约 1600 位唯一贡献者；近年每年约 5000 个改动、每天 9–10 个 commit，80% 的日子有活动；代码约 60 万行、15000 个文件（含 makefile 片段、Config.in、defconfig、测试与补丁）。

用户案例也不空：Home Assistant OS 自 2018 年起用 Buildroot、演讲称约 200 万套安装；Tomato64 路由器项目用 `BR2_EXTERNAL` 做集成与升级；Arm 的 VP 也给了纪念致辞。

## 四、LTS：从「没有政策」到三年支持加付费 steward

这条线特别能说明嵌入式行业这 25 年的变化。Peter 在演讲里回忆：

1. 2015 年有人（Chris Simons）问有没有 LTS 政策，当时答案是「没有」—— 每三个月一版，想拿修复就得升级；
2. 后来做过 1 年 LTS，相邻 LTS 之间留 1 个月重叠；
3. 2024 年提出面向专业用户的更长方案，2025.02 起改为 3 年支持、每两年一个 LTS，两版之间留 1 年迁移窗口；官网 LTS 页确认：`2025.02.x` 支持到 2028-03，下一个是 `2027.02`。

更值得注意的是机制而不是年限：官网写明每周由受赞助的 LTS stewards 从 master 的提交里挑候选、标注、cherry-pick 到 staging 分支供其他维护者复核，漏洞修复优先 backport；赞助商还能指定关注的包与架构、拿定制安全报告。同场另有一场《Buildroot LTS in the CRA Era: 18 Months of Keeping a 3-Year Branch Secure》，对应欧盟 CRA 带来的合规压力。

一个 2001 年靠志愿者攒起来的 Makefile 项目，如今有付费岗位来维持「旧分支别出安全洞」—— 这大概是最能说明「嵌入式 Linux 已经不是爱好」的一句话。

## 五、边界

- LWN 1103395 正文未读，页面写明 2026-12-03 免费开放；本文不用、不转述、不绕过订阅墙。
- 25 周年演讲的数字与年份取自 YouTube 自动转录（Linux Foundation 频道，2026-11-02 发布）；自动文稿有口语、错字与个别人名误识（例如把 Eric 听成 Egil），凡涉及确定性事实（首个 commit、版本号、LTS 日期）我都回到 GitLab / 邮件列表 / 官网复核，其余规模数字按「演讲者自报」标注。
- 60324 commits（2021 年 20 周年）与约 85000 commits（2026 年演讲）是不同时点、不同统计口径，不要当作同一序列直接相减。
- GitHub `buildroot/buildroot` 是镜像，2013 年才建；官方仓库在 GitLab 且 2017 年迁入，仓库「创建时间」不等于项目起始时间。
- 本文未编译 Buildroot、未跑任何 defconfig；Arm 社区文与官网的功能描述按出处标注。

## 六、结论

25 年前那次提交只做了 1166 行：一个 Makefile、一份 BusyBox 与 Boa 的配方、一份 UML 内核配置。目标朴素到有点固执 —— 让交叉编译出一套嵌入式 Linux 别那么麻烦。

25 年后，目标还是这句，但「别那么麻烦」背后是 3300 多个包、每季度发版、SBOM 与 CVE 跟踪、3 年 LTS 和付费 steward、7 人维护团队、1600 位贡献者。项目没变成发行版，也没去追通用桌面；它把「简单」当成需要持续投入的工程属性在维护。

最耐人寻味的倒是 Peter 在问答里那句：Yocto 用得开心就继续用，开源本来就该有 vi 和 Emacs、有一堆发行版。一个 25 岁的项目不急着证明自己赢了，大概也正是它能活到 25 岁的原因。

至于 LWN 那篇，等 12 月 3 日解禁可以再对照着看；但这次不用等它 —— git 历史、邮件列表和演讲视频已经把话说完了。

## Sources

- LWN《25 years of Buildroot》（订阅墙，正文未取用）：<https://lwn.net/Articles/1103395/>
- 官方 GitLab 仓库：<https://gitlab.com/buildroot.org/buildroot/> ｜ 首个 commit：<https://gitlab.com/buildroot.org/buildroot/-/commit/ffde94bd2ca21542ae0b4518348f8e986b9d92e0> ｜ GitHub 镜像：<https://github.com/buildroot/buildroot>
- 邮件列表：20 周年 <https://lists.buildroot.org/pipermail/buildroot/2021-December/315970.html> ｜ 25 周年征集用户案例 <https://lists.buildroot.org/pipermail/buildroot/2026-September/809351.html>
- OSS+ELC EU 2026 议程：<https://osselceu2026.sched.com/event/2Ragq/> ｜ 演讲视频与转录（Linux Foundation）：<https://www.youtube.com/watch?v=qGq6TkomhFU>
- Buildroot 官网：<https://buildroot.org/> ｜ 新闻归档：<https://buildroot.org/news.html> ｜ 下载与 EOL：<https://buildroot.org/download.html> ｜ LTS：<https://buildroot.org/lts.html>
- Arm Community《25 years of Buildroot》（2026-10-13）：<https://developer.arm.com/community/arm-community-blogs/b/embedded-and-microcontrollers-blog/posts/25-years-of-buildroot-simplifying-embedded-linux-on-arm>
