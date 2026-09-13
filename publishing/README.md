# Talking Head Editor · 教学口播剪辑总 Skill

当前规则与执行器版本0.2.5；品牌/圆窗审计见主Skill的brand-and-presenter.md。历史渲染证据与新规则实际验收分开记录。

由 Codex 理解口播内容，用 ChatCut 管理可编辑主时间轴，按场景调用 HyperFrames 和 Remotion 制作动画。包含完整规则、Python执行器、两套动画源码、原生重点字示例、检查程序和回归测试。

本预设来自创作者反复反馈并明确认可的一条完整教学视频：对象动作、流程计时与分拍重点字；当前升级为Logo品牌色、轻水印、全屏素材同步真人动态圆窗、安静音乐与轻音效。公开代码不附带私人视频、头像、账号、客户数据或旧项目历史。

## 第一次按这个顺序看

1. **[总 Skill 入口](skill/talking-head-editor/SKILL.md)**：决定路线，守住单一主时间轴。
2. **[完整执行流程与小 Skill 顺序](skill/talking-head-editor/references/approved-workflow.md)**：16步从接收、粗剪、选材、动画到导出；包含历次反馈形成的规则。
3. **[已认可预设](skill/talking-head-editor/references/user-preferences.md)** 与 **[完整质量规则](skill/talking-head-editor/references/master-playbook.md)**。
4. 使用网页编辑时读 **[ChatCut流程](skill/talking-head-editor/references/chatcut.md)**；动画选型看 **[两引擎分工](skill/talking-head-editor/references/reference-motion.md)**。
5. **[验收](skill/talking-head-editor/references/quality.md)** → **[手动修改/恢复](skill/talking-head-editor/references/manual-editing.md)**。

日常只调用 `$talking-head-editor`。辅助Skill按场景加载，不需要把所有工具依次运行一遍。

## 主要规则

- 保留真人、原声、事实、否定和条件；先做完整语义粗剪，再包装；删改可恢复。
- 默认按原片比例输出一版；口播主体绝对1.2倍一次，字幕和事件共同映射；外部动画/BGM不重复加速。
- 每3～5秒有相关可见变化；画面先有对象/动作/条件/结果，再配重点字。
- HyperFrames做短状态卡，Remotion做精确多步骤/计时/片尾，简单重点字用ChatCut原生层。
- 音乐与SFX分别极轻，人声清楚。先处理原声再混音，不在混合后整体提高响度。
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

`CustomerJourney`是四步流程教学示例，不是所有新口播的固定文案或时间。片尾需要将你有权使用的真实头像放在 `extensions/remotion-vd44/public/presenter.jpg`，并修改结束语/品牌后渲染；代码不附头像。当前场景模板为16:9，竖屏必须重新排版并验证。

### 辅助 Skill

- ChatCut：从Codex插件目录安装官方插件，在自己的账号授权；从 `chatcut:chatcut-plugin-basics` 进入，然后按总Skill调用所需子步骤。
- Remotion与video-use：固定来源在 `extensions/upstream-lock.json`，自己的范围适配在 `skill-adapters`。按 [安装说明](docs/INSTALL_SKILLS.md) 安装完整上游，不能只复制缺少参考文件的适配入口。
- HyperFrames：按 [安装说明](docs/INSTALL_SKILLS.md) 在动画项目内安装所需官方Skill，规则顺序见approved-workflow；不全局覆盖总Skill。

## 给Codex的启动消息

```text
使用 $talking-head-editor，沿用已认可动作节奏，使用我的Logo品牌配色、淡水印和全屏素材动态圆窗。
原片：<路径>；文稿/术语：<可选>；素材：<可选文件夹>。
用ChatCut作为主时间轴，按场景选HyperFrames/Remotion。
保留原意原声，按原片比例一版，口播相对原片绝对1.2倍一次，音乐与音效极轻。
先粗剪，再安排真实画面和对象动作。交付完整MP4、字幕、正确可见工程及修改记录。
```

## 分享和开发

```powershell
.\.venv\Scripts\python.exe scripts/export_student_skill.py --out '<新建的学员包目录>'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

学员包包含完整规则合订阅读版和可安装Skill目录；可执行源码就是本仓库。无原片不能重建案例成片；外部动画在ChatCut里是视频片段，内部文字需修改HTML/React源码重渲染。

原创代码与规则采用 [MIT](LICENSE)。Remotion、GSAP、ChatCut、字体/音乐等保留各自许可，不承诺整套第三方服务免费。当前没有自动发布、常驻后台服务、自动付款或声音克隆。实片的风格反馈与技术/视听证据界限见 [验证状态](docs/VALIDATION.md)。

## Complete deliveries and project storage

Each full video includes MP4 with cover, standalone cover, plain TXT, SRT, full production explanation, per-second/per-frame records and honest QA. Read `skill/talking-head-editor/references/final-delivery.md`. Keep active code, dependencies and work/cache outside OneDrive. Use `scripts/create_video_folder.py --hub "YOUR_PROJECT_HUB" --name "AIVD - Your topic"` to create separate per-video media/delivery and local-work folders; revisions reuse the pair. The Hub has no implicit code-root default. Private footage and exports are excluded from Git. Repository visibility remains the owner’s explicit choice.
