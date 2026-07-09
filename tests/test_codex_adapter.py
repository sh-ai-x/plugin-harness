"""Tests for the Codex adapter.

Verifies `register_codex` installs the skill at the Codex-expected path
(`.agents/skills/plugin-harness/SKILL.md` per
https://developers.openai.com/codex/skills), content sanity, idempotency,
no "dev-kit" references, and that the skill points at the shared engine
entrypoint (`python -m src.engine.cli`).
"""

from __future__ import annotations

import os
import pathlib
import tempfile
from pathlib import Path

import pytest

from src.adapter.codex import register_codex


CODEX_SKILL_PATH = Path(".agents/skills/plugin-harness/SKILL.md")
EXPECTED_FIXTURE = Path(
    "tests/fixtures/codex_install/expected/.agents/skills/plugin-harness/SKILL.md"
)


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


def test_skill_matches_expected_fixture() -> None:
    """Emitted SKILL.md matches the checked-in expected fixture."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        register_codex(project_dir)
        emitted = (project_dir / CODEX_SKILL_PATH).read_text()
        expected = EXPECTED_FIXTURE.read_text()
        assert emitted == expected, "emitted SKILL.md drifted from fixture"


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


# ---------- PR #26 review regression: A06 majors ----------
def test_register_codex_refuses_symlink_under_project():
    """A06-3: refuse the install if any path under the project is a symlink."""
    import pytest
    with tempfile.TemporaryDirectory() as td:
        project = pathlib.Path(td)
        # Pre-plant a symlink at the target SKILL.md path
        skill_dir = project / ".agents" / "skills" / "plugin-harness"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.symlink_to("/etc/passwd")
        with pytest.raises(FileExistsError, match="refusing to write through symlink"):
            register_codex(project)


def test_register_codex_atomic_write_creates_no_tempfile_residue():
    """A06-1: success path leaves no .tmp residue under the project."""
    with tempfile.TemporaryDirectory() as td:
        project = pathlib.Path(td)
        register_codex(project)
        residual = list((project / ".agents").rglob("*.tmp"))
        assert residual == [], f"unexpected tempfile residue: {residual}"


def test_register_codex_explicit_file_mode_0o644(tmp_path):
    """A02 minor: explicit mode 0o644 — not world-writable under permissive umask."""
    old_umask = os.umask(0o000)  # worst-case permissive
    try:
        register_codex(tmp_path)
        skill = tmp_path / ".agents" / "skills" / "plugin-harness" / "SKILL.md"
        mode = skill.stat().st_mode & 0o777
        assert mode == 0o644, f"expected 0o644, got {oct(mode)}"
    finally:
        os.umask(old_umask)


def test_register_codex_backup_prior_when_file_exists():
    """A06-2: a pre-existing SKILL.md is preserved as a .bak.<ts> sibling."""
    import re
    with tempfile.TemporaryDirectory() as td:
        project = pathlib.Path(td)
        skill_dir = project / ".agents" / "skills" / "plugin-harness"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("hand-authored content", encoding="utf-8")
        register_codex(project)
        # The new SKILL.md reflects the bundled install; the prior is preserved
        backups = list(skill_dir.glob("SKILL.md.bak.*"))
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == "hand-authored content"
