# 文件与数据

`project.json` 保存 source、transcript、assets、plan、revision、fixture、style_approval、delivery。历史 `history/r000001.json` 为完整快照。输入文件按 SHA256 命名保存；禁止原地编辑受管理文件。项目没有数据库和外部后台。

转写导入最小结构（时间单位为秒）：
```json
{"schema_version":1,"words":[{"id":"w000001","text":"如果","start":0.5,"end":0.9,"confidence":null}]}
```
字词时间来自真实识别/标注，confidence=null 表示没有置信度。不可均匀分配字符伪造时间。文稿为参考，不替换原声。句子可按标点和停顿组合，但剪辑锚点始终回到词时间。

方案示例仅展示格式，不是建议剪辑内容：
```json
{
  "schema_version":1,"base_revision":5,
  "clips":[
    {"id":"c001","start":1.0,"end":8.0,"reason":"完整观点及其条件",
     "layouts":{"landscape":{"fit":"contain"},"portrait":{"fit":"contain"}}}
  ],
  "deletions":[{"start":0,"end":1,"reason":"原片开始未说话"}],
  "caption_corrections":{},"overlays":[],"style":{},
  "semantic_review":{"status":"reviewed","evidence":"实际上下文审阅记录"}
}
```
示例假定原片恰好8秒。deletions 必须覆盖所有未保留的原片区间；按完整缺口记录，内部多个删除理由可合并说明。clips 的数组顺序是输出顺序；不能重叠使用同一原片区间。裁切边界不能深入字词25ms以上。每片段向上取整到30fps一帧，音视频同时补齐，最大约33ms；接缝仍需听审。

`caption_corrections` 为 `{word_id: "校正文字"}`，同时写 `correction_evidence`。它只更正显示，不能改变实际原声。关键数字/否定词的改动必须有可定位原声证据。

overlay 必需 `id, clip_id, offset, duration, purpose`，offset 为片段开始后的秒数；mode 为 full 或 pip。素材类型增加 `asset_id` 与可选 `source_start`。图形类型增加：
```json
{"graphic":{"type":"title","title":"一句标题"}}
```
还支持 `keywords`（同标题卡）、`flow`（title+nodes，1～5个）、`bar`（title+items [{label,value}]、unit、evidence，最多6项非负值）。图表必须有真实依据，不合适的数据用文字解释。轻动画为淡入淡出，不宣称复杂 Vox 动画。

素材 metadata：
```json
{"license":{"kind":"free","url":"https://www.pexels.com/license/"},"source_url":"实际素材详情链接","author":"实际作者","purpose":"具体用途"}
```
kind = provided/free/paid。paid 另需 preview_url、price {amount,currency}，并有真实用户 approval。许可与文件哈希绑定；素材换内容要重新登记。图库风险/商标/可识别人物的具体限制由会话核实记录，字段存在不代表任何用途都获许可。

安全构图默认 contain 保留全图并填背景。cover 需 x/y（0到1）与 review_evidence 指出实际检查的人脸、手势、信息区域。横竖可独立设置。字幕在两版按各自宽度重新断行；不能把横屏整体拉伸。

