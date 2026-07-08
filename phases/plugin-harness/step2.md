---
step: 2
phase: A
title: Persist answers + emit interview-recap
depends_on: [step1]
methodology: tdd
---

# Step 2 — Persist answers + emit interview-recap

## Goal
Take the 6 question stubs from step1, capture the author's answers (manual edit OR harness-driven), and produce a deterministic interview recap section.

## Inputs
- `.prd/interview-<slug>.md` (from step1)
- `.prd/interview-<slug>.log` (from step1, may already have partial lines)

## Outputs
- `.prd/interview-<slug>.md` — fully answered form (each Q has an Answer row).
- `.prd/interview-<slug>.log` — completed JSONL with all 6 lines.
- `.prd/interview-<slug>.recap.md` — recap section used by Phase B/C (manifest + SKILL.md author).

## Verification artifact
- **Scenario** `tests/scenario/test_interview_recap.py`:
  - all 6 answer rows non-empty.
  - recap contains `intent_keyword` (extracted from Q1) and `verification_keyword` (extracted from Q4).
- **Contract** `tests/contract/test_recap_schema.py`:
  - recap frontmatter has 3 fields: `intent`, `verification`, `audience` — all strings.

## Out of scope
- No manifest generation (Phase B).
- No skill generation (Phase C).

## Iron-law checklist
- L1: covered (scenario + contract).
- L3: enforced by harness-runner.
- L4: no TODOs.
