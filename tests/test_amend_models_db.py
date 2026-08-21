import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ringer import build_models_api_payload, log_has_amendments  # noqa: E402


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


def _write_log(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _write_registry(path):
    path.write_text(
        """
[engines.opencode]
harness = "OpenCode"
access = "OpenRouter API"

[engines.opencode.models."glm-5.2"]
display = "GLM 5.2"
confidence = "verified"
source = "fixture"
""",
        encoding="utf-8",
    )


def _write_catalog(path):
    path.write_text(json.dumps({"models": []}), encoding="utf-8")


class TestAmendModelsDbPath(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old_env = os.environ.copy()
        self.addCleanup(self.restore_env)
        os.environ["HOME"] = str(self.root / "home")
        os.environ["RINGER_HOME"] = str(self.root / "ringer-home")
        self.catalog_path = self.root / "catalog.json"
        self.registry_path = self.root / "model-identity.toml"
        self.notes_path = self.root / "missing-notes.md"
        _write_catalog(self.catalog_path)
        _write_registry(self.registry_path)

    def restore_env(self) -> None:
        os.environ.clear()
        os.environ.update(self.old_env)

    def _payload(self, log_path):
        return build_models_api_payload(
            log_path=log_path,
            default_log_path=log_path,
            db_path=None,
            catalog_path=self.catalog_path,
            registry_path=self.registry_path,
            notes_path=self.notes_path,
        )

    def test_default_path_applies_the_void(self):
        clean_log_path = self.root / "clean.jsonl"
        amended_log_path = self.root / "amended.jsonl"
        _write_log(clean_log_path, _base())
        _write_log(amended_log_path, _base() + [_amendment()])

        payload_groups = self._payload(amended_log_path)["groups"]

        # control: no amendments -> DB fast-path stays available
        self.assertFalse(log_has_amendments(clean_log_path))
        # with amendments -> forced JSONL, void applied on the default path
        self.assertTrue(log_has_amendments(amended_log_path))
        g = {(x["model"], x["task_type"]): x for x in payload_groups}[("glm-5.2", "code-fix")]
        self.assertEqual(1, g["amended"])
        self.assertEqual(1.0, g["first_try_pass_rate"])


if __name__ == "__main__":
    unittest.main()
