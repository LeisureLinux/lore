---
title: "Vagrant 走到 EOL：那个把 vagrant up 写成动词的公司，把它还给了社区"
date: 2026-11-13
slug: vagrant-eol-hashicorp-mit-license
category: 技术/解读
author: FreeLAMP.com
original_source: "一手核对：HashiCorp Discuss《Vagrant is moving to an open source model》（kala.nenkova，2026-11-12 18:17 UTC；官方写明 Vagrant 年底 EOL、使用率下降、不再打补丁与维护发布、一两个月内归档仓库、许可证由 BUSL 改回 MIT、任何人可 fork 维护；新建 MPL-2.0 的 hashicorp/vagrant-registry-export 用于导出 box 与元数据；给出 2010 年前六个月无版本下载过 100 次、两年后年下载破百万、2020 年每年四五百万、近 1300 位贡献者/14000+ commits/12 万行代码）＋ HashiCorp 官方博客《HCP Vagrant deprecation: important dates and migration guidance》（Kala Gullick、Matt McQuillan，2026-09-17；10-01 停止新建 box/registry、11-02 结束支持维护、12-31 停止运营；明确「此弃用仅适用于 HCP Vagrant」，CLI 与 GitHub 源码仓库保留；导出到本地、S3 托管指南、静态归档与 URL 重定向；联系邮箱 vagrant@ibm.com）＋ HCP 官方文档《Deprecation of HCP Vagrant》（2026-07-30 创建、2026-08-26 修改，FAQ 与时间表）＋ HashiCorp Discuss《Deprecation of HCP Vagrant》（2026-08-03）＋ GitHub hashicorp/vagrant 实时元数据与 LICENSE（2026-11-13 查询：MIT、Copyright IBM Corp. 2026、archived=false、27228 stars / 4488 forks / 758 open issues、默认分支 main、Ruby、最新提交 2026-11-12「Move docs back into the repository」、最近稳定版 2.4.9 于 2025-08 及 2.4.10.dev 预发布）＋ HashiCorp《Announcing HashiCorp》（Mitchell Hashimoto，2012-11-27；「创立 HashiCorp 是为了推动 Vagrant 的发展」、Vagrant 此前三年只是每天 2–4 小时的副项目、承诺 Vagrant 永远开源且宽松许可、2010 年大学宿舍起步）＋ HashiCorp《HashiCorp: 2013 in Review》（Vagrant 1.1 于 2013-03 发布，脱离 VirtualBox 单一依赖）＋ HashiCorp《Vagrant Cloud Migration Announcement》（2017-05-31，Vagrant Cloud 从 Atlas 独立）＋ HashiCorp《HashiCorp Terraform》发布公告（2014-07-28）＋ HashiCorp《HashiCorp adopts Business Source License》（Armon Dadgar，2023-08-10；全线产品由 MPL 2.0 改 BSL 1.1/BUSL，API/SDK 仍 MPL 2.0）＋ HashiCorp《HashiCorp officially joins the IBM family》（Armon Dadgar，2025-02-27，IBM 收购交割完成）＋ HashiCorp Origin Story 与《Growing HashiCorp From Dorm Room OSS to Thriving Company》＋ AlmaLinux《AlmaLinux Vagrant boxes have a new home》（2026-11-02，自建 vagrant.almalinux.org 目录、VAGRANT_SERVER_URL 与 Vagrantfile 的 box_server_url 用法）＋ Wikipedia Vagrant / HashiCorp 条目用于版本号与沿革交叉验证"
original_date: 2026-11-12
original_url: "https://discuss.hashicorp.com/t/vagrant-is-moving-to-an-open-source-model/78189"
description: "求证「Vagrant 要凉了」：属实，但要分两层。2026 年 7–9 月官宣的是 HCP Vagrant（原 Vagrant Cloud 托管 box 注册表）分阶段关停，时间表为 10-01 停止新建、11-02 结束支持、12-31 停止运营，当时官方明确写「CLI 与源码仓库保留」。真正的转折是 2026-11-12 HashiCorp Discuss 的《Vagrant is moving to an open source model》：官方带着遗憾确认 Vagrant 年底进入 EOL，使用率下降、无力继续打补丁与维护发布，一两个月内归档仓库；同时把许可证从 BUSL 改回 MIT，允许任何人 fork 维护，并新建 MPL-2.0 的 vagrant-registry-export 帮助搬迁 boxes。文章写出与 Terraform 的关系：Vagrant 是 HashiCorp 的起点，2010 年 Mitchell Hashimoto 在大学宿舍做出它，2012 年他成立 HashiCorp 的理由就是「推动 Vagrant 的发展」，之后才有 Terraform（2014）、Consul、Vault、Nomad、Packer；2023 年全线改 BUSL，2025-02 IBM 完成收购，如今联系邮箱已是 vagrant@ibm.com。历史部分用官方数字：首发半年无版本下载过 100 次、两年后年下载破百万、2020 年每年四五百万、近 1300 位贡献者 14000+ 次提交 12 万行 Ruby 代码。也给出退场后的现实处置：HCP 注册表 12-31 关停后短名字 box 会失效，AlmaLinux 已自建目录，可用 VAGRANT_SERVER_URL 或在 Vagrantfile 写 box_server_url 迁移；仓库实时状态为 MIT、尚未归档。结尾以克制的惋惜收束：把「环境可写进文件、可销毁重建」变成一代人常识的工具，最后靠改回 MIT 交还社区收场。"
published: true
---

