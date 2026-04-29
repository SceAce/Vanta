"""JSON-RPC entry point for the Vanta Python pwn worker."""

from __future__ import annotations

from typing import Any

from vanta_pwn_worker.gdb_mcp import HybridGdbManager
from vanta_pwn_worker.gdb_worker import GdbWorkerError
from vanta_pwn_worker.ida import IdaMcpAdapter
from vanta_pwn_worker.jsonrpc import JsonObject, JsonRpcError, JsonRpcServer
from vanta_pwn_worker.workflow import PwnWorkflow


class Worker:
    """Dispatches pwn worker JSON-RPC methods."""

    def __init__(self, ida: Any | None = None, gdb: Any | None = None) -> None:
        self._ida = ida or IdaMcpAdapter()
        self._gdb = gdb or HybridGdbManager()
        self._workflow = PwnWorkflow(self._ida, self._gdb)

    def server(self) -> JsonRpcServer:
        """Build a JSON-RPC server for this worker."""

        return JsonRpcServer(
            {
                "worker.capabilities": self.capabilities,
                "ida.status": self.ida_status,
                "ida.decompile_function": self.ida_decompile_function,
                "ida.analyze_pseudocode": self.ida_analyze_pseudocode,
                "gdb.status": self.gdb_status,
                "gdb.mcp_status": self.gdb_status,
                "gdb.start": self.gdb_start,
                "gdb.command": self.gdb_command,
                "gdb.snapshot": self.gdb_snapshot,
                "gdb.stop": self.gdb_stop,
                "pwn.static_scan": self.pwn_static_scan,
                "pwn.breakpoint_plan": self.pwn_breakpoint_plan,
                "pwn.dynamic_verify": self.pwn_dynamic_verify,
                "pwn.poc_draft": self.pwn_poc_draft,
                "pwn.pattern_match": self.pwn_pattern_match,
            }
        )

    def capabilities(self, _params: JsonObject) -> JsonObject:
        """Return worker capabilities and risk levels."""

        return {
            "schema_version": "vanta.pwn-worker.capabilities.v1",
            "methods": {
                "ida.status": {"risk_level": "read-only"},
                "ida.decompile_function": {"risk_level": "read-only"},
                "ida.analyze_pseudocode": {"risk_level": "read-only"},
                "gdb.status": {"risk_level": "read-only"},
                "gdb.mcp_status": {"risk_level": "read-only"},
                "gdb.start": {"risk_level": "execute local"},
                "gdb.command": {"risk_level": "execute local"},
                "gdb.snapshot": {"risk_level": "read-only"},
                "gdb.stop": {"risk_level": "read-only"},
                "pwn.static_scan": {"risk_level": "read-only"},
                "pwn.breakpoint_plan": {"risk_level": "read-only"},
                "pwn.dynamic_verify": {"risk_level": "execute local"},
                "pwn.poc_draft": {"risk_level": "write workspace"},
                "pwn.pattern_match": {"risk_level": "read-only"},
            },
            "analysis": [
                "ida-mcp-pseudocode",
                "pwno-mcp-gdb",
                "gdb-long-lived-session",
                "pwndbg-compatible",
                "pwn-case-workflow",
            ],
        }

    def ida_status(self, _params: JsonObject) -> JsonObject:
        """Return IDA MCP connection status."""

        return self._ida.status()

    def ida_decompile_function(self, params: JsonObject) -> JsonObject:
        """Return pseudocode for one function."""

        function = require_str(params, "function")
        binary_path = optional_str(params, "binary_path")
        return self._ida.decompile_function(function, binary_path)

    def ida_analyze_pseudocode(self, params: JsonObject) -> JsonObject:
        """Return pseudocode snippets for selected functions."""

        binary_path = require_str(params, "binary_path")
        functions = require_str_list(params, "functions")
        return self._ida.analyze_pseudocode(binary_path, functions)

    def gdb_status(self, _params: JsonObject) -> JsonObject:
        """Return GDB worker status."""

        return self._gdb.status()

    def gdb_start(self, params: JsonObject) -> JsonObject:
        """Start a GDB session."""

        return self._gdb.start(
            optional_str(params, "binary_path"),
            optional_bool(params, "pwndbg", True),
        )

    def gdb_command(self, params: JsonObject) -> JsonObject:
        """Run a command in an existing GDB session."""

        try:
            return self._gdb.command(
                require_str(params, "session_id"),
                require_str(params, "command"),
            )
        except GdbWorkerError as error:
            raise JsonRpcError(-32000, str(error)) from error

    def gdb_snapshot(self, params: JsonObject) -> JsonObject:
        """Collect debug-state summaries from GDB."""

        try:
            return self._gdb.snapshot(require_str(params, "session_id"))
        except GdbWorkerError as error:
            raise JsonRpcError(-32000, str(error)) from error

    def gdb_stop(self, params: JsonObject) -> JsonObject:
        """Stop a GDB session."""

        return self._gdb.stop(require_str(params, "session_id"))

    def pwn_static_scan(self, params: JsonObject) -> JsonObject:
        """Run high-level static scan contract."""

        return self._workflow.static_scan(params)

    def pwn_breakpoint_plan(self, params: JsonObject) -> JsonObject:
        """Run high-level breakpoint plan contract."""

        return self._workflow.breakpoint_plan(params)

    def pwn_dynamic_verify(self, params: JsonObject) -> JsonObject:
        """Run high-level dynamic verification contract."""

        return self._workflow.dynamic_verify(params)

    def pwn_poc_draft(self, params: JsonObject) -> JsonObject:
        """Run high-level PoC draft contract."""

        return self._workflow.poc_draft(params)

    def pwn_pattern_match(self, params: JsonObject) -> JsonObject:
        """Run high-level pattern matching contract."""

        return self._workflow.pattern_match(params)


def require_str(params: JsonObject, key: str) -> str:
    """Read a required string parameter."""

    value = params.get(key)
    if not isinstance(value, str) or not value:
        raise JsonRpcError(-32602, f"params.{key} must be a non-empty string")
    return value


def optional_str(params: JsonObject, key: str) -> str | None:
    """Read an optional string parameter."""

    value = params.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise JsonRpcError(-32602, f"params.{key} must be a string")
    return value


def optional_bool(params: JsonObject, key: str, default: bool) -> bool:
    """Read an optional boolean parameter."""

    value: Any = params.get(key, default)
    if not isinstance(value, bool):
        raise JsonRpcError(-32602, f"params.{key} must be a boolean")
    return value


def require_str_list(params: JsonObject, key: str) -> list[str]:
    """Read a required list of strings."""

    value = params.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise JsonRpcError(-32602, f"params.{key} must be a string array")
    return value


def main() -> None:
    """Run the worker JSON-RPC server on stdio."""

    Worker().server().serve()


if __name__ == "__main__":
    main()
