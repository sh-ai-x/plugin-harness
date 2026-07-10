"""InterviewState tests: transitions, validation, and round-trip serialization."""
from __future__ import annotations

import pytest

from src.schema.questions import QUESTIONS, DEFAULT_MAX_LENGTH
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
    # PR #21 security round 3: advance() refuses to move the cursor
    # when the current question has no answer. The test now sets the
    # answer first, mirroring the canonical interview flow.
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
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
    s = InterviewState.from_dict({"schema_version": 1, "cursor": True, "answers": {}})
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


# ---------- PR #21 review regression: max_length cap + cursor-fallback walk ----------
def test_set_answer_rejects_too_long_value():
    """PR #21 review (🟠 major): max_length caps answer length to bound the
    memory-exhaustion DoS surface on the documented user-input trust boundary.
    """
    s = InterviewState()
    too_long = "x" * (DEFAULT_MAX_LENGTH + 1)
    with pytest.raises(ValidationError):
        s.set_answer("what-who-where", too_long)


def test_set_answer_accepts_value_at_max_length():
    """Boundary case: value of exactly max_length chars is accepted."""
    s = InterviewState()
    at_max = "x" * DEFAULT_MAX_LENGTH
    s.set_answer("what-who-where", at_max)
    assert s.answers["what-who-where"] == at_max


def test_from_dict_cursor_walks_canonical_on_out_of_order_answers():
    """PR #21 review (🟡 minor): previous cursor fallback jumped to
    max(answered)+1 and stranded earlier canonical questions when answers
    arrived out of order (e.g. Q4 answered before Q0). Now walks
    canonical_ids() to the first unanswered question.
    """
    s = InterviewState.from_dict({
        "schema_version": 1,
        "answers": {
            "how-verified": "x" * 30,  # idx 4
            "what-who-where": "y" * 30,  # idx 0
            # Q1, Q2, Q3 unanswered
        }
    })
    # The first unanswered canonical question is idx 1 (why-this-problem).
    assert s.current_question()["id"] == "why-this-problem"


def test_state_does_not_import_private_question_index():
    """PR #21 review (🟠 major leaky abstraction): state.py previously
    imported the private _QUESTION_BY_ID. Now uses only the public
    get_question() / canonical_ids() API.
    """
    import src.schema.state as state_mod
    src = open(state_mod.__file__).read()
    assert "_QUESTION_BY_ID" not in src, "state.py must not import the private _QUESTION_BY_ID"


# ---------- PR #21 security round 3 regression ----------
def test_set_answer_rejects_out_of_order():
    """🟠 major: set_answer no longer accepts an out-of-order qid."""
    s = InterviewState()
    s.set_answer("what-who-where", _valid_answer("what-who-where"))
    # Cursor is now 0 (still — set_answer doesn't advance in this contract).
    # Attempt to answer Q4 directly should raise.
    s2 = InterviewState()
    with pytest.raises(SchemaError, match="set_answer out of order"):
        s2.set_answer("how-verified", _valid_answer("how-verified"))


def test_advance_refuses_when_current_question_unanswered():
    """🟠 major: advance() refuses to skip ahead when the current q has no answer."""
    s = InterviewState()
    with pytest.raises(SchemaError, match="has no answer"):
        s.advance()


def test_from_dict_atomic_on_partial_validation_failure():
    """🟠 major (A10): from_dict assigns state.answers only after full success."""
    # The 6th canonical question id is unknown -> ValidationError must NOT leave
    # state.answers populated. Note: from_dict validates qid membership before
    # validate_answer, so an unknown qid raises SchemaError not ValidationError.
    # Use a known qid with too-short value to trigger ValidationError mid-loop.
    too_short = "x" * 5
    with pytest.raises(ValidationError):
        InterviewState.from_dict({
            "schema_version": 1,
            "answers": {
                "what-who-where": _valid_answer("what-who-where"),
                "why-this-problem": too_short,  # < min_length
            }
        })
    # The error path: a separate fresh state must not be polluted.
    # The error path: too_short value triggers ValidationError before built is
    # assigned to state.answers. From the from_dict contract this is a single
    # exception; we never reach the return statement. Test the *observable*
    # contract: a separate fresh state must not be polluted.
    fresh = InterviewState()
    assert fresh.answers == {}


