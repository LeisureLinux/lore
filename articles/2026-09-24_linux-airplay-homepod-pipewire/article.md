# Linux 把本地 mp3 推到 HomePod：从 atvremote 到 mpv 到 PipeWire 升级的完整排障

需求很简单：一台 Debian 机器上存了几十 GB 的 mp3，想把它推到房间里的 HomePod 音箱播放。原以为是个「点一下就行」的小事，结果一路从 `atvremote` 试到 `mpv`、再到升级 PipeWire，中间撞上一个极其隐蔽的「播到 35 秒突然没声」的坑。这篇文章把整个过程和背后的原理完整记录下来。

先说结论：**最终解法是把 PipeWire 从 1.4.2 升到 1.4.9（走 trixie-backports），断流问题彻底消失**。下面按时间线复盘，每一步都讲清楚「为什么这么走、原理是什么、踩了什么坑」。

---

## 一、起点：atvremote（pyatv）方案

最早用的是 `atvremote`，它是 `pyatv` 库附带的命令行工具，通过 Apple 的私有协议（AirPlay / MediaRemote）控制 Apple TV 和 HomePod。当时的 `play.sh` 长这样：

```bash
#!/bin/bash
MDIR="$HOME/Music"
if [ -r "$1" ]; then
	atvremote -n StudyRoom stream_file="$1" 2>/dev/null
	exit
fi
! find ${MDIR} -name "*.mp3" | shuf | xargs -I {} atvremote -n StudyRoom stream_file={} 2>/dev/null && echo "exit with error"
```

这个方案**能出声**，但有几个问题：

1. **每首歌重建一次 AirPlay 会话**。`find | shuf | xargs -I {}` 会对每一首 mp3 单独起一个 `atvremote stream_file` 进程，意味着每首歌之间都要重新握手、重新建流，曲目切换有停顿，还容易丢歌首。
2. **错误被 `2>/dev/null` 吞掉**。失败静默，出问题看不到原因。
3. **`! ... && echo` 的逻辑反直觉**，实际是失败才提示，但读起来像"成功才提示"。

更重要的是，`atvremote stream_file` 走的是 pyatv 的 AirPlay 推流路径，它**自己管理 RTSP 会话**，虽然能播，但它是「每首一个进程」的黑盒，无法做播放列表、无法暂停切歌，也无法显示封面歌词。

所以下一步自然是想换成 mpv——Linux 上最顺手的播放器，有键盘控制、有图形界面、能播列表。

---

## 二、换 mpv：撞上「35 秒断流」

mpv 本身不直接支持 AirPlay 输出，但它能通过 PipeWire 输出音频。PipeWire 有一个 `raop-sink` 模块（RAOP = Remote Audio Output Protocol，即 AirPlay 的底层协议），能把 HomePod 变成系统里一个普通的音频 sink。于是脚本改成：

```bash
SINK=$(pactl list short sinks | awk '/raop_sink/{print $2; exit}')
mpv --audio-device="pipewire/$SINK" --no-video --shuffle "${files[@]}"
```

这一换，问题来了：**播放约 35 秒后，音乐还在走（进度条在动、sink 显示 RUNNING），但 HomePod 没声音了**。

这个现象非常反直觉——「看起来一切正常，但就是没声」。要定位它，得先理解 AirPlay 的协议结构。

---

## 三、原理：为什么「还在播」但「没声」

AirPlay（RAOP）推流分**两条独立通道**：

| 通道 | 协议 | 作用 | 断了会怎样 |
|---|---|---|---|
| **控制通道** | RTSP over TCP（端口 7000） | 握手、协商编码、音量同步、时间戳对齐 | 音频流变成「无头」数据，HomePod 不再出声 |
| **音频通道** | RTP over UDP | 承载 PCM/ALAC 音频数据 | 直接没声，但 sink 会报错 |

关键在这里：**两条通道是独立的**。当 HomePod 把控制通道（TCP 7000）断掉后，音频通道（UDP）可能还在发——于是本机的 mpv 看到 sink 还在 RUNNING、进度还在走，就以为一切正常；但 HomePod 那边已经因为失去控制通道而停止出声了。

