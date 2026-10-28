from copy import deepcopy
import json
import shutil
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
            'source_url':'https://example.com','source_id':'fixture','version':'fixture','license':'fixture','availability':'fixture','validation':{'state':'test'},'demos':[demo]}


class IntegrationGrowthTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'templates').mkdir()
        self.media=self.root/'docs/template-gallery/demos/cases/fixture.mp4'
        self.media.parent.mkdir(parents=True)
        self.media.write_bytes(b'unit-test fixture; not a rendered or reviewed user sample')
        self.gallery=module('build_template_gallery')
        self.base=entry({'url':'https://example.com/official.mp4'})

    def tearDown(self): self.temp.cleanup()

    def record(self, ident='case-one', target='one'):
        return {'id':ident,'entry_id':target,'project_id':'TEST fixture',
                'integrated_at':'2026-10-27T10:00:00Z',
                'source':{'url':'https://example.com/official','package_id':'fixture',
                          'version':'v2','sha256':'a'*64,'official':True,'verification_note':'unit-test fixture'},
                'invocation':{'method':'official helper','command':'python scripts/motiongit_adapter.py start --summary',
                              'guide_url':'https://example.com/guide','inputs_zh':['own footage']},
                'rights':{'private_demo_redistribution':True,'evidence':'unit-test fixture'},
                'qa':{'state':'verified_demo','decode_verified':True,'sample_images_viewed':True,
                      'scope':'unit-test fixture, not actual user validation','continuous_watch':False},
                'demo':{'kind':'own','path':'demos/cases/fixture.mp4','sha256':sha256(self.media.read_bytes()).hexdigest(),
                        'bytes':self.media.stat().st_size,'description_zh':'unit-test fixture'}}

    def apply(self, records, entries=None):
        (self.root/'templates/template-integrations.json').write_text(json.dumps({'schema_version':1,'integrations':records}),encoding='utf-8')
        return self.gallery.apply_integrations(self.root, entries if entries is not None else [self.base], False)

    def test_empty_overlay_does_not_change_entries(self):
        merged,records,_=self.apply([])
        self.assertEqual(merged,[self.base]); self.assertEqual(records,[])

    def test_existing_entry_keeps_original_validation_and_version(self):
        original=deepcopy(self.base)
        merged,_,_=self.apply([self.record()])
        self.assertEqual(len(merged),1)
        self.assertEqual(self.base,original)
        self.assertEqual(merged[0]['validation'],original['validation'])
        self.assertEqual(merged[0]['version'],original['version'])
        self.assertEqual(merged[0]['demos'][0]['integration_id'],'case-one')
        self.assertEqual(merged[0]['demos'][1],original['demos'][0])

    def test_latest_case_is_chronological_and_demo_not_duplicated(self):
        older=self.record('old'); newer=self.record('new')
        newer['integrated_at']='2026-10-28T10:00:00Z'
        merged,_,_=self.apply([newer,older])
        self.assertEqual(merged[0]['latest_integration_id'],'new')
        self.assertEqual(len(merged[0]['demos']),2)
        self.assertEqual(len(merged[0]['integrations']),2)

    def ratio_cases(self):
        portrait=self.record('portrait'); landscape=self.record('landscape')
        portrait['source']['version']='portrait-version'
        portrait['demo'].update(width=720,height=1280)
        landscape['source']['version']='landscape-version'
        landscape['integrated_at']='2026-10-28T10:00:00Z'
        media=self.media.with_name('landscape.mp4');media.write_bytes(b'landscape unit-test fixture')
        landscape['demo'].update(path='demos/cases/landscape.mp4',width=1280,height=720,
                                 sha256=sha256(media.read_bytes()).hexdigest(),bytes=media.stat().st_size)
        return portrait,landscape

    def test_matching_ratio_preview_preserves_true_latest_case(self):
        self.base['ratio']='9:16';portrait,landscape=self.ratio_cases()
        merged,_,_=self.apply([landscape,portrait]); row=merged[0]
        self.assertEqual(row['latest_integration_id'],'landscape')
        self.assertEqual([c['id'] for c in row['integrations']],['landscape','portrait'])
        self.assertEqual(row['preview_integration_id'],'portrait')
        self.assertEqual([d.get('integration_id') for d in row['demos'][:2]],['portrait','landscape'])
        self.assertEqual(self.gallery.preview_integration(row)['source']['version'],'portrait-version')

    def test_ratio_label_fallback_and_no_match_keep_newest(self):
        self.base['ratio']='16:9';portrait,landscape=self.ratio_cases()
        landscape['demo'].pop('width');landscape['demo'].pop('height');landscape['demo']['ratio']='16:9'
        merged,_,_=self.apply([portrait,landscape])
        self.assertEqual(merged[0]['preview_integration_id'],'landscape')
        self.base['ratio']='1:1'
        merged,_,_=self.apply([portrait,landscape])
        self.assertEqual(merged[0]['preview_integration_id'],'landscape')

    def test_preview_metadata_matches_ratio_on_homepage_and_markdown(self):
        self.base['ratio']='9:16';portrait,landscape=self.ratio_cases()
        merged,records,_=self.apply([landscape,portrait])
        home=module('build_homepage_showcase')
        asset={'kind':'local_gif','path':'fixture.gif','duration_seconds':3,'width':180,'source_demo':'fixture.mp4'}
        fragment=home.make_fragment({'entries':merged,'integrations':records},{'one':asset})
        self.assertIn('当前本人Demo版本：portrait-version',fragment)
        self.assertNotIn('当前本人Demo版本：landscape-version',fragment)
        with patch.object(self.gallery,'read_sources',return_value=([self.base],[],[])):
            self.gallery.build(self.root,False)
        markdown=(self.root/'templates/README.zh-CN.md').read_text(encoding='utf-8')
        self.assertIn('当前本人Demo版本：portrait-version',markdown)
        self.assertNotIn('当前本人Demo版本：landscape-version',markdown)

    def test_new_candidate_joins_existing_layer_only_after_verified_case(self):
        rec=self.record(target='new-style'); new=entry(None)
        new.update(id='new-style',layer='style',source_url=rec['source']['url'],demos=[])
        rec['new_entry']=new
        merged,records,_=self.apply([rec])
        self.assertEqual(len(merged),2)
        self.assertEqual(merged[1]['layer'],'style')
        self.assertEqual(merged[1]['validation']['state'],'integrated_case_verified')
        counts,_=self.gallery.validate(merged,self.root/'docs/template-gallery',False)
        self.assertEqual(dict(counts),{'control':1,'style':1})
        rec['new_entry']['layer']='integrated'
        with self.assertRaisesRegex(ValueError,'existing layer'): self.apply([rec])

    def test_overlay_cannot_overwrite_baseline_entry(self):
        rec=self.record(); rec['new_entry']=deepcopy(self.base)
        with self.assertRaisesRegex(ValueError,'cannot overwrite'): self.apply([rec])

    def test_unreviewed_or_unlicensed_cases_are_rejected(self):
        for section,key,value in [('qa','sample_images_viewed',False),('source','official',False),
                                  ('rights','private_demo_redistribution',False)]:
            rec=self.record();rec[section][key]=value
            with self.assertRaises(ValueError): self.apply([rec])

    def test_reviewed_media_hash_mismatch_is_rejected(self):
        rec=self.record();self.media.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed after review'): self.apply([rec])

    def test_cross_entry_path_collision_is_rejected(self):
        second=deepcopy(self.base);second['id']='two'
        with self.assertRaisesRegex(ValueError,'shared across entries'):
            self.apply([self.record(),self.record('case-two','two')],[self.base,second])

    def test_baseline_missing_row_is_detected_before_overlay(self):
        for name in self.gallery.SOURCES:
            shutil.copy2(ROOT/'templates'/name,self.root/'templates'/name)
        p=self.root/'templates/motiongit-controls.json'
        data=json.loads(p.read_text(encoding='utf-8'));data['entries'].pop()
        p.write_text(json.dumps(data),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Frozen baseline counts changed'):
            self.gallery.read_sources(self.root)

    def test_strict_decode_rejects_non_video_even_with_matching_hash(self):
        # Validate the rejection path with explicit test metadata, no media render.
        with patch.object(self.gallery,'subprocess') as proc:
            proc.run.return_value.stdout=json.dumps({'streams':[{'codec_type':'audio'}],'format':{'duration':'1'}}).encode()
            with self.assertRaisesRegex(ValueError,'one video and no audio'):
                self.gallery.verify_integration_demo(self.root,self.record()['demo'],True)

    def test_homepage_separates_demo_version_from_baseline_qa(self):
        merged,records,_=self.apply([self.record()]); row=merged[0]
        home=module('build_homepage_showcase')
        asset={'kind':'local_gif','path':'fixture.gif','duration_seconds':3,'width':180,'source_demo':'fixture.mp4'}
        fragment=home.make_fragment({'entries':merged,'integrations':records},{'one':asset})
        self.assertIn('当前本人Demo版本：v2',fragment)
        self.assertIn('登记基线版本：fixture',fragment)
        self.assertIn('verified_demo',fragment)
        self.assertIn('不代表用户审美认可',fragment)
        self.assertEqual(row['validation'],self.base['validation'])

    def test_homepage_dynamic_counts_and_only_changed_demo_needs_render(self):
        home=module('build_homepage_showcase')
        row=deepcopy(self.base);row['id']='fixture'
        row['demos']=[{'kind':'own','path':'demos/cases/fixture.mp4',
                       'sha256':sha256(self.media.read_bytes()).hexdigest(),'bytes':self.media.stat().st_size}]
        out=self.root/'gif';out.mkdir();gif=out/'fixture.gif';gif.write_bytes(b'cached test GIF')
        cached={'id':'fixture','sha256':sha256(gif.read_bytes()).hexdigest(),
                'source_sha256':row['demos'][0]['sha256'],'source_demo':'old/path.mp4'}
        meta={'streams':[{'codec_type':'video','width':540,'height':960}],'format':{'duration':'6'}}
        with patch.object(home,'ROOT',self.root),patch.object(home,'GALLERY',self.root/'docs/template-gallery'),patch.object(home,'OUT',out),patch.object(home,'probe',return_value=meta),patch.object(home,'validate_gif',return_value={}),patch.object(home,'run') as render:
            result=home.build_gif(row,Path('ffmpeg'),Path('ffprobe'),cached)
            self.assertTrue(result['cache_reused']);render.assert_not_called()
            self.assertEqual(result['source_demo'],'docs/template-gallery/demos/cases/fixture.mp4')
        asset={'kind':'local_gif','path':'fixture.gif','duration_seconds':3,'width':180,'source_demo':'fixture.mp4'}
        fragment=home.make_fragment({'entries':[row],'integrations':[]},{'fixture':asset})
        self.assertIn('1 条目录',fragment);self.assertNotIn('216 条目录',fragment)


if __name__=='__main__':
    unittest.main()
