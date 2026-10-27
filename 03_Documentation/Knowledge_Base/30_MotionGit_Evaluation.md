# 30 · MotionGit 接入评估与局部动画候选

日期：2026-10-27。审计源码基线：`d63ada2ab6ede9006b4ad1c1198cb77128697ae3`。
范围：现有系统审计、公开源码试跑、官网个人包实际局部制作及同内容A/B比较。
状态：技术检查与编码静帧抽检已完成；未连续观看／听审、未人工逐词校对、未获本条审美认可。
本次仅为本机隔离候选，没有注册新的正式Skill、替换主剪辑路线或实施下列检查器修复。

## 1. 结论、现有定位与实际工具链

**保留ChatCut、语义粗剪、同步原声与字幕的单一主时间轴；模板按表达任务补充概念解释，不设为默认。**
新工具已证明一条局部制作路径可以运行，尚不能证明整套替换后更好、更快或适合任意素材。

| 对象 | 实际职责与已实施证据 | 不可扩大解释 |
|---|---|---|
| 总Skill | 理解完整原声、比较take、保留否定／条件、删除无关与重复，再统一剪后帧映射 | 语义取舍由会话判断，不是静音检测或模板自动保证 |
| AIVD8 | ChatCut Script、独立视频／人声／BGM／SFX、字幕和**ChatCut原生MG**；平台真实导出 | 不能从平台MP4元数据推断本机Remotion／HyperFrames做了这条片 |
| AIVD8本地辅助 | FFmpeg音量与素材处理、ASR疑词复核、image_gen封面 | 响度不是听感，ASR不是人工逐字听审 |
| AIVD9 | Remotion **4.0.523**／React、MediaPipe遮罩、FFmpeg同源合成；828帧母版分19段回ChatCut，已有907帧实际导出 | 19项是特定样片的效果分支，不是19套通用自动剪辑模板 |
| HyperFrames | **0.8.35**按短状态卡／HTML动画场景调用，已有历史201帧渲染与采样验证 | 不是每条片必用，本次MotionGit组件也不由它渲染 |

已有特效可以继续参数化，但人像遮罩、源时钟、画幅、品牌及素材质量必须分别适配。
当前主流程适合真人知识口播、AI教学、营销方法及系统功能讲解；长访谈先走主题切片分支。剧情改编需要另外的分镜流程；只有文稿时先收集真人原片，不自动配音或生成数字人。
源入口：[总Skill](../../skill/talking-head-editor/SKILL.md)、[两引擎分工](../../skill/talking-head-editor/references/reference-motion.md)、[KB29](29_Reusable_Effect_Library.md)。
版本证据：[Remotion依赖](../../extensions/remotion-vd44/package.json)、[HyperFrames入口](../../extensions/hyperframes-vd44/package.json)。

## 2. 质量根因：规则、调用、实现、素材与未验证

| 类别 | 具体发现 | 本轮状态 |
|---|---|---|
| 规则适用 | 旧头像片尾、全程水印文字与当前固定片尾例外混排；无同期作者的拍屏不能造假圆窗 | 当前个人规则优先；仍需降低文档与检查器歧义 |
| 调用与证据 | cadence检查可能exit0但JSON为false；代表帧、登记事件或成功渲染不能证明每3秒重点有效 | 必须读取报告与实际导出，不能只看退出码 |
| 字音与字幕 | AIVD8曾修复接缝；ASR仍有20／50ms紧余量，部分短词卡仅9–14帧 | 不据此断言当前仍断字，也不能未经听审宣称完整 |
| 素材 | 拍屏倾斜、小字、手／鼠标遮挡；AIVD9快速手臂／腕部遮罩仍有缺边 | 模板不能恢复被挡住的信息或凭空提高分割细节 |
| 验证缺口 | 完整动态观看、听审和人工逐词对齐未完成 | 与技术通过、用户内容确认分别记录 |

以下是**尚未实施的代码修复建议**，与当前ChatCut在线成片是否失败不是同一结论：

