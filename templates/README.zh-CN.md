# 中文剪辑模板中心

由四份固定基线和独立接入记录生成。更新后运行 `scripts/build_template_gallery.py --strict`，不要手工维护另一套重复清单。

本次B版获认可的是局部重点文字效果。目录完整性、实际运行和新片验收分别记录；有Demo不代表自动适合口播。

| 层级 | 数量 | 计数说明 |
|---|---:|---|
| 官网集合 | 72 | 基线72项，加已验证的新候选；不是全站总数 |
| 官网控件 | 70 | 原包基线70项/210变体冻结，新接入另记版本；不代表所有变体实测 |
| 代码库注册项 | 55 | 基线55注册项/52实现基础，新接入按来源区分 |
| 真人特效分支 | 19 | 基线19分支；不是完整剪辑系统 |
| 本片接入记录 | 4 | 版本与本人Demo记录，不加入上方模板条目总数 |

## 浏览方式

GitHub里可按下方中文分类直接打开每条Demo；在本机运行以下命令打开可搜索、可播放的完整目录：

```powershell
Set-Location "C:\Codex Workspace\talking-head-editor"
.\.venv\Scripts\python.exe scripts/serve_template_gallery.py
```

浏览器访问命令返回的本机地址。官网示例需要联网，本地演示随仓库同步。

[分类动画预览](../docs/template-gallery/CATEGORIES.md) · [来源与中文化说明](PROVENANCE.zh-CN.md) · [路线边界](../skill/talking-head-editor/references/editing-routes.md) · [模板选择规则](../skill/talking-head-editor/references/template-selection.md)

## 官网模板与片段

### 产品宣传与教程

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 多屏拼贴 · 品牌宣传 `mg-style-128610` | 用多屏拼贴、版面切换和品牌收尾展示产品与创作流程，适合品牌介绍和工具宣传。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/585/draft-zh-78bba5fd21f6.mp4) |
| 像素闯关 · 产品宣传 `mg-style-252912` | 像素城市、角色闯关和复古游戏音色组成产品介绍，适合数字工具与功能说明。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/586/draft-zh-b8792f9887ad.mp4) |
| 明暗快切 · 产品宣传 `mg-style-867595` | 明暗画面快速切换，结合大字和界面展示突出产品功能，适合节奏鲜明的宣传片。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/587/draft-zh-89b65ccfd5ce.mp4) |
| 流程演示 · 产品教程 `mg-style-670021` | 沿着选择模板、提供内容、生成视频的流程讲解产品使用，适合工具教程和上手演示。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/588/draft-zh-ca08bac0650e.mp4) |
| 模块拼贴 · 创作者宣传 `mg-style-452365` | 以模块拼贴呈现内容、素材和动画的组合关系，适合创作者工具与工作方式介绍。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/589/draft-zh-4d806a380523.mp4) |
| 工程蓝图 · 产品拆解 `mg-style-213827` | 以工程蓝图、结构示意和模块拆解展示产品组成，适合技术产品与工作流讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/590/draft-zh-308a5a69232f.mp4) |
| 发布会舞台 · 产品演示 `mg-style-667934` | 以发布会舞台和大屏展示组织产品演示，适合新品介绍、功能发布与品牌展示。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/591/draft-zh-958b2690a669.mp4) |
| 宣纸手卷 · 品牌叙事 `mg-style-394243` | 沿宣纸手卷展开品牌故事，以水墨意象和卷轴转场营造东方叙事。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/592/draft-zh-eba2e4e6f671.mp4) |
| 拼贴出场 · COLLAGE OPEN `mg-style-873` | 8.5 秒拼贴出场：9 块创作样张依次飞入拼贴墙，主张版块落位。可换品牌名、片头编号、强调色与两行标题。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/873/1.0.0-zh-6b7b749b3dc5.mp4) |
| 多屏墙换版 · WALL SWAP `mg-style-874` | 从面板擦除进入多屏拼贴墙，再切到「一个想法，四种看法」的分屏版面；8.6 秒展示多素材并置与版面切换。可换品牌名、片头编号、强调色与两行标题。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/874/1.0.0-zh-7831dd69bc6b.mp4) |
| 四种看法与片格 · VIEWS / STRIP `mg-style-875` | 「一个想法，四种看法」分屏版面切到横滚片格，真实晚霞树影与创作样张横向滚动；8.2 秒，适合多镜头并置与作品条带展示。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/875/1.0.0-zh-cd8ad1570460.mp4) |
| 产品与品牌 · PRODUCT → BRAND `mg-style-877` | 从面板擦除进入产品工作台（分镜/画布/调色/时间线同窗联动），再以墨色擦除收进棱镜标志、字标、主张与 CTA；14.4 秒，适合产品演示与品牌落版。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/877/1.0.0-zh-97910ee13592.mp4) |
| DEEP STAGE 产品讲解 `mg-style-648878` | 产品讲解动效：产品主屏推入并持续推近，3 个参数切片从 3D 空间错峰浮出、数字从 0 滚到终值，右下角人物小画中画入位。12 秒，适合产品卖点与参数讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/881/1.0.0-bf4d2ce8953d.mp4) |
| 多屏商务 · 动态图表 `mg-style-640261` | 固定20秒横屏商务短片，以多屏重排呈现团队、比较、趋势、构成与行动。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/891/0.1.1-candidate-zh-a43ff10687ec.mp4) |

