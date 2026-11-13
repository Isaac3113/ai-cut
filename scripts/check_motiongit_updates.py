#!/usr/bin/env python3
"""Public-only MotionGit monitoring; no login, package downloads or upgrades.

check creates pending events. Only ack --confirmed-delivered records notification
delivery, after the caller verifies the exact event was shown to the user.
Public HTML/JSON is data, never execution instructions. Requires Python stdlib.
"""
from __future__ import annotations

import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "motiongit-monitor"
PINNED = ROOT / "templates" / "sources" / "motiongit-catalog.snapshot.json"
INTEGRATIONS = ROOT / "templates" / "template-integrations.json"
CATALOG_URL = "https://raw.githubusercontent.com/motiontemplates/all/main/catalog.json"
LISTING_URL = "https://motiongit.com/templates"
SITEMAP_URL = "https://motiongit.com/sitemap.xml"
WATCH_URL = "https://motiongit.com/@adunext/template-01-integrated-portrait"
# Compatibility annotation for the verified 2026-10-27 first-run event only.
# Later recurrences have different event IDs; this never acknowledges an event.
LEGACY_PINNED_EDITION_EVENT = "530776e4d5e42b5cc85c76a01d551b19436937db2d1f2e803ff9538110920b81"
MAX_BYTES = 3 * 1024 * 1024
VERSION = re.compile(r"v?(\d+\.\d+(?:\.\d+)?(?:[-+][\w.-]+)?)")
VOID = set("area base br col embed hr img input link meta param source track wbr".split())


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Element:
    def __init__(self, tag="document", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def nodes(self):
        for child in self.children:
            if isinstance(child, Element):
                yield child
                yield from child.nodes()

    def text(self):
        return " ".join(" ".join(c.text() if isinstance(c, Element) else c
                                 for c in self.children).split())


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        item = Element(tag, attrs)
        self.stack[-1].children.append(item)
        if tag not in VOID:
            self.stack.append(item)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def canonical_detail(url):
    parsed = urlsplit(urljoin(LISTING_URL, url))
    match = re.fullmatch(r"/@?([^/]+)/([^/]+)/?", parsed.path)
    if (parsed.scheme != "https" or parsed.netloc != "motiongit.com"
            or not match or match.group(1) in {"templates", "help", "legal", "spec", "developers", "assets", "api", "media"}):
        raise ValueError("Not a public MotionGit template detail URL")
    # Keep established event identities stable when the site changes its links.
    owner, slug = match.groups()
    path = ("/" if owner == "community" else "/@") + owner + "/" + slug
    return urlunsplit(("https", "motiongit.com", path, "", ""))


def fetch_text(url, timeout=15):
    """Bounded public GET. No cookie jar, auth headers or package URLs."""
    parts = urlsplit(url)
    allowed = (url == CATALOG_URL or
               (parts.scheme == "https" and parts.netloc == "motiongit.com"
                and (parts.path in {"/templates", "/sitemap.xml"}
                     or re.fullmatch(r"/templates/c/[a-z0-9-]+", parts.path)
                     or re.fullmatch(r"/@?[^/]+/[^/]+", parts.path))))
    if not allowed:
        raise ValueError("URL outside the public monitor scope")
    req = Request(url, headers={"User-Agent": "TalkingHeadEditor-PublicUpdateMonitor/1.0",
                                "Accept": "text/html,application/json", "Accept-Language": "en"})
    with urlopen(req, timeout=timeout) as response:
        if urlsplit(response.url).netloc != parts.netloc:
            raise ValueError("Unexpected cross-host redirect")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Public metadata exceeded bounded response size")
        return data.decode("utf-8-sig")


def parse_listing(html, page_url):
    nodes = list(Document(html).root.nodes())
    cards = {}
    for card in (n for n in nodes if n.tag == "article" and n.has_class("vcard")):
        links = [n for n in card.nodes() if n.tag == "a" and n.has_class("vthumb")]
        if len(links) != 1:
            raise ValueError("Template card structure changed")
        url = canonical_detail(links[0].attrs.get("href", ""))
        title = next((n.text() for n in card.nodes() if n.tag == "h3"), "")
        cards[url] = {"url": url, "title": title,
                      "content_type": card.attrs.get("data-content-type", "")}
    if not cards:
        raise ValueError("No public template cards; refusing empty baseline")
    totals = []
    for css, pattern in (("idx-meta", r"([0-9][0-9,]*) results"),
                         ("market-bottom", r"Total ([0-9][0-9,]*) video templates")):
        container = next((n for n in nodes if n.has_class(css)), None)
        label = next((n.text() for n in container.children if isinstance(n, Element) and n.tag == "span"), "") if container else ""
        match = re.fullmatch(pattern, label)
        if not match:
            raise ValueError("Public listing total missing or changed")
        totals.append(int(match.group(1).replace(",", "")))
    if totals[0] != totals[1]:
        raise ValueError("Public listing totals disagree")
    status = parse_qs(urlsplit(page_url).query).get("status", [""])[0]
    pagers = [n for n in nodes if n.tag == "nav" and n.has_class("pager")]
    if len(pagers) != 1:
        raise ValueError("Public pagination missing or ambiguous")
    next_nodes = [n for n in pagers[0].nodes() if n.text() == "Next"]
    if len(next_nodes) != 1:
        raise ValueError("Pagination must explicitly show Next or disabled Next")
    next_node, next_url = next_nodes[0], None
    if next_node.tag == "a":
        next_url = urljoin(page_url, next_node.attrs.get("href", ""))
        p, current = urlsplit(next_url), urlsplit(page_url)
        query = parse_qs(p.query)
        if not (p.scheme == "https" and p.netloc == "motiongit.com" and p.path == "/templates"
                and query.get("status", [""])[0] == status and set(query) <= {"status", "page"}
                and int(query.get("page", ["1"])[0]) == int(parse_qs(current.query).get("page", ["1"])[0]) + 1):
            raise ValueError("Invalid or non-incrementing next page")
    elif not (next_node.tag == "span" and next_node.has_class("dis")):
        raise ValueError("Unknown Next page state")
    innovation = next((urljoin(page_url, n.attrs["href"]) for n in nodes
                       if n.tag == "a" and n.attrs.get("href") == "/templates?status=innovation"), None)
    return cards, next_url, innovation, totals[0]


def parse_detail(html, card):
    nodes = list(Document(html).root.nodes())
    versions = [VERSION.fullmatch(value) for n in nodes if n.has_class("mono-pill")
                for value in (n.attrs.get("title", ""), n.text())]
    version = next((m.group(1) for m in versions if m), None)
    acquire = next((n for n in nodes if n.has_class("repo-acquire")), None)
    if acquire is not None and acquire.has_class("prelaunch-box"):
        return dict(card, id=card["url"], version=None,
                    availability={"stage": "prelaunch", "downloadable": False},
                    release_time=None, release_note=None)
    if not version:
        raise ValueError("Current public version missing; detail structure may have changed")
    if acquire is None:
        raise ValueError("Public acquire section missing; refusing guessed download status")
    acquire_nodes = list(acquire.nodes())
    price = next((n.text() for n in acquire_nodes
                  if n.has_class("get-price") or n.has_class("free")), None)
    login = any(n.tag == "a" and n.attrs.get("href", "").startswith("/login?")
                for n in acquire_nodes)
    locked = any(n.attrs.get("id") == "social-support"
                 and n.attrs.get("data-social-locked") == "true" for n in nodes)
    if not price or not (login or locked):
        routes = sorted({urlsplit(n.attrs.get("href", "")).path for n in acquire_nodes if n.tag == "a"})[:5]
        raise ValueError("Acquire signals changed; cannot infer unlock/download status "
                         f"(price_present={bool(price)}, login={login}, social_locked={locked}, link_paths={routes})")
    release = next((n for n in nodes if n.has_class("template-update-entry")), None)
    release_time = next((n.attrs.get("datetime") for n in release.nodes() if n.tag == "time"), None) if release else None
    release_note = next((n.text() for n in release.nodes() if n.tag == "p"), None) if release else None
    item = dict(card, id=card["url"], version=version,
                availability={"social_locked": locked, "login_required": login, "price_label": price},
                release_time=release_time, release_note=release_note)
    return item


def normalize_catalog(data):
    if data.get("format") != "motiongit.catalog/1" or not data.get("templates"):
        raise ValueError("Invalid or empty public catalog")
    entries = {}
    for record in data["templates"]:
        url = canonical_detail(record["website"])
        if url in entries or not record.get("version"):
            raise ValueError("Duplicate catalog URL or missing version")
        title = record.get("title", {})
        entries[url] = {"id": url, "url": url, "title": title.get("zh", title.get("en", "")),
                        "repository_id": str(record.get("repositoryId", "")),
                        "version": record["version"],
                        "catalog_origin": {"url": CATALOG_URL, "repository": record.get("repository"),
                                           "open_source": record.get("openSource") is True},
                        "distribution_editions": [
                            {"source_version": v["sourceEdition"].get("version"),
                             "source_ratio": v["sourceEdition"].get("ratio"),
                             "variant_version": v.get("version"), "variant_ratio": v.get("ratio"),
                             "edition_note": v.get("editionNote", {}).get("zh")}
                            for v in record.get("additionalDemos", []) if isinstance(v.get("sourceEdition"), dict)],
                        "variant_versions": {str(v.get("ratio", "")): v["version"]
                                             for v in record.get("additionalDemos", []) if v.get("version")},
                        "availability": record.get("download", {}).get("availability"),
                        "download_type": record.get("download", {}).get("type")}
    for record in data.get("previews", []):
        identity = "preview:" + str(record["previewId"])
        title = record.get("title", {})
        entries[identity] = {"id": identity, "url": record.get("website", LISTING_URL),
                             "title": title.get("zh", title.get("en", "")),
                             "version": record.get("version"),
                             "availability": record.get("download", {}).get("availability"),
                             "download_type": record.get("download", {}).get("type")}
    return entries


def directory_navigation(html, page_url):
    """Discover status sections and categories without following sort/locale copies."""
    sections, categories = set(), set()
    for node in Document(html).root.nodes():
        if node.tag != "a" or not node.attrs.get("href"):
            continue
        url = urljoin(page_url, node.attrs["href"])
        p, query = urlsplit(url), parse_qs(urlsplit(url).query)
        if p.scheme != "https" or p.netloc != "motiongit.com":
            continue
        if p.path == "/templates" and set(query) == {"status"}:
            if len(query["status"]) != 1 or not re.fullmatch(r"[a-z0-9-]+", query["status"][0]):
                raise ValueError("Invalid public status navigation")
            sections.add(urlunsplit((p.scheme, p.netloc, p.path, "status=" + query["status"][0], "")))
        if re.fullmatch(r"/templates/c/[a-z0-9-]+", p.path):
            categories.add(urlunsplit((p.scheme, p.netloc, p.path, "", "")))
        if p.path == "/templates" and set(query) == {"cat"} and len(query["cat"]) == 1:
            cat = query["cat"][0]
            if not re.fullmatch(r"[a-z0-9-]+", cat):
                raise ValueError("Invalid public category navigation")
            categories.add("https://motiongit.com/templates/c/" + cat)
    return sections, categories


def sitemap_inventory(html):
    try:
        root = ET.fromstring(html)
    except ET.ParseError as error:
        raise ValueError("Public sitemap XML missing or changed") from error
    if root.tag.rsplit("}", 1)[-1] != "urlset":
        raise ValueError("Public sitemap format changed; coverage requires review")
    categories, details = set(), set()
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] != "loc" or not node.text:
            continue
        p = urlsplit(node.text)
        if p.scheme != "https" or p.netloc != "motiongit.com":
            raise ValueError("Unexpected public sitemap origin")
        if re.fullmatch(r"/templates/c/[a-z0-9-]+", p.path):
            categories.add(urlunsplit((p.scheme, p.netloc, p.path, "", "")))
        try:
            details.add(canonical_detail(node.text))
        except ValueError:
            pass  # Site help/legal/developer pages are not templates.
    return categories, details


