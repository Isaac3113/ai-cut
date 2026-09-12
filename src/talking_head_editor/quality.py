from __future__ import annotations

import html
import json
import math
import re
import time
import zipfile
from fractions import Fraction
from pathlib import Path

from .assets import contact_sheet
from .project import source_path
from .timeline import output_formats
from .util import (atomic_json, inside, read_json, load_job, require, file_hash,
                   executable, run, probe, streams, job_lock)

REVIEW_CATEGORIES = ("meaning", "seams", "captions", "framing", "assets", "audio_sync")
QUALITY_CATEGORIES = ("full_watch", "full_listen", "full_captions", "privacy", "color", "overall")
QUALITY_STATES = ("pass", "fail", "unverified", "not_applicable")


def quality_check_template():
    """Unperformed inspection is not a failed inspection or an approval."""
    return {category: {"status": "unverified", "evidence": ""} for category in QUALITY_CATEGORIES}


def loudness_failures(loudness, style):
    """Check measured input audio, never loudnorm's hypothetical output values."""
    try:
        measured_i, measured_tp = float(loudness["input_i"]), float(loudness["input_tp"])
    except (KeyError, TypeError, ValueError):
        return ["Unmeasurable or silent output audio"]
    if not all(math.isfinite(v) for v in (measured_i, measured_tp)):
        return ["Unmeasurable or silent output audio"]
    failures = []
    target_i, target_tp = style.get("loudness_lufs", -16), style.get("true_peak_db", -1)
    if abs(measured_i-target_i) > 2:
        failures.append("Integrated loudness differs from target by >2 LU")
    if measured_tp > target_tp:
        failures.append(f"True peak {measured_tp:g} dBTP exceeds target {target_tp:g} dBTP")
    return failures


def validate_quality_review(review, q, r, *, require_complete=False):
    """Validate human evidence declarations; this does not perform human perception.

    The exact render fingerprint binds every item. Legacy six-category reviews
    may still be read, but only explicit new checks can satisfy final delivery.
    """
    require(review.get("fingerprint") == r["fingerprint"] and review.get("reviewer"),
            "review_identity", "Review must name reviewer and exact render fingerprint")
    require(q.get("fingerprint", None if require_complete else r["fingerprint"]) == r["fingerprint"],
            "qa_required", "Quality evidence needs the same QA/render fingerprint")
    duration = r["expected_duration"]
    for aspect in r["files"]:
        checks = review.get("variants", {}).get(aspect, {}).get("quality_checks", {})
        require(isinstance(checks, dict) and not set(checks)-set(QUALITY_CATEGORIES),
                "quality_review_schema", "Use supported quality_checks categories")
        for category in QUALITY_CATEGORIES:
            item = checks.get(category)
            if item is None and not require_complete:
                continue
            require(isinstance(item, dict), "quality_review_incomplete", f"{aspect}/{category} has not been reviewed")
            status = item.get("status")
            require(status in QUALITY_STATES, "quality_review_status", f"{aspect}/{category}: use {QUALITY_STATES}")
            evidence = item.get("evidence", "")
            require(isinstance(evidence, str), "quality_review_evidence", "Evidence must be text")
            if status != "unverified":
                require(evidence.strip(), "quality_review_evidence", f"{aspect}/{category} needs actual inspection evidence")
            if status == "not_applicable":
                no_captions = category == "full_captions" and q["variants"][aspect].get("caption_count") == 0
                require(category in ("privacy", "color") or no_captions,
                        "quality_review_not_applicable", f"{aspect}/{category} cannot be skipped")
                require(isinstance(item.get("reason"), str) and item["reason"].strip(),
                        "quality_review_evidence", "Explain why this check does not apply")
            if require_complete:
                require(status in ("pass", "not_applicable"), "quality_review_incomplete",
                        f"{aspect}/{category} is {status}; final delivery remains blocked")
            if status != "pass":
                continue
            if category in ("full_watch", "full_listen"):
                modes = ("continuous_video", "continuous_av") if category == "full_watch" else ("continuous_audio", "continuous_av")
                require(item.get("mode") in modes, "quality_review_mode",
                        f"{aspect}/{category} needs continuous inspection, not frames or waveform")
                span = item.get("range_seconds")
                require(isinstance(span, list) and len(span) == 2 and
                        all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in span) and
                        0 <= span[0] <= .04 and span[0] < span[1] and duration-.04 <= span[1] <= duration+.04,
                        "quality_review_coverage", f"{aspect}/{category} must cover the entire current output")
            if category == "full_captions":
                count = item.get("reviewed_cue_count")
                total = q["variants"][aspect].get("caption_count")
                require(item.get("mode") == "all_captions", "quality_review_mode", "Review every caption cue")
                require(type(count) is int and type(total) is int and count == total and total >= 0,
                        "quality_caption_coverage", "Caption count must match current QA; rerun legacy QA if the count is missing")


