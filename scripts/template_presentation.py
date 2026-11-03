"""One evidence-based learner guide shared by GitHub and the static gallery.

Presentation fields never change the frozen source, QA, IDs or demo assets.
"""
from __future__ import annotations

from collections import OrderedDict
import json
from pathlib import Path

LEARNER_CATEGORIES = OrderedDict([
    ('talk', '真人口播'), ('screen', '录屏与操作教学'),
    ('flow', '流程与时间线'), ('data', '数据与对比'),
    ('product', '产品与案例展示'), ('text', '标题与重点字'),
    ('transition', '转场与片尾'), ('visual', '视觉与背景'),
])
SECTION_TITLES = ['1. 效果预览', '2. 适用内容', '3. 所需素材',
                  '4. 可改参数与限制', '5. 怎样交给 AI 使用',
                  '6. 当前能否使用', '7. 来源与许可']
CATEGORY_MAP = {
    '口播与讲解': 'talk', '人物与背景': 'talk', '概念教学': 'talk',
    '界面与交互演示': 'screen', '界面与设备': 'screen',
    '关系与系统结构': 'flow', '列表与步骤': 'flow', '知识解说与流程图': 'flow',
    '数据与图表': 'data', '数据与进度': 'data',
    '产品宣传与教程': 'product', '真实素材展示': 'product', 'Logo与品牌': 'product',
    '文字与标题': 'text', '文字动态': 'text', '基础讲解': 'text', '装饰与强调': 'text',
    '叠加标注与装饰': 'text', '转场': 'transition', '镜头与转场': 'transition',
    '品牌与行动': 'transition', '社交与界面': 'screen',
    '循环与背景': 'visual', '科技视觉（非口播默认）': 'visual',
    '视觉与场景动效（非口播默认）': 'visual', '预告（不计入主清单）': 'visual',
    'RemotionUI本地适配': 'visual', '中文示例': 'text',
}
OVERRIDES = {
    **dict.fromkeys(['mg-control-compare','mg-control-bars','mg-control-number',
        'mg-control-beforeafter','mg-control-vs','mg-control-prosCons','mg-control-price',
        'mg-style-287792','mg-style-587362','mg-style-257987','mg-style-808349',
        'remotion-library-bar-zh','remotion-split-screen'], 'data'),
    **dict.fromkeys(['mg-control-steps','mg-control-timeline','mg-control-checklist',
        'mg-control-list','mg-style-968813'], 'flow'),
    **dict.fromkeys(['mg-control-callout','mg-control-progressbar','mg-control-spotlight',
        'mg-control-device','mg-style-670021','remotion-library-player-zh'], 'screen'),
    **dict.fromkeys(['mg-control-logo','mg-control-media','mg-control-cta','mg-control-reveal'], 'product'),
    **dict.fromkeys(['mg-control-sticker','mg-control-emoji','mg-control-confetti',
        'mg-control-frame','mg-control-fusion'], 'visual'),
    **dict.fromkeys(['mg-control-chapter','remotion-end-card'], 'transition'),
    **dict.fromkeys(['remotion-library-text-mask','remotion-library-glass-zh'], 'text'),
    **dict.fromkeys(['mg-style-643842','mg-style-233154','mg-style-360840'], 'talk'),
}


def learner_category(entry):
    return OVERRIDES.get(entry['id'], CATEGORY_MAP.get(entry.get('category_zh'), 'visual'))


def learner_status(entry):
    if entry.get('preview_only') or entry.get('layer') == 'preview':
        return '官方预告 · 待开放/核对'
    if entry.get('integrations'):
        return '已有接入案例 · 新片仍需适配'
    if entry.get('layer') == 'style':
        return '官方参考 · 先取得并核对原包'
    if entry.get('layer') == 'control':
        return '已有控件演示 · 需自备授权原包'
    if entry.get('layer') == 'effect':
        return '样片效果 · 需要源码适配'
    if entry.get('layer') == 'remotion':
        return '代码已入库 · 准备环境后适配'
    return '使用条件待核对'


def load_parameter_evidence(root):
    path = root / 'templates/parameter-evidence.json'
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('entries'), dict):
        raise ValueError('Invalid parameter-evidence registry')
    for ident, row in data['entries'].items():
        for key in ('parameters_zh', 'limits_zh', 'evidence'):
            if not isinstance(row.get(key), list) or not all(isinstance(v, str) and v.strip() for v in row[key]):
                raise ValueError(f'{ident}: invalid parameter evidence {key}')
        for relative in row['evidence']:
            path = (root / relative).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError(f'{ident}: parameter evidence path not in repository: {relative}')
    return data['entries']


