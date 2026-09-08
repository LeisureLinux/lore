# Broadcom 下架 VDDK 下载：离开 VMware 的退路被堵，企业需要哪些 Plan B？

> **一句话总结**：2026 年 9 月 7 日，Broadcom 悄然停掉 VMware VDDK 的公开下载——这个"不起眼"的开发包是 Azure Migrate、Red Hat MTV、Nutanix Move、virt-v2v 等几乎所有迁移工具的底层命脉。没有公告、没有替代方案，只有支持工单里一句"VDDK 不再提供使用或下载"。这本质是一次针对"迁出路径"的供应商锁定动作，企业该把 Plan B 提上日程了。

2026 年 9 月 7 日，Broadcom 停止提供 VMware VDDK（Virtual Disk Development Kit，虚拟磁盘开发套件）的下载。原下载链接全部返回 404，没有过渡通知、没有弃用公告、没有替代工具说明——只有 Reddit 上客户贴出的 Broadcom Customer Care 回复，白纸黑字写着 VDDK "no longer available for use or download"。

对正在用 VMware、或者正打算离开 VMware 的企业来说，这不是一次普通的下载页维护，而是一记打在"退路"上的闷棍。

## 一、VDDK 为什么是命脉

VDDK 本质是 VMware 提供的一套 C 语言库 + 工具，让第三方软件能直接读写 VMDK 虚拟磁盘、通过 NBD（Network Block Device）传输数据。

它"小众"，却是下面这些迁移工具的核心依赖：

| 工具 | 用途 | 对 VDDK 的依赖 |
|------|------|----------------|
| Microsoft Azure Migrate | 无代理迁移 VMware VM 到 Azure | appliance 上需安装 VDDK |
| Red Hat MTV | 迁移到 OpenShift Virtualization | 拉取 VMDK 靠 VDDK |
| Nutanix Move | 迁移到 AHV | 需要 VDDK 7.0.3.1 / 8.0.3.2 |
| virt-v2v | 转换到 KVM / libvirt | 读 VMDK 靠 VDDK |
| nbdkit | 通用块设备服务 | VDDK 插件 |

换句话说，VDDK 是 VMware 生态"迁出"路径上的公共组件。砍掉它，等于在所有迁离工具的前面设了一道路障。

## 二、时间线：这不是事故

关键节点（2026 年 8 月底～9 月初）：

- **8 月 25 日**：ShapeBlue 在 VMware-to-KVM 迁移文档里发现，引用的 VDDK 下载页开始报错；测试 VDDK 8 和 VDDK 9 的版本特定 URL 全部不可用。
- **8 月 27 日**：Red Hat 发布支持文章《Unable to download VMware VDDK images for MTV》，客户开始收到 "not found" / "access denied"。
- **8 月底**：Microsoft 更新 Azure Migrate 文档，新增警示——若拿不到 VDDK，请改用 agent-based（基于代理）迁移。
- **9 月 1 日**：Platform9 的 vJailbreak 项目发文，确认传统"VDDK + NBD"迁移路线受阻。
- 同期，Reddit 上的支持工单证实了"故意移除"，有消息称 VDDK 被移入了 VMware Technology Alliance Program（TAP），需要合作伙伴关系与支持权限才能获取。

几个信号叠加，性质已经很清楚了：**没有官方公告、没有弃用声明、没有替代工具**，再加上工单里的"故意为之"，这不是网站故障，而是一次有计划的渠道收缩。

## 三、点评：一边降门槛，一边堵退路

最值得玩味的是时机。

就在同一时期，Broadcom 在 VMware World 上把 **vSphere Standard 版**带了回来——这是给中小企业的"挽留价"：降门槛、降低授权成本，安抚被订阅制涨价吓跑的 SMB。

而另一只手，把 VDDK 从公开渠道拿掉——专门卡住"迁离"这个动作。

一个降、一个堵，策略指向非常一致：**让你留下更容易，让你离开更麻烦**。这已经不是普通的商业策略，而是教科书级的 vendor lock-in（供应商锁定）信号。

