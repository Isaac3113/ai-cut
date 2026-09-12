from __future__ import annotations

import copy
import os
import time
from pathlib import Path

from .timeline import default_plan, validate_plan, validate_transcript, critical_words, DEFAULT_STYLE, output_formats
from .util import (ROOT, require, read_json, atomic_json, copy_media, probe, streams,
                   job_lock, load_job, save_revision, inside, digest, file_hash, ident, run, executable)


def create(job, source, script=None, fixture=False):
    job = Path(job).resolve()
    require(not job.exists() or not any(job.iterdir()), "job_exists", "Choose a new empty project folder")
    info = probe(source)
    require(streams(info, "video") and streams(info, "audio"), "source_streams", "Real talking-head source needs video and audio tracks")
    duration = float(info["format"]["duration"])
    require(duration > .1, "empty_source", "Source video has no usable duration")
    job.mkdir(parents=True, exist_ok=True)
    source_record = copy_media(source, job)
    source_record.update(duration=duration, probe=info)
    project = {"schema_version": 1, "revision": 0, "created_at": time.time(),
               "source": source_record, "fixture": bool(fixture), "transcript": None,
               "assets": {}, "plan": None, "style_approval": None, "delivery": None,
               "event": "created"}
    if script:
        project["script"] = copy_media(script, job, "references")
    atomic_json(job / "project.json", project)
    atomic_json(job / "history" / "r000000.json", project)
    return {"job": str(job), "revision": 0, "duration": duration, "next": "transcribe"}


def source_path(job, project):
    p = inside(job, project["source"]["path"])
    require(p.is_file() and file_hash(p) == project["source"]["sha256"], "source_changed", "Managed source hash mismatch; original must remain unchanged")
    return p


def audit_source(job):
    with job_lock(job):
        job,p=load_job(job)
        source=source_path(job,p)
        report_path=job/"source-qa.json"
        if report_path.exists():
            report=read_json(report_path)
            if report.get("source_sha256")==p["source"]["sha256"] and report.get("full_decode_pass"):
                return {**report,"reused":True}
        run([executable("ffmpeg"),"-nostdin","-v","error","-xerror","-i",source,"-f","null","-"],
            timeout=max(300,int(p["source"]["duration"]*10)),log=job/"logs/source-decode.log")
        report={"source_sha256":p["source"]["sha256"],"full_decode_pass":True,"duration":p["source"]["duration"],
                "checked_at":time.time(),"visual_audio_review":"pending"}
        atomic_json(report_path,report)
        return report


def transcript(job, project):
    record = project.get("transcript")
    require(record, "transcription_required", "Run transcribe or import a verified word-timed transcript first")
    path = inside(job, record["path"])
    require(file_hash(path) == record["sha256"], "transcript_changed", "Transcript changed outside versioned workflow")
    return read_json(path)


def install_transcript(job, data, provenance, expected=None):
    with job_lock(job):
        job, p = load_job(job)
        source_path(job, p)
        if expected is not None:
            require(p["revision"] == expected, "revision_conflict", "Project changed during transcription")
        validate_transcript(data, p["source"]["duration"])
        require(provenance in ("funasr", "user_verified", "test_fixture"), "transcript_provenance", "Record transcript origin")
        require(provenance != "test_fixture" or p["fixture"], "fixture_only", "Test transcripts cannot enter real projects")
        data = {**data, "provenance": provenance, "source_sha256": p["source"]["sha256"]}
        path = job / "transcripts" / (digest(data) + ".json")
        atomic_json(path, data)
        p["transcript"] = {"path": path.relative_to(job).as_posix(), "sha256": file_hash(path), "provenance": provenance}
        p["plan"] = None
        p = save_revision(job, p, expected=p["revision"], event="transcribed")
        proposal = default_plan(p["source"]["duration"], p["revision"])
        atomic_json(job / "proposal.json", proposal)
        critical = critical_words(data["words"])
        atomic_json(job / "review" / "transcript-brief.json", {"words": data["words"], "critical_words": critical,
                    "source_duration": p["source"]["duration"], "instruction": "Agent must review original audio/context; no automatic keyword deletion"})
        return {"revision": p["revision"], "words": len(data["words"]), "proposal": str(job / "proposal.json")}


