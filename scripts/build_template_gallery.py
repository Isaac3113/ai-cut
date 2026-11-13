"""Build the current official inventory and preserved local layers/integrations."""
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
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from template_presentation import (LEARNER_CATEGORIES, enrich_entries,
                                   load_parameter_evidence, markdown_catalog,
                                   markdown_category_pages, official_posters)

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
        # Official inventory grows; local code/control registries retain their baseline.
        expected = data.get('source_manifest', {}).get('expected_entry_ids') if isinstance(data, dict) else None
        if baseline_layer == 'style' and expected is not None:
            if not isinstance(expected, list) or not all(isinstance(x, str) for x in expected):
                raise ValueError('Invalid official source manifest in ' + filename)
            wrong_count = set(e['id'] for e in rows) != set(expected) or len(rows) != len(expected)
        else:
            wrong_count = len(rows) != BASELINE_EXPECTED[baseline_layer]
        if wrong_count or any(e.get('layer') != baseline_layer for e in rows):
            raise ValueError('Frozen baseline counts changed in ' + filename)
        entries.extend(rows)
        if isinstance(data, dict):
            expected_previews = data.get('source_manifest', {}).get('expected_preview_ids')
            actual_previews = [e['id'] for e in data.get('previews', [])]
            if expected_previews is not None and (set(actual_previews) != set(expected_previews) or len(actual_previews) != len(expected_previews)):
                raise ValueError('Official preview inventory is incomplete in ' + filename)
            previews.extend(data.get('previews', []))
        provenance.append({'path': 'templates/' + filename,
                           'sha256': sha256(raw).hexdigest(), 'entries': len(rows)})
    counts = Counter(e['layer'] for e in entries)
    if any(counts[layer] != count for layer, count in BASELINE_EXPECTED.items() if layer != 'style'):
        raise ValueError(f'Frozen baseline counts changed: {dict(counts)}; expected {BASELINE_EXPECTED}')
    return entries, previews, provenance


def source_status(root):
    path = root / 'templates/motiongit-styles.json'
    if not path.is_file():
        return {}
    source = json.loads(path.read_text(encoding='utf-8'))
    return source.get('sync_status', {}) if isinstance(source, dict) else {}


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
        if entry['layer'] not in LAYERS and entry['layer'] != 'preview':
            raise ValueError('Unknown catalog layer: ' + str(entry['layer']))
        counts[entry['layer']] += 1
        if not entry['demos'] and strict and not (entry['layer'] in ('style', 'preview') and entry.get('no_demo_reason')):
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


def demo_matches_ratio(demo, ratio):
    """Prefer a matching preview without changing integration chronology."""
    try:
        rw, rh = (float(part) for part in ratio.split(':'))
        width, height = demo.get('width'), demo.get('height')
        if not width or not height:
            width, height = (float(part) for part in demo.get('ratio', '').split(':'))
        if min(rw, rh, width, height) <= 0:
            return False
        # Allow dimensions rounded to whole pixels, but never another layout.
        return abs((width / height) / (rw / rh) - 1) < 0.015
    except (AttributeError, TypeError, ValueError, ZeroDivisionError):
        return False


