#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[build] generating deterministic demo data"
python3 -m brain.run --out data --copy-web

echo "[build] assembling dist"
rm -rf dist
mkdir -p dist
cp -R web/. dist/

echo "[build] done -> dist/"

