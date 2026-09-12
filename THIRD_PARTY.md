# 项目许可与第三方来源

本项目自行编写的总Skill、Python编排/检查程序及原创动画场景使用根目录MIT许可。该许可不重新授权依赖、原片、参考视频、肖像、图库、音乐、字体、品牌或账号服务。公开仓库不附带讲师视频/头像、私人项目历史、模型、二进制引擎、node_modules或授权凭证。

| 组件 | 来源与许可边界 | 本仓库如何处理 |
|---|---|---|
| Remotion 4.0.523 | https://www.remotion.dev/license ，有独立使用条件 | 保留原创React场景与依赖锁；引擎由使用者安装，不将其重新标为MIT；公司商业使用自行核实资格 |
| Remotion起始模板 | https://github.com/remotion-dev/template-empty ，原始提交见扩展manifest | 保留来源说明；未使用的空Composition不进入公开版；第三方模板内容不由本MIT重新授权 |
| HyperFrames 0.8.35 | https://github.com/heygen-com/hyperframes ，Apache-2.0 | 随附upstream/中的两份参考组件、完整Apache许可；改写组件保留来源与修改说明；引擎独立安装 |
| GSAP 3.14.2 | https://gsap.com/community/standard-license/ | 公开发行不分发gsap.min.js；使用者从固定官方发布下载，保留版权；该标准许可不是MIT |
| Noto Sans SC | https://github.com/google/fonts/tree/main/ofl/notosanssc ，SIL OFL1.1 | 随附许可文本；运行时下载字体，不附讲师机器字体 |
| FunASR与模型 | https://github.com/modelscope/FunASR | 代码与Paraformer/FSMN/标点模型许可分别核实；模型不入Git |
| PyTorch / Torchaudio | https://pytorch.org/ | 本机可选ASR依赖，不分发模型或CUDA二进制 |
| FFmpeg / FFprobe | https://ffmpeg.org/legal.html | 不分发二进制；使用者所装构建的GPL/LGPL及编译选项分别判断 |
| Pillow / NumPy | 各官方项目与安装包LICENSE | Python依赖，保留固定兼容版本记录 |
| ChatCut | 官方Codex插件与产品服务 | 仓库只有调用流程和原创MG；官方插件、账号、云服务额度另行取得；不转授账号 |
| Remotion/video-use官方Skill | extensions/upstream-lock.json 中的仓库/提交 | 本仓库仅含自己的适配入口与固定来源记录；完整官方规则由安装流程取得并保留原许可 |
| 剪映适配参考 | extensions/jianying-source-lock.json、jianying-core-lock.json | 可选路线；不承诺任意客户端版本兼容，不转授产品许可 |
| Pexels等素材 | https://www.pexels.com/license/ | 逐项记录来源和用途；普通图库不冒充真实客户/产品 |

2026-09-12核对了Remotion官方许可、HyperFrames仓库许可及GSAP标准许可。后续依赖更新或商业用途改变时重新核实。讲师案例的风格认可不是学员的商业许可。

案例音乐Digital Lemonade由Kevin MacLeod制作，按CC BY4.0使用，公开代码不分发该音轨。使用者如采用该曲，需依来源记录署名、说明修改与许可；也可换成自己有权使用且实际试听合适的曲目。来源：https://incompetech.com/music/royalty-free/index.html?Search=Search&isrc=USUAN1700010 。
