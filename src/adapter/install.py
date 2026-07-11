"""Install-time primitives shared across all adapters.

PR #26 LLM review (🟠 major #1 + #2): the previous codex.py co-located
install-time helpers (_atomic_write_text, _backup_existing,
_refuse_if_symlink_chain) with codex-specific code, forcing the
still-pending cc-adapter (step 4) to re-implement the same primitives.
Extract them here so any future adapter imports a single, audited
helper module.

These helpers are install-time only — they are not invoked by the
runtime interview engine. They have no dependency on the adapter
specifics (CC vs Codex layout), only on POSIX filesystem semantics.
The single `Path`-in / `Path`-out contract lets each adapter compose
the helpers differently.
"""

from __future__ import annotations

import datetime as _dt
import os
import stat
import tempfile
from pathlib import Path


def atomic_write_text(target: Path, content: str) -> None:
    """Write `content` to `target` atomically with explicit file mode.

    PR #26 A06-1: target.write_text truncates the existing file before
    the new bytes are fully flushed. SIGKILL / ENOSPC / power-loss
    mid-write leaves a truncated file at the runtime discovery path.
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


def backup_existing(target: Path) -> None:
    """Snapshot a pre-existing file before overwriting (A06-2).

    The reviewer's preferred alternative (refuse-if-foreign) breaks
    idempotent re-runs on hand-authored content. Backing up to a
    timestamped sibling preserves prior content while still honoring
    the idempotent-re-run contract.

    PR #26 round 9 minor: mirror the A02 fix on the main write so
    backups under a permissive umask don't end up world-writable.
    """
    ts = _dt.datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup = target.with_suffix(target.suffix + f".bak.{ts}")
    backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    backup.chmod(0o644)


def refuse_if_symlink_chain(target: Path, project_root: Path) -> None:
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


__all__ = ["atomic_write_text", "backup_existing", "refuse_if_symlink_chain"]
