---
title: "Firefox 160 补上 MKV 的三种音轨：这是追平 Chrome，不是超越"
date: 2026-11-10
slug: firefox-160-mkv-chrome-diff
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Mozilla Firefox 160.0 / 160.0beta 官方 Release Notes + MDN Firefox 160 for developers + Bugzilla meta bug 1422891（含完整时间线与 FLAC/MP3 曾「不在计划」的原话）+ Bug 1991752（Firefox 145 默认启用 matroska）+ Bug 1991746 / 1991747（FLAC / MP3 in Matroska）+ Mozilla dev-platform「Intent to prototype: Matroska playback support」+ Chromium 官方 Audio/Video 编解码支持页 + Chromium commit d081300（Matroska MIME 映射）+ Phoronix 报道（Michael Larabel，2026-11-09）"
original_date: 2026-11-09
original_url: "https://www.phoronix.com/news/Firefox-160-Released"
description: "本文解读 Firefox 160 的 MKV 支持，并纠正一个容易被标题带偏的理解：Mozilla 这次加的不是「MKV 容器支持」，而是「MKV 容器里 FLAC / MP3 / PCM 三种音轨的解码」。容器本身早在 Firefox 145 就通过 media.mkv.enabled 默认启用（Bug 1991752）；145 前后陆续补齐了 AVC/AAC、Opus/Vorbis/VP8/VP9/AV1/HEVC。Bugzilla 里 Mozilla 工程师一年前明确写过「FLAC and MP3 are not implemented yet, as they require additional plumbing and have very limited usage」，而 160 把这最后三种补上了。本文据 Bugzilla 完整时间线还原这件事，并与 Chrome 逐项对照：Chromium 官方 Audio/Video 页的容器清单里早有 Matroska，音频清单里早有 FLAC / MP3 / 三种 PCM；Mozilla 自己在 Intent to prototype 里也写明「Chromium-based browsers already support MKV playback」「Blink: Supported with common codecs such as H.264, AAC, Opus, Vorbis」「WebKit(Safari): Not supported」。差异点分五层列出：容器支持时间（Chrome 多年 vs Firefox 145）、音轨 codec 覆盖（Chrome 早有 FLAC/MP3/PCM，Firefox 160 刚补）、MIME/扩展名识别（Chromium commit d081300 才补 video/matroska→mkv / audio/matroska→mka 映射，此前访问 .mkv 会触发下载）、专有 codec（Chrome 品牌构建才含 AAC/H.264/H.265，Chromium 开源构建默认不含；Firefox 侧对应差异）、MSE 与 MediaRecorder（Firefox 的 Matroska in MSE 仍是 NEW，Chrome 的 MediaRecorder 历史上会产出 MKV 容器文件）。也记录 Firefox 160 另外三项：Web Speech API 识别侧（40 种语言、端侧实时）、PiP 播放速度 0.25x–2.0x、地址栏域名对比度提升，以及官方 Beta notes 里 Phoronix 没提的几项（macOS 上 WebGL 走 Metal、Smart Window 法语、历史记录拖到标签栏、地址栏 Paste and Search、PDF 保存保留 MathML）。"
published: true
---

> 官方：Firefox 160.0 Release Notes <https://www.firefox.com/en-US/firefox/160.0/releasenotes/> ｜ Bugzilla 1422891 ｜ Chromium Audio/Video 支持页
> 报道：Phoronix《Firefox 160 Available With Speech-To-Text, MKV Files With FLAC / MP3 / PCM Audio》（2026-11-09）
>
> 本文依据 Mozilla 官方发布说明、Bugzilla 完整时间线、Chromium 官方支持页与 Chromium 源码提交逐条核对。

## 一、先把标题读对：补的是音轨 codec，不是 MKV 容器

Phoronix 的标题强调「MKV 文件带 FLAC / MP3 / PCM 音频」，Mozilla 官方发布说明的原话是：

> **Firefox now plays Matroska (MKV) files with FLAC, MP3, or PCM audio.**

这句话的重心在 **with FLAC, MP3, or PCM audio**。它不是「Firefox 终于支持 MKV 了」—— **MKV 容器支持早在 Firefox 145 就默认开启了**。

Mozilla 自己的 Bugzilla 总单（1422891，主题为「在 Firefox 中支持 MKV / Matroska 容器」）里写着：

