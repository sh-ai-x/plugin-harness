# PRD — plugin-harness

> Plan stage output. Methodology: tdd. Worktree: `.claude/worktrees/plan-v3`. Branch: `plan/plugin-harness-v3`. Date: 2026-07-08.

## §1 Frame

- **goal**: Ship a dual-runtime (Claude Code + Codex) plugin-harness that interviews the user via 5 fixed questions (what/who/where · why-this-problem · how-it-works · AI-usage · how-verified) and emits a final idea plan, structured per the Codex plugin layout (`src/.codex-plugin/plugin.json`, `src/skills/<name>/SKILL.md`, `src/.mcp.json`, `README.md`).
- **target_user**: marketing manager at a mid-size SaaS company (50–200 employees), 3-person growth team, no coding background, mandated to operationalize AI for the team's daily workflow. Today uses ChatGPT web + Notion AI in parallel, 5+ hours/week context-switching, no way to ship a team plugin. Second-wave persona: product manager at a 3-person growth team, also non-coder.
- **situation**: plugin authors hand-roll `plugin.json`, `SKILL.md`, and `.mcp.json` directly from docs, with no guided ideation pass — they jump from idea to file edits, skipping the "what/who/why/how/AI/verify" reasoning the harness demands. No-code plugin authoring is the gap.

## §2 Validate

- **evidence_count**: 3 (PASS, threshold ≥3)
  1. first-person — the user is the first user
  2. prior failed attempt — plan #7 merged without the interview-driven ideation layer
  3. analogue product — ChatGPT Custom GPTs / Claude Projects prove demand for "anyone-configures-an-AI-for-a-team"
- **value_score**: 33.33 (PASS, threshold ≥3.0) — `$2,000 LTV × 500 reachable users / $30,000 cost = $1,000,000 / $30,000`
- **ambiguity_score**: 3 (PASS, threshold ≤3) — narrowed 10 → 3 over 3 cycles (scope, kill, second-persona knobs)
- **convergence**: PASS. Detail in `.prd/decision-log.md` and `.dev-kit/loop-log.json`.

## §3 Non-Goals

| # | Non-goal | Rationale | Breach response |
|---|---|---|---|
| 1 | Skip logging this stage | user will configure separately | route any log PR to a separate "logging" PRD |
| 2 | Zero `dev-kit` text references in any artifact | harness is a standalone plugin, not an extension | replace with neutral phrasing ("the runner", "the build engine") or move to docs/README out of the plugin layout |
| 3 | Commercial / marketplace plugin out of scope | different product; requires review + signing + marketplace metadata | split into a separate "publish" PRD with its own gates |
| 4 | Open-source project plugin out of scope | user explicitly chose team plugin over the OS-or-team choice | reject OS-project PRs and split |
| 5 | GUI / web wizard out of scope | CLI is sufficient for the target persona | if GUI is added, require a CLI fallback for automation |

## §4 Phase Plan

7 steps in `phases/0-mvp/` (decomposition ordered dependency-first: data → engine → assembler → emitter → adapters → e2e).

Source of truth: `phases/0-mvp/index.json`.

| step | name | title |
|---|---|---|
| 0 | question-schema | 5-question schema + interview state |
| 1 | interview-engine | Interview engine (2 modes) |
| 2 | idea-plan-assembler | Idea-plan assembler |
| 3 | dual-runtime-emitter | Dual-runtime plugin emitter |
| 4 | cc-adapter | Claude Code adapter |
| 5 | codex-adapter | Codex adapter |
| 6 | e2e-smoke | E2E test + cross-runtime smoke test |

## §5 Acceptance Criteria

Representative subset of per-step AC commands from `phases/0-mvp/step<N>.md`. Each step file owns its own full AC inventory (29 ACs across 7 steps). The build runner reads both PRD §5 (representative subset) and the per-step files (full inventory); mismatch on any row listed here fails the build. Steps 1, 2, 4, 5 also have full per-step ACs that are NOT mirrored in this table; see their step files for the full contract.

| AC# | Step | Command | Source |
|---|---|---|---|
| AC1 | step 0 | `python -m pytest tests/test_question_schema.py -v → exit 0 (5 questions present)` | `phases/0-mvp/step0.md` AC1 |
| AC2 | step 0 | `python -m pytest tests/test_interview_state.py -v → exit 0` | `phases/0-mvp/step0.md` AC2 |
| AC3 | step 3 | `python -m pytest tests/test_emitter.py -v → exit 0` | `phases/0-mvp/step3.md` AC1 |
| AC4 | step 6 | `bash scripts/e2e.sh → exit 0` | `phases/0-mvp/step6.md` AC1 |
| AC5 | step 6 | `grep -r "dev-kit" src/ scripts/ tests/ → exit 1` (no matches — non-goal b; post-emit output_dir now also covered per step 6 AC5) | `phases/0-mvp/step6.md` AC5 |

## §6 Hand-off

Next invocation: **`/dev-kit:build`**.

Build stage expectations:
- TDD methodology (per `CLAUDE.md` §2, current methodology = tdd). Tests first.
- Iron Laws L1 (no prod code without verification artifact) + L2 (no fix without reproduction) + L3 (no completion claim without quoted exit code / test count / build log) + L4 (no TODO/FIXME) + L5 (no option lists when not asked) all active.
- Each step in `phases/0-mvp/step<N>.md` runs under the harness-runner. Sub-agent updates the step's `status` field in `index.json` and emits the two-line HTML-comment marker per the pinned template.
- Active hooks during build: `tdd-guard`, `bash-guard`, `secret-scan` (R), `slop-detector`, `stop-verify`.
- After all 7 steps reach `status: completed`, the dual-runtime plugin-harness MVP is shipped: a CLI that interviews the user via 5 fixed questions, assembles the idea plan, and emits a Codex-layout plugin that installs identically in Claude Code and Codex.

Hand-off artifact: `.dev-kit/hand-off/plan→build.md` (this directory).
