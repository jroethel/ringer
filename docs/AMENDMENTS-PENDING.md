# Pending amendments: stm-nav-restructure run (2026-07-17/18)

Companion to `AMENDMENT-ROWS.md` (the design note) and GitHub issue #65.
This file is the DATA: which recorded rows are misattributed, the evidence, the correction usable today without the patch, and the exact injection to run once the patch lands.
Written by the orchestrating session that caused every one of these check bugs, from its gate audits; each row's work product was verified correct by an independent re-derivation before its commit.

## A. The misattributed rows (amend these)

All seven are `model: glm-5.2`, `verdict: fail after retry`; in every case the worker's output was audited correct at the orchestrator gate and committed unchanged (see the per-round table in forge `docs/superpowers/plans/2026-07-17-stm-nav-restructure_loop-state.md`).

| run_id | task_key | why the check was wrong |
|---|---|---|
| stm-nav-restructure-20260718T032612Z-p359280 | task-05-pipeline-trim-admin | negative phrase-grep matched the exact link-out stub the spec requested; allowlist grep matched an explanatory comment |
| stm-nav-restructure-20260718T120157Z-p461404 | task-09-condense-tableau | repo-wide negative grep counted historical docs the spec forbade the worker from touching; unsatisfiable by design |
| stm-nav-restructure-20260718T143419Z-p525993 | task-17-dash-font-cleanup | spec/check gap: schema.html is a hybrid hand-edited shell no worker owned, so its `&mdash;` was unreachable within the boundary |
| stm-nav-restructure-20260718T162712Z-p566096 | task-18-schema-guide | check transport: quoted for-loop mangled through JSON-to-shell; every step green when re-run at the gate |
| stm-nav-restructure-20260718T180947Z-p600985 | task-20-prose-list-measure | "only file X changed" whole-tree assertion tripped on the ORCHESTRATOR'S own uncommitted plan edit |
| stm-nav-restructure-20260718T131829Z-p489410 | task-12-validate | validator rubric echoed a stale orchestrator premise (mockups importing forge.css - they are self-contained); artifact correct, verdict spec-problem |
| stm-nav-restructure-20260718T174614Z-p595222 | task-18-19-guide-validate | attempt-1 verdict was accurate (attempt-2 audit agreed); the output-format check rejected its shape |

## B. Do NOT amend (signal, not noise)

| run_id | task_key | why it stays |
|---|---|---|
| stm-nav-restructure-20260718T024819Z-p347247 | task-03-stm-guide-validate | genuine model signal both ways: attempt 1 wrote pass against its own contradicting notes (verdict indiscipline), and the final fail verdict correctly flagged a real implementer content defect (duplicated scraper internals) |

Undiagnosed, no evidence either way - leave untouched: the attempt-1 failures inside rounds that finally passed on retry with no gate diagnosis (site map task-14-sitemap-guide-index, task-19-schema-fixes, task-19-wide-nav-reset, task-21-nav-v2-all-guides).

Borderline, Jeremy's call, only if the patch ever supports per-ATTEMPT amendment (whole-task amendment would erase a legitimate pass): task-01-overflow-fix (run ...013812Z-p321439; attempt-1 fail was an over-strict determinism check) and task-06-schema-refresh-validate (run ...031352Z-p355426; attempt-1 was a check crash with no output).

## C. Usable NOW, without the patch

Corrected aggregates from the raw log, excluding the seven misattributed (run_id, task_key) pairs - paste-ready:

```bash
jq -s '
  [ .[] | select(.model != null) ] as $rows |
  [ ["stm-nav-restructure-20260718T032612Z-p359280","task-05-pipeline-trim-admin"],
    ["stm-nav-restructure-20260718T120157Z-p461404","task-09-condense-tableau"],
    ["stm-nav-restructure-20260718T143419Z-p525993","task-17-dash-font-cleanup"],
    ["stm-nav-restructure-20260718T162712Z-p566096","task-18-schema-guide"],
    ["stm-nav-restructure-20260718T180947Z-p600985","task-20-prose-list-measure"],
    ["stm-nav-restructure-20260718T131829Z-p489410","task-12-validate"],
    ["stm-nav-restructure-20260718T174614Z-p595222","task-18-19-guide-validate"] ] as $amended |
  [ $rows[] | select( ([.run_id, .task_key]) as $k | ($amended | index($k)) | not ) ]
  | group_by(.model)
  | map({model: .[0].model, rows: length})
' ~/.ringer/runs.jsonl
```

