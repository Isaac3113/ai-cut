"""Reconcile public MotionGit metadata without acquiring or executing templates.

The GitHub collection and the website are independent observations. Existing
IDs, local demos and version-scoped validation are preserved. Absent records are
retained and labelled; public previews/claim cards never become runnable cases.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG_URL = "https://raw.githubusercontent.com/motiontemplates/all/main/catalog.json"
MAX_BYTES = 8 * 1024 * 1024
GROUPS = {
    "open": "科技视觉（非口播默认）", "talk": "口播与讲解",
    "explainer": "知识解说与流程图", "product": "产品宣传与教程",
    "art": "视觉与场景动效（非口播默认）", "innovation": "实验与创新",
    "prelaunch": "行业预告", "preview": "预告（不计入主清单）",
    "claim": "待认领展示",
}
UNKNOWN_INPUT = "来源未列完整素材要求；先核对随包 guide、素材槽和参数合同，不从 Demo 猜测。"
BOUNDARY = "公开元数据与官方演示链接已登记；未取得或执行新版原包，未逐条播放、确认下载权限或做新片验收。"


def text_zh(value, fallback=""):
    if isinstance(value, dict):
        return value.get("zh") or value.get("en") or fallback
    return value if isinstance(value, str) and value else fallback


def safe_url(value, required=False):
    if not value:
        if required:
            raise ValueError("Required public HTTPS URL missing")
        return None
    p = urlsplit(value)
    if p.scheme != "https" or not p.netloc or p.username or p.password or any(c.isspace() for c in value):
        raise ValueError("Unsafe public metadata URL: expected HTTPS without credentials")
    return value


def identity(value):
    """Compare old /@author/slug and current /author/slug without renaming IDs."""
    safe_url(value, True)
    p = urlsplit(value)
    path = p.path.rstrip("/")
    if p.netloc == "motiongit.com":
        path = re.sub(r"^/@", "/", path)
    return urlunsplit((p.scheme, p.netloc, path, "", ""))


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def fetch_catalog(commit=None):
    url = CATALOG_URL.replace("/main/", "/" + commit + "/") if commit else CATALOG_URL
    request = Request(url, headers={"User-Agent": "AI-Cut-PublicCatalogSync/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        if urlsplit(response.url).netloc != "raw.githubusercontent.com":
            raise ValueError("Unexpected public catalog redirect")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Public catalog response exceeds metadata limit")
    return json.loads(raw.decode("utf-8-sig")), raw


def validate_catalog(catalog):
    if catalog.get("format") != "motiongit.catalog/1" or not catalog.get("templates"):
        raise ValueError("Invalid or empty official collection")
    seen = set()
    for key, identity_key in (("templates", "repositoryId"), ("previews", "previewId")):
        rows = catalog.get(key, [])
        if not isinstance(rows, list):
            raise ValueError("Official collection rows must be lists")
        local = set()
        for row in rows:
            stable = str(row.get(identity_key, ""))
            if not stable or stable in local:
                raise ValueError("Missing or duplicate official stable ID")
            local.add(stable)
            if row.get("website"):
                url = identity(row["website"])
                if url in seen:
                    raise ValueError("Duplicate official template/preview URL")
                seen.add(url)
            for name in ("repository", "poster", "preview", "demo"):
                safe_url(row.get(name))
            safe_url(row.get("download", {}).get("url"))
            for media in row.get("media", {}).values():
                for name in ("poster", "preview", "demo"):
                    safe_url(media.get(name))
            for variant in row.get("additionalDemos", []):
                for name in ("website", "poster", "preview", "demo"):
                    safe_url(variant.get(name))
                for media in variant.get("media", {}).values():
                    for name in ("poster", "preview", "demo"):
                        safe_url(media.get(name))
        declared = catalog.get("listing", {}).get("templateCount" if key == "templates" else "previewCount")
        if declared is not None and declared != len(rows):
            raise ValueError("Official declared count differs from unique records")


def official_demos(source):
    result = []
    for index, row in enumerate([source] + source.get("additionalDemos", [])):
        media = row.get("media", {}).get("zh", {})
        url = safe_url(media.get("demo") or row.get("demo"))
        if not url:
            continue
        result.append({
            "kind": "official", "url": url,
            "description_zh": "官方来源演示；公开登记版本 " + str(row.get("version") or source.get("version") or "未提供") + "，演示文件未必对应最新包，未本机实测。",
            "ratio": row.get("ratio") or source.get("ratio") or "未提供",
            "source_version": row.get("version") or source.get("version"),
        })
    return list({demo["url"]: demo for demo in result}.values())


def variants(source):
    return [{
        "label_zh": text_zh(row.get("label") or row.get("title"), "官方附加演示"),
        "ratio": row.get("ratio"), "version": row.get("version"),
        "source_template_id": source.get("templateId"),
        "source_url": row.get("website") or source.get("website"),
        "demo_index": index + 1, "source_edition": deepcopy(row.get("sourceEdition")),
        "note_zh": text_zh(row.get("editionNote"), "附加演示的版本与画幅独立登记；不作为本机验证。"),
    } for index, row in enumerate(source.get("additionalDemos", []))]


def _lookup(rows, source, preview=False):
    """Prefer stable remote ID, then website identity; never derive a new local ID on rename."""
    stable = str(source.get("previewId" if preview else "repositoryId", ""))
    matches = [row for row in rows if str(row.get("source_id", "")) == stable]
    if not matches and source.get("website"):
        matches = [row for row in rows if row.get("source_url") and identity(row["source_url"]) == identity(source["website"])]
    if not matches and not preview and source.get("templateId") is not None:
        matches = [row for row in rows if row.get("source_template_id") == source["templateId"]]
    if len(matches) > 1:
        raise ValueError("Ambiguous existing stable template mapping")
    return matches[0] if matches else None


def registry_entry(source, old=None, preview=False, directory=None):
    old = deepcopy(old) if old else {}
    row = deepcopy(old)
    group = source.get("group") or ("preview" if preview else "uncategorized")
    stable = str(source.get("previewId" if preview else "repositoryId"))
    title = text_zh(source.get("title"), "名称未提供")
    summary = text_zh(source.get("summary"), "来源未提供完整简介；请查看官方条目。")
    if old and (old.get("version") != source.get("version") or old.get("variants", []) != variants(source)):
        row.setdefault("frozen_validation_reference", {
            "version": old.get("version"), "validation": deepcopy(old.get("validation", {})),
            "variants": deepcopy(old.get("variants", [])),
            "meaning_zh": "刷新前本机记录，仅对应所列旧版本及验证范围；不是新版已验证。",
        })
    row.update({
        "id": old.get("id") or ("mg-preview-" if preview else "mg-style-") + stable,
        "label_zh": title, "layer": "preview" if preview else "style",
        "category_zh": old.get("category_zh") or GROUPS.get(group, "分类待核对"),
        "description_zh": summary, "version": source.get("version"),
        "source_id": stable,
        "source_url": source.get("website") or old.get("source_url") or "https://github.com/motiontemplates/all",
        "source_template_id": source.get("templateId"), "ratio": source.get("ratio") or "未提供",
        "source_group": group, "official_group": group, "official_group_zh": GROUPS.get(group, group),
        "source_repository_url": source.get("repository"), "source_revision": source.get("commit"),
        "catalog_download_type": source.get("download", {}).get("type"),
        "catalog_availability": source.get("download", {}).get("availability"),
        "preview_only": preview, "stage": source.get("stage") or ("prelaunch" if preview and group == "prelaunch" else "preview" if preview else "published"),
        "family_label_zh": old.get("family_label_zh") or re.sub(r"\s*[·｜|]\s*竖屏$", "", title),
    })
    row.setdefault("uses_zh", [summary])
    row.setdefault("avoid_zh", ["演示人物、数据和品牌是来源的示例；使用前改为自己的获授权素材，并核对本条真实内容。"])
    row["inputs_zh"] = [text_zh(source.get("materials"))] if text_zh(source.get("materials")) else old.get("inputs_zh") or [UNKNOWN_INPUT]
    row.setdefault("license", "官方演示可看不等于原包、字体、音乐或素材可再分发；许可须逐包核对。")
    row.setdefault("validation", {"state": "官方Demo可看" if official_demos(source) else "来源已登记 · 无演示", "scope": BOUNDARY})
    availability = row["catalog_availability"] or "未提供"
    row["availability"] = "待认领展示；原包未开放，不可直接调用" if row["stage"] == "claim" else "官方目录状态：" + availability + "；实际取得条件以官网为准"
    local = [deepcopy(demo) for demo in old.get("demos", []) if demo.get("kind") != "official" or demo.get("path") or demo.get("integration_id")]
    row["demos"] = local + official_demos(source)
    row["variants"] = variants(source)
    row["official_poster"] = safe_url(source.get("media", {}).get("zh", {}).get("poster") or source.get("poster") or source.get("media", {}).get("zh", {}).get("preview") or source.get("preview"))
    if not row["demos"]:
        row["no_demo_reason"] = "公开来源未提供可播放的 Demo；保留官方入口，不推断模板可运行。"
    else:
        row.pop("no_demo_reason", None)
    row["official_categories"] = deepcopy(source.get("categories", []))
    row["industry_tags"] = deepcopy(source.get("industryTags", source.get("industry_tags", [])))
    row["latest_official"] = {
        "catalog_version": source.get("version"), "catalog_url": CATALOG_URL,
        "availability": availability,
        "variant_versions": {str(v.get("ratio")): v.get("version") for v in source.get("additionalDemos", [])},
    }
    row["source_observation"] = {"catalog": "present", "website": "not_checked"}
    if directory:
        apply_directory(row, directory)
    return row


def apply_directory(row, record):
    url = safe_url(record.get("url"), True)
    row["latest_official"]["website_url"] = url
    website_version = record.get("version") or record.get("website_version")
    if website_version:
        row["website_version"] = website_version
        row["latest_official"]["website_version"] = website_version
    row["website_status"] = record.get("status") or ("claim" if "claim" in record.get("sections", []) else "prelaunch" if record.get("availability", {}).get("prelaunch") else "published")
    row["source_observation"]["website"] = "present"
    row["website_sections"] = deepcopy(record.get("sections", []))
    if record.get("attribution"):
        row["official_attribution"] = record["attribution"]
        if row.get("stage") == "claim":
            row["license"] = "公开待认领参考作品，未提供可调用原包；官网署名：" + record["attribution"] + "。公开展示不转移原作者权利，也不代表允许再分发。"
    row["official_categories"] = deepcopy(record.get("categories") or record.get("official_categories") or row.get("official_categories") or [])
    row["industry_tags"] = deepcopy(record.get("industry_tags") or record.get("industryTags") or row.get("industry_tags") or [])
    for key in ("availability", "price_label", "login_required", "social_locked", "content_type", "detail_status"):
        if key in record:
            row["latest_official"][key] = deepcopy(record[key])
    if not row.get("official_poster"):
        row["official_poster"] = safe_url(record.get("poster") or record.get("preview"))
    if not row.get("demos") and record.get("demo"):
        row["demos"] = [{"kind": "official", "url": safe_url(record["demo"], True), "ratio": record.get("ratio") or row.get("ratio"), "description_zh": "官网公开演示；未取得原包或在本机执行。", "source_version": website_version}]
        row.pop("no_demo_reason", None)
    if record.get("fields"):
        row["official_input_fields"] = deepcopy(record["fields"])
    if record.get("release_note"):
        row["latest_official"]["release_note"] = record["release_note"]
    if record.get("availability", {}).get("observed_acquire_section"):
        state = record["availability"]
        row["availability"] = ("官网预告，原包尚未开放" if state.get("prelaunch") else
                               "官网：" + str(state.get("price_label") or "取得条件待核对") +
                               ("；需登录" if state.get("login_required") else "")) + "；未验证下载或运行"


def normalize_directory_record(record):
    """Accept the read-only website auditor's nested detail observation."""
    row = deepcopy(record)
    detail = row.pop("detail", {})
    for key in ("version", "fields", "release_note", "detail_read", "availability"):
        if key in detail:
            row[key] = deepcopy(detail[key])
    for key in ("demo", "poster"):
        if detail.get(key):
            row[key] = detail[key]
    if detail.get("summary_zh"):
        row["summary"] = {"zh": detail["summary_zh"]}
    if detail.get("repository_id"):
        row["templateId"] = int(detail["repository_id"]) if str(detail["repository_id"]).isdigit() else detail["repository_id"]
    if row.get("ratio"):
        match = re.search(r"\d+:\d+", row["ratio"])
        row["ratio"] = match.group(0) if match else "未提供"
    return row


