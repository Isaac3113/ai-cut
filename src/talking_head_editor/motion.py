"""Frame-timed visual emphasis, quiet independent SFX, and a registered ending."""
from __future__ import annotations

import math
import re
import wave
from pathlib import Path

import numpy as np

from .util import number, require, ident, inside, atomic_json
from .visuals import ass_time, ass_escape, ass_color, font, write_captions

RATE = 48000


def validate_motion(plan, clips, assets):
    by_id = {c['id']: c for c in clips}
    seen = set()
    for group in ('visual_effects', 'sound_effects'):
        events = plan.get(group, [])
        require(isinstance(events, list) and len(events) <= 500, 'motion_events', 'Use at most 500 explicit events')
        for e in events:
            ident(e['id'])
            require(e['id'] not in seen, 'motion_id', 'Effect IDs must be unique')
            seen.add(e['id'])
            require(e.get('clip_id') in by_id, 'motion_anchor', 'Effect must reference a retained clip')
            c = by_id[e['clip_id']]
            at = number(e.get('offset'), 'effect.offset')
            span = number(e.get('duration'), 'effect.duration', .08)
            require(at + span <= c['end'] - c['start'] + .001, 'motion_range', 'Effect must fit source clip')
            require(e.get('purpose', '').strip(), 'motion_purpose', 'Explain the spoken point and visible action')
            if group == 'sound_effects':
                require(e.get('kind') in ('tap', 'pop', 'swipe'), 'sfx_kind', 'Use tap/pop/swipe')
                require(number(e.get('gain', .05), 'sfx.gain') <= .05, 'sfx_gain', 'SFX linear gain must be at most 5 percent')
                require(span <= .7, 'sfx_duration', 'Keep accents short, at most 0.7 source seconds')
            else:
                require(e.get('kind') in ('punch', 'keyword'), 'visual_effect_kind', 'Use punch or keyword')
                if e['kind'] == 'punch':
                    require(e.get('target','presenter') in ('presenter','scene'), 'zoom_target', 'Zoom presenter or explicitly reviewed whole scene')
                    require(1 <= number(e.get('factor', 1.08), 'zoom.factor') <= 1.14, 'zoom_factor', 'Use a restrained 1..1.14 zoom')
                    require(e.get('review_evidence', '').strip(), 'zoom_review', 'Inspect face, hands and screen edges before zooming')
                else:
                    require(re.fullmatch(r'#[A-Fa-f0-9]{6}',e.get('color','#FFFFFF')), 'keyword_color', 'Use #RRGGBB emphasis color')
                    require(e.get('animation','pop') in ('pop','settle','fade'), 'keyword_animation', 'Use pop/settle/fade')
                    require(36 <= number(e.get('font_size',72),'keyword.font_size') <= 96, 'keyword_size', 'Use 36..96px emphasis')
                    require(number(e.get('outline',2),'keyword.outline') <= 4, 'keyword_outline', 'Use 0..4px outline independently of color')
                    require(isinstance(e.get('bold',False),bool),'keyword_weight','bold must be boolean')
                    text = e.get('text', '')
                    require(isinstance(text, str) and 0 < len(text.strip()) <= 24 and '\n' not in text, 'emphasis_text', 'Use a short, single-line keyword')
                for axis in ('x', 'y'):
                    require(.05 <= number(e.get(axis, .5), axis) <= .95, 'effect_position', 'Position must be inside the frame')
    for o in plan.get('overlays', []):
        values = o.get('motion_times', [])
        require(isinstance(values, list), 'motion_times', 'Internal visual actions need source-relative times')
        for value in values:
            require(number(value, 'motion_time') < o['duration'], 'motion_times', 'Visual action must be inside the overlay')
    ending = plan.get('ending')
    if ending:
        aid = ending.get('asset_id')
        require(aid in assets and assets[aid]['kind'] == 'video', 'ending_asset', 'Ending needs a registered video asset')
        a = assets[aid]
        require(a.get('review', {}).get('evidence') and a.get('review', {}).get('description'), 'ending_review', 'Inspect actual avatar and ending frames')
        require(a.get('license', {}).get('kind') == 'provided', 'ending_license', 'Use an owned ending made from user-provided footage')
        require(1 <= number(ending.get('duration'), 'ending.duration') <= 5, 'ending_duration', 'Append 1..5 output seconds')
        start = number(ending.get('source_start', 0), 'ending.source_start')
        require(start + ending['duration'] <= a['duration'] + .001, 'ending_range', 'Ending source is too short')
        require(ending.get('purpose', '').strip(), 'ending_purpose', 'Record original avatar source and ending purpose')
    if plan.get('visual_rhythm', {}).get('enforce'):
        report = rhythm_report(plan, clips)
        require(report['max_gap_seconds'] <= 5.001, 'visual_rhythm_gap', f"Visual gap exceeds 5s: {report['largest_gap']}")


