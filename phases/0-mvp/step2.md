# Step 2: Idea-plan assembler

## Status
**pending** — last update: 2026-07-08T23:50:00Z

## Read first
- `/PRD.md`
- `phases/0-mvp/step0.md` (schema)
- `phases/0-mvp/step1.md` (engine)
- `phases/0-mvp/step2.md` (this file)

## Task
Take a completed `InterviewState` and produce the final idea plan as a single Markdown document. The plan is the user-facing deliverable between the interview and the plugin emission.

Files to create:
- `src/assembler/__init__.py`
- `src/assembler/plan.py` — `assemble(state: InterviewState) -> str` returns the Markdown plan
- `src/assembler/templates/idea_plan.md.j2` — Jinja2 template (or pure-Python f-string; pick one and stick to it)
- `tests/test_assembler.py` — pytest: given a state with all 5 answers, returns a non-empty Markdown containing each question's answer; missing answer raises `AssemblerError`
- `tests/fixtures/completed_state.json` — fixture

Plan shape (locked):
```
# Idea Plan — <derived plugin name>

## 1. What, who, where
<answer to what-who-where>

## 2. Why this problem
<answer to why-this-problem>

## 3. How the plugin works
<answer to how-it-works>

## 4. AI usage
<answer to ai-usage>

## 5. Verification
<answer to how-verified>

## 6. Synthesis
<one-paragraph synthesis derived from answers 1-3; max 200 words>
```

Non-negotiable rules:
- All 6 sections must be present, in order.
- Section 6 (synthesis) is generated; sections 1-5 are direct quotes of answers.
- Empty answer → raise `AssemblerError`, do not silently skip.
- Output is deterministic for a given state (same input → same output byte-for-byte).
- User-supplied answer text MUST be Markdown-escaped before insertion into the assembled plan (escape `[`, `]`, `<`, `>`, `` ` ``, `#`, `*`, `_`, and any leading `>`) to prevent Markdown injection. Section headings stay hard-coded; only the answer body is escaped.

## Acceptance Criteria
```bash
AC1: python -m pytest tests/test_assembler.py -v → exit 0 (all-sections, missing-answer, determinism, escape-injection)
AC2: python -c "from src.assembler.plan import assemble; from src.schema.state import InterviewState; s=InterviewState(); [s.set_answer(q,'x'*30) for q in ['what-who-where','why-this-problem','how-it-works','ai-usage','how-verified']]; out=assemble(s); assert all(h in out for h in ['## 1.','## 2.','## 3.','## 4.','## 5.','## 6.'])" → exit 0
AC3: python -c "from src.assembler.plan import assemble; from src.schema.state import InterviewState; s=InterviewState(); out=assemble(s)" 2>&1 | grep -q "AssemblerError" → exit 0
AC4: python -c "from src.assembler.plan import assemble; from src.schema.state import InterviewState; s=InterviewState(); s.set_answer('what-who-where','# heading\\n[link](http://x)\\n![img](http://x)\\n`code`\\n*em*\\n_str_\\n> quote\\n<script>alert(1)</script>'); [s.set_answer(q,'x'*30) for q in ['why-this-problem','how-it-works','ai-usage','how-verified']]; out=assemble(s); for tok, esc in [('# heading\\n', '&#35; heading\\n'), ('[link](http://x)', '\\[link\\]\\(http://x\\)'), ('![img]', '!\\[img\\]'), ('`code`', '\\\\`code\\\\`'), ('*em*', '\\\\*em\\\\*'), ('_str_', '\\\\_str\\\\_'), ('> quote', '\\> quote'), ('<script>', '&lt;script&gt;')]: assert tok not in out and esc in out" → exit 0 (all 8 escape vectors neutralized; AND-semantics: token must be absent AND its escaped form must be present — no-op escape fails because the escaped form would be missing)
```

## Verification & Status Update (REQUIRED before claiming done)
1. Run the AC commands above. Quote each exit code.
2. Update `phases/0-mvp/index.json` for THIS step (one of three outcomes):
   - **Success** → `"status": "completed"`, `"summary": "<one-line: files created/modified + key decisions>"`
   - **Unrecoverable failure** (3 retries exhausted) → `"status": "error"`, `"error_message": "<concrete error: which AC failed, with exit code + last 3 lines>"`
   - **External dependency** → `"status": "blocked"`, `"blocked_reason": "<what's needed>"`, then STOP.
3. Emit EXACTLY these two HTML-comment markers as the **last two lines** of the final reply:

```
<!-- status: completed | error | blocked -->
<!-- summary: <one-line outcome> | error_message: <concrete error> | blocked_reason: <what's needed> -->
```

## Don't
- Do not skip section 6 (synthesis). 이유: it is the product surface that ties the 5 answers together.
- Do not call network or external tools. 이유: the assembler is pure-Python; non-goal (1) defers logging.
- Do not include "dev-kit" anywhere. 이유: non-goal (b).
- Do not write outside `src/assembler/`, `tests/test_assembler.py`, `tests/fixtures/completed_state.json`. 이유: path scope.
- Do not skip TDD. 이유: Iron Law L1.
