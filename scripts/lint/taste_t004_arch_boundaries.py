#!/usr/bin/env python3
"""T-004 Taste Invariant Linter — enforce architectural crate boundaries.

Reads `.config/arch-boundaries.toml` for the allow/forbid list, then walks
every `Cargo.toml` under `crates/` and `apps/` to verify that intra-workspace
dependencies conform to the declared boundary policy.

Exit codes:
  0  no violations
  1  one or more boundary violations found
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef,import-not-found]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

_REPO_ROOT = Path(os.environ.get("REPO_ROOT_OVERRIDE") or Path(__file__).resolve().parents[2])
_BOUNDARIES_FILE = _REPO_ROOT / ".config" / "arch-boundaries.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    if tomllib is not None:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    return _parse_toml_minimal(path.read_text(encoding="utf-8"))


def _parse_toml_minimal(text: str) -> dict[str, Any]:
    """Very small TOML subset parser: [[crate]] blocks with string arrays."""
    result: dict[str, Any] = {}
    crates: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if line == "[[crate]]":
            current = {}
            crates.append(current)
            continue
        if current is None:
            continue
        m = re.match(r"^(\w+)\s*=\s*\[([^\]]*)\]", line)
        if m:
            key, val = m.group(1), m.group(2)
            items = [s.strip().strip('"') for s in val.split(",") if s.strip().strip('"')]
            current[key] = items
            continue
        m = re.match(r'^(\w+)\s*=\s*"([^"]*)"', line)
        if m:
            current[m.group(1)] = m.group(2)
    result["crate"] = crates
    return result


def _parse_cargo_workspace_deps(cargo_text: str) -> set[str]:
    """Return the set of intra-workspace dep names from a Cargo.toml."""
    return {
        m.group(1)
        for m in re.finditer(r"^([a-zA-Z0-9_-]+)\s*=\s*\{[^}]*path\s*=", cargo_text, re.MULTILINE)
    }


def main() -> int:
    if not _BOUNDARIES_FILE.exists():
        print(
            f"[T-004] .config/arch-boundaries.toml not found at {_BOUNDARIES_FILE}. "
            "Create it to define crate boundary policy.",
            file=sys.stderr,
        )
        return 1

    policy = _load_toml(_BOUNDARIES_FILE)
    crate_rules: dict[str, dict[str, list[str]]] = {}
    for entry in policy.get("crate", []):
        name = entry.get("name", "")
        crate_rules[name] = {
            "allowed": entry.get("allowed_deps", []),
            "forbidden": entry.get("forbidden_deps", []),
        }

    violations: list[str] = []

    search_roots = [_REPO_ROOT / "crates", _REPO_ROOT / "apps"]
    for root in search_roots:
        if not root.exists():
            continue
        for cargo_toml in sorted(root.rglob("Cargo.toml")):
            crate_name = cargo_toml.parent.name
            cargo_text = cargo_toml.read_text(encoding="utf-8")
            actual_ws_deps = _parse_cargo_workspace_deps(cargo_text)

            rules = crate_rules.get(crate_name)
            if rules is None:
                continue

            allowed = set(rules["allowed"])
            forbidden = set(rules["forbidden"])
            rel = cargo_toml.relative_to(_REPO_ROOT)

            for dep in sorted(actual_ws_deps):
                if dep in forbidden:
                    violations.append(
                        f"{rel}: '{crate_name}' must not depend on '{dep}' "
                        "(forbidden by arch-boundaries.toml). "
                        "Remove this dependency to maintain layer separation (T-004)."
                    )
                elif allowed and dep not in allowed:
                    violations.append(
                        f"{rel}: '{crate_name}' depends on '{dep}' which is not in its "
                        "allowed_deps list in arch-boundaries.toml. "
                        "Add it to allowed_deps or remove the dependency (T-004)."
                    )

    if violations:
        for v in violations:
            print(f"[T-004] {v}", flush=True)
        print(
            f"\nT-004 FAILED: {len(violations)} architectural boundary violation(s). "
            "Fix crate dependency graph to match .config/arch-boundaries.toml.",
            flush=True,
        )
        return 1

    crate_count = sum(1 for root in search_roots if root.exists() for _ in root.rglob("Cargo.toml"))
    print(
        f"T-004 passed: {crate_count} Cargo.toml(s) conform to arch-boundaries.toml.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
