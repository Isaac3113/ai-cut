# AI Cut project instructions

> 2026-11-02：品牌与仓库改名为 AI Cut / Isaac3113/ai-cut；源码 C:\Codex Workspace\ai-cut，资料 Hub 为 Project-AI Cut，总 Skill 为 ai-cut。先读 docs/AI_CUT_RENAME.md。旧包名、schema、manager 和冻结ID仅保留为兼容合同，不作为当前项目入口。

# Project instructions

Read README.md, the master Skill and 03_Documentation/Knowledge_Base/00_Start_Here.md. Continue the existing Python runtime and animation extensions; do not rebuild the architecture.

- Preserve a single authoritative editing timeline, source files, semantic meaning, revisions and independently adjustable voice/music/SFX.
- The approved teaching preset is reusable, but another user's footage, credentials, permissions, likeness and validation are not inherited.
- Never commit original footage, full deliveries, source portraits/masks, accounts, personal .motion packages, .env files, models, node_modules or local job history. Preserve dependency licenses. The owner explicitly requested curated template demos on 2026-10-27: reviewed small demo MP4s and posters are allowed only under docs/template-gallery/demos, with source/rights and validation records. The owner extended this on 2026-10-27 to reviewed short owner-demo excerpts and integration instructions from future videos; this historical private-archive permission does not authorize full source/delivery uploads, sensitive client data or credentials. The current public-release scope below governs publication.
- Only report checks actually run; code tests and user style feedback do not prove continuous viewing/listening or new-machine success.
- Run relevant regression tests for behavior changes. Preserve user files except for explicitly authorized cleanup; validate new exports before replacing superseded deliveries.
- Update the project knowledge base for changes and teaching workflows. Use normal Git commits without rewriting existing histories.

- Keep editing and validation records in local work. From 2026-10-31, this owner's formal delivery is the unified AI video library, not the old 05_成片/最新版. Inside each mapped work, create 参考图 and AI 成片 only when files exist; existing SRT or other subtitle files stay at the work root. Do not generate subtitles or empty categories merely for archiving. Facebook/Xiaohongshu copy and the fixed first comment remain at the existing working-materials entry and in chat, outside the library. Validate a replacement before updating the same work; preserve original footage, assets, recovery dependencies and the active editing project. See final-delivery.md, project-storage.md and KB34. Follow the current repository visibility and public-release scope below.
- For the owner’s current cover and ending, read skill/ai-cut/references/intro-outro.md: 0.1-second cover and the supplied fixed outro; use docs/CROSS_COMPUTER_UPDATE.md for safe rule/media handoff.

## 剪辑交付与独立发布Skill衔接（2026-11-06）

- `ai-cut`负责剪辑、两比例封面及成品审核；Facebook文案必须调用当前可用的`fb-content`，按ADDA新写AD并保持所选固定DA原文，依据本版字幕和必要画面，不按标题编事实。视频仍用本条已确认比例，不因发布强制改9:16；封面为16:9、9:16各一张，旧五项／三封面包仅作历史或另有明确要求时使用。
- 只有用户要求Google Drive归档、Marketing OS入库或发布时，才接到独立[video-publish](skill/video-publish/SKILL.md)及[发布SOP](skill/video-publish/references/sop.md)。先核对本版路径／哈希、认可范围和本条授权；具体Drive根、账号、负责人、时区和当前三链接首评读取仓库外Project Hub的`发布流程/owner-profile.json`，不把私人ID或配置拷入公开仓库。其他使用者配置自己的目标，不继承本人的账号权限。
- 已认可正文不在发布时顺手改写。FB／IG共用与TikTok独立短稿按本条实际内容和平台限制分别判断；hashtag与平台限制冲突先说明并确认，不偷偷删标签或挪入首评。首评只用个人配置当前system、solutions、testimonials三项原文，不回退旧链接，不夹带音乐／许可／来源说明；制作与许可记录仍保留工作区。
- 成品认可、草稿保存和发布授权分别记录；本条已有明确发布账号、内容与时机的授权直接沿用，最新“立即发布”覆盖旧排程。提交超时、返回未知或pending时先逐账号核查现有任务／帖子和结果，不报成功、不把五账号全部重发；实际保存、提交、发布与首评成功分别核对。

