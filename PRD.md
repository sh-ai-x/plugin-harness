# PRD — plugin-harness (1-skill-rewrite)

> Plan stage output. Phase: `1-skill-rewrite`. Parent phase: `0-mvp` (see `PRD-0-mvp.md` for the original implementation plan). Methodology: tdd. Worktree: `.claude/worktrees/plugin-harness-skill-rewrite`. Branch: `feat/plugin-harness-skill-rewrite`. Date: 2026-07-14.

## §1 Frame

- **goal**: Refactor plugin-harness so its 5-question interview, idea-plan assembly, and Codex-layout emit are implemented **natively as Claude Code + Codex skills** — drop the Python CLI indirection (`python -m src.engine.cli`) and the `cc-adapter` / `codex-adapter` thin-wrapper layer. Each runtime's `SKILL.md` owns its own prompt-driven interview flow; both skills share a JSON resource export of the schema + emit templates so the skill prompt chain is fully self-contained.
- **target_user**: Plugin author who already runs plugin-harness via `/plugin-harness new` (CC) or the Codex equivalent and finds the Python-CLI indirection inconvenient — they want skill-native authoring where the LLM reasons over the interview transcript end-to-end instead of shelling to Python between every question. Same dual-persona cohort as 0-mvp (marketing manager / PM at a 3-person growth team, no coding background), with the power-user subset (developer-advocate authors who hack on the harness itself) as a secondary audience.
- **situation**: Today `phases/0-mvp/` ships a Python core (`src/engine/cli.py`, `src/schema/`, `src/emitter/`) plus two adapter layers (`src/adapter/cc.py`, `src/adapter/codex.py`) that install thin SKILL.md files pointing at `python -m src.engine.cli`. Three concrete frictions: (1) author must have a Python runtime to use the harness at all; (2) the SKILL.md can't reason over previous answers — it shells to Python between every question, breaking context continuity; (3) updating interview logic requires editing Python + redeploying, not editing the SKILL.md in place.
- **scope**: skill-rewrite only — re-implement interview/assembly/emit as CC + Codex native skills. Keep the 5-question schema and the Codex plugin-layout emit format identical (those are the user-facing contracts the harness promises).
- **direction**: dual-runtime (CC + Codex). The user message said "CC skill OR Codex skill" but the existing product is dual-runtime; collapsing to one runtime would break the `0-mvp` PRD §1 commitment and the dual-runtime emit validator. Direction slot is marked `<unspecified>` for explicit user override if they want single-runtime.

## §2 Validate

- **evidence_count**: 3 (PASS, threshold ≥3)
  1. **Repo state** — `phases/0-mvp/index.json` shows current architecture is `src/engine/cli.py` Python core + `cc-adapter` + `codex-adapter` thin wrappers. Different origin: existing code artifact.
  2. **User first-person** — "현재 플러그인을 만드는 것을 도와주는 하네스인데 불편한거 같아. claude code skill이나 codex skil로 구현방식을 해줬으면 좋겠네." Different origin: direct user signal.
  3. **Existing SKILL.md thinness** — `phases/0-mvp/step5.md` documents the codex-adapter SKILL.md as a thin wrapper that shells to `python -m src.engine.cli`. Different origin: existing skill artifact.
- **value_score**: 33.33 (PASS, threshold ≥3.0) — `$2,000 LTV × 500 reachable users / $30,000 cost = $33.33` (same envelope as 0-mvp — refactor scope, not new product surface).
- **ambiguity_score**: 3 (PASS, threshold ≤3) — narrowed 10 → 3 over 3 cycles (user / metric / kill knobs resolved with user-implicit defaults; user replied "do it" → blanket-accept of inferred defaults per skill rule "If any field is empty, ask once, then proceed with `<unspecified>`").
- **convergence**: PASS. Detail in `.prd/decision-log.md` and `.dev-kit/loop-log.json`.

## §3 Non-Goals

| # | Non-goal | Rationale | Breach response |
|---|---|---|---|
| 1 | Drop the Python core (`src/engine/`, `src/schema/`, `src/emitter/`) entirely. | Schema validator + Jinja2 templates are still useful as library code; the SKILL.md wraps these, doesn't replace them. The user's pain is the *adapter indirection*, not the Python library. | If a PR deletes `src/` outright, reject and require keeping the core as a library the skill can import (or call via stdlib if needed). |
| 2 | Change the 5-question schema or order. | The question set is the user-facing contract; changing it breaks every plugin already scaffolded with 0-mvp and any downstream consumer depending on the schema. | If a reviewer asks to add / remove / reorder a question, defer to a separate `2-schema-v2` PRD. |
| 3 | Switch emit format from Codex plugin layout. | `PRD-0-mvp.md` §1 commits to Codex layout (`src/.codex-plugin/plugin.json`, `src/skills/<name>/SKILL.md`, `src/.mcp.json`, `README.md`); changing emit format is a different product. | If a PR proposes CC-layout or another format, route to a separate PRD. |
| 4 | Single-runtime collapse (CC-only or Codex-only). | User message said "CC skill OR Codex skill" but existing product is dual-runtime and the dual-runtime emit validator (`src/emitter/validator.py`) requires both. Direction slot in §1 is `<unspecified>` for explicit override. | If a PR collapses to one runtime without explicit user override, reject and require the user to amend §1 first. |