> 目前 Firefox 在 Matroska 中支持 Opus、Vorbis、VP8、VP9、AV1 和 HEVC。该功能由 `media.mkv.enabled` 控制，**自 Firefox 145 起默认启用**。
那句「自 145 起默认启用」值得再读一遍：它说的是**容器解析器**已经在了，`media.mkv.enabled` 这个 pref 就是开关。160 之前，你把 `.mkv` 拖进 Firefox，只要里面的音轨是 Opus / Vorbis / VP8 / VP9 / AV1 / HEVC，是能播的；**放不了的是 FLAC、MP3、PCM 这三种音轨**。

Mozilla 工程师在 meta bug 里一年前写过一句很实在的话，大意是：FLAC 和 MP3 还没实现，因为需要额外的管线改造，而且实际用量非常有限。160 把这句「不在计划」翻了案 —— 三种一起补齐。

所以准确说法是：**Firefox 160 补的是「MKV 容器里三种音轨的解码」，不是「MKV 容器支持」，更不是「终于能放 MKV 了」。**

## 二、先把两层拆开：容器是盒子，codec 是盒子里装的东西

这个问题不拆清楚，后面 Safari 那段一定会绕晕。媒体文件永远是两层：

| 层 | 是什么 | 例子 |
|---|---|---|
| **容器**（container / demuxer） | 把视频轨、音轨、字幕、章节、索引打包的盒子 | MKV / Matroska、MP4、WebM、MOV、M4V、Ogg |
| **编解码器**（codec） | 每一条轨本身怎么压缩 | 视频 H.264 / HEVC / AV1 / VP9；音频 AAC / FLAC / MP3 / PCM / Opus |

**一个容器能装很多种 codec，一个 codec 也能装进不同容器。** 比如 H.264 既能放 MP4 也能放 MKV；AAC 既能放 M4A 也能放 MKV。浏览器要播一个文件，**得先认这个盒子（容器解析），再认盒子里的每一条轨（codec 解码）**，两层都过才行。

这次 Firefox 160 动的只有**第二层里 MKV 盒子的音频部分**。

## 三、和 Chrome 的差异，逐层列出来

这是最容易被「Firefox 终于支持 MKV」这类标题带偏的地方。Mozilla 自己在 2025 年 8 月的 Intent to prototype 邮件里写得很直白：Chromium 系浏览器早就支持 MKV 播放，Gecko 缺这个导致播放失败、被迫下载、要手动转码。按五层对照：

**① 容器支持时间：Chrome 多年，Firefox 145（2025 年）才默认开。**
Chromium 的容器清单里 Matroska 早就在列。Firefox 侧是 meta bug 1422891 追了很多年，直到 Firefox 145 把 `media.mkv.enabled` 默认置为开启。

**② 音轨 codec 覆盖：Chrome 早有，Firefox 160 刚补齐。**
Chromium 官方 Audio/Video 支持页的音频清单里，FLAC、MP3、以及三种 PCM（8-bit unsigned、16-bit signed LE、32-bit float LE，另加 μ-law）都在。也就是说 Firefox 160 这次补的三种，Chrome 用户早就习以为常。Mozilla 的 intent 邮件还列了 Blink 在 MKV 里支持的常见 codec：H.264、AAC、Opus、Vorbis —— 连 **AAC 在 MKV 里**都算进去了。

**③ MIME / 扩展名识别：有个很具体的历史坑。**
Chromium commit `d0813004e27eb2f679dd4a9e26a13baeac4be9f2`（提交说明为「给媒体与网络层补上 Matroska 的 MIME 类型」，4 个文件、39 行新增）才把 `audio/matroska`、`video/matroska`、`audio/x-matroska`、`video/x-matroska` 加进 `mime_util_internal.cc`。**在此之前，即便解码器认得 MKV，浏览器访问 `.mkv` / `.mka` 也可能因为 MIME 不认识而直接触发下载**，不是播放。这是「支持解码」和「认得这个文件类型」两件事。

**④ 专有 codec：Chrome 品牌构建 ≠ Chromium 开源构建。**
Mozilla intent 里写 Blink 支持 H.264 / AAC，指的是 **Google Chrome 品牌构建**；纯 Chromium 开源构建默认不含这些专有 codec（很多 Linux 发行版打包的 Chromium 就缺）。Firefox 走的是系统解码器 / 自带 ffmpeg 的另一套路径，两边在「哪些 codec 能用」上本来就不完全对齐。**别把「Chrome 能放」当成「所有 Chromium 系都能放」。**

