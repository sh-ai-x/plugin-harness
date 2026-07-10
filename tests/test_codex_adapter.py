"""Tests for the Codex adapter.

Verifies `register_codex` installs the skill at the Codex-expected path
(`.agents/skills/plugin-harness/SKILL.md` per
https://developers.openai.com/codex/skills), content sanity, idempotency,
no "dev-kit" references, and that the skill points at the shared engine
entrypoint (`python -m src.engine.cli`).
"""

from __future__ import annotations

import pathlib
import tempfile
from pathlib import Path

import pytest

from src.adapter.codex import register_codex


CODEX_SKILL_PATH = Path(".agents/skills/plugin-harness/SKILL.md")
def test_register_codex_creates_skill_file() -> None:
    """register_codex MUST create the Codex skill at the expected path."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_codex(project_dir)
        target = project_dir / CODEX_SKILL_PATH
        assert target.is_file(), f"expected skill at {target}"


def test_register_codex_is_idempotent() -> None:
    """Re-running register_codex MUST overwrite (no duplicates, no append)."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_codex(project_dir)
        first = (project_dir / CODEX_SKILL_PATH).read_text()
        register_codex(project_dir)
        # Exactly one SKILL.md under the project (no duplicate writes).
        matches = list(project_dir.rglob("SKILL.md"))
        assert len(matches) == 1, f"expected 1 SKILL.md, found {matches}"
        second = (project_dir / CODEX_SKILL_PATH).read_text()
        assert first == second, "idempotent re-run produced different content"


def test_skill_matches_bundled_reference() -> None:
    """Emitted SKILL.md matches the bundled reference resolved at test
    time via importlib.resources — no on-disk fixture drift (PR #26
    round 7 🟠 major: previous test_skill_matches_expected_fixture
    compared against tests/fixtures/codex_install/expected/.../SKILL.md,
    which was a byte-identical copy of the bundled source and so
    could never detect drift between the two).
    """
    from importlib import resources
    try:
        bundled = (
            resources.files("src.adapter.codex_skills.plugin-harness")
            .joinpath("SKILL.md")
            .read_text(encoding="utf-8")
        )
    except (ModuleNotFoundError, FileNotFoundError):
        here = Path(__file__).resolve().parent.parent
        bundled = (here / "src" / "adapter" / "codex_skills" / "plugin-harness" / "SKILL.md").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_codex(project_dir)
        emitted = (project_dir / CODEX_SKILL_PATH).read_text()
        assert emitted == bundled, "emitted SKILL.md drifted from bundled reference"


def test_skill_invokes_engine_cli() -> None:
    """The skill body MUST point at `python -m src.engine.cli`."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_codex(project_dir)
        body = (project_dir / CODEX_SKILL_PATH).read_text()
        assert "python -m src.engine.cli" in body, (
            "skill must invoke the shared engine entrypoint"
        )


def test_skill_has_codex_frontmatter() -> None:
    """SKILL.md MUST have YAML frontmatter with name + description."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_codex(project_dir)
        body = (project_dir / CODEX_SKILL_PATH).read_text()
        assert body.startswith("---\n"), "missing YAML frontmatter opening"
        assert "\n---\n" in body, "missing YAML frontmatter closing"
        front = body.split("---\n", 2)[1]
        assert "name: plugin-harness" in front, "missing name in frontmatter"
        assert "description:" in front, "missing description in frontmatter"


def test_no_dev_kit_token_in_emitted_skill(tmp_path: Path) -> None:
    """Emitted artifact MUST NOT contain the 'dev-kit' token."""
    register_codex(tmp_path)
    body = (tmp_path / CODEX_SKILL_PATH).read_text()
    assert "dev-kit" not in body.lower(), (
        "skill body must not reference 'dev-kit'"
    )


def test_no_dev_kit_in_adapter_source() -> None:
    """src/adapter/ source MUST NOT contain 'dev-kit' (AC3)."""
    adapter_dir = Path("src/adapter")
    assert adapter_dir.is_dir(), "src/adapter/ should exist"
    offenders: list[str] = []
    for path in adapter_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".md", ".txt", ".yaml", ".yml", ".json"}:
            continue
        text = path.read_text()
        if "dev-kit" in text:
            offenders.append(str(path))
    assert not offenders, f"'dev-kit' found in: {offenders}"


def test_register_codex_accepts_pathlib_path() -> None:
    """register_codex should accept a pathlib.Path (typed API)."""
    import inspect

    sig = inspect.signature(register_codex)
    params = list(sig.parameters.values())
    assert params, "register_codex must declare at least one parameter"
    first = params[0]
    assert first.annotation in (pathlib.Path, "pathlib.Path") or first.name == "project_dir"
