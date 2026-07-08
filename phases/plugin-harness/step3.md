# Step 3 — implement AI web-research fill (mode B — AI-research)

## Goal
Given an idea or company (from CLI), AI searches the web for evidence and fills the 5 questions. Output same `interview.json` shape as mode A.

## Inputs
- `questions.json` from step 1
- `interview.json` schema (from step 2)
- Web search API (MCP or direct)
- LLM with internet access

## Outputs
- `/dev-kit:plan-plugin --mode B <idea-or-company>` command
- `interview.json` with AI-filled answers + evidence URLs
- Unit tests: each question has evidence, no hallucination, format match

## Acceptance criteria
- Mode B takes a single input (idea or company name) and produces a full `interview.json`
- Each answer cites at least 1 web source (URL + retrieval timestamp)
- If web search fails for a question, fall back to LLM-only with explicit "no evidence" marker
- Output is interchangeable with mode A output (downstream steps don't care which mode produced it)

## TDD order
1. RED: test that mode B produces `interview.json` with 5 answers
2. RED: test that each answer has at least 1 evidence URL
3. RED: test that output matches mode A schema
4. GREEN: implement web search wrapper
5. GREEN: implement LLM fill loop per question
6. REFACTOR: extract evidence-collector

## Risks
- Hallucination: LLM may fabricate URLs — verify URLs resolve before accepting
- Rate limits: web search APIs have limits — batch + cache
- Privacy: company names may be sensitive — log redaction
