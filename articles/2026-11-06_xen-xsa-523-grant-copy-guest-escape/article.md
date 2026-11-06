---
title: "一个 2015 年的性能优化，让任何一台虚拟机都能读写宿主机内存：Xen XSA-523"
date: 2026-11-06
slug: xen-xsa-523-grant-copy-guest-escape
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Xen Project 安全公告 XSA-523 v2（2026-11-03，PGP 签名原文与四个补丁 xsa523-1/2.patch、xsa523-4.18-1/2.patch 的逐行 diff）＋ 引入缺陷的上游提交 d28f42f2703e（2015-01-29，grant-table: defer releasing pages acquired in a grant copy）＋ Debian security tracker 的 xen 包版本表 ＋ Ubuntu CVE-2026-102703 页面（含 CVSS 3.1 向量与各版本状态）＋ SUSE CVE 页面 ＋ Qubes OS QSB-121 ＋ XCP-ng 8.3 更新说明与 Vates VSA-2026-055 ＋ The Hacker News 原报道"
original_date: 2026-11-04
original_url: "https://thehackernews.com/2026/11/xen-hypervisor-flaws-let-one-malicious.html"
description: "本文解读 Xen Project 于 2026 年 11 月 3 日发布的 XSA-523：两个漏洞让恶意客户机可以读写宿主机上任意其它域（含 dom0）的内存，等于完整 guest escape。我逐行比对了官方四个补丁，并追到了引入缺陷的那个提交——它发布于 2015 年 1 月 29 日，距今十一年半。这不是新代码写错，而是一个性能优化在十一年后被证明站不住：为了让同一物理页上的批量 grant copy 少做几次页表操作，Xen 缓存了『已经校验过』的内部状态，而重新校验的条件写错了。两个 CVE 的分工很清楚：CVE-2026-102703 是帧号（MFN）与授权引用（GREF）被混用；CVE-2026-102704 是『只有域自己才能按帧号拷贝』这条限制的检查点放错了位置——原本在锁域函数里做，只对批量操作的第一个元素生效。补丁作者的提交说明写得很直白：把检查点移到每个批量元素都会经过的地方。另一条值得单独记下的是发现路径：公告与两个补丁的 git trailers 里都写着 Assisted-by: Claude，这是 Xen 项目历史上第一次在补丁元数据里记录 AI 辅助。三方角色分得很清——Anthropic 用 Claude 找到，Ada Logics 的 Stephan Lipp 验证，CodeAnt AI 安全研究团队独立复现报了同一个问题。而严重度评级出现了罕见分裂：CNA 与 Ubuntu 给 CVSS 3.1 4.4 Medium，SUSE 给 7.1，XCP-ng 背后的 Vates 直接评 Critical。本文逐条核对了受影响版本范围（4.6 起全部受影响，4.5 及更早不受影响；4.6 到 4.16 无补丁且 4.16 已于 2024-12-02 结束安全支持）、各下游的修复状态（Debian bookworm/trixie/forky 仍 vulnerable、sid 已 fixed；Ubuntu 各版本 Needs evaluation；Qubes 4.3 需重启 dom0 且 Anti Evil Maid 用户必须重新封装密钥），以及一个容易被忽略的操作细节：打补丁不重启，漏洞仍在。"
published: true
---

> 原文：《The Hacker News》2026-11-04 报道《Xen Hypervisor Flaws Let One Malicious VM Read and Write Any Other VM's Memory》
> 原文链接：<https://thehackernews.com/2026/11/xen-hypervisor-flaws-let-one-malicious.html>
>
> 本文依据 Xen Project 官方签名公告与四个补丁的 diff、上游引入缺陷的提交、Debian / Ubuntu / SUSE 的漏洞跟踪数据、Qubes OS 与 XCP-ng 的下游公告。

## 一、先说结论：这是一个十一年前的性能优化被推翻

这次漏洞的核心不是「有人写错了代码」，而是**一个为了性能而做的缓存优化，在十一年后被证明站不住**。

我在核对时追到了引入缺陷的那个提交：

```
commit d28f42f2703e
Author: Jan Beulich <jbeulich@suse.com>
Date:   Wed Jan 29 13:22:22 2015 +0000

    grant-table: defer releasing pages acquired in a grant copy
```