def map_effects(plan, clips, field):
    by_id = {c['id']: c for c in clips}
    result = []
    for e in plan.get(field, []):
        if e['clip_id'] not in by_id:
            continue
        c = by_id[e['clip_id']]
        at = c['output_start'] + e['offset'] / c['playback_speed']
        length = min(e['duration'] / c['playback_speed'], c['output_start'] + c['output_duration'] - at)
        if length > 0:
            result.append({**e, 'output_start': at, 'output_duration': length})
    return sorted(result, key=lambda e: e['output_start'])


def continues_into_ending(overlay, clip, plan):
    """A full-frame final overlay may continue into the same registered asset."""
    ending = plan.get('ending')
    return bool(ending and plan.get('clips') and clip['id'] == plan['clips'][-1]['id']
                and overlay.get('mode', 'full') == 'full'
                and overlay.get('asset_id') == ending.get('asset_id')
                and abs(overlay['offset'] + overlay['duration'] - (clip['end']-clip['start'])) < .001
                and abs(overlay.get('source_start', 0) + overlay['duration']/clip.get('playback_speed', plan.get('style',{}).get('playback_speed',1))*overlay.get('asset_speed',clip.get('playback_speed', plan.get('style',{}).get('playback_speed',1))) - ending.get('source_start', 0)) < .001)


def rhythm_report(plan, clips, include_ending=True):
    events = [{'time': 0., 'kind': 'opening'}]
    by_id = {c['id']: c for c in clips}
    for o in plan.get('overlays', []):
        if o['clip_id'] not in by_id:
            continue
        c = by_id[o['clip_id']]
        for at, kind in [(o['offset'], 'broll_in'), (o['offset']+o['duration'], 'broll_out')] + [(o['offset']+x, 'object_action') for x in o.get('motion_times', [])]:
            if kind == 'broll_out' and include_ending and continues_into_ending(o, c, plan):
                continue
            if at <= c['end'] - c['start']:
                events.append({'time': c['output_start']+at/c['playback_speed'], 'kind': kind, 'id': o['id']})
    for e in map_effects(plan, clips, 'visual_effects'):
        events.append({'time': e['output_start'], 'kind': e['kind'], 'id': e['id']})
    body = sum(c['output_duration'] for c in clips)
    continuous_tail = include_ending and any(continues_into_ending(o, by_id[o['clip_id']], plan) for o in plan.get('overlays', []) if o['clip_id'] in by_id)
    if not continuous_tail:
        events.append({'time': body, 'kind': 'ending' if include_ending and plan.get('ending') else 'end'})
    if include_ending and plan.get('ending'):
        events.append({'time': body + plan['ending']['duration'], 'kind': 'end'})
    events.sort(key=lambda e: e['time'])
    gap = max(zip(events, events[1:]), key=lambda pair: pair[1]['time']-pair[0]['time'])
    return {'basis': 'renderable effects and reviewed B-roll/object actions; ordinary cuts alone do not count; inspect actual export separately',
            'max_gap_seconds': round(gap[1]['time']-gap[0]['time'], 6), 'largest_gap': [gap[0]['time'], gap[1]['time']], 'events': events}


