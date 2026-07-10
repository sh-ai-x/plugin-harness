"""Mode B — AI-research: calls the runtime's tool surface to draft each answer.

The tool surface is injected at the CLI layer. It must expose
`draft_answer(*, question, idea) -> str` (keyword-only, matching the
`ToolSurface` Protocol in runner.py) and may additionally use web_search /
web_fetch to gather material before drafting. This module itself performs no I/O.
"""
from __future__ import annotations

from typing import Optional

from src.engine.errors import InterviewIncompleteError, UserAbortError

from src.engine.runner import ToolSurface


class DefaultToolSurface:
    """Fallback tool surface when the runtime has not injected one.

    Real Claude Code / Codex runtimes pass in a richer surface via the CLI.
    This default keeps the engine usable in standalone contexts.
    """

    def draft_answer(self, *, question: dict, idea: str) -> str:
        # PR #22 round 10 (major): the previous template produced
        # strings over per-question max_length (e.g. a 2000-char idea
        # plus the f-string literal plus the Korean prompt totaled
        # ~2150 chars). _record would then raise ValidationError ->
        # exit 4 with a confusing message blaming the surface.
        # 1. Build the template; pad up to min_length if short.
        idea_fragment = idea.strip() or "your idea"
        template = (
            f"For the idea {idea_fragment!r}, address {question['id']!r}: "
            f"{question['prompt']} This response is generated as a starting "
            f"draft and is at least twenty characters long."
        )
        if len(template) < question["min_length"]:
            template = template + " " + "x" * (question["min_length"] - len(template))
        # 2. Hard-clamp to max_length so the surface never produces
        #    a string the validator will reject. Truncation is the
        #    right behavior for the offline fallback; the real LLM
        #    surface is expected to produce naturally bounded text.
        return template[: question["max_length"]]


def make_tool_surface(surface: Optional[ToolSurface]) -> ToolSurface:
    """Return the supplied tool surface, or the in-process DefaultToolSurface.

    PR #22 round 8 (🟠 major #2): both arg and return were `Any`,
    defeating the ToolSurface Protocol from runner.py. Now both are
    typed `Optional[ToolSurface]` / `ToolSurface` so the Protocol
    contract actually flows through the factory boundary.
    """
    if surface is None:
        return DefaultToolSurface()
    return surface


def is_default_surface(surface: Any) -> bool:
    return isinstance(surface, DefaultToolSurface)


__all__ = ["DefaultToolSurface", "make_tool_surface"]

# PR #22 round 9: register this mode's setup with the dispatch table.
from src.engine.modes import register_mode
def _setup_ai_research_mode(_make_reader, _make_writer, make_tool_surface):
    return None, None, make_tool_surface(None)


def _ai_research_per_question(question, idea, _stdin_reader, tool_surface):
    """Per-question handler for the 'ai-research' mode."""
    if tool_surface is None:
        raise UserAbortError("ai-research mode requires tool_surface")
    return _ai_draft_safe(tool_surface, question, idea)


def _ai_draft_safe(tool_surface, question, idea):
    """Wrap _ai_draft with the round-7 error handling."""
    try:
        return tool_surface.draft_answer(question=question, idea=idea)
    except (UserAbortError, KeyboardInterrupt):
        raise
    except Exception as exc:
        raise InterviewIncompleteError(
            f"tool-surface error while drafting {question['id']!r}: "
            f"{type(exc).__name__}"
        ) from exc
register_mode("ai-research", _ai_research_per_question)