> 一手：HashiCorp 官方 EOL 公告、HCP Vagrant 弃用公告与文档、GitHub 仓库实时状态、HashiCorp 历年官方博客
> 对照：AlmaLinux 的 box 目录迁移公告、Wikipedia 版本号交叉验证
>
> 这不是一次事故，也不是被谁正面击败。一个把「开发环境可以写进一个文件」变成常识的工具，最后是靠改回 MIT 许可证、请社区自己接手来收场的。

## 一、先把「要凉了」这句话核清楚

2026 年 7 月到 9 月，HashiCorp 先公告的是 HCP Vagrant（原 Vagrant Cloud，托管 box 的注册表）分阶段关停：

- 10 月 1 日：不再新建 box 与 registry；
- 11 月 2 日：结束支持与维护；
- 12 月 31 日：停止运营，剩余部署全部下线。

那份公告反复强调一句 「此弃用仅适用于 HCP Vagrant」，并写明 Vagrant CLI 与 GitHub 源码仓库都会保留，团队仍可本地构建 box、或把 box 放到自己托管的位置。所以当时若只看到「HCP Vagrant 关停」的标题，很容易以为只是关掉一项云服务。

真正把话说死的是 2026-11-12 HashiCorp Discuss 上的《Vagrant is moving to an open source model》。公告开头那句「It is with sadness, we remind the community that Vagrant is reaching end of life at the end of this year.」把情绪写得很明白，随后给出四条硬信息：

1. Vagrant 年底进入生命周期终点（EOL）；
2. 技术工具与使用方式已经变了，Vagrant 的使用率与流行度下降，加上职责优先级，厂商已无力继续打补丁和发布维护版本；
3. 一两个月内仓库会归档，此后不再有更新或维护发布；
4. 为让仍在使用的人继续用下去，许可证从 BUSL 改回 MIT，任何人可自由 fork 并自行维护。

另外新建了 `hashicorp/vagrant-registry-export`（MPL-2.0），帮用户从即将关停的注册表里导出 box 与元数据。

查了 GitHub API 与仓库现状（2026-11-13）：`hashicorp/vagrant` 的 `LICENSE` 已经是 MIT，署名 `Copyright IBM Corp. 2026`；仓库尚未归档，27228 stars、4488 forks、758 个 open issues，默认分支 `main`，语言 Ruby，最新提交是 11-12 的「把文档移回仓库」。也就是说公告刚落地，归档动作还在路上。

准确说法因此是：Vagrant 的厂商维护结束了，软件没被删，代码被松开了手。「凉」这个字，用在「不再有官方新版本、注册表年底关停」上是成立的；用在「命令立刻跑不动」上则过了。

## 二、和 Terraform 何止同一家

「我记得和 Terraform 是同一家公司」—— 这个记忆不但没错，还说轻了：Vagrant 是 HashiCorp 成立的原因。