**⑤ MSE 与 MediaRecorder：还没拉平。**
Firefox 的「在 MSE 中使用 Matroska」条目在 Bugzilla 里仍是 NEW 状态，自适应流场景还没覆盖；Chrome 的 MediaRecorder 历史上反而会产出 MKV 容器（后来才加 WebM/MP4）。也就是说容器这一层，两边在**生成**和**流式喂入**上仍有差异。

**一句话收这节**：**160 是 Firefox 把「本地 MKV 文件」这条最常用路径追到和 Chrome 差不多齐，不是超越，更不是 Chrome 做不到。**

## 四、Safari 与 iOS 呢？—— 答案卡在容器，不卡在 codec

这是最值得单独说的一段，因为**直觉容易反过来**。

### 结论先给

**iOS 上的 Safari 不能原生播放 MKV / Matroska 容器。** 无论里面装的是 FLAC、MP3、PCM、AAC，还是 H.264、HEVC —— 只要盒子是 `.mkv`，Safari 就不认。

Mozilla 那份 Intent to prototype 在「Other browsers」一栏写得很干脆：Blink（Chromium）支持；**WebKit（Safari）不支持**。Apple 官方的 Safari 视频交付文档也只推荐两条路：流媒体用 HLS，静态文件用 H.264 编码的 MP4。老的 Safari Web Content Guide 里列出的受支持扩展名是 `.mov`、`.mp4`、`.m4v`、`.3gp`，对应 MIME 是 `video/quicktime`、`video/mp4`、`video/x-m4v`、`video/3gpp` —— **没有 `video/x-matroska`**。

### 但你问的 AAC，恰恰是 Safari 的强项

这里就是混淆点：**AAC 支持好不好，和能不能播 MKV 是两件事。**

- AAC 是**编码**。Safari / iOS 对 AAC 的支持几乎是全场最稳的 —— 从最早那代 iPhone 的官方文档起，AAC-LC（最高 48 kHz）就是基线要求；`.m4a`、`.aac`（ADTS）、MP4 里的 AAC、HLS 里的 AAC 都能播。
- Safari 还支持 **ALAC**（Apple Lossless，放在 MP4/M4A 里），这一点 Chrome / Firefox 反而不支持。
- **FLAC** 也能播，iOS 11+ / Safari 13+ 就支持；**MP3** 全平台支持；**PCM** 通过 WAV / AIFF / CAF 支持。

**换句话说：Firefox 160 这次补的 FLAC / MP3 / PCM 三种音轨，Safari 单独拿出来每一种都会播** —— 只不过各自装在 `.flac` / `.mp3` / `.wav` 这些容器里。**把它们塞进 MKV，Safari 立刻就不认了，因为它不认那个盒子。**

### 视频编码格式呢？同样「codec 很强、容器不认」

用户特别问视频编码，答案和音频是对称的：

| 视频 codec | Safari / iOS 支持 | 通常在什么容器 |
|---|---|---|
| H.264 / AVC | 原生、硬件解码，最稳 | MP4 / MOV / M4V / HLS(fMP4) |
| HEVC / H.265 | 原生、硬件解码，Apple 生态最全 | MP4 / MOV / HLS |
| AV1 | 较新设备 / iOS 17+ 部分支持 | MP4 / WebM（视硬件） |
| VP8 / VP9 | iOS / iPadOS 17.4+ 有限支持 | WebM / WebRTC 路径 |
| Dolby Vision | Apple 设备支持 | HLS(fMP4) |

Apple 的 HLS 作者规范明确列出视频编码只能是 H.264、HEVC、Dolby Vision 或 AV1，H.264 的容器必须是 fMP4 或 MPEG-TS。**MKV 从头到尾不在清单里。**

于是有个很反直觉但很关键的结果：**一段 H.264 + AAC 的视频，放在 `.mp4` 里 Safari 播得飞起（这是它的主场），原封不动 remux 成 `.mkv`，Safari 就放不了** —— codec 一个字节没变，变的只是盒子。WebKit 有个被反复提到的 bug（260491）正好演示了这种挑剔：系统对「容器 + codec 字符串」的组合校验很严，MP4 注册机构里没登记的 codec 字符串会直接被判为不可播。

### iOS 上「换个浏览器」也没用

这条必须点明：**iOS / iPadOS 上所有浏览器都是 WebKit**。App Store 审核规则要求浏览网页的 App 使用 WebKit，所以 Chrome for iOS、Firefox for iOS、Edge for iOS 本质都是套了壳的 WebKit（欧盟 DMA 之后才刚开了极窄的口子）。**编码解码由系统 Core Media / AVFoundation 提供，不归浏览器自己决定。**

