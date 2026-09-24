# 声卡整个消失了：一个被删掉的 .tplg 文件，和 SOF 驱动找文件的全部逻辑

开机之后，扬声器没了，麦克风也没了。声音设置里只剩下一个「虚拟输出」，而蓝牙耳机一切正常。

这是我这台搭载 Alder Lake-P 的国产轻薄本（Debian 13 trixie + XanMod 7.2.7 内核）今天早上的状态。查下去的过程比想象中值得写：**根因是一行 `rm`，但真正有意思的是内核怎么找、怎么读、怎么加载那个文件**——以及为什么这次连重启都不是必需的。

先把结论放在前面：

```
dmesg:1076  sof-audio-pci-intel-tgl 0000:00:1f.3: SOF firmware and/or topology file not found.
dmesg:1077  sof-audio-pci-intel-tgl 0000:00:1f.3: Supported default profiles
dmesg:1079  sof-audio-pci-intel-tgl 0000:00:1f.3:  Firmware file: intel/sof/sof-adl.ri
dmesg:1080  sof-audio-pci-intel-tgl 0000:00:1f.3:  Topology file: intel/sof-tplg/sof-hda-generic-2ch.tplg
dmesg:1103  sof-audio-pci-intel-tgl 0000:00:1f.3: error: sof_probe_work failed err: -2
```

`err: -2` 就是 `ENOENT`。**固件 `.ri` 在，拓扑文件 `.tplg` 不在。** 声卡因此根本没有注册到内核里。

---

## 一、症状指纹：蓝牙为什么毫发无伤

先看三层证据，它们指向同一个结论。

**第一层，ALSA 层面完全没有声卡：**

```bash
$ aplay -l
aplay: device_list:279: no soundcards found...
$ arecord -l
arecord: device_list:279: no soundcards found...
$ cat /proc/asound/cards
（空）
```

注意这不是「设备被静音了」或「路由选错了」——`/proc/asound` 下连 `card0` 都不存在。上层任何 mixer 操作都是无意义的。

**第二层，PipeWire 只剩一个兜底设备：**

```
$ wpctl status
Audio
 ├─ Devices:
 ├─ Sinks:
 │  *   35. 虚拟输出                        [vol: 1.00]
 ├─ Sources:
```

那个「虚拟输出」是 PipeWire 的 `auto_null` sink。它的出现本身就是一条信息：**PipeWire 发现系统里一张声卡都没有，为了不让没有输出设备的应用崩溃，临时造了一个黑洞设备。**

**第三层，驱动其实绑定成功了：**

```bash
$ lspci -nnk -s 00:1f.3
00:1f.3 Multimedia audio controller [0401]: Intel Corporation Alder Lake PCH-P High Definition Audio Controller [8086:51c8] (rev 01)
	Kernel driver in use: sof-audio-pci-intel-tgl
	Kernel modules: snd_soc_avs, snd_sof_pci_intel_tgl, snd_hda_intel
```

`Kernel driver in use` 说明 PCI 设备匹配、驱动 probe 都发生了，**只是 probe 的最后阶段失败了**。这一点很关键，它把「驱动没加载」和「驱动加载了但初始化失败」区分开了。

那为什么蓝牙还能用？因为**蓝牙音频走的是完全独立的链路**：蓝牙控制器是挂在 USB 上的独立设备，音频经 HCI SCO/A2DP 由 BlueZ 处理，全程不经过 Intel HDA 控制器、不经过 SOF、不经过 `.tplg`。BLE 固件（`ibt-0040-0041.sfi`）加载成功，蓝牙音频就正常。**「只有蓝牙能用」不是巧合，而是故障域恰好没有覆盖到蓝牙。**

---

## 二、这个故障的自然误诊方向，和它的两个坑

看到「声卡消失」，工程师的第一反应通常是「换个 topology 试试」。这个方向有历史渊源：`sof-hda-generic-*ch.tplg` 这一族文件按数字麦克风通道数分 1/2/3/4ch，确实存在「选错 ch 数导致设备异常」的经典问题。

**但这次的方向是错的，而且路上埋了两个坑。**

### 坑 1：`.bak` 备份文件不是原版

排查时目录里有这样一个文件：

```
-rw-r--r--  44247  9月21日 19:46  sof-hda-generic-2ch.tplg.bak
```

看起来是「上次改动前的备份」，回滚它天经地义。**但它不是。** 校验一下就露馅：

