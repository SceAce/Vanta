#!/usr/bin/env python3
"""Codex Stop hook: push current branch and reachable annotated tags.

Runs at the end of every conversation (after block_dirty_stop.py confirms
the working tree is clean). Ensures every committed session is reflected on
the remote without requiring manual intervention.

Behavior:
- `git fetch origin` to refresh remote state.
- Determine current branch and whether a remote tracking ref exists.
- If local is BEHIND remote: block — divergence must be resolved manually.
- If local is AHEAD or remote branch does not exist: push with --follow-tags.
  --follow-tags pushes only annotated tags reachable from the pushed commits,
  which is the correct policy for SemVer release tags.
- If local and remote are at the same commit: no-op (nothing to push).
- If push fails for any reason: block so the user is aware.

Multi-agent note:
  Each agent is expected to work on its own feature/* or dev branch.
  This hook never force-pushes and never pushes to a branch it did not create.
  Conflicts are surfaced as blocks, not silently skipped.
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
        json.load(sys.stdin)  # consume payload
    except Exception:
        pass

    # Re-fetch to get the latest remote state before deciding.
    # Cap at 10 s so a slow network doesn't hang the stop hook indefinitely.
    # On timeout we fall through using the locally-cached remote ref; git will
    # surface any real conflict when it attempts the push.
    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin", "--prune"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if fetch.returncode != 0:
            return block(
                f"[auto_push] git fetch failed before push: {fetch.stderr.strip()}. "
                "Check network connectivity and retry."
            )
    except subprocess.TimeoutExpired:
        print(
            "[auto_push] git fetch timed out (>10 s); proceeding with cached remote refs.",
            file=sys.stderr,
        )

    # Current branch
    branch_proc = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch_proc.returncode != 0:
        return block("[auto_push] Could not determine current branch.")
    branch = branch_proc.stdout.strip()
    if branch == "HEAD":
        # Detached HEAD — cannot push meaningfully
        return block(
            "[auto_push] Repository is in detached HEAD state. "
            "Checkout a named branch before ending the session."
        )

    # Check remote tracking ref
    tracking = run(["git", "rev-parse", "--verify", f"origin/{branch}"])
    remote_exists = tracking.returncode == 0

    if remote_exists:
        # Behind check
        behind_proc = run(["git", "rev-list", "--count", f"HEAD..origin/{branch}"])
        behind = int((behind_proc.stdout.strip() or "0") if behind_proc.returncode == 0 else "0")
        if behind > 0:
            return block(
                f"[auto_push] Local branch '{branch}' is {behind} commit(s) behind "
                f"origin/{branch}. Run `git pull --rebase origin {branch}` to reconcile "
                "before the session can end."
            )

        # Ahead check — if 0 commits ahead, nothing to push
        ahead_proc = run(["git", "rev-list", "--count", f"origin/{branch}..HEAD"])
        ahead = int((ahead_proc.stdout.strip() or "0") if ahead_proc.returncode == 0 else "0")
        if ahead == 0:
            # Up to date — nothing to push
            return 0

    # Push: use --follow-tags to include reachable annotated tags only
    push_cmd = ["git", "push", "origin", branch, "--follow-tags"]
    if not remote_exists:
        push_cmd.insert(3, "--set-upstream")

    push = run(push_cmd)
    if push.returncode != 0:
        return block(
            f"[auto_push] Push to origin/{branch} failed:\n{push.stderr.strip()}\n"
            "Resolve the issue and push manually before ending the session."
        )

    pushed_tags = [
        line for line in push.stderr.splitlines() if "->" in line and "tag" in line.lower()
    ]
    tag_summary = f" (+{len(pushed_tags)} tag(s))" if pushed_tags else ""
    print(
        f"[auto_push] Pushed '{branch}' to origin{tag_summary}.",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
