# 项目入口、代码与每条视频的存放

执行存放或迁移前先读用户的共享规则及Project Hub内PROJECT_STRUCTURE.md。用户给OneDrive项目路径时，它是项目资料入口，不能推断为把源码、依赖或缓存也放进去。此前“所有内容同一个物理根”的本项目规则已纠正。

本用户2026-10-31起以[统一作品库交付](final-delivery.md#本用户精简交付入口)替代旧05路径与命名。仅改变媒体交付位置和作品标识，原声、速度、比例确认、字幕制作、品牌、音乐、片头片尾及最新版本替换偏好不变。已归档旧来源不再次搬移／删除，不把规则更新扩大为重剪或发布授权。

## 三个位置，一条权威时间轴

- `CODE_ROOT`：OneDrive之外、本次实际选定的Active Git Repo。按本Skill的`scripts/run.py`现有机制解析：先取`TALKING_HEAD_EDITOR_ROOT`，再取已安装Skill的`installation.json.source_root`，最后从该入口所在目录向上查找同时含`pyproject.toml`与`src/talking_head_editor`的源码根；找不到就明确报错。本用户当前电脑已核对的Active Repo为`C:\Codex Workspace\talking-head-editor`；`AI-Talking-Head-Editor`属于历史维护路径，不能据此覆盖当前安装。此处只记录本机现状，跨电脑仍按实际checkout及安装记录定位。源码、总Skill源码、技术知识库、动画源工程、.git、.venv、node_modules、模型、缓存和实际剪辑工作目录在所选根内；代码经private GitHub同步。
- `PROJECT_HUB`：本用户原OneDrive下`Projects-AI-Talking-Head-Editor`。原片、素材、参考、品牌公共素材、现有发布文案及旧工程入口继续原位保留；04只记录本机工程入口。旧05属于历史来源，停止作为新交付默认。不把新作品库配置误填为project_hub，否则旧目录助手会再拼一层“视频项目”。
- `DELIVERY_LIBRARY`：本用户正式媒体交付根为`C:\Users\User\OneDrive\Documents\Codex Workspace\AI 短视频创作\02_AI 视频作品库`。先读其父目录AGENTS.md、素材索引.md与`04_整理记录/2026-10-31_统一AI视频作品库/项目映射.json`。作品内仅非空`参考图`、`AI 成片`和根目录已有且匹配当前视频的字幕；不放源码、依赖、工程、日志、发布素材或说明目录，不为归档新增字幕。归档复制记录放外部04整理记录或本机work，工程入口由素材索引关联原Hub。
- 技术知识库只有CODE_ROOT/03_Documentation/Knowledge_Base一份正式维护位置；Hub记录链接，不另维护同步副本。可供分享的固定ZIP/阅读导出不属于第二份Active Repo。
- ChatCut仍只有官方时间轴一条执行依据；本机模式仍沿用既有job/revision，存储分开不建立两套剪辑清单。

```text
CODE_ROOT/
  src/ scripts/ skill/ extensions/ tests/
  .git/ .venv/ .runtime/
  03_Documentation/Knowledge_Base/
  work/videos/既有冻结目录或新统一作品名/04_剪辑工程/
    job或原有outputs/       实际工程、字幕、报告、检查证据、动画工作文件、抽帧、日志、缓存

PROJECT_HUB/
  PROJECT_STRUCTURE.md
  00_项目入口.md
  视频项目/原工作名或新统一作品名/
    00_视频说明.md
    01_原片/
    02_自有素材/
    03_参考视频/
    04_剪辑工程/本机剪辑工程.md   只写位置及恢复入口，不复制运行时
    05_成片/最新版/              仅既有历史来源；新建助手不再创建或默认交付
  学员分发/                    完整Skill ZIP与教学阅读件
  项目资料/                    需求原稿、存储说明与小型验收报告

DELIVERY_LIBRARY/
  AIVD-028 - Codex剪辑 - 简短标题/
    参考图/                    有封面／采用图片才建
    AI 成片/                   有已验证交付视频才建
    已有字幕.srt               已有且匹配当前版本才交付；本结构仅示意，不预建空目录
```

## 全平台统一编号与旧工程映射（2026-10-31）

项目名称为`AIVD-三位编号 - 主要制作来源 - 简短标题`。全部平台共用一套ID，来源不等于发布平台；真人口播／录屏由Codex剪辑时标`Codex剪辑`，即梦或Higgsfield生成后再剪辑仍保留主要生成来源，完整工具链和发布渠道另记。题目优先采用用户提供或已授权代理按内容确定的简短主题，未授权且缺少主题时才询问。

- 新作品分配前同时核对真实作品目录、素材索引正式作品表及映射。005、006预留且不建空目录；NextNewID=028只是本次登记下限，不是永久下一号。不回填缺号、不因换平台或工具新建编号；只读plan不占号，真正交付前再核对并登记索引，避免并发重号。
- 同片重剪、改字幕或重导出按完整旧名／原工程映射找既有统一ID，保留主要来源。原剪辑1～4对应011～014，5-01～5-08对应015～022，7～11对应023～027；原11为027。原母片5和旧6没有独立映射，不能凭裸数字造一个新作品或套用另一平台的同号；先核对真实作品关系。
- AIVD-023仅有待视频校验封面，没有成功归档的当前成片；AIVD-008仅有图片。目录存在、HasVideo或文件名“成片”均不等于本次内容验收通过，状态沿来源证据另记。
- 现有工作目录、ChatCut项目／时间轴、job/revision、冻结缓存ID与原文件名保持不动。映射后的新作品名称不用于全局替换内部证据。新建工作可使用已核对的统一作品名；恢复旧片从索引OriginalProject及原Hub04入口读实际work位置，不能用新名称找不到目录为理由新建空工程。

## 只读交付规划与本机配置

本机`runtime.local.json`保存独立键`delivery_library_root`、`delivery_registry`（项目映射JSON）、`delivery_asset_index`（素材索引）；`project_hub`仍是旧工作Hub，`video_work_root`仍在C盘。路径优先级为明确CLI参数→对应`TALKING_HEAD_DELIVERY_*`环境变量→本机配置。其他电脑先同步媒体／索引，按实际位置配置，不靠Git复制本机运行时或个人路径配置。

在CODE_ROOT执行；以下plan／audit均只读，不创建目录、不复制媒体、不更新索引：

```text
python scripts/delivery_library.py plan --title "简短标题" --source-label Codex剪辑 --stem-suffix 9比16_1.2倍
python scripts/delivery_library.py plan --existing "AIVD-027"
python scripts/delivery_library.py audit --existing "AIVD-027" --hash
```

plan的新片结果是候选编号和视频／两封面路径，不代表占号或已经导出。已有字幕只有显式提供真实已有文件时才规划根目录目标；审计不强制缺失字幕，也不替代解码、听审、字幕同步或OneDrive云同步。视频和已有字幕不再同目录，`delivery_names.py`的通用同目录三件套审计继续用于制作工作区，不能拿它要求作品库新增字幕。

既有work中一次性finalize／export脚本或回执里的旧05路径保留原制作证据，不作为本轮默认出口。继续同片时先运行当前planner得到映射后的交付路径，不直接重跑旧交付脚本，也不全局改写冻结缓存／历史回执中的路径。

## 实际创建与恢复

每条新口播先定位或规划统一ID；在原工作流程中生成并验证，再按final-delivery把选定视频、图片和已有匹配字幕复制到作品库。逐文件核对源／目标字节和SHA256；同名冲突先核对，不盲目覆盖。本次衔接不搬动已归档来源，不改原片或恢复资料。Windows非法字符不静默替换。

在CODE_ROOT执行：

```text
python scripts/create_video_folder.py --hub "PROJECT_HUB" --name "AIVD-028 - Codex剪辑 - 简短标题"
```

该助手只建立原工作Hub的01／02／03／04资料位置与CODE_ROOT本机工作目录，并在Hub04写实际入口；不创建05／06或作品库空目录。028是示例候选号，必须先读plan并复核索引。`--existing`仍可兼容带旧05／06的原工作结构且不覆盖，不能用它将旧work更名成映射后的统一ID。Hub查找顺序为明确`--hub`（兼容`--root`）→TALKING_HEAD_PROJECT_HUB→runtime.local.json.project_hub；缺配置明确报错，不将库根当工作Hub或回退到源码根。工作根为`--work-root`或runtime.local.json.video_work_root，默认CODE_ROOT/work/videos，禁止落入OneDrive。

原片与交付继续按final-delivery.md保存和核对哈希。需要跨电脑恢复时，提供不含运行时/缓存的工程导出及素材绑定；另一台电脑用自己的Git checkout与本机工作目录恢复，不靠OneDrive搬运.venv/node_modules。个人Codex Skill和官方插件仍由应用管理；安装记录绑定CODE_ROOT。

## 迁移与验收

共享规则优先：先核对branch/HEAD/remote/dirty/untracked/env存在性、备份未推送工作。其他电脑可能仍在使用旧OneDrive源码时，在逐台核对之前保留旧目录，标记LEGACY-CLEANUP-PENDING。原件尚未移走时可先建立非OneDrive副本、验证依赖与登录。

仅在迁移条件满足后移出旧源码/缓存；不批量删除，不用Git版本覆盖未知本机改动。保留旧新路径映射，历史日志不篡改；不要在OneDrive创建指回本机源码/缓存的目录junction来伪装已移出。

迁移后核对Git历史、已安装Skill哈希及source_root、实际模块路径、FFmpeg/模型可见性、真实job状态和代表片段、成片与字幕哈希。更新PROJECT_STRUCTURE.md、源码知识库与现有登记；确认private GitHub提交。文件数量减少是本机事实，OneDrive同步队列完成与网络速度改善须另外观察，不能由.gitignore或测试结果推断。

历史原AIVD 4现对应统一AIVD-014，冻结工作仍位于work/videos/001-20260919/04_剪辑工程。继续同片时读取原Hub的04_剪辑工程/本机剪辑工程.md定位已有工程，不对新展示名称强行运行create_video_folder --existing或新建空工程。


## 长录屏母项目与子切片（2026-09-21）

旧母片AIVD 5与5-01～5-08是历史工作别名，八支作品已统一为015～022；旧工程和母片不改名。2026-10-31起的新独立交付切片逐支从全平台作品编号分配统一ID，母片／切片关系记在外部索引或工作清单，不再开启另一套母号加子序号。只有内部母片工作任务时不创建无媒体的作品目录。

共用不可变母片和同源转写；母项目保存切片总索引，每支子片有自己的ChatCut主时间轴、源范围映射、字幕、统一作品库目录和验收状态。成片不嵌套在旧母项目“最新版”下；不要为每支片重复复制母片到作品库，也不通过目录助手为恢复旧切片创建空工程。

用户明确授权自行想主题/命名时，先理解原片，再拟忠于内容的正式主题，记录“用户授权代理命名”，不冒称用户逐字确认。未授权自行命名且缺正式主题时才按原规则询问。尚未分析内容时使用准备目录或临时候选号，不提前编造内容标题。
