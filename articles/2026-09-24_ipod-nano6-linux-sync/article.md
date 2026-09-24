# 在 Linux 上给 iPod Nano 6 加歌：libgpod 的「Unsupported checksum type」是怎么被绕过去的

我有一台 iPod Nano 6（8GB 银色，型号 xC526），是十几年前的老设备。最近把它插到 Debian 机器上，想整理一下曲库、顺便试着加几首歌。整理（备份到电脑）很顺利；但**往 iPod 里写**——删一首歌、加一首歌——却让 rhythmbox 直接段错误崩溃。

报错只有一行，但极其关键：

```
Could not write database to iPod: Unsupported checksum type
```

这篇文章记录从"识别"到"误判无解"再到"找到正确工具"的完整过程，也包含一个我自己的判断失误——值得写下来提醒自己：**别凭印象下"无解"的结论**。

---

## 一、先厘清：iPod 在 Linux 上为什么"插上就能用"

很多人的第一反应是"要装 iPod 驱动吧"。**不需要。** 关键在于 iPod 分两大类：

| 类型 | 传输方式 | Linux 支持 |
|---|---|---|
| 老 iPod（Classic / Nano / Shuffle 等带转盘的） | **USB 大容量存储（UMS）** | 内核自带，零驱动 |
| 新设备（iPhone / iPod touch） | 苹果私有协议（usbmux） | 需 libimobiledevice + usbmuxd |

老 iPod 会把自己**伪装成一个 U 盘**。实测这台 Nano 6 的驱动链是：

```
iPod Nano 6 (USB 05ac:1266)
  └─ usb_storage   内核模块（"USB Mass Storage driver for Linux"）
      └─ sd        内核 SCSI 磁盘驱动
          └─ /dev/sdc1（vfat/FAT32）
              └─ 挂载后就是 iPod_Control/Music/F00–F13 这种结构
```

决定性证据是这一行：

```
$ readlink -f /sys/block/sdc/device/driver
/sys/bus/scsi/drivers/sd
```

它被当成一块**普通 SCSI 磁盘**，和插个 U 盘毫无区别。`usb_storage`、`vfat` 都是内核内置模块，开机即有。

> 顺带澄清一个常见混淆：系统里如果装着 `usbmuxd`/`libimobiledevice`，那是给 iPhone 用的，**和 Nano 6 无关**。

**所以"识别"从来不是问题。问题在"写"。**

---

## 二、iPod 的数据库：为什么"拷文件"没用

老 iPod 不是"扫目录播放"的——它只认一个**数据库文件**。你把 mp3 拷进 `Music/F0X/` 目录，iPod 开机**看不到**，除非同时更新数据库。

而且这个数据库分两代：

| 代次 | 数据库 | 说明 |
|---|---|---|
| 老的（Nano 1–4、Classic 等） | `iTunesDB` | 二进制，`mhbd` 魔数 |
| 新的（**Nano 5G/6G/7G**） | `iTunesCDB` | **压缩版**（zlib），`mhbd` 魔数；旁边还有 SQLite 库 |

你的 Nano 6 属于后者。`SysInfoExtended` 里明确写着：

```xml
<key>SQLiteDB</key><true/>
```

设备真正读取的是 `iPod_Control/iTunes Library.itlp/` 下那套 **SQLite 数据库**（`Library.itdb`、`Locations.itdb` 等），`iTunesCDB` 是给 iTunes 看的压缩镜像。

---

## 三、踩坑：libgpod 报「Unsupported checksum type」

在 Linux 上管理 iPod 的标准库是 **libgpod**（gtkpod、rhythmbox 这些工具都用它）。装好 libgpod-common 后，rhythmbox 能**读**出 iPod 的 380 首歌，也能播放。但一删歌就崩，日志里反复出现：

```
Could not write database to iPod: Unsupported checksum type
```

查下去，根因是 **iPod 的数据库需要"签名"（防篡改校验），而不同代次用不同算法**：

| 设备 | 签名算法 |
|---|---|
| iPod Classic 1G–3G | HASH58 |
| iPod Nano 3G–4G | HASH58 |
| iPod Nano 5G | HASH72 |
| **iPod Nano 6G / 7G** | **HASHAB**（白盒 AES） |
| 更老的（Nano 1–2、Mini 等） | 无签名 |

你的 Nano 6 需要 **HASHAB**。而 libgpod 0.8.3 虽然源码里有 `itdb_hashAB.c`，但**写入路径没有真正实现对 Nano 6G 的 HASHAB 支持**，于是直接报 "Unsupported checksum type"。

我还确认了一个前提：libgpod 甚至没去读 `SysInfoExtended`（strace 显示它只 `access()` 了几个目录），说明它连签名所需的设备信息都没取。

**这里我犯了个错**：看到这个错误，我就下了"Linux 写不了 Nano 6"的结论，还建议用户放弃。这是错的。

---

## 四、正解：`ipodsync` 绕开了 libgpod

被提醒"网上难道没人写这个"之后，我搜了一下——**有，而且不止一个**：

