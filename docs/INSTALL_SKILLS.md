# 安装哪些Skill，按什么顺序

1. 仓库根执行 `scripts/install_skill.py` 安装唯一总入口 ai-cut。直接复制时必须保留references/scripts/agents，并配置源码目录。
2. ChatCut路线：在自己的Codex插件目录安装官方ChatCut，自己登录/授权；先读官方chatcut-plugin-basics，按总Skill调用asset-import、talking-head-guide、transcription（需要时）、create-motion-graphics、verification、export。插件源码不包含在本项目。
3. Remotion/video-use：请Codex使用系统skill-installer，严格读取extensions/upstream-lock.json中的repository、commit和path，把上游完整目录放进一个新的暂存目录（每个子目录以锁文件name命名）。然后执行：

```powershell
.\.venv\Scripts\python.exe scripts/install_extensions.py --staging '<暂存目录>' --check
.\.venv\Scripts\python.exe scripts/install_extensions.py --staging '<暂存目录>'
```

安装器检查上游文件哈希、现有安装归属和本地修改。遇到已存在且改过的Skill先比较，不覆盖。适配入口需要上游REFERENCE.md等文件，不能孤立复制。

4. HyperFrames：官方来源 https://github.com/heygen-com/hyperframes 。按extensions/hyperframes-vd44/skills-lock.json的技能名称/path，在该动画目录的`.agents/skills`安装所需官方规则。先hyperframes与motion-graphics，再按需core/animation/keyframes；使用组件才加载registry，运行命令时加载cli。版本变化先比较来源和实际效果，不全局更新所有Skill。
5. 软件运行时与Skill是两回事：按根README安装Node、引擎、字体与FFmpeg，然后实际check/render。确认工具可用后处理自己的真实原片。

小Skill具体何时调用和应产出什么，见主Skill的references/approved-workflow.md。仅安装规则不等于已经完成视频。开始新片仍须先取得用户对视频比例的明确回答，不能用原片或封面比例代替；同片修改沿用确认。采用本创作者预设且含电脑实操时，按practical-demo约每3秒安排真实重点变化及同步轻音效，无实操则跳过。ChatCut主时间轴保留独立人声、BGM及逐事件SFX片段；安装本地特效工具不等于这些声音和在线工程已建立。


## 换电脑时保持同一工作路线（2026-09-21）

GitHub同步规则和代码，不自动同步插件授权、账号登录、素材、本机依赖或云工程定位。先pull最新代码，保护并比较已有Skill，再安装/同步；默认ChatCut路线需实际列出可调用工具，确认自己的账号与既有项目/时间轴，避免重复建项目。没有工具时报告缺口，不把“文档说已安装”当检查通过，也不静默转成本机最终交付。

已有个人Skill绑定其他源码根时，安装器会保留它并报错。先核对installation.json归属与文件哈希、保留旧安装备份，再由用户明确选择的源码根重新安装；不要绕过归属检查或删除运行环境。本次本机既有运行根的规则同步不等于另一台电脑环境已验证。

实操无声素材helper在skill/ai-cut/scripts/render_practical_demo.py；用法与已验证画幅边界见references/practical-renderer.md。它可复用六类画面效果，但不会建立ChatCut项目、上传素材或生成独立音效时间轴，这些仍需主流程实际完成。
