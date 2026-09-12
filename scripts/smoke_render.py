"""Actual dual-1080p FFmpeg regression using generated calibration media, never user acceptance."""
import copy
import json
import time
import wave
from pathlib import Path
from PIL import Image

from talking_head_editor import project, assets
from talking_head_editor.util import ROOT, run, executable, atomic_json, load_job, file_hash, require, EditorError
from talking_head_editor.timeline import default_plan, gaps
from talking_head_editor.render import render
from talking_head_editor.quality import qa, package


def main():
    root=ROOT/"work"/f"smoke-{time.time_ns()}"
    root.mkdir(parents=True)
    source=root/"TEST-CALIBRATION.mp4"
    run([executable("ffmpeg"),"-y","-v","error","-f","lavfi","-i","testsrc2=size=1280x720:rate=30:duration=12",
         "-f","lavfi","-i","aevalsrc='0.2*sin(2*PI*t*if(lt(t,4),440,if(lt(t,8),660,880)))':s=48000:d=12","-c:v","libx264","-preset","ultrafast",
         "-threads","2","-c:a","aac","-shortest",source])
    job=root/"job"; project.create(job,source,fixture=True)
    words=[]
    for i,(start,text) in enumerate([(1,"这不是"),(1.6,"RM100。"),(4.5,"如果"),(5.2,"API可用。"),(8.5,"非常"),(9.2,"非常重要。")]):
        words.append({"id":f"w{i}","start":start,"end":start+.45,"text":text})
    project.install_transcript(job,{"schema_version":1,"words":words},"test_fixture")
    pic=root/"TEST-ASSET.png"; Image.new("RGB",(640,480),"#266577").save(pic)
    aid=assets.register(job,pic)["asset_id"]
    assets.annotate(job,aid,"Generated solid teal calibration image","Automated fixture definition; not real semantic review")
    _,p=load_job(job); plan=default_plan(12,p["revision"]); plan["output_formats"]=["landscape","portrait"]
    plan["clips"]=[{"id":"hook","start":8.2,"end":10.11,"reason":"fixture reordered emphasis"},
                   {"id":"condition","start":4.2,"end":6.1,"reason":"fixture full condition"},
                   {"id":"fact","start":.7,"end":2.4,"reason":"fixture negation and amount preserved"}]
    plan["deletions"]=[{"start":a,"end":b,"reason":"test calibration omitted interval"} for a,b in gaps(plan["clips"],12)]
    plan["overlays"]=[{"id":"graphic","clip_id":"hook","offset":.1,"duration":1.3,"mode":"pip","purpose":"label calibration",
                        "graphic":{"type":"title","title":"测试素材"}},
                       {"id":"asset","clip_id":"condition","offset":.1,"duration":1.4,"mode":"pip","purpose":"test asset compositing","asset_id":aid}]
    plan["semantic_review"]={"status":"reviewed","evidence":"Synthetic mapping fixture, not a spoken-content acceptance test"}
    plan["style"]["keywords"]=["API","非常"]
    project.apply_plan(job,plan); revision=load_job(job)[1]["revision"]
    original_hash=file_hash(source)
    first=render(job,"final"); checks=qa(job)
    require(checks["technical_pass"],"smoke_qa",str(checks))
    # Decode the exported AAC. Three distinct source tones must follow the
    # same reordered timeline as the visible source frames and captions.
    import numpy as np
    audio_checks={}
    for aspect,record in first["files"].items():
        wav=root/f"{aspect}-decoded.wav"
        run([executable("ffmpeg"),"-y","-v","error","-i",job/record["path"],"-vn","-ac","1","-ar","48000","-c:a","pcm_s16le",wav])
        with wave.open(str(wav)) as handle: samples=np.frombuffer(handle.readframes(handle.getnframes()),dtype=np.int16).astype(float)
        detected=[]
        for clip,expected in zip(first["clips"],(880,660,440)):
            at=clip["output_start"]+clip["output_duration"]*.5
            window=samples[int((at-.125)*48000):int((at+.125)*48000)]
            spectrum=np.abs(np.fft.rfft(window*np.hanning(len(window))))
            frequency=np.fft.rfftfreq(len(window),1/48000)[np.argmax(spectrum)]
            require(abs(frequency-expected)<5,"audio_order",f"Expected {expected}Hz, decoded {frequency}Hz")
            detected.append(round(float(frequency),2))
        audio_checks[aspect]=detected
    repeated=render(job,"final"); require(repeated.get("reused"),"cache_failure","Whole-render resume did not reuse outputs")
    _,p=load_job(job); changed=copy.deepcopy(p["plan"]); changed["base_revision"]=p["revision"]
    changed["overlays"][1]["duration"]=1.2
    project.apply_plan(job,changed)
    edited=render(job,"final")
    require(edited["audio_reused"] and edited["cached_clips"]>=4,"partial_cache","Visual edit should reuse voice and unaffected clips")
    restored=project.restore(job,revision,load_job(job)[1]["revision"])
    back=render(job,"final"); require(back["fingerprint"]==first["fingerprint"] and back.get("reused"),"restore","Restored plan should reproduce original outputs")
    require(file_hash(source)==original_hash,"source_mutated","Original source changed")
    qa(job)
    try: package(job,root/"unreviewed.zip")
    except EditorError as e: require(e.code=="review_required","package_gate",str(e))
    else: raise AssertionError("Unreviewed package passed")
    draft=package(job,root/"TEST-DRAFT.zip",draft=True)
    result={"fixture_only":True,"job":str(job),"technical_pass":True,"both_1080p":True,
            "resume_reused":True,"partial_edit_cached_clips":edited["cached_clips"],"audio_reused":edited["audio_reused"],
            "restore_reused":True,"source_unchanged":True,"unreviewed_delivery_blocked":True,
            "decoded_audio_tones_hz":audio_checks,"files":first["files"],"draft":draft}
    atomic_json(ROOT/"work"/"latest-smoke.json",result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__": main()