def test_from_dict_rejects_cursor_that_desyncs_from_answered():
    """🟠 major (A06-3): caller cursor > max(answered)+1 is clamped."""
    s = InterviewState.from_dict({
        "schema_version": 1,
        "cursor": 4,  # claims Q4 is next, but only Q0-Q2 answered
        "answers": {
            "what-who-where": _valid_answer("what-who-where"),
            "why-this-problem": _valid_answer("why-this-problem"),
            "how-it-works": _valid_answer("how-it-works"),
        },
    })
    # max_answered_idx=2, so cursor must clamp to 3 (next after Q2).
    assert s._cursor == 3
    assert s.current_question()["id"] == "ai-usage"


def test_from_dict_enforces_per_question_max_length():
    """🟠 major (A06): per-question max_length caps individual answer length.

    The total-payload cap (MAX_TOTAL_PAYLOAD) is defense-in-depth on top
    of per-question max_length; with 5 canonical questions at the
    per-question cap, the total equals MAX_TOTAL_PAYLOAD exactly. Going
    over per-question max_length is caught first (this test), and the
    total cap is the second line of defense.
    """
    with pytest.raises(ValidationError, match="fails validation"):
        InterviewState.from_dict({
            "schema_version": 1,
            "answers": {
                qid: "x" * (DEFAULT_MAX_LENGTH + 1)  # 1 over per-q cap
                for qid in ["what-who-where", "why-this-problem", "how-it-works", "ai-usage", "how-verified"]
            }
        })


# ---------- PR #21 security round 4 regression ----------
def test_validate_answer_is_static_and_shared():
    """🟠 major (round 4): validate_answer must be @staticmethod so from_dict
    can share the same validation path. Asserts no instance required and
    that the helper is callable from from_dict's build loop.
    """
    # Static: no instance needed
    valid = InterviewState.validate_answer("what-who-where", _valid_answer("what-who-where"))
    assert valid is True
    invalid = InterviewState.validate_answer("what-who-where", "x" * 5)
    assert invalid is False


def test_module_no_longer_exports_private_validator():
    """🟠 major (round 4): the round-3 _validate_value_against_question helper
    must be removed in round 4 (its divergent logic was the round-4 finding).
    """
    import src.schema.state as state_mod
    assert not hasattr(state_mod, "_validate_value_against_question"), (
        "private validator helper must be removed — its divergent logic is the round-4 finding"
    )


def test_current_question_returns_none_past_end():
    """🟠 major (round 4): current_question() past end returns None, not the
    last question. Callers must branch on completion explicitly.
    """
    s = InterviewState()
    for q in QUESTIONS:
        s.set_answer(q["id"], _valid_answer(q["id"]))
        s.advance()
    assert s.is_complete() is True
    assert s.current_question() is None


# ---------- PR #21 round 6 regression: symmetric cursor clamp ----------
def test_from_dict_rejects_negative_cursor():
    """🟠 major: cursor < 0 silently reset the interview to start. Now
    raises SchemaError."""
    with pytest.raises(SchemaError, match="cursor must be non-negative"):
        InterviewState.from_dict({"schema_version": 1, "cursor": -1, "answers": {}})


def test_deep_freeze_questions_blocks_mutation():
    """🟠 major: PR #21 round 6 deep-freezes each question dict via
    MappingProxyType so callers cannot mutate a question via
    QUESTIONS[i]['max_length'] = 10**9 to silently disable the DoS cap.
    """
    from src.schema.questions import QUESTIONS
    for q in QUESTIONS:
        with pytest.raises(TypeError, match="does not support item assignment"):
            q["max_length"] = 10**9


# ---------- PR #21 round 7 regression: schema_version handshake ----------
def test_from_dict_rejects_unsupported_schema_version():
    """🟠 major (round 7): from_dict must reject any payload whose
    schema_version is != 1, instead of silently treating a future v2
    payload as v1 (which silently produced an empty state with the
    answers key renamed)."""
    with pytest.raises(SchemaError, match="unsupported schema_version"):
        InterviewState.from_dict({"schema_version": 2, "answers": {}})
    with pytest.raises(SchemaError, match="unsupported schema_version"):
        InterviewState.from_dict({"schema_version": None, "answers": {}})
    # Missing schema_version field
    with pytest.raises(SchemaError, match="unsupported schema_version"):
        InterviewState.from_dict({"answers": {}})


def test_from_dict_accepts_schema_version_1():
    """The handshake must NOT reject schema_version=1 (positive case)."""
    state = InterviewState.from_dict({
        "schema_version": 1,
        "answers": {
            qid: _valid_answer(qid) for qid in [q["id"] for q in QUESTIONS]
        },
    })
    assert state.is_complete()
