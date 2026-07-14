"""Tests for the plugin_create sub-mode + dual-skill-bundle emitter.

Iron Law L1 (TDD): this file predates src/emitter/plugin_skill_bundle.py.
Tests are RED until that module lands.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest


# ---------- emit_plugin_skill_bundle ----------

def _complete_state():
    """Build a completed 0-mvp InterviewState with all 5 answers."""
    from src.schema.state import InterviewState
    s = InterviewState()
    long = "x" * 30
    s.set_answer("what-who-where", long)
    s.advance()
    s.set_answer("why-this-problem", long)
    s.advance()
    s.set_answer("how-it-works", long)
    s.advance()
    s.set_answer("ai-usage", long)
    s.advance()
    s.set_answer("how-verified", long)
    return s


def test_emit_plugin_skill_bundle_writes_plugin_json_and_dual_skills(tmp_path):
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    state = _complete_state()
    plan_md = "# Demo Plugin\n\nSample plan body for testing purposes."

    result = emit_plugin_skill_bundle(
        state, plan_md, tmp_path, skill_slugs=["demo-skill"]
    )

    # Filesystem layout
    assert (tmp_path / "src" / ".codex-plugin" / "plugin.json").exists()
    assert (tmp_path / "src" / ".mcp.json").exists()
    assert (tmp_path / ".claude" / "skills" / "demo-skill" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / "demo-skill" / "SKILL.md").exists()

    # Result has all four paths
    assert result.plugin_json.exists()
    assert result.canonical_skill.exists()
    assert result.cc_skill.exists()
    assert result.codex_skill.exists()


def test_emit_plugin_skill_bundle_plugin_json_validates_against_vendored_schema(tmp_path):
    """plugin.json must round-trip against docs/codex-plugin.schema.json."""
    import jsonschema
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    state = _complete_state()
    plan_md = "# Demo Plugin\n\nSchema-roundtrip test plan body content here."
    result = emit_plugin_skill_bundle(
        state, plan_md, tmp_path, skill_slugs=["demo-skill"]
    )
    schema = json.loads(Path("docs/codex-plugin.schema.json").read_text())
    plugin = json.loads(result.plugin_json.read_text())
    jsonschema.validate(plugin, schema)
    assert plugin["version"] == "0.1.0"
    assert plugin["name"]


def test_emit_plugin_skill_bundle_dual_skills_validate(tmp_path):
    """Both emitted CC and Codex SKILL.md files must pass the step-0 validator."""
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    from src.skill_schema.validator import validate_skill_md
    state = _complete_state()
    plan_md = "# Demo Plugin\n\nTest plan for dual runtime skill validation."
    result = emit_plugin_skill_bundle(
        state, plan_md, tmp_path, skill_slugs=["demo-skill"]
    )
    cc = validate_skill_md(result.cc_skill, "cc")
    codex = validate_skill_md(result.codex_skill, "codex")
    assert cc.ok, cc.errors
    assert codex.ok, codex.errors


def test_emit_plugin_skill_bundle_idempotent(tmp_path):
    """Re-running emit overwrites in place; no duplicate files."""
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    state = _complete_state()
    plan_md = "# Demo Plugin\n\nIdempotency test plan body."
    emit_plugin_skill_bundle(state, plan_md, tmp_path, skill_slugs=["demo-skill"])
    emit_plugin_skill_bundle(state, plan_md, tmp_path, skill_slugs=["demo-skill"])
    cc_files = list((tmp_path / ".claude" / "skills").rglob("SKILL.md"))
    codex_files = list((tmp_path / ".codex" / "skills").rglob("SKILL.md"))
    assert len(cc_files) == 1
    assert len(codex_files) == 1


def test_emit_plugin_skill_bundle_5q_reuses_0mvp_schema(tmp_path):
    """plugin_create must NOT duplicate QUESTIONS; it uses the 0-mvp schema."""
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    from src.schema.questions import QUESTIONS as PLUGIN_QUESTIONS
    from src.schema.state import InterviewState
    from src.engine.modes.skill_create import run_skill_interview, SkillInterviewState

    state = _complete_state()  # 0-mvp 5-question interview
    plan_md = "# Demo Plugin\n\nTest plan body content here."
    emit_plugin_skill_bundle(state, plan_md, tmp_path, skill_slugs=["demo-skill"])
    # Sanity: not the same schema as skill_create's 3-question schema.
    assert PLUGIN_QUESTIONS != __import__("src.skill_schema.prompts", fromlist=["SKILL_QUESTIONS"]).SKILL_QUESTIONS
    # And the bundle above was produced from a 5-question interview state.
    assert isinstance(state, InterviewState)
    assert not isinstance(state, SkillInterviewState)


def test_emit_plugin_skill_bundle_no_devkit_substring(tmp_path):
    """Bundled skill files must not be written when the render contains dev-kit.

    Note: the 0-mvp canonical emit (src.emitter.codex.emit) writes
    plugin.json BEFORE its dev-kit substring check; on substring violation
    it raises EmitError mid-write, so plugin.json may already exist on
    disk. The bundle files (the new ones this emitter is responsible for)
    must NOT be written if their in-memory render fails validation.
    """
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle, EmitError
    s = _complete_state()
    plan_md = "# Plugin\n\nTest plan for dev-kit bundle scenarios only"
    with pytest.raises(EmitError):
        emit_plugin_skill_bundle(s, plan_md, tmp_path, skill_slugs=["demo-skill"])
    # The CC bundle file is OUR responsibility; assert it was NOT written.
    cc_files = list((tmp_path / ".claude" / "skills").rglob("SKILL.md"))
    codex_files = list((tmp_path / ".codex" / "skills").rglob("SKILL.md"))
    assert cc_files == []
    assert codex_files == []


def test_emit_plugin_skill_bundle_no_devkit_substring_in_state(tmp_path):
    """If state.answers contains dev-kit, emit rejects (validator catches it)."""
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle, EmitError
    from src.schema.state import InterviewState
    s = InterviewState()
    long = "x" * 30
    # Set what-who-where with a description containing dev-kit.
    s.set_answer("what-who-where", "Test dev-kit description " + long)
    s.advance()
    s.set_answer("why-this-problem", long)
    s.advance()
    s.set_answer("how-it-works", long)
    s.advance()
    s.set_answer("ai-usage", long)
    s.advance()
    s.set_answer("how-verified", long)
    s.advance()
    plan_md = "# Plugin\n\nClean plan body content here"
    with pytest.raises(EmitError):
        emit_plugin_skill_bundle(s, plan_md, tmp_path, skill_slugs=["demo-skill"])


def test_emit_plugin_skill_bundle_incomplete_state_raises(tmp_path):
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle, EmitError
    from src.schema.state import InterviewState
    s = InterviewState()
    # 0/5 answers
    with pytest.raises(EmitError):
        emit_plugin_skill_bundle(s, "# plan\n\nbody", tmp_path, skill_slugs=["demo-skill"])


# ---------- CLI surface ----------

def test_cli_accepts_skill_slug_flag():
    import subprocess
    import sys
    REPO_ROOT = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "src.engine.cli", "new", "x", "--help"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert "--skill-slug" in result.stdout
