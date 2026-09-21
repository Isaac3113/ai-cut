"""Plan and audit explicit video/subtitle filenames without renaming history."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

def typed_stem(stem, kind):
    if kind not in {"视频", "字幕"}:
        raise ValueError("Unknown delivery type")
    p = Path(stem)
    name = p.name
    if not name or name != name.strip() or name.endswith("."):
        raise ValueError("A non-empty filename stem without trailing dots/spaces is required")
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        raise ValueError("Use a valid Windows filename stem; do not silently replace characters")
    if name.lower().endswith((".mp4", ".mov", ".txt", ".srt", ".json")):
        raise ValueError("Pass a stem, not a filename with an extension")
    if name in {"视频", "字幕"}:
        return p.with_name(kind)
    while re.search(r"_(视频|字幕)$", name):
        name = re.sub(r"_(视频|字幕)$", "", name)
    if not name:
        raise ValueError("Missing video title")
    return p.with_name(name + "_" + kind)

def delivery_paths(stem):
    video = typed_stem(stem, "视频")
    captions = typed_stem(stem, "字幕")
    return {"video": Path(str(video)+".mp4"), "txt": Path(str(captions)+".txt"),
            "srt": Path(str(captions)+".srt")}

def _sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()

def audit_delivery(stem):
    paths = delivery_paths(stem)
    missing = [str(p) for p in paths.values() if not p.is_file() or p.stat().st_size == 0]
    if missing:
        raise ValueError("Missing or empty typed deliverables: " + ", ".join(missing))
    return {"naming_rule": "0.2.9", "files": {
        k: {"path": str(p.resolve()), "bytes": p.stat().st_size, "sha256": _sha256(p)}
        for k,p in paths.items()},
        "verified": ["typed_filenames", "required_files_exist_and_nonempty"],
        "not_verified": ["video_decode", "caption_sync", "human_watch_and_listen"]}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-stem", required=True, type=Path)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    try:
        result = audit_delivery(args.output_stem) if args.audit else {
            k: str(p) for k,p in delivery_paths(args.output_stem).items()}
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc)+"\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
