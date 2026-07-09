# Step 5: Codex adapter

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (schema)
- `phases/0-mvp/step1.md` (engine)
- `phases/0-mvp/step2.md` (assembler)
- `phases/0-mvp/step3.md` (emitter)
- `phases/0-mvp/step4.md` (CC adapter — sets the adapter pattern)
- `phases/0-mvp/step5.md` (this file)

## Task
Make the harness invokable from Codex as a skill. The Codex adapter mirrors the CC adapter shape but installs at the Codex skill path (`.codex/skills/<plugin_slug>/SKILL.md` or the path Codex expects per https://developers.openai.com/codex/skills).

Files to create:
- `src/adapter/codex.py` — `register_codex(project_dir: Path) -> None` installs the Codex skill manifest
- `src/adapter/codex_skills/plugin-harness/SKILL.md` — the Codex skill body
- `tests/test_codex_adapter.py` — pytest: register_codex creates the file with valid contents; idempotent
- `tests/fixtures/codex_install/expected/.codex/skills/plugin-harness/SKILL.md`

Non-negotiable rules:
- `register_codex` MUST create the skill at the path Codex expects (verify against https://developers.openai.com/codex/skills).
- The skill MUST invoke the same `src.engine.cli` entrypoint (one command, two surfaces).
- Re-running `register_codex` MUST be idempotent.
- Output MUST NOT contain "dev-kit" string anywhere.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_codex_adapter.py -v → exit 0 (file creation + idempotency + content sanity)
AC2: python -c "from src.adapter.codex import register_codex; import pathlib, tempfile; d=pathlib.Path(tempfile.mkdtemp()); register_codex(d); files=list(d.rglob('SKILL.md')); assert len(files) >= 1" → exit 0
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
- Do not duplicate the engine logic. 이유: step 1 owns the engine; this step only adapts the surface for Codex.
- Do not mention "dev-kit" in any emitted file. 이유: non-goal (b).
- Do not write outside `src/adapter/`, `tests/test_codex_adapter.py`, `tests/fixtures/codex_install/`, EXCEPT the adapter install paths under `.codex/skills/` inside the target `project_dir` passed to `register_codex`. Those writes are the adapter's contract — they are NOT inside the plugin's own source tree. 이유: path scope clarification.
- Do not skip TDD. 이유: Iron Law L1.
