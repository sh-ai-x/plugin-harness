# Step 0: CC SKILL.md re-authored as native interview driver

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `/phases/0-mvp/step4.md` (current cc-adapter, the wrapper being replaced)
- `/phases/0-mvp/step0.md` (5-question schema, contract being preserved)
- `/src/schema/questions.py` (canonical 5-question order + prompts)
- `.claude/skills/plugin-harness/SKILL.md` (current thin wrapper at CC install path; if missing, search `src/adapter/cc.py:install_skill()`)

## Task
Re-author the Claude Code skill so the SKILL.md owns the 5-question interview end-to-end via prompts, instead of shelling to `python -m src.engine.cli` between questions.

Concrete changes:
1. Rewrite `.claude/skills/plugin-harness/SKILL.md` (or whichever path `src/adapter/cc.py` installs to) so it embeds the 5 questions inline as numbered prompts the runtime drives in sequence. Question text comes from `src/schema/questions.py` — copy the prompts into the SKILL.md verbatim, do not paraphrase.
2. After the 5th answer, the SKILL.md MUST instruct the runtime to invoke the emit step directly (write files into the target plugin directory using the templates), not shell out to `python -m src.engine.cli`.
3. The 5-question schema must remain canonical — same questions, same order, same wording as `src/schema/questions.py`. Drift = AC fail.
4. Delete `src/adapter/cc.py` only if no other caller still uses it (grep first). Otherwise keep as a fallback adapter marked deprecated.
5. Idempotency: re-installing the skill on an existing target MUST NOT corrupt prior state (the runtime's standard install path is idempotent — verify by reading the runtime's install behavior and mirroring it).

Non-negotiable rules:
- No `python -m src.engine.cli` references inside the new SKILL.md prompt chain. If the skill must invoke Python, it may call a small `emit` helper (defined in step 3), not the full CLI.
- The skill must reference the schema validator (step 3) at the end of the emit, so the kill-condition is enforceable.
- Do not modify `src/schema/questions.py` (locked by gate-3 non-goal #2).

## Acceptance Criteria
```bash
# AC0: SKILL.md exists at the CC install path and contains all 5 question prompts verbatim
AC0: grep -c "what/who/where" .claude/skills/plugin-harness/SKILL.md && \
     grep -c "why-this-problem" .claude/skills/plugin-harness/SKILL.md && \
     grep -c "how-it-works" .claude/skills/plugin-harness/SKILL.md && \
     grep -c "ai-usage" .claude/skills/plugin-harness/SKILL.md && \
     grep -c "how-verified" .claude/skills/plugin-harness/SKILL.md
# expected: each grep returns 1 or more (exit 0)

# AC1: SKILL.md has zero `python -m src.engine.cli` references in the prompt chain
AC1: ! grep -F "python -m src.engine.cli" .claude/skills/plugin-harness/SKILL.md
# expected: exit 0 (grep finds nothing, `!` inverts)

# AC2: SKILL.md references the validator (kill-condition is enforceable)
AC2: grep -F "validator" .claude/skills/plugin-harness/SKILL.md
# expected: exit 0

# AC3: existing pytest suite still green (no regression on the 0-mvp AC)
AC3: pytest tests/ -q
# expected: exit 0 (count of passing tests reported)

# AC4: cc-adapter not referenced from any non-deprecated caller
AC4: ! grep -rE "from src\.adapter\.cc|import src\.adapter\.cc" src/ tests/ .claude/ 2>/dev/null | grep -v deprecated
# expected: exit 0 (no live callers)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code (AC0..AC4 → exit 0).
2. Update `phases/1-skill-rewrite/index.json` for THIS step:
   - **Success** → `"status": "completed"`, `"summary": "<one-line: SKILL.md re-authored, cc-adapter deprecated/removed>"`
   - **Unrecoverable failure** (3 retries exhausted) → `"status": "error"`, `"error_message": "<AC# that failed + exit code + last 3 lines of pytest output>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP — do not continue to step 1.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

The marker value MUST match the `status` field written to `index.json` in step 2.

## Don't
- Do not paraphrase the 5-question prompts in the SKILL.md. Reason: schema drift breaks every downstream consumer; the prompts are the user-facing contract.
- Do not introduce `python -m src.engine.cli` invocations inside the SKILL.md prompt chain. Reason: that's the exact indirection the user flagged as inconvenient.
- Do not modify `src/schema/questions.py`. Reason: locked by gate-3 non-goal #2; any change requires a separate schema-v2 PRD.
- Do not delete `src/adapter/cc.py` blindly. Reason: other callers may still depend on it; verify with grep AC4 before removal.
- Do not bypass the validator reference in the SKILL.md. Reason: validator is the kill-condition AC; without it the rewrite can't be checked against the 0-mvp reference output.