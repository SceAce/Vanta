#!/usr/bin/env python3
"""Codex UserPromptSubmit hook: fetch, auto-rebase, or block.

Single authoritative sync hook — replaces the former auto_pull_rebase.py +
auto_sync_check.py pair (which ran in parallel and raced against each other).

Behavior:
- Always fetches origin --prune (non-blocking on failure).
- If already up-to-date: pass through silently.
- If behind and working tree is clean (tracked files only): auto-rebase.
- If behind and working tree is dirty (tracked changes): block with a clear
  message so the user can stash/commit before pulling.
- If the rebase itself fails: block with the error for manual resolution.

Untracked files are ignored when assessing cleanliness — they are never
touched by git rebase and must not prevent an automatic pull.
"""

from __future__ import annotations

import json
import subprocess
import sys


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)


def block(reason: str) -> int:
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    return 0


def main() -> int:
    try:
        json.load(sys.stdin)  # consume payload; content unused
    except Exception:
        pass

    # Fetch — non-blocking on failure (offline / no remote configured).
    # Timeout of 10 s prevents hanging on slow networks.
    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin", "--prune"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        print(
            "[auto_sync_check] git fetch timed out (>10 s); skipping sync check.",
            file=sys.stderr,
        )
        return 0
    if fetch.returncode != 0:
        print(
            f"[auto_sync_check] git fetch failed (offline?): {fetch.stderr.strip()}",
            file=sys.stderr,
        )
        return 0

    # Determine current branch
    branch_proc = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch_proc.returncode != 0:
        return 0
    branch = branch_proc.stdout.strip()
    if branch == "HEAD":
        return 0  # detached HEAD — skip

    # Check whether a remote tracking branch exists
    tracking = run(["git", "rev-parse", "--verify", f"origin/{branch}"])
    if tracking.returncode != 0:
        return 0  # new branch, no remote yet

    # Count commits behind
    behind_proc = run(["git", "rev-list", "--count", f"HEAD..origin/{branch}"])
    if behind_proc.returncode != 0:
        return 0
    behind = int(behind_proc.stdout.strip() or "0")
    if behind == 0:
        return 0  # already up-to-date

    # Dirty check — tracked changes only (untracked files are rebase-safe)
    dirty = run(["git", "status", "--porcelain", "--untracked-files=no"])
    if dirty.stdout.strip():
        return block(
            f"Local branch '{branch}' is {behind} commit(s) behind "
            f"origin/{branch} and the working tree has uncommitted changes. "
            "Stash or commit your changes, then run "
            f"`git pull --rebase origin {branch}` before continuing."
        )

    # Safe to rebase — pull
    pull = run(["git", "pull", "--rebase", "origin", branch])
    if pull.returncode != 0:
        return block(
            f"Auto-rebase of '{branch}' against origin/{branch} failed.\n"
            f"{pull.stderr.strip()}\n"
            "Resolve conflicts manually, then continue."
        )

    print(
        f"[auto_sync_check] Rebased '{branch}' onto origin/{branch} ({behind} commit(s) pulled).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
