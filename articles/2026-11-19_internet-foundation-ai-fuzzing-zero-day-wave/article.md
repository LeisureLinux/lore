---
title: "Linux 到 PHP 全线失守：AI 扫描器一周撬开互联网底座"
date: 2026-11-19
slug: internet-foundation-ai-fuzzing-zero-day-wave
category: 技术/解读
author: FreeLAMP.com
original_source: "综合报道：2026 年 10 月至 11 月，AI 辅助漏洞挖掘集中披露 PHP2Shell（CVE-2026-109618/109619，Calif/OpenAI/Wiz，10-21）、Java4Shell（CVE-2026-114938，Calif/OpenJDK，11-17）、Apache mod_http2 RCE（CVE-2026-119618，Anthropic OSS Scanner + Google，11-11）、NGINX2Root（CVE-2026-123007/123633 等，Xint/Wiz/Rapid7，11-18，另 chaining 一个未打补丁的 Linux SCTP 0-day）、MySQL CVE-2026-114952（CVSS 9.1，11-17）、Ruby2Shell（CVE-2026-132825，Ada Logics/Anthropic，11-19）。在线核对：CVE 记录、厂商公告、Cloudflare Radar、W3Techs 流量/网站份额、CISA KEV、各研究团队技术报告。"
description: "解读 2026 年 10~11 月这一轮由 AI 辅助挖掘驱动、横跨 Linux 内核、Apache、NGINX、MySQL、PHP、Ruby、OpenJDK 的严重漏洞潮。逐个梳理 CVE-2026-119618/123007/64564、CVE-2026-114952、PHP2Shell、Ruby2Shell、Java4Shell 的成因、影响与修复版本，并用 W3Techs 数据说明这些组件覆盖的网站份额。强调 AI 把老代码中的陈年内存安全债集中翻出来，但'互联网底座崩塌'说法夸张：多数漏洞有补丁、有触发条件。"
published: true
---

过去一个月，安全圈经历了一场密集到让人喘不过气的披露潮。从 Linux 内核的 SCTP、Apache 的 mod_http2、NGINX 的 HTTP/2，到 MySQL 客户端、PHP 引擎、Ruby 字符串转换、OpenJDK 的 Base64 解码器——几乎每一个撑起现代 Web 的基础组件，都在同一时间段里被挖出可远程代码执行（RCE）或本地提权（LPE）的严重漏洞。

让这件事格外扎眼的，不是漏洞本身，而是它们背后的共同推手：AI 辅助的漏洞挖掘。Anthropic 的 OSS Scanner 报出了 Apache 的 critical 漏洞，Google Cloud 的研究团队独立复现；OpenAI 的 Codex 帮研究者在一小时内、花不到 200 美元 token 成本找到了 OpenJDK 的 Java4Shell；NGINX 的漏洞有团队用上了 GPT-6 Astra；Ruby 的 1 字节堆溢出也是 Ada Logics 的研究者配 Anthropic 报出来的。

这些组件到底占了多少互联网？按 W3Techs 2026 年 11 月对已知服务端技术的统计：NGINX 约 30%，Apache 约 20%，PHP 约 68% 的网站；Calif 称 OpenJDK 跑在 90% 的财富 500 强里。说它们是「互联网底座」并不夸张，但先别急着说「底座塌了」——我们一条条拆开看，哪些是真的危险，哪些被标题夸大了。

## 一、Linux 内核 SCTP：从容器里拿到宿主机 root

先说最底层的。Xint 团队在研究 NGINX 漏洞时，顺手在 Linux 内核的 SCTP（流控制传输协议）子系统里发现了一个零日：一个 use-after-free / double-free，代码路径从 Linux 4.15（2018 年）就存在。

问题出在 SCTP 的发送路径：一个 send 操作还在等待时，它所属的 association 可以被转移到另一个 socket，等在这个 send 随后又释放掉已经转移的 association，就造成释放后重用或双重释放。研究者把它和 NGINX 的 RCE 串起来，拿到了宿主机 root——nginx 跑在 Docker 容器里也一样能逃出来。由于同一台机器上的所有容器共享内核，攻下内核等于攻下宿主机和上面所有容器。

有个重要区分：这个零日**没有 CVE、截至披露时也没有内核补丁**，Xint 扣着技术细节没发。它和 8 月份那个 SCTPhantom（CVE-2026-64564）不是同一个漏洞——后者是 SCTP ASCONF 路径的 use-after-free，已在 7.1.6/6.18.42/6.12.101/6.6.148 等稳定版内核修复。但两者都说明一件事：容器从来不是安全边界。临时规避办法是在 `/etc/modprobe.d/` 里写 `install sctp /bin/false` 阻止模块加载（对已加载模块和编进内核的 SCTP 无效）。

## 二、Apache mod_http2：AI 扫描器报出的 critical RCE

CVE-2026-119618，Apache HTTP Server 的 mod_http2 在 `assign_headers()` 里的竞态条件（CWE-362），可导致堆内存破坏乃至 RCE。影响范围：httpd 2.4.55 到 2.4.70，以及独立的 mod_h2 2.0.8 到 2.0.42。只有协商了 HTTP/2（`Protocols` 里带 `h2` 或 `h2c`）的服务器才暴露。

