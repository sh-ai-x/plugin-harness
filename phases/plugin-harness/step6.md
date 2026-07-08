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

## Threat model (frontmatter hardening + mtime re-emit)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **YAML-safe frontmatter emit.** All values flowing into SKILL.md frontmatter (`name`, `description`) MUST round-trip through `yaml.safe_dump` then `yaml.safe_load` byte-equal. Multi-line inputs are collapsed to single-line (newline + control chars → space) BEFORE emit. | `tests/contract/test_frontmatter_escape.py` |
| 2 | **Description cap.** `description` field is capped at 240 chars; if Q1's intent + audience exceeds cap, truncate on a word boundary + append `…`. | same contract test |
| 3 | **Shared→side replication with mtime watch.** `shared/skills/<name>/SKILL.md` is the single source of truth. Claude-side and Codex-side are symlinks to `shared/`. When `shared/` mtime advances (`os.stat().st_mtime_ns` strictly greater than last-emit snapshot), the harness re-emits both sides (re-creates the symlinks + bumps a `.last-emit` marker). Step 6 is **re-entrant**: a future Phase C pass that mutates `shared/` (e.g., author edit) triggers a deterministic re-emit; no drift. | `tests/contract/test_skill_mtime_reemit.py` |
| 4 | **Cross-target byte-equality.** After step 6 (or any re-emit), the byte content of the target the symlink resolves to MUST be the same on both sides. Tested via `os.readlink` + `Path.read_bytes()`. | `tests/contract/test_skill_body_mirror.py` |
| 5-9 | Inherit step1-5 rules (path containment, secret redaction, log integrity, recap PII cap, name consistency, MCP mirror). | step1-5 test files |

**Why this matters.** Security findings 2, 4, 6 in PR #4 explicitly named `step6.md:28` (SKILL.md description = raw Q1 verbatim → frontmatter shadow + PII propagation). Rules 1+2 fix the frontmatter injection; rules 3+4 keep both sides byte-equal AND prevent drift on re-entry.
