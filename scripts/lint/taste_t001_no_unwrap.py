#!/usr/bin/env python3
"""T-001 Taste Invariant Linter — no raw `.unwrap()` in library crates.

Scans all `.rs` files under `crates/` for `.unwrap()` calls that are NOT
inside a `#[cfg(test)]` block.  Suggests using `?` or an explicit error
type instead.

Exit codes:
  0  no violations
  1  one or more violations found
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])
_CRATES_DIR = _REPO_ROOT / "crates"

_UNWRAP_RE = re.compile(r"\.unwrap\(\)")


def _is_test_attr(line: str) -> bool:
    s = line.strip()
    return s.startswith("#[cfg(test)]") or s.startswith("#[test]")


def check_file(path: Path) -> list[str]:
    """Return a list of violation strings for *path*."""
    violations: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    in_test_block = False
    brace_depth = 0
    test_start_depth = 0
    pending_test_attr = False

    for lineno, raw in enumerate(lines, start=1):
        if _is_test_attr(raw):
            pending_test_attr = True

        opens = raw.count("{")
        closes = raw.count("}")

        if pending_test_attr and "{" in raw:
            in_test_block = True
            test_start_depth = brace_depth
            pending_test_attr = False

        brace_depth += opens - closes

        if in_test_block and brace_depth <= test_start_depth:
            in_test_block = False

        if in_test_block:
            continue

        code_part = raw.strip().split("//")[0]
        if _UNWRAP_RE.search(code_part):
            rel = path.relative_to(_REPO_ROOT)
            violations.append(
                f"{rel}:{lineno}: T-001 bare `.unwrap()` outside test block. "
                f"Replace with `?`, `map_err`, or a typed error."
            )

    return violations


def main() -> int:
    if not _CRATES_DIR.exists():
        print(f"T-001: crates/ directory not found at {_CRATES_DIR}", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    for rs_file in sorted(_CRATES_DIR.rglob("*.rs")):
        all_violations.extend(check_file(rs_file))

    if all_violations:
        for v in all_violations:
            print(f"[T-001] {v}", flush=True)
        print(
            f"\nT-001 FAILED: {len(all_violations)} violation(s). "
            "Use `?` or explicit error types instead of `.unwrap()` in library crates.",
            flush=True,
        )
        return 1

    print(
        f"T-001 passed: no bare .unwrap() found in {_CRATES_DIR.relative_to(_REPO_ROOT)}/.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
