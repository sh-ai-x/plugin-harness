# Step 7 — implement log↔plugin↔questionnaire consistency check

## Goal
Before zipping, verify that the logs, the plugin source, and the interview answers all agree. Catch drift before submission rejection.

## Inputs
- `interview.json` (5 answers)
- `src/` (generated plugin)
- `logs/` (verbatim conversation)

## Outputs
- Consistency report: pass/fail per check + evidence
- Blocking on failure (refuse to zip if check fails)

## Acceptance criteria
- Each interview answer appears in the generated SKILL.md body
- Each SKILL.md feature traces back to an interview answer
- The logs reference all 5 questions (the conversation actually covered them)
- The Codex `plugin.json` and Claude Code `.mcp.json` agree on the plugin's primary entry point — **CONDITIONAL**: only enforced when both `plugin.json` and `.mcp.json` are present. If `.mcp.json` is absent (Codex-only transport), the check is skipped with an explicit "Codex-only transport" allow-state marker in the consistency report.
- If any check fails, exit code 1 + clear error

## TDD order
1. RED: test that all 5 answers are referenced in the generated plugin
2. RED: test that the logs mention all 5 questions
3. RED: test that `plugin.json` and `.mcp.json` agree on entry point
4. GREEN: implement checker
5. REFACTOR: pluggable check rules

## Risks
- Synonyms / paraphrasing may break the trace — use semantic similarity, not exact match
- False positives — keep the bar high (don't block on minor wording diffs)