def punch_filter(effects, speed, width, height, layer='presenter'):
    punches = [e for e in effects if e['kind'] == 'punch' and e.get('target','presenter') == layer]
    if not punches:
        return None
    terms = []
    # Focus stays consistent across a clip; avoid accidental abrupt pans.
    x, y = punches[0].get('x', .5), punches[0].get('y', .5)
    for e in punches:
        a, b = e['offset']/speed*30, (e['offset']+e['duration'])/speed*30
        amount = e.get('factor', 1.08)-1
        terms.append(f"if(between(on,{a:.6f},{b:.6f}),{amount:.6f}*max(0,min(1,(on-{a:.6f})/5))*max(0,min(1,({b:.6f}-on)/7)),0)")
    expression = 'min(1.14,1+' + '+'.join(terms) + ')'
    return f"zoompan=z='{expression}':x='(iw-iw/zoom)*{x}':y='(ih-ih/zoom)*{y}':d=1:s={width}x{height}:fps=30"


def append_keywords(path, effects, speed, width, height, scale):
    rows = []
    for e in effects:
        if e['kind'] != 'keyword':
            continue
        size = round(e.get('font_size',72 if width >= height else 56) * scale)
        require(font(size).getlength(e['text']) * 1.18 <= width*.86, 'keyword_overflow', 'Keyword would leave safe frame; shorten it')
        x, y = round(width*e.get('x', .5)), round(height*e.get('y', .72))
        half_width = font(size).getlength(e['text']) * 1.18 / 2
        half_height = size * 1.45 * 1.18 / 2
        require(x-half_width >= width*.04 and x+half_width <= width*.96 and y-half_height >= height*.04 and y+half_height <= height*.84, 'keyword_position', 'Emphasis would leave safe frame or overlap subtitle zone')
        tags = (fr'{{\an5\pos({x},{y})\fs{size}\b0\bord2\shad0\fscx82\fscy82'
                r'\t(0,140,\fscx118\fscy118)\t(140,300,\fscx100\fscy100)\fad(35,160)}')
        if e.get('animation') == 'settle':
            tags = (fr'{{\an5\pos({x},{y})\fs{size}\b0\shad0\fscx96\fscy96'
                    r'\t(0,220,\fscx100\fscy100)\fad(80,160)}')
        elif e.get('animation') == 'fade':
            tags = fr'{{\an5\pos({x},{y})\fs{size}\b0\shad0\fad(120,160)}}'
        color_tag = ('{' + r'\1c' + ass_color(e.get('color','#FFFFFF')) + '&'
                     + fr"\bord{e.get('outline',2)}\b{-1 if e.get('bold') else 0}" + '}')
        rows.append(f"Dialogue: 2,{ass_time(e['offset']/speed)},{ass_time((e['offset']+e['duration'])/speed)},Default,,0,0,0,,{tags}{color_tag}{ass_escape(e['text'])}")
    if rows:
        with Path(path).open('a', encoding='utf-8') as output:
            output.write('\n'+'\n'.join(rows)+'\n')


def synthesize_sfx(kind, duration, gain=.05):
    """Original procedural cues, pre-levelled to -6 dBFS peak, then <=5% gain."""
    require(kind in ('tap', 'pop', 'swipe') and 0 <= gain <= .05, 'sfx_gain', 'Invalid SFX type/gain')
    n = max(1, round(duration*RATE)); t = np.arange(n)/RATE
    if kind == 'swipe':
        rng = np.random.default_rng(90211)
        noise = rng.normal(size=n)
        signal = np.convolve(noise, np.ones(23)/23, mode='same') * np.sin(np.pi*np.arange(n)/n)**2
    else:
        frequency = 780 if kind == 'tap' else 430
        chirp = np.sin(2*np.pi*(frequency*t-170*t*t))
        signal = (chirp + .18*np.sin(2*np.pi*frequency*1.5*t))*np.exp(-t/(.034 if kind == 'tap' else .060))
        signal *= np.minimum(1, t/.006)
    signal *= np.minimum(1, (duration-t)/.025)
    peak = np.max(np.abs(signal))
    return (signal / peak * (10**(-6/20)) * gain).astype(np.float32) if peak else signal.astype(np.float32)