def current_render(job):
    job, p = load_job(job)
    r = read_json(job / "latest-render.json")
    require(r.get("complete") and r["revision"] == p["revision"], "stale_render", "Render the current project revision first")
    expected = set(output_formats(p["plan"],p["source"]["probe"])) if "requested_formats" in r else {"landscape","portrait"}
    require(set(r["files"]) == expected, "missing_variant", "All requested variants must exist")
    for f in r["files"].values():
        require(inside(job,f["path"]).is_file() and file_hash(inside(job,f["path"])) == f["sha256"], "render_changed", "Rendered bytes differ from receipt")
    return job, p, r


def qa(job):
    with job_lock(job):
        job, p, r = current_render(job)
        source_path(job,p)
        report = {"schema_version":1,"fingerprint":r["fingerprint"],"revision":p["revision"],
                  "fixture":p["fixture"],"created_at":time.time(),"variants":{},
                  "manual_review":"pending", "limitations":[
                      "Silence/freeze/black detectors flag candidates, not editorial errors.",
                      "Container timing does not prove lip sync or speech recognition accuracy.",
                      "The <=200ms caption target needs audio-verified manual checkpoints."]}
        root = job / "review" / r["fingerprint"]
        root.mkdir(parents=True, exist_ok=True)
        for aspect, record in r["files"].items():
            path = inside(job,record["path"])
            info = probe(path)
            v, a = streams(info,"video"), streams(info,"audio")
            failures = []
            if len(v)!=1 or len(a)!=1:
                failures.append("Expected one video and one audio stream")
            else:
                if (v[0].get("width"),v[0].get("height")) != (record["width"],record["height"]):
                    failures.append("Incorrect resolution")
                if v[0].get("codec_name")!="h264" or a[0].get("codec_name")!="aac":
                    failures.append("Incorrect codecs")
                if abs(float(Fraction(v[0].get("avg_frame_rate","0/1")))-30) > .001:
                    failures.append("Incorrect frame rate")
                duration = float(info["format"]["duration"])
                if abs(duration-r["expected_duration"])>.12:
                    failures.append("Duration mismatch >120ms")
                av_duration_delta = abs(float(v[0].get("duration",duration))-float(a[0].get("duration",duration)))
                av_start_delta = abs(float(v[0].get("start_time",0))-float(a[0].get("start_time",0)))
                if av_duration_delta>.12 or av_start_delta>.08:
                    failures.append("Audio/video stream timing mismatch")
            # -xerror makes decode failures fatal. Detectors process the entire output.
            args = [executable("ffmpeg"),"-hide_banner","-nostdin","-xerror","-i",path,
                    "-vf","blackdetect=d=0.15:pix_th=0.08,freezedetect=n=-50dB:d=2",
                    "-af","silencedetect=noise=-45dB:d=0.8,loudnorm=I=-16:TP=-1:LRA=11:print_format=json",
                    "-f","null","-"]
            _, logs = run(args, timeout=max(300,int(r["expected_duration"]*10)), log=root/f"{aspect}-decode.log")
            detections = [line.strip() for line in logs.splitlines() if any(x in line for x in
                          ("black_start:","freeze_start:","freeze_end:","silence_start:","silence_end:"))]
            matches = re.findall(r'\{\s*"input_i"[\s\S]*?\}',logs)
            loudness = json.loads(matches[-1]) if matches else {}
            style = p["plan"].get("style", {})
            failures.extend(loudness_failures(loudness, style))
            cues_path = path.parent/"captions.json"
            cues = read_json(cues_path)
            for cue in cues:
                if not (0 <= cue["start"] < cue["end"] <= r["expected_duration"]+.04):
                    failures.append("Caption outside timeline")
                if len(cue["lines"])>2 or cue["max_line_width"]>record["width"]*.85:
                    failures.append("Caption exceeds safe width")
            times = sorted(set([.1, max(.1,r["expected_duration"]/2), max(.1,r["expected_duration"]-.15)]+
                               [max(.01,c["output_start"]+d) for c in r["clips"][1:] for d in (-.08,.08)]))
            sheets=[contact_sheet(job,path,"qa-"+aspect+"-"+r["fingerprint"][:12]+f"-{i//24+1}",times[i:i+24]) for i in range(0,len(times),24)]
            excerpts = []
            for i,c in enumerate(r["clips"][1:]):
                start=max(0,c["output_start"]-.8)
                dest=root/f"{aspect}-seam-{i+1:03d}.mp4"
                run([executable("ffmpeg"),"-hide_banner","-loglevel","error","-nostdin","-y",
                     "-ss",start,"-i",path,"-t",min(1.6,r["expected_duration"]-start),
                     "-vf","scale=-2:540","-c:v","libx264","-preset","ultrafast","-threads","2",
                     "-c:a","aac",dest])
                excerpts.append({"at":c["output_start"],"path":dest.relative_to(job).as_posix()})
            report["variants"][aspect]={"sha256":record["sha256"],"technical_pass":not failures,
                "failures":failures,"detections":detections,"loudness":loudness,
                "audio_targets":{"loudness_lufs":style.get("loudness_lufs",-16),"true_peak_db":style.get("true_peak_db",-1)},
                "caption_count":len(cues),
                "contact_sheet":sheets[0],"contact_sheets":sheets,"seam_excerpts":excerpts,"captions_sha256":file_hash(cues_path),
                "subtitle_sha256":file_hash(inside(job,record["subtitles"])),
                "ass_sha256":file_hash(path.parent/"captions.ass")}
        report["technical_pass"]=all(x["technical_pass"] for x in report["variants"].values())
        atomic_json(root/"qa.json",report)
        atomic_json(job/"latest-qa.json",report)
        template={"fingerprint":r["fingerprint"],"reviewer":"", "variants":{a:{
            "checks":{c:{"passed":False,"evidence":""} for c in REVIEW_CATEGORIES},
            "quality_checks":quality_check_template(),
            "detector_dispositions":[{"detection":d,"acceptable":False,"reason":""} for d in report["variants"][a]["detections"]],
            "timing_checkpoints":[]
        } for a in r["files"]}}
        atomic_json(root/"review-template.json",template)
        return {"technical_pass":report["technical_pass"],"report":str(root/"qa.json"),
                "review_template":str(root/"review-template.json"),"manual_review":"pending"}


