"""Idempotent shadow run harness: replay dataset tasks through Jev, append one row each.

Re-invoking with the same `--out` resumes a partial run: task keys already present
are skipped, so no call is re-spent. Accessors are pinned in jev-pilot/SDK-CONTRACT.md.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from typesafe_sdk import TypeSafeClient

from jev_pilot.tasktype_question import classify

BACKOFF_BASE_S = 0.5
BACKOFF_CAP_S = 8.0


def make_client():
    """Build the one client for a run; the key comes from the environment only."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        raise RuntimeError(
            "TYPESAFE_API_KEY is not set. Export it before running the pilot; "
            "it is read from the environment only and never stored in a file."
        )
    return TypeSafeClient()


def _read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def estimate_cost(dataset_path, price_per_m_input, chars_per_token=4.0) -> dict:
    """Pre-run estimate from summed spec lengths, for HC1 to read before any call."""
    rows = _read_jsonl(dataset_path)
    est_input_tokens = int(sum(len(r["spec"]) for r in rows) / chars_per_token)
    return {
        "est_input_tokens": est_input_tokens,
        "est_cost": est_input_tokens / 1_000_000 * price_per_m_input,
    }


def run(dataset_path, out_path, limit=None, retries=3) -> dict:
    """Classify each not-yet-answered dataset task and append its row to out_path."""
    rows = _read_jsonl(dataset_path)
    if limit is not None:
        rows = rows[:limit]
    done = {r["task_key"] for r in _read_jsonl(out_path)}
    client = make_client()
    written = skipped = failed = 0

    with Path(out_path).open("a") as fh:
        for row in rows:
            if row["task_key"] in done:
                skipped += 1
                continue
            result = _classify_with_backoff(client, row["spec"], retries)
            if result is None:
                failed += 1
                continue
            answer, latency_ms = result
            fh.write(json.dumps({
                "task_key": row["task_key"],
                "hand_label": row["hand_label"],
                "spec_source": row["spec_source"],
                "choice": answer["choice"],
                "probabilities": answer["probabilities"],
                "confidence": answer["confidence"],
                "input_tokens": answer["input_tokens"],
                "output_tokens": answer["output_tokens"],
                "latency_ms": latency_ms,
            }) + "\n")
            fh.flush()
            done.add(row["task_key"])
            written += 1

    return {"written": written, "skipped": skipped, "failed": failed}


def _classify_with_backoff(client, spec, retries):
    """Up to `retries` attempts with bounded exponential backoff; None if all fail."""
    for attempt in range(retries):
        started = time.perf_counter()
        try:
            answer = classify(client, spec)
        except Exception as exc:  # a failed task must not abort a resumable run
            print(f"attempt {attempt + 1}/{retries} failed: {type(exc).__name__}", file=sys.stderr)
            if attempt + 1 < retries:
                time.sleep(min(BACKOFF_BASE_S * 2 ** attempt, BACKOFF_CAP_S))
            continue
        return answer, (time.perf_counter() - started) * 1000.0
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description="Run the Jev task_type shadow pilot.")
    p.add_argument("--dataset", required=True)
    p.add_argument("--out")
    p.add_argument("--limit", type=int)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--estimate-only", action="store_true")
    p.add_argument("--price-per-m-input", type=float, default=0.0)
    args = p.parse_args(argv)

    if args.estimate_only:
        est = estimate_cost(args.dataset, args.price_per_m_input)
        print(f"est_input_tokens={est['est_input_tokens']} est_cost=${est['est_cost']:.6f} "
              f"(estimate from summed spec lengths at ${args.price_per_m_input}/M input tokens)")
        return 0

    if not args.out:
        p.error("--out is required unless --estimate-only is given")
    counts = run(args.dataset, args.out, limit=args.limit, retries=args.retries)
    print(f"written={counts['written']} skipped={counts['skipped']} failed={counts['failed']}")
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
