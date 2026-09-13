# ChatCut 执行与恢复

用户已选择 ChatCut 网页插件进行本片重剪，保留 master-playbook 和 user-preferences 的全部剪辑合同。后续别的原片仍按用户选择决定工具，不把本次授权扩大为所有文件默认上云。

## 接手

1. 读原工程 revision、源片哈希、已有转写/删改记录，保留原片与历史版本。读取已保存的 ChatCut projectId；有工程就 target/read，不重复创建。一次任务只使用一个活动语义时间轴。
2. 官方 chatcut-plugin-basics 是接口入口；从当前工具 Schema 取字段，不把文档宣传当能力证据。插件安装、OAuth 成功、上传、时间轴修改、渲染、观看、试听分别记录。
3. create_project / get_editor_url 的 browserHandoff 用于右侧 Browser，完整保留内部参数；公开链接使用 editorUrl。不得保存 OAuth、上传令牌或临时登录链接进工程包/Git。

## 小 Skill 何时调用

| 阶段 | 调用 | 必须产生的实际证据 |
|---|---|---|
| 本地素材进入工程 | asset-import；import_media + 官方 upload-media.mjs | assetId、原路径/哈希、上传完成状态 |
| 口误/重复/结构 | talking-head-guide；read_script → apply_script | 修改前后 Script、保留/删除理由、源片与成片帧对应 |
| ASR 错字 | manage_transcript fix，先 preview | 旧词/新词记录；修正后重读 Script |
| 长停顿 | clean_script 仅处理已判断可压缩的静音 | 被改停顿和节省时间；不机械删除“呢/啊/嗯” |
| 流程/关键词 | create-motion-graphics，inline JSX | 实际 assetId、可编辑文字/配色、逐步动作时间及合成帧 |
| 基础字幕 | edit_captions / read_captions | 明确声音来源、真实卡片、越界与提前/滞后检查 |
| 分轨精修 | detach_audio / edit_item / smooth_audio | 原声不重复播放；逐轨增益、淡入淡出与最终测量 |
| 画面审查 | verification / preview_timeline | 已查看的真实帧；成功 URL 不是看过 |
| 成片 | export / submit_export / track_export | complete 的 renderId、本地 MP4、SRT 和检查报告 |
| 错误 | known-errors | 原错误、修复原因、一次明确修复后的证据 |

## 可编辑时间轴

原片片段做主体，不导入旧的扁平成片冒充可编辑工程。按 Script 选择完整语义，再将所有主体片段统一到默认1.2倍或用户本条指定的绝对速度，并重新计算整数帧位置；已有1.1倍改1.2倍时从源范围重算，不能叠乘成1.32。之后所有字幕/素材/动作都从这条时间轴取位置，封面占时同步计入。给图层命名：人物、素材与流程、重点字、人声、背景音乐、重点音效。

本次保留本机 r57 作为历史参考，不覆盖它。ChatCut 新剪完成后保存原工程哈希、当前官方快照及 Script；在线手改之后先重新读取，不用过期本地快照覆盖。原有工程恢复与原生修改自动回写并非已实现功能。

流程用真实对象/档案、动作和条件表现。并列状态不用因果箭头。声明“流程示意/情境示意”。配色、字重和动画按当前已提供参考；VD44提供分拍动作参考，本轮及以后颜色从实际Logo提取；按[品牌与圆窗](brand-and-presenter.md)建立独立水印、圆形真人层与核查证据。不把所有基础字幕改成大字。持续画面变化须检查真实输出，抽帧不等于完整观看。复杂动作按[外部动画流程](reference-motion.md)导入，保留源码和帧绑定。

