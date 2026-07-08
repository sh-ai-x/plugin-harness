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

## Threat model (scenario-test integrity)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Scenario file path containment.** `tests/scenario/<name>.md` slug must pass the same resolve+relative-to check (step1 rule 1). | step1 test file |
| 2 | **Intent-key determinism.** `intent_key` in the scenario is the SHA-256 prefix of the normalized Q1 intent, not the raw Q1 string. Two PRs with same intent at Q1 must produce same `intent_key`. | `tests/contract/test_intent_key_determinism.py` |
| 3-9 | Inherit step1-6 rules. | step1-6 test files |

**Why this matters.** Security finding 1 (`tests/scenario/name.md`) was flagged for the same path-traversal surface as the manifest paths. Rule 1 closes that. Rule 2 makes the intent-key a stable hash, so AC3 verification can compare across runs without leaking Q1's verbatim text into scenario dry-run outputs.
