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
| 2 | **Secret redaction (broadened).** Before appending any answer line to `.prd/interview-<slug>.log`, run a pre-write regex scan. Same scan also runs on every write to `.prd/interview-*.md` and the `env` block of `.mcp.json`. Pattern (case-insensitive, OR-joined):<br>• `(aws_access_key_id\|aws_secret_access_key)=`<br>• `ghu_[A-Za-z0-9]{36}` (GitHub user token)<br>• `gh[pousr]_[A-Za-z0-9]{36,255}` (GitHub PAT family)<br>• `sk-[A-Za-z0-9]{20,}` and `sk_live_[A-Za-z0-9]{20,}` (OpenAI / Stripe live)<br>• `xox[baprs]-[A-Za-z0-9-]{10,}` (Slack tokens)<br>• `-----BEGIN (RSA \|EC \|OPENSSH \|PGP \|)PRIVATE KEY-----` (PEM blocks)<br>• `eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}` (JWT shape)<br>• `(api[_-]?key\|api[_-]?token\|secret[_-]?key)\s*[:=]\s*["']?[A-Za-z0-9]{16,}`<br>• `bearer\s+[A-Za-z0-9_\-.=]{20,}`<br>• `authorization:\s*basic\s+[A-Za-z0-9+/=]{8,}` (Basic auth header)<br>• `AKIA[0-9A-Z]{16}` (AWS access key ID prefix)<br>On hit: refuse write + author warning before Phase B. No secret text is auto-removed; author decides. | `tests/contract/test_secret_scan.py` |
| 3 | **Log integrity (append-only + HMAC chain).** Each `.prd/interview-<slug>.log` line carries an HMAC over `(prev_chain_hash \|\| canonicalized_line)`. HMAC key source policy, in priority order:<br>1. env var `PLUGIN_HARNESS_HMAC_KEY` (CI / author workstation);<br>2. fallback file `.prd/.hmac-key` mode `0600` (created on first run if absent, never re-created);<br>3. `.prd/.hmac-key` is **repo-ignored** via `.gitignore` rule `*.key` extension AND `.prd/.hmac-key` literal; CI runner MUST inject env var (never let a `.key` file reach the CI box).<br>step8 asserts the chain verifies before AC status. | `tests/contract/test_log_integrity.py` + `tests/contract/test_hmac_key_source.py` |
| 4 | **Frontmatter escaping (active in step6).** All `description` / `intent_keyword` strings flowing into SKILL.md frontmatter must round-trip through `yaml.safe_dump` + `yaml.safe_load` byte-equal. Multi-line / control-char inputs are pre-collapsed to single-line before frontmatter emit. | `tests/contract/test_frontmatter_escape.py` (step6 test file) |

**Why these exist.** Findings 1, 5, 7 from `/dev-kit:security` review of PR #4, plus findings 5-7 in `/dev-kit:review` iter-2 (secret regex PEM/JWT/Slack/Stripe/Basic/md-scope gaps; HMAC key source not specified). All rules are concrete contract-test obligations, not aspirational TODOs.

## TDD isolation (revised after iter-2 review)

The iter-1 scenario test (`tests/scenario/test_interview_walk.py`) was implicit on `.prd/interview-<slug>.recap.md` — which is a step2 artifact. That breaks TDD isolation: step1 was depending on step2 emit. The scenario test now uses an **in-memory stub of the 6-answer recorder**; step1 does NOT touch step2's outputs. step2's scenario is the one that reads from `recap.md`.

Concretely:
- `tests/scenario/test_interview_walk.py` — instantiates a stub `Recorder` class, not the real one. Asserts recap-render is non-empty using stub-produced answers.
- The real `recap.md` write is exercised in step2's `tests/scenario/test_interview_recap.py`.

This is the isolation break fix flagged in `/dev-kit:review` iter-2 finding #4.
