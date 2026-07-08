# Step 7 — implement submission.zip assembly

## Goal
Bundle the generated plugin source + README + scrubbed logs into `submission.zip` matching the Codex submission spec. Runs ONLY after step 6 (consistency check) passes.

## Inputs
- `src/` (Claude Code + Codex plugin source from steps 4 + 5)
- `README.md` (root-level — produced by step 5; copied to zip root)
- `logs/` (verbatim AI conversation from step 2 or 3 — SCRUBBED before inclusion)

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
- Unit tests: zip structure, file presence, no extra files at root, scrubber runs

## Acceptance criteria
- Zip structure exactly matches Codex submission spec
- `src/.codex-plugin/plugin.json` is at `src/.codex-plugin/plugin.json` (not nested deeper)
- `logs/` contains **SCRUBBED** AI conversation — scrubbing is a hard requirement (was previously in Risks; promoted to AC per review)
- **Log scrubbing rules** (applied before zip):
  - Strip lines matching `(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+`
  - Replace email addresses (RFC 5322 pattern) with `<email-redacted>`
  - Replace strings matching `sk-[A-Za-z0-9]{20,}` with `<token-redacted>`
  - Replace IPv4 dotted-quad addresses with `<ip-redacted>`
  - Scrubber unit test: known-bad log sample → all secrets redacted
- Zip contents are stable in size and order, but NOT byte-equal across runs (mode B retrieval timestamps make byte-stable reproducibility infeasible; document this explicitly)

## TDD order
1. RED: test zip has `src/`, `README.md`, `logs/` at root
2. RED: test that `src/.codex-plugin/plugin.json` is at the right path
3. RED: test log scrubbing — API key line redacted
4. RED: test log scrubbing — email redacted
5. RED: test log scrubbing — `sk-...` token redacted
6. RED: test log scrubbing — IP redacted
7. RED: test log scrubbing — known-bad log sample → all secrets redacted
8. GREEN: implement zip builder + scrubber
9. REFACTOR: normalize file ordering, extract scrubber

## Risks
- Scrubber may over-redact (false positives) — tune regex iteratively
- Scrubber may under-redact (miss novel secret formats) — extend pattern library over time
- Zip format edge cases (UTF-8 names, large files) — use Python's `zipfile` with proper flags