### 口播与讲解

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 现代图文 · 口播讲解 · 竖屏 `mg-style-314486` | 用现代图文版式、文字强调和信息拆解配合口播，适合观点、证据与步骤讲解。 | 局部实测 | [演示1](../docs/template-gallery/demos/case-studies/approved-b-highlight.mp4) / [演示2](https://media.openaicut.com/previews/606/draft-zh-9086d86d6129.mp4) |
| 现代图文 · 口播讲解 `mg-style-336980` | 用现代图文版式、文字强调和信息拆解配合口播，适合观点、证据与步骤讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/605/draft-zh-99e0d21cfdd9.mp4) |
| 纸面透视 · 口播讲解 `mg-style-358192` | 用纸面透视、卡片层次和图文关系配合口播，适合方法拆解与结构化知识。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/607/draft-zh-613d68ad449f.mp4) |
| 纸面透视 · 口播讲解 · 竖屏 `mg-style-295450` | 用纸面透视、卡片层次和图文关系配合口播，适合方法拆解与结构化知识。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/608/draft-zh-927e16779f16.mp4) |
| 深色立体 · 多屏展陈 `mg-style-304634` | 用深色立体舞台、多屏和空间层次展示口播内容，适合产品、案例与媒体素材讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/609/draft-zh-a33d6dc67131.mp4) |
| 深色立体 · 多屏展陈 · 竖屏 `mg-style-569615` | 用深色立体舞台、多屏和空间层次展示口播内容，适合产品、案例与媒体素材讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/610/draft-zh-3200b44b2818.mp4) |
| 科技控制台 · 口播讲解 `mg-style-553346` | 用科技控制台、紫色玻璃质感与动态信息组件配合口播，适合技术与数据说明。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/611/2.5.7-zh-96b144413879.mp4) |
| 科技控制台 · 口播讲解 · 竖屏 `mg-style-738182` | 用科技控制台、紫色玻璃质感与动态信息组件配合口播，适合技术与数据说明。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/612/2.5.7-zh-a93efdfb29ba.mp4) |
| 鲜色角色 · 叙事讲解 `mg-style-960723` | 用鲜明配色、角色素材与叙事动效配合口播，适合故事、观点和情境解释。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/613/draft-zh-9454c905098e.mp4) |
| 鲜色角色 · 叙事讲解 · 竖屏 `mg-style-293151` | 用鲜明配色、角色素材与叙事动效配合口播，适合故事、观点和情境解释。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/614/draft-zh-6382724d35a0.mp4) |
| 活力海报 · 口播讲解 `mg-style-762139` | 用高对比海报、大字、清单和图形关系配合口播，含原生动画与新增组件，横屏独立编排。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/623/draft-zh-e8e43fce1aae.mp4) |
| 活力海报 · 口播讲解 · 竖屏 `mg-style-721489` | 用高对比海报、大字、清单和图形关系配合口播，含原生动画与新增组件，竖屏独立编排。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/624/draft-zh-11cf23913cdd.mp4) |
| 口播宣传动效 10 秒 `mg-style-854836` | 10 秒横版宣传动效：用一个数字、一句大字和品牌收尾，做短视频开场或产品预告片头。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/870/1.0.0-6dcf8b7863ca.mp4) |
| 3D 口播开场 `mg-style-554769` | 3D 口播开场 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/871/draft-40ddede10a69.mp4) |
| DEEP STAGE 口播主舞台 `mg-style-228996` | 口播主舞台动效：9:16 人物画面（CAM 01 / REC 取景标签）与主信息屏、竖向章节导航屏三层错峰入位，下三分之一人名条滑入，镜头全程缓慢横移。14 秒，适合口播正文与知识讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/880/1.0.0-2c8e89fea7a8.mp4) |
| DEEP STAGE 深境舞台完整版 `mg-style-838778` | 46 秒整条口播包装视频模板：深色 3D 舞台开场点火 → 口播主舞台（人物画面 + 信息屏 + 章节屏）→ 产品讲解 → 案例数据 → 媒体素材墙 → 收尾锁版，一条连续镜头运动。可替换品牌、标题、人名职务、三屏文案、产品/案例文案、10 句口播字幕与主色；随包可选音效轨（纯合 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/885/1.0.0-1d0d4dc1ea23.mp4) |
| Kit 2 · 口播动效包装（竖屏） `mg-style-583549` | 给真人出镜的口播视频套上完整动效包装：人像窗口在全屏、圆窗、卡片之间插值过渡，配 10 个段落可视化隐喻与深色药丸双语字幕（重点词橙色）。高潮锚词砸下（震屏+橙闪），片尾手写收尾。1080×1920/30fps，样例 36.5 秒，含程序化动作音效。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/890/1.0.0-a07dfe35eea8.mp4) |
| 突破边界 `mg-style-178707` | 纸面画框、破框转场与彩蛋动效。内测版，新文案适配仍在完善。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/896/draft-zh-995fe8c7aa31.mp4) |
| 字符剧场 `mg-style-148294` | 字符角色、作品墙与剧场式动画。内测版，新文案适配仍在完善。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/897/draft-zh-1bc9e79516df.mp4) |
| 卡通讲解风 `mg-style-875206` | 手绘卡通讲解、步骤演示与原生转场。内测版，新文案适配仍在完善。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/898/draft-zh-07d37803544c.mp4) |
| 像素海洋 `mg-style-966597` | 像素海浪、水位上涨与过关式动画。内测版，新文案适配仍在完善。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/899/draft-zh-e97c782669c1.mp4) |

