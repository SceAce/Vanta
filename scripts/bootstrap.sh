#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git config core.hooksPath .githooks
echo "[bootstrap] ensuring signed commits are enabled locally"
git config commit.gpgsign true || true

echo "[bootstrap] installing Node metadata tooling via pnpm"
if command -v pnpm >/dev/null 2>&1; then
  pnpm install --ignore-scripts
fi

echo "[bootstrap] syncing Python environment with uv"
if command -v uv >/dev/null 2>&1; then
  uv sync --all-groups
fi

echo "[bootstrap] complete"
