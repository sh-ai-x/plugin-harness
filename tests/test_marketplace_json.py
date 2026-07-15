"""Tests for `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

Pins the manifest schemas against:
- the [Claude plugin manifest](https://code.claude.com/docs/en/plugins)
- the [Claude marketplace](https://code.claude.com/docs/en/plugin-marketplaces)
- the [Agent Skills](https://agentskills.io) standard for SKILL.md frontmatter

Iron Law L1: tests written first (RED), schema fields verified against the
docs at the time of authoring. Tests are RED if either JSON file is missing
or fails validation.

Two layers of checks per file:
1. **Structural** — JSON parses; required fields present; types correct.
2. **Semantic** — name matches branch convention; version is semver; skills[]
   entries reference real on-disk files; SKILL.md frontmatter is the Agent
   Skills standard shape.

Update these tests when the marketplace.json / plugin.json shape evolves.
The exact field set is the contract; if a field is added or removed,
this test file is the SSOT.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------- helper: simple semver check (no external deps) ----------

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.\-]+)?$")


def _is_semver(s: str) -> bool:
    return bool(_SEMVER_RE.match(s))


def _read_json(rel_path: str) -> dict:
    path = REPO_ROOT / rel_path
    assert path.is_file(), f"missing manifest: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


# ---------- plugin.json: structural ----------

@pytest.fixture(scope="module")
def plugin_manifest() -> dict:
    return _read_json(".claude-plugin/plugin.json")


@pytest.fixture(scope="module")
def codex_plugin_manifest() -> dict:
    return _read_json(".codex-plugin/plugin.json")


def test_plugin_manifest_required_fields(plugin_manifest):
    for field in ("name", "version", "description"):
        assert field in plugin_manifest, f"plugin.json missing required field {field!r}"


def test_plugin_manifest_name_is_kebab(plugin_manifest):
    name = plugin_manifest["name"]
    assert re.match(r"^[a-z0-9][a-z0-9-]*$", name), f"name {name!r} must be kebab-case"


def test_plugin_manifest_version_is_semver(plugin_manifest):
    assert _is_semver(plugin_manifest["version"]), (
        f"version {plugin_manifest['version']!r} is not semver"
    )


def test_plugin_manifest_skills_path_exists(plugin_manifest):
    skills_path = REPO_ROOT / plugin_manifest["skills"].lstrip("./")
    assert skills_path.is_dir(), f"skills path {skills_path} is not a directory"


def test_plugin_manifest_commands_path_exists(plugin_manifest):
    if "commands" not in plugin_manifest:
        pytest.skip("commands/ is optional")
    cmds_path = REPO_ROOT / plugin_manifest["commands"].lstrip("./")
    assert cmds_path.is_dir(), f"commands path {cmds_path} is not a directory"


def test_plugin_manifest_author_has_name(plugin_manifest):
    if "author" in plugin_manifest:
        assert "name" in plugin_manifest["author"], "author must have name"


# ---------- plugin.json: semantic — every skill asset is real ----------

SKILL_NAMES = {"plugin-harness", "skill-creator", "plugin-creator"}


def test_every_skill_directory_exists():
    skills_root = REPO_ROOT / "skills"
    for name in SKILL_NAMES:
        d = skills_root / name
        assert d.is_dir(), f"missing skill dir: {d}"


def test_every_skill_has_cc_layout_SKILL_md():
    skills_root = REPO_ROOT / "skills"
    for name in SKILL_NAMES:
        cc = skills_root / name / "SKILL.md"
        assert cc.is_file(), f"missing CC layout: {cc}"


def test_every_skill_has_codex_layout_companion():
    skills_root = REPO_ROOT / "skills"
    for name in SKILL_NAMES:
        cx = skills_root / name / "SKILL.codex.md"
        assert cx.is_file(), f"missing Codex layout: {cx}"


def test_every_skill_frontmatter_passes_agent_skills_standard():
    """SKILL.md frontmatter must have name + description per the Agent Skills
    standard (referenced by code.claude.com/docs/en/skills). The plugin-harness
    repo's own validator (src/skill_schema/validator.py) is the SSOT — this
    test exercises it on the bundled assets.
    """
    from src.skill_schema.validator import validate_skill_md

    skills_root = REPO_ROOT / "skills"
    for name in SKILL_NAMES:
        cc_report = validate_skill_md(skills_root / name / "SKILL.md", "cc")
        assert cc_report.ok, f"{name}/SKILL.md (CC) failed validation: {cc_report.errors}"


# ---------- commands/new.md frontmatter ----------

def test_new_command_has_required_frontmatter():
    new_path = REPO_ROOT / "commands" / "new.md"
    assert new_path.is_file(), f"missing commands/new.md: {new_path}"
    text = new_path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "commands/new.md must start with YAML frontmatter"
    assert "description:" in text, "commands/new.md must have a description field"


# ---------- marketplace.json: structural ----------

@pytest.fixture(scope="module")
def marketplace_manifest() -> dict:
    return _read_json(".claude-plugin/marketplace.json")


def test_marketplace_manifest_required_fields(marketplace_manifest):
    for field in ("name", "owner", "plugins"):
        assert field in marketplace_manifest, (
            f"marketplace.json missing required field {field!r}"
        )


def test_marketplace_owner_has_name(marketplace_manifest):
    assert "name" in marketplace_manifest["owner"], "owner must have name"


def test_marketplace_plugins_is_list(marketplace_manifest):
    assert isinstance(marketplace_manifest["plugins"], list)
    assert len(marketplace_manifest["plugins"]) >= 1, "at least one plugin entry"


def test_each_marketplace_plugin_has_required_fields(marketplace_manifest):
    for entry in marketplace_manifest["plugins"]:
        for field in ("name", "description", "source"):
            assert field in entry, f"marketplace plugin missing field {field!r}: {entry.get('name')}"
        src = entry["source"]
        assert isinstance(src, dict), "source must be an object"
        assert src.get("source") in {"url", "git", "local", "github"}, (
            f"unknown source.type {src.get('source')!r}"
        )
        if src.get("source") == "url":
            assert src.get("url"), "source.url is required when source.type=url"


def test_marketplace_plugin_names_match_bundled_skills(marketplace_manifest):
    names = {p["name"] for p in marketplace_manifest["plugins"]}
    # plugin-harness itself is the only required marketplace entry today.
    assert "plugin-harness" in names


# ---------- version consistency ----------

def test_plugin_and_codex_versions_match():
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text())
    assert plugin["version"] == codex["version"], (
        f"plugin.json version {plugin['version']!r} != codex-plugin version {codex['version']!r}"
    )


def test_marketplace_source_ref_present():
    """marketplace.json's plugin entry must declare a ref (git ref or commit) so
    users get a deterministic install pin. Per the version-management docs."""
    m = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    for entry in m["plugins"]:
        src = entry["source"]
        if src.get("source") == "url":
            assert src.get("ref"), (
                f"marketplace plugin {entry['name']!r} source.url lacks a 'ref' (version-management best practice)"
            )
