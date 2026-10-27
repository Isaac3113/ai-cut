"""Make real-frame posters and small category GIFs from registered local demos."""
from pathlib import Path
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FF=ROOT/'.runtime/ffmpeg/bin/ffmpeg.exe'
GALLERY=ROOT/'docs/template-gallery'


def run(args):
    r=subprocess.run([str(FF),'-hide_banner','-v','error','-nostdin',*map(str,args)],capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8',errors='replace'))


def main():
    data=json.loads((ROOT/'templates/catalog.json').read_text(encoding='utf-8'))
    records=ROOT/'work/template-center-20261027/preview-cache.json'
    cache=json.loads(records.read_text(encoding='utf-8')) if records.exists() else {}
    paths={};categories={}
    for e in data['entries']:
        for demo in e['demos']:
            if demo.get('path'):
                p=GALLERY/demo['path'];assert p.is_file()
                assert p.resolve().is_relative_to((GALLERY/'demos').resolve())
                paths[p]=demo['path']
                categories.setdefault(e['category_zh'],(e,p))
    def poster(item):
        p,rel=item;digest=sha256(p.read_bytes()).hexdigest();out=p.with_suffix('.jpg')
        if not out.exists() or cache.get(rel)!=digest:
            probe=json.loads(subprocess.check_output([str(FF.with_name('ffprobe.exe')),'-v','error','-show_entries','format=duration','-of','json',str(p)]))
            at=float(probe['format']['duration'])*0.5
            run(['-ss',at,'-i',p,'-frames:v','1','-vf','scale=480:-2','-q:v','5','-y',out])
        return rel,digest
    with ThreadPoolExecutor(max_workers=4) as pool:cache.update(dict(pool.map(poster,paths.items())))
    gifdir=GALLERY/'demos/categories';gifdir.mkdir(exist_ok=True)
    category_rows=[]
    for category,(entry,p) in sorted(categories.items()):
        name='category-'+sha256(category.encode()).hexdigest()[:12]+'.gif';out=gifdir/name
        key='category:'+category;digest=sha256(p.read_bytes()).hexdigest()
        if not out.exists() or cache.get(key)!=digest:
            run(['-i',p,'-t','3','-filter_complex',
                 'fps=8,scale=256:-2:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=bayer',
                 '-loop','0','-y',out])
        cache[key]=digest
        category_rows.append({'category_zh':category,'path':'demos/categories/'+name,
                              'source_entry':entry['id'],'description_zh':'该分类的一个实际控件演示；其他条目见完整清单'})
    records.parent.mkdir(parents=True,exist_ok=True)
    records.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
    gif_count=len(category_rows)
    for category in sorted({e['category_zh'] for e in data['entries']}-set(categories)):
        entry=next(e for e in data['entries'] if e['category_zh']==category and e.get('demos'))
        demo=next(d for d in entry['demos'] if d.get('url'))
        category_rows.append({'category_zh':category,'url':demo['url'],
                              'source_entry':entry['id'],'description_zh':entry['label_zh']+'：官方在线分类演示'})
    category_rows.sort(key=lambda c:c['category_zh'])
    (GALLERY/'category-demos.json').write_text(json.dumps(category_rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 分类动画预览','','每个分类都有演示入口：23类提供真实本地Demo的动画小样，4类链接官方原片。逐项演示及适用条件见[完整中文清单](../../templates/README.zh-CN.md)。静音演示不代表本条成片已验收。','']
    for c in category_rows:
        lines += ['## '+c['category_zh'],'']
        if c.get('path'):
            lines += ['![分类动画：'+c['category_zh']+']('+c['path']+')','']
        else:
            lines += ['['+c['description_zh']+']('+c['url']+')','','官方视频保留原样，在线播放需要联网。','']
        lines += ['来源条目：`'+c['source_entry']+'`。','']
    (GALLERY/'CATEGORIES.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'posters':len(paths),'categories':len(category_rows),'category_gifs':gif_count,'official_categories':len(category_rows)-gif_count}))


if __name__=='__main__':
    main()
