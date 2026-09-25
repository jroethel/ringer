#!/usr/bin/env python3
"""Offline replay of logged FAILs through the live FAIL-flag contract.

Sends each FAIL pair's logged spec and check output to TypeSafe unless
--dry-run is passed; the live replay is a human checkpoint (HC1), never CI.
Writes results.jsonl (resumable), summary.json, and review.csv under --out.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ringer  # noqa: E402

HAND_LABELS = ("check_bug", "spec_defect", "lane_outage")
LABEL_COUNT_KEYS = (*HAND_LABELS, "unamended")
REDACTED_SPEC = "[redacted request packet]"
BAR = 9


def collect_pairs(
    attempts: list[dict[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], set[tuple[str, str]]]:
    """First FAIL row per (run_id, task_key) in file order, plus retry-passed pairs."""
    firsts: dict[tuple[str, str], dict[str, Any]] = {}
    retry_passed: set[tuple[str, str]] = set()
    for row in attempts:
        key = (row.get("run_id"), row.get("task_key"))
        if row.get("verdict") == "FAIL":
            firsts.setdefault(key, row)
        elif key in firsts and row.get("verdict") == "PASS" and ringer.model_log_row_is_retry(row):
            retry_passed.add(key)
    return firsts, retry_passed


def load_labels(path: Path) -> list[dict[str, Any]] | None:
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        print(f"labels: could not read a JSON list from {path}", file=sys.stderr)
        return None
    if not isinstance(content, list) or not all(isinstance(item, dict) for item in content):
        print(f"labels: {path} is not a JSON list of objects", file=sys.stderr)
        return None
    return content


def validate_labels(
    content: list[dict[str, Any]],
    firsts: dict[tuple[str, str], dict[str, Any]],
    voided: set[tuple[str, str]],
) -> dict[tuple[str, str], str] | None:
    labels: dict[tuple[str, str], str] = {}
    for entry in content:
        key = (entry.get("run_id"), entry.get("task_key"))
        label = entry.get("label")
        if label not in HAND_LABELS:
            print(f"labels: {key[0]} {key[1]} has unknown label {label}", file=sys.stderr)
            return None
        if key not in firsts:
            print(f"labels: {key[0]} {key[1]} has no FAIL in the log", file=sys.stderr)
            return None
        labels[key] = str(label)
    for key in firsts:
        if key in voided and key not in labels:
            print(f"labels: {key[0]} {key[1]} is amended but has no label", file=sys.stderr)
            return None
    return labels


def load_finished_pairs(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    finished: dict[tuple[str, str], dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:  # a crash mid-append can leave one partial line; skipping it keeps the rerun resumable
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and "run_id" in row and "task_key" in row:
            finished[(row["run_id"], row["task_key"])] = row
    return finished


def append_result(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()


def build_summary(
    firsts: dict[tuple[str, str], dict[str, Any]],
    retry_passed: set[tuple[str, str]],
    labels: dict[tuple[str, str], str],
    results: dict[tuple[str, str], dict[str, Any]],
    config: ringer.JevConfig,
) -> dict[str, Any]:
    label_of = lambda key: labels.get(key, "unamended")
    flagged = lambda key: bool(results[key].get("flagged"))
    label_counts = {label: 0 for label in LABEL_COUNT_KEYS}
    for key in firsts:
        label_counts[label_of(key)] += 1
    check_bug_flagged = sum(1 for key in firsts if flagged(key) and label_of(key) == "check_bug")
    false_flags = sum(1 for key in firsts if flagged(key) and key in retry_passed)
    known_wrong_flags = sum(
        1 for key in firsts if flagged(key) and (key in retry_passed or label_of(key) == "lane_outage"))
    hand_review = [
        {"run_id": key[0], "task_key": key[1]}
        for key in firsts
        if flagged(key) and label_of(key) == "unamended" and key not in retry_passed
    ]
    return {
        "pairs": len(firsts),
        "label_counts": label_counts,
        "retry_passed": len(retry_passed),
        "flags_total": sum(1 for key in firsts if flagged(key)),
        "check_bug_flagged": check_bug_flagged,
        "false_flags": false_flags,
        "known_wrong_flags": known_wrong_flags,
        "spec_defect_flagged": sum(1 for key in firsts if flagged(key) and label_of(key) == "spec_defect"),
        "lane_outage_flagged": sum(1 for key in firsts if flagged(key) and label_of(key) == "lane_outage"),
        "hand_review": hand_review,
        "bar": BAR,
        "bar_met": check_bug_flagged >= BAR,
        "contract": ringer.JEV_CONTRACT_FAIL_FLAG,
        "model": config.model,
        "cutoff": config.fail_flag_cutoff,
        "input_tokens": sum(int((row.get("usage") or {}).get("input_tokens") or 0) for row in results.values()),
    }


def write_review_csv(
    path: Path,
    hand_review: list[dict[str, str]],
    firsts: dict[tuple[str, str], dict[str, Any]],
    results: dict[tuple[str, str], dict[str, Any]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["run_id", "task_key", "cause", "confidence", "spec", "check_output", "verdict"])
        for entry in hand_review:
            key = (entry["run_id"], entry["task_key"])
            first = firsts[key]
            state = ringer.jev_fail_state(
                str(first.get("spec") or ""), ringer.jev_check_output_from_notes(str(first.get("notes") or "")))
            row = results[key]
            writer.writerow([
                key[0], key[1], row.get("cause", "unspecified"), f"{float(row.get('confidence') or 0.0):.2f}",
                state["task_spec"], state["check_output"], "",
            ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replay each logged task's first FAIL through the live FAIL-flag contract."
    )
    parser.add_argument("--log", type=Path, required=True, help="eval log (runs.jsonl) to replay")
    parser.add_argument("--labels", type=Path, required=True, help="JSON list of hand labels")
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument("--config", type=Path, default=None, help="config file to read [jev] from")
    parser.add_argument("--dry-run", action="store_true", help="count pairs and labels without any call or file")
    args = parser.parse_args(argv)

    log_path = args.log.expanduser().resolve()
    rows, _ = ringer.read_model_log_rows(args.log.expanduser())
    attempts, voided, _ = ringer.partition_amendments(rows)
    firsts, retry_passed = collect_pairs(attempts)

    content = load_labels(args.labels.expanduser())
    labels = validate_labels(content, firsts, voided) if content is not None else None
    if labels is None:
        return 2

    if args.dry_run:
        label_counts = {label: 0 for label in LABEL_COUNT_KEYS}
        for key in firsts:
            label_counts[labels.get(key, "unamended")] += 1
        print(
            f"pairs={len(firsts)} check_bug={label_counts['check_bug']} "
            f"spec_defect={label_counts['spec_defect']} lane_outage={label_counts['lane_outage']} "
            f"unamended={label_counts['unamended']} retry_passed={len(retry_passed)}"
        )
        return 0

    config = ringer.load_jev_config_file(args.config.expanduser() if args.config else None)
    out = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    results_path = out / "results.jsonl"
    results = load_finished_pairs(results_path)
    called = 0
    for key, first in firsts.items():
        if key in results:
            continue
        base = {
            "run_id": key[0],
            "task_key": key[1],
            "label": labels.get(key, "unamended"),
            "retry_passed": key in retry_passed,
        }
        spec = str(first.get("spec") or "")
        if spec == REDACTED_SPEC:
            row: dict[str, Any] = {**base, "skipped": "redact_spec"}
        else:
            state = ringer.jev_fail_state(
                spec, ringer.jev_check_output_from_notes(str(first.get("notes") or "")))
            result = ringer.jev_call(config, state, ringer.JEV_FAIL_QUESTIONS)
            called += 1
            if result.skipped:
                print(f"jev: skipped ({result.skipped}); stopping replay; rerun to resume", file=sys.stderr)
                return 1
            row = {**base, **ringer.jev_fail_flag_record(result, config.fail_flag_cutoff, key[0], key[1], log_path)}
        append_result(results_path, row)
        results[key] = row

    summary = build_summary(firsts, retry_passed, labels, results, config)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_review_csv(out / "review.csv", summary["hand_review"], firsts, results)
    print(
        f"replay: pairs={summary['pairs']} called={called} flags={summary['flags_total']} "
        f"check_bug_flagged={summary['check_bug_flagged']} false_flags={summary['false_flags']} "
        f"hand_review={len(summary['hand_review'])} bar_met={str(summary['bar_met']).lower()}"
    )
    print(f"summary: {out / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
