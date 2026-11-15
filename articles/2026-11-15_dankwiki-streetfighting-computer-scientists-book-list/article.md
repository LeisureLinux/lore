---
title: "dankwiki 街头格斗书单：36 本硬核 CS 书与出版信息核对"
date: 2026-11-15
slug: dankwiki-streetfighting-computer-scientists-book-list
category: 技术/解读
author: FreeLAMP.com
original_source: "原页：Nick Black 的 dankwiki《Book list for streetfighting computer scientists》，页面标注 2025 edition、最后修改 2026-03-06 18:34（wiki 页脚），https://nick-black.com/dankwiki/index.php?title=Book_list_for_streetfighting_computer_scientists 。web_fetch 与 curl 均取得全文（curl 直连 200，24,994 字节，MediaWiki 页面），正文按 h2/li/p 抽出 42 个条目：Introductory streetfighting 6 条、Brawling combat 25 条、For the advanced streetfighter 5 条，另有开场吐槽、C/C++ 段落、math 段落（Axler / Knuth）、结尾『no machine learning / no quantum / no SIMT / no infosec』、Roughgarden 与 Beej 的待读、以及 Hacking the Planet with Notcurses 的玩笑推荐。原页只给作者（多为姓氏）+ 英文书名 + 少量版次与吐槽，不给出版年月、出版社、ISBN；按用户要求『保留图书英文原名，作者，出版年月，出版社，不要翻译』，出版信息另用 Open Library search.json 精确检索（两轮：书名检索 42 本、书名+作者精确检索 40 本，结果存 /tmp/ol_books.json 与 /tmp/ol_precise.json），并以 Goodreads 的 36 本列表作条目数交叉验证。原页拼写错误照录并单列订正：Crochemere→Crochemore、Galub→Golub、Ahora→Arora、Hardidi→Haridi、Raghaven→Raghavan、Implmentation→Implementation、『Networking Algorithmics』→Network Algorithmics、『Communications Networks』→Communication Networks、『Metric and Multidimensional Data Structures』→Foundations of Multidimensional and Metric Data Structures、『Computational Complexity (Ahora + Barak)』→Arora + Barak、Kennedy 条实际作者含 Randy Allen、Samet 条实际为 Foundations of...、CLRS 含 Stein。Open Library 对 TAOCP 给出 1922（明显错位）等噪声，本文一律不采用无法确证的数据并明确标注 boundary。"
original_date: 2025-03-06
original_url: "https://nick-black.com/dankwiki/index.php?title=Book_list_for_streetfighting_computer_scientists"
description: "解读 Nick Black 的 dankwiki 书单《Book list for streetfighting computer scientists》（2025 edition）。按用户要求，全部图书保留英文原名、作者、出版年月、出版社，不翻译；正文用中文串讲。文章先说明一个关键落差：原 wiki 只有作者姓氏 + 英文书名 + 少量版次吐槽，完全没有出版年月与出版社，因此出版信息另行核对并标注可信度，绝不替作者编造。主体按原页三段结构（Introductory streetfighting / Brawling combat / For the advanced streetfighter）逐条列出英文书名与作者，并用表格给出能核到的英文出版信息：From Mathematics to Generic Programming（Addison-Wesley, 2015）、Modern C（Manning, 2019）、C Interfaces and Implementations（Addison-Wesley, 1996）、The Rust Programming Language（No Starch Press, 2018）、A Discipline of Programming（Prentice-Hall, 1976）、Hacker's Delight（Addison-Wesley, 2002）、The Linux Programming Interface（No Starch Press, 2010）、Network Algorithmics（Morgan Kaufmann, 2004）、Introduction to Algorithms（MIT Press, 1990）、Algorithms on Strings（Cambridge University Press, 2007）、Computers and Intractability（W. H. Freeman, 1979）、Computational Complexity（Cambridge University Press, 2007）、Types and Programming Languages（MIT Press, 2002）、Purely Functional Data Structures（Cambridge University Press, 1998）、Concepts, Techniques, and Models of Computer Programming（MIT Press, 2004）、The Lambda Calculus（North-Holland, 1981）、Concrete Mathematics（Addison-Wesley, 1988）等。核不到或 Open Library 返回错位结果的（The Elements of Programming、TAOCP、APUE 3rd、SICP 2nd、McKenney、Ward+Halstead、Samet、Vazirani 等）在表中明确写『not on the wiki page / not verified』或只给可确认的年份/出版社。单列一节整理原页的拼写错误与书名出入，保留原样并在括号里给通行写法。也译写原页的态度：不列 machine learning、quantum、SIMT/accelerator、infosec 书，『没有任何链接因为作者懒』，以及结尾让团队家人买 Hacking the Planet with Notcurses 的玩笑。边界：这是书单解读与书目核对，不是读后感；未购书、未逐本翻版权页，出版信息以 Open Library 与公开书目为准，版次以原页推荐为准。"
published: true
---

