"""Real dual-format render of synthetic fixture; never a user-video acceptance claim."""
import copy
import json
import wave
from pathlib import Path
import numpy as np
from talking_head_editor import assets,project
from talking_head_editor.render import render
from talking_head_editor.quality import qa
from talking_head_editor.util import ROOT,read_json,load_job,atomic_json,require,inside,run,executable


def pcm(path):
    with wave.open(str(path)) as w:return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.int32)


def main():
    # The standard smoke first verifies old dual layouts, source tones, reuse and restore.
    from smoke_render import main as original_smoke
    original_smoke()
    old=read_json(ROOT/'work/latest-smoke.json');job=Path(old['job'])
    ending=assets.register(job,job.parent/'TEST-CALIBRATION.mp4')['asset_id']
    assets.annotate(job,ending,'Synthetic calibration ending, not a portrait','Known generated testsrc2 fixture')
    _,p=load_job(job);plan=copy.deepcopy(p['plan']);plan['base_revision']=p['revision']
    first=plan['clips'][0]['id']
    plan['visual_effects']=[{'id':'zoom','clip_id':first,'offset':.1,'duration':1.4,'kind':'punch','factor':1.10,'purpose':'Test restrained crop','review_evidence':'Generated calibration frame, no person to crop'},
                            {'id':'word','clip_id':first,'offset':.3,'duration':1.1,'kind':'keyword','text':'重点','purpose':'Test keyword timing'}]
    plan['sound_effects']=[{'id':'tap','clip_id':first,'offset':.3,'duration':.3,'gain':.05,'kind':'tap','purpose':'Test accent aligned to keyword'}]
    plan['ending']={'asset_id':ending,'source_start':0,'duration':2,'purpose':'Two-second synthetic ending fixture'}
    project.apply_plan(job,plan)
    result=render(job,'draft');checks=qa(job);require(checks['technical_pass'],'motion_smoke',str(checks))
    work=inside(job,next(iter(result['files'].values()))['path']).parent.parent
    report=read_json(work/'sfx-report.json');base=pcm(report['body_audio']);mixed=pcm(work/'finished-mix.wav');fx=pcm(work/'sfx-only.wav')
    padded=np.pad(base,(0,len(mixed)-len(base)))
    error=int(np.max(np.abs(mixed-padded-fx)))
    require(error<=2,'sfx_voice_changed','Independent addition changed voice/base unexpectedly')
    require(report['track_peak_dbfs']<=-32,'sfx_loud','SFX exceeded reference cap')
    require(abs(result['expected_duration']-sum(c['output_duration'] for c in result['clips'])-2)<1e-7,'ending_time','Ending changed body timing')
    for value in result['files'].values():
        movie=inside(job,value['path'])
        require('\\fscx118' in (movie.parent/'captions.ass').read_text(encoding='utf-8-sig'),'keyword_missing','Editable ASS lacks emphasis event')
    result.update(fixture_only=True,technical_pass=True,voice_base_plus_sfx_max_error_lsb=error,sfx_peak_dbfs=report['track_peak_dbfs'],both_1080p=True,ending_seconds=2)
    atomic_json(ROOT/'work/latest-motion-smoke.json',result)
    print(json.dumps({'motion_smoke':'passed','both_1080p':True,'voice_addition_error_lsb':error,'sfx_peak_dbfs':report['track_peak_dbfs'],'job':str(job)}))

if __name__=='__main__':main()
