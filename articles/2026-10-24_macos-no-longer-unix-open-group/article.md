# macOS 不再是 Unix：Open Group 注册表里，Apple 的条目空了

> **2026 年 10 月，Open Group 的 UNIX 认证产品注册表上 Apple/macOS 消失了。这不是操作系统代码的「衰退」通知，而是一个自愿、有续费门槛的商标/合规产品的到期与注销。**

## 先说结论

1. **macOS 不再是 Open Group 官方注册的 UNIX® 产品**。截至 2026 年 10 月 24 日，主注册表 `https://www.opengroup.org/openbrand/register/` 和 `UNIX 03` 专用页 `/openbrand/register/xy.htm` 都已没有 Apple/macOS 条目；列表上剩下的包括 IBM（AIX/z/OS）、HPE（HP-UX）和 The SCO Group（UnixWare/OpenServer）等。
2. **官方没有公告、没有新闻稿、没有 ceremony**。The Open Group 与 Apple 都未发布公开说明； disappearance 因各技术媒体转引与 Wayback 对比而被 noticing。
3. **现有 macOS 26 Tahoe 的 UNIX 03 证书页面仍能打开**，并显示 **Registered on: 29-Aug-2025**、**Next renewal date: 29 Aug 2026**、环境分为 Apple silicon 与 Intel 两类。在证书有效期字段与官方注册表之间，官方网页目前自相矛盾。
4. **macOS 仍然是 Darwin/XNU，仍然大量继承 BSD 与 POSIX 语义**。「Unix 认证」与「Unix-like」/「BSD derivative」不是一回事。App 与脚本不会因为注册表消失而突然失灵。
5. **这次变化改变的首先是商标与合规身份，不是内核/ABI/API**。Apple 是否继续把自己称作 Unix，会从 legal claim 退到市场/历史称谓，尤其是在 macOS 27 附近/version branding 上。

## Open Group 注册表上到底少了什么

Open Group 控制 UNIX® 商标。只有通过 Single UNIX Specification 测试并继续维持认证的系统，才有资格被列在官方注册表里，并使用该商标/Mark。

注册表公开显示内容，本轮变化发生在 2026 年 10 月 7 日到 11 日之间：

- 10 月 7 日 Wayback capture：注册表里仍能看到 macOS 26 Tahoe 的 Apple Silicon 与 Intel 条目；
- 10 月 11 日及之后的抓取：Apple 条目从主注册表消失；
- 10 月 24 日复查：主注册表只显示 IBM、HPE、SCO；
- UNIX 03 专用页同样不再显示 Apple。

官方品牌证书详情页仍能打开，并保留两个注册：

- `Apple Inc.`，`macOS version 26.0 Tahoe`，on Apple silicon-based Mac computers，`Registered on: 29-Aug-2025`，`Next renewal date: 29 Aug 2026`，证书 `1223p.pdf`；
- `Apple Inc.`，`macOS version 26.0 Tahoe`，on Intel-based Mac computers，同样日期，证书 `1224p.pdf`。

把这两页与 `/openbrand/register/` 的空白对照，可以看出一个事实：**注册表的主列表已经不认它了，但证书详情页还没被完全清理**。Open Group 网站并不一致。

因此，macOS 26 Tahoe 不是"从未注册"过；相反，它在 2025 年 8 月 29 日仍被注册成 UNIX 03。它 missing 的是**后续维持（renewal / 版本 lineage）**。

## 我们把相关认证材料保存下来了

这次研究把 Open Group 上与 macOS 相关的注册/证书材料落到了仓库里，避免网页再变化后资料丢失。保存文件：

- `assets/cert-macos-26-tahoe-apple-silicon-unix03.png` 与同名 `.pdf`
- `assets/cert-macos-26-tahoe-intel-unix03.png` 与同名 `.pdf`
- `assets/og-unix-register-main-2026-10-24.png`（主注册表当前状态）
- `assets/og-unix03-register-2026-10-24.png`（UNIX 03 专用页当前状态）

证书 PDF 文本包含以下信息（摘录）：

```text
Open Brand
Certificate

This is to certify that

Apple Inc.
has entered into a Trademark License Agreement
with The Open Group Limited in accordance with which
the following are registered under the Open Brand Program

UNIX® 03
Registration No: P1223

macOS version 26.0 Tahoe
on Apple silicon-based Mac computers

Date of first issue: 29 August 2025
Next renewal date: 29 August 2026

License No: L3064
```

Intel 那份对应 `P1224`，其余字段同理。

这个证书值得读一遍，因为它把注册制的本意写得非常清楚：它是 trademark license，不是"操作系统技术评审 opinion"。Open Group 不宣布 macOS 是否是 Unix-like，它只确认某版本 OS 的 specified conformance + legal licensing 续期情况。

## macOS 是从什么时候变成"Unix 的"？

Apple 的 Unix 认证 historically 与 macOS/Unix 品牌化相联系，可追溯到 2007 年 Leopard 时代。macOS X/OS X/macOS 在 UNIX 03 体系下持续注册，版本 schedule 与 cert cycle 有 lag：

- 早期：Mac OS X 10.5 Leopard (2007) 通过 UNIX 03；
- macOS Tahoe 26.0 (2025-08-29) 是目前已 certified 的版本；
- 未见 macOS 27 之 certified entry。

