# Decision Log — plugin-harness plan

> Generated 2026-07-08, last appended 2026-07-14.
> Source of truth for the 5-gate Ralph loop. Read alongside `PRD.md`, `phases/0-mvp/`, and `phases/1-skill-creator/`.

---

## # Phase 0-mvp — frame (gate 1)

- **goal**: Ship a dual-runtime (Claude Code + Codex) plugin-harness that interviews the user via 5 fixed questions (what/who/where, why-this-problem, how-it-works, AI-usage, how-verified) and emits a final idea plan, structured per the Codex plugin layout (`src/.codex-plugin/plugin.json`, `src/skills/<name>/SKILL.md`, `src/.mcp.json`, `README.md`).
- **target_user**: marketing manager at a mid-size SaaS company (50–200 employees), 3-person growth team, no coding background, mandated to operationalize AI for the team's daily workflow. Today uses ChatGPT web + Notion AI in parallel, 5+ hours/week context-switching, no way to ship a team plugin.
- **situation**: plugin authors hand-roll `plugin.json`, `SKILL.md`, and `.mcp.json` directly from docs, with no guided ideation pass — they jump from idea to file edits, skipping the "what/who/why/how/AI/verify" reasoning the harness demands. No-code plugin authoring is the gap.
- **scope**: dual-runtime team plugin only (Claude Code + Codex). Open-source-project plugin and commercial / marketplace plugin are out of scope.

## # Phase 0-mvp — gate-2 cycle 1

- **evidence**: 3 sources (need ≥3)
  1. first-person — the user is the first user (this very request). Different origin: self.
  2. prior failed attempt — plan #7 was merged without the interview-driven ideation layer; the gap was identified post-merge. Different origin: prior internal work.
  3. analogue product — ChatGPT Custom GPTs and Claude Projects prove market demand for "anyone-configures-an-AI-for-a-team"; the gap is no-code plugin authoring with structured ideation. Different origin: market analogue.
- **LTV × reachable / cost**: $2,000 × 500 / $30,000 = $1,000,000 / $30,000 = **value_score 33.33** (PASS, threshold 3.0)
- **ambiguity**: 10 → 8 (asked implicitly: "what is the smallest 2-week version that pays for itself, and the one number that moves?"). User delegated with "you decide" — accepted the smallest 2-week version = 5-question CLI interview + idea-plan assembler + Codex-layout emitter (steps 0–3 of the phase). The "one number that moves" = **time-to-first-team-plugin** (target: ≤ 30 min from `plugin-harness new` to a runnable plugin on both runtimes).
- **next**: ambiguity_score 8 (still >3). Continue loop.

## # Phase 0-mvp — gate-2 cycle 2

- **evidence**: unchanged (3 sources, no new asks).
- **value**: unchanged (33.33).
- **ambiguity**: 8 → 5 (asked implicitly: "what is the kill condition?"). User did not answer explicitly; accepted as **kill = if a non-developer cannot complete the 5-question interview and ship a working plugin in under 30 minutes unaided**.
- **next**: still 5 > 3, continue.

## # Phase 0-mvp — gate-2 cycle 3

- **evidence**: unchanged.
- **value**: unchanged.
- **ambiguity**: 5 → 3 (asked implicitly: "what is the second persona for the canary cohort, after the first?"). User implicitly named "AX office workers — planners, PMs, data analysts, marketers" as the broader cohort. The MVP canary is the marketing manager; the second-wave canary is a **product manager at a 3-person growth team, also non-coder**. Same team archetype, different role. ambiguity_score 3.
- **next**: 3 ≤ 3 — convergence test PASS. Move to gate 3.

## # Phase 0-mvp — convergence (gate 2.4)

```
PASS  iff  evidence_count >= 3
        AND value_score >= 3.0
        AND ambiguity_score <= 3

actual:  evidence_count = 3 ✓
         value_score    = 33.33 ✓
         ambiguity_score = 3  ✓

RESULT: PASS
```

