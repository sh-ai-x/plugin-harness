---
name: plugin-creator
description: Author a new dual-runtime plugin (plugin.json + skill bundle) by reusing the existing plugin-harness 5-question interview and adding a CC + Codex skill bundle. Use when a single plugin needs to ship one or more named skills under it.
---

# plugin-creator

This skill drives the plugin-harness 5-question interview (no schema
duplication), emits a Codex-layout `plugin.json` via the existing
`src.emitter.codex.emit`, AND additionally emits a dual-runtime skill
bundle under `.claude/skills/<slug>/` and `.codex/skills/<slug>/`.

## When to use this skill

Use this skill when the user asks to:

- author a plugin that bundles one or more named skills under one
  `plugin.json`
- ship a single artifact that installs identically in both Claude
  Code and Codex

Do not use this skill for skills without a plugin wrapper (use the
`skill-creator` skill for that) or for maintenance of an existing
plugin.

## Invocation

The plugin-creator uses the existing 5-question flow plus a
`--skill-slug` flag. Each `--skill-slug` adds one bundled skill under
both runtimes.

```bash
python -m src.engine.cli new "<one-line idea>" --mode=user \
  --output-dir <dir> --skill-slug <slug1> --skill-slug <slug2> ...
```

The CLI exits 0 on a complete 5-answer interview; the bundle is
written under `<dir>/.claude/skills/<slug>/SKILL.md` and
`<dir>/.codex/skills/<slug>/SKILL.md`, validated against the vendored
schemas from step 0.

## Notes

- The 5-question schema is reused — `src/schema/questions.py` is
  NOT modified.
- `src/emitter/codex.py` is reused for the canonical Codex-layout
  emission; this skill only ADDS the dual-runtime skill bundle.
- Re-running the CLI with the same `--output-dir` is idempotent.
- Reuses the existing plugin-harness engine — no separate entry point.
