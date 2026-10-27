"""Build four frozen registry layers plus reviewed per-video integration records."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import re
import subprocess
from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['motiongit-styles.json', 'motiongit-controls.json',
           'remotion-library.json', 'presenter-effects.json']
LAYERS = {'style': '官网模板与片段', 'control': '官网动画控件',
          'remotion': '现有代码模板', 'effect': '真人口播特效'}
BASELINE_EXPECTED = {'style': 72, 'control': 70, 'remotion': 55, 'effect': 19}


def read_sources(root: Path):
    entries, previews, provenance = [], [], []
    for filename in SOURCES:
        path = root / 'templates' / filename
        raw = path.read_bytes()
        data = json.loads(raw)
        rows = data if isinstance(data, list) else data['entries']
        baseline_layer = list(BASELINE_EXPECTED)[SOURCES.index(filename)]
        if len(rows) != BASELINE_EXPECTED[baseline_layer] or any(e.get('layer') != baseline_layer for e in rows):
            raise ValueError('Frozen baseline counts changed in ' + filename)
        entries.extend(rows)
        if isinstance(data, dict):
            previews.extend(data.get('previews', []))
        provenance.append({'path': 'templates/' + filename,
                           'sha256': sha256(raw).hexdigest(), 'entries': len(rows)})
    counts = Counter(e['layer'] for e in entries)
    if dict(counts) != BASELINE_EXPECTED:
        raise ValueError(f'Frozen baseline counts changed: {dict(counts)}; expected {BASELINE_EXPECTED}')
    return entries, previews, provenance


def validate(entries, gallery: Path, strict: bool):
    identifiers, counts, local_paths = set(), Counter(), set()
    for entry in entries:
        required = ['id', 'label_zh', 'layer', 'category_zh', 'description_zh',
                    'uses_zh', 'avoid_zh', 'inputs_zh', 'source_url', 'source_id', 'version', 'license', 'availability', 'validation', 'demos']
        for key in required:
            if key not in entry:
                raise ValueError(f"{entry.get('id')}: missing {key}")
        if entry['id'] in identifiers:
            raise ValueError('Duplicate ID: ' + entry['id'])
        identifiers.add(entry['id'])
        if entry['layer'] not in LAYERS:
            raise ValueError('Unknown catalog layer: ' + str(entry['layer']))
        counts[entry['layer']] += 1
        if not entry['demos'] and strict:
            raise ValueError(entry['id'] + ': no demo')
        for demo in entry['demos']:
            if demo.get('path'):
                path = (gallery / demo['path']).resolve()
                if not path.is_relative_to((gallery / 'demos').resolve()):
                    raise ValueError('Demo outside approved directory: ' + str(path))
                if strict and not path.is_file():
                    raise ValueError('Missing demo: ' + str(path))
                if path.is_file() and path.stat().st_size > 8 * 1024 * 1024:
                    raise ValueError('Demo exceeds 8 MiB: ' + str(path))
                local_paths.add(path)
            elif urlsplit(demo.get('url', '')).scheme != 'https':
                raise ValueError(entry['id'] + ': invalid demo URL')
    return counts, local_paths


def required_text(value, context):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(context + ': expected nonempty text')
    return value


def official_url(value, context):
    required_text(value, context)
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError(context + ': expected official HTTPS source without credentials')
    return value


def verify_integration_demo(root, demo, strict):
    """Validate a reviewed own clip; never acquire packages or render media."""
    if demo.get('kind') != 'own' or not str(demo.get('path', '')).endswith('.mp4'):
        raise ValueError('Integration requires a local own MP4 demo')
    gallery = root / 'docs/template-gallery'
    path = (gallery / demo['path']).resolve()
    if not path.is_relative_to((gallery / 'demos').resolve()):
        raise ValueError('Integration demo outside approved directory')
    if not path.is_file():
        raise ValueError('Integration demo missing: ' + demo['path'])
    if not re.fullmatch(r'[0-9a-f]{64}', str(demo.get('sha256', ''))):
        raise ValueError('Integration requires reviewed SHA256')
    if demo.get('bytes') != path.stat().st_size or sha256(path.read_bytes()).hexdigest() != demo['sha256']:
        raise ValueError('Integration demo changed after review')
    if not 0 < path.stat().st_size <= 8 * 1024 * 1024:
        raise ValueError('Integration demo exceeds curated size limit')
    required_text(demo.get('description_zh'), 'Integration demo description')
    if strict:
        ff = root / '.runtime/ffmpeg/bin/ffmpeg.exe'
        probe = ff.with_name('ffprobe.exe')
        result = subprocess.run([str(probe), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], capture_output=True, check=True)
        media = json.loads(result.stdout)
        if sum(s['codec_type'] == 'video' for s in media['streams']) != 1 or any(s['codec_type'] == 'audio' for s in media['streams']):
            raise ValueError('Integration demo must contain one video and no audio')
        if not 0 < float(media['format']['duration']) <= 20:
            raise ValueError('Integration demo must be a curated excerpt of at most 20 seconds')
        decoded = subprocess.run([str(ff), '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'], capture_output=True)
        if decoded.returncode or decoded.stderr.strip():
            raise ValueError('Integration demo failed full decode')


def apply_integrations(root, entries, strict):
    """Attach version-scoped cases, never promote the frozen source validation."""
    path = root / 'templates/template-integrations.json'
    if not path.is_file():
        return entries, [], None
    raw = path.read_bytes(); data = json.loads(raw)
    if data.get('schema_version') != 1 or not isinstance(data.get('integrations'), list):
        raise ValueError('Invalid integration overlay schema')
    merged = deepcopy(entries); by_id = {e['id']: e for e in merged}
    seen = set(); records = []
    for record in data['integrations']:
        ident = record.get('id', '')
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', ident) or ident in seen:
            raise ValueError('Invalid or duplicate integration ID: ' + str(ident))
        seen.add(ident)
        target = required_text(record.get('entry_id'), ident + ' entry_id')
        required_text(record.get('project_id'), ident + ' project_id')
        stamp = datetime.fromisoformat(required_text(record.get('integrated_at'), ident + ' integrated_at').replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError(ident + ': integrated_at needs timezone')
        source = record.get('source', {})
        official_url(source.get('url'), ident + ' source')
        for key in ['package_id', 'version', 'verification_note']:
            required_text(source.get(key), ident + ' source.' + key)
        if source.get('official') is not True or not re.fullmatch(r'[0-9a-f]{64}', str(source.get('sha256', ''))):
            raise ValueError(ident + ': official provenance and exact package/revision hash required')
        invoke = record.get('invocation', {})
        for key in ['method', 'command']:
            required_text(invoke.get(key), ident + ' invocation.' + key)
        official_url(invoke.get('guide_url'), ident + ' guide')
        if not isinstance(invoke.get('inputs_zh'), list) or not invoke['inputs_zh'] or not all(isinstance(x, str) and x.strip() for x in invoke['inputs_zh']):
            raise ValueError(ident + ': input requirements missing')
        rights = record.get('rights', {})
        if rights.get('private_demo_redistribution') is not True:
            raise ValueError(ident + ': private demo redistribution rights required')
        required_text(rights.get('evidence'), ident + ' rights evidence')
        qa = record.get('qa', {})
        if qa.get('decode_verified') is not True or qa.get('sample_images_viewed') is not True or qa.get('state') != 'verified_demo':
            raise ValueError(ident + ': actual decoded and visually reviewed demo required')
        required_text(qa.get('scope'), ident + ' QA scope')
        demo = deepcopy(record.get('demo', {}))
        verify_integration_demo(root, demo, strict)
        if target not in by_id:
            new = deepcopy(record.get('new_entry'))
            if not isinstance(new, dict) or new.get('id') != target or new.get('layer') not in LAYERS:
                raise ValueError(ident + ': unknown entry requires a complete new_entry in an existing layer')
            if new.get('source_url') != source['url']:
                raise ValueError(ident + ': new entry must bind the verified official source')
            if new.get('demos'):
                raise ValueError(ident + ': new entry demos must come from its reviewed integration record')
            new['demos'] = []
            new['validation'] = {'state': 'integrated_case_verified', 'scope': 'Only the linked version and per-video demo are verified; other variants, future inputs and full-film QA are not implied.'}
            new['integration_origin'] = ident
            merged.append(new); by_id[target] = new
        elif 'new_entry' in record:
            raise ValueError(ident + ': new_entry cannot overwrite an existing entry')
        row = by_id[target]
        demo['integration_id'] = ident
        cases = row.setdefault('integrations', [])
        cases.append(deepcopy(record))
        cases.sort(key=lambda c: datetime.fromisoformat(c['integrated_at'].replace('Z', '+00:00')), reverse=True)
        # Keep prior demos and baseline provenance. Only the first preview changes.
        case_demos = [dict(c['demo'], integration_id=c['id']) for c in cases]
        ordered = case_demos + [d for d in row['demos'] if not d.get('integration_id')]
        unique = {}; row['demos'] = []
        for item in ordered:
            key = item.get('path') or item.get('url')
            if key in unique:
                if unique[key].get('sha256') != item.get('sha256'):
                    raise ValueError(ident + ': reused demo path has conflicting hashes')
                continue
            unique[key] = item; row['demos'].append(item)
        row['latest_integration_id'] = cases[0]['id']
        records.append(deepcopy(record))
    # Paths may be reused within one entry, but must never overwrite another entry.
    owners = {}
    for row in merged:
        for demo in row.get('demos', []):
            if demo.get('path'):
                key = (root / 'docs/template-gallery' / demo['path']).resolve()
                if key in owners and owners[key] != row['id']:
                    raise ValueError('Demo path shared across entries: ' + demo['path'])
                owners[key] = row['id']
    provenance = {'path': 'templates/template-integrations.json', 'sha256': sha256(raw).hexdigest(), 'records': len(records)}
    return merged, records, provenance


def demo_href(demo, markdown=False):
    if demo.get('path'):
        return ('../docs/template-gallery/' if markdown else '') + demo['path']
    return demo.get('url', '')


HTML = r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>AGI TOP · 中文剪辑模板中心</title>
<style>
:root{font-family:"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif;color:#153340;background:#f4f7f9;--cyan:#148bad}*{box-sizing:border-box}body{margin:0}header{background:#153340;color:white;padding:34px max(24px,calc((100vw - 1400px)/2));border-top:5px solid #47b4d0}h1{font-size:30px;margin:8px 0 12px}p{line-height:1.75}header p{max-width:1100px;color:#d4e4eb;font-size:14px}.topline{font-size:12px;letter-spacing:.08em;color:#77d8ed}.stats{display:flex;gap:12px;flex-wrap:wrap;margin-top:18px}.stat{border:1px solid #3c606d;padding:10px 18px;border-radius:10px}.stat strong{font-size:24px;margin-right:6px}main{max-width:1448px;padding:24px;margin:auto}.notice{border:1px solid #c4d9e2;background:#eaf5f8;padding:14px 18px;border-radius:10px;font-size:13px}.toolbar{position:sticky;top:0;background:#f4f7f9f5;backdrop-filter:blur(8px);z-index:3;padding:16px 0;display:flex;gap:9px;flex-wrap:wrap}input,select,button{font:inherit;border:1px solid #c6d6df;border-radius:8px;padding:10px 12px;background:white;color:#153340}input{flex:1;min-width:230px}button{cursor:pointer}button.active{background:#153340;color:white}.tabs{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:20px}.card{background:white;border:1px solid #dce6eb;border-radius:13px;overflow:hidden;box-shadow:0 2px 7px #15334008}.preview{background:#0a1820;height:215px;display:flex;align-items:center;justify-content:center}.preview video{width:100%;height:100%;object-fit:contain}.body{padding:17px}.body h3{font-size:18px;margin:8px 0}.body p{font-size:13px;margin:9px 0}.eyebrow{font-size:11px;color:#507582}.chips{display:flex;gap:5px;flex-wrap:wrap}.chip{font-size:11px;background:#e8f4f8;border-radius:5px;padding:4px 7px;color:#126581}.status{background:#f0f2f4;color:#5e6870}details{font-size:12px;line-height:1.8;margin-top:12px;border-top:1px solid #edf1f4;padding-top:10px}summary{cursor:pointer;font-weight:600}ul{padding-left:18px;margin:7px 0}.links{display:flex;gap:12px;font-size:12px;margin-top:12px}a{color:#08769a;text-decoration:none}a:hover{text-decoration:underline}.result{font-size:13px;margin:15px 0;color:#567080}.empty{padding:60px;text-align:center}.routes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:20px 0}.route{border:1px solid #d4e3ea;border-radius:10px;padding:14px;background:white;font-size:12px}.route strong{font-size:15px}.route p{margin:8px 0}.foot{font-size:12px;color:#66808b;margin:30px 0}dialog{border:0;border-radius:12px;max-width:95vw;padding:15px}dialog::backdrop{background:#000a}dialog video{max-width:90vw;max-height:80vh}.small{font-size:11px;color:#6a828e}.preview-only{margin:20px 0;padding:15px;border:1px dashed #a6bfc9;border-radius:10px}@media(max-width:600px){h1{font-size:24px}main{padding:15px}.toolbar{position:static}.grid{grid-template-columns:1fr}}
</style>
<header><div class="topline">AGI TOP / TEMPLATE CENTER / 中文目录</div><h1>先看效果，再选择适合内容的模板</h1>
<p>整套风格、动画控件、代码模板与真人特效分别登记。中文名称、使用条件、来源和 Demo 放在同一个入口；有演示不等于已通过新片验收。</p>
<div class="stats">__STATS__</div></header>
<main><div class="notice">本次 B 版获认可的是局部重点文字效果。模板按实际内容选择，不强套整片。官网 Demo 需要联网；本地控件 Demo 为静音版式演示，示例数值与模拟界面不代表真实业务成果。个人 .motion、Key 和完整原片不在本目录。</div>
<div class="routes"><div class="route"><strong>知识口播</strong><p>讲述与原意驱动画面。优先字幕、概念解释、重点句与关系图。</p></div><div class="route"><strong>系统实操</strong><p>真实按钮与操作证据优先。放大、标注须指向实际目标。</p></div><div class="route"><strong>长访谈切片</strong><p>先按独立主题剪成完整论点，再添加包装与字幕。</p></div><div class="route"><strong>旅行 / Vlog</strong><p>按地点、事件、镜头连续性、环境声与音乐节奏剪辑；当前仅定义路线边界，未实现专用自动流程。</p></div></div>
<div class="tabs" id="tabs"></div><div class="toolbar"><input id="search" aria-label="搜索模板" placeholder="搜索中文名称、用途、控件ID…"><select id="category" aria-label="分类"><option value="">全部分类</option></select><select id="demoType" aria-label="Demo来源"><option value="">全部Demo来源</option><option value="local">本地实际演示</option><option value="official">官方在线演示</option></select><button id="reset">重置</button></div>
<div class="result" id="result"></div><div class="grid" id="grid"></div><div id="extra"></div>
<p class="foot">来源、许可证与更新口径：<a href="https://github.com/Isaac3113/talking-head-editor/blob/main/templates/PROVENANCE.zh-CN.md">来源说明</a> · <a href="https://github.com/Isaac3113/talking-head-editor/blob/main/templates/README.zh-CN.md">完整中文清单</a> · <a href="https://github.com/Isaac3113/talking-head-editor/blob/main/docs/template-gallery/CATEGORIES.md">分类动画预览</a> · <a href="https://github.com/Isaac3113/talking-head-editor/blob/main/skill/talking-head-editor/references/template-selection.md">Skill选择规则</a><br>2026-10-27长期授权：以后每片经QA精选的本人静音Demo与集成说明可进入私人Git；完整原片、完整成片、源人像蒙版、Key、个人包与客户敏感信息不进入Git。这不是公开发布授权。其他电脑仍需独立准备运行环境、个人模板授权和新片素材。</p></main>
<script>const DATA=__DATA__;const LAYERS=__LAYERS__;
function integrationInfo(e){if(!e.integrations?.length)return '';const c=e.integrations[0],s=c.source,i=c.invocation;return '<details><summary>本片接入与复用边界</summary><p>'+esc(c.project_id+' · '+s.package_id+' · '+s.version)+'</p><p>输入：'+esc(i.inputs_zh.join('；'))+'</p><p>调用：<code>'+esc(i.command)+'</code></p><p>本片检查：'+esc(c.qa.scope)+'</p><p>仅此版本与Demo；原条目和全部变体验证状态不因此改变。</p></details>'}
const stateName=x=>({'integrated_case_verified':'仅本片接入已检查','registered':'已登记，演示生成中','registered_pending_render':'演示生成中','validated_demo':'本机演示已检查','verified':'本机演示已检查','rendered_verified':'本机演示已检查'}[x]||x);const availabilityName=x=>({'local_rendered_demo':'已有本地演示','available':'可按条件使用','registered_pending_render':'本地演示生成中'}[x]||x);const $=x=>document.getElementById(x), esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let layer='';
function safe(x){return typeof x==='string'&&(x.startsWith('https://')||x.startsWith('demos/'))?esc(x):''}
function bullet(items){return '<ul>'+(items||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'}
function renderTabs(){const tabs=[['','全部'],...Object.entries(LAYERS)];$('tabs').innerHTML=tabs.map(([id,label])=>'<button data-layer="'+id+'" class="'+(layer===id?'active':'')+'">'+label+'</button>').join('');$('tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>{layer=b.dataset.layer;renderTabs();render()})}
function render(){const q=$('search').value.trim().toLowerCase(),cat=$('category').value,type=$('demoType').value;const rows=DATA.entries.filter(e=>(!layer||e.layer===layer)&&(!cat||e.category_zh===cat)&&(!q||JSON.stringify(e).toLowerCase().includes(q))&&(!type||e.demos.some(d=>type==='local'?d.path:!d.path)));
$('result').textContent='显示 '+rows.length+' / '+DATA.entries.length+' 条；这些条目属于不同层级，不相加称为完整视频模板。';
$('grid').innerHTML=rows.map(e=>{if(!e.demos.length)return '<article class="card"><div class="preview"><p style="color:white">演示生成中</p></div><div class="body"><div class="eyebrow">'+esc(LAYERS[e.layer])+'</div><h3>'+esc(e.label_zh)+'</h3><p>'+esc(e.description_zh)+'</p><span class="chip status">尚未完成真实演示</span></div></article>';const d=e.demos[0],src=safe(d.path||d.url),poster=d.poster_path||'',latest=e.integrations?.[0];return '<article class="card"><div class="preview"><video controls muted playsinline preload="none" '+(poster?'poster="'+safe(poster)+'"':'')+' src="'+src+'" aria-label="'+esc(e.label_zh)+' Demo"></video></div><div class="body"><div class="eyebrow">'+esc(LAYERS[e.layer])+' · '+esc(e.id)+'</div><h3>'+esc(e.label_zh)+'</h3><div class="chips"><span class="chip">'+esc(e.category_zh)+'</span><span class="chip status">'+esc(stateName(e.validation.state))+'</span></div><p>'+esc(e.description_zh)+'</p><p class="small">'+esc(d.description_zh||'')+'</p>'+(latest?'<p class="small">当前本人Demo版本：'+esc(latest.source.version)+' · 本片QA：'+esc(latest.qa.state)+'（仅已解码与抽帧检查）</p>':'')+'<details><summary>适用情况、输入与验证边界</summary><b>适合</b>'+bullet(e.uses_zh)+'<b>需要</b>'+bullet(e.inputs_zh)+'<b>注意</b>'+bullet(e.avoid_zh)+'<p>'+esc(e.validation.scope)+'</p><p>登记基线版本：'+esc(e.version||'见来源')+'<br>许可：'+esc(e.license||'见来源；素材另核')+'<br>可取得状态：'+esc(availabilityName(e.availability)||'按实际环境核对')+'</p>'+(e.variants?.length?'<b>变体（不表示全部实测）</b>'+bullet(e.variants.map(v=>typeof v==='string'?v:((v.label_zh||v.id)+' / '+v.id))):'')+'</details><div class="links"><a href="'+src+'" target="_blank" rel="noopener">打开Demo</a>'+(e.source_url?'<a href="'+esc(e.source_url)+'" target="_blank" rel="noopener">原始来源</a>':'')+'</div>'+(e.demos.length>1?'<p class="small">其他演示：'+e.demos.slice(1).map((x,i)=>'<a target="_blank" rel="noopener" href="'+safe(x.path||x.url)+'">'+esc(x.description_zh||('版本'+(i+2)))+'</a>').join(' · ')+'</p>':'')+integrationInfo(e)+'</div></article>'}).join('')||'<div class="empty">没有匹配项，试试另一个关键词。</div>';
document.querySelectorAll('video').forEach(v=>v.addEventListener('play',()=>document.querySelectorAll('video').forEach(other=>{if(other!==v)other.pause()})));
}
const categories=[...new Set(DATA.entries.map(e=>e.category_zh))].sort((a,b)=>a.localeCompare(b,'zh'));categories.forEach(c=>{let o=document.createElement('option');o.value=c;o.textContent=c;$('category').append(o)});
['search','category','demoType'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));$('reset').onclick=()=>{layer='';$('search').value='';$('category').value='';$('demoType').value='';renderTabs();render()};
if(DATA.previews.length)$('extra').innerHTML='<div class="preview-only"><strong>附加预览，不计入模板条目</strong>'+DATA.previews.map(p=>'<p><a target="_blank" rel="noopener" href="'+safe(p.url||p.demo||p.demoUrl||p.demos?.[0]?.url)+'">'+esc(p.label_zh||p.title||p.name||'3D书籍预览')+'</a> · 仅供效果预览，获取状态见来源。</p>').join('')+'</div>';
renderTabs();render();</script></html>'''


def build(root: Path, strict=False):
    gallery = root / 'docs/template-gallery'
    gallery.mkdir(parents=True, exist_ok=True)
    entries, previews, provenance = read_sources(root)
    entries, integrations, integration_source = apply_integrations(root, entries, strict)
    entries.sort(key=lambda e: (0 if e['id']=='mg-style-314486' else 1 if e['layer']=='style' and e['category_zh']=='口播与讲解' else 2 if e['layer']=='style' else 3))
    counts, local_paths = validate(entries, gallery, strict)
    data = {'schema': 'talking-head-template-center/1', 'updated_on': datetime.now().astimezone().date().isoformat(),
            'counts_by_layer': dict(counts), 'build_mode':'complete' if strict else 'draft', 'counts_are_not_additive_templates': True,
            'sources': provenance, 'baseline_counts_by_layer': BASELINE_EXPECTED,
            'integration_source': integration_source, 'integrations': integrations,
            'entries': entries, 'previews': previews}
    for entry in entries:
        for demo in entry.get('demos', []):
            if demo.get('path'):
                poster = Path(demo['path']).with_suffix('.jpg')
                demo['poster_path'] = poster.as_posix() if (gallery / poster).is_file() else ''
    (root/'templates/catalog.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    page = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('<', chr(92)+'u003c'))
    page = page.replace('__LAYERS__', json.dumps(LAYERS, ensure_ascii=False))
    page = page.replace('__STATS__', ''.join(f'<div class="stat"><strong>{counts[k]}</strong>{escape(v)}</div>' for k,v in LAYERS.items()) + f'<div class="stat"><strong>{len(integrations)}</strong>本片接入记录（不重复计为模板）</div>')
    if not strict:
        page=page.replace('<main><div class="notice">','<main><div class="notice">开发预览：部分演示仍在制作，不能当成全部完成。<br>')
    (gallery/'index.html').write_text(page, encoding='utf-8')
    md = ['# 中文剪辑模板中心', '', '由四份固定基线和独立接入记录生成。更新后运行 `scripts/build_template_gallery.py --strict`，不要手工维护另一套重复清单。', '',
          '本次B版获认可的是局部重点文字效果。目录完整性、实际运行和新片验收分别记录；有Demo不代表自动适合口播。', '',
          '| 层级 | 数量 | 计数说明 |', '|---|---:|---|',
          f'| 官网集合 | {counts["style"]} | 基线72项，加已验证的新候选；不是全站总数 |',
          f'| 官网控件 | {counts["control"]} | 原包基线70项/210变体冻结，新接入另记版本；不代表所有变体实测 |',
          f'| 代码库注册项 | {counts["remotion"]} | 基线55注册项/52实现基础，新接入按来源区分 |',
          f'| 真人特效分支 | {counts["effect"]} | 基线19分支；不是完整剪辑系统 |',
          f'| 本片接入记录 | {len(integrations)} | 版本与本人Demo记录，不加入上方模板条目总数 |', '',
          '## 浏览方式', '',
          'GitHub里可按下方中文分类直接打开每条Demo；在本机运行以下命令打开可搜索、可播放的完整目录：', '',
          '```powershell', 'Set-Location "C:\\Codex Workspace\\talking-head-editor"',
          '.\\.venv\\Scripts\\python.exe scripts/serve_template_gallery.py', '```', '',
          '浏览器访问命令返回的本机地址。官网示例需要联网，本地演示随仓库同步。', '',
          '[分类动画预览](../docs/template-gallery/CATEGORIES.md) · [来源与中文化说明](PROVENANCE.zh-CN.md) · [路线边界](../skill/talking-head-editor/references/editing-routes.md) · [模板选择规则](../skill/talking-head-editor/references/template-selection.md)', '']
    for layer, title in LAYERS.items():
        md += ['## '+title, '']
        rows = [e for e in entries if e['layer']==layer]
        for category in sorted({e['category_zh'] for e in rows}):
            md += ['### '+category, '', '| 名称 | 用途 | 当前验证 | Demo |', '|---|---|---|---|']
            for e in (x for x in rows if x['category_zh']==category):
                links = ' / '.join('[演示'+str(i+1)+']('+demo_href(d, True)+')' for i,d in enumerate(e['demos']))
                md.append('| '+escape(e['label_zh']).replace('|','／')+' `'+e['id']+'` | '+e['description_zh'].replace('|','／').replace('\n',' ')+' | '+{'validated_demo':'本机演示已检查','verified':'本机演示已检查','registered':'演示制作中','rendered_verified':'本机演示已检查'}.get(e['validation']['state'],e['validation']['state']).replace('|','／')+' | '+links+' |')
            for e in (x for x in rows if x['category_zh']==category and x.get('integrations')):
                c=e['integrations'][0]
                md += ['- `'+e['id']+'` 登记基线版本：'+e.get('version','见来源')+'；当前本人Demo版本：'+c['source']['version']+'；本片QA：'+c['qa']['state']+'。'+c['qa']['scope']+'（不改变原条目验证范围，不代表用户审美认可）']
            md.append('')
    md += ['## 附加预览', '', '3D书籍等preview只作为效果参考，不计入上方目录条目；可取得情况按官网当前页面核对。', '',
           '个人.motion与Key、原始口播、完整成片、旧工作记录、依赖及保护内核不进入本目录或Git。', '']
    for preview in previews:
        for demo in preview.get('demos',[]):
            md += ['['+preview.get('label_zh','附加效果预览')+']('+demo.get('url','')+')', '']
    (root/'templates/README.zh-CN.md').write_text('\n'.join(md), encoding='utf-8')
    (gallery/'README.md').write_text('# 可播放中文模板中心\n\n[完整中文清单](https://github.com/Isaac3113/talking-head-editor/blob/main/templates/README.zh-CN.md) · [来源说明](https://github.com/Isaac3113/talking-head-editor/blob/main/templates/PROVENANCE.zh-CN.md)\n\n本机运行 `python scripts/serve_template_gallery.py` 查看可搜索目录。`index.html` 是由机器登记表生成的浏览入口；GitHub本身不会把HTML作为网站执行。\n\n2026-10-27长期授权：`demos/`可收以后每片经QA精选的本人静音Demo与集成说明，限私人Git。完整原片、完整成片、源人像蒙版、Key、个人包和客户敏感信息不进入Git；本规则不授权公开。静音动画演示不代表完整声画剪辑已通过。\n', encoding='utf-8')
    return {'entries':len(entries), 'counts':dict(counts), 'local_demo_files':len(local_paths), 'integration_records':len(integrations), 'strict':strict}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--strict',action='store_true')
    args=p.parse_args();print(json.dumps(build(args.root.resolve(),args.strict),ensure_ascii=False))
