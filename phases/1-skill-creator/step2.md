# Step 2: plugin-creator: 5-question interview + plugin.json + dual-skill bundle emitter

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (5-question schema — REUSED here; do not modify)
- `phases/0-mvp/step1.md` (interview engine — REUSED)
- `phases/0-mvp/step2.md` (assembler — REUSED)
- `phases/0-mvp/step3.md` (Codex emitter — REUSED; do not fork; phase1 extends via the skill-bundle path)
- `phases/1-skill-creator/step0.md` (skill schema + validators)
- `phases/1-skill-creator/step1.md` (skill-creator mode + emitter — pattern reused here for the SKILL.md bundle)
- `phases/1-skill-creator/step2.md` (this file)

## Task
Add `mode=plugin_create` that runs the existing 0-mvp 5-question interview and emits a `plugin.json` PLUS a BUNDLE of CC + Codex SKILL.md files under a single plugin root. The plugin-creator output is what the 0-mvp emitter already produces, PLUS a `skills/` subtree in BOTH the CC layout AND the Codex layout (two trees, same SKILL content but distinct metadata).

Files to create:
- `src/engine/modes/plugin_create.py` — `PluginInterviewState` reuses 0-mvp's `InterviewState` (no schema change). Adds a `skill_slugs: list[str]` field for the N bundled SKILLs (default empty list; populated by the CLI from a CLI flag or stdin).
- `src/emitter/plugin_skill_bundle.py` — `emit_plugin_skill_bundle(state, plan_md, output_dir, skill_slugs) -> EmitResult` produces:
  - `output_dir/src/.codex-plugin/plugin.json` (reuses 0-mvp's emitter — DO NOT duplicate)
  - `output_dir/src/.mcp.json` (reuses 0-mvp's emitter — DO NOT duplicate)
  - `output_dir/src/skills/<plugin_slug>/SKILL.md` (Codex layout — reuses 0-mvp's template + plan_md; the canonical path, per the 0-mvp layout)
  - `output_dir/.claude/skills/<plugin_slug>/SKILL.md` (CC layout — NEW; same body, different frontmatter; validates against step 0 CC spec)
  - `output_dir/.codex/skills/<plugin_slug>/SKILL.md` (Codex layout — NEW; same body, different frontmatter; validates against step 0 Codex spec)
  Both CC and Codex SKILL.md files validate against the step 0 schemas via `validate_skill_md`.
- `src/engine/cli.py` — extend to accept `--mode=plugin_create` (and a `--skill-slug` flag for the bundled skill name; default empty list).
- `tests/test_plugin_sub_mode.py` — pytest: 5Q interview end-to-end (reuses `src.schema.questions.QUESTIONS`); emit produces `plugin.json` + CC SKILL.md + Codex SKILL.md; all validate against the right schema; idempotent; `skill_slugs` defaults and explicit list both work.
- `tests/fixtures/plugin_state_with_skills.json`.

Non-negotiable rules:
- `src/engine/modes/plugin_create.py` MUST NOT duplicate the 5 questions; REUSE `src.schema.questions.QUESTIONS`.
- `plugin.json` MUST validate against the vendored `docs/codex-plugin.schema.json` (extends 0-mvp's contract).
- Both CC and Codex SKILL.md files MUST validate via step 0's `validate_skill_md` with the correct runtime argument.
- Re-running `emit_plugin_skill_bundle` on the same `output_dir` MUST be idempotent.
- Output MUST NOT contain "dev-kit" string anywhere.
- `plugin.json.version` MUST equal `"0.1.0"` (extends 0-mvp step 3 AC4).

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_plugin_sub_mode.py -v → exit 0 (5Q interview round-trip; plugin.json + CC SKILL.md + Codex SKILL.md emitted; all validate; idempotent; skill_slugs defaults and explicit both work)
AC2: python -c "
import json, jsonschema, pathlib, tempfile
from src.schema.state import InterviewState
from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
s = InterviewState()
for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']:
    s.set_answer(q, 'x'*30)
d = pathlib.Path(tempfile.mkdtemp())
emit_plugin_skill_bundle(s, '# plan', d, skill_slugs=['demo-skill'])
assert (d/'src/.codex-plugin/plugin.json').exists()
assert (d/'.claude/skills/demo-skill/SKILL.md').exists()
assert (d/'.codex/skills/demo-skill/SKILL.md').exists()
schema = json.load(open('docs/codex-plugin.schema.json'))
plugin = json.load(open(d/'src/.codex-plugin/plugin.json'))
jsonschema.validate(plugin, schema)
assert plugin['version'] == '0.1.0'
assert plugin['name']
print('OK')
" → exit 0 (plugin.json validates against vendored schema; CC + Codex layout SKILL.md files both exist)
AC3: python -c "
import pathlib, tempfile
from src.schema.state import InterviewState
from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
from src.skill_schema.validator import validate_skill_md
s = InterviewState()
for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']:
    s.set_answer(q, 'x'*30)
d = pathlib.Path(tempfile.mkdtemp())
emit_plugin_skill_bundle(s, '# plan', d, skill_slugs=['demo-skill'])
cc = next(iter((d/'.claude/skills/demo-skill').rglob('SKILL.md')))
cx = next(iter((d/'.codex/skills/demo-skill').rglob('SKILL.md')))
assert validate_skill_md(cc, 'cc').ok
assert validate_skill_md(cx, 'codex').ok
print('OK')
" → exit 0 (both emitted skill files validate against step 0 specs)
AC4: bash -c '! grep -r "dev-kit" src/engine/modes/plugin_create.py src/emitter/plugin_skill_bundle.py' → exit 1
AC5: python -c "from src.engine.modes.plugin_create import PluginInterviewState; from src.schema.questions import QUESTIONS; assert PluginInterviewState.questions == QUESTIONS" → exit 0 (plugin_create reuses 0-mvp's questions, no duplication)
AC6: python -c "
import pathlib, tempfile
from src.schema.state import InterviewState
from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
s = InterviewState()
for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']:
    s.set_answer(q, 'x'*30)
d = pathlib.Path(tempfile.mkdtemp())
emit_plugin_skill_bundle(s, '# plan', d, skill_slugs=['demo-skill'])
emit_plugin_skill_bundle(s, '# plan', d, skill_slugs=['demo-skill'])
assert len(list((d/'.claude/skills/demo-skill').iterdir())) == 1, 'expected exactly one file in CC skill dir after rerun'
assert len(list((d/'.codex/skills/demo-skill').iterdir())) == 1, 'expected exactly one file in Codex skill dir after rerun'
print('OK')
" → exit 0 (idempotent rerun)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/1-skill-creator/index.json` for THIS step.
3. Emit the two-line HTML-comment marker per the pinned contract.

## Don't
- Do not modify 0-mvp's emitter. 이유: it ships; plugin_create EXTENDS it via the skill bundle path.
- Do not modify 0-mvp's question schema. 이유: phase1 non-goal 1; 0-mvp's question order is the product surface.
- Do not introduce a "plugin-creator-only" question schema. 이유: plugin_create reuses 0-mvp's 5 questions; user-driven and plugin_create are the same interview.
- Do not emit a single combined skill file. 이유: format divergence is real (CC vs Codex frontmatter shape).
- Do not write outside `src/engine/modes/plugin_create.py`, `src/emitter/plugin_skill_bundle.py`, `tests/test_plugin_sub_mode.py`, `tests/fixtures/plugin_state_with_skills.json`. EXCEPT extending `src/engine/cli.py` (consumed by both phases; this is the only allowed cross-phase write) and the emitted files inside the caller's `--output-dir`.
- Do not skip TDD. 이유: Iron Law L1.
