# Jev in ringer

Ringer can ask Jev, the System One model from TypeSafe, for help with two decisions it makes badly on its own.
Every Jev feature is off by default.
With the master switch off, the API key unset, or the API unreachable, ringer behaves exactly as it does without Jev.

## Switches

All settings live in the `[jev]` table of `config.toml`, and no environment variable overrides them.
A feature runs only when `enabled` and that feature's own switch are both `true`.
Each feature has its own section below; a switch whose section is missing has no effect yet.

| Key                | Default                                   | Meaning                                                              |
|--------------------|-------------------------------------------|----------------------------------------------------------------------|
| `enabled`          | `false`                                   | Master switch; no Jev feature runs unless this is `true`.            |
| `task_type`        | `false`                                   | Record the task_type Jev assigns, in `lint` and `run`.               |
| `fail_flag`        | `false`                                   | Ask Jev whether a FAIL is the check's fault before the retry.        |
| `model`            | `"jev-1.13.0"`                            | Pinned model version sent with every request.                        |
| `endpoint`         | `"https://api.typesafe.ai/v1/systemone"`  | TypeSafe System One endpoint.                                        |
| `timeout_s`        | `5.0`                                     | Hard timeout for one request, in seconds.                            |
| `task_type_cutoff` | `0.9`                                     | Lowest Jev confidence at which its task_type is recorded.            |
| `fail_flag_cutoff` | `0.9`                                     | Lowest Jev confidence at which a FAIL is flagged as a check fault.   |
| `held_out`         | `["research", "probe", "persona-review"]` | Task types Jev never assigns or overrides; edit the list to release. |

## API key

The key is read from the `TYPESAFE_API_KEY` environment variable only.
It is never read from config, never logged, and never printed.
Without it, Jev is skipped with one line on stderr, and ringer carries on as it does today.

## Declared fields

Each decision point sends exactly one request, and that request carries only these state fields, cut to these caps.
The text leaves this host verbatim up to the cap; ringer applies no other redaction.
A task with `"redact_spec": true` sends nothing at all: task_type keeps the hand label, and a FAIL is retried as before with `{"skipped": "redact_spec"}` on its row.
The constant `JEV_DECLARED_FIELDS` in `ringer.py` must equal this table, and `tests/test_jev_plumbing.py` fails if they drift.

| Decision point | Field          | Source                                                | Cap (chars) |
|----------------|----------------|-------------------------------------------------------|-------------|
| `task_type`    | `task_spec`    | The manifest task's `spec`                            | 12000       |
| `fail_flag`    | `task_spec`    | The FAIL row's logged `spec` (`spec[:500]`)           | 500         |
| `fail_flag`    | `check_output` | The check output excerpt the FAIL row logs in `notes` | 2000        |

## Fallback

Every request runs off the asyncio event loop with a hard timeout, so a slow or hanging API never stalls other tasks.
During `run`, at most 4 Jev requests are in flight at once, and time spent waiting for a slot does not count against `timeout_s`.
Ringer never retries a Jev request.
Each feature has its own breaker, so a task_type failure never turns off the FAIL flag.
A service-level failure prints one line on stderr and turns that feature off for the rest of the `lint` or `run` invocation:

```text
jev: skipped <feature> (<reason>); continuing without Jev
```

A request-specific failure skips only that one decision; it is recorded on the attempt row (and printed by `lint` for that task), and Jev stays on.

| Reason                  | Meaning                                                    | Turns the feature off |
|-------------------------|------------------------------------------------------------|-----------------------|
| `no-key`                | `TYPESAFE_API_KEY` is unset or empty; no request was sent. | yes                   |
| `timeout`               | No response within `timeout_s`.                            | yes                   |
| `network`               | Connection refused, DNS failure, or another network error. | yes                   |
| `http-401`              | Missing or invalid API key.                                | yes                   |
| `http-429`              | Rate limited.                                              | yes                   |
| `http-5xx`              | A server error, including `http-529` (overloaded).         | yes                   |
| `http-422`              | TypeSafe rejected this request body.                       | no                    |
| `http-<other 4xx>`      | Any other client error for this request.                   | no                    |
| `bad-response`          | The response was not the expected JSON shape.              | no                    |
| `error-<ExceptionType>` | An unexpected client-side error; ringer never raises.      | no                    |

