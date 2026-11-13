# AI Cut｜AI知识口播自动剪辑特效模板使用教学

AI Cut 包含两部分：**学习 AI 怎样剪好一支知识口播**，以及**按内容选择、使用特效模板**。你可以从原片开始完成整支视频，也可以只挑一个合适效果，放进自己的剪辑工程。

**公开版默认交付到你指定的本机目录：实际 MP4、本版已有字幕，以及明确需要的封面。** 使用 AI Cut 不需要 Google Drive、讲师的 Content Management OS、发布账号或私人 `fb-content` Skill。讲师的云盘归档与审核后发布属于独立私人流程，不随本仓库提供，也不是剪辑或导出的前置条件。

AI Cut 已开放下载：无需向讲师提交 GitHub 用户名、等待邀请或申请仓库权限。浏览、下载 ZIP 和 HTTPS clone 均可直接进行；剪辑工具仍使用你自己的账号。

## 先看 AI Cut 自己的特效与本人 Demo

这里不只有 MotionGit 官方示例。先分清通用自制模板、已有真人效果分支、本人套用官方案例，以及官方／第三方目录，就容易找到你想用的效果：

| 内容 | 直接入口与说明 |
| --- | --- |
| **AI Cut 通用自制模板：编辑画布** | [源码与使用说明](https://github.com/Isaac3113/ai-cut/blob/main/extensions/editorial-canvas/README.zh-CN.md) · [作者.motion包](https://github.com/Isaac3113/ai-cut/blob/main/templates/authored-packages/ai-cut-editorial-canvas-1.0.0.motion) · [参数、Demo 与实际状态](https://github.com/Isaac3113/ai-cut/blob/main/templates/categories/talk.md#ai-cut-editorial-canvas)：可按内容更换窗口、素材、图解与布局，不是19个旧分支的另一个名字 |
| **AI Cut 自制／适配真人特效（19 项）** | [19 项说明与源码](https://github.com/Isaac3113/ai-cut/blob/main/extensions/remotion-vd44/src/template-library/talking-head-effects/README.md)：包括剪纸描边、人物破框、杂志封面等，为本项目制作，部分复用第三方组件 |
| **本人套用官方模板的案例** | [打开本人 Demo 展厅](https://aicut.agi-top.com/#owner-demos)：画面与内容使用 Isaac 本人的素材，效果来源仍是官方 MotionGit，不改称原创 |
| **官方与第三方模板目录** | [全部分类与逐项说明](https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md)：按用途选择 MotionGit、Remotion 等来源的效果，并核对素材、参数、接入状态与许可 |

**只看 19 项真人特效：**打开[本人 Demo](https://aicut.agi-top.com/#owner-demos)，再点击来源分类「真人口播特效」。本人 Demo 也包含套用官方模板的案例，“画面里是本人”不等于“模板是原创”。

使用时换成你自己的素材，并适配真人抠像、画幅和出现时间。这 19 项是效果分支，不是 19 套已通用化的 `.motion` 包；看得到 Demo 与能在你的新视频上使用，需要分别检查。

## 风格与模板怎样选？

「风格」是一整支视频的视觉语言；「模板」是可重复使用的场景或动作。选择一种风格，不等于每集都播放同一套设计。

例如「编辑画布式知识口播」会让真人窗口、真实素材和流程图在连续画布里讲解；一片可用文件展开，另一片用素材墙、窗口对照或状态流转。保持层级、节奏与窗口关系，让每片的内容决定画面，不能只换标题和颜色。旧知识图解、文字 B 和其他效果仍可单独选用。

[编辑画布风格说明](https://github.com/Isaac3113/ai-cut/blob/main/skill/ai-cut/references/editorial-canvas-style.md) · [通用模板源码](https://github.com/Isaac3113/ai-cut/blob/main/extensions/editorial-canvas/README.zh-CN.md)

```text
请使用 $ai-cut，采用「编辑画布式知识口播」方向。
原片：[我自己的MP4完整路径]
视频比例：[本条明确选择的比例]
内容重点：[填写]
请保留原声原意，按讲解选真实素材、连续图解与真人窗口。
风格保持一致，但为本片重新设计构图、图解机制、素材与转场，不沿用固定场景顺序或只换字换色。
先核对模板的实际运行入口、素材、参数和许可；不要把官方场景或讲师本人Demo当成我的原创素材。
交付目录：[我自己的目录]
```

源码可调用、`.motion`文件已打包、MotionGit官方平台已导入、你的新电脑已安装是不同状态，须看具体模板的说明与验证范围；不能因为扩展名是`.motion`就推定已官网审核或任意官方工具能直接执行。

## 选择你的学习入口

| 你想完成什么 | 从哪里开始 |
| --- | --- |
| 学习自动剪辑：从原片到成片 | 按本页第一至第六节准备工具、安装 Skill，用 20～30 秒口播试剪；再学习修改和更新 |
| 选择、使用模板：先找一个效果 | 先看[线上模板展厅](https://aicut.agi-top.com)和本页第七节，再按[逐项说明](https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md)准备自己的输入 |

仓库网址保留 [Isaac3113/ai-cut](https://github.com/Isaac3113/ai-cut)，总 Skill 仍叫 `ai-cut`。模板网页用于选效果，实际制作还要使用对应工具与运行环境。

## 一、这个 Skill 适合剪什么？

适合真人知识口播、AI 教学、营销方法、系统操作演示，以及从长访谈中整理单一主题短片。

它会指导 AI 理解内容、删掉无用重复和停顿、整理字幕，并按讲解选择重点字、放大、流程动画、音乐和音效。原则是保留你的原声和原意，不把字音剪断。

Skill 是 AI 的工作流程与规则。实际制作还需要能读取本机文件的 Codex、剪辑工具、自己的账号和素材。它不是把一句提示词贴进任意聊天窗口就能运行的软件，也不是所有视频类型的通用一键剪辑器。旅游 Vlog、剧情和多场景混剪，需要另选制作路线。

## 二、直接取得项目

1. 打开下方公开 GitHub 项目主页，无需申请权限。
2. 推荐让 Codex 使用 Git clone 下载，方便以后安全更新。
3. 也可以点击 Code → Download ZIP，解压后阅读教学；ZIP 不包含 Git 历史，不能直接用 git pull 更新。
4. 只读浏览、下载与 HTTPS clone 无需 GitHub 账号；提交代码或提 Issue 时再使用自己的账号。

[项目主页与完整文件](https://github.com/Isaac3113/ai-cut)

看到 404、Repository not found 或下载失败时，先核对网址是否为 Isaac3113/ai-cut、网络和 GitHub 服务状态；不要反复重新安装软件。

以下 GitHub 教学链接均可直接打开。原创代码与规则采用 MIT，第三方模板、媒体、肖像和品牌保留各自的许可；公开源码不附送账号或付费服务。

## 三、电脑需要准备什么？

这份入门教学以 Windows 为主，其他系统请先让 Codex 检查兼容性，不直接照抄 Windows 命令。

| 准备项 | 用途 |
| --- | --- |
| 能访问本机文件的 Codex 客户端及自己的账号 | 阅读规则、检查环境、调用剪辑工具 |
| Git | 下载公开源码，之后安全更新代码 |
| Python 3.11 或 3.12 | 运行本项目的安装及辅助脚本 |
| 自己的 ChatCut 插件、账号及实际可用连接 | 本教学默认使用的剪辑工程和导出路线 |
| 自己的 MP4 | 先用 20～30 秒清晰口播验证流程 |

Codex、ChatCut、云端转写、生成和导出的可用功能与费用，取决于各自的账号、当前套餐及额度。下载 Skill 不附送这些服务额度。

首次不必安装所有动画引擎，也不必先安装本地语音识别模型。先完成基础试剪，遇到具体特效需求时，再按文档准备 Node、Remotion、HyperFrames 或自己的 MotionGit 包。

本教程只安装公开的 `ai-cut` 剪辑入口。你认可成片后，默认任务即完成，不会自动创建云盘文件夹、登录讲师系统或提交社媒发布。若另需营销文案，明确提出平台、品牌与用途，AI 再按你的资料准备；不套用讲师的固定文案或首评。

## 四、安装到自己的电脑

建议源码目录：`C:\Codex Workspace\ai-cut`。这是推荐示例，不是讲师电脑的共享文件夹；不要把正在运行的源码、依赖和缓存放进 OneDrive 同步目录。

### 方法 A：让 Codex 带你安装

打开能访问本机文件的 Codex，复制以下内容。下载本公开仓库不需要先登录 GitHub；若其他工具需要账号，请在官方窗口登录你自己的账号。

```text
请帮我安装 ai-cut。我使用 Windows，直接从以下公开 GitHub 仓库下载，无需申请仓库权限。
仓库：https://github.com/Isaac3113/ai-cut
建议源码目录：C:\Codex Workspace\ai-cut

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
git clone https://github.com/Isaac3113/ai-cut.git
Set-Location "C:\Codex Workspace\ai-cut"
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe scripts/install_skill.py --target "$env:USERPROFILE\.agents\skills\ai-cut"
.\.venv\Scripts\python.exe -m talking_head_editor.cli doctor
```

这里的 `--target` 使用当前官方文档列出的用户级 `.agents/skills` 目录。旧客户端或既有安装可能使用其他位置，请先检查，保留一份有明确归属的有效安装。安装器提示既有 Skill 被修改或来源不同，先比较处理，不要强删覆盖。

任何一步报错，先停在该步，把命令和完整错误发给 Codex。不要忽略失败继续往下执行，也不需要为了本项目全局放宽脚本执行策略。

完成后让 Codex确认能发现 `ai-cut`，并读到本仓库的规则。新 Skill 没出现时可重启客户端再检查。`doctor` 成功不代表 ChatCut 已连接，也不代表任何新视频已经完成。

[详细环境、动画及辅助 Skill 安装](https://github.com/Isaac3113/ai-cut/blob/main/docs/INSTALL_SKILLS.md)

## 五、先连接自己的剪辑工具

当前默认主路线是 ChatCut：安装并授权你自己的插件，登录自己的账号，再让 Codex 检查本次实际可用的工具。

Skill 安装、账号登录、工具可调用、素材可读、工程可导出，是不同检查项。Git clone 不会复制讲师的登录状态、原片、音乐、片尾、MotionGit 私人包或云工程。

如果工具连接不上，先完成连接检查；若选择改走本机制作，应明确新的路线和输出限制，不能把静音 Demo 当作已完成的口播成片。

## 六、剪第一支视频

先准备一段 20～30 秒的自有口播，记下 MP4 的完整路径。将下面的方括号内容换成你的真实资料，填写视频比例后发送。

```text
请使用 $ai-cut 帮我做第一次知识口播试剪。

原片完整路径：[填写我的 MP4 完整路径]
本条视频比例：[明确填写 9:16、16:9、1:1 或沿用原片比例]
主题：[填写主题，或写“看完后按实际内容命名”]
重点保留：[我希望观众记住的内容]
必须保留的术语／数字：[填写；没有则写“无”]
输出目录：[填写我自己的交付目录]

请先核对规则、实际工具和原片，再开始制作。仓库中 Isaac 的品牌、固定片尾、速度、路径和编号都只是他的个人预设，不自动套用到我。
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

## 七、模板是做什么的？剪辑时怎样用？

**模板展厅展示的是你以后剪辑时，可以选择使用的画面包装与动画效果。** 先看喜欢的效果，再让 AI Cut 根据你的视频内容制作，并放到对应的讲解位置。

[打开 AI Cut 模板展厅，直接看效果](https://aicut.agi-top.com)

模板入口按真人口播、录屏与操作教学、流程与时间线、数据与对比、产品与案例展示、标题与重点字、转场与片尾、视觉与背景组织。来源类型、版本和技术分类保留为进一步筛选资料。

**每条模板用同一顺序讲解：**

1. 效果预览：先看实际 Demo 和画幅。
2. 适用内容：适合讲什么，以及不适合什么。
3. 所需素材：你要准备哪些文字、图片、视频或数据。
4. 可改参数与限制：能换什么、支持多少内容、哪些比例或时长已确认。
5. 怎样使用：复制该条的指令，填入自己的内容。
6. 当前可用与验证状态：是已接入、还需适配，还是仅有官方参考/尚未开放。
7. 来源和许可：模板来自哪里，哪些内容允许修改或分享。

未核对的参数会明确写待核对。能看到 Demo，不代表每个学员的电脑已装好依赖，也不表示所有官方模板包已经包含在仓库。

例如，你在口播里说“先吸引客户，再预约，最后跟进”，AI 可以把这三个真实步骤做成逐项出现的流程动画。画面里的文字、人物和素材会按你的内容适配，原声与讲解逻辑仍然保留。

| 你的视频讲什么 | 可以选用什么效果 |
| --- | --- |
| 操作步骤、先后关系 | 步骤条、流程图、时间线动画 |
| 两种方案的差别 | 左右对比、前后对比 |
| 有依据的数字或变化 | 数字动画、柱状图、趋势图 |
| 电脑操作、软件教学 | 局部放大、重点聚焦、操作引导 |
| 重要观点或关键词 | 重点字、标题动画、强调效果 |

**两种用法都可以：**

- 不知道选哪个：给 AI 原片，让它按实际内容选择合适的效果。
- 已有喜欢的：把展厅里的模板名称或编号告诉 AI，并说明想用在哪一段。

套用时会使用你自己的原片、文字、数据，以及你有权使用的图片和 Logo。展厅中的讲师本人 Demo 是效果示范；使用时需要换成你的素材，真人抠像、画幅和出现时间也要按你的原片调整。

制作顺序是：理解原片与精剪 → 选择合适效果 → 适配素材、文字、比例和时长 → 对齐讲解加入剪辑工程 → 导出并检查。网页负责展示效果，实际制作由你连接的剪辑工具和所需动画环境完成；不用每一段都加特效，也不会为了凑模板编造步骤或数据。

**看展厅时留意状态：**“官方示例”供选型参考；“本人 Demo”展示已经做过的适配案例；“已接入”表示已有调用路径，新电脑和新视频仍须检查依赖与素材。官方预览不等于仓库已附送对应个人 `.motion` 模板包，未接入的效果需要先核对取得方式、许可和运行条件，再试做。

安装完成后，可以在交付原片时加上这段：

```text
请使用 $ai-cut，根据这支视频的实际讲解选择合适的模板效果。
我喜欢的模板名称或编号：[填写；没有则写“由你按内容选择”]
希望使用的位置或内容：[填写；没有则写“由你判断”]

先读懂内容和完成精剪，再用我自己的素材、文字和真实数据适配效果，对齐原声与已确认的视频比例。
先检查所选模板是否已接入、依赖及素材是否齐全；未接入时先说明适配方案，遇到收费要求先告诉我。
特效要帮助观众理解，不要每段都硬套；完成后展示实际效果让我确认。
```

[完整模板分类与来源](https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md) · [看 Demo、制作特效和剪整片的区别](https://github.com/Isaac3113/ai-cut/blob/main/docs/GETTING_STARTED.zh-CN.md)

### 在自己电脑浏览同一份模板展厅

[直接打开 AI Cut 线上模板展厅](https://aicut.agi-top.com)

这里可以查看分类、本人Demo和官网候选预览，供个人学习与免费交流，不用于业务获客或销售。浏览网页不需要先安装本机环境；[完整模板登记与来源](https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md)和公开源码均可直接查看。线上使用已登记静音Demo，官方示例依赖外部网络。

如果需要在自己电脑打开同一份HTML模板中心，在源码根目录运行：

```powershell
Set-Location "C:\Codex Workspace\ai-cut"
python scripts/serve_template_gallery.py
```

打开命令实际显示的地址。默认端口是 8768，可能因启动参数不同而变化；`127.0.0.1` 和 `localhost` 都表示访问者自己的电脑。浏览完成后，在运行命令的终端按 Ctrl+C 停止服务。

GitHub 保存 HTML 和 Demo 文件，但 GitHub 文件页不会自动运行这份交互网页。网页及配套 `demos` 目录必须保持完整；官网预览还需要能访问对应网络。

### 想把自己的好效果保留下来？

先告诉 AI 哪支视频、哪一段，核对它是套用现成模板、自行实现还是混合制作。自制效果可以进一步整理成通用模板：把文案、素材、颜色和支持的数量/比例做成可替换输入，换不同内容验证，再编写说明与打包。换颜色或换人物本身不等于已完成通用化。

[从一段效果到可复用 MotionGit 模板：完整教学](https://github.com/Isaac3113/ai-cut/blob/main/docs/TEMPLATE_AUTHORING.zh-CN.md)

模板源码、自己的示例、个人原片和凭据分别处理。分享给别人前先明确哪些文件有权公开；不直接上传含个人 Key 的模板包。

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
请更新我电脑上的 ai-cut。
先定位现有源码和实际安装的 Skill，检查分支、Git 状态、本地改动和安装归属，再按 docs/CROSS_COMPUTER_UPDATE.md 安全获取更新。
不要删除我的原片、工程、配置和成片，不强制覆盖本地修改，也不要安装第二份同名 Skill。
代码更新后，按现有安装目标同步 Skill，检查基础环境和工具连接。报告实际更新的内容、需要我重新授权的部分及未验证项。
```

[安全更新与换电脑说明](https://github.com/Isaac3113/ai-cut/blob/main/docs/CROSS_COMPUTER_UPDATE.md)

## 十、遇到问题先看这里

| 情况 | 先检查什么 |
| --- | --- |
| GitHub 404／clone 被拒绝 | 仓库网址、网络或代理、GitHub 服务状态；本仓库不要求邀请 |
| python 或 git 找不到 | 本机是否安装，终端是否需要重新打开 |
| Skill 没出现 | 实际安装路径、客户端是否发现、是否有同名重复安装 |
| ChatCut 连不上 | 自己的插件、登录授权及本次实际工具连接 |
| 工程提示 relink／缺素材 | 原片或外部素材是否还在原位置，需要重新关联哪些文件 |
| Demo 能看，特效不能生成 | 所选引擎、依赖、自己有权使用的包及素材是否齐全 |
| 不能导出／提示额度 | 当前工具的实际错误、账号权限、格式和套餐；不是看到提示就直接购买 |
| localhost 发给别人打不开 | 这是访问者自己的电脑地址；看效果可直接用 https://aicut.agi-top.com ，本机版本则需自行启动服务 |

排错时提供：你进行到哪一步、完整错误文字、软件版本、当前工程与相关文件位置。登录密码、Key 和其他凭据不需要发到聊天或 GitHub。

## 完整资料入口

- [线上模板展厅：直接看分类与Demo](https://aicut.agi-top.com)
- [项目主页](https://github.com/Isaac3113/ai-cut)
- [完整中文新手入门](https://github.com/Isaac3113/ai-cut/blob/main/docs/GETTING_STARTED.zh-CN.md)
- [安装说明](https://github.com/Isaac3113/ai-cut/blob/main/docs/INSTALL_SKILLS.md)
- [总 Skill](https://github.com/Isaac3113/ai-cut/blob/main/skill/ai-cut/SKILL.md)
- [模板与分类](https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md)
- [把自制效果整理成通用模板](https://github.com/Isaac3113/ai-cut/blob/main/docs/TEMPLATE_AUTHORING.zh-CN.md)
- [换电脑与更新](https://github.com/Isaac3113/ai-cut/blob/main/docs/CROSS_COMPUTER_UPDATE.md)

文档核对：2026-11-03。Windows 命令按当前仓库脚本核对；未将此教学视为所有学员电脑已实测通过。界面、套餐和第三方模板会更新，具体以你实际工具和对应官方文档为准。

## 工具官方资料

- [OpenAI：Skill 说明与当前发现目录](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI：桌面客户端与本机工作入口](https://learn.chatgpt.com/docs/app)
- [Git for Windows](https://git-scm.com/downloads/win)
- [Python for Windows](https://www.python.org/downloads/windows/)
- [ChatCut](https://www.chatcut.io/)

本指南不是 MotionGit 官方产品文档。原创代码与规则及第三方内容的使用范围，分别查看仓库 [LICENSE](https://github.com/Isaac3113/ai-cut/blob/main/LICENSE) 与 [THIRD_PARTY.md](https://github.com/Isaac3113/ai-cut/blob/main/THIRD_PARTY.md)。
