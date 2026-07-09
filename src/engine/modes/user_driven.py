"""Mode A — user-driven: prompts the user, reads one line from stdin per question.

This module is intentionally minimal: it does not call out to network, filesystem,
or any external tool. The runner orchestrates validation; this handler returns the
raw line (including empty strings) so the runner can emit a typed error.
"""
from __future__ import annotations

import sys
from typing import Callable, Optional

from src.engine.errors import UserAbortError


def default_stdin_reader(prompt: str) -> str:
    """Read one line from real stdin, raising UserAbortError on EOF / Ctrl-D / Ctrl-C.

    The runner already writes the prompt via stdout_writer; we read with an
    empty prompt to avoid double-echoing.
    """
    try:
        line = input("")
    except EOFError as exc:
        raise UserAbortError("stdin closed (EOF / Ctrl-D)") from exc
    except KeyboardInterrupt as exc:
        raise UserAbortError("interrupted by user (Ctrl-C)") from exc
    return line


def default_stdout_writer(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def make_reader(reader: Optional[Callable[[str], str]]) -> Callable[[str], str]:
    return reader if reader is not None else default_stdin_reader


def make_writer(writer: Optional[Callable[[str], None]]) -> Callable[[str], None]:
    return writer if writer is not None else default_stdout_writer

# PR #22 round 9: register this mode's setup with the dispatch table.
from src.engine.modes import register_mode
def _setup_user_mode(make_reader, make_writer, _make_tool_surface):
    return make_reader(None), make_writer(None), None
register_mode("user", _setup_user_mode)