def write_sfx_track(plan, clips, duration, target):
    output = np.zeros(round(duration*RATE), dtype=np.float32)
    events = map_effects(plan, clips, 'sound_effects')
    last_end = -1.
    for e in events:
        require(e['output_start'] >= last_end-.001, 'sfx_overlap', 'Do not stack accents into a louder sound')
        signal = synthesize_sfx(e['kind'], e['output_duration'], e.get('gain', .05))
        at = round(e['output_start']*RATE)
        usable = min(len(signal), len(output)-at)
        if usable > 0:
            output[at:at+usable] += signal[:usable]
        last_end = e['output_start'] + e['output_duration']
    stereo = np.repeat(output[:,None], 2, axis=1)
    with wave.open(str(target), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(np.round(stereo*32767).astype('<i2').tobytes())
    peak = float(np.max(np.abs(output)))
    return {'events':events, 'linear_gain_max':max((e.get('gain',.05) for e in events),default=0),
            'pre_gain_peak_dbfs':-6, 'track_peak_dbfs':20*math.log10(peak) if peak else None,
            'source':'original procedural tap/pop/swipe, no third-party audio', 'listened':False}


def finish_audio(job, plan, clips, body_audio, work, ending_duration, ff, music=None):
    body = sum(c['output_duration'] for c in clips); total=body+ending_duration
    if not plan.get('sound_effects') and not ending_duration:
        return body_audio
    sfx = work/'sfx-only.wav'
    report = write_sfx_track(plan, clips, total, sfx)
    # Add a quiet original tap at the start of the tail only when explicitly requested.
    output = work/'finished-mix.wav'
    filters = f'[0:a]apad,atrim=duration={total:.9f}[body];[body][1:a]amix=inputs=2:duration=first:normalize=0[out]'
    inputs = ['-i',body_audio,'-i',sfx]
    if ending_duration and music:
        inputs += ['-ss',body % music['duration'],'-stream_loop','-1','-i',inside(job,music['path'])]
        filters = (f'[0:a]apad,atrim=duration={total:.9f}[body];'
                   f'[2:a]atrim=duration={ending_duration},asetpts=PTS-STARTPTS,loudnorm=I=-18:TP=-2:LRA=11,'
                   f'volume={plan.get("style",{}).get("music_gain_db",-35.020599913279625)}dB,'
                   f'afade=t=in:d=0.12,afade=t=out:st={max(0,ending_duration-1.2)}:d=1.2,'
                   'aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,'
                   f'adelay={round(body*1000)}:all=1[tail];'
                   '[body][1:a][tail]amix=inputs=3:duration=first:normalize=0[out]')
    ff([*inputs,'-filter_complex',filters,'-map','[out]','-t',total,'-ar',RATE,'-ac',2,'-c:a','pcm_s16le',output],work,'sfx-mix')
    report.update(body_audio=str(body_audio), output=str(output), ending_duration_seconds=ending_duration, ending_audio='quiet original BGM with fade' if ending_duration and music else 'silence',
                  post_mix_normalization=False, note='Voice/BGM base not attenuated; no automatic gain after SFX addition.')
    atomic_json(work/'sfx-report.json',report)
    return output


def render_ending(job, plan, work, dimensions, scale, ff):
    ending=plan['ending'];asset=plan['_ending_asset']
    width,height=[round(v*scale/2)*2 for v in dimensions]
    duration=round(ending['duration']*30)/30
    target=work/'ending.mp4'
    ff(['-ss',ending.get('source_start',0),'-i',inside(job,asset['path']),'-t',duration,
        '-vf',f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30',
        '-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
        '-video_track_timescale','90000','-movie_timescale','90000',target],work,'ending-render')
    return target
