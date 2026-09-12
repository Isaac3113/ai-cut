"""Download an official FunASR demonstration audio, then test local Paraformer. Not user footage."""
import json
import time
import urllib.request
import sys
from talking_head_editor.util import ROOT, executable, run, atomic_json, load_job, file_hash
from talking_head_editor.project import create, transcript
from talking_head_editor.asr import transcribe

sys.stdout.reconfigure(encoding="utf-8")
root=ROOT/"work"/f"asr-smoke-{time.time_ns()}"
root.mkdir(parents=True)
url="https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_example_zh.wav"
audio=root/"official-example.wav"
with urllib.request.urlopen(url,timeout=60) as response, audio.open("wb") as target:
    while chunk:=response.read(1024*1024): target.write(chunk)
video=root/"OFFICIAL-AUDIO-TEST.mp4"
run([executable("ffmpeg"),"-y","-v","error","-f","lavfi","-i","color=c=0x263445:s=640x360:r=30",
     "-i",audio,"-c:v","libx264","-preset","ultrafast","-threads","2","-c:a","aac","-shortest",video])
job=root/"job"; create(job,video,fixture=True)
result=transcribe(job,device="auto")
_,p=load_job(job); data=transcript(job,p)
receipt={"fixture_only":True,"source_url":url,"source_sha256":file_hash(audio),"job":str(job),"result":result,
         "text":data["text"],"word_count":len(data["words"]),"first_word":data["words"][0],"last_word":data["words"][-1]}
atomic_json(ROOT/"work"/"latest-asr-smoke.json",receipt)
print(json.dumps(receipt,ensure_ascii=False,indent=2))
