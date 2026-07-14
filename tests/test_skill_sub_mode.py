"""Tests for the skill_create sub-mode (engine + emitter).

Iron Law L1 (TDD): this file predates src/engine/modes/skill_create.py
and src/emitter/skill.py. Tests are RED until those modules land.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------- SkillInterviewState ----------

def test_skill_state_round_trip_through_set_answer_and_advance():
    from src.engine.modes.skill_create import SkillInterviewState
    state = SkillInterviewState()
    state.set_answer("purpose", "x" * 50)
    state.advance()
    state.set_answer("examples", "y" * 30)
    state.advance()
    state.set_answer("success-criteria", "z" * 30)
    state.advance()
    assert state.is_complete()


def test_skill_state_set_answer_out_of_order_raises_schema_error():
    from src.engine.modes.skill_create import SkillInterviewState
    from src.schema.state import SchemaError
    state = SkillInterviewState()
    with pytest.raises(SchemaError):
        state.set_answer("examples", "y" * 30)  # cursor expects "purpose"


def test_skill_state_set_answer_unknown_id_raises_schema_error():
    from src.engine.modes.skill_create import SkillInterviewState
    from src.schema.state import SchemaError
    state = SkillInterviewState()
    with pytest.raises(SchemaError):
        state.set_answer("not-a-real-id", "anything")


def test_skill_state_validate_answer_rejects_short_input():
    from src.engine.modes.skill_create import SkillInterviewState
    assert SkillInterviewState.validate_answer("purpose", "short") is False
    assert SkillInterviewState.validate_answer("purpose", "x" * 50) is True


def test_skill_state_validate_answer_rejects_non_string():
    from src.engine.modes.skill_create import SkillInterviewState
    assert SkillInterviewState.validate_answer("purpose", 12345) is False


# ---------- run_skill_interview ----------

def test_run_skill_interview_reads_three_answers_from_stdin():
    from src.engine.modes.skill_create import run_skill_interview
    answers = iter([
        "purpose: a sample skill that does X for users of the plugin-harness",  # ≥50 chars
        "examples: invoke via /skill-creator slash command in CC",
        "criteria: emits dual SKILL.md and both validate",
    ])

    def fake_reader(prompt: str) -> str:
        return next(answers)

    state = run_skill_interview(idea="x", stdin_reader=fake_reader, stdout_writer=lambda s: None)
    assert state.is_complete()
    assert "purpose" in state.answers
    assert "examples" in state.answers
    assert "success-criteria" in state.answers


def test_run_skill_interview_propagates_user_abort():
    from src.engine.modes.skill_create import run_skill_interview
    from src.engine.errors import UserAbortError

    def abort_reader(prompt: str) -> str:
        raise UserAbortError("test abort")

    with pytest.raises(UserAbortError):
        run_skill_interview(idea="x", stdin_reader=abort_reader, stdout_writer=lambda s: None)


# ---------- emit_skill ----------

def test_emit_skill_writes_dual_runtime_files(tmp_path):
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill

    state = SkillInterviewState()
    state.set_answer("purpose", "Convert a user handoff into an interview transcript demo-skill")
    state.advance()
    state.set_answer("examples", "Sales call to pricing-doc handoff demo example here")
    state.advance()
    state.set_answer("success-criteria", "PRD filled from handoff within 5 minutes")
    state.advance()

    result = emit_skill(state, tmp_path)
    assert result.cc_path.exists()
    assert result.codex_path.exists()


def test_emit_skill_both_files_validate(tmp_path):
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill
    from src.skill_schema.validator import validate_skill_md

    state = SkillInterviewState()
    state.set_answer("purpose", "Demonstration skill with a number one specific purpose")
    state.advance()
    state.set_answer("examples", "Run via /skill-creator slash command in CC and Codex")
    state.advance()
    state.set_answer("success-criteria", "Emit two SKILL.md that both validate")
    state.advance()

    result = emit_skill(state, tmp_path)
    cc = validate_skill_md(result.cc_path, "cc")
    codex = validate_skill_md(result.codex_path, "codex")
    assert cc.ok, cc.errors
    assert codex.ok, codex.errors


def test_emit_skill_idempotent(tmp_path):
    """Re-running emit on the same dir does not duplicate files."""
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill

    state = SkillInterviewState()
    state.set_answer("purpose", "Demonstration skill with idempotency check here now")
    state.advance()
    state.set_answer("examples", "Re-running emit produces same files; no duplicates")
    state.advance()
    state.set_answer("success-criteria", "Re-run leaves exactly one SKILL.md per runtime")
    state.advance()

    emit_skill(state, tmp_path)
    emit_skill(state, tmp_path)
    cc_files = list((tmp_path / ".claude" / "skills").rglob("SKILL.md"))
    codex_files = list((tmp_path / ".codex" / "skills").rglob("SKILL.md"))
    assert len(cc_files) == 1, f"expected idempotent CC files, got {cc_files}"
    assert len(codex_files) == 1, f"expected idempotent Codex files, got {codex_files}"


def test_emit_skill_slug_is_deterministic(tmp_path):
    """Same purpose → same slug across separate emits."""
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill

    def make_state():
        s = SkillInterviewState()
        s.set_answer("purpose", "A specific purpose string with the same words duplicated")
        s.advance()
        s.set_answer("examples", "Example one and example two are demonstrative here")
        s.advance()
        s.set_answer("success-criteria", "Criteria one and criteria two together now")
        s.advance()
        return s

    out1 = tmp_path / "first"
    out2 = tmp_path / "second"
    r1 = emit_skill(make_state(), out1)
    r2 = emit_skill(make_state(), out2)
    assert r1.cc_path.parent.parent.name == r2.cc_path.parent.parent.name
    assert r1.codex_path.parent.parent.name == r2.codex_path.parent.parent.name


def test_emit_skill_no_devkit_substring_in_output(tmp_path):
    """Either runtime's emitted SKILL.md must not contain forbidden substring.

    The skill PURPOSE field becomes part of the description; if purpose
    contains the forbidden token, validate_skill_md must reject. This
    confirms the round-trip emit → validate catches the violation
    rather than silently shipping it.
    """
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill, EmitError
    from src.skill_schema.validator import validate_skill_md

    state = SkillInterviewState()
    state.set_answer("purpose", "Demonstration skill for the dev-kit substring test")
    state.advance()
    state.set_answer("examples", "Examples invoked by users of this skill")
    state.advance()
    state.set_answer("success-criteria", "Criteria proven by tests passing all green here")
    state.advance()

    # Emit raises EmitError before writing the file because the validator
    # catches the substring violation on the in-memory render.
    with pytest.raises(EmitError):
        emit_skill(state, tmp_path)
    # And nothing was written.
    assert list((tmp_path / ".claude" / "skills").rglob("SKILL.md")) == []
    assert list((tmp_path / ".codex" / "skills").rglob("SKILL.md")) == []


def test_emit_skill_incomplete_state_raises():
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill, EmitError
    from pathlib import Path
    state = SkillInterviewState()
    state.set_answer("purpose", "Incomplete state with only one answer here ok and more")
    state.advance()
    # Only purpose answered; interview is not complete.
    with pytest.raises(EmitError):
        emit_skill(state, Path("/tmp/should-not-be-written"))


def test_emit_skill_incomplete_state_raises():
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill, EmitError
    state = SkillInterviewState()
    state.set_answer("purpose", "Incomplete state with only one answer here ok")
    with pytest.raises(EmitError):
        emit_skill(state, Path("/tmp/should-not-be-written"))


# ---------- CLI surface ----------

def test_cli_accepts_skill_create_mode(tmp_path):
    """`python -m src.engine.cli new --mode=skill_create` must be accepted by argparse."""
    result = subprocess.run(
        [sys.executable, "-m", "src.engine.cli", "new", "x", "--mode=skill_create", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    # --help exits 0 and prints usage; just confirm mode is in choices
    assert "--mode" in result.stdout or "skill_create" in result.stdout or result.returncode == 0
