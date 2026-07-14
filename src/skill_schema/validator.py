"""validator.py — SKILL.md frontmatter validation.

Extracts YAML frontmatter (between two `---` markers), runs JSON Schema
validation against the vendored spec for the requested runtime, and returns
a typed `ValidationReport`. Also enforces the `dev-kit` substring prohibition
(non-goal b of the 0-mvp PRD, extended to phase1) because JSON Schema
draft-07 has no regex-negation primitive.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal

import jsonschema

from src.skill_schema.loader import load_spec

FORBIDDEN_SUBSTRINGS = ("dev-kit",)


@dataclass
class ValidationReport:
    """Typed result of validating one SKILL.md file against one runtime spec.

    Attributes:
        ok: True iff every check passed (schema + substring + presence).
        runtime: The runtime tag that was used for validation (`"cc"` or `"codex"`).
        errors: Human-readable error strings; empty when `ok=True`.
    """

    ok: bool
    runtime: str
    errors: List[str] = field(default_factory=list)


# ---- minimal frontmatter parser (no PyYAML dependency) ----

_FRONTMATTER_OPEN = re.compile(r"^---\s*$")
_FRONTMATTER_KV = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")


def _parse_frontmatter(md_text: str) -> dict:
    """Parse the YAML-style frontmatter between two `---` markers.

    Supports the subset used by Claude Code and Codex skills:
      - top-level `key: value` (scalar string by default)
      - top-level `key:` followed by indented child `key: value` lines
        (the parent becomes a dict; children are merged into it)
      - single-line JSON array/object value (e.g. `metadata: {"k":"v"}`)

    Returns an empty dict if the file has no opening `---` marker.

    PR #40 review (🟠 major, followup fix): previously, a top-level
    `metadata:` (no scalar value) was rendered as the empty string
    `""`, so indented children were silently dropped. Now: when a
    top-level key has no scalar value AND indented children follow,
    we initialize the key as an empty dict and merge children into it.
    """
    lines = md_text.splitlines()
    if not lines or not _FRONTMATTER_OPEN.match(lines[0]):
        return {}

    out: dict = {}
    current_top: str | None = None
    closed = False
    has_indented_children_remaining = False
    for raw in lines[1:]:
        if _FRONTMATTER_OPEN.match(raw):
            closed = True
            break
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = _FRONTMATTER_KV.match(raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if not raw.startswith((" ", "\t")):
            # top-level key
            current_top = key
            if value == "":
                # defer: an empty value at a top-level key may be a
                # nested-block opener; do not assign until we know.
                out[key] = None  # sentinel
            else:
                out[key] = _coerce_scalar(value)
        else:
            has_indented_children_remaining = True
            # Indented child. Promote a pending None parent to a dict.
            if current_top is not None and out.get(current_top) is None:
                out[current_top] = {}
            # Indented child of current_top; collect into dict at that key
            if current_top is None or not isinstance(out.get(current_top), dict):
                continue
            out[current_top][key] = _coerce_scalar(value)
    if not closed:
        return {}
    # Drop sentinel parents that never received indented children — they
    # were empty top-level scalars after all.
    for k in [k for k, v in out.items() if v is None]:
        del out[k]
    return out


def _coerce_scalar(value: str):
    """Best-effort scalar coercion for top-level values.

    Try JSON first (handles strings with quotes, numbers, booleans, null,
    single-line lists/objects). Fall back to raw string with surrounding
    quotes stripped.
    """
    if value == "":
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _extract_errors(exc: jsonschema.ValidationError) -> List[str]:
    """Format a single jsonschema ValidationError as a human-readable string.

    The caller already iterates errors via `validator.iter_errors()`; this
    helper renders ONE error per call. (Previously fed `ErrorTree(exc)` which
    expects an iterable of errors, not a single error.)
    """
    path = "/".join(str(p) for p in exc.absolute_path) or "<root>"
    return [f"{path}: {exc.message}"] if exc.message else ["<empty error message>"]


def _format_error(exc: jsonschema.ValidationError) -> str:
    """Single-line rendering of one jsonschema ValidationError."""
    path = "/".join(str(p) for p in exc.absolute_path) or "<root>"
    return f"{path}: {exc.message}"


# ---- public API ----

def validate_skill_md(path: Path, runtime: Literal["cc", "codex"]) -> ValidationReport:
    """Validate the frontmatter of a SKILL.md against the given runtime's spec.

    Args:
        path: Path to a Markdown file with YAML frontmatter between `---` markers.
        runtime: Which vendored schema to validate against (`"cc"` or `"codex"`).

    Returns:
        ValidationReport with `ok`, `runtime`, and `errors`. Never raises for
        malformed or missing files — failures are reported in `errors`.
    """
    report = ValidationReport(ok=False, runtime=runtime)
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        report.errors.append(f"file not found: {path}")
        return report
    except OSError as e:
        report.errors.append(f"could not read file: {e}")
        return report

    frontmatter = _parse_frontmatter(text)
    if not frontmatter:
        report.errors.append("missing YAML frontmatter (no opening `---` marker found)")
        return report

    # Substring prohibition (non-goal b).
    desc = frontmatter.get("description", "")
    if not isinstance(desc, str):
        report.errors.append("`description` must be a string")
    else:
        for needle in FORBIDDEN_SUBSTRINGS:
            if needle in desc:
                report.errors.append(f"`description` contains forbidden substring {needle!r}")

    # Schema validation.
    spec = load_spec(runtime)
    validator = jsonschema.Draft7Validator(spec)
    schema_errors = sorted(validator.iter_errors(frontmatter), key=lambda e: list(e.absolute_path))
    for e in schema_errors:
        report.errors.extend(_extract_errors(e))

    report.ok = not report.errors
    return report
