"""Tests for the Claude Code adapter.

Covers the install-time contract of ``src.adapter.cc.register_cc``:

* Creates ``.claude/commands/plugin-harness.md`` and ``.claude/skills/plugin-harness/SKILL.md``.
* Both files point at the same ``src.engine.cli`` entrypoint.
* Re-running ``register_cc`` is idempotent (overwrite, no duplicates).
* Installed content contains no ``dev-kit`` token.
* Installed command matches the frozen fixture snapshot.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.adapter.cc import register_cc


_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "cc_install" / "expected"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_register_cc_creates_slash_command() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)
        command = project_dir / ".claude" / "commands" / "plugin-harness.md"
        assert command.exists()
        assert "python -m src.engine.cli" in _read(command)


def test_register_cc_creates_skill() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)
        skill = project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md"
        assert skill.exists()
        assert "python -m src.engine.cli" in _read(skill)


def test_register_cc_creates_expected_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)
        assert (project_dir / ".claude" / "commands" / "plugin-harness.md").exists()
        assert (project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md").exists()


def test_register_cc_command_and_skill_share_engine_entrypoint() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)
        command = _read(project_dir / ".claude" / "commands" / "plugin-harness.md")
        skill = _read(project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md")
        assert "src.engine.cli" in command
        assert "src.engine.cli" in skill
        # Same entrypoint surface, same module target.
        assert "python -m src.engine.cli" in command
        assert "python -m src.engine.cli" in skill


def test_register_cc_is_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)

        first_command = _read(project_dir / ".claude" / "commands" / "plugin-harness.md")
        first_skill = _read(project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md")

        # Re-run; should overwrite (not duplicate).
        register_cc(project_dir)

        commands_dir = project_dir / ".claude" / "commands"
        skills_dir = project_dir / ".claude" / "skills" / "plugin-harness"
        assert sorted(p.name for p in commands_dir.iterdir()) == ["plugin-harness.md"]
        assert sorted(p.name for p in skills_dir.iterdir()) == ["SKILL.md"]

        assert _read(project_dir / ".claude" / "commands" / "plugin-harness.md") == first_command
        assert _read(project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md") == first_skill


def test_register_cc_emitted_content_has_no_dev_kit_token() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)
        command = _read(project_dir / ".claude" / "commands" / "plugin-harness.md")
        skill = _read(project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md")
        assert "dev-kit" not in command
        assert "dev-kit" not in skill


def test_installed_command_matches_expected_fixture() -> None:
    expected = _FIXTURE_DIR / ".claude" / "commands" / "plugin-harness.md"
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_cc(project_dir)
        installed = project_dir / ".claude" / "commands" / "plugin-harness.md"
        assert _read(installed) == _read(expected)