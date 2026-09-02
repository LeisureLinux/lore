# QEMU 11.1 发布：3200+ 提交、285 位作者，把 RISC-V 大端、ARM 嵌套虚拟化和 UFS 4.1 仿真都装进来了

> **原始出处**：QEMU 11.1.0 官方公告 + ChangeLog/11.1
> **发布日期**：2026 年 8 月 11 日
> **作者**：QEMU 社区
> **官方公告**：https://www.qemu.org/2026/08/11/qemu-11-1-0/
> **完整 changelog**：https://wiki.qemu.org/ChangeLog/11.1
> **翻译/解读**：LeisureLinux
> **关键词**：QEMU 11.1、RISC-V 大端、ARM 嵌套虚拟化、UFS 4.1、GICv5、迁移改进

## 引言：没有爆点，但到处都是小升级

QEMU 11.1 在 8 月 11 日悄然发布。和 11.0 比起来，11.1 没有那种"一锤定音"的特性，而是用 3200+ 个 commit、285 位作者，把一堆分散在各个架构和子系统里的工作收拢到一起。

标题里几个关键字可能一眼看不懂，但它们串起来刚好是 QEMU 11.1 的主线：**RISC-V 大端**补全了 ISA 拼图、**ARM 嵌套虚拟化**让 Apple Silicon 上的 hvf 终于能跑嵌套 VM、**UFS 4.1 Write Booster 与 HID** 让移动存储设备的仿真追上协议规范、**GICv5 中断控制器**以实验性身份首次登场、**virtio-rtc 与 vhost-host-user** 让时钟类设备也能 offload 到 hypervisor。

剩下的篇幅，我会按架构（ARM / RISC-V / PowerPC / HPPA / s390x）、子系统（存储 / GUI / 监控器 / 迁移 / 用户态）和安全补丁三块拆开。

---

## 一、整体数字：3200+ 提交、285 位作者

QEMU 11.1 是 11.x 系列的第一个维护性更新。它没有像某些大版本那样大改模块边界，但合并窗口跨了大半年，积累的提交数比单季度工作多得多：

| 维度 | QEMU 11.1 |
|------|-----------|
| **commit 数** | 3200+ |
| **贡献者** | 285 人 |
| **发布周期** | 11.0（2026 年初）之后约 6 个月 |
| **新 machine type** | imx8mp-evk（i.MX 8MM EVK 板） |
| **新 firmware** | SeaBIOS-hppa v25、SLOF 20260627、OpenSBI v1.8.1 |

下面分架构拆。

---

## 二、ARM 平台：从 FP8 到嵌套虚拟化

ARM 是 QEMU 11.1 改动最密集的架构。重点：

### 2.1 Apple hvf 加速器：嵌套虚拟化 + vGIC

`qemu-system-aarch64 -accel hvf -machine virt` 现在支持：

- **嵌套虚拟化**：在 macOS 上用 Apple 虚拟化框架（hvf）跑的 VM，可以再开一层 Guest VM。
- **virt board 平台 vGIC**：硬件辅助的虚拟 Generic Interrupt Controller，让中断处理路径更短。

这两件事叠加，对 macOS 开发者来说意义不小：在 Apple Silicon 上跑嵌套 VM 不再是 KVM 才有的能力。

### 2.2 GICv5 中断控制器（实验性）

QEMU 11.1 引入了对 **GICv5** 的实验性仿真。命令行参数是 `gic-version=x-5`，文档明确标注"实验性"。在 semihosting 与完整中断控制器支持齐备之前，不要把它用在生产路径上。

### 2.3 NVIDIA Tegra241：CMDQV

在 Tegra241 硬件上，新增 `arm-smmuv3` 设备的 CMDQV（Command Queue Virtualization）支持：

```bash
-device arm-smmuv3,accel=on,cmdqv=on
```

效果是给每个 VM 独立的 SMMUv3 命令队列，提升多 VM 并发下的吞吐。

### 2.4 i.MX 8MM EVK 与 FlexCAN

- **imx8mp-evk**：新 machine type，仿 i.MX 8MM Evaluation Kit 板。
- **fsl-imx6ul**：LCDIF 显示设备实现落地。
- **sabrelite**：FlexCAN 仿真支持。
- **32 位 guest 在 64 位 TCG CPU 上启动**：通过 `-cpu,aarch64=off`，`qemu-system-aarch64` 现在能引导 32 位 guest。

### 2.5 大量新增 ARM 架构特性

这是 11.1 ARM 端最长的清单，我按家族归类：

