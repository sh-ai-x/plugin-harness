# plugin-harness

> Interview-driven authoring for dual-runtime (Claude Code + Codex) plugins
> and skills. One CLI, two runtimes: identical install on each side.

A CLI that interviews you through a fixed set of questions about an idea and
produces structured artifacts that install identically in
[Claude Code](https://docs.anthropic.com/en/docs/claude-code) and
[Codex](https://github.com/openai/codex). Three interview flows ship today:

- **`plugin-harness new`** (5 questions, `--mode user`): structured idea plan
  + a full Codex-layout plugin (`src/.codex-plugin/plugin.json`,
  `src/skills/<slug>/SKILL.md`, `src/.mcp.json`, `README.md`).
- **`skill-creator`** (3 questions, `--mode=skill_create`): a single dual-runtime
  `SKILL.md` pair (`<output>/.claude/skills/<slug>/SKILL.md`,
  `<output>/.codex/skills/<slug>/SKILL.md`), validated against vendored schemas.
- **`plugin-creator`** (5 questions, `--skill-slug <slug>`): the existing
  plugin flow plus a dual-runtime skill bundle — a `plugin.json` AND a skill
  per `--skill-slug`.

The engine is one process; per-mode dispatch lives in `src/engine/modes/`.
Built for non-coders who need to operationalize an AI workflow for a team
without hand-editing `plugin.json` and `SKILL.md`.

- **Interviews:** two schemas shipped — 5 questions for plugins
  (`what/who/where`, `why-this-problem`, `how-it-works`, `ai-usage`,
  `how-verified`; see `src/schema/questions.py`) and 3 questions for skills
  (`purpose`, `examples`, `success-criteria`; see
  `src/skill_schema/prompts.py`). Order, text, and validation thresholds are
  the product surface for each.
- **Modes (plugin):** `user` (interactive answers) or `ai-research` (runtime
  tool surface drafts answers from a one-line idea).
- **Modes (skill):** `skill_create` (3-question skill authorship; see
  `Skill authoring` below).
- **Emits (downstream):** Codex layout (`src/.codex-plugin/plugin.json`,
  `src/skills/<slug>/SKILL.md`, `src/.mcp.json`, `README.md`) plus dual-runtime
  skill files (`.claude/skills/<slug>/SKILL.md`, `.codex/skills/<slug>/SKILL.md`)
  plus CC slash-command + skill adapters that install alongside.

## Install

```bash
python -m pip install -e .
```

Requires Python ≥ 3.10. Runtime deps (pinned in `pyproject.toml`):
`jinja2 >= 3.1, < 4` and `jsonschema >= 4.18, < 5`.

## Usage

### Plugin authoring (5-question flow)

Start an interview for a one-line idea:

```bash
python -m src.engine.cli new "<one-line idea>" --mode user
# or
python -m src.engine.cli new "<one-line idea>" --mode ai-research
```

Exit codes (apply to all modes):

| Code | Meaning |
|-----:|---------|
| 0 | Interview completed; final stdout line is `complete` |
| 2 | Invalid CLI args |
| 3 | User aborted (Ctrl-C / EOF on stdin) |
| 4 | Validation failure on a submitted answer |

The CLI runs the interview and prints `complete` on stdout; downstream
plan assembly + plugin-file emission are library calls
(`src/assembler/plan`, `src/emitter/codex`) that callers invoke separately.
The Claude Code + Codex slash-command / skill adapters in `src/adapter/`
wrap that same engine entry point and register themselves only inside
their respective runtime hosts — `pip install -e .` does **not** register
a `/plugin-harness` command.

### Skill authoring (3-question flow)

The `skill-create` sub-mode runs a focused 3-question interview
(`purpose` / `examples` / `success-criteria`) and emits a **pair**
of `SKILL.md` files — one for Claude Code, one for Codex — so the
resulting skill loads identically in both runtimes.

```bash
# Interactive: prompts purpose, examples, success-criteria via stdin;
# on 'complete', emits both SKILL.md files into <dir>.
python -m src.engine.cli new "<one-line idea>" \
    --mode=skill_create --output-dir <dir>

# Library call (test-friendly, fully programmatic):
python -c "
from pathlib import Path
from src.engine.modes.skill_create import SkillInterviewState, run_skill_interview
from src.emitter.skill import emit_skill

state = SkillInterviewState()
state.set_answer('purpose',           'A description of what the skill does ...')
state.advance()
state.set_answer('examples',          'One or two concrete usage examples ...')
state.advance()
state.set_answer('success-criteria',  'Acceptance criteria for the done state ...')
state.advance()
result = emit_skill(state, Path('<dir>'))
print(result.cc_path, result.codex_path)
"
```

**Output layout:**

```
<dir>/
├── .claude/
│   └── skills/<slug>/SKILL.md     ← Claude Code layout, validated against docs/cc-skill.schema.json
└── .codex/
    └── skills/<slug>/SKILL.md     ← Codex layout, validated against docs/codex-skill.schema.json
```

`<slug>` is derived deterministically from the `purpose` answer (first 5
alphabetic tokens after stripping articles/prepositions, lowercased,
hyphenated, ≤ 64 chars). Same purpose → same slug across runs.

**Atomicity:** both rendered bodies are validated in-memory (against the
step-0 vendored schemas and the `dev-kit` substring guard) BEFORE any
file is written. A failed validation raises `EmitError` and **no file
lands on disk**. Re-running on the same `<dir>` is idempotent (overwrite
in place; no `.bak` files; no duplicates).

**No atomic magic — invalid SLUG wins are rejectd up front.** If the
`purpose` answer yields no usable tokens, slug defaults to `skill`. The
validator rejects `dev-kit` (and any other substring on the configured
blocklist) in the `description` field.

### Plugin + bundled skill (5Q + skill bundle)

Add `--skill-slug <slug>` (repeatable) to a normal `plugin-harness new`
invocation. The 5-question schema is reused unchanged; `src/emitter/codex.emit`
is reused for the canonical Codex-layout plugin files; the **new**
emitter `src/emitter/plugin_skill_bundle.emit_plugin_skill_bundle()`
additionally writes one `.claude/skills/<slug>/SKILL.md` and one
`.codex/skills/<slug>/SKILL.md` per `--skill-slug`.

```bash
# One bundled skill under the plugin
python -m src.engine.cli new "<one-line idea>" \
    --mode=user --output-dir <dir> --skill-slug intake-form

# N bundled skills
python -m src.engine.cli new "<one-line idea>" \
    --mode=user --output-dir <dir> \
    --skill-slug intake-form --skill-slug followup-email --skill-slug status-update
```

**Output layout under `--output-dir`:**

```
<dir>/
├── src/
│   ├── .codex-plugin/plugin.json                          ← from src.emitter.codex.emit (unchanged)
│   ├── .mcp.json                                         ← from src.emitter.codex.emit
│   ├── skills/<plugin_slug>/SKILL.md                     ← canonical Codex layout
│   └── ...
├── README.md                                             ← from src.emitter.codex.emit
├── .claude/skills/<slug>/SKILL.md                        ← per --skill-slug, CC layout
└── .codex/skills/<slug>/SKILL.md                        ← per --skill-slug, Codex layout
```

**Atomicity:** the canonical plugin files are written first (by the
0-mvp emitter); only after the in-memory dual-skill bundle validates
against step-0 specs does the writer commit the bundle files. On
validation failure, `EmitError` is raised and **no bundle file lands**
(0-mvp's canonical files may already exist — that's its pre-existing
behavior).

**No `--force` flag needed.** Re-running is idempotent; pre-existing
plugin.json / .mcp.json / README.md are overwritten.

### Adapter install

After authoring, install the surface for each runtime. The adapter
siblings (`register_cc_skill`, `register_codex_skill`) handle the new
`skill-creator` and `plugin-creator` skills alongside the 0-mvp
`register_cc` / `register_codex`.

```python
from pathlib import Path
from src.adapter.cc import register_cc, register_cc_skill
from src.adapter.codex import register_codex, register_codex_skill

project = Path(".")

# Original plugin-harness install (0-mvp, unchanged signature).
register_cc(project)        # slash command + skill at .claude/commands + .claude/skills/plugin-harness/
register_codex(project)     # skill at .agents/skills/plugin-harness/SKILL.md

# New 1-skill-creator installs (each independently re-runnable).
register_cc_skill("skill-creator",  project)   # -> .claude/skills/skill-creator/SKILL.md
register_cc_skill("plugin-creator", project)   # -> .claude/skills/plugin-creator/SKILL.md
register_codex_skill("skill-creator",  project) # -> .codex/skills/skill-creator/SKILL.md
register_codex_skill("plugin-creator", project) # -> .codex/skills/plugin-creator/SKILL.md
```

All install functions are idempotent: re-running produces the same
end state (no `.bak.<ts>` files for skills; overwrite-in-place).
Symlink chains under the install path are refused defensively
(see `src/adapter/install.py`).

### Validating existing artifacts

If you already have `SKILL.md` files on disk and want to check them
against the vendored schemas without re-emitting:

```python
from pathlib import Path
from src.skill_schema.validator import validate_skill_md

r = validate_skill_md(Path(".claude/skills/my-skill/SKILL.md"), runtime="cc")
print(r.ok, r.errors)            # ok=True or list of human-readable errors
print(r.runtime)                 # "cc" — runtime tag echoes what you asked for
```

### What ships with the engine (vs. what is installed by it)

The CLI runs the interview + emit. It does NOT register runtime surface
artifacts into a project — that is the adapter's job. `pip install -e .`
gives you the engine and library API; `register_cc_skill(...)` etc.
materialize the per-runtime surface on the filesystem.

## Architecture

```
src/
├── schema/         canonical 5-question schema + InterviewState codec
├── skill_schema/   vendored skill frontmatter schemas (cc, codex) + 3-question schema + frontmatter validator
├── engine/         interview runner + CLI; per-mode (user, ai-research, skill_create) dispatch
├── assembler/      idea-plan assembly (jinja2 templates)
├── emitter/        Codex-layout file emission + JSON Schema validation
│   ├── codex.py            canonical 0-mvp plugin emit
│   ├── skill.py            dual-runtime SKILL.md emit (skill_create)
│   └── plugin_skill_bundle.py   plugin.json + dual-skill bundle (--skill-slug)
└── adapter/        runtime surfaces:
    ├── cc.py       Claude Code slash command + skill + new register_cc_skill()
    ├── codex.py    Codex skill + new register_codex_skill()
    └── install.py  shared install-time primitives (atomic write, backup, symlink-chain refuse)
```

The engine is one process; the per-mode dispatch (registry in
`src/engine/modes/__init__.py`) routes to the right question schema and
per-question handler. The adapters are thin wrappers that install the
right surface for each runtime and forward into the same `run_interview()`
loop. `scripts/ci-local.sh` (and the `tests/e2e/test_dual_runtime_parity.py`
kill-condition check) assert runtime parity — CC `SKILL.md` body must
match Codex `SKILL.md` body byte-for-byte, modulo front-matter.

## Development

```bash
bash scripts/test.sh       # pytest tests/ (installs pytest/jinja2/jsonschema if missing)
bash scripts/e2e.sh        # full dual-runtime pipeline: schema → engine → emitter → adapters
bash scripts/ci-local.sh   # local CI: validate + test (mirrors what .github/workflows/ci.yml runs)
bash scripts/smoke.sh      # lightweight smoke check
```

Test layout:

| Path | Scope |
|------|-------|
| `tests/test_question_schema.py` | 5 questions present, immutable |
| `tests/test_interview_state.py` | state codec, validation, cursor |
| `tests/test_runner.py` | engine loop + per-mode dispatch |
| `tests/test_cli.py` | argparse, exit codes, mode registry |
| `tests/test_assembler.py` | idea-plan jinja templates |
| `tests/test_emitter.py` | Codex layout emission + JSON Schema |
| `tests/test_cc_adapter.py` | Claude Code adapter install surface |
| `tests/test_codex_adapter.py` | Codex adapter install surface |
| `tests/test_skill_schema.py` | step 0: vendored skill frontmatter schemas + validator |
| `tests/test_skill_prompts.py` | step 1: 3-question skill_create schema |
| `tests/test_skill_sub_mode.py` | step 1: SkillInterviewState + emit_skill |
| `tests/test_plugin_sub_mode.py` | step 2: emit_plugin_skill_bundle |
| `tests/test_skill_adapter.py` | step 3: register_cc_skill + register_codex_skill |
| `tests/e2e/test_dual_runtime_parity.py` | step 4: kill condition — CC body byte-equal Codex body |
| `tests/e2e/test_skill_creator_e2e.py` | step 4: end-to-end smoke |
| `tests/e2e/test_full_pipeline.py` | full pipeline end-to-end |
| `tests/e2e/test_smoke.py` | cross-runtime parity smoke |

## CI

`.github/workflows/ci.yml` runs three jobs:

- **branch-policy** — fail-closed on direct push to `main` whose commit
  has no associated PR (probes `GET /repos/{owner}/{repo}/commits/{sha}/pulls`;
  empty array means "direct push bypassing review"). Mirrored client-side
  by `.githooks/pre-push`.
- **test** — `bash scripts/test.sh` on `pull_request` and `workflow_dispatch`.
- **validate** — `python3 scripts/validate.py` on the same triggers.

Client-side: opt into the local pre-push hook with
`git config core.hooksPath .githooks`. Direct pushes that bypass it
(`git push --no-verify`) are caught by the in-workflow check.

## Contributing

Per `.claude/rules/git-workflow.md`, every change goes on a fresh worktree +
branch (`<type>/<slug>`, e.g. `fix/cli-nameerror`, `feat/new-mode`). The
project ships three enforcement hooks in `hooks/`:
- `worktree-guard.sh` (PreToolUse Edit/Write) — hard-blocks edits in the main checkout.
- `task-detector.sh` (UserPromptSubmit) — early-warning nudge when new-task intent is detected in the main checkout.
- `session-start-check.sh` (SessionStart) — gentle nudge when the session starts in the main checkout.

PR title: `<type>(<scope>): <subject>` (Conventional Commits). Body must
include a quoted test plan with exit codes / test counts.

## Status

Early-stage (v0.1.0 per `pyproject.toml`). No license file is included in
this repository yet — assume all rights reserved unless one is added.