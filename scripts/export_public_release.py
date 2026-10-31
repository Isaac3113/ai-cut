"""Export a reviewed source snapshot without private Git history or media.

This command is offline. It does not create repositories, publish, or copy .git.
Only tracked source under declared roots is eligible; output must be new.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOP={'.gitignore','.gitattributes','LICENSE','THIRD_PARTY.md','pyproject.toml','requirements.lock.txt'}
PREFIXES=('src/','tests/','schemas/','skill/','skill-adapters/','profiles/','publishing/')
SCRIPTS={'bootstrap.ps1','bootstrap_runtime.py','install_skill.py','install_extensions.py',
 'adapt_jianying_skill.py','build_jianying_project.py','audit_chatcut_snapshot.py',
 'verify_review_media.py','video_use_review.py','smoke_asr.py','smoke_asr_core.py',
 'audit_visual_contract.py','delivery_names.py','delivery_library.py','export_final_subtitles.py','create_video_folder.py','package_social_delivery.py','smoke_media.py','smoke_motion.py','smoke_render.py','export_student_skill.py','export_public_release.py'}
EXTENSIONS=('extensions/remotion-vd44/','extensions/hyperframes-vd44/','extensions/chatcut-vd44/')
EXCLUDE={'extensions/hyperframes-vd44/assets/gsap.min.js',
 'extensions/hyperframes-vd44/meta.json','extensions/remotion-vd44/src/Composition.tsx'}
SUFFIXES={'.py','.ps1','.md','.txt','.json','.yaml','.yml','.toml','.html','.js','.mjs','.jsx','.ts','.tsx'}
SPECIAL={'.gitignore','.gitattributes','.prettierrc','LICENSE'}
SECRET_PATTERNS=(rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{30,}',
 rb'sk-(?:proj-)?[A-Za-z0-9_-]{30,}',rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 rb'editor-boot-token=[A-Za-z0-9_-]{10,}',rb'Authorization: Bearer [A-Za-z0-9_.-]{20,}')

def safe_path(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:
        raise ValueError('Unsafe release path')
    if any(part.lower().startswith('.env') or part.lower() in
           {'.git','.venv','.runtime','node_modules','jobs','work','outputs','models','__pycache__','public-media'} for part in p.parts):
        raise ValueError('Private/cache path rejected: '+name)
    if p.suffix not in SUFFIXES and p.name not in SPECIAL:
        raise ValueError('Non-source file rejected: '+name)
    return p

def eligible(name):
    if name in EXCLUDE:return False
    return (name in TOP or name.startswith(PREFIXES) or name.startswith(EXTENSIONS)
        or (name.startswith('scripts/') and Path(name).name in SCRIPTS)
        or name in {'extensions/resolve-tools.ps1','extensions/upstream-lock.json',
                    'extensions/jianying-core-lock.json','extensions/jianying-source-lock.json'})

def sanitize_document(text):
    text=re.sub(r'https://app\.chatcut\.io/editor/[^\s)<>]+','<YOUR_CHATCUT_PROJECT>',text)
    text=re.sub(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b','<EXAMPLE_ID>',text)
    text=re.sub(r'\b[0-9a-f]{64}\b','<EXAMPLE_SHA256>',text)
    return text.replace('C:\\Users\\User','<USER_HOME>').replace('C:/Users/User','<USER_HOME>')

def scan(name,data):
    safe_path(name)
    if len(data)>2*1024*1024:raise ValueError('Unexpected large source: '+name)
    if b'\0' in data:raise ValueError('Binary content rejected: '+name)
    data.decode('utf-8-sig')
    for pattern in SECRET_PATTERNS:
        if re.search(pattern,data):raise ValueError('Credential-like content rejected in '+name+'; value not printed')
    if re.search(rb'https://app\.chatcut\.io/editor/[0-9a-f-]{36}',data):
        raise ValueError('Private online project reference rejected: '+name)

def prepare(root=ROOT):
    root=Path(root).resolve()
    tracked=subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),'-C',str(root),'ls-files','-z']).decode('utf-8').split('\0')
    prepared={}; records=[]
    for name in filter(None,tracked):
        if not eligible(name):continue
        relative=safe_path(name); source=root/relative
        if source.is_symlink() or not source.resolve().is_relative_to(root):raise ValueError('External source rejected: '+name)
        raw=source.read_bytes(); text=raw.decode('utf-8-sig')
        if source.suffix=='.md':text=sanitize_document(text)
        if name=='extensions/remotion-vd44/src/Ending.tsx':text=text.replace('AGI TOP · 系统教学','你的品牌 · 系统教学')
        if name=='extensions/chatcut-vd44/placements.json':
            text=sanitize_document(text)
        if name=='extensions/remotion-vd44/source-manifest.json':
            value=json.loads(text)
            value.pop('timelineId',None);value.pop('portrait',None)
            for render in value.get('renders',[]):
                render.pop('assetId',None);render.pop('sha256',None)
                render['scope']='example timing; rendered media is not distributed'
            text=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
        data=text.encode('utf-8');scan(name,data);prepared[name]=data
        records.append({'file':name,'source_sha256':hashlib.sha256(raw).hexdigest(),
                        'release_sha256':hashlib.sha256(data).hexdigest(),'adapted':raw!=data})
    templates={'README.md':'README.md','AGENTS.md':'AGENTS.md','INSTALL_SKILLS.md':'docs/INSTALL_SKILLS.md','VALIDATION.md':'docs/VALIDATION.md','WORKFLOW_AND_TOOLS.md':'docs/WORKFLOW_AND_TOOLS.md'}
    for source,target in templates.items():
        prepared[target]=(root/'publishing'/source).read_bytes()
    guide=root/'03_Documentation/Knowledge_Base/15_Student_Walkthrough.md'
    prepared['03_Documentation/Knowledge_Base/15_Student_Walkthrough.md']=sanitize_document(guide.read_text(encoding='utf-8-sig')).encode('utf-8')
    kb={
     'README.md':'# Project knowledge base\nRead 00_Start_Here.md. Historical private jobs are not distributed.',
     '00_Start_Here.md':'# Start here\nRead ../../README.md and ../../skill/talking-head-editor/references/approved-workflow.md. The approved teaching preset is reusable; every new video is separately checked. This public snapshot contains source, not private footage or account permissions.',
     '02_Feature_Register.md':'# Features\nMaster Skill, Python revisioned runtime, local ASR option, independent audio, ChatCut workflow, Remotion/HyperFrames teaching scene sources, inspection and packaging. Each new environment needs actual installation and render checks.',
     '03_Technical_Knowledge.md':'# Technical knowledge\nOne authoritative main timeline. Speech defaults to absolute 1.2, with per-video override; brand colors come from the supplied logo and full-screen inserts require a synchronized moving circular presenter. New graphics use final timing at 1.0; documented approved-asset retiming follows final-delivery.md. Background music is processed separately; never re-normalize a mix to compensate for weak raw speech. See master Skill and docs/VALIDATION.md.',
     '04_FAQ.md':'# FAQ\nSkills are instructions; runtimes execute. Complex rendered animation internals require editing HTML/React and re-rendering. The visible browser timeline must match the delivered export. No accounts or private example media are included.',
     '05_Development_Precautions.md':'# Precautions\nPreserve source files and revisions. Do not commit credentials, media, caches or private job metadata. Preserve third-party licenses. Tests do not certify listening, user consent or video quality.',
     '06_Teaching_Playbook.md':'# Teaching\nFollow the master Skill, references/approved-workflow.md and 15_Student_Walkthrough.md. Use your own footage and explicitly choose the preset. Read only the relevant engine branch.',
     '07_Change_Log.md':'# Change log\n2026-09-12: clean public source release; original creator approved the final teaching style. Added portable Skill root discovery and animation tool paths; no core rendering algorithm or source timeline rewritten.',
     '08_Decision_Log.md':'# Decisions\nUse a clean public source snapshot to retain private job/history separation. MIT covers original work only. Preserve existing working runtime and a single timeline; animation engines provide insert assets.',
     '09_Glossary.md':'# Glossary\nA-roll: original speaker. B-roll: supporting visual. BGM: background music. SFX: short event sound. Skill: agent instructions. Revision: recoverable plan version. Frame anchor: location on the final main timeline.',
     '_Templates.md':'# Evidence template\nRequirement -> actual implementation -> decision/change -> verification method -> observed evidence -> unverified limitations. Never fill evidence with assumptions.',
     '14_Reference_Motion.md':'# Reference motion\nRead the master Skill references/reference-motion.md and docs/VALIDATION.md. Original creator style approval exists; private project IDs, hashes, footage and screenshots are not distributed.'
    }
    for name,text in kb.items():prepared['03_Documentation/Knowledge_Base/'+name]=(text+'\n').encode('utf-8')
    prepared['.github/workflows/tests.yml']=b"""name: Tests\non: [push, pull_request]\njobs:\n  python:\n    runs-on: windows-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - run: choco install ffmpeg --no-progress -y\n      - run: python -m pip install -e .\n      - run: python -m unittest discover -s tests -v\n"""
    # Strict checks happen before any output directory is created.
    for name,data in prepared.items():scan(name,data)
    manifest={'scope':'public source snapshot; no private Git history or media','source_files':records,
              'excluded':'private knowledge history, jobs, media, accounts, vendored GSAP runtime, caches',
              'files':{name:hashlib.sha256(data).hexdigest() for name,data in sorted(prepared.items())},
              'new_machine_execution':'not certified by packaging','public_visibility':'must be verified after publishing'}
    prepared['PUBLIC_RELEASE_MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    return prepared

def export(destination, root=ROOT):
    destination=Path(destination).resolve()
    if destination.exists():raise ValueError('Output exists; use a new path and preserve old versions')
    prepared=prepare(root)
    destination.mkdir(parents=True,exist_ok=False)
    for name,data in prepared.items():
        path=destination/safe_path(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        if path.read_bytes()!=data:raise ValueError('Written bytes differ: '+name)
    return {'directory':str(destination),'files':len(prepared),'source_scan':'passed','media_or_git_history_copied':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(export(args.out),ensure_ascii=False,indent=2))
