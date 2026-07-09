#!/usr/bin/env bash
# scripts/smoke.sh — quick dual-runtime smoke (full interview, both
# adapters install, validator passes).
#
# Per step 0 the 5-question contract is locked, so smoke runs the
# full interview flow (not an abbreviation). The runtime-parity
# byte-check is in scripts/e2e.sh (e2e-specific proof point); smoke
# stops once both adapters install and the validator passes, which
# is enough to catch the most common regressions during iteration.
#
# Exits 0 only if every step succeeds.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || (cd "$(dirname "$0")/.." && pwd))"
cd "$REPO_ROOT"

if [ ! -d "src" ]; then
    echo "smoke.sh: upstream pipeline source (src/) is missing on this branch." >&2
    echo "          Merge feat/0-mvp-step0..feat/0-mvp-step5 first, then re-run." >&2
    exit 1
fi

if [ ! -d "tests/e2e" ]; then
    echo "smoke.sh: tests/e2e/ missing — step 6 deliverable not in this checkout." >&2
    exit 1
fi

exec python3 -m pytest tests/e2e/test_smoke.py -v "$@"
