# 这个开源项目让 GitHub .deb 安装从 5 步变成 1 步

> 读完本文，你会知道如何用一条命令安装和升级所有从 GitHub 下载的 .deb 包。

---

## 一个熟悉的场景

你在 GitHub 上发现一个好用的工具，比如 RustDesk、bat、ripgrep。作者提供了 `.deb` 包。

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

它自动检测你的系统架构（amd64、arm64、loong64、riscv64），从 GitHub Releases 找到匹配的 `.deb` 文件，下载，安装。

升级更简单：

```bash
ghdeb upgrade
```

一条命令升级所有通过 ghdeb 管理的包。

---

## 它解决了什么

Debian/Ubuntu 的包管理体系很成熟，但有一个盲区：**从 GitHub 直接安装的 .deb 包是"孤儿"**。

它们不在任何 apt 源里。`apt list --upgradable` 看不到它们。`apt upgrade` 不会升级它们。

ghdeb 把这些孤儿包纳入统一管理：

- **scan**：扫描系统中所有孤儿包，识别哪些来自 GitHub
- **list**：列出所有已管理的包和版本
- **upgrade**：一键升级
- **history**：查看每个包的安装/升级历史

---

## 技术细节

几个值得注意的设计：

**架构自动匹配**。不只是 amd64。arm64、loong64（龙芯）、riscv64 都支持。文件名里的 `x86_64`、`aarch64`、`armhf` 都能识别。

**下载容错**。3 次重试，指数退避（2s/4s/8s）。支持断点续传。网络不稳时不会从头再来。

**代理感知**。自动读取 `https_proxy` 环境变量。国内用户配好代理就能用。

**非交互式安装**。设置 `DEBIAN_FRONTEND=noninteractive`，不会出现 debconf 弹窗卡住脚本。

**零配置**。不需要写 JSON、YAML。装上就能用。

---

## 对比

| 工具 | 方式 | 问题 |
|------|------|------|
| ghdeb | 客户端 CLI，零配置 | — |
| github-apt-repos | 服务端 APT 仓库 | 需要基础设施，个人用太重 |
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

支持 amd64、arm64、loong64、riscv64 四种架构的 .deb 包。

---

## 常用命令

```bash
ghdeb install cli/cli              # 安装 GitHub CLI
ghdeb install rustdesk/rustdesk    # 安装 RustDesk
ghdeb upgrade                      # 升级所有
ghdeb scan --deep                  # 深度扫描孤儿包
ghdeb list                         # 列出所有已管理的包
ghdeb info LeisureLinux/ghdeb      # 查看最新版本信息
```

---

## 写在最后

这不是一个改变世界的工具。它只是把一件小事做好了。

Debian/Ubuntu 用户从 GitHub 装 .deb 包是个高频操作。每次五步，累积起来就是时间。ghdeb 把它变成一步。

开源地址：[github.com/LeisureLinux/ghdeb](https://github.com/LeisureLinux/ghdeb)

---

*你在工作中用过这个工具吗？或者你有什么管理 GitHub .deb 包的方法？留言聊聊。*

*下周五我们继续推荐好用的开源工具。关注别错过。*
