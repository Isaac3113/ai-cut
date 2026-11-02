"""Protect the renamed public entry and legacy runtime compatibility."""
import importlib.util
import os
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'ai_cut_practical_renderer', ROOT/'skill/ai-cut/scripts/render_practical_demo.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class AiCutIdentityTests(unittest.TestCase):
    def test_distribution_keeps_both_console_entries(self):
        project = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']
        self.assertEqual(project['name'], 'ai-cut')
        self.assertEqual(project['scripts']['ai-cut'], 'talking_head_editor.cli:main')
        self.assertEqual(project['scripts']['talking-head'], project['scripts']['ai-cut'])

    def test_practical_tools_prefer_current_runtime_root(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for label in ('current', 'legacy'):
                binary = base/label/'.runtime/ffmpeg/bin/ffmpeg.exe'
                binary.parent.mkdir(parents=True)
                binary.write_bytes(b'path-only fixture; never executed')
            with patch.dict(os.environ, {
                'AI_CUT_ROOT': str(base/'current'),
                'TALKING_HEAD_EDITOR_ROOT': str(base/'legacy')}, clear=True):
                self.assertEqual(Path(renderer.tool_path('ffmpeg', {}, base)),
                                 (base/'current/.runtime/ffmpeg/bin/ffmpeg.exe').resolve())

    def test_practical_tools_still_accept_legacy_root(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            binary = base/'.runtime/ffmpeg/bin/ffmpeg.exe'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'path-only fixture; never executed')
            with patch.dict(os.environ, {'TALKING_HEAD_EDITOR_ROOT': str(base)}, clear=True):
                self.assertEqual(Path(renderer.tool_path('ffmpeg', {}, base)), binary.resolve())


if __name__ == '__main__':
    unittest.main()
