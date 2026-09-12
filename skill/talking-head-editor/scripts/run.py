"""Dispatch to the selected local checkout without inheriting another user's path."""
import json
import os
import subprocess
import sys
from pathlib import Path


def resolve_root(entry=None, environ=None):
    entry = Path(entry or __file__).resolve()
    environ = os.environ if environ is None else environ
    if environ.get('TALKING_HEAD_EDITOR_ROOT'):
        return Path(environ['TALKING_HEAD_EDITOR_ROOT']).expanduser().resolve()
    manifest = entry.parent.parent / 'installation.json'
    if manifest.is_file():
        return Path(json.loads(manifest.read_text(encoding='utf-8-sig'))['source_root']).resolve()
    for parent in entry.parents:
        if (parent / 'pyproject.toml').is_file() and (parent / 'src/talking_head_editor').is_dir():
            return parent
    raise ValueError('Set TALKING_HEAD_EDITOR_ROOT to your cloned talking-head-editor repository, or install with scripts/install_skill.py.')


def main():
    try:
        root = resolve_root()
    except (ValueError, KeyError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file() or not (root / 'pyproject.toml').is_file():
        raise SystemExit(f'Runtime missing at {root}. Run scripts/bootstrap.ps1 or configure TALKING_HEAD_EDITOR_ROOT.')
    return subprocess.call([str(python), '-m', 'talking_head_editor.cli', *sys.argv[1:]], cwd=root)


if __name__ == '__main__':
    raise SystemExit(main())
