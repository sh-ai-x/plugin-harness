# Step 1: Interview engine (2 modes)

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (creates `src/schema/`)
- `phases/0-mvp/step1.md` (this file)

## Task
Build the interview engine that drives the 5-question flow. Two modes:
- **Mode A — user-driven**: prompts the user with one question at a time, reads stdin
- **Mode B — AI-research**: tool-calls Claude/Codex to fill in answers from a one-line idea (uses the runtime's tool surface)

CLI entrypoint: `python -m src.engine.cli new "<one-line idea>" [--mode user|ai-research]`

Files to create:
- `src/engine/__init__.py`
- `src/engine/cli.py` — argparse, dispatches to mode handler
- `src/engine/modes/user_driven.py` — prints prompt, reads input, calls `set_answer`
- `src/engine/modes/ai_research.py` — uses runtime tool calls (CC: `Bash`/`WebFetch`/`WebSearch`; Codex: equivalent) to draft answers
- `src/engine/runner.py` — `run_interview(state, mode) -> InterviewState` shared loop
- `tests/test_runner.py` — pytest: both modes advance state, mode A reads from a fake stdin, mode B calls injected tool surface
- `tests/test_cli.py` — pytest: argparse, --mode flag, dispatch

Non-negotiable rules:
- Mode A MUST NOT call any tool that requires network or write. Pure stdin/stdout.
- Mode B MUST use only the runtime's provided tool surface (no hidden imports, no subprocess to other tools).
- Either mode produces a complete `InterviewState` (all 5 answers) or fails with a typed `InterviewIncompleteError`.
- The CLI MUST exit 0 on success and non-zero on user abort (Ctrl-C, empty input, validation failure).
- Zero references to "dev-kit" anywhere.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_runner.py -v → exit 0 (both modes advance + complete state)
AC2: python -m pytest tests/test_cli.py -v → exit 0 (argparse + dispatch)
AC3: echo -e "x\\ny\\nz\\na\\nb" | python -m src.engine.cli new "test idea" --mode user → exit 0, prints "complete"
AC4: python -m src.engine.cli new "test" --mode invalid 2>&1 | grep -q "invalid choice" → exit 0
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/0-mvp/index.json` for THIS step (one of three outcomes):
   - **Success** → `"status": "completed"`, `"summary": "<one-line: files created/modified + key decisions>"`
   - **Unrecoverable failure** (3 retries exhausted) → `"status": "error"`, `"error_message": "<concrete error: which AC failed, with exit code + last 3 lines>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

The marker value MUST match the `status` field written to `index.json` in step 2.

## Don't
- Do not silently truncate or skip questions. 이유: the 5-question interview is the product surface; skipping is a contract violation.
- Do not add log emission. 이유: non-goal (1) defers logging to a later stage.
- Do not write outside `src/engine/`, `tests/test_runner.py`, `tests/test_cli.py`. 이유: path scope.
- Do not use dev-kit as a dependency. 이유: non-goal (b) — standalone plugin.
- Do not skip TDD — write tests first. 이유: Iron Law L1.
