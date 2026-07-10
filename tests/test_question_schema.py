"""Schema tests: load + structural completeness of the 5 fixed interview questions."""
from __future__ import annotations

import pytest

from src.schema.questions import QUESTIONS


REQUIRED_FIELDS = ("id", "prompt", "answer_type", "choices", "min_length", "validation_hint")
CANONICAL_IDS = (
    "what-who-where",
    "why-this-problem",
    "how-it-works",
    "ai-usage",
    "how-verified",
)


def test_questions_count_is_five():
    assert len(QUESTIONS) == 5


def test_questions_canonical_order():
    ids = [q["id"] for q in QUESTIONS]
    assert ids == list(CANONICAL_IDS)


def test_every_question_has_all_required_fields():
    for q in QUESTIONS:
        for field in REQUIRED_FIELDS:
            assert field in q, f"question {q.get('id')!r} missing field {field!r}"


def test_every_question_id_is_non_empty_string():
    for q in QUESTIONS:
        assert isinstance(q["id"], str) and q["id"], f"empty id in {q!r}"


def test_every_question_prompt_is_non_empty_string():
    for q in QUESTIONS:
        assert isinstance(q["prompt"], str) and q["prompt"], f"empty prompt in {q['id']!r}"


def test_every_question_answer_type_is_text():
    for q in QUESTIONS:
        assert q["answer_type"] == "text", (
            f"question {q['id']!r} answer_type must be 'text', got {q['answer_type']!r}"
        )


def test_every_question_choices_is_list():
    for q in QUESTIONS:
        assert isinstance(q["choices"], list), (
            f"question {q['id']!r} choices must be a list"
        )


def test_every_question_min_length_is_positive_int():
    for q in QUESTIONS:
        assert isinstance(q["min_length"], int) and q["min_length"] > 0, (
            f"question {q['id']!r} min_length must be a positive int"
        )


def test_every_question_validation_hint_is_string():
    for q in QUESTIONS:
        assert isinstance(q["validation_hint"], str) and q["validation_hint"], (
            f"question {q['id']!r} validation_hint must be a non-empty string"
        )


def test_min_length_matches_hint_threshold():
    for q in QUESTIONS:
        assert q["min_length"] == 20, (
            f"question {q['id']!r} min_length must be 20 (locked canonical), got {q['min_length']}"
        )


def test_ids_are_unique():
    ids = [q["id"] for q in QUESTIONS]
    assert len(set(ids)) == len(ids), f"duplicate ids in schema: {ids}"


def test_question_ids_match_canonical_exactly():
    ids = [q["id"] for q in QUESTIONS]
    assert set(ids) == set(CANONICAL_IDS), (
        f"schema ids {ids!r} must match canonical set {CANONICAL_IDS!r}"
    )

def test_questions_is_list_of_mapping_proxies():
    """Each question dict is wrapped in MappingProxyType (PR #21 round 6)."""
    assert isinstance(QUESTIONS, list)
    assert len(QUESTIONS) > 0
    for q in QUESTIONS:
        as_dict = dict(q)
        assert "id" in as_dict
        assert "max_length" in as_dict
