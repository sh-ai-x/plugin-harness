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