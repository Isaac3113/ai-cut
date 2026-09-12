from __future__ import annotations

import contextlib
import os
import re
import time
import importlib.metadata
from pathlib import Path

from .util import ROOT, atomic_json, digest, require, run, executable, EditorError, job_lock, read_json, file_hash
from .project import load_job, source_path, install_transcript, audit_source

TOKEN = re.compile(r"[A-Za-z0-9]+(?:[.'%+-][A-Za-z0-9]+)*|[\u3400-\u9fff]|[^\s]")
PUNCTUATION = set('，。！？、：；,.!?;:…“”‘’"()（）《》【】[]—')


def timestamp_words(text, timestamps):
    tokens = []
    for token in TOKEN.findall(text):
        if token in PUNCTUATION:
            if tokens:
                tokens[-1] += token
        else:
            tokens.append(token)
    require(len(tokens) == len(timestamps), "alignment_mismatch",
            f"ASR produced {len(tokens)} tokens but {len(timestamps)} timestamps. Raw result preserved; do not fabricate timing.")
    result = []
    for index, (text, stamp) in enumerate(zip(tokens, timestamps)):
        start, end = float(stamp[0])/1000, float(stamp[1])/1000
        require(end > start, "alignment_mismatch", "ASR produced a zero-duration word; inspect raw output")
        result.append({"id": f"w{index:06d}", "text": text, "start": start, "end": end,
                       "confidence": None})
    return result


def transcribe(job, hotwords=None, device="auto"):
    with job_lock(job,".asr.lock"):
        return _transcribe(job,hotwords,device)


def _transcribe(job, hotwords=None, device="auto"):
    audit_source(job)
    job, p = load_job(job)
    source = source_path(job, p)
    hotwords = hotwords or []
    if isinstance(hotwords, str):
        hotwords = [x.strip() for x in hotwords.splitlines() if x.strip()]
    manifest_file=ROOT/".runtime/asr-models.json"
    manifest=read_json(manifest_file) if manifest_file.exists() else None
    if manifest:
        for record in manifest.values():
            for name,sha in record["files"].items():
                path=Path(record["path"])/name
                require(path.is_file() and file_hash(path)==sha,"asr_model_changed","Local model differs from tested receipt; inspect before accepting new weights")
    def cache_key(m):
        return digest({"source": p["source"]["sha256"], "model": "paraformer-zh", "hotwords": hotwords,
                       "adapter": 2, "funasr":importlib.metadata.version("funasr"),"model_manifest":m})
    key = cache_key(manifest)
    normalized = job / "asr-cache" / f"{key}.json"
    if normalized.exists():
        from .project import transcript
        cached=read_json(normalized)
        if p.get("transcript"):
            current=transcript(job,p)
            if current.get("words")==cached["words"] and current.get("hotwords")==hotwords:
                return {"revision":p["revision"],"words":len(current["words"]),"reused":True,"plan_preserved":True}
        return install_transcript(job, cached, "funasr", expected=p["revision"])
    cache = ROOT / ".runtime" / "models"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MODELSCOPE_CACHE", str(cache / "modelscope"))
    os.environ.setdefault("HF_HOME", str(cache / "huggingface"))
    os.environ["PATH"]=str(Path(executable("ffmpeg")).parent)+os.pathsep+os.environ.get("PATH","")
    log = job / "logs" / "transcribe.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        import torch
        from funasr import AutoModel
    except ImportError as e:
        raise EditorError("asr_not_installed", "Run scripts/bootstrap.ps1 -ASR; no synthetic transcript will be substituted") from e
    if device == "auto":
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if device.startswith("cuda"):
        require(torch.cuda.is_available(), "cuda_unavailable", "CUDA is unavailable; explicitly select cpu if needed")
    audio = job / "asr-cache" / "source-16k.wav"
    audio.parent.mkdir(parents=True, exist_ok=True)
    run([executable("ffmpeg"), "-y", "-v", "error", "-i", source, "-vn", "-ac", "1", "-ar", "16000", audio], log=job / "logs" / "extract-audio.log")
    started = time.time()
    with log.open("w", encoding="utf-8") as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        aliases={"model":"paraformer-zh","vad_model":"fsmn-vad","punc_model":"ct-punc"}
        choices={k:manifest[k]["path"] if manifest else v for k,v in aliases.items()}
        model = AutoModel(**choices,
                          device=device, disable_update=True, disable_pbar=True, ncpu=4)
        if not manifest:
            manifest={}
            for k,config in (("model",model.kwargs),("vad_model",model.vad_kwargs),("punc_model",model.punc_kwargs)):
                path=Path(config["model_path"])
                files={x.name:file_hash(x) for x in path.iterdir() if x.is_file() and not x.name.startswith(".")}
                require("model.pt" in files,"model_receipt","Expected model weights missing")
                manifest[k]={"alias":aliases[k],"path":str(path),"files":files}
            atomic_json(manifest_file,manifest)
            key=cache_key(manifest)
            normalized=job/"asr-cache"/f"{key}.json"
        result = model.generate(input=str(audio), batch_size_s=60, hotword=" ".join(hotwords))
    raw_path = job / "asr-cache" / f"{key}-raw.json"
    atomic_json(raw_path, result)
    require(result and result[0].get("timestamp"), "timestamps_missing", "ASR did not return word timestamps; inspect raw output")
    r = result[0]
    words = timestamp_words(r["text"], r["timestamp"])
    data = {"schema_version": 1, "text": r["text"], "words": words,
            "model": "paraformer-zh", "device": device, "hotwords": hotwords,
            "model_manifest_sha256":digest(manifest),
            "runtime_versions":{n:importlib.metadata.version(n) for n in ("funasr","torch","modelscope")},
            "elapsed_seconds": round(time.time()-started, 2), "review_status": "pending"}
    atomic_json(normalized, data)
    receipt = install_transcript(job, data, "funasr", expected=p["revision"])
    return {**receipt, "device": device, "elapsed_seconds": data["elapsed_seconds"], "raw": str(raw_path)}
