---
title: "为了在手机上看歌词逐字跳，我把 349 首歌转了三遍：LRC、A2、TTML 的来历与分裂"
date: 2026-10-18
slug: lrc-ttml-karaoke-formats
tags: [LRC, LRC A2, Enhanced LRC, TTML, TTML2, DFXP, W3C, 歌词格式, 卡拉OK, 逐词歌词, Gramophone, 留声机, Steve, OnePlayer, play:Sub, Subsonic, Navidrome, Android Auto, CarPlay, 车载, 离线播放器, Android, iOS, Charabia, 分词]
category: 开源/工具
author: FreeLAMP.com
original_source: "Wikipedia：LRC (file format)、Timed Text Markup Language；W3C TTML1/TTML2 规范；AMLL Docs「Lyric Formats」；Gramophone 与 Steve 官方说明"
original_author: "维基百科编者；W3C Timed Text Working Group；AMLL 项目；FoedusProgramme（Gramophone）；Hamza RABI（Steve）"
original_date: 2026-10-18
original_url: "https://en.wikipedia.org/wiki/LRC_(file_format)"
description: "歌词文件有三种互不兼容的逐词写法：1998 年从台湾起步的 LRC 只有行级时间戳，A2 Media Player 给它加了尖括号词级标记，W3C 的 TTML 则是从字幕标准长出来的 XML。车载是硬需求，而 CarPlay 与 Android Auto 是两套互不兼容的系统，这直接锁死了平台选择。我为 349 首歌的歌词先转成 A2 给 Android 的 Gramophone，又转成 TTML 给 iOS 的 Steve，中间因为分错播放器、搞错空格规则白做两轮；iOS 上还实测了 OnePlayer 免费版不能切歌，以及 play:Sub 的「离线」只是缓存、想完整曲库得把后端暴露到公网。这篇讲清三种格式的来历与七种方言的成因，也说明为什么同时满足免费、离线、逐词、车载的播放器只剩两个。"
published: true
---

