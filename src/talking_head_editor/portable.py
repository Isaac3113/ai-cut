"""Package rights and fresh-directory recovery using the same main project."""
from __future__ import annotations
import zipfile
from pathlib import Path, PurePosixPath
from . import __version__
from .util import require,inside,file_hash,read_json,atomic_json,load_job,executable,run


def package_manifest(job, project, selected, audience):
    require(audience in ('internal','external'),'package_audience','Choose internal or external')
    allowed=set(selected); withheld=[]
    raw={inside(job,a['path']):a for a in project['assets'].values()}
    raw[inside(job,project['source']['path'])]={'sha256':project['source']['sha256'],'license':{'kind':'provided'},'name':'original speaker footage'}
    for path,a in raw.items():
        if audience=='external' and a.get('license',{}).get('redistribute_raw') is not True:
            allowed.discard(path)
            withheld.append({'path':path.relative_to(job).as_posix(),'sha256':a['sha256'],
                             'reason':'Raw redistribution not explicitly recorded; recipient must lawfully relink this dependency'})
    # Never hide a font binary or credential in references/history. No system font
    # is shipped: restore requires an installed, locally licensed compatible font.
    for path in list(allowed):
        name=path.name.casefold()
        require(name not in ('.env','runtime.local.json') and not name.startswith('.env.')
                and path.suffix.lower() not in ('.ttf','.otf','.ttc','.woff','.woff2'),
                'unsafe_package_file',f'Do not package secrets/runtime credentials/font binaries: {path.name}')
    manifest={'schema_version':1,'engine':__version__,'audience':audience,
              'scope':'private editing handoff' if audience=='internal' else 'external handoff with raw-media rights filtering',
              'dependencies':[{'path':x.relative_to(job).as_posix(),'sha256':file_hash(x)} for x in sorted(allowed)],
              'withheld':withheld,'ready_to_rerender':not withheld,
              'runtime_requirements':['Python package ai-cut '+__version__,'FFmpeg with libass','FFprobe','locally licensed Chinese font via THE_FONT'],
              'source_original_unchanged':True,'model_or_font_binaries_included':False}
    return allowed,manifest


def rough_package_files(job, project):
    """Preserve only a complete, current rough export; this is not watch approval."""
    from .timeline import output_formats
    from .workflow import structure_fingerprint
    job=Path(job).resolve()
    pointer=job/'latest-rough.json'
    state={'included':False,'status':'absent','continuous_review':'unverified'}
    if not pointer.exists():return set(),state
    rough=read_json(pointer)
    require(isinstance(rough,dict) and rough.get('mode')=='rough',
            'rough_package_pointer','Expected a rough export receipt')
    if rough.get('complete') is not True:
        return set(),{**state,'status':'incomplete','reason':'Incomplete rough export omitted'}
    if rough.get('structure_fingerprint')!=structure_fingerprint(project):
        return set(),{**state,'status':'stale','reason':'Rough structure differs from current source cuts and words'}
    files=rough.get('files')
    expected=set(output_formats(project['plan'],project['source']['probe']))
    require(isinstance(files,dict) and set(files)==expected and files,
            'rough_package_variants','Current rough export must contain all requested formats')
    selected={pointer}
    for record in files.values():
        require(isinstance(record,dict),'rough_package_pointer','Malformed rough file record')
        for name in ('path','subtitles'):
            value=record.get(name)
            require(isinstance(value,str) and value and not Path(value).is_absolute() and ':' not in value,
                    'rough_package_pointer','Rough file pointers must be relative project paths')
        video=inside(job,record['path'])
        require(video.suffix.lower()=='.mp4' and video.is_file() and file_hash(video)==record.get('sha256'),
                'rough_package_changed','Rough video missing or changed; inspect/rebuild it before packaging')
        subtitle=inside(job,record['subtitles'])
        require(subtitle==video.parent/'captions.srt','rough_package_pointer','Rough subtitle pointer must match its video directory')
        sidecars={video.parent/name for name in ('captions.ass','captions.srt','captions.json')}
        require(all(path.is_file() for path in sidecars),
                'rough_package_sidecars','Rough ASS/SRT/JSON sidecars are required for a complete handoff')
        selected.update({video,*sidecars})
    return selected,{**state,'included':True,'status':'current_export',
                     'structure_fingerprint':rough['structure_fingerprint'],
                     'note':'Video receipt verified; packaged sidecars are manifest-hashed. No viewing/listening approval inferred.'}


