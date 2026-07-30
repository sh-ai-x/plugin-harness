"""src.skill_schema — vendored skill frontmatter validation.

Public surface:
    from src.skill_schema.loader import load_spec
    from src.skill_schema.validator import validate_skill_md, ValidationReport
"""
from src.skill_schema.loader import load_spec
from src.skill_schema.validator import ValidationReport, validate_skill_md

__all__ = [
    "load_spec",
    "validate_skill_md",
    "ValidationReport",
]
