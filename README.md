# Talking Head Editor · 教学口播剪辑总 Skill

2026-09-21整合版：保留原Python执行器0.2.5及动画扩展；合入比例确认、双平台五项素材、类型命名、AIVD连续编号、实操六类效果与ChatCut主路线规则。规则更新不等于已连接云端或完成新视频验收。

由 Codex 理解口播内容，用 ChatCut 管理可编辑主时间轴，按场景调用 HyperFrames 和 Remotion 制作动画。包含完整规则、Python执行器、两套动画源码、原生重点字示例、检查程序和回归测试。

本预设来自创作者反复反馈并明确认可的一条完整教学视频：对象动作、流程计时与分拍重点字；当前升级为Logo品牌色、轻水印、全屏素材同步真人动态圆窗、安静音乐与轻音效。公开代码不附带私人视频、头像、账号、客户数据或旧项目历史。

## 第一次按这个顺序看

1. **[总 Skill 入口](skill/talking-head-editor/SKILL.md)**：决定路线，守住单一主时间轴。
2. **[完整执行流程与小 Skill 顺序](skill/talking-head-editor/references/approved-workflow.md)**：从接收、粗剪、选材、动画到导出的完整步骤；包含历次反馈形成的规则。
3. **[已认可预设](skill/talking-head-editor/references/user-preferences.md)** 与 **[完整质量规则](skill/talking-head-editor/references/master-playbook.md)**。
4. 使用网页编辑时读 **[ChatCut流程](skill/talking-head-editor/references/chatcut.md)**；动画选型看 **[两引擎分工](skill/talking-head-editor/references/reference-motion.md)**。
5. **[验收](skill/talking-head-editor/references/quality.md)** → **[手动修改/恢复](skill/talking-head-editor/references/manual-editing.md)**。

日常只调用 `$talking-head-editor`。辅助Skill按场景加载，不需要把所有工具依次运行一遍。

2026-10-08包装更新：本用户片内封面只闪0.1秒（30fps为3帧，无淡入淡出）；固定片尾改用用户提供的视频，当前实施参数为原件1.2倍一次，正文和BGM不因此再加速。详见[固定片头片尾](skill/talking-head-editor/references/intro-outro.md)。换电脑先读[安全pull、Skill与素材同步](docs/CROSS_COMPUTER_UPDATE.md)及[KB28](03_Documentation/Knowledge_Base/28_Intro_Outro_And_Cross_Computer.md)；Git不包含私人片尾素材或在线工程。

## 当前统一路线

对本仓库创作者，ChatCut是默认主编辑时间轴与最终导出入口；仅明确选择其他主路线时切换。换电脑先核对实际工具、账号、项目ID和当前时间轴，缺连接先说明，不静默改为本机工程。复杂特效可由本机工具生成素材再导入ChatCut；字幕、人声、音乐与逐事件音效保留独立轨道/片段。外部特效素材的内部参数仍可能需要源码重渲染。

本机可恢复ZIP与最终MP4不等于ChatCut可编辑时间轴。详见[工具与工程说明](docs/WORKFLOW_AND_TOOLS.md)；本次代码整合没有创建或迁移用户的在线视频工程。

## 主要规则

- 保留真人、原声、事实、否定和条件；先做完整语义粗剪，再包装；删改可恢复。
- 每条新视频先询问并取得用户确认的视频比例，只做所选一版；口播主体绝对1.2倍一次，字幕和事件共同映射；外部动画/BGM不重复加速。
- 普通口播每3～5秒有相关可见变化；有真实电脑实操则约每3秒安排重点放大、框选、聚光、下划线、脉冲或流程推进，配同步轻音效；无实操不套用。重点字放大，基础字幕可读。
- HyperFrames做短状态卡，Remotion做精确多步骤/计时/片尾，简单重点字用ChatCut原生层。
- 音乐轻且能听见、音效与重点动作同步可听，人声清楚；旧极低增益不是新素材固定上限。先处理原声再混音，不在混合后整体提高响度。
- 使用真实素材或标明示意；采购有授权，素材许可和公开分发权限分开。
- 实际导出、观看、试听和检查分别记录。风格已获原创作者认可，不证明其他视频或机器已经通过。
- 交付前确认浏览器真实选中的新版时间轴，打开关键动画，并核对完整MP4；不只交单独动画素材。

## Windows安装

需要Git和Python3.11/3.12。ChatCut使用你自己的官方插件/账号；密码与授权确认由你输入。

```powershell
git clone https://github.com/Isaac3113/talking-head-editor.git
Set-Location talking-head-editor
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe scripts/install_skill.py
.\.venv\Scripts\python.exe -m talking_head_editor.cli doctor
```

需要本地语音识别时再执行 `scripts/bootstrap.ps1 -ASR`（会下载模型和较大依赖）。ChatCut模式可用已授权的官方转写或已有有效转写，不要求重复安装另一套识别。

Skill安装器会记录你的源码目录。若手动复制Skill目录，设置 `TALKING_HEAD_EDITOR_ROOT` 指向本仓库；环境检测没通过时不能说已具备剪辑能力。

