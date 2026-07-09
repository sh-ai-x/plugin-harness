"""Pytest coverage for the dual-runtime plugin emitter (step 3).

Covered scenarios:
- emit() writes the 4 product files into <output_dir>/src and README.md
- validator reports ok=True when all 4 files are well-formed
- validator reports ok=False when files are missing or malformed
- re-running emit on the same output_dir is idempotent (no duplicate files)
- user-supplied text containing Markdown-injection tokens is escaped
- the emitted plugin.json round-trips against the vendored Codex schema
- the emitted .mcp.json uses the `mcpServers` (camelCase) key
- the output never contains the forbidden "dev-kit" string
"""

from __future__ import annotations

import json
import pathlib
import tempfile

import jsonschema
import pytest

from src.emitter.codex import EmitError, _derive_plugin_name, emit
from src.emitter.validator import ValidationReport, validate_emit
from src.schema.state import InterviewState


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "docs" / "codex-plugin.schema.json"

ALL_QUESTIONS = [
    "what-who-where",
    "why-this-problem",
    "how-it-works",
    "ai-usage",
    "how-verified",
]

# Default plan used by emit() — its H1 drives the derived plugin name.
DEFAULT_PLAN = "# Idea Plan — Test Plugin\n\n## 1. What\nbody\n"
DEFAULT_PLUGIN_NAME = _derive_plugin_name(DEFAULT_PLAN)


# --------------------------------------------------------------------- fixtures
@pytest.fixture
def completed_state() -> InterviewState:
    state = InterviewState()
    for qid in ALL_QUESTIONS:
        state.set_answer(qid, ("x" * 30))
    return state


@pytest.fixture
def output_dir() -> pathlib.Path:
    return pathlib.Path(tempfile.mkdtemp(prefix="plugin-emit-"))


