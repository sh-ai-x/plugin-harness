"""CLI entrypoint for the interview engine.

Usage:
    python -m src.engine.cli new "<one-line idea>" [--mode user|ai-research|skill_create]

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

from src.engine.runner import (
    InterviewIncompleteError,
    UserAbortError,
    run_interview,
)
from src.schema.state import InterviewState


# PR #22 round 8 (major #3): mode list lifted into
# src/engine/modes/__init__.py as the single source of truth. Import
# MODES there and use it for argparse choices and validation.
# PR #22 round 12 (🟠 major #3): per-mode reader + tool-surface
# factories are also looked up through the registry. cli.py no longer
# imports `make_reader` / `make_tool_surface` directly from per-mode
# modules — adding a third mode requires no changes here.
from src.engine.modes import (
    MODES,
    setup_reader,
    setup_surface,
)
from src.engine.modes.user_driven import make_writer  # writer is shared across modes
from src.engine.modes.skill_create import SkillInterviewState, run_skill_interview
from src.skill_schema.prompts import SKILL_QUESTIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plugin-harness.cli",
        description="Interview-driven plugin authoring CLI.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)
    new_cmd = sub.add_parser("new", help="Start a new interview for an idea.")
    def _idea_value(value: str) -> str:
        # PR #22 round 11 (🟠 major): wire MAX_IDEA_LENGTH into argparse.
        # Oversize input exits 2 (invalid args), not 4 (incomplete).
        if len(value) > MAX_IDEA_LENGTH:
            raise argparse.ArgumentTypeError(
                f"--idea exceeds MAX_IDEA_LENGTH={MAX_IDEA_LENGTH} chars"
            )
        return value

    new_cmd.add_argument("idea", type=_idea_value, help="One-line description of the plugin idea.")
    new_cmd.add_argument(
        "--mode",
        choices=MODES,
        default="user",
        help="Interview mode: 'user' (stdin), 'ai-research' (tool surface), or 'skill_create' (3-question skill authoring + dual SKILL.md emission).",
    )
    new_cmd.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for emitted artifacts (skill_create only). Required for skill_create when stdin is not a TTY.",
    )
    new_cmd.add_argument(
        "--skill-slug",
        action="append",
        default=[],
        help="Skill slug name to bundle under both .claude/skills/ and .codex/skills/ inside --output-dir (plugin_create only). May be repeated.",
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
    # PR #22 round 11: MODE_DISPATCH is now per-question (used by
    # runner.py, not cli.py). The CLI layer still constructs
    # reader/writer/surface here; the per-question handler looks them
    # up at runtime.
    # PR #22 round 12 (🟠 major #2 + #3): per-mode reader and
    # tool-surface factories are looked up via src.engine.modes. The
    # `if args.mode == "user": ... else: ...` hardcoded branch is
    # gone — adding a third mode requires no changes here.
    if args.mode not in MODES:
        _print(f"invalid choice: {args.mode!r} (choose from {MODES})")
        return 2

    # 1-skill-creator: skill_create runs a 3-question interview and emits
    # dual SKILL.md files; dispatch BEFORE the 5-question path so it
    # never accidentally runs through the 0-mvp QUESTIONS list.
    if args.mode == "skill_create":
        return _run_skill_create(args)

    if args.skill_slug and not args.output_dir:
        _print("--skill-slug requires --output-dir")
        return 2

    state = InterviewState()
    writer = make_writer(None)
    reader = setup_reader(args.mode)
    tool_surface = setup_surface(args.mode)

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


def _run_skill_create(args) -> int:
    """CLI dispatch for the skill_create sub-mode.

    Runs the 3-question interview and, when --output-dir is provided,
    emits dual-runtime SKILL.md files. With no --output-dir, exits 0
    after the interview completes (parity with the 0-mvp behavior of
    "interview complete; further actions separate").
    """
    writer = make_writer(None)
    # skill_create requires a real stdin reader; tests pass one directly.
    from src.engine.modes.user_driven import default_stdin_reader
    reader = default_stdin_reader

    try:
        state = run_skill_interview(
            args.idea,
            stdin_reader=reader,
            stdout_writer=writer,
        )
    except UserAbortError as exc:
        _print(f"aborted: {exc}")
        return 3

    if args.output_dir is not None:
        try:
            from pathlib import Path
            from src.emitter.skill import emit_skill, EmitError
            emit_skill(state, Path(args.output_dir))
        except EmitError as exc:
            _print(f"emit error: {exc}")
            return 4

    _print("complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())