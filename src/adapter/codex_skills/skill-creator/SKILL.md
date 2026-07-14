---
name: skill-creator
description: Author a new skill by running the 3-question skill_create interview and emitting dual-runtime SKILL.md files (CC + Codex). Use when you want a brand-new skill without writing frontmatter by hand.
---

# skill-creator

Drives the plugin-harness interview in `--mode=skill_create` and emits
two SKILL.md files (Claude Code + Codex layouts) that load identically
in both runtimes. The interview asks for the skill's purpose,
examples, and success criteria; the emit step writes both layouts and
validates each against the vendored schema in `docs/{cc,codex}-skill.schema.json`.

## When to use this skill

- create a new skill from a one-line idea
- ship a skill whose CC and Codex artifacts are equivalent

## Invocation

```bash
python -m src.engine.cli new "<one-line idea>" --mode=skill_create --output-dir <dir>
```

Exit 0 on a complete 3-answer interview; the two SKILL.md files appear
under `<dir>/.claude/skills/<slug>/SKILL.md` and
`<dir>/.codex/skills/<slug>/SKILL.md`. Validation failures exit
non-zero with the offending file path.

## Notes

- The skill validates against the vendored schemas; description
  field is filtered for forbidden internal-tool substrings before
  install is allowed.
- Reuses the existing plugin-harness engine — no separate entry point.
- Re-running `register_codex_skill('skill-creator')` is idempotent.
