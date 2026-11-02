# 自动剪辑 Skill 使用教学｜从领取到剪出第一支口播

欢迎领取 Talking Head Editor（知识口播剪辑 Skill）。这份指南先带你完成安装，再用自己的素材试剪。第一次使用，按顺序做到第六步即可；进阶模板稍后再学。

当前领取方式：私人 GitHub 仓库逐个授权。收到这份教学不等于已经取得仓库访问权限。

## 一、这个 Skill 适合剪什么？

适合真人知识口播、AI 教学、营销方法、系统操作演示，以及从长访谈中整理单一主题短片。

它会指导 AI 理解内容、删掉无用重复和停顿、整理字幕，并按讲解选择重点字、放大、流程动画、音乐和音效。原则是保留你的原声和原意，不把字音剪断。

Skill 是 AI 的工作流程与规则。实际制作还需要能读取本机文件的 Codex、剪辑工具、自己的账号和素材。它不是把一句提示词贴进任意聊天窗口就能运行的软件，也不是所有视频类型的通用一键剪辑器。旅游 Vlog、剧情和多场景混剪，需要另选制作路线。

## 二、先取得 GitHub 访问权限

1. 准备自己的 GitHub 账号，将 GitHub 用户名提供给讲师。
2. 讲师邀请后，用被邀请的账号接受仓库邀请。
3. 登录同一账号，确认能打开下方项目主页，再开始安装。

