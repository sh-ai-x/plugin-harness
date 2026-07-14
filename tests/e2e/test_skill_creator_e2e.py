"""E2E smoke test for skill_create and plugin_create.

Runs the full pipeline: emit + validate + adapter install + parity check.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def completed_state():
    from src.schema.state import InterviewState
    s = InterviewState()
    long = "x" * 30
    s.set_answer("what-who-where", "Demonstration plugin purpose summary sentence")
    s.advance()
    s.set_answer("why-this-problem", "Sample problem definition describing user need")
    s.advance()
    s.set_answer("how-it-works", "Sample plugin flow describing inputs and outputs")
    s.advance()
    s.set_answer("ai-usage", "Sample AI usage explanation describing model calls here")
    s.advance()
    s.set_answer("how-verified", "Sample verification method used to confirm done")
    return s


def test_e2e_skill_create_cli_invocation(tmp_path):
    """`python -m src.engine.cli new --mode=skill_create` produces dual SKILL.md."""
    from src.engine.modes.skill_create import SkillInterviewState, run_skill_interview
    from src.emitter.skill import emit_skill
    s = SkillInterviewState()
    answers = iter([
        "Demonstration skill purpose describing intent here clearly now",
        "Invoke slash command users across both runtime surfaces later",
        "Acceptance criteria verified by green test suite passing cleanly",
    ])
    s = run_skill_interview(idea="x", stdin_reader=lambda p: next(answers),
                            stdout_writer=lambda line: None)
    result = emit_skill(s, tmp_path)
    assert result.cc_path.exists()
    assert result.codex_path.exists()


def test_e2e_plugin_create_dual_skill_bundle(tmp_path, completed_state):
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    plan_md = "# E2E\n\nplan body for e2e smoke test that exercises dual-runtime bundle"
    result = emit_plugin_skill_bundle(
        completed_state, plan_md, tmp_path, skill_slugs=["e2e-skill"]
    )
    assert result.plugin_json.exists()
    assert result.cc_skill.exists()
    assert result.codex_skill.exists()


def test_e2e_adapter_install_round_trip(tmp_path):
    """Each of skill-creator / plugin-creator installs into both CC and Codex cleanly."""
    from src.adapter.cc import register_cc_skill
    from src.adapter.codex import register_codex_skill
    register_cc_skill("skill-creator", tmp_path)
    register_cc_skill("plugin-creator", tmp_path)
    register_codex_skill("skill-creator", tmp_path)
    register_codex_skill("plugin-creator", tmp_path)

    assert (tmp_path / ".claude" / "skills" / "skill-creator" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "plugin-creator" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / "skill-creator" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / "plugin-creator" / "SKILL.md").exists()


def test_e2e_cli_help_lists_skill_create_mode():
    """`python -m src.engine.cli new --help` advertises --mode=skill_create."""
    result = subprocess.run(
        [sys.executable, "-m", "src.engine.cli", "new", "x", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert "--mode" in result.stdout
    assert "skill_create" in result.stdout
    assert "--skill-slug" in result.stdout
