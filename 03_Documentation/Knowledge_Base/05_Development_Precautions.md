# Precautions
Preserve source files and revisions. Do not commit credentials, media, caches or private job metadata. Preserve third-party licenses. Tests do not certify listening, user consent or video quality.

## 2026-10-28：ChatCut重剪后的源映射与分离原声

以下来自本次用户指令、实际API回执与本机信号／画面检查；案例计数不是通用默认值。完整质量规则仍见[quality.md](../../skill/talking-head-editor/references/quality.md)，主编辑合同见[chatcut.md](../../skill/talking-head-editor/references/chatcut.md)。

- 源画面内嵌人物与独立PIP是两层内容；移除人物要同时检查V1和已烘焙辅助视频。局部素色补片无法恢复被窗遮住的原UI，不用整体右裁破坏功能区或已有PII坐标；保留圆窗时须同源同期。
- Script clean本次29处约16.3源秒＝13.6输出秒；ASR不能证明等待区间无空白。双VAD＋RMS补44区间、530输出帧，按源时钟保留100ms保护余量。信号检查不能代替句尾与接缝试听。
- V1切分不会自动同步旧detached A1／辅助素材。原135个mosaic被切分复制为802项后，需按实际保留源区间重新投射；当前82片结构对应362效果分片，不代表362个独立电话。源坐标、效果变换顺序、片段时钟分别核对。
- 本次fromItemId克隆detached audio实测assetId／尺寸错误；按官方detach_audio逐一分离新增72个V1项再移A1，保留并更新原10段A1，得到82段同源原声。不要为绕过单次错误修改adapter、猜私有字段或把本次观察泛化为所有版本。
- 原声相对原片1.2倍只执行一次；aux不带音轨，不替代主时间轴。此片封面3帧、片尾80帧；最新read_project实读在线工程1920×1080、5802帧／30fps＝193.4秒。抽帧QA已通过、未连续视听；本地变速音轨限制，2026-10-28在所需素材全部同步后实际重测云端导出，免费额度不足；无renderId／新MP4，已停止、不付费、不重试。工程保存、局部抽检、全解码、连续视听和实际交付分别登记。

## 2026-10-28：跨clip字幕修复与透明层验证（进行中）

- 当前原生字幕为111张Card。实测7组待合并卡分属不同clip（时间轴媒体片段）；首个修复batch返回Cannot merge Cards that come from different clips，applied为0，该失败批次没有提交字幕修改。相邻、同一素材或同一sourceToken不代表同一clip；不能把本机帧范围合法模拟当成原生接口已接受。此前依赖跨clip合并的修复候选已撤回。
- 当前原生111卡备份保留、显示已停用。现有set_card_tokens只能在Card既有范围内调整；不能靠改单词、源ASR、legacy字段或私有接口补出Card外时窗。原生显示停用不等于原生修复完成。
- 此前112时段VP8字幕辅助素材已准备并导入，但实际浏览器合成的2个样本出现黑矩形；该失败视频时间轴项现已移除，素材备份保留。生成、导入、编码／alpha标记及本机解码不能替代真实浏览器叠加检查。
- 最新112张PNG已全部按原时序接入“修正版逐句透明字幕”轨；原生字幕备份仍停用。主线程及独立代理实际看过13帧合成联络图：第4000／4524帧黑底消失，所查样本未见双字幕或重复PIP；第0帧封面、第5719帧正文及第5722／5801帧干净片尾已抽检。此为13帧抽检，不代表全片逐帧、连续视听或最终文件验收。图片字幕以后改字须重生成对应PNG。
- 当前工程5802帧／30fps＝193.4秒。本地retimed_audio实际渲染失败；全部所需素材同步后，2026-10-28实际调用submit_export返回“Could not submit export render job: Free export quota is insufficient”，未取得renderId，新的最终MP4未生成。当前已明确为本轮实际重测的免费导出额度阻塞，已停止，不付费、不重试；不再记为仍在上传。112张PNG接入及13帧抽检通过、原生字幕备份停用的状态不变，未完成连续视听。上述终态与QA来自主线程回报，本次知识更新未操作ChatCut或再次看过媒体。
