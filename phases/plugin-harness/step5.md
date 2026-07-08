---
step: 5
phase: B
title: MCP shape adapter
depends_on: [step3, step4]
methodology: tdd
---

# Step 5 — MCP shape adapter

## Goal
If the interview (Q3 — "how does the plugin work?") implies an MCP server, generate `.mcp.json` for both targets from a single source of truth so server names + transports match across Claude and Codex.

## Inputs
- `claude-side/.claude-plugin/plugin.json` (step3).
- `codex-side/src/.codex-plugin/plugin.json` (step4).
- `.prd/interview-<slug>.recap.md` (Phase A exit artifact).

## Outputs
- `claude-side/.mcp.json`
- `codex-side/src/.mcp.json`

## Verification artifact
- **Contract** `tests/contract/test_mcp_shape.py`:
  - both `.mcp.json` parse.
  - server `name`s mirror 1:1 (set equality).
  - transports match (stdio/http).
- **Scenario** `tests/scenario/test_mcp_dual_target.py`:
  - load both, simulate `server.list_tools()` parity; both sides return the same tool names.

## Out of scope
- No skill content authoring (step6).
- No scenario-test authoring for the skill (step7).

## Threat model (cross-target mirror; conditional on Q3 implying MCP)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **MCP server-name equivalence (conditional).** Server `name`s in `claude-side/.mcp.json` and `codex-side/src/.mcp.json` MUST be set-equal *iff* Q3 implies MCP. If Q3 implies no MCP, both files MUST be absent OR both files MUST be present-empty-list. Mixed absence/presence is hard-fail. | `tests/contract/test_mcp_name_mirror.py` |
| 2 | **Transport equivalence (conditional).** Transports (`stdio` / `http`) for each server name MUST match across both sides, when present. A name present on one side with `stdio` but `http` on the other is hard-fail (silent mismatch). | `tests/contract/test_mcp_transport_mirror.py` |
| 3 | **MCP conditional acceptance.** step5's contract test accepts three valid outcomes and rejects the fourth:<br>• both files absent (Q3 = no MCP) — PASS<br>• both files present, valid, name + transport mirror — PASS<br>• both files present-empty-list — PASS<br>• only one side present — FAIL |
| 4 | **Cross-target `plugin.json::name` byte-equality.** `claude-side/.claude-plugin/plugin.json::name` MUST equal `codex-side/src/.codex-plugin/plugin.json::name` byte-equal. (This rule was moved from step4 in iter-3 because step4 alone cannot enforce it — step3 may not have written its manifest yet when step4 emits.) | `tests/contract/test_dual_target_name.py` |
| 5-8 | Inherit step1+2+3+4 rules (path containment, secret redaction, log integrity, frontmatter escaping, recap PII cap). | step1-4 test files |

**Why this matters.** Step5 is the side-equivalence gate (previously called "cross-target lock"; softened per `/dev-kit:review` iter-2 finding #12 — "lock" implied mutex; the actual semantics are dual-side parity, not exclusion). It catches the "one side silent drift" class of bugs (rule 1+2 transport drift) and ensures manifest discoverability is uniform across markets (rule 4).
