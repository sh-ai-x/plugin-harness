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

## Threat model (mirror of step3, Codex-side; cross-target name check moved to step5)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **Path containment at write time.** `codex-side/src/skills/<name>/SKILL.md` and `codex-side/src/.codex-plugin/plugin.json` paths MUST go through `pathlib.Path(name).resolve().relative_to(project_root)`; reject `..` or absolute prefix. | `tests/contract/test_codex_path_containment.py` |
| 2-5 | Inherit step1+step2 rules (secret redaction, log integrity, frontmatter escaping, recap PII cap). | step1.md / step2.md test files |

**Why this matters.** Security finding 1 in PR #4 named `step4.md:19` as well. Mirror of step3 rule 1 — same resolve+relative-to check on the Codex side.

> **Step 4 ordering precondition (added iter-3).** step4 is gated on step3 manifest emitting first; cannot run concurrently with step3 (otherwise step4's path-containment rule sees a half-state). This is encoded in `depends_on: [step2]` AND a runtime assertion that `claude-side/.claude-plugin/plugin.json` exists with valid JSON before step4 begins. See `tests/contract/test_step4_precondition.py`.
>
> **Cross-target name check moved to step5** (per `/dev-kit:review` iter-2 finding #6: step4 alone cannot enforce name byte-equality because step3 may not have completed its emit yet). step5 rule 4 now owns that check.
