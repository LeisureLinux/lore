---
title: "一条磁带如何长成一个操作系统：F/OSS Comics 的 Unix 与 BSD 五部曲（系列导读）"
date: 2026-11-03
slug: foss-comics-unix-bsd-series-guide
tags: [FOSSComics, Unix, BSD, 历史, 漫画, 系列导读, KenThompson, DennisRitchie, BillJoy, ChuckHaley, vi, ed, em, ex, Berkeley, BellLabs, UCBerkeley, 磁带, AT&T, 反垄断, 自由软件, 技术史, 开源运动, Linux, MINIX, Plan9, Inferno]
category: 技术/历史
author: FreeLAMP.com
original_source: "⭐ 一手核对：F/OSS Comics 系列全部五篇（Joone Hur 绘，2026-08-22 ~ 2026-10-30）原文与配图，含 69 张漫画原图"
original_date: 2026-11-03
original_url: "https://fosscomics.com/"
description: "F/OSS Comics 是一个用漫画讲自由开源软件史的系列，2026 年 8 月到 10 月连更五篇，从 Unix 哲学讲到 BSD 的诞生。本文是整个系列的导读：先给出五篇的时间线与阅读顺序，再逐篇提炼内容要点（第 9 篇 Unix 哲学与 MINIX→Linux 的血缘、第 10 篇 Dennis Ritchie 生平与 C 语言、第 11 篇 Unix 源码 tapes 到伯克利、第 12 篇 ed→em→ex→vi 的编辑器家谱、第 13 篇 BSD 诞生、VAX 虚存与 2BSD→3BSD），最后给出笔者的整体观察：这个系列最值得学的不是某个史实，而是它把「**代码怎么流动**」这条主线讲清楚了 —— 从磁带到共享软件，而这正是自由软件运动在技术上真正继承的东西。"
published: true
---

> **原文**：F/OSS Comics，**Joone Hur** 绘，2026-08-22 ~ 2026-10-30 连载五篇
> 系列首页：<https://fosscomics.com/>
> **本文是系列导读**，五篇原文将逐篇做完整中文翻译。
> ⭐ **本文的一个额外目的**：把「**代码怎么流动**」这条主线单独拎出来 —— 因为它贯穿五篇，却不在任何一篇的标题里。

## 一句话结论

**⭐ 而这个系列最值得学的，不是任何单个史实，而是它反复讲的同一件事：**

```
Unix 源码装在磁带上 → 磁带寄给伯克利 → 伯克利把源码连同改进一起再寄出去
     → 更多人拿到源码 → 更多人改进 → 更多人拿到
```

**⭐ 也就是说：⭐ 「自由软件」这个运动，在技术上的真正继承物不是「许可证」，而是「**让代码能流动起来的那些具体做法**」。**

## 一、系列全景

**⭐ 五篇的时间线与主题：**

| # | 标题 | 发布 | 讲什么 |
|---|---|---|---|
| **9** | **The Unix Philosophy**（Unix 哲学）** | 2026-08-22** | **Unix 哲学的由来；MINIX 与 Linux 的血缘** |
| **10** | **The Life of Dennis Ritchie**（Dennis Ritchie 生平）** | 2026-09-26** | **从哈佛到贝尔实验室：C 语言、Unix、Plan 9、Inferno** |
| **11** | **BSD Unix, Part 1 — Unix Code Goes to UC Berkeley** | 2026-09-30** | **1973 SOSP 演讲 → 源码磁带 → 伯克利装机** |
| **12** | **BSD Unix, Part 2 — The Birth of the vi Editor** | 2026-10-11** | **ed → em → ex → vi 的编辑器家谱** |
| **13** | **BSD Unix, Part 3 — The Beginning of BSD Unix** | 2026-10-30** | **1977 第一版 BSD → VAX 虚存 → 2BSD / 3BSD** |

**⭐ 而第 11–13 篇是一个连续的三部曲，作者自己也在第 13 篇开头留了前两篇的链接。**

**⭐ 关于这个系列本身，有两点需要先说清楚：**

**① 它明确说了「对话是戏剧化的」**

> **「This comic is based on Marshall Kirk McKusick's "Twenty Years of Berkeley Unix." **The dialogue is dramatized, not a verbatim record of what the participants said.**」**
>
> **「The comic is based on … **The dialogue is dramatized, not a verbatim record of what the participants said.**」**（第 11 篇）

**⭐ 也就是说：⭐ 漫画里那些「人物对话」是作者的再创作，不是史料。** **而正文里的史实段落是有文献引用的（每篇末尾都有 References）。**

