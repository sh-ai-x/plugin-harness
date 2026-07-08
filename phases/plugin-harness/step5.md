# Step 5 — implement Codex plugin generation

## Goal
Given `interview.json`, emit a valid Codex plugin source tree at `src/`. Must include `.codex-plugin/plugin.json` and `skills/<name>/SKILL.md`.

## Inputs
- `interview.json` from step 2 or 3
- Codex plugin spec: https://developers.openai.com/codex/plugins
- Codex skills spec: https://developers.openai.com/codex/skills
- Skill name (from `--name` flag)

## Outputs
- `src/.codex-plugin/plugin.json` (with name, version, entry points)
- `src/skills/<name>/SKILL.md` (Codex format)
- `src/README.md` (merged usage doc — sole writer, emitted AFTER step 4 completes)
- Unit tests: `plugin.json` schema, SKILL.md format

**Note**: Step 5 runs AFTER step 4 (depends on step 4's CC files existing on disk). Step 5 is the SOLE emitter of `src/README.md`. Step 4 must NOT emit `src/README.md`. This eliminates the merge-order ambiguity flagged in review.

## Acceptance criteria
- Generated `.codex-plugin/plugin.json` is valid per Codex spec
- Generated `skills/<name>/SKILL.md` is valid per Codex skills spec
- Plugin installs cleanly in Codex (smoke test: install + invoke `/<skill-name>`)
- Plugin metadata matches what was generated for Claude Code (consistency check upstream — links to step 7)

## TDD order
1. RED: test that emitted `plugin.json` matches Codex schema
2. RED: test that SKILL.md is valid per Codex format
3. RED: test that plugin name and version match across runtimes
4. GREEN: implement emitter
5. REFACTOR: share template with step 4 (single source, two format mappings — counters Q4 lesson about hand-ported layouts)

## Risks
- Codex spec may change — pin version
- Field-name diffs vs Claude Code — must be detected (links to step 7 consistency check)
