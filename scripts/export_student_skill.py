"""Export a complete reading/installation skill bundle, not accounts or footage."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skill/talking-head-editor'


def sanitize(text):
    text = text.replace('C:\\Users\\User', '<USER_HOME>').replace('C:/Users/User', '<USER_HOME>')
    text = re.sub(r'https://app\.chatcut\.io/editor/[^\s)<>]+', '<YOUR_CHATCUT_PROJECT>', text)
    text = re.sub(r'\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b', '<EXAMPLE_ID>', text)
    text = re.sub(r'\b[0-9a-f]{64}\b', '<EXAMPLE_SHA256>', text)
    return text


def export(destination):
    destination = destination.resolve()
    if destination.exists():
        raise ValueError('Output exists; choose a new directory. Prior exports are preserved.')
    archive = destination.with_suffix('.zip')
    if archive.exists():
        raise ValueError('ZIP exists; choose a new directory name.')
    source_files = sorted(p for p in SOURCE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    expected = {'SKILL.md', 'scripts/run.py', 'agents/openai.yaml'}
    if not expected.issubset({p.relative_to(SOURCE).as_posix() for p in source_files}):
        raise ValueError('Missing required source skill files')
    prepared = {'LICENSE': (ROOT/'LICENSE').read_text(encoding='utf-8'), 'THIRD_PARTY.md': (ROOT/'THIRD_PARTY.md').read_text(encoding='utf-8')}
    source_records = []
    for path in source_files:
        if path.suffix not in {'.md', '.py', '.yaml'}:
            raise ValueError(f'Unexpected file type in the skill: {path.name}')
        raw = path.read_bytes()
        content = sanitize(raw.decode('utf-8-sig'))
        relative = 'talking-head-editor/' + path.relative_to(SOURCE).as_posix()
        prepared[relative] = content
        source_records.append({'file': relative, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'redacted': content != raw.decode('utf-8-sig')})
    guide = ROOT / '03_Documentation/Knowledge_Base/15_Student_Walkthrough.md'
    prepared['01_逐步流程与Skill对照.md'] = sanitize(guide.read_text(encoding='utf-8-sig'))
    prepared['00_学员先读.md'] = '''# 口播剪辑完整Skill学员包

先读01_逐步流程与Skill对照.md，随后看02_完整规则阅读版.md。真正的Skill目录为talking-head-editor，入口是SKILL.md，其所有参考文件均包含在包内。

本包保留全部总Skill文件（数量以manifest.json为准）。02是这些Markdown规则的合订阅读版，不要把它额外安装成第二个Skill。辅助规则文件用于理解本项目的调用范围；Remotion、video-use和ChatCut官方完整依赖须另外取得，不能把辅助说明当完整软件。

本包不含讲师原片、头像、参考视频、账号、私人在线工程ID、临时登录地址、模型或node_modules。具体文件路径/工程ID/素材哈希已替换成占位符；其余个人风格数值保留为教学案例，不是所有创作者的通用默认。

安装前请让Codex检查你的现有同名Skill；已有修改先比较，不要直接覆盖。个人Skill通常放在你自己的.codex/skills目录。完整文件夹复制只能提供规则，不能自动提供剪辑软件、模型、账户和本项目执行器。

本创作者默认ChatCut为唯一主时间轴、最终导出和在线手改；学员明确选择自己的工具与素材授权。采用ChatCut路线时核对当前可调用工具、账号、项目及活动时间轴，不借用讲师账号。缺工具先说明，继续独立检查/分析/素材准备，不静默切换本地主路线。只有用户明确改选本机或剪映才切换。

本机路线的scripts/run.py从TALKING_HEAD_EDITOR_ROOT读取源码根；需要另有本项目源码与.venv。没有执行器源码先解决依赖，不把安装Skill说成已能剪片。本地实操/动画工具也可以只制作无声素材，再实际导入ChatCut，不等于自动建立在线工程。

环境状态、商业许可和最终验收均不继承。每条新视频先询问并收到本条视频比例的明确答复，再布局和剪辑；读取原片或封面比例不代替用户选择。同片修改沿用已确认比例。实际转写与声音逐片检查，不套用案例人声增益；讲师的风格认可不代替学员选择。

采用本预设且含电脑实操时，约每3秒按真实目标选择六类效果中的合适组合并配同步轻SFX；没有实操则跳过。ChatCut里保留独立人声、BGM、逐事件SFX片段，不能只给一整条音效混音。外部效果素材的内部参数仍可能需源码重渲染；MP4/恢复ZIP不是可逐层手改的在线工程。

依赖与来源见03_工具与依赖.json。修改源码/内部动画的示例工程与软件运行时不在这个规则包里；它不是可以离线还原讲师视频的工程包。
'''
    lock = json.loads((ROOT / 'extensions/upstream-lock.json').read_text(encoding='utf8'))
    dependencies = {
        'bundle_scope': 'Complete project-owned master skill plus reading guide; external products and runtime dependencies are separate.',
        'main_skill_files': len(source_files),
        'skill_names': ['talking-head-editor', 'remotion-best-practices', 'video-use', 'chatcut:chatcut-plugin-basics', 'chatcut:asset-import', 'chatcut:talking-head-guide', 'chatcut:create-motion-graphics', 'chatcut:verification', 'chatcut:export'],
        'hyperframes_project_skills': list(json.loads((ROOT/'extensions/hyperframes-vd44/skills-lock.json').read_text())['skills']),
        'runtime_versions_used_in_case': {'Remotion':'4.0.523', 'HyperFrames':'0.8.35', 'ChatCut_plugin':'1.10.12', 'Node':'24.19.0'},
        'version_note': 'These are verified case versions, not a claim about the newest release or the student machine.',
        'official_sources': [{'skill':s['name'], 'repository':'https://github.com/'+s['repository'], 'commit_used':s['commit']} for s in lock['skills'] if s['name'] in {'remotion-best-practices','video-use'}],
        'hyperframes_source': 'https://github.com/heygen-com/hyperframes',
        'chatcut_installation': 'Install the official ChatCut plugin from your own Codex plugin catalog and authorize your own account.',
        'local_runtime': 'Separate AI-Talking-Head-Editor source + Python environment, FFmpeg/FFprobe; FunASR if choosing local transcription.',
        'licenses': ['https://www.remotion.dev/license','https://gsap.com/standard-license/','https://github.com/google/fonts/tree/main/ofl/notosanssc'],
        'social_delivery': {
            'rules': 'talking-head-editor/references/social-delivery.md',
            'required_source_tool': 'scripts/package_social_delivery.py from the source repository',
            'image_generation': 'Use the available built-in imagegen; actual generation and image review are required.',
            'optional_skills': ['facebook-copywriter', 'xiaohongshu-copywriter', 'image-prompt-designer'],
            'private_factory_plugin_required': False,
        },
        'student_environment_tested': False,
    }
    prepared['03_工具与依赖.json'] = json.dumps(dependencies, ensure_ascii=False, indent=2)
    for name in ['remotion-best-practices','video-use']:
        content = sanitize((ROOT/'skill-adapters'/name/'SKILL.md').read_text(encoding='utf-8-sig'))
        prepared[f'辅助规则/{name}.md'] = '# 本项目辅助入口的阅读副本\n\n此文件供教学说明；其中上游参考由官方Skill另行安装，不把本文件视为完整独立安装包。\n\n' + content
    order = ['SKILL.md', 'references/project-storage.md', 'references/approved-workflow.md','references/brand-and-presenter.md','references/master-playbook.md','references/user-preferences.md','references/editorial.md','references/visual-storytelling.md','references/reference-motion.md','references/chatcut.md','references/final-delivery.md','references/cover-prompt-worker.md','references/quality.md','references/manual-editing.md','references/tool-stack.md','references/operations.md','references/data-contract.md','references/jianying.md']
    combined = ['# 完整口播总Skill · 学员合订阅读版\n\n这份文件合并全部Markdown规则供上课阅读；可安装版本仍是旁边的talking-head-editor目录。案例参数与历史状态不代表学员机器已通过。\n']
    order.insert(order.index('references/cover-prompt-worker.md'), 'references/social-delivery.md')
    # A new routed reference must also be present in the complete reading edition.
    order += sorted(p.relative_to(SOURCE).as_posix() for p in source_files
                    if p.suffix == '.md' and p.relative_to(SOURCE).as_posix() not in order)
    for relative in order:
        def rebase_link(match):
            target=match.group(1)
            if re.match(r'[a-z]+://|#',target):return match.group(0)
            return ']('+ (Path('talking-head-editor')/Path(relative).parent/target).as_posix()+')'
        reading=re.sub(r'\]\(([^)]+)\)',rebase_link,prepared['talking-head-editor/'+relative])
        combined.extend(['\n\n---\n\n# 文件：'+relative+'\n\n', reading])
    prepared['02_完整规则阅读版.md'] = ''.join(combined)
    for relative, content in prepared.items():
        if 'C:\\Users\\User' in content or 'app.chatcut.io/editor/' in content:
            raise ValueError('Private location leaked: '+relative)
        if re.search(r'editor-boot-token=|Authorization: Bearer\s+\S+|sk-[A-Za-z0-9]{30,}',content):
            raise ValueError('Credential-like content in '+relative)
    # Check all local links in the complete master skill before any write.
    broken=[]
    for relative,content in prepared.items():
        if not (relative.startswith('talking-head-editor/') or relative=='02_完整规则阅读版.md') or not relative.endswith('.md'): continue
        for target in re.findall(r'\]\(([^)]+)\)',content):
            if re.match(r'[a-z]+://|#',target): continue
            key=(Path(relative).parent/target.split('#')[0]).as_posix()
            if key not in prepared: broken.append((relative,target))
    if broken: raise ValueError('Broken master-skill links: '+repr(broken))
    destination.mkdir(parents=True,exist_ok=False)
    records=[]
    for relative, content in prepared.items():
        path=destination/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding='utf-8')
        records.append({'file':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'master_skill_files':len(source_files),'package_files_excluding_manifest':len(records),'source_files':source_records,'files':records,'master_links_pass':True,'privacy_text_scan_pass':True,'new_machine_runtime':'not tested','video_reedited_in_this_export':False}
    (destination/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(destination.rglob('*')):
            if path.is_file():z.write(path,path.relative_to(destination).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('ZIP CRC failure')
        for entry in records:
            if hashlib.sha256(z.read(entry['file'])).hexdigest()!=entry['sha256']:raise ValueError('ZIP hash mismatch')
    print(json.dumps({'directory':str(destination),'archive':str(archive),'files':len(records)+1,'master_skill_files':len(source_files),'crc_and_hashes':'passed','master_links':'passed','privacy_scan':'passed'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    export(args.out)
