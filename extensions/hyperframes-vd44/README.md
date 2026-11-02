# 客户并列状态短动画 · VD44 风格验证

> 当前状态更新（2026-09-12）：原创作者已明确认可最后完整视频及HyperFrames/Remotion的做法，并要求作为后续默认。此前“风格待认可”记录为历史；本次不补写代理未执行的连续视听或人工同步。完整流程与顺序见总Skill的references/approved-workflow.md。


本目录是既有 ai-cut 的动画素材扩展，只产生一段 **1920×1080、30fps、201帧、6.7秒、无声** 的 HyperFrames 素材。主剪辑与原声仍由现有 ChatCut 工程管理。

接入位置：主时间轴第435帧开始、长度201帧，素材播放速度1.0。主口播已1.1倍，不能再次加速此素材。

内容：先以日历表现跟进天数，随后在相对51/97/149帧分别展示「没有回复」「已经购买」「没有兴趣」。三种状态独立，没有从A到B到C的流程箭头。客户A/B/C、日历天数、图标均为教学示意，不能当成真实客户或系统截图。

风格参考为用户的 VD44.mov：粗体奶油黄/亮黄、黑色偏移阴影、短词放大入场、有对象及动作的界面卡片。原创作者已认可该风格；本目录的技术检查仍不代表全片验收。

## 运行

已有本机环境可执行 `powershell -ExecutionPolicy Bypass -File .\run.ps1 -Action Check`，`-Action Snapshot` 生成审阅截图，`-Action Render` 渲染无声MP4。用户已明确授权本次重剪与渲染；后续改变素材或发布范围，遵循总Skill。

要求 Node>=22、FFmpeg、Chrome。包装脚本默认使用本机隔离Node24，避免系统Node20。CLI固定0.8.35，GSAP本地3.14.2，字体固定本地Noto Sans SC，运行中不请求在线字体。

Render默认输出带时间的新文件；可用OutputPath指定一个尚不存在的文件，拒绝覆盖旧动画。下列固定文件名是本次已完成的历史渲染证据，不是以后自动覆盖的目标。

新的机器先复制或从下列来源获取 `assets/NotoSansSC.ttf`；不要提交字体二进制、媒体、缓存和node_modules。目录只安装了所需官方HyperFrames项目Skill（`.agents/skills`），没有覆盖个人总Skill。官方init会全局更新Skill，所以此范围任务使用官方CI开关跳过全局刷新，再用官方skills安装器按名字安装到本子目录。

## 2026-09-12 实际验证

HyperFrames 0.8.35 已在 Windows / Node24 / RTX3090 上真实渲染成功。MP4是201帧、6.7秒、H.264、无音频，共1,181,667 bytes。SHA-256为 `<EXAMPLE_SHA256>`。

最终严格check通过：17个布局样点、135个动画样点、69项文字对比度，0错误、0警告。卡片移位时有3条单帧遮挡info，实际编码帧已检查，属于卡片入场让位时的短暂重叠，重点词在停留阶段完整可读。前两轮失败日志保留：修正了断言选择器，以及日历淡出时的文字对比度；没有屏蔽全场审查。

FFprobe确认尺寸/帧数/声轨；FFmpeg `-xerror`完整解码退出0。读取全部201个编码帧做空白检测，无纯色空帧候选。已实际查看14张编码后关键帧联系表；原创作者风格已认可；代理连续播放观看及完整ChatCut成片验收仍未验证。无音轨是设计要求，因此没有把未试听写成试听通过。

## 编辑和来源

- `compositions/yt-comment-card.html`：实际动画源码，保留单一暂停GSAP时间轴；注册名称与主入口一致。
- `index.html`：固定201帧主合成。
- `index.motion.json`：检查真实浏览器中状态进入先后、可见时间、边界和动画活跃度。
- `shot-plan.json`：语义、逐帧时序和画面安排。
- `upstream/`：官方组件原件与HyperFrames Apache2许可证。
- `source-manifest.json`：来源、版本、哈希及许可链接。
- `evidence/`：实际检查、探测和完整解码记录（本地忽略）。

复用官方 `yt-comment-card` 的卡片/头像构建和显现方式，以及 `spring-pop` 的0.9起始缩放、有限过冲与独立透明度缓动。将社交评论重构为教学示意，不保留原示例用户和评论。所有文字仍可在HTML修改后重渲染；导入ChatCut后它是一段独立动画视频，内部小卡片不会自动变成ChatCut原生可编辑元素。

许可证来源：HyperFrames https://github.com/heygen-com/hyperframes （Apache-2.0），GSAP https://gsap.com/standard-license/ ，Noto Sans SC https://github.com/google/fonts/tree/main/ofl/notosanssc （SIL OFL）。
