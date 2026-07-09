"""Dual-runtime plugin emitter (Codex layout).

Public surface:
- `emit(state, plan_md, output_dir) -> EmitResult`
- `validate_emit(output_dir) -> ValidationReport`
- `EmitError`, `EmitResult`
"""

from src.emitter.codex import EmitError, EmitResult, emit
from src.emitter.validator import ValidationReport, validate_emit

__all__ = ["emit", "validate_emit", "EmitError", "EmitResult", "ValidationReport"]