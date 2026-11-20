#!/usr/bin/env bash
# lychee：只查相对链接，离线。优先 ~/profile/bin，其次 PATH。
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
GOV="$ROOT/governance"
[ -d "$GOV" ] || GOV="$HOME/profile/context/governance"
cd "$ROOT"
[ $# -eq 0 ] && set -- .
BIN="$HOME/profile/bin/lychee"
[ -x "$BIN" ] || BIN=$(command -v lychee)
exec "$BIN" --config "$GOV/lychee.toml" --offline --no-progress "$@"
