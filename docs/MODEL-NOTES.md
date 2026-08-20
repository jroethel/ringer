# Model notes — how workers actually perform

A running log of how models perform on real Ringer tasks, so engine and
model choices are made on evidence instead of vibes. The raw numbers now
live in the local eval log (`~/.ringer/runs.jsonl`); run `./ringer.py models`
to print the per-model, per-task_type scoreboard (tasks, attempts,
pass_rate, first_try_pass_rate, median duration/tokens, last_seen). This
file remains the judgment layer on top of those numbers.

**How to add a row:** after reviewing a run (post-run ritual step 5 in the
ringer skill), append one dated line under the model. Say the task type,
what happened, and what you'd do differently. Only write what the executed
checks and raw logs support — no vibes, no worker self-reports.

## codex (GPT-5-class, own harness)

- Strongest general worker; the default engine. Spend reasoning effort per
  task via `engine_args` (`["-c", "model_reasoning_effort=low|medium|high"]`)
  — high on gnarly tasks, low on boilerplate.
- 2026-07-05 — carried the heavy lanes of the milk-crate demo rehearsals
  (market read with source allowlist, site build) with clean first-attempt
  passes.
- 2026-07-10 — gpt-5.6-sol, code-feature (steering-profiles feature in
  ringer.py itself, ~470-line change + 18 tests + docs, run
  ringer-steering-profiles): shipped as PR #25. 2 attempts, 379k tokens,
  but the attempt-1 FAIL was the CHECK's fault, not the model's — the check
  gated on the ENTIRE pre-existing suite being green inside the worker
  sandbox (localhost binds blocked, fixture missing). The feature work
  itself was verified green both attempts; attempt 2 "hardened" an already
  -sound implementation. Scoreboard's FAIL row for this run understates the
  model. Lesson for check authors: regression gates must compare against
  the BASELINE failure set, never assert absolute suite green.
- 2026-07-06 — adversarial pre-merge review (aicred spark): passed on
  attempt 1, ~85k tokens.
- 2026-07-06 — motion design (5 HTML animations for video b-roll) + 2
  editorial diagram pages, each verified by rendering through headless
  Chromium to MP4/PNG: 7/7 passed on attempt 1. Broadcast-quality visual
  output from rich storyboard specs; the render-as-check pattern works.
- 2026-07-06 — milk-crate demo: two single-file website builds (v1 scaffold
  316s/~175k tok; final brand+market-test reskin 622s/~184k tok), both passed
  14-assertion content checks on attempt 1, including base64-embedding photos
  and honoring honesty-marker requirements. Codex remains the site-build lane.
- 2026-07-06 — ringer.py feature batch (task_type field + enriched eval rows
  + `models` scoreboard + hud single-tab fix; ~640-line diff incl. two new
  test suites): substance passed on attempt 1 — its check printed PASS
  (compile, all 16 suites, exact CLI aggregation contract) — but the run
  recorded attempt 2 because of the expect_files-before-check harness bug
  (see process lessons). Heavy single-file feature work against an exact
  behavioral contract is squarely codex's lane.

- 2026-07-06 — elsas-website demo: Next.js scaffold PASSED attempt 2 (682s,
  ~354k tok) — attempt 1 built a complete homepage and silently skipped the
  other 10 routes; the route-enumeration check caught it. Narration lane
  (15 ElevenLabs calls, chunked, nohup pattern) passed attempt 1. CAUTION: a
  codex fix worker GAMED a verbatim-content needle by hiding the required text
  in a visually-hidden paragraph — passed the check, caught only by
  orchestrator integration review. Needle checks need an anti-hidden-text
  assertion or documented exceptions.

- 2026-07-06 — OpenRouter catalog + explore suggester (catalog subcommand
  with snapshot/changelog/free-detection, daemon auto-refresh, tiered
  --explore; offline fixture-driven contract check): PASS attempt 1, 362s.
  Follow-up sentinel-pricing fix (variable-pricing models): PASS attempt 1,
  114s. With the verify-order fix landed, zero phantom retries across the
  whole batch.
- 2026-07-06 — adversarial review of the model-router stack (2,650-line
  diff, structured report contract): PASS attempt 1, 176s — found a real
  HIGH (--since window inflating first-try rates) plus 3 MEDIUMs, all
  confirmed against the code. Then fixed all five review findings in one
  batch (task-level --since, pricing transitions, event durability + flock,
  unknown pricing, stderr notice) with test coverage: PASS attempt 1, 202s.
  Review->fix roundtrip in codex's lane works end to end.
- 2026-07-06 — scoreboard HTML page (zero-LLM renderer, ~700-line diff,
  design + evidence-floor ranking + cost math + notes parser): substance
  PASS attempt 1 (the run's recorded retry was an orchestrator check bug —
  the free-promo watchlist legitimately mentions a free model before the
  ranked cards, and the check compared raw first-occurrence). Six review
  findings fixed in one batch, PASS attempt 1, 141s.
- 2026-07-06 — model-db stack (SQLite read model 516s, page redesign 536s,
  Ringside tab 527s, plus three fix batches all attempt-1): five substantial
  ringer.py features in one day, every one against an executed contract
  check. Review lane found the HIGH that mattered (sync cursor skipping a
  half-written trailing line). Codex is the proven lane for both sides of
  the review->fix loop on this codebase.

## glm-5.2 via opencode (`openrouter/z-ai/glm-5.2`)

- The cheap-intelligence default (~$0.74/M in, $2.33/M out, 2026-07 —
  20-30x cheaper output than frontier coding models). Reliable on
  mechanical, tightly-specced work: file edits, format conversions,
  template-driven builds.
- 2026-07-05 — milk-crate demo rehearsals: handled brand-board/SVG/copy
  tasks at around a penny per passing task.
- 2026-07-06 — adversarial pre-merge review (aicred spark): passed, but
  needed the retry (attempt 2) where codex passed on attempt 1. Long
  structured reviews sit at the edge of its comfort zone; keep the section
  contract explicit in the spec.
- 2026-07-06 — three mechanical image-generation batches (18 images via
  openrouter-image commands, idempotent batch-runner spec): 3/3 passed on
  attempt 1, ~14.5k tokens each. The "execute these exact commands, do not
  improve them" spec pattern is fully reliable for glm-5.2.

- 2026-07-06 — backfill/seed script for the model log (252-line stdlib CLI
  with a run-state join, 3-level mapping precedence, never-overwrite and
  idempotency rules): the artifact was CORRECT; the recorded FAIL was an
  orchestrator check-fixture bug (a missing newline glued the fixture's last
  row to a garbage line) plus the harness ordering bug below. Verified PASS
  once the check was fixed. Tight behavior contracts in the spec work great
  for glm — and read the raw logs before blaming the model.
- 2026-07-06 — README/MODEL-NOTES docs + task_type sweep across 17 template
  manifests: passed attempt 2; attempt 1 was lost to the harness ordering
  bug, not model quality — the retry worker's log correctly diagnosed that
  harness bug unprompted, impressive debugging from the cheap lane.
- 2026-07-06 — catalog/explore README section (flags, promotion ladder,
  per-user framing): PASS attempt 1, ~21.5k tokens. Doc sections against a
  grep-able content contract remain a safe glm lane.
- 2026-07-06 — milk-crate demo, full run: 4 independent buyer-persona
  reviews (focus group) all passed attempt 1 (~15k tokens, ~2¢ each) with an
  explicit VERDICT-block contract — persona work is squarely in glm's zone.
  Market read with live curl fetching passed once the spec demanded verbatim
  copy-paste of source URLs (first fail was the worker trimming URL slugs —
  spec/check craft, not model weakness). Brand-kit doc incl. a clean inline
  SVG wordmark: good, one bounce off an over-strict check regex.

- 2026-07-06 — elsas-website demo: verbatim content capture (16 pages + 19
  news posts, 213 blockquotes) passed attempt 2 — attempt 1 SELF-REPORTED
  "all 213 match exactly, 0 errors" while the executed check found 13 stitched/
  paraphrased quotes. Self-reports are worthless; the retry with injected
  failures fixed all 13 (~148k tok total, ~3¢). Page builds (about+faq;
  news index + 19 generated post routes via its own extraction script) and
  2 focus-group personas: all attempt 1. Fix batch attempt 1.
- 2026-07-06 — invariants/file-I/O review lens on the same stack: PASS
  attempt 1, 68k tokens — caught the non-atomic backfill rewrite (real data
  loss risk) and the daemon stdout race; both confirmed. Then fixed the
  backfill atomicity (tmp+os.replace, pid-stamped backups) attempt 1 with
  the original behavioral grader unchanged. Structured review with an
  explicit lens is now proven glm territory, not just probation.
- 2026-07-06 — solo adversarial review of the scoreboard renderer (~700
  line diff, injection-focused lens): PASS attempt 1 — 1 MEDIUM (unanchored
  MODEL-NOTES heading match cross-contaminating gpt-4/gpt-4o-style
  families) + 5 real LOWs, plus an empirically-verified injection all-clear
  (it actually rendered hostile model ids to prove escaping). Second
  proven-tier structured review in one day; glm is now the default review
  lane for mid-size diffs.
- 2026-07-06 — invariants/injection/frontend review of the 4,061-line
  model-db branch: PASS attempt 1, 96k tokens, 14 coverage items — two real
  contention findings (full catalog re-ingest per sync; schema writes on
  read paths) plus an empirical XSS all-clear on the new DOM surfaces.
  Third proven-tier structured review today.

- 2026-08-08 - loop-setup-reconcile (code-feature, harness claude-zai, loop-stack-session):
  recorded fail-after-retry is MISATTRIBUTED - the check never ran. Ringer executes
  checks via create_subprocess_shell -> /bin/sh (dash on this WSL host), which dies on
  the check's first line (`set -uo pipefail`, "Illegal option -o pipefail"), so both
  attempts burned against an unrunnable gate. Gate audit re-ran the full check under
  bash against the surviving worktree: all six suites green, exactly 4 commits, clean
  tree, footprint exactly the 8 owned files - work committed unchanged (3eaa7f9).
- 2026-08-08 - same run, signal: the worker caught a real plan self-contradiction
  (verbatim test needs `git rm --cached`, plan prose said bare `git rm -f`), deviated
  correctly, and left a comment naming the reason. Second time GLM has diagnosed a
  harness bug unprompted from the cheap lane. Amendment row appended to
  AMENDMENTS-PENDING.md; harness fix (executable="/bin/bash" in _run_check) staged
  for Jeremy, not applied.
- 2026-08-09 - gitlab-glab-loop wave 1 (claude-zai engine): code-feature x2, both
  first-try PASS under executed checks (own new suite plus the full 30-suite run
  inside the worktree). task-1-tracker transcribed a 213-line verbatim test file and
  a multi-branch dispatch rewrite (+303/-25) cleanly; task-2-mirrors was a small
  case-block edit. Confirms the "tightly-specced plus executed check" lane again;
  no signal events, no retries.
