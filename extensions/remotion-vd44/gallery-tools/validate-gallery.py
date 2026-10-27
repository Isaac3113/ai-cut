"""Validate rendered gallery assets and build the Chinese registry, without claiming final-video QA."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

EXT = Path(__file__).resolve().parents[1]
REPO = EXT.parent.parent
OUT = REPO / 'docs/template-gallery/demos/remotion'
WORK = EXT / 'gallery-tools/remotion-work'
FFMPEG = REPO / '.runtime/ffmpeg/bin/ffmpeg.exe'
FFPROBE = FFMPEG.with_name('ffprobe.exe')
FONT = EXT / 'public/NotoSansSC.ttf'

USE = {
    'Logo与品牌': ['品牌标记登场', '活动或栏目开场'],
    '文字与标题': ['口播重点词与章节', '旅行视频地点或段落标题'],
    '转场': ['语义转折或明确换场', '旅行地点与时间转换'],
    '数据与图表': ['有来源的数据比较', '步骤进度与指标解释'],
    '社交与界面': ['人物介绍与界面示意', '对比、对话或行动提示'],
    '循环与背景': ['标题背板与氛围衬底', '有意使用的图形过场'],
}
AVOID = {
    'Logo与品牌': ['不要代替本用户已确定的固定片尾', '不应遮挡证据或频繁打断口播'],
    '文字与标题': ['长段字幕不直接塞入大标题', '按实际画幅重新检查安全区'],
    '转场': ['不要在一句话尚未说完时强切', '不将演示色块当成已接入的真实素材'],
    '数据与图表': ['示意数据不能当成真实业绩或改善结果', '无可靠数据时不用图表暗示结论'],
    '社交与界面': ['虚构对话与界面不能当成客户见证', '未接入真人的图形人物不得冒充用户'],
    '循环与背景': ['不要替代有证据价值的实拍画面', '背景运动不能干扰正文阅读'],
}

def run(args):
    return subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--partial', action='store_true', help='Review currently available assets without writing the final registry.')
    ap.add_argument('--record-reviewed', action='store_true', help='Record human contact-sheet review only after the operator actually viewed every sheet.')
    args = ap.parse_args()
    if args.record_reviewed:
        record = json.loads((WORK / 'verification.json').read_text(encoding='utf-8'))
        registry_path = REPO / 'templates/remotion-library.json'
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        assert record['checked_count'] == len(registry['entries']) == 55
        for check in record['checks']:
            current = OUT / (check['id'] + '.mp4')
            assert hashlib.sha256(current.read_bytes()).hexdigest() == check['sha256'], 'Changed after review: '+check['id']
        assert len(record['contact_sheets']) == 7 and all(Path(p).is_file() for p in record['contact_sheets'])
        scope = '55项真实Remotion渲染；每项完整解码、帧数、比例、静音及2 MB限额通过；实际查看每项18%/52%/82%编码帧联系表。不是逐帧连续观看，不代表其他画幅、真人合成、用户审美认可或最终视频QA。'
        record['visual_review'] = {'state':'contact_sheets_reviewed','scope':scope,'continuous_watch_listen':False}
        for entry in registry['entries']:
            entry['validation'] = {'state':'validated_demo','scope':scope}
        (WORK / 'verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        registry_path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Recorded actual review of all 55 demos; current hashes matched.')
        return
    catalog = json.loads((EXT / 'template-catalog.json').read_text(encoding='utf-8'))
    expected = catalog['compositions']
    sources = {x['id']: x for x in catalog['sources']}
    props = json.loads((EXT / 'src/template-gallery/chinese-props.json').read_text(encoding='utf-8'))
    items = [x for x in expected if (OUT / (x['composition_id'] + '.mp4')).is_file()]
    if not args.partial and len(items) != 55:
        raise RuntimeError(f'Expected 55 videos, found {len(items)}')
    snapshots = WORK / 'decoded-stills'
    snapshots.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(FONT), 24)
    smallfont = ImageFont.truetype(str(FONT), 18)
    entries, checks = [], []
    for item in items:
        ident = item['composition_id']
        path = OUT / (ident + '.mp4')
        meta = json.loads(run([FFPROBE, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', path]).stdout)
        video = next(s for s in meta['streams'] if s['codec_type'] == 'video')
        assert not any(s['codec_type'] == 'audio' for s in meta['streams']), ident + ': unexpected audio'
        assert int(video['nb_read_frames']) == item['duration_frames'], ident + ': frame count mismatch'
        assert video['avg_frame_rate'] == '30/1', ident + ': fps mismatch'
        assert video['width'] * item['height'] == video['height'] * item['width'], ident + ': ratio mismatch'
        assert path.stat().st_size < 2_000_000, ident + ': exceeds 2 MB'
        run([FFMPEG, '-v', 'error', '-i', path, '-f', 'null', '-'])
        frames = sorted(set([max(1, int(item['duration_frames'] * n)) for n in (.18, .52, .82)]))
        hashes = []
        for n, frame in enumerate(frames):
            snap = snapshots / f'{ident}-{n}.jpg'
            run([FFMPEG, '-y', '-v', 'error', '-i', path, '-vf', rf'select=eq(n\,{frame})', '-frames:v', 1, '-q:v', '2', snap])
            hashes.append(hashlib.sha256(snap.read_bytes()).hexdigest())
        assert len(set(hashes)) > 1, ident + ': sampled frames did not change'
        check = {'id': ident, 'full_decode_exit': 0, 'frames': int(video['nb_read_frames']), 'width':video['width'], 'height':video['height'], 'fps':'30/1', 'bytes': path.stat().st_size, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'audio_streams':0, 'sample_frames':frames, 'sample_hashes':hashes}
        checks.append(check)
        source = sources[item['source_id']]
        category = item['category_zh']
        uses = USE.get(category, ['可参数化的图形动画', '按表达任务选择局部使用'])
        avoid = AVOID.get(category, ['真实素材合成与其他比例须另测', '不声称演示等同于本条成片验收'])[:]
        label = '标题弹入' if ident == 'bounce-in-headline' else item['name_zh']
        base_item = next((x for x in expected if x['composition_id'] == item.get('base_composition_id')), item)
        description = '整段标题从上方弹入，带回弹。并非逐词分拍。' if ident == 'bounce-in-headline' else item.get('description_zh', base_item.get('description_zh', item['name_zh']))
        if item['kind'] == 'localized_example':
            description += '；已有基础模板的中文参数示例，不新增模板家族。'
        if ident in ('four-tone-mono-titler', 'pixel-typewriter-quote', 'pixel-candlestick-ohlc', 'pourover-drip-fill-gauge'):
            description += '；中文演示层使用 NotoSansSC 补字，保留原动画时序；原版像素字库只覆盖英文。'
        if ident == 'character-jumping':
            description += '；独立演示层修正原版重复扣除跳跃位移并降低跳高，防止角色跳出画框；原始源码未改。'
        if ident == 'community-chat':
            description += '；独立演示层把桌面尺寸字体放大，方便阅读竖版中文界面。'
        if ident == 'library-orbit':
            avoid.append('此项为几何人物占位；本人环绕效果另见口播效果16')
        if ident == 'library-text-mask':
            avoid.append('此项演示渐变填充；真人镂空视频另见口播效果11')
        if ident == 'end-card':
            avoid.append('只作模板展示，不能自动覆盖用户固定结尾模板')
        entry = {
            'id':'remotion-'+ident, 'label_zh':label, 'layer':'remotion', 'category_zh':category,
            'description_zh':description, 'uses_zh':uses, 'avoid_zh':avoid,
            'inputs_zh':['中文文案与颜色参数','按本条素材确认的时间长度','对应画幅的安全区检查'],
            'version':source['commit']+'+zh-gallery.1', 'source_url':source['repository']+'/tree/'+source['commit'],
            'source_id':item['source_id'], 'license':'MIT（模板源码）；Remotion 运行时与字体许可分别适用',
            'availability':'local_rendered_demo',
            'validation':{'state':'technical_pass_visual_samples_pending','scope':'真实 Remotion 渲染；完整解码、帧数、比例、静音、2 MB 限额与三个不同时点检查通过；待联系表人工查看；不代表连续观看、真人合成或最终视频 QA'},
            'demos':[{'kind':'source_render','path':'demos/remotion/'+ident+'.mp4','description_zh':'原注册动画的中文参数演示；静音；示例文字与数值不是实际业务结果','sha256':check['sha256'],'bytes':check['bytes']}],
            'ratio':'16:9' if item['width'] > item['height'] else '9:16' if item['width'] < item['height'] else '1:1',
            'composition_id':ident, 'registration_kind':item['kind'],
            'demo_dimensions':[video['width'],video['height']], 'duration_frames':item['duration_frames'],
            'default_parameters':props[ident],
        }
        if item.get('base_composition_id'): entry['base_composition_id'] = item['base_composition_id']
        entries.append(entry)
        print(ident + ': decode/frame/ratio/size/silence/motion-samples OK')
    sheets = []
    # Each tile shows actual encoded frames at 18%, 52% and 82%, with no stretched media.
    for page in range((len(items)+7)//8):
        subset = items[page*8:page*8+8]
        sheet = Image.new('RGB', (1440, len(subset)*190), '#102330')
        draw = ImageDraw.Draw(sheet)
        for row, item in enumerate(subset):
            y = row*190
            sheet_label = '标题弹入' if item['composition_id'] == 'bounce-in-headline' else item['name_zh']
            draw.text((16,y+5),sheet_label+' / '+item['composition_id'],font=font,fill='white')
            for col in range(3):
                img=Image.open(snapshots/f"{item['composition_id']}-{col}.jpg").convert('RGB')
                img.thumbnail((460,146))
                sheet.paste(img,(col*480+(460-img.width)//2,y+40+(146-img.height)//2))
        target=WORK/f'contact-{page+1:02}.jpg'
        sheet.save(target,quality=90)
        sheets.append(str(target))
    result={'schema_version':1,'registered_count':55,'checked_count':len(checks),'checks':checks,'contact_sheets':sheets,'continuous_watch_listen':False,'visual_review':'pending'}
    (WORK/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not args.partial:
        target=REPO/'templates/remotion-library.json'
        target.write_text(json.dumps({'schema_version':1,'updated_on':'2026-10-27','counting_note_zh':'55个注册项 = 50个 RenderComp 模板 + 2个 RemotionUI 适配演示 + 3个已有基础的中文参数示例；共52个实现基础，不与19项口播效果混加。','runtime':{'engine':'Remotion','version':'4.0.523','license_url':'https://www.remotion.dev/license'},'entries':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checked':len(checks),'contact_sheets':sheets,'registry_written':not args.partial},ensure_ascii=False))

if __name__ == '__main__': main()