def validate_directory(directory, records):
    """A supplied complete observation must account for every declared section."""
    coverage = directory.get("coverage", {})
    if not coverage:
        return
    if coverage.get("page_failures") or coverage.get("detail_failures") or coverage.get("category_unknown_urls"):
        raise ValueError("Website observation has incomplete pages/details/categories")
    if coverage.get("unique_listing_urls") is not None and coverage["unique_listing_urls"] != len(records):
        raise ValueError("Website unique card count differs from observed records")
    for section, declared in coverage.get("sections", {}).items():
        observed = sum(section in record.get("sections", []) for record in records)
        if declared != observed:
            raise ValueError("Website section total differs from observed cards: " + section)
    if coverage.get("detail_requested") is not None and coverage.get("detail_success") != coverage["detail_requested"]:
        raise ValueError("Website detail coverage is incomplete")


def directory_source(record, claim=False):
    stable_id = record.get("templateId", record.get("template_id"))
    suffix = str(stable_id) if stable_id is not None else sha256(identity(record["url"]).encode()).hexdigest()[:16]
    stable = ("claim-" if claim else "site-") + suffix
    return {
        "previewId" if claim else "repositoryId": stable,
        "templateId": stable_id, "website": record["url"], "version": None if claim else record.get("version"),
        "title": {"zh": text_zh(record.get("title"), "名称未提供")},
        "summary": {"zh": text_zh(record.get("summary"), "官网公开待认领展示；原包尚未开放。" if claim else "官网公开条目；完整能力和素材要求以来源说明为准。")},
        "group": "claim" if claim else record.get("group") or ("innovation" if "innovation" in record.get("sections", []) else "uncategorized"),
        "stage": "claim" if claim else "published", "ratio": record.get("ratio"),
        "download": {"type": "official-page", "availability": "claim" if claim else "check-official-page"},
        "demo": record.get("demo"), "poster": record.get("poster"), "preview": record.get("preview"),
        "materials": record.get("materials"),
    }


