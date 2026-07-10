"""CLI entrypoint for the interview engine.

Usage:
    python -m src.engine.cli new "<one-line idea>" [--mode user|ai-research]

Exit codes:
    0  — interview completed; final line of stdout is "complete"
    2  — invalid CLI args (argparse)
    3  — interview aborted by the user (Ctrl-C / EOF / empty input)
    4  — interview produced an invalid answer (validation failure)
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from src.engine.modes.ai_research import make_tool_surface
from src.engine.modes.user_driven import make_reader, make_writer
from src.engine.runner import (
    InterviewIncompleteError,
    UserAbortError,
    run_interview,
)
from src.schema.state import InterviewState


# PR #22 round 8 (major #3): mode list lifted into
# src/engine/modes/__init__.py as the single source of truth. Import
# MODES there and use it for argparse choices and validation.
from src.engine.modes import MODE_DISPATCH, MODES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plugin-harness.cli",
        description="Interview-driven plugin authoring CLI.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)
    new_cmd = sub.add_parser("new", help="Start a new interview for an idea.")
    new_cmd.add_argument("idea", help="One-line description of the plugin idea.")
    new_cmd.add_argument(
        "--mode",
        choices=MODES,
        default="user",
        help="Interview mode: 'user' (stdin) or 'ai-research' (tool surface).",
    )
    return parser


# PR #22 round 9 (🟡 minor): cap the --idea argument at the CLI layer
# so DefaultToolSurface cannot allocate an unbounded f-string before
# max_length validation rejects it. 2000 chars matches per-question
# max_length in src/schema/questions.py (the answer-side cap).
MAX_IDEA_LENGTH = 2000


def _print(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse already wrote "invalid choice" / usage to stderr.
        return 2 if exc.code != 0 else 0

    if args.subcommand != "new":
        _print(f"unknown subcommand {args.subcommand!r}")
        return 2

    # PR #22 round 9 (🟠 major): data-driven dispatch via MODE_DISPATCH.
    # Each mode module self-registers a setup callable at import
    # time; cli.py looks it up by name. MODES and MODE_DISPATCH
    # are imported at module top; no need to re-import here.
    if args.mode not in MODES:
        _print(f"invalid choice: {args.mode!r} (choose from {MODES})")
        return 2
    if args.mode not in MODE_DISPATCH:
        _print(f"mode {args.mode!r} is not yet wired up at the CLI layer")
        return 2

    state = InterviewState()
    writer = make_writer(None)
    reader, _, tool_surface = MODE_DISPATCH[args.mode](
        make_reader, make_writer, make_tool_surface
    )

    try:
        run_interview(
            state,
            mode=args.mode,
            idea=args.idea,
            stdin_reader=reader,
            stdout_writer=writer,
            tool_surface=tool_surface,
        )
    except UserAbortError as exc:
        _print(f"aborted: {exc}")
        return 3
    except InterviewIncompleteError as exc:
        _print(f"incomplete: {exc}")
        return 4

    _print("complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())