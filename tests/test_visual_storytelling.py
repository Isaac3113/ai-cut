import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

from talking_head_editor.illustrations import frame, render_scene, validate
from talking_head_editor.timeline import DEFAULT_STYLE, default_plan, validate_plan
from talking_head_editor.util import EditorError, executable, file_hash, probe, run
from talking_head_editor.visuals import write_captions


class VisualStorytelling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Retain small calibration artifacts for inspection; never touch user media.
        cls.folder = Path(tempfile.mkdtemp(prefix="talking-head-storytelling-"))

    def scene(self, kind="states"):
        return {"kind": kind, "duration": 5,
                "events": [0, 1.5, 3] if kind in ("states", "registration") else [0, 1.5],
                "purpose": "Generated regression fixture, not a real customer or product capture"}

    def assert_rejected(self, spec, code=None):
        with self.assertRaises(EditorError) as caught:
            validate(spec)
        if code:
            self.assertEqual(caught.exception.code, code)

    def test_scene_event_order_bounds_and_finite_values(self):
        for kind in ("states", "entry", "no_reply", "registration"):
            spec = self.scene(kind)
            before = copy.deepcopy(spec)
            self.assertEqual(validate(spec), before)
            self.assertEqual(spec, before)
        bad_events = [[], [0, 1], [.1, 1, 2], [0, 1, 1], [0, 2, 1],
                      [0, -1, 2], [0, 1, 5], [0, 1, float("inf")],
                      [0, float("nan"), 2], [False, 1, 2], [0, "1", 2]]
        for events in bad_events:
            with self.subTest(events=events):
                self.assert_rejected({**self.scene(), "events": events}, "scene_events")
        for duration in (None, True, "5", .49, 30.01, float("inf"), float("nan")):
            with self.subTest(duration=duration):
                self.assert_rejected({**self.scene(), "duration": duration}, "scene_duration")

    def test_malformed_scene_inputs_raise_editor_errors(self):
        cases = [None, [], "states", 1,
                 {**self.scene(), "kind": "unknown"}, {**self.scene(), "kind": []},
                 {**self.scene(), "events": None}, {**self.scene(), "events": "012"},
                 {**self.scene(), "events": {"a": 0, "b": 1, "c": 2}},
                 {**self.scene(), "purpose": None}, {**self.scene(), "purpose": 123},
                 {**self.scene(), "purpose": "  "}]
        for spec in cases:
            with self.subTest(spec=spec):
                self.assert_rejected(spec)

    def test_states_change_the_object_panel_without_moving_the_window(self):
        spec = self.scene()
        images = [frame(spec, t, 1280, 720) for t in (.1, 1.6, 3.1)]
        for image in images:
            self.assertEqual(image.size, (1280, 720))
        for before, after in zip(images, images[1:]):
            # A changed selection alone is insufficient: the illustrated object must change.
            self.assertIsNotNone(ImageChops.difference(
                before.crop((691, 219, 1186, 532)), after.crop((691, 219, 1186, 532))).getbbox())
            self.assertIsNone(ImageChops.difference(
                before.crop((0, 0, 1280, 190)), after.crop((0, 0, 1280, 190))).getbbox())
            self.assertIsNone(ImageChops.difference(
                before.crop((42, 100, 213, 587)), after.crop((42, 100, 213, 587))).getbbox())

    def card_bounds(self, image):
        # This stroke uniquely belongs to the movable customer record, not the columns.
        difference = ImageChops.difference(image, Image.new("RGB", image.size, "#C8D9E4"))
        channels = difference.split()
        nonzero = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        bounds = nonzero.point(lambda value: 255 if value == 0 else 0).getbbox()
        self.assertIsNotNone(bounds)
        return bounds

    def test_customer_card_moves_through_intermediate_pixels(self):
        for kind in ("entry", "no_reply", "registration"):
            spec = self.scene(kind)
            original = copy.deepcopy(spec)
            for event in spec["events"][1:]:
                with self.subTest(kind=kind, event=event):
                    frames = [frame(spec, t, 1280, 720)
                              for t in (event-.01, event+.325, event+.7)]
                    bounds = [self.card_bounds(image) for image in frames]
                    self.assertLess(bounds[0][0], bounds[1][0])
                    self.assertLess(bounds[1][0], bounds[2][0])
                    self.assertEqual(bounds[0][1:], (300, bounds[0][2], 439))
                    self.assertEqual([b[1] for b in bounds], [300]*3)
                    self.assertEqual([b[3] for b in bounds], [439]*3)
                    self.assertIsNotNone(ImageChops.difference(frames[0], frames[1]).getbbox())
                    self.assertIsNotNone(ImageChops.difference(frames[1], frames[2]).getbbox())
            self.assertEqual(spec, original)

    def test_subtitle_band_is_empty_at_both_supported_sizes(self):
        # Current desktop layout keeps the bottom 1/6 of the frame clear (180 px at 1080p).
        # Caption weight/size must still be checked on the actual composed video.
        for kind in ("states", "entry", "no_reply", "registration"):
            spec = self.scene(kind)
            for size in ((1280, 720), (1920, 1080)):
                for event in spec["events"]:
                    with self.subTest(kind=kind, size=size, event=event):
                        image = frame(spec, event+.2, *size)
                        band = image.crop((0, size[1]*5//6, size[0], size[1]))
                        self.assertIsNone(ImageChops.difference(
                            band, Image.new("RGB", band.size, "#E9EDEF")).getbbox())
        with self.assertRaises(EditorError) as caught:
            frame(self.scene(), 0, 1080, 1920)
        self.assertEqual(caught.exception.code, "scene_geometry")

    def test_natural_caption_style_is_written_without_changing_cues(self):
        cues = [{"start": .25, "end": 1.75, "lines": ["客户在哪一步", "系统都能知道"]}]
        original = copy.deepcopy(cues)
        styles = [("legacy", dict(DEFAULT_STYLE), -1, 3, 1),
                  ("natural", {**DEFAULT_STYLE, "caption_bold": False,
                               "caption_outline": 1.5, "caption_shadow": 0,
                               "caption_color": "#FFFFFF", "keywords": []}, 0, 1.5, 0),
                  ("no-stroke", {**DEFAULT_STYLE, "caption_bold": False,
                                 "caption_outline": 0, "caption_shadow": 0}, 0, 0, 0)]
        srt_outputs = []
        for name, style, bold, outline, shadow in styles:
            folder = self.folder / name
            folder.mkdir()
            write_captions(folder, cues, 1920, 1080, style)
            ass = (folder / "captions.ass").read_text(encoding="utf-8-sig")
            style_line = next(line for line in ass.splitlines() if line.startswith("Style: Default,"))
            field_names = next(line for line in ass.splitlines() if line.startswith("Format: Name,")).split(": ", 1)[1].split(", ")
            fields = dict(zip(field_names, style_line.split(": ", 1)[1].split(",")))
            self.assertEqual(int(fields["Bold"]), bold)
            self.assertEqual(float(fields["Outline"]), outline)
            self.assertEqual(float(fields["Shadow"]), shadow)
            self.assertEqual(fields["PrimaryColour"], "&H00FFFFFF")
            self.assertIn("Dialogue: 0,0:00:00.25,0:00:01.75,", ass)
            if name == "natural":
                self.assertNotIn(r"\blur", ass)
                self.assertNotIn(r"{\c", ass)
            srt_outputs.append((folder / "captions.srt").read_text(encoding="utf-8"))
        self.assertEqual(cues, original)
        self.assertEqual(srt_outputs, [srt_outputs[0]]*3)
        self.assertIn("00:00:00,250 --> 00:00:01,750", srt_outputs[0])

    def test_illegal_caption_style_parameters_are_rejected(self):
        plan = default_plan(2, 0)
        base = copy.deepcopy(plan)
        for key, values in (("caption_bold", [0, 1, "false", None]),
                            ("caption_outline", [-.1, 4.1, True, "2", None, float("nan"), float("inf")]),
                            ("caption_shadow", [-.1, 4.1, True, "0", None, float("nan"), float("inf")])):
            for value in values:
                with self.subTest(key=key, value=value):
                    plan = copy.deepcopy(base)
                    plan["style"][key] = value
                    with self.assertRaises(EditorError) as caught:
                        validate_plan(plan, 2, [], {})
                    self.assertIn(caught.exception.code, {"caption_weight", "caption_stroke", "invalid_number"})
        natural = copy.deepcopy(base)
        natural["style"].update(caption_bold=False, caption_outline=1.5, caption_shadow=0)
        self.assertEqual(validate_plan(natural, 2, [], {}), validate_plan(base, 2, [], {}))

    def test_shortest_three_state_scene_encodes_and_fully_decodes(self):
        # Synthetic half-second calibration, never evidence of user-footage acceptance.
        spec = {**self.scene(), "duration": .5, "events": [0, .15, .3]}
        target = self.folder / "shortest-states.mp4"
        receipt = render_scene(spec, target)
        info = probe(target)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"]), (1920, 1080))
        self.assertEqual(video["pix_fmt"], "yuv420p")
        self.assertEqual(video["r_frame_rate"], "30/1")
        self.assertEqual(int(video["nb_frames"]), 15)
        self.assertAlmostEqual(float(info["format"]["duration"]), .5, places=2)
        self.assertFalse(any(s["codec_type"] == "audio" for s in info["streams"]))
        self.assertEqual(receipt["sha256"], file_hash(target))
        self.assertEqual(json.loads(target.with_suffix(".json").read_text())["frames"], 15)
        run([executable("ffmpeg"), "-v", "error", "-xerror", "-i", target, "-f", "null", "-"])
        images = []
        for index, at in enumerate((.03, .23, .43)):
            png = self.folder / f"decoded-{index}.png"
            run([executable("ffmpeg"), "-y", "-v", "error", "-i", target, "-ss", str(at),
                 "-frames:v", "1", png])
            with Image.open(png) as image:
                images.append(image.convert("RGB").crop((1040, 330, 1780, 795)))
        self.assertIsNotNone(ImageChops.difference(images[0], images[1]).getbbox())
        self.assertIsNotNone(ImageChops.difference(images[1], images[2]).getbbox())
        with self.assertRaises(EditorError) as caught:
            render_scene(spec, target)
        self.assertEqual(caught.exception.code, "scene_exists")


if __name__ == "__main__":
    unittest.main()
