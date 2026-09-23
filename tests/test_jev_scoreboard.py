#!/usr/bin/env python3
"""Scoreboard counts of hand-labeled and Jev-labeled tasks per task_type bucket."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

import ringer  # noqa: E402
from jev_stub import JevCliTestCase  # noqa: E402


def attempt(run_id: str, task_key: str, task_type: str, *, source: str | None = None, verdict: str = "PASS",
            retry: bool = False, logged_at: str = "2026-09-20T10:00:00+00:00") -> dict:
    row = {
        "run_id": run_id, "task_key": task_key, "worker_engine": "opencode",
        "model": "openrouter/z-ai/glm-5.2", "task_type": task_type, "verdict": verdict, "retry": retry,
        "duration_ms": 100, "worker_tokens": None, "logged_at": logged_at, "orchestrator": "tester",
        "notes": "retry=true" if retry else "retry=false",
    }
    if source is not None:
        row["task_type_source"] = source
    return row


SAMPLE = [
    attempt("r1", "t1", "docs"),                      # historical row: no source recorded, so hand
    attempt("r1", "t2", "docs", source="jev"),
    attempt("r1", "t3", "site-build", source="jev", verdict="FAIL"),
    attempt("r1", "t3", "site-build", source="jev", retry=True, logged_at="2026-09-20T10:05:00+00:00"),
    attempt("r2", "t4", "site-build", source="hand"),
    attempt("r2", "t5", ""),                           # untyped: counted in neither
]
EXPECTED = {
    "docs": {"hand": 1, "jev": 1},
    "site-build": {"hand": 1, "jev": 1},
    "(untyped)": {"hand": 0, "jev": 0},
}


class TaskTypeSourceTests(unittest.TestCase):
    def test_row_source_rule(self) -> None:
        source = ringer.model_log_row_task_type_source
        self.assertEqual("hand", source({"task_type": "docs"}))
        self.assertEqual("jev", source({"task_type": "docs", "task_type_source": "jev"}))
        self.assertEqual("hand", source({"task_type": "docs", "task_type_source": "hand"}))
        self.assertEqual("hand", source({"task_type": "docs", "task_type_source": "other"}))
        self.assertEqual("hand", source({"task_type": "docs", "task_type_source": None}))
        self.assertEqual("", source({"task_type": ""}))
        self.assertEqual("", source({}))

    def test_aggregate_counts_tasks_by_source(self) -> None:
        groups = {group["task_type"]: group for group in ringer.aggregate_model_log_rows(SAMPLE)}
        self.assertEqual(EXPECTED, {key: group["task_type_sources"] for key, group in groups.items()})
        self.assertEqual(2, groups["site-build"]["tasks"])

    def test_final_attempt_row_decides_the_source(self) -> None:
        rows = [
            attempt("r3", "t6", "docs", source="hand", verdict="FAIL"),
            attempt("r3", "t6", "docs", source="jev", retry=True, logged_at="2026-09-20T10:05:00+00:00"),
        ]
        (group,) = ringer.aggregate_model_log_rows(rows)
        self.assertEqual({"hand": 0, "jev": 1}, group["task_type_sources"])

    def test_voided_tasks_are_not_counted(self) -> None:
        amendment = {"type": "amendment", "run_id": "r2", "task_key": "t4", "reclassify": "check_bug",
                     "note": "check was wrong", "amended_at": "2026-09-21T00:00:00+00:00",
                     "logged_at": "2026-09-21T00:00:00+00:00", "identity": "tester"}
        groups = {group["task_type"]: group for group in ringer.aggregate_model_log_rows(SAMPLE + [amendment])}
        self.assertEqual({"hand": 0, "jev": 1}, groups["site-build"]["task_type_sources"])


class ReadModelMigrationTests(unittest.TestCase):
    def test_v3_database_gains_task_type_source_without_data_loss(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "ringer.db"
            with sqlite3.connect(db) as conn:
                conn.executescript(
                    """
                    PRAGMA user_version = 3;
                    CREATE TABLE schema_version(version INTEGER NOT NULL);
                    INSERT INTO schema_version VALUES (3);
                    CREATE TABLE attempts (
                        id INTEGER PRIMARY KEY, run_id TEXT, task_key TEXT, logged_at TEXT,
                        engine TEXT, model TEXT, reported_model TEXT, expected_model TEXT,
                        reasoning_effort TEXT, task_type TEXT, retry INTEGER, verdict TEXT,
                        duration_ms INTEGER, worker_tokens INTEGER, orchestrator TEXT
                    );
                    INSERT INTO attempts(model, task_type, verdict) VALUES ('gpt-5.5', 'docs', 'PASS');
                    """
                )
                ringer.create_read_model_schema(conn)
                columns = {row[1] for row in conn.execute("PRAGMA table_info(attempts)")}
                self.assertIn("task_type_source", columns)
                self.assertEqual(("gpt-5.5", "docs", "PASS", None), conn.execute(
                    "SELECT model, task_type, verdict, task_type_source FROM attempts").fetchone())
                self.assertEqual(4, conn.execute("PRAGMA user_version").fetchone()[0])
                self.assertEqual(4, conn.execute("SELECT version FROM schema_version").fetchone()[0])

    def test_ingest_stores_and_reads_back_the_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "runs.jsonl"
            log.write_text("".join(json.dumps(row) + "\n" for row in SAMPLE), encoding="utf-8")
            ringer.rebuild_read_model_db(root / "ringer.db", log, catalog_path=root / "missing-catalog.json",
                                         registry_path=root / "missing-registry.toml")
            rows, _registry = ringer.db_attempt_rows(root / "ringer.db")
            self.assertEqual([None, "jev", "jev", "jev", "hand", None], [row["task_type_source"] for row in rows])
            groups = {group["task_type"]: group for group in ringer.aggregate_model_log_rows(rows)}
            self.assertEqual(EXPECTED, {key: group["task_type_sources"] for key, group in groups.items()})


class ScoreboardCliTests(JevCliTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.log = self.root / "sample-runs.jsonl"
        self.log.write_text("".join(json.dumps(row) + "\n" for row in SAMPLE), encoding="utf-8")
        self.config = self.write_config(None)

    def sources(self, stdout: str) -> dict:
        return {group["task_type"]: group["task_type_sources"] for group in json.loads(stdout)}

    def test_models_json_and_text_show_hand_and_jev_counts(self) -> None:
        result = self.cli("models", "--log", str(self.log), "--json", config=self.config)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(EXPECTED, self.sources(result.stdout))
        text = self.cli("models", "--log", str(self.log), config=self.config)
        self.assertEqual(0, text.returncode, text.stderr)
        self.assertIn("Task type: docs (hand 1, jev 1)\n", text.stdout)
        self.assertIn("Task type: site-build (hand 1, jev 1)\n", text.stdout)
        self.assertIn("Task type: (untyped) (hand 0, jev 0)\n", text.stdout)

    def test_log_without_jev_rows_prints_todays_models_output(self) -> None:
        hand_only = [row for row in SAMPLE if row.get("task_type_source") != "jev"]
        self.log.write_text("".join(json.dumps(row) + "\n" for row in hand_only), encoding="utf-8")
        text = self.cli("models", "--log", str(self.log), config=self.config)
        self.assertEqual(0, text.returncode, text.stderr)
        self.assertIn("Task type: docs\n", text.stdout)
        self.assertNotIn("(hand ", text.stdout)
        result = self.cli("models", "--log", str(self.log), "--json", config=self.config)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(all("task_type_sources" not in group for group in json.loads(result.stdout)))

    def test_read_model_db_path_carries_the_source(self) -> None:
        db = self.root / "ringer.db"
        result = self.cli("models", "--log", str(self.log), "--db", str(db), "--json", config=self.config)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)  # no fallback: the SQLite read model served this
        self.assertEqual(EXPECTED, self.sources(result.stdout))
        with sqlite3.connect(db) as conn:
            self.assertEqual(4, conn.execute("PRAGMA user_version").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
