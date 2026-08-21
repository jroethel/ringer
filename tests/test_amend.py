import json
import tempfile
import unittest
from pathlib import Path

from ringer import append_amendment


class TestAmendAppend(unittest.TestCase):
    def test_append_then_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "runs.jsonl"
            path.write_text(
                json.dumps({"run_id": "r1", "task_key": "t1", "model": "glm-5.2",
                            "verdict": "FAIL", "logged_at": "2026-07-01T10:00:00+00:00"}) + "\n",
                encoding="utf-8")
            before = path.read_text(encoding="utf-8")

            appended = append_amendment(path, "r1", "t1", "check_bug", "why", "tester",
                                        now="2026-07-02T00:00:00+00:00")
            self.assertTrue(appended)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(lines))
            row = json.loads(lines[-1])
            self.assertEqual("amendment", row["type"])
            self.assertEqual("r1", row["run_id"])
            self.assertEqual("t1", row["task_key"])
            self.assertEqual("check_bug", row["reclassify"])
            self.assertEqual("why", row["note"])
            self.assertEqual("tester", row["identity"])
            self.assertEqual("2026-07-02T00:00:00+00:00", row["amended_at"])
            self.assertEqual("2026-07-02T00:00:00+00:00", row["logged_at"])  # survives --since
            self.assertEqual(before, lines[0] + "\n")  # original row byte-identical

            appended2 = append_amendment(path, "r1", "t1", "check_bug", "why", "tester",
                                         now="2026-07-03T00:00:00+00:00")
            self.assertFalse(appended2)  # same (run_id, task_key, reclassify) -> no-op
            self.assertEqual(2, len(path.read_text(encoding="utf-8").splitlines()))


if __name__ == "__main__":
    unittest.main()
