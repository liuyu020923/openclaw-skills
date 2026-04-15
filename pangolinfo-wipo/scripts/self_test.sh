#!/usr/bin/env bash
# Self-test for Pangolinfo WIPO API Client
# Validates auth + basic WIPO search
# NOTE: Each successful search costs 2 credits

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/pangolinfo.py"
PASS=0
FAIL=0

ok()   { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

echo "=== Pangolinfo WIPO API Self-Test ==="
echo "WARNING: Successful searches consume 2 credits each."
echo ""

# --- Test 1: Auth check (free) ---
echo "[1/3] Auth check (no credits)..."
if python3 "$SCRIPT" --auth-only 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['success']" 2>/dev/null; then
    ok "auth-only"
else
    fail "auth-only -- check PANGOLINFO_API_KEY or PANGOLINFO_EMAIL+PANGOLINFO_PASSWORD"
    echo ""
    echo "Results: $PASS passed, $FAIL failed"
    exit 1
fi

# --- Test 2: WIPO search by IRN (2 credits) ---
echo "[2/3] WIPO search by IRN (2 credits)..."
if python3 "$SCRIPT" --irn "000298" --ds AL --num 1 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['success']; assert d['total']>=0" 2>/dev/null; then
    ok "wipo-irn-search"
else
    fail "wipo-irn-search"
fi

# --- Test 3: WIPO search by product (2 credits) ---
echo "[3/3] WIPO search by product (2 credits)..."
if python3 "$SCRIPT" --prod "chair" --ds US --num 1 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['success']" 2>/dev/null; then
    ok "wipo-product-search"
else
    fail "wipo-product-search"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed (up to 4 credits consumed)"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