```bash
$ md5sum sof-hda-generic-2ch.tplg.bak sof-hda-generic-2ch-pdm1.tplg
91e6e760a72927deafe158efe29c9572  sof-hda-generic-2ch.tplg.bak
91e6e760a72927deafe158efe29c9572  sof-hda-generic-2ch-pdm1.tplg
```

`.bak` 和 `-pdm1` 变体**完全同哈希**。它是在一次「先备份再覆盖」的操作中，对**已经被替换过的文件**做的快照——本质是一个只有一个麦克风通道的 pdm1 拓扑。用它"回滚"，等于把故障从「没有声卡」换成「少一个麦克风」。

原版文件的哈希应该是这个（来自 Debian 发行包）：

```bash
$ grep "sof-hda-generic-2ch.tplg" /var/lib/dpkg/info/firmware-sof-signed.md5sums
ef04df1833429c628a71a852bc83e4a4  usr/lib/firmware/intel/sof-tplg/sof-hda-generic-2ch.tplg
```

**教训：`.bak` 只证明「某次操作备份过」，不证明「备份的是原始文件」。** 校验哈希、或者干脆从包里重新提取，是唯一可靠的做法。

从包里提取原版的方式（不需要 root）：

```bash
$ apt-get download firmware-sof-signed
$ dpkg-deb -x firmware-sof-signed_2025.01-1_all.deb /tmp/extract
$ md5sum /tmp/extract/usr/lib/firmware/intel/sof-tplg/sof-hda-generic-2ch.tplg
ef04df1833429c628a71a852bc83e4a4   ← 与 dpkg md5sums 一致 ✅
```

### 坑 2：`dpkg -V` 才是权威

比对比哈希更直接的手段是让包管理器自己报告：

```bash
$ dpkg -V firmware-sof-signed
missing     /usr/lib/firmware/intel/sof-tplg/sof-hda-generic-2ch.tplg
```

`missing` 而不是 `5`（内容被改），说明文件是被**整体删除**的，不是被改坏的。这条信息直接把「拓扑内容不对」这个方向排除了。

顺带一提，`/lib` 在这台机器上是 `/usr/lib` 的符号链接：

```bash
$ ls -ld /lib
lrwxrwxrwx 1 root root 7 8月8日 10:11 /lib -> usr/lib
```

所以 `/lib/firmware/...` 和 `/usr/lib/firmware/...` 是同一个文件，别被两个路径绕晕。

---

## 三、内核是怎么找到这个文件的

排除了误诊方向，回到主线：既然文件不存在，那内核**当初是怎么算出这个名字的**？

### 1. 文件名是三段拼出来的，`-2ch` 是内核自己算的

`sound/soc/intel/common/soc-acpi-intel-hda-match.c` 里，机器的拓扑名只给了一个**基名**：

```c
struct snd_soc_acpi_mach snd_soc_acpi_intel_hda_machines[] = {
	{
		.drv_name = "skl_hda_dsp_generic",
		.sof_tplg_filename = "sof-hda-generic",   /* 只有基名，没有 -2ch */
		.tplg_quirk_mask = SND_SOC_ACPI_TPLG_INTEL_DMIC_NUMBER,
	},
};
```

后缀由 `hda_machine_select()`（`sound/soc/sof/intel/hda.c`）里的这段逻辑补齐：

```c
	if (tplg_fixup &&
	    mach->tplg_quirk_mask & SND_SOC_ACPI_TPLG_INTEL_DMIC_NUMBER &&
	    mach->mach_params.dmic_num) {
		tplg_filename = devm_kasprintf(sdev->dev, GFP_KERNEL,
					       "%s%s%d%s",
					       sof_pdata->tplg_filename,
					       "-", mach->mach_params.dmic_num, "ch");
		...
	}
```

而 `dmic_num` 来自 NHLT（Non-HDA Link Table，BIOS 提供的一张音频链路描述表）：

```c
	/* first check for DMICs (using NHLT or module parameter) */
	dmic_num = check_dmic_num(sdev);
	...
	dev_info(sdev->dev, "DMICs detected in NHLT tables: %d\n", dmic_num);
```

这就解释了 dmesg 里那两行的因果关系：

```
dmesg:1075  DMICs detected in NHLT tables: 2                  ← NHLT 说有两个数字麦
dmesg:1080  Topology file: intel/sof-tplg/sof-hda-generic-2ch.tplg   ← 于是要 -2ch
```

