from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class EditorError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise EditorError(code, message)


def number(value, name, minimum=0):
    require(isinstance(value, (float, int)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= minimum,
            "invalid_number", f"{name} must be finite and >= {minimum}")
    return float(value)


def ident(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value),
            "invalid_id", "IDs must contain only letters, digits, underscores or hyphens")
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(tmp, path)


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inside(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    require(path.is_relative_to(root) and path != root,
            "unsafe_path", f"Path must remain inside project: {relative}")
    return path


def copy_media(source, job, category="media"):
    source = Path(source).resolve()
    require(source.is_file(), "missing_media", f"File not found: {source}")
    sha = file_hash(source)
    suffix = source.suffix.lower()
    require(re.fullmatch(r"\.[a-z0-9]{1,8}", suffix), "media_extension", "Unsupported file extension")
    relative = f"{category}/{sha}{suffix}"
    target = inside(job, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        tmp = target.with_suffix(suffix + ".partial")
        shutil.copyfile(source, tmp)
        require(file_hash(tmp) == sha, "source_changed", "Source changed while being copied")
        os.replace(tmp, target)
    else:
        require(file_hash(target) == sha, "media_changed", "Existing managed media was modified")
    return {"path": relative, "sha256": sha, "name": source.name}


def runtime_config():
    path = ROOT / "runtime.local.json"
    return read_json(path) if path.exists() else {}


def executable(name):
    config = runtime_config()
    candidate = os.environ.get("THE_" + name.upper()) or config.get(name)
    candidate = candidate or str(ROOT / ".runtime" / "ffmpeg" / "bin" / (name + (".exe" if os.name == "nt" else "")))
    if not Path(candidate).is_file():
        candidate = shutil.which(name)
    require(candidate, "missing_dependency", f"{name} unavailable; run scripts/bootstrap.ps1")
    return str(candidate)


def run(args, *, cwd=None, timeout=1800, log=None):
    if Path(str(args[0])).stem.lower()=="ffmpeg":
        args=[args[0],"-threads","2","-filter_threads","2",*args[1:]]
    proc = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    require(proc.returncode == 0, "process_failed", f"Process exit {proc.returncode}: " + (proc.stderr[-2200:] or proc.stdout[-2200:]))
    return proc.stdout, proc.stderr


def probe(path):
    out, _ = run([executable("ffprobe"), "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
    return json.loads(out)


def streams(info, kind):
    return [x for x in info["streams"] if x.get("codec_type") == kind]


@contextlib.contextmanager
def job_lock(job, name=".edit.lock"):
    job = Path(job)
    require(name in (".edit.lock",".asr.lock"),"lock_name","Unknown lock name")
    lock = job / name
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise EditorError("job_locked", f"Another edit may be running. Inspect {lock}; use unlock only after verifying its PID has exited.")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump({"pid": os.getpid(), "created": time.time()}, f)
        yield
    finally:
        lock.unlink(missing_ok=True)


def load_job(job):
    job = Path(job).resolve()
    data = read_json(job / "project.json")
    require(data.get("schema_version") == 1, "schema_version", "Unsupported project schema")
    return job, data


def save_revision(job, project, *, expected, event):
    current = read_json(Path(job) / "project.json")
    require(current["revision"] == expected, "revision_conflict", "Project changed; read status and rebase your edit")
    project["revision"] = expected + 1
    project["updated_at"] = time.time()
    project["event"] = event
    project["delivery"] = None
    historical=Path(job) / "history" / f"r{project['revision']:06d}.json"
    require(not historical.exists(),"history_conflict","A prior interrupted save left this history revision; inspect it before recovery, never overwrite history")
    atomic_json(historical, project)
    atomic_json(Path(job) / "project.json", project)
    return project
