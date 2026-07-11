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

    if not plugin_json_path.is_file():
        errors.append(f"plugin.json missing at {plugin_json_path}")
    if not mcp_path.is_file():
        errors.append(f".mcp.json missing at {mcp_path}")
    if not readme_path.is_file():
        errors.append(f"README.md missing at {readme_path}")
    if not skills_root.is_dir():
        errors.append(f"skills directory missing at {skills_root}")
        return ValidationReport(ok=False, errors=errors)

    # SKILL.md: find the single slug directory and check SKILL.md exists.
    skill_dirs = [p for p in skills_root.iterdir() if p.is_dir()]
    if not skill_dirs:
        errors.append(f"no skill directory under {skills_root}")
        return ValidationReport(ok=False, errors=errors)
    if len(skill_dirs) > 1:
        errors.append(
            f"multiple skill directories under {skills_root}: "
            f"{[p.name for p in skill_dirs]}"
        )
    skill_md = skill_dirs[0] / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"SKILL.md missing at {skill_md}")
        return ValidationReport(ok=False, errors=errors)

    # ------------------------------------------------------------ plugin.json shape
    try:
        plugin_payload = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"plugin.json is not valid JSON: {exc}")
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
    if skill_md.stat().st_size == 0:
        errors.append(f"SKILL.md is empty at {skill_md}")

    # ------------------------------------------------------------ README.md non-empty
    if readme_path.stat().st_size == 0:
        errors.append(f"README.md is empty at {readme_path}")

    return ValidationReport(ok=not errors, errors=errors)