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
