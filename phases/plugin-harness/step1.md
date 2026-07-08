# Step 1 — spec the 5 questions (Codex format)

## Goal
Define the 5 questions as a stable contract. Output `questions.json` (or equivalent) that modes A and B share. Each question has a stable id, prompt text, and an `evidence_mode` flag (can-AI-fill).

## Inputs
- Codex plugin submission spec: https://developers.openai.com/codex/plugins
- Codex skills spec: https://developers.openai.com/codex/skills
- Codex plugin build: https://developers.openai.com/codex/plugins/build
- Q1 grill-me answer: failure mode = no plugin tool exists, every author re-rolls the same boilerplate

## Outputs
- `questions.json` schema with 5 questions, plus a top-level `interview_metadata` block (owned by step 1):
  - `primary_entry_point` (string, e.g., `/<skill-name>`) — the single field both step 4 and step 5 write to their respective runtime configs; step 6 compares byte-equal
  - `skill_name` (string, kebab-case)
  - `idea_or_company` (string)
- `/plugin-harness:plan --mode <A|B> --name <skill-name> <idea-or-company>` CLI command (owned by step 1; delegates to step 2 or step 3 based on `--mode`)
- Unit tests for schema validation
- README snippet documenting the 5 questions + interview_metadata

## Acceptance criteria
- 5 questions defined, matching the Codex submission format
- Each question has: `id`, `prompt`, `response_shape`, `evidence_mode`
- Schema is versioned and stable across modes A and B
- `interview_metadata` block is the SOLE owner of `primary_entry_point`, `skill_name`, `idea_or_company` — step 4 and step 5 read these fields; they do NOT introduce their own copy
- Unit tests cover all 5 questions + edge cases (empty response, multi-line response)

## TDD order (red → green → refactor)
1. RED: failing test `test_questions_schema.py::test_5_questions_match_codex_format`
2. RED: failing test `test_questions_schema.py::test_each_question_has_id_prompt_evidence_mode`
3. GREEN: implement `questions.json` with 5 questions sourced from Codex format
4. REFACTOR: extract schema validator

## Risks
- Codex submission format may change — pin version, document
- Question text may need translation — start with English, leave room for i18n
