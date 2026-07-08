---
step: 7
phase: C
title: Author scenario test from interview Q1+Q4
depends_on: [step6]
methodology: tdd
---

# Step 7 — Author scenario test from interview Q1+Q4

## Goal
Close AC3 ("skill-invoke time → behaves as designed") by emitting a scenario test under `tests/scenario/<skill>.md` whose dry-run returns the intent-key derived from Q1 and whose expected match mirrors Q4's verification answer.

## Inputs
- `shared/skills/<name>/SKILL.md` (step6).
- `.prd/interview-<slug>.recap.md` (intent_keyword + verification_keyword).

## Outputs
- `tests/scenario/<skill>.md` — scenario spec with `given`, `when`, `then`, `intent_key`, `verification_key`.

## Verification artifact
- **Scenario** `tests/scenario/test_intent_match.py`:
  - given a simulated user query matching Q1's audience, assert the skill's loaded description matches → intent_key returned.
- **Contract** `tests/contract/test_scenario_schema.py`:
  - scenario file has 4 required fields (`given`, `when`, `then`, `intent_key`).

## Out of scope
- No AC status board yet (step8).

## Iron-law checklist
- L1: contract + scenario.
- L4: no TODOs.
