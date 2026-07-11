"""Quick smoke for the dual-runtime pipeline.

Per step 0 the 5-question contract is locked, so smoke runs the full
interview flow (not an abbreviation): interview → assemble → emit →
validate → cc_adapter.register → codex_adapter.register.

Runtime-parity byte-equality is the e2e-specific proof point and
lives in `test_full_pipeline.py`; smoke stops once both adapters
install and the validator passes, which is enough to catch the most
common regressions during iteration.
"""
from __future__ import annotations

import pathlib

import pytest

from tests.e2e.pipeline import run_smoke_pipeline


@pytest.fixture()
def plugin_output(tmp_path) -> pathlib.Path:
    output_dir = tmp_path / "plugin"
    yield output_dir
    # tmp_path is auto-cleaned by pytest; nothing else to do.


def test_smoke_interview_and_emit(plugin_output: pathlib.Path) -> None:
    """interview → assemble → emit produce a complete plugin layout."""
    summary = run_smoke_pipeline(plugin_output)

    assert summary["state"].is_complete(), \
        "interview state should be complete after scripted 5-question flow"
    assert summary["plan"], "assembled plan should be non-empty"
    assert summary["report"].ok, (
        f"validate_emit failed: {'; '.join(summary['report'].errors)}"
    )

    src = plugin_output / "src"
    assert (src / ".codex-plugin" / "plugin.json").is_file()
    assert (src / ".mcp.json").is_file()
    assert (src / "skills").is_dir()
    assert (plugin_output / "README.md").is_file()


def test_smoke_both_adapters_install(plugin_output: pathlib.Path) -> None:
    """cc_adapter and codex_adapter install under non-overlapping paths."""
    run_smoke_pipeline(plugin_output)

    # CC side.
    assert (plugin_output / ".claude" / "commands" / "plugin-harness.md").is_file()
    assert (plugin_output / ".claude" / "skills" / "plugin-harness" / "SKILL.md").is_file()

    # Codex side (per https://developers.openai.com/codex/skills).
    assert (plugin_output / ".agents" / "skills" / "plugin-harness" / "SKILL.md").is_file()

    # Sanity: install paths do not overlap (no runtime leak).
    cc_skill = plugin_output / ".claude" / "skills" / "plugin-harness" / "SKILL.md"
    codex_skill = plugin_output / ".agents" / "skills" / "plugin-harness" / "SKILL.md"
    assert cc_skill.exists() and codex_skill.exists()
    assert str(cc_skill.resolve()) != str(codex_skill.resolve())
