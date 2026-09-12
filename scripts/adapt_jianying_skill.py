"""Verify the pinned upstream installation and install only our scoped entry.

First acquire the upstream bundle with Codex's skill-installer. This script
does not download, run installers, edit user drafts, or install dependencies.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from install_extensions import ROOT, git_blob, inside, sha256


def adapt(target: Path, check: bool = False):
    target = target.resolve(strict=True)
    lock = json.loads((ROOT / "extensions/jianying-source-lock.json").read_text(encoding="utf-8-sig"))
    manifest_path = target / "local-adapter.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if previous.get("manager") != "talking-head-editor-jianying":
            raise ValueError("Unrecognized local adapter; preserve the existing entry")
        for relative, expected in previous["files"].items():
            if sha256(inside(target, relative).read_bytes()) != expected:
                raise ValueError(f"User-modified adapter preserved: {relative}")

    original = None
    for relative, expected in lock["git_blobs"].items():
        actual = "UPSTREAM_SKILL.md" if relative == "SKILL.md" and manifest_path.exists() else relative
        data = inside(target, actual).read_bytes()
        if git_blob(data) != expected:
            data = data.replace(b"\r\n", b"\n")
        if git_blob(data) != expected:
            raise ValueError(f"Pinned upstream file differs: {relative}")
        if relative == "SKILL.md":
            original = data
    if original is None:
        raise ValueError("Missing pinned upstream entry")

    desired = {"UPSTREAM_SKILL.md": original,
               "SKILL.md": (ROOT / "skill-adapters/jianying-editor/SKILL.md").read_bytes()}
    if not manifest_path.exists() and (target / "UPSTREAM_SKILL.md").exists():
        if (target / "UPSTREAM_SKILL.md").read_bytes() != original:
            raise ValueError("Existing upstream archive differs; preserve it")
    receipt = {"manager": "talking-head-editor-jianying", "repository": lock["repository"],
               "commit": lock["commit"], "source_root": str(ROOT),
               "verified_upstream_files": len(lock["git_blobs"]),
               "files": {key: sha256(value) for key, value in desired.items()},
               "native_open_export": "See current project evidence; installation is not verification"}
    if not check:
        for relative, data in desired.items():
            inside(target, relative).write_bytes(data)
        manifest_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"check_only": check, "target": str(target), **receipt}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=Path.home() / ".codex/skills/jianying-editor")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(adapt(args.target, args.check), ensure_ascii=False, indent=2))
