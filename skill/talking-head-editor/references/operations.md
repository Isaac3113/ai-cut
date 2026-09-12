# 实际命令

当前用户最新要求见 [用户剪辑偏好](user-preferences.md)。0.1.3已接入单比例、1.1倍速和逐步流程。plan中设置output_formats=["source"]（默认）或明确的["landscape","portrait"]；style.playback_speed控制统一时间轴，原版无该字段时保持1倍速。用户要求重剪完整内容可用draft模式输出完整1080p审阅版；不等于final风格批准。

PowerShell 使用源码项目的 `& 'C:\Codex Workspace\AI-Talking-Head-Editor\.venv\Scripts\python.exe' -m talking_head_editor.cli <命令>`；也可用任意 Python 执行本 Skill 的 `scripts/run.py`。有空格的路径加引号，参数不拼成 shell 指令。

```
doctor
init --job <新工程目录> --source <真人原片> [--script <文稿txt或md>]
status --job <工程>
source-qa --job <工程>
inspect --job <工程> [--times 0.1,15,30]
transcribe --job <工程> [--hotwords <每行一项txt>] [--device auto]
import-transcript --job <工程> --file <已核实字词时间json> --provenance user_verified
asset-index --job <工程> --folder <用户指定素材目录>
asset-add --job <工程> --file <素材> [--metadata <来源许可json>]
inspect --job <工程> --asset-id <素材id> [--times 1,2,3]
asset-review --job <工程> --id <素材id> --description <实际内容> --evidence <查看或听审位置>
pexels-search --job <工程> --query <英文检索词> --type video --limit 6
pexels-download --job <工程> --candidate <选中候选json>
asset-approve-paid --job <工程> --id <素材id> --user-evidence <真实确认记录>
plan-export --job <工程> --out <新方案json>
plan-apply --job <工程> --file <方案json>
render --job <工程> --mode preview
render --job <工程> --mode draft
profile-approve --job <工程> --name default --user-evidence <用户实际反馈>
profile-use --job <工程> --name default
render --job <工程> --mode final
qa --job <工程>
review --job <工程> --file <完成证据的review-template副本>
package --job <工程> --out <工程外新zip> [--draft]
restore --job <工程> --revision <旧版本> --expected <当前版本>
unlock --job <工程> [--asr]
```

首次模型下载较大；通过 `job/logs/transcribe.log` 判断进展。CUDA 失败说明原因，不自动删环境重装。`doctor` 只证明依赖可见，真正识别要以实际 `transcribe` 成功为准。下载模型不上传用户原片；Codex 会话对文字及被查看画面的理解依赖当前服务。

所有内容改动使 revision 增加，计划应用要求 base_revision 对得上。先登记与审阅素材，再导出计划，避免使用旧版本号。待确认的素材可保存到 `research/paid-candidates.json`，不加入可渲染方案。付款动作不由本程序执行，付费审批命令只是记录已发生的用户批准。

中断后先 status。已有正常转写不重做；渲染缓存以内容哈希校验，未变片段直接复用。上次渲染失败需读 logs 再 `render ... --retry`，同一指纹只准一次重试。变更程序修复渲染行为必须更新引擎版本使旧缓存失效。遗留 `.edit.lock` 只有 PID 确认已退出时 `unlock` 才删除该单一文件。

无源视频时停在输入阶段；缺素材时保留真人并用有依据的轻推近/重点或对象动作补足节奏，不用连续字卡替代画面。没有 Pexels key 可走网页候选+asset-add；不要读取或输出 `.env`。自带 `--test-fixture` 仅限开发校准，不允许借此跳过真实样片确认。

## 本轮0.1.6：按完整规则重剪

完整新剪/重剪先读[总规则](master-playbook.md)，参数与现有字段对照[data-contract](data-contract.md)。现有ASR有效就复用；新视觉和声音仍经plan-export、plan-apply进入同一revision，不直接改project.json。

1. 用现有素材和真实原话安排B-roll、人物轻推近、关键词、流程动作，记录已查看的内部motion_times。设置visual_rhythm.enforce=true，按最终1.1倍速后的时间检查全片≤5秒间隔；程序通过后仍须看实际变化。
2. 把punch/keyword写入visual_effects，把少量重点tap/pop/swipe写入sound_effects。SFX增益≤0.05（预峰值-6dBFS后再衰减），BGM显式保留music_gain_db=-35.020599913279625，不能调低真人或调大音乐代替音效。
3. 从真实原片选本人头像帧，实际看裁切，生成并登记新的片尾视频；保留源帧、时间点、crop和衍生证据。当前ending模块是16:9本条客户流程模板，其他主题不能原样复用其固定文字/音乐署名，也没有新增独立CLI子命令。
4. 计划ending选择已登记的owned视频asset，显式duration=3最终秒及实际source_start，检查完整结尾与署名。preview不包含片尾，检查完整收尾用draft；没有真实听审不把sfx_review填成已听。
5. 渲染draft后读取当前render目录的visual-rhythm.json、sfx-report.json、sfx-only.wav及finished-mix.wav，检查事件、音效增益、人声基底、BGM尾轨和实际成片。不得只看65项旧阶段测试就说新片合格。
6. 使用video-use本地包装检查疑点与接缝；只参考Remotion帧驱动规则，本轮实际FFmpeg合成，未装Remotion运行时。所有素材/文字须按本片查看，先完成可自主完成的工作再交付待听审点。

