#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HAS_CARGO_MANIFEST=0
if [ -f Cargo.toml ]; then
  HAS_CARGO_MANIFEST=1
fi

if [ "$HAS_CARGO_MANIFEST" -eq 1 ]; then
  echo "[verify] cargo fmt --check"
  cargo fmt --all --check

  echo "[verify] cargo clippy"
  cargo clippy --workspace --all-targets -- -D warnings

  echo "[verify] cargo test --workspace"
  cargo test --workspace
else
  echo "[verify] skip Rust checks (Cargo.toml not found)"
fi

if [ "$HAS_CARGO_MANIFEST" -eq 1 ]; then
  echo "[verify] check dep docs"
  uv run python scripts/lint/check_dep_docs.py
else
  echo "[verify] skip dep docs check (Cargo.toml not found)"
fi

echo "[verify] check ADR policy"
uv run python scripts/lint/check_adr_policy.py

echo "[verify] check repo policy"
uv run python scripts/lint/check_repo_policy.py

if [ "$HAS_CARGO_MANIFEST" -eq 1 ]; then
  echo "[verify] taste T-001 (no unwrap in library crates)"
  uv run python scripts/lint/taste_t001_no_unwrap.py

  echo "[verify] taste T-002 (public API rustdoc)"
  uv run python scripts/lint/taste_t002_rustdoc.py
else
  echo "[verify] skip T-001 and T-002 (Cargo.toml not found)"
fi

echo "[verify] taste T-003 (no marker comments in production code)"
uv run python scripts/lint/taste_t003_no_marker_comments.py

echo "[verify] taste T-004 (arch boundaries)"
uv run python scripts/lint/taste_t004_arch_boundaries.py

echo "[verify] taste T-005 (evidence-lease refs)"
uv run python scripts/lint/taste_t005_evidence_lease_ref.py

echo "[verify] taste T-006 (stale change intents)"
uv run python scripts/lint/taste_t006_stale_intents.py

if [ "$HAS_CARGO_MANIFEST" -eq 1 ]; then
  echo "[verify] taste T-007 (function size ≤ 60 lines)"
  uv run python scripts/lint/taste_t007_fn_size.py
else
  echo "[verify] skip T-007 (Cargo.toml not found)"
fi

echo "[verify] uv run pytest"
uv run pytest

echo "[verify] uv run mypy"
uv run mypy tools scripts

echo "[verify] uv run ruff check"
uv run ruff check tools scripts

echo "[verify] pnpm lint"
pnpm run lint

echo "[verify] pnpm prettier check"
pnpm run format:check

echo "[verify] check doc freshness (local)"
GITHUB_EVENT_NAME="" uv run python scripts/ci/check_doc_freshness.py --local
