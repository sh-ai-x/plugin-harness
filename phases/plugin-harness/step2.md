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

## Threat model (cross-step; pulls rules from step1 + adds recap-PII rules)

| # | Rule (inherits + extends) | Where it lives |
|---|---|---|
| 1-4 | Inherit all step1 threat-model rules (path containment, secret redaction, log integrity, frontmatter escaping). | step1.md test files |
| 5 | **Recap PII propagation cap (widened).** `intent_keyword`, `audience`, `verification_keyword` extracted into `.prd/interview-<slug>.recap.md` are capped at 240 chars each, lowercased, and stripped of:<br>• any 9+ digit run (phone / SSN-like / long IDs)<br>• email-shaped runs (`localpart@domain.tld`, RFC-lite match)<br>• IPv4 runs (`\d{1,3}(\.\d{1,3}){3}`)<br>• IPv6 runs (`[0-9a-f:]{2,}` with `:` >= 2)<br>• GUID-shaped runs (`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`)<br>This blocks the A09-major finding that PII-bearing Q1 strings propagate verbatim into manifest description → SKILL.md → marketplace index. | `tests/contract/test_recap_pii.py` |

**Why this matters.** Security finding 6 in PR #4 (`/dev-kit:security`) called out that `intent_keyword` flows unchanged from Q1 answer into the manifest and then the marketplace description. Capping + normalization at recap-emit is the earliest, cheapest stage to clamp it.
