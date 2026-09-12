---
name: remotion-best-practices
description: Remotion官方动画参考的本地入口。用于流程推进、重点字和动画时序的帧驱动规则，以及真实Remotion/React工程修改；普通口播由talking-head-editor主控，不默认安装运行时或声称使用Remotion渲染。
---

# Remotion官方规则：时序参考与按需工程支持

参考来自[remotion-dev/skills](https://github.com/remotion-dev/skills)，固定版本和文件哈希见installation.json。[原始入口](UPSTREAM_SKILL.md)保留。规则安装与引擎安装分别检查：本项目extensions/remotion-vd44的4.0.523已于2026-09-12真实渲染流程和头像片尾并导入ChatCut，证据见项目知识库14_Reference_Motion.md。这个案例不证明另一台机器已安装、所有动画都已使用或商业许可已确认。

1. 真人口播先遵守相邻talking-head-editor的总规则、用户偏好及画面规则。本机路线以project.json/revision、ChatCut路线以当前官方时间轴为唯一主工程；主Skill负责语义剪辑、音频和交付，本辅助不能替代主流程。
2. 设计重点字、对象动作和流程推进时可读[Markup](remotion-markup/REFERENCE.md)的帧驱动规则：动画由当前帧/时间确定，重复渲染与跳转到同一帧应得到同一画面。实际React实现使用官方对应版本的useCurrentFrame/interpolate等方式，不依赖实时CSS动画或计时器。
3. 只参考原则、实际由FFmpeg/Pillow执行时，要明确说明执行器。已有Remotion工程则检查固定版本、源代码与真实渲染文件；确实执行后才能说“已用Remotion渲染”。不因为引擎支持某效果就称本片已实现，不为普通重点字重复建React项目。
4. 视觉遵守每3～5秒变化、硬上限5秒：人物克制变化、原话短重点、相关素材和流程推进按语义排布。重点字是额外短暂强调层，基础字幕自然；SFX仅重点事件轻短出现，与安静BGM分轨，真人原声不降。具体参数由主偏好统一维护。
5. 动画必须展示对象动作并保留条件；并列状态不连成错误因果。与主时间轴的1.1倍速和输出时间对齐，生成后作为素材登记，不重复变速或叠加素材原音。片尾使用真实原片本人头像，不生成替代人物或虚构身份。
6. 实际已有Remotion项目先检查目录、Git状态、版本与用户改动。按问题读取[Captions](remotion-captions/REFERENCE.md)、[Render](remotion-render/REFERENCE.md)、[Studio](remotion-studio/REFERENCE.md)；确需新建独立动画项目才读[Create](remotion-create/REFERENCE.md)，版本/API不明才读[Docs](remotion-docs/REFERENCE.md)。不加载全套文档，不在已有Python项目根运行脚手架。
7. 首次启用运行时先核实[许可](https://www.remotion.dev/license)和用途，再处理实际缺失的环境并验证最小实片。没有运行与导出证据不得说引擎可用，规则开源也不等于所有商业使用免费。
8. 审看实际动画、字幕安全区、事件时序与素材来源，返回主Skill继续完整检查。仅实际启动测试后才能称Studio可交互；Codex右侧MP4仍是预览，不是编辑时间线，也不是剪映草稿。