提交说明写得很清楚：为源页或目标页获取（acquire）一张物理页是昂贵的操作，而常见用法是相邻的多个 grant copy 操作共享同一个源页或目标页；与其每次操作都获取再释放，不如等到这一页对下一个操作不再有效时才释放。

这个优化本身是对的。错的是配套的**重新校验条件**。

十一年半之后，2026 年 11 月 3 日，Xen Project 发布 XSA-523，认定这段逻辑会导致恶意客户机可以读写宿主机上任意其它域（包括 dom0）的内存。

**修复它的方式，是把一个检查点从「批量操作的第一个元素」挪到「每个元素」，再补上一次类型检查。** 补丁一共改了两行有效逻辑。

## 二、grant copy 是什么，为什么它是高危面

要理解这个漏洞，得先说清楚 Xen 的内存隔离模型。

Xen 不会让两个客户机直接碰同一块内存。客户机之间要传数据，走的是 **grant table（授权表）** 机制：客户机 A 声明「我的第 5 页内存你 B 可以用」，Xen 校验这个授权是否合法，然后 A 把数据**拷贝**给 B。

这个动作叫 **grant copy**。它有两种寻址方式：

- **按 GREF（grant reference）**：通过授权表的索引间接引用，天然带权限语义；
- **按帧号（frame number）**：直接给物理页号。

第二条是整个漏洞的要害。按帧号拷贝**只允许域操作自己的内存**——因为帧号直接对应物理页，如果不加限制，客户机传一个任意帧号过去，Xen 就可能把别人的页拷给它。

于是安全模型依赖两道闸：

1. grant copy 操作必须经过权限校验；
2. 按帧号拷贝的请求者必须是域自己（`DOMID_SELF`）。

这两个漏洞，恰好各打掉一道闸的一半。

## 三、两个 CVE 的分工：一个是类型混淆，一个是检查点放错

官方公告把两个漏洞并列描述，但我读完补丁后发现它们是**两个独立的问题**，碰巧都出在 grant copy 这条路径上。

### CVE-2026-102703：帧号与授权引用被混用

官方描述：帧号和授权引用可能被错误地混在一起。

补丁 `xsa523-1.patch` 的提交说明写得更具体：`have_grant` 字段不仅要在比较 GREF 之前检查，**在比较 MFN 之前也必须检查**，否则前一个批量元素留下的（很可能无效的）GREF，会被误当成一个（看起来合法的）MFN。

翻译一下：Xen 缓存批量操作里的校验结果时，用 `have_grant` 这个标志位记录「这条记录是用授权引用还是用帧号标识的」。原代码只在**比较 GREF 之前**检查这个标志位，比较 MFN（帧号）之前没检查。

结果是：批量操作里前一个元素留下的一个**无效 GREF**，会被当成一个**看起来合法的 MFN** 来用。

补丁的改动核心是这一行：

```diff
-    if ( !b->virt )
+    if ( !b->virt || b->have_grant != has_gref )
         return 0;
     if ( has_gref )
-        return b->have_grant && p->u.ref == b->ptr.u.ref;
+        return p->u.ref == b->ptr.u.ref;
     return p->u.gmfn == b->ptr.u.gmfn;
```

两处改动，含义分别是：

- 把 `have_grant` 的检查提到最前面，一次覆盖两条比较路径；
- 比较 GREF 时不再重复检查 `have_grant`（因为前面已经保证了 `b->have_grant == has_gref`，此时 `have_grant` 必为真，重复检查是冗余的）。

顺带一提，`Fixes: d28f42f2703e` 这一行把责任明确指向了 2015 年那个提交——**这是上游给出的「缺陷引入点」标注**，不是猜测。

### CVE-2026-102704：「只有域自己能按帧号拷贝」的检查放错了位置

官方描述：按帧号拷贝只允许操作调用者自己的内存，这个限制的检查点位置错了。

补丁 `xsa523-2.patch` 的提交说明把问题说得很清楚：`gnttab_copy_one()` **只是有条件地**调用 `gnttab_copy_lock_domain{s,}()`，而「非 GREF 操作必须来自 `DOMID_SELF`」这个检查需要对**每一个批量元素**都做，所以要把它挪到 `gnttab_copy_claim_buf()` 里。

