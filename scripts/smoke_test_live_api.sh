#!/usr/bin/env bash
# smoke_test_live_api.sh — catches exactly the class of bug found in R2.5
# (docs/phase-reports/R2-mobile-ui.md): the live, long-running Docker container
# silently served code from 19+ hours before the auth bypass was fixed, and
# 613 passing pytest tests (which run against a separate local venv, never the
# deployed container) never caught it. This hits the REAL running :8000, not
# a test process, specifically to catch "source says X, deployment still does Y".
#
# Usage: scripts/smoke_test_live_api.sh [base_url]   (default http://localhost:8000)
set -euo pipefail
BASE_URL="${1:-http://localhost:8000}"
FAIL=0

check() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "[PASS] $desc (got $actual)"
  else
    echo "[FAIL] $desc (expected $expected, got $actual)"
    FAIL=1
  fi
}

echo "=== Smoke-testing live API at $BASE_URL ==="

CURL="curl --max-time 5"

# Allow up to 10s for the container to finish starting up if just redeployed
for _ in {1..10}; do
  if $CURL -s -o /dev/null "$BASE_URL/health" 2>/dev/null; then
    break
  fi
  sleep 1
done

# 1. The server responds at all.
health_code=$($CURL -s -o /dev/null -w '%{http_code}' "$BASE_URL/v1/openapi.json" 2>/dev/null) || health_code="000"
check "OpenAPI schema reachable" "200" "$health_code"

# 2. The specific bug this script exists to catch: a wrong password must be
#    rejected. If this ever returns 200 again, the deployed container is
#    running stale/vulnerable code regardless of what the test suite says.
login_code=$($CURL -s -o /dev/null -w '%{http_code}' -X POST "$BASE_URL/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke-test-nonexistent-user@example.invalid","password":"definitely-wrong"}' \
  2>/dev/null) || login_code="000"
check "Wrong-password login is rejected (not a bypass)" "401" "$login_code"

# 3. CORS is configured for the local dev origins real clients need
#    (apps/web/src, apps/mobile's Expo web preview) — see R2.5's CORS bug.
cors_header=$($CURL -s -i -X OPTIONS "$BASE_URL/v1/auth/login" \
  -H "Origin: http://localhost:8082" \
  -H "Access-Control-Request-Method: POST" \
  | grep -i "^access-control-allow-origin:" | tr -d '\r' || true)
if [ -n "$cors_header" ]; then
  echo "[PASS] CORS preflight for mobile dev origin ($cors_header)"
else
  echo "[FAIL] CORS preflight for mobile dev origin returned no Access-Control-Allow-Origin header"
  FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo "=== All smoke checks passed — the live deployment matches source for these checks ==="
else
  echo "=== SMOKE TEST FAILED — the live deployment likely does not match current source. Rebuild and redeploy: 'make redeploy' ==="
  exit 1
fi
