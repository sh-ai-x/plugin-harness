"""Runner tests: shared interview loop drives both modes to a complete InterviewState."""
from __future__ import annotations

from typing import Any

import pytest

from src.engine.runner import (
    InterviewIncompleteError,
    UserAbortError,
    run_interview,
)
from src.schema.questions import QUESTIONS
from src.schema.state import InterviewState


# ---------- helpers ----------


def _valid(i: int) -> str:
    return f"answer-{i}-with-at-least-twenty-chars"


def _stdout_capture() -> list:
    return []


def _stdout_writer(sink: list):
    def _w(line: str) -> None:
        sink.append(line)
    return _w


def _stdin_scripted(lines: list):
    """A stdin reader that returns the next line from `lines` on each call.

    If `lines` is exhausted, raises UserAbortError to mirror real EOF/Ctrl-D.
    """
    idx = {"i": 0}

    def _r(_prompt: str) -> str:
        if idx["i"] >= len(lines):
            raise UserAbortError("stdin closed (no more answers)")
        out = lines[idx["i"]]
        idx["i"] += 1
        return out
    return _r


class _FakeToolSurface:
    """Records calls; returns canned answers in canonical order."""

    def __init__(self, answers: list[str] | None = None, fail_on: str | None = None):
        self.answers = answers or [_valid(i) for i in range(1, 6)]
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.fail_on = fail_on
        self.idx = 0

    def web_search(self, **kwargs):
        self.calls.append(("web_search", kwargs))
        if self.fail_on and self.calls.__len__() == 1 and self.fail_on == "web_search":
            raise RuntimeError("tool failed")
        return "search-result-stub"

    def web_fetch(self, **kwargs):
        self.calls.append(("web_fetch", kwargs))
        if self.fail_on and self.fail_on == "web_fetch":
            raise RuntimeError("tool failed")
        return "fetch-result-stub"

    def draft_answer(self, question: dict[str, Any], idea: str) -> str:
        self.calls.append(("draft_answer", {"question": question, "idea": idea}))
        if self.fail_on and self.fail_on == "draft_answer":
            raise RuntimeError("tool failed")
        if self.idx >= len(self.answers):
            raise RuntimeError("FakeToolSurface exhausted")
        out = self.answers[self.idx]
        self.idx += 1
        return out


# ---------- mode A (user-driven) ----------


def test_mode_user_driven_advances_through_all_five():
    state = InterviewState()
    sink = _stdout_capture()
    reader = _stdin_scripted([_valid(i) for i in range(1, 6)])

    result = run_interview(
        state,
        mode="user",
        idea="test idea",
        stdin_reader=reader,
        stdout_writer=_stdout_writer(sink),
    )

    assert result is state
    assert result.is_complete() is True
    assert len(result.answers) == 5
    for i, q in enumerate(QUESTIONS, start=1):
        assert result.answers[q["id"]] == _valid(i)


def test_mode_user_driven_writes_prompt_to_stdout():
    state = InterviewState()
    sink = _stdout_capture()
    reader = _stdin_scripted([_valid(i) for i in range(1, 6)])

    run_interview(
        state,
        mode="user",
        idea="test",
        stdin_reader=reader,
        stdout_writer=_stdout_writer(sink),
    )

    # 5 questions → 5 prompts.
    assert len(sink) == 5
    # Each prompt references the question prompt text.
    for q in QUESTIONS:
        assert any(q["prompt"] in line for line in sink), f"no prompt for {q['id']!r}"


def test_mode_user_driven_raises_user_abort_when_stdin_closes():
    state = InterviewState()
    reader = _stdin_scripted([])  # EOF on first call

    with pytest.raises(UserAbortError):
        run_interview(
            state,
            mode="user",
            idea="test",
            stdin_reader=reader,
            stdout_writer=_stdout_writer(_stdout_capture()),
        )


def test_mode_user_driven_raises_incomplete_on_empty_input():
    state = InterviewState()
    reader = _stdin_scripted(["", _valid(2), _valid(3), _valid(4), _valid(5)])

    with pytest.raises(InterviewIncompleteError):
        run_interview(
            state,
            mode="user",
            idea="test",
            stdin_reader=reader,
            stdout_writer=_stdout_writer(_stdout_capture()),
        )


def test_mode_user_driven_raises_incomplete_on_too_short_input():
    state = InterviewState()
    reader = _stdin_scripted(["too short", _valid(2), _valid(3), _valid(4), _valid(5)])

    with pytest.raises(InterviewIncompleteError):
        run_interview(
            state,
            mode="user",
            idea="test",
            stdin_reader=reader,
            stdout_writer=_stdout_writer(_stdout_capture()),
        )


def test_mode_user_driven_does_not_invoke_any_tool_surface():
    """Mode A is pure stdin/stdout — the tool surface must not be touched."""
    state = InterviewState()
    tool = _FakeToolSurface()

    run_interview(
        state,
        mode="user",
        idea="test",
        stdin_reader=_stdin_scripted([_valid(i) for i in range(1, 6)]),
        stdout_writer=_stdout_writer(_stdout_capture()),
        tool_surface=tool,
    )

    assert tool.calls == []