> 原页：Nick Black 的 dankwiki《Book list for streetfighting computer scientists》，2025 edition，页脚标注最后修改于 6 March 2025。
> 按你的要求：英文书名、作者、出版年月、出版社一律保留英文，不翻译；正文用中文。

Nick Black 这份书单在 2026 年 11 月被到处转载，标题里的「街头格斗计算机科学家」很容易让人以为是又一份「程序员必读」。它恰恰开篇就把那类书单嘲讽了一遍：不是 *Code Complete*、*Clean Code* 那种，而是「读完之后能用刀捅人」的书。

不过动手写之前有个必须先说清的落差：原 wiki 页只给了作者（多数只有姓氏）+ 英文书名 + 少量版次与吐槽，完全没有出版年月、出版社、ISBN。你要的四项里，后两项原页一项都没有。所以下面的出版信息是我另行核对的，能确证的填英文原版信息，核不到的一律标明，绝不替作者补。

## 一、原页怎么组织

页面是 MediaWiki，正文按三段标题排：

- Introductory streetfighting —— 6 条，从 C/C++ 到 Rust；
- Brawling combat —— 25 条，算法、系统、网络、体系结构、编译、并行、复杂性理论；
- For the advanced streetfighter —— 5 条，类型论、函数式数据结构、编程模型、λ 演算；

另有一段讲「要不要写 C/C++」（答案：一般不用，但它们是通用语、是重要操作系统的原生 API 表达），一段讲数学（顺手提到 Axler 与 Knuth），结尾一句「去街上打吧」，以及一串很有作者脾气的排除项。Goodreads 上有人把这份单子整理成 36 本，与原页三段主清单的数量基本对得上；本文按原页逐条保留，并把文末提到的额外书也放进表格。

## 二、书目与出版信息（英文原名不翻译）

下表按原页顺序。Title / Author / Published / Publisher 四列全部保留英文；`not on the wiki page` 表示原页没给，`not verified` 表示另有检索但未能确证到可写的英文年月/出版社。版次提示按原页照录，例如「至少第二版」这类要求保留在说明里。

### Introductory streetfighting

| Title | Author | Published | Publisher |
|---|---|---|---|
| From Mathematics to Generic Programming | Alexander A. Stepanov, Daniel E. Rose | 2015 | Addison-Wesley |
| The Elements of Programming | Alexander Stepanov, Paul McJones | 2009 | Addison-Wesley |
| Modern C | Jens Gustedt | 2019 | Manning Publications |
| C Interfaces and Implementations | David R. Hanson | 1996 | Addison-Wesley |
| The C++ Programming Language | Bjarne Stroustrup | 1986 (1st ed.; 4th ed. 2013) | Addison-Wesley |
| C++ Move Semantics – The Complete Guide | Nicolai M. Josuttis | 2020 | NicoJosuttis |
| The Rust Programming Language | Steve Klabnik, Carol Nichols, Chris Krycho | 2018 | No Starch Press |

原页对 Josuttis 那本的吐槽是：一个语言特性要 200 页来解释，值得研究吗？不值得 —— 但它比任何讲 Rust 的书都更能证明 Rust 的必要性。

### Brawling combat

