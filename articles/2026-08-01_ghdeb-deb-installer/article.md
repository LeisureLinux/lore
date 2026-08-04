# 这个开源项目让 GitHub .deb 安装从 5 步变成 1 步

> 读完本文，你会知道如何用一条命令安装和升级所有从 GitHub 下载的 .deb 包。

---

## 一个熟悉的场景

你在 GitHub 上发现一个好用的工具，比如 bat、fd、ripgrep、RustDesk。作者提供了 `.deb` 包。

你开始安装：

1. 打开 Releases 页面
2. 找到对应架构的 `.deb` 文件
3. 复制下载链接
4. `wget` 下载
5. `sudo dpkg -i` 安装

五步。不算多，但每次升级都要再来一遍。

更麻烦的是，这些包不在 apt 仓库里。`apt upgrade` 不会管它们。你装了就忘了，版本永远停留在安装那天。

**ghdeb** 就是为了解决这个问题。

---

## 一行命令

```bash
ghdeb install rustdesk/rustdesk
```

完了。

它自动检测你的系统架构，从 GitHub Releases 找到匹配的 `.deb` 文件，下载，安装。

ghdeb 内置了 50+ 个热门 GitHub `.deb` 包的目录（catalog），所以大部分时候连完整仓库名都不用写：

```bash
ghdeb install bat        # → sharkdp/bat
ghdeb install fd         # → sharkdp/fd
ghdeb install ripgrep    # → BurntSushi/ripgrep
ghdeb install gh         # → cli/cli
```

升级更简单：

```bash
ghdeb upgrade
```

一条命令升级所有通过 ghdeb 管理的包。也可以只升级某一个：

```bash
ghdeb upgrade rustdesk
```

---

## 它解决了什么

Debian/Ubuntu 的包管理体系很成熟，但有一个盲区：**从 GitHub 直接安装的 .deb 包是"孤儿"**。

它们不在任何 apt 源里。`apt list --upgradable` 看不到它们。`apt upgrade` 不会升级它们。

ghdeb 把这些包纳入统一管理。它不扫描你系统里装了什么，而是维护一份**精选目录**（catalog），让你像用 apt 一样管理这些包：

- **update**：像 `apt update` 一样，把目录里所有项的最新版本刷新到本地快照
- **list**：列出目录里所有包和版本（读本地快照，不联网）
- **search**：按名称/简介搜索目录里的包
- **catalog**：`add` / `modify` / `delete` / `validate`，维护你自己的包目录
- **upgrade**：一键升级
- **history**：查看每个包的安装/升级历史

---

## 技术细节

几个值得注意的设计：

**目录驱动的管理方式**。ghdeb 自带一份精选 catalog（`/etc/ghdeb/catalog.toml`，50+ 个包）。`ghdeb update` 把每个条目在 GitHub 上的最新版本、本地安装版本等信息写到系统级缓存 `/var/cache/ghdeb/cache.json`，之后 `ghdeb list` 只读缓存、完全不联网，像 `apt` 一样快。

**架构自动匹配**。通过 `dpkg --print-architecture` 检测架构，识别 amd64 / arm64，并处理 `x86_64`、`aarch64` 等文件名变体，优先选标准包，跳过 musl / static / portable 等变体。

**x86-64 微架构优化（v2/v3/v4）**。有的项目（比如 `daeuniverse/dae`）会针对不同 CPU 微架构发布多个 `.deb`（如 `dae-linux-x86_64_v3_avx2.deb`）。ghdeb 读 `/proc/cpuinfo`，检测你的 CPU 支持到 v1/v2/v3/v4 哪一档，自动挑选能跑的最高档变体，没有匹配时回退到普通 `x86_64` 包。

**下载容错**。3 次重试，指数退避（2s/4s/8s）。支持断点续传。网络不稳时不会从头再来。

**代理感知**。支持 `https_proxy` 环境变量，也可以写在 `~/.config/ghdeb/config.json` 里。国内用户配好代理就能用。

**非交互式安装**。设置 `DEBIAN_FRONTEND=noninteractive`，不会出现 debconf 弹窗卡住脚本。

**Shell 补全**。装好后自带 zsh / bash / fish 的命令补全。

**维护配套**。`reinstall` 重装、`purge` 卸载并清除配置、`clean` 清理下载缓存。

---

## 对比

| 工具 | 方式 | 问题 |
|------|------|------|
| ghdeb | 客户端 CLI，零配置 | — |
| gitdeb | Shell 脚本 | 没有社区验证 |
| debian-package-installer | Python + JSON 配置 | 需要配置文件 |
| github-apt-repos | 服务端 APT 仓库 | 需要基础设施，个人用太重 |
| inapt | 服务端 APT 代理 | 需要基础设施 |
| apt-transport-github | APT 传输层 | 标记"未完成"，已停止维护 |

ghdeb 的定位很明确：**轻量、零配置、客户端工具**。不替代 apt，只管理 apt 管不到的包。

---

## 安装

```bash
ghdeb install LeisureLinux/ghdeb
```

或者从源码构建：

```bash
git clone https://github.com/LeisureLinux/ghdeb.git
cd ghdeb && make build && sudo make install
```

---

## 常用命令

```bash
ghdeb install cli/cli              # 安装 GitHub CLI
ghdeb install rustdesk             # 短名称安装 RustDesk（走内置目录）
ghdeb update                       # 刷新版本信息到本地快照（类似 apt update）
ghdeb list                         # 列出所有目录项（读本地快照）
ghdeb search monitor               # 搜索目录里的包
ghdeb catalog show bat             # 查看某个目录项详情
ghdeb upgrade                      # 升级所有
ghdeb info LeisureLinux/ghdeb      # 查看最新版本信息
ghdeb history rustdesk             # 查看安装/升级历史
```

---

## 写在最后

这不是一个改变世界的工具。它只是把一件小事做好了。

Debian/Ubuntu 用户从 GitHub 装 .deb 包是个高频操作。每次五步，累积起来就是时间。ghdeb 把它变成一步。

开源地址：[github.com/LeisureLinux/ghdeb](https://github.com/LeisureLinux/ghdeb)

---

*你在工作中用过这个工具吗？或者你有什么管理 GitHub .deb 包的方法？留言聊聊。*

*下周五我们继续推荐好用的开源工具。关注别错过。*