**⭐ 这个区分很重要：⭐ 读的时候该信的、该查的、该存疑的，是三件不同的事。**

**② 它的史实底本是可靠的**

**⭐ 从 References 能看出来，作者主要依据的是这几本经典文献：**

- ⭐ **Marshall Kirk McKusick,《Twenty Years of Berkeley Unix》**（1999）—— **BSD 史的权威著作，也是这个三��曲的直接来源**
- **Andrew Leonard,《BSD Unix: Power to the people, from the code》**（2000）
- ⭐ **D. M. Ritchie & K. Thompson,《The UNIX Time-Sharing System》**（1974）—— **SOSP 那篇原始论文**

**⭐ 而第 9 篇的 References 里还有一条特别值得注意：**

> **「Linus Torvalds, Notes for Linux release 0.01, 1991.」**

**—— 也就是说，作者是直接查了 Linux 0.01 的发布说明来核对那句话的。**

## 二、⭐ 逐篇内容提炼

### 2.1 第 9 篇：Unix 哲学

**⭐ 这一篇回答的是「Unix 哲学到底从哪来」。**

**⭐ 而它的答案很反直觉 —— 「Unix 哲学」并不是 Unix 诞生时就有的纲领：**

> **「But Unix did not start with a grand philosophy. Eric S. Raymond later summed it up with a familiar design principle: "Keep it simple, stupid."」**
>
> **「Come on, you must be joking. Tell me the real philosophy.」**
> **「Hmm... **We just made it.**」**

**⭐ 漫画用这个对话把整件事说透了：⭐ Unix 哲学不是先有纲领、后有实践 —— 它是实践的结果，后来才被人总结成条目。**

**⭐ 而 Doug McIlroy 1978 年那份正式表述，被完整列了出来：**

- **让每个程序只做一件事并做好。要做新活，就重新造一个，而不是给老程序加功能。**
- **预期每个程序的输出会成为另一个（尚未知道的）程序的输入。不要用多余信息污染输出。不要坚持严格的列式或二进制输入格式。不要坚持交互式输入。**
- **设计并构建软件（哪怕是操作系统）要尽早试用，最好在几周之内。不要犹豫于扔掉笨拙的部分并重做。**
- **优先用工具而不是无能的帮助来减轻编程负担，即便你得绕道去造这些工具、并预期用完后把它们扔掉。**

**⭐ 而 Peter Salus 1994 年的三条简化版也一并给了：**

- **写只做一件事并做好的程序。**
- **写能一起工作的程序。**
- **写能处理文本流的程序，因为文本流是一种通用接口。**

**⭐ 而这一篇真正独特的地方，是它把 MINIX → Linux 这条血缘线补上了：**

```
1979  Unix V7 许可证禁止在课堂上使用其源码
  ↓
  Andrew Tanenbaum 造了 MINIX 用于教学，1987 年发布
  ↓
1991  Linus Torvalds 在新买的 386 上用着 MINIX，
      边读 Tanenbaum 的《操作系统：设计与实现》边写 Linux 内核
  ↓
  ⭐ Linux 内核**没有**使用 MINIX 或 Unix 源码，
     它实现的是 **POSIX 风格的标准接口** ——
     所以现有 Unix 程序的源码可以**不改一行**就编译运行
  ↓
  ⭐ 而且 Linux 0.01 发布时就自带了 **Bash 的移植版**
```

**⭐ 而 Tanenbaum 那句被漫画引用的话：**

> **「Maybe I should build a simple OS for my students.」（Tanenbaum，1979）**

**⭐ 而 Torvalds 那句更有名：**

> **「Long winter break... I think I'll read this MINIX book.」（1991）**

### 2.2 第 10 篇：Dennis Ritchie 生平

**⭐ 这一篇的结构是按时间倒着来的 —— 从 1998 年那通电话开始往回追溯。**

**⭐ 而那个开场特别有味道：**

> **「An unexpected call in 1998」**
>
> **「Ring ring!」（电话）**
>
> **「The National Medal of Technology? Both of us? Well, Ken... looks like we're going to Washington.」**
> **「Aren't we getting too many awards?」**
> **「Yeah. I was happy with just the Turing Award.」**
> **「Ha, same here.」**

**⭐ 而往回追溯的关键节点：**