style 可覆盖 font_size(28～84)、accent/background/caption_color(#RRGGBB)、keywords、music_gain_db(-36～-12)、loudness_lufs(-20～-14)、true_peak_db(-3～-1)。配乐用 plan.music_asset_id。经用户认可的节奏、素材密度可写 style.editorial_preferences 对象供后续会话遵循；该字段供判断使用，不会机械驱动删减比例。

## 0.1.3 向后兼容扩展

- `output_formats`: 默认 `["source"]` 按显示宽高（计旋转/SAR）选一版；明确双版 `["landscape","portrait"]`。原版素材与历史不改写。
- `style.playback_speed`: 新计划1.1，范围0.5–2；旧计划缺省1。clip位置、overlay offset/duration和step_times仍用原片秒，编译时共同除以速度并补齐30fps；音乐保持自然节奏。
- `graphic.type=states`: 并列状态不画箭头；`flow`才连接。`nodes`配`step_times`，每个节点一个从0递增的原片相对时间，最后一个须小于overlay.duration。`mode=banner`为安全区内的关键词条；`graphic.subtitle`可提供短说明。
- `caption_groups`: `[{"word_ids":["w1","w2"],"text":"Webinar"}]` 合并相邻ASR碎片，使用原有首尾时间，保留source_word_ids并要求correction_evidence，不能剪断组合术语。
- `render --mode draft`: 完整1080p、待听审/风格反馈的迭代版。不得作为最终验收通过的证据；package仍用--draft。

## 0.1.4 自然字幕与画面扩展

style新增caption_bold（布尔，缺省true保持旧版）、caption_outline和caption_shadow（0～4，缺省3/1）。0.1.4自然字幕曾显式false/2/0、keywords=[]；不改变SRT文本/时间。本轮保留基础自然样式，但新增显式keyword动画，不能把历史空列表当成禁止重点字。新建方案默认music_gain_db=-29，历史显式增益不改写。对象动作动画由illustrations模块输出视频asset，仍使用已有overlay及资产许可/审阅字段；schema版本不变。详见visual-storytelling.md。

## 0.1.5～0.1.6：重点动作、独立SFX与本人片尾

schema_version仍为1，以下字段可省略，旧计划没有这些字段时不自动追加效果或片尾。不用null代替可省略的对象。当前个人偏好明确启用相应功能时，必须写入新方案并验证；不能只更新规则文件。

### visual_effects：人物推近和短暂重点字

每个事件必需id、clip_id、offset、duration、kind、purpose。两类事件表中的id合并检查唯一；visual_effects与sound_effects每表至多500项。clip_id必须属于保留片段；offset≥0，duration≥0.08，且整个事件在该片段的原片区间内。时间单位是该clip开始后的原片秒，不是成片秒；输出起点=clip.output_start+offset/playback_speed，时长同样除以速度并截在片段输出边界。

- kind=punch：factor缺省1.08，允许1～1.14；必须提供review_evidence说明实际看过脸、手势和边缘。target缺省presenter，先推近真人再叠素材；scene表示明确审阅后的整幅画面推近，会包括素材，须防止裁掉标签。x/y允许0.05～0.95，默认0.5；同一clip同一target的多次推近沿用第一个事件的焦点。
- kind=keyword：text为1～24字符的非空单行原话重点，color可用#RRGGBB，默认白色。位置x/y允许0.05～0.95；渲染默认x=0.5、y=0.72，并按字体、118%峰值缩放和实际位置检查边界/字幕安全区，不因坐标合法就保证文字放得下。
- 重点字追加到ASS的独立显示层，不改基础SRT原文和时间。自然字幕仍可保持caption_bold=false、outline=2、shadow=0。旧style.keywords=[]不禁止新的显式keyword事件。

以下是合并进已有有效计划的片段示例，不是可单独应用的完整方案：
```json
{
  "visual_effects": [
    {"id":"p1","clip_id":"c001","offset":1.1,"duration":2.2,"kind":"punch","factor":1.08,"target":"presenter","purpose":"跟随这句完整观点","review_evidence":"填写实际构图检查位置"},
    {"id":"k1","clip_id":"c001","offset":3.3,"duration":1.1,"kind":"keyword","text":"客户状态","x":0.5,"y":0.68,"color":"#FFFFFF","purpose":"仅当原话确实说到客户状态"}
  ],
  "sound_effects": [
    {"id":"s1","clip_id":"c001","offset":3.3,"duration":0.22,"kind":"tap","gain":0.05,"purpose":"客户状态重点字出现的轻提示"}
  ],
  "visual_rhythm":{"enforce":true}
}
```
必须用真实clip与原话替换示例，补齐全片视觉安排、已有删改和审阅；本示例本身不保证全片5秒覆盖。

### sound_effects：与BGM分开的轻短音效

当前支持本地原创程序音效tap/pop/swipe，不是任意外部音频asset_id接口。每个事件时长0.08～0.7原片秒，gain缺省0.05且范围0～0.05。输出事件按主时间轴当前绝对速度生成，事件不能叠加成更大的提示声。

音效先预整平至-6dBFS峰值，再施加gain。gain=0.05是约-26.0206dB增益，生成轨的最大峰值约-32.0206dBFS；它不是系统音量5%、相对人声5%或最终响度。只在重点事件安排，刺耳时继续降低，不能每次视觉变化都响。

SFX在既有人声+BGM基底完成后独立相加，normalize=0，之后不再整体归一化或调低人声。输出保留sfx-only.wav、finished-mix.wav、sfx-report.json，后者记录映射事件、预整平基准、增益、实际峰值和listened=false。正式final且有SFX时要求plan.sfx_review的listened=true和真实evidence；没有听审先输出draft，不伪造字段。

BGM仍由plan.music_asset_id指定，个人基线style.music_gain_db=-35.020599913279625。程序通用缺省-29不等于当前个人偏好；原有音乐链路的-18 LUFS预整平、侧链与基底处理仍保留。新增SFX不改变该BGM基底增益。

### ending：已登记的本人头像视频

ending为对象，包含asset_id、duration、purpose及可选source_start。asset须为video，许可kind=provided，已有review.description/evidence；purpose记录真实原片头像来源，不能凭provided字样代替本人来源核验。

duration取1～5个最终输出秒，本用户用3秒；source_start缺省0，选用范围必须在资产内。最终时长按30fps取整后追加到正文，不再除以1.1。preview不追加片尾；draft/final追加并把总时长记录到receipt。原片没有增加口播，片尾素材自带音轨不混入。

ending.render_ending_asset可从已看过的真实原片帧和crop生成衍生视频并留.source.json。当前ending.py是16:9客户流程示例模板，包含该片主题与音乐署名；其他主题/授权/画幅必须重新配置并验证，不把其固定文案和署名当通用素材。生成素材可以长于3秒，计划只选已核实的3秒范围，须检查选中末尾的实际淡出。

0.1.6有BGM时单独延伸低音量音乐到片尾，按现有曲目位置衔接并淡入淡出，尾轨在混合前明确回到48kHz/stereo，避免其loudnorm的采样率影响正文。无BGM时片尾静音，不合成新说话声。原声和SFX不因加片尾被再归一化。

### visual_rhythm与overlay.motion_times

visual_rhythm.enforce=true时，在验证计划阶段按最终时间计算事件覆盖，最大间隔不能超过5.001秒（5秒要求的数值容差）。事件来自素材进入/退出、overlay.motion_times记录的内部动作、可渲染visual_effects、正文/片尾边界；普通clip切分本身不计入，不能把连续同镜头拆段来“通过”。

motion_times是相对该overlay起点的原片秒列表，值必须≥0且小于overlay.duration；它是会话实际查看动作后填写的定位信息，不是自动识别出的动作，也不单独产生动画。必须与真实素材对应。

visual-rhythm.json只报告计划事件和最长间隔；有效变化是否真的可见、重点字是否被遮挡仍需看成片，不能把JSON或程序通过当视觉验收。当前同片段的返回/退出效果不自动全部记作新事件，必要时按真实画面补充合理安排，不伪造motion_times。

### 版本、台账与工程包

apply_plan把visual_effects、sound_effects、ending、visual_rhythm写进当前revision的edit-ledger。渲染总指纹包含完整plan、引擎、媒体和字体；视频缓存含视觉事件，原声+BGM缓存保持独立，SFX在当前渲染目录合成。改行为必须升级引擎，不能误用旧缓存。

工程包现在额外包含当前visual-rhythm.json、sfx-report.json、sfx-only.wav（存在时），并保留原有原片/素材/历史/字幕/报告。它仍是程序工程，不是NLE原生分轨草稿；完整音频缓存和运行环境不因这些字段而自动包含在包内。

### 0.1.7：正文头像素材连续进入片尾

最后一个保留clip内的full模式overlay，只有asset_id与ending相同、overlay结束恰在该clip结束、素材源区间的source_start+duration恰等于ending.source_start时，才识别为同一素材连续播放（边界容差0.001秒）。此时跳过正文overlay的淡出，避免先露回真人再切回片尾。pip/banner、其他资产、非最后clip或有源时间间隙不能借此跳过退出效果。

rhythm_report不把这段同源连续画面的overlay退出和正文/片尾接点算成新的视觉变化；最后片尾结束仍作为区间边界。preview不包含ending，不套用上述连续性豁免。这个判断只解决衔接，不自动证明视觉节奏或最终观看已通过。


### 0.1.8 缓存版本维护

完整输出指纹仍含引擎版本。普通片段由VIDEO_PIPELINE_REVISION加源SHA、片段/字幕/效果、素材SHA、样式/比例/速度/字体共同确定；改公共像素、字幕或时序算法必须递增此版本。只有实际连续到片尾的最后满屏overlay增加CONTINUOUS_ENDING_REVISION及ending依赖。改连续片尾算法必须递增后者。preview没有追加片尾时，保持普通淡出并使用普通片段键；不得计入不可见片尾边界。不得为重试篡改attempts计数或复制失败文件作为有效缓存。


## 0.2.2 增量契约
仍为schema_version=1、同一compiled clips整数帧时间轴；旧合法计划默认行为不变。顶层和style/overlay/effect/layout未知执行键报错，不把拼错colour变成默认白字。

- overlay.asset_speed：0.5～2，省略按旧口播速度；素材原片区间为source_start至source_start+duration/style.playback_speed*asset_speed。offset/duration锚定主片段；最终显示时长不由素材速度改写。
- keyword：color=#RRGGBB；font_size=36～96；outline=0～4独立于color；bold布尔；animation=pop/settle/fade。实际ASS消费每项，不是空配置。
- style.encode_headroom_db：-3～0，最终AAC编码前统一衰减，明确影响含人声的整个混音，默认0兼容历史。
- `render --mode rough`：深拷贝视图移除包装/BGM/SFX/片尾，完整原声段落不变；输出latest-rough.json和独立structure_fingerprint，不覆盖latest-render.json。切段/字词边界仍严格验证。
- workflow packet与当前plan/source/transcript/assets/rule_version绑定；rough单独与结构绑定，换素材不要求重新识别/粗剪。历史版本不被重写。
- QA新增每版quality_checks：full_watch/full_listen/full_captions/privacy/color/overall；status四值pass/fail/unverified/not_applicable。完整观看/试听的pass必须连续模式和覆盖全时长；字幕pass必须all_captions和当前总数。最终包不能缺项。
- package --audience external过滤无原始分发授权的raw，DEPENDENCIES.json列哈希和withheld；internal是给本人继续编辑的包，不能当外部分发授权。


0.2.5新任务默认style.playback_speed=1.2，旧已保存计划不会自动改值；缺speed的历史计划仍按1倍。品牌与圆窗审计是独立schema_version=1的只读证据合同，见brand-and-presenter.md；不把这些字段塞进不支持的本机plan。当前本机mode=pip表示素材小窗，不等于强制真人圆窗，未实现的渲染分支不能通过规则文字冒充。

overlay.caption_theme支持default/dark；dark仅全屏素材。改变ASS外观不改SRT文字和时间。QA的ass_sha256也是正式验收必需字段，旧QA缺少时须重检。