| 家族 | 新增特性 |
|------|---------|
| **FP8 / FP16** | FEAT_F8F16MM、FEAT_F8F32MM、FEAT_FP8DOT2、FEAT_FP8DOT4、FEAT_FP8FMA、FEAT_FP8 |
| **SME / SSVE** | FEAT_SME_LUTv2、FEAT_SME_F8F32、FEAT_SME_F8F16、FEAT_SSVE_FP8DOT2、FEAT_SSVE_FP8DOT4、FEAT_SSVE_FP8FMA、FEAT_SSVE_AES、FEAT_SME_MOP4 |
| **MTE（内存标签扩展）** | FEAT_MTE_CANONICAL_TAGS、FEAT_MTE_NO_ADDRESS_TAGS、FEAT_MTE_PERM、FEAT_MTE_STORE_ONLY、FEAT_MTE_TAGGED_FAR、FEAT_MTE4 |
| **浮点 / SIMD** | FEAT_FAMINMAX、FEAT_FPMR、FEAT_CMPBR、FEAT_FPRCVT、FEAT_SSVE_FEXPA |
| **杂项** | FEAT_RNG_TRAP、FEAT_LUT、FEAT_RME_GPC3、FEAT_WxFT |

### 2.6 WFE / WFET 真正"生效"

WFE（Wait For Event）和 WFET（带超时的 WFE）此前在 QEMU 里是 no-op，guest 直接忙等。11.1 起，它们真正实现为让 vCPU 暂停并响应 trap 条件（包括超时），syndrome 与寄存器信息也按规范上报。

这意味着 guest OS 的低功耗 idle 路径终于在 QEMU 里有了正确的语义，对电源管理调试、长跑测试的可靠性都有意义。

---

## 三、RISC-V 平台：补上"大端"最后一块拼图

RISC-V 在 11.1 上的最大新闻是**大端支持**首次进入主线。

### 3.1 RISC-V 大端目标支持

`qemu-system-riscv64` 和 `qemu-user-riscv64` 现在可以配置为 big-endian。这是 RISC-V 国际基金会推荐但可选的端序配置，过去在 QEMU 上一直是缺位。补上后，RISC-V 大端生态（部分嵌入式、某些特定 SoC）终于有可用的仿真。

### 3.2 ISA 扩展

| 扩展 | 状态 | 说明 |
|------|------|------|
| **Zbr** | 草案（xbr0p93） | 位操作扩展 |
| **Zvfbfa** | 已合入 | 向量 BFloat16 |
| **Zicbop** | KVM 支持 | 缓存块预取指令 |
| **BFloat16** | KVM 支持 | KVM 加速路径下的 BF16 |
| **向量 SHA** | fractional LMUL | 允许非整数倍的 LMUL |

其他改进：`mnret` 反汇编支持、不再在 gdbstub 中隐藏 Sstc CSR、U-mode 下拒绝 Svinval、对保留 PTE.PBMT 值触发 fault、新增 PMA 访问 fault。

### 3.3 板级与固件

- **K230 板**：新 board 支持。
- **Tenstorrent mvendorid**：识别 Tenstorrent 设备的 mvendorid。
- **OpenSBI 升级到 v1.8.1**。
- **Microchip mpfs ioscb PLL 与 sysreg 时钟分频器**实现。
- 移除 `spike` 默认 machine；弃用 `shakti_c` machine。
- 修复 `--disable-tcg` 构建路径。

---

## 四、PowerPC：Power11 / PowerNV11 成为默认

PowerPC 的改动集中在"现代化默认"上：

- **pseries 默认 CPU**：从旧版切到 **Power11**。
- **PowerNV 默认 machine**：切到 **PowerNV11**。
- **MPIPL**：PowerNV 增加对 Memory Preserving IPL 的支持，允许在意外 reset 后保留内存现场。
- **nest MMU 模型**：ppc/pnv 新增仿真嵌套 MMU。
- **HPB 代码重构**：提升可维护性。
- 移除弃用的 Power8E / Power8NVL CPU；撤销 405 CPU 的弃用（回炉）。
- 暴露 guest TB offset 到 QEMU monitor，方便时间同步调试。
- SLOF 固件更新到 20260627。

还有 `hw/ssi/pnv_spi` 修复 fifo8 内存泄漏、`hw/intc/xics` 增加无效 server id 检查、`target/ppc/kvm` 修 CPU alias 后缀修剪的 const 违反等一批小修。

---

## 五、HPPA：HP-UX 9 兼容性

HPPA 的关注点很窄：