| 实现问题 | 实际源码位置与证据 |
|---|---|
| 检查器固定横版 | [audit_chatcut_snapshot.py:18](../../scripts/audit_chatcut_snapshot.py#L18)要求1920×1080；[verify_review_media.py:73](../../scripts/verify_review_media.py#L73)同样固定，[:83](../../scripts/verify_review_media.py#L83)把取样拉成640×360 |
| 合法帧量化误报倍率 | [audit_chatcut_snapshot.py:42](../../scripts/audit_chatcut_snapshot.py#L42)固定倍率容差；本轮内存探测1.03秒／1.2倍→26帧仅差0.25帧却失败 |
| 品牌与人像例外未编码完整 | [visual_contract.py:162](../../src/talking_head_editor/visual_contract.py#L162)无条件PIP；[:184](../../src/talking_head_editor/visual_contract.py#L184)片尾品牌绑定；[:191](../../src/talking_head_editor/visual_contract.py#L191)水印整片覆盖 |
| 本机无SFX分支缺文件 | [motion.py:207](../../src/talking_head_editor/motion.py#L207)提前返回，而[audio_controls.py:15](../../src/talking_head_editor/audio_controls.py#L15)、[:42](../../src/talking_head_editor/audio_controls.py#L42)仍读SFX报告／WAV；静态控制流判断，未跑媒体复现 |
| 本机片尾能力落后于规则 | [motion.py:238](../../src/talking_head_editor/motion.py#L238)使用`-an`；不能直接保留固定模板自带音轨和独立1.2倍 |
| Showcase存在案例耦合 | [Showcase.tsx:25](../../extensions/remotion-vd44/src/template-library/talking-head-effects/Showcase.tsx#L25)固定21.75秒；[render-showcase.mjs:17](../../extensions/remotion-vd44/render-showcase.mjs#L17)仅按bundle存在复用，[:20](../../extensions/remotion-vd44/render-showcase.mjs#L20)固定浏览器路径 |

字幕映射已有真实实现：[timeline.py:82](../../src/talking_head_editor/timeline.py#L82)、[:271](../../src/talking_head_editor/timeline.py#L271)。
因此不能把所有问题归因于“缺动画”，也不能把增加模板当作字音、混音与检查器修复。

## 3. 来源身份、环境和许可边界

| 路线 | 固定身份 | 实际做到哪里 |
|---|---|---|
| 官网个人包 | Modern Editorial Portrait **2.7.17-alpha.2**；官方helper **1.0.0-rc.50**，官方SHA核验 | verified、setup、doctor、plan、preview成功；tail-v3真实render退出0 |
| 官网扩展接口 | motion-kit库 **0.3.0**与其公开参数合同，同一已验个人包内的控件路线 | 本轮使用highlight／underline；不称原生完整组复现 |
| 公开源码补充 | adu-motion-video commit `4a52ae2cff542cfb0bfcf6e93e5120c55d0110cf`；classic-performance `1.1.1-candidate` | 独立副本真实编译／渲染15.7秒，最终组件耗时75.5秒 |
| 初始目录／其他候选 | 早期官网目录2.7.13；Kinetic Tech公开候选 | 不用classic运行记录给官网新版背书；Kinetic Tech未运行 |

官网包并非前述公开classic包；工具版本、模板版本、schema版本与helper版本分别记录。
公开classic是HTML／CSS／JavaScript DOM动画，由Chrome／Playwright／FFmpeg输出，不是Remotion。
`.motion`是容器和契约，不代表任意包都用同一引擎或自动互通。

主要来源：[模板目录](https://github.com/motiontemplates/all)、[固定公开源码](https://github.com/adunext/adu-motion-video/tree/4a52ae2cff542cfb0bfcf6e93e5120c55d0110cf)、[格式规范](https://motiongit.com/spec)、[本次官网模板](https://motiongit.com/@adunext/template-01-integrated-portrait)。

本机官网环境使用标准便携Node **24.19.0**，以临时`PATH`指向现有Python和标准Node/npm，使用无空格自定义cache后setup／doctor成功。
默认Windows AppData虚拟化路径曾在ensurepip阶段失败；这是环境阻断，不是模板美学或画幅失败。
成功恢复只证明当前本机路径，不保证另一台Windows机器已通过。

全程经已验证官方helper与公开schema处理，没有手拆、修改受保护内核或绕过授权。
`private.motion`包含个人Key：**不得进入Git、知识库正文、日志分享或学员包**；本报告不记录账号ID、keyID或原Key。
公开classic的MIT许可与依赖许可需保留；不能推断原作者人像、音乐和演示素材也获得复用授权。
官网时间／圆标属于当前模板声明的视觉设计，输出保留；它与用户Logo需独立避让。

## 4. 输入输出兼容矩阵与时钟合同

| 项目 | 兼容判断 | 本次约束 |
|---|---|---|
| 已剪媒体文件 | 文件级直连 | 底片已按绝对1.2倍处理；新组件按1.0倍使用，不重复加速 |
| 全片规格 | 需适配，最终技术已验 | 1080×1920、30fps、1651帧；官网组件按60fps制作，再适配为307帧30fps |
| 句级字幕 | motion-kit支持 | 40条完整句级字幕；不制造逐字highlight.units，不宣称逐字高亮 |
| 局部字幕时钟 | 需显式映射 | tail使用源caption35–39，减去样本44.8秒一次，原字幕／原声不改 |
| 同步声音 | 文件级直连 | 两版共用同一完整AAC；组件模板声音剔除，避免增加BGM／SFX变量 |
| 纯拍屏人物 | 有条件适配 | 没有同期本人时省略额外presenter；UI里的AI角色不是讲师 |
| 竖屏实操可读性 | 全片试排不合适 | 官网media仍用横向容器，实际竖片约342px宽；因此保留A真实证据画面 |
| 概念归纳 | 局部候选已运行 | 只在末段用两个highlight／underline，完整文字需看最终编码 |
| ChatCut工程 | 导入路径未实测 | MP4可作为素材的设计不等于已重新导入；内部控件不会自动变成原生MG层 |
| 任意模板自动选择 | 未实现／未验证 | 不能声称一键按任意原片自动选型并验收 |

native要求真实逐词证据及其原生媒体合同；句级输入与无同期人像情况按公开guide选择motion-kit。
motion-kit不是旧`mode=components`，也不能与native任意混合在同一模板时间轴。
`narrationMap`按完整句与真实相交captionIndices绑定；不能为动画时长删句、拼造步骤或延长音频。
普通口播3～5秒、实操约3秒的要求仍需按真实内容检查；两个标题变化不是全片节奏已通过。

## 5. 实际实验、取舍与最终A/B

A取AIVD8正式导出的`[0.1,55.133333)`秒区间，从0计时为55.033333秒，保留原讲话与程序声音。
这是完整问题、实际演示到限制说明的样本，不含正式0.1秒封面、课程CTA或固定片尾。

**官网完整55秒project-v1仅做到plan／preview，没有全片模板渲染。**
主执行者看实际0.8／28.5秒预览，media横容器把竖屏证据缩小到约342px宽，不适合看按钮／衣服字样。
因此没有继续强套整段：最终B保留A的`[0,1344)`帧，只替换`[1344,1651)`，即44.8–55.033333秒。
官网组件长度10.233333秒、最终307帧，两个highlight／underline用于末段归纳；其余A不重新语义剪辑。

独立审阅查看tail-v3的0.60／3.80／6.30／7.90／10.20秒实际预览。
修订把不自然的“但／是”断行改为摘要“衣服没问题，剧情却改变”；完整原字幕／原声未改。
所看主字完整、没有遮挡字幕；6.30秒阶段性模糊后转清晰，10.20秒主内容不再模糊。
预览中末句字幕偏灰被列为风险；主执行者随后查看实际编码45.4／53.2／55.0秒：主字完整，Logo不重叠。
53.2秒末句字幕为白色清晰，55.0秒为末端淡出，不能再写成整段字幕发灰。
仍有局部时码0–10秒，不能当作55秒整片时码；模板原生蓝也不等于AGI精确青色。

官网tail-v3真实render退出0，helper总耗时**30.824秒**；最终拼接**4.801秒**。
这不是全流程制作时长，更不是官网与ChatCut速度的严格基准比较。
本轮没有调用付费生成或购买云渲染，使用已有素材与本机算力；未查询账号积分账单，也未统计完整人工选型、调参与排错工时，不能据此给出端到端费用或投资回报。官网路线已有一次真实渲染成功，尚无批量或跨机器稳定性结论；后续改稿仍需重新计划、预览与渲染。
公开classic的15.7秒／75.5秒候选只作补充研究；其UI缩小、残余时钟与品牌文字问题不混成官网tail的结果。

| 最终文件 | SHA256／大小 |
|---|---|
| `A-existing-workflow.mp4` | `4bc96ec55da2acd50af5fa3d4050e8ae85036bd0c8699da9b3bfef7399e77b8d`；67,951,994 bytes |
| `B-official-motiongit-hybrid.mp4` | `b38c0754fd858677a438a7285bcdd26e9e65f00ddd9275009a8a877f6cb3d5c8`；51,294,147 bytes |

最终文件仅在本机`work/motiongit-evaluation-20261026/outputs/`，不是用户05最新版的新正式交付。
两文件均1080×1920／30fps／1651帧／55.033333秒，完整解码exit0。
编码AAC共同SHA256：`15f5c7c265d7b02303f4e2b292463a3498e29952c60612ec938abc3e9b08828f`。
解码PCM共同SHA256：`2f0faeff4bc0bb9ad0f2044debcbe6cc1cb62544d7e803662327677cb17a1c84`。
音轨相同证明声音比较变量受控，不证明原片字音已无缺陷；官网自身SFX已剔除，其音效表现本轮未评估。

## 6. 推荐调用、回退与后续改进

1. 继续由ChatCut管理语义粗剪、原声、字幕和最终时间轴；先冻结内容，再选外部视觉表达。
2. 按真实任务选择：步骤／关系／概念归纳可用模板；实操证据优先全屏与准确局部聚焦。
3. 不因主题涉及AI就强制科技风；不为固定三项模板凑第三项、不用通用标签替代真实结果。
4. 先核对公开参数、容量、语言、媒体、动作与声音合同，再经plan审阅、实际preview及render。
5. 外部动画按最终时钟与1.0倍合回；若不合适，保留既有A路线即可回退。
6. 当前仅有本机隔离副本与人工选择，未注册正式Skill，也没有一键自动模板路由或自动回退产品。

本机执行入口为`work/motiongit-evaluation-20261026/prototype/run_official.py`；它调用经校验的随包helper，原包与授权仍需保留。候选参数与公开制作记录保存在`prototype/official-candidate-records/`。新制作按官方`new → plan → prepare → preview → render`顺序创建新输出，真实审阅计划和预览后才设置对应review标记；参数变更重新检查，不跳审核。该入口含本机测试路径，未作为正式Skill安装，也不随本次Git文档同步；不能把它称为跨电脑一键生产命令。

建议优先修画幅检查、帧量化容差、规则例外、缺SFX分支，再参数化已成功案例。
这些是后续建议，本轮没有改正式检查器、剪辑源码、Skill默认或安装状态。
官网完整原生组、其他控件、长期稳定性和新机器环境仍需分别测试，不能由本次两个控件外推。

## 7. 验收边界、证据入口与跨电脑交付

| 检查 | 状态 |
|---|---|
| 个人包身份／helper、setup、doctor | 当前本机已完成；不是美学认可 |
| 官网tail真实导出／最终局部合成 | 已完成；完整55秒模板试排仍只有preview |
| 最终帧数、尺寸、全解码、AAC／PCM同一性 | 已完成，绑定上表文件哈希 |
| 实际预览与编码静帧 | 已按上述范围查看；不能代替连续动态观看 |
| 完整连续观看／听审／人工逐词200ms核对 | 未完成，不报`passed_final` |
| 重新导入ChatCut／用户审美认可 | 未完成；不能声称正式工程已接入或默认采用 |
| 正式源码与安装Skill | 27文件不变；正式最新版6文件不变；此次只新增技术报告 |

本机详细证据根：`work/motiongit-evaluation-20261026/`；这些路径不随Git同步。

- `research/existing-system-audit.md`：规则、实现缺口与源码行号。
- `research/historical-quality-and-sample.md`：真实历史工程、源映射与同内容样本。
- `research/motiongit-source-audit.md`：公开来源、版本、引擎、容量与许可。
- `qa/official-input-binding.json`、`qa/official-tail-binding.json`：完整输入与局部时钟。
- `qa/official-comparison-assembly.json`、`qa/official-final-comparison-technical.json`：拼接、最终文件与技术QA。
- `qa/B-official-final-encoded-contact.jpg`：最终编码联系表；源图片不进入Git。

原片、实验视频、字幕证据、个人包、凭据、依赖cache和可恢复本机工程均不进入Git。
另一台电脑pull只能取得本报告及已受控源码，不能因此获得用户媒体、个人授权、已验运行环境或本机实验结果文件。
正式交付入口保持最新1个MP4、16:9／9:16两封面与发布素材3个TXT；不混入本报告或实验包。
本轮Git只包含本报告、知识库入口与变更日志；以实际commit／push回执确认同步，不由文档同步推断正式接入或媒体已同步。
