import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'review_media', Path(__file__).parents[1] / 'scripts/verify_review_media.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReviewMediaSamplingTests(unittest.TestCase):
    def test_legacy_call_keeps_original_sample_set(self):
        samples, binding = module.sampling_plan(3045)
        self.assertEqual(len(samples), 98)
        self.assertEqual(samples[:6], [0, 60, 64, 65, 120, 134])
        self.assertIn(2954, samples)
        self.assertIn(2955, samples)
        self.assertEqual(samples[-1], 3044)
        self.assertEqual(binding, {'mode': 'legacy_defaults'})

    def test_new_cover_cut_and_ending_indices_replace_old_case_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'boundaries.json'
            frames = [29, 30, 31, 395, 396, 396, 2738, 2739]
            path.write_text(json.dumps(frames), encoding='utf-8-sig')
            samples, binding = module.sampling_plan(2829, path)
            self.assertTrue(set(frames) <= set(samples))
            self.assertTrue(set(range(0, 2829, 60)) <= set(samples))
            self.assertEqual(samples[-1], 2828)
            self.assertEqual(samples.count(396), 1)
            self.assertNotIn(64, samples)
            self.assertNotIn(2955, samples)
            self.assertEqual(binding['requested_frames'], frames)
            self.assertEqual(binding['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_custom_grid_only_still_checks_both_endpoints(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'empty.json'
            path.write_text('[]', encoding='utf-8')
            self.assertEqual(module.sampling_plan(62, path)[0], [0, 60, 61])
            self.assertEqual(module.sampling_plan(1, path)[0], [0])

    def test_invalid_custom_input_stops_before_output_or_decoding(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            path = directory / 'invalid.json'
            for value in ([-1], [2829], [30.0], [True], ['30'], {'frames': [30]}):
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding='utf-8')
                    with patch.object(module, 'run') as run:
                        with self.assertRaises(ValueError):
                            module.verify(directory / 'not-read.mp4', directory / 'not-created',
                                          'not-called-ffmpeg', 'not-called-ffprobe', 2829, path)
                        run.assert_not_called()
                    self.assertFalse((directory / 'not-created').exists())
            for count in (0, -1, 30.0, True):
                with self.assertRaises(ValueError): module.sampling_plan(count)


    def test_balanced_expression_preserves_all_indices(self):
        import re
        samples = list(range(0, 1200, 3)) + [1199]
        expression = module.select_expression(samples)
        self.assertEqual([int(n) for n in re.findall(r'eq\(n,(\d+)\)', expression)], samples)
        depth = maximum = 0
        for token in expression:
            if token == '(':
                depth += 1
                maximum = max(maximum, depth)
            elif token == ')':
                depth -= 1
        self.assertEqual(depth, 0)
        self.assertLessEqual(maximum, 10)
        self.assertEqual(module.select_expression([17]), 'eq(n,17)')
        self.assertEqual(module.select_expression([]), '0')

    def test_real_ffmpeg_accepts_151_indices_and_preserves_selected_pts(self):
        # This is a 16x16 generated lavfi fixture, never user footage or quality evidence.
        configured = os.environ.get('FFMPEG_EXE') or shutil.which('ffmpeg')
        bundled = Path.home() / '.chatcut/cache/ffmpeg/8.1/win32-x64/ffmpeg.exe'
        ffmpeg = configured or (str(bundled) if bundled.is_file() else None)
        if not ffmpeg:
            self.skipTest('FFmpeg is unavailable; set FFMPEG_EXE to run the real parser regression')
        samples = list(range(0, 300, 2)) + [299]
        expression = module.select_expression(samples)
        command = [ffmpeg, '-hide_banner', '-nostdin', '-v', 'error',
                   '-f', 'lavfi', '-i', 'testsrc2=size=16x16:rate=30:duration=10',
                   '-vf', f"select='{expression}'", '-fps_mode', 'vfr',
                   '-c:v', 'rawvideo', '-f', 'framemd5', '-']
        result = subprocess.run(command, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
        rows = [line.split(',') for line in result.stdout.decode('utf-8').splitlines()
                if line.strip() and not line.startswith('#')]
        self.assertEqual(len(rows), 151)
        self.assertEqual([int(row[2].strip()) for row in rows], samples)


if __name__ == '__main__':
    unittest.main()
