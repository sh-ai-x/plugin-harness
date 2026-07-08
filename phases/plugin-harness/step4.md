---
step: 4
phase: B
title: Generate Codex-side plugin manifest
depends_on: [step2]
methodology: tdd
---

# Step 4 — Generate Codex-side plugin manifest

## Goal
From the same `.prd/interview-<slug>.recap.md`, emit a valid `codex-side/src/.codex-plugin/plugin.json` plus a Codex-side scaffold for ≥1 skill directory. Step is a structural mirror of step3 — the schema differs.

## Inputs
- `.prd/interview-<slug>.recap.md` (Phase A exit artifact).

## Outputs
- `codex-side/src/.codex-plugin/plugin.json` — manifest.
- `codex-side/src/skills/<name>/SKILL.md` — initial SKILL.md stub.

## Verification artifact
- **Contract** `tests/contract/test_codex_manifest.py`:
  - manifest parses; `name`, `description`, `version` present (Codex schema).
  - `name` matches step3's `name` (dual-target consistency).
  - `description` mirrors Q1 + Q4 (same source as step3 — single-source-of-truth).
- **Scenario** `tests/scenario/test_codex_manifest_intent.py`:
  - simulate Codex loading; description matches Q1 audience.

## Out of scope
- No MCP wiring (step5).
- No scenario-test authoring for the skill (step7).
- No cross-target lock (step5 enforces it via `.mcp.json` shape).

## Iron-law checklist
- L1: contract + scenario.
- L4: stub is intentional.
