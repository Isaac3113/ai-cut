"""Parameterised, file-only adapter for a new native Jianying staging project.

No UI controller, live-draft registration, downloads, install or rendering.
Pinned upstream core generates segments; the user's empty native template owns
the surrounding schema. Semantic choices remain in the existing project plan;
this adapter only maps that plan and the verified render's single timebase.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.machinery
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import types
import wave

UPSTREAM_COMMIT = "32c56928ded4f9e2c2b80e099dc7abb793d2c30b"
FORBIDDEN_MODULES = ("uiautomation", "pyJianYingDraft.jianying_controller", "pyJianYingDraft.draft_folder")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def matches_git_blob(data, expected):
    def blob(value):
        return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()
    if blob(data) == expected:
        return True
    # Git's Windows checkout may only have converted LF to CRLF. No other
    # whitespace, JSON reformatting or source transformation is accepted.
    return b"\r\n" in data and blob(data.replace(b"\r\n", b"\n")) == expected


def write_new_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def us(seconds):
    return round(float(seconds) * 1_000_000)


def verified_media(root, record):
    root = Path(root).resolve()
    path = (root / record["path"]).resolve(strict=True)
    if not path.is_relative_to(root) or file_sha256(path) != record["sha256"]:
        raise ValueError(f"Media hash/path mismatch: {path}")
    return path


def install_file_only_guard(output_root, ffprobe):
    output_root, ffprobe = Path(output_root).resolve(), Path(ffprobe).resolve(strict=True)
    sys.dont_write_bytecode = True
    os.environ["PATH"] = str(ffprobe.parent) + os.pathsep + os.environ.get("PATH", "")

    def audit(event, args):
        if event == "import" and any(str(args[0]).startswith(n) for n in FORBIDDEN_MODULES):
            raise RuntimeError("UI/DraftFolder imports are forbidden")
        if (event.startswith("socket.") and event != "socket.gethostname") or event in ("os.remove", "os.rmdir", "os.system"):
            raise RuntimeError(f"Forbidden adapter operation: {event}")
        if event == "subprocess.Popen":
            requested = args[0]
            if requested is None:
                command = args[1]
                requested = command.split(" ", 1)[0] if isinstance(command, str) else command[0]
                if requested not in ("ffprobe", "ffprobe.exe"):
                    raise RuntimeError("Only FFprobe may execute")
            resolved = Path(shutil.which(str(requested)) or str(requested)).resolve()
            if resolved != ffprobe:
                raise RuntimeError("Only the supplied FFprobe may execute")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            mode, flags = args[1:3]
            writing = isinstance(mode, str) and any(c in mode for c in "wax+")
            writing |= isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            if writing and not Path(os.fsdecode(args[0])).resolve().is_relative_to(output_root):
                raise RuntimeError("Write outside the selected staging root")
        if event in ("os.mkdir", "os.rename"):
            for target in (args[:2] if event == "os.rename" else args[:1]):
                if not Path(os.fsdecode(target)).resolve().is_relative_to(output_root):
                    raise RuntimeError("Directory mutation outside staging")

    sys.addaudithook(audit)


def load_pinned_core(vendor_root, vendor_lock):
    vendor_root = Path(vendor_root).resolve(strict=True)
    lock = read_json(vendor_lock)
    if lock["commit"] != UPSTREAM_COMMIT:
        raise ValueError("Unreviewed upstream commit")
    prefix = "scripts/vendor/pyJianYingDraft/"
    for entry in lock["files"]:
        if not entry["upstream_path"].startswith(prefix):
            raise ValueError("Invalid vendor lock entry")
        path = (vendor_root / entry["upstream_path"][len(prefix):]).resolve(strict=True)
        if not path.is_relative_to(vendor_root) or not matches_git_blob(path.read_bytes(), entry["git_blob_sha1"]):
            raise ValueError(f"Pinned source changed: {path}")
    package_name = "pyJianYingDraft"
    if package_name in sys.modules:
        raise RuntimeError("Use a fresh process for pinned core loading")
    package = types.ModuleType(package_name)
    package.__package__ = package_name
    package.__path__ = [str(vendor_root)]
    package.__spec__ = importlib.machinery.ModuleSpec(package_name, loader=None, is_package=True)
    sys.modules[package_name] = package
    names = {
        "script_file": ["ScriptFile"], "local_materials": ["VideoMaterial", "AudioMaterial"],
        "video_segment": ["VideoSegment"], "audio_segment": ["AudioSegment"],
        "text_segment": ["TextSegment", "TextStyle", "TextBorder"],
        "segment": ["ClipSettings"], "time_util": ["Timerange"], "track": ["TrackType"],
        "keyframe": ["KeyframeProperty"],
    }
    exports = {}
    for module, members in names.items():
        loaded = importlib.import_module(f"{package_name}.{module}")
        exports.update({name: getattr(loaded, name) for name in members})
    return types.SimpleNamespace(**exports)


def new_script(api, width, height, fps):
    original = platform.system
    platform.system = lambda: {"win32": "Windows", "darwin": "Darwin"}.get(sys.platform, "Linux")
    try:
        return api.ScriptFile(width, height, fps, True)
    finally:
        platform.system = original


def frame_mapping(clips, fps):
    result, frame = [], 0
    for clip in clips:
        start = round(frame / fps * 1e6)
        end = round((frame + clip["frames"]) / fps * 1e6)
        if abs(start / 1e6 - clip["output_start"]) > 1e-6:
            raise ValueError("Compiled clip start does not match the shared frame clock")
        rate = float(clip["playback_speed"])
        source_start = us(clip["start"])
        source_duration = round((end - start) * rate)
        extension = source_start + source_duration - us(clip["end"])
        if not -2 <= extension < math.ceil(1e6 / fps * rate) + 2:
            raise ValueError("Visual padding exceeds one output frame")
        result.append({**clip, "target_start_us": start, "target_duration_us": end - start,
                       "source_start_us": source_start, "source_duration_us": source_duration,
                       "visual_extension_us": extension})
        frame += clip["frames"]
    return result


def read_srt(path):
    result = []
    def timestamp(value):
        h, m, s, ms = map(int, re.split("[:,]", value))
        return ((h * 60 + m) * 60 + s) * 1_000_000 + ms * 1000
    for block in re.split(r"\r?\n\s*\r?\n", Path(path).read_text(encoding="utf-8-sig").strip()):
        lines = block.splitlines()
        match = re.fullmatch(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", lines[1]) if len(lines) >= 3 else None
        if not match:
            raise ValueError("Malformed SRT")
        start, end = map(timestamp, match.groups())
        if end <= start or (result and start < result[-1]["end"]):
            raise ValueError("Invalid/overlapping subtitle timing")
        result.append({"start": start, "end": end, "text": "\n".join(lines[2:])})
    return result


def themed_captions(cues, dark_ranges):
    result = []
    for index, cue in enumerate(cues):
        edges = {cue["start"], cue["end"]}
        for a, b in dark_ranges:
            edges.update(x for x in (a, b) if cue["start"] < x < cue["end"])
        ordered = sorted(edges)
        for start, end in zip(ordered, ordered[1:]):
            dark = any(a <= (start + end) / 2 < b for a, b in dark_ranges)
            result.append({**cue, "start": start, "end": end, "theme": "dark" if dark else "light", "original_cue_index": index})
    return result


def rgb(color):
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", color):
        raise ValueError("Invalid RGB color")
    return tuple(int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))


def text_segment(api, script, track, text, start, end, *, pixels, color, bold=False, x=.5, y=.89, outline=2):
    segment = api.TextSegment(text, api.Timerange(start, end - start),
        style=api.TextStyle(size=pixels * 7.5 / 52, color=rgb(color), bold=bold,
                            align=1, auto_wrapping=True, max_line_width=.84),
        border=api.TextBorder(color=(0, 0, 0) if color != "#172B3A" else (1, 1, 1),
                              width=max(0, outline) * 5) if outline else None,
        clip_settings=api.ClipSettings(transform_x=2 * x - 1, transform_y=1 - 2 * y))
    script.add_segment(segment, track)
    # Upstream omits this inherited TextSegment reference from ScriptMaterial.
    script.materials.speeds.append(segment.speed)
    return segment


def punch_points(effects, speed, duration_us, *, clip_offset_us=0, layers=("presenter", "scene")):
    groups = [[e for e in effects if e.get("target", "presenter") == layer] for layer in layers]
    if not any(groups):
        return []
    edges = {0, duration_us}
    # Sample each output frame as well as exact effect boundaries. This follows
    # the existing five-frame-in/seven-frame-out envelope, including when an
    # overlay begins halfway through a scene punch.
    edges.update(range(0, duration_us, round(1e6 / 30)))
    for group in groups:
        for effect in group:
            a, b = us(effect["offset"] / speed), us((effect["offset"] + effect["duration"]) / speed)
            edges.update(t - clip_offset_us for t in (a, a + us(5 / 30), b - us(7 / 30), b)
                         if 0 <= t - clip_offset_us <= duration_us)
    points = []
    for offset in sorted(edges):
        at = (offset + clip_offset_us) / 1e6
        scale, tx, ty = 1., 0., 0.
        for group in groups:
            if not group:
                continue
            amount = 0.
            for effect in group:
                a, b = effect["offset"] / speed, (effect["offset"] + effect["duration"]) / speed
                if a <= at <= b:
                    amount += (effect.get("factor", 1.08) - 1) * max(0, min(1, (at-a)/(5/30))) * max(0, min(1, (b-at)/(7/30)))
            zoom = min(1.14, 1 + amount)
            x, y = group[0].get("x", .5), group[0].get("y", .5)
            # Composition order matches the renderer: presenter, then scene.
            scale, tx, ty = scale * zoom, tx * zoom + (zoom-1)*(1-2*x), ty * zoom + (zoom-1)*(2*y-1)
        points.append((offset, scale, tx, ty))
    # Keep linear envelopes small. Retain per-frame samples only where a
    # composition actually creates a nonlinear section.
    compact = []
    for point in points:
        while len(compact) >= 2:
            left, middle = compact[-2:]
            fraction = (middle[0]-left[0])/(point[0]-left[0])
            if all(abs(middle[i]-(left[i]+(point[i]-left[i])*fraction)) <= 1e-10 for i in (1, 2, 3)):
                compact.pop()
            else:
                break
        compact.append(point)
    return compact


def add_punch(api, segment, effects, speed, *, clip_offset_us=0, layers=("presenter", "scene")):
    for at, scale, x, y in punch_points(effects, speed, segment.duration, clip_offset_us=clip_offset_us, layers=layers):
        segment.add_keyframe(api.KeyframeProperty.uniform_scale, at, scale)
        segment.add_keyframe(api.KeyframeProperty.position_x, at, x)
        segment.add_keyframe(api.KeyframeProperty.position_y, at, y)


def align_native_duration(segment, expected_us):
    adjustment = expected_us - segment.duration
    if abs(adjustment) > 1:
        raise ValueError("Native library changed the shared duration by more than 1us")
    segment.duration = expected_us
    return adjustment


def validate_native_document(document, template, body_us, full_us, main_segments, stems, mapping):
    allowed = {"canvas_config", "config", "fps", "duration", "tracks", "materials"}
    for key, value in template.items():
        if key not in allowed and document.get(key) != value:
            raise ValueError(f"Unrelated native field changed: {key}")
    if not set(template["materials"]).issubset(document["materials"]):
        raise ValueError("Lost a native material category")
    ids = {m["id"] for values in document["materials"].values() if isinstance(values, list)
           for m in values if isinstance(m, dict) and "id" in m}
    checked_refs, keyframe_count, segment_count = 0, 0, 0
    for track in document["tracks"]:
        previous_end = 0
        for segment in sorted(track["segments"], key=lambda s: s["target_timerange"]["start"]):
            span = segment["target_timerange"]
            start, end = span["start"], span["start"] + span["duration"]
            if not 0 <= start < end <= full_us + 1 or start < previous_end:
                raise ValueError(f"Timeline gap/overlap boundary error on {track['name']}")
            previous_end = end
            refs = [segment["material_id"], *segment.get("extra_material_refs", [])]
            if set(refs) - ids:
                raise ValueError("Unresolved material reference")
            checked_refs += len(refs)
            if track["type"] == "video" and segment.get("volume") != 0:
                raise ValueError("All native video clips must be muted; fixed voice stem owns sound")
            for keyframe in segment.get("common_keyframes", []):
                points = keyframe["keyframe_list"]
                if any(not 0 <= p["time_offset"] <= span["duration"] for p in points):
                    raise ValueError("Keyframe is outside its segment")
                if any(not all(math.isfinite(v) for v in p["values"]) for p in points):
                    raise ValueError("Nonfinite keyframe value")
                keyframe_count += len(points)
            segment_count += 1
    cursor = 0
    for segment in main_segments:
        if segment.start != cursor:
            raise ValueError("Main video has a gap")
        cursor = segment.end
    if cursor != full_us or main_segments[len(mapping) - 1].end != body_us:
        raise ValueError("Body/ending boundary mismatch")
    if len(stems) != 3 or any(s["start_us"] != 0 or s["duration_us"] != full_us or s["gain"] != 1 for s in stems.values()):
        raise ValueError("Three audio stems must share time zero, full duration, and unity gain")
    audio_segments = [s for t in document["tracks"] if t["type"] == "audio" for s in t["segments"]]
    if len(audio_segments) != 3 or any(s["volume"] != 1 or s["speed"] != 1 or s["target_timerange"] != {"start": 0, "duration": full_us} for s in audio_segments):
        raise ValueError("Actual native audio segments disagree with the fixed stems")
    audio_materials = {a["id"]: a for a in document["materials"]["audios"]}
    actual_paths = sorted(str(Path(audio_materials[s["material_id"]]["path"]).resolve()) for s in audio_segments)
    expected_paths = sorted(str(Path(stem["path"]).resolve()) for stem in stems.values())
    if actual_paths != expected_paths:
        raise ValueError("Native audio tracks duplicate or replace an approved stem")
    return {"status": "pass", "checked_references": checked_refs, "keyframe_points": keyframe_count,
            "segments": segment_count, "body_duration_us": body_us, "duration_us": full_us,
            "source_clips": len(mapping), "three_audio_stems_at_zero": True,
            "all_video_muted": True, "native_open_export": "unverified"}


def build_project(*, job, native_blank, output, output_root, vendor_root, vendor_lock,
                  engine_src, audio_stems, ffprobe):
    job, native_blank, output = Path(job).resolve(), Path(native_blank).resolve(), Path(output).resolve()
    output_root, audio_stems = Path(output_root).resolve(), Path(audio_stems).resolve()
    if output.exists() or not output.is_relative_to(output_root) or "com.lveditor.draft" in output.parts:
        raise ValueError("Only a NEW directory inside the declared staging root is allowed")
    project = read_json(job / "project.json")
    receipt = read_json(job / "latest-render.json")
    if not receipt.get("complete") or receipt["revision"] != project["revision"]:
        raise ValueError("Current render and project revision disagree")
    sys.path.insert(0, str(Path(engine_src).resolve(strict=True)))
    engine = importlib.import_module("talking_head_editor.timeline")
    plan = project["plan"]
    transcript = read_json(verified_media(job, project["transcript"]))
    engine.validate_plan(plan, project["source"]["duration"], transcript["words"], project["assets"])
    compiled = engine.compile_clips(plan["clips"], plan["style"]["playback_speed"])
    for actual, old in zip(compiled, receipt["clips"], strict=True):
        for key in ("id", "start", "end", "frames", "output_start", "output_duration", "playback_speed"):
            if actual[key] != old[key]:
                raise ValueError(f"Compiled timeline disagrees with current render: {actual['id']} {key}")
    mapping = frame_mapping(compiled, engine.FPS)
    by_id = {c["id"]: c for c in mapping}
    body_us = mapping[-1]["target_start_us"] + mapping[-1]["target_duration_us"]
    ending = plan.get("ending")
    full_us = body_us + us(ending["duration"] if ending else 0)
    if abs(full_us / 1e6 - receipt["expected_duration"]) > 1e-6:
        raise ValueError("Final duration differs from the accepted render timebase")
    source = verified_media(job, project["source"])
    tracks_receipt = read_json(audio_stems / "tracks.json")
    if tracks_receipt["revision"] != project["revision"] or tracks_receipt["fingerprint"] != receipt["fingerprint"]:
        raise ValueError("Audio stems belong to another render")
    stem_paths, stems = {}, {}
    for key in ("voice", "music", "sfx"):
        entry = tracks_receipt["tracks"][key]
        path = verified_media(audio_stems, entry)
        with wave.open(str(path), "rb") as wav:
            rate, frames = wav.getframerate(), wav.getnframes()
            wav_duration = frames / rate
            if abs(wav_duration - full_us / 1e6) > 1 / rate or entry["start_seconds"] != 0 or not entry["gain_already_applied"]:
                raise ValueError("Audio stem timebase/gain mismatch")
            stems[key] = {"path": str(path), "sha256": entry["sha256"], "start_us": 0,
                          "duration_us": full_us, "samples": frames, "sample_rate": rate,
                          "channels": wav.getnchannels(), "sample_width_bytes": wav.getsampwidth(), "gain": 1}
        stem_paths[key] = path
    subtitle_path = (job / receipt["files"]["landscape"]["subtitles"]).resolve(strict=True)
    if not subtitle_path.is_relative_to(job):
        raise ValueError("Subtitle path escapes the job")
    cues = read_srt(subtitle_path)
    if any(c["end"] > body_us for c in cues):
        raise ValueError("Subtitle extends beyond original speech body")
    native_project_path = native_blank / "Timelines/project.json"
    native_project = read_json(native_project_path)
    timeline_id = native_project["main_timeline_id"]
    if not re.fullmatch(r"[A-Za-z0-9-]+", timeline_id):
        raise ValueError("Invalid native timeline id")
    template_path = native_blank / "Timelines" / timeline_id / "template.tmp"
    template = read_json(template_path)
    if template.get("tracks") or any(template.get("materials", {}).values()):
        raise ValueError("Native seed must be the genuinely empty template")
    if len(receipt["requested_formats"]) != 1 or receipt["requested_formats"][0] != "landscape":
        raise ValueError("This first adapter handles the current landscape project only")
    width, height = receipt["files"]["landscape"]["width"], receipt["files"]["landscape"]["height"]
    install_file_only_guard(output_root, ffprobe)
    api = load_pinned_core(vendor_root, vendor_lock)
    script = new_script(api, width, height, engine.FPS)
    track_names = {"main": "01 真人原片与片尾（画面静音）", "overlay": "02 素材与流程（独立可移动）",
                   "caption": "03 字幕（独立可编辑）", "keyword": "04 彩色重点字（独立可编辑）",
                   "voice": "05 人声（已调平，不再归一化）", "music": "06 背景音乐（已降低，可手调）",
                   "sfx": "07 轻音效（独立）"}
    script.add_track(api.TrackType.video, track_names["main"])
    script.add_track(api.TrackType.video, track_names["overlay"], relative_index=1)
    script.add_track(api.TrackType.text, track_names["caption"])
    script.add_track(api.TrackType.text, track_names["keyword"], relative_index=1)
    for key in ("voice", "music", "sfx"):
        script.add_track(api.TrackType.audio, track_names[key])
    material_cache, used_assets = {}, {}
    def video_material(path):
        path = Path(path)
        if str(path) not in material_cache:
            material_cache[str(path)] = api.VideoMaterial(str(path))
        return material_cache[str(path)]
    def asset_material(asset_id):
        asset = project["assets"][asset_id]
        if asset["kind"] != "video":
            raise ValueError("Only the current registered video overlays are supported")
        if asset_id not in used_assets:
            path = verified_media(job, asset)
            used_assets[asset_id] = {"path": str(path), "sha256": asset["sha256"], "license": asset["license"],
                                     "internal_text_editable": False}
        material = video_material(used_assets[asset_id]["path"])
        registered_duration = us(asset["duration"])
        # Upstream truncates float seconds to int microseconds (4.1 can become
        # 4,099,999). Reconcile only this <=2us numeric-rounding discrepancy.
        if abs(material.duration - registered_duration) <= 2:
            used_assets[asset_id].setdefault("duration_rounding_adjustment_us", registered_duration - material.duration)
            material.duration = registered_duration
        return material
    main_segments = []
    for clip in mapping:
        segment = api.VideoSegment(video_material(source), api.Timerange(clip["target_start_us"], clip["target_duration_us"]),
            source_timerange=api.Timerange(clip["source_start_us"], clip["source_duration_us"]),
            speed=clip["playback_speed"], volume=0)
        clip["native_duration_adjustment_us"] = align_native_duration(segment, clip["target_duration_us"])
        effects = [e for e in plan["visual_effects"] if e["clip_id"] == clip["id"] and e["kind"] == "punch"]
        add_punch(api, segment, effects, clip["playback_speed"])
        script.add_segment(segment, track_names["main"])
        main_segments.append(segment)
    overlay_rows, dark_ranges = [], []
    for overlay in plan["overlays"]:
        if not overlay.get("asset_id") or overlay.get("mode", "full") != "full":
            raise ValueError("Current adapter requires explicit full-frame video assets")
        clip = by_id[overlay["clip_id"]]
        speed = clip["playback_speed"]
        start = us(clip["output_start"] + overlay["offset"] / speed)
        end = us(clip["output_start"] + (overlay["offset"] + overlay["duration"]) / speed)
        asset_speed = overlay.get("asset_speed", speed)
        source_start = us(overlay.get("source_start", 0))
        source_duration = round((end - start) * asset_speed)
        material = asset_material(overlay["asset_id"])
        if source_start + source_duration > material.duration + 1:
            raise ValueError("Overlay needs more source duration than the registered asset")
        segment = api.VideoSegment(material, api.Timerange(start, end - start),
            source_timerange=api.Timerange(source_start, source_duration), speed=asset_speed, volume=0)
        duration_adjustment = align_native_duration(segment, end-start)
        scene_effects = [e for e in plan["visual_effects"] if e["kind"] == "punch" and e["clip_id"] == clip["id"] and e.get("target", "presenter") == "scene"]
        add_punch(api, segment, scene_effects, speed, clip_offset_us=us(overlay["offset"]/speed), layers=("scene",))
        continuous = bool(ending and overlay["clip_id"] == mapping[-1]["id"] and
                          overlay["asset_id"] == ending["asset_id"] and
                          abs(source_start + source_duration - us(ending["source_start"])) <= 2 and abs(end - body_us) <= 1)
        # Alpha keyframes use the upstream VideoSegment API, not an online effect.
        fade = min(us(.18), segment.duration // 4)
        segment.add_keyframe(api.KeyframeProperty.alpha, 0, 0)
        segment.add_keyframe(api.KeyframeProperty.alpha, fade, 1)
        if not continuous:
            segment.add_keyframe(api.KeyframeProperty.alpha, segment.duration - fade, 1)
            segment.add_keyframe(api.KeyframeProperty.alpha, segment.duration, 0)
        script.add_segment(segment, track_names["overlay"])
        overlay_rows.append({"id": overlay["id"], "asset_id": overlay["asset_id"], "start_us": start, "end_us": end,
                             "source_start_us": source_start, "source_duration_us": source_duration,
                             "asset_speed": asset_speed, "continuous_into_ending": continuous,
                             "native_duration_adjustment_us": duration_adjustment,
                             "scene_punch_ids": [e["id"] for e in scene_effects]})
        if overlay.get("caption_theme") == "dark":
            dark_ranges.append((start, end))
    if ending:
        segment = api.VideoSegment(asset_material(ending["asset_id"]), api.Timerange(body_us, full_us - body_us),
            source_timerange=api.Timerange(us(ending["source_start"]), full_us - body_us), speed=1, volume=0)
        script.add_segment(segment, track_names["main"])
        main_segments.append(segment)
        last_overlay = overlay_rows[-1]
        if not last_overlay["continuous_into_ending"]:
            raise ValueError("Avatar overlay no longer joins the intended ending continuously")
    themed = themed_captions(cues, dark_ranges)
    for cue in themed:
        text_segment(api, script, track_names["caption"], cue["text"], cue["start"], cue["end"],
                     pixels=plan["style"]["font_size"], color="#172B3A" if cue["theme"] == "dark" else "#FFFFFF",
                     bold=plan["style"].get("caption_bold", False), outline=0 if cue["theme"] == "dark" else plan["style"].get("caption_outline", 2))
    keyword_rows = []
    for effect in plan["visual_effects"]:
        if effect["kind"] != "keyword":
            continue
        clip = by_id[effect["clip_id"]]
        start = us(clip["output_start"] + effect["offset"] / clip["playback_speed"])
        end = us(clip["output_start"] + (effect["offset"] + effect["duration"]) / clip["playback_speed"])
        segment = text_segment(api, script, track_names["keyword"], effect["text"], start, end,
            pixels=effect.get("font_size", 72), color=effect.get("color", "#FFFFFF"), bold=effect.get("bold", False),
            x=effect.get("x", .5), y=effect.get("y", .72), outline=effect.get("outline", 2))
        if effect.get("animation") == "settle":
            segment.add_keyframe(api.KeyframeProperty.uniform_scale, 0, .96)
            segment.add_keyframe(api.KeyframeProperty.uniform_scale, min(us(.22), segment.duration), 1)
        elif effect.get("animation") == "fade":
            # TextSegment inherits this API, although upstream documents alpha
            # rendering only for VideoSegment. Author it as a testable local
            # keyframe; do not claim the native text renderer has accepted it.
            fade_in, fade_out = min(us(.12), segment.duration//4), min(us(.16), segment.duration//4)
            for at, value in ((0, 0), (fade_in, 1), (segment.duration-fade_out, 1), (segment.duration, 0)):
                segment.add_keyframe(api.KeyframeProperty.alpha, at, value)
        keyword_rows.append({"id": effect["id"], "text": effect["text"], "color": effect.get("color", "#FFFFFF"),
                             "start_us": start, "end_us": end, "native_animation": "scale .96 to 1" if effect.get("animation") == "settle" else "alpha 0 to 1 to 0 via inherited API; native text playback unverified"})
    for key, path in stem_paths.items():
        segment = api.AudioSegment(api.AudioMaterial(str(path)), api.Timerange(0, full_us), volume=1, speed=1)
        script.add_segment(segment, track_names[key])
    generated = json.loads(script.dumps())
    merged = copy.deepcopy(template)
    merged["canvas_config"].update(width=width, height=height, ratio="original")
    merged["fps"], merged["duration"] = engine.FPS, full_us
    merged["tracks"] = generated["tracks"]
    merged["materials"].update(generated["materials"])
    merged["config"]["maintrack_adsorb"] = True
    validation = validate_native_document(merged, template, body_us, full_us, main_segments, stems, mapping)
    nested = output / "Timelines" / timeline_id
    nested.mkdir(parents=True, exist_ok=False)
    write_new_json(output / "draft_content.json", merged)
    write_new_json(nested / "draft_content.json", merged)
    write_new_json(output / "Timelines/project.json", native_project)
    with (output / "captions.srt").open("xb") as stream:
        stream.write(subtitle_path.read_bytes())
    manifest = {
        "status": "staged_native_candidate_not_app_verified", "revision": project["revision"],
        "source_fingerprint": receipt["fingerprint"], "source_project_sha256": file_sha256(job / "project.json"),
        "upstream_commit": UPSTREAM_COMMIT, "vendor_root": str(Path(vendor_root).resolve()),
        "source": {"path": str(source), "sha256": project["source"]["sha256"]},
        "body_duration_us": body_us, "duration_us": full_us, "compiled_clips": mapping,
        "audio_stems": stems, "audio_loudness_normalization": False, "all_video_audio_muted": True,
        "overlays": overlay_rows, "assets": used_assets, "ending": ending,
        "subtitles": {"path": str(subtitle_path), "sha256": file_sha256(subtitle_path), "cue_count": len(cues),
                      "native_segments_after_color_split": len(themed), "dark_ranges_us": dark_ranges,
                      "srt_unchanged": file_sha256(output / "captions.srt") == file_sha256(subtitle_path)},
        "keywords": keyword_rows, "native_template": {"path": str(template_path), "sha256": file_sha256(template_path),
                     "id_preserved": template["id"], "main_timeline_id": timeline_id, "new_version": template["new_version"]},
        "content_sha256": file_sha256(output / "draft_content.json"),
        "root_nested_identical": file_sha256(output / "draft_content.json") == file_sha256(nested / "draft_content.json"),
        "structural_validation": validation, "ui_modules_loaded": [m for m in FORBIDDEN_MODULES if m in sys.modules],
        "live_store_written": False, "extra_dependencies_installed": [],
        "limitations": ["Native app open, font sizing, render, and audiovisual review are unverified",
                        "Flow/avatar video internals are baked; their timeline placement is independently editable",
                        "Video alpha keyframes are authored with upstream API; native rendering requires visual confirmation",
                        "The one fade-only keyword uses inherited local alpha keyframes; upstream guarantees video alpha only, so text fading is explicitly unverified",
                        "Per-clip muted picture extends by less than one output frame; fixed voice stem is unchanged",
                        "Encrypted native metadata is preserved by the separate deployment task; this adapter does not register live drafts"],
    }
    write_new_json(output / "build-manifest.json", manifest)
    write_new_json(output / "structural-validation.json", validation)
    return manifest
