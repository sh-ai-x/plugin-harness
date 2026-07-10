"""Runtime adapters that expose the plugin-harness engine to different hosts.

Each adapter is a thin install-time surface that exposes the same
`src.engine.cli` entrypoint through the runtime's native invocation
shape (slash command, skill, etc.). The engine logic is owned by step 1;
adapters do not duplicate it.

Public API:

  - `Adapter` — `runtime_checkable` Protocol; every adapter satisfies
    `register(project_dir) -> Path`. Existing adapters (Codex) and
    still-pending ones (cc-adapter) declare conformance without
    importing adapter internals.
  - `register_codex` — the Codex adapter's entry point.

The install primitives (`atomic_write_text`, `backup_existing`,
`refuse_if_symlink_chain`) live in `src.adapter.install` (no underscore
prefix → public module name matches the public surface) and are NOT
re-exported here. Adapters import them directly:

    from src.adapter.install import (
        atomic_write_text, backup_existing, refuse_if_symlink_chain,
    )

Re-exporting them here previously violated the public/private layering
signal (PR #26 round 12 🟠 major): the helpers had no underscore prefix
but the module name carried a leading underscore (`_install.py`),
sending mixed signals about whether the surface was public. The fix
renames `_install.py` to `install.py` so the public module name
matches the public re-export boundary; nothing re-exports it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.adapter.codex import register_codex


@runtime_checkable
class Adapter(Protocol):
    """Contract every runtime adapter satisfies.

    `register(project_dir)` is the only method an adapter has to
    implement. It writes the runtime-specific discovery file(s) under
    `project_dir` and returns the absolute path of the canonical
    artifact it just installed (so callers can verify post-conditions).

    Adapters MUST be idempotent: re-running `register(project_dir)`
    on a project that already has the skill installed MUST produce
    the same end state as a fresh install. The shared `install`
    primitives enforce this — `backup_existing` + `atomic_write_text`
    make a second install either an overwrite (same content) or a
    prior-content-preserving re-install.

    Adapters MUST NOT perform any I/O outside `project_dir` (no
    network, no global config writes, no shell hooks).
    """

    def register(self, project_dir: Path) -> Path: ...


__all__ = ["Adapter", "register_codex"]
