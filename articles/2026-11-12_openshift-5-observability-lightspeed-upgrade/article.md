---
title: "OpenShift 5 可观测性：AI 会自动排障，但每个改动都要人点确认"
date: 2026-11-12
slug: openshift-5-observability-lightspeed-upgrade
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：Red Hat 官方博客《Guide to observability with Red Hat OpenShift 5》（Simon Herlofsson、Eric Evans、Vanessa Martini、Jamie Parker、Roger Florén，2026-11-11，6 分钟阅读）全文 ＋ 官方文档 OpenShift Container Platform 4.16《About Observability》组件清单 ＋ 本站 2025-02 同类《Guide to observability with Red Hat OpenShift 4.18》对照 ＋ Red Hat build of OpenTelemetry / OpenShift AI 官方文档中 operator 分工说明"
original_date: 2026-11-11
original_url: "https://www.redhat.com/en/blog/guide-observability-red-hat-openshift-5"
description: "本文解读 Red Hat 官方《OpenShift 5 可观测性指南》，指出标题叫「指南」而实质是一份版本变更清单，并把厂商宣传口径与可验证的配置事实分开。三大 AI 能力分层：自主排障（配置 Alertmanager 适配器后告警触发即自动调查、生成诊断与修复计划进入决策队列，所有状态变更需管理员显式批准、在沙箱 Pod 内按动态 RBAC 执行、修复失败直接升级给人，属技术预览，需 Lightspeed operator 2 + OpenShift 5）；智能助手排障（汇总指标/事件/Pod 日志/分布式追踪为结构化摘要，需 OpenShift 4.22+ 与 Lightspeed operator 1.1.5+，在 OpenShift 5 生产可用）；AI 生成 Perses 仪表盘（无需 PromQL 按需出图，cluster observability operator 1.6 起每个面板带 AI-Assisted 标记，可审计底层 PromQL、时间范围与指标后再固定）。文章重点写升级前必须处理的配置变更：Prometheus remote-write 每个端点单独设 messageVersion（V1.0 默认 / V2.0 带元数据，改前须确认接收端支持）；node-exporter 的 nvmesubsystem collector 在 OpenShift 5 默认开启（上游默认关闭），关闭时 CSIVolumeNVMePathDegraded/Lost 两条告警不会触发；ClusterMonitoring CR 仍为技术预览且需 TechPreviewNoUpgrade 特性门，ConfigMap 优先；Thanos sidecar/Ruler 改用集群 TLS profile、kube-state-metrics 与 openshift-state-metrics 改用 EndpointSlices。另梳理 logging 6.7（Loki 4.0 / schema v13+ / TSDB 索引、olderThan 丢弃过滤、Elasticsearch P2C 与 HA、AWS PrivateLink、AtLeastOnce 磁盘缓冲）与 OpenTelemetry 3.11（webhook HA、OBI eBPF 零代码插桩技术预览、Remote Write receiver、Redaction processor、Headers setter、Leader Elector、Tempo HA 与 MCP 追踪工具）。也如实标注厂商稿的边界：全篇无性能数字与第三方验证、结论区文档链接仍指向 4.18、多处功能标注技术预览或需特定 operator 版本。"
published: true
---

> 一手：Red Hat 官方博客《Guide to observability with Red Hat OpenShift 5》（2026-11-11）全文
> 对照：OpenShift 官方文档的组件清单、同系列 4.18 指南
>
> 这是厂商发布的版本变更清单，不是第三方评测；文中把「宣传表述」与「配置事实」分开写。

Red Hat 11 月 11 日发了《Guide to observability with Red Hat OpenShift 5》，五位产品经理联署，6 分钟阅读。标题叫「指南」，但通篇没有一条 `oc` 命令、没有性能数字，实质是 OpenShift 5 可观测性组件的版本变更清单。

这类文章最容易被改写成产品宣传稿。真正值得读的是两处：AI 排障能力被分成了三种不同的可用状态，以及升级到 5 之前有几项必须预先确认的配置变化会改变行为。

## 一、三种 AI 能力，三种成熟度

开篇说 OpenShift 5 的可观测性由 Red Hat OpenShift Lightspeed 驱动，有「3 项核心能力」。逐条看，这三项的门槛完全不同：

| 能力 | 做什么 | 状态与门槛 |
|---|---|---|
| 自主排障 | 配好 Alertmanager 适配器后，告警一触发就自动启动调查：检查集群状态、起草初步诊断、把可执行的修复方案放进决策队列等人在控制台或 CLI 复核 | 技术预览；需 Lightspeed operator 2 + OpenShift 5 |
| 智能助手排障 | 人自己主导调查，Lightspeed 把指标、事件、Pod 日志、分布式追踪汇总成一份结构化摘要，过滤噪声、定位根因 | OpenShift 4.22+ / Lightspeed operator 1.1.5+ 可开始用；在 OpenShift 5 生产可用 |
| AI 生成 Perses 面板 | 不用写 PromQL，直接问「哪些 Pod 在 crashloop」「各命名空间内存用量」，用 cluster observability operator + Red Hat build of Perses 按需出图 | 起步需 COO 1.5+；AI-Assisted 徽章要 COO 1.6 + Lightspeed 1.1.5+ + OpenShift 5 |

