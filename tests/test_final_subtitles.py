import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "final_subtitles", Path(__file__).parents[1] / "scripts/export_final_subtitles.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FinalSubtitleTests(unittest.TestCase):
    def cards(self):
        return [
            {"id": "first", "start_frame": 0, "end_frame": 70, "text": "客户进来，"},
            {"id": "second", "start_frame": 70, "end_frame": 101, "text": "follow up"},
            {"id": "third", "start_frame": 103, "end_frame": 131, "text": "before\n不是购买。"},
        ]

    def test_final_cover_offset_shared_boundary_and_spoken_words(self):
        srt, plain, normalized, rate = module.prepare(
            self.cards(), 30, offset_frames=30, duration_frames=161,
            paragraphs=[["first", "second", "third"]])
        self.assertIn("00:00:01,000 --> 00:00:03,333", srt)
        self.assertIn("00:00:03,333 --> 00:00:04,367", srt)
        self.assertEqual(normalized[1]["end_ms"], 4367)
        self.assertEqual(normalized[2]["start_ms"], 4433)
        self.assertEqual(normalized[-1]["end_ms"], 5367)
        self.assertEqual(plain, "客户进来， follow up before 不是购买。\n")
        self.assertNotIn("-->", plain)
        self.assertNotIn("first", plain)
        self.assertEqual("".join(plain.split()), "".join("".join(c["text"].split()) for c in self.cards()))

    def test_rational_rate_rounds_absolute_boundaries_without_cumulative_drift(self):
        cards = [{"id": n, "start_frame": n, "end_frame": n + 1, "text": "字"} for n in range(3000)]
        srt, plain, normalized, rate = module.prepare(cards, "30000/1001")
        self.assertEqual(normalized[-1]["end_ms"], 100100)
        self.assertTrue(all(a["end_ms"] == b["start_ms"] for a, b in zip(normalized, normalized[1:])))
        self.assertEqual(len(plain.splitlines()), 3000)

    def test_no_implicit_speed_or_second_offset(self):
        cards = [{"id": "a", "start_frame": 30, "end_frame": 2760, "text": "按最终 1.2 倍时间。"}]
        srt, plain, normalized, rate = module.prepare(cards, 30, duration_frames=2850)
        self.assertEqual(normalized[0]["start_ms"], 1000)
        self.assertEqual(normalized[0]["end_ms"], 92000)
        self.assertIn("1.2", plain)

    def test_invalid_frames_overlap_or_ids_rejected(self):
        changes = [
            {"start_frame": -1}, {"start_frame": 1.5}, {"start_frame": True},
            {"end_frame": 0}, {"text": ""}, {"text": "a\n\nb"}, {"id": False},
        ]
        for changed in changes:
            with self.subTest(changed=changed):
                cards = self.cards(); cards[0].update(changed)
                with self.assertRaises(ValueError): module.prepare(cards, 30)
        for changed in ({"start_frame": 69}, {"id": "first"}):
            cards = self.cards(); cards[1].update(changed)
            with self.assertRaises(ValueError): module.prepare(cards, 30)

    def test_duration_and_paragraphs_cannot_silently_drop_or_reorder_speech(self):
        with self.assertRaises(ValueError): module.prepare(self.cards(), 30, offset_frames=30, duration_frames=160)
        for paragraphs in ([["first", "second"]], [["second", "first", "third"]],
                           [["first", "second", "third", "third"]], [[]]):
            with self.subTest(paragraphs=paragraphs):
                with self.assertRaises(ValueError): module.prepare(self.cards(), 30, paragraphs=paragraphs)
        for fps in ("nan", "0", "-1", "1/0"):
            with self.assertRaises(ValueError): module.prepare(self.cards(), fps)

    def test_export_hashes_preserve_history_and_validation_before_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source = directory / "cards.json"
            source.write_text(json.dumps(self.cards(), ensure_ascii=False), encoding="utf-8-sig")
            paths = module.export(source, directory / "final", 30, duration_frames=131)
            manifest = json.loads(Path(paths["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["caption_count"], 3)
            self.assertEqual(manifest["input_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            for kind in ("txt", "srt"):
                self.assertEqual(manifest["files"][kind]["sha256"], hashlib.sha256(Path(paths[kind]).read_bytes()).hexdigest())
            self.assertIn("actual_video_caption_match", manifest["not_verified"])
            with self.assertRaises(FileExistsError): module.export(source, directory / "final", 30)
            with self.assertRaises(ValueError): module.export(source, directory / "invalid", 30, duration_frames=130)
            self.assertFalse((directory / "invalid_字幕.srt").exists())


if __name__ == "__main__":
    unittest.main()
