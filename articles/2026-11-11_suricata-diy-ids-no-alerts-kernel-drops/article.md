---
title: "Suricata 没告警不等于没看见：一台双网口旧 PC 做 IDS 的三个真问题"
date: 2026-11-11
slug: suricata-diy-ids-no-alerts-kernel-drops
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：MakeUseOf《I turned an old PC into a DIY hacker detector, then tried to hack it》（Gregory Gibson，2026-11-10，全文含正文未提及的后半段：196 个 SYN flow 全部 alerted=false、自制 threshold 规则、吞吐测试 5.73M/7.80M 丢包）＋ Suricata 官方 Quickstart（sid 2100498 测试签名、ET Open 默认规则集、EVE JSON）＋ Suricata 官方 EVE JSON Format（flow.alerted 字段定义、event_type flow/alert 关联）＋ Suricata 官方 Thresholding Keywords（type threshold / limit / both、detection_filter 的垂直扫描示例）＋ Suricata 官方 Statistics（capture.kernel_packets / kernel_drops 在 AF_PACKET 下的含义）＋ Suricata 官方论坛关于 AF_PACKET IPS 不能与 Linux 网桥共用 ＋ ET Open 官方下载说明（每日更新、Suricata-Update 为推荐方式）＋ EveBox 官方文档与 GitHub（SQLite / Elasticsearch 后端、oneshot 模式、端口 5636）＋ Debian 13 ifupdown/interfaces(5) 手册"
original_date: 2026-11-10
original_url: "https://www.makeuseof.com/i-turned-an-old-pc-into-a-diy-hacker-detector-then-tried-to-hack-it/"
description: "本文核对 MakeUseOf 上「用旧 PC 做 DIY 黑客探测器」一文，指出流传的摘要漏掉了原文后半最关键的三段。作者 Gregory Gibson 用双网口 Zotac Nano 装 Debian 13，在 /etc/network/interfaces 里用三行把 enp3s0 与 ens1 桥成 br0 并从 DHCP 取管理地址，笔记本关 Wi-Fi 后经网桥到 Starlink 路由器；再装 Suricata 监听笔记本侧端口、suricata-update 拉 ET Open 规则，用 EveBox 看 EVE 事件。Nmap 扫 100 个端口找到 4 个开放端口却零告警 —— 但原文并未停在「没给原因」：作者查了 flow 日志，196 个带 SYN 的 TCP flow、覆盖全部 100 个目的端口，每个 alerted 都是 false，即 IDS 看见了、只是 ET Open 规则集不认为裸 SYN 扫描该升级为告警；他补了一条本地 threshold 规则（同一源 10 秒内 20 个 SYN）后重扫才在 EveBox 看到告警。更关键的是被摘要完全漏掉的吞吐测试：7.80M 个可供捕获的包里丢了 5.73M，约 73.5%，原因是桥接转发照常进行、Suricata 只拿副本，捕获缓冲满了就丢副本而不影响业务流量 —— 这正是 IDS 旁路部署的固有语义。文章据 Suricata 官方文档逐条解释这套机制：flow.alerted 字段含义、alert 与 flow 通过 flow_id 关联、sid 2100498 是官方指定的功能验证签名、threshold 与 detection_filter 的差别、kernel_drops 在 AF_PACKET 下的定义、AF_PACKET IPS 必须由 Suricata 自己桥接而不能用内核网桥，以及 ET Open 与 ET Pro、EveBox 的 SQLite/Elasticsearch/oneshot 三种形态。结论：这套盒子的价值是让人亲手验证「IDS 是否真的看到流量」，而不是拿它守家；上线前要做的是先验证捕获链路、再确认规则覆盖、最后盯 kernel_drops。"
published: true
---

> 一手：MakeUseOf 原文全文（2026-11-10）
> 官方：Suricata 快速上手、EVE 事件格式、阈值规则、性能统计与官方论坛，ET 开放规则集说明，EveBox 文档，Debian 13 网络配置手册
>
> 本文据原文与官方文档逐条核对。流传的摘要停在「Nmap 扫完没有告警、正文未给出原因」，实际原文后半段把这个悬案破了，还做了一次吞吐压测。

