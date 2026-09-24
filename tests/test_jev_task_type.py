#!/usr/bin/env python3
"""Jev task_type recording: decision rule, cache, lint lines, run rows, fallback, concurrency."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

import ringer  # noqa: E402
from jev_stub import DUMMY_KEY, TODAY_ROW_KEYS, JevCliTestCase, free_port_url, logged_at_epoch  # noqa: E402

FIXTURE = TESTS / "fixtures" / "jev_task_type_responses.jsonl"
FIXTURE_ROWS = {
    row["task_key"]: row
    for row in (json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip())
}
HELD = ("research", "probe", "persona-review")
REDACTED_SPEC = "fixture spec redacted-docs: synthetic private text that must never leave the host, long enough for lint."
SLOW_SPEC = "fixture spec slow-a: synthetic stand-in text whose Jev call hangs past the timeout, long enough for lint."


def task_type_response(row: dict) -> dict:
    return {
        "model": "jev-1.13.0",
        "answers": {"task_type": {"type": "choice", "choice": row["choice"],
                                  "probabilities": row["probabilities"], "confidence": row["confidence"]}},
        "usage": {"input_tokens": row["input_tokens"], "output_tokens": row["output_tokens"]},
    }


def answer(choice: str, confidence: float) -> dict:
    return {"choice": choice, "confidence": confidence, "probabilities": {choice: confidence}}


class DecideTaskTypeTests(unittest.TestCase):
    def test_decision_matrix(self) -> None:
        decide = ringer.decide_task_type
        self.assertEqual(("site-build", "jev", ""), decide("docs", answer("site-build", 0.97), 0.9, HELD))
        self.assertEqual(("code-review", "jev", ""), decide("code-review", answer("code-review", 0.9), 0.9, HELD))
        self.assertEqual(("docs", "hand", "below-cutoff"), decide("docs", answer("site-build", 0.78), 0.9, HELD))
        self.assertEqual(("site-build", "jev", ""), decide("docs", answer("site-build", 0.78), 0.75, HELD))
        self.assertEqual(("probe", "hand", "held-out"), decide("probe", answer("probe", 1.0), 0.9, HELD))
        self.assertEqual(("docs", "hand", "held-out"), decide("docs", answer("research", 0.99), 0.9, HELD))
        self.assertEqual(("research", "hand", "held-out"), decide("research", answer("docs", 0.99), 0.9, HELD))
        self.assertEqual(("image-gen", "hand", "hand-outside-vocabulary"),
                         decide("image-gen", answer("site-build", 0.99), 0.9, HELD))
        self.assertEqual(("docs", "jev", ""), decide("", answer("docs", 0.95), 0.9, HELD))
        self.assertEqual(("", "hand", "no-answer"), decide("", None, 0.9, HELD))
        # Releasing a held-out class is a config edit: an empty list lets Jev assign it.
        self.assertEqual(("research", "jev", ""), decide("", answer("research", 0.99), 0.9, ()))


class TaskTypeRequestTests(unittest.TestCase):
    def test_questions_are_the_pilot_contract(self) -> None:
        questions = ringer.JEV_TASK_TYPE_QUESTIONS
        self.assertEqual(["task_type"], list(questions))
        question = questions["task_type"]
        self.assertEqual("choice", question["type"])
        self.assertEqual("Classify the software task described in `task_spec` into exactly one task type.",
                         question["instructions"])
        self.assertEqual(list(ringer.JEV_TASK_TYPE_VOCAB), list(question["criteria"]))
        self.assertEqual(8, len(ringer.JEV_TASK_TYPE_VOCAB))
        self.assertEqual("Repairing a bug, regression, or defect in existing code.", question["criteria"]["code-fix"])
        self.assertEqual("task_type-v1", ringer.JEV_CONTRACT_TASK_TYPE)

    def test_request_caps_the_spec_and_keys_the_cache_by_contract_model_and_spec(self) -> None:
        config = ringer.JevConfig(enabled=True, task_type=True)
        task = ringer.TaskSpec(key="big", spec="x" * 13000, check="true")
        key, state = ringer.jev_task_type_request(task, config)
        self.assertEqual({"task_spec": "x" * 12000}, state)
        self.assertEqual(set(ringer.JEV_DECLARED_FIELDS["task_type"]), set(state))
        expected = hashlib.sha256(json.dumps(["task_type-v1", "jev-1.13.0", "x" * 12000]).encode("utf-8")).hexdigest()
        self.assertEqual(expected, key)
        self.assertEqual(expected, ringer.jev_cache_key("task_type-v1", "jev-1.13.0", "x" * 12000))
        other_key, _ = ringer.jev_task_type_request(task, dataclasses.replace(config, model="jev-1.14.0"))
        self.assertNotEqual(key, other_key)

    def test_cache_loader_skips_malformed_lines_and_the_last_entry_wins(self) -> None:
        def entry(choice: str) -> dict:
            return {"key": "k1", "contract": "task_type-v1", "requested_model": "jev-1.13.0", "model": "jev-1.13.0",
                    "answer": answer(choice, 0.95), "usage": {"input_tokens": 1, "output_tokens": 1},
                    "cached_at": "2026-09-23T00:00:00+00:00"}

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "jev-cache.jsonl"
            path.write_text(json.dumps(entry("docs")) + "\n{broken\n" + json.dumps(entry("site-build")) + "\n",
                            encoding="utf-8")
            cache = ringer.load_jev_cache(path)
            self.assertEqual({"k1"}, set(cache))
            self.assertEqual("site-build", cache["k1"]["answer"]["choice"])
            self.assertEqual({}, ringer.load_jev_cache(Path(temp) / "missing.jsonl"))

    def test_cache_loader_skips_wellformed_json_that_would_crash_the_consumers(self) -> None:
        def entry(key: str, **overrides: object) -> dict:
            base = {"key": key, "contract": "task_type-v1", "requested_model": "jev-1.13.0", "model": "jev-1.13.0",
                    "answer": answer("docs", 0.95), "usage": {"input_tokens": 1, "output_tokens": 1},
                    "cached_at": "2026-09-23T00:00:00+00:00"}
            base.update(overrides)
            return base

        good_answer = answer("docs", 0.95)
        bad = [
            entry("bad-model", model=1),
            entry("bad-usage", usage=[]),
            entry("bad-choice", answer=good_answer | {"choice": 1}),
            entry("bad-confidence", answer=good_answer | {"confidence": "high"}),
            entry("bad-probabilities", answer=good_answer | {"probabilities": "high"}),
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "jev-cache.jsonl"
            lines = [json.dumps(entry("good-key"))] + [json.dumps(item) for item in bad]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual({"good-key"}, set(ringer.load_jev_cache(path)))


class PostgresRowTests(unittest.TestCase):
    def test_jev_task_type_keys_are_dropped_like_task_type(self) -> None:
        class FakeConn:
            params: dict | None = None

            def execute(self, _sql: str, params: dict) -> None:
                self.params = params

            def close(self) -> None:
                pass

        with tempfile.TemporaryDirectory() as temp:
            logger = ringer.EvalLogger(ringer.EvalConfig(backend="jsonl", jsonl_path=Path(temp) / "eval.jsonl"))
            fake = FakeConn()
            logger._conn = fake
            logger.log_attempt({
                "run_id": "run", "pattern": "ringer-py", "task_key": "a", "spec": "spec", "worker_engine": "opencode",
                "shepherd_model": "gpt", "verify_method": "executed-check", "verdict": "PASS", "duration_ms": 1,
                "worker_tokens": 2, "notes": "retry=false", "orchestrator": "tester", "model": "m",
                "task_type": "docs", "retry": False, "task_type_source": "jev", "task_type_hand": "docs",
                "jev_task_type": {"choice": "docs"},
            })
            assert fake.params is not None
            for key in ("task_type_source", "task_type_hand", "jev_task_type"):
                self.assertNotIn(key, fake.params)


class TaskTypeCliTests(JevCliTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.stub.responses.update({row["spec"]: task_type_response(row) for row in FIXTURE_ROWS.values()})

    def fixture_task(self, key: str, **extra: object) -> dict:
        row = FIXTURE_ROWS[key]
        extra.setdefault("task_type", row["hand_label"])
        return self.task(key, row["spec"], **extra)

    def lint(self, manifest: Path, config: Path | None, key: str | None = DUMMY_KEY):
        return self.cli("lint", str(manifest), config=config, key=key)

    def assert_task_type_requests(self, bodies: list[dict]) -> None:
        for body in bodies:
            self.assertEqual(ringer.JEV_TASK_TYPE_QUESTIONS, body["questions"])
            self.assertEqual("jev-1.13.0", body["model"])
            self.assertEqual(set(ringer.JEV_DECLARED_FIELDS["task_type"]), set(body["state"]))
            self.assertLessEqual(len(body["state"]["task_spec"]), ringer.JEV_DECLARED_FIELDS["task_type"]["task_spec"])

    def test_switches_off_lint_output_is_todays(self) -> None:
        manifest = self.write_manifest([self.fixture_task(k) for k in ("task-02-nav-infra", "task-03-stm-guide", "task-06-schema-refresh")])
        configs = [
            None,
            self.write_config(None, name="plain.toml"),
            self.write_config(self.jev_on(enabled=False, task_type=True), name="master-off.toml"),
            self.write_config(self.jev_on(task_type=False), name="switch-off.toml"),
        ]
        for config in configs:
            with self.subTest(config=str(config)):
                result = self.lint(manifest, config)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("lint: clean (3 tasks)\n", result.stdout)
                self.assertEqual("", result.stderr)
        self.assertEqual(0, self.stub.count)

    def test_lint_prints_one_decision_line_per_task_and_keeps_the_exit_code(self) -> None:
        tasks = [
            self.fixture_task("task-02-nav-infra"),
            self.fixture_task("task-03-stm-guide"),
            self.fixture_task("task-06-schema-refresh"),
            self.fixture_task("task-03-stm-guide-validate", task_type=""),
            self.fixture_task("zai-smoke"),
            self.task("redacted-docs", REDACTED_SPEC, redact_spec=True),
        ]
        result = self.lint(self.write_manifest(tasks), self.write_config(self.jev_on(task_type=True)))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertEqual(
            "jev: task-02-nav-infra: task_type=code-feature confidence=0.97 hand=code-feature -> agrees\n"
            "jev: task-03-stm-guide: task_type=site-build confidence=0.97 hand=docs -> overrides hand\n"
            "jev: task-06-schema-refresh: task_type=site-build confidence=0.78 hand=docs -> keeps hand (below-cutoff)\n"
            "jev: task-03-stm-guide-validate: task_type=code-review confidence=0.89 hand=(none) -> keeps hand (below-cutoff)\n"
            "jev: zai-smoke: task_type=probe confidence=1.00 hand=probe -> keeps hand (held-out)\n"
            "jev: redacted-docs: task_type not sent (redact_spec) hand=docs -> keeps hand\n"
            "lint: clean (6 tasks)\n",
            result.stdout,
        )
        bodies = self.stub.bodies()
        self.assertEqual(5, len(bodies))  # one request per sent task; none for the redacted task
        self.assert_task_type_requests(bodies)
        self.assertNotIn(REDACTED_SPEC, json.dumps(bodies))

    def test_cache_hit_needs_no_call_and_cutoff_change_redecides(self) -> None:
        manifest = self.write_manifest([self.fixture_task("task-06-schema-refresh")])
        strict = self.write_config(self.jev_on(task_type=True), name="strict.toml")
        first = self.lint(manifest, strict)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(1, self.stub.count)
        again = self.lint(manifest, strict, key=None)  # no key: only the cache can answer
        self.assertEqual(first.stdout, again.stdout)
        self.assertEqual("", again.stderr)
        loose = self.lint(manifest, self.write_config(self.jev_on(task_type=True, task_type_cutoff=0.75), name="loose.toml"), key=None)
        self.assertEqual(
            "jev: task-06-schema-refresh: task_type=site-build confidence=0.78 hand=docs -> overrides hand\n"
            "lint: clean (1 tasks)\n",
            loose.stdout,
        )
        self.assertEqual(1, self.stub.count)
        self.assertEqual(1, len((self.ringer_home / "jev-cache.jsonl").read_text(encoding="utf-8").splitlines()))

    def test_unavailable_jev_leaves_lint_output_unchanged_with_one_reason_line(self) -> None:
        manifest = self.write_manifest([self.fixture_task(k) for k in ("task-02-nav-infra", "task-03-stm-guide", "task-06-schema-refresh")])
        cases = [
            ("no-key", {}, None),
            ("http-401", {"status": 401}, DUMMY_KEY),
            ("http-429", {"status": 429}, DUMMY_KEY),
            ("http-529", {"status": 529}, DUMMY_KEY),
            ("timeout", {"hang": True}, DUMMY_KEY),
            ("network", {"endpoint": free_port_url()}, DUMMY_KEY),
        ]
        for reason, setup, key in cases:
            with self.subTest(reason=reason):
                self.stub.status = setup.get("status", 200)
                self.stub.hang_specs = {FIXTURE_ROWS["task-02-nav-infra"]["spec"]} if setup.get("hang") else set()
                overrides = {"task_type": True, "timeout_s": 1.0}
                if "endpoint" in setup:
                    overrides["endpoint"] = setup["endpoint"]
                before = self.stub.count
                started = time.monotonic()
                result = self.lint(manifest, self.write_config(self.jev_on(**overrides)), key=key)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("lint: clean (3 tasks)\n", result.stdout)
                self.assertEqual(f"jev: skipped task_type ({reason}); continuing without Jev\n", result.stderr)
                self.assertLessEqual(self.stub.count - before, 1)  # the breaker stops after the first failure
                self.assertLess(time.monotonic() - started, 15)

    def test_a_rejected_request_skips_that_task_only(self) -> None:
        keys = ("task-02-nav-infra", "task-03-stm-guide", "task-06-schema-refresh")
        manifest = self.write_manifest([self.fixture_task(k) for k in keys])
        self.stub.status = 422
        result = self.lint(manifest, self.write_config(self.jev_on(task_type=True)))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)  # a request-specific failure never trips the breaker
        self.assertEqual(
            "".join(f"jev: {k}: task_type skipped (http-422) hand={FIXTURE_ROWS[k]['hand_label']} -> keeps hand\n" for k in keys)
            + "lint: clean (3 tasks)\n",
            result.stdout,
        )
        self.assertEqual(3, self.stub.count)

    def test_malformed_jev_table_is_a_config_error(self) -> None:
        manifest = self.write_manifest([self.fixture_task("task-02-nav-infra")])
        result = self.lint(manifest, self.write_config(self.jev_on(task_type=True, timeout_s=0)))
        self.assertEqual(2, result.returncode)
        self.assertIn("jev.timeout_s must be positive", result.stderr)

    def test_run_rows_record_hand_jev_confidence_source_model_usage(self) -> None:
        keys = list(FIXTURE_ROWS)
        tasks = [self.fixture_task(k) for k in keys] + [self.task("redacted-docs", REDACTED_SPEC, redact_spec=True)]
        result = self.run_manifest(self.write_manifest(tasks, max_parallel=3), self.write_config(self.jev_on(task_type=True)))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)
        rows = {row["task_key"]: row for row in self.rows()}
        expected = {
            "task-02-nav-infra": ("code-feature", "jev"),
            "task-03-stm-guide": ("site-build", "jev"),
            "task-06-schema-refresh": ("docs", "hand"),
            "task-06-schema-refresh-validate": ("code-review", "jev"),
            "task-03-stm-guide-validate": ("code-review", "hand"),
            "zai-smoke": ("probe", "hand"),
        }
        for key, (recorded, source) in expected.items():
            with self.subTest(task=key):
                row, fixture = rows[key], FIXTURE_ROWS[key]
                self.assertEqual(recorded, row["task_type"])
                self.assertEqual(source, row["task_type_source"])
                self.assertEqual(fixture["hand_label"], row["task_type_hand"])
                self.assertEqual(
                    {"choice": fixture["choice"], "confidence": fixture["confidence"],
                     "probabilities": fixture["probabilities"], "model": "jev-1.13.0",
                     "usage": {"input_tokens": fixture["input_tokens"], "output_tokens": fixture["output_tokens"]},
                     "cutoff": 0.9, "cached": False},
                    row["jev_task_type"],
                )
                self.assertIn(f"task_type={recorded}", row["notes"])
        redacted = rows["redacted-docs"]
        self.assertEqual(("docs", "hand", "docs"),
                         (redacted["task_type"], redacted["task_type_source"], redacted["task_type_hand"]))
        self.assertEqual({"skipped": "redact_spec"}, redacted["jev_task_type"])
        bodies = self.stub.bodies()
        self.assertEqual(sorted(FIXTURE_ROWS[k]["spec"] for k in keys), sorted(b["state"]["task_spec"] for b in bodies))
        self.assert_task_type_requests(bodies)

    def test_cutoff_is_a_config_value_at_run_time(self) -> None:
        manifest = self.write_manifest([self.fixture_task("task-06-schema-refresh")])
        strict = self.run_manifest(manifest, self.write_config(self.jev_on(task_type=True), name="strict.toml"))
        loose = self.run_manifest(manifest, self.write_config(self.jev_on(task_type=True, task_type_cutoff=0.75), name="loose.toml"))
        self.assertEqual(0, strict.returncode, strict.stdout + strict.stderr)
        self.assertEqual(0, loose.returncode, loose.stdout + loose.stderr)
        first, second = self.rows()
        self.assertEqual(("docs", "hand"), (first["task_type"], first["task_type_source"]))
        self.assertEqual(("site-build", "jev"), (second["task_type"], second["task_type_source"]))
        self.assertFalse(first["jev_task_type"]["cached"])
        self.assertTrue(second["jev_task_type"]["cached"])
        self.assertEqual(0.75, second["jev_task_type"]["cutoff"])
        self.assertEqual(1, self.stub.count)

    def test_switches_off_rows_have_todays_shape(self) -> None:
        manifest = self.write_manifest([self.fixture_task("task-03-stm-guide")])
        for name, jev in (("plain.toml", None),
                          ("master-off.toml", self.jev_on(enabled=False, task_type=True, fail_flag=True))):
            result = self.run_manifest(manifest, self.write_config(jev, name=name))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stderr)
        rows = self.rows()
        self.assertEqual(2, len(rows))
        for row in rows:
            self.assertEqual(TODAY_ROW_KEYS, set(row))
            self.assertEqual("docs", row["task_type"])
        self.assertEqual(0, self.stub.count)

    def test_missing_key_or_rate_limit_run_keeps_hand_labels(self) -> None:
        manifest = self.write_manifest([self.fixture_task("task-02-nav-infra"), self.fixture_task("task-03-stm-guide")])
        config = self.write_config(self.jev_on(task_type=True))
        for reason, key, status in (("no-key", None, 200), ("http-429", DUMMY_KEY, 429)):
            with self.subTest(reason=reason):
                self.stub.status = status
                self.jsonl_path.unlink(missing_ok=True)
                result = self.run_manifest(manifest, config, key=key)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual(f"jev: skipped task_type ({reason}); continuing without Jev\n", result.stderr)
                rows = self.rows()
                self.assertEqual(2, len(rows))
                for row in rows:
                    self.assertEqual(FIXTURE_ROWS[row["task_key"]]["hand_label"], row["task_type"])
                    self.assertEqual("hand", row["task_type_source"])
                    self.assertEqual({"skipped": reason}, row["jev_task_type"])

    def test_hanging_call_does_not_stall_other_tasks(self) -> None:
        self.stub.hang_specs = {SLOW_SPEC}  # the stub holds this request for 8 s
        timeout_s = 4.0
        manifest = self.write_manifest([self.task("slow-a", SLOW_SPEC), self.fixture_task("task-02-nav-infra")], max_parallel=2)
        result = self.run_manifest(manifest, self.write_config(self.jev_on(task_type=True, timeout_s=timeout_s)))
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("jev: skipped task_type (timeout); continuing without Jev\n", result.stderr)
        rows = {row["task_key"]: row for row in self.rows()}
        slow_request = next(item for item in self.stub.requests if item["body"]["state"]["task_spec"] == SLOW_SPEC)
        arrived = slow_request["arrived"]
        # Ordering only: B's row lands before A's Jev call times out, and A's row lands after it.
        self.assertLess(logged_at_epoch(rows["task-02-nav-infra"]), arrived + timeout_s)
        self.assertGreaterEqual(logged_at_epoch(rows["slow-a"]), arrived + timeout_s - 0.1)
        self.assertEqual(("docs", "hand"), (rows["slow-a"]["task_type"], rows["slow-a"]["task_type_source"]))
        self.assertEqual({"skipped": "timeout"}, rows["slow-a"]["jev_task_type"])
        self.assertEqual(("code-feature", "jev"),
                         (rows["task-02-nav-infra"]["task_type"], rows["task-02-nav-infra"]["task_type_source"]))


if __name__ == "__main__":
    unittest.main()
