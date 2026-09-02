# systemd 262-rc1 发布：嵌入兜底 unit、PID 1 静态容器、TPM/SEV-SNP/TDX 全栈机密计算加码

## 一句话总结

systemd 262-rc1 进入发布候选前测试。这是一次**同时改启动路径、改调度语义、改安全栈**的全栈版本。三块最硬的改动：**PID 1 现在可构建为单文件静态二进制**（专为极小容器设计）、**manager 内嵌一组兜底 unit**（容器没装 unit 文件也能起 basic / shutdown / reboot）、**机密计算栈从 TPM 一路打到 vmspawn 的 TDX / SEV-SNP**。其他重要项：`NUMAPolicy=` 新增 `preferred-many` 和 `weighted-interleave`；`RestartRandomizedDelaySec=` 把同步故障重启"撕开"；TPM 凭证强制绑 SRK 防 MITM 偷取；`cryptenroll` 新增 first-boot wizard；`systemd-coredump` 走 Linux 6.17 内核 coredump socket 协议；journald 的 FSS 密封从 libgcrypt 迁到 OpenSSL。

---

## 事件速览

* **发布版本**：**systemd 262-rc1**（首个 rc）
* **原始公告**：Phoronix 报道 + systemd GitHub release notes (`v262-rc1`)
* **破坏性变更**：多项 Meson 选项移除、`Type=notify-reload` 协议更严、`UnsetEnvironment=` 顺序变更、`journalctl -F` 与过滤器互斥、`RateLimit` 时钟改 `CLOCK_BOOTTIME`
* **测试范围**：覆盖 manager / credentials / systemctl / firstboot / boot+stub / hostnamed / networkd / journald / coredump / resolved / timesyncd / udevd / homed / cryptsetup+cryptenroll / repart+dissect / nspawn / vmspawn / report / TPM / pcrlock / tmpfiles / machined
* **下一步**：跟踪 rc2 / rc3 → 正式版 262

---

## 这篇文章的视角

systemd 262-rc1 改动密度非常高，原文 release notes 长篇累牍。本文**不逐行搬运**，按下列主线**重新组织**，并把对运维、SRE、平台工程师**最有用的部分**拎出来：

1. **PID 1 与启动路径**——单文件静态多调用二进制、嵌入兜底 unit
2. **调度语义**——NUMA 新值、`RestartRandomizedDelaySec=`、`ActivatingConcurrencyMax=`
3. **API 扩展**——`EnqueueUnitJobMany()`、StartTransient 扩展、Varlink 接口扩张
4. **机密计算与可信启动**——TPM SRK 绑死、cryptenroll first-boot、Argon2id PIN、NvPCR 重写
5. **文档交换 / 数据完整性**——dm-verity over LUKS、journald 从 libgcrypt 迁到 OpenSSL、Live Update Orchestrator
6. **杂项与人机界面**——hostnamed 通配符、`systemd.firstboot=headless`、vmspawn TDX、SEV-SNP initrd 凭证传递
7. **兼容性与坑**——必须知道的破坏性变更

---

## 一、PID 1 与启动路径：极小容器友好

### 1. PID 1 现在可以是"单文件静态多调用二进制"

```
Meson 配置:
  --default-library=static --prefer-static
  -Dbuild-static=true
  -Dsystemd-multicall-binary=true
```

systemd 一直是个**庞然大物**：unit 文件、NSS、dlopen 动态库一应俱全。在**通用发行版**这是优点；在**极小容器镜像**是负担。262 把这条路打通了：

* **静态链接**所有可选库（不再 dlopen）
* **不走 NSS**，直接读 `passwd` / `group` 文件
* 整个 PID 1 + executor 是个**单文件多调用二进制**（multicall），各子命令（systemctl、journalctl、systemd-run 等）都打到同一个 .bin

对**distroless / scratch / alpine-micro** 风格的容器镜像特别有用——systemd 终于能像 busybox 一样"一个文件搞定一切"，而不必把 50 个 ELF 全塞进镜像层。

### 2. manager 内嵌基础 unit 文件

```
manager 现内嵌: basic.target / sysinit.target / multi-user.target /
reboot.target / shutdown.target / systemd-poweroff.service ...
```

