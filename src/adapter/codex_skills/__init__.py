"""Marker package — `src.adapter.codex_skills` exists so
`importlib.resources.files("src.adapter.codex_skills.plugin-harness")`
can resolve the bundled SKILL.md at install-time.

PR #26 LLM review (🟠 major #3): without this `__init__.py`, the
importlib.resources path was unreachable and the install-time code
silently fell back to a filesystem read — masking broken packaging
in `pip install .` workflows.
"""
