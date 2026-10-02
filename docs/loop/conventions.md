# Loop conventions

Prose surface for the loop skills.
The line-anchored keys live in `docs/loop/pointer.md`.

## The agent: label vocabulary

- `agent:todo` - open and unclaimed.
- `agent:working` - claimed and in progress.
- `agent:needs-input` - blocked on a human answer.
- `agent:review` - work done, awaiting review.
- `agent:done` - finished.

Exactly one `agent:` label is active on an issue at a time.
`agent:done` is reachable only through the receipt helper's `done` verb, which ships inside the loop-drive skill.
Two non-agent labels also exist: `idea` (parked backlog item, not active work) and `wayfinder:map` (wayfinder mapping item).

## Filename grammar

Files in the doc-tree homes (`docs/handoffs/`, `docs/briefs/`, `docs/plans/`, `docs/reviews/`, `docs/archive/`) are named `YYYY-MM-DD.<descriptor>.md`.
The date comes first and segments are dot-separated.
The descriptor is a short slug with optional tracker-token segments, for example `.I6` for issue 6.
The loop-drive resume pointer (`YYYY-MM-DD.<unit-slug>.resume.md`) and the loop-auto batch-review journal (`YYYY-MM-DD.<tokens>.<slug>-batch-review.md`) are the two fixed instances.

## Archive and graduation

Work that is finished or superseded moves to `docs/archive/` with its filename unchanged.
A parked `idea` graduates to active work by dropping the `idea` label and adding `agent:todo`.
Nothing is deleted on graduation; the tracker keeps the history.

## Verbose announce

When a loop skill acts, it announces what it is about to do and which source it resolved before doing it.
Nothing runs silently, and the announcement names the file or issue number it touches.
