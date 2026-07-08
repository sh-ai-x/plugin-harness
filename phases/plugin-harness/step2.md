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
- **Log redaction policy** (LAYERED scrubber — single-pattern regex is bypassable per the LLM review; applied to BOTH user prompts and assistant responses before write):
  1. **Known secret patterns (with separator)**: `(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+`
  2. **AWS access keys**: `\bAKIA[0-9A-Z]{16}\b`
  3. **GitHub PATs**: `\bghp_[A-Za-z0-9]{30,}\b`
  4. **JWT tokens**: `\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b`
  5. **PEM blocks**: `-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----`
  6. **Bearer tokens**: `(?i)bearer\s+[A-Za-z0-9._\-+/=]{20,}`
  7. **No-separator API keys** (e.g., `sk-proj-abc`): `\bsk-(proj-)?[A-Za-z0-9]{20,}\b`
  8. **Length-based heuristic**: any standalone alphanumeric run of 40+ chars that looks base64-like is replaced with `<long-token-redacted>`
  9. **Emails** (RFC 5322): replace with `<email-redacted>`
  10. **IPv4 dotted-quad**: replace with `<ip-redacted>`
  11. **Replacements**: each matched pattern is replaced with the appropriate `<*-redacted>` marker
  12. **Redaction unit test**: known-bad log sample (containing AKIA..., ghp_..., eyJ..., sk-proj-abc, PEM block, bearer token) → ALL secrets redacted
  13. **Shared with step 3**: mode B's web-retrieval output goes through this same scrubber before logging

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
