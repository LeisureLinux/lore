---
title: "「改内核、修 bug，然后继续复制」：F/OSS Comics 第 13 篇《BSD 的开端》中文翻译"
date: 2026-11-03
slug: foss-comics-13-bsd-beginnings
tags: [FOSSComics, BSD, 2BSD, 3BSD, BillJoy, ChuckHaley, OzalpBabaoglu, KenThompson, VAX, 32V, 虚存, Macsyma, RichardFateman, DomenicoFerrari, ex, vi, Cshell, 磁带, AT&T, 反垄断, Unix, DARPA, ARPANET, 技术史, 漫画翻译, 开源运动]
category: 技术/历史
author: FreeLAMP.com
original_source: "F/OSS Comics 第 13 篇《BSD Unix, Part 3 - The Beginning of BSD Unix》，Joone Hur 绘，2026-10-30 首发。系列首页：https://fosscomics.com/ 。本文为完整中文翻译。"
original_date: 2026-10-30
original_url: "https://fosscomics.com/posts/13.%20BSD%20Unix%20Part%203%20-%20The%20Beginning%20of%20BSD%20Unix"
description: "本文是 F/OSS Comics 第 13 篇《BSD Unix, Part 3 - The Beginning of BSD Unix》的完整中文翻译 —— 也是整个五部曲的收尾。开头两行就把这个系列的循环闭合了：「BSD Unix, Part 1 - Unix Code Goes to UC Berkeley」「BSD Unix, Part 2 - The Birth of the vi Editor」。正文完整记录了 BSD 的诞生：1976 年 Joy 与 Haley 亲手改内核，1977 年初第一版 BSD 只是「装到现有 Unix 上的软件集合」而非独立操作系统，30 盘磁带寄出，伯克利只收磁带费而源码许可需自备 AT&T 许可证；Joy 那句「我们有 Unix，但反垄断协议不让我们做计算机生意」引出 AT&T 的历史约束；2BSD 时期 Joy 一个人处理所有分发请求、亲自拷磁带邮寄；1978 年 VAX 到来，研究生 Ozalp Babaoglu 为 Fateman 教授的 Macsyma 符号数学系统加入虚拟内存，Joy 协助集成调试，1979 年 1 月跑通，12 月 3BSD 开始出货。结尾回到 ARPANET 与 DARPA 如何因为「各机构机器不同、软件难共享」而注意到 Unix 的可移植性。"
published: true
---

> **原文**：F/OSS Comics 第 13 篇《BSD Unix, Part 3 — The Beginning of BSD Unix》，**Joone Hur** 绘，**2026 年 10 月 30 日**
> 原文链接：<https://fosscomics.com/posts/13.%20BSD%20Unix%20Part%203%20-%20The%20Beginning%20of%20BSD%20Unix>
> **本文为完整中文翻译**，保留原文的旁白、对话与 References。⭐ 标记处为译者补充。
> ⭐ **本文是 F/OSS Comics 五部曲的第五篇，也是 BSD 三部曲的终篇。**

## 开篇

**⭐ 原文开头的前两行，是这个系列的索引：**

> **「BSD Unix, Part 1 - Unix Code Goes to UC Berkeley」**
> **「BSD Unix, Part 2 - The Birth of the vi Editor」**

## BSD Unix 的开端

**⭐ 旁白：**

> **「1976 年 Ken Thompson 回到贝尔实验室后，Bill Joy 和 Chuck Haley 开始自己研究 Unix 内核。」**

**（对话：）**

> **「嗯……内核这里我们可以再快点。」**
> **「试试看。」**

**⭐ 旁白：**

> **「其他大学想要我们的 Pascal 编译器。我们把它和 ex 打包，给他们寄盘磁带吧。」**

**（对话：）**

> **「其他大学想要我们的 Pascal 编译器。」**
> **「我们把它和 ex 打包，给他们寄盘磁带吧。」**

**⭐ 旁白：**

> **「1977 年初，Bill Joy 组建了 Berkeley Software Distribution（简称 BSD），把 Pascal 系统与 ex（一个从 em 发展而来的行编辑器）打包在一起。**早期的 BSD 并不是一个独立的操作系统：它是一套装到现有 Unix 系统上的软件集合。接下来一年里大约寄出了三十份副本。**[1]」**

**（对话：）**

> **「三十盘磁带要复制……」**

**⭐ 旁白：**

> **「当时要拿到 BSD 需要一份 AT&T 的 Unix 源码许可证。伯克利只收取磁带和分发的费用。[2]」**

**（对话：）**

