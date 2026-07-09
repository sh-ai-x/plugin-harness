# Step 4: Claude Code adapter

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (schema)
- `phases/0-mvp/step1.md` (engine)
- `phases/0-mvp/step2.md` (assembler)
- `phases/0-mvp/step3.md` (emitter)
- `phases/0-mvp/step4.md` (this file)

## Task
Make the harness invokable from Claude Code as a slash command + a skill. The CC adapter is a thin shell wrapper that exposes `src/engine/cli.py` to the user via CC's slash-command surface.

Files to create:
- `src/adapter/__init__.py`
- `src/adapter/cc.py` — `register_cc(project_dir: Path) -> None` installs the slash command and skill manifest
- `src/adapter/cc_commands/plugin-harness.md` — the CC slash command body (markdown front-matter + body invoking `python -m src.engine.cli`)
- `src/adapter/cc_skills/plugin-harness/SKILL.md` — the CC skill body (same engine, CC-mode invocation)
- `tests/test_cc_adapter.py` — pytest: register_cc creates the 2 files with valid contents; idempotent
- `tests/fixtures/cc_install/expected/.claude/commands/plugin-harness.md`

Non-negotiable rules:
- `register_cc` MUST create the slash command at `.claude/commands/plugin-harness.md` and the skill at `.claude/skills/plugin-harness/SKILL.md`.
- Both files MUST point at the same `src.engine.cli` entrypoint (one command, two surfaces).
- Re-running `register_cc` MUST be idempotent (overwrite, no duplicates).
- Output MUST NOT contain "dev-kit" string anywhere.
- The adapter is the install-time surface; it does not modify runtime behavior of the engine.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_cc_adapter.py -v → exit 0 (file creation + idempotency + content sanity)
AC2: python -c "from src.adapter.cc import register_cc; import pathlib, tempfile; d=pathlib.Path(tempfile.mkdtemp()); register_cc(d); assert (d/'.claude/commands/plugin-harness.md').exists(); assert (d/'.claude/skills/plugin-harness/SKILL.md').exists()" → exit 0
AC3: bash -c '! grep -rq "dev-kit" src/adapter/ 2>/dev/null' → exit 0 (no dev-kit token in adapter source)
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

## Don't
- Do not modify the engine CLI in this step. 이유: step 1 owns the engine; this step only adapts the surface.
- Do not mention "dev-kit" in any emitted file. 이유: non-goal (b).
- Do not write outside `src/adapter/`, `tests/test_cc_adapter.py`, `tests/fixtures/cc_install/`, EXCEPT the adapter install paths under `.claude/commands/` and `.claude/skills/` inside the target `project_dir` passed to `register_cc`. Those writes are the adapter's contract — they are NOT inside the plugin's own source tree. 이유: path scope clarification.
- Do not skip TDD. 이유: Iron Law L1.