11 月 10 日 MakeUseOf 发了篇动手文章：把一台双网口 Zotac Nano 小主机塞到笔记本和交换机之间，做成 DIY 入侵检测系统。常见的转述到这里就结束了 —— 装 Debian 13、桥接两个网口、装 Suricata 和 EveBox、用 Nmap 扫出 4 个开放端口，结果 IDS 一条告警没出，「正文未给出原因」。

把原文读完后半段会发现，这个「未给出原因」是转述漏读造成的。作者不但查明了原因、写了条本地规则把告警逼出来，还顺手跑了吞吐测试，测出 73.5% 的捕获丢包率，最后自己下的结论是这盒子只能留在实验台上。这三段才是文章里最值钱的部分。

## 一、先把那台盒子怎么搭的还原清楚

硬件是带双以太网口的 Zotac Nano mini PC，装 Debian 13。接线方式：`enp3s0` 接交换机，`ens1` 接 Windows 笔记本，笔记本关掉 Wi-Fi，逼它的上网流量走这台盒子的网桥，再转发到 Starlink 路由器。

`/etc/network/interfaces` 里就三行：

```
auto br0
iface br0 inet dhcp
    bridge_ports enp3s0 ens1
```

这三行做了两件事：把两个物理口并进二层网桥 `br0`，并让 `br0` 自己通过 DHCP 拿一个管理地址。Debian 13 默认不再预装 `ifupdown`（手册里 `interfaces(5)` 仍由该包提供），所以照抄之前得先确认 `ifupdown` 与网桥支持在位，否则配置文件写了也不会被读取。注意 `br0` 拿的是管理地址，两个物理口本身不配 IP —— 这正是「透明串接」该有的样子。

接着装 Suricata，设它监听笔记本那一侧的物理口，`sudo suricata-update` 拉 Emerging Threats Open 规则集。Suricata 官方 Quickstart 的默认流程就是这一句，规则落到 `/var/lib/suricata/rules/suricata.rules`。因为 Suricata 没有 GUI，又装了 EveBox 看记录。

这里藏着第一个概念分层：Linux 网桥负责转发，Suricata 负责旁路看副本。网桥在内核二层把帧从一口复制到另一口，业务流量不经过 Suricata；Suricata 通过 `AF_PACKET` 从指定网卡拿到一份拷贝去解码、跟规则比对。两者不是同一条路径。Suricata 官方论坛有个几乎同配置的提问，回答写得很直白：`AF_PACKET` 的 IPS 模式必须由 Suricata 自己充当网桥（用 `copy-mode: ips` + `copy-iface` 在两个口之间搬包），不能和 Linux 内核网桥混用，因为内核网桥工作在不同层，Suricata 控制不了。想做阻断得推倒重来；这套配置从一开始就是纯 IDS。

## 二、「零告警」的真相：看见了，但规则说不值得报

先说作者怎么确认链路是通的。他在 Linux 机器上写了个含 `uid=0(root) gid=0(root) groups=0(root)` 的文本文件，用临时 Python HTTP server 提供，再从笔记本用 PowerShell 跨网桥取回来。EveBox 立刻出现两条告警：一条认出 Python HTTP server 的 banner，另一条是 `GPL ATTACK_RESPONSE id check returned root`。

这条不是巧合。Suricata 官方 Quickstart 里把 SID 2100498 明写为「专门用来测试 IDS 功能」的签名：

```
alert ip any any -> any any (msg:"GPL ATTACK_RESPONSE id check returned root"; content:"uid=0|28|root|29|"; classtype:bad-unknown; sid:2100498; rev:7; ...)
```

