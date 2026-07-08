---
step: 1
phase: A
title: Scaffold the 6-question interview
depends_on: []
methodology: tdd
---

# Step 1 — Scaffold the 6-question interview

## Goal
Emit a deterministic interview scaffold: the 6 questions, in a fixed order, each with stable keys (`q1..q6`). Author iterates answers in `.prd/interview-<slug>.md` (manual) OR through the harness `/dev-kit:plugin-harness interview` command (TBD).

## Inputs
- `PRD.md` §4 (socratic structure) — keeps the user-side contract consistent.
- `.prd/decision-log.md` — already has the question shapes from Gate 5.

## Outputs
- `.prd/interview-<slug>.md` — interview doc with the 6 question stubs + answer rows.
- `.prd/interview-<slug>.log` — JSONL log, one line per Q-and-A pair.

## Verification artifact
- **Contract test** `tests/contract/test_interview_scaffold.py`:
  - scaffold must produce exactly 6 question rows, keys `q1..q6` in order.
  - JSONL log must include `{ts, key, prompt, answer}` per line.
- **Scenario test** `tests/scenario/test_interview_walk.py`:
  - walk end-to-end; assert recap is non-empty after the 6th answer.

## Out of scope (this step)
- No manifest generation yet (Phase B — step3+).
- No skill generation yet (Phase C — step6).

## Iron-law checklist
- L1 (verification artifact): covered (contract + scenario listed).
- L2 (reproduce): n/a (greenfield scaffold; no bug to reproduce).
- L3 (exit-code / test count): enforced by harness-runner.
- L4 (no TODOs): stub file is the scaffold; no "we'll extend later" phrases.
- L5 (one answer): single scaffold shape, no option lists.

## Notes
- The 6-question order matches Codex's "submission" rubric (Q1=what/who/where, Q2=why, Q3=how, Q4=AI use, Q5=verification, Q6=recap).
- This step writes ONLY scaffolding artifacts; no Claude/Codex manifest exists yet.

## Threat model (must enforce in contract tests)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Path containment.** Every path derived from a Q-answer (interview file path, skill slug, scenario slug) is normalized against `project_root`; rejects any input containing `..` or absolute-path prefixes before filesystem write. | `tests/contract/test_path_containment.py` |
| 2 | **Secret redaction.** Before appending any answer line to `.prd/interview-<slug>.log`, run a pre-write regex scan (`(aws_access_key|ghu_|github_pat|sk-[A-Za-z0-9]{20,}|api[_-]?key=|token=|bearer\s)` case-insensitive). On hit, refuse write + surface an author warning before Phase B. No secret text is auto-removed; author decides. | `tests/contract/test_secret_scan.py` |
| 3 | **Log integrity (append-only + HMAC chain).** Each `.prd/interview-<slug>.log` line carries an HMAC over `(prev_chain_hash \|\| canonicalized_line)`; step8 asserts the chain verifies before AC status. | `tests/contract/test_log_integrity.py` |
| 4 | **Frontmatter escaping (becomes active in step6).** All `description` / `intent_keyword` strings flowing into SKILL.md frontmatter must round-trip through `yaml.safe_dump` + `yaml.safe_load` byte-equal. Multi-line / control-char inputs are pre-collapsed to single-line before frontmatter emit. | `tests/contract/test_frontmatter_escape.py` (introduced in step6) |

**Why these exist.** Findings 1, 5, 7 from `/dev-kit:security` review of PR #4 flagged path-traversal, missing secret redaction, and log-integrity gaps in step1. All four rules are concrete contract-test obligations, not aspirational TODOs.
