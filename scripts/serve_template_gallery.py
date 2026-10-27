"""Serve only the curated gallery on this computer, without another web framework."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser(description='本机中文剪辑模板中心')
    parser.add_argument('--port', type=int, default=8768)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parents[1] / 'docs/template-gallery'
    if not (folder/'index.html').is_file():
        parser.error('请先运行 scripts/build_template_gallery.py --strict')
    class Handler(SimpleHTTPRequestHandler):
        def list_directory(self, path):
            self.send_error(404)
        def end_headers(self):
            self.send_header('X-Content-Type-Options', 'nosniff')
            super().end_headers()
    handler = partial(Handler, directory=str(folder))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    print(f'中文模板中心：http://127.0.0.1:{args.port}/index.html', flush=True)
    print('仅本机访问；按 Ctrl+C 停止。GitHub清单位于 templates/README.zh-CN.md。', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
