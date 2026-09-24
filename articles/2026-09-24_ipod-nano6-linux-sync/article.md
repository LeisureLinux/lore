# 在 Linux 上给 iPod Nano 6 加歌：libgpod 的「Unsupported checksum type」是怎么绕过去的

笔者手头有台 iPod Nano 6，8GB，银色，型号 xC526，搁了十几年。最近把它插到一台 Debian 机器上，想整理一下曲库，顺手加几首歌。整理（把歌备份到电脑）没什么波折，但往 iPod 里写就不行了——删一首、加一首，rhythmbox 直接段错误退出。

日志只留下一行，但这一行很要命：

```
Could not write database to iPod: Unsupported checksum type
```

笔者先把这个问题交给 AI 助手分析。它查了一圈，给出的结论是：Linux 写不了 Nano 6，建议放弃。这个结论后来被证明是错的。下文把整件事讲清楚：iPod 为什么会这样，真正的原因是什么，以及最后是怎么解决的。

---

## 一、iPod 在 Linux 上为什么插上就能用

不少人的第一反应是要装 iPod 驱动。其实不用。关键在 iPod 分两大类：

| 类型 | 传输方式 | Linux 支持 |
|---|---|---|
| 老 iPod（Classic / Nano / Shuffle 这类带转盘的） | USB 大容量存储（UMS） | 内核自带，零驱动 |
| 新设备（iPhone / iPod touch） | 苹果私有协议（usbmux） | 需要 libimobiledevice + usbmuxd |

老 iPod 会把自己当成一个 U 盘。这台 Nano 6 的驱动链是这样：

```
iPod Nano 6 (USB 05ac:1266)
  └─ usb_storage   内核模块（"USB Mass Storage driver for Linux"）
      └─ sd        内核 SCSI 磁盘驱动
          └─ /dev/sdc1（vfat/FAT32）
              └─ 挂载后就是 iPod_Control/Music/F00–F13 这种结构
```

判断它是不是被当成普通磁盘，看这一行就够了：

```
$ readlink -f /sys/block/sdc/device/driver
/sys/bus/scsi/drivers/sd
```

它挂在 SCSI 磁盘驱动下面，跟插个 U 盘没有区别。`usb_storage` 和 `vfat` 都是内核内置模块，开机就有。

顺带说一个容易混淆的地方：系统里如果装着 `usbmuxd`、`libimobiledevice`，那是给 iPhone 用的，跟 Nano 6 没有关系。

**识别从来不是问题，问题在写。**

---

## 二、iPod 的数据库：为什么拷文件没用

老 iPod 不扫目录播放，它只认一个数据库文件。把 mp3 拷进 `Music/F0X/`，iPod 开机看不到，除非同时更新数据库。这个数据库还分两代：

| 代次 | 数据库 | 说明 |
|---|---|---|
| 老的（Nano 1–4、Classic 等） | `iTunesDB` | 二进制，`mhbd` 魔数 |
| 新的（Nano 5G/6G/7G） | `iTunesCDB` | 压缩版（zlib），`mhbd` 魔数，旁边还有 SQLite 库 |

Nano 6 属于后者。设备的 `SysInfoExtended` 里写得很明白：

```xml
<key>SQLiteDB</key><true/>
```

设备真正读的是 `iPod_Control/iTunes Library.itlp/` 下那套 SQLite 数据库（`Library.itdb`、`Locations.itdb` 等）。`iTunesCDB` 是给 iTunes 看的压缩镜像。

---

## 三、libgpod 报「Unsupported checksum type」

Linux 上管理 iPod 用得最多的库是 libgpod，gtkpod、rhythmbox 都基于它。装好 libgpod-common 之后，rhythmbox 能读出 iPod 里的 380 首歌，也能播放。但只要删歌就崩，日志里反复出现同一句：

```
Could not write database to iPod: Unsupported checksum type
```

原因在于，iPod 的数据库需要签名（防篡改校验），而不同代次用的算法不一样：

| 设备 | 签名算法 |
|---|---|
| iPod Classic 1G–3G | HASH58 |
| iPod Nano 3G–4G | HASH58 |
| iPod Nano 5G | HASH72 |
| iPod Nano 6G / 7G | HASHAB（白盒 AES） |
| 更老的（Nano 1–2、Mini 等） | 无签名 |

Nano 6 要的是 HASHAB。libgpod 0.8.3 的源码里明明有 `itdb_hashAB.c`，但写入路径并没有真正实现对 Nano 6G 的 HASHAB 支持，于是直接报 Unsupported checksum type。

还有一点，libgpod 甚至没去读 `SysInfoExtended`。用 strace 跟一下就会发现，它只 `access()` 了几个目录，连签名需要的设备信息都没取。

到了这里，AI 助手就下了那个错误结论：既然 libgpod 写不了，那 Linux 就没法给 Nano 6 加歌。**这个判断是错的。一个库做不到，不等于整个平台做不到。**

---

## 四、正解：ipodsync 绕开了 libgpod

