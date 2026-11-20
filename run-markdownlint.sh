#!/usr/bin/env bash
# markdownlint-cli2：优先用本地 tooling，其次 PATH（CI 里是全局安装）。
set -euo pipefail
ROOT=$(git rev-parse --show-toplevel)
GOV="$ROOT/governance"
LOCAL="$HOME/profile/context/governance/tooling/node_modules/.bin/markdownlint-cli2"
[ -d "$GOV" ] || GOV="$HOME/profile/context/governance"
cd "$ROOT"
# 无参数时按默认 glob 扫全部（0.24 起不传 pattern 会 lint 0 个文件）
if [ $# -eq 0 ]; then set -- "**/*.md"; fi
if [ -x "$LOCAL" ]; then
  exec node "$LOCAL" --config "$GOV/.markdownlint-cli2.jsonc" "$@"
fi
exec markdownlint-cli2 --config "$GOV/.markdownlint-cli2.jsonc" "$@"
