# 安装哪些Skill，按什么顺序

1. 仓库根执行 `scripts/install_skill.py` 安装唯一总入口 talking-head-editor。直接复制时必须保留references/scripts/agents，并配置源码目录。
2. ChatCut路线：在自己的Codex插件目录安装官方ChatCut，自己登录/授权；先读官方chatcut-plugin-basics，按总Skill调用asset-import、talking-head-guide、transcription（需要时）、create-motion-graphics、verification、export。插件源码不包含在本项目。
3. Remotion/video-use：请Codex使用系统skill-installer，严格读取extensions/upstream-lock.json中的repository、commit和path，把上游完整目录放进一个新的暂存目录（每个子目录以锁文件name命名）。然后执行：

```powershell
.\.venv\Scripts\python.exe scripts/install_extensions.py --staging '<暂存目录>' --check
.\.venv\Scripts\python.exe scripts/install_extensions.py --staging '<暂存目录>'
```

安装器检查上游文件哈希、现有安装归属和本地修改。遇到已存在且改过的Skill先比较，不覆盖。适配入口需要上游REFERENCE.md等文件，不能孤立复制。

4. HyperFrames：官方来源 https://github.com/heygen-com/hyperframes 。按extensions/hyperframes-vd44/skills-lock.json的技能名称/path，在该动画目录的`.agents/skills`安装所需官方规则。先hyperframes与motion-graphics，再按需core/animation/keyframes；使用组件才加载registry，运行命令时加载cli。版本变化先比较来源和实际效果，不全局更新所有Skill。
5. 软件运行时与Skill是两回事：按根README安装Node、引擎、字体与FFmpeg，然后实际check/render。确认工具可用后处理自己的真实原片。

小Skill具体何时调用和应产出什么，见主Skill的references/approved-workflow.md。仅安装规则不等于已经完成视频。
