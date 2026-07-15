# plugin-harness

> Authors Claude Code Skills, Claude Code Plugins, and Codex Skills per the
> official specs. One pipeline, two runtimes, no fork.

This project produces two kinds of runtime artifacts and installs them so
Claude Code and OpenAI Codex pick them up:

1. **SKILL.md files** — the [Agent Skills](https://agentskills.io) open
   standard that both runtimes consume. A SKILL.md is a Markdown file with
   YAML frontmatter (`name`, `description`) that Claude uses to decide
   whether to load a skill, and that a user invokes directly with
   `/skill-name` in Claude Code or `$skill-name` in Codex.
2. **Plugin bundles** — a directory with a `.claude-plugin/plugin.json`
   manifest plus one or more skills, agents, hooks, or MCP servers, loadable
   by Claude Code via `claude --plugin-dir <dir>` or `/plugin install` from a
   marketplace. Codex has its own distribution story (plugins as bundles of
   skills + connectors).

This README is grounded in three primary sources; the
[CLI sub-sections](#cli-ux-the-interview-flows) are secondary and optional:

- Claude Code Skills — <https://code.claude.com/docs/en/skills>
- Claude Code Plugins — <https://code.claude.com/docs/en/plugins>
- Codex Skills — <https://learn.chatgpt.com/docs/build-skills>

If any claim below disagrees with the official docs, **the docs win**. This
project does not redefine what a "skill" or a "plugin" is — it conforms.

---

## What is a skill, in current Claude and Codex?

| Runtime | Where SKILL.md lives | How the runtime sees it | Manual install path |
|---|---|---|---|
| **Claude Code** (user) | `~/.claude/skills/<name>/SKILL.md` | auto-loaded when relevant; explicit `/<name>` invoke | (managed by Claude Code itself) |
| **Claude Code** (project) | `.claude/skills/<name>/SKILL.md` | auto-loaded when relevant; explicit `/<name>` invoke | yes — drop into the directory |
| **Codex** (user) | `$HOME/.agents/skills/<name>/SKILL.md` | auto-loaded via description; explicit `$<name>` invoke | (managed by Codex itself) |
| **Codex** (repo) | `.agents/skills/<name>/SKILL.md` | auto-loaded via description | yes |
| **Codex** (admin) | `/etc/codex/skills/<name>/SKILL.md` | system-wide | (admin task) |

A skill is a **directory** containing one `SKILL.md` (plus optional
`scripts/`, `references/`, `assets/`). The `name` frontmatter field is the
invocation token; `description` is the auto-load hook. There is **no CLI
subcommand called "skill"** in either runtime — that abstraction lives
only at the file-system level. In Claude Code, `.claude/commands/<name>.md`
(a flat file) and `.claude/skills/<name>/SKILL.md` (a folder) create the
same `/<name>` invocation (per the merged-commands docs above).

This project's whole reason to exist is producing valid SKILL.md files in
**the right runtime directories** so the load happens without users having
to memorize where Claude Code and Codex look for skills.

## What is a plugin, in current Claude Code?

A **plugin** is a self-contained directory tree (anywhere on disk) that
ships one or more of:

| Sub-path on the plugin root | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | manifest (name, description, version, author) |
| `skills/<name>/SKILL.md`    | skills; invocation becomes `/<plugin-name>:<name>` |
| `commands/<name>.md`        | flat-Markdown skills, namespaced the same way |
| `agents/<name>.md`          | custom subagents |
| `hooks/hooks.json`          | event handlers |
| `.mcp.json`                 | MCP server registrations |
| `.lsp.json`                 | LSP server registrations |
| `monitors/monitors.json`    | background watchers |
| `bin/`                      | executables added to the Claude Bash PATH |
| `settings.json`             | default settings when the plugin is enabled |

Critically, plugin skills are **always namespaced** (`/plugin-name:skill-name`)
to avoid collisions across plugins. `/plugin-harness:skill-creator` and
`plugin-harness:plugin-creator` are exactly the kind of namespacing the
official Plugins docs prescribe.

Test a plugin locally:
```bash
claude --plugin-dir ./my-plugin
/reload-plugins
/my-plugin:hello
```

Codex has a different distribution model. **For Codex skills, drop
SKILL.md into `.agents/skills/<name>/SKILL.md` (repo), `$HOME/.agents/skills/<name>/SKILL.md`
(user), or `/etc/codex/skills/<name>/SKILL.md` (admin).** Codex currently
ships skills first-class; Codex plugins as a distribution bundle are
documented but lighter than the Claude Code plugin manifest.

---

## What this project produces, exactly

Inputs (one of): a 3-question interview answer set for a skill, a 5-question
interview answer set for a plugin. **Or, by library call, just a state
object or a path on disk.**

Artifacts emitted (validated in-memory against vendored schemas before
any file lands — see `src/skill_schema/validator.py`):

- **Claude Skill files** at `<output>/.claude/skills/<slug>/SKILL.md`
  with the Agent-Skills frontmatter (`name`, `description`, optional
  `disable-model-invocation`, `$ARGUMENTS` substitution).
- **Codex Skill files** at `<output>/.codex/skills/<slug>/SKILL.md` with
  the same Agent-Skills frontmatter; Codex reads the same shape.
- **Codex plugin layout** at `<output>/src/.codex-plugin/plugin.json`,
  `<output>/src/.mcp.json`, `<output>/src/skills/<slug>/SKILL.md`,
  `<output>/README.md` — the canonical 4-file layout that Codex exposes
  via `.agents/skills/`.
- (Future) **Claude plugin manifest** at
  `<output>/.claude-plugin/plugin.json` for packaging under
  `--plugin-dir` / `/plugin install`.

Installers (`src/adapter/cc.py` and `src/adapter/codex.py`):

| Function | Source | Destination | Idempotent |
|---|---|---|---|
| `register_cc(project)` | bundled `cc_commands/plugin-harness.md` + `cc_skills/plugin-harness/SKILL.md` | `.claude/commands/`, `.claude/skills/` | yes (overwrite) |
| `register_codex(project)` | bundled `codex_skills/plugin-harness/SKILL.md` | `.agents/skills/` | yes (overwrite + `.bak.<ts>`) |
| `register_cc_skill(name, project)` | bundled `cc_skills/<name>/SKILL.md` (allowlisted names) | `.claude/skills/<name>/SKILL.md` | yes (overwrite) |
| `register_codex_skill(name, project)` | bundled `codex_skills/<name>/SKILL.md` (allowlisted names) | `.codex/skills/<name>/SKILL.md` | yes (overwrite) |

The `register_*_skill` siblings install into the **runtime skill
directories** documented in the table above. After install, Claude Code
discovers the skills automatically (per the description frontmatter) and
the user can invoke them via `/<name>`.

The interview-driven flows in `src/engine/cli.py` (`--mode=user`,
`--mode=ai-research`, `--mode=skill_create`, `--skill-slug <slug>`) are
**one UX path** for authoring skill/plugin content — useful for non-coders.
The CLI does not redefine skills or plugins; it produces files in the same
shape those runtimes consume. Library callers (`src.assembler.plan`,
`src.emitter.{codex,skill,plugin_skill_bundle}`, `src.adapter.*`) skip the
interview entirely and produce the same artifacts programmatically.

---

## Install

The repo is a Claude Code plugin published through a **self-hosted
marketplace**. The plugin manifest lives at
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json); the
marketplace catalog entry is at
[`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json);
and a parallel Codex-side manifest is at
[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json). The three
SKILL.md assets ship at repo-root
[`skills/<name>/SKILL.md`](skills/) (Claude layout) and
`skills/<name>/SKILL.codex.md` (Codex layout companion).

The full install has **two parts**: (1) the user adds the marketplace
once; (2) the user installs the plugin from the marketplace. Both
happen from the Claude Code CLI.

### 1. Add the self-hosted marketplace (one-time, per machine)

Before running the `add` command: open
<https://github.com/sh-ai-x/plugin-harness> in a browser and confirm the
URL is the official plugin-harness repo. Self-hosted marketplace entries
land the user's machine in whatever repo the URL points to by design —
a typo'd URL could land you in an arbitrary repo. Verify first.

```bash
claude plugin marketplace add https://github.com/sh-ai-x/plugin-harness
```

Verify it registered:

```bash
claude plugin marketplace list
# expect a line containing: sh-ai-x-plugins  https://github.com/sh-ai-x/plugin-harness
```

To remove the marketplace later (without uninstalling the plugin
itself — the plugin is already on disk and survives marketplace removal):

```bash
claude plugin marketplace remove sh-ai-x-plugins
```

### 2. Install the plugin

```bash
claude plugin install plugin-harness
```

> **Security:** Adding a marketplace trusts the marketplace catalog and
> (after install) every plugin revision it resolves on `claude plugin
> update`. `marketplace.json` ships with `source.ref: "main"` (a mutable
> ref), so any merge to `main` is immediately served to users on the
> next `update`. The version-bump workflow pins a SHA only on its own
> future runs, not at user-install time. **Pin a marketplace SHA before
> installing and verify it against a signed release tag** — branch refs
> like `main` resolve to whatever the branch currently points at, so a
> compromise of `main` would be served to every user on their next
> update. The project has a follow-up plan to default `source.ref` to
> a pinned SHA + signed-tag workflow; for now, check the commit SHA at
> <https://github.com/sh-ai-x/plugin-harness/commits/main> before
> `claude plugin install`.

The CLI clones the repo (or pulls a vendored copy) and registers
`plugin-harness` with Claude Code. After install, three skills become
available as **namespaced slash commands**:

| Slash command | What it does |
|---|---|
| `/plugin-harness:plugin-harness` | 5-question plugin interview → Codex-layout plugin |
| `/plugin-harness:skill-creator` | 3-question skill interview → dual-runtime SKILL.md pair |
| `/plugin-harness:plugin-creator` | 5-question plugin + dual-runtime skill bundle |
| `/plugin-harness:new` | Primary CLI entry point: runs the interview engine with the flags you pass (`--mode user` / `--mode=skill_create` / `--mode=ai-research` / `--skill-slug <slug>` / `--output-dir <dir>`) |

Namespacing follows the Claude plugin convention: `<plugin-name>:<skill-name>`
to avoid collisions across plugins.

### 3. Verify the install

```bash
# Reload the plugin registry (always do this after install/update)
claude plugin reload

# Confirm the plugin is loaded
claude plugin list
# expect a line containing: plugin-harness  <version>  ...

# Confirm the three skills are visible
/help
# search for: /plugin-harness:plugin-harness  /plugin-harness:skill-creator  /plugin-harness:plugin-creator
```

### 4. Update an existing install

When the maintainer bumps the version (the
[version-bump workflow](.github/workflows/version-bump.yml) does this
on every merge to main), refresh your local install:

```bash
claude plugin update plugin-harness
claude plugin reload
```

If `update` errors (rare; usually a permissions issue on the cache
directory), uninstall + reinstall:

```bash
claude plugin uninstall plugin-harness
claude plugin install plugin-harness
```

### 5. Uninstall

```bash
claude plugin uninstall plugin-harness
```

The plugin's runtime artifacts (`.claude/skills/plugin-harness:*/SKILL.md`,
`.claude/commands/...`) are removed. The marketplace registration
persists (a separate removal if you want it gone too — see step 1).

### Dev-mode install (plugin-harness contributors)

If you're editing the plugin-harness source itself, point Claude
Code at the local checkout instead of the marketplace entry — this
lets you test changes before cutting a release:

```bash
# from inside the plugin-harness repo
claude --plugin-dir .
```

> **Security:** The `--plugin-dir` path is **auto-loaded by Claude Code at
> session start** — including all `.claude-plugin/` directives (hooks,
> MCP/LSP servers, monitors, `bin/`, agents, settings). Only run from a
> verified checkout you trust. Inspect the `.claude-plugin/` tree
> (especially `hooks/hooks.json` and `.mcp.json`) before running.

The `--plugin-dir` flag (per
[code.claude.com/docs/en/plugins](https://code.claude.com/docs/en/plugins))
points Claude Code at a local plugin directory. It takes the directory
**above** `.claude-plugin/` (i.e. the plugin root), not `.claude-plugin/`
itself nor the manifest file. Use `/reload-plugins` after each code
change.

When your changes are ready, the workflow is:
1. Run `bash scripts/ci-local.sh` (verifies tests + JSON manifests).
2. Commit + push to main.
3. The CI version-bump workflow
   ([`.github/workflows/version-bump.yml`](.github/workflows/version-bump.yml))
   patches the version + commit-pins the marketplace ref on every merge to
   main. Users pick up the new version via `claude plugin update`.
4. Users run `claude plugin update plugin-harness` to pull the new
   version.

### Fallback — `pip install` for the library path only

```bash
python -m pip install -e .
```

Requires Python ≥ 3.10. Runtime deps (pinned in `pyproject.toml`):
`jinja2 >= 3.1, < 4` and `jsonschema >= 4.18, < 5`.

`pip install` does **not** install Claude or Codex skills by itself; it
only gives you the library API + CLI. To get the bundled skills into a
runtime skill directory, use the marketplace install above, or call
`register_cc_skill` / `register_codex_skill` programmatically (see
"Library API" below). The library install path is for users who want
to integrate plugin-harness into their own Python tools, not for
everyday skill authoring.

### Fallback — manual install (no marketplace, no pip)

For users who can't or don't want to use `claude plugin marketplace add`
yet (offline, CI restrictions, etc.), drop the three SKILL.md files
into `~/.claude/skills/<name>/` by hand:

```bash
# from the plugin-harness repo root
mkdir -p ~/.claude/skills/plugin-harness
mkdir -p ~/.claude/skills/skill-creator
mkdir -p ~/.claude/skills/plugin-creator
# cp -i prompts before overwriting; use 'n' to keep any pre-existing
# custom skill by the same name. Plain 'cp' silently clobbers.
cp -i skills/plugin-harness/SKILL.md  ~/.claude/skills/plugin-harness/
cp -i skills/skill-creator/SKILL.md   ~/.claude/skills/skill-creator/
cp -i skills/plugin-creator/SKILL.md  ~/.claude/skills/plugin-creator/
```

Then `/reload-plugins` in Claude Code. The skills appear as
`/plugin-harness`, `/skill-creator`, `/plugin-creator` (unprefixed in
this mode). Note: this is the install path BEFORE the marketplace was
shipped; the marketplace install supersedes it.

**`/plugin-harness:new` is NOT available in the manual install path.**
That slash command requires the plugin's `commands/new.md` asset, which
ships only in the plugin root directory (consumed by the marketplace
install via `claude --plugin-dir` or `/plugin install`). The manual
`cp` path gives you the three SKILL.md assets only; if you need the
`/new` slash command, use the marketplace or dev-mode install.

### Codex-side install

Codex reads the same SKILL.md files (the `.codex.md` companions) from
a parallel location. Per
[learn.chatgpt.com/docs/build-skills](https://learn.chatgpt.com/docs/build-skills),
Codex's user-level canonical path is `$HOME/.agents/skills/<name>/` (NOT
`~/.codex/skills/`, which was an earlier convention):

```bash
# user-level install (Codex canonical)
# Codex reads SKILL.md (not SKILL.codex.md) at this path. The .codex.md
# filename is a sibling artifact in the repo; the runtime file is
# named SKILL.md per the §Where skills live table and the
# register_codex_skill adapter's CODEX_SKILL_REL_PATH.
mkdir -p "$HOME/.agents/skills/plugin-harness"
mkdir -p "$HOME/.agents/skills/skill-creator"
mkdir -p "$HOME/.agents/skills/plugin-creator"
# cp -i prompts before overwriting; plain cp silently clobbers.
# Symlink source check: refuse to copy from a path where the parent is
# a symlink (cp dereferences symlinks, which can silently inject
# attacker content on a typosquatted fork).
for s in plugin-harness skill-creator plugin-creator; do
  src="skills/$s/SKILL.codex.md"
  [ -L "$src" ] && { echo "refusing to copy from symlink: $src" >&2; continue; }
  cp -i "$src" "$HOME/.agents/skills/$s/SKILL.md"
done

# repo-level install (project-scoped, what `/skill-creator` in Codex reads)
for s in plugin-harness skill-creator plugin-creator; do
  mkdir -p ".agents/skills/$s"
  src="skills/$s/SKILL.codex.md"
  [ -L "$src" ] && { echo "refusing to copy from symlink: $src" >&2; continue; }
  cp -i "$src" ".agents/skills/$s/SKILL.md"
done
```

Then restart Codex. The skills become invocable as `$plugin-harness`,
`$skill-creator`, `$plugin-creator`.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/help` doesn't list the skills after install | Reload not run | `claude plugin reload` |
| `claude plugin install` errors with "manifest not found" | Marketplace catalog entry pointing at a stale SHA or the repo's `.claude-plugin/plugin.json` is missing/malformed | `gh api repos/sh-ai-x/plugin-harness/contents/.claude-plugin/plugin.json` to confirm the file is reachable; rerun `claude plugin marketplace add` if you changed the URL |
| `claude --plugin-dir <path>` errors with "manifest not found" | Wrong target — `--plugin-dir` takes the **parent directory** containing `.claude-plugin/plugin.json`, not the file itself | Pass the directory above the `.claude-plugin/` dir, e.g. `claude --plugin-dir .` (if you ran the command from the plugin root) |
| Skill assets installed but `dev-kit` substring in description triggers nothing | The `dev-kit` substring validator (`src/skill_schema/validator.py`) fires at **emit time** (when this project's `src/emitter/{skill,plugin_skill_bundle}.py` produces a SKILL.md), NOT at marketplace install. A skill that already contains `dev-kit` will be installed as-is; this project's own emitter refuses to generate one. | Edit the offending description and re-emit (or edit the file directly if you have a fork with the same issue) |
| Marketplace not found at `claude plugin marketplace add` | GitHub URL unreachable, or the marketplace.json in the repo root is malformed | Visit the URL in a browser; confirm `.claude-plugin/marketplace.json` exists; rerun the `add` command |
| `claude plugin update` says "no update available" | Marketplace ref not bumped yet (the version-bump workflow ran but didn't update) | Open a PR; the workflow runs on merge-to-main |

---

## Library API (the primary surface)

Producing skill/plugin content directly, no CLI:

```python
from pathlib import Path
from src.engine.modes.skill_create import SkillInterviewState, run_skill_interview
from src.emitter.skill import emit_skill
from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
from src.adapter.cc import register_cc_skill
from src.adapter.codex import register_codex_skill

# 1. Author a SKILL.md pair via the 3-question interview.
state = SkillInterviewState()
state.set_answer("purpose",          "A description of what the skill does")
state.advance()
state.set_answer("examples",         "One or two concrete usage examples")
state.advance()
state.set_answer("success-criteria", "Acceptance criteria for the done state")
state.advance()

# 2. Emit to a temp directory — atomic; no files written on validation failure.
result = emit_skill(state, Path("/tmp/my-skill"))
print(result.cc_path, result.codex_path)

# 3. OR: emit a plugin + dual-runtime skill bundle via the 5-question flow.
from src.schema.state import InterviewState
plugin_state = InterviewState()
# ... fill 5 answers ...

emit_plugin_skill_bundle(
    plugin_state, "# Plan\nbody", Path("/tmp/my-plugin"),
    skill_slugs=["intake-form", "followup-email"],
)

# 4. Install a bundled skill into the Claude + Codex runtime directories.
register_cc_skill("skill-creator",  Path("."))   # -> .claude/skills/skill-creator/SKILL.md
register_codex_skill("skill-creator", Path(".")) # -> .codex/skills/skill-creator/SKILL.md
```

Validating an existing SKILL.md against the vendored schema:

```python
from src.skill_schema.validator import validate_skill_md
r = validate_skill_md(Path(".claude/skills/my-skill/SKILL.md"), runtime="cc")
print(r.ok, r.runtime, r.errors)
```

Re-emitting a SKILL.md from existing content (manual / no interview):

```python
from src.skill_schema.loader import load_spec
spec = load_spec("codex")   # or "cc"
print(spec["required"])     # ['name', 'description']
```

---

## CLI UX (the interview flows)

The CLI is one UX path for producing skill/plugin content. Each mode
runs the existing engine (`src/engine/runner.run_interview`) with a
specific question schema and emission contract.

### Plugin authoring (Codex layout, 5 questions)

```bash
python -m src.engine.cli new "<one-line idea>" --mode user
# or
python -m src.engine.cli new "<one-line idea>" --mode ai-research
```

Exit codes:

| Code | Meaning |
|---:|---|
| 0 | interview complete; `complete` on stdout |
| 2 | invalid CLI args |
| 3 | user aborted (Ctrl-C / EOF on stdin) |
| 4 | validation failure on a submitted answer |

Output (in `<output_dir>/`):

```
src/.codex-plugin/plugin.json          ← Codex plugin manifest
src/.mcp.json                          ← Codex MCP servers (empty in MVP)
src/skills/<slug>/SKILL.md            ← canonical Codex-skill layout
README.md                            ← assembled idea plan
```

### Skill authoring (Claude + Codex skill, 3 questions)

The `--mode=skill_create` flow runs the **3-question skill interview**
(`purpose` / `examples` / `success-criteria`) and emits two SKILL.md
files — one in the Claude layout, one in the Codex layout — so the same
content loads as a Claude Skill via `/<slug>` AND as a Codex Skill via
`$<slug>`. See the docs links at the top of this README for how each
runtime consumes these files.

```bash
python -m src.engine.cli new "<one-line idea>" \
    --mode=skill_create --output-dir <dir>
```

Output:

```
<dir>/.claude/skills/<slug>/SKILL.md      ← Claude Skill format
<dir>/.codex/skills/<slug>/SKILL.md      ← Codex Skill format (same shape)
```

Both files share the **body** byte-for-byte (the parity carry-forward);
only the frontmatter shape is runtime-specific (Codex gets an optional
`metadata:` block carrying `openai` / `slug` / `dual_runtime` keys).
Atomically validated before any write commits; a failed validation raises
`EmitError` and **no file lands on disk**. Idempotent on re-run.

### Plugin + bundled skill (5Q + dual-runtime skill bundle)

Adding `--skill-slug <slug>` (repeatable) to a normal `plugin-harness new`
invocation extends the existing 5-question flow: the canonical Codex
plugin files are emitted (unchanged behavior) and **per `--skill-slug`**,
one Claude Skill file + one Codex Skill file land alongside. The
dual-runtime skill bundle reuses `src/emitter/codex.emit` (the
0-mvp canonical emitter) and ADDS the skill files via
`src/emitter/plugin_skill_bundle.emit_plugin_skill_bundle`.

```bash
python -m src.engine.cli new "<one-line idea>" \
    --mode=user --output-dir <dir> \
    --skill-slug intake-form --skill-slug followup-email
```

### Adapter install from the CLI

The interview + emit runs in process; **adapters do not run automatically.**
To drop the bundled `skill-creator` and `plugin-creator` skills into a
project's runtime skill directories:

```bash
python -c "
from pathlib import Path
from src.adapter.cc import register_cc_skill
from src.adapter.codex import register_codex_skill
for n in ('skill-creator', 'plugin-creator'):
    register_cc_skill(n, Path('.'))
    register_codex_skill(n, Path('.'))
"
```

Then in Claude Code: `/skill-creator` and `/plugin-harness:plugin-creator`
become invocable.

---

## Architecture (what this project produces vs consumes)

```
inputs                     produced artifacts              where they land
─────────────────         ─────────────────────            ──────────────────
5-question plugin state → src/.codex-plugin/plugin.json → <project>/src/...
                        → src/.mcp.json
                        → src/skills/<slug>/SKILL.md
                        → README.md

3-question skill state  → <dir>/.claude/skills/<slug>/    Claude Code
                            SKILL.md                     (per code.claude.com)
                        → <dir>/.codex/skills/<slug>/     Codex
                            SKILL.md                     (per learn.chatgpt.com)

raw file on disk         → validate_skill_md(path, runtime)
                            via vendored schema
                            (CC schema in docs/cc-skill.schema.json,
                             Codex schema in docs/codex-skill.schema.json)

register_cc_skill(name)  → <project>/.claude/skills/      project-level Claude
                            <name>/SKILL.md                skill directory

register_codex_skill(name)→ <project>/.codex/skills/       project-level Codex
                            <name>/SKILL.md                skill directory
```

The runtime skill directories (`.claude/skills/`, `.codex/skills/`,
`.agents/skills/`) are read by **Claude Code and Codex themselves**; this
project never reads them. The adapter writes to them. The reader is the
runtime.

```
src/
├── schema/         canonical 5-question schema + InterviewState codec
├── skill_schema/   vendored skill frontmatter schemas + validator + 3-question prompt
├── engine/         interview runner + CLI; per-mode dispatch (user/ai-research/skill_create)
├── assembler/      idea-plan assembly (jinja2)
├── emitter/        Codex-layout plugin emit + dual-runtime skill emit + dual-skill bundle
│   ├── codex.py                  0-mvp canonical Codex layout
│   ├── skill.py                  SKILL.md pair (Claude + Codex)
│   └── plugin_skill_bundle.py    plugin.json + per-arg skill bundle
└── adapter/        runtime-surface writers
    ├── cc.py       register_cc + register_cc_skill  (installs into .claude/...)
    ├── codex.py    register_codex + register_codex_skill  (installs into .codex/...)
    └── install.py  shared install primitives (atomic write, symlink refusal)
```

---

## Tests

```bash
bash scripts/test.sh       # pytest tests/  (installs deps if missing)
bash scripts/e2e.sh        # full dual-runtime pipeline e2e
bash scripts/ci-local.sh   # local CI: validate + test (mirrors .github/workflows/ci.yml)
bash scripts/smoke.sh      # lightweight smoke
```

| Path | Scope |
|---|---|
| `tests/test_question_schema.py` | 5 questions present, immutable |
| `tests/test_interview_state.py` | state codec, validation, cursor |
| `tests/test_runner.py` | engine loop + per-mode dispatch |
| `tests/test_cli.py` | argparse, exit codes, mode registry |
| `tests/test_assembler.py` | idea-plan jinja templates |
| `tests/test_emitter.py` | Codex-layout emission + JSON Schema |
| `tests/test_cc_adapter.py` | Claude Code adapter install surface (0-mvp register_cc) |
| `tests/test_codex_adapter.py` | Codex adapter install surface (0-mvp register_codex) |
| `tests/test_skill_schema.py` | vendored skill frontmatter schemas + validator |
| `tests/test_skill_prompts.py` | 3-question skill_create schema |
| `tests/test_skill_sub_mode.py` | SkillInterviewState + emit_skill |
| `tests/test_plugin_sub_mode.py` | emit_plugin_skill_bundle |
| `tests/test_skill_adapter.py` | register_cc_skill + register_codex_skill |
| `tests/e2e/test_dual_runtime_parity.py` | CC body byte-equal Codex body (kill condition) |
| `tests/e2e/test_skill_creator_e2e.py` | end-to-end smoke |
| `tests/e2e/test_full_pipeline.py` | full 5Q pipeline end-to-end |
| `tests/e2e/test_smoke.py` | cross-runtime parity smoke |
| `tests/test_worktree_guard.py` | dev-kit worktree-guard regressions |

---

## CI

`.github/workflows/ci.yml` runs three jobs:

- **branch-policy** — fail-closed on direct push to `main` whose commit
  has no associated PR. Mirrored client-side by `.githooks/pre-push`.
- **test** — `bash scripts/test.sh` on `pull_request` and `workflow_dispatch`.
- **validate** — `python3 scripts/validate.py` on the same triggers.

`.github/workflows/review.yml` runs the 3-dim and 10-dim LLM reviews in
parallel; a combined severity gate decides merge. PRs that edit
`.github/workflows/` skip the LLM step (per the action's documented
self-protection guard) and the severity gate defaults to Approve via the
empty-verdict fallback.

## Contributing

Per `.claude/rules/git-workflow.md`, every change goes on a fresh worktree +
branch (`<type>/<slug>`, e.g. `fix/cc-skill-no-devkit`). The dev-kit plugin
ships three enforcement hooks in `hooks/`:

- `worktree-guard.sh` (PreToolUse Edit/Write) — hard-blocks edits in the main checkout.
- `task-detector.sh` (UserPromptSubmit) — early-warning nudge on new-task intent in main.
- `session-start-check.sh` (SessionStart) — gentle nudge at session-start in main.

PR title: `<type>(<scope>): <subject>` (Conventional Commits). Body must
include a quoted test plan with exit codes / test counts. Identity:
`sh-ai-x <tkd1496@gmail.com>` (SSOT per local memory; always pass
`-c user.email=...` on commit because CI runners reset identity).

## Status

Early-stage (v0.1.0 per `pyproject.toml`). No license file is included in
this repository yet — assume all rights reserved unless one is added.