| 时间 | 事件 |
|---|---|
| 2010-01 / 03 | Mitchell Hashimoto 在大学宿舍里开始写 Vagrant，3 月首发；用 Ruby 把 VirtualBox 包装成「一个 Vagrantfile + 一条 `vagrant up`」 |
| 2012-11-27 | Hashimoto 发文《Announcing HashiCorp》，原话是自己是 Vagrant 的创建者与维护者，创立公司就是为了推动 Vagrant 的发展；此前三年 Vagrant 只是每天投入 2–4 小时的副项目。文中还承诺 Vagrant 将永远保持开源与宽松许可 |
| 2013-03 | Vagrant 1.1 发布，官方年终回顾称其为「monumental release」，开始脱离对 VirtualBox 的单一依赖，provider 接口向 AWS、KVM、LXC 等开放 |
| 2014-07-28 | Terraform 发布，把「基础设施即代码」推向跨云编排 |
| 2017-05 | Vagrant Cloud 从 Atlas 中拆出独立运营，box 可以按名字搜索、版本化、分享 |
| 2023-08-10 | HashiCorp 宣布全线产品从 MPL 2.0 改为 BSL 1.1 / BUSL，Vagrant 与 Terraform 同在此列（API、SDK 仍保持 MPL 2.0）；社区当时有专门的许可证讨论帖 |
| 2025-02-27 | IBM 完成对 HashiCorp 的收购；如今 HCP Vagrant 弃用公告里的问题联系邮箱已写成 `vagrant@ibm.com` |
| 2025-08 | 稳定版 `2.4.9` 发布，此后主要是 `2.4.10.dev` 预发布 |
| 2026-07 → 11 | HCP Vagrant 官宣关停 → 11-12 Vagrant 本体 EOL、许可证回退 MIT、预告归档 |

一个副项目长成一家公司，公司长出改变运维行业的一整套工具链，十六年后被大厂收进产品线，最后一个「改回 MIT、交还社区」的公告收尾。这条曲线本身，比任何评价都更有年代感。

## 三、它曾经把什么变成了常识

官方在告别帖里给了组数字，比任何形容词都实在：

- 2010 年首发时，前六个月没有任何一个版本的下载量超过 100 次；
- 两年后，年下载量突破一百万；
- 到 2020 年，每年四五百万次；
- 背后是近 1300 位贡献者、14000 多次提交、约 12 万行代码。

这些数字对应的是一件很朴素的事：在 Vagrant 之前，「配一个能跑项目的环境」通常意味着手工装系统、装依赖、改配置，然后在交接时补一句「在我机器上是好的」。Vagrant 把它压缩成三行命令 —— `vagrant init`、`vagrant up`、`vagrant ssh` —— 环境写进 `Vagrantfile`，可以版本控制、可以销毁重建、可以发给同事。

后来这套观念被容器、云开发环境、声明式基础设施接了过去，接得比它自己更彻底。 Terraform 把同样的思路从「一台开发虚拟机」放大到「整个跨云基础设施」，某种意义上正是 Vagrant 那套直觉的规模化版本。所以公告里那句「技术工具已经变了、使用率下降」，翻成大白话是：它教会的那套做法赢了，而它自己不再是默认载体。

## 四、还在用的人，眼下该做什么

EOL 不等于今天就不能用，但 12 月 31 日 HCP 注册表关停是个实打实的坎：依赖 `bento/ubuntu-24.04`、`almalinux/9` 这类短名字 box 的 `vagrant up` 或 `vagrant box add`，到时候会因为找不到目录而失败。

HashiCorp 给的迁移路径是：清点 Vagrantfile、CI/CD 流水线、内部文档与自建 box，把 `.box` 文件和 catalog metadata（版本、provider、架构、下载 URL、校验和）迁到自己托管的位置，例如 S3 或静态归档；官方也承诺提供导出工具与迁移指南。

社区已经在自救。AlmaLinux 于 11 月 2 日上线自建目录 `vagrant.almalinux.org`，保留了曾在 HCP 发布过的全部历史版本，box 名字不变，只需指过去：

```
export VAGRANT_SERVER_URL=https://vagrant.almalinux.org
vagrant init almalinux/10
vagrant up
```

或在 `Vagrantfile` 里写 `config.vm.box_server_url`，CI 用 `sudo vagrant up` 时更稳妥（sudo 会丢掉大部分环境变量）。AlmaLinux 还提醒一个坑：已经从 HCP 加进来的 box 会记住旧来源，即使改了环境变量，`vagrant box outdated` 仍可能误报为最新；需要在新目录下重新 add，再 `vagrant box prune` 清掉旧版本。运行中的 VM 不受影响。