### 知识解说与流程图

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 量价图表：K线突破与分时动画 `mg-style-287792` | 量价教学图表独立组件，包含两组日K与一组分时动画。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/869/1.0.0-zh-d5fd83bc28a8.mp4) |
| 流程与时间线 · FLOW / TIMELINE `mg-style-876` | 四步创作流程（说戏→分镜→画面→成片）推进到一条时间线，四轨片段铺开、播放头扫过、统计落位；9.8 秒，适合 AIGC/创作工具的能力说明。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/876/1.0.0-zh-294b6a370e6d.mp4) |
| DEEP STAGE 案例数据 `mg-style-587362` | 案例讲解动效：数据仪表盘推入，3 个 KPI 数字滚动，6 根柱图从底部逐根生长（最高值自动主色高亮），前后对比副屏滑入。13 秒，适合案例复盘与成果汇报。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/882/1.0.0-5df639825460.mp4) |
| 目标与证据 · 17类语义动效 `mg-style-509099` | 暖灰米白与绿色的17类语义动效，适用于知识讲解、产品说明、指标比较与观点表达。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/886/0.4.0-rc.4-7ab29961149d.mp4) |
| 图解口播与图片展示 `mg-style-643842` | 月白渐变风格的图解与口播模板，支持图形讲解、图片视频展示和人物卡片；新增7种同系列食物SVG与透明PNG。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/888/0.8.0-rc.2-6971ec2770b7.mp4) |
| Kit 1 · 人文纪录片知识短片 `mg-style-233154` | 无口播、画面+字幕叙事的人文纪录片风知识短片模板：暗场开题、锚词砸出（缩放回弹+闪白+震屏）、结尾亮背景重定义。替换锚词与双语字幕即可制作新短片，1920×1080/30fps，样例 20 秒含程序化 BGM 与音效。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/889/1.0.0-c28fac802c50.mp4) |
| 水墨人物志 · 一个人的故事 `mg-style-360840` | 用汉字当角色（韩、刘、萧、项…）的水墨动画，2 分 48 秒讲完一个历史人物的一生，并用心理学解释他为什么落到这个下场。改预设里的对白、成语签、地点年份、括注和场景即可换一个新人物。1920×1080 / 30fps，样例含程序化动作音效。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/892/1.0.0-zh-1f9aa1a124de.mp4) |
| 瑞士信息设计 · 知识讲解模板 `mg-style-257987` | 用清晰网格、对象计数和比例变化讲明白“百分比在除什么”。适合分母、权重与统计比较，可由AI助手按本期文稿选择图示，支持可选真人开场。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/900/2.5.3-zh-5df29820b59b.mp4) |
| 黏土实验台 · 知识讲解模板 `mg-style-517652` | 把拆分、附着和搬运变成可追踪的黏土实验。适合对象变化与过程解释，由AI助手选择图标和图示，可选真人全屏开头后缩成圆窗。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/901/2.5.3-zh-8f8876c01431.mp4) |
| 粉笔黑板 · 知识讲解模板 `mg-style-173723` | 用粉笔线条把光线、视角与遮挡条件逐步画清。适合轨道、投影和几何原因辨析，提供图标图示选择引导，可选真人开场后圆窗陪讲。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/902/2.5.3-zh-3d0943b9524d.mp4) |
| 生长导图 · 知识讲解模板 `mg-style-880856` | 让关系沿分支生长，让对象沿路径前进。适合层级、分流、局部放大与不同时间尺度的解释，配有图示选择引导，可选真人开场后缩圆窗。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/903/2.5.3-zh-fe14805ea913.mp4) |
| 博物馆展墙 · 知识讲解模板 `mg-style-949192` | 以展墙与展品机制串起一段知识历程。适合日影、液位、齿轮、摆动、分频与共振的解释，由AI助手选图示，可选真人开场后圆窗陪讲。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/904/2.5.3-zh-12ca8272b15b.mp4) |
| 发光玻璃板 · 知识讲解模板 `mg-style-803150` | 在发光线条中看见波形怎样相遇、延时怎样留下残余。适合信号叠加、相位与反馈解释，提供图标图示引导，可选真人开头后缩圆窗。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/905/2.5.3-zh-90f1d36b5c30.mp4) |
| 等距系统图 · 知识讲解模板 `mg-style-106531` | 用等距剖切把内部结构、物质通路与能量关系分开讲清。适合换热、压缩和能量核算，提供图示选择引导，可选真人开场后缩圆窗。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/906/2.5.3-zh-f7f712d44ade.mp4) |
| 纸雕层叠 · 知识讲解模板 `mg-style-546070` | 用层叠纸片看见内部、压缩与搬运。适合层序、褶皱、切面和错动的教学解释，提供图标图示选择引导，可选真人开场后缩成圆窗。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/907/2.5.3-zh-66b986377f2a.mp4) |
| 地铁线路图 · 知识讲解模板 `mg-style-447390` | 沿着线路追踪占用、停车与队列变化。适合安全间隔、状态读数和有限服务流程的教学表达，配有图标图示引导，可选真人开头后缩圆窗。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/908/2.5.3-zh-fd8d9dc5ae03.mp4) |
| 双色孔版 · 知识讲解模板 `mg-style-808349` | 用双色套印看清复制、增长和基数差异。适合固定增量与固定比例、谱系和指数规则的解释，提供图示选择引导，可选真人开场后圆窗陪讲。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/909/2.5.3-zh-15d6f65e42f3.mp4) |
| 点阵手账 · 知识讲解模板 `mg-style-968813` | 把步骤、关键词和修订留在同一本点阵手账里。适合方法拆解与学习回顾，提供图标图示选择引导；页面为19.95秒早期风格短样。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/910/2.5.3-zh-5ebc896f6930.mp4) |
| 彩色几何 · 知识讲解模板 `mg-style-118272` | 用彩色边、面积与刚体拼图讲清几何等量关系。原生新稿围绕直角三角形模型，提供图示选择引导；页面为23.8667秒早期风格短样。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/911/2.5.3-zh-b27b76c06f66.mp4) |

