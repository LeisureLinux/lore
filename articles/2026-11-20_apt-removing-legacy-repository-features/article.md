---
title: "APT 要删掉老仓库支持：AI 把兼容性的账算到了 Debian 头上"
date: 2026-11-20
slug: apt-removing-legacy-repository-features
category: 技术/解读
author: FreeLAMP.com
original_source: "Phoronix《Debian's APT Removing Some Features Due To Advancements In AI Security Discoveries》（2026-11-19/20）＋ Debian-devel-announce 一手公告《EOL notice for various APT repository configurations》（Julian Andres Klode，2026-11-19，message-id av7_w0YhAlMjzbjL@jak-t14-g3）＋ DSA-6607-1（CVE-2026-109518，Max Justicz，apt 3.0.4 修复）＋ 本号此前两篇 APT 文章（CVE-2026-109518 与 Ubuntu SHA3）的交叉核对。"
description: "解读 Debian APT 维护者 Julian Andres Klode 宣布在 unstable 移除一批遗留仓库特性：detached Release.gpg、弱哈希（MD5/SHA1）仓库、无哈希或无 Release 文件的仓库；并在评估移除 allow-insecure/allow-downgrade-to-insecure 与各类 fallback。动机是 CVE-2026-109518 暴露的下载代码复杂性与 AI 辅助安全研究放大了这种复杂性风险。给出迁移建议、时间表（unstable 11-24 截止，stable 仍支持但 2027 起可能无预警移除），并辨析'AI 逼着删功能'的说法。"
published: true
---

Debian 的 APT 要动刀了。不是加功能，是删功能——而且删的理由很直白：这些老仓库格式的兼容代码太复杂，AI 又让挖漏洞变得太容易，留着的风险已经大过好处。

维护者 Julian Andres Klode 在 11 月 19 日的 debian-devel-announce 上发了正式 EOL 通知：从下周（unstable 的改动截止日是 11 月 24 日）开始，移除一批遗留仓库配置的支持。这不是开发者的即兴发言，是一份带着明确清单、明确时间线、明确迁移路径的公告。

## 一、导火索：验证完了，包还是被换了

这件事的直接背景，是本号此前写过的一条漏洞：CVE-2026-109518。Debian 在 11 月 4 日的 DSA-6607-1 里披露，APT 在 HTTP 重定向后可能把两次不同的包下载合并成同一个 URI，断点续传时重新打开目标文件（可能是硬链接），于是中间人能在**签名验证之后**把包换掉，以 root 执行任意代码。发现者是 Max Justicz，稳定版 trixie 在 apt 3.0.4 修复，同时带了几个越界访问问题的修复。

Klode 的原话把因果链讲得很清楚：这次的下载代码漏洞，加上 AI 在安全研究上的持续进步，让 APT 下载代码的「惊人复杂度」被摆到了聚光灯下。而这些复杂度里，很大一块就是为了维持那些「其实没人用、或者很容易迁走」的旧仓库格式。

换句话说：漏洞不是因为某个算法写错了，而是因为代码路径太多、状态太复杂，复杂到连维护者自己都承认「里面可能藏着一大堆 bug」。AI 只是把「复杂度 = 攻击面」这个等式从理论变成了预算表上的数字。

## 二、现在就删的：三类仓库格式

Klode 列了明确的移除清单（unstable 下周生效）。

**第一类，带独立 Release.gpg 签名的仓库。** 请尽快加上 InRelease 文件；不加的话，这些仓库以后只能当「不受信任」（untrusted）仓库用。

**第二类，只有 MD5、SHA1 这类弱哈希的仓库。** 过去靠 `Acquire::AllowWeakRepositories` / `allow-weak` 打开，但「哪些文件允许用弱哈希」这件事需要额外的状态跟踪，容易搞混。替代方案是把哈希框架扩展成 `APT::Hashes::<name>::Trusted`，给某个哈希打上「可信」标记，用来有限度地支持检查历史仓库。

顺带一提，这和本号 10 月初写过的另一件事正好对上：Canonical 的开发者正在给 APT 加 SHA3-256/384，为 SHA2 万一被攻破提前铺路。一边加新哈希族，一边砍弱哈希的兼容分支——方向是一致的。

**第三类，没有哈希、或者压根没有 Release 文件的仓库。** 这类仓库 APT 以前不知道文件大小和哈希，只能把所有可能的文件路径挨个探测一遍，结果是可能遭遇无限响应之类的问题——Klode 特意点了这个风险。

