"""Verify catalog completeness and the exact curated media allowlist before Git."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--decode',action='store_true')
    p.add_argument('--report',type=Path,default=ROOT/'work/template-center-20261027/gallery-verification.json')
    args=p.parse_args();gallery=ROOT/'docs/template-gallery'
    data=json.loads((ROOT/'templates/catalog.json').read_text(encoding='utf-8'))
    ff=ROOT/'.runtime/ffmpeg/bin/ffmpeg.exe';probe=ff.with_name('ffprobe.exe')
    paths={};registered_hashes={};counts=Counter()
    for e in data['entries']:
        counts[e['layer']]+=1
        for demo in e['demos']:
            if demo.get('path'):
                path=(gallery/demo['path']).resolve()
                assert path.is_relative_to((gallery/'demos').resolve())
                assert path.is_file(), str(path)
                paths[path]=demo['path']
                assert demo.get('sha256') and demo.get('bytes'), demo['path']+' missing reviewed media identity'
                registered_hashes[path]=(demo['sha256'],demo['bytes'])
    details=[]
    for path,rel in sorted(paths.items()):
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert (digest,path.stat().st_size)==registered_hashes[path], rel+' changed after registry review'
        raw=subprocess.check_output([str(probe),'-v','error','-show_streams','-show_format','-of','json',str(path)])
        d=json.loads(raw);video=next(x for x in d['streams'] if x['codec_type']=='video')
        assert not any(x['codec_type']=='audio' for x in d['streams']), rel+' is not silent'
        assert 0<float(d['format']['duration'])<=20, rel+' duration outside curated-demo range'
        assert path.stat().st_size<=8*1024*1024,rel+' too large'
        if args.decode:
            run=subprocess.run([str(ff),'-v','error','-i',str(path),'-f','null','-'],capture_output=True)
            assert run.returncode==0,rel+' cannot decode'
        details.append({'path':rel,'sha256':digest,
                        'bytes':path.stat().st_size,'width':video['width'],'height':video['height'],
                        'fps':video['r_frame_rate'],'seconds':float(d['format']['duration'])})
    unexpected=[str(x.relative_to(gallery)) for x in (gallery/'demos').rglob('*.mp4') if x.resolve() not in paths]
    assert not unexpected,'Unregistered media in approved folder: '+repr(unexpected)
    record={'catalog_entries':len(data['entries']),'counts':dict(counts),
            'local_demo_files':len(details),'local_demo_bytes':sum(x['bytes'] for x in details),
            'all_registered_demos_present':True,'all_local_demos_silent':True,
            'full_decode_this_invocation':args.decode,'continuous_watch':False,
            'details':details,'unregistered_mp4':unexpected}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='details'},ensure_ascii=False))


if __name__=='__main__':
    main()
