# Step 0: 5-question schema + interview state

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (this file)

## Task
Define the 5 fixed interview questions as a structured schema and a serializable interview state. The schema is the product surface; the state is the runtime carrier.

Files to create:
- `src/schema/questions.json` — the 5-question schema (id, prompt, answer_type, choices, min_length, validation hint)
- `src/schema/state.py` — `InterviewState` class with `advance()`, `set_answer(qid, value)`, `is_complete()`, `current_question()`, `to_dict()`, `from_dict()`, `validate_answer(qid, value)`
- `src/schema/__init__.py` — re-exports `QUESTIONS`, `InterviewState`
- `tests/test_question_schema.py` — pytest: schema loads, all 5 questions present, fields complete
- `tests/test_interview_state.py` — pytest: state transitions, round-trip serialization, validation errors

Canonical questions (locked, in order):
1. `what-who-where` — "무엇을, 누가, 어떤 상황에서 쓰나요?" — answer_type=text, min_length=20
2. `why-this-problem` — "왜 이 문제를 선택했나요?" — answer_type=text, min_length=20
3. `how-it-works` — "플러그인은 어떻게 작동하나요?" — answer_type=text, min_length=20
4. `ai-usage` — "AI를 어떻게 활용했나요?" — answer_type=text, min_length=20
5. `how-verified` — "어떻게 검증했나요?" — answer_type=text, min_length=20

Non-negotiable rules:
- All 5 questions must be present in canonical order. Reorder is a product change.
- `InterviewState.to_dict()` and `from_dict()` must round-trip without loss.
- Missing required schema fields raise `SchemaError` — no silent defaults.
- Zero references to "dev-kit" in any source comment, docstring, or string literal.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_question_schema.py -v → exit 0 (5 questions present, all fields populated)
AC2: python -m pytest tests/test_interview_state.py -v → exit 0 (transitions + round-trip + validation errors)
AC3: python -c "from src.schema.questions import QUESTIONS; assert len(QUESTIONS) == 5; ids = [q['id'] for q in QUESTIONS]; assert ids == ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']" → exit 0
AC4: python -c "from src.schema.state import InterviewState; s = InterviewState(); s.set_answer('what-who-where','x'*25); d=s.to_dict(); s2=InterviewState.from_dict(d); assert s2.answers == s.answers" → exit 0
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/0-mvp/index.json` for THIS step (one of three outcomes):
   - **Success** → `"status": "completed"`, `"summary": "<one-line: files created/modified + key decisions>"`
   - **Unrecoverable failure** (3 retries exhausted) → `"status": "error"`, `"error_message": "<concrete error: which AC failed, with exit code + last 3 lines>"`
   - **External dependency** (API key, manual config, human approval) → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP — do not continue to the next step.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply. The build runner parses them with the regex in `lib/execute.py:parse_status_marker()`:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

The marker value MUST match the `status` field written to `index.json` in step 2.

## Don't
- Do not change the canonical question text or order. 이유: the 5-question interview is the product surface; changing prompts is a product change, not a refactor.
- Do not add "dev-kit" anywhere in source, comments, or docstrings. 이유: non-goal (b) — this plugin is standalone; mentioning dev-kit violates the "separate plugin" requirement.
- Do not emit any log line. 이유: non-goal (1) defers logging to a later stage.
- Do not write outside `src/schema/`, `src/schema/__init__.py`, `tests/test_question_schema.py`, `tests/test_interview_state.py`. 이유: path scope declared in `## Read first`.
- Do not skip writing tests first (TDD methodology, per CLAUDE.md §2). 이유: Iron Law L1 (no prod code without verification artifact).
