# 32 · 首页效果展示、本机浏览与公开准备

日期：2026-10-27。用户授权先准备知识口播项目首页、全部效果和对比，不公开仓库、不部署网站。

## 三种入口

GitHub保存源码与README，根README是GitHub首页；docs/template-gallery/index.html是可运行浏览页；127.0.0.1:8768是当前电脑启动本地服务后的地址。别人复制这个URL会访问自己的电脑，须取得完整文件夹并运行自己的serve脚本。对外域名与网站托管是另一个阶段，仓库私有与网站访问权限分别确认。

浏览页已内嵌数据、样式和脚本，Demo/海报使用相对demos路径。scripts/serve_template_gallery.py只用Python标准库。独立副本在-I -S模式、禁用sitepackages且无项目运行环境安装的情况下，HTTP页面200、视频MIME及SHA匹配；测试发现并修复stdout中文UTF8输出。该验证不是另一电脑、直接双击文件或所有浏览器测试。

## 首页组织与重建

README保留两个机器区块：HOMEPAGE_COMPARISON为同源A/B节选；HOMEPAGE_SHOWCASE由scripts/build_homepage_showcase.py读取四份登记汇总与固定官网快照生成。全部216个条目按层级及中文分类折叠，本地效果提供真实动图节选和完整Demo链接；官网项使用来源已有HTTPS预览图并链接官方Demo，不把他人的预览当作本地适配完成。

各层分别为72官网集合、70控件/210变体、55代码注册项和19真人分支。官网当前全站数量会变化，本期展示按固定快照，不混称216套完整视频模板。A/B对比来自相同源区间44.8–48.8秒，静音节选保留速度；认可范围是官网局部重点文字，不是全库或整片。

## 教学与后续约定

中文新手页docs/GETTING_STARTED.zh-CN.md分别指导看Demo、重渲特效和剪整片。前者只需浏览文件和Python；后两者另需引擎、原片、品牌素材、模板包与账号。19真人效果仍有样片专用时间逻辑，换片需适配。首页统一当前所有者的两封面和三TXT精简交付；其他创作者按自己明确要求。

用户后续不用重新描述首页规格，现已固化在docs/RELEASE_PREPARATION.md和AGENTS.md。当前保持Private；后续明确发布才执行当次授权范围，不因准备就自动公开或部署。原创代码MIT，第三方代码/字体/媒体/个人包许可分别处理；本轮私人仓库小样授权不能提前扩成所有媒体可公开再分发。

## 来源身份

