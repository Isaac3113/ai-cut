"""Protect installed local rules and verify pinned code before adaptation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import adapt_jianying_skill as installer


class JianyingInstallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="jianying-install-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.target = self.root / "installed"
        self.target.mkdir()
        original = b"upstream\n"
        (self.target / "SKILL.md").write_bytes(original.replace(b"\n", b"\r\n"))
        (self.target / "core.py").write_bytes(b"pinned-core\n")
        (self.root / "extensions").mkdir()
        lock = {"repository": "fixture/repo", "commit": "fixed-fixture", "git_blobs": {
            "SKILL.md": installer.git_blob(original),
            "core.py": installer.git_blob(b"pinned-core\n")}}
        (self.root / "extensions/jianying-source-lock.json").write_text(json.dumps(lock))
        adapter = self.root / "skill-adapters/jianying-editor"
        adapter.mkdir(parents=True)
        (adapter / "SKILL.md").write_bytes(b"scoped-local-rule\n")
        root_patch = patch.object(installer, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def test_preflight_is_read_only_and_roundtrip_preserves_upstream(self):
        installer.adapt(self.target, check=True)
        self.assertFalse((self.target / "local-adapter.json").exists())
        self.assertFalse((self.target / "UPSTREAM_SKILL.md").exists())
        installer.adapt(self.target)
        self.assertEqual((self.target / "UPSTREAM_SKILL.md").read_bytes(), b"upstream\n")
        installer.adapt(self.target)
        self.assertEqual((self.target / "SKILL.md").read_bytes(), b"scoped-local-rule\n")

    def test_modified_core_blocks_all_writes(self):
        original = (self.target / "SKILL.md").read_bytes()
        (self.target / "core.py").write_text("unexpected code")
        with self.assertRaisesRegex(ValueError, "Pinned upstream"):
            installer.adapt(self.target)
        self.assertEqual((self.target / "SKILL.md").read_bytes(), original)
        self.assertFalse((self.target / "UPSTREAM_SKILL.md").exists())

    def test_user_modified_rule_is_preserved(self):
        installer.adapt(self.target)
        (self.target / "SKILL.md").write_text("user's new rule")
        with self.assertRaisesRegex(ValueError, "User-modified"):
            installer.adapt(self.target)
        self.assertEqual((self.target / "SKILL.md").read_text(), "user's new rule")


if __name__ == "__main__":
    unittest.main()
