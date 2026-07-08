# Step 6 — implement log↔plugin↔questionnaire consistency check

## Goal
Before the smoke test (step 7), verify that the logs, the plugin source, and the interview answers all agree. Catch drift before downstream consumption. BLOCKING gate — step 7 only runs if this step passes.

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
- The Codex `plugin.json` and Claude Code `.mcp.json` agreement check — **PINNED contract**:
  - `primary_entry_point` is an explicit field in `interview.json` (added in step 1's schema: `{"primary_entry_point": "/<skill-name>"}`). Both emitters (step 4 → `.mcp.json`, step 5 → `plugin.json`) MUST write this exact string. Step 6 compares the two values byte-equal.
  - **DOWNGRADED-BUT-ACTIVE** (always runs, never silently skipped):
  - If both `plugin.json` and `.mcp.json` are present → they MUST agree on `primary_entry_point` (HARD FAIL on mismatch)
  - If only `plugin.json` is present (Codex-only transport) → log WARNING with "Codex-only transport" allow-state marker, do NOT hard-fail
  - If only `.mcp.json` is present (Claude-Code-only transport) → log WARNING with "Claude-Code-only transport" allow-state marker, do NOT hard-fail
  - If NEITHER is present → HARD FAIL with "no transport config emitted" — an emitter that failed silently must not pass the BLOCKING gate
- If any HARD-FAIL check fails, exit code 1 + clear error
- **Remediation map**: every HARD-FAIL check declares which upstream step to re-run, and the error message names the failing check + the upstream step:
  - `interview.json` shape mismatch (5 questions missing or malformed) → re-run step 2 (mode A) or step 3 (mode B)
  - Generated plugin doesn't reference any of the 5 answers → re-run step 4 and step 5 with the same `interview.json`
  - Logs don't mention all 5 questions → re-run step 2 or step 3 (whichever produced `logs/`)
  - Cross-runtime metadata mismatch between `plugin.json` and `.mcp.json` (both-present case, or neither-present case) → fix the inconsistent field in both emitters (step 4 and step 5) or fix the upstream step that failed to emit
  - The smoke test in step 7 is BLOCKED until every check passes

## TDD order
1. RED: test that all 5 answers are referenced in the generated plugin
2. RED: test that the logs mention all 5 questions
3. RED: test that `plugin.json` and `.mcp.json` agree on `primary_entry_point` (both-present case → hard fail)
4. RED: test that "Codex-only transport" logs WARNING but passes (warning, not skip) — verifies `plugin.json`'s `primary_entry_point` matches `interview.json`
5. RED: test that "Claude-Code-only transport" logs WARNING but passes — verifies `.mcp.json`'s `primary_entry_point` matches `interview.json`
6. RED: test that "neither file present" HARD-FAILS (no silent pass for missing emitter output)
7. RED: test that step 7 is BLOCKED on hard-fail
8. GREEN: implement checker (reads both file outputs + interview.json, compares primary_entry_point, runs all checks)
9. REFACTOR: pluggable check rules

## Risks
- Synonyms / paraphrasing may break the trace — use semantic similarity, not exact match
- False positives — keep the bar high (don't hard-fail on minor wording diffs)