# --------------------------------------------------------------------- emit
class TestEmit:
    def test_creates_all_four_product_files(self, completed_state, output_dir):
        emit(completed_state, DEFAULT_PLAN, output_dir)

        plugin_json = output_dir / "src" / ".codex-plugin" / "plugin.json"
        assert plugin_json.is_file(), "plugin.json missing"

        skill_md = output_dir / "src" / "skills" / DEFAULT_PLUGIN_NAME / "SKILL.md"
        assert skill_md.is_file(), "SKILL.md missing"

        mcp_json = output_dir / "src" / ".mcp.json"
        assert mcp_json.is_file(), ".mcp.json missing"

        readme = output_dir / "README.md"
        assert readme.is_file(), "README.md missing"

    def test_plugin_json_has_required_fields(self, completed_state, output_dir):
        emit(completed_state, "# Idea Plan — Foo\n\n## 1. What\nx", output_dir)
        payload = json.loads(
            (output_dir / "src" / ".codex-plugin" / "plugin.json").read_text()
        )
        assert payload["name"], "name must be non-empty"
        assert payload["version"] == "0.1.0"
        assert payload["description"], "description must be non-empty"

    def test_mcp_json_uses_camelcase_mcpservers(self, completed_state, output_dir):
        emit(completed_state, "# Idea Plan\n", output_dir)
        payload = json.loads((output_dir / "src" / ".mcp.json").read_text())
        assert "mcpServers" in payload, "key MUST be camelCase `mcpServers`"
        assert payload["mcpServers"] == []

    def test_readme_is_assembled_plan_verbatim(self, completed_state, output_dir):
        plan = "# Idea Plan — verbatim\n\n## 6. Synthesis\nsomething"
        emit(completed_state, plan, output_dir)
        # Markdown-escape happens before template render, so README.md holds the escaped plan.
        from src.emitter.codex import _md_escape
        assert (output_dir / "README.md").read_text() == _md_escape(plan)

    def test_skill_md_contains_how_it_works_and_plan(self, completed_state, output_dir):
        plan = "# Idea Plan\n\n## plan body\n"
        emit(completed_state, plan, output_dir)
        skill_name = _derive_plugin_name(plan)
        skill = (output_dir / "src" / "skills" / skill_name / "SKILL.md").read_text()
        assert "x" * 30 in skill, "how-it-works answer should appear in SKILL.md"
        assert "Idea Plan" in skill, "assembled plan should appear in SKILL.md"

    def test_idempotent_overwrites_existing_files(self, completed_state, output_dir):
        emit(completed_state, "# plan one", output_dir)
        emit(completed_state, "# plan two", output_dir)

        # No duplicates — exactly one plugin.json, one SKILL.md, one .mcp.json, one README.md
        codex_dir = output_dir / "src" / ".codex-plugin"
        # The plugin name derives from "# plan two" → "plan-two"
        skill_dir = output_dir / "src" / "skills" / "plan-two"
        assert len(list(codex_dir.glob("plugin.json"))) == 1
        assert len(list(skill_dir.glob("SKILL.md"))) == 1
        assert len(list((output_dir / "src").glob(".mcp.json"))) == 1
        assert len(list(output_dir.glob("README.md"))) == 1

        # second emit's README wins (Markdown-escaped form)
        from src.emitter.codex import _md_escape
        assert (output_dir / "README.md").read_text() == _md_escape("# plan two")

    def test_markdown_injection_escaped(self, output_dir):
        evil = (
            "# heading\n"
            "[link](http://x)\n"
            "![img](http://x)\n"
            "`code`\n"
            "*em*\n"
            "_str_\n"
            "> quote\n"
            "<script>alert(1)</script>"
        )
        state = InterviewState()
        state.set_answer("what-who-where", evil)
        for qid in ("why-this-problem", "how-it-works", "ai-usage", "how-verified"):
            state.set_answer(qid, "x" * 30)
        emit(state, "# plan", output_dir)

        skill_name = _derive_plugin_name("# plan")
        skill = (output_dir / "src" / "skills" / skill_name / "SKILL.md").read_text()
        readme = (output_dir / "README.md").read_text()

        # The dangerous tokens must be neutralized in SKILL.md (which carries the user's
        # how-it-works + description = what-who-where). README.md carries the plan
        # only — different escape vectors apply there.
        escaped_forms_skill = [
            ("\\# heading", "hashed heading escape"),
            ("\\[link\\](http://x)", "link escape"),  # `(`, `)` are not in the step-2 escape set
            ("!\\[img\\](http://x)", "image escape"),
            ("\\`code\\`", "code-span escape"),
            ("\\*em\\*", "emphasis escape"),
            ("\\_str\\_", "underscore escape"),
            ("\\> quote", "leading > Markdown blockquote escape"),
            ("&lt;script&gt;", "html tag escape (via Jinja |e autoescape)"),
        ]
        for esc, label in escaped_forms_skill:
            assert esc in skill, f"{label} missing in SKILL.md: {esc!r}"

        # SKILL.md must not contain raw dangerous tokens either.
        assert "<script>" not in skill
        assert "[link](http://x)" not in skill

        # README.md is a verbatim copy of the plan (# plan); inject the evil string
        # into the plan too to test README escape.
        emit(state, evil, output_dir)
        readme = (output_dir / "README.md").read_text()
        for esc, label in escaped_forms_skill:
            assert esc in readme, f"{label} missing in README.md: {esc!r}"
        assert "<script>" not in readme
        assert "[link](http://x)" not in readme

    def test_no_dev_kit_in_emit_generated_structure(self, completed_state, output_dir):
        """The emitter's own templates and structural fields MUST NOT inject 'dev-kit'.
        User-supplied plan text passes through verbatim (it is the user's content).
        This test asserts the scaffold (plugin.json + .mcp.json + the SKILL.md header /
        footer produced by the template, NOT the user's how-it-works answer body)
        is free of dev-kit mentions."""
        emit(completed_state, "# clean plan\n\n## 1. What\nx", output_dir)

        # plugin.json + .mcp.json are fully emitter-generated — must be dev-kit-free.
        plugin_text = (output_dir / "src" / ".codex-plugin" / "plugin.json").read_text()
        mcp_text = (output_dir / "src" / ".mcp.json").read_text()
        assert "dev-kit" not in plugin_text
        assert "dev-kit" not in mcp_text

        # Source: emitter templates must not contain dev-kit (read raw, not rendered).
        from pathlib import Path

        templates_dir = REPO_ROOT / "src" / "emitter" / "templates" / "codex"
        for tpl in templates_dir.glob("*.j2"):
            assert "dev-kit" not in tpl.read_text(), f"forbidden token in template {tpl}"

    def test_emit_raises_on_missing_answer(self, output_dir):
        bad_state = InterviewState()
        bad_state.set_answer("what-who-where", "x" * 30)
        # only 1 of 5 answered
        with pytest.raises(EmitError):
            emit(bad_state, "# plan", output_dir)

    def test_json_injection_escaped(self, output_dir):
        state = InterviewState()
        state.set_answer("what-who-where", "evil\"json\\break-that-is-very-long")
        for qid in ("why-this-problem", "how-it-works", "ai-usage", "how-verified"):
            state.set_answer(qid, "x" * 30)
        emit(state, "# plan", output_dir)
        payload = json.loads(
            (output_dir / "src" / ".codex-plugin" / "plugin.json").read_text()
        )
        # description should contain the raw text intact (JSON-escaped for transport)
        assert "evil" in payload["description"]
        assert "json" in payload["description"]
        assert "break-that-is-very-long" in payload["description"]


