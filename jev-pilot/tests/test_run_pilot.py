# jev-pilot/tests/test_run_pilot.py
import json, os, subprocess, sys
from pathlib import Path
import pytest
from jev_pilot import run_pilot

VOCAB = {"code-feature", "code-fix", "code-review", "docs",
         "site-build", "persona-review", "probe", "research"}


def test_run_is_idempotent_and_skips_existing(tmp_path, monkeypatch):
    ds = tmp_path / "ds.jsonl"
    ds.write_text("\n".join(json.dumps({"task_key": f"t{i}", "hand_label": "docs",
                  "spec": "write the readme", "spec_source": "log"}) for i in range(3)))
    out = tmp_path / "resp.jsonl"
    calls = {"n": 0}

    def fake_classify(client, spec, model="jev-latest"):
        calls["n"] += 1
        return {"choice": "docs", "probabilities": {"docs": 1.0}, "confidence": 0.99,
                "input_tokens": 10, "output_tokens": 1}

    monkeypatch.setattr(run_pilot, "classify", fake_classify)
    monkeypatch.setattr(run_pilot, "make_client", lambda: object())
    run_pilot.run(ds, out, retries=1)
    run_pilot.run(ds, out, retries=1)  # second pass must add nothing
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    keys = [r["task_key"] for r in rows]
    assert calls["n"] == 3, "second run must skip all existing keys"
    assert keys == sorted(set(keys)) and len(keys) == 3, "exactly one row per task_key"


@pytest.mark.skipif(not os.environ.get("TYPESAFE_API_KEY"), reason="live API key required")
def test_smoke_three_real_calls(tmp_path):
    out = tmp_path / "smoke.jsonl"
    subprocess.run(
        [sys.executable, "-m", "jev_pilot.run_pilot",
         "--dataset", "jev-pilot/out/dataset.jsonl", "--out", str(out), "--limit", "3"],
        check=True, env={**os.environ, "PYTHONPATH": "jev-pilot"},
    )
    rows = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert len(rows) == 3
    for r in rows:
        assert r["choice"] in VOCAB
        assert 0.0 <= r["confidence"] <= 1.0
        assert abs(sum(r["probabilities"].values()) - 1.0) <= 0.02
        assert r["input_tokens"] is not None and r["latency_ms"] >= 0
