#!/usr/bin/env python3
"""T-006 Taste Invariant Linter — stale open change intents.

Scans state/progress.json for change-intent entries (or feature entries)
whose status is open or in_progress and whose updated_at timestamp is
older than STALE_DAYS days. Emits a warning for each stale entry.

Exit codes:
  0  no violations
  1  one or more stale intents found
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])
_PROGRESS = _REPO_ROOT / "state" / "progress.json"

STALE_DAYS = 7
_STALE_STATUSES = {"open", "in_progress", "draft"}


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(ts, fmt)
            return dt.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _check_progress(violations: list[str], now: datetime) -> None:
    if not _PROGRESS.exists():
        return
    try:
        data = json.loads(_PROGRESS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    cutoff = now - timedelta(days=STALE_DAYS)

    change_intents = data.get("change_intents", [])
    for ci in change_intents:
        if not isinstance(ci, dict):
            continue
        status = ci.get("status", "")
        if status not in _STALE_STATUSES:
            continue
        cid = ci.get("id") or ci.get("intent_id") or "<unknown>"
        ts_str = ci.get("updated_at") or ci.get("created_at") or ci.get("detected_at")
        ts = _parse_ts(ts_str)
        if ts is not None and ts < cutoff:
            age_days = (now - ts).days
            violations.append(
                f"state/progress.json: change_intent '{cid}' has status '{status}' "
                f"and has not been updated in {age_days} days (threshold: {STALE_DAYS}). "
                "Close, defer, or advance this intent (T-006)."
            )

    features = data.get("features", {})
    if isinstance(features, list):
        items: list[Any] = features
    elif isinstance(features, dict):
        items = list(features.values())
    else:
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        status = item.get("status", "")
        if status not in _STALE_STATUSES:
            continue
        fid = item.get("id") or item.get("feature_id") or "<unknown>"
        ts_str = item.get("updated_at") or item.get("created_at")
        ts = _parse_ts(ts_str)
        if ts is not None and ts < cutoff:
            age_days = (now - ts).days
            violations.append(
                f"state/progress.json: feature '{fid}' has status '{status}' "
                f"and has not been updated in {age_days} days (threshold: {STALE_DAYS}). "
                "Advance or close this feature entry (T-006)."
            )


def main() -> int:
    now = datetime.now(UTC)
    violations: list[str] = []
    _check_progress(violations, now)

    if violations:
        for v in violations:
            print(f"[T-006] {v}", flush=True)
        print(
            f"\nT-006 FAILED: {len(violations)} stale open change intent(s). "
            f"All open/in_progress intents must show activity within {STALE_DAYS} days "
            "(T-006).",
            flush=True,
        )
        return 1

    print(
        f"T-006 passed: no stale open change intents (threshold: {STALE_DAYS} days).",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
