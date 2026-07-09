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
- `src/emitter/validator.py` — `validate_emit(output_dir: Path) -> ValidationReport` checks the 4 files exist with required fields, runs `jsonschema.validate` against `docs/codex-plugin.schema.json`
- `src/emitter/templates/codex/plugin.json.j2`
- `src/emitter/templates/codex/SKILL.md.j2`
- `src/emitter/templates/codex/mcp.json.j2`
- `src/emitter/templates/codex/README.md.j2`
- `tests/test_emitter.py` — pytest: emit produces the 4 files with valid contents; validator catches missing fields
- `tests/fixtures/sample_state.json`

Pre-existing files consumed (NOT created by this step):
- `docs/codex-plugin.schema.json` — vendored copy of the Codex plugin schema. Must be in place before this step runs. Step 3 AC0 verifies the file does NOT contain the literal "Pinned placeholder" marker (the build bootstrap is responsible for replacing any placeholder with the real vendored copy). If AC0 fails, the step reports `status: blocked` with `blocked_reason: docs/codex-plugin.schema.json is still a placeholder; vendor the real schema first`.

Field derivation (locked):
- `plugin.json.name` → derived from idea plan title (kebab-case)
- `plugin.json.version` → constant `"0.1.0"` for MVP (bump manually per release). Required by the schema; without it AC4 round-trip fails.
- `plugin.json.description` → from answer to "what-who-where" (first 200 chars)
- `SKILL.md` body → from answer to "how-it-works" + the assembled plan
- `.mcp.json.mcpServers` → empty array (the harness emits no MCP servers in MVP; teams add their own). Field name MUST be `mcpServers` (camelCase) to match the Codex schema and MCP spec; `servers` is non-standard and silently ignored at load time.
- `README.md` → assembled plan verbatim

Non-negotiable rules:
- All 4 output files MUST be created; missing file → `EmitError`.
- `plugin.json` MUST validate against the vendored `docs/codex-plugin.schema.json` (NOT against the live URL — that may change). The validator loads the vendored schema and runs `jsonschema.validate`. Validator MUST reject bad shapes with a typed error.
- Re-running `emit` on the same `output_dir` MUST be idempotent (overwrite, no duplicates).
- Output MUST NOT contain "dev-kit" string anywhere.
- User-supplied answer text MUST be JSON-escaped before insertion into `plugin.json` (use `json.dumps`, not f-strings) and Markdown-escaped before insertion into `SKILL.md` / `README.md` (escape as in step 2: `[`, `]`, `<`, `>`, `` ` ``, `#`, `*`, `_`, leading `>`).
- The Jinja2 SSTI defense uses **Jinja value-substitution with `|e` filter** in the templates ONLY. The emitter does NOT perform character-level escaping of `{`, `}`, `{{`, `}}`, `%`, `#`. User text passes through unchanged; the template `{{ user_text | e }}` (which escapes via Markup) renders safely. AC5 verifies end-to-end render-through.

## Acceptance Criteria
```bash
AC0: bash -c '! grep -q "Pinned placeholder" docs/codex-plugin.schema.json' → exit 0 (vendored schema is real, not a placeholder); if fail, step reports `status: blocked`
AC1: python -m pytest tests/test_emitter.py -v → exit 0 (emit + validate + idempotency + escape-injection + schema-roundtrip)
AC2: python -c "from src.emitter.codex import emit; from src.emitter.validator import validate_emit; from src.schema.state import InterviewState; import tempfile, pathlib; s=InterviewState(); [s.set_answer(q,'x'*30) for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']]; plan='# Idea Plan — test\n\n## 1. What\nx'; d=pathlib.Path(tempfile.mkdtemp()); emit(s, plan, d); r=validate_emit(d); assert r.ok" → exit 0
AC3: python -c "from src.emitter.validator import validate_emit; import pathlib, tempfile; r=validate_emit(pathlib.Path(tempfile.mkdtemp())); assert not r.ok" → exit 0
AC4: python -c "import json, jsonschema, pathlib, tempfile; from src.emitter.codex import emit; from src.schema.state import InterviewState; d=pathlib.Path(tempfile.mkdtemp()); s=InterviewState(); [s.set_answer(q,'x'*30) for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']]; emit(s, '# Idea Plan — test\n\n## 1. What\nx', d); schema=json.load(open('docs/codex-plugin.schema.json')); emitted=json.load(open(d/'src/.codex-plugin/plugin.json')); jsonschema.validate(emitted, schema); assert emitted['version'] == '0.1.0'; assert emitted['name']; mcp=json.load(open(d/'src/.mcp.json')); assert mcp.get('mcpServers') == []" → exit 0 (round-trip against vendored schema, with version + name + mcpServers key)
AC5: python -c "from jinja2 import Environment; env=Environment(autoescape=True); tpl=env.from_string(open('src/emitter/templates/codex/SKILL.md.j2').read()); rendered=tpl.render(how_it_works='{{7*7}}', plan='# plan'); assert '49' not in rendered and '{{7*7}}' not in rendered" → exit 0 (end-to-end SSTI defense: template uses `{{ how_it_works | e }}` (autoescape on); the literal `{{7*7}}` user input is rendered as the escaped text `{{7*7}}` and Jinja does NOT evaluate it; `49` (the result of `7*7`) never appears in the rendered output)
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
- Do not write outside `src/emitter/`, `tests/test_emitter.py`, `tests/fixtures/sample_state.json`, EXCEPT reading `docs/codex-plugin.schema.json` (consumed, not modified) and writing the 4 emitted files inside the caller's `output_dir` (those are the emitter's contract). 이유: path scope clarification.
- Do not skip TDD. 이유: Iron Law L1.
