# rspamd 把 46% 的合法邮件丢进了垃圾箱：一次从配置文件体系开始的排查

自建邮件的同学大概都经历过这个循环：发现某封该收到的信躺在 Junk 里，于是加一条域名白名单；过几天换个发件人，又漏一封，再加一条。白名单越写越长，误判照旧。

我的一台 Debian 12 邮件网关（postfix + dovecot + rspamd）就跑到了这个状态。真正促使我下决心排查的，是归档邮件的统计结果：**用户手动标过「非垃圾」的邮件里，有一半是服务端先扔进 Junk、用户再从客户端捞回来的**。

最后的结论有点意外——这不是「规则不够多」的问题，而是 **rspamd 的配置体系被破坏了一处，导致一整套检查形同虚设**；再加上一个**所有自建邮件都会踩的语义陷阱**。

先说排查结果：

| 指标 | 排查前 | 排查后 |
|---|---|---|
| 合法邮件被误判进 Junk | **294 / 643（46%）** | **40 / 643（6%）** |
| 真实垃圾被正确拦截 | 19 / 27 | 13 / 27 |
| 单封扫描耗时 | ~4136 ms | 611–1236 ms |

误判率降到七分之一，顺带把扫描耗时砍掉四分之三。下面把这套配置体系的每一层拆开讲清楚，再逐条说问题出在哪。

---

## 一、先把 rspamd 的配置文件体系理清

rspamd 的配置目录初看很乱——`/etc/rspamd/` 下有近四十个文件，还有 `local.d/`、`override.d/`、`modules.d/`、`scores.d/` 四套平行目录。但它的设计其实非常规整，核心只有一条规则：**发行版的默认值走 `*.conf` / `*.d/`，你的修改走 `local.d/` 或 `override.d/`**。

### 1. 顶层编排：`rspamd.conf`

这是唯一的入口，不定义具体参数，只负责把其它文件按顺序拼起来：

```
/etc/rspamd/rspamd.conf
 └─ .include "$CONFDIR/common.conf"        # 公共部分
     ├─ metrics.conf                        # metric 定义（分数聚合方式）
     ├─ actions.conf                        # 分数阈值 → 动作
     ├─ groups.conf                         # 符号分组 → 各 group 的分数表
     ├─ composites.conf                     # 复合规则（多个符号组合出新符号）
     ├─ statistic.conf                      # 贝叶斯统计后端
     ├─ modules.conf → modules.d/*.conf     # 各功能模块
     └─ settings.conf                       # 条件化配置（按用户/网络）
```

然后依次定义 `options`、`lang_detection`、`logging`、各 `worker`（normal / controller / rspamd_proxy / fuzzy / hs_helper）。每个段落都是同一个三段式结构：

```
options {
    .include "$CONFDIR/options.inc"                                          # 发行版默认
    .include(try=true; priority=1,duplicate=merge) "$LOCAL_CONFDIR/local.d/options.inc"   # merge 覆盖
    .include(try=true; priority=10) "$LOCAL_CONFDIR/override.d/options.inc"  # 严格覆盖
}
```

### 2. `local.d/` 与 `override.d/` 的区别（最容易踩的语义）

这两者的差异是**合并方式**，不是优先级高低：

| 目录 | 语义 | 行为 |
|---|---|---|
| `local.d/` | merge（`duplicate=merge`，priority=1） | **逐键合并**。只写你要改的键，其余保留默认值 |
| `override.d/` | strict override（priority=10） | **整段替换**。一旦存在，这个段落的默认值全部作废，只有你写的内容生效 |

这就是第一个大坑。`local.d/` 是安全的（写多少生效多少），而 **`override.d/` 里的文件必须自身完整**——它会把发行版定义的同名段落整个顶掉。

### 3. `scores.d/` 与 `groups.conf`：符号分数定义在哪

符号的分数不在 `metrics.conf` 里，而是按 **group** 组织在 `scores.d/`：

```
group "headers" {
    .include "$CONFDIR/scores.d/headers_group.conf"
    .include(try=true; priority=1; duplicate=merge) "$LOCAL_CONFDIR/local.d/headers_group.conf"
    .include(try=true; priority=10) "$LOCAL_CONFDIR/override.d/headers_group.conf"
}
```

`policies_group.conf` 就是其中一个 group，管的是 SPF / DKIM / DMARC / ARC 这一族符号：

