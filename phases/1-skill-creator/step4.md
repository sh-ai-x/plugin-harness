# Step 4: E2E + dual-runtime parity test

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step6.md` (e2e smoke — pattern reused; do not modify)
- `scripts/e2e.sh` (0-mvp e2e entry — pattern reference)
- `phases/1-skill-creator/step0.md` (skill spec + validators)
- `phases/1-skill-creator/step1.md` (skill-creator mode)
- `phases/1-skill-creator/step2.md` (plugin-creator mode)
- `phases/1-skill-creator/step3.md` (adapter install)
- `phases/1-skill-creator/step4.md` (this file)

## Task
End-to-end smoke test for both new sub-modes, plus a "dual-runtime parity" assertion: for the same set of interview answers, the CC SKILL.md and Codex SKILL.md emitted by step 1 differ ONLY in frontmatter (a known, locked divergence), and the BODY is byte-identical. The parity test IS the **kill condition** defined in Gate 2 cycle 2 — bypassing it would silently ship a single-runtime pair, violating the dual-runtime promise.

Files to create:
- `scripts/e2e-skill-creator.sh` — bash entrypoint. Runs in sequence:
  1. `python -m src.engine.cli new --mode=skill_create --output-dir <tmp>` against a sample fixture
  2. `python -m src.engine.cli new --mode=plugin_create --output-dir <tmp2> --skill-slug <name>`
  3. CC install: `register_cc_skill('skill-creator', <tmp3>)` + `register_cc_skill('plugin-creator', <tmp3>)`
  4. Codex install: `register_codex_skill('skill-creator', <tmp3>)` + `register_codex_skill('plugin-creator', <tmp3>)`
  5. parity check (step 4 own logic): compare CC vs Codex SKILL.md bodies byte-for-byte
  6. Re-run steps 1–5 to confirm idempotency
  Exits 0 only if every step succeeds; non-zero on any failure with the failing step's stderr surfaced to the runner.
- `tests/e2e/test_skill_creator_e2e.py` — pytest: invokes `scripts/e2e-skill-creator.sh` via `subprocess.run` in a tmpdir, asserts exit 0, asserts the 4 expected files (CC + Codex SKILL.md for each sub-mode) validate against step 0.
- `tests/e2e/test_dual_runtime_parity.py` — pytest: parse the emitted CC SKILL.md and Codex SKILL.md; strip frontmatter (between the leading `---` markers); assert bodies are byte-equal; assert frontmatter keys differ ONLY in the locked runtime-specific set (`name`+`description` for CC; `name`+`metadata` for Codex; no other key may appear in one but not the other).
- `tests/e2e/fixtures/skill_creator_sample_answers.json` — reproducible fixture answers for the 3 skill-create questions (purpose, examples, success-criteria).

Non-negotiable rules:
- The parity test MUST fail (exit non-zero) if either runtime ships fewer features than the other — e.g., a body byte that differs, or a frontmatter field that is missing on one side.
- The e2e script MUST be self-contained and reproducible — no network calls, no environment variables beyond what 0-mvp's `scripts/e2e.sh` already requires (PATH, PYTHONPATH only).
- The parity test runs for BOTH sub-modes: `skill_create` and `plugin_create`. The `plugin_create` case additionally verifies `plugin.json` validates against the 0-mvp vendored schema at `docs/codex-plugin.schema.json`.
- The e2e + parity tests MUST be the LAST step in this phase — they consume the outputs of steps 0, 1, 2, 3.

## Acceptance Criteria
```bash
AC1: bash scripts/e2e-skill-creator.sh → exit 0 (full e2e: emit + install + parity check + idempotent rerun; non-zero on any failure)
AC2: python -m pytest tests/e2e/test_skill_creator_e2e.py tests/e2e/test_dual_runtime_parity.py -v → exit 0 (parity: CC SKILL body == Codex SKILL body byte-equal; frontmatter keys differ ONLY in the locked runtime-specific set, for both sub-modes)
AC3: python -c "import json; data = json.load(open('tests/e2e/fixtures/skill_creator_sample_answers.json')); assert 'purpose' in data or any(k.startswith('purpose') for k in data.keys()); print('OK')" → exit 0 (fixture has a `purpose` answer for skill_create)
AC4: bash -c '! grep -r "dev-kit" tests/e2e/test_skill_creator_e2e.py tests/e2e/test_dual_runtime_parity.py scripts/e2e-skill-creator.sh' → exit 1 (no matches — non-goal b)
AC5: bash scripts/ci-local.sh → exit 0 (CI-local full suite still green after phase1 lands; no regression on 0-mvp)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/1-skill-creator/index.json` for THIS step.
3. Emit the two-line HTML-comment marker per the pinned contract.

## Don't
- Do not skip the parity test. 이유: it IS the kill condition from Gate 2 cycle 2; bypassing it would silently ship a single-runtime pair.
- Do not write outside `scripts/e2e-skill-creator.sh`, `tests/e2e/test_skill_creator_e2e.py`, `tests/e2e/test_dual_runtime_parity.py`, `tests/e2e/fixtures/skill_creator_sample_answers.json`. 이유: path scope.
- Do not add a "if CC fails, ship Codex-only" branch. 이유: that's a single-runtime strategy, not dual-runtime; it would trigger the kill condition and require a separate PRD.
- Do not skip TDD. 이유: Iron Law L1.
