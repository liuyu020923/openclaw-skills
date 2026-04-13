#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PANGOLINFO="$SCRIPT_DIR/pangolinfo.py"

# Cross-platform Python detection
if python3 --version >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

PASS=0
FAIL=0

run_test() {
  local name="$1"
  shift
  echo -n "  [$name] "
  if "$@"; then
    echo "PASS"
    PASS=$((PASS + 1))
  else
    echo "FAIL (exit code $?)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Pangolinfo AI SERP Self-Test ==="

# --- Auth tests (no credits consumed) ---
echo "Auth tests:"
run_test "auth-check" $PYTHON "$PANGOLINFO" --auth-only

# --- Input validation tests (no credits consumed) ---
echo "Input validation tests:"

run_test "missing-query" bash -c "! $PYTHON \"$PANGOLINFO\" 2>/dev/null"
run_test "follow-up-in-serp" bash -c "! $PYTHON \"$PANGOLINFO\" --q test --mode serp --follow-up q 2>/dev/null"
run_test "region-in-ai-mode" bash -c "! $PYTHON \"$PANGOLINFO\" --q test --mode ai-mode --region us 2>/dev/null"
run_test "invalid-region" bash -c "! $PYTHON \"$PANGOLINFO\" --q test --mode serp --region xx 2>/dev/null"
run_test "invalid-num-zero" bash -c "! $PYTHON \"$PANGOLINFO\" --q test --num 0 2>/dev/null"

# --- Live API tests (consumes credits) ---
if [ "${RUN_LIVE_TESTS:-0}" = "1" ]; then
  echo "Live API tests (credits will be consumed):"

  run_test "serp-query" bash -c "$PYTHON \"$PANGOLINFO\" --q openclaw --mode serp 2>/dev/null | $PYTHON -c \"import sys,json; d=json.load(sys.stdin); assert d['success']==True; print(f'Got {d.get(\\\"results_num\\\",0)} results')\""

  run_test "ai-mode-query" bash -c "$PYTHON \"$PANGOLINFO\" --q 'what is python' 2>/dev/null | $PYTHON -c \"import sys,json; d=json.load(sys.stdin); assert d['success']==True\""
else
  echo "Live API tests: SKIPPED (set RUN_LIVE_TESTS=1 to enable -- consumes credits)"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
