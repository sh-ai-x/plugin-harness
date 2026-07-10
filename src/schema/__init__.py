"""Schema package: canonical 5-question interview schema + InterviewState runtime.

Public API:
  - `canonical_ids()` — read-only sequence of question ids in canonical order
  - `get_question(qid)` — fetch a question dict by id
  - `InterviewState` — runtime carrier with cursor + answers + validation
  - `SchemaError`, `ValidationError` — typed exceptions
  - `QUESTIONS` — frozen tuple of MappingProxyType entries (deep-immutable)

PR #21 round 5: deep-freeze the inner question dicts so callers
cannot mutate QUESTIONS[i][...] to disable the round-3 DoS caps.
PR #21 round 7: collapsed duplicate __all__ blocks into a single
declaration after the .state import.
PR #21 round 8: QUESTIONS is now a tuple at the source (questions.py)
so the import-time _CANONICAL_IDS / _QUESTION_BY_ID caches cannot
desync from QUESTIONS at runtime.
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
