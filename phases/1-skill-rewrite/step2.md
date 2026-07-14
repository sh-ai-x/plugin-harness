# Step 2: Schema + emit templates exported as JSON resources loadable by both skills

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `/phases/1-skill-rewrite/step0.md` (CC skill — first consumer of these resources)
- `/phases/1-skill-rewrite/step1.md` (Codex skill — second consumer)
- `/src/schema/questions.py` (canonical question definitions; do NOT modify per non-goal)
- `/src/emitter/templates/codex/*.j2` (Jinja2 emit templates; do NOT modify per non-goal)
- `/src/emitter/codex.py` (current emit logic — may import these resources)

## Task
Make the 5-question schema and the Codex-layout emit templates loadable by both skills WITHOUT requiring a Python `import` from `src.schema` / `src.emitter`. The skills (steps 0/1) must be able to read them as plain JSON / template text from disk.

Concrete changes:
1. Add a script `scripts/export_resources.py` (or extend an existing one) that reads `src/schema/questions.py` and emits a stable JSON resource at `resources/schema.json` containing: question id, prompt text, allowed input shape (text | enum | list), and the 5 questions in canonical order.
2. Same script emits `resources/templates/<file>.j2` copies of the Jinja2 templates under `src/emitter/templates/codex/`, byte-identical to the originals (the resources/ copy is a flat-layout convenience for skill consumers that can't traverse Python packages).
3. The script MUST be idempotent — re-running it produces byte-identical `resources/` output (no timestamps, no random keys).
4. The script MUST exit non-zero if `src/schema/questions.py` and `resources/schema.json` ever diverge (compare and assert).
5. Wire the script into the existing test pipeline so `pytest` runs the export first and fails if drift is detected.

Non-negotiable rules:
- Do not modify `src/schema/questions.py` or `src/emitter/templates/codex/*.j2` (locked by gate-3 non-goals #2 and #3). The export is read-only on those.
- The exported `resources/schema.json` MUST be loadable by a non-Python consumer (no `__main__` markers, no Python-only types like `set` or `tuple`).

## Acceptance Criteria
```bash
# AC0: export script exists and runs cleanly
AC0: python scripts/export_resources.py
# expected: exit 0

# AC1: resources/schema.json exists and contains all 5 question ids
AC1: jq -r '.[].id' resources/schema.json | sort | uniq | wc -l
# expected: 5 (exit 0)

# AC2: templates copied byte-identically
AC2: diff -r src/emitter/templates/codex/ resources/templates/
# expected: exit 0 (no diff)

# AC3: script is idempotent (re-run produces no diff)
AC3: python scripts/export_resources.py && \
     sha256sum resources/schema.json resources/templates/*.j2 > /tmp/r1.sha && \
     python scripts/export_resources.py && \
     sha256sum resources/schema.json resources/templates/*.j2 > /tmp/r2.sha && \
     diff /tmp/r1.sha /tmp/r2.sha
# expected: exit 0

# AC4: pytest detects drift between src/ and resources/
AC4: pytest tests/test_resource_export.py -q
# expected: exit 0

# AC5: full pytest suite still green
AC5: pytest tests/ -q
# expected: exit 0 (count reported)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code (AC0..AC5 → exit 0).
2. Update `phases/1-skill-rewrite/index.json` for THIS step:
   - **Success** → `"status": "completed"`, `"summary": "<one-line: export script + resources/ added; src/ untouched; idempotency verified>"`
   - **Unrecoverable failure** → `"status": "error"`, `"error_message": "<AC# + exit code + last 3 lines>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

## Don't
- Do not modify `src/schema/questions.py`. Reason: locked by gate-3 non-goal #2.
- Do not modify `src/emitter/templates/codex/*.j2`. Reason: locked by gate-3 non-goal #3.
- Do not introduce non-portable JSON (Python `set`, `tuple`, `datetime` without custom encoder). Reason: the resources are read by the runtime skill, not by Python; non-portable types break parsing.
- Do not skip the drift test. Reason: without it, `src/` and `resources/` will silently diverge and the skills will see stale prompts.