### 中断和已定位失败

本轮0.1.5首次真实全片在states片段出现FFmpeg7.1退出3221225509及CABAC/qscale错误；单独源/素材解码和源单/双线程检查通过，未证明源文件损坏，根因未确认。记录属于该次失败现场，不是其他视频必然故障的结论。

接手先status与失败render/log，保留旧产物；当前0.1.6恢复结果以本工程最新记录为准。主线选择单线程解码/滤镜作为保守策略，不等于根因已查明。不要在故障对比或真实重试期间并行运行视频压力测试；不要为重复失败循环改版本或重试。

只修已定位问题，同一未变指纹最多一次显式--retry。不能用跳过错误、fixture开关或伪造review继续。若恢复尚未成功，交代当前阻碍与保留路径，绝不称本轮已完成。

### 证据按版本记录

0.1.5阶段：65项单测及scripts/smoke_motion.py双1080p技术校准通过，日志为work/motion-final-unit-results.txt和work/motion-final-smoke-results.txt。0.1.6：带BGM的片尾分支单独复测通过，正文+SFX逐采样误差0，证据在work/motion-bgm-tail-fixture-1789126980393602000/verification.json。后者不是0.1.6全套回归或用户视频验收；新的实际验证结果另记，旧日志不覆盖。

### 本次真实恢复与片尾衔接状态

0.1.6真实revision42已恢复并通过完整技术QA；111帧复看后，revision43仅修正NoReply重点字的实心深色和提前退场。随后video-use的8帧衔接检查发现89.3秒头像素材淡出、短暂露回真人再回头像；0.1.7修复连续片尾后重编码result片段仍两次崩溃；0.1.8核验不变片段的缓存后复用12段完成新版，整片技术QA及片尾8帧复核通过。听审和人工200ms仍待验证。

当前交付为完整draft审阅版，不能把技术通过说成全部人工验收。重点查看头像进入、正文/片尾接点和实际尾部淡出；5秒计划检查必须使用0.1.7连续边界逻辑，不能把同一张头像的无变化接点充当新动作。


## 0.2.2 质量优先操作补充
使用现有.venv：`python -m talking_head_editor.cli source-profile --job JOB` → `render --mode rough` → `workflow-review --file packet.json` → `workflow-status` → `render --mode draft` → `qa`。第一次/重剪视觉尚未确认仍交付完整draft；final另外要求真实风格反馈、粗剪/画面锁定与源条件就绪。

packet由当前project生成plan_fingerprint（workflow.plan_fingerprint），包含brief、每段editorial_units、take_comparisons、uncertainties、每个overlay及background_music的shots，候选必须注明owned/free/paid、观察方式、采用理由、来源/许可URL及选中资产SHA。evidence_files给JOB内部真实文件路径，工具计算SHA；变更后旧packet失效。rough_watch/picture_lock没有实际连续审查就写unverified，不能为过门禁虚填pass。

恢复：`portable.restore_package(zip_path, new_empty_path)`验证解压文件；再调用`portable.verify_restored_clip(original_job,new_job,"entry")`实际重渲染同一片段并比对视频/字幕/声音。需要本机可用执行器和授权字体；包不含模型、字体二进制或密钥。


阶段性检查用`review-progress --job JOB --file review.json`保存，不改变delivery。正式review仍须完整证据。导出后检查ASS/SRT与烧录画面一致；失效粗剪不随包假装有效。


## 0.2.3 音量修正与手动调节

先单独处理原声到目标响度，冻结voice.wav及其哈希，再将整平后的BGM按music_gain_db和人声侧链压低后加入，最后叠加SFX。禁止在音乐已加入后再次loudnorm整个混音，否则原片人声过小时会把音乐同时提高。amix明确normalize=0；最终-0.6dB编码余量仍透明作用于全混音。音乐调小一半的回归必须证明人声PCM缓存相同，不能只看参数。不要将“5%参数”称作最终主观响度。

用户要手动调节时执行`audio-controls --job JOB --out NEW_FOLDER`，提供仅含画面和人声的MP4、从0秒对齐的背景音乐及音效WAV。用户在剪映等软件调各轨音量；100%指已处理后的轨道基准，设50%可继续减半。不要对这些轻声轨再次开启自动响度，不要叠回旧混合MP4，不要重复加入纯人声WAV。Codex右侧仍只有文件/视频预览，未提供原生NLE时间线。局部声音修改后核对压缩视频包哈希和字幕，不重剪画面。

本片0.2.2原声很轻，混合后loudnorm曾整体提高约22–25dB，已经由真实缓存测量确认。0.2.3改为先原声、后音乐；属于明确的人声处理链修正，不宣称新旧人声PCM完全一致。以后只调音乐不改变这个新的人声基线。完整试听、手机听感仍须真实执行，不能凭测量代替。
