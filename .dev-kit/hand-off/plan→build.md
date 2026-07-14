# Plan → Build hand-off (1-skill-rewrite)

> From: `/dev-kit:plan` stage. To: `/dev-kit:build` stage. Date: 2026-07-14.
> Replaces prior 0-mvp hand-off.

## Plan summary

Refactor plugin-harness so its 5-question interview, idea-plan assembly, and Codex-layout emit are implemented natively as CC + Codex skills. Drop the Python CLI indirection (`python -m src.engine.cli`) and the `cc-adapter` / `codex-adapter` thin-wrapper layer. Keep the 5-question schema and the Codex plugin-layout emit format identical (those are the user-facing contracts).

Dual-runtime (CC + Codex). Direction slot in `PRD.md` §1 is `<unspecified>` for explicit single-runtime override if the user wants to collapse.

## Plan artifacts (this commit)

| Artifact | Path | Purpose |
|---|---|---|
| PRD | `PRD.md` | 6-section plan (§1 frame, §2 validate, §3 non-goals, §4 phase plan, §5 AC, §6 hand-off) |
| Prior PRD preserved | `PRD-0-mvp.md` | Renamed from prior `PRD.md` so the 0-mvp plan remains on disk |
| Phase index | `phases/1-skill-rewrite/index.json` | 5 steps + ambiguity/value/evidence scores |
| Step files | `phases/1-skill-rewrite/step{0..4}.md` | Per-step pinned template (Status / Read first / Task / AC / Verification / Don't) |
| Decision log | `.prd/decision-log.md` | Cumulative Gate 1-3 entries; appended to 0-mvp log |
| Loop log | `.dev-kit/loop-log.json` | 3 Gate-2 cycles; status=`pass` |
| Hand-off | `.dev-kit/hand-off/plan→build.md` | This file |

## Gate results

| Gate | Result |
|---|---|
| 1 frame | captured (goal + target_user + situation; direction = dual-runtime) |
| 2 validate | evidence 3 ✓, value 33.33 ✓, ambiguity 3 ✓ → PASS |
| 3 non-goals | 4 entries with rationale + breach-response |
| 4 decompose | 5 steps in `1-skill-rewrite`, dependency-first order |
| 5 emit | PRD.md DoD pass, all 6 conditions; hand-off written |

## Build stage expectations

- methodology = tdd (Iron Law L1 + L4 active)
- step runner = harness-runner per `lib/execute.py`
- active hooks = `tdd-guard`, `bash-guard`, `secret-scan` (R), `slop-detector`, `stop-verify`
- Iron Laws L2/L3: every step quote exit codes + test counts; no completion claim without them
- marker contract = the two-line HTML-comment block in `step<N>.md`'s `## Verification & Status Update` section

## Per-step AC totals (full inventory)

- step0 (cc-skill-native): AC0..AC4 → 5 ACs
- step1 (codex-skill-native): AC0..AC5 → 6 ACs
- step2 (shared-resources): AC0..AC5 → 6 ACs
- step3 (validator-keep): AC0..AC5 → 6 ACs
- step4 (e2e-no-python-shells): AC0..AC6 → 7 ACs
- **Total: 30 ACs across 5 steps** (PRD §5 representative subset: 11 ACs; full per-step inventory: 30 ACs)

## Carry-forward constraints (must hold across build)

1. `src/schema/questions.py` MUST NOT be modified (gate-3 non-goal #2)
2. `src/emitter/templates/codex/*.j2` MUST NOT be modified (gate-3 non-goal #3)
3. `src/emitter/validator.py` MUST NOT be modified (kill-condition anchor)
4. SKILL.md prompt chain MUST NOT shell to `python -m src.engine.cli` — only `python scripts/verify_emit.py` is allowed
5. Both runtimes' question content MUST match (CC + Codex SKILL.md share the same 5 questions verbatim)
6. Zero `dev-kit` text references in any artifact (carry-over from 0-mvp non-goal)
7. All emitted plugin files MUST validate against the **vendored** Codex schema at `docs/codex-plugin.schema.json`

## Kill-condition anchor

Phase succeeds iff:
- step-3 AC1 + AC2 pass (validator passes reference fixture, fails malformed fixture)
- step-4 AC3 + AC4 pass (e2e proves zero-Python-shell interview + byte-equivalent Codex-layout emit on both runtimes)
- All 5 step files marked `status: completed` in `phases/1-skill-rewrite/index.json`

Phase fails (kill) iff any of the above fails after 3 retries per step → revert to 0-mvp adapter architecture.

## Step ordering (dependency-first)

0. cc-skill-native → 1. codex-skill-native → 2. shared-resources → 3. validator-keep → 4. e2e-no-python-shells

Steps 0 and 1 may run in parallel (independent SKILL.md rewrites) — but step 2 depends on both. Step 3 depends on step 2. Step 4 depends on steps 0, 1, 2, 3.

The harness-runner is responsible for dependency resolution; this hand-off only documents the order.

## Out of scope (parked, not forgotten)

- 5-question schema change (defer to `2-schema-v2` PRD)
- Codex plugin-layout emit format change
- Single-runtime collapse (CC-only or Codex-only) — direction is `<unspecified>` for user override
- Logging
- Commercial / marketplace publishing
- Open-source project plugin scaffolding
- GUI / web wizard

## Resume path on interruption

- If build stops mid-phase, the runner resumes from the last `pending` step in `phases/1-skill-rewrite/index.json`.
- If a step reaches `error` after 3 retries, it surfaces `error_message` to the user; resume by re-running `/dev-kit:build`.
- If a step reaches `blocked`, the user provides the unblocker and re-runs `/dev-kit:build`.

## Next command

`/dev-kit:build`