复制视频做画中画后，不能假设fromItemId复制了audioDetached；逐项inspect并显式muted:true，当前接口解析为-60dB（有效静音，非声称负无穷）。保留A1唯一人声。当前工具说明列出layout-screen-face-bubble但实际返回Asset not found，不能声称预设可用；已用可编辑裁切框+圆角实现小窗，并对原片及合成帧比较人脸。全屏素材期间小窗是强制动态圆窗；遮挡“流程示意”、状态词或字幕时移动/缩放小窗或重排素材，不以移除小窗解决。必须实际验明圆形遮罩与源时码，旧圆角矩形的成功不证明圆窗已实现。

## 声音特别规则

detach_audio 后视频必须保持音频分离状态，原声只能播放一次。人声、BGM、SFX 三轨独立。旧的安静 BGM 已处理增益，再导入后 0 dB / 100% 表示保持这个安静文件；需要减半时对 BGM 的所有片段减 6.0206 dB，不动人声。

不把旧 music_gain_db 再施加一次，也不启用整段自动响度去放大轻声音乐。角色 ducking 只有理解实际预处理链后才用；已有侧链处理的音乐不重复处理。音效5%是上限起点；早期ChatCut版为-38dB，最新VD44审阅版为-40dB，不同文件仍须按实际听感校正。音量字段成功不等于听感合格。

本片原声素材-38.5LUFS，原峰值约-19.3dBFS。早期以独立原声+17dB导出，测得-21.6LUFS/-4.7dBTP后仅把人声调到+20.5dB；音乐保持0dB，早期音效-38dB，最新VD44为-40dB。不能把+20.5写成所有原片的默认值：每条片须独立测量，不调低真人来容纳配乐。原声已从历史FFmpeg处理链换成ChatCut原生增益，不能宣称两版PCM相同或专业压缩器已实现。

## Windows 导入兼容

官方 1.10.12 助手的波形 ametadata 文件路径未转义 Windows 盘符。本次可用方式：在本任务独立临时目录前台运行官方 helper，并仅为该进程设置 TMPDIR='.'；这样生成相对文件名，无须修改插件或系统变量。遇到已有占位 assetId 时按错误返回的 retry.args 和新 session 续传同一资源，不重复上传/注册。

本机无写权限/网络权限时走正式权限机制。若是明确拒绝上传文件，停止该上传路径，不换工具绕过。上传失败不转为本机重新扁平合成 ChatCut 主交付。

## 验证与交付

保存不含密钥的 read_project/preview_timeline/read_captions/inspect_item 证据，运行 scripts/audit_chatcut_snapshot.py 检查画幅、连续主视频、独立人声音源、其支持的速度对应和字幕结构。该脚本从0.2.5起默认绝对速度1.2；检查历史1.1成片时显式传`--expected-speed 1.1`；仅对与人声音轨配对的原片片段校验速度，主画面的无声封面/片尾只检查连续覆盖。结构检查不代替声音/画面质量。

用 ChatCut 实际导出的 MP4 做完整解码、响度/峰值/黑帧/冻结/静音候选检查。抽查全部接缝与流程动作。完整连续观看、试听、人工 200ms 同步未执行时显式 unverified，交付审阅版，不写“质量通过”。

按[固定交付](final-delivery.md)交付在线工程链接、含封面实际MP4、TXT/SRT、独立封面、完整制作说明与逐秒/逐帧对照、删改/素材/检查记录。封面以真实资产入主时间轴，导出后实看首帧/边界；read_captions读取含封面与本条速度的全部卡片，再用scripts/export_final_subtitles.py导出同源TXT/SRT。在线流程和重点字可编辑；沿用的头像片尾是独立视频素材，其内部文字是烘焙的，不能声称所有元素都原生可改。XML/归档只在需要时导出并报告丢失效果等限制。

## 正确版本交付

既有浏览器可能保留旧Timeline选择，即使服务器activeTimelineId已是新版。导出后检查真实页面的活动时间轴名称/ID，定位关键动画，并对比实际MP4同一时刻。保留旧版但明确区分，不只给工程首页或单独动画。当前VD44完整版本已获原创作者风格认可；新片仍需独立检查。
