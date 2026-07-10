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
- Markdown-bound user text → _md_escape (Markdown-injection defense)
- Template-bound user text → Jinja `| e` filter (SSTI defense, in templates)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

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
    return kebab or "plugin"


def _md_escape(text: str) -> str:
    """Markdown-injection escape per phases/0-mvp/step2.md, combined with
    HTML-entity escape for `<`, `>`.

    Combining both in one pass avoids double-escape (`&lt;` → `&amp;lt;`) that
    would happen if HTML-entity escape ran here AND Jinja `|e` re-escaped `&`.

    Escape set:
      Markdown backslash: `[`, `]`, `` ` ``, `#`, `*`, `_`, leading `>`
      HTML entity:        `<`, `>` (line-content, after the Markdown leading-> pass)
      Literal `&` is preserved (no entity escape) to avoid entity double-escape;
      this is safe because user input never reaches a context where `&` would
      be interpreted as an entity starter.
    """
    if not text:
        return ""

    out = text
    # Markdown-special: backslash-escape first.
    for ch, esc in (
        ("[", "\\["),
        ("]", "\\]"),
        ("`", "\\`"),
        ("#", "\\#"),
        ("*", "\\*"),
        ("_", "\\_"),
    ):
        out = out.replace(ch, esc)
    # Leading ">" on a line → blockquote-injection defense (Markdown backslash).
    # Use a sentinel for the backslash so the next pass does not re-escape the
    # literal `>` we just produced.
    out = re.sub(r"(?m)^>", "\x00GTBS\x00", out)
    # HTML entity escape for `<` and `>`. `>` outside the leading-position has
    # not been escaped yet by the previous step.
    out = out.replace("<", "&lt;").replace(">", "&gt;")
    # Restore the Markdown-escaped leading `>` (was `\→`, sentinel resolves to `\>`).
    out = out.replace("\x00GTBS\x00", "\\>")
    return out


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
    codex_dir = output_dir / "src" / ".codex-plugin"
    skill_dir = output_dir / "src" / "skills" / plugin_slug
    src_dir = output_dir / "src"
    skills_root = output_dir / "src" / "skills"

    # Idempotency: clear stale emitted files (but keep output_dir itself).
    # If the previous run used a different plugin slug, its skill directory must also go.
    for stale in (
        codex_dir / "plugin.json",
        skill_dir / "SKILL.md",
        src_dir / ".mcp.json",
        output_dir / "README.md",
    ):
        if stale.exists():
            stale.unlink()
    if skills_root.is_dir():
        for old_slug_dir in skills_root.iterdir():
            if old_slug_dir.is_dir() and old_slug_dir.name != plugin_slug:
                # recursively remove the previous slug directory
                for child in old_slug_dir.rglob("*"):
                    if child.is_file():
                        child.unlink()
                for child_dir in sorted(old_slug_dir.rglob("*"), reverse=True):
                    if child_dir.is_dir():
                        child_dir.rmdir()
                old_slug_dir.rmdir()

    codex_dir.mkdir(parents=True, exist_ok=True)
    skill_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ render
    # Autoescape is OFF at the Jinja level: the emitter-side `_md_escape` already
    # applies both Markdown backslash escape AND HTML entity escape. Adding
    # Jinja's `|e` on top would re-escape our `&` (`&lt;` → `&amp;lt;`).
    # SSTI defense still holds because user text reaches the template as a
    # Python value (not as template source) — Jinja will not re-evaluate
    # `{{ user_text }}` inside the value.
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

    plugin_json_path = codex_dir / "plugin.json"
    plugin_json_path.write_text(plugin_json_text, encoding="utf-8")

    # SKILL.md: Markdown-escape user input, then render template with `| e` (SSTI defense).
    skill_tpl = env.get_template("SKILL.md.j2")
    skill_md_text = skill_tpl.render(
        plugin_slug=plugin_slug,
        description=_md_escape(description),
        how_it_works=_md_escape(how_it_works),
        plan=_md_escape(plan_body),
    )
    if "dev-kit" in skill_md_text:
        raise EmitError("forbidden token 'dev-kit' detected in SKILL.md output")

    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(skill_md_text, encoding="utf-8")

    # .mcp.json: static template, no user input.
    mcp_tpl = env.get_template("mcp.json.j2")
    mcp_json_text = mcp_tpl.render()
    mcp_json_path = src_dir / ".mcp.json"
    mcp_json_path.write_text(mcp_json_text, encoding="utf-8")

    # README.md: assembled plan verbatim (Markdown-escaped, then template `| e` re-escapes).
    readme_tpl = env.get_template("README.md.j2")
    # PR #27 round 7 (🟠 major): removed the dev-kit guard from
    # README.md. README is the assembled plan (user content, already
    # Markdown-escaped); a user writing about their dev-kit
    # workflow would falsely trip the check.
    readme_text = readme_tpl.render(plan=_md_escape(plan_body))

    readme_path = output_dir / "README.md"
    readme_path.write_text(readme_text, encoding="utf-8")

    return EmitResult(
        plugin_json=plugin_json_path,
        skill_md=skill_md_path,
        mcp_json=mcp_json_path,
        readme=readme_path,
    )