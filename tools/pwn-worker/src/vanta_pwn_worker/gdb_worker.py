"""Long-lived GDB session support for Vanta pwn analysis."""

from __future__ import annotations

import os
import select
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


class GdbWorkerError(Exception):
    """Raised when a GDB session cannot complete a requested action."""


@dataclass
class GdbSession:
    """A long-lived GDB CLI session."""

    session_id: str
    process: subprocess.Popen[str]
    timeout_seconds: float

    def command(self, command: str) -> str:
        """Run one command in the GDB session and return text output."""

        if self.process.stdin is None:
            raise GdbWorkerError("GDB stdin is unavailable")
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        return self._read_until_prompt()

    def close(self) -> None:
        """Close the GDB process."""

        if self.process.poll() is not None:
            return
        if self.process.stdin is not None:
            self.process.stdin.write("quit\n")
            self.process.stdin.flush()
        try:
            self.process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            self.process.terminate()

    def _read_until_prompt(self) -> str:
        if self.process.stdout is None:
            raise GdbWorkerError("GDB stdout is unavailable")
        deadline = time.monotonic() + self.timeout_seconds
        chunks: list[str] = []
        fd = self.process.stdout.fileno()
        while time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.05)
            if not ready:
                if self.process.poll() is not None:
                    break
                continue
            chunk = os.read(fd, 4096).decode(errors="replace")
            chunks.append(chunk)
            if "(gdb)" in chunk:
                return "".join(chunks).replace("(gdb)", "").strip()
        raise GdbWorkerError("timed out waiting for GDB prompt")


class GdbManager:
    """Manages long-lived GDB sessions for JSON-RPC calls."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout_seconds = timeout_seconds
        self._sessions: dict[str, GdbSession] = {}

    def status(self) -> JsonObject:
        """Return local GDB availability and active session count."""

        gdb_path = shutil.which("gdb")
        return {
            "available": gdb_path is not None,
            "gdb_path": gdb_path,
            "active_sessions": len(self._sessions),
        }

    def start(self, binary_path: str | None = None, pwndbg: bool = True) -> JsonObject:
        """Start a long-lived GDB session."""

        gdb_path = shutil.which("gdb")
        if gdb_path is None:
            return {"started": False, "reason": "gdb not found in PATH"}
        command = [gdb_path, "--quiet", "-iex", "set pagination off"]
        if not pwndbg:
            command.append("--nx")
        if binary_path:
            command.append(str(Path(binary_path)))
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
        )
        session = GdbSession(str(uuid.uuid4()), process, self._timeout_seconds)
        try:
            banner = session._read_until_prompt()
        except GdbWorkerError:
            session.close()
            raise
        self._sessions[session.session_id] = session
        return {
            "started": True,
            "session_id": session.session_id,
            "binary_path": binary_path,
            "pwndbg_requested": pwndbg,
            "banner": compact_output(banner),
        }

    def command(self, session_id: str, command: str) -> JsonObject:
        """Run a command in an existing session."""

        session = self._get_session(session_id)
        output = session.command(command)
        return {"session_id": session_id, "command": command, "output": compact_output(output)}

    def snapshot(self, session_id: str) -> JsonObject:
        """Collect registers, stack, maps, and backtrace summaries."""

        session = self._get_session(session_id)
        return {
            "session_id": session_id,
            "registers": compact_output(session.command("info registers")),
            "stack": compact_output(session.command("x/32gx $rsp")),
            "maps": compact_output(session.command("info proc mappings")),
            "backtrace": compact_output(session.command("bt")),
        }

    def stop(self, session_id: str) -> JsonObject:
        """Stop a GDB session."""

        session = self._sessions.pop(session_id, None)
        if session is None:
            return {"stopped": False, "reason": "unknown session_id"}
        session.close()
        return {"stopped": True, "session_id": session_id}

    def _get_session(self, session_id: str) -> GdbSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise GdbWorkerError("unknown session_id")
        return session


def compact_output(output: str, limit: int = 12000) -> str:
    """Trim tool output to an evidence-friendly size."""

    if len(output) <= limit:
        return output
    return output[:limit] + "\n[truncated]"
