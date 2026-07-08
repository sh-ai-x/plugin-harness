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

## Threat model (frontmatter hardening)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **YAML-safe frontmatter emit.** All values flowing into SKILL.md frontmatter (`name`, `description`) MUST round-trip through `yaml.safe_dump` then `yaml.safe_load` byte-equal. Multi-line inputs are collapsed to single-line (newline + control chars → space) BEFORE emit. | `tests/contract/test_frontmatter_escape.py` |
| 2 | **Description cap.** `description` field is capped at 240 chars; if Q1's intent + audience exceeds cap, truncate on a word boundary + append `…`. | same contract test |
| 3 | **Cross-target byte-equality.** `shared/skills/<name>/SKILL.md` body MUST be byte-equal in both `claude-side/skills/<name>/SKILL.md` and `codex-side/src/skills/<name>/SKILL.md` after symlink/include resolution. No silent divergence. | `tests/contract/test_skill_body_mirror.py` |
| 4-8 | Inherit step1-5 rules (path containment, secret redaction, log integrity, recap PII cap, name consistency, MCP mirror). | step1-5 test files |

**Why this matters.** Security findings 2, 4, 6 in PR #4 explicitly named `step6.md:28` (SKILL.md description = raw Q1 verbatim → frontmatter shadow + PII propagation). Rule 1+2 fix the frontmatter injection; rule 3 keeps both sides byte-equal so marketplace search consistency holds.
