"""Reveal the blind HC2 picks: join blind_review.csv against blind_key.csv and write
the `category` column of disagreements.csv, plus inter-rater agreement over a second
rater's sample.

The categorization stays blind by construction: the rater picked option_a or option_b
without seeing which side was Jev's, and the label is derived here from that pick.
"""

import argparse
import csv
from pathlib import Path

CATEGORIES = {"jev-correct", "hand-correct", "ambiguous"}

# The HC2 sheet was filled in shorthand, so A/B and option_a/option_b both normalize.
_PICKS = {
    "a": "option_a",
    "option_a": "option_a",
    "b": "option_b",
    "option_b": "option_b",
    "ambiguous": "ambiguous",
}


def normalize_pick(raw: str) -> str:
    """Case-insensitive A/B shorthand to the rubric's literal pick value."""
    try:
        return _PICKS[(raw or "").strip().lower()]
    except KeyError:
        raise ValueError(
            f"unrecognized pick {raw!r}; expected one of A, option_a, B, option_b, ambiguous"
        ) from None


def _read_picks(path) -> dict:
    rows = list(csv.DictReader(Path(path).open(newline="")))
    return {r["task_key"]: normalize_pick(r["pick"]) for r in rows}


def categorize(picks: dict, key: dict) -> dict:
    """Map each task_key's normalized pick to jev-correct, hand-correct, or ambiguous."""
    out = {}
    for task_key, pick in picks.items():
        if task_key not in key:
            raise ValueError(f"{task_key} has a pick but no entry in blind_key.csv")
        if pick == "ambiguous":
            out[task_key] = "ambiguous"
        else:
            out[task_key] = "jev-correct" if pick == key[task_key] else "hand-correct"
    return out


def inter_rater(picks_a: dict, picks_b: dict) -> dict:
    """Share of the overlapping task_keys where both raters picked the same value."""
    shared = sorted(set(picks_a) & set(picks_b))
    agree = sum(1 for k in shared if picks_a[k] == picks_b[k])
    return {"n": len(shared), "agree": agree, "rate": agree / len(shared) if shared else 0.0}


def write_categories(disagreements_path, categories: dict) -> int:
    """Add or fill the category column of disagreements.csv; every row must be covered."""
    path = Path(disagreements_path)
    rows = list(csv.DictReader(path.open(newline="")))
    missing = [r["task_key"] for r in rows if r["task_key"] not in categories]
    if missing:
        raise ValueError(f"no blind pick for {len(missing)} disagreement rows: {missing}")
    fields = [f for f in rows[0] if f != "category"] + ["category"]
    for r in rows:
        r["category"] = categories[r["task_key"]]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description="Reveal the blind HC2 categorization.")
    p.add_argument("--review", default="jev-pilot/out/blind_review.csv")
    p.add_argument("--key", default="jev-pilot/out/blind_key.csv")
    p.add_argument("--rater2", default="jev-pilot/out/blind_review_rater2.csv")
    p.add_argument("--disagreements", default="jev-pilot/out/disagreements.csv")
    args = p.parse_args(argv)

    picks = _read_picks(args.review)
    key = {r["task_key"]: r["jev_option"] for r in csv.DictReader(Path(args.key).open(newline=""))}
    categories = categorize(picks, key)
    written = write_categories(args.disagreements, categories)

    counts = {c: sum(1 for v in categories.values() if v == c) for c in sorted(CATEGORIES)}
    print(f"categorized rows={written} " + " ".join(f"{c}={n}" for c, n in counts.items()))

    rater2_path = Path(args.rater2)
    if rater2_path.exists():
        ir = inter_rater(picks, _read_picks(rater2_path))
        print(f"inter_rater n={ir['n']} agree={ir['agree']} rate={ir['rate']:.3f}")
    else:
        print("inter_rater: no second rater file found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
