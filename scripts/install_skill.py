"""Install exact reviewed skill files; never overwrite an unrelated existing skill."""
import argparse
import json
import shutil
from pathlib import Path
from talking_head_editor.util import ROOT, file_hash, atomic_json, require

p=argparse.ArgumentParser()
p.add_argument("--skill", choices=("ai-cut", "video-publish"), default="ai-cut")
p.add_argument("--target",type=Path)
a=p.parse_args(); source=ROOT/"skill"/a.skill
target=(a.target or Path.home()/".codex/skills"/a.skill).resolve()
require(source.is_dir(), "skill_source", "Requested skill source is missing")
manifest=target/"installation.json"
if target.exists() and any(target.iterdir()):
    require(manifest.is_file() and Path(json.loads(manifest.read_text())["source_root"]).resolve()==ROOT,"existing_skill","Existing unrecognized skill preserved")
    old=json.loads(manifest.read_text())
    require(old.get("skill_name", "ai-cut")==a.skill,"existing_skill","Existing skill has a different identity; preserved")
    for path,sha in old["files"].items():
        require((target/path).is_file() and file_hash(target/path)==sha,"skill_modified","Installed skill was modified; reconcile before updating")
files={}
for path in source.rglob("*"):
    if not path.is_file() or "__pycache__" in path.parts: continue
    relative=path.relative_to(source); dest=target/relative
    dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,dest)
    require(file_hash(dest)==file_hash(path),"install_hash","Installed bytes mismatch")
    files[relative.as_posix()]=file_hash(dest)
atomic_json(manifest,{"source_root":str(ROOT),"skill_name":a.skill,"files":files})
print(json.dumps({"skill":a.skill,"installed":str(target),"verified_files":len(files)},ensure_ascii=False))
