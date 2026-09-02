# Debian 11 "bullseye" LTS 正式 EOL：今天之后没有安全更新了，老系统何去何从？

## 一句话总结

Debian LTS 团队在 2026 年 8 月 31 日正式宣布：**Debian 11 "bullseye" 进入 End-of-Life**。从 9 月起，Debian 不再为 bullseye 提供任何安全更新；一部分包由外部 Extended LTS 接手维护。还没升级的服务器与桌面用户，从今天起就站在"无补丁"的悬崖边上。

---

## 事件时间线

* **2021-08-14**：Debian 11 "bullseye" 正式发布。
* **2024-08-14**：3 年 full support 结束，切换到 LTS 阶段。
* **2026-08-31**：LTS 阶段结束，bullseye 整体 EOL。
* **2026-09 起**：Debian 不再提供安全更新；部分包由 Extended LTS 第三方继续维护。
* **官方建议**：尽快升级到 Debian 12 "bookworm"，并向 Debian 13 "trixie" 滚动。

> **bullseye 生命周期回顾**：5 年总周期 = 3 年 full support（2021-08-14 → 2024-08-14） + 2 年 LTS（2024-08-14 → 2026-08-31）。这是 Debian 标准的"双段式"支持模型，不是 5 年 LTS。

---

## 官方公告核心要点（直译 + 解读）

### 1. EOL 之后会怎样

官方原文一句话：

> Starting in September, Debian will not provide further security updates for Debian 11. A subset of "bullseye" packages will be supported by external parties.

实际含义：

| 类别 | 状态 |
|------|------|
| **Debian LTS 团队** | 不再为 bullseye 提供任何安全补丁 |
| **Debian Security Team** | 不再为 bullseye 发布 DSA |
| **Debian 镜像源** | bullseye 仓库仍然存在，但新安全更新会停 |
| **Extended LTS（ELTS）** | 由第三方（Freexian 等）继续维护部分关键包 |
| **第三方 backports 仓库** | bullseye-backports 不再有官方更新 |

ELTS 不是 Debian 官方项目，是社区出资、商业化运营的延保服务，覆盖包少、价格另算。如果你的业务真离不开 bullseye，得**预算 + 谈判**两条腿走路。

### 2. 接班的 bookworm LTS

公告明确：

> The Debian LTS Team is currently providing security support for Debian 12 "bookworm", the current oldstable release. ... Debian 12 will receive Long Term Support until 30 June 2028.

bookworm LTS 几个关键时点：

| 项目 | 详情 |
|------|------|
| **支持截止** | 2028-06-30 |
| **支持架构** | amd64、i386、arm64、armhf、ppc64el |
| **支持模式** | 5 年总周期（3 年 full support + 2 年 LTS） |
| **当前状态** | current oldstable（已移交 LTS Team） |

注意架构列表比 bullseye LTS 多一个 **ppc64el** —— bullseye LTS 只覆盖 amd64、i386、armhf、arm64。还在跑 PPC64 设备的兄弟，bookworm LTS 是升级后的合法落脚点。

### 3. bullseye 与 bookworm 的 LTS 架构差异

| 架构 | bullseye LTS | bookworm LTS |
|------|--------------|--------------|
| **amd64** | ✓ | ✓ |
| **i386** | ✓ | ✓ |
| ****armhf** | ✓ | ✓ |
| **arm64** | ✓ | ✓ |
| **ppc64el** | ✗ | ✓ |

在升级前务必确认目标架构是否还在 bookworm 的支持名单里。

---

## 对运维实操的直接影响

### 1. 升级路径（官方推荐）

公告里附了 LTS/Using 文档，最干净的路径是分两步：

```
Debian 11 bullseye  ──>  Debian 12 bookworm  ──>  Debian 13 trixie
       (EOL)                  (LTS 收尾)          (current stable)
```

**不建议**直接从 bullseye 跨版本跳到 trixie，会触发 apt 依赖地狱。官方和社区实践都建议"逐级升级"：

```bash
# 1. 升级到 bookworm
sudo sed -i 's/bullseye/bookworm/g' /etc/apt/sources.list
sudo apt update && sudo apt upgrade && sudo apt full-upgrade
sudo reboot

# 2. 验证环境
sudo apt autoremove
# 检查残留 bullseye 配置
dpkg -l | grep -i bullseye

# 3. 之后等 trixie 周期稳定后，再升级到 trixie
```

### 2. 升级前的硬性检查清单

升级前**至少**逐项确认：