* **磁盘上的 unit 文件仍优先**——磁盘有的用磁盘的,磁盘没有才用内嵌的。
* **关键收益**:容器里**没装任何 unit 文件**,systemd 也能起 basic / shutdown / reboot 链路。
* 这条改动把 systemd 当 PID 1 跑容器的"开箱即用"门槛大幅降低。

### 3. udevd 跑在 sibling cgroup

systemd-udevd 现在把 worker 进程放进一个**独立的 sibling "workers" cgroup**,与 manager 进程分开。在支持 `cgroup.kill` 的内核上,udev 可以**原子地一次性清掉全部残留 worker**——以前 udev 残留 worker 是 initramfs / early boot 阶段一个反复出现的"小尾巴"问题。

---

## 二、调度语义:把同步故障"撕开",把 NUMA 调细

### 1. `RestartRandomizedDelaySec=` —— 防重启风暴

```ini
[Service]
Restart=on-failure
RestartSec=2s
RestartRandomizedDelaySec=10s
```

旧行为:`RestartSec=2s` 之后**严格 2 秒**重启——多个单元一起挂时,**会同时拉起来**——典型的 thundering herd。262 加了一个**均匀分布的额外延迟**(0 到该值之间均匀采样),把启动时间撕开。

适用场景:

* 同质化容器编排——节点故障恢复时几百个副本一起重启
* 微服务健康检查假阳——多副本同时被判 fail 又同时被拉起
* 数据库主从切换后旧主批量回切

### 2. Slice 的 `ActivatingConcurrencyMax=`

```ini
[Slice]
ActivatingConcurrencyMax=10
```

限制**该 slice 层级下"activating 状态"的并发数**。剩下的激活请求**排队**,前面腾出槽位再启动。这是为大规模 systemd 部署准备的——以前 slice 没有"并发上限",只能靠 RestartMaxStartTime 等机制做粗控。

### 3. `NUMAPolicy=` 新增 `preferred-many` 和 `weighted-interleave`

| 值 | 内核要求 | 用途 |
|----|----------|------|
| `preferred-many` | Linux ≥ 5.15 | 优先多个 NUMA 节点,兼顾延迟与带宽 |
| `weighted-interleave` | Linux ≥ 6.9 | 按内核 sysfs 文件中配置的权重轮询 |

过去 NUMAPolicy 只支持 `default` / `interleave` / `preferred` / `bind` / `local` 几档。262 把内核新加的 weighted interleaving 直接挂上 systemd 接口——对**延迟敏感但内存占用大的服务**(in-memory KV、内存数据库)很值。

### 4. Rate-limit 时钟换 `CLOCK_BOOTTIME`

sd-event 的 rate-limit 计时,以及 `StartLimitIntervalSec=` 等 manager 计时,**改用 CLOCK_BOOTTIME** 而不是 CLOCK_MONOTONIC。

含义:**系统挂起的时间算进 rate limit 窗口**。升级后,旧的 rate-limit 状态会比预期**略早**一点过期(因为存储的时间戳是用旧时钟、比较时却用新时钟)。多数情况影响小,但**状态化部署**要意识到。

---

## 三、API 扩展:D-Bus 与 Varlink 双线扩张

### 1. `EnqueueUnitJobMany()` —— 一次排多个作业

D-Bus 新增 `EnqueueUnitJobMany()`,**一个事务**里排多个 unit 的 start/stop/restart/reload。**事务里指定顺序后,ordering 依赖按命名解析**(不按命令行顺序)。

systemctl 和 portablectl 在 manager 支持时会优先用新方法——老的 manager 自动 fallback 到 per-unit 调用。

对**编排工具**(Ansible、Salt、Nomad、Pulumi 自定义 driver)在批量操作大量服务时,这一改能**显著减少 D-Bus round trip**。

### 2. StartTransient 接受更丰富的属性

`io.systemd.Unit Varlink StartTransient()` 现在接受:

* 更多 `Exec*` 上下文(users/groups、credentials、root images/directories、namespace paths)
* **沙箱类布尔参数**
* `UMask=` / `OOMScoreAdjust=` / `CollectMode=`
* **从 Varlink 调用本身传入 stdin/stdout/stderr fd**

