from hashlib import sha256
import importlib.util
from pathlib import Path
import zipfile

import unittest
from unittest.mock import patch
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


class TemplateCenterIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def test_unknown_helper_rejected_before_extraction(self):
        adapter=module('motiongit_adapter');archive=self.root/'unknown.motion'
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('assistant/motion.mjs','unverified code')
        with self.assertRaisesRegex(ValueError,'Unknown helper hash'):
            adapter.bootstrap(archive,self.root/'runtime')
        self.assertFalse((self.root/'runtime').exists())
    def test_verified_bootstrap_keeps_credentials_and_content_inside_archive(self):
        adapter=module('motiongit_adapter');archive=self.root/'fixture.motion';helper=b'fixture-helper'
        with zipfile.ZipFile(archive,'w') as z:
            for name in adapter.PUBLIC_FILES:
                z.writestr(name,helper if name.endswith('motion.mjs') else b'public')
            z.writestr('personal/motiongit.key.json','fixture-private-not-to-copy')
            z.writestr('content/release.bin','fixture-protected-not-to-copy')
        with patch.object(adapter,'KNOWN_HELPERS',{sha256(helper).hexdigest():'fixture'}):
            path,version=adapter.bootstrap(archive,self.root/'runtime')
        self.assertEqual(path.read_bytes(),helper)
        self.assertEqual(version,'fixture')
        actual={p.relative_to(path.parents[1]).as_posix() for p in path.parents[1].rglob('*') if p.is_file()}
        self.assertEqual(actual,set(adapter.PUBLIC_FILES))
    def test_run_allowlist_checks_selected_command_not_payload_words(self):
        adapter=module('motiongit_adapter')
        for args in [['--instance','local','api','render'], ['api','render'],
                     ['--instance','local','render','--instance','other']]:
            with self.assertRaises(ValueError):
                adapter.selected_run_operation(args)
        self.assertEqual(adapter.selected_run_operation(['--instance','local','plan','params.json']), 'plan')
    def test_gallery_refuses_private_media_path(self):
        gallery=module('build_template_gallery')
        with self.assertRaisesRegex(ValueError,'outside approved'):
            gallery.validate([entry({'path':'../../private-original.mp4'})],self.root,False)
    def test_gallery_refuses_executable_demo_url(self):
        gallery=module('build_template_gallery')
        with self.assertRaisesRegex(ValueError,'invalid demo URL'):
            gallery.validate([entry({'url':'javascript:alert(1)'})],self.root,False)
    def test_gallery_refuses_duplicate_ids(self):
        gallery=module('build_template_gallery');row=entry({'url':'https://example.com/demo.mp4'})
        with self.assertRaisesRegex(ValueError,'Duplicate ID'):
            gallery.validate([row,row],self.root,False)


def entry(demo):
    return {'id':'one','label_zh':'演示','layer':'control','category_zh':'测试',
            'description_zh':'示意','uses_zh':[],'avoid_zh':[],'inputs_zh':[],
            'source_url':'https://example.com','validation':{'state':'test'},'demos':[demo]}


if __name__=='__main__':
    unittest.main()
