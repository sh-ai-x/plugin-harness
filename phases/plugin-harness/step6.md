# Step 6 — implement log↔plugin↔questionnaire consistency check

## Goal
Before zip assembly (step 7), verify that the logs, the plugin source, and the interview answers all agree. Catch drift before submission rejection. BLOCKING gate — step 7 only runs if this step passes.

## Inputs
- `interview.json` (5 answers from step 2 or 3)
- `src/` (generated plugin from steps 4 + 5)
- `logs/` (verbatim conversation from step 2 or 3)

## Outputs
- Consistency report: pass/fail per check + evidence
- Blocking on failure (refuse to proceed to step 7 if any HARD-FAIL check fails)

## Acceptance criteria
- Each interview answer appears in the generated SKILL.md body
- Each SKILL.md feature traces back to an interview answer
- The logs reference all 5 questions (the conversation actually covered them)
- The Codex `plugin.json` and Claude Code `.mcp.json` agreement check — **DOWNGRADED-BUT-ACTIVE** (always runs, never silently skipped):
  - If both `plugin.json` and `.mcp.json` are present → they MUST agree on the plugin's primary entry point (HARD FAIL on mismatch)
  - If only `plugin.json` is present (Codex-only transport) → log WARNING with "Codex-only transport" allow-state marker, do NOT hard-fail
  - If only `.mcp.json` is present (Claude-Code-only transport) → log WARNING with "Claude-Code-only transport" allow-state marker, do NOT hard-fail
- If any HARD-FAIL check fails, exit code 1 + clear error

## TDD order
1. RED: test that all 5 answers are referenced in the generated plugin
2. RED: test that the logs mention all 5 questions
3. RED: test that `plugin.json` and `.mcp.json` agree on entry point (both-present case → hard fail)
4. RED: test that "Codex-only transport" logs WARNING but passes (warning, not skip)
5. RED: test that "Claude-Code-only transport" logs WARNING but passes
6. RED: test that step 7 is BLOCKED on hard-fail
7. GREEN: implement checker
8. REFACTOR: pluggable check rules

## Risks
- Synonyms / paraphrasing may break the trace — use semantic similarity, not exact match
- False positives — keep the bar high (don't hard-fail on minor wording diffs)