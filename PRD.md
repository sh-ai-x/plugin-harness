---
prd: plugin-harness
cycle: 1
decided: 2026-07-08
branch: feat/plugin-harness-prd
status: ready-for-build
---

# PRD — plugin-harness

## 1. Frame

**Idea (1-line).** Interview-driven **plugin-of-plugins** harness. An AI assistant that runs a 6-question guided interview and produces a working plugin for *both* Claude Code (slash-commands / skills / MCP) and OpenAI Codex (`.codex-plugin/plugin.json` + skills + `.mcp.json`) from a single set of answers.

**Customer.** Internal developer team. First user = a teammate; the smallest thing they'd click = "finish my first skill on a real plugin via the harness" (Socratic Q2 PASS).

**Situation.** No current tool — plugin authors wing it from Codex's and Claude's spec docs. Specs are dense and span two vendor formats + MCP wiring, so first-cut plugins are typically under-scoped and unverifiable.

**Cause (best-effort).** Docs-first surface area with no PM-style interview forcing authors to articulate "what / who / situation / why / verification" before scaffolding.

**Cost of inaction.** Continued author-time tax + low-quality submissions. (User signal: "그냥진행" — proceed without hard deadline.)

## 2. Acceptance criteria

| # | AC | Verifiable by |
|---|---|---|
| AC1 | **Interview finishes → working plugin.** Author answers the 6 questions in either Claude Code or Codex; harness scaffolds both targets' plugin manifests plus ≥1 inner skill. | Files-on-disk + manifest validation (Claude `plugin.json` + Codex `.codex-plugin/plugin.json` + matched `skills/<n>/SKILL.md`). |
| AC2 | **Marketplace registration → searchable.** After registration, the plugin AND its skills are queryable by name + description in their marketplace. | Author confirms via search; harness emits a registration checklist item. |
| AC3 | **Skill-invoke time → behaves as designed.** When a user invokes the skill, runtime matches the intent stated during the interview. | Harness auto-generates ≥1 scenario test under `tests/scenario/<skill>.md` derived from interview answers. |

## 3. Non-goals (with breach response)

1. **No IDE integration.** Claude Code (CLI/chat) and Codex (CLI / agent SDK) only.
2. **No store auto-publish.** Harness produces publishable artifacts; it does not call marketplace publish APIs.
3. **No submission.zip packaging.** Deliverable is the author's repo with manifests + skills committed in-tree, not a zipped bundle.

**Breach response.** Phase-2/3 PRs that violate the above get rejected at review with redirect to a separate `<type>/<scope>-<slug>` branch.

## 4. Socratic interview summary

| # | Question | Answer | Verdict |
|---|---|---|---|
| Q1 | "What breaks if you ship nothing for 2 weeks?" | — (best-effort) | best-effort |
| Q2 | "Who is the first user + smallest click?" | 1 teammate, first skill on a real plugin | **PASS** |
| Q3 | "Cheapest invalidating experiment (≤1 wk, ≤1 person-day)?" | Manual 6-Q script with one teammate (~3-4h) | **PASS** |
| Q4 | "What did you try that didn't work + lesson?" | — (best-effort) | best-effort |
| Q5 | "If this works, what's next + why?" | Marketplace indexer / registry (so AC2 becomes automated) | **PASS** |

**Passes: 3/5 firm (≥3 required) → gate met.** Two best-effort slots accepted per plan-ralph: `Q1`, `Q4`.

## 5. Evidence

| Source | URL | Role |
|---|---|---|
| Codex plugin overview | https://developers.openai.com/codex/plugins | Defines the plugin manifest model. |
| Codex build guide | https://developers.openai.com/codex/plugins/build | Submission shape + artifact layout (README, src/, logs/). |
| Codex skill authoring | https://developers.openai.com/codex/skills | SKILL.md rules — applied verbatim to inner skills. |
| Claude Code skills convention | project memory + parent dev-harness-kit | Mirror of Codex SKILL.md; cross-validated. |

Source count = **4** ≥ 3 — evidence gate PASS.

## 6. Phases

Decomposed into `phases/plugin-harness/`. See `phases/plugin-harness/index.json` + per-step files.

| Phase | Title | Steps |
|---|---|---|
| A | Interview flow | step1 = question scaffolder; step2 = answer recorder + decision-log writer |
| B | Dual-target manifest generator | step3 = Claude manifest; step4 = Codex manifest; step5 = MCP shape adapter |
| C | Skill + scenario test generator | step6 = SKILL.md author; step7 = scenario test authoring from interview Q1+Q4 |
| D | Verifiability | step8 = AC1/2/3 self-check (manifest-valid + scenario-run) |

Total: **8 steps**. Each step = one cycle in `dev-kit:build`.

### Phase boundary conditions (entering each step)

- A→B: 6 answers collected + written to `.prd/interview-<plugin-slug>.md`.
- B→C: both manifests emitted + pass `manifest-valid` scenario.
- C→D: ≥1 SKILL.md + ≥1 scenario test on disk, scenario dry-run returns expected intent key.
- D→hand-off: AC1/2/3 status board shows GREEN for AC1 + AC3, AC2 is "manual-pending" (registration is user-side).

### Methodology (per CLAUDE.md §2)
- default = `tdd` (MUST-48).
- For each step: red (failing contract test) → green (impl) → refactor.
- Verification artifacts: contract per manifest, scenario per skill, scenario per AC.