这正是「还在播但没声」的根因。日志证实了这一点：

```
mod.raop-sink: sess.latency.msec 250.000000 should be an integer multiple of rtp.ptime 7.755102
mod.raop-sink: error -32 (断开的管道)
mod.raop-sink: error sending control packet: -9
```

- `error -32` = EPIPE，控制通道（RTSP/TCP）被对端断开；
- `error -9` = EBADF，之后模块还在往一个已失效的 socket 写数据，每秒刷一次。

而 `-9` 那条日志最迷惑人：它刷得很凶，让人以为是网络抖动，其实它只是「控制通道已死」的**后续症状**，不是根因。

---

## 四、深挖根因：HomePod 主动断连接

为了确认不是网络问题，我做了一个关键观察——盯着 TCP 7000 连接的状态：

```
[11:37:16] sink=RUNNING tcp7000=1
[11:37:18] sink=RUNNING tcp7000=0   # 控制通道断了
[11:37:20] sink=RUNNING tcp7000=0
```

约 35 秒后，`tcp7000` 从 1 变 0——控制通道被断开，但 sink 依然是 RUNNING、mpv 依然在播。这坐实了「控制通道静默断开、音频通道假活」的判断。

社区里有人进一步抓包确认：**是 HomePod 主动终止控制通道**（TCP 7000），断连后 HomePod 还会发 mDNS cache-flush 包——这是「协议层拒绝连接」的明确信号。也就是说，**不是网络抖动，是 PipeWire 的 raop-sink 实现与 HomePod 的 AirPlay 协议不兼容**，HomePod 在约 30 秒后撤掉了会话。

其中一个关键线索是日志里的加密类型：

- PipeWire 1.4.2 的 raop-sink 默认 `raop.encryption.type = none`；
- 而 HomePod 要求 **SAP25（FairPlay）加密**的 AirPlay 会话。

加密协商对不上，HomePod 就在 keep-alive 超时后断掉了连接。这解释了为什么调 `raop.latency.ms` 参数「只能多撑几秒」——治标不治本，真正的病根在加密协商。

---

## 五、绕行：raop_play 稳定，但没有图形界面

在确认 PipeWire 的 raop-sink 是病根后，我先找了一个绕行方案：`raop_play`（Rust 写的独立 AirPlay 推流工具）。用 `ffmpeg` 把 mp3 解码成 PCM 喂给它：

```bash
ffmpeg -re -f concat -safe 0 -i playlist.txt -f s16le -acodec pcm_s16le -ar 44100 -ac 2 - \
  | raop_play -v 50 -p 7000 192.168.68.158 -
```

实测这个方案**稳定播了 150 秒零断流**——因为 `raop_play` 自己正确实现了 HomePod 需要的加密握手和 keep-alive。

但它有两个致命缺点：

1. **没有图形界面**，看不到封面、歌词、进度；
2. **音量/暂停/切歌都要自己写**（后来补了个 `hpctl` 控制音量，但暂停切歌做不了）。

所以问题又绕回来了：**想要 mpv 的体验，就必须让 PipeWire 的 raop-sink 修好**。

---

## 六、最终解：升级 PipeWire 1.4.2 → 1.4.9

这时候做了个决定性的验证：编译最新的 PipeWire master（当时是 1.7.0），发现它的 raop-sink **自动选择了 `fp_sap25` 加密**：

```
mod.raop-discover: loading module args:'{... "raop.encryption.type":"fp_sap25" ...}'
```

这证明上游**已经修了 HomePod 的加密协商问题**——只是 Debian trixie 的 1.4.2 太旧，没吃到这个修复。

于是走 **trixie-backports** 源，把 PipeWire 全家桶从 1.4.2 升到 **1.4.9**（backports 官方打包，依赖 `libc6 >= 2.38` 与旧版一致，不拉高基础库，风险低、可回滚）。

升级后，`mpv → PipeWire raop-sink → HomePod` 的断流问题**彻底消失**。

**升级脚本**（回滚脚本同理，显式降回 1.4.2 即可）：

