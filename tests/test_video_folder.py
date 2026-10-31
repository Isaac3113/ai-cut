import importlib.util
from pathlib import Path
import tempfile,unittest,json,subprocess,sys,os
spec=importlib.util.spec_from_file_location('video_folders',Path(__file__).parents[1]/'scripts/create_video_folder.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class VideoFolderTests(unittest.TestCase):
    def test_chinese_title_reedit_and_separate_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);hub=root/'OneDrive/hub';local=root/'active/work';title='AIVD - 客户走到哪一步？系统都可以知道吗？'
            result=mod.create(hub,title,work_root=local);folder=Path(result['directory']);work=Path(result['work_directory'])
            original=folder/'01_原片'/'source.txt';original.write_text('immutable')
            self.assertEqual(folder.name,title);self.assertTrue(work.is_relative_to(local))
            self.assertFalse(work.is_relative_to(hub))
            self.assertEqual([x.name for x in (folder/'04_剪辑工程').iterdir()],['本机剪辑工程.md'])
            self.assertFalse((folder/'05_成片').exists());self.assertFalse((folder/'06_历史交付').exists())
            self.assertIn('delivery_library.py',(folder/'00_视频说明.md').read_text(encoding='utf-8'))
            with self.assertRaises(FileExistsError):mod.create(hub,title,work_root=local)
            self.assertTrue(mod.create(hub,title,True,work_root=local)['reused']);self.assertEqual(original.read_text(),'immutable')
    def test_invalid_names_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ('../escape','x/y','x\\y','CON','NUL.txt','a?b','a:video','..',' bad','bad.',''):
                with self.subTest(name=name),self.assertRaises(ValueError):mod.create(root/'hub',name,work_root=root/'work')
            self.assertEqual(list(root.iterdir()),[])
    def test_existing_requires_complete_hub_and_local_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(FileNotFoundError):mod.create(root/'hub','missing',True,work_root=root/'work')
            target=root/'hub/视频项目/partial';target.mkdir(parents=True)
            with self.assertRaises(ValueError):mod.create(root/'hub','partial',True,work_root=root/'work')
    def test_legacy_optional_delivery_folders_are_not_required_or_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);result=mod.create(root/'hub','legacy',work_root=root/'work')
            target=Path(result['directory'])
            (target/'05_成片').mkdir();(target/'06_历史交付').mkdir()
            receipt=target/'05_成片'/'keep.txt';receipt.write_text('keep legacy bytes')
            self.assertTrue(mod.create(root/'hub','legacy',True,work_root=root/'work')['reused'])
            self.assertEqual(receipt.read_text(),'keep legacy bytes')
    def test_reopening_unified_name_uses_original_pointer_and_frozen_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);created=mod.create(root/'hub','AIVD 11 - 旧主题',work_root=root/'work')
            target=Path(created['directory']);old_work=Path(created['work_directory'])
            frozen=root/'work'/'001-frozen'/'04_剪辑工程';frozen.mkdir(parents=True)
            pointer=target/'04_剪辑工程'/'本机剪辑工程.md'
            pointer.write_text('# 工作入口\n\n'+str(frozen)+'\n',encoding='utf-8')
            registry=root/'mapping.json';registry.write_text(json.dumps({'Projects':[{'ID':'AIVD-027',
                'OriginalName':target.name,'OriginalProject':str(target),
                'DestinationName':'AIVD-027 - Codex剪辑 - 新展示名'}]}),encoding='utf-8')
            for requested in ('AIVD-027','AIVD-027 - Codex剪辑 - 新展示名',target.name):
                result=mod.create(root/'hub',requested,True,work_root=root/'work',registry=registry)
                self.assertEqual(Path(result['directory']),target)
                self.assertEqual(Path(result['work_directory']),frozen)
                self.assertTrue(result['reused'])
            self.assertTrue(old_work.is_dir())
            self.assertFalse((root/'work'/'AIVD-027').exists())
            self.assertFalse((root/'hub'/'视频项目'/'AIVD-027').exists())
    def test_delivery_library_is_not_used_as_working_hub(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'code';repo.mkdir();delivery=root/'OneDrive'/'library'
            (repo/'runtime.local.json').write_text(json.dumps({'project_hub':str(delivery),'delivery_library_root':str(delivery)}))
            with self.assertRaisesRegex(ValueError,'not the working Project Hub'):
                mod.resolve_roots(repo=repo,env={})
            self.assertFalse(delivery.exists())
    def test_mapped_media_without_original_work_entry_creates_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);registry=root/'mapping.json'
            registry.write_text(json.dumps({'Projects':[{'ID':'AIVD-010',
                'OriginalProject':None,'DestinationName':'AIVD-010 - Higgsfield - 原作品'}]}),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'no original editing-project entry'):
                mod.create(root/'hub','AIVD-010',True,work_root=root/'work',registry=registry)
            self.assertEqual({p.name for p in root.iterdir()},{'mapping.json'})
    def test_onedrive_work_is_rejected_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for work in (root/'OneDrive/work',root/'OneDrive - Team/work',root/'hub/local'):
                with self.subTest(work=work),self.assertRaises(ValueError):mod.create(root/'hub','test',work_root=work)
            self.assertEqual(list(root.iterdir()),[])
    def test_cli_root_resolution_never_defaults_hub_to_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'code';repo.mkdir();hub=root/'OneDrive/hub'
            with self.assertRaises(ValueError):mod.resolve_roots(repo=repo,env={})
            (repo/'runtime.local.json').write_text(json.dumps({'project_hub':str(hub)}))
            self.assertEqual(mod.resolve_roots(repo=repo,env={}), (hub,repo/'work/videos'))
            override=root/'alternate';self.assertEqual(mod.resolve_roots(override,repo=repo,env={})[0],override)
            self.assertEqual(mod.resolve_roots(repo=repo,env={'TALKING_HEAD_PROJECT_HUB':str(override)})[0],override)
    def test_active_repo_and_custom_onedrive_root_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):mod.resolve_roots(root/'hub',repo=root/'OneDrive/code',env={})
            with self.assertRaises(ValueError):mod.resolve_roots(root/'hub',root/'cloud/work',repo=root/'code',env={'OneDrive':str(root/'cloud')})

    def test_cli_chinese_output_with_legacy_windows_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=subprocess.run([sys.executable,str(Path(__file__).parents[1]/'scripts/create_video_folder.py'),
                '--hub',str(root/'hub'),'--work-root',str(root/'work'),'--name','AIVD - 中文主题？'],
                env={**os.environ,'PYTHONIOENCODING':'cp1252','PYTHONUTF8':'0'},capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf8',errors='replace'))
            self.assertEqual(Path(json.loads(result.stdout.decode('utf8'))['directory']).name,'AIVD - 中文主题？')
