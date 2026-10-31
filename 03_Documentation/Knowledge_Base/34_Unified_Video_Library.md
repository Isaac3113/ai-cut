# 统一AI视频作品库与旧工程衔接（2026-10-31）

本页记录所有者本轮授权的位置与命名合同；末节仅记实际执行的验证，不代表重新迁移媒体或已验证另一台电脑。其他创作者按自己的明确约定，不继承本人的媒体与账号授权。

依据本轮[完整衔接提示词](<C:/Users/User/OneDrive/Documents/Codex Workspace/AI 短视频创作/04_整理记录/2026-10-31_统一AI视频作品库/给AI-Talking-Head-Editor的衔接提示词.txt>)、新Hub的[AGENTS规则](<C:/Users/User/OneDrive/Documents/Codex Workspace/AI 短视频创作/AGENTS.md>)、[素材索引](<C:/Users/User/OneDrive/Documents/Codex Workspace/AI 短视频创作/素材索引.md>)与[实际项目映射](<C:/Users/User/OneDrive/Documents/Codex Workspace/AI 短视频创作/04_整理记录/2026-10-31_统一AI视频作品库/项目映射.json>)；后续分号仍核对当时实际状态。

## 三个根，各司其职

| 根位置 | 职责 |
|---|---|
| C:\Codex Workspace\talking-head-editor | Active Repo、总Skill源码、唯一技术KB、运行环境、动画源码、可执行工作工程及cache；仍由private GitHub管理源码 |
| C:\Users\User\OneDrive\Documents\Codex Workspace\Projects-AI-Talking-Head-Editor | 旧工作Hub；原片、工作素材、品牌资料、固定片尾、发布TXT与旧工程入口原位保留 |
| C:\Users\User\OneDrive\Documents\Codex Workspace\AI 短视频创作\02_AI 视频作品库 | 正式交付作品库；非空参考图／AI 成片及作品根已有字幕 |

新Hub的AGENTS.md、素材索引.md和04_整理记录/2026-10-31_统一AI视频作品库/项目映射.json共同定位作品。交付根与原工作Hub是不同角色；不要只把旧project_hub位置改成作品库根，否则原片、Logo和片尾查找会失效。另一台电脑按实际OneDrive根及本机配置定位，不迁移源码或运行时到库中。

## 统一ID与来源标记

作品目录为 AIVD-三位编号 - 主要制作来源 - 简短标题。所有来源共用一个编号空间：Codex剪辑的真人口播／录屏用Codex剪辑；主要由即梦或Higgsfield生成后再剪辑，仍保留主要生成来源，完整工具链另记，来源不等于发布平台。

同一作品更新、换工具、重剪或改字幕不换ID。先查实际目录、索引和映射再分号；AIVD-005／006预留，不创建空目录。AIVD-028是2026-10-31当日下一号快照，不能成为代码里的固定next值。

旧口播项目的17条作品必须查实际映射：旧1～4对应011～014，旧5-01～5-08对应015～022，旧7对应023，旧8～11对应024～027。旧6没有映射，不因新库的006预留号创建另一作品；未知别名先报告待核实。旧AIVD11的新名为AIVD-027 - Codex剪辑 - AI角色怎样从单图做到多角度。

新ID只负责对外交付和关联；旧ChatCut project／timeline、冻结cache ID、本机工作路径、原片名和既有归档文件不全局替换。长视频母片／子切片的现有旧别名也通过映射关联，不以旧母号派生规则绕开统一作品编号。

## 作品目录只收媒体

- 参考图：本片封面及采用图片；两比例封面制作和聊天直接展示偏好沿用。
- AI 成片：选定交付视频。库内历史原片／片段／测试也可能按此分类，分类名不等于当前已验收成片；这不是把本机全部原片、工程或cache搬进库的指令。
- 作品根：已经存在、与交付版本对应的SRT等字幕文件。没有就不建，不为了归档另生成字幕或空目录；制作本身需要的转写、字幕与QA仍按原剪辑流程处理并保留工作记录。

Facebook文案、小红书文案、固定第一评论三份TXT继续生成、展示和确认，保留原工作资料入口／聊天，不进入作品库；报告、工程说明、ZIP、检查证据、源码、依赖和cache同样不进入作品目录。索引关联原工程及发布资料入口，不在媒体作品里再增加说明目录。

AIVD-023（旧AIVD7）当前只有待视频校验封面，没有成功归档的当前成片；不能用参考片、过程录屏或过期字幕补齐。新库当前仍含历史媒体文件，不能把统一归档当成逐片质量验收，也不能顺便清理未获本次授权的旧内容。

## 复制、冲突与同片替换

1. 按统一ID定位同片和真实输出，核对视频、封面与已有字幕是否为同一版本；原片／缓存／旧工程原位保留。
2. 验证目标属于配置的正式作品库及映射作品后，只复制选定交付；有实际文件再创建对应分类。
3. 逐文件记录源路径、目标路径、字节数及SHA256并核对一致；清单放04_整理记录或原工作记录，不进作品目录。
4. 同名同SHA256可核对沿用；同名异SHA256先停止该文件并记录冲突，不盲目覆盖。经用户授权的同片更新，先验证真实新导出，再按既有最新版偏好替换已知当前版，不静默覆盖不同内容、不自动堆积历史。
5. 已归档旧来源、迁移时保留的历史文件和冻结ID不重复搬动、删除或重命名。复制核验不证明OneDrive远端同步；实际生成、完整视听、用户认可和发布状态分别报告。