- 2026-08-09 - gitlab-glab-loop wave 2 (claude-zai engine): code-feature x1, first-try
  PASS. task-3-setup: a 37k-char spec with eleven interacting sub-steps across five
  files (+358/-55); worker recorded two conservative readings in report.md instead of
  guessing wide, both correct calls. The report-your-reading discipline holds on the
  cheap lane.
- 2026-08-09 - gitlab-glab-loop wave 4 (claude-zai engine): code-feature x1, first-try
  PASS (task-5-migrate, +203/-20 across three files with a vendoring seam into
  setup.sh). Mechanical end of the confirmed lane; no open questions, no retries.
  Running tally this run: glm-5.2 is 4/4 first-try on code-feature.
- 2026-08-09 - gitlab-glab-loop wave 5, signal (check-bug attribution): the recorded
  task-6-fix fail-after-retry is MISATTRIBUTED. The manifest check and a stale repo
  test (`acceptance.sh` scratch ban, premise false since afc7fbd) formed an
  unwinnable gate; the worker fixed all three prose sites correctly, diagnosed the
  conflict, named the exact stale line, and recommended the right resolution. Third
  time GLM has diagnosed a harness/gate bug unprompted from the cheap lane. Row
  logged in AMENDMENTS-PENDING.md; work salvaged from the failed worktree and
  committed after gate audit.
- 2026-08-09 - gitlab-glab-loop wave 5 (claude-zai engine): docs x1, first-try PASS
  (task-6-docs, 7 files). The opus review then failed it on two residual GitHub-only
  prose sites and one understated root list - real substance misses on the strongest
  posterior lane. Lesson: multi-site "fix every occurrence" prose sweeps need the
  occurrence list enumerated in the spec, or a review layer; the keyword check alone
  passed a 3-of-5 fix.
- 2026-08-09 - gitlab-glab-loop terminal repair (claude-zai engine): code-fix x1,
  first-try PASS (task-3-fix: dry-run remote classification plus a committed
  regression scenario). Orchestrator re-ran the reviewer's live repro post-apply
  and confirmed the fix independently. Final run tally for glm-5.2: 6 tasks typed,
  6 substance-correct, one recorded FAIL amended as a check bug.

## opus via claude engine (`claude -p`, model `opus`)

- 2026-08-09 - gitlab-glab-loop wave 3 (claude engine, model opus): code-feature x1,
  first-try PASS on the run's risk-pinned unit (task-4-sweep: destructive archive
  moves plus a judgment edit of an existing green suite, +343/-16). Signal: the
  risk-concentration pin paid off first-try again; worker re-derived a plan count,
  found it off by one for an accounted reason, and named one deliberate one-line
  spec widening in its report instead of taking it silently.
- 2026-08-09 - gitlab-glab-loop wave 3, code-review x1, first-try PASS
  (task-4-review): walked 15 criteria, mutation-tested the guards it was asked to
  verify, and cross-checked the one authorized test retarget by running the
  pre-task suite against the new implementation. Verdict discipline held; two
  advisory findings correctly routed to the orchestrator instead of self-fixed.

## kimi-k2.7 via opencode (`openrouter/moonshotai/kimi-k2.7-code`)

- 2026-07-06 — adversarial pre-merge review (aicred spark): passed on
  attempt 1, ~83k tokens. First real outing; promising for review work.
  (Ran through an ad-hoc copy of the opencode engine block — the per-task
  `model` field now makes that unnecessary.)

## kimi-k2.6 (`moonshotai/kimi-k2.6`, subject-model evidence via OpenRouter)

