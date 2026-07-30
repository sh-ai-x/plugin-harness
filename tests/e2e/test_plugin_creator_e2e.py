"""E2E smoke test for plugin_create.

Runs the full pipeline: emit + validate + adapter install.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def completed_state():
    from src.schema.state import InterviewState
    s = InterviewState()
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
    """plugin-creator installs into both CC and Codex cleanly."""
    from src.adapter.cc import register_cc_skill
    from src.adapter.codex import register_codex_skill
    register_cc_skill("plugin-creator", tmp_path)
    register_codex_skill("plugin-creator", tmp_path)

    assert (tmp_path / ".claude" / "skills" / "plugin-creator" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / "plugin-creator" / "SKILL.md").exists()


def test_e2e_cli_help_lists_output_dir_flag():
    """`python -m src.engine.cli new --help` advertises --output-dir/--skill-slug."""
    result = subprocess.run(
        [sys.executable, "-m", "src.engine.cli", "new", "x", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert "--output-dir" in result.stdout
    assert "--skill-slug" in result.stdout
