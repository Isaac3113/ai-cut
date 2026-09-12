"""Evidence-bound editorial workflow around the existing single source timeline.

This does not make semantic decisions or claim to watch/hear media. It validates
the agent's packet, exposes missing checks, and binds them to the current plan.
"""
from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path

from .util import (atomic_json, digest, executable, file_hash, inside, load_job,
                   read_json, require, run, streams)

RULE_VERSION = "quality-first-v2.1"
STATES = {"pass", "fail", "unverified", "not_applicable"}


def structure_fingerprint(project):
    p = project['plan']
    return digest({'source': project['source']['sha256'], 'transcript': project['transcript']['sha256'],
                   'clips': [{k:c[k] for k in ('id','start','end')} for c in p['clips']],
                   'speed': p.get('style',{}).get('playback_speed',1),
                   'corrections': p.get('caption_corrections',{}), 'groups': p.get('caption_groups',[])})


def plan_fingerprint(project):
    return digest({'source': project['source']['sha256'], 'transcript': project['transcript']['sha256'],
                   'plan': project['plan'], 'assets': {k:a['sha256'] for k,a in project['assets'].items()},
                   'rules': RULE_VERSION})


def rough_view(project):
    """Derived view, never saved as a second plan; same source cuts/speed/order."""
    result=copy.deepcopy(project); p=result['plan']
    for field in ('overlays','visual_effects','sound_effects'): p[field]=[]
    p.pop('music_asset_id',None); p.pop('ending',None)
    p['style']['keywords']=[]
    for clip in p['clips']:
        for layout in clip.get('layouts',{}).values():layout.pop('title',None)
    p['visual_rhythm']={'enforce':False}
    return result


def caption_readability(cues):
    """Review flags, not universal Chinese/English pass/fail or a listening claim."""
    rows=[]
    for i,c in enumerate(cues):
        text=c.get('text',''); duration=c['end']-c['start']
        cjk=len(re.findall(r'[\u3400-\u9fff]',text))
        latin=len(re.findall(r'[A-Za-z0-9]+',text))
        flags=[]
        if duration < .7: flags.append('short_exposure')
        if cjk/max(duration,.001)>9: flags.append('fast_chinese_reading')
        if latin/max(duration,.001)>4: flags.append('fast_latin_reading')
        rows.append({'index':i,'start':c['start'],'end':c['end'],'text':text,
                     'cjk_per_second':round(cjk/max(duration,.001),2),
                     'latin_words_per_second':round(latin/max(duration,.001),2),'flags':flags})
    return {'rule_version':RULE_VERSION,'count':len(rows),'flagged':sum(bool(x['flags']) for x in rows),
            'status':'unverified','basis':'Computed exposure only; full proofreading and phone review still required','cues':rows}


