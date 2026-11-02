"""Install exact reviewed skill files; never overwrite an unrelated existing skill."""
import argparse
import json
import shutil
from pathlib import Path
from talking_head_editor.util import ROOT, file_hash, atomic_json, require

p=argparse.ArgumentParser(); p.add_argument("--target",type=Path,default=Path.home()/".codex/skills/ai-cut")
a=p.parse_args(); source=ROOT/"skill/ai-cut"; target=a.target.resolve()
manifest=target/"installation.json"
if target.exists() and any(target.iterdir()):
    require(manifest.is_file() and Path(json.loads(manifest.read_text())["source_root"]).resolve()==ROOT,"existing_skill","Existing unrecognized skill preserved")
    old=json.loads(manifest.read_text())
    for path,sha in old["files"].items():
        require((target/path).is_file() and file_hash(target/path)==sha,"skill_modified","Installed skill was modified; reconcile before updating")
files={}
for path in source.rglob("*"):
    if not path.is_file() or "__pycache__" in path.parts: continue
    relative=path.relative_to(source); dest=target/relative
    dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,dest)
    require(file_hash(dest)==file_hash(path),"install_hash","Installed bytes mismatch")
    files[relative.as_posix()]=file_hash(dest)
atomic_json(manifest,{"source_root":str(ROOT),"files":files})
print(json.dumps({"installed":str(target),"verified_files":len(files)},ensure_ascii=False))
