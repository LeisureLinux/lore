---
title: "Python 失去 Tim Peters：他留下的不只是 19 行禅语和一个排序算法"
date: 2026-11-12
slug: tim-peters-1952-2026-python-in-memoriam
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Guido van Rossum 在 discuss.python.org 发起的《In Memoriam: Tim Peters 1952–2026》（Core Development 版块，2026-11-11 05:36 UTC，主帖与全部 30+ 条回复的 .md 分页原文）＋ 帖中链接的讣告页（bratleyfamilyfuneralhomes.com）、维基百科条目、PEP 20 与 listsort.txt ＋ Hugo van Kemenade 引用的 Tim 最后一帖、Chris McDonough 的长篇回忆、Chris Angelico / Antoine Pitrou / Mark Dickinson / Steve Holden / Thomas Wouters / Greg Stein 等人的回复 ＋ Python 官方 PEP 20 页面、Timsort 与 Powersort 相关 CPython 提交、PSF 2017 杰出服务奖页面、Zoom 无涉"
original_date: 2026-11-11
original_url: "https://discuss.python.org/t/in-memoriam-tim-peters-1952-2026/110028"
description: "本文据 Python 官方讨论区的纪念帖与其全部回复写成。Guido van Rossum 于 2026-11-11 05:36 UTC 在 Core Development 版块宣布 Tim Peters 已于同年 7 月 15 日去世，标题标注生卒 1952–2026。文章把散落在回复里的技术史整理成一条线：他说服 Guido 让 Python 支持 int 与 float 混合运算（Guido 称这是他的「第一件事」）、在邮件列表上以「Timbot」之名用无数耐心回答奠定了早期核心开发的讨论风气、2002 年给出 Timsort（后被 Java/Android/V8/Node.js 采用，Python 3.11 起合并策略换成 Powersort）、写下 PEP 20《Python 之禅》（20 条格言只写下了 19 条，import this 可见）、贡献 doctest 与 timeit、2001–2014 任 PSF 董事、2017 年获 PSF 杰出服务奖。重点不在讣告本身，而在几十位回复者反复提到的同一件事：他从不武断否定任何人，会认真回复明显的挑衅帖、详细解释「为什么行或不行」，用 <wink> 与幽默代替权威；Chris McDonough 说 1995–2010 年间启动的 Python 项目都带着一点「Tim 文化」。也如实记录帖子里的复杂声音：有人提到他晚年讨论风格变得较为对抗、以及曾被指导委员会禁言，Steve Holden 写道他深受影响但仍持续助人。文中区分了公告确认的事实（Guido 主帖、讣告链接、日期）与社区回忆（个人轶事、评价），并标注「7 月去世、11 月才公开」这一时间差。"
published: true
---

> 一手：Python 官方讨论区核心开发版块的纪念帖，含主帖与全部回复
> 官方材料：第二十号提案、排序设计原文、代码提交记录、基金会奖项页
>
> 这是一篇纪念，不是产品解读。文中把公告确认的事实与社区回忆分开写。

2026 年 11 月 11 日 05:36 UTC，Guido van Rossum 在 Python 官方讨论区的 Core Development 版块发了一帖，标题是《In Memoriam: Tim Peters 1952–2026》。第一句就很克制：

> 我极其沉痛地宣布，Tim Peters 已于今年 7 月 15 日去世。

7 月 15 日去世，11 月 11 日才由 Guido 公开 —— 这个近四个月的时间差，是读这帖时第一个该注意的事实。帖子发出后十几小时内涌入三十多条回复，来自 CPython core developer、PSF 老成员、以及只跟他通邮件从未见过面的人。132 个赞，几乎每条长回复都在讲同一件事，而那件事跟 Timsort 无关。

## 一、官方确认了什么

按最严格的口径，能当作事实的只有这几条：

- 主帖作者是 Guido van Rossum（CPython core developer 标识），发布于 2026-11-11 05:36 UTC，版块 Core Development；
- Tim Peters 于 2026 年 7 月 15 日去世，标题标注 1952–2026；Guido 在正文里链接了殡仪馆的讣告页；
- Guido 把他的定位写成「导师与语言共同设计者」，并说他对 Python 的影响怎么高估都不过分；
- 主帖末尾那句签名是 Guido 式的幽默：一句把 Tim 的名字嵌进他自己惯用落款里的双关：没有 Tim，Python 就不会是今天这样。