| 时期 | 发生了什么 |
|---|---|
| **1940s** | ⭐ **父亲 Alistair E. Ritchie 在贝尔实验室研究交换电路理论**（自动交换机已投入使用，但许多通话仍需话务员接线）** |
| **1950s-60s** | **哈佛**：选择物理还是数学专业时犹豫；接触计算机 |
| **贝尔实验室** | 与 Ken Thompson 一起工作 |
| **1969** | Unix 诞生（Thompson 写的）** |
| **B → C** | ⭐ **「Learning C through a book」** —— Dennis 是**自学 C 的**，用的是那本《C 程序设计语言》（K&R）** |
| **1970s** | **C 语言与 Unix** |
| **1980s-90s** | **Plan 9**（「The road not taken」）** |
| **1990s** | **Inferno 与 Limbo 语言** |
| **2007** | 退休 |
| **2011-10** | ⭐ **去世**（「A quiet farewell in October 2011」）** |

**⭐ 而「用一本书自学一门语言」这个细节，我觉得是全篇最动人的地方** —— 因为它和第 9 篇的 Unix 哲学遥相呼应：⭐ **Ritchie 造了 Unix，又造了用来写 Unix 的语言，而他自己也是靠一本书学会这门语言的。**

### 2.3 第 11 篇：Unix 代码到伯克利

**⭐ 这一篇从一场演讲开始。**

**⭐ 1973 年 SOSP（ Symposium on Operating Systems Principles）上，Ken Thompson 和 Dennis Ritchie 介绍了 Unix：**

> **「Unix is an interactive, multi-user operating system. We've rewritten it mostly in C, a high-level language, rather than assembly.」**
>
> **「What's C? Wait—you can write an OS in a high-level language?」**

**⭐ 而那五条「main features」被完整列了出来：**

1. **一个分层文件系统，包含可卸下的卷**
2. **兼容的文件、设备与进程间 I/O**
3. **启动异步进程的能力**
4. **系统命令语言可按用户选择**
5. **超过 100 个子系统，包含十几种语言**

**⭐ 而演讲之后的转折 —— 伯克利计算机科学系的 Bob Fabry 找上门：**

> **「I'm Bob Fabry from Berkeley. We'd like to try Unix. Could we get a copy?」**
> **「For research? That should be possible. Do you have a PDP-11/45?」**
> **「We only have mainframes. We're planning to buy a PDP-11. I'll be in touch once we have it.」**

**⭐ 然后是那段特别生动的装机过程：**

**⭐ 1974 年 1 月，装着 Unix Version 4 的磁带到了，研究生 Keith Standiford 负责安装：**

> **「It runs, but it keeps crashing.」**
>
> **（Thompson 通过调制解调器拨号进来帮忙）**
>
> **「The trouble came when both disks tried to seek at once — their shared controller couldn't handle it reliably.」**

**⭐ 而「计算机时间不够分」这段，是我觉得最有画面感的部分：**

> **⭐ **「计算机科学的学生喜欢 Unix，但数学和统计系想要 DEC 的 RSTS。」**
> **⭐ **「折中方案：Unix 每天 8 小时，RSTS 每天 16 小时。为了公平，班次每天轮换。」**
> **⭐ **「每第三天，Unix 拿到午夜到早上 8 点。」**
>
> **「But we're the ones who installed Unix...」**

**⭐ 1975 年秋，伯克利买到了更新的 PDP-11/70，而此时 Thompson 正好回来休假：**

> **「Good timing! I'm taking my sabbatical at Berkeley. I'll install Version 6 when I get there.」**
>
> **「Together with Jeff Schriebman and Bob Kridle, he got Unix Version 6 running on the new PDP-11/70. **The work that followed at Berkeley would eventually grow into BSD Unix.**」**

### 2.4 第 12 篇：vi 的诞生

**⭐ 这一篇讲的是编辑器家谱，而它的叙事结构特别漂亮 —— 从「怎么用电话线打字机编辑文本」这个约束开始。**

**⭐ 起点是 ed（Thompson 1969 年写的）：**

> **「Isn't ed awkward to use?」**
> **「I wrote it for teletypes. Still works for me...」**

**⭐ 而漫画把一段完整的 ed 会话原样呈现了出来 —— 这段在原文里是排版成代码块的：**

```
$ ed
a
ed is the standard Unix text editor.
This is line number one.
.
,p
ed is the standard Unix text editor.
This is line number one.
2s/one/two/
,p
ed is the standard Unix text editor.
This is line number two.
w text
62
q
$ cat text
ed is the standard Unix text editor.
This is line number two.
```

**⭐ 而 1976 年 George Coulouris 从 Queen Mary College 访问伯克利，带来了 em 的磁带：**

> **「Bill! His editor, em, lets you edit a line right on the screen. That's what I need.」**
> **「Here's the em source tape. It'll show you how it handles a video terminal.」**

