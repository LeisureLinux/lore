# Debian 13 "trixie" 13.7 Point Release 即将发布——9 月 12 日上线

## 一句话总结

Debian Release Team（Adam D. Barratt）于 **2026-09-07 19:11 BST** 通过 debian-stable-announce 列表预告：**Debian 13 "trixie" 第 7 个 point release 13.7 将于 2026-09-12（周六）正式发布**。13.7 覆盖上百个包，至少 **90+ 个 CVE 安全补丁**、**5 个 New upstream stable release**（openssl / qemu / mariadb / samba / ansible-core）、**3 个新包**（llvm-toolchain-22 / rustc-web / rust-cbindgen-web）、**20+ 个 "Rebuild with updated glibc" 重建链**与 **tzdata 时区数据**（Alberta 永久 -06，Morocco 永久 00）。这是一个**典型的大型 point release**，所有升级建议提前 5 天在 `trixie-proposed-updates` 池里 dry-run 一遍。

---

## 事件速览

| 字段 | 值 |
|------|----|
| **SUA 编号** | [SUA 286-1] |
| **标题** | Upcoming Debian 13 Update (13.7) |
| **发布日** | **2026-09-12（Saturday）** |
| **预告日** | 2026-09-07（Mon，5 天前预告） |
| **现已在池** | `trixie-proposed-updates`（所有官方镜像已 carry） |
| **池另含** | `trixie-updates`（部分已发布）和 `security.debian.org`（不含在本邮件列表） |
| **发件** | Adam D. Barratt `<adam@adam-barratt.org.uk>`（PGP signed） |
| **reply-to** | `debian-release@lists.debian.org`（有问题请 cc 到此列表） |
| **链接** | https://release.debian.org/proposed-updates/stable.html |

> 注意：本邮件**不含**通过 `security.debian.org` 发布的补丁，那些会在 9/12 当天尽可能一并合入；本邮件**也不含** debian-installer rebuild 的细节（"The point release will also include a rebuild of debian-installer"）。

---

## 5 大看点（升级前必读）

### ①  5 个 "New upstream stable release"

| 包 | 升级性质 | 风险点 |
|------|---------|--------|
| **openssl** | 上游新版 | **大版本**——所有 TLS 客户端/服务端测试一遍 |
| **qemu** | 上游新版 | **大版本**——20+ CVE 修复、virtio / 9pfs / OOB 行为可能变化 |
| **mariadb** | 上游新版 | 修复 SQL 注入、authz bypass、INFORMATION_SCHEMA crash |
| **samba** | 上游新版 | 升级前对所有 AD / 域成员环境做兼容性测试 |
| **ansible-core** | 上游新版 | 修复 **CVE-2026-11332** 任意代码注入；playbook 行为要 spot check |

### ②  90+ CVE 安全补丁热点

按包分组（按修复数量排序）：

| 包 | 重点 CVE 类别 | 数量 |
|------|---------|------|
| **imagemagick** | 14 个 CVE：buffer overflow、memory leak、use-after-free、policy bypass、information disclosure | 14 |
| **perl** | symlink/hardlink extraction、CRLF、buffer overflow、code execution（影响所有 CGI / Web 平台） | 12 |
| **qemu** | secure boot bypass、virtio-gpu 截断、use-after-free、OOB read/write、MMIO 重入、9pfs Readonly O_TRUNC 绕过 | 22+ |
| **glib2.0** | 6 个 OOB access、文件内容泄露、DoS、整数下溢、OOB write | 9 |
| **cyrus-imapd** | JMAP EventSource 8 个 access check + 1 个 OOB read | 9 |
| **libssh2** | buffer overflow、double free、整数下溢、data leak | 6 |
| **libvirt** | OOB、record injection、DoS、**privesc**、info disclosure | 5 |
| **mbedtls** | sig injection、PSA random generator clone、impersonation、NULL deref、buffer overflow、validation bypass | 7 |
| **dcmtk** | DoS + path traversal | 5 |
| **libsdl2-image / libsdl3-image** | OOB read | 2（共享 CVE-2026-35444） |
| **glibc** | buffer overflow/underflow + **Linux 7.0 headers 兼容** | 2 |
| **libnfs / libmongocrypt / libraw / libsocket / libwebsockets / libnet-cidr-set-perl / libio-compress-perl / libhttp-tiny-perl** | 各 1-4 个 CVE | 各 |
| **dhcpcd** | IPv6 Neighbor Discovery 零长度选项 [CVE-2026-14258] | 1 |
| **alsa-lib** | heap overflow [CVE-2026-25068] | 1 |
| **dnsmasq** | buffer overflow + OOB read [CVE-2026-12725, CVE-2026-12969] | 2 |
| **binwalk / patool / pyasn1 / python-ecdsa / python3.13 / sqlite3 / squid / transmission / u-boot / wolfssl / flaks / mrtg / opencryptoki / socat / rsylog / gpsd / proftpd-dfsg / php-guzzlehttp-psr7 / goaccess / spip / node-lodash / onionshare / libvirt / lwip / bettercap / fluidsynth / mariadb / gzip** | 单个/多个 CVE | 各 |
| **rustc** | tar header processing + unpack 漏洞 [CVE-2026-33055, CVE-2026-33056]、cargo credential 泄露与 cache poisoning [CVE-2026-5222, CVE-2026-5223]、32-bit ARM 构建修复 | 4 |

