#!/usr/bin/env python3
"""ADR policy linter — validate Architecture Decision Records.

Scans docs/architecture/decisions/ for ADR markdown files and checks:
  1. Each ADR has a valid status header (proposed, accepted, deprecated,
     superseded).
  2. Accepted ADRs include a Date field.
  3. Superseded ADRs reference their successor.
  4. File names follow the pattern NNN-slug.md.

Exit codes:
  0  no violations
  1  one or more policy violations found
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])
_ADR_DIR = _REPO_ROOT / "docs" / "architecture" / "decisions"

_FILENAME_RE = re.compile(r"^\d{3,4}-.+\.md$")
_STATUS_RE = re.compile(r"^\*?\*?Status\*?\*?:\s*(.+)", re.IGNORECASE)
_DATE_RE = re.compile(r"^\*?\*?Date\*?\*?:\s*(.+)", re.IGNORECASE)
_SUPERSEDED_RE = re.compile(r"superseded\s+by", re.IGNORECASE)

_VALID_STATUSES = {"proposed", "accepted", "deprecated", "superseded"}


def _check_adr(path: Path, violations: list[str]) -> None:
    rel = path.relative_to(_REPO_ROOT)
    name = path.name

    # Check filename convention
    if not _FILENAME_RE.match(name):
        violations.append(f"{rel}: filename does not match NNN-slug.md convention.")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    status_value: str | None = None
    has_date = False

    for line in lines:
        m_status = _STATUS_RE.match(line.strip())
        if m_status:
            status_value = m_status.group(1).strip().lower()
        m_date = _DATE_RE.match(line.strip())
        if m_date and m_date.group(1).strip():
            has_date = True

    # Check valid status
    if status_value is None:
        violations.append(f"{rel}: missing Status header.")
    elif status_value not in _VALID_STATUSES:
        violations.append(
            f"{rel}: invalid status '{status_value}'. "
            f"Must be one of: {', '.join(sorted(_VALID_STATUSES))}."
        )

    # Accepted ADRs must have a date
    if status_value == "accepted" and not has_date:
        violations.append(f"{rel}: accepted ADR is missing a Date header.")

    # Superseded ADRs must reference successor
    if status_value == "superseded" and not _SUPERSEDED_RE.search(text):
        violations.append(
            f"{rel}: superseded ADR does not reference its successor. "
            "Add 'Superseded by ADR-NNN' to the status or body."
        )


def main() -> int:
    if not _ADR_DIR.exists():
        print(
            "check_adr_policy: docs/architecture/decisions/ not found — skipping ADR checks.",
            flush=True,
        )
        return 0

    adr_files = sorted(_ADR_DIR.glob("*.md"))
    if not adr_files:
        print(
            "check_adr_policy: no ADR files found in docs/architecture/decisions/ — skipping.",
            flush=True,
        )
        return 0

    violations: list[str] = []
    for adr in adr_files:
        _check_adr(adr, violations)

    if violations:
        for v in violations:
            print(f"[ADR-POLICY] {v}", flush=True)
        print(
            f"\nADR policy check FAILED: {len(violations)} violation(s).",
            flush=True,
        )
        return 1

    print(
        f"ADR policy check passed: {len(adr_files)} ADR(s) validated.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
