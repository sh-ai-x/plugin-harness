# Step 4: E2E test asserting zero `python -m src.engine.cli` invocations during interview

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `/phases/1-skill-rewrite/step0.md`, `step1.md`, `step2.md`, `step3.md` (all prior steps in this phase)
- `/tests/e2e/` (existing e2e harness from 0-mvp step 6)
- `/scripts/e2e.sh` (existing e2e shell wrapper)
- `/phases/0-mvp/step6.md` (e2e-smoke design from prior phase)

## Task
Prove end-to-end that the skill-rewrite is complete: a fresh author can install both skills, run the 5-question interview through each runtime, and emit a Codex-layout plugin WITHOUT any `python -m src.engine.cli` invocation. This is the dual-runtime kill-condition that the entire phase is judged against.

Concrete changes:
1. Add `tests/e2e/test_skill_rewrite.py` (pytest e2e) that:
   - For each of CC and Codex: spawns the runtime's skill invocation in a sandbox (mock the runtime if no real one is available, per existing 0-mvp e2e pattern).
   - Feeds canned answers to the 5 questions.
   - Captures the process tree (or traces subprocess invocations via `subprocess` hooks) and asserts: no `python -m src.engine.cli` appears anywhere in the captured subprocess log.
   - Asserts the resulting plugin directory passes `python scripts/verify_emit.py` (step 3's kill-condition helper).
   - Asserts the resulting plugin directory is byte-equivalent to the 0-mvp reference fixture `tests/fixtures/sample_plugin/` for the 4 Codex-layout files (`plugin.json`, `SKILL.md`, `.mcp.json`, `README.md`).
2. Add `scripts/e2e_skill_rewrite.sh` that runs the e2e test in CI mode (no interactive prompts).
3. The e2e test MUST be hermetic — no network, no real runtime API calls, deterministic given canned answers.

Non-negotiable rules:
- The subprocess trace MUST cover every `os.exec*` / `subprocess.Popen` / `Bash` invocation the runtime makes during the interview + emit phase. If the trace can be bypassed, the test is invalid.
- The byte-equivalence check covers only the 4 Codex-layout files. The `<author_answers>` template variable may legitimately differ — do not assert byte-equivalence on parts of the README that interpolate answers.

## Acceptance Criteria
```bash
# AC0: e2e test exists and is registered with pytest
AC0: pytest --collect-only tests/e2e/test_skill_rewrite.py -q
# expected: exit 0, at least 2 tests collected (CC + Codex)

# AC1: e2e test passes for CC skill
AC1: pytest tests/e2e/test_skill_rewrite.py::test_cc_skill_rewrite -q
# expected: exit 0

# AC2: e2e test passes for Codex skill
AC2: pytest tests/e2e/test_skill_rewrite.py::test_codex_skill_rewrite -q
# expected: exit 0

# AC3: subprocess trace shows zero `python -m src.engine.cli` invocations
AC3: pytest tests/e2e/test_skill_rewrite.py -q -s 2>&1 | grep -c "python -m src.engine.cli"
# expected: 0 (exit 0 from grep -c is fine; the value must be 0)

# AC4: emitted Codex-layout files are byte-equivalent to 0-mvp reference fixture
AC4: diff -r tests/fixtures/sample_plugin/.codex-plugin/ /tmp/skill_rewrite_out_cc/.codex-plugin/ && \
     diff -r tests/fixtures/sample_plugin/skills/ /tmp/skill_rewrite_out_cc/skills/
# expected: exit 0 (no diff on the 4-file Codex layout)

# AC5: emitted plugin passes verify_emit.py (kill-condition from step 3)
AC5: python scripts/verify_emit.py /tmp/skill_rewrite_out_cc/ && \
     python scripts/verify_emit.py /tmp/skill_rewrite_out_codex/
# expected: exit 0

# AC6: full pytest suite green (e2e included)
AC6: pytest tests/ -q
# expected: exit 0 (count reported)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code (AC0..AC6 → exit 0).
2. Update `phases/1-skill-rewrite/index.json` for THIS step:
   - **Success** → `"status": "completed"`, `"summary": "<one-line: e2e proves zero-Python-shell interview + byte-equivalent Codex-layout emit on both runtimes>"`
   - **Unrecoverable failure** → `"status": "error"`, `"error_message": "<AC# + exit code + last 3 lines of pytest output>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed (e.g. fixture generation, runtime mock)>"`, then STOP.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

## Don't
- Do not assert byte-equivalence on parts of the README that interpolate answers. Reason: legitimate variance — only the 4-file Codex layout (`.codex-plugin/plugin.json`, `skills/<name>/SKILL.md`, `.mcp.json`, `README.md` skeleton) is the contract.
- Do not let the subprocess trace be bypassable. Reason: if the runtime can shell to Python unobserved, the kill-condition is unenforceable.
- Do not run e2e against the real runtime API. Reason: hermetic + deterministic is the contract; live API flakiness will mask real regressions.
- Do not skip AC3 (zero-Python-shell assertion). Reason: it's the entire reason this phase exists.