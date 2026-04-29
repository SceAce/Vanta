from __future__ import annotations

from typing import Any

from vanta_pwn_worker.gdb_mcp import HybridGdbManager
from vanta_pwn_worker.mcp_client import McpTool

JsonObject = dict[str, Any]


class FakeMcpClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, JsonObject]] = []
        self.closed = False

    def list_tools(self) -> list[McpTool]:
        return [
            McpTool(name="set_file", description="load binary"),
            McpTool(name="execute", description="execute gdb command"),
            McpTool(name="get_context", description="get context"),
        ]

    def call_tool(self, name: str, arguments: JsonObject) -> JsonObject:
        self.calls.append((name, arguments))
        return {"content": [{"type": "text", "text": f"{name} ok"}]}

    def close(self) -> None:
        self.closed = True


class HybridGdbManagerHarness(HybridGdbManager):
    def __init__(self, client: FakeMcpClient) -> None:
        super().__init__(command_line="python -m pwnomcp")
        self.client = client

    def _ensure_client(self) -> Any:
        return self.client


def test_pwno_mcp_status_reports_tools() -> None:
    manager = HybridGdbManagerHarness(FakeMcpClient())

    status = manager.status()

    assert status["available"] is True
    assert status["backend"] == "pwno-mcp"
    assert status["missing_recommended_tools"] == []


def test_pwno_mcp_start_loads_binary_and_command_uses_execute() -> None:
    client = FakeMcpClient()
    manager = HybridGdbManagerHarness(client)

    start = manager.start("/workspace/chall")
    command = manager.command("pwno-mcp", "info registers")

    assert start["started"] is True
    assert start["backend"] == "pwno-mcp"
    assert command["output"] == "execute ok"
    assert client.calls == [
        ("set_file", {"binary_path": "/workspace/chall"}),
        ("execute", {"command": "info registers"}),
    ]


def test_pwno_mcp_snapshot_uses_get_context() -> None:
    client = FakeMcpClient()
    manager = HybridGdbManagerHarness(client)

    snapshot = manager.snapshot("pwno-mcp")

    assert snapshot["context"] == "get_context ok"
    assert client.calls == [("get_context", {"context_type": "all"})]
