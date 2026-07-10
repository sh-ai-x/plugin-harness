"""Validator for the dual-runtime plugin emitter.

`validate_emit(output_dir) -> ValidationReport` checks the 4 emitted files exist
with the required fields and that plugin.json validates against the vendored
Codex schema at `docs/codex-plugin.schema.json` (NOT against the live URL).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "docs" / "codex-plugin.schema.json"


@dataclass
class ValidationReport:
    ok: bool
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # pragma: no cover - convenience
        return self.ok


def _expected_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "plugin.json": output_dir / "src" / ".codex-plugin" / "plugin.json",
        "SKILL.md": output_dir / "src" / "skills",  # directory; specific slug checked later
        ".mcp.json": output_dir / "src" / ".mcp.json",
        "README.md": output_dir / "README.md",
    }


def validate_emit(output_dir: Path) -> ValidationReport:
    errors: list[str] = []

    # ------------------------------------------------------------ existence
    expected = _expected_paths(output_dir)
    plugin_json_path = expected["plugin.json"]
    mcp_path = expected[".mcp.json"]
    readme_path = expected["README.md"]
    skills_root = expected["SKILL.md"]  # directory

    # PR #27 review (🔴 critical): each 'missing required file' branch
    # appends to errors and returns ValidationReport(ok=False, ...) so
    # the later stat().st_size and read_text() calls do not raise an
    # uncaught FileNotFoundError. Missing-file reports stay first-class
    # failures; the validator no longer crashes mid-walk.
    if not plugin_json_path.is_file():
        errors.append(f"plugin.json missing at {plugin_json_path}")
        return ValidationReport(ok=False, errors=errors)
    if not mcp_path.is_file():
        errors.append(f".mcp.json missing at {mcp_path}")
        return ValidationReport(ok=False, errors=errors)
    if not readme_path.is_file():
        errors.append(f"README.md missing at {readme_path}")
        return ValidationReport(ok=False, errors=errors)
    if not skills_root.is_dir():
        errors.append(f"skills directory missing at {skills_root}")
        return ValidationReport(ok=False, errors=errors)

    # PR #27 round 8 (🟠 major): parse plugin.json FIRST so we can use
    # plugin_payload["skills"][0] to find the matching skill directory.
    # Previously the validator blindly picked `skill_dirs[0]`, which
    # silently mis-attributes errors when stale slugs linger.
    try:
        plugin_payload = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"plugin.json is not valid JSON: {exc}")
        return ValidationReport(ok=False, errors=errors)

    # SKILL.md: locate the skill directory whose name matches the
    # plugin_payload["skills"] slug list.
    skill_slugs = plugin_payload.get("skills", [])
    if not skill_slugs:
        errors.append(f"plugin.json.skills is empty or missing")
        return ValidationReport(ok=False, errors=errors)
    expected_slug = skill_slugs[0]
    expected_skill_md = skills_root / expected_slug / "SKILL.md"
    if not expected_skill_md.is_file():
        errors.append(
            f"SKILL.md missing at expected path {expected_skill_md} "
            f"(plugin.json.skills[0]={expected_slug!r})"
        )
        return ValidationReport(ok=False, errors=errors)
    skill_md = expected_skill_md
    skill_dirs = [p for p in skills_root.iterdir() if p.is_dir()]
    if len(skill_dirs) > 1:
        # Multiple slugs on disk is allowed (idempotent re-run), but
        # only the one matching plugin.json is validated here.
        errors.append(
            f"multiple skill directories under {skills_root}: "
            f"{[p.name for p in skill_dirs]}; validating {expected_slug!r}"
        )

        return ValidationReport(ok=False, errors=errors)

    for required in ("name", "version", "description"):
        if required not in plugin_payload:
            errors.append(f"plugin.json missing required field: {required!r}")
        elif not isinstance(plugin_payload[required], str) or not plugin_payload[required]:
            errors.append(f"plugin.json.{required} must be a non-empty string")

    # Schema round-trip against the vendored schema.
    if not SCHEMA_PATH.is_file():
        errors.append(f"vendored schema missing at {SCHEMA_PATH}")
    else:
        try:
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"vendored schema at {SCHEMA_PATH} is not valid JSON: {exc}")
        else:
            try:
                jsonschema.validate(plugin_payload, schema)
            except jsonschema.ValidationError as exc:
                errors.append(
                    f"plugin.json fails vendored schema validation: {exc.message}"
                )

    # ------------------------------------------------------------ .mcp.json shape
    try:
        mcp_payload = json.loads(mcp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f".mcp.json is not valid JSON: {exc}")
    else:
        if "mcpServers" not in mcp_payload:
            errors.append(
                ".mcp.json missing required key 'mcpServers' (camelCase; "
                "'servers' is non-standard and ignored at load time)"
            )
        elif not isinstance(mcp_payload["mcpServers"], list):
            errors.append(".mcp.json.mcpServers must be an array")

    # ------------------------------------------------------------ SKILL.md non-empty
    # PR #27 round 6 (TOCTOU): the redundant is_file() re-check that
    # previously guarded stat() was removed in round 5; replaced with a
    # try/except OSError around stat() so a missing-file race produces
    # a clean error rather than crashing the validator mid-walk.
    try:
        skill_size = skill_md.stat().st_size
    except OSError as exc:
        errors.append(f"SKILL.md stat failed at {skill_md}: {exc}")
        skill_size = 0
    if skill_size == 0:
        errors.append(f"SKILL.md is empty at {skill_md}")

    # ------------------------------------------------------------ README.md non-empty
    try:
        readme_size = readme_path.stat().st_size
    except OSError as exc:
        errors.append(f"README.md stat failed at {readme_path}: {exc}")
        readme_size = 0
    if readme_size == 0:
        errors.append(f"README.md is empty at {readme_path}")

    return ValidationReport(ok=not errors, errors=errors)