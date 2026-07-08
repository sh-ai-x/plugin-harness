# Step 8 — end-to-end smoke test (kill-shot)

## Goal
Validate the full pipeline end-to-end on 1 real idea, within the ≤2 person-day bound from Q3.

## Inputs
- 1 real idea (e.g., "GitHub PR triage" or "Notion daily digest")
- All previous steps implemented

## Outputs
- `submission.zip` for the smoke-test idea
- Test report: pass/fail per step + install verification in both runtimes
- Time/effort log (must be ≤2 person-days)

## Acceptance criteria
- Full pipeline runs in ≤2 person-days (1 day, 1 person)
- Generated plugin installs cleanly in Claude Code AND Codex
- `submission.zip` passes the consistency check (step 7)
- 5-question answers are coherent + non-hallucinated (manual review by user)
- No silent runtime breaks (verify by invoking the plugin in both runtimes)

## TDD order (scenario-style)
1. Pick 1 real idea (e.g., "GitHub PR triage")
2. Run mode A: `/dev-kit:plan-plugin "GitHub PR triage" --mode A`
3. Verify all 5 answers are filled
4. Run mode B on the same idea
5. Compare mode A vs mode B outputs
6. Generate plugin (steps 4 + 5)
7. Install in Claude Code, invoke once, verify behavior
8. Install in Codex, invoke once, verify behavior
9. Build `submission.zip`
10. Run consistency check (step 7)
11. Compare runtime behavior (this is the "kill shot" for the next-build Q5 idea)

## Risks
- Real idea may have edge cases — keep it simple for first run
- Install issues in one runtime may block — have rollback plan
- Time bound is tight — track time per step
