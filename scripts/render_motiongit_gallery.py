"""Render the authorized MotionGit controls through its public helper only.

This orchestrator contains our catalogue/demo inputs, never the protected renderer.
The .motion personal envelope and helper/cache remain local and outside Git.
Plan and image review are separate explicit phases; this script never auto-approves.
This is the 2026-10-27 silent catalogue batch, not the new-video editing adapter.
New videos use scripts/motiongit_adapter.py and their own reviewed narration/layout.
Runtime package/node come from --config (motiongit.local.json) or CLI overrides.
Batch inputs need gallery.public_dir/source_video/logo or their CLI equivalents;
work_dir holds the local new-instance receipt, public contracts, plans and QA.
The frozen work default is intentional evidence storage, not a portable dependency.
The public gallery recipes are pinned to package 2.7.17-alpha.2 / library 0.3.0.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, time
import re
from render_motiongit_gallery_data import GROUPS, PROPS, VARIANTS, AVOID, INPUT_HINT

REPO = pathlib.Path(__file__).resolve().parents[1]
CONFIG = REPO / 'motiongit.local.json'
ADAPTER = REPO / 'scripts/motiongit_adapter.py'
PUBLIC = None
SOURCE_VIDEO = None
LOGO = None
WORK = REPO / 'work/template-center-20261027/motiongit'
OUTPUT = REPO / 'docs/template-gallery/demos/motiongit'
NODE = pathlib.Path(shutil.which('node')) if shutil.which('node') else None
PACKAGE = None
FFMPEG = REPO / '.runtime/ffmpeg/bin/ffmpeg.exe'
FFPROBE = FFMPEG.with_name('ffprobe.exe')
EXPECTED_HELPER_SHA = '7004609ddbc0ccf6451beeb477aff0d3c85bda74f902e5922465c85cd347f6f3'

def read(p):
    return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))

def write(p, value):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def sha(p):
    h=hashlib.sha256()
    with pathlib.Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def configure(args):
    """Read paths only; never print local configuration or personal package data."""
    global CONFIG, PUBLIC, SOURCE_VIDEO, LOGO, WORK, NODE, PACKAGE, FFMPEG, FFPROBE
    CONFIG = args.config.resolve()
    config = read(CONFIG) if CONFIG.is_file() else {}
    gallery = config.get('gallery', {})
    def path(cli, value, fallback=None):
        selected = cli if cli is not None else value
        return pathlib.Path(selected).expanduser().resolve() if selected else fallback
    NODE = path(args.node, config.get('node'), NODE)
    PACKAGE = path(args.package, config.get('package'))
    PUBLIC = path(args.public_dir, gallery.get('public_dir'))
    SOURCE_VIDEO = path(args.source_video, gallery.get('source_video'))
    LOGO = path(args.logo, gallery.get('logo'))
    WORK = path(args.work_dir, gallery.get('work_dir'), WORK)
    FFMPEG = path(args.ffmpeg, gallery.get('ffmpeg'), FFMPEG)
    FFPROBE = FFMPEG.with_name('ffprobe.exe')

def env():
    e=os.environ.copy(); e['PYTHONUTF8']='1'; e['ADU_PYTHON']=sys.executable
    prefixes=([str(NODE.parent)] if NODE else []) + [str(pathlib.Path(sys.executable).parent),str(FFMPEG.parent)]
    e['PATH']=os.pathsep.join([*prefixes,e.get('PATH','')])
    return e

def official(name, action, args):
    # The shared adapter verifies the public helper before official execution.
    WORK.mkdir(parents=True,exist_ok=True)
    for suffix in ['.json','-stderr.txt']:
        previous=WORK/(name+suffix)
        if previous.exists():
            history=WORK/'history'; history.mkdir(exist_ok=True)
            shutil.copy2(previous,history/(name+'-'+str(time.time_ns())+suffix))
    t=time.perf_counter()
    command=[sys.executable,str(ADAPTER),'--config',str(CONFIG)]
    if PACKAGE: command.extend(['--package',str(PACKAGE)])
    if NODE: command.extend(['--node',str(NODE)])
    r=subprocess.run([*command,action,*args],env=env(),capture_output=True,encoding='utf-8',errors='replace')
    try:
        receipt=json.loads(r.stdout)
        output=pathlib.Path(receipt['result_file']).read_text(encoding='utf-8')
        stderr=pathlib.Path(receipt['stderr_file']).read_text(encoding='utf-8')
    except (ValueError,KeyError):
        output=r.stdout; stderr=r.stderr
    (WORK/(name+'.json')).write_text(output,encoding='utf-8')
    (WORK/(name+'-stderr.txt')).write_text(stderr,encoding='utf-8')
    result={'operation':action,'exit':r.returncode,'seconds':round(time.perf_counter()-t,3),'receipt':str(WORK/(name+'.json'))}
    try:
        d=json.loads(output)
        for k in ['status','ok','error','code','instanceDirectory']:
            if k in d: result[k]=d[k]
    except ValueError: pass
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if r.returncode: raise SystemExit(r.returncode)
    return json.loads(output)

def instance():
    return pathlib.Path(read(WORK/'new-instance.json')['instanceDirectory'])

def group_tag(group):
    revisions=read(WORK/'revisions.json') if (WORK/'revisions.json').exists() else {}
    return group+revisions.get(group,'')

def cue_count(control, props):
    fixed={'title':2,'compare':3,'quote':1,'stamp':1,'chapter':1,'fusion':2,
      'logo':2,'intro':2,'cta':2,'subscribe':2,'countdown':1,'price':3,'reveal':2,
      'qa':2,'myth':3,'definition':3,'tip':2,'linechart':3,'matrix':3,
      'beforeafter':2,'device':2,'collage':2,'highlight':2,'scramble':2,
      'marquee':2,'bigtype':2,'search':3,'social':2,'lowerthird':2,'callout':2,
      'sticker':2,'emoji':1,'progressbar':2,'confetti':1,'frame':1}
    if control in fixed: return fixed[control]
    if control in ['keyword','number']: return 1+len(props.get('sub' if control=='keyword' else 'note',[]))
    if control in ['media','browser']: return (1 if control=='media' else 2)+len(props.get('callouts',[]))
    if control in ['outro','donut','table','comment','notify','checklist','hub']: return 1+len(props.get('rows',props.get('items',[])))
    if control=='prosCons': return len(props['pros'])+len(props['cons'])+1
    if control=='vs': return 3+len(props['stats'])
    if control=='venn': return 1+len(props['sets'])
    if control=='mindmap': return 1+len(props['branches'])
    if control=='spotlight': return 1+len(props['points'])
    for k in ['items','steps','nodes','layers','lines','words','messages']:
        if k in props: return len(props[k])
    raise ValueError(control)

def build():
    if not all(p and p.is_file() for p in [SOURCE_VIDEO, LOGO]) or not PUBLIC:
        raise ValueError('build needs --public-dir, --source-video and --logo, or gallery paths in local config; use your own authorized inputs')
    guide=read(PUBLIC/'public-guide.json')['extensionLibrary']
    contract=read(WORK/'contract-all.json')
    if len(contract['selectedControls'])!=70: raise RuntimeError('All 70 public control contracts must be read first')
    ins=instance(); inputs=ins/'inputs'; inputs.mkdir(exist_ok=True)
    src=SOURCE_VIDEO
    assets=[]
    for name,sec in [('presenter.jpg',4),('screen.jpg',36.6),('detail.jpg',50)]:
        dest=inputs/name
        if not dest.exists():
            subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-ss',str(sec),'-i',str(src),'-frames:v','1','-q:v','2',str(dest)],check=True,env=env())
        assets.append({'file':name,'source_sha256':sha(src),'source_time':sec,'sha256':sha(dest),'role':'own video frame'})
    logo=LOGO
    if not (inputs/'logo.png').exists(): shutil.copy2(logo,inputs/'logo.png')
    assets.append({'file':'logo.png','sha256':sha(inputs/'logo.png'),'role':'own brand logo'})
    write(WORK/'input-manifest.json',{'assets':assets,'input_directory':str(inputs),'no_narration':True,'silent_output':True})
    entries=[]; groups=[]
    for key,(category,ids) in GROUPS.items():
        segments=[]; overlays=[]; clips=[]
        for i,cid in enumerate(ids):
            c=guide['controls'][cid]; props=PROPS[cid]; n=cue_count(cid,props)
            t0=i*6; t1=t0+6; tail=max(c.get('tail',1.6),1.6)
            last=6-tail-0.15
            cues=[round(t0+0.2+(last-0.2)*(j/max(1,n-1)),3) for j in range(n)]
            variant=VARIANTS.get(cid,c['variants'][0])
            seg={'control':cid,'variant':variant,'t0':t0,'t1':t1,'cues':cues,'props':props}
            if cid=='confetti': seg['area']={'x':0,'y':1080,'w':1080,'h':720}
            if key=='overlay': overlays.append(seg)
            else: seg.update(presenter='hide',transition='cut',styleProfile='dark'); segments.append(seg)
            variants=[]
            note=c['variantsNote']
            for v in c['variants']:
                m=re.search(r'(?:^|/)\s*'+re.escape(v)+r'\s+(.+?)(?=\s*/|$)',note)
                variants.append({'id':v,'label_zh':m.group(1).strip() if m else note})
            own=any(x in json.dumps(props) for x in ['presenter.jpg','screen.jpg','detail.jpg','logo.png']) or key=='overlay'
            if cid=='bigtype' and variant!='mask': own=False
            entries.append({'id':'mg-control-'+cid,'label_zh':c['label'],'layer':'control','category_zh':category,
                'description_zh':c['use'],'uses_zh':[c['use']],'avoid_zh':AVOID[key],
                'inputs_zh':INPUT_HINT[key],'version':'0.3.0 (package2.7.17-alpha.2)',
                'source_url':'https://motiongit.com/@adunext/template-01-integrated-portrait','source_id':cid,
                'license':'MotionGit 个人授权模板包，以原包授权为准；仅包含自有素材及明确示例数据的渲染演示，不分发受保护代码。',
                'availability':'registered_pending_render','validation':{'state':'registered','scope':'已核对官方公开合同；代表变体演示待渲染，其他变体未测试。'},
                'demos':[],'variants':variants,'layer_kind':'overlay' if key=='overlay' else 'segment',
                'demo_plan':{'group':key,'variant':variant,'t0':t0,'t1':t1,'kind':'own' if own else 'source_render'},
                'label_provenance':'原作者公开中文 guide：label/use/variantsNote；中文分类与使用提醒由本项目整理。'})
            clips.append({'control':cid,'variant':variant,'t0':t0,'t1':t1,'cues':cues,'kind':'own' if own else 'source_render'})
        if key=='overlay':
            # Each overlay is isolated over the same authorized still; this is not a narrated final edit.
            segments=[{'control':'media','variant':'zoom','t0':0,'t1':len(ids)*6,'cues':[0.2],
                       'props':{'src':'presenter.jpg'},'presenter':'hide','transition':'cut','styleProfile':'dark'}]
        timeline={'layout':'portrait','duration':len(ids)*6,'voiceover':'','music':'','hud':False,
                  'styleProfile':'dark','theme':{'accent':'#47B4D0','accent2':'#18A7CA','bg':'#0B1318'},
                  'ending':'cut','captions':[],'segments':segments,'overlays':overlays,
                  'mediaPolicies':{'presenter.jpg':{'role':'photo','fit':'contain'},'screen.jpg':{'role':'evidence','fit':'contain'},'detail.jpg':{'role':'evidence','fit':'contain'},'logo.png':{'role':'logo','fit':'contain'}},
                  '$comment':'静音控件目录演示；所有数字、评论、界面和价格均为明确示例，不是正式教学或真实业务成果。cues 为动画排程，不是语音对齐。'}
        used=json.dumps([segments,overlays],ensure_ascii=False)
        timeline['mediaPolicies']={k:v for k,v in timeline['mediaPolicies'].items() if k in used}
        params={'workflow':'motion-kit','header':{'shortTitle':'控件演示 · '+category},'timeline':timeline}
        write(ins/('params-'+key+'.json'),params)
        write(WORK/'params'/('params-'+key+'.json'),params)
        groups.append({'id':key,'label_zh':category,'controls':ids,'duration':len(ids)*6,'clips':clips,'params_sha256':sha(ins/('params-'+key+'.json'))})
    write(WORK/'groups.json',groups)
    write(REPO/'templates/motiongit-controls.json',{'schema_version':'1.0','source':{'package_version':'2.7.17-alpha.2','library_version':'0.3.0','official_helper_sha256':EXPECTED_HELPER_SHA,'public_schema_sha256':contract['source']['sha256'],'control_count':70,'variant_count':210},'scope_zh':'每项只渲染一个代表变体；全部210个变体登记不等于全部已渲染。中文名称与变体说明来自原作者。','entries':entries})
    print(json.dumps({'groups':len(groups),'controls':len(entries),'variants':sum(len(e['variants']) for e in entries),'instance':str(ins)},ensure_ascii=False))

def phase(group, phase_name):
    ids=list(GROUPS) if group=='all' else [group]
    for key in ids:
        ins=instance(); lang=['--language','zh']; tag=group_tag(key)
        if phase_name=='check': op='check-params'; argv=['params-'+key+'.json','--inputs','inputs',*lang]
        elif phase_name=='plan': op='plan'; argv=['params-'+key+'.json','--inputs','inputs','--out','plan-'+tag,*lang]
        elif phase_name=='prepare': op='prepare'; argv=['@vault','--inputs','@vault','--plan','plan-'+tag,'--out','project-'+tag,*lang]
        elif phase_name=='preview':
            times=[i*6+5.2 for i in range(len(GROUPS[key][1]))]
            if key=='overlay': times.extend([19.2,37.2])
            op='preview'; argv=['project-'+tag,'--times',','.join(str(t) for t in sorted(times)),*lang]
        elif phase_name=='render': op='render'; argv=['project-'+tag,'--out',tag+'.mp4',*lang]
        else: raise ValueError(phase_name)
        official(tag+'-'+phase_name,'run',['--instance',str(ins),op,*argv])

def preview_sheet(group):
    from PIL import Image, ImageDraw, ImageFont
    p=instance()/('project-'+group_tag(group)); meta=read(p/'preview.json')
    files=sorted(meta['stills'],key=lambda x:float(pathlib.Path(x).stem[2:]))
    w,h=360,672; cols=4; rows=(len(files)+cols-1)//cols
    sheet=Image.new('RGB',(w*cols,h*rows),'#0b1318'); draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
    for i,f in enumerate(files):
        assert sha(p/f)==meta['stills'][f]
        im=Image.open(p/f).convert('RGB'); im.thumbnail((w,640))
        x=(i%cols)*w; y=(i//cols)*h; sheet.paste(im,(x,y))
        t=float(pathlib.Path(f).stem[2:]); index=min(int(t//6),len(GROUPS[group][1])-1)
        draw.text((x+5,y+644),f'{GROUPS[group][1][index]}  {t:.2f}s',font=font,fill='white')
    out=WORK/'preview-sheets'/(group+'.jpg'); out.parent.mkdir(exist_ok=True); sheet.save(out,quality=94)
    print(str(out)); return out

def export_group(group, identity_label=False):
    """Split an officially rendered montage; resize and remove audio only."""
    from PIL import Image, ImageDraw, ImageFont
    group_info=next(g for g in read(WORK/'groups.json') if g['id']==group)
    src=instance()/(group_tag(group)+'.mp4')
    if not src.is_file(): raise RuntimeError('Official montage is not rendered: '+str(src))
    project=instance()/('project-'+group_tag(group))
    assert read(project/'preview.json')['reviewed'] is True
    OUTPUT.mkdir(parents=True,exist_ok=True)
    qa=WORK/('encoded-qa-labeled' if identity_label else 'encoded-qa'); qa.mkdir(exist_ok=True)
    staging=WORK/'labeled-candidates'; staging.mkdir(exist_ok=True)
    records=[]; pictures={1.2:[],3.2:[],5.2:[]}
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
    for clip in group_info['clips']:
        cid=clip['control']; dest=(staging if identity_label else OUTPUT)/(cid+'.mp4')
        # No logo removal, retiming or renderer source modifications. The optional
        # lower-left identity tag is our explicit gallery annotation, not native UI.
        vf='scale=540:960:flags=lanczos,fps=30,setsar=1'
        if identity_label:
            vf+="\u002cdrawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':text='控件演示 · 非正式内容':x=18:y=h-36:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=6"
        cmd=[str(FFMPEG),'-hide_banner','-loglevel','error','-n','-ss',str(clip['t0']),'-i',str(src),'-t','6','-map','0:v:0','-an','-vf',vf,'-c:v','libx264','-preset','medium','-crf','25','-maxrate','1800k','-bufsize','3600k','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
        if not dest.exists(): subprocess.run(cmd,env=env(),check=True,capture_output=True)
        probe=subprocess.run([str(FFPROBE),'-v','error','-show_streams','-show_format','-of','json',str(dest)],capture_output=True,encoding='utf-8',check=True)
        info=json.loads(probe.stdout); stream=info['streams'][0]
        assert len(info['streams'])==1 and stream['codec_type']=='video'
        assert stream['width']==540 and stream['height']==960 and stream['nb_frames']=='180'
        assert abs(float(info['format']['duration'])-6)<0.001 and dest.stat().st_size<2_000_000
        decode=subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-i',str(dest),'-f','null','-'],capture_output=True,encoding='utf-8')
        (qa/(cid+'-decode.log')).write_text(decode.stderr,encoding='utf-8')
        if decode.returncode or decode.stderr.strip(): raise RuntimeError('Decode issue: '+cid)
        samples=[]
        for sec in pictures:
            png=qa/(cid+'-'+str(sec)+'.png')
            if not png.exists(): subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-ss',str(sec),'-i',str(dest),'-frames:v','1',str(png)],capture_output=True,check=True)
            im=Image.open(png).convert('RGB')
            # Center content excludes the fixed author mark/clock, so a changing clock alone is not motion evidence.
            center=im.crop((0,130,540,900))
            samples.append({'time':sec,'file':str(png),'pixel_sha256':hashlib.sha256(center.tobytes()).hexdigest()})
            pictures[sec].append((cid,im.copy()))
        if identity_label:
            final=OUTPUT/(cid+'.mp4'); previous=WORK/'pre-identity-demos'/(cid+'.mp4')
            previous.parent.mkdir(exist_ok=True)
            if final.exists() and not previous.exists(): shutil.copy2(final,previous)
            assert dest.resolve().is_relative_to(WORK.resolve()) and final.resolve().is_relative_to(OUTPUT.resolve())
            os.replace(dest,final); dest=final
        records.append({'control':cid,'variant':clip['variant'],'montage_source':str(src),'montage_source_sha256':sha(src),'range_seconds':[clip['t0'],clip['t1']],
            'file':str(dest),'sha256':sha(dest),'bytes':dest.stat().st_size,'duration':6,'frames':180,'fps':'30/1','width':540,'height':960,'audio_streams':0,'full_decode_exit':0,'full_decode_errors':0,
            'sampled_motion':len({s['pixel_sha256'] for s in samples})>1,'samples':samples,
            'continuous_watch':False,'owner_artistic_acceptance':False,'export_sample_images_viewed':False})
        records[-1]['gallery_identity_label']='控件演示 · 非正式内容' if identity_label else None
        print(json.dumps({'exported':cid,'bytes':dest.stat().st_size,'decode':'pass'},ensure_ascii=False),flush=True)
    for sec,ims in pictures.items():
        w,h,cols=360,672,4; rows=(len(ims)+cols-1)//cols
        sheet=Image.new('RGB',(w*cols,h*rows),'#0b1318'); d=ImageDraw.Draw(sheet)
        for i,(cid,im) in enumerate(ims):
            im.thumbnail((w,640)); x=(i%cols)*w;y=(i//cols)*h;sheet.paste(im,(x,y));d.text((x+5,y+644),f'{cid} {sec}s',font=font,fill='white')
        sheet.save(qa/(group+'-'+str(sec)+'.jpg'),quality=94)
    write(qa/(group+'-verification.json'),records)

def catalogue_final():
    catalog=read(REPO/'templates/motiongit-controls.json'); allrecords=[]
    for group in GROUPS: allrecords.extend(read(WORK/'encoded-qa-labeled'/(group+'-verification.json')))
    lookup={r['control']:r for r in allrecords}
    for entry in catalog['entries']:
        r=lookup[entry['source_id']]
        if not r['export_sample_images_viewed']: raise RuntimeError('Export images not reviewed: '+entry['source_id'])
        plan=entry['demo_plan']
        entry['availability']='available'
        entry['validation']={'state':'rendered_verified','scope':'一个代表变体已由官方 helper 渲染；静音小样完整解码，并已查看实际导出抽帧。其他两个变体仅登记，未渲染；不代表连续观看或用户审美认可。',
          'rendered_variant':r['variant'],'decode_verified':True,'sample_images_viewed':True,'sampled_motion':r['sampled_motion'],'continuous_watch':False,'owner_artistic_acceptance':False}
        entry['demos']=[{'kind':plan['kind'],'path':'demos/motiongit/'+entry['source_id']+'.mp4',
          'description_zh':'官方控件真实渲染；'+('使用本人授权素材。' if plan['kind']=='own' else '使用中文示例文案或示例数据。')+'6秒静音控件演示；保留模板原生标记与组内时码，角标不是本文件播放计时。低位演示身份标为本目录后处理添加。',
          'variant_id':r['variant'],'duration_seconds':6,'width':540,'height':960,'sha256':r['sha256'],'bytes':r['bytes'],'audio':'none'}]
    write(REPO/'templates/motiongit-controls.json',catalog)
    write(WORK/'encoded-qa-labeled/final-summary.json',{'controls':len(allrecords),'variants_registered':210,'variants_rendered':70,'total_bytes':sum(r['bytes'] for r in allrecords),'max_bytes':max(r['bytes'] for r in allrecords),'full_decode_pass':all(r['full_decode_exit']==0 for r in allrecords),'all_silent':all(r['audio_streams']==0 for r in allrecords),'all_sample_images_viewed':all(r['export_sample_images_viewed'] for r in allrecords),'all_sampled_motion':all(r['sampled_motion'] for r in allrecords),'identity_label':'控件演示 · 非正式内容','continuous_watch':False,'owner_artistic_acceptance':False})
    print('Catalogue bound to 70 verified rendered demos.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=pathlib.Path,default=REPO/'motiongit.local.json')
    for option in ['package','node','public-dir','source-video','logo','work-dir','ffmpeg']:
        ap.add_argument('--'+option,type=pathlib.Path)
    sp=ap.add_subparsers(dest='command',required=True)
    q=sp.add_parser('official'); q.add_argument('name'); q.add_argument('action'); q.add_argument('args',nargs=argparse.REMAINDER)
    q=sp.add_parser('run'); q.add_argument('name'); q.add_argument('operation'); q.add_argument('args',nargs=argparse.REMAINDER)
    sp.add_parser('build')
    q=sp.add_parser('phase'); q.add_argument('phase',choices=['check','plan','prepare','preview','render']); q.add_argument('group',choices=['all',*GROUPS])
    q=sp.add_parser('sheet'); q.add_argument('group',choices=GROUPS)
    q=sp.add_parser('export'); q.add_argument('group',choices=['all',*GROUPS])
    q=sp.add_parser('label'); q.add_argument('group',choices=['all',*GROUPS])
    sp.add_parser('finalize')
    args=ap.parse_args()
    configure(args)
    if args.command=='official': official(args.name,args.action,args.args)
    elif args.command=='run': official(args.name,'run',['--instance',str(instance()),args.operation,*args.args])
    elif args.command=='build': build()
    elif args.command=='phase': phase(args.group,args.phase)
    elif args.command=='sheet': preview_sheet(args.group)
    elif args.command=='export':
        for g in (list(GROUPS) if args.group=='all' else [args.group]): export_group(g)
    elif args.command=='finalize': catalogue_final()
    elif args.command=='label':
        for g in (list(GROUPS) if args.group=='all' else [args.group]): export_group(g,identity_label=True)

if __name__=='__main__': main()
