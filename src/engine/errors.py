"""Shared engine error types + cross-module contracts.

PR #22 review (🟠 major #4): Mode modules previously imported
UserAbortError and InterviewIncompleteError directly from runner.py,
creating a circular-import hazard and coupling the modes to the
orchestrator. Promote both to a shared module so the modes can be
imported standalone (e.g. for unit tests of just one mode).

PR #22 round 12 (🟠 major): ToolSurface Protocol also moved here from
runner.py so that `modes/ai_research.py` can reference the surface
contract without depending on the orchestrator. The Protocol lives in
errors.py because both the modes and the runner need it; placing it in
either one creates a one-way import that the other direction has to
work around. errors.py is the dependency root for both.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = [
    "UserAbortError",
    "InterviewIncompleteError",
    "ToolSurface",
]


class UserAbortError(RuntimeError):
    """User aborted the interview (Ctrl-C, EOF on stdin, etc.).

    The CLI translates this to exit code 3.
    """


class InterviewIncompleteError(RuntimeError):
    """Interview cannot proceed because state is not complete.

    The CLI translates this to exit code 4.
    """


@runtime_checkable
class ToolSurface(Protocol):
    """Optional tool surface that ai-research mode invokes to draft each answer.

    Keyword-only signature: callers (the runner) and fakes (the tests)
    must agree. Returns the answer as a string. Real Claude Code / Codex
    runtimes pass in a richer surface; the in-process DefaultToolSurface
    is the offline fallback.
    """

    def draft_answer(self, *, question: dict, idea: str) -> str: ...
