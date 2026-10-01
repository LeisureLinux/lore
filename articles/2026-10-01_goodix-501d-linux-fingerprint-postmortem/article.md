> 主题：设备驱动逆向 · 虚拟化 · 系统安全。本文是**原创复盘**，素材来自一台 H3C H3CBook Ultra 14T（i002）在 Debian 13 / niri / Wayland 下为期三天的 Goodix 指纹适配。最终结论是放弃，但过程中我们把 PSK 提取、Windows 协议抓包、私有引擎逆向、Wine 兼容层、Win11 虚机直通这些路都走了一遍。写下来，给将来拿到同款传感器的人省几天时间。

## 一句话结论

一颗 80×64（约 13 mm²）的 Goodix GM168SEC 指纹传感器，能在 Linux 上把协议层的每个环节都走通，从 TLS-PSK 建立到图像采集和模板录入。**唯一不通的是最后一步：匹配算法。**

而这一步没法自己补。Windows 能用，是因为 Goodix 有一个闭源的私有匹配引擎，专门针对小面积传感器调过；这个引擎**架构上不能脱离 Windows 的 WBDI（Windows Biometric Driver Interface）框架独立运行**。两条绕开它的路，Wine 里跑引擎和虚机里调 WinBio API，分别在「缺宿主」和「安全策略拒绝」两处撞墙。

这是一个**明确的、有原因的放弃**，原因不在参数。

## 先从硬件说起

拿到这块传感器，第一件事是搞清它到底是谁。Goodix 的 VID 是 `27c6`，但同一个 VID 下有多个**完全不同**的 PSK 家族，这是后面所有踩坑的根源。

| 项 | 值 |
|---|---|
| USB ID | `27c6:501d` |
| 型号 | Goodix GM168SEC，固件 `GFUSB_GM168SEC_APP_10034` |
| 成像面积 | 80×64 px @ 500 dpi ≈ 4.06 × 3.25 mm ≈ **13 mm²** |
| 原始帧 | 10564 B（TLS 载荷）→ 80×64 12-bit packed |
| 预处理后 | 64×80 8-bit 灰度 |

传感器集成在**电源键**上（系统里已设 `HandlePowerKey=ignore`，短按不关机；轻触传感面即可，不需要机械按压）。

## 第一步：用错了驱动家族

一开始，我们用社区 fork `djnz00/libfprint` 里的 `goodixtls52xd` 驱动。它的 `id_table` 只列了 `0x521d`，我们把自己的 `0x501d` 加进去，设备立刻被认出来了，打印 `Goodix TLS Fingerprint Sensor 52XD`。

看起来一切正常，直到 PSK 比对失败：`Unsupported device PSK hash`，紧接着 TLS 握手被拒：`TLS server rejected device handshake`。

在这里我们做了一件当时觉得很聪明、其实是死路的事：**从 libfprint 的调试日志里把本机真实的 PSK 哈希抠出来，替换掉驱动里硬编码的那个**，让 `memcmp` 通过。

**哈希能比对通过，不等于能握手。** 52xd 家族的 PSK 是一个**硬编码的白盒常量**（`goodix_52xd_psk_10034`），全家族共用；而 501d 硬件里烧的是一份**每台设备独有的密钥**。我们把哈希填对了，但 TLS 服务端回调拿出的密钥和硬件里的不相等，握手必然失败。

判据其实很简单：**看设备上报的固件串**。`GFUSB_GM168SEC_APP_10034` 属于 GM168SEC 家族，不是 52xd，也不是 G4。教训是，Goodix 支持高度碎片化，**别按 PID 相邻猜家族**。

## 第二步：PSK 到底藏在哪里

改用正确家族（`mrcook1e-ai/goodix-gm168` / `ejsergeev/libfprint-goodix-gm168sec`）之后，我们终于看清了这个家族的设计。

GM168SEC 的 PSK 由 **Windows 驱动第一次联机时随机生成、用该 Windows 的 DPAPI 密封、写进 MCU NVRAM**，固件里没有这个常量：

