---
title: "Cacti 未修 0day：四个 HTTP 请求从访客到 root，没有补丁"
date: 2026-11-27
slug: cacti-4http2shell-zero-day-rce
category: 技术/解读
author: FreeLAMP.com
original_source: "The Hacker News 报道（Ravie Lakshmanan，2026-11-27）＋ 一手核对研究员 ek0ms savi0r 的 4HTTP2SHELL PoC 仓库 README（四个请求全文与四个信任失败）与 watchTowr 的 4HTTP2ROOT FAQ（2026-11-26）。"
description: "解读 Cacti 零日 4HTTP2SHELL/4HTTP2ROOT：无需 CVE 编号，最新版 Cacti Core 1.2.31 开启 guest 账户时，四个 HTTP 请求即可从匿名访客拿到服务器命令执行。链路：guest 经 auth_profile.php?action=update_data 把非数字字符串写进 preview_graphs_per_page → graph_view.php 读取该 stored default 拼进 SQL LIMIT，PDO 接受堆叠语句形成二阶注入 → UPDATE poller_item.arg1 为 shell 命令 → graph_realtime.php 触发 realtime poller，arg1 未经白名单传给 PHP popen()。四个失败叠加：guest 可写数字设置为任意字符串、stored default 绕过请求校验、LIMIT 拼进 SQL、poller 执行数据库存储命令。无内存破坏无反序列化，日志唯一响动是非数字值 PHP warning。watchTowr：截至 11-27 无在野利用、无 CVE、无补丁；缓解为禁用 guest、限制 Web 界面访问、检查 poller 配置与日志。Cacti 常存全网凭证，是天然跳板。"
published: true
---

11 月 26 日，一个化名 **ek0ms savi0r** 的研究员公开了 Cacti 的一个零日：**四个 HTTP 请求，从一个全新的匿名访客会话，拿到 Cacti 服务器的命令执行**——不用登录、不用 API key、不用钓鱼。他称之为 **4HTTP2SHELL / 4HTTP2ROOT**。The Hacker News 11 月 27 日报道。

关键点：**目前没有 CVE 编号、没有官方补丁**。watchTowr 的 FAQ 显示，截至 11 月 27 日也无在野利用报告。但 PoC 已经公开，受影响的是**最新版 Cacti Core 1.2.31**（开启 guest 账户时）。

## 一、四个请求，一条完整的链

这条链最"优雅"（也最可怕）的地方是：**没有内存破坏、没有反序列化 gadget、没有暴力破解**——用研究员的话说，"只是一个从来就不是边界的信任边界"。

**请求 1：成为 guest**。`auth_profile.php` 给每个新访客发一个 guest 会话和 CSRF token，不需要任何凭证。研究员的评论很到位：「问题不是 guest 账户本身，而是 guest 能写什么。」

**请求 2：写入 payload**。guest 通过 `auth_profile.php?action=update_data` 把 `preview_graphs_per_page`（本应是一个"每页显示多少图"的数字）改成一串 SQL：

```
1;UPDATE poller_item SET host_id=1,action=1,arg1=0x<命令的hex> WHERE local_data_id=1;-- 
```

写入用的是 prepared statement——**存储层是安全的，消费层不安全**。设置的值是字符串，之后会被当成 SQL 语句的一部分。

**请求 3：让数据库执行它**。`graph_view.php?action=preview` 读取这个 stored default，把它拼进 `get_allowed_graphs()` 的 SQL `LIMIT` 子句。`graphs` 的值来自数据库里的 guest 设置，而请求侧的 `FILTER_VALIDATE_INT` 根本看不到数据库的默认值。结果 SQL 变成：

```sql
... LIMIT 0,1;UPDATE poller_item SET ...;--
```

**PDO 驱动接受堆叠语句（stacked statements）**，于是 UPDATE 执行了——而 HTTP 响应还是一个正常的预览页面，没有任何明显错误，只有一条 PHP 警告说"非数字值"。

