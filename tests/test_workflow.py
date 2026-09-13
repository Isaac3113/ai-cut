import copy
import tempfile
import unittest
from pathlib import Path
from talking_head_editor.workflow import rough_view, structure_fingerprint, caption_readability, record_packet, workflow_status
from talking_head_editor.timeline import default_plan, validate_plan
from talking_head_editor.motion import append_keywords
from talking_head_editor.visuals import write_captions
from talking_head_editor.process_visuals import frame,validate_spec
from talking_head_editor.util import EditorError,atomic_json,file_hash


class WorkflowTests(unittest.TestCase):
    def test_rough_is_derived_and_keeps_main_timing(self):
        p={'plan':default_plan(9,1),'source':{'sha256':'source'},'transcript':{'sha256':'words'}}
        p['plan'].update(music_asset_id='m',ending={'duration':3},overlays=[{'id':'asset'}],visual_effects=[{'id':'word'}])
        before=copy.deepcopy(p); result=rough_view(p)
        self.assertEqual(p,before)
        self.assertEqual(result['plan']['clips'],p['plan']['clips'])
        self.assertEqual(result['plan']['style']['playback_speed'],1.2)
        self.assertNotIn('ending',result['plan']);self.assertNotIn('music_asset_id',result['plan'])
        self.assertEqual(result['plan']['overlays'],[])
        self.assertEqual(structure_fingerprint(result),structure_fingerprint(p))
        changed=copy.deepcopy(p);changed['plan']['clips'][0]['end']=8
        self.assertNotEqual(structure_fingerprint(changed),structure_fingerprint(p))

    def test_unknown_execution_field_fails_instead_of_ignoring(self):
        plan=default_plan(5,0);plan['privacy_masks']=[{'box':[1,2,3,4]}]
        with self.assertRaises(EditorError) as caught:validate_plan(plan,5,[],{})
        self.assertEqual(caught.exception.code,'unsupported_plan_field')

    def test_normal_speed_broll_can_fill_accelerated_speech(self):
        p=default_plan(5.5,0)
        a={'v':{'kind':'video','duration':5,'review':{'description':'viewed','evidence':'actual frame'},'license':{'kind':'provided'}}}
        p['overlays']=[{'id':'o','clip_id':'c001','offset':0,'duration':5.5,'asset_speed':1,
                        'asset_id':'v','purpose':'same five seconds in output'}]
        validate_plan(p,5.5,[],a)
        p['overlays'][0].pop('asset_speed')
        with self.assertRaises(EditorError) as caught:validate_plan(p,5.5,[],a)
        self.assertEqual(caught.exception.code,'asset_too_short')

    def test_color_no_longer_removes_explicit_outline_and_motion_selects(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t);style=default_plan(3,0)['style'];write_captions(path,[],1920,1080,style)
            e={'kind':'keyword','offset':0,'duration':1.8,'text':'按行业定制','color':'#F0BE69',
               'outline':2,'animation':'settle','font_size':80,'bold':True,'x':.5,'y':.72}
            append_keywords(path/'captions.ass',[e],1.1,1920,1080,1)
            text=(path/'captions.ass').read_text(encoding='utf-8')
            self.assertIn(r'\bord2\b-1',text);self.assertIn(r'\fscx96',text)
            self.assertNotIn(r'\fscx118',text)

    def test_readability_flags_are_not_false_caption_approval(self):
        r=caption_readability([{'text':'这是一个过快的中文字幕示例','start':0,'end':.3},
                               {'text':'ordinary English caption','start':1,'end':3}])
        self.assertEqual(r['status'],'unverified');self.assertEqual(r['flagged'],1)
        self.assertIn('fast_chinese_reading',r['cues'][0]['flags'])

    def test_flow_frames_deterministic_and_conditions_visible(self):
        spec={'kind':'entry','title':'新客户先记录，再跟进','purpose':'未购买条件','duration':9,'events':[0,2,5]}
        validate_spec(spec)
        self.assertEqual(frame(spec,6,640,360).tobytes(),frame(spec,6,640,360).tobytes())
        self.assertNotEqual(frame(spec,1,640,360).tobytes(),frame(spec,6,640,360).tobytes())
        with self.assertRaises(EditorError): frame(spec,1,360,640)

    def test_codec_headroom_cannot_raise_audio(self):
        p=default_plan(5,0);p['style']['encode_headroom_db']=.2
        with self.assertRaises(EditorError):validate_plan(p,5,[],{})

    def test_global_caption_theme_uses_main_clip_speed_and_keeps_srt(self):
        from talking_head_editor.render import global_caption_themes
        clips=[{'id':'b','output_start':10.,'playback_speed':1.1}]
        plan={'overlays':[{'clip_id':'b','offset':1.1,'duration':2.2,'caption_theme':'dark'}]}
        themes=global_caption_themes(plan,clips)
        self.assertEqual(themes,[{'start':11.,'end':13.,'theme':'dark'}])
        with tempfile.TemporaryDirectory() as t:
            path=Path(t);style=default_plan(3,0)['style']
            cues=[{'start':10.,'end':14.,'lines':['同一行字幕'],'text':'同一行字幕','max_line_width':200}]
            write_captions(path,cues,1920,1080,style)
            original=(path/'captions.srt').read_bytes()
            write_captions(path,cues,1920,1080,style,theme_ranges=themes)
            self.assertEqual((path/'captions.srt').read_bytes(),original)
            self.assertIn('3D2F17',(path/'captions.ass').read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
