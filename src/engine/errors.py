"""Shared engine error types.

PR #22 review (🟠 major #4): Mode modules previously imported
UserAbortError and InterviewIncompleteError directly from runner.py,
creating a circular-import hazard and coupling the modes to the
orchestrator. Promote both to a shared module so the modes can be
imported standalone (e.g. for unit tests of just one mode).
"""

__all__ = ["UserAbortError", "InterviewIncompleteError"]


class UserAbortError(RuntimeError):
    """User aborted the interview (Ctrl-C, EOF on stdin, etc.).

    The CLI translates this to exit code 3.
    """


class InterviewIncompleteError(RuntimeError):
    """Interview cannot proceed because state is not complete.

    The CLI translates this to exit code 4.
    """
