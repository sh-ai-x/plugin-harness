"""Codex-layout plugin emitter.

Public API:
- `emit(state: InterviewState, plan_md: str, output_dir: Path) -> EmitResult`

Writes 4 files into <output_dir>:
  src/.codex-plugin/plugin.json
  src/skills/<plugin_slug>/SKILL.md
  src/.mcp.json
  README.md

Field derivation (locked):
- `plugin.json.name` → kebab-case from idea plan title
- `plugin.json.version` → constant "0.1.0"
- `plugin.json.description` → from answer to "what-who-where" (first 200 chars)
- `SKILL.md` body → from "how-it-works" + the assembled plan
- `.mcp.json.mcpServers` → empty array
- `README.md` → assembled plan verbatim

Escaping contract:
- JSON-bound user text → json.dumps (transport-escape)
- Markdown-bound user text → `src.emitter._shared.md_escape` (single shared table)
- Template-bound user text → Jinja `| replace("{", "&#123;")` chain (SSTI defense, in templates)

PR #27 LLM review (🟠 major #3): the previous version of this file carried
its own `_md_escape` table that disagreed with `plan.py._escape_markdown`
on (`(`, `)`) coverage and on the `#` representation
(backslash-prefix vs HTML entity). Both files now route through
`md_escape` from `src.emitter._shared.md_escape`.

PR #27 LLM review (🟠 major #4): the previous version duplicated the
output layout (`.codex-plugin/`, `src/skills/<slug>/`, `src/.mcp.json`,
`README.md`) with `validator.py`. The four canonical paths now live in
`src.emitter._shared.layout.CodexLayout`; both files consume it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.emitter._shared.layout import CodexLayout
from src.emitter._shared.md_escape import md_escape

# Backward-compat alias for tests/imports that pre-date the round-13
# refactor (which extracted `_md_escape` to `src.emitter._shared`).
_md_escape = md_escape

from src.schema.state import InterviewState

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates" / "codex"
PLUGIN_VERSION = "0.1.0"
DESCRIPTION_MAX = 200


class EmitError(RuntimeError):
    """Raised when emit cannot produce the 4 product files."""


@dataclass
class EmitResult:
    plugin_json: Path
    skill_md: Path
    mcp_json: Path
    readme: Path


# --------------------------------------------------------------------- helpers
def _derive_plugin_name(plan_md: str) -> str:
    """Pull the first H1 from the plan (stripped of leading '#') and kebab-case it.

    Falls back to "plugin" when no H1 is present.
    """
    match = re.search(r"^#\s+(.+?)\s*$", plan_md, flags=re.MULTILINE)
    raw = match.group(1) if match else "plugin"
    # strip markdown emphasis / punctuation / unicode dashes
    raw = re.sub(r"[`*_~]", "", raw)
    raw = raw.replace("—", "-").replace("–", "-")
    # collapse any non-[a-z0-9] run into a single hyphen
    kebab = re.sub(r"[^a-zA-Z0-9]+", "-", raw).strip("-").lower()
    # collapse leading/trailing hyphens and limit length
    kebab = re.sub(r"-+", "-", kebab).strip("-")[:64].strip("-")
    if not kebab:
        kebab = "plugin"
    # schema pattern: ^[a-z0-9][a-z0-9-]{1,63}$  →  2-64 chars, start alphanumeric
    if not re.match(r"^[a-z0-9]", kebab):
        kebab = "p-" + kebab
        kebab = kebab[:64].strip("-")
    # PR #27 round 8 (🟠 major): enforce 2-char minimum so the result
    # matches the vendored schema pattern `^[a-z0-9][a-z0-9-]{1,63}$`
    # (2-64 chars, starts alphanumeric). A 1-char kebab (e.g. 'p-a')
    # survives the alpha-prefix check but fails the length minimum.
    if len(kebab) < 2:
        kebab = "plugin"
    return kebab or "plugin"


# --------------------------------------------------------------------- emit
def emit(state: InterviewState, plan_md: str, output_dir: Path) -> EmitResult:
    if not state.is_complete():
        raise EmitError(
            f"cannot emit: interview incomplete (have {len(state.answers)}/5 answers)"
        )
    if "what-who-where" not in state.answers:
        raise EmitError("missing required answer: what-who-where")
    if "how-it-works" not in state.answers:
        raise EmitError("missing required answer: how-it-works")

    plugin_name = _derive_plugin_name(plan_md)
    plugin_slug = plugin_name  # identical to name; schema requires same pattern

    description_raw = state.answers["what-who-where"]
    description = description_raw[:DESCRIPTION_MAX]

    how_it_works = state.answers["how-it-works"]
    plan_body = plan_md

    # ------------------------------------------------------------------ layout
    # PR #27 LLM review (🟠 major #4): the four canonical Codex output
    # paths are now sourced from a single CodexLayout instance. The
    # validator.py side reads from the same class, so adding a fifth
    # file in either file is no longer a hand-matched edit.
    layout = CodexLayout(output_dir=output_dir, plugin_slug=plugin_slug)

    # Idempotency: clear stale emitted files (but keep output_dir itself).
    # If the previous run used a different plugin slug, its skill directory must also go.
    for stale in (
        layout.plugin_json,
        layout.skill_md,
        layout.mcp_json,
        layout.readme,
    ):
        if stale.exists():
            stale.unlink()
    if layout.skills_root.is_dir():
        for old_slug_dir in layout.skills_root.iterdir():
            if old_slug_dir.is_dir() and old_slug_dir.name != plugin_slug:
                # recursively remove the previous slug directory
                for child in old_slug_dir.rglob("*"):
                    if child.is_file():
                        child.unlink()
                for child_dir in sorted(old_slug_dir.rglob("*"), reverse=True):
                    if child_dir.is_dir():
                        child_dir.rmdir()
                old_slug_dir.rmdir()

    layout.codex_dir.mkdir(parents=True, exist_ok=True)
    layout.skill_dir.mkdir(parents=True, exist_ok=True)
    layout.codex_dir.parent.mkdir(parents=True, exist_ok=True)  # <output_dir>/src

    # ------------------------------------------------------------------ render
    # Autoescape is OFF at the Jinja level: the shared `md_escape` already
    # applies both Markdown backslash escape AND HTML entity escape. Adding
    # Jinja's `|e` on top would re-escape our `&` (`&lt;` → `&amp;lt;`).
    # SSTI defense still holds because user text reaches the template as a
    # Python value (not as template source) — Jinja will not re-evaluate
    # `{{ user_text }}` inside the value.
    # PR #27 review A05 (🟡 minor): SSTI defense-in-depth. The reviewer's
    # recommendation was autoescape=True, but enabling autoescape breaks
    # the existing test_markdown_injection_escaped assertion (which expects
    # the specific backslash-greater Markdown-blockquote escape, not
    # Jinja2's HTML entity escape &gt;). Switching to autoescape would
    # require changing the test contract; deferring. SSTI defense
    # continues to rely on the per-template replace chain in
    # SKILL.md.j2 (replace open-brace with &#123; etc.) — the same
    # primary defense the reviewer accepted as workable.
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
    )

    # plugin.json: pre-build a dict, json.dumps for transport-escape (handles JSON injection).
    plugin_payload = {
        "name": plugin_name,
        "version": PLUGIN_VERSION,
        "description": description,
        "skills": [plugin_slug],
    }
    plugin_json_text = json.dumps(plugin_payload, indent=2, ensure_ascii=False) + "\n"
    # PR #27 round 7 (🟠 major): removed the dev-kit guard from
    # plugin.json output. The 'description' field is user-derived and
    # a user's legitimate plugin description containing the literal
    # 'dev-kit' (e.g. "generates dev-kit scaffolding") would falsely
    # trip the check and emit a confusing failure. The dev-kit
    # sentinel is reserved for emitted SOURCE files where the
    # emitter itself controls the content (the bundled SKILL.md
    # template is emitter-controlled and still checked below).

    layout.plugin_json.write_text(plugin_json_text, encoding="utf-8")

    # SKILL.md: Markdown-escape user input, then render template with
    # `| replace("{", "&#123;")` (SSTI defense; the template does NOT
    # auto-escape).
    #
    # PR #27 LLM review (🟠 major #3): `plan_body` is the assembled plan
    # from `assembler/plan.py`, which already runs each user-supplied
    # answer through `md_escape` before interpolation. Re-running
    # `md_escape` here would drift the output against the assembler's
    # intent (because the two functions previously disagreed on
    # `(` / `)` and `#`). Pass the assembled plan through verbatim.
    skill_tpl = env.get_template("SKILL.md.j2")
    skill_md_text = skill_tpl.render(
        plugin_slug=plugin_slug,
        description=md_escape(description),
        how_it_works=md_escape(how_it_works),
        plan=plan_body,
    )
    if "dev-kit" in skill_md_text:
        raise EmitError("forbidden token 'dev-kit' detected in SKILL.md output")

    layout.skill_md.write_text(skill_md_text, encoding="utf-8")

    # .mcp.json: static template, no user input.
    mcp_tpl = env.get_template("mcp.json.j2")
    mcp_json_text = mcp_tpl.render()
    layout.mcp_json.write_text(mcp_json_text, encoding="utf-8")

    # README.md: the assembled plan IS user content, and the assembler
    # has already markdown-escaped each section. Escape once at template
    # substitution time (no `| replace` chain on the README template
    # side; the `| replace` SSTI chain only protects SKILL.md).
    readme_tpl = env.get_template("README.md.j2")
    # PR #27 round 7 (🟠 major): removed the dev-kit guard from
    # README.md. README is the assembled plan (user content, already
    # Markdown-escaped); a user writing about their dev-kit
    # workflow would falsely trip the check.
    readme_text = readme_tpl.render(plan=plan_body)

    layout.readme.write_text(readme_text, encoding="utf-8")

    return EmitResult(
        plugin_json=layout.plugin_json,
        skill_md=layout.skill_md,
        mcp_json=layout.mcp_json,
        readme=layout.readme,
    )