```
"R_DKIM_ALLOW" { weight = -0.1; description = "DKIM verification succeed"; one_shot = true; groups = ["dkim"]; }
"R_DKIM_REJECT" { weight = 1.0; ... }
"R_SPF_ALLOW" { weight = -0.2; ... }
"DMARC_POLICY_ALLOW" { weight = -0.5; ... }
```

注意这同样是三段式 include——**所以它也有 `local.d/` 和 `override.d/` 变体**。

### 4. `actions.conf`：分数如何变成动作

这是整个评分体系的出口，也是理解后文的关键：

```
actions {
    reject = 15;      # 达到 15 分 → 拒收
    add_header = 6;   # 达到 6 分 → 加垃圾标记头
    greylist = 4;     # 达到 4 分 → 灰名单（软拒，要求重投）
}
```

### 5. `modules.d/`、`settings.conf`、`rspamd.local.lua`、`maps.d/`

- **`modules.d/*.conf`**：每个功能模块一段（`dkim`、`dmarc`、`spf`、`greylist`、`multimap`…），同样是 `local.d/` + `override.d/` 三段式。
- **`settings.conf`**：按条件切换策略，比如「来自内网的邮件只验 DKIM 不查 RBL」。
- **`rspamd.local.lua`**：自定义 Lua 规则的挂载点，通过 `rspamd_config.<SYMBOL> = { callback = ..., score = ... }` 注册符号。
- **`maps.d/` + `multimap` 模块**：外部数据列表（白名单域名、IP 段、SURBL 例外等）。

理清这五层之后，排查就有了路径：**先确认每个模块是否真的加载了，再确认符号是否真的有权重，最后才轮到调分数**。

---

## 二、问题一：一份被截断的 `options.inc`，让整套 DKIM 检查静默失效

### 症状

`rspamadm configtest` 报了一串可疑的警告：

```
$ rspamadm configtest
cannot enable arc plugin: dkim is disabled
cannot register delayed dependency DMARC_CHECK -> R_DKIM_ALLOW: destination R_DKIM_ALLOW is missing
cannot register delayed dependency WHITELIST_DKIM -> R_DKIM_ALLOW: destination R_DKIM_ALLOW is missing
cannot register delayed dependency WHITELIST_SPF_DKIM -> R_DKIM_ALLOW: destination R_DKIM_ALLOW is missing
...
syntax OK
```

注意最后一行是 `syntax OK`——**语法没问题，但依赖全断了**。这种「语法通过、功能静默缺失」的状态最危险。

### 根因

对比一下 `/etc/rspamd/options.inc` 和发行版原件 `/etc/rspamd/options.inc.dpkg-dist`：

```bash
$ wc -l /etc/rspamd/options.inc /etc/rspamd/options.inc.dpkg-dist
  25 /etc/rspamd/options.inc
  93 /etc/rspamd/options.inc.dpkg-dist
```

当前的 `options.inc` 只剩 25 行，有效内容就一句：

```
local_additions = "enable";
```

而原件第 16 行是：

```
filters = "chartable,dkim,regexp,fuzzy_check";
```

**rspamd 官方文档原文**：

> C modules provide the core functionality of Rspamd and are statically linked to the main Rspamd code. C modules are defined in `options.inc` with the `filters` attribute. The default configuration enables all C modules explicitly:
> `filters = "chartable,dkim,regexp,fuzzy_check";`
> **If no filters attribute is defined, all C modules are disabled.**

这些模块是**静态编译进 `librspamd-server.so` 的 C 模块**，不是 Lua 插件——所以它们在磁盘上找不到对应的 `.lua` 文件，肉眼检查完全看不出问题。验证一下二进制里确实有：

```bash
$ nm -D /usr/lib/rspamd/librspamd-server.so | grep -ci dkim
31
$ strings /usr/lib/rspamd/librspamd-server.so | grep "src/plugins/dkim_check.c" | head -2
./src/plugins/dkim_check.c:179
./src/plugins/dkim_check.c:596
```

能力都在，只是 `filters` 一空，**一个都没注册**。

### 连锁反应

DKIM 模块没加载，`R_DKIM_ALLOW` / `R_DKIM_NA` / `R_DKIM_REJECT` 这几个符号就不存在。而 rspamd 的配置是**声明式依赖**——凡是引用了不存在符号的规则，不会报错，只是永远不触发。实测这些规则全部失效：

