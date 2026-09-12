"""Local filmstrip + waveform review. Does not edit, transcribe or upload media."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from talking_head_editor.util import executable, probe, run, streams
from talking_head_editor.visuals import font_path


def strict_frames(video, start, end, n, dest_dir):
    paths = []
    for i, time in enumerate(np.linspace(start, end, n)):
        out = dest_dir / f"f_{i:03d}.jpg"
        run([executable("ffmpeg"), "-v", "error", "-xerror", "-ss", f"{time:.6f}", "-i", video,
             "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "4", "-n", out], timeout=120)
        if not out.is_file() or out.stat().st_size == 0:
            raise ValueError(f"Missing frame at {time:.6f}s")
        paths.append(out)
    return paths


def strict_envelope(video, start, end, samples=2000):
    cmd = [executable("ffmpeg"), "-threads", "2", "-v", "error", "-xerror", "-ss", str(start),
           "-i", str(video), "-t", str(end-start), "-map", "0:a:0", "-vn", "-ac", "1",
           "-ar", "16000", "-f", "s16le", "pipe:1"]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError("Audio decode failed: " + result.stderr.decode("utf-8", errors="replace")[-1800:])
    pcm = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768
    if not pcm.size:
        raise ValueError("Empty audio decode; cannot infer silence")
    expected = round((end - start) * 16000)
    tolerance = max(2, round(min(0.05, (end - start) * 0.05) * 16000))
    if abs(pcm.size - expected) > tolerance:
        raise ValueError(f"Incomplete audio range: expected {expected / 16000:.3f}s, decoded {pcm.size / 16000:.3f}s")
    envelope = np.array([np.sqrt(np.mean(chunk**2)) if chunk.size else 0 for chunk in np.array_split(pcm, samples)])
    return envelope / envelope.max() if envelope.max() else envelope


def review(video, start, end, output, skill_root, transcript=None):
    video, output = video.resolve(), output.resolve()
    report_path = output.with_suffix(".review.json")
    if not video.is_file() or output.suffix.lower() != ".png":
        raise ValueError("Existing video and a new .png output are required")
    if output.exists() or report_path.exists():
        raise ValueError("Output exists; choose a new review filename")
    info = probe(video)
    duration = float(info["format"]["duration"])
    if not streams(info, "video") or not streams(info, "audio"):
        raise ValueError("Filmstrip review requires both video and audio streams")
    if not all(math.isfinite(t) for t in (start, end, duration)) or not (0 <= start < end < duration):
        raise ValueError("Require 0 <= start < end < duration (end frame must exist)")
    if end - start > 60:
        raise ValueError("Review one local decision point at a time, at most 60 seconds")
    helper = skill_root / "helpers/timeline_view.py"
    manifest = json.loads((skill_root / "installation.json").read_text(encoding="utf-8"))
    expected = manifest["files"]["helpers/timeline_view.py"]
    actual = hashlib.sha256(helper.read_bytes()).hexdigest()
    if actual != expected or manifest.get("manager") != "talking-head-editor-extensions":
        raise ValueError("Installed helper changed; audit before executing")
    spec = importlib.util.spec_from_file_location("video_use_timeline_review", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.FONT_CANDIDATES.insert(0, str(font_path()))
    module.extract_frames = strict_frames
    module.compute_envelope = strict_envelope
    # A transcript gap is not proof of actual acoustic silence. Disable upstream
    # silence labels; show decoded waveform and optional aligned words only.
    module.find_silences = lambda *a, **kw: []
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="local-video-review-") as tmp:
        transcript_path = None
        if transcript:
            data = json.loads(transcript.read_text(encoding="utf-8"))
            if not isinstance(data.get("words"), list):
                raise ValueError("Transcript requires words with start/end in this video's timebase")
            words = []
            for word in data["words"]:
                ws, we = float(word["start"]), float(word["end"])
                if not (math.isfinite(ws) and math.isfinite(we) and 0 <= ws <= we <= duration + .2):
                    raise ValueError("Invalid word timing; verify transcript timebase")
                words.append({**word, "type": "word", "start": ws, "end": we})
            transcript_path = Path(tmp) / "words.json"
            transcript_path.write_text(json.dumps({"words": sorted(words, key=lambda w: w["start"])}), encoding="utf-8")
        temp_image = Path(tmp) / "review.png"
        module.render_timeline(video, start, end, temp_image, n_frames=8, transcript=transcript_path)
        with output.open("xb") as stream:
            stream.write(temp_image.read_bytes())
    report = {"video": str(video), "range_seconds": [start, end], "frames": 8,
              "ffmpeg": executable("ffmpeg"), "helper_sha256": actual, "audio_decode": "passed",
              "transcript": str(transcript) if transcript else None, "timebase_verified": False,
              "listened": False, "human_visual_review": "pending",
              "limits": "Normalized waveform, not loudness. Frames are not full playback. No silence or 200ms sync verdict."}
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    return {"image": str(output), "report": str(report_path), "decoded": True, "listened": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--end", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path.home() / ".codex/skills/video-use")
    args = parser.parse_args()
    print(json.dumps(review(args.video, args.start, args.end, args.output, args.skill_root, args.transcript), ensure_ascii=False))
