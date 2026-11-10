---
title: "virtme-ng 不重启宿主机：换的是虚机里的内核"
date: 2026-11-10
slug: virtme-ng-no-host-reboot-guest-kernel
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：arighi/virtme-ng 官方 README 与 Examples（v1.42，PyPI）＋ Debian unstable 的 vng(1) man page（2026-11-04）＋ virtme-ng 技术介绍（Kernel Recipes 2024）＋ 本机只读实测（libvirt 11.3.0、现有域 XML 的 direct kernel boot 结构、QEMU / KVM / busybox / `/boot/vmlinuz-*` 可读性）＋ libvirt / Red Hat 关于 Direct Kernel Boot 的官方文档"
original_date: 2026-11-10
original_url: "https://github.com/arighi/virtme-ng"
description: "本文把 virtme-ng（arighi/virtme-ng，v1.42）介绍清楚，并纠正一个容易被宣传语带偏的理解：它不重启的是宿主机，换掉的是 QEMU 虚机里的内核。官方 README 自己也写得明白——'kernel is automatically started in a virtualized environment that is an exact copy-on-write copy of your live system'、'exit to return back to the real system'。所以它每次都是新起一个 QEMU/microVM 进程，从虚机生命周期看，与 libvirt 里 virsh edit 改 <kernel>/<initrd>/<cmdline> 再 start 没有区别。对本来就跑 libvirtd 的人来说，'不重启换内核' 这个痛点本来就不存在。本文据 man page 把 --run/-r 的六条不编译路径逐条列出（不带参数启动宿主同版、已安装版本编号、v6.6 自动下载 Ubuntu mainline 预编译内核、本地 bzImage/目录、dpkg -x 解出的发行版内核、--root-disk 独立磁盘镜像），说明'要重新编译内核'只属于 --build 这一条路；同时指出它相对'改 XML'真正的增量只有一条：用宿主机根文件系统的写时复制快照当 rootfs，连同内核模块一起只读导出，省掉准备测试镜像与模块匹配。文章也如实列出它少的那部分：guest 默认跳过 udev/tmpfiles、最小 .config 内核缺大量功能、--rw 会真写回宿主机、virtiofs 的 POSIX ACL 已知坑，以及本机实测的依赖状况（QEMU/KVM/busybox/5 个可读 vmlinuz 齐备，缺 virtiofsd 会退回 9p，vng 未安装）。"
published: true
---

> 项目：<https://github.com/arighi/virtme-ng> ｜ 手册：<https://manpages.debian.org/unstable/virtme-ng/vng.1.en.html>
>
> 本文依据官方 README / Examples、vng(1) man page，以及本机只读核对。

## 一、先把话说准：不重启的是宿主机，换的是虚机内核

virtme-ng 命令叫 `vng`，作者是 Andrea Righi（NVIDIA），2022 年 11 月建，GPL-2.0，PyPI 最新 v1.42。它是 Andy Lutomirski 那个已停维护的 `virtme` 的重写。

官方 README 里的措辞其实很精确：

> 内核会自动启动在**一个虚拟化环境**里，这个环境是你当前系统的**写时复制精确副本**；在虚拟化环境里做的任何改动都不影响宿主机。
>
> …现在你有了一个 shell，跑在**你整个系统的虚拟化副本里**，用的是新内核。输入 `exit` 就回到**真实的系统**。

**三个词划清了边界**：`virtualized environment`、`copy-on-write copy`、`return back to the real system`。

所以它做的事是：

```
vng -r v6.6  →  新起一个 QEMU / microVM 进程
              →  里面跑 6.6 内核 + 宿主机文件系统的 CoW 快照
              →  exit 之后，宿主机的 7.2.15 内核从头到尾没动过
```

**它不是 kexec，不是热替换，也不是 attach 到一台正在跑的虚机把内核换掉。** 每次都是一次完整的开机。

## 二、于是「不重启」这个卖点，得看跟谁比

这个说法对比的是**传统内核开发的物理机循环**：

```
改源码 → 编译 → 把内核装到测试机 → 重启测试机 → 跑测试 → 崩了 → 再重启 …
```

省掉的是「把内核部署到真机并重启真机」这一串。**它从来没说「虚机不用重启」** —— 虚机当然要开机，因为它是新起的一个。

