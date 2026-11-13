"""Offline stdlib tests: source coverage and notification delivery are separate."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("motiongit_updates", Path(__file__).resolve().parents[1] / "scripts/check_motiongit_updates.py")
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)
URL = monitor.WATCH_URL


def sitemap(paths=()):
    return '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(
        '<url><loc>https://motiongit.com' + path + '</loc></url>' for path in paths) + '</urlset>'


def catalog(version="2.7.17-alpha.2"):
    return {"format": "motiongit.catalog/1", "templates": [{"website": URL, "repositoryId": "314486",
        "version": version, "title": {"zh": "测试模板"},
        "download": {"type": "official-page", "availability": "check-official-page"}}]}


def listing(next_page=False, url=URL, total=1):
    return (f'<a href="/templates?status=innovation">Innovation</a><article class="vcard" data-content-type="template">'
            f'<a class="vthumb" href="{url}"></a><h3>测试模板</h3></article>'
            f'<div class="idx-meta"><span>{total} results</span></div>'
            f'<div class="market-bottom"><span>Total {total} video templates</span></div><nav class="pager">'
            + ('<a href="/templates?page=2">Next</a>' if next_page else '<span class="dis">Next</span>') + '</nav>')


def detail(version="2.7.17-alpha.3"):
    return (f'<span class="mono-pill">v{version}</span><div class="repo-acquire"><span class="get-price">Free</span>'
            '<a href="/login?next=example">Download</a></div><li class="template-update-entry">'
            '<time datetime="2026-10-27T05:08:54.000Z"></time><p>修复标题。</p></li>')


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.pinned = monitor.normalize_catalog(catalog())
        self.state = monitor.initial_state(self.pinned)

    def test_initial_pinned_baseline_only_reports_actual_change(self):
        new = monitor.normalize_catalog(catalog("2.7.17-alpha.3"))
        monitor.apply_observation(self.state, "public_catalog", new, "one")
        event = next(iter(self.state["pending"].values()))
        self.assertEqual(len(self.state["pending"]), 1)
        self.assertEqual(event["kind"], "version")
        self.assertEqual(event["before"], "2.7.17-alpha.2")

    def test_counters_titles_and_release_notes_are_not_changes(self):
        new = copy.deepcopy(self.pinned)
        new[URL].update(download_count=900, stars=50, title="changed", release_note="new prose")
        self.assertEqual(monitor.compare(self.pinned, new), [])

    def test_pending_survives_repeat_and_explicit_ack_is_idempotent(self):
        new = monitor.normalize_catalog(catalog("2.7.17-alpha.3"))
        monitor.apply_observation(self.state, "public_catalog", new, "one")
        event_id = next(iter(self.state["pending"]))
        monitor.apply_observation(self.state, "public_catalog", new, "two")
        self.assertEqual(list(self.state["pending"]), [event_id])
        self.assertEqual(self.state["acknowledged"], {})
        monitor.acknowledge(self.state, [event_id], "three")
        monitor.acknowledge(self.state, [event_id], "four")
        self.assertFalse(self.state["pending"])
        self.assertEqual(self.state["acknowledged"][event_id]["acknowledged_at"], "three")

    def test_unknown_ack_does_not_remove_pending(self):
        monitor.apply_observation(self.state, "public_catalog", monitor.normalize_catalog(catalog("3.0.0")), "one")
        before = copy.deepcopy(self.state)
        with self.assertRaises(ValueError):
            monitor.acknowledge(self.state, list(self.state["pending"]) + ["not-an-event"], "two")
        self.assertEqual(self.state, before)

    def test_temporarily_missing_not_deleted_or_reported_as_new_on_return(self):
        result = monitor.apply_observation(self.state, "public_catalog", {}, "one")
        self.assertEqual(result["temporarily_absent"], [URL])
        self.assertIn(URL, self.state["sources"]["public_catalog"]["baseline"])
        monitor.apply_observation(self.state, "public_catalog", self.pinned, "two")
        self.assertFalse(self.state["pending"])

    def test_failed_source_preserves_baselines_and_pending(self):
        before = copy.deepcopy(self.state)
        def fail(url):
            raise TimeoutError("offline")
        report = monitor.run_check(self.state, fail)
        self.assertEqual(self.state, before)
        self.assertTrue(all(s["baseline_preserved"] for s in report["sources"].values()))

    def test_source_failure_does_not_block_other_source_change(self):
        def fetch(url):
            if url == monitor.CATALOG_URL:
                return json.dumps(catalog("2.7.17-alpha.3"))
            raise TimeoutError("site unavailable")
        before = copy.deepcopy(self.state["sources"]["official_directory"])
        report = monitor.run_check(self.state, fetch)
        self.assertEqual(report["sources"]["public_catalog"]["status"], "ok")
        self.assertEqual(self.state["sources"]["official_directory"], before)
        self.assertEqual(len(self.state["pending"]), 1)

    def test_actual_pagination_and_innovation_are_followed(self):
        visited = []
        other = "https://motiongit.com/@test/other"
        def fetch(url):
            visited.append(url)
            if url == monitor.SITEMAP_URL:
                return sitemap()
            if url in (URL, other):
                return detail()
            if url == monitor.LISTING_URL:
                return listing(next_page=True, total=2)
            if url == monitor.LISTING_URL + "?page=2":
                return listing(url=other, total=2)
            return listing()
        entries, pages = monitor.collect_directory(fetch)
        self.assertEqual(len(entries), 2)
        self.assertIn(monitor.LISTING_URL + "?page=2", pages)
        self.assertIn(monitor.LISTING_URL + "?status=innovation", pages)
        self.assertNotIn(monitor.LISTING_URL + "?status=claim", visited)

    def test_lost_pagination_cannot_advance_good_baseline(self):
        with self.assertRaises(ValueError):
            monitor.collect_directory(lambda url: listing(total=2))
        with self.assertRaises(ValueError):
            monitor.parse_listing(listing().replace('<span class="dis">Next</span>', ''), monitor.LISTING_URL)

    def test_one_acquire_retry_recovers_only_with_explicit_login_signal(self):
        attempts = []
        def fetch(url):
            if url == monitor.SITEMAP_URL:
                return sitemap()
            if url == URL:
                attempts.append(url)
                return detail().replace('/login?', '/unknown?') if len(attempts) == 1 else detail()
            return listing()
        entries, _ = monitor.collect_directory(fetch)
        self.assertEqual(len(attempts), 2)
        self.assertTrue(entries[URL]["availability"]["login_required"])
        self.assertTrue(entries[URL]["monitor_diagnostics"]["acquire_retry_recovered"])

    def test_persistent_unknown_acquire_has_url_and_keeps_good_baseline(self):
        attempts = []
        before = copy.deepcopy(self.state["sources"]["official_directory"])
        def fetch(url):
            if url == monitor.SITEMAP_URL:
                return sitemap()
            if url == monitor.CATALOG_URL:
                return json.dumps(catalog())
            if url == URL:
                attempts.append(url)
                return detail().replace('/login?', '/unknown?')
            return listing()
        report = monitor.run_check(self.state, fetch)
        failed = report["sources"]["official_directory"]
        self.assertEqual(len(attempts), 2)
        self.assertEqual(failed["status"], "failed")
        self.assertTrue(failed["baseline_preserved"])
        self.assertIn(URL, failed["message"])
        self.assertIn("login=False", failed["message"])
        self.assertEqual(self.state["sources"]["official_directory"], before)

    def test_acknowledged_transition_recurrence_is_not_suppressed(self):
        new = monitor.normalize_catalog(catalog("3.0.0"))
        monitor.apply_observation(self.state, "public_catalog", new, "one")
        first_id = next(iter(self.state["pending"]))
        monitor.acknowledge(self.state, [first_id], "two")
        monitor.apply_observation(self.state, "public_catalog", self.pinned, "three")
        monitor.acknowledge(self.state, list(self.state["pending"]), "four")
        monitor.apply_observation(self.state, "public_catalog", new, "five")
        self.assertEqual(len(self.state["pending"]), 1)
        self.assertNotEqual(next(iter(self.state["pending"])), first_id)

    def test_late_corroborating_source_does_not_duplicate_ack(self):
        new = monitor.normalize_catalog(catalog("3.0.0"))
        monitor.apply_observation(self.state, "public_catalog", new, "one")
        monitor.acknowledge(self.state, list(self.state["pending"]), "two")
        monitor.apply_observation(self.state, "official_directory", new, "three")
        self.assertFalse(self.state["pending"])

    def test_verified_integration_updates_reference_without_mutating_frozen_version(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "integrations.json"
            path.write_text(json.dumps({"schema_version": 1, "integrations": [
                {"id": "new-clip", "integrated_at": "2026-10-28", "qa": {"state": "verified_demo"},
                 "source": {"url": URL, "package_id": "314486", "version": "2.7.17-alpha.3",
                            "sha256": "a" * 64, "official": True}},
                {"id": "unverified", "qa": {"state": "pending"}, "source": {"version": "9.0.0"}}
            ]}), encoding="utf-8")
            result = monitor.local_references(self.pinned, path)["packages"]["314486"]
            self.assertEqual(result["frozen_catalog_version"], "2.7.17-alpha.2")
            self.assertEqual(result["latest_recorded_verified_version"], "2.7.17-alpha.3")

    def test_pinned_kinetic_edition_context_is_precise_and_does_not_change_pending(self):
        url = "https://motiongit.com/@adunext/385712"
        raw = catalog("0.2.7-open-beta")
        record = raw["templates"][0]
        record.update(website=url, repositoryId="385712", repository="https://github.com/motiontemplates/385712",
                      openSource=True, ratio="16:9", additionalDemos=[{
                          "version": "0.2.38-open-beta", "ratio": "9:16",
                          "sourceEdition": {"version": "0.2.7-open-beta", "ratio": "16:9"},
                          "editionNote": {"zh": "官网中文竖屏与 GitHub 开源包分别标版。"}}])
        pinned = monitor.normalize_catalog(raw)
        state = monitor.initial_state(pinned)
        observed = {url: dict(pinned[url], version="0.2.40-alpha.1")}
        monitor.apply_observation(state, "official_directory", observed, "one")
        event = next(iter(state["pending"].values()))
        self.assertEqual(event["source_baselines"]["official_directory"], "repo_pinned_snapshot")
        # The existing first-run event has no stored origin; its exact ID is handled.
        legacy = copy.deepcopy(event)
        legacy.pop("source_baselines")
        self.assertEqual(legacy["event_id"], monitor.LEGACY_PINNED_EDITION_EVENT)
        before = copy.deepcopy(state)
        for candidate in (event, legacy):
            context = monitor.annotate_pending_events([candidate], pinned)[0]["baseline_context"]
            self.assertEqual(context["classification"], "initial_cross_distribution_comparison")
            self.assertEqual(context["before_source"]["repository"], record["repository"])
        self.assertEqual(state, before)
        self.assertNotIn("baseline_context", event)
        # A later website observation with the same prerelease suffixes is an ordinary update.
        later = dict(event, event_id="later-event", source_baselines={"official_directory": "public_observation"})
        self.assertNotIn("baseline_context", monitor.annotate_pending_events([later], pinned)[0])
        # Suffixes alone, without structured distribution evidence, never trigger the label.
        without_evidence = copy.deepcopy(pinned)
        without_evidence[url]["distribution_editions"] = []
        self.assertNotIn("baseline_context", monitor.annotate_pending_events([event], without_evidence)[0])

    def test_unknown_initial_availability_is_not_a_change(self):
        item = monitor.parse_detail(detail("2.7.17-alpha.2"), {"url": URL, "title": "测试"})
        monitor.apply_observation(self.state, "official_directory", {URL: item}, "one")
        self.assertFalse(self.state["pending"])
        changed = copy.deepcopy(item)
        changed["availability"]["social_locked"] = True
        monitor.apply_observation(self.state, "official_directory", {URL: changed}, "two")
        self.assertEqual(next(iter(self.state["pending"].values()))["kind"], "availability")

    def test_invalid_empty_sources_rejected(self):
        with self.assertRaises(ValueError):
            monitor.normalize_catalog({"format": "motiongit.catalog/1", "templates": []})
        with self.assertRaises(ValueError):
            monitor.parse_listing("<html>login</html>", monitor.LISTING_URL)
        with self.assertRaises(ValueError):
            monitor.parse_detail("<html>missing</html>", {"url": URL})

    def test_safe_url_and_atomic_json(self):
        with self.assertRaises(ValueError):
            monitor.canonical_detail("https://example.org/evil")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            monitor.atomic_json(path, self.state)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), self.state)
            with monitor.state_lock(path):
                with self.assertRaises(FileExistsError):
                    with monitor.state_lock(path):
                        pass
            self.assertFalse(path.with_suffix(".json.lock").exists())

    def test_new_detail_links_keep_existing_event_identity(self):
        self.assertEqual(monitor.canonical_detail(URL.replace('/@', '/')), URL)
        claim = 'https://motiongit.com/community/example'
        self.assertEqual(monitor.canonical_detail(claim), claim)
        for url in ['https://motiongit.com/help/download', 'https://motiongit.com/templates/c']:
            with self.assertRaises(ValueError):
                monitor.canonical_detail(url)

    def test_current_version_title_and_free_price_are_observed(self):
        html = detail().replace('<span class="mono-pill">v2.7.17-alpha.3</span>',
                                '<span class="mono-pill" title="v2.7.17-alpha.3">Updated today</span>')
        html = html.replace('class="get-price"', 'class="free"')
        parsed = monitor.parse_detail(html, {'url': URL})
        self.assertEqual(parsed['version'], '2.7.17-alpha.3')
        self.assertEqual(parsed['availability']['price_label'], 'Free')

    def test_prelaunch_has_no_invented_version_or_download(self):
        parsed = monitor.parse_detail('<section class="repo-acquire prelaunch-box">Coming soon</section>', {'url': URL})
        self.assertIsNone(parsed['version'])
        self.assertFalse(parsed['availability']['downloadable'])
        self.assertEqual(parsed['availability']['stage'], 'prelaunch')

    def test_discovered_claim_and_new_category_are_audited(self):
        claim = 'https://motiongit.com/community/new-reference'
        category = 'https://motiongit.com/templates/c/new-industry'
        visited = []
        def fetch(url):
            visited.append(url)
            if url == monitor.SITEMAP_URL:
                return sitemap(['/templates/c/new-industry', '/community/new-reference'])
            if url == category:
                return '<h1>New industry</h1>'
            if url == URL:
                return detail()
            if url == monitor.LISTING_URL + '?status=claim':
                return listing(url=claim)
            return listing() + '<a href="/templates?status=claim">Claim</a>'
        entries, pages = monitor.collect_directory(fetch)
        self.assertIn(claim, entries)
        self.assertEqual(entries[claim]['availability'], {'stage': 'claim', 'downloadable': False})
        self.assertNotIn(claim, visited)  # No need to read every unclaimed detail or video.
        self.assertIn(category, pages)
        self.assertIn(monitor.SITEMAP_URL, pages)

    def test_uncovered_sitemap_template_preserves_baseline(self):
        before = copy.deepcopy(self.state['sources']['official_directory'])
        def fetch(url):
            if url == monitor.CATALOG_URL:
                return json.dumps(catalog())
            if url == monitor.SITEMAP_URL:
                return sitemap(['/@other/new-section'])
            return listing()
        report = monitor.run_check(self.state, fetch)
        self.assertEqual(report['sources']['official_directory']['status'], 'failed')
        self.assertIn('outside scanned sections', report['sources']['official_directory']['message'])
        self.assertEqual(self.state['sources']['official_directory'], before)

    def test_ack_requires_delivery_flag(self):
        with self.assertRaises(SystemExit) as result:
            monitor.main(["ack", "--event-id", "x"])
        self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
