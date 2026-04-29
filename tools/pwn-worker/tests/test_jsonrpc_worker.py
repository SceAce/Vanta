from __future__ import annotations

from typing import Any

from vanta_pwn_worker.server import Worker

JsonObject = dict[str, Any]


class FakeIda:
    def status(self) -> JsonObject:
        return {"available": True, "pseudocode_tool": "decompile_function"}

    def decompile_function(self, function: str, binary_path: str | None = None) -> JsonObject:
        return {
            "available": True,
            "function": function,
            "binary_path": binary_path,
            "pseudocode": "int main() { return 0; }",
        }

    def analyze_pseudocode(self, binary_path: str, functions: list[str]) -> JsonObject:
        return {"available": True, "binary_path": binary_path, "functions": functions}


class FakeGdb:
    def status(self) -> JsonObject:
        return {"available": True, "active_sessions": 0}

    def start(self, binary_path: str | None = None, pwndbg: bool = True) -> JsonObject:
        return {"started": True, "session_id": "s1", "binary_path": binary_path, "pwndbg": pwndbg}

    def command(self, session_id: str, command: str) -> JsonObject:
        return {"session_id": session_id, "command": command, "output": "ok"}

    def snapshot(self, session_id: str) -> JsonObject:
        return {"session_id": session_id, "registers": "rax 0x0"}

    def stop(self, session_id: str) -> JsonObject:
        return {"stopped": True, "session_id": session_id}


def test_capabilities_expose_ida_and_gdb_methods() -> None:
    response = make_worker().handle({"jsonrpc": "2.0", "id": 1, "method": "worker.capabilities"})

    assert response is not None
    result = response["result"]
    assert "ida.decompile_function" in result["methods"]
    assert "gdb.mcp_status" in result["methods"]
    assert "gdb.start" in result["methods"]
    assert "pwn.static_scan" in result["methods"]
    assert "pwn.dynamic_verify" in result["methods"]
    assert result["methods"]["gdb.start"]["risk_level"] == "execute local"
    assert result["methods"]["pwn.static_scan"]["risk_level"] == "read-only"


def test_ida_decompile_function_contract() -> None:
    response = make_worker().handle(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "ida.decompile_function",
            "params": {"function": "main", "binary_path": "./chall"},
        }
    )

    assert response is not None
    assert response["result"]["available"] is True
    assert response["result"]["function"] == "main"
    assert "return 0" in response["result"]["pseudocode"]


def test_gdb_start_and_command_contract() -> None:
    server = make_worker()
    start = server.handle({"jsonrpc": "2.0", "id": 3, "method": "gdb.start", "params": {}})
    command = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "gdb.command",
            "params": {"session_id": "s1", "command": "info registers"},
        }
    )

    assert start is not None
    assert command is not None
    assert start["result"]["session_id"] == "s1"
    assert command["result"]["output"] == "ok"


def test_invalid_params_return_jsonrpc_error() -> None:
    response = make_worker().handle(
        {"jsonrpc": "2.0", "id": 5, "method": "ida.decompile_function", "params": {}}
    )

    assert response is not None
    assert response["error"]["code"] == -32602


def test_pwn_static_scan_degrades_when_ida_unavailable() -> None:
    server = Worker(ida=UnavailableTool(), gdb=FakeGdb()).server()
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "pwn.static_scan",
            "params": {"case": {"binary_path": "./chall"}},
        }
    )

    assert response is not None
    result = response["result"]
    assert result["schema_version"] == "vanta.pwn-worker.workflow-result.v1"
    assert result["status"] == "degraded"
    assert result["ida"]["available"] is False


def test_pwn_dynamic_verify_blocks_when_gdb_unavailable() -> None:
    server = Worker(ida=FakeIda(), gdb=UnavailableTool()).server()
    response = server.handle(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "pwn.dynamic_verify",
            "params": {"case": {"binary_path": "./chall"}},
        }
    )

    assert response is not None
    result = response["result"]
    assert result["status"] == "blocked"
    assert result["failure"]["category"] == "tool_unavailable"


def test_pwn_poc_draft_does_not_execute_exploit() -> None:
    response = make_worker().handle(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "pwn.poc_draft",
            "params": {"case": {"binary_path": "./chall"}},
        }
    )

    assert response is not None
    artifact = response["result"]["artifacts"][0]
    assert artifact["type"] == "poc_draft"
    assert artifact["executes_payload"] is False


def test_pwn_pattern_match_returns_candidate_actions() -> None:
    response = make_worker().handle(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "pwn.pattern_match",
            "params": {"findings": ["printf", "system"]},
        }
    )

    assert response is not None
    candidates = response["result"]["artifacts"][0]["candidates"]
    assert {candidate["pattern"] for candidate in candidates} >= {"fmtstr", "ret2win"}


def make_worker() -> Any:
    return Worker(ida=FakeIda(), gdb=FakeGdb()).server()


class UnavailableTool:
    def status(self) -> JsonObject:
        return {"available": False, "reason": "not installed"}