**而对一个本来就跑 libvirtd、会 `virsh edit` 的人，这个痛点本来就不存在。** libvirt 的 domain XML 里 `<os>` 段原生支持 direct kernel boot：

```xml
<os>
  <type arch='x86_64' machine='pc-q35'>hvm</type>
  <kernel>/boot/vmlinuz-6.6</kernel>
  <initrd>/boot/initrd.img-6.6</initrd>
  <cmdline>root=/dev/vda console=ttyS0</cmdline>
</os>
```

改完 `virsh define` + `virsh start`，一样是「宿主机不重启、虚机换个内核起一次」。我在这台机器上只读核对了一个现有域（`alpine-demo`）的 `<os>` 段，目前是 `<boot dev='hd'/>` 走磁盘引导；libvirt 11.3.0 支持上述 direct kernel boot 结构。

**所以准确说法应该是：「不重启宿主机，快速起一个跑指定内核的一次性虚机」**，而不是「不重启换内核」。标题里少了「宿主机」三个字，意思就完全不同了。

## 三、「要重新编译内核吗」——只属于 `--build` 一条路

这个疑问来自 README 开头那句自我定位：

> virtme-ng is a tool that allows to easily and quickly **recompile** and test a Linux kernel, starting from the source code.

（**这一句是全文我唯一想原样保留的英文** —— 因为它正是「以为必须重新编译」这个误解的来源：它只描述 `--build` 这一条路径，却被写在了 README 的第一段。）

**这句话只描述 `--build`**，但很容易让人以为整个工具都要求编译。man page 里 `--run` / `-r` 明确接受四类参数，加上 README 的 Examples，共六条不编译路径：

| 命令 | 内核从哪来 | 编译？ |
|---|---|---|
| `vng -r` | 不带参数 → 启动**与宿主同版**的内核（读 `/boot/vmlinuz-*`） | 否 |
| `vng -r 6.2.0-21-generic` | 系统里已安装的其它版本 | 否 |
| `vng -r v6.6` / `vng -r v6.6.17` | **自动下载 Ubuntu mainline 的预编译上游内核** | 否 |
| `vng -r ./arch/x86/boot/bzImage` | 任意现成内核二进制，或含内核的目录 | 否 |
| `vng -r ./test/boot/vmlinuz-6.2.0-1003-lowlatency` | `apt download` + `dpkg -x` 解出发行版内核 deb | 否 |
| `vng --run ./bzImage --root-disk ./tumbleweed.raw` | 现成内核 + 独立磁盘镜像做 rootfs | 否 |
| `vng --build` / `vng -b` | 从当前目录源码，自动生成最小 `.config` 后编译 | **是** |

官方在 `vng -r v6.6` 那个例子旁边专门写了一句：直接测特定版本、**省下大量构建时间**。

**所以：只想不重启试另一个版本，`vng -r v6.6` 就够了，下载的是别人编好的二进制，不需要源码树。** 前提是它拉的是 Ubuntu mainline 预编译包 —— 只有那个仓库里存在的上游版本、x86_64 generic 构建。想测发行版自己的内核（openSUSE、Debian riscv64 等）就走 `dpkg -x` 或 `--root-disk`；README 里甚至给了一个完整的 riscv64 例子（Debian sid cloud image + 解一个 riscv64 内核 deb + `--arch riscv64 --root-disk --root-fstype ext4`）。

**只有测自己改过的源码 / 补丁 / 某个 commit 时才编译**：

```sh
cd linux
vng --build --commit v6.2-rc4    # 自动生成最小 .config → 编译 → 起 VM
vng -b                            # 已 checkout 的当前源码
```

这里的「最小 `.config`」是它的核心设计：只开「能在 QEMU 里启动并跑测试」所需的功能，把构建压到几分钟（官方说 rather than hours），产物带 `-virtme` 后缀。**代价是这个内核缺大量功能，不能当生产内核用。** 可以用 `--config` / `--configitem CONFIG_FOO=bar` 追加，或 `--build-host` 丢到远程服务器编译。

## 四、那它相对「改 XML」到底多什么

把两边摆齐，增量其实只有一条：

