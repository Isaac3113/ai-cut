"""Build compact Chinese demos from the already-rendered local master.

No source/Root/vendor edits and no new Remotion render. All timing is derived from
Showcase.tsx's actual sourceTime decision, never the historical effect filenames.

This is a local reproduction helper, not a portable source-only renderer. It needs
Python + Pillow, the ignored AIVD 9 master/props/scene manifest and Noto font below,
the repo-local Windows FFmpeg/ffprobe executables, and Windows Microsoft YaHei Bold.
Those media/runtime/font dependencies are not supplied by cloning this script.
The checked-in compact demos can be viewed independently. Reproduction on another
computer has not been verified; restore authorized inputs and verify paths first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
WORK = Path(__file__).parent / "presenter-work"
JOB = ROOT / "work/videos/AIVD 9 - 自动剪辑特效，免费送给你/04_剪辑工程"
MASTER = JOB / "visual-r3/visual-master-silent.mp4"
PROPS = JOB / "showcase-props.json"
SOURCE_MANIFEST = JOB / "visual-r3/scenes/scene-manifest.json"
SHOWCASE = ROOT / "extensions/remotion-vd44/src/template-library/talking-head-effects/Showcase.tsx"
DEST = ROOT / "docs/template-gallery/demos/presenter"
CATALOG = ROOT / "templates/presenter-effects.json"
FFMPEG = ROOT / ".runtime/ffmpeg/bin/ffmpeg.exe"
FFPROBE = ROOT / ".runtime/ffmpeg/bin/ffprobe.exe"
FONT = JOB / "render-assets/NotoSansSC.ttf"
DEMO_FONT = Path("C:/Windows/Fonts/msyhbd.ttc")
FPS = 30
LIMIT = 2_000_000

# Actual visible behavior, not a claim of a pixel-identical reference recreation.
META = [
    (1, "条形增长", "数据与图表", "三条横向示意条按顺序增长，叠在口播画面上。", "比较选项或说明阶段进展", "示意长度不能当作真实业绩数据", "口播视频、真实标签与数值"),
    (2, "玻璃标签", "文字与标题", "半透明圆角玻璃标签进入画面，突出一个短标题。", "强调一句关键词或术语", "避免长段落和低对比背景", "口播视频、短标题、品牌颜色"),
    (3, "冲击缩放", "镜头与转场", "同一镜头快速推近、模糊并回拉，配合扩散边框。", "段落转折或短促强调", "不是两个场景间的真正穿越；避免频繁使用", "口播视频、推近焦点和切点"),
    (4, "剪纸描边", "人物与背景", "动态抠像人物加白色纸边和阴影，置于纸张纹理背景。", "人物介绍或轻松创意片段", "抠像边缘抖动时不宜直接使用", "同步人物透明视频、纸张背景"),
    (5, "照片墙", "人物与背景", "多张照片组成错位移动墙，动态人物位于前景。", "展示素材集合或个人经历", "避免无授权照片及背景信息过密", "授权照片、同步人物透明视频"),
    (6, "拉远揭幕", "镜头与转场", "口播画面逐步缩小，显露带标题栏的悬浮窗口。", "从讲述过渡到内容预览", "小窗口内的重要文字要另行放大", "口播视频、窗口标题、背景颜色"),
    (7, "界面窗框", "界面与设备", "口播被放入带标题栏的悬浮窗框，形成界面容器效果。", "介绍视频内容或界面场景", "此演示没有真实软件操作与点击", "口播视频、窗口标题、背景颜色"),
    (8, "杂志封面", "人物与背景", "人物与封面标题分层，形成杂志封面式口播包装。", "人物专题或章节开场", "避免把装饰标题当作真实媒体背书", "口播视频、同步人物透明视频、封面文字"),
    (9, "抠像换景", "人物与背景", "已抠像的人物合成到原创蓝色空间背景。", "替换环境或建立主题场景", "演示使用人物透明层，不代表原片拍摄了绿幕", "同步人物透明视频、替换背景"),
    (10, "打勾清单", "列表与步骤", "清单项依次打勾，顶部进度随演示推进。", "步骤总结或完成项确认", "不能把演示勾选当作真实任务完成", "口播视频、清单文字、逐项时间"),
    (11, "视频镂空字", "文字与标题", "真人视频透过大型中文字显示，并保留圆形人物小窗。", "章节主题或短词视觉强调", "长句和细笔画会降低视频辨识度", "口播视频、粗体中文短词、人物小窗"),
    (12, "手绘涂鸦", "装饰与强调", "线条、星形与箭头逐步绘出，围绕人物形成手绘强调。", "提醒重点或营造轻松节奏", "避免箭头指向错误对象或遮住字幕", "口播视频、短标题、强调位置"),
    (13, "标题墙", "文字与标题", "重复大字在人物后方交错移动，形成动态文字墙。", "强化主题词或品牌关键词", "避免长句与高密度信息同时出现", "同步人物透明视频、短主题词"),
    (14, "手机画面", "界面与设备", "口播装入带旋转动作的手机轮廓与播放信息层。", "展示竖屏内容或手机场景", "这是设备示意，不是已完成真实手机实操", "竖屏视频、设备内标题与信息"),
    (15, "人物破框", "人物与背景", "同源画面在倾斜窗口内显示，透明人物延伸到窗口外。", "人物登场或突出主体", "前后两层必须同步，避免双重人物边缘", "同步口播视频与人物透明视频、窗口位置"),
    (16, "环绕文字", "装饰与强调", "三张中文词卡沿椭圆轨迹环绕人物，并表现前后遮挡。", "展示围绕核心人物的几个关键词", "避免词卡盖脸或把并列关系暗示为先后步骤", "同步人物透明视频、三个短关键词"),
    (17, "数字推近", "镜头与转场", "围绕人物焦点逐步放大原画面，叠加构图框。", "强调一句原声重点", "低清晰度素材不宜过度放大", "口播视频、焦点坐标、目标倍率"),
    (18, "收据列表", "列表与步骤", "纸张从打印口逐步出现，列出三项内容并打勾。", "总结清单或展示内容目录", "示意收据不能冒充真实交易凭据", "口播视频、列表文字、出现时间"),
    (19, "贴纸轮播", "装饰与强调", "五枚原创图标贴纸沿椭圆轨道轮转，并改变前后大小。", "串联几个创作主题或轻量装饰", "避免遮挡关键内容与连续无意义转动", "口播视频、授权贴纸或原创图标"),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args, log=None):
    result = subprocess.run([str(x) for x in args], capture_output=True, check=False)
    if log:
        Path(log).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace")[-3000:])
    return result.stdout


def mappings():
    data = json.loads(PROPS.read_text(encoding="utf-8-sig"))
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8-sig"))
    assert sha(MASTER) == manifest["master_sha256"], "Master does not match frozen scene manifest"
    assert sha(PROPS) == manifest["props_sha256"], "Props do not match frozen scene manifest"
    code = SHOWCASE.read_text(encoding="utf-8")
    assert "clip.sourceStart+frame/30*clip.playbackRate" in code
    assert "clip.kind===9&&sourceTime>=21.75?10:clip.kind" in code
    groups = {}
    for clip in data["clips"]:
        for local in range(clip["durationInFrames"]):
            kind = 10 if clip["kind"] == 9 and clip["sourceStart"] + local / 30 * clip["playbackRate"] >= 21.75 else clip["kind"]
            groups.setdefault(kind, []).append(clip["fromFrame"] + local)
    assert set(groups) == set(range(1, 21))
    result = []
    for kind in range(1, 20):
        frames = groups[kind]
        assert frames == list(range(frames[0], frames[-1] + 1))
        result.append({"kind": kind, "start_frame": frames[0], "end_frame_exclusive": frames[-1] + 1,
                       "frames": len(frames), "duration_seconds": len(frames) / FPS})
    assert result[8]["end_frame_exclusive"] == 333 and result[9]["start_frame"] == 333
    return result


def sheet(frames, labels, target, columns=5):
    thumbw, thumbh, labelh = 216, 384, 52
    rows = (len(frames) + columns - 1) // columns
    out = Image.new("RGB", (columns * thumbw, rows * (thumbh + labelh)), "#10232c")
    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype(str(FONT), 20)
    for i, (frame, label) in enumerate(zip(frames, labels)):
        x, y = i % columns * thumbw, i // columns * (thumbh + labelh)
        im = Image.open(frame).convert("RGB").resize((thumbw, thumbh))
        out.paste(im, (x, y))
        draw.text((x + 8, y + thumbh + 8), label, font=font, fill="white")
    out.save(target)


def inspect_source(mapping):
    folder = WORK / "source-frames"
    folder.mkdir(parents=True, exist_ok=True)
    chosen = [x["start_frame"] + x["frames"] // 2 for x in mapping]
    select = "+".join(f"eq(n\\,{n})" for n in chosen)
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", MASTER,
         "-vf", f"select='{select}',scale=432:768", "-fps_mode", "passthrough", "-q:v", "2", folder / "%02d.jpg"], WORK / "source-extraction.log")
    sheet([folder / f"{i:02d}.jpg" for i in range(1, 20)],
          [f"{k:02d} {label}" for k, label, *_ in META], WORK / "presenter-source-contact.jpg")


def text_filter(name, text, x, y, size, color="white"):
    (WORK / f"{name}.txt").write_text(text, encoding="utf-8")
    return f"drawtext=fontfile=font.ttf:textfile={name}.txt:fontsize={size}:fontcolor={color}:x={x}:y={y}"


def rectangle(x, y, w, h, color):
    return f"drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t=fill"


def chinese_layer(kind, label):
    # Coordinates target the frozen 1080x1920 master, before scaling. Baked labels
    # are covered by an independent demo-only design layer; effect timing stays intact.
    f = [rectangle(0, 1570, 1080, 350, "0x153340"),
         text_filter(f"{kind:02d}-title", label, "(w-text_w)/2", 1622, 78),
         text_filter(f"{kind:02d}-note", "本人素材 · 效果演示", "(w-text_w)/2", 1740, 31, "0x9BD9E6")]
    if kind == 4:
        f += [rectangle(60, 100, 365, 245, "0xF2F8FA"), text_filter("04-paper", "剪纸", 111, 171, 74, "0x153340")]
    if kind == 8:
        f += [rectangle(0, 65, 1080, 245, "0x153340"), text_filter("08-kicker", "动态人物专刊", 70, 85, 30, "0x47B4D0"),
              text_filter("08-magazine", "剪辑特效", 70, 135, 145),
              rectangle(810, 1060, 115, 300, "0x153340"), text_filter("08-side", "创作", 815, 1140, 36), text_filter("08-side2", "复用", 815, 1200, 36)]
    if kind == 17:
        f += [rectangle(190, 300, 300, 75, "0x153340"), text_filter("17-zoom", "数字推近", 205, 320, 36)]
    return f


def build_one(item):
    kind = item["kind"]
    label = META[kind - 1][1]
    dest = DEST / f"presenter-effect-{kind:02d}.mp4"
    filters = [f"trim=start_frame={item['start_frame']}:end_frame={item['end_frame_exclusive']}", "setpts=PTS-STARTPTS",
               *chinese_layer(kind, label)]
    tail = ["scale=540:960:flags=lanczos", "setsar=1", "format=yuv420p"]
    inputs = ["-i", MASTER]
    filter_args = ["-vf", ",".join(filters + tail)]
    if kind == 18:
        patch = Image.new("RGBA", (420, 50), "#F2F8FA")
        draw = ImageDraw.Draw(patch)
        font = ImageFont.truetype(str(DEMO_FONT), 22)
        caption = "效果目录 · 可复用"
        draw.text(((420 - draw.textlength(caption, font=font)) / 2, 8), caption, font=font, fill="#153340")
        patch.save(WORK / "18-footer.png")
        inputs += ["-loop", "1", "-framerate", FPS, "-i", WORK / "18-footer.png"]
        graph = (f"[0:v]{','.join(filters)}[base];"
                 "[1:v]format=rgba,fade=t=out:st=0.966666667:d=0.133333333:alpha=1[patch];"
                 f"[base][patch]overlay=x=330:y=1410:enable='gte(n,15)':shortest=1,{','.join(tail)}[out]")
        filter_args = ["-filter_complex", graph, "-map", "[out]"]
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *inputs,
         *filter_args, "-an", "-r", FPS, "-frames:v", item["frames"], "-c:v", "libx264", "-preset", "medium", "-crf", "24",
         "-threads", "2", "-movflags", "+faststart", "-map_metadata", "-1", dest], WORK / f"{kind:02d}-encode.log")
    probe = json.loads(run([FFPROBE, "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", dest]))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert len(probe["streams"]) == 1, "Demo must contain only silent video"
    assert int(video["nb_read_frames"]) == item["frames"]
    assert (video["width"], video["height"], video["avg_frame_rate"]) == (540, 960, "30/1")
    assert dest.stat().st_size < LIMIT
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-xerror", "-i", dest, "-f", "null", "-"], WORK / f"{kind:02d}-decode.log")
    sample_frames = sorted(set([0, item["frames"] // 2, item["frames"] - 1]))
    samples = []
    for j, frame in enumerate(sample_frames):
        output = WORK / "final-frames" / f"{kind:02d}-{j}.jpg"
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", dest, "-vf", f"select=eq(n\\,{frame})", "-frames:v", 1, "-q:v", 2, output])
        samples.append(str(output))
    return {**item, "path": str(dest.relative_to(ROOT)), "sha256": sha(dest), "bytes": dest.stat().st_size,
            "width": 540, "height": 960, "fps": 30, "decoded_frames": int(video["nb_read_frames"]),
            "full_decode": "passed", "audio_streams": 0, "contact_frames": samples,
            "demo_only_chinese_layer": True, "new_remotion_render": False}


def build(mapping):
    DEST.mkdir(parents=True, exist_ok=True)
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    (WORK / "final-frames").mkdir(exist_ok=True)
    shutil.copyfile(DEMO_FONT, WORK / "font.ttf")
    # Relative drawtext text/font paths avoid platform filter escaping hazards.
    import os
    os.chdir(WORK)
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(build_one, mapping))
    for page, start in enumerate(range(0, 19, 7), 1):
        batch = records[start:start + 7]
        frames = [Path(p) for record in batch for p in record["contact_frames"]]
        labels = [f"{record['kind']:02d} {META[record['kind']-1][1]} {part}"
                  for record in batch for part in ("开始", "中段", "结束")]
        sheet(frames, labels, WORK / f"presenter-final-contact-{page}.jpg", columns=3)
    entries = []
    for record, meta in zip(records, META):
        kind, label, category, description, use, avoid, inputs = meta
        entries.append({"id": f"presenter-effect-{kind:02d}", "label_zh": label, "layer": "effect", "category_zh": category,
                        "description_zh": description, "uses_zh": [use], "avoid_zh": [avoid], "inputs_zh": inputs.split("、"),
                        "version": "1.0.0", "source_url": "https://github.com/Isaac3113/ai-cut/tree/main/extensions/remotion-vd44/src/template-library/talking-head-effects",
                        "source_id": "talking-head-effects", "license": "MIT（原创代码）；演示肖像仅按本人本次授权展示，非素材再分发授权；Remotion 引擎另有许可",
                        "availability": "available", "validation": {"state": "technical_verified_visual_pending", "scope": "已核对实际效果编号及母版帧区间，完整解码，检查尺寸、帧数和文件大小；起中末联系表待实际审看。"},
                        "demos": [{"kind": "own", "path": f"demos/presenter/presenter-effect-{kind:02d}.mp4", "description_zh": "本人素材中文无声演示，来自已渲染母版的对应效果片段。", "sha256": record["sha256"], "bytes": record["bytes"]}],
                        "ratio": "9:16", "base_composition_id": "TalkingHeadShowcase", "effect_kind": kind})
    CATALOG.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = {"schema_version": 1, "source_master_sha256": sha(MASTER), "source_props_sha256": sha(PROPS),
                "showcase_sha256": sha(SHOWCASE), "executor": "FFmpeg extraction, Chinese demo-only overlays and H.264 encoding",
                "source_total_frames": 828, "included_kinds": list(range(1, 20)), "excluded_kind": 20,
                "kind_9_to_10_split": {"local_frame": 46, "master_frame": 333, "preceding_source_time": 21.73, "first_checklist_source_time": 21.77},
                "size_limit_bytes": LIMIT, "total_bytes": sum(r["bytes"] for r in records), "max_bytes": max(r["bytes"] for r in records),
                "contact_sheets_viewed": False, "records": records}
    (WORK / "presenter-verification.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(records), "max_bytes": evidence["max_bytes"], "total_bytes": evidence["total_bytes"], "catalog": str(CATALOG), "contact_sheets_viewed": False}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("inspect", "build", "confirm-view"))
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    mapping = mappings()
    (WORK / "presenter-frame-map.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.action == "inspect":
        inspect_source(mapping)
        print(WORK / "presenter-source-contact.jpg")
    elif args.action == "build":
        build(mapping)
    else:
        evidence_file = WORK / "presenter-verification.json"
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
        for record in evidence["records"]:
            assert sha(ROOT / record["path"]) == record["sha256"]
        evidence["contact_sheets_viewed"] = True
        evidence["visual_review_scope"] = "Codex实际查看三张联系表，覆盖19条演示的起点、中段和结束帧；不是逐帧连续观看。"
        evidence_file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        for entry in catalog["entries"]:
            entry["validation"] = {"state": "verified", "scope": "已核对实际效果编号及母版帧区间，完整解码，检查尺寸、帧数、文件大小，并实际审看起中末联系表；无新音频，不代表逐帧连续观看或完整参考复刻。"}
        CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Recorded actual contact-sheet review after verifying all current output hashes.")
