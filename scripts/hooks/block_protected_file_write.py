#!/usr/bin/env python3
"""Codex PreToolUse hook that blocks Write/Edit to T0-protected files.

Bypass: the owner can authorize changes by asking the agent to create .t0-unlock
in the repo root. The agent creates the file, performs the edit, then deletes it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROTECTED: list[str] = [
    "AGENTS.md",
    "CLAUDE.md",
    "CODEX.md",
    "state/policy.json",
    ".claude/settings.json",
    ".codex",
    ".codex-config/settings.json",
    # Hook scripts are self-protecting — tampering would disable the guards.
    "scripts/hooks/block_protected_file_write.py",
    "scripts/hooks/block_protected_bash_write.py",
    "scripts/hooks/block_unsafe_git_commit.py",
    "scripts/hooks/auto_push.py",
    "scripts/hooks/block_dirty_stop.py",
    "scripts/hooks/auto_sync_check.py",
    "scripts/hooks/pre_compact_state_save.py",
    ".githooks/pre-commit",
    ".githooks/commit-msg",
]


def extract_tool_name(payload: dict[str, Any]) -> str:
    for key in ("tool_name", "tool"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_file_path(payload: dict[str, Any]) -> str:
    for key in ("tool_input", "input", "toolInput"):
        value = payload.get(key, {})
        if isinstance(value, dict):
            fp = value.get("file_path", "")
            if isinstance(fp, str) and fp.strip():
                return fp.strip()
    return ""


def is_protected(file_path: str) -> bool:
    """Return True if file_path matches or ends with any protected path."""
    fp = file_path.replace("\\", "/")
    for protected in PROTECTED:
        p = protected.replace("\\", "/")
        if fp == p or fp.endswith("/" + p):
            return True
    return False


def main() -> int:
    # Explicit user unlock — skip all protection.
    # The owner authorizes by asking the agent to create .t0-unlock in the repo root.
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / ".t0-unlock").exists():
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    tool_name = extract_tool_name(payload)
    if tool_name not in ("Write", "Edit"):
        return 0

    file_path = extract_file_path(payload)
    if not file_path:
        return 0

    if is_protected(file_path):
        json.dump(
            {
                "decision": "block",
                "reason": (
                    f"{file_path} is a T0-protected file. "
                    "Changes require a dedicated branch and a PR with T0 review. "
                    "If the owner has explicitly authorized this change in the "
                    "conversation, create the file .t0-unlock in the repo root "
                    "(touch .t0-unlock) then retry. Delete it when done "
                    "(rm .t0-unlock)."
                ),
            },
            sys.stdout,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
