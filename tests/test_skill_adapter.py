"""Tests for the CC + Codex adapter siblings (skill-creator / plugin-creator).

Iron Law L1 (TDD): this file predates the new install functions in
src/adapter/{cc,codex}.py and the SKILL.md assets under
src/adapter/{cc,codex}_skills/{skill,plugin}-creator/.
"""
from __future__ import annotations

from pathlib import Path

import pytest


# ---- CC adapter ----

def test_register_cc_skill_skill_creator_installs_to_dot_claude(tmp_path):
    from src.adapter.cc import register_cc_skill
    target = register_cc_skill("skill-creator", tmp_path)
    assert target.exists()
    assert target == tmp_path / ".claude" / "skills" / "skill-creator" / "SKILL.md"


def test_register_cc_skill_plugin_creator_installs_to_dot_claude(tmp_path):
    from src.adapter.cc import register_cc_skill
    target = register_cc_skill("plugin-creator", tmp_path)
    assert target.exists()
    assert target == tmp_path / ".claude" / "skills" / "plugin-creator" / "SKILL.md"


def test_register_cc_skill_installed_file_validates(tmp_path):
    """The installed file must validate against the vendored CC schema."""
    from src.adapter.cc import register_cc_skill
    from src.skill_schema.validator import validate_skill_md
    target = register_cc_skill("skill-creator", tmp_path)
    r = validate_skill_md(target, "cc")
    assert r.ok, r.errors


def test_register_cc_skill_idempotent(tmp_path):
    from src.adapter.cc import register_cc_skill
    register_cc_skill("skill-creator", tmp_path)
    register_cc_skill("skill-creator", tmp_path)
    files = list((tmp_path / ".claude" / "skills" / "skill-creator").iterdir())
    assert len(files) == 1


def test_register_cc_skill_unknown_name_raises(tmp_path):
    from src.adapter.cc import register_cc_skill
    with pytest.raises(FileNotFoundError):
        register_cc_skill("not-a-real-skill", tmp_path)


def test_register_cc_skill_no_devkit_in_installed_file(tmp_path):
    from src.adapter.cc import register_cc_skill
    target = register_cc_skill("skill-creator", tmp_path)
    text = target.read_text(encoding="utf-8")
    # Schema rules + non-goal b: the installed SKILL.md must not contain
    # the forbidden substring in any of its user-facing fields.
    assert "dev-kit" not in text


# ---- Codex adapter ----

def test_register_codex_skill_skill_creator_installs_to_dot_codex(tmp_path):
    from src.adapter.codex import register_codex_skill
    target = register_codex_skill("skill-creator", tmp_path)
    assert target.exists()
    assert target == tmp_path / ".codex" / "skills" / "skill-creator" / "SKILL.md"


def test_register_codex_skill_plugin_creator_installs_to_dot_codex(tmp_path):
    from src.adapter.codex import register_codex_skill
    target = register_codex_skill("plugin-creator", tmp_path)
    assert target.exists()
    assert target == tmp_path / ".codex" / "skills" / "plugin-creator" / "SKILL.md"


def test_register_codex_skill_installed_file_validates(tmp_path):
    from src.adapter.codex import register_codex_skill
    from src.skill_schema.validator import validate_skill_md
    target = register_codex_skill("skill-creator", tmp_path)
    r = validate_skill_md(target, "codex")
    assert r.ok, r.errors


def test_register_codex_skill_idempotent(tmp_path):
    from src.adapter.codex import register_codex_skill
    register_codex_skill("skill-creator", tmp_path)
    register_codex_skill("skill-creator", tmp_path)
    files = list((tmp_path / ".codex" / "skills" / "skill-creator").iterdir())
    assert len(files) == 1


def test_register_codex_skill_unknown_name_raises(tmp_path):
    from src.adapter.codex import register_codex_skill
    with pytest.raises(KeyError):
        register_codex_skill("not-a-real-skill", tmp_path)


def test_register_codex_skill_no_devkit_in_installed_file(tmp_path):
    from src.adapter.codex import register_codex_skill
    target = register_codex_skill("plugin-creator", tmp_path)
    text = target.read_text(encoding="utf-8")
    assert "dev-kit" not in text


# ---- 0-mvp signatures unchanged ----

def test_register_cc_signature_unchanged():
    """0-mvp's `register_cc(project_dir)` signature must not change."""
    import inspect
    from src.adapter.cc import register_cc
    sig = inspect.signature(register_cc)
    assert list(sig.parameters.keys()) == ["project_dir"]


def test_register_codex_signature_unchanged():
    import inspect
    from src.adapter.codex import register_codex
    sig = inspect.signature(register_codex)
    assert list(sig.parameters.keys()) == ["project_dir"]


def test_register_cc_skill_does_not_break_0mvp_register_cc(tmp_path):
    """Re-running register_cc still installs the original slash command + skill."""
    from src.adapter.cc import register_cc, register_cc_skill
    register_cc(tmp_path)
    register_cc_skill("skill-creator", tmp_path)
    # Both files exist (original plugin-harness + new skill-creator)
    assert (tmp_path / ".claude" / "commands" / "plugin-harness.md").exists()
    assert (tmp_path / ".claude" / "skills" / "plugin-harness" / "SKILL.md").exists()
    assert (tmp_path / ".claude" / "skills" / "skill-creator" / "SKILL.md").exists()
