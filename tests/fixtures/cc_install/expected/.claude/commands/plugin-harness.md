---
description: Plan a new plugin via the 5-question interview and emit the Codex-layout plugin files.
---

# plugin-harness

Run the plugin-harness engine with the user's one-line idea.

```bash
python -m src.engine.cli new "$ARGUMENTS"
```

The engine interviews the user via 5 fixed questions (what/who/where ·
why-this-problem · how-it-works · ai-usage · how-verified), assembles the
idea plan, and emits the plugin files in Codex layout (`src/.codex-plugin/plugin.json`,
`src/skills/<slug>/SKILL.md`, `src/.mcp.json`, `README.md`).

Use `--mode user` for interactive answers or `--mode ai-research` to let the
runtime tool surface draft answers from a one-line idea.