def validate_review(review, q, r, *, require_quality=False):
    require(review.get("fingerprint")==r["fingerprint"] and review.get("reviewer"), "review_identity", "Review must name reviewer and exact render fingerprint")
    for aspect in r["files"]:
        v=review.get("variants",{}).get(aspect,{})
        for category in REVIEW_CATEGORIES:
            item=v.get("checks",{}).get(category,{})
            require(item.get("passed") is True and str(item.get("evidence","")).strip(), "review_incomplete", f"{aspect}/{category} needs actual inspection evidence")
        dispositions=v.get("detector_dispositions",[])
        require([d.get("detection") for d in dispositions]==q["variants"][aspect]["detections"],"detector_review","Review every detector finding in order")
        require(all(d.get("acceptable") is True and d.get("reason") for d in dispositions), "unresolved_detection", "Correct or explain every detector finding")
        checks=v.get("timing_checkpoints",[])
        require(len(checks)>=3,"timing_checkpoints","Record audio-verified caption checkpoints near beginning, middle and end")
        positions=[]
        for c in checks:
            require(isinstance(c.get("output_time"),(int,float)) and 0<=c["output_time"]<=r["expected_duration"] and
                    isinstance(c.get("error_ms"),(int,float)) and abs(c["error_ms"])<=200 and c.get("evidence"),
                    "timing_error","Each measured checkpoint needs output_time, <=200ms error and evidence")
            positions.append(c["output_time"]/r["expected_duration"])
        require(min(positions)<=.25 and max(positions)>=.75 and any(.3<=x<=.7 for x in positions),
                "timing_coverage","Check the beginning, middle and end")
    validate_quality_review(review,q,r,require_complete=require_quality)


def record_progress(job, review):
    """Save partial findings without setting delivery/reviewed or inventing passes."""
    with job_lock(job):
        job,p,r=current_render(job)
        q=read_json(job/'latest-qa.json')
        require(q['fingerprint']==r['fingerprint'],'qa_required','Partial findings must refer to the current output')
        validate_quality_review(review,q,r,require_complete=False)
        result={**review,'recorded_at':time.time(),'status':'incomplete_review','delivery_approved':False}
        atomic_json(job/'review'/r['fingerprint']/'review-progress.json',result)
        return result


