# jev-pilot/tests/test_analyze.py
import json
from pathlib import Path
from jev_pilot import analyze as a

FIX = Path(__file__).parent / "fixtures"
ROWS = [json.loads(l) for l in (FIX / "mini_responses.jsonl").read_text().splitlines() if l.strip()]
REPEAT = [json.loads(l) for l in (FIX / "mini_repeat.jsonl").read_text().splitlines() if l.strip()]


def test_agreement_is_stratified_and_has_a_baseline():
    r = a.agreement(ROWS)
    assert r["n"] == len(ROWS)
    assert r["agree"] == sum(1 for x in ROWS if x["choice"] == x["hand_label"])
    assert set(r["by_source"]) <= {"manifest", "log"} and r["by_source"]
    assert all("n" in v and "rate" in v for v in r["by_label"].values())
    assert 0.0 <= r["majority_baseline_rate"] <= 1.0


def test_calibration_carries_n_and_parent_beats_fine_on_unconfident():
    c = a.calibration(ROWS, cutoff=0.9)
    assert c["confident_n"] + c["unconfident_n"] == len(ROWS)
    assert c["unconfident_parent_acc"] >= c["unconfident_fine_acc"]


def test_economics_uses_measured_tokens_and_both_prices():
    e = a.economics(ROWS, price_per_m_input=0.042, price_per_m_output=0.0)
    assert e["total_input_tokens"] == sum(x["input_tokens"] for x in ROWS)
    assert e["total_output_tokens"] == sum(x["output_tokens"] for x in ROWS)
    assert e["cost_per_decision"] > 0 and e["p95_latency_ms"] >= e["median_latency_ms"]


def test_stochasticity_reports_flip_rate():
    s = a.stochasticity(ROWS, REPEAT)
    assert s["repeat_n"] == 2 and 0.0 <= s["flip_rate"] <= 1.0 and s["flip_n"] == 1