def audit_category(fetch, start, known, pages):
    """Read all category pages; a new inventory gap must not advance the baseline."""
    url, page, seen = start, 1, set()
    while url:
        if url in pages or page > 80:
            raise ValueError("Category pagination cycle or bound reached")
        nodes = list(Document(fetch(url)).root.nodes())
        if not any(n.tag == "h1" for n in nodes):
            raise ValueError("Public category page missing heading")
        cards = [n for n in nodes if n.tag == "article" and n.has_class("vcard")]
        current = set()
        for card in cards:
            links = [n for n in card.nodes() if n.tag == "a" and n.has_class("vthumb")]
            if len(links) != 1:
                raise ValueError("Category template card structure changed")
            current.add(canonical_detail(links[0].attrs.get("href", "")))
        if current & seen:
            raise ValueError("Duplicate category cards across pages")
        unknown = current - known
        if unknown:
            raise ValueError("Public category has templates outside scanned sections: " + ", ".join(sorted(unknown)[:3]))
        seen.update(current)
        pages.add(url)
        pagers = [n for n in nodes if n.tag == "nav" and n.has_class("pager")]
        if not pagers:
            if len(cards) >= 24:
                raise ValueError("Full public category page missing pagination")
            break  # Explicit empty categories remain part of coverage.
        next_nodes = [n for n in pagers[0].nodes() if n.text() == "Next"]
        if len(pagers) != 1 or len(next_nodes) != 1:
            raise ValueError("Public category pagination missing or ambiguous")
        node = next_nodes[0]
        if node.tag == "span" and node.has_class("dis"):
            break
        nxt = urljoin(url, node.attrs.get("href", ""))
        p, q = urlsplit(nxt), parse_qs(urlsplit(nxt).query)
        if not (node.tag == "a" and p.scheme == "https" and p.netloc == "motiongit.com"
                and p.path == urlsplit(start).path and set(q) == {"page"}
                and q["page"] == [str(page + 1)]):
            raise ValueError("Invalid category next page")
        url, page = nxt, page + 1


