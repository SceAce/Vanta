#!/usr/bin/env python3
"""Signing-config linter — verify git commit-signing is configured.

Checks the local (repo-level) and global git config for:
  1. commit.gpgSign = true
  2. tag.gpgSign = true  (warning only)
  3. A signing key is configured (user.signingKey or gpg.format + key)

This linter does NOT enforce a specific key format — GPG, SSH, and
X.509 are all accepted.

Exit codes:
  0  signing is properly configured
  1  signing is not configured or partially configured
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])


def _git_config(key: str) -> str | None:
    """Read a git config value, checking local then global scope."""
    for scope in ("--local", "--global"):
        try:
            result = subprocess.run(
                ["git", "config", scope, key],
                capture_output=True,
                text=True,
                cwd=_REPO_ROOT,
            )
            val = result.stdout.strip()
            if val:
                return val
        except FileNotFoundError:
            return None
    return None


def main() -> int:
    violations: list[str] = []
    warnings: list[str] = []

    # 1. commit.gpgSign
    commit_sign = _git_config("commit.gpgSign")
    if commit_sign is None or commit_sign.lower() != "true":
        violations.append(
            "commit.gpgSign is not set to 'true'. Run: git config --local commit.gpgSign true"
        )

    # 2. tag.gpgSign (advisory)
    tag_sign = _git_config("tag.gpgSign")
    if tag_sign is None or tag_sign.lower() != "true":
        warnings.append(
            "tag.gpgSign is not set to 'true' (recommended). "
            "Run: git config --local tag.gpgSign true"
        )

    # 3. Signing key
    signing_key = _git_config("user.signingKey")
    gpg_format = _git_config("gpg.format")
    if not signing_key:
        violations.append(
            "No user.signingKey configured. "
            "Set a GPG or SSH signing key: git config --local user.signingKey <KEY>"
        )

    # Print results
    for w in warnings:
        print(f"[SIGNING-CONFIG] WARNING: {w}", flush=True)

    if violations:
        for v in violations:
            print(f"[SIGNING-CONFIG] {v}", flush=True)
        print(
            f"\nSigning config check FAILED: {len(violations)} issue(s). "
            "Commit signing must be enabled for this repository.",
            flush=True,
        )
        return 1

    fmt_note = f" (format: {gpg_format})" if gpg_format else ""
    print(
        f"Signing config check passed: commit signing is enabled{fmt_note}.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