路径前缀 `intel/sof-tplg` 来自平台描述符 `sof_dev_desc->default_tplg_path[ipc_type]`，在 `sound/soc/sof/sof-pci-dev.c` 里定义。

**这里有个容易被忽略的实践含义：`-2ch` 不是你选的，是 BIOS 的 NHLT 表决定的。** 如果哪天固件升级把 DMIC 数从 2 改成 4，内核就会去要 `-4ch.tplg`，你对 `-2ch.tplg` 做的任何改动都会被绕过。反过来说，也有办法用模块参数强压：`snd_sof_intel_hda_common dmic_num=N`（`check_dmic_num()` 里 `dmic_num_override` 的用途）。

### 2. 先「试开一次」再真正加载

`.tplg` 不是固件的一部分，而是用户态安装的**描述文件**。SOF 在真正加载它之前，会先做一次纯存在性探测：

```c
/* sound/soc/sof/fw-file-profile.c */
static int sof_test_topology_file(struct device *dev,
				  struct sof_loadable_file_profile *profile)
{
	...
	ret = firmware_request_nowarn(&fw, tplg_filename, dev);   /* 只问「在不在」 */
	if (!ret)
		release_firmware(fw);                              /* 在就立刻释放，不占内存 */
	else
		dev_dbg(dev, "Failed to open topology file: %s\n", tplg_filename);
	return ret;
}
```

调用顺序在 `sof_file_profile_for_ipc_type()` 尾部：

```c
	/* Test only default firmware file */
	if ((!base_profile->fw_path && !base_profile->fw_name) &&
	    sof_platform_uses_generic_loader(sdev))
		ret = sof_test_firmware_file(dev, out_profile, NULL);

	if (!ret)
		ret = sof_test_topology_file(dev, out_profile);
```

失败后走 `sof_print_missing_firmware_info()`，**这就是 dmesg 里那一整段的出处**：

```c
	dev_err(dev, "SOF firmware and/or topology file not found.\n");
	dev_info(dev, "Supported default profiles\n");
	for (i = 0; i <= ipc_type_count; i++) {
		...
		dev_info(dev, " Firmware file: %s/%s\n", desc->default_fw_path[i], ...);
		dev_info(dev, " Topology file: %s/%s\n", desc->default_tplg_path[i], ...);
	}
	...
	dev_info(dev, "Check if you have 'sof-firmware' package installed.\n");
```

看清楚这段代码就能避开一个常见误读：**它把「固件文件」和「拓扑文件」都列了出来，但不代表两个都缺。** 它只是把该 IPC 类型下应有的文件全部打印一遍。真正判定缺失的是两个 `sof_test_*_file()` 的返回值。你这台机器 `.ri` 在、`.tplg` 不在——这也是为什么错误信息是「firmware **and/or** topology」，含糊是设计使然。

### 3. 一个文件名的 15 条候选路径

`firmware_request_nowarn()` → `_request_firmware()` → `fw_get_filesystem_firmware()`，候选目录是一个定长数组（`drivers/base/firmware_loader/main.c`）：

```c
static char fw_path_para[256];
static const char * const fw_path[] = {
	fw_path_para,                          /* 内核参数 firmware_class.path=，最高优先级 */
	"/lib/firmware/updates/" UTS_RELEASE,  /* 例如 /lib/firmware/updates/7.2.7-x64v3-xanmod1 */
	"/lib/firmware/updates",
	"/lib/firmware/" UTS_RELEASE,
	"/lib/firmware",                       /* 本次实际命中的一级 */
};
```

同一个文件名在这 5 个目录里逐个试，每次失败后再试两种压缩变体：

```c
	ret = fw_get_filesystem_firmware(device, fw->priv, "", NULL);
	/* Only full reads can support decompression, platform, and sysfs. */
	if (!(opt_flags & FW_OPT_PARTIAL))
		nondirect = true;
#ifdef CONFIG_FW_LOADER_COMPRESS_ZSTD
	if (ret == -ENOENT && nondirect)
		ret = fw_get_filesystem_firmware(device, fw->priv, ".zst", fw_decompress_zstd);
#endif
#ifdef CONFIG_FW_LOADER_COMPRESS_XZ
	if (ret == -ENOENT && nondirect)
		ret = fw_get_filesystem_firmware(device, fw->priv, ".xz", fw_decompress_xz);
#endif
	if (ret == -ENOENT && nondirect)
		ret = firmware_fallback_platform(fw->priv);   /* 最后去 UEFI 固件里找 */
```

