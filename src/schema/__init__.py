"""Schema SSOT package: 5-question interview schema + state machine."""

from src.schema.questions import QUESTIONS
from src.schema.state import InterviewState, SchemaError

__all__ = ["QUESTIONS", "InterviewState", "SchemaError"]