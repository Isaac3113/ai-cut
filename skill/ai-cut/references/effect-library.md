# 可复用代码特效库

2026-10-26：Active Repo 的 `extensions/remotion-vd44/TEMPLATE_LIBRARY.md` 和
`template-catalog.json` 是目录入口。主Skill仍管理口播和ChatCut主时间轴。
模板使用独立 `src/template-library/index.ts`，不改变既有 `src/Root.tsx`。

真人原片的19项试剪另读[独立Showcase说明](../../../extensions/remotion-vd44/src/template-library/talking-head-effects/README.md)：
入口为 `src/template-library/talking-head-effects/index.tsx`，由冻结主时间轴的源区间、
同期人物alpha和图形层合成。它是独立composition，不改变既有55项模板目录或ChatCut主时间轴。
蒙版准备按[隔离人物分割扩展](../../../extensions/segmentation/README.md)，不要把灰度蒙版直接当透明人物视频。
本条部分时间边界仍需按新口播适配，源码/素材改变后使用新的render revision，避免复用旧bundle。

## 来源与范围

- RenderComp/free-remotion-templates，固定提交
  `f648980e528defb7594e24c6447055f0540f340b`：50个参数化模板，MIT。
  `src/vendor/rendercomp/upstream-manifest.json` 保留上游Git blob及SHA256、本地哈希；
  五个文件仅删除未使用声明，保留全部许可。上游package.json只作来源记录，不执行安装。
- riaz37/remotion-ui，固定提交
  `0aecaca2b61a167992e1205d10e4da16d8a71331`：选择OrbitMotion和TextMaskVideo，MIT。
  原始源码、许可、修改与哈希在 `src/template-library/remotion-ui`。
- 复用现有Remotion 4.0.523、React 19.2.3依赖锁。模板MIT不改变引擎自己的许可。

## 调用顺序

1. 用户要求参考特效或复用模板时，先看真实画面及19项对照，选择合适组件。
   上游能力、下载完成和示意预览都不能冒称完整复刻。
2. 核对本条确认的比例、原片、原声、最终速度和主时间轴。库预览画幅不是用户选择。
3. 用JSON props替换内容；本条配置放私有work目录，保留新revision。模板示例收入、数字、
   公司、头像、点赞等只是测试资料，不能作为业务事实或直接套给用户。
4. 新组合放 `src/template-library`，不覆盖vendor原始证据，更新目录及来源。
   简单可编辑重点字仍优先ChatCut原生层，不为普通文字叠加整套外部动画。
5. 外部动画按最终时间生成，1.0倍、静音导回ChatCut。人物、字幕、音效共用时间映射；
   口播只加速一次。全屏替换仍执行同源动态真人圆窗规则。
6. 检查入/停/出帧、实际渲染、中文长文字和画幅；导入后检查真实合成及最终MP4。
   库测试不代替本条连续观看、试听和人工同步检查。

## 能力边界

- 50个上游模板加2个适配组件不等于参考19项已经同款完成。
- 图表是完整图形场景；玻璃模板是下三分之一卡片；播放器是图形示意。
  放入口播、改中央胶囊、输入真人视频或换画幅均需适配。
- OrbitMotion提供前后层级，不能生成透明人物；矩形原片不等于人物轮廓。
- TextMaskVideo的静音视频、图片、渐变分支分别验证，不互相替代。
- 剪纸、换景、背后标题墙、照片墙前景、破框和跟踪轮廓需要人物遮罩。
  初次模板库接入未包含人物抠像；后续独立Showcase使用隔离MediaPipe流程与真实原片样本，
  不代表精细发丝/手指、整段跨帧稳定性或完整参考复刻已经通过。
- MediaPipe的版本、模型和许可在隔离扩展单独维护；BackgroundMattingV2仍为候选，
  不因代码模板可用就安装其他模型或继承其素材授权。
- 转场示例两张图形卡片不自动成为任意口播片段的转场。
- 原片、模型、缓存和渲染视频不进Git。OneDrive保存媒体，Active Repo保存源码和技术KB。

## 使用与验证

在扩展目录使用 `run-library.ps1 -Action Check` 检查库入口，`-Action List` 列实际注册项。
`-Action Preview` 开模板Studio；`-Action Render -TemplateId ID -PropsPath JSON -OutputPath NEW`
导出独立素材。脚本拒绝覆盖输出，不自动修改任何ChatCut工程。

`verify-library.mjs` 用真实浏览器渲染全部注册项的代表帧和五个完整示例，输出带哈希
的verification.json；新增模板时同步目录条目与数量。实际结果与历史兼容问题见KB29。
