from __future__ import annotations

import math
import re
from fractions import Fraction

from .util import ident, number, require, digest

FPS = 30
FORMATS = {"landscape": (1920, 1080), "portrait": (1080, 1920)}
DEFAULT_STYLE = {"font_size": 52, "accent": "#F7C95C", "keywords": [],
                 "music_gain_db": -29, "loudness_lufs": -16, "true_peak_db": -1,
                 "background": "#151923", "caption_color": "#FFFFFF"}
CRITICAL = re.compile(r"\d+|不|没|无|仅|只|至少|至多|除非|如果|可能|也许|RM|%|[A-Z]{2,}")


def critical_words(words):
    combined="".join(w["text"] for w in words)
    spans=[m.span() for m in CRITICAL.finditer(combined)]
    result=[]; position=0
    for w in words:
        end=position+len(w["text"])
        if any(a<end and b>position for a,b in spans): result.append(w)
        position=end
    return result


def validate_transcript(data, duration):
    require(data.get("schema_version") == 1 and isinstance(data.get("words"), list),
            "transcript_schema", "Expected schema_version=1 and words[] with id/text/start/end")
    previous = 0
    ids = set()
    for w in data["words"]:
        ident(w["id"])
        require(w["id"] not in ids, "duplicate_word", "Duplicate word ID")
        ids.add(w["id"])
        start, end = number(w["start"], "word.start"), number(w["end"], "word.end")
        require(start >= previous - .02 and end > start and end <= duration + .1,
                "word_timing", f"Invalid word timing: {w['id']}")
        require(isinstance(w.get("text"), str) and w["text"].strip(), "word_text", "Empty word")
        previous = end
    require(data["words"], "empty_transcript", "No words recognized; do not fabricate transcript")
    return data


def gaps(clips, duration):
    ordered = sorted((c["start"], c["end"]) for c in clips)
    pos = 0.0
    result = []
    for a, b in ordered:
        if a > pos + .001:
            result.append((pos, a))
        pos = max(pos, b)
    if pos < duration - .001:
        result.append((pos, duration))
    return result


def output_formats(plan, source_info):
    requested = plan.get("output_formats", ["source"])
    require(isinstance(requested, list) and requested and len(requested) == len(set(requested))
            and all(x in (*FORMATS, "source") for x in requested), "output_formats", "Choose source or explicit landscape/portrait")
    require("source" not in requested or len(requested) == 1, "output_formats", "Source must be the only automatic format")
    if requested != ["source"]:
        return {x: FORMATS[x] for x in requested}
    v = next((s for s in source_info.get("streams", []) if s.get("codec_type") == "video"), {})
    sw, sh = v.get("width", 0), v.get("height", 0)
    require(sw > 0 and sh > 0, "source_geometry", "Source dimensions are required")
    sar = v.get("sample_aspect_ratio", "1:1")
    try: ratio = sw / sh * float(Fraction(sar.replace(":", "/")))
    except (ValueError, ZeroDivisionError): ratio = sw / sh
    if ratio <= 0: ratio = sw / sh
    rotation = next((s["rotation"] for s in v.get("side_data_list", []) if "rotation" in s), v.get("tags", {}).get("rotate", 0))
    if abs(round(float(rotation))) % 180 == 90: ratio = 1 / ratio
    for name, (w,h) in FORMATS.items():
        if abs(ratio - w/h) < .002: return {name: (w,h)}
    w,h = (round(1080*ratio/2)*2,1080) if ratio >= 1 else (1080,round(1080/ratio/2)*2)
    require(max(w,h) <= 7680, "source_geometry", "Unusual aspect ratio needs an explicit layout")
    return {"source": (w,h)}


def compile_clips(clips, speed=1):
    position = 0
    result = []
    for clip in clips:
        c = dict(clip)
        rate = c.get("playback_speed", speed)
        frames = math.ceil((c["end"] - c["start"]) / rate * FPS - 1e-7)
        c.update(output_start=position / FPS, frames=frames, output_duration=frames / FPS, playback_speed=rate)
        position += frames
        result.append(c)
    return result


