# 项目入口、代码与每条视频的存放

执行存放或迁移前先读用户的共享规则及Project Hub内PROJECT_STRUCTURE.md。用户给OneDrive项目路径时，它是项目资料入口，不能推断为把源码、依赖或缓存也放进去。此前“所有内容同一个物理根”的本项目规则已纠正。

## 两个根，一条权威时间轴

- `CODE_ROOT`：OneDrive之外、本次实际选定的Active Git Repo。按本Skill的`scripts/run.py`现有机制解析：先取`TALKING_HEAD_EDITOR_ROOT`，再取已安装Skill的`installation.json.source_root`，最后从该入口所在目录向上查找同时含`pyproject.toml`与`src/talking_head_editor`的源码根；找不到就明确报错。本用户当前电脑的`C:\Codex Workspace\AI-Talking-Head-Editor`仍是有效维护目录，仅记录本机现状，不是跨电脑写死默认，也不据此替换用户这次选择的checkout。源码、总Skill源码、技术知识库、动画源工程、.git、.venv、node_modules、模型、缓存和实际剪辑工作目录在所选根内；代码经private GitHub同步。
- `PROJECT_HUB`：用户指定的资料项目；本用户使用OneDrive下Projects-AI-Talking-Head-Editor。保存PROJECT_STRUCTURE.md、需求、教学阅读件、原片、素材、参考、封面、字幕、完整制作说明与完整交付。这里不保留Active Git Repo、展开的运行时或缓存。
- 技术知识库只有CODE_ROOT/03_Documentation/Knowledge_Base一份正式维护位置；Hub记录链接，不另维护同步副本。可供分享的固定ZIP/阅读导出不属于第二份Active Repo。
- ChatCut仍只有官方时间轴一条执行依据；本机模式仍沿用既有job/revision，存储分开不建立两套剪辑清单。

```text
CODE_ROOT/
  src/ scripts/ skill/ extensions/ tests/
  .git/ .venv/ .runtime/
  03_Documentation/Knowledge_Base/
  work/videos/AIVD 5 - 视频主题/04_剪辑工程/
    job或原有outputs/       实际工程、动画工作文件、抽帧、日志、缓存

PROJECT_HUB/
  PROJECT_STRUCTURE.md
  00_项目入口.md
  视频项目/AIVD 5 - 视频主题/
    00_视频说明.md
    01_原片/
    02_自有素材/
    03_参考视频/
    04_剪辑工程/本机剪辑工程.md   只写位置及恢复入口，不复制运行时
    05_成片/最新版/              本用户唯一交付入口：MP4、封面、TXT、SRT、说明与证据
    06_历史交付/                 旧版本内部归档，不与最新版并列交付
  学员分发/                    完整Skill ZIP与教学阅读件
  项目资料/                    需求原稿、存储说明与小型验收报告
```

## AIVD连续编号与正式主题（2026-09-21）

本用户所有新视频项目按 `AIVD {顺序数字} - {用户确认的主题}` 命名，编号与AIVD之间保留一个空格。创建前列出Hub现有视频目录，兼容识别AIVD3/AIVD 3以避免重号；同一条重剪、改音乐或加特效继续使用原编号。用户明确指定编号和标题时优先采用，检查是否与另一项目冲突；未提供编号时接续最大已用数字，不回填缺号。缺少正式主题且未授权代理自行命名时先询问主题，不把原片名001或拍摄日期当作正式项目名。2026-09-21用户指定本条为“AIVD 4 - 你是如何一个人做到两个 million 的业绩？”，现有最大编号4，下一条新视频接续5；此数字记录随新项目更新，不硬编码永远用5。

新建Hub资料目录与本机工作目录使用相同项目名，最新视频/字幕等交付文件以同一AIVD编号和主题为前缀，再保留比例、速度及_视频/_字幕类型后缀。原片文件名、冻结证据、ZIP内历史名称和已有内部缓存ID不为展示改名而全局替换；需改既有目录时同步活动入口、清单与路径并核验哈希。

以下AIVD 5只是当前下一条的示例，运行前仍核对实际编号。

