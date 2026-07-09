#!/usr/bin/env bash
# scripts/e2e.sh — end-to-end dual-runtime pipeline test.
#
# Wires the full build-time pipeline against a temp project dir,
# asserts both adapters install, asserts the emitted plugin passes
# the validator, and asserts the runtime-parity contract (CC SKILL.md
# body == Codex SKILL.md body, byte-for-byte, modulo front-matter).
#
# Exits 0 only if every step succeeds. Any step failure → non-zero
# exit and a stderr message naming the failing step. Re-runnable.
set -euo pipefail

# Locate REPO_ROOT (this script lives at <repo>/scripts/e2e.sh). Scope
# the fallback in a subshell so the inner `pwd` cannot leak out and
# corrupt REPO_ROOT via the `A || B && C` operator-precedence trap.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || (cd "$(dirname "$0")/.." && pwd))"
cd "$REPO_ROOT"

if [ ! -d "src" ]; then
    echo "e2e.sh: upstream pipeline source (src/) is missing on this branch." >&2
    echo "         Merge feat/0-mvp-step0..feat/0-mvp-step5 first, then re-run." >&2
    exit 1
fi

if [ ! -d "tests/e2e" ]; then
    echo "e2e.sh: tests/e2e/ missing — step 6 deliverable not in this checkout." >&2
    exit 1
fi

exec python3 -m pytest tests/e2e/test_full_pipeline.py -v "$@"
