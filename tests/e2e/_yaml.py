"""Shared YAML front-matter helpers for the e2e suite.

PR #27 round 6 (🟠 major): _extract_body was duplicated across
tests/e2e/pipeline.py, tests/e2e/test_full_pipeline.py, and the new
regression test. Promote to a shared module.
"""


def extract_body(text: str) -> str:
    """Return the document body (everything after YAML front-matter).

    A document with front-matter begins with `---` on line 1 and closes
    front-matter at the next `---` on its own line. If no front-matter
    is detected, the whole document is returned unchanged so naive
    comparisons stay meaningful.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[i + 1:])
    return text
