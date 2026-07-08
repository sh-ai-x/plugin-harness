# Step 1 — spec the 5 questions (Codex format)

## Goal
Define the 5 questions as a stable contract. Output `questions.json` (or equivalent) that modes A and B share. Each question has a stable id, prompt text, and an `evidence_mode` flag (can-AI-fill).

## Inputs
- Codex plugin submission spec: https://developers.openai.com/codex/plugins
- Codex skills spec: https://developers.openai.com/codex/skills
- Codex plugin build: https://developers.openai.com/codex/plugins/build
- Q1 grill-me answer: failure mode = no plugin tool exists, every author re-rolls the same boilerplate

## Outputs
- `questions.json` schema with 5 questions
- Unit tests for schema validation
- README snippet documenting the 5 questions

## Acceptance criteria
- 5 questions defined, matching the Codex submission format
- Each question has: `id`, `prompt`, `response_shape`, `evidence_mode`
- Schema is versioned and stable across modes A and B
- Unit tests cover all 5 questions + edge cases (empty response, multi-line response)

## TDD order (red → green → refactor)
1. RED: failing test `test_questions_schema.py::test_5_questions_match_codex_format`
2. RED: failing test `test_questions_schema.py::test_each_question_has_id_prompt_evidence_mode`
3. GREEN: implement `questions.json` with 5 questions sourced from Codex format
4. REFACTOR: extract schema validator

## Risks
- Codex submission format may change — pin version, document
- Question text may need translation — start with English, leave room for i18n
