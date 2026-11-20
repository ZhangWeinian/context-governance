#!/usr/bin/env bash
# adr check：过滤“编号缺口”这类预期 warning（历史编号不重排），只保留真问题。
set -uo pipefail
ROOT=$(git rev-parse --show-toplevel)
LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT
adr check --dir "$ROOT/DECISIONS" >"$LOG" 2>&1
rc=$?
grep -v 'number-gap' "$LOG" || true
exit $rc
