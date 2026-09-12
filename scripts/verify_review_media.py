"""Decode an actual review export and create evidence; never certify listening/taste."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


def run(command, log):
    result = subprocess.run(command, capture_output=True)
    log.write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'Command failed; preserve {log}')
    return result


def verify(media, output, ffmpeg, ffprobe, expected):
    output.mkdir(parents=True, exist_ok=False)
    probe = run([ffprobe, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(media)], output/'probe.json')
    info = json.loads(probe.stdout)
    videos = [s for s in info['streams'] if s['codec_type']=='video']
    audios = [s for s in info['streams'] if s['codec_type']=='audio']
    video = videos[0]
    errors=[]
    if (video['width'], video['height'], video['r_frame_rate']) != (1920,1080,'30/1'):
        errors.append('Unexpected format; expected 1080p30 landscape')
    if int(video.get('nb_frames',0)) != expected:
        errors.append('Unexpected encoded frame count')
    if not audios:
        errors.append('Missing final speech/audio stream')
    run([ffmpeg,'-hide_banner','-nostdin','-xerror','-i',str(media),'-vf','blackdetect=d=0.12:pix_th=0.10:pic_th=0.98,freezedetect=n=-50dB:d=2','-af','silencedetect=noise=-48dB:d=1,ebur128=peak=true','-f','null','-'],output/'full-decode.log')
    frames=output/'frames'; frames.mkdir()
    boundaries=[0,64,65,134,135,208,209,332,333,434,435,485,486,531,532,583,584,635,636,787,788,907,908,1147,1148,1200,1305,1388,1389,1500,1530,1531,1599,1600,1750,1854,1855,1946,1985,1986,2158,2159,2763,2764,2925,2926,2954,2955,2985,3044]
    samples=sorted(set(range(0,expected,60))|set(x for x in boundaries if x<expected))
    expression='+'.join(f'eq(n,{n})' for n in samples)
    run([ffmpeg,'-hide_banner','-nostdin','-xerror','-i',str(media),'-vf',f"select='{expression}',scale=640:360",'-fps_mode','vfr',str(frames/'frame-%03d.jpg')],output/'frame-decode.log')
    files=sorted(frames.glob('*.jpg'))
    if len(files)!=len(samples): errors.append('Sample count mismatch')
    for start in range(0,len(files),9):
        sheet=Image.new('RGB',(1920,1140),'#191919'); draw=ImageDraw.Draw(sheet)
        for j,path in enumerate(files[start:start+9]):
            x=(j%3)*640;y=(j//3)*380
            with Image.open(path) as im: sheet.paste(im,(x,y+20))
            draw.text((x+8,y+3),f'{samples[start+j]}f / {samples[start+j]/30:.3f}s',fill='white')
        sheet.save(output/f'sheet-{start//9+1:02d}.jpg',quality=94)
    log=(output/'full-decode.log').read_text(encoding='utf8',errors='replace')
    last=log.rsplit('Summary:',1)[-1]
    integrated=re.search(r'I:\s+(-?[\d.]+) LUFS',last)
    peak=re.search(r'Peak:\s+(-?[\d.]+) dBFS',last)
    flags=[l for l in log.splitlines() if any(k in l for k in ['black_start:','freeze_start:','silence_start:','silence_end:'])]
    result={'input':str(media),'sha256':hashlib.sha256(media.read_bytes()).hexdigest(),'bytes':media.stat().st_size,'expected_frames':expected,'frames':video.get('nb_frames'),'duration':info['format']['duration'],'audio_video_duration_delta':abs(float(video['duration'])-float(audios[0]['duration'])) if audios else None,'technical_errors':errors,'decode_pass':True,'integrated_lufs':float(integrated[1]) if integrated else None,'true_peak_dbfs':float(peak[1]) if peak else None,'review_candidates':flags,'sample_frames':samples,'samples_extracted':len(files),'continuous_watch':'unverified','listening':'unverified','manual_200ms_sync':'unverified','user_style_approval':'pending'}
    (output/'technical-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='sample_frames'},ensure_ascii=False,indent=2))
    return 1 if errors else 0


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('media',type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True);p.add_argument('--frames',type=int,required=True)
    a=p.parse_args();raise SystemExit(verify(a.media,a.out,a.ffmpeg,a.ffprobe,a.frames))
