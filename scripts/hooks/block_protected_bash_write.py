#!/usr/bin/env python3
"""Codex PreToolUse hook that blocks Bash commands writing to T0-protected files.

Detects write operations across all common languages and tools:
- Shell: >, >>, tee, cp, mv, install, rsync, sed -i, awk, dd, truncate, patch
- Python: Path().write_text/write_bytes, open() with write modes, python -c write
- Ruby: File.write, File.open, IO.write, IO.sysopen
- Node.js: fs.writeFile, fs.writeFileSync, fs.appendFile
- Perl: open(FH, ">..."), sysopen
- Here-docs: cat << ... > file
- Batch tools: xargs cp/mv, find -exec cp/mv

Bypass: the owner can authorize changes by asking the agent to create .t0-unlock
in the repo root. The agent creates the file, performs the edit, then deletes it.
"""

from __future__ import annotations

import json
import re
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


def extract_command(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("tool_input", {}).get("command"),
        payload.get("input", {}).get("command"),
        payload.get("command"),
        payload.get("toolInput", {}).get("command"),
    ]
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _file_variants(path: str) -> list[str]:
    """Return the full path and its basename as search variants."""
    variants = [path]
    basename = path.split("/")[-1]
    if basename != path:
        variants.append(basename)
    return variants


def command_writes_to_file(command: str, protected_path: str) -> bool:
    """Return True if the command appears to write to the protected path."""
    for variant in _file_variants(protected_path):
        e = re.escape(variant)
        checks = [
            # ── Shell builtins and redirects ──
            rf">+\s*[\x27\x22]?{e}[\x27\x22]?(\s|$|;|&&|\|\|)",
            rf"\btee\b[^|]*\b{e}\b",
            rf"\b(?:cp|mv|install)\b.*\s[\x27\x22]?{e}[\x27\x22]?(\s|$|;)",
            rf"\brsync\b.*\s[\x27\x22]?{e}[\x27\x22]?(\s|$|;)",
            rf"\bsed\b.*-i.*\b{e}\b",
            rf"\bsed\b.*\b{e}\b.*-i",
            rf"\bawk\b.*>\s*[\x27\x22]?{e}[\x27\x22]?",
            rf"\bdd\b.*\bof=[\x27\x22]?{e}[\x27\x22]?",
            rf"\btruncate\b.*\b{e}\b",
            rf"\bpatch\b.*\b{e}\b",
            rf"\bgit\b.+\b(?:checkout|restore|show)\b.*\b{e}\b",
            # ── Here-doc to file ──
            rf"cat\s*<<.*>\s*[\x27\x22]?{e}",
            rf"cat\s*>\s*[\x27\x22]?{e}",
            # ── Python ──
            rf"open\([\x27\x22]?{e}[\x27\x22]?\s*,\s*[\x27\x22](?:w|wb|a|ab|w\+|a\+|r\+)[\x27\x22]",
            rf"Path\([\x27\x22]?{e}[\x27\x22]?\)\s*\.\s*write_",
            rf"Path\([\x27\x22]?{e}[\x27\x22]?\)\s*\.\s*open\(",
            rf"python[23]?\s+-c\s+.*{e}.*(?:write|dump)",
            rf"python[23]?\s+-c\s+.*(?:write|dump).*{e}",
            rf"\.write_text\(.*{e}",
            rf"\.write_bytes\(.*{e}",
            rf"pathlib.*{e}.*write",
            # ── Ruby ──
            rf"File\.(?:write|open|new)\([\x27\x22]?{e}",
            rf"IO\.(?:write|sysopen)\([\x27\x22]?{e}",
            rf"ruby\b.*-e\b.*{e}.*(?:write|open)",
            # ── Node.js ──
            rf"fs\.(?:writeFile|writeFileSync|appendFile|appendFileSync)\([\x27\x22]?{e}",
            rf"writeFileSync\([\x27\x22]?{e}",
            rf"node\b.*-e\b.*{e}.*(?:write|append)",
            # ── Perl ──
            rf"perl\b.*-e\b.*{e}.*(?:open|write|print)",
            rf"open\s*\(.*[>]+.*{e}",
            rf"sysopen\s*\(.*{e}",
            # ── Batch tools ──
            rf"xargs.*\b(?:cp|mv|tee)\b.*{e}",
            rf"find\b.*-exec.*\b(?:cp|mv)\b.*{e}",
            # ── Catch-all: any interpreter writing to file ──
            rf"(?:python|ruby|node|perl|lua|php).*{e}.*(?:\.write|>|dump|save|output)",
        ]
        for pattern in checks:
            if re.search(pattern, command):
                return True
    return False


def main() -> int:
    # Explicit user unlock — skip all protection.
    # The owner authorizes by asking the agent to create .t0-unlock in the repo root.
    # The agent creates the file, performs the edit, then deletes it.
    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / ".t0-unlock").exists():
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    tool_name = ""
    for key in ("tool_name", "tool"):
        v = payload.get(key)
        if isinstance(v, str) and v.strip():
            tool_name = v.strip()
            break
    if tool_name != "Bash":
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    for protected in PROTECTED:
        if command_writes_to_file(command, protected):
            json.dump(
                {
                    "decision": "block",
                    "reason": (
                        f"Attempted Bash write to T0-protected file '{protected}'. "
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
