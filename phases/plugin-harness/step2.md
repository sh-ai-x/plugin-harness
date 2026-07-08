# Step 2 — implement 5-question interview form (mode A — user-driven)

## Goal
CLI that runs the 5-question interview; user fills answers directly. Persists answers to a stable location (e.g., `interview.json`) that mode B and downstream steps consume.

## Inputs
- `questions.json` from step 1
- `interview.json` schema (defined in this step)

## Outputs
- `/dev-kit:plan-plugin --mode A <idea-or-company>` command
- `interview.json` with user-filled answers
- `logs/<session-id>.md` (verbatim AI conversation — every user prompt + every assistant response)
- Unit tests: prompt order, required fields, persistence, resume, log capture

## Acceptance criteria
- CLI asks all 5 questions in order
- User can save mid-interview and resume
- All answers validate against the `questions.json` schema
- Output `interview.json` is JSON-serializable + human-readable
- Verbatim AI conversation captured to `logs/<session-id>.md` (md format, no edits/excerpts)
- **Log redaction policy** (applied to BOTH user prompts and assistant responses before write): strip lines matching `(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+`, replace email addresses (RFC 5322 pattern) with `<email-redacted>`, replace strings matching `sk-[A-Za-z0-9]{20,}` with `<token-redacted>`, replace IPv4 dotted-quad addresses with `<ip-redacted>`. Redaction unit test: known-bad log sample → all secrets redacted. Shared with step 3 (mode B's web-retrieval output goes through the same scrubber before logging).

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
