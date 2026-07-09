"""End-to-end test for the full dual-runtime pipeline.

Proves the integration claim end-to-end:

    interview (mode A, scripted) → assemble → emit → validate →
    cc_adapter.register → codex_adapter.register → runtime-parity

Each step is exposed as a single pytest case so a regression names
the failing stage in the pytest summary instead of one giant
"AssertionError" traceback.
"""
from __future__ import annotations

import pathlib

import pytest

from tests.e2e.pipeline import run_e2e_pipeline


@pytest.fixture()
def plugin_output(tmp_path) -> pathlib.Path:
    output_dir = tmp_path / "plugin"
    yield output_dir
    # tmp_path is auto-cleaned by pytest; nothing else to do.


def test_full_pipeline_emits_valid_plugin(plugin_output: pathlib.Path) -> None:
    """Full 7-step pipeline (interview → parity) completes without error."""
    summary = run_e2e_pipeline(plugin_output)

    # 1+2+3: interview → assemble → emit.
    assert summary["state"].is_complete(), "interview state should be complete"
    assert summary["plan"], "assembled plan should be non-empty"
    assert summary["report"].ok, (
        f"validate_emit failed: {'; '.join(summary['report'].errors)}"
    )

    # 4: emitter wrote all four product files into plugin_output/src/.
    src = plugin_output / "src"
    assert (src / ".codex-plugin" / "plugin.json").is_file(), \
        "missing emitted plugin.json"
    assert (src / ".mcp.json").is_file(), "missing emitted .mcp.json"
    assert (src / "skills").is_dir(), "missing emitted skills/ directory"
    assert (plugin_output / "README.md").is_file(), "missing emitted README.md"

    # 5+6: both runtime adapters installed under their canonical paths
    # (CC under .claude/, Codex under .agents/ per the Codex skill spec).
    assert (plugin_output / ".claude" / "commands" / "plugin-harness.md").is_file(), \
        "CC slash command missing"
    assert (plugin_output / ".claude" / "skills" / "plugin-harness" / "SKILL.md").is_file(), \
        "CC skill missing"
    assert (plugin_output / ".agents" / "skills" / "plugin-harness" / "SKILL.md").is_file(), \
        "Codex skill missing"


def test_full_pipeline_runtime_parity(plugin_output: pathlib.Path) -> None:
    """The dual-runtime contract: CC skill body == Codex skill body.

    Both files are installed by their respective adapter in this
    single run, so parity is checked against the actual emitted
    artifacts (not pre-bundled fixtures). The contract is byte-for-byte
    identity of the bodies (after YAML front-matter).
    """
    run_e2e_pipeline(plugin_output)

    cc_skill = (plugin_output / ".claude" / "skills" / "plugin-harness" / "SKILL.md")
    codex_skill = (plugin_output / ".agents" / "skills" / "plugin-harness" / "SKILL.md")
    cc_text = cc_skill.read_text(encoding="utf-8")
    codex_text = codex_skill.read_text(encoding="utf-8")

    # Strip front-matter (both files have a `---`-bounded YAML block at the top).
    def _body(s: str) -> str:
        lines = s.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            return s
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "".join(lines[i + 1:])
        return s

    cc_body = _body(cc_text)
    codex_body = _body(codex_text)
    assert cc_body == codex_body, (
        f"runtime parity violated: CC body ({len(cc_body)} bytes) != "
        f"Codex body ({len(codex_body)} bytes)"
    )

    # Sanity: the front-matters differ by convention; only the bodies match.
    assert cc_text != codex_text, (
        "expected CC and Codex SKILL.md to differ in front-matter; "
        "if these are now byte-identical, the dual-runtime contract "
        "test is weakened — bodies alone should be compared"
    )


# ---------- PR #27 review regression ----------
def test_cc_and_codex_skill_bodies_byte_identical_post_frontmatter():
    """🟠 major: dual-runtime SKILL.md bodies must be byte-identical
    after front-matter stripping. This is the e2e parity contract.
    """
    cc = pathlib.Path("/Users/sanghee/dev/plugin-harness/.claude/worktrees/0-mvp-step6/src/adapter/cc_skills/plugin-harness/SKILL.md")
    cx = pathlib.Path("/Users/sanghee/dev/plugin-harness/.claude/worktrees/0-mvp-step6/src/adapter/codex_skills/plugin-harness/SKILL.md")
    assert cc.is_file() and cx.is_file()

    def _body(t):
        lines = t.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            return t
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "".join(lines[i + 1:])
        return t

    cc_body = _body(cc.read_text(encoding="utf-8"))
    cx_body = _body(cx.read_text(encoding="utf-8"))
    assert cc_body == cx_body, (
        f"CC body ({len(cc_body)}) != Codex body ({len(cx_body)})"
    )
