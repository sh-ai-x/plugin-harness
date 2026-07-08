# Step 6 — implement submission.zip assembly

## Goal
Bundle the generated plugin source + README + logs into `submission.zip` matching the Codex submission spec.

## Inputs
- `src/` (Claude Code + Codex plugin source from steps 4 + 5)
- `README.md` (root-level)
- `logs/` (verbatim AI conversation from the entire run)

## Outputs
- `submission.zip` with the structure:
  ```
  submission.zip
  ├── src/
  │   ├── .codex-plugin/plugin.json
  │   ├── skills/<name>/SKILL.md
  │   ├── .claude/skills/<name>/SKILL.md
  │   ├── .mcp.json
  │   └── ...
  ├── README.md
  └── logs/
      └── <conversation>.md
  ```
- Unit tests: zip structure, file presence, no extra files at root

## Acceptance criteria
- Zip structure exactly matches Codex submission spec
- `src/.codex-plugin/plugin.json` is at `src/.codex-plugin/plugin.json` (not nested deeper)
- `logs/` contains verbatim AI conversation
- Zip is reproducible (same input → same bytes)

## TDD order
1. RED: test zip has `src/`, `README.md`, `logs/` at root
2. RED: test that `src/.codex-plugin/plugin.json` is at the right path
3. RED: test reproducibility (byte-equal on second build)
4. GREEN: implement zip builder
5. REFACTOR: normalize file ordering

## Risks
- Logs may contain sensitive data — scrub before zip
- Zip format edge cases (UTF-8 names, large files) — use Python's `zipfile` with proper flags
