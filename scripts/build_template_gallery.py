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
LAYERS = {'authored': 'AI Cut通用自制模板', 'style': '官网模板与片段', 'control': '官网动画控件',
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
    # Add independently authored templates without rewriting any frozen upstream registry.
    authored_path = root / 'templates/authored-templates.json'
    if authored_path.is_file():
        raw = authored_path.read_bytes()
        authored = json.loads(raw)
        if authored.get('schema_version') != 1 or not isinstance(authored.get('entries'), list):
            raise ValueError('Invalid authored template registry')
        if any(entry.get('layer') != 'authored' for entry in authored['entries']):
            raise ValueError('Authored registry must not relabel upstream templates')
        entries.extend(authored['entries'])
        provenance.append({'path': 'templates/authored-templates.json',
                           'sha256': sha256(raw).hexdigest(), 'entries': len(authored['entries'])})
    return entries, previews, provenance


def source_status(root):
    path = root / 'templates/motiongit-styles.json'
    if not path.is_file():
        return {}
    source = json.loads(path.read_text(encoding='utf-8'))
    return source.get('sync_status', {}) if isinstance(source, dict) else {}


def verify_authored_packages(root, entries):
    """Keep a published author archive bound to its reviewed bytes, never a private package."""
    for entry in entries:
        package = entry.get('author_package') if entry.get('layer') == 'authored' else None
        if not package:
            continue
        path = (root / str(package.get('path', ''))).resolve()
        if not path.is_relative_to((root / 'templates/authored-packages').resolve()) or path.suffix != '.motion':
            raise ValueError(entry['id'] + ': author package outside approved directory')
        if not path.is_file() or path.stat().st_size != package.get('bytes') or sha256(path.read_bytes()).hexdigest() != package.get('sha256'):
            raise ValueError(entry['id'] + ': author package differs from reviewed bytes')


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


def is_owner_demo(demo):
    """A demo rendered from the owner's own footage, photos or brand ('own' material)."""
    return demo.get('kind') == 'own'


def gallery_view(root, data):
    """Public page may hide owner-made content; catalog.json keeps the full registry."""
    path = root / 'templates/gallery-hidden.json'
    if not path.is_file():
        return data
    rules = json.loads(path.read_text(encoding='utf-8'))
    hide_layers = rules.get('hide_layers', [])
    if rules.get('schema_version') != 1 or not isinstance(hide_layers, list) or set(hide_layers) - set(LAYERS):
        raise ValueError('Invalid gallery hide rules in templates/gallery-hidden.json')
    hide_owner = rules.get('hide_owner_demos') is True
    entries = []
    for entry in data['entries']:
        if entry['layer'] in hide_layers:
            continue
        if hide_owner:
            kept = [d for d in entry['demos'] if not is_owner_demo(d)]
            if entry['demos'] and not kept:
                continue  # nothing public left to preview
            if len(kept) != len(entry['demos']) or entry.get('integrations'):
                entry = {k: v for k, v in entry.items() if k not in ('integrations', 'latest_integration_id', 'preview_integration_id')}
                entry['demos'] = kept
        entries.append(entry)
    visible = {e['id'] for e in entries}
    integrations = [] if hide_owner else [r for r in data['integrations'] if r.get('entry_id') in visible]
    return dict(data, entries=entries, integrations=integrations,
                counts_by_layer=dict(Counter(e['layer'] for e in entries)))


def demo_href(demo, markdown=False):
    if demo.get('path'):
        return ('../docs/template-gallery/' if markdown else '') + demo['path']
    return demo.get('url', '')


HTML = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Cut · 视频特效模板库</title>
<meta name="description" content="开源的中文视频特效模板目录：口播、录屏教学、流程、数据、产品展示等用途的动画效果，先看效果，再看素材要求和使用状态。">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&family=Schibsted+Grotesk:wght@500;700&display=swap">
<style>
:root{--ground:#f1f2ef;--paper:#fff;--ink:#121314;--ink-2:#4a4c50;--ink-3:#66686d;--line:#d9dad5;--line-2:#e6e7e2;--frame:#131417;--accent:#2a44d4;--accent-soft:#e3e7fb;--ready:#1d7a4c;--prep:#a35f00;--view:#8a8c91;--sans:"Schibsted Grotesk","Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;--ease:cubic-bezier(.16,1,.3,1);color-scheme:light}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scrollbar-color:#b9bbb5 transparent}
body{margin:0;background:var(--ground);color:var(--ink);font:400 15px/1.6 var(--sans);font-feature-settings:"tnum" 0}
::selection{background:var(--accent);color:#fff}
a{color:var(--accent);text-underline-offset:3px;text-decoration-thickness:1px}
button,input,select{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
svg.i{width:18px;height:18px;flex:none;stroke:currentColor;fill:none;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}
.skip{position:absolute;left:-999px;top:8px;background:var(--ink);color:#fff;padding:8px 12px;border-radius:6px;z-index:50}.skip:focus{left:12px}
.bar{display:flex;align-items:center;justify-content:space-between;gap:16px;height:60px;padding:0 max(20px,calc((100vw - 1480px)/2 + 32px));border-bottom:1px solid var(--line)}
.mark{display:flex;align-items:baseline;gap:8px;color:var(--ink);text-decoration:none}.mark b{font-weight:700;font-size:19px;letter-spacing:-.01em}.mark span{color:var(--ink-2);font-size:15px}
.bar nav{display:flex;gap:22px;font-size:14px}.bar nav a{color:var(--ink-2);text-decoration:none}.bar nav a:hover{color:var(--ink);text-decoration:underline}
.intro{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px 64px;align-items:end;max-width:1480px;margin:0 auto;padding:52px 32px 36px}
.intro h1{margin:0;font-weight:900;font-size:clamp(30px,3.4vw,46px);line-height:1.12;letter-spacing:-.02em;text-wrap:balance}
.intro p{margin:0;max-width:36em;color:var(--ink-2);font-size:16px;line-height:1.75}.intro p a{white-space:nowrap}
.shell{display:grid;grid-template-columns:236px minmax(0,1fr);gap:44px;max-width:1480px;margin:0 auto;padding:0 32px}
.filters{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;padding:14px 4px 40px 0;scrollbar-width:thin}
.sheet-head{display:none}
.facet{margin:0 0 26px}.facet h2{margin:0 0 8px;font-size:13px;font-weight:700;color:var(--ink)}
.opts{display:flex;flex-direction:column;gap:1px}
.opt{display:flex;align-items:center;gap:9px;width:100%;padding:6px 9px;border:0;border-radius:6px;background:none;text-align:left;font-size:14px;line-height:1.4;cursor:pointer;color:var(--ink)}
.opt:hover{background:var(--line-2)}.opt .n{margin-left:auto;font-size:12.5px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.opt[aria-pressed=true]{background:var(--ink);color:#fff}.opt[aria-pressed=true] .n{color:#c9cacd}
.opt.zero{color:var(--ink-3)}.opt.zero:not([aria-pressed=true]){cursor:default}
.dot{width:7px;height:7px;border-radius:50%;flex:none;background:var(--view)}.dot.ready{background:var(--ready)}.dot.prep{background:var(--prep)}
.more{border-top:1px solid var(--line);padding-top:14px}.more summary{cursor:pointer;font-size:13px;font-weight:700;list-style:none;display:flex;align-items:center;gap:6px}.more summary::-webkit-details-marker{display:none}.more[open] summary svg{transform:rotate(90deg)}.more summary svg{width:14px;height:14px;transition:transform .2s var(--ease)}
.more label{display:block;margin:14px 0 0;font-size:12.5px;color:var(--ink-2)}.more select{display:block;width:100%;margin-top:5px;padding:8px 10px;border:1px solid var(--line);border-radius:7px;background:var(--paper);font-size:13.5px}
.clear{margin-top:18px;border:0;background:none;padding:0;color:var(--accent);font-size:13.5px;cursor:pointer;text-decoration:underline;text-underline-offset:3px}
.tools{position:sticky;top:0;z-index:5;display:flex;gap:10px;padding:14px 0 12px;background:var(--ground)}
.search{position:relative;flex:1}.search svg{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--ink-3)}
.search input{width:100%;height:48px;padding:0 16px 0 42px;border:1px solid var(--line);border-radius:10px;background:var(--paper);font-size:15px}.search input::placeholder{color:var(--ink-3)}.search input:focus{outline:2px solid var(--accent);outline-offset:-1px;border-color:transparent}
.filter-btn{display:none;align-items:center;gap:7px;height:48px;padding:0 15px;border:1px solid var(--line);border-radius:10px;background:var(--paper);cursor:pointer;font-size:14.5px}.filter-btn b{min-width:20px;height:20px;border-radius:10px;background:var(--ink);color:#fff;font-size:12px;line-height:20px;text-align:center;padding:0 5px}.filter-btn b:empty{display:none}
.rail{display:none}
.status-line{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;min-height:32px;margin:4px 0 18px;font-size:14px;color:var(--ink-2)}.status-line strong{color:var(--ink);font-variant-numeric:tabular-nums}
.chip{display:inline-flex;align-items:center;gap:4px;height:28px;padding:0 6px 0 10px;border:1px solid var(--line);border-radius:14px;background:var(--paper);font-size:13px;cursor:pointer;color:var(--ink)}.chip svg{width:14px;height:14px;color:var(--ink-3)}.chip:hover{border-color:var(--ink-3)}
.hint{flex-basis:100%;margin:0;font-size:13px;color:var(--ink-3)}.hint a{color:var(--ink-2)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(228px,1fr));gap:30px 20px}
.tile{display:flex;flex-direction:column;gap:11px;color:var(--ink);text-decoration:none;min-width:0}
.frame{position:relative;display:block;aspect-ratio:4/3;background:var(--frame);border-radius:8px;overflow:hidden;transition:box-shadow .25s var(--ease)}
.grid.tall .frame{aspect-ratio:9/16}.grid.square .frame{aspect-ratio:1}.grid.wide .frame{aspect-ratio:16/9}
.frame video,.frame img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:block}
.frame .rt{position:absolute;left:8px;bottom:8px;padding:1px 6px;border-radius:4px;background:rgba(10,11,12,.62);color:#e9eaec;font-size:11px;font-weight:500;letter-spacing:.02em;font-variant-numeric:tabular-nums}
.frame .play{position:absolute;right:8px;bottom:8px;width:26px;height:26px;border-radius:50%;background:rgba(10,11,12,.62);color:#fff;display:grid;place-items:center;opacity:0;transition:opacity .2s}.frame .play svg{width:12px;height:12px;fill:currentColor;stroke:none}
.tile:hover .frame,.tile:focus-visible .frame{box-shadow:0 0 0 2px var(--ground),0 0 0 4px var(--accent)}.tile:focus-visible{outline:0}
.tile.playing .play{opacity:1}
.noplay{position:absolute;inset:0;display:grid;place-items:center;color:#9a9ca1;font-size:13px}
.cap{display:flex;flex-direction:column;gap:5px;min-width:0}
.cap .t{font-size:15px;font-weight:500;line-height:1.42;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.cap .m{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--ink-2);min-width:0}.cap .m .u{color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.cap .m .lv{display:inline-flex;align-items:center;gap:6px;white-space:nowrap}
.empty{grid-column:1/-1;padding:72px 0;text-align:center;color:var(--ink-2)}.empty p{margin:0 0 14px}
.more-row{display:flex;justify-content:center;padding:44px 0 72px}
.load{height:46px;padding:0 26px;border:1px solid var(--ink);border-radius:23px;background:none;cursor:pointer;font-size:14.5px}.load:hover{background:var(--ink);color:#fff}.load span{color:var(--ink-3);margin-left:6px}.load:hover span{color:#c9cacd}
.about{border-top:1px solid var(--line);background:#e9eae6}
.about-in{max-width:1480px;margin:0 auto;padding:48px 32px 64px;display:grid;grid-template-columns:236px minmax(0,1fr);gap:44px}
.about h2{margin:0;font-size:22px;font-weight:900;letter-spacing:-.01em}
.about-body{max-width:76ch;font-size:14px;line-height:1.85;color:var(--ink-2)}.about-body h3{margin:28px 0 6px;font-size:15px;color:var(--ink)}.about-body h3:first-child{margin-top:0}.about-body p{margin:0 0 10px}
.stats{display:flex;flex-wrap:wrap;gap:8px 28px;margin:8px 0 4px}.stat{font-size:13.5px}.stat strong{display:block;font-size:24px;font-weight:700;color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.routes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 28px}.route p{margin:2px 0 0}.route strong{color:var(--ink)}
.foot{font-size:12.5px;color:var(--ink-3)}
.dev-notice{max-width:1480px;margin:16px auto 0;padding:0 32px;color:var(--prep);font-size:14px}
dialog.detail{position:fixed;inset:0 0 0 auto;width:min(760px,100vw);height:100%;max-width:none;max-height:none;margin:0;padding:0;border:0;background:var(--paper);color:var(--ink);overflow:auto;overscroll-behavior:contain}
dialog.detail[open]{animation:slide .42s var(--ease)}dialog.detail::backdrop{background:rgba(18,19,20,.52)}
@keyframes slide{from{transform:translateX(48px);opacity:.4}to{transform:none;opacity:1}}
#d-title:focus{outline:0}.d-top{position:sticky;top:0;z-index:2;display:flex;justify-content:flex-end;padding:10px;pointer-events:none}
.d-close{pointer-events:auto;display:grid;place-items:center;width:40px;height:40px;border:0;border-radius:50%;background:rgba(18,19,20,.72);color:#fff;cursor:pointer}.d-close:hover{background:var(--ink)}
.d-media{margin-top:-60px;background:var(--frame);display:flex;justify-content:center}.d-media video{display:block;width:100%;max-height:62vh;aspect-ratio:16/9;object-fit:contain;background:var(--frame)}.d-media.portrait video{aspect-ratio:9/16;width:auto;height:62vh;max-width:100%}
.d-body{padding:26px 36px 56px}
.d-body h2{margin:0;font-size:27px;font-weight:900;line-height:1.25;letter-spacing:-.015em;text-wrap:balance}
.d-meta{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px;margin:10px 0 0;font-size:13.5px;color:var(--ink-2)}.d-meta .lv{display:inline-flex;align-items:center;gap:6px;color:var(--ink)}.d-meta code{font:500 12.5px var(--sans);color:var(--ink-3)}
.d-desc{margin:16px 0 0;font-size:16px;line-height:1.75;max-width:62ch}
.d-version{padding:12px 36px 14px;background:var(--ground);border-bottom:1px solid var(--line-2);font-size:13px;color:var(--ink-2)}.d-version .open-demo{display:inline-block;margin-top:6px}.d-version label{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;font-weight:500;color:var(--ink)}.d-version select{flex:1;min-width:220px;padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:var(--paper);font-size:13px}
.d-version label+.demo-row{margin-top:8px}.demo-row{display:flex;align-items:flex-start;justify-content:space-between;gap:6px 16px}.demo-more{flex:1;min-width:0}.demo-more>summary{cursor:pointer;color:var(--ink);font-weight:500;list-style-position:inside}.demo-more .playback-note{display:none}.d-version .demo-meta p{margin:6px 0 0}.d-version .small{font-size:12.5px;color:var(--ink-2)}.d-version .demo-meta details{margin-top:8px}.d-version .demo-meta summary{cursor:pointer}.d-version a{font-size:13px;white-space:nowrap}
.d-status{display:flex;gap:12px;align-items:flex-start;margin:20px 0 6px;padding:14px 16px;border:1px solid var(--line);border-radius:10px}.d-status .dot{margin-top:8px}.d-status strong{display:block;font-size:15px}.d-status p{margin:2px 0 0;font-size:13.5px;color:var(--ink-2)}
.sec{border-top:1px solid var(--line-2)}.sec:first-of-type{margin-top:18px}
.sec summary{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:15px 0;cursor:pointer;list-style:none;font-size:15.5px;font-weight:700}.sec summary::-webkit-details-marker{display:none}.sec summary svg{color:var(--ink-3);transition:transform .25s var(--ease)}.sec[open] summary svg{transform:rotate(180deg)}
.sec-in{padding:0 0 18px;font-size:14.5px;line-height:1.8;color:var(--ink-2)}.sec-in ul{margin:0;padding-left:1.2em}.sec-in li{margin:3px 0}.sec-in p{margin:10px 0 0}.sec-in details{margin-top:10px}.sec-in summary{cursor:pointer;font-weight:500}.sec-in a{overflow-wrap:anywhere}
.copy-wrap{position:relative}.copy-wrap pre{margin:0;padding:16px 16px 16px 16px;padding-right:84px;border-radius:10px;background:var(--ground);white-space:pre-wrap;overflow-wrap:anywhere;font:400 13.5px/1.75 var(--sans);color:var(--ink)}
.copy{position:absolute;top:10px;right:10px;display:inline-flex;align-items:center;gap:5px;height:30px;padding:0 10px;border:1px solid var(--line);border-radius:7px;background:var(--paper);font-size:12.5px;cursor:pointer}.copy svg{width:14px;height:14px}.copy:hover{border-color:var(--ink-3)}
.scrim{display:none}
@media (max-width:1100px){.shell,.about-in{grid-template-columns:200px minmax(0,1fr);gap:32px}}
@media (max-width:900px){
.bar{height:54px}.bar nav{gap:16px;font-size:13.5px}.bar nav .gh{display:none}
.intro{grid-template-columns:1fr;padding:28px 16px 16px;gap:10px}.intro h1{font-size:28px}.intro p{font-size:14.5px}
.shell{display:block;padding:0 16px}
.filters{position:fixed;left:0;right:0;bottom:0;top:auto;z-index:30;max-height:84vh;padding:0 20px 28px;background:var(--paper);border-radius:16px 16px 0 0;transform:translateY(102%);transition:transform .38s var(--ease);box-shadow:0 -8px 30px rgba(0,0,0,.18)}
.filters.open{transform:none}
.sheet-head{display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:1;margin:0 -20px 14px;padding:14px 20px;background:var(--paper);border-bottom:1px solid var(--line-2)}.sheet-head strong{font-size:16px}.sheet-head button{height:36px;padding:0 16px;border:0;border-radius:18px;background:var(--ink);color:#fff;cursor:pointer;font-size:14px}
.scrim{display:block;position:fixed;inset:0;z-index:29;background:rgba(18,19,20,.45);opacity:0;pointer-events:none;transition:opacity .3s}.scrim.on{opacity:1;pointer-events:auto}
.tools{padding:10px 0 8px}.search input{height:44px;font-size:15px}.filter-btn{display:inline-flex;height:44px}
.rail{display:flex;gap:7px;overflow-x:auto;margin:0 -16px;padding:2px 16px 10px;scrollbar-width:none}.rail::-webkit-scrollbar{display:none}
.rail button{flex:none;height:34px;padding:0 13px;border:1px solid var(--line);border-radius:17px;background:var(--paper);font-size:13.5px;cursor:pointer;white-space:nowrap}.rail button[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:#fff}
.status-line{margin:2px 0 14px;font-size:13.5px}
.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 12px}.cap .t{font-size:14px}.cap .m{font-size:12px}.cap .m .u{display:none}
.about-in{grid-template-columns:1fr;gap:18px;padding:36px 16px 48px}.routes{grid-template-columns:1fr}
.d-body{padding:20px 18px 44px}.d-version{padding:10px 18px 12px}.d-body h2{font-size:23px}.d-media.portrait video{height:58vh}
}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
</style></head><body>
<a class="skip" href="#grid">跳到模板列表</a>
<header class="bar"><a class="mark" href="./"><b>AI Cut</b><span>模板库</span></a>
<nav aria-label="站点"><a href="https://github.com/Isaac3113/ai-cut/blob/main/docs/NOTION_GUIDE.zh-CN.md">学习自动剪辑</a><a href="#about">来源与状态说明</a><a class="gh" href="https://github.com/Isaac3113/ai-cut">GitHub</a></nav></header>
<!--DRAFT_NOTICE-->
<section class="intro"><h1 id="template-library">视频特效模板库</h1>
<p id="lead">口播、录屏教学、流程、数据、产品展示……按用途找动画效果。先看它动起来的样子，选中了再看要准备什么素材、现在能不能直接用。第一次接触自动剪辑？<a href="https://github.com/Isaac3113/ai-cut/blob/main/docs/NOTION_GUIDE.zh-CN.md">从这里开始</a></p></section>
<div class="shell">
<aside class="filters" id="filters" aria-label="筛选模板"><div class="sheet-head"><strong>筛选</strong><button type="button" id="sheetDone">看结果</button></div>
<div class="facet"><h2>现在能不能用</h2><div class="opts" id="f-level"></div></div>
<div class="facet"><h2>用途</h2><div class="opts" id="f-use"></div></div>
<div class="facet"><h2>画面比例</h2><div class="opts" id="f-ratio"></div></div>
<details class="more" id="moreFilters"><summary><svg class="i" viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>更多筛选</summary>
<label>来源层级<select id="layer" aria-label="来源层级"></select></label>
<label>原始细类<select id="sourceCategory" aria-label="原始细类"><option value="">全部原始细类</option></select></label>
<label>详细状态<select id="executionStatus" aria-label="详细状态"><option value="">全部详细状态</option></select></label>
<label>演示来源<select id="demoType" aria-label="演示来源"><option value="">全部演示来源</option><option value="own">本人Demo（已登记案例）</option><option value="official">官网示例</option><option value="other">其他本地演示</option></select></label>
</details>
<button type="button" class="clear" id="reset">清除全部筛选</button></aside>
<div class="scrim" id="scrim"></div>
<main id="main">
<div class="tools"><label class="search"><svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/></svg><input id="search" type="search" aria-label="搜索模板" placeholder="搜索效果、用途或编号，例如：时间线、对比、手机界面" autocomplete="off"></label>
<button type="button" class="filter-btn" id="openFilters" aria-controls="filters" aria-expanded="false"><svg class="i" viewBox="0 0 24 24"><path d="M4 6h16M7 12h10M10 18h4"/></svg>筛选<b id="filterCount"></b></button></div>
<div class="rail" id="rail" aria-label="按用途快速筛选"></div>
<div class="status-line" id="result" aria-live="polite"></div>
<div class="grid" id="grid"></div>
<div class="more-row"><button type="button" class="load" id="loadMore">再看 24 个</button></div>
</main></div>
<section class="about" id="about"><div class="about-in"><h2>来源与状态说明</h2><div class="about-body">
<h3>预览和能用是两回事</h3><p>先按内容选择风格与场景，不强套固定整片设计。AI Cut通用自制模板在来源分类中单列；官方预览、旧效果分支与真实可调用状态分别说明。官网 Demo 需要联网；本地演示为静音版，示例数值与模拟界面不代表真实业务成果。第三方个人原包、Key 和完整原片不在本目录，自制包按各条说明取得。</p>
<p>每个模板固定七项：预览、用途、素材、可改参数、给 AI 的指令、使用状态、来源许可，点开任意模板即可查看。中文名称、使用条件、来源和 Demo 放在同一个入口；有演示不等于已通过新片验收。</p>
<p id="syncStatus"></p><p id="localPlayback">本人库样例为静音版；已关联的本机原声版可在同一条模板里直接播放。</p>
<h3>目录里有什么</h3><p>通用自制模板、官方风格、动画控件、代码注册项与真人特效分别登记，数量不能合称整片模板。</p><div class="stats">__STATS__</div>
<h3>四种剪辑路线</h3><div class="routes"><div class="route"><strong>知识口播</strong><p>讲述与原意驱动画面。优先字幕、概念解释、重点句与关系图。</p></div><div class="route"><strong>系统实操</strong><p>真实按钮与操作证据优先。放大、标注须指向实际目标。</p></div><div class="route"><strong>长访谈切片</strong><p>先按独立主题剪成完整论点，再添加包装与字幕。</p></div><div class="route"><strong>旅行 / Vlog</strong><p>按地点、事件、镜头连续性、环境声与音乐节奏剪辑；当前仅定义路线边界，未实现专用自动流程。</p></div></div>
<h3>来源、许可与授权</h3><p>来源、许可证与更新口径：<a href="https://github.com/Isaac3113/ai-cut/blob/main/templates/PROVENANCE.zh-CN.md">来源说明</a> · <a href="https://github.com/Isaac3113/ai-cut/blob/main/templates/README.zh-CN.md">完整中文清单</a> · <a href="https://github.com/Isaac3113/ai-cut/blob/main/docs/template-gallery/CATEGORIES.md">分类动画预览</a> · <a href="https://github.com/Isaac3113/ai-cut/blob/main/skill/ai-cut/references/template-selection.md">Skill选择规则</a></p>
<p class="foot">2026-10-27历史归档授权：以后每片经QA精选的本人静音Demo与集成说明可进入私人Git；完整原片、完整成片、源人像蒙版、Key、个人包与客户敏感信息不进入Git。2026-11-02现行展示授权：本页精选的现有预览可在 aicut.agi-top.com 公开展示，供个人学习与免费交流，不用于业务获客或销售。同日后续用户授权将GitHub源码仓库公开，上方源码与教学链接可直接浏览、下载，无需申请仓库权限。官网候选预览保留原来源与许可，不代表附送官方原包或全部模板已可执行。其他电脑仍需独立准备运行环境、个人模板授权和新片素材。</p>
</div></div></section>
<dialog class="detail" id="detail" aria-labelledby="d-title"><div class="d-top"><button type="button" class="d-close" id="d-close" aria-label="关闭"><svg class="i" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></button></div><div id="d-content"></div></dialog>
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
  return {src:demoKey(d),audio:false,label:e.layer==='authored'?'自制模板通用示例 · 静音':demoSource(e,d)==='official'?'官网示例 · 联网播放':'静音库样例 · 随仓库同步'};
}
function demoLabel(e,d){const source=e.layer==='authored'?'自制模板通用示例':{own:'本人',official:'官网示例',other:'本地效果'}[demoSource(e,d)],ratio=demoRatio(e,d),c=demoCase(e,d);return source+' · '+(ratio==='unknown'?'比例未标注':ratio)+(c?' · '+c.source.version:(d.variant_id?' · '+d.variant_id:''))}
// END_DEMO_MODEL
const $=x=>document.getElementById(x),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let overrides=Object.create(null);const selectedKeys=new Map();
const ICON={chev:'<svg class="i" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>',x:'<svg class="i" viewBox="0 0 24 24"><path d="M7 7l10 10M17 7 7 17"/></svg>',copy:'<svg class="i" viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h8"/></svg>',play:'<svg class="i" viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z"/></svg>'};
function safe(x){return typeof x==='string'&&(x.startsWith('https://')||x.startsWith('demos/')||/^local-owner-media\/[A-Za-z0-9_-]+\.mp4$/.test(x))?esc(x):''}
function bullet(items){return '<ul>'+(items||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'}
function integrationInfo(e,d){const c=demoCase(e,d);if(!c)return '';const s=c.source,i=c.invocation;return '<details><summary>本片接入与复用边界</summary><p>Git库样例登记说明：'+esc(d.description_zh||'见本次记录')+'</p><p>'+esc(c.project_id+' · '+s.package_id+' · '+s.version)+'</p><p>输入：'+esc(i.inputs_zh.join('；'))+'</p><p>调用：<code>'+esc(i.command)+'</code></p><p>本片检查：'+esc(c.qa.scope)+'</p><p>仅此版本与Demo；原条目和全部变体验证状态不因此改变。</p></details>'}
function demoMetadata(e,d){const p=demoPlayback(e,d,overrides),c=demoCase(e,d),source=demoSource(e,d);return '<p class="playback-note">'+esc(p.label)+'</p>'+(c?'<p class="small">当前本人Demo版本：'+esc(c.source.version)+' · 已解码与抽帧检查'+(c.qa.owner_artistic_acceptance?'':' · 风格待确认')+'</p>':'<p class="small">'+esc(d.description_zh||'')+'</p><p class="small">'+esc(source==='official'?'官网原始示例；不代表本人输入已经验证。':source==='own'?'历史本人素材样例；沿用原登记的检查范围。':'本地效果示例；不据此认定画面人物或业务成果。')+'</p>')+integrationInfo(e,d)}
function cardTitle(e){return e.layer==='style'&&e.family_label_zh?e.family_label_zh:e.label_zh}
const LEVEL={source_ready:['ready','源码可调用'],package_required:['prep','需自备授权原包'],not_integrated:['prep','需先取得原包'],adaptation_required:['prep','需源码适配'],claim_pending:['view','原包未开放'],preview:['view','官方预告']};
const LEVEL_GROUPS={ready:'源码可调用',prep:'需原包或适配',view:'暂时只能看预览'};
function level(e){return LEVEL[e.learner_guide?.execution_status]||['view',e.learner_guide?.execution_status_zh||'状态待核对']}
const RATIO_NAME={'9:16':'竖屏 9:16','16:9':'横屏 16:9','1:1':'方形 1:1','4:3':'4:3','3:4':'3:4',unknown:'比例未标注'};
const LAYER_OPTIONS=[...Object.entries(LAYERS),['preview','官方预告／待开放']];
const state={q:'',level:'',use:'',ratio:'',layer:'',sourceCat:'',execution:'',source:''};
const FACET_LABEL={level:v=>LEVEL_GROUPS[v],use:v=>(DATA.learner_categories||{})[v]||v,ratio:v=>RATIO_NAME[v]||v,layer:v=>(LAYER_OPTIONS.find(x=>x[0]===v)||[,v])[1],sourceCat:v=>v,execution:v=>executionOptions.get(v)||v,source:v=>({own:'本人Demo',official:'官网示例',other:'其他本地演示'}[v])};
const searchText=new Map();function textOf(e){if(!searchText.has(e.id))searchText.set(e.id,JSON.stringify(e).toLowerCase());return searchText.get(e.id)}
function passes(e,skip){
  const g=e.learner_guide||{};
  if(skip!=='level'&&state.level&&level(e)[0]!==state.level)return false;
  if(skip!=='use'&&state.use&&g.category!==state.use)return false;
  if(skip!=='layer'&&state.layer&&e.layer!==state.layer)return false;
  if(skip!=='sourceCat'&&state.sourceCat&&e.category_zh!==state.sourceCat)return false;
  if(skip!=='execution'&&state.execution&&g.execution_status!==state.execution)return false;
  if(state.q&&!textOf(e).includes(state.q))return false;
  const source=skip==='source'?'':state.source,ratio=skip==='ratio'?'':state.ratio;
  if(candidateDemos(e,source,ratio).length)return true;
  return !source&&!(e.demos||[]).length&&(!ratio||demoRatio(e,{})===ratio);
}
function facetHas(e,f,v){if(f==='level')return level(e)[0]===v;if(f==='use')return e.learner_guide?.category===v;if(f==='ratio')return candidateDemos(e,state.source,v).length>0;return false}
function facetButtons(f,options,allLabel){
  const pool=ALL_ENTRIES.filter(e=>passes(e,f));
  return [['',allLabel,pool.length],...options.map(([v,l])=>[v,l,pool.filter(e=>facetHas(e,f,v)).length])].map(([v,l,n])=>{const on=state[f]===v;return '<button type="button" class="opt'+(n||on?'':' zero')+'" data-f="'+f+'" data-v="'+esc(v)+'" aria-pressed="'+on+'"'+(n||on?'':' disabled')+'>'+(f==='level'&&v?'<span class="dot '+v+'"></span>':'')+'<span>'+esc(l)+'</span><span class="n">'+n.toLocaleString('zh-CN')+'</span></button>'}).join('')
}
const useOptions=Object.entries(DATA.learner_categories||{});
const ratios=[...new Set(ALL_ENTRIES.flatMap(e=>(e.demos||[]).map(d=>demoRatio(e,d))))].sort((a,b)=>{const order=['9:16','16:9','1:1','4:3','3:4'];return (order.indexOf(a)<0?99:order.indexOf(a))-(order.indexOf(b)<0?99:order.indexOf(b))||a.localeCompare(b)});
const executionOptions=new Map(ALL_ENTRIES.map(e=>[e.learner_guide?.execution_status,e.learner_guide?.execution_status_zh]).filter(([k,v])=>k&&v));
function renderFilters(){
  $('f-level').innerHTML=facetButtons('level',Object.entries(LEVEL_GROUPS),'全部');
  $('f-use').innerHTML=facetButtons('use',useOptions,'全部用途');
  $('f-ratio').innerHTML=facetButtons('ratio',ratios.map(r=>[r,RATIO_NAME[r]||r]),'全部比例');
  $('rail').innerHTML=[['','全部'],...useOptions].map(([v,l])=>'<button type="button" data-f="use" data-v="'+esc(v)+'" aria-pressed="'+(state.use===v)+'">'+esc(l)+'</button>').join('');
  const active=['level','use','ratio','layer','sourceCat','execution','source'].filter(f=>state[f]).length;$('filterCount').textContent=active||'';
  $('layer').value=state.layer;$('sourceCategory').value=state.sourceCat;$('executionStatus').value=state.execution;$('demoType').value=state.source;
}
let shownLimit=24,rows=[];
const io='IntersectionObserver' in window?new IntersectionObserver(items=>{for(const it of items){if(!it.isIntersecting)continue;const v=it.target;io.unobserve(v);if(!v.getAttribute('src')){v.preload='metadata';v.src=v.dataset.src+(v.dataset.thumb?'#t=0.6':'')}}},{rootMargin:'300px 0px'}):null;
function tileHtml(e,d){
  const [lv,lvLabel]=level(e),r=d?demoRatio(e,d):'unknown',poster=d?(d.poster_path||(demoSource(e,d)==='official'?e.learner_poster:'')):'',p=d?demoPlayback(e,d,overrides):null;
  const media=d?'<video muted playsinline loop preload="none" '+(poster?'poster="'+safe(poster)+'" ':'data-thumb="1" ')+'data-src="'+safe(p.src)+'" aria-hidden="true"></video><span class="play">'+ICON.play+'</span>':'<span class="noplay">暂无演示</span>';
  return '<a class="tile" href="#m='+encodeURIComponent(e.id)+'" data-entry-id="'+esc(e.id)+'"><span class="frame">'+media+(d&&r!=='unknown'?'<span class="rt">'+esc(r)+'</span>':'')+'</span><span class="cap"><span class="t">'+esc(cardTitle(e))+'</span><span class="m"><span class="lv"><span class="dot '+lv+'"></span>'+esc(lvLabel)+'</span><span class="u">'+esc(e.learner_guide?.category_zh||e.category_zh)+'</span></span></span></a>';
}
function chipsHtml(){return ['level','use','ratio','layer','sourceCat','execution','source'].filter(f=>state[f]).map(f=>'<button type="button" class="chip" data-clear="'+f+'" aria-label="移除筛选：'+esc(FACET_LABEL[f](state[f]))+'">'+esc(FACET_LABEL[f](state[f]))+ICON.x+'</button>').join('')+(state.q?'<button type="button" class="chip" data-clear="q">“'+esc(state.q)+'”'+ICON.x+'</button>':'')}
function render(){
  stopVideos();rows=ALL_ENTRIES.filter(e=>passes(e,''));renderFilters();
  const grid=$('grid');grid.className='grid'+(state.ratio==='9:16'||state.ratio==='3:4'?' tall':state.ratio==='1:1'?' square':state.ratio==='16:9'?' wide':'');
  const demoCount=rows.reduce((n,e)=>n+candidateDemos(e,state.source,state.ratio).length,0);
  $('result').innerHTML='<span><strong>'+rows.length.toLocaleString('zh-CN')+'</strong> 个模板'+(rows.length!==ALL_ENTRIES.length?' · 共 '+ALL_ENTRIES.length.toLocaleString('zh-CN')+' 个':'')+'</span>'+chipsHtml()+'<p class="hint">缩略图只代表效果的样子。点开模板看能不能直接用、要准备什么（共 '+demoCount.toLocaleString('zh-CN')+' 个演示版本）。<a href="#about">来源与状态说明</a></p>';
  grid.innerHTML=rows.slice(0,shownLimit).map(e=>{const d=selectedDemo(e,state.source,state.ratio,selectedKeys.get(e.id));if(d)selectedKeys.set(e.id,demoKey(d));return tileHtml(e,d)}).join('')||'<div class="empty"><p>没有符合条件的模板。</p><button type="button" class="load" data-reset>清除筛选</button></div>';
  grid.querySelectorAll('video[data-src]').forEach(v=>io?io.observe(v):(v.src=v.dataset.src));
  const rest=Math.max(0,rows.length-shownLimit);$('loadMore').hidden=!rest;$('loadMore').innerHTML='再看 24 个<span>还有 '+rest.toLocaleString('zh-CN')+' 个</span>';
}
function appendMore(){const from=shownLimit;shownLimit+=24;const html=rows.slice(from,shownLimit).map(e=>{const d=selectedDemo(e,state.source,state.ratio,selectedKeys.get(e.id));if(d)selectedKeys.set(e.id,demoKey(d));return tileHtml(e,d)}).join('');$('grid').insertAdjacentHTML('beforeend',html);$('grid').querySelectorAll('video[data-src]:not([src])').forEach(v=>io?io.observe(v):(v.src=v.dataset.src));const rest=Math.max(0,rows.length-shownLimit);$('loadMore').hidden=!rest;$('loadMore').innerHTML='再看 24 个<span>还有 '+rest.toLocaleString('zh-CN')+' 个</span>';const first=$('grid').children[from];if(first)first.focus({preventScroll:true})}
function stopVideos(except){document.querySelectorAll('video').forEach(v=>{if(v!==except&&!v.paused)v.pause()})}
const hoverable=matchMedia('(hover:hover) and (pointer:fine)').matches;
$('grid').addEventListener('pointerover',ev=>{if(!hoverable)return;const t=ev.target.closest('.tile');if(!t||t.contains(ev.relatedTarget))return;const v=t.querySelector('video');if(!v)return;if(!v.getAttribute('src'))v.src=v.dataset.src;stopVideos(v);t.classList.add('playing');v.play().catch(()=>{})});
$('grid').addEventListener('pointerout',ev=>{const t=ev.target.closest('.tile');if(!t||t.contains(ev.relatedTarget))return;const v=t.querySelector('video');t.classList.remove('playing');if(v&&!v.paused)v.pause()});
function setFilter(f,v){state[f]=v;shownLimit=24;if(f==='source')syncOwnerHash();render()}
document.addEventListener('click',ev=>{const o=ev.target.closest('[data-f]');if(o&&!o.disabled){setFilter(o.dataset.f,state[o.dataset.f]===o.dataset.v&&o.dataset.v?'':o.dataset.v);return}const c=ev.target.closest('[data-clear]');if(c){if(c.dataset.clear==='q'){state.q='';$('search').value=''}else state[c.dataset.clear]='';shownLimit=24;if(c.dataset.clear==='source')syncOwnerHash();render();return}if(ev.target.closest('[data-reset]'))resetAll()});
function resetAll(){Object.keys(state).forEach(k=>state[k]='');$('search').value='';shownLimit=24;syncOwnerHash();render()}
$('reset').onclick=resetAll;
let searchTimer;$('search').addEventListener('input',()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.q=$('search').value.trim().toLowerCase();shownLimit=24;render()},140)});
[['layer','layer'],['sourceCategory','sourceCat'],['executionStatus','execution'],['demoType','source']].forEach(([id,f])=>$(id).addEventListener('change',()=>setFilter(f,$(id).value)));
LAYER_OPTIONS.forEach(([v,l],i)=>{if(!i){const a=document.createElement('option');a.value='';a.textContent='全部来源层级';$('layer').append(a)}const o=document.createElement('option');o.value=v;o.textContent=l;$('layer').append(o)});
[...new Set(ALL_ENTRIES.map(e=>e.category_zh))].sort((a,b)=>a.localeCompare(b,'zh')).forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;$('sourceCategory').append(o)});
executionOptions.forEach((label,key)=>{const o=document.createElement('option');o.value=key;o.textContent=label;$('executionStatus').append(o)});
$('loadMore').onclick=appendMore;
function openSheet(on){$('filters').classList.toggle('open',on);$('scrim').classList.toggle('on',on);$('openFilters').setAttribute('aria-expanded',String(on));if(on)$('sheetDone').focus()}
$('openFilters').onclick=()=>openSheet(true);$('sheetDone').onclick=()=>{openSheet(false);$('openFilters').focus()};$('scrim').onclick=()=>openSheet(false);
document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&$('filters').classList.contains('open'))openSheet(false)});
function syncOwnerHash(){try{if(state.source==='own')history.replaceState(null,'','#owner-demos');else if(location.hash==='#owner-demos')history.replaceState(null,'',location.pathname+location.search)}catch(_){}}
// Detail panel: every section of the seven-part guide stays reachable here.
function learnerSection(s){
  if(s.id==='preview')return '';
  let content=s.id==='instructions'?'<div class="copy-wrap"><pre>'+esc((s.text||[]).join('\n'))+'</pre><button type="button" class="copy" data-copy>'+ICON.copy+'<span>复制指令</span></button></div>':bullet(s.text||[]);
  if(s.notes?.length){content+=s.id==='status'?'<details><summary>原始检查范围</summary>'+bullet(s.notes)+'</details>':bullet(s.notes)}
  if(s.evidence?.length)content+='<p>参数依据：'+s.evidence.map(p=>'<a target="_blank" rel="noopener" href="https://github.com/Isaac3113/ai-cut/blob/main/'+esc(p)+'">'+esc(p.split('/').pop())+'</a>').join(' · ')+'</p>';
  if(s.id==='source')content+='<p>'+(s.url?'<a target="_blank" rel="noopener" href="'+safe(s.url)+'">原始来源</a>':'')+(s.repository_url?' · <a target="_blank" rel="noopener" href="'+safe(s.repository_url)+'">上游技术资料</a>':'')+(s.package_url?' · <a target="_blank" rel="noopener" href="'+safe(s.package_url)+'">作者内容包（.motion，非个人签发包）</a>':'')+'</p>';
  return '<details class="sec"'+(['use','instructions'].includes(s.id)?' open':'')+'><summary>'+esc(s.title.replace(/^\d+\.\s*/,''))+ICON.chev+'</summary><div class="sec-in">'+content+'</div></details>'
}
let detailEntry=null,detailFromNav=false;
function detailHtml(e,choices,d){
  const g=e.learner_guide||{category_zh:e.category_zh,status:'使用条件待核对',sections:[]},[lv]=level(e),p=d?demoPlayback(e,d,overrides):null,portrait=d&&['9:16','3:4'].includes(demoRatio(e,d)),poster=d&&(d.poster_path||(demoSource(e,d)==='official'?e.learner_poster:''));
  const media=d?'<div class="d-media'+(portrait?' portrait':'')+'"><video controls autoplay loop playsinline '+(p.audio?'':'muted ')+(poster?'poster="'+safe(poster)+'" ':'')+'src="'+safe(p.src)+'" aria-label="'+esc(e.label_zh)+' 演示"></video></div>':'<div class="d-media"><p class="noplay" style="position:static;padding:80px 0">暂无可播放演示；见本条来源状态</p></div>';
  const version=d?'<div class="d-version">'+(choices.length>1?'<label>演示版本<select class="demo-version" aria-label="'+esc(e.label_zh)+' 演示版本">'+choices.map(x=>'<option value="'+esc(demoKey(x))+'"'+(demoKey(x)===demoKey(d)?' selected':'')+'>'+esc(demoLabel(e,x))+'</option>').join('')+'</select></label>':'')+'<div class="demo-row"><details class="demo-more"><summary>'+esc(p.label)+' · 演示说明</summary><div class="demo-meta">'+demoMetadata(e,d)+'</div></details><a class="open-demo" href="'+safe(p.src)+'" target="_blank" rel="noopener">新窗口打开</a></div></div>':'';
  const status=g.execution_status_zh&&g.status!==g.execution_status_zh?'<p>'+esc(g.status)+'</p>':'';
  return media+version+'<div class="d-body"><h2 id="d-title">'+esc(cardTitle(e))+'</h2><p class="d-meta"><span>'+esc(g.category_zh)+'</span><span>'+esc(e.category_zh)+'</span><span>'+esc(LAYERS[e.layer]||'官方预告')+'</span><code>'+esc(e.id)+'</code></p><p class="d-desc">'+esc(e.description_zh)+'</p><div class="d-status"><span class="dot '+lv+'"></span><div><strong>'+esc(g.execution_status_zh||g.status)+'</strong>'+status+'</div></div>'+(g.sections||[]).map(learnerSection).join('')+'</div>';
}
function openDetail(id,fromNav){
  const e=ALL_ENTRIES.find(x=>x.id===id);if(!e)return false;stopVideos();detailEntry=e;detailFromNav=fromNav;detailCleaned=false;
  const choices=candidateDemos(e),d=selectedDemo(e,'','',selectedKeys.get(e.id));
  $('d-content').innerHTML=detailHtml(e,choices,d);const dlg=$('detail');if(!dlg.open)dlg.showModal();dlg.scrollTop=0;const head=$('d-title');if(head){head.tabIndex=-1;head.focus({preventScroll:true})}
  bindDetail(e,choices);return true;
}
function bindDetail(e,choices){const dlg=$('detail'),sel=dlg.querySelector('.demo-version');if(sel&&!sel.dataset.bound){sel.dataset.bound='1';sel.addEventListener('change',()=>{const nd=choices.find(x=>demoKey(x)===sel.value);if(!nd)return;selectedKeys.set(e.id,demoKey(nd));$('d-content').innerHTML=detailHtml(e,choices,nd);bindDetail(e,choices);dlg.querySelector('.demo-version')?.focus()})}}
$('d-content').addEventListener('click',ev=>{const b=ev.target.closest('[data-copy]');if(!b)return;const text=b.parentElement.querySelector('pre').textContent;const done=()=>{b.querySelector('span').textContent='已复制';setTimeout(()=>{b.querySelector('span').textContent='复制指令'},1600)};if(navigator.clipboard)navigator.clipboard.writeText(text).then(done,()=>{});});
// One close path: some embedded browsers never dispatch the dialog close event.
let detailCleaned=true;
function closeDetail(viaHistory){
  const dlg=$('detail');if(dlg.open)dlg.close();if(detailCleaned)return;detailCleaned=true;stopVideos();
  const v=$('d-content').querySelector('video');if(v){v.removeAttribute('src');v.load()}
  if(!viaHistory&&location.hash.startsWith('#m=')){if(detailFromNav)history.back();else history.replaceState(null,'',location.pathname+location.search)}
  const t=detailEntry&&document.querySelector('.tile[data-entry-id="'+CSS.escape(detailEntry.id)+'"]');if(t)t.focus({preventScroll:true});
}
$('d-close').onclick=()=>closeDetail(false);
$('detail').addEventListener('click',ev=>{if(ev.target===$('detail'))closeDetail(false)});
$('detail').addEventListener('cancel',ev=>{ev.preventDefault();closeDetail(false)});
$('detail').addEventListener('keydown',ev=>{if(ev.key==='Escape'){ev.preventDefault();closeDetail(false)}});
$('detail').addEventListener('close',()=>closeDetail(false));
$('grid').addEventListener('click',ev=>{const t=ev.target.closest('.tile');if(t&&location.hash===t.getAttribute('href')){ev.preventDefault();openDetail(t.dataset.entryId,false)}});
function routeHash(fromNav){const h=location.hash;if(h.startsWith('#m=')){openDetail(decodeURIComponent(h.slice(3)),fromNav)}else{if($('detail').open||!detailCleaned)closeDetail(true);if(h==='#owner-demos'&&state.source!=='own'&&$('demoType').querySelector('option[value=own]')){state.source='own';shownLimit=24;render()}}}
window.addEventListener('hashchange',()=>routeHash(true));
const sync=DATA.sync_status||{};$('syncStatus').textContent='目录同步：'+(sync.checked_at||DATA.updated_on)+'。目录登记、原包取得、运行接入分别标记；旧案例保留其真实版本。'+(sync.scope_zh||'成功来源与覆盖边界见 GitHub 的本轮同步说明。')+((sync.gaps||[]).length?' 仍有 '+sync.gaps.length+' 项来源缺口，详见同步记录。':'');
if(location.hash==='#owner-demos'&&$('demoType').querySelector('option[value=own]'))state.source='own';
render();if(location.hash.startsWith('#m='))routeHash(false);
if(location.protocol!=='file:'){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),1800);
  fetch('local-demo-manifest.json',{cache:'no-store',credentials:'same-origin',signal:controller.signal}).then(response=>response.ok?response.json():null).then(manifest=>{
    overrides=localOverrides(manifest,DATA.entries);const count=Object.keys(overrides).length;if(!count)return;$('localPlayback').textContent='已关联 '+count+' 个本机版本；原声与静音状态显示在对应模板里。';render();
  }).catch(()=>{}).finally(()=>clearTimeout(timer));
}
</script></body></html>'''


def build(root: Path, strict=False):
    gallery = root / 'docs/template-gallery'
    gallery.mkdir(parents=True, exist_ok=True)
    entries, previews, provenance = read_sources(root)
    verify_authored_packages(root, entries)
    entries, integrations, integration_source = apply_integrations(root, entries, strict)
    entries.sort(key=lambda e: (-1 if e['layer']=='authored' else 0 if e['id']=='mg-style-314486' else 1 if e['layer']=='style' and e['category_zh']=='口播与讲解' else 2 if e['layer']=='style' else 3))
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
    view = gallery_view(root, data)
    view_counts = view['counts_by_layer']
    view_layers = {k: v for k, v in LAYERS.items() if view_counts.get(k)}
    page = HTML.replace('__DATA__', json.dumps(view, ensure_ascii=False).replace('<', chr(92)+'u003c'))
    page = page.replace('__LAYERS__', json.dumps(view_layers, ensure_ascii=False))
    page = page.replace('__STATS__', ''.join(f'<div class="stat"><strong>{view_counts[k]}</strong>{escape(v)}</div>' for k,v in view_layers.items()) + f'<div class="stat"><strong>{len(view["integrations"])}</strong>本片接入记录（不重复计为模板）</div>')
    if not any(is_owner_demo(d) for e in view['entries'] for d in e['demos']):
        page = page.replace('<option value="own">本人Demo（已登记案例）</option>', '')
        page = page.replace('<p id="localPlayback">本人库样例为静音版；已关联的本机原声版可在同一条模板里直接播放。</p>', '<p id="localPlayback"></p>')
    if not strict:
        page=page.replace('<!--DRAFT_NOTICE-->','<p class="dev-notice">开发预览：部分演示仍在制作，不能当成全部完成。</p>')
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
