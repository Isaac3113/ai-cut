"""Verify the renamed rules bundle without installing or copying any runtime."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('student_skill_export', ROOT/'scripts/export_student_skill.py')
student = importlib.util.module_from_spec(spec)
spec.loader.exec_module(student)


class StudentSkillExportTests(unittest.TestCase):
    def test_rules_still_link_to_bundled_references(self):
        content = '[选择](template-selection.md)'
        self.assertEqual(student.link_source_documents(
            content, student.SOURCE/'references/effect-library.md'), content)

    def test_runtime_documentation_links_to_repository(self):
        content = '[更新](../../../docs/CROSS_COMPUTER_UPDATE.md)'
        self.assertEqual(student.link_source_documents(
            content, student.SOURCE/'references/intro-outro.md'),
            '[更新](https://github.com/Isaac3113/ai-cut/blob/main/docs/CROSS_COMPUTER_UPDATE.md)')

    def test_external_files_are_not_read_or_bundled(self):
        with self.assertRaisesRegex(ValueError, 'escapes'):
            student.link_source_documents('[private](../../../../outside.md)',
                                          student.SOURCE/'references/example.md')

    def test_real_rules_bundle_uses_ai_cut_without_another_runtime(self):
        with tempfile.TemporaryDirectory(prefix='ai-cut-rules-test-') as folder:
            output = Path(folder)/'rules'
            with contextlib.redirect_stdout(io.StringIO()):
                student.export(output)
            manifest = json.loads((output/'manifest.json').read_text(encoding='utf-8'))
            dependencies = json.loads((output/'03_工具与依赖.json').read_text(encoding='utf-8'))
            self.assertTrue((output/'ai-cut/SKILL.md').is_file())
            self.assertFalse((output/'talking-head-editor/SKILL.md').exists())
            self.assertFalse((output/'.venv').exists())
            self.assertEqual(dependencies['skill_names'][0], 'ai-cut')
            self.assertTrue(manifest['master_links_pass'])
            with zipfile.ZipFile(output.with_suffix('.zip')) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn('ai-cut/SKILL.md', archive.namelist())


if __name__ == '__main__':
    unittest.main()
