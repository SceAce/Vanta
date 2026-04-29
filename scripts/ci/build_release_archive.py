#!/usr/bin/env python3
"""Build a markdown release archive document for a given tag.

Extracts the matching section from CHANGELOG.md and appends milestone
status from state/progress.json.

Usage:
    python scripts/ci/build_release_archive.py --tag v0.1.0 --output-file release-notes.md
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
PROGRESS_PATH = REPO_ROOT / "state" / "progress.json"


def _extract_changelog_section(tag: str) -> str | None:
    """Extract the CHANGELOG.md section for the given tag.

    Looks for a heading like ``## [v0.1.0]`` or ``## v0.1.0`` and captures
    everything until the next ``## `` heading or end of file.
    """
    if not CHANGELOG_PATH.is_file():
        return None

    text = CHANGELOG_PATH.read_text()
    # Normalise: match with or without brackets
    escaped = re.escape(tag)
    pattern = re.compile(
        rf"^##\s+\[?{escaped}\]?.*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return None

    start = match.end()
    # Find the next ## heading
    next_heading = re.search(r"^## ", text[start:], re.MULTILINE)
    if next_heading:
        section = text[start : start + next_heading.start()]
    else:
        section = text[start:]

    return section.strip()


def _load_milestones(tag: str) -> list[dict[str, object]]:
    """Return milestones from progress.json that match the tag."""
    if not PROGRESS_PATH.is_file():
        return []

    data = json.loads(PROGRESS_PATH.read_text())
    milestones = data.get("milestones", [])
    return [m for m in milestones if m.get("version") == tag or m.get("tag") == tag]


def build_release_document(tag: str) -> str:
    """Assemble the full release markdown document."""
    lines: list[str] = []
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines.append(f"# Release {tag}")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")

    # Changelog section
    changelog = _extract_changelog_section(tag)
    if changelog:
        lines.append("## Changelog")
        lines.append("")
        lines.append(changelog)
        lines.append("")
    else:
        lines.append("## Changelog")
        lines.append("")
        lines.append(f"_No changelog section found for {tag}._")
        lines.append("")

    # Milestone status
    milestones = _load_milestones(tag)
    if milestones:
        lines.append("## Milestone Status")
        lines.append("")
        for ms in milestones:
            status = ms.get("status", "unknown")
            title = ms.get("title", ms.get("version", tag))
            lines.append(f"- **{title}**: {status}")
        lines.append("")

    # Feature summary from feature-manifest
    manifest_path = REPO_ROOT / "state" / "feature-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        features = [f for f in manifest.get("features", []) if f.get("milestone") == tag]
        if features:
            lines.append("## Features in this Release")
            lines.append("")
            lines.append("| Feature | Priority | Status |")
            lines.append("|---------|----------|--------|")
            for feat in features:
                lines.append(f"| {feat['title']} | {feat['priority']} | {feat['status']} |")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Archive generated from `scripts/ci/build_release_archive.py` for tag `{tag}`._")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a markdown release archive document.")
    parser.add_argument(
        "--tag",
        required=True,
        help="Release tag, e.g. v0.1.0",
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Path to write the release document",
    )
    args = parser.parse_args()

    document = build_release_document(args.tag)

    output = Path(args.output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document)

    print(f"Release archive written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