```bash
sudo apt-get update
sudo apt-get install -y -t trixie-backports \
    pipewire pipewire-bin pipewire-pulse pipewire-alsa pipewire-audio \
    libpipewire-0.3-0t64 libpipewire-0.3-modules libpipewire-0.3-common \
    libspa-0.2-modules libspa-0.2-bluetooth gstreamer1.0-pipewire \
    wireplumber libwireplumber-0.5-0

systemctl --user restart pipewire.service pipewire-pulse.service wireplumber.service
```

这里有个关键决策点：**为什么用 backports 而不是 sid？** 因为 sid 的 1.6.9 可能连带拉高 glibc 等基础库，风险大；而 backports 的 1.4.9 是官方为 trixie 专门打包的，依赖干净，`apt-get -s` 模拟安装显示「升级 15 个、新增 0、卸载 0」。

---

## 七、彩蛋：图形窗口 + 封面 + 歌词

升级完成后，顺手把播放体验也补全了。mpv 原生就支持显示内嵌封面（attached_pic 会被识别为 `Image` 视频轨）和加载同名 `.lrc` 歌词（`sub-auto=fuzzy`）：

```bash
mpv --no-config --audio-device="pipewire/$SINK" \
    --force-window=yes --sub-auto=fuzzy --shuffle "${files[@]}"
```

- `--force-window=yes`：弹出图形窗口；
- 去掉 `--no-video`：让内嵌封面显示出来；
- `--sub-auto=fuzzy`：自动加载与 mp3 同名的 `.lrc` 歌词，按时间高亮滚动。

实测验证：`Image --vid=1 "Album cover" (png 1280x720)` + `Subs --sid=1 'lrc' (text)` + `sink RUNNING`，封面、歌词、声音三者齐活。

> 一个小坑：`--audio-display` 在 mpv 0.40 里是三态选项，`--audio-display=yes` 会报错、裸写 `--audio-display` 又要求参数。实际上它默认就开启，**根本不用显式指定**——只要别加 `--no-video` 就行。

---

## 八、总结

### 各方案对比

| 方案 | 断流 | 图形界面 | 封面/歌词 | 暂停切歌 | 结论 |
|---|---|---|---|---|---|
| atvremote（pyatv） | 无（但每首歌重连） | 无 | 无 | 无 | 起步方案，体验差 |
| mpv + PipeWire 1.4.2 | **35s 必断** | 有 | 有 | 有 | 病根在 raop-sink 加密协商 |
| raop_play（独立推流） | 无 | 无 | 无 | 无 | 稳定但体验残缺 |
| **mpv + PipeWire 1.4.9** | **无** | **有** | **有** | **有** | **最终解** |

### 方法论沉淀

1. **「还在播但没声」要想到双通道协议**。AirPlay 的控制通道（RTSP/TCP）和音频通道（RTP/UDP）独立，控制通道断了音频通道可能假活，这是这类「假正常」的经典来源。

2. **日志里的 `-9`（EBADF）是症状不是根因**。它表示「往失效的 socket 写数据」，真正要追的是它之前的 `-32`（EPIPE）——那是连接被对端断开的时刻。

3. **加密协商是 HomePod 断连的根因**。PipeWire 1.4.2 用 `none`，HomePod 要 SAP25；1.4.9 修复了自动选择。升级比调 latency 参数有效得多。

4. **Debian 升级优先 backports 而非 sid**。backports 是官方为当前发行版打包的、依赖干净可回滚；sid 可能拉高基础库，风险不可控。

5. **先看代码再动手、改动可回滚**。这次升级全程保留了回滚脚本和版本清单，出问题随时能退回 1.4.2。

### 最终可用的脚本

- `newplay.sh`：mpv 弹窗播放 + 封面 + 歌词，声音走 HomePod；
- `hpctl`：独立的音量控制命令（`hpctl up/down/vol N/mute`），与播放并行。

至此，从「点一下」到「点一下真的能用」，中间隔着一个协议加密协商的坑。希望这篇复盘能帮到下一个想在 Linux 上推流到 HomePod 的人。
