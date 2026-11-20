#!/usr/bin/env bash
# markdownlint-cli2：优先用本地 tooling，其次 PATH（CI 里是全局安装）。
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
GOV="$ROOT/governance"
LOCAL="$HOME/profile/context/governance/tooling/node_modules/.bin/markdownlint-cli2"
[ -d "$GOV" ] || GOV="$HOME/profile/context/governance"
cd "$ROOT"
if [ -x "$LOCAL" ]; then
  exec node "$LOCAL" --config "$GOV/.markdownlint-cli2.jsonc" "$@"
fi
exec markdownlint-cli2 --config "$GOV/.markdownlint-cli2.jsonc" "$@"
