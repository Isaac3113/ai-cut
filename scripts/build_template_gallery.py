"""Build the Chinese template center from four source registries, not copied tables."""
from __future__ import annotations

import argparse
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
EXPECTED = {'style': 72, 'control': 70, 'remotion': 55, 'effect': 19}


def read_sources(root: Path):
    entries, previews, provenance = [], [], []
    for filename in SOURCES:
        path = root / 'templates' / filename
        raw = path.read_bytes()
        data = json.loads(raw)
        rows = data if isinstance(data, list) else data['entries']
        entries.extend(rows)
        if isinstance(data, dict):
            previews.extend(data.get('previews', []))
        provenance.append({'path': 'templates/' + filename,
                           'sha256': sha256(raw).hexdigest(), 'entries': len(rows)})
    return entries, previews, provenance


def validate(entries, gallery: Path, strict: bool):
    identifiers, counts, local_paths = set(), Counter(), set()
    for entry in entries:
        required = ['id', 'label_zh', 'layer', 'category_zh', 'description_zh',
                    'uses_zh', 'avoid_zh', 'inputs_zh', 'source_url', 'validation', 'demos']
        for key in required:
            if key not in entry:
                raise ValueError(f"{entry.get('id')}: missing {key}")
        if entry['id'] in identifiers:
            raise ValueError('Duplicate ID: ' + entry['id'])
        identifiers.add(entry['id'])
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
    if dict(counts) != EXPECTED:
        raise ValueError(f'Unexpected catalog counts: {dict(counts)}; expected {EXPECTED}')
    return counts, local_paths


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
<div class="stats"><div class="stat"><strong>72</strong>官网集合条目</div><div class="stat"><strong>70</strong>控件 · 210变体</div><div class="stat"><strong>55</strong>代码库注册项</div><div class="stat"><strong>19</strong>真人效果分支</div></div></header>
<main><div class="notice">本次 B 版获认可的是局部重点文字效果。模板按实际内容选择，不强套整片。官网 Demo 需要联网；本地控件 Demo 为静音版式演示，示例数值与模拟界面不代表真实业务成果。个人 .motion、Key 和完整原片不在本目录。</div>
<div class="routes"><div class="route"><strong>知识口播</strong><p>讲述与原意驱动画面。优先字幕、概念解释、重点句与关系图。</p></div><div class="route"><strong>系统实操</strong><p>真实按钮与操作证据优先。放大、标注须指向实际目标。</p></div><div class="route"><strong>长访谈切片</strong><p>先按独立主题剪成完整论点，再添加包装与字幕。</p></div><div class="route"><strong>旅行 / Vlog</strong><p>按地点、事件、镜头连续性、环境声与音乐节奏剪辑；当前仅定义路线边界，未实现专用自动流程。</p></div></div>
<div class="tabs" id="tabs"></div><div class="toolbar"><input id="search" aria-label="搜索模板" placeholder="搜索中文名称、用途、控件ID…"><select id="category" aria-label="分类"><option value="">全部分类</option></select><select id="demoType" aria-label="Demo来源"><option value="">全部Demo来源</option><option value="local">本地实际演示</option><option value="official">官方在线演示</option></select><button id="reset">重置</button></div>
<div class="result" id="result"></div><div class="grid" id="grid"></div><div id="extra"></div>
<p class="foot">来源、许可证与更新口径：<a href="https://github.com/Isaac3113/talking-head-editor/blob/main/templates/PROVENANCE.zh-CN.md">来源说明</a> · <a href="https://github.com/Isaac3113/talking-head-editor/blob/main/templates/README.zh-CN.md">完整中文清单</a> · <a href="https://github.com/Isaac3113/talking-head-editor/blob/main/docs/template-gallery/CATEGORIES.md">分类动画预览</a> · <a href="https://github.com/Isaac3113/talking-head-editor/blob/main/skill/talking-head-editor/references/template-selection.md">Skill选择规则</a><br>GitHub只同步经过整理的目录、受许可源码及本次明确授权的演示小样。其他电脑仍需独立准备运行环境、个人模板授权和新片素材。</p></main>
<script>const DATA=__DATA__;const LAYERS=__LAYERS__;
const stateName=x=>({'registered':'已登记，演示生成中','registered_pending_render':'演示生成中','validated_demo':'本机演示已检查','verified':'本机演示已检查','rendered_verified':'本机演示已检查'}[x]||x);const availabilityName=x=>({'local_rendered_demo':'已有本地演示','available':'可按条件使用','registered_pending_render':'本地演示生成中'}[x]||x);const $=x=>document.getElementById(x), esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let layer='';
function safe(x){return typeof x==='string'&&(x.startsWith('https://')||x.startsWith('demos/'))?esc(x):''}
function bullet(items){return '<ul>'+(items||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'}
function renderTabs(){const tabs=[['','全部'],...Object.entries(LAYERS)];$('tabs').innerHTML=tabs.map(([id,label])=>'<button data-layer="'+id+'" class="'+(layer===id?'active':'')+'">'+label+'</button>').join('');$('tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>{layer=b.dataset.layer;renderTabs();render()})}
function render(){const q=$('search').value.trim().toLowerCase(),cat=$('category').value,type=$('demoType').value;const rows=DATA.entries.filter(e=>(!layer||e.layer===layer)&&(!cat||e.category_zh===cat)&&(!q||JSON.stringify(e).toLowerCase().includes(q))&&(!type||e.demos.some(d=>type==='local'?d.path:!d.path)));
$('result').textContent='显示 '+rows.length+' / '+DATA.entries.length+' 条；这些条目属于不同层级，不相加称为完整视频模板。';
$('grid').innerHTML=rows.map(e=>{if(!e.demos.length)return '<article class="card"><div class="preview"><p style="color:white">演示生成中</p></div><div class="body"><div class="eyebrow">'+esc(LAYERS[e.layer])+'</div><h3>'+esc(e.label_zh)+'</h3><p>'+esc(e.description_zh)+'</p><span class="chip status">尚未完成真实演示</span></div></article>';const d=e.demos[0],src=safe(d.path||d.url),poster=d.path?(d.path.slice(0,d.path.lastIndexOf('.'))+'.jpg'):'';return '<article class="card"><div class="preview"><video controls muted playsinline preload="none" '+(poster?'poster="'+safe(poster)+'"':'')+' src="'+src+'" aria-label="'+esc(e.label_zh)+' Demo"></video></div><div class="body"><div class="eyebrow">'+esc(LAYERS[e.layer])+' · '+esc(e.id)+'</div><h3>'+esc(e.label_zh)+'</h3><div class="chips"><span class="chip">'+esc(e.category_zh)+'</span><span class="chip status">'+esc(stateName(e.validation.state))+'</span></div><p>'+esc(e.description_zh)+'</p><p class="small">'+esc(d.description_zh||'')+'</p><details><summary>适用情况、输入与验证边界</summary><b>适合</b>'+bullet(e.uses_zh)+'<b>需要</b>'+bullet(e.inputs_zh)+'<b>注意</b>'+bullet(e.avoid_zh)+'<p>'+esc(e.validation.scope)+'</p><p>版本：'+esc(e.version||'见来源')+'<br>许可：'+esc(e.license||'见来源；素材另核')+'<br>可取得状态：'+esc(availabilityName(e.availability)||'按实际环境核对')+'</p>'+(e.variants?.length?'<b>变体（不表示全部实测）</b>'+bullet(e.variants.map(v=>typeof v==='string'?v:((v.label_zh||v.id)+' / '+v.id))):'')+'</details><div class="links"><a href="'+src+'" target="_blank" rel="noopener">打开Demo</a>'+(e.source_url?'<a href="'+esc(e.source_url)+'" target="_blank" rel="noopener">原始来源</a>':'')+'</div>'+(e.demos.length>1?'<p class="small">其他演示：'+e.demos.slice(1).map((x,i)=>'<a target="_blank" rel="noopener" href="'+safe(x.path||x.url)+'">'+esc(x.description_zh||('版本'+(i+2)))+'</a>').join(' · ')+'</p>':'')+'</div></article>'}).join('')||'<div class="empty">没有匹配项，试试另一个关键词。</div>';
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
    entries.sort(key=lambda e: (0 if e['id']=='mg-style-314486' else 1 if e['layer']=='style' and e['category_zh']=='口播与讲解' else 2 if e['layer']=='style' else 3))
    counts, local_paths = validate(entries, gallery, strict)
    data = {'schema': 'talking-head-template-center/1', 'updated_on': '2026-10-27',
            'counts_by_layer': dict(counts), 'build_mode':'complete' if strict else 'draft', 'counts_are_not_additive_templates': True,
            'sources': provenance, 'entries': entries, 'previews': previews}
    (root/'templates/catalog.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    page = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('<', chr(92)+'u003c'))
    page = page.replace('__LAYERS__', json.dumps(LAYERS, ensure_ascii=False))
    if not strict:
        page=page.replace('<main><div class="notice">','<main><div class="notice">开发预览：部分演示仍在制作，不能当成全部完成。<br>')
    (gallery/'index.html').write_text(page, encoding='utf-8')
    md = ['# 中文剪辑模板中心', '', '由四份来源登记表生成。更新后运行 `scripts/build_template_gallery.py --strict`，不要手工维护另一套重复清单。', '',
          '本次B版获认可的是局部重点文字效果。目录完整性、实际运行和新片验收分别记录；有Demo不代表自动适合口播。', '',
          '| 层级 | 数量 | 计数说明 |', '|---|---:|---|',
          '| 官网集合 | 72 | 包含整套模板与片段；不是全站总数 |',
          '| 官网控件 | 70 | 62场景＋8叠加；210变体不都已单独测试 |',
          '| 代码库注册项 | 55 | 52个基础实现，另3项中文参数示例 |',
          '| 真人特效分支 | 19 | 单独登记，不计作19套完整剪辑系统 |', '',
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
            md.append('')
    md += ['## 附加预览', '', '3D书籍等preview只作为效果参考，不计入上面72个条目；可取得情况按官网当前页面核对。', '',
           '个人.motion与Key、原始口播、完整成片、旧工作记录、依赖及保护内核不进入本目录或Git。', '']
    for preview in previews:
        for demo in preview.get('demos',[]):
            md += ['['+preview.get('label_zh','附加效果预览')+']('+demo.get('url','')+')', '']
    (root/'templates/README.zh-CN.md').write_text('\n'.join(md), encoding='utf-8')
    (gallery/'README.md').write_text('# 可播放中文模板中心\n\n[完整中文清单](https://github.com/Isaac3113/talking-head-editor/blob/main/templates/README.zh-CN.md) · [来源说明](https://github.com/Isaac3113/talking-head-editor/blob/main/templates/PROVENANCE.zh-CN.md)\n\n本机运行 `python scripts/serve_template_gallery.py` 查看可搜索目录。`index.html` 是由机器登记表生成的浏览入口；GitHub本身不会把HTML作为网站执行。\n\n`demos/`仅收录本次明确授权的精简演示小样，不收原片、完整成片、用户账号或个人模板包。静音动画演示不代表完整声画剪辑已通过。\n', encoding='utf-8')
    return {'entries':len(entries), 'counts':dict(counts), 'local_demo_files':len(local_paths), 'strict':strict}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--strict',action='store_true')
    args=p.parse_args();print(json.dumps(build(args.root.resolve(),args.strict),ensure_ascii=False))