- **SeaBIOS-hppa 升级到 v25**。
- **HP-UX 9 快速 TLB insert 修复**：让老 HP-UX 9 能在 QEMU 里正常引导。

---

## 六、s390x：ASTFLE facility 2

`kvm` 加速器新增 **ASTFLE facility 2** 支持（用于嵌套虚拟化）。这是 s390x 端唯一一个显著改动。

---

## 七、存储与设备仿真：UFS 4.1 是亮点

### 7.1 UFS 4.1 仿真（UFS Write Booster + HID）

UFS（Universal Flash Storage）是移动设备主流的闪存接口。QEMU 11.1 按 UFS 4.1 规范补齐两块：

- **UFS Write Booster 仿真**：设备级缓存，把顺序写入吸收到 SLC 区域。
- **Host Initiated Defragmentation（HID）仿真**：主机主动整理后台闪存的碎片。

这套仿真让 SoC 固件 / 文件系统 / 性能测试团队可以在 QEMU 里复现"真实 UFS 4.1 设备"的行为，而不再需要每次都跑真机。

### 7.2 virtio-gpu 与 USB 多个 CVE

- **virtio-gpu use-after-free**（CVE-2026-6502）。
- **USB 多个修复**：包括 use-after-free、usb-redir 上的死循环/崩溃、XHCI sysbus 设备的越界堆访问。
- **9p 文件系统的两个安全修复**：
  - CVE-2026-63318：通过 `O_TRUNC` 在只读导出上的旁路读取。
  - CVE-2026-8348：限制同时打开的 xattr fid 数为 1024（可通过新选项 `max_xattr` 调整），防止宿主内存被耗尽。

### 7.3 virtio-rtc 与 vhost-host-user

新增 `vhost-user-rtc` 设备，可以连接到提供 virtio-rtc 实现的 vhost-user daemon。配合 vhost-host-user，把实时时钟处理从 hypervisor 自身 offload 到独立的 daemon，是实时性要求高的场景（工业控制、音视频同步）的关键改进。

---

## 八、GUI 与虚拟控制台：CP437 / UTF-8 双修

### 8.1 字符编码可控

- **vc chardev** 新增 `encoding` 选项，支持 `cp437` 或 `utf8`。
- **-display dbus** 暴露 `org.qemu.Display1.Chardev.VCEncoding` D-Bus 属性。
- **vt100 仿真器**支持 UTF-8 输入、CP437 渲染。

这套改动背后是远程运维真实场景：很多人靠 SSH 客户端串口连 VM，字符编码错位一直是调试效率杀手。

### 8.2 GTK 与 VNC

- **`-display gtk`**：改善控制台热插拔处理。
- **`qemu-vnc`**：新增独立 VNC server，可导出 `-display dbus`。
- 退出时清理资源更彻底。

---

## 九、迁移：RDMA chunk 控制 + 下线时间估算

迁移方面 QEMU 11.1 重点是"可观测 + 可控"：

- **x-rdma-chunk-size**：新增 RDMA 迁移 chunk 大小参数。
- **enhanced query-migrate**：同时报告系统级剩余字节数与预期下线时间（含 VFIO 设备状态）。
- **CPR-transfer 下线时间优化**：用哈希表加速 FD lookup。

修复的迁移 bug 包括：

- multifd + zerocopy 同时启用时的崩溃。
- `POSTCOPY_DEVICE` 状态下的可能挂起。
- 第二次迁移（第一次被取消）的崩溃。
- VFIO 迁移中的偶发崩溃。

---

## 十、监控器（QMP / HMP）：可热插拔 + close-action

QEMU 11.1 把 monitor 从单一进程级资源变成对象：

- **QMP monitor**：可用 `-object monitor-qmp,id=NNN,chardev=MMM` 创建，原 `-mon` 参数被弃用。
- **QMP 热插拔**：可通过 `object-add` / `object-add monitor-qmp` 动态新增/移除。
- **`close-action=delete`**：客户端断开后自动删除 monitor 实例。
- **HMP**：可热新增（不可移除）；`-mon` 同样被弃用。

`-qmp` / `-monitor` 这种"高级语法糖"保留。

---

## 十一、用户态仿真（linux-user）改进

`qemu-user` 在 11.1 的更新覆盖面很广，按子系统分：