删完之后，仓库只剩两种形态：带 InRelease 的签名仓库，以及带 Release 文件的未签名仓库；后续所有请求都带着可信的哈希和大小。这能让下载代码大幅瘦身。

## 三、还在评估的：insecure 选项和各类 fallback

除了「已经决定删的」，Klode 还列了「正在评估删除」的：

- **`allow-insecure` / `allow-downgrade-to-insecure`**（对应 `Acquire::AllowInsecureRepositories`、`Acquire::AllowDowngradeToInsecureRepositories`）。功能看着小，但值得问一句：既然「trusted」标志已经能表达信任，何必再留一套 insecure 逻辑？把仓库要么真信任、要么强制信任，概念上简单得多。
- **各种 fallback**：比如 Packages.xz 缺失或校验错就退回 Packages.gz，pdiff 不完整就退回完整 Packages，翻译文件也有类似的回退。Klode 说得很重——这些类在几种状态之间来回切换，「相当糟糕」，和无哈希仓库一样会引入复杂的控制流和状态管理，而状态机正是 bug 的温床。
- **其他非必要特性**，比如索引文件的压缩存储。这类目前没有已知的直接安全影响，但压缩索引会让「提交前验证沙箱最终结果」变得更难。

## 四、时间表与影响：你的 sources.list 该体检了

关键时间点：

- **unstable**：下周二（11 月 24 日）之后的改动窗口开始删除；
- **stable**：Klode 希望继续为这些特性提供安全支持，但「可能无法做到」；
- **2027 年起**：安全更新可能不再提前通知就移除相关特性。

所以现在最该做的事，是清点自己的软件源：

1. 有没有还在用 `Release.gpg` 而没有 `InRelease` 的仓库？去找上游要 InRelease，或者接受它变成 untrusted。
2. 有没有 MD5/SHA1 老仓库？迁到有 SHA2 的镜像；实在要留，关注 `APT::Hashes::<name>::Trusted` 的新机制。
3. 有没有 flat repository（无 Release 文件）？这是被 pointed out 的「无限响应」风险点，优先处理。
4. 用了 `allow-insecure` / `allow-downgrade-to-insecure` 的，开始规划替代方案——这些选项可能保不住。
5. 自建镜像站的，确认索引生成管线会产出 InRelease 和带哈希的 Release，别只发 Packages.gz。

## 五、怎么读「AI 逼着 Debian 删功能」这个说法

Phoronix 的标题写的是「因 AI 安全发现进步，APT 移除部分特性」。这个因果是真的，但很容易被读成「AI 找到了 bug，Debian 吓得删功能」——那是把复杂的关系压扁了。

更准确的说法有三层：

- **漏洞是近因**。CVE-2026-109518 是一次实打实的根权限代码执行，不是理论推演；修复提交本身很小（独占打开目标文件、续传时改为复制内容到新文件），但它暴露的是「文件状态管理」这块地基的问题。
- **复杂度是根因**。Klode 说的是风险收益比：这些兼容分支服务的是「没人用或很容易迁走」的仓库，收益极低；而每多一条状态路径，审计和验证的成本就上升一截。
- **AI 是放大器**。它让「把每条老代码路径都翻一遍」的边际成本大幅下降。本号前一篇写 Xen XSA-523 时也见过同样的署名：`Assisted-by: Claude`。当审计成本趋近于零，「留着老代码」就不再是免费的。

所以这不是恐慌性删库，而是一次迟到的技术债清算：过去二十年，兼容旧格式的成本被摊薄在「反正也没人审计那么细」的默契里；现在这个默契不成立了。

对普通用户来说，结论反而简单：你的日常 `apt update` 大概率不会有任何变化——Debian、Ubuntu 官方源早就用 InRelease 和 SHA2/SHA256 了。真正需要动作的，是那些自建仓库、内网老镜像、以及还钉着十年前第三方源的部署。对这些人，Klode 的提醒值得原样转述：请尽快迁移，2027 年之后的安全更新可能不再提前打招呼。

## 参考资料

- Phoronix 原文：https://www.phoronix.com/news/Debian-APT-Removing-Features
- Debian-devel-announce 一手公告（Julian Andres Klode，2026-11-19）：https://lists.debian.org/debian-devel-announce/2026/11/msg00001.html
- CVE-2026-109518 / DSA-6607-1 报道：https://www.phoronix.com/news/Debian-APT-MITM-RCE ；DSA-6607-1：https://lists.debian.org/debian-security-announce/2026/msg00526.html
- 本号相关阅读：文章《签名验证过了，然后被换掉：APT 自己的 CVE-2026-109518》、《Ubuntu 正在给 Debian 的 APT 加 SHA3》
