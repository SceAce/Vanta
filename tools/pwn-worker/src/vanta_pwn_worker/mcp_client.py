"""Minimal stdio MCP client for IDA integration."""

from __future__ import annotations

import json
import os
import select
import shlex
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class McpTool:
    """Tool exposed by an MCP server."""

    name: str
    description: str


class McpClientError(Exception):
    """Raised when an MCP stdio request fails."""


class StdioMcpClient:
    """Short-lived JSON-RPC client for newline-delimited MCP stdio servers."""

    def __init__(self, command: Sequence[str], timeout_seconds: float = 10.0) -> None:
        if not command:
            raise McpClientError("MCP command is empty")
        self._command = list(command)
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_command_line(cls, command_line: str, timeout_seconds: float = 10.0) -> StdioMcpClient:
        """Create a client from a shell-like command line without invoking a shell."""

        return cls(shlex.split(command_line), timeout_seconds)

    def list_tools(self) -> list[McpTool]:
        """Return tools advertised by the MCP server."""

        process = self._open_process()
        try:
            self._initialize(process)
            response = self._request(process, "tools/list", {})
            tools = response.get("tools", [])
            if not isinstance(tools, list):
                raise McpClientError("MCP tools/list result missing tools array")
            return [parse_tool(tool) for tool in tools if isinstance(tool, dict)]
        finally:
            close_process(process)

    def call_tool(self, name: str, arguments: JsonObject) -> JsonObject:
        """Call one MCP tool and return its raw structured response."""

        process = self._open_process()
        try:
            self._initialize(process)
            return self._request(
                process,
                "tools/call",
                {"name": name, "arguments": arguments},
            )
        finally:
            close_process(process)

    def _initialize(self, process: subprocess.Popen[str]) -> None:
        self._request(
            process,
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "vanta-pwn-worker", "version": "0.0.0"},
            },
        )
        self._notify(process, "notifications/initialized", {})

    def _open_process(self) -> subprocess.Popen[str]:
        return subprocess.Popen(
            self._command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _request(
        self,
        process: subprocess.Popen[str],
        method: str,
        params: JsonObject,
    ) -> JsonObject:
        self._write_message(
            process,
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        )
        line = self._read_line(process)
        response = json.loads(line)
        if not isinstance(response, dict):
            raise McpClientError("MCP response is not an object")
        error = response.get("error")
        if isinstance(error, dict):
            message = error.get("message", "MCP request failed")
            raise McpClientError(str(message))
        result = response.get("result", {})
        if not isinstance(result, dict):
            raise McpClientError("MCP response result is not an object")
        return result

    def _notify(self, process: subprocess.Popen[str], method: str, params: JsonObject) -> None:
        self._write_message(process, {"jsonrpc": "2.0", "method": method, "params": params})

    def _write_message(self, process: subprocess.Popen[str], message: JsonObject) -> None:
        if process.stdin is None:
            raise McpClientError("MCP stdin is unavailable")
        process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        process.stdin.flush()

    def _read_line(self, process: subprocess.Popen[str]) -> str:
        if process.stdout is None:
            raise McpClientError("MCP stdout is unavailable")
        deadline = time.monotonic() + self._timeout_seconds
        fd = process.stdout.fileno()
        buffer = bytearray()
        while time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.05)
            if not ready:
                if process.poll() is not None:
                    break
                continue
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            buffer.extend(chunk)
            if b"\n" in buffer:
                line, _, _rest = bytes(buffer).partition(b"\n")
                return line.decode(errors="replace")
        stderr = read_stderr(process)
        if stderr:
            raise McpClientError(f"MCP server did not respond: {stderr}")
        raise McpClientError("MCP server did not respond before timeout")


