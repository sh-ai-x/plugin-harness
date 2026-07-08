# PRD — plugin-harness

> Plan stage output. Methodology: tdd. Worktree: `feat/plugin-harness`. Date: 2026-07-08.

## 1. Frame

**Idea**: A standalone plugin (plugin-harness) that authors new dual-runtime (Claude Code + Codex) plugins via a 5-question interview. Two input modes — user-driven (mode A) and AI-research-driven (mode B).

**Customer**: Plugin authors who need to ship dual-runtime plugins. First user = repo owner (you). Second user archetype = first-time Codex plugin contestant. Third user archetype = hackathon team that needs a working plugin by demo.

**Situation**: Author has an idea (or a company to target), wants to ship a plugin to both Claude Code and Codex, but must hand-roll the 5-question interview, dual plugin.json layouts, and verbatim logs — with no tool to enforce cross-runtime consistency.

**Cause**: Existing tools (cookiecutter-style generators) produce code but not the 5 questions or logs. Manual porting between runtimes is error-prone. Log↔plugin↔questionnaire drift is the #1 cause of build-time inconsistency.

**Cost**: Hours of manual work per plugin; silent runtime breaks from field-name diffs; smoke-test failures from drift; abandonment of plugin ideas that "are too much boilerplate to ship."

## 2. Evidence

| # | Source | URL | Independent | Use |
|---|---|---|---|---|
| 1 | Codex plugin overview | https://developers.openai.com/codex/plugins | yes (official) | 5-question format + plugin.json layout |
| 2 | Codex plugin build | https://developers.openai.com/codex/plugins/build | yes (official) | plugin.json + MCP integration |
| 3 | Codex skills spec | https://developers.openai.com/codex/skills | yes (official) | SKILL.md structure |
| 4 | User's prior CC→Codex port (Q4 grill-me) | first-hand | first-person | validates dual-runtime pain |

**Rubric**: 4 independent sources, official specs + first-hand experience. **PASS** (≥3 required, rubric ≥ 75).

## 3. Diff / Profit

**Alternatives considered**:

1. **Manual approach** — author hand-writes 5-question responses, plugin code, `logs/`. No tooling.
2. **Existing plugin generators** (cookiecutter, npm init, Yeoman) — produce code scaffolding but not the 5-question interview or logs.
3. **plugin-harness** (this project) — 2 modes, dual-runtime, log↔plugin↔questionnaire consistency check.

**Differentiation (customer language)**:
- "I can either fill in 5 questions or just give an idea — the tool researches the rest."
- "I get a plugin that works in Claude Code AND Codex, not just one."
- "My logs and plugin can't drift — the consistency check catches it before the smoke test."

**Unit margin**: positive. Each plugin shipped saves hours of manual work + reduces rejection rate. Tool itself is a one-time build, reusable across many plugins.

## 4. Non-Goals

1. **Extending or modifying dev-kit** — dev-kit is the dev environment, not the product.
   - **Breach response**: if a PR adds dev-kit features, reject and split into a separate dev-kit PR.
2. **Auto-publish to plugin marketplaces** — manual review required for quality control.
   - **Breach response**: if auto-publish is added, gate behind explicit opt-in and dry-run preview.
3. **GUI / web wizard** — CLI is sufficient.
   - **Breach response**: if GUI is added, require a CLI fallback for automation.
4. **Non-md skill formats** (binary skills) — Codex submission requires md/txt/json/jsonl.
   - **Breach response**: if binary skills are needed, ship as separate `.bin` asset with `.md` manifest.

## 5. Socratic interview summary

```
Q1 [PASS]: failure mode — no plugin-creation tool exists, every author re-rolls the same boilerplate
Q2 [PASS]: first user — you; smallest action `/dev-kit:plan-plugin <idea-or-company>` → 5-question plan + dual-runtime plugin
Q3 [PASS (sharpen×1)]: kill-shot — interview + AI research + plugin generation, ≤2 person-days, test on 1 real idea
Q4 [PASS]: prior try — wrote CC skill, ported to Codex; learned dual plugin.json is hand-ported and error-prone
Q5 [PASS]: next build — plugin dry-run tester (runs plugin in both runtimes, diffs behavior)
```

Passes: **5/5**.

## 6. Phases

See `phases/plugin-harness/index.json` for the canonical phase manifest. Step files in the same directory.

| # | Step | Summary |
|---|---|---|
| 1 | spec the 5 questions (Codex format) | Define 5 questions as a stable contract |
| 2 | implement 5-question interview form (mode A) | User-driven mode: user fills the 5 questions |
| 3 | implement AI web-research fill (mode B) | AI-driven mode: AI searches web, fills with evidence |
| 4 | implement Claude Code plugin generation | Emit valid CC skill + .mcp.json |
| 5 | implement Codex plugin generation | Emit valid Codex plugin (plugin.json + SKILL.md) |
| 6 | implement log↔plugin↔questionnaire consistency check (BLOCKING) | Catch drift before smoke test; blocks step 7 on hard-fail |
| 7 | end-to-end smoke test (kill-shot) | 1 real idea, ≤2 person-days, install in both runtimes |

## 7. Acceptance criteria

1. `/dev-kit:plan-plugin --mode <A|B> <idea-or-company>` runs the 5-question interview (mode A) OR web-research + auto-fill (mode B)
2. Output installs cleanly in Claude Code AND Codex as a plugin (no dev-kit runtime dep)
3. Verbatim AI conversation log captured to `logs/` (md/txt/json/jsonl) by the producer step (step 2 mode A, step 3 mode B)
4. Generated plugin source tree matches Codex spec format (`.codex-plugin/plugin.json` + `skills/<name>/SKILL.md`)
5. logs↔plugin↔questionnaire consistency check (step 6) passes BEFORE smoke test (step 7); hard-fail blocks the smoke test