## 实际创建与恢复

每条新口播单独建文件夹，保留用户给的中文主题和全角问号；同片重剪沿用文件夹。依照2026-09-13最新要求，先在工作区生成并验证，再把旧交付移入06历史归档、更新05最新版的固定入口；给用户只展示最新版。目录移动前核对源/目标绝对路径都在本条视频资料目录内，并保存映射；不批量删除原片或恢复资料。Windows非法字符不静默替换。

在CODE_ROOT执行：

```text
python scripts/create_video_folder.py --hub "PROJECT_HUB" --name "AIVD 5 - 视频主题"
```

它真实创建Hub资料目录及CODE_ROOT/work/videos内的工作目录，并在Hub的04文件夹写本机位置。`--existing`核对成对目录后复用，不覆盖。Hub查找顺序为明确`--hub`（兼容旧`--root`参数）→TALKING_HEAD_PROJECT_HUB→本机runtime.local.json.project_hub；没有配置就明确报错，不退回把资料放在源码根。工作根通过`--work-root`或runtime.local.json.video_work_root设置，默认CODE_ROOT/work/videos，禁止落入OneDrive。程序同时拒绝从OneDrive内的Active Repo启动该建目录流程。

原片与交付继续按final-delivery.md保存和核对哈希。需要跨电脑恢复时，提供不含运行时/缓存的工程导出及素材绑定；另一台电脑用自己的Git checkout与本机工作目录恢复，不靠OneDrive搬运.venv/node_modules。个人Codex Skill和官方插件仍由应用管理；安装记录绑定CODE_ROOT。

## 迁移与验收

共享规则优先：先核对branch/HEAD/remote/dirty/untracked/env存在性、备份未推送工作。其他电脑可能仍在使用旧OneDrive源码时，在逐台核对之前保留旧目录，标记LEGACY-CLEANUP-PENDING。原件尚未移走时可先建立非OneDrive副本、验证依赖与登录。

仅在迁移条件满足后移出旧源码/缓存；不批量删除，不用Git版本覆盖未知本机改动。保留旧新路径映射，历史日志不篡改；不要在OneDrive创建指回本机源码/缓存的目录junction来伪装已移出。

迁移后核对Git历史、已安装Skill哈希及source_root、实际模块路径、FFmpeg/模型可见性、真实job状态和代表片段、成片与字幕哈希。更新PROJECT_STRUCTURE.md、源码知识库与现有登记；确认private GitHub提交。文件数量减少是本机事实，OneDrive同步队列完成与网络速度改善须另外观察，不能由.gitignore或测试结果推断。

本次已有AIVD 4是名称校正例外：Hub已使用正式名，冻结工作仍位于work/videos/001-20260919/04_剪辑工程。继续同片时读取Hub的04_剪辑工程/本机剪辑工程.md定位已有工程，不对新展示名称强行运行create_video_folder --existing或新建空工程。此映射不改变后续新片资料/工作目录同名规则。


## 长录屏母项目与子切片（2026-09-21）

用户把一段长录屏指定为一个AIVD项目时，该母项目只占一个连续编号，子片用母编号加两位切片序号。例如母项目 `AIVD 5 - {母主题}`，子片 `AIVD 5-01 - {子主题}`、`AIVD 5-02 - {子主题}`，不占用下个独立母项目的AIVD 6。每个子片的修订沿用其编号。下一母项目编号仍应检查当前最大已用母编号，不把5-01误作501。

共用不可变母片和同源转写；母项目保存切片总索引，每支子片有自己的ChatCut主时间轴、源范围映射、字幕、交付目录和验收状态。可由已有目录助手创建母项目；子片放在母项目最新版下的独立子目录，不为每片重复复制母片或再占母编号。

用户明确授权自行想主题/命名时，先理解原片，再拟忠于内容的正式主题，记录“用户授权代理命名”，不冒称用户逐字确认。未授权自行命名且缺正式主题时才按原规则询问。尚未分析内容时使用准备目录或临时候选号，不提前编造内容标题。