其余所有细节——生平、性格、具体贡献的年份与影响——分散在回复与外链资料里，属于社区回忆与公开史料，本文分别标注。

## 二、技术史：他改过 Python 的哪些地方

把主帖、维基条目、PEP 与 CPython 记录拼起来，是一条从语言诞生初期一直延续到近年的线。

第一件事是说服 Guido 支持混合算术。 Guido 写：Tim 在 Python 最初发布后不久找到这门语言，他的「first deed」就是让 Guido 相信 `int` 与 `float` 之间应该能直接运算，因为大多数用户本来就这么预期。维基条目引用了 Guido 更早的表述，把 Tim 和 Steve Majewski 列为「聚焦于非常细微的设计细节、极大帮助澄清各种特性该如何工作」的早期采用者，并举了同一个 mixed arithmetic 例子。

「Timbot」与早期核心开发的语气。 他很快成为邮件列表上的现象级存在：无数细致耐心的用户回答，配上 `<wink>` / `<0.5 wink>` 标记的冷幽默，还常自称在「channeling Guido」。Guido 给的评价比任何技术贡献都重：「Tim really set the tone for early core development」—— 他为早期核心开发定下了基调，从不武断否定任何人，而是详细解释一件事为什么可行或不可行。

这句话在回复里被反复引用。Hugo van Kemenade 贴出 Tim 在讨论区的最后一帖，结尾仍是那句绕了一圈只为说明「现实世界比我们干净的抽象所希望的更复杂」，并照例带上一个眨眼表情 —— 从开始到最后，都是同一个语气。Thomas Wouters 补了一个更具体的场景：有人发了个明显是挑衅的「Python 该学某语言」帖，Tim 回了一篇比原帖长得多、认真到技术细节的答复；Thomas 问他不觉得在浪费时间吗，Tim 说知道自己大概被 troll 了，但「不确定，所以不会直接否定」，而且那篇回复更是写给围观者看的——用善意淹没挑衅。

2002 年，Timsort。 Guido 的措辞是「Tim 给了我们 Timsort」：为 Python list 设计的混合排序算法，后被 Java 与 Android 采用。更完整的公开记录还包括 V8 / Chromium / Node.js、Octave；CPython 自 2.3 起使用它，3.11 起合并策略换成了 Powersort（保留 Timsort 的 run 检测与 galloping 思路）。原始设计文档 `Objects/listsort.txt` 至今是算法工程写作的范本。此外他还贡献了标准库的 `doctest` 与 `timeit` 模块，以及《Python Cookbook》的算法章节。

PEP 20 与那第 20 条。 他最广为人知的是《The Zen of Python》。PEP 20 页面写明作者 Tim Peters、创建于 2004-08-19，摘要里那句玩笑很关键：二十条格言只写下了十九条，剩下一条至今是留白。`import this` 就能看到。Antoine Pitrou 在回复里说，尽管如今引用少了，它作为「优雅与清晰的框架」影响了太多人的日常实践。

社区职务与荣誉。 Chris McDonough 的长篇回忆提到他 2001–2014 年任 PSF 董事（维基条目同样记载），2017 年获 PSF 杰出服务奖；还写到他早年在 Cray Research 写超级计算机编译器、在 Dragon Systems 做语音转文本，以及后来在 Harley-Davidson 工作过——所以那位「长灰发、大胡子、穿着像机修工」的人，并不是社区想象出来的形象。

## 三、几十条回复真正在纪念什么

如果只看技术清单，会漏掉这个帖子的重心。绝大多数回复纪念的是一种待人方式。

Chris Angelico 说，他有幸与 Tim 讨论过很多话题，「他在技术讨论里的意见我一直极为看重；他从不把你当傻子，从不一口否定你的顾虑，总是回答并解释。」两人通了很多年邮件，因地理原因从未见面。

Mark Dickinson 写自己 2008 年加入 core dev 时 Tim 本人并不在场，却通过大量贡献「无处不在」—— 邮件列表文章与代码影响了他整个 CPython 生涯；后来 Tim 回归核心开发才得以直接交流，他说 Tim 的温厚学识、幽默与耐心没有尽头。

