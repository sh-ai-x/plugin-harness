"""Shared interview loop. Dispatches each question to a mode-specific handler."""
from __future__ import annotations

from typing import Any, Callable, Optional

# PR #22 review (🟠 major): ToolSurface was previously `Any`, which
# discarded the contract. ai-research calls
# `tool_surface.draft_answer(question=question, idea=idea)` and the
# docstring + FakeToolSurface in tests must agree on the same
# keyword-only signature. Promote to a runtime.Protocol so callers
# can type-check without forcing a subclassing dependency.
# PR #22 round 12 (🟠 major): the Protocol now lives in
# src/engine/errors.py so modes can import it without depending on
# the orchestrator. Re-exported here for backward compatibility with
# any direct runner.ToolSurface importer.
from src.engine.errors import InterviewIncompleteError, ToolSurface  # noqa: F401

from src.schema.questions import QUESTIONS
from src.schema.state import InterviewState, SchemaError, ValidationError


StdinReader = Callable[[str], str]
StdoutWriter = Callable[[str], None]


# PR #22 round 8: UserAbortError and InterviewIncompleteError moved
# to src/engine/errors.py. Re-exported here for backward compatibility
# with cli.py and modes/*. The canonical home is src.engine.errors.
from src.engine.errors import InterviewIncompleteError, UserAbortError  # noqa: F401  # re-export
from src.engine.errors import ToolSurface  # noqa: F401  # re-export (canonical home)


# PR #22 round 8/9: cap on the `idea` parameter. CLI layer caps at
# MAX_IDEA_LENGTH = 2000 (its argparse type); run_interview is a
# defense-in-depth secondary check at the same threshold so library
# callers that bypass the CLI cannot drive unbounded f-string
# allocation through DefaultToolSurface.
MAX_IDEA_LEN = 2000


def run_interview(
    state: InterviewState,
    mode: str,
    *,
    idea: str = "",
    stdin_reader: Optional[StdinReader] = None,
    stdout_writer: Optional[StdoutWriter] = None,
    tool_surface: Optional[ToolSurface] = None,
    questions: Optional[tuple] = None,
) -> InterviewState:
    """Drive an interview against `state`, returning it when complete.

    The 0-mvp behavior (5 questions, hardcoded) is the default. Pass
    `questions=...` to override the question list — used by the
    `skill_create` sub-mode (3 questions). `state` is duck-typed:
    any object with `set_answer(qid, raw)` and `advance()` works.

    Mode dispatch:
        - "user": reads one line per question via stdin_reader; writes prompt via stdout_writer.
        - "ai-research": asks tool_surface.draft_answer(question, idea) for each question.
        - "skill_create": registered for registry completeness; cli.py dispatches
                          directly to run_skill_interview (no per-question dispatch needed).

    Either mode raises:
        - ValueError for an unknown mode (programming error, not user input).
        - UserAbortError when mode="user" and stdin closes early (propagated from the reader).
        - InterviewIncompleteError when an answer is missing/invalid before completion.
    """
    # PR #22 round 8/9: defense-in-depth cap on the `idea` parameter.
    # CLI layer also caps at MAX_IDEA_LENGTH (argparse type=); this
    # is the secondary check at the same threshold for library
    # callers that bypass the CLI.
    if len(idea) > MAX_IDEA_LEN:
        raise InterviewIncompleteError(
            f"idea parameter exceeds MAX_IDEA_LEN={MAX_IDEA_LEN} chars"
        )

    # PR #22 round 8 (major #3): mode list lifted into
    # src/engine/modes/__init__.py as the single source of truth.
    from src.engine.modes import MODES
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")

    # 1-skill-creator: allow callers (cli.py, library) to pass an alternate
    # question list. Defaults to the 0-mvp QUESTIONS so existing callers
    # are unaffected.
    q_list = questions if questions is not None else QUESTIONS

    # PR #22 round 12 (🟡 minor): validate per-mode dependencies BEFORE
    # any prompt is emitted. The per-question dispatch raises
    # UserAbortError → exit 3 if a dep is missing, but emitting the
    # first prompt and only then failing would be confusing. Use typed
    # ValueError → exit 2 (programming error, not user input).
    if mode == "user" and stdin_reader is None:
        raise ValueError("'user' mode requires stdin_reader")
    if mode == "ai-research" and tool_surface is None:
        raise ValueError("'ai-research' mode requires tool_surface")

    for question in q_list:
        _prompt(question, stdout_writer)

        # PR #22 round 11 (🟠 major): data-driven per-question dispatch
        # via MODE_DISPATCH. Each mode module self-registers a per-
        # question callable at import time; runner looks it up by name.
        from src.engine.modes import MODE_DISPATCH
        if mode not in MODE_DISPATCH:
            raise ValueError(
                f"mode {mode!r} is in MODES but not in MODE_DISPATCH; "
                "did its module's register_mode() call run?"
            )
        # PR #22 round 11 (🟠 major): per-mode handler may itself raise
        # InterviewIncompleteError (e.g. DefaultToolSurface in
        # ai_research.py wraps surface errors). Re-raise those as-is
        # rather than double-wrapping; otherwise the CLI message
        # would surface "InterviewIncompleteError" instead of the
        # actual surface-error type name.
        try:
            raw = MODE_DISPATCH[mode](question, idea, stdin_reader, tool_surface)
        except KeyboardInterrupt:
            raise UserAbortError("interrupted by user (Ctrl-C)")
        except UserAbortError:
            raise
        except InterviewIncompleteError:
            raise
        except Exception as exc:
            raise InterviewIncompleteError(
                f"tool-surface error while drafting {question['id']!r}: "
                f"{type(exc).__name__}"
            ) from exc

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
    except (UserAbortError, KeyboardInterrupt):
        # PR #22 round 8 (major #1): preserve user-abort semantics
        # through the tool-surface layer. Re-raise so the CLI exits 3
        # instead of swallowing it as InterviewIncompleteError (exit 4).
        raise
    except Exception as exc:
        # PR #22 round 8 (major #1): surface only type(exc).__name__
        # to the caller; full traceback belongs in logs.
        raise InterviewIncompleteError(
            f"tool-surface error while drafting {question['id']!r}: "
            f"{type(exc).__name__}"
        ) from exc