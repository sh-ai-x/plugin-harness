"""Shared helpers for the dual-runtime plugin emitter.

PR #27 LLM review (🟠 major #3 + #4): two divergent Markdown-escape
tables were kept in codex.py and plan.py, and the Codex output layout
(`.codex-plugin/`, `src/skills/<slug>/`, `src/.mcp.json`, `README.md`)
was hardcoded in two unrelated files. Extract one shared
`md_escape` and one `CodexLayout` here so:

  - plan.py and codex.py render user-derived text through the SAME
    escape table (no drift),
  - codex.py and validator.py agree on the same output paths.

This module is intentionally tiny: a single function and a single
class. Anything emitter-specific (templates, Jinja environment)
stays in codex.py / templates/.
"""