被提醒「网上难道没人写这个」之后，笔者去搜了一圈。有，而且不止一个：

- `ipodsync`（PyPI，纯 Python）：支持 Nano 6G/7G，自己实现 HASHAB
- `iOpenPod`（GitHub）：Nano 6G/7G 用 WebAssembly 版 HASHAB

ipodsync 的思路是关键——它不碰难搞的 iTunesCDB：

> 数据库用 SQLite `iTunes Library.itlp/*.itdb`，不是 `iTunesCDB`（后者设备会自己重新生成）。只有 `Locations.itdb` 受签名保护，对应 `.cbk` 文件。

具体做法：

1. 直接写设备真正读取的 SQLite 库
2. 只给 `Locations.itdb` 生成 `.cbk` 签名文件，用的是纯 Python 实现的 hashAB（白盒 AES，官方测试向量 100/100 通过）
3. 完全不依赖 libgpod

签名需要设备的 FireWireGUID。这东西本来在设备的 `SysInfo*` 文件里，但那文件在 HFS+ 上是压缩的，Linux 驱动读不出来。ipodsync 换成从 USB 序列号取：

```
ID_SERIAL=Apple_iPod_XXXXXXXXXXXXXXXX-0:0
```

这串序列号对应的 GUID，正好等于 `SysInfoExtended` 里的 `FireWireGUID`，工具能自动拿到。

---

## 五、安装与验证

pipx 装一个隔离环境就行，纯 Python，不用编译：

```bash
pipx install --backend pip ipodsync
```

先只读验证，不写库：

```bash
export IPODSYNC_MOUNT="/media/$USER/iPod"
ipodsync status
# ✅ iPod ready: /media/<用户名>/iPod  (380 tracks)

ipodsync list | head
# [ 2816281227101471536] Aaron Neville — Yes I Love You  (To Make Me Who I Am, 4:46)  F13/YJVZ.mp3
```

再做一次写入的闭环测试，加一首、确认、删掉：

```bash
ipodsync -b add /tmp/test.mp3
# → backed up the library (itlp-20260924-214529)
#   ✓ added "test.mp3" (+ cover art)  ·  pid 8677968574691807434
# ✓ Added 1 track.

ipodsync status          # 381 tracks
ipodsync rm 8677968574691807434
ipodsync status          # 380 tracks（恢复原状）
```

都成功了。它有两个设计笔者比较喜欢：一是自动附加封面，从 mp3 内嵌的 APIC/covr 读出来，写进 ArtworkDB 和 `.ithmb`；二是每次写库前自动备份到 `~/ipod-backups/`，还顺手打印一条 undo 命令。

---

## 六、几种工具对比

| 工具 | Nano 6G 写库 | 问题 |
|---|---|---|
| gtkpod | 不行 | 太老，`gtkpod_app` 初始化就崩，跟现代 GTK/GLib 不兼容 |
| rhythmbox | 不行 | 底层用 libgpod 写库，报 Unsupported checksum type 并段错误 |
| libgpod（底层库） | 不行 | 未真正实现 Nano 6G 的 HASHAB 写入 |
| ipodsync | 可以 | 绕开 libgpod，纯 Python 写 SQLite + hashAB |
| iOpenPod | 可以 | PyQt6 GUI，Nano 6G/7G 用 WASM 版 HASHAB |

---

## 七、几条经验

识别和写入是两回事。UMS 让 iPod 插上就能读，但写库是另一层，涉及数据库格式和签名，两者互不相干。

报错要追到算法层。Unsupported checksum type 的背后是「设备要 HASHAB，库不支持」，既不是设备坏了，也不是配置错了。

遇到老设备的兼容问题，先搜再下结论。这次的教训就是：单凭一个库的报错，就推断整个平台不行。一个库的局限，跟一个平台的局限是两码事。

写设备数据库之前先备份。ipodsync 的自动备份加 undo 命令，是这类工具该有的样子。

别让 Apple 的软件自动同步。手动加进去的歌，会被一次 iTunes 同步冲掉，记得把 iPod 保持在「手动管理音乐」模式。

---

## 附：常用命令

```bash
export IPODSYNC_MOUNT="/media/$USER/iPod"

ipodsync status                    # 状态
ipodsync list                      # 列出曲目（含 pid）
ipodsync add "song.mp3"            # 加歌（自动附带封面）
ipodsync add -f ~/Music/某专辑      # 加整个目录
ipodsync rm <pid>                  # 删歌（连文件一起删）
ipodsync export ~/Music/ipod       # 导出全部（只读）
ipodsync cover <pid> --image c.jpg # 单独加封面
```

顺便提一句，排查过程中还装过 `libgpod-common`，它带了一条 udev 规则和 `ipod-read-sysinfo-extended`（读设备生成 `SysInfoExtended`）。这些对 ipodsync 不是必需的，它从 USB 序列号取 GUID，但对别的工具可能有帮助。

---

说回来，Linux 完全能给 iPod Nano 6 加歌，用 ipodsync 就可以。那个「无解」的说法，是 AI 没查证就下的结论，不作数。
