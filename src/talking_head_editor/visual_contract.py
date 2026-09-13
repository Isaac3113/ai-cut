"""Deterministic brand/PIP evidence checks. No renderer or subjective quality claims."""
from __future__ import annotations
import copy
import hashlib
import math
from pathlib import Path

DEFAULT_SPEED = 1.2


def _interval(item):
    a, b = item['from_frame'], item['to_frame']
    if not isinstance(a, int) or not isinstance(b, int) or a < 0 or b <= a:
        raise ValueError('Expected a positive integer-frame interval')
    return a, b


def retime_speech(segments, speed=DEFAULT_SPEED, fps=30, start_frame=0):
    """Always derive duration from source bounds; repeated 1.2x is idempotent."""
    if not math.isfinite(speed) or not .5 <= speed <= 2 or fps <= 0:
        raise ValueError('Expected 0.5..2x absolute speed and positive fps')
    result = []
    cursor = start_frame
    for original in segments:
        item = copy.deepcopy(original)
        seconds = item['source_end'] - item['source_start']
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('Missing or invalid immutable source bounds')
        frames = math.ceil(seconds / speed * fps - 1e-7)
        item.update(from_frame=cursor, to_frame=cursor+frames, speed=speed)
        cursor += frames
        result.append(item)
    return result


def plan_presenter(segments, visuals, fps=30):
    """Intersect final insert ranges with final speech; never make a second timeline."""
    result = []
    for visual in visuals:
        va, vb = _interval(visual)
        for speech in segments:
            sa, sb = _interval(speech)
            a, b = max(va, sa), min(vb, sb)
            if a >= b:
                continue
            speed = speech.get('speed', (speech['source_end']-speech['source_start'])/((sb-sa)/fps))
            result.append({
                'id': f"pip-{visual['id']}-{speech['id']}", 'visual_id': visual['id'],
                'speech_id': speech['id'], 'asset_id': speech['asset_id'],
                'from_frame': a, 'to_frame': b,
                'source_start': speech['source_start']+(a-sa)/fps*speed,
                'source_end': min(speech['source_end'], speech['source_start']+(b-sa)/fps*speed),
                'speed': speed, 'media_type': 'video', 'shape': 'circle', 'muted': True,
            })
    return result


def _uncovered(start, end, intervals):
    cursor = start
    gaps = []
    for a, b in sorted(intervals):
        a, b = max(start, a), min(end, b)
        if b <= a:
            continue
        if a > cursor:
            gaps.append([cursor, a])
        cursor = max(cursor, b)
    if cursor < end:
        gaps.append([cursor, end])
    return gaps


def _overlap(a, b):
    return (a['x'] < b['x']+b['width'] and b['x'] < a['x']+a['width'] and
            a['y'] < b['y']+b['height'] and b['y'] < a['y']+a['height'])


