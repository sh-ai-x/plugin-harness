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

## Threat model (status-board integrity + AC3 oracle hard rule)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Log chain-hash assert.** Before AC status emission, `.dev-kit/ac-status.json` writer verifies the `.prd/interview-<slug>.log` HMAC chain (step1 rule 3). If any line fails, emit a top-level `AC0=red` row + refuse to write AC status as `green`. | `tests/contract/test_ac_log_chain.py` |
| 2 | **Status-board writable only by build orchestrator.** `.dev-kit/ac-status.json` file mode `0600`; owner = build-runner uid; refuses write if existing file mode widens to `0644`+. | `tests/contract/test_ac_status_mode.py` |
| 3 | **AC3 oracle hard rule (resolves review critical).** AC3 ("skill-invoke time → behaves as designed") MUST NOT be marked `green` by the harness itself. AC3 transitions to `green` ONLY when an external oracle confirms the manifest reflects author intent — specifically: a curated registry check OR a third-party-supplied scenario fixture spec signed by a non-build-runner key. Until an oracle artifact is present in `tests/fixtures/oracle/<plugin-slug>.txt`, AC3 status MUST be `manual-pending`. Never `green`. The harness may update other ACs; only AC3 has this restriction. This closes the unresolved F3 critical from `/dev-kit:review` iter-2. | `tests/contract/test_ac3_oracle.py` |
| 4 | **AC1 skill-existence assert.** AC1 ("interview finishes → working plugin") requires ≥1 inner skill directory present. step8 AC1 scenario checks both manifests parse AND ≥1 of `claude-side/skills/<n>/SKILL.md` or `codex-side/src/skills/<n>/SKILL.md` exists with valid frontmatter. Closes the iter-2 review gap where AC1 was manifest-only. | `tests/scenario/test_ac1_skill_exists.py` |
| 5-12 | Inherit step1-7 rules (all of them). | step1-7 test files |

**Why this matters.** The critical F3 finding (`AC3 verification authority is the harness itself`) lands at step8. Rule 3 enforces a hard wall: harness cannot self-approve AC3. Rule 4 closes the AC1 skill-existence gap.
