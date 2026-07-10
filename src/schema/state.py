"""Runtime carrier for the 5-question interview: state + validation + (de)serialization."""
from __future__ import annotations

from typing import Any

from .questions import DEFAULT_MAX_LENGTH, QUESTIONS, canonical_ids, get_question

# PR #21 review (security round 3): total-payload cap across all
# answers, on top of the per-question max_length. Default 5 * 2000
# = 10_000 chars — well within 'multi-paragraph idea' territory,
# tight enough to bound the memory-exhaustion DoS surface that
# unbounded input on a documented user-input trust boundary exposed.
# PR #21 round 5: pin MAX_TOTAL_PAYLOAD as an independent constant.
# The previous formula (DEFAULT_MAX_LENGTH * len(QUESTIONS)) auto-grew
# with the schema; adding a question would silently raise the cap and
# re-open the DoS surface. 10_000 chars (5 * 2000) is the explicit
# round-3 bound; tests assert this constant directly.
MAX_TOTAL_PAYLOAD = 10000


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

    def current_question(self) -> dict[str, Any] | None:
        # PR #21 round 4: previously returned QUESTIONS[-1] past end,
        # which silently stalled the interview UI and broke the
        # is_complete() invariant by masquerading as 'still on last
        # question'. Now returns None so callers must branch on end.
        if self._cursor >= len(QUESTIONS):
            return None
        return QUESTIONS[self._cursor]

    def is_complete(self) -> bool:
        return self._cursor >= len(QUESTIONS) and len(self.answers) == len(QUESTIONS)

    def advance(self) -> None:
        # PR #21 review (security round 3, major): advance() now refuses
        # to move the cursor when the current question has no answer.
        # The previous silent increment let a caller reach
        # is_complete()==True while skipping earlier canonical questions.
        if self._cursor >= len(QUESTIONS):
            return  # idempotent at end-of-interview
        expected = canonical_ids()[self._cursor]
        if expected not in self.answers:
            raise SchemaError(
                f"cannot advance: question {expected!r} (cursor={self._cursor}) "
                f"has no answer"
            )
        self._cursor += 1

    def set_answer(self, qid: str, value: Any) -> None:
        # PR #21 round 5 (🟠 major): unknown-id must be reported before
        # out-of-order. The previous ordering made "unknown qid" surface
        # as a misleading "out of order" message because the order
        # check ran first. Now _lookup_question runs first so an
        # unknown id raises SchemaError('unknown question id') even when
        # it also happens to differ from the cursor's expected qid.
        question = self._lookup_question(qid)  # raises SchemaError on unknown id
        ids = canonical_ids()
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
                f"invalid answer for {qid!r}: length {n} outside "
                f"[{question['min_length']}, {question.get('max_length', 'inf')}]"
            )
        self.answers[qid] = value

    @staticmethod
    def validate_answer(qid: str, value: Any) -> bool:
        # PR #21 round 4: promoted to @staticmethod so from_dict can
        # share the same validation path used by set_answer, eliminating
        # the round-3 parallel-validator that the reviewer flagged as
        # sure-to-diverge. min_length and max_length are read from
        # the question dict; both required for a valid answer.
        question = InterviewState._lookup_question(qid)
        if not isinstance(value, str):
            return False
        n = len(value)
        # PR #21 round 6 (🟠 major): strict max_length lookup.
        # The previous .get(..., inf) silently bypassed the round-3 DoS
        # cap when a question dict omitted max_length. Now KeyError → the
        # caller raises a clear ValidationError. To make a question
        # unbounded, callers must explicitly set max_length to math.inf.
        return question["min_length"] <= n <= question["max_length"]


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
        # PR #21 round 7 (🟠 major): schema_version handshake. to_dict
        # serializes schema_version=1; previously from_dict ignored it,
        # so a future v2 payload would silently load as v1 with
        # `payload.get("answers", {})` returning {} on a renamed key
        # (data-loss with no error signal). Now reject anything != 1.
        schema_version = payload.get("schema_version")
        if schema_version != 1:
            raise SchemaError(
                f"unsupported schema_version: {schema_version!r} "
                f"(expected 1)"
            )
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
        # PR #21 review (security round 3, major + A10 partial-state bug):
        # Build a LOCAL dict during validation, then assign to state.answers
        # atomically. A mid-loop ValidationError now raises with state.answers
        # untouched. Also enforce a total-payload cap (sum of answer
        # lengths) to bound the memory-exhaustion DoS surface that the
        # per-question max_length cap alone did not close.
        built: dict[str, str] = {}
        total_len = 0
        for qid, value in raw_answers.items():
            if not isinstance(value, str):
                raise ValidationError(
                    f"payload answer for {qid!r}: must be str, "
                    f"got {type(value).__name__}"
                )
            if not InterviewState.validate_answer(qid, value):
                raise ValidationError(
                    f"payload answer for {qid!r} fails validation"
                )
            total_len += len(value)
            if total_len > MAX_TOTAL_PAYLOAD:
                raise ValidationError(
                    f"payload exceeds MAX_TOTAL_PAYLOAD={MAX_TOTAL_PAYLOAD} chars"
                )
            built[qid] = value
        # Cursor clamp: tie to max_answered_idx so a caller-supplied
        # cursor that desyncs from the answered set is rejected (A06-3).
        max_answered_idx = -1
        for qid in built.keys():
            idx = ids.index(qid)
            if idx > max_answered_idx:
                max_answered_idx = idx
        cursor = payload.get("cursor")
        # PR #21 round 8 (🟠 major): reject non-int cursors with an
        # explicit SchemaError. Previously a non-int cursor (e.g. a
        # string or float) silently fell through to the canonical_ids
        # walk in the else branch, masking a programming error as
        # a valid first-unanswered cursor.
        if cursor is not None and (
            type(cursor) is not int or isinstance(cursor, bool)
        ):
            raise SchemaError(
                f"cursor must be an int, got {type(cursor).__name__}: {cursor!r}"
            )
        if type(cursor) is int and not isinstance(cursor, bool) and cursor >= 0:
            # Caller cursor must not exceed the highest answered index + 1;
            # otherwise the state is unreachable-by-construction.
            # PR #21 round 6 (🟠 major): symmetric cursor clamp with
            # lower bound. Previously cursor could be < 0 (silently
            # resetting the interview to start) or > len(QUESTIONS)
            # (producing an unreachable-by-construction state).
            if cursor < 0:
                raise SchemaError(
                    f"cursor must be non-negative, got {cursor}"
                )
            if cursor > len(QUESTIONS):
                raise SchemaError(
                    f"cursor {cursor} exceeds len(QUESTIONS)={len(QUESTIONS)}"
                )
            # Upper bound: cursor may not exceed max_answered_idx+1
            # (otherwise the state would be unreachable-by-construction).
            state_cursor = min(cursor, max_answered_idx + 1, len(QUESTIONS))
            state._cursor = state_cursor
        else:
            # PR #21 round 6 (🟠 major): even when the caller doesn't
            # supply a cursor, validate cursor parity (caller used the
            # boolean-false branch which is correct, but a non-int cursor
            # value like -1 in the JSON must still be rejected).
            if isinstance(cursor, int) and cursor < 0:
                raise SchemaError(
                    f"cursor must be non-negative, got {cursor}"
                )
            # No caller cursor: walk canonical_ids() to the first
            # unanswered question. PR #21 round-2 fix; preserves the
            # round-trip semantics where a re-loaded state prompts for
            # the right next question even when answers arrived in a
            # non-canonical order.
            state._cursor = 0
            for qid in canonical_ids():
                if qid not in built:
                    break
                state._cursor += 1
        # Only assign the built dict after the cursor is settled, so any
        # exception path leaves state in its post-construction state.
        state.answers = built
        return state