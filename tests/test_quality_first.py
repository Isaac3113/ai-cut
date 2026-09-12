"""Quality gate contracts with synthetic file fixtures, never real media rendering."""
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from talking_head_editor import quality
from talking_head_editor.util import EditorError, atomic_json, file_hash, read_json


class QualityFirstTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job = self.root/'job'
        video = self.job/'renders/f/landscape/final.mp4'
        source = self.job/'media/source.mp4'
        video.parent.mkdir(parents=True)
        source.parent.mkdir(parents=True)
        source.write_bytes(b'synthetic source marker; not playable media')
        video.write_bytes(b'synthetic export marker; not playable media')
        (video.parent/'captions.ass').write_text('test fixture ASS', encoding='utf-8')
        srt = video.parent/'captions.srt'
        srt.write_text('1\n00:00:01,000 --> 00:00:02,000\nfixture\n', encoding='utf-8')
        cues = [{'start': 1., 'end': 2., 'lines': ['fixture'], 'max_line_width': 80},
                {'start': 5., 'end': 6., 'lines': ['only'], 'max_line_width': 40}]
        atomic_json(video.parent/'captions.json', cues)
        self.r = {'schema_version': 1, 'complete': True, 'revision': 1, 'fingerprint': 'f',
                  'mode': 'final', 'requested_formats': ['landscape'], 'expected_duration': 10.,
                  'files': {'landscape': {'path': video.relative_to(self.job).as_posix(),
                            'sha256': file_hash(video), 'width': 1920, 'height': 1080,
                            'subtitles': srt.relative_to(self.job).as_posix()}},
                  'clips': [{'id': 'c', 'output_start': 0., 'output_duration': 10.}]}
        self.p = {'schema_version': 1, 'revision': 1, 'fixture': False,
                  'source': {'path': source.relative_to(self.job).as_posix(), 'sha256': file_hash(source),
                             'probe': {'streams': [{'codec_type': 'video', 'width': 1920, 'height': 1080}]}},
                  'assets': {}, 'plan': {'output_formats': ['landscape'],
                                        'style': {'loudness_lufs': -16, 'true_peak_db': -1}},
                  'delivery': {'fingerprint': 'f'}}
        self.q = {'fingerprint': 'f', 'technical_pass': True, 'variants': {'landscape': {
                  'sha256': file_hash(video), 'detections': [], 'subtitle_sha256': file_hash(srt),
                  'captions_sha256': file_hash(video.parent/'captions.json'),
                  'ass_sha256': file_hash(video.parent/'captions.ass'), 'caption_count': 2}}}
        self.review = {'fingerprint': 'f', 'reviewer': 'unit test declarations, no human inspection',
                       'variants': {'landscape': {
                           'checks': {c: {'passed': True, 'evidence': 'synthetic contract fixture'}
                                      for c in quality.REVIEW_CATEGORIES},
                           'detector_dispositions': [],
                           'timing_checkpoints': [{'output_time': t, 'error_ms': 0,
                                                  'evidence': 'synthetic checkpoint'} for t in (1, 5, 9)]}}}
        self.save_fixture()

    def save_fixture(self):
        atomic_json(self.job/'project.json', self.p)
        atomic_json(self.job/'latest-render.json', self.r)
        atomic_json(self.job/'latest-qa.json', self.q)
        atomic_json(self.job/'review/f/review.json', self.review)

    def completed_review(self):
        result = copy.deepcopy(self.review)
        checks = {c: {'status': 'pass', 'evidence': 'synthetic gate fixture, not real inspection'}
                  for c in quality.QUALITY_CATEGORIES}
        checks['full_watch'].update(mode='continuous_video', range_seconds=[0., 10.])
        checks['full_listen'].update(mode='continuous_audio', range_seconds=[0., 10.])
        checks['full_captions'].update(mode='all_captions', reviewed_cue_count=2)
        result['variants']['landscape']['quality_checks'] = checks
        return result

    def expect(self, code, call):
        with self.assertRaises(EditorError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_legacy_six_checks_remain_readable_but_do_not_approve_new_final_gate(self):
        quality.validate_review(self.review, self.q, self.r)
        self.expect('quality_review_incomplete',
                    lambda: quality.validate_review(self.review, self.q, self.r, require_quality=True))
        quality.validate_review(self.completed_review(), self.q, self.r, require_quality=True)

    def test_states_distinguish_pending_fail_and_not_applicable(self):
        for state in ('unverified', 'fail'):
            with self.subTest(state=state):
                review = self.completed_review()
                review['variants']['landscape']['quality_checks']['color']['status'] = state
                quality.validate_quality_review(review, self.q, self.r)
                self.expect('quality_review_incomplete',
                            lambda: quality.validate_quality_review(review, self.q, self.r, require_complete=True))
        review = self.completed_review()
        color = review['variants']['landscape']['quality_checks']['color']
        color.update(status='not_applicable', reason='Synthetic case has no image to grade')
        quality.validate_quality_review(review, self.q, self.r, require_complete=True)
        del color['reason']
        self.expect('quality_review_evidence', lambda: quality.validate_quality_review(review, self.q, self.r))
        color.update(status='reviewed')
        self.expect('quality_review_status', lambda: quality.validate_quality_review(review, self.q, self.r))

    def test_whole_output_checks_cannot_be_replaced_by_samples_or_na(self):
        for category in ('full_watch', 'full_listen'):
            for change, code in (({'mode': 'contact_sheet'}, 'quality_review_mode'),
                                 ({'range_seconds': [1., 9.]}, 'quality_review_coverage'),
                                 ({'range_seconds': [0., float('nan')]}, 'quality_review_coverage'),
                                 ({'status': 'not_applicable', 'reason': 'not available'}, 'quality_review_not_applicable')):
                with self.subTest(category=category, change=change):
                    review = self.completed_review()
                    review['variants']['landscape']['quality_checks'][category].update(change)
                    self.expect(code, lambda: quality.validate_quality_review(review, self.q, self.r, require_complete=True))

    def test_all_captions_need_current_qa_count_and_exact_fingerprint(self):
        review = self.completed_review()
        review['variants']['landscape']['quality_checks']['full_captions']['reviewed_cue_count'] = 1
        self.expect('quality_caption_coverage', lambda: quality.validate_quality_review(review, self.q, self.r, require_complete=True))
        review = self.completed_review()
        review['fingerprint'] = 'old-render'
        self.expect('review_identity', lambda: quality.validate_quality_review(review, self.q, self.r, require_complete=True))
        q = copy.deepcopy(self.q)
        del q['variants']['landscape']['caption_count']
        self.expect('quality_caption_coverage', lambda: quality.validate_quality_review(self.completed_review(), q, self.r, require_complete=True))

    def test_real_package_entry_blocks_missing_whole_watch_or_listen(self):
        for category in ('full_watch', 'full_listen'):
            with self.subTest(category=category):
                self.review = self.completed_review()
                del self.review['variants']['landscape']['quality_checks'][category]
                self.save_fixture()
                target = self.root/f'blocked-{category}.zip'
                self.expect('quality_review_incomplete', lambda: quality.package(self.job, target))
                self.assertFalse(target.exists())

    def test_draft_package_stays_available_and_complete_gate_allows_final_package(self):
        draft = self.root/'draft.zip'
        result = quality.package(self.job, draft, draft=True)
        self.assertTrue(result['draft'])
        with zipfile.ZipFile(draft) as z:
            self.assertIn('DRAFT', z.read('PACKAGE-STATUS.txt').decode())
        self.review = self.completed_review()
        self.save_fixture()
        final = self.root/'complete.zip'
        result = quality.package(self.job, final)
        self.assertFalse(result['draft'])
        with zipfile.ZipFile(final) as z:
            self.assertIn('Reviewed export', z.read('PACKAGE-STATUS.txt').decode())

    def test_record_review_does_not_promote_legacy_draft_to_final_quality(self):
        self.expect('quality_review_incomplete', lambda: quality.record_review(self.job, self.review))
        self.r['mode'] = 'draft'
        self.save_fixture()
        result = quality.record_review(self.job, self.review)
        self.assertEqual(result['status'], 'draft_review')

    def test_qa_uses_plan_peak_target_and_generates_unverified_check_template(self):
        info = {'format': {'duration': '10'}, 'streams': [
            {'codec_type': 'video', 'width': 1920, 'height': 1080, 'codec_name': 'h264',
             'avg_frame_rate': '30/1', 'duration': '10', 'start_time': '0'},
            {'codec_type': 'audio', 'codec_name': 'aac', 'duration': '10', 'start_time': '0'}]}
        stats = {'input_i': '-16.00', 'input_tp': '-0.72', 'output_tp': '-1.00'}
        with patch.object(quality, 'probe', return_value=info), \
                patch.object(quality, 'run', return_value=('', json.dumps(stats))) as run_mock, \
                patch.object(quality, 'executable', return_value='not-executed-ffmpeg'), \
                patch.object(quality, 'contact_sheet', return_value='synthetic-sheet.jpg'):
            result = quality.qa(self.job)
        self.assertFalse(result['technical_pass'])
        q = read_json(self.job/'latest-qa.json')
        self.assertIn('exceeds target -1', q['variants']['landscape']['failures'][0])
        self.assertEqual(q['variants']['landscape']['audio_targets']['true_peak_db'], -1)
        self.assertEqual(q['variants']['landscape']['caption_count'], 2)
        template = read_json(Path(result['review_template']))
        checks = template['variants']['landscape']['quality_checks']
        self.assertEqual(set(checks), set(quality.QUALITY_CATEGORIES))
        self.assertTrue(all(c['status'] == 'unverified' for c in checks.values()))
        self.assertEqual(run_mock.call_count, 1)
        self.assertEqual(quality.loudness_failures({'input_i': '-16', 'input_tp': '-1'}, {'true_peak_db': -1}), [])
        self.assertTrue(quality.loudness_failures({'input_i': 'nan', 'input_tp': '-1'}, {}))

    def test_partial_review_is_saved_without_approving_delivery(self):
        self.p['delivery'] = None
        self.save_fixture()
        review = copy.deepcopy(self.review)
        review['variants']['landscape']['quality_checks'] = quality.quality_check_template()
        result = quality.record_progress(self.job, review)
        self.assertFalse(result['delivery_approved'])
        self.assertIsNone(read_json(self.job/'project.json')['delivery'])
        self.assertTrue((self.job/'review/f/review-progress.json').is_file())

    def test_changed_ass_sidecar_invalidates_review_and_final_package(self):
        self.review = self.completed_review()
        self.save_fixture()
        (self.job/'renders/f/landscape/captions.ass').write_text('changed style', encoding='utf-8')
        self.expect('qa_changed', lambda: quality.record_review(self.job, self.review))
        self.expect('qa_changed', lambda: quality.package(self.job, self.root/'stale.zip'))


if __name__ == '__main__':
    unittest.main()
