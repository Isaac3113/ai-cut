> 2026-09-21追加 long-form-clips-v2：用户指定AIVD5 Zoom母项目，1:1已确认，自主选题/命名，条数不限5条；逐句筛选痛点、真实卖点、原声钩子与必要条件，删除啰嗦。要求ChatCut与完整A到Z操作录屏。每片用AIVD5子序号。当前已注册官方MCP并登录成功，但本会话及子代理尚无ChatCut工具，待新会话加载。未开始正式剪辑。详见KB27最新段落。

> 2026-09-21新增 long-form-clips-v1：Zoom/长访谈按单一主题策划 2～5 条，目标每条加速后含包装 90～120 秒，保留问答/条件、避免重复；每条独立主时间轴。详见 [KB27](27_Long_Form_Clips.md)。本次规则安装与实际剪辑状态分开记录。

> 2026-09-21用户最终认可AIVD4 R6音量，并指定以后沿用。Skill已升级aivd4-r6-quiet-bgm-v1：BGM比人声低约39 LU为参考，实际成片匹配极轻听感；同一已处理音乐不重复衰减，新曲重新校准，SFX独立。替代旧15～20 LU起点及R4/R5历史参数。此次仅规则/认可记录更新，未重剪；用户认可与代理未连续试听分开。

> 2026-09-21 GitHub总Skill整合与ChatCut主路线：用户指定仓库已合入后续规则与配套代码，ChatCut为默认主路线，缺连接不静默换工具；本轮无视频迁移。当前证据读[26_GitHub_Skill_Integration.md](26_GitHub_Skill_Integration.md)。

# Start here
2026-10-27: [KB30 MotionGit接入评估](30_MotionGit_Evaluation.md)记录当前Skill审计、官网2.7.17-alpha.2隔离实测及同音轨A/B。建议保留现有主时间轴、按内容局部接入；未设为默认，个人模板包和测试媒体不进入Git。技术检查、抽帧审阅与完整听审／用户风格认可分别记录。

2026-10-26 封面风格认可：用户已认可原片暗背景、真人轮廓描边、hook及主副辅助文字层级的样图，命名为`dark-frame-cutout-hook-v1`，并明确这是多种风格之一。可按内容与画幅尝试其他风格，不固定样图标题、斜黑体或右下布局；旧亮浅渐层加居中大头像及普通主题词不再作为默认。规则和Hub参考图入口见[当前用户偏好](../../skill/talking-head-editor/references/user-preferences.md)与[封面提示词员工](../../skill/talking-head-editor/references/cover-prompt-worker.md)。本次风格认可不替代实际片头替换、重新导出或全片验收；0.1秒片头规则保持。

2026-10-26: [KB29 可复用代码特效库](29_Reusable_Effect_Library.md)记录50套现成模板、两项适配组件、独立调用入口、参考19项差距与本次真实渲染范围。

Read ../../README.md and ../../skill/talking-head-editor/references/approved-workflow.md. The approved teaching preset is reusable; every new video is separately checked. This public snapshot contains source, not private footage or account permissions.

2026-10-08: [KB28 固定片头片尾与跨电脑更新](28_Intro_Outro_And_Cross_Computer.md)记录0.1秒封面、用户视频片尾、媒体哈希及安全更新边界。规则正文在master Skill的references/intro-outro.md；一键复制交接与安全pull见docs/CROSS_COMPUTER_UPDATE.md。

2026-09-13: Keep code/runtime/work outside OneDrive; the Project Hub stores documents, media and deliveries. Directory helper requires a configured Hub and separately creates local work. Existing Chinese titles are preserved; Windows CLI output uses UTF-8. See master references/project-storage.md. Actual regression status: docs/VALIDATION.md.
