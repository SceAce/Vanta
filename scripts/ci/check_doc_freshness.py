#!/usr/bin/env python3
"""CI freshness invariant checker.

Usage:
    uv run python scripts/ci/check_doc_freshness.py <base-sha> <head-sha>
    uv run python scripts/ci/check_doc_freshness.py --local
    uv run python scripts/ci/check_doc_freshness.py --staged

Hard invariants (exit 1 on violation):
  1. Source code changed → state/progress.json also changed
  2. state/progress.json changed → CHANGELOG.md also changed (PR only)
  3. specs/** changed → state/completion-ledger.json also changed
  4. crates/apps/tools changed → docs/modules/<category>/<name>.md must exist and be updated
  13. ADR structure: docs/architecture/decisions/adr-*.md must have required sections

Soft invariants (warning only):
  6. Event/NATS code changed → schemas/json/events/ should change
  7. state/policy.json changed → AGENTS.md/CLAUDE.md/CODEX.md should change
  15. Crate internal README check

Exit codes:
  0  all hard invariants satisfied
  1  one or more hard violations
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_SOURCE_SUFFIXES = {".rs", ".py", ".ts", ".tsx", ".js", ".jsx"}
_SOURCE_PREFIXES = ("src/", "crates/", "tools/", "scripts/", "tests/")
_SPEC_PREFIXES = ("specs/",)
_EVENT_PATTERNS = re.compile(r"(event|nats|publish|subscribe|message)")


def _is_source(path: str) -> bool:
    p = Path(path)
    if p.suffix in _SOURCE_SUFFIXES:
        return True
    return any(path.startswith(prefix) for prefix in _SOURCE_PREFIXES)


def _is_spec(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _SPEC_PREFIXES)


def _crate_name(path: str) -> tuple[str, str] | None:
    for prefix in ("crates/", "apps/", "tools/"):
        if path.startswith(prefix):
            rest = path[len(prefix) :]
            name = rest.split("/")[0]
            category = prefix.rstrip("/")
            return (category, name) if name else None
    return None


_IN_GHA = os.environ.get("GITHUB_ACTIONS") == "true"


def _error(message: str) -> None:
    if _IN_GHA:
        print(f"::error::{message}", flush=True)
    print(f"ERROR: {message}", file=sys.stderr, flush=True)


def _warning(message: str) -> None:
    if _IN_GHA:
        print(f"::warning::{message}", flush=True)
    print(f"WARNING: {message}", file=sys.stderr, flush=True)


def _changed_files(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        capture_output=True,
        text=True,
        check=True,
    )
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def _local_changed_files() -> list[str]:
    seen: set[str] = set()
    files: list[str] = []

    def _add(lines: str) -> None:
        for line in lines.splitlines():
            p = line.strip()
            if p and p not in seen:
                seen.add(p)
                files.append(p)

    branch = (
        subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        or "dev"
    )
    merge_base = subprocess.run(
        ["git", "merge-base", f"origin/{branch}", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if merge_base:
        r = subprocess.run(
            ["git", "diff", "--name-only", merge_base, "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        _add(r.stdout)
    else:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD^", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        _add(r.stdout)

    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    _add(r.stdout)

    r = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    _add(r.stdout)

    r = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=False,
    )
    _add(r.stdout)

    return files


def _repo_root() -> Path:
    return Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )


def _run_checks(files: list[str]) -> int:
    file_set = set(files)
    repo_root = _repo_root()

    violations: list[str] = []
    warnings: list[str] = []

    # Hard 1: source changed → state/progress.json changed
    source_changed = any(_is_source(f) for f in files)
    if source_changed and "state/progress.json" not in file_set:
        violations.append(
            "Source files changed but state/progress.json was not updated. "
            "Record progress before merging."
        )

    # Hard 2: progress.json changed → CHANGELOG.md changed (PR only)
    _is_pr = os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
    if _is_pr and "state/progress.json" in file_set and "CHANGELOG.md" not in file_set:
        violations.append(
            "state/progress.json changed but CHANGELOG.md was not recompiled. "
            "Run 'git-cliff --output CHANGELOG.md' before merging."
        )

    # Hard 3: specs/** changed → state/completion-ledger.json changed
    spec_changed = any(_is_spec(f) for f in files)
    if spec_changed and "state/completion-ledger.json" not in file_set:
        violations.append(
            "specs/ changed but state/completion-ledger.json was not updated. "
            "Reflect spec changes in the completion ledger before merging."
        )

    # Hard 4: crates/apps/tools changed → docs/modules/<category>/<name>.md
    changed_crates: set[tuple[str, str]] = set()
    for f in files:
        result = _crate_name(f)
        if result:
            changed_crates.add(result)

    for category, name in sorted(changed_crates):
        crate_dir = repo_root / category / name
        if not crate_dir.exists():
            continue
        doc_path = repo_root / "docs" / "modules" / category / f"{name}.md"
        doc_rel = f"docs/modules/{category}/{name}.md"
        if not doc_path.exists():
            violations.append(
                f"{name} source changed but {doc_rel} does not exist. "
                f"Create {doc_rel} documenting public API and architecture."
            )
        elif doc_rel not in file_set:
            violations.append(
                f"{name} source changed but {doc_rel} was not updated. Sync docs before merging."
            )

    # Soft 6: event code changed → schemas should change
    event_code_files = [
        f
        for f in files
        if f.startswith(("crates/", "src/")) and _EVENT_PATTERNS.search(Path(f).name.lower())
    ]
    event_schema_changed = any(f.startswith("schemas/json/events/") for f in files)
    if event_code_files and not event_schema_changed:
        warnings.append(
            "Files suggesting event code changed but no schemas/json/events/*.json was updated."
        )

    # Soft 7: state/policy.json changed → AGENTS.md/CLAUDE.md/CODEX.md should change
    if "state/policy.json" in file_set:
        ai_updated = any(f in ("AGENTS.md", "CLAUDE.md", "CODEX.md") for f in files)
        if not ai_updated:
            warnings.append(
                "state/policy.json changed but AGENTS.md/CLAUDE.md/CODEX.md were not updated. "
                "Verify AI instruction files still reflect current policy."
            )

    # Hard 13: ADR structure check
    adr_files_in_diff = [
        f for f in files if f.startswith("docs/architecture/decisions/adr-") and f.endswith(".md")
    ]
    _REQUIRED_ADR_SECTIONS = ["## Status", "## Context", "## Decision"]
    for adr_rel in adr_files_in_diff:
        adr_path = repo_root / adr_rel
        if not adr_path.exists():
            continue
        content = adr_path.read_text(encoding="utf-8")
        missing = [s for s in _REQUIRED_ADR_SECTIONS if s not in content]
        if missing:
            violations.append(f"{adr_rel} is missing required section(s): {', '.join(missing)}.")
        if not re.match(r"^# ADR-\d{4}:", content.lstrip()):
            violations.append(
                f"{adr_rel} is missing a valid title line. Expected: '# ADR-NNNN: <title>'"
            )

    # Soft 15: crate internal README check
    for f in files:
        for prefix in ("crates/", "apps/", "tools/"):
            if not f.startswith(prefix):
                continue
            parts = f.split("/")
            if len(parts) < 3:
                continue
            pkg = "/".join(parts[:2])
            readme = f"{pkg}/README.md"
            if (repo_root / readme).exists() and readme not in file_set:
                warnings.append(f"{f} changed but {readme} was not updated.")
            break

    for w in warnings:
        _warning(w)

    if violations:
        for v in violations:
            _error(v)
        return 1

    print(
        f"Freshness check passed ({len(files)} files changed, {len(warnings)} warning(s)).",
        flush=True,
    )
    return 0


def run(base: str, head: str) -> int:
    return _run_checks(_changed_files(base, head))


def run_local() -> int:
    return _run_checks(_local_changed_files())


def _staged_files() -> list[str]:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [f.strip() for f in r.stdout.splitlines() if f.strip()]


def run_staged() -> int:
    return _run_checks(_staged_files())


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--local":  # noqa: PLR2004
        sys.exit(run_local())
    if len(sys.argv) == 2 and sys.argv[1] == "--staged":  # noqa: PLR2004
        sys.exit(run_staged())
    if len(sys.argv) != 3:  # noqa: PLR2004
        print(f"Usage: {sys.argv[0]} <base-sha> <head-sha>", file=sys.stderr)
        print(f"       {sys.argv[0]} --local", file=sys.stderr)
        print(f"       {sys.argv[0]} --staged", file=sys.stderr)
        sys.exit(2)
    sys.exit(run(sys.argv[1], sys.argv[2]))
