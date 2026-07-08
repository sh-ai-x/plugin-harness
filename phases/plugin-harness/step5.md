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

## Threat model (cross-target mirror)

| # | Rule | Where it lives |
|---|---|---|
| 1 | **MCP server-name equivalence.** Server `name`s in `claude-side/.mcp.json` and `codex-side/src/.mcp.json` MUST be set-equal. No silent divergence. | `tests/contract/test_mcp_name_mirror.py` (renamed from `test_mcp_shape.py` for clarity) |
| 2 | **Transport equivalence.** Transports (`stdio` / `http`) for each server name MUST match across both sides. A name present on one side with `stdio` but `http` on the other is hard-fail (silent mismatch). | `tests/contract/test_mcp_transport_mirror.py` |
| 3-7 | Inherit step1+2+3+4 rules (path containment, secret redaction, log integrity, frontmatter escaping, recap PII cap, name consistency). | step1-4 test files |

**Why this matters.** Step5 is the cross-target lock. Security finding 7 in PR #4 didn't flag MCP specifically, but the dual-target name + transport equivalence is the gate that catches the next class of "one side silent drift" bugs.
