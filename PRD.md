# PRD — plugin-harness

> Plan stage output. Methodology: tdd.
> Active phase: **1-skill-creator**. Prior phase: 0-mvp (emitted 2026-07-08; mid-build: 4/7 steps completed; steps 1, 2, 6 still pending).
> Worktree: `.claude/worktrees/skill-plugin-creator`. Branch: `feat/skill-plugin-creator`. Date: 2026-07-14.

## §1 Frame

- **goal**: extend plugin-harness with two new sub-skills — `skill-creator` (3-question interview that emits dual-runtime SKILL.md) and `plugin-creator` (5-question interview that emits dual-runtime plugin.json + bundled SKILL.md) — both registered natively as CC skills and Codex skills, both shelling out to plugin-harness CLI in a dedicated sub-mode (`mode=skill_create` | `mode=plugin_create`).
- **target_user**: a plugin author who already shipped via plugin-harness 0-mvp and now wants to author a **skill** (single SKILL.md, no plugin wrapper) without rewriting the interview flow; secondarily, a plugin author who wants to ship a plugin that bundles multiple SKILLs under one `plugin.json`.
- **situation**: today plugin-harness stops at the plugin boundary — users hand-roll SKILL.md by copying `src/adapter/codex_skills/plugin-harness/SKILL.md` as a template and filling in frontmatter manually. Two artifacts of confusion occur: (a) the CC skill format expects YAML frontmatter with `name` + `description`; Codex expects `name` + `metadata` block — hand-rolling drifts; (b) the plugin-creator experience isn't surfaced — anyone who wants to author a plugin still types 5 questions and waits through plugin emission, even if what they actually want is "5 SKILLs under one plugin.json".

## §2 Validate