| | libvirt XML + `virsh` | `vng` |
|---|---|---|
| 换内核 | `<kernel>` / `<initrd>` / `<cmdline>` + `define` + `start` | `-r v6.6` / `-r ./bzImage` |
| 宿主机重启 | 不需要 | 不需要 |
| 虚机 | 重新 `start` | 新起一个 microVM |
| **rootfs** | **你得先有一个装好系统的磁盘镜像** | **直接把宿主机根文件系统导出成 CoW 快照，不用准备镜像** |
| 内核模块 | 得保证镜像里 `/lib/modules` 与换进去的内核匹配，否则 `modprobe` 全挂 | 默认连宿主机模块一起只读导出，天然匹配 |
| 内核来源 | 你自己放 | 额外支持自动下载 Ubuntu mainline 预编译内核 |
| 编译 | 不管 | `--build` 从源码生成最小 `.config`，几分钟编出来 |

**唯一真正的增量是 rootfs**：用 virtiofs（或回退 9p）把宿主机根文件系统导出成只读 + overlay 写时复制，于是 guest 里的软件环境几乎和宿主机一模一样，而你在里面 `rm -rf /` 或把内核搞 panic，宿主机毫发无损。README 的原话是：你可以安全地摧毁整个文件系统、让内核崩溃，而不影响宿主机。

Kernel Recipes 2024 的技术介绍把组件列全了：**QEMU/KVM + microVM + virtio-fs + overlayfs**，目标是把「部署并维护一套专用测试系统」这件事省掉。

**而 `--root-disk` 是较新的能力**（2026-09 有博客专门写）：绕开 virtiofs/9p 的诸多限制，直接挂 virtio-blk 磁盘做根，才让「测发行版内核 + 任意 userspace」变得靠谱。README 里写得很清楚：内核、initramfs、模块与 guest 工具都从宿主机以只读独立挂载导出，**所以那个磁盘镜像不需要知道它要启动哪个内核**。代价是内核得有 `CONFIG_VIRTIO_BLK` 和对应文件系统支持 —— 文件系统不在 virtme-ng 的默认 config 里，要 `--configitem CONFIG_EXT4_FS=y` 或 `--root-fstype ext4`。

**注意这个转折**：一旦你用上 `--root-disk` 挂一个独立发行版镜像，做的事就非常接近你本来在 libvirt 里做的事了 —— 只是把 `virsh edit` 换成了 `vng --run`。

## 五、它少的那部分，也得说清

- **guest 不是完整发行版体验**：默认跳过 udev / tmpfiles 初始化；`--fast-boot`（`-F`）更激进，设备权限规则、udev 模块加载、hotplug 规则都不可用，tmpfiles 本该建的文件/目录/权限/符号链接可能缺失。`--systemd` 可保留完整初始化。
- **最小 config 内核功能残缺**，这是把构建压到几分钟的代价。
- **`--rw` 危险**：默认 rootfs 是只读导出，加 `--rw` 会真的能写回宿主机文件系统 —— README 自己标了 WARNING。
- **已知坑**：外部 virtiofs root 开 POSIX ACL 时可能 `switch_root` 失败 + guest panic，解法 `--no-root-posix-acl`；guest 里必须有 `/usr/bin/env`（helper 脚本用 bash shebang）；`vng -r` 不带参数常因 `/boot/vmlinuz-*` 是 600 而报 `unable to access ... (check for read permissions)`，要 `sudo chmod +r /boot/vmlinuz-*`。
- **不是热切换**：guest 里跑的是另一台虚拟机，宿主机上正在跑的工作负载不会迁过去。CoW 快照让它「看起来像」，但只是像。

## 六、本机只读核对（没装、没起 VM）

| 项 | 要求 | 本机 |
|---|---|---|
| Python | PyPI 写 ≥3.10，README 写 3.11+ | 3.12.8 ✅ |
| QEMU | ≥1.6 推荐 | `/usr/bin/qemu-system-x86_64` ✅ |
| KVM | 强烈建议（裸机或嵌套虚拟化） | `/dev/kvm` 存在，用户在 `kvm` 组 ✅ |
| 静态 busybox | 部分选项需要 | `/usr/bin/busybox` ✅ |
| virtiofsd | ≥1.7.0，可选但影响性能 | **未装**（会退回 9p） |
| `/boot/vmlinuz-*` 可读 | `vng -r` 需要 | 5 个 vmlinuz，全部 `-rw-r--r--` ✅ |
| libvirt | 对照用 | 11.3.0，10 域 / 3 网络 / 17 池 |
| `vng` 本体 | — | **未安装** |