**请求 4：执行命令**。guest 可访问的 `graph_realtime.php?action=init` 触发 realtime poller，后者读取被改写的 `poller_item.arg1`，**不经任何白名单**直接传给 PHP 的 `popen()`。命令通过 shell 执行。研究员的演示在实验环境里（web 层和 poller 跑在 root 下）拿到了 `uid=0(root)`；正常部署中通常是以 `www-data` 或 `apache` 这样的 web 用户执行——**权限取决于部署，但拿到 shell 的能力不取决于部署**。

## 二、四个失败叠加

研究员把根因总结为四层，每层单看都不致命，叠在一起就是预认证 RCE：

1. **guest 能把数字设置写成任意字符串**——profile 端点只检查设置名存在，不检查值是合法整数；
2. **stored default 绕过请求校验**——请求参数被过滤，数据库默认值没有；应用信任自己的存储，仿佛值已经被校验过；
3. **LIMIT 被拼进 SQL**——`LIMIT` 当字符串片段处理，而数据库驱动接受堆叠语句；
4. **poller 执行数据库里存的命令**——`poller_item.arg1` 直接进 `popen()`，任何能写那一行的人都能跑 shell 命令。

第 4 步把 SQL 注入变成了 shell；第 3 步让 Cacti 的数据库"说实话"；前两步让匿名访客走到了这一步。

## 三、为什么 Cacti 的 shell 特别值钱

这不是"某个 web 应用拿到 shell"那么简单。watchTowr 说得好：Cacti 通常存着路由器、交换机、服务器等设备的凭证和连接细节，攻击者到这个层级后，**能获得的立足点远远超出监控服务器本身**。

研究员列了一份 Cacti 主机上通常有的东西：

- 网络设备的 SNMP community strings；
- 数据库里的设备登录凭证；
- poller 用的 SSH key 或服务账号；
- `include/config.php` 里的数据库凭证；
- 邮件中继凭证；
- 对内部管理网络的访问；
- cron 任务和备份脚本；
- 每一台接受监控流量的设备的信任。

「监控网络的那台机器，现在站到了攻击者那边。」而且这条四请求路径很安静：guest 会话正常，profile 更新正常，预览请求正常，实时图请求正常——**没有上传、没有长得像 shell 的 URL payload、没有认证事件**。动静最大的痕迹就是那条非数字值的 PHP warning，而大多数团队不会为它告警。

## 四、没有补丁，怎么办

watchTowr 和 THN 给出的缓解措施：

1. **禁用 guest 账户**——打断整条链的入口；
2. 把 Cacti Web 界面的访问**限制在可信内部网络**；
3. 检查 poller 配置项里有没有**不符合正常轮询设置的异常命令值**；
4. 盯日志里关于"图形显示设置为非数字值"的 warning——这是这条链产生的特征；
5. 官方修复版一出，**立即升级**。

另外，poller 进程创建的新文件也是链已经跑过的迹象。Cacti 官方尚未发布修复版本——这是那种"PoC 已公开、补丁还没有"的最难受窗口期。

## 五、怎么定性

这个漏洞的价值不在技术花活，而在它示范了一种"**信任链的复利**"：一个无害的 per-user 显示设置、一个"反正存数据库里应该没问题"的默认值、一个图方便拼起来的 LIMIT、一个"数据库里存的命令当然可信"的 poller——四个各自看起来都能理解的设计，串起来就是预认证 RCE。

对本号读者：这和我们前面写过的 PHP2Shell→Fragnesia、NGINX 状态机残留标记是同一类教训——**别让低权限输入能写到高权限代码会读取并执行的地方**。Cacti 这次，正是把"访客能写"和"poller 能执行"连成了一条线。

## 参考资料

- The Hacker News 报道：https://thehackernews.com/2026/11/unpatched-cacti-zero-day-enables-rce-in.html
- 研究员 PoC 与完整技术说明（4HTTP2SHELL）：https://github.com/ekomsSavior/Sad-Girls-0day-Club/tree/main/4http2shell
- watchTowr 4HTTP2ROOT FAQ：https://watchtowr.com/intelligence/4http2root-cacti-zero-day-faq/
- Cacti 官网：https://www.cacti.net/
