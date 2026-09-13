"""Create separate per-video Hub and local work directories; never render or upload."""
import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
FOLDERS=('01_原片','02_自有素材','03_参考视频','04_剪辑工程','05_成片','06_历史交付')

def in_onedrive(path, env=None):
    path=Path(path).resolve();env=os.environ if env is None else env
    roots=[Path(env[k]).resolve() for k in ('OneDrive','OneDriveConsumer','OneDriveCommercial') if env.get(k)]
    return any(path==root or path.is_relative_to(root) for root in roots) or any(
        part.casefold()=='onedrive' or part.casefold().startswith('onedrive - ') for part in path.parts)

def resolve_roots(hub=None,work_root=None,*,repo=ROOT,env=None):
    repo=Path(repo).resolve();env=os.environ if env is None else env
    config_path=repo/'runtime.local.json'
    config=json.loads(config_path.read_text(encoding='utf-8-sig')) if config_path.is_file() else {}
    hub=hub or env.get('TALKING_HEAD_PROJECT_HUB') or config.get('project_hub')
    if not hub:
        raise ValueError('Project Hub is not configured; provide --hub or TALKING_HEAD_PROJECT_HUB')
    local=Path(work_root or config.get('video_work_root') or repo/'work/videos').resolve()
    if in_onedrive(repo,env) or in_onedrive(local,env):
        raise ValueError('Active code and video work/cache must be outside OneDrive')
    return Path(hub).resolve(),local

def create(root,name,existing=False,*,work_root):
    hub=Path(root).resolve();work_root=Path(work_root).resolve()
    if (not name or name!=name.strip() or name in {'.','..'} or name.endswith('.')
            or re.search(r'[<>:"/\\|?*\x00-\x1f]',name)
            or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',name,re.I)):
        raise ValueError('Use one valid Windows folder name; do not silently change the user title')
    target=hub/'视频项目'/name
    work=work_root/name/'04_剪辑工程'
    if not target.resolve().is_relative_to(hub) or not work.resolve().is_relative_to(work_root):
        raise ValueError('Video folder resolves outside its declared root')
    if in_onedrive(work) or work==target or work.is_relative_to(hub):
        raise ValueError('Local editing work/cache must be separate from the Project Hub')
    if target.exists() or work.exists():
        if not existing:raise FileExistsError('Video exists; reuse it explicitly with --existing')
        if not all((target/f).is_dir() for f in FOLDERS) or not work.is_dir():
            raise ValueError('Existing Hub/work pair is incomplete; inspect before adopting')
        return {'directory':str(target),'work_directory':str(work),'reused':True,'files_overwritten':False}
    if existing:raise FileNotFoundError('Requested existing video is missing')
    # Both locations validated before either is written. Interrupted partial pairs are preserved.
    target.mkdir(parents=True,exist_ok=False);work.mkdir(parents=True,exist_ok=False)
    for folder in FOLDERS:(target/folder).mkdir()
    (target/'00_视频说明.md').write_text('# '+name+'\n\n原片、素材、参考与完整交付保存在本Project Hub。\n'
        '代码、可执行剪辑工程与缓存保存在OneDrive之外；04_剪辑工程只提供本机工程入口。\n'
        '05_成片按日期及版本交付MP4、封面、TXT、SRT、完整制作说明及检查记录，旧版不覆盖。\n',encoding='utf8')
    (target/'04_剪辑工程'/'本机剪辑工程.md').write_text('# 本机剪辑工程位置\n\n'+str(work)+'\n\n'
        '这是路径说明，不复制运行时、源码或缓存到OneDrive。换电脑先取得代码与完整工程导出，再更新本机路径。\n',encoding='utf8')
    (work/'hub-location.json').write_text(json.dumps({'project_hub':str(hub),'video_folder':str(target)},ensure_ascii=False,indent=2),encoding='utf8')
    return {'directory':str(target),'work_directory':str(work),'reused':False,'files_overwritten':False}

if __name__=='__main__':
    if hasattr(sys.stdout, 'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hub','--root',dest='hub',type=Path,help='Project Hub for media and deliveries; --root is a compatibility alias, not the code root')
    p.add_argument('--work-root',type=Path);p.add_argument('--name',required=True);p.add_argument('--existing',action='store_true');a=p.parse_args()
    try:
        hub,local=resolve_roots(a.hub,a.work_root)
        result=create(hub,a.name,a.existing,work_root=local)
    except (ValueError,OSError) as exc:p.exit(2,str(exc)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
