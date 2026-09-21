# 实操图形层渲染 helper

`scripts/render_practical_demo.py`，独立版本 `approved-practical-v1`。此 helper 晋升自用户认可的完整版实操渲染器。它读取真实视频当前帧，输出**无声音、无字幕、无 Logo 的图形层**；不能把 `graphics-silent.mp4` 当成完整成片交付。

## 使用边界

- 已验证布局为 **1080×1080、30 fps**，输入为方形像素的 **16:9 视频**。源画面完整放在 y=180、高 608 的区域；流程条在 y=805–850，字幕与标题空间留给主合成器。
- 脚本拒绝非 16:9 输入。其他目标比例、录屏比例、动态裁切、复杂脸部小窗布局必须显式适配并看真实短样；不要把这个 helper 当成跨画幅自动布局框架。
- 依赖 Python、Pillow、FFmpeg、FFprobe；Windows 默认用微软雅黑/黑体。其他机器须准备相应中文字库并检查字形，不可把缺字预览当通过。
- 原片只读。用新 revision 目录渲染；非空输出目录默认拒绝。`--force` 只表示明确允许覆盖该目录内的渲染器输出，仍禁止覆盖源视频、配置、脚本及输出符号链接，不删除目录。
- 这层没有音频逻辑，也没有通用“音乐 70%”默认。配乐选择、音量与音效必须由主时间轴按本条视频处理；某一案例坐标、遮罩高度、文案、歌曲和音量不可照搬到下一条。

## 执行步骤

1. 先识别口播中的真实电脑实操时间段，绑定主时间轴；没有实操就不调用。
2. 按讲解识别重点，从真实源画面量取像素坐标。每约 3 秒安排一个有意义的提示，六类交替，不机械地每次放大。先做事件表，再运行审计；脚本不会补造默认事件来掩盖遗漏。
3. 对移动、缩放或手持拍屏使用 `rect_keyframes` 跟踪。`lens` 只截取**当时正在解码的同一帧**；不能取别的时间的清晰截图替代当前操作。
4. 先批量预览，检查目标、遮挡与语义，再导出代表段；完整渲染完成后，由主合成器加入**同一有效时间轴**的人声、BGM、每个重点效果对应的可听 SFX、字幕及品牌 Logo。
5. 核对最终视频帧数、时长、解码与声音，查看进场/停留/退场、流程转折、首尾边界。技术审计只检查几何和时间，不能代替真实语义审阅、连续观看或试听。

## CLI

工具解析顺序：JSON 的 `ffmpeg`/`ffprobe` 明确配置 → `TALKING_HEAD_EDITOR_ROOT/.runtime/ffmpeg/bin` → PATH。配置中的 `source` 和显式相对工具路径均以 **JSON 所在目录**为基准，和 shell 工作目录无关。

以下命令从源码仓库根目录运行，配置与输出路径请换为本条的实际位置。

```powershell
python skill/talking-head-editor/scripts/render_practical_demo.py --config work/practical.json --validate-only
python skill/talking-head-editor/scripts/render_practical_demo.py --config work/practical.json --out-dir work/practical-previews-r1 --stills-only --preview-times "1,3.9,6.9,9.9,15.9,21.4"
python skill/talking-head-editor/scripts/render_practical_demo.py --config work/practical.json --out-dir work/practical-sample-r1 --range-start 0 --range-duration 6
python skill/talking-head-editor/scripts/render_practical_demo.py --config work/practical.json --out-dir work/practical-full-r1
```

`--validate-only` 只读，不要求 `--out-dir`，不创建文件。输出真实事件数量、类型、相邻效果起点最大间隔、超过 3 秒的间隔及首尾覆盖提示。配置错误返回非零；节奏遗漏报告 `cadence_ok: false` 和 `warnings`，不擅自修改计划。是否允许语义上的例外由主流程记录。

`--range-start` 必须对齐输出帧，`--range-duration` 四舍五入为整帧。**所有事件和预览时间始终相对于整段实操**，截取渲染范围不归零事件时间，也不改变声音时间轴。源定位为 `source_start + range_start × speed`；第 i 帧的效果时间为 `range_start + i / fps`。用于恢复验证时选新目录，按这些映射重新合成对应主时间轴片段。

## 配置字段

