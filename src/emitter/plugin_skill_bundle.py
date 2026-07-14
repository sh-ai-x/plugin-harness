"""plugin_skill_bundle.py — plugin_create emitter (dual-skill bundle).

Emits the plugin's `plugin.json` + `.mcp.json` + canonical CodeX-layout SKILL.md
(reuses `src.emitter.codex.emit`) AND a dual-runtime skill bundle:
  - `.claude/skills/<slug>/SKILL.md` (CC layout, validated against step-0 CC schema)
  - `.codex/skills/<slug>/SKILL.md` (Codex layout, validated against step-0 Codex schema)

Both new files share a body derived from the assembled idea plan; only the
frontmatter shape differs (per the dual-runtime divergence described in
PRD.md §4 phase 1-skill-creator).

Files to create: this file. Touches:
  - `src/emitter/codex.py` (existing, NOT modified — reused)
  - `src/skill_schema/validator.py` (step-0, NOT modified — consumed)

Non-negotiable rules:
  - `plugin.json` MUST validate against vendored `docs/codex-plugin.schema.json`.
  - Both new CC and Codex SKILL.md files MUST validate against step-0 specs.
  - Re-running emit MUST be idempotent.
  - Output MUST NOT contain "dev-kit" string anywhere.
  - `plugin.json.version` MUST equal "0.1.0".
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from src.emitter.codex import emit as codex_emit
from src.schema.state import InterviewState
from src.skill_schema.validator import validate_skill_md


class EmitError(RuntimeError):
    """Raised when emit cannot produce the bundled artifacts."""


@dataclass
class PluginBundleResult:
    """Result of `emit_plugin_skill_bundle(...)`."""
    plugin_json: Path
    canonical_skill: Path
    cc_skill: Path
    codex_skill: Path
    mcp_json: Path


def _render_cc_skill(name: str, description: str, body: str) -> str:
    """Render the CC-layout SKILL.md frontmatter + body."""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n\n{body}\n"
    )


def _render_codex_skill(name: str, description: str, body: str) -> str:
    """Render the Codex-layout SKILL.md frontmatter + body (no metadata block)."""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name}\n\n{body}\n"
    )


def _write_if_missing(parent: Path, name: str, text: str) -> Path:
    """Atomic-ish write: write to a tmp path, rename into place."""
    final = parent / name
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tmp", delete=False, encoding="utf-8",
        dir=str(parent),
    ) as fp:
        fp.write(text)
        tmp = Path(fp.name)
    tmp.replace(final)
    return final


def emit_plugin_skill_bundle(
    state: InterviewState,
    plan_md: str,
    output_dir: Path,
    skill_slugs: Optional[List[str]] = None,
) -> PluginBundleResult:
    """Emit the 0-mvp plugin layout PLUS a dual-runtime skill bundle.

    The 0-mvp emitter produces the 4 canonical files (plugin.json, mcp.json,
    canonical SKILL.md, README.md). This function wraps that call, then
    additionally emits `<output>/.claude/skills/<slug>/SKILL.md` and
    `<output>/.codex/skills/<slug>/SKILL.md` for each `slug` in
    `skill_slugs`. Both new files validate against step-0 specs.

    Args:
        state: completed 0-mvp InterviewState (5 answers).
        plan_md: assembled idea plan markdown.
        output_dir: destination directory; created if missing.
        skill_slugs: list of skill slug names to bundle. Empty list = no bundle.

    Returns:
        PluginBundleResult with paths to the emitted files.

    Raises:
        EmitError: if the interview is incomplete, the 0-mvp emit fails, or
                   any emitted file fails validation.
    """
    skill_slugs = list(skill_slugs or [])
    if not state.is_complete():
        raise EmitError(
            f"cannot emit: interview incomplete (have {len(state.answers)}/5 answers)"
        )
    if "what-who-where" not in state.answers:
        raise EmitError("missing required answer: what-who-where")
    if "how-it-works" not in state.answers:
        raise EmitError("missing required answer: how-it-works")

    description_raw = state.answers["what-who-where"]
    how_it_works = state.answers["how-it-works"]

    # ---- 0-mvp canonical emit (writes plugin.json + canonical SKILL.md + mcp.json + README) ----
    try:
        canonical = codex_emit(state, plan_md, output_dir)
    except Exception as exc:
        raise EmitError(f"0-mvp canonical emit failed: {exc}") from exc

    # ---- dual-skill bundle (in-memory render first, validate, then commit) ----
    bundle_description = description_raw[:500]
    bundle_body = (
        "## Plan\n\n"
        f"{plan_md}\n\n"
        "## How it works\n\n"
        f"{how_it_works}"
    )

    # Render and validate in memory before any write happens.
    planned_files: list[tuple[Path, str, str]] = []  # (path, runtime, text)
    for slug in skill_slugs:
        cc_text = _render_cc_skill(slug, bundle_description, bundle_body)
        codex_text = _render_codex_skill(slug, bundle_description, bundle_body)

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
                    f"bundle CC SKILL.md for {slug!r} failed validation: {cc_report.errors}"
                )
            if not codex_report.ok:
                raise EmitError(
                    f"bundle Codex SKILL.md for {slug!r} failed validation: {codex_report.errors}"
                )
        finally:
            for p in (cc_tmp_path, codex_tmp_path):
                try:
                    p.unlink()
                except OSError:
                    pass

        # All validated; queue for commit.
        cc_dir = output_dir / ".claude" / "skills" / slug
        codex_dir = output_dir / ".codex" / "skills" / slug
        planned_files.append((cc_dir / "SKILL.md", "cc", cc_text))
        planned_files.append((codex_dir / "SKILL.md", "codex", codex_text))

    # Commit only if every planned file passed validation.
    bundled_paths = []
    for path, _runtime, text in planned_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        bundled_paths.append(path)

    if not bundled_paths:
        # No skill slugs — emit nothing extra. Return 0-mvp paths only.
        # Find the Codex canonical SKILL.md under src/skills/<slug>/SKILL.md
        skill_root = output_dir / "src" / "skills"
        canonical_skill = next(iter(skill_root.rglob("SKILL.md")), Path())
        return PluginBundleResult(
            plugin_json=canonical.plugin_json,
            canonical_skill=canonical_skill,
            cc_skill=canonical_skill,  # alias; bundle was empty
            codex_skill=canonical_skill,
            mcp_json=canonical.mcp_json,
        )

    # We have a bundle. Split into CC and Codex pairs (first emitted per runtime).
    cc_skill = next(p for p, rt, _ in planned_files if rt == "cc")
    codex_skill = next(p for p, rt, _ in planned_files if rt == "codex")
    canonical_skill = next(iter((output_dir / "src" / "skills").rglob("SKILL.md")), cc_skill)

    return PluginBundleResult(
        plugin_json=canonical.plugin_json,
        canonical_skill=canonical_skill,
        cc_skill=cc_skill,
        codex_skill=codex_skill,
        mcp_json=canonical.mcp_json,
    )


emit_plugin_skill_bundle_v1 = emit_plugin_skill_bundle  # backwards-friendly alias