完整候选序列是 **5 个目录 × {无后缀, .zst, .xz} + UEFI 内嵌 = 15 条**，顺序严格，`.zst` 优先于 `.xz`。

读取本身用 `kernel_read_file_from_path_initns()`——注意函数名里的 `initns`：**以内核凭据、在内核的挂载命名空间里读**。这解释了两件事：普通用户加读权限没用；以及为什么改完文件不需要进 chroot 或重启用户态。

顺便做个排除性验证：这台机器上 `/lib/firmware/updates/` 根本不存在，也没有 `/lib/firmware/7.2.7-x64v3-xanmod1/`，所以「有影子副本覆盖了正常文件」这条可能性不成立。

### 4. `.tplg` 里到底是什么

`.tplg` 是 ALSA ASoC topology 二进制容器，由 `.conf` 经 `alsatplg` 编译而成。格式很朴素——**一串块，每块 = 36 字节块头 + 变长 payload**：

```c
struct snd_soc_tplg_hdr {
	__le32 magic;         /* 0x41536F43 */
	__le32 abi;           /* ABI 版本 */
	__le32 version;
	__le32 type;
	__le32 size;          /* 块头自身大小，= 36 */
	__le32 vendor_type;
	__le32 payload_size;
	__le32 index;
	__le32 count;
} __attribute__((packed));
```

照这个结构解析本机的官方文件（44247 字节）：

```text
文件大小    44247 字节
块数量      27
块头大小    36 字节
ABI 取值    全部 = 5
收尾校验    43815(末块偏移) + 396(payload) + 36(块头) = 44247   ✅ 精确覆盖，无残余
```

27 个块的类型分布：

| type | 名称 | 块数 | 内容 |
|---|---|---|---|
| 4 | DAPM_GRAPH | 10 | widget 之间的连接（route） |
| 5 | DAPM_WIDGET | 14 | PCM / HP / SPK / DMIC / HDMI 等 DAPM 部件 |
| 7 | PCM | 1 | 前端 PCM 定义（本例 7 个） |
| 8 | MANIFEST | 1 | 文件清单 |
| 10 | BACKEND_LINK | 1 | 后端 DAI link（本例 6 条） |

**magic 有个阅读陷阱**：`0x41536F43` 按小端落在字节流里是 `43 6f 53 41`，即 ASCII 字符串 **`CoSA`**——是 `ASoC` 的**反写**。宏定义在 `include/uapi/sound/asoc.h`：

```c
#define SND_SOC_TPLG_MAGIC		0x41536F43 /* ASoC */
```

（我自己第一版解析脚本就栽在这里：把块头里的 `size` 字段当成了 payload 长度，偏移算成 `off += 36 + 36`，撞进一段全零数据，误报「第二块 magic = 0x00000000」。正确公式是 `off += size + payload_size`；因为 `size` 恒等于 36，很多人会误以为它就是「块总长」。）

内核侧的解析器 `snd_soc_tplg_component_load()`（`sound/soc/soc-topology.c`）**不是顺序单遍**，而是按 8 个 pass 反复扫描整个文件：

```c
#define SOC_TPLG_PASS_MANIFEST		0
#define SOC_TPLG_PASS_VENDOR		1
#define SOC_TPLG_PASS_CONTROL		2
#define SOC_TPLG_PASS_WIDGET		3
#define SOC_TPLG_PASS_PCM_DAI		4
#define SOC_TPLG_PASS_GRAPH		5
#define SOC_TPLG_PASS_BE_DAI		6
#define SOC_TPLG_PASS_LINK		7
```

源码注释解释了原因：块在文件里不保证有序，分轮处理才能确保 component driver 在 widget / DAPM 图建立之前已经拿到 vendor 数据。

### 5. ABI 校验：只看 MAJOR

日志里这一行很容易让人紧张：

```
Topology: ABI 3:22:1 Kernel ABI 3:23:1
```

拓扑的 ABI minor (22) 比内核 (23) 落后一版。会不会不兼容？不会。规则在 `include/uapi/sound/sof/abi.h`：

