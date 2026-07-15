#!/usr/bin/env bash
# scripts/branch-policy.sh — Callable branch-policy check (mirrors .githooks/pre-push).
#
# Behavior by environment:
#   - GitHub Actions (GITHUB_REF set):
#       * push to main/master WITHOUT an associated merged PR → FAIL-CLOSED
#         (direct push bypassing review; ::error:: + exit 1).
#       * push to main/master WITH an associated merged PR → ALLOW (legitimate
#         GitHub-UI merge of an approved PR; exit 0).
#       * other push refs / non-push events → ALLOW (exit 0).
#   - Manual: print policy text and exit 0.
#
# Detection of merge-commit pushes: a PR-merged push arrives at main with a
# merge-commit SHA. GitHub's REST API endpoint
#   /repos/{owner}/{repo}/commits/{sha}/pulls
# returns the PR(s) associated with that SHA — empty array means "not from any
# PR", i.e. a direct push.
#
# Active enforcement also lives in `.githooks/pre-push` (client-side git
# hook). This script is the server-side mirror so CI catches direct pushes
# that bypass client-side hooks (`git push --no-verify`, `--force-with-lease`,
# web-based merges without the hook in scope).
#
# PR #35 review history:
#   - Round 1: warn-only (`::warning::` + exit 0). A06/A10 critical:
#     fail-open — direct push to main passed CI with a green check.
#   - Round 2: fail-closed (`::error::` + exit 1) on EVERY push event to
#     main. Closed the critical but caused a regression: legitimate
#     GitHub-UI PR merges (which arrive as `push` events) were blocked.
#   - Round 3 (this file): fail-closed ONLY on direct pushes; merge
#     pushes exit 0 via the /commits/{sha}/pulls probe.

set -eo pipefail

is_protected_ref() {
  case "$1" in
    refs/heads/main|refs/heads/master) return 0 ;;
    *) return 1 ;;
  esac
}

if [ -n "${GITHUB_REF:-}" ] && [ -n "${GITHUB_EVENT_NAME:-}" ]; then
  if [ "$GITHUB_EVENT_NAME" = "push" ] && is_protected_ref "$GITHUB_REF"; then
    SHA="${GITHUB_SHA:-}"
    REPO="${GITHUB_REPOSITORY:-}"
    if [ -z "$SHA" ] || [ -z "$REPO" ]; then
      # Fail-safe: if we cannot determine provenance, fail-closed. The
      # alternative (allowing unknown provenance) re-opens the very
      # fail-open hole this script exists to close.
      echo "::error::Cannot determine commit provenance (GITHUB_SHA or GITHUB_REPOSITORY missing); fail-closed by default."
      exit 1
    fi

    # Two-call probe: gh api --include doesn't reliably insert a blank
    # line between HTTP headers and JSON body, so parsing them out of a
    # single response is brittle. Issue two calls instead: one with
    # --include for the status line, one without for the JSON array.
    # The HTTP status check guards against 422 (unknown SHA) and other
    # 4xx/5xx returning error envelopes whose `length` would otherwise
    # look like a positive PR count.
    headers=$(gh api "repos/${REPO}/commits/${SHA}/pulls" --include --silent 2>&1 || true)
    http_status=$(printf '%s\n' "$headers" | head -n 1 | awk '{print $2}')
    if [ "$http_status" != "200" ]; then
      echo "::error::Cannot probe commit provenance (HTTP ${http_status:-?} for ${SHA}); fail-closed by default."
      exit 1
    fi
    pr_count=$(gh api "repos/${REPO}/commits/${SHA}/pulls" --jq 'length' 2>/dev/null || echo 0)
    if [ "${pr_count:-0}" = "0" ]; then
      echo "::error::Direct push to main detected. Policy: PR review required before merge."
      echo "  Commit:  ${SHA}"
      echo "  Author:  ${GITHUB_ACTOR:-unknown}"
      echo "  Event:   push (not pull_request) — no associated PR"
      echo "  Remediation: revert on main + branch from pre-push sha + open PR"
      exit 1
    fi
    # Legitimate PR-merge push.
    echo "branch-policy: PR-merge push detected (commit ${SHA} is associated with ${pr_count} PR); allowing."
    exit 0
  fi
  exit 0
fi

echo "branch-policy.sh: active enforcement lives in .githooks/pre-push."
echo "  Client-side:    git config core.hooksPath .githooks"
echo "  Server-side:    this script (fail-closed on direct pushes only)."
echo "  Bypass (emergency hotfix only): git push --no-verify"
exit 0