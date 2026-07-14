"""Claude Code adapter — install-time surface for the plugin-harness engine.

The adapter is a thin shell wrapper. It does not modify runtime behavior of the
engine; it only copies the template files (slash command + skill) into the
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


# ---- 1-skill-creator: skill-creator and plugin-creator install siblings ----

from src.adapter.install import atomic_write_text, refuse_if_symlink_chain  # noqa: E402


# PR #40 review (🟠 major): Allowlist for `register_cc_skill(name, ...)`. The name
# flows into a filesystem path, so unvalidated input enables path traversal.
# Mirror the Codex adapter's runtime-keyed pattern: only the named skills ship
# as bundled assets in `src/adapter/cc_skills/` are installable.
_CC_SKILL_ALLOWLIST = frozenset({"skill-creator", "plugin-creator"})


def _cc_skill_template(name: str) -> Path:
    """Locate the bundled CC SKILL.md template for `name`.

    Raises FileNotFoundError if the template does not exist.
    Raises ValueError if `name` is not in the bundled-asset allowlist.
    """
    if name not in _CC_SKILL_ALLOWLIST:
        raise ValueError(
            f"unknown CC skill {name!r}; expected one of {sorted(_CC_SKILL_ALLOWLIST)}"
        )
    candidate = _PACKAGE_DIR / "cc_skills" / name / "SKILL.md"
    if not candidate.is_file():
        raise FileNotFoundError(f"bundled CC skill template not found: {candidate}")
    return candidate


def register_cc_skill(name: str, project_dir: Path) -> Path:
    """Install a CC skill template (skill-creator / plugin-creator) into a project.

    Creates (or overwrites):

        ``<project_dir>/.claude/skills/<name>/SKILL.md``

    Idempotent on re-run. Returns the path to the installed SKILL.md.

    `name` is allowlisted against `_CC_SKILL_ALLOWLIST` BEFORE the target
    path is constructed; an unrecognized name raises ValueError to block
    path-traversal via `../` or absolute-path injection.
    """
    project_dir = Path(project_dir)
    template = _cc_skill_template(name)  # validates `name` first
    target = project_dir / ".claude" / "skills" / name / "SKILL.md"
    refuse_if_symlink_chain(target, project_root=project_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, target)
    return target