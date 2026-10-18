---
title: "从「能免费在车里唱歌」出发，我为什么会撞上三种歌词格式"
date: 2026-10-18
slug: lrc-ttml-karaoke-formats
tags: [LRC, LRC A2, Enhanced LRC, TTML, TTML2, DFXP, W3C, 歌词格式, 卡拉OK, 逐词歌词, SPL, Salt Player, 椒盐音乐, YRC, 网易云, QRC, QQ音乐, KRC, 酷狗, 私有格式, 加密, 格式碎片化, LRCLIB, Musixmatch, Spotify, Gramophone, 留声机, Steve, OnePlayer, play:Sub, Android Auto, CarPlay, 车载, 免费软件, 离线播放器, Charabia, 分词]
category: 开源/工具
author: FreeLAMP.com
original_source: "Wikipedia：LRC (file format)、Timed Text Markup Language；W3C TTML1/TTML2 规范；AMLL Docs「Lyric Formats」；LRCLIB API 文档与官方说明；Musixmatch API 定价页；Gramophone 与 Steve 官方说明"
original_author: "维基百科编者；W3C Timed Text Working Group；AMLL 项目；LRCLIB 作者；FoedusProgramme（Gramophone）；Hamza RABI（Steve）"
original_date: 2026-10-18
original_url: "https://en.wikipedia.org/wiki/LRC_(file_format)"
description: "起点很简单：想在自己拥有的音乐上，免费地在车里跟着歌词唱歌。车载是硬需求，而 CarPlay 与 Android Auto 互不兼容，这直接锁死了平台；「免费」又把大部分带逐词功能的播放器排除掉了。筛到最后只剩两个能用的，它们的逐词格式却完全不同——于是同一批歌词不得不转换两次。这篇从这三个出发点讲起，把 LRC、A2、TTML 的来历，八种逐词方言的归属，以及 QQ 音乐 QRC 与酷狗 KRC 为什么是加密的，一并讲清楚。"
published: true
---

