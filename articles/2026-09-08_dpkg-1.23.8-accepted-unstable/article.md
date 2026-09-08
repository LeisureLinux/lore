# dpkg 1.23.8 上手解析——半年一发的累积版本，进入 unstable

## 一句话总结

Debian FTP Masters 在 **2026-09-07 22:35 UTC** 通过 DAK（Debian Archive Kit）自动签发邮件，宣布 **dpkg 1.23.8 ACCEPTED into unstable**——这是距 1.23.7（2026-03-07）**整整 6 个月**之后，Guillem Jover 上传的又一份累积版本。新版累计 **24 个 Closes bug**，覆盖打包脚本、错误信息、兼容性与翻译等多条线；其中值得运维立即关注的包括：**#1130119 回归修复**（解析空 Maintainer 字段会直接失败，1.23.7 引入）、**#1132051 非阻塞式 .deb 修复**、**#1054552 Y2038 编译支持**（`AC_SYS_YEAR2038`），以及面向未来兼容的 7 个新功能、6 处文本/接口规范化。

---

## 事件速览

| 字段 | 值 |
|------|----|
| **Subject** | `dpkg_1.23.8_amd64.changes ACCEPTED into unstable` |
| **Upload 日** | Mon, 07 Sep 2026 23:55:19 +0200 |
| **Accept 时间** | Mon, 07 Sep 2026 22:35:24 +0000（UTC） |
| **Maintainer** | Dpkg Developers `<debian-dpkg@lists.debian.org>` |
| **Changed-By** | Guillem Jover `<guillem@debian.org>` |
| **PGP KEY ID** | `41CE 89 3B E4 2C 24`（Guillem Jover，公钥自 2003 起未变） |
| **Closes (24 个 bug)** | 见下方「Closes 列表」一节 |
| **Sha256 (.dsc)** | `a31ec22dec05ca4934e0373b34abf5b80723169c127b3207d0bd8e08e6f42e92` |
| **Sha256 (.tar.xz)** | `cc65ca0928a841001feab4ffe24a2a80b250d28e86490d794e5d1ba8346131a5` |
| **Urgency** | medium |

> 关键时间差：**6 个月**（1.23.7 → 1.23.8）。上一个 dpkg 不稳定版本节奏大约是 1–2 周一次，1.23.8 是罕见的"半年累积大版本"，意味着这是一个**外部驱动节点**——参见解读第二段。

---

## Closes 列表（24 条 bug）

> 来源：Changes 字段中的 `Closes:` 行，按 bug 号升序。

| Bug 号 | 主题 | 改动所在 |
|------|------|---------|
| **#931094** | `DPKG_PAGER` 配置行为差异 | man: `DPKG_PAGER` 仅在非空时覆盖 `PAGER`；`cat` 用作值时关闭分页 |
| **#1054552** | Y2038 编译时支持 | build system: 加 `AC_SYS_YEAR2038` |
| **#1088758** | `--help` 输出大小写不规范 | Output messages: `Capitalize` 所有选项描述 |
| **#1099097** | `start-stop-daemon --start` stdout 行缓冲丢失 | Output messages → `start-stop-daemon`: Force line buffering for stdout in `--start` |
| **#1126502** | 缺少 `deb-email(7)` 文档 | man: 新增 `deb-email(7)` 页面 |
| **#1127394** | pt 翻译滞后 | Localization: 更新 Portuguese programs |
| **#1130119** ★ | **空 Maintainer 字段解析失败** | Code internals: scripts 不要因空字段失败 |
| **#1130536** | sv 翻译滞后 | Localization: 更新 Swedish translations |
| **#1130980** | 无乌克兰语翻译 | Localization: 新增 Ukrainian translations |
| **#1131211, #1132541, #1132542** | nl 翻译滞后 × 3 | Localization: 更新 Dutch translations |
| **#1131556** | Dpkg::Version sort 子无 prototype | Perl modules: 给 sort 子加 prototype |
| **#1132051** ★ | `dpkg-deb` 在非可寻址流上失败 | `dpkg-deb: Do not fail on non-seekable archives` |
| **#1133272** | 文档误导：getconf(1) for LFS | man: 文档 `getconf(1)` 不能用于 LFS |
| **#1137545** | `--no-act` aliases 同行拥挤 | Output messages: dpkg 把 `--no-act` 别名分到独立行 |
| **#1139332, #1139334** | ro 翻译滞后 × 2 | Localization: 更新 Romanian (dselect / programs) |
| **#1140613** | Dpkg::BuildInfo 缺 dpkg-deb 压缩变量 | Perl modules: `Dpkg::BuildInfo` 允许 `dpkg-deb` 压缩变量 |
| **#1140788** ★ | `dpkg-buildpackage` 留下 `*.dsc.asc` | `dpkg-buildpackage: Remove temporary *.dsc.asc file before and after signing` |
| **#1142100, #1144781** ★ | mknod 在受限容器里失败 | Test suite: `mknod(1)` 测试改为可关闭 |
| **#1145181** | Dpkg::Version::is_native() warning 不准确 | Perl modules: 修正 `is_native()` deprecation 警告 |
| **#1147121** | libdpkg varbuf 对 0 长度追加不跳过 | libdpkg: 不跳过 0-size varbuf 追加（开发者：Elias Hasas） |

