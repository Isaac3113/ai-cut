"""Build a staged Jianying candidate from an existing verified render and audio stems.

Run in a fresh process. This command neither registers a live draft nor opens,
renders or exports in Jianying. Native compatibility requires separate checks.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from talking_head_editor import __version__
from talking_head_editor.jianying import build_project


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("job", "native-blank", "output", "output-root", "audio-stems"):
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--vendor-root", type=Path, default=Path.home() /
                        ".codex/skills/jianying-editor/scripts/vendor/pyJianYingDraft")
    parser.add_argument("--vendor-lock", type=Path, default=ROOT / "extensions/jianying-core-lock.json")
    parser.add_argument("--ffprobe", type=Path, default=ROOT / ".runtime/ffmpeg/bin/ffprobe.exe")
    args = vars(parser.parse_args())
    manifest = build_project(**args, engine_src=ROOT / "src")
    print(json.dumps({"version": __version__, "output": str(args["output"].resolve()),
                      "status": manifest["status"], "revision": manifest["revision"],
                      "duration_seconds": manifest["duration_us"] / 1e6,
                      "validation": manifest["structural_validation"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
