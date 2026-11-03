"""Learner docs must be complete without inventing template capabilities."""
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class LearnerGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gallery = module('build_template_gallery')
        cls.guide = module('template_presentation')
        rows, previews, _ = cls.gallery.read_sources(ROOT)
        cls.rows, cls.integrations, _ = cls.gallery.apply_integrations(ROOT, rows, False)
        cls.previews = previews
        cls.evidence = cls.guide.load_parameter_evidence(ROOT)

    def enriched(self):
        return self.guide.enrich_entries(deepcopy(self.rows), self.evidence), self.guide.enrich_entries(deepcopy(self.previews), self.evidence)

    def test_all_entries_and_preview_have_seven_ordered_nonempty_sections(self):
        rows, previews = self.enriched()
        self.assertEqual((len(rows), len(previews), len(self.integrations)), (216, 1, 11))
        for row in rows + previews:
            sections = row['learner_guide']['sections']
            self.assertEqual([s['id'] for s in sections], ['preview', 'use', 'inputs', 'parameters', 'instructions', 'status', 'source'], row['id'])
            self.assertEqual([s['title'] for s in sections], self.guide.SECTION_TITLES)
            self.assertTrue(all(s['text'] for s in sections), row['id'])

    def test_enrichment_does_not_change_frozen_identity_qa_demos_or_cases(self):
        rows, previews = self.enriched()
        for old, enriched in zip(self.rows + self.previews, rows + previews):
            enriched.pop('learner_guide')
            self.assertEqual(enriched, old)
        categories = {row['category_zh'] for row in self.rows}
        self.assertEqual(len(categories), 27)
        self.assertFalse(categories - set(self.guide.CATEGORY_MAP))

    def test_parameter_contract_is_evidence_based_and_rejects_missing_or_outside_sources(self):
        self.assertEqual(len(self.evidence), 144)
        ids = {r['id'] for r in self.rows if r['layer'] in ('control', 'remotion', 'effect')}
        self.assertEqual(set(self.evidence), ids)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'templates').mkdir()
            data = {'schema_version': 1, 'entries': {'fixture': {'parameters_zh': ['Known'], 'limits_zh': ['Limited'], 'evidence': ['../outside.md']}}}
            (root/'templates/parameter-evidence.json').write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'not in repository'):
                self.guide.load_parameter_evidence(root)

    def test_unknown_parameters_and_sample_defaults_cannot_become_general_capabilities(self):
        row = {'id': 'fixture', 'label_zh': '测试', 'layer': 'style', 'demos': []}
        params, limits = self.guide.parameter_notes(row)
        self.assertIn('不能根据 Demo 推断', params[0])
        row['default_parameters'] = {'color': '#fff'}
        params, limits = self.guide.parameter_notes(row)
        self.assertIn('示例输入', params[0])
        self.assertIn('任意规格', limits[0])
        row['layer'] = 'effect'
        self.assertIn('需要源码适配', self.guide.learner_status(row))

    def test_eight_category_pages_include_every_entry_once_and_preview_separately(self):
        rows, previews = self.enriched()
        pages = self.guide.markdown_category_pages(rows, previews)
        self.assertEqual(set(pages), set(self.guide.LEARNER_CATEGORIES))
        for row in rows + previews:
            anchor = '<a id="' + row['id'] + '"></a>'
            self.assertEqual(sum(content.count(anchor) for content in pages.values()), 1, row['id'])
            page = pages[row['learner_guide']['category']]
            self.assertIn(anchor, page)
            self.assertTrue(self.guide.guide_path(row).endswith(row['learner_guide']['category'] + '.md#' + row['id']))
        self.assertTrue(all(len(page.encode('utf-8')) < 512*1024 for page in pages.values()))
        combined = '\n'.join(pages.values())
        for title in self.guide.SECTION_TITLES:
            self.assertEqual(combined.count('**' + title + '**'), 217)

    def test_catalog_index_links_each_entry_to_complete_guide(self):
        rows, previews = self.enriched()
        index = self.guide.markdown_catalog(rows, previews, Counter(r['layer'] for r in rows), self.integrations)
        for row in rows + previews:
            link = 'categories/' + row['learner_guide']['category'] + '.md#' + row['id']
            self.assertIn(link, index)
        self.assertIn('不能把它们称为 216 套整片一键模板', index)
        self.assertLess(len(index.encode('utf-8')), 512*1024)

    def test_readme_replacement_preserves_other_sections_byte_for_byte(self):
        home = module('build_homepage_showcase')
        original = b'prefix\r\n<!-- COMPARISON -->unchanged\r\n<!-- HOMEPAGE_SHOWCASE:START -->\r\nold\r\n<!-- HOMEPAGE_SHOWCASE:END -->\r\nsuffix'
        updated = home.replace_showcase(original, 'new content')
        start = b'<!-- HOMEPAGE_SHOWCASE:START -->'
        end = b'<!-- HOMEPAGE_SHOWCASE:END -->'
        self.assertEqual(original.split(start)[0], updated.split(start)[0])
        self.assertEqual(original.split(end)[1], updated.split(end)[1])


if __name__ == '__main__':
    unittest.main()