def record_review(job, review):
    with job_lock(job):
        job,p,r=current_render(job)
        q=read_json(job/"latest-qa.json")
        require(q["fingerprint"]==r["fingerprint"] and q["technical_pass"],"qa_required","Current technical QA must pass first")
        for aspect,record in r["files"].items():
            checked=q["variants"][aspect]
            require(checked["sha256"]==record["sha256"] and checked["subtitle_sha256"]==file_hash(inside(job,record["subtitles"])) and
                    checked["captions_sha256"]==file_hash(inside(job,record["path"]).parent/"captions.json") and
                    checked.get("ass_sha256")==file_hash(inside(job,record["path"]).parent/"captions.ass"),"qa_changed","Rerun QA after media/subtitle changes")
        validate_review(review,q,r,require_quality=r["mode"] == "final")
        status = "test_fixture_only" if p["fixture"] else "reviewed" if r["mode"] == "final" else "draft_review"
        receipt={**review,"recorded_at":time.time(),"fixture":p["fixture"],"status":status}
        atomic_json(job/"review"/r["fingerprint"]/"review.json",receipt)
        p["delivery"]={"fingerprint":r["fingerprint"],"revision":p["revision"],"status":receipt["status"],"mode":r["mode"]}
        atomic_json(job/"project.json",p)
        return p["delivery"]


def package(job, target, draft=False, audience="internal"):
    with job_lock(job):
        job,p,r=current_render(job)
        source_path(job,p)
        for a in p["assets"].values():
            require(file_hash(inside(job,a["path"]))==a["sha256"],"asset_changed","Cannot package modified managed assets")
        if not draft:
            require(r["mode"]=="final" and (p.get("delivery") or {}).get("fingerprint")==r["fingerprint"],"review_required","Final package needs reviewed current final outputs; use --draft for clearly labelled incomplete handoff")
            q=read_json(job/"latest-qa.json")
            require(q["fingerprint"]==r["fingerprint"] and q["technical_pass"],"qa_required","Current QA required")
            for aspect,f in r["files"].items():
                require(file_hash(inside(job,f["subtitles"]))==q["variants"][aspect]["subtitle_sha256"] and
                        file_hash(inside(job,f["path"]).parent/"captions.json")==q["variants"][aspect]["captions_sha256"] and
                        file_hash(inside(job,f["path"]).parent/"captions.ass")==q["variants"][aspect].get("ass_sha256"),
                        "qa_changed","Subtitle sidecars changed after QA; inspect before delivery")
            validate_review(read_json(job/"review"/r["fingerprint"]/"review.json"),q,r,require_quality=True)
        target=Path(target).resolve()
        require(target.suffix==".zip" and not target.exists(),"package_target","Choose a new .zip file; existing files are preserved")
        require(not target.is_relative_to(job),"package_location","Package must be outside the job")
        selected={job/"project.json",job/"latest-render.json"}
        # Include all immutable inputs and historical manifests, so old revisions restore offline.
        for folder in ("media","references","assets","transcripts","history","edits"):
            if (job/folder).exists(): selected.update(x for x in (job/folder).rglob("*") if x.is_file())
        for f in r["files"].values():
            selected.add(inside(job,f["path"]))
            selected.update(inside(job,f["path"]).parent/x for x in ("captions.ass","captions.srt","captions.json"))
        render_folder = inside(job,next(iter(r["files"].values()))["path"]).parent.parent
        for name in ("visual-rhythm.json","sfx-report.json","sfx-only.wav"):
            path = render_folder/name
            if path.exists(): selected.add(path)
        for name in ("qa.json","review.json","review-template.json","review-progress.json"):
            path=job/"review"/r["fingerprint"]/name
            if path.exists(): selected.add(path)
        if (job/"latest-qa.json").exists(): selected.add(job/"latest-qa.json")
        for path in (job/"review"/"source-profile.json",):
            if path.exists(): selected.add(path)
        if (job/"review"/"workflow").exists(): selected.update((job/"review"/"workflow").glob("*.json"))
        for f in r["files"].values():
            path=inside(job,f["path"]).parent/"caption-readability.json"
            if path.exists(): selected.add(path)
        from .portable import package_manifest, rough_package_files
        rough_files, rough_state = rough_package_files(job,p)
        selected.update(rough_files)
        selected, manifest = package_manifest(job,p,selected,audience)
        manifest["rough_export"] = rough_state
        target.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(target,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
            for path in sorted(selected):
                require(path.resolve().is_relative_to(job),"unsafe_package","Package input outside job")
                archive.write(path,path.relative_to(job).as_posix())
            archive.writestr("DEPENDENCIES.json",json.dumps(manifest,ensure_ascii=False,indent=2))
            archive.writestr("PACKAGE-STATUS.txt",f"{'DRAFT: review incomplete' if draft else 'Reviewed export'}\nFixture: {p['fixture']}\nRevision: {p['revision']}\nNo credentials or model files included.\nOpen with talking-head status --job <extracted-folder>.\n")
        return {"path":str(target),"sha256":file_hash(target),"draft":draft,"fixture":p["fixture"]}
