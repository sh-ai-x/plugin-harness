"""Tests for src/skill_schema/{loader,validator}.py.

Iron Law L1 (no prod code without tests): tests written first; this file
predates src/skill_schema/. Tests are RED until the implementation lands.
"""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

CC_VALID = FIXTURES / "cc_skill_valid.md"
CC_INVALID_NAME = FIXTURES / "cc_skill_invalid_name.md"
CC_INVALID_DEVKIT = FIXTURES / "cc_skill_invalid_devkit.md"
CODEX_VALID = FIXTURES / "codex_skill_valid.md"
CODEX_INVALID_METADATA = FIXTURES / "codex_skill_invalid_metadata.md"


# ---------- load_spec ----------

def test_load_spec_cc_returns_object_schema():
    from src.skill_schema.loader import load_spec
    spec = load_spec("cc")
    assert spec["type"] == "object"
    assert "name" in spec["required"]
    assert "description" in spec["required"]


def test_load_spec_codex_returns_object_schema():
    from src.skill_schema.loader import load_spec
    spec = load_spec("codex")
    assert spec["type"] == "object"
    assert "name" in spec["required"]
    assert "description" in spec["required"]


def test_load_spec_unknown_runtime_raises():
    from src.skill_schema.loader import load_spec
    with pytest.raises((KeyError, ValueError)):
        load_spec("not-a-runtime")


# ---------- validate_skill_md ----------

def test_validate_cc_valid_is_ok():
    from src.skill_schema.validator import validate_skill_md
    r = validate_skill_md(CC_VALID, "cc")
    assert r.ok
    assert r.runtime == "cc"
    assert r.errors == []


def test_validate_codex_valid_is_ok():
    from src.skill_schema.validator import validate_skill_md
    r = validate_skill_md(CODEX_VALID, "codex")
    assert r.ok
    assert r.runtime == "codex"
    assert r.errors == []


def test_validate_cc_invalid_name_rejected_with_name_in_errors():
    from src.skill_schema.validator import validate_skill_md
    r = validate_skill_md(CC_INVALID_NAME, "cc")
    assert not r.ok
    assert r.runtime == "cc"
    assert any("name" in e.lower() for e in r.errors), f"errors: {r.errors}"


def test_validate_cc_invalid_devkit_rejected_by_validator_substring_check():
    """`dev-kit` substring is enforced by validator.py, not the JSON Schema."""
    from src.skill_schema.validator import validate_skill_md
    r = validate_skill_md(CC_INVALID_DEVKIT, "cc")
    assert not r.ok
    assert any("dev-kit" in e for e in r.errors), f"errors: {r.errors}"


def test_validate_codex_invalid_metadata_rejected_with_metadata_in_errors():
    from src.skill_schema.validator import validate_skill_md
    r = validate_skill_md(CODEX_INVALID_METADATA, "codex")
    assert not r.ok
    assert r.runtime == "codex"
    assert any("metadata" in e.lower() for e in r.errors), f"errors: {r.errors}"


def test_validate_runtime_mismatch_uses_specified_runtime():
    """Validating a CC file with `runtime='codex'` is allowed but uses the
    Codex spec; the file's content matches either spec here, so both pass."""
    from src.skill_schema.validator import validate_skill_md
    r_cc = validate_skill_md(CC_VALID, "cc")
    r_cx = validate_skill_md(CC_VALID, "codex")
    # CC_VALID has no metadata block, so it satisfies both CC and Codex schemas.
    # But the runtime tag must reflect what was passed, not the file path.
    assert r_cc.runtime == "cc"
    assert r_cx.runtime == "codex"


def test_validate_missing_file_raises_or_returns_error():
    """A non-existent path must NOT crash; the validator returns a typed error."""
    from src.skill_schema.validator import validate_skill_md
    missing = FIXTURES / "does_not_exist.md"
    r = validate_skill_md(missing, "cc")
    assert not r.ok
    assert any("not found" in e.lower() or "no such file" in e.lower() for e in r.errors), \
        f"errors: {r.errors}"