## Cost

Price read from docs.typesafe.ai on 2026-09-23: $0.042 per million input tokens, and output tokens are free.
The pilot's 155 task_type calls used 128,400 input tokens in total, about $0.0054.
At about 100 calls a month of up to 1,500 input tokens each, Jev costs under $0.01 a month.

## FAIL flag gate

The FAIL flag is parked as of 2026-09-23, and `fail_flag = true` has no effect because the flag was never built.
The offline replay ran once on 2026-09-23 with contract `fail_flag-v1` over the 47 logged FAIL pairs and missed the bar: it flagged 0 of the 11 labeled check_bug tasks and 0 tasks overall, with a highest `check` probability of 0.78 against the 0.9 cutoff.
The replay script `scripts/jev_fail_replay.py` still sends each logged task's first FAIL to Jev with the same fields and caps a live flag would use, writes `results.jsonl`, `summary.json`, and `review.csv` into its `--out` directory, and is safe to rerun, because finished pairs are skipped.
The bar it scores is unchanged: `bar_met: true` needs at least 9 of the 11 labeled check_bug tasks flagged, and hand-judged wrong flags in `review.csv` plus `false_flags` must total at most 20% of `flags_total`.
The plan's one allowed rewording (`fail_flag-v2`) was not spent, because the declared fields, not the wording, are the likely limit; the handoff `docs/handoffs/2026-09-23.jev-fail-flag-parked.md` records the evidence and the follow-up candidates.

## task_type

With `enabled = true` and `task_type = true`, `./ringer.py lint` and `./ringer.py run` ask Jev for each task's type, one request per task.
The question is the pilot's pinned 8-type contract (`task_type-v1`): `code-feature`, `code-fix`, `code-review`, `docs`, `site-build`, `persona-review`, `probe`, `research`.
Jev's label is recorded when its confidence is at least `task_type_cutoff`, neither Jev's label nor the hand label is in `held_out`, and the hand label is empty or one of the 8 types.
Otherwise the hand label is recorded.
Lint prints one info line per task, for example `jev: t1: task_type=site-build confidence=0.97 hand=docs -> overrides hand` (or `-> agrees`, or `-> keeps hand (<reason>)`), and the exit code is unchanged.
A task counts as labeled by Jev whenever Jev's label was used, including when it matches the hand label.
Answers are cached in `~/.ringer/jev-cache.jsonl` (or under `RINGER_HOME`), keyed by the contract, the model, and the exact spec text sent, so an unchanged task makes no second call and a cutoff change needs no call.
Each attempt row then carries `task_type` (the recorded value), `task_type_source` (`hand` or `jev`), `task_type_hand`, and `jev_task_type` with Jev's choice, confidence, probabilities, `model`, `usage`, the cutoff, and whether the answer came from the cache.
The Postgres log backend drops these fields, as it already drops `task_type`.

## Scoreboard

`./ringer.py models` groups results by the recorded task_type, as before.
Once the log holds at least one Jev-labeled task, each bucket header shows how many tasks were labeled by hand and how many by Jev, for example `Task type: docs (hand 40, jev 8)`, and `--json` groups carry `task_type_sources: {"hand": n, "jev": n}`.
A log with no Jev-labeled task prints exactly what it printed before Jev existed.
A task's source is its final attempt row's `task_type_source`; rows written before Jev count as `hand` when they have a task_type, and untyped rows count as neither.
The SQLite read model stores `task_type_source` from schema version 4; run `./ringer.py db rebuild` if an older ringer process ingested Jev-labeled rows before the upgrade.
