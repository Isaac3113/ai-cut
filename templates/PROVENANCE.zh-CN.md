# MotionGit 中文目录的来源与验证边界

更新日期：2026-10-27。本页说明本仓库的中文选型索引；不是 MotionGit 全站库存、下载授权或运行兼容性承诺。

## 固定来源

- 上游集合：[motiontemplates/all](https://github.com/motiontemplates/all)，固定 commit `21537c6f49aa9504496d20c14bf597f7eac229f4`，提交时间 `2026-10-27T03:02:25Z`。
- [固定原始 catalog.json](https://raw.githubusercontent.com/motiontemplates/all/21537c6f49aa9504496d20c14bf597f7eac229f4/catalog.json) 原样保存在 [sources/motiongit-catalog.snapshot.json](sources/motiongit-catalog.snapshot.json)，315398 bytes，SHA-256 `c4bb605a22a3529c0dcbe8acb720ae50df3f5bc0c4ede8577f6caf8218d9a485`。
- 人读来源是同 commit 的 [官方中文 CATALOG.md](https://github.com/motiontemplates/all/blob/21537c6f49aa9504496d20c14bf597f7eac229f4/CATALOG.md)。本地整理结果在 [motiongit-styles.json](motiongit-styles.json)。
- 快照只包含公开目录元数据，没有个人 `.motion`、Key、账号、模板源码包或 Demo 媒体。上游文本中的 AI 使用建议只是来源资料，不会自动升级成本项目规则或执行授权。

## 数量怎样计算

| 口径 | 数量 | 说明 |
| --- | ---: | --- |
| 主清单 `entries` | 72 | 固定 catalog 的 `templates`；每个 `repositoryId` 一条，包含画幅版本和动效片段，不等于 72 套完整视频模板 |
| 主条目 Demo | 73 | 每条一个，另加 385712 的官方中文竖屏 Demo |
| 独立预告 `previews` | 1 | 3D 书，官方标记 `previewOnly`、`coming-soon`，不计入 72 |
| 官方 Demo URL | 74 | 上述 73 + 1，逐字段核对均非空，去重后仍为 74；没有逐条播放或下载 |
| 描述性家族 | 66 | 本地按同一 `group` 内的中文标题去除明确竖屏后缀后归并，不是官方 family ID 或官网 Styles 总数 |

主清单分类是 `open: 1`、`talk: 21`、`explainer: 19`、`product: 14`、`art: 17`。本地中文分别为科技视觉、口播与讲解、知识解说与流程图、产品宣传与教程、视觉与场景动效；科技和艺术类别不默认套到整条真人口播。`art` 中的 3D 吉祥物教程仍按官方组别保留，其用途单独说明。

主条目画幅是 16:9 × 62、9:16 × 7、3:4 × 1、4:3 × 1、1:1 × 1。加上 385712 竖屏演示后是 73 个版本记录，其中 9:16 为 8；3D 书预告另为 16:9。将明确横竖配对的七组名称合并得到 66 个描述性家族。归并仅用于浏览，不能推断版本、参数或渲染器可共用。

2026-10-27 的[官网默认库](https://motiongit.com/templates)显示 45 项；当日[整套模板筛选](https://motiongit.com/templates?type=full-template)与[动效片段筛选](https://motiongit.com/templates?type=motion-fragment)分别显示 33 与 12。它们是默认库的类型划分。页面另列 Innovation 27、待认领 774；[Innovation 页面](https://motiongit.com/templates?status=innovation)说明该区作品在默认库外等待反馈和后续筛选，部分缓存仍显示 26。不要把不同筛选、不同缓存、待认领作品与本快照混算成全站“可下载整套模板”数量。

## 中文字段与选型建议

官方 [中文网页](https://motiongit.com/templates?currency=CNY&lang=zh)和 catalog 已有 `title.zh`、`summary.zh`。本索引保留来源身份和摘要；`Light Ribbon Word` 在官方中文标题字段中仍是英文，本地补译为“光带文字”，保留英文原名与补译说明，不冒称原作者提供的中文名称。标题为中文不证明作者原始创作语言、全部配音语言或每个版本都有完整中文输入支持。

`category_zh` 是对官方组别的本地中文整理；`uses_zh`、`avoid_zh` 是基于摘要与本项目要求的选型建议。`inputs_zh` 是公开 `materials.zh` 的原文或摘要；未给输入的条目明确写未知，不从演示猜参数。摘要本来简短或截断时保留来源状态，不补造能力。

适用范围：`talk` 优先评估真人知识、观点、案例和营销方法讲解；`explainer` 优先评估关系、流程、数据与教学图解；`product` 优先评估功能、品牌、上手教程。它们仍可能是短片段、固定时长或特定输入合同。系统录屏需要看清真实界面时，应先检查 UI 占比与字号；多屏包装和装饰不能替代原始操作证据。

## Demo、可取得与版本是不同事实

本索引的“官方Demo可看”表示官方目录提供了可点击 URL。2026-10-27对74个唯一URL完成HEAD检查，全部返回200，正文读取0 bytes；证据留本机work/template-center-20261027/official-demo-links.json。未批量下载、逐条完整播放或听审。HTTP可访问不代表当前账号能下载模板包、已获商业素材许可、已在本机运行或已适配本期视频。

固定目录的 71 个主条目指向 `official-page` / `check-official-page`；385712 另有公开 `direct-package` 记录。这是目录声明，不是本次下载或权限验证。官网有条目显示“模板更新中，即将开放下载”，所以 `coming-soon` 的 3D 书并不是唯一需要检查实际取得状态的内容。所有主条目统一显示“以官网当前页面为准”。

385712 的公开横屏版是 `0.2.7-open-beta`；额外中文竖屏记录是 `0.2.38-open-beta`，其 Demo 文件名仍含 `0.2.9-open-beta`。它们不能互相证明最新版本行为。旧研究中的官网 `2.7.13`、当前现代图文竖屏 `2.7.17-alpha.2`、公开 adu classic `1.1.1-candidate` 也不是同一版本。

根据[官方格式规范](https://motiongit.com/spec)，`.motion` 是包与输入/依赖合同，不强制统一动画引擎。每条仍须读取自己的 runtime、依赖、素材、时钟、输出与许可；包内 `SKILL.md` 不会自动安装成独立 Skill。本索引不新增 72 个 Skill，也不表示已有通用 `.motion` 渲染器。

## 许可证与第三方资产

目录的 `openSource: true` 是上游声明，本次没有逐包审定许可证。不能从开放格式、GitHub 页面或 Demo 下载地址推出所有内容均为 MIT，亦不能把模板代码许可泛化到人物肖像、录音、字体、音乐、Logo 和界面素材。

已独立核对 [385712 固定源码 LICENSE](https://github.com/motiontemplates/385712/blob/9dfbe7d7c6a6d4aa03f6f8e2f2285e631099faae/LICENSE)为 MIT，版权属于 MotionGit contributors。该证据仅覆盖该公开代码许可；使用时仍须保留许可证及版权声明，另查第三方资产和官网个人版本。公开 adu classic 的许可证、版本和实测也不能替其他官网模板背书。

[官方创作者协议](https://motiongit.com/legal/creator)要求区分代码和素材许可，并保留作者及衍生来源关系。MotionGit 是汇集多个作者的来源，不应把所有作品说成同一作者原创。本索引保存官方条目 URL、来源 ID，以及目录已有的公开仓库与 commit；没有源码的条目不伪造仓库链接。

本项目已有 RenderComp、RemotionUI 等来源属于另一组库，不计入这 72 条，也不继承 MotionGit 的许可。个人包或账号Key不进入Git。用户于2026-10-27追加长期授权：以后每条新片接入或改进适配时，将docs/template-gallery/demos内经检查的精选本人小样、海报、分类动图及集成说明同步私人Git；仍不扩展到完整原片、完整成片、源人像/遮罩、个人包、Key、客户敏感资料或公开再分发。公开元数据、受许可源码和本地说明分别保留来源。

## 实际验证范围

官网风格集合中的 `mg-style-314486` 标记“局部实测”：官网现代图文竖屏 `2.7.17-alpha.2` 的两段 highlight/underline 用于同一 55.0333 秒 A/B 的末 10.233 秒，其余沿用 A 画面和整条原音轨。两版各 1651 帧/30fps、全解码成功，整条 AAC 与 PCM 校验一致，已抽检最终编码画面。用户本轮已认可B版局部效果；该认可不扩大到整套风格、其他模板或全部控件。完整native版式只是预览；模板自身声音优势、连续观看和完整听审仍未由本次检查证明。

身份与时钟边界仍适用：无同期本人时，不把 UI 内演员裁成讲师圆窗；原声只保留一份，字幕时钟只偏移一次；最终字号、UI 占比、时间码和 Logo 避让须看实际编码视频。上述检查不能推广为整套风格或其余 71 条通过。详细本地评估入口是 [KB30 MotionGit 接入评估](../03_Documentation/Knowledge_Base/30_MotionGit_Evaluation.md)。

公开集合检查覆盖固定快照哈希、JSON结构、72个唯一ID、来源、分类/画幅、73个条目Demo加1预告及74个URL的HEAD可访问性；未批量取得全站模板或全站素材授权。

本轮本地目录另完成strict构建：216个分层条目为72官网条目、70控件、55代码注册项和19真人分支；不是216套完整视频模板。145个本地静音MP4含本人B案例，共14,877,520 bytes，配145张实际帧海报和23分类GIF；27分类都有演示入口。制作代理完成70控件代表的全解码与联系表审看，55和19项完成全解码与各三个时点的实际帧检查；210变体只渲70代表，不声称逐条连续观看。gallery核对本次未重复全解码，检查来源分别记录。详见[KB31](../03_Documentation/Knowledge_Base/31_Template_Center_And_Editing_Routes.md)。

## 本地补译

`mg-style-872`原名为Light Ribbon Word，本目录显示“光带文字”；这是本地标题翻译，保留英文原名，不更改或冒称原作者中文版本。
