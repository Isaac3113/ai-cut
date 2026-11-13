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
        self.assertEqual(len(rows), len(self.rows))
        self.assertEqual(len(previews), len(self.previews))
        self.assertGreater(len(self.integrations), 0)
        for row in rows + previews:
            sections = row['learner_guide']['sections']
            self.assertEqual([s['id'] for s in sections], ['preview', 'use', 'inputs', 'parameters', 'instructions', 'status', 'source'], row['id'])
            self.assertEqual([s['title'] for s in sections], self.guide.SECTION_TITLES)
            self.assertTrue(all(s['text'] for s in sections), row['id'])

    def test_enrichment_does_not_change_frozen_identity_qa_demos_or_cases(self):
        rows, previews = self.enriched()
        self.assertTrue(all(row['learner_guide']['category'] in self.guide.LEARNER_CATEGORIES for row in rows + previews))
        for old, enriched in zip(self.rows + self.previews, rows + previews):
            enriched.pop('learner_guide')
            self.assertEqual(enriched, old)

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

    def test_category_and_paged_preview_documents_include_every_entry_once(self):
        rows, previews = self.enriched()
        pages = self.guide.markdown_category_pages(rows, previews)
        self.assertTrue(set(self.guide.LEARNER_CATEGORIES).issubset(pages))
        for row in rows + previews:
            anchor = '<a id="' + row['id'] + '"></a>'
            self.assertEqual(sum(content.count(anchor) for content in pages.values()), 1, row['id'])
            page_name = row['learner_guide']['detail_page'].removesuffix('.md')
            page = pages[page_name]
            self.assertIn(anchor, page)
            self.assertTrue(self.guide.guide_path(row).endswith(row['learner_guide']['detail_page'] + '#' + row['id']))
        self.assertTrue(all(len(page.encode('utf-8')) < 512*1024 for page in pages.values()))
        combined = '\n'.join(pages.values())
        for title in self.guide.SECTION_TITLES:
            self.assertEqual(combined.count('**' + title + '**'), len(rows) + len(previews))

    def test_catalog_index_links_each_entry_to_complete_guide(self):
        rows, previews = self.enriched()
        index = self.guide.markdown_catalog(rows, previews, Counter(r['layer'] for r in rows), self.integrations)
        for row in rows + previews:
            link = self.guide.guide_path(row).removeprefix('templates/')
            self.assertTrue(link in index, row['id'] + ' missing detail link')
        self.assertIn(f'不能把它们称为 {len(rows)} 套整片一键模板', index)
        self.assertLess(len(index.encode('utf-8')), 1024*1024)

    def test_catalog_update_cannot_promote_old_case_to_new_version_validation(self):
        row = deepcopy(next(r for r in self.rows if r.get('integrations')))
        old_case_version = self.guide.primary_case(row)['source']['version']
        row.update(layer='style', version='99.0.0', website_version='98.0.0',
                   latest_official={'catalog_version': '99.0.0'})
        guide = self.guide.guide_for(row)
        status = '\n'.join(guide['sections'][5]['text'])
        self.assertEqual(guide['execution_status'], 'integrated_case')
        self.assertIn('当前公开版尚未验证', guide['status'])
        self.assertIn(old_case_version, status)
        self.assertIn('公开 GitHub 合集当前版本：99.0.0', status)
        self.assertIn('官网独立核对版本：98.0.0', status)
        self.assertEqual(self.guide.primary_case(row)['source']['version'], old_case_version)

    def test_new_industry_and_unknown_categories_do_not_become_visual_backgrounds(self):
        self.assertEqual(self.guide.learner_category({'id':'new','official_group':'prelaunch','category_zh':'新行业'}), 'industry')
        self.assertEqual(self.guide.learner_category({'id':'new','official_group':'innovation','category_zh':'新分类'}), 'innovation')
        self.assertEqual(self.guide.learner_category({'id':'new','category_zh':'完全未知'}), 'uncategorized')

    def test_missing_or_website_only_source_is_not_called_current_catalog_version(self):
        row = {'id':'source-test', 'label_zh':'来源测试', 'layer':'style', 'version':'1.0', 'demos':[],
               'source_observation':{'catalog':'temporarily_absent'}}
        status = '\n'.join(self.guide.guide_for(row)['sections'][5]['text'])
        self.assertIn('上次记录版本：1.0', status)
        self.assertNotIn('合集当前版本', status)
        row['source_observation']['catalog'] = 'not_in_collection'
        status = '\n'.join(self.guide.guide_for(row)['sections'][5]['text'])
        self.assertIn('不能把官网版本当成 GitHub 已发布原包', status)

    def test_claims_are_not_executable_and_large_preview_groups_are_paged(self):
        rows = [{'id':f'claim-{i:03}', 'label_zh':f'展示{i}', 'layer':'preview', 'stage':'claim',
                 'preview_only':True, 'official_group':'claim', 'official_categories':['建筑'], 'demos':[]}
                for i in range(103)]
        self.guide.enrich_entries(rows)
        self.assertTrue(all(r['learner_guide']['execution_status']=='claim_pending' for r in rows))
        pages = self.guide.markdown_category_pages([], rows)
        detail_pages = [p for k,p in pages.items() if k.startswith('preview-')]
        self.assertEqual(len(detail_pages), 3)
        self.assertTrue(all(p.count('**1. 效果预览**') <= 50 for p in detail_pages))
        self.assertIn('官方来源暂未提供可播放 Demo', detail_pages[0])

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
