#!/usr/bin/env python3
"""T-007 Taste Invariant Linter — no non-test function exceeds 60 lines.

Walks all `.rs` files under `crates/`.  Test files (inside `tests/` directories
or ending with `_test.rs`) and functions inside `#[cfg(test)]` blocks are
excluded.  Any non-test function exceeding 60 lines emits a violation.

Exit codes:
  0  no violations
  1  one or more functions exceed the limit
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])
_CRATES_DIR = _REPO_ROOT / "crates"
_FN_LIMIT = 60

_FN_RE = re.compile(r"^\s*(pub\s+)?(pub\s*\([^)]*\)\s+)?(async\s+)?(unsafe\s+)?fn\s+(\w+)")


def _is_test_file(path: Path) -> bool:
    if "tests" in path.parts:
        return True
    return path.stem.endswith(("_test", "_tests"))


def _check_file(path: Path) -> list[tuple[str, int, int]]:
    """Return (fn_name, start_line_1based, size) for oversized non-test functions."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    oversized: list[tuple[str, int, int]] = []

    depth = 0
    cfg_test_pending = False
    cfg_test_outer: int | None = None

    fn_start: int | None = None
    fn_name: str | None = None
    fn_open_pending = False
    fn_body_depth: int | None = None

    for i, line in enumerate(lines):
        open_b = line.count("{")
        close_b = line.count("}")
        depth_before = depth
        depth += open_b - close_b

        if "#[cfg(test)]" in line:
            cfg_test_pending = True

        if cfg_test_pending and open_b > 0 and cfg_test_outer is None:
            cfg_test_outer = depth_before
            cfg_test_pending = False

        in_cfg_test = cfg_test_outer is not None

        if in_cfg_test and cfg_test_outer is not None and depth <= cfg_test_outer:
            cfg_test_outer = None
            in_cfg_test = False

        if in_cfg_test:
            fn_start = None
            fn_name = None
            fn_open_pending = False
            fn_body_depth = None
            continue

        if fn_start is None:
            m = _FN_RE.match(line)
            if m:
                fn_start = i
                fn_name = m.group(5)
                fn_open_pending = True
                fn_body_depth = depth_before + 1

        if fn_open_pending:
            if open_b > 0:
                fn_open_pending = False
            elif ";" in line:
                fn_start = None
                fn_name = None
                fn_open_pending = False
                fn_body_depth = None

        if (
            not fn_open_pending
            and fn_start is not None
            and fn_body_depth is not None
            and depth < fn_body_depth
        ):
            size = i - fn_start + 1
            if size > _FN_LIMIT:
                oversized.append((fn_name or "?", fn_start + 1, size))
            fn_start = None
            fn_name = None
            fn_body_depth = None

    return oversized


def main() -> int:
    if not _CRATES_DIR.exists():
        print(f"T-007: crates/ directory not found at {_CRATES_DIR}", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    for rs_file in sorted(_CRATES_DIR.rglob("*.rs")):
        if _is_test_file(rs_file):
            continue
        rel = rs_file.relative_to(_REPO_ROOT)
        for fn_name, start_line, size in _check_file(rs_file):
            all_violations.append(
                f"{rel}:{start_line}: fn `{fn_name}` is {size} lines "
                f"(limit {_FN_LIMIT}). Extract helpers to reduce size (T-007)."
            )

    if all_violations:
        for v in all_violations:
            print(f"[T-007] {v}", flush=True)
        print(
            f"\nT-007 FAILED: {len(all_violations)} function(s) exceed {_FN_LIMIT} lines.",
            flush=True,
        )
        return 1

    print(
        f"T-007 passed: all non-test functions in crates/ are within {_FN_LIMIT} lines.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