MotionGit[官网About](https://motiongit.com/about)自述创始团队背景来自硅谷、伦敦、香港和新加坡；模板作者[adunext公开GitHub](https://github.com/adunext)显示Michael Du及中文项目“阿杜的AI剪辑Skill”。公开资料没有给出国籍，不从名字、语言或办公背景推断国籍，也不把一个模板作者等同整个平台全部作者。

源码保存、图片显示、动图检查、Git远端同步及公开状态分别验证；具体本轮结果以实际工具回执为准。


## 本轮首页检查

145个本地原速动图节选共20,098,343 bytes，每个不超过512KiB，源视频及输出哈希全部匹配；制作代理完成全解码、时长和比例核对，实际抽看16个GIF的三个时点。另有同源A/B四秒对比动图，源及输出身份单独记录。72个官网图片HEAD均200且image类型，读取正文0 bytes。GitHub官方Markdown渲染保留218张图片（216条目＋附加预告＋A/B）、34折叠组和32表格；此项不等于逐张浏览器加载或连续观看。

## 2026-11-02 Notion 教学与私有学员领取

用户选择不购买 Notion 自定义域名，直接制作可复制教学并配 GitHub 链接；明确保留私人仓库，按学员 GitHub 账号逐个授权。本次不改变可见性、不发送邀请、不发布 Notion 页面、不部署网站或配置 DNS。

唯一学员简版位于 [docs/NOTION_GUIDE.zh-CN.md](../../docs/NOTION_GUIDE.zh-CN.md)，README 首屏及中文新手页直接引用。教程说明接受邀请、Windows Git/Python 环境、源码获取、安装、自己的 ChatCut、首支 20～30 秒试剪、比例与交付约定、模板边界、局部修改和安全更新；Isaac 个人品牌、固定片尾、速度、路径、编号、社媒设置都不是学员默认授权。

安装命令按当前脚本核对。新的手动安装示例显式传 `--target "$env:USERPROFILE\.agents\skills\talking-head-editor"`，参照 [OpenAI 当前 Skill 发现文档](https://learn.chatgpt.com/docs/build-skills)；已有安装先核对位置与归属，不改所有者当前 `.codex/skills` 安装，不创建同名重复项。未在另一电脑安装，不把脚本静态核对或本机 doctor 等同于学员环境与 ChatCut 已连接。

HTML 仍唯一维护在 `docs/template-gallery/index.html`。它是模板展厅，GitHub 是源码与获授权文件入口，Notion 是教学，Vercel 是可选网站托管，域名是网址。技术上可静态部署该目录，须包含采用的相对 `demos/` 视频与海报；官方 HTTPS 预览依赖外部网络。当前本机原声映射由 Python 服务读取 `gallery.local.json` 并提供本地路由，不能作为静态目录自动迁移；网站将回退已登记静音版本。

网页公开与仓库私有分别配置，网页公开不会授予私有仓库权限。对外发布需明确采用媒体与访问范围，现有私人本人 Demo 授权不自动扩大。完整模板包、私人 `.motion`、Key、原片与本机目录不因此公开。Vercel 自定义域名连接是后续任务，本次仅核对现有文件与官方说明，不宣称网站已上线。


## 2026-11-02 个人交流展厅正式上线

以上为各阶段历史记录。用户随后明确授权在Vercel配置和发布现有精选展厅，并确认用途是个人学习与免费交流、不用于业务获客或销售。正式入口为 https://aicut.agi-top.com ，Hobby免费版，未购买或升级套餐；源码仓库 https://github.com/Isaac3113/ai-cut 仍Private，按GitHub账号逐个授权。公开展厅和私人源码权限分别管理，不公开完整原片、私人.motion包、Key、运行缓存或客户资料。

现有项目为Isaac Chong's projects下的ai-cut。Root Directory为docs/template-gallery，Preset为Other，Build与Install Command为空，Output Directory为`.`，关闭包含根目录外文件。Namecheap CNAME由用户填写：aicut → a36ff3d4d2816e20.vercel-dns-017.com.；Vercel回读verified=true、misconfigured=false。域名配置通过与网页部署成功是两个独立检查。

本次生产部署dpl_7KNHHdXEmjJtuZAKA4PLUma8Cdp5为READY，来源提交3b34674974741c33bb6d170e78fefd151c8c855f。HTTPS首页200，线上HTML的SHA256与该提交Git blob逐字节相同；本机工作文件仅有CRLF/LF换行差异。312/312本地MP4、JPG仅做HEAD检查，状态与MIME正确，4条官网代表预览HEAD通过。浏览器确认本人横竖比例筛选与知识流程分类；代表性本人横版及官网流程动画已播放至结束，竖版样本确认时间推进，样本无视频错误；不把这些结果扩大为全部媒体的连续声画QA。HTTP详细回执留本机work/vercel-setup-20261102/media-http-validation.json，不进入公开作品目录。

线上沿用同一生成器、登记表、中文分类和精选静音预览。本机Python服务可按个人gallery.local.json提供原声路由，静态网站不自动读取该本机配置。官网候选、取得原包、已接入、Demo检查及新片验收继续分别标记；官网预览不表示官方原包附送或全部模板可执行。

GitHub主线连接及本次推送后的生产部署已验证。今后新增模板要先核对来源、许可、公开范围和QA，再重建同一HTML并push，最后核对具体部署及正式网址。MotionGit每周监测仍只通知变化，不自动下载、接入、改旧工程或发布网站；Git部署连接不能冒称整个模板发现到发布的自动流程已接通。

当前操作说明见[网站与域名教学](../../docs/VERCEL_AI_CUT.zh-CN.md)，面向领取者的教学见[Notion使用指南](../../docs/NOTION_GUIDE.zh-CN.md)。

## 2026-11-02 后续公开源码与直接下载教学

同日用户进一步明确要求将Isaac3113/ai-cut由Private改为Public，取消领取GitHub权限的步骤。此前私人仓库和逐个邀请的段落保留为阶段历史，以本段为当前访问状态。GitHub设置页已显示Public；无登录凭据的公开REST接口返回private=false、visibility=public、license=MIT，raw README匿名访问HTTP 200。公开浏览、ZIP下载和HTTPS clone不需要邀请或登录，写入仓库仍需相应权限。ZIP不含Git历史，长期更新优先clone。

当前README、中文新手页、Notion教学源文件、生成展厅页脚与规则入口均按公开分发更新。Notion原页40c0a6f4-5e60-8030-97b0-fc6a2990f0b6通过7处针对性内容更新，工具返回成功且无warning；保留图片、同步区块和其他原有内容，网页验收由当前执行线程单独核对。没有因开源改变剪辑风格、媒体身份、作品编号或收费工具权限。

原创代码与规则继续MIT；第三方代码、模板、肖像、品牌和媒体的权利独立。现有经审查的精选Demo属于此次公开范围，完整原片、完整成片、个人.motion包、Key、客户敏感资料与工作缓存保持排除。后续新片先在本机积累，只有已有明确公开授权且许可与隐私检查通过的小样才进入公开仓库；不把历史私人归档权限扩成所有未来视频公开授权。实际规则见[模板长期接入规则](../../skill/ai-cut/references/template-lifecycle.md)。

## 2026-11-03 模板用途与学员套用说明

用户要求让学员明确展厅中的模板用于后续剪辑效果选择。Notion 原教学第 6 节与 [GitHub 教学第七节](../../docs/NOTION_GUIDE.zh-CN.md#七模板是做什么的剪辑时怎样用)同步补充：流程、对比、数据、实操和重点字分别如何配合内容；可让 AI 按内容选择，也可指定模板名称／编号；使用学员自己的原片、文字、数据及获授权素材，经过精剪、适配、对齐、导出和检查。提供可复制的模板选型指令。

教学继续区分官方示例、本人 Demo 和已接入状态；不把看得到预览写成所有模板已能一键运行，不附送个人模板包或讲师素材。此项仅补充使用解释，不修改 Skill 选型行为、目录数量、动画实现或媒体文件。
