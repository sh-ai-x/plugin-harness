---
step: 3
phase: B
title: Generate Claude-side plugin manifest
depends_on: [step2]
methodology: tdd
---

# Step 3 — Generate Claude-side plugin manifest

## Goal
From `.prd/interview-<slug>.recap.md`, emit a valid `claude-side/.claude-plugin/plugin.json` plus the Claude-side scaffold for ≥1 skill directory.

## Inputs
- `.prd/interview-<slug>.recap.md` (Phase A exit artifact).

## Outputs
- `claude-side/.claude-plugin/plugin.json` — manifest.
- `claude-side/skills/<name>/SKILL.md` — initial SKILL.md stub.

## Verification artifact
- **Contract** `tests/contract/test_claude_manifest.py`:
  - manifest parses as JSON; `name`, `description`, `version` present.
  - `name` mirrors the interview's intent keyword.
  - `description` mirrors the interview's audience + verification (Q1 + Q4).
- **Scenario** `tests/scenario/test_claude_manifest_intent.py`:
  - when the harness simulates Claude Code loading the manifest, the plugin's `description` matches the Q1 audience (sanity only; full invoke-time test = AC3 in step8).

## Out of scope
- No Codex side yet (step4).
- No MCP wiring yet (step5).
- No scenario-test authoring for the skill (step7).

## Threat model (inherits + adds Claude-side path-containment binding)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Path containment at write time.** `claude-side/skills/<name>/SKILL.md` and `claude-side/.claude-plugin/plugin.json` paths derived from interview `<name>` slug MUST go through `pathlib.Path(name).resolve().relative_to(project_root)`; reject if `..` in input or resolved path escapes project_root. | `tests/contract/test_claude_path_containment.py` |
| 2-5 | Inherit step1 rules 2-4 and step2 rule 5 (secret redaction, log integrity, frontmatter escaping, recap PII cap). | step1.md / step2.md test files |

**Why this matters.** Security finding 1 in PR #4 explicitly named `step3.md:19` (`claude-side/skills/name/SKILL.md`) as the path-traversal surface. Adding the resolve+relative-to check at write is the actual fix.
