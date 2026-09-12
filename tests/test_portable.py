import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from talking_head_editor.portable import package_manifest,restore_package
from talking_head_editor.render import seal
from talking_head_editor.util import EditorError,file_hash
from talking_head_editor.visuals import write_captions
from talking_head_editor.timeline import default_plan


class PortableTests(unittest.TestCase):
    def test_external_raw_media_requires_explicit_redistribution(self):
        with tempfile.TemporaryDirectory() as t:
            job=Path(t);src=job/'source.mp4';stock=job/'stock.mp4';owned=job/'diagram.mp4'
            for f in (src,stock,owned):f.write_bytes(f.name.encode())
            p={'source':{'path':'source.mp4','sha256':file_hash(src)},'assets':{
                'stock':{'path':'stock.mp4','sha256':file_hash(stock),'license':{'kind':'free'}},
                'own':{'path':'diagram.mp4','sha256':file_hash(owned),'license':{'kind':'provided','redistribute_raw':True}}}}
            files,manifest=package_manifest(job,p,{src,stock,owned},'external')
            self.assertEqual(files,{owned});self.assertEqual(len(manifest['withheld']),2)
            self.assertFalse(manifest['ready_to_rerender'])
            self.assertEqual(package_manifest(job,p,{src,stock,owned},'internal')[0],{src,stock,owned})

    def test_restore_new_directory_checks_hash_and_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'data.txt';src.write_text('real content');good=root/'good.zip'
            m={'dependencies':[{'path':'data.txt','sha256':file_hash(src)}],'withheld':[]}
            with zipfile.ZipFile(good,'w') as z:
                z.write(src,'data.txt');z.writestr('DEPENDENCIES.json',json.dumps(m))
            r=restore_package(good,root/'fresh');self.assertEqual(r['verified_files'],1)
            self.assertFalse(r['rerender_verified'])
            with self.assertRaises(EditorError):restore_package(good,root/'fresh')
            bad=root/'bad.zip'
            with zipfile.ZipFile(bad,'w') as z:
                z.writestr('../unsafe','bad');z.writestr('DEPENDENCIES.json',json.dumps(m))
            with self.assertRaises(EditorError):restore_package(bad,root/'unsafe-dest')
            self.assertFalse((root/'unsafe-dest').exists())

    def test_corrupt_video_is_not_given_a_valid_cache_seal(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'clip.mp4';path.write_bytes(b'not really video')
            with patch('talking_head_editor.render.probe',return_value={}),patch('talking_head_editor.render.run',side_effect=EditorError('process_failed','corrupt')):
                with self.assertRaises(EditorError):seal(path,'key')
            self.assertFalse(Path(str(path)+'.json').exists())

    def test_light_background_changes_ass_only_not_spoken_srt(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t);cue={'start':0.,'end':2.,'text':'如果未回复','lines':['如果未回复']};style=default_plan(2,0)['style']
            write_captions(path,[cue],1920,1080,style)
            original=(path/'captions.srt').read_bytes()
            write_captions(path,[cue],1920,1080,style,theme_ranges=[{'start':.5,'end':1.5,'theme':'dark'}])
            self.assertEqual(original,(path/'captions.srt').read_bytes())
            ass=(path/'captions.ass').read_text(encoding='utf-8-sig')
            self.assertEqual(ass.count('Dialogue:'),3);self.assertIn(r'\1c&H003D2F17&\bord0',ass)

    def test_secret_filenames_are_case_insensitive_without_reading_contents(self):
        with tempfile.TemporaryDirectory() as t:
            job=Path(t)
            p={'source':{'path':'source.mp4','sha256':'fixture'},'assets':{}}
            for name in ('.env','.ENV','.ENV.production','Runtime.Local.JSON','font.TTF'):
                with self.subTest(name=name), patch('talking_head_editor.portable.file_hash') as hashed:
                    with self.assertRaises(EditorError) as error:
                        package_manifest(job,p,{job/'references'/name},'external')
                    self.assertEqual(error.exception.code,'unsafe_package_file')
                    hashed.assert_not_called()

    def rough_handoff_fixture(self,root):
        from talking_head_editor.util import atomic_json
        from talking_head_editor.workflow import structure_fingerprint
        job=root/'job';source=job/'media/source.mp4'
        source.parent.mkdir(parents=True);source.write_bytes(b'source fixture, not playable')
        p={'schema_version':1,'revision':2,'fixture':True,'assets':{},'transcript':{'sha256':'words'},
           'plan':default_plan(5.5,1),'source':{'path':'media/source.mp4','sha256':file_hash(source),
            'duration':5.5,'probe':{'streams':[{'codec_type':'video','width':1920,'height':1080}]}}}
        records={}
        for mode in ('draft','rough'):
            video=job/'renders'/mode/'landscape'/(mode+'.mp4')
            video.parent.mkdir(parents=True);video.write_bytes((mode+' fixture, not playable').encode())
            for name,text in (('captions.ass','ASS fixture'),('captions.srt','SRT fixture'),('captions.json','[]')):
                (video.parent/name).write_text(text,encoding='utf8')
            records[mode]={'path':video.relative_to(job).as_posix(),'sha256':file_hash(video),
                           'subtitles':(video.parent/'captions.srt').relative_to(job).as_posix()}
        final={'schema_version':1,'revision':2,'complete':True,'fixture':True,'mode':'draft','fingerprint':'draft',
               'requested_formats':['landscape'],'files':{'landscape':records['draft']},'expected_duration':5.}
        rough={'schema_version':1,'revision':1,'complete':True,'mode':'rough','fingerprint':'rough',
               'structure_fingerprint':structure_fingerprint(p),'files':{'landscape':records['rough']}}
        atomic_json(job/'project.json',p);atomic_json(job/'latest-render.json',final)
        atomic_json(job/'latest-rough.json',rough)
        return job,p,rough

    def test_internal_package_restores_actual_current_rough_and_all_sidecars(self):
        from talking_head_editor.quality import package
        from talking_head_editor.workflow import workflow_status
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);job,p,rough=self.rough_handoff_fixture(root)
            target=root/'handoff.zip';package(job,target,draft=True)
            required={'latest-rough.json',rough['files']['landscape']['path'],
                      'renders/rough/landscape/captions.ass','renders/rough/landscape/captions.srt',
                      'renders/rough/landscape/captions.json'}
            with zipfile.ZipFile(target) as archive:
                self.assertTrue(required.issubset(set(archive.namelist())))
                manifest=json.loads(archive.read('DEPENDENCIES.json'))
                self.assertTrue(required.issubset({d['path'] for d in manifest['dependencies']}))
                self.assertEqual(manifest['rough_export']['status'],'current_export')
                self.assertEqual(manifest['rough_export']['continuous_review'],'unverified')
            restored=root/'restored';receipt=restore_package(target,restored)
            self.assertFalse(receipt['rerender_verified'])
            status=workflow_status(restored)
            self.assertTrue(status['rough_render_valid'])
            self.assertEqual(status['rough_watched']['status'],'unverified')

    def test_stale_or_incomplete_rough_is_omitted_and_explicitly_marked(self):
        from talking_head_editor.quality import package
        from talking_head_editor.util import atomic_json
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);job,p,rough=self.rough_handoff_fixture(root)
            for name,change,status in [('stale',{'structure_fingerprint':'old-structure'},'stale'),
                                       ('incomplete',{'complete':False},'incomplete')]:
                atomic_json(job/'latest-rough.json',{**rough,**change})
                target=root/(name+'.zip');package(job,target,draft=True)
                with zipfile.ZipFile(target) as archive:
                    self.assertNotIn('latest-rough.json',archive.namelist())
                    self.assertNotIn(rough['files']['landscape']['path'],archive.namelist())
                    manifest=json.loads(archive.read('DEPENDENCIES.json'))
                    self.assertFalse(manifest['rough_export']['included'])
                    self.assertEqual(manifest['rough_export']['status'],status)

    def test_rough_package_rejects_changed_video_unsafe_pointer_or_missing_sidecar(self):
        import copy
        from talking_head_editor.quality import package
        from talking_head_editor.util import atomic_json
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);job,p,rough=self.rough_handoff_fixture(root)
            bad=copy.deepcopy(rough);bad['files']['landscape']['sha256']='wrong'
            cases=[('hash',bad,'rough_package_changed')]
            bad=copy.deepcopy(rough);bad['files']['landscape']['path']='../outside.mp4'
            cases.append(('path',bad,'unsafe_path'))
            bad=copy.deepcopy(rough);bad['files']['landscape']['subtitles']='renders/draft/landscape/captions.srt'
            cases.append(('subtitle',bad,'rough_package_pointer'))
            bad=copy.deepcopy(rough);bad['files']={}
            cases.append(('variants',bad,'rough_package_variants'))
            for name,record,code in cases:
                atomic_json(job/'latest-rough.json',record);target=root/(name+'.zip')
                with self.subTest(name=name),self.assertRaises(EditorError) as error:package(job,target,draft=True)
                self.assertEqual(error.exception.code,code);self.assertFalse(target.exists())
            atomic_json(job/'latest-rough.json',rough)
            missing=job/'renders/rough/landscape/captions.ass'
            self.assertTrue(missing.is_relative_to(root));missing.unlink()
            with self.assertRaises(EditorError) as error:package(job,root/'missing.zip',draft=True)
            self.assertEqual(error.exception.code,'rough_package_sidecars')



if __name__=='__main__':unittest.main()
