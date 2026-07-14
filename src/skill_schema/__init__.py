"""src.skill_schema — vendored skill frontmatter validation + skill_create prompts.

Public surface:
    from src.skill_schema.loader import load_spec
    from src.skill_schema.validator import validate_skill_md, ValidationReport
    from src.skill_schema.prompts import SKILL_QUESTIONS, get_skill_question, skill_canonical_ids
"""
from src.skill_schema.loader import load_spec
from src.skill_schema.prompts import (
    SKILL_QUESTIONS,
    get_skill_question,
    skill_canonical_ids,
)
from src.skill_schema.validator import ValidationReport, validate_skill_md

__all__ = [
    "load_spec",
    "validate_skill_md",
    "ValidationReport",
    "SKILL_QUESTIONS",
    "get_skill_question",
    "skill_canonical_ids",
]