### 动画运行时

Node>=22（案例使用24）、npm、Chrome与FFmpeg。安装不包含商业许可；先读 [THIRD_PARTY](THIRD_PARTY.md)。在仓库根目录运行：

```powershell
.\extensions\remotion-vd44\run.ps1 -Action Install
.\extensions\remotion-vd44\run.ps1 -Action Check
.\extensions\remotion-vd44\run.ps1 -Action Render -Composition CustomerJourney
.\extensions\hyperframes-vd44\run.ps1 -Action Install
.\extensions\hyperframes-vd44\run.ps1 -Action Doctor
.\extensions\hyperframes-vd44\run.ps1 -Action Check
.\extensions\hyperframes-vd44\run.ps1 -Action Render
```

脚本可传 `-NodePath`、`-NpmCli`；Remotion可传 `-BrowserPath`，HyperFrames可传 `-FfmpegDirectory`。没有可用工具会明确失败，不默认沿用讲师个人路径。HyperFrames Install会下载并核对固定GSAP/字体哈希，Doctor/check/render分别验证引擎。

`CustomerJourney`是四步流程教学示例，不是所有新口播的固定文案或时间。仅明确选用旧头像片尾方案时，才将有权使用的真实头像放在 `extensions/remotion-vd44/public/presenter.jpg`，修改结束语/品牌后渲染；代码不附头像。本用户当前使用上述固定视频片尾。当前Remotion场景模板为16:9，竖屏必须重新排版并验证。

### 辅助 Skill

- ChatCut：从Codex插件目录安装官方插件，在自己的账号授权；从 `chatcut:chatcut-plugin-basics` 进入，然后按总Skill调用所需子步骤。
- Remotion与video-use：固定来源在 `extensions/upstream-lock.json`，自己的范围适配在 `skill-adapters`。按 [安装说明](docs/INSTALL_SKILLS.md) 安装完整上游，不能只复制缺少参考文件的适配入口。
- HyperFrames：按 [安装说明](docs/INSTALL_SKILLS.md) 在动画项目内安装所需官方Skill，规则顺序见approved-workflow；不全局覆盖总Skill。

## 给Codex的启动消息

```text
使用 $talking-head-editor，沿用已认可动作节奏，使用我的Logo品牌配色、淡水印和全屏素材动态圆窗。
原片：<路径>；文稿/术语：<可选>；素材：<可选文件夹>。
用ChatCut作为主时间轴，开始前核对工具连接和已有工程；缺连接先说明，不静默换路线。按场景选HyperFrames/Remotion或本机实操素材工具。
保留原意原声，先确认本条视频比例再做所选一版，口播相对原片绝对1.2倍一次，音乐轻且能听见、重点音效同步可听。
先粗剪，再安排真实画面和对象动作；有电脑实操时约每3秒安排合适效果并配同步音效，没有实操则跳过。
人声、背景音乐、逐事件音效保留独立轨道或片段，方便在ChatCut逐个调整；外部动画内部参数保留源码供重渲染。
项目用AIVD连续编号加确认主题，同片修改沿用编号。交付完整MP4、字幕、ChatCut工程链接/时间轴标识及修改记录。
```

## 分享和开发

```powershell
.\.venv\Scripts\python.exe scripts/export_student_skill.py --out '<新建的学员包目录>'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

学员包包含完整规则合订阅读版和可安装Skill目录；可执行源码就是本仓库。无原片不能重建案例成片；外部动画在ChatCut里是视频片段，内部文字需修改HTML/React源码重渲染。

原创代码与规则采用 [MIT](LICENSE)。Remotion、GSAP、ChatCut、字体/音乐等保留各自许可，不承诺整套第三方服务免费。当前没有自动发布、常驻后台服务、自动付款或声音克隆。实片的风格反馈与技术/视听证据界限见 [验证状态](docs/VALIDATION.md)。

## Complete deliveries and project storage

Each full video includes MP4 with cover, standalone cover, plain TXT, SRT, full production explanation, per-second/per-frame records and honest QA. Read `skill/talking-head-editor/references/final-delivery.md`. Keep active code, dependencies and work/cache outside OneDrive. Use `scripts/create_video_folder.py --hub "YOUR_PROJECT_HUB" --name "AIVD 5 - Your confirmed topic"` to create separate per-video media/delivery and local-work folders; revisions reuse the pair. The Hub has no implicit code-root default. Private footage and exports are excluded from Git. Repository visibility remains the owner’s explicit choice.


编号5仅为例子，创建前核对已有AIVD编号；已有视频修改不增加编号。缺主题先询问，不以原片001或拍摄日期代替正式项目名。每条完整视频还交付Facebook/小红书两篇文案、Facebook封面、小红书竖版与4:3横版封面；既有原片/历史交付不批量改名。音乐“降低30%”仅是已指定案例相对已认可音轨乘0.70，不是每条重复降低或所有音乐的默认值。
