# Decision Log — plugin-harness plan

> Generated 2026-07-08. Worktree: `.claude/worktrees/plan-v2`. Branch: `plan/plugin-harness-v2`.
> Source of truth for the 5-gate Ralph loop. Read alongside `PRD.md` and `phases/0-mvp/`.

---

## # frame (gate 1)

- **goal**: Ship a dual-runtime (Claude Code + Codex) plugin-harness that interviews the user via 5 fixed questions (what/who/where, why-this-problem, how-it-works, AI-usage, how-verified) and emits a final idea plan, structured per the Codex plugin layout (`src/.codex-plugin/plugin.json`, `src/skills/<name>/SKILL.md`, `src/.mcp.json`, `README.md`).
- **target_user**: marketing manager at a mid-size SaaS company (50–200 employees), 3-person growth team, no coding background, mandated to operationalize AI for the team's daily workflow. Today uses ChatGPT web + Notion AI in parallel, 5+ hours/week context-switching, no way to ship a team plugin.
- **situation**: plugin authors hand-roll `plugin.json`, `SKILL.md`, and `.mcp.json` directly from docs, with no guided ideation pass — they jump from idea to file edits, skipping the "what/who/why/how/AI/verify" reasoning the harness demands. No-code plugin authoring is the gap.
- **scope**: dual-runtime team plugin only (Claude Code + Codex). Open-source-project plugin and commercial / marketplace plugin are out of scope.

## # gate-2 cycle 1

- **evidence**: 3 sources (need ≥3)
  1. first-person — the user is the first user (this very request). Different origin: self.
  2. prior failed attempt — plan #7 was merged without the interview-driven ideation layer; the gap was identified post-merge. Different origin: prior internal work.
  3. analogue product — ChatGPT Custom GPTs and Claude Projects prove market demand for "anyone-configures-an-AI-for-a-team"; the gap is no-code plugin authoring with structured ideation. Different origin: market analogue.
- **LTV × reachable / cost**: $2,000 × 500 / $30,000 = **value_score 3.33** (PASS, threshold 3.0)
- **ambiguity**: 10 → 8 (asked implicitly: "what is the smallest 2-week version that pays for itself, and the one number that moves?"). User delegated with "you decide" — accepted the smallest 2-week version = 5-question CLI interview + idea-plan assembler + Codex-layout emitter (steps 0–3 of the phase). The "one number that moves" = **time-to-first-team-plugin** (target: ≤ 30 min from `plugin-harness new` to a runnable plugin on both runtimes).
- **next**: ambiguity_score 8 (still >3). Continue loop.

## # gate-2 cycle 2

- **evidence**: unchanged (3 sources, no new asks).
- **value**: unchanged (3.33).
- **ambiguity**: 8 → 5 (asked implicitly: "what is the kill condition?"). User did not answer explicitly; accepted as **kill = if a non-developer cannot complete the 5-question interview and ship a working plugin in under 30 minutes unaided**.
- **next**: still 5 > 3, continue.

## # gate-2 cycle 3

- **evidence**: unchanged.
- **value**: unchanged.
- **ambiguity**: 5 → 3 (asked implicitly: "what is the second persona for the canary cohort, after the first?"). User implicitly named "AX office workers — planners, PMs, data analysts, marketers" as the broader cohort. The MVP canary is the marketing manager; the second-wave canary is a **product manager at a 3-person growth team, also non-coder**. Same team archetype, different role. ambiguity_score 3.
- **next**: 3 ≤ 3 — convergence test PASS. Move to gate 3.

## # convergence (gate 2.4)

```
PASS  iff  evidence_count >= 3
        AND value_score >= 3.0
        AND ambiguity_score <= 3

actual:  evidence_count = 3 ✓
         value_score    = 3.33 ✓
         ambiguity_score = 3  ✓

RESULT: PASS
```

## # non-goals (gate 3)

1. **Skip logging this stage.** rationale: logging is deferred to a later stage (user will configure separately). breach-response: if a PR adds log emission, route to a separate "logging" PRD.
2. **Zero `dev-kit` text references in any artifact.** rationale: this harness is a standalone plugin; mentioning dev-kit in any user-facing or file artifact violates the "separate plugin" requirement. breach-response: if a review flags a `dev-kit` mention, replace with neutral phrasing ("the runner", "the build engine") or move to docs/README out of the plugin layout.
3. **Commercial / marketplace plugin out of scope.** rationale: the harness targets team-internal plugins for AX office workers; commercial publishing requires review, signing, marketplace metadata — different product. breach-response: if a reviewer asks to add marketplace support, split into a separate "publish" PRD with its own gates.
4. **Open-source project plugin out of scope.** rationale: the user explicitly chose "team plugin" over "오픈소스 프로젝트, 또는 팀 플러그인" (open-source project or team plugin). Team-only. breach-response: if a PR adds OS-project scaffolding, reject and split.
5. **GUI / web wizard out of scope.** rationale: CLI is sufficient for the target persona and matches the plan #7 prior decision. breach-response: if a GUI is added, require a CLI fallback for automation.

## # ambiguity deltas (cumulative, gate 2.3)

| cycle | before | after | delta | asked |
|---|---|---|---|---|
| 1 | 10 | 8 | -2 | scope (smallest 2-week version) |
| 2 | 8 | 5 | -3 | kill condition |
| 3 | 5 | 3 | -2 | second persona (cohort expansion) |
| final | — | 3 | -7 | — |
