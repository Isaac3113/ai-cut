"""Package already-reviewed social copy/covers; never generate or certify their meaning."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

from PIL import Image


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def format_copy(text):
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    if not paragraphs:
        raise ValueError('Empty copy')
    if any('```' in line or '\x00' in line for line in paragraphs):
        raise ValueError('Copy must contain plain publication text, without code fences')
    return '\n\n'.join('\n'.join(paragraphs[i:i + 3])
                       for i in range(0, len(paragraphs), 3)) + '\n'


def check_copy(text, platform):
    if text != format_copy(text):
        raise ValueError('Copy must have a blank line after each three short paragraphs')
    if platform == 'Facebook':
        pattern = r'^\s*(?:[AID]\s*[-—:：]\s*)?(?:AIDA|ADDA|Attention|Interest|Desire|Action)\b'
        if any(re.match(pattern, line.strip('*# '), re.I) for line in text.splitlines()):
            raise ValueError('Facebook copy contains framework labels')


def ratio_value(value):
    try:
        width, height = (float(x) for x in value.split(':'))
        if width <= 0 or height <= 0:
            raise ValueError
        return width / height
    except (ValueError, ZeroDivisionError):
        raise ValueError('Ratio must be positive width:height') from None


def cover(data, expected_ratio):
    with Image.open(io.BytesIO(data)) as picture:
        picture.load()
        if picture.format not in {'PNG', 'JPEG'}:
            raise ValueError('Cover must be a decoded PNG or JPEG')
        width, height = picture.size
        if width / height <= 0 or abs(width / height / expected_ratio - 1) > 0.02:
            raise ValueError('Cover ratio differs from the selected platform ratio')
        return {'width': width, 'height': height,
                'extension': '.png' if picture.format == 'PNG' else '.jpg'}


def copy_markdown(copies):
    return '# 平台文案 · 一键复制\n\n每个文本框右上角可复制；框内只有发布内容。\n\n' + ''.join(
        f'## {name}\n\n```text\n{text}```\n\n' for name, text in copies.items())


def build(out, transcript, video, facebook_copy, facebook_cover,
          xiaohongshu_copy, xiaohongshu_cover, evidence, facebook_ratio='16:9', *,
          xiaohongshu_landscape_cover, xiaohongshu_ratio='3:4'):
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Output exists; preserve it and build into a new directory')
    transcript = Path(transcript)
    body = transcript.read_text(encoding='utf-8-sig')
    if not body.strip() or re.search(r'\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->', body):
        raise ValueError('Use the final plain transcript TXT, not SRT or an empty file')
    # Complete preflight, including the video and evidence, before creating output.
    source_hashes = {'transcript_sha256': file_sha(transcript), 'video_sha256': file_sha(video)}
    if Path(video).stat().st_size == 0:
        raise ValueError('Video is empty')
    evidence_data = Path(evidence).read_bytes()
    if not evidence_data.decode('utf-8-sig').strip():
        raise ValueError('Provide the actual editorial/prompt review record')
    if xiaohongshu_ratio not in {'3:4', '9:16'}:
        raise ValueError('Xiaohongshu portrait ratio must be 3:4 or 9:16')
    prepared = {'制作依据.md': evidence_data}
    copies, images = {}, {}
    for platform, draft, image_path, ratio in (
        ('Facebook', facebook_copy, facebook_cover, ratio_value(facebook_ratio)),
        ('小红书', xiaohongshu_copy, xiaohongshu_cover, ratio_value(xiaohongshu_ratio)),
    ):
        text = format_copy(Path(draft).read_text(encoding='utf-8-sig'))
        check_copy(text, platform)
        image = Path(image_path).read_bytes()
        info = cover(image, ratio)
        copies[platform] = text
        images[platform] = {**info, 'expected_ratio': ratio}
        prepared[f'{platform}/文案.txt'] = text.encode('utf-8')
        prepared[f'{platform}/封面{info["extension"]}'] = image
    landscape = Path(xiaohongshu_landscape_cover).read_bytes()
    landscape_info = cover(landscape, 4 / 3)
    images['小红书_4比3横版'] = {**landscape_info, 'expected_ratio': 4 / 3}
    prepared[f'小红书/封面_4比3横版{landscape_info["extension"]}'] = landscape
    prepared['一键复制.md'] = copy_markdown(copies).encode('utf-8')
    manifest = {
        'schema_version': 2, 'workflow_rules': '0.2.7', 'sources': source_hashes,
        'files': {name: {'sha256': sha(data), 'bytes': len(data)} for name, data in prepared.items()},
        'covers': images, 'technical_status': 'passed',
        'editorial_record': '制作依据.md',
        'not_certified_by_this_tool': ['copy_facts_and_persuasion', 'cover_identity_and_text',
                                      'video_decode_and_full_watch_listen', 'publishing_or_engagement'],
    }
    prepared['交付清单.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    out.mkdir(parents=True, exist_ok=False)
    for name, data in prepared.items():
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as target:
            target.write(data)
    return audit(out, transcript, video)


def audit(out, transcript, video, allow_legacy=False):
    out = Path(out).resolve()
    manifest = json.loads((out / '交付清单.json').read_text(encoding='utf-8'))
    version = manifest['schema_version']
    if version not in {1, 2}:
        raise ValueError('Unsupported social-delivery schema')
    if version == 1 and not allow_legacy:
        raise ValueError('Legacy package needs the 4:3 cover; use allow_legacy only for historical audit')
    if version == 2 and manifest.get('workflow_rules') != '0.2.7':
        raise ValueError('Unexpected workflow rules for social-delivery schema 2')
    if manifest['sources'] != {'transcript_sha256': file_sha(transcript), 'video_sha256': file_sha(video)}:
        raise ValueError('Stale delivery: transcript or video has changed')
    expected = {'制作依据.md', '一键复制.md'}
    for platform in ('Facebook', '小红书'):
        extension = manifest['covers'][platform]['extension']
        if extension not in {'.png', '.jpg'}:
            raise ValueError('Unexpected cover extension')
        expected.update({f'{platform}/文案.txt', f'{platform}/封面{extension}'})
    if version == 2:
        landscape_info = manifest['covers'].get('小红书_4比3横版', {})
        extension = landscape_info.get('extension')
        if extension not in {'.png', '.jpg'}:
            raise ValueError('Missing or invalid Xiaohongshu 4:3 cover metadata')
        expected.add(f'小红书/封面_4比3横版{extension}')
    if set(manifest['files']) != expected:
        raise ValueError('Manifest must contain all required deliverables and supporting records')
    for name, item in manifest['files'].items():
        path = (out / name).resolve()
        if not path.is_relative_to(out) or not path.is_file():
            raise ValueError('Missing or external delivery file: ' + name)
        data = path.read_bytes()
        if sha(data) != item['sha256'] or len(data) != item['bytes']:
            raise ValueError('Delivery file differs from receipt: ' + name)
    copies = {}
    for platform in ('Facebook', '小红书'):
        copies[platform] = (out / platform / '文案.txt').read_text(encoding='utf-8')
        check_copy(copies[platform], platform)
        info = manifest['covers'][platform]
        data = (out / platform / ('封面' + info['extension'])).read_bytes()
        actual = cover(data, info['expected_ratio'])
        if any(actual[key] != info[key] for key in actual):
            raise ValueError('Cover metadata differs from receipt')
        if platform == '小红书':
            allowed = (3 / 4,) if version == 1 else (3 / 4, 9 / 16)
            if info['expected_ratio'] not in allowed:
                raise ValueError('Unexpected Xiaohongshu portrait ratio')
            cover(data, info['expected_ratio'])
    if version == 2:
        info = manifest['covers']['小红书_4比3横版']
        if info.get('expected_ratio') != 4 / 3:
            raise ValueError('Xiaohongshu landscape cover must be 4:3')
        data = (out / '小红书' / ('封面_4比3横版' + info['extension'])).read_bytes()
        actual = cover(data, 4 / 3)
        if any(actual[key] != info[key] for key in actual):
            raise ValueError('Landscape cover metadata differs from receipt')
    if (out / '一键复制.md').read_text(encoding='utf-8') != copy_markdown(copies):
        raise ValueError('Copy blocks differ from platform TXT files')
    return {'directory': str(out), 'schema_version': version,
            'deliverable_count': 5 if version == 2 else 4,
            'current_workflow_complete': version == 2,
            'five_deliverables': 'present' if version == 2 else 'legacy_missing_4:3',
            'hashes_layout_images_copy_blocks': 'passed',
            'not_certified_by_this_tool': manifest['not_certified_by_this_tool']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for action in ('build', 'audit'):
        command = commands.add_parser(action)
        for name in ('out', 'transcript', 'video'):
            command.add_argument('--' + name, type=Path, required=True)
        if action == 'build':
            for name in ('facebook-copy', 'facebook-cover', 'xiaohongshu-copy', 'xiaohongshu-cover',
                         'xiaohongshu-landscape-cover', 'evidence'):
                command.add_argument('--' + name, type=Path, required=True)
            command.add_argument('--facebook-ratio', default='16:9')
            command.add_argument('--xiaohongshu-ratio', choices=['3:4', '9:16'], default='3:4')
        else:
            command.add_argument('--allow-legacy', action='store_true',
                                 help='Audit historical schema 1 files without claiming current completeness')
    args = vars(parser.parse_args())
    action = args.pop('command')
    print(json.dumps((build if action == 'build' else audit)(**args), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