```c
#define SOF_ABI_VERSION_INCOMPATIBLE(sof_ver, client_ver)		\
	(SOF_ABI_VERSION_MAJOR((sof_ver)) !=				\
		SOF_ABI_VERSION_MAJOR((client_ver))			\
	)
```

**只比较 MAJOR。** 两者 MAJOR 都是 3 → 兼容，minor 差异是正常的向后兼容（固件包 2025.01 配 2026 年份的内核）。真正会导致加载失败的只有 MAJOR 不等，那时唯一的解法是换 `firmware-sof-signed` 包版本。

顺带说明：`firmware-sof-signed` 这个包**只决定文件的内容版本，不决定文件名**。文件名是内核算的。

### 6. 完整时序：拓扑为什么加载得那么晚

把上述环节串起来，`sof_probe_continue()`（`sound/soc/sof/core.c`）的顺序是：

```text
snd_sof_probe()                          DSP PCI 硬件探测
  ↓
sof_machine_check()                      ACPI/DMI 匹配 → 决定 skl_hda_dsp_generic 和 tplg 名
  ↓
sof_select_ipc_and_paths()          ★  上面的「存在性预检」就在这里，失败即返回
  ↓
snd_sof_dbg_init() → snd_sof_ipc_init()
  ↓
snd_sof_load_firmware()                  读 intel/sof/sof-adl.ri
  ↓
snd_sof_run_firmware()                   启动 DSP、等待 FW_READY、读回 fw_version / ABI
  ↓
devm_snd_soc_register_component()        注册 DSP component
  ↓
snd_sof_machine_register()               触发 skl_hda_dsp_generic probe
  ↓
  └─ snd_soc_tplg_component_load()   ★  这时才真正 request_firmware(tplg) 并打印 "loading topology"
```

**关键认识：拓扑不是固件的一部分。** DSP 固件先启动成功，拓扑随后才被解析。所以缺 `.tplg` 不会让 DSP 起不来，而是让 machine driver 建不出 `snd_card`。于是就有了那个看起来完全不像「文件缺失」的错误：

```
error: sof_probe_work failed err: -2
```

---

## 四、热重载：为什么这次连重启都不需要

修好它只需要一条 `cp`，加上「让驱动重新 probe 一次」。而重新 probe 不需要重启——driver core 早就给了入口。

### 1. sysfs 的两个属性

```bash
$ ls /sys/bus/pci/drivers/sof-audio-pci-intel-tgl/
0000:00:1f.3  bind  module  new_id  remove_id  uevent  unbind
```

`bind` / `unbind` 由 `drivers/base/dd.c` 实现，语义就是「把这个设备从驱动上摘掉 / 重新绑上」，等价于一次完整的 remove + probe，但**不需要卸载内核模块**（模块还被别的设备引用着时也卸不掉）：

```bash
sudo sh -c 'echo 0000:00:1f.3 > /sys/bus/pci/drivers/sof-audio-pci-intel-tgl/unbind'
sleep 2
sudo sh -c 'echo 0000:00:1f.3 > /sys/bus/pci/drivers/sof-audio-pci-intel-tgl/bind'
```

### 2. 坑：probe 是异步的

```c
int snd_sof_device_probe(struct device *dev, struct snd_sof_pdata *plat_data)
{
	...
	ret = snd_sof_probe_early(sdev);
	if (ret < 0)
		return ret;

	if (IS_ENABLED(CONFIG_SND_SOC_SOF_PROBE_WORK_QUEUE)) {
		INIT_WORK(&sdev->probe_work, sof_probe_work);
		schedule_work(&sdev->probe_work);   /* 丢进工作队列，立刻 return 0 */
		return 0;
	}
	return sof_probe_continue(sdev);
}
```

这台机器上 `CONFIG_SND_SOC_SOF_PROBE_WORK_QUEUE=y`（在 `/boot/config-*` 里可查）。所以 `bind` 的 `write()` **瞬间返回**，真正的初始化交给工作队列：

```c
static void sof_probe_work(struct work_struct *work)
{
	...
	ret = sof_probe_continue(sdev);     /* 干实活：预检 → 读 .ri → 起 DSP → 读 tplg */
	if (ret < 0)
		dev_err(sdev->dev, "error: %s failed err: %d\n", __func__, ret);
}
```

**实践含义有三条：**

