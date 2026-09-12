"""Independent quality-first regressions. All media execution is mocked."""
import copy
import importlib
import json
import tempfile
import unittest
from contextlib import ExitStack, nullcontext
from pathlib import Path
from unittest.mock import patch

from talking_head_editor import workflow
from talking_head_editor.timeline import compile_clips, default_plan, validate_plan
from talking_head_editor.util import EditorError, atomic_json, file_hash, read_json

renderer = importlib.import_module('talking_head_editor.render')


class WorkflowReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.job = Path(self.tmp.name)
        plan = default_plan(5.5, 1)
        plan['semantic_review'] = {'status':'reviewed','evidence':'Synthetic semantic fixture only'}
        self.p = {'schema_version':1,'revision':1,'fixture':True,'plan':plan,
                  'source':{'path':'source.mp4','sha256':'source-hash','duration':5.5,
                            'probe':{'streams':[{'codec_type':'video','width':1920,'height':1080}]}},
                  'transcript':{'sha256':'transcript-hash'},'assets':{}}
        self.words = [{'id':'w001','text':'完整','start':.1,'end':.5}]

    def fake_ff(self, args, work, name, timeout=3600):
        Path(args[-1]).write_bytes(b'NOT PLAYABLE; mocked render artifact')
        return '', ''

    def render_mocks(self, stack):
        def fake_clip(job, p, c, words, aspect, style, scale, dimensions, **kw):
            self.assertEqual(words, [])
            self.assertEqual(p['plan']['overlays'], [])
            self.assertFalse(kw['include_ending'])
            target = job/'mock-clip.mp4'; target.write_bytes(b'clip fixture')
            return target, False

        def fake_captions(folder, cues, *args, **kwargs):
            (folder/'captions.srt').write_text('', encoding='utf8')
            (folder/'captions.ass').write_text('', encoding='utf8')

        def fake_concat(parts, target, work):
            target.write_bytes(b'concatenated fixture')

        patches = {
            'job_lock':lambda job: nullcontext(), 'load_job':lambda job: (self.job,self.p),
            'source_path':lambda *args: self.job/'source.mp4',
            'transcript':lambda *args: {'words':self.words},
            'render_audio':lambda *args: (self.job/'audio.wav',False),
            'finish_audio':lambda *args,**kw: self.job/'audio.wav',
            'render_clip':fake_clip, 'concatenate':fake_concat,
            'ff':self.fake_ff, 'write_captions':fake_captions,
            'append_keywords':lambda *args: None,
        }
        for name,value in patches.items():
            stack.enter_context(patch.object(renderer,name,side_effect=value))

    def test_rough_ignores_unfinished_picture_plan_and_preserves_latest_render(self):
        self.p['plan']['overlays'] = [{'id':'unfinished','clip_id':'c001','asset_id':'missing',
                                     'offset':0,'duration':2,'purpose':'not selected yet'}]
        self.p['plan']['visual_rhythm'] = {'enforce':True}
        before = copy.deepcopy(self.p)
        atomic_json(self.job/'latest-render.json',{'fingerprint':'existing-draft','complete':True})
        existing = (self.job/'latest-render.json').read_bytes()
        with ExitStack() as stack:
            self.render_mocks(stack)
            first = renderer.render(self.job,mode='rough')
            second = renderer.render(self.job,mode='rough')
        self.assertTrue(first['complete'])
        self.assertEqual(first['mode'],'rough')
        self.assertEqual(first['structure_fingerprint'],workflow.structure_fingerprint(self.p))
        self.assertEqual(first['ending_duration'],0)
        self.assertTrue(second['reused'])
        self.assertEqual(existing,(self.job/'latest-render.json').read_bytes())
        self.assertEqual(read_json(self.job/'latest-rough.json')['fingerprint'],first['fingerprint'])
        self.assertEqual(self.p,before)

    def test_rough_still_rejects_a_cut_through_a_spoken_word(self):
        self.p['plan']['clips'][0]['start'] = .3
        self.p['plan']['deletions'] = [{'start':0,'end':.3,'reason':'test invalid cut'}]
        with ExitStack() as stack:
            self.render_mocks(stack)
            with self.assertRaises(EditorError) as caught:
                renderer.render(self.job,mode='rough')
        self.assertEqual(caught.exception.code,'cut_inside_word')
        self.assertFalse((self.job/'latest-rough.json').exists())

    def test_misspelled_nested_execution_fields_are_rejected(self):
        effect = {'id':'k','kind':'keyword','clip_id':'c001','offset':1,'duration':1,
                  'text':'重点','purpose':'fixture emphasis','colour':'#E6AC55'}
        plan = copy.deepcopy(self.p['plan']); plan['visual_effects']=[effect]
        with self.assertRaises(EditorError): validate_plan(plan,5.5,self.words,{})
        overlay = {'id':'v','clip_id':'c001','offset':0,'duration':5.5,
                   'asset_id':'asset','asset_speeed':1,'purpose':'normal-speed broll'}
        asset = {'kind':'video','duration':10,'review':{'description':'frame fixture','evidence':'synthetic'},
                 'license':{'kind':'provided'}}
        plan = copy.deepcopy(self.p['plan']); plan['overlays']=[overlay]
        with self.assertRaises(EditorError): validate_plan(plan,5.5,self.words,{'asset':asset})

    def test_asset_speed_changes_source_interval_filters_and_cache(self):
        overlay = {'id':'v','clip_id':'c001','offset':0,'duration':5.5,
                   'asset_id':'asset','asset_speed':1,'source_start':.5,'purpose':'normal-speed broll'}
        self.p['plan']['overlays']=[overlay]
        self.p['assets']['asset']={'path':'asset.mp4','sha256':'asset-hash','kind':'video'}
        clip = compile_clips(self.p['plan']['clips'],1.1)[0]
        def fake_seal(path,key):
            atomic_json(str(path)+'.json',{'key':key,'sha256':file_hash(path)})
        with patch.object(renderer,'ff',side_effect=self.fake_ff) as ff, \
                patch.object(renderer,'seal',side_effect=fake_seal):
            normal,reused=renderer.render_clip(self.job,self.p,clip,[],'landscape',self.p['plan']['style'],.5)
            self.assertFalse(reused)
            filters=(normal.parent/'filters.txt').read_text(encoding='utf8')
            self.assertIn('trim=duration=5.0,setpts=(PTS-STARTPTS)/1,',filters)
            args=ff.call_args.args[0]
            asset_input=args.index(self.job/'asset.mp4')
            self.assertEqual(args[asset_input-5:asset_input-3],['-t',5.0])
            self.assertEqual(renderer.render_clip(self.job,self.p,clip,[],'landscape',self.p['plan']['style'],.5),(normal,True))
            self.p['plan']['overlays'][0]['asset_speed']=1.1
            accelerated,reused=renderer.render_clip(self.job,self.p,clip,[],'landscape',self.p['plan']['style'],.5)
            self.assertFalse(reused); self.assertNotEqual(normal,accelerated)
            self.assertIn('trim=duration=5.5,setpts=(PTS-STARTPTS)/1.1,',
                          (accelerated.parent/'filters.txt').read_text(encoding='utf8'))
            self.assertEqual(ff.call_count,2)

    def test_source_profile_is_bound_and_does_not_claim_listening(self):
        values=[0,.04,.08,.12]
        probe=self.p['source']['probe']['streams'][0]
        probe.update(color_transfer='smpte2084',sample_aspect_ratio='1:1',start_time='0')
        def response(*args,**kw):
            return json.dumps({'frames':[{'best_effort_timestamp_time':str(x)} for x in values]}),''
        with patch.object(workflow,'load_job',return_value=(self.job,self.p)), \
                patch('talking_head_editor.project.source_path',return_value=self.job/'source.mp4'), \
                patch('talking_head_editor.project.audit_source',return_value={'full_decode_pass':True}), \
                patch.object(workflow,'executable',return_value='MOCK-FFPROBE'), \
                patch.object(workflow,'run',side_effect=response) as run:
            first=workflow.source_profile(self.job)
            self.assertTrue(first['monotonic_pts']);self.assertTrue(first['hdr_requires_working_copy'])
            self.assertEqual(first['audio_listening'],'unverified')
            cached=workflow.source_profile(self.job);self.assertTrue(cached['reused'])
            self.assertEqual(run.call_count,1)
            self.p['source']['sha256']='new-source'
            values[:]=[0,.04,.02,.10]
            changed=workflow.source_profile(self.job)
            self.assertFalse(changed['monotonic_pts']);self.assertEqual(run.call_count,2)
            self.assertEqual(changed['source_sha256'],'new-source')

    def test_source_gate_blocks_hdr_or_nonmonotonic_timestamps(self):
        good={'source_sha256':self.p['source']['sha256'],'rule_version':workflow.RULE_VERSION,
              'full_decode_pass':True,'monotonic_pts':True,'hdr_requires_working_copy':False,
              'frame_count':100,'video_start':'0','audio_starts':['0'],'variable_frame_intervals':False}
        with patch.object(workflow,'load_job',return_value=(self.job,self.p)):
            for field in ('hdr_requires_working_copy','monotonic_pts','full_decode_pass'):
                bad={**good,field:field=='hdr_requires_working_copy'}
                atomic_json(self.job/'review/source-profile.json',bad)
                with self.subTest(field=field), patch.object(workflow,'source_profile',return_value=bad):
                    with self.assertRaises(EditorError):workflow.require_source_ready(self.job)
            atomic_json(self.job/'review/source-profile.json',good)
            with patch.object(workflow,'source_profile',return_value=good):workflow.require_source_ready(self.job)

    def packet(self):
        evidence=self.job/'research/evidence.txt';evidence.parent.mkdir(exist_ok=True)
        evidence.write_text('synthetic evidence fixture only',encoding='utf8')
        self.p['assets']={x:{'sha256':x+'-hash','kind':'video'} for x in ('actual','wrong')}
        self.p['plan']['overlays']=[{'id':'shot','clip_id':'c001','asset_id':'actual'}]
        return {'plan_fingerprint':workflow.plan_fingerprint(self.p),
                'brief':{x:'synthetic' for x in ('audience','goal','format','style','budget','delivery')},
                'editorial_units':[{'clip_id':'c001','role':'premise','meaning':'complete sentence',
                                    'context_check':'no new context','selection_reason':'fixture'}],
                'take_comparisons':[{'reason':'fixture'}],'uncertainties':[],
                'shots':[{'shot_id':'shot','need':'show object','selected_reason':'synthetic selected asset',
                          'candidates':[{'id':'choice','kind':'owned','observation':'frames','reason':'synthetic frame',
                                         'selected':True,'asset_id':'actual','sha256':'actual-hash'}]}],
                'evidence_files':[{'path':'research/evidence.txt'}]}

    def test_packet_selection_must_match_the_asset_used_by_its_shot(self):
        packet=self.packet()
        packet['shots'][0]['candidates'][0].update(asset_id='wrong',sha256='wrong-hash')
        with patch.object(workflow,'load_job',return_value=(self.job,self.p)):
            with self.assertRaises(EditorError):workflow.record_packet(self.job,packet)

    def test_packet_and_evidence_become_stale_after_changes(self):
        packet=self.packet()
        with patch.object(workflow,'load_job',return_value=(self.job,self.p)):
            result=workflow.record_packet(self.job,packet)
            self.assertTrue(result['packet_valid'])
            (self.job/'research/evidence.txt').write_text('changed evidence',encoding='utf8')
            self.assertFalse(workflow.workflow_status(self.job)['packet_valid'])
            self.p['plan']['clips'][0]['end']=5.0
            with self.assertRaises(EditorError) as caught:workflow.record_packet(self.job,packet)
            self.assertEqual(caught.exception.code,'workflow_stale')


if __name__ == '__main__':unittest.main()