**⭐ 关键的转折是 Joy 在 ex 上加的「全屏可视模式」—— 那就是 vi：**

> **「Now I'll add a full-screen visual mode to ex.」**
> **「Coding's a lot more fun in visual mode.」**
>
> **⭐ **「视觉模式在 BSD 用户中流行开来。用 vi 命令启动编辑器会直接进入可视模式。**你今天仍然可以在 vi 里用 ex 命令。**」**

**⭐ 而这一篇里我最喜欢的一段，是 West Coast Unix Users Group 的场景：**

> **「Did everyone bring their printouts?」**
> **「Too long!」（Thompson 带着打印好的内核源码，一行一行讲）**
>
> **⭐ **「那种分享代码、解释它如何工作的传统，延续进了 BSD，并进入了更广泛的自由开源软件社区。」**

### 2.5 第 13 篇：BSD 的开端

**⭐ 这一篇是整个三部曲的收尾，而它的标题「The Beginning of BSD Unix」很克制 —— 因为此时 BSD 还不是操作系统。**

**⭐ 起点是 1976 年 Joy 和 Haley 回到实验室后「自己动手改内核」：**

> **「Hmm... we could speed things up here in the kernel. Let's try it.」**
> **「Other universities want copies of our Pascal compiler. Let's bundle it with ex and send them a tape.」**

**⭐ 而 1977 年初的第一版 BSD：**

> **⭐ **「In early 1977, Bill Joy put together the Berkeley Software Distribution, or BSD, bundling the Pascal system with ex… **Early BSD was not a standalone operating system: it was a collection of software to install on an existing Unix system.** About thirty copies were sent out over the following year.」**
>
> **「Thirty tapes to copy...」**

**⭐ 而「为什么只收磁带费」这个细节，连带出了 AT&T 的反垄断协议这条暗线：**

> **「At the time, an AT&T Unix source license was needed to get BSD. **Berkeley charged only for the tape and distribution.**」**
>
> **「If you already have a Unix source license, **it's just the tape and postage.**」**
>
> **⭐ **「Berkeley already had a tradition of sharing research software. BSD carried it on. **Berkeley's Free Speech Movement, hippie culture, and antiwar activism are also said to have influenced Joy's decision to charge so little.**」**

**⭐ 而 Joy 那句抱怨，直接引出了反垄断协议：**

> **「We have Unix, but the **antitrust agreement bars us from the computer business**... **We can't sell it as a product, either.**」**

**⭐ 2BSD：Joy 一个人处理所有分发请求**

> **「Joy did more than fix bugs. **He handled every distribution request, copied BSD onto tapes, and mailed them out himself.**」**
>
> **「Oh, you need a copy of BSD?」**
> **「Another university wants a copy.」**
> **「Tune the kernel. Fix the bugs.」**
> **「More copying.」**

**⭐ 然后是 VAX 与虚拟内存 —— 这一段把 Ozalp Babaoglu 带了出来：**

> **「Professor Fateman's group is getting a VAX. **It's 32-bit, with a whole megabyte of memory.**」**
>
> **「My adviser asked me to add virtual memory to VAX Unix. Could you look over the code?」**
>
> **⭐ **「At the time, 32/V did not use the VAX hardware's virtual-memory capabilities. A program's address space was limited by physical memory, but Professor Richard Fateman's work on the computer algebra system **Macsyma** needed more.」**
>
> **（Macsyma 是 MIT 从 1960 年代末开始做的符号表达式系统，能因式分解、求导、积分）**
>
> **「Not going away for the holidays? Might as well debug this while fewer people are using the VAX.」**
>
> **「By January 1979, most of the bugs had been fixed.」**
>
> **「Finally. It runs without crashing.」**

**⭐ 而 3BSD 的构成也被列了出来：**

> **「Joy ported ex, vi, the C shell, and other 2BSD tools to the VAX, while Peter Kessler and Marshall Kirk McKusick ported the Pascal system. These programs were bundled with the standard 32/V utilities and the virtual-memory kernel that Babaoglu and Joy had integrated and debugged. **The result was 3BSD, which began shipping in December 1979.**」**

## 三、⭐⭐⭐ 我的观察：这条主线是「代码怎么流动」

**⭐ 而我读完五篇，最想说的不是任何一个史实，而是⭐ 「代码怎么流动」这条贯穿始终、却不在任何一篇标题里的主线。**

### 3.1 ⭐ 五篇里的「流动」链条

