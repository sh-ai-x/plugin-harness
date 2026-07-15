---
name: plugin-creator
description: Author a dual-runtime plugin (plugin.json + skill bundle) using the existing 5-question plugin-harness interview. Use when a single plugin needs to ship one or more named skills under it.
---

# plugin-creator

Drives the plugin-harness 5-question interview (REUSES the existing
schema; does not duplicate questions) AND emits the dual-runtime skill
bundle. The canonical Codex layout (`plugin.json`, `.mcp.json`,
`src/skills/<plugin_slug>/SKILL.md`, `README.md`) comes from
`src/emitter/codex.py`; the new code is only the skill bundle.

## When to use this skill

- author a plugin with one or more bundled skills
- reuse the existing 5-question schema and emitter

## Invocation

```bash
python -m src.engine.cli new "<one-line idea>" --mode=user \
  --output-dir <dir> --skill-slug <slug1> --skill-slug <slug2> ...
```

Exit 0 on a complete 5-answer interview. The plugin.json, .mcp.json,
canonical Codex SKILL.md, and README.md are written by the existing
emitter; per `--skill-slug`, one CC + one Codex SKILL.md are bundled.

## Notes

- The 5-question schema (`src/schema/questions.py`) is reused unchanged.
- `src/emitter/codex.py` is reused for the canonical Codex emission.
- The bundle adds `.claude/skills/<slug>/SKILL.md` and
  `.codex/skills/<slug>/SKILL.md` and validates each against the
  vendored schemas from step 0.
