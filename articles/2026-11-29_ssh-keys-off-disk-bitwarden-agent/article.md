---
title: "SSH 私钥别再放磁盘：用 Bitwarden 的 agent 把密钥收进密码库"
date: 2026-11-29
slug: ssh-keys-off-disk-bitwarden-agent
category: 技术/解读
author: FreeLAMP.com
original_source: "jola.dev《You can't afford to keep your SSH keys on disk》（Johanna Larsson，2026-11-23）全文（含原文链接：I deleted all my SSH keys、Bitwarden 导入与 SSH agent 配置、git commit signing 命令）＋ 原文 raw HTML 核对补全 SSH_AUTH_SOCK/IdentityAgent 两步＋ 本号 2026-11-11《macOS Secure Enclave 存 SSH 密钥》文章交叉核对。"
description: "解读 Johanna Larsson 的 SSH 密钥实践：把私钥从磁盘挪进 Bitwarden，由其内置 SSH agent 提供，磁盘上不再留可被恶意代码扫描窃取的私钥。给出完整步骤：Bitwarden 导入既有密钥（含 UI 上传图标的隐藏入口）、启用 SSH agent 与策略、~/.ssh/config 加 IdentityAgent、shell 加 SSH_AUTH_SOCK、ssh-add -L 验证后删磁盘副本；Bonus 是用专用 SSH 密钥做 git commit/tag 签名（gpg.format ssh、user.signingkey、commit.gpgsign）与 GitHub/Gitea/Forgejo 配置。并与 Secure Enclave 方案对比安全性与人体工学，给出风险边界（磁盘残留、agent 转发、密钥备份、vault 锁定间隔）。"
published: true
---

一个自托管的重度用户，把跑着的老服务一个个关掉之后，开始对个人电脑做同样的「减面」：密码管理器用了很久、每个服务都开了 2FA 或 passkey，但有一个角落一直没收拾——**SSH 私钥**。

jola.dev 的 Johanna Larsson 在这篇短文里给了一个直白的判断：以前她把私钥的副本放在密码管理器里「保管」，但**实际用的还是磁盘上那份、由 `ssh-add` 加载进内存的版本**——这意味着私钥随时可能被扫描磁盘的恶意代码外带。她决定把密钥彻底挪离磁盘，选了门槛最低的一条路：**Bitwarden 的内置 SSH agent**。

## 一、为什么是它：安全与人机工程的取舍

作者说得很坦诚：macOS 的 Secure Enclave 方案「听起来 incredibly cool」，但她要的是易用、改动小。她已经在用 Bitwarden、密钥也在里面，于是顺手就把 agent 用上了。

这和本号 11 月 11 日写的那篇《macOS Secure Enclave 存 SSH 密钥》正好构成一组对照：

| 方案 | 安全属性 | 代价 |
|------|---------|------|
| Secure Enclave | 私钥不可导出、每次签名要 Touch ID、设备绑定 | 只能 NIST P-256、不能导入既有密钥、UI 弹窗难看、备份麻烦 |
| Bitwarden SSH agent | 私钥不在磁盘、可随密码库同步备份、既有密钥可导入 | 安全边界依赖密码库；需要点击授权；跨设备靠同步 |

作者本人的体验是：两周就适应了，唯一多出来的摩擦是 Bitwarden 偶尔弹窗要求授权——库解锁时点一下 approve，锁着时用 Touch ID 解锁。她甚至提了两个改进建议：希望 approve 也能用 Touch ID 或回车，而不是必须摸触控板；希望 vault 锁定间隔和密钥授权间隔能分开配置。

## 二、实操步骤

**第一步：把私钥放进 Bitwarden。** 如果还没有，先导入。作者指出 Bitwarden 导入 SSH 密钥的 UI 有点别扭：

1. 在 Bitwarden 里新建一个 SSH key 条目（它会自动生成一对）；
2. 把既有私钥复制到剪贴板，例如 `cat ~/.ssh/id_rsa | pbcopy`；
3. 在编辑表单的 Private Key 字段里，星号遮罩的最右侧有一个**上传图标**，点它；
4. 私钥就导入了，起个好名字保存。

**第二步：启用 SSH agent。** Preferences → App settings (all accounts)，勾选 "Enable SSH agent"，并选择多久要求一次授权。作者选的是「vault 锁定时」再问，并把 vault 锁定间隔设为 4 小时——在安全和便利之间取平衡。

注意：她写的是直接安装的客户端；如果是 App Store 安装的，socket 路径可能不同（原文给了 Bitwarden 社区帖的链接）。