## 本次不改变的规则与验证边界

确认本条比例、原声原意、绝对1.2倍一次、字幕、品牌、轻音乐与独立音效、0.1秒封面、固定片尾、可编辑主时间轴、模板按内容选用及发布授权边界均沿用原合同。库的主要来源标记不替用户换剪辑路线或发布内容。

更新配置、Skill源码、已安装Skill与路径工具后，各自检查真实状态；不得只因改了文档就声称导出路径已实现、媒体已同步或另一台电脑已恢复。无需为本次位置修改重剪整片、调用付费生成或发布内容。执行与测试结果以末节及本轮实际回执为准。

## 本机配置与只读路径工具

当前本机`runtime.local.json`已将以下职责分开；该文件由Git忽略，换电脑按实际OneDrive根合并相应键，保留原有FFmpeg／FFprobe等配置，不整份覆盖：

| 配置键 | 当前用途／位置 |
|---|---|
| project_hub | 原Projects-AI-Talking-Head-Editor工作Hub |
| video_work_root | C:\Codex Workspace\talking-head-editor\work\videos |
| delivery_library_root | AI 短视频创作\02_AI 视频作品库 |
| delivery_registry | AI 短视频创作\04_整理记录\2026-10-31_统一AI视频作品库\项目映射.json |
| delivery_asset_index | AI 短视频创作\素材索引.md |

`scripts/delivery_library.py`只规划路径和读取现有文件，不占号、不建目录、不复制文件、不改索引。明确CLI参数优先，其次对应的`TALKING_HEAD_DELIVERY_LIBRARY_ROOT`、`TALKING_HEAD_DELIVERY_REGISTRY`、`TALKING_HEAD_DELIVERY_ASSET_INDEX`环境变量，最后使用本机配置。新片计划仍要在实际交付前重新核对目录与索引并登记，不把一次plan视为跨任务锁号。

```powershell
.\.venv\Scripts\python.exe -B -X utf8 scripts/delivery_library.py plan --title "简短标题" --source-label Codex剪辑 --stem-suffix 9比16_1.2倍
.\.venv\Scripts\python.exe -B -X utf8 scripts/delivery_library.py plan --existing "AIVD-027"
.\.venv\Scripts\python.exe -B -X utf8 scripts/delivery_library.py audit --existing "AIVD-027" --hash
```

提供`--subtitle`时必须选已有非空字幕；没有就不提供，不能为补齐旧同目录三件套新造字幕。`delivery_names.py`保留通用制作区文件类型命名；正式作品库的视频与字幕分开放置，布局由新工具检查。`create_video_folder.py`只建工作Hub的01～04及C盘工程目录；它不创建旧05／06或统一库空目录，已有旧工作结构可显式复用。

路径审计与文件哈希只证明位置／字节和本次选择，不能证明全片内容、字幕同步、未来发布或OneDrive云同步；本次未为验证重新剪辑或生成媒体。

`plan`中的video_path／cover_paths是下一次选定导出的目标名，不表示同名文件已存在；既有归档文件保留历史名，找真实文件须读取`audit`列出的路径。恢复工程时只认原04指针或原工作记录；缺入口先标待核实，不按新作品名新建替代cache。

## 2026-10-31实际验证

- 49项针对性回归通过：作品库规划19、工作目录11、文件类型命名4、最终字幕6、Skill源码根解析4、源码分发保护5。测试只用临时目录／元数据，不渲染视频。
- 真实配置下17个只读CLI案例通过：新片候选028且不占号／不建目录／不补字幕；旧11回到027，旧5八片回到015～022，旧4继续使用04指针中的001冻结工作；023仅3张封面、无视频；裸旧号、未映射旧6、预留005及改写Higgsfield主要来源被拒绝。真实库、索引和映射前后快照未变。
- 库的25项目结构、216目标文件大小、75份Copy来源存在／字节及17个原项目目录入口通过；027三份源／目标本轮SHA一致。216份全量SHA为迁移时的既有验收，本轮没有重算全部视频，也没有重新做内容质量／字幕时序验收。
- 实际安装的总Skill30个文件与源码、installation.json的SHA256一致；source_root仍为C盘Active Repo，quick_validate通过。README生成展示区未改；原声／速度／比例确认／品牌／音乐／片头片尾实现未改。
- 独立前向检查发现：017原项目缺04工程指针，010旧平台入口已不可达；它们没有被推断成新工程，原资料未改。它们是既有恢复入口待核实项，不是作品库媒体不存在或丢失的结论。

本机技术证据在`work/unified-delivery-20261031/`：independent-library-audit.json、real-path-validation.json、forward-check.json、learning-archive-validation.json。它们留本机，不复制进媒体作品目录。Git同步另以提交／远端回执核对；OneDrive远端同步和其他电脑仍未验证。