> **「如果你已经有 Unix 源码许可证，那就只要磁带和邮费。」**
> **「如果你已经有 Unix 源码许可证，那就只要磁带和邮费。」**

**⭐ 旁白：**

> **「伯克利本来就有分享研究软件的传统。BSD 延续了这一点。据说**伯克利的言论自由运动、嬉皮士文化与反战 activism，也影响了 Joy 把价格压得这么低的决定**。[2]」**

![漫画配图：free-speech](images/free-speech.png)

>
> **「大学和研究机构可以用不高的许可费获得 Unix，包括它的源代码。这也有助于系统的传播。[2][6]」**

**（对话：）**

> **「我们有 Unix，但**反垄断协议不让我们做计算机生意**……我们也不能把它当产品卖。」**
> **「我们有 Unix，但反垄断协议不让我们做计算机生意……我们也不能把它当产品卖。」**

## 第二次发行：2BSD

**⭐ 旁白：**

> **「第一次 BSD 发行之后，Joy 根据用户反馈改进了 Pascal 系统。他把它与 vi（ex 的可视模式）、C shell 以及其他工具打包，组成**第二次伯克利软件发行版（2BSD）**。接下来一年里发出了将近七十五盘磁带。[1][5]」**

**⭐ 旁白：**

> **「Joy 做的远不止修 bug。**他处理每一份分发请求，把 BSD 拷到磁带上，然后自己寄出去。**」**

**（对话：）**

> **「哦，你们需要一份 BSD？」**
> **「另一所大学想要一份。」**
> **「调优内核。修 bug。」**
> **「继续复制。」**
> **「继续复制。」**

## 一台 VAX 来到伯克利，1978

**⭐ 旁白：**

> **「Fateman 教授的团队要拿到一台 VAX 了。它是 32 位的，**有一整兆字节的内存**。」**

**（对话：）**

> **「真的吗？我们该把 Unix 装上去。」**
> **「他们已经从贝尔实验室拿到 VAX Unix 了。叫 32/V。」**
> **「你好，我是 Ozalp Babaoglu。」**
> **「我的导师让我给 VAX Unix 加虚拟内存。你能帮忙看看代码吗？」**
> **「当然。我们来看。」**

**⭐ 旁白：**

> **「Babaoglu 是伯克利的研究生，与 Domenico Ferrari 教授一起工作。Joy 协助他把虚拟内存代码整合进 32/V 并调试它。[1][4]」**
>
> **「当时 32/V 并没有使用 VAX 硬件的虚拟内存能力。一个程序的地址空间受限于物理内存，但 Richard Fateman 教授在计算机代数系统 **Macsyma** 上的工作需要更多。虚拟内存用磁盘存储给程序一个比物理内存更大的地址空间。[1]」**
>
> **「Macsyma 由 MIT 从 1960 年代末开始开发，处理符号表达式。它能因式分解、计算导数、进行积分。」**

**（对话：）**

> **「假期不回家吗？」**
> **「不如趁用 VAX 的人少的时候调试这个。」**

**⭐ 旁白：**

> **「调试一直持续到 1978 年底的假期。」**
>
> **「到 1979 年 1 月，大多数 bug 都已修好。[1]」**

**（对话：）**

> **「来试试带虚拟内存的 Unix。」**
> **「终于。它跑起来不崩了。」**

**⭐ 旁白：**

> **「Joy 把 ex、vi、C shell 和其他 2BSD 工具移植到 VAX，Peter Kessler 与 Marshall Kirk McKusick 移植了 Pascal 系统。这些程序与标准的 32/V 工具、以及 Babaoglu 与 Joy 整合并调试好的虚拟内存内核一起打包。**结果就是 3BSD，于 1979 年 12 月开始出货。**[1]」**

**（对话：）**

> **「终于，我们可以把这些发出去了。」**
> **「终于，我们可以把这些发出去了。」**

**⭐ 旁白：**

> **「自 1969 年起，ARPANET 就把由 DARPA（美国国防高级研究计划局）资助的研究机构连接了起来。[3] 但这些机构使用着不同的计算机与操作系统，因此常常无法共享软件。把现有软件移植到新机器上也很昂贵。**DARPA 由此注意到了 Unix 的可移植性，也留意到了伯克利成功向研究机构发行 3BSD 的事。**[1]」**

**（对话：）**

> **「BSD 在这台 VAX 上跑得挺好的。」**
> **「BSD 在这台 VAX 上跑得挺好的。」**

## References