- `cmd 0xE4 / tag 0xbb010002` 读回的是一份 **324 字节 sealed blob**，前 20 字节是标准 DPAPI 魔数 `01000000 d08c9ddf 0115d111 8c7a00c0 4fc297eb`；
- `tag 0xbb020001` 读回的是 **SHA-256(psk) 完整性哈希**，它只是校验值，不是密钥本体。之前我们费劲抠出来的那个哈希，就是这个东西。

问题来了：解封这份 blob 需要**当初 provision 它的那台 Windows 的 DPAPI 主密钥**。而这台机器出厂是 Win11，已经被我们重装成 Debian，原 C 盘（现在的 `nvme0n1p3`，挂成 `/nfsroot`）也格式化了，主密钥**永久丢失**。

顺手核实了一下恢复分区：`nvme0n1p4`（WINRE_DRV）里的 `Winre.wim` 是通用 Windows RE 镜像，把 7z 拆开看，**没有 `Microsoft/Protect` 目录**，也没有 Goodix 驱动或用户数据。此路不通。

## 第三步：虚机直通，重新 provision

既然原始 DPAPI 密钥没了，那就**重新 provision 一份新的**。

思路是：把指纹 USB 设备直通进一台全新的 Windows 虚机，装 H3C 官方驱动，让**虚机自己的 DPAPI** 去生成并密封一份新 PSK 盖掉 MCU 里的旧值。

具体步骤（`RUNBOOK-planC.md` 里记了全过程）：

1. `win11-ltsc` 虚机（UEFI q35 + TPM + qemu-xhci）用 **SPICE usbredir** 把 `27c6:501d` 挂进客机（virt-viewer 菜单 File → USB device selection）。设备管理器出现"生物识别设备"。
2. 装 H3C 官方驱动 `Goodix_FP_A00_v3.11710.0.110.zip`（`WbdiUsb.inf` 里精确含 `USB\Vid_27C6&Pid_501D`）。**PSK 在驱动联机那一刻就 provision 了，不需要真的去录指纹**，录指纹只是采集模板。到这一步直接取消即可。
3. 在 virt-viewer 里取消 USB 重定向，设备回到宿主（`/sys` 里接口 driver 从 `usbfs` 变回 `usb`）。
4. 宿主上 root 跑构建树的 `img-capture`，读出 324 字节新 sealed blob。新旧 sha256 不同（`1984c735...` vs `162e7612...`），说明**覆盖成功**。
5. blob 传回虚机，用 `gm168_unseal.ps1`（mrcook1e 提供，以 SYSTEM 账户调 DPAPI 解封），得到 **32 字节明文 PSK**。

拿到 PSK 那一刻的心情，大概等于三天里唯一一次"成了"。落盘到 `/etc/goodix-gm168/psk.bin`（root 0600），三处备份。再跑 `img-capture`，日志给出四条铁证：

```
pre-shared key loaded from /var/lib/fprint/gm168/psk.bin
TLS handshake complete, cipher PSK-AES128-CBC-SHA256
INIT_NUM_STATES completed successfully
AWAIT_FINGER_ON
```

到这一步，**协议层全线打通**。

## 第四步：FDT 阈值，卡了三周的常量

但设备就位、TLS 通了之后，一个更折磨人的问题出现了：**怎么按手指都没反应**。

`fprintd-enroll` 卡在 `PRESS_NUM_STATES`，零触摸事件。INIT 全过，校准帧也正常（`stats16 calibration-background nonzero 3274/5120`），但就是检测不到手指，每 5 秒刷一次 `no touch event for a while, re-arming`。

根因藏在一个没人会想到的地方：驱动里的 **FDT（Finger Detection Threshold）常量是从 589a 型号（固件 10008）逆向来的，和 501d（固件 10034）对不上**。