def collect_directory(fetch=fetch_text):
    pages, starts, entries = set(), [LISTING_URL], {}
    categories, sitemap_details = sitemap_inventory(fetch(SITEMAP_URL))
    pages.add(SITEMAP_URL)
    for start in starts:
        url, section, declared = start, {}, None
        while url:
            if url in pages or len(pages) >= 200:
                raise ValueError("Pagination cycle or bound reached")
            html = fetch(url)
            cards, next_url, innovation, total = parse_listing(html, url)
            sections, discovered_categories = directory_navigation(html, url)
            categories.update(discovered_categories)
            for section_url in sorted(sections):
                if section_url not in starts:
                    starts.append(section_url)
            if declared is not None and total != declared:
                raise ValueError("Total changed during pagination; retry next run")
            if set(cards) & set(section):
                raise ValueError("Duplicate cards across pages; refusing incomplete crawl")
            declared = total
            if parse_qs(urlsplit(start).query).get("status") == ["claim"]:
                for card in cards.values():
                    card["stage"] = "claim"
            section.update(cards)
            pages.add(url)
            if start == LISTING_URL and innovation and innovation not in starts:
                starts.append(innovation)
            url = next_url
        if len(section) != declared:
            raise ValueError("Unique public card count does not equal declared total")
        entries.update(section)
    if LISTING_URL + "?status=innovation" not in starts:
        raise ValueError("Innovation entry missing; public directory coverage uncertain")
    if len(entries) > 5000:
        raise ValueError("Template bound reached; coverage requires review")
    missing = sitemap_details - set(entries)
    if missing:
        raise ValueError("Public sitemap has templates outside scanned sections: " + ", ".join(sorted(missing)[:3]))
    for category in sorted(categories):
        audit_category(fetch, category, set(entries), pages)
    def read_detail(card):
        if card.get("stage") == "claim":
            return dict(card, id=card["url"], version=None,
                        availability={"stage": "claim", "downloadable": False},
                        release_time=None, release_note=None)
        first_error = None
        for attempt in range(2):
            try:
                item = parse_detail(fetch(card["url"]), card)
                if first_error:
                    item["monitor_diagnostics"] = {"acquire_retry_recovered": True, "first_error": first_error}
                return item
            except Exception as error:
                # One fresh public response can recover a transient acquire fragment.
                # Unknown status after the retry still fails the complete source.
                if attempt == 0 and isinstance(error, ValueError) and str(error).startswith("Acquire signals changed"):
                    first_error = str(error)
                    continue
                raise ValueError(f"Public detail {card['url']}: {type(error).__name__}: {error}") from error
    with ThreadPoolExecutor(max_workers=4) as pool:
        details = list(pool.map(read_detail, entries.values()))
    return {item["id"]: item for item in details}, sorted(pages)