# ---------- mode B (AI-research) ----------


def test_mode_ai_research_advances_through_all_five():
    state = InterviewState()
    tool = _FakeToolSurface()

    result = run_interview(
        state,
        mode="ai-research",
        idea="build a thing",
        tool_surface=tool,
        stdout_writer=_stdout_writer(_stdout_capture()),
    )

    assert result.is_complete() is True
    for i, q in enumerate(QUESTIONS, start=1):
        assert result.answers[q["id"]] == _valid(i)


def test_mode_ai_research_uses_injected_tool_surface():
    state = InterviewState()
    tool = _FakeToolSurface()

    run_interview(
        state,
        mode="ai-research",
        idea="an idea",
        tool_surface=tool,
        stdout_writer=_stdout_writer(_stdout_capture()),
    )

    assert len(tool.calls) >= 5
    # Each draft_answer call must reference the question being answered.
    draft_calls = [c for c in tool.calls if c[0] == "draft_answer"]
    assert len(draft_calls) == 5
    seen_ids = [c[1]["question"]["id"] for c in draft_calls]
    assert seen_ids == [q["id"] for q in QUESTIONS]


def test_mode_ai_research_propagates_idea_to_tool():
    state = InterviewState()
    tool = _FakeToolSurface()

    run_interview(
        state,
        mode="ai-research",
        idea="my one-line idea",
        tool_surface=tool,
        stdout_writer=_stdout_writer(_stdout_capture()),
    )

    draft_calls = [c for c in tool.calls if c[0] == "draft_answer"]
    ideas = {c[1]["idea"] for c in draft_calls}
    assert ideas == {"my one-line idea"}


def test_mode_ai_research_raises_incomplete_on_short_answer():
    state = InterviewState()
    tool = _FakeToolSurface(answers=["too short", _valid(2), _valid(3), _valid(4), _valid(5)])

    with pytest.raises(InterviewIncompleteError):
        run_interview(
            state,
            mode="ai-research",
            idea="idea",
            tool_surface=tool,
            stdout_writer=_stdout_writer(_stdout_capture()),
        )


def test_mode_ai_research_does_not_read_stdin():
    """Mode B is tool-driven — stdin must not be invoked."""
    state = InterviewState()
    tool = _FakeToolSurface()

    def _should_not_be_called(_prompt: str) -> str:
        raise AssertionError("mode B must not read stdin")

    run_interview(
        state,
        mode="ai-research",
        idea="idea",
        tool_surface=tool,
        stdout_writer=_stdout_writer(_stdout_capture()),
        stdin_reader=_should_not_be_called,
    )


# ---------- shared loop invariants ----------


def test_runner_returns_state_with_all_five_answers_when_complete():
    state = InterviewState()
    tool = _FakeToolSurface()
    result = run_interview(
        state,
        mode="ai-research",
        idea="idea",
        tool_surface=tool,
        stdout_writer=_stdout_writer(_stdout_capture()),
    )
    assert sorted(result.answers.keys()) == sorted([q["id"] for q in QUESTIONS])


def test_runner_mutates_input_state_in_place():
    state = InterviewState()
    tool = _FakeToolSurface()
    result = run_interview(
        state,
        mode="ai-research",
        idea="idea",
        tool_surface=tool,
        stdout_writer=_stdout_writer(_stdout_capture()),
    )
    assert result is state
    assert state.is_complete() is True


def test_runner_rejects_unknown_mode():
    state = InterviewState()
    with pytest.raises(ValueError):
        run_interview(
            state,
            mode="bogus",
            idea="idea",
            tool_surface=_FakeToolSurface(),
            stdout_writer=_stdout_writer(_stdout_capture()),
        )

# ---------- PR #22 review regression: KeyboardInterrupt parity ----------
def test_mode_ai_research_keyboardinterrupt_translates_to_user_abort():
    """PR #22 review (🟠 major A10-006): ai-research branch was leaking
    KeyboardInterrupt as traceback + exit 1, inconsistent with user-mode's
    UserAbortError + exit 3. Verify the translator site lives in runner.
    """
    from src.engine.runner import run_interview, UserAbortError

    class _KbIntToolSurface:
        def draft_answer(self, *, question: dict, idea: str) -> str:
            raise KeyboardInterrupt("Ctrl-C")

    state = InterviewState()
    with pytest.raises(UserAbortError):
        run_interview(
            state,
            mode="ai-research",
            idea="some idea",
            tool_surface=_KbIntToolSurface(),
            stdout_writer=None,
            stdin_reader=None,
        )
    assert state.answers == {}, "no answers should be recorded on Ctrl-C"


