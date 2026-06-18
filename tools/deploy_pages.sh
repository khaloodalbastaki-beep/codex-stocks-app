#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${PAGES_REMOTE:-origin}"
BRANCH="${PAGES_BRANCH:-gh-pages}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cd "$ROOT"
bash tools/build.sh

git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null
REMOTE_URL="$(git remote get-url "$REMOTE")"

git clone --quiet --branch "$BRANCH" "$REMOTE_URL" "$TMP_DIR" 2>/dev/null || {
  git clone --quiet "$REMOTE_URL" "$TMP_DIR"
  git -C "$TMP_DIR" checkout --orphan "$BRANCH"
  git -C "$TMP_DIR" rm -rf . >/dev/null 2>&1 || true
}

find "$TMP_DIR" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$ROOT/dist/." "$TMP_DIR/"
touch "$TMP_DIR/.nojekyll"

git -C "$TMP_DIR" add .
if git -C "$TMP_DIR" diff --cached --quiet; then
  echo "[deploy] no Pages changes"
else
  git -C "$TMP_DIR" commit -m "Deploy UAE stocks app" >/dev/null
  git -C "$TMP_DIR" push "$REMOTE" "$BRANCH" >/dev/null
  echo "[deploy] pushed $BRANCH"
fi

