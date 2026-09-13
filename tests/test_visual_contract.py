import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from talking_head_editor.visual_contract import audit_contract, plan_presenter, retime_speech
from talking_head_editor.timeline import default_plan, validate_plan


class VisualContractTests(unittest.TestCase):
    def fixture(self, root):
        logo=Path(root)/'logo.png'; logo.write_bytes(b'fixture supplied logo; pixel review separate')
        evidence=Path(root)/'inspect.json'; evidence.write_text('{"calibration": true}')
        speech=[{'id':'a','asset_id':'source','from_frame':30,'to_frame':330,'source_start':10,'source_end':22,'speed':1.2},
                {'id':'b','asset_id':'source','from_frame':330,'to_frame':630,'source_start':40,'source_end':52,'speed':1.2}]
        visuals=[{'id':'flow','from_frame':270,'to_frame':390,'purpose':'Explain assignment','action':'Card moves to assigned column'}]
        pips=plan_presenter(speech,visuals)
        for p in pips:p['bounds']={'x':48,'y':650,'width':240,'height':240}
        palette={'primary':'#47B4D0','text':'#153340'}
        return {'schema_version':1,'fps':30,'duration_frames':720,'canvas':{'width':1920,'height':1080},
                'evidence_sources':[{'path':str(evidence),'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}],
                'speech_segments':speech,'full_screen_visuals':visuals,'pip_segments':pips,
                'caption_regions':[{'from_frame':30,'to_frame':630,'bounds':{'x':250,'y':910,'width':1420,'height':100}}],
                'brand':{'status':'ready','logo_path':str(logo),'logo_sha256':hashlib.sha256(logo.read_bytes()).hexdigest(),
                         'palette':palette,'palette_bindings':[{'target':x,'colors':['#47B4D0']} for x in ['keywords','cards','arrows','cover','ending']],
                         'watermarks':[{'id':'logo','from_frame':0,'to_frame':720,'opacity':.1,'preserve_aspect':True}]}}

    def test_new_default_and_absolute_retime_are_idempotent(self):
        p=default_plan(12,0)
        self.assertEqual(p['style']['playback_speed'],1.2)
        self.assertEqual(validate_plan(p,12,[],{})[0]['frames'],300)
        source=[{'id':'a','asset_id':'source','source_start':10,'source_end':22,'from_frame':0,'to_frame':328,'speed':1.1}]
        before=copy.deepcopy(source)
        once=retime_speech(source,start_frame=30)
        self.assertEqual(source,before)
        self.assertEqual(once,retime_speech(once,start_frame=30))
        self.assertEqual(once[0]['to_frame'],330)

    def test_pip_splits_at_actual_source_cut_and_stays_on_source_clock(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t)
            self.assertEqual([(p['from_frame'],p['to_frame']) for p in c['pip_segments']],[(270,330),(330,390)])
            self.assertAlmostEqual(c['pip_segments'][0]['source_start'],19.6)
            self.assertAlmostEqual(c['pip_segments'][1]['source_start'],40)
            self.assertTrue(audit_contract(c)['ready_for_brand_delivery'])

    def test_pip_missing_frame_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); c['pip_segments'][0]['to_frame']-=1
            result=audit_contract(c)
            self.assertFalse(result['structural_pass'])
            self.assertEqual(result['pip_coverage'][0]['missing_pip_frames'],[[329,330]])

    def test_still_wrong_source_clock_and_duplicate_sound_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); p=c['pip_segments'][0]
            p.update(media_type='image',muted=False,source_start=0,shape='rounded_rectangle')
            result=audit_contract(c)
            self.assertFalse(result['structural_pass'])
            self.assertTrue(any('clock' in e for e in result['errors']))
            self.assertTrue(any('moving, circular and muted' in e for e in result['errors']))

    def test_pip_over_caption_and_wrong_corner_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t)
            c['pip_segments'][0]['bounds']={'x':750,'y':830,'width':240,'height':240}
            result=audit_contract(c)
            self.assertTrue(any('caption' in e for e in result['errors']))
            self.assertTrue(any('lower-left/right' in e for e in result['errors']))

    def test_logo_pending_does_not_claim_brand_delivery(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); c['brand']={'status':'pending_logo'}
            result=audit_contract(c)
            self.assertTrue(result['structural_pass'])
            self.assertFalse(result['ready_for_brand_delivery'])
            self.assertTrue(result['pending'])

    def test_wrong_logo_palette_and_loud_watermark_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); b=c['brand']
            b['logo_sha256']='0'*64
            b['palette_bindings'][0]['colors']=['#FFD545']
            b['watermarks'][0]['opacity']=.8
            result=audit_contract(c)
            self.assertEqual(len(result['errors']),3,result['errors'])

    def test_multiplied_1_32_and_missing_full_watermark_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t)
            c['speech_segments'][0]['speed']=1.32
            c['brand']['watermarks'][0]['from_frame']=1
            result=audit_contract(c)
            self.assertTrue(any('speed' in e for e in result['errors']))
            self.assertTrue(any('full export' in e for e in result['errors']))

    def test_no_extra_pip_for_keywords_on_presenter_or_silent_ending(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); c['full_screen_visuals']=[]; c['pip_segments']=[]
            self.assertTrue(audit_contract(c)['ready_for_brand_delivery'])
            c['full_screen_visuals']=[{'id':'ending','from_frame':630,'to_frame':720,'purpose':'End','action':'Portrait fades in'}]
            self.assertTrue(audit_contract(c)['ready_for_brand_delivery'])

    def test_missing_actual_evidence_or_caption_bounds_stays_pending(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); c.pop('evidence_sources'); c['caption_regions']=[]
            result=audit_contract(c)
            self.assertFalse(result['ready_for_brand_delivery'])
            self.assertEqual(len(result['pending']),2)

    def test_nonfinite_clock_and_duplicate_pip_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            c=self.fixture(t); c['speech_segments'][0]['source_end']=float('nan')
            with self.assertRaises(ValueError):audit_contract(c)
            c=self.fixture(t); c['pip_segments'].append(copy.deepcopy(c['pip_segments'][0]))
            self.assertIn('overlapping duplicate presenter circles',audit_contract(c)['errors'])