```
589a:  1c 01  a4 00  a6 00  a4 00  a5 00   (35B) → 阈值 164/166/164/165
501d:  9c 01  25 01  1f 01  27 01  21 01   (40B) → 阈值 293/287/295/289
```

Windows 的检测帧是 **40 字节**，Linux 驱动发的是 **35 字节**；Windows 还会多发两条 Linux 完全不会发的命令（`0x36`、`0x80`）。

抓真值的办法：在宿主上用 `usbmon` 抓 Windows 虚机经 SPICE usbredir 的**真实流量**（`tcpdump -i usbmon3 -w pcap`，链路类型 220）。因为走的是虚拟 USB，明文帧全能抓到。把 501d 的真实 FDT 帧和采图触发参数替换进驱动，重新编译，**触摸立刻被检测到**：`finger_detected=1`。

顺带踩的坑：`0x32/0x34` 帧里只有前 10 字节是固定阈值，后面 8 组 u16 是自适应增益（每次触摸都不同）；而 `set_param(0x90)` 反而应该用原来的 589a 值，照搬 Windows 抓到的 5 套官方参数，会让校准帧几何变错。**同一个抓包结果，有的能照搬，有的不能**，得逐个验证。

## 第五步：录入成功，但匹配器分不开手指

FDT 修好之后，路突然就顺了。`ejsergeev/libfprint-goodix-gm168sec` 集成树（patch 0001 capture + 0002 sigfm + 0003~0008 修复）走完全部流程：

```
enrollment validated: 14 presses, cluster 13, LOO pass 11
  (min 99, median 15842, max 25425) at T=1000
```

**录入成功了。** 14 次按压、聚类 13、留一法（LOO）验证 11 次通过。离可用只差验证。

然后，问题出现了。部署到工作点 `TVERIFY=1000`（来自 `extras/fprintd-tuning.conf`），实测结果：

| 按压 | SIGFM 分数 | 结果 |
|---|---|---|
| 右食指 #1 | **554** | 拒（真手指被拒）|
| 右食指 #2 | 1845 | 通过 |
| 左手中指 #1 | **1091** | **通过（陌生手指！）** |
| 左手中指 #2 | **1067** | **通过（陌生手指！）** |

真手指的分数范围 [554, 1845] 和陌生手指的 [1067, 1091] **重叠**。阈值怎么调都没用，分数本身就分不开。

换用 libfprint 默认的 NBIS/Bozorth3 算法：`mindtct` 实测 **0.38 个细节点/帧**。Bozorth3 至少需要 2 个匹配的细节点才产生分数。**结构性不可用。**

根本原因是面积。13 mm² 太小了，指纹细节点的物理密度就在 0.2–0.5 个/mm² 这个量级，一帧理论上只有几个点，还经常采不到。空白传感器因为噪声反而"检"出更多假细节点，这本身就说明问题。

## 第六步：Wine 方案，逆向私有引擎

既然开源匹配器不行，那就只能用 Windows 那个。

我们从 H3C 驱动包里挖出 `GoodixEngineAdapter.dll`（1,176,792 字节，PE32+ x86-64，29 个未混淆的 C 导出函数）。这是一台完整的 Windows 生物识别引擎：

```
enrolStartEx / enrolAddImage / enrolFinish / enrolGetTemplate
identifyImage / identifytemplate / identifyUpdate
preprocessor / preprocessor_init / preprocess_load_calidata / preprocess_save_calidata
getQuality / getAlgorithmVersion / gx_sensorCheck
LivenssDetection / GetLivenssVersion
WbioQueryEngineInterface / ppp_param_init / templatePack / templateUnPack
```

它的 vtable 是标准的 WBDI `WINBIO_ENGINE_INTERFACE`，23 个函数指针，从 `WbioQueryEngineInterface` 返回的结构体 +0x20 处开始。好消息是：这个 DLL **不导入任何 SGX 运行时**，依赖只有 KERNEL32/ADVAPI32/OLE32/OLEAUT32/WINMM/WS2_32/dbghelp/UCRT，对 Wine 友好。

