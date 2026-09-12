"""Focused, media-free regressions for the maintained native adapter."""
import copy
import hashlib
from types import SimpleNamespace
import unittest

from talking_head_editor.jianying import (align_native_duration, frame_mapping, matches_git_blob,
                             punch_points, rgb, themed_captions, validate_native_document)


def validation_fixture():
    material = lambda identity, path: {"id": identity, "path": path}
    segment = lambda identity, volume: {"material_id": identity, "extra_material_refs": [],
        "target_timerange": {"start": 0, "duration": 1_000_000}, "volume": volume,
        "speed": 1, "common_keyframes": []}
    template = {"id": "native-id", "new_version": "75.0.0", "materials": {"videos": [], "audios": []}}
    document = {**copy.deepcopy(template), "duration": 1_000_000,
        "materials": {"videos": [material("v", "source.mkv")],
                      "audios": [material(k, k + ".wav") for k in ("voice", "music", "sfx")]},
        "tracks": [{"type": "video", "name": "main", "segments": [segment("v", 0)]}] +
                  [{"type": "audio", "name": k, "segments": [segment(k, 1)]} for k in ("voice", "music", "sfx")]}
    stems = {k: {"path": k + ".wav", "start_us": 0, "duration_us": 1_000_000, "gain": 1}
             for k in ("voice", "music", "sfx")}
    return document, template, stems


class NativeAdapterTests(unittest.TestCase):
    def validate(self, document, template, stems):
        return validate_native_document(document, template, 1_000_000, 1_000_000,
            [SimpleNamespace(start=0, end=1_000_000)], stems, [{}])

    def test_git_blob_accepts_only_raw_or_exact_crlf_conversion(self):
        source = b"import json\nvalue = 1\n"
        expected = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
        self.assertTrue(matches_git_blob(source, expected))
        self.assertTrue(matches_git_blob(source.replace(b"\n", b"\r\n"), expected))
        self.assertFalse(matches_git_blob(source.replace(b"1", b"2"), expected))
        self.assertFalse(matches_git_blob(source + b" ", expected))

    def test_frame_clock_preserves_exact_join_and_limits_silent_visual_extension(self):
        clips = [{"id": "a", "start": 20.72, "end": 28.66, "frames": 217,
                  "output_start": 0, "playback_speed": 1.1},
                 {"id": "b", "start": 32.29, "end": 38.30, "frames": 164,
                  "output_start": 217 / 30, "playback_speed": 1.1}]
        rows = frame_mapping(clips, 30)
        self.assertEqual(rows[0]["target_duration_us"], rows[1]["target_start_us"])
        self.assertEqual(sum(r["target_duration_us"] for r in rows), 12_700_000)
        self.assertTrue(all(-2 <= r["visual_extension_us"] < 36_668 for r in rows))
        clips[1]["output_start"] += .1
        with self.assertRaisesRegex(ValueError, "shared frame clock"):
            frame_mapping(clips, 30)

    def test_native_duration_rounding_is_bounded_not_cumulative(self):
        segment = SimpleNamespace(duration=999_999)
        self.assertEqual(align_native_duration(segment, 1_000_000), 1)
        self.assertEqual(segment.duration, 1_000_000)
        with self.assertRaisesRegex(ValueError, "more than 1us"):
            align_native_duration(segment, 1_000_002)

    def test_dark_subtitles_split_only_appearance_and_preserve_complete_time(self):
        cues = [{"start": 0, "end": 2_000_000, "text": "如果还没有购买，"}]
        pieces = themed_captions(cues, [(500_000, 1_500_000)])
        self.assertEqual([p["theme"] for p in pieces], ["light", "dark", "light"])
        self.assertEqual(sum(p["end"]-p["start"] for p in pieces), 2_000_000)
        self.assertTrue(all(p["text"] == cues[0]["text"] for p in pieces))
        self.assertEqual(cues[0]["start"], 0)

    def test_scene_punch_maps_inside_an_overlay_from_the_same_clip_clock(self):
        effects = [{"target": "scene", "offset": 1, "duration": 2,
                    "factor": 1.1, "x": .6, "y": .4}]
        points = punch_points(effects, 1, 1_000_000, clip_offset_us=1_500_000, layers=("scene",))
        self.assertAlmostEqual(points[0][1], 1.1)
        self.assertAlmostEqual(points[0][2], -.02)
        self.assertAlmostEqual(points[0][3], -.02)
        self.assertEqual(points[-1][0], 1_000_000)
        self.assertEqual(punch_points(effects, 1, 4_000_000, layers=("presenter",)), [])

    def test_native_validation_accepts_three_unique_fixed_stems(self):
        document, template, stems = validation_fixture()
        self.assertEqual(self.validate(document, template, stems)["status"], "pass")

    def test_native_validation_rejects_dangling_text_speed_reference(self):
        document, template, stems = validation_fixture()
        document["tracks"][0]["segments"][0]["extra_material_refs"] = ["missing-speed"]
        with self.assertRaisesRegex(ValueError, "Unresolved"):
            self.validate(document, template, stems)

    def test_native_validation_rejects_original_video_audio_double_mix(self):
        document, template, stems = validation_fixture()
        document["tracks"][0]["segments"][0]["volume"] = 1
        with self.assertRaisesRegex(ValueError, "must be muted"):
            self.validate(document, template, stems)

    def test_native_validation_rejects_wrong_audio_gain_and_duplicate_stem(self):
        document, template, stems = validation_fixture()
        document["tracks"][1]["segments"][0]["volume"] = .5
        with self.assertRaisesRegex(ValueError, "Actual native audio"):
            self.validate(document, template, stems)
        document["tracks"][1]["segments"][0]["volume"] = 1
        document["tracks"][2]["segments"][0]["material_id"] = "voice"
        with self.assertRaisesRegex(ValueError, "duplicate or replace"):
            self.validate(document, template, stems)

    def test_keyword_color_is_preserved_and_invalid_color_rejected(self):
        self.assertEqual(rgb("#F0BE69"), (240/255, 190/255, 105/255))
        with self.assertRaises(ValueError):
            rgb("white")


if __name__ == "__main__":
    unittest.main(verbosity=2)
