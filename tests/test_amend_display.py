import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import ringer
from ringer import MODEL_SCOREBOARD_COLUMNS


def _amended_log(path):
    rows = [
        {"run_id": "r1", "task_key": "t1", "worker_engine": "opencode", "model": "glm-5.2",
         "task_type": "code-fix", "verdict": "FAIL", "duration_ms": 100, "worker_tokens": 10,
         "retry": False, "logged_at": "2026-07-01T10:00:00+00:00"},
        {"run_id": "r1", "task_key": "t1", "worker_engine": "opencode", "model": "glm-5.2",
         "task_type": "code-fix", "verdict": "PASS", "duration_ms": 100, "worker_tokens": 10,
         "retry": True, "logged_at": "2026-07-01T10:05:00+00:00"},
        {"run_id": "r2", "task_key": "t2", "worker_engine": "opencode", "model": "glm-5.2",
         "task_type": "code-fix", "verdict": "PASS", "duration_ms": 100, "worker_tokens": 10,
         "retry": False, "logged_at": "2026-07-01T11:00:00+00:00"},
        {"type": "amendment", "run_id": "r1", "task_key": "t1", "reclassify": "check_bug",
         "note": "check was wrong", "amended_at": "2026-07-02T00:00:00+00:00",
         "logged_at": "2026-07-02T00:00:00+00:00", "identity": "tester"},
    ]
    Path(path).write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


class TestAmendDisplay(unittest.TestCase):
    def test_amended_column_declared(self):
        self.assertIn("Amended", MODEL_SCOREBOARD_COLUMNS)

    def test_cli_table_has_header_and_group_carries_count(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "eval.jsonl"
            _amended_log(path)
            read_rows, skipped = ringer.read_model_log_rows(path)
            groups = ringer.aggregate_model_log_rows(read_rows)
            g = {(x["model"], x["task_type"]): x for x in groups}[("glm-5.2", "code-fix")]
            self.assertEqual(1, g["amended"])       # the value the column will render
            buf = io.StringIO()
            with redirect_stdout(buf):
                # real signature is (path, rows_read, skipped, groups) -- ringer.py:8431
                ringer.print_model_log_table(path, len(read_rows), skipped, groups)
            self.assertIn("Amended", buf.getvalue())  # header renders (the column exists)


if __name__ == "__main__":
    unittest.main()
