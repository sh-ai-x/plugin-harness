"""Runtime carrier for the 5-question interview: state + validation + (de)serialization."""
from __future__ import annotations

from typing import Any

from .questions import QUESTIONS, canonical_ids, get_question


class SchemaError(Exception):
    """Raised when the schema reference is wrong (unknown id, malformed payload)."""


class ValidationError(Exception):
    """Raised when an answer does not satisfy its question's validation rules."""


class InterviewState:
    """Mutable interview progress: answers dict + cursor index.

    Cursor semantics: ``_cursor`` is the index of the next question to ask.
    ``set_answer`` only records the value (and validates). ``advance`` is
    the only way to move the cursor forward.
    """

    def __init__(self) -> None:
        self.answers: dict[str, str] = {}
        self._cursor: int = 0

    # ---- schema helpers ----

    @staticmethod
    def _lookup_question(qid: str) -> dict[str, Any]:
        # PR #21 review: switched from the private question-by-id dict
        # to the public get_question() accessor, with a KeyError to
        # SchemaError translation so the unknown-id contract stays
        # consistent across this module.
        try:
            return get_question(qid)
        except KeyError as exc:
            raise SchemaError(f"unknown question id: {qid!r}") from exc

    # ---- public API ----

    def current_question(self) -> dict[str, Any]:
        if self._cursor >= len(QUESTIONS):
            return QUESTIONS[-1]
        return QUESTIONS[self._cursor]

    def is_complete(self) -> bool:
        return self._cursor >= len(QUESTIONS) and len(self.answers) == len(QUESTIONS)

    def advance(self) -> None:
        if self._cursor < len(QUESTIONS):
            self._cursor += 1

    def set_answer(self, qid: str, value: Any) -> None:
        question = self._lookup_question(qid)  # raises SchemaError on unknown id
        if not self.validate_answer(qid, value):
            n = len(value) if isinstance(value, str) else 0
            raise ValidationError(
                f"invalid answer for {qid!r}: length {n} outside "
                f"[{question['min_length']}, {question.get('max_length', 'inf')}]"
            )
        self.answers[qid] = value

    def validate_answer(self, qid: str, value: Any) -> bool:
        question = self._lookup_question(qid)
        if not isinstance(value, str):
            return False
        n = len(value)
        # PR #21 review: per-question max_length cap (default 2000) bounds
        # the memory-exhaustion DoS surface on the documented user-input
        # trust boundary. min_length and max_length are read from the
        # question dict; both are required for a valid answer.
        return question["min_length"] <= n <= question.get("max_length", float("inf"))

    # ---- (de)serialization ----

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "cursor": self._cursor,
            "answers": dict(self.answers),
            "canonical_ids": list(canonical_ids()),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterviewState":
        if not isinstance(payload, dict):
            raise SchemaError(f"payload must be a dict, got {type(payload).__name__}")
        raw_answers = payload.get("answers", {})
        if not isinstance(raw_answers, dict):
            raise SchemaError("payload['answers'] must be a dict")
        ids = canonical_ids()
        unknown = [k for k in raw_answers.keys() if k not in ids]
        if unknown:
            raise SchemaError(
                f"payload contains unknown question ids: {sorted(unknown)!r}"
            )
        state = cls()
        # Validate every answer; raises ValidationError on bad data.
        for qid, value in raw_answers.items():
            if not state.validate_answer(qid, value):
                raise ValidationError(
                    f"payload answer for {qid!r} fails validation"
                )
            state.answers[qid] = value
        # Honor caller-supplied cursor when it's a non-negative int.
        # Note: `type(cursor) is int` (NOT isinstance) because in Python `bool`
        # is a subclass of `int`; isinstance(True, int) is True. A payload like
        # {"cursor": true} would otherwise silently set _cursor = 1 and skip
        # question 0. See regression test_rejects_bool_cursor in test_interview_state.py.
        cursor = payload.get("cursor")
        if type(cursor) is int and not isinstance(cursor, bool) and cursor >= 0:
            state._cursor = min(cursor, len(QUESTIONS))
        else:
            # PR #21 review: previous derivation jumped to max(answered)+1
            # and stranded earlier canonical questions if answers arrived
            # out of order (e.g. Q4 answered before Q0). Walk canonical_ids()
            # to the first unanswered question so re-runs prompt for the
            # right next question.
            state._cursor = 0
            for qid in canonical_ids():
                if qid not in state.answers:
                    break
                state._cursor += 1
        return state
