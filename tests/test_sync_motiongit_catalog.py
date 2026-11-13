from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sync_motiongit_catalog", ROOT / "scripts/sync_motiongit_catalog.py")
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)
STAMP = "2026-11-13T00:00:00+00:00"


def source(ident="123", slug="one", version="2.0.0", group="talk"):
    return {"repositoryId": ident, "templateId": int(ident), "website": "https://motiongit.com/@author/" + slug,
            "version": version, "title": {"zh": "官方名称"}, "summary": {"zh": "官方说明"}, "group": group,
            "ratio": "16:9", "demo": "https://media.example.com/" + slug + ".mp4",
            "poster": "https://media.example.com/" + slug + ".jpg",
            "download": {"type": "official-page", "availability": "check-official-page"}}


def catalog(*rows, previews=None):
    return {"format": "motiongit.catalog/1", "templates": list(rows), "previews": previews or [],
            "listing": {"templateCount": len(rows), "previewCount": len(previews or [])}}


def local(row=None):
    row = row or source()
    return {"id": "existing-stable-id", "source_id": row["repositoryId"], "source_template_id": row["templateId"],
            "source_url": row["website"], "label_zh": "旧名", "layer": "style", "version": "1.0.0", "ratio": "16:9",
            "source_group": "talk", "category_zh": "口播与讲解", "validation": {"state": "old-demo-only", "scope": "old version"},
            "license": "previous evidence", "demos": [{"kind": "own", "path": "demos/old.mp4", "sha256": "a" * 64},
                                                     {"kind": "official", "url": "https://media.example.com/obsolete.mp4"}]}


def styles(*rows):
    return {"schema_version": 1, "entries": list(rows), "previews": [], "categories": []}


