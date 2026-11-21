#!/usr/bin/env bash
# lychee：只查相对链接，离线。
# 二进制不进 PATH：优先 $LYCHEE_BIN，其次 ~/.local/share/lychee/lychee，
# 再次旧的 ~/profile/bin/lychee，最后 PATH（兼容其他机器/CI）。
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
GOV="$ROOT/governance"
[ -d "$GOV" ] || GOV="$HOME/profile/context/governance"
cd "$ROOT"
[ $# -eq 0 ] && set -- .
BIN=""
for cand in "${LYCHEE_BIN:-}" "$HOME/.local/share/lychee/lychee" "$HOME/profile/bin/lychee"; do
  if [ -n "$cand" ] && [ -x "$cand" ]; then BIN="$cand"; break; fi
done
if [ -z "$BIN" ]; then BIN=$(command -v lychee || true); fi
if [ -z "$BIN" ]; then
  echo "lychee 未安装：放到 ~/.local/share/lychee/lychee 或设置 LYCHEE_BIN" >&2
  exit 2
fi
exec "$BIN" --config "$GOV/lychee.toml" --offline --no-progress "$@"