* `/etc/apt/sources.list` 和 `sources.list.d/*.list` 全部已归档第三方源（Docker、NodeSource、Ondrej PHP 等）；升完再单独恢复。
* `uname -m` 确认目标架构还在 bookworm LTS 支持名单（amd64 / i386 / arm64 / armhf / ppc64el）。
* 内核关键模块（DKMS、eBPF、wireguard、nvidia）先在测试机验证。
* 数据库 / 应用栈版本兼容性 —— bullseye 默认 PostgreSQL 13、PHP 7.4；bookworm 默认 PostgreSQL 15、PHP 8.2，跨度较大。
* 备份快照 + 救援盘可启动（万一 GRUB 挂了还能进 recovery）。
* 计划停机窗口 —— 关键业务至少留 4 小时缓冲。

### 3. 不能立即升级的业务系统怎么办

现实里总有不能立即升级的场景：内嵌老版本 glibc 的二进制、定制内核模块、跟硬件厂商锁版本的老 SAP/Oracle、没维护方签字的工控机。这种情况有三条退路：

| 退路 | 适用场景 | 风险 |
|------|---------|------|
| **购买 Extended LTS** | 关键生产、无法升级 | 第三方 SLA、覆盖包少、预算要批 |
| **网络隔离 + 访问控制** | 内网、非面向公网 | CVE 不会因为隔离而消失，被突破是早晚的事 |
| **容器化迁移** | 可重新打包的应用栈 | 把"老系统"隔离在容器里，宿主机升 bookworm | 

注意：把"暂时不动"伪装成"低优先级"是**最差的选择**。bullseye 一旦出远程 RCE 级别 CVE，且没有补丁，资产就只能在隔离网里硬撑到出 CVE 后才能被发现 —— 这是慢性自杀。

### 4. 时间窗口已经很紧

bookworm LTS 还剩 **22 个月**（到 2028-06-30）。trixie 预计 2028 年中才进入 LTS 阶段（按 3+2 模型推算）。也就是说：

> 从今天起到下一个稳定 LTS 真正接管，中间有大约 22 个月的"换挡期"。

拖得越晚，可选升级路径越窄。建议把 bullseye 升级到 bookworm 当作**未来 3-6 个月内必须完成的事**，而不是"下半年再说"。

---

## Debian LTS 团队想招人

公告结尾提了一句：

> If you rely on Debian LTS, please consider joining the team, providing patches, testing or funding the efforts.

老实说，Debian LTS 是个几乎全靠志愿者撑着的高难度项目 —— 给老版本反向移植上游安全补丁，工作量比写新包还大。Freexian 等商业 ELTS 在接外包，企业用户出钱能解决一部分，但**核心 LTS 团队仍然人手紧张**。

如果你或你的团队从 Debian LTS 里长期受益，能做的几件事：

* **提交补丁**：上游 CVE 来了之后做反向移植，发到 `debian-lts@lists.debian.org`。
* **测试**：在 LTS/Development 页有"测试包"队列，新补丁需要人手跑回归。
* **资金**：通过 LTS/Funding 页对接 Freexian 等赞助渠道。
* **架构维护**：某些架构（特别是 non-amd64）的回归测试长期人手不够。

一句话：这条基础设施靠着免费劳动在维持，能搭把手就搭。

---

## 写在最后

Debian 11 "bullseye" 这五年的生命周期，是社区驱动 LTS 的一个典型样本：3 年 full support 把上游主流版本吃透，2 年 LTS 接力把重要 CVE 修掉，最后干净退场让位给下一代。它不像商业 Linux 的 10 年付费 LTS 那么长，但**成本也是零**。

对还在 bullseye 上的系统来说，今天就是**决策日**。三条路摆在面前：升级到 bookworm、买 ELTS、还是赌一把"反正没人攻击我"。无论选哪条，都得现在定 —— 不然下个月 CVE 公告一发，就不是你能选的了。

---

## 参考文献

1. Debian Project. *Debian 11 Long Term Support reaches end-of-life*. 2026-08-31. https://www.debian.org/News/2026/20260831
2. Debian Wiki. *LTS/Extended*. https://wiki.debian.org/LTS/Extended
3. Debian Wiki. *LTS/Using*. https://wiki.debian.org/LTS/Using
4. Debian Wiki. *LTS/Development*. https://wiki.debian.org/LTS/Development
5. Debian Wiki. *LTS/Funding*. https://wiki.debian.org/LTS/Funding
6. Debian. *Security support for Bookworm handed over to the LTS team*. 2026-07-12. https://www.debian.org/News/2026/20260712
7. Debian. *Debian 11 "bullseye" Release Information*. https://www.debian.org/releases/bullseye/

*注：本文事实部分全部来自 Debian 官方公告与 Debian Wiki；解读与运维建议基于通用 Debian 升级实践。*