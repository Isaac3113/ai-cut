"""Approved practical renderer v1: same-frame screen-demo effects.

Reads source media without modifying it; exports a SILENT 1080-square layer.
Requires a 16:9 square-pixel source. See references/practical-renderer.md.
Usage: python render_practical_demo.py --config config.json --out-dir OUTPUT
       [--stills-only] [--preview-times 1.2,3.4] [--range-start 12 --range-duration 6]
All config and preview times remain relative to the whole practical section.
Rectangles use source pixels. Ranges change neither event nor speech timing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RENDERER_REVISION = "approved-practical-v1"
EFFECT_KINDS = frozenset(("lens", "focus", "spotlight", "underline", "pulse", "flow"))
W = H = 1080
PANEL_Y = 180
PANEL_H = 608
BG = (7, 20, 27)
CYAN = (62, 223, 238)
TEAL = (25, 172, 198)
WHITE = (233, 252, 255)


def smooth(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


def visibility(event, t):
    start, end = float(event["start"]), float(event["end"])
    if t < start or t > end:
        return 0.0
    ramp = min(float(event.get("ramp", .34)), (end - start) / 3)
    return min(smooth((t - start) / ramp), smooth((end - t) / ramp))


def rect_at(event, t):
    keyframes = sorted(event["rect_keyframes"], key=lambda f: f["time"])
    first, last = keyframes[0], keyframes[-1]
    if t <= first["time"]:
        return tuple(float(first[k]) for k in ("x", "y", "w", "h"))
    if t >= last["time"]:
        return tuple(float(last[k]) for k in ("x", "y", "w", "h"))
    for a, b in zip(keyframes, keyframes[1:]):
        if a["time"] <= t <= b["time"]:
            u = (t - a["time"]) / (b["time"] - a["time"])
            return tuple(float(a[k]) + (float(b[k]) - float(a[k])) * u
                         for k in ("x", "y", "w", "h"))
    raise RuntimeError("No rectangle interval")


def font(size):
    for path in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\simhei.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONTS = {size: font(size) for size in (18, 20, 22, 24, 26, 28)}


def text_center(draw, xy, text, size, fill):
    box = draw.textbbox((0, 0), text, font=FONTS[size])
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2 - box[1]),
              text, font=FONTS[size], fill=fill)


def mapped_rect(rect, src_size):
    x, y, w, h = rect
    sx, sy = W / src_size[0], PANEL_H / src_size[1]
    return x * sx, PANEL_Y + y * sy, w * sx, h * sy


def draw_target(base, rect, alpha, src_size, kind, t, event):
    x, y, w, h = mapped_rect(rect, src_size)
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    a = round(255 * alpha)
    if kind == "underline":
        # An editorial scan under the observed object, not a software cursor.
        progress = smooth((t-float(event["start"]))/float(event.get("sweep", .65)))
        line_y = min(PANEL_Y+PANEL_H-5, y+h+7)
        end_x = x+w*progress
        d.line((x, line_y, x+w, line_y), fill=(*TEAL, round(60*alpha)), width=3)
        d.line((x, line_y, end_x, line_y), fill=(*CYAN, a), width=5)
        if end_x > x:
            d.line((max(x, end_x-18), line_y, end_x, line_y), fill=(*WHITE, a), width=3)
        return Image.alpha_composite(base, layer)
    if kind == "pulse":
        # Slow, low-contrast breathing outlines identify the real rectangle.
        # They intentionally do not resemble a click, tap, or application state.
        pulse = .5-.5*math.cos((t-float(event["start"]))*2*math.pi*.8)
        padding = 5+5*pulse
        d.rounded_rectangle((x-5, y-5, x+w+5, y+h+5), radius=9,
                            outline=(*CYAN, round((150+70*pulse)*alpha)), width=3)
        d.rounded_rectangle((x-padding-4, y-padding-4, x+w+padding+4, y+h+padding+4),
                            radius=13, outline=(*TEAL, round((45+60*pulse)*alpha)), width=2)
        return Image.alpha_composite(base, layer)
    padding = 5
    bounds = (x - padding, y - padding, x + w + padding, y + h + padding)
    d.rounded_rectangle(bounds, radius=9, fill=(*CYAN, round(12 * alpha)),
                        outline=(*CYAN, a), width=3)
    # Corner accents identify the exact source object while leaving its text clear.
    for px, py, dx, dy in ((x-5, y-5, 1, 1), (x+w+5, y-5, -1, 1),
                          (x-5, y+h+5, 1, -1), (x+w+5, y+h+5, -1, -1)):
        d.line((px, py, px + dx*17, py), fill=(*WHITE, a), width=3)
        d.line((px, py, px, py + dy*17), fill=(*WHITE, a), width=3)
    if kind == "flow" and event.get("path"):
        # Optional source-pixel path traces only an observed original connection.
        # Without it, keep the target frame; never invent a directional UI arrow.
        points = [(px*W/src_size[0], PANEL_Y+py*PANEL_H/src_size[1])
                  for px, py in event["path"]]
        if len(points) >= 2:
            d.line(points, fill=(*TEAL, round(70*alpha)), width=9, joint="curve")
            d.line(points, fill=(*CYAN, round(205*alpha)), width=3, joint="curve")
            distances = [math.dist(p1, p2) for p1, p2 in zip(points, points[1:])]
            total = sum(distances)
            travel = (((t-float(event["start"])) % 1.45)/1.45)*total
            dot_x, dot_y = points[-1]
            for p1, p2, distance in zip(points, points[1:], distances):
                if travel <= distance:
                    u = travel/distance if distance else 0
                    dot_x = p1[0]+(p2[0]-p1[0])*u
                    dot_y = p1[1]+(p2[1]-p1[1])*u
                    break
                travel -= distance
            for radius, opacity in ((12, 25), (8, 65), (4, 255)):
                d.ellipse((dot_x-radius, dot_y-radius, dot_x+radius, dot_y+radius),
                          fill=(*CYAN, round(opacity*alpha)))
    return Image.alpha_composite(base, layer)


def draw_magnifier(base, source, rect, event, t, amount):
    x, y, rw, rh = rect
    rx, ry, rwidth, rheight = mapped_rect(rect, source.size)
    origin = (rx + rwidth/2, ry + rheight/2)
    target = event.get("center", [785, 499])
    cx = origin[0] + (target[0] - origin[0]) * amount
    cy = origin[1] + (target[1] - origin[1]) * amount
    full_diameter = float(event.get("diameter", 460))
    diameter = max(24, round(66 + (full_diameter - 66) * amount))
    radius = diameter / 2
    left, top = round(cx - radius), round(cy - radius)

    # Expand the requested source rectangle to a square without distorting text.
    side = max(rw, rh) * float(event.get("crop_padding", 1.12))
    crop_cx, crop_cy = x + rw/2, y + rh/2
    side = min(side, source.width, source.height)
    crop_cx = min(source.width-side/2, max(side/2, crop_cx))
    crop_cy = min(source.height-side/2, max(side/2, crop_cy))
    crop_box = (round(crop_cx-side/2), round(crop_cy-side/2),
                round(crop_cx+side/2), round(crop_cy+side/2))
    # Always crop the current decoded video frame. No cached/still replacement.
    crop = source.crop(crop_box).resize((diameter, diameter), Image.Resampling.LANCZOS).convert("RGBA")
    mask2 = Image.new("L", (diameter*2, diameter*2))
    ImageDraw.Draw(mask2).ellipse((1, 1, diameter*2-2, diameter*2-2), fill=round(255*amount))
    mask = mask2.resize((diameter, diameter), Image.Resampling.LANCZOS)
    crop.putalpha(mask)

    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    # Leader stops at the glass rim instead of crossing the magnified content.
    vx, vy = cx - origin[0], cy - origin[1]
    length = math.hypot(vx, vy)
    if length > radius + 20:
        endpoint = (cx - vx/length*(radius+5), cy - vy/length*(radius+5))
        d.line((*origin, *endpoint), fill=(*CYAN, round(210*amount)), width=2)
        d.ellipse((origin[0]-4, origin[1]-4, origin[0]+4, origin[1]+4), fill=(*WHITE, round(255*amount)))
    # Broad, soft-looking concentric shadow remains entirely outside the glass.
    for spread, opacity in ((17, 8), (12, 17), (7, 40)):
        d.ellipse((left-spread, top-spread+5, left+diameter+spread, top+diameter+spread+5),
                  fill=(0, 3, 8, round(opacity*amount)))
    layer.alpha_composite(crop, (left, top))
    d = ImageDraw.Draw(layer)
    d.ellipse((left-5, top-5, left+diameter+5, top+diameter+5),
              outline=(*TEAL, round(180*amount)), width=2)
    d.ellipse((left-1, top-1, left+diameter+1, top+diameter+1),
              outline=(*CYAN, round(250*amount)), width=5)
    d.arc((left+7, top+7, left+diameter-7, top+diameter-7), 211, 293,
          fill=(*WHITE, round(210*amount)), width=2)
    label = event.get("label", "")
    if label and amount > .7:
        la = round(255 * smooth((amount-.7)/.3))
        box = d.textbbox((0, 0), label, font=FONTS[24])
        tw = box[2] - box[0] + 34
        ly = max(145, top - 48)
        d.rounded_rectangle((cx-tw/2, ly, cx+tw/2, ly+36), radius=12,
                            fill=(*BG, la), outline=(*CYAN, la), width=1)
        text_center(d, (cx, ly+18), label, 24, (*WHITE, la))
    return Image.alpha_composite(base, layer)


def draw_flow_strip(base, cfg, t):
    segments = cfg.get("flow_steps", [])
    current = next((f for f in segments if f["start"] <= t < f["end"]), None)
    if current is None:
        return base
    vis = min(smooth((t-current["start"])/.22), smooth((current["end"]-t)/.22))
    # Keep a shared strip steady across contiguous changes in active step.
    if any(abs(s["end"]-current["start"]) < .04 for s in segments):
        vis = max(vis, smooth((current["end"]-t)/.22))
    if any(abs(s["start"]-current["end"]) < .04 for s in segments):
        vis = max(vis, smooth((t-current["start"])/.22))
    layer = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(layer)
    labels = current.get("labels", cfg.get("flow_labels", ["步骤一", "步骤二", "步骤三"]))
    if len(labels) != 3:
        raise ValueError("Each flow strip must have exactly three labels.")
    widths = [210, 245, 245]
    lefts = [112, 391, 701]
    for i, (label, left, width) in enumerate(zip(labels, lefts, widths)):
        selected = i == int(current["active"])
        d.rounded_rectangle((left, 805, left+width, 850), radius=13,
                            fill=(*( (20, 79, 94) if selected else (15, 37, 45)), round(255*vis)),
                            outline=(*(CYAN if selected else (40, 77, 89)), round(255*vis)),
                            width=2 if selected else 1)
        text_center(d, (left+width/2, 827.5), label, 24,
                    (*(WHITE if selected else (121, 162, 174)), round(255*vis)))
    for ax in (356, 669):
        d.line((ax-17, 828, ax+15, 828), fill=(*CYAN, round(190*vis)), width=2)
        d.line((ax+7, 820, ax+15, 828, ax+7, 836), fill=(*CYAN, round(190*vis)), width=2)
    return Image.alpha_composite(base, layer)


def render_frame(raw_source, cfg, t):
    source = raw_source.copy()
    # Omit the captured browser/address strip before either overview or crop.
    top_mask = int(cfg.get("source_top_mask", 0))
    if top_mask:
        ImageDraw.Draw(source).rectangle((0, 0, source.width, top_mask), fill=BG)
    panel = source.resize((W, PANEL_H), Image.Resampling.LANCZOS)
    base = Image.new("RGBA", (W, H), (*BG, 255))
    base.paste(panel, (0, PANEL_Y))
    active = [(e, visibility(e, t)) for e in cfg.get("events", [])]
    active = [(e, a) for e, a in active if a > 0]
    dim_levels = {"lens": .18, "spotlight": .34, "underline": .025, "pulse": .035}
    dim = max((a * dim_levels.get(e.get("kind"), .055) for e, a in active), default=0)
    if dim:
        dim_layer = Image.new("RGBA", (W, H))
        ImageDraw.Draw(dim_layer).rectangle((0, PANEL_Y, W, PANEL_Y+PANEL_H), fill=(0, 6, 10, round(255*dim)))
        base = Image.alpha_composite(base, dim_layer)
    for event, amount in active:
        rect = rect_at(event, t)
        kind = event.get("kind", "focus")
        if kind == "spotlight":
            # Restore the target from this frame's original panel; the surrounding
            # frame stays gently dimmed. No synthetic or cached replacement image.
            x, y, rw, rh = mapped_rect(rect, source.size)
            mask = Image.new("L", (W, H))
            ImageDraw.Draw(mask).rounded_rectangle((x-8, y-8, x+rw+8, y+rh+8), radius=10,
                                                   fill=round(255*amount))
            mask = mask.filter(ImageFilter.GaussianBlur(5))
            clean = Image.new("RGBA", (W, H), (*BG, 255))
            clean.paste(panel, (0, PANEL_Y))
            base = Image.composite(clean, base, mask)
        base = draw_target(base, rect, amount, source.size, kind, t, event)
        if kind == "lens":
            base = draw_magnifier(base, source, rect, event, t, amount)
    base = draw_flow_strip(base, cfg, t)
    return base.convert("RGB")


def run_json(command):
    result = subprocess.run(command, capture_output=True, check=True)
    return json.loads(result.stdout)


def source_metadata(cfg):
    result = run_json([cfg["ffprobe"], "-v", "error", "-select_streams", "v:0",
                       "-show_entries", "stream=width,height,avg_frame_rate,sample_aspect_ratio:stream_tags=rotate:stream_side_data=rotation:format=duration",
                       "-of", "json", cfg["source"]])
    if not result.get("streams"):
        raise ValueError("Source contains no video stream.")
    metadata = result["streams"][0]
    metadata["duration"] = float(result["format"]["duration"])
    return metadata


def tool_path(name, cfg, config_dir):
    """Resolve explicit config first, then local runtime, then PATH."""
    explicit = cfg.get(name)
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute():
            candidate = config_dir / candidate
        if candidate.is_file():
            return str(candidate.resolve())
        found = shutil.which(str(explicit))
        if found:
            return str(Path(found).resolve())
        raise ValueError(f"Configured {name} was not found: {explicit}")
    runtime_root = os.environ.get("AI_CUT_ROOT") or os.environ.get("TALKING_HEAD_EDITOR_ROOT")
    if runtime_root:
        for executable in (name + ".exe", name):
            candidate = Path(runtime_root).expanduser() / ".runtime" / "ffmpeg" / "bin" / executable
            if candidate.is_file():
                return str(candidate.resolve())
    found = shutil.which(name)
    if found:
        return str(Path(found).resolve())
    raise ValueError(f"{name} unavailable: set config {name}, PATH, or AI_CUT_ROOT (legacy alias: TALKING_HEAD_EDITOR_ROOT).")


def load_config(config_path):
    cfg = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(cfg, dict):
        raise ValueError("Config must be a JSON object.")
    if not isinstance(cfg.get("source"), str) or not cfg["source"]:
        raise ValueError("Config requires source path.")
    source = Path(cfg["source"]).expanduser()
    if not source.is_absolute():
        source = config_path.parent / source
    if not source.is_file():
        raise ValueError(f"Source does not exist: {source}")
    cfg["source"] = str(source.resolve())
    for name in ("ffmpeg", "ffprobe"):
        cfg[name] = tool_path(name, cfg, config_path.parent)
    return cfg


def finite_number(value, label, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be >= {minimum}.")
    return float(value)


def validate_config(cfg, metadata):
    """Read-only structural and cadence audit; never invent or retime an effect."""
    duration = finite_number(cfg.get("duration"), "duration", 0.000001)
    source_start = finite_number(cfg.get("source_start"), "source_start", 0)
    speed = finite_number(cfg.get("speed", 1.2), "speed", 0.000001)
    fps = finite_number(cfg.get("fps", 30), "fps", 1)
    if fps != int(fps):
        raise ValueError("fps must be an integer.")
    width, height = metadata["width"], metadata["height"]
    if abs(width / height - 16 / 9) > 0.001:
        raise ValueError("This layout requires a 16:9 source; adapt the layout explicitly instead of stretching it.")
    if metadata.get("sample_aspect_ratio", "1:1") not in ("1:1", "N/A", "0:1"):
        raise ValueError("This layout requires square source pixels (SAR 1:1).")
    rotations = [metadata.get("tags", {}).get("rotate", 0)]
    rotations += [side.get("rotation", 0) for side in metadata.get("side_data_list", [])]
    if any(abs(float(rotation) % 360) > 1e-7 for rotation in rotations):
        raise ValueError("Rotated sources require explicit orientation/layout adaptation before this helper.")
    if source_start + duration * speed > metadata["duration"] + speed / fps:
        raise ValueError("Requested source interval extends past the video duration.")
    mask = finite_number(cfg.get("source_top_mask", 0), "source_top_mask", 0)
    if mask != int(mask) or mask >= height:
        raise ValueError("source_top_mask must be an integer smaller than source height.")
    events = cfg.get("events", [])
    if not isinstance(events, list):
        raise ValueError("events must be an array.")
    for index, event in enumerate(events):
        label = f"events[{index}]"
        if not isinstance(event, dict) or event.get("kind") not in EFFECT_KINDS:
            raise ValueError(f"{label}.kind must be one of {sorted(EFFECT_KINDS)}.")
        start = finite_number(event.get("start"), label + ".start", 0)
        end = finite_number(event.get("end"), label + ".end", 0)
        if end <= start or end > duration + 1e-7:
            raise ValueError(f"{label} must satisfy 0 <= start < end <= duration.")
        for key in ("ramp", "sweep", "crop_padding", "diameter"):
            if key in event:
                finite_number(event[key], label + "." + key, 0.000001)
        if "center" in event:
            center = event["center"]
            if not isinstance(center, list) or len(center) != 2:
                raise ValueError(f"{label}.center must contain two output-pixel coordinates.")
            for coordinate in center:
                finite_number(coordinate, label + ".center")
        keyframes = event.get("rect_keyframes")
        if not isinstance(keyframes, list) or not keyframes:
            raise ValueError(f"{label} requires rect_keyframes.")
        last_time = -1.0
        for frame in keyframes:
            if not isinstance(frame, dict):
                raise ValueError(f"{label}.rect_keyframes must contain objects.")
            time = finite_number(frame.get("time"), label + ".keyframe.time", 0)
            if time <= last_time or time > duration + 1e-7:
                raise ValueError(f"{label} keyframe times must strictly increase within duration.")
            last_time = time
            x = finite_number(frame.get("x"), label + ".x", 0)
            y = finite_number(frame.get("y"), label + ".y", 0)
            rw = finite_number(frame.get("w"), label + ".w", 0.000001)
            rh = finite_number(frame.get("h"), label + ".h", 0.000001)
            if x + rw > width + 1e-7 or y + rh > height + 1e-7:
                raise ValueError(f"{label} rectangle exceeds source pixel bounds.")
        if keyframes[0]["time"] > start + 1e-7 or keyframes[-1]["time"] < end - 1e-7:
            raise ValueError(f"{label} keyframes must cover the entire event interval.")
        if "path" in event:
            points = event["path"]
            if event["kind"] != "flow" or not isinstance(points, list) or len(points) < 2:
                raise ValueError(f"{label}.path requires kind=flow and at least two points.")
            for point in points:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError(f"{label}.path point must contain source x,y.")
                px = finite_number(point[0], label + ".path.x", 0)
                py = finite_number(point[1], label + ".path.y", 0)
                if px > width or py > height:
                    raise ValueError(f"{label}.path exceeds source pixel bounds.")
            if not any(a != b for a, b in zip(points, points[1:])):
                raise ValueError(f"{label}.path must have nonzero length.")
    flow_steps = cfg.get("flow_steps", [])
    if not isinstance(flow_steps, list):
        raise ValueError("flow_steps must be an array.")
    previous_end = -1.0
    for index, step in enumerate(flow_steps):
        label = f"flow_steps[{index}]"
        if not isinstance(step, dict):
            raise ValueError(f"{label} must be an object.")
        start = finite_number(step.get("start"), label + ".start", 0)
        end = finite_number(step.get("end"), label + ".end", 0)
        if start < previous_end - 1e-7 or end <= start or end > duration + 1e-7:
            raise ValueError(f"{label} must be chronological, nonoverlapping, and within duration.")
        previous_end = end
        if type(step.get("active")) is not int or step["active"] not in (-1, 0, 1, 2):
            raise ValueError(f"{label}.active must be -1, 0, 1, or 2.")
        labels = step.get("labels", cfg.get("flow_labels"))
        if not isinstance(labels, list) or len(labels) != 3 or not all(isinstance(x, str) and x.strip() for x in labels):
            raise ValueError(f"{label} requires three content-specific labels (or config.flow_labels).")
    starts = sorted(float(event["start"]) for event in events)
    intervals = list(zip(starts, starts[1:]))
    uncovered = [(a, b) for a, b in intervals if b-a > 3+1e-7]
    if starts and starts[0] > 3+1e-7:
        uncovered.insert(0, (0.0, starts[0]))
    if starts and duration-starts[-1] > 3+1e-7:
        uncovered.append((starts[-1], duration))
    warnings = []
    if not starts:
        warnings.append("No practical effects were supplied; this is not an approved enhanced section.")
    if uncovered:
        warnings.append("Effect onset cadence exceeds 3 seconds in reported intervals; inspect semantics and edit the plan explicitly.")
    if fps != 30:
        warnings.append("This helper has been verified at 30 fps; validate the requested frame rate before delivery.")
    return {"valid": True, "renderer_revision": RENDERER_REVISION,
            "layout": "1080x1080; 16:9 panel at y=180, h=608",
            "event_count": len(events), "effect_kinds": sorted(set(e["kind"] for e in events)),
            "onset_max_gap_seconds": max((b-a for a, b in intervals), default=None),
            "cadence_over_3s": uncovered, "cadence_ok": bool(starts) and not uncovered,
            "warnings": warnings, "source": cfg["source"], "source_metadata": metadata,
            "audio": "SILENT graphics layer; parent workflow must composite audio/subtitles/logo."}


def prepare_output(out, protected, force):
    """A new/empty directory by default; explicit force never permits input replacement."""
    out = out.resolve()
    if out.exists() and not out.is_dir():
        raise ValueError("Output path must be a directory.")
    if out.exists() and any(out.iterdir()) and not force:
        raise ValueError("Output directory is not empty. Choose a new revision directory or use explicit --force.")
    # Guard all predictable output names, including previews and log files.
    for path in protected:
        path = path.resolve()
        if path.parent == out and (path.name in {"graphics-silent.mp4", "graphics-manifest.json", "decode.log", "encode.log"}
                                   or path.name.startswith("preview-")):
            raise ValueError(f"Output would overwrite an input: {path}")
    if out.exists():
        for path in out.iterdir():
            generated_name = (path.name in {"graphics-silent.mp4", "graphics-manifest.json", "decode.log", "encode.log"}
                              or path.name.startswith("preview-"))
            if generated_name and path.is_symlink():
                raise ValueError(f"Refusing an output symlink: {path}")
            if generated_name and path.exists():
                for source_path in protected:
                    if source_path.exists() and path.samefile(source_path):
                        raise ValueError(f"Output aliases an input file: {path}")
    out.mkdir(parents=True, exist_ok=True)
    return out


def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        part = stream.read(count-len(result))
        if not part:
            break
        result.extend(part)
    return bytes(result)


def extract_frame(cfg, metadata, t):
    seek = float(cfg["source_start"]) + t*float(cfg.get("speed", 1.2))
    result = subprocess.run([cfg["ffmpeg"], "-hide_banner", "-loglevel", "error",
                             "-ss", f"{seek:.9f}", "-i", cfg["source"], "-map", "0:v:0",
                             "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                            capture_output=True, check=True)
    return Image.frombytes("RGB", (metadata["width"], metadata["height"]), result.stdout)


def write_manifest(cfg, out, metadata, times, config_path, range_start, duration, video=None):
    manifest = {"revision": RENDERER_REVISION, "renderer": str(Path(__file__).resolve()),
                "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "config": str(Path(config_path).resolve()),
                "config_sha256": hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
                "source": cfg["source"], "source_metadata": metadata,
                "source_start": cfg["source_start"], "duration": cfg["duration"],
                "render_range_start": range_start, "render_range_duration": duration,
                "decoded_source_start": float(cfg["source_start"])+range_start*float(cfg.get("speed", 1.2)),
                "event_time_origin": "whole practical section; unaffected by render range",
                "speed": cfg.get("speed", 1.2), "fps": cfg.get("fps", 30),
                "current_frame_crop": True, "audio": "silent; mixed by parent workflow",
                "preview_times": times, "events": cfg.get("events", []),
                "flow_steps": cfg.get("flow_steps", []),
                "validation": cfg.get("_validation"),
                "flow_labels": cfg.get("flow_labels", ["步骤一", "步骤二", "步骤三"])}
    if video:
        manifest["rendered_video"] = str(video.resolve())
        manifest["rendered_video_sha256"] = hashlib.sha256(video.read_bytes()).hexdigest()
        manifest["rendered_frames"] = round(duration*int(cfg.get("fps", 30)))
    (out / "graphics-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out-dir", help="New/empty revision directory; not needed for --validate-only")
    parser.add_argument("--validate-only", action="store_true", help="Read-only config/source/cadence audit; writes nothing")
    parser.add_argument("--force", action="store_true", help="Explicitly permit replacement of renderer output files in out-dir")
    parser.add_argument("--stills-only", action="store_true")
    parser.add_argument("--preview-times", help="Comma-separated times on the whole practical section")
    parser.add_argument("--range-start", type=float, default=0.0)
    parser.add_argument("--range-duration", type=float)
    args = parser.parse_args()
    config_path = Path(args.config).expanduser().resolve()
    try:
        cfg = load_config(config_path)
        metadata = source_metadata(cfg)
        cfg["_validation"] = validate_config(cfg, metadata)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    print(json.dumps(cfg["_validation"], ensure_ascii=False), flush=True)
    if args.validate_only:
        return
    if not args.out_dir:
        parser.error("--out-dir is required for rendering.")
    try:
        out = prepare_output(Path(args.out_dir), [Path(cfg["source"]), config_path, Path(__file__)], args.force)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    full_duration = float(cfg["duration"])
    fps = int(cfg.get("fps", 30))
    range_start = float(args.range_start)
    duration = args.range_duration if args.range_duration is not None else full_duration-range_start
    if not math.isfinite(range_start) or not math.isfinite(duration) or range_start < 0 or duration <= 0 or range_start+duration > full_duration+1e-7:
        parser.error("Render range must be positive and lie within config duration.")
    if abs(range_start*fps-round(range_start*fps)) > .001:
        parser.error("Range start must align with a video frame.")
    duration = round(duration*fps)/fps
    range_end = range_start+duration
    if duration <= 0 or range_end > full_duration+1/fps/2:
        parser.error("Rounded render range must contain frames and fit within config duration.")
    if args.preview_times:
        preview_times = [float(t.strip()) for t in args.preview_times.split(",") if t.strip()]
    elif cfg.get("preview_times"):
        preview_times = cfg["preview_times"]
        if not args.stills_only:
            preview_times = preview_times[:6]
    else:
        events = cfg.get("events", [])
        preview_times = []
        if events:
            first = events[0]
            preview_times += [first["start"]+.13, (first["start"]+first["end"])/2, first["end"]-.13]
            preview_times += [(e["start"]+e["end"])/2 for e in events[1:4]]
        preview_times += [range_start+duration*x for x in (.15, .3, .5, .7, .85, .95)]
        preview_times = preview_times[:6]
    if not all(isinstance(t, (int, float)) and math.isfinite(t) for t in preview_times):
        parser.error("Preview times must be finite numbers.")
    preview_times = [float(t) for t in preview_times if range_start <= float(t) < range_end]
    if not preview_times:
        preview_times = [range_start+duration/2]
    preview_times = [max(range_start, min(range_end-1/fps, t)) for t in preview_times]
    write_manifest(cfg, out, metadata, preview_times, args.config, range_start, duration)
    for index, t in enumerate(preview_times):
        raw = extract_frame(cfg, metadata, t)
        render_frame(raw, cfg, t).save(out / f"preview-{index+1:02d}-{t:.3f}s.png")
    print(json.dumps({"previews": str(out), "times": preview_times}, ensure_ascii=False), flush=True)
    if args.stills_only:
        return
    count = round(duration*fps)
    decode_log = (out / "decode.log").open("wb")
    encode_log = (out / "encode.log").open("wb")
    ffmpeg = cfg["ffmpeg"]
    decoder = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "warning", "-threads", "2",
                                "-ss", str(float(cfg["source_start"])+range_start*float(cfg.get("speed", 1.2))),
                                "-i", cfg["source"], "-map", "0:v:0",
                                "-an", "-vf", f"setpts=(PTS-STARTPTS)/{cfg.get('speed', 1.2)},fps={fps}",
                                "-frames:v", str(count), "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"],
                               stdout=subprocess.PIPE, stderr=decode_log)
    encoder = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "warning", "-y",
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1080", "-r", str(fps),
                                "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", cfg.get("preset", "medium"),
                                "-crf", str(cfg.get("crf", 19)), "-pix_fmt", "yuv420p", "-threads", "4",
                                "-movflags", "+faststart", str(out / "graphics-silent.mp4")],
                               stdin=subprocess.PIPE, stderr=encode_log)
    bytecount = metadata["width"]*metadata["height"]*3
    completed = 0
    try:
        for i in range(count):
            data = read_exact(decoder.stdout, bytecount)
            if len(data) != bytecount:
                raise RuntimeError(f"Source ended at {i}/{count} frames ({len(data)} bytes).")
            source = Image.frombytes("RGB", (metadata["width"], metadata["height"]), data)
            rendered = render_frame(source, cfg, range_start+i/fps)
            encoder.stdin.write(rendered.tobytes())
            completed += 1
            if (i+1) % 150 == 0:
                print(f"Rendered {i+1}/{count} frames", flush=True)
        encoder.stdin.close()
        decoder.stdout.close()
        decode_rc = decoder.wait()
        encode_rc = encoder.wait()
        if decode_rc or encode_rc:
            raise RuntimeError(f"FFmpeg failed: decode={decode_rc} encode={encode_rc}; see logs.")
    except BaseException:
        decoder.kill()
        encoder.kill()
        raise
    finally:
        decode_log.close()
        encode_log.close()
    print(json.dumps({"video": str(out / "graphics-silent.mp4"), "frames": completed,
                      "duration": completed/fps, "range_start": range_start}, ensure_ascii=False), flush=True)
    write_manifest(cfg, out, metadata, preview_times, args.config, range_start, duration,
                   out / "graphics-silent.mp4")


if __name__ == "__main__":
    main()