| 失效的规则 | 本应作用 |
|---|---|
| `WHITELIST_DKIM` | DKIM 通过的白名单域给负分 |
| `WHITELIST_SPF_DKIM` | SPF + DKIM 双通过给强负分 |
| `WHITELIST_DMARC` | DMARC 对齐给负分 |
| `TRUSTED_NEWSLETTER_PASS` | 可信订阅邮件对冲 `FORGED_SENDER` |
| `DMARC_CHECK` | DMARC 策略检查 |
| `NO_AUTH_SPOOF` | 无认证伪造检测 |

顺手翻出同一份文件里丢掉的其它东西：

```
dns {
	timeout = 1s;
	sockets = 16;
	retransmits = 5;
}
local_addrs = [192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, fd00::/8, 169.254.0.0/16, fe80::/10];
```

`local_addrs` 丢失会让 `is_local()` 判断失真；`dns` 段落丢失意味着 RBL 查询用默认超时——实测这台机器 rspamd 日志里每天有 **1304 次 `query timed out`**（集中在 `asn6.rspamd.com` 和 DNSWL/URIBL 各 zone），既拖慢扫描，又让 `DWL_DNSWL_HI`（-3.5 分）这类白名单负分拿不到。

### 修复：用 `local.d/` 补回，不动原文件

`options.inc` 顶部自己就写着「请改用 `local.d/`」，而且 `local.d/` 是 merge 语义，补键最安全：

```
# /etc/rspamd/local.d/options.inc
local_additions = "enable";
filters = "chartable,dkim,regexp,fuzzy_check";

local_addrs = [192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, fd00::/8, 169.254.0.0/16, fe80::/10];

dns {
	timeout = 1s;
	sockets = 16;
	retransmits = 5;
}
```

重载后：

```bash
$ rspamadm configtest 2>&1 | grep -c "is missing"
0
$ rspamc counters | grep R_DKIM
| 494 | R_DKIM_ALIGNED  | -0.1 |
| 495 | R_DKIM_ALLOW    | -0.1 |
| 496 | R_DKIM_NA       |  0.0 |
| 497 | R_DKIM_PERMFAIL |  0.0 |
| 498 | R_DKIM_REJECT   |  1.0 |
| 499 | R_DKIM_TEMPFAIL |  0.0 |
```

扫描耗时立刻从 ~4136 ms 降到 611–1236 ms——**DNS 配置的收益比什么都直接**。

---

## 三、问题二：`override.d/` 的严格覆盖语义，漏掉了六个符号

DKIM 模块注册成功后，`configtest` 又报出新的一层：

```
symbol R_DKIM_ALLOW has no score registered, skip its check
symbol R_DKIM_REJECT has no score registered, skip its check
symbol R_DKIM_NA has no score registered, skip its check
...
```

符号存在，但权重是空的。查 `override.d/policies_group.conf`：

```
$ wc -l scores.d/policies_group.conf override.d/policies_group.conf
  158 scores.d/policies_group.conf
   28 override.d/policies_group.conf
```

`override.d` 版本只有 28 行，定义了 SPF、DMARC、ARC 三组，**唯独没有 DKIM**。因为它是 `priority=10` 的严格覆盖，发行版那 158 行里的 DKIM 段落被整个顶掉了。

这就是 `override.d` 的正确用法陷阱：**它适合「我完全接管这一组配置」，而不是「我只想改其中几条」**。后者应该用 `local.d/`。

补上六个符号（权重照抄 `scores.d/` 的默认值）即可。修复后 `WHITELIST_DMARC`（-7.0）和 `WHITELIST_SPF_DKIM`（-3.0）这两条之前完全没触发过的规则，在语料重扫中命中 858 次和 885 次。

---

## 四、问题三：`FORGED_SENDER` 对 ESP 的正常行为开枪

前两个问题修完，评分分布已经明显健康了，但还有一类邮件稳定误判：合规的批量邮件。

### 触发条件

`FORGED_SENDER` 的定义在 `forged_recipients.lua`：

```lua
-- Check sender
if smtp_from and smtp_from[1] and smtp_from[1]['addr'] ~= '' then
  local mime_from = task:get_from({ 'mime', 'orig' })
  if not same_mailbox((mime_from or E)[1], smtp_from[1]) then
    task:insert_result(symbol_sender, 1, ...)   -- +5.0
  end
end
```

