#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DEPLOY=0
ARGS=()
for arg in "$@"; do
  if [[ "$arg" == "--deploy" ]]; then
    DEPLOY=1
  else
    ARGS+=("$arg")
  fi
done

python3 tools/update_live.py "${ARGS[@]}"
python3 tools/update_news.py
bash tools/build.sh

if [[ "$DEPLOY" == "1" ]]; then
  bash tools/deploy_pages.sh
fi
