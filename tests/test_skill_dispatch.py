import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('skill_dispatch', ROOT/'skill/ai-cut/scripts/run.py')
dispatch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dispatch)

class SkillDispatchTests(unittest.TestCase):
    def test_ai_cut_root_wins_over_legacy_and_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); (base/'scripts').mkdir()
            (base/'installation.json').write_text(json.dumps({'source_root':str(base/'installed')}))
            self.assertEqual(dispatch.resolve_root(base/'scripts/run.py',{
                'AI_CUT_ROOT':str(base/'chosen'),
                'TALKING_HEAD_EDITOR_ROOT':str(base/'legacy')}), (base/'chosen').resolve())

    def test_explicit_root_wins_over_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); (base/'scripts').mkdir()
            (base/'installation.json').write_text(json.dumps({'source_root':str(base/'old')}))
            self.assertEqual(dispatch.resolve_root(base/'scripts/run.py',{'TALKING_HEAD_EDITOR_ROOT':str(base/'chosen')}), (base/'chosen').resolve())

    def test_installed_root_is_restored_without_author_path(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder); (base/'scripts').mkdir()
            (base/'installation.json').write_text(json.dumps({'source_root':str(base/'my-project')}))
            self.assertEqual(dispatch.resolve_root(base/'scripts/run.py',{}), (base/'my-project').resolve())

    def test_checkout_discovery_works(self):
        self.assertEqual(dispatch.resolve_root(ROOT/'skill/ai-cut/scripts/run.py',{}),ROOT.resolve())

    def test_unconfigured_installation_does_not_guess_author_path(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,'TALKING_HEAD_EDITOR_ROOT'):
                dispatch.resolve_root(Path(folder)/'skill/scripts/run.py',{})
