import copy
import unittest

from talking_head_editor.timeline import DEFAULT_STYLE, default_plan, mapped_words, validate_plan
from talking_head_editor.util import EditorError
from talking_head_editor.visuals import caption_cues


class CaptionBreaks(unittest.TestCase):
    def setUp(self):
        self.words = [{"id": f"w{i}", "text": text, "start": .1 + i*.22, "end": .29 + i*.22}
                      for i,text in enumerate("客户在哪一步系统知道")]
        self.plan = default_plan(3, 0)

    def test_explicit_boundaries_preserve_source_and_output_time(self):
        untouched = copy.deepcopy(self.words)
        original_clips = validate_plan(self.plan, 3, self.words, {})
        original_words = mapped_words(self.words, original_clips)
        self.plan["caption_break_after"] = ["w5", "w9"]
        clips = validate_plan(self.plan, 3, self.words, {})
        marked = mapped_words(self.words, clips, breaks=self.plan["caption_break_after"])
        # Audio uses these same source intervals/frame durations; none have changed.
        self.assertEqual(clips, original_clips)
        self.assertEqual([{k:v for k,v in w.items() if k != "caption_break_after"} for w in marked], original_words)
        self.assertEqual(self.words, untouched)
        for width, height, scale in ((960, 540, .5), (540, 960, .5), (1080, 1920, 1)):
            cues = caption_cues(marked, width, height, DEFAULT_STYLE, scale)
            self.assertEqual([c["text"] for c in cues], ["客户在哪一步", "系统知道"])
            self.assertAlmostEqual(cues[0]["end"], original_words[5]["end"])
            self.assertAlmostEqual(cues[1]["start"], original_words[6]["start"])

    def test_old_call_and_explicit_empty_list_are_identical(self):
        clips = validate_plan(self.plan, 3, self.words, {})
        old = mapped_words(self.words, clips)
        self.assertEqual(old, mapped_words(self.words, clips, None, []))
        self.assertTrue(all("caption_break_after" not in w for w in old))
        self.assertEqual(len(caption_cues(old, 960, 540, DEFAULT_STYLE, .5)), 1)

    def test_invalid_and_duplicate_word_ids_are_rejected(self):
        for value in (["unknown"], ["w1", "w1"], "w1", None, [None], [{}]):
            with self.subTest(value=value):
                self.plan["caption_break_after"] = value
                with self.assertRaises(EditorError) as caught:
                    validate_plan(self.plan, 3, self.words, {})
                self.assertEqual(caught.exception.code, "caption_break_after")

    def test_explicit_break_does_not_disable_duration_or_width_guardrails(self):
        words = [{"id": f"long{i}", "clip_id": "c", "text": "客户", "start": i*.5, "end": i*.5+.4}
                 for i in range(15)]
        words[-1]["caption_break_after"] = True
        cues = caption_cues(words, 540, 960, DEFAULT_STYLE, .5)
        self.assertGreater(len(cues), 1)
        self.assertTrue(all(c["end"]-c["start"] <= 3.2 and len(c["lines"]) <= 2 for c in cues))
        self.assertEqual([wid for c in cues for wid in c["word_ids"]], [w["id"] for w in words])


if __name__ == "__main__":
    unittest.main()
