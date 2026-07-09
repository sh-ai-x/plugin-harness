"""Claude Code adapter — install-time surface for the plugin-harness engine.

The adapter is a thin shell wrapper. It does not modify runtime behavior of the
engine; it only copies the two template files (slash command + skill) into the
target project so Claude Code can invoke ``python -m src.engine.cli``.
"""
from __future__ import annotations

import shutil
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_COMMAND_TEMPLATE = _PACKAGE_DIR / "cc_commands" / "plugin-harness.md"
_SKILL_TEMPLATE = _PACKAGE_DIR / "cc_skills" / "plugin-harness" / "SKILL.md"


def register_cc(project_dir: Path) -> None:
    """Install the slash command and skill into a Claude Code project.

    Creates (or overwrites):

        ``<project_dir>/.claude/commands/plugin-harness.md``
        ``<project_dir>/.claude/skills/plugin-harness/SKILL.md``

    Both files point at the same ``src.engine.cli`` entrypoint. Re-running this
    function on the same ``project_dir`` is idempotent: existing files are
    overwritten, no duplicates are created.
    """
    project_dir = Path(project_dir)
    command_target = project_dir / ".claude" / "commands" / "plugin-harness.md"
    skill_target = project_dir / ".claude" / "skills" / "plugin-harness" / "SKILL.md"

    command_target.parent.mkdir(parents=True, exist_ok=True)
    skill_target.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(_COMMAND_TEMPLATE, command_target)
    shutil.copyfile(_SKILL_TEMPLATE, skill_target)