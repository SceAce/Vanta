#!/usr/bin/env python3
"""T-002 Taste Invariant Linter — public API must have rustdoc.

Invokes `cargo doc --no-deps 2>&1` and parses the output for missing-doc
warnings on `pub` items in any crate under `crates/`.  Fails if any such
warning is found.

Exit codes:
  0  no violations
  1  one or more missing-doc warnings found
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

_MISSING_DOC_RE = re.compile(r"warning: missing documentation for ")
_LOCATION_RE = re.compile(r"\s+-->\s+(crates/.+)")


def main() -> int:
    result = subprocess.run(
        ["cargo", "doc", "--no-deps", "--workspace"],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )

    output = result.stderr + result.stdout

    violations: list[str] = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if _MISSING_DOC_RE.search(line):
            location = ""
            if i + 1 < len(lines):
                m = _LOCATION_RE.match(lines[i + 1])
                if m:
                    location = m.group(1)
                    i += 1
            msg = line.strip()
            if location:
                msg = f"{location}: {msg}"
            violations.append(msg)
        i += 1

    if violations:
        for v in violations:
            print(f"[T-002] {v}", flush=True)
        print(
            f"\nT-002 FAILED: {len(violations)} missing-doc warning(s). "
            "Add rustdoc comments to all public items in library crates.",
            flush=True,
        )
        return 1

    print("T-002 passed: all public items in crates/ have rustdoc.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
