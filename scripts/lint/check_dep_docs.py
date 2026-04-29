#!/usr/bin/env python3
"""Check that every external Cargo dependency has a docs/references/<lib>-llms.txt file.

Scans all Cargo.toml files in workspace members, collects external dependency
names, filters out workspace members and an exempt list of well-known crates,
then verifies that each remaining dependency has a corresponding reference doc.

Exit code 0 if all deps are documented, 1 otherwise.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Workspace member crate names -- these are internal, not external deps.
_WORKSPACE_MEMBERS: frozenset[str] = frozenset(
    {
        "vanta-cli",
        "vanta-core",
    }
)

# Well-known crates exempt from requiring a reference doc.
# This list is intentionally large during the bootstrap phase.
_EXEMPT = frozenset(
    {
        # Serialization
        "serde",
        "serde_json",
        "toml",
        # Error handling
        "thiserror",
        "anyhow",
        # Identifiers & time
        "uuid",
        "time",
        # Async runtime
        "tokio",
        "tokio-stream",
        # Web framework
        "axum",
        "tower",
        "tower-http",
        # HTTP client
        "reqwest",
        "reqwest-eventsource",
        # Observability
        "tracing",
        "tracing-subscriber",
        # CLI
        "clap",
        # Embedding
        "rust-embed",
        # Dev / test only
        "criterion",
        "proptest",
        "insta",
        "wiremock",
        "tempfile",
        "assert_cmd",
        "predicates",
        "tokio-test",
        "pretty_assertions",
        "test-log",
        "tracing-test",
    }
)

_DEP_SECTION_RE = re.compile(
    r"^\[((?:workspace\.)?(?:dependencies|dev-dependencies|build-dependencies)(?:\.\S+)?)\]",
)
_DEP_LINE_RE = re.compile(r"^(\S+)\s*=")

REFERENCES_DIR = REPO_ROOT / "docs" / "references"


def _collect_cargo_tomls() -> list[Path]:
    """Return all Cargo.toml files in the repo."""
    paths = [REPO_ROOT / "Cargo.toml"]
    for member_dir in (REPO_ROOT / "crates").iterdir():
        cargo = member_dir / "Cargo.toml"
        if cargo.is_file():
            paths.append(cargo)
    for member_dir in (REPO_ROOT / "apps").iterdir():
        cargo = member_dir / "Cargo.toml"
        if cargo.is_file():
            paths.append(cargo)
    return paths


def _parse_deps(cargo_path: Path) -> set[str]:
    """Extract dependency names from a Cargo.toml file."""
    deps: set[str] = set()
    in_dep_section = False

    for line in cargo_path.read_text().splitlines():
        stripped = line.strip()

        # Check for section headers
        if stripped.startswith("["):
            in_dep_section = bool(_DEP_SECTION_RE.match(stripped))
            continue

        if in_dep_section:
            m = _DEP_LINE_RE.match(stripped)
            if m:
                deps.add(m.group(1).split(".")[0])

    return deps


def main() -> int:
    all_deps: set[str] = set()
    for cargo_path in _collect_cargo_tomls():
        all_deps |= _parse_deps(cargo_path)

    # Filter out workspace members and exempt crates
    external = all_deps - _WORKSPACE_MEMBERS - _EXEMPT

    missing: list[str] = []
    for dep in sorted(external):
        ref_file = REFERENCES_DIR / f"{dep}-llms.txt"
        if not ref_file.is_file():
            missing.append(dep)

    if missing:
        print(f"ERROR: {len(missing)} external dependency(ies) missing reference docs:")
        for dep in missing:
            expected = f"docs/references/{dep}-llms.txt"
            print(f"  - {dep}  (expected: {expected})")
        print()
        print(
            "Add the dep to _EXEMPT in scripts/lint/check_dep_docs.py "
            "if it is a well-known crate that does not need a reference doc, "
            "or create the reference file."
        )
        return 1

    print(f"OK: all {len(all_deps)} dependencies accounted for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