### 科技视觉（非口播默认）

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 酷炫科技风 `mg-style-385712` | 金属立体字、光效与空间动效；中英横屏、中文竖屏，新增英文竖屏基础表达 B1–B4，支持人脸居中与圆形署名。 | 官方Demo可看 | [演示1](https://motiontemplates.github.io/385712/assets/demo.mp4) / [演示2](https://media.openaicut.com/previews/626/0.2.9-open-beta-zh-11eae4868d37.mp4) |

### 视觉与场景动效（非口播默认）

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 半调网点 · 人像标题 `mg-style-381814` | 三张人像化为流动的双色网点，散开后重新汇聚成标题，适合人像与主题开场。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/615/draft-zh-87b41df4a38a.mp4) |
| 照片马赛克 · 拼图揭幕 `mg-style-460349` | 多张照片组成主视觉，从局部照片拉远揭示完整马赛克，适合集体回忆与拼图揭幕。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/616/draft-zh-3c3bc74e9591.mp4) |
| 几何拼贴 · 动态海报 `mg-style-907345` | 将四张照片裁成几何形状，在三组包豪斯动态海报中重组，适合活动与视觉主题展示。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/617/draft-zh-d014a696e0ba.mp4) |
| 笔触重绘 · 艺术照片 `mg-style-328828` | 用三层定向笔触重绘照片，与原图对照后呈现署名标题，适合摄影与艺术展示。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/618/draft-zh-9a122d6aac1e.mp4) |
| 信号故障 · 照片转场 `mg-style-638039` | 用像素排序、RGB 分离和扫描线改造照片，并以 CRT 关机效果收尾，适合科技视觉片段。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/619/draft-zh-567d566f31a3.mp4) |
| 双重曝光 · 人像叠影 `mg-style-800829` | 以风景填充人像剪影，双层画面反向漂移，标题从薄雾显现，适合诗意人像叠影。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/620/draft-zh-eb40eb882b43.mp4) |
| 空间画廊 · 回忆相册 `mg-style-743702` | 穿行带有文字说明的立体照片画廊，最后推进主照片并揭示全屏标题，适合回忆与作品集。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/621/draft-zh-13dffcc71ff3.mp4) |
| 镜像万花筒 · 照片变幻 `mg-style-551805` | 将两张照片镜像成旋转的十二分段万花筒，经扩张圆环转场再展开原图，适合视觉主题片。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/622/draft-zh-3a7bf4639a39.mp4) |
| DeepSeek 鲸鱼粒子聚合 `mg-style-404937` | 粒子从散落聚合成品牌鲸鱼 Logo，适合片头、品牌露出或章节转场。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/628/1.1.0-e0d9c9e4a5b8.mp4) |
| DeepSeek 粒子形变 `mg-style-380710` | 同一批粒子在四种三维形状间形变，适合科技感转场、概念串联或片尾。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/629/1.1.0-0892fa4bf82d.mp4) |
| DeepSeek 词语粒子 `mg-style-941301` | 粒子按顺序拼出四个关键词，适合概念介绍、能力列表与口号式开场。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/630/1.1.0-7b16186bd6b2.mp4) |
| 光带文字 `mg-style-872` | 光之丝带汇聚成一个词：丝带流动、粒子成字、光带扫过，再散回丝带。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/872/1.0.0-08a812711d78.mp4) |
| 面板擦除 · WIPE PACK `mg-style-878` | 四套面板擦除过场：竖条合拢、横条下压、纸色竖条、墨色竖条；8 秒转场包，可用于场景切换与章节过渡。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/878/1.0.0-zh-be7dc794ab1a.mp4) |
| DEEP STAGE 开场点火标题 `mg-style-921052` | 深色立体舞台开场：地平线点火、地面透视网格生长、远景屏幕墙点亮，两段主标题落下（金属渐变），最后落到副标题与角标。10 秒片头动效，可换品牌、标题、副标题与主色。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/879/1.0.0-8e74030d1901.mp4) |
| DEEP STAGE 媒体素材墙 `mg-style-430770` | 媒体素材墙动效：六宫格（2×3）在 3D 空间逐张落位，每格独立纵深与旋转，落位后极缓慢浮动，镜头持续后拉。10 秒，适合素材盘点与 B-roll 讲解。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/883/1.0.0-a30bac716f4b.mp4) |
| DEEP STAGE 收尾锁版 `mg-style-581039` | 收尾锁版动效：屏幕退向纵深，logo 描边锁定，字标、副标、规格行与版本胶囊依次落位，一道横扫光掠过，结尾稳定呼吸。8 秒，适合片尾与版本标识。 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/884/1.0.0-651f2839086d.mp4) |
| 3D 吉祥物手把手教程 `mg-style-887145` | 把网页或 App 的一段操作流程（注册、下单、设置等），做成 3D 小宠物带着一步步点、打字、指重点的横屏教程视频 | 官方Demo可看 | [演示1](https://media.openaicut.com/previews/895/1.0.0-zh-a15d0b9cfbab.mp4) |

## 官网动画控件

### 关系与系统结构

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 流程图 `mg-control-flow` | 3–6 个有先后顺序的环节（步骤、流水线、因果链），或一个起点分出多个去向（branch）；节点可带图标 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/integrated/aivd-10/2.7.17-alpha.2/flow-chain-owner-v1.mp4) / [演示2](../docs/template-gallery/demos/motiongit/flow.mp4) |
| 循环图 `mg-control-cycle` | 首尾相接、周而复始的 3–6 个环节：飞轮、迭代闭环、生命周期；中心可写主题 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/cycle.mp4) |
| 漏斗 / 层级 `mg-control-funnel` | 逐层收窄的转化、筛选（funnel），或自下而上的层级、金字塔、技术栈（pyramid / layers）；每层可带一个数值 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/funnel.mp4) |
| 交集图 `mg-control-venn` | 两三个概念的交集或合成：A + B 的重叠点、三者兼得；merge 变体表示合而为一 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/venn.mp4) |
| 思维导图 `mg-control-mindmap` | 一个主题展开 3–6 个方面，每个方面可再列 0–2 个要点：知识框架、话题拆解 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/mindmap.mp4) |
| 2×2 象限 `mg-control-matrix` | 两个维度把事物分成四类：重要/紧急、投入/回报、定位分析；可在象限里落几个点，priority 变体突出一个象限 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/matrix.mp4) |
| 中心辐射 `mg-control-hub` | 一个核心连接 3–8 个周边：平台与生态、能力清单、一个工具对接多个场景 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/integrated/aivd-10/2.7.17-alpha.2/hub-constellation-owner-v1.mp4) / [演示2](../docs/template-gallery/demos/motiongit/hub.mp4) |
- `mg-control-flow` 登记基线版本：0.3.0 (package2.7.17-alpha.2)；当前本人Demo版本：2.7.17-alpha.2；本片QA：verified_demo。本片横屏flow/chain：1280×720、30fps、419帧、无音轨，完整解码通过；实际查看编码帧6,209,345,418及同帧圆窗放大联系表。源参数仅概念文字/图标；抽检未见客户资料或网址；圆窗头脸完整、透明角无黑方块、不遮概念正文。保留原生时码、.m标与出场淡出。仅本版本/此输入/此变体；不等于全帧人工审阅、连续观看、用户美学确认、全部变体或另一台机器通过。（不改变原条目验证范围，不代表用户审美认可）
- `mg-control-hub` 登记基线版本：0.3.0 (package2.7.17-alpha.2)；当前本人Demo版本：2.7.17-alpha.2；本片QA：verified_demo。本片横屏hub/constellation：1280×720、30fps、384帧、无音轨，完整解码通过；实际查看编码帧6,192,300,383及同帧圆窗放大联系表。源参数仅概念文字/图标；抽检未见客户资料或网址；圆窗头脸完整、透明角无黑方块、不遮概念正文。保留原生时码、.m标与出场淡出。仅本版本/此输入/此变体；不等于全帧人工审阅、连续观看、用户美学确认、全部变体或另一台机器通过。（不改变原条目验证范围，不代表用户审美认可）

