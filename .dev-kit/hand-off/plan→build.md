# Plan → Build hand-off

> From: `/dev-kit:plan` stage. To: `/dev-kit:build` stage. Date: 2026-07-08.

## Plan artifacts

- `PRD.md` — 6-section DoD-pass plan (this commit)
- `phases/0-mvp/index.json` — 7-step state machine, all `status: pending`
- `phases/0-mvp/step{0..6}.md` — pinned-template step files
- `.prd/decision-log.md` — frame + gate-2 cycles + non-goals + ambiguity deltas
- `.dev-kit/loop-log.json` — narrowing [10, 8, 5, 3], convergence PASS

## Gate results

| Gate | Result |
|---|---|
| 1 frame | captured (goal + target_user + situation) |
| 2 validate | evidence 3 ✓, value 3.33 ✓, ambiguity 3 ✓ → PASS |
| 3 non-goals | 5 entries with rationale + breach-response |
| 4 decompose | 7 steps in `0-mvp`, dependency-first order |
| 5 emit | PRD.md DoD pass, all 6 conditions |

## Build stage expectations

- methodology = tdd (Iron Law L1 + L4 active)
- step runner = harness-runner per `lib/execute.py`
- active hooks = `tdd-guard`, `bash-guard`, `secret-scan` (R), `slop-detector`, `stop-verify`
- Iron Laws L2/L3: every step quote exit codes + test counts; no completion claim without them
- marker contract = the two-line HTML-comment block in `step<N>.md`'s `## Verification & Status Update` section

## Carry-forward constraints

- The 5-question interview order is locked. Reorder is a product change, not a refactor.
- All emitted plugin files MUST validate against the Codex layout (https://developers.openai.com/codex/plugins, https://developers.openai.com/codex/skills).
- Zero `dev-kit` text references in any artifact (non-goal b). Sub-agents that emit dev-kit mentions fail review.
- No log emission (non-goal 1). Defer to a later stage.
- No GUI / web wizard (non-goal 5). CLI only.

## Out of MVP scope (parked, not forgotten)

- Logging
- Commercial / marketplace publishing
- Open-source project plugin scaffolding
- GUI / web wizard

## Resume path on interruption

- If build stops mid-phase, the runner resumes from the last `pending` step in `phases/0-mvp/index.json`.
- If a step reaches `error` after 3 retries, it surfaces `error_message` to the user; resume by re-running `/dev-kit:build`.
- If a step reaches `blocked`, the user provides the unblocker and re-runs `/dev-kit:build`.

## Next command

`/dev-kit:build`
