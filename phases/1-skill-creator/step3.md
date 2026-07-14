# Step 3: CC + Codex adapters register skill-creator and plugin-creator as native skills

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step4.md` (CC adapter — extends, do not fork)
- `phases/0-mvp/step5.md` (Codex adapter — extends, do not fork)
- `src/adapter/cc.py`, `src/adapter/codex.py` (existing adapters)
- `src/adapter/cc_skills/plugin-harness/SKILL.md`, `src/adapter/codex_skills/plugin-harness/SKILL.md` (existing skill assets — pattern reference)
- `phases/1-skill-creator/step0.md` (skill spec + validators — `validate_skill_md` is consumed here)
- `phases/1-skill-creator/step1.md` (skill-creator mode)
- `phases/1-skill-creator/step2.md` (plugin-creator mode)
- `phases/1-skill-creator/step3.md` (this file)

## Task
Extend the existing `register_cc` and `codex_install` adapters to ALSO register `skill-creator` and `plugin-creator` as native runtime skills. After install, the user can invoke `skill-creator` or `plugin-creator` directly via the runtime's skill mechanism — `/<name>:` in CC, the Codex skill loader in Codex.

Files to modify:
- `src/adapter/cc.py` — `register_cc` (existing, do not modify signature) gains a sibling `register_cc_skill(name: str, root: Path) -> InstallReport` that copies the SKILL.md asset to `<root>/.claude/skills/<name>/SKILL.md` and validates against the CC schema from step 0. Idempotent — re-runs overwrite, no duplicates.
- `src/adapter/codex.py` — `codex_install` (existing, do not modify signature) gains a sibling `register_codex_skill(name: str, root: Path) -> InstallReport` that copies to `<root>/.codex/skills/<name>/SKILL.md` and validates against the Codex schema from step 0. Idempotent.

Files to create:
- `src/adapter/cc_skills/skill-creator/SKILL.md` — NEW. CC-native skill wrapping `python -m src.engine.cli new --mode=skill_create`. Body MUST validate against CC schema.
- `src/adapter/codex_skills/skill-creator/SKILL.md` + `__init__.py` — NEW. Codex-native skill wrapping the same CLI invocation. Body MUST validate against Codex schema.
- `src/adapter/cc_skills/plugin-creator/SKILL.md` — NEW. CC-native wrapping `python -m src.engine.cli new --mode=plugin_create`.
- `src/adapter/codex_skills/plugin-creator/SKILL.md` + `__init__.py` — NEW. Codex-native.
- `tests/test_skill_adapter.py` — pytest: each of the 4 install paths (CC × {skill-creator, plugin-creator}, Codex × {skill-creator, plugin-creator}) installs idempotently; each installed file validates against the right step 0 spec; no `dev-kit` substring in any installed file; `register_cc` and `codex_install` signatures unchanged (zero regression on 0-mvp).

Non-negotiable rules:
- Each installed SKILL.md MUST validate via `validate_skill_md(path, runtime)` from step 0 (CC install → CC validate, Codex install → Codex validate).
- Install MUST be idempotent — re-running `register_cc_skill('skill-creator')` produces the same end state as a single run; no leftover files, no error.
- Each installed file's body MUST NOT contain "dev-kit" (extends non-goal b).
- The adapter CLI command in the SKILL.md body MUST be `python -m src.engine.cli new --mode=<mode>` — exactly the same CLI surface, not a separate entry point. This guarantees that step 1 and step 2 are the only places where mode-specific logic lives.
- `register_cc` and `codex_install` signatures MUST NOT change — 0-mvp's install path is unchanged for backward compat.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_skill_adapter.py -v → exit 0 (4 install paths × idempotent × schema-validates × no-dev-kit-substring × backward-compat of 0-mvp's register_cc / codex_install)
AC2: python -c "
import pathlib, tempfile
from src.adapter.cc import register_cc_skill
from src.adapter.codex import register_codex_skill
tmp = pathlib.Path(tempfile.mkdtemp())
register_cc_skill('skill-creator', tmp)
register_codex_skill('skill-creator', tmp)
assert (tmp/'.claude/skills/skill-creator/SKILL.md').exists()
assert (tmp/'.codex/skills/skill-creator/SKILL.md').exists()
register_cc_skill('skill-creator', tmp)
register_codex_skill('skill-creator', tmp)
assert len(list((tmp/'.claude/skills/skill-creator').iterdir())) == 1, 'expected exactly one file in CC skill dir after rerun'
assert len(list((tmp/'.codex/skills/skill-creator').iterdir())) == 1, 'expected exactly one file in Codex skill dir after rerun'
print('OK')
" → exit 0 (idempotent install — both runtimes)
AC3: bash -c '! grep -r "dev-kit" src/adapter/cc_skills src/adapter/codex_skills' → exit 1
AC4: python -c "
import pathlib, tempfile
from src.adapter.cc import register_cc_skill
from src.skill_schema.validator import validate_skill_md
tmp = pathlib.Path(tempfile.mkdtemp())
register_cc_skill('skill-creator', tmp)
r = validate_skill_md(tmp/'.claude/skills/skill-creator/SKILL.md', 'cc')
assert r.ok, r.errors
print('OK')
" → exit 0
AC5: python -c "
import pathlib, tempfile
from src.adapter.codex import register_codex_skill
from src.skill_schema.validator import validate_skill_md
tmp = pathlib.Path(tempfile.mkdtemp())
register_codex_skill('plugin-creator', tmp)
r = validate_skill_md(tmp/'.codex/skills/plugin-creator/SKILL.md', 'codex')
assert r.ok, r.errors
print('OK')
" → exit 0 (Codex plugin-creator installs and validates)
AC6: python -c "import inspect; from src.adapter.cc import register_cc; from src.adapter.codex import codex_install; assert 'install_root' in inspect.signature(register_cc).parameters or 'root' in inspect.signature(register_cc).parameters; assert 'install_root' in inspect.signature(codex_install).parameters or 'root' in inspect.signature(codex_install).parameters" → exit 0 (0-mvp's register_cc / codex_install signature unchanged — backward compat verified)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/1-skill-creator/index.json` for THIS step.
3. Emit the two-line HTML-comment marker per the pinned contract.

## Don't
- Do not fork the existing `register_cc` / `codex_install` adapters. 이유: extend, don't duplicate; 0-mvp's install path is unchanged.
- Do not create a separate CLI entry for skill-creator / plugin-creator. 이유: it's the same `src.engine.cli` with `--mode=` switch; new entry points fragment the surface.
- Do not introduce a runtime cross-compiler (CC↔Codex). 이유: phase1 non-goal 2.
- Do not write outside `src/adapter/cc.py`, `src/adapter/codex.py`, `src/adapter/{cc,codex}_skills/{skill,plugin}-creator/`, `tests/test_skill_adapter.py`. 이유: path scope.
- Do not skip TDD. 이유: Iron Law L1.
