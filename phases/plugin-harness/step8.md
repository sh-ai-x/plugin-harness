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

## Threat model (status-board integrity)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Log chain-hash assert.** Before AC status emission, `.dev-kit/ac-status.json` writer verifies the `.prd/interview-<slug>.log` HMAC chain (step1 rule 3). If any line fails, emit a top-level `AC0=red` row + refuse to write AC status as `green`. | `tests/contract/test_ac_log_chain.py` |
| 2 | **Status-board writable only by build orchestrator.** `.dev-kit/ac-status.json` file mode `0600`; owner = build-runner uid; refuses write if existing file mode widens to `0644`+. | `tests/contract/test_ac_status_mode.py` |
| 3-10 | Inherit step1-7 rules (all of them). | step1-7 test files |

**Why this matters.** Security finding 3 (`AC3 verification authority is the harness itself`) and finding 7 (`.prd/interview-<slug>.log` mutable scratch) both point at step8 — this is where AC status is declared. Rule 1 ties log integrity to AC verdict (so a tampered log cannot pass AC). Rule 2 prevents a misconfigured step from leaking intent_key to a wider reader.
