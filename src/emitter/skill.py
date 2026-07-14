"""skill.py — dual-runtime SKILL.md emitter for the skill_create sub-mode.

Public API:
    emit(state: SkillInterviewState, output_dir: Path) -> EmitResult

Writes TWO files into the output directory:
    <output_dir>/.claude/skills/<slug>/SKILL.md   (Claude Code layout)
    <output_dir>/.codex/skills/<slug>/SKILL.md   (Codex layout)

Both files share the same body. The frontmatter differs only in shape
(CC: `name` + `description`; Codex: same fields, validator-compat).
Both are validated against the vendored schemas from step 0
(`docs/cc-skill.schema.json`, `docs/codex-skill.schema.json`) and
against the substring rule (no `dev-kit`).

Idempotency: re-running emit on the same `output_dir` overwrites the
two files in place; no extra files are created.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.engine.modes.skill_create import SkillInterviewState
from src.skill_schema.validator import validate_skill_md


class EmitError(RuntimeError):
    """Raised when emit cannot produce the two product files."""


@dataclass
class EmitResult:
    """Result of `emit_skill(state, output_dir)`. """
    cc_path: Path
    codex_path: Path


SLUG_PREFIX_KEYWORDS = (
    "the", "a", "an", "of", "for", "to", "into", "with", "by", "on", "at",
)


def _slug_from_purpose(purpose: str) -> str:
    """Derive a deterministic slug from the `purpose` answer.

    First 5 alphabetic tokens, lowercased, joined with hyphens. Articles and
    prepositions (the/a/an/for/to/with/...) are stripped from the front so the
    slug opens with the noun phrase. Falls back to "skill" if the purpose
    yields no usable tokens.
    """
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]*", purpose)
    out: list[str] = []
    for t in tokens:
        if not out and t.lower() in SLUG_PREFIX_KEYWORDS:
            continue
        out.append(t)
        if len(out) >= 5:
            break
    slug = "-".join(t.lower() for t in out) or "skill"
    # Trim trailing punctuation/whitespace; clamp to schema's 64-char limit.
    slug = re.sub(r"-+$", "", slug)
    return slug[:64].rstrip("-")


def _md_escape(text: str) -> str:
    """Markdown backslash escape for the subset emitted into SKILL.md."""
    if not text:
        return ""
    out = text
    for ch in ("[", "]", "`", "#", "*", "_"):
        out = out.replace(ch, "\\" + ch)
    return out


def _render_cc_skill(name: str, description: str, body: str) -> str:
    """Render the CC-layout SKILL.md (frontmatter + body)."""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n\n"
        f"{body}\n"
    )


def _render_codex_skill(name: str, description: str, body: str, metadata: dict | None = None) -> str:
    """Render the Codex-layout SKILL.md. Optional metadata block is emitted as YAML."""
    if metadata is None:
        header = (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            "---\n\n"
        )
    else:
        meta_lines = "\n".join(f"  {k}: {v!r}" if isinstance(v, str) else f"  {k}: {v}"
                                for k, v in metadata.items())
        header = (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            "metadata:\n"
            f"{meta_lines}\n"
            "---\n\n"
        )
    return header + f"# {name}\n\n{body}\n"


def emit(state: SkillInterviewState, output_dir: Path) -> EmitResult:
    """Emit dual-runtime SKILL.md files. Idempotent on re-run.

    Args:
        state: a completed SkillInterviewState with answers for
               `purpose`, `examples`, `success-criteria`.
        output_dir: destination directory; created if missing.

    Returns:
        EmitResult with paths to the two emitted files.

    Raises:
        EmitError: if the interview is incomplete, required answers
                   are missing, or either emitted file fails validation
                   against the vendored schema.
    """
    if not state.is_complete():
        raise EmitError(
            f"cannot emit: interview incomplete (have {len(state.answers)}/3 answers)"
        )
    for required in ("purpose", "examples", "success-criteria"):
        if required not in state.answers:
            raise EmitError(f"missing required answer: {required}")

    purpose = state.answers["purpose"]
    examples = state.answers["examples"]
    criteria = state.answers["success-criteria"]
    slug = _slug_from_purpose(purpose)

    description = _md_escape(purpose[:500])

    body = "\n\n".join([
        f"## Examples\n\n{_md_escape(examples)}",
        f"## Success criteria\n\n{_md_escape(criteria)}",
    ])

    cc_text = _render_cc_skill(slug, description, body)
    codex_text = _render_codex_skill(slug, description, body)

    cc_dir = output_dir / ".claude" / "skills" / slug
    codex_dir = output_dir / ".codex" / "skills" / slug
    cc_path = cc_dir / "SKILL.md"
    codex_path = codex_dir / "SKILL.md"

    # Validate in-memory rendered text BEFORE writing any file. The validator
    # works on Path objects; we round-trip through a temporary path.
    # Failure here means no files were written — atomic safety net.
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as cc_tmp:
        cc_tmp.write(cc_text)
        cc_tmp_path = Path(cc_tmp.name)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as codex_tmp:
        codex_tmp.write(codex_text)
        codex_tmp_path = Path(codex_tmp.name)

    try:
        cc_report = validate_skill_md(cc_tmp_path, "cc")
        codex_report = validate_skill_md(codex_tmp_path, "codex")
        if not cc_report.ok:
            raise EmitError(
                f"CC SKILL.md failed validation: {cc_report.errors}"
            )
        if not codex_report.ok:
            raise EmitError(
                f"Codex SKILL.md failed validation: {codex_report.errors}"
            )

        # Validation passed; commit to disk.
        cc_dir.mkdir(parents=True, exist_ok=True)
        codex_dir.mkdir(parents=True, exist_ok=True)

        # Idempotency: clear stale slug subtrees (different slugs from prior runs).
        for stale_root in (cc_dir.parent, codex_dir.parent):
            if stale_root.is_dir():
                for child in stale_root.iterdir():
                    if child.is_dir() and child.name != slug:
                        for sub in sorted(child.rglob("*"), reverse=True):
                            if sub.is_file():
                                sub.unlink()
                            elif sub.is_dir():
                                sub.rmdir()
                        child.rmdir()

        cc_path.write_text(cc_text, encoding="utf-8")
        codex_path.write_text(codex_text, encoding="utf-8")
    finally:
        for p in (cc_tmp_path, codex_tmp_path):
            try:
                p.unlink()
            except OSError:
                pass

    return EmitResult(cc_path=cc_path, codex_path=codex_path)


# Backwards-compatible alias for tests/importers that used the older name.
emit_skill = emit
