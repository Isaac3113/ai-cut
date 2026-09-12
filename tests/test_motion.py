import copy
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from talking_head_editor.timeline import default_plan, validate_plan, compile_clips
from talking_head_editor.motion import map_effects, rhythm_report, synthesize_sfx, write_sfx_track, append_keywords, continues_into_ending
from talking_head_editor.visuals import write_captions
from talking_head_editor.util import EditorError, atomic_json, file_hash
from talking_head_editor.render import render_clip


class MotionTests(unittest.TestCase):
    def effect(self, **extra):
        return {'id':'e1','clip_id':'c001','offset':1.1,'duration':.33,'purpose':'test cue','kind':'pop',**extra}

    def test_sfx_gain_is_capped_and_not_peak_normalized_after_gain(self):
        signal=synthesize_sfx('pop',.3,.05)
        self.assertAlmostEqual(float(abs(signal).max()),10**(-6/20)*.05,places=6)
        plan=default_plan(5,0);plan['sound_effects']=[self.effect(gain=.5)]
        with self.assertRaises(EditorError): validate_plan(plan,5,[],{})

    def test_effect_uses_same_speed_and_reorder_timeline(self):
        clips=compile_clips([{'id':'b','start':5,'end':7.2},{'id':'c001','start':0,'end':3.3}],1.1)
        e=map_effects({'sound_effects':[self.effect()]},clips,'sound_effects')[0]
        self.assertAlmostEqual(e['output_start'],3)
        self.assertAlmostEqual(e['output_duration'],.3)

    def test_more_than_five_seconds_without_visual_change_is_blocked(self):
        p=default_plan(12,0);p['visual_rhythm']={'enforce':True}
        with self.assertRaises(EditorError) as caught:validate_plan(p,12,[],{})
        self.assertEqual(caught.exception.code,'visual_rhythm_gap')
        p['visual_effects']=[self.effect(id='v1',kind='keyword',offset=4.4,duration=1.1,text='重点'), self.effect(id='v2',kind='keyword',offset=8.8,duration=1.1,text='流程')]
        clips=validate_plan(p,12,[],{})
        self.assertLessEqual(rhythm_report(p,clips)['max_gap_seconds'],5)

    def test_uninspected_crop_and_unowned_ending_are_blocked(self):
        p=default_plan(5,0);p['visual_effects']=[self.effect(kind='punch')]
        with self.assertRaises(EditorError):validate_plan(p,5,[],{})
        p['visual_effects']=[];p['ending']={'asset_id':'missing','duration':3,'purpose':'test'}
        with self.assertRaises(EditorError):validate_plan(p,5,[],{})

    def test_sound_cannot_cross_clip_or_stack_louder(self):
        p=default_plan(5,0);p['sound_effects']=[self.effect(offset=4.9)]
        with self.assertRaises(EditorError):validate_plan(p,5,[],{})
        clips=compile_clips(p['clips'],1.1)
        p['sound_effects']=[self.effect(),self.effect(id='s2')]
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(EditorError):write_sfx_track(p,clips,5,Path(t)/'fx.wav')

    def test_keyword_does_not_modify_spoken_srt(self):
        p=default_plan(5,0)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);write_captions(root,[],1920,1080,p['style'])
            before=(root/'captions.srt').read_bytes()
            append_keywords(root/'captions.ass',[self.effect(kind='keyword',text='重点')],1.1,1920,1080,1)
            self.assertEqual((root/'captions.srt').read_bytes(),before)
            self.assertIn(r'\t(0,140,\fscx118', (root/'captions.ass').read_text(encoding='utf-8-sig'))

    def test_contiguous_source_splits_do_not_count_as_visual_changes(self):
        plan = default_plan(12, 0)
        plan['clips'] = [
            {'id': f'c{i+1:03d}', 'start': i*4, 'end': (i+1)*4,
             'reason': 'Continuous original shot split only for bookkeeping'}
            for i in range(3)
        ]
        clips = compile_clips(plan['clips'], 1.1)
        report = rhythm_report(plan, clips)
        self.assertAlmostEqual(report['max_gap_seconds'], sum(c['output_duration'] for c in clips), places=5)
        self.assertGreater(report['max_gap_seconds'], 5)
        plan['visual_rhythm'] = {'enforce': True}
        with self.assertRaises(EditorError) as caught:
            validate_plan(plan, 12, [], {})
        self.assertEqual(caught.exception.code, 'visual_rhythm_gap')

    def test_keyword_near_edge_rejects_actual_text_overflow(self):
        plan = default_plan(5, 0)
        effect = self.effect(kind='keyword', text='客户跟进', x=.05, y=.5)
        plan['visual_effects'] = [effect]
        # The normalized anchor itself is legal; text geometry still must fit.
        validate_plan(plan, 5, [], {})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_captions(root, [], 1920, 1080, plan['style'])
            target = root/'captions.ass'
            before = target.read_bytes()
            with self.assertRaises(EditorError) as caught:
                append_keywords(target, [effect], 1.1, 1920, 1080, 1)
            self.assertEqual(caught.exception.code, 'keyword_position')
            self.assertEqual(target.read_bytes(), before)


    def test_continuous_ending_requires_matching_full_final_overlay(self):
        plan = default_plan(13.2, 0)
        plan['clips'] = [
            {'id': 'first', 'start': 0., 'end': 6.6},
            {'id': 'last', 'start': 6.6, 'end': 13.2},
        ]
        plan['ending'] = {'asset_id': 'avatar', 'source_start': 3.3, 'duration': 3}
        overlay = {'id': 'avatar-enter', 'clip_id': 'last', 'asset_id': 'avatar',
                   'mode': 'full', 'offset': 3.3, 'duration': 3.3, 'source_start': 0.}
        plan['overlays'] = [overlay]
        plan['visual_effects'] = [self.effect(id='cue', clip_id='first', kind='keyword',
                                            offset=4.4, duration=.33, text='重点')]
        clips = compile_clips(plan['clips'], 1.1)
        last = clips[-1]
        self.assertTrue(continues_into_ending(overlay, last, plan))
        default_full = {k: v for k, v in overlay.items() if k != 'mode'}
        self.assertTrue(continues_into_ending(default_full, last, plan))
        cases = [
            ('wrong_asset', {**overlay, 'asset_id': 'another'}, last, plan),
            ('pip', {**overlay, 'mode': 'pip'}, last, plan),
            ('banner', {**overlay, 'mode': 'banner'}, last, plan),
            ('nonlast', {**overlay, 'clip_id': 'first'}, clips[0], plan),
            ('clip_gap', {**overlay, 'offset': 3.1}, last, plan),
            ('source_gap', {**overlay, 'source_start': .1}, last, plan),
            ('source_overlap', {**overlay, 'source_start': -.1}, last, plan),
            ('no_ending', overlay, last, {k: v for k, v in plan.items() if k != 'ending'}),
        ]
        for name, candidate, clip, candidate_plan in cases:
            with self.subTest(case=name):
                self.assertFalse(continues_into_ending(candidate, clip, candidate_plan))

        body = sum(c['output_duration'] for c in clips)
        report = rhythm_report(plan, clips)
        # Same footage crossing the body/tail join produces no visible change.
        self.assertFalse(any(e['kind'] in ('ending', 'broll_out') and
                             abs(e['time'] - body) < .001 for e in report['events']))
        self.assertAlmostEqual(report['events'][-1]['time'], body + 3)
        self.assertEqual(report['events'][-1]['kind'], 'end')
        self.assertAlmostEqual(report['max_gap_seconds'], 6, places=5)

        preview = rhythm_report(plan, clips, include_ending=False)
        self.assertTrue(any(e['kind'] == 'broll_out' and abs(e['time'] - body) < .001
                            for e in preview['events']))
        self.assertAlmostEqual(preview['events'][-1]['time'], body)
        self.assertAlmostEqual(preview['max_gap_seconds'], 5, places=5)
        broken = copy.deepcopy(plan)
        broken['overlays'][0]['asset_id'] = 'another'
        broken_report = rhythm_report(broken, clips)
        self.assertTrue(any(e['kind'] == 'ending' and abs(e['time'] - body) < .001
                            for e in broken_report['events']))
        self.assertAlmostEqual(broken_report['max_gap_seconds'], 5, places=5)


    def test_preview_uses_fading_cache_even_when_full_ending_is_continuous(self):
        plan = default_plan(6.6, 0)
        plan['ending'] = {'asset_id': 'avatar', 'source_start': 3.3, 'duration': 3}
        plan['overlays'] = [{'id': 'avatar-enter', 'clip_id': 'c001', 'asset_id': 'avatar',
                             'mode': 'full', 'offset': 3.3, 'duration': 3.3, 'source_start': 0.}]
        clip = compile_clips(plan['clips'], 1.1)[0]
        project = {'source': {'path': 'source.mp4', 'sha256': 'source-fixture'},
                   'plan': plan,
                   'assets': {'avatar': {'path': 'avatar.mp4', 'sha256': 'avatar-fixture', 'kind': 'video'}}}

        def fake_ff(args, work, name, timeout=3600):
            # Not a playable file: exercise filter construction/cache receipts only.
            Path(args[-1]).write_bytes(b'mock media for cache test only')
            return '', ''

        def fake_seal(path, key):
            atomic_json(str(path) + '.json', {'key': key, 'sha256': file_hash(path)})

        with tempfile.TemporaryDirectory() as temporary, \
                patch('talking_head_editor.render.ff', side_effect=fake_ff) as ff_mock, \
                patch('talking_head_editor.render.seal', side_effect=fake_seal):
            job = Path(temporary)

            def run(candidate, include_ending):
                return render_clip(job, candidate, clip, [], 'landscape', plan['style'], .5,
                                   include_ending=include_ending)

            full, cached = run(project, True)
            self.assertFalse(cached)
            self.assertNotIn('fade=t=out:', (full.parent/'filters.txt').read_text(encoding='utf-8'))
            preview, cached = run(project, False)
            self.assertFalse(cached)
            self.assertNotEqual(full.parent.name, preview.parent.name)
            self.assertIn('fade=t=out:', (preview.parent/'filters.txt').read_text(encoding='utf-8'))
            same_preview, cached = run(project, False)
            self.assertTrue(cached)
            self.assertEqual(same_preview, preview)
            self.assertEqual(ff_mock.call_count, 2)

            # Without a tail, or with a gap, the legacy fading pixels are reusable.
            no_tail = copy.deepcopy(project)
            no_tail['plan'].pop('ending')
            self.assertEqual(run(no_tail, True), (preview, True))
            gap = copy.deepcopy(project)
            gap['plan']['ending']['source_start'] += .2
            self.assertEqual(run(gap, True), (preview, True))
            not_last = copy.deepcopy(project)
            not_last['plan']['clips'].append({'id': 'later', 'start': 6.6, 'end': 7.7})
            self.assertEqual(run(not_last, True), (preview, True))

            # A source-position edit must select different pixels and a different key.
            shifted = copy.deepcopy(project)
            shifted['plan']['overlays'][0]['source_start'] = .2
            shifted['plan']['ending']['source_start'] = 3.5
            shifted_path, cached = run(shifted, True)
            self.assertFalse(cached)
            self.assertNotIn(shifted_path.parent.name, {full.parent.name, preview.parent.name})
            self.assertNotIn('fade=t=out:', (shifted_path.parent/'filters.txt').read_text(encoding='utf-8'))
            self.assertEqual(ff_mock.call_count, 3)
