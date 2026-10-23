#!/usr/bin/env bash
# PostToolUse check (Edit|Write): fail fast on patterns this project forbids.
# Exit 2 returns stderr to Claude so it fixes the file before continuing.
set -u
export LC_ALL=C.UTF-8
payload="$(cat)"
path="$(printf '%s' "$payload" | python3 -I -c 'import json,sys
try:
    d=json.load(sys.stdin); ti=d.get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")
except Exception:
    print("")')"
[ -z "$path" ] || [ ! -f "$path" ] && exit 0
rel="${path#"${CLAUDE_PROJECT_DIR:-$PWD}"/}"
fail() { echo "FORBIDDEN PATTERN ($1) in $rel — see CLAUDE.md non-negotiables / MASTER_PROMPT." >&2; exit 2; }

is_test=0
case "$rel" in
  */tests/*|*/__tests__/*|*.test.*|*.spec.*|packages/fixtures/*|*/app/core/prod_guard.py|docs/*|.claude/*|*.md) is_test=1 ;;
esac

# 1) Simulation switches outside tests/guard/docs
if [ $is_test -eq 0 ] && grep -nE 'DEMO_MODE|MOCK_BANK_PROVIDER|SIMULATED_CLOCK|FAKE_PUSH_SUCCESS' "$path" >/dev/null 2>&1; then
  fail "simulation flag outside tests/prod_guard"
fi
# 2) Floating-point money in backend code
if [[ "$rel" == backend/app/*.py ]] && grep -nE '(amount|principal|deposit|balance)[A-Za-z_]*\s*[:=]\s*float\b|float\((amount|principal|deposit|balance)' "$path" >/dev/null 2>&1; then
  fail "float used for money (use Decimal/NUMERIC)"
fi
# 3) Android code must use Material Symbols only
if [[ "$rel" == apps/mobile/src/android/* || "$rel" == apps/mobile/*android* ]] && \
   grep -nEi "from ['\"](lucide|@expo/vector-icons|react-native-vector-icons|@phosphor|react-native-heroicons|@tabler|react-icons|expo-symbols)" "$path" >/dev/null 2>&1; then
  fail "non-Material-Symbols icon source in Android code"
fi
# 4) iOS-specific code must not use Material Symbols
if [[ "$rel" == apps/mobile/src/ios/* ]] && grep -nEi "material-symbols|@expo/material-symbols" "$path" >/dev/null 2>&1; then
  fail "Material Symbols in iOS code (use SF Symbols)"
fi
# 5) Emoji used as UI icons in app source
if [[ "$rel" == apps/*/src/* || "$rel" == apps/*/app/* ]] && grep -nP '[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]' "$path" >/dev/null 2>&1; then
  fail "emoji in UI source (use the icon system)"
fi
exit 0
