# AI Cut 中文新手入门：学习自动剪辑与使用模板

> 首次从领取入口来的学员，先读[可复制到 Notion 的领取与安装教学](NOTION_GUIDE.zh-CN.md)：公开源码直接下载、Windows 新装、自己的工具账号及首支试剪。本文保留较详细的环境与模板说明。

这个项目专门处理真人知识口播、教学、营销方法、系统实操和长访谈切片。先选择自己的目标；只想看效果的人不用先安装完整剪辑环境。

| 入口 | 阅读顺序 |
| --- | --- |
| 学习自动剪辑 | [学员教学](NOTION_GUIDE.zh-CN.md) → 取得源码与安装 → 连接自己的剪辑工具 → 第一支口播 → 导出检查 |
| 选择、使用特效模板 | [展厅](https://aicut.agi-top.com)或[逐项说明](../templates/README.zh-CN.md) → 选具体效果 → 准备输入与依赖 → 重渲并检查 → 放入自己的剪辑工程 |

模板条目统一说明效果预览、适用内容、所需素材、可改参数与限制、怎样使用、当前可用与验证状态、来源和许可。用途分类方便选择，来源/版本标签方便核对；每个模板的实际支持范围以条目证据为准。

## 1. 取得文件

当前仓库开放下载。浏览、下载 ZIP 与 HTTPS clone 无需 GitHub 邀请或登录。推荐 clone 以便以后更新；Code → Download ZIP 适合只取文件，解压目录不能直接 git pull。将 active repo 放在非 OneDrive 的本机文件夹。

```powershell
New-Item -ItemType Directory -Force -Path "C:\Codex Workspace" | Out-Null
Set-Location "C:\Codex Workspace"
git clone https://github.com/Isaac3113/ai-cut.git
Set-Location ai-cut
```

如果已经有同一个 repo，先检查本地修改和分支，按[安全换电脑说明](CROSS_COMPUTER_UPDATE.md)更新，不要为更新删除旧目录或强制覆盖。

## 2. 先看效果：线上展厅或本机浏览

直接打开 [AI Cut 线上模板展厅](https://aicut.agi-top.com)，无需安装剪辑环境或自己购买域名。需要本机浏览完整目录时，电脑有 Python 3.11 或 3.12 后，在仓库根目录运行：

```powershell
python scripts/serve_template_gallery.py
```

打开命令显示的地址，默认是 `http://127.0.0.1:8768/index.html`。搜索中文名称、选择分类、点视频播放；Ctrl+C 停止本机服务。若默认端口已被占用，可换一个端口：

```powershell
python scripts/serve_template_gallery.py --port 8769
```

浏览目录只使用 Python 标准库，不需要安装项目依赖、Node、ChatCut、ASR 或 MotionGit 个人包。官方在线图片和视频需要联网；已在本地的 Demo 可以离线播放。

复制给另一人时必须保留下面的相对结构；只发 index.html 会缺视频。脚本位于 scripts/，它会读取同一份 docs/template-gallery/。源码和媒体目录不是你电脑的 URL。

```text
交付根目录/
├─ scripts/serve_template_gallery.py
└─ docs/template-gallery/
   ├─ index.html
   └─ demos/ （保留所有子目录与文件）
```

HTML 已内嵌数据、样式和脚本。推荐以上 HTTP 打开方式；直接双击 HTML 的表现取决于浏览器的本地文件规则，不承诺所有浏览器均相同。127.0.0.1／localhost 都指向当前访问者自己的电脑，不能用来让别人连接你这台电脑。

### 在同一个中心比较本人、官网与不同画幅

后续本人Demo与风格对比都回到这一份模板中心，不另开长期独立HTML。顶部「本人Demo」是同一目录的筛选入口，也可访问`index.html#owner-demos`；四层分类与用途分类保持。来源和画幅筛选会限制实际可播放版本，每张卡的「演示版本」可切换本人横／竖版及官网示例，版本、说明和QA随选择更新。

「本人」依据明确的肖像授权或本人案例记录；`kind=own`仅表示自制，Logo、图表等自制演示不会因此成为本人Demo。库中精选本人MP4保持静音；官网视频依自己的音轨与网络状态播放。

本机需要在同一卡播放原声时，在repo根建立被Git忽略的`gallery.local.json`，将已登记的本人案例映射到自己有权使用的本机MP4，再启动原服务。例如将下方媒体目录和文件名换成实际值：

```json
{
  "schema": "talking-head-gallery-local/1",
  "media_root": "<本机原声媒体目录>",
  "clips": {
    "demos/integrated/owner-native-20261028/paper/portrait.mp4": "纸面透视_9x16.mp4"
  }
}
```

服务只开放明确映射、仍位于媒体目录内的已登记本人MP4，不开放整个资料目录；网页不接收原始绝对路径。有实际原声文件时标「原声版·仅本机」，无本机配置、媒体未到位或静态打开时回退已登记静音样例。Git pull不会复制此本机映射或原声文件；另一台电脑须另行核对媒体与配置。个人包、Key及原片仍不进入模板中心。

## 3. 自己重渲效果：按选定引擎准备

看 Demo 和生成新动画是两个阶段。Remotion／HyperFrames 需要相应 Node/npm、浏览器、FFmpeg、字体及许可；使用根 README 和[安装说明](INSTALL_SKILLS.md)，不要复制别人电脑的node_modules、虚拟环境或运行缓存。

已有动画引擎的安装、检查与小样渲染入口如下。在仓库根目录执行，只选择本次需要的一组；源码不附你的原片或个人头像。`CustomerJourney`是已有四步教学示例，不是每条新片的固定文案或时长。

```powershell
.\extensions\remotion-vd44\run.ps1 -Action Install
.\extensions\remotion-vd44\run.ps1 -Action Check
.\extensions\remotion-vd44\run.ps1 -Action Render -Composition CustomerJourney
```

```powershell
.\extensions\hyperframes-vd44\run.ps1 -Action Install
.\extensions\hyperframes-vd44\run.ps1 -Action Doctor
.\extensions\hyperframes-vd44\run.ps1 -Action Check
.\extensions\hyperframes-vd44\run.ps1 -Action Render
```

脚本支持显式Node/npm路径；Remotion可传BrowserPath，HyperFrames可传FfmpegDirectory，具体参数读相应run.ps1。先检查输出中的真实状态，缺依赖时完成本机安装，不借用讲师电脑路径或假定另一电脑已能运行。55项代码库的独立入口及参数见[模板库说明](../extensions/remotion-vd44/TEMPLATE_LIBRARY.md)。

MotionGit 先准备自己有权使用的原始.motion，并复制仓库的motiongit.example.json为被Git忽略的motiongit.local.json，填写本机package与node路径。不要把Key粘到JSON、聊天或Git。

```powershell
.\.venv\Scripts\python.exe scripts/motiongit_adapter.py start --summary
```

该命令需已按下一节准备本仓库Python环境；它核验原包并返回本机回执位置。让Codex读取该回执提供的公开制作入口，再按所选包执行：读取guide/schema → 创建新实例 → 检查依赖和参数 → 制作计划 → 审看真实预览 → 渲染 → 检查实际输出。每个包的输入与命令以自己的公开合同为准，不把旧案例的路径、逐词时间或审核标记直接照抄。

模板中心的70控件各有一个代表变体实测，210变体没有全部单独渲染。19真人效果还需要新片自己的同源视频、逐帧对应人像遮罩和时间映射，不能仅替换一个文件名；源码README明确保留的样片专用逻辑须按新片适配。

## 4. 剪自己的知识口播

在仓库根目录安装本机Python环境与唯一总Skill：

```powershell
.\scripts\bootstrap.ps1
.\.venv\Scripts\python.exe scripts/install_skill.py
.\.venv\Scripts\python.exe -m talking_head_editor.cli doctor
```

已有安装被修改或属于另一个源码目录时，安装器会停止保护原文件，先比较再协调。doctor只报告本机环境，不证明ChatCut已连接或成片已完成。

准备自己的原片、本条视频比例、术语、Logo/品牌素材及交付目标。让Codex使用ai-cut，按照[完整流程](../skill/ai-cut/references/approved-workflow.md)工作。当前默认主路线是ChatCut，需自己的插件、账号、既有工程定位和当场可用工具；缺连接时先说明，继续独立的素材核对，不把本地Demo冒充完整在线工程。

原声语义粗剪 → 冻结最终时间 → 添加相关动画/字幕/SFX → 实际导出 → 全片观看及听审 → 用户确认。外部动画是画面素材，其内部文字可能需要修改源码重渲；不一定成为ChatCut原生可编辑文字层。

本仓库包含Isaac已确认的个人预设。其他使用者先明确自己的速度、品牌、片尾、命名、交付和发布要求；不得自动使用Isaac的媒体、账号或内容认可。旅行Vlog与剧情片的专用自动剪辑流程尚未实现。

## 5. 把自己的效果做成通用模板

模板使用与模板制作是两件事。指定一段好效果后，先核对是现成模板、自行实现还是混合方案，再决定提炼范围。自制部分需要保留源码、分离内容与实现、声明可改参数及边界，并使用不同内容实际预览和导出，才有依据称为可复用。

[通用模板制作教学](TEMPLATE_AUTHORING.zh-CN.md)提供来源核对、参数设计、验证、`.motion` 打包和分享说明。现有官方示例和本人 Demo 不因整理目录就变成已完成通用化的模板；学员的账号、素材和公开授权仍须自己提供。

## 6. 常见问题

| 情况 | 判断和处理 |
|---|---|
| 仓库404或clone拒绝 | 核对 Isaac3113/ai-cut 网址、网络、代理或 GitHub 服务状态；无需申请仓库权限 |
| python命令找不到 | 先安装/选择本机Python；不要把未安装解释成项目失败 |
| 目录可打开但视频缺失 | 核对demos目录、相对路径与文件完整性；官方链接另需网络 |
| localhost别人打不开 | 直接分享 https://aicut.agi-top.com；本机版则需对方取得完整文件并启动自己的服务 |
| 目录能看但不能重渲 | 另查选定引擎、依赖、模板包、素材和授权，不能从Demo推断已配置 |
| 有原片但真人抠像缺失 | 同源遮罩和新时间映射需先制作与检查，不从旧片借人物 |
| 图表、价格、评论是示例 | 正式内容必须换成有依据的数据或清楚保留示例身份 |
| 想公开展示网站 | 按[发布准备约定](RELEASE_PREPARATION.md)单独处理，不通过更改localhost实现 |

## 验证范围

本机已有目录、动画代表小样和部分案例验证；不把这些结果说成所有变体、任意新片、另一台电脑、所有浏览器或完整连续视听均已通过。原始视频、授权账号和运行依赖不随Git自动恢复。