这条漏洞的「AI 味」最浓：CVE 记录里明确记着，Anthropic 的 OSS Scanner 在 2026-10-26 报告（编号 ANT-2026-MAPKT6MZ），Google Cloud 的研究者在 11-03 独立报告；Apache 在 11-11 随 2.4.71 一起修掉。CSA 的研究简报把它当作「AI 加速发现老代码漏洞、且几天内被独立重复发现」的典型案例。不能马上打补丁的，把 `h2`/`h2c` 从 `Protocols` 拿掉（留 `Protocols http/1.1`，但要先确认没有 gRPC 后端依赖 HTTP/2）。

## 三、NGINX2Root：2015 年埋下的 HTTP/2 整数下溢

11 月 18 日，F5 发布 NGINX 修复，Xint 把其中五个漏洞打包命名为 NGINX2Root。最严重的是 CVE-2026-123007：HTTP/2 流控里的整数下溢（CWE-191 + CWE-787），从 2015 年引入 HTTP/2 的 1.9.5 起就存在，一直到 1.31.8。

原理不复杂：客户端发 WINDOW_UPDATE 抬高窗口，再发 RST_STREAM 取消请求，NGINX 退回未发送的额度时没检查 HTTP/2 上限，计数溢出后一个负数长度流进 TLS 发送路径，变成越界内存拷贝。F5 官方措辞谨慎，说代码执行需要 ASLR 被禁用或绕过；但 Wiz、Xint、Rapid7 都演示了绕过 ASLR 后执行代码，Rapid7 还放出了针对 1.31.8 Docker 镜像的可用 PoC。Wiz 甚至在一台只服务静态文件、没有后端和第三方模块的服务器上跑通了——因为漏洞在 NGINX 自己身上。

修复版本：开源版 1.30.7（stable）/ 1.31.9（mainline），Plus 37.0.8.1 / 37.3.0.1；注意 `nginx -s reload` 不会换二进制，必须重启。临时缓解是在监听端口上 `http2 off`。另外，社区版 ingress-nginx 和 NGINX Plus R33–R36 没有修复，Kubernetes 用户尤其要留意——这是最危险的一群暴露面。

顺带说一句「NGINX 默认配置就中招」：准确说法是模块编进了官方镜像，但默认配置并没有打开 HTTP/2；真正默认开着 HTTP/2 的是 ingress-nginx 这类发行版。读安全新闻时这种措辞差别很关键。

## 四、MySQL CVE-2026-114952：客户端组件里的 9.1 分

这条容易被忽略，因为它出在「客户端程序」（Client programs）组件。Oracle 的 CVE 记录写得很清楚：MySQL Server 8.4.0–8.4.13、9.7.0–9.7.4、26.10，以及 MySQL Cluster 多个版本受影响；攻击者无需认证、通过网络协议即可读写甚至删除 MySQL 能访问的全部关键数据，CVSS 3.1 打分 9.1（机密性 + 完整性影响，无可用性影响）。注意 Oracle 这次**没有给 8.0 的 MySQL Server 打补丁**，只有 Cluster 的 8.0 分支在列。如果你的资产清单里有老 8.0，这条要单独盯。

## 五、PHP2Shell 与 Ruby2Shell：语言运行时层面的 RCE

**PHP2Shell**（CVE-2026-109618 和 109619，10 月 21 日披露）是 PHP 引擎自身的问题，和你写的业务代码无关。一个是 OOM/内存_limit 致命错误打断原生代码、请求清理时处理了部分初始化的数据（use-after-free），另一个是陈旧的全局状态导致 OPcache 类型混淆。Calif、OpenAI、Wiz 联合发现，CVSS v4.0 都是 9.2。Wiz 在 WordPress、Drupal、Joomla 的最新容器镜像上做了免认证 RCE 演示，还能未认证读出密码、token、API key。CISA 已在 10 月 26 日把它俩加进 KEV（已知被利用漏洞）目录。修复版本：PHP 8.5.12 / 8.4.27 / 8.3.36 / 8.2.35；8.1 及更早只能找发行版的回移植补丁。受影响部署包括 mod_php、PHP-FPM、php-cgi、FrankenPHP、LiteSpeed——PHP 官网把 mod_php 的风险列为最高。

**Ruby2Shell / ruby2ßhell**（CVE-2026-132825，GHSA-34m4-m9fh-gqp5，11 月 19 日披露）是一个 1 字节堆溢出：在 ISO-8859-1、Windows-1252 等单字节编码里，德语 ß 转成大写要写两个字节「SS」，代码却只检查了 1 字节空间，21 个 ß 就能溢出 1 字节。UTF-8 走另一条路径，不受影响。代码从 Ruby 2.4.0 就有。Veria Labs 说默认配置的 Rails 和经典风格 Sinatra 无需认证就能触发；GitLab、GitHub Enterprise Server、Mastodon、Discourse 等自带 Ruby 的产品都在受影响名单里。修在 3.3.14 / 3.4.13 / 4.0.10；Ruby 3.2 及更老版本已 EOL，不提供补丁。Ruby 团队说手里有能达成 RCE 的 PoC，暂未发现野外利用——这点和 PHP2Shell 不一样，别混为一谈。