def apply_plan(job, candidate):
    with job_lock(job):
        job, p = load_job(job)
        require(candidate.get("base_revision") == p["revision"], "revision_conflict", "Read project revision and update candidate base_revision")
        words = transcript(job, p)["words"]
        compiled = validate_plan(candidate, p["source"]["duration"], words, p["assets"])
        p["plan"] = candidate
        approved = p.get("style_approval")
        if approved and approved["style_hash"] != style_hash(candidate):
            p["style_approval"] = None
        p = save_revision(job, p, expected=candidate["base_revision"], event="plan_applied")
        folder=job/"edits"/f"r{p['revision']:06d}"
        atomic_json(folder/"edit-ledger.json",{"clips":candidate["clips"],"deletions":candidate.get("deletions",[]),
                    "caption_corrections":candidate.get("caption_corrections",{}),"caption_groups":candidate.get("caption_groups",[]),"semantic_review":candidate.get("semantic_review",{}),
                    "visual_effects":candidate.get("visual_effects",[]),"sound_effects":candidate.get("sound_effects",[]),"ending":candidate.get("ending"),"visual_rhythm":candidate.get("visual_rhythm")})
        atomic_json(folder/"asset-sources.json",p["assets"])
        return {"revision": p["revision"], "duration": sum(c["output_duration"] for c in compiled)+round(candidate.get("ending",{}).get("duration",0)*30)/30,
                "style_approved": bool(p["style_approval"]), "next": "render preview"}


def restore(job, revision, expected):
    with job_lock(job):
        job, current = load_job(job)
        historical = read_json(job / "history" / f"r{int(revision):06d}.json")
        require(historical["source"]["sha256"] == current["source"]["sha256"], "source_identity", "Cannot restore a different source")
        require(current["revision"] == expected, "revision_conflict", "Read current revision before restore")
        historical["revision"] = current["revision"]
        p = save_revision(job, historical, expected=expected, event=f"restored_from_r{revision}")
        return {"revision": p["revision"], "restored_from": revision, "next": "render; cached unchanged clips are reused"}


def style_hash(plan):
    return digest({**DEFAULT_STYLE, **plan.get("style", {})})


def approve_style(job, evidence, name="default"):
    require(evidence.strip(), "user_evidence", "Record the user's actual short-sample feedback")
    ident(name)
    with job_lock(job):
        job, p = load_job(job)
        require(p.get("plan"), "plan_required", "Create a plan first")
        require(not p["fixture"], "fixture_style", "Test media cannot establish the user's real style preference")
        receipt = read_json(job / "latest-render.json")
        require(receipt["revision"] == p["revision"] and receipt["mode"] in ("preview","draft"),
                "preview_required", "Generate the current plan preview or draft first")
        require(set(receipt["files"]) == set(output_formats(p["plan"],p["source"]["probe"])), "preview_formats", "Review the requested aspect ratios first")
        for record in receipt["files"].values():
            require(file_hash(inside(job, record["path"])) == record["sha256"], "preview_changed", "Preview bytes changed")
        approval = {"style_hash": style_hash(p["plan"]), "user_evidence": evidence,
                    "preview_fingerprint": receipt["fingerprint"], "approved_at": time.time()}
        p["style_approval"] = approval
        profile = {"schema_version": 1, "name": name, "style": p["plan"]["style"], "approval": approval}
        atomic_json(ROOT / ".runtime" / "profiles" / f"{name}.json", profile)
        save_revision(job, p, expected=p["revision"], event="style_approved")
        return {"revision": p["revision"], "profile": name}


def use_profile(job, name):
    ident(name)
    profile = read_json(ROOT / ".runtime" / "profiles" / f"{name}.json")
    with job_lock(job):
        job, p = load_job(job)
        require(p.get("plan"), "plan_required", "Apply the content plan first")
        require(profile.get("approval", {}).get("user_evidence"), "profile_approval", "Profile has not been user approved")
        p["plan"]["style"] = profile["style"]
        require(style_hash(p["plan"]) == profile["approval"]["style_hash"], "profile_changed", "Profile style changed after approval")
        p["style_approval"] = profile["approval"]
        save_revision(job, p, expected=p["revision"], event="profile_applied")
        return {"revision": p["revision"], "profile": name}


def status(job):
    job, p = load_job(job)
    latest = read_json(job / "latest-render.json") if (job / "latest-render.json").exists() else None
    next_step = "transcribe" if not p["transcript"] else "plan and inspect assets" if not p["plan"] else "render preview" if not p["style_approval"] and not p["fixture"] else "render final and qa"
    return {"job": str(job), "revision": p["revision"], "fixture": p["fixture"], "next": next_step,
            "duration": p["source"]["duration"], "transcribed": bool(p["transcript"]),
            "assets": len(p["assets"]), "plan_ready": bool(p["plan"]),
            "style_approved": bool(p["style_approval"]),
            "render": latest, "render_current": bool(latest and latest["revision"] == p["revision"]),
            "delivery": p.get("delivery"), "warning": "Rendering is not semantic or human acceptance"}
