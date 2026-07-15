---
description: Run the plugin-harness interview to author a new plugin or skill. Use when starting a fresh idea that should become a Claude Code plugin, Codex plugin, or standalone SKILL.md pair.
allowed-tools: Bash
---

# /plugin-harness:new

Run the plugin-harness interview engine. Pick the mode based on the
flags you pass.

## When to use

- starting a fresh idea and want a structured interview before writing
- authoring a Claude Code plugin, Codex plugin, or standalone SKILL.md
  pair from one input

## Invocation

```bash
python -m src.engine.cli new "<one-line idea>" [flags]
```

Flags:

- `--mode user` (default): prompts 5 questions interactively for a
  Codex-layout plugin (`src/.codex-plugin/plugin.json` + `.mcp.json`
  + `src/skills/<slug>/SKILL.md` + `README.md`).
- `--mode ai-research`: drafts 5 answers via the runtime tool surface.
- `--mode skill_create`: prompts 3 questions for a standalone SKILL.md
  pair (Claude + Codex layouts).
- `--output-dir <dir>`: required for `--mode skill_create`; where to
  emit files.
- `--skill-slug <slug>` (repeatable): bundles a dual-runtime skill
  alongside the plugin (uses `src/emitter/plugin_skill_bundle.py`).

## Exit codes

- `0` — interview complete; `complete` on stdout
- `2` — invalid CLI args
- `3` — user aborted
- `4` — validation failure on a submitted answer

After exit 0, the emit step writes files (Codex layout + per-arg skill
bundle if `--skill-slug` given).

## Notes

- The CLI is one UX path; the library is the primary surface. See README
  §Library API for programmatic emission via
  `src/emitter/{codex,skill,plugin_skill_bundle}.py` and
  `src/adapter/{cc,codex}.py`.
- Reuses the existing plugin-harness engine — no separate entry point.
- Skill assets bundled here validate against vendored schemas
  (`docs/{cc,codex}-skill.schema.json`); the `dev-kit` substring
  prohibition is enforced by `src/skill_schema/validator.py`.
