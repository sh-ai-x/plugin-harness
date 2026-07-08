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

## Iron-law checklist
- L1: contract + scenario.
- L4: no TODOs.
