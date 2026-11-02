from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import os
import sys
from pathlib import Path

from . import __version__, assets, project
from .util import ROOT, EditorError, require, read_json, atomic_json, executable, run, load_job, inside


def doctor():
    from .visuals import font_path
    result={"version":__version__,"python":sys.version,"root":str(ROOT),"font":str(font_path()),"packages":{}}
    for name in ("ffmpeg","ffprobe"):
        result[name]=run([executable(name),"-version"])[0].splitlines()[0]
    for name in ("Pillow","torch","torchaudio","funasr","modelscope"):
        try: result["packages"][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: result["packages"][name]="missing"
    try:
        import torch
        result["cuda_available"]=torch.cuda.is_available()
        if result["cuda_available"]: result["gpu"]=torch.cuda.get_device_name(0)
    except ImportError: result["cuda_available"]=False
    return result


def unlock(job,asr=False):
    job,_=load_job(job)
    path=job/(".asr.lock" if asr else ".edit.lock")
    if not path.exists(): return {"unlocked":False,"reason":"No lock"}
    raw=path.read_bytes(); info=json.loads(raw); pid=int(info["pid"])
    require(pid>0,"lock_pid","Invalid PID; inspect lock manually")
    if os.name=="nt":
        import ctypes
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel.OpenProcess.restype=ctypes.c_void_p
        handle=kernel.OpenProcess(0x1000,False,pid)
        if handle:
            kernel.CloseHandle.argtypes=[ctypes.c_void_p]; kernel.CloseHandle(handle)
            raise EditorError("process_alive","Lock owner still exists; do not unlock")
        require(ctypes.get_last_error()==87,"process_unknown","Cannot verify PID has exited")
    else:
        try: os.kill(pid,0)
        except ProcessLookupError: pass
        except PermissionError: raise EditorError("process_unknown","Cannot verify lock owner")
        else: raise EditorError("process_alive","Lock owner still exists")
    require(path.read_bytes()==raw,"lock_changed","Lock changed while checking PID")
    path.unlink()
    return {"unlocked":True,"exited_pid":pid}


def parser():
    p=argparse.ArgumentParser(description="AI Cut: local, versioned knowledge-video editing tools. Semantic decisions belong to the agent Skill.")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("doctor")
    def command(name):
        c=sub.add_parser(name); c.add_argument("--job",required=True,type=Path); return c
    c=command("init"); c.add_argument("--source",required=True,type=Path); c.add_argument("--script",type=Path); c.add_argument("--test-fixture",action="store_true")
    c=command("transcribe"); c.add_argument("--hotwords",type=Path); c.add_argument("--device",choices=["auto","cpu","cuda:0"],default="auto")
    c=command("import-transcript"); c.add_argument("--file",required=True,type=Path); c.add_argument("--provenance",required=True,choices=["user_verified","test_fixture"])
    c=command("inspect"); c.add_argument("--asset-id"); c.add_argument("--times",help="Comma-separated seconds")
    c=command("asset-index"); c.add_argument("--folder",required=True,type=Path)
    c=command("asset-add"); c.add_argument("--file",required=True,type=Path); c.add_argument("--metadata",type=Path)
    c=command("asset-review"); c.add_argument("--id",required=True); c.add_argument("--description",required=True); c.add_argument("--evidence",required=True)
    c=command("asset-approve-paid"); c.add_argument("--id",required=True); c.add_argument("--user-evidence",required=True)
    c=command("pexels-search"); c.add_argument("--query",required=True); c.add_argument("--type",choices=["video","image"],default="video"); c.add_argument("--limit",type=int,default=6)
    c=command("pexels-download"); c.add_argument("--candidate",required=True,type=Path)
    c=command("plan-export"); c.add_argument("--out",required=True,type=Path)
    c=command("plan-apply"); c.add_argument("--file",required=True,type=Path)
    c=command("restore"); c.add_argument("--revision",required=True,type=int); c.add_argument("--expected",required=True,type=int)
    c=command("profile-approve"); c.add_argument("--user-evidence",required=True); c.add_argument("--name",default="default")
    c=command("profile-use"); c.add_argument("--name",default="default")
    c=command("render"); c.add_argument("--mode",choices=["rough","preview","draft","final"],default="preview"); c.add_argument("--retry",action="store_true")
    command("qa"); command("status"); command("source-qa"); command("source-profile")
    c=command("workflow-review"); c.add_argument("--file",required=True,type=Path)
    command("workflow-status")
    c=command("unlock"); c.add_argument("--asr",action="store_true")
    c=command("review"); c.add_argument("--file",required=True,type=Path)
    c=command("review-progress"); c.add_argument("--file",required=True,type=Path)
    c=command("audio-controls"); c.add_argument("--out",required=True,type=Path)
    c=command("package"); c.add_argument("--out",required=True,type=Path); c.add_argument("--draft",action="store_true"); c.add_argument("--audience",choices=["internal","external"],default="internal")
    return p


def dispatch(a):
    c=a.cmd
    if c=="doctor": return doctor()
    if c=="init": return project.create(a.job,a.source,a.script,a.test_fixture)
    if c=="transcribe":
        from .asr import transcribe
        words=[x.strip() for x in a.hotwords.read_text(encoding="utf-8-sig").splitlines() if x.strip()] if a.hotwords else None
        return transcribe(a.job,words,a.device)
    if c=="import-transcript": return project.install_transcript(a.job,read_json(a.file),a.provenance)
    if c=="inspect":
        job,p=load_job(a.job)
        path=inside(job,p["assets"][a.asset_id]["path"]) if a.asset_id else project.source_path(job,p)
        times=[float(x) for x in a.times.split(",")] if a.times else None
        return {"contact_sheet":assets.contact_sheet(job,path,a.asset_id or "source",times)}
    if c=="asset-index": return assets.index_folder(a.job,a.folder)
    if c=="asset-add": return assets.register(a.job,a.file,read_json(a.metadata) if a.metadata else None)
    if c=="asset-review": return assets.annotate(a.job,a.id,a.description,a.evidence)
    if c=="asset-approve-paid": return assets.approve_paid(a.job,a.id,a.user_evidence)
    if c=="pexels-search": return assets.pexels_search(a.job,a.query,a.type,a.limit)
    if c=="pexels-download": return assets.download_pexels(a.job,read_json(a.candidate))
    if c=="plan-export":
        from .timeline import default_plan
        job,p=load_job(a.job); plan=copy.deepcopy(p["plan"] or default_plan(p["source"]["duration"],p["revision"]))
        plan["base_revision"]=p["revision"]
        require(not a.out.exists(),"output_exists","Choose a new proposal file to preserve old edits")
        atomic_json(a.out,plan); return {"path":str(a.out),"revision":p["revision"]}
    if c=="plan-apply": return project.apply_plan(a.job,read_json(a.file))
    if c=="restore": return project.restore(a.job,a.revision,a.expected)
    if c=="profile-approve": return project.approve_style(a.job,a.user_evidence,a.name)
    if c=="profile-use": return project.use_profile(a.job,a.name)
    if c=="render":
        from .render import render
        return render(a.job,a.mode,a.retry)
    if c=="qa":
        from .quality import qa
        return qa(a.job)
    if c=="review":
        from .quality import record_review
        return record_review(a.job,read_json(a.file))
    if c=="review-progress":
        from .quality import record_progress
        return record_progress(a.job,read_json(a.file))
    if c=="audio-controls":
        from .audio_controls import export_tracks
        return export_tracks(a.job,a.out)
    if c=="package":
        from .quality import package
        return package(a.job,a.out,a.draft,a.audience)
    if c=="status": return project.status(a.job)
    if c=="source-qa": return project.audit_source(a.job)
    if c=="source-profile":
        from .workflow import source_profile
        return source_profile(a.job)
    if c=="workflow-review":
        from .workflow import record_packet
        return record_packet(a.job,read_json(a.file))
    if c=="workflow-status":
        from .workflow import workflow_status
        return workflow_status(a.job)
    if c=="unlock": return unlock(a.job,a.asr)


def main():
    if hasattr(sys.stdout,"reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    args=parser().parse_args()
    try:
        print(json.dumps({"ok":True,"result":dispatch(args)},ensure_ascii=False,indent=2,allow_nan=False))
    except (EditorError,FileNotFoundError,ValueError,KeyError) as e:
        print(json.dumps({"ok":False,"error":getattr(e,"code",type(e).__name__),"message":str(e)},ensure_ascii=False),file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
