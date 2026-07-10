"""CLI tests: argparse, --mode flag, dispatch, exit codes."""
from __future__ import annotations

import io
import sys

import pytest

import src.engine.cli as cli_mod
from src.engine.cli import build_parser, main
from src.schema.state import InterviewState


VALID_INPUT_LINES = [
    "answer-one-with-at-least-twenty-chars",
    "answer-two-with-at-least-twenty-chars",
    "answer-three-with-at-least-twenty-chars",
    "answer-four-with-at-least-twenty-chars",
    "answer-five-with-at-least-twenty-chars",
]


# ---------- argparse ----------


def test_parser_requires_subcommand():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_new_subcommand_takes_idea():
    parser = build_parser()
    args = parser.parse_args(["new", "build a thing"])
    assert args.subcommand == "new"
    assert args.idea == "build a thing"


def test_parser_new_default_mode_is_user():
    parser = build_parser()
    args = parser.parse_args(["new", "idea"])
    assert args.mode == "user"


def test_parser_new_explicit_mode_user():
    parser = build_parser()
    args = parser.parse_args(["new", "idea", "--mode", "user"])
    assert args.mode == "user"


def test_parser_new_explicit_mode_ai_research():
    parser = build_parser()
    args = parser.parse_args(["new", "idea", "--mode", "ai-research"])
    assert args.mode == "ai-research"


def test_parser_new_rejects_unknown_mode():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["new", "idea", "--mode", "invalid"])


# ---------- dispatch + exit codes ----------


def _run_with_stdin(argv, stdin_text: str) -> int:
    """Invoke main(argv) with the given stdin_text and return the exit code."""
    saved_stdin = sys.stdin
    saved_argv = sys.argv
    sys.stdin = io.StringIO(stdin_text)
    sys.argv = ["prog"] + argv
    try:
        return main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    finally:
        sys.stdin = saved_stdin
        sys.argv = saved_argv


def test_cli_user_mode_exits_0_on_complete_stdin(capsys):
    code = _run_with_stdin(
        ["new", "test idea", "--mode", "user"],
        "\n".join(VALID_INPUT_LINES) + "\n",
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "complete" in captured.out


def test_cli_user_mode_exits_nonzero_on_empty_input(capsys):
    code = _run_with_stdin(
        ["new", "test idea", "--mode", "user"],
        "",
    )
    assert code != 0


def test_cli_user_mode_exits_nonzero_on_validation_failure(capsys):
    code = _run_with_stdin(
        ["new", "test idea", "--mode", "user"],
        "\n".join(["short"] + VALID_INPUT_LINES[1:]) + "\n",
    )
    assert code != 0


def test_cli_invalid_mode_exits_nonzero_with_error(capsys):
    code = _run_with_stdin(
        ["new", "test", "--mode", "invalid"],
        "",
    )
    assert code != 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "invalid choice" in combined


def test_cli_ai_research_mode_dispatches_to_ai_handler(monkeypatch, capsys):
    """ai-research mode routes through the AI handler with a tool surface."""
    state = InterviewState()

    def fake_run(state_arg, *, mode, **kwargs):
        assert mode == "ai-research"
        from src.schema.questions import QUESTIONS

        for q in QUESTIONS:
            state_arg.set_answer(q["id"], "x" * (q["min_length"] + 1))
            state_arg.advance()
        return state_arg

    monkeypatch.setattr(cli_mod, "run_interview", fake_run)

    code = _run_with_stdin(["new", "test idea", "--mode", "ai-research"], "")
    assert code == 0
    captured = capsys.readouterr()
    assert "complete" in captured.out


def test_cli_user_mode_dispatches_to_user_handler(monkeypatch, capsys):
    seen = {}

    def fake_run(state_arg, *, mode, **kwargs):
        seen["mode"] = mode
        seen["has_reader"] = kwargs.get("stdin_reader") is not None
        seen["has_writer"] = kwargs.get("stdout_writer") is not None
        from src.schema.questions import QUESTIONS

        for q in QUESTIONS:
            state_arg.set_answer(q["id"], "x" * (q["min_length"] + 1))
            state_arg.advance()
        return state_arg

    monkeypatch.setattr(cli_mod, "run_interview", fake_run)

    code = _run_with_stdin(
        ["new", "test idea", "--mode", "user"],
        "\n".join(VALID_INPUT_LINES) + "\n",
    )
    assert code == 0
    assert seen["mode"] == "user"
    assert seen["has_reader"] is True
    assert seen["has_writer"] is True


def test_cli_ai_research_mode_does_not_consume_stdin(monkeypatch, capsys):
    """ai-research must not block on stdin; we leave it empty and the run still completes."""
    seen = {}

    def fake_run(state_arg, *, mode, **kwargs):
        seen["reader"] = kwargs.get("stdin_reader")
        from src.schema.questions import QUESTIONS

        for q in QUESTIONS:
            state_arg.set_answer(q["id"], "x" * (q["min_length"] + 1))
            state_arg.advance()
        return state_arg

    monkeypatch.setattr(cli_mod, "run_interview", fake_run)

    code = _run_with_stdin(["new", "test idea", "--mode", "ai-research"], "")
    assert code == 0
    # ai-research mode should not pass a stdin reader
    assert seen["reader"] is None