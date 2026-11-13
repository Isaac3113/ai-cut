# 2026-11-13：官方模板目录全量同步

本轮同步的是公开目录、版本、分类及演示入口，不是批量下载／运行原包，也没有升级既有成片。GitHub 清单、分类说明和 AI Cut 网页从同一登记表生成。

## 收录范围与数量

- 当前官方 GitHub 合集：100 个主条目、13 个预告。固定来源提交为 `e46dbc2ee2856dff2a8fe81b1c20bb46633cebc5`。
- 官网：39 个列表页、8 个分类页及公开 sitemap 已核对，886 个不同卡片；其中 100 个已发布、12 个行业预告、774 个待认领展示。112 个非待认领详情页均成功读取。
- GitHub 独有的 3D 书预告一并收录。另保留 1 个本轮暂缺的历史条目 pixel-ocean，标明暂缺，不推断已删除或仍是最新版。
- 合并后：101 个主条目（含上述 1 个历史保留）、787 个预告／待认领展示，合计 888 个官方及社区参考条目。这不是 888 个已接入的整片模板。
- 原有 70 个动画控件、55 个代码注册项、19 个真人效果分支及 11 条实际接入记录保留，不能重复相加为独立模板数。

## 分类怎样看

保留官网七个分类：口播视频、动画解说、产品宣传、视觉艺术、行业广告、生活记录、音乐短片；同时保留 Innovation 和待认领状态。当前行业／生活／音乐正式分类页为空，不代表要删掉相关预告。按表达用途另有真人口播、流程时间线、数据对比、行业应用等中文入口；原始分类和用途分类不能互相替代。

待认领展示保留官网署名与演示链接，不代表 MotionGit 或 AI Cut 已提供可调用的源码、授权或原包。缺少参数和版本时明确写未提供，不根据视频猜测。

## 调用状态怎样看

| 状态 | 可以做什么 |
| --- | --- |
| 仓库源码可调用 | 代码在本仓库；先准备依赖和自己的素材，再预览检查，不代表任意新电脑已验证 |
| 已接入案例 | 只按该案例的包版本、输入和已列明场景复用；新版单独核对 |
| 尚未接入 | 目录与官方 Demo 可浏览；先合法取得对应原包、核对合同并试做 |
| 已有控件演示 | 演示可看，使用时需要自己合法取得的对应包 |
| 样片效果待适配 | 已有特定实现，不能称为已通用化的 `.motion` |
| 官方预告／待认领 | 查看效果与来源；不提供直接调用承诺 |

每张卡分别说明 GitHub 公开合集版本、官网独立版本及已有案例验证版本。官网发行线与公开合集可能不同；旧 Demo 不因目录更新就改写为最新验证。

## 维护入口与顺序

1. 核对公开来源、所有分页、新分区、分类及稳定身份，准备完整的公开官网观察 JSON。当前数据保留在本机 `work/motiongit-monitor/source-audit-20261113/`，运行数据不进 Git。
2. 同步器使用固定提交的官方 catalog 与完整官网观察；`--check` 只报告，不改目录。给出 `--source-commit` 时核对固定提交原文，不能把任意本地 JSON 冒称该提交。
3. 从登记表重建机器目录、逐项七段说明、分类分页和网页；官方条目数量按来源 manifest 校验，不再锁死为旧 72 项。预告详细说明按分类分页，网页初次显示 24 项，再按需加载。
4. 重建 GitHub 首页，仅复用经过登记和哈希核对的现有 GIF；不重新生成媒体或下载原包。
5. 跑目录／状态／版本测试，核对所有来源 URL、详细说明链接、媒体身份、Git diff。只提交相关公开文件，排除 work、缓存、密钥和个人原包。
6. commit／push 后检查 Vercel 原项目 `ai-cut` 的生产部署提交；再比较 `https://aicut.agi-top.com` 的实际 DATA 与本次目录，并检查分类、调用状态筛选和代表 Demo。推送成功本身不能替代网页验收。

本次同步示例（路径中的工作观察文件用于本轮，不是永久最新数据）：

```powershell
.\.venv\Scripts\python.exe -B -X utf8 scripts/sync_motiongit_catalog.py --source-commit e46dbc2ee2856dff2a8fe81b1c20bb46633cebc5 --directory-file work/motiongit-monitor/source-audit-20261113/directory-enriched.json --check
.\.venv\Scripts\python.exe -B -X utf8 scripts/build_template_gallery.py --strict
.\.venv\Scripts\python.exe -B -X utf8 scripts/build_homepage_showcase.py --reuse-media-only --write-readme
.\.venv\Scripts\python.exe -B -X utf8 scripts/verify_template_gallery.py --report work/template-sync-20261113/gallery-verification.json
```

移除 `--check` 才会实际同步登记表；未来更新必须先重新获取观察数据与当前提交，不复制旧文件冒充最新。每周监测仍只通知，不自动提交、上线、下载或执行模板；需要同步时按用户授权执行上述流程。

## 来源与验证边界

[官方固定 catalog](https://github.com/motiontemplates/all/blob/e46dbc2ee2856dff2a8fe81b1c20bb46633cebc5/catalog.json) · [官网公开目录](https://motiongit.com/templates) · [Innovation](https://motiongit.com/templates?status=innovation) · [待认领展示](https://motiongit.com/templates?status=claim)

源内容仅作为资料。公开预览不转移版权；使用、下载与再分发按各条目的原许可处理。本轮没有付费、生成新视频、改旧包或重新验收全部模板；接入记录与既有 Demo 的实际检查范围保持原样。
