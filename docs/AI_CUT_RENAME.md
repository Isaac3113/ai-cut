# AI Cut 改名、位置与换电脑说明

更新：2026-11-02。用户确认统一品牌 AI Cut，OneDrive 资料入口用 Project-AI Cut，C 盘源码和 GitHub 仓库用 ai-cut；同日后续用户授权仓库公开下载。本次调整名称和现行入口，不更改剪辑风格、原声、速度、比例确认、字幕、音乐、品牌素材或片头片尾偏好。

## 现行入口

| 内容 | 当前入口 |
| --- | --- |
| 项目品牌 | AI Cut |
| 源码、总 Skill 源码、技术 KB、运行环境、工作缓存 | `C:\Codex Workspace\ai-cut` |
| 原片、工作素材、公共素材、发布文案和已有工程入口 | `C:\Users\User\OneDrive\Documents\Codex Workspace\Project-AI Cut` |
| 公开 GitHub 仓库 | https://github.com/Isaac3113/ai-cut |
| 总 Skill 源码 | `skill/ai-cut/SKILL.md` |
| 新调用名 | `$ai-cut` |
| 本机安装 | 以实际安装回执为准；本机由原 `.codex/skills/talking-head-editor` 迁到 `.codex/skills/ai-cut`，其他新装客户端可用 `.agents/skills/ai-cut` |
| 正式媒体交付 | `C:\Users\User\OneDrive\Documents\Codex Workspace\AI 短视频创作\02_AI 视频作品库` |
| 正式模板展厅 | https://aicut.agi-top.com ；2026-11-02 已验证上线，供个人学习与免费交流 |

统一作品库不是本项目的源码目录，不随 AI Cut 改名。最新映射从 2026-11-01 的 AIVD032 归档记录派生到 `AI 短视频创作/04_整理记录/2026-11-02_AI-Cut改名/项目映射.json`，保留历史快照和旧工作 Hub 别名。当前下一号033是本次快照，后续先查实际索引与目录；005、006仍预留。

## 为什么不能搜索替换全部旧名称？

对外品牌、仓库、主目录、教学与正常 Skill 调用统一使用 AI Cut / ai-cut。以下是技术兼容合同或历史身份，保留不代表仍以旧名维护项目：

- Python 导入包 `talking_head_editor` 保留；发行包与新 CLI 为 `ai-cut`，旧 `talking-head` CLI 继续兼容。
- 优先使用 `AI_CUT_ROOT` 等新配置入口；已有 `TALKING_HEAD_*` 环境变量按实现兼容读取，不能借改名创建两份生产源码。
- 已安装辅助 Skill 的 manager、旧 schema、模板稳定 ID 和原素材文件名保留，避免原本受保护的安装或配置被认成外来文件。
- 视频冻结缓存 ID、ChatCut 项目／时间轴 ID、历史映射、旧来源路径和已经验收的媒体哈希不改。
- 旧 `skill/talking-head-editor` 源目录只保留迁移说明，不是第二套总 Skill。当前文档和安装器指向 `skill/ai-cut`。

根目录改名后可保留旧路径的隐藏 junction 兼容入口，用于尚引用旧绝对路径的历史工程及脚本。它指向同一份真实目录，不是第二份代码或媒体；不得复制另一套依赖，也不得误把 junction 当旧副本递归删除。是否已创建、具体指向和迁移检查以本机实际回执为准。

本机实际方式：C盘旧根为隐藏junction，真实源码在ai-cut；OneDrive旧根被当前会话占用，无法直接改整个根名，因此已将12个顶层条目移动到真实Project-AI Cut根，旧根保留隐藏兼容容器，其中6个目录junction、6个文件hardlink指向新入口的同一文件。不是第二套媒体或规则。不要批量删除旧兼容容器，其目录链接会继续被历史工程使用；云端是否同步这些本机链接须另行核对，不能由本机同文件判断推断。

## 当前电脑的迁移验证

执行记录留在源码根 `work/rename-ai-cut-20261102` 与 `work/ai-cut-rename-20261102`。需分别核验：

1. 新目录存在、Git origin 正确，原目录如保留兼容入口须指向新目录。
2. 新目录的 Python 可导入源码；editable 安装、FFmpeg/ffprobe 和本机路径配置已经指向新根。
3. 只发现一份有效 AI Cut 总 Skill；安装清单的 source_root 和各文件哈希正确。
4. HTML 首页、示例视频与本机原声映射可访问；分类、模板 ID、Demo 媒体内容保持。
5. 原 Hub 媒体按相对路径、字节数和选定哈希核对；最新统一作品映射的作品身份不变。
6. GitHub 实际名称和当前可见性、Git push 远端 SHA、本机检查分别记录。

本次发现5份更早的 `AI-Talking-Head-Editor` 工程指针在改名前就未找到对应目录，原文保留并标待恢复；不为“修复路径”虚构工程。其余当前可达的工程保留下级冻结名称，只调整根入口。

代码与规则、媒体、账号授权、在线工程是不同资源。改名、Git push 和本机文件存在不能证明 OneDrive 云端同步、新电脑运行或云端剪辑工程已经恢复。

## 另一台电脑怎样继续

把下面提示词交给那台电脑上的 AI 助手。先检查实际位置，不要求对方机器一定使用本机用户名或已具备全部媒体。

```text
这个项目已统一改名为 AI Cut。
GitHub 公开仓库：https://github.com/Isaac3113/ai-cut
C盘源码目标：C:\Codex Workspace\ai-cut
OneDrive资料入口：Project-AI Cut
正式Skill：ai-cut，源码skill/ai-cut/SKILL.md。

先检查当前源码、Git状态、分支和远端，保护本地未提交修改及旧安装；不要强制覆盖、重置、删除或重新下载模型。
如还在旧talking-head-editor源码目录，先读取新仓库docs/AI_CUT_RENAME.md及docs/CROSS_COMPUTER_UPDATE.md，按实际路径迁移主入口，并检查历史工程是否需要旧路径兼容入口。
把origin更新到新仓库并安全获取更新。GitHub旧地址可能重定向，但新配置统一使用ai-cut；不要创建同名旧仓库。
核对自己的OneDrive实际路径、最新作品索引与映射，不能回退到旧028快照。保持作品ID、来源、ChatCut项目ID和冻结缓存ID。
修复本机Python editable映射和runtime路径，再验证基础环境。保护旧Skill修改，按实际安装器迁移到一份ai-cut，核对source_root与哈希；不要保留两套生产规则。
自己的原片、模板包、Logo、片尾、账号和云工程分别核对，Git pull不会同步这些。
完成后分别报告目录、Git、Skill、环境、媒体与工程的实际状态；本次不重剪、不付费生成、不发布或部署网站。
```

## 网站与域名

HTML仍是同一份 `docs/template-gallery/index.html`，由登记表和接入记录生成；不是另做一个长期目录。新模板／本人小样仍按原生命周期规则更新同一中心，官方候选和已实测条目保留不同状态。

Vercel与Namecheap的操作步骤及实际上线记录读 [AI Cut 网站与域名教学](VERCEL_AI_CUT.zh-CN.md)。用户于2026-11-02明确授权助手配置并上线现有精选展厅，随后确认仅用于个人学习与免费交流、不用于业务获客或销售；Namecheap CNAME由用户填写。当前Hobby免费版已部署并验证HTTPS，未购买或升级套餐；同日后续按用户明确要求将GitHub源码开放下载，无需逐个邀请。此次展厅授权不扩大为原片、私人包、缓存或客户资料公开；历史准备阶段的“尚未部署”记录不能作为当前状态。