所以「iOS 上装个 Chrome 就能放 MKV」是不成立的。真要放，只能走**第三方播放器 App**（VLC、Infuse、nPlayer 一类）—— 它们自带 demuxer 与解码器，不走 WebKit 的媒体管线，属于「另一个播放器」，不是「浏览器支持了」。这也是为什么 iOS 上 MKV 的正确建议一直是「装个播放器」或「转成 MP4」，而不是「换个浏览器」。

### 一个容易误导人的例外：GNOME Web

caniuse 那个 MKV feature request 里有人测出「GNOME Web（WebKit-based）支持 MKV」。这不假，但**别拿它推 Safari**：GNOME Web 用的是 WebKitGTK，媒体后端是 Linux 上的 **GStreamer**，装什么 demuxer 取决于系统；Safari / iOS 的 WebKit 后端是 **Core Media / AVFoundation**。同一个 WebKit 分支，媒体栈完全不同。**「WebKit 支持」不等于「Safari 支持」。**

### 这一段的小结

| 问题 | 答案 |
|---|---|
| iOS Safari 能播 MKV 容器吗 | **不能**（Mozilla intent 与 Apple 容器清单一致） |
| 里面是 AAC 呢 | 也不行 —— 卡在容器解析，不卡在 AAC |
| 里面是 H.264 / HEVC 呢 | 也不行 —— 同上；这些 codec 在 MP4 里反而是 Safari 强项 |
| AAC 本身支持吗 | 极好，AAC-LC 是 iOS 基线；另有 ALAC |
| FLAC / MP3 / PCM 本身支持吗 | 都支持，但各自容器（.flac / .mp3 / .wav） |
| 换个 iOS 浏览器 | 没用，全是 WebKit |
| 真要放 MKV | 第三方播放器 App，或转成 MP4 / HLS |

## 五、三方对照：一张表看清

| 维度 | Chrome / Chromium | Firefox 160 | Safari / iOS |
|---|---|---|---|
| MKV 容器 | 早支持（品牌构建含专有 codec） | 145 起默认开 | **不支持** |
| MKV 内 FLAC / MP3 / PCM | 早支持 | **160 刚补** | 不适用（容器不认） |
| MKV 内 AAC / H.264 | 品牌构建支持 | 145 前后陆续补 | 不适用 |
| `.mkv` MIME 识别 | commit d081300 补齐映射 | 随容器支持 | 无 |
| MP4 + H.264 + AAC | 支持 | 支持 | **主场，硬件解码** |
| HEVC / ALAC / Dolby Vision | 部分 / 需硬件 | 有限 | **最全** |
| FLAC / MP3 / PCM（独立容器） | 支持 | 支持 | 支持 |
| MSE 里的 Matroska | 可用 | 仍 NEW | 不适用 |
| iOS 上换引擎 | Android/桌面可换 | iOS 版仍是 WebKit | 全是 WebKit |

**读法**：这张表里 Safari 不是「落后」，是**走了另一条路** —— 它把 MP4 / MOV / HLS 这条链做到极深（含 HEVC、ALAC、Dolby Vision、硬件解码），代价是完全不碰 MKV。Chrome 走「容器最宽」，Firefox 160 刚把「本地 MKV 音轨」这条补齐。三条路线没有谁全面赢。

## 六、顺带记录 Firefox 160 的其它变化

MKV 只是标题里最抓眼的一条。官方 Release Notes 与 Beta notes 里还有：

- **Web Speech API 的识别侧**：端侧实时语音转文字，约 40 种语言（此前 Firefox 主要只有合成侧）；
- **画中画播放速度**：0.25× 到 2.0× 可调；
- **macOS 上 WebGL 改走 Metal**；
- 地址栏域名对比度提升、地址栏「粘贴并搜索」、历史记录可拖到标签栏；
- Smart Window 增加法语；PDF 保存保留 MathML。

这些和 MKV 无关，但放在一起才看得出 160 是一次常规的双周更新，不是「MKV 专版」。

## 七、事实边界（哪些是官方、哪些是推断）

