#!/usr/bin/env python3
"""Repository policy linter — verify required files, structure, and policy invariants.

Checks:
  1. Required files and directories exist in the repo root.
  2. state/policy.json exists and contains the expected policy invariants
     set to true.

Exit codes:
  0  all checks pass
  1  one or more violations found
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])

# ── Required paths (relative to repo root) ──────────────────────────────
_REQUIRED_FILES: list[str] = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "CODEX.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "state/policy.json",
    "state/progress.json",
    "state/test-report.json",
    "state/feature-manifest.json",
    "state/benchmark-baseline.json",
]

_REQUIRED_DIRS: list[str] = [
    "docs/",
    "specs/",
]

# ── Policy invariants expected in state/policy.json ─────────────────────
_REQUIRED_INVARIANTS: list[str] = [
    "require_signed_commits",
    "require_verify_green_before_commit",
    "require_docs_update",
    "require_progress_update",
    "require_real_timestamps",
]


def _check_required_files(violations: list[str]) -> None:
    for rel in _REQUIRED_FILES:
        p = _REPO_ROOT / rel
        if not p.exists():
            violations.append(f"Missing required file: {rel}")
        elif p.stat().st_size == 0:
            violations.append(f"Required file is empty: {rel}")


def _check_required_dirs(violations: list[str]) -> None:
    for rel in _REQUIRED_DIRS:
        p = _REPO_ROOT / rel
        if not p.is_dir():
            violations.append(f"Missing required directory: {rel}/")


def _check_policy_invariants(violations: list[str]) -> None:
    policy_path = _REPO_ROOT / "state" / "policy.json"
    if not policy_path.exists():
        # Already reported as missing file — skip invariant check.
        return
    try:
        data = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        violations.append(f"state/policy.json: invalid JSON — {exc}")
        return

    invariants = data.get("invariants", data)
    if not isinstance(invariants, dict):
        violations.append(
            "state/policy.json: expected top-level 'invariants' object or "
            "a flat key-value structure."
        )
        return

    for key in _REQUIRED_INVARIANTS:
        val = invariants.get(key)
        if val is None:
            violations.append(f"state/policy.json: missing policy invariant '{key}'.")
        elif val is not True:
            violations.append(f"state/policy.json: invariant '{key}' must be true (got {val!r}).")


def main() -> int:
    violations: list[str] = []
    _check_required_files(violations)
    _check_required_dirs(violations)
    _check_policy_invariants(violations)

    if violations:
        for v in violations:
            print(f"[REPO-POLICY] {v}", flush=True)
        print(
            f"\nRepo policy check FAILED: {len(violations)} violation(s).",
            flush=True,
        )
        return 1

    print("Repo policy check passed: all required files and invariants verified.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