相当于 transient unit 越来越接近"完整 unit",适合做**一次性沙箱执行**的场景。

### 3. SecureBits 新值

`SecureBits=` 识别:

* `no-cap-ambient-raise`
* `exec-restrict-file`
* `exec-deny-interactive`
* 各自 `-locked` 变体

把 kernel securebits flags 一对一映射出来,容器安全策略描述更直接。

---

## 五、机密计算与可信启动:这一版的"重头戏"

systemd 在 262 把 TPM、cryptsetup、cryptenroll、pcrlock、vmspawn 这一整条**机密计算栈**全部更新。

### 1. TPM 凭证强制绑 SRK —— 防 MITM 偷取

> TPM-sealed credentials are now pinned to the TPM's SRK. This prevents MITM interposer attacks from stealing the decrypted credentials by ensuring that communication with the TPM is protected by a private key only known to the same TPM the credential was sealed to.

含义:TPM **密封凭证的解密通信,改用只属于该 TPM 的私有 key(基于 SRK)** 保护。中途插入 MITM TPM 仿器偷走解密结果的攻击**不再可能**。

附带好处:TPM owner hierarchy 用 PIN 锁着也能用 TPM-sealed credentials——以前必须 PIN 解锁才能用。

**注意兼容性**:**新策略下铸造的 TPM-bound 凭证,旧 systemd 不识别**。但**反向兼容**——262 仍能解旧凭证。**升级单向安全**。

### 2. systemd-cryptenroll 增 first-boot wizard

```
systemd-cryptenroll --firstboot
```

推出新 unit:

* `systemd-cryptenroll-firstboot.service`
* `systemd-cryptenroll.socket`(socket-activated)
* `systemd-cryptenroll@.service`
* `io.systemd.CryptEnroll` Varlink API

新选项:`--firstboot`、`--unlock-empty`、`--unlock-headless`、`--prompt-suppress=`、`--chrome=`、`--mute-console=`。**专做首次开机的全自动 / 半自动磁盘加密 enroll**——云镜像、IoT 边缘、Ceph 存储节点都能直接跑。

### 3. Argon2id 强化 TPM2 PIN

```
systemd-cryptsetup / cryptenroll:
  --tpm2-with-pin=yes          # 新默认走 Argon2id
  --tpm2-with-pin=direct       # 旧的 PBKDF2 兼容模式

  --tpm2-argon2id-memory=
  --tpm2-argon2id-iterations=
  --tpm2-argon2id-parallelism=
  --tpm2-argon2id-iter-time=
```

**只有 TPM 被攻陷还不行**——还要 PIN——两个一起被偷才能解出卷密钥。把 TPM-sealed 凭证从"单因素依赖 TPM"升级到"双因素"。

### 4. NvPCR 重写:不再靠 anchor secret

NvPCR(由 systemd 管理的非易失性 PCR)**改成基于 PCR policy**——只能由 initrd 阶段的初始 extend 写入,**不再依赖被 TPM 密封的 anchor secret**。

配套要求:

* 所有 NvPCR 定义(`/usr/lib/nvpcr/*.nvpcr`)必须装进 UKI
* UKI 必须含用 initrd 阶段绑定的签名 PCR policy,带 `"initrd"` policy reference
* 装配命令:**`ukify --sign-initrd-pcrs ...`**

**兼容路径**:旧 NvPCR 自动升级,旧的 anchor secret 自动从 `/var/lib` 与 ESP/XBOOTLDR 清除。

这是把 **measured boot 信任链**从"靠 secret 锚定"迁到"靠签名 + 阶段策略锚定"的标准化迁移。

### 5. dm-verity over LUKS

systemd-repart / systemd-dissect 262 引入 **DDI 模式**:

```
data partition = Encrypt= + Verity=data
  → 先 LUKS2 密文 → 再在上面建 dm-verity 元数据
```

* **外层是 dm-verity(真实性)**,**内层是 LUKS2(机密性)**。
* 镜像既防篡改、又不可读——适合**不可信边缘节点**拉镜像部署。

### 6. vmspawn 加 Intel TDX

```
systemd-vmspawn --coco=tdx          # 新增
systemd-vmspawn --coco=sev-snp      # 已支持
```