- **`ipodsync`**（PyPI，纯 Python）：支持 Nano 6G/7G，自己实现 HASHAB
- **`iOpenPod`**（GitHub）：Nano 6G/7G 用 WebAssembly 版 HASHAB

`ipodsync` 的思路很关键——**它不碰难的 iTunesCDB**：

> 数据库用 SQLite `iTunes Library.itlp/*.itdb`（不是 `iTunesCDB`，后者设备会自己重生成）。只有 `Locations.itdb` 是受签名保护的（`.cbk`）。

也就是说：
1. 直接写设备真正读取的 **SQLite 库**
2. 只对 `Locations.itdb` 生成 **`.cbk` 签名文件**，用**纯 Python 实现的 hashAB**（白盒 AES，100/100 测试向量）
3. 完全不依赖 libgpod

**签名需要的 FireWireGUID 从哪来？** 从设备 **USB 序列号**自动读取——这解决了一个大坑（iPod 的 `SysInfo*` 文件在 HFS+ 上是压缩的，Linux 驱动读不了）。实测这台设备的：

```
ID_SERIAL=Apple_iPod_000A270022D57C06-0:0
```

正好等于 `SysInfoExtended` 里的 `FireWireGUID`，工具能自动取到。

---

## 五、实操：安装与验证

安装（`pipx` 隔离环境，纯 Python 无需编译）：

```bash
pipx install --backend pip ipodsync
```

只读验证（不写库）：

```bash
export IPODSYNC_MOUNT="/media/axu/ALBERT_S IP"
ipodsync status
# ✅ iPod ready: /media/axu/ALBERT_S IP  (380 tracks)

ipodsync list | head
# [ 2816281227101471536] Aaron Neville — Yes I Love You  (To Make Me Who I Am, 4:46)  F13/YJVZ.mp3
```

写入闭环测试（加一首 → 确认 → 删掉）：

```bash
ipodsync -b add /tmp/test.mp3
# → backed up the library (itlp-20260924-214529)
#   ✓ added "test.mp3" (+ cover art)  ·  pid 8677968574691807434
# ✓ Added 1 track.

ipodsync status          # 381 tracks
ipodsync rm 8677968574691807434
ipodsync status          # 380 tracks（恢复原状）
```

**全部成功。** 而且注意到两个贴心设计：
- 自动**附加封面**（从 mp3 的内嵌 APIC/covr 读取，写入 ArtworkDB + `.ithmb`）
- 每次写库前**自动备份**到 `~/ipod-backups/`，并打印一条 undo 命令

---

## 六、几种工具的真实对比

| 工具 | Nano 6G 写库 | 问题 |
|---|---|---|
| **gtkpod** | ❌ | 太老，`gtkpod_app` 初始化崩溃（与现代 GTK/GLib 不兼容） |
| **rhythmbox** | ❌ | 用 libgpod 写库，报 Unsupported checksum type 并段错误 |
| **libgpod**（底层库） | ❌ | 未真正实现 Nano 6G 的 HASHAB 写入 |
| **ipodsync** | ✅ | 绕开 libgpod，纯 Python 写 SQLite + hashAB |
| **iOpenPod** | ✅ | PyQt6 GUI，Nano 6G/7G 用 WASM 版 HASHAB |

---

## 七、方法论沉淀

1. **"识别" ≠ "写入"**。UMS 让 iPod 插上就能读，但写库是另一层（数据库格式 + 签名），两者独立。
2. **报错信息要追到算法层**。"Unsupported checksum type" 背后是"设备要 HASHAB、库不支持 HASHAB"，而不是"设备坏了"或"配置错了"。
3. **遇到老设备兼容问题，先搜再下结论**。我这次犯的错就是凭"libgpod 报错"推断"Linux 整个不行"，而实际上早有专门工具绕开了它。**一个库的局限 ≠ 一个平台的局限。**
4. **写设备数据库前先备份**。`ipodsync` 的自动备份 + undo 命令是这类工具的正确姿势。
5. **别让 Apple 软件自动同步**。手动加的歌会被一次 iTunes 同步覆盖（保持"手动管理音乐"模式）。

---

## 附：常用命令

```bash
export IPODSYNC_MOUNT="/media/axu/ALBERT_S IP"

ipodsync status                    # 状态
ipodsync list                      # 列出曲目（含 pid）
ipodsync add "song.mp3"            # 加歌（自动附带封面）
ipodsync add -f ~/Music/某专辑      # 加整个目录
ipodsync rm <pid>                  # 删歌（连文件一起删）
ipodsync export ~/Music/ipod       # 导出全部（只读）
ipodsync cover <pid> --image c.jpg # 单独加封面
```

一段小插曲：为了排查，我还顺带装了 `libgpod-common`，它带来一条 **udev 规则**（`90-libgpod.rules`）和 `ipod-read-sysinfo-extended`（读设备生成 `SysInfoExtended`）。这些对 ipodsync 不是必需（它从 USB 序列号取 GUID），但对其它工具可能有用。

---

**结论**：Linux 完全可以给 iPod Nano 6 加歌，用 `ipodsync` 就行。之前我说的"无解"，是没查证就下的错误结论——记住这个教训。
