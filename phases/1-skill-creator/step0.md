# Step 0: Dual-runtime skill spec + validators

## Status
**pending** — last update: 2026-07-14T00:00:00Z

## Read first
- `/PRD.md`
- `docs/ARCHITECTURE.md` (does not exist in this project)
- `docs/ADR.md` (does not exist in this project)
- `phases/0-mvp/step3.md` (Codex plugin emitter — analogous emitter pattern, for prior-art comparison only; do NOT modify)
- `phases/1-skill-creator/step0.md` (this file)

## Task
Vendored JSON Schemas for both runtimes' SKILL.md frontmatter, plus a Python module that loads the schemas and validates a SKILL.md source against the right shape. This is the schema surface for steps 1 and 2 — both sub-modes emit SKILL.md files that MUST validate before the emitter claims done.

Files to create:
- `docs/cc-skill.schema.json` — vendored JSON Schema for Claude Code skill frontmatter. Required keys: `name` (kebab-case, ≤64 chars), `description` (≤1024 chars). Forbids (rejected): empty `name`, `dev-kit` substring in `description`.
- `docs/codex-skill.schema.json` — vendored JSON Schema for Codex skill frontmatter. Required keys: `name` (kebab-case), `metadata` (object). Forbids: same name/description shape drift; missing `metadata` block.
- `src/skill_schema/__init__.py`
- `src/skill_schema/loader.py` — `load_spec(runtime: Literal["cc","codex"]) -> dict` reads the appropriate file under `docs/` and returns the parsed JSON Schema. Cached at module import.
- `src/skill_schema/validator.py` — `validate_skill_md(path: Path, runtime: Literal["cc","codex"]) -> ValidationReport` extracts YAML frontmatter (between two `---` lines), runs `jsonschema.validate` against the appropriate spec, returns a typed `ValidationReport` with `ok: bool`, `errors: list[str]`, `runtime: str`.
- `tests/test_skill_schema.py` — pytest: load_spec returns valid JSON Schemas for both runtimes; validate_skill_md accepts representative fixtures; rejects missing name, missing description, `dev-kit` substring, wrong-runtime frontmatter shape.
- `tests/fixtures/cc_skill_valid.md`, `tests/fixtures/cc_skill_invalid_name.md`, `tests/fixtures/cc_skill_invalid_devkit.md`, `tests/fixtures/codex_skill_valid.md`, `tests/fixtures/codex_skill_invalid_metadata.md`.

Non-negotiable rules:
- The vendored schemas MUST be real JSON Schemas (no "Pinned placeholder" marker). If either is a placeholder, the step is reported as `status: blocked` with `blocked_reason: "<file> is still a placeholder; vendor the real schema first"`.
- `validate_skill_md` MUST distinguish CC vs Codex runtime errors via the typed `ValidationReport.runtime` field. A CC file MUST NOT be validated against the Codex spec and vice versa.
- Zero references to "dev-kit" in any source comment, docstring, or string literal (extends 0-mvp non-goal b).
- The validator MUST NOT require network access — schemas are vendored under `docs/`, never fetched from a URL at runtime.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_skill_schema.py -v → exit 0 (CC schema + Codex schema validators active; valid fixtures pass; each invalid fixture rejected for the right reason)
AC2: python -c "from src.skill_schema.loader import load_spec; cc=load_spec('cc'); cx=load_spec('codex'); assert cc['type']=='object' and 'name' in cc['required'] and 'description' in cc['required']; assert cx['type']=='object' and 'name' in cx['required'] and 'metadata' in cx['required']" → exit 0
AC3: bash -c '! grep -q "Pinned placeholder" docs/cc-skill.schema.json docs/codex-skill.schema.json' → exit 0 (both vendored schemas are real, not placeholders)
AC4: python -c "import pathlib; from src.skill_schema.validator import validate_skill_md; r=validate_skill_md(pathlib.Path('tests/fixtures/cc_skill_invalid_name.md'), 'cc'); assert not r.ok and r.runtime=='cc'; assert any('name' in e.lower() for e in r.errors)" → exit 0 (rejects missing name with correct runtime tag)
AC5: bash -c '! grep -q "dev-kit" docs/cc-skill.schema.json docs/codex-skill.schema.json' → exit 0 (no matches in the two user-visible vendored schemas; src/ and tests/ are intentionally exempt — the validator implementation and its tests must reference the forbidden substring to assert on it; this extends non-goal b for emitted artifacts only)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/1-skill-creator/index.json` for THIS step (one of three outcomes):
   - **Success** → `"status": "completed"`, `"summary": "<one-line: files created/modified + key decisions>"`
   - **Unrecoverable failure** (3 retries exhausted) → `"status": "error"`, `"error_message": "<concrete error: which AC failed, with exit code + last 3 lines>"`
   - **External dependency** (placeholder schema, manual config, human approval) → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP — do not continue to the next step.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply. The build runner parses them with the regex in `lib/execute.py:parse_status_marker()`:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

The marker value MUST match the `status` field written to `index.json` in step 2. If the marker is missing or malformed, the runner falls back to the `index.json` status (best-effort, not blocking).

## Don't
- Do not fetch skill schemas from the network. 이유: vendored only; the validator must run offline.
- Do not write a single "generic skill" schema spanning both runtimes. 이유: format divergence is real; one schema fails validation on either runtime. The validator picks the right schema via the `runtime` argument.
- Do not emit any log line. 이유: extends 0-mvp non-goal 1.
- Do not write outside `docs/cc-skill.schema.json`, `docs/codex-skill.schema.json`, `src/skill_schema/`, `tests/test_skill_schema.py`, `tests/fixtures/`. 이유: path scope declared in `## Read first`.
- Do not skip TDD. 이유: Iron Law L1 — tests first.
