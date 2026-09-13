# Homebrew 7.0.0 发布：Intel Mac 降级、Landlock 沙箱、原生 GUI 与内置漏洞检查

> 译文来源：Homebrew 官方博客《Homebrew: 7.0.0》，MikeMcQuaid，2026-09-13，原文链接 https://brew.sh/2026/09/13/homebrew-7.0.0/

9 月 13 日，Homebrew 发布 7.0.0 大版本。官方对 6.0.0 以来最重要变化的概括只有一句话：**更快的安装与升级、更强的沙箱、原生 macOS 应用、内置漏洞检查与公告数据库、macOS 10.15 支持终结、Intel Mac 降至 Tier 3。**

对一句话里没有展开的部分——尤其是 Intel Mac 用户该怎么办、Linux 沙箱为什么换了实现、`post_install` 为什么被弃用——本文在译文之外给出解读。

## 事件概览

Homebrew 的版本节奏是一年一个大版本：6.0.0 于今年 6 月发布，7.0.0 如约而至。升级方式无门槛：自动更新（或设置了 `$HOMEBREW_NO_AUTO_UPDATE` 的用户手动 `brew update`）即可完成。

但这一次的"破坏面"比以往更宽。官方列出的环境行为变更时间线：

| 环境 / 接口 | 7.0.0 行为 | 生效时间 |
|---|---|---|
| macOS 10.15 及更早 | 已移除，需升级 macOS 11+ | 立即 |
| macOS Sonoma 14 | Tier 3，无新 bottles | 立即 |
| macOS Golden Gate 27（Apple Silicon） | Tier 1 全支持，预构建 bottles | 立即 |
| `ghcr.io/homebrew/ubuntu22.04` 镜像 | 已移除，迁移至 `ghcr.io/homebrew/brew` | 立即 |
| `Homebrew/actions/*@master` | 已移除，固定 CalVer release 或完整 SHA | 立即 |
| setuid wrapper（真实/有效 UID 不同） | 直接拒绝 | 立即 |
| Intel macOS 11+ | Tier 3，无新 bottles | 立即；2027-09-01 停止运行 |
| Apple Silicon macOS 11 | 2027-09-01 移除 | 届时 |
| 第三方 formula `post_install` / cask `*flight` 块 | 弃用，迁移至 `*_steps` | 2027-12-11 |
| `Homebrew/brew` 的 `master` 分支 | 冻结引导，切 `main` | 2027-03-01 |

## 关键变化解读

### 一、Intel Mac：不是"减少支持"，是倒计时

这是本次发布最重磅也最无争议的消息。Apple 已在 macOS 27 Golden Gate 中放弃 Intel `x86_64`，GitHub Actions 将于 2027 年秋退役 Intel macOS runner。官方原话很直白：

> 如果 Apple 和 Microsoft 的 GitHub——世界上最大的两家科技公司——都无法继续支持 macOS Intel x86_64，很遗憾 Homebrew 也做不到。MacPorts 仍然支持该平台，且大概率能提供更好的结果。

时间表：7.0.0 起 Intel 就是 Tier 3（现有 bottles 保留，但更新过的 formula 可能要源码编译）；2027-09-01 起 Homebrew 彻底停止在 Intel 上运行。`.pkg` 安装器现在仅支持 Apple Silicon 且要求 macOS Sequoia 15+。

### 二、Linux 沙箱：Bubblewrap 换 Landlock

6.0.0 引入的 Bubblewrap 沙箱在 7.0.0 被替换为内核原生的 **Landlock**（Linux 6.1+，ABI 2）。原因很实际：Bubblewrap 需要额外依赖和提升的 Docker 权限，落地时问题不少；Landlock 零依赖、无提权。内核不支持 Landlock 的机器仍可运行，只是退回 6.0.0 之前"无沙箱"的旧配置，`brew doctor` 会给出 advisory 提示。

配套变量变化：`HOMEBREW_SANDBOX_LINUX` 已禁用（Landlock 可用时自动启用）；`HOMEBREW_NO_SANDBOX_LINUX` 与 `HOMEBREW_ARCH` 于 2027-12-11 弃用。

### 三、安全：公告数据库 + `brew vulns` + 一批 GHSA 修复

这是 7.0.0 最值得安全团队关注的部分：

