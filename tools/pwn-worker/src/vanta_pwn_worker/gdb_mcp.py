"""pwno-mcp adapter with fallback to the local GDB worker."""

from __future__ import annotations

import os
from typing import Any

from vanta_pwn_worker.gdb_worker import GdbManager
from vanta_pwn_worker.mcp_client import McpClientError, PersistentStdioMcpClient

JsonObject = dict[str, Any]

GDB_MCP_COMMAND_ENV = "VANTA_GDB_MCP_COMMAND"
PWNO_REQUIRED_TOOLS = {"execute", "get_context", "set_file"}


class HybridGdbManager:
    """Uses pwno-mcp when configured, otherwise falls back to local GDB."""

    def __init__(
        self,
        command_line: str | None = None,
        fallback: GdbManager | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._command_line = command_line or os.environ.get(GDB_MCP_COMMAND_ENV)
        self._fallback = fallback or GdbManager()
        self._timeout_seconds = timeout_seconds
        self._client: PersistentStdioMcpClient | None = None

    def status(self) -> JsonObject:
        """Return pwno-mcp status or local GDB fallback status."""

        if not self._command_line:
            status = self._fallback.status()
            status["backend"] = "local-gdb"
            status["mcp_configured"] = False
            return status
        try:
            client = self._ensure_client()
            tools = {tool.name for tool in client.list_tools()}
        except (McpClientError, OSError) as error:
            return {
                "available": False,
                "backend": "pwno-mcp",
                "mcp_configured": True,
                "reason": str(error),
            }
        return {
            "available": bool(PWNO_REQUIRED_TOOLS & tools),
            "backend": "pwno-mcp",
            "mcp_configured": True,
            "tools": sorted(tools),
            "missing_recommended_tools": sorted(PWNO_REQUIRED_TOOLS - tools),
        }

    def start(self, binary_path: str | None = None, pwndbg: bool = True) -> JsonObject:
        """Start or attach to a pwno-mcp debugging state."""

        if not self._command_line:
            return self._fallback.start(binary_path, pwndbg)
        try:
            result: JsonObject = {}
            if binary_path:
                result = self._call_tool("set_file", {"binary_path": binary_path})
        except (McpClientError, OSError) as error:
            return {"started": False, "backend": "pwno-mcp", "reason": str(error)}
        return {
            "started": True,
            "backend": "pwno-mcp",
            "session_id": "pwno-mcp",
            "binary_path": binary_path,
            "pwndbg_requested": pwndbg,
            "set_file": summarize_mcp_result(result),
        }

    def command(self, session_id: str, command: str) -> JsonObject:
        """Run a GDB/pwndbg command through pwno-mcp or local GDB."""

        if not self._command_line:
            return self._fallback.command(session_id, command)
        result = self._call_tool("execute", {"command": command})
        return {
            "session_id": session_id,
            "backend": "pwno-mcp",
            "command": command,
            "output": summarize_mcp_result(result),
            "raw": result,
        }

    def snapshot(self, session_id: str) -> JsonObject:
        """Collect debug context through pwno-mcp or local GDB."""

        if not self._command_line:
            return self._fallback.snapshot(session_id)
        result = self._call_tool("get_context", {"context_type": "all"})
        return {
            "session_id": session_id,
            "backend": "pwno-mcp",
            "context": summarize_mcp_result(result),
            "raw": result,
        }

    def stop(self, session_id: str) -> JsonObject:
        """Close the pwno-mcp client or local GDB session."""

        if not self._command_line:
            return self._fallback.stop(session_id)
        if self._client is not None:
            self._client.close()
            self._client = None
        return {"stopped": True, "backend": "pwno-mcp", "session_id": session_id}

    def _call_tool(self, name: str, arguments: JsonObject) -> JsonObject:
        return self._ensure_client().call_tool(name, arguments)

    def _ensure_client(self) -> PersistentStdioMcpClient:
        if self._client is None:
            if not self._command_line:
                raise McpClientError(f"{GDB_MCP_COMMAND_ENV} is not set")
            self._client = PersistentStdioMcpClient.from_command_line(
                self._command_line,
                self._timeout_seconds,
            )
        return self._client


def summarize_mcp_result(result: JsonObject) -> str:
    """Extract compact text from common MCP tool result shapes."""

    content = result.get("content")
    if isinstance(content, list):
        texts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                texts.append(item["text"])
        if texts:
            return "\n".join(texts)
    for key in ("output", "text", "result", "context"):
        value = result.get(key)
        if isinstance(value, str):
            return value
    return str(result)
