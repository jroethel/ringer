# Import triage 2026-10-02

Run by loop-setup in github mode against jroethel/ringer.
Candidates scanned: repo root and `docs/`, skipping governed lanes.

| source-doc                         | item                                   | class | verdict       | evidence / issue                                      | action        |
| ---                                | ---                                    | ---   | ---           | ---                                                   | ---           |
| docs/AMENDMENTS-PENDING.md         | amend molt u10-molt-on-molt            | issue | outstanding   | #6                                                    | filed, keep   |
| docs/AMENDMENTS-PENDING.md         | amend molt u13-instr-files             | issue | outstanding   | #7                                                    | filed, keep   |
| docs/AMENDMENTS-PENDING.md         | amend molt u12e-kanban-ledger          | issue | outstanding   | #8                                                    | filed, keep   |
| ringer-live-artifacts-plan.md      | reporter block, on_complete            | idea  | outstanding   | #9                                                    | filed, archive |
| ringer-live-artifacts-plan.md      | reporter rolling mode                  | idea  | outstanding   | #10                                                   | filed, archive |
| ringer-live-artifacts-plan.md      | publish_cmd hook                       | idea  | outstanding   | #11                                                   | filed, archive |
| ringside-upgrade-notes.md          | per-run collapse                       | idea  | outstanding   | #12                                                   | filed, archive |
| docs/AMENDMENTS-PENDING.md         | Section D amend injection              | -     | already-built | E1                                                    | drop          |
| docs/AMENDMENTS-PENDING.md         | /bin/bash check runner                 | -     | already-built | E2                                                    | drop          |
| docs/MODEL-NOTES.md                | Jev cache malformed-line loader        | -     | already-built | E3                                                    | drop          |
| ringer-live-artifacts-plan.md      | per-task engine_args                   | -     | already-built | E4                                                    | drop          |
| ringer-live-artifacts-plan.md      | Tier 0 page, final report, index       | -     | already-built | E5                                                    | drop          |
| ringside-upgrade-notes.md          | link artifact index from Ringside      | idea  | already-built | E6                                                    | drop          |
| ringside-upgrade-notes.md          | open final report from Ringside        | idea  | already-built | E6                                                    | drop          |
| ringside-upgrade-notes.md          | live-verify 3 Tauri commands           | issue | stale         | E7                                                    | drop          |

Dropped evidence:

- E1: `runs.jsonl` holds amendment rows for all ten earlier pairs; `amend` is at `ringer.py:11743`.
- E2: `executable="/bin/bash"` at `ringer.py:9404`.
- E3: `load_jev_cache` validates model, usage and confidence at `ringer.py:1469-1495`.
- E4: `engine_args` parsing at `ringer.py:2150`.
- E5: `render_status_html` at `ringer.py:5314`, `render_final_report_html` at `ringer.py:5352`, index at `ringer.py:5455` (commit bc5c6cf, 2026-07-04).
- E6: the artifact library (`ringer.py:3741-3912`, read in `dashboard/dashboard.html:2262-2268`) shipped with the Ringside overhaul, 2026-07-05 and 2026-07-09; inferred from code, entry types not exhaustively checked.
- E7: `dashboard/dashboard.html` no longer invokes `resize_main_window` or `read_artifact_html`; only `load_settings` and `save_settings` remain, and the app was rebuilt after the note.

Left in place as reference or drafts: `docs/TAXONOMY.md`, `docs/STEERING.md`, `docs/JEV.md`, `docs/MODEL-NOTES.md`, `docs/interview-prompt.md`, `docs/PR-65-FRAMING.md`, `docs/ringer-65-comment-draft.md`, `docs/AMENDMENT-ROWS.md` (its "proposed, not built" status line is stale).
