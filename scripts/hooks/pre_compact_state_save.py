#!/usr/bin/env python3
"""Codex PreCompact hook: save current goal, active lease, and pending tasks
before context compression so that mid-session state is not lost.

Behavior:
- Reads optional PreCompact payload from stdin (may be empty).
- Writes a snapshot to .codex-config/pre_compact_state.json with:
    - current_goal:  extracted from the last UserPromptSubmit payload if available,
                     otherwise the git branch name as a proxy.
    - active_lease:  contents of state/policy.json lease section if present.
    - pending_tasks: from state/progress.json (milestones with status != completed).
    - timestamp:     ISO-8601 UTC.
- Always exits 0 (never blocks compaction).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_DIR / ".codex-config" / "pre_compact_state.json"


def _read_stdin() -> dict[str, object]:
    try:
        raw = sys.stdin.read()
        result = json.loads(raw) if raw.strip() else {}
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}


def _branch_name() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _load_json(path: Path) -> dict[str, object] | list[object] | None:
    try:
        parsed: dict[str, object] | list[object] = json.loads(path.read_text())
        return parsed
    except Exception:
        return None


def main() -> int:
    payload = _read_stdin()

    # Derive current goal: prefer explicit field, fall back to branch name
    current_goal: str = str(payload.get("current_goal") or _branch_name())

    # Active lease from policy.json
    policy_raw = _load_json(PROJECT_DIR / "state" / "policy.json")
    policy: dict[str, object] = policy_raw if isinstance(policy_raw, dict) else {}
    active_lease = policy.get("lease") or policy.get("active_lease") or {}

    # Pending milestones from progress.json
    progress_raw = _load_json(PROJECT_DIR / "state" / "progress.json")
    progress: dict[str, object] = progress_raw if isinstance(progress_raw, dict) else {}
    milestones_raw = progress.get("milestones", [])
    milestones: list[object] = milestones_raw if isinstance(milestones_raw, list) else []
    pending_tasks = [
        {"id": m.get("id"), "title": m.get("title"), "status": m.get("status")}
        for m in milestones
        if isinstance(m, dict) and m.get("status") not in ("completed", "skipped")
    ]

    snapshot = {
        "timestamp": datetime.now(UTC).isoformat(),
        "current_goal": current_goal,
        "active_lease": active_lease,
        "pending_tasks": pending_tasks,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(snapshot, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
