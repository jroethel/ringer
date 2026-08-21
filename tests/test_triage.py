import unittest

from ringer import triage_run


class TestTriageRun(unittest.TestCase):
    def _rows(self):
        return [
            {"run_id": "r1", "task_key": "t1", "model": "glm-5.2", "verdict": "FAIL",
             "notes": "raw_check_output_first_2000_chars: grep failed",
             "retry": False, "logged_at": "2026-07-01T10:00:00+00:00"},
            {"run_id": "r1", "task_key": "t2", "model": "glm-5.2", "verdict": "PASS",
             "notes": "", "retry": False, "logged_at": "2026-07-01T10:05:00+00:00"},
            {"run_id": "rX", "task_key": "tZ", "model": "glm-5.2", "verdict": "FAIL",
             "notes": "other run", "retry": False, "logged_at": "2026-07-01T10:06:00+00:00"},
            {"type": "amendment", "run_id": "r1", "task_key": "t1", "reclassify": "check_bug",
             "note": "check was wrong", "amended_at": "2026-07-02T00:00:00+00:00",
             "logged_at": "2026-07-02T00:00:00+00:00", "identity": "tester"},
        ]

    def test_lists_only_this_run_fails_with_amendment_inline(self):
        report = triage_run(self._rows(), "r1")
        self.assertEqual(1, len(report))          # only r1's FAIL, not the PASS, not run rX
        entry = report[0]
        self.assertEqual("t1", entry["task_key"])
        self.assertEqual("FAIL", entry["verdict"])
        self.assertTrue(entry["amended"])
        self.assertEqual("check was wrong", entry["amendment_note"])
        self.assertIn("grep failed", entry["check_excerpt"])


if __name__ == "__main__":
    unittest.main()
