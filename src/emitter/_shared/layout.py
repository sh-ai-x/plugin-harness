"""Canonical Codex plugin output layout.

PR #27 LLM review (🟠 major #4): codex.py and validator.py each
hardcoded the four-file layout (`.codex-plugin/plugin.json`,
`src/skills/<slug>/SKILL.md`, `src/.mcp.json`, `README.md`).
Adding a fifth file in either file required matching the other by
hand. `CodexLayout` is the single source of truth — pass an
`output_dir` and the four canonical paths are derived.

The four paths form a tree under `<output_dir>`:
  <output_dir>/
    src/
      .codex-plugin/
        plugin.json
      skills/
        <plugin_slug>/
          SKILL.md
      .mcp.json
    README.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodexLayout:
    """All four canonical Codex-plugin output paths under one tree.

    Instances are constructed once per `emit()` call so the slug is
    captured in `skill_dir` and `skill_md` (which both include it).
    """

    output_dir: Path
    plugin_slug: str

    @property
    def codex_dir(self) -> Path:
        return self.output_dir / "src" / ".codex-plugin"

    @property
    def plugin_json(self) -> Path:
        return self.codex_dir / "plugin.json"

    @property
    def skills_root(self) -> Path:
        return self.output_dir / "src" / "skills"

    @property
    def skill_dir(self) -> Path:
        return self.skills_root / self.plugin_slug

    @property
    def skill_md(self) -> Path:
        return self.skill_dir / "SKILL.md"

    @property
    def mcp_json(self) -> Path:
        return self.output_dir / "src" / ".mcp.json"

    @property
    def readme(self) -> Path:
        return self.output_dir / "README.md"

    @property
    def plugin_json_text(self) -> str:
        # Stable, machine-readable summary for log lines / error paths
        # (avoids stringifying four separate Path objects ad-hoc).
        return (
            f"plugin.json={self.plugin_json} "
            f"skill_md={self.skill_md} "
            f"mcp_json={self.mcp_json} "
            f"readme={self.readme}"
        )


__all__ = ["CodexLayout"]