> 一手材料：[Wikipedia：LRC (file format)](https://en.wikipedia.org/wiki/LRC_(file_format))、[Wikipedia：Timed Text Markup Language](https://en.wikipedia.org/wiki/Timed_Text_Markup_Language)、[W3C：TTML1 第三版（2018-11-08）](https://www.w3.org/TR/2018/REC-ttml1-20181108/)、[W3C：TTML2（2018-11-08）](https://www.w3.org/TR/ttml2/)、[AMLL Docs：Lyric Formats](https://amll.dev/en/guides/lyric/formats.html)
> 播放器来源：[Gramophone（F-Droid / GitHub，GPLv3）](https://f-droid.org/packages/org.akanework.gramophone/)、[Steve: Offline Music Player（App Store）](https://apps.apple.com/us/app/steve-offline-music-player/id6751122850)
> 实测环境（**2026-10-18**）：Honor 50 / Android 14 + Gramophone 1.1.2；iPhone + Steve（App 名显示为「无广告音乐播放器」）。曲库 349 首，中文 246、英文 103。

## 一句话结论

**「歌词文件」不是一个格式，而是三类互不兼容的方言。** **1998 年台湾的 LRC 只记到「整行」；A2 Media Player 用尖括号给每个词加了时间；W3C 的 TTML 是从字幕标准长出来的 XML。** **这三者没有一个是另一个的超集，播放器各认一部分，所以你为 A 播放器转好的歌词，B 播放器打开可能只显示一半。**

我为 349 首歌做这件事，**总共转了三遍**，前两遍是白做的。下面把格式来历和自己踩的坑都写清楚。

## 一、LRC：1998 年，一个 Winamp 插件

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

也就是说，**一个 1998 年的 Winamp 插件悄悄变成了 28 年的事实标准，而且至今没有权威规范**。这就是后面所有混乱的根源。

## 二、A2 扩展：给每个词加时间

行级时间戳解决不了「唱到哪个字」。于是 **A2 Media Player 的作者给它加了一个扩展**，维基百科称之为 **A2 extension**，也常叫 **Enhanced LRC**：

```
[00:00.00] <00:00.04> When <00:00.16> the <00:00.82> truth <00:01.29> is <00:01.63> found
```

**规则就一条：把方括号换成尖括号 `<mm:ss.xx>`，插在词前面，表示「这个词从此刻开始唱」。**

这个扩展的巧妙之处在于**向后兼容**：不认识尖括号的老播放器会把 `<00:00.04>` 当普通文字——表现不好但不会崩，认识的新播放器则能做逐词高亮。

但「普通文字」这个兜底也埋了雷。**如果你的播放器认 LRC 但不认 A2，你会看到时间戳和歌词混在一起。** 我在 Steve 上第一次就撞了这个，后面细说。

## 三、TTML：字幕标准的副产品

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

## 四、所以为什么会有这么多种格式

我整理了一下目前能找到的主要方言（数据来自 AMLL 的格式对照表）：

| 格式 | 扩展名 | 行级 | 词级 | 原生支持翻译/对唱 |
|---|---|---|---|---|
| **LRC** | `.lrc` | ✅ | ❌ | ❌ |
| **LRC A2**（Enhanced LRC） | `.lrc`, `.alrc` | ✅ | ✅ | ❌ |
| **SPL**（Salt Player Lyrics） | `.spl` | ✅ | ✅ | ❌ |
| **YRC**（网易云） | `.yrc` | ✅ | ✅ | ❌ |
| **QRC**（QQ音乐） | `.qrc` | ✅ | ✅ | ❌ |
| **Lyricify Syllable** | `.lys` | ✅ | ✅ | ✅ |
| **TTML** | `.ttml` | ✅ | ✅ | ✅ |

**七个能表达逐词的格式。** 为什么会这样？我的判断是三个原因叠加：

**第一，起点没有权威规范。** LRC 是 1998 年的插件产物，从未标准化。没有权威规范，就意味着「每个人都按自己理解实现」，然后各自打补丁。

**第二，商业闭环驱动方言。** 网易云做 YRC，QQ音乐做 QRC，各家的歌词编辑器、播放器、桌面歌词窗口都是围绕自家方言长出来的。**格式是护城河的一部分**，没有动力统一。

**第三，字幕和歌词是两个圈子。** TTML 从字幕圈来，工程能力强、能表达复杂排版，但对「一首歌几十行、每行几个词」这种场景是过度设计。LRC 圈则是从播放器插件长起来的，简单到极致，但缺乏表达能力。**两个圈子各解决各的问题，中间没有桥。**

## 五、免费离线 + 逐词显示：可选的真不多

这是我这次最意外的发现。**同时满足「免费」「完全离线」「逐词高亮」的播放器，数量少得不成比例。**

我查过的（2026-10 现状）：

| 播放器 | 平台 | 免费 | 离线 | 逐词 | 车载 | 逐词格式 |
|---|---|---|---|---|---|---|
| **Gramophone（留声机）** | Android | ✅ GPLv3 | ✅ | ✅ | ✅ **Android Auto** | LRC / TTML / SRT |
| **Steve** | iOS | ✅ 无内购 | ✅ | ✅ | ✅ **CarPlay** | **仅 TTML** |
| Booming | Android | ✅ GPLv3 | ✅ | ⚠️ | ✅ Android Auto | 自有语法，**中文被插空格** |
| Local Player | Android | ✅ MIT | ✅ | ✅ | ❌ | TTML |
| NeoMusic | Android | ⚠️ | ✅ | ✅ | ✅ Android Auto | LRC，$4.99 一次性解锁 |
| Fluxio | Android | ✅ GPLv3 | ✅ | ✅ | ✅ Android Auto | LRC A2，仅 GitHub 个人 fork |
| OnePlayer | iOS | ⚠️ | ✅ | ✅ | ✅ CarPlay | LRC，**免费版不能切歌**（实测） |
| play:Sub | iOS | 买断 | ⚠️ 缓存式 | ❌ | ✅ CarPlay | 无（纯播放） |
| Doppi / lytti / Trove | iOS | ⚠️ | ✅ | ⚠️ | ✅ CarPlay | 多为行级 |

**把「零付费 + 完全离线 + 逐词可用 + 有车载」四条同时满足的筛出来，只剩两个：Android 的 Gramophone，iOS 的 Steve。**

> 表里 play:Sub 的「离线」标成**缓存式**：它的文件在服务器上，出门能不能听取决于你在家里同步过什么。这不是一回事，下面单独说。

而它们的**逐词格式还不一样**——Gramophone 认 LRC A2 和 TTML，Steve 的逐词**只认 TTML**（它官方描述里的原话是 "Word-by-word, beat-by-beat highlighting **from TTML**"）。

### 车载是硬需求，而它锁死了平台

对我来说**车载不是加分项，是必要条件**——开车时必须能在车机上浏览、切歌、看歌词。这一点直接决定了选型，因为**车载系统是两套互不兼容的东西**：

| | Android Auto | CarPlay |
|---|---|---|
| 归属 | Google | Apple |
| 只能跑在 | Android 手机 | iPhone |
| 能互换吗 | ❌ | ❌ |

**CarPlay 是 Apple 的专有接口，Android 应用不可能接入；Android Auto 同理。** 所以「一个播放器同时支持 CarPlay 和 Android Auto」这种说法本身就不成立——它取决于你手上是什么手机。

我分别确认了两个选择的车载能力（不是看宣传语，是看实现）：

**Gramophone（Android）——支持 Android Auto。** 源码里能看到它实现了 Android Auto 媒体应用必需的 `MediaLibraryService`，并在 Manifest 注册了车载元数据：

```xml
<!-- app/src/main/res/xml/automotive_app_desc.xml -->
<automotiveApp>
    <uses name="media" />
</automotiveApp>
```

```kotlin
// GramophonePlaybackService.kt
class GramophonePlaybackService : MediaLibraryService(), MediaSessionService.Listener
```

**Steve（iOS）——支持 CarPlay。** 它的官方描述里明确列了：「CARPLAY: Browse your music and control playback from your car's display」，另外还支持 Apple Watch。

**一个必须提前确认的前提**：**你的车支持哪个系统，是硬件属性，不是软件能补的。** 我见过的情况里：有的车只支持 CarPlay（不少合资/进口车型），有的只支持 Android Auto，近年新车两个都支持，老车则只有蓝牙。**如果车只认 CarPlay，那 Android 手机接上去只能走蓝牙**——能用，但没有车机界面，也不能在车机上浏览曲库。

这也是为什么我在 Android 和 iOS 上各选一个，而不是只选一个换平台。

### 还有一个分类维度：本地文件播放器 vs 服务器客户端

我在这上面也交过学费，值得单拎出来说，因为**这两类应用的「离线」含义完全不同**。

**一类是本地文件播放器**：文件存在手机里，播放不依赖任何网络。Gramophone、Steve 都是这一类。

**另一类是服务器客户端（Subsonic / Navidrome 生态）**：文件在你自己家里的 NAS 或服务器上，手机只是个遥控器 + 播放器。代表是 **play:Sub**（iOS，我买过）。

play:Sub 本身是个做得相当成熟的应用——支持 Subsonic / Navidrome / Airsonic / Ampache，有缓存、无缝离线模式、CarPlay、10 段均衡器，而且维护了很多年（2026 年 9 月还在更新，把「下载」和「缓存」拆成了两个独立概念）。但它有一个**架构上的前提**：

> **「A licensed installation of Subsonic 4.8+ is required.」**

也就是说，**它必须有一个服务器在跑**。它的「离线」是**缓存**意义上的离线——你在家里 Wi-Fi 下听过的歌会被缓存下来，出门才有得听；没缓存过的歌，出门就是听不了。

这就带来一个很不舒服的现实：**你的「离线播放」范围，取决于你出门前在家里同步了什么。** 想要完整曲库随时随地可用，只有两条路：

1. 出门前手动把专辑一张张缓存好（play:Sub 支持「手动缓存整个文件夹/歌手/专辑」，但这是体力活）
2. **把你后端的端口暴露到互联网**，让手机在外面也能连回家里

第 2 条是很多人实际做的选择，但它的代价是：**你为了让一个播放器工作，把一个本来只在内网的服务挂到了公网上。** 这是安全暴露面，不是播放器功能问题。

**所以「免费离线播放器」这个说法要先拆开问：**你要的是**文件在手机上**，还是**文件在家里、手机能连回去**？前者只需要存储空间，后者需要一个 7×24 在线的服务器、一个公网入口、以及相应的安全维护。

我最后选 Gramophone 和 Steve，很大程度上就是为了避开这一整类问题——**文件直接放手机里，349 首 2.1 GB，不依赖任何后端。**

### 另一个坑：免费版的功能阉割

顺便提醒：iOS 上看起来「免费」的离线播放器，很多靠内购解锁核心能力。

**OnePlayer** 是个典型例子。我实际用过，**免费版连切歌都不行**——这不是猜测，是一手体验。它的 App Store 内购列表也印证了这种重度付费墙：Premium 版本 $14.99、月付 Pro $1.99、年付 Pro $4.99，还有按分钟计费的 AI 歌词识别（60 分钟 $1.99 起）。

这类应用的功能列表往往写得很全，**但免费版能用到哪一步，只有装上试过才知道**。判断方法很简单：去 App Store 页面看「In-App Purchases」那一栏，条目越多、越涉及「播放控制」这类基础能力，免费版能用的就越少。

## 六、我最终的选择和踩的坑

选型：**Android 用 Gramophone（中文名「留声机」），iOS 用 Steve（App 图标显示为「无广告音乐播放器」）。** 两个都免费、都能完全离线、都支持逐词。

代价是：**同一批歌词要维护两种格式。**

我先后踩了三个坑，都是「想当然」造成的。

### 坑一：把 A2 给了只认行级的播放器

我最初做了个自动加词级时间戳的脚本，按 2 字一组切分中文，生成 A2 格式，先给了 Android 上的 Booming 试。

结果用户反馈：**「词间距有改变，而且有些明显不符合中文，例如『是你 的甜 言蜜 语改 变季节』这种分词完全错误。」**

问题不在播放器，在我的切分方法。**按固定字数切中文，切口必然出现在词中间。** 中文的词边界需要分词，不是数数。

换成 **Charabia**（Rust 生态里做 CJK 分词的库，也是 lrcget 项目自己在用的）之后：

```
是你的甜言蜜语改变季节 → ["是", "你", "的", "甜言", "蜜语", "改变", "季节"]
```

这才对。

### 坑二：Booming 会给每个词强制加空格

换了对的分词后，Booming 还是不对。我去读了它的源码（`LrcLyricsParser.kt`）：

```kotlin
if (index < matches.lastIndex && !wordText.endsWith(" ")) {
    wordText += " "        // 无条件加空格，不判断语言
}
```

**它给每个非末词都补一个空格，不管是不是中文。** 所以中文必然渲染成 `雨 一直 下`。这不是文件格式能解决的问题，得改应用本身。**这条路直接放弃。**

### 坑三：Steve 的 LRC 解析器不剥离尖括号

转投 iOS 后，我把 A2 格式的 LRC 传给了 Steve。结果用户说：**「歌词里的那些时间都被显示了和真正的歌词混合在一起。」**

原因：**Steve 的 LRC 支持只到行级，而且它的解析器不认识 `<mm:ss.xx>`，直接当正文显示。** 它的逐词能力**只从 TTML 来**。

而我又犯了第二个错：**打好「原始 LRC 备份」之后才发现，那个备份是转换后的版本**，真正的原始文件在另一个目录里。只好重新找、重新备份。

## 七、现在的做法

最终流程是「一份原始 LRC，生成两种派生格式」：

```
原始行级 LRC（唯一真实来源，备份 226 KB）
   ├── LRC A2  ──→ Android / Gramophone
   └── TTML    ──→ iOS / Steve
```

几个技术点值得记下：

**分词用 Charabia，不用字数切分。** 中文没有空格，分词决定切口，这一步错了后面全错。

**时间按字符数比例分配，不是平均分。** 四个字的词应该比一个虚词占更多时间。但这仍然是估算——**没有做音频分析，所以长音和快词会漂**。这是方法的固有限制，不是 bug。

**TTML 里拉丁词之间的空格要写在 `<span>` 外面。** AMLL 的规范文档把这个列为「最合规」写法。写成标签内会让渲染结果出现多余空格。

**验证方式必须是「文本重建」**：把生成的逐词标记剥掉，拼接所有词的文本，**必须和原始歌词逐字符相同**。我拿 349 个文件全量跑过这个检查，中英文都零差异。中文只靠肉眼看「差不多」是不够的。

**改之前先备份，而且要验证备份内容。** 我第一次备份就把已转换的文件打进去了，等于没有原始版本。

## 八、几点判断

**第一，这不是一个「格式选得好不好」的问题，是生态分裂的必然结果。** LRC 出身民间、从未标准化，A2 是播放器作者的私人扩展，TTML 来自完全不同的字幕工业。三者解决的问题不同，没有理由收敛。

**第二，免费 + 离线 + 逐词这个组合稀缺，是有原因的。** 逐词歌词需要**词级时间数据**，而公开歌词库（包括 LRCLIB）绝大部分只有行级。播放器要支持逐词，就得自己做分词 + 时间估算，或者要求用户手工打轴——两者都不讨喜。商业播放器可以把歌词做成卖点收费，免费项目没这个动力。

**第三，如果只想要「能跟着唱」，行级就够了。** 逐词是锦上添花，代价是你要维护两套文件、或者接受自动估算的错位。我现在这套流程能自动化，但如果换播放器，格式这块还得重来一遍。

**第四，跨平台用同一个曲库，歌词格式这块目前没有统一解。** 除非你愿意为了格式统一而放弃其中一个平台——那可能反而是更省事的选择。

---

*数据与来源均在上文标注。曲库实测数据来自笔者本机：349 个 LRC，中文 246 首、英文 103 首，Charabia 分词 + 按字符数比例分配时间，TTML 与 A2 双格式全量生成并通过文本重建校验。*
