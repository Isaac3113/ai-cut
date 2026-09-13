"""Read-only checks of a captured official ChatCut timeline; never certify taste/listening."""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path


def audit(snapshot, expected_speed=1.2):
    """Check voice-paired source clips; silent cover/ending items need no speech rate."""
    expected_speed = float(expected_speed)
    if not math.isfinite(expected_speed) or expected_speed <= 0:
        raise ValueError("expected_speed must be positive and finite")
    errors = []
    state = snapshot['state']
    fps = state['fps']
    if state['canvas'] != {'width': 1920, 'height': 1080} or fps != 30:
        errors.append('expected source 16:9 1080p30')
    timeline = snapshot['timeline']
    if timeline.get('totalEntries') != len(timeline['entries']):
        errors.append('incomplete timeline snapshot; paginate before audit')
    items = [x for x in timeline['entries'] if x['kind'] == 'item']
    video = sorted((x for x in items if x['trackId'] == snapshot['videoTrackId']), key=lambda x: x['fromFrame'])
    voice = [x for x in items if x['trackId'] == snapshot['voiceTrackId']]
    end = 0
    for item in video:
        interval = item['timelineRange']
        if interval['fromFrame'] != end or interval['toFrame'] <= end:
            errors.append('primary video gap/overlap/nonpositive duration: ' + item['id'])
        end = interval['toFrame']
    if end != state['durationInFrames']:
        errors.append('primary video does not cover entire export')
    for audio in voice:
        same = [v for v in video if v['timelineRange'] == audio['timelineRange'] and v.get('sourceRange') == audio.get('sourceRange')]
        if len(same) != 1:
            errors.append('voice has no unique matching video source range: ' + audio['id'])
        source = audio.get('sourceRange')
        if not source:
            errors.append('missing source range: ' + audio['id'])
            continue
        seconds = (audio['timelineRange']['toFrame'] - audio['fromFrame']) / fps
        rate = (source['endSeconds'] - source['startSeconds']) / seconds
        if abs(rate - expected_speed) > .002:
            errors.append('speech playback rate drift: ' + audio['id'])
    if not voice:
        errors.append('missing independent voice track')
    captions = snapshot['captions']
    if captions.get('hasMore') or not captions.get('total'):
        errors.append('missing/incomplete captions')
    if re.search(r'"overflow"\s*:\s*true', captions.get('text', '')):
        errors.append('caption overflow reported')
    source = Path(snapshot['sourcePath'])
    if not source.is_file():
        errors.append('source file missing')
    elif hashlib.sha256(source.read_bytes()).hexdigest() != snapshot['sourceSha256']:
        errors.append('source hash mismatch')
    return {'structural_pass': not errors, 'expected_speed': expected_speed, 'errors': errors, 'video_items': len(video), 'voice_items': len(voice), 'duration_frames': end, 'captions': captions['total'], 'not_proven': ['continuous watch', 'listening', 'manual 200ms sync', 'semantic material fit', 'pixel-level visual cadence', 'audio track gain (requires inspect_item and export analysis)']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--expected-speed', type=float, default=1.2,
                        help='Absolute speech speed relative to the source; default is the current creator rule; pass 1.1 explicitly for historical exports')
    args = parser.parse_args()
    if not math.isfinite(args.expected_speed) or args.expected_speed <= 0:
        parser.error('--expected-speed must be positive and finite')
    result = audit(json.loads(args.snapshot.read_text(encoding='utf-8-sig')), expected_speed=args.expected_speed)
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        if args.out.exists():
            raise SystemExit('Refusing to overwrite prior audit evidence')
        args.out.write_text(content, encoding='utf-8')
    print(content)
    raise SystemExit(0 if result['structural_pass'] else 1)