def validate_plan(plan, duration, words, assets):
    require(plan.get("schema_version") == 1, "plan_schema", "Expected schema_version=1")
    supported = {"schema_version", "base_revision", "scope", "clips", "deletions", "overlays",
                 "caption_corrections", "caption_groups", "caption_break_after", "correction_evidence",
                 "style", "semantic_review", "output_formats", "music_asset_id", "ending",
                 "visual_effects", "sound_effects", "visual_rhythm", "sfx_review"}
    require(not (set(plan)-supported), "unsupported_plan_field",
            "Unsupported plan fields: " + ", ".join(sorted(set(plan)-supported)))
    def keys(value, supported, where):
        require(not (set(value)-set(supported)), "unsupported_field", f"Unsupported {where} fields: {sorted(set(value)-set(supported))}")
    keys(plan.get('style',{}), set(DEFAULT_STYLE)|{'playback_speed','caption_bold','caption_outline','caption_shadow','editorial_preferences','encode_headroom_db'},'style')
    for effect in plan.get('visual_effects',[]):
        keys(effect,{'id','clip_id','offset','duration','kind','purpose','target','factor','review_evidence','text','x','y','color','font_size','outline','bold','animation'},'visual_effect')
    for effect in plan.get('sound_effects',[]):
        keys(effect,{'id','clip_id','offset','duration','kind','purpose','gain'},'sound_effect')
    for overlay in plan.get('overlays',[]):
        keys(overlay,{'id','clip_id','offset','duration','asset_id','source_start','asset_speed','mode','purpose','graphic','motion_times','caption_theme'},'overlay')
        require(overlay.get('caption_theme','default') in ('default','dark'),'caption_theme','Only default or dark caption theme supported')
        require(overlay.get('caption_theme','default')=='default' or overlay.get('mode','full')=='full',
                'caption_theme','A dark caption theme requires an inspected light full-frame visual')
    speed = number(plan.get("style", {}).get("playback_speed", 1), "playback_speed", .5)
    require(speed <= 2, "playback_speed", "Use 0.5..2x speech speed")
    requested = plan.get("output_formats", ["source"])
    require(isinstance(requested, list) and requested and all(isinstance(x,str) and x in (*FORMATS,"source") for x in requested)
            and len(requested)==len(set(requested)) and ("source" not in requested or len(requested)==1),
            "output_formats", "Choose source alone or explicit landscape/portrait")
    clips = plan.get("clips", [])
    require(isinstance(clips, list) and 0 < len(clips) <= 500, "clips", "Expected 1..500 clips")
    ids = set()
    for c in clips:
        ident(c["id"])
        require(c["id"] not in ids, "duplicate_clip", "Duplicate clip ID")
        ids.add(c["id"])
        a, b = number(c["start"], "clip.start"), number(c["end"], "clip.end")
        require(b - a >= .1 and b <= duration + .001, "clip_range", "Clip outside source or shorter than 0.1s")
        require(c.get("reason", "").strip(), "missing_reason", "Every retained/moved clip needs a reason")
        require("playback_speed" not in c, "clip_speed", "Set speed once in plan.style, not per source clip")
        for w in words:
            require(not (w["start"] + .025 < a < w["end"] - .025 or w["start"] + .025 < b < w["end"] - .025),
                    "cut_inside_word", f"Cut would split word {w['id']} ({w['text']}); move the boundary")
        require(isinstance(c.get("layouts", {}), dict), "layout", "layouts must be an object")
        for variant, layout in c.get("layouts", {}).items():
            require(variant in (*FORMATS, "source") and isinstance(layout, dict), "layout", "Unknown layout")
            keys(layout,{'fit','background','title','review_evidence','x','y'},'layout')
            fit = layout.get("fit", "contain")
            require(fit in ("contain", "cover"), "layout", "Unknown layout")
            require(layout.get("background", "solid") in ("solid", "blur"),
                    "layout_background", "Layout background must be solid or blur")
            require(layout.get("background") != "blur" or fit == "contain",
                    "layout_background", "Blur background requires contain framing")
            if "title" in layout:
                title = layout["title"]
                require(variant == "portrait" and fit == "contain", "layout_title",
                        "A layout title is supported only above portrait contain framing")
                require(isinstance(title, str) and 0 < len(title.strip()) <= 80
                        and all(ord(ch) >= 32 or ch == "\n" for ch in title),
                        "layout_title", "Use a nonempty title of at most 80 characters")
            if layout.get("fit") == "cover":
                require(layout.get("review_evidence", "").strip(), "crop_review", "Cover crop requires inspected-frame evidence")
            for axis in ("x", "y"):
                require(0 <= number(layout.get(axis, .5), axis) <= 1, "crop_position", "Crop focus must be 0..1")
    chronological = sorted(clips, key=lambda x: x["start"])
    for left, right in zip(chronological, chronological[1:]):
        require(left["end"] <= right["start"] + .001, "overlapping_source", "Source intervals cannot repeat/overlap")
    removed = plan.get("deletions", [])
    expected = gaps(clips, duration)
    require(len(expected) == len(removed), "unlogged_deletion", "Record each omitted source gap in deletions[]")
    for (a, b), d in zip(expected, sorted(removed, key=lambda x: x["start"])):
        require(abs(number(d["start"], "deletion.start")-a)<.002 and abs(number(d["end"], "deletion.end")-b)<.002,
                "deletion_range", "Deletion ledger does not match retained clips")
        require(d.get("reason", "").strip(), "deletion_reason", "Every deletion needs a specific reason")
    corrections = plan.get("caption_corrections", {})
    word_ids = {w["id"] for w in words}
    caption_breaks = plan.get("caption_break_after", [])
    require(isinstance(caption_breaks, list)
            and all(isinstance(wid, str) and wid in word_ids for wid in caption_breaks),
            "caption_break_after", "Caption breaks must be a list of existing transcript word IDs")
    require(len(caption_breaks) == len(set(caption_breaks)), "caption_break_after",
            "Caption break word IDs must be unique")
    require(all(k in word_ids and isinstance(v, str) and v.strip() for k,v in corrections.items()),
            "caption_correction", "Caption corrections must reference existing word IDs and nonempty text")
    if corrections:
        require(plan.get("correction_evidence", "").strip(), "correction_evidence", "Explain corrections against original audio/script")
    order = [w["id"] for w in words]
    grouped = set()
    for group in plan.get("caption_groups", []):
        members = group.get("word_ids", [])
        require(isinstance(members,list) and members and all(w in word_ids for w in members)
                and isinstance(group.get("text"),str) and group["text"].strip(), "caption_group", "Caption group needs existing consecutive words and text")
        at = order.index(members[0])
        require(order[at:at+len(members)]==members and not grouped.intersection(members), "caption_group", "Caption groups must be consecutive and disjoint")
        grouped.update(members)
        for clip in clips:
            included = [w["id"] for w in words if w["id"] in members and w["start"]>=clip["start"]-.025 and w["end"]<=clip["end"]+.025]
            require(not included or included == members, "caption_group_cut", "Do not cut through a grouped term")
        require(plan.get("correction_evidence", "").strip(), "correction_evidence", "Explain grouped spelling against source speech")
    clip_map = {c["id"]: c for c in clips}
    overlay_ids = set()
    for o in plan.get("overlays", []):
        ident(o["id"])
        require(o["id"] not in overlay_ids, "overlay_id", "Duplicate overlay ID")
        overlay_ids.add(o["id"])
        require(o.get("clip_id") in ids, "overlay_anchor", "Overlay must reference a retained clip")
        length = clip_map[o["clip_id"]]["end"]-clip_map[o["clip_id"]]["start"]
        offset, span = number(o["offset"], "overlay.offset"), number(o["duration"], "overlay.duration", .1)
        require(offset + span <= length + .001, "overlay_range", "Overlay exceeds its source clip")
        require(o.get("purpose", "").strip(), "overlay_purpose", "Explain what this visual adds to the spoken sentence")
        require(o.get("mode", "full") in ("full", "pip", "banner"), "overlay_mode", "mode must be full, pip or banner")
        if o.get("asset_id"):
            require(o["asset_id"] in assets, "missing_asset", "Unknown asset")
            a = assets[o["asset_id"]]
            require(a.get("kind") in ("image", "video"), "visual_asset", "Overlay needs an image or video asset")
            require(a.get("review", {}).get("description") and a.get("review", {}).get("evidence"),
                    "asset_not_reviewed", "Inspect asset contact sheet/clip and annotate it before rendering")
            license = a.get("license", {})
            require(license.get("kind") in ("provided", "free", "paid"), "asset_license", "Asset license not recorded")
            if license["kind"] in ("free", "paid"):
                require(license.get("url") and a.get("source_url"), "asset_provenance", "Web assets require source and license URLs")
            if license["kind"] == "paid":
                approval = a.get("approval", {})
                require(approval.get("user_evidence") and approval.get("sha256") == a["sha256"]
                        and a.get("preview_url") and isinstance(a.get("price"), dict),
                        "paid_approval_required", "Show preview, price and purpose; record actual user approval first")
            if a.get("kind") == "video":
                asset_speed = number(o.get("asset_speed", speed), "asset_speed", .5)
                require(asset_speed <= 2, "asset_speed", "Asset speed must be 0.5..2x")
                require(number(o.get("source_start", 0), "asset.source_start") + span/speed*asset_speed <= a["duration"]+.001,
                        "asset_too_short", "Video asset shorter than selected interval")
        else:
            g = o.get("graphic", {})
            require(g.get("type") in ("title", "keywords", "bar", "flow", "states"), "graphic_type", "Unknown graphic")
            require(g.get("title") or g.get("text"), "graphic_text", "Graphic needs a title/text")
            if g["type"] in ("flow", "states"):
                nodes = g.get("nodes", [])
                require(isinstance(nodes,list) and 1 <= len(nodes) <= 5 and all(isinstance(n,str) and n.strip() for n in nodes), "flow_nodes", "Use 1..5 nonempty nodes")
                times = g.get("step_times")
                if times is not None:
                    require(isinstance(times,list) and len(times)==len(nodes), "flow_timing", "One source-relative time per node")
                    values = [number(x,"step_time") for x in times]
                    require(values[0]==0 and all(a<b for a,b in zip(values,values[1:])) and values[-1]<span,
                            "flow_timing", "Step times must start at zero, ascend and fit overlay")
            if g["type"] == "bar":
                require(g.get("evidence", "").strip() and g.get("items"), "chart_evidence", "Charts require real data and its source")
                for item in g["items"]:
                    number(item["value"], "bar.value")
                    require(item.get("label"), "chart_label", "Bar needs a label")
    music = plan.get("music_asset_id")
    if music:
        require(music in assets and assets[music].get("kind") == "audio", "music_asset", "Select a registered audio asset")
        a = assets[music]
        require(a.get("review", {}).get("evidence"), "music_review", "Listen to music before using it")
        require(a.get("license", {}).get("kind") in ("provided", "free", "paid"), "music_license", "Music license missing")
        if a["license"]["kind"] in ("free", "paid"):
            require(a["license"].get("url") and a.get("source_url"), "music_provenance", "Web music needs source and license URLs")
        if a["license"]["kind"] == "paid":
            require(a.get("approval", {}).get("sha256") == a["sha256"] and a.get("approval", {}).get("user_evidence") and a.get("preview_url") and a.get("price"),
                    "paid_approval_required", "Paid music approval is missing")
    style = {**DEFAULT_STYLE, **plan.get("style", {})}
    require(isinstance(style["keywords"], list) and all(isinstance(k, str) and k.strip() for k in style["keywords"]), "keywords", "Keywords must be nonempty strings")
    require(isinstance(style.get("caption_bold",True),bool), "caption_weight", "caption_bold must be boolean")
    for key,default in (("caption_outline",3),("caption_shadow",1)):
        require(number(style.get(key,default),key)<=4,"caption_stroke","Caption outline/shadow must be 0..4")
    require(28 <= number(style["font_size"], "font_size") <= 84, "font_size", "Use 28..84px base font")
    for key in ("accent", "background", "caption_color"):
        require(re.fullmatch(r"#[A-Fa-f0-9]{6}", style[key]), "color", "Colors must be #RRGGBB")
    require(-36 <= number(style["music_gain_db"], "music_gain_db", -36) <= -12, "music_gain", "Music gain must be -36..-12 dB")
    require(-20 <= number(style["loudness_lufs"], "loudness_lufs", -20) <= -14, "loudness", "Speech target must be -20..-14 LUFS")
    require(-3 <= number(style["true_peak_db"], "true_peak_db", -3) <= -1, "true_peak", "Peak target must be -3..-1 dBTP")
    require(-3 <= number(style.get("encode_headroom_db",0),"encode_headroom_db",-3) <= 0,
            "encode_headroom", "Codec headroom is a documented attenuation of 0..3dB, never amplification")
    compiled = compile_clips(clips, speed)
    from .motion import validate_motion
    validate_motion(plan, compiled, assets)
    return compiled