def preview_integration(entry):
    cases = entry.get('integrations', [])
    return next((c for c in cases if c['id'] == entry.get('preview_integration_id')),
                cases[0] if cases else None)


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
        # Keep the true newest case separate from the entry's matching preview.
        preferred = next((c for c in cases if demo_matches_ratio(c['demo'], row.get('ratio'))), cases[0])
        preview_cases = [preferred] + [c for c in cases if c['id'] != preferred['id']]
        case_demos = [dict(c['demo'], integration_id=c['id']) for c in preview_cases]
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
        row['preview_integration_id'] = preferred['id']
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
<meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Cut · 中文剪辑模板中心</title>
<style>
:root{font-family:"Microsoft YaHei","Noto Sans SC",system-ui,sans-serif;color:#153340;background:#f4f7f9;--cyan:#148bad}*{box-sizing:border-box}body{margin:0}header{background:#153340;color:white;padding:34px max(24px,calc((100vw - 1400px)/2));border-top:5px solid #47b4d0}h1{font-size:30px;margin:8px 0 12px}p{line-height:1.75}header p{max-width:1100px;color:#d4e4eb;font-size:14px}.topline{font-size:12px;letter-spacing:.08em;color:#77d8ed}.stats{display:flex;gap:12px;flex-wrap:wrap;margin-top:18px}.stat{border:1px solid #3c606d;padding:10px 18px;border-radius:10px}.stat strong{font-size:24px;margin-right:6px}main{max-width:1448px;padding:24px;margin:auto}.notice{border:1px solid #c4d9e2;background:#eaf5f8;padding:14px 18px;border-radius:10px;font-size:13px}.toolbar{position:sticky;top:0;background:#f4f7f9f5;backdrop-filter:blur(8px);z-index:3;padding:16px 0;display:flex;gap:9px;flex-wrap:wrap}input,select,button{font:inherit;border:1px solid #c6d6df;border-radius:8px;padding:10px 12px;background:white;color:#153340}input{flex:1;min-width:230px}button{cursor:pointer}button.active{background:#153340;color:white}.tabs{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0 0}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:20px}.card{background:white;border:1px solid #dce6eb;border-radius:13px;overflow:hidden;box-shadow:0 2px 7px #15334008}.preview{background:#0a1820;height:215px;display:flex;align-items:center;justify-content:center}.preview video{width:100%;height:100%;object-fit:contain}.body{padding:17px}.body h3{font-size:18px;margin:8px 0}.body p{font-size:13px;margin:9px 0}.eyebrow{font-size:11px;color:#507582}.chips{display:flex;gap:5px;flex-wrap:wrap}.chip{font-size:11px;background:#e8f4f8;border-radius:5px;padding:4px 7px;color:#126581}.status{background:#f0f2f4;color:#5e6870}details{font-size:12px;line-height:1.8;margin-top:12px;border-top:1px solid #edf1f4;padding-top:10px}summary{cursor:pointer;font-weight:600}ul{padding-left:18px;margin:7px 0}.links{display:flex;gap:12px;font-size:12px;margin-top:12px}a{color:#08769a;text-decoration:none}a:hover{text-decoration:underline}.result{font-size:13px;margin:15px 0;color:#567080}.empty{padding:60px;text-align:center}.routes{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:20px 0}.route{border:1px solid #d4e3ea;border-radius:10px;padding:14px;background:white;font-size:12px}.route strong{font-size:15px}.route p{margin:8px 0}.foot{font-size:12px;color:#66808b;margin:30px 0}dialog{border:0;border-radius:12px;max-width:95vw;padding:15px}dialog::backdrop{background:#000a}dialog video{max-width:90vw;max-height:80vh}.small{font-size:11px;color:#6a828e}.preview-only{margin:20px 0;padding:15px;border:1px dashed #a6bfc9;border-radius:10px}@media(max-width:600px){h1{font-size:24px}main{padding:15px}.toolbar{position:static}.grid{grid-template-columns:1fr}}
.views{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:18px}.views p{margin:0 0 0 8px}.version-label{display:block;font-size:12px;color:#507582;margin:12px 0 8px}.demo-version{display:block;width:100%;margin-top:5px;font-size:12px;min-width:0}.preview.portrait{height:350px}.playback-note{padding:8px 10px;background:#eef7f8;border-radius:7px;font-size:12px!important;color:#235d68}.demo-meta:empty{display:none}.card select:focus-visible,.views button:focus-visible{outline:3px solid #47b4d0;outline-offset:2px}
.entrylinks{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}.entrylinks a{border:1px solid #76bdce;border-radius:8px;color:white;padding:10px 15px}.entrylinks a:first-child{background:#eaf5f8;color:#153340}.guide-section pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f6f8;padding:12px;font-size:12px;line-height:1.65}.guide-section summary{font-size:13px}.preview-label{padding:10px 17px;margin:0;font-size:13px;background:#eaf5f8}.section-note{font-size:12px;color:#55717c}.guide-section a{overflow-wrap:anywhere}.learner-status{font-weight:600;color:#126581}.source-tabs-label{margin:18px 0 0;font-size:12px;color:#55717c}.grid{grid-template-columns:repeat(auto-fill,minmax(390px,1fr))}@media(max-width:600px){.grid{grid-template-columns:1fr}}
</style>
<header><div class="topline">AGI TOP / AI CUT / 中文效果目录</div><h1>先看效果，再选择适合内容的模板</h1>
<p>整套风格、动画控件、代码模板与真人特效分别登记。中文名称、使用条件、来源和 Demo 放在同一个入口；有演示不等于已通过新片验收。</p>
<nav class="entrylinks" aria-label="两个使用入口"><a href="https://github.com/Isaac3113/ai-cut/blob/main/docs/NOTION_GUIDE.zh-CN.md">① 学习自动剪辑</a><a href="#template-library">② 选择与使用模板</a></nav>
<div class="stats">__STATS__</div></header>
<main><div class="notice">本次 B 版获认可的是局部重点文字效果。模板按实际内容选择，不强套整片。官网 Demo 需要联网；本地控件 Demo 为静音版式演示，示例数值与模拟界面不代表真实业务成果。个人 .motion、Key 和完整原片不在本目录。</div>
<div class="routes"><div class="route"><strong>知识口播</strong><p>讲述与原意驱动画面。优先字幕、概念解释、重点句与关系图。</p></div><div class="route"><strong>系统实操</strong><p>真实按钮与操作证据优先。放大、标注须指向实际目标。</p></div><div class="route"><strong>长访谈切片</strong><p>先按独立主题剪成完整论点，再添加包装与字幕。</p></div><div class="route"><strong>旅行 / Vlog</strong><p>按地点、事件、镜头连续性、环境声与音乐节奏剪辑；当前仅定义路线边界，未实现专用自动流程。</p></div></div>
<div class="views" role="group" aria-label="浏览入口"><button id="allTemplates" type="button">全部模板</button><button id="ownerDemos" type="button">本人Demo（已登记案例）</button><p class="small" id="localPlayback">本人库样例为静音版；已关联的本机原声版可在同一张卡直接播放。</p></div>
<h2 id="template-library">按内容选择特效模板</h2><p class="section-note">每条固定七项：预览、用途、素材、可改参数、给 AI 的指令、使用状态、来源许可。先选你想表达的内容，再查看来源层级和细类。</p><p class="source-tabs-label">来源层级（保留技术归属，数量不能合称整片模板）</p><div class="tabs" id="tabs"></div><div class="toolbar"><input id="search" aria-label="搜索模板" placeholder="搜索中文名称、用途、控件ID…"><select id="category" aria-label="用途分类"><option value="">全部用途分类</option></select><select id="sourceCategory" aria-label="原始细类"><option value="">全部原始细类</option></select><select id="executionStatus" aria-label="调用状态"><option value="">全部调用状态</option></select><select id="demoType" aria-label="Demo来源"><option value="">全部Demo来源</option><option value="own">本人Demo（已登记案例）</option><option value="official">官网示例</option><option value="other">其他本地演示</option></select><select id="ratio" aria-label="视频比例"><option value="">全部比例</option></select><button id="reset">重置</button></div>
<p class="notice" id="syncStatus"></p><div class="result" id="result"></div><div class="grid" id="grid"></div><p><button id="loadMore" type="button">再看24项</button></p><div id="extra"></div>
<p class="foot">来源、许可证与更新口径：<a href="https://github.com/Isaac3113/ai-cut/blob/main/templates/PROVENANCE.zh-CN.md">来源说明</a> · <a href="https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md">完整中文清单</a> · <a href="https://github.com/Isaac3113/ai-cut/blob/main/docs/template-gallery/CATEGORIES.md">分类动画预览</a> · <a href="https://github.com/Isaac3113/ai-cut/blob/main/skill/ai-cut/references/template-selection.md">Skill选择规则</a><br>2026-10-27历史归档授权：以后每片经QA精选的本人静音Demo与集成说明可进入私人Git；完整原片、完整成片、源人像蒙版、Key、个人包与客户敏感信息不进入Git。2026-11-02现行展示授权：本页精选的现有预览可在 aicut.agi-top.com 公开展示，供个人学习与免费交流，不用于业务获客或销售。同日后续用户授权将GitHub源码仓库公开，上方源码与教学链接可直接浏览、下载，无需申请仓库权限。官网候选预览保留原来源与许可，不代表附送官方原包或全部模板已可执行。其他电脑仍需独立准备运行环境、个人模板授权和新片素材。</p></main>
<script>const DATA=__DATA__;const LAYERS=__LAYERS__;
const ALL_ENTRIES=[...DATA.entries,...DATA.previews];
// BEGIN_DEMO_MODEL — shared by the browser and focused interaction tests.
function demoKey(d){return d.path||d.url||''}
function demoCase(e,d){return d.integration_id?(e.integrations||[]).find(c=>c.id===d.integration_id)||null:null}
function demoSource(e,d){const c=demoCase(e,d);if(d.kind==='own'&&d.path&&(d.subject==='owner'||c?.qa?.state==='verified_demo'))return 'own';return d.kind==='official'?'official':'other'}
function demoRatio(e,d){
  const value=d.ratio||((d.width&&d.height)?d.width+':'+d.height:e.ratio)||'';
  const parts=String(value).split(':').map(Number);if(parts.length!==2||!parts.every(x=>Number.isFinite(x)&&x>0))return 'unknown';
  let [w,h]=parts;if(Number.isInteger(w)&&Number.isInteger(h)){const gcd=(a,b)=>b?gcd(b,a%b):a;const g=gcd(w,h);w/=g;h/=g}return w+':'+h;
}
function candidateDemos(e,source='',ratio=''){return (e.demos||[]).filter(d=>demoKey(d)&&(!source||demoSource(e,d)===source)&&(!ratio||demoRatio(e,d)===ratio))}
function selectedDemo(e,source,ratio,preferredKey){const choices=candidateDemos(e,source,ratio);return choices.find(d=>demoKey(d)===preferredKey)||choices[0]||null}
function localOverrides(manifest,entries){
  const result=Object.create(null);if(manifest?.schema!=='talking-head-local-demos/1'||!manifest.clips||typeof manifest.clips!=='object'||Array.isArray(manifest.clips))return result;
  const known=new Set(entries.flatMap(e=>(e.demos||[]).filter(d=>d.path&&d.kind==='own'&&demoCase(e,d)?.qa?.state==='verified_demo').map(d=>d.path)));
  for(const [key,value] of Object.entries(manifest.clips)){if(!known.has(key)||!value||typeof value.audio!=='boolean'||typeof value.url!=='string'||!/^local-owner-media\/[A-Za-z0-9_-]+\.mp4$/.test(value.url))continue;result[key]={url:value.url,audio:value.audio}}return result;
}
function demoPlayback(e,d,overrides){
  const local=d.path&&overrides[d.path];if(local)return {src:local.url,audio:local.audio,label:local.audio?'原声版 · 仅本机':'静音画面版 · 仅本机'};
  return {src:demoKey(d),audio:false,label:demoSource(e,d)==='official'?'官网示例 · 联网播放':'静音库样例 · 随仓库同步'};
}
function demoLabel(e,d){const source={own:'本人',official:'官网示例',other:'本地效果'}[demoSource(e,d)],ratio=demoRatio(e,d),c=demoCase(e,d);return source+' · '+(ratio==='unknown'?'比例未标注':ratio)+(c?' · '+c.source.version:(d.variant_id?' · '+d.variant_id:''))}
// END_DEMO_MODEL
const stateName=x=>({'integrated_case_verified':'仅本片接入已检查','registered':'已登记，演示生成中','registered_pending_render':'演示生成中','validated_demo':'本机演示已检查','verified':'本机演示已检查','rendered_verified':'本机演示已检查'}[x]||x);
const availabilityName=x=>({'local_rendered_demo':'已有本地演示','available':'可按条件使用','registered_pending_render':'本地演示生成中'}[x]||x);
const $=x=>document.getElementById(x),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let layer='',overrides=Object.create(null);const selectedKeys=new Map();
function safe(x){return typeof x==='string'&&(x.startsWith('https://')||x.startsWith('demos/')||/^local-owner-media\/[A-Za-z0-9_-]+\.mp4$/.test(x))?esc(x):''}
function bullet(items){return '<ul>'+(items||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'}
function integrationInfo(e,d){const c=demoCase(e,d);if(!c)return '';const s=c.source,i=c.invocation;return '<details><summary>本片接入与复用边界</summary><p>Git库样例登记说明：'+esc(d.description_zh||'见本次记录')+'</p><p>'+esc(c.project_id+' · '+s.package_id+' · '+s.version)+'</p><p>输入：'+esc(i.inputs_zh.join('；'))+'</p><p>调用：<code>'+esc(i.command)+'</code></p><p>本片检查：'+esc(c.qa.scope)+'</p><p>仅此版本与Demo；原条目和全部变体验证状态不因此改变。</p></details>'}
function demoMetadata(e,d){const p=demoPlayback(e,d,overrides),c=demoCase(e,d),source=demoSource(e,d);return '<p class="playback-note">'+esc(p.label)+'</p>'+(c?'<p class="small">当前本人Demo版本：'+esc(c.source.version)+' · 已解码与抽帧检查'+(c.qa.owner_artistic_acceptance?'':' · 风格待确认')+'</p>':'<p class="small">'+esc(d.description_zh||'')+'</p><p class="small">'+esc(source==='official'?'官网原始示例；不代表本人输入已经验证。':source==='own'?'历史本人素材样例；沿用原登记的检查范围。':'本地效果示例；不据此认定画面人物或业务成果。')+'</p>')+integrationInfo(e,d)}
function demoStatus(e,d){return {own:'本人案例 · 见本次检查范围',official:'官网示例',other:'本地效果演示'}[demoSource(e,d)]}
function cardTitle(e){return e.layer==='style'&&e.family_label_zh?e.family_label_zh:e.label_zh}
function renderTabs(){const tabs=[['','全部'],...Object.entries(LAYERS),['preview','官方预告／待开放']];$('tabs').innerHTML=tabs.map(([id,label])=>'<button data-layer="'+id+'" class="'+(layer===id?'active':'')+'">'+label+'</button>').join('');$('tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>{layer=b.dataset.layer;shownLimit=24;renderTabs();render()})}
function learnerSection(s){
  if(s.id==='preview')return '';
  let content=s.id==='instructions'?'<pre>'+esc((s.text||[]).join('\n'))+'</pre>':bullet(s.text||[]);
  if(s.notes?.length){content+=s.id==='status'?'<details><summary>原始检查范围</summary>'+bullet(s.notes)+'</details>':bullet(s.notes)}
  if(s.evidence?.length)content+='<p>参数依据：'+s.evidence.map(p=>'<a target="_blank" rel="noopener" href="https://github.com/Isaac3113/ai-cut/blob/main/'+esc(p)+'">'+esc(p.split('/').pop())+'</a>').join(' · ')+'</p>';
  if(s.id==='source')content+='<p>'+(s.url?'<a target="_blank" rel="noopener" href="'+safe(s.url)+'">原始来源</a>':'')+(s.repository_url?' · <a target="_blank" rel="noopener" href="'+safe(s.repository_url)+'">上游技术资料</a>':'')+'</p>';
  return '<details class="guide-section"'+(['use','status'].includes(s.id)?' open':'')+'><summary>'+esc(s.title)+'</summary>'+content+'</details>'
}
function cardHtml(e,choices,d){
  const guide=e.learner_guide||{category_zh:e.category_zh,status:'使用条件待核对',sections:[]};
  const p=d?demoPlayback(e,d,overrides):null,portrait=d&&demoRatio(e,d)==='9:16',poster=d&&(d.poster_path||(demoSource(e,d)==='official'?e.learner_poster:''));
  const preview=d?'<div class="preview'+(portrait?' portrait':'')+'"><video controls '+(p.audio?'':'muted ')+'playsinline preload="none" '+(poster?'poster="'+safe(poster)+'"':'')+' src="'+safe(p.src)+'" aria-label="'+esc(e.label_zh)+' Demo"></video></div>':'<div class="preview"><p style="color:white">暂无可播放演示；见本条来源状态</p></div>';
  const selector=d?'<label class="version-label">演示版本<select class="demo-version" aria-label="'+esc(e.label_zh)+' 演示版本">'+choices.map(x=>'<option value="'+esc(demoKey(x))+'"'+(demoKey(x)===demoKey(d)?' selected':'')+'>'+esc(demoLabel(e,x))+'</option>').join('')+'</select></label><div class="demo-meta">'+demoMetadata(e,d)+'</div><a class="open-demo" href="'+safe(p.src)+'" target="_blank" rel="noopener">打开当前 Demo</a>':'';
  return '<article class="card" data-entry-id="'+esc(e.id)+'"><div class="body"><div class="eyebrow">'+esc(LAYERS[e.layer]||'官方预告')+' · '+esc(e.id)+'</div><h3>'+esc(cardTitle(e))+'</h3><div class="chips"><span class="chip">'+esc(guide.category_zh)+'</span><span class="chip">'+esc(e.category_zh)+'</span>'+(d?'<span class="chip demo-ratio">'+esc(demoRatio(e,d)==='unknown'?'比例未标注':demoRatio(e,d))+'</span><span class="chip status demo-status">'+esc(demoStatus(e,d))+'</span>':'')+'</div><p>'+esc(e.description_zh)+'</p><p class="learner-status">'+esc(guide.status)+'</p></div><h4 class="preview-label">1. 效果预览</h4>'+preview+'<div class="body">'+selector+(guide.sections||[]).map(learnerSection).join('')+'</div></article>';
}
function stopOtherVideos(current){document.querySelectorAll('video').forEach(v=>{if(v!==current)v.pause()})}
function activateDemo(card,e,d,pauseOthers=true){
  const v=card.querySelector('video'),p=demoPlayback(e,d,overrides),ratio=demoRatio(e,d);if(pauseOthers)stopOtherVideos(null);v.pause();v.src=p.src;v.muted=!p.audio;v.poster=d.poster_path||(demoSource(e,d)==='official'?e.learner_poster:'')||'';v.load();card.querySelector('.preview').classList.toggle('portrait',ratio==='9:16');card.querySelector('.demo-meta').innerHTML=demoMetadata(e,d);card.querySelector('.demo-status').textContent=demoStatus(e,d);card.querySelector('.demo-ratio').textContent=ratio==='unknown'?'比例未标注':ratio;card.querySelector('.open-demo').href=p.src;selectedKeys.set(e.id,demoKey(d));
}
function syncOwnerHash(){try{history.replaceState(null,'',$('demoType').value==='own'?'#owner-demos':location.href.split('#')[0])}catch(_){}}
function updateViewButtons(){const own=$('demoType').value==='own';for(const [id,active] of [['ownerDemos',own],['allTemplates',!own]]){$(id).classList.toggle('active',active);$(id).setAttribute('aria-pressed',String(active))}}
let shownLimit=24;
function render(){
  stopOtherVideos(null);const q=$('search').value.trim().toLowerCase(),cat=$('category').value,sourceCat=$('sourceCategory').value,source=$('demoType').value,ratio=$('ratio').value,execution=$('executionStatus').value;
  const rows=ALL_ENTRIES.filter(e=>(!execution||e.learner_guide?.execution_status===execution)&&(!layer||e.layer===layer)&&(!cat||e.learner_guide?.category===cat)&&(!sourceCat||e.category_zh===sourceCat)&&(!q||JSON.stringify(e).toLowerCase().includes(q))).map(e=>({e,choices:candidateDemos(e,source,ratio)})).filter(x=>x.choices.length||(!source&&!(x.e.demos||[]).length&&(!ratio||demoRatio(x.e,{})===ratio)));
  $('result').textContent='显示 '+rows.length+' / '+ALL_ENTRIES.length+' 个目录条目（含预告） · '+rows.reduce((n,x)=>n+x.choices.length,0)+' 个匹配演示版本；同一条目可在卡内切换来源和比例。';
  $('loadMore').hidden=rows.length<=shownLimit;$('loadMore').textContent='再看24项（还有 '+Math.max(0,rows.length-shownLimit)+' 项）';
  $('grid').innerHTML=rows.slice(0,shownLimit).map(({e,choices})=>{const d=selectedDemo(e,source,ratio,selectedKeys.get(e.id));if(d)selectedKeys.set(e.id,demoKey(d));return cardHtml(e,choices,d)}).join('')||'<div class="empty">没有匹配的演示。试试其他来源、比例或分类。</div>';
  $('grid').querySelectorAll('.card[data-entry-id]').forEach(card=>{const e=ALL_ENTRIES.find(x=>x.id===card.dataset.entryId),select=card.querySelector('.demo-version');if(!select||!card.querySelector('video'))return;card.querySelector('video').addEventListener('play',event=>stopOtherVideos(event.currentTarget));select.addEventListener('change',()=>{const d=candidateDemos(e,$('demoType').value,$('ratio').value).find(x=>demoKey(x)===select.value);if(d)activateDemo(card,e,d)})});updateViewButtons();
}
function chooseView(own){shownLimit=24;layer='';$('search').value='';$('category').value='';$('sourceCategory').value='';$('executionStatus').value='';$('ratio').value='';$('demoType').value=own?'own':'';syncOwnerHash();renderTabs();render()}
Object.entries(DATA.learner_categories||{}).forEach(([key,label])=>{const o=document.createElement('option');o.value=key;o.textContent=label;$('category').append(o)});
const categories=[...new Set(ALL_ENTRIES.map(e=>e.category_zh))].sort((a,b)=>a.localeCompare(b,'zh'));categories.forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;$('sourceCategory').append(o)});
const ratios=[...new Set(ALL_ENTRIES.flatMap(e=>(e.demos||[]).map(d=>demoRatio(e,d))))].sort((a,b)=>{const order=['9:16','16:9','1:1','4:3','3:4'];return (order.indexOf(a)<0?99:order.indexOf(a))-(order.indexOf(b)<0?99:order.indexOf(b))||a.localeCompare(b)});ratios.forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r==='unknown'?'比例未标注':r;$('ratio').append(o)});
['search','category','sourceCategory','executionStatus','demoType','ratio'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>{shownLimit=24;if(id==='demoType')syncOwnerHash();render()}));$('reset').onclick=()=>chooseView(false);$('allTemplates').onclick=()=>chooseView(false);$('ownerDemos').onclick=()=>chooseView(true);
window.addEventListener('hashchange',()=>{if(location.hash==='#owner-demos')chooseView(true)});if(location.hash==='#owner-demos')$('demoType').value='own';
const executionOptions=new Map(ALL_ENTRIES.map(e=>[e.learner_guide?.execution_status,e.learner_guide?.execution_status_zh]).filter(([k,v])=>k&&v));executionOptions.forEach((label,key)=>{const o=document.createElement('option');o.value=key;o.textContent=label;$('executionStatus').append(o)});
const sync=DATA.sync_status||{};$('syncStatus').textContent='目录同步：'+(sync.checked_at||DATA.updated_on)+'。目录登记、原包取得、运行接入分别标记；旧案例保留其真实版本。'+(sync.scope_zh||'成功来源与覆盖边界见 GitHub 的本轮同步说明。')+((sync.gaps||[]).length?' 仍有 '+sync.gaps.length+' 项来源缺口，详见同步记录。':'');

$('loadMore').onclick=()=>{shownLimit+=24;render()};
renderTabs();render();
if(location.protocol!=='file:'){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),1800);
  fetch('local-demo-manifest.json',{cache:'no-store',credentials:'same-origin',signal:controller.signal}).then(response=>response.ok?response.json():null).then(manifest=>{
    overrides=localOverrides(manifest,DATA.entries);const count=Object.keys(overrides).length;if(!count)return;$('localPlayback').textContent='已关联 '+count+' 个本机版本；原声与静音状态显示在对应卡片里。';
    $('grid').querySelectorAll('.card[data-entry-id]').forEach(card=>{const v=card.querySelector('video');if(!v||!v.paused||v.currentTime>0)return;const e=ALL_ENTRIES.find(x=>x.id===card.dataset.entryId),d=selectedDemo(e,$('demoType').value,$('ratio').value,selectedKeys.get(e.id));if(d&&overrides[d.path])activateDemo(card,e,d,false)})
  }).catch(()=>{}).finally(()=>clearTimeout(timer));
}
</script></html>'''


def build(root: Path, strict=False):
    gallery = root / 'docs/template-gallery'
    gallery.mkdir(parents=True, exist_ok=True)
    entries, previews, provenance = read_sources(root)
    entries, integrations, integration_source = apply_integrations(root, entries, strict)
    entries.sort(key=lambda e: (0 if e['id']=='mg-style-314486' else 1 if e['layer']=='style' and e['category_zh']=='口播与讲解' else 2 if e['layer']=='style' else 3))
    counts, local_paths = validate(entries, gallery, strict)
    _, preview_paths = validate(previews, gallery, strict)
    if len({e['id'] for e in entries + previews}) != len(entries) + len(previews):
        raise ValueError('Duplicate ID across templates and previews')
    local_paths.update(preview_paths)
    parameter_evidence = load_parameter_evidence(root)
    enrich_entries(entries, parameter_evidence)
    enrich_entries(previews, parameter_evidence)
    posters = official_posters(root)
    for entry in entries + previews:
        if entry['id'] in posters:
            entry['learner_poster'] = posters[entry['id']]
    data = {'schema': 'talking-head-template-center/1', 'updated_on': datetime.now().astimezone().date().isoformat(),
            'counts_by_layer': dict(counts), 'build_mode':'complete' if strict else 'draft', 'counts_are_not_additive_templates': True,
            'sources': provenance, 'baseline_counts_by_layer': BASELINE_EXPECTED,
            'sync_status': source_status(root),
            'integration_source': integration_source, 'integrations': integrations,
            'learner_categories': LEARNER_CATEGORIES,
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
    (root/'templates/README.zh-CN.md').write_text(markdown_catalog(entries, previews, counts, integrations, posters, data['sync_status']), encoding='utf-8')
    category_root = root / 'templates/categories'
    category_root.mkdir(exist_ok=True)
    for category, content in markdown_category_pages(entries, previews, posters).items():
        (category_root / (category + '.md')).write_text(content, encoding='utf-8')
    (gallery/'README.md').write_text('# AI Cut · 可播放中文模板中心\n\n[完整中文清单](https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md) · [来源说明](https://github.com/Isaac3113/ai-cut/blob/main/templates/PROVENANCE.zh-CN.md)\n\n本机运行 `python scripts/serve_template_gallery.py` 查看可搜索目录。`index.html` 是由机器登记表生成的浏览入口；GitHub本身不会把HTML作为网站执行。\n\n2026-10-27历史归档授权：`demos/`可收以后每片经QA精选的本人静音Demo与集成说明，限私人Git。完整原片、完整成片、源人像蒙版、Key、个人包和客户敏感信息不进入Git；当时的归档授权不涵盖公开展示。\n\n2026-11-02现行展示授权：本页精选的现有预览可在 `https://aicut.agi-top.com` 公开展示，供个人学习与免费交流，不用于业务获客或销售。同日后续用户授权将GitHub源码仓库公开，源码和教学可直接浏览、下载，无需申请仓库权限。官网候选预览保留原来源与许可，不代表附送官方原包或全部模板已可执行；现有来源、rights与QA记录不因公开展示而改写。静音动画演示不代表完整声画剪辑已通过。\n', encoding='utf-8')
    return {'entries':len(entries), 'counts':dict(counts), 'local_demo_files':len(local_paths), 'integration_records':len(integrations), 'strict':strict}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--strict',action='store_true')
    args=p.parse_args();print(json.dumps(build(args.root.resolve(),args.strict),ensure_ascii=False))
