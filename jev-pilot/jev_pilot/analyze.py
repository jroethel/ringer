"""Offline analysis of the shadow run: stratified agreement, calibration, economics,
stochasticity, and the blind-review kit for HC2.

Reads only the persisted responses, so a re-diff never costs another call.
"""

import argparse
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from jev_pilot.tasktype_question import parent_label

DIFF_FIELDS = ["task_key", "hand_label", "choice", "confidence", "agree", "spec_source"]


def _read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _rate(agree, n):
    return agree / n if n else 0.0


def _tally(rows):
    n = len(rows)
    agree = sum(1 for r in rows if r["choice"] == r["hand_label"])
    return {"n": n, "agree": agree, "rate": _rate(agree, n)}


def agreement(rows, outdir=None, specs=None) -> dict:
    """Pooled agreement plus the spec_source and hand_label strata and the majority baseline.

    With `outdir` set, also writes diff.csv, disagreements.csv and the blind-review kit.
    """
    by_source = defaultdict(list)
    by_label = defaultdict(list)
    for r in rows:
        by_source[r["spec_source"]].append(r)
        by_label[r["hand_label"]].append(r)

    label_counts = Counter(r["hand_label"] for r in rows)
    result = dict(
        _tally(rows),
        by_source={k: _tally(v) for k, v in by_source.items()},
        by_label={k: _tally(v) for k, v in by_label.items()},
        majority_baseline_rate=_rate(max(label_counts.values(), default=0), len(rows)),
    )
    if outdir is not None:
        _write_csvs(rows, Path(outdir), specs or {})
    return result


def _write_csvs(rows, outdir, specs):
    outdir.mkdir(parents=True, exist_ok=True)
    diffs = [
        {
            "task_key": r["task_key"],
            "hand_label": r["hand_label"],
            "choice": r["choice"],
            "confidence": r["confidence"],
            "agree": r["choice"] == r["hand_label"],
            "spec_source": r["spec_source"],
        }
        for r in rows
    ]
    _write_csv(outdir / "diff.csv", DIFF_FIELDS, diffs)
    _write_csv(outdir / "disagreements.csv", DIFF_FIELDS, [d for d in diffs if not d["agree"]])
    _write_blind_kit(outdir, [r for r in rows if r["choice"] != r["hand_label"]], specs)


def _write_csv(path, fields, records):
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def _write_blind_kit(outdir, disagreements, specs):
    """Shuffle the hand label and Jev's choice per row; the mapping lives only in blind_key.csv."""
    review, key = [], []
    for r in disagreements:
        jev_is_a = random.random() < 0.5
        option_a, option_b = (
            (r["choice"], r["hand_label"]) if jev_is_a else (r["hand_label"], r["choice"])
        )
        review.append({
            "task_key": r["task_key"],
            "spec": specs.get(r["task_key"], ""),
            "option_a": option_a,
            "option_b": option_b,
            "pick": "",
        })
        key.append({"task_key": r["task_key"], "jev_option": "option_a" if jev_is_a else "option_b"})
    _write_csv(outdir / "blind_review.csv", ["task_key", "spec", "option_a", "option_b", "pick"], review)
    _write_csv(outdir / "blind_key.csv", ["task_key", "jev_option"], key)


def calibration(rows, cutoff=0.9) -> dict:
    """Accuracy above and below the confidence cutoff, with the free parent fallback below it."""
    confident = [r for r in rows if r["confidence"] >= cutoff]
    unconfident = [r for r in rows if r["confidence"] < cutoff]
    parent_hits = sum(
        1 for r in unconfident if parent_label(r["choice"]) == parent_label(r["hand_label"])
    )
    return {
        "cutoff": cutoff,
        "confident_n": len(confident),
        "confident_acc": _tally(confident)["rate"],
        "unconfident_n": len(unconfident),
        "unconfident_fine_acc": _tally(unconfident)["rate"],
        "unconfident_parent_acc": _rate(parent_hits, len(unconfident)),
    }


