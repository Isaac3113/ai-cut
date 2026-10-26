# KB29：可复用代码特效库

日期：2026-10-26。用户授权先搜索GitHub等现成模板，合适的直接接入；后续再按参考19项补缺口、提供跟读稿并接收真人原片。

## 本次接入

入口：`extensions/remotion-vd44/TEMPLATE_LIBRARY.md`、`template-catalog.json`。
独立注册：`src/template-library/index.ts`；不更换既有 `src/Root.tsx` 或ChatCut主工程。

- RenderComp：50套MIT模板，固定 `f648980e528defb7594e24c6447055f0540f340b`。
  原始来源61文件约405KB；保留LICENSE、ASSETS、README、package与逐文件指纹。
  五文件只移除未使用声明，以通过现有严格检查；manifest同时保留上游及本地SHA256。
- RemotionUI：选择OrbitMotion、TextMaskVideo，固定
  `0aecaca2b61a167992e1205d10e4da16d8a71331`，MIT；原始字节、修改和许可全部保留。
  演示包装支持JSON文字/标签替换；TextMask支持静音视频/图片/渐变，缺素材时报错。
- 3项中文示例加上述2项适配演示，共55个Composition；不是55种已复刻参考的效果。
- 使用原有package-lock安装Remotion 4.0.523/React 19.2.3；未新增应用依赖。
  本机缺npm，使用已捆绑pnpm临时调用官方npm 11.6.0执行 `ci --ignore-scripts`，没有改锁文件。
- Noto Sans SC字体SHA256与既有HyperFrames清单一致：
  `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da`。
  二进制不入Git；公开许可保留在public/OFL.txt。

## 复用规则

总Skill新增 `references/effect-library.md`，指向目录和19项差距。
`run-library.ps1` 管理Check/List/Still/Render/Preview，接受JSON props并拒绝覆盖输出。
显式props/输出路径在切换目录前解析；默认输出留扩展out。Preview与Render使用同一props文件。

模板默认是完整图形场景。H264没有透明通道，不能把黑底当透明层。
口播上叠加须另行合成或走已验证alpha路线；不能将这些预览冒称真人成片。
新视频先确定比例，按最终时间重算动作，静音素材1.0倍导回ChatCut。

## 调研后未接入

- RVE 81套模板：大量内容写死，根目录缺独立LICENSE文件；本次不再引入第二套相似大库。
- 21st Video Blocks：手机/照片墙/清单候选接近，但未取得完整Component源码及素材依据。
- MediaPipe Selfie Segmentation、BackgroundMattingV2：可评估人物遮罩，但本次不装模型。
  后者需要同机位无人背景；未来拍摄可多留背景板。
- RVM为GPL-3.0；rembg代码MIT不代表默认BRIA模型可按MIT商用。未自动安装这些模型。
- React Bits是网页实时动画，含Commons Clause；不为普通视觉动画再引入一套依赖。

## 实际验证

独立库typecheck、适配代码ESLint、55项注册已通过；全部55项代表帧实际渲染成功。
已导出图表、玻璃卡片、界面示意、环绕、渐变镂空五个完整MP4；FFmpeg完整解码、帧数、
画幅和静音video-only轨检查通过。代表帧拼图及中文图表已实际查看。

本机证据在 `work/template-library-20261026/verification.json` 及对应视频/图片。
后续JSON参数变体和合成视频分支的结果追加到本节后方；不要将未追加的项视为通过。

追加验证：从仓库根以相对props/输出路径调用，中文环绕卡片与合成视频镂空两种参数变体实际导出，完整解码及180/120帧计数通过，两个代表帧已查看。合成视频输入使用自己生成的图表MP4，不是用户原片；真人输入仍未验。24秒五项预览在同目录template-preview.mp4。独立库typecheck及ESLint在修正参数包装后重跑通过。

完整旧扩展tsc在FollowupCalendar.tsx和FollowupCalendarSquare.tsx已有6个未使用声明错误。
本次独立tsconfig只检查库入口及其传递依赖，不改这两个历史文件，也不把该结果写成全仓检查通过。

