"""Schema package: canonical 5-question interview schema + InterviewState runtime.

PR #21 round 5: drop QUESTIONS from the public API; it is a
mutable singleton. Callers should use canonical_ids() to enumerate
or get_question(qid) to fetch by id. MappingProxyType freezes the
list at the package boundary so callers can't append/remove questions
through `src.schema.QUESTIONS.append(...)` and corrupt the canonical
schema.

PR #21 round 7: collapsed the previous duplicate __all__ blocks into
a single declaration after the .state import.
"""
from .questions import QUESTIONS as _QUESTIONS  # noqa: F401  (re-exported as tuple)
from .questions import canonical_ids, get_question  # noqa: F401  (public API)
from .state import InterviewState, SchemaError, ValidationError  # noqa: F401  (public API)

QUESTIONS: tuple = tuple(_QUESTIONS)

__all__ = [
    "QUESTIONS",
    "canonical_ids",
    "get_question",
    "InterviewState",
    "SchemaError",
    "ValidationError",
]