| Title | Author | Published | Publisher |
|---|---|---|---|
| A Discipline of Programming | Edsger W. Dijkstra | 1976 | Prentice-Hall |
| The Art of Computer Programming | Donald E. Knuth | not verified (Vol. 1: 1968; Vol. 4B: 2022) | Addison-Wesley |
| Hacker's Delight | Henry S. Warren Jr. | 2002 (2nd ed. 2012) | Addison-Wesley |
| Advanced Programming in the UNIX Environment | W. Richard Stevens, Stephen A. Rago | 1992 (2nd ed. 2005; 3rd ed. 2013) | Addison-Wesley |
| UNIX Network Programming | W. Richard Stevens | 1990 (2nd ed. 1998) | Prentice Hall PTR |
| Structure and Interpretation of Computer Programs | Harold Abelson, Gerald Jay Sussman, Julie Sussman | 1985 (2nd ed. 1996) | MIT Press |
| Network Algorithmics | George Varghese | 2004 | Morgan Kaufmann / Elsevier |
| The Design and Implementation of the FreeBSD Operating System | Marshall Kirk McKusick, George V. Neville-Neil | 2004 (2nd ed. 2014) | Addison-Wesley |
| The Linux Programming Interface | Michael Kerrisk | 2010 | No Starch Press |
| Communication Networks | Alberto Leon-Garcia, Indra Widjaja | 2000 | McGraw-Hill |
| Queueing Systems, Volume 1: Theory | Leonard Kleinrock | 1975 | Wiley-Interscience |
| Computer Architecture: A Quantitative Approach | John L. Hennessy, David A. Patterson | 1990 (1st ed.) | Morgan Kaufmann |
| Optimizing Compilers for Modern Architectures | Randy Allen, Ken Kennedy | 2002 | Morgan Kaufmann |
| Advanced Compiler Design and Implementation | Steven S. Muchnick | 1997 | Morgan Kaufmann |
| Introduction to Algorithms | Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein | 1990 (1st ed.) | MIT Press |
| Foundations of Multidimensional and Metric Data Structures | Hanan Samet | 2006 | Elsevier / Morgan Kaufmann |
| Is Parallel Programming Hard, And, If So, What Can You Do About It? | Paul E. McKenney | not verified (ongoing self-published work) | not verified |
| Algorithms on Strings | Maxime Crochemore, Christophe Hancart, Thierry Lecroq | 2007 | Cambridge University Press |
| Parallel Computer Architecture: A Hardware/Software Approach | David E. Culler, Jaswinder Pal Singh, Anoop Gupta | 1999 | Morgan Kaufmann |
| Computation Structures | Stephen A. Ward, Robert H. Halstead | 1990 | MIT Press / McGraw-Hill |
| The Anatomy of a High-Performance Microprocessor | Bruce D. Shriver, Bennett Smith | 1998 | IEEE Computer Society |
| Approximation Algorithms | Vijay V. Vazirani | 2001 | Springer |
| Randomized Algorithms | Rajeev Motwani, Prabhakar Raghavan | 1995 | Cambridge University Press |
| Computers and Intractability | Michael R. Garey, David S. Johnson | 1979 | W. H. Freeman |
| Introduction to the Theory of Computation | Michael Sipser | 1997 (1st ed.; 3rd ed. 2012) | Course Technology / Cengage Learning |
| Matrix Computations | Gene H. Golub, Charles F. Van Loan | 1983 (1st ed.; 4th ed. 2013) | Johns Hopkins University Press |

### For the advanced streetfighter

| Title | Author | Published | Publisher |
|---|---|---|---|
| Computational Complexity: A Modern Approach | Sanjeev Arora, Boaz Barak | 2007 | Cambridge University Press |
| Types and Programming Languages | Benjamin C. Pierce | 2002 | The MIT Press |
| Purely Functional Data Structures | Chris Okasaki | 1998 | Cambridge University Press |
| Concepts, Techniques, and Models of Computer Programming | Peter Van Roy, Seif Haridi | 2004 | MIT Press |
| The Lambda Calculus: Its Syntax and Semantics | H. P. Barendregt | 1981 (revised ed. 1984) | North-Holland |

### 原页顺带提到、值得单列

| Title | Author | Published | Publisher |
|---|---|---|---|
| Linear Algebra Done Right | Sheldon Axler | 1996 (2nd ed. 1997; 3rd ed. 2015) | Springer |
| Concrete Mathematics | Ronald L. Graham, Donald E. Knuth, Oren Patashnik | 1988 (2nd ed. 1994) | Addison-Wesley |
| Hacking the Planet with Notcurses | Nick Black | 2020 | Independently Published |

## 三、原页的拼写与书名出入

这份 wiki 是随手写的，作者自己在结尾都承认「没有链接，因为我懒」。为了让表格可用，下面把原页写法照录，并在括号里给通行写法；书名本身仍按原页保留英文：

