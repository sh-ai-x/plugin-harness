"""Adapter layer — installs the harness onto downstream runtimes.

Each adapter is a thin install-time surface that exposes the same
`src.engine.cli` entrypoint through the runtime's native invocation
shape (slash command, skill, etc.). The engine logic is owned by step 1;
adapters do not duplicate it.

PR #26 LLM review (🟠 major #1): the previous `__init__` was empty —
nothing bound the layer. Add a thin `Adapter` Protocol so the
still-pending cc-adapter (step 4) and any future adapter can declare
"register me is the contract" without importing codex internals.

PR #26 LLM review (🟠 major #2): install-time primitives (atomic write,
backup, symlink refusal) used to live in codex.py. They are now in
`_install` and re-exported here as a public surface so adapters import
one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.adapter._install import (
    atomic_write_text,
    backup_existing,
    refuse_if_symlink_chain,
)


@runtime_checkable
class Adapter(Protocol):
    """Contract every runtime adapter satisfies.

    `register(project_dir)` is the only method an adapter has to
    implement. It writes the runtime-specific discovery file(s) under
    `project_dir` and returns the absolute path of the canonical
    artifact it just installed (so callers can verify post-conditions).

    Adapters MUST be idempotent: re-running `register(project_dir)`
    on a project that already has the skill installed MUST produce
    the same end state as a fresh install. The shared `_install`
    primitives enforce this — backup_existing + atomic_write_text
    make a second install either an overwrite (same content) or a
    prior-content-preserving re-install.

    Adapters MUST NOT perform any I/O outside `project_dir` (no
    network, no global config writes, no shell hooks).
    """

    def register(self, project_dir: Path) -> Path: ...


__all__ = [
    "Adapter",
    "atomic_write_text",
    "backup_existing",
    "refuse_if_symlink_chain",
]
