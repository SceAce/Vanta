#!/usr/bin/env python3
"""T-005 Taste Invariant Linter — evidence-lease ref completeness.

Scans state/progress.json for feature entries whose status is
candidate_complete or verified_complete and checks that each has a
non-empty evidence_ref (or evidence_bundle_ref) field.  Also checks
state/completion-ledger.json items for required evidence_ref.

Exit codes:
  0  no violations
  1  one or more missing evidence refs found
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])
_PROGRESS = _REPO_ROOT / "state" / "progress.json"
_LEDGER = _REPO_ROOT / "state" / "completion-ledger.json"

_COMPLETE_STATUSES = {"candidate_complete", "verified_complete"}


def _check_progress(violations: list[str]) -> None:
    if not _PROGRESS.exists():
        return
    try:
        data = json.loads(_PROGRESS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    features = data.get("features", {})
    if isinstance(features, list):
        items = features
    elif isinstance(features, dict):
        items = list(features.values())
    else:
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status", "")
        if status not in _COMPLETE_STATUSES:
            continue
        fid = item.get("id") or item.get("feature_id") or "<unknown>"
        ref = (
            item.get("evidence_ref")
            or item.get("evidence_bundle_ref")
            or item.get("evidence_bundle_refs")
        )
        if not ref:
            violations.append(
                f"state/progress.json: feature '{fid}' has status '{status}' "
                "but is missing evidence_ref. "
                "Attach an evidence bundle before marking complete (T-005)."
            )


def _check_completion_ledger(violations: list[str]) -> None:
    if not _LEDGER.exists():
        return
    try:
        data = json.loads(_LEDGER.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    entries = data.get("entries", [])
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        eid = entry.get("id") or entry.get("feature_id") or "<unknown>"
        refs = (
            entry.get("evidence_ref")
            or entry.get("evidence_bundle_ref")
            or entry.get("evidence_bundle_refs")
        )
        if not refs:
            violations.append(
                f"state/completion-ledger.json: entry '{eid}' is missing evidence_ref. "
                "Every completion ledger entry must point to an evidence bundle (T-005)."
            )


def main() -> int:
    violations: list[str] = []
    _check_progress(violations)
    _check_completion_ledger(violations)

    if violations:
        for v in violations:
            print(f"[T-005] {v}", flush=True)
        print(
            f"\nT-005 FAILED: {len(violations)} missing evidence-lease ref(s). "
            "Every candidate_complete / verified_complete feature must have an "
            "evidence_ref field (T-005).",
            flush=True,
        )
        return 1

    print("T-005 passed: all complete features carry evidence refs.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
