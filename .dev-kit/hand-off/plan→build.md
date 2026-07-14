# Plan → Build hand-off

> From: `/dev-kit:plan` stage. To: `/dev-kit:build` stage. Date: 2026-07-14.
> Active phase: **1-skill-creator**. Prior phase 0-mvp build continues in parallel.

## Plan artifacts

- `PRD.md` — 6-section DoD-pass plan (this emission; multi-phase)
- `phases/1-skill-creator/index.json` — 5-step state machine, all `status: pending`
- `phases/1-skill-creator/step{0..4}.md` — pinned-template step files
- `.prd/decision-log.md` — frame + gate-2 cycles + non-goals + ambiguity deltas (both phases)
- `.dev-kit/loop-log.json` — narrowing [10, 8, 5, 3] (0-mvp) + [10, 7, 5, 3] (1-skill-creator), both PASS

## Gate results

| Gate | Result (1-skill-creator) |
|---|---|
| 1 frame | captured (goal + target_user + situation) — extends 0-mvp, adds 2 sub-modes |
| 2 validate | evidence 3 ✓, value 66.67 ✓, ambiguity 3 ✓ → PASS |
| 3 non-goals | 5 entries with rationale + breach-response |
| 4 decompose | 5 steps in `1-skill-creator`, dependency-first order |
| 5 emit | PRD.md DoD pass, all 6 conditions |

## Build stage expectations

- methodology = tdd (Iron Law L1 + L4 active)
- step runner = harness-runner per `lib/execute.py`
- active hooks = `tdd-guard`, `bash-guard`, `secret-scan` (R), `slop-detector`, `stop-verify`
- Iron Laws L2/L3: every step quote exit codes + test counts; no completion claim without them
- marker contract = the two-line HTML-comment block in `step<N>.md`'s `## Verification & Status Update` section

## Carry-forward constraints

- 0-mvp's 5-question interview order is locked. Do not modify `src/schema/questions.py` (phase1 non-goal 1).
- 0-mvp's emitter (`src/emitter/codex.py`) and assembler (`src/assembler/plan.py`) are reused; do not fork.
- The CC and Codex SKILL.md formats are distinct; each runtime has its own vendored schema in `docs/{cc,codex}-skill.schema.json`.
- All emitted plugin + skill files MUST validate against the **vendored** schemas — `docs/codex-plugin.schema.json` for `plugin.json`, `docs/cc-skill.schema.json` for CC SKILL.md, `docs/codex-skill.schema.json` for Codex SKILL.md. Live URLs may change.
- Zero `dev-kit` text references in any artifact (extends 0-mvp non-goal b).
- The dual-runtime parity test (`tests/e2e/test_dual_runtime_parity.py`) is the **kill condition** (Gate 2 cycle 2): if CC and Codex SKILL bodies diverge byte-for-byte beyond the locked frontmatter divergence, the build is blocked.
- 0-mvp steps 1, 2, 6 are still `pending` in `phases/0-mvp/index.json`. The build runner handles both phases — phase1 steps that depend on 0-mvp internals (step 1 extends `src/engine/cli.py`, step 2 reuses 0-mvp's emitter, step 3 extends the adapters) can run in parallel with 0-mvp's pending steps where dependencies permit.

## Out of MVP scope (parked, not forgotten)

- Logging
- Commercial / marketplace publishing
- Open-source project plugin/skill scaffolding
- GUI / web wizard
- Editorial / lint / style gate on SKILL.md body
- Runtime cross-compilation between CC and Codex formats
- 0-mvp interview reordering

## Resume path on interruption

- If build stops mid-phase, the runner resumes from the last `pending` step in `phases/1-skill-creator/index.json`.
- If a step reaches `error` after 3 retries, it surfaces `error_message` to the user; resume by re-running `/dev-kit:build`.
- If a step reaches `blocked`, the user provides the unblocker and re-runs `/dev-kit:build`.

## Next command

`/dev-kit:build`