[项目主页与完整文件](https://github.com/Isaac3113/talking-head-editor)

看到 404、Repository not found 或没有下载入口时，先核对账号、邀请和权限；不要反复重新安装软件。

以下 GitHub 教学链接也需要同一份访问权限。

## 三、电脑需要准备什么？

这份入门教学以 Windows 为主，其他系统请先让 Codex 检查兼容性，不直接照抄 Windows 命令。

| 准备项 | 用途 |
| --- | --- |
| 能访问本机文件的 Codex 客户端及自己的账号 | 阅读规则、检查环境、调用剪辑工具 |
| Git | 将获授权的项目下载到电脑，之后更新代码 |
| Python 3.11 或 3.12 | 运行本项目的安装及辅助脚本 |
| 自己的 ChatCut 插件、账号及实际可用连接 | 本教学默认使用的剪辑工程和导出路线 |
| 自己的 MP4 | 先用 20～30 秒清晰口播验证流程 |

Codex、ChatCut、云端转写、生成和导出的可用功能与费用，取决于各自的账号、当前套餐及额度。取得 Skill 或 GitHub 权限不附送这些服务额度。

首次不必安装所有动画引擎，也不必先安装本地语音识别模型。先完成基础试剪，遇到具体特效需求时，再按文档准备 Node、Remotion、HyperFrames 或自己的 MotionGit 包。

## 四、安装到自己的电脑

建议源码目录：`C:\Codex Workspace\talking-head-editor`。这是推荐示例，不是讲师电脑的共享文件夹；不要把正在运行的源码、依赖和缓存放进 OneDrive 同步目录。

### 方法 A：让 Codex 带你安装

打开能访问本机文件的 Codex，复制以下内容。若需要登录 GitHub，请你自己在官方登录窗口完成。

```text
请帮我安装 talking-head-editor。我使用 Windows，已经接受私人 GitHub 仓库的邀请。
仓库：https://github.com/Isaac3113/talking-head-editor
建议源码目录：C:\Codex Workspace\talking-head-editor

先检查本机 Git、Python 3.11／3.12、是否已有源码及同名 Skill，再读取仓库的 docs/NOTION_GUIDE.zh-CN.md、docs/GETTING_STARTED.zh-CN.md 和 docs/INSTALL_SKILLS.md。
没有源码时再 clone；已有源码时先保护本地修改，不能删除或强制覆盖。
按当前安装脚本准备环境并安装总 Skill。首次新装使用当前客户端支持的 Skill 发现目录；如已有安装，先核对归属，避免安装两份同名 Skill。
检查我自己的 ChatCut 插件、账号与实际可调用工具。需要我登录时告诉我操作位置；不要从文档里的“已连接”推断本机已连接。
本次先安装并验证，不剪正式视频、不生成付费素材、不发布内容。安装完成后，分别报告源码、Skill、基础环境、ChatCut连接各自的实际状态。
```

### 方法 B：已具备基础环境时手动安装

以下命令用于第一次安装，且目标源码目录和同名 Skill 尚不存在。如果已经安装过，直接看后面的更新说明。

在 PowerShell 中逐行执行。第一行创建源码父目录；clone 下载项目；bootstrap 准备独立 Python 环境、FFmpeg/FFprobe 及核心依赖；install_skill 安装规则；doctor 检查部分本机环境。

```powershell
New-Item -ItemType Directory -Force -Path "C:\Codex Workspace" | Out-Null
Set-Location "C:\Codex Workspace"
git clone https://github.com/Isaac3113/talking-head-editor.git
Set-Location "C:\Codex Workspace\talking-head-editor"
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe scripts/install_skill.py --target "$env:USERPROFILE\.agents\skills\talking-head-editor"
.\.venv\Scripts\python.exe -m talking_head_editor.cli doctor
```

这里的 `--target` 使用当前官方文档列出的用户级 `.agents/skills` 目录。旧客户端或既有安装可能使用其他位置，请先检查，保留一份有明确归属的有效安装。安装器提示既有 Skill 被修改或来源不同，先比较处理，不要强删覆盖。

任何一步报错，先停在该步，把命令和完整错误发给 Codex。不要忽略失败继续往下执行，也不需要为了本项目全局放宽脚本执行策略。

完成后让 Codex确认能发现 `talking-head-editor`，并读到本仓库的规则。新 Skill 没出现时可重启客户端再检查。`doctor` 成功不代表 ChatCut 已连接，也不代表任何新视频已经完成。

[详细环境、动画及辅助 Skill 安装](https://github.com/Isaac3113/talking-head-editor/blob/main/docs/INSTALL_SKILLS.md)

## 五、先连接自己的剪辑工具

当前默认主路线是 ChatCut：安装并授权你自己的插件，登录自己的账号，再让 Codex 检查本次实际可用的工具。

Skill 安装、账号登录、工具可调用、素材可读、工程可导出，是不同检查项。Git clone 不会复制讲师的登录状态、原片、音乐、片尾、MotionGit 私人包或云工程。

如果工具连接不上，先完成连接检查；若选择改走本机制作，应明确新的路线和输出限制，不能把静音 Demo 当作已完成的口播成片。

## 六、剪第一支视频

先准备一段 20～30 秒的自有口播，记下 MP4 的完整路径。将下面的方括号内容换成你的真实资料，填写视频比例后发送。

```text
请使用 $talking-head-editor 帮我做第一次知识口播试剪。

原片完整路径：[填写我的 MP4 完整路径]
本条视频比例：[明确填写 9:16、16:9、1:1 或沿用原片比例]
主题：[填写主题，或写“看完后按实际内容命名”]
重点保留：[我希望观众记住的内容]
必须保留的术语／数字：[填写；没有则写“无”]
输出目录：[填写我自己的交付目录]

请先核对规则、实际工具和原片，再开始制作。仓库中 Isaac 的品牌、固定片尾、速度、路径、编号、社媒标签和发布账号都只是他的个人配置，不自动套用到我。
本次保持原速；只使用我提供或有权使用的素材。我没有提供 Logo 或片尾时先省略。
删除无意义的停顿、重录和啰嗦，保留完整原声、因果和条件，不能把半个字剪掉。不清楚的术语先标记并问我。
先做语义粗剪，再加入相关字幕、重点动画和轻音效，音乐以人声清楚为准。特效服务于讲解；不要为了套模板改写事实。
本次先交付 MP4 和本版已有字幕；封面、文案及其他交付物另按我明确要求制作。
导出后检查声音、接缝、字幕、画面及文件是否能正常播放，报告真实保存位置和未完成检查，展示给我确认。
仓库中讲师的历史确认和长期授权不适用于我。未经我明确同意，不把我的视频或本人 Demo 上传到 GitHub、不公开内容，也不购买或调用付费生成及导出服务。需要为制作上传到云端剪辑工具时，先说明上传范围。
本次不上传社交平台、不替我发送消息、不发布或排程；遇到收费要求先说明用途和费用。
```

完整制作顺序：检查原片 → 转写及术语核对 → 语义粗剪 → 确定最终时间 → 添加相关画面、字幕和声音 → 实际导出 → 观看及听审 → 你确认。

比例控制视频画幅；两种封面不代表一定需要导出两版视频。每支新片先明确比例，同片修改不必重复确认。

## 七、看模板、选特效

先按内容挑表达方式：讲步骤用流程动画，比较方案用对比，讲数据用有依据的图表，演示电脑操作用局部放大和重点引导。

[全部模板、分类与来源](https://github.com/Isaac3113/talking-head-editor/blob/main/templates/README.zh-CN.md)

想在电脑打开现有 HTML 模板中心，在源码根目录运行：

```powershell
Set-Location "C:\Codex Workspace\talking-head-editor"
python scripts/serve_template_gallery.py
```

打开命令实际显示的地址。默认端口是 8768，可能因启动参数不同而变化；`127.0.0.1` 和 `localhost` 都表示访问者自己的电脑。浏览完成后，在运行命令的终端按 Ctrl+C 停止服务。

GitHub 保存 HTML 和 Demo 文件，但 GitHub 文件页不会自动运行这份交互网页。网页及配套 `demos` 目录必须保持完整；官网预览还需要能访问对应网络。

看到 Demo、取得模板源码、装好运行环境、用自己的原片验证，是不同阶段。MotionGit 官方预览不等于已经附送该模板的个人 `.motion` 包；真人抠像和多角度效果也不一定只换一个视频文件就能复用。

[看 Demo、制作特效和剪整片的区别](https://github.com/Isaac3113/talking-head-editor/blob/main/docs/GETTING_STARTED.zh-CN.md)

## 八、检查成片与提出修改

第一次至少确认：能完整播放；字音没有被切断；字幕术语正确；音乐没有盖住人声；画面比例正确；导出的文件确实在你的目录中。

工程里能预览，不等于已经导出 MP4；文件存在，也不等于全片已经看过、听过。最终导出后仍要人工确认内容。

需要局部修改时，直接给成片时间和具体问题，例如：

```text
请在同一工程修改刚才的成片：
00:18，“AI”最后的声音被切掉，请恢复完整字音。
00:42，背景音乐太响，请只降低音乐。
其余部分沿用现有工程与已确认内容。完成后重新导出本版，验证后更新我的交付文件，并说明保存位置。
```

## 九、以后怎样更新？

代码和规则可通过 GitHub 更新，原片、依赖、登录授权及具体云工程需要另行核对。

把以下内容发给 Codex，比直接覆盖旧文件更稳妥：

```text
请更新我电脑上的 talking-head-editor。
先定位现有源码和实际安装的 Skill，检查分支、Git 状态、本地改动和安装归属，再按 docs/CROSS_COMPUTER_UPDATE.md 安全获取更新。
不要删除我的原片、工程、配置和成片，不强制覆盖本地修改，也不要安装第二份同名 Skill。
代码更新后，按现有安装目标同步 Skill，检查基础环境和工具连接。报告实际更新的内容、需要我重新授权的部分及未验证项。
```

[安全更新与换电脑说明](https://github.com/Isaac3113/talking-head-editor/blob/main/docs/CROSS_COMPUTER_UPDATE.md)

## 十、遇到问题先看这里

| 情况 | 先检查什么 |
| --- | --- |
| GitHub 404／clone 被拒绝 | 登录账号、是否接受邀请、是否有仓库权限 |
| python 或 git 找不到 | 本机是否安装，终端是否需要重新打开 |
| Skill 没出现 | 实际安装路径、客户端是否发现、是否有同名重复安装 |
| ChatCut 连不上 | 自己的插件、登录授权及本次实际工具连接 |
| 工程提示 relink／缺素材 | 原片或外部素材是否还在原位置，需要重新关联哪些文件 |
| Demo 能看，特效不能生成 | 所选引擎、依赖、自己有权使用的包及素材是否齐全 |
| 不能导出／提示额度 | 当前工具的实际错误、账号权限、格式和套餐；不是看到提示就直接购买 |
| localhost 发给别人打不开 | 这是本机地址，对方需自己启动服务或使用另行部署的网站 |

排错时提供：你进行到哪一步、完整错误文字、软件版本、当前工程与相关文件位置。登录密码、Key 和其他凭据不需要发到聊天或 GitHub。

## 完整资料入口

- [项目主页](https://github.com/Isaac3113/talking-head-editor)
- [完整中文新手入门](https://github.com/Isaac3113/talking-head-editor/blob/main/docs/GETTING_STARTED.zh-CN.md)
- [安装说明](https://github.com/Isaac3113/talking-head-editor/blob/main/docs/INSTALL_SKILLS.md)
- [总 Skill](https://github.com/Isaac3113/talking-head-editor/blob/main/skill/talking-head-editor/SKILL.md)
- [模板与分类](https://github.com/Isaac3113/talking-head-editor/blob/main/templates/README.zh-CN.md)
- [换电脑与更新](https://github.com/Isaac3113/talking-head-editor/blob/main/docs/CROSS_COMPUTER_UPDATE.md)

文档核对：2026-11-02。Windows 命令按当前仓库脚本核对；未将此教学视为所有学员电脑已实测通过。界面、套餐和第三方模板会更新，具体以你实际工具和对应官方文档为准。

## 工具官方资料

- [OpenAI：Skill 说明与当前发现目录](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI：桌面客户端与本机工作入口](https://learn.chatgpt.com/docs/app)
- [Git for Windows](https://git-scm.com/downloads/win)
- [Python for Windows](https://www.python.org/downloads/windows/)
- [ChatCut](https://www.chatcut.io/)

本指南不是 MotionGit 官方产品文档。原创代码与规则及第三方内容的使用范围，分别查看仓库 [LICENSE](https://github.com/Isaac3113/talking-head-editor/blob/main/LICENSE) 与 [THIRD_PARTY.md](https://github.com/Isaac3113/talking-head-editor/blob/main/THIRD_PARTY.md)。
