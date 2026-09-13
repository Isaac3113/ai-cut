import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('video_folders',Path(__file__).parents[1]/'scripts/create_video_folder.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class VideoFolderTests(unittest.TestCase):
    def test_chinese_title_and_reedit_preserve_existing_media(self):
        with tempfile.TemporaryDirectory() as root:
            title='AIVD - 客户走到哪一步？系统都可以知道吗？'
            result=mod.create(root,title);folder=Path(result['directory'])
            original=folder/'01_原片'/'source.txt';original.write_text('immutable')
            self.assertEqual(folder.name,title)
            with self.assertRaises(FileExistsError):mod.create(root,title)
            self.assertTrue(mod.create(root,title,True)['reused'])
            self.assertEqual(original.read_text(),'immutable')
    def test_invalid_names_do_not_create_any_output(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ('../escape','x/y','x\\y','CON','NUL.txt','a?b','a:video','..',' bad','bad.',''):
                with self.subTest(name=name),self.assertRaises(ValueError):mod.create(root,name)
            self.assertEqual(list(Path(root).iterdir()),[])
    def test_existing_requires_real_complete_video_folder(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):mod.create(root,'missing',True)
            target=Path(root)/'视频项目'/'partial';target.mkdir(parents=True)
            with self.assertRaises(ValueError):mod.create(root,'partial',True)