# ---------- PR #22 round 8 regression ----------
def test_ai_draft_preserves_user_abort_through_tool_surface():
    """🟠 major: _ai_draft now re-raises UserAbortError from the tool surface
    so the CLI exits 3 instead of swallowing it as InterviewIncompleteError (exit 4).
    """
    from src.engine.runner import run_interview, UserAbortError, InterviewIncompleteError

    class _AbortToolSurface:
        def draft_answer(self, *, question: dict, idea: str) -> str:
            raise UserAbortError("tool surface aborted")

    state = InterviewState()
    with pytest.raises(UserAbortError):
        run_interview(
            state,
            mode="ai-research",
            idea="x",
            tool_surface=_AbortToolSurface(),
            stdout_writer=None,
            stdin_reader=None,
        )


def test_ai_draft_surfaces_only_type_name_for_unexpected_errors():
    """🟠 major: tool-surface errors that aren't UserAbortError/KeyboardInterrupt
    become InterviewIncompleteError with `type(exc).__name__`, not the full
    str(exc) (which can leak LLM-prompt content or auth headers).
    """
    from src.engine.runner import run_interview, InterviewIncompleteError

    class _BoomToolSurface:
        def draft_answer(self, *, question: dict, idea: str) -> str:
            raise RuntimeError("leaked-secret-prompt-content")

    state = InterviewState()
    with pytest.raises(InterviewIncompleteError) as exc_info:
        run_interview(
            state,
            mode="ai-research",
            idea="x",
            tool_surface=_BoomToolSurface(),
            stdout_writer=None,
            stdin_reader=None,
        )
    # PR #22 round 11 (🟠 major): the per-mode dispatchable handler
    # wraps the surface error and surfaces only type(exc).__name__
    # in the message — the original RuntimeError is preserved via
    # __cause__ for any future logging.
    assert "leaked-secret-prompt-content" not in str(exc_info.value)
    assert "RuntimeError" in str(exc_info.value)
    cause = exc_info.value.__cause__
    assert cause is not None
    assert isinstance(cause, RuntimeError)


# ---------- PR #22 round 9 regression: data-driven mode dispatch ----------
def test_mode_dispatch_registers_both_modes():
    """🟠 major: MODE_DISPATCH must include both 'user' and 'ai-research' after
    the mode modules have been imported. cli.py and runner.py look up the
    setup callable by name; a missing entry would silently route to the
    wrong branch."""
    from src.engine.modes import MODE_DISPATCH, MODES
    for name in MODES:
        assert name in MODE_DISPATCH, f"mode {name!r} not registered"


def test_mode_dispatch_unknown_name_raises():
    """🟠 major: lookup of an unknown mode raises KeyError so the CLI layer
    can surface a clear error rather than silently routing to the wrong branch."""
    from src.engine.modes import dispatch_for
    with pytest.raises(KeyError):
        dispatch_for("not-a-real-mode")


def test_run_interview_caps_idea_length():
    """🟡 minor: run_interview rejects `idea` longer than MAX_IDEA_LEN so
    library callers that bypass the CLI cap cannot drive unbounded
    f-string allocation through DefaultToolSurface."""
    from src.engine.runner import run_interview, InterviewIncompleteError, MAX_IDEA_LEN
    state = InterviewState()
    with pytest.raises(InterviewIncompleteError, match="idea parameter exceeds"):
        run_interview(
            state,
            mode="user",
            idea="x" * (MAX_IDEA_LEN + 1),
            stdin_reader=lambda prompt: "valid answer " * 5,
            stdout_writer=None,
        )


def test_default_tool_surface_clamps_to_max_length():
    """🟠 major (round 10): DefaultToolSurface.draft_answer previously produced
    strings over per-question max_length; the validator then raised
    ValidationError and the CLI exited 4 with a confusing message. Now
    hard-clamps to max_length.
    """
    from src.engine.modes.ai_research import DefaultToolSurface
    from src.schema.questions import QUESTIONS

    surface = DefaultToolSurface()
    long_idea = "x" * 2000  # at the per-question max
    for q in QUESTIONS:
        out = surface.draft_answer(question=q, idea=long_idea)
        assert len(out) <= q["max_length"], (
            f"DefaultToolSurface output {len(out)} > max_length {q['max_length']}"
        )


def test_run_interview_rejects_missing_stdin_reader_for_user_mode():
    """PR #22 round 12: missing stdin_reader for 'user' mode now raises ValueError
    BEFORE the first prompt is emitted, mapping to exit 2 (programming
    error) rather than mid-interview UserAbortError → exit 3.
    """
    from src.engine.runner import run_interview, InterviewState
    state = InterviewState()
    with pytest.raises(ValueError, match="'user' mode requires stdin_reader"):
        run_interview(state, mode="user", idea="x",
                     stdin_reader=None, stdout_writer=None)


def test_run_interview_rejects_missing_tool_surface_for_ai_research_mode():
    """PR #22 round 12: same for ai-research."""
    from src.engine.runner import run_interview, InterviewState
    state = InterviewState()
    with pytest.raises(ValueError, match="'ai-research' mode requires tool_surface"):
        run_interview(state, mode="ai-research", idea="x",
                     stdin_reader=None, stdout_writer=None,
                     tool_surface=None)
