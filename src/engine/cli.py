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


VALID_MODES = ("user", "ai-research")


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
        choices=VALID_MODES,
        default="user",
        help="Interview mode: 'user' (stdin) or 'ai-research' (tool surface).",
    )
    return parser


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

    if args.mode not in VALID_MODES:
        _print(f"invalid choice: {args.mode!r} (choose from {VALID_MODES})")
        return 2

    state = InterviewState()
    writer = make_writer(None)

    if args.mode == "user":
        reader = make_reader(None)
        tool_surface = None
    else:
        reader = None
        tool_surface = make_tool_surface(None)

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