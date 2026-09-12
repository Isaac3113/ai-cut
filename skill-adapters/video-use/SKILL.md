---
name: video-use
description: 本地适配的视频审阅辅助。用于用户点名video use、检查重录停顿、剪切接缝、流程动作、重点事件和局部画面节奏；沿用talking-head-editor的转写与可恢复工程，不默认使用ElevenLabs云转写。
---

# Video Use：本地审阅辅助

方法与时间轴图工具来自[browser-use/video-use](https://github.com/browser-use/video-use)，固定来源见installation.json。本地入口由AI-Talking-Head-Editor维护。[上游原始说明](UPSTREAM_SKILL.md)仅作参考；云密钥、安装、粗体字幕、独立EDL、默认音量及三次重试规则不覆盖用户已确认的主流程。

## 什么时候使用，检查什么

1. 接手真人口播先读相邻talking-head-editor/SKILL.md与其references/user-preferences.md。完整任务的全部步骤在references/master-playbook.md。已有工程读取当前revision和转写；主Skill负责实际剪辑、渲染、声音与打包，本辅助步骤完成就返回，不另建EDL或重新识别。
2. 对失败重录、口癖与停顿先比较完整语义，再看局部原片证据；有意强调、否定和条件不得机械删除。删改建议锚定原片时间并写回主工程。
3. 复核流程“对象—动作—状态变化”，保留尚未购买/未回复等条件；并列分类不当顺序。图库和原创界面不能冒充真实客户/系统。
4. 按当前规则复核每3～5秒可见变化、硬上限5秒；重点字短暂放大、人物克制推近已获授权。普通字幕换行和嘴动不算有效变化，事件安排还须与实际输出对照。
5. 声音只辅助定位：SFX和BGM独立，SFX轻短仅重点事件、BGM安静、人声不降；具体参数读主偏好。波形不证明音效增益、听感、响度或200ms同步通过，也不能用转写间隙宣称静音。
6. 查看本人片尾的实际来源、构图、文字和收尾；不凭抽帧推断音频已淡出。所有观察记录真实位置，没有听审就标待验证。同一问题定位修复后最多明确重试一次。

## 使用已审阅的包装脚本

源码默认C:\Codex Workspace\AI-Talking-Head-Editor，迁移后用实际目录。使用已有.venv，不安装上游整套依赖。

调用scripts/video_use_review.py，参数为--video <真实文件> --start <开始秒> --end <结束秒> --output <新的PNG路径>，需要时另加--transcript <与此视频同时间轴的JSON>。原片转写只能叠在原片上；成片转写必须已经按剪辑/1.1倍速映射，无法证明时省略转写。

包装加载经哈希核验的helpers/timeline_view.py，使用现有FFmpeg、中文字体和严格解码，拒绝不足音频；只生成局部抽帧/波形PNG及范围/限制JSON。不改视频、不转写、不上传、不购买、不生成新声音。

未启用上游transcribe.py、transcribe_batch.py、独立render.py和Manim引擎。不要根据install.md读取.env、索取API key或设置账号。用户将来明确要求其他服务时再核实用途、费用、许可和数据去向；现有授权的本地审阅不重复请示。
