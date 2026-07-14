"""loader.py — vendored skill schema loader.

Reads the right JSON Schema for the requested runtime from `docs/`. Cached
at module import to avoid re-parsing on every validation call. The schemas
are checked into the repository (vendored), never fetched over the network,
so the validator is offline-safe.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs"

_RUNTIMES = ("cc", "codex")


@lru_cache(maxsize=None)
def load_spec(runtime: Literal["cc", "codex"]) -> dict:
    """Load and return the vendored JSON Schema for the requested runtime.

    Args:
        runtime: one of `"cc"` (Claude Code) or `"codex"` (Codex).

    Returns:
        The parsed JSON Schema as a Python dict.

    Raises:
        KeyError: if `runtime` is not a known runtime.
        FileNotFoundError: if the schema file is missing (treated as a setup error).
        json.JSONDecodeError: if the schema file is malformed JSON.
    """
    if runtime not in _RUNTIMES:
        raise KeyError(f"unknown runtime {runtime!r}; expected one of {_RUNTIMES}")
    path = DOCS_DIR / f"{runtime}-skill.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))