- **「160 补的是音轨 codec 而非容器」**：依据 Mozilla 官方 Release Notes 措辞 + Bugzilla meta bug 1422891 的 `media.mkv.enabled` 自 145 默认启用说明 + Bug 1991752 / 1991746 / 1991747。这是本文最想纠正的一点。
- **Chrome 侧的容器与 codec 清单**：依据 Chromium 官方 Audio/Video 支持页与 commit d081300；「Blink 在 MKV 里支持 H.264/AAC/Opus/Vorbis」出自 Mozilla intent 邮件的转述，指 Google Chrome 品牌构建，**不等于纯 Chromium 开源构建**。
- **Safari / iOS 不支持 MKV 容器**：依据 Mozilla intent 邮件的 Other browsers 栏 + Apple《Delivering Video Content for Safari》与 Safari Web Content Guide 的容器/MIME 清单。**Apple 没有发过「我们不支持 MKV」的公告**，这是从官方支持清单反推的事实，不是官方声明。
- **AAC / ALAC / FLAC / MP3 / PCM 在 Safari 的支持**：依据 Apple 官方文档、caniuse FLAC 表、WebKit bug 260491 与公开 codec 矩阵；各 codec 的具体版本门槛（iOS 11 / Safari 13 / iOS 17.4 / Safari 18.4 等）随系统版本变化，本文按公开资料标注，未逐版本实机验证。
- **「iOS 上全是 WebKit」**：依据 App Store 审核规则 2.5.6 与公开报道；欧盟 DMA 后的浏览器引擎例外仍在演进，本文按当前主流情形陈述。
- **GNOME Web 的差异**：来自 caniuse issue #7347 的社区测试；GStreamer 与 Core Media 的后端区别是本文的技术解释，非该 issue 原话。
- **本文未实机测试**：没有在 iOS 设备、macOS Safari、各 Chromium 发行版上逐个 `canPlayType` 验证。所有结论来自官方文档、源码提交与公开兼容性资料。要在生产环境做交付，请以目标设备实测为准。
- 本文只做格式与引擎能力核对，不构成编解码选型或转码建议。

## 八、结论

**Firefox 160 不是「追上 Safari」，是「在本地 MKV 文件这条路径上追到接近 Chrome」。**

而把 Safari 拉进来对照，真正值钱的不是谁多支持了三种音轨，是那条被标题掩盖的分界：**容器和编码是两层，必须分别过。** Safari 把 MP4/HLS 这条链做到硬件级深，却完全不认 MKV 这个盒子；它连 AAC、H.264、HEVC、ALAC 都支持得比谁都好，但只要这些 codec 被装进 `.mkv`，就一律放不了。

所以下次看到「某浏览器支持 MKV 了」，值得多问一句：**支持的是盒子，还是盒子里哪几条轨？** —— Firefox 160 的答案，是后者里的三种音频。

---

## Sources

- Mozilla Firefox 160.0 Release Notes: <https://www.firefox.com/en-US/firefox/160.0/releasenotes/>
- MDN《Firefox 160 for developers》与 Beta notes
- Bugzilla meta bug 1422891（Matroska 支持总单，含完整时间线）: <https://bugzilla.mozilla.org/show_bug.cgi?id=1422891>
- Bug 1991752（145 默认启用 matroska）｜ Bug 1991746 / 1991747（FLAC / MP3 in Matroska）
- Mozilla dev-platform《Intent to prototype: Matroska playback support》（2025-08-26，含 Other browsers 栏）: <https://groups.google.com/a/mozilla.org/g/dev-platform/c/0ib0_yqiBmk/m/lY27dMnOCgAJ>
- Chromium 官方 Audio/Video 支持页: <https://www.chromium.org/audio-video/>
- Chromium commit `d0813004e27eb2f679dd4a9e26a13baeac4be9f2`: <https://chromium.googlesource.com/chromium/src/+/d0813004e27eb2f679dd4a9e26a13baeac4be9f2>
- Apple《Delivering Video Content for Safari》: <https://developer.apple.com/documentation/webkit/delivering-video-content-for-safari>
- Apple《HLS authoring specification for Apple devices》: <https://developer.apple.com/streaming/hls-authoring-specification-for-apple-devices.html>
- Apple《Safari Web Content Guide – Creating Video》（受支持容器与 MIME 清单）: <https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/CreatingVideoforSafarioniPhone/CreatingVideoforSafarioniPhone.html>
- WebKit bug 260491 / PR 16956（容器+codec 组合校验）: <https://bugs.webkit.org/show_bug.cgi?id=260491>
- caniuse FLAC 支持表: <https://caniuse.com/flac> ｜ caniuse MKV feature request #7347: <https://github.com/Fyrd/caniuse/issues/7347>
- Phoronix《Firefox 160 Available With Speech-To-Text, MKV Files With FLAC / MP3 / PCM Audio》（Michael Larabel，2026-11-09）: <https://www.phoronix.com/news/Firefox-160-Released>