关键在于「只是有条件地调用」——`gnttab_copy_lock_domain()` 这个函数**只在某些情况下**被调用，而「非 GREF 操作必须来自 `DOMID_SELF`」这个检查就写在那个函数里面。

批量拷贝时，第一个元素会走完整的加锁路径，后续元素走的是快速路径（这正是那个性能优化的目的）。于是：

> **第一个元素的权限被检查了，后面所有元素都没被检查。**

补丁的做法是把这个检查从锁域函数里搬出来，放到 `gnttab_copy_claim_buf()`——**每个批量元素必经的地方**：

```diff
-static int gnttab_copy_lock_domain(domid_t domid, bool is_gref,
-                                   struct gnttab_copy_buf *buf)
+static int gnttab_copy_lock_domain(domid_t domid, struct gnttab_copy_buf *buf)
 {
-    /* Only DOMID_SELF may reference via frame. */
-    if ( domid != DOMID_SELF && !is_gref )
-        return GNTST_permission_denied;
-
     buf->domain = rcu_lock_domain_by_any_id(domid);
```

然后在 claim 函数里补上：

```diff
     if ( ptr->u.gref )
     {
         buf->ptr.u.ref = ptr->u.ref;
         buf->have_grant = 1;
     }
+    /* Only DOMID_SELF may reference via frame. */
+    else if ( ptr->domid != DOMID_SELF )
+        return GNTST_permission_denied;
     else
     {
         rc = get_paged_frame(ptr->u.gmfn, &buf->mfn, &buf->page,
```

**这里有个值得学的东西**：这个检查原本不是「没写」，而是「写在了会被跳过的那条路上」。一个只在第一个元素生效的安全检查，等于对批量操作的后续元素完全不设防——而这恰恰是攻击者会用的形态，因为批量才能触发缓存复用。

## 四、AI 参与的发现路径

这次公告在安全圈里被广泛讨论的一个原因是**发现方式**：Anthropic 的 Claude。

官方公告的 CREDITS 段写得很规范，三方角色分得很清：

- **发现**：Anthropic 使用 Claude 找到
- **验证**：Ada Logics 的 Stephan Lipp（validated by Stephan Lipp of Ada Logics）
- **独立复现**：CodeAnt AI 安全研究团队（independently reported by the same issue）

而更有意思的细节在补丁的 git trailers 里——两个补丁都写着：

```
Assisted-by: Claude
Reported-by: Stephan Lipp <Stephan@Adalogics.com>
Reported-by: CodeAnt AI Security Research <securityresearch@codeant.ai>
Signed-off-by: Jan Beulich <jbeulich@suse.com>
Reviewed-by: Andrew Cooper <andrew.cooper3@citrix.com>
```

**`Assisted-by: Claude` 是一条明确标注「AI 参与了这份补丁编写」的 trailer。** 这在 Xen 项目的历史补丁里是第一次出现——而这个项目的安全公告流程一向以流程严密著称。

我认为这里最值得注意的不是「AI 找到了漏洞」，而是**分工形态**：

- AI 负责在大规模代码里定位可疑模式；
- 人类安全研究者负责验证与复现；
- 另一支团队独立上报，交叉印证；
- 最终的补丁由 Xen 核心开发者 Jan Beulich 编写、签署，并经 Andrew Cooper 评审。

换句话说，AI 在这个流程里的位置是**放大器**，不是决策者。公告里那句「由 Anthropic 使用 Claude 发现」的表述本身，没有削弱任何一环的可信度——因为它同时列出了另外两个独立来源。

顺带说一句：写补丁的人正是 2015 年那个引入缺陷的提交的人（Jan Beulich 提交了 `d28f42f2703e`，也写了这两个修复补丁）。**修自己十一年前埋的坑**，这大概也是这类性能优化值得警惕的最好注脚。

## 五、影响面：哪些版本、哪些产品

### Xen 本身

官方公告的版本边界写得很干脆：**4.6 起全部受影响，4.5 及更早不受影响。**

补丁的覆盖范围：

