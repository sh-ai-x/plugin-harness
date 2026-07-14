"""Tests for src/skill_schema/prompts.py (3-question skill_create schema)."""
from __future__ import annotations

import pytest


# ---------- shape ----------

def test_skill_questions_count_is_three():
    from src.skill_schema.prompts import SKILL_QUESTIONS
    assert len(SKILL_QUESTIONS) == 3


def test_skill_canonical_order_is_locked():
    from src.skill_schema.prompts import SKILL_QUESTIONS, skill_canonical_ids
    assert skill_canonical_ids() == ("purpose", "examples", "success-criteria")
    assert [q["id"] for q in SKILL_QUESTIONS] == ["purpose", "examples", "success-criteria"]


def test_every_skill_question_has_required_fields():
    from src.skill_schema.prompts import SKILL_QUESTIONS
    required = ("id", "prompt", "answer_type", "choices", "min_length",
                "max_length", "validation_hint")
    for q in SKILL_QUESTIONS:
        for field in required:
            assert field in q, f"skill question {q.get('id')!r} missing field {field!r}"


def test_get_skill_question_known_returns_dict():
    from src.skill_schema.prompts import get_skill_question
    q = get_skill_question("purpose")
    assert q["id"] == "purpose"
    assert q["min_length"] >= 1


def test_get_skill_question_unknown_raises_keyerror():
    from src.skill_schema.prompts import get_skill_question
    with pytest.raises(KeyError):
        get_skill_question("not-a-real-question")


def test_skill_questions_is_immutable_tuple_of_mappings():
    """MappingProxyType is closed-form: any mutation must raise TypeError."""
    from src.skill_schema.prompts import SKILL_QUESTIONS
    assert isinstance(SKILL_QUESTIONS, tuple)
    with pytest.raises(TypeError):
        SKILL_QUESTIONS[0]["min_length"] = 999_999


def test_skill_questions_have_no_devkit_substring():
    """Skill schema metadata must not reference the forbidden token."""
    from src.skill_schema.prompts import SKILL_QUESTIONS
    for q in SKILL_QUESTIONS:
        for field in ("id", "prompt", "validation_hint"):
            assert "dev-kit" not in q[field], \
                f"skill question {q['id']!r} field {field!r} contains forbidden token"
