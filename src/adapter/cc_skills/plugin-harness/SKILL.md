---
name: plugin-harness
description: Plan and emit a new plugin from a one-line idea using the 5-question interview and the dual-runtime emitter.
---

# plugin-harness

Drive the plugin-harness engine in skill mode. When the user describes an idea
for a new plugin and wants guided ideation, run the engine:

```bash
python -m src.engine.cli new "<one-line idea>" --mode user
```

## When to use

- The user describes an idea for a new Claude Code or Codex plugin.
- The user wants the 5-question interview (what/who/where · why-this-problem ·
  how-it-works · ai-usage · how-verified) instead of free-form ideation.

## What it does

1. Runs the 5-question interview to capture the user's intent.
2. Assembles the idea plan as a Markdown document.
3. Emits the plugin files in the Codex layout: `src/.codex-plugin/plugin.json`,
   `src/skills/<slug>/SKILL.md`, `src/.mcp.json`, and `README.md`.

## Engine entrypoint

```bash
python -m src.engine.cli new "<idea>" [--mode user|ai-research]
```

The skill and the `/plugin-harness` slash command share this same entrypoint.