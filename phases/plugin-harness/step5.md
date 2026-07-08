# Step 5 — implement Codex plugin generation

## Goal
Given `interview.json`, emit a valid Codex plugin source tree at `src/`. Must include `.codex-plugin/plugin.json` and `skills/<name>/SKILL.md`.

## Inputs
- `interview.json` from step 2 or 3 (sole source for codex metadata)
- Codex plugin spec: https://developers.openai.com/codex/plugins
- Codex skills spec: https://developers.openai.com/codex/skills
- Skill name (from `--name` flag)

**Note on leaky contracts**: step 5 reads ONLY `interview.json`, not step 4's on-disk emitter output. Cross-runtime metadata (plugin name, version, skill name) is derived from `interview.json` alone, not by parsing step 4's emitted files. This keeps the data contract explicit and avoids the implicit "step 5 must wait for step 4 and parse its output shape" coupling. Step 6's consistency check then compares step 4 vs step 5 outputs at the file level, not by implicit shared state.

## Outputs
- `src/.codex-plugin/plugin.json` (with name, version, entry points, primary_entry_point)
- `src/skills/<name>/SKILL.md` (Codex format)
- `src/README.md` (merged usage doc — sole writer; the writer-exclusion mutex below is the only real constraint against step 4)
- Unit tests: `plugin.json` schema (including `primary_entry_point` field), SKILL.md format

> **Removed** (per LLM review): `README.md` at repo root. Emitting it would clobber plugin-harness's own `README.md` on first run. If a local-repo copy is desired, the build stage will provide a separate opt-in post-build step (not in this plan).

**Note on ordering**: the only real constraint between step 4 and step 5 is the **writer-exclusion mutex** on `src/README.md` — step 4 must NOT emit it, step 5 is the sole writer. Step 5 does NOT depend on step 4's on-disk output (it reads only `interview.json`, see Inputs above). The two emitters can run in any order as long as the mutex holds.

## Acceptance criteria
- Generated `.codex-plugin/plugin.json` is valid per Codex spec
- Generated `skills/<name>/SKILL.md` is valid per Codex skills spec
- Plugin installs cleanly in Codex (smoke test: install + invoke `/<skill-name>`)
- Plugin metadata matches what was generated for Claude Code (consistency check upstream — links to step 6). Even in the no-MCP case (Codex-only transport), `plugin.json`'s `primary_entry_point` must equal the `primary_entry_point` field in `interview.json` (step 6 verifies this even when `.mcp.json` is absent)
- Step 5 emits BOTH `src/README.md` and a root-level `README.md` (identical content; root copy is for local repo discoverability — there is no zip step in this pipeline)

## TDD order
1. RED: test that emitted `plugin.json` matches Codex schema
2. RED: test that SKILL.md is valid per Codex format
3. RED: test that plugin name and version match across runtimes
4. GREEN: implement emitter
5. REFACTOR: extract a shared `Metadata` dataclass (fields: `name`, `version`, `primary_entry_point`, `description`) populated from `interview.json`. Both step 4 and step 5 format the same `Metadata` into their respective runtime shapes (Codex `plugin.json` shape vs Claude Code `.mcp.json` shape). The shared module is the single source of truth; only the FORMAT MAPPING differs.

## Risks
- Codex spec may change — pin version
- Field-name diffs vs Claude Code — must be detected (links to step 6 consistency check)
