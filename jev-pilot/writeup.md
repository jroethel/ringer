# Jev task_type shadow-mode pilot: results

Jev matched the hand-assigned `task_type` on 103 of 155 real historical tasks, a pooled agreement rate of 0.665 against a majority-class baseline of 0.310.
Under blind review of the 52 disagreements, the categorizer preferred Jev's label 38 times and the hand label 14 times, with zero called ambiguous.
Every number below is copied from `jev-pilot/out/analysis.json` or recomputed from `jev-pilot/out/diff.csv` and `jev-pilot/out/disagreements.csv`; nothing here is estimated.

Source artifacts: `jev-pilot/out/analysis.json`, `diff.csv` (155 rows), `disagreements.csv` (52 rows), `blind_review.csv`, `blind_key.csv`, `blind_review_rater2.csv`.
The run is one live pass over all 155 distinct log tasks, model `jev-latest`, plus a 12-task retest for the noise floor.

## Agreement

Pooled agreement is 103/155 = 0.665.
The majority-class baseline is 0.310, the share of the most common hand label (`docs`, 48 of 155), so agreement runs 0.355 above the baseline a constant predictor would achieve.

Stratified by `spec_source`, because 113 of 155 inputs carry only the log's 500-char truncated spec:

| spec_source | n   | agree | rate  |
| ----------- | --- | ----- | ----- |
| manifest    | 42  | 31    | 0.738 |
| log         | 113 | 72    | 0.637 |
| pooled      | 155 | 103   | 0.665 |

Agreement is 0.101 higher on the full-spec (`manifest`) stratum than on the truncated (`log`) stratum, which is the direction a truncation effect would predict.
The full-spec stratum is the better estimate of production behavior, because a live assignment would see the whole spec.

Per hand label:

| hand_label     | n  | agree | rate  | power                |
| -------------- | -- | ----- | ----- | -------------------- |
| docs           | 48 | 19    | 0.396 | adequately powered   |
| code-feature   | 43 | 38    | 0.884 | adequately powered   |
| code-fix       | 39 | 23    | 0.590 | adequately powered   |
| site-build     | 12 | 11    | 0.917 | adequately powered   |
| code-review    | 7  | 7     | 1.000 | adequately powered   |
| persona-review | 4  | 4     | 1.000 | inconclusive (n < 5) |
| probe          | 1  | 1     | 1.000 | inconclusive (n < 5) |
| research       | 1  | 0     | 0.000 | inconclusive (n < 5) |

Three classes carry n < 5 and are flagged inconclusive: `persona-review` (n = 4), `probe` (n = 1), and `research` (n = 1).
Their rates of 1.000, 1.000, and 0.000 are single-digit-sample artifacts and must not be read as performance.

The `research` row is additionally prediction-empty.
Across all 155 tasks Jev drew `research` zero times, so no evidence about that class exists in either direction; its one hand-labeled task was assigned `docs` by Jev.
Jev's full prediction distribution over the 155 tasks is `code-feature` 69, `site-build` 27, `code-fix` 24, `docs` 22, `code-review` 7, `persona-review` 4, `probe` 2, `research` 0.

The pooled rate is dominated by one class.
`docs` at 0.396 carries 29 of the 52 disagreements by itself, and the next section shows where those 29 landed under blind review.

## Disagreement review

All 52 disagreements were categorized blind.
The categorizer saw only `task_key`, the spec, and two candidate labels shuffled as `option_a` and `option_b` in `blind_review.csv`, with no indication of which side was Jev's.
The A/B-to-source mapping lived only in `blind_key.csv`, which the categorizer did not open while picking.
`jev-pilot/jev_pilot/reveal.py` performed the join afterward, so no category was ever hand-entered next to a visible "this is Jev's answer".

The rubric, verbatim from the plan:
`jev-correct` = Jev's type is the correct one for this spec.
`hand-correct` = the hand-assigned type is correct.
`ambiguous` = both are defensible or neither clearly fits.

Categorizer identities: the first rater is the project owner, rating blind, covering all 52 rows.
The second rater is an independent blind reasoning-model pass (opus), covering a seeded random sample of 20 of the 52.

