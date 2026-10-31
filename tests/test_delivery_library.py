import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("delivery_library", ROOT / "scripts/delivery_library.py")
library = importlib.util.module_from_spec(spec)
spec.loader.exec_module(library)


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "directory"
            for p in Path(root).rglob("*")}


class DeliveryLibraryTests(unittest.TestCase):
    def fixture(self, root, *, number=27, source="Codex剪辑", title="角色多角度", original="AIVD 11 - 原来的完整主题"):
        root = Path(root)
        repo = root / "code"
        repo.mkdir()
        delivery = root / "OneDrive" / "library"
        delivery.mkdir(parents=True)
        registry = root / "registry.json"
        index = root / "index.md"
        name = f"AIVD-{number:03d} - {source} - {title}"
        project = delivery / name
        project.mkdir()
        old = root / "OneDrive" / "working-hub" / "视频项目" / original
        pointer = old / "04_剪辑工程" / "本机剪辑工程.md"
        pointer.parent.mkdir(parents=True)
        frozen = repo / "work" / "videos" / "001-frozen-cache" / "04_剪辑工程"
        frozen.mkdir(parents=True)
        pointer.write_text("# Existing work\n\n" + str(frozen) + "\n", encoding="utf-8")
        row = {"ID": f"AIVD-{number:03d}", "SourceLabel": source, "OriginalName": original,
               "OriginalProject": str(old), "DestinationName": name, "DestinationProject": str(project),
               "HasVideo": False}
        data = {"ReservedIDs": ["AIVD-005", "AIVD-006"], "NextNewID": "AIVD-028", "Projects": [row]}
        registry.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        index.write_text(f"# Index\n下一支新片为AIVD-028。\n| {row['ID']} | {title} |\n| AIVD-005 | 保留 |\n| AIVD-006 | 保留 |\n", encoding="utf-8")
        settings = library.resolve_settings(delivery, registry, index, repo=repo, env={})
        return settings, data, row, project, frozen

    def test_settings_required_and_no_old_delivery_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "Missing delivery_library_root"):
                library.resolve_settings(repo=root, env={})
            self.assertEqual(list(root.iterdir()), [])

    def test_settings_precedence_and_runtime_is_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            config = settings["repo"] / "runtime.local.json"
            config.write_text(json.dumps({"ffmpeg": "keep-this", "delivery_library_root": str(settings["library_root"]),
                                          "delivery_registry": str(settings["registry"]),
                                          "delivery_asset_index": str(settings["asset_index"])}), encoding="utf-8")
            before = config.read_bytes()
            env = {"TALKING_HEAD_DELIVERY_LIBRARY_ROOT": "missing",
                   "TALKING_HEAD_DELIVERY_REGISTRY": "missing",
                   "TALKING_HEAD_DELIVERY_ASSET_INDEX": "missing"}
            explicit = library.resolve_settings(settings["library_root"], settings["registry"], settings["asset_index"],
                                                repo=settings["repo"], env=env)
            self.assertEqual(explicit["library_root"], settings["library_root"])
            configured = library.resolve_settings(repo=settings["repo"], env={})
            self.assertEqual(configured["registry"], settings["registry"])
            env = {"TALKING_HEAD_DELIVERY_LIBRARY_ROOT": str(settings["library_root"]),
                   "TALKING_HEAD_DELIVERY_REGISTRY": str(settings["registry"]),
                   "TALKING_HEAD_DELIVERY_ASSET_INDEX": str(settings["asset_index"])}
            self.assertEqual(library.resolve_settings(repo=settings["repo"], env=env)["asset_index"], settings["asset_index"])
            self.assertEqual(config.read_bytes(), before)

    def test_new_plan_is_028_without_counting_next_id_prose_or_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            before = snapshot(tmp)
            plan = library.plan(settings, title="下一条主题", stem_suffix="9比16_1.2倍")
            self.assertEqual(plan["project_id"], "AIVD-028")
            self.assertEqual(plan["project_name"], "AIVD-028 - Codex剪辑 - 下一条主题")
            self.assertEqual(Path(plan["video_path"]).parent.name, "AI 成片")
            self.assertTrue(Path(plan["video_path"]).name.endswith("_9比16_1.2倍_视频.mp4"))
            self.assertEqual({Path(p).parent.name for p in plan["cover_paths"].values()}, {"参考图"})
            self.assertEqual(plan["subtitles"], [])
            self.assertFalse(plan["id_reserved"])
            self.assertFalse(plan["project_exists"])
            self.assertEqual(snapshot(tmp), before)

    def test_code_work_and_custom_non_onedrive_library_never_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            custom=Path(tmp)/"custom-delivery"
            custom.mkdir()
            nested_repo=custom/"code"
            nested_repo.mkdir()
            for repo,work in ((nested_repo,Path(tmp)/"work"),
                              (settings["repo"],custom),
                              (settings["repo"],custom/"work"),
                              (settings["repo"],custom.parent)):
                with self.subTest(repo=repo,work=work),self.assertRaises(ValueError):
                    library.resolve_settings(custom,settings["registry"],settings["asset_index"],work,repo=repo,env={})

    def test_number_uses_all_platform_directories_index_and_reserved_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, data, _, _, _ = self.fixture(tmp)
            (settings["library_root"] / "AIVD-029 - Higgsfield - 新动画").mkdir()
            settings["asset_index"].write_text("| AIVD-030 | 已登记未导出 |\n下一支AIVD-999只是说明。", encoding="utf-8")
            data["ReservedIDs"].append("AIVD-031")
            settings["registry"].write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(library.plan(settings, title="另外一条")["project_id"], "AIVD-032")

    def test_snapshot_next_id_is_only_a_lower_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, data, _, _, _ = self.fixture(tmp)
            data["NextNewID"] = "AIVD-035"
            settings["registry"].write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(library.plan(settings, title="主题")["project_id"], "AIVD-035")

    def test_existing_alias_path_and_id_keep_mapping_and_frozen_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, row, project, frozen = self.fixture(tmp)
            before = snapshot(tmp)
            for selector in (row["ID"], row["OriginalName"], row["OriginalProject"]):
                with self.subTest(selector=selector):
                    plan = library.plan(settings, existing=selector)
                    self.assertEqual(Path(plan["project_directory"]), project)
                    self.assertEqual(plan["project_id"], "AIVD-027")
                    self.assertEqual(Path(plan["work"]["work_directory"]), frozen)
            self.assertEqual(snapshot(tmp), before)

    def test_existing_principal_source_is_not_changed_by_codex_reedit(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, row, _, _ = self.fixture(tmp, source="Higgsfield")
            self.assertEqual(library.plan(settings, existing=row["ID"])["source_label"], "Higgsfield")
            with self.assertRaisesRegex(ValueError, "principal source"):
                library.plan(settings, existing=row["ID"], source_label="Codex剪辑")
            with self.assertRaisesRegex(ValueError, "title conflict"):
                library.plan(settings, existing=row["ID"], title="不同作品")

    def test_unknown_legacy_and_reserved_ids_never_allocate_a_new_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            before = snapshot(tmp)
            for selector in ("AIVD6", "AIVD 6", "AIVD 5", "5-01", "AIVD-005", "AIVD-006", "AIVD-099"):
                with self.subTest(selector=selector), self.assertRaises(ValueError):
                    library.plan(settings, existing=selector)
            self.assertEqual(snapshot(tmp), before)

    def test_ambiguous_original_names_need_full_original_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, data, row, project, _ = self.fixture(tmp)
            second = dict(row, ID="AIVD-009", SourceLabel="即梦", OriginalProject=str(Path(tmp) / "other-work"),
                          DestinationName="AIVD-009 - 即梦 - 另一部片", DestinationProject=str(settings["library_root"] / "AIVD-009 - 即梦 - 另一部片"))
            data["Projects"].append(second)
            settings["registry"].write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "uniquely"):
                library.plan(settings, existing=row["OriginalName"])
            self.assertEqual(Path(library.plan(settings, existing=row["OriginalProject"])["project_directory"]), project)

    def test_existing_unmapped_future_id_does_not_infer_or_create_work_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            (settings["library_root"] / "AIVD-028 - 即梦 - 新作").mkdir()
            plan = library.plan(settings, existing="AIVD-028")
            self.assertIsNone(plan["work"]["work_directory"])
            self.assertIn("do not infer", plan["work"]["work_basis"])

    def test_missing_mapped_delivery_and_pointer_never_create_replacement_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, row, project, _ = self.fixture(tmp)
            project.rmdir()
            pointer=Path(row["OriginalProject"]) / "04_剪辑工程" / "本机剪辑工程.md"
            pointer.unlink()
            before=snapshot(tmp)
            result=library.plan(settings, existing=row["ID"])
            self.assertFalse(result["project_exists"])
            self.assertIsNone(result["work"]["work_directory"])
            self.assertFalse(result["work"]["work_entry_exists"])
            with self.assertRaisesRegex(ValueError, "does not exist"):
                library.audit(settings, existing=row["ID"])
            self.assertEqual(snapshot(tmp), before)

    def test_bad_registry_destination_duplicates_and_directory_conflict_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, data, row, project, _ = self.fixture(tmp)
            bad = dict(row, DestinationProject=str(Path(tmp) / row["DestinationName"]))
            data["Projects"] = [bad]
            settings["registry"].write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "destination"):
                library.plan(settings, title="新作")
            data["Projects"] = [row, row]
            settings["registry"].write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                library.plan(settings, title="新作")
            data["Projects"] = [row]
            settings["registry"].write_text(json.dumps(data), encoding="utf-8")
            (settings["library_root"] / "AIVD-027 - Codex剪辑 - 不同内容").mkdir()
            with self.assertRaises(ValueError):
                library.plan(settings, title="新作")

    def test_only_explicit_nonempty_existing_subtitles_are_planned(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            srt = Path(tmp) / "已有字幕.srt"
            srt.write_text("1\n00:00:00,000 --> 00:00:01,000\n你好\n", encoding="utf-8")
            txt = Path(tmp) / "已有字幕.txt"
            txt.write_text("你好\n", encoding="utf-8")
            before = snapshot(tmp)
            result = library.plan(settings, title="新作", subtitles=[srt, txt])
            self.assertEqual(len(result["subtitles"]), 2)
            self.assertTrue(all(Path(x["target"]).parent == Path(result["project_directory"]) for x in result["subtitles"]))
            self.assertEqual(snapshot(tmp), before)
            with self.assertRaises(ValueError):
                library.plan(settings, title="新作", subtitles=[srt, srt])
            with self.assertRaises(ValueError):
                library.plan(settings, title="新作", subtitles=[Path(tmp) / "missing.srt"])
            publication = Path(tmp) / "Facebook文案.txt"
            publication.write_text("不是字幕", encoding="utf-8")
            with self.assertRaises(ValueError):
                library.plan(settings, title="新作", subtitles=[publication])

    def test_other_existing_subtitle_formats_and_archived_multiple_srt_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, project, _ = self.fixture(tmp)
            subtitles=[]
            for extension in (".vtt", ".ass", ".ssa"):
                path=Path(tmp) / ("已有字幕"+extension)
                path.write_text("metadata test subtitle", encoding="utf-8")
                subtitles.append(path)
            result=library.plan(settings, title="新作", subtitles=subtitles)
            self.assertEqual({Path(x["target"]).suffix for x in result["subtitles"]}, {".vtt", ".ass", ".ssa"})
            for name in ("旧版字幕.srt", "另一比例字幕.srt", "已有字幕.vtt", "已有字幕.ass", "已有字幕.ssa"):
                (project/name).write_text("existing archival subtitle", encoding="utf-8")
            audit=library.audit(settings, existing="AIVD-027")
            self.assertTrue(audit["layout_valid"])
            self.assertEqual(len(audit["files"]), 5)
            self.assertFalse(audit["has_nonempty_video"])

    def test_image_only_023_is_a_partial_delivery_not_an_invented_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, project, _ = self.fixture(tmp, number=23)
            (project / "参考图").mkdir()
            (project / "参考图" / "封面.png").write_bytes(b"metadata fixture only")
            before = snapshot(tmp)
            result = library.audit(settings, existing="AIVD-023")
            self.assertTrue(result["layout_valid"])
            self.assertFalse(result["has_nonempty_video"])
            self.assertEqual(result["delivery_state"], "no_current_video_found")
            self.assertFalse((project / "AI 成片").exists())
            self.assertNotIn("sha256", result["files"][0])
            self.assertEqual(snapshot(tmp), before)

    def test_audit_checks_real_files_empty_folders_and_optional_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, project, _ = self.fixture(tmp)
            (project / "AI 成片").mkdir()
            video = project / "AI 成片" / "已交付.mp4"
            video.write_bytes(b"hash fixture only, not playable media")
            (project / "参考图").mkdir()
            (project / "Facebook文案.txt").write_text("work copy", encoding="utf-8")
            before = snapshot(tmp)
            result = library.audit(settings, existing="AIVD-027", include_hash=True)
            self.assertFalse(result["layout_valid"])
            self.assertTrue(result["has_nonempty_video"])
            self.assertEqual(result["files"][0]["sha256"], hashlib.sha256(video.read_bytes()).hexdigest())
            self.assertEqual(len(result["empty_directories"]), 1)
            self.assertIn(str(project / "Facebook文案.txt"), result["unexpected_paths"])
            self.assertIn("video_decode", result["not_verified"])
            self.assertEqual(snapshot(tmp), before)

    def test_invalid_new_names_and_duplicate_source_title_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            for title in (None, "", " bad", "bad.", "bad?", "../escape"):
                with self.subTest(title=title), self.assertRaises(ValueError):
                    library.plan(settings, title=title)
            with self.assertRaisesRegex(ValueError, "already exists"):
                library.plan(settings, title="角色多角度")
            with self.assertRaises(ValueError):
                library.plan(settings, title="新片", source_label="来源 - 混合")

    def test_cli_uses_explicit_roots_and_utf8_without_creating_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings, _, _, _, _ = self.fixture(tmp)
            before = snapshot(tmp)
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/delivery_library.py"), "plan",
                                     "--library-root", str(settings["library_root"]), "--registry", str(settings["registry"]),
                                     "--asset-index", str(settings["asset_index"]), "--work-root", str(settings["work_root"]),
                                     "--title", "中文新主题"], capture_output=True,
                                    env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"})
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
            self.assertEqual(json.loads(result.stdout.decode("utf-8"))["project_id"], "AIVD-028")
            self.assertEqual(snapshot(tmp), before)


if __name__ == "__main__":
    unittest.main()
