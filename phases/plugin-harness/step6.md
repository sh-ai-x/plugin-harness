---
step: 6
phase: C
title: Author SKILL.md from interview Q1+Q4
depends_on: [step5]
methodology: tdd
---

# Step 6 — Author SKILL.md from interview Q1+Q4

## Goal
Replace the SKILL.md stubs from step3/4 with content derived deterministically from the interview (Q1 = intent/audience; Q4 = how AI is used). Single-source-of-truth so Claude-side and Codex-side share the same wording.

## Inputs
- `claude-side/skills/<name>/SKILL.md` (step3 stub)
- `codex-side/src/skills/<name>/SKILL.md` (step4 stub)
- `.prd/interview-<slug>.recap.md`

## Outputs
- `shared/skills/<name>/SKILL.md` — single source of truth for the body.
- `claude-side/skills/<name>/SKILL.md` — links / includes shared/.
- `codex-side/src/skills/<name>/SKILL.md` — links / includes shared/.

## Verification artifact
- **Contract** `tests/contract/test_skill_md.py`:
  - frontmatter has `name`, `description` (Codex-style).
  - body sections: `## Intent`, `## How AI is used`, `## Verification`.
  - `description` field equals Q1's intent + audience string.
- **Scenario** `tests/scenario/test_skill_describes_intent.py`:
  - simulated marketplace search by the `description` field returns the skill as a hit for the Q1 query.

## Out of scope
- No scenario-test authoring yet (step7).

## Iron-law checklist
- L1: contract + scenario.
- L4: no TODOs; sections are filled, not stubbed.
