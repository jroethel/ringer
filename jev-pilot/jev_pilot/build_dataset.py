"""Build the shadow-mode dataset: one row per distinct historical task_key,
gated by a closed-set check on the hand label and a secret scan on the spec
before anything is written for a live call.
"""

import argparse
import json
import re
from pathlib import Path

from jev_pilot.tasktype_question import VOCAB

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-"),
    re.compile(r"(?i)\b(token|secret|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9+/_\-]{16,}"),
]


def _manifest_spec_map(manifests_dir: Path) -> dict:
    specs = {}
    for path in sorted(manifests_dir.glob("**/*.json")):
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for task in data.get("tasks", []):
            key = task.get("key")
            spec = task.get("spec")
            if key and spec:
                specs[key] = spec
    return specs


def build(log_path: Path, manifests_dir: Path) -> list[dict]:
    manifest_specs = _manifest_spec_map(Path(manifests_dir))

    rows = []
    seen = set()
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            task_key = entry.get("task_key")
            hand_label = entry.get("task_type")
            if not task_key or not hand_label or task_key in seen:
                continue
            seen.add(task_key)
            if task_key in manifest_specs:
                spec = manifest_specs[task_key]
                spec_source = "manifest"
            else:
                spec = entry.get("spec", "")
                spec_source = "log"
            rows.append({
                "task_key": task_key,
                "hand_label": hand_label,
                "spec": spec,
                "spec_source": spec_source,
            })
    return rows


def assert_closed_set(rows: list[dict]) -> None:
    vocab = set(VOCAB)
    for row in rows:
        if row["hand_label"] not in vocab:
            raise ValueError(
                f"unknown task_type {row['hand_label']!r} for task_key {row['task_key']!r}"
            )


def scan_secrets(rows: list[dict]) -> list[dict]:
    return [row for row in rows if any(p.search(row["spec"]) for p in SECRET_PATTERNS)]


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--manifests", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    log_path = Path(args.log).expanduser()
    manifests_dir = Path(args.manifests).expanduser()
    out_path = Path(args.out)

    rows = build(log_path, manifests_dir)
    assert_closed_set(rows)
    flagged = scan_secrets(rows)
    flagged_keys = {r["task_key"] for r in flagged}
    clean_rows = [r for r in rows if r["task_key"] not in flagged_keys]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for row in clean_rows:
            f.write(json.dumps(row) + "\n")

    scan_path = out_path.parent / "secret-scan.txt"
    with open(scan_path, "w") as f:
        if flagged:
            for row in flagged:
                f.write(f"{row['task_key']}\t{row['spec_source']}\n")
        else:
            f.write("no flagged rows\n")

    full_spec = sum(1 for r in clean_rows if r["spec_source"] == "manifest")
    truncated = sum(1 for r in clean_rows if r["spec_source"] == "log")
    label_counts: dict = {}
    for r in clean_rows:
        label_counts[r["hand_label"]] = label_counts.get(r["hand_label"], 0) + 1

    print(f"rows={len(clean_rows)} full_spec={full_spec} truncated={truncated} flagged={len(flagged)}")
    for label in sorted(label_counts):
        print(f"{label}={label_counts[label]}")


if __name__ == "__main__":
    _main()
