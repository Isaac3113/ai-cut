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
