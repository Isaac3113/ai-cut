import unittest
from talking_head_editor.timeline import default_plan, validate_plan, mapped_words, output_formats
from talking_head_editor.util import EditorError
from talking_head_editor.render import preview_plan

class SpeedAndFormats(unittest.TestCase):
    def test_common_speed_maps_reordered_words_and_frame_padding(self):
        p=default_plan(10,0)
        p.update(clips=[{"id":"b","start":5,"end":8.31,"reason":"later complete unit"},{"id":"a","start":1,"end":3.2,"reason":"earlier unit"}],
                 deletions=[{"start":0,"end":1,"reason":"prep"},{"start":3.2,"end":5,"reason":"retake"},{"start":8.31,"end":10,"reason":"tail"}])
        words=[{"id":"a","text":"不是","start":1.2,"end":2.2},{"id":"b","text":"如果","start":5.22,"end":6.32}]
        clips=validate_plan(p,10,words,{})
        self.assertEqual([c["frames"] for c in clips],[91,60])
        mapped=mapped_words(words,clips)
        self.assertAlmostEqual(mapped[0]["start"],.2)
        self.assertAlmostEqual(mapped[0]["end"],1.2)
        self.assertAlmostEqual(mapped[1]["start"],91/30+.2/1.1)
        self.assertAlmostEqual(sum(c["output_duration"] for c in clips),151/30)
    def test_source_rotation_sar_and_explicit_both(self):
        p=default_plan(10,0)
        v={"codec_type":"video","width":1920,"height":1080}
        info={"streams":[v]}
        self.assertEqual(output_formats(p,info),{"landscape":(1920,1080)})
        v["side_data_list"]=[{"rotation":90}]
        self.assertEqual(output_formats(p,info),{"portrait":(1080,1920)})
        v.update(width=1440,height=1080,sample_aspect_ratio="4:3",side_data_list=[])
        self.assertEqual(output_formats(p,info),{"landscape":(1920,1080)})
        v.update(width=1080,height=1080,sample_aspect_ratio="1:1")
        self.assertEqual(output_formats(p,info),{"source":(1080,1080)})
        p["output_formats"]=["landscape","portrait"]
        self.assertEqual(len(output_formats(p,info)),2)
    def test_old_plan_missing_speed_remains_one_times(self):
        p=default_plan(10,0); del p["style"]["playback_speed"]
        self.assertEqual(validate_plan(p,10,[],{})[0]["frames"],300)
    def test_flow_cannot_run_past_spoken_interval(self):
        p=default_plan(10,0)
        p["overlays"]=[{"id":"o","clip_id":"c001","offset":1,"duration":3,"purpose":"test","graphic":{"type":"flow","title":"流程","nodes":["进入","跟进"],"step_times":[0,3]}}]
        with self.assertRaises(EditorError) as c: validate_plan(p,10,[],{})
        self.assertEqual(c.exception.code,"flow_timing")
    def test_grouped_english_keeps_original_time_and_word_provenance(self):
        p=default_plan(5,0)
        words=[{"id":"a","text":"Web","start":1.1,"end":1.5},{"id":"b","text":"inar","start":1.5,"end":2.2}]
        p["caption_groups"]=[{"word_ids":["a","b"],"text":"Webinar"}]
        p["correction_evidence"]="Adjacent ASR fragments in calibration"
        clips=validate_plan(p,5,words,{})
        mapped=mapped_words(words,clips,groups=p["caption_groups"])
        self.assertEqual(len(mapped),1)
        self.assertEqual(mapped[0]["text"],"Webinar")
        self.assertEqual(mapped[0]["source_word_ids"],["a","b"])
        self.assertAlmostEqual(mapped[0]["start"],1)
        self.assertAlmostEqual(mapped[0]["end"],2)
    def test_partial_english_group_cannot_be_cut_into_new_term(self):
        p=default_plan(5,0)
        words=[{"id":"a","text":"Web","start":1.1,"end":1.5},{"id":"b","text":"inar","start":1.5,"end":2.2}]
        p["clips"][0]["end"]=1.5
        p["deletions"]=[{"start":1.5,"end":5,"reason":"fixture"}]
        p["caption_groups"]=[{"word_ids":["a","b"],"text":"Webinar"}]
        p["correction_evidence"]="fixture"
        with self.assertRaises(EditorError) as c: validate_plan(p,5,words,{})
        self.assertEqual(c.exception.code,"caption_group_cut")
    def test_preview_limit_is_output_time(self):
        c=preview_plan([{"id":"a","start":0,"end":60}],[],maximum=45,speed=1.1)
        self.assertAlmostEqual(c[0]["output_duration"],45)

if __name__=="__main__": unittest.main()
