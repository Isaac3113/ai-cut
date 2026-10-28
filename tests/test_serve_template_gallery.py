import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from http.server import ThreadingHTTPServer
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/serve_template_gallery.py'
spec = importlib.util.spec_from_file_location('serve_template_gallery', SCRIPT)
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)


class LocalOwnerMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root/'owner'
        self.media.mkdir()
        self.movie = self.media/'original-voice.mp4'
        self.movie.write_bytes(b'local routing fixture; not a decoded-media assertion')
        (self.media/'unregistered.mp4').write_bytes(b'not authorized by mapping')
        self.key = 'demos/integrated/owner-case/portrait.mp4'
        self.catalog = self.root/'catalog.json'
        self.catalog.write_text(json.dumps({'entries':[{'demos':[
            {'kind':'own','integration_id':'owner-case','path':self.key},
            {'kind':'own','path':'demos/logo.mp4'}]}]}), encoding='utf-8')
        self.config = self.root/'gallery.local.json'

    def configure(self, clips=None):
        self.config.write_text(json.dumps({'schema':'talking-head-gallery-local/1',
            'media_root':str(self.media),'clips':clips or {self.key:self.movie.name}}),encoding='utf-8')
        return gallery.local_demo_resources(self.config,self.catalog)

    def test_missing_config_and_missing_movie_leave_silent_catalog_available(self):
        manifest, resources = gallery.local_demo_resources(self.config,self.catalog)
        self.assertEqual(manifest['clips'],{})
        self.assertEqual(resources,{})
        manifest, resources = self.configure({self.key:'missing.mp4'})
        self.assertEqual(manifest['clips'],{})
        self.assertEqual(resources,{})

    def test_reject_unregistered_case_absolute_path_and_directory_escape(self):
        outside=self.root/'outside.mp4'
        outside.write_bytes(b'outside')
        for mapping in [{self.key:'../outside.mp4'}, {self.key:str(outside)},
                        {'demos/logo.mp4':self.movie.name}, {'demos/unknown.mp4':self.movie.name}]:
            with self.subTest(mapping=mapping),self.assertRaises(ValueError):
                self.configure(mapping)

    def test_http_manifest_and_movie_expose_only_exact_mapped_resource(self):
        manifest, resources = self.configure()
        self.assertNotIn(str(self.media),json.dumps(manifest))
        static = self.root/'gallery'
        static.mkdir()
        (static/'index.html').write_text('curated gallery',encoding='utf-8')
        handler = gallery.make_handler(static,manifest,resources)
        server = ThreadingHTTPServer(('127.0.0.1',0),handler)
        thread=Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base=f'http://127.0.0.1:{server.server_port}'
        with urlopen(base+'/local-demo-manifest.json',timeout=2) as response:
            self.assertEqual(json.load(response),manifest)
            self.assertEqual(response.headers['Cache-Control'],'no-store')
        route=manifest['clips'][self.key]['url']
        with urlopen(base+'/'+route,timeout=2) as response:
            self.assertEqual(response.read(),self.movie.read_bytes())
            self.assertEqual(response.headers['Content-Type'],'video/mp4')
        with urlopen(Request(base+'/'+route,method='HEAD'),timeout=2) as response:
            self.assertEqual(response.read(),b'')
            self.assertEqual(int(response.headers['Content-Length']),self.movie.stat().st_size)
        for path in ['/local-owner-media/unregistered.mp4','/local-owner-media/../outside.mp4',
                     '/local-owner-media/','/owner/unregistered.mp4','/gallery.local.json']:
            with self.subTest(path=path),self.assertRaises(HTTPError) as error:
                urlopen(base+path,timeout=2)
            self.assertEqual(error.exception.code,404)


if __name__=='__main__':
    unittest.main()
