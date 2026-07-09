"""Schema package: canonical 5 questions + interview state runtime."""
from .questions import QUESTIONS, canonical_ids, get_question
from .state import InterviewState, SchemaError, ValidationError

__all__ = [
    "QUESTIONS",
    "canonical_ids",
    "get_question",
    "InterviewState",
    "SchemaError",
    "ValidationError",
]