class SyncMotionGitCatalogTests(unittest.TestCase):
    def run_sync(self, cat=None, old=None, snapshot=None, directory=None):
        return sync.synchronize(cat or catalog(source()), snapshot or catalog(source(version="1.0.0")), old or styles(local()), directory, checked_at=STAMP)

    def test_updated_source_preserves_stable_id_local_demo_and_validation(self):
        previous = styles(local()); before = deepcopy(previous)
        _, result = self.run_sync(old=previous)
        row = result["entries"][0]
        self.assertEqual(row["id"], "existing-stable-id")
        self.assertEqual(row["version"], "2.0.0")
        self.assertEqual(row["validation"], previous["entries"][0]["validation"])
        self.assertEqual(row["frozen_validation_reference"]["version"], "1.0.0")
        self.assertEqual(row["demos"][0], previous["entries"][0]["demos"][0])
        self.assertNotIn("obsolete", str(row["demos"]))
        self.assertEqual(previous, before)

    def test_new_categories_and_variants_are_not_filtered(self):
        item = source("456", "innovation", group="new-industry")
        item["additionalDemos"] = [{"ratio": "9:16", "version": "3.0.0", "demo": "https://media.example.com/portrait.mp4",
                                     "sourceEdition": {"version": "2.0.0", "ratio": "16:9"}}]
        _, result = self.run_sync(cat=catalog(source(), item))
        row = next(row for row in result["entries"] if row["source_id"] == "456")
        self.assertEqual(row["official_group"], "new-industry")
        self.assertEqual(row["category_zh"], "分类待核对")
        self.assertEqual(row["variants"][0]["version"], "3.0.0")
        self.assertEqual(row["variants"][0]["source_edition"]["version"], "2.0.0")
        self.assertEqual(len(row["demos"]), 2)

    def test_website_alias_and_independent_version_do_not_overwrite_catalog(self):
        directory = {"records": {"one": {"url": "https://motiongit.com/author/one", "sections": ["default"],
                      "categories": [{"id": "talk", "title": "口播视频"}],
                      "detail": {"version": "9.0.0", "availability": {"price_label": "收费", "login_required": True, "observed_acquire_section": True}}}}}
        _, result = self.run_sync(directory=directory)
        self.assertEqual(len(result["entries"]), 1)
        row = result["entries"][0]
        self.assertEqual(row["version"], "2.0.0")
        self.assertEqual(row["website_version"], "9.0.0")
        self.assertEqual(row["source_url"], "https://motiongit.com/@author/one")
        self.assertIn("需登录", row["availability"])
        self.assertEqual(row["official_categories"][0]["id"], "talk")

    def test_absent_source_is_retained_and_marked(self):
        absent = source("789", "absent")
        old = local(absent); old["id"] = "absent-stable-id"
        snapshot, result = self.run_sync(old=styles(local(), old), snapshot=catalog(source(), absent))
        row = next(row for row in result["entries"] if row["id"] == "absent-stable-id")
        self.assertEqual(row["source_observation"]["catalog"], "temporarily_absent")
        self.assertIn("absent-stable-id", result["source_manifest"]["retained_absent_entry_ids"])
        self.assertEqual(snapshot["listing"]["templateCount"], 1)
        self.assertEqual(len(snapshot["templates"]), 2)

    def test_claim_cards_are_distinct_unversioned_previews_and_idempotent(self):
        directory = {"records": {"claim": {"url": "https://motiongit.com/community/example-123", "title": "待认领作品", "sections": ["claim"],
                      "stage": "claim", "ratio": "待认领 9:16", "poster": "https://media.example.com/claim.jpg", "demo": "https://media.example.com/claim.mp4"}}}
        snapshot, result = self.run_sync(directory=directory)
        claim = result["previews"][0]
        self.assertEqual(claim["stage"], "claim")
        self.assertIsNone(claim["version"])
        self.assertTrue(claim["preview_only"])
        self.assertEqual(claim["ratio"], "9:16")
        self.assertEqual(claim["source_observation"]["catalog"], "not_in_collection")
        snapshot2, result2 = self.run_sync(old=result, snapshot=snapshot, directory=directory)
        self.assertEqual(result2, result)
        self.assertEqual(snapshot2, snapshot)

    def test_previews_are_not_duplicated_by_website_listing(self):
        preview = {"previewId": "industry-1", "website": "https://motiongit.com/@author/preview", "title": {"zh": "行业预告"}, "group": "prelaunch", "ratio": "9:16"}
        directory = {"records": {"preview": {"url": "https://motiongit.com/author/preview", "title": "行业预告", "sections": ["default"], "detail": {"availability": {"prelaunch": True}}}}}
        _, result = self.run_sync(cat=catalog(source(), previews=[preview]), directory=directory)
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(len(result["previews"]), 1)
        self.assertEqual(result["previews"][0]["website_status"], "prelaunch")
        self.assertIn("no_demo_reason", result["previews"][0])

    def test_promotion_keeps_preview_id(self):
        old = local(); old.update(id="existing-preview-id", layer="preview", preview_only=True)
        previous = styles(); previous["previews"] = [old]
        _, result = self.run_sync(old=previous)
        self.assertEqual(result["entries"][0]["id"], "existing-preview-id")
        self.assertEqual(result["entries"][0]["previous_kind"], "preview")
        self.assertFalse(result["previews"])

    def test_missing_or_duplicate_metadata_fails_without_mutating_inputs(self):
        cat = catalog(source()); cat["listing"]["templateCount"] = 9
        before = deepcopy(cat)
        with self.assertRaisesRegex(ValueError, "declared count"):
            self.run_sync(cat=cat)
        self.assertEqual(cat, before)
        with self.assertRaisesRegex(ValueError, "duplicate official stable ID"):
            self.run_sync(cat=catalog(source(), source()))

    def test_executable_or_credential_urls_are_rejected(self):
        for url in ("javascript:alert(1)", "https://secret@example.com/demo.mp4"):
            row = source(); row["demo"] = url
            with self.assertRaisesRegex(ValueError, "Unsafe public"):
                self.run_sync(cat=catalog(row))

    def test_new_collection_rows_repeat_without_growing_or_changing_ids(self):
        cat = catalog(source(), source("456", "new", group="innovation"))
        snapshot, result = self.run_sync(cat=cat)
        snapshot2, result2 = self.run_sync(cat=cat, old=result, snapshot=snapshot)
        self.assertEqual(snapshot2, snapshot)
        self.assertEqual(result2, result)

    def test_complete_website_observation_refuses_missing_section_cards(self):
        directory = {"records": {}, "coverage": {"sections": {"claim": 774}, "unique_listing_urls": 0}}
        with self.assertRaisesRegex(ValueError, "section total"):
            self.run_sync(directory=directory)

    def test_missing_website_observation_does_not_report_claim_cards_absent(self):
        directory = {"records": {"claim": {"url": "https://motiongit.com/community/example-123", "title": "作品", "sections": ["claim"]}}}
        snapshot, result = self.run_sync(directory=directory)
        _, result2 = self.run_sync(old=result, snapshot=snapshot)
        claim = result2["previews"][0]
        self.assertEqual(claim["source_observation"], {"catalog": "not_in_collection", "website": "not_checked"})
        self.assertNotIn(claim["id"], result2["source_manifest"]["retained_absent_entry_ids"])

    def test_source_commit_uses_pinned_raw_instead_of_main(self):
        response = MagicMock()
        response.url = "https://raw.githubusercontent.com/motiontemplates/all/" + "a" * 40 + "/catalog.json"
        response.read.return_value = sync.encode(catalog(source()))
        response.__enter__.return_value = response
        with patch.object(sync, "urlopen", return_value=response) as opened:
            sync.fetch_catalog("a" * 40)
        self.assertEqual(opened.call_args.args[0].full_url, response.url)


if __name__ == "__main__":
    unittest.main()
