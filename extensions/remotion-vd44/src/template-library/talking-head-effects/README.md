# 真人口播19项特效试剪模块

独立 composition：`TalkingHeadShowcase`；入口为本目录的 `index.tsx`。它把已冻结主时间轴的源区间映射到真人画面、人物alpha和图形层，用于观察19项参考效果的实现方向。它不是参考原版模板，也不是新的主剪辑器。

本模块不改变 `src/Root.tsx` 或模板库 `src/template-library/index.ts`。既有模板目录仍是 **55个composition**；本模块是一项独立showcase，内部有19种效果分支及本条结尾配图，不追加成“74个模板”。

## 文件与接口

- `GraphicLayers.tsx`：原创透明图形层；`GraphicLayer`由主组件传入局部帧，不使用实时动画、随机数、媒体或音频。
- `Showcase.tsx`：原片/alpha合成、场景分支、独立字幕标题、淡Logo；复用已保留MIT许可的 `../remotion-ui/OrbitMotion.tsx`。
- `index.tsx`：注册1080×1920、30fps的独立composition。
- 扩展根目录 `render-showcase.mjs`：按工作目录的props打包、抽取代表帧或渲染静音素材；`tsconfig.showcase.json`提供独立类型检查入口。

```tsx
type SourceClip = {
  fromFrame: number;          // 在最终素材时间轴中的起点，30fps整数帧
  durationInFrames: number;   // 最终占用帧数
  sourceStart: number;        // 原始源时间，单位秒
  playbackRate: number;      // 相对原始源的绝对播放率
  kind: number;
  title: string;
};

type ShowcaseProps = {
  clips: SourceClip[];
  totalFrames: number;
  sourceFile: string;         // render-assets内的同源CFR30视频
  alphaFile: string;          // render-assets内的同源、同期透明人物视频
};

type GraphicLayerProps = {
  kind: number;
  frame: number;
  duration: number;
  width: number;
  height: number;
  title: string;
  accent?: string;
};
```

工作目录保存 `showcase-props.json` 和 `render-assets/`。媒体文件名通过 `staticFile()` 相对该素材目录解析，不能把某个旧项目的绝对媒体路径硬塞到源码。

当前素材目录还需本条 `logo.png`、本机已授权的 `NotoSansSC.ttf`，以及照片墙使用的 `portrait-01.jpg` 至 `portrait-08.jpg`；照片应从本条有权使用的原片提取。媒体、蒙版、模型、私有props、bundle和导出不进入Git。

**当前试剪仍有本条专用时间逻辑：** 绿幕换景和打勾清单共用kind9源段，`Scene`按原片21.75秒切换为kind10；代表帧脚本也要求该kind9段存在。换原片时必须按新口播边界适配这段逻辑及采样，不直接继承21.75秒，也不宣称任意独立kind10片段已通用化。kind20仅用于本条末尾领取资料配图，不计入19项。

## 19项映射

| kind | 效果 | 当前实现及边界 |
|---|---|---|
| 01 | 长条成长 | 透明图表卡片、三条中性示例长条增长；不造业务数据 |
| 02 | 玻璃字 | 半透明胶囊、文字与光线；需在真实背景上查看模糊和对比 |
| 03 | 穿越转场 | 源视频推近/回落、短模糊与扩张外框；不是任意物体的三维穿越 |
| 04 | 剪纸 | 真人alpha、纸张图形、浅色轮廓与阴影；边缘质量受蒙版限制 |
| 05 | 照片墙 | 本条原片静帧网格与前景真人alpha，不使用外来人物照片 |
| 06 | 拉远揭幕 | 全屏真人缩入播放器窗口，保持同源讲话 |
| 07 | 界面世界 | 真人嵌入代码绘制窗口；界面为示意 |
| 08 | 杂志封面 | 杂志式文字层位于真实人物alpha后方 |
| 09 | 绿幕换景 | 人物alpha合成代码背景；名称不代表拍摄时使用了绿幕 |
| 10 | 打勾清单 | 玻璃字/手机画面/贴纸轮播三项依次勾选；当前由kind9源段切换 |
| 11 | 镂空字 | 真人视频裁入SVG大字，另保留同源动态真人圆窗 |
| 12 | 手绘涂鸦 | 原创手绘路径和人物alpha轮廓；不是自动手部/物体跟踪 |
| 13 | 标题墙 | 重复实心/空心文字在人物alpha后方，无固定椭圆假遮挡 |
| 14 | 手机画面 | 原片缩入旋转手机框，按同一角度摆放内容与外框 |
| 15 | 破框而出 | 正常视频与人物alpha共用全画幅源变换，底层裁入独立窗口，人物可越过边框 |
| 16 | 环绕字 | OrbitMotion卡片前后排序；中心为同源同期人物alpha |
| 17 | 数位推近 | 真人画面逐步推近、取景框与倍率；检查脸部裁切 |
| 18 | 收据列印/列表 | 纸张出口、锯齿边、三个真实特效标签；不造价格或成交记录 |
| 19 | 贴纸轮播 | 原创矢量图标沿椭圆运动；没有下载第三方品牌贴纸 |

