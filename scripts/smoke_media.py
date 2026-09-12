"""Second generated input: video overlay, graph, music mix and preview rendering."""
import json
import time
from talking_head_editor import project, assets
from talking_head_editor.util import ROOT, executable, run, load_job, atomic_json, require
from talking_head_editor.timeline import default_plan
from talking_head_editor.render import render
from talking_head_editor.quality import qa

root=ROOT/"work"/f"media-smoke-{time.time_ns()}"; root.mkdir(parents=True)
source=root/"TEST-24FPS.mp4"; music=root/"TEST-MUSIC.wav"
run([executable("ffmpeg"),"-y","-v","error","-f","lavfi","-i","testsrc2=size=640x480:rate=24:duration=8",
     "-f","lavfi","-i","sine=frequency=660:sample_rate=44100:duration=8","-c:v","libx264","-preset","ultrafast","-threads","2","-c:a","aac",source])
run([executable("ffmpeg"),"-y","-v","error","-f","lavfi","-i","sine=frequency=110:sample_rate=44100:duration=3",music])
job=root/"job"; project.create(job,source,fixture=True)
project.install_transcript(job,{"schema_version":1,"words":[{"id":"w1","text":"24fps测试片。","start":.4,"end":2.2},{"id":"w2","text":"这只是校准数据。","start":4.1,"end":5.6}]},"test_fixture")
vid=assets.register(job,source)["asset_id"]; bg=assets.register(job,music)["asset_id"]
assets.annotate(job,vid,"Generated animated test pattern","Generated fixture definition; no user content")
assets.annotate(job,bg,"110Hz calibration tone","Known generated signal; not reviewed music for publishing")
_,p=load_job(job); plan=default_plan(8,p["revision"])
plan["music_asset_id"]=bg
plan["overlays"]=[{"id":"v","clip_id":"c001","asset_id":vid,"offset":.2,"duration":2,"mode":"pip","purpose":"test video overlay"},
{"id":"g","clip_id":"c001","offset":3,"duration":2.7,"purpose":"test chart layout",
 "graphic":{"type":"bar","title":"校准数据","unit":"","items":[{"label":"A","value":10},{"label":"B","value":20}],"evidence":"Deliberately generated test values, never user data"}}]
plan["semantic_review"]={"status":"reviewed","evidence":"Generated test fixture only"}
project.apply_plan(job,plan)
r=render(job,"preview"); q=qa(job)
require(q["technical_pass"],"media_smoke",str(q))
result={"fixture_only":True,"job":str(job),"technical_pass":True,"features":["24fps to 30fps","video overlay","data-card layout","music ducking","two-pass loudness","two-format preview"],"files":r["files"]}
atomic_json(ROOT/"work/latest-media-smoke.json",result)
print(json.dumps(result,ensure_ascii=False,indent=2))