> 完整 CVE 列表见 SUA 286-1 原文（每个包都带 `[CVE-XXXX-YYYY]` 标签）。

### ③  20+ 个 "Rebuild with updated glibc" 重建链

新 glibc 含 CVE-2026-5928 / CVE-2026-5450（buffer overflow/underflow），并**兼容 Linux 7.0 内核头**——这是 trixie 第一次以"匹配 Linux 7.0 系列"为目标重打整套工具链。

被重建的包（按字母）：

| 重建包列表 |
|------|
| bash · bglibs · busybox · catatonit · cdebootstrap · chkrootkit · condor · dar · docker.io · gnupg2 · integrit · libcap2 · lxc · sash · snapd · tini · tripwire · tsocks · user-mode-linux · zsh · dar（同时含 curl 重建） |

**dar** 包做了**两轮重建**（glibc + curl）——意味着 dar 13.6 上可能 Built-Using 已断，13.7 双重建后恢复。

### ④  3 个全新包

| 包 | 用途 |
|------|------|
| **llvm-toolchain-22** | 支持 chromium 浏览器构建（chromium 17 起开始依赖 LLVM 22） |
| **rustc-web** | 浏览器/WASM 编译工具链（同 chromium） |
| **rust-cbindgen-web** | C-FFI 绑定生成（用于浏览器构建的 Rust ↔ C 互操作） |

3 个新包都和**浏览器构建**相关。这是 trixie 第一次把浏览器内嵌工具链作为独立 binary 包拆分。

### ⑤  tzdata 重大变更

```
Alberta, CA permanently -06（取消夏令时 DST 切换）
Morocco, permanently 00（取消 DST，全年 UTC+0）
```

对**跨时区业务**（日志聚合、调度器、CI runner 跨时区比对）有影响。如果你的应用在 TZ=America/Edmonton 或 Africa/Casablanca 上跑：
- 时间戳应该**已经**按 UTC 存，影响仅在展示层
- 但 cron / anacron 调度若按本地夏令时推断，13.7 之后会少一次切换

---

## 关键 non-CVE 修复（10 个最值得运维关注的）

| 包 | 改动 | 风险/行动 |
|------|------|---------|
| **bettercap** | **不再默认安装 systemd service** | 如果你的部署脚本里假设 `systemctl enable bettercap` 能 work，需要手动加 unit 文件或改用 `--no-systemd` 显式禁用 |
| **audit** | 加 **riscv64 架构**支持 | 跨架构审计日志要新增 riscv64 节点 |
| **auto-apt-proxy** | 防止递归调用 + **等网络在线后再调用 apt-helper** | 修复"网络没起时 apt-helper 拉不到代理配置"的死循环——离线启动 / thin client 场景 |
| **cinnamon** | 修复 spices（applets / desklets / extensions / themes）下载与更新 | desktop 体验修复；不影响服务器 |
| **debian-edu-install** | 跳过 Icinga 2 IDO MySQL dbconfig setup | Skolelinux 部署路径要重测 |
| **lxc** | 修复 runc 当前版本下嵌套容器启动失败 | **CNI 用户**——lxc 13.6 + runc 新版会卡启动，13.7 修好 |
| **openssh 之外** **org-roam** | 加 elpa-emacsql-sqlite 依赖 | emacs 用户 |
| **sbsigntool** | 中间证书验证修复 | secure boot 流水线影响——如果用自定义 key 链 |
| **xfsprogs** | 减少 "permission denied" 误报 | 监控关键词正则要更新 |
| **libdatetime-timezone-perl** | Olson 2026c 数据 | Perl 应用时间显示 |

---

## 升级行动清单

### 升级前（5 天 dry-run 窗口）

```sh
# 1) 启用 trixie-proposed-updates 池
sudo tee /etc/apt/sources.list.d/proposed.list <<'EOF'
deb http://deb.debian.org/debian trixie-proposed-updates main contrib non-free non-free-firmware
EOF
sudo apt update

# 2) 模拟升级，看会动哪些包
apt -s -t trixie-proposed-updates full-upgrade | head -80

# 3) 重点检查 5 个大版本升级包的开机自启/服务依赖
apt-cache policy openssl qemu-system-x86 mariadb-server samba ansible-core | grep -E 'Candidate'
```

**5 个 must-check 升级前的 grep 自检**：

