# VD44 客户流程与头像片尾

> 当前状态更新（2026-09-12）：原创作者已明确认可最后完整视频及HyperFrames/Remotion的做法，并要求作为后续默认。此前“风格待认可”记录为历史；本次不补写代理未执行的连续视听或人工同步。完整流程与顺序见总Skill的references/approved-workflow.md。


这里是现有 ai-cut 的素材扩展。Remotion 4.0.523 与 React 19.2.3 实际生成动画，主剪辑、字幕和声音仍在原 ChatCut 工程。没有用动画重新定义语义剪辑。

## 实际组成

- CustomerJourney：1920×1080、30fps、838帧；主时间轴[1148,1986)，插入速度1.0。四阶段起点0/241/452/707帧，体现新客户、未购买继续跟进、未回复继续跟进、回复并报名后登记。
- PresenterEnding：同尺寸、90帧；主时间轴[2955,3045)，真实用户肖像与3秒收尾。
- 两个composition均无声音；真人小窗、原声、字幕、BGM、SFX交由同一ChatCut主时间轴管理。主体1.1倍已经应用，禁止再次整体加速。

黄色/奶油大字、黑色阴影、图形对象和动作参考VD44。底部175px留给原生字幕；过程中的人物小窗也是原生单独图层。动画内部文字可在src/scenes修改，重新渲染导入。不是ChatCut内部可直接拆分的图层。

## 运行

在本目录 PowerShell 执行：

```powershell
.\run.ps1 -Action Install
.\run.ps1 -Action Check
.\run.ps1 -Action Preview
.\run.ps1 -Action Render -Composition CustomerJourney
.\run.ps1 -Action Render -Composition PresenterEnding
```

默认使用本机Node24与Chrome；其他机器可传NodePath、NpmCli、BrowserPath。Install使用锁文件npm ci并获取官方Noto Sans SC字体，保留public/OFL.txt。片尾还需public/presenter.jpg：只能从已授权原片选真人，不得生成假头像。Git忽略字体二进制和肖像；本次本机源码交付包包含所用文件。

Render默认新建带时间的输出文件，指定OutputPath时若已存在会拒绝覆盖。Check实际运行ESLint和TypeScript，不会把检查通过当成已渲染。预览与每次render都仍需实际查看画面。

## 已运行的验证

两个正式动画实际渲染、完整解码及关键帧查看完成，source-manifest.json记录各自哈希。27.933秒流程和3秒片尾已导入并通过ChatCut云端合成为101.5秒最终审阅稿。run.ps1的Check已退出0。

官方create-video初始化受codeload证书异常阻挡，转用同一官方template-empty仓库commit 9d03be1df2796a5f46eb26c747a106f21a11cefc；未关闭TLS。模板Rspack在本机无法找到bundle.js，改用官方Webpack配置后真实渲染成功。没有全局升级/替换Node。保留package-lock.json；不能自动追latest。

## 许可与边界

本次是用户指定的动画适配评估审阅稿。Remotion对公司使用有单独条件，商业使用前核对 https://www.remotion.dev/license 的资格或已有Company License；没有代购或自动发布。字体为SIL OFL，官方许可随工程。场景内客户、消息和计时是教学示意，参考片里的数字/客户不是本片证据。

用户风格已明确批准；代理完整连续观看、试听、人工200ms同步未完成；不声称复刻了精细抠像或人物背后大字。