* TDVF / OVMF feature requirements 自动验证
* `--secure-boot=yes` 可选启用带预置密钥的固件——机密 VM 固件**没有可写 NVRAM** 给运行时 enroll 用,**必须靠预置密钥**

对**云厂商 + 机密 VM 部署**关键。

### 7. SEV-SNP 通过 initrd 凭证传递

```
systemd-vmspawn --coco=sev-snp:
  → credentials 通过 cpio 追加到 initrd 的 /.extra/system_credentials/
```

* 凭证纳入 SEV-SNP **launch measurement**(可证明、可审计)
* **不提供机密性**——host / VMM 仍能看到明文
* **要求 guest 内 systemd 支持从 /.extra/system_credentials/ 导入凭证**——262 内置支持

这是**把 initrd 作为凭证信任根**的标准化路径,**完全在 launch measurement 范围内**——审计员可以重放测量,确认 launch 时确实有这套凭证。

### 8. systemd-cryptsetup 移除旧 PCR-bank 选项

`tpm2-measure-bank=` crypttab 选项**废弃**,不再生效。新方式走 systemd-pcrextend 的 varlink 调用,**自动选所有合适的 TPM2 PCR banks**(包括 SHA384 / SHA512)。

TPM 那边也跟了:**PCR bank 优先级**改成 SHA256 → SHA512 → SHA384 → SHA1,SHA384/512 只在 SHA256 不可用时启用。

### 9. 简表

| 模块 | 262 关键改动 | 受益方 |
|------|--------------|--------|
| TPM 凭证 | 绑 SRK 防 MITM | 所有 TPM 用户 |
| cryptenroll | first-boot wizard + Varlink API | 云镜像 / IoT / 自动部署 |
| cryptsetup PIN | Argon2id 取代 PBKDF2 | 全部 TPM2 加密卷 |
| NvPCR | 改用 PCR policy + UKI 签名 | 可信启动链 |
| dm-verity + LUKS | 分层加密 + 验证 | 不可信边缘节点 |
| vmspawn TDX | `--coco=tdx` | 云厂商 / 机密 VM |
| SEV-SNP 凭证 | initrd `/.extra/system_credentials/` | 机密 VM launch 审计 |
| pcrlock | `--strict=` + 新 Varlink 方法 | UKI 策略强制 |

---

## 六、文档交换 / 数据完整性

### 1. Live Update Orchestrator(LUO)支持

```
service unit:
  LUOSession=yes  → 让 systemd 创建 LUO 会话,通过 fd store 传给主进程
```

* Manager 在 D-Bus / Varlink 上**暴露 KExecsCount** 与**当前 / 上次 shutdown 时间戳**(内核支持时)
* `systemd-analyze time` 在 LUO 内核下会报告 **kexec / live-update timing**

对**永远在线 + 不能停的服务**(电信、银行核心交易、关键数据库)——LUO 是 kexec 的接班人,**在 Linux 7.x 内核**下逐步成熟。

### 2. `RestrictFileSystemAccess=` 接受 dm-verity 签名的 overlayfs

旧行为:overlayfs 一律拒绝执行。

新行为:**底层 file data 落在 dm-verity 签名 + 验证过的 fs 上**的 overlayfs,**允许执行**——只拒绝写在 writable upper layer 里的文件。需要 Linux ≥ 7.2,老内核维持旧的"全拒绝"行为。

对**不可变 OS / 边缘节点 / auto-update 容器**很关键——OS 层签名了,容器根 fs 跑在 overlayfs 上,**启动脚本可以正常执行**,同时**安全审计能验明底层 file data 完整性**。

### 3. ukify inspect --json 输出结构变化

```
重复的 PE sections 现在按数组输出
multi-profile UKI 引入 _profiles 数组
```

**消费 ukify inspect JSON 的工具**(比如镜像构建流水线、验证器)**必须更新**——以前假设每个 section name 出现至多一次的逻辑不再成立。

### 4. systemd-coredump 走 Linux 6.17 内核 coredump socket 协议

Linux 6.17 引入了新的内核 coredump socket 协议——`/run/systemd/coredumpd/kernel` 监听,**`systemd-coredump-register.service` 通过 `kernel.core_pattern` 注册 socket**。

