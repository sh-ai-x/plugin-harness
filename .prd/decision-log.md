# Decision log — plugin-harness plan

> Cumulative log of all plan decisions. Last update: 2026-07-08.

## Gate 1 — frame-problem (PASS)

- **Idea**: standalone plugin (plugin-harness) that authors dual-runtime (CC + Codex) plugins via 5-question interview
- **Customer**: plugin authors; first user = repo owner
- **Situation**: no good tool exists; author hand-rolls 5 questions, dual plugin.json layouts, logs, submission.zip
- **Cause**: existing tools (cookiecutter, npm init) produce code but not the 5 questions or logs; manual porting is error-prone
- **Cost**: hours of manual work per plugin, silent runtime breaks, submission rejections

## Gate 2 — evidence-gate (PASS, 4 sources)

| # | Source | URL | Independent | Use |
|---|---|---|---|---|
| 1 | Codex plugin overview | https://developers.openai.com/codex/plugins | yes (official) | 5-question format + submission.zip layout |
| 2 | Codex plugin build | https://developers.openai.com/codex/plugins/build | yes (official) | plugin.json + MCP integration |
| 3 | Codex skills spec | https://developers.openai.com/codex/skills | yes (official) | SKILL.md structure |
| 4 | User's prior CC→Codex port (Q4) | first-hand | first-person | dual-runtime pain evidence |

Rubric: 4 independent sources. **PASS** (≥3 required, rubric ≥ 75).

## Gate 3 — diff-profit-gate (PASS)

**Alternatives considered**:
1. Manual approach — hand-write everything
2. Existing plugin generators — code scaffolding, no 5-questions, no logs
3. plugin-harness (this) — 2 modes, dual-runtime, consistency check

**Differentiation (customer language)**:
- "I can either fill in 5 questions or just give an idea — the tool researches the rest."
- "I get a plugin that works in Claude Code AND Codex, not just one."
- "My logs and plugin can't drift — the consistency check catches it before submission."

**Unit margin**: positive (one-time build, reusable across many plugins, saves hours per plugin).

## Gate 4 — non-goals (4 items, all with breach-response)

1. **Extending or modifying dev-kit** — dev-kit is the dev env, not the product
   - Breach: PR adds dev-kit features → reject, split into separate dev-kit PR
2. **Auto-publish to plugin marketplaces** — manual review required
   - Breach: opt-in + dry-run preview gate
3. **GUI / web wizard** — CLI is sufficient
   - Breach: if GUI added, require CLI fallback for automation
4. **Non-md skill formats** — Codex submission requires md/txt/json/jsonl
   - Breach: binary skills ship as `.bin` + `.md` manifest

## Gate 5 — socratic-deepen (5/5 PASS)

- Q1 [PASS]: failure mode — no plugin-creation tool exists
- Q2 [PASS]: first user = you; smallest action `/dev-kit:plan-plugin --mode <A|B> <idea-or-company>`
- Q3 [PASS (sharpen×1)]: kill-shot — interview + AI research + plugin gen, ≤2 person-days
- Q4 [PASS]: prior try — wrote CC skill, ported to Codex; learned dual plugin.json is hand-ported
- Q5 [PASS]: next build — plugin dry-run tester

## Gate 6 — phase-decompose (PASS)

7 steps (zip assembly dropped per user scope change), see `phases/plugin-harness/index.json`.

## Gate 7 — seed-convergence (PASS)

Two independent seed passes produced the same 7-step phase decomposition. Per-step titles and acceptance criteria match across passes. Similarity ≥ 0.85. **PASS**.

## Gate 8 — prd-writer (PASS)

PRD.md emitted with 6 sections + 7th acceptance-criteria section. Hand-off written to `.dev-kit/hand-off/plan→build.md`. All 5 DoD conditions met:

1. ✓ All 6 sections present
2. ✓ Socratic 5/5 PASS recorded
3. ✓ `phases/plugin-harness/index.json` exists with 7 steps
4. ✓ Hand-off file written
5. ✓ Decision log cumulative across all gates
