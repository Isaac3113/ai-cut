import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('social_delivery', ROOT / 'scripts/package_social_delivery.py')
social = importlib.util.module_from_spec(spec)
spec.loader.exec_module(social)


class SocialDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, value in [('transcript.txt', '最终口播，没有时间轴。'), ('video.mp4', 'test bytes; not a real video'),
                            ('fb.txt', '一句\n二句\n三句\n\n四句\n五句'), ('xhs.txt', '标题\n场景\n步骤\n结尾'),
                            ('evidence.md', 'Synthetic fixture: no editorial approval or video validation.')]:
            (self.root / name).write_text(value, encoding='utf-8')
        Image.new('RGB', (160, 90)).save(self.root / 'fb.png')
        Image.new('RGB', (120, 160)).save(self.root / 'xhs.png')
        Image.new('RGB', (160, 120)).save(self.root / 'landscape.png')
        self.args = dict(out=self.root / 'out', transcript=self.root / 'transcript.txt', video=self.root / 'video.mp4',
                         facebook_copy=self.root / 'fb.txt', facebook_cover=self.root / 'fb.png',
                         xiaohongshu_copy=self.root / 'xhs.txt', xiaohongshu_cover=self.root / 'xhs.png',
                         evidence=self.root / 'evidence.md',
                         xiaohongshu_landscape_cover=self.root / 'landscape.png')

    def test_five_deliverables_and_copy_text_preserved_without_false_review(self):
        result = social.build(**self.args)
        out = self.args['out']
        self.assertEqual(result['five_deliverables'], 'present')
        self.assertTrue(result['current_workflow_complete'])
        self.assertEqual(result['deliverable_count'], 5)
        self.assertEqual((out / '小红书/封面_4比3横版.png').read_bytes(), (self.root / 'landscape.png').read_bytes())
        self.assertEqual((out / '小红书/封面.png').read_bytes(), (self.root / 'xhs.png').read_bytes())
        self.assertEqual((out / 'Facebook/文案.txt').read_text(encoding='utf-8'), '一句\n二句\n三句\n\n四句\n五句\n')
        self.assertEqual((out / 'Facebook/封面.png').read_bytes(), (self.root / 'fb.png').read_bytes())
        self.assertEqual((out / '一键复制.md').read_text(encoding='utf-8').count('```text'), 2)
        self.assertIn('video_decode_and_full_watch_listen', result['not_certified_by_this_tool'])

    def test_missing_cover_does_not_create_partial_package(self):
        self.args['xiaohongshu_cover'] = self.root / 'missing.png'
        with self.assertRaises(FileNotFoundError):
            social.build(**self.args)
        self.assertFalse(self.args['out'].exists())

    def test_wrong_ratio_and_broken_image_rejected_before_write(self):
        for data in [b'not an image', (self.root / 'fb.png').read_bytes()]:
            (self.root / 'xhs.png').write_bytes(data)
            with self.assertRaises((ValueError, OSError)):
                social.build(**self.args)
            self.assertFalse(self.args['out'].exists())

    def test_existing_delivery_never_overwritten(self):
        social.build(**self.args)
        before = (self.args['out'] / '交付清单.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Output exists'):
            social.build(**self.args)
        self.assertEqual(before, (self.args['out'] / '交付清单.json').read_bytes())

    def test_changed_transcript_video_and_deliverable_detected(self):
        social.build(**self.args)
        for path in [self.root / 'transcript.txt', self.root / 'video.mp4', self.args['out'] / 'Facebook/文案.txt',
                     self.args['out'] / '小红书/封面_4比3横版.png']:
            old = path.read_bytes()
            path.write_bytes(old + b'changed')
            with self.assertRaises(ValueError):
                social.audit(self.args['out'], self.args['transcript'], self.args['video'])
            path.write_bytes(old)

    def test_framework_labels_rejected_but_regular_chinese_kept(self):
        for label in ['A — Attention：', 'I — Interest：', 'D — Desire：', 'A — Action：', 'AIDA']:
            (self.root / 'fb.txt').write_text(label + '\n正文', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'framework'):
                social.build(**self.args)
        self.assertEqual(social.format_copy('  销售说跟了。\n\n老板怎么查？'), '销售说跟了。\n老板怎么查？\n')

    def test_srt_and_missing_required_manifest_entry_rejected(self):
        (self.root / 'transcript.txt').write_text('1\n00:00:00,000 --> 00:00:01,000\n口播', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'plain transcript'):
            social.build(**self.args)
        (self.root / 'transcript.txt').write_text('口播', encoding='utf-8')
        social.build(**self.args)
        path = self.args['out'] / '交付清单.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        del manifest['files']['Facebook/文案.txt']
        path.write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'required deliverables'):
            social.audit(self.args['out'], self.args['transcript'], self.args['video'])


    def test_missing_landscape_or_portrait_passed_as_landscape_leaves_no_output(self):
        for candidate, error in [(self.root / 'missing.png', FileNotFoundError),
                                 (self.root / 'xhs.png', ValueError)]:
            self.args['xiaohongshu_landscape_cover'] = candidate
            with self.assertRaises(error):
                social.build(**self.args)
            self.assertFalse(self.args['out'].exists())

    def test_existing_9_16_portrait_is_preserved_with_additional_4_3(self):
        Image.new('RGB', (90, 160)).save(self.root / 'xhs.png')
        self.args['xiaohongshu_ratio'] = '9:16'
        result = social.build(**self.args)
        self.assertTrue(result['current_workflow_complete'])
        with Image.open(self.args['out'] / '小红书/封面.png') as im:
            self.assertEqual(im.size, (90, 160))
        with Image.open(self.args['out'] / '小红书/封面_4比3横版.png') as im:
            self.assertEqual(im.size, (160, 120))

    def test_landscape_ratio_cannot_be_relaxed_by_changing_receipt(self):
        social.build(**self.args)
        out = self.args['out']
        path = out / '交付清单.json'
        m = json.loads(path.read_text(encoding='utf8'))
        m['covers']['小红书_4比3横版']['expected_ratio'] = 3 / 4
        path.write_text(json.dumps(m), encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'must be 4:3'):
            social.audit(out, self.args['transcript'], self.args['video'])

    def test_legacy_package_needs_explicit_audit_and_is_not_current_complete(self):
        social.build(**self.args)
        out = self.args['out']
        path = out / '交付清单.json'
        m = json.loads(path.read_text(encoding='utf8'))
        m['schema_version'] = 1
        m['workflow_rules'] = '0.2.6'
        del m['covers']['小红书_4比3横版']
        del m['files']['小红书/封面_4比3横版.png']
        path.write_text(json.dumps(m), encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'Legacy package'):
            social.audit(out, self.args['transcript'], self.args['video'])
        legacy = social.audit(out, self.args['transcript'], self.args['video'], allow_legacy=True)
        self.assertFalse(legacy['current_workflow_complete'])
        self.assertEqual(legacy['deliverable_count'], 4)
        self.assertEqual(legacy['five_deliverables'], 'legacy_missing_4:3')


if __name__ == '__main__':
    unittest.main()
