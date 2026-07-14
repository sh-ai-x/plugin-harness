"""Dual-runtime parity test — the kill condition from Gate 2 cycle 2.

For the same interview answers, the CC SKILL.md and Codex SKILL.md
emitted by `emit_plugin_skill_bundle` must:

  1. Both validate against their respective vendored schemas.
  2. Bodies are byte-equal (after stripping YAML frontmatter).
  3. Frontmatter key sets agree on the locked CC + Codex intersection
     (`name`, `description`); a runtime-specific optional key
     (`metadata` on Codex) may differ.

If any of these fail, the dual-runtime promise is broken and the build
must be `status: blocked`. The hatchet is hard-coded into the contract;
do not soften.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _complete_5q_state():
    """Build a completed 0-mvp InterviewState with sample 5 answers."""
    from src.schema.state import InterviewState
    sample = json.loads(
        Path(__file__).parent.joinpath("fixtures", "skill_creator_sample_answers.json")
        .read_text(encoding="utf-8")
    )
    # The fixture has skill-creator (3) answers — we need 0-mvp's 5.
    s = InterviewState()
    long = "x" * 30
    s.set_answer("what-who-where", "Demonstration purpose sentence about a sample plugin")
    s.advance()
    s.set_answer("why-this-problem", "Sample problem that the user is trying to solve")
    s.advance()
    s.set_answer("how-it-works", "Sample how-it-works flow describing inputs and outputs")
    s.advance()
    s.set_answer("ai-usage", "Sample AI usage explanation describing model calls here")
    s.advance()
    s.set_answer("how-verified", "Sample verification method used to confirm done")
    return s, sample


@pytest.fixture
def two_runtime_artifacts(tmp_path):
    """Run emit_plugin_skill_bundle and yield the (cc_path, codex_path) pair."""
    from src.emitter.plugin_skill_bundle import emit_plugin_skill_bundle
    state, _sample = _complete_5q_state()
    plan_md = (
        "# Sample Plan\n\n"
        "A reproducible idea-plan body for the dual-runtime parity check.\n\n"
        "## 1. What\n\nsample\n\n"
    )
    result = emit_plugin_skill_bundle(
        state, plan_md, tmp_path, skill_slugs=["parity-demo-skill"]
    )
    return result.cc_skill, result.codex_skill


def _strip_frontmatter(text: str) -> str:
    """Return the body of a SKILL.md with the YAML frontmatter (between two
    leading `---` markers) stripped."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end >= 0:
            return text[end + 3 :].lstrip("\n")
    return text


def test_parity_both_files_exist(two_runtime_artifacts):
    cc_path, codex_path = two_runtime_artifacts
    assert cc_path.exists()
    assert codex_path.exists()


def test_parity_both_files_validate_against_their_schemas(two_runtime_artifacts):
    from src.skill_schema.validator import validate_skill_md
    cc_path, codex_path = two_runtime_artifacts
    cc_report = validate_skill_md(cc_path, "cc")
    codex_report = validate_skill_md(codex_path, "codex")
    assert cc_report.ok, cc_report.errors
    assert codex_report.ok, codex_report.errors


def test_parity_bodies_are_byte_equal(two_runtime_artifacts):
    """The kill condition: CC SKILL.md body == Codex SKILL.md body byte-for-byte."""
    cc_path, codex_path = two_runtime_artifacts
    cc_text = cc_path.read_text(encoding="utf-8")
    codex_text = codex_path.read_text(encoding="utf-8")
    cc_body = _strip_frontmatter(cc_text)
    codex_body = _strip_frontmatter(codex_text)
    assert cc_body == codex_body, (
        f"dual-runtime parity broken:\n--- CC body ---\n{cc_body!r}\n"
        f"--- Codex body ---\n{codex_body!r}"
    )


def test_parity_required_top_level_keys_present(two_runtime_artifacts):
    """Both runtimes' SKILL.md files must carry the locked minimum frontmatter:
    `name` and `description`. Runtime-specific optional top-level keys
    (e.g., Codex `metadata:`) are allowed and not compared — the kill
    condition is body byte-equality, not frontmatter shape."""
    cc_path, codex_path = two_runtime_artifacts
    cc_text = cc_path.read_text(encoding="utf-8")
    codex_text = codex_path.read_text(encoding="utf-8")
    import re
    cc_fm = re.match(r"^---\s*\n(.+?)\n---\s*\n", cc_text, re.DOTALL)
    codex_fm = re.match(r"^---\s*\n(.+?)\n---\s*\n", codex_text, re.DOTALL)
    assert cc_fm is not None, f"could not parse CC frontmatter in {cc_text!r}"
    assert codex_fm is not None, f"could not parse Codex frontmatter in {codex_text!r}"
    cc_top_keys = {
        line.split(":", 1)[0].strip()
        for line in cc_fm.group(1).splitlines()
        if ":" in line and not line.startswith((" ", "\t"))
    }
    codex_top_keys = {
        line.split(":", 1)[0].strip()
        for line in codex_fm.group(1).splitlines()
        if ":" in line and not line.startswith((" ", "\t"))
    }
    # Locked minimum: name + description. Missing either → fail.
    for required in ("name", "description"):
        assert required in cc_top_keys, f"CC missing required top-level key {required!r}"
        assert required in codex_top_keys, f"Codex missing required top-level key {required!r}"
    # Both files also validate against step-0's vendored schemas (covered by
    # `test_parity_both_files_validate_against_their_schemas` above); that
    # is the structural contract. This test asserts the minimum frontmatter.


def test_parity_no_devkit_substring_in_either_runtime(two_runtime_artifacts):
    """Both emitted SKILL.md files must not contain the forbidden token."""
    cc_path, codex_path = two_runtime_artifacts
    for path in (cc_path, codex_path):
        text = path.read_text(encoding="utf-8")
        assert "dev-kit" not in text, f"forbidden token in {path}"


def test_parity_skill_creator_submode_also_passes(tmp_path):
    """The same parity condition must hold for `mode=skill_create` (3-question) emit."""
    from src.engine.modes.skill_create import SkillInterviewState
    from src.emitter.skill import emit_skill
    s = SkillInterviewState()
    s.set_answer("purpose", "Demonstration skill purpose sentence here describing intent")
    s.advance()
    s.set_answer("examples", "Demonstration examples invocation pattern shown below")
    s.advance()
    s.set_answer("success-criteria", "Acceptance criteria for done state of this skill")
    s.advance()
    result = emit_skill(s, tmp_path)
    cc_body = _strip_frontmatter(result.cc_path.read_text(encoding="utf-8"))
    codex_body = _strip_frontmatter(result.codex_path.read_text(encoding="utf-8"))
    assert cc_body == codex_body, "skill_create parity broken"