def parameter_notes(entry, evidence=None):
    evidence = evidence or {}
    known = list(evidence.get('parameters_zh', []))
    limits = list(evidence.get('limits_zh', []))
    if not known:
        defaults = entry.get('default_parameters')
        if defaults:
            known.append('本库 Demo 曾传入：' + '、'.join(defaults) + '。这是示例输入，完整类型、容量及生效范围须读源码确认。')
        variants = entry.get('variants', [])
        if variants:
            known.append('已登记变体：' + '；'.join((v.get('label_zh') or v.get('id') or '见来源') + (' [' + v['id'] + ']' if v.get('id') else '') if isinstance(v, dict) else str(v) for v in variants) + '；登记不等于每个变体已实测。')
        if entry.get('integrations'):
            fields = sorted({k for c in entry['integrations'] for k in c.get('invocation', {}).get('actual_parameters', {})})
            if fields:
                known.append('接入案例曾使用字段：' + '、'.join(fields) + '。这些是特定案例记录，不作为完整通用参数合同。')
    if not known:
        known = ['尚未核对可替换参数合同；请先读原模板的 guide/schema 或源码。不能根据 Demo 推断能任意换颜色、数量、比例或时长。']
    if not limits:
        limits = ['文字容量、素材数量、颜色、时长和画幅的可调范围，按对应版本的实际合同核对；演示规格不等于任意规格都受支持。']
    return known, limits


def primary_case(entry):
    cases = entry.get('integrations', [])
    return next((c for c in cases if c['id'] == entry.get('preview_integration_id')), cases[0] if cases else None)


def guide_for(entry, evidence=None):
    params, limits = parameter_notes(entry, evidence)
    title, ident = entry['label_zh'], entry['id']
    instructions = (
        f'请使用 AI Cut 模板目录中的「{title}」（编号 {ident}）。\n'
        '我的内容或原片：[填写]；输出比例：[填写]；需要强调的内容：[填写]。\n'
        '先核对本条来源、当前状态、素材和参数合同；使用我自己的获授权素材，保留原声原意。\n'
        '按照本条已支持的参数范围做短预览，确认文字、动作和声音的时间一致，再放入剪辑工程。\n'
        '若原包、依赖或素材缺失，说明缺什么；遇到费用先告诉我。不要将示例人物或示例数据当成我的内容。'
    )
    status = [learner_status(entry)]
    if entry.get('layer') == 'control':
        status.append('本仓库提供目录与已渲染演示，未附送个人 .motion 原包；学员须使用自己合法取得的对应包。')
    elif entry.get('layer') == 'effect':
        status.append('当前为特定样片的效果分支，颜色、素材与时间逻辑尚有固定实现；不视为已通用化 .motion 包。')
    elif entry.get('layer') == 'remotion':
        status.append('本仓库包含相应代码；需准备 Remotion 运行环境及本条素材，参数修改后重新预览检查。')
    else:
        status.append('可取得状态：' + str(entry.get('availability') or '以来源当前页面为准'))
    case = primary_case(entry)
    if case:
        status.append('目录默认本人Demo版本：' + case['source']['version'] + '；本片QA：' + case['qa']['state'] + '。只对应已登记版本与输入；切换其他演示时，以播放器下方显示的该版本说明为准。')
    status.append('登记基线版本：' + str(entry.get('version') or '未登记；以来源为准') + '。新输入、新电脑和其他变体须另行验证。')
    sections = [
        {'id':'preview','title':SECTION_TITLES[0], 'text':['点击本条 Demo 查看实际效果；各版本的来源、画幅和检查范围独立标注。']},
        {'id':'use','title':SECTION_TITLES[1], 'text':entry.get('uses_zh') or [entry.get('description_zh') or '用途待核对'], 'notes':entry.get('avoid_zh') or []},
        {'id':'inputs','title':SECTION_TITLES[2], 'text':entry.get('inputs_zh') or ['来源尚未提供完整素材要求；取得制作指南后逐项核对，不从 Demo 猜测。']},
        {'id':'parameters','title':SECTION_TITLES[3], 'text':params, 'notes':limits, 'evidence':(evidence or {}).get('evidence',[])},
        {'id':'instructions','title':SECTION_TITLES[4], 'text':[instructions]},
        {'id':'status','title':SECTION_TITLES[5], 'text':status, 'notes':[entry.get('validation',{}).get('scope') or '验证范围尚未登记'],
         'case':{'id':case['id'], 'qa':{'scope':case['qa']['scope']}, 'invocation':{'command':case['invocation']['command']}} if case else None},
        {'id':'source','title':SECTION_TITLES[6], 'text':[entry.get('license') or '许可待核对；演示可看不代表素材可再分发。'], 'url':entry.get('source_url',''), 'repository_url':entry.get('source_repository_url','')},
    ]
    return {'schema':'ai-cut-learner-guide/1', 'category':learner_category(entry),
            'category_zh':LEARNER_CATEGORIES[learner_category(entry)],
            'status':learner_status(entry), 'sections':sections}