def mapped_words(words, clips, corrections=None, breaks=None, groups=None):
    result = []
    break_ids = set(breaks or [])
    for c in compile_clips(clips):
        for word in words:
            if word["start"] >= c["start"]-.025 and word["end"] <= c["end"]+.025:
                w = dict(word)
                w.update(text=(corrections or {}).get(w["id"], w["text"]), clip_id=c["id"],
                         source_start=w["start"], source_end=w["end"],
                         start=max(0, w["start"]-c["start"])/c["playback_speed"]+c["output_start"],
                         end=(min(c["end"], w["end"])-c["start"])/c["playback_speed"]+c["output_start"])
                if w["id"] in break_ids:
                    w["caption_break_after"] = True
                result.append(w)
    for group in groups or []:
        ids = group["word_ids"]
        positions = [i for i,w in enumerate(result) if w["id"] in ids]
        if not positions: continue
        require(len(positions)==len(ids) and positions==list(range(positions[0],positions[0]+len(ids))), "caption_group_cut", "Grouped term was partially selected")
        members = result[positions[0]:positions[-1]+1]
        merged = {**members[0], "text":group["text"], "end":members[-1]["end"], "source_end":members[-1]["source_end"],
                  "source_word_ids":ids, "caption_break_after":any(w.get("caption_break_after") for w in members)}
        result[positions[0]:positions[-1]+1] = [merged]
    return result


def default_plan(duration, revision):
    return {"schema_version": 1, "base_revision": revision, "output_formats": ["source"],
            "clips": [{"id": "c001", "start": 0, "end": duration, "reason": "Initial full source; agent has not reviewed edits"}],
            "deletions": [], "overlays": [], "caption_corrections": {},
            "style": {**DEFAULT_STYLE, "playback_speed": 1.1}, "semantic_review": {"status": "pending", "evidence": ""}}
