#!/usr/bin/env python3
"""Codex PreToolUse hook that blocks unsigned git commit commands."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    command = extract_command(payload)
    normalized = re.sub(r"\s+", " ", command).strip()

    if not normalized:
        return 0

    if re.search(r"(^|\s)git\s+commit(\s|$)", normalized):
        has_signed_flag = re.search(r"(^|\s)-S(\s|$)", normalized)
        has_gpgsign = re.search(r"commit\.gpgsign\s+true", normalized)

        if not has_signed_flag and not has_gpgsign:
            json.dump(
                {
                    "decision": "block",
                    "reason": (
                        "This project requires signed commits. Use `git commit -S ...` "
                        "or ensure `commit.gpgsign=true` is active and explicit."
                    ),
                },
                sys.stdout,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
