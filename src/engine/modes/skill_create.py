"""Mode C — skill_create: 3-question interview + dual-runtime SKILL.md emitter.

This module adds the `skill_create` sub-mode to the existing plugin-harness
engine. It DOES NOT modify 0-mvp's 5-question interview, schema, or emitter;
it runs in parallel via:
  - SKILL_QUESTIONS (3 questions, defined in src/skill_schema/prompts.py)
  - SkillInterviewState (this file; bound to SKILL_QUESTIONS)
  - emit_skill (defined in src/emitter/skill.py)

The runner iterates whichever question list is passed in; the new `questions`
parameter on `run_interview` defaults to the 0-mvp `QUESTIONS` and is
overridden by cli.py for `--mode=skill_create`.
"""
from __future__ import annotations

from typing import Callable, List, Optional

from src.engine.errors import ToolSurface, UserAbortError
from src.schema.state import SchemaError, ValidationError
from src.skill_schema.prompts import (
    SKILL_QUESTIONS,
    get_skill_question,
    skill_canonical_ids,
)


# ---- state ----

MAX_TOTAL_PAYLOAD = 6000  # 3 questions × 2000 chars; matches src/schema/state.py policy


class SkillInterviewState:
    """Mutable interview progress bound to SKILL_QUESTIONS.

    Mirrors src/schema/state.py:InterviewState but pinned to the 3-question
    skill_create schema. Same exception types (SchemaError, ValidationError)
    so the runner's catch-blocks work uniformly.
    """

    def __init__(self) -> None:
        self.answers: dict[str, str] = {}
        self._cursor: int = 0

    @staticmethod
    def _lookup_question(qid: str) -> dict:
        try:
            return get_skill_question(qid)
        except KeyError as exc:
            raise SchemaError(f"unknown question id: {qid!r}") from exc

    def current_question(self) -> Optional[dict]:
        ids = skill_canonical_ids()
        if self._cursor >= len(ids):
            return None
        return SKILL_QUESTIONS[self._cursor]

    def is_complete(self) -> bool:
        return len(self.answers) >= len(skill_canonical_ids())

    def advance(self) -> None:
        ids = skill_canonical_ids()
        if self._cursor >= len(ids):
            return
        expected = ids[self._cursor]
        if expected not in self.answers:
            raise SchemaError(
                f"cannot advance: question {expected!r} (cursor={self._cursor}) "
                f"has no answer"
            )
        self._cursor += 1

    def set_answer(self, qid: str, value) -> None:
        self._lookup_question(qid)  # raises SchemaError on unknown id
        ids = skill_canonical_ids()
        if self._cursor >= len(ids):
            raise SchemaError(
                f"cannot set_answer: interview already complete (cursor={self._cursor})"
            )
        expected = ids[self._cursor]
        if qid != expected:
            raise SchemaError(
                f"set_answer out of order: expected {expected!r} at cursor "
                f"{self._cursor}, got {qid!r}"
            )
        if not self.validate_answer(qid, value):
            n = len(value) if isinstance(value, str) else 0
            raise ValidationError(
                f"invalid answer for {qid!r}: length {n} outside accepted range"
            )
        self.answers[qid] = value

    @staticmethod
    def validate_answer(qid: str, value) -> bool:
        try:
            q = SkillInterviewState._lookup_question(qid)
        except SchemaError:
            return False
        if not isinstance(value, str):
            return False
        return q["min_length"] <= len(value) <= q["max_length"]


# ---- runner shortcut ----

def run_skill_interview(
    idea: str,
    *,
    stdin_reader: Callable[[str], str],
    stdout_writer: Optional[Callable[[str], None]] = None,
    _tool_surface: Optional[ToolSurface] = None,
) -> SkillInterviewState:
    """Drive the 3-question skill_create interview.

    Args:
        idea: free-form idea string (currently unused but kept for runner parity).
        stdin_reader: callable that returns one answer per question prompt.
        stdout_writer: optional callable to emit each prompt.

    Returns:
        A completed SkillInterviewState.

    Raises:
        UserAbortError: when the reader signals abort.
        SchemaError / ValidationError: propagated from the state.
    """
    state = SkillInterviewState()
    for question in SKILL_QUESTIONS:
        if stdout_writer is not None:
            stdout_writer(question["prompt"])
        try:
            raw = stdin_reader(question["prompt"])
        except UserAbortError:
            raise
        except Exception as exc:  # pragma: no cover (defensive only)
            raise UserAbortError(f"skill_create reader raised {type(exc).__name__}") from exc
        try:
            state.set_answer(question["id"], raw)
            state.advance()
        except (SchemaError, ValidationError):
            # PR #40 review (🟠 major): Do NOT mask state errors as UserAbortError.
            # `run_interview` translates state errors to InterviewIncompleteError
            # (mapped to exit 4 at the CLI); we follow the same convention here
            # so the CLI in `_run_skill_create` can map these to exit 4 (validation
            # failure), not exit 3 (user abort). UserAbortError is reserved for
            # the stdin-reader signal.
            raise

    return state


# ---- mode registration (consumed by the engine) ----

def _setup_skill_create(_make_reader, _make_writer, _make_tool_surface):
    """No-op factory: skill_create uses the same reader/surface machinery
    as `user` mode (one line per question via stdin)."""
    return None, None, None


# PR #40 review fix: register a real (non-poisoned) MODE_DISPATCH entry for
# `skill_create`. The 0-mvp test `test_mode_dispatch_registers_both_modes`
# asserts every name in MODES has a MODE_DISPATCH entry. cli.py dispatches
# skill_create through `run_interview(questions=SKILL_QUESTIONS, ...)`,
# which iterates the question list passed in (NOT the 5-question default
# `QUESTIONS`) and dispatches each question to the registered handler.
def _skill_create_per_question(question, idea, stdin_reader, _tool_surface):
    """Per-question handler for skill_create mode.

    Reads one line per SKILL_QUESTIONS item via `stdin_reader`. The runner
    (run_interview) passes each question dict and the same stdin_reader
    the cli.py / caller configured. Returns the raw answer text.
    """
    if stdin_reader is None:
        raise UserAbortError("'skill_create' mode requires stdin_reader")
    return stdin_reader(question["prompt"])


# Imports at the bottom so the registration call fires after `register_mode`
# is defined.
from src.engine.modes import register_mode  # noqa: E402

register_mode("skill_create", _skill_create_per_question)