def confidence_histogram(rows, bins=10) -> list:
    """Equal-width buckets over [0,1] so the cutoff can be checked against the real spread."""
    counts = [0] * bins
    for r in rows:
        idx = min(int(r["confidence"] * bins), bins - 1)
        counts[idx] += 1
    return [
        {"lo": round(i / bins, 4), "hi": round((i + 1) / bins, 4), "n": counts[i]}
        for i in range(bins)
    ]


def _p95(values):
    """Nearest-rank 95th percentile, which is never below the median."""
    ordered = sorted(values)
    idx = max(0, -(-95 * len(ordered) // 100) - 1)
    return ordered[idx]


def economics(rows, price_per_m_input, price_per_m_output) -> dict:
    """Cost and latency from the measured usage fields, never from an estimate."""
    n = len(rows)
    total_in = sum(r["input_tokens"] for r in rows)
    total_out = sum(r["output_tokens"] for r in rows)
    latencies = [r["latency_ms"] for r in rows]
    total_cost = total_in / 1_000_000 * price_per_m_input + total_out / 1_000_000 * price_per_m_output
    return {
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "input_tokens_per_decision": total_in / n if n else 0.0,
        "cost_per_decision": total_cost / n if n else 0.0,
        "median_latency_ms": statistics.median(latencies) if latencies else 0.0,
        "p95_latency_ms": _p95(latencies) if latencies else 0.0,
    }


def stochasticity(rows, repeat_rows) -> dict:
    """Noise floor: how often the same task_key drew a different choice on a second call."""
    first = {r["task_key"]: r["choice"] for r in rows}
    paired = [r for r in repeat_rows if r["task_key"] in first]
    flips = sum(1 for r in paired if r["choice"] != first[r["task_key"]])
    return {"repeat_n": len(paired), "flip_n": flips, "flip_rate": _rate(flips, len(paired))}


def main(argv=None):
    p = argparse.ArgumentParser(description="Analyze the Jev task_type shadow run.")
    p.add_argument("--responses", required=True)
    p.add_argument("--repeat")
    p.add_argument("--outdir", required=True)
    p.add_argument("--price-per-m-input", type=float, default=0.0)
    p.add_argument("--price-per-m-output", type=float, default=0.0)
    p.add_argument("--cutoff", type=float, default=0.9)
    args = p.parse_args(argv)

    rows = _read_jsonl(args.responses)
    repeat_rows = _read_jsonl(args.repeat) if args.repeat else []
    # blind_review.csv needs the spec text, which lives in the dataset beside the responses.
    specs = {r["task_key"]: r["spec"] for r in _read_jsonl(Path(args.responses).parent / "dataset.jsonl")}

    report = {
        "agreement": agreement(rows, outdir=args.outdir, specs=specs),
        "calibration": calibration(rows, cutoff=args.cutoff),
        "confidence_histogram": confidence_histogram(rows),
        "economics": economics(rows, args.price_per_m_input, args.price_per_m_output),
        "stochasticity": stochasticity(rows, repeat_rows),
    }
    Path(args.outdir, "analysis.json").write_text(json.dumps(report, indent=2) + "\n")

    ag, cal, eco, sto = report["agreement"], report["calibration"], report["economics"], report["stochasticity"]
    print(f"agreement n={ag['n']} agree={ag['agree']} rate={ag['rate']:.3f} "
          f"majority_baseline={ag['majority_baseline_rate']:.3f}")
    for src, v in sorted(ag["by_source"].items()):
        print(f"  spec_source={src} n={v['n']} rate={v['rate']:.3f}")
    print(f"calibration cutoff={cal['cutoff']} confident n={cal['confident_n']} acc={cal['confident_acc']:.3f} "
          f"| unconfident n={cal['unconfident_n']} fine={cal['unconfident_fine_acc']:.3f} "
          f"parent={cal['unconfident_parent_acc']:.3f}")
    print(f"economics input_tokens/decision={eco['input_tokens_per_decision']:.1f} "
          f"cost/decision=${eco['cost_per_decision']:.8f} "
          f"median_latency_ms={eco['median_latency_ms']:.1f} p95_latency_ms={eco['p95_latency_ms']:.1f}")
    print(f"stochasticity repeat_n={sto['repeat_n']} flip_n={sto['flip_n']} flip_rate={sto['flip_rate']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
