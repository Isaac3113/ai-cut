# 项目入口、代码与每条视频的存放

执行存放或迁移前先读用户的共享规则及Project Hub内PROJECT_STRUCTURE.md。用户给OneDrive项目路径时，它是项目资料入口，不能推断为把源码、依赖或缓存也放进去。此前“所有内容同一个物理根”的本项目规则已纠正。

## 两个根，一条权威时间轴

- `CODE_ROOT`：OneDrive之外的Active Git Repo；本用户为 `C:\Codex Workspace\AI-Talking-Head-Editor`。源码、总Skill源码、技术知识库、动画源工程、.git、.venv、node_modules、模型、缓存和实际剪辑工作目录在这里；代码经private GitHub同步。
- `PROJECT_HUB`：用户指定的资料项目；本用户使用OneDrive下Projects-AI-Talking-Head-Editor。保存PROJECT_STRUCTURE.md、需求、教学阅读件、原片、素材、参考、封面、字幕、完整制作说明与完整交付。这里不保留Active Git Repo、展开的运行时或缓存。
- 技术知识库只有CODE_ROOT/03_Documentation/Knowledge_Base一份正式维护位置；Hub记录链接，不另维护同步副本。可供分享的固定ZIP/阅读导出不属于第二份Active Repo。
- ChatCut仍只有官方时间轴一条执行依据；本机模式仍沿用既有job/revision，存储分开不建立两套剪辑清单。

```text
CODE_ROOT/
  src/ scripts/ skill/ extensions/ tests/
  .git/ .venv/ .runtime/
  03_Documentation/Knowledge_Base/
  work/videos/AIVD - 视频主题/04_剪辑工程/
    job或原有outputs/       实际工程、动画工作文件、抽帧、日志、缓存

PROJECT_HUB/
  PROJECT_STRUCTURE.md
  00_项目入口.md
  视频项目/AIVD - 视频主题/
    00_视频说明.md
    01_原片/
    02_自有素材/
    03_参考视频/
    04_剪辑工程/本机剪辑工程.md   只写位置及恢复入口，不复制运行时
    05_成片/YYYYMMDD_版本说明/   MP4、封面、TXT、SRT、完整说明与检查证据
    06_历史交付/
  学员分发/                    完整Skill ZIP与教学阅读件
  项目资料/                    需求原稿、存储说明与小型验收报告
```

## 实际创建与恢复

每条新口播单独建文件夹。本用户命名 `AIVD - 视频主题`，保留用户给的中文主题和全角问号；同片重剪沿用文件夹、成片另存版本。Windows非法字符不静默替换。

在CODE_ROOT执行：

```text
python scripts/create_video_folder.py --hub "PROJECT_HUB" --name "AIVD - 视频主题"
```

它真实创建Hub资料目录及CODE_ROOT/work/videos内的工作目录，并在Hub的04文件夹写本机位置。`--existing`核对成对目录后复用，不覆盖。Hub查找顺序为明确`--hub`（兼容旧`--root`参数）→TALKING_HEAD_PROJECT_HUB→本机runtime.local.json.project_hub；没有配置就明确报错，不退回把资料放在源码根。工作根通过`--work-root`或runtime.local.json.video_work_root设置，默认CODE_ROOT/work/videos，禁止落入OneDrive。程序同时拒绝从OneDrive内的Active Repo启动该建目录流程。

原片与交付继续按final-delivery.md保存和核对哈希。需要跨电脑恢复时，提供不含运行时/缓存的工程导出及素材绑定；另一台电脑用自己的Git checkout与本机工作目录恢复，不靠OneDrive搬运.venv/node_modules。个人Codex Skill和官方插件仍由应用管理；安装记录绑定CODE_ROOT。

## 迁移与验收

共享规则优先：先核对branch/HEAD/remote/dirty/untracked/env存在性、备份未推送工作。其他电脑可能仍在使用旧OneDrive源码时，在逐台核对之前保留旧目录，标记LEGACY-CLEANUP-PENDING。原件尚未移走时可先建立非OneDrive副本、验证依赖与登录。

仅在迁移条件满足后移出旧源码/缓存；不批量删除，不用Git版本覆盖未知本机改动。保留旧新路径映射，历史日志不篡改；不要在OneDrive创建指回本机源码/缓存的目录junction来伪装已移出。

迁移后核对Git历史、已安装Skill哈希及source_root、实际模块路径、FFmpeg/模型可见性、真实job状态和代表片段、成片与字幕哈希。更新PROJECT_STRUCTURE.md、源码知识库与现有登记；确认private GitHub提交。文件数量减少是本机事实，OneDrive同步队列完成与网络速度改善须另外观察，不能由.gitignore或测试结果推断。