def synchronize(catalog, previous_snapshot, previous_styles, directory=None, *, checked_at, source_sha256=None, source_commit=None):
    validate_catalog(catalog)
    snapshot = deepcopy(catalog)
    rows = deepcopy(previous_styles.get("entries", []))
    previews = deepcopy(previous_styles.get("previews", []))
    directory = directory or {}
    records = directory.get("records", directory.get("entries", []))
    if isinstance(records, dict):
        records = list(records.values())
    validate_directory(directory, records)
    by_url = {}
    for record in records:
        record = normalize_directory_record(record)
        key = identity(record["url"])
        if key in by_url:
            raise ValueError("Duplicate normalized website identity")
        by_url[key] = record
    observed_ids, observed_preview_ids = set(), set()
    output, output_previews = [], []
    for key, previous, target, seen, is_preview in (("templates", rows, output, observed_ids, False), ("previews", previews, output_previews, observed_preview_ids, True)):
        for source in catalog.get(key, []):
            old = _lookup(previous, source, is_preview)
            if old is None and not is_preview:
                old = _lookup(previews, source, False)
            match = by_url.get(identity(source["website"])) if source.get("website") else None
            row = registry_entry(source, old, is_preview, match)
            if old and old.get("layer") == "preview" and not is_preview:
                row["previous_kind"] = "preview"
            target.append(row); seen.add(row["id"])
    retained = []
    for previous, target, seen in ((rows, output, observed_ids), (previews, output_previews, observed_preview_ids)):
        for old in previous:
            if old["id"] in observed_ids | observed_preview_ids:
                continue
            row = deepcopy(old)
            outside_collection = old.get("source_observation", {}).get("catalog") == "not_in_collection"
            row["source_observation"] = {"catalog": "not_in_collection" if outside_collection else "temporarily_absent", "website": "temporarily_absent" if records else "not_checked"}
            row.setdefault("latest_official", {})
            if row.get("source_url") and identity(row["source_url"]) in by_url:
                apply_directory(row, by_url[identity(row["source_url"])])
            target.append(row)
            if not outside_collection:
                retained.append(row["id"])
    existing_urls = {identity(row["source_url"]) for row in output + output_previews if row.get("source_url")}
    directory_only = []
    for key, record in by_url.items():
        if key in existing_urls:
            continue
        claim = record.get("status") == "claim" or "claim" in record.get("sections", [])
        source = directory_source(record, claim)
        row = registry_entry(source, _lookup(previews if claim else rows, source, claim), claim, record)
        row["source_observation"]["catalog"] = "not_in_collection"
        row["latest_official"].pop("catalog_version", None)
        row["latest_official"].pop("catalog_url", None)
        row["catalog_availability"] = "claim" if claim else "not_in_collection"
        (output_previews if claim else output).append(row)
        existing_urls.add(key); directory_only.append(row["id"])
    # Retain the last source metadata for temporarily absent existing entries so
    # their verified IDs/posters do not disappear. Declared counts remain upstream counts.
    for key, stable_key in (("templates", "repositoryId"), ("previews", "previewId")):
        seen = {str(row[stable_key]) for row in snapshot.get(key, [])}
        for old in previous_snapshot.get(key, []):
            if str(old[stable_key]) not in seen:
                item = deepcopy(old); item["_source_observation"] = "temporarily_absent"
                snapshot.setdefault(key, []).append(item)
    output_ids = [row["id"] for row in output + output_previews]
    if len(output_ids) != len(set(output_ids)):
        raise ValueError("Duplicate local stable IDs after reconciliation")
    old_order = {row["id"]: index for index, row in enumerate(rows)}
    old_preview_order = {row["id"]: index for index, row in enumerate(previews)}
    output.sort(key=lambda row: (row["id"] not in old_order, old_order.get(row["id"], 0), row["id"]))
    output_previews.sort(key=lambda row: (row["id"] not in old_preview_order, old_preview_order.get(row["id"], 0), row["id"]))
    categories = directory.get("categories", {})
    category_summary = [{"id": key, **{field: value[field] for field in ("title", "url", "total_unique_cards", "page_scope") if field in value}} for key, value in categories.items()] if isinstance(categories, dict) else categories
    coverage = {
        "checked_at": checked_at,
        "sources": [{"name": "public_catalog", "url": CATALOG_URL, "status": "ok", "observed_templates": len(catalog["templates"]), "observed_previews": len(catalog.get("previews", []))},
                    {"name": "official_directory", "url": "https://motiongit.com/templates", "status": "ok" if records else "not_checked", "observed_cards": len(records), "pages": len(directory.get("pages", []))}],
        "website_sections": {key: {"total": value.get("total"), "observed": len(value.get("urls", []))} for key, value in directory.get("sections", {}).items()},
        "official_categories": deepcopy(category_summary),
        "gaps": deepcopy(directory.get("gaps", [])) if records else ["本次未提供完整官网枚举；仅更新官方GitHub合集。"],
        "scope_zh": "公开目录、预告和待认领展示按来源登记；不含私人库存、账号专属原包，也不代表下载或运行已验证。",
    }
    if directory.get("coverage"):
        site = directory["coverage"]
        coverage["official_directory"] = {key: deepcopy(site[key]) for key in ("sections", "unique_listing_urls", "detail_requested", "detail_success", "detail_failures", "page_failures", "category_unknown_urls") if key in site}
        coverage["official_directory"].update({"listing_pages": len(site.get("pages", [])), "category_pages": len(site.get("category_pages", [])), "sitemap_path_count": len(site.get("sitemap_paths", []))})
        coverage["sources"][1]["pages"] = len(site.get("pages", []))
    coverage["summary_zh"] = (f"官方GitHub合集：{len(catalog['templates'])}个主条目、{len(catalog.get('previews', []))}个预告；"
                              + (f"官网：{len(records)}个公开卡片，{coverage['sources'][1]['pages']}页，含待认领展示。" if records else "本次未重新枚举官网。")
                              + f"保留{len(retained)}个本次合集暂缺的旧条目；登记不等于取得原包或运行验证。")
    snapshot["_sync"] = {"checked_at": checked_at, "upstream_sha256": source_sha256, "upstream_commit": source_commit, "retained_absent_ids": retained, "note": "listing counts describe the current upstream collection; arrays also retain last-known absent metadata. Website-only cards are in motiongit-styles.json."}
    snapshot_bytes = encode(snapshot)
    result = deepcopy(previous_styles)
    result.update({"updated": checked_at[:10], "entries": output, "previews": output_previews, "sync_status": coverage, "source_coverage": coverage})
    result["source"] = {"repository": "https://github.com/motiontemplates/all", "catalog_url": CATALOG_URL, "checked_at": checked_at, "snapshot_path": "sources/motiongit-catalog.snapshot.json", "snapshot_bytes": len(snapshot_bytes), "snapshot_sha256": sha256(snapshot_bytes).hexdigest(), "upstream_sha256": source_sha256, "provenance_path": "PROVENANCE.zh-CN.md"}
    if source_commit:
        result["source"]["commit"] = source_commit
        result["source"]["catalog_url"] = CATALOG_URL.replace("/main/", "/" + source_commit + "/")
    directory_only = [row["id"] for row in output + output_previews if row.get("source_observation", {}).get("catalog") == "not_in_collection"]
    result["source_manifest"] = {"expected_entry_ids": [row["id"] for row in output], "expected_preview_ids": [row["id"] for row in output_previews], "observed_catalog_template_count": len(catalog["templates"]), "observed_catalog_preview_count": len(catalog.get("previews", [])), "retained_absent_entry_ids": retained, "directory_only_entry_ids": directory_only}
    groups = Counter(row.get("source_group", "uncategorized") for row in output)
    entry_demos = sum(len(row["demos"]) for row in output)
    demo_urls = [demo["url"] for row in output + output_previews for demo in row.get("demos", []) if demo.get("kind") == "official" and demo.get("url")]
    result["counts"] = {"main_entries": len(output), "entry_demos": entry_demos, "previews": len(output_previews), "claim_previews": sum(row.get("stage") == "claim" for row in output_previews), "official_demo_urls": len(demo_urls), "unique_official_demo_urls": len(set(demo_urls)), "descriptive_families": len({(row.get("source_group"), row.get("family_label_zh")) for row in output}), "by_source_group": dict(groups), "main_entries_by_ratio": dict(Counter(row.get("ratio") for row in output)), "notes_zh": "按稳定来源身份合并，主条目、预告及待认领分别计数；不是本机可执行模板数。暂缺旧条目保留并标明来源状态。"}
    previous_categories = {row["source_group"]: row for row in previous_styles.get("categories", [])}
    result["categories"] = [dict(previous_categories.get(group, {}), source_group=group, label_zh=GROUPS.get(group, group), count=count, description_zh=previous_categories.get(group, {}).get("description_zh", "保留官方来源分组；用途与取得条件逐条查看。")) for group, count in groups.items()]
    result["validation_boundary_zh"] = BOUNDARY + " 历史实测与 Demo 继续绑定原来的包版本；当前官网版与GitHub公开版分开登记。"
    result.setdefault("field_provenance_zh", {}).update({"version": "当前公开GitHub合集版本；官网独立版本在website_version；历史本机验证在frozen_validation_reference及integrations。", "official_group": "保留来源group；中文名称是本地导航翻译，不是行业适用性筛选。", "official_categories": "官网明确给出的分类标签；来源未提供则为空，不推测行业。", "industry_tags": "仅保留来源实际行业标签；未知不归入视觉背景。", "source_observation": "来源本次是否观察到该条目；暂缺不等于删除。"})
    return snapshot, result


