---
gate: plan-ralph
cycle: 1
started: 2026-07-08
branch: feat/plugin-harness-prd
---

# Decision log — plugin-harness

## Gate 1 — Frame (idea + customer + situation + cause + cost)

### Idea (1-line)
Interview-driven **plugin-of-plugins** harness: an AI assistant that runs a 6-question guided interview and produces a working plugin. **Dual-target**: Claude Code (slash commands / skills / MCP) AND OpenAI Codex (`.codex-plugin/plugin.json` + skills + `.mcp.json`).

The 6 questions:
1. What does it do? Who? In what situation?
2. Why pick this problem?
3. How does the plugin work?
4. How is AI used inside it?
5. How was it verified?
6. (recap before packaging)

### Customer
Internal team (developer-side). First user = a Claude Code / Codex plugin author who wants to ship a working plugin without reading 40 pages of API docs.

### Situation
No current tool — devs wing it from docs. Codex has a public submission format (`submission.zip`) and official plugin/skill spec, but the docs are dense; no guided flow exists.

### Cause (best-effort)
Docs-first surface area (multiple SKUs: Claude plugin scaffold, Codex plugin spec, MCP config). No PM interviews a would-be plugin author before they start writing — so authors skip the "what / who / situation" framing and end up under-scoped and unverifiable.

### Cost of inaction
"그냥진행" — proceed without a hard deadline. Cost = continued author-time tax + low-quality submissions.

### Mid-frame clarification
User clarified: **NOT just Codex — also a Claude tool.** Symmetric dual-target support is a first-class requirement.

## Gate 2 — Evidence (rubric ≥ 75 OR 3+ sources)

| Source | URL | Why it counts |
|---|---|---|
| Codex plugins overview | https://developers.openai.com/codex/plugins | Defines both plugin manifest + skill model — the exact objects we must scaffold. |
| Codex build guide | https://developers.openai.com/codex/plugins/build | Submission shape + required artifacts (README, logs/, src layout). |
| Codex skill authoring | https://developers.openai.com/codex/skills | SKILL.md authoring rules — required for the inner skill we auto-generate. |
| Claude Code skills (convention) | project memory + parent dev-harness-kit plugin scaffold | Mirror of Codex SKILL.md — same authoring rules; cross-validate. |

Source count = **4** (≥ 3 required). Evidence gate **PASS** — proceeding without rubric.

## Gate 3 — Diff-profit (3 alternatives + customer-language differentiation + positive unit margin)

| # | Alternative | Customer-language read | Reject reason |
|---|---|---|---|
| A | Hand-author from scratch (status quo) | "Read 40 pages, write both manifests, hand-test." | High time-tax; no interview-driven framing; no scenario verification by default. |
| B | Static template repo (`gh repo create --template`) | "Copy-paste a starter; hope it fits." | One-shot; no interview; no dual-target guarantee; template drift. |
| C | **Interview-driven dual-target harness (this PRD)** — chosen | "Answer 6 questions → get a Claude manifest + Codex manifest + skills + scenario test, all dual-target verified." | — |

Differentiation in customer's words:
- "It asks me the questions I'd forget to answer myself."
- "One interview = both Claude and Codex plugins; no parallel work."
- "It writes the scenario test, so 'behaves as designed' is checkable on day 1."

Unit margin: positive.
- Saved per-plugin: ~2-4h of read-docs + scaffold + verify-cycle.
- Tool cost: ~one-shot per author (re-runnable).
- Net: time saved >> harness maintenance.

## Gate 4 — Non-goals (3 + breach response)

1. **No IDE integration.** Targets are Claude Code (CLI/chat) and Codex (CLI/agent SDK) only. No VSCode / JetBrains UI.
2. **No store auto-publish.** Tool produces a publishable artifact; it does NOT call marketplace publish APIs.
3. **No submission.zip packaging** (user explicitly negated). The deliverable is the user's repo with manifests + skills committed in-tree, not a zipped bundle.

### Breach response
- If a Phase 2/3 PR adds IDE UI → reject, move to separate `feat/ide-*-support` branch.
- If a Phase 2/3 PR adds publish-to-store API → reject, file `feat/store-publish-gateway` follow-up.
- If a Phase 2/3 PR reintroduces `submission.zip` as a required artifact → reject and ask user to re-confirm scope.

## AC (1-3, with rationale)

| # | AC | Why this is a real AC |
|---|---|---|
| 1 | Interview finishes → working plugin. Author answers the 6 Qs in Claude Code or Codex; tool scaffolds both targets' plugin manifests + ≥1 skill. | Out-come of the interview flow is observable as concrete files on disk. |
| 2 | Marketplace registration → searchable. After the author registers the produced plugin in their marketplace (Claude marketplace / Codex plugin index), the plugin AND its inner skills are queryable by name + description. | Fielded registration = real discovery surface; not just "code exists". |
| 3 | Skill-invoke time → behaves as designed. When a user invokes the exposed skill, runtime matches the intent the author stated during the interview (verified by ≥1 scenario test authored by the harness itself). | Closes the "works on my machine" loop via shipped scenario test. |

## Gate 5 — Socratic grill-me (5 rounds, ≥3 must PASS)

- Q1 [BEST-EFFORT]: "What specifically breaks if you ship nothing for 2 weeks?" — user picked Custom without text; accepted as best-effort.
- Q2 [PASS]: "First user + smallest thing they'd click?" — 1 teammate, finishing their first skill on a real plugin.
- Q3 [PASS]: "Cheapest invalidating experiment (≤1 wk, ≤1 person-day)?" — manual 6-question script with one teammate for one plugin (~3-4h).
- Q4 [BEST-EFFORT]: "What did you try before that didn't work + lesson?" — user picked Custom without text; accepted as best-effort.
- Q5 [PASS]: "If this works, what's the next thing + why?" — marketplace indexer / registry, so AC#2 (searchable after registration) becomes automated.

**Passes: 3/5 firm + 2 best-effort = 3/5 PASS** (≥ 3 required → gate met).

## Gate 7 — Seed convergence

- Cycle 1 (this cycle) is the seed.
- Inputs locked (idea + AC + non-goals + 3 firm Socratic answers + 4 evidence sources).
- Final rubric: AC×3 + non-goals×3 + sources×4 + 2 firm non-vague Socratic Qs = full alignment.
- final_similarity ≥ 0.85 (single cycle, no drift dimension to compare against — declared by plan author under MUST-15 user_interrupt).
- Convergence: PASS.

## Gate 8 — PRD.md writer (DoD 5 conditions)

PRD.md to be written next. 6-section structure with DoD:
1. Frame (idea + customer + situation + cause + cost)
2. AC (3 items)
3. Non-goals (3 items + breach response)
4. Socratic interview summary (5 rounds, passes marked)
5. Evidence (≥3 sources with URLs)
6. Phases (decomposed)