用 `x86_64-w64-mingw32-gcc` 编测试程序，在 Wine 10.0 下实测：

- `LoadLibraryA` 成功，29 个导出全部解析；
- `WbioQueryEngineInterface(&iface)` 返回 S_OK；
- `EngineAdapterAttach` 入口能过，但有个诡异前提：`EngineParam + 0x08` 必须是 **64 位** 的 `-1`（写成 32 位 `-1` 会失败），且 `+0x38` 为 NULL。满足则返回 S_OK 并回写 context。

然后，撞墙。

`Attach` 之后是 `CreateContext`（`gxlogicalgorithm.c`），它 malloc 一个 0x4d70 的全局单例，从 `EngineParam` 拷贝传感器信息，然后调 `_LogicAlgCreateContext(p, 1)`。**注意那个 `1`：memcpy 的 size 硬编码成 1 字节**，只拷一个字节。后面 `ppp_param_init(*(uint8*)(dst+4))` 读到的是 malloc 垃圾。

就算解决了这个，更根本的问题也躲不掉：**引擎初始化需要 7 个设备接口虚函数的回调**。

```
vtable idx 11 (+0x58)  唤醒/初始化设备
vtable idx 12 (+0x60)  发命令
vtable idx 15 (+0x78)  读数据
vtable idx 16 (+0x80)  写设备
vtable idx 17 (+0x88)  读传感器属性 (_GetSensorAttribute 发 0x442004)
vtable idx 19 (+0x98)  状态查询
vtable idx 20 (+0xa0)  控制单元
```

在 Windows 上，这层接口由 **WBDI 框架 + `Wbdi.dll` 驱动**注入，而 `Wbdi.dll` 本身是 UMDF 驱动，靠 IOCTL 工作，Wine 里根本没有 WDF 宿主。引擎自己会写日志到 `C:\ProgramData\Goodix\engineadapter-new.log`，实测初始化失败时写的是：

```
[error][engineadapter.cpp][EngineAdapterAttach :0552] >> invalid device state
[error][additional.c][_GetSensorAttribute :0219] >> -->failed
[fatal] unhandled exception
```

`_GetSensorAttribute` 会向设备 MCU 发命令 `0x442004` 读传感器属性。没有宿主转发，就报 `invalid device state`。

量化一下代价：`x86_64-w64-mingw32-gcc` 编一个 x64 PE 只要 0.7 秒，但 **Wine 每次启动约 7.4 秒**（prefix 773MB）。这意味着即使跑通，也只能是"Wine + 常驻 helper 进程，驱动经 Unix socket 调用"的部署形态，绝不能每次扫描起一个新 Wine。这还没算要逆向出 `0x442004` 对应我们 Linux 协议里的哪条命令（`0xd6 READ_REG`？`0xe4 SPEC_DATA`？），那是一条从零开始的映射工程。

**Wine 方案到此为止：能装载，不能初始化。**

## 第七步：虚机方案，Windows Hello 完美而 WinBio 被拒

既然 Wine 缺宿主，那就在**真 Windows 里面调**。

在虚机里实测 Windows Hello：录入正常、识别正常、陌生手指被正确拒绝。**功能层面完全可用。**

于是转向微软官方 API。`WbioSrvc` 服务默认是 Stopped，启动成 Running 之后：

- `WinBioEnumBiometricUnits` 用 **Factor=8**（`WINBIO_TYPE_FINGERPRINT`）返回 `hr=0, count=1`，注意只有 8 是对的，1/2/4 都返回 0；
- `WinBioOpenSession` 返回 `hr=0x00000000, handle=1`，会话能开；
- 引擎位于 `C:\Windows\System32\WinBioPlugIns\GoodixEngineAdapter.dll`，被 WBF 框架主动加载，**它拿得到完整的 WBDI 环境**；
- 数据库 `C:\Windows\System32\WinBioDatabase\*.DAT` 里已经有模板。

