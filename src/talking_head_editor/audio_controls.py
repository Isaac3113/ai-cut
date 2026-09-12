"""Export aligned, already-levelled tracks for manual volume control in an NLE."""
from pathlib import Path
from .util import read_json,inside,require,file_hash,atomic_json,run,executable
from .quality import current_render
from .render import ff


def export_tracks(job,target):
    job,p,r=current_render(job);target=Path(target).resolve()
    require(not target.exists(),'audio_target','Choose a new output folder; existing exports are preserved')
    require(not target.is_relative_to(job),'audio_target','Keep handoff outside managed project')
    # finish_audio records the body cache that actually produced this render.
    video=inside(job,next(iter(r['files'].values()))['path'])
    work=video.parent.parent
    report=read_json(work/'sfx-report.json')
    body_mix=Path(report['body_audio']).resolve()
    require(body_mix.is_relative_to(job),'audio_cache','Audio cache must be in the current job')
    stems=read_json(body_mix.parent/'audio-stems.json')
    voice=inside(job,stems['voice'])
    require(file_hash(voice)==stems['voice_sha256'],'audio_cache','Voice changed since rendering')
    target.mkdir(parents=True)
    duration=r['expected_duration'];body=stems['duration'];tail=round(duration-body,9)
    headroom=p['plan']['style'].get('encode_headroom_db',0)
    voice_out=target/'voice.wav';music_out=target/'background-music.wav';sfx_out=target/'sound-effects.wav'
    ff(['-i',voice,'-af',f'apad,atrim=duration={duration},volume={headroom}dB',
        '-ar',48000,'-ac',2,'-c:a','pcm_s24le',voice_out],target,'voice')
    if stems['music']:
        bg=inside(job,stems['music']);require(file_hash(bg)==stems['music_sha256'],'audio_cache','Music changed since rendering')
        inputs=['-i',bg];filters=f'[0:a]apad,atrim=duration={duration}[bg];[bg]volume={headroom}dB[out]'
        if tail>0:
            asset=p['assets'][p['plan']['music_asset_id']]
            inputs+=['-ss',body%asset['duration'],'-stream_loop','-1','-i',inside(job,asset['path'])]
            filters=(f'[0:a]apad,atrim=duration={duration}[bg];'
                f'[1:a]atrim=duration={tail},asetpts=PTS-STARTPTS,loudnorm=I=-18:TP=-2:LRA=11,'
                f'volume={p["plan"]["style"]["music_gain_db"]}dB,afade=t=in:d=0.12,'
                f'afade=t=out:st={max(0,tail-1.2)}:d=1.2,aresample=48000,'
                f'aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,adelay={round(body*1000)}:all=1[tail];'
                f'[bg][tail]amix=inputs=2:duration=first:normalize=0,volume={headroom}dB[out]')
        ff([*inputs,'-filter_complex',filters,'-map','[out]','-t',duration,'-ar',48000,'-ac',2,'-c:a','pcm_s24le',music_out],target,'music')
    else:
        ff(['-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t',duration,'-c:a','pcm_s24le',music_out],target,'music')
    ff(['-i',work/'sfx-only.wav','-af',f'volume={headroom}dB','-ar',48000,'-ac',2,'-c:a','pcm_s24le',sfx_out],target,'sfx')
    videos={}
    for aspect,f in r['files'].items():
        original=inside(job,f['path']);dest=target/f'picture-and-voice-{aspect}.mp4'
        ff(['-i',original,'-i',voice_out,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
            '-ar',48000,'-movflags','+faststart','-t',duration,dest],target,'voice-video-'+aspect)
        hashes=[]
        for item in (original,dest):
            value,_=run([executable('ffmpeg'),'-v','error','-i',item,'-map','0:v:0','-c','copy','-f','hash','-'])
            hashes.append(value.strip())
        require(hashes[0]==hashes[1],'picture_changed','Manual audio handoff must preserve compressed video packets')
        run([executable('ffmpeg'),'-v','error','-xerror','-i',dest,'-f','null','-'],timeout=300)
        videos[aspect]={'path':dest.name,'sha256':file_hash(dest),'video_packet_hash':hashes[0]}
    data={'revision':p['revision'],'fingerprint':r['fingerprint'],'duration':duration,'videos':videos,
        'tracks':{name:{'path':f.name,'sha256':file_hash(f),'start_seconds':0,'gain_already_applied':True}
                  for name,f in [('voice',voice_out),('music',music_out),('sfx',sfx_out)]},
        'instructions':'Use picture-and-voice MP4 plus music/SFX at time zero. Do NOT add voice.wav again. Disable auto-loudness on music/SFX. 100% is already the new quiet level; reduce to 50% or mute as desired.',
        'scope':'Private audio handoff only; not an editable picture timeline or raw-stock redistribution license',
        'continuous_listening':'unverified','source_project_unchanged':True}
    atomic_json(target/'tracks.json',data)
    return data
