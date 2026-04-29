#!/usr/bin/env python3
"""T-003 Taste Invariant Linter — no marker comments in production code.

Scans ALL source files under crates/, apps/, tools/, and sdks/ for bare
marker comments. Supported: Rust, Python, TypeScript, JavaScript, CSS,
SCSS, SQL, TOML, YAML, Shell.

Marker comments are undocumented technical debt: they belong in a tracked
GitHub issue, not in source files.

Exit codes:
  0  no violations
  1  one or more violations found
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])

_SCAN_DIRS = ["crates", "apps", "tools", "sdks"]

# Build marker keywords via concatenation to avoid self-detection.
_MARKERS = "|".join(["TO" + "DO", "FIX" + "ME", "HA" + "CK", "ST" + "UB", "X" + "XX"])

# Comment patterns per file extension.
_COMMENT_PATTERNS: dict[str, re.Pattern[str]] = {}
for _ext in (".rs", ".ts", ".tsx", ".js", ".jsx"):
    _COMMENT_PATTERNS[_ext] = re.compile(rf"//[^\n]*\b({_MARKERS})\b")
for _ext in (".py", ".toml", ".yml", ".yaml", ".sh"):
    _COMMENT_PATTERNS[_ext] = re.compile(rf"#[^\n]*\b({_MARKERS})\b")
_COMMENT_PATTERNS[".sql"] = re.compile(rf"--[^\n]*\b({_MARKERS})\b")
for _ext in (".css", ".scss"):
    _COMMENT_PATTERNS[_ext] = re.compile(rf"(/\*|//)[^\n]*\b({_MARKERS})\b")

_TEST_PATTERNS = ["tests/", "test_", "_test.", "__tests__/", ".test.", ".spec.", "__mocks__/"]

_SKIP_DIRS = {"node_modules", "dist", "target", "__pycache__", ".venv"}


def _is_test_path(path: Path) -> bool:
    s = str(path)
    return any(pattern in s for pattern in _TEST_PATTERNS)


def _in_rust_test_block(lines: list[str], target_idx: int) -> bool:
    depth = 0
    for i in range(target_idx, -1, -1):
        line = lines[i]
        depth += line.count("}") - line.count("{")
        if re.search(r"#\[cfg\(test\)\]", line):
            return depth <= 0
    return False


def check_file(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    pattern = _COMMENT_PATTERNS.get(suffix)
    if pattern is None:
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    lines = text.splitlines()
    violations: list[str] = []

    for i, line in enumerate(lines):
        if not pattern.search(line):
            continue
        if suffix == ".rs" and _in_rust_test_block(lines, i):
            continue
        if suffix in (".py", ".ts", ".tsx", ".js", ".jsx") and _is_test_path(path):
            continue

        rel = path.relative_to(_REPO_ROOT)
        violations.append(f"{rel}:{i + 1}: {line.strip()}")

    return violations


def main() -> int:
    all_violations: list[str] = []

    for dir_name in _SCAN_DIRS:
        directory = _REPO_ROOT / dir_name
        if not directory.exists():
            continue
        for source_file in sorted(directory.rglob("*")):
            if not source_file.is_file():
                continue
            if source_file.suffix.lower() not in _COMMENT_PATTERNS:
                continue
            if any(p in source_file.parts for p in _SKIP_DIRS):
                continue
            all_violations.extend(check_file(source_file))

    scanned = ", ".join(d for d in _SCAN_DIRS if (_REPO_ROOT / d).exists())

    if all_violations:
        for v in all_violations:
            print(f"[T-003] {v}", flush=True)
        print(
            f"\nT-003 FAILED: {len(all_violations)} violation(s). "
            "Remove marker comments from production code. "
            "Track the work in a GitHub issue instead.",
            flush=True,
        )
        return 1

    print(f"T-003 passed: no marker comments found in {scanned}.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