1. 写完 `bind` 不要立刻用 `dmesg | tail` 判断成败，等 1–3 秒；
2. `bind` 命令本身不报错**不代表成功**，唯一判据是之后 `aplay -l` 里有没有 `card 0`；
3. 因为 `sof_probe_work` 是异步的，连续快速 unbind/bind 有撞上正在运行的 work 的风险，中间加个 `sleep`。

### 3. 为什么这次的热重载是"干净"的

看 `snd_sof_device_remove()` 的分支：

```c
	if (sdev->fw_state > SOF_FW_BOOT_NOT_STARTED) {
		/* 完整清理：DSP 掉电、i915 audio component 解绑、IPC 释放… */
		sof_fw_trace_free(sdev);
		snd_sof_dsp_power_down_notify(sdev);
		snd_sof_ipc_free(sdev);
		snd_sof_free_debug(sdev);
		snd_sof_remove(sdev);
		snd_sof_remove_late(sdev);
		sof_ops_free(sdev);
	} else if (aborted) {
		/* probe_work 根本没跑成 */
		snd_sof_remove_late(sdev);
		sof_ops_free(sdev);
	}
```

本次的路径是**最理想的**：probe 因为 `.tplg` 缺失而失败，`sof_probe_continue()` 的错误出口把设备状态置回

```c
	/* all resources freed, update state to match */
	sof_set_fw_state(sdev, SOF_FW_BOOT_NOT_STARTED);
```

于是 `fw_state == NOT_STARTED`，unbind 时两个分支都不进——**没有 DSP 电源域、没有 i915 的 wakeref 需要收拾**。bind 从零开始，完全干净。

换句话说：**「从来没能成功过」的设备，热重载反而最安全。** 相反，如果 DSP 已经 `BOOT_COMPLETE`，unbind 会走完整清理路径，涉及 i915 display audio 的电源域。内核在这一带历史上出过 wakeref 未释放的 bug，对应补丁是 *ASoC: SOF: Core: Add remove_late() to sof_init_environment failure path*。那种情况下热重载通常也能用，但一致性不如这次。

### 4. 热重载的能力边界

顺手把「哪些改动能靠热重载生效」一次说清：

| 想改的东西 | 热重载能否生效 |
|---|---|
| 恢复 `sof-hda-generic-2ch.tplg` | ✅ 能（本文实测生效） |
| 换用另一个 tplg（拷成同名文件） | ✅ 能，bind 时会重新 `request_firmware` |
| `snd_sof.sof_debug`、`fw_path` 等模块参数 | ❌ 权限 `0444`，只读，见 `/sys/module/snd_sof/parameters/` 全是 `-r--r--r--` |
| `snd_sof_intel_hda_common` 的 `dmic_num=` / `hda_model=` | ⚠️ 改 `/etc/modprobe.d/*.conf` 后需重插模块；被依赖链牵连，通常仍要重启 |
| `i915.force_probe=` 等内核命令行参数 | ❌ 只读于 boot |
| `firmware_class.path=` | ❌ boot 参数 |

### 5. 一个容易被误当成故障的日志

修好之后，这条依然会出现：

```
skl_hda_dsp_generic: hda_dsp_hdmi_build_controls: no PCM in topology for HDMI converter 3
```

它**不是故障**。原因：`-2ch` 拓扑本身不含 HDMI converter 3 的 PCM 节点，而 ALC256 向系统报告了 3 个 HDMI 转换器。两边数量对不上，内核礼貌地提示一句，仅此而已。**它是噪音，别为它去改拓扑。**

---

## 五、真正的根因：一行 `rm`

修好了，但「文件为什么会不在」还没回答。答案是 shell 历史：

```bash
# 时间戳换算后的完整时间线
2026-09-20 21:30  sudo cp sof-hda-generic-4ch.tplg  → sof-hda-generic-2ch.tplg
2026-09-20 21:32  sudo cp sof-hda-generic-2ch-pdm1.tplg → sof-hda-generic-2ch.tplg
2026-09-21 19:46  sudo cp sof-hda-generic-2ch.tplg → sof-hda-generic-2ch.tplg.bak
                  sudo cp sof-hda-generic-4ch.tplg  → sof-hda-generic-2ch.tplg
2026-09-23 07:36  sudo rm sof-hda-generic-2ch.tplg        ← 就是这一步
2026-09-23 07:41  重启 → 声卡消失
```

07:36 删掉，07:41 重启，07:44 用户报告没声音。时间线严丝合缝。

