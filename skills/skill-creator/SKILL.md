---
name: skill-creator
description: Author a new Claude Code skill by running the 3-question skill_create interview and emitting a dual-runtime SKILL.md pair (.claude + .codex). Use when you want a brand-new skill without writing the frontmatter or picking an interview by hand.
---

# skill-creator

This skill drives the plugin-harness interview in `--mode=skill_create`
and emits two SKILL.md files — one for Claude Code, one for Codex —
so the new skill loads identically in both runtimes.

## When to use this skill

Use this skill when the user asks to:

- create a new skill (a SKILL.md wrapper that documents an intent +
  examples + success criteria for the runtime to recognize)
- bootstrap a skill they can install in another project, without
  rewriting the frontmatter or the interview by hand

Do not use this skill for plugin authoring (use the `plugin-creator`
skill for that) or for any task that is not a fresh skill ideation flow.

## Invocation

Run the shared engine. The engine handles argparse, dispatch,
serialization, the dual-runtime emit, and validation against the
vendored schemas in `docs/{cc,codex}-skill.schema.json`.

```bash
python -m src.engine.cli new "<one-line idea>" --mode=skill_create --output-dir <dir>
```

The CLI exits 0 on a complete 3-answer interview, writes both SKILL.md
files under `<dir>/.claude/skills/<slug>/SKILL.md` and
`<dir>/.codex/skills/<slug>/SKILL.md`, and exits non-zero on
validation failure (e.g. forbidden tokens in the description).

## Notes

- The skill assets bundled here validate against the vendored schemas;
  re-running `register_cc_skill('skill-creator')` is idempotent.
- No external runtime dependencies beyond Python 3 and the engine CLI.
- Reuses the existing plugin-harness engine — no separate entry point.
