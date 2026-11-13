"""The authored extension must preserve upstream registries and honest runtime labels."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def authored_entry():
    return {
        'id': 'ai-cut-fixture-canvas', 'label_zh': '自制编辑画布测试',
        'layer': 'authored', 'category_zh': '口播与讲解',
        'description_zh': '独立作者源码场景，不是官方原包。',
        'uses_zh': ['流程讲解'], 'avoid_zh': ['无实际来源的数据'],
        'inputs_zh': ['自备获授权素材'],
        'source_url': 'https://github.com/Isaac3113/ai-cut',
        'source_id': 'ai-cut-fixture-canvas', 'version': 'test',
        'license': 'MIT authored fixture',
        'availability': '作者源码测试状态；官方平台导入未验证',
        'validation': {'state': 'fixture', 'scope': 'Unit fixture only, not a rendered demo'},
        'demos': [{'kind': 'synthetic', 'url': 'https://example.com/fixture.mp4'}],
    }


class AuthoredTemplateExtensionTests(unittest.TestCase):
    def setUp(self):
        self.gallery = module('build_template_gallery')
        self.presentation = module('template_presentation')
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'templates').mkdir()
        for filename in self.gallery.SOURCES:
            shutil.copyfile(ROOT / 'templates' / filename, self.root / 'templates' / filename)

    def tearDown(self):
        self.temp.cleanup()

    def add_registry(self, rows):
        (self.root / 'templates' / 'authored-templates.json').write_text(
            json.dumps({'schema_version': 1, 'entries': rows}), encoding='utf-8')

    def test_optional_extension_keeps_every_upstream_record_and_baseline_intact(self):
        before, previews, provenance = self.gallery.read_sources(self.root)
        raw_before = {p.name: p.read_bytes() for p in (self.root / 'templates').iterdir()}
        row = authored_entry()
        self.add_registry([row])
        after, after_previews, after_provenance = self.gallery.read_sources(self.root)
        self.assertEqual(after[:-1], before)
        self.assertEqual(after[-1], row)
        self.assertEqual(after_previews, previews)
        self.assertEqual(after_provenance[:-1], provenance)
        self.assertEqual(after_provenance[-1]['path'], 'templates/authored-templates.json')
        self.assertEqual({p.name: p.read_bytes() for p in (self.root / 'templates').iterdir()
                          if p.name != 'authored-templates.json'}, raw_before)
        self.assertEqual(self.gallery.BASELINE_EXPECTED,
                         {'style': 72, 'control': 70, 'remotion': 55, 'effect': 19})

    def test_authored_file_cannot_relabel_an_upstream_source(self):
        row = authored_entry()
        row['layer'] = 'style'
        self.add_registry([row])
        with self.assertRaisesRegex(ValueError, 'must not relabel upstream'):
            self.gallery.read_sources(self.root)

    def test_authored_id_cannot_shadow_existing_template(self):
        original, _, _ = self.gallery.read_sources(self.root)
        row = authored_entry()
        row['id'] = original[0]['id']
        self.add_registry([row])
        rows, _, _ = self.gallery.read_sources(self.root)
        with self.assertRaisesRegex(ValueError, 'Duplicate ID'):
            self.gallery.validate(rows, self.root / 'docs/template-gallery', False)

    def test_authored_guide_keeps_its_own_runtime_and_package_boundary(self):
        row = authored_entry()
        before = deepcopy(row)
        guide = self.presentation.guide_for(row)
        self.assertEqual(row, before)
        self.assertEqual(guide['execution_status'], 'source_ready')
        status = '\n'.join(guide['sections'][5]['text'])
        self.assertIn(row['availability'], status)
        self.assertIn('本条自己的运行入口', status)
        self.assertNotIn('本仓库提供目录与已渲染演示，未附送个人', status)
        self.assertNotIn('需准备 Remotion 运行环境', status)
        self.assertNotIn('公开 GitHub 合集当前版本', status)

    def test_authored_preview_is_visible_before_collapsed_categories(self):
        home = module('build_homepage_showcase')
        row = authored_entry()
        asset = {'kind': 'official_image', 'url': 'https://example.com/fixture.jpg',
                 'source_demo_url': 'https://example.com/fixture.mp4',
                 'width': 1920, 'height': 1080}
        fragment = home.make_fragment({'entries': [row], 'integrations': []},
                                      {row['id']: asset})
        featured = fragment.index('### AI Cut 通用自制模板')
        card = fragment.index('<strong>自制编辑画布测试</strong>')
        category = fragment.index('<details>')
        self.assertLess(featured, card)
        self.assertLess(card, category)

    def test_author_package_requires_allowlisted_path_and_reviewed_identity(self):
        row = authored_entry()
        package = self.root / 'templates/authored-packages/fixture.motion'
        package.parent.mkdir()
        package.write_bytes(b'archive identity fixture; not a MotionGit conformance assertion')
        row['author_package'] = {'path': package.relative_to(self.root).as_posix(),
                                 'bytes': package.stat().st_size,
                                 'sha256': sha256(package.read_bytes()).hexdigest()}
        self.gallery.verify_authored_packages(self.root, [row])
        package.write_bytes(b'changed after review')
        with self.assertRaisesRegex(ValueError, 'differs from reviewed bytes'):
            self.gallery.verify_authored_packages(self.root, [row])
        row['author_package']['path'] = '../private.motion'
        with self.assertRaisesRegex(ValueError, 'outside approved directory'):
            self.gallery.verify_authored_packages(self.root, [row])


if __name__ == '__main__':
    unittest.main()