- **Homebrew advisory-database**：新开的漏洞公告数据库，针对 Homebrew 实际打包的 formula 版本与 revision 记录漏洞（包括 backport 的安全修复），OSV 格式，CC0 许可，可自由复用。
- **`brew vulns` 内置命令**：基于 OSV.dev 扫描已安装 formula 的已知漏洞，无需额外 tap 或 gem。支持 `--severity=high`、`--deps`、`--brewfile`、`--fix-available` 等过滤，还有 `--list-skipped` 查看覆盖缺口。
- 漏洞发现也进 formula API 和可下载的 advisory 索引，第三方工具可以区分"未修复"与"已随包发布修复"。
- 一批安全公告修复：包括 6.0.12 修复的 **GHSA-rg9r-ppxp-87hm（高危）**——未签名的 cask 卸载元数据可经 `sudo` 执行命令；以及 7.0.0 修复的 **GHSA-5263-whxq-77hp（中危）**——恶意 cask 可经 LaunchServices 在沙箱外执行代码，现已限制应用启动、Mach 服务与 Unix socket 连接。

沙箱本身也在收紧：formula 与 cask 操作进入沙箱、依赖下载迁往独立 `fetch` 阶段（下载时有网络+可写缓存，`install` 阶段断网+缓存只读）、默认阻止沙箱内读取用户 home 目录。

### 四、BrewUI：官方原生 macOS 应用

`brew install homebrew-app`（macOS Tahoe 26+）可装上官方 GUI：包浏览、搜索、已装版本信息一个窗口搞定，并且每个操作都会显示底层 `brew` 命令——不是把终端藏起来，而是把 GUI 操作和熟悉的命令对应起来。

### 五、性能：并发贯穿安装链路

- `brew install/reinstall/upgrade` 的包准备与下载重叠执行，`brew bundle` 批量安装同样受益；
- `brew config`、`brew tap-info --json` 并发收集系统信息；
- `brew cleanup` 避免重复缓存扫描；`brew fetch` 直接从 API 元数据取下载信息；
- 启动子进程减少，热运行复用已解析的 API 数据（签名每次加载都验）。

### 六、Tap 维护者：`post_install` 时代落幕

formula 的 `post_install` 与 cask 的 `*flight` Ruby 块被弃用，改为声明式 `*_steps`。动机是安全：显式的操作与路径可以被验证、沙箱化、经签名 API 下发，而不是"装包时执行任意 Ruby"。官方 tap 已直接拒绝旧钩子，第三方 tap 宽限到 2027-12-11。`brew style --fix` 可自动转换常见钩子。

## 我的解读

**1. "去 Ruby 化"是主线，安全和性能是同一枚硬币的两面。** 从弃用 `post_install`、把下载信息挪进 API、到 cask 语言变体不再逐个 eval Ruby 定义——Homebrew 在持续收缩"包定义=可执行代码"的表面积。这不是审美洁癖：Cask 类恶意包（如本次修复的 LaunchServices 沙箱逃逸）恰恰是通过"安装时执行代码"得手的。声明式 steps + 签名数据 + 沙箱，是供应链防护的三件套。

**2. `brew vulns` 补上了包管理器级漏洞可见性的缺口。** Linux 发行版有发行版安全公告（DSA/USN）已久，Homebrew 此前一直是空白——用户装了什么、哪些版本带 CVE，靠自觉。现在有了 CC0 的 OSV 数据库 + 内置扫描命令，CI 里跑 `brew vulns --brewfile` 就能给开发环境做漏洞门禁。对用 Homebrew 管理 macOS 开发机的团队，这是 7.0.0 里 ROI 最高的一个功能。

**3. Intel Mac 的退场时间表值得现在就行动。** Tier 3 意味着今天起就可能碰到"formula 更新了但没有新 bottle，只能源码编译"的情况，且会越来越频繁。2027-09-01 不是"停止支持"而是"停止运行"。还在用 Intel Mac 做开发机的，现在迁移 Apple Silicon 或转 MacPorts 的成本，远低于一年后被动迁移。

**4. Linux 侧选 Landlock 是明智的务实。** Bubblewrap 需要引入依赖和 Docker 权限，对一个"装在用户目录、不以 root 跑"的工具来说部署摩擦太大。Landlock 的代价是依赖内核版本（6.1+），但 2026 年的主流发行版都已覆盖；无 Landlock 时优雅降级而非报错，这个取舍做得干净。

## 结语

Homebrew 7.0.0 是一个"基础设施型"大版本：用户可见的新东西（BrewUI、`brew vulns`）不多，但底层从安全模型到沙箱实现到安装链路并发都在换梁换柱。6.0.0 到 7.0.0 之间 Homebrew/brew 仓库长期保持 0 个 open issue，这个志愿者项目的工程纪律可见一斑。

升级建议：`brew update` 即可。Intel Mac 用户、CI 里引用 `ubuntu22.04` 镜像或 `@master` action 的、以及维护第三方 tap 的，按上文时间线尽早迁移。详细迁移指南见官方 7.0.0-migration-guide。
