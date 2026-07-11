# plugin-harness

> 5-question interview → dual-runtime (Claude Code + Codex) plugin emitter.

A CLI that interviews you through five fixed questions about an idea, assembles
a structured idea plan, and emits the plugin files in a layout that installs
identically in [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
and [Codex](https://github.com/openai/codex). Built for non-coders who need to
operationalize an AI workflow for a team without hand-editing `plugin.json`
and `SKILL.md`.

- **Interviews:** 5 fixed questions (`what/who/where`, `why-this-problem`,
  `how-it-works`, `ai-usage`, `how-verified`). Order, text, and validation
  thresholds are the product surface — see `src/schema/questions.py`.
- **Modes:** `user` (interactive answers) or `ai-research` (runtime tool
  surface drafts answers from a one-line idea).
- **Emits:** Codex layout (`src/.codex-plugin/plugin.json`,
  `src/skills/<slug>/SKILL.md`, `src/.mcp.json`, `README.md`) plus Claude
  Code slash-command + skill adapters that install alongside.

## Install

```bash
python -m pip install -e .
```

Requires Python ≥ 3.10. Runtime deps (pinned in `pyproject.toml`):
`jinja2 >= 3.1, < 4` and `jsonschema >= 4.18, < 5`.

## Usage

Start an interview for a one-line idea:

```bash
python -m src.engine.cli new "<one-line idea>" --mode user
# or
python -m src.engine.cli new "<one-line idea>" --mode ai-research
```

Exit codes:

| Code | Meaning |
|-----:|---------|
| 0 | Interview completed; final stdout line is `complete` |
| 2 | Invalid CLI args |
| 3 | User aborted (Ctrl-C / EOF / empty input) |
| 4 | Validation failure on a submitted answer |

From inside Claude Code or Codex, invoke the installed slash command / skill
(`/plugin-harness …`) — both adapters delegate to the same engine entry point.

## Architecture

```
src/
├── schema/         canonical 5-question schema + InterviewState codec
├── engine/         interview runner + CLI; per-mode (user / ai-research) dispatch
├── assembler/      idea-plan assembly (jinja2 templates)
├── emitter/        Codex-layout file emission + JSON Schema validation
└── adapter/        runtime surfaces:
    ├── cc.py       Claude Code slash command + skill
    ├── codex.py    Codex skill
    └── install.py  cross-runtime installer
```

The engine is one process; the adapters are thin wrappers that install the
right surface for each runtime and forward into the same `run_interview()`
loop. `scripts/e2e.sh` asserts runtime parity — CC `SKILL.md` body must match
Codex `SKILL.md` body byte-for-byte, modulo front-matter.

## Development

```bash
bash scripts/test.sh       # pytest tests/ (installs pytest/jinja2/jsonschema if missing)
bash scripts/e2e.sh        # full dual-runtime pipeline: schema → engine → emitter → adapters
bash scripts/ci-local.sh   # local equivalent of the GitHub Actions `validate` job
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
| `tests/e2e/test_full_pipeline.py` | full pipeline end-to-end |
| `tests/e2e/test_smoke.py` | cross-runtime parity smoke |

## CI

`.github/workflows/ci.yml` runs three jobs:

- **branch-policy** — fail-closed on direct push to `main` (requires an
  associated merged PR). Mirrored client-side by `.githooks/pre-push`.
- **test** — `bash scripts/test.sh` on `pull_request` and `workflow_dispatch`.
- **validate** — `python3 scripts/validate.py` on the same triggers.

Client-side: opt into the local pre-push hook with
`git config core.hooksPath .githooks`. Direct pushes that bypass it
(`git push --no-verify`) are caught by the in-workflow check.

## Contributing

Per `.claude/rules/git-workflow.md`, every change goes on a fresh worktree +
branch (`<type>/<slug>`, e.g. `fix/cli-nameerror`, `feat/new-mode`). Direct
commits to `main` are blocked by `hooks/git-guard.sh`; edits in the main
checkout are blocked by `hooks/worktree-guard.sh`.

PR title: `<type>(<scope>): <subject>` (Conventional Commits). Body must
include a quoted test plan with exit codes / test counts.

## Status

Early-stage (v0.1.0 per `pyproject.toml`). No license file is included in
this repository yet — assume all rights reserved unless one is added.