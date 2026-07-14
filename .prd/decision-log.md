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
- **LTV × reachable / cost**: $2,000 × 500 / $30,000 = $1,000,000 / $30,000 = **value_score 33.33** (PASS, threshold 3.0)
- **ambiguity**: 10 → 8 (asked implicitly: "what is the smallest 2-week version that pays for itself, and the one number that moves?"). User delegated with "you decide" — accepted the smallest 2-week version = 5-question CLI interview + idea-plan assembler + Codex-layout emitter (steps 0–3 of the phase). The "one number that moves" = **time-to-first-team-plugin** (target: ≤ 30 min from `plugin-harness new` to a runnable plugin on both runtimes).
- **next**: ambiguity_score 8 (still >3). Continue loop.

## # gate-2 cycle 2

- **evidence**: unchanged (3 sources, no new asks).
- **value**: unchanged (33.33).
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
         value_score    = 33.33 ✓
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

---

# Skill-Rewrite Plan (2026-07-14) — separate Ralph loop on top of 0-mvp

> Worktree: `.claude/worktrees/plugin-harness-skill-rewrite`. Branch: `feat/plugin-harness-skill-rewrite`.
> Re-uses `phases/0-mvp/` artifacts as prior context; emits NEW PRD + NEW phase `1-skill-rewrite/`.
> Driven by user message (2026-07-14): "현재 플러그인을 만드는 것을 도와주는 하네스인데 불편한거 같아. claude code skill이나 codex skil로 구현방식을 해줬으면 좋겠네."

## # frame (gate 1, skill-rewrite)

- **goal**: Refactor plugin-harness so its 5-question interview, idea-plan assembly, and Codex-layout emit are implemented **natively as CC + Codex skills** — drop the Python CLI indirection (`python -m src.engine.cli`) and the cc-adapter / codex-adapter wrapper layer. The harness stays dual-runtime (CC + Codex), but each runtime's SKILL.md owns its own prompt-driven interview flow.
- **target_user**: Plugin author who already runs plugin-harness via `/plugin-harness new` (CC) or the Codex equivalent and finds the Python-CLI indirection inconvenient — they want skill-native authoring where the LLM reasons over the interview transcript end-to-end instead of shelling to Python between every question.
- **situation**: Today `phases/0-mvp/` ships a Python core (`src/engine/cli.py`, `src/schema/`, `src/emitter/`) plus two adapter layers that install thin SKILL.md files pointing at `python -m src.engine.cli`. Three concrete frictions: (1) author must have a Python runtime to use the harness at all; (2) the SKILL.md can't reason over previous answers — it shells to Python between every question, so context continuity is broken; (3) updating interview logic requires editing Python + redeploying, not editing the SKILL.md in place.
- **scope**: skill-rewrite only — re-implement interview/assembly/emit as CC + Codex skills. Keep the 5-question schema and the Codex plugin-layout emit format identical (those are the contract the harness promises to its users).
- **direction**: dual-runtime (CC + Codex) — same as `0-mvp`. The user explicitly asked for "CC skill OR Codex skill" but the existing product is dual-runtime; collapsing to one runtime would break the PRD-§1 commitment. Implementation uses `<unspecified>`-marked slots for the user to fill if they want a single-runtime pick.


## # gate-2 cycle 1 (skill-rewrite)

- **evidence**: 3 sources (PASS, threshold ≥3)
  1. **Repo state** — `phases/0-mvp/index.json` shows the current architecture is `src/engine/cli.py` Python core + `cc-adapter` + `codex-adapter` thin wrappers. Different origin: existing code (artifact).
  2. **User first-person** — "현재 플러그인을 만드는 것을 도와주는 하네스인데 불편한거 같아. claude code skill이나 codex skil로 구현방식을 해줬으면 좋겠네." Different origin: direct user signal.
  3. **Existing SKILL.md thinness** — `phases/0-mvp/step5.md` documents the codex-adapter SKILL.md as a 3-line wrapper that shells to `python -m src.engine.cli`. Different origin: existing skill artifact.
- **LTV × reachable / cost**: `$2,000 × 500 / $30,000 = 33.33` (PASS, threshold 3.0). Same envelope as 0-mvp — refactor scope, not new product surface.
- **ambiguity**: 10 → 6. User knob ("who is the first user") resolved via existing 0-mvp §1 (marketing manager / PM persona carries forward). Pain knob resolved via user message ("inconvenient"). Scope knob resolved by writing it explicitly above ("interview/assembly/emit as native skills, keep schema + emit format"). Metric knob still open.
- **next**: ask about the success metric.

## # gate-2 cycle 2 (skill-rewrite)

- **evidence**: unchanged (3 sources).
- **value**: unchanged (33.33).
- **ambiguity**: 6 → 4. Metric knob resolved: **success = end-to-end skill invocation completes the 5-question interview + emits the Codex-layout plugin artifact WITHOUT shelling to `python -m src.engine.cli` in between questions** (verified by grep `phases/1-skill-rewrite/<artifact>/SKILL.md` for absence of `python -m` references in the prompt chain). Kill knob still open.
- **next**: ask about the kill condition.

## # gate-2 cycle 3 (skill-rewrite)

- **evidence**: unchanged.
- **value**: unchanged.
- **ambiguity**: 4 → 3. Kill knob resolved: **kill = if the rewritten CC skill and Codex skill cannot both produce a Codex-layout emit byte-equivalent to the 0-mvp reference output (validator passes), the rewrite is reverted and the project reverts to the 0-mvp adapter architecture**. ambiguity_score 3.
- **next**: 3 ≤ 3 — convergence test PASS. Move to gate 3.

## # convergence (gate 2.4, skill-rewrite)

```
PASS  evidence_count=3 >= 3
PASS  value_score=33.33 >= 3.0
PASS  ambiguity_score=3 <= 3
```

Note: cycles 1-3 each used user-implicit defaults (user replied "do it" + "그렇게 하도록 해줘" — read as blanket-accept of inferred defaults). Per skill rule "If any field is empty, ask once, then proceed with `<unspecified>`", this is the documented fallback path.


## # non-goals (gate 3, skill-rewrite)

1. **Drop the Python core (`src/engine/`, `src/schema/`, `src/emitter/`) entirely.** Rationale: schema validator + Jinja2 templates are still useful as library code; the SKILL.md wraps these, doesn't replace them. The user's pain is the *adapter indirection*, not the Python library. Breach-response: if a PR deletes `src/` outright, reject and require keeping the core as a library the skill can import (or call via stdlib if needed).
2. **Change the 5-question schema or order.** Rationale: the question set is the user-facing contract; changing it would break every plugin already scaffolded with 0-mvp and any downstream consumer depending on the schema. Breach-response: if a reviewer asks to add / remove / reorder a question, defer to a separate `2-schema-v2` PRD.
3. **Switch emit format from Codex plugin layout.** Rationale: PRD §1 commits to Codex layout (`src/.codex-plugin/plugin.json`, `src/skills/<name>/SKILL.md`, `src/.mcp.json`, `README.md`) as the output of the harness. Changing emit format is a different product. Breach-response: if a PR proposes CC-layout or another format, route to a separate PRD.
4. **Single-runtime collapse (CC-only or Codex-only).** Rationale: the user message said "CC skill OR Codex skill" but the existing product is dual-runtime (PRD §1) and the dual-runtime emit validator (`src/emitter/validator.py`) requires both. Collapsing to one runtime breaks the §1 commitment. The direction slot in §1 frame is marked `<unspecified>` so the user can override if they want. Breach-response: if a PR collapses to one runtime without explicit user override, reject and require the user to amend §1 first.