### 叠加标注与装饰

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 人名条 `mg-control-lowerthird` | 第一次出现某个人、讲者、嘉宾或角色时标出名字和身份；也可当一条短字幕条。贴在左下（或右下），横屏在口播卡左侧、字幕之上 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/lowerthird.mp4) |
| 箭头标注 `mg-control-callout` | 指出画面里的某个位置（录屏按钮、图片细节、口播卡外的内容）：给目标点 x/y（0–1 画面比例）和一句短标注 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/callout.mp4) |
| 贴纸 `mg-control-sticker` | 给一句话盖个情绪章：「绝了」「重点」「NEW」「必看」，或一个图标贴纸。位置 x/y 可选（默认右上），不压口播卡和字幕 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/sticker.mp4) |
| 表情飘赞 `mg-control-emoji` | 情绪时刻的一阵表情：点赞、比心、火、笑。icon 用图标名（彩色圆泡），或 text 填 1–2 个 emoji 字符；n 为数量 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/emoji.mp4) |
| 章节进度条 `mg-control-progressbar` | 告诉观众「现在讲到第几部分」：2–6 个章节名 + 当前章节序号。放在章节切换处，停留 2–6 秒 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/progressbar.mp4) |
| 角标 `mg-control-tag` | 画面角落的话题标签、集数、属性：「#干货」「第 3 集」「新」，1–3 条，可整段常驻 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/tag.mp4) |
| 庆祝特效 `mg-control-confetti` | 里程碑、达成、好消息、结尾致谢：彩纸 / 烟花，可选一句短字居中弹出。每个 cue 一波（最多 3 波） | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/confetti.mp4) |
| 画面装饰框 `mg-control-frame` | 给整段画面加氛围：拍摄感取景框、录制中、霓虹边框。框住内容区（避开口播卡与字幕），可整段常驻 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/frame.mp4) |

### 品牌与行动

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| Logo 揭示 `mg-control-logo` | 片头或片尾亮出品牌/频道标志：有 logo 图片就用图片，没有就用名字首字或图标生成字标；下方可带一句标语 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/logo.mp4) |
| 片头 `mg-control-intro` | 视频开头的节目标题卡：标题 + 副标题 + 可选期数/日期。电影感开场、系列节目、栏目包装 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/intro.mp4) |
| 片尾 `mg-control-outro` | 视频结尾：感谢语 + 1–3 个下一步（推荐视频、下期预告、关注/链接文字），可带头像 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/outro.mp4) |
| 行动号召 `mg-control-cta` | 引导观众做一个动作：点链接、领取、评论、往下看、上滑。一个按钮文字 + 一句补充 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/cta.mp4) |
| 关注 / 三连 `mg-control-subscribe` | 求关注、求三连、开铃铛：按钮依次被光标点亮，图标弹跳、数字 +1。items 可自定义 2–3 个按钮 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/subscribe.mp4) |
| 倒计时 `mg-control-countdown` | 3–10 秒倒数：开奖、开播、限时、揭晓前的紧张感；归零时爆开出现结束语 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/countdown.mp4) |
| 价格 / 优惠 `mg-control-price` | 亮出价格与优惠：原价划掉、新价砸入、标签盖章；可带 1–3 个卖点 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/price.mp4) |
| 揭晓 / 抽奖 `mg-control-reveal` | 悬念揭晓：抽奖结果、答案、排名第一、新品名。鼓点悬念 → 打开 → 彩纸 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/reveal.mp4) |

### 基础讲解

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 两行标题 `mg-control-title` | 开场、段落开头：一行陈述 + 一行重点（重点行砸入） | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/title.mp4) |
| 关键词砸入 `mg-control-keyword` | 一个词或短语是这段话的重点；后面可以补 1–3 句解释，逐句出现 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/keyword.mp4) |
| 数字滚动 `mg-control-number` | 一个关键数字：时长、数量、百分比、价格。可带 1–3 句注释 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/number.mp4) |
| 要点列表 `mg-control-list` | 1–6 个并列要点，逐条出现；全部出现后高亮依次轮转 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/list.mp4) |
| 左右对比 `mg-control-compare` | 两种做法、前后变化、A 和 B 的差别；可给结论并标出胜者 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/compare.mp4) |
| 步骤流程 `mg-control-steps` | 2–5 个先后步骤；光点沿轨道依次点亮 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/integrated/aivd-10/2.7.17-alpha.2/steps-track-owner-v1.mp4) / [演示2](../docs/template-gallery/demos/motiongit/steps.mp4) |
| 金句 / 引用 `mg-control-quote` | 一句原话、观点或引用，逐字打出；*星号* 包住的词高亮 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/quote.mp4) |
| 数据条 `mg-control-bars` | 2–5 项数值比较；数值必须来自真实数据 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/bars.mp4) |
| 录屏 / 图片窗 `mg-control-media` | 展示用户的录屏、截图、产品图；可在画面上标出 1–3 处重点 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/media.mp4) |
| 印章强调 `mg-control-stamp` | 下结论、表态：免费、已上线、不推荐 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/stamp.mp4) |
| 章节卡 `mg-control-chapter` | 长视频分段：编号 + 段名 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/chapter.mp4) |
| 光球合成 `mg-control-fusion` | A × B 合在一起得到结果 C | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/fusion.mp4) |
- `mg-control-steps` 登记基线版本：0.3.0 (package2.7.17-alpha.2)；当前本人Demo版本：2.7.17-alpha.2；本片QA：verified_demo。本片横屏steps/track：1280×720、30fps、398帧、无音轨，完整解码通过；实际查看编码帧6,199,270,397及同帧圆窗放大联系表。源参数仅概念文字/图标；抽检未见客户资料或网址；圆窗头脸完整、透明角无黑方块、不遮概念正文。保留原生时码、.m标与出场淡出。仅本版本/此输入/此变体；不等于全帧人工审阅、连续观看、用户美学确认、全部变体或另一台机器通过。（不改变原条目验证范围，不代表用户审美认可）

### 数据与进度

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 环形占比 `mg-control-donut` | 几个部分占整体多少：构成、份额、预算分配、用户来源（2–5 项）。数值按占比换算成百分比 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/donut.mp4) |
| 折线趋势 `mg-control-linechart` | 随时间的变化：增长、下降、波动、两条对比（4–12 个点）。终点标注最后一个值 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/linechart.mp4) |
| KPI 数字卡 `mg-control-counter` | 2–4 个关键数字并排：用户数、营收、增长率、时长；可带涨跌 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/counter.mp4) |
| 进度 / 完成度 `mg-control-progress` | 完成了多少：项目进度、目标达成、技能熟练度、电量式的程度（1–4 条，百分比） | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/progress.mp4) |
| 时间线 / 里程碑 `mg-control-timeline` | 按时间顺序的 3–6 个节点：发展历程、计划路线图、事件经过；current 标出「现在」 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/timeline.mp4) |
| 对比表 / 功能矩阵 `mg-control-table` | 2–3 个方案在 2–5 项上逐项比较；单元格写 ✓ / ✗ 或短文字；赢家列高亮 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/table.mp4) |
| 排行榜 `mg-control-ranking` | 3–6 项按数值排名：榜单、名次、Top N；自动按 value 从大到小排序 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/ranking.mp4) |