def initial_state(pinned):
    pinned = {key: dict(item) for key, item in pinned.items()}
    directory = {key: dict(item, availability=None, download_type=None)
                 for key, item in pinned.items() if not key.startswith("preview:")}
    return {"schema_version": 1, "sources": {
        "public_catalog": {"baseline": pinned, "baseline_origin": "repo_pinned_snapshot"},
        "official_directory": {"baseline": directory, "baseline_origin": "repo_pinned_snapshot"}},
        "pending": {}, "acknowledged": {}}


def compare(old, new):
    changes = []
    for identity, item in sorted(new.items()):
        previous = old.get(identity)
        if previous is None:
            changes.append((identity, "new_entry", None, {k: item.get(k) for k in ("version", "availability")}))
            continue
        for field in ("version", "variant_versions", "availability", "download_type"):
            if previous.get(field) is not None and item.get(field) is not None and previous[field] != item[field]:
                changes.append((identity, field, previous[field], item[field]))
    return changes


def apply_observation(state, source, entries, timestamp):
    current = state["sources"][source]
    baseline = current["baseline"]
    for identity, kind, before, after in compare(baseline, entries):
        payload = [identity, kind, before, after]
        signature = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        event_id = next((key for key, event in state["pending"].items()
                         if event.get("signature", key) == signature), signature)
        acknowledged = [(key, value) for key, value in state["acknowledged"].items()
                        if value["event"].get("signature", key) == signature]
        if event_id not in state["pending"] and acknowledged:
            last_ack = acknowledged[-1][1]["event"]
            if source not in last_ack["sources"]:
                # A slower second source is corroborating an already delivered event.
                last_ack["sources"].append(source)
                continue
            # A genuine recurrence after a reversal needs a fresh notification.
            sequence = state.get("event_sequence", 0) + 1
            state["event_sequence"] = sequence
            event_id = hashlib.sha256(f"{signature}:{sequence}".encode()).hexdigest()
        if event_id not in state["pending"]:
            item = entries[identity]
            state["pending"][event_id] = {"event_id": event_id, "signature": signature, "template_id": identity,
                "title": item.get("title", ""), "url": item.get("url"), "kind": kind,
                "before": before, "after": after, "first_seen_at": timestamp,
                "sources": [], "release_note": item.get("release_note"),
                "previously_evaluated_314486": identity == WATCH_URL}
        event = state["pending"][event_id]
        event.setdefault("source_baselines", {})[source] = current.get("baseline_origin", "unknown")
        if source not in event["sources"]:
            event["sources"].append(source)
        if entries[identity].get("release_note"):
            event["release_note"] = entries[identity]["release_note"]
    missing = sorted(set(baseline) - set(entries))
    # A temporarily absent item is retained. No deletion or reappearance alerts.
    baseline.update(entries)
    current.update(last_success_at=timestamp, baseline_origin="public_observation")
    return {"status": "ok", "observed_entries": len(entries), "temporarily_absent": missing}


