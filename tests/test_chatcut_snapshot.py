import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('chatcut_audit', Path(__file__).parents[1] / 'scripts/audit_chatcut_snapshot.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChatcutSnapshotTests(unittest.TestCase):
    def fixture(self, path):
        path = path / 'source.bin'
        path.write_bytes(b'test source')
        source = {'startSeconds': 10, 'endSeconds': 11.1}
        def item(id, track):
            return {'id': id, 'trackId': track, 'kind': 'item', 'fromFrame': 0, 'timelineRange': {'fromFrame': 0, 'toFrame': 30}, 'sourceRange': dict(source)}
        return {'state': {'canvas': {'width': 1920, 'height': 1080}, 'fps': 30, 'durationInFrames': 30}, 'timeline': {'totalEntries': 2, 'entries': [item('v', 'video'), item('a', 'voice')]}, 'videoTrackId': 'video', 'voiceTrackId': 'voice', 'captions': {'hasMore': False, 'total': 1, 'text': '"overflow":false'}, 'sourcePath': str(path), 'sourceSha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_bound_source_and_matching_clock(self):
        with tempfile.TemporaryDirectory() as folder:
            result = module.audit(self.fixture(Path(folder)))
            self.assertTrue(result['structural_pass'])
            self.assertIn('listening', result['not_proven'])

    def test_gap_and_voice_drift_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            s = self.fixture(Path(folder)); s['timeline']['entries'][0]['timelineRange']['fromFrame'] = 1
            s['timeline']['entries'][1]['sourceRange']['endSeconds'] = 12
            result = module.audit(s)
            self.assertFalse(result['structural_pass'])
            self.assertGreaterEqual(len(result['errors']), 3)

    def test_partial_snapshot_and_caption_overflow_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            s = self.fixture(Path(folder)); s['timeline']['totalEntries'] = 3
            s['captions']['text'] = '"overflow":true'
            self.assertEqual(len(module.audit(s)['errors']), 2)

    def test_changed_original_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            s = self.fixture(Path(folder)); s['sourceSha256'] = '0' * 64
            self.assertIn('source hash mismatch', module.audit(s)['errors'])