- **evidence_count**: 3 (PASS, threshold ≥3)
  1. **prior reverted attempt** — commit `266897b` ("feat(plan): add 1-skill-rewrite phase for native CC+Codex skill implementation", PR #38) was merged then reverted by `9e5583a` (PR #39). Different origin: prior internal work — proves user intent and surfaces the failure mode this phase must avoid.
  2. **first-person** — the user re-issued the same ask in this prompt. Different origin: self.
  3. **analogue product** — Anthropic's `claude-code-guide` skill and OpenAI's Codex plugin authoring flow each ship a single-runtime authoring tool; neither covers both runtimes from one interview. Different origin: market analogue.
- **value_score**: 66.67 (PASS, threshold ≥3.0) — `$2,000 LTV × 200 reachable / $6,000 cost = $400,000 / $6,000`.
- **ambiguity_score**: 3 (PASS, threshold ≤3) — narrowed 10 → 7 → 5 → 3 over 3 cycles (scope given revert, kill = parity test, first user + first click).
- **convergence**: PASS. Detail in `.prd/decision-log.md` and `.dev-kit/loop-log.json`.

## §3 Non-Goals

| # | Non-goal | Rationale | Breach response |
|---|---|---|---|
| 1 | No rewrite of the 0-mvp 5-question interview | 0-mvp's question order is the product surface; reordering breaks all canary installations | reject reorder PRs touching `src/schema/questions.py`; split into a separate "interview-revision" PRD |
| 2 | No runtime cross-compilation from CC-skill to Codex-skill (or vice versa) | format divergence is real (different frontmatter shapes, different metadata keys, different invocation semantics); post-hoc conversion loses information — emit both from the same interview instead | if reviewer asks for `convert-skill` sub-mode, defer to a separate "format-converter" PRD |
| 3 | No GUI / web wizard | CLI suffices; extends 0-mvp non-goal 5 | if GUI added, require CLI fallback for automation |
| 4 | No marketplace / commercial publishing | 0-mvp non-goal 3 extends; skill/plugin authors ship to their own team, not a marketplace | defer to a separate "publish" PRD |
| 5 | No editorial / lint / style gate on the SKILL.md body | 0-mvp's emitter has none; adding one couples the build to a style guide | if PR adds a lint pass, defer to a separate "skill-lint" PRD |

## §4 Phase Plan

Two phases:

- **0-mvp** (emitted 2026-07-08): 7 steps. 4 completed (0, 3, 4, 5); 3 pending (1, 2, 6). Source: `phases/0-mvp/index.json`. Not the active plan; included here for context. 0-mvp build resumes from step 1.
- **1-skill-creator** (this plan, 2026-07-14): 5 steps, all `pending`. Source: `phases/1-skill-creator/index.json`.

| phase | step | name | title |
|---|---|---|---|
| 1-skill-creator | 0 | skill-spec-schema | Dual-runtime skill spec + validators |
| 1-skill-creator | 1 | skill-sub-mode | skill-creator: 3-question interview + dual SKILL.md emitter |
| 1-skill-creator | 2 | plugin-sub-mode | plugin-creator: 5-question interview + plugin.json + dual-skill bundle emitter |
| 1-skill-creator | 3 | adapter-register | CC + Codex adapters register skill-creator and plugin-creator as native skills |
| 1-skill-creator | 4 | e2e-parity | E2E + dual-runtime parity test |

## §5 Acceptance Criteria

Representative subset of per-step AC commands from `phases/1-skill-creator/step<N>.md`. The build runner reads both this §5 (representative subset) and the per-step files (full inventory); mismatch on any row fails the build. Steps 1, 2, 3, 4 also have full per-step ACs not mirrored here; see those step files for the full contract.

| AC# | Step | Command | Source |
|---|---|---|---|
| AC1 | step 0 | `python -m pytest tests/test_skill_schema.py -v → exit 0 (CC schema + Codex schema validators active)` | `phases/1-skill-creator/step0.md` AC1 |
| AC2 | step 0 | `bash -c '! grep -q "Pinned placeholder" docs/cc-skill.schema.json docs/codex-skill.schema.json' → exit 0` | `phases/1-skill-creator/step0.md` AC3 |
| AC3 | step 1 | `python -m pytest tests/test_skill_sub_mode.py -v → exit 0 (3Q interview + dual SKILL.md emit + validation + idempotency)` | `phases/1-skill-creator/step1.md` AC1 |
| AC4 | step 3 | `python -m pytest tests/test_skill_adapter.py -v → exit 0 (CC + Codex native skill install, idempotent, both validate)` | `phases/1-skill-creator/step3.md` AC1 |
| AC5 | step 4 | `bash scripts/e2e-skill-creator.sh → exit 0 (cross-runtime parity)` | `phases/1-skill-creator/step4.md` AC1 |

## §6 Hand-off

Next invocation: **`/dev-kit:build`**.

Build stage expectations:
- TDD methodology (per `CLAUDE.md` §2, current methodology = tdd). Tests first.
- Iron Laws L1 (no prod code without verification artifact) + L2 (no fix without reproduction) + L3 (no completion claim without quoted exit code / test count / build log) + L4 (no TODO/FIXME) + L5 (no option lists when not asked) all active.
- Each step in `phases/1-skill-creator/step<N>.md` runs under the harness-runner. Sub-agent updates the step's `status` field in `phases/1-skill-creator/index.json` and emits the two-line HTML-comment marker per the pinned template.
- Active hooks during build: `tdd-guard`, `bash-guard`, `secret-scan` (R), `slop-detector`, `stop-verify`.
- After all 5 steps reach `status: completed`, the skill-creator + plugin-creator sub-modes are shipped: a CLI that takes `--mode=skill_create|plugin_create` and emits dual-runtime skill or plugin artifacts, registered natively in both CC and Codex.

Hand-off artifact: `.dev-kit/hand-off/plan→build.md` (this directory).

## Builds on prior phase: 0-mvp (carry-forward)

- 0-mvp's `src/schema/questions.py` is reused for `mode=plugin_create`; do NOT modify.
- 0-mvp's `src/assembler/plan.py` is reused for `mode=plugin_create`; do NOT duplicate.
- 0-mvp's `src/emitter/codex.py` is the template engine for `mode=plugin_create`; this phase EXTENDS it via `src/emitter/plugin_skill_bundle.py`, not forks.
- The 0-mvp adapter install (`register_cc` + `codex_install` from steps 4, 5) is the bootstrap point — phase1 step 3 EXTENDS these with two new siblings `register_cc_skill` and `register_codex_skill`, not replaces.
- 0-mvp non-goal 2 (zero `dev-kit` text references) extends to phase1 — none in any emitted artifact, src comment, docstring, fixture, or test.
- 0-mvp non-goal 1 (no log emission) extends to phase1 — no log lines emitted by any new module.
- The dual-runtime parity test (`tests/e2e/test_dual_runtime_parity.py`) is the kill condition defined in Gate 2 cycle 2 — if CC and Codex SKILL bodies diverge byte-for-byte beyond the locked frontmatter divergence, the build is blocked.
