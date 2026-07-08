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

## Iron-law checklist
- L1: covered (contract + scenario).
- L4: stub is intentional (Phase B first cut), not "we'll extend later".