def enrich_entries(entries, evidence=None):
    evidence = evidence or {}
    for entry in entries:
        entry['learner_guide'] = guide_for(entry, evidence.get(entry['id']))
    return entries


def official_posters(root):
    path = root / 'templates/sources/motiongit-catalog.snapshot.json'
    if not path.is_file():
        return {}
    snapshot = json.loads(path.read_text(encoding='utf-8'))
    result = {}
    for row in snapshot.get('templates',[]):
        media = row.get('media',{}).get('zh',{})
        result['mg-style-'+str(row['repositoryId'])] = media.get('poster') or row.get('poster') or media.get('preview') or row.get('preview')
    for row in snapshot.get('previews',[]):
        media = row.get('media',{}).get('zh',{})
        result['mg-preview-'+str(row['previewId'])] = media.get('poster') or media.get('preview')
    return result


def demo_link(demo, prefix='../docs/template-gallery/'):
    return prefix+demo['path'] if demo.get('path') else demo.get('url','')


def guide_path(entry):
    category = (entry.get('learner_guide') or guide_for(entry))['category']
    return 'templates/categories/' + category + '.md#' + entry['id']


def markdown_card(entry, poster=None, root_prefix='../'):
    guide = entry.get('learner_guide') or guide_for(entry)
    lines = [f'<a id="{entry["id"]}"></a>', '', f'### {entry["label_zh"]}', '',
             f'`{entry["id"]}` · {guide["category_zh"]} · {entry.get("category_zh", "")} · **{guide["status"]}**', '', entry.get('description_zh',''), '']
    for section in guide['sections']:
        lines += ['**'+section['title']+'**', '']
        if section['id'] == 'preview':
            for index, demo in enumerate(entry.get('demos', []),1):
                href=demo_link(demo, root_prefix+'docs/template-gallery/')
                image=root_prefix+'docs/template-gallery/'+demo['poster_path'] if demo.get('poster_path') else (poster if not demo.get('path') else None)
                if index == 1 and image:
                    lines += [f'[![{entry["label_zh"]} 预览]({image})]({href})', '']
                kind='官方示例' if demo.get('kind')=='official' else '本人案例' if demo.get('integration_id') or demo.get('subject')=='owner' else '本地效果演示'
                lines += [f'- [{kind} {index} · {demo.get("ratio") or entry.get("ratio") or "规格见演示"}]({href})：{demo.get("description_zh") or "沿用原登记范围"}']
            lines += ['']
        elif section['id'] == 'instructions':
            lines += ['<details>', '<summary>复制本模板的使用提示词</summary>', '', '```text', section['text'][0], '```', '', '</details>', '']
        elif section['id'] == 'parameters':
            lines += ['按已核对的字段与限制修改；尚未核对的能力会明确标注。', '', '<details>', '<summary>查看参数、限制与来源依据</summary>', '']
            lines += ['- '+text for text in section['text']] + ['']
        else:
            lines += ['- '+text for text in section['text']] + ['']
        if section.get('notes'):
            if section['id']=='status':
                lines += ['<details>', '<summary>查看原始检查范围与接入记录</summary>', '']
            lines += ['- '+text for text in section['notes']] + ['']
            if section['id']=='status':
                case=section.get('case')
                if case:
                    lines += ['本片接入：'+case['id'], '', case['qa']['scope'], '', '```text',case['invocation']['command'],'```','', '不改变原条目验证范围，不代表用户审美认可。', '']
                lines += ['</details>', '']
        if section.get('evidence'):
            lines += ['参数依据：'+' · '.join(f'[{Path(p).name}]({root_prefix}{p})' for p in section['evidence']), '']
        if section['id'] == 'parameters':
            lines += ['</details>', '']
        if section['id']=='source':
            links=[]
            if section.get('url'): links.append('[原始来源]('+section['url']+')')
            if section.get('repository_url'): links.append('[上游技术资料]('+section['repository_url']+')')
            lines += [' · '.join(links), '']
    return '\n'.join(lines)


