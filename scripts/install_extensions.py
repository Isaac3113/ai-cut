"""Install reviewed, pinned upstream skill bundles plus narrowly scoped local entries.

Download with Codex's official skill-installer first; this script never runs
downloaded setup files or installs runtime packages. No secret files are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def inside(root, relative):
    parts = PurePosixPath(relative).parts
    if not parts or ".." in parts or PurePosixPath(relative).is_absolute() or any(":" in p for p in parts):
        raise ValueError(f"Unsafe relative path: {relative}")
    if any(p == ".git" or p.startswith(".env") or p == "__pycache__" for p in parts):
        raise ValueError(f"Excluded path: {relative}")
    target = root.joinpath(*parts)
    if not target.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in [root, target, *target.parents] if p.is_relative_to(root)):
        raise ValueError(f"Symlink or escaped path: {relative}")
    return target


def prepare(staging, spec):
    source = staging / spec["name"]
    result = {}
    for relative, expected in spec["git_blobs"].items():
        data = inside(source, relative).read_bytes()
        if git_blob(data) != expected:
            # Git autocrlf on Windows. Accept only bytes which reproduce the
            # exact upstream blob after CRLF normalization; never arbitrary edits.
            data = data.replace(b"\r\n", b"\n")
        if git_blob(data) != expected:
            raise ValueError(f"Upstream mismatch: {spec['name']}/{relative}")
        destination = "UPSTREAM_SKILL.md" if relative == "SKILL.md" else relative
        if relative != "SKILL.md" and relative.endswith("/SKILL.md"):
            # Keep optional Manim reference without registering an extra skill.
            destination = relative[:-len("SKILL.md")] + "REFERENCE.md"
        result[destination] = data
    for path in (ROOT / "skill-adapters" / spec["name"]).rglob("*"):
        if path.is_file():
            relative = path.relative_to(ROOT / "skill-adapters" / spec["name"]).as_posix()
            inside(source, relative)  # validate destination without reading it
            result[relative] = path.read_bytes()
    if "SKILL.md" not in result or "UPSTREAM_SKILL.md" not in result:
        raise ValueError("Incomplete skill entry")
    return result


def check_existing(target, name, desired):
    if not target.exists():
        return
    if target.is_symlink():
        raise ValueError(f"Refusing symlink target: {target}")
    manifest = target / "installation.json"
    if not manifest.is_file():
        raise ValueError(f"Existing unmanaged skill preserved: {target}")
    old = json.loads(manifest.read_text(encoding="utf-8"))
    if old.get("manager") != "talking-head-editor-extensions" or old.get("name") != name:
        raise ValueError(f"Unrecognized installation: {target}")
    for relative, expected in old["files"].items():
        file = inside(target, relative)
        if not file.is_file() or sha256(file.read_bytes()) != expected:
            raise ValueError(f"User-modified installed file preserved: {file}")
    if set(old["files"]) - set(desired):
        raise ValueError("Upgrade would leave obsolete files; reconcile explicitly")
    for relative in desired:
        file = inside(target, relative)
        if file.exists() and relative not in old["files"]:
            raise ValueError(f"Unmanaged installed file preserved: {file}")


def install(staging, destination, check=False):
    lock = json.loads((ROOT / "extensions/upstream-lock.json").read_text(encoding="utf-8"))
    prepared = []
    for spec in lock["skills"]:
        files = prepare(staging, spec)
        target = inside(destination, spec["name"])
        check_existing(target, spec["name"], files)
        prepared.append((spec, target, files))
    # Validate every source and existing target before the first write.
    reports = []
    for spec, target, files in prepared:
        manifest = {
            "manager": "talking-head-editor-extensions", "name": spec["name"],
            "source_root": str(ROOT), "repository": spec["repository"], "commit": spec["commit"],
            "upstream_path": spec["path"], "adaptation": spec["adaptation"],
            "files": {relative: sha256(data) for relative, data in files.items()},
        }
        if not check:
            check_existing(target, spec["name"], files)
            for relative, data in files.items():
                out = inside(target, relative)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(data)
                if out.read_bytes() != data:
                    raise ValueError(f"Install verification failed: {out}")
            (target / "installation.json").write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        reports.append({"skill": spec["name"], "files": len(files), "target": str(target), "mode": "preflight" if check else "installed_verified"})
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--target", type=Path, default=Path.home() / ".codex/skills")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(install(args.staging.resolve(), args.target.resolve(), args.check), ensure_ascii=False, indent=2))