Chris McDonough 那段被整篇贴出的旧文最系统：他说 Tim 在早期 Python 里扮演「守门人与打磨者」，把 Java / 微软系语言那种冗长复杂的借口挡在门外；说自己的开源项目在设计讨论里刻意「channel Tim」，用低姿态幽默化解冲突、先把题目学透再回话；最后给出那句被很多人转引的判断——1995 到 2010 年间启动的任何 Python 项目，都带着一点 Tim 文化，因为模仿他的不止他一个。

还有更生活化的：Steve Holden 回忆两人 1983 年就在曼彻斯特见过（Tim 当时代表 Cray Research），后来在弗吉尼亚靠中式午餐和筹办 Python 会议成了朋友，PythonLabs 散了之后午餐固定到 PF Chang's，Tim 每次都以那座「巧克力山」甜点收尾；Greg Stein 也记得那份九层巧克力蛋糕。有人记得他站在楼外拿纸笔发呆想算法，有人记得他一句「你有没有在源码里搜过 six？」把同事的调试思路逗笑。

## 四、帖子里的复杂声音，也该如实记下

这不是一篇只有赞美的悼词，回避那部分反而不尊重。

Antoine Pitrou 写道，他 2007 年前后开始贡献时 Tim 已不太活跃，近年反而在一些讨论里（包括这个讨论区）显得「略显对抗」；他紧接着补了一句自己的判断：相信 Tim 出自好意、仍深切关心这个社区，只是对「可以用不同手段达成同样目标」这件事理解起来有困难——并自嘲这可能是他自视过高。

Steve Holden 提到 Tim 曾因观念原因被 Python 指导委员会禁言，「deeply affected」但没有因此停止帮助别人，这份善意一直持续到最后。

这些是个人观察与感受，不是官方结论，也不是本文能裁定的事。把它们放进来，只是因为一个真实的人比一份功劳清单更值得被记住：他既写下了「美优于丑」，也在晚年经历过社区内部的摩擦。

## 五、事实边界

- 公开确认的事实以 Guido 主帖为准：发布日期 2026-11-11 05:36 UTC、去世日期 2026-07-15、生卒标注 1952–2026、讣告链接。本文未独立联系家属或核实讣告页内容。
- 技术贡献（Timsort 采用范围、Powersort 切换、doctest / timeit、PSF 董事任期与奖项）取自维基条目、PEP 20、CPython 提交与 PSF 页面，非纪念帖原文；Guido 主帖只提到 PEP 20、混合算术与 Timsort（Java/Android）。
- 所有轶事、性格评价、晚年风格与禁言相关说法，均出自讨论区个人回复，属社区回忆，本文按作者逐条标注，未作事实裁定。
- 帖子仍在增加回复（本文核对时已超过 30 条），后续内容可能补充或修正细节。
- 本文不评价 Python 社区治理争议，也不对逝者作整体定论。

## 六、结语

Guido 在主帖下自己跟了一条：「欢迎补上你们自己的 Tim 轶事，我写不全他做过的事。」于是这个帖子变成了一件很 Python 的事：一群人排队讲同一个人的小故事，讲他怎么回帖、怎么不把人当傻子、怎么在明显被挑衅时仍认真写长回复。

`import this` 会打印 19 行。第 20 行从来没写出来 —— 但看完这三十多条回复，大概能猜到它不在 PEP 里，而在那些被他耐心对待过的人后来怎么对待别人。

## Sources

- Guido van Rossum《In Memoriam: Tim Peters 1952–2026》（discuss.python.org，2026-11-11）：<https://discuss.python.org/t/in-memoriam-tim-peters-1952-2026/110028>
- 该帖纯文本分页：<https://discuss.python.org/t/in-memoriam-tim-peters-1952-2026/110028.md?page=1> ｜ <https://discuss.python.org/t/in-memoriam-tim-peters-1952-2026/110028.md?page=2>
- PEP 20 – The Zen of Python：<https://peps.python.org/pep-0020/>
- Timsort 原始设计文档 `listsort.txt`：<https://svn.python.org/projects/python/trunk/Objects/listsort.txt>
- 维基百科 Tim Peters 条目：<https://en.wikipedia.org/wiki/Tim_Peters_(software_engineer)>
- PSF Distinguished Service Awards：<https://www.python.org/community/awards/psf-distinguished-awards/>