它匹配的是 IP 流量里出现 `uid=0(root)` 这段载荷。作者自嘲「我的黑客技术就是往文本文件里打了个 root」，但这一步的价值很实在：用一条已知必定命中的签名证明「采集 → 检测 → EVE 输出 → EveBox 展示」整条链路是通的。这篇文章里最有方法论意义的操作，其实就是这个。

然后是 Nmap：

```
sudo nmap -sS -n -Pn --top-ports 100 --reason 192.168.1.208
```

不到两秒，100 个常见 TCP 端口里 4 个 open（多是远程管理端口）、96 个 filtered。EveBox 刷新后没有任何新告警。

原文接着写道，他去查了 Suricata 的 flow 日志：两台机器之间 196 个带 SYN 标志的 TCP flow，覆盖全部 100 个目的端口，但每个事件的 `alerted` 都是 `false`。这个字段在 Suricata 官方 EVE JSON 文档里有明确定义 —— `flow.alerted` 表示「该 flow 上是否出现过告警」，取值 true 或 false；`alert` 事件和 `flow` 事件通过同一个 `flow_id` 关联，无论有没有告警都会产生 flow 记录。

所以答案不是「IDS 没看到」，是 IDS 看到了，但没有一条规则认为这值得升级成告警 —— 原文那句「The IDS had seen it. Suricata had just decided it wasn't worth escalating.」说得很准。这两者在运维上完全是两回事：

- 「没看到」= 采集链路断了（接口选错、网桥没转发、混杂模式、缓冲丢包）；
- 「看到了没报」= 规则集覆盖问题。

`-sS` 是半开 SYN 扫描，不发完整握手、没有应用层载荷。ET Open 里当然有 `ET SCAN` 类规则，但大量扫描类签名依赖特定报文特征、载荷内容或阈值，一次默认速率的 `--top-ports 100` 不必然命中。把「没告警」当成 IDS 失效，会去查错的方向。

作者的修法是写一条本地规则：同一源 IP 在 10 秒内对测试笔记本发出 20 个 TCP SYN 就告警，命名 `LAB TCP SYN burst to test laptop`，并特意说明这样命名是为了避免反复扫单一端口也把规则绊响。重载规则后重扫，EveBox 里出现了这条告警和扫描器 IP。

这正好对上 Suricata 官方文档里 `threshold` 关键字的 `type threshold` 语义：`track by_src, count N, seconds T` 表示「在 T 秒内匹配到第 N 次才生成告警」，与 `limit`（抑制告警洪泛）、`both`（两者结合）分工不同；文档还给了一个更贴切的扫描检测例子，用 `detection_filter` 按 `unique_on dst_port` 统计「60 秒内 ≥10 个不同目的端口」的垂直扫描。也就是说，端口扫描这类行为在 Suricata 里靠阈值与去重计数表达，单包签名覆盖不了。原文没贴出规则全文，这层机制是官方文档补上的。

顺带一句：ET Open 官方下载说明写着规则集工作日每日更新、偶尔有带外更新，推荐用 `suricata-update` 每日拉取、不要高于每小时一次（先看 `version.txt` 是否递增）。它是免费的开放规则集，与商业的 ET Pro 分开；用默认规则集跑实验室可以，指望它覆盖全部扫描行为不现实。

## 三、被摘要整段漏掉的吞吐测试：73.5% 丢包

这才是作者最终没把盒子放进家庭网络的原因。

原文的说法是：Debian 一边转发每个包，一边给 Suricata 一份副本去检查；在持续大负载下，副本到达的速度远快于检测器处理速度。捕获缓冲一旦填满，Debian 就开始丢弃送检的副本，而转发照常进行。跨桥接测试里，7.80M 个可供捕获的包丢了 5.73M，约 73.5%。

他补了一句很关键的推论：规则只能匹配 Suricata 真正看得见的证据；如果那个装着假 `uid=0(root)` 响应的包正好在被丢的副本里，文件照样取回来了，但一条告警都不会有。