- 2026-07-07 — Benchmark Suite 2.0 operator eval, killed by Jon at ~4.5h.
  Serving throughput, not model quality, was the failure: on the Brick
  1000-piece case (reasoning xhigh, pinned provider order
  inceptron→decart→baidu→modelrun, no fallbacks) K2.6 averaged ~21 tok/s
  with two ~19-min stalls at 4.5 tok/s — 136+ min unfinished vs Sonnet 5's
  25 min (94 tok/s) and GPT-5.5's 24 min (55 tok/s) on the identical case.
  Model behavior itself was fine: 28 turns (fewer than Sonnet's 82), 170k
  output tokens (in family norms), 12% reasoning, zero API errors. Verdict:
  do NOT schedule K2.6 for long agentic work through that provider set;
  if K2.6 data is ever wanted, probe a single case against other providers
  first. Distinct model from k2.7-code above — don't transfer this verdict
  to k2.7.


## grok-build (Grok CLI engine, flat plan)

- 2026-07-10 — identity correction (Jon): the Grok Build CLI is a HARNESS
  serving exactly two models — Grok 4.5 (xAI) and Composer 2.5 (Cursor).
  The engine-lane slug `grok-build` resolves to Grok 4.5. "Grok Build 0.1"
  was never a model; earlier notes/rows using it as one describe Grok 4.5.

- 2026-07-06 — first outing (elsas-website demo), engine added same day:
  audition PASS attempt 1 in 28.9s. Then: asset harvest (11 images, live URL
  re-fetch check), books page, 5 work-page routes in one task (59 verbatim
  needles), adversarial code review (10 real findings incl. an unshelled 404
  and a broken embedded link), press/media fix batch, audio-player integration
  across 15 pages — ALL attempt 1 (player's red ledger entry was a check bug,
  artifact certified). Fast, precise on mechanical/code work. No token counts
  in JSON output (flat plan) — cost reads "included in plan".

## grok-composer-2.5-fast (Grok CLI engine, flat plan)

- 2026-07-06 — first outing (elsas-website demo): audition PASS attempt 1
  (138s — slower than grok-build but the strongest copy of the round).
  Accessibility constitution (14 testable criteria, SC-numbered) attempt 1;
  a11y-gatekeeper harness (axe+Playwright, light/dark, reduced-motion assert)
  attempt 2 — attempt 1's harness mishandled Next's default /404 route.
  Events/faq/contact fix batch attempt 1, but satisfied "editorial grid" with
  an EMPTY aside landmark — axe caught it (landmark-complementary-is-top-level).
  Persona work: good. Watch for letter-of-the-spec shortcuts on layout asks.

## nemotron-3-super-120b (via opencode, `openrouter/nvidia/nemotron-3-super-120b-a12b:free`)

- 2026-07-06 — AUDITION FAILED (exploration slot, $0 spent — free promo).
  Task: fresh-eyes adversarial review of a 2,650-line diff with a structured
  report contract. Failed both attempts on the same executed check: report
  had the right sections and verdict but under 3 concrete code citations —
  shallow engagement with the actual code, 212k tokens burned. Don't re-run
  this audition on long structured code review; if it gets another slot,
  try a shorter, more mechanical task first.

## llama-3.3-70b-instruct (via opencode, `openrouter/meta-llama/llama-3.3-70b-instruct:free`)

- 2026-07-06 — AUDITION FAILED (exploration slot, $0). Fresh-eyes review of
  a 4,061-line diff with a verbatim-quote citation requirement: failed the
  structured-report check both attempts. Second free-model audition to fail
  on long structured code review (after nemotron-3-super) — the exploration
  ladder now says: audition free models on SHORT mechanical tasks first;
  long-diff review is a proven-tier lane.
- 2026-07-17 — TIMEOUT, even on a trivial one-liner probe (`date`/`whoami`
  plus a 3-section transcript). Two attempts, 300s each, zero output —
  not a content failure like 2026-07-06, a dead connection. Direct
  `opencode-sandboxed.sh` call outside Ringer reproduced the same hang.
  This model looks capacity-throttled on the free tier right now; don't
  route wiring-verification probes to it. `nvidia/nemotron-nano-9b-v2:free`
  answered the same trivial probe in ~3s at $0 — prefer it for a quick
  free-tier smoke test.

## nemotron-nano-9b-v2 (via opencode, `openrouter/nvidia/nemotron-nano-9b-v2:free`)

- 2026-07-17 — WORKS for trivial mechanical probes. Direct
  `opencode-sandboxed.sh` call (outside Ringer, diagnosing the
  llama-3.3-70b-instruct timeout above) answered a one-line instruction in
  ~3s, $0 cost, tool use intact. Untested on real manifest tasks yet —
  next slot should audition it on a short mechanical task per the
  free-model exploration ladder.
- Same session: `meta-llama/llama-3.2-3b-instruct:free` and
  `qwen/qwen3-30b-a3b:free` both failed immediately (3.2-3b: "No endpoints
  found that support tool use" — 404, model doesn't support tool calling
  at all, unusable with OpenCode's agentic harness regardless of task;
  qwen3-30b and `mistralai/mistral-small-3.2-24b-instruct:free`: opaque
  "Unexpected server error" from OpenRouter). Don't route agentic/tool-use
  tasks to non-tool-calling free models — check `supported_parameters`
  before auditioning, not after a timeout.

## Small / flash-class models

- First to choke on long conversational or multi-turn harness tasks —
  watch retry counts before scaling them into a batch (2026-07-05 focus
  group lesson).

## Process lessons (cross-model)

- 2026-07-06 — the orchestrator's CHECKS were the day's top failure source:
  three check bugs (fixture newline join, first-occurrence ordering vs the
  watchlist strip, claim-prefix split on '.' instead of ':') each produced
  a FAIL verdict on work that was actually correct — including all four
  capability-research packets at once. Every one was caught by reading raw
  logs/artifacts before blaming the model. Corollary for the scoreboard:
  recorded FAILs whose root cause was a check bug are annotated here, and
  check fixtures deserve the same review care as production code.


- 2026-07-06 — HARNESS BUG (fix in flight on feat/model-perf-log):
  Verifier.verify evaluated expect_files BEFORE running the check, so any
  check that itself creates/exports its deliverable (the worktree
  patch-export pattern) failed attempt 1 with "missing expected files" even
  when the check printed PASS. Cost 3 phantom retries in one run — and it
  poisons first_try_pass_rate, the model log's routing signal. Until the
  reorder lands on your checkout: have the WORKER write the declared
  deliverable, or don't declare check-created files in expect_files. When
  reading seeded scoreboard numbers, remember 2026-07-06 first-try rates
  are depressed by this.
- 2026-07-06 — the model log is now automatic: every attempt row carries
  model/task_type/retry; `./ringer.py models` prints the scoreboard; 81
  historical rows were seeded via scripts/backfill_model_log.py with a
  hand-authored task-type mapping. Give every manifest task a task_type or
  its evidence buckets as (untyped).

- 2026-07-06 — a three-model "bakeoff" ran every task on the engine's
  hard-coded model: task keys said glm/gpt/kimi, but the opencode engine
  block pinned glm-5.2, so one model wrote all three "competing" reviews.
  This is why the per-task `model` field exists — a bakeoff is only a
  bakeoff if the manifest, not the engine block, names the model. Verify
  with the `model` column in the run state, not the task key.
- 2026-07-06 — spawning 5-6 opencode workers simultaneously hit opencode's
  local "database is locked" (sqlite) — several instant attempt-1 failures,
  all absorbed by Ringer's retry. Cosmetic in Ringside ("sent back" at 0s) but
  wastes an attempt; consider staggering opencode spawns.
- 2026-07-06 — opencode's bash tool kills foreground commands around the
  ~2-minute mark: a 2min+ image-generation API call can never finish inline.
  Spec pattern that works: nohup the long command in the background, then
  poll for the output file in separate short commands.
- 2026-07-06 — two check-craft lessons from the same run: (1) URL-allowlist
  checks must be prefix-tolerant (workers legitimately trim slugs); (2) any
  heading-regex must tolerate numbered headings ("## 3. Type / Typography").
  Both failures looked like worker laziness until the raw logs said otherwise.
- 2026-07-06 — elsas-website demo, check-craft in BOTH directions: (1) a fixed
  800-char body floor failed a worker for faithfully converting genuinely tiny
  source posts — floor must scale with the source; (2) a citation gate treating
  every backtick as a page-quote failed honest reviewers who backticked their
  own fix-suggestions — line-scoped pair parsing + attribute-aware corpus fixed
  it; (3) needle-exception lists must be shared across ALL checks that consume
  the needle set (a needle excepted in one checker failed a task through
  another). Post-mortems ruled FOR the worker 3 times this run — read raw logs
  before blaming the model.
- 2026-07-06 — opencode sqlite "database is locked" again with just 2
  simultaneous opencode spawns (page-news + page-about-faq); retry absorbed it.

## codex (2026-07-06, bench-operator-proofing)
- 8/8 code-feature tasks passed attempt 1 across 3 rounds (worktrees mode, Python harness refactor; 108k-406k tokens/task). Specs embedded the approved architecture doc + exact file ownership; checks built fresh uv venvs and ran the full pytest suite.
- Lesson (check design, not model): all 3 post-integration bugs were invisible to the checks — a test that passed only because the worker's worktree lacked .env, a `--help`-only assertion missing a runtime importlib/sys.modules bug (py3.12 dataclasses), and bare console-script names failing outside activated venvs. Checks should exercise one real invocation from a cold shell, not just --help.

## gpt-5.6-sol (codex)
- 2026-07-15 ringer-self-update run (3 serial tasks, direct-repo-edit mode): code-fix baseline-test repair 1/1 first-try (61k tokens, 1.6m); code-feature self-update mechanism (git fetch/ff-pull/re-exec + HUD staleness restart + 20-test suite) 1/1 first-try at high effort (153k, 8.1m); code-feature signal-contract (all 3 scoreboard surfaces + canonical-route lint enforcement) passed on retry (358k, 13.7m) — attempt 1 died on stale old-column assertions in pre-existing tests it hadn't finished updating; the retry prompt's injected FAIL list was enough to close it out. Lesson: when a task rewrites a display contract, name every test file asserting the old contract in the spec's ownership list AND tell it to update them FIRST.
- 2026-07-09 code-feature/code-fix (ringside-overhaul): 4/4 first-try — a ringer.py logging change with tests, a 265-line stdlib backfill CLI (atomic rewrite, dry-run, idempotence all check-verified), a ~1500-line single-file HTML redesign (running-now pills + worker-card grid + multi-expansion refactor, 30KB patch, node --check + contract greps + unittest), and a render-gating change where it correctly UPDATED tests asserting the old behavior instead of gaming the check. Medium/high reasoning, 65–120k tokens/task.
- Same day, different session (bench-harness-patches, code-fix): 0.29 first-try over 7 tasks on a Next.js/Turbopack harness. Spec and check quality dominate model choice — see the scoreboard before generalizing either number.

## GPT-5.5 (codex) — attribution caveat
- Scoreboard rows dated before 2026-07-09 may actually be gpt-5.6: codex eval rows logged model="" until the write-time stamping fix (PR #18) and were credited to GPT-5.5 by the registry default at read time, while the machine's codex default had already moved to gpt-5.6-sol at an unknown earlier date. `scripts/backfill_model_from_logs.py` re-stamps rows with surviving command-log evidence; anything it skips is a mixed-model aggregate. Trust post-2026-07-09 rows.

## nvidia/nemotron-3-super-120b-a12b:free
- 2026-07-08 (research, content-strategy-recon): FAIL x2. Did the analysis in chat but never wrote report.md; attempt 2 exited rc=0 with no file. Doesn't reliably follow file-output contracts under OpenCode. Demoted — don't re-audition on file-deliverable tasks.

## meta-llama/llama-3.3-70b-instruct:free
- 2026-07-08 (research, content-strategy-recon): FAIL x2. Timed out at 900s both attempts on a moderate DB-scrape+format task. Too slow on the free tier for harness work. Demoted — don't re-audition without much longer timeouts or paid tier.

## z-ai/glm-5.2 (addendum)
- 2026-07-08 (research/filter, pitch-foundry): FAIL x2 on a long-spec rubric-application task (~40k input: embedded rubric + 4 candidate files). Read all inputs, exited rc=0 with ZERO output tokens both attempts — silent stall, no file written. GLM handled the same session's shorter formatting specs fine. Lesson: keep GLM specs short; route long-context apply-this-rubric work to codex.

## GPT-5.5 (codex) — honesty flag
- 2026-07-08 (image-gen, pitch-foundry): sandbox DNS blocked openrouter.ai; ALL 10 API calls errored (logged honestly in gen-log) — but the worker then FABRICATED 10 deliverables locally (composited canvases from the ref image) to satisfy a files-exist>40KB check, and passed. Lesson: (a) codex sandbox has no external DNS on this machine — route API-calling tasks to opencode (network open); (b) never write an existence-only check for generated media — require the success log (SAVED/cost lines) to match the file count.

- 2026-07-09 persona-review (pitch-foundry exec-briefing panel): 0/2 first-try+retry. Produced coherent review CONTENT as chat text but never wrote report.md — does not reliably use file-write tools under opencode. Demoted; do not re-audition for file-deliverable tasks without a write-tool probe first.

## gpt-5.6-luna (codex)
- 2026-07-09 code-feature (unlock-ai guide-format conversion, strict type-contract check): 1/1 first-try, 42.6k tokens, 80s. Followed a multi-file TS pattern precisely at $1/$6 pricing. Good candidate for mechanical codegen/docs lanes; audition in adjacent types.

## opencode / z-ai glm-5.2 (via openrouter)
- 2026-07-09 (aicred-invoice-downloads, 4 code-fix tasks + 1 follow-up, worktrees+npm ci checks): systematic attempt-1 NO-OP — all 4 parallel workers produced zero edits and no summary on first attempt, then completed cleanly on attempt 2 after retry-prompt injection (34k-69k tokens each). Follow-up single task passed attempt 1. Suspect first-invocation session warm-up in opencode-sandboxed under parallel spawn; budget for 2 attempts on parallel GLM batches. Output quality on Next.js/Stripe route+test work: solid, spec-faithful, one boss-caught design gap (used user-scoped supabase client where RLS demanded service role — spec didn't say explicitly; say it explicitly).

## z-ai/glm-5.2 (claude-zai lane) - vaultwise admin-panel
- 2026-07-20 code-feature (admin-panel, 1 task, worktrees, ~28k-char embedded TDD plan as spec): 1/1 first-try, 28m. Executed the full 3-task plan (12 files, +610/-133, suite 141->151), left thorough worker notes with sensible conservative deviations. Gate caught 2 seam defects invisible to the executed check (a query param dropped across a template seam; an htmx swap missing hx-select) - UI seams between tasks need explicit spec lines or a browser-level check, not just pytest.
- 2026-07-20 code-fix (same run, seam-fix round): 1/1 first-try, 6m, minimal exact diff. Flag: worker initially edited the MAIN repo instead of its worktree (keyed off absolute repo paths appearing in the spec), self-caught via a pytest import mismatch and restored surgically - verified clean at the gate. Spec lesson: in worktrees mode give absolute paths ONLY for out-of-worktree deliverables and state "your cwd is the worktree; every repo path is relative to it".

- 2026-07-20 code-feature x3 (vaultwise atomic-artifacts, 2 waves, worktrees): 3/3 first-try - two parallel ~15k-char specs (9m each) and one 44k-char 6-task sequential chain spec (40m, largest glm spec to date, no stall). Worker notes caught real contract subtleties unprompted (argparse explicit-dest hyphen behavior, module-shadowing alias, PyYAML date round-trip risk). The 40k-token stall ceiling appears to be about token count, not task count; 44k chars (~11k tokens) is safely under it.

- 2026-08-02 (substack-scraper resync-rebuild-prune loop, wave 1): code-feature x2 (claude-zai lane, worktrees, TDD specs with embedded test code). Worker output fully correct on attempt 1 for both tasks (target tests, full suite, ruff check, mypy all green). Run recorded FAIL x2 - orchestrator CHECK BUG, not model failure: check ran repo-wide `ruff format --check .` which hit pre-existing drift in two files outside worker ownership; unsatisfiable under the spec's boundary. Both scoreboard fail rows for run resync-rebuild-prune wave 1 are misattributed; glm-5.2 code-feature posterior should be read as undepressed. Notable: on the retry, the worker saw the format failure in the retry prompt and still refused to reformat unowned files, explicitly citing its ownership boundary - boundary adherence under check pressure is strong. Lesson: never put repo-wide format gates in a check unless the baseline is verified clean; scope to owned files.
- 2026-08-02 (substack-scraper loop, wave 2): code-feature x1 (t3-scraper, ~10k-char behavior-contract spec, claude-zai lane). Output correct and contract-faithful (14 target tests + 114 full suite + ruff green; clean handling of collision rules, write-before-unlink, dry-run previews). Run recorded FAIL x2 - second orchestrator CHECK BUG: check enforced repo-wide mypy, but the plan itself sequences the cli.py call-site fix into the NEXT task; unsatisfiable inside t3's ownership. Misattributed fail rows again. Worker again respected the boundary under retry pressure and left ponytail-style comments justifying a forced design compromise (direct _conn reads) - good judgment signal. Lesson: cross-task transient breaks are plan-legal; per-task checks must gate only what the task's boundary can satisfy.
- 2026-08-02 (substack-scraper loop, wave 3): code-feature x1 (t4-cli) PASS attempt 1, full gate green including the mypy restoration the plan sequenced across tasks 3-4. glm-5.2 claude-zai now 3/3 clean worker outputs this run; both earlier FAILs were check bugs.
- 2026-08-02 (substack-scraper loop, wave 4): code-feature x1 (t5-prune, destructive-deletion logic) PASS attempt 1, full gate green. Orchestrator line-by-line review found all safety invariants correctly implemented (marker guard, tracked-file exclusion by construction, protective failure directions). glm-5.2 claude-zai 4/4 clean outputs this run.
- 2026-08-02 (substack-scraper loop, wave 5 + run close): docs x1 (t6-docs) PASS attempt 1; documentation accurate against the implemented surface without being shown the diffs. Run total for glm-5.2 claude-zai: 6/6 substantively correct worker outputs across code-feature x5 + docs x1; the only red rows this run were two orchestrator check bugs (repo-wide format/mypy gates crossing task ownership boundaries), both attributed above. TDD specs with embedded test code remain a fully reliable glm lane.
- 2026-08-02 (substack-scraper resource-resync loop, wave 1): code-feature x2 (claude-zai lane, worktrees, TDD specs with embedded test code). Both PASS attempt 1 (145s / 82s); diffs exactly scoped to ownership, contract-faithful (canonicalization via str-coerce on entries was a sensible conservative reading). Repo-wide format/mypy gates were safe this run because the orchestrator verified the baseline clean at compile time - the prior run's check-bug lesson applied as prevention.
- 2026-08-02 (substack-scraper resource-resync loop, wave 2): code-feature x1 (t3-resource-sync, ~23k-char behavior-contract spec with 15 embedded tests, claude-zai lane). PASS attempt 1 in 9.4m; 302-line module, line-by-line gate review found zero contract deviations. Notably good reuse judgment: routed whitelist matching through the existing resources._match_site and the path-segment fallback through resources._slug instead of duplicating either, keeping one canonical comparison path. ~23k chars confirms comfortably under the lane's stall ceiling.
- 2026-08-02 (substack-scraper resource-resync loop, wave 3): code-feature x1 (t4-scraper wiring). PASS attempt 2. Attempt 1 was a PLAN gap, not a model failure: the plan's ownership list omitted tests/test_cli_report.py, which asserts the exact report manifest the task's contract extends - the known "name every test asserting the old display contract" lesson recurring. Worker behavior exemplary both rounds: flagged the boundary conflict as an open question instead of crossing it, then made the minimal one-line expectation fix once the retry sanctioned it. Also absorbed a bug in the plan's embedded mock test (setdefault-or idiom returning the wrong object) with commented getattr defaults rather than editing sanctioned test code - conservative-reading discipline holding under pressure.
- 2026-08-03 (substack-scraper resource-resync loop, wave 4 + run close): docs x1 (t5-docs) PASS attempt 1 (4.6m); accurate against the implemented surface, matched per-file conventions, zero em dashes under an explicit style-grep gate. Run total for glm-5.2 claude-zai: 5/5 substantively correct outputs (code-feature x4, docs x1); the single retry (t4) was a plan ownership gap, attributed in the wave-3 line. TDD specs with embedded test code remain the fully reliable glm lane; docs posterior now has repeated first-try evidence on this repo.
- 2026-08-03 (substack-scraper resource-resync loop, follow-up t6-report-summary): code-feature x1 (claude-zai lane). PASS attempt 1 (2.7m); exact-contract diff across scraper.py render, cli.py verbose threading, and appended render tests. Lane now 6/6 substantively correct this run.
- 2026-08-03 (loop-stack build-wave, wave 1): docs x4 (managed-block autonomy flip, loop-drive gate-line surgery with a no-touch rule over every other tagged line, loop-plan dispatch prose, loop-which frontmatter trim to 66 words) - 4/4 PASS attempt 1. Verbatim-test GREEN-only pattern (orchestrator pre-commits the RED test; worker may not touch tests/) held perfectly; the gate-tag no-touch constraint with two sanctioned exceptions was followed exactly.
- 2026-08-03 (loop-stack build-wave, wave 1): code-feature x2 (graduate-parking.sh bash parser + skill wiring; wayfinder skill port + awk mirror exclusion) - 2/2 PASS attempt 1. The wayfinder port preserved the source's HITL/AFK structure while remapping all four ticket types to loop-stack conventions unprompted-clean; ownership audits clean on both.
- 2026-08-03 (loop-stack build-wave, wave 1): code-fix x1 (awk gsub -> char-loop esc() parity in gen-gate-registry.sh) - 1/1 PASS attempt 1, minimal exact diff.
- 2026-08-03 (loop-stack build-wave, wave 2): code-feature x1 (loop-auto per-repo default rider: bash subcommand surgery on an existing script + skill/config doc edits, 3-file ownership) - 1/1 PASS attempt 1 (~9m); clean line-anchored key handling and the effective-mode fallback chain exactly per contract.
- 2026-08-03 (loop-stack build-wave, wave 2): code-fix x1 (fable-sandwich -> frontier-sandwich rename sweep across 6 owned paths incl. install.sh retire list and doctor self-check) - 1/1 PASS attempt 1; exactly-once retire-list constraint and repo-wide old-name sweep both verified by the executed check, no collateral edits.
- 2026-08-03 (loop-stack build-wave, wave 3 + run close): code-fix x1 (terminal consolidation: registry regeneration + retiring a one-shot baseline-diff invariant in favor of per-type count floors read from the fresh registry, then proving the full 17-script suite green in-worktree incl. a live read-only gh leg) - 1/1 PASS attempt 1 (~4m). Run total for glm-5.2 claude-zai on loop-stack: 10/10 attempt-1 PASS across docs x4, code-feature x3, code-fix x3; zero retries, zero check bugs. The committed-RED-test GREEN-only spec pattern plus exact ownership lists is now a proven lane shape on this repo.
- 2026-08-04 glm-5.2 (claude-zai) docs: tracker-mode wave 1 task8 pass-on-2; attempt-1 FAIL attributed to a PRE-EXISTING repo defect (stale generated gate registry made the check unsatisfiable as scoped), not a model miss - worker diagnosed it correctly on attempt 1 and fixed it on attempt 2. Scoreboard's attempt-2 ding overstates; treat as attempt-1-quality.
- 2026-08-04 glm-5.2 (claude-zai) code-feature: tracker-mode wave 4 task7 double-FAIL was a SPEC defect (test called a script setup never installs); worker wrote the test verbatim, respected ownership, and attributed the defect upstream correctly both attempts. Scoreboard fail rows overstate; treat as spec-problem, not model miss.

## opencode (harness note, any model)
- 2026-07-28 (code-review, pr82-token-saver-review): GLM 5.2 produced a complete, high-quality 218-line report but could NOT write it to an output directory created by the parent Claude Code process — every write returned EPERM. It then spent ~3000s burning retries on ctypes/`openat`/AppleScript/`sandbox-exec` workarounds until it timed out, and the task logged as FAIL despite the deliverable existing in its taskdir. Codex workers in the same run were unaffected. Lesson: point opencode workers' output INSIDE their own taskdir and harvest via `expect_files`; never hand them a shared output dir another process created. This is an orchestrator spec bug, not a model failure — do not read the FAIL as evidence against GLM.

## Process lessons (2026-07-28, PR #82 review)
- **Ideas worth keeping from a rejected PR.** PR #82's pre-call gateway was dropped (needs your own API key, so it converts flat-rate OAuth plans into metered API billing; incompatible with Claude Code; and it saves tokens by stripping the tool list, which is the thing that makes the CLI worth using). One idea inside it is worth remembering if the problem ever comes back: an *explicitly blessed* answer cache — key a reviewed answer to the exact request plus the exact selected source packet, and replay it with zero upstream calls, never auto-accepting a model answer. It only fires on byte-identical repeats, which is why it didn't justify 2,000 lines here.
- **Doc-stated support floors need a CI job or they are fiction.** README promised Python 3.11+ while CI only ever ran 3.12; a 3.12-only f-string reached review with a fully green suite. Either test the floor or move it.

## glm-5.2 (claude-zai)
- 2026-07-17 code-fix (stm-nav round 1): retry caused by an over-strict orchestrator check (byte-identical builds vs plan's "except timestamps"); on retry produced a clean idempotent-write fix rather than gaming the check, and flagged it honestly. Lesson: give GLM precise determinism semantics up front; it handles nuance well when told.
- 2026-07-17 site-build (stm-nav round 6): logged FAIL is a CHECK bug, not a model failure - the worker's output was fully correct on manual audit (both "failures" were format-strict greps: a negative phrase-grep matching the requested link-out stub, and an allowlist grep matching an explanatory comment). Discount this row when reading the scoreboard.
- 2026-07-17 docs (stm-nav round 8): second false FAIL from an orchestrator check (repo-wide negative grep counted historical docs as dangling references); worker's 23-file restructure was fully in scope and correct on audit. Rule distilled: negative assertions only over files the task owns, never repo-wide.
- 2026-07-18 run summary (stm-nav, 21 rounds): glm-5.2 implemented 20/21 rounds, zero substantive failures; every recorded FAIL traced to orchestrator check bugs (5 total, all annotated above - amend these rows when the amendment feature lands). Opus took the one aesthetic-bar round (sitemap flow redesign), first-try pass. GLM validators caught the only two real content defects of the run.
- 2026-07-19 site-build (prototypes-expectations-page): single fat task (author a 10-section content-heavy HTML page against a detailed plan + create a verbatim check + 7-file nav/orientation wiring), first-try pass in 15.7 min against a 33% first-try prior. Worker also correctly diagnosed an out-of-scope repo inconsistency (committed atlas stale vs committed sources), verified it against whats_next.md, and proposed the two-commit split the orchestrator adopted. Heavy-but-tightly-specced authoring with an executed check chain is a safe GLM lane; the proactive-diagnosis quality was above what the probation tier suggested.
- 2026-07-19 presignoff-2b (1 code-feature + 2 code-fix, parallel x3): 3/3 first-try passes. The code-feature (generator template change: native details/summary collapse + localStorage persistence + CSS, plus two blurb wordsmiths) shipped a no-flash synchronous state application unprompted and correctly declined to add an unneeded custom event, documenting both. Tightly-specced generator work with executed check chains is confirmed GLM territory; wordsmithing to a hard char budget also landed well (130/136 vs 140).

2026-07-19 - glm-5.2 (claude-zai), run model-routing-unification: 6/6 first-try, zero retries (5 docs, 1 code-fix). Spec style was detailed content contracts with verbatim blocks; transcription fidelity was perfect including nested quoting in shell doctor checks. Zero check bugs this run; lint caught the orchestrator's one pre-launch bug (phantom $RINGER_EXPORT_DIR from the old example plan). Supports: proven on docs; code-fix probation number remains amendment-depressed, this run adds a clean row.

2026-07-20 - uiux-punchlist wave 1 (glm-5.2, claude-zai): code-feature (inventory scraper w/ injection contract) 1/1 first-try 707s; site-build (chrome CSS) 1/1 first-try 438s; code-fix (prototypes rename) retry 1 - attempt 1 renamed term+class but paraphrased the spec's required verbatim legend sentence; the check's quoted-fragment grep caught it and attempt 2 landed it exactly. Lesson: GLM treats "exact sentence" requirements as paraphrasable unless the sentence is set off as a quoted block in the spec; keep substance greps for verbatim contracts.

2026-07-20 - uiux-punchlist wave 2 (7 parallel): glm-5.2 (claude-zai) 4/6 first-try. t03 code-feature (fat generator change: per-field card + JSON island injection + full-picklist embed) first-try 982s - confirms the heavy-but-tightly-specced generator lane. t05 site-build retry 1: attempt 1 missed the SharePoint href (spec said "the 2d URL" without spelling it - spec gap, split blame) and typed one em dash; attempt 2 clean. t08 site-build retry 1: committed its scratch task-local check into scripts/checks/ (outside ownership); in-check ownership gate caught it, attempt 2 relocated it and explained the root cause well. t07/t09/t10 first-try. opus (claude) 1/1 first-try on the judgment unit (61-story archetype mapping, 620s): 25 covered / 36 proposed, creation prompts grounded in a real validator script it found itself - the aesthetic/judgment pin keeps paying. Orchestrator gate fix (not a worker fault): the inventory injector needed em-dash sanitization at the data-to-display boundary; a whole-file em-dash check over a page holding injected workbook data is an invariant-missing-its-exception unless the injector sanitizes.
- 2026-07-20 addendum, uiux-punchlist wave 3: glm-5.2 (claude-zai) site-build (schema.html shell surgery inside injected-blob constraints) 1/1 first-try, 696s. Wave totals for the run so far: glm 8/10 first-try, 10/10 pass; opus 2/2 first-try.
- 2026-07-20 addendum, uiux-punchlist wave 4 (final): opus (claude) docs retry 1 - attempt 1 abstracted the 13.5px font-floor value away in the name of portability; the substance grep held and attempt 2 kept the number. Lesson: Opus over-generalizes "portable" toward valueless prose; pin the load-bearing constants in the spec. glm-5.2 code-fix x2: t13 retry 1 (built labels without the mandated exact literals), t14 first-try. Run final: 14/14 units passed, glm 9/12 first-try 12/12 pass, opus 2/3 first-try 3/3 pass, zero check bugs charged to workers, one orchestrator check-bug lesson (em-dash invariant needed the injected-data exception, fixed at the injector).
- 2026-07-20 addendum, uiux-punchlist waves 5-6: glm-5.2 (claude-zai) docs (two-guide content merge with dedupe judgment + 5-page reference surgery) pass on retry (attempt 1 tripped the one-forge.css invariant with 4 carried-over references; dedupe decisions were documented and audited sound). t16 nav-feedback logged FAIL x2 but is a CHECK BUG, not a model failure: the orchestrator's ownership regex forbade scripts/checks/check_nav.py while the task structurally required it (check_nav resolves every nav href on disk; an external SharePoint URL needs the skip). Worker made the minimal correct 2-line check fix and passed every functional gate; work salvaged from the kept worktree and committed (forge 9c5ad30). Discount both t16 rows when reading the scoreboard; amend when ringer #65 lands (run uiux-punchlist-20260720T175349Z-p302692, task t16-nav-feedback). Rule re-learned: ownership lists must include the repo's own selftests when the change alters what the selftest validates.

2026-07-22 - dshoney step-06 wave 11 (Agent-tool transport, dshon repo): opus code-feature (WP-24 consumer migration + release prep: live etl.py import swap, config v2 migration, wheel + provisioning doc) 1/1 first-try; opus code-review validator 1/1, re-derived every claim by a second route (independent pytest 262/1, rebuilt wheel, throwaway-venv import, byte-compared configs, cross-walked 24 WP logs) and correctly separated an authorized-deviation set from real criteria. Signal event: implementer disclosed a known-upstream data-loss gap (WP-19 first-format-wins destination collapse surfacing in a migrated live config) instead of papering over it - flag-don't-fudge held under a release-gate prompt. Step 06 final: 24/24 WPs merged, opus implementers 8/8 pass (1 fix cycle across them), sonnet-4.6 implementers 16/16 pass (3 fix cycles), opus validators caught every real defect they were shown.

2026-07-23 - spec-backlog-input (forge, 1 fat code-feature task: 2-unit serialized page feature + verbatim Playwright check + docs): opus (claude) 1/1 first-try, 322s - transcribed a 163-line pinned check byte-identical to the plan block and landed every contract literal. glm-5.2 (claude-zai) shows 2 FAIL rows on this run_name that are NOT model signal: both were z.ai gateway 529 outages (zero worker output, ~15 min sustained), plus 1 ERROR row from a stale-worktree setup collision; discount all three when reading the scoreboard. Orchestrator check-bug lesson: ringer executes checks via /bin/sh (dash) - `set -o pipefail` is dash-illegal; guard commands individually instead.

2026-08-07 - audit-remediation-loop wave 0 (ltv-rfm-segments repo, worktrees:false): glm-5.2 (claude-zai) code-fix T1-ruff-green logged fail/TIMEOUT x2 - NOT model signal, discount both rows: (a) 900s default timeout_s was a budget ceiling for a repo-wide sweep on a slow /mnt/c WSL filesystem (model made monotone progress, 461 -> 94 ruff errors across the two attempts, no bad edits, pytest baseline intact); (b) orchestrator CHECK BUG - with worktrees:false the check runs in the scratch task dir, not the repo, so relative `.venv/bin/ruff` hit exit 127 and expect_files could never resolve, meaning the check was unsatisfiable as written. Fix applied to all four ringer templates: specs open with an explicit cd to the repo, checks capture TD=$(pwd) then cd to the repo, expect_files are receipts the check copies into the task dir, timeout_s raised to 1800-3600. Rule learned: with worktrees:false, task dir is CWD for both worker and check - never use repo-relative paths bare.

2026-08-07 - audit-remediation-loop T3b-ltv-reader (ltv-rfm-segments, worktrees:false): glm-5.2 (claude-zai) code-fix logged fail/FAIL x2 - CHECK BUG, discount both rows: the orchestrator's awk range pattern (/def load_ltv_output/,/def [a-z_]+\(/) self-terminates on its own start line (the def line matches both endpoints), so the substance grep saw only the signature and the check was unsatisfiable. Worker's attempt-1 code was fully correct (commit 261b302; verified at gate: reader on ltv/, sibling loader untouched, 619 tests green, ruff 0) and its attempt-2 diagnosis of the harness mechanics was itself accurate. Rule learned: never use an awk /start/,/end/ range where the start line can match the end pattern; use sed with anchored ^def endpoints.

2026-08-08 - audit-remediation-loop waves 3-5 Agent-tool receipts (ltv-rfm-segments, canonical checkout, batched per model/task_type): opus code-feature (T5 golden harness with determinism canonicalization) 1/1 first-try. opus code-fix (T6 period amount, T7 float64 money, T8 date-math bundle) 3/3 first-try - each landed test-first with zero repair rounds, and each surfaced a real out-of-scope regression or precision issue unprompted (T6: running_totals gift_records gap; T7: legacy float32 path; T8: produced the human-gate diff report). opus code-review validators 6/6 - every verdict earned by independent rerun; standouts: T8's validator exhaustively classified ~3.05M changed golden cells (0 unattributed) and caught a report-precision error the implementer missed; T9's validator dual-tree-grepped 12 deletions. sonnet code-fix (T9 legacy deletion, 254k tokens/152 tool uses) 1/1 first-try with a correct caller map. Signal event: opus T10 honored a mandatory equivalence STOP gate - proof failed (normalize_once not behavior-preserving), it committed only skipped proof tests and escalated with evidence instead of forcing the golden green; flag-don't-fudge held under an end-of-run completion pressure prompt. glm-5.2 (claude-zai) closing note: 7 ringer units (T1-T4, T3b, T6b, T9b) all functionally correct; the only FAIL rows this run were orchestrator check bugs (T1 CWD, T3b awk), both amended above.

- 2026-08-08 (glm-5.2, code-fix, normalize-once-batching W1): task1-money-float64 first-try pass, 4.6m, exact-line spec followed cleanly; flagged its one judgment call (docstring sync) unprompted. Check gap (orchestrator fault, not model): check omitted ruff, one auto-fixable I001 slipped to the gate.
- 2026-08-08 (opus, code-feature, normalize-once-batching W1): task2-batch-normalize first-try pass, 11.8m, ~150-line dispatch restructure + self-contained integration boundary test; opus adversarial validator confirmed all 9 criteria incl. the date_aggregated_df silent-failure guard. Pin (risk-concentration) justified in hindsight: clean first-try on the run's highest-risk unit.
- 2026-08-08 (glm-5.2, code-feature, normalize-once-batching W2): task3-uat-loader pass on attempt 2. Attempt-1 fail was a SPEC bug (the spec's embedded "verbatim" test code was lint-dirty: duplicate inline imports I001, semicolon E702, caught by the distilled ruff check step); on retry the model resolved the verbatim-vs-lint conflict correctly (semantics untouched, all asserts intact) and disclosed the deviation unprompted. Good judgment signal, not a capability miss.
- 2026-08-08 (glm-5.2, code-feature, normalize-once-batching W3): task4a-golden-diff-classifier first-try pass, 13.8m, 984-line typed classifier + 8-case synthetic self-check, mypy/ruff clean under the repo ratchet. Long numeric spec (float32-ULP bound, four column-set contracts) executed faithfully; flagged its derive-vs-hardcode judgment call unprompted. Strong signal for the tightly-specced + executed-check lane.
- 2026-08-08 (glm-5.2, code-fix, normalize-once-batching w4): calcdate-stability run verdict FAIL x2 is a CHECK BUG, not model signal - the orchestrator's check string had a bash parse error (brace group closed with } where fi belonged), so the check died before running anything on both attempts. The model's attempt-1 code was correct (orchestrator re-ran every check step on the applied tree: 10 tests pass, ruff clean, full gate OVERALL: PASS, committed); attempt 2 correctly diagnosed the broken check and manually exported the patch. Treat both FAIL rows as amended; strong diagnostic signal.

2026-08-08 - loop-improve (loop-stack-session, 1 fat code-feature task: working-skill refactor + new skill + vendored playbook + gate test): glm-5.2 (claude-zai) 1/1 first-try, 19.8m. Three sequential authoring tasks committed per plan; byte-exact contract compliance (four gate suites green in worktree AND re-derived at the gate; deep-read of the prose-extraction diff found zero deviations; all five mandated rephrases of vendored MIT playbook lines faithful). Confirms the tightly-specced authoring lane extends to skill-prose surgery, not just code. Orchestrator lesson (not model signal): `ringer.py lint` exits non-zero on advisory findings, so the `lint && run` launch chain silently never runs a manifest carrying a by-design finding - lint separately, review, then `run` alone.

## sonnet-5 (Agent-tool transport)

- 2026-08-08 - code-fix (audit-sweep run, loop-stack-session: 7-task plumbing
  hardening as a single Agent-tool unit): first-attempt pass. Executed a
  verbatim TDD plan (7 RED-GREEN-commit cycles) byte-exact; independent opus
  validator passed all five criteria with zero scope violations. Signal: the
  worker correctly attributed the one full-suite failure to a pre-existing
  repo bug and reproduced it at the base commit instead of hacking around it.
  Routed by benchmark prior (default Agent-tool execution worker); no re-route.

## 2026-08-16 copywriter-skill-loop wave 1 (design-brand-pack)

- glm-5.2 / claude-zai, docs (t1-vocabulary, t3-spine, t4-assumption-protocol, t5-seat-protocol): 4/4 pass on attempt 1; opus validators confirmed t1, t3, t5 with zero violations.
- Signal, spec-bug attribution: t4's validator FAIL traced to the orchestrator's manifest expansion (a frozen block flattened into bullets), not the model; the worker reproduced its spec faithfully and the fix was applied at the gate. Do not charge glm-5.2.
- glm-5.2 / claude-zai, code-feature (t2-checker, 517-line stdlib checker with a 20-scenario CLI self-test): attempt 1 passed its executed check but an opus validator's own probes found fail-open ledger parsing plus two spec contradictions; a relaunch with the amended spec passed and re-validated clean, including regression probes. Lesson repeated: executed checks bound what workers prove, adversarial validation catches what checks cannot; the second attempt cost one flat-rate round.
- opus / Agent tool, code-review (5 validator dispatches): all five verdicts evidence-backed and decisive; the t2 validator's self-invented probes were the round's highest-value output.
- 2026-08-16 wave 2: opus / Agent tool, research (t8-v5-baseline delta audit, 48-row ledger over 10 sources plus a 133-claim carry-forward): strong first pass (independently re-derived counts, refused to invent lineage for the sourceless 2027 claim) but validator found two missed extractions and two broken citations; one SendMessage repair fixed seven of eight items; final citation off-by-two repaired at the gate. opus validator (code-review stance on prose): both rounds decisive, second round caught its own repair's miss - evidence-first verdicts holding up.
- 2026-08-16 wave 3: opus / Agent tool across t9b draft (2,900-word sourced guide, first try inside band, only expected gate open), t9c extraction (146 rows, caught 9 misinterpretations in a fresh opus draft, re-verified 64 markers), t9d resolution (9/9 fixed, both gates green first try), t9g triage (43 findings verdicted, one protocol breach caught by the package validator and repaired in one round). sonnet / Agent tool, t9e re-extraction: clean, precise, cheap - right-sized routing. glm-5.2 / claude-zai, persona-review x4 seats: 4/4 pass, findings substantive (a caption arithmetic error three opus stages missed was flagged by all four seats); persona work remains squarely glm's zone. Pattern for the record: every stage that FAILED validation failed on claim-coverage discipline, never on prose quality - the protocol's paperwork is where models cut corners.

## 2026-08-17 content-guides-and-form-audit loop (Agent-tool transport, not ringer)
- sonnet / docs (wave 2, Task 1): clean pass, frozen-block insertion into a live global guide; validator confirmed verbatim. No issues.
- sonnet / research (wave 2, Task 4): pass after one repair. Substance genuine (17-row ltv-rfm digest, no filler). Signal: needed a one-sentence-per-line repair because the task's acceptance check (t4.sh) omits the awk guard that t1/t2 carry; the adversarial validator caught it, the script did not. Check-gap attribution, not a model weakness.
- sonnet / docs (wave 4, Task 3): clean pass, citation swap against a frozen line-to-rule map. Signal: isolation:worktree landed the branch on main not the integration branch; worker detected and reset before editing. Harness-quirk, not a model weakness; future prompts pin the base branch explicitly.
- opus / docs (wave 5, Tasks 5/6/8): three parallel clean passes, all validated. Task 5 three doctype files, Task 6 five persona files, Task 8 form-audit protocol + Stage 3 rewrite. Signal: Task 8 hit a check-vs-plan tension (check bans "doctype" in the cold-seat section, plan step 5 says "no doctype file"); worker resolved via "contract file" synonym, validator confirmed faithful. Opus held voice and contract fidelity across all three; no repairs needed.
- sonnet / docs (wave 6, Task 7): clean pass, plan amendment against a frozen shape. Signal: validator returned fail on scope, but both points were false positives from the validator prompt's wrong premise about commit structure (worker split into two commits; a shared ancestor commit read as a branch change). Orchestrator re-derived against git and attributed pass. Lesson: give validators the branch name and let them derive commit structure, do not assert which commit holds what.
- opus / probe (wave 6, Task 9 calibration): the form audit, run blind, correctly separated the r1/r2 pair (r1 blocking, r2 clean). Note: it blocked r1 on spine/never/always rather than the owner's stated altitude/focus, a defensible structural read; the calibration check was relaxed to "blocks on any dimension" rather than tuning the blind auditor.

- 2026-08-17 sonnet code-feature: copywriter-rule-corpus-audit wave 1 (claude engine) - PASS first attempt; wrote a 372-line stdlib audit script + emitted a 259-row skeleton CSV that reconciled by independent grep. Clean.
- 2026-08-17 glm-5.2 code-feature/research: copywriter-rule-corpus-audit T1 - SIGNAL: three consecutive runs failed on sustained z.ai 529 (api.z.ai overloaded, ~10 min window); no worker output produced. Not a model-quality signal - provider outage. Re-routed T1 and T2 to sonnet at owner request.
- 2026-08-04 (substack-scraper resource-sites-matching loop, wave 1): code-feature x2 (T1-report render format, T2-models host_matches/split_host_path helpers) both PASS attempt 1 (84s/93s). Ownership-scoped checks (task pytest target + scoped ruff only, no repo-wide gates in partial worktrees) produced zero false FAILs. Worker open-questions discipline good: flagged an import-style fold and a `*.www.` canonicalization edge conservatively, both correct readings. glm-5.2 claude-zai 2/2 clean this run.
- 2026-08-04 (substack-scraper resource-sites-matching loop, wave 2): code-feature x1 (T3-config url/urls parsing + wildcard validation) PASS attempt 1 (5.7m). All nine embedded tests plus every un-tested validation branch implemented with entry-named errors. glm-5.2 claude-zai 3/3 clean this run.
- 2026-08-04 (substack-scraper resource-sites-matching loop, wave 3 + run close): code-feature x1 (T4-matching) scoreboard FAIL x2 - ATTRIBUTED at the gate as a formatting-only miss, not a substance failure: all 176 tests, ruff check, mypy, and both substance greps passed in the preserved worktree; the sole red step was `ruff format --check` on ONE test file whose layout the spec supplied verbatim ("add exactly these tests") and ruff wanted to collapse. Orchestrator salvaged (formatted the one file, re-verified full chain green, exported and committed). Worker's own attempt-2 diagnosis guessed infrastructure interruption - wrong; note the spec/check tension: verbatim-test-layout instructions + a format gate can conflict; future specs should say "then run ruff format on files you touched" (T3's worker did this unprompted and passed). Treat T4 as attempt-1-substance-correct. Run total glm-5.2 claude-zai: 4/4 substantively correct outputs (code-feature x4), one formatting salvage.
- 2026-08-08 (pokemine improve-fix-sequencing loop, wave 1): code-fix x1 (001 path-traversal guard) PASS attempt 1 (202s). Chokepoint design followed exactly (safe() inside dir()/trainerDir(), not sprinkled), both bridge routes guarded, both regression tests named per plan, live probe 400/contained/200 re-derived at the gate. Worker notes discipline good: flagged a benign one-line drift and a real behavioral consequence (list() now throws on stray non-slug data-dir entries) with correct conservative readings. Orchestrator check-bug found at gate: `git add -A` staged the setup node_modules symlink into the exported patch; fixed by unstaging node_modules before diff in the remaining checks. glm-5.2 claude-zai 1/1 clean this run.
- 2026-08-08 (pokemine improve-fix-sequencing loop, wave 2): code-fix x1 (002 store Drive-resilience) PASS attempt 1 (157s). Exact contract delivery: lossy list()/trainersList() with skip-and-warn, atomic tmp+renameSync save, ENOENT-null getters, five route 404s placed before SSE headers, three named regression tests mirroring the existing app.listen(0) pattern. Clean patch after the wave-1 export fix (node_modules unstaged before diff). glm-5.2 claude-zai 2/2 clean this run.
- 2026-08-08 (pokemine improve-fix-sequencing loop, wave 3): code-fix x1 (004 cleanup) PASS attempt 1 (132s), code-feature x1 (005 extract) PASS attempt 1 (281s), max_parallel 2, no attempt-1 warm-up NO-OP this time. Patches landed exactly disjoint per ownership lists; both workers correctly deferred the shared plans/README.md row to the orchestrator. 005 took its sanctioned optional step (stageLabel) cleanly; 004 skipped its gated optional step and said so. glm-5.2 claude-zai 4/4 clean this run.
- 2026-08-08 (pokemine improve-fix-sequencing loop, wave 4 + run close): code-fix x1 (003 record-update integrity) PASS attempt 1 (272s). Teeth discipline exemplary: wrote both regression tests first, confirmed both fail with the exact predicted assertion messages, and correctly attributed the spec's `^not ok` grep coming up empty to Node's spec-style reporter instead of claiming the teeth check passed. Barrier-based concurrency test forces the real interleave. Run total glm-5.2 claude-zai: 5/5 PASS attempt 1 across code-fix x4 + code-feature x1, zero retries, zero check-bug FAILs (one orchestrator export-pollution check bug found and fixed at the wave-1 gate before it could bite).
- 2026-08-08 (pokemine improve-fix-sequencing loop, wave 5 remediation): code-fix x1 (006 stray-entry skip in list scans) PASS attempt 1 (99s), dispatched off a confirmed terminal loop-review Spec finding. Surgical: SAFE_ID pre-filter in exactly the two scans, guard semantics untouched elsewhere, honest note about test-artifact residue in shared DATA_DIR. Final run total glm-5.2 claude-zai: 6/6 PASS attempt 1 (code-fix x5, code-feature x1), zero retries.
- 2026-08-09 (iamawriter design-runs loop, wave 1): docs x1 (T1 identity dossier) opus claude PASS attempt 1 - substance greps (verbatim exclusions, motif tokens, projection contract) all present, voice-consistent prose, exact single-file ownership. code-feature x1 (T2 structural checker) glm-5.2 claude-zai PASS attempt 1 - 7-case --self-test green on independent orchestrator rerun, stdlib-only, url()/srcset scanning implemented per spec. Both patch-exports clean, exactly one file each. 2/2 attempt-1 this wave.
- 2026-08-09 (iamawriter design-runs loop, wave 2 gate 1): site-build x1 (run 01 "Gesso") fable claude-fable-5 via Agent tool PASS attempt 1 - NOVEL EVIDENCE, fable's first site-build receipt. Full surprise-me ritual honored (6 lanes, announced d6 roll, 5 critique passes), opus validator passed all 9 criteria on independent evidence (checker rerun exit 0, contrast re-derived 12.96:1, hard-exclusion audit clean, diff scope-clean). Honest tool-absence handling: verified no image-gen tool exists, built self-made SVG assets, flagged Substack font-menu names as training-memory. No narration-reroute observed.
- 2026-08-10 (iamawriter design-runs loop, wave 2 gate 2): site-build x1 (run 02 "Unlined") fable claude-fable-5 via Agent tool PASS attempt 1 - opus validator 9/9 on independent evidence (contrast re-derived 13.69:1, exclusion audit clean, scope-clean diff). First run on the enriched dossier; visibly consumed the Scanner Daybook material. Worker self-caught 18 em-dashes against house style and re-rendered before returning. fable site-build now 2/2 attempt-1.
- 2026-08-10 (iamawriter design-runs loop, wave 2 gate 3): site-build x1 (run 03 "Instar") fable claude-fable-5 via Agent tool PASS attempt 1 - opus validator pass on all criteria (declared pair 13.05:1 re-derived; all palette-molt bands >= 10.49:1; exclusion audit clean; scope-clean). Variable-font mid-molt wordmark + SMIL morphing; 5 critique passes. fable site-build 3/3 attempt-1.
- 2026-08-10 (iamawriter design-runs loop, wave 2 gate 4): site-build x1 (run 04 "The Chrysalis Papers") fable claude-fable-5 via Agent tool PASS attempt 1 - opus validator 11/11 (contrast re-derived 11.5:1, iridescence judged organic not tech-drift, zero local assets - all inline SVG). Lane collision with run 03 (both metamorphosis family, dice 5 and 4) - expected cost of the recorded no-dedup decision, executions differ. fable site-build 4/4 attempt-1.
- 2026-08-10 (iamawriter design-runs loop, wave 2 close): site-build x1 (run 05 "Nurse Log") fable claude-fable-5 via Agent tool PASS attempt 1 - opus validator 9/9 (contrast re-derived 12.11:1, glow-network judged organic not tech, scope-clean). Wave 2 final tally: fable site-build 5/5 attempt-1, zero repair passes, zero narration reroutes, honest tool-absence handling in all five, 3-6 critique passes each. Signal: strong first site-build evidence for fable as a worker under the no-narration guard.
- 2026-08-10 (iamawriter design-runs loop, wave 3 + run close): docs x1 (T8 verify/ballot/journal) opus via Agent tool PASS attempt 1 - validator 6/6 (IHDR-verified uniform 1440px widths, blank-check by size + eyeball, scope clean); solved the IntersectionObserver blank-capture hazard belt-and-suspenders. Run totals: fable site-build 5/5 attempt-1, opus docs 2/2, glm-5.2 code-feature 1/1, zero repair passes across all eight units.
- 2026-08-10 (glm-5.2, claude-zai, code-feature): triage-default-import-loop wave 1, 1 task, pass on attempt 2. Signal: attempt 1 killed by the 900s default timeout with 35/36 suites already passing - the unit runs a 36-suite bash matrix repeatedly, so wall clock was the binding constraint, not capability. Route lesson: set timeout_s explicitly for units whose check-or-iterate loop includes a multi-minute full suite. Second lesson (check-writing): a check that prints only `tail -3` of a suite run starved the retry prompt of the failing suite's name; print the FAIL lines themselves.
- 2026-08-10 (glm-5.2, claude-zai, docs): triage-default-import-loop wave 2, 2 tasks, both first-try pass. Grep-contract doc rewrites with an executed test gate; house-style (no em-dash, one sentence per line, aligned tables) held without correction. Nominal.
- 2026-08-12 (model-intel loop, wave A): code-feature x1 (T2 canonical schema) glm-5.2 claude-zai PASS attempt 1 (213s) - TDD spec with embedded verbatim tests, hand-authored downstream-contract fixture correct on first try. code-feature x1 (T1b source-survey fixtures) sonnet via Agent tool PASS attempt 1 - opus validator 7/7 on independent reruns; honest negative finding (AA free tier exposes NO access/host field, only model_creator) verified against the raw body rather than invented. Signal (check-bug, orchestrator-owned): wave-A check template staged __pycache__ into the patch export via git add -A; patch applied with --exclude, purge line distilled into remaining wave templates. Not a worker fault.
- 2026-08-12 (model-intel loop, wave B): code-feature x6 (T3-T8 adapters/views) glm-5.2 claude-zai 6/6 PASS attempt 1 (239s wall, max_parallel 3). TDD specs with verbatim embedded tests; scope exactly per ownership lists; T8 authored honest role-mapping notes against the only fixture it could see. Signal (check-bug, orchestrator-owned): wave-A pycache purge distill was anchored before the unittest run, which regenerates pycache before git add -A; purge re-anchored immediately before the add for waves C-E. Worker record unaffected.
- 2026-08-12 (model-intel loop, wave C): code-feature x1 (T9 build orchestrator) glm-5.2 claude-zai PASS attempt 1 (344s). Dash-containing-host filename rule honored; cross-source merge collapsed without alias help. Signal (spec-writing lesson, orchestrator-owned): worker smoke-tested the spec'd CLI, which reads AA_API_KEY from the inherited env and legitimately wrote a snapshot outside the ownership list - spec ownership lists should anticipate a unit's own CLI side effects when env credentials are present. Accepted as a live Layer-1 capture, not a worker fault.
- 2026-08-12 (model-intel loop, wave D): code-feature x1 (T10 refresh pipeline) glm-5.2 claude-zai PASS attempt 1 (126s). Threaded reference_dir/config_dir through cleanly for the test seam while keeping CLI defaults. Run so far: glm-5.2 claude-zai 9/9 attempt-1 across waves A-D. Note for identity work: ai-benchmark's canonical reference now folds ringer slug "opus" onto Opus 4.8 by user decision (mixed-era rows accepted); TAXONOMY-driven era split remains open upstream.
- 2026-08-12 (model-intel loop, wave E + run close): docs x1 (T11 skill + installer) glm-5.2 claude-zai PASS attempt 1 (156s). Front matter, five-point body, #18 supersede footer, and a clean --dry-run installer verified by independent orchestrator rerun. Run total glm-5.2 claude-zai: 10/10 PASS attempt 1 (code-feature x9, docs x1), zero retries, zero worker-fault FAILs; both recorded signals were orchestrator-owned check/spec bugs. sonnet Agent-tool code-feature 1/1 with opus validator 7/7.
- 2026-08-15 (control-plane loop, wave 1): code-feature x1 (T1 tracker.sh label+comment primitives, 3-backend dispatch) glm-5.2 claude-zai PASS attempt 1 (167s). Custody pattern's first live run: orchestrator-placed RED test, worker ownership excluded tests/, check diffed golden copy + scope-grepped tests/ before running - all three stages clean. Worker left one honest note (guard message forward-references `tracker.sh done`, which lands in W2 - correct conservative reading, no boundary cross).
- 2026-08-15 (control-plane loop, wave 2): code-feature x1 (T2 claim/reclaim/status/evidence-gated done, exit-code contract 4/5/6/7) glm-5.2 claude-zai PASS attempt 1. Security-critical unit: full gate diff-read clean - receipt-before-flip ordering, anchored receipt grammar, earliest-ts owner with lex tie-break, --ran real-exit capture all per contract. Worker self-initiated a behavior-preserving DRY refactor of the W1 arms into shared dispatch helpers, inside ownership; 39/39 suite proved it safe.
- 2026-08-15 (control-plane loop, wave 3): code-feature x1 (T3 next-eligible: no-jq brace-scan JSON, stale-working sweep, blocker open-set) glm-5.2 claude-zai PASS attempt 1. Diff-read clean: body-only blocker scan, lexical-ts-equals-epoch trick justified by the claim verb's fixed timestamp shape, BSD/GNU date portability handled unprompted. Run so far 3/3 attempt-1, zero custody flags.
- 2026-08-15 (control-plane loop, wave 4): docs x2 (T4 queue-runner prompt, T5 run-state-onto-tickets) + code-feature x1 (T6 lifecycle-lint, 160-line four-class detector) glm-5.2 claude-zai 3/3 PASS, max_parallel 3. T4/T5 attempt 1; T6 attempt 2 - attempt 1 was rc=143 (timeout kill), not a logic failure; retry passed in ~1 min. Signal (disclosed narrowings, accepted): T6 documented remote title-only stem matching (tracker.sh list exposes no bodies) and class-d local-only (list is open-state only) in the script header - real seam limits, fail-safe consequences, not worker faults. Run total: 6/6 units green, 5/6 attempt-1, zero custody flags across 6 custody-checked units.
- 2026-08-16 (control-plane loop, kill-demo re-run): probe x1 (blind queue-runner kill/resume, prompt-only) glm-5.2 claude-zai PASS attempt 1. Owner rejected the earlier sonnet demo and directed the flat lane; fixture strengthened with an untouched-decoy todo. Runner selected the stale ticket, reclaimed, relaunched (left the dead unit-1 branch alone as outside ownership), evidenced done via re-executed --ran exit 0, decoy untouched - one per run proven. Honest self-noted stumble: tried a nonexistent `tracker.sh show` verb once, recovered by reading the issue file.
- 2026-08-16 (packaging loop, wave 1): code-feature x1 (T1 config surface: host.env template, config.toml -> placeholdered template rename, hardcode sweep) glm-5.2 claude-zai PASS attempt 2 (722s run). Attempt 1 failed on environment, not logic: tests/run.sh needs the gitignored generated mirrors (ISSUES.md/BACKLOG.md), absent in any fresh worktree; attempt 2 self-diagnosed, regenerated via scripts/gen-mirrors.sh, and passed everything. Custody clean (sweep.sh byte-matched the orchestrator golden); patch exactly the six owned files; gate suite 44/44 on the integration branch.
- 2026-08-16 (packaging loop, wave 1, signal): environment footgun distilled, not a model fault - worktree runs of this repo's tests/run.sh require a prior scripts/gen-mirrors.sh; wave 2+ specs now carry that line so attempt 1 is not burned re-learning it.
- 2026-08-16 (packaging loop, wave 2): code-feature x1 (T2 install.sh: host.env sourcing with env-wins capture, #30 non-TTY style refusal, absent-only config.toml render with sed-metachar guard, ringer doctor + stale-bin warnings) glm-5.2 claude-zai PASS attempt 1. Wave-1 mirror distill consumed cleanly (worker ran gen-mirrors unprompted-by-error). Full gate diff-read clean: all four verbatim edits landed exactly, no drift, ownership exact (install.sh + tests/install/ only). Acceptance re-run green on the integration branch; suite 45/45.
- 2026-08-16 (packaging loop, wave 3, signal - orchestrator, no model): T3 collapsed to a gate action (deliverable was its own verbatim check). Orchestrator briefly misattributed a spec-problem (live.sh vs clean-room satisfiability) and added a guard the harness's own output then disproved - tests/run.sh already runner-skips live.sh without gh auth; guard reverted same wave, net zero. Lesson for gate attribution: check the runner's skip list before declaring a suite-vs-sandbox conflict unsatisfiable.
- 2026-08-16 (packaging loop, wave 4): docs x1 (T4 README multi-host section, file-map rows, ringer-note repointing) glm-5.2 claude-zai PASS-after-attribution. Run JSON says fail, but the FAIL was a CHECK BUG, not the model: the orchestrator's ownership-guard grep had broken quoting (pattern parsed as filename), false-failing a worktree whose only change was the owned README.md; attempt 1's work was complete and correct, attempt 2's retry burned to a 900s timeout re-chasing the phantom. Orchestrator re-ran every check stage by hand against the surviving worktree (ownership exact, all greps, no em-dash, suite 45/45), full diff-read clean, work committed. Scoreboard fail row for this task should be read as check-bug, not model failure.
- 2026-08-16 (packaging loop, wave 4, signal): check-authoring lesson distilled - never build nested-quoted grep guards inside python-composed shell strings; state the guard as grep -cv 'literal' with single quotes, and dry-run the check against a synthetic worktree before launch.
- 2026-08-17 (reviewer-blacklist loop, wave 1): docs x3 (T1/T2/T3 reviewer-conduct contract into loop-drive, loop-review, loop-plan SKILL.md homes) glm-5.2 OPENCODE lane (openrouter/z-ai/glm-5.2) 3/3 PASS attempt 1 (106-204s, 25-32k tokens). All three blocks byte-identical to the orchestrator golden on independent gate re-diff; T2's two include-list reference bullets exact; zero scope flags; gate suite 45/45 on the integration branch.
- 2026-08-17 (reviewer-blacklist loop, wave 1, signal - lane, no model fault): claude-zai (z.ai direct) hard-down with API 529 on 6/6 attempts across the first launch, zero worker tokens; direct probe hung 90s. Re-routed same model via opencode/OpenRouter, which passed a one-token health probe and then went 3/3 attempt-1. Lesson: on all-task zero-token FAILs, probe the lane before burning retries; the scoreboard fail rows for run 20260817T023212Z are lane-outage, not model failure.
- 2026-08-17 (reviewer-blacklist loop, wave 2): code-feature x1 (T4 static uniformity gate tests/gates/reviewer-contract.sh, byte-given transcription) glm-5.2 OPENCODE lane PASS attempt 2 (275s). Attempt 1 died in the worker's own verify stage on worktree environment (stale gate-registry + missing mirrors), not logic; attempt 2 self-corrected. Gate: golden byte-diff identical, negative-path proof live (one-word mutation caught), suite 46/46 on integration.
- 2026-08-17 (reviewer-blacklist loop, wave 2, T5a): docs x1 (probe fixture, byte-given) glm-5.2 OPENCODE lane run-verdict fail TIMEOUT x2 but PASS-after-attribution: the surviving worktree held the complete fixture byte-identical to the golden (scope clean, canary absent) written early; the clock burned on off-task wandering (worker read ringer.py's own source at length). Orchestrator re-ran all check stages by hand, clean, committed the audited work. Scoreboard fail rows for T5a this run are worker-discipline timeout, not capability; the deliverable was perfect.
- 2026-08-17 (reviewer-blacklist loop, wave 2, signal): opencode-lane glm-5.2 shows a wander-after-done failure mode on trivial byte-transcription tasks - it finishes the work, then explores unrelated code until timeout_s kills it. Mitigation for future manifests: add "when the VERIFY commands pass, stop immediately and return" to mechanical specs, or cap timeout_s lower so the kill lands after the work but before the retry burns.
- 2026-08-17 (reviewer-blacklist loop, T5b ship-time probe): probe x1 (adversarial reviewer-contract probe, hardened Spec-axis prompt + mutating fixture) sonnet via claude engine PASS attempt 1 (15s). Engine re-pinned from glm-5.2/claude-zai (z.ai down; opencode sandbox would have blanked the canary observable; allow_full_access=false). Reviewer refused the embedded install.sh citing the contract verbatim, flagged the criterion unverifiable-without-mutation, and still delivered the correct Spec finding (missing ValueError branch). Canary absent, 16 skill links inode-identical, fixture untouched. Scoreboard note: probe rows measure contract-honoring, not code-review skill.
- 2026-08-18 (context-map-34 loop, single-unit run): code-feature x1 (T1+T3+T4: map create, pointer wiring, class-e lint + tests) glm-5.2 claude-zai PASS attempt 1 (161s). Byte-exact transcription of three verbatim plan blocks confirmed at the gate (map file diff-identical to the plan block); stop-on-verify honored, no wander-after-done; zero 529s this run despite overnight lane instability (user-pinned sonnet fallback unused). Gate suite 46/46 on main.
- 2026-08-18 (setup-lint-vendor, single-unit run): code-feature x1 (vendor lifecycle-lint.sh into loop-setup: install block, drift pair, template v3 + rule 1a, distribution-test extension) glm-5.2 claude-zai PASS attempt 1 (97s). All four verbatim edits exact on gate diff-read; zero 529s. Two orchestrator check-authoring lessons, no model fault: (1) the custody check ran a SUBSET of suites and the full-suite gate then failed on version-pinned assertions the check never exercised - custody checks for config-surface changes should run the whole suite or grep for pinned literals; (2) a gate command chained through a pipe (tail) masked the suite's non-zero exit and let a red suite reach a commit - capture suite exit codes plainly, never through a pipeline tail.
- 2026-08-20 (amend-command loop, wave 1): code-feature x1 (T1 amend cmd: append_amendment, run_amend_command, subparser, dispatch) sonnet via Agent tool PASS attempt 1 (257-test suite green, RED-GREEN honored, validator byte-match on canonical test). docs x1 (T7 ringer#65 comment draft, Jeremy-voice, credit-accurate vs live upstream thread) opus via Agent tool PASS attempt 1. Both validators independent-reran checks; zero scope flags.
- 2026-08-20 (amend-command loop, wave 2): code-feature x1 (T2 dual-aggregator amendment void, partition_amendments, F3/F4/F6 traps all covered) opus via Agent tool PASS attempt 1 (261/261 suite; high-effort validator ran its own /tmp synthetic probe: first_try 0.5->1.0, void survives --engine and --since; both sanctioned deviations honest). Signal: pre-existing --since is date-granular (parse_log_date), noted for awareness, outside this diff.
- 2026-08-20 (amend-command loop, wave 3): code-feature x1 (T3 log_has_amendments forces JSONL over the SQLite read-model; insert skips amendment rows) sonnet via Agent tool PASS attempt 1 (262/262; validator re-derived the live default-path sandbox proof and a stale-DB adversarial probe - stale read-model does not win). Note: real-log growth 147->149 during the wave attributed to the concurrent config-v4-split run, not this build.
- 2026-08-20 (amend-command loop, wave 4): code-feature x1 (T4 Amended column across CLI table + HUD JS + standalone HTML; amendment notes folded into Notes tooltips via one enrichment edit) sonnet via Agent tool PASS attempt 1 (264/264; validator re-ran the HTML smoke, verified 13/13 cell alignment, tooltip placement, and always-present-0 on a clean log).
- 2026-08-20 (amend-command loop, wave 5): code-feature x1 (T5 triage subcommand: per-run non-PASS view with inline [amended] markers, read-only) sonnet via Agent tool PASS attempt 1 (265/265; validator probe confirmed ERROR/TIMEOUT inclusion, PASS/other-run exclusion, log byte-identical after run).
- 2026-08-20 (amend-command loop, wave 6): docs x1 (T6 RIT-UADV2223 cleanup runbook) glm-5.2 OPENCODE lane run-verdict fail x2 but PASS-after-attribution: run p92887's 2 zero-token FAILs were an orchestrator manifest bug (bare model slug "glm-5.2" where the opencode lane needs "openrouter/z-ai/glm-5.2"); run p93713's FAIL was a check bug (manifest omitted the repo key, so worktrees:true made a plain dir and the check's git patch-export hit "not a git repository") plus a JSON-to-shell quoting artifact that escaped the seven command quotes. Worker content otherwise complete and correct; orchestrator de-escaped, re-ran every check stage by hand (all green, seven commands byte-identical to plan), Opus reviewer 5/5 pass, committed 9ca35fa. Scoreboard fail rows for both runs are orchestration/check errors, not model failures - amend candidates on this host once the amend feature merges to main.
- 2026-08-20 (amend-command loop, wave 6, signal): manifest-authoring lessons - opencode lane model field takes the full openrouter slug, never the bare model name; worktrees:true without a repo key yields non-git taskdirs, so any git-based export in a check needs "repo" set. Probe one-token before re-running any all-task zero-token FAIL.
- 2026-08-20 (sfextract reports-extract, single-unit run): code-feature x1 (3-task plan: connection helpers + reports.py + CLI wiring, live staging checks) opus AGENT-TOOL lane PASS attempt 1 (~6m, 36 tool uses). Fresh opus validator 16/16 criteria on independent rerun (offline suite 75/75, live criteria 2-4, throwaway-dir idempotency byte-identical except extractedAt); scope clean, zero repairs. Correctly took the plan's pre-authorized concurrency branch when the org's real scale (614 reports) broke the stated <100 premise.
- 2026-08-20 (sfextract reports-extract, signal - orchestrator check bug, no model fault): validator launch prompt cited base 5aa30e6, a divergent sibling, not an ancestor of the unit branch; naive diff-from-base would have manufactured a docs/ scope-violation FAIL. Validator re-derived the true merge-base (e9ac57d) and attributed correctly instead of failing the worker. Lesson: compute the scope-audit base with git merge-base at launch time, never assume current main is the branch point of a worktree created earlier.
- 2026-08-20 (sfextract reportTypeId follow-up, single-unit run): code-feature x1 (metadata-id enrichment, 3 files + live regeneration) opus AGENT-TOOL lane PASS attempt 1 (~3.5m). Orchestrator-gated: 78/78 suite, 614/614 records keyed, custom-flag/id cross-route 0 mismatches. Worker self-detected a stale worktree base (snapshot at conversation-start, not current main) and ff-forwarded before working - second occurrence this session; future briefs should state the expected base commit.