依赖几乎全齐，只差 `virtiofsd` 和 `vng` 本身。**但我没有装，也没有起 VM** —— 这篇文章要说的恰恰是「它跟改 XML 是一回事」，装了反而多余。本机 `/boot` 里 5 个内核（6.12.x 系列 + 6.18.x xanmod）全是 644，如果哪天想试 `vng -r 6.12.48+deb13-amd64`，读权限这道坎不存在。

## 七、什么情况下它值得开

**唯一值得的场景**：你刚改完内核源码，想在一个「和当前系统一模一样、但又写不坏」的环境里跑测试，且懒得维护一个专用测试镜像。这时 CoW 快照确实省事，几分钟起一个，`--fast-boot` 更快，还能 `--gdb` 挂调试、`--debug` 抓 crash dump、`--build-host` 把编译丢到远程。

README 里还有 MCP server（AI Agent 集成）示例工作流：编译内核并检查 dmesg、与 mainline v6.12 比较行为、验证补丁系列里每个 commit 都能构建并启动 —— 这些是给内核补丁迭代准备的，不是给「换个版本用用」准备的。

**其余情况**：想试现成内核 → `virsh edit` 改 `<kernel>`；想试自己编的内核 → XML 一行 + 模块打进 initrd 或挂匹配镜像；想测发行版内核配发行版 userspace → 你本来就有磁盘镜像和 libvirt。

## 八、结论

把它一句话说死：

> **virtme-ng 优化的是「测试环境准备」，不是「换内核」本身。换内核这件事，改一行 libvirt XML 早就做到了。**

它真正的贡献是把「专用测试机 / 测试镜像」换成了「宿主机文件系统的 CoW 快照 + 自动匹配的模块」，再用一个 `vng` 命令把「下载内核 → 生成最小 config → 编译 → 起虚拟机 → 进去跑 → exit 回真机」串成一条流水线。

**标题里如果只写「不重启换内核」，那是唬人的；写「不重启宿主机、换的是虚机里的内核」才准确。**

顺带留一个方法论上的观察：这类工具的宣传语常常省略**比较对象**。「几分钟重新编译内核」对比的是「几小时的全量构建」，「不重启」对比的是「重启物理测试机」，而「当前系统的精确副本」听起来像热迁移，实际只是只读导出加一层 overlay。**读这类项目时，先把「比什么」问出来，再决定它对自己有没有用。**

---

## Sources

- arighi/virtme-ng 官方 README 与 Examples（v1.42）: <https://github.com/arighi/virtme-ng>
- `vng(1)` man page，Debian unstable（2026-11-04，`--run` 的四类参数、Requirements、动作说明）: <https://manpages.debian.org/unstable/virtme-ng/vng.1.en.html>
- PyPI `virtme-ng` v1.42（版本、Python 要求、许可证）: <https://pypi.org/project/virtme-ng/>
- Kernel Recipes 2024, *virtme-ng*（QEMU/KVM + microVM + virtio-fs + overlayfs 的技术介绍）: <https://kernel-recipes.org/en/2024/virtme-ng/>
- Red Hat / libvirt 关于 Direct Kernel Boot 的文档（`<kernel>` / `<initrd>` / `<cmdline>`）: <https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/virtualization_deployment_and_administration_guide/sect-Manipulating_the_domain_xml-Operating_system_booting>
- 本机只读核对：libvirt 11.3.0、`virsh dumpxml alpine-demo` 的 `<os>` 段、QEMU / KVM / busybox / `/boot/vmlinuz-*`

### 事实边界说明

- 「换的是虚机内核、宿主机不动」「每次新起 QEMU/microVM」「CoW 快照」「最小 .config」：均引自官方 README 与 man page 的措辞，本文按其明确表述解读。
- `--run` 的六条不编译路径：前四条出自 man page 的 `--run` ACTION 段，后两条出自 README Examples。
- 「与改 libvirt XML 等价」是本文基于 libvirt direct kernel boot 文档与虚机生命周期的分析，virtme-ng 文档未作此对比；文中已标明这是「从生命周期看」的判断而非功能等价。
- 本机依赖状态为只读实测；**本文未安装 virtme-ng、未启动任何虚拟机、未改动宿主机内核或任何域配置**。
- `--root-disk` 的时间信息（2026-09 相关博客）来自检索结果，未逐字核对博客全文，仅作背景提及。
- 本文只做技术解读与选型参考，不构成安装建议。