### 文字动态

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 逐行动态排版 `mg-control-kinetic` | 一句有节奏的观点拆成 2–5 个短行，跟着口播一行一行冲出来；适合开场钩子、口号、情绪句 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/integrated/aivd-10/2.7.17-alpha.2/kinetic-stack-owner-v1.mp4) / [演示2](../docs/template-gallery/demos/motiongit/kinetic.mp4) |
| 重点词标记 `mg-control-highlight` | 一句完整的话里有 1–2 个必须被看见的词（用 *星号* 标出）：先出整句，再在重点上画标记 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/highlight.mp4) |
| 乱码解码 `mg-control-scramble` | 揭晓一个名字、术语、答案、代号：乱码逐位锁定。科技、数据、揭秘类内容 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/scramble.mp4) |
| 轮换词 `mg-control-rotator` | 同一句话换不同的词：「适合 学生 / 老师 / 公司」、「它能 写 / 画 / 剪」。最后一个词停住 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/rotator.mp4) |
| 滚动横幅 `mg-control-marquee` | 一串关键词/标签/口号持续滚动：活动、清单很长、节奏型过渡；可在横幅上砸入一个大词 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/marquee.mp4) |
| 巨字 `mg-control-bigtype` | 一个词撑满画面的冲击时刻：段落主题、结论词、品牌词；mask 变体可让图片/视频透过字显示 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/bigtype.mp4) |
- `mg-control-kinetic` 登记基线版本：0.3.0 (package2.7.17-alpha.2)；当前本人Demo版本：2.7.17-alpha.2；本片QA：verified_demo。本片横屏kinetic/stack：1280×720、30fps、272帧、无音轨，完整解码通过；实际查看编码帧6,136,195,271及同帧圆窗放大联系表。源参数仅概念文字/图标；抽检未见客户资料或网址；圆窗头脸完整、透明角无黑方块、不遮概念正文。保留原生时码、.m标与出场淡出。仅本版本/此输入/此变体；不等于全帧人工审阅、连续观看、用户美学确认、全部变体或另一台机器通过。（不改变原条目验证范围，不代表用户审美认可）

### 概念教学

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 图标要点卡 `mg-control-iconcards` | 2–4 个并列要点，每个配一个图标：功能亮点、方法要素、几个理由。比 list 更有画面感；要点有顺序/因果时改用 steps | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/iconcards.mp4) |
| 问答 `mg-control-qa` | 先抛出一个问题，停顿后揭晓答案：设问、观众常问、知识小测。cue 对准口播说出答案的那一刻 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/qa.mp4) |
| 误区与真相 `mg-control-myth` | 纠正一个常见错误说法：先摆出误区、否定它、再给出正确说法。辟谣、避坑、常见误解 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/myth.mp4) |
| 优缺点 `mg-control-prosCons` | 权衡一件事的好处与代价，最后给结论（偏向哪边）。选购、方案评估、利弊分析 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/prosCons.mp4) |
| 名词解释 `mg-control-definition` | 解释一个术语/概念：词条 + 注音/英文 + 类别 + 一句定义 + 可选例句。知识科普、行业黑话、新概念 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/definition.mp4) |
| 小贴士 / 警告 `mg-control-tip` | 插一句提醒：小技巧（tip）、注意事项（warn）、补充信息（info）、确认无误（ok）。类型决定图标与颜色 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/tip.mp4) |
| 待办清单 `mg-control-checklist` | 逐项完成的清单：准备步骤、检查项、已做到的事。和 list 的区别是有打勾过程、进度计数和最后的完成章 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/checklist.mp4) |
| 两方对决 `mg-control-vs` | 两个对象正面比拼 1–3 项数值并分出胜负：产品 A/B、方案、两个人或团队。只比观点不比数值时用 compare | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/vs.mp4) |

### 界面与交互演示

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 聊天对话 `mg-control-chat` | 把一段对话演出来：用户与客服/朋友的聊天、群里的讨论、向 AI 助手提问并得到回答；2–6 条消息逐条出现 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/chat.mp4) |
| 评论 / 弹幕 `mg-control-comment` | 展示观众反馈、网友评论、热评、弹幕刷屏：2–5 条评论逐条浮现，点赞数上涨，最高赞那条被强调（热评 / 置顶 / 放大停住） | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/comment.mp4) |
| 通知横幅 `mg-control-notify` | 表现「消息来了」：订单、提醒、私信、系统通知一条接一条弹出；也可做锁屏收到通知的画面 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/notify.mp4) |
| 搜索框 `mg-control-search` | 演示「搜一下」：输入关键词 → 回车 → 联想/结果出现、命中词高亮；适合讲搜索热度、怎么找资料、工具里的命令面板 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/search.mp4) |
| 浏览器 / 应用窗口 `mg-control-browser` | 演示「打开一个网页 / 网站 / 应用」：地址栏输入网址、加载、页面滚动，再用 1–3 个高亮框标出重点区域。只需要静态录屏展示用 0.2.0 的 media | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/browser.mp4) |
| 社交数据卡 `mg-control-social` | 展示一条内容的反响：帖子被点赞、主页涨粉、三项互动数据；数字滚动上涨。数字请标注示意 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/social.mp4) |
| 鼠标点击演示 `mg-control-cursor` | 演示软件操作步骤：依次点几个按钮、把文件拖进某个区域、打开菜单选一项。可以放截图作为背景 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/cursor.mp4) |