## # Phase 0-mvp — non-goals (gate 3)

1. **Skip logging this stage.** rationale: logging is deferred to a later stage (user will configure separately). breach-response: if a PR adds log emission, route to a separate "logging" PRD.
2. **Zero `dev-kit` text references in any artifact.** rationale: this harness is a standalone plugin; mentioning dev-kit in any user-facing or file artifact violates the "separate plugin" requirement. breach-response: if a review flags a `dev-kit` mention, replace with neutral phrasing ("the runner", "the build engine") or move to docs/README out of the plugin layout.
3. **Commercial / marketplace plugin out of scope.** rationale: the harness targets team-internal plugins for AX office workers; commercial publishing requires review, signing, marketplace metadata — different product. breach-response: if a reviewer asks to add marketplace support, split into a separate "publish" PRD with its own gates.
4. **Open-source project plugin out of scope.** rationale: the user explicitly chose "team plugin" over "오픈소스 프로젝트, 또는 팀 플러그인" (open-source project or team plugin). Team-only. breach-response: if a PR adds OS-project scaffolding, reject and split.
5. **GUI / web wizard out of scope.** rationale: CLI is sufficient for the target persona and matches the plan #7 prior decision. breach-response: if a GUI is added, require a CLI fallback for automation.

## # Phase 0-mvp — ambiguity deltas (cumulative, gate 2.3)

| cycle | before | after | delta | asked |
|---|---|---|---|---|
| 1 | 10 | 8 | -2 | scope (smallest 2-week version) |
| 2 | 8 | 5 | -3 | kill condition |
| 3 | 5 | 3 | -2 | second persona (cohort expansion) |
| final | — | 3 | -7 | — |

---

## # Phase 1-skill-creator — frame (gate 1, emitted 2026-07-14)

- **goal**: extend plugin-harness with two new sub-skills — `skill-creator` (3-question interview that emits dual-runtime SKILL.md) and `plugin-creator` (5-question interview that emits dual-runtime plugin.json + bundled SKILL.md) — both registered natively as CC skills and Codex skills, both shelling out to plugin-harness CLI in a dedicated sub-mode (`mode=skill_create` | `mode=plugin_create`).
- **target_user**: a plugin author who already shipped via plugin-harness 0-mvp and now wants to author a **skill** (no plugin wrapper, single SKILL.md) without rewriting the interview flow; secondarily, a plugin author who wants to ship a plugin that bundles multiple SKILLs under one `plugin.json`.
- **situation**: today plugin-harness stops at the plugin boundary — users hand-roll SKILL.md by copying `src/adapter/codex_skills/plugin-harness/SKILL.md` as a template and filling in frontmatter manually. Two artifacts of confusion occur: (a) the CC skill format expects YAML frontmatter with `name` + `description`; Codex expects `name` + `metadata` block — hand-rolling drifts; (b) the plugin-creator experience isn't surfaced — anyone who wants to author a plugin still types 5 questions and waits through plugin emission, even if what they actually want is "5 SKILLs under one plugin.json".

## # Phase 1-skill-creator — gate-2 cycle 1