def markdown_catalog(entries, previews, counts, integrations, posters=None):
    posters=posters or {}
    lines=['# AI Cut · 特效模板库', '',
        '选择效果时先看内容用途，再看来源与当前状态。每条按同一顺序说明：效果预览 → 适用内容 → 所需素材 → 可改参数与限制 → 怎样交给 AI 使用 → 当前能否使用 → 来源与许可。', '',
        '[学习自动剪辑](../docs/NOTION_GUIDE.zh-CN.md) · [在线筛选与播放](https://aicut.agi-top.com) · [模板来源说明](PROVENANCE.zh-CN.md) · [本机使用方法](../docs/GETTING_STARTED.zh-CN.md)', '',
        '## 按你要表达的内容选择', '',
        '| 用途分类 | 条目 |', '| --- | ---: |']
    for key,label in LEARNER_CATEGORIES.items():
        n=sum(e['learner_guide']['category']==key for e in entries)
        lines.append(f'| [{label}](#use-{key}) | {n} |')
    lines += ['', f'共 {len(entries)} 条不同层级的目录：{counts["style"]} 项官网模板与片段、{counts["control"]} 个官网控件、{counts["remotion"]} 个代码注册项、{counts["effect"]} 个真人效果分支。另有 {len(integrations)} 条接入案例，不重复计为模板；附加预告单列。不能把它们称为 {len(entries)} 套整片一键模板。', '',
        '## 状态怎样看', '', '已有案例表示对应输入曾经测试；代码入库仍需自己的运行环境；官方参考需要核对原包和取得状态；样片效果需要适配；官方预告不代表已开放下载。参数未查证的地方会明确保留“待核对”。', '',
        '原来的四个来源层级和中文细类保留在每张卡及机器目录中。官方集合来自固定快照，并非官网最新全站库存。', '']
    for key,label in LEARNER_CATEGORIES.items():
        lines += [f'<a id="use-{key}"></a>', f'## {label}', '', f'[打开本分类的完整七项说明](categories/{key}.md)', '',
                  '| 模板 | 用途与当前状态 | Demo |', '| --- | --- | --- |']
        for entry in entries:
            if entry['learner_guide']['category']==key:
                link='categories/'+key+'.md#'+entry['id']
                demos=' · '.join('[Demo '+str(i)+']('+demo_link(d)+')' for i,d in enumerate(entry['demos'],1))
                case=primary_case(entry)
                version='<br>当前本人Demo版本：'+case['source']['version'] if case else ''
                lines += [f'| [{entry["label_zh"].replace("|","／")}]({link})<br>`{entry["id"]}` | {entry.get("description_zh", "").replace("|","／")}<br>**{entry["learner_guide"]["status"]}**{version} | {demos} |']
        lines += ['']
    lines += ['## 附加预告 · 不计入主清单', '']
    for entry in previews:
        lines += ['['+entry['label_zh']+'](categories/'+entry['learner_guide']['category']+'.md#'+entry['id']+')：'+entry['learner_guide']['status'], '']
    lines += ['## 维护说明', '', '本页和 HTML 由同一登记表及学员说明层生成；参数证据单独记录并验证文件存在。修改后运行：', '',
              '```powershell', 'python scripts/build_template_gallery.py --strict', '```', '',
              '个人 .motion、Key、完整原片、完整成片和工作缓存不包含在模板目录内。源文件与历史验证记录保持不变。', '']
    return '\n'.join(lines)


def markdown_category_pages(entries, previews, posters=None):
    posters=posters or {}
    pages={}
    for key,label in LEARNER_CATEGORIES.items():
        rows=[e for e in entries if e['learner_guide']['category']==key]
        lines=['# '+label+' · 特效模板详细说明', '',
               '[返回全部分类](../README.zh-CN.md) · [学习自动剪辑](../../docs/NOTION_GUIDE.zh-CN.md) · [在线筛选与播放](https://aicut.agi-top.com)', '',
               f'本页 {len(rows)} 个目录条目；每项固定七段，参数依据与使用状态独立标注。先准备自己的合法素材，再按对应版本检查依赖和预览。', '',
               ' · '.join('['+e['label_zh']+'](#'+e['id']+')' for e in rows), '']
        for entry in rows:
            lines += [markdown_card(entry,posters.get(entry['id']),'../../'), '---', '']
        extra=[e for e in previews if e['learner_guide']['category']==key]
        if extra:
            lines += ['## 附加预告 · 不计入上述条目', '']
            for entry in extra:
                lines += [markdown_card(entry,posters.get(entry['id']),'../../'), '']
        pages[key]='\n'.join(lines).rstrip()+'\n'
    return pages