* 老内核走旧的 per-coredump `@.service` 路径,**继续支持**
* 改 `coredump.conf` 后**需要 reload `systemd-coredumpd.service`**
* 自定义 `kernel.core_pattern` 的部署必须**停 / mask `systemd-coredump-register.service`**

### 5. journald FSS 迁到 OpenSSL

journal sealing(FSS,Forward Secure Sealing)的实现从 libgcrypt 迁到 OpenSSL。**libsystemd 不再 link libgcrypt**。

* sealed journal 文件**没 sealing 支持时仍能读**(只跳过 seal tag 验证)
* 减少一个重量级依赖——对**静态构建 / 边缘镜像**意义重大

### 6. systemd-repart 的 SOURCE_DATE_EPOCH

`SOURCE_DATE_EPOCH` env 在 populating images 时**生效**:从源 tree 拷文件的时间戳 clamp 到该 epoch,该值会**传给 mkfs / mtools**。

`--offline=yes` + 配套 fs 工具可以达到**逐字节可复现**的镜像构建。**容器镜像 / IoT 镜像 / OTA 更新包**的 CI 流水线可以彻底告别"diff-only" 验证。

---

## 七、其他重要模块

### 1. systemd-firstboot headless 模式

```
systemd.firstboot=headless
```

* 不弹任何交互提示
* 但仍做**全自动的非交互配置**(选唯一 locale、按 credential 应用设置)
* 给**无人值守安装**用——PReseed / cloud-init 之后的进一步统一化路径

### 2. hostnamed 通配符展开

`/etc/hostname`、`systemd.hostname=`、`firstboot.hostname`、`system.hostname=`,以及 `systemd-firstboot --hostname=`,支持确定性通配符:

* `?` → 展开为 machine-id 派生的 hex 字符
* `$` → 从编号词表选稳定的单词

示例:`host-?` → `host-1f2c3a4b`;`router-$` → `router-helios`。

`hostnamectl tags` 现在接受 `+TAG` / `-TAG`——原子增减,**不替换整张表**。`[Match]` 增加 `MachineTag=`,可匹配 machine tag。

### 3. networkd 的 `ProxyNeighbor=`

`.network` 文件 `[Network]` 段里 `IPv6ProxyNDPAddress=` **重命名为 `ProxyNeighbor=`**(老名仍接受,标弃用)。

新名同时支持 IPv4 / IPv6 加入内核的 neighbor proxy 表——`ProxyNeighbor=` 是 IPv4 ARP proxy 与 IPv6 NDP proxy 的统一入口。

### 4. udev 容忍无效普通属性

sd-device 与 systemd-udevd 现在**忽略无效的 ordinary kernel 属性**,不再因为一条普通属性错误**整条 uevent 拒收**。**required 属性与 typed 属性仍严格**。

这个改动的现实意义:某些 BIOS / 固件会发一些不规范的属性,过去会让整个设备 uevent 失败、设备不被识别——u盘、网卡都遇到过。262 修掉这块反复出现的痛点。

### 5. systemd-tmpfiles 改严校验

* 对**不使用 argument 字段**的 tmpfiles.d 行类型,**非空 argument 字段**现在**直接 reject**(以前只是警告后忽略)
* `r` / `R` 类型在 `--clean` 时**遵守 age 字段**
* `%D` specifier:**系统模式** → `/usr/share`,**用户模式** → `$XDG_DATA_HOME`

**注意**:**这是兼容性破坏**——下游发行版必须审一遍自己的 tmpfiles.d snippet,**非空字段填错会被 reject**。

### 6. `systemd-vmspawn` 鼠标滚轮 + `--coco=` 同时支持 TDX / SEV-SNP

详见上节"机密计算"。

### 7. systemd-report 加签名后端

```
systemd-report sign:
  --sign=no             # 不签名
  --sign=best-effort    # 能签就签,签不了也不报错
  --sign=require-one    # 至少一个签名
  --sign=require-all    # 所有 signer 都必须成功
```

签名后端走 Varlink,链接在 `/run/systemd/report.sign/`。带签名的 report 输出 JSON-SEQ:report 对象 + 每份签名一个对象。

适合把 systemd-report 当**远程健康 / 安全报告入口**接 SIEM / 合规存储的场景。