> 一手材料：[Wikipedia：LRC (file format)](https://en.wikipedia.org/wiki/LRC_(file_format))、[Wikipedia：Timed Text Markup Language](https://en.wikipedia.org/wiki/Timed_Text_Markup_Language)、[W3C：TTML1 第三版（2018-11-08）](https://www.w3.org/TR/2018/REC-ttml1-20181108/)、[W3C：TTML2（2018-11-08）](https://www.w3.org/TR/ttml2/)、[AMLL Docs：Lyric Formats](https://amll.dev/en/guides/lyric/formats.html)、[LRCLIB API 文档](https://lrclib.net/docs)、[Musixmatch API 定价](https://about.musixmatch.com/api-pricing)
> 播放器来源：[Gramophone（F-Droid / GitHub，GPLv3）](https://f-droid.org/packages/org.akanework.gramophone/)、[Steve: Offline Music Player（App Store）](https://apps.apple.com/us/app/steve-offline-music-player/id6751122850)
> 实测环境（**2026-10-18**）：Android 14 手机 + Gramophone 1.1.2；iPhone + Steve（App 名显示为「无广告音乐播放器」）。

## 一句话结论

**我的要求只有三条：在自己拥有的本地音乐上、免费地、能在车里跟着逐字歌词唱。** **这三条把市面上的播放器筛到只剩两个，而这两个的逐词歌词格式还互不兼容——于是同一批歌词，我不得不转换两次。** **顺着「为什么格式不通用」这个问题往下挖，挖出来的是一整层没人讲清楚的事：八种逐词方言，只有一个是国际标准，其中两家音乐平台的格式还是加密的。**

## 一、起点：三个不能让步的要求

**第一，载体是我自己拥有的音乐。** 不是流媒体，是硬盘上那些 `.mp3`、`.m4a`、`.flac`。所以播放器必须能读本地文件、能完全离线。

**第二，免费。** 不是「免费试用」「免费版够用」那种免费，是**功能完整、不用买断、不用订阅**。这一条后面会淘汰掉绝大部分候选。

**第三，车载是硬需求。** 开车时要能在车机上浏览、切歌、看歌词——不是「能出声就行」，是**要有车机界面**。

**这三个要求本身都不苛刻，但它们叠加起来之后，可选范围小得超出预期。** 而其中第二条和第三条各有一层隐藏的门槛，是真正麻烦的地方。

## 二、车载：它先把平台锁死了

**CarPlay 和 Android Auto 是两套互不兼容的东西，不存在「一个播放器同时支持两者」。**

| | Android Auto | CarPlay |
|---|---|---|
| 归属 | Google | Apple |
| 只能跑在 | Android 手机 | iPhone |
| 能互换吗 | ❌ | ❌ |

**CarPlay 是 Apple 的专有接口，Android 应用不可能接入；Android Auto 同理。** 所以「支持车载」这句话必须先问：**你手上是什么手机，你的车支持哪一套。**

而且**车支持哪个系统是硬件属性，软件补不了**。我见过的情况里：有的车只认 CarPlay（不少合资与进口车型），有的只认 Android Auto，近年新车两个都支持，老车则只有蓝牙。**如果车只认 CarPlay，Android 手机接上去只能走蓝牙**——能用，但没有车机界面，也不能在车机上浏览曲库。

这一条直接决定了我的方案不是「选一个播放器」，而是**「Android 和 iOS 各选一个」**。

## 三、免费：它淘汰掉的比想象中多

这一条踩下去，才发现「免费」在音乐播放器这个领域有很强的稀释。

**iOS 上的典型是 OnePlayer。** 它的功能列表写得很全，但我实际用过之后确认：**免费版连切歌都不行。** 这不是猜测，是一手体验。它的内购列表也印证了这种付费墙的密度——Premium 买断、月付 Pro、年付 Pro，还有按分钟计费的 AI 歌词识别。

**判断方法很简单**：去 App Store 页面看「In-App Purchases」那一栏。条目越多、越涉及**播放控制**这类基础能力，免费版能用的就越少。

另一个坑和「离线」这个词有关，值得单独说。

### 「离线」有两种，含义完全不同

**一类是本地文件播放器**：文件在手机里，播放不依赖网络。

**另一类是服务器客户端**（Subsonic / Navidrome 生态）：文件在你自己家里的 NAS 上，手机只是遥控器加播放器。我买过其中一个代表，**play:Sub**。

它本身做得相当成熟——支持 Navidrome、Airsonic、Ampache，有缓存、有无缝离线模式、有 CarPlay，维护了很多年。但它有一个架构前提，官方说明写得很直白：**必须有一个服务器在跑**。

**它的「离线」是缓存意义上的离线**：你在家 Wi-Fi 下听过的歌被缓存下来，出门才有得听。没缓存过的歌，出门就没有。

这就带来一个很不舒服的现实：**你的「离线播放」范围，取决于出门前在家同步了什么。** 想要完整曲库随时随地可用，只有两条路——出门前手动一张张缓存好，或者**把后端端口暴露到互联网**。第二条很多人真的这么干，但代价是：**为了一个播放器，把一个本来只在内网的服务挂到了公网上。**

**所以「免费的离线播放器」这个说法要先拆开问：你要的是「文件在手机上」，还是「文件在家里、手机能连回去」？** 前者只需要存储空间，后者需要一个 7×24 在线的服务器、一个公网入口，以及相应的安全维护。

我最后选的方案，很大程度上就是为了避开这一整类问题：**文件直接放手机里，不依赖任何后端。**

## 四、筛到最后，只剩两个

把「免费」「完全离线」「逐词显示」「有车载」四条同时套上，剩下的是：

| 播放器 | 平台 | 免费 | 逐词 | 车载 |
|---|---|---|---|---|
| **Gramophone（留声机）** | Android | ✅ GPLv3 | ✅ | ✅ **Android Auto** |
| **Steve** | iOS | ✅ 无内购 | ✅ | ✅ **CarPlay** |
| Booming | Android | ✅ GPLv3 | ⚠️ | ✅ Android Auto |
| Local Player | Android | ✅ MIT | ✅ | ❌ |
| NeoMusic | Android | ⚠️ 有买断 | ✅ | ✅ Android Auto |
| Fluxio | Android | ✅ GPLv3 | ✅ | ✅ Android Auto |
| OnePlayer | iOS | ⚠️ 免费版不能切歌 | ✅ | ✅ CarPlay |
| play:Sub | iOS | 买断 | ❌ | ✅ CarPlay |

**两个选择我都确认过实现，不是看宣传语：**

**Gramophone** 实现了 Android Auto 媒体应用必需的 `MediaLibraryService`，Manifest 里注册了车载元数据（`automotiveApp / uses name=media`）。

**Steve** 的官方描述明确写着：「CARPLAY: Browse your music and control playback from your car's display」，另外还支持 Apple Watch。

**但它们的逐词格式不一样。** Gramophone 认增强型 LRC 和 TTML，而 Steve 的逐词**只认 TTML**——它描述里的原话是 "Word-by-word, beat-by-beat highlighting **from TTML**"。

**这就是「不得不转换两次」的由来。** 而为了搞懂为什么不能只转一次，得先回答一个更基本的问题：**歌词文件到底有几种格式？**

## 五、LRC：1998 年，一个 Winamp 插件

**LRC 的出身很具体**：据维基百科与多份格式文档的记载，它**由台湾的 Kuo（Djohan）Shiang-shiang 在 1998 年引入**，配套一个 **Winamp 插件**，程序名就叫 Lyrics Displayer。

维基百科的原话是：它是**最早尝试模拟卡拉OK效果的程序之一**（"one of the first computer programs, if not the first, that attempted to simulate Karaoke performance"）。

语法简单到可以口头描述：

```
[00:12.00]第一行歌词
[00:17.20]第二行歌词
[00:21.10][00:45.10]重复的副歌
```

方括号里是 `[mm:ss.xx]`，分、秒、百分秒。一行可以有多个时间标签（副歌重复），还支持 `[ti:标题]` `[ar:歌手]` `[al:专辑]` `[offset:+/-毫秒]` 这类 ID 标签。

**这里有个细节值得注意：LRC 从来没有被任何标准组织正式定义过。** AMLL 的格式文档写得很直白：

> **「LRC was not formally defined by a single organization. Its original source is unknown, and it has become an industry convention with many variants and unspecified details.」**

也就是说，**一个 1998 年的 Winamp 插件悄悄变成了二十多年的事实标准，而且至今没有权威规范**。这就是后面所有混乱的根源。

## 六、A2 扩展：给每个词加时间

行级时间戳解决不了「唱到哪个字」。于是 **A2 Media Player 的作者给它加了一个扩展**，维基百科称之为 **A2 extension**，也常叫 **Enhanced LRC**：

```
[00:00.00] <00:00.04> When <00:00.16> the <00:00.82> truth <00:01.29> is <00:01.63> found
```

**规则就一条：把方括号换成尖括号 `<mm:ss.xx>`，插在词前面，表示「这个词从此刻开始唱」。**

这个扩展的巧妙之处在于**向后兼容**：不认识尖括号的老播放器会把 `<00:00.04>` 当普通文字——表现不好但不会崩，认识的新播放器则能做逐词高亮。

但「当普通文字」这个兜底也埋了雷。**如果你的播放器认 LRC 但不认 A2，你会看到时间戳和歌词混在一起。** 我在 Steve 上就撞了这个，后面细说。

## 七、TTML：字幕标准的副产品

**LRC 是民间产物，TTML 是官方产物**，两者的设计目标完全不同。

TTML 的全名是 **Timed Text Markup Language**，**前身叫 DFXP（Distribution Format Exchange Profile）**。维基百科记录了它的时间线：

| 时间 | 事件 |
|---|---|
| 2003 年 | W3C 成立 Timed Text 工作组，开始起草 |
| 2004 年 11 月 | 发布早期草案，名为 **Timed Text (TT) Authoring Format 1.0 – DFXP** |
| 2010 年 11 月 | **TTML1** 成为 W3C 正式推荐标准 |
| 2010 年 | WHATWG 另起炉灶做 WebVTT（因为 TTML 太重） |
| 2012 年 2 月 | 美国 FCC 把 SMPTE 的闭路字幕标准（TTML 超集）列为「安全港」交换格式 |
| 2018 年 11 月 | **TTML2** 定稿 |
| 2015 年 | Netflix、HBO、SMPTE、W3C 因 TTML 获艾美奖 |

**注意最后那条**：它拿的是「非直播宽带字幕标准化」的艾美奖。**TTML 是为电视字幕和流媒体字幕设计的**，卡拉OK 只是它顺带能做的事——W3C 甚至专门有一个 **TTML Karaoke Extension Module** 草案，说明「用 TTML 表达卡拉OK」本身是件需要额外规范的事。

TTML 是 XML，一个最小的逐词歌词长这样：

```xml
<tt xmlns="http://www.w3.org/ns/ttml"
    xmlns:itunes="http://music.apple.com/lyric-ttml-internal"
    itunes:timing="Word">
  <body><div>
    <p begin="00:29.250" end="00:33.410">
      <span begin="00:29.250" end="00:30.762">2002</span>
      <span begin="00:30.762" end="00:31.140">年</span>
    </p>
  </div></body>
</tt>
```

**和 LRC 的根本差别：TTML 里每个元素都显式带 `begin` 和 `end`，而 LRC A2 只给开始时间，结束时间靠「下一个时间戳」隐式推出。**

这个差别看起来小，实际影响很大：TTML 能表达**间隙**（这一段唱完到下一段之间有空白），LRC A2 不能——它假定时间是连续铺满的。

## 八、八种逐词方言，只有一个是真的标准

我把目前能找到的主要方言整理出来，并且把**每个格式的归属**也列上——这一列才是关键：

| 格式 | 扩展名 | 行级 | 词级 | **谁定的** | 公开规范？ |
|---|---|---|---|---|---|
| **LRC** | `.lrc` | ✅ | ❌ | 1998 年台湾一个 Winamp 插件 | **❌ 从未被任何组织定义** |
| **LRC A2** | `.lrc`, `.alrc` | ✅ | ✅ | A2 Media Player 作者 | ❌ 仅维基百科描述 |
| **SPL** | `.spl` | ✅ | ✅ | **椒盐音乐作者个人** | ✅ 有文档，但只此一家 |
| **YRC** | `.yrc` | ✅ | ✅ | **网易云音乐** | **❌ 靠反向工程** |
| **QRC** | `.qrc` | ✅ | ✅ | **QQ 音乐** | **❌ 加密，靠破解** |
| **KRC** | `.krc` | ✅ | ✅ | **酷狗音乐** | **❌ 加密，靠破解** |
| **Lyricify Syllable** | `.lys` | ✅ | ✅ | Lyricify 作者 | ❌ |
| **TTML** | `.ttml` | ✅ | ✅ | **W3C** | ✅ 正式国际标准 |

**八种能表达逐词的格式，只有一个是真正的国际标准。** 剩下的：一个来自 1998 年的私人插件，两个是播放器作者的私人扩展，三家是音乐平台的私有格式，还有两个是个人 App 的格式。

### 逐词歌词为什么会被加密

这是整件事里我最想让人知道的部分。要拿到 QQ 音乐和酷狗的逐词歌词，实际流程是这样的：

**QRC（QQ 音乐）**：

```
歌词 XML 里的 CDATA → 大写 hex 字符串 → TripleDES 解密 → zlib/inflate → UTF-8
```

**KRC（酷狗）**：

```
异或 + zlib
```

**YRC（网易云）** 不加密，但也是一种自定义的 JSON 嵌文本结构：

```
[20630,5210](20630,180,0)あ(20810,160,0)な(20970,150,0)た...
```

`[行开始毫秒, 行时长]` 后面跟一串 `(字开始, 字时长, 0)字`。

**这三家没有一家公开过自己的格式规范。** 开源项目能读它们，全靠逆向——你在那些项目的代码注释里能直接看到「移植自 xxx 的 qrc_decrypt」「对齐 xxx.rs 的解析逻辑」这类说明。

**为什么加密？因为对平台来说，逐词时间轴是内容资产。** 它是平台花钱（或用户众包）打出来的，加密能防批量抓取、防竞品直接复用。这是护城河，不是技术疏忽。

### SPL 的尴尬：一个 App 的格式

SPL（Salt Player Lyrics）是个更近的例子。它的官方规范文档写着：

> **制定时间：2024 年 12 月 16 日**
> **制定作者：不要糖醋放椒盐**

**一个为自家 App 制定的格式，规范只有一行作者署名。**

它的出发点其实是好的——LRC 生态里各种不规范写法太多（毫秒位数不统一、冒号句号混用、行尾时间戳缺失），SPL 想把这些「语法糖」标准化。但它也带来了新的不兼容：有人在其仓库提 issue 指出，SPL 要求行末必须显式写结束时间戳，**这导致标准 A2 格式在 SPL 规范下无法直接兼容**。作者回应说解析时会自动补隐式行结尾，但这是事后补丁，两边仍然不是同一套规则。

### 为什么会分裂成这样

我的判断是三个原因叠加：

**第一，起点没有权威规范，所以谁都可以加一版。** LRC 是 1998 年的插件产物，从未标准化。没有规范的后果不是「大家都不用」，而是「大家都用自己的」。播放器作者发现 LRC 表达不了逐词，就自己加一层尖括号；另一个作者觉得 LRC 的兼容性写法太乱，就另立一套标准。**每一次「我来改好一点」都产生一个新方言。**

**第二，平台把歌词当资产，不当标准。** 网易云做 YRC、QQ 音乐做 QRC、酷狗做 KRC，而且后两个还加密。它们不公开规范，不是没时间写文档，是**不想让别人轻易拿走**。当格式是护城河的一部分时，「统一」就等于「放弃优势」。

**第三，字幕和歌词是两个圈子，互不通气。** TTML 从字幕圈来，工程能力强、能表达复杂排版，但对「一首歌几十行、每行几个词」是过度设计；LRC 圈从播放器插件长起来，简单到极致但缺乏表达能力。**两个圈子各解决各的问题，中间没有桥。**

**结果就是：唯一真正标准化的 TTML 最重、最难手写；最容易手写的 LRC 最没有约束、最容易分裂。** 这个组合几乎注定了解析器要写好几套。

## 九、歌词库的开放性，才是这一切的根

格式分裂是一层，**歌词数据本身从哪来、能不能自由用**是更底下的一层。这一层决定了「免费逐词」为什么必然稀缺。

### LRCLIB：唯一真正开放的那个

我们用歌词的那个库叫 **LRCLIB**（`lrclib.net`）。它的性质值得说清楚：

- **完全免费、不需要 API key、CORS 开放**
- **服务端代码 MIT 开源**（Rust + SQLite）
- **数据库定期公开 dump**，就是 SQLite 文件，谁都能下载
- 作者在 Hacker News 上的原话：**「aimed to provide completely free synchronized lyrics for everyone, especially for FOSS music players, with zero profit intention」**

**但它的曲库以行级歌词为主。** 它的 API 里有个 `hasWordSync` 字段，还有 `lyricsfile`（YAML 格式，含 `lines[].words`）——**说明这个格式本身就支持逐词，只是绝大多数记录是用户上传的行级 LRC，`hasWordSync` 为 false。**

**这解释了我们为什么要自己生成逐词：库里没有这个数据，不是库不支持。**

### Spotify：完全没有开放的歌词接口

- **Spotify 的 Web API 里从来没有歌词接口**，无论在 Tracks 还是 Search 下都找不到
- 客户端里显示的歌词来自 **Musixmatch 授权**
- 开发者想拿，只能爬取登录 cookie 去调内部的歌词路径——**这会失效**，因为 cookie 绑定个人账号、会过期、接口形状会变

而且它显示的歌词是**行级**的：响应里 `syncType` 是 `LINE_SYNCED`，逐词字段存在但是空的。

### Musixmatch：法律上最干净，也最贵

这是 Spotify、Apple Music、Instagram、TikTok 背后共同的歌词供应方。

| 项目 | 内容 |
|---|---|
| 曲库 | 千万级歌曲，五十多种语言 |
| 授权 | 有 Sony、Universal、Warner 及独立出版商的正式授权 |
| 定价 | Basic 档月费约三十美元（每天数百次调用）、Scale 档月费约一百二十美元（每天两千次） |
| **禁止缓存** | Basic/Scale 明确「**No caching or storing lyrics data is permitted**」 |
| 合规审计 | 官方文档写着自己会做定期合规审计 |
| 逐词 | 只有贵的那档才有逐词接口 |

**注意「禁止缓存」这条**：意味着即使付了钱，也不能把歌词存到本地——这直接和离线播放器的需求冲突。

而 Apple App Store 审核条款要求开发者证明拥有显示歌词的合法权利，Musixmatch 卖的正是这份「授权确认函」。

### 三层拼起来，前面的问题全对上了

| 现象 | 原因 |
|---|---|
| 为什么格式有八种 | 开放库不强制格式；封闭平台用私有格式建护城河 |
| 为什么 QRC/KRC 加密 | 无授权抓取，只能防；Musixmatch 有授权，就敢公开做 API 收费 |
| 为什么逐词这么少 | 逐词数据成本高（人工打轴或音频对齐），开放库里没人做；商业库把它放在最贵的档位 |
| 为什么免费播放器只能用行级 | 免费库只有行级；有逐词的库付费且禁止缓存 |

**一句话：逐词歌词的商业本质是「人工打轴成本 + 版权授权」，这两样都不免费。** 开放库之所以能免费，是因为它只做行级（成本低）且放弃版权主张（社区贡献）。

## 十、不得不做的两次转换

回到我的两个选择。Gramophone 要增强型 LRC，Steve 要 TTML，**同一批歌词得转两次。**

**第一次尝试就撞了墙。**

我先做的是 A2 格式自动生成，按固定字数切分中文，先给了 Android 上的 Booming 试。反馈是：**「词间距有改变，而且有些明显不符合中文，例如『是你 的甜 言蜜 语改 变季节』这种分词完全错误。」**

问题不在播放器，在我的切分方法。**按固定字数切中文，切口必然落在词中间。** 换成 Charabia（Rust 生态的 CJK 分词库）之后才对：

```
是你的甜言蜜语改变季节 → ["是", "你", "的", "甜言", "蜜语", "改变", "季节"]
```

**第二次撞的是播放器自己。** 换了对的分词后还是不显示。我去读了 Booming 的源码，看到这段：

```kotlin
if (index < matches.lastIndex && !wordText.endsWith(" ")) {
    wordText += " "        // 无条件加空格，不判断语言
}
```

**它给每个非末词都补一个空格，不管是不是中文。** 所以中文必然渲染成 `雨 一直 下`。这不是文件格式能解决的问题，得改应用本身。这条路直接放弃。

**第三次撞的是 Steve。** 我把 A2 格式的歌词传过去，结果**时间戳和歌词混在一起显示**。原因：**Steve 的 LRC 支持只到行级，解析器不认识 `<mm:ss.xx>`，直接当正文显示**。它的逐词能力**只从 TTML 来**。

同一个错误我还犯了第二次：**打好「原始歌词备份」之后才发现，那个备份是转换后的版本**，真正的原始文件在另一个目录里。只好重新找、重新备份。

### 现在的做法

「一份原始行级 LRC，生成两种派生格式」：

```
原始行级 LRC（唯一真实来源）
   ├── 增强 LRC（A2）──→ Android / Gramophone
   └── TTML          ──→ iOS / Steve
```

几个技术点值得记下：

**分词用 Charabia，不用字数切分。** 中文没有空格，分词决定切口，这一步错了后面全错。

**时间按字符数比例分配，不是平均分。** 四个字的词应该比一个虚词占更多时间。

**必须诚实说：这仍然是估算。** 没有做音频分析，所以长音和快词会漂。真正准确的做法是「强制对齐」——用 Whisper 这类模型先识别语音，再把已知歌词对齐到时间轴上，精度能到毫秒级。但那需要 GPU 和模型，跑完整个曲库的成本远高于字符均分。**字符均分是「够用但会漂」，强制对齐是「准确但昂贵」。**

**TTML 里拉丁词之间的空格要写在 span 标签外面。** AMLL 的规范文档把这个列为「最合规」写法。

**验证方式必须是「文本重建」**：把生成的逐词标记剥掉，拼接所有词的文本，**必须和原歌词逐字符相同**。中文只靠肉眼看「差不多」是不够的。

## 十一、几点判断

**第一，这不是一个「格式选得好不好」的问题，是生态分裂的必然结果。** LRC 出身民间、从未标准化，A2 是播放器作者的私人扩展，TTML 来自完全不同的字幕工业，还有三家平台把自己加密的格式当资产。三者解决的问题不同，没有理由收敛。

**第二，「免费 + 离线 + 逐词 + 车载」这个组合稀缺，是有硬原因的。** 逐词需要词级时间数据，公开歌词库绝大部分只有行级；有逐词的商业库付费且禁止缓存；车载又要求原生实现。这不是开发者不愿意做，是这几个约束在商业上互斥。

**第三，行级歌词对「跟着唱」其实够用。** 逐词是锦上添花，代价是要维护两套文件、或者接受估算的错位。**如果你只想跟着唱，不追求字幕级别的精确，行级反而是更省事的选择。**

**第四，跨平台用同一个曲库，歌词格式这块目前没有统一解。** 除非你愿意为了格式统一而放弃其中一个平台——那可能反而是更省事的选择。

---

*数据与来源均在上文标注。本文的实测部分来自笔者本机：整库歌词先转增强 LRC 供 Android 播放器，再转 TTML 供 iOS 播放器，两种格式均通过「文本重建」校验（剥掉逐词标记后与原歌词逐字符比对，零差异）。*