未执行：真人抠像、发丝/手指跨帧稳定性、真人视频参考19项完整复刻、最终ChatCut合成、连续人工试听和用户风格认可。

## 参考口播

参考：https://www.instagram.com/reel/De6Aa5fMaFt/ 。21.73秒。
本机faster-whisper medium与small已从既有缓存离线识别音轨；没有安装模型或上传云服务。
按画面将同音误识别校正为拉远揭幕、绿幕换景、收据列印等；第17项为数位推近。
两模型尾句一致。跟读稿属于机器转写加画面术语校正，尚无逐字人工听审。
原片、音轨、机器JSON和参考图只在本机临时分析目录，不提交Git。

## 后续：真人19项试剪实现（2026-10-26，进行中）

上方“未执行／候选未安装”等记录对应初次模板库接入阶段；本节追加后续真人试剪范围，
不改写此前的图形模板验证，也不把后续实现倒填为初次已完成。

- 新增独立 [TalkingHeadShowcase模块说明](../../extensions/remotion-vd44/src/template-library/talking-head-effects/README.md)，
  源码为该目录的 `index.tsx`、`Showcase.tsx`、`GraphicLayers.tsx`；
  扩展根目录 `render-showcase.mjs` 与 `tsconfig.showcase.json` 提供独立运行/检查入口。
- 一项showcase内部按冻结源区间映射19种效果，并保留本条结尾配图；既有目录仍为55项，
  不把分支数量加成新的已验收模板数量。总Skill的 `references/effect-library.md` 已链接该模块。
- [隔离人物分割扩展](../../extensions/segmentation/README.md)使用独立
  `.runtime/segmentation-venv` 与官方MediaPipe模型目录，主Python环境不变；
  包/模型/许可证/哈希由该扩展manifest维护，模型和私有原片/蒙版不入Git。
- 真实原片已用于二元/多类别模型样本比较与R2合成代表帧检查；灰度置信度蒙版和实际人物alpha
  是不同产物。快速模糊手臂/腕部仍有缺边，不能把单帧显现人物写成全片边缘稳定。
- R2发现标题墙静态椭圆洞、破框两层源变换不一致；已定点移除假遮挡、统一源变换，
  TSX独立类型检查及ESLint通过。R3完整静音渲染已启动，本节更新时尚未登记完成。
- 静音素材按最终帧制作，1.0倍导回同一ChatCut主时间轴；原声只按原片绝对1.2倍一次。
  源CFR与人物alpha必须同源同期，不能把已加速粗剪再乘1.2。源码/素材改变须新revision重打包，
  避免 `render-showcase.mjs` 复用该revision旧bundle。

仍待：R3实际完整渲染结果与全片解码、最终ChatCut合成/真实导出、连续观看试听、
字幕与动作同步、人物边缘跨帧质量及用户认可。没有声明参考19项逐帧一致或本条正式成片已完成。

## 后续实检：效果审阅版实际导出（2026-10-26）

R3静音母版已完整渲染828帧；切出的19段均完成逐帧解码，frame MD5与母版对应区间逐帧一致。
ChatCut V2时间轴已导入全部19段，声音保持独立。最终实际导出已下载并通过完整解码：
1080×1920、30fps、H.264/AAC、907帧、约30.233秒、29,618,844字节；
SHA256为 `7e32bcb7b57b3f438a41876fa6f6ae1f005e9484f20f87d777155106a6d2eb99`。

已检查23个ChatCut实际viewer采样画面，并另查最终输出8个入/出场边界帧。
最终音轨ASR已识别19项名称及完整领取资料CTA；这是机器核对，不是连续人工听审。
本机个人Skill已同步27个文件，并核对安装manifest及文件哈希；不据此继承另一电脑的运行状态。

本次结果是特效试剪审阅版，正式封面、社媒文案及精简发布包不在本次交付范围。
运动模糊下的手臂/腕部蒙版缺边和少量残留仍有限制；上述逐帧校验用于证明切片与母版一致，
不证明人像边缘每帧合格、连续观看/试听完成或用户已经认可，也不声称与参考原版逐帧完全相同。
