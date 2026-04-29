"""IDA MCP adapter for pseudocode-oriented binary analysis."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from vanta_pwn_worker.mcp_client import McpClientError, McpTool, StdioMcpClient

JsonObject = dict[str, Any]

IDA_COMMAND_ENV = "VANTA_IDA_MCP_COMMAND"
PSEUDOCODE_TOOL_CANDIDATES = (
    "decompile_function",
    "get_pseudocode",
    "decompile",
    "ida_decompile_function",
)
FUNCTION_LIST_TOOL_CANDIDATES = ("list_functions", "get_functions", "ida_list_functions")


@dataclass(frozen=True)
class IdaToolSelection:
    """Selected IDA MCP tools relevant to Vanta analysis."""

    pseudocode_tool: str | None
    function_list_tool: str | None
    tools: list[McpTool]


class IdaMcpAdapter:
    """Connects Vanta worker methods to an IDA MCP stdio server."""

    def __init__(self, command_line: str | None = None, timeout_seconds: float = 10.0) -> None:
        self._command_line = command_line or os.environ.get(IDA_COMMAND_ENV)
        self._timeout_seconds = timeout_seconds

    def status(self) -> JsonObject:
        """Return IDA MCP availability and advertised analysis tools."""

        if not self._command_line:
            return {"available": False, "reason": f"{IDA_COMMAND_ENV} is not set", "tools": []}
        try:
            selection = self._select_tools()
        except (McpClientError, OSError) as error:
            return {"available": False, "reason": str(error), "tools": []}
        return {
            "available": selection.pseudocode_tool is not None,
            "reason": "ready" if selection.pseudocode_tool else "no pseudocode tool found",
            "pseudocode_tool": selection.pseudocode_tool,
            "function_list_tool": selection.function_list_tool,
            "tools": [tool.name for tool in selection.tools],
        }

    def decompile_function(self, function: str, binary_path: str | None = None) -> JsonObject:
        """Fetch pseudocode for one function through IDA MCP."""

        if not function:
            return {"available": False, "reason": "function is required", "pseudocode": None}
        try:
            selection = self._select_tools()
            if selection.pseudocode_tool is None:
                return {
                    "available": False,
                    "reason": "no pseudocode tool found",
                    "pseudocode": None,
                }
            arguments: JsonObject = {"function": function}
            if binary_path is not None:
                arguments["binary_path"] = binary_path
            response = self._client().call_tool(selection.pseudocode_tool, arguments)
        except (McpClientError, OSError) as error:
            return {"available": False, "reason": str(error), "pseudocode": None}
        return {
            "available": True,
            "source": "ida-mcp",
            "tool": selection.pseudocode_tool,
            "function": function,
            "pseudocode": extract_text(response),
            "raw": response,
        }

    def analyze_pseudocode(self, binary_path: str, functions: list[str]) -> JsonObject:
        """Collect pseudocode snippets for selected functions."""

        selected = functions[:10]
        results = [self.decompile_function(function, binary_path) for function in selected]
        available = any(bool(result.get("available")) for result in results)
        return {
            "available": available,
            "source": "ida-mcp" if available else "ida-mcp-unavailable",
            "binary_path": binary_path,
            "functions": results,
        }

    def _select_tools(self) -> IdaToolSelection:
        tools = self._client().list_tools()
        names = {tool.name for tool in tools}
        return IdaToolSelection(
            pseudocode_tool=first_present(PSEUDOCODE_TOOL_CANDIDATES, names),
            function_list_tool=first_present(FUNCTION_LIST_TOOL_CANDIDATES, names),
            tools=tools,
        )

    def _client(self) -> StdioMcpClient:
        if not self._command_line:
            raise McpClientError(f"{IDA_COMMAND_ENV} is not set")
        return StdioMcpClient.from_command_line(self._command_line, self._timeout_seconds)


def first_present(candidates: tuple[str, ...], names: set[str]) -> str | None:
    """Return the first candidate that appears in a tool name set."""

    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def extract_text(response: JsonObject) -> str:
    """Extract human-readable text from a common MCP tool response shape."""

    content = response.get("content")
    if isinstance(content, list):
        texts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                texts.append(item["text"])
        if texts:
            return "\n".join(texts)
    for key in ("pseudocode", "text", "result"):
        value = response.get(key)
        if isinstance(value, str):
            return value
    return ""