至于更远的将来，MIT 许可证摆在那里，仓库尚未归档，任何团队都可以 fork 后自己维护。只是从厂商角度，不会再有官方补丁与维护版本了 —— 这一点公告写得没有回旋余地。

## 五、事实边界

- 本文的 EOL、许可证回退、归档预告与下载/贡献者数字，均出自 2026-11-12 官方公告；HCP 时间表与「仅适用于 HCP Vagrant」来自 7–9 月官方文档与博客。
- 仓库状态（MIT、`archived=false`、stars / forks / issues、最新提交、版本线）为 2026-11-13 通过 GitHub API 与 `LICENSE` 文件实时查询的结果，归档动作可能在之后随时发生。
- 「被容器与云开发环境分走需求」属于技术史归纳；官方只写了使用率下降、技术工具改变、无力继续维护，本文未把归纳包装成厂商原话。
- 2012 年公告里「Vagrant 将永远保持开源与宽松许可」是当时的承诺，与 2023 年改 BUSL、2026 年改回 MIT 的事实并列呈现，不作评价性推断。
- 本文未安装 Vagrant、未验证 HCP 注册表迁移流程；命令行示例引自 AlmaLinux 官方迁移公告。

## 六、结语

Vagrant 的退场没什么戏剧性。没有重大事故，没有一场正面竞品对决，只是「本地起一台完整虚拟机」这个需求慢慢被更轻的方案分走了。官方写得克制：使用率下降，职责太多，无法再打补丁。

遗憾大概就在这里。今天的基础设施比 2010 年可复现得多、也声明式得多，工具链漂亮得像样板间；可那个最先让人尝到甜头、连公司都因它而建的小工具，最后是靠「改回 MIT、请社区自己接手」收场的。技术往前走的时候，很少回头给铺路的东西发一张感谢状。

好在他不是被埋掉，是被交还。MIT 许可证还在，仓库还没归档，两万多颗星还亮着。守着几台跑得好好的 Vagrant VM 的人，把 box 迁到自己的目录还能慢慢用下去；愿意接手的人，fork 一个继续维护也名正言顺。

`vagrant up` 大概不会再有新版本了。但那台第一次被一行命令拉起来的虚拟机，很多人应该都还记得。

## Sources

- HashiCorp Discuss《Vagrant is moving to an open source model》（2026-11-12）：<https://discuss.hashicorp.com/t/vagrant-is-moving-to-an-open-source-model/78189>
- HashiCorp《HCP Vagrant deprecation: important dates and migration guidance》（2026-09-17）：<https://www.hashicorp.com/en/blog/hcp-vagrant-deprecation-important-dates-and-migration-guidance>
- HCP 文档《Deprecation of HCP Vagrant》：<https://developer.hashicorp.com/hcp/docs/vagrant/hcp-vagrant-eol> ｜ 导出工具：<https://github.com/hashicorp/vagrant-registry-export>
- GitHub 仓库：<https://github.com/hashicorp/vagrant>
- HashiCorp《Announcing HashiCorp》（2012-11-27）：<https://www.hashicorp.com/en/blog/announcing-hashicorp> ｜ 《HashiCorp: 2013 in Review》：<https://www.hashicorp.com/en/blog/hashicorp-2013-in-review>
- HashiCorp《HashiCorp Terraform》（2014-07-28）：<https://www.hashicorp.com/en/blog/terraform-announcement> ｜ 《Vagrant Cloud Migration Announcement》（2017-05-31）：<https://www.hashicorp.com/en/blog/vagrant-cloud-migration-announcement>
- HashiCorp《HashiCorp adopts Business Source License》（2023-08-10）：<https://www.hashicorp.com/en/blog/hashicorp-adopts-business-source-license> ｜ 《HashiCorp officially joins the IBM family》（2025-02-27）：<https://www.hashicorp.com/en/blog/hashicorp-officially-joins-the-ibm-family>
- AlmaLinux《AlmaLinux Vagrant boxes have a new home》（2026-11-02）：<https://almalinux.org/blog/2026-11-02-vagrant-catalog/>
