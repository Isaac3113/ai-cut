# 可复用动画模板库

这是现有口播剪辑工程的独立素材库：50 个 RenderComp 源码模板、2 个 RemotionUI 本地适配组件演示、3 个中文示例，共 55 个 composition。它们为参考效果提供不同程度的基础，**不表示已经完整复刻 Instagram 参考的 19 项效果**。

源码注册、渲染检查、真人素材验收、连续观看试听与用户认可各自独立；本页不记载本轮测试结论。

## 位置与来源

- Active Repo：`C:\Codex Workspace\ai-cut`。
- 本扩展：`C:\Codex Workspace\ai-cut\extensions\remotion-vd44`。
- 独立入口：`src/template-library/index.ts`，调用 `LibraryRoot.tsx`；没有替换原 `src/Root.tsx`，原工程继续由原 `run.ps1` 管理。
- 机器目录：`template-catalog.json`；含来源、默认参数入口、画幅/帧率/时长和 19 项差距，后续效果继续追加。
- RenderComp 原文件：`src/vendor/rendercomp/`，固定 commit `f648980e528defb7594e24c6447055f0540f340b`；[上游仓库](https://github.com/RenderComp/free-remotion-templates)。
- RemotionUI 适配：`src/template-library/remotion-ui/`，固定 commit `0aecaca2b61a167992e1205d10e4da16d8a71331`；[上游仓库](https://github.com/riaz37/remotion-ui)。原始字节、哈希与修改说明见其 `source-manifest.json` 与 README。

## 使用顺序

先由总 Skill 确认本条视频比例、口播剪辑与最终时间，再从目录选模板。默认模板有横屏、方形和少量竖屏，并未统一改成 9:16；换比例需要重排并审看。

在 PowerShell 进入扩展目录，列出模板并打开独立预览：

```powershell
Set-Location "C:\Codex Workspace\ai-cut\extensions\remotion-vd44"
.\run-library.ps1 -Action List
.\run-library.ps1 -Action Preview
```

`Preview` 启动本地 Studio 且不自动打开浏览器；这是素材预览，不是 ChatCut 主时间轴。`Check` 执行脚本定义的 TypeScript 与本地适配代码 lint；列出 composition 或类型检查不能代替画面验收。

导出中文示例或单帧：

```powershell
.\run-library.ps1 -Action Check
.\run-library.ps1 -Action Render -TemplateId library-bar-zh
.\run-library.ps1 -Action Still -TemplateId library-glass-zh -Frame 45
```

未指定 `OutputPath` 时写入 `out/template-library/` 的带时间文件名，已有文件不覆盖。可传 `NodePath`、`BrowserPath`、`PropsPath`、`OutputPath`；实际参数以 `run-library.ps1` 为准。默认渲染使用 H264 MP4，**不保留 alpha 透明通道**。叠加到口播前，须在同一 composition 内与底层视频合成，或使用工程已有、另行验证的透明素材路线；黑底不是透明底。

中文示例需要本机 `public/NotoSansSC.ttf` 及其 `public/OFL.txt`。按现有字体来源与许可准备；没有字体时脚本报错，不悄悄换成缺字字体。上游模板用系统字体，中文需明确绑定字体并检查换行与出界。

下面 JSON 可保存为本条工程中的 props 文件，然后用 `-PropsPath` 指向它；测试数值不得当作真实业务结果：

```json
{
  "title": "长条成长示例",
  "subtitle": "以下为测试数值",
  "bars": [
    {
      "label": "项目一",
      "value": 40
    },
    {
      "label": "项目二",
      "value": 80
    }
  ],
  "background": "#102B36",
  "titleColor": "#F2F8FA",
  "accentColor": "#47B4D0"
}
```

```powershell
.\run-library.ps1 -Action Render -TemplateId library-bar-zh -PropsPath "C:\Codex Workspace\ai-cut\work\template-library\bar-props.json"
```

## 50 个上游模板目录

以下为默认 composition 信息，来源均为 RenderComp。文字、颜色、数字等参数名称见对应源码的 `Props` 类型与 `default...Props`，机器目录也记录 `prop_fields`。时长按各自默认 30fps 计算，不能把本例帧号原样套到下一集。

### Logo与品牌

| ID | 中文名称与用途 | 默认画幅 | 默认时长 |
|---|---|---|---|
| `brush-stroke-reveal` | 笔刷揭示：笔刷扫过后显现标记 | 1920×1080 | 4 秒 |
| `logo-blur-reveal` | Logo由模糊变清晰：由虚焦过渡到清晰 | 1920×1080 | 4 秒 |
| `logo-bounce-drop` | Logo弹落：标记下落后弹性停稳 | 1920×1080 | 3 秒 |
| `logo-mask-wipe` | Logo遮罩擦入：斜向遮罩显现标记 | 1920×1080 | 3.33333 秒 |
| `logo-split-reveal` | Logo分裂揭示：左右面板分开显现标记 | 1920×1080 | 4 秒 |
| `logo-stroke-draw` | Logo描边绘制：轮廓逐段描绘后填充 | 1920×1080 | 3.66667 秒 |
| `neon-sign` | 霓虹文字闪烁：霓虹文字闪动后亮起 | 1080×1080 | 3.33333 秒 |
| `shatter-reveal` | 碎片揭示：覆盖层碎裂并显现后层 | 1920×1080 | 4 秒 |

### 文字与标题

| ID | 中文名称与用途 | 默认画幅 | 默认时长 |
|---|---|---|---|
| `bounce-in-headline` | 标题逐词弹入：标题词语依次弹入 | 1920×1080 | 4 秒 |
| `chapter-title` | 章节标题卡：编号与章节标题显现 | 1920×1080 | 5 秒 |
| `four-tone-mono-titler` | 四色标题切换：标题块切换四组颜色 | 1920×1080 | 4 秒 |
| `glitch-text` | 故障文字：RGB错位抖动后稳定 | 1920×1080 | 4 秒 |
| `gradient-text-sweep` | 文字渐变扫过：颜色渐变经过标题 | 1920×1080 | 3.66667 秒 |
| `kinetic-word-stack` | 动态词语堆叠：词语逐个入场形成文字块 | 1920×1080 | 4 秒 |
| `pixel-typewriter-quote` | 像素打字引语：像素风格逐字输入引语 | 1920×1080 | 6 秒 |
| `scramble-text` | 乱序文字归位：字符变化后组成目标标题 | 1920×1080 | 5 秒 |
| `text-mask-reveal` | 文字遮罩揭示：文字从遮罩边界内滑出 | 1920×1080 | 3.66667 秒 |
| `typewriter` | 打字机：逐字输入并显示光标 | 1080×1080 | 3.33333 秒 |
| `wave-text` | 波浪文字：文字按波形上下移动 | 1920×1080 | 5 秒 |

### 转场

| ID | 中文名称与用途 | 默认画幅 | 默认时长 |
|---|---|---|---|
| `camera-shake` | 镜头震动：短促镜头抖动基础 | 1920×1080 | 4 秒 |
| `card-flip-transition` | 卡片翻面转场：画面按卡片方式翻转 | 1920×1080 | 4 秒 |
| `transition-circle-wipe` | 圆形擦除转场：圆形遮罩由中心扩张 | 1920×1080 | 3 秒 |
| `ink-spread-transition` | 墨迹扩散转场：墨迹扩散覆盖画面 | 1920×1080 | 4 秒 |
| `flip-page-transition` | 翻页转场：页面翻动切换场景 | 1920×1080 | 4 秒 |
| `pixel-mosaic-transition` | 像素马赛克转场：画面拆成像素块再组合 | 1920×1080 | 3 秒 |
| `slide-wipe` | 滑动擦除转场：面板滑动切换场景 | 1920×1080 | 4 秒 |
| `whip-pan` | 快速甩镜：快速横移与模糊转场 | 1920×1080 | 4 秒 |

### 数据与图表

| ID | 中文名称与用途 | 默认画幅 | 默认时长 |
|---|---|---|---|
| `bar-chart-anim` | 长条图成长：柱状图按数值依次增长 | 1920×1080 | 5 秒 |
| `line-chart-anim` | 折线图绘制：折线沿横轴逐步绘出 | 1920×1080 | 5 秒 |
| `pourover-drip-fill-gauge` | 滴入式填充计量：滴落式动画填满目标比例 | 1920×1080 | 6 秒 |
| `kpi-counter` | 数字计数器：数字递增到目标值 | 1920×1080 | 4 秒 |
| `pixel-candlestick-ohlc` | 像素蜡烛图：像素风格OHLC数据演示 | 1920×1080 | 6 秒 |
| `racing-chart` | 排名竞速长条图：长条随数据变化交换排名 | 1920×1080 | 7 秒 |

### 社交与界面

| ID | 中文名称与用途 | 默认画幅 | 默认时长 |
|---|---|---|---|
| `community-chat` | 聊天界面：竖屏聊天消息逐条展示 | 1080×1920 | 9 秒 |
| `end-card` | 通用结束卡：通用CTA结束卡；不替换用户固定片尾 | 1920×1080 | 5 秒 |
| `eye-reveal` | 眼睛揭示动画：代码图形的眼睛开合揭示 | 1080×1080 | 3 秒 |
| `lower-third-glass-card` | 玻璃信息卡：半透明玻璃下三分之一信息卡 | 1920×1080 | 4 秒 |
| `character-jumping` | 角色跳动：代码图形角色弹跳 | 1080×1080 | 4 秒 |
| `social-reel` | 短视频播放器界面：代码绘制竖屏播放器与信息层 | 1920×1080 | 5 秒 |
| `split-screen` | 分屏布局：两个画面区域进入并排布局 | 1920×1080 | 5 秒 |
| `thinking-bubble` | 思考气泡：代码图形思考气泡 | 1080×1080 | 4 秒 |
| `wave-hello` | 角色招手：代码图形招手动画 | 1080×1080 | 3 秒 |

### 循环与背景

| ID | 中文名称与用途 | 默认画幅 | 默认时长 |
|---|---|---|---|
| `bokeh-circles` | 散景光圈背景：柔焦圆形漂浮背景 | 1920×1080 | 5 秒 |
| `fireworks-burst` | 烟花爆开：放射粒子爆开 | 1080×1080 | 3.66667 秒 |
| `loop-grid-wave` | 网格波浪循环：网格按波形循环变化 | 1920×1080 | 3 秒 |
| `parallax-pan` | 视差平移：多层图形以不同速度移动 | 1920×1080 | 4 秒 |
| `pencil-draw` | 铅笔绘制：铅笔沿星形路径绘制 | 1080×1080 | 3.33333 秒 |
| `pixel-waterfall-cycle` | 像素瀑布循环：竖屏像素图形循环 | 1080×1920 | 6 秒 |
| `particle-snow` | 粒子雪花：图形粒子持续飘落 | 1080×1080 | 5 秒 |
| `starfield` | 星空穿行背景：星点向外运动的空间背景 | 1920×1080 | 5 秒 |

## 2 个适配组件与 3 个中文示例

| ID | 内容 | 默认规格 | 关键边界 |
|---|---|---|---|
| `library-orbit` | 前后环绕卡片 | 1080×1080、30fps、6秒 | 中心为原创几何图形；真人需提供透明人物层，矩形视频不能冒充人像遮挡 |
| `library-text-mask` | SVG文字镂空媒体 | 1080×1080、30fps、4秒 | 演示用合成渐变；真实视频解码和中文字体须另验 |
| `library-bar-zh` | 中文长条成长 | 1920×1080、30fps、5秒 | 数值为测试示意，需按本条事实替换 |
| `library-glass-zh` | 中文玻璃信息卡 | 1920×1080、30fps、4秒 | 不是参考中间胶囊文字的精确版 |
| `library-player-zh` | 中文播放器界面 | 1920×1080、30fps、5秒 | 目前为代码图形界面，未接入真人视频 |

适配组件的可复用导出是 `OrbitMotion` 和 `TextMaskVideo`。两个 `...Demo` composition 用于观察基础动作；修改实际组件参数时，在本条素材 composition 中调用它们，不把演示图形当作已经抠好的人物。`TextMaskVideo` 的实际视频输入明确静音；它不会替代主时间轴的人声。

## 参考 19 项效果：可用基础与差距

名称依据用户提供的[参考片](https://www.instagram.com/reel/De6Aa5fMaFt/)。第 17 项是“数位推近”。所有行均为开发映射，不代表参考原版已经实现或验收。

| 序号 | 参考效果 | 本库候选基础 | 还需要做什么 |
|---|---|---|---|
| 01 | 长条成长 | `bar-chart-anim`、`library-bar-zh`、`racing-chart` | 改成参考中的比较卡片与数值变化方式；根据真实口播重新映射时间，替换测试数值 |
| 02 | 玻璃字 | `lower-third-glass-card`、`library-glass-zh` | 现有为玻璃信息卡，需改成参考胶囊文字的尺寸、位置与进退场；在实际视频背景上检查透明和模糊效果 |
| 03 | 穿越转场 | `transition-circle-wipe`、`shatter-reveal` | 现成通用遮罩或碎片转场不是参考穿越画面；需重做穿越运动、目标区域遮罩及镜头衔接 |
| 04 | 剪纸 | 无直接模板 | 需要真人动态alpha或逐帧蒙版；需制作白色轮廓、纸张纹理、阴影及边缘稳定性处理 |
| 05 | 照片墙 | `split-screen` | 需要照片网格、卡片移动与用户素材输入；若真人位于照片墙前景，需动态人像alpha与遮挡处理 |
| 06 | 拉远揭幕 | `social-reel`、`library-player-zh` | 需添加真实视频输入并设计从全屏拉远到窗口的运动；重排窗口边框与最终画幅 |
| 07 | 介面世界 | `social-reel`、`library-player-zh`、`community-chat` | 播放器或聊天界面是图形示意，需添加真实视频和本条内容；需制作参考浏览器窗口与交互图形 |
| 08 | 杂志封面 | `kinetic-word-stack`、`bounce-in-headline` | 需设计杂志标题、封面信息与排版；文字若位于人物后方，需人像alpha与前后图层合成 |
| 09 | 绿幕换景 | 无直接模板 | 没有真人去背模板或自动换景流水线；需按真实原片选择色键或人像分割并验证发丝与时间稳定性 |
| 10 | 打勾清单 | 无直接模板 | 当前50模板与2组件没有参考清单模板；需新增清单、打勾、进度与口播时间参数 |
| 11 | 镂空字 | `library-text-mask`、`text-mask-reveal` | TextMaskVideo提供媒体穿过文字的组件基础，演示是合成渐变；需接入实际视频、中文字体与参考描边/暗层；文字滑出模板本身不是镂空媒体 |
| 12 | 手绘涂鸦 | `pencil-draw` | 铅笔模板仅提供星形路径绘制基础；若要参考的人物轮廓白线，需轮廓提取、跟踪或动态蒙版 |
| 13 | 标题墙 | `kinetic-word-stack`、`four-tone-mono-titler` | 需新增重复标题墙及字重/空心交替排版；人物位于标题前方时需动态人像alpha |
| 14 | 手机画面 | `social-reel`、`library-player-zh` | 现有为代码播放器界面，无真人视频输入；需加入真实视频、手机外框、透视运动与本条界面内容 |
| 15 | 破框而出 | 无直接模板 | 需对人物与框内视频分层；需匹配同源时码、框边遮挡与人物alpha，不能用矩形视频冒充抠像 |
| 16 | 环绕字 | `library-orbit` | OrbitMotion可安排前后卡片与文字，但演示中心为原创几何图形；需接入真实透明人物层并验证前后遮挡、边缘和节奏 |
| 17 | 数位推近 | 无直接模板 | 可复用总Skill已有轻推近流程；此库没有参考真人倍率框模板；需加入目标取景、倍率标注与安全裁切并匹配实际口播 |
| 18 | 收据列印 | `typewriter`、`text-mask-reveal` | 打字与文字遮罩仅为动作基础；需新增收据纸、出口遮罩、纸张向下输送、撕边与本条文字 |
| 19 | 贴纸轮播 | `library-orbit` | 环绕组件只提供位置与层级运动基础；需接入有使用权限的贴纸、轮播顺序、进退场与最终布局 |

## 回到口播主工程

1. 沿用总 Skill 的唯一 ChatCut 主时间轴。模板只生成素材；人物、原声、字幕、BGM、SFX 都按本条最终时间映射。
2. 模板按最终帧制作，插入主时间轴时为 1.0 倍；不重复加速原声、BGM或已制作动画。外部动画内部文字或动作改变时，回到源码与 props 重新渲染。
3. 视频素材输入保持静音；人声、BGM、SFX继续分轨。没有音轨的图形素材不构成声音验收。
4. 全屏素材按现有品牌与真人圆窗规则合成；模板里的通用结束卡不替换用户已指定固定片尾。
5. 真实视频输入、人物alpha、发丝边缘、逐帧闪烁、前后遮挡、字幕安全区及最终ChatCut输出分别检查。当前库没有提供真人抠像流水线，不因几何人物演示就声称已经验证抠像。

## 许可与同步

- RenderComp 源码采用 MIT；保留 `src/vendor/rendercomp/LICENSE`、SPDX 与版权声明。其 `ASSETS.md` 记录没有捆绑图片、音频、视频或字体，图形为代码绘制。
- RemotionUI 原始许可随 `src/template-library/remotion-ui/upstream/LICENSE` 保存，本地改动记录在对应 manifest。
- **Remotion 引擎独立授权**，不因为这些模板是 MIT 就自动获得所有商业用途资格。使用前核对[当前运行时许可](https://www.remotion.dev/license)与实体资格；字体、照片、贴纸、视频和音效也分别核对。
- GitHub同步源码、规则与目录；用户视频、参考媒体、输出、运行缓存和模型不进入Git。媒体与交付按OneDrive Hub既有规则保存，本地缓存留Active Repo的工作目录。

## 后续增加效果

新增模板先登记唯一ID、来源URL/固定commit、许可、源码与props、默认画幅/帧率/时长；保留上游原文件，将本地适配分开。再接入独立 `LibraryRoot.tsx` 并更新 `template-catalog.json`。新增效果可继续追加到 `reference_effects`，编号不限制为19。

每个模板分别记录后续检查证据。模板数量、引擎支持和一次示意渲染都不能代替新视频的完整验收。

## 两项适配组件的JSON参数

`library-orbit` 接受 labels/title/note/periodInFrames；`library-text-mask` 接受 text/title/note/media/src/gradient/fontFamily。默认对象在 remotion-ui/Demos.tsx。媒体src使用public下相对路径，不接受Windows磁盘路径；video/image缺src时报错。Preview和Render读取同一个PropsPath；显式文件路径按调用时所在目录解析，建议使用绝对路径。