GraphicLayer以1080×1920设计坐标等比缩放；图形主要在顶部或y约1080–1512，底部y≥1570留给标题字幕。真实人物与图形的遮挡必须在整合画面中检查；其他比例需要重新排版，不自动继承9:16布局。

## 速度与单一主时间轴

1. `clips`从本条冻结的ChatCut主时间轴取得，保留源区间、最终起点、时长和绝对播放率。不要在特效模块重新做语义剪辑或另建竞争主时间轴。
2. `sourceFile`与`alphaFile`都代表**未加速的同一源时钟**。当前`Source`按30fps源CFR取`sourceStart`，再应用同一个`playbackRate`。默认口播相对原片绝对1.2倍一次；不能给预先1.2倍的视频再乘1.2。
3. 原始VFR先按受记录的源时间映射转为CFR30；alpha必须与这个CFR源逐帧对应。源秒、源帧和最终帧不可混用；不能把已剪好/已加速的粗剪文件当未加速源。
4. 渲染输出是已按最终时间制作的**静音H264 MP4素材**，没有透明通道；原片和alpha在内部均静音。导回同一个ChatCut主时间轴时保持1.0倍，锁定原声、字幕、SFX和BGM的映射，避免重复人声或二次加速。
5. 片内封面、固定片尾、三轨声音和正式导出继续由总Skill与当前主时间轴管理。素材渲染成功不等于完整ChatCut导出成功。

## 蒙版预处理

先读[隔离人物分割流程](../../../../segmentation/README.md)。它使用独立 `.runtime/segmentation-venv` 与独立模型目录，不更改主Python环境；具体包版本、模型来源、许可证和SHA在该扩展manifest中维护。

该流程先输出白人黑背景的**灰度置信度视频**，不能直接把它当作`alphaFile`。需将同源CFR视频与灰度蒙版转换为支持真实alpha的中间视频，再检查本模块的透明解码。两文件必须同尺寸、同CFR、同源起点与同时间映射。

MediaPipe不是精细逐帧人像抠像器。已观察样本存在快速模糊手臂/腕部缺失和少量背景残留；低分辨率推理上采样无法恢复已丢失的发丝/手指。单帧能看见人物不证明整段边缘稳定。阈值、侵蚀、最大连通块等调整必须按原片另验，不能无条件复制给下一集。

## 调用与revision

Active Repo：`C:\Codex Workspace\talking-head-editor`。在扩展目录检查，使用本机已配置Node与Chrome：

```powershell
Set-Location "C:\Codex Workspace\talking-head-editor\extensions\remotion-vd44"
. "..\resolve-tools.ps1"
$nodePath = Resolve-EditingNode ''
& $nodePath .\node_modules\typescript\bin\tsc --project tsconfig.showcase.json --noEmit
& $nodePath .\node_modules\eslint\bin\eslint.js .\src\template-library\talking-head-effects
```

先将`$workPath`明确设为本条含`showcase-props.json`的绝对工作目录；它不是系统自动注入变量。以下`r4`只是未使用revision示例，执行前选择本条实际新编号：

```powershell
& $nodePath .\render-showcase.mjs $workPath stills r4
& $nodePath .\render-showcase.mjs $workPath render r4
```

输出进入工作目录`visual-r4/`，代表帧与静音MP4不覆盖已有文件。**脚本只判断该revision的`bundle/index.html`是否存在，存在就复用bundle，并不检查源码或素材更新。** 修改TSX、字体、照片、视频或模型结果后必须使用新的revision重新打包；只有源码和素材均未变，才可以用同一revision从stills继续render。不要为重试删除旧证据或误把旧bundle结果当修复结果。

特效内部文字/动作修改后需要改props或源码并重渲染；导入ChatCut后的MP4不会自动变成逐字可编辑图层。若主时间轴后续删改口播，重新冻结映射并渲染受影响素材，不凭肉眼挪几个字幕。

## 当前状态（2026-10-26，进行中）

本条真人原片已用于人物蒙版样本和R2代表帧检查。R2发现的标题墙固定椭圆洞、破框两层人物坐标不一致已定点修正；相关TSX独立类型检查与ESLint通过。

R3完整静音渲染已启动，本页更新时尚未登记完成；最终ChatCut合成、最终MP4导出、连续观看/试听、字幕同步与用户认可仍须分别核对。这里不声明19项与参考逐帧相同，不把代表帧检查或代码检查写成成片验收。
