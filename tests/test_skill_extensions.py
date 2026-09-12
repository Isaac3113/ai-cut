"""Regression checks for extension installation and honest media review failures."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('install_extensions')
reviewer = load('video_use_review')


class SkillExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='skill-extension-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'stage'
        self.target = self.root / 'installed'
        specs = []
        for name in ('first', 'second'):
            data = b'upstream\n'
            source = self.stage / name
            source.mkdir(parents=True)
            (source / 'SKILL.md').write_bytes(data)
            adapter = self.root / 'skill-adapters' / name
            adapter.mkdir(parents=True)
            (adapter / 'SKILL.md').write_text('local scope', encoding='utf-8')
            specs.append({'name': name, 'repository': 'test/fixture', 'commit': 'fixed-test', 'path': '.',
                          'adaptation': 'test', 'git_blobs': {'SKILL.md': installer.git_blob(data)}})
        (self.root / 'extensions').mkdir()
        (self.root / 'extensions/upstream-lock.json').write_text(json.dumps({'skills': specs}), encoding='utf-8')
        self.root_patch = patch.object(installer, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_all_sources_checked_before_first_install(self):
        (self.stage / 'second/SKILL.md').write_text('tampered', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Upstream mismatch'):
            installer.install(self.stage, self.target)
        self.assertFalse(self.target.exists())

    def test_windows_newlines_reproduce_exact_upstream(self):
        (self.stage / 'first/SKILL.md').write_bytes(b'upstream\r\n')
        installer.install(self.stage, self.target)
        self.assertEqual((self.target / 'first/UPSTREAM_SKILL.md').read_bytes(), b'upstream\n')

    def test_user_edited_skill_preserved_on_upgrade(self):
        installer.install(self.stage, self.target)
        file = self.target / 'second/SKILL.md'
        file.write_text('user custom rule', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'User-modified'):
            installer.install(self.stage, self.target)
        self.assertEqual(file.read_text(encoding='utf-8'), 'user custom rule')

    def test_unmanaged_skill_preserved(self):
        (self.target / 'first').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'unmanaged'):
            installer.install(self.stage, self.target)
        self.assertFalse((self.target / 'second').exists())

    def test_paths_cannot_escape_or_read_secrets(self):
        for relative in ('../private', 'C:/secret', '.env.example', '.git/config'):
            with self.subTest(path=relative), self.assertRaises(ValueError):
                installer.inside(self.root, relative)

    def test_failed_audio_is_not_reported_as_silence(self):
        result = subprocess.CompletedProcess([], 1, b'', b'bad audio decoder')
        with patch.object(reviewer, 'executable', return_value='ffmpeg'), patch.object(reviewer.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'Audio decode failed'):
                reviewer.strict_envelope(Path('video.mp4'), 0, 1)

    def test_short_audio_cannot_fill_long_review_range(self):
        result = subprocess.CompletedProcess([], 0, b"\0\0" * 1600, b"")
        with patch.object(reviewer, 'executable', return_value='ffmpeg'), patch.object(reviewer.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'Incomplete audio range'):
                reviewer.strict_envelope(Path('video.mp4'), 50, 54)

    def test_existing_review_is_not_overwritten(self):
        video = self.root / 'video.mp4'
        video.write_bytes(b'test')
        output = self.root / 'review.png'
        output.write_bytes(b'user review')
        with self.assertRaisesRegex(ValueError, 'Output exists'):
            reviewer.review(video, 0, 1, output, self.root)
        self.assertEqual(output.read_bytes(), b'user review')

    def test_invalid_range_writes_nothing(self):
        video = self.root / 'video.mp4'
        video.write_bytes(b'test')
        output = self.root / 'new.png'
        info = {'format': {'duration': '10'}, 'streams': [{'codec_type': 'video'}, {'codec_type': 'audio'}]}
        with patch.object(reviewer, 'probe', return_value=info):
            with self.assertRaisesRegex(ValueError, 'Require 0'):
                reviewer.review(video, 5, float('nan'), output, self.root)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