```
第 9 篇   Unix 源码在贝尔实验室内部流动 → 后来上了磁带
第 11 篇  磁带寄到伯克利 → 研究生装上 → 机器时间不够分给 Unix
第 12 篇  伯克利开「West Coast Unix Users Group」，带打印好的内核源码逐行讲
第 13 篇  Joy 一个人把 BSD 拷到磁带上、寄给各大学 → 2BSD → 3BSD
```

**⭐ 而第 13 篇那两行漫画，是整条主线最凝练的总结：**

> **「Tune the kernel. Fix the bugs.」**
> **「More copying.」**

**⭐ 改内核、修 bug，然后 —— 继续复制。**

### 3.2 ⭐ 而「复制」这个动作，在技术上到底是什么

**⭐ 我想把它说清楚，因为这正是这个系列最值得被现代读者理解的地方：**

**⭐ 那时候复制一份 Unix 源码，需要三样东西：**

| | |
|---|---|
| **① 磁带** | ⭐ **物理载体** |
| **② AT&T 的源码许可证** | ⭐ **法律载体**（持有 Unix 源码许可证才能拿到 BSD）** |
| **③ 一台 PDP-11** | ⭐ **能跑起来的机器** |

**⭐ 而第 13 篇那行「If you already have a Unix source license, it's just the tape and postage.」把这件事说得非常干净：**

**⭐ —— 许可证是门槛，而磁带只是邮费。**

**⭐ 而「门槛」在 AT&T 反垄断协议的约束下被压得很低 —— Berkeley 只收磁带和邮寄费，源码许可仍需自备但费用低廉。**

**⭐ 而这正是为什么 BSD 能够扩散 —— ⭐ 不是因为它免费，而是因为**它足够便宜，而门槛又在法律允许的范围内被尽量放低**。**

### 3.3 ⭐⭐ 而这就是自由软件运动真正继承的东西

**⭐ 我想把这个观察说得更直接一点：**

**⭐ 自由软件运动的核心主张是「**软件应当被自由传播**」。而这句话的技术含义，恰恰就是第 12 篇里那个 West Coast Unix Users Group 的场景：**

> **⭐ **「分享代码，并解释它如何工作。」**

**⭐ 也就是说 —— ⭐ 自由软件运动继承的不是「许可证文本」，而是「**一群人聚在一起读代码、然后把改好的版本传出去**」这个具体做法。**

**⭐ 而这个系列妙就妙在：⭐ 它没有讲这句话，而是用五篇漫画把这件事演了一遍。**

**⭐ 而如果读者今天只记住这个系列的一件事，我希望是这句：**

> **⭐⭐ **「先做出来，然后分���它。」**
> **⭐ **「把磁带邮给下一家。」**

## Sources

- ⭐ 一手：F/OSS Comics 系列（五篇全部原文与配图，Joone Hur 绘）
  - 第 9 篇 The Unix Philosophy（2026-08-22）：<https://fosscomics.com/posts/9.%20The%20Unix%20Philosophy>
  - 第 10 篇 The Life of Dennis Ritchie（2026-09-26）：<https://fosscomics.com/posts/10.%20The%20Life%20of%20Dennis%20Ritchie>
  - 第 11 篇 BSD Unix Part 1（2026-09-30）：<https://fosscomics.com/posts/11.%20BSD%20Unix%20Part%201%20-%20Unix%20Code%20Goes%20to%20UC%20Berkeley>
  - 第 12 篇 BSD Unix Part 2（2026-10-11）：<https://fosscomics.com/posts/12.%20BSD%20Unix%20Part%202%20-%20The%20Birth%20of%20the%20vi%20Editor>
  - 第 13 篇 BSD Unix Part 3（2026-10-30）：<https://fosscomics.com/posts/13.%20BSD%20Unix%20Part%203%20-%20The%20Beginning%20of%20BSD%20Unix>
- ⭐ 史实底本：Marshall Kirk McKusick《Twenty Years of Berkeley Unix》(1999)｜Andrew Leonard《BSD Unix: Power to the people, from the code》(2000)｜D. M. Ritchie & K. Thompson《The UNIX Time-Sharing System》(1974)｜Linus Torvalds《Notes for Linux release 0.01》(1991)
- 相关：本号此前的《选择无聊的技术：创新代币与全局优化》、《BSD 家族全表：四个正统、一个桌面发行版》

---

（说明：本文为系列导读，五篇原文将逐篇做完整中文翻译；**第三节的「代码怎么流动」主线归纳与「自由软件运动继承的是具体做法而非许可证文本」这一判断为笔者观点**。）
