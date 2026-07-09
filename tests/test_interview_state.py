"""InterviewState tests: transitions, validation, and round-trip serialization."""
from __future__ import annotations

import pytest

from src.schema.questions import QUESTIONS
from src.schema.state import InterviewState, SchemaError, ValidationError


def _valid_answer(qid: str) -> str:
    for q in QUESTIONS:
        if q["id"] == qid:
            return "x" * (q["min_length"] + 1)
    raise AssertionError(f"unknown qid {qid!r}")


def test_fresh_state_starts_at_first_question():
    s = InterviewState()
    assert s.current_question() == QUESTIONS[0]


def test_fresh_state_is_not_complete():
    s = InterviewState()
    assert s.is_complete() is False


def test_fresh_state_answers_dict_is_empty():
    s = InterviewState()
    assert s.answers == {}


def test_set_answer_records_value_for_current_question():
    s = InterviewState()
    value = _valid_answer("what-who-where")
    s.set_answer("what-who-where", value)
    assert s.answers["what-who-where"] == value


def test_advance_moves_to_next_question():
    s = InterviewState()
    s.advance()
    assert s.current_question() == QUESTIONS[1]


def test_advance_full_sequence_reaches_completion():
    s = InterviewState()
    for q in QUESTIONS:
        s.set_answer(q["id"], _valid_answer(q["id"]))
        s.advance()
    assert s.is_complete() is True


def test_is_complete_false_when_only_some_answered():
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    s.advance()
    assert s.is_complete() is False


def test_from_dict_rejects_bool_cursor():
    """Regression: in Python, `isinstance(True, int)` is True (bool subclasses int).
    A payload like `{"cursor": true}` would otherwise silently set _cursor = 1
    and skip question 0 on round-trip. The fix uses `type(cursor) is int and
    not isinstance(cursor, bool)` to reject the bool-as-int subclass case.
    """
    s = InterviewState.from_dict({"cursor": True, "answers": {}})
    # cursor must default to 0 (the derive path), not silently advance to 1.
    assert s.current_question() == QUESTIONS[0]

def test_set_answer_rejects_unknown_question_id():
    s = InterviewState()
    with pytest.raises(SchemaError):
        s.set_answer("not-a-real-id", "anything")


def test_set_answer_rejects_too_short_value():
    s = InterviewState()
    with pytest.raises(ValidationError):
        s.set_answer("what-who-where", "x" * 5)


def test_set_answer_rejects_non_string_value():
    s = InterviewState()
    with pytest.raises(ValidationError):
        s.set_answer("what-who-where", 12345)  # type: ignore[arg-type]


def test_set_answer_rejects_empty_string():
    s = InterviewState()
    with pytest.raises(ValidationError):
        s.set_answer("what-who-where", "")


def test_validate_answer_returns_true_for_valid_value():
    s = InterviewState()
    assert s.validate_answer("what-who-where", _valid_answer("what-who-where")) is True


def test_validate_answer_returns_false_for_short_value():
    s = InterviewState()
    assert s.validate_answer("what-who-where", "short") is False


def test_validate_answer_raises_for_unknown_qid():
    s = InterviewState()
    with pytest.raises(SchemaError):
        s.validate_answer("not-real", "anything")


def test_to_dict_returns_serializable_payload():
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    d = s.to_dict()
    assert isinstance(d, dict)
    assert "answers" in d and isinstance(d["answers"], dict)
    assert "cursor" in d
    assert d["answers"]["what-who-where"] == _valid_answer("what-who-where")


def test_from_dict_rebuilds_equivalent_state():
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    s.advance()
    s.set_answer("why-this-problem", _valid_answer("why-this-problem"))
    d = s.to_dict()

    s2 = InterviewState.from_dict(d)
    assert s2.answers == s.answers
    assert s2.is_complete() == s.is_complete()
    assert s2.current_question()["id"] == s.current_question()["id"]


def test_round_trip_preserves_all_answers():
    s = InterviewState()
    for q in QUESTIONS:
        s.set_answer(q["id"], _valid_answer(q["id"]))
        s.advance()
    d = s.to_dict()
    s2 = InterviewState.from_dict(d)
    assert s2.answers == s.answers
    assert s2.is_complete() is True


def test_from_dict_preserves_partial_progress():
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    s.advance()
    s.set_answer("why-this-problem", _valid_answer("why-this-problem"))
    s.advance()
    d = s.to_dict()
    s2 = InterviewState.from_dict(d)
    assert s2.current_question() == QUESTIONS[2]


def test_from_dict_rejects_unknown_question_id_in_payload():
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    d = s.to_dict()
    d["answers"]["bogus-id"] = "irrelevant"
    with pytest.raises(SchemaError):
        InterviewState.from_dict(d)


def test_from_dict_rejects_undersized_value_in_payload():
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    d = s.to_dict()
    d["answers"]["why-this-problem"] = "x"  # 1 char, min is 20
    with pytest.raises(ValidationError):
        InterviewState.from_dict(d)
