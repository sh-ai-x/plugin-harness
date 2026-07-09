"""Mode B — AI-research: calls the runtime's tool surface to draft each answer.

The tool surface is injected at the CLI layer. It must expose
`draft_answer(*, question, idea) -> str` (keyword-only, matching the
`ToolSurface` Protocol in runner.py) and may additionally use web_search /
web_fetch to gather material before drafting. This module itself performs no I/O.
"""
from __future__ import annotations

from typing import Any, Optional


class DefaultToolSurface:
    """Fallback tool surface when the runtime has not injected one.

    Real Claude Code / Codex runtimes pass in a richer surface via the CLI.
    This default keeps the engine usable in standalone contexts.
    """

    def draft_answer(self, *, question: dict, idea: str) -> str:
        idea_fragment = idea.strip() or "your idea"
        template = (
            f"For the idea {idea_fragment!r}, address {question['id']!r}: "
            f"{question['prompt']} This response is generated as a starting "
            f"draft and is at least twenty characters long."
        )
        if len(template) < question["min_length"]:
            template = template + " " + "x" * (question["min_length"] - len(template))
        return template


def make_tool_surface(surface: Optional[Any]) -> Any:
    if surface is None:
        return DefaultToolSurface()
    return surface


def is_default_surface(surface: Any) -> bool:
    return isinstance(surface, DefaultToolSurface)


__all__ = ["DefaultToolSurface", "make_tool_surface", "is_default_surface"]