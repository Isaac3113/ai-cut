"""Install a private runtime; never modify machine PATH or delete directories."""
import argparse
import hashlib
import json
import os
import re
import urllib.request
import venv
import zipfile
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--root', required=True)
root = Path(p.parse_args().root).resolve()
if not (root / 'pyproject.toml').is_file():
    raise SystemExit('Expected project root containing pyproject.toml')
runtime = root / '.runtime'
runtime.mkdir(exist_ok=True)
bin_dir = runtime / 'ffmpeg' / 'bin'
receipt_file = runtime / 'ffmpeg-receipt.json'
tested_path=root/'03_Documentation/Knowledge_Base/runtime-versions.json'
tested=json.loads(tested_path.read_text(encoding='utf-8')).get('ffmpeg_receipt') if tested_path.exists() else None
if not all((bin_dir / name).is_file() for name in ('ffmpeg.exe', 'ffprobe.exe')):
    url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    print('Downloading FFmpeg build and publisher checksum', flush=True)
    with urllib.request.urlopen(url + '.sha256', timeout=60) as response:
        checksum = response.read().decode().strip().split()[0]
    if not re.fullmatch('[0-9a-fA-F]{64}', checksum):
        raise SystemExit('Invalid FFmpeg checksum response')
    if tested and checksum.lower()!=tested['archive_sha256'].lower():
        raise SystemExit('Publisher build changed since tested version. Obtain the recorded build or review and test the new version before updating the runtime receipt.')
    archive = runtime / 'ffmpeg-download.zip'
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != checksum.lower():
        with urllib.request.urlopen(url, timeout=120) as response, archive.open('wb') as f:
            while chunk := response.read(1024*1024):
                f.write(chunk)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum.lower():
        raise SystemExit('FFmpeg SHA256 mismatch; no extraction performed')
    bin_dir.mkdir(parents=True, exist_ok=True)
    binaries = {}
    with zipfile.ZipFile(archive) as z:
        for name in ('ffmpeg.exe', 'ffprobe.exe'):
            member = [x for x in z.namelist() if x.endswith('/bin/' + name)]
            if len(member) != 1:
                raise SystemExit('Unexpected archive structure')
            payload = z.read(member[0])
            (bin_dir / name).write_bytes(payload)
            binaries[name] = hashlib.sha256(payload).hexdigest()
        licenses = [x for x in z.namelist() if x.endswith('LICENSE') or x.endswith('LICENSE.txt')]
        if licenses:
            (bin_dir.parent / 'LICENSE.txt').write_bytes(z.read(licenses[0]))
    receipt_file.write_text(json.dumps({'url':url,'archive_sha256':checksum,'binaries':binaries}, indent=2), encoding='utf-8')
elif receipt_file.exists():
    receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
    for name, expected in receipt['binaries'].items():
        if tested and expected!=tested['binaries'][name]:
            raise SystemExit('Installed build differs from the project tested version')
        if hashlib.sha256((bin_dir/name).read_bytes()).hexdigest() != expected:
            raise SystemExit('Installed FFmpeg changed; inspect before reinstalling')
else:
    raise SystemExit('Untracked FFmpeg binaries found without installation receipt; inspect them first')
venv_python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
if not venv_python.exists():
    print('Creating isolated Python environment', flush=True)
    venv.EnvBuilder(with_pip=True).create(root / '.venv')
config = {'ffmpeg':str(bin_dir/'ffmpeg.exe'),'ffprobe':str(bin_dir/'ffprobe.exe')}
config_path = root / 'runtime.local.json'
if config_path.exists():
    config = {**config, **json.loads(config_path.read_text(encoding='utf-8'))}
config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
print('Runtime paths ready', flush=True)
