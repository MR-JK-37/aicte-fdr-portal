#!/usr/bin/env bash
# PreToolUse guard (Edit|Write). Exit 2 blocks the tool call and shows stderr to Claude.
# Reads the hook JSON on stdin; uses python3 so no jq dependency.
set -u
payload="$(cat)"
path="$(printf '%s' "$payload" | python3 -I -c 'import json,sys
try:
    d=json.load(sys.stdin); ti=d.get("tool_input",{}); print(ti.get("file_path") or ti.get("path") or "")
except Exception:
    print("")')"
[ -z "$path" ] && exit 0
rel="${path#"${CLAUDE_PROJECT_DIR:-$PWD}"/}"

block() { echo "BLOCKED by .claude/hooks/protect-files.sh: $1 ($rel)" >&2; exit 2; }

case "$rel" in
  .env|.env.*|*/.env|*/.env.*) [ "$rel" = ".env.example" ] || block "secrets files must never be edited by the agent" ;;
  secrets/*|*.p8|*service-account*.json)  block "credential material" ;;
  docs/spec/SPEC_v3.md|docs/spec/PS26265_problem_statement.txt) block "authoritative source documents are read-only; raise a question instead" ;;
  pnpm-lock.yaml|uv.lock|package-lock.json) block "lockfiles change only through the package manager" ;;
  backend/alembic/versions/*)
     # Existing migrations are immutable once committed; new files are fine.
     if git -C "${CLAUDE_PROJECT_DIR:-$PWD}" ls-files --error-unmatch "$rel" >/dev/null 2>&1; then
        block "committed migrations are immutable; add a new migration"
     fi ;;
esac
exit 0
