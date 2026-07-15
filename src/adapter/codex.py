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

from pathlib import Path

from src.adapter.install import (
    atomic_write_text,
    backup_existing,
    refuse_if_symlink_chain,
)

# 1-skill-creator follow-up: skill assets shipped at repo-root skills/<name>/.
# CC reads the .md file (Claude Code layout); Codex reads the .codex.md
# companion file (Codex layout). Both files share the same body; only the
# frontmatter shape is runtime-specific.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/adapter/ -> src/ -> repo root
_SKILLS_DIR = _PROJECT_ROOT / "skills"

# Canonical Codex path per https://developers.openai.com/codex/skills:
#   $REPO_ROOT/.agents/skills/<skill-name>/SKILL.md
CODEX_SKILL_REL_PATH = Path(".agents/skills/plugin-harness/SKILL.md")


def _read_bundled_skill() -> str:
    """Read the Codex-layout SKILL.md for plugin-harness from the source tree."""
    candidate = _SKILLS_DIR / "plugin-harness" / "SKILL.codex.md"
    if not candidate.is_file():
        raise FileNotFoundError(f"bundled Codex SKILL.md not found: {candidate}")
    return candidate.read_text(encoding="utf-8")


def _bundled_skill_via_filesystem() -> Path | None:
    """Filesystem-only fallback (kept for the importlib-style API surface)."""
    candidate = _SKILLS_DIR / "plugin-harness" / "SKILL.codex.md"
    return candidate if candidate.is_file() else None


# ---- 1-skill-creator: skill-creator / plugin-creator install siblings ----

_CODEX_SKILL_REL_PATHS = {
    # name → relative install path under the project root
    "skill-creator": Path(".codex/skills/skill-creator/SKILL.md"),
    "plugin-creator": Path(".codex/skills/plugin-creator/SKILL.md"),
}


def _read_codex_skill(name: str) -> str:
    """Read the Codex-layout SKILL.md for `name` from the source tree."""
    candidate = _SKILLS_DIR / name / "SKILL.codex.md"
    if not candidate.is_file():
        raise FileNotFoundError(f"bundled Codex skill {name!r} not found: {candidate}")
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