到这里架构看起来很清晰：`Linux (PAM/niri) → IPC → 虚机内 WinBio 程序 → WBF 栈(含 WBDI) → Goodix 引擎 → 设备`。

但真正调用 `WinBioIdentify` / `WinBioCaptureSample` 时，返回 **`ACCESS_DENIED`**。

Win11 的生物识别安全策略**只允许锁屏/登录流程触发采集**，第三方进程即使拿到会话句柄也没资格。这是设计上的隔离，不是配置问题，它恰恰是为了防止"一个后台程序偷偷拿你的指纹做别的事"。

从宿主导控虚机也不轻松：`win11-ltsc` 没装 qemu-guest-agent，ping 不通（Windows 防火墙拦 ICMP），445/5985/5986/22 全关，只有 RDP 3389 开放。后来在 libvirt XML 里补了 `org.qemu.guest_agent.0` channel，才能用 `virsh qemu-agent-command` 跑 PowerShell（还得绕过执行策略，用 `-ExecutionPolicy Bypass` 或 `-EncodedCommand`）。

**虚机方案到此为止：功能完备，但 API 层被安全策略封死。**

## 那我们到底做成了什么

把三天的工作按层拆开，能成的都成了：

| 层 | 目标 | 结果 |
|----|------|------|
| USB 协议 | 读 sealed blob / TLS-PSK 会话 | 通 |
| PSK 提取 | 虚机重新 provision + DPAPI 解封 | 通 |
| 传感器校准 | 5 帧暗帧 → 暗参考 | 通 |
| 手指检测 | FDT 0x32/0x34 + IRQ_ARM | 通（修完阈值） |
| 图像采集 | 0x20 TRIG → 80×64 12-bit | 通 |
| 模板录入 | 14 次按压、LOO pass 11 | 通 |
| Windows Hello（虚机内） | 录入/识别/拒绝 | 通 |
| 引擎逆向 | 29 导出 + 23 vtable + 结构体 | 通 |
| **SIGFM 匹配** | 分数可分 | 分不开 |
| **NBIS 匹配** | 细节点够用 | 0.38/帧 |
| **Wine 调引擎** | 引擎初始化 | 缺 WBDI 宿主 |
| **虚机调 WinBio** | 第三方触发采集 | ACCESS_DENIED |

**协议全通，算法不通。** 这就是最终的边界。

## 为什么这个边界绕不过去

回头看，两条"绕过匹配算法"的路，失败的原因是同一个：**Goodix 的匹配引擎不是一个能独立跑的库，它是一个必须活在 Windows 生物识别框架里的组件。**

- Wine 能装载它的代码，但给不了它赖以工作的 WBDI 宿主；
- Windows 虚机能给它完整宿主，但 Win11 不允许框架外的程序触发采集。

这个引擎和 Windows 是**耦合**的，架构上就搬不走。这是架构问题，努力程度解决不了。

而自己写匹配器这条路，被 **13 mm² 的物理面积**封死了。开源算法在这个分辨率下没有可用的信噪比，这不是调参能救的。

## 如果我们非要"用上"这块传感器

只有一个办法，而且它不叫"Linux 支持指纹":**把设备直通给常开的 Win11 虚机，用 Windows Hello 解锁那个虚机。**

实用性很低：为了指纹要一直开着一台虚机，而且它只能解锁虚机自己，不是你的 Linux 会话。我们最终停在这里。

当前状态：

- Linux 指纹登录：停用（`systemctl mask fprintd`）；
- Linux 解锁：纯密码，完全可用；
- 设备：重定向给 `win11-ltsc` 虚机（virt-viewer SPICE usbredir）；
- 保留：虚机磁盘**不能删**，它承载着解封当前 PSK 的 DPAPI 环境。

## 留下来的东西

虽然结果是放弃，但资产是实的。将来有人拿到同款传感器，这些东西能省他几天：

