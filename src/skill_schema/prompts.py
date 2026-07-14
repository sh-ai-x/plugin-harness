"""skill_create prompts — 3-question interview schema.

Independent from `src/schema/questions.py` (0-mvp's 5 questions). The
phase1 non-goal 1 forbids modifying the 0-mvp question order; this
module is a SEPARATE schema surface for the skill-creation sub-mode.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

DEFAULT_MAX_LENGTH = 2000


def _freeze(q: dict[str, Any]) -> MappingProxyType:
    """Immutable question dict (closed-form, prevents downstream mutation)."""
    return MappingProxyType(q)


# 3 questions for skill_create. Order and wording are part of the
# skill_create sub-mode contract. Reordering is a product change.
SKILL_QUESTIONS: tuple[MappingProxyType, ...] = (
    _freeze({
        "id": "purpose",
        "prompt": "What does this skill do? (purpose, ~30 chars min)",
        "answer_type": "text",
        "choices": [],
        "min_length": 30,
        "max_length": DEFAULT_MAX_LENGTH,
        "validation_hint": "describe what the skill does, who invokes it, and why",
    }),
    _freeze({
        "id": "examples",
        "prompt": "Give 1-2 concrete usage examples (a sentence or two each).",
        "answer_type": "text",
        "choices": [],
        "min_length": 30,
        "max_length": DEFAULT_MAX_LENGTH,
        "validation_hint": "show how a user invokes the skill and what they get back",
    }),
    _freeze({
        "id": "success-criteria",
        "prompt": "How will you know the skill works? (acceptance criteria)",
        "answer_type": "text",
        "choices": [],
        "min_length": 30,
        "max_length": DEFAULT_MAX_LENGTH,
        "validation_hint": "what does 'done' look like for this skill",
    }),
)

_CANONICAL_IDS: tuple[str, ...] = tuple(q["id"] for q in SKILL_QUESTIONS)
_QUESTION_BY_ID: dict[str, dict[str, Any]] = {q["id"]: q for q in SKILL_QUESTIONS}


def get_skill_question(qid: str) -> dict[str, Any]:
    """Return the skill_create question dict for `qid`, or raise KeyError."""
    return _QUESTION_BY_ID[qid]


def skill_canonical_ids() -> tuple[str, ...]:
    """Return the canonical id sequence for skill_create (read-only)."""
    return _CANONICAL_IDS