Inter-rater agreement is 17 of 20 = 0.850 over the overlapping keys, counting `ambiguous` as a value.
The three differing rows are `t01-inventory-scraper` (rater 1 picked option_b, rater 2 option_a), `u14-proof-2` (option_a versus ambiguous), and `u15-submission` (option_b versus ambiguous).
On that shared 20-row sample the two raters skew the same direction: rater 1 gives 15 jev-correct and 5 hand-correct, rater 2 gives 12 jev-correct, 6 hand-correct, and 2 ambiguous.
The category skew is therefore not an artifact of a single rater.

The category skew over all 52 disagreements:

| hand_label        | disagreements | jev-correct | hand-correct | ambiguous |
| ----------------- | ------------- | ----------- | ------------ | --------- |
| docs              | 29            | 23          | 6            | 0         |
| code-feature      | 5             | 4           | 1            | 0         |
| code-fix          | 16            | 10          | 6            | 0         |
| site-build        | 1             | 1           | 0            | 0         |
| research          | 1             | 0           | 1            | 0         |
| all disagreements | 52            | 38          | 14           | 0         |

Disagreements skew 38 jev-correct to 14 hand-correct, a 0.731 jev-correct share, with zero rows called ambiguous.
The skew is strongest exactly where agreement was weakest: 23 of the 29 `docs` disagreements were judged jev-correct, meaning most of the `docs` class's low 0.396 agreement rate is the hand label being wrong rather than Jev being wrong.
Of the 38 jev-correct rows, Jev's winning label was `code-feature` 26 times, `site-build` 10 times, `probe` once, and `code-fix` once.
By `spec_source` the skew holds in both strata: `log` 32 jev-correct to 9 hand-correct, `manifest` 6 jev-correct to 5 hand-correct.
The `manifest` stratum's 11 disagreements are a thin slice, so the near-even split there is weak evidence and should not be read as a real stratum difference.

Reading the blind review as ground truth on the disagreements only, Jev would be right on 103 + 38 = 141 of 155 tasks (0.910) and the hand assignment right on 103 + 14 = 117 of 155 (0.755).
That comparison carries one structural caveat: the 103 agreeing rows were never independently reviewed, so both sides are credited as correct there by construction, and only the 52 disagreements were actually adjudicated.

## Calibration

Split at the plan's 0.9 confidence cutoff:

| cell                     | n  | fine accuracy | parent accuracy | power              |
| ------------------------ | -- | ------------- | --------------- | ------------------ |
| confident (conf >= 0.9)  | 89 | 0.809         | n/a             | adequately powered |
| unconfident (conf < 0.9) | 66 | 0.470         | 0.545           | adequately powered |

Both cells carry n well above 10, so neither is flagged underpowered; no calibration cell in this run falls below that threshold.
Confidence separates the two groups cleanly: 0.809 accuracy above the cutoff against 0.470 below it, a 0.339 gap, so the confidence field carries real signal and is usable as a routing gate.

Confidence histogram, non-empty bins only:

| confidence bin | n  |
| -------------- | -- |
| 0.4 to 0.5     | 9  |
| 0.5 to 0.6     | 9  |
| 0.6 to 0.7     | 6  |
| 0.7 to 0.8     | 14 |
| 0.8 to 0.9     | 28 |
| 0.9 to 1.0     | 89 |

The mass splits 89 at or above 0.9 against 66 below, a 57/43 split.
The plan's conditional re-run at a data-driven cutoff triggers only when the mass sits almost entirely on one side of 0.9, which it does not, so that re-run was not triggered.
A supplementary read at the median confidence of 0.95 was computed read-only during Task 4 and is recorded in `jev-pilot/out/loop/unit-04.md`: confident n = 78 accuracy 0.795, unconfident n = 77 fine 0.532 parent 0.597.
It may be cited as a sensitivity check only; it is not a second primary result, and it moves the confident-versus-unconfident gap from 0.339 to 0.263 rather than overturning it.

The parent fallback lifts the unconfident cell from 0.470 to 0.545, a gain of 0.076, or 5 of the 66 unconfident rows.
That gain benefits only the code family.
`parent_label` collapses `code-feature`, `code-fix`, and `code-review` to `code`, while `docs`, `site-build`, `persona-review`, `probe`, and `research` each map to themselves.
A low-confidence miss outside the code family therefore gets no fallback credit at all, and the headline parent number must not be read as a general safety net.

## Economics

