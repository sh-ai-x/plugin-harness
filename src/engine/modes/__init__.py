"""Mode registry for the interview engine.

PR #22 review (🟠 major, round 8/9): the previous version of this module
exposed only a `MODES` tuple. cli.py and runner.py imported it but never
consulted it for dispatch — both still hardcoded if/else on the literal
mode name. A third mode added to MODES would silently route to the
wrong branch.

This module now provides both:
  - `MODES`: tuple of valid mode names (used by argparse `choices=`).
  - `MODE_DISPATCH`: dict[name, callable] used by runner.py and
    cli.py to look up the per-mode behavior, replacing the hardcoded
    if/else.

Each mode module self-registers at import time:

    # src/engine/modes/user_driven.py
    from src.engine.modes import register_mode
    def _setup_user_mode(make_reader, make_writer, _make_tool_surface):
        return make_reader(None), make_writer(None), None
    register_mode("user", _setup_user_mode)

The dispatch table is populated as a side effect of importing the
per-mode submodules. `MODES` and the per-mode imports are imported
in a single block at the bottom of this module so the symbol
`register_mode` is defined first.
"""

from __future__ import annotations

from typing import Callable

__all__ = ["MODES", "MODE_DISPATCH", "register_mode", "dispatch_for"]


_MODES: tuple[str, ...] = (
    "user",
    "ai-research",
)


# PR #22 round 11 (🟠 major): the registry now stores per-question
# callables, not setup tuples. The runner looks up the per-question
# callable by mode name; cli.py builds (reader, writer, surface)
# separately from the registry (see cli.py round 9 dispatch).
MODE_DISPATCH: dict[str, Callable] = {}


def register_mode(name: str, per_question: Callable) -> None:
    """Register a per-question callable for `name` in MODE_DISPATCH.

    Used by mode modules at import time. Re-registering an existing
    name overrides the prior entry; tests rely on that to swap in a
    fake surface for ai-research.
    """
    MODE_DISPATCH[name] = per_question


def dispatch_for(name: str) -> Callable:
    """Look up the per-question callable for `name`. Raises KeyError on miss."""
    return MODE_DISPATCH[name]


# Public read-only view of the dispatch table. A separate MODES tuple
# surfaces for argparse `choices=` and "invalid mode" error messages;
# it is the static "what modes exist" view, while MODES_DISPATCH is
# the dynamic "what's wired up" view (always a subset of MODES in
# practice).
MODES = _MODES



# Import the mode modules here so their register_mode() calls fire at
# package import time. Without this, MODE_DISPATCH would be empty until
# each mode module is explicitly imported (a regression risk for
# library callers that import src.engine.modes without first touching
# the per-mode submodules). Must come AFTER register_mode is defined
# above to avoid circular-import errors.
from src.engine.modes import user_driven  # noqa: E402, F401  (registers 'user')
from src.engine.modes import ai_research  # noqa: E402, F401  (registers 'ai-research')
