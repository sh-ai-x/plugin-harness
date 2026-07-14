# Step 1: Codex SKILL.md re-authored as native interview driver

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `/phases/0-mvp/step5.md` (current codex-adapter, the wrapper being replaced)
- `/phases/0-mvp/step0.md` (5-question schema, contract being preserved)
- `/src/schema/questions.py` (canonical 5-question order + prompts)
- `/phases/1-skill-rewrite/step0.md` (CC skill rewrite; mirror its structure)
- `.agents/skills/plugin-harness/SKILL.md` (current thin wrapper at Codex install path; verify path per `developers.openai.com/codex/skills` conventions)

## Task
Re-author the Codex skill so the SKILL.md owns the 5-question interview end-to-end via prompts, mirroring the CC rewrite from step 0.

Concrete changes:
1. Rewrite `.agents/skills/plugin-harness/SKILL.md` (or the canonical Codex skill path) so it embeds the 5 questions inline as numbered prompts the runtime drives in sequence. Question text matches `src/schema/questions.py` verbatim — same wording as the CC SKILL.md.
2. After the 5th answer, the SKILL.md MUST instruct the runtime to invoke the emit step directly (write files into the target plugin directory using the templates), not shell out to `python -m src.engine.cli`.
3. The 5-question schema must remain canonical — same questions, same order, same wording as `src/schema/questions.py`. Drift = AC fail.
4. Delete `src/adapter/codex.py` only if no other caller still uses it (grep first). Otherwise keep as a fallback adapter marked deprecated.
5. Idempotency: re-installing the skill on an existing target MUST NOT corrupt prior state.
6. The Codex SKILL.md MUST be byte-equivalent in question content to the CC SKILL.md (only the surrounding skill-frontmatter and runtime-specific invocation may differ).

Non-negotiable rules:
- No `python -m src.engine.cli` references inside the new SKILL.md prompt chain. If the skill must invoke Python, it may call a small `emit` helper (defined in step 3), not the full CLI.
- The skill must reference the schema validator (step 3) at the end of the emit, so the kill-condition is enforceable.
- Do not modify `src/schema/questions.py` (locked by gate-3 non-goal #2).
- Question content MUST match the CC SKILL.md from step 0 — same 5 questions, same wording, same order.

## Acceptance Criteria
```bash
# AC0: SKILL.md exists at the Codex install path and contains all 5 question prompts verbatim
AC0: grep -c "what/who/where" .agents/skills/plugin-harness/SKILL.md && \
     grep -c "why-this-problem" .agents/skills/plugin-harness/SKILL.md && \
     grep -c "how-it-works" .agents/skills/plugin-harness/SKILL.md && \
     grep -c "ai-usage" .agents/skills/plugin-harness/SKILL.md && \
     grep -c "how-verified" .agents/skills/plugin-harness/SKILL.md
# expected: each grep returns 1 or more (exit 0)

# AC1: SKILL.md has zero `python -m src.engine.cli` references in the prompt chain
AC1: ! grep -F "python -m src.engine.cli" .agents/skills/plugin-harness/SKILL.md
# expected: exit 0 (grep finds nothing)

# AC2: SKILL.md references the validator (kill-condition is enforceable)
AC2: grep -F "validator" .agents/skills/plugin-harness/SKILL.md
# expected: exit 0

# AC3: question content matches CC SKILL.md (diff the 5 question blocks)
AC3: diff <(grep -E "^[0-9]\.|^- " .claude/skills/plugin-harness/SKILL.md) \
          <(grep -E "^[0-9]\.|^- " .agents/skills/plugin-harness/SKILL.md)
# expected: exit 0 (no diff)

# AC4: codex-adapter not referenced from any non-deprecated caller
AC4: ! grep -rE "from src\.adapter\.codex|import src\.adapter\.codex" src/ tests/ .agents/ 2>/dev/null | grep -v deprecated
# expected: exit 0 (no live callers)

# AC5: full pytest suite green (CC + Codex e2e combined)
AC5: pytest tests/ -q
# expected: exit 0 (count of passing tests reported)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code (AC0..AC5 → exit 0).
2. Update `phases/1-skill-rewrite/index.json` for THIS step:
   - **Success** → `"status": "completed"`, `"summary": "<one-line: Codex SKILL.md re-authored, codex-adapter deprecated/removed, question content matches CC>"`
   - **Unrecoverable failure** → `"status": "error"`, `"error_message": "<AC# that failed + exit code + last 3 lines>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

## Don't
- Do not paraphrase the 5-question prompts in the SKILL.md. Reason: schema drift breaks downstream consumers; CC and Codex must match.
- Do not introduce `python -m src.engine.cli` invocations inside the SKILL.md prompt chain. Reason: same indirection the user flagged.
- Do not let question content diverge from the CC SKILL.md. Reason: dual-runtime contract — same author must get the same interview regardless of which runtime they invoke.
- Do not modify `src/schema/questions.py`. Reason: locked by gate-3 non-goal #2.
- Do not delete `src/adapter/codex.py` blindly. Reason: verify with grep AC4 before removal.