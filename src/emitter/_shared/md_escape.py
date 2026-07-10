"""Markdown + HTML escape for user-supplied text.

Single canonical escape function. PR #27 LLM review (🟠 major #3):
codex.py and plan.py each carried a divergent `_md_escape` and
`_escape_markdown` respectively. They disagreed on (`(`, `)`)
coverage and on the `#` representation (backslash-prefix vs HTML
entity), causing the assembled plan to drift between the assembler
output and the emitter output.

The canonical table (matches what `tests/test_emitter.py` expects for
`test_markdown_injection_escaped`):
  `<`            -> `&lt;`
  `>` (leading)  -> `\\>` (Markdown backslash — blockquote-injection defense)
  `>` (mid-line) -> `&gt;`
  `[`, `]`, `` ` ``, `#`, `*`, `_` -> `\\X` (Markdown backslash)
  `(`, `)`       -> preserved (link syntax `[]()` survives the
                    character class; `test_markdown_injection_escaped`
                    comment: "`(`, `)` are not in the step-2 escape set")
  `!`            -> preserved as-is (AC4: `!important` must stay raw)
  `&`            -> preserved as-is (no entity escape; user input never
                    reaches a context where `&` would be interpreted as
                    an entity starter).

The `>` leading-position pass uses a sentinel (`\\x00GTBS\\x00`) so
the literal `\\>` we just inserted is not re-matched by the
subsequent `&gt;` substitution.
"""

from __future__ import annotations

import re

__all__ = ["md_escape"]

# Sentinel that survives the &gt; substitution round-trip. We use it to
# distinguish "leading > we want as \\>" from "mid-line > we want as &gt;".
_LEADING_GT_SENTINEL = "\x00GTBS\x00"


def md_escape(text: str) -> str:
    """Escape user-derived text for Markdown + HTML insertion.

    Returns the empty string when `text` is empty (matches the existing
    convention in codex.py).
    """
    if not text:
        return ""

    # Markdown-special: backslash-escape. Single-pass, character by
    # character, so each replacement does not collide with the next.
    # `#` is escaped here (NOT as `&#35;`) to keep the table identical
    # to codex.py's original `_md_escape` — the previous divergence
    # between codex.py's `\#` and plan.py's `&#35;` is closed in favor
    # of the codex.py choice, which is what tests/test_emitter.py
    # asserts on.
    out = text
    for ch in ("[", "]", "`", "#", "*", "_"):
        out = out.replace(ch, "\\" + ch)

    # Leading `>` on a line → Markdown backslash (blockquote-injection).
    # Sentinel the backslash so the next pass does not double-escape.
    out = re.sub(r"(?m)^>", _LEADING_GT_SENTINEL, out)

    # HTML-entity escape `<` and the non-leading `>`.
    out = out.replace("<", "&lt;").replace(">", "&gt;")

    # Restore the leading-`>` escape (its sentinel above was replaced
    # by `&gt;` when the substitution touched the literal `>`).
    out = out.replace(_LEADING_GT_SENTINEL, "\\>")

    return out
