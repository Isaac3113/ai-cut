import copy
import time
import unittest

from PIL import Image, ImageChops, ImageStat

from talking_head_editor.render import portrait_title_image, render_clip
from talking_head_editor.timeline import DEFAULT_STYLE, default_plan, validate_plan
from talking_head_editor.util import ROOT, EditorError, executable, file_hash, probe, run


class Layouts(unittest.TestCase):
    def setUp(self):
        self.plan = default_plan(1, 0)

    def test_old_layouts_and_opt_in_do_not_change_timing(self):
        original = validate_plan(self.plan, 1, [], {})
        for layout in ({"fit": "contain"}, {"fit": "cover", "review_evidence": "test only"},
                       {"fit": "contain", "background": "blur", "title": "客户走到哪一步？"}):
            self.plan["clips"][0]["layouts"] = {"portrait": layout}
            compiled = validate_plan(self.plan, 1, [], {})
            self.assertEqual([(c["frames"], c["output_start"]) for c in compiled],
                             [(c["frames"], c["output_start"]) for c in original])

    def test_invalid_layout_extensions_are_rejected(self):
        cases = [([], "layout"), ({"portrait": "contain"}, "layout"),
                 ({"portrait": {"background": "unknown"}}, "layout_background"),
                 ({"portrait": {"fit": "cover", "background": "blur"}}, "layout_background"),
                 ({"landscape": {"title": "title"}}, "layout_title"),
                 ({"portrait": {"fit": "cover", "title": "title"}}, "layout_title"),
                 ({"portrait": {"title": " "}}, "layout_title"),
                 ({"portrait": {"title": 42}}, "layout_title"),
                 ({"portrait": {"title": "a" * 81}}, "layout_title"),
                 ({"portrait": {"title": "text\x00"}}, "layout_title")]
        for layouts, code in cases:
            with self.subTest(layouts=layouts):
                self.plan["clips"][0]["layouts"] = layouts
                with self.assertRaises(EditorError) as caught:
                    validate_plan(self.plan, 1, [], {})
                self.assertEqual(caught.exception.code, code)

    def test_title_stays_in_letterbox_and_rejects_missing_space(self):
        folder = ROOT / "work" / f"layout-title-{time.time_ns()}"
        folder.mkdir(parents=True)
        info = {"streams": [{"codec_type": "video", "width": 1280, "height": 720}]}
        meta = portrait_title_image("客户走到哪一步？系统都知道", folder / "title.png", 540, 960, info, DEFAULT_STYLE)
        self.assertLessEqual(len(meta["lines"]), 2)
        self.assertLess(meta["title_bounds"][3], meta["foreground_top"] - 10)
        info["streams"][0].update(width=720, height=1280)
        with self.assertRaises(EditorError) as caught:
            portrait_title_image("title", folder / "no-space.png", 540, 960, info, DEFAULT_STYLE)
        self.assertEqual(caught.exception.code, "layout_title_space")
        info["streams"][0]["side_data_list"] = [{"rotation": -90}]
        meta = portrait_title_image("旋转后横画面", folder / "rotated.png", 540, 960, info, DEFAULT_STYLE)
        self.assertLess(meta["title_bounds"][3], meta["foreground_top"] - 10)

    def test_real_render_preserves_contained_foreground_and_default_background(self):
        # This is a generated calibration source, never a user video or acceptance proof.
        folder = ROOT / "work" / f"layout-render-{time.time_ns()}"
        folder.mkdir(parents=True)
        source = folder / "source.mp4"
        run([executable("ffmpeg"), "-y", "-v", "error", "-f", "lavfi", "-i",
             "testsrc2=size=320x180:rate=30", "-frames:v", "30", "-c:v", "libx264",
             "-pix_fmt", "yuv420p", source])
        project = {"source": {"path": "source.mp4", "sha256": file_hash(source), "probe": probe(source)},
                   "plan": {"overlays": []}, "assets": {}}
        plain = validate_plan(self.plan, 1, [], {})[0]
        decorated = copy.deepcopy(plain)
        decorated["layouts"] = {"portrait": {"fit": "contain", "background": "blur", "title": "客户走到哪一步？"}}
        frames = []
        for name, clip in (("plain", plain), ("decorated", decorated)):
            movie, _ = render_clip(folder, project, clip, [], "portrait", DEFAULT_STYLE, .5)
            image = folder / f"{name}.png"
            run([executable("ffmpeg"), "-y", "-v", "error", "-ss", "0.5", "-i", movie,
                 "-frames:v", "1", image])
            with Image.open(image) as im:
                frames.append(im.convert("RGB"))
        self.assertEqual(frames[0].size, (540, 960))
        # Compare the sharp center, away from codec boundary blocks and the title.
        difference = ImageChops.difference(frames[0].crop((15, 350, 525, 610)),
                                          frames[1].crop((15, 350, 525, 610)))
        self.assertLess(max(ImageStat.Stat(difference).mean), 3)
        corner = frames[0].getpixel((10, 900))
        self.assertTrue(all(abs(a-b) <= 4 for a,b in zip(corner, (21, 25, 35))))
        self.assertGreater(max(ImageStat.Stat(frames[1].crop((0, 720, 540, 940))).stddev), 10)

        # A title adds an input before assets. Verify a following PIP still uses its own pixels.
        asset = folder / "blue.png"
        Image.new("RGB", (100, 100), "#0040ff").save(asset)
        project["assets"]["blue"] = {"path": "blue.png", "kind": "image", "sha256": file_hash(asset)}
        project["plan"]["overlays"] = [{"id": "pip", "clip_id": decorated["id"], "asset_id": "blue",
                                         "offset": 0, "duration": 1, "mode": "pip", "purpose": "calibration only"}]
        movie, _ = render_clip(folder, project, decorated, [], "portrait", DEFAULT_STYLE, .5)
        image = folder / "pip.png"
        run([executable("ffmpeg"), "-y", "-v", "error", "-ss", "0.5", "-i", movie,
             "-frames:v", "1", image])
        with Image.open(image) as im:
            red, green, blue = im.convert("RGB").getpixel((410, 150))
        self.assertLess(red, 15)
        self.assertGreater(blue, 220)


if __name__ == "__main__":
    unittest.main()
