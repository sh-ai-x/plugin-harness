# Step 6: E2E test + cross-runtime smoke test

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (schema)
- `phases/0-mvp/step1.md` (engine)
- `phases/0-mvp/step2.md` (assembler)
- `phases/0-mvp/step3.md` (emitter)
- `phases/0-mvp/step4.md` (CC adapter)
- `phases/0-mvp/step5.md` (Codex adapter)
- `phases/0-mvp/step6.md` (this file)

## Task
Wire the full pipeline into one command and prove it runs end-to-end on both runtimes. This is the integration step that proves the dual-runtime claim.

Pipeline: `interview (mode A, scripted stdin, full 5-question flow) → assembler → emitter → cc_adapter.register → codex_adapter.register → runtime-parity check (CC skill body == Codex skill body byte-for-byte, modulo install path prefix) → smoke`

The `runtime-parity check` is a concrete assertion: both adapters write a `SKILL.md` file; the e2e script extracts the body (everything after the front-matter) and asserts byte-identical content. The install paths differ (`.claude/skills/plugin-harness/SKILL.md` vs `.codex/skills/plugin-harness/SKILL.md`) but the bodies must match — this proves the dual-runtime contract.

Files to create:
- `scripts/e2e.sh` — bash entrypoint that runs the full pipeline against a temp project dir, asserts both adapters install, asserts emitted plugin passes validator
- `tests/e2e/test_full_pipeline.py` — pytest that calls the same pipeline programmatically
- `scripts/smoke.sh` — quick smoke (full 5-question flow, both adapters install, validator passes; per step 0 the 5-question contract is locked, so the smoke runs the full flow, not an abbreviation)
- `tests/e2e/test_smoke.py` — pytest wrapper for smoke

Non-negotiable rules:
- `scripts/e2e.sh` MUST exit 0 only if every step succeeds; any step failure → non-zero exit and stderr message naming the failing step.
- Both `cc_adapter` AND `codex_adapter` MUST run against the same `output_dir` and produce non-overlapping installs (CC under `.claude/`, Codex under `.codex/`).
- The validator MUST pass on the emitted plugin (round-trip with step 3's validator).
- Output MUST NOT contain "dev-kit" string anywhere.

## Acceptance Criteria
```bash
AC1: bash scripts/e2e.sh → exit 0
AC2: python -m pytest tests/e2e/test_full_pipeline.py -v → exit 0
AC3: bash scripts/smoke.sh → exit 0
AC4: python -m pytest tests/e2e/test_smoke.py -v → exit 0
AC5: bash -c 'set -e; TMP=$(mktemp -d); python -m src.engine.cli new "test idea" --mode user < <(printf "answer-one-with-at-least-twenty-chars\\nanswer-two-with-at-least-twenty-chars\\nanswer-three-with-at-least-twenty-chars\\nanswer-four-with-at-least-twenty-chars\\nanswer-five-with-at-least-twenty-chars\\n") >/dev/null; python -c "from src.emitter.codex import emit; from src.schema.state import InterviewState; import pathlib; s=InterviewState(); [s.set_answer(q, q + \"-text-padded-to-meet-min-length-requirement\") for q in [\"what-who-where\",\"why-this-problem\",\"how-it-works\",\"ai-usage\",\"how-verified\"]]; emit(s, \"# plan\", pathlib.Path(\"$TMP\"))"; ! grep -rq "dev-kit" src/ scripts/ tests/ "$TMP" 2>/dev/null; rm -rf "$TMP"' → exit 0 (no dev-kit token in source, scripts, tests, OR the emitted plugin files in output_dir)
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
- Do not skip the dual-runtime assertion. 이유: the dual-runtime claim is the core product surface; single-runtime tests do not validate it.
- Do not silently pass when one runtime fails. 이유: silent pass on dual-runtime smoke = silent regression on the contract.
- Do not mention "dev-kit" anywhere. 이유: non-goal (b).
- Do not write outside `scripts/`, `tests/e2e/`. 이유: path scope.
- Do not skip TDD. 이유: Iron Law L1.