这不是 bug，是旁路 IDS 的设计取舍。Suricata 官方 Statistics 文档对 `AF_PACKET` 模式下两个计数的定义很干脆：`capture.kernel_packets` 是成功送到用户态的包数，`capture.kernel_drops` 是被丢弃、没有送到用户态的包数；官方性能分析章节把 `capture.kernel_drops` 列为最明显的排查指标，理想值是不掉包。因为转发由内核网桥独立完成，丢的只是副本，用户的下载、游戏、视频完全无感 —— 这正是「IDS 不打断业务」的代价：它静默地失效，而且从业务侧看不出来。

所以这三个环节是有先后的：先确认采集链路（`kernel_packets` 在涨、`kernel_drops` 接近零），再确认规则会不会命中（用已知签名验证），最后才是讨论「某次扫描为什么没报」。作者的顺序恰好相反——先用一条必中签名侥幸验证了链路，再撞上「看见却不报」，最后才在压测里发现满载时链路根本不成立。这也是他写「还没资格进家庭网络」的原因：家里有人打 3A、看流媒体、下大文件，73.5% 的丢包率不能接受。他自己也留了余地，认为算力给够 Suricata 会好很多。

## 四、这套工具链值得单独认识一下

| 组件 | 是什么 | 在这套方案里的角色 |
|---|---|---|
| Linux 网桥 `br0` | 内核二层转发 | 让笔记本流量物理经过这台盒子，管理地址由 DHCP 给 `br0` |
| Suricata | 开源网络 IDS/IPS 引擎（OISF） | `AF_PACKET` 旁路取副本，解码、跟踪 flow、比对规则 |
| `suricata-update` | 官方规则管理命令 | 默认拉 ET Open，输出到 `/var/lib/suricata/rules/suricata.rules` |
| ET Open | Proofpoint Emerging Threats 的免费开放规则集 | 提供 `GPL ATTACK_RESPONSE` 等签名；工作日每日更新 |
| EVE JSON | Suricata 的结构化事件输出 | `alert` / `flow` / `dns` / `http` 等 `event_type`，用 `flow_id` 关联 |
| EveBox | Jason Ish 开发的 Suricata EVE 事件 Web 查看器，MIT 许可 | 把 `eve.json` 变成可搜索的告警面板，默认端口 5636 |

EveBox 常被简化成「Suricata 的 GUI」，但它的定位更像事件查看器：官方文档列了四种部署形态（已有 Elasticsearch + Logstash / Filebeat、EveBox Server + Elasticsearch、EveBox Server + 内置 SQLite，以及 `oneshot` 直接读一个 `eve.json` 到临时库）。对家庭/低负载场景官方直接建议从 SQLite 起步，不用搭一整套 ELK；`evebox oneshot /path/to/eve.json` 则适合离线翻一份日志。它还有 PCAP 模式，能拉容器化 Suricata 处理抓包文件、自动更新 ET Open 等规则后导入事件，全程本地不上传。文章里用它看 `example.org` 的 DNS 查询与响应、看 flow 的 `alerted`，用的就是事件检索这一层。

顺手记一处原文的限定：作者特意提醒，开始任何探测前先记下时间和双方 IP，这样在大量事件里过滤会容易得多。这是实操里真会省时间的细节。

## 五、想照着做，按什么顺序验收

把原文的经验整理成检查单，比直接抄那三行 `interfaces` 有用：

