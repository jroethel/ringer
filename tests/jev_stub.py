"""Loopback stand-in for the TypeSafe /v1/systemone endpoint, plus a CLI test base for Jev tests.

Nothing here touches the network: the stub binds 127.0.0.1 on a free port, and
ringer is pointed at it through `[jev] endpoint` in a per-test config.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RINGER_PATH = ROOT / "ringer.py"
DUMMY_KEY = "test-dummy-key"
PASS_CHECK = "test -s out.txt || { echo 'FAIL: out.txt missing'; exit 1; }"
FAIL_CHECK = "echo 'FAIL: grep matched the stub the spec asked for'; exit 1"
# Every key an attempt row carries today when the Jev switches are off.
TODAY_ROW_KEYS = {
    "run_id", "pattern", "task_key", "spec", "worker_engine", "shepherd_model",
    "verify_method", "verdict", "duration_ms", "worker_tokens", "notes", "orchestrator",
    "model", "reported_model", "expected_model", "reasoning_effort", "task_type", "retry",
    "logged_at", "log_sink", "fallback_reason",
}
FAULT_OPTIONS = ("worker", "check", "spec", "infra", "unclear")
CAUSE_OPTIONS = (
    "matches_requested", "syntax_or_transport", "out_of_scope",
    "contradicts_spec", "stale_premise", "not_a_check_bug",
)
PROXY_VARS = ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY")


def fail_flag_response(fault: str, confidence: float, cause: str, cause_confidence: float = 0.9) -> dict[str, Any]:
    """A /v1/systemone response body answering the fail_flag-v1 questions."""

    def spread(options: tuple[str, ...], chosen: str, top: float) -> dict[str, float]:
        rest = round((1 - top) / (len(options) - 1), 4)
        return {option: (top if option == chosen else rest) for option in options}

    return {
        "model": "jev-1.13.0",
        "answers": {
            "fault": {"type": "choice", "choice": fault, "confidence": confidence,
                      "probabilities": spread(FAULT_OPTIONS, fault, confidence)},
            "check_cause": {"type": "choice", "choice": cause, "confidence": cause_confidence,
                            "probabilities": spread(CAUSE_OPTIONS, cause, cause_confidence)},
        },
        "usage": {"input_tokens": 900, "output_tokens": 60},
    }


def logged_at_epoch(row: dict[str, Any]) -> float:
    return datetime.fromisoformat(str(row["logged_at"])).timestamp()


def free_port_url() -> str:
    """A loopback URL on a port nothing listens on (the network-error path)."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return f"http://127.0.0.1:{port}/v1/systemone"


class JevStub:
    """Serves canned responses keyed by the request's state.task_spec and records every request."""

    def __init__(self, responses: dict[str, dict[str, Any]] | None = None) -> None:
        self.responses: dict[str, dict[str, Any]] = dict(responses or {})
        self.status = 200          # any other value answers every request with that status
        self.malformed = False     # True answers 200 with a body that is not JSON
        self.hang_specs: set[str] = set()      # hang requests whose state.task_spec is listed
        self.hang_questions: set[str] = set()  # hang requests that ask any of these question ids
        self.hang_s = 8.0
        self.requests: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._server: ThreadingHTTPServer | None = None

    @property
    def count(self) -> int:
        with self._lock:
            return len(self.requests)

    def bodies(self) -> list[dict[str, Any]]:
        with self._lock:
            return [item["body"] for item in self.requests]

    def start(self) -> str:
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length)
                try:
                    body = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    body = {"unparseable": raw.decode("utf-8", errors="replace")}
                record = {
                    "body": body,
                    "path": self.path,
                    "authorization": self.headers.get("Authorization"),
                    "content_type": self.headers.get("Content-Type"),
                    "arrived": time.time(),
                    "released": None,
                }
                with stub._lock:
                    stub.requests.append(record)
                state = body.get("state") if isinstance(body, dict) else None
                task_spec = state.get("task_spec") if isinstance(state, dict) else None
                questions = body.get("questions") if isinstance(body, dict) else None
                asked = set(questions) if isinstance(questions, dict) else set()
                if task_spec in stub.hang_specs or stub.hang_questions & asked:
                    time.sleep(stub.hang_s)
                record["released"] = time.time()
                if stub.status != 200:
                    self._send(stub.status, json.dumps({"error": f"stub status {stub.status}"}).encode("utf-8"))
                    return
                if stub.malformed:
                    self._send(200, b"{not json")
                    return
                response = stub.responses.get(task_spec) if isinstance(task_spec, str) else None
                if response is None:
                    self._send(422, json.dumps({"error": "stub has no response for this task_spec"}).encode("utf-8"))
                    return
                self._send(200, json.dumps(response).encode("utf-8"))

            def _send(self, status: int, payload: bytes) -> None:
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        server.block_on_close = False
        self._server = server
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{server.server_address[1]}/v1/systemone"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None


