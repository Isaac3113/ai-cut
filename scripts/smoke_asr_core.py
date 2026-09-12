"""Isolate the timestamped ASR engine from first-run punctuation downloads."""
import argparse
import json
import sys
import time
from pathlib import Path
from talking_head_editor.util import ROOT, atomic_json, require
from talking_head_editor.asr import timestamp_words
from funasr import AutoModel

sys.stdout.reconfigure(encoding="utf-8")
p=argparse.ArgumentParser(); p.add_argument("--audio",required=True,type=Path)
a=p.parse_args()
folders=[x.parent for folder in (ROOT/".runtime/models/modelscope/models").glob("iic--speech_seaco_paraformer*") for x in folder.rglob("config.yaml") if (x.parent/"model.pt").is_file()]
require(len(folders)==1,"model_missing","Run normal transcribe to download the official Paraformer first")
started=time.time()
model=AutoModel(model=str(folders[0]),device="cuda:0",disable_update=True,disable_pbar=True,ncpu=4)
result=model.generate(input=str(a.audio),hotword="")
require(result and result[0].get("timestamp"),"timestamp_missing","No actual timestamps")
words=timestamp_words(result[0]["text"],result[0]["timestamp"])
receipt={"fixture_only":True,"engine":"Paraformer only; punctuation pipeline separately tested", "elapsed_seconds":time.time()-started,
         "word_count":len(words),"text":result[0]["text"],"words":words,"device":"cuda:0"}
atomic_json(ROOT/"work/latest-asr-core.json",receipt)
print(json.dumps({k:v for k,v in receipt.items() if k!="words"},ensure_ascii=False,indent=2))
