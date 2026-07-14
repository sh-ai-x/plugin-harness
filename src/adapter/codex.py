"""Codex adapter — installs the plugin-harness as a Codex skill.

The Codex runtime discovers project-level skills under
`.agents/skills/<skill-name>/SKILL.md` (per
https://developers.openai.com/codex/skills). This adapter installs exactly
that layout and points the skill body at the shared
`python -m src.engine.cli` entrypoint, so the harness can be invoked
identically from CC and Codex (one command, two surfaces).

The adapter is install-time only — it does not modify runtime behavior
of the engine.

PR #26 LLM review (🟠 major #1 + #2): the Adapter Protocol from
src.adapter declares the contract; this module satisfies it. The
shared install-time primitives (atomic write, backup, symlink refusal)
now live in src.adapter.install instead of being co-located with
codex-specific code.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from src.adapter.install import (
    atomic_write_text,
    backup_existing,
    refuse_if_symlink_chain,
)

# Canonical Codex path per https://developers.openai.com/codex/skills:
#   $REPO_ROOT/.agents/skills/<skill-name>/SKILL.md
CODEX_SKILL_REL_PATH = Path(".agents/skills/plugin-harness/SKILL.md")

# Package path of the bundled SKILL.md within the source tree.
# PR #26 LLM review (🟠 major #3): the previous version relied on the
# filesystem fallback because codex_skills/ had no __init__.py and the
# repo had no pyproject.toml `[tool.setuptools.package-data]` entry.
# Adding __init__.py files at every level makes the package importable
# via importlib.resources; the filesystem fallback remains as a
# belt-and-suspenders for editable installs that haven't been built.
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


# ---- 1-skill-creator: skill-creator / plugin-creator install siblings ----

_CODEX_SKILL_REL_PATHS = {
    # name → relative install path under the project root
    "skill-creator": Path(".codex/skills/skill-creator/SKILL.md"),
    "plugin-creator": Path(".codex/skills/plugin-creator/SKILL.md"),
}

_SKILL_RESOURCE_PACKAGES = {
    "skill-creator": "src.adapter.codex_skills.skill-creator",
    "plugin-creator": "src.adapter.codex_skills.plugin-creator",
}


def _read_codex_skill(name: str) -> str:
    """Read the bundled Codex SKILL.md for `name` from package data."""
    pkg = _SKILL_RESOURCE_PACKAGES[name]
    try:
        return (
            resources.files(pkg).joinpath("SKILL.md").read_text(encoding="utf-8")
        )
    except (ModuleNotFoundError, FileNotFoundError):
        here = Path(__file__).resolve().parent
        candidate = here / "codex_skills" / name / "SKILL.md"
        if not candidate.is_file():
            raise FileNotFoundError(f"bundled Codex skill {name!r} not found")
        return candidate.read_text(encoding="utf-8")


def register_codex_skill(name: str, project_dir: Path) -> Path:
    """Install a Codex skill template (skill-creator / plugin-creator) into a project.

    Creates (or overwrites):

        ``<project_dir>/.codex/skills/<name>/SKILL.md``

    Idempotent on re-run: same target path is overwritten in place; no
    `.bak.<timestamp>` files are emitted (unlike the canonical
    `register_codex` plugin install which backs up before writing).
    Returns the path to the installed SKILL.md.
    """
    if name not in _CODEX_SKILL_REL_PATHS:
        raise KeyError(
            f"unknown codex skill {name!r}; expected one of {list(_CODEX_SKILL_REL_PATHS)}"
        )
    project_dir = Path(project_dir)
    target = project_dir / _CODEX_SKILL_REL_PATHS[name]
    refuse_if_symlink_chain(target, project_root=project_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = _read_codex_skill(name)
    atomic_write_text(target, content)
    return target


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


class CodexAdapter:
    """Installs the plugin-harness skill into a Codex project.

    Satisfies the `Adapter` Protocol from src.adapter. Idempotent:
    re-running `register(project_dir)` produces the same end state
    as a fresh install (same content, prior version backed up).
    """

    def register(self, project_dir: Path) -> Path:
        target = Path(project_dir) / CODEX_SKILL_REL_PATH
        # Defense-in-depth: refuse symlinks BEFORE creating any directory.
        # Otherwise mkdir would materialize attacker-controlled parent
        # dirs (PR #26 round 7: closes the partial-state gap).
        refuse_if_symlink_chain(target, project_root=Path(project_dir))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            backup_existing(target)  # preserve prior content
        content = _bundled_skill_text()
        atomic_write_text(target, content)
        return target


def register_codex(project_dir: Path) -> Path:
    """Module-level convenience function matching the prior call shape.

    Equivalent to `CodexAdapter().register(project_dir)`. Kept so
    existing callers (tests, downstream scripts) can stay on the
    free-function form.
    """
    return CodexAdapter().register(project_dir)


__all__ = ["register_codex", "CODEX_SKILL_REL_PATH", "CodexAdapter"]
