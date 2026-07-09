"""Interview state machine.

Carries the user's answers through the 5-question interview and round-trips
to a plain dict for persistence between process boundaries.
"""

from __future__ import annotations

from typing import Any

from src.schema.questions import QUESTIONS


class SchemaError(ValueError):
    """Raised when the schema is incomplete or a required field is missing."""


class InterviewState:
    """Runtime carrier for the 5-question interview."""

    def __init__(self) -> None:
        self._current_index: int = 0
        self.answers: dict[str, str] = {}

    # ------------------------------------------------------------------ cursor
    def current_question(self) -> dict | None:
        if self._current_index >= len(QUESTIONS):
            return None
        return QUESTIONS[self._current_index]

    def advance(self) -> None:
        if self._current_index < len(QUESTIONS):
            self._current_index += 1

    def is_complete(self) -> bool:
        return self._current_index >= len(QUESTIONS) and all(
            q["id"] in self.answers for q in QUESTIONS
        )

    # ------------------------------------------------------------------ mutate
    def set_answer(self, qid: str, value: str) -> None:
        if not any(q["id"] == qid for q in QUESTIONS):
            raise SchemaError(f"unknown question id: {qid!r}")
        self.validate_answer(qid, value)
        self.answers[qid] = value
        # auto-advance if we just answered the current question
        cur = self.current_question()
        if cur is not None and cur["id"] == qid:
            self.advance()

    def validate_answer(self, qid: str, value: str) -> None:
        if not any(q["id"] == qid for q in QUESTIONS):
            raise SchemaError(f"unknown question id: {qid!r}")
        if not isinstance(value, str):
            raise SchemaError(f"answer for {qid!r} must be str, got {type(value).__name__}")
        if not value.strip():
            raise SchemaError(f"answer for {qid!r} is empty")
        q = next(q for q in QUESTIONS if q["id"] == qid)
        if len(value) < q["min_length"]:
            raise SchemaError(
                f"answer for {qid!r} too short ({len(value)} < {q['min_length']})"
            )

    # ------------------------------------------------------------------ round-trip
    def to_dict(self) -> dict[str, Any]:
        return {
            "current_index": self._current_index,
            "answers": dict(self.answers),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterviewState":
        state = cls()
        state._current_index = int(payload.get("current_index", 0))
        state.answers = dict(payload.get("answers", {}))
        return state