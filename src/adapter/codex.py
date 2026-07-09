"""Codex adapter — installs the plugin-harness as a Codex skill.

The Codex runtime discovers project-level skills under
`.agents/skills/<skill-name>/SKILL.md` (per
https://developers.openai.com/codex/skills). This adapter installs exactly
that layout and points the skill body at the shared
`python -m src.engine.cli` entrypoint, so the harness can be invoked
identically from CC and Codex (one command, two surfaces).

The adapter is install-time only — it does not modify runtime behavior
of the engine.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

# Canonical Codex path per https://developers.openai.com/codex/skills:
#   $REPO_ROOT/.agents/skills/<skill-name>/SKILL.md
CODEX_SKILL_REL_PATH = Path(".agents/skills/plugin-harness/SKILL.md")

# Package path of the bundled SKILL.md within the source tree.
_SKILL_PACKAGE = "src.adapter.codex_skills.plugin-harness"
_SKILL_RESOURCE = "SKILL.md"


def _read_bundled_skill() -> str:
    """Read the bundled SKILL.md from this adapter's package data."""
    return (
        resources.files(_SKILL_PACKAGE)
        .joinpath(_SKILL_RESOURCE)
        .read_text(encoding="utf-8")
    )


def _bundled_skill_via_filesystem() -> Path | None:
    """Fallback for editable installs: read the SKILL.md from the source tree.

    `importlib.resources` resolves installed packages; during local
    development the package may live on disk as loose files. This
    fallback lets `register_codex` work in both scenarios.
    """
    here = Path(__file__).resolve().parent
    candidate = here / "codex_skills" / "plugin-harness" / "SKILL.md"
    return candidate if candidate.is_file() else None


def _bundled_skill_text() -> str:
    """Resolve the bundled SKILL.md contents (package data or filesystem)."""
    try:
        return _read_bundled_skill()
    except (ModuleNotFoundError, FileNotFoundError):
        fs = _bundled_skill_via_filesystem()
        if fs is None:
            raise FileNotFoundError(
                "bundled SKILL.md not found in package data or source tree"
            )
        return fs.read_text(encoding="utf-8")


def register_codex(project_dir: Path) -> Path:
    """Install the plugin-harness Codex skill into `project_dir`.

    Writes exactly one file: `<project_dir>/.agents/skills/plugin-harness/SKILL.md`,
    the path Codex scans for project-level skills. Re-running this function
    overwrites the same file (idempotent — no duplicates).

    Parameters
    ----------
    project_dir:
        The repository root where Codex should discover the skill. Must
        exist or be writable; parent directories are created as needed.

    Returns
    -------
    pathlib.Path
        Absolute path to the written SKILL.md.
    """
    target = Path(project_dir) / CODEX_SKILL_REL_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_bundled_skill_text(), encoding="utf-8")
    return target


__all__ = ["register_codex", "CODEX_SKILL_REL_PATH"]