| 产物 | 说明 |
|---|---|
| `~/fp-goodix/gm168/src/` | libfprint 集成树，0001~0008 完整 patch 链 |
| `win-protocol/{GOLD.md, REFERENCE.md}` | 501d 真实协议金标准（从 Windows usbmon 抓包） |
| `RUNBOOK-planC.md` | Win11 虚机 PSK 提取流程 |
| `FINAL-TECHNICAL-REVIEW.md` | 309 行完整技术复盘 |
| `win-vm-share/` | H3C 驱动包 + PSK + sealed blob + 解封脚本 |
| `/etc/goodix-gm168/psk.bin` | 32 字节 PSK（三处备份） |

## 几个可以复用的坑

写下来是因为它们跟指纹无关，下次做别的驱动适配一样会撞：

- **先认家族再动手。** 同一个 VID 下可能有完全不同的协议家族。判据是设备上报的固件串，不是 PID 邻近。用错家族的驱动会"认得设备但握手被拒"，症状很迷惑。
- **哈希可比对 ≠ 能握手。** 完整性哈希和密钥本体是两回事，别被 `memcmp` 通过骗了。
- **`fprintd.service` 有 `ProtectSystem=strict` + `ProtectHome=true`。** 库必须是 `/usr/lib` 下的真实文件，不能 symlink 到 `/home`（`ProtectHome` 会让 fprintd 读不到，直接 `cannot open shared object file`）。驱动要写 sealed blob 到 StateDirectory 时也会因为 `/etc` 只读而失败，PSK bootstrap 要用独立的 root 程序做，别走 fprintd 服务。
- **Debian trixie 的 udev 改名。** pkg-config 模块名从 `udev` 变成 `libudev`，且 `libudev.pc` 没有 `udevdir` 变量。构建时要显式传 `-Dudev_rules_dir=/usr/lib/udev/rules.d -Dudev_hwdb_dir=/usr/lib/udev/hwdb.d`。
- **`apt-mark hold` 会锁死替换。** `libfprint-2-2` 被 hold 时装自编译 .deb 会报 Conflicts，先 unhold 装完再 hold 回去。
- **抓虚拟 USB 的明文帧是最省事的逆向手段。** SPICE usbredir 走 `usbmon`，`tcpdump -i usbmon3` 就能拿到 Windows 驱动的真实协议，比静态逆向快得多。
- **`sudo bash` 下 `~` 会展开成 `/root`。** 脚本里的路径要写死绝对路径。
- **下"无解"结论前先全网搜。** 这次一开始差点就认定没救了，实际上有 `mrcook1e-ai/goodix-gm168`、`ejsergeev/libfprint-goodix-gm168sec`、`jaydee101/goodix-5117-linux` 好几个项目。要区分"上游没做"和"我没找到"。

## 最后

这次"失败"其实给了一个挺清楚的判断框架。一块 Goodix 传感器要在 Linux 上可用，需要三件事同时成立：

1. libfprint 有认得它的驱动（加 PID 通常能解决）；
2. 它的 PSK 方案能拿到（虚机重新 provision 是可行的）；
3. **它的匹配算法能在 Linux 侧跑出可分的分数。**

第 3 条是真正的门槛，而且它跟你的努力无关，取决于传感器面积、Goodix 是否开源引擎，以及 Windows 是否允许框架外调用。这三样都不是在 Linux 上能改的。

所以最终我们停了。停下来的理由很明确：**每一层都试到了边界，边界之外是厂商的闭源资产和操作系统的安全策略**。

好的一面是，现在任何人问起这台机器的指纹，你能给出一个完整的、有证据的答案，而不是"Linux 就是不支持指纹"。这两者差别很大。

设备还在，PSK 还在，虚机还在。哪天 Goodix 开源了引擎，或者有人逆出了 `0x442004` 的映射，这些记录就直接能用。

---

*基于 2026-09-28 至 09-30 三天调试的完整日志、抓包与数据整理。*
