# Step 1: skill-creator: 3-question interview + dual SKILL.md emitter

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step1.md` (interview engine — pattern reference; do not modify 0-mvp)
- `phases/0-mvp/step3.md` (Codex emitter — pattern reference; do not modify)
- `phases/1-skill-creator/step0.md` (skill spec + validators — `load_spec` and `validate_skill_md` are consumed here)
- `phases/1-skill-creator/step1.md` (this file)

## Task
Add `mode=skill_create` to the existing `src/engine/runner.py` and a new `src/engine/modes/skill_create.py` that runs a 3-question interview (purpose, examples, success-criteria) and emits a SKILL.md for each of CC and Codex — two distinct files in two distinct directory layouts, both validated against the spec from step 0.

Files to create:
- `src/skill_schema/prompts.py` — `SKILL_QUESTIONS: list[dict]` (3 questions: `purpose`, `examples`, `success-criteria`), analogous to 0-mvp's `src/schema/questions.py` BUT a SEPARATE schema (do NOT modify 0-mvp's).
- `src/engine/modes/skill_create.py` — `SkillInterviewState` composing 0-mvp's `InterviewState` semantics (round-trip serialization + validation errors) but bound to the 3Q schema. Reuses 0-mvp's answer type `text` and min-length validation.
- `src/emitter/skill.py` — `emit_skill(state, output_dir: Path) -> EmitResult` produces TWO files:
  - `output_dir/.claude/skills/<slug>/SKILL.md` (CC layout)
  - `output_dir/.codex/skills/<slug>/SKILL.md` (Codex layout, distinct path)
  Both files validated via `validate_skill_md` from step 0. Both MUST contain the same body content; only the frontmatter shape differs.
- `src/engine/cli.py` — extend the existing CLI to accept `--mode=skill_create` (route to `SkillInterviewState` + `emit_skill`); preserve existing `--mode=user_driven` and `--mode=ai_research` paths unchanged (the `mode` argument is already in the runner signature per 0-mvp step 1).
- `tests/test_skill_sub_mode.py` — pytest: 3Q interview runs end-to-end; emit produces both files; both validate against the right spec; idempotent re-run; slug derivation is deterministic.
- `tests/fixtures/skill_state.json`.

Field derivation (locked, no drift between two emitters of the same state):
- `name` (frontmatter, both runtimes) → kebab-case slug derived from the `purpose` answer (first 5 words, lowercased, alphanumeric and hyphen only).
- `description` (CC only) → first sentence of `purpose` + first 80 chars of `examples`, capped at 1024 chars.
- `metadata` (Codex only) → JSON object with keys `slug`, `examples_count` (int), `success_criteria_present` (bool). No Markdown body.
- SKILL.md body (both files) → joined text from `examples` + `success-criteria` answers, Markdown-escaped.

Non-negotiable rules:
- Both emitted files MUST validate via `validate_skill_md(path, runtime)` from step 0. If either fails, `emit_skill` raises `EmitError` with the file path and the validator's `errors` list.
- Re-running `emit_skill` on the same `output_dir` MUST be idempotent (overwrite, no duplicates, no `--force` flag required).
- Output MUST NOT contain "dev-kit" string anywhere.
- The slug derivation function MUST be deterministic — same `purpose` produces same `name` across runs.
- `src/skill_schema/prompts.py` MUST NOT import from or modify `src/schema/questions.py`; the two schemas are independent surfaces.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_skill_sub_mode.py -v → exit 0 (3Q interview round-trip; emit produces both files; both validate; idempotent re-run; deterministic slug)
AC2: python -c "from src.skill_schema.prompts import SKILL_QUESTIONS; assert len(SKILL_QUESTIONS) == 3; ids=[q['id'] for q in SKILL_QUESTIONS]; assert ids == ['purpose','examples','success-criteria']" → exit 0
AC3: python -c "
import pathlib, subprocess, tempfile
from src.skill_schema.validator import validate_skill_md
ans = 'x'*30
out = pathlib.Path(tempfile.mkdtemp())
subprocess.run(['python','-m','src.engine.cli','new','--mode=skill_create','--output-dir',str(out),'--purpose',ans,'--examples',ans,'--success-criteria',ans], check=True, capture_output=True)
cc_files = list((out/'.claude/skills').rglob('SKILL.md'))
cx_files = list((out/'.codex/skills').rglob('SKILL.md'))
assert cc_files and cx_files, (cc_files, cx_files)
assert validate_skill_md(cc_files[0], 'cc').ok
assert validate_skill_md(cx_files[0], 'codex').ok
print('OK', cc_files[0], cx_files[0])
" → exit 0 (CLI smoke + both emitted SKILL.md files validate against step 0 specs)
AC4: bash -c '! grep -r "dev-kit" src/skill_schema/prompts.py src/emitter/skill.py src/engine/modes/skill_create.py' → exit 1 (no matches — extends non-goal b)
AC5: python -c "from src.engine.runner import runner; import inspect; sig=inspect.signature(runner); assert 'mode' in sig.parameters" → exit 0 (runner already accepts the mode argument; backward compatible with 0-mvp's --mode=user_driven)
AC6: python -c "
import pathlib, tempfile
from src.emitter.skill import emit_skill
from src.engine.modes.skill_create import SkillInterviewState
out = pathlib.Path(tempfile.mkdtemp())
s = SkillInterviewState()
s.set_answer('purpose', 'Convert user handoff into an interview transcript')
s.set_answer('examples', 'Sales-call-to-pricing-doc handoff')
s.set_answer('success-criteria', 'PRD filled from handoff within 5 minutes')
emit_skill(s, out)
emit_skill(s, out)
cc = list((out/'.claude/skills').rglob('SKILL.md'))
assert len(cc) == 1
print('OK')
" → exit 0 (idempotency — re-running emit produces exactly one CC SKILL.md)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/1-skill-creator/index.json` for THIS step (one of three outcomes per the pinned contract).
3. Emit the two-line HTML-comment marker per the pinned contract.

## Don't
- Do not modify `src/schema/questions.py` (0-mvp's 5 questions). 이유: phase1 non-goal 1 — the two schemas are independent surfaces; product order is locked.
- Do not emit a single combined "dual-runtime" SKILL.md that both runtimes read. 이유: format divergence; each runtime reads its own file in its own path.
- Do not introduce a runtime cross-compiler. 이유: phase1 non-goal 2.
- Do not write outside `src/skill_schema/prompts.py`, `src/engine/modes/skill_create.py`, `src/emitter/skill.py`, `tests/test_skill_sub_mode.py`, `tests/fixtures/skill_state.json`. EXCEPT extending `src/engine/cli.py` (consumed by both phases; this is the only allowed cross-phase write in step 1) and writing the two emitted skill files inside the caller's `--output-dir`.
- Do not skip TDD. 이유: Iron Law L1.