1. 先验桥接确实在转发。 笔记本关 Wi-Fi 后能经 `br0` 拿到 Starlink 侧的网络，两个物理口不配 IP、`br0` 有管理地址。Debian 13 上先确认 `ifupdown` 已装，否则 `/etc/network/interfaces` 不生效。
2. 验 Suricata 真的在收包。 看 `stats.log`（默认每 8 秒一条）里的 `capture.kernel_packets` 与 `capture.kernel_drops`，或用 `jq 'select(.event_type=="stats")' /var/log/suricata/eve.json`。掉包不为零，后面所有结论都不可靠。
3. 用已知签名验整条链路。 Suricata 官方 Quickstart 推荐的 SID 2100498 就是这个用途；原文的 Python HTTP server + 假 root 文本是同一思路。这一步过了，才能说 EVE 输出和 EveBox 展示都正常。
4. 区分「没看到」与「没告警」。 查 `flow` 事件的 `alerted` 字段和 `flow_id` 关联，别只盯告警面板。
5. 给扫描行为写阈值规则，而不是等默认规则集。 `threshold: type threshold, track by_src, count N, seconds T`，或 `detection_filter` 配 `unique_on dst_port` 做垂直扫描检测；命名时写清实验用途，避免和别的测试互相绊响。
6. 满载压测再谈上线。 旁路 IDS 会静默丢副本；`kernel_drops` 才是决定这台盒子能不能守网的数字。若目标是阻断而非只告警，得改用 `AF_PACKET` 的 `copy-mode: ips` 由 Suricata 自己桥接，且必须移除内核网桥，两个物理口不给 IP。

## 六、事实边界

- 原文数据与命令（三行 `interfaces`、`nmap -sS -n -Pn --top-ports 100 --reason`、`196` 个 SYN flow / `100` 个目的端口 / `alerted=false`、`5.73M/7.80M` 约 `73.5%` 丢包、23:35:58 的 DNS 事件）均取自 2026-11-10 的 MakeUseOf 全文；该域名本机直连与 Chrome 均报 `ERR_HTTP2_PROTOCOL_ERROR`，正文经 `web_fetch` 取得。
- 作者那条本地规则的完整 rule 文本未在原文给出，只有「10 秒内 20 个 SYN、按源计数」的口径；本文引用的 `threshold` / `detection_filter` 语法与扫描示例来自 Suricata 官方文档，不是对作者规则的复原。
- `flow.alerted`、`flow_id` 关联、`kernel_packets` / `kernel_drops` 定义、SID 2100498、ET Open 更新频率、EveBox 部署形态，均取自各项目官方文档。
- 原文未披露 Zotac Nano 的具体 CPU / 内存型号与 Suricata 版本号，因此 73.5% 丢包率只对该次测试环境成立，不能外推到其它硬件。本文未实机复现。

## 七、结论

这篇动手文章真正教人的是三个层次的区分：转发不等于检测，看见不等于告警，装好不等于扛得住流量。

`alerted=false` 是最值得记住的一个字段 —— 它把「IDS 没工作」和「规则没覆盖」分开了。而 73.5% 的丢包提醒更冷一些：旁路 IDS 掉包时业务毫无感知，你以为在守网，其实只是偶尔抽样。作者最后把盒子留在实验台上，是对的；它的用途是让人亲手把这几层验证一遍，而不是接进家里那条正在跑 4K 视频的链路。

## Sources

- MakeUseOf（Gregory Gibson，2026-11-10）：<https://www.makeuseof.com/i-turned-an-old-pc-into-a-diy-hacker-detector-then-tried-to-hack-it/>
- Suricata 官方 Quickstart：<https://docs.suricata.io/en/latest/quickstart.html>
- Suricata EVE JSON Format（`flow.alerted` / `flow_id`）：<https://docs.suricata.io/en/latest/output/eve/eve-json-format.html>
- Suricata Thresholding Keywords：<https://docs.suricata.io/en/latest/rules/thresholding.html>
- Suricata Statistics（`kernel_drops`）：<https://docs.suricata.io/en/latest/performance/statistics.html>
- Suricata 官方论坛：AF_PACKET IPS 与 Linux 网桥不能共用：<https://forum.suricata.io/t/linux-bridge-and-af-packet-wont-drop-on-rule/4975>
- ET Open 官方下载说明：<https://rules.emergingthreats.net/OPEN_download_instructions.html>
- EveBox 文档：<https://evebox.org/docs/> ｜ GitHub：<https://github.com/jasonish/evebox>
- Suricata GitHub：<https://github.com/OISF/suricata> ｜ Debian 13 `interfaces(5)`：<https://manpages.debian.org/trixie/ifupdown/interfaces.5.en.html>