值得注意的是**前面那两次 `cp` 覆盖为什么没造成这次故障**。因为「文件内容不对」和「文件不存在」是两个不同的失败模式：

- 文件存在但内容不匹配（比如把 4ch 塞进 2ch 的名字）→ 内核能读到、能解析，只是 profile 建立不全，通常表现为「有设备但声音不对」；
- 文件不存在 → `sof_select_ipc_and_paths()` 的存在性预检直接失败，**整个 probe 中止，一张声卡都不注册**。

后者是硬失败，症状也更彻底。而上游排查者（包括我）往往把这两类混为一谈，于是反复在「换哪个 ch 数」上打转。

### 修复三行

```bash
# 1) 放回原版文件（md5 必须等于 ef04df1833429c628a71a852bc83e4a4）
sudo cp <原版文件> /usr/lib/firmware/intel/sof-tplg/sof-hda-generic-2ch.tplg

# 2) 热重载，无需重启
sudo sh -c 'echo 0000:00:1f.3 > /sys/bus/pci/drivers/sof-audio-pci-intel-tgl/unbind'
sleep 2
sudo sh -c 'echo 0000:00:1f.3 > /sys/bus/pci/drivers/sof-audio-pci-intel-tgl/bind'

# 3) 验证（等 3 秒再看）
sleep 3
aplay -l
```

修复后的正确状态：

```bash
$ cat /proc/asound/cards
 0 [sofhdadsp      ]: sof-hda-dsp - sof-hda-dsp
                      ...

$ aplay -l | grep "^card"
card 0: sofhdadsp [sof-hda-dsp], device 0: HDA Analog (*) []
card 0: sofhdadsp [sof-hda-dsp], device 3: HDMI1 (*) []
card 0: sofhdadsp [sof-hda-dsp], device 4: HDMI2 (*) []
card 0: sofhdadsp [sof-hda-dsp], device 5: HDMI3 (*) []
card 0: sofhdadsp [sof-hda-dsp], device 31: HDA Analog Deep Buffer (*) []

$ arecord -l | grep "^card"
card 0: sofhdadsp [sof-hda-dsp], device 0: HDA Analog (*) []
card 0: sofhdadsp [sof-hda-dsp], device 6: DMIC (*) []
card 0: sofhdadsp [sof-hda-dsp], device 7: DMIC16kHz (*) []
```

扬声器、耳机、模拟麦、DMIC 全部回来了。

---

## 六、可以带走的东西

**诊断顺序（按信息量从高到低）：**

```bash
aplay -l                              # 一张声卡都没有？→ 驱动层问题，不是 mixer 问题
lspci -nnk -s 00:1f.3                 # driver in use 有没有？→ 区分「没加载」和「加载失败」
journalctl -k -b | grep -E "sof|snd_hda"   # 找 err / -ENOENT
sudo dmesg -T | grep -E "Topology file|err:"
dpkg -V firmware-sof-signed           # 权威判定：文件是被删了还是被改了
```

**这次的三条经验：**

1. **「没有声卡」和「声卡不对」要分开处理。** `/proc/asound/cards` 为空 = 硬失败，别去调 mixer、别去换拓扑；`dpkg -V` 一条命令就能定性。

2. **`.bak` 不等于原版。** 校验哈希，或者从发行包里重新提取——两种方式都只要几秒钟，而盲目回滚会把一个故障换成另一个。

3. **先确认「问题在哪一层」，再决定「改成什么」。** 这次真正的成本不在于修复（三行命令），而在于前面在「换哪个 ch 数的拓扑」上绕的那几圈——因为症状（设备消失）和误判方向（拓扑内容不对）确实有表面上的相似性。

**关于热重载**，记住一句就够：`/sys/bus/pci/drivers/<drv>/{unbind,bind}` 能替代大部分「改完驱动相关文件要重启」的场景，但 SOF 的 probe 是**异步**的——命令返回不等于 probe 完成，必须用 `aplay -l` 这种结果性证据来判定，而不是命令的退出码。

最后一件事：这个文件将来还可能被误删。要根治，就把它纳入配置管理；或者给它加不可变属性——但那样 `apt upgrade firmware-sof-signed` 会失败，得先解锁：

```bash
sudo chattr +i /usr/lib/firmware/intel/sof-tplg/sof-hda-generic-2ch.tplg
```

对一个被删过一次的文件来说，这可能比下次再走一遍上面这套排查流程便宜得多。
