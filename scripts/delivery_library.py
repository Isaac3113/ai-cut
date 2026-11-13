"""Read-only plans and audits for the shared AIVD delivery library.

This module never reserves an ID, creates directories, copies media, or changes
the registry. The caller must recheck the plan before an authorized delivery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"AIVD-(\d{3})")
NAME_RE = re.compile(r"(AIVD-\d{3}) - (.+?) - (.+)")
INDEX_ROW_RE = re.compile(r"^\|\s*(AIVD-\d{3})\s*\|", re.MULTILINE)
RESERVED = {"AIVD-005", "AIVD-006"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".ts"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
SUBTITLE_EXTENSIONS = {".srt", ".txt", ".vtt", ".ass", ".ssa"}
PUBLICATION_NAMES = {"Facebook文案.txt", "小红书文案.txt", "第一评论.txt", "一键复制.txt"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
GROUPS = {
    "01_语音": ("voice", AUDIO_EXTENSIONS),
    "02_数字人": ("presenter", {".mp4"}),
    "03_口播内容": ("spoken_text", {".txt", ".md"}),
    "04_剪辑成片": ("video", VIDEO_EXTENSIONS),
}


def _publication_text(path):
    path = Path(path)
    if path.suffix.lower() not in {".txt", ".md"}:
        return False
    stem = path.stem.casefold()
    names = {Path(value).stem.casefold() for value in PUBLICATION_NAMES} | {"首条留言", "首评"}
    return any(stem == name or stem.endswith(tuple(separator + name for separator in ("_", " - ", "-")))
               for name in names)


def _delivery_target(project, *parts):
    target = project.joinpath(*parts)
    if not target.resolve().is_relative_to(project.resolve()):
        raise ValueError(f"Delivery target points outside the project: {target}")
    return target


def _supporting_file(project, stem, kind, source):
    folder, (_, extensions) = next((name, value) for name, value in GROUPS.items() if value[0] == kind)
    path = Path(source).resolve()
    if path.suffix.lower() not in extensions or _publication_text(path):
        raise ValueError(f"Select a supported {kind} delivery file; publication copy is excluded")
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Selected {kind} file is missing or empty: {path}")
    if kind == "spoken_text":
        try:
            if not path.read_text(encoding="utf-8-sig").strip():
                raise ValueError(f"Selected spoken_text file contains no text: {path}")
        except UnicodeError as exc:
            raise ValueError(f"Selected spoken_text must be UTF-8 text: {path}") from exc
    suffix = {"voice": "语音", "presenter": "数字人原片", "spoken_text": "口播内容"}[kind]
    target = _delivery_target(project, "AI 成片", folder, stem + "_" + suffix + path.suffix.lower())
    return {"kind": kind, "source": str(path), "target": str(target), "bytes": path.stat().st_size}


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read JSON source {path}: {exc}") from exc


def _number(identifier):
    match = ID_RE.fullmatch(str(identifier))
    if not match or int(match[1]) == 0:
        raise ValueError(f"Expected an AIVD ID with three digits: {identifier}")
    return int(match[1])


def _component(value, label):
    if (not isinstance(value, str) or not value or value != value.strip()
            or value.endswith((".", " ")) or re.search(r'[<>:"/\\|?*\x00-\x1f]', value)):
        raise ValueError(f"Use a valid Windows {label}; characters are not silently replaced")
    return value


def _name(identifier, source_label, title):
    _number(identifier)
    _component(source_label, "source label")
    _component(title, "short title")
    if " - " in source_label:
        raise ValueError("Source label cannot contain the project-name separator")
    return _component(f"{identifier} - {source_label} - {title}", "project name")


def _parse_name(name):
    match = NAME_RE.fullmatch(name)
    if not match:
        raise ValueError(f"Expected AIVD-NNN - source - short title: {name}")
    identifier, source_label, title = match.groups()
    _name(identifier, source_label, title)
    return identifier, source_label, title


def _outside_onedrive(path, env):
    path = Path(path).resolve()
    roots = [Path(env[k]).resolve() for k in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial") if env.get(k)]
    return not (any(path == root or path.is_relative_to(root) for root in roots)
                or any(p.casefold() == "onedrive" or p.casefold().startswith("onedrive - ") for p in path.parts))


def resolve_settings(library_root=None, registry=None, asset_index=None, work_root=None, *, repo=ROOT, env=None):
    """Explicit arguments > named environment settings > runtime.local.json."""
    repo = Path(repo).resolve()
    env = os.environ if env is None else env
    local = repo / "runtime.local.json"
    config = _json(local) if local.is_file() else {}
    if not isinstance(config, dict):
        raise ValueError("runtime.local.json must contain an object")
    values = {}
    for key, argument, variable in (
        ("library_root", library_root, "TALKING_HEAD_DELIVERY_LIBRARY_ROOT"),
        ("registry", registry, "TALKING_HEAD_DELIVERY_REGISTRY"),
        ("asset_index", asset_index, "TALKING_HEAD_DELIVERY_ASSET_INDEX"),
    ):
        config_key = {"library_root": "delivery_library_root", "registry": "delivery_registry",
                      "asset_index": "delivery_asset_index"}[key]
        value = argument if argument is not None else env.get(variable) or config.get(config_key)
        if value is None or not str(value).strip():
            raise ValueError(f"Missing {config_key}; pass --{key.replace('_', '-')} or {variable}")
        values[key] = Path(value).resolve()
    if not values["library_root"].is_dir():
        raise ValueError(f"Delivery library does not exist: {values['library_root']}")
    for key in ("registry", "asset_index"):
        if not values[key].is_file():
            raise ValueError(f"Required {key} does not exist: {values[key]}")
    if (values["library_root"] == repo or values["library_root"].is_relative_to(repo)
            or repo.is_relative_to(values["library_root"])):
        raise ValueError("Delivery library must be separate from the active code repository")
    values["repo"] = repo
    values["work_root"] = Path(work_root or env.get("TALKING_HEAD_VIDEO_WORK_ROOT")
                               or config.get("video_work_root") or repo / "work/videos").resolve()
    library_root = values["library_root"]
    if (values["work_root"] == library_root or values["work_root"].is_relative_to(library_root)
            or library_root.is_relative_to(values["work_root"])):
        raise ValueError("Work/cache and delivery library must not overlap or contain one another")
    if not _outside_onedrive(repo, env) or not _outside_onedrive(values["work_root"], env):
        raise ValueError("Active code and work/cache must remain outside OneDrive")
    return values


def _catalog(settings):
    registry = _json(settings["registry"])
    if not isinstance(registry, dict) or not isinstance(registry.get("Projects"), list):
        raise ValueError("Registry must contain a Projects array")
    reserved = RESERVED | set(registry.get("ReservedIDs", []))
    for identifier in reserved:
        _number(identifier)
    floor = _number(registry.get("NextNewID", "AIVD-001"))
    rows = {}
    root = settings["library_root"]
    for row in registry["Projects"]:
        if not isinstance(row, dict):
            raise ValueError("Registry project rows must be objects")
        identifier = row.get("ID")
        _number(identifier)
        if identifier in rows or identifier in reserved:
            raise ValueError(f"Duplicate or reserved registry ID: {identifier}")
        name = row.get("DestinationName", "")
        parsed_id, source, _ = _parse_name(name)
        if parsed_id != identifier or row.get("SourceLabel") != source:
            raise ValueError(f"Registry name/source disagrees with ID: {identifier}")
        destination = Path(row.get("DestinationProject", "")).resolve()
        if destination.parent != root or destination.name != name:
            raise ValueError(f"Registry destination escapes or disagrees with the delivery library: {identifier}")
        rows[identifier] = row
    directories = {}
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith("AIVD-"):
            continue
        identifier, _, _ = _parse_name(path.name)
        if identifier in reserved or identifier in directories:
            raise ValueError(f"Reserved or duplicate library ID: {identifier}")
        if not path.resolve().is_relative_to(root):
            raise ValueError(f"Project directory points outside the library: {path}")
        directories[identifier] = path
        if identifier in rows and path.resolve() != Path(rows[identifier]["DestinationProject"]).resolve():
            raise ValueError(f"Directory and registry disagree for {identifier}; inspect before reuse")
    index_text = settings["asset_index"].read_text(encoding="utf-8-sig")
    indexed = set(INDEX_ROW_RE.findall(index_text))
    for identifier in indexed:
        _number(identifier)
    used = (set(rows) | set(directories) | indexed) - reserved
    next_number = max(floor, max((_number(x) for x in used), default=0) + 1)
    while next_number <= 999 and f"AIVD-{next_number:03d}" in reserved:
        next_number += 1
    if next_number > 999:
        raise ValueError("The three-digit AIVD range is exhausted")
    return {"rows": rows, "directories": directories, "reserved": reserved,
            "used": used, "indexed": indexed, "next_id": f"AIVD-{next_number:03d}"}


def _path_identity(value):
    return str(Path(value).resolve()).casefold()


def _existing(selector, settings, catalog):
    selector = str(selector)
    if ID_RE.fullmatch(selector):
        identifier = selector
        _number(identifier)
        if identifier in catalog["reserved"]:
            raise ValueError(f"Reserved ID cannot be used: {identifier}")
        row = catalog["rows"].get(identifier)
        path = Path(row["DestinationProject"]) if row else catalog["directories"].get(identifier)
        if path is None:
            raise ValueError(f"Unknown existing ID: {identifier}")
        return path.resolve(), row
    matches = [row for row in catalog["rows"].values()
               if selector == row.get("OriginalName")
               or (row.get("OriginalProject") and _path_identity(selector) == _path_identity(row["OriginalProject"]))]
    if len(matches) != 1:
        raise ValueError("Existing selector must uniquely match a full OriginalName, OriginalProject, or unified AIVD-NNN ID; legacy numbers are not inferred")
    return Path(matches[0]["DestinationProject"]).resolve(), matches[0]


def _work_entry(row, settings, name):
    if row is None:
        return {"work_directory": str(settings["work_root"] / name / "04_剪辑工程"),
                "work_basis": "new-project plan only; directory not created"}
    original = row.get("OriginalProject")
    result = {"original_project": original, "work_directory": None,
              "work_basis": "existing original entry; frozen cache ID is never inferred from the new display name"}
    if not original:
        return result
    pointer = Path(original) / "04_剪辑工程" / "本机剪辑工程.md"
    result["work_entry"] = str(pointer)
    result["work_entry_exists"] = pointer.is_file()
    if pointer.is_file():
        for line in pointer.read_text(encoding="utf-8-sig").splitlines():
            value = line.strip().strip('`')
            if re.match(r"^[A-Za-z]:[\\/]", value) or value.startswith("/"):
                result["work_directory"] = value
                result["work_directory_exists"] = Path(value).is_dir()
                break
    return result


def plan(settings, *, title=None, source_label=None, existing=None, stem_suffix=None, subtitles=(),
         layout="legacy", voice=None, presenter=None, spoken_text=None):
    if layout not in {"legacy", "grouped"}:
        raise ValueError("Delivery layout must be legacy or grouped")
    if layout != "grouped" and any(value is not None for value in (voice, presenter, spoken_text)):
        raise ValueError("Supporting files require the explicit grouped delivery layout")
    catalog = _catalog(settings)
    row = None
    if existing is not None:
        destination, row = _existing(existing, settings, catalog)
        identifier, source, actual_title = _parse_name(destination.name)
        if title is not None and title != actual_title:
            raise ValueError("Existing title conflict; do not rename or reassign another work")
        if source_label is not None and source_label != source:
            raise ValueError("Keep the existing principal source label; re-editing does not change it")
    else:
        identifier = catalog["next_id"]
        source = source_label or "Codex剪辑"
        actual_title = _component(title, "short title")
        destination = settings["library_root"] / _name(identifier, source, actual_title)
        for name in [r["DestinationName"] for r in catalog["rows"].values()] + [p.name for p in catalog["directories"].values()]:
            _, old_source, old_title = _parse_name(name)
            if (source, actual_title) == (old_source, old_title):
                raise ValueError("This source/title already exists; identify it explicitly with --existing")
        if destination.exists():
            raise ValueError("New-project destination already exists; inspect and use --existing")
    if destination.parent.resolve() != settings["library_root"]:
        raise ValueError("Planned project must be a direct child of the delivery library")
    stem = destination.name
    if stem_suffix is not None:
        stem += "_" + _component(stem_suffix, "stem suffix")
    subtitle_paths = []
    extensions = set()
    for value in subtitles:
        path = Path(value).resolve()
        extension = path.suffix.lower()
        if extension not in SUBTITLE_EXTENSIONS or _publication_text(path):
            raise ValueError("Only explicitly selected existing subtitle files may go in the project root; publication TXT is excluded")
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Existing subtitle is missing or empty: {path}")
        if extension in extensions:
            raise ValueError("Select at most one existing subtitle of each extension; conflicting versions need explicit review")
        extensions.add(extension)
        subtitle_paths.append({"source": str(path), "target": str(_delivery_target(destination, stem + "_字幕" + extension)),
                               "bytes": path.stat().st_size})
    supporting_files = [_supporting_file(destination, stem, kind, value)
                        for kind, value in (("voice", voice), ("presenter", presenter), ("spoken_text", spoken_text))
                        if value is not None]
    video_parts = ("AI 成片", "04_剪辑成片") if layout == "grouped" else ("AI 成片",)
    work = _work_entry(row, settings, destination.name)
    if existing is not None and row is None:
        work = {"work_directory": None, "work_basis": "existing library ID has no original-work mapping; do not infer or create a replacement cache"}
    return {"planned_only": True, "id_reserved": False, "project_id": identifier,
            "source_label": source, "title": actual_title, "project_name": destination.name,
            "project_directory": str(destination), "project_exists": destination.is_dir(),
            "next_available_id": catalog["next_id"], "reserved_ids": sorted(catalog["reserved"]),
            "layout": layout, "supporting_files": supporting_files,
            "video_path": str(_delivery_target(destination, *video_parts, stem + "_视频.mp4")),
            "cover_paths": {ratio: str(_delivery_target(destination, "参考图", destination.name + "_封面_" + label + ".png"))
                            for ratio, label in (("16:9", "16比9"), ("9:16", "9比16"))},
            "subtitles": subtitle_paths, "publication_materials_archived": False,
            "directories_created": [], "work": work,
            "sources": {k: str(settings[k]) for k in ("library_root", "registry", "asset_index")},
            "warning": "No ID was registered or reserved. Recheck directory/index/registry before an authorized delivery."}


def audit(settings, *, existing, include_hash=False):
    catalog = _catalog(settings)
    project, row = _existing(existing, settings, catalog)
    if not project.is_dir():
        raise ValueError(f"Mapped project directory does not exist: {project}")
    files, unexpected, empty_directories = [], [], []
    candidates = []

    def collect(path, kind, extensions):
        if (path.is_file() and path.resolve().is_relative_to(project)
                and path.suffix.lower() in extensions and not _publication_text(path)):
            candidates.append((path, kind))
        else:
            unexpected.append(str(path))

    for path in project.iterdir():
        if not path.resolve().is_relative_to(project):
            unexpected.append(str(path)); continue
        if path.is_dir() and path.name in {"参考图", "AI 成片"}:
            children = list(path.iterdir())
            if not children:
                empty_directories.append(str(path))
            for child in children:
                if (path.name == "AI 成片" and child.is_dir() and child.name in GROUPS
                        and child.resolve().is_relative_to(project)):
                    grouped_files = list(child.iterdir())
                    if not grouped_files:
                        empty_directories.append(str(child))
                    kind, extensions = GROUPS[child.name]
                    for grouped_file in grouped_files:
                        collect(grouped_file, kind, extensions)
                else:
                    collect(child, "image" if path.name == "参考图" else "video",
                            IMAGE_EXTENSIONS if path.name == "参考图" else VIDEO_EXTENSIONS)
        elif path.is_file() and path.suffix.lower() in SUBTITLE_EXTENSIONS and not _publication_text(path):
            candidates.append((path, "subtitle"))
        else:
            unexpected.append(str(path))
    for path, kind in sorted(candidates):
        record = {"path": str(path), "kind": kind, "bytes": path.stat().st_size}
        if include_hash:
            with path.open("rb") as stream:
                record["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
        files.append(record)
    empty_files = [f["path"] for f in files if f["bytes"] == 0]
    has_video = any(f["kind"] == "video" and f["bytes"] > 0 for f in files)
    return {"read_only": True, "project_id": _parse_name(project.name)[0],
            "project_directory": str(project), "layout_valid": not (unexpected or empty_directories or empty_files),
            "has_nonempty_video": has_video, "delivery_state": "video_present_not_quality_verified" if has_video else "no_current_video_found",
            "registry_has_video": row.get("HasVideo") if row else None,
            "files": files, "unexpected_paths": unexpected, "empty_directories": empty_directories,
            "empty_files": empty_files, "hashes_checked": include_hash,
            "not_verified": ["video_decode", "latest_version_identity", "content_quality", "human_watch_and_listen", "OneDrive_cloud_sync"]}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("plan", "audit"):
        command = commands.add_parser(action)
        command.add_argument("--library-root", type=Path)
        command.add_argument("--registry", type=Path)
        command.add_argument("--asset-index", type=Path)
        command.add_argument("--work-root", type=Path)
        command.add_argument("--existing", required=action == "audit")
        if action == "plan":
            command.add_argument("--title")
            command.add_argument("--source-label")
            command.add_argument("--stem-suffix")
            command.add_argument("--subtitle", action="append", default=[], type=Path)
            command.add_argument("--layout", choices=("legacy", "grouped"), default="legacy",
                                 help="Optional grouped deliverables; default preserves the existing flat video layout")
            command.add_argument("--voice", type=Path, help="Selected existing audio delivery; requires --layout grouped")
            command.add_argument("--presenter", type=Path, help="Selected existing clean presenter MP4; requires --layout grouped")
            command.add_argument("--spoken-text", type=Path, help="Selected existing UTF-8 final spoken TXT/MD; requires --layout grouped")
        else:
            command.add_argument("--hash", action="store_true", dest="include_hash")
    args = parser.parse_args()
    try:
        settings = resolve_settings(args.library_root, args.registry, args.asset_index, args.work_root)
        result = (plan(settings, title=args.title, source_label=args.source_label, existing=args.existing,
                       stem_suffix=args.stem_suffix, subtitles=args.subtitle, layout=args.layout,
                       voice=args.voice, presenter=args.presenter, spoken_text=args.spoken_text) if args.action == "plan"
                  else audit(settings, existing=args.existing, include_hash=args.include_hash))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Delivery library: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