def acknowledge(state, event_ids, timestamp):
    unknown = set(event_ids) - set(state["pending"]) - set(state["acknowledged"])
    if unknown:
        raise ValueError("Unknown event IDs; no acknowledgement applied")
    for event_id in set(event_ids):
        if event_id in state["pending"]:
            event = state["pending"].pop(event_id)
            state["acknowledged"][event_id] = {"acknowledged_at": timestamp, "event": event}


def annotate_pending_events(events, pinned):
    """Presentation-only context: keep pending IDs, notification state and seeds intact."""
    annotated = copy.deepcopy(events)
    for event in annotated:
        item = pinned.get(event["template_id"], {})
        initial_directory_comparison = (
            event.get("source_baselines", {}).get("official_directory") == "repo_pinned_snapshot"
            or event.get("event_id") == LEGACY_PINNED_EDITION_EVENT)
        editions = [edition for edition in item.get("distribution_editions", [])
                    if edition.get("source_version") == event.get("before")
                    and edition.get("variant_version") not in (None, event.get("before"))
                    and edition.get("source_ratio") and edition.get("variant_ratio")
                    and edition["source_ratio"] != edition["variant_ratio"]]
        if (event.get("kind") != "version" or "official_directory" not in event.get("sources", [])
                or not initial_directory_comparison or event.get("before") != item.get("version")
                or not item.get("catalog_origin", {}).get("open_source") or not editions):
            continue
        event["baseline_context"] = {
            "classification": "initial_cross_distribution_comparison",
            "baseline_origin": "repo_pinned_snapshot",
            "before_source": item["catalog_origin"], "after_source": event.get("url"),
            "distribution_evidence": editions,
            "legacy_event_annotation": event.get("event_id") == LEGACY_PINNED_EDITION_EVENT,
            "note_zh": (
                f"首次对照发现公开分发版本差异：冻结 GitHub 开源分发为 {event['before']}，"
                f"官网页面当前为 {event['after']}。固定目录明确区分源码分发与官网画幅版本，"
                "这不是已安装本地升级的证据，也不能据此视为同一分发的连续版本更新；未下载或升级模板。")}
    return annotated