**第三步：让 ssh 走 Bitwarden 的 agent。** 在 `~/.ssh/config` 加：

```
Host *
    IdentityAgent ~/.bitwarden-ssh-agent.sock
```

这是全局设置，任何调用 ssh 的工具都会走这个 agent。

**第四步：让终端里的其他工具也走它。** 在 `.zshrc`（或你的 shell 配置）里加：

```bash
export SSH_AUTH_SOCK=~/.bitwarden-ssh-agent.sock
```

这一步覆盖的是那些需要 SSH agent 但不是 `ssh` 本身的工具，比如 `ssh-keygen`。

**第五步：验证并清理磁盘。** `ssh-add -L` 应该列出所有已加载的密钥。确认密钥都复制进密码管理器之后，就可以删掉磁盘上那份了。

## 三、Bonus：用 SSH 密钥给 git 提交签名

Git 提交里传统上只有作者信息、没有作者身份的证明，伪造某人的 commit 很容易（仓库访问控制能挡住外人，但签名提供的是另一层可验证性）。以前只能用 GPG 密钥，现代 git 支持用 SSH 密钥签名。作者的做法是用**一把专门的密钥只干签名这件事**，这样创建 commit 和 push 需要**两把不同的 SSH 密钥**、各自单独授权。

配置命令（原文按行给出）：

```bash
git config --global gpg.format ssh
git config --global user.signingkey "key:: $(ssh-add -L | grep 'YOURKEYNAME')"
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

在一个仓库里提交后，`git cat-file -p HEAD` 应该能看到签名。要让代码托管平台认这个签名，还得把那把公钥加进去：GitHub 在 `settings/keys` 里添加为 signing key；Tangled 自动信任你配置的 SSH 密钥作为签名密钥；Gitea 和 Forgejo 需要在 `/user/settings/keys` 按指引额外配置信任。

## 四、这套做法的边界：别把它当银弹

文章是一篇个人实践记录，基调是「我用着挺好」，所以有几处值得补一句：

- **它防的是「磁盘上的静态私钥被扫走」**，不是所有攻击。恶意代码仍然可以在你解锁 vault 后、通过 agent 请求签名（这就是授权弹窗的意义），所以「多久问一次」是个真实的策略选择；作者选的 4 小时偏便利，高威胁场景应该更激进。
- **确认备份再删盘上密钥**。她的顺序是「确认 ssh-add -L 列出所有密钥 → 删磁盘副本」，但真正的保险是先在另一台设备或离线介质上验证过能恢复，再删。
- **留意 agent 转发**。`SSH_AUTH_SOCK` 是全局 export 的，任何本地进程都能访问这个 socket；不要把 agent 转发到不可信的跳板机（`ssh -A`），那等于把签名能力交出去。
- **和硬件方案的取舍**。如果你要的是「私钥物理上不可复制 + 每次强制生物识别」，Secure Enclave / FIDO 硬件密钥仍然更强；Bitwarden 方案赢在**能导入既有密钥、能备份、跨设备同步**——本号那篇 Secure Enclave 文章里「不能导入既有密钥、设备绑定」的痛点，正好是它解决的。

## 五、为什么这件事值得做

把 SSH 私钥留在磁盘上，是很多人默认了几年的习惯：生成一把 key、放进 `~/.ssh`、设个 passphrase（或者干脆没设），然后就再也没想过。但在「恶意代码扫磁盘」已经成为常态化威胁的前提下，磁盘上那份静态私钥就是一个长期存在的、可被一次性窃取的资产。

作者的做法本质上是把 SSH 私钥纳入她已经成熟管理的那套体系——密码库 + 主密码 + 2FA + 生物识别解锁 + 集中同步——而不是让它继续做一个游离在安全体系之外的例外。这个思路比具体用哪家产品更重要：**如果你的 secrets 已经有了一个受控的保险箱，就别让私钥睡在走道里**。

## 参考资料

- 原文：https://jola.dev/posts/you-cant-afford-ssh-keys-disk
- 作者提到的《I deleted all my SSH keys》：见原文链接（shelf.cafe）
- 从 1Password 迁移到 Bitwarden：https://jola.dev/posts/migrating-from-1password-to-bitwarden
- Bitwarden SSH agent（App Store 安装路径差异）：https://community.bitwarden.com/t/ssh-agent-in-macos-not-working/82609/8
- 本号相关阅读：《macOS Secure Enclave 存 SSH 密钥：拿不走的私钥与丑弹窗》