### 8. systemd-pcrlock `--strict=` 与新 Varlink 方法

`pcrlock predict / make-policy` 加 `--strict=`:**严格模式**下,如果某个 PCR 进不了 predict / policy,**直接报错**,不再静默丢掉。

Varlink API 加 list / generate / remove 方法,覆盖 firmware code / firmware config / Secure Boot policy / Secure Boot authority 测量。

### 9. systemd-resolved 新方法

`io.systemd.Resolve.Monitor` Varlink 接口加 `FlushCaches()`、`ResetServerFeatures()`。resolvectl 对应命令在 manager 支持时优先用新方法。

### 10. systemd-timesyncd 用 resolved 的 Varlink API

```
NTPNTP server 解析走 systemd-resolved 的 Varlink API
  → 本地钟同步前抑制 DNSSEC 校验
  → resolved 不可用时 fallback 到 getaddrinfo()
  → IPv6 disabled 时跳 AAAA
```

---

## 八、必须知道的破坏性变更

这一节是**给 SRE / 平台 / 打包方**看的——升级前请评估。

### 1. Meson 选项移除

移除的选项(对应功能保留,但用其他选项启用):

* `-Dlibiptc=`(v259 起已弃用)
* `-Dlibidn=`
* `-Drc-local=`
* `-Dsysvinit-path=`
* `-Dsysvrcnd-path=`(v260 起已弃用)

### 2. 静态 / 多调用构建选项改名

```
旧: -Dbuild-executor-shared=single   → 新: -Dsystemd-multicall-binary=true
旧: -Dstandalone-binaries=           → 新: -Dstandalone-binaries=<csv pattern>(可列表)
```

老的 true/false 仍接受,但**已弃用**。老的 Meson build 目录**可能要重建**。

### 3. `Type=notify-reload` 服务协议更严

发 `READY=1` 时,必须**捕获或阻塞 `ReloadSignal=`**——否则启动报协议错误。

旧行为:这种服务仍能起,但**后续 reload 可能用默认动作终止服务**(自己作死)。

新行为:**协议错误直接失败启动**,逼迫你显式处理 ReloadSignal。

### 4. `UnsetEnvironment=` 顺序变更

现在**在 `ExecStart=` 等命令行的环境变量展开之后**应用。

含义:`UnsetEnvironment=` 列出的变量**仍可在 `Exec*=` 命令行里用 `$VAR` 引用**(展开时变量还在),**最终传给进程的 env 里没有**。

依赖"整词 `$VAR` 引用会被丢掉"的行为要改——以前丢,现在不丢。

### 5. `journalctl -F` 与过滤器互斥

`-F / --field` 现在**与 `unit / boot / time / cursor / grep` 过滤器互斥**。

旧行为:过滤器**静默忽略**。

新行为:直接 reject。

依赖"先 `-F` 再 `grep`"脚本要改成显式两步:`journalctl -F` 列出字段,**另跑 `journalctl --grep ...` 查条目**。

### 6. systemd-sysupdate 单元重命名

```
systemd-sysupdate.service         → systemd-sysupdate-update.service
systemd-sysupdate.timer           → systemd-sysupdate-update.timer
```

**保留兼容 symlink**——老名字仍能用,但 alias 用旧名的 unit / timer / override 文件**要更新**。同时为**新 `systemd-sysupdate@.service` (varlink activation)** 腾出空间。

### 7. systemd-repart 的 MakeSymlinks= 展开 `%`

`%` 字符 specifier 在 symlink **target** 里也展开(以前只在 source)。如果你自定义 MakeSymlinks 用了字面 `%`,**会变展开结果**——这是 specifier 设计修正,大概率影响小,但要审。

### 8. systemd-repart 默认 CoW 行为

默认**不强制关闭 CoW**,改由 fs / 父目录策略决定。新增 `--cow=auto | yes | no`。

旧默认(强制 NOCOW)**要走 `--cow=no` 显式保留**。

### 9. TPM-sealed 凭证单向兼容

新策略下铸造的 TPM-bound 凭证**旧 systemd 不识别**——但**反向**(262 解旧)成立。**升级单向安全**,但**混合集群**要统一。

### 10. OpenPGP keyring lookup 默认合并