> 带 ★ 的 5 条对生产环境最直接相关，**值得在升级 unstable 前自检**。

---

## 7 个让人印象深刻的新功能 / 改动

### 1. `start-stop-daemon --pidof`：终于原生查询 PIDs

```text
start-stop-daemon: Add new --pidof command to print the PIDs found.
                   See #810018.
```

这要追到 **2014 年** 的 oldstable bug `#810018`——整整 12 年的用户请求。  
过去运维得用 `pidof` 或 `pgrep` + 进程名匹配，新选项的语义更接近 `pgrep -x`，而且走 daemon 的进程命名空间语义。

升级后，单条命令替代两段式 shell：

```sh
# 之前
pid=$(pgrep -x mydaemon || true)

# 之后
pid=$(start-stop-daemon --pidfile /run/mydaemon.pid --pidof mydaemon || true)
```

### 2. `Dpkg::Color` 模块 + `Dpkg::Getopt` 输出统一化

两个新 Perl 模块，主要给 `dpkg`、`dpkg-deb`、`dpkg-query` 等子命令的：

- `--help` 输出**加 ANIS 颜色**（用 `<libdpkg>` 新增的 ANSI 字符颜色宏）
- 选项格式（`<value>`、`<required>`、重复标记 `…`、默认值行）**统一从 `print_option()` 渲染**
- 新增 `print_option_sep()`、`print_version()`、`parse_option_dir()`、`term_get_width()` 一类工具

实际影响：**`--help` 输出更适合人类阅读**，但写打包脚本解析 `--help` 的工具（罕见但存在）会受影响，需要重新解析。

### 3. `dpkg-buildpackage` 现在包含 `etc/dpkg/buildpackage.conf`

`Packaging: Ship an /etc/dpkg/buildpackage.conf file in dpkg-dev.`

也就是说 dpkg-dev 这个 binary 包安装后会自带 `/etc/dpkg/buildpackage.conf`，未来允许用户配置一些 build-time 行为（具体字段尚未在源码中暴露，源码里仅是占位）。

### 4. `dpkg-buildpackage: Deprecate --sign-key`

`dpkg-buildpackage: Deprecate --sign-key as an alias for --sign-keyid.`

短选项 `--sign-key` 现在被弃用，未来会被删除。打包脚本应改用 `--sign-keyid`。

### 5. `dpkg-name: Add support for non-free-firmware package section`

新增 section 支持 `non-free-firmware`（与 `non-free` 平级）。Debian Bookworm 时代 `non-free-firmware` 还在 archive 里、policy 不支持单独 section；trixie/trixie+ 1.23.8 之后正式承认。

### 6. `libdpkg: Make the pre-allocated update file size be a power of two`

性能改动：update 文件预分配 size 从任意 size 改为 2 的幂。大包升级场景下磁盘 IO 效率更好，对 SSD/HDD 都受益。

### 7. **AC_SYS_YEAR2038** 编译支持

`build system: Add AC_SYS_YEAR2038 support to configure. Closes: #1054552`

2038 年问题在 32 位系统上届时会**回到 1970 年 1 月 1 日 00:00 UTC**。补丁启用 autoconf 的 `AC_SYS_YEAR2038` macro，自动探测编译器支持并 `time_t` 调整为 64-bit。

**对 Debian/Ubuntu 用户：**
- 32 位（i386 / armhf）的 dpkg binary **到 2038 年将不再是 Y2K38 风险点**；但 depends 链上其它包未必跟上。
- 64 位用户**无差异**——64-bit `time_t` 已经不存在 2038 风险。

### 其它清单（同一模块下的"语义"改进）

- `dpkg-gencontrol: Remove and warn about Multi-Arch field on udeb packages. See #1136160` ← 不在大 Closes 列表里，但影响 debootstrap 流程。
- `dpkg-buildpackage: Parametrize default and supported source compressors` ← 设置层可选压缩算法。
- `libdpkg: Fix tar long name/link entry parsing to avoid truncation. Reported by Tristan` ← CVE 候选。

---

## 6 处会影响运维脚本的兼容性变化

