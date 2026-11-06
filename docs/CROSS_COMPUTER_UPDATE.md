# 换电脑更新：规则、素材与同一个在线工程

GitHub同步本仓库代码、Skill与技术说明；OneDrive同步Project Hub资料和私人媒体；ChatCut保存在线主时间轴。三者分别核对，`git pull`不等于视频、依赖、账号或Skill安装已经同步。

2026-11-06新增独立发布技能 `video-publish`：安全更新源码后，按[安装说明](INSTALL_SKILLS.md#剪辑后的归档与发布video-publish)执行 `scripts/install_skill.py --skill video-publish`。自己的 Drive、账号、首评等从公开仓库外的 `owner-profile.json` 读取，或由 `VIDEO_PUBLISH_PROFILE` 指定；配置与登录分别准备。`ai-cut` 仅接到该入口，不因换电脑或安装而开始上传／发布。当前仓库公开可读；下方有日期的 private 验证要求仅属于旧记录。

## 三个位置先分清（2026-10-31）

| 位置 | 当前职责 |
|---|---|
| C:\Codex Workspace\ai-cut | Active Repo、总Skill源码、唯一技术KB、运行环境、工作工程与缓存；继续用private GitHub同步源码 |
| C:\Users\User\OneDrive\Documents\Codex Workspace\Project-AI Cut | 旧工作Hub；原片、素材、固定片尾、品牌资料、发布TXT及旧工程入口保留原位 |
| C:\Users\User\OneDrive\Documents\Codex Workspace\AI 短视频创作\02_AI 视频作品库 | 统一正式交付入口；每片非空参考图、AI 成片，以及项目根已有字幕 |

先读新Hub的AGENTS.md、素材索引.md和04_整理记录/2026-10-31_统一AI视频作品库/项目映射.json，再以统一ID找到旧工程。旧AIVD11对应AIVD-027，旧5-01～5-08对应015～022；旧6无映射，不按同号创建。005、006预留不建空目录，028只是2026-10-31当日下一号，运行时仍查实际目录、索引和映射。详见[KB34](../03_Documentation/Knowledge_Base/34_Unified_Video_Library.md)。不要把旧工作Hub配置直接改成作品库根，否则会让Logo、片尾和原片定位失效。

## 更新前后顺序

1. 在本机`C:\Codex Workspace\ai-cut`核对repo；如果使用了其他本机路径，先核对remote再采用实际位置。不要在OneDrive旧副本开发，不覆盖本地修改或迁入缓存。
2. 确认`origin`是`Isaac3113/ai-cut`且仓库仍为PRIVATE。用GitHub账户的当前权限核对可见性，不根据旧文档就宣称已验证；不要求用户贴密码或token。
3. 查看当前分支、`git status --short`和diff。存在本地工作、不同分支或分叉时先说明并保留，比较后处理；不自动`reset --hard`、`clean`、强制checkout、删除或覆盖。
4. 仅在正确仓库、main干净、提交关系允许快进时执行`git fetch origin`、`git pull --ff-only origin main`。核对本地HEAD与`origin/main`；快进失败时保留现场，不能用强制同步掩盖冲突。
5. 阅读`AGENTS.md`、`README.md`、KB入口、KB34、总Skill、`references/intro-outro.md`及新Hub当前索引／映射和任务相关规则。安装前查看个人Skill的`installation.json`和本地改动，按`docs/INSTALL_SKILLS.md`保留并协调已有安装；运行现有`scripts/install_skill.py`更新Skill。没有Python运行环境时先核对现有依赖，再按README恢复必要环境，不复制另一台电脑的`.venv`、模型、`node_modules`或缓存。
6. 运行本机doctor并如实区分缺失工具。只有规则修改时不无故安装ASR模型、商业工具或另一套引擎。
7. 从本机OneDrive中定位Project Hub的`公共素材/固定片尾/结尾模板.mp4`，确保不是未下载占位符；核对KB28记录的源文件SHA256、尺寸、音轨与时长。不要假定用户目录仍为`C:\Users\User`，也不要要求另一台电脑在相同`Videos`路径放一份。
8. 继续本片前先按统一库映射读取当前任务交接信息和旧工作Hub该片资料，确认ChatCut当前账号、projectId、活动timelineId及浏览器实际选择。打开既有工程并读取最新状态，不重复创建，不把本地旧快照覆盖在线较新的修订。凭证/带临时授权参数的URL不写入Git。
9. 视频导出能力和剩余额度必须当场核对。导出受限时只报告规则/工程的实际完成状态，不虚构已生成视频，也不默默切换本机最终渲染路线。只有真实输出通过检查后才更新映射作品的正式作品库；旧05_成片/最新版只作历史入口，不再默认接收新交付。复制记录源／目标、字节数与SHA256，同名异哈希先停止该文件，不盲目覆盖。

## 本次要记住的包装规则

- 片内封面0.1秒：30fps为3帧，无淡入淡出；独立封面仍为16:9与9:16两张。正式视频放映射作品的AI 成片，封面和采用图片放参考图，已有字幕放作品根；有文件才建目录，不为归档补字幕。Facebook文案、小红书文案与固定第一评论三份TXT继续留原工作入口并在聊天中展示，不进入作品库。
- 固定片尾使用用户提供的原始`结尾模板.mp4`；当前工程默认以原件1.2倍一次播放。用户没有指定这个精确数字，后续明确要求可覆盖。
- 只改变片尾速度，正文不再乘速；正文BGM不随片尾加速。片尾原音轨保留且不重复，正文BGM结束后再由片尾自身声音承接。
- 适配已确认画幅，不裁核心Logo文字；片尾不叠第二个水印、不强加口播圆窗/基础字幕。
- 缩短片头后同步移动正文画面、原声、字幕、圆窗、MG和SFX；跨片头的连续BGM可保留0帧起点并按正文新终点裁定，贴正文起点的BGM随正文平移。重新从同一个主时间轴导出字幕。保护已修复的完整讲话范围，不能又按词切得过紧。

以下提示词可交给另一台电脑的Codex。执行时使用当前GitHub主线和实时工程状态，不把文字里的要求当作已经完成的验证。

```text
请更新这台电脑的 ai-cut 项目，并按最新规则继续工作。

先在 C:\Codex Workspace\ai-cut 核对实际repo、origin、当前分支和git status/diff。origin应为Isaac3113/ai-cut，并核对PRIVATE可见性。若实际repo在别的非OneDrive本机路径，核对remote后使用该路径。保留本地未提交工作、未推送提交和个人Skill修改；不要reset --hard、clean、强制覆盖或删除。

正确仓库在main、工作区干净且允许快进时，git fetch origin，再git pull --ff-only origin main，核对HEAD==origin/main；遇到本地修改或分叉先比较和说明，不强制同步。

读取AGENTS.md、README.md、03_Documentation/Knowledge_Base/00_Start_Here.md、03_Documentation/Knowledge_Base/31_Template_Center_And_Editing_Routes.md、03_Documentation/Knowledge_Base/28_Intro_Outro_And_Cross_Computer.md、03_Documentation/Knowledge_Base/34_Unified_Video_Library.md、skill/ai-cut/SKILL.md、skill/ai-cut/references/intro-outro.md和docs/CROSS_COMPUTER_UPDATE.md。保护并核对个人Skill installation.json归属及改动后，用本仓库scripts/install_skill.py更新安装，运行doctor，分别报告规则和运行环境结果。

先从本机OneDrive定位AI 短视频创作Hub，读AGENTS.md、素材索引.md及04_整理记录/2026-10-31_统一AI视频作品库/项目映射.json。作品采用全库唯一的AIVD-三位编号 - 主要制作来源 - 简短标题；同片重剪或换工具不换ID，旧AIVD11查为027，旧5-01～08查为015～022，旧6无映射不能按006创建。005/006预留；028只是2026-10-31当日快照，新片仍核对实际目录、索引与映射。

当前规则：片头封面只闪0.1秒，30fps为3帧，无淡入淡出；以后结尾用用户提供的原始“结尾模板.mp4”。当前实施参数是原始片尾直接1.2倍一次，只加快片尾；正文速度不变，BGM不整体加速。保留片尾自己的音轨，只播放一次；正文BGM在正文结束处收尾。适配本条已确认比例，不裁关键Logo文字，片尾不重复叠Logo水印或强加真人圆窗、口播字幕。独立封面仍须16:9和9:16两张；新成片进入统一作品库的映射作品/AI 成片，封面与采用图片放参考图，已有字幕直接放作品根；只建非空目录，不为归档新生成字幕。发布素材三份TXT留旧工作入口并在聊天展示，不进入作品库。检查资料、ZIP、可编辑工程与缓存留本机工作区，原片与固定素材仍从原工作Hub找。先验新导出再按同片最新版规则替换，不批量清理旧归档文件。

正式视频的原片、完整成片和固定片尾不在Git中；2026-10-27本次授权的精简模板Demo位于docs/template-gallery/demos并随私人Git同步。请从本机OneDrive的口播Project Hub/公共素材/固定片尾/结尾模板.mp4取得完整原件，核对KB28的SHA256；不能把旧电脑Videos路径当唯一入口。代码、运行时和缓存留在C盘非OneDrive repo。

默认继续ChatCut同一个项目与唯一有效时间轴。先从当前任务交接或Hub资料核对projectId/timelineId，再读取在线最新状态；不要重复创建，也不要用旧快照覆盖新工程。缩短片头时同步平移正文画面、原声、字幕、MG、圆窗和SFX；跨片头的连续BGM可保留0帧起点并按正文新终点裁定，贴正文起点的BGM随正文平移。保护完整字音，重新导出字幕；已完成的位移不能重复执行。当前账号、工具、导出额度当场核对；工程修改、MP4真实导出、完整观看/试听和另一电脑恢复验证分开报告。没有真实导出就不要说视频已经完成，不静默改用其他主路线。

同时阅读templates/README.zh-CN.md、来源说明及references/editing-routes.md和template-selection.md（references位于skill/ai-cut下）。模板中心分为72官网条目、70控件/210变体、55代码注册项、19真人效果，不能称216套完整视频模板。先选剪辑路线再选模板；知识口播与旅行Vlog不同，Vlog专用自动流程尚未实现。个人.motion与Key不入Git，需要本机自己的授权包及配置，不复制旧电脑运行内核。

更新完成后告诉我实际commit、Skill安装结果、模板中心是否能浏览、素材哈希和在线工程状态，以及仍需完成的项目。
```

## 中文模板中心与MotionGit（2026-10-27）

安全pull后，中文清单在`templates/README.zh-CN.md`，精选演示小样位于`docs/template-gallery/demos`并随本次私人仓库同步。运行`python scripts/serve_template_gallery.py`可在本机看可搜索目录；GitHub本身不执行HTML。目录与Demo可看，不等于这台电脑已能重渲或剪好新片。

MotionGit使用自己的原始个人.motion，切勿把原包或Key发到GitHub。将`motiongit.example.json`复制为被忽略的`motiongit.local.json`并填写本机原包路径与标准Node22+路径（需npm时使用含npm的安装），再由`scripts/motiongit_adapter.py start --summary`验签；未知helper先核官方元数据，不跳过SHA检查。按实际包公开guide/schema检查依赖与输入；不复制旧电脑保护内核、.venv或node_modules代替安装。旅行Vlog专用自动流程尚未实现，不能由目录出现旅行类素材就推断已支持。


## 官方模板按新片接入与监测

每条新片同时考虑已接入和未接入官方候选；适合、免费可取得且许可允许时可直接核验/实测/接入，并把已验证精选本人Demo及调用记录同步现有私人库。读取template-lifecycle规则与docs/MOTIONGIT_UPDATES.md，不把完整原片、个人包或Key带入Git。更新通知不自动替换已认可素材。定时监测和本机基线不随git pull自动迁移，换电脑先核对已有监测任务及运行机器，避免重复创建。
