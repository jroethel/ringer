# jev-pilot/tests/test_writeup.py
import csv, os, subprocess
from pathlib import Path

W = Path("jev-pilot/writeup.md")
DIS = Path("jev-pilot/out/disagreements.csv")


def test_writeup_has_all_sections_and_no_em_dash():
    text = W.read_text()
    for h in ["## Agreement", "## Disagreement review", "## Calibration",
              "## Economics", "## No production path changed", "## Adoption input"]:
        assert h in text
    assert "—" not in text, "no em dash character allowed"


def test_writeup_reports_stratified_agreement_and_baseline():
    text = W.read_text().lower()
    assert "spec_source" in text or ("manifest" in text and "log" in text)
    assert "baseline" in text


def test_every_disagreement_is_categorized():
    rows = list(csv.DictReader(DIS.open()))
    assert rows, "there must be at least one disagreement row"
    assert all(r["category"] in {"jev-correct", "hand-correct", "ambiguous"} for r in rows)


def test_ringer_runtime_paths_untouched_since_branch_point():
    ringer = os.path.expanduser("~/repos/ringer")
    base = subprocess.run(["git", "-C", ringer, "merge-base", "main", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    out = subprocess.run(
        ["git", "-C", ringer, "diff", "--name-only", f"{base}...HEAD", "--",
         "ringer.py", "registry", "engines", "hooks", "hud", "dashboard"],
        capture_output=True, text=True, check=True,
    )
    assert out.stdout.strip() == "", f"runtime path changed: {out.stdout!r}"