def restore_package(archive_path,target):
    archive_path=Path(archive_path).resolve();target=Path(target).resolve()
    require(not target.exists(),'restore_target','Restore into a new directory only')
    with zipfile.ZipFile(archive_path) as z:
        require('DEPENDENCIES.json' in z.namelist(),'restore_manifest','New package manifest required')
        import json
        manifest=json.loads(z.read('DEPENDENCIES.json'))
        for name in z.namelist():
            part=PurePosixPath(name)
            require(not part.is_absolute() and '..' not in part.parts and ':' not in name and '\\' not in name,
                    'unsafe_archive','Archive contains an unsafe path')
        target.mkdir(parents=True)
        z.extractall(target)
    missing=[]
    for d in manifest['dependencies']:
        f=inside(target,d['path'])
        if not f.is_file() or file_hash(f)!=d['sha256']:missing.append(d['path'])
    require(not missing,'restore_hash','Restored files do not match manifest: '+str(missing))
    result={'archive_sha256':file_hash(archive_path),'target':str(target),
            'verified_files':len(manifest['dependencies']),'withheld':manifest['withheld'],
            'relink_required':bool(manifest['withheld']),'rerender_verified':False}
    atomic_json(target/'restore-receipt.json',result)
    return result


def verify_restored_clip(original_job,restored_job,clip_id,aspect='landscape'):
    """Actually render a representative restored clip, not merely zip.testzip()."""
    from .render import render_clip,render_audio,ff
    from .timeline import validate_plan,mapped_words,DEFAULT_STYLE,output_formats
    from .project import transcript,source_path
    original,p=load_job(original_job); restored,q=load_job(restored_job)
    require(p['plan']==q['plan'] and p['source']['sha256']==q['source']['sha256'],'restore_plan','Restored project differs')
    source_path(restored,q)
    words=transcript(restored,q)['words'];plan=q['plan'];style={**DEFAULT_STYLE,**plan.get('style',{})}
    clips=validate_plan(plan,q['source']['duration'],words,q['assets'])
    c=next((x for x in clips if x['id']==clip_id),None);require(c,'restore_clip','Unknown representative clip')
    mapped=mapped_words(words,clips,plan.get('caption_corrections'),plan.get('caption_break_after'),plan.get('caption_groups'))
    dims=output_formats(plan,q['source']['probe'])[aspect]
    baseline,_=render_clip(original,p,c,mapped,aspect,style,1,dims)
    rebuilt,cached=render_clip(restored,q,c,mapped,aspect,style,1,dims)
    require(not cached,'restore_cache','Fresh restoration must render without original video cache')
    for path in (baseline,rebuilt):
        run([executable('ffmpeg'),'-v','error','-xerror','-i',path,'-f','null','-'],timeout=300)
    # Exact compressed bytes + subtitle sidecars prove same frames and timing for
    # the same deterministic software/runtime. Full playback is a separate check.
    require(file_hash(baseline)==file_hash(rebuilt),'restore_pixels','Re-rendered clip differs')
    require((baseline.parent/'captions.ass').read_bytes()==(rebuilt.parent/'captions.ass').read_bytes(),'restore_subtitles','Restored subtitle timing differs')
    work=restored/'recovery-test';work.mkdir(exist_ok=True)
    # Directly exercise the source/time mapping into audio in both directories.
    audio=[]
    for job,name in ((original,'reference'),(restored,'restored')):
        out=work/(name+'.wav')
        filt=f"atempo={c['playback_speed']},apad,atrim=duration={c['output_duration']},asetpts=PTS-STARTPTS"
        ff(['-ss',c['start'],'-t',c['end']-c['start'],'-i',inside(job,q['source']['path']),'-vn','-af',filt,
            '-ar','48000','-ac','2','-c:a','pcm_s16le',out],work,name)
        audio.append(out)
    require(file_hash(audio[0])==file_hash(audio[1]),'restore_audio','Restored source speech differs')
    result={'clip_id':clip_id,'output_duration':c['output_duration'],'video_sha256':file_hash(rebuilt),
            'exact_video_match':True,'subtitle_match':True,'source_audio_match':True,
            'fresh_cache':True,'full_playback':'unverified','note':'Representative clip recovery, not full external handoff validation'}
    atomic_json(work/'recovery-verification.json',result);return result
