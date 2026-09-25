#!/usr/bin/env python3
"""Offline FAIL replay harness: pairs, labels, resumable results, summary, review list."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

import ringer  # noqa: E402
from jev_stub import DUMMY_KEY, JevStub, fail_flag_response, jev_cli_env  # noqa: E402

SCRIPT = ROOT / "scripts" / "jev_fail_replay.py"
MINI_LOG = TESTS / "fixtures" / "jev_replay_mini_runs.jsonl"
MINI_LABELS = TESTS / "fixtures" / "jev_replay_mini_labels.json"


def first_fail_rows() -> dict[tuple[str, str], dict]:
    firsts: dict[tuple[str, str], dict] = {}
    for line in MINI_LOG.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("type") != "amendment" and row["verdict"] == "FAIL":
            firsts.setdefault((row["run_id"], row["task_key"]), row)
    return firsts


class ReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="ringer-jev-replay-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.out = self.root / "out"
        firsts = first_fail_rows()
        self.stub = JevStub({
            firsts[("r1", "a")]["spec"]: fail_flag_response("check", 0.95, "matches_requested"),
            firsts[("r1", "b")]["spec"]: fail_flag_response("check", 0.92, "out_of_scope"),
            firsts[("r2", "c")]["spec"]: fail_flag_response("check", 0.91, "syntax_or_transport"),
            firsts[("r3", "e")]["spec"]: fail_flag_response("spec", 0.8, "not_a_check_bug"),
            firsts[("r3", "f")]["spec"]: fail_flag_response("infra", 0.99, "not_a_check_bug"),
        })
        endpoint = self.stub.start()
        self.addCleanup(self.stub.stop)
        self.config = self.root / "config.toml"
        self.config.write_text(f'[jev]\nendpoint = "{endpoint}"\ntimeout_s = 2.0\n', encoding="utf-8")

    def replay(self, *extra: str, log: Path = MINI_LOG, labels: Path = MINI_LABELS, key: str | None = DUMMY_KEY):
        cmd = [sys.executable, "-B", str(SCRIPT), "--log", str(log), "--labels", str(labels),
               "--out", str(self.out), "--config", str(self.config), *extra]
        env = jev_cli_env(self.root, self.root / "ringer-home", key)
        return subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True, timeout=60, check=False)

    def results(self) -> list[dict]:
        path = self.out / "results.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def summary(self) -> dict:
        return json.loads((self.out / "summary.json").read_text(encoding="utf-8"))

    def test_dry_run_counts_pairs_and_makes_no_call(self) -> None:
        result = self.replay("--dry-run", key=None)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("pairs=5 check_bug=1 spec_defect=1 lane_outage=1 unamended=2 retry_passed=1\n", result.stdout)
        self.assertEqual(0, self.stub.count)
        self.assertFalse((self.out / "results.jsonl").exists())

    def test_replay_writes_results_summary_and_review_list(self) -> None:
        result = self.replay()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("replay: pairs=5 called=5 flags=3 check_bug_flagged=1 false_flags=1 hand_review=1 bar_met=false\n",
                      result.stdout)
        self.assertEqual(
            {"pairs": 5,
             "label_counts": {"check_bug": 1, "spec_defect": 1, "lane_outage": 1, "unamended": 2},
             "retry_passed": 1, "flags_total": 3, "check_bug_flagged": 1, "false_flags": 1, "known_wrong_flags": 1,
             "spec_defect_flagged": 0, "lane_outage_flagged": 0,
             "hand_review": [{"run_id": "r2", "task_key": "c"}],
             "bar": 9, "bar_met": False, "contract": "fail_flag-v1", "model": "jev-1.13.0",
             "cutoff": 0.9, "input_tokens": 4500},
            self.summary(),
        )
        results = {(row["run_id"], row["task_key"]): row for row in self.results()}
        self.assertEqual(5, len(results))
        a, b = results[("r1", "a")], results[("r1", "b")]
        self.assertEqual(("check_bug", False, True, "matches_requested"), (a["label"], a["retry_passed"], a["flagged"], a["cause"]))
        self.assertEqual(("unamended", True, True), (b["label"], b["retry_passed"], b["flagged"]))
        self.assertEqual(
            ringer.jev_amend_command("r1", "a", "matches_requested", 0.95, MINI_LOG.resolve()), a["amend_command"])
        self.assertFalse(results[("r3", "e")]["flagged"])
        self.assertFalse(results[("r3", "f")]["flagged"])
        firsts = first_fail_rows()
        with (self.out / "review.csv").open(newline="", encoding="utf-8") as fh:
            review = list(csv.DictReader(fh))
        c = firsts[("r2", "c")]
        self.assertEqual(
            [{"run_id": "r2", "task_key": "c", "cause": "syntax_or_transport", "confidence": "0.91",
              "spec": c["spec"], "check_output": ringer.jev_check_output_from_notes(c["notes"]), "verdict": ""}],
            review,
        )
        bodies = self.stub.bodies()
        self.assertEqual(5, len(bodies))  # one request per pair, both questions in it
        expected_states = sorted(
            json.dumps(ringer.jev_fail_state(row["spec"], ringer.jev_check_output_from_notes(row["notes"])), sort_keys=True)
            for row in firsts.values()
        )
        self.assertEqual(expected_states, sorted(json.dumps(body["state"], sort_keys=True) for body in bodies))
        for body in bodies:
            self.assertEqual(ringer.JEV_FAIL_QUESTIONS, body["questions"])
            self.assertEqual("jev-1.13.0", body["model"])
            self.assertEqual(set(ringer.JEV_DECLARED_FIELDS["fail_flag"]), set(body["state"]))

    def test_rerun_resumes_without_new_calls(self) -> None:
        first = self.replay()
        self.assertEqual(0, first.returncode, first.stderr)
        summary = self.summary()
        second = self.replay()
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertIn("called=0", second.stdout)
        self.assertEqual(5, self.stub.count)
        self.assertEqual(summary, self.summary())
        self.assertEqual(5, len(self.results()))

    def test_a_skip_stops_the_replay_and_a_rerun_resumes(self) -> None:
        self.stub.status = 429
        first = self.replay()
        self.assertEqual(1, first.returncode)
        self.assertEqual("jev: skipped (http-429); stopping replay; rerun to resume\n", first.stderr)
        self.assertEqual([], self.results())
        self.assertFalse((self.out / "summary.json").exists())
        self.stub.status = 200
        second = self.replay()
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(6, self.stub.count)
        self.assertEqual(3, self.summary()["flags_total"])

    def test_missing_key_stops_before_any_request(self) -> None:
        result = self.replay(key=None)
        self.assertEqual(1, result.returncode)
        self.assertEqual("jev: skipped (no-key); stopping replay; rerun to resume\n", result.stderr)
        self.assertEqual(0, self.stub.count)

    def test_a_redacted_row_is_skipped_like_the_live_flag(self) -> None:
        rows = [json.loads(line) for line in MINI_LOG.read_text(encoding="utf-8").splitlines()]
        rows.append({"run_id": "r5", "task_key": "h", "verdict": "FAIL", "retry": False,
                     "spec": "[redacted request packet]", "notes": "retry=false\nraw_check_output_first_2000_chars:\nFAIL: x",
                     "logged_at": "2026-09-06T10:00:00+00:00", "model": "m", "task_type": "docs", "worker_engine": "opencode"})
        log = self.root / "runs.jsonl"
        log.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        result = self.replay(log=log)
        self.assertEqual(0, result.returncode, result.stderr)
        results = {(row["run_id"], row["task_key"]): row for row in self.results()}
        self.assertEqual({"run_id": "r5", "task_key": "h", "label": "unamended", "retry_passed": False,
                          "skipped": "redact_spec"}, results[("r5", "h")])
        self.assertEqual(5, self.stub.count)  # the redacted pair never reached the API
        self.assertEqual(6, self.summary()["pairs"])

    def test_labels_must_match_the_log(self) -> None:
        labels = json.loads(MINI_LABELS.read_text(encoding="utf-8"))
        cases = [
            (labels + [{"run_id": "r9", "task_key": "zz", "label": "check_bug"}], "labels: r9 zz has no FAIL in the log\n"),
            (labels[:2], "labels: r3 f is amended but has no label\n"),
            ([dict(labels[0], label="maybe")] + labels[1:], "labels: r1 a has unknown label maybe\n"),
        ]
        for index, (content, message) in enumerate(cases):
            with self.subTest(message=message):
                path = self.root / f"labels-{index}.json"
                path.write_text(json.dumps(content), encoding="utf-8")
                result = self.replay("--dry-run", labels=path, key=None)
                self.assertEqual(2, result.returncode)
                self.assertEqual(message, result.stderr)


if __name__ == "__main__":
    unittest.main()
