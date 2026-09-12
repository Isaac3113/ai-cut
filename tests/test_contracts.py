import copy
import unittest

from talking_head_editor.timeline import validate_plan, mapped_words, default_plan, gaps, compile_clips
from talking_head_editor.asr import timestamp_words
from talking_head_editor.quality import validate_review, REVIEW_CATEGORIES
from talking_head_editor.util import EditorError, inside
from talking_head_editor.visuals import caption_cues


class Contracts(unittest.TestCase):
    def setUp(self):
        self.words=[{"id":"w1","text":"不是","start":1.,"end":1.5},
                    {"id":"w2","text":"RM100。","start":2.,"end":2.8},
                    {"id":"w3","text":"如果","start":5.,"end":5.4},
                    {"id":"w4","text":"API","start":5.5,"end":6.}]
        self.plan=default_plan(10,1)
        self.plan["style"]["playback_speed"]=1
    def expect(self,code,fn):
        with self.assertRaises(EditorError) as caught: fn()
        self.assertEqual(caught.exception.code,code)
    def test_cut_inside_negation_rejected(self):
        self.plan["clips"][0]["start"]=1.2
        self.expect("cut_inside_word",lambda:validate_plan(self.plan,10,self.words,{}))
    def test_missing_deletion_ledger(self):
        self.plan["clips"][0]["start"]=3
        self.expect("unlogged_deletion",lambda:validate_plan(self.plan,10,self.words,{}))
    def test_reorder_and_frame_padding_keep_word_mapping(self):
        clips=[{"id":"later","start":4.9,"end":6.11,"reason":"complete conditional"},
               {"id":"earlier","start":.9,"end":2.9,"reason":"complete negation"}]
        self.plan.update(clips=clips,deletions=[{"start":a,"end":b,"reason":"test gap"} for a,b in gaps(clips,10)])
        compiled=validate_plan(self.plan,10,self.words,{})
        mapped=mapped_words(self.words,compiled)
        self.assertEqual([x["text"] for x in mapped],["如果","API","不是","RM100。"])
        self.assertAlmostEqual(mapped[2]["start"],37/30+.1)
    def test_intentional_repetition_not_automatically_deleted(self):
        repeated=[{"id":"a","start":1.,"end":1.5,"text":"非常"},{"id":"b","start":1.6,"end":2.,"text":"非常"}]
        self.assertEqual(len(mapped_words(repeated,validate_plan(self.plan,10,repeated,{}))),2)
    def test_split_chinese_conditions_are_flagged(self):
        from talking_head_editor.timeline import critical_words
        words=[{"text":x,"id":str(i)} for i,x in enumerate("如果可以，可能不需要。")]
        self.assertEqual("".join(w["text"] for w in critical_words(words)),"如果可能不")
    def test_repeated_source_interval_rejected(self):
        self.plan["clips"].append({"id":"two","start":0,"end":2,"reason":"bad duplicate"})
        self.expect("overlapping_source",lambda:validate_plan(self.plan,10,[],{}))
    def test_safe_portrait_default_and_cover_review(self):
        validate_plan(self.plan,10,self.words,{})
        self.plan["clips"][0]["layouts"]={"portrait":{"fit":"cover"}}
        self.expect("crop_review",lambda:validate_plan(self.plan,10,self.words,{}))
    def test_paid_and_unreviewed_material_blocked(self):
        self.plan["overlays"]=[{"id":"o","clip_id":"c001","offset":3,"duration":1,"purpose":"illustrate","asset_id":"a"}]
        a={"kind":"image","sha256":"abc","license":{"kind":"paid","url":"https://example.com/license"},"source_url":"https://example.com/item"}
        self.expect("asset_not_reviewed",lambda:validate_plan(self.plan,10,self.words,{"a":a}))
        a["review"]={"description":"test image","evidence":"test annotation"}
        self.expect("paid_approval_required",lambda:validate_plan(self.plan,10,self.words,{"a":a}))
    def test_missing_asset_blocked(self):
        self.plan["overlays"]=[{"id":"o","clip_id":"c001","offset":3,"duration":1,"purpose":"illustrate","asset_id":"missing"}]
        self.expect("missing_asset",lambda:validate_plan(self.plan,10,self.words,{}))
    def test_music_provenance(self):
        self.plan["music_asset_id"]="a"
        a={"kind":"audio","license":{"kind":"free"},"review":{"evidence":"listened"}}
        self.expect("music_provenance",lambda:validate_plan(self.plan,10,self.words,{"a":a}))
    def test_no_invented_timestamps(self):
        self.expect("alignment_mismatch",lambda:timestamp_words("今天API",[[0,100],[100,200]]))
    def test_mixed_language_and_punctuation_alignment(self):
        self.assertEqual([w["text"] for w in timestamp_words("今天 API，不是100。",[[i*100,(i+1)*100] for i in range(6)])],
                         ["今","天","API，","不","是","100。"])
    def test_path_escape(self):
        self.expect("unsafe_path",lambda:inside("C:/sandbox","../escape"))
    def test_subtitle_wrap(self):
        from talking_head_editor.timeline import DEFAULT_STYLE
        words=[{"id":f"w{i}","text":x,"start":i*.15,"end":i*.15+.14,"clip_id":"c"} for i,x in enumerate("数字100不是保证回报，必须保留上下文和限定条件。")]
        for width,height in ((1920,1080),(1080,1920)):
            cues=caption_cues(words,width,height,DEFAULT_STYLE)
            self.assertTrue(all(len(c["lines"])<=2 and c["max_line_width"]<=width*.84 for c in cues))
    def test_review_requires_evidence_and_three_point_sync(self):
        r={"fingerprint":"f","expected_duration":10,"files":{"portrait":{}}}
        q={"variants":{"portrait":{"detections":[]}}}
        review={"fingerprint":"f","reviewer":"unit-test","variants":{"portrait":{"checks":{c:{"passed":True,"evidence":"fixture"} for c in REVIEW_CATEGORIES},"detector_dispositions":[],"timing_checkpoints":[]}}}
        self.expect("timing_checkpoints",lambda:validate_review(review,q,r))
        review["variants"]["portrait"]["timing_checkpoints"]=[{"output_time":t,"error_ms":30,"evidence":"fixture only"} for t in (1,5,9)]
        validate_review(review,q,r)
        review["variants"]["portrait"]["timing_checkpoints"][1]["error_ms"]=250
        self.expect("timing_error",lambda:validate_review(review,q,r))


if __name__=="__main__": unittest.main()