最值得写的是第一项的护栏设计，而不是「AI 自动修故障」这个卖点。官方给的约束很具体：

- 所有状态变更都要管理员显式批准（官方原话「all state changes require explicit administrator approval」）；
- 执行发生在沙箱 Pod 内，按动态 RBAC；
- 如果提出的修复失败，agent 不重试、不猜，直接升级给人类操作员；
- 修复计划只「暂存」在决策队列里，不自动落地。

也就是说，它把「提议」和「执行」拆成了两层，中间卡着一个人。这跟本站写 secwrap 时那条「提问层可以漏、强制层不能漏」是同一个思路 —— 在运维场景里，AI 最贵的错误不是没查出问题，是自动改错了集群。

第三项也有个很克制的设计：COO 1.6 起每个 AI 生成的面板都带 AI-Assisted 标记，平台团队可以先审计底层 PromQL、时间范围和指标，再决定是否固定到生产仪表盘。生成物默认不被当成可信产物，这一点比「自然语言生成仪表盘」本身更重要。

顺带说清组件分工，免得把 operator 混成一团：按 Red Hat 官方文档，集群监控栈（Prometheus / Alertmanager / Thanos Querier / Telemeter Client）由 Cluster Monitoring Operator（CMO） 预装管理；Cluster Observability Operator（COO） 是单独安装的，负责 Perses 仪表盘与控制台 UI 插件，并不管 Loki/Tempo 后端；日志走 Loki Operator + Logging Operator，追踪走 Tempo Operator + Red Hat build of OpenTelemetry。博客里这些名字密集出现，但没解释层级。

## 二、升级前必须先确认的四处配置变化

这一节是全文对运维最有用的部分，而且都是会改变行为的默认值/语义变化。

① Prometheus remote-write 消息版本，按端点单独设。 在 `cluster-monitoring-config` ConfigMap 里，每个 remoteWrite 端点有自己的 `prometheusK8s.remoteWrite[].messageVersion`，允许 `V1.0` 与 `V2.0`，默认 V1.0、不设就是 V1.0。选 V2.0 时，Prometheus 会把抓取指标的元数据（指标类型、可选 help 字符串与单位）追加到 WAL。官方明确提醒：改之前先确认接收端支持哪个版本。这在多接收端（自建 Thanos、云厂商、第三方 APM）的环境里是最容易踩的一项。

② node-exporter 的 NVMe collector 默认打开了。 OpenShift 5 把 `nvmesubsystem` collector 设为默认启用，而上游 node-exporter 默认是关的。它暴露 NVMe over Fabrics 的子系统与路径健康：节点能看到哪些控制器、每条路径是 live / connecting / deleting、属于哪个子系统。关键在于两条存储告警 `CSIVolumeNVMePathDegraded` 与 `CSIVolumeNVMePathLost` 读的就是这些指标 —— collector 关掉，告警不会触发。没有 NVMe 设备的节点上，collector 只读一个空目录，开销可忽略；仍可在 node-exporter collector 配置里关掉。这是一条典型的「默认行为变了，告警覆盖面跟着变」的升级项。

③ ClusterMonitoring CR 还是技术预览，ConfigMap 仍优先。 目前 `cluster-monitoring-config` ConfigMap 依旧是 CMO 实际应用的配置源；ConfigMap 不校验取值，写错了要等 operator 日志里才看得出来。新的 `ClusterMonitoring` 自定义资源是 Phase 1 技术预览，藏在 `ClusterMonitoringConfig` 特性门后，而该门只有集群使用 `TechPreviewNoUpgrade` 或 `DevPreviewNoUpgrade` 特性集时才开启 —— 这两个特性集本身就意味着不能升级。第一阶段只覆盖 node-exporter、Thanos querier、telemeter client、监控插件与 OpenShift state metrics；同一字段若 ConfigMap 与 CR 都设了，operator 保留 ConfigMap 的值。把它当成「配置迁移已完成」会出事。

④ Thanos 与目标发现的底层变化。 Thanos sidecar 与 Thanos Ruler 的 gRPC TLS 密码套件与曲线改为继承集群 TLS profile，不再是硬编码 —— 如果集群已经选了自定义 profile，之前硬编码会忽略它。`kube-state-metrics` 与 `openshift-state-metrics` 的目标发现改用 EndpointSlices。

## 三、日志与追踪：一串版本号，挑影响最大的说

Logging 6.7 的核心是 Loki 4.0 引擎迁移到 schema v13+ 的 TSDB 索引：官方称可降低磁盘 I/O 争用、减少标签尖峰时的内存占用、加快 LogQL 查询，并原生支持 OTLP 属性而不引发 stream 爆炸。官方给的动作很直接：迁移 LokiStack 配置到 schema v13+ 才能用上这些能力。其余四项偏工程韧性：`olderThan` 丢弃过滤（ClusterLogForwarder API，自动丢掉截止日期前的历史日志，避免集群恢复/重连时日志积压）、Elasticsearch 多端点的 P2C 负载均衡 + 自动故障转移（兼容单 URL 旧配置）、LokiStack 原生 AWS S3 VPC Endpoint / PrivateLink（对象存储流量走私网、减少出网费）、以及 `AtLeastOnce` 磁盘缓冲（下游故障或网络抖动时不丢数据，批量参数可调）。