| measure                    | value       |
| -------------------------- | ----------- |
| total input tokens         | 128,400     |
| total output tokens        | 12,555      |
| input tokens per decision  | 828.4       |
| cost per decision          | $0.00003479 |
| cost for all 155 decisions | $0.005393   |
| median latency             | 188.6 ms    |
| p95 latency                | 261.3 ms    |

Token counts are the measured `usage` fields from the live responses, not an estimate from character counts.
Cost uses both HC1-confirmed prices, $0.042 per million input tokens and $0.00 per million output tokens for `jev-1.13.0`, so output tokens contribute nothing at the current price and the whole 155-task run cost about half a cent.
The docs warn that prices can change without notice, so the per-decision figure is only valid at the HC1-confirmed rate.
Latency is measured wall-clock per call with `time.perf_counter`, single-threaded, from this machine; p95 at 261 ms is well inside what an assignment-time call could absorb.

Stochasticity is the noise caveat on every rate above.
The 12-task retest produced 0 flips out of 12, a flip rate of 0.000.
That retest is a head-of-file draw, not a random sample: it is the first 12 rows of `dataset.jsonl`, which are 11 `manifest` and 1 `log`, while the full dataset is 42 `manifest` and 113 `log`.
So 0/12 bounds the noise floor only for that slice, which is heavily weighted toward the full-spec stratum where confidence and agreement are both higher.
The truncated-spec stratum, which carries 113 of 155 tasks and 41 of 52 disagreements, has no measured noise floor at all, and a retest drawn from it could show a higher flip rate.

## No production path changed

No ringer runtime path was modified at any point in this pilot.
All pilot code lives under `jev-pilot/` on the branch `jev-pilot-task-type`, and all outputs live under the git-ignored `jev-pilot/out/`.
The hand-assigned `task_type` remained authoritative throughout; Jev's picks were written to disk and never fed back into any ringer decision.
`~/.ringer/runs.jsonl` and `~/.ringer/manifests/` were read only.

This is enforced by a test, not by assertion.
`test_ringer_runtime_paths_untouched_since_branch_point` in `jev-pilot/tests/test_writeup.py` takes the merge-base of `main` and `HEAD` and diffs `ringer.py`, `registry`, `engines`, `hooks`, `hud`, and `dashboard` across the whole branch, asserting the changed-file list is empty.
The test passes, so the branch demonstrably touches zero runtime paths.

## Adoption input

The adoption read belongs to HC3 and is not made here.
What the evidence supports, and what it does not:

Supporting adoption: agreement is 0.665 against a 0.310 baseline; it rises to 0.738 on the full-spec stratum a production call would actually see; disagreements skew 38 jev-correct to 14 hand-correct with zero ambiguous, and the second rater's sample skews the same way; confidence separates accuracy cleanly at 0.809 versus 0.470, giving a usable gate; and the whole run cost half a cent at 189 ms median latency, so the economics are not a constraint.

Arguing for caution: the raw agreement rate of 0.665 is not itself high, and the case for adoption rests on the blind review being right that most disagreements are hand-label errors, which is a judgment call adjudicated on 52 rows by one full rater and one 20-row second rater.
Three classes (`persona-review`, `probe`, `research`) are inconclusive at n < 5 and `research` has no Jev predictions at all, so adoption would be adopting a system with no evidence on three of the eight types.
The noise floor is measured only on a 12-task full-spec slice, so the stability of the truncated-spec majority is unmeasured.
Unconfident predictions are near coin-flip at 0.470 fine accuracy, and the parent fallback that softens this covers only the code family.

The plan's HC3 conditions map to this evidence as follows.
Agreement high relative to the majority-class baseline: met, 0.665 against 0.310.
Holds up within the full-spec stratum: met, 0.738 on n = 42.
Disagreements skew jev-correct or ambiguous under blind review: met, 38 of 52 jev-correct and 0 ambiguous, against 14 hand-correct.
Calibration holds on adequately powered subgroups: met, both cells n >= 66 with a 0.339 accuracy gap across the cutoff.

If adoption proceeds, the shape the evidence supports is proposal with a confidence gate, not silent auto-assignment.
Route predictions at or above 0.9 as a pre-filled default a human can override, leave predictions below 0.9 unassigned or flagged, and keep `research`, `probe`, and `persona-review` out of the automated path until each has been observed on a real sample of at least five tasks.