一句话：**envelope sender（SMTP `MAIL FROM`）与 header `From` 不是同一个邮箱，就扣 5 分**。

问题是，**整个 ESP（邮件发送服务商）行业就是靠这个机制工作的**。所有主流 ESP 都用独立域做退信地址：

| header From | envelope sender | 服务商 |
|---|---|---|
| `news@customer.com` | `bounce-hash@bounce.customer.com` | 通用模式 |
| `publishing@email.mckinsey.com` | `bounce@email.mckinsey.com` | McKinsey |
| `jobs-noreply@linkedin.com` | `m-1but2tww...@bounce.linkedin.com` | LinkedIn |
| `notifications@github.com` | `bounces@sgmail.github.com` | GitHub |
| `author@debian.org` | `bounce-debian-list=user=freelamp.com@lists.debian.org` | 邮件列表 VERP |

这是 RFC 合规设计，不是伪造。但 `FORGED_SENDER` 对此一概 +5.0。

rspamd 确实内置了一个针对性的规则 `ENVFROM_PRVS`，注释写得很清楚：

```lua
--[[
    Detect PRVS/BATV addresses to avoid FORGED_SENDER
    prvs=TAG=USER@example.com       BATV 草案
    btv1==TAG==USER@example.com     Barracuda
    msprvs1=TAG=USER@example.com    Sparkpost
]] --
local re_text = '^(?:(prvs|msprvs1)=([^=]+)=|btv1==[^=]+==)(.+@(.+))$'
```

它只认这三种格式。实测在生产日志里 **0 次命中**——因为 `bounce@`、`sgmail.` 这些主流写法一个都不匹配。

### 量化：这类邮件到底是不是垃圾

在 3687 封归档邮件上做统计，把 envelope 域与 header 域的关系分类：

| envelope 域 vs header 域 | 数量 | 标签 |
|---|---|---|
| 不同但同源（子域关系） | **1785** | 全部是合法邮件，**零垃圾** |
| 同域 | 1577 | — |
| 不同且无关 | 69 | 混杂 |

1785 封「信封域与信头域不同但属于同一组织」的邮件，**没有一封是垃圾**。这个信号本身是高度可信的。

### 修复：不做域名白名单，做 relay 识别

之前的做法是维护 `whitelist_domains.inc`，每来一个新 ESP 加一行——这是**枚举式**方案，永远漏。

改成**特征式**：在 `rspamd.local.lua` 注册一个新符号，条件是「信封域与信头域同源 + 信封看起来是 relay 地址 + 至少通过一种认证」，然后对冲掉 `FORGED_SENDER` 的 5 分。

```lua
-- envelope 域与 header 域是否同源（含子域关系）
local function domains_related(env_dom, from_dom)
  if not env_dom or not from_dom then return false end
  env_dom, from_dom = env_dom:lower(), from_dom:lower()
  if env_dom == from_dom then return true end
  -- bounce.linkedin.com / linkedin.com
  if lua_util.str_endswith(env_dom, '.' .. from_dom) then return true end
  if lua_util.str_endswith(from_dom, '.' .. env_dom) then return true end
  return false
end

-- 信封是否是 relay/bounce 形态
local RELAY_LOCAL_RE = rspamd_regexp.create_cached(
  '^(?:bounce|bounces|mailer-daemon|postmaster|msprvs[0-9]*|prvs|btv[0-9]*|srs[0-9]*|' ..
  'return|no-?reply|noreply|newsletter|news|marketing|notifications?|updates?|' ..
  '[a-z0-9]+[=+][a-z0-9=+_.-]*=?|.*=bounces=)')
local RELAY_HOST_RE = rspamd_regexp.create_cached(
  '(?:^|\\.)(?:bounce[0-9]*|bounces|mailer|lists|list|mail|email|em[0-9]+|mta[0-9]*|' ..
  'smtp[0-9]*|send|sending|news|newsletter|marketing|mkt[0-9]*|campaign|sgmail|rsgsv|' ..
  'cmail|mcsv|createsend|mandrill|sparkpost|mailgun|sendgrid|amazonses|postmark|' ..
  'exacttarget|hubspot|braze|iterable|klaviyo|sailthru)\\.')

rspamd_config.RELAY_ENVELOPE = {
  callback = function(task)
    if not task:has_symbol('FORGED_SENDER') then return false end
    if not is_relay_envelope(task) then return false end
    -- 关键：必须至少通过一种认证，否则可能真是伪造
    return task:has_symbol('R_SPF_ALLOW')
        or task:has_symbol('DMARC_POLICY_ALLOW')
        or task:has_symbol('R_DKIM_ALLOW')
  end,
  score = -5.0,
  group = 'headers',
  description = 'Envelope is a bounce/relay address related to the From domain and the message authenticated',
}
```

