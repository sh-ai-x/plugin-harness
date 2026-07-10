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

import os
import stat
import tempfile
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

    Raises
    ------
    FileExistsError
        If the project_dir or any path under the install path is a
        symlink. Hard-fails rather than follow the symlink so an
        attacker who pre-plants the project tree as a symlink cannot
        divert the install. PR #26 round 7 reordered this check to
        run BEFORE mkdir so partial directory state does not persist
        on a hostile project_dir.
    """
    target = Path(project_dir) / CODEX_SKILL_REL_PATH
    # Defense-in-depth: refuse symlinks BEFORE creating any directory.
    # Otherwise mkdir would materialize attacker-controlled parent
    # dirs (PR #26 round 7: closes the partial-state gap).
    _refuse_if_symlink_chain(target, project_root=Path(project_dir))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        _backup_existing(target)  # preserve prior content
    content = _bundled_skill_text()
    _atomic_write_text(target, content)
    return target


def _refuse_if_symlink_chain(target: Path, project_root: Path) -> None:
    """Refuse the install if any path STRICTLY BELOW `project_root` is a symlink.

    Defense-in-depth: an attacker who pre-plants the project tree or
    any path under the install root as a symlink can otherwise divert
    the install into an arbitrary host path writable by the installer.
    Sibling-tempfile + os.replace does not follow symlinks at the
    rename target on POSIX, so checking the chain here is
    belt-and-suspenders.

    Walks ancestors from `target` up to but EXCLUDING `project_root`.
    macOS exposes /var -> /private/var, /tmp -> /private/tmp, etc. —
    those symlinks live at the project root (caller passes
    `/tmp` as the project_dir on macOS, for example). The check
    must NOT fire on the project_root itself, only on paths below
    it (PR #26 round 8: previous code rejected legitimate installs
    when the caller passed a system-symlinked project_dir).
    """
    for path in (target, *target.parents):
        if path == project_root:
            break  # don't check project_root itself
        if path.is_symlink():
            raise FileExistsError(
                f"refusing to write through symlink: {path}"
            )


def _backup_existing(target: Path) -> None:
    """Snapshot a pre-existing SKILL.md before overwriting (A06-2).

    The reviewer's preferred alternative (refuse-if-foreign) breaks
    idempotent re-runs on hand-authored content. Backing up to a
    timestamped sibling preserves prior content while still honoring
    the idempotent-re-run contract.
    """
    import datetime as _dt
    ts = _dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")


def _atomic_write_text(target: Path, content: str) -> None:
    """Write `content` to `target` atomically with explicit file mode.

    PR #26 A06-1: target.write_text truncates the existing file before
    the new bytes are fully flushed. SIGKILL / ENOSPC / power-loss
    mid-write leaves a truncated SKILL.md at the Codex discovery path.
    The sibling-tempfile + os.replace pattern is atomic on POSIX.

    PR #26 A02 minor: explicit mode=0o644 so the file does not end up
    world-writable under permissive umasks (common in slim containers
    and some CI providers).
    """
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        os.replace(tmp_name, target)
    except BaseException:
        # Clean up the temp file on any failure path.
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


__all__ = ["register_codex", "CODEX_SKILL_REL_PATH"]