def atomic_write(path, data):
    path = Path(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        temp = Path(stream.name); stream.write(data)
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog-file", type=Path, help="Previously fetched official public catalog JSON")
    parser.add_argument("--directory-file", type=Path, help="Complete public website observation JSON; never a package")
    parser.add_argument("--checked-at", default=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    parser.add_argument("--source-commit", help="Independently verified GitHub catalog commit")
    parser.add_argument("--check", action="store_true", help="Report reconciliation without writing files")
    args = parser.parse_args(argv)
    if args.source_commit and not re.fullmatch(r"[a-f0-9]{40}", args.source_commit):
        parser.error("--source-commit needs a full verified commit SHA")
    snapshot_path = args.root / "templates/sources/motiongit-catalog.snapshot.json"
    styles_path = args.root / "templates/motiongit-styles.json"
    if args.catalog_file:
        raw = args.catalog_file.read_bytes(); catalog = json.loads(raw.decode("utf-8-sig"))
        if args.source_commit:
            pinned, pinned_raw = fetch_catalog(args.source_commit)
            if catalog != pinned:
                raise ValueError("Local catalog does not match the specified official commit")
            catalog, raw = pinned, pinned_raw
    else:
        catalog, raw = fetch_catalog(args.source_commit)
    snapshot, styles = synchronize(catalog, load(snapshot_path), load(styles_path), load(args.directory_file) if args.directory_file else None, checked_at=args.checked_at, source_sha256=sha256(raw).hexdigest(), source_commit=args.source_commit)
    if not args.check:
        atomic_write(snapshot_path, encode(snapshot)); atomic_write(styles_path, encode(styles))
    print(json.dumps({"written": not args.check, "counts": styles["counts"], "source_coverage": styles["source_coverage"], "retained_absent_entry_ids": styles["source_manifest"]["retained_absent_entry_ids"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
