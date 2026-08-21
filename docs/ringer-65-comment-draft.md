Shipped this, and the design is better for @barthballard's notes - thank you for the careful read.

Two of your points shaped the build directly. On placement, I partition the amendments out and group the attempts, so a (model, task_type) pair whose only task was amended drops out of the table entirely rather than surviving as a `tasks == 0`, 0.00 first-try row - exactly the "total failure on the scoreboard you are trying to correct" trap you flagged. And on void-do-not-flip, the amended attempt is treated as evidence-void, neither credit nor blame, so a wrong FAIL stops demoting the model without a phantom PASS over-crediting output that was never actually validated.

The part I want to credit you for by name is the generalization: framing a wrong FAIL and a human rejection of a bad PASS as mirror images that both want the same primitive - append-only, caller-trusted, note-required, audit-logged - so building `amend` general enough to carry both directions leaves one audit model instead of two. That reframe is what the shipped schema is built around. The amendment row carries an open `reclassify` field rather than a boolean check-bug flag, so the second direction lands later as one more value on one command, with no new log format and no migration.

What shipped in this pass:

- An append-only `amend` command - `./ringer.py amend <run_id> <task_key> --reclassify check_bug --note "why"` - that appends a typed amendment row to `runs.jsonl` and never edits or reorders an existing line. A second identical call is a no-op with a message.
- Whole-task void, per your default: if the check was wrong, everything it graded is voided, and the (run_id, task_key) key leaves room for the attempt-level filter you hit that one edge on.
- `check_bug` as the only accepted `reclassify` value today, with the schema left open for the human-rejection direction and any future kind.
- The `amended` count surfaced on the `models` table and HTML page, plus a read-only `triage` view that shows each amendment inline next to the FAIL it corrects, so the per-run report knows better too - your fourth note.

Net effect: an audited misattribution can now be voided after the fact, and the promotion math (`first_try_pass_rate` against `PROVEN_MIN_FIRST_TRY`) finally hears about it. The non-goal holds - attribution stays human-driven, the command trusts its caller and requires the note for the audit trail. Would welcome a look at the general schema against your fork's `mark --check-fault` shape.
