"""Assemble a completed InterviewState into the user-facing idea plan Markdown.

The plan shape is locked by phases/0-mvp/step2.md:

    # Idea Plan — <derived plugin name>
    ## 1. What, who, where
    ## 2. Why this problem
    ## 3. How the plugin works
    ## 4. AI usage
    ## 5. Verification
    ## 6. Synthesis

Sections 1-5 are direct quotes of the user's answers (Markdown-escaped).
Section 6 is derived from answers 1-3 (synthesis paragraph, <= 200 words).

Output is byte-for-byte deterministic for a given state: no randomness, no
clock, no environment-dependent formatting. The Jinja2 template is rendered
with `keep_trailing_newline=True` so a final newline is preserved.
"""
from __future__ import annotations

import pathlib
import re
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.schema.questions import QUESTIONS, canonical_ids
from src.schema.state import InterviewState


class AssemblerError(Exception):
    """Raised when the state cannot be assembled into a plan."""


_TEMPLATE_DIR = pathlib.Path(__file__).parent / "templates"
_TEMPLATE_NAME = "idea_plan.md.j2"

# Synthesis section hard cap (locked by step2.md).
SYNTHESIS_MAX_WORDS = 200

# Canonical question id order for sections 1-5.
_SECTION_ORDER: tuple[str, ...] = (
    "what-who-where",
    "why-this-problem",
    "how-it-works",
    "ai-usage",
    "how-verified",
)

_SECTION_TITLES: dict[str, str] = {
    "what-who-where": "What, who, where",
    "why-this-problem": "Why this problem",
    "how-it-works": "How the plugin works",
    "ai-usage": "AI usage",
    "how-verified": "Verification",
}


# ---- Markdown escape --------------------------------------------------------


# Order is significant: < first (does not introduce newlines), then > with
# leading-aware handling, then the inline-punctuation tokens, then the
# heading-anchor (#) last. We do NOT escape '!' — AC4 verifies it stays raw.
def _escape_markdown(text: str) -> str:
    """Neutralize Markdown-significant characters in user-supplied answer text.

    Escape table (per phases/0-mvp/step2.md AC4):
        '<'     -> '&lt;'
        '>'     -> '\\>'   (start of string, OR preceded by actual '\\n',
                            OR preceded by literal '\\' — the case after
                            a literal '\\n' two-char sequence in the input)
              -> '&gt;'   (otherwise)
        '['     -> '\\['
        ']'     -> '\\]'
        '('     -> '\\('
        ')'     -> '\\)'
        '`'     -> '\\`'
        '#'     -> '&#35;'
        '*'     -> '\\*'
        '_'     -> '\\_'

    '!' is intentionally NOT escaped (image-syntax break is acceptable;
    AC4 verifies `!important` stays raw). Section headings are NOT escaped
    because they are hard-coded strings, not user input.

    The '>' substitution is done in a single regex pass so the '>' inside
    any '\\>' we just inserted is not re-matched. The "<" pass is run first
    so its replacement '&lt;' does not collide with the '>' pass.
    """
    if not text:
        return text
    # 1. '<' first so its replacement '&lt;' does not introduce a '<'.
    out = text.replace("<", "&lt;")
    # 2. '>' — leading (start of input, OR preceded by '\\n' literal 2-char,
    #    OR preceded by actual newline char) -> '\\>'. Else -> '&gt;'.
    def _gt_repl(match: "re.Match[str]") -> str:
        i = match.start()
        if i == 0:
            return "\\>"
        prev = out[i - 1]
        if prev == "\\" or prev == "\n":
            return "\\>"
        return "&gt;"
    out = re.sub(">", _gt_repl, out)
    # 3-10. remaining tokens
    out = out.replace("[", "\\[")
    out = out.replace("]", "\\]")
    out = out.replace("(", "\\(")
    out = out.replace(")", "\\)")
    out = out.replace("`", "\\`")
    out = out.replace("#", "&#35;")
    out = out.replace("*", "\\*")
    out = out.replace("_", "\\_")
    return out