覆盖率的离线评估结果：

```
=== offline rule coverage by label ===
   2426  ham:CAUGHT
     37  ham:MISS
    110  inbox:CAUGHT
```

合法邮件的信封形态覆盖率 **98.5%**（2426 / 2463）。而漏掉的 37 封里，绝大多数是 envelope 域等于 header 域的情况——**那些根本不触发 `FORGED_SENDER`，不需要这条规则**。

注意最后那个 `authed` 条件不是装饰：**没有它，真实伪造（信封域碰巧同源但完全无认证）也会被放过**。这道保险必须留。

---

## 五、问题四：一条 `force_actions` 规则，硬拒了合法邮件列表

这条是排查中**最值得单独拿出来讲**的，因为它的表达式看起来完全合理。

`force_actions` 模块允许无视分数直接执行动作。配置里有一条：

```
BLOCK_SPOOFED_LOCAL_DOMAIN {
    expression = "FORGED_SENDER & !DMARC_POLICY_ALLOW & !R_SPF_ALLOW";
    action = "reject";
    message = "Security breach: Spoofed internal domain identity rejected.";
}
```

名字叫「拦截伪造本地域」，`message` 说要防的是「内部身份伪造」。但看表达式——**它一个字都没提到本地域**。

它实际的含义是：*任何* envelope 与 From 不一致、且没有 SPF/DMARC 的邮件，直接拒收。

而 Debian 邮件列表的信封长这样：

```
From: Peter Pentchev <roam@ringlet.net>
Return-Path: <bounce-debian-devel=albertxu=freelamp.com@lists.debian.org>
```

`freelamp.com` 出现在信封里，但它是 **VERP 编码的投递标签**（`list名=收件人=域名`），不是身份声明。这条规则把它当成了「伪造本地域」，硬拒。

一条命令就能看出问题：

```bash
$ grep -c "forced: reject" /var/log/rspamd/rspamd.log
32
$ grep "forced: reject" /var/log/rspamd/rspamd.log | grep -oE "from: <[^>]*>" | sed 's/.*@//;s/>//' | sort | uniq -c | sort -rn
     22 lists.debian.org
      4 scoutcamp.bounces.google.com
```

32 次强制拒收里，22 次是 Debian 邮件列表。

### 修复：把「本地域」这个判断真的写进去

用 Lua 重新实现，这次**真的检查 header From 是否声称本地域**：

```lua
local LOCAL_DOMAINS = { "freelamp.com" }

local function spoofed_local_domain_cb(task)
  local hdr = task:get_from('mime')
  if not hdr or not hdr[1] or not hdr[1].domain then return false end
  local hd = hdr[1].domain:lower()

  local is_local = false
  for _, d in ipairs(LOCAL_DOMAINS) do
    if hd == d or lua_util.str_endswith(hd, '.' .. d) then is_local = true; break end
  end
  if not is_local then return false end          -- 关键：不是本地域，直接放过

  -- 声称是本地域，就必须自证
  if task:has_symbol('DMARC_POLICY_ALLOW') then return false end
  if task:get_user() then return false end        -- 已认证提交
  local ip = task:get_from_ip()
  if ip and ip:is_local() then return false end   -- 本机产生
  if task:has_symbol('R_SPF_ALLOW') then return false end
  if task:has_symbol('R_DKIM_ALLOW') then return false end
  return true
end

rspamd_config.SPOOFED_LOCAL_DOMAIN = {
  callback = spoofed_local_domain_cb,
  score = 8.0,
  group = 'headers',
  description = 'Header From claims a local domain but the message failed SPF, DKIM and DMARC',
}
```

另一个必须记住的细节：**`force_actions` 不认 `enable = false`**。它的规则加载循环只读 `action` 和 `expression` 两个字段：

```lua
for name, sett in pairs(opts.rules) do
  local action = sett.action
  local expr = sett.expression
  if action and expr then
    ...
```

