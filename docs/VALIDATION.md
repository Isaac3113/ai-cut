# 验证状态与复用边界

原创作者于2026-09-12明确认可最后的完整视频与HyperFrames/Remotion动画做法，要求后续沿用；预设标识approved-vd44-teaching-v1。

已有代表工程证据：1920×1080、30fps、101.5秒；1.1倍口播主体；HyperFrames6.7秒状态卡、Remotion27.933秒多阶段流程及3秒头像片尾真实渲染并合成到ChatCut。完整MP4技术检查及关键帧审阅曾执行。私人视频、截图和账号工程不公开，公开仓库不假装附有这些可自行核验的媒体。

不随案例继承：代理完整连续观看/试听、人工字幕≤200ms测量、新机器安装、第二条不同原片重复成功、所有画幅验证、第三方商业许可。这些仍按真实运行逐项验证。创作者的满意反馈与代理实际执行的检查分开保存。

本次公开快照通过的测试/构建记录见发行时的实际终端结果和CI；测试数量不是审美得分。当前verify_review_media.py含代表工程的1080p30和关键帧采样预设，其他视频必须按主时间轴调整，不能直接当通用验收器。

## 2026-09-13 本机公开源码验证

原始维护目录与干净公开目录各128项unittest通过。公开目录的媒体测试需FFmpeg；第一次未配置时3项明确失败，加入已安装FFmpeg后通过。Remotion ESLint/TypeScript通过；HyperFrames修复资源路径后严格check为0错误0警告，135动画样点、69对比度检查。

从公开目录实际下载GSAP/字体并通过固定SHA256检查，渲染201帧/6.7秒状态动画，完整解码通过，实际查看一张卡片画面。新编码视频与旧素材的解码哈希不同，不声称逐像素等价；未替换用户已认可的成片。该验证使用同一台电脑，不等于全新机器安装或另一条原片全流程通过。

公开包入口链接、JSON私人路径检查通过，Skill格式验证通过。GitHub在线CI尚未执行；本文件记录的是本机验证。

## 2026-09-13 完整交付与目录规则

维护项目146项Python回归通过；新增TXT/SRT导出、绝对速度核验、独立视频目录和大批边界平衡抽帧。实际代表片94.3秒含封面，102帧抽查及全片解码通过；完整试听和人工200ms同步仍未验证。每片目录规则见project-storage.md，固定交付见final-delivery.md。代码分发不自动改变仓库private可见性。

## Shared storage correction

The per-video directory helper now separates Project Hub media/deliveries from local editing work, requires an explicit/configured Hub, and rejects OneDrive work/cache roots. Earlier same-root examples are superseded by references/project-storage.md. Migration checks and actual regression results are recorded separately from video listening.

同一台迁移后的电脑上，分发源码146项回归也已通过；使用已安装运行时，不能称为新电脑首次安装通过。

2026-09-13 storage correction verified on the existing computer: 150 tests passed in the maintenance checkout (11.588s) and independently in the distribution checkout (11.026s). This is not new-machine validation. Legacy OneDrive removal is still pending the owner's other-computer confirmation; runtime/Skill now use the local checkout. No new full-video listening or rendering claim.

2026-09-13 follow-up: the owner confirmed the old OneDrive copy was used only on this computer. Legacy source/cache removal is now COMPLETE; originals were moved to an off-OneDrive backup, not deleted. Media and deliveries remain in the Hub. Post-move real runtime, existing job, model/Skill hashes, representative transcode/decode and unchanged subtitle checks passed. No implementation change or new-machine/full-film acceptance claim.

## 2026-09-21 整合后复核

目标checkout完整176项unittest通过；原始沙箱/路径失败及修正见KB26。Skill格式验证通过；24个安装文件与维护源码逐文件SHA256一致，保留原source_root。目标源码的完整学员包实际导出33文件（其中24个总Skill文件），ZIP CRC/逐文件哈希、主Skill链接与文本隐私扫描通过。出版allowlist内的所有规则/代码与经脱敏的维护源码一致。

实际只读审计已认可案例配置：43个实操事件、六类效果、最大起点间隔3.0秒、cadence_ok=true；独立helper代码SHA256与已认可版本相同。本轮未重新渲染或视听视频。前向审查覆盖缺ChatCut连接、新片未选比例、已确认方形实操逐个音效编辑、同片字幕修改不重复降低音乐、明确本机路线与9:16源限制；修正发现的旧默认/交付数量/路径冲突。

新Remotion示例并非全部注册在旧默认入口，私人头像不随源码分发，详见WORKFLOW_AND_TOOLS.md。本机已有Python/FFmpeg用于验证，未声称在全新电脑安装、线上CI或新ChatCut工程通过。保留PRIVATE仓库规则，不改变可见性。
