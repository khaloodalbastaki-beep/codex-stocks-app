#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_SRC="$ROOT/launchd/com.bastaki.codex-stocks-refresh.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.bastaki.codex-stocks-refresh.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/tmp"
cp "$PLIST_SRC" "$PLIST_DST"
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "Loaded com.bastaki.codex-stocks-refresh every 300 seconds"
echo "Logs: $ROOT/tmp/refresh.out.log and $ROOT/tmp/refresh.err.log"

