# Step 4 — implement Claude Code plugin generation

## Goal
Given `interview.json`, emit a valid Claude Code plugin source tree at `src/`. Must include `.claude/skills/<name>/SKILL.md`, optional `.mcp.json`.

## Inputs
- `interview.json` from step 2 or 3
- Claude Code skill spec (see https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- Skill name (from `--name` flag or default `plugin-harness`)

## Outputs
- `src/.claude/skills/<name>/SKILL.md` (with frontmatter + body)
- `src/.mcp.json` (if MCP needed for the plugin)
- `src/README.md` (plugin usage)
- Unit tests: frontmatter validity, body structure, file presence

## Acceptance criteria
- Generated `.claude/skills/<name>/SKILL.md` is valid per Claude Code spec
- Frontmatter includes `name`, `description`, optional `allowed-tools`
- Body includes 5-question answers as plugin description
- Plugin installs cleanly in Claude Code (smoke test: install + invoke `/<skill-name>`)

## TDD order
1. RED: test that emitted SKILL.md has valid frontmatter
2. RED: test that SKILL.md body includes 5-question answers
3. RED: test that `.mcp.json` is valid JSON
4. GREEN: implement emitter
5. REFACTOR: template engine

## Risks
- Claude Code spec may change — pin version
- MCP server config may need additional setup — document
