#!/usr/bin/env python3
"""Jev plumbing: config, stdlib client and fallback, breaker, FAIL-flag contract, declared fields."""
from __future__ import annotations

import asyncio
import contextlib
import io
import os
import re
import shlex
import sys
import tempfile
import time
import tomllib
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

import ringer  # noqa: E402
from jev_stub import DUMMY_KEY, JevStub, free_port_url  # noqa: E402

QUESTIONS = {"q": {"type": "choice", "instructions": "Pick one.", "criteria": {"a": "Option a.", "b": "Option b."}}}
OK_RESPONSE = {
    "model": "jev-1.13.0",
    "answers": {"q": {"type": "choice", "choice": "a", "probabilities": {"a": 0.93, "b": 0.07}, "confidence": 0.9}},
    "usage": {"input_tokens": 318, "output_tokens": 34},
}


def fail_answers(fault: str, confidence: float, cause: str | None = "matches_requested") -> dict:
    answers = {"fault": {"choice": fault, "confidence": confidence, "probabilities": {fault: confidence}}}
    if cause is not None:
        answers["check_cause"] = {"choice": cause, "confidence": 0.8, "probabilities": {cause: 0.8}}
    return answers


class JevConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, text: str, name: str = "config.toml") -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_defaults_are_all_off(self) -> None:
        config = ringer.JevConfig()
        self.assertEqual(
            (False, False, False, "jev-1.13.0", "https://api.typesafe.ai/v1/systemone", 5.0, 0.9, 0.9,
             ("research", "probe", "persona-review")),
            (config.enabled, config.task_type, config.fail_flag, config.model, config.endpoint,
             config.timeout_s, config.task_type_cutoff, config.fail_flag_cutoff, config.held_out),
        )
        self.assertFalse(config.task_type_active)
        self.assertFalse(config.fail_flag_active)

    def test_a_feature_needs_the_master_switch_and_its_own(self) -> None:
        self.assertFalse(ringer.JevConfig(task_type=True, fail_flag=True).task_type_active)
        self.assertFalse(ringer.JevConfig(task_type=True, fail_flag=True).fail_flag_active)
        self.assertFalse(ringer.JevConfig(enabled=True).task_type_active)
        self.assertFalse(ringer.JevConfig(enabled=True).fail_flag_active)
        self.assertTrue(ringer.JevConfig(enabled=True, task_type=True).task_type_active)
        self.assertTrue(ringer.JevConfig(enabled=True, fail_flag=True).fail_flag_active)

    def test_app_config_without_a_jev_table_is_all_off(self) -> None:
        config = ringer.AppConfig.load(self.write('[eval]\nbackend = "jsonl"\n'))
        self.assertEqual(ringer.JevConfig(), config.jev)

    def test_app_config_reads_the_jev_table(self) -> None:
        config = ringer.AppConfig.load(self.write(
            "[jev]\nenabled = true\ntask_type = true\ntimeout_s = 2\ntask_type_cutoff = 0.75\n"
            'fail_flag_cutoff = 0.8\nheld_out = ["probe"]\nmodel = "jev-1.14.0"\n'
        ))
        self.assertEqual(
            ringer.JevConfig(enabled=True, task_type=True, timeout_s=2.0, task_type_cutoff=0.75,
                             fail_flag_cutoff=0.8, held_out=("probe",), model="jev-1.14.0"),
            config.jev,
        )

    def test_malformed_values_raise_value_errors(self) -> None:
        cases = [
            ([1], "jev must be a TOML table"),
            ({"enabled": "yes"}, "jev.enabled must be true or false"),
            ({"task_type": 1}, "jev.task_type must be true or false"),
            ({"fail_flag": "no"}, "jev.fail_flag must be true or false"),
            ({"model": ""}, "jev.model must be a non-empty string"),
            ({"endpoint": "ftp://example.test"}, "jev.endpoint must be an http or https URL"),
            ({"timeout_s": True}, "jev.timeout_s must be a number"),
            ({"timeout_s": 0}, "jev.timeout_s must be positive"),
            ({"task_type_cutoff": 1.5}, "jev.task_type_cutoff must be a number between 0 and 1"),
            ({"fail_flag_cutoff": "high"}, "jev.fail_flag_cutoff must be a number between 0 and 1"),
            ({"held_out": "probe"}, "jev.held_out must be a list of strings"),
            ({"held_out": ["probe", 3]}, "jev.held_out must be a list of strings"),
        ]
        for raw, message in cases:
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(ValueError, re.escape(message)):
                    ringer.load_jev_config(raw)
        self.assertEqual(ringer.JevConfig(), ringer.load_jev_config(None))
        self.assertEqual(ringer.JevConfig(), ringer.load_jev_config({"unknown_key": 1}))

    def test_config_file_loader_is_tolerant_like_lint_today(self) -> None:
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.root / "xdg")}):
            os.environ.pop("RINGER_CONFIG", None)
            self.assertEqual(ringer.JevConfig(), ringer.load_jev_config_file(None))
            self.assertEqual(ringer.JevConfig(), ringer.load_jev_config_file(self.root / "missing.toml"))
            self.assertEqual(ringer.JevConfig(), ringer.load_jev_config_file(self.write("not = [valid toml", "broken.toml")))
            self.assertEqual(ringer.JevConfig(enabled=True),
                             ringer.load_jev_config_file(self.write("[jev]\nenabled = true\n", "good.toml")))
            with self.assertRaisesRegex(ValueError, re.escape("jev.timeout_s must be positive")):
                ringer.load_jev_config_file(self.write("[jev]\ntimeout_s = 0\n", "bad.toml"))

    def test_sample_config_block_documents_the_defaults(self) -> None:
        lines = (ROOT / "config.sample.toml").read_text(encoding="utf-8").splitlines()
        start = lines.index("# [jev]")
        block = []
        for line in lines[start:]:
            if not line.startswith("# "):
                break
            block.append(line[2:])
        self.assertEqual(ringer.JevConfig(), ringer.load_jev_config(tomllib.loads("\n".join(block))["jev"]))


class JevCallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stub = JevStub({"spec one": OK_RESPONSE})
        self.endpoint = self.stub.start()
        self.addCleanup(self.stub.stop)
        self.config = ringer.JevConfig(enabled=True, task_type=True, endpoint=self.endpoint, timeout_s=1.0)

    def call(self, spec: str = "spec one", config: ringer.JevConfig | None = None) -> ringer.JevResult:
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}):
            return ringer.jev_call(config or self.config, {"task_spec": spec}, QUESTIONS)

    def test_missing_key_skips_without_a_request(self) -> None:
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("TYPESAFE_API_KEY", None)
            result = ringer.jev_call(self.config, {"task_spec": "spec one"}, QUESTIONS)
        self.assertEqual("no-key", result.skipped)
        self.assertEqual(0, self.stub.count)

    def test_success_returns_answers_model_and_usage_from_one_request(self) -> None:
        result = self.call()
        self.assertEqual("", result.skipped)
        self.assertEqual({"q": {"choice": "a", "confidence": 0.9, "probabilities": {"a": 0.93, "b": 0.07}}}, result.answers)
        self.assertEqual("jev-1.13.0", result.model)
        self.assertEqual({"input_tokens": 318, "output_tokens": 34}, result.usage)
        self.assertEqual(1, self.stub.count)
        request = self.stub.requests[0]
        self.assertEqual("/v1/systemone", request["path"])
        self.assertEqual(f"Bearer {DUMMY_KEY}", request["authorization"])
        self.assertEqual("application/json", request["content_type"])
        self.assertEqual({"state": {"task_spec": "spec one"}, "model": "jev-1.13.0", "questions": QUESTIONS}, request["body"])
        self.assertNotIn(DUMMY_KEY, repr(result))

    def test_http_errors_map_to_their_status(self) -> None:
        for status in (401, 422, 429, 529, 500):
            with self.subTest(status=status):
                self.stub.status = status
                self.assertEqual(f"http-{status}", self.call().skipped)

    def test_unusable_bodies_are_bad_response(self) -> None:
        self.stub.responses["no answer"] = {"model": "jev-1.13.0", "answers": {}, "usage": {}}
        self.stub.responses["bad choice"] = {"model": "jev-1.13.0", "answers": {"q": {
            "type": "choice", "choice": "z", "probabilities": {"z": 1.0}, "confidence": 1.0}}, "usage": {}}
        self.stub.responses["bad confidence"] = {"model": "jev-1.13.0", "answers": {"q": {
            "type": "choice", "choice": "a", "probabilities": {"a": 1.0}, "confidence": "high"}}, "usage": {}}
        for spec in ("no answer", "bad choice", "bad confidence"):
            with self.subTest(spec=spec):
                self.assertEqual("bad-response", self.call(spec).skipped)
        self.stub.malformed = True
        self.assertEqual("bad-response", self.call().skipped)

    def test_hanging_endpoint_times_out(self) -> None:
        self.stub.hang_specs = {"spec one"}
        started = time.monotonic()
        result = self.call()
        self.assertEqual("timeout", result.skipped)
        self.assertLess(time.monotonic() - started, 2.5)

    def test_refused_connection_is_network(self) -> None:
        config = ringer.JevConfig(enabled=True, endpoint=free_port_url(), timeout_s=1.0)
        self.assertEqual("network", self.call(config=config).skipped)

    def test_an_unexpected_exception_is_reported_by_type_and_never_raised(self) -> None:
        with mock.patch.object(ringer.urllib.request, "urlopen", side_effect=RuntimeError("boom")):
            self.assertEqual("error-RuntimeError", self.call().skipped)

    def test_async_call_runs_off_the_event_loop(self) -> None:
        self.stub.hang_specs = {"spec one"}
        finished: dict[str, float] = {}

        async def scenario() -> ringer.JevResult:
            started = time.monotonic()

            async def ticker() -> None:
                await asyncio.sleep(0.3)
                finished["ticker"] = time.monotonic() - started

            async def call() -> ringer.JevResult:
                result = await ringer.jev_call_async(self.config, {"task_spec": "spec one"}, QUESTIONS)
                finished["call"] = time.monotonic() - started
                return result

            result, _ = await asyncio.gather(call(), ticker())
            return result

        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}):
            result = asyncio.run(scenario())
        self.assertEqual("timeout", result.skipped)
        self.assertLess(finished["ticker"], finished["call"])
        self.assertLess(finished["ticker"], 0.8)

    def test_async_wrapper_bounds_a_stuck_thread(self) -> None:
        def stuck(*_args: object) -> ringer.JevResult:
            time.sleep(1.5)
            return ringer.JevResult(model="late")

        config = ringer.JevConfig(enabled=True, endpoint=self.endpoint, timeout_s=0.2)
        with mock.patch.object(ringer, "jev_call", stuck):
            result = asyncio.run(ringer.jev_call_async(config, {"task_spec": "spec one"}, QUESTIONS))
        self.assertEqual("timeout", result.skipped)


class JevSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.stub = JevStub({"spec one": OK_RESPONSE})
        endpoint = self.stub.start()
        self.addCleanup(self.stub.stop)
        self.config = ringer.JevConfig(enabled=True, task_type=True, endpoint=endpoint, timeout_s=1.0)

    def test_first_skip_prints_one_line_and_turns_jev_off_for_the_invocation(self) -> None:
        self.stub.status = 429
        session = ringer.JevSession(self.config, "task_type")
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}), contextlib.redirect_stderr(err):
            first = session.call({"task_spec": "spec one"}, QUESTIONS)
            second = session.call({"task_spec": "spec one"}, QUESTIONS)
            third = asyncio.run(session.call_async({"task_spec": "spec one"}, QUESTIONS))
        self.assertEqual(["http-429"] * 3, [first.skipped, second.skipped, third.skipped])
        self.assertEqual(1, self.stub.count)
        self.assertEqual("http-429", session.skip_reason)
        self.assertEqual("jev: skipped task_type (http-429); continuing without Jev\n", err.getvalue())

    def test_successful_calls_leave_the_session_on(self) -> None:
        session = ringer.JevSession(self.config, "task_type")
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}), contextlib.redirect_stderr(err):
            results = [session.call({"task_spec": "spec one"}, QUESTIONS) for _ in range(2)]
        self.assertEqual(["", ""], [result.skipped for result in results])
        self.assertEqual(2, self.stub.count)
        self.assertEqual("", err.getvalue())

    def test_only_service_level_reasons_trip_the_breaker(self) -> None:
        trips = ringer.jev_reason_trips_breaker
        for reason in ("no-key", "network", "timeout", "http-401", "http-429", "http-500", "http-529", "http-503"):
            self.assertTrue(trips(reason), reason)
        for reason in ("http-422", "http-400", "http-404", "bad-response", "error-RuntimeError", "redact_spec"):
            self.assertFalse(trips(reason), reason)

    def test_request_specific_failures_skip_one_decision_and_keep_the_session_on(self) -> None:
        self.stub.status = 422
        session = ringer.JevSession(self.config, "task_type")
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}), contextlib.redirect_stderr(err):
            results = [session.call({"task_spec": "spec one"}, QUESTIONS) for _ in range(2)]
            self.stub.status = 200
            self.stub.malformed = True
            results.append(session.call({"task_spec": "spec one"}, QUESTIONS))
        self.assertEqual(["http-422", "http-422", "bad-response"], [result.skipped for result in results])
        self.assertEqual(3, self.stub.count)
        self.assertEqual("", session.skip_reason)
        self.assertEqual("", err.getvalue())

    def test_concurrent_failures_print_one_line(self) -> None:
        self.stub.status = 429
        session = ringer.JevSession(self.config, "fail_flag")
        err = io.StringIO()

        async def scenario() -> list[ringer.JevResult]:
            return list(await asyncio.gather(*(session.call_async({"task_spec": "spec one"}, QUESTIONS) for _ in range(3))))

        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}), contextlib.redirect_stderr(err):
            results = asyncio.run(scenario())
        self.assertEqual(["http-429"] * 3, [result.skipped for result in results])
        self.assertLessEqual(self.stub.count, 3)
        self.assertEqual("jev: skipped fail_flag (http-429); continuing without Jev\n", err.getvalue())

    def test_the_limiter_caps_calls_in_flight_and_queued_calls_see_the_breaker(self) -> None:
        self.stub.hang_specs = {"spec one"}
        err = io.StringIO()

        async def scenario() -> list[ringer.JevResult]:
            session = ringer.JevSession(self.config, "task_type", asyncio.Semaphore(ringer.JEV_MAX_CONCURRENT_CALLS))
            calls = (session.call_async({"task_spec": "spec one"}, QUESTIONS) for _ in range(6))
            return list(await asyncio.gather(*calls))

        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": DUMMY_KEY}), contextlib.redirect_stderr(err):
            results = asyncio.run(scenario())
        self.assertEqual(4, ringer.JEV_MAX_CONCURRENT_CALLS)
        self.assertEqual(["timeout"] * 6, [result.skipped for result in results])
        self.assertEqual(4, self.stub.count)  # the two queued calls never reach the API once the breaker trips
        self.assertEqual("jev: skipped task_type (timeout); continuing without Jev\n", err.getvalue())