(Adjust the final reduce to whatever stat is needed; the load-bearing part is the `$amended` exclusion list, which is the same data Section D injects.)

## D. Post-patch injection (run after `ringer.py amend` exists)

Ready to paste, notes included - these are the seven commands, nothing else:

```bash
cd ~/repos/ringer
./ringer.py amend stm-nav-restructure-20260718T032612Z-p359280 task-05-pipeline-trim-admin --reclassify check_bug --note "negative phrase-grep matched the requested link-out stub; allowlist grep matched a comment; work audited correct, committed 0c29bc7"
./ringer.py amend stm-nav-restructure-20260718T120157Z-p461404 task-09-condense-tableau --reclassify check_bug --note "repo-wide negative grep demanded a state the spec forbade; work audited correct, committed d72ca3c"
./ringer.py amend stm-nav-restructure-20260718T143419Z-p525993 task-17-dash-font-cleanup --reclassify check_bug --note "hybrid schema.html shell was outside every worker boundary; work correct, one-line gate fix, committed 5d7c2ba"
./ringer.py amend stm-nav-restructure-20260718T162712Z-p566096 task-18-schema-guide --reclassify check_bug --note "check transport bug (JSON-to-shell quoting); all steps green on gate re-run, committed 414979d"
./ringer.py amend stm-nav-restructure-20260718T180947Z-p600985 task-20-prose-list-measure --reclassify check_bug --note "whole-tree only-X-changed assertion hit the orchestrator's own uncommitted plan edit; rule correct, committed c7ae3a1"
./ringer.py amend stm-nav-restructure-20260718T131829Z-p489410 task-12-validate --reclassify check_bug --note "validator rubric encoded a stale orchestrator premise; artifact correct (spec-problem verdict), committed ce7c027"
./ringer.py amend stm-nav-restructure-20260718T174614Z-p595222 task-18-19-guide-validate --reclassify check_bug --note "accurate verdict rejected on output shape by the check; attempt-2 audit agreed with attempt-1's pass"
```

Agent prompt to run the injection and verify (paste into any capable session after the patch merges):

> In ~/repos/ringer, run the seven `./ringer.py amend` commands in docs/AMENDMENTS-PENDING.md Section D exactly as written - do not amend anything in Section B.
> Then run `./ringer.py models` and confirm: (1) an amended count of 7 appears against glm-5.2's groups, (2) glm-5.2's first-try and pass rates for site-build/docs/code-fix/code-review no longer count those seven tasks in their denominators, (3) `runs.jsonl` grew by exactly seven appended amendment rows and no existing row changed (verify with `git diff` semantics or a before/after line count + checksum of the original lines).
> Re-run one amend command and confirm it is an idempotent no-op.
> Report the before/after rates for glm-5.2.

## D. loop-setup-reconcile run (2026-08-08) - same pattern, new cause

| run_id | task_key | why the check was wrong |
|---|---|---|
| loop-setup-reconcile-20260808T044738Z-p246730 | loop-setup-reconcile | check transport: ringer runs checks via /bin/sh (dash on WSL), which rejects `set -o pipefail` at line 1; zero assertions ever executed. Work audited correct at the gate (full check re-run under bash: six suites green, 4 commits, clean tree) and committed unchanged as 3eaa7f9 in loop-stack-session. |

Root fix staged, Jeremy's to fire: `executable="/bin/bash"` in `_run_check`'s `create_subprocess_shell` call (ringer.py ~8649).
- 2026-08-08 run normalize-once-batching-20260808T131030Z-p348363 task calcdate-stability (glm-5.2, code-fix): amend both FAIL attempts to check-bug (orchestrator's check had a bash syntax error and never executed); worker output audited correct and committed as-is.

## gitlab-glab-loop run (2026-08-09)

One misattributed row, same class as section A: the worker's output was audited correct at the orchestrator gate and committed unchanged (loop-stack-session `docs/handoffs/2026-08-09-gitlab-glab-loop-run-state.md`, wave 5).

| run_id | task_key | why the check was wrong |
|---|---|---|
| gitlab-glab-loop-20260809T191559Z-p881946 | task-6-fix | unsatisfiable gate: the manifest check required `.scratch/*/issues` documented in loop-setup SKILL.md while the repo's own `tests/loop-setup/acceptance.sh:18` (stale since setup.sh re-added the scratch scan in afc7fbd) failed the full suite on any `scratch` substring there; attempt 2 satisfied the check's demand and was failed by the stale test. Gate audit deleted the stale test line, salvaged the worktree diff, verified all three fix sites by hand, and committed with the full suite green (36/36) |
