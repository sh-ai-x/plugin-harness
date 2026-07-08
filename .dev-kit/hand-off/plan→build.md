# Hand-off — plan → build

**Date**: 2026-07-08
**From**: `/dev-kit:plan`
**To**: `/dev-kit:build`
**Worktree**: `feat/plugin-harness`
**Branch base**: `origin/main`

## Artifacts emitted

- `PRD.md` — 6 sections + acceptance criteria
- `.prd/decision-log.md` — cumulative decisions across all 8 gates
- `phases/plugin-harness/index.json` — 8 steps
- `phases/plugin-harness/step{1..8}.md` — per-step specs

## Stage transition
- `plan` → `build`
- methodology: `tdd`
- kill-shot (Q3): ≤2 person-days, 1 real idea, full pipeline

## Next action
Run `/dev-kit:build` to convert `phases/plugin-harness/step<N>.md` into per-step implementation.

## Constraints
- Standalone plugin, no dev-kit runtime dep
- Two modes: user-driven (A) and AI-research-driven (B)
- 5 questions from Codex submission format
- Dual runtime: Claude Code + Codex
- `submission.zip` matches Codex spec
- Consistency check before zip (log↔plugin↔questionnaire)

## Open risks (from Q4)
- Dual plugin.json layout hand-ported, error-prone — addressed by sharing template in steps 4+5
- Silent runtime breaks from field-name diffs — caught by step 7 consistency check
