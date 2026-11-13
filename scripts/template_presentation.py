"""One evidence-based learner guide shared by GitHub and the static gallery.

Presentation fields never change the frozen source, QA, IDs or demo assets.
"""
from __future__ import annotations

from collections import OrderedDict
from hashlib import sha256
import json
from pathlib import Path

LEARNER_CATEGORIES = OrderedDict([
    ('talk', '真人口播'), ('screen', '录屏与操作教学'),
    ('flow', '流程与时间线'), ('data', '数据与对比'),
    ('product', '产品与案例展示'), ('text', '标题与重点字'),
    ('transition', '转场与片尾'), ('visual', '视觉与背景'),
    ('industry', '行业应用'), ('innovation', '实验与创新'),
    ('uncategorized', '分类待核对'),
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
    '行业应用': 'industry', '行业模板预告': 'industry',
    '实验与创新': 'innovation', '创新与实验': 'innovation',
    '分类待核对': 'uncategorized',
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
    if entry['id'] in OVERRIDES:
        return OVERRIDES[entry['id']]
    if entry.get('learner_category') in LEARNER_CATEGORIES:
        return entry['learner_category']
    group = entry.get('official_group') or entry.get('source_group')
    if group in ('industry', 'prelaunch') or entry.get('industry_tags'):
        return 'industry'
    if entry.get('category_zh') in CATEGORY_MAP:
        return CATEGORY_MAP[entry['category_zh']]
    if group == 'innovation':
        return 'innovation'
    return 'uncategorized'


EXECUTION_STATUSES = OrderedDict([
    ('integrated_case', '已接入案例 · 按已验证版本使用'),
    ('source_ready', '仓库源码可调用 · 先检查环境与素材'),
    ('not_integrated', '尚未接入 · 先取得并核对原包'),
    ('package_required', '已有控件演示 · 需自备授权原包'),
    ('adaptation_required', '样片效果 · 需要源码适配'),
    ('preview', '官方预告 · 待开放/核对'),
    ('claim_pending', '待认领展示 · 原包未开放'),
    ('unknown', '使用条件待核对'),
])


def execution_status(entry):
    if entry.get('stage') == 'claim' or entry.get('catalog_availability') == 'claim':
        return 'claim_pending'
    if entry.get('preview_only') or entry.get('layer') == 'preview':
        return 'preview'
    if entry.get('integrations'):
        return 'integrated_case'
    return {'style': 'not_integrated', 'control': 'package_required',
            'effect': 'adaptation_required', 'remotion': 'source_ready'}.get(entry.get('layer'), 'unknown')


def learner_status(entry):
    state = execution_status(entry)
    if state == 'integrated_case':
        versions = {c.get('source', {}).get('version') for c in entry['integrations']}
        if entry.get('version') not in versions:
            return '已接入历史版 · 当前公开版尚未验证'
        return '已有同版本接入案例 · 新片仍需适配'
    return EXECUTION_STATUSES[state]


def official_classification(entry):
    labels = []
    group = entry.get('official_group_zh') or entry.get('official_group') or entry.get('source_group')
    if group:
        labels.append(str(group))
    for field in ('official_categories', 'industry_tags'):
        values = entry.get(field) or []
        if isinstance(values, str):
            values = [values]
        for value in values:
            label = value if isinstance(value, str) else value.get('name') or value.get('label') or value.get('id')
            if label and str(label) not in labels:
                labels.append(str(label))
    return labels


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
    if entry.get('layer') in ('style', 'preview'):
        latest = entry.get('latest_official') or {}
        observation = entry.get('source_observation', {}).get('catalog')
        version = str(latest.get('catalog_version') or entry.get('version') or '来源未提供版本号')
        if observation == 'temporarily_absent':
            status.append('公开 GitHub 合集上次记录版本：' + version + '；本轮未观察到此项，保留历史条目，不能据此认定已删除或仍是当前最新版。')
        elif observation == 'not_in_collection':
            status.append('公开 GitHub 合集本轮未列此项；本条来自官网公开展示，不能把官网版本当成 GitHub 已发布原包。')
        else:
            status.append('公开 GitHub 合集当前版本：' + version + '；这是目录元数据，不代表本机已安装或验证这个版本。')
        website_version = entry.get('website_version') or latest.get('website_version')
        status.append('官网独立核对版本：' + str(website_version) if website_version else '官网独立版本：本轮尚无独立详情证据；不把公开合集版本冒称官网已验证版本。')
        frozen = entry.get('frozen_validation_reference') or {}
        if frozen.get('version') and frozen['version'] != entry.get('version'):
            status.append('原检查记录对应版本：' + frozen['version'] + '；原有 Demo、包与检查记录保持原版，新版尚未因目录更新而通过验证。')
        if execution_status(entry) == 'not_integrated':
            status.append('尚未接入 AI Cut：可以交给 AI 选型，但须先合法取得原包、核对依赖与参数并做短样，才能确认可用于自己的内容。')
    else:
        status.append('本库登记版本：' + str(entry.get('version') or '未登记；以来源为准') + '。新输入、新电脑和其他变体须另行验证。')
    classifications = official_classification(entry)
    uses = list(entry.get('uses_zh') or [entry.get('description_zh') or '用途待核对'])
    if classifications:
        uses.append('官方分类与行业：' + '、'.join(classifications) + '。用途导航仅帮助查找，不会隐藏其他行业的模板。')
    sections = [
        {'id':'preview','title':SECTION_TITLES[0], 'text':['点击本条 Demo 查看实际效果；各版本的来源、画幅和检查范围独立标注。' if entry.get('demos') else '官方来源暂未提供可播放 Demo；保留条目与来源入口，不用其他模板的画面补位。']},
        {'id':'use','title':SECTION_TITLES[1], 'text':uses, 'notes':entry.get('avoid_zh') or []},
        {'id':'inputs','title':SECTION_TITLES[2], 'text':entry.get('inputs_zh') or ['来源尚未提供完整素材要求；取得制作指南后逐项核对，不从 Demo 猜测。']},
        {'id':'parameters','title':SECTION_TITLES[3], 'text':params, 'notes':limits, 'evidence':(evidence or {}).get('evidence',[])},
        {'id':'instructions','title':SECTION_TITLES[4], 'text':[instructions]},
        {'id':'status','title':SECTION_TITLES[5], 'text':status, 'notes':[entry.get('validation',{}).get('scope') or '验证范围尚未登记'],
         'case':{'id':case['id'], 'qa':{'scope':case['qa']['scope']}, 'invocation':{'command':case['invocation']['command']}} if case else None},
        {'id':'source','title':SECTION_TITLES[6], 'text':[entry.get('license') or '许可待核对；演示可看不代表素材可再分发。'], 'url':entry.get('source_url',''), 'repository_url':entry.get('source_repository_url','')},
    ]
    return {'schema':'ai-cut-learner-guide/1', 'category':learner_category(entry),
            'category_zh':LEARNER_CATEGORIES[learner_category(entry)],
            'detail_page':learner_category(entry) + '.md',
            'execution_status':execution_status(entry),
            'execution_status_zh':EXECUTION_STATUSES[execution_status(entry)],
            'status':learner_status(entry), 'sections':sections}


def enrich_entries(entries, evidence=None):
    evidence = evidence or {}
    for entry in entries:
        entry['learner_guide'] = guide_for(entry, evidence.get(entry['id']))
    # Keep GitHub documents readable even when the website exposes hundreds of
    # not-yet-open entries. These are navigation pages, not a second inventory.
    groups = OrderedDict()
    for entry in entries:
        if entry.get('preview_only') or entry.get('layer') == 'preview':
            groups.setdefault(preview_group(entry), []).append(entry)
    for label, rows in groups.items():
        group_id = sha256(label.encode('utf-8')).hexdigest()[:10]
        for i, entry in enumerate(sorted(rows, key=lambda e: e['id'])):
            entry['learner_guide']['detail_page'] = f'preview-{group_id}-{i // 50 + 1}.md'
    return entries


def preview_group(entry):
    labels = official_classification(entry)
    return ' / '.join(labels) if labels else entry.get('category_zh') or '分类待核对'


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
    guide = entry.get('learner_guide') or guide_for(entry)
    return 'templates/categories/' + guide.get('detail_page', guide['category'] + '.md') + '#' + entry['id']


def markdown_card(entry, poster=None, root_prefix='../'):
    guide = entry.get('learner_guide') or guide_for(entry)
    lines = [f'<a id="{entry["id"]}"></a>', '', f'### {entry["label_zh"]}', '',
             f'`{entry["id"]}` · {guide["category_zh"]} · {entry.get("category_zh", "")} · **{guide["status"]}**', '', entry.get('description_zh',''), '']
    for section in guide['sections']:
        lines += ['**'+section['title']+'**', '']
        if section['id'] == 'preview':
            if not entry.get('demos'):
                lines += section['text'] + ['']
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


def markdown_catalog(entries, previews, counts, integrations, posters=None, sync_status=None):
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
        '## 状态怎样看', '', '已有案例仅证明已登记版本与输入曾经测试；当前公开版本单独显示，目录刷新不会升级旧 Demo 或原包。源码可调用仍需自己的运行环境和素材；未接入模板须先取得并核对原包；样片效果需要适配；官方预告与待认领展示不代表已开放下载。参数未查证的地方保留“待核对”。', '',
        '| 调用状态 | 条目与预告合计 |', '| --- | ---: |']
    for state, label in EXECUTION_STATUSES.items():
        n = sum(execution_status(e) == state for e in entries + previews)
        if n:
            lines.append(f'| {label} | {n} |')
    lines += ['', '## 本轮来源与覆盖', '']
    if sync_status:
        lines += ['元数据核对时间：' + str(sync_status.get('checked_at') or '见同步记录') + '。', '']
        sources = sync_status.get('sources') or {}
        if isinstance(sources, dict):
            sources = [dict(value, name=key) if isinstance(value, dict) else {'name': key, 'status': value} for key, value in sources.items()]
        for source in sources:
            label = source.get('name') or source.get('source') or source.get('url') or '公开来源'
            state = source.get('status') or source.get('state') or '见同步记录'
            state = {'ok':'成功读取', 'not_checked':'本轮未核对', 'failed':'读取失败'}.get(state, state)
            count = source.get('observed_cards')
            if count is None and source.get('observed_templates') is not None:
                count = source['observed_templates'] + source.get('observed_previews', 0)
            lines.append('- ' + str(label) + '：' + str(state) + (f'；{count} 条来源记录' if count is not None else '') + ('；' + str(source['note']) if source.get('note') else ''))
        if sync_status.get('scope_zh'):
            lines += ['', sync_status['scope_zh']]
        if sync_status.get('gaps'):
            lines += ['', '本轮仍未完成的来源核对：']
            for gap in sync_status['gaps']:
                lines.append('- ' + (gap if isinstance(gap, str) else json.dumps(gap, ensure_ascii=False)))
        lines += ['', '具体来源、分页、数量及缺口见机器目录的 `sync_status`；无法读取的分区不能视为没有更新。仅覆盖本轮公开可枚举内容，不包含未公开或账号专属原包。', '']
    else:
        lines += ['本页按已登记来源生成；本轮来源覆盖尚未登记，不能据此宣称官网最新全站已收齐。', '']
    lines += ['官方原分类与行业标签保留在每条七项说明中；用途分类只是辅助选型，四个来源层级不能相加当作整片模板数。', '']
    for key,label in LEARNER_CATEGORIES.items():
        lines += [f'<a id="use-{key}"></a>', f'## {label}', '', f'[打开本分类的完整七项说明](categories/{key}.md)', '',
                  '| 模板 | 用途与当前状态 | Demo |', '| --- | --- | --- |']
        for entry in entries:
            if entry['learner_guide']['category']==key:
                link=guide_path(entry).removeprefix('templates/')
                demos=' · '.join('[Demo '+str(i)+']('+demo_link(d)+')' for i,d in enumerate(entry['demos'],1))
                case=primary_case(entry)
                version='<br>公开登记版本：'+str(entry.get('version') or '未提供') if entry.get('layer')=='style' else ''
                version += '<br>当前本人Demo版本：'+case['source']['version'] if case else ''
                lines += [f'| [{entry["label_zh"].replace("|","／")}]({link})<br>`{entry["id"]}` | {entry.get("description_zh", "").replace("|","／")}<br>**{entry["learner_guide"]["status"]}**{version} | {demos} |']
        lines += ['']
    lines += [f'## 预告与待认领展示 · {len(previews)} 项 · 不计入主清单', '']
    groups = OrderedDict()
    for entry in previews:
        groups.setdefault(preview_group(entry), []).append(entry)
    for label, rows in groups.items():
        lines += ['### ' + label, '', '| 名称 | 状态 | Demo |', '| --- | --- | --- |']
        for entry in rows:
            link=guide_path(entry).removeprefix('templates/')
            demos=' · '.join('[Demo '+str(i)+']('+demo_link(d)+')' for i,d in enumerate(entry.get('demos', []),1)) or '来源未提供'
            lines += ['| ['+entry['label_zh'].replace('|','／')+']('+link+') | '+entry['learner_guide']['status']+' | '+demos+' |']
        lines += ['']
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
                link = Path(guide_path(entry).split('#', 1)[0]).name + '#' + entry['id']
                lines += ['- [' + entry['label_zh'] + '](' + link + ') · ' + entry['learner_guide']['status']]
        pages[key]='\n'.join(lines).rstrip()+'\n'
    grouped = OrderedDict()
    for entry in previews:
        page = entry['learner_guide'].get('detail_page', entry['learner_guide']['category'] + '.md')
        grouped.setdefault(page, []).append(entry)
    for page, rows in grouped.items():
        # Callers using un-enriched fixtures keep the historical inline path.
        if page.removesuffix('.md') in LEARNER_CATEGORIES:
            pages[page.removesuffix('.md')] += '\n'.join(markdown_card(e,posters.get(e['id']),'../../') for e in rows)
            continue
        lines = ['# ' + preview_group(rows[0]) + ' · 预告与待认领详情', '',
                 '[返回全部分类](../README.zh-CN.md) · [在线筛选与播放](https://aicut.agi-top.com)', '',
                 '这里是官方公开展示记录。预告、待认领与可下载原包是不同状态；每项按七段说明，未知参数和许可保留待核对。', '']
        for entry in rows:
            lines += [markdown_card(entry, posters.get(entry['id']), '../../'), '---', '']
        pages[page.removesuffix('.md')] = '\n'.join(lines).rstrip() + '\n'
    return pages
