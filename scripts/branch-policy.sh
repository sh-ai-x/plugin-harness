#!/usr/bin/env bash
# scripts/branch-policy.sh — Callable branch-policy check (mirrors .githooks/pre-push).
#
# Behavior by environment:
#   - GitHub Actions (GITHUB_REF set): FAIL-CLOSED on direct push to main/main (exit 1)
#     with `::error::` annotation. Pair with branch protection rules for full coverage.
#   - Manual: print policy text and exit 0
#
# Active enforcement lives in `.githooks/pre-push` (client-side git hook).
# This script provides the server-side mirror so CI catches direct pushes that
# bypass client-side hooks (e.g. `git push --no-verify`, `--force-with-lease`,
# web-based pushes).
#
# PR #35 security review (A06/A10 critical): the previous version was
# fail-open — it detected the policy violation, emitted a `::warning::`,
# then `exit 0`. The result: a direct push to main passed CI with a
# green check, masking the violation. Now fail-closed: any detected
# direct push to main/master exits 1 with `::error::`.

set -eo pipefail

if [ -n "${GITHUB_REF:-}" ] && [ -n "${GITHUB_EVENT_NAME:-}" ]; then
  if [ "$GITHUB_EVENT_NAME" = "push" ] && { [ "$GITHUB_REF" = "refs/heads/main" ] || [ "$GITHUB_REF" = "refs/heads/master" ]; }; then
    echo "::error::Direct push to main detected. Policy: PR review required before merge."
    echo "  Commit:  ${GITHUB_SHA:-unknown}"
    echo "  Author:  ${GITHUB_ACTOR:-unknown}"
    echo "  Event:   push (not pull_request)"
    echo "  Remediation: revert on main + branch from pre-push sha + open PR"
    exit 1
  fi
  exit 0
fi

echo "branch-policy.sh: active enforcement lives in .githooks/pre-push."
echo "  Client-side:    git config core.hooksPath .githooks"
echo "  Server-side:    this script (fail-closed in CI)."
echo "  Bypass (emergency hotfix only): git push --no-verify"
exit 0
