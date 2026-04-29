"""High-level pwn workflow methods for case orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

JsonObject = dict[str, Any]

WORKFLOW_SCHEMA_VERSION = "vanta.pwn-worker.workflow-result.v1"


class PwnWorkflow:
    """Implements evidence-friendly pwn workflow method contracts."""

    def __init__(self, ida: Any, gdb: Any) -> None:
        self._ida = ida
        self._gdb = gdb

    def static_scan(self, params: JsonObject) -> JsonObject:
        """Return static scan findings with IDA fallback metadata."""

        binary_path = case_binary_path(params)
        ida_status = self._safe_status(self._ida)
        status = "degraded" if not ida_status.get("available", False) else "ok"
        summary = "static scan completed with IDA MCP" if status == "ok" else "IDA unavailable"
        pseudocode = self._pseudocode_scan(binary_path, ida_status)
        return workflow_result(
            status=status,
            summary=summary,
            artifacts=[
                {
                    "type": "static_scan",
                    "binary_path": binary_path,
                    "pseudocode": pseudocode,
                }
            ],
            evidence_candidates=[{"kind": "binary_path", "value": binary_path}],
            extra={
                "ida": {
                    "available": bool(ida_status.get("available", False)),
                    "reason": ida_status.get("reason"),
                },
                "findings": static_findings(binary_path),
            },
        )

    def breakpoint_plan(self, params: JsonObject) -> JsonObject:
        """Return a conservative breakpoint plan without starting GDB."""

        binary_path = case_binary_path(params)
        return workflow_result(
            status="ok",
            summary="breakpoint plan drafted",
            artifacts=[
                {
                    "type": "breakpoint_plan",
                    "binary_path": binary_path,
                    "breakpoints": ["main", "read", "gets", "system"],
                }
            ],
            evidence_candidates=[],
            extra={"requires_gdb": True},
        )

    def dynamic_verify(self, params: JsonObject) -> JsonObject:
        """Return dynamic verification readiness or a structured blocker."""

        gdb_status = self._safe_status(self._gdb)
        if not gdb_status.get("available", False):
            return workflow_result(
                status="blocked",
                summary="GDB backend unavailable",
                artifacts=[],
                evidence_candidates=[],
                failure=failure(
                    "tool_unavailable",
                    "GDB backend is unavailable for dynamic verification",
                    "worker:gdb.status",
                    "Install GDB or configure VANTA_GDB_MCP_COMMAND, then rerun dynamic verify.",
                ),
                extra={"gdb": gdb_status},
            )
        return workflow_result(
            status="ready",
            summary="GDB backend is available; runtime permission is required before execution",
            artifacts=[{"type": "dynamic_verify_plan", "case": compact_case(params)}],
            evidence_candidates=[{"kind": "gdb_status", "value": gdb_status}],
            extra={"gdb": gdb_status},
        )

    def poc_draft(self, params: JsonObject) -> JsonObject:
        """Return a PoC draft artifact shape without executing an exploit."""

        binary_path = case_binary_path(params)
        return workflow_result(
            status="drafted",
            summary="PoC draft generated without exploit execution",
            artifacts=[
                {
                    "type": "poc_draft",
                    "binary_path": binary_path,
                    "language": "python",
                    "executes_payload": False,
                }
            ],
            evidence_candidates=[],
        )

    def pattern_match(self, params: JsonObject) -> JsonObject:
        """Suggest exploit patterns from current static and dynamic hints."""

        text = str(params).lower()
        candidates = pattern_candidates(text)
        return workflow_result(
            status="ok",
            summary="pattern candidates generated",
            artifacts=[{"type": "pattern_match", "candidates": candidates}],
            evidence_candidates=[],
        )

    def _safe_status(self, tool: Any) -> JsonObject:
        try:
            status = tool.status()
        except (OSError, RuntimeError) as error:
            return {"available": False, "reason": str(error)}
        if isinstance(status, dict):
            return status
        return {"available": False, "reason": "tool returned non-object status"}

    def _pseudocode_scan(self, binary_path: str | None, ida_status: JsonObject) -> JsonObject:
        if not binary_path or not ida_status.get("available", False):
            return {"available": False, "functions": []}
        analyzer = getattr(self._ida, "analyze_pseudocode", None)
        if not callable(analyzer):
            return {"available": False, "functions": []}
        result = analyzer(binary_path, ["main", "win", "vuln", "read_flag"])
        return result if isinstance(result, dict) else {"available": False, "functions": []}


def workflow_result(
    *,
    status: str,
    summary: str,
    artifacts: list[JsonObject],
    evidence_candidates: list[JsonObject],
    failure: JsonObject | None = None,
    extra: JsonObject | None = None,
) -> JsonObject:
    """Build the common workflow result shape."""

    result: JsonObject = {
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "status": status,
        "summary": summary,
        "artifacts": artifacts,
        "evidence_candidates": evidence_candidates,
        "failure": failure,
    }
    if extra:
        result.update(extra)
    return result


def failure(
    category: str,
    message: str,
    evidence_ref: str,
    suggested_next_action: str,
) -> JsonObject:
    """Build the common workflow failure shape."""

    return {
        "category": category,
        "message": message,
        "evidence_ref": evidence_ref,
        "suggested_next_action": suggested_next_action,
    }


def compact_case(params: JsonObject) -> JsonObject:
    """Return a scrubbed compact case shape for artifact summaries."""

    case = params.get("case")
    source: Mapping[str, Any] = case if isinstance(case, dict) else params
    return {
        "binary_path": source.get("binary_path"),
        "aslr": source.get("aslr", "preserve"),
        "timeout_seconds": source.get("timeout_seconds", 10),
        "retry_limit": source.get("retry_limit", 1),
        "seed": source.get("seed", 0),
        "mode": source.get("mode", "ctf"),
        "has_remote": isinstance(source.get("remote"), dict),
    }


def case_binary_path(params: JsonObject) -> str | None:
    """Read binary_path from params or nested case object."""

    case = params.get("case")
    if isinstance(case, dict) and isinstance(case.get("binary_path"), str):
        return str(case["binary_path"])
    value = params.get("binary_path")
    return value if isinstance(value, str) else None


def static_findings(binary_path: str | None) -> list[JsonObject]:
    """Return MVP static findings without executing external tools."""

    findings: list[JsonObject] = []
    if binary_path:
        findings.append({"kind": "target", "value": binary_path})
    findings.append({"kind": "next_action", "value": "run pwn.breakpoint_plan"})
    return findings


def pattern_candidates(text: str) -> list[JsonObject]:
    """Return heuristic pattern candidates for first-pass ranking."""

    candidates: list[JsonObject] = []
    if "win" in text or "system" in text:
        candidates.append(candidate("ret2win", 0.55, "confirm win/system control-flow path"))
    if "printf" in text or "format" in text:
        candidates.append(candidate("fmtstr", 0.5, "verify controlled format string argument"))
    if "malloc" in text or "free" in text or "tcache" in text:
        candidates.append(candidate("tcache_poisoning", 0.45, "collect heap allocation trace"))
    if "libc" in text or "puts" in text:
        candidates.append(candidate("ret2libc", 0.45, "leak libc address and resolve base"))
    return candidates or [candidate("ret2win", 0.2, "look for simple win function first")]


def candidate(name: str, confidence: float, next_action: str) -> JsonObject:
    """Build a pattern candidate."""

    return {"pattern": name, "confidence": confidence, "next_action": next_action}
