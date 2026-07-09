"""End-to-end pipeline orchestration shared between e2e and smoke tests.

Wires the build-time pipeline that proves the dual-runtime contract:

    interview (mode A, user-driven)  ->
    assembler.plan.assemble           ->
    emitter.codex.emit                ->
    emitter.validator.validate_emit   ->
    adapter.cc.register_cc            ->
    adapter.codex.register_codex      ->
    runtime-parity (CC skill body == Codex skill body, byte-for-byte)

Two entrypoints exposed for the two bash wrappers:

    run_e2e_pipeline(output_dir)    — full proof including parity check
    run_smoke_pipeline(output_dir)  — smoke subset (parity is e2e-only)

Both entrypoints return a dict so callers (bash wrappers, pytest) can
inspect intermediate artifacts without re-running anything.

Note on stdin injection: `run_interview` accepts an injectable
`stdin_reader` callable (see src/engine/modes/user_driven.py). The
scripted reader here exhausts a 5-element queue; an `AssertionError`
is raised if the reader is asked for a 6th answer (guards against
regressions where the interview grows past 5 questions).
"""
from __future__ import annotations

import pathlib

from tests.e2e._yaml import extract_body as _extract_body
from typing import Callable, List

from src.adapter.cc import register_cc
from src.adapter.codex import register_codex
from src.assembler.plan import assemble
from src.emitter.codex import emit
from src.emitter.validator import validate_emit
from src.engine import run_interview
from src.schema.state import InterviewState


# Five scripted answers, each ≥ 20 chars so they clear the schema
# `min_length` constraint without trimming or padding gymnastics.
SCRIPTED_ANSWERS: List[str] = [
    "answer-one-with-at-least-twenty-chars",
    "answer-two-with-at-least-twenty-chars",
    "answer-three-with-at-least-twenty-chars",
    "answer-four-with-at-least-twenty-chars",
    "answer-five-with-at-least-twenty-chars",
]

IDEA: str = "dual-runtime plugin-harness end-to-end test"


def _scripted_reader(answers: List[str]) -> Callable[[str], str]:
    """Inject answers to the engine's stdin-reader in order.

    Each prompt consumes the next answer; the queue must be exhausted
    in exactly five calls (the canonical interview length). A sixth
    call raises `AssertionError` so a regression that grows the
    interview past 5 questions is caught loudly.
    """
    queue: List[str] = list(answers)

    def reader(_prompt: str) -> str:
        if not queue:
            raise AssertionError(
                "scripted reader exhausted before interview completed; "
                "if the interview grew past 5 questions, update "
                "SCRIPTED_ANSWERS in tests/e2e/pipeline.py"
            )
        return queue.pop(0)

    return reader


def _quiet_writer() -> Callable[[str], None]:
    """Discard stdout output from the engine (keep pytest output clean)."""
    def writer(_line: str) -> None:
        return None
    return writer


def _run_interview_scripted() -> InterviewState:
    """Drive mode A (user-driven) interview with SCRIPTED_ANSWERS.

    Returns a fully completed `InterviewState` or raises.
    """
    state = InterviewState()
    state = run_interview(
        state,
        "user",
        idea=IDEA,
        stdin_reader=_scripted_reader(SCRIPTED_ANSWERS),
        stdout_writer=_quiet_writer(),
        tool_surface=None,
    )
    if not state.is_complete():
        answered = sum(1 for v in state.answers.values() if v)
        raise AssertionError(
            f"interview did not complete; got {answered}/5 answers"
        )
    return state




_CC_SKILL_REL = pathlib.Path(".claude/skills/plugin-harness/SKILL.md")
_CODEX_SKILL_REL = pathlib.Path(".agents/skills/plugin-harness/SKILL.md")


def _assert_runtime_parity(project_dir: pathlib.Path) -> None:
    """CC skill body must equal Codex skill body, byte-for-byte.

    Install paths differ by convention — CC under `.claude/`, Codex
    under `.agents/` per https://developers.openai.com/codex/skills —
    but the bodies inside (after front-matter) must match. That's the
    concrete dual-runtime contract this harness promises.
    """
    cc_skill = pathlib.Path(project_dir) / _CC_SKILL_REL
    codex_skill = pathlib.Path(project_dir) / _CODEX_SKILL_REL
    if not cc_skill.is_file():
        raise AssertionError(f"CC skill missing: {cc_skill}")
    if not codex_skill.is_file():
        raise AssertionError(f"Codex skill missing: {codex_skill}")
    cc_body = _extract_body(cc_skill.read_text(encoding="utf-8"))
    codex_body = _extract_body(codex_skill.read_text(encoding="utf-8"))
    if cc_body != codex_body:
        def _snippet(body: str, limit: int = 120) -> str:
            return (body[:limit] + "...") if len(body) > limit else body
        raise AssertionError(
            "runtime parity failed: CC SKILL.md body != Codex SKILL.md body\n"
            f"--- CC body ({len(cc_body)} bytes) ---\n{_snippet(cc_body)}\n"
            f"--- Codex body ({len(codex_body)} bytes) ---\n{_snippet(codex_body)}\n"
        )


def run_e2e_pipeline(output_dir: pathlib.Path) -> dict:
    """Full end-to-end pipeline including the runtime-parity check.

    Steps, in order (each must succeed for the next to run):

      1. run_interview (mode A, scripted stdin, full 5-question flow)
      2. assemble(state) → plan Markdown
      3. emit(state, plan_md, output_dir)
      4. validate_emit(output_dir)
      5. register_cc(output_dir)
      6. register_codex(output_dir)
      7. assert CC SKILL.md body == Codex SKILL.md body (parity proof)
    """
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    state = _run_interview_scripted()
    plan_md = assemble(state)
    emit(state, plan_md, output_dir)

    report = validate_emit(output_dir)
    if not report.ok:
        raise AssertionError(
            "validate_emit reported failures: " + "; ".join(report.errors)
        )

    register_cc(output_dir)
    register_codex(output_dir)
    _assert_runtime_parity(output_dir)

    return {"state": state, "plan": plan_md, "report": report}


def run_smoke_pipeline(output_dir: pathlib.Path) -> dict:
    """Smoke subset: skip parity check (parity is the e2e proof point).

    Per step 0 the 5-question contract is locked, so smoke runs the
    full interview flow (not an abbreviation), installs both adapters,
    and validates the emitted plugin. Parity byte-equality is in
    run_e2e_pipeline.
    """
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    state = _run_interview_scripted()
    plan_md = assemble(state)
    emit(state, plan_md, output_dir)

    report = validate_emit(output_dir)
    if not report.ok:
        raise AssertionError(
            "validate_emit reported failures: " + "; ".join(report.errors)
        )

    register_cc(output_dir)
    register_codex(output_dir)

    return {"state": state, "plan": plan_md, "report": report}


__all__ = [
    "run_e2e_pipeline",
    "run_smoke_pipeline",
    "SCRIPTED_ANSWERS",
    "IDEA",
]