### 真实素材展示

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 图集 `mg-control-gallery` | 3–8 张图片/视频一起亮相：作品集、案例合集、活动照片、产品多角度；每个 cue 出一张（carousel/stack 是每个 cue 转到下一张） | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/gallery.mp4) |
| 前后对比 `mg-control-beforeafter` | 同一对象改造前后、修图前后、旧版新版：两张素材对照，第二个 cue 揭示 after | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/beforeafter.mp4) |
| 纪录片推拉 `mg-control-kenburns` | 讲故事、回顾、旅程、案例背景：1–4 张图片纪录片式慢推慢移、交叉溶解，底部逐字打出说明；每个 cue 换一张 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/kenburns.mp4) |
| 拍立得 `mg-control-polaroid` | 生活感、回忆、幕后花絮、团队/人物照片：1–4 张照片卡 + 手写说明；每个 cue 出一张 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/polaroid.mp4) |
| 设备样机 `mg-control-device` | 展示 App、网页、录屏、作品画面：素材放进手机 / 平板 / 显示器屏幕里，视频按成片时钟播放；可配标题 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/device.mp4) |
| 拼贴墙 `mg-control-collage` | 大量作品/截图/用户照片的气势感：作品墙、社区、合集封面。masonry / wall 用 4–9 张（不够会循环）；mosaic 只用第一张，碎片拼成整图 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/collage.mp4) |
| 聚光放大 `mg-control-spotlight` | 在一张截图/照片/视频画面里依次指出 1–3 个关注点（x、y 为 0–1 的相对位置），每个点带一个短标签 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/motiongit/spotlight.mp4) |

## 现有代码模板

### Logo与品牌

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 笔刷揭示 `remotion-brush-stroke-reveal` | 笔刷扫过后显现标记 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/brush-stroke-reveal.mp4) |
| Logo由模糊变清晰 `remotion-logo-blur-reveal` | 由虚焦过渡到清晰 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/logo-blur-reveal.mp4) |
| Logo弹落 `remotion-logo-bounce-drop` | 标记下落后弹性停稳 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/logo-bounce-drop.mp4) |
| Logo遮罩擦入 `remotion-logo-mask-wipe` | 斜向遮罩显现标记 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/logo-mask-wipe.mp4) |
| Logo分裂揭示 `remotion-logo-split-reveal` | 左右面板分开显现标记 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/logo-split-reveal.mp4) |
| Logo描边绘制 `remotion-logo-stroke-draw` | 轮廓逐段描绘后填充 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/logo-stroke-draw.mp4) |
| 霓虹文字闪烁 `remotion-neon-sign` | 霓虹文字闪动后亮起 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/neon-sign.mp4) |
| 碎片揭示 `remotion-shatter-reveal` | 覆盖层碎裂并显现后层 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/shatter-reveal.mp4) |

### RemotionUI本地适配

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 前后环绕卡片演示 `remotion-library-orbit` | 卡片绕原创几何示意人物前后运动；没有真人抠像输入 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/library-orbit.mp4) |
| 文字镂空媒体演示 `remotion-library-text-mask` | SVG文字镂空与渐变移动；演示使用合成渐变 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/library-text-mask.mp4) |

### 中文示例

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 中文长条成长示例 `remotion-library-bar-zh` | 柱状图按数值依次增长；已有基础模板的中文参数示例，不新增模板家族。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/library-bar-zh.mp4) |
| 中文玻璃卡片示例 `remotion-library-glass-zh` | 半透明玻璃下三分之一信息卡；已有基础模板的中文参数示例，不新增模板家族。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/library-glass-zh.mp4) |
| 中文播放器界面示例 `remotion-library-player-zh` | 代码绘制竖屏播放器与信息层；已有基础模板的中文参数示例，不新增模板家族。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/library-player-zh.mp4) |

### 循环与背景

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 散景光圈背景 `remotion-bokeh-circles` | 柔焦圆形漂浮背景 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/bokeh-circles.mp4) |
| 烟花爆开 `remotion-fireworks-burst` | 放射粒子爆开 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/fireworks-burst.mp4) |
| 网格波浪循环 `remotion-loop-grid-wave` | 网格按波形循环变化 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/loop-grid-wave.mp4) |
| 视差平移 `remotion-parallax-pan` | 多层图形以不同速度移动 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/parallax-pan.mp4) |
| 铅笔绘制 `remotion-pencil-draw` | 铅笔沿星形路径绘制 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/pencil-draw.mp4) |
| 像素瀑布循环 `remotion-pixel-waterfall-cycle` | 竖屏像素图形循环 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/pixel-waterfall-cycle.mp4) |
| 粒子雪花 `remotion-particle-snow` | 图形粒子持续飘落 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/particle-snow.mp4) |
| 星空穿行背景 `remotion-starfield` | 星点向外运动的空间背景 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/starfield.mp4) |

### 数据与图表

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 长条图成长 `remotion-bar-chart-anim` | 柱状图按数值依次增长 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/bar-chart-anim.mp4) |
| 折线图绘制 `remotion-line-chart-anim` | 折线沿横轴逐步绘出 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/line-chart-anim.mp4) |
| 滴入式填充计量 `remotion-pourover-drip-fill-gauge` | 滴落式动画填满目标比例；中文演示层使用 NotoSansSC 补字，保留原动画时序；原版像素字库只覆盖英文。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/pourover-drip-fill-gauge.mp4) |
| 数字计数器 `remotion-kpi-counter` | 数字递增到目标值 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/kpi-counter.mp4) |
| 像素蜡烛图 `remotion-pixel-candlestick-ohlc` | 像素风格OHLC数据演示；中文演示层使用 NotoSansSC 补字，保留原动画时序；原版像素字库只覆盖英文。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/pixel-candlestick-ohlc.mp4) |
| 排名竞速长条图 `remotion-racing-chart` | 长条随数据变化交换排名 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/racing-chart.mp4) |

### 文字与标题

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 标题弹入 `remotion-bounce-in-headline` | 整段标题从上方弹入，带回弹。并非逐词分拍。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/bounce-in-headline.mp4) |
| 章节标题卡 `remotion-chapter-title` | 编号与章节标题显现 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/chapter-title.mp4) |
| 四色标题切换 `remotion-four-tone-mono-titler` | 标题块切换四组颜色；中文演示层使用 NotoSansSC 补字，保留原动画时序；原版像素字库只覆盖英文。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/four-tone-mono-titler.mp4) |
| 故障文字 `remotion-glitch-text` | RGB错位抖动后稳定 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/glitch-text.mp4) |
| 文字渐变扫过 `remotion-gradient-text-sweep` | 颜色渐变经过标题 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/gradient-text-sweep.mp4) |
| 动态词语堆叠 `remotion-kinetic-word-stack` | 词语逐个入场形成文字块 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/kinetic-word-stack.mp4) |
| 像素打字引语 `remotion-pixel-typewriter-quote` | 像素风格逐字输入引语；中文演示层使用 NotoSansSC 补字，保留原动画时序；原版像素字库只覆盖英文。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/pixel-typewriter-quote.mp4) |
| 乱序文字归位 `remotion-scramble-text` | 字符变化后组成目标标题 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/scramble-text.mp4) |
| 文字遮罩揭示 `remotion-text-mask-reveal` | 文字从遮罩边界内滑出 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/text-mask-reveal.mp4) |
| 打字机 `remotion-typewriter` | 逐字输入并显示光标 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/typewriter.mp4) |
| 波浪文字 `remotion-wave-text` | 文字按波形上下移动 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/wave-text.mp4) |

