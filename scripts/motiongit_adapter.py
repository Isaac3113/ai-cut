"""Run the verified official entry; never unpack personal data or protected code."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
# Independently checked against the fixed official HTTPS runtime metadata.
KNOWN_HELPERS = {'7004609ddbc0ccf6451beeb477aff0d3c85bda74f902e5922465c85cd347f6f3': '1.0.0-rc.50'}
PUBLIC_FILES = ('00-START-HERE.md', 'README.md', 'assistant/guide.json',
                'assistant/motion.mjs', 'assistant/BUILD.json', 'assistant/THIRD-PARTY-NOTICES.txt')
RUN_OPERATIONS = {'setup', 'doctor', 'capabilities', 'check-params',
                  'plan', 'prepare', 'preview', 'render'}


def bootstrap(package: Path, destination: Path):
    with zipfile.ZipFile(package) as archive:
        helper = archive.read('assistant/motion.mjs')
        digest = sha256(helper).hexdigest()
        if digest not in KNOWN_HELPERS:
            raise ValueError('Unknown helper hash: verify fixed official HTTPS metadata before updating this adapter')
        folder = destination / KNOWN_HELPERS[digest]
        for name in PUBLIC_FILES:
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = archive.read(name)
            if not path.exists() or path.read_bytes() != raw:
                path.write_bytes(raw)
        return folder/'assistant/motion.mjs', KNOWN_HELPERS[digest]


def selected_run_operation(arguments):
    # Use one documented form; an allowed word inside an API payload is not
    # evidence that the selected command itself is allowed.
    if len(arguments) < 3 or arguments[0] != '--instance' or not arguments[1]:
        raise ValueError('run requires --instance <local-instance> <operation>')
    operation = arguments[2]
    if operation not in RUN_OPERATIONS or '--instance' in arguments[3:]:
        raise ValueError('run operation is not allowed by this local adapter')
    return operation


def main(argv=None):
    parser=argparse.ArgumentParser(description='MotionGit官方个人包的本机适配入口，不含账号凭据')
    parser.add_argument('--config',type=Path,default=ROOT/'motiongit.local.json')
    parser.add_argument('--package',type=Path)
    parser.add_argument('--node',type=Path)
    parser.add_argument('action',choices=['start','new','read','contract','run'])
    parser.add_argument('arguments',nargs=argparse.REMAINDER)
    args=parser.parse_args(argv)
    config=json.loads(args.config.read_text(encoding='utf-8')) if args.config.is_file() else {}
    package=args.package or (Path(config['package']) if config.get('package') else None)
    if not package or not package.is_file():
        parser.error('需要自己的原始.motion；使用--package或本机motiongit.local.json指定，不粘贴Key')
    arguments=args.arguments[1:] if args.arguments[:1]==['--'] else args.arguments
    if args.action=='run':
        try:
            selected_run_operation(arguments)
        except ValueError as error:
            parser.error(str(error))
    node=args.node or (Path(config['node']) if config.get('node') else None)
    if node is None:
        found=shutil.which('node')
        node=Path(found) if found else None
    if not node or not node.is_file():
        parser.error('需要Node.js22+，初次setup使用含npm的标准安装或便携版')
    version=subprocess.check_output([str(node),'--version'],text=True).strip()
    if int(version.lstrip('v').split('.')[0])<22:
        parser.error('Node.js版本低于22')
    helper,helper_version=bootstrap(package.resolve(),ROOT/'.runtime/motiongit')
    env=os.environ.copy()
    env['PYTHONUTF8']='1'
    env['ADU_PYTHON']=sys.executable
    env['PATH']=str(node.parent)+os.pathsep+str(Path(sys.executable).parent)+os.pathsep+str(ROOT/'.runtime/ffmpeg/bin')+os.pathsep+env.get('PATH','')
    folder=ROOT/'work/motiongit-runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    result=subprocess.run([str(node),str(helper),args.action,str(package.resolve()),*arguments],
                          env=env,capture_output=True)
    (folder/'result.json').write_bytes(result.stdout)
    (folder/'stderr.txt').write_bytes(result.stderr)
    # Account IDs and raw helper output stay in the ignored local record.
    print(json.dumps({'exit_code':result.returncode,'helper_version':helper_version,
                      'result_file':str(folder/'result.json'),'stderr_file':str(folder/'stderr.txt')},ensure_ascii=False))
    return result.returncode


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,zipfile.BadZipFile) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(2)
