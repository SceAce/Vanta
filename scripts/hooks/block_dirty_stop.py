#!/usr/bin/env python3
"""Codex Stop/SubagentStop hook that blocks stopping on a dirty worktree."""

from __future__ import annotations

import json
import subprocess
import sys


def git_dirty() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def main() -> int:
    _ = sys.stdin.read()
    if git_dirty():
        json.dump(
            {
                "decision": "block",
                "reason": (
                    "Repository is not clean. Update progress/test/changelog "
                    "state and leave an explainable handoff before stopping."
                ),
            },
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