def audit_contract(contract, expected_speed=DEFAULT_SPEED):
    """Audit normalized official item/config evidence, not intended placements.

    The caller retains original inspect responses alongside the normalized input.
    Structural pass cannot certify a logo's pixels, human identity, crop or lip sync.
    """
    errors, pending, checks = [], [], []
    if contract.get('schema_version') != 1:
        raise ValueError('Expected visual-contract schema_version=1')
    fps = contract['fps']
    duration = contract['duration_frames']
    canvas = contract['canvas']
    if not math.isfinite(expected_speed) or not .5 <= expected_speed <= 2:
        raise ValueError('Expected 0.5..2x absolute speed')
    if fps <= 0 or duration <= 0:
        raise ValueError('Invalid timeline fps/duration')
    speech = contract['speech_segments']
    evidence = contract.get('evidence_sources', [])
    if not evidence:
        pending.append('actual editor snapshot/inspect evidence is not bound')
    for record in evidence:
        path = Path(record['path'])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            errors.append('editor evidence missing or hash mismatch')
    if not speech:
        errors.append('missing speech source segments')
    for s in speech:
        a, b = _interval(s)
        if not all(math.isfinite(s[x]) for x in ('source_start','source_end')) or s['source_end'] <= s['source_start']:
            raise ValueError('Invalid speech source range')
        if b > duration:
            errors.append('speech outside timeline: '+s['id'])
        expected_frames = (s['source_end']-s['source_start'])/expected_speed*fps
        if abs((b-a)-expected_frames) > 1.001:
            errors.append('absolute speech speed mismatch: '+s['id'])
        if 'speed' in s and abs(s['speed']-expected_speed) > .00001:
            errors.append('explicit speech speed mismatch: '+s['id'])
    pips = contract['pip_segments']
    captions = contract.get('caption_regions', [])
    if not captions:
        pending.append('actual caption bounds are not provided; PIP collision not verified')
    for left, right in zip(sorted(pips,key=lambda p:p['from_frame']), sorted(pips,key=lambda p:p['from_frame'])[1:]):
        if left['to_frame'] > right['from_frame']:
            errors.append('overlapping duplicate presenter circles')
    for p in pips:
        pa, pb = _interval(p)
        if not all(math.isfinite(p[x]) for x in ('source_start','source_end')) or p['source_end'] <= p['source_start']:
            raise ValueError('Invalid PIP source range')
        matches = [s for s in speech if s['from_frame'] <= pa and s['to_frame'] >= pb
                   and s['asset_id'] == p['asset_id']]
        if len(matches) != 1:
            errors.append('PIP must match one original speech segment: '+p['id'])
        else:
            s = matches[0]
            speed = s.get('speed', expected_speed)
            start = s['source_start']+(pa-s['from_frame'])/fps*speed
            end = min(s['source_end'], s['source_start']+(pb-s['from_frame'])/fps*speed)
            if abs(p['source_start']-start) > speed/fps+.002 or abs(p['source_end']-end) > speed/fps+.002:
                errors.append('PIP source clock mismatch: '+p['id'])
        if p.get('media_type') != 'video' or p.get('shape') != 'circle' or p.get('muted') is not True:
            errors.append('PIP must be moving, circular and muted: '+p['id'])
        r = p.get('bounds')
        if not r:
            errors.append('PIP needs actual inspected bounds: '+p['id'])
            continue
        w, h = canvas['width'], canvas['height']
        if not all(math.isfinite(r[x]) for x in ('x','y','width','height')):
            raise ValueError('Invalid PIP bounds')
        if (abs(r['width']-r['height']) > 2 or min(r['width'],r['height']) <= 0 or
            r['x'] < 0 or r['y'] < 0 or r['x']+r['width'] > w or r['y']+r['height'] > h or
            r['y']+r['height']/2 < h*.55 or r['width'] > min(w,h)*.3 or
            not (r['x']+r['width'] <= w*.4 or r['x'] >= w*.6)):
            errors.append('PIP must be a small lower-left/right circle inside canvas: '+p['id'])
        for caption in captions:
            ca, cb = _interval(caption)
            if pa < cb and ca < pb and _overlap(r, caption['bounds']):
                errors.append('PIP overlaps caption region: '+p['id'])
                break
    for visual in contract['full_screen_visuals']:
        va, vb = _interval(visual)
        if vb > duration:
            errors.append('visual outside timeline: '+visual['id'])
        if not visual.get('purpose') or not visual.get('action'):
            errors.append('full-screen visual lacks semantic purpose/object action: '+visual['id'])
        # Full-screen visuals overlapping actual speech require continuous PIP.
        required = [(max(va,s['from_frame']),min(vb,s['to_frame'])) for s in speech
                    if s['from_frame'] < vb and va < s['to_frame']]
        coverage = []
        for a,b in required:
            coverage.extend(_uncovered(a,b,[_interval(p) for p in pips]))
        checks.append({'visual_id':visual['id'], 'missing_pip_frames':coverage})
        if coverage:
            errors.append('full-screen spoken visual missing PIP coverage: '+visual['id'])
    brand = contract['brand']
    if brand.get('status') == 'pending_logo':
        pending.append('company logo and palette are awaiting supplied artwork; brand not verified')
    elif brand.get('status') != 'ready':
        errors.append('brand status must be ready or pending_logo')
    else:
        logo = Path(brand.get('logo_path',''))
        if not logo.is_file() or hashlib.sha256(logo.read_bytes()).hexdigest() != brand.get('logo_sha256'):
            errors.append('supplied logo missing or hash mismatch')
        colors = {v.upper() for v in brand.get('palette',{}).values()}
        if len(colors) < 2:
            errors.append('brand requires inspected logo palette and readable companion color')
        bindings = brand.get('palette_bindings',[])
        required = {'keywords','cards','arrows','cover','ending'}
        if not required.issubset({b['target'] for b in bindings}):
            errors.append('brand palette bindings missing from one or more output components')
        for binding in bindings:
            if not binding.get('colors') or any(c.upper() not in colors for c in binding['colors']):
                errors.append('component uses undeclared brand color: '+binding['target'])
        watermarks = brand.get('watermarks',[])
        if _uncovered(0,duration,[_interval(w) for w in watermarks]):
            errors.append('logo watermark does not cover the full export')
        for watermark in watermarks:
            opacity = watermark.get('opacity',0)
            if not .08 <= opacity <= .12 and not (0 < opacity <= .25 and watermark.get('contrast_adjustment')):
                errors.append('logo opacity needs 8-12% baseline or recorded contrast adjustment')
            if watermark.get('preserve_aspect') is not True:
                errors.append('logo aspect preservation not recorded')
    return {'schema_version':1,'structural_pass':not errors,'ready_for_brand_delivery':not errors and not pending,
            'expected_speed':expected_speed,'errors':errors,'pending':pending,'pip_coverage':checks,
            'not_proven':['rendered logo visibility and matching palette pixels','actual moving circle mask and face crop',
                          'visual relevance and continuous viewing','human listening and lip/caption sync']}