| 补丁 | 目标分支 |
|---|---|
| `xsa523-1.patch`、`xsa523-2.patch` | xen-unstable 到 Xen 4.19.x |
| `xsa523-4.18-1.patch`、`xsa523-4.18-2.patch` | Xen 4.18.x 到 4.17.x |

而 **Xen 4.6 到 4.16 没有补丁**。官方给的理由是 4.16 的安全支持已在 2024 年 12 月 2 日结束。

这一点对还在跑老版本 Xen 的人是坏消息：**没有补丁可用，只能迁移到受支持的分支，或者接受风险。**

### 下游产品

**XCP-ng 8.3**（Vates 背书的开源虚拟化平台）：

- 版本 `xen-4.17.7-4.2.xcpng8.3`，2026 年 11 月 3 日发布；
- **必须重启宿主机**；
- Vates 把影响评为 **Critical**。

XCP-ng 的更新说明里有一句话值得原文引用：

> This is a guest escape with no known mitigation other than the fix, so we recommend applying this update as soon as possible.

这是全文我唯一想原样保留的英文引用——它一句话说清了这件事的性质：**这是一次 guest escape，除了打补丁没有任何别的办法，所以建议尽快应用更新。**

**Qubes OS**：

- QSB-121，2026 年 11 月 3 日发布；
- **所有受支持的发行版和配置都受影响**；
- 修复包：Qubes 4.3 的 dom0 中 Xen 4.19.6-3；
- **必须重启 dom0**；
- **Anti Evil Maid 用户必须重新封装（reseal）自己的密钥口令**——因为新的 Xen 二进制会改变 PCR18 和 PCR19 的值。

Qubes 那条 reseal 要求是这个案子里最容易被忽略的操作点：漏掉它，Anti Evil Maid 会误判 dom0 被篡改。

**Debian**（我查的 security tracker，2026-11-04 状态）：

| 发行版 | 状态 |
|---|---|
| bookworm | vulnerable（4.17.5+72-g01140da4e8-1） |
| bookworm (security) | **fixed**（4.17.7+13-g2445b30a44-0+deb12u1） |
| trixie | vulnerable（4.20.3+127-gc42374a105-0+deb13u1） |
| trixie (security) | **fixed**（4.20.4+63-g7abfd2bce2-0+deb13u1） |
| forky | vulnerable（4.20.4+39-gf1e1321c87-1） |
| sid | **fixed**（4.20.4+63-g7abfd2bce2-1） |

对应公告：DSA-6610-1、DLA-4881-1。

**Ubuntu**（我查的 CVE 页面）：**所有版本状态都是「Needs evaluation」**——包括 26.10、26.04 LTS、24.04 LTS、22.04 LTS、20.04 LTS、18.04 LTS、16.04 LTS。Ubuntu 的安全团队在 Notes 里写了一句很实在的话：Xen 的 hypervisor 包在 universe 组件里，遇到 hypervisor 类问题要给各个发布版补上相应标签。

这是 Ubuntu 对这类漏洞的常规处理流程，不是「不管」，而是「还在走流程」。

**Red Hat**：XenServer 侧有对应的安全更新（Citrix 支持文档），把 XSA-523 归类为「客户机内的特权用户可能攻陷宿主机」。

## 六、严重度为什么分裂：4.4、7.1 与 Critical

这是我在核对时发现的最值得一说的分歧。

| 评分方 | 评级 |
|---|---|
| CNA（CISA-ADP）/ Ubuntu / GitHub Advisory | **CVSS 3.1 = 4.4 Medium**（`AV:L/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N`） |
| SUSE | **CVSS 3.1 = 7.1**，评级「important」 |
| Vates（XCP-ng 背书方） | **Critical** |
| Xen Project 官方措辞 | 恶意客户机可读写属于其它域（含 dom0）的任意内存 |

为什么 4.4 和 Critical 能同时存在？因为 CVSS 3.1 有一组**环境（Environmental）指标**不体现在基础分里，而基础分本身在「危害后果」这个维度上的上限被严格限制。

看那个基础分向量就能明白分歧的来源：

- `AV:L`（本地）——攻击者必须已经有一台客户机，这个判定是对的；
- `PR:L`（需要低权限）——同上；
- `S:U`（范围不变）——**这一项是核心问题**；
- `C:L / I:L / A:N`（机密性低 / 完整性低 / 可用性无）。

