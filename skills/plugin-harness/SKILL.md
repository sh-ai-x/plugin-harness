---
name: plugin-harness
description: Plan and emit a new plugin from a one-line idea using the 5-question interview and the dual-runtime emitter.
---

# plugin-harness

This skill drives the plugin-harness interview and emits a dual-runtime
(Codex + Claude Code) plugin. It is the surface for the same engine that
the CC slash command exposes — one engine, two runtimes.

## When to use this skill

Use this skill when the user asks to:

- author or scaffold a Codex / Claude Code plugin from an idea
- run the 5-question interview (`what-who-where`, `why-this-problem`,
  `how-it-works`, `ai-usage`, `how-verified`)
- assemble or emit a plugin layout that installs identically in both
  CC and Codex

Do not use this skill for general code questions, plugin maintenance, or
any task that is not a fresh ideation-to-plugin flow.

## Invocation

Run the shared engine. The engine handles argparse, dispatch, and
serialization; the adapter only installs the surface.

```bash
python -m src.engine.cli new "<one-line idea>" --mode user
```

Modes:

- `--mode user` — prompts one question at a time, reads stdin (default).
- `--mode ai-research` — drafts answers from the runtime's tool surface.

The CLI exits 0 on a complete 5-answer interview and emits the plugin
layout under the configured output directory.

## Notes

- The skill is installed at `.agents/skills/plugin-harness/SKILL.md`,
  the canonical Codex path per https://developers.openai.com/codex/skills.
- Re-running the install is idempotent — it overwrites the same file.
- No external runtime dependencies beyond Python 3 and the engine CLI.
