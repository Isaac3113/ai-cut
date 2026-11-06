# 换电脑更新 AI Cut

GitHub 同步本仓库的代码、公开剪辑 Skill 和模板说明。自己的原片、品牌素材、账号登录、付费服务额度与剪辑工程需要分别准备；`git pull` 不代表这些已经恢复。

公开 AI Cut 的默认范围是自动剪辑、字幕、特效模板、所需封面和本机成片交付。不需要讲师的 Google Drive、Content Management OS、私人文案 Skill 或发布账号；私人归档／发布不随公开仓库安装，也不会因为认可成片就自动执行。

## 先检查旧电脑与新电脑

1. 旧电脑如有源码修改，先检查并正常 commit、push；不要把 `.git`、依赖或运行缓存交给 OneDrive 同步。
2. 新电脑先找到已有源码、同名 Skill 及 `installation.json`。有本机修改就先比较，不能 `reset --hard`、强制覆盖或删除旧运行环境。
3. 源码建议放在非同步代码目录，例如 `C:\Codex Workspace\ai-cut`。这是你自己的位置，不是讲师共享目录；交付目录由你指定。
4. 已有正确仓库且工作区干净、没有需要保留的分歧时，再安全更新：

```powershell
git fetch origin
git pull --ff-only origin main
```

没有源码时，按[新手安装教学](NOTION_GUIDE.zh-CN.md)从公开仓库 clone。没有权限申请步骤；遇到 404 先核对网址和网络。

## 安装与恢复分别验证

1. 阅读当前 `AGENTS.md`、`README.md`、[公开 Skill](../skill/ai-cut/SKILL.md)和[安装说明](INSTALL_SKILLS.md)。不要把旧电脑的绝对路径或历史环境检查结果当成新电脑事实。
2. 准备本机 Python、FFmpeg/FFprobe 和当前制作所需依赖，不复制另一台电脑的 `.venv`、模型缓存或 `node_modules`。
3. 核对旧 Skill 归属及哈希，保护本机修改后，从当前仓库安装公开 `ai-cut`：

```powershell
.\.venv\Scripts\python.exe -B -X utf8 scripts/install_skill.py
```

4. 在自己的 Codex 中实际检查所选剪辑插件、账号和可调用工具。已有 ChatCut 工程要核对同一个项目／时间轴；素材路径改变时按软件提示 relink，不新建平行权威工程。
5. 找到自己有权使用的原片、Logo、片尾、音乐及模板包。讲师的品牌、速度、目录、作品编号和历史授权不自动套用。
6. 先用一段自己的短片检查读片、字幕和实际导出。新视频仍须明确比例；已有确认不要重复问。最终给出当前 MP4、本版已有字幕和所需封面的本机路径，未完成检查如实说明。

## 模板展厅与特效运行

- 中文清单在 `templates/README.zh-CN.md`；公开演示在 `docs/template-gallery/demos`。看得到 Demo 不等于本机已装好所需引擎，或所有官方原包都已附送。
- 用 `python scripts/serve_template_gallery.py` 启动本机展厅；终端显示的 `127.0.0.1` 地址只指向当前电脑，分享该地址不会把媒体发给别人。
- MotionGit 使用你自己的合法原包；配置按适配器文档核对。原包、Key、完整私人原片和客户资料不进公开 Git，不复制另一电脑的保护内核代替安装。
- 安全更新规则和当前模板登记后，按内容选型并核对输入、许可及本机依赖；监测或目录登记不代表已替新片验证全部效果。

## 可以直接交给新电脑上的 AI

```text
请安全更新我的公开 ai-cut 项目。
先核对源码目录、origin、分支、Git 状态与现有 Skill 的 installation.json，保护本地修改。
阅读 README、AGENTS、公开 Skill 和当前安装说明；确认无分歧后安全拉取并安装 ai-cut。
检查我自己的剪辑工具、账号、素材、依赖及已有工程，不继承讲师的个人设置。
本次只恢复剪辑和本机交付，不创建云盘归档、营销系统草稿或发布任务。
分别报告 Git、Skill、依赖、工具连接、素材与工程的实际结果。
```

创作者历史的作品库迁移和旧工程映射可在相应有日期的技术记录中追溯；这些是历史来源，不是公开安装的前置条件。
