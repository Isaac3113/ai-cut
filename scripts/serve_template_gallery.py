"""Serve only the curated gallery on this computer, without another web framework."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
from hashlib import sha256
import json
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


def local_demo_resources(config_path, catalog_path):
    """Expose only configured owner-case movies, never a user directory."""
    manifest = {'schema': 'talking-head-local-demos/1', 'clips': {}}
    resources = {}
    if not config_path.is_file():
        return manifest, resources
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    if config.get('schema') != 'talking-head-gallery-local/1':
        raise ValueError('Invalid local gallery configuration schema')
    catalog = json.loads(catalog_path.read_text(encoding='utf-8-sig'))
    allowed = {demo['path'] for entry in catalog['entries'] for demo in entry.get('demos', [])
               if demo.get('kind') == 'own' and demo.get('integration_id') and demo.get('path')}
    media_root = Path(config['media_root']).resolve()
    if not media_root.is_dir() or not isinstance(config.get('clips'), dict):
        raise ValueError('Local media root or clip mapping is invalid')
    for demo_path, filename in config['clips'].items():
        if demo_path not in allowed or not isinstance(filename, str) or Path(filename).is_absolute():
            raise ValueError('Local clip must reference a registered owner case and a relative filename')
        movie = (media_root / filename).resolve()
        if not movie.is_relative_to(media_root) or movie.suffix.lower() != '.mp4':
            raise ValueError('Local movie must remain inside the configured media directory')
        if not movie.is_file():
            continue  # Another computer may not have synchronized the original-voice movie.
        route = 'local-owner-media/' + sha256(demo_path.encode()).hexdigest()[:24] + '.mp4'
        manifest['clips'][demo_path] = {'url': route, 'audio': True}
        resources['/' + route] = movie
    return manifest, resources


def make_handler(folder, local_manifest=None, resources=None):
    local_manifest = local_manifest or {'schema': 'talking-head-local-demos/1', 'clips': {}}
    resources = resources or {}

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(folder), **kwargs)

        def list_directory(self, path):
            self.send_error(404)

        def end_headers(self):
            self.send_header('X-Content-Type-Options', 'nosniff')
            super().end_headers()

        def do_GET(self):
            self.serve_request(head_only=False)

        def do_HEAD(self):
            self.serve_request(head_only=True)

        def serve_request(self, head_only):
            path = unquote(urlsplit(self.path).path)
            if path == '/local-demo-manifest.json':
                body = json.dumps(local_manifest, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                if not head_only:
                    self.wfile.write(body)
                return
            if path.startswith('/local-owner-media/'):
                movie = resources.get(path)
                if movie is None or not movie.is_file():
                    self.send_error(404)
                    return
                with movie.open('rb') as stream:
                    size = movie.stat().st_size
                    self.send_response(200)
                    self.send_header('Content-Type', 'video/mp4')
                    self.send_header('Content-Length', str(size))
                    self.send_header('Cache-Control', 'private, max-age=0')
                    self.end_headers()
                    if not head_only:
                        self.copyfile(stream, self.wfile)
                return
            if head_only:
                super().do_HEAD()
            else:
                super().do_GET()
    return Handler


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='本机中文剪辑模板中心')
    parser.add_argument('--port', type=int, default=8768)
    parser.add_argument('--local-config', type=Path, default=ROOT/'gallery.local.json')
    args = parser.parse_args()
    folder = ROOT / 'docs/template-gallery'
    if not (folder/'index.html').is_file():
        parser.error('请先运行 scripts/build_template_gallery.py --strict')
    try:
        manifest, resources = local_demo_resources(args.local_config, ROOT/'templates/catalog.json')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    handler = make_handler(folder, manifest, resources)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    print(f'中文模板中心：http://127.0.0.1:{args.port}/index.html', flush=True)
    print('仅本机访问；按 Ctrl+C 停止。GitHub清单位于 templates/README.zh-CN.md。', flush=True)
    print(f'已连接本机原声示例：{len(resources)}；未连接时使用库中静音样例。', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
