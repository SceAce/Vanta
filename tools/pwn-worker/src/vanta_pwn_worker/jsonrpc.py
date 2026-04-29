"""Small JSON-RPC 2.0 helpers used by the pwn worker."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, TextIO

JsonObject = dict[str, Any]
Handler = Callable[[JsonObject], JsonObject]


@dataclass(frozen=True)
class JsonRpcError(Exception):
    """JSON-RPC error with a stable code and message."""

    code: int
    message: str


class JsonRpcServer:
    """Line-delimited JSON-RPC 2.0 server over stdio-like streams."""

    def __init__(self, handlers: Mapping[str, Handler]) -> None:
        self._handlers = dict(handlers)

    def handle(self, request: JsonObject) -> JsonObject | None:
        """Handle one JSON-RPC request or notification."""

        request_id = request.get("id")
        try:
            method = self._read_method(request)
            params = self._read_params(request)
            result = self._dispatch(method, params)
            if request_id is None:
                return None
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except JsonRpcError as error:
            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": error.code, "message": error.message},
            }

    def serve(self, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
        """Serve JSON-RPC requests until stdin closes."""

        for line in stdin:
            if not line.strip():
                continue
            response = self.handle(parse_json_line(line))
            if response is not None:
                stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                stdout.flush()

    def _dispatch(self, method: str, params: JsonObject) -> JsonObject:
        handler = self._handlers.get(method)
        if handler is None:
            raise JsonRpcError(-32601, f"unknown method: {method}")
        return handler(params)

    @staticmethod
    def _read_method(request: JsonObject) -> str:
        method = request.get("method")
        if not isinstance(method, str) or not method:
            raise JsonRpcError(-32600, "request.method must be a non-empty string")
        return method

    @staticmethod
    def _read_params(request: JsonObject) -> JsonObject:
        params = request.get("params", {})
        if not isinstance(params, dict):
            raise JsonRpcError(-32602, "request.params must be an object")
        return params


def parse_json_line(line: str) -> JsonObject:
    """Parse one JSON object from a line."""

    try:
        value = json.loads(line)
    except json.JSONDecodeError as error:
        raise JsonRpcError(-32700, f"invalid json: {error.msg}") from error
    if not isinstance(value, dict):
        raise JsonRpcError(-32600, "request must be a JSON object")
    return value
