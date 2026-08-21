import json
import tempfile
import unittest
from pathlib import Path

from ringer import (read_model_log_rows, aggregate_model_log_rows,
                    aggregate_model_scoreboard_rows)


def _base():
    # glm-5.2 code-fix: task t1 = first-try FAIL then retry PASS (the check-bug task);
    #                    task t2 = clean first-try PASS.
    return [
        {"run_id": "r1", "task_key": "t1", "worker_engine": "opencode", "model": "glm-5.2",
         "task_type": "code-fix", "verdict": "FAIL", "duration_ms": 100, "worker_tokens": 10,
         "retry": False, "logged_at": "2026-07-01T10:00:00+00:00"},
        {"run_id": "r1", "task_key": "t1", "worker_engine": "opencode", "model": "glm-5.2",
         "task_type": "code-fix", "verdict": "PASS", "duration_ms": 100, "worker_tokens": 10,
         "retry": True, "logged_at": "2026-07-01T10:05:00+00:00"},
        {"run_id": "r2", "task_key": "t2", "worker_engine": "opencode", "model": "glm-5.2",
         "task_type": "code-fix", "verdict": "PASS", "duration_ms": 100, "worker_tokens": 10,
         "retry": False, "logged_at": "2026-07-01T11:00:00+00:00"},
    ]


def _amendment():
    return {"type": "amendment", "run_id": "r1", "task_key": "t1", "reclassify": "check_bug",
            "note": "check was wrong", "amended_at": "2026-07-02T00:00:00+00:00",
            "logged_at": "2026-07-02T00:00:00+00:00", "identity": "tester"}


def _read(rows):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "eval.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        read_rows, _ = read_model_log_rows(path)
    return read_rows


def _breakdown_tasks(model_group, task_type):
    # Field-name adjustment (spec field-name note): aggregate_model_scoreboard_rows
    # exposes the per-task-type breakdown as a LIST under "task_types" (breakdown_rows,
    # ringer.py ~7588), not a dict keyed by task_type. Find the row and read "tasks".
    for breakdown in model_group["task_types"]:
        if breakdown["task_type"] == task_type:
            return breakdown["tasks"]
    raise KeyError(task_type)


class TestAmendmentExclusion(unittest.TestCase):
    def test_pre_amend_first_try_is_half(self):
        groups = aggregate_model_log_rows(_read(_base()))
        g = {(x["model"], x["task_type"]): x for x in groups}[("glm-5.2", "code-fix")]
        self.assertEqual(0.5, g["first_try_pass_rate"])  # t1 first FAIL, t2 first PASS
        self.assertEqual(0, g.get("amended", 0))

    def test_amendment_lifts_first_try_and_is_visible(self):
        groups = aggregate_model_log_rows(_read(_base() + [_amendment()]))
        by = {(x["model"], x["task_type"]): x for x in groups}
        g = by[("glm-5.2", "code-fix")]
        self.assertEqual(1.0, g["first_try_pass_rate"])  # t1 dropped; only t2 (first PASS) counts
        self.assertEqual(1, g["amended"])                # correction visible
        self.assertIn("check was wrong", " ".join(g["amendments"]))
        # the amendment row must NOT self-group into a phantom empty-model group (F4):
        self.assertFalse(any(x.get("model", "") == "" for x in groups))

    def test_scoreboard_aggregator_also_excludes(self):
        # the tier/HTML/per-type surface uses aggregate_model_scoreboard_rows (F2):
        pre = aggregate_model_scoreboard_rows(_read(_base()))
        post = aggregate_model_scoreboard_rows(_read(_base() + [_amendment()]))
        pre_g = {x["model"]: x for x in pre}["glm-5.2"]
        post_g = {x["model"]: x for x in post}["glm-5.2"]
        self.assertLess(pre_g["first_try_pass_rate"], post_g["first_try_pass_rate"])
        # the code-fix per-type denominator shrank by the one voided task:
        pre_cf = _breakdown_tasks(pre_g, "code-fix")
        post_cf = _breakdown_tasks(post_g, "code-fix")
        self.assertEqual(pre_cf - 1, post_cf)

    def test_all_voided_group_is_dropped(self):
        # a model whose only task is voided leaves no misleading 0% row (F6):
        rows = [
            {"run_id": "r9", "task_key": "t9", "worker_engine": "opencode", "model": "solo",
             "task_type": "docs", "verdict": "FAIL", "duration_ms": 1, "worker_tokens": 1,
             "retry": False, "logged_at": "2026-07-01T10:00:00+00:00"},
            {"type": "amendment", "run_id": "r9", "task_key": "t9", "reclassify": "check_bug",
             "note": "bad check", "amended_at": "2026-07-02T00:00:00+00:00",
             "logged_at": "2026-07-02T00:00:00+00:00", "identity": "tester"},
        ]
        groups = aggregate_model_log_rows(_read(rows))
        self.assertFalse(any(x["model"] == "solo" for x in groups))


if __name__ == "__main__":
    unittest.main()