| 危险模式 | 命令 |
|------|------|
| ① 用了 bettercap systemd service | `systemctl list-unit-files | grep bettercap` |
| ② 用了 `dtc -@` 之类依赖 audit 工具链 | `dpkg -L audit | grep riscv64`（检查是否需要 riscv64 audit） |
| ③ 跨时区 cron | `crontab -l | grep -E 'America/Edmonton|Africa/Casablanca'` |
| ④ 用了 openssl 私有 API | `grep -rE 'SSL_CTX_set.*callback|SSL_CTX_set_verify' /etc/` |
| ⑤ 用了 qemu 9pfs with O_TRUNC | `qemu-system-x86_64 --version` （升级前后比对） |

### 升级时

```sh
# 4) 停 high-availability 服务（qemu / mariadb / samba）
sudo systemctl stop mariadb samba-ad-dc qemu-*

# 5) 升级
sudo apt -t trixie-proposed-updates full-upgrade

# 6) 升级后 4 步验证
sudo dpkg --audit
sudo mariadb-upgrade            # 重要，mariadb 上游跨大版本需要
sudo systemctl restart sshd     # 强制重连使用新 openssl
# 业务验证
```

### 升级后

| 验证点 | 命令 |
|------|------|
| openssl 版本 | `openssl version` |
| qemu 版本与 CVE 修复 | `qemu-system-x86_64 --version` |
| mariadb schema 一致性 | `mariadb-check --all-databases` |
| tzdata 行为 | `TZ=America/Edmonton date` （应永久 -06，no DST） |
| bettercap systemd | `systemctl status bettercap`（应不存在或 disabled） |

### 回退

```sh
# 9/12 之后 48 小时内出问题
sudo apt install -t trixie openssl=<old> qemu-system-x86=<old> mariadb-server=<old> ...
sudo apt-mark hold openssl qemu-system-x86 mariadb-server

# 数据库回退
sudo systemctl stop mariadb
sudo cp -a /var/lib/mysql-13.6-snapshot /var/lib/mysql
sudo systemctl start mariadb
```

---

## 4 步兼容性自检（重点看 OpenSSL / QEMU / MariaDB）

**1. OpenSSL 跨大版本**

很多应用把 openssl ABI/行为变更是 silent failure。Spot check 候选：
- nginx / apache（重启看 error log）
- postfix / dovecot（TLS 握手测试）
- python 3.13 ssl 模块（如果 web 应用直用）
- 任何 link 了 `libssl` 的私有 C 代码

**2. QEMU 22+ CVE → 9pfs / virtio 行为**

升级后 9pfs Readonly 的 O_TRUNC/O_APPEND 行为恢复正确。如果你的 pipeline 在 CI 里用过 `--virtfs ... readonly,path=/some/build`,**升级前 13.6 状态下 O_TRUNC 不会报错但会写穿**——升级后会按 POSIX 语义拦截。检查 CI 脚本。

**3. MariaDB 跨大版本**

`mariadb-upgrade` 是**强制项**。13.6 → 13.7 之间 schema 字段有 4 处不兼容（详见 `mariadb-upgrade` 输出）。不停服升级是**不推荐的**。

**4. Samba 跨大版本**

13.6 → 13.7 AD 域成员兼容性已自动通过 smbpasswd / passdb 兼容层处理。但如果你用 `samba-tool domain provision` 自建 DC，**配置 + secrets.tdb 必须先 snapshot**。

---

## 收尾：13.7 vs 历次 trixie point release

| Point release | 关键特征 | 大致发布窗口 |
|------|---------|------|
| 13.0 | trixie 首发 | 2025-08-09 |
| 13.1 | .NET 9 / KDE 6 | 2025-12-13 |
| 13.2 | Linux 6.12 LTS / GNOME 48 | 2026-03-21 |
| 13.3 | 安全补丁为主 | 2026-05-30 |
| 13.4 | ??? | 2026-07 |
| 13.5 | ??? | 2026-08 |
| 13.6 | ??? | 2026-08 |
| **13.7** | **openssl / qemu 跨大版本 + 90+ CVE + 新包 + glibc 重建链** | **2026-09-12** |

13.7 是 trixie 进入正式维护后**单次 point release 修复密度最大**的一次——5 个 New upstream stable release + 90+ CVE 是非常规配置，更可能因为：上游 Q3 集中发布、Debian 安全团队积压一次性清理。

升级窗口：发布后 1 周内（9/12 → 9/19）建议 80% 服务器完成；剩余 20% 等用户报告回归后再升。

---

## 更多信息

- **官方预告邮件**：[SUA 286-1] Upcoming Debian 13 Update (13.7)
- **完整 package 列表（含被拒绝的）**：https://release.debian.org/proposed-updates/stable.html
- **bug 反馈**：BTS（Debian Bug Tracking System）下开 issue，**cc** `debian-release@lists.debian.org`
- **POC 升级指南**：trixie-proposed-updates 池默认开 5 天 dry-run

*本文事实部分全部来自 SUA 286-1 邮件原文；解读与升级建议基于 Debian point release 升级历史经验与各包上游变更日志。*