## §4 Phase Plan

5 steps in `phases/1-skill-rewrite/` (decomposition ordered dependency-first: skills → shared resources → kill-condition → e2e proof).

Source of truth: `phases/1-skill-rewrite/index.json`.

| step | name | title |
|---|---|---|
| 0 | cc-skill-native | CC SKILL.md re-authored as native interview driver |
| 1 | codex-skill-native | Codex SKILL.md re-authored as native interview driver |
| 2 | shared-resources | Schema + emit templates exported as JSON resources loadable by both skills |
| 3 | validator-keep | Validator (src/emitter/validator.py) kept as kill-condition verifier |
| 4 | e2e-no-python-shells | E2E test asserting zero `python -m src.engine.cli` invocations during interview |

Parent phase context: `phases/0-mvp/` (see `PRD-0-mvp.md`).

## §5 Acceptance Criteria

Representative subset of per-step AC commands from `phases/1-skill-rewrite/step<N>.md`. Each step file owns its own full AC inventory (24 ACs across 5 steps). The build runner reads both PRD §5 (representative subset) and the per-step files (full inventory); mismatch on any row listed here fails the build.

| step | representative AC | maps to |
|---|---|---|
| 0 (cc-skill-native) | AC1 — `! grep -F "python -m src.engine.cli" .claude/skills/plugin-harness/SKILL.md` → exit 0 | `phases/1-skill-rewrite/step0.md` AC1 |
| 0 (cc-skill-native) | AC3 — `pytest tests/ -q` → exit 0 (no regression on 0-mvp AC) | `phases/1-skill-rewrite/step0.md` AC3 |
| 1 (codex-skill-native) | AC3 — `diff` of question blocks between CC and Codex SKILL.md → exit 0 (question content matches) | `phases/1-skill-rewrite/step1.md` AC3 |
| 1 (codex-skill-native) | AC5 — `pytest tests/ -q` → exit 0 (CC + Codex combined) | `phases/1-skill-rewrite/step1.md` AC5 |
| 2 (shared-resources) | AC2 — `diff -r src/emitter/templates/codex/ resources/templates/` → exit 0 (byte-identical templates) | `phases/1-skill-rewrite/step2.md` AC2 |
| 2 (shared-resources) | AC3 — idempotency hash diff → exit 0 | `phases/1-skill-rewrite/step2.md` AC3 |
| 3 (validator-keep) | AC1 — `python scripts/verify_emit.py tests/fixtures/sample_plugin/` → exit 0 (validator passes reference fixture) | `phases/1-skill-rewrite/step3.md` AC1 |
| 3 (validator-keep) | AC2 — `! python scripts/verify_emit.py tests/fixtures/malformed_plugin/` → exit 0 (negative test) | `phases/1-skill-rewrite/step3.md` AC2 |
| 4 (e2e-no-python-shells) | AC3 — `pytest tests/e2e/test_skill_rewrite.py -q -s 2>&1 \| grep -c "python -m src.engine.cli"` → value `0` | `phases/1-skill-rewrite/step4.md` AC3 |
| 4 (e2e-no-python-shells) | AC4 — `diff -r` between emitted Codex-layout files and `tests/fixtures/sample_plugin/` → exit 0 (byte-equivalent emit) | `phases/1-skill-rewrite/step4.md` AC4 |
| 4 (e2e-no-python-shells) | AC6 — `pytest tests/ -q` → exit 0 (full suite including e2e) | `phases/1-skill-rewrite/step4.md` AC6 |

## §6 Hand-off

Next invocation: `/dev-kit:build` — converts `phases/1-skill-rewrite/step<N>.md` into per-step implementation via harness-runner.

Build must satisfy ALL step AC files (`step0.md`..`step4.md`), not just the PRD §5 representative subset; the runner reads both. Step-0 AC0..AC4, step-1 AC0..AC5, step-2 AC0..AC5, step-3 AC0..AC5, step-4 AC0..AC6 — total 25 ACs.

Kill-condition anchor: step-3 AC1 + AC2 (validator passes reference fixture, fails malformed fixture) and step-4 AC3 + AC4 (e2e proves zero-Python-shell interview + byte-equivalent Codex-layout emit on both runtimes).

Hand-off detail: `.dev-kit/hand-off/plan→build.md`.