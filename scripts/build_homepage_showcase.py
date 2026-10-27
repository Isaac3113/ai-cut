"""Build a GitHub-compatible, four-layer showcase from the frozen local catalog.

Uses only Python's standard library and existing FFmpeg/ffprobe. Local MP4s become
silent, original-speed excerpts of at most three seconds. Official poster URLs
are referenced from the snapshot without network requests or remote downloads.
Only catalog-owned GIF names are written; other homepage assets are never removed.
By default only a fragment is written. Explicit --write-readme replaces the unique
HOMEPAGE_SHOWCASE section; all bytes outside it, including COMPARISON, stay intact.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import subprocess
from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / 'docs/template-gallery'
OUT = GALLERY / 'demos/homepage'
WORK = ROOT / 'work/homepage-prep-20261027'
CATALOG = ROOT / 'templates/catalog.json'
SNAPSHOT = ROOT / 'templates/sources/motiongit-catalog.snapshot.json'
MANIFEST = OUT / 'manifest.json'
FRAGMENT = WORK / 'homepage-showcase.fragment.md'
MAX_BYTES = 512 * 1024
TOTAL_TARGET = 25 * 1024 * 1024
FPS = 10
MAX_SECONDS = 3.0
LAYERS = OrderedDict([
    ('style', '官网模板与片段'), ('control', '动画控件'),
    ('remotion', 'Remotion 代码注册项'), ('effect', '真人口播特效'),
])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-2500:])
    return result.stdout


def probe(path, ffprobe, count=False):
    return json.loads(run([ffprobe, '-v', 'error', *(['-count_frames'] if count else []),
                           '-show_streams', '-show_format', '-of', 'json', path]))


def local_demo(entry):
    matches = [d for d in entry.get('demos', []) if d.get('path', '').lower().endswith('.mp4')]
    if not matches:
        return None
    # Curated own demo (notably the approved B case) precedes synthetic examples.
    return sorted(matches, key=lambda d: d.get('kind') != 'own')[0]


def local_source(demo):
    path = (GALLERY / demo['path']).resolve()
    if not path.is_relative_to(GALLERY.resolve()) or not path.is_file():
        raise ValueError('Invalid or missing local demo: ' + demo['path'])
    return path


def https_url(url):
    if not isinstance(url, str) or urlsplit(url).scheme != 'https' or not urlsplit(url).netloc:
        raise ValueError('Expected an HTTPS URL')
    return url


def official_image(entry, snapshot, preview=False):
    records = snapshot['previews'] if preview else snapshot['templates']
    key = 'previewId' if preview else 'repositoryId'
    matches = [x for x in records if str(x.get(key)) == str(entry['source_id'])]
    if len(matches) != 1:
        raise ValueError(f"{entry['id']}: official image identity is not unique")
    source = matches[0]
    if not preview:
        assert source['templateId'] == entry['source_template_id']
        assert source['website'] == entry['source_url']
        assert source['ratio'] == entry['ratio']
    chinese = source.get('media', {}).get('zh', {})
    poster = https_url(chinese.get('poster') or source.get('poster') or chinese.get('preview') or source.get('preview'))
    if not re.search(r'\.(?:jpe?g|png|webp|gif)$', urlsplit(poster).path, re.I):
        raise ValueError(f"{entry['id']}: not an image URL")
    official_demos = [d for d in entry.get('demos', []) if d.get('url')]
    expected_demo = chinese.get('demo') or source.get('demo')
    assert any(d['url'] == expected_demo for d in official_demos), entry['id'] + ': poster/demo mismatch'
    return {'id': entry['id'], 'kind': 'official_poster', 'url': poster,
            'snapshot_id': str(source[key]), 'ratio': source.get('ratio'),
            'width': source.get('width'), 'height': source.get('height'),
            'source_demo_url': expected_demo, 'network_checked': False}


def validate_gif(path, source_meta, expected_frames, ffmpeg, ffprobe):
    meta = probe(path, ffprobe, count=True)
    video = next(s for s in meta['streams'] if s['codec_type'] == 'video')
    frames = int(video['nb_read_frames'])
    duration = float(meta['format']['duration'])
    assert frames == expected_frames, (path.name, frames, expected_frames)
    assert 0 < duration <= MAX_SECONDS + 0.001
    assert abs(duration - frames / FPS) < 0.011, (path.name, duration, frames / FPS)
    assert path.stat().st_size <= MAX_BYTES
    source_ratio = source_meta['width'] / source_meta['height']
    assert abs(video['width'] / video['height'] - source_ratio) / source_ratio < 0.015
    run([ffmpeg, '-v', 'error', '-xerror', '-i', path, '-f', 'null', '-'])
    return {'width': video['width'], 'height': video['height'], 'frames': frames,
            'duration_seconds': duration, 'bytes': path.stat().st_size, 'sha256': digest(path)}


def build_gif(entry, ffmpeg, ffprobe, cached=None, force=False):
    ident = entry['id']
    assert re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', ident)
    demo = local_demo(entry)
    source = local_source(demo)
    source_hash = digest(source)
    if demo.get('sha256') and demo['sha256'] != source_hash:
        raise ValueError(ident + ': source SHA256 differs from catalog')
    if demo.get('bytes') and demo['bytes'] != source.stat().st_size:
        raise ValueError(ident + ': source byte count differs from catalog')
    meta = probe(source, ffprobe)
    video = next(s for s in meta['streams'] if s['codec_type'] == 'video')
    duration = float(meta['format']['duration'])
    frames = max(1, math.floor(min(MAX_SECONDS, duration) * FPS + 1e-5))
    excerpt_duration = frames / FPS
    start = min(0.5, max(0, (duration - excerpt_duration) / 2))
    output = OUT / (ident + '.gif')
    if not force and cached and output.is_file() and cached.get('source_sha256') == source_hash and cached.get('sha256') == digest(output):
        verified = validate_gif(output, video, frames, ffmpeg, ffprobe)
        return {**cached, **verified}
    for edge, colors in ((360, 96), (320, 64), (280, 48), (240, 32)):
        if video['width'] >= video['height']:
            width = min(edge, video['width']); height = max(2, round(width * video['height'] / video['width'] / 2) * 2)
        else:
            height = min(edge, video['height']); width = max(2, round(height * video['width'] / video['height'] / 2) * 2)
        graph = (f'[0:v]fps={FPS},scale={width}:{height}:flags=lanczos,split[a][b];'
                 f'[a]palettegen=max_colors={colors}:stats_mode=diff[p];'
                 '[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle[out]')
        run([ffmpeg, '-y', '-v', 'error', '-ss', f'{start:.6f}', '-i', source,
             '-t', f'{excerpt_duration:.6f}', '-filter_complex_threads', '1', '-filter_complex', graph,
             '-map', '[out]', '-an', '-frames:v', frames, '-loop', '0', '-final_delay', '10',
             '-gifflags', '+transdiff', '-map_metadata', '-1', '-threads', '1', output])
        if output.stat().st_size <= MAX_BYTES:
            verified = validate_gif(output, video, frames, ffmpeg, ffprobe)
            return {'id': ident, 'kind': 'local_gif', 'path': output.relative_to(ROOT).as_posix(),
                    'source_demo': (Path('docs/template-gallery') / demo['path']).as_posix(),
                    'source_sha256': source_hash, 'source_bytes': source.stat().st_size,
                    'source_duration_seconds': duration, 'source_start_seconds': start,
                    'source_excerpt_seconds': excerpt_duration, 'playback_speed': 1,
                    'sampling_fps': FPS, 'palette_colors': colors, **verified}
    raise RuntimeError(ident + ': unable to meet 512 KiB GIF cap')


def card(entry, asset):
    esc = html.escape
    label = esc(entry['label_zh'])
    demos = []
    primary = local_demo(entry)
    for demo in entry.get('demos', []):
        if demo.get('path'):
            link = (Path('docs/template-gallery') / demo['path']).as_posix()
            title = '完整本地 Demo'
        elif demo.get('url'):
            link = https_url(demo['url'])
            title = '官方 Demo' + (' · ' + demo['ratio'] if demo.get('ratio') else '')
        else:
            continue
        demos.append(f'<a href="{esc(link, quote=True)}">{esc(title)}</a>')
    if not demos:
        raise ValueError(entry['id'] + ': missing full demo link')
    demo_link = ((Path('docs/template-gallery') / primary['path']).as_posix() if primary else asset['source_demo_url'])
    image_link = asset['path'] if asset['kind'] == 'local_gif' else asset['url']
    if asset['kind'] == 'local_gif':
        caption = f"原速节选 · {asset['duration_seconds']:.1f} 秒 · 无声 GIF"
        if 'case-studies/' in asset['source_demo']:
            caption = '本人 B 版局部 · ' + caption
        image_width = asset['width']
    else:
        caption = '官方预览图 · 点击查看完整 Demo'
        w, h = asset.get('width') or 1920, asset.get('height') or 1080
        image_width = round(360 * w / max(w, h))
    source = https_url(entry['source_url'])
    return ('<td width="50%" align="center" valign="top">\n'
            f'<strong>{label}</strong><br>\n'
            f'<a href="{esc(demo_link, quote=True)}"><img src="{esc(image_link, quote=True)}" width="{image_width}" alt="{label} · {esc(caption)}"></a><br>\n'
            f'<sub>{esc(caption)}</sub><br>\n'
            + ' · '.join(demos) + f' · <a href="{esc(source, quote=True)}">来源</a>\n</td>')


def table(entries, assets):
    lines = ['<table>']
    for i in range(0, len(entries), 2):
        lines.append('<tr>')
        lines.extend(card(entry, assets[entry['id']]) for entry in entries[i:i+2])
        if i + 1 == len(entries):
            lines.append('<td width="50%"></td>')
        lines.append('</tr>')
    lines.append('</table>')
    return '\n'.join(lines)


def make_fragment(catalog, assets):
    entries = catalog['entries']
    counts = Counter(e['layer'] for e in entries)
    lines = ['<!-- Generated by scripts/build_homepage_showcase.py; insert only inside HOMEPAGE_SHOWCASE markers. -->',
             '216 条目录分为 **72 项官网模板与片段、70 个控件、55 个代码注册项、19 个真人口播特效**，不同层级不合并成 216 套独立模板。按分类展开，点击画面或 Demo 链接查看完整演示。',
             '', '本地 GIF 是 **最多 3 秒、原速度、无声节选**，不是完整视频。官网项目使用官方预览图；演示、可下载状态、实际运行和本条成片验收分别核对。', '']
    for layer, title in LAYERS.items():
        group = [e for e in entries if e['layer'] == layer]
        categories = OrderedDict()
        for entry in group:
            categories.setdefault(entry['category_zh'], []).append(entry)
        lines.extend([f'<details{" open" if layer == "style" else ""}>',
                      f'<summary><strong>{html.escape(title)} · {counts[layer]} 项</strong></summary>', ''])
        for i, (category, members) in enumerate(categories.items()):
            # The approved B case stays first in its existing catalog order.
            lines.extend([f'<details{" open" if layer == "style" and i == 0 else ""}>',
                          f'<summary>{html.escape(category)} · {len(members)} 项</summary>', '',
                          table(members, assets), '', '</details>', ''])
        lines.extend(['</details>', ''])
    if catalog.get('previews'):
        lines.extend(['<details>', '<summary><strong>额外官方预告 · 不计入上述 216 项</strong></summary>', '',
                      '<p>官方标记 <code>previewOnly</code>／<code>coming-soon</code>，当前仅效果预告，不视为已开放下载或已在本机运行。</p>', '',
                      table(catalog['previews'], assets), '', '</details>', ''])
    return '\n'.join(lines)


def replace_showcase(readme_bytes, fragment):
    """Return a replacement only when the exact marker pair is unique and ordered."""
    start = b'<!-- HOMEPAGE_SHOWCASE:START -->'
    end = b'<!-- HOMEPAGE_SHOWCASE:END -->'
    if readme_bytes.count(start) != 1 or readme_bytes.count(end) != 1:
        raise ValueError('README must contain exactly one existing HOMEPAGE_SHOWCASE marker pair.')
    begin = readme_bytes.index(start) + len(start)
    finish = readme_bytes.index(end)
    if begin > finish:
        raise ValueError('README HOMEPAGE_SHOWCASE markers are out of order.')
    newline = b'\r\n' if b'\r\n' in readme_bytes else b'\n'
    body = fragment.replace('\r\n', '\n').strip().encode('utf-8').replace(b'\n', newline)
    return readme_bytes[:begin] + newline + newline + body + newline + newline + readme_bytes[finish:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=ROOT / '.runtime/ffmpeg/bin/ffmpeg.exe')
    parser.add_argument('--ffprobe', type=Path, default=ROOT / '.runtime/ffmpeg/bin/ffprobe.exe')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--write-readme', action='store_true', help='Explicitly replace only the unique existing HOMEPAGE_SHOWCASE marker section.')
    args = parser.parse_args()
    if args.verify_only and args.write_readme:
        parser.error('--verify-only and --write-readme cannot be combined')
    assert 1 <= args.jobs <= 4
    if not args.ffmpeg.is_file() or not args.ffprobe.is_file():
        raise FileNotFoundError('Provide existing FFmpeg and ffprobe executables; no runtime is installed by this helper.')
    catalog, snapshot = load(CATALOG), load(SNAPSHOT)
    assert len(catalog['entries']) == len({x['id'] for x in catalog['entries']}) == 216
    assert set(e['layer'] for e in catalog['entries']) == set(LAYERS)
    local = [e for e in catalog['entries'] if local_demo(e)]
    assert len(local) == 145
    previous = load(MANIFEST) if MANIFEST.is_file() else {}
    cached = {x['id']: x for x in previous.get('assets', [])}
    if args.verify_only:
        assert previous['catalog_sha256'] == digest(CATALOG)
        assert previous['snapshot_sha256'] == digest(SNAPSHOT)
        for entry in local:
            asset = cached[entry['id']]
            source = local_source(local_demo(entry))
            assert digest(source) == asset['source_sha256']
            assert digest(ROOT / asset['path']) == asset['sha256']
            video = next(s for s in probe(source, args.ffprobe)['streams'] if s['codec_type'] == 'video')
            validate_gif(ROOT / asset['path'], video, asset['frames'], args.ffmpeg, args.ffprobe)
        print(json.dumps({'verified_local_gifs': len(local), 'source_and_output_hashes': 'matched', 'remote_images_downloaded': 0}))
        return
    OUT.mkdir(parents=True, exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    assets = {}
    for entry in catalog['entries']:
        if not local_demo(entry):
            assets[entry['id']] = official_image(entry, snapshot)
    for entry in catalog.get('previews', []):
        assets[entry['id']] = official_image(entry, snapshot, preview=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {pool.submit(build_gif, e, args.ffmpeg, args.ffprobe, cached.get(e['id']), args.force): e['id'] for e in local}
        for n, future in enumerate(as_completed(pending), 1):
            record = future.result(); assets[record['id']] = record
            if n % 10 == 0 or n == len(local):
                print(json.dumps({'generated_and_verified': n, 'total_local': len(local)}), flush=True)
    ordered = [assets[e['id']] for e in catalog['entries'] + catalog.get('previews', [])]
    total = sum(a['bytes'] for a in ordered if a['kind'] == 'local_gif')
    manifest = {'schema_version': 1, 'built_at_utc': datetime.now(timezone.utc).isoformat(),
                'catalog': CATALOG.relative_to(ROOT).as_posix(), 'catalog_sha256': digest(CATALOG),
                'snapshot': SNAPSHOT.relative_to(ROOT).as_posix(), 'snapshot_sha256': digest(SNAPSHOT),
                'counts': {'catalog_entries':216, 'local_gifs':145, 'official_posters':71,
                           'extra_preview_posters':len(catalog.get('previews', [])), 'local_gif_bytes':total},
                'limits': {'max_gif_seconds':MAX_SECONDS, 'max_gif_bytes':MAX_BYTES, 'target_total_bytes':TOTAL_TARGET},
                'validation': {'full_decode':True, 'source_hashes_checked':True, 'timing_and_ratio_checked':True,
                               'continuous_watch':False, 'remote_image_network_check':False}, 'assets':ordered}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    fragment = make_fragment(catalog, assets)
    FRAGMENT.write_text(fragment, encoding='utf-8')
    if args.write_readme:
        readme = ROOT / 'README.md'
        original = readme.read_bytes()
        updated = replace_showcase(original, fragment)
        if readme.read_bytes() != original:
            raise RuntimeError('README changed while preparing its replacement; refusing to overwrite.')
        readme.write_bytes(updated)
    print(json.dumps({'manifest':str(MANIFEST), 'fragment':str(FRAGMENT), 'counts':manifest['counts'],
                      'below_25_mib_target':total < TOTAL_TARGET, 'readme_modified':args.write_readme}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