def source_profile(job):
    """Inspect real stream metadata and all frame timestamps without altering source."""
    from .project import source_path, audit_source
    job,p=load_job(job); src=source_path(job,p)
    decode=audit_source(job)
    output=job/'review'/'source-profile.json'
    old=read_json(output) if output.exists() else {}
    if old.get('source_sha256')==p['source']['sha256'] and old.get('rule_version')==RULE_VERSION:
        return {**old,'reused':True}
    probe=p['source']['probe']; v=streams(probe,'video')[0]; aud=streams(probe,'audio')
    raw,_=run([executable('ffprobe'),'-v','error','-select_streams','v:0','-show_frames',
               '-show_entries','frame=best_effort_timestamp_time','-of','json',src],timeout=600)
    pts=[float(x['best_effort_timestamp_time']) for x in json.loads(raw)['frames'] if 'best_effort_timestamp_time' in x]
    delta=[b-a for a,b in zip(pts,pts[1:])]
    nominal=sorted(delta)[len(delta)//2] if delta else 0
    transfer=v.get('color_transfer','unknown')
    rotations=[x.get('rotation') for x in v.get('side_data_list',[]) if 'rotation' in x]
    result={'rule_version':RULE_VERSION,'source_sha256':p['source']['sha256'],
            'full_decode_pass':decode['full_decode_pass'],'frame_count':len(pts),
            'monotonic_pts':bool(delta) and min(delta)>0,
            'variable_frame_intervals':any(abs(x-nominal)>.002 for x in delta),
            'nominal_interval':nominal,'rotation':rotations or [v.get('tags',{}).get('rotate',0)],
            'sample_aspect_ratio':v.get('sample_aspect_ratio','unknown'),
            'video_start':v.get('start_time'),'audio_starts':[x.get('start_time') for x in aud],
            'audio_channels':[x.get('channels') for x in aud],
            'color':{k:v.get(k,'unknown') for k in ('color_space','color_primaries','color_transfer','color_range','pix_fmt')},
            'hdr_requires_working_copy':transfer in ('smpte2084','arib-std-b67'),
            'audio_listening':'unverified','privacy_review':'unverified','checked_at':time.time()}
    atomic_json(output,result); return result


def require_source_ready(job):
    job,p=load_job(job)
    profile=source_profile(job)
    require(profile.get('source_sha256')==p['source']['sha256'] and profile.get('full_decode_pass'),
            'source_profile_stale','Profile must describe the actual current source')
    require(profile.get('monotonic_pts') is True,'source_pts_unsupported','Nonmonotonic source timestamps need an inspected working-copy repair')
    require(profile.get('hdr_requires_working_copy') is False,'source_hdr_unsupported',
            'HDR needs a verified SDR working copy; metadata relabeling is not color conversion')


def record_packet(job, packet):
    """A real review packet: brief + every cut reason + shot comparisons + files.

    No numerical ranking forces free media over paid media. Unwatched candidates
    remain eligible for research but cannot be labeled a verified final choice.
    """
    job,p=load_job(job)
    require(packet.get('plan_fingerprint')==plan_fingerprint(p),'workflow_stale','Packet must match current plan and asset identities')
    brief=packet.get('brief',{})
    for field in ('audience','goal','format','style','budget','delivery'):
        require(isinstance(brief.get(field),str) and brief[field].strip(),'brief_missing',f'Missing brief.{field}')
    units=packet.get('editorial_units',[])
    require({x.get('clip_id') for x in units}=={x['id'] for x in p['plan']['clips']},'editorial_coverage','Explain each retained semantic unit')
    for x in units:
        for field in ('role','meaning','context_check','selection_reason'):
            require(x.get(field),'editorial_reason',f'Missing {field} for {x.get("clip_id")}')
    require(packet.get('take_comparisons') and packet.get('uncertainties') is not None,
            'rough_judgment','Record alternative takes and uncertainties, including why no take was changed')
    shots=packet.get('shots',[])
    expected={o['id'] for o in p['plan'].get('overlays',[])}
    if p['plan'].get('music_asset_id'): expected.add('background_music')
    require({x.get('shot_id') for x in shots}==expected,'shot_coverage','Every used overlay and music needs a selection record')
    for shot in shots:
        require(shot.get('need') and shot.get('selected_reason') and shot.get('candidates'),'shot_need','Define object/action/result and compare candidates')
        candidates=shot['candidates']
        require(len({x.get('id') for x in candidates})==len(candidates),'candidate_duplicate','Duplicate comparison candidate')
        selected=[x for x in candidates if x.get('selected')]
        require(len(selected)==1,'candidate_selection','Select exactly one candidate for this draft slot')
        for candidate in candidates:
            require(candidate.get('kind') in ('owned','free','paid'),'candidate_kind','Record candidate source kind')
            require(candidate.get('observation') in ('metadata_only','frames','motion_watched','listened'),
                    'candidate_observation','State how the candidate was actually examined')
            require(candidate.get('reason'),'candidate_reason','Explain adoption/rejection or pending state')
            if candidate['kind']!='owned':
                require(candidate.get('source_url') and candidate.get('license_url'),'candidate_source','Retain official source and license URLs')
            if candidate.get('selected'):
                aid=candidate.get('asset_id')
                require(aid in p['assets'],'candidate_asset','Chosen media must be registered')
                intended=p['plan'].get('music_asset_id') if shot['shot_id']=='background_music' else next(o.get('asset_id') for o in p['plan']['overlays'] if o['id']==shot['shot_id'])
                require(aid==intended,'candidate_wrong_shot','Candidate must match the media actually used in this slot')
                require(candidate.get('sha256')==p['assets'][aid]['sha256'],'candidate_hash','Chosen candidate hash differs')
                require(candidate.get('preview_only') is not True,'preview_not_final','A paid/watermarked preview cannot enter a render')
                if candidate['kind']=='paid':
                    require(p['assets'][aid].get('approval',{}).get('sha256')==candidate['sha256'],'paid_approval_required','Actual paid asset approval required')
    evidence=[]
    for item in packet.get('evidence_files',[]):
        path=inside(job,item['path'])
        require(path.is_file(),'workflow_evidence_missing',str(path))
        evidence.append({'path':item['path'],'sha256':file_hash(path)})
    require(evidence,'workflow_evidence_missing','Attach actual files, not only claims')
    packet={**packet,'rule_version':RULE_VERSION,'evidence_files':evidence,'recorded_at':time.time()}
    dst=job/'review'/'workflow'/f"{packet['plan_fingerprint']}.json"
    atomic_json(dst,packet)
    return workflow_status(job)


def workflow_status(job):
    job,p=load_job(job); key=plan_fingerprint(p)
    file=job/'review'/'workflow'/f'{key}.json'
    packet=read_json(file) if file.exists() else None
    rough=read_json(job/'latest-rough.json') if (job/'latest-rough.json').exists() else None
    rough_valid=bool(rough and rough.get('complete') and rough.get('structure_fingerprint')==structure_fingerprint(p)
                     and all(inside(job,f['path']).is_file() and file_hash(inside(job,f['path']))==f['sha256'] for f in rough['files'].values()))
    evidence_valid=bool(packet and all(inside(job,f['path']).is_file() and file_hash(inside(job,f['path']))==f['sha256'] for f in packet['evidence_files']))
    return {'rule_version':RULE_VERSION,'plan_fingerprint':key,'packet_valid':evidence_valid,
            'rough_render_valid':rough_valid,'rough_watched':(packet or {}).get('rough_watch',{'status':'unverified'}),
            'picture_lock':(packet or {}).get('picture_lock',{'status':'unverified'}),
            'note':'Rendered / packet present never implies continuous viewing or listening'}


def require_editorial_ready(job):
    result=workflow_status(job)
    require(result['packet_valid'] and result['rough_render_valid'],'editorial_workflow_pending',
            'Current editorial packet and complete standalone A-roll rough render required; render draft while pending')
    require(result['rough_watched'].get('status')=='pass' and result['rough_watched'].get('evidence'),
            'rough_watch_pending','Complete A-roll viewing/listening is not verified')
    require(result['picture_lock'].get('status')=='pass' and result['picture_lock'].get('evidence'),
            'picture_lock_pending','Context sample/picture lock remains unverified')
