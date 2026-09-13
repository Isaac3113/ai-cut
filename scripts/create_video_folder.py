"""Create one reversible workspace per video; this does not edit or upload media."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('01_原片', '02_自有素材', '03_参考视频', '04_剪辑工程', '05_成片', '06_历史交付')

def create(root, name, existing=False):
    root = Path(root).resolve()
    if (not name or name != name.strip() or name in {'.', '..'} or name.endswith('.')
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', name, re.I)):
        raise ValueError('Use one valid Windows folder name; do not silently change the user title')
    parent = root / '视频项目'
    target = parent / name
    # Reject an existing junction/symlink escaping the declared project.
    if not target.resolve().is_relative_to(root):
        raise ValueError('Video folder resolves outside this project')
    if target.exists():
        if not existing:
            raise FileExistsError('Video already exists; reuse it explicitly with --existing')
        if not all((target/f).is_dir() for f in FOLDERS):
            raise ValueError('Existing folder is incomplete; inspect before adopting')
        return {'directory':str(target), 'reused':True, 'files_overwritten':False}
    if existing:
        raise FileNotFoundError('Requested existing video is missing')
    target.mkdir(parents=True, exist_ok=False)
    for folder in FOLDERS: (target/folder).mkdir()
    (target/'00_视频说明.md').write_text(
        '# '+name+'\n\n原片、素材、参考片分别保存；剪辑工程放04_剪辑工程。\n'
        '每次完整交付在05_成片新建日期与版本目录，交付MP4、封面、TXT、SRT、制作说明及检查记录。\n'
        '修改同一视频沿用本文件夹，不覆盖旧版。此处仅创建目录，尚未执行剪辑或验收。\n',encoding='utf-8')
    return {'directory':str(target), 'reused':False, 'files_overwritten':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--name',required=True)
    p.add_argument('--existing',action='store_true');a=p.parse_args()
    try: result=create(a.root,a.name,a.existing)
    except (ValueError,OSError) as exc: p.exit(2,str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
