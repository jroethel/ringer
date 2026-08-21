# Amendment rows as the routing integrity layer (ringer #65)

This note is the argument for upstream acceptance of issue #65 (amendment rows).
It is written to be lifted into the PR description.

## The reframing

loop-stack's routing now leans on the scoreboard as its single evidence source for every unit.
Under that design, amendment rows stop being a nice-to-have correction tool.
They become the integrity layer of the entire routing system.
A check bug is no longer one bad log line: left unamended, it silently mis-routes every future unit of that task_type, because the check's exit code is the only verdict ringer records and `first_try_pass_rate` drives the promotion ladder.

## The evidence

The stm-nav-restructure run (2026-07-17/18) recorded 8 diagnosed FAILs.
Of those, 7 were orchestrator check bugs, not model failures - all seven on glm-5.2, and every one had its worker output audited correct at the gate and committed unchanged.
The 8th stayed a genuine model signal.
Per-row rationale and corrected aggregates are in `docs/AMENDMENTS-PENDING.md` (Sections A through D).
The patch design - append-only amendment rows, the `amend` CLI, and aggregation that subtracts amended attempts - is in `docs/AMENDMENT-ROWS.md`.

## The appeals process

This is not a feature being argued past the maintainer.
Nate pre-argues it himself.

> "When a check fails a worker, sometimes the check is wrong, so build in the post-mortem that can rule for the accused. Without one, your verification layer calcifies into bureaucracy people learn to game."
> - Nate B. Jones, 2026-07-08 Substack ringer article, section "The appeals process".

The patch is specced in `docs/AMENDMENT-ROWS.md`, and the seven pending amendments in `docs/AMENDMENTS-PENDING.md` Section D are its first acceptance test.