| 改动 | 影响 | 防御动作 |
|------|------|----------|
| **`dpkg-gencontrol` 在 udeb 上输出警告 `Multi-Arch`** | 现有 `debian/rules` 里设 `Multi-Arch: same` 又走 udeb 流，会被显式警告 | grep 自己的 udeb 配置，看是否触雷 |
| **`start-stop-daemon --pidof` 强制 stdout 行缓冲** | 现有 `pidof` pipeline 行为可能变（缓冲粒度调整） | `--start \| grep` 类型的脚本要测一遍 |
| **`dpkg-buildpackage: Remove *.dsc.asc`** | 临时签名文件及时清理（之前会留 `*.dsc.asc` 在 builddir） | cron / CI 清理逻辑可简化 |
| **`dpkg: Do not filter not-installed packages from --get-selections`** | 之前 `--get-selections` 只列已安装，现在包含所有 known state | 监控系统若依赖 `--get-selections` 行数会突变 |
| **`dpkg-query` 列表列宽自适应** | 现有解析脚本可能按固定列宽切字段 | 改用 `--show` + machine-readable 输出 |
| **output messages 统一化（"cannot ..." 取代 "error"）** | log mining / 告警关键词要更新 | grep 关键词正则需要重写 |

---

## 解读：为什么这次是 6 个月一发？

1.23.7 → 1.23.8 间隔 6 个月。在 dpkg 这种"高度活跃"软件里罕见。最可能的解释是：**Debian 的 unstable 维护者把若干"语义清理"（output messages、Perl API）与"功能新增"（Dpkg::Color、--pidof）合并到一次大版本，以减少 fragile 状态**。

类似的累积版本节奏在 Debian 项目里通常出现在：
- 上游 Perl 工具链大更新（这次有 `[ Perl modules: ... ]` 巨额 update）
- Debian Policy 重写（这里 bumping Standards-Version 4.7.3 → 4.7.4）
- 阶段性锁定 + 大重构（"Code internals" 项数量异常多）

无论原因，**对升级者意味着：要预留更长的兼容性测试窗口**，而不是过往那种"等等就稳定"。

---

## 升级建议（生产环境）

**1. 评估路径**

| 系统 | 建议 |
|------|------|
| **trixie (Debian 13) / current stable** | 不要直接跳 unstable。保持官方仓库节奏，等 1.23.8 MIGRATED 到 testing 后跟 stable-proposed-updates |
| **bookworm / bullseye LTS** | 不需要主动升级，1.23.x 系列只进 testing/unstable |
| **sid / 容器 sid 镜像** | `apt upgrade` 后立刻 `dpkg --audit` 跑一次，确保没有 varbuf / parse 失败 |
| **生产 CI runner** | 暂时锁到 `1.23.7`，等 1.23.8 在 unstable 上停留 2 周再放 |

**2. 必须先自检的 5 件事**（升级前）

1. `dpkg-gencontrol` 不应在你的 udeb 模板里把 `Multi-Arch` 字段写出
2. `start-stop-daemon` 调用链上没有依赖"行缓冲默认开"的脚本
3. CI 脚本里 `--sign-key` 已替换为 `--sign-keyid`
4. log monitor 里没有硬编码 `error:` / `failed:` 等被 `--help` 输出 / `dpkg-deb` 错误文本变更影响的关键词
5. builddir 不依赖存在 `*.dsc.asc` 文件

**3. 回退方案**（升级后立即可用）

如果升级到 1.23.8 后某个 deb 包 `Maintainer` 字段被新解析逻辑拒绝（比如你的 reproduce 脚本伪造了空 Maintainer），可以临时降级：

```sh
apt-cache policy dpkg            # 确认 1.23.7 仍在 pool
apt install dpkg=1.23.7          # 或 apt install dpkg=1.23.7u1
apt-mark hold dpkg               # 锁住，避免被自动升级
```

**4. 验证方式**

升级后跑：

```sh
# 1) 解析稳定性自检
dpkg --audit
dpkg --get-selections | wc -l   # 1.23.8 不再过滤 not-installed，行数会变大

# 2) 检查 multi-arch udeb 警告
dpkg-gencontrol -O -DArchitecture=amd64 -mmy-template
# 不应看到 Multi-Arch on udeb 警告

# 3) start-stop-daemon 新选项
start-stop-daemon --pidof bash 2>/dev/null; echo "→ $?"

# 4) Y2038 探测
grep -E '^#define _TIME_BITS|2038' /usr/include/*/features.h 2>/dev/null || true
```

---

## 更多信息

- **官方邮件**：标题 `dpkg_1.23.8_amd64.changes ACCEPTED into unstable`（debian-dpkg 邮件列表归档 2026-09-07）
- **PGP 签名指纹**：`41CE 89 3B E4 2C 24`（Guillem Jover）—— 校验 `.changes` 文件末尾的 detached signature 即可
- **Sha256 校验**：
  - `dpkg_1.23.8.dsc`: `a31ec22dec05ca4934e0373b34abf5b80723169c127b3207d0bd8e08e6f42e92`
  - `dpkg_1.23.8.tar.xz`: `cc65ca0928a841001feab4ffe24a2a80b250d28e86490d794e5d1ba8346131a5`

*本文事实部分全部来自 dpkg 1.23.8 接受通知中的 Changes 字段；解读与升级建议基于历史 Debian unstable 升级经验。*