# ---- Plugin-name derivation -------------------------------------------------


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _derive_plugin_name(state: InterviewState) -> str:
    """Derive the plugin display name deterministically from the state.

    Strategy: take up to the first 5 word-like tokens from the
    ``what-who-where`` answer, slugify, then title-case for display.
    Falls back to ``"Untitled Plugin"`` when the answer is empty or
    yields no word tokens (the assembler rejects empty answers upstream,
    so this is a safety net only).
    """
    first = state.answers.get("what-who-where", "").lower()
    tokens = re.findall(r"[a-z0-9]+", first)[:5]
    slug = "-".join(tokens).strip("-")
    if not slug:
        return "Untitled Plugin"
    title = " ".join(part.capitalize() for part in slug.split("-") if part)
    return title or "Untitled Plugin"


# ---- Synthesis --------------------------------------------------------------


def _derive_synthesis(state: InterviewState) -> str:
    """Derive section 6 from answers 1-3 as a single paragraph (<=200 words).

    Strategy: take the first ~60 words of each of answers 1, 2, 3; concatenate
    with bridging phrases; truncate the final paragraph to 200 words. The
    result is deterministic for a given state because the input is bounded
    and no randomness / clock is involved. All snippets are Markdown-escaped
    so the synthesis cannot leak unescaped Markdown-significant characters
    into the assembled plan.
    """
    fragments: list[str] = []
    bridges = (
        "The plugin addresses the following situation:",
        "It is motivated by this problem:",
        "It works by doing this:",
    )
    sources = (
        state.answers["what-who-where"],
        state.answers["why-this-problem"],
        state.answers["how-it-works"],
    )
    for bridge, source in zip(bridges, sources):
        snippet = _first_n_words(source, 60)
        fragments.append(f"{bridge} {_escape_markdown(snippet)}".strip())
    paragraph = " ".join(fragments)
    words = paragraph.split()
    if len(words) > SYNTHESIS_MAX_WORDS:
        paragraph = " ".join(words[:SYNTHESIS_MAX_WORDS])
    return paragraph


def _first_n_words(text: str, n: int) -> str:
    """Return the first ``n`` whitespace-delimited words of ``text``."""
    words = text.split()
    if len(words) <= n:
        return text.strip()
    return " ".join(words[:n]).strip()


# ---- Validation -------------------------------------------------------------


def _validate_state(state: InterviewState) -> None:
    """Raise AssemblerError on any missing or empty canonical answer."""
    missing = [
        qid for qid in canonical_ids()
        if not state.answers.get(qid)
    ]
    if missing:
        raise AssemblerError(
            f"interview state is incomplete; missing answers: {missing!r}"
        )


# ---- Jinja environment ------------------------------------------------------


def _make_env() -> Environment:
    loader = FileSystemLoader(str(_TEMPLATE_DIR))
    env = Environment(
        loader=loader,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,  # we escape ourselves, deterministically
        trim_blocks=False,
        lstrip_blocks=False,
    )
    return env


_ENV = _make_env()
_TEMPLATE = _ENV.get_template(_TEMPLATE_NAME)


# ---- Public API -------------------------------------------------------------


def assemble(state: InterviewState) -> str:
    """Assemble the final idea plan Markdown from a completed state.

    Sections 1-5 are direct, Markdown-escaped quotes of the user's answers.
    Section 6 is the synthesis derived from answers 1-3.

    Raises:
        AssemblerError: state is missing any of the 5 canonical answers.
    """
    _validate_state(state)

    sections: list[dict[str, str]] = []
    for qid in _SECTION_ORDER:
        sections.append(
            {
                "qid": qid,
                "title": _SECTION_TITLES[qid],
                "body": _escape_markdown(state.answers[qid]),
            }
        )

    synthesis = _derive_synthesis(state)
    plugin_name = _derive_plugin_name(state)

    rendered = _TEMPLATE.render(
        plugin_name=plugin_name,
        sections=sections,
        synthesis=synthesis,
    )
    return rendered


__all__ = ["AssemblerError", "assemble"]


# Touch QUESTIONS at import time so a future schema drift surfaces as an
# ImportError rather than a runtime KeyError inside assemble().
_ = QUESTIONS  # noqa: F841