def local_references(pinned, integrations_path):
    """Read public provenance, never personal package/key files; no new QA claim."""
    packages = {}
    for item in pinned.values():
        identity = item.get("repository_id")
        if identity:
            packages[identity] = {"frozen_catalog_version": item["version"], "verified_integrations": []}
    result = {"packages": packages, "integration_file_status": "missing", "invalid_entries": 0,
              "meaning": "Frozen catalog versions are not installation proof. Verified integrations are existing repo QA records, not a fresh runtime verification."}
    if not integrations_path.exists():
        return result
    data = json.loads(integrations_path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1 or not isinstance(data.get("integrations"), list):
        raise ValueError("Invalid template integration registry")
    result["integration_file_status"] = "read"
    for entry in data["integrations"]:
        if entry.get("qa", {}).get("state") != "verified_demo":
            continue
        source = entry.get("source", {})
        try:
            valid = (entry.get("id") and entry.get("integrated_at") and source.get("official") is True
                     and source.get("package_id") and VERSION.fullmatch(str(source.get("version", "")))
                     and re.fullmatch(r"[a-fA-F0-9]{64}", str(source.get("sha256", ""))))
            public_url = canonical_detail(source.get("url", ""))
            if not valid:
                raise ValueError("Incomplete integration provenance")
        except (ValueError, TypeError):
            result["invalid_entries"] += 1
            continue
        package = packages.setdefault(str(source["package_id"]), {"frozen_catalog_version": None, "verified_integrations": []})
        package["verified_integrations"].append({"integration_id": entry["id"], "integrated_at": entry["integrated_at"],
                                                "version": source["version"], "url": public_url, "sha256": source["sha256"]})
    for package in packages.values():
        package["verified_integrations"].sort(key=lambda x: x["integrated_at"])
        package["latest_recorded_verified_version"] = (package["verified_integrations"][-1]["version"]
                                                        if package["verified_integrations"] else None)
    return result


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def state_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        lock.unlink()


def run_check(state, fetch=fetch_text):
    timestamp, results = now(), {}
    for source in ("public_catalog", "official_directory"):
        try:
            if source == "public_catalog":
                entries, pages = normalize_catalog(json.loads(fetch(CATALOG_URL))), [CATALOG_URL]
            else:
                entries, pages = collect_directory(fetch)
            results[source] = dict(apply_observation(state, source, entries, timestamp), pages=pages)
            recovered = [key for key, item in entries.items()
                         if item.get("monitor_diagnostics", {}).get("acquire_retry_recovered")]
            if recovered:
                results[source]["acquire_retry_recovered_urls"] = recovered
        except Exception as error:
            # No partial source results are applied; last good source baseline survives.
            results[source] = {"status": "failed", "error_type": type(error).__name__,
                               "message": str(error)[:350], "baseline_preserved": True}
    return {"schema_version": 1, "checked_at": timestamp, "sources": results,
        "coverage": {"public_catalog": "Fixed curated GitHub collection, additional variant versions and preview-only entries; not the entire site.",
                     "official_directory": "Discovered public status sections (including Claim), complete pagination, sitemap/category reconciliation, and published/prelaunch detail versions/status; Claim cards are references without callable packages.",
                     "excluded": ["private/unlisted templates", "account-only availability", "personal package contents"],
                     "watch_314486": "Public detail compared with repo-pinned previously evaluated version; local package is not inspected or upgraded."},
        "pending_events": sorted(state["pending"].values(), key=lambda e: (e["first_seen_at"], e["event_id"])),
        "notification_ack_required": True,
        "limitations": "Public availability is an observed page signal, not a successful download or render. The first comparison is against pinned collection versions; website and open-source editions may differ (notably Kinetic Tech). Missing entries are never inferred as deletions. No package/media downloads or remote content execution."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "ack"):
        sub = commands.add_parser(command)
        sub.add_argument("--state", type=Path, default=WORK / "state.json")
        if command == "check":
            sub.add_argument("--report", type=Path, default=WORK / "latest-report.json")
            sub.add_argument("--pinned", type=Path, default=PINNED)
            sub.add_argument("--integrations", type=Path, default=INTEGRATIONS)
        else:
            sub.add_argument("--event-id", action="append", required=True)
            sub.add_argument("--confirmed-delivered", action="store_true",
                             help="Required only after these exact events were visibly delivered to the user.")
    args = parser.parse_args(argv)
    if args.command == "ack" and not args.confirmed_delivered:
        parser.error("ack requires --confirmed-delivered after verified notification delivery")
    with state_lock(args.state):
        if args.state.exists():
            state = json.loads(args.state.read_text(encoding="utf-8"))
            if state.get("schema_version") != 1:
                raise ValueError("Unsupported state schema; refusing overwrite")
        elif args.command == "check":
            state = initial_state(normalize_catalog(json.loads(args.pinned.read_text(encoding="utf-8-sig"))))
        else:
            raise ValueError("No existing state to acknowledge")
        if args.command == "ack":
            acknowledge(state, args.event_id, now())
            atomic_json(args.state, state)
            print(json.dumps({"acknowledged": args.event_id, "pending_count": len(state["pending"])}, ensure_ascii=False))
            return 0
        report = run_check(state)
        try:
            pinned = normalize_catalog(json.loads(args.pinned.read_text(encoding="utf-8-sig")))
            report["pending_events"] = annotate_pending_events(report["pending_events"], pinned)
            report["local_version_references"] = local_references(pinned, args.integrations)
        except (OSError, ValueError, KeyError, TypeError) as error:
            report["local_version_references"] = {"integration_file_status": "invalid", "message": str(error)[:250]}
        # Save pending events first: a report-write interruption cannot silently lose alerts.
        atomic_json(args.state, state)
        atomic_json(args.report, report)
        print(json.dumps({"state": str(args.state), "report": str(args.report),
                          "sources": report["sources"], "pending_events": report["pending_events"]}, ensure_ascii=False, indent=2))
        return 2 if any(s["status"] == "failed" for s in report["sources"].values()) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error_type": type(error).__name__, "message": str(error)[:350]}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