- Marshall Kirk McKusick,《Twenty Years of Berkeley Unix》, in *Open Sources: Voices from the Open Source Revolution*, 1999. Korean edition, Hanbit Media, 2013.
- Andrew Leonard,《BSD Unix: Power to the people, from the code》, Salon, 2000.
- SRI International, ARPANET. Its origins and the first transmission in 1969.
- Ozalp Babaoglu, *Biographical note*. His Unix virtual-memory research as a Berkeley graduate student.
- The Unix Heritage Society (TUHS), *Original 2BSD distribution archive*. The installation document `install.ms` and source code in `2bsd.tar.gz`.
- Warren Toomey,《The Strange Birth and Long Life of Unix》, IEEE Spectrum, 2011.

---

## ⭐ 译者按：三点补充

### 一、⭐⭐⭐ 而「继续复制」这两行，是整个系列最凝练的总结

**⭐ 漫画里 Joy 一个人处理分发请求时，只有四句对话：**

> **「哦，你们需要一份 BSD？」**
> **「另一所大学想要一份。」**
> **「调优内核。修 bug。」**
> **「继续复制。」**

**⭐ 我认为这四句就是「开源」这件事的完整算法：**

```
有人要 → 给他 → 改好 → 再给别人
```

**⭐ 而注意第三句「调优内核」—— ⭐ **这不是「给他一份复制品」，是「**给他一份我改过的**」。**

**⭐ 这就是「衍生作品」这件事的最初形态 —— ⭐ **比「开源许可证」这个概念早了大约二十年。**

### 二、⭐⭐ 而「反垄断协议」那句，是这个故事里最被低估的一根线

**⭐ Joy 那句：**

> **「我们有 Unix，但**反垄断协议不让我们做计算机生意**……我们也不能把它当产品卖。」**

**⭐ 而它和前一句正好构成一对：**

| | |
|---|---|
| **不能卖** | ⭐ **AT&T 的反垄断协议让贝尔实验室不能卖计算机 —— 于是 Unix 不能作为产品卖** |
| **所以给了出去** | ⭐ **而 Unix 的源码许可证（价格极低）成了替代方案** |
| **而伯克利更进一步** | ⭐ **BSD 本身只收磁带费，源码许可需自备 AT&T 许可证** |

**⭐ 我认为这条线解释了为什么「Unix 走的是大学与研究机构」而不是「企业」：⭐ **因为在反垄断协议的约束下，贝尔实验室无法把它变成产品，而研究机构恰好是「学术使用、允许拿源码」的那一类。**

**—— 于是 Unix 的扩散路径，被法律结构直接决定了。**

### 三、⭐⭐ 而 VAX 与虚拟内存，是 BSD 第一次「技术上 necessity」

**⭐ 原文有一句非常关键：**

> **「At the time, 32/V **did not use** the VAX hardware's virtual-memory capabilities. A program's address space was limited by physical memory, but Professor Richard Fateman's work on the computer algebra system Macsyma needed more.」**

**⭐ 我认为这一点值得展开，因为它是「一个需求如何催生一项技术能力」的干净案例：**

```
VAX 有 1 MB 内存（对当时来说很大）
    ↓
但 32/V 没用 VAX 的虚存硬件
    ↓
而 Fateman 的 Macsyma 需要处理巨大的符号表达式 → 装不下
    ↓
⭐ 「需要虚存」这个需求，逼出了 3BSD 的虚存内核
```

**⭐ 而 Babaoglu 那句「假期不回家吗」「不如趁用 VAX 的人少的时候调试这个」，把这段工程史的温度写出来了 —— ⭐ **1978 年底的假期里，伯克利的一间机房，有人在调 VAX 上的虚拟内存。**

**⭐ 而这恰好呼应了本号此前写的《选择无聊的技术》里那句：「我们要的是能思考更大问题的自由」—— ⭐ **而一个系统之所以能被拿去思考更大问题，往往正是因为前人替它垫好了虚拟内存这一层。**

---

## 关于本系列

| # | 标题 | 发布 |
|---|---|---|
| 9 | Unix 哲学 | 2026-08-22 |
| 10 | Dennis Ritchie 生平 | 2026-09-26 |
| 11 | BSD Unix 第一部：Unix 源码进入伯克利 | 2026-09-30 |
| 12 | BSD Unix 第二部：vi 的诞生 | 2026-10-11 |
| **13** | **BSD Unix 第三部：BSD 的开端（本文）** | **2026-10-30** |

**⭐ 系列导读见《一条磁带如何长成一个操作系统：F/OSS Comics 的 Unix 与 BSD 五部曲（系列导读）》。**

---

（说明：本文为原文的完整中文翻译，保留原文的旁白、对话与 References；**译者按三节为笔者补充**。）
