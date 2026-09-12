import copy
import time
import unittest
from unittest.mock import patch
from talking_head_editor import project
from talking_head_editor.render import render
from talking_head_editor.timeline import default_plan
from talking_head_editor.util import ROOT, load_job, EditorError, job_lock
from talking_head_editor.cli import unlock


class Revisions(unittest.TestCase):
    def setUp(self):
        root=ROOT/"work"/f"unit-{time.time_ns()}"; root.mkdir(parents=True)
        src=root/"dummy.mp4"; src.write_bytes(b"unit-test-source-not-a-playable-video")
        self.job=root/"job"
        with patch.object(project,"probe",return_value={"streams":[{"codec_type":"video"},{"codec_type":"audio"}],"format":{"duration":"10"}}):
            project.create(self.job,src)
        project.install_transcript(self.job,{"schema_version":1,"words":[{"id":"w1","text":"不是","start":1,"end":2}]},"user_verified")
        self.plan=default_plan(10,1); self.plan["semantic_review"]={"status":"reviewed","evidence":"unit test only"}
        project.apply_plan(self.job,self.plan)
    def test_real_final_requires_first_style_confirmation(self):
        with self.assertRaises(EditorError) as e: render(self.job,"final")
        self.assertEqual(e.exception.code,"style_confirmation_required")
    def test_stale_edit_cannot_clobber_new_revision(self):
        with self.assertRaises(EditorError) as e: project.apply_plan(self.job,self.plan)
        self.assertEqual(e.exception.code,"revision_conflict")
        self.assertEqual(load_job(self.job)[1]["revision"],2)
    def test_restore_is_new_revision_and_preserves_history(self):
        changed=copy.deepcopy(self.plan); changed["base_revision"]=2; changed["style"]["accent"]="#00FF00"
        project.apply_plan(self.job,changed)
        result=project.restore(self.job,2,3)
        self.assertEqual(result["revision"],4)
        self.assertEqual(load_job(self.job)[1]["plan"]["style"]["accent"],"#F7C95C")
        self.assertTrue((self.job/"history/r000003.json").exists())
    def test_active_lock_cannot_be_removed(self):
        with job_lock(self.job):
            with self.assertRaises(EditorError) as e: unlock(self.job)
            self.assertEqual(e.exception.code,"process_alive")
        self.assertFalse((self.job/".edit.lock").exists())
    def test_fixture_transcript_blocked_in_real_job(self):
        with self.assertRaises(EditorError) as e:
            project.install_transcript(self.job,{"schema_version":1,"words":[{"id":"w","text":"假","start":1,"end":2}]},"test_fixture")
        self.assertEqual(e.exception.code,"fixture_only")


if __name__=="__main__": unittest.main()
