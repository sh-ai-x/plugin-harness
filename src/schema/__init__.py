"""Schema package: canonical 5 questions + interview state runtime."""
# PR #21 round 5: drop QUESTIONS from the public API; it is a
# mutable singleton. Callers should use canonical_ids() to enumerate
# or get_question(qid) to fetch by id. MappingProxyType freezes the
# list at the package boundary so callers can't append/remove questions
# through `src.schema.QUESTIONS.append(...)` and corrupt the canonical
# schema.
# PR #21 round 5: the underlying QUESTIONS tuple from .questions is
# private-by-convention; we re-export it as a tuple here so consumers
# get an immutable view (tuples don't support append/extend/etc.). The
# module-level QUESTIONS in .questions remains mutable; the package
# boundary converts it to a tuple so callers can't corrupt the
# canonical schema through `src.schema.QUESTIONS.append(...)`.
from .questions import QUESTIONS as _QUESTIONS  # noqa: F401
from .questions import canonical_ids, get_question  # noqa: F401

QUESTIONS: tuple = tuple(_QUESTIONS)