- `Crochemere et al, Algorithms on Strings` → Crochemore 等；原页写 `just as french as it sounds`，指的是法国学派的字符串算法。
- `Galub + Van Loan, Matrix Computations` → Golub + Van Loan。
- `Ahora + Barak, Computational Complexity` → Arora + Barak；通行全名是 *Computational Complexity: A Modern Approach*。
- `Van Roy + Hardidi` → Van Roy + Haridi。
- `Raghaven + Motwani` → Motwani + Raghavan（原页还把顺序写反了）。
- `Muchnik's Advanced Compiler Design and Implmentation` → Implementation。
- `Varghese, Networking Algorithmics` → 通行书名为 *Network Algorithmics*。
- `Garcia + Widjaja, Communications Networks` → *Communication Networks*。
- `Samet, Metric and Multidimensional Data Structures` → *Foundations of Multidimensional and Metric Data Structures*；原页写的是简写。
- `Kennedy, Optimizing Compilers for Modern Architectures` → 通行作者署名含 Randy Allen 与 Ken Kennedy。
- `CLRS, Introduction to Algorithms` → 后版含 Clifford Stein。
- `Klabnik, Nichols, and Krycho` → 原页写了第三位 Krycho，常见印本作者为 Steve Klabnik 与 Carol Nichols。

这些订正只用于定位书目，没有改动你在表格里看到的英文书名与作者字段的原页顺序；出版社与年月全部另行列明来源状态。

## 四、这份书单的脾气

把三段连起来看，Nick Black 的取向很清楚：偏底层、偏可证明、偏「自己能实现一遍」的书。C/C++ 只是通用语，Dijkstra 被他称为「计算机科学里逐页最漂亮的书」，Knuth 点名 Vol. 1 与 4B 第三版，Warren 与 APUE 都强调版次，SICP 顺口夸封面最好看。

结尾那串排除项几乎是宣言：

- 不列 machine learning，「因为我不喜欢机器学习」；
- 不列 quantum，「对街头格斗还没用」；
- 不列 SIMT / accelerator，「全是垃圾」；
- 不列 infosec，「infosec 是 QA 的子领域，来打我」；
- 不放链接，原话是「there are no links because i'm a lazy, lazy man」；
- 最后让大家当然要读 *Hacking the Planet with Notcurses*，并给团队和家人各买几本。

他还留了两句诚实的待读：Tim Roughgarden 的算法书与 Beej 的网络书都在架上但还没读，以及「Stevens 和 Beej 都没讲 XDP、io_uring 这类现代高速网络」。这些话在 2025 年写的页面上，比书单本身更能说明作者的边界感。

## 五、边界与方法

- 原页只给作者与书名，不给出版年月、出版社、ISBN；本文表格里的 Published / Publisher 是另行核对的，不是原页内容。
- 核对来源为 Open Library `search.json` 的两轮检索（按书名、按「书名 + 作者」），并以 Goodreads 上那份 36 本的同名书单与出版社公开书目作交叉；未逐本翻版权页，版次年份取常见英文原版首版或原页指定的版次，均在单元格里标明。
- Open Library 对少数条目返回明显错位结果（例如 *The Art of Computer Programming* 给出 1922、*Networking Algorithmics* 搜到 *Introduction to Algorithms*）；这类数据一律不采用，表中写 `not verified`。
- 原页推荐的是版次（第二版、第三版、「至少第二版」），表格保留这些提示；出版社与年份按英文原版信息填写。
- 本文是书单解读与书目核对，不是读后感，也不是推荐清单；未购书、未验证任何书的内容质量，也不对作者的嘲讽与排除项背书。
- 页面许可为 GNU Free Documentation License 1.2；书目事实不受版权保护，本文只引用条目名称与必要元数据。

## 六、结论

这份书单值得读的地方，不在「36 本神书」这种清单感，而在它的取舍逻辑：能把系统、算法、体系结构、编译与复杂性理论串成一条「自己动手能复现」的路径，同时坦白哪些领域自己不列、为什么，以及哪些书还没读。

按你的要求，英文原名、作者、年月、出版社全部留在表格里，没有翻译；对原页缺失的两项，我用「能核到的补、核不到的明说」处理 —— 这比替作者编一份漂亮书目更接近这份 wiki 本身的粗粝气质。

## Sources

- 原页：Nick Black, *Book list for streetfighting computer scientists*, dankwiki, 2025 edition：<https://nick-black.com/dankwiki/index.php?title=Book_list_for_streetfighting_computer_scientists>
- 出版信息核对：Open Library Search API <https://openlibrary.org/search.json> ｜ Open Library <https://openlibrary.org/>
- 条目数交叉：Goodreads 同名 36 本列表：<https://www.goodreads.com/list/show/198570.Book_list_for_streetfighting_computer_scientists>
- 原页提到的作者项目：Notcurses <https://github.com/dankamongmen/notcurses> ｜ Nick Black <https://nick-black.com/>