# --------------------------------------------------------------------- validator
class TestValidator:
    def test_ok_on_full_emit(self, completed_state, output_dir):
        emit(completed_state, "# plan", output_dir)
        report = validate_emit(output_dir)
        assert report.ok is True
        assert report.errors == []

    def test_fails_on_empty_dir(self):
        empty = pathlib.Path(tempfile.mkdtemp(prefix="plugin-empty-"))
        report = validate_emit(empty)
        assert report.ok is False
        assert any("missing" in e.lower() or "not found" in e.lower() for e in report.errors)

    def test_fails_on_malformed_plugin_json(self, completed_state, output_dir):
        emit(completed_state, "# plan", output_dir)
        # corrupt the plugin.json so it fails schema validation
        bad_path = output_dir / "src" / ".codex-plugin" / "plugin.json"
        bad_path.write_text(json.dumps({"name": "BadName!", "version": "not-semver"}))
        report = validate_emit(output_dir)
        assert report.ok is False
        assert report.errors

    def test_fails_when_mcpservers_key_is_wrong(self, completed_state, output_dir):
        emit(completed_state, "# plan", output_dir)
        # rename the key from mcpServers to servers (non-standard)
        mcp_path = output_dir / "src" / ".mcp.json"
        mcp_path.write_text(json.dumps({"servers": []}))
        report = validate_emit(output_dir)
        assert report.ok is False


# --------------------------------------------------------------------- schema round-trip
class TestSchemaRoundTrip:
    def test_emitted_plugin_json_validates_against_vendored_schema(
        self, completed_state, output_dir
    ):
        emit(completed_state, "# Idea Plan — roundtrip\n\n## 1. What\nx", output_dir)
        schema = json.loads(SCHEMA_PATH.read_text())
        emitted = json.loads(
            (output_dir / "src" / ".codex-plugin" / "plugin.json").read_text()
        )
        # MUST not raise
        jsonschema.validate(emitted, schema)
        assert emitted["version"] == "0.1.0"
        assert emitted["name"]

        mcp = json.loads((output_dir / "src" / ".mcp.json").read_text())
        assert mcp.get("mcpServers") == []


# --------------------------------------------------------------------- SSTI defense
class TestSSTIDefense:
    def test_skill_template_does_not_evaluate_user_input(self):
        """End-to-end SSTI defense: template uses `{{ how_it_works | e }}` (autoescape on);
        the literal `{{7*7}}` user input is rendered as the escaped text and Jinja does
        NOT evaluate it. `49` never appears in the rendered output."""
        from jinja2 import Environment

        env = Environment(autoescape=True)
        template_text = (
            pathlib.Path(__file__).resolve().parents[1]
            / "src"
            / "emitter"
            / "templates"
            / "codex"
            / "SKILL.md.j2"
        ).read_text()
        tpl = env.from_string(template_text)
        rendered = tpl.render(how_it_works="{{7*7}}", plan="# plan")
        assert "49" not in rendered, "Jinja must not evaluate user-supplied `{{7*7}}`"
        assert "{{7*7}}" not in rendered, "autoescape must escape the literal braces"