### 社交与界面

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 聊天界面 `remotion-community-chat` | 竖屏聊天消息逐条展示；独立演示层把桌面尺寸字体放大，方便阅读竖版中文界面。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/community-chat.mp4) |
| 通用结束卡 `remotion-end-card` | 通用CTA结束卡；不替换用户固定片尾 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/end-card.mp4) |
| 眼睛揭示动画 `remotion-eye-reveal` | 代码图形的眼睛开合揭示 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/eye-reveal.mp4) |
| 玻璃信息卡 `remotion-lower-third-glass-card` | 半透明玻璃下三分之一信息卡 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/lower-third-glass-card.mp4) |
| 角色跳动 `remotion-character-jumping` | 代码图形角色弹跳；独立演示层修正原版重复扣除跳跃位移并降低跳高，防止角色跳出画框；原始源码未改。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/character-jumping.mp4) |
| 短视频播放器界面 `remotion-social-reel` | 代码绘制竖屏播放器与信息层 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/social-reel.mp4) |
| 分屏布局 `remotion-split-screen` | 两个画面区域进入并排布局 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/split-screen.mp4) |
| 思考气泡 `remotion-thinking-bubble` | 代码图形思考气泡 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/thinking-bubble.mp4) |
| 角色招手 `remotion-wave-hello` | 代码图形招手动画 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/wave-hello.mp4) |

### 转场

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 镜头震动 `remotion-camera-shake` | 短促镜头抖动基础 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/camera-shake.mp4) |
| 卡片翻面转场 `remotion-card-flip-transition` | 画面按卡片方式翻转 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/card-flip-transition.mp4) |
| 圆形擦除转场 `remotion-transition-circle-wipe` | 圆形遮罩由中心扩张 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/transition-circle-wipe.mp4) |
| 墨迹扩散转场 `remotion-ink-spread-transition` | 墨迹扩散覆盖画面 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/ink-spread-transition.mp4) |
| 翻页转场 `remotion-flip-page-transition` | 页面翻动切换场景 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/flip-page-transition.mp4) |
| 像素马赛克转场 `remotion-pixel-mosaic-transition` | 画面拆成像素块再组合 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/pixel-mosaic-transition.mp4) |
| 滑动擦除转场 `remotion-slide-wipe` | 面板滑动切换场景 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/slide-wipe.mp4) |
| 快速甩镜 `remotion-whip-pan` | 快速横移与模糊转场 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/remotion/whip-pan.mp4) |

## 真人口播特效

### 人物与背景

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 剪纸描边 `presenter-effect-04` | 动态抠像人物加白色纸边和阴影，置于纸张纹理背景。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-04.mp4) |
| 照片墙 `presenter-effect-05` | 多张照片组成错位移动墙，动态人物位于前景。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-05.mp4) |
| 杂志封面 `presenter-effect-08` | 人物与封面标题分层，形成杂志封面式口播包装。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-08.mp4) |
| 抠像换景 `presenter-effect-09` | 已抠像的人物合成到原创蓝色空间背景。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-09.mp4) |
| 人物破框 `presenter-effect-15` | 同源画面在倾斜窗口内显示，透明人物延伸到窗口外。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-15.mp4) |

### 列表与步骤

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 打勾清单 `presenter-effect-10` | 清单项依次打勾，顶部进度随演示推进。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-10.mp4) |
| 收据列表 `presenter-effect-18` | 纸张从打印口逐步出现，列出三项内容并打勾。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-18.mp4) |

### 数据与图表

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 条形增长 `presenter-effect-01` | 三条横向示意条按顺序增长，叠在口播画面上。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-01.mp4) |

### 文字与标题

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 玻璃标签 `presenter-effect-02` | 半透明圆角玻璃标签进入画面，突出一个短标题。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-02.mp4) |
| 视频镂空字 `presenter-effect-11` | 真人视频透过大型中文字显示，并保留圆形人物小窗。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-11.mp4) |
| 标题墙 `presenter-effect-13` | 重复大字在人物后方交错移动，形成动态文字墙。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-13.mp4) |

### 界面与设备

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 界面窗框 `presenter-effect-07` | 口播被放入带标题栏的悬浮窗框，形成界面容器效果。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-07.mp4) |
| 手机画面 `presenter-effect-14` | 口播装入带旋转动作的手机轮廓与播放信息层。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-14.mp4) |

### 装饰与强调

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 手绘涂鸦 `presenter-effect-12` | 线条、星形与箭头逐步绘出，围绕人物形成手绘强调。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-12.mp4) |
| 环绕文字 `presenter-effect-16` | 三张中文词卡沿椭圆轨迹环绕人物，并表现前后遮挡。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-16.mp4) |
| 贴纸轮播 `presenter-effect-19` | 五枚原创图标贴纸沿椭圆轨道轮转，并改变前后大小。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-19.mp4) |

### 镜头与转场

| 名称 | 用途 | 当前验证 | Demo |
|---|---|---|---|
| 冲击缩放 `presenter-effect-03` | 同一镜头快速推近、模糊并回拉，配合扩散边框。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-03.mp4) |
| 拉远揭幕 `presenter-effect-06` | 口播画面逐步缩小，显露带标题栏的悬浮窗口。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-06.mp4) |
| 数字推近 `presenter-effect-17` | 围绕人物焦点逐步放大原画面，叠加构图框。 | 本机演示已检查 | [演示1](../docs/template-gallery/demos/presenter/presenter-effect-17.mp4) |

## 附加预览

3D书籍等preview只作为效果参考，不计入上方目录条目；可取得情况按官网当前页面核对。

个人.motion与Key、原始口播、完整成片、旧工作记录、依赖及保护内核不进入本目录或Git。

[3D书 · 阿杜和那个影响了](https://github.com/motiontemplates/all/releases/download/demo-batch-two-2026-10-21/3d-book-demo-6dc0bd1a0e5bc9e8.mp4)