## 六、OpenJDK Java4Shell：AVX-512 手写汇编里的溢出

CVE-2026-114938，Calif 找到、11 月 17 日随 Oracle 补丁一起公开。问题出在 OpenJDK 为加速 Base64 解码写的 AVX-512 手写汇编：输入 64 个 `A` 加一个 `=` 时，尾部填充的长度计算出错，往一个可能只有 50 字节的缓冲区写进 64 字节，程序随后才拒绝这个非法输入，但内存已经被踩坏了。

Calif 称研究者用 OpenAI 的 Codex 花一小时、不到 200 美元 token 就找到它，并管这种人机协作叫「半人马黑客」。他们在 Keycloak、Jira、Confluence、Artifactory、Jenkins、PingFederate 的默认配置上演示了免认证 RCE。触发有硬件前提：x86-64 且支持 AVX-512 VBMI（Ice Lake 及更新的 Intel、Zen 4 及更新的 AMD），ARM64 不受影响；刚启动的 JVM 还没 JIT 编译到那条快路径，也暂时不走漏洞代码。修复看 11 月 17 日的 OpenJDK 公告和 Oracle CPSU；临时缓解可加 `-XX:-UseBASE64Intrinsics`（会有性能代价）。

## 七、「摇摇欲坠」吗：把恐慌和数字放在一起看

回到开头那个问题——这些组件占多少互联网？W3Techs 的口径是「网站数」（且可重叠），不是流量：NGINX 约 30%、Apache 约 20%、PHP 约 68%，Cloudflare Server 约 34%（它多数时候是前面的反向代理）。Java 的 90% 财富 500 强是 Calif 的估算。这些数字足够说明「覆盖面广」，但不足以支撑「互联网完了」。

几个必须放在一起说的限定：

- **大多数有补丁**。Apache 2.4.71、NGINX 1.31.9/1.30.7、PHP 四个分支、Ruby 三个版本、OpenJDK 11 月更新、MySQL 对应版本都已修。真正没有补丁的是那条 Linux SCTP 零日，和不给修复的 ingress-nginx / NGINX Plus R 系列。
- **触发条件并不总是「连上就打」**。NGINX 官方说要绕过 ASLR；Java4Shell 要特定 CPU 和 JIT 后的调用路径；Ruby2Shell 要应用把某类单字节编码的用户输入做大小写转换；Apache 要开了 HTTP/2。
- **野外利用要分开看**。PHP2Shell 已进 CISA KEV；Java4Shell 有 CISA 告警、已有攻击尝试和可工作的利用代码；而 Apache、NGINX 那批截至披露时多数学者报告「无确认的野外利用」，NGINX 不在 KEV 里。
- **AI 是放大器，不是魔法**。这些 bug 在代码里躺了 8 到 18 年；AI 做的是把审计规模和速度提上去——自动扫描、自动复现、自动构造利用链。CSA 的原话很到位：连 Anthropic 和 Google 几天内都能独立重复发现同一条 critical 漏洞，说明这类代码路径的「发现门槛」正在崩塌。

真正该慌的，是那些「编译进去就忘了、过期 EOL 分支还在跑、容器镜像钉死旧 digest」的部署：PHP 8.1 以下、Ruby 3.2 以下、社区版 ingress-nginx、没打 SCTP 缓解的内核。与其说互联网底座摇摇欲坠，不如说它从来就建在一批比使用者年纪还大的 C/C++ 代码上，现在终于有人拿着新工具逐块敲过来了。敲出来的每一块，都该补上。

## 参考资料

- CVE-2026-119618（Apache mod_http2）：https://www.cve.org/CVERecord?id=CVE-2026-119618 ；Apache 2.4.71 公告：https://httpd.apache.org/security/vulnerabilities_24.html
- CVE-2026-123007（NGINX HTTP/2）及 Xint NGINX2Root：https://xint.io/blog/nginx2root-remote-code-execution ；Rapid7 分析：https://www.rapid7.com/blog/post/ve-cve-2026-123007-critical-nginx-http-2-integer-underflow-leads-to-rce-fixed
- NGINX SCTP 零日与容器逃逸：https://lwn.net/Articles/1108362
- CVE-2026-114952（MySQL）：https://www.cve.org/CVERecord?id=CVE-2026-114952
- PHP2Shell（CVE-2026-109618/109619）：https://www.wiz.io/blog/php2shell-php-rce ；CISA 告警：https://www.cisa.gov/news-events/alerts/2026/10/21/critical-vulnerabilities-php-require-immediate-patching
- Ruby2Shell（CVE-2026-132825）：https://radar.cloudflare.com/zero-wire/ruby2shell
- Java4Shell（CVE-2026-114938）：https://cyberscoop.com/java4shell-critical-java-flaw-openjdk ；OpenJDK 公告：https://openjdk.org/groups/vulnerability/advisories/2026-11-17
- 网站份额数据：https://w3techs.com/technologies/overview/web_server ；https://w3techs.com/technologies/details/pl-php
