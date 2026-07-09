"""Shared interview loop. Dispatches each question to a mode-specific handler."""
from __future__ import annotations

from typing import Any, Callable, Optional
from typing import Protocol

# PR #22 review (🟠 major): ToolSurface was previously `Any`, which
# discarded the contract. ai-research calls
# `tool_surface.draft_answer(question=question, idea=idea)` and the
# docstring + FakeToolSurface in tests must agree on the same
# keyword-only signature. Promote to a runtime.Protocol so callers
# can type-check without forcing a subclassing dependency.
class ToolSurface(Protocol):
    def draft_answer(self, *, question: dict, idea: str) -> str:
        """Draft an answer to one interview question.

        Keyword-only signature: callers (the runner) and fakes (the
        tests) must agree. Returns the answer as a string.
        """

from src.schema.questions import QUESTIONS
from src.schema.state import InterviewState, SchemaError, ValidationError


StdinReader = Callable[[str], str]
StdoutWriter = Callable[[str], None]


class InterviewIncompleteError(RuntimeError):
    """Raised when the interview ends before all 5 answers were recorded.

    Covers: empty input, validation failure (too short), tool-surface failure
    on a non-final question, or any other interruption that left state partial.
    """


class UserAbortError(RuntimeError):
    """Raised when the user closed stdin / hit Ctrl-D / hit Ctrl-C."""


def run_interview(
    state: InterviewState,
    mode: str,
    *,
    idea: str = "",
    stdin_reader: Optional[StdinReader] = None,
    stdout_writer: Optional[StdoutWriter] = None,
    tool_surface: Optional[ToolSurface] = None,
) -> InterviewState:
    """Drive the 5-question interview against `state`, returning it when complete.

    Mode dispatch:
        - "user": reads one line per question via stdin_reader; writes prompt via stdout_writer.
        - "ai-research": asks tool_surface.draft_answer(question, idea) for each question.

    Either mode raises:
        - ValueError for an unknown mode (programming error, not user input).
        - UserAbortError when mode="user" and stdin closes early (propagated from the reader).
        - InterviewIncompleteError when an answer is missing/invalid before completion.
    """
    if mode not in ("user", "ai-research"):
        raise ValueError(f"unknown mode {mode!r}; expected 'user' or 'ai-research'")

    for question in QUESTIONS:
        _prompt(question, stdout_writer)

        if mode == "user":
            assert stdin_reader is not None, "user mode requires stdin_reader"
            try:
                raw = stdin_reader(question["prompt"])
            except UserAbortError:
                raise
            except KeyboardInterrupt:
                raise UserAbortError("interrupted by user (Ctrl-C)")
        else:
            assert tool_surface is not None, "ai-research mode requires tool_surface"
            try:
                raw = _ai_draft(tool_surface, question, idea)
            except KeyboardInterrupt:
                # PR #22 review (🟠 major A10-006): ai-research branch was
                # propagating KeyboardInterrupt as a traceback + exit 1,
                # inconsistent with user-mode's UserAbortError + exit 3.
                raise UserAbortError("interrupted by user (Ctrl-C)")

        _record(state, question, raw)

    return state


def _prompt(question: dict, writer: Optional[StdoutWriter]) -> None:
    if writer is None:
        return
    writer(question["prompt"])


def _record(state: InterviewState, question: dict, raw: str) -> None:
    """Apply validation, raise typed errors on failure, advance on success."""
    try:
        state.set_answer(question["id"], raw)
        state.advance()
    except SchemaError as exc:
        raise InterviewIncompleteError(
            f"schema error on {question['id']!r}: {exc}"
        ) from exc
    except ValidationError as exc:
        raise InterviewIncompleteError(
            f"invalid answer for {question['id']!r}: {exc}"
        ) from exc


def _ai_draft(tool_surface: ToolSurface, question: dict, idea: str) -> str:
    try:
        return tool_surface.draft_answer(question=question, idea=idea)
    except Exception as exc:
        raise InterviewIncompleteError(
            f"tool-surface error while drafting {question['id']!r}: {exc}"
        ) from exc