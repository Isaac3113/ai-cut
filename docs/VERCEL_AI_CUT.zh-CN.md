# AI Cut：把模板展厅放到自己的域名

正式地址：[AI Cut 模板展厅](https://aicut.agi-top.com)。2026-11-02已验证上线，公开源码入口为 https://github.com/Isaac3113/ai-cut 。本页保留操作教学，并单独记录实际部署与验证，避免把连接GitHub当作网站已发布。

## 当前已验证状态（2026-11-02）

- 用途：用户确认个人学习与免费交流，不用于业务获客或销售；使用Hobby，未开通付费套餐。
- Vercel Team：`Isaac Chong's projects`；项目：`ai-cut`；仓库：`Isaac3113/ai-cut`，按同日后续用户请求开放下载，无需逐个邀请。
- 生产部署：`dpl_7KNHHdXEmjJtuZAKA4PLUma8Cdp5`，状态`READY`，环境`production`，来源提交`3b34674974741c33bb6d170e78fefd151c8c855f`。
- 构建配置：Root Directory=`docs/template-gallery`，Preset=`Other`，Build/Install Command为空，Output Directory=`.`，不包含根目录以外文件。
- Namecheap CNAME：Host=`aicut`，Value=`a36ff3d4d2816e20.vercel-dns-017.com.`；由用户填写，Vercel回读`verified=true`、`misconfigured=false`。该值是本次配置记录，未来重建项目时重新读取Vercel要求。
- HTTPS首页200，线上HTML与该部署提交的Git文件逐字节一致；本机仅有CRLF/LF换行差异。312份本地MP4/JPG的HEAD状态与类型全部通过，4条官方代表预览HEAD通过。浏览器分类与本人横竖比例筛选通过；代表性本人横版和官网流程动画已播放至结束，竖版样本确认时间推进，样本无视频错误；不代表全部视频已连续看听验收。

以下步骤用于理解与维护现有项目，不需要重新创建第二个同名项目。

## 两边各负责什么

- Vercel：存放可访问的网站、连接GitHub、管理部署和自定义域名。
- Namecheap：管理 `agi-top.com` 的DNS，把 `aicut` 子域名指向Vercel。
- GitHub：公开代码与教学入口；网站托管、源码许可和剪辑工具账号分别管理。

`aicut` 是现有域名的子域名，不需要重新买一个域名。不要改根域名、Nameservers、现有邮件MX或其他业务的DNS记录。

## 第一步：先确定准备展示的文件

现有模板中心的静态目录是 `docs/template-gallery`：HTML、配套Demo视频和海报使用相对路径，不能只上传一个HTML。

本机 `/local-demo-manifest.json` 与 `/local-owner-media/` 来自Python服务，Vercel静态托管不会自动读取个人电脑原声素材；没有这些本机路由时页面回退已登记静音Demo。不要把整个工作Hub、原片、私人MotionGit包、密钥、客户资料或运行缓存放入部署范围。

现有精选预览已获本次公开展示授权；新增或替换Demo时仍核对采用范围和第三方许可。官网示例保留来源、许可及候选状态，不把全部预览写成已附送的可执行模板。当前GitHub源码也可直接下载；下载者的账号、运行环境及个人模板授权仍需自行准备。

## 第二步：在Vercel建立项目

1. 登录自己的Vercel，选择准备承载AI Cut的Team。
2. 进入 `Add New… → Project`。
3. 在Import Git Repository中找到 `Isaac3113/ai-cut`。看不到时，在官方GitHub连接设置中只给所需仓库访问权；由账号持有人完成授权。
4. 项目名称填 `ai-cut`。如果该Team已有同名项目，先检查是否就是本项目，不另建重复项目或覆盖其他项目。
5. Framework Preset选 `Other`。
6. Root Directory选 `docs/template-gallery`。
7. 这是现成静态目录，不需要安装Python、Node动画引擎或运行剪辑：Build Command留空并覆盖默认自动构建；Install Command设置为不执行依赖安装；Output Directory使用当前Root目录 `.`，以预览界面的实际选项为准。
8. 核对本次文件、访问范围、套餐及发布授权后执行 `Deploy`；本项目已完成首次部署，维护时复用现有项目。
9. 等待Ready，先打开Vercel生成的网址，检查分类、视频、海报、手机排版及来源链接。出现404或缺视频先修部署目录，不急着加DNS。

如果界面设置与本说明不同，把当前页面给AI助手看，按实际界面解释，不盲填其他项目的配置值。广告营销属商业用途，Vercel Hobby限个人非商业用途，应按自己的实际套餐处理；不要由助手自动购买或升级。

## 第三步：添加域名

项目页面进入 `Settings → Domains → Add Domain`，填写：

```text
aicut.agi-top.com
```

选择关联Production。Vercel会显示这个项目实际需要的DNS记录；这时看到 `Invalid Configuration` 并不等于网站失败，通常是DNS尚未填写或尚未传播。

## 第四步：在Namecheap填写Vercel给出的记录

进入 `agi-top.com → Advanced DNS → Host Records`。

通常子域名会使用CNAME，但具体Type、Value和必要的验证记录以本项目Vercel页面为准：

| Namecheap字段 | 填写内容 |
| --- | --- |
| Type | Vercel当前要求的类型，子域名通常为CNAME Record |
| Host | `aicut` |
| Value / Target | 完整复制本项目Vercel页面给出的目标值 |
| TTL | Automatic或平台默认 |

不要照抄网上或旧项目的固定CNAME值。若已有 `aicut` 记录，先核对其现用途，避免覆盖其他服务；Vercel另要求TXT时，按它显示的Host和Value新增对应记录。

## 第五步：回Vercel验证

保存Namecheap记录后，回到Vercel Domains等待或使用页面提供的重新检查功能。DNS传播与HTTPS证书就绪可能需要时间，不承诺固定分钟数。

最终确认：

- 域名配置显示有效，HTTPS正常。
- `https://aicut.agi-top.com`能打开AI Cut页面。
- 分类、本人Demo、官网示例和配套媒体可用，实际访问范围符合你的选择。
- GitHub公开状态与匿名访问通过；不把公开仓库误写成需要邀请，写入权限仍受GitHub管理。

只有完成这一步，才把正式域名放到学习分享或Notion教学页。本次用途已明确为个人非商业交流；将来若改为业务推广、获客或销售，先重新核对托管套餐与实际用途。

## 后续更新

现有项目已连接GitHub主线，本次推送后的生产部署已实际验证。后续更新仍使用同一份HTML：新增模板先更新真实登记与QA，检查公开展示范围，重建目录并核对配套文件，再commit/push；每次以Vercel实际部署状态、来源提交和正式网址检查确认是否上线。文档或仓库连接成功不能替代部署验收。

官网版本监测继续沿用每周安排，只监测通知，不因此下载或升级模板、修改旧工程或自动发布网站。需要扩展成自动更新线上展厅时，另按明确范围配置并验证，不能把通知任务写成已经接通发布流程。

## 官方资料

- [Vercel构建与静态目录](https://vercel.com/docs/builds/configure-a-build)
- [Vercel添加自定义域名](https://vercel.com/docs/domains/working-with-domains/add-a-domain)
- [Vercel商业用途说明](https://vercel.com/docs/limits/fair-use-guidelines)
- [GitHub仓库改名及旧地址重定向](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)