## 本人视觉叙事与封面变化（2026-11-06）

- 最新认可：用户已明确认可 AIVD-034 第二版的完整知识流程讲解及16:9、9:16封面，作为以后同类口播的质量标准。新会话制作前必读 [user-preferences.md](skill/ai-cut/references/user-preferences.md) 和 [visual-storytelling.md](skill/ai-cut/references/visual-storytelling.md)，不能回退到首版贴纸堆叠或旧3～5秒变化要求。本次只记录认可，不再修改该成片或封面；认可不等于社媒发布授权，也不补写未做的连续视听QA。
- 正文按最终输出时间逐秒设计与检查：每个1秒区间都要有可辨认、与当前内容相关的实际动画进展。连续流线、对象传递、条件分支、状态与重点推进可跨多秒；静态图停留、嘴动、普通字幕换字、淡水印或无关装饰不能单独达标。不要求每秒切镜、换模板或响音效。0.1秒片内封面和固定片尾保持既有合同；实操约3秒只作重点动作锚点，不能替代逐秒动效覆盖。
- 讲到Facebook、IG／Instagram等平台时，有可用的正确真实icon就随对应原话显示，并融入对象／流程和标签。先核对平台身份、素材来源和可用范围；缺素材如实记录，不画错商标、不以泛用方框冒充。详见[平台图标](skill/ai-cut/references/visual-storytelling.md#平台图标随讲解出现)。此要求用于以后制作，本次获认可版本不补加。
- 用户纠正：知识讲解必须形成完整、可跟随的画面流程，不能以大量贴纸堆叠代替机制说明。“每一帧／每秒都有特效”指正文各段持续用画面表达当前原话中的对象、动作、关系和状态演进，不是每秒强切、不断弹跳或无意义炫技；固定片尾仍按既有规则保留。
- 完整制作先按剪后原话建立视觉叙事，再逐段选官方与自有模板：同一对象跨步骤保持身份，条件与结果一起表达，顺序、分支和并列关系不能混淆。漂浮贴纸、字幕换字和微缩放可作辅助，不能单独作为已完成流程的证据。执行与检查见 [visual-storytelling.md](skill/ai-cut/references/visual-storytelling.md)。
- 用户要求整条重做时，重审全片结构、模板覆盖和各段合成，不仅补几处动画；已确认的原声、语义、比例、速度及同源同步规则继续生效。模板选择充分比较当前官方和自有库，但不为凑模板数量虚构步骤或强塞不适合的效果。
- 如上版只有局部套用官方模板，准确说明对应区间、机制、来源版本与自制部分；不得把少数官方片段、已登记Demo或浮动装饰包装成整片已采用官方流程模板。技术QA、连续视听与用户风格认可仍分别记录。
- 每条封面保持品牌辨识度，同时重新设计hook、构图、字形层级、真实人物帧／姿态与画面组织；与最近封面对照，不能只换标题、颜色或把同一头像挪一点。人物姿态只能从真实原片选择，不生成新动作或替代脸。16:9与9:16分别排版并展示，详见 [cover-prompt-worker.md](skill/ai-cut/references/cover-prompt-worker.md)及[user-preferences.md](skill/ai-cut/references/user-preferences.md)。

- Read the owner’s shared storage rules before moving a project. OneDrive is a documentation/media Hub, not an active source or runtime location. Keep the authoritative technical KB in the local Git repo and link it from PROJECT_STRUCTURE.md. Preserve other-computer checkpoints before removing legacy copies.

## Owner storage and identity (2026-10-31)

- Active code, Skill source, technical KB, runtimes and work/cache remain in C:\Codex Workspace\ai-cut. The old Hub at C:\Users\User\OneDrive\Documents\Codex Workspace\Project-AI Cut remains the source/working-materials and project-entry location. The formal delivery root is C:\Users\User\OneDrive\Documents\Codex Workspace\AI 短视频创作\02_AI 视频作品库; resolve this owner's actual OneDrive path on another computer rather than moving code there.
- Before delivery or assigning a number, read the AI 短视频创作 Hub's AGENTS.md, 素材索引.md and 04_整理记录/2026-10-31_统一AI视频作品库/项目映射.json. All production sources share AIVD-NNN - 主要制作来源 - 简短标题. Codex-edited talking-head/screen footage uses Codex剪辑; later editing does not replace an existing primary generation-source label.
- Same work keeps its mapped identity across revisions and tools. AIVD-005/006 are reserved without empty directories. AIVD-028 is the next-ID snapshot on 2026-10-31, not a hardcoded allocator. Old AIVD11 maps to AIVD-027, old AIVD5-01…08 map to 015…022; old AIVD6 has no mapping and must not be recreated by matching a number. Preserve frozen IDs, old work paths and historic archive filenames.
- Copy only the selected verified delivery files; record source/target, byte sizes and SHA256 outside the media work folder. Same-name/different-hash conflicts stop that copy; identical copies may be reused after checking. Existing archived source files and prior migration records are not a new cleanup target. AIVD-023 has covers pending video validation and no successfully archived current film. This storage update changes no editing, audio, branding, tool or publishing-authorization preference.

## Repository visibility

On 2026-11-02 the owner explicitly requested making Isaac3113/ai-cut Public so everyone can browse, download and clone it without an invitation. This supersedes the 2026-09-13 private-only requirement for this repository. The GitHub settings page and anonymous REST readback verified public visibility; anonymous raw README access returned HTTP 200. Preserve original-code MIT notices and independent third-party/media rights. This authorizes the reviewed source, documentation and existing selected demos, not credentials, personal packages, full footage/deliveries, customer material or automatic publication of every future video. Verify later visibility changes rather than inferring live state from this dated record.


## Homepage and future public release

The owner authorized preparing the knowledge-talking-head project homepage, all effect previews, A/B comparison and Chinese onboarding on 2026-10-27. Preserve the knowledge/teaching scope and the four separate catalog layers. README showcase blocks are generated by scripts/build_homepage_showcase.py from catalog and provenance; do not hand-maintain a second inventory. Follow docs/RELEASE_PREPARATION.md for these standing presentation requirements. Use the owner's dated public-release authorization above; preparing other docs or previews does not itself authorize a different repository or website release.


## On-demand official template integration and update monitoring

2026-11-03 owner clarification: official catalog collection covers all public official templates across industries and categories, not only those suitable for Isaac, AGI TOP or knowledge talking-head editing. At each catalog refresh, reconcile every entry and preview in successfully enumerated official sources, preserve official category/industry labels and stable IDs, and include new categories. Unavailable, paid or unverified entries remain listed with actual status and official links; inclusion never requires an owner-video demo or successful integration. Learner-use categories are a secondary index, not an exclusion filter. Audit new source sections and complete pagination; report coverage gaps instead of claiming an old snapshot is current full-site inventory. Acquisition, redistribution rights, runtime QA and selection for one video remain separate. Weekly monitoring covers every public category and keeps its notification-only boundary. Follow the full-catalog section in template-lifecycle.md and docs/MOTIONGIT_UPDATES.md.

For each new video, consider both integrated templates and suitable official candidates not yet integrated. The owner authorizes free, permitted acquisition, verified official execution, actual input testing and local-library enrichment without a repeated per-template approval. Public Git uploads must also meet the authorized public-demo scope and independent rights/privacy checks; a successful render alone is not public consent. Read skill/ai-cut/references/template-lifecycle.md. Store stable-ID case/integration records in templates/template-integrations.json and regenerate both catalogs and homepage after real QA. Never mark all official templates executable from previews. The update monitor notifies only; it does not auto-upgrade approved projects or publish anything.


## Public gallery scope (2026-11-02)

The owner explicitly authorized publishing the existing curated template gallery and its current selected previews at https://aicut.agi-top.com for personal learning and free exchange, not business lead generation or sales. The website authorization supplemented the earlier private-Git-only archival permission; the subsequent explicit repository-publication request is recorded above. GitHub teaching should use direct public access rather than individual invitations once visibility is verified. Neither authorization includes full originals, full deliveries, personal .motion packages, credentials, caches, or sensitive client material. Preserve third-party sources, licenses, candidate/integrated distinctions, and historical rights/QA records; official previews do not mean original packages are included or all templates are executable. Deployment success and DNS/HTTPS verification must be reported from actual evidence, not inferred from this authorization.

## 中文定位、双入口与逐项说明（2026-11-03）

- 用户确认保留仓库网址 `Isaac3113/ai-cut`、本机目录和 Skill 调用名，首页名称与简介加入「AI知识口播自动剪辑特效模板」。不再为中文展示名重命名仓库、目录或域名。
- GitHub 首页分为「学习自动剪辑」和「选择、使用特效模板」两条路径。前者教环境、原片到成片的流程；后者按实际表达用途看 Demo、准备输入并使用效果。模板重渲不等于整片剪辑，也不附送讲师账号、原片或个人包。
- 首页开头保留「AI Cut 自制／适配真人特效」与「本人 Demo」的显著入口和既有精选预览，位于大篇幅官方目录之前；Notion 教学同步说明。分清自制／适配效果、本人套用官方模板的案例、官方与第三方目录，不将本人出镜当成模板原创证明，也不将效果分支称为已通用化的 `.motion` 包。复用现有登记与媒体，不另建第二套库存。
- 参考 `motiontemplates/all` 的图文说明顺序；它是现有上游来源之一，不是 AI Cut 全部功能的来源，也不意味着官网更新已全部接入。继续保留四层来源、稳定 ID、版本和验证范围，用用户能理解的用途分类作为主要入口。
- 所有模板及预告统一七项顺序：**效果预览 → 适用内容 → 所需素材 → 可改参数与限制 → 怎样使用 → 当前可用与验证状态 → 来源和许可**。逐项依据源码、参数合同或明确来源填写；未知字段写待核对，不从 Demo 推测能力。使用方法提供可复制的指令，长 QA 与维护命令折叠。
- GitHub、中文目录和 HTML 从同一登记资料生成；不得手工维护分叉的分类/数量/状态。改动展示或用法后检查 Notion 教学是否需要对应更新。原有媒体、ID、剪辑偏好、声音、速度和交付位置继续沿用。

## 自制效果沉淀为通用模板（2026-11-03）

当 Isaac 指定一段好效果并询问来源，先依据该片源码、时间轴和模板记录说明它属于现成模板、自行实现或混合方案，并给出来源、版本和实际改动。不能把第三方模板换字、换色或本人 Demo 称为原创。

用户已要求：指定效果若为自行实现，继续将其整理为自己和他人均可复用的 Motion Graphics 模板；按 [模板创作规则](skill/ai-cut/references/template-authoring.md)推进参数化、去个人化、独立内容验证、说明和目录登记，并核对当前官方规范制作 `.motion` 交付。遇到只具备 MP4、缺源码或其他实际阻碍时说明阶段，不能把旧成片改后缀冒充模板。修改现成模板时保留来源和许可，只对自制部分作相应原创声明。

本条授权覆盖该指定效果的可分享通用源码、文档及已确认可再分发的去个人化示例，完成验证后按常规 Git 流程公开，无需重复征求同一范围的泛化许可。它不授权公开完整原片/成片、客户资料、私人 `.motion` 包或凭据，也不授权付费生成或任意发布新视频。其他学员不继承 Isaac 的私人素材与长期授权。源码已整理、参数已验证、`.motion` 已验收、GitHub 已同步和网站已部署分别报告。
