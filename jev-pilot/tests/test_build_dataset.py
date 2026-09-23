# jev-pilot/tests/test_build_dataset.py
from pathlib import Path
import pytest
from jev_pilot import build_dataset as b

FIX = Path(__file__).parent / "fixtures"


def test_build_dedups_drops_untyped_and_joins_full_spec():
    rows = b.build(FIX / "mini_runs.jsonl", FIX)  # FIX is the dir holding mini_manifest.json
    keys = [r["task_key"] for r in rows]
    assert len(keys) == len(set(keys)), "task_key must be deduped"
    assert all(r["hand_label"] for r in rows), "untyped rows must be dropped"
    joined = [r for r in rows if r["spec_source"] == "manifest"]
    assert joined and all(len(r["spec"]) > 200 for r in joined), "matched key carries the full manifest spec"


def test_assert_closed_set_rejects_unknown_label():
    with pytest.raises(ValueError):
        b.assert_closed_set([{"task_key": "x", "hand_label": "not-a-real-type", "spec": "s", "spec_source": "log"}])


def test_assert_closed_set_passes_known_labels():
    b.assert_closed_set([{"task_key": "x", "hand_label": "docs", "spec": "s", "spec_source": "log"}])


def test_scan_secrets_flags_credential_bearing_spec():
    rows = b.build(FIX / "mini_runs.jsonl", FIX)
    flagged = b.scan_secrets(rows)
    assert any("AKIA" in r["spec"] for r in flagged), "a spec with an AWS-key-shaped token must be flagged"
