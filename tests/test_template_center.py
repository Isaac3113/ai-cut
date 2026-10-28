from copy import deepcopy
import json
import shutil
import subprocess
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


class GalleryDemoSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gallery=module('build_template_gallery')
        candidate=Path(shutil.which('node') or ROOT/'work/motiongit-evaluation-20261026/prototype/node-v24.19.0-win-x64/node.exe')
        if not candidate.is_file():
            raise unittest.SkipTest('Node is required to execute the real browser selection functions')
        cls.node=candidate
        cls.model=cls.gallery.HTML.split('// BEGIN_DEMO_MODEL',1)[1].split('\n',1)[1].split('// END_DEMO_MODEL',1)[0]

    def setUp(self):
        self.entry={
            'id':'style-one','ratio':'9:16',
            'integrations':[
                {'id':'portrait-case','project_id':'owner-demo','source':{'version':'portrait-version','package_id':'portrait-package'},'qa':{'state':'verified_demo','scope':'portrait scope'},'invocation':{'inputs_zh':['actual portrait inputs'],'command':'render portrait'}},
                {'id':'landscape-case','project_id':'owner-demo','source':{'version':'landscape-version','package_id':'landscape-package'},'qa':{'state':'verified_demo','scope':'landscape scope'},'invocation':{'inputs_zh':['actual landscape inputs'],'command':'render landscape'}},
            ],
            'demos':[
                {'kind':'own','integration_id':'portrait-case','path':'demos/owner/portrait.mp4','ratio':'9:16'},
                {'kind':'own','integration_id':'landscape-case','path':'demos/owner/landscape.mp4','ratio':'16:9'},
                {'kind':'official','url':'https://official.example/demo.mp4','ratio':'9:16'},
                {'kind':'own','path':'demos/controls/logo.mp4','ratio':'16:9'},
                {'kind':'source_render','path':'demos/code.mp4','ratio':'1:1'},
                {'kind':'own','subject':'owner','path':'demos/legacy-owner.mp4','ratio':'1:1'},
            ]}

    def evaluate(self,statement,payload=None,extra=''):
        program=self.model+'\n'+extra+'\nconst input=JSON.parse(require("fs").readFileSync(0,"utf8"));\n'+statement
        proc=subprocess.run([str(self.node),'-e',program],input=json.dumps(payload if payload is not None else self.entry),capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(proc.returncode,0,proc.stderr)
        return json.loads(proc.stdout)

    def test_source_filter_selects_the_playing_demo_not_only_the_card(self):
        result=self.evaluate("const official=selectedDemo(input,'official','',input.demos[0].path);console.log(JSON.stringify({src:demoKey(official),case:demoCase(input,official),other:candidateDemos(input,'other').map(d=>demoKey(d))}));")
        self.assertEqual(result['src'],'https://official.example/demo.mp4')
        self.assertIsNone(result['case'])
        self.assertEqual(result['other'],['demos/controls/logo.mp4','demos/code.mp4'])

    def test_ratio_switch_does_not_reuse_an_incompatible_selected_demo(self):
        result=self.evaluate("console.log(JSON.stringify({landscape:demoKey(selectedDemo(input,'own','16:9',input.demos[0].path)),portrait:demoKey(selectedDemo(input,'own','9:16',input.demos[1].path)),none:selectedDemo(input,'own','4:3',input.demos[0].path)}));")
        self.assertEqual(result['landscape'],'demos/owner/landscape.mp4')
        self.assertEqual(result['portrait'],'demos/owner/portrait.mp4')
        self.assertIsNone(result['none'])

    def test_personal_identity_requires_registered_evidence_or_explicit_subject(self):
        result=self.evaluate("console.log(JSON.stringify({own:candidateDemos(input,'own').map(d=>demoKey(d)),ordinary:demoSource(input,input.demos[3]),remote:demoSource(input,{kind:'own',subject:'owner',url:'https://example.com/avatar.mp4'}),render:demoSource(input,{kind:'source_render',subject:'owner',path:'demos/render.mp4'})}));")
        self.assertEqual(result['own'],['demos/owner/portrait.mp4','demos/owner/landscape.mp4','demos/legacy-owner.mp4'])
        self.assertEqual(result['ordinary'],'other')
        self.assertEqual(result['remote'],'other')
        self.assertEqual(result['render'],'other')

    def test_local_manifest_accepts_only_registered_paths_and_opaque_relative_media(self):
        fixture={'entry':self.entry,'manifest':{'schema':'talking-head-local-demos/1','clips':{
            'demos/owner/portrait.mp4':{'url':'local-owner-media/abc_123-xyz.mp4','audio':True},
            'demos/owner/landscape.mp4':{'url':'https://other.example/upload.mp4','audio':True},
            'demos/controls/logo.mp4':{'url':'local-owner-media/logo.mp4','audio':True},
            'demos/legacy-owner.mp4':{'url':'local-owner-media/legacy.mp4','audio':True},
            'unknown-private.mp4':{'url':'local-owner-media/unknown.mp4','audio':True}}}}
        result=self.evaluate("console.log(JSON.stringify(localOverrides(input.manifest,[input.entry])));",fixture)
        self.assertEqual(result,{'demos/owner/portrait.mp4':{'url':'local-owner-media/abc_123-xyz.mp4','audio':True}})

    def test_local_manifest_rejects_traversal_queries_and_non_boolean_audio(self):
        fixture={'entry':self.entry,'urls':['../private.mp4','local-owner-media/../private.mp4','local-owner-media/%2e%2e.mp4','local-owner-media/a.mp4?path=private','local-owner-media/nested/a.mp4','//other.example/a.mp4']}
        result=self.evaluate("const key=input.entry.demos[0].path;const accepted=input.urls.map(url=>Object.keys(localOverrides({schema:'talking-head-local-demos/1',clips:{[key]:{url,audio:true}}},[input.entry])).length);const stringAudio=localOverrides({schema:'talking-head-local-demos/1',clips:{[key]:{url:'local-owner-media/a.mp4',audio:'true'}}},[input.entry]);console.log(JSON.stringify({accepted,stringAudio}));",fixture)
        self.assertEqual(result['accepted'],[0]*6)
        self.assertEqual(result['stringAudio'],{})

    def test_missing_manifest_keeps_silent_library_and_valid_manifest_enables_local_voice(self):
        result=self.evaluate("const d=input.demos[0],fallback=demoPlayback(input,d,localOverrides(null,[input]));const valid=localOverrides({schema:'talking-head-local-demos/1',clips:{[d.path]:{url:'local-owner-media/voice.mp4',audio:true}}},[input]);console.log(JSON.stringify({fallback,voice:demoPlayback(input,d,valid),official:demoPlayback(input,input.demos[2],valid)}));")
        self.assertEqual(result['fallback']['src'],'demos/owner/portrait.mp4')
        self.assertFalse(result['fallback']['audio'])
        self.assertIn('静音库样例',result['fallback']['label'])
        self.assertEqual(result['voice']['src'],'local-owner-media/voice.mp4')
        self.assertTrue(result['voice']['audio'])
        self.assertIn('原声版',result['voice']['label'])
        self.assertEqual(result['official']['src'],'https://official.example/demo.mp4')

    def test_selected_demo_metadata_tracks_its_own_integration(self):
        self.entry['demos'][1]['description_zh']='18.5秒静音；原始Git登记说明。'
        extra="const esc=x=>String(x),overrides={'demos/owner/landscape.mp4':{url:'local-owner-media/voice.mp4',audio:true}};\n"+'\n'.join(line for line in self.gallery.HTML.splitlines() if line.startswith(('function integrationInfo(', 'function demoMetadata(')))
        result=self.evaluate("console.log(JSON.stringify({official:demoMetadata(input,input.demos[2]),landscape:demoMetadata(input,input.demos[1])}));",extra=extra)
        self.assertNotIn('当前本人Demo版本',result['official'])
        self.assertNotIn('portrait-version',result['official'])
        self.assertIn('landscape-version',result['landscape'])
        self.assertIn('landscape scope',result['landscape'])
        self.assertNotIn('portrait scope',result['landscape'])
        self.assertIn('原声版 · 仅本机',result['landscape'].split('<details>',1)[0])
        self.assertNotIn('18.5秒静音',result['landscape'].split('<details>',1)[0])
        self.assertIn('Git库样例登记说明：18.5秒静音；原始Git登记说明。',result['landscape'])

    def test_real_browser_script_compiles_and_ratio_uses_actual_demo_dimensions(self):
        script=self.gallery.HTML.split('<script>',1)[1].split('</script>',1)[0].replace('__DATA__','{"entries":[],"previews":[]}').replace('__LAYERS__','{}')
        result=self.evaluate("new (require('vm').Script)(input.script);console.log(JSON.stringify({ratio:demoRatio({ratio:'9:16'},{width:1920,height:1080}),invalid:demoRatio({}, {ratio:'NaN:1'})}));",{'script':script})
        self.assertEqual(result,{'ratio':'16:9','invalid':'unknown'})


if __name__=='__main__':
    unittest.main()