所以想停用一条规则，**只能把整块注释掉**，加 `enable = false` 是无效的（这一点我实测确认过——配置检查仍然会注册那个 `FORCE_ACTION_BLOCK_*` 符号）。

---

## 六、问题五：Sieve 的 `X-Spam: Yes` 阈值语义

最后一个是投递层的。Dovecot 用一个全局 Sieve 脚本把垃圾邮件投进 Junk：

```sieve
require ["fileinto", "mailbox"];

if anyof (
  header :contains "X-Spam" "Yes",
  header :contains "X-Spam-Flag" "YES",
  header :contains "X-Spamd-Bar" "+"
) {
  fileinto :create "Junk";
  stop;
}
```

看起来没问题——「标记为垃圾就进 Junk」。但 `X-Spam: Yes` 是谁写的、什么条件下写？

在 `milter_headers.lua` 里：

```lua
routines['x-spam-status'] = function()
  local score = common['metric_score'][1]
  local action = common['metric_action']
  local is_spam
  if action ~= 'no action' and action ~= 'greylist' then
    is_spam = 'Yes'          -- ← 只要动作不是 no action/greylist
  else
    is_spam = 'No'
  end
  spamstatus = is_spam .. ', score=' .. string.format('%.2f', score)
```

而动作是由 `actions.conf` 决定的：

```
actions {
    reject = 15;      # 15 分 → reject
    add_header = 6;   # 6 分 → add header  ← 这里就已经是 "Yes" 了
    greylist = 4;
}
```

所以 **`X-Spam: Yes` 的真正阈值是 6 分，不是 15 分**。从 6 到 15 之间有整整 9 分的空间被压缩成了一个二元判断——只要达到 `add_header`，Sieve 立刻投进 Junk，用户永远看不到中间地带。

这也解释了为什么用户要反复标 `NonJunk`：**大量 6–8 分的订阅邮件、邮件列表、ESP 批量邮件，就卡在这个区间被一刀切**。

### 修复：用真实阈值

Sieve 支持关系比较，直接对着硬动作和分数栏判断：

```sieve
require ["fileinto", "mailbox"];

# X-Rspamd-Action: reject 是 rspamd 自己认为「确定是垃圾」的动作（≥15 分），
# rewrite subject 次之（≥12 分）。X-Spamd-Bar 每分一个 '+'，八个 '+' 即 ≥8 分。
if anyof (
  header :contains "X-Rspamd-Action" "reject",
  header :contains "X-Rspamd-Action" "rewrite subject",
  header :contains "X-Spamd-Bar" "++++++++"
) {
  fileinto :create "Junk";
  stop;
}
```

`X-Spamd-Bar` 的生成逻辑正好是「分数取整后重复 `+`」，可以直接当分数用：

```lua
local spambar
if score <= -1 then
  spambar = string.rep(local_mod.negative, math.floor(score * -1))
elseif score >= 1 then
  spambar = string.rep(local_mod.positive, math.floor(score))
else
  spambar = local_mod.neutral
end
```

---

## 七、怎么验证改对了（而不是拍脑袋）

改配置最怕「感觉好点了」。这套排查里最有价值的方法论是：**用归档邮件建带标签的回归集**。

Dovecot 的 Maildir 本身就是标注数据——用户把邮件放进哪个文件夹、打了什么关键字，就是标签。但这里有个**几乎所有人都会踩的坑**：

**`dovecot-keywords` 是每个文件夹独立的映射表**。同一个字母 `c`，在 INBOX 里是 `NonJunk`，在别的文件夹里可能是 `Junk`：

```bash
$ cat Maildir/dovecot-keywords
0 unknown-0
1 unknown-1
2 NonJunk      ← index 2
3 Junk
$ cat Maildir/.LinkedIn/dovecot-keywords
0 unknown-0
1 NonJunk      ← index 1，不同！
2 Junk
$ cat Maildir/.McKinsey/dovecot-keywords
0 NonJunk      ← index 0
1 Junk
```

`INBOX/cur/...:2,Sc` 里的 `c` 是 index 2 → `NonJunk`。**跨文件夹套用同一张表，会把用户「标记为非垃圾」读成「标记为垃圾」，结论完全反过来。**