我的点评有三层：

1. **合法但失信**。VDDK 是 Broadcom 的专有软件，它有权决定分发方式。但"不公告、不解释、直接 404"，与早年 VMware 的开放生态形成鲜明对比。Red Hat 都只能无奈地让客户"自己找 Broadcom 要"——因为它无权托管和再分发。

2. **伤敌一千自损八百**。VDDK 不止迁离工具在用，大量第三方备份/灾备产品同样依赖它。堵住 VDDK，等于同时削弱了围绕 VMware 的整个第三方工具生态。信任一旦崩塌，反而可能加速客户转向不依赖 VDDK 的方案（比如 Proxmox）。

3. **最受伤的是"还没走成"的人**。已经迁完的无所谓，铁了心留下的也无所谓，真正被卡住的是那些正在评估、正在迁移、工具链已经搭好一半的企业——他们现在进退两难。

## 四、影响面：谁在遭殃

- **VMware 用户**：任何正在用 Azure Migrate / MTV / Nutanix Move 迁离的团队，迁移计划可能当场搁浅。
- **非 VMware 虚拟化生态**：KVM、AHV、Hyper-V、OpenShift 的"迁入"工具链集体受牵连——VDDK 卡的是 VMware 这一侧，砸的却是竞争对手的迁入门槛。
- **备份与灾备**：依赖 VDDK 的第三方备份/恢复产品，其 VMware 支持能力同样被削弱。

## 五、Plan B：企业现在该准备什么

按场景拆解，把"退路"提前铺好：

### 1. 走 Azure Migrate 的
短期直接切换到 **agent-based migration**（基于代理的迁移），不依赖 VDDK。代价是多装 agent，但路径是通的。

### 2. 走 Red Hat MTV / OpenShift 的
短期只能**联系 Broadcom 支持碰运气要副本**；长期盯 Red Hat 正在研究的 **storage copy offload**（存储复制卸载）——但这条路依赖底层存储阵列能力，不是每家都有。

### 3. 走 Nutanix Move 的
要么通过 **TAP 计划**拿合法 VDDK 副本，要么**检查底层存储是否支持存储级复制**，绕过 VDDK。

### 4. 走 Platform9 的
它提供了两条不依赖 VDDK 的路：**storage assisted migration**（存储辅助迁移）+ 在 VMware 内起 **proxy VM** 直连 VM 存储的 accelerated 选项。

### 5. 通用、最省事的：Proxmox import utility
**VMware → Proxmox 的迁移完全不受影响**，因为 Proxmox 内置的导入向导不依赖 VDDK，能直接处理 VMDK。无论是 homelab 还是生产，这条路都通。

### 6. 战略层的三条建议

1. **别把迁移路线锁死在单一工具上**。评估至少两条不依赖 VDDK 的路径，一条当主、一条当备。
2. **现在就验证你的 VDDK 副本**。如果之前下载过，先确认版本、留档；如果是采购的第三方工具，找供应商确认其 VDDK 来源是否合法可持续。
3. **把"迁出能力"写进供应商评估**。这次教训的核心是：一个平台的开放度，决定了你将来离开它的成本。选型时把"迁移生态是否开放"纳入打分。

## 结语

VDDK 下架这件事，技术层面只是一次下载渠道的关闭，但战略层面是一声警钟：**企业对自己基础设施的"退出权"，正在被供应商一点点收回。**

对正在用 VMware 的企业，现在不是恐慌的时候，而是把 Plan B 从"以后再说"提上日程的时候。迁移路线要铺两条，VDDK 依赖要能替代，选型要算清"离开成本"——因为这一次，Broadcom 用行动告诉市场：留下很容易，离开，得先过我这关。

---

*本文基于 Virtualization Howto 2026-09-07《Leaving VMware Just Got Harder After Broadcom Pulled VDDK Downloads》（作者 Brandon Lee）翻译解读，并补充点评与企业应对建议。*