| 字段 | 含义 |
| --- | --- |
| `source` | 源视频，绝对路径或相对 JSON 的路径 |
| `source_start` | 实操段起点在未加速原片中的秒数 |
| `duration` | 实操段在有效输出时间轴中的时长，秒 |
| `speed` | 原片绝对速度倍率；默认 1.2，不对已加速片重复乘 |
| `fps` | 输出帧率；默认且已验证 30 |
| `source_top_mask` | 在原片像素中遮住顶部的高度，默认 0；按实际隐私区域量取 |
| `events` | 实操效果事件数组，必须显式规划 |
| `flow_steps` | 可选三步流程条；每段提供 `start/end/active/labels` |
| `flow_labels` | 可选的统一三步文字；只在某段没有 `labels` 时使用，不能遗漏实际语义文字 |
| `preview_times` | 可选整段实操时间点数组；`--stills-only` 导出全部，普通渲染最多取前 6 个；CLI 可指定任意批量点 |
| `ffmpeg` / `ffprobe` | 可选执行文件路径或 PATH 命令名 |
| `preset` / `crf` | 可选 H.264 编码参数，默认 medium / 19 |

每个效果必填 `kind`、`start`、`end`、`rect_keyframes`。时间以整段实操输出起点为 0；范围为 `0 ≤ start < end ≤ duration`。关键帧必须严格按时间递增且覆盖整个事件，`x/y/w/h` 全为**原片像素**，矩形在源画面内。帧间线性插值，不是固定套模板坐标。

| `kind` | 用途与行为 |
| --- | --- |
| `lens` | 圆形局部放大：当前帧裁切、原目标框、引导线、柔和进退场；适合小字和关键设置 |
| `focus` | 青蓝框选和角标；明确指出正在讲的真实对象 |
| `spotlight` | 周围轻暗、目标恢复当前原画面亮度；适合拥挤界面 |
| `underline` | 目标下方扫描下划线；适合字段、标签、重点行 |
| `pulse` | 缓慢呼吸轮廓；适合强调目标，不伪装为真实点击或 UI 状态 |
| `flow` | 框选目标并沿实际可见连接运行光点；`path` 是源像素折线，缺少路径只框选，不凭空画连接 |

可选事件参数：`ramp`（默认 0.34 秒，自动不超过事件时长的三分之一）、`label`、`center`（放大镜中心，输出像素）、`diameter`（放大镜直径）、`crop_padding`（扩展当前矩形裁切范围）、`sweep`（下划线扫动时长）、`path`（仅 flow，至少两个非重复源像素点）。复杂移动路径需要拆成多个经实际审阅的事件；矩形关键帧不会自动跟踪静态 `path`。

`flow_steps.labels` 是当段真实讲解的三步短词，`active` 为 -1（全中性）、0、1、2。步骤区段须按时间递增且互不重叠。可在不同流程区段换一组 labels，不能让上一流程的固定词残留。

以下配置仅展示结构，目标坐标与流程词**必须按本条真实画面重新量取**：

```json
{
  "source": "../01_原片/screen-demo.mp4",
  "source_start": 0,
  "duration": 6,
  "speed": 1.2,
  "fps": 30,
  "source_top_mask": 0,
  "events": [
    {
      "kind": "focus", "start": 0, "end": 2.2,
      "rect_keyframes": [
        {"time": 0, "x": 320, "y": 260, "w": 300, "h": 100},
        {"time": 2.2, "x": 320, "y": 260, "w": 300, "h": 100}
      ]
    },
    {
      "kind": "lens", "start": 3, "end": 5.8,
      "label": "关键设置", "center": [785, 499], "diameter": 460,
      "rect_keyframes": [
        {"time": 3, "x": 420, "y": 430, "w": 260, "h": 100},
        {"time": 5.8, "x": 440, "y": 435, "w": 260, "h": 100}
      ]
    }
  ],
  "flow_steps": [
    {"start": 0, "end": 3, "active": 0, "labels": ["选择入口", "填写内容", "检查结果"]},
    {"start": 3, "end": 6, "active": 1, "labels": ["选择入口", "填写内容", "检查结果"]}
  ]
}
```

## 输出与复核记录

输出包括 `graphics-silent.mp4`、`preview-*.png`、FFmpeg 日志和 `graphics-manifest.json`。Manifest 记录独立 renderer revision、脚本/配置/视频 SHA-256、源参数、真实时间范围、预览点、事件、审计与静音层标记。恢复验证须保留原配置及依赖，并把图形层与主时间轴重新合成，不能只证明 PNG 能生成就宣称完整工程可恢复。
