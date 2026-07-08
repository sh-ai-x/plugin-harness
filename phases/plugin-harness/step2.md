# Step 2 — implement 5-question interview form (mode A — user-driven)

## Goal
CLI that runs the 5-question interview; user fills answers directly. Persists answers to a stable location (e.g., `interview.json`) that mode B and downstream steps consume.

## Inputs
- `questions.json` from step 1
- `interview.json` schema (defined in this step)

## Outputs
- `/dev-kit:plan-plugin --mode A <idea-or-company>` command
- `interview.json` with user-filled answers
- Unit tests: prompt order, required fields, persistence, resume

## Acceptance criteria
- CLI asks all 5 questions in order
- User can save mid-interview and resume
- All answers validate against the `questions.json` schema
- Output `interview.json` is JSON-serializable + human-readable

## TDD order
1. RED: test that CLI asks all 5 questions in order
2. RED: test that CLI saves to `interview.json`
3. RED: test that CLI resumes from partial `interview.json`
4. GREEN: implement CLI with readline / prompt
5. GREEN: implement save/resume
6. REFACTOR: extract prompt logic

## Risks
- Long answers may break terminal — use proper input handling
- Special characters in user input — escape properly