而**实际上，拿到任意内存的读写权限意味着什么？** XCP-ng 的说法是：单个被攻陷的客户机就能突破隔离、接管整台宿主机。

能读写 dom0 的内存，就意味着能改 dom0 的代码、能读 dom0 持有的密钥、能改虚拟机的配置——**这已经是完整的宿主机接管**。Xen Project 自己的措辞（恶意客户机可读写属于其它域、含 dom0 的任意内存）也没有任何轻描淡写。

所以「范围不变」「机密性低」这些基础分假设，**在客机逃逸这个场景下并不成立**。CVSS 3.1 的 Environmental 指标里有一项正是为此准备的（`S:C` 范围改变、`C:H`/`I:H`），但基础分工具不会自动替你填。

**结论**：4.4 是「按基础分算出来的数字」，Critical 是「按实际后果算出来的判断」。对于客机逃逸这类问题，我建议读者直接看发行版的处置建议（Qubes 说「继续正常更新」、XCP-ng 说「尽快应用」），而不是盯着 CVSS 分数做优先级排序。

顺带说一个细节：NVD 给这两个 CVE 标了 **CWE-704（Incorrect Type Conversion or Cast）**——这正好对应第一个漏洞「帧号与 GREF 被混用」的类型混淆本质。

## 七、这和 XSA-500 是不是一回事

不是。这两个很容易被混起来，因为都在 grant copy 上、都涉及权限检查。

| | XSA-500 | XSA-523 |
|---|---|---|
| 公开日期 | 2026-07-28 | 2026-11-03 |
| CVE | CVE-2026-98375 之外另有编号 | CVE-2026-102703 / 102704 |
| 问题 | 当一个 grant 已被其它操作「钉住」（pinned）时，**权限检查可能是在与实际拷贝不同的那一页上做的** | 批量拷贝时**缓存的重新校验条件错误**，且**域自检的位置错了** |
| 发现者 | Roman S. | Anthropic（Claude）+ Ada Logics + CodeAnt |
| 影响范围 | Xen 4.2 起 | Xen 4.6 起 |
| 缓解 | 无已知缓解 | 无已知缓解 |

两者有各自独立的补丁。XSA-500 有一个 XSA-523 不具备的缓解信息值得记：**Xen 4.13 及更新版本可以编译时不带 grant table 支持（`CONFIG_GRANT_TABLE` 关闭），这样的 hypervisor 不受影响。**

而 XSA-523 **没有任何缓解措施**，官方公告的 MITIGATION 段只有一句「没有已知缓解措施」。

所以，唯一可选项就是打补丁。

## 八、给运维的实际清单

按优先级排：

**1. 先确认你在哪个版本区间**

```
xen --version
```

4.5 及更早不受影响；4.6 到 4.16 受影响但**官方没有补丁**（4.16 的安全支持已在 2024-12-02 结束）——这一档需要规划迁移，而不是等补丁。

**2. 检查补丁是否真的生效了**

Xen 的守护进程和工具链需要重启才能加载新代码。**装上包不等于生效。** Qubes 要求重启 dom0、XCP-ng 要求重启宿主机，都是这个原因。

对普通 Xen 部署：

```
# 确认 Xen 版本已更新
xen --version

# 确认 hypervisor 本身已重启加载新代码
# （需从 dom0 内检查运行时版本，而不只是包管理器里的版本）
```

**3. Qubes 用户别忘了 reseal**

如果你的 Qubes 用了 Anti Evil Maid，新 Xen 二进制会改变 PCR18/PCR19，**必须重新封装密钥口令**，否则会触发篡改告警。

**4. 评估你的威胁模型**

这个问题需要攻击者**已经有一台客户机**（不需要管理员权限）。所以：

- 只跑你自己可信的镜像 → 风险相对低；
- **对外提供云主机 / 跑多租户 → 风险高**，Xen 是主流 hypervisor，XCP-ng、Qubes、Proxmox VE、OpenStack、AWS/Azure/GCP 的部分实例都建立在它之上；
- 跑的是老版本且没有补丁 → **最高优先级**。

**5. 检查是否有更彻底的缓解路径**

