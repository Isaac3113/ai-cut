# 逐片模板接入记录

`template-integrations.json` 是独立的接入记录，不是第五类模板。本文件是结构说明，由总 Skill 的模板生命周期规则明确引用；它不会自行执行下载、渲染、Git 上传或公开发布。

2026-10-27 已收录 AIVD 10 的 4 条本人接入记录，引用既有 `mg-control-flow`、`mg-control-steps`、`mg-control-hub`、`mg-control-kinetic`，不新增模板编号或第五层。Demo 使用已实际渲染并放回本片 ChatCut 时间轴的官网概念画面，另按同源时钟合成本人圆窗；它们是短静音案例，不是完整成片。已有四份登记表和官方快照保持原样，基线分别为 72／70／55／19，共 216 条目录；它们缺行仍会使构建失败。特别是 70 控件对应旧包 2.7.17-alpha.2，其版本、210 变体和实际验证范围不因新案例改变。

本次实际覆盖 `flow/chain`、`steps/track`、`hub/constellation`、`kinetic/stack` 的横屏输入。4 个精选 MP4 共 1,497,168 bytes，均低于 20 秒／8 MiB、无音轨，已完整解码并查看首中尾等编码样本及圆窗细节；未连续观看，用户美学确认仍待复核。原生时码、圆形 `.m` 标记和出场淡出保留。个人包仅记录整包 SHA256 与公开调用合同，不入库；含客户及网址的白板窗口镜头只留本机生产记录，不作为可提交 Demo。

## 引用既有条目或加入新候选

- **既有条目**：填写稳定 `entry_id`，不提供 `new_entry`。构建只附加接入记录与本人 Demo；保留原版本、来源、原 Demo 和原验证状态。按带时区的 `integrated_at` 选择最新本人 Demo 展示，不重复增加模板条目。
- **新官方候选**：完成真实小样与审核后，提供完整 `new_entry`，放入既有 `style`／`control`／`remotion`／`effect` 层。`new_entry.id` 必须等于 `entry_id`，`source_url` 与本次官方来源一致；`demos` 留空，使用本次已验证的 `demo`。不能用它覆盖已有 ID。
- 每次接入用独立记录 ID。相同条目可以有多次不同版本接入；MP4 使用独立版本路径，不覆盖旧素材。不同条目不能共用同一个输出路径。本人 Demo 只是本片、本版本、本输入的证据，不代表所有模板、变体或另一台电脑已可运行。

## 最小字段示例

以下仅展示结构，包含占位值与尚未通过的 QA，不能直接登记为成功。完成真实制作和检查后才填写有效来源、哈希、时间和状态。不要把本机原片路径、个人 `.motion`、Key、账户信息或客户敏感信息放进这些字段。

```json
{
  "id": "integration-project-template-version",
  "entry_id": "<现有稳定条目ID>",
  "project_id": "<本条项目编号>",
  "integrated_at": "<真实完成时间，ISO8601并含时区>",
  "source": {
    "url": "https://<已核对的官方页面>",
    "package_id": "<官方包或仓库身份>",
    "version": "<本次使用版本>",
    "sha256": "<本次包或固定源码版本的64位SHA256>",
    "official": true,
    "verification_note": "<官方身份、入口与版本的实际核验依据，不含凭据>"
  },
  "invocation": {
    "method": "<官方适配器或许可允许的源码入口>",
    "command": "<可复用调用方法，用本机配置与参数占位符，不含私有绝对路径或Key>",
    "guide_url": "https://<官方公开指南>",
    "inputs_zh": ["<需提供的本片输入与时间映射要求>"]
  },
  "rights": {
    "private_demo_redistribution": true,
    "evidence": "<本人素材与模板渲染小样可进入私人库的实际授权依据>"
  },
  "qa": {
    "state": "pending",
    "decode_verified": false,
    "sample_images_viewed": false,
    "continuous_watch": false,
    "scope": "<真实检查过的范围；未检查的项目明确保留>"
  },
  "demo": {
    "kind": "own",
    "path": "demos/integrated/<项目>/<模板版本>/demo.mp4",
    "description_zh": "<本片本人素材静音节选与示例身份说明>",
    "sha256": "<实际MP4的64位SHA256>",
    "bytes": 0
  }
}
```

实际通过后，`qa.state` 使用 `verified_demo`，`decode_verified`、`sample_images_viewed` 必须为真实的 `true`；这不等于连续观看、完整听审或用户审美认可。工具会检查真实文件存在、哈希及大小；严格构建还使用现有 FFprobe/FFmpeg 验证单视频、无音轨、最多 20 秒、最多 8 MiB，并完整解码。官方来源和许可记录需要执行者实际核验，HTTPS 和布尔字段本身不能替代授权证据。

新候选的 `new_entry` 必须包括 `id`、`label_zh`、`layer`、`category_zh`、`description_zh`、`uses_zh`、`avoid_zh`、`inputs_zh`、`version`、`source_url`、`source_id`、`license`、`availability`、`validation`、`demos: []`。新条目的验证状态由构建器限定为“仅本片接入已检查”；不能写成整套引擎通用验收。

## 更新和验证

在正确的 active repo 根执行；只使用已有 Python、FFmpeg 和 FFprobe。先完成实际官方制作，再登记，以下命令不负责下载模板或合成新片。

```powershell
.\.venv\Scripts\python.exe scripts/build_template_gallery.py --strict
.\.venv\Scripts\python.exe scripts/verify_template_gallery.py --decode
.\.venv\Scripts\python.exe scripts/build_homepage_showcase.py --write-readme
```

首页与目录显示实际四层数量，接入记录另计。最新 Demo 旁展示本次包版本与 QA；基线版本保留并明确标为历史登记。首页仅替换唯一生成标记区，其他正文和 A/B 区块保持。

GIF 按源 MP4 哈希和已有 GIF 哈希复用缓存，只在新增或源视频变化时重新生成该项；不会因增加一条接入记录而重渲所有旧 GIF。缓存仍会验证解码、时长和比例。没有 JPG 海报时目录直接展示可播放视频，不要求为登记补造图片。

新产物与说明完成后，按总 Skill 的长期授权审查并同步到私人 Git。完整原片、完整成片、源人像蒙版、个人包、Key 和客户敏感信息继续排除；不扩大为公开发布许可。监测发现新版只通知，不能因此替换已认可工程；新片有需要时另存新版本制作和记录。
