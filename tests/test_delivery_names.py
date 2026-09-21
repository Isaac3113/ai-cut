import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("delivery_names", ROOT/"scripts/delivery_names.py")
names = importlib.util.module_from_spec(spec); spec.loader.exec_module(names)
spec2 = importlib.util.spec_from_file_location("final_subtitles_names", ROOT/"scripts/export_final_subtitles.py")
subs = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(subs)

class DeliveryNamesTests(unittest.TestCase):
    def test_distinct_roles_speed_dots_and_idempotence(self):
        stem = Path("folder/客户流程_1比1_1.44倍")
        paths = names.delivery_paths(stem)
        self.assertEqual(paths["video"].name, "客户流程_1比1_1.44倍_视频.mp4")
        self.assertEqual(paths["txt"].name, "客户流程_1比1_1.44倍_字幕.txt")
        for suffix in ("_视频", "_字幕", "_视频_字幕"):
            self.assertEqual(names.delivery_paths(str(stem)+suffix), paths)
        self.assertEqual(str(names.typed_stem("字幕", "字幕")), "字幕")
    def test_reject_bad_stems_before_writes(self):
        for s in ("bad?.mp4", "title.mp4", "name ", "name.", "foo:bar"):
            with self.subTest(s=s), self.assertRaises(ValueError):
                names.delivery_paths(s)
    def test_real_export_names_hashes_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); stem = root/"课题_1.44倍"
            cards = root/"cards.json"
            cards.write_text(json.dumps([dict(id="1",start_frame=30,end_frame=60,text="不是全部客户。")]),encoding="utf-8")
            out = subs.export(cards, stem, 30, duration_frames=90)
            self.assertEqual(Path(out["txt"]),names.delivery_paths(stem)["txt"])
            self.assertEqual(Path(out["srt"]),names.delivery_paths(stem)["srt"])
            self.assertEqual(Path(out["txt"]).read_text(encoding="utf-8"), "不是全部客户。\n")
            with self.assertRaises(FileExistsError): subs.export(cards, str(stem)+"_字幕", 30)
            with self.assertRaises(ValueError): names.audit_delivery(stem)
            video=names.delivery_paths(stem)["video"]; video.touch()
            with self.assertRaises(ValueError): names.audit_delivery(stem)
            video.write_bytes(b"filename-test-only-not-a-video")
            report=names.audit_delivery(stem)
            self.assertIn("video_decode",report["not_verified"])
            self.assertEqual(report["files"]["txt"]["sha256"],json.loads(Path(out["manifest"]).read_text(encoding="utf-8"))["files"]["txt"]["sha256"])
    def test_cli_from_other_working_directory(self):
        with tempfile.TemporaryDirectory() as d:
            out=subprocess.run([sys.executable,str(ROOT/"scripts/delivery_names.py"),"--output-stem","客户_1.44倍"],cwd=d,capture_output=True,encoding="utf-8",env={**__import__("os").environ,"PYTHONUTF8":"1"},check=True)
            self.assertEqual(json.loads(out.stdout)["video"],"客户_1.44倍_视频.mp4")

if __name__=="__main__": unittest.main()
