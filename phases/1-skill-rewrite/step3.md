# Step 3: Validator kept as kill-condition verifier (emit-equivalence gate)

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `/phases/0-mvp/step3.md` (original dual-runtime-emitter + validator design)
- `/src/emitter/validator.py` (existing jsonschema-based validator — keep, do not rewrite)
- `/src/emitter/codex.py` (current emit; will be invoked by the small emit helper)
- `/docs/codex-plugin.schema.json` (vendored jsonschema contract)
- `/phases/1-skill-rewrite/step0.md`, `step1.md` (skills that MUST reference the validator)
- `/phases/1-skill-rewrite/step2.md` (resources the validator validates against)

## Task
Wire the existing `src/emitter/validator.py` into the kill-condition for the skill-rewrite. The validator already enforces the Codex plugin-layout contract; this step makes it the executable gate that proves the skill-native rewrite produces the same artifact as the 0-mvp adapter-based implementation.

Concrete changes:
1. Add `scripts/verify_emit.py` (a small, single-purpose Python helper — NOT the full CLI) that:
   - Takes a target plugin directory as `argv[1]`.
   - Runs `src/emitter/validator.py:validate(target_dir)` against it.
   - Exits 0 if valid, non-zero with a concrete error message if not.
   - This is the ONE Python helper the skills (steps 0/1) are allowed to shell to. The full CLI is still banned.
2. Update both SKILL.md files (CC and Codex) so the final emit step calls `python scripts/verify_emit.py <target_dir>` after writing the files. This is the kill-condition check.
3. The validator must run against BOTH the resource-loaded schema (`resources/schema.json` per step 2) AND the original `src/schema/questions.py` — pick whichever is more stable; document the choice in this step's completion summary.
4. No change to `src/emitter/validator.py` itself — read-only on it.

Non-negotiable rules:
- The skills may shell to `python scripts/verify_emit.py` but NOT to `python -m src.engine.cli`. The former is a single-purpose helper; the latter is the indirection being removed.
- The validator MUST exit non-zero on any drift from the Codex-layout contract (existing behavior — keep it).
- Do not modify `src/emitter/validator.py`. Reason: it's the kill-condition anchor; rewriting it changes what "kill" means.

## Acceptance Criteria
```bash
# AC0: verify_emit.py exists and is invocable
AC0: python scripts/verify_emit.py --help
# expected: exit 0 (or 2 with usage text — both are acceptable as long as the script runs)

# AC1: validator passes against a freshly-emitted 0-mvp reference fixture
AC1: python scripts/verify_emit.py tests/fixtures/sample_plugin/
# expected: exit 0

# AC2: validator fails on a deliberately-malformed fixture (negative test)
AC2: ! python scripts/verify_emit.py tests/fixtures/malformed_plugin/
# expected: exit 0 (validator exited non-zero, `!` inverts)

# AC3: both SKILL.md files reference verify_emit.py in their emit step
AC3: grep -F "verify_emit.py" .claude/skills/plugin-harness/SKILL.md && \
     grep -F "verify_emit.py" .agents/skills/plugin-harness/SKILL.md
# expected: exit 0

# AC4: skills do NOT shell to the full CLI anywhere
AC4: ! grep -F "python -m src.engine.cli" .claude/skills/plugin-harness/SKILL.md && \
     ! grep -F "python -m src.engine.cli" .agents/skills/plugin-harness/SKILL.md
# expected: exit 0

# AC5: full pytest suite green (validator tests included)
AC5: pytest tests/ -q
# expected: exit 0 (count reported)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code (AC0..AC5 → exit 0).
2. Update `phases/1-skill-rewrite/index.json` for THIS step:
   - **Success** → `"status": "completed"`, `"summary": "<one-line: verify_emit.py wired as kill-condition; both SKILL.md reference it; validator kept untouched>"`
   - **Unrecoverable failure** → `"status": "error"`, `"error_message": "<AC# + exit code + last 3 lines>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

## Don't
- Do not modify `src/emitter/validator.py`. Reason: it's the kill-condition anchor; rewriting it changes the kill definition.
- Do not let the SKILL.md files shell to `python -m src.engine.cli`. Reason: that's the full-CLI indirection being removed.
- Do not skip the negative test (AC2). Reason: a validator that can't fail is no validator; the kill-condition has no teeth.
- Do not add new validation rules beyond what `src/emitter/validator.py` already enforces. Reason: scope creep into schema changes (locked by gate-3 non-goals).