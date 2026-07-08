---
step: 8
phase: D
title: AC1/2/3 self-check + registration checklist
depends_on: [step7]
methodology: tdd
---

# Step 8 — AC1/2/3 self-check + registration checklist

## Goal
Emit `.dev-kit/ac-status.json` with the three ACs marked GREEN (or manual-pending for AC2), and write a registration checklist the author runs to satisfy AC2.

## Inputs
- All Phase B + C outputs.
- `tests/scenario/<skill>.md` (step7).

## Outputs
- `.dev-kit/ac-status.json`
- `docs/registration-checklist.md`

## Verification artifact
- **Scenario** `tests/scenario/test_ac_status.py`:
  - AC1 = `"green"` — both `claude-side/.claude-plugin/plugin.json` and `codex-side/src/.codex-plugin/plugin.json` parse + match intent_keyword.
  - AC3 = `"green"` — `tests/scenario/<skill>.md` dry-run returns expected intent_key.
  - AC2 = `"manual-pending"` — registration is outside the harness (intentional).
- **Contract** `tests/contract/test_ac_status_shape.py`:
  - `.dev-kit/ac-status.json` has the 3 keys; values are `"green" | "manual-pending" | "red"`.

## Out of scope
- No marketplace automation — non-goal #2 forbids it.

## Iron-law checklist
- L1: scenario + contract.
- L3: status board is the verification artifact for hand-off.
- L4: no TODOs.