Red Hat build of OpenTelemetry 3.11 的新东西分两类。可立即用的：operator webhook HA（可设副本数，避免 webhook 离线导致服务中断）、Prometheus Remote Write receiver（让 OTel Collector 直接作为 Prometheus 的 remote-write 目标）、Redaction processor（删除不在允许列表里的数据点属性，用来清理 PII / 凭据 / 敏感遥测）、Headers setter extension（改导出请求的 HTTP/gRPC 头，便于多租户路由与认证）、Kubernetes Leader Elector extension（集群级组件跑 HA 而不压垮 API server）。技术预览的是 OBI 接收器：用 eBPF 检查代码与网络，零代码改动抓取 Web 流量 trace span 与 RED（Request / Error / Duration）指标。

分布式追踪侧给了 Tempo HA（可定义每个 Pod 的副本数与放置，支持 zone-aware replication 以扛住整可用区丢失）、启用 query RBAC 时服务名/命名空间的自动补全（以前菜单是空的），以及把追踪工具接进 MCP server：可列出 Tempo 实例、按 ID 取 trace、搜索 traces/tags/tag values。最后一条最有时代感：OpenShift 5 里用 Lightspeed 的客户能在 Tempo 中审计 agentic runs，从控制台的 Agentic Runs UI 拿到审计 trace 链接，用来回答 AI 合规问题 —— 也就是上一节「AI 提议 + 人批准」这套流程本身，也要被可观测性记录下来。

## 四、厂商稿的边界，得自己补上

- 全文没有任何性能数字、基准或第三方验证。像「大幅降低 I/O 争用」「加快查询」「过滤无关噪声」都是定性表述，没有量级。
- 多处功能带状态标签：自主排障是技术预览、ClusterMonitoring CR 是技术预览且需不可升级特性集、OBI 自动插桩是技术预览；AI 面板的 AI-Assisted 徽章要 COO 1.6，智能助手在 4.22 就能起步但「生产可用」绑定 OpenShift 5。把这些混成「OpenShift 5 全都可用」是误读。
- 结论区给的文档链接指向 OpenShift Container Platform 4.18 的文档页，而正文讲的是 OpenShift 5 —— 属于厂商博客常见的链接滞后，查配置时请以对应版本文档为准。
- 文章末尾是产品试用与反馈表单，性质是发布说明 + 营销内容。本文未把其中任何宣传语当作实测结论。

也有个值得对照的历史坐标：同系列 2025 年 2 月的《OpenShift 4.18 可观测性指南》还在列 Alertmanager 0.27 / Prometheus 2.55.1 / Thanos 0.36.1 这类组件版本号；这次 5 的指南几乎不报上游版本，重心完全移到了 Lightspeed 的 AI 能力与配置迁移。这个变化本身比某一项新功能更能说明产品方向。

## 五、事实边界

- 本文所有功能、版本号、配置字段与默认行为均取自 Red Hat 2026-11-11 官方博客原文；组件分工参照 OpenShift 官方文档，未安装 OpenShift 5 实测。
- `messageVersion`、NVMe collector、`ClusterMonitoring` CR、Thanos TLS 与 EndpointSlices 等为厂商描述，本文未验证在真实集群上的行为；升级前请以目标版本官方文档核对。
- Loki 4.0 / schema v13+ / OTel 3.11 / Tempo HA 等均为发布说明口径，无性能数据；「显著」「更快」等表述不作定量解读。
- 技术预览功能按 Red Hat 惯例不附带生产 SLA，本文未展开各功能的支持策略，请以官方支持声明为准。

## 六、结论

把这篇「指南」压缩成运维动作，其实只有几条：升 5 前先盘一遍 remote-write 每个端点的 `messageVersion`；确认 NVMe collector 开/关与两条 CSI 告警的覆盖关系；别把 ClusterMonitoring CR 当成已迁移；LokiStack 要迁到 schema v13+。

而它真正想说的产品判断藏在护栏里：AI 可以自动调查、自动起草诊断、自动出图，但修复计划要进队列等人批准、执行要进沙箱、失败要交还给人、生成的面板要带可审计标记。可观测性走到 agent 时代，新增的是「让 AI 的每一次提议都留下可查的证据」—— 后者恰好是可观测性本来就该干的事。

## Sources

- Red Hat《Guide to observability with Red Hat OpenShift 5》（2026-11-11）：<https://www.redhat.com/en/blog/guide-observability-red-hat-openshift-5>
- OpenShift 官方文档《About Observability》（4.16）：<https://docs.redhat.com/en/documentation/openshift_container_platform/4.16/html/observability_overview/observability-overview>
- 同系列《Guide to observability with Red Hat OpenShift 4.18》（2025-02）：<https://www.redhat.com/en/blog/guide-observability-red-hat-openshift-418>
