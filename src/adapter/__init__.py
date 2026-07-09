"""Adapter layer — installs the harness onto downstream runtimes.

Each adapter is a thin install-time surface that exposes the same
`src.engine.cli` entrypoint through the runtime's native invocation
shape (slash command, skill, etc.). The engine logic is owned by step 1;
adapters do not duplicate it.
"""

__all__: list[str] = []