class FailFlagContractTests(unittest.TestCase):
    def test_declared_fields_constant(self) -> None:
        self.assertEqual(
            {"task_type": {"task_spec": 12000}, "fail_flag": {"task_spec": 500, "check_output": 2000}},
            ringer.JEV_DECLARED_FIELDS,
        )

    def test_fail_state_uses_declared_fields_and_caps(self) -> None:
        state = ringer.jev_fail_state("s" * 900, "c" * 3000)
        self.assertEqual(set(ringer.JEV_DECLARED_FIELDS["fail_flag"]), set(state))
        self.assertEqual(500, len(state["task_spec"]))
        self.assertEqual(2000, len(state["check_output"]))
        self.assertEqual({"task_spec": "short", "check_output": "out"}, ringer.jev_fail_state("short", "out"))

    def test_fail_questions_are_one_batch_of_two_choices(self) -> None:
        questions = ringer.JEV_FAIL_QUESTIONS
        self.assertEqual("fail_flag-v1", ringer.JEV_CONTRACT_FAIL_FLAG)
        self.assertEqual(["fault", "check_cause"], list(questions))
        self.assertEqual(["worker", "check", "spec", "infra", "unclear"], list(questions["fault"]["criteria"]))
        self.assertEqual(
            ["matches_requested", "syntax_or_transport", "out_of_scope", "contradicts_spec", "stale_premise", "not_a_check_bug"],
            list(questions["check_cause"]["criteria"]),
        )
        for question in questions.values():
            self.assertEqual("choice", question["type"])
            self.assertTrue(question["instructions"])

    def test_decide_fail_flag(self) -> None:
        self.assertEqual(
            {"flagged": True, "fault": "check", "confidence": 0.9, "probabilities": {"check": 0.9}, "cause": "matches_requested"},
            ringer.decide_fail_flag(fail_answers("check", 0.9), 0.9),
        )
        self.assertFalse(ringer.decide_fail_flag(fail_answers("check", 0.89), 0.9)["flagged"])
        self.assertTrue(ringer.decide_fail_flag(fail_answers("check", 0.89), 0.85)["flagged"])
        self.assertFalse(ringer.decide_fail_flag(fail_answers("worker", 0.99), 0.9)["flagged"])
        self.assertEqual("unspecified", ringer.decide_fail_flag(fail_answers("check", 0.95, cause=None), 0.9)["cause"])

    def test_amend_command_is_exact_shell_safe_and_names_the_log(self) -> None:
        log = Path("/tmp/my logs/runs.jsonl")
        command = ringer.jev_amend_command("run-1", "task a", "matches_requested", 0.953, log)
        self.assertEqual(
            "./ringer.py amend run-1 'task a' --reclassify check_bug "
            "--note 'jev: suspected check fault (matches_requested, confidence 0.95)' "
            "--log '/tmp/my logs/runs.jsonl'",
            command,
        )
        self.assertEqual(
            ["./ringer.py", "amend", "run-1", "task a", "--reclassify", "check_bug", "--note",
             "jev: suspected check fault (matches_requested, confidence 0.95)", "--log", "/tmp/my logs/runs.jsonl"],
            shlex.split(command),
        )

    def test_fail_flag_record(self) -> None:
        usage = {"input_tokens": 900, "output_tokens": 60}
        log = Path("/tmp/runs.jsonl")
        flagged = ringer.jev_fail_flag_record(
            ringer.JevResult(answers=fail_answers("check", 0.95), model="jev-1.13.0", usage=usage), 0.9, "run-1", "t1", log)
        self.assertEqual(
            {"flagged": True, "fault": "check", "confidence": 0.95, "probabilities": {"check": 0.95},
             "cause": "matches_requested",
             "amend_command": ringer.jev_amend_command("run-1", "t1", "matches_requested", 0.95, log),
             "model": "jev-1.13.0", "usage": usage, "cutoff": 0.9},
            flagged,
        )
        unflagged = ringer.jev_fail_flag_record(
            ringer.JevResult(answers=fail_answers("worker", 0.97), model="jev-1.13.0", usage=usage), 0.9, "run-1", "t1", log)
        self.assertFalse(unflagged["flagged"])
        self.assertEqual("", unflagged["amend_command"])
        self.assertEqual({"skipped": "timeout"},
                         ringer.jev_fail_flag_record(ringer.JevResult(skipped="timeout"), 0.9, "run-1", "t1", log))

    def test_check_output_from_notes(self) -> None:
        notes = "retry=false\nworker_returncode=0\nraw_check_output_first_2000_chars:\nFAIL: x\nline2"
        self.assertEqual("FAIL: x\nline2", ringer.jev_check_output_from_notes(notes))
        self.assertEqual("", ringer.jev_check_output_from_notes("retry=false\nraw_check_output_first_2000_chars:\n"))
        self.assertEqual("", ringer.jev_check_output_from_notes("retry=false"))


class JevDocsTests(unittest.TestCase):
    def test_declared_field_table_matches_constant(self) -> None:
        text = (ROOT / "docs" / "JEV.md").read_text(encoding="utf-8")
        section = text.split("## Declared fields", 1)[1].split("\n## ", 1)[0]
        table: dict[str, dict[str, int]] = {}
        for line in section.splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            table.setdefault(cells[0].strip("`"), {})[cells[1].strip("`")] = int(cells[3])
        self.assertEqual(ringer.JEV_DECLARED_FIELDS, table)


if __name__ == "__main__":
    unittest.main()
