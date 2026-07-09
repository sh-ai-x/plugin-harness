"""Runtime carrier for the 5-question interview: state + validation + (de)serialization."""
from __future__ import annotations

from typing import Any

from .questions import QUESTIONS, _QUESTION_BY_ID, canonical_ids


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
        q = _QUESTION_BY_ID.get(qid)
        if q is None:
            raise SchemaError(f"unknown question id: {qid!r}")
        return q

    # ---- public API ----

    def current_question(self) -> dict[str, Any]:
        if self._cursor >= len(QUESTIONS):
            return QUESTIONS[-1]
        return QUESTIONS[self._cursor]

    def is_complete(self) -> bool:
        # PR #28 / step-6 round-1: completeness is a function of the answer
        # set, NOT the cursor position. set_answer() documents that it
        # ONLY records (and validates); advance() moves the cursor.
        # Therefore requiring _cursor >= len(QUESTIONS) is an invariant
        # violation — every caller that filled all 5 answers without
        # calling advance() (the test_emitter.py:46 fixture, offline bulk
        # import, deserialization of pre-populated states) was wrongly
        # reported incomplete. See regression test:
        # test_is_complete_true_when_all_answers_set_via_set_answer_without_advance.
        return len(self.answers) >= len(QUESTIONS)

    def advance(self) -> None:
        if self._cursor < len(QUESTIONS):
            self._cursor += 1

    def set_answer(self, qid: str, value: Any) -> None:
        self._lookup_question(qid)  # raises SchemaError on unknown id
        if not self.validate_answer(qid, value):
            raise ValidationError(
                f"invalid answer for {qid!r}: must be str with len >= "
                f"{_QUESTION_BY_ID[qid]['min_length']}"
            )
        self.answers[qid] = value

    def validate_answer(self, qid: str, value: Any) -> bool:
        question = self._lookup_question(qid)
        if not isinstance(value, str):
            return False
        return len(value) >= question["min_length"]

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
        unknown = [k for k in raw_answers.keys() if k not in _QUESTION_BY_ID]
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
        cursor = payload.get("cursor")
        if isinstance(cursor, int) and cursor >= 0:
            state._cursor = min(cursor, len(QUESTIONS))
        else:
            # Derive cursor from the highest canonical index with an answer.
            max_idx = -1
            for qid in raw_answers.keys():
                idx = canonical_ids().index(qid)
                if idx > max_idx:
                    max_idx = idx
            state._cursor = max_idx + 1 if max_idx >= 0 else 0
        return state