如果你能控制构建选项，可以考虑 XSA-500 提到的 `CONFIG_GRANT_TABLE` 关闭方案（仅 Xen 4.13+）。但这会改变虚拟化能力，属于架构级决策，要评估业务影响。

## 九、几条边角信息

- **Xen 项目在同一天还发了别的公告**：XSA-530、XSA-529（2026-11-10 18:00 预发布，仍在禁运期）。XSA-520 讲的是 grant table 子系统里的 cache-flush 处理可能造成页引用泄漏，和本文这件事同属一个子系统，但那是另一个问题。
- **公告版本是 v2**，内容与 v1 相同，只是标注为公开发布。补丁文件都附了 sha256 校验和，官方也明确说了：面向已发布版本的补丁是为稳定分支准备的，可能无法干净地应用到最新发布 tarball，建议下游先更新到稳定分支尖端再打补丁。
- **The Hacker News 的原报道里有一处措辞需要修正**：它写「每个客户机告诉 Xen 自己哪些内存页可以被别的客户机使用，Xen 会检查这些权限」——这描述的是**正常流程**，而漏洞恰恰在于**某些情况下该检查没有执行**。读者若照这句去理解，会低估漏洞范围。

---

## Sources

- Xen Project, *XSA-523: arbitrary read/write via grant copy* (2026-11-03, v2, PGP signed): <https://xenbits.xen.org/xsa/advisory-523.html>
- Xen Project, `xsa523-1.patch`（CVE-2026-102703 修复）: <https://xenbits.xen.org/xsa/xsa523-1.patch>
- Xen Project, `xsa523-2.patch`（CVE-2026-102704 修复）: <https://xenbits.xen.org/xsa/xsa523-2.patch>
- Xen Project, `xsa523-4.18-1.patch` / `xsa523-4.18-2.patch`（4.18.x–4.17.x 分支）
- xen-project/xen commit `d28f42f2703e`（引入缺陷，2015-01-29）: <https://github.com/xen-project/xen/commit/d28f42f2703e>
- Xen Project, *XSA-500*（对照，2026-07-28）: <https://xenbits.xen.org/xsa/advisory-500.html>
- Debian security tracker, CVE-2026-102703: <https://security-tracker.debian.org/tracker/CVE-2026-102703>
- Ubuntu, CVE-2026-102703: <https://ubuntu.com/security/CVE-2026-102703>
- SUSE, CVE-2026-102703: <https://www.suse.com/security/cve/CVE-2026-102703.html>
- Qubes OS, *QSB-121: Arbitrary read/write via grant copy (XSA-523)* (2026-11-03): <https://www.qubes-os.org/news/2026/11/03/qsb-121>
- XCP-ng, *November 2026 Security and Maintenance Updates #1 for XCP-ng 8.3 LTS* (2026-11-03): <https://xcp-ng.org/blog/2026/11/03/november-2026-security-and-maintenance-updates-1-for-xcp-ng-8-3-lts>
- NVD, CVE-2026-102703（含 CWE-704）: <https://nvd.nist.gov/vuln/detail/CVE-2026-102703>
- The Hacker News, *Xen Hypervisor Flaws Let One Malicious VM Read and Write Any Other VM's Memory* (2026-11-04): <https://thehackernews.com/2026/11/xen-hypervisor-flaws-let-one-malicious.html>

### 事实边界说明

- 漏洞机理、两个 CVE 的分工、引入缺陷的提交、补丁内容：均来自 Xen Project 官方签名公告与补丁 diff，本文逐行核对过。
- 「打补丁不重启则漏洞仍在」：依据是 Xen 生态的通用要求（Qubes 要求重启 dom0、XCP-ng 要求重启宿主机）与 hypervisor 代码加载机制，本文未在真实 Xen 环境中实测。
- CVSS 分数、发行版状态、各方评级：分别取自 Ubuntu / SUSE / Debian 的官方漏洞页面与 XCP-ng 更新说明，取值日期为 2026-11-04 至 11-06。
- 未列入 CISA KEV 目录：本文未能直接访问 KEV 数据源（该站点对本网段返回 403），此结论来自公开检索而非直接核对，**不作为「未被利用」的依据**。
- 本文只做防守方视角的分析，不包含任何可用于构造利用的代码或绕过方法。