| 子系统 | 改进 |
|--------|------|
| **syscalls** | 新增 `preadv2` / `pwritev2`、`fsmount` 系列、为 systemd 提供 `/proc/cpuinfo` 仿真（ppc / loongarch / m68k） |
| **架构** | 修复 sparc / sparc64 信号处理、loongarch64 guest 的 stat64 结构、sh4 VDSO 支持 |
| **CDROM** | 增加 ioctls 支持 |
| **网络** | 允许 `getsockopt()` 使用 NULL optval、IP_RECVERR 与 IPV6_RECVERR 的 errno 翻译 |
| **AUXV** | 修复 symlink 程序的 `AT_EXECFN`、重定位 program header 时的 `AT_PHDR` |
| **coredump** | 为 hppa / riscv / alpha / sparc / mips64 / mipsn32 新增 coredump 支持 |
| **HP-UX** | hex 目标 unaligned 访问修复（早期 HP-UX 9 之前依赖错误行为） |

---

## 十二、Hexagon 与 Hexagon 软仿真

- **Hexagon 系统仿真（hexagon-softmmu）** 首次落地，但因 semihosting 与中断控制器尚未齐备，11.1 上能用场景很有限，建议等后续版本。
- 构建依赖：**flex** 与 **bison**。非 Linux 宿主如果开全部 target，现在也需要它们（hexagon-linux-user 早已需要）。

---

## 十三、几个值得拎出来说的 bug

- **9p 只读导出**的 O_TRUNC 旁路读取（CVE-2026-63318，commit a0414545）。
- **9p 同时打开 xattr fid** 数量未限制（CVE-2026-8348，commit 693b296b17，新选项 `max_xattr`，commit e6116a81f0）。
- **virtio-gpu** use-after-free（CVE-2026-6502）。
- **Windows 下 EGL 不可用**时的 virtio-gpu 崩溃修复。
- **usb-redir** 死循环/崩溃。
- **XHCI sysbus** 越界堆访问。
- **nettle / gcrypt** configure flag 恢复有效。

---

## 十四、升级建议

QEMU 11.1 改动量大但向后兼容友好，下面是分场景的简版建议：

| 场景 | 建议 |
|------|------|
| **生产虚拟化栈** | 11.1.0 通过社区构建稳定后再上，关注 11.1.1 之后的 bugfix。 |
| **macOS 嵌套 VM** | 强烈升级；hvf 嵌套虚拟化是 Apple Silicon 上第一次能用。 |
| **RISC-V 大端固件开发** | 11.1 起可弃用旧版本地补丁方案。 |
| **UFS 4.1 性能测试** | 强烈升级，避免再每次跑真机。 |
| **9p / virtio-gpu 重度使用** | 升级，多个安全修复必打。 |
| **x86 KVM 迁移** | 升级，下线时间估算与 RDMA chunk 控制值得用。 |
| **HP-UX 9 复古 / 测试** | 升级，TLB insert 修复让老系统能正常引导。 |

---

## 十五、为什么 QEMU 11.1 看着"散"？

最后说一句个人观察。QEMU 11.1 的 changelog 看起来是"什么都有一点"，但这恰恰是 QEMU 现在的常态：它已经不靠单一爆点推动进步，而是把每个架构、每个子系统的渐进改进一点点收拢。每次"小升级"背后是某个公司某个团队几个月的代码工作——285 位作者里大多数只贡献了几十个 commit，但合起来就撑起了一个完整的 3200+ commit 版本。

这也是为什么 QEMU 不太可能突然"被某个新方案颠覆"。它太分散、太渐进、覆盖太多架构，新的仿真器想做完整替代品必须从零补齐这一摊工作量，而 QEMU 每六个月就推进一摊。

下一个有意思的看点是：**GICv5 真正走出 experimental 标签**的那次大版本。

---

**参考资料**：

1. QEMU 11.1.0 官方公告：<https://www.qemu.org/2026/08/11/qemu-11-1-0/>
2. QEMU Wiki ChangeLog/11.1：<https://wiki.qemu.org/ChangeLog/11.1>
3. LWN：<https://lwn.net/Articles/1088490/>
4. Phoronix：<https://www.phoronix.com/news/QEMU-11.1-Released>
5. linuxiac：<https://linuxiac.com/qemu-11-1-adds-risc-v-big-endian-support-arm-nested-virtualization/>
6. QEMU 源码：<https://github.com/qemu/qemu>

---

*本文基于 QEMU 11.1.0 官方公告、QEMU Wiki ChangeLog/11.1 与社区资料整理，旨在为中国开发者提供快速理解和参考。*

*作者观点不代表任何厂商立场，仅供技术讨论参考。架构特性清单摘自 ChangeLog，落地效果依硬件平台与构建配置可能有所差异。*