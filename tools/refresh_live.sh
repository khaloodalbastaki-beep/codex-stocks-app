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

finish_refresh() {
  local code=$?
  trap - EXIT
  if [[ "${REFRESH_FINALIZED:-0}" != "1" || "$code" != "0" ]]; then
    python3 tools/refresh_status.py finish --exit-code "$code" >/dev/null 2>&1 || true
  fi
  exit "$code"
}

trap finish_refresh EXIT
REFRESH_FINALIZED=0

if [[ "$DEPLOY" == "1" ]]; then
  python3 tools/refresh_status.py start --deploy
else
  python3 tools/refresh_status.py start
fi

if [[ "${#ARGS[@]}" -gt 0 ]]; then
  python3 tools/update_live.py "${ARGS[@]}"
else
  python3 tools/update_live.py
fi
python3 tools/update_news.py
python3 tools/update_disclosures.py
python3 tools/refresh_status.py finish --exit-code 0
REFRESH_FINALIZED=1
bash tools/build.sh

if [[ "$DEPLOY" == "1" ]]; then
  bash tools/deploy_pages.sh
fi

trap - EXIT
