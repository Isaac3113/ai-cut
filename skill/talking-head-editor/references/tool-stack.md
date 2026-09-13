# 工具与Skill的精简分工

保留一个主剪辑入口，按任务路由本机、ChatCut或剪映；不叠装全部截图工具。用户可直接说“按我的口播规则剪这条视频”。完整步骤在[总规则](master-playbook.md)，个人参数在[用户偏好](user-preferences.md)。

## 调用条件和责任

| Skill / 工具 | 调用条件 | 结果进入哪里 | 不做什么 |
|---|---|---|---|
| talking-head-editor | 接收原片、完整剪辑或任何修改 | 当前执行器的唯一时间轴、绑定源片和交付版本 | 不让本地与云端计划独立漂移 |
| ChatCut官方插件 | 用户选网页后台剪辑和在线手改 | asset-import → Script → native captions/MG → verification → export | 不上传其他未授权文件，不以扁平旧成片冒充工程 |
| jianying-editor | 用户选本机剪映 | 既有时间轴转候选草稿，必须实际打开验证 | 不将结构生成当作原生导出成功 |
| video-use本地适配版 | 重录/停顿疑点、接缝、流程对象和局部检查 | 主工程的审阅证据、待修正位置 | 不使用上游ElevenLabs转写、独立EDL/render、默认粗体字幕 |
| remotion-best-practices | 设计重点字、流程推进或其他时序动画；实际React任务 | 帧驱动与同步规则，或经验证后登记的动画素材 | 不因读规则就安装运行时或声称已由Remotion导出 |
| FunASR / FFmpeg / FFprobe / Pillow | 实际识别、剪辑、声音、轻图形、导出和检查 | 主工程当前版本 | 不重复安装已有有效依赖 |
| cover-prompt-worker（主Skill内子任务） | 每条完整片TXT确定，需封面结构稿 | 当前Codex/子代理输出四个标题角度和规定结构；主员工审核后交内置imagegen | 不上传到未知服务，不编造本人身份/成果 |
| 内置imagegen | 审核Prompt及真实参考帧已就绪 | 独立封面素材，回主时间轴实际入片 | 不声称工具未返回的模型版本；图片生成不等于入片 |
| scripts/export_final_subtitles.py | 最终速度/封面与字幕卡锁定 | 同源SRT、无时码TXT及校验清单 | 不重新ASR、不变速、不自动完整审片 |

talking-head-editor主控所有声音轨和视觉事件。video-use子步骤完成即返回主流程。用户已授权的Remotion4.0.523和HyperFrames0.8.35在extensions的独立子目录真实渲染；普通重点字继续用ChatCut原生MG，复杂动画作为无声插入素材返回唯一在线时间轴，按[实际引擎流程](reference-motion.md)执行。安装规则、本机依赖、云端导出和用户认可分别记录。

辅助Skill必须遵守最新个人偏好：原片单比例、默认1.1倍速且本条指定速度优先、每3～5秒可见变化且硬上限5秒、自然字幕和显式重点动画、独立轻SFX、安静BGM、本人真实头像片尾。上游高音量、默认云上传、批量安装或重复审批不替代用户已确认规则。当前音效/音乐参数由主工程统一管理，辅助规则不各写一套。

## 已研究项目的处理

| 名称 | 处理 | 边界 |
|---|---|---|
| [FFmpeg](https://ffmpeg.org/documentation.html)、[FunASR](https://github.com/modelscope/FunASR)、Pillow | 沿用本地环境 | 负责实际执行，不再重复安装Skill或复制源码 |
| [Remotion官方Skills](https://github.com/remotion-dev/skills) | 已安装规则与本地范围入口 | [引擎许可](https://www.remotion.dev/license)与使用规则另核，规则安装不等于运行时可用 |
| [video-use](https://github.com/browser-use/video-use) | 已安装本地适配，使用局部审片包装 | 原版默认ElevenLabs云转写；本地入口禁用云helpers和独立渲染，不索取密钥 |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | 0.8.35已在独立子目录实际渲染 | 短HTML/GSAP状态动作；只装所需项目Skill，保持Apache2及GSAP/字体许可记录 |
| JianyingEditor | 已装固定来源的本地适配入口 | [社区项目](https://github.com/luoluoluo22/jianying-editor-skill)不是剪映官方；生成候选已验证，原生打开/手调/导出尚未验证 |
| ChatCut | 官方插件1.10.12已安装、登录、真实重剪和导出 | 官方MCP执行，不占用桌面剪映焦点；右侧在线工程，实际视听质量仍另验 |
| Azure TTS、ElevenLabs | 暂不接入 | 保留真人原声，不增加合成配音/云音频上传 |
| Shots (by LTX) | 未安装，来源待明确 | 截图无唯一仓库，不以同名第三方包替代 |
| Epidemic Sound | 未接入订阅 | 商业素材服务不能当免费库；继续自有、原创或许可明确的免费BGM/SFX |
| FunClip、Auto-Editor、MoneyPrinterTurbo等候选 | 不重复安装 | 曾研究不等于都是依赖，按实际缺口决定 |

截图营销名称和热度不能证明官方来源、Windows可用、免费许可或已经导出真实用户MP4。

## 来源、安装与更新

源码extensions/upstream-lock.json锁定GitHub提交与逐文件Git blob；skill-adapters仅维护本地范围入口。上游参考/脚本装到个人目录，不把整套仓库、媒体、模型、.env或.git复制进源码Git。

scripts/install_extensions.py先校验全部来源与已有安装，再写入；Windows CRLF只在能还原精确上游字节时接受。已有个人修改、缺文件或哈希异常停止覆盖，保留现状。installation.json记录来源、固定提交、适配范围和字节哈希；上游入口保存为UPSTREAM_SKILL.md。内嵌Manim入口仅保留REFERENCE.md，不注册更多Skill或安装引擎。

video-use只通过已审阅的scripts/video_use_review.py使用。包装使用现有FFmpeg、中文字体和严格解码，拒绝缺失/不足音频，不把转写间隙当静音；PNG旁保存检查范围与限制。归一化波形不能证明5%音效、响度或200ms同步达标，报告继续标记实际听审状态。这不是GUI时间线，不改原片。

迁移按Knowledge_Base/10_Skill_Stack.md恢复固定来源与本地环境。安装成功、规则可发现、辅助脚本跑通、引擎可用和真实成片验收分别核实。重开任务可刷新Skill列表，不为此重装Codex。

本轮规则增加视觉节奏、SFX与片尾，不表示旧v4已经改变；实际成片以当前计划、引擎版本、渲染指纹和真实检查为准。

## 学员阅读顺序

总入口 → [完整执行顺序](approved-workflow.md)与当前预设 → 已选工具基础Skill → 内容粗剪 → 画面选材 → 原生重点字/HyperFrames/Remotion的对应分支 → 统一合成 → 实际导出验收 → 可见版本交付。每个分支的名字、职责和产物在approved-workflow逐项列出，不要求每步把全部小Skill加载一遍。