```
default: /usr/ (vendor keyring) + /etc/ (local keyring)
```

依赖"只用 /etc/ 来排除 vendor trust"的系统**必须显式设 $SYSTEMD_OPENPGP_KEYRING**。

### 11. ukify inspect --json 输出结构变更

见上节"文档交换"。

### 12. NvPCR 需要 UKI 集成

见上节"机密计算"。

---

## 九、给不同角色的快读表

| 角色 | 重点关注 |
|------|---------|
| **容器 / 镜像打包** | PID 1 单文件静态二进制、嵌入兜底 unit、journald OpenSSL 迁移、SOURCE_DATE_EPOCH 可复现构建 |
| **调度 / SRE** | `RestartRandomizedDelaySec=`、`ActivatingConcurrencyMax=`、`EnqueueUnitJobMany()`、StartTransient 扩展 |
| **内核 / 性能** | NUMAPolicy `preferred-many` / `weighted-interleave`、CLOCK_BOOTTIME rate-limit |
| **TPM / 可信启动** | SRK pinning、Argon2id PIN、NvPCR 重写、ukify `--sign-initrd-pcrs`、pcrlock `--strict=` |
| **机密 VM** | `--coco=tdx`、`--coco=sev-snp` + initrd 凭证、dm-verity over LUKS |
| **Ceph / 存储** | cryptenroll first-boot wizard + Varlink API、自动 enroll 流程 |
| **边缘 / IoT** | cryptenroll `--unlock-headless`、`--prompt-suppress=`、`--mute-console=` |
| **桌面 / 多语言** | hostnamed 通配符、Notebookbar 改进(本版本无大变化) |
| **打包 / 发行版** | Meson 选项移除、tmpfiles.d 严格校验、TPM 凭证单向兼容、OpenPGP keyring 默认合并 |

---

## 十、写在最后

systemd 262-rc1 是一份**该有的地方全有**的发布。**容器路径**终于能做单文件 PID 1,**调度语义**补齐了"防 thundering herd"与"slice 并发上限",**机密计算栈**把 TPM / cryptsetup / vmspawn / dm-verity 一路打通,**API** 在 D-Bus 与 Varlink 双线扩张,**release notes** 长度本身就是工程规模的说明。

值得**赞同**的两点:

1. **从"靠 secret 锚定"迁到"靠签名 + PCR policy 锚定"**——NvPCR 的重写是 measured boot 信任链的一次范式升级,让 UKI 把 initrd 阶段绑定为信任根,**长期正确**。
2. **dm-verity over LUKS**——双层(真实性 + 机密性)在 systemd-repart 一站式完成,**distroless 镜像 / OTA 更新包**从此可以走"既不可信边缘节点拉镜像,又保证机密性"的标准化路径。

值得**留意**的两点:

1. **Meson 选项重命名 + tmpfiles.d 严格校验 + UnsetEnvironment 顺序变更**——这几个破坏性变更**打包方必须逐条审**。系统跑起来可能没问题,但**debuginfo / custom builds** 容易踩坑。
2. **TPM-sealed 凭证单向兼容**——**新版本铸造的旧版不认**,对滚动升级是单向安全的,对混合集群(新旧 manager 同时跑)要**确保在 leader 上完成升级**。

按 systemd 的节奏,**rc1 → rc2 / rc3 → 正式版**大约还需要几周。**生产环境**可以等 262.2 / 262.3 之后再上;**测试环境 / staging** 现在就该开始跑,数这次改动的颗粒度,生产前一定有几条要 hit。

---

## 参考文献

1. Phoronix. *systemd 262-rc1 Released*. 2026-08-26. https://www.phoronix.com/news/systemd-262-rc1
2. systemd Project. *CHANGES WITH 262 in spe (v262-rc1)*. GitHub Releases. https://github.com/systemd/systemd/releases/tag/v262-rc1
3. systemd Project. *systemd Repository*. https://github.com/systemd/systemd
4. systemd Project. *systemd Wiki*. https://systemd.io/
5. systemd Project. *ukify Manual*. https://www.freedesktop.org/software/systemd/man/ukify.html

*注:本文事实部分全部来自 systemd 官方 GitHub release notes 与 Phoronix 报道;解读与生态评论为作者观点。*