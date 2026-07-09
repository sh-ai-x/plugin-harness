# Step 3: Dual-runtime plugin emitter

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (schema)
- `phases/0-mvp/step1.md` (engine)
- `phases/0-mvp/step2.md` (assembler)
- `phases/0-mvp/step3.md` (this file)

## Task
Take the assembled idea plan + the completed interview state and emit the plugin files in the Codex layout (which is the canonical layout; CC uses the same SKILL.md and .mcp.json). The emitter is the build-time counterpart to the interview.

Output layout (locked):
```
<output_dir>/
├── src/
│   ├── .codex-plugin/plugin.json
│   ├── skills/<plugin_slug>/SKILL.md
│   └── .mcp.json
└── README.md
```

Files to create:
- `src/emitter/__init__.py`
- `src/emitter/codex.py` — `emit(state: InterviewState, plan_md: str, output_dir: Path) -> EmitResult`
- `src/emitter/validator.py` — `validate_emit(output_dir: Path) -> ValidationReport` checks the 4 files exist with required fields
- `src/emitter/templates/codex/plugin.json.j2`
- `src/emitter/templates/codex/SKILL.md.j2`
- `src/emitter/templates/codex/mcp.json.j2`
- `src/emitter/templates/codex/README.md.j2`
- `tests/test_emitter.py` — pytest: emit produces the 4 files with valid contents; validator catches missing fields
- `tests/fixtures/sample_state.json`
- `docs/codex-plugin.schema.json` — vendored copy of the Codex plugin schema (downloaded from https://developers.openai.com/codex/plugins; pinned to a specific version; used by the validator)

Field derivation (locked):
- `plugin.json.name` → derived from idea plan title (kebab-case)
- `plugin.json.description` → from answer to "what-who-where" (first 200 chars)
- `SKILL.md` body → from answer to "how-it-works" + the assembled plan
- `.mcp.json.servers` → empty array (the harness emits no MCP servers in MVP; teams add their own)
- `README.md` → assembled plan verbatim

Non-negotiable rules:
- All 4 output files MUST be created; missing file → `EmitError`.
- `plugin.json` MUST validate against the vendored `docs/codex-plugin.schema.json` (NOT against the live URL — that may change). The validator loads the vendored schema and runs `jsonschema.validate`. Validator MUST reject bad shapes with a typed error.
- Re-running `emit` on the same `output_dir` MUST be idempotent (overwrite, no duplicates).
- Output MUST NOT contain "dev-kit" string anywhere.
- User-supplied answer text MUST be JSON-escaped before insertion into `plugin.json` (use `json.dumps`, not f-strings) and Markdown/Jinja-escaped before insertion into `SKILL.md` / `README.md` (escape `{`, `}`, `{{`, `}}`, `%`, `#` to prevent Jinja2 SSTI / template injection; escape Markdown as in step 2).

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_emitter.py -v → exit 0 (emit + validate + idempotency + escape-injection + schema-roundtrip)
AC2: python -c "from src.emitter.codex import emit; from src.emitter.validator import validate_emit; from src.schema.state import InterviewState; import tempfile, pathlib; s=InterviewState(); [s.set_answer(q,'x'*30) for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']]; plan='# Idea Plan — test\n\n## 1. What\nx'; d=pathlib.Path(tempfile.mkdtemp()); emit(s, plan, d); r=validate_emit(d); assert r.ok" → exit 0
AC3: python -c "from src.emitter.validator import validate_emit; import pathlib, tempfile; r=validate_emit(pathlib.Path(tempfile.mkdtemp())); assert not r.ok" → exit 0
AC4: python -c "import json, jsonschema, pathlib; schema=json.load(open('docs/codex-plugin.schema.json')); emitted=json.load(open('<tmp>/src/.codex-plugin/plugin.json')); jsonschema.validate(emitted, schema)" → exit 0 (round-trip against vendored schema)
AC5: python -c "from src.emitter.codex import emit; from src.schema.state import InterviewState; import tempfile, pathlib; s=InterviewState(); s.set_answer('how-it-works','{{7*7}}'); [s.set_answer(q,'x'*30) for q in ['what-who-where','why-this-problem','ai-usage','how-verified']]; d=pathlib.Path(tempfile.mkdtemp()); emit(s, '# plan', d); skill=open(d/'src/skills/test/SKILL.md').read(); assert '{{7*7}}' in skill and '49' not in skill" → exit 0 (Jinja SSTI neutralized)
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
- Do not skip any of the 4 output files. 이유: the Codex layout is the product contract.
- Do not add MCP servers in MVP. 이유: scope — teams add their own; keep the emitter minimal.
- Do not mention "dev-kit" in any emitted file. 이유: non-goal (b).
- Do not write outside `src/emitter/`, `tests/test_emitter.py`, `tests/fixtures/sample_state.json`. 이유: path scope.
- Do not skip TDD. 이유: Iron Law L1.