class PersistentStdioMcpClient:
    """Persistent newline-delimited MCP stdio client for stateful servers."""

    def __init__(self, command: Sequence[str], timeout_seconds: float = 10.0) -> None:
        if not command:
            raise McpClientError("MCP command is empty")
        self._command = list(command)
        self._timeout_seconds = timeout_seconds
        self._next_id = 1
        self._read_buffer = bytearray()
        self._process = self._open_process()
        self._initialize()

    @classmethod
    def from_command_line(
        cls,
        command_line: str,
        timeout_seconds: float = 10.0,
    ) -> PersistentStdioMcpClient:
        """Create a persistent client from a shell-like command line."""

        return cls(shlex.split(command_line), timeout_seconds)

    def list_tools(self) -> list[McpTool]:
        """Return tools advertised by the MCP server."""

        response = self.request("tools/list", {})
        tools = response.get("tools", [])
        if not isinstance(tools, list):
            raise McpClientError("MCP tools/list result missing tools array")
        return [parse_tool(tool) for tool in tools if isinstance(tool, dict)]

    def call_tool(self, name: str, arguments: JsonObject) -> JsonObject:
        """Call one MCP tool and return its raw structured response."""

        return self.request("tools/call", {"name": name, "arguments": arguments})

    def close(self) -> None:
        """Close the persistent MCP process."""

        close_process(self._process)

    def request(self, method: str, params: JsonObject) -> JsonObject:
        """Send one JSON-RPC request and return its result."""

        request_id = self._next_id
        self._next_id += 1
        self._write_message(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        return self._read_response(request_id)

    def notify(self, method: str, params: JsonObject) -> None:
        """Send one JSON-RPC notification."""

        self._write_message({"jsonrpc": "2.0", "method": method, "params": params})

    def _initialize(self) -> None:
        self.request(
            "initialize",
            {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "vanta-pwn-worker", "version": "0.0.0"},
            },
        )
        self.notify("notifications/initialized", {})

    def _open_process(self) -> subprocess.Popen[str]:
        return subprocess.Popen(
            self._command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _write_message(self, message: JsonObject) -> None:
        if self._process.stdin is None:
            raise McpClientError("MCP stdin is unavailable")
        self._process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        self._process.stdin.flush()

    def _read_response(self, request_id: int) -> JsonObject:
        deadline = time.monotonic() + self._timeout_seconds
        while time.monotonic() < deadline:
            line = self._read_json_line(0.05)
            if line is None:
                if self._process.poll() is not None:
                    break
                continue
            response = json.loads(line)
            if not isinstance(response, dict) or response.get("id") != request_id:
                continue
            error = response.get("error")
            if isinstance(error, dict):
                message = error.get("message", "MCP request failed")
                raise McpClientError(str(message))
            result = response.get("result", {})
            if not isinstance(result, dict):
                raise McpClientError("MCP response result is not an object")
            return result
        stderr = read_stderr(self._process)
        if stderr:
            raise McpClientError(f"MCP server did not respond: {stderr}")
        raise McpClientError("MCP server did not respond before timeout")

    def _read_json_line(self, wait_seconds: float) -> str | None:
        if self._process.stdout is None:
            raise McpClientError("MCP stdout is unavailable")
        existing = pop_buffered_line(self._read_buffer)
        if existing is not None:
            return existing
        fd = self._process.stdout.fileno()
        ready, _, _ = select.select([fd], [], [], wait_seconds)
        if not ready:
            return None
        chunk = os.read(fd, 4096)
        if not chunk:
            return None
        self._read_buffer.extend(chunk)
        return pop_buffered_line(self._read_buffer)


def parse_tool(value: JsonObject) -> McpTool:
    """Parse a tool descriptor from MCP tools/list output."""

    name = value.get("name")
    description = value.get("description", "")
    if not isinstance(name, str):
        raise McpClientError("MCP tool missing string name")
    if not isinstance(description, str):
        description = ""
    return McpTool(name=name, description=description)


def read_stderr(process: subprocess.Popen[str]) -> str:
    """Read available stderr without blocking indefinitely."""

    if process.stderr is None:
        return ""
    fd = process.stderr.fileno()
    ready, _, _ = select.select([fd], [], [], 0)
    if not ready:
        return ""
    return os.read(fd, 4096).decode(errors="replace").strip()


def pop_buffered_line(buffer: bytearray) -> str | None:
    """Pop one newline-delimited line from a byte buffer."""

    if b"\n" not in buffer:
        return None
    line, _, rest = bytes(buffer).partition(b"\n")
    buffer.clear()
    buffer.extend(rest)
    return line.decode(errors="replace")


def close_process(process: subprocess.Popen[str]) -> None:
    """Terminate a short-lived MCP process after a request."""

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        process.kill()