Open Group 的 UNIX 03 对应 SUSv3（2004 / POSIX.1-2001 with TC1 / 等）。如果用 "V7" 与 AIX 7.2 TL5+ 对标，macOS 从未有过最新商标版本的 claim。因此 macOS 的 "Unix 证书"本身就是 "UNIX 03 认证" 的 level，不是 "最新 certified UNIX"。

## 这一变化不意味着什么

- **内核未一夜之间改变**：Darwin/XNU 仍然是 BSD-derived Unix-like kernel，API/POSIX 语义没被注册表决定。
- **你的脚本不会突然失败**：`bash`、`make`、`sed`、`find`、`awk`、shell POSIX 语义不会因为 Open Group register 从 explicit listing 中删一条而变化。OS-level features 由 Darwin 实现。
- **libc/Unix 工具链不受影响**：macOS `usr/include`、`sys`、`libc`、syscall stubs remain。
- **软件兼容性不由 trademark certificate 定义**：development and enterprise support 也不会因注册表空缺而直接 terminate。

## 这一变化真正意味着什么

1. **法律/营销 angle**：Apple 不再能以该注册表作为 "UNIX®"- certified claim
2. **compliance/procurement angle**：在重视 POSIX certified 的 contexts（政府/enterprise procurement、secure deployment benchmarks），macOS 26 的 certification 可能不再被 renew
3. **archive/version continuity angle**：这标志着 Apple 的 long-standing "macOS 是 certified Unix" 的 era 的 closure（likely）；OS news interpretation
4. **cost/admin angle**：Open Group certification 涉及 test suites、fee、reversion validation、vendor cooperation。Apple 通常 discretion

## 为什么 Apple 可能不续？

我们不能确认真正原因，因为没有官方声明。合理的 hypotheses：

- **diminishing value**：macOS 的 Unix branding historically 用于 enterprise credibility, but macOS 早已以 Apple 生态、dev tools、consumer UX 为 selling point
- **release cadence/version churn**：每 version 需要 renew，且 26 等 certification lag。macOS 27 可能尚未送测
- **cost/benefit**：cert process & license fees may not offset marketing benefit
- **trademark vs accuracy gap**：" certified" vs "Unix-like" gap。Apple can simply say it's UNIX-based or BSD-derived without relying on trademark

None of these are verified.

## 关于 Open Group 注册表不一致的几点

- 无 expiry date in certificate；"Next renewal" gives date
- register page contradiction：Apple brand detail remains even though register excludes it
- no public announcement of delisting, per observers
- result：reporting has to rely on page diff + Wayback, leading to debate of "still Unix / not Unix?"

## 两个技术 distinction that matter

1. **Certified UNIX vs Unix-like**
   - "Unix-like" is technical description of ancestry/compatibility.
   - "UNIX®" is legal trademark term controlled by Open Group.
2. **UNIX 03 vs UNIX V7**
   - macOS was at 03 (SUSv3). Only one OS currently conforms to latest V7：AIX 7.2 TL5+.
   - Other commercial Unix (HP-UX, Solaris-ish/OpenIndiana/illumos) mostly 03 or not certified at all.

So "macOS was never the most certified Unix to begin with"; it was at the 2003 standard, and Apple never claimed V7.

## macOS 与 Linux identity 的旁注

Amusing potential tie-in：Linux is not certified UNIX in general, but runs Unix-like workloads; macOS was certified. The Open Group removal of macOS highlights that certifications can lapse due to business decisions even as code remains Unix-like. `ios-Linuxkit` runs on ARM64 Linux userland; this is another "Unix identity" angle but unrelated to cert. Keep focus: trademark status != OS ancestry.

## Sources

- Open Group Register: https://www.opengroup.org/openbrand/register/
- UNIX 03 register: https://www.opengroup.org/openbrand/register/xy.htm
- Apple silicon certificate page: https://www.opengroup.org/openbrand/register/brand3725.htm
- Intel certificate page: https://www.opengroup.org/openbrand/register/brand3720.htm
- Apple silicon cert PDF：https://www.opengroup.org/openbrand/certificates/1223p.pdf
- Intel cert PDF：https://www.opengroup.org/openbrand/certificates/1224p.pdf
- OSnews：https://www.osnews.com/story/146203/apple-stops-pretending-macos-is-unix (2026-10-20)
- Authon blog：https://blog.authon.dev/is-macos-still-unix-open-group-registry
- allthenews：https://www.allthenews.today/item/apple-macos-silently-removed-from-official-unix-registry
- newzino：https://newzino.com/story/apple-macos-silently-removed-from-official-unix-registry-425ab4

Sources include media interpretation; official Open Group was silent as reported.

## 附录：时间线

- 2007：macOS 以 UNIX 03 认证进入 Open Group 注册表
- 2025-08-29：macOS 26.0 Tahoe（Apple Silicon + Intel）注册 UNIX 03，下次续期 2026-08-29
- 2026-10-07：Wayback 仍含 Apple/macOS 条目
- 2026-10-10/11：主注册表与 UNIX 03 专用页移除 Apple 条目
- 2026-10-24：复查仍无 Apple 条目，但证书详情页仍可打开

---

（说明：本文仅引用公开网页/机构材料与第三方报道；所有 "Apple 不再认证" 结论均基于网页注册表对比，因 Open Group 尚未公开声明。）