第二个坑：**重扫会破坏 DKIM 签名**。Maildir 里存的是 LF 换行，而原始邮件是 CRLF，DKIM 是签在规范化的原始字节上的——重扫一遍，body hash 全部失效，`R_DKIM_REJECT` 全是假象。判断真实 DKIM 结论只能看生产日志：

```bash
$ grep -oE "R_DKIM_(ALLOW|REJECT|NA)\([-0-9.]+\)" /var/log/rspamd/rspamd.log | sed 's/(.*//' | sort | uniq -c
    459 R_DKIM_ALLOW
     62 R_DKIM_REJECT
     43 R_DKIM_NA
```

第三个坑：**重扫时 rspamd 会读到自己上次写进去的 `X-Spam: Yes`**，触发 `SPAM_FLAG` 规则再 +5.0。必须在扫描前把自己产生的头（`X-Spam*`、`X-Rspamd*`、`Authentication-Results`）剥掉，否则每一封都凭空多 5 分，回归数据全废。

最终对比（670 封可比对样本）：

| 判据 | 合法邮件误入 Junk | 真垃圾正确拦截 |
|---|---|---|
| 旧：`X-Spam: Yes`（≥6 分） | 294 / 643（46%） | 19 / 27（70%） |
| 新：`Bar≥8` 或 `reject` | 40 / 643（6%） | 13 / 27（48%） |

误判降到 6%。漏判看起来从 8 封涨到 14 封，但需要说明的是：那 40 封「误判」里，有相当一部分其实是**真垃圾**（取到 `BAYES_SPAM`、`PHISHING`、`VIOLATED_DIRECT_SPF` 等强特征）——只是用户没清理，留在 INBOX 里被当成了正样本。自动标注天然带噪，这个残差是标签问题，不是规则问题。

---

## 八、复盘：三条通用经验

**1. 「语法 OK」不等于「功能 OK」。**

rspamd 的 `configtest` 会对缺失的符号依赖给出 `destination ... is missing`，但那只是 warning，最后仍然打印 `syntax OK`。这类警告必须当成错误看。更隐蔽的是 `filters` 这种——它连警告都不给，只是整套 C 模块安静地不工作。**部署后第一件事应该是 `rspamc counters`，确认该出现的符号都出现了。**

**2. `local.d/` 是安全网，`override.d/` 是刀。**

`local.d/` 是逐键合并，写多少生效多少，鼓励使用。`override.d/` 是整段替换，**用它的那一刻你就要对整段内容的完整性负责**——包括发行版未来新增的项。凡是「只改其中几条」的场景，一律用 `local.d/`。

`FORGED_SENDER` 那条 `force_actions` 规则则提醒了另一面：**表达式的语义要和规则的意图对齐**。名字叫「拦截伪造本地域」，表达式却没有任何本地域判断——这种错位不会报错，只会在几个月后以「用户抱怨邮件列表收不到」的形式暴露。

**3. 阈值型配置要追到最后一层。**

分数 → 动作 → 邮件头 → Sieve，一条链上任何一层的阈值都和你想的不一样，最终行为就会出乎意料。`X-Spam: Yes` 这个头名字太有迷惑性，让人以为它代表「确定是垃圾」，实际上它只是「不是 no action」——**阈值是 6 分**。**每一条规则的效果都要追到用户实际看到的那个信箱为止**，中间任何一层用「应该没问题」带过，都会留下这种半年后才发作的坑。

---

## 附：本次改动清单

| 文件 | 改动 |
|---|---|
| `local.d/options.inc` | 补回 `filters` / `dns{}` / `local_addrs` |
| `override.d/policies_group.conf` | 补回 6 个 `R_DKIM_*` 符号权重 |
| `rspamd.local.lua` | 新增 `RELAY_ENVELOPE`、`SPOOFED_LOCAL_DOMAIN` |
| `local.d/force_actions.conf` | 注释掉 `BLOCK_SPOOFED_LOCAL_DOMAIN` |
| `/var/lib/dovecot/sieve/spam-to-junk.sieve` | 判据改为 `X-Rspamd-Action` / `Bar≥8` |

全部改动均可回滚，改动前都保留了 `.bak.<timestamp>` 备份。改完建议至少观察一个完整投递周期再清理备份。

最后重申那个最省事的教训：**排查配置类问题时，先确认「模块加载了吗」和「符号有权重吗」，再考虑「分数要不要调」**。这次五个问题里有三个属于前者——而它们造成的损失，远大于任何调分数的努力。