def jev_cli_env(root: Path, ringer_home: Path, key: str | None) -> dict[str, str]:
    env = os.environ.copy()
    for name in ("TYPESAFE_API_KEY", "RINGER_CONFIG", *PROXY_VARS):
        env.pop(name, None)
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "RINGER_NO_SELF_UPDATE": "1",
        "RINGER_NO_CATALOG_REFRESH": "1",
        "RINGER_HOME": str(ringer_home),
        "XDG_CONFIG_HOME": str(root / "xdg"),
        "HOME": str(root / "home"),
        "no_proxy": "127.0.0.1,localhost",
        "NO_PROXY": "127.0.0.1,localhost",
    })
    if key is not None:
        env["TYPESAFE_API_KEY"] = key
    return env


class JevCliTestCase(unittest.TestCase):
    """Runs the real ringer CLI in a subprocess against the loopback stub."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="ringer-jev-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.jsonl_path = self.root / "runs.jsonl"
        self.ringer_home = self.root / "ringer-home"
        self.count_path = self.root / "worker-count.txt"
        self.stub = JevStub()
        self.endpoint = self.stub.start()
        self.addCleanup(self.stub.stop)

    def jev_on(self, **overrides: Any) -> dict[str, Any]:
        values: dict[str, Any] = {"enabled": True, "endpoint": self.endpoint, "timeout_s": 2.0}
        values.update(overrides)
        return values

    def write_config(self, jev: dict[str, Any] | None, *, name: str = "config.toml") -> Path:
        count = str(self.count_path)
        lines = [
            f'state_dir = "{self.root / "state"}"',
            "dashboard_port_base = 18787",
            "allow_full_access = false",
            "",
            "[eval]",
            'backend = "jsonl"',
            f'jsonl_path = "{self.jsonl_path}"',
            "",
            "[artifact]",
            "enabled = false",
            "",
        ]
        engines = {
            "write_done": f"echo run >> {count}; printf done > out.txt",
        }
        for engine, script in engines.items():
            lines += [
                f"[engines.{engine}]",
                'bin = "/bin/sh"',
                f"args_template = {json.dumps(['-c', script])}",
                "sandbox_args = []",
                "full_access_args = []",
                "",
            ]
        if jev is not None:
            lines.append("[jev]")
            lines += [f"{key} = {json.dumps(value)}" for key, value in jev.items()]
        path = self.root / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def task(self, key: str, spec: str, *, task_type: str = "docs", check: str = PASS_CHECK,
             engine: str = "write_done", **extra: Any) -> dict[str, Any]:
        task: dict[str, Any] = {
            "key": key,
            "spec": spec,
            "check": check,
            "engine": engine,
            "expect_files": ["out.txt"],
            "verified": "out.txt exists and is not empty",
            "task_type": task_type,
        }
        task.update(extra)
        return task

    def write_manifest(self, tasks: list[dict[str, Any]], *, name: str = "jev", max_parallel: int = 2) -> Path:
        path = self.root / f"{name}.json"
        manifest = {
            "run_name": name,
            "workdir": str(self.root / f"work-{name}"),
            "max_parallel": max_parallel,
            "tasks": tasks,
        }
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path

    def cli(self, *args: str, config: Path | None, key: str | None = DUMMY_KEY,
            timeout: int = 90) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-B", str(RINGER_PATH)]
        if config is not None:
            cmd += ["--config", str(config)]
        cmd += list(args)
        env = jev_cli_env(self.root, self.ringer_home, key)
        return subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True,
                              timeout=timeout, check=False)

    def run_manifest(self, manifest: Path, config: Path, *, key: str | None = DUMMY_KEY) -> subprocess.CompletedProcess[str]:
        return self.cli("run", str(manifest), "--identity", "jev-test", "--no-dashboard", config=config, key=key)

    def rows(self) -> list[dict[str, Any]]:
        if not self.jsonl_path.exists():
            return []
        return [json.loads(line) for line in self.jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def worker_runs(self) -> int:
        if not self.count_path.exists():
            return 0
        return len(self.count_path.read_text(encoding="utf-8").splitlines())
