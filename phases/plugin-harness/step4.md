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

## Threat model (mirror of step3, Codex-side)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Path containment at write time.** `codex-side/src/skills/<name>/SKILL.md` and `codex-side/src/.codex-plugin/plugin.json` paths MUST go through `pathlib.Path(name).resolve().relative_to(project_root)`; reject `..` or absolute prefix. | `tests/contract/test_codex_path_containment.py` |
| 2-5 | Inherit step1+step2 rules (secret redaction, log integrity, frontmatter escaping, recap PII cap). | step1.md / step2.md test files |
| 6 | **Cross-target name consistency.** `codex-side/src/.codex-plugin/plugin.json::name` MUST equal `claude-side/.claude-plugin/plugin.json::name` byte-equal (also enforced in step5 via `.mcp.json` mirror). No `name` divergence between Claude and Codex manifests. | `tests/contract/test_dual_target_name.py` |

**Why this matters.** Security finding 1 in PR #4 named `step4.md:19` as well. Mirror of step3 rule 1 — same resolve+relative-to check on the Codex side. Rule 6 keeps `name` consistent so both sides stay discoverable as the same plugin in their marketplaces.