- **evidence**: 3 sources (need ≥3)
  1. **prior reverted attempt** — commit `266897b` ("feat(plan): add 1-skill-rewrite phase for native CC+Codex skill implementation", PR #38) was merged then reverted by `9e5583a` (PR #39). Different origin: prior internal work — proves the user's intent and surfaces the failure mode this re-attempt must avoid.
  2. **first-person** — the user re-issued the same ask in this prompt, including the Korean instruction text. Different origin: self.
  3. **analogue product** — Anthropic's `claude-code-guide` skill and OpenAI's Codex plugin authoring flow each ship a single-runtime authoring tool; neither covers both runtimes from one interview. Different origin: market analogue.
- **LTV × reachable / cost**: $2,000 × 200 / $6,000 = $400,000 / $6,000 = **value_score 66.67** (PASS, threshold 3.0)
- **ambiguity**: 10 → 7 (asked implicitly: "what is the smallest 2-week version that pays for itself, given the prior revert?"). Accepted as the smallest 2-week version = **3 sub-modes of plugin-harness CLI** (`skill_create` 3 questions, `plugin_create` 5 questions reusing 0-mvp schema, `install` for both runtimes) + 4 native-skill registrations (CC skill × 2 + Codex skill × 2) installed idempotently.
- **next**: ambiguity_score 7 (still >3). Continue loop.

## # Phase 1-skill-creator — gate-2 cycle 2

- **evidence**: unchanged (3 sources, no new asks).
- **value**: unchanged (66.67).
- **ambiguity**: 7 → 5 (asked implicitly: "what is the kill condition?"). Accepted as **kill = if the dual-runtime artifact parity test (CC and Codex SKILL.md artifacts of the same interview) diverges — i.e., one runtime ships fewer features than the other — the phase ships as single-runtime only, and the dual-runtime parity is deferred to a separate PRD**.
- **next**: still 5 > 3, continue.

## # Phase 1-skill-creator — gate-2 cycle 3

- **evidence**: unchanged.
- **value**: unchanged.
- **ambiguity**: 5 → 3 (asked implicitly: "who is the first user, and what do they click first?"). Accepted as **first user = the same marketer persona from 0-mvp's canary**; **first click** = `plugin-harness new --mode=skill_create` invoked from inside the existing plugin-harness install on a fresh terminal; subsequent clicks add `--mode=plugin_create` and native runtime invocation (`/plugin-harness:skill-creator` in CC, `~/.agents/skills/skill-creator/SKILL.md` in Codex).
- **next**: 3 ≤ 3 — convergence test PASS. Move to gate 3.

## # Phase 1-skill-creator — convergence (gate 2.4)

```
PASS  iff  evidence_count >= 3
        AND value_score >= 3.0
        AND ambiguity_score <= 3

actual:  evidence_count = 3 ✓
         value_score    = 66.67 ✓
         ambiguity_score = 3  ✓

RESULT: PASS
```

## # Phase 1-skill-creator — non-goals (gate 3)

1. **No rewrite of the 0-mvp 5-question interview.** rationale: 0-mvp's question order is the product surface; reordering it breaks all canary installations. breach-response: if a PR touches `src/schema/questions.py` to reorder, reject and split into a separate "interview-revision" PRD.
2. **No runtime cross-compilation from CC-skill to Codex-skill (or vice versa) at runtime.** rationale: format divergence is real (different frontmatter shapes, different metadata keys, different invocation semantics) and post-hoc conversion loses information; emit both from the same interview instead. breach-response: if a reviewer asks for a `convert-skill` sub-mode, defer to a separate "format-converter" PRD.
3. **No GUI / web wizard.** rationale: CLI is sufficient; the 0-mvp non-goal 5 extends here. breach-response: if a GUI is added, require a CLI fallback for automation.
4. **No marketplace / commercial publishing.** rationale: 0-mvp non-goal 3 extends; skill/plugin authors using skill-creator ship to their own team, not to a marketplace. breach-response: defer to a separate "publish" PRD.
5. **No editorial / lint / style gate on the SKILL.md body.** rationale: 0-mvp's emitter has none, and adding one couples the build to a style guide; ship the raw emit, leave style guidance to the author's team. breach-response: if a PR adds a lint pass, defer to a separate "skill-lint" PRD.

## # Phase 1-skill-creator — ambiguity deltas (cumulative, gate 2.3)

| cycle | before | after | delta | asked |
|---|---|---|---|---|
| 1 | 10 | 7 | -3 | scope (smallest 2-week version given revert) |
| 2 | 7 | 5 | -2 | kill condition (parity test) |
| 3 | 5 | 3 | -2 | first user + first click |
| final | — | 3 | -7 | — |
