# Amendment rows: reclassifying check-bug FAILs (design note)

Status: proposed, not built.
Owner: Jeremy (patch planned).
Filed as a GitHub issue on 2026-07-17; this note carries the implementation detail the issue summarizes.

## Problem

The executed check's exit code is the only verdict ringer records.
When the CHECK is wrong (over-strict grep, unsatisfiable assertion, crash), the FAIL lands on the model's eval row anyway.
`first_try_pass_rate` drives the promotion ladder (`PROVEN_MIN_FIRST_TRY`, ringer.py ~2364), so check bugs demote models invisibly.
The only correction channel today is a prose annotation in `docs/MODEL-NOTES.md` - human-read, not machine-read; the scoreboard math never hears about it.

Evidence this is a recurring class, not a one-off:

- Run `stm-nav-restructure` (2026-07-17): two recorded FAILs (`task-05-pipeline-trim-admin`, `task-09-condense-tableau`) were orchestrator check bugs; worker output audited fully correct both times (format-strict negative greps - one matched the requested link-out stub, one matched historical docs the spec forbade the worker from touching).
- MODEL-NOTES already carries at least three earlier check-bug annotations from other runs (see lines noting "recorded retry was an orchestrator check bug").

## Proposal

Append-only amendment rows in `runs.jsonl`, written by an explicit CLI command; aggregation subtracts amended attempts.

### CLI

```
./ringer.py amend <run_id> <task_key> --reclassify check_bug --note "why"
```

- Appends one JSON object to the model log (same file the eval rows live in):

```json
{"type": "amendment", "run_id": "...", "task_key": "...", "reclassify": "check_bug", "note": "...", "amended_at": "ISO8601", "identity": "<who>"}
```

- Idempotent: a second identical amend is a no-op with a message.
- No delete/edit of existing rows, ever - immutability is the point.
- `--reclassify` starts with the single value `check_bug`; leave room in the schema for future kinds but do NOT build them.

### Aggregation

- `aggregate_model_log_rows` (ringer.py:5357): collect amendments first, then skip every attempt row whose `(run_id, task_key)` is amended when computing tasks, first-try, pass counts, and token medians.
- Amend the whole `(run_id, task_key)`, not individual attempts - if the check was wrong, every attempt it graded is meaningless.
- Track an `amended` count per (model, task_type) group so the exclusion is visible.

### Display

- `models` table: an `Amended` column (or a footnote count) per row - corrections must be visible, not silent.
- `models --open` HTML (rendering ~ringer.py:4552-4589): same, plus the amendment notes surfaced next to MODEL-NOTES excerpts.
- The derived SQLite read model (`db` command) needs the same exclusion or a rebuild step; check how it ingests runs.jsonl.

### Non-goals

- No auto-detection of check bugs: attribution genuinely requires judgment; this stays a human/orchestrator call.
- No editing of MODEL-NOTES from the command; prose context still belongs there.

## Acceptance

1. Amending the two stm-nav check-bug rows restores glm-5.2's first-try rate to what the audited reality supports, and `models` shows the amended count.
2. `runs.jsonl` after amending contains only appended rows; every original row byte-identical.
3. Re-running `amend` with the same args changes nothing and says so.
4. A run that was legitimately failed by its check cannot be distinguished mechanically - the command trusts its caller; the `note` field is mandatory for the audit trail.
