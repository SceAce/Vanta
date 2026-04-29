#!/usr/bin/env python3
"""Normalize CHANGELOG.md: collapse excess blank lines and ensure spacing around headings."""

import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("CHANGELOG.md")
text = path.read_text()
text = re.sub(r"\n{3,}", "\n\n", text)
# Ensure blank line before any ## heading (covers list-item → heading transitions)
text = re.sub(r"([^\n])\n(##)", r"\1\n\n\2", text)
# Ensure blank line after the last list item before a heading (MD032)
text = re.sub(r"(- [^\n]+)\n(##)", r"\1\n\n\2", text)
# Escape glob asterisks for prettier (e.g. state/*.json → state/\*.json)
text = re.sub(r"(?<=[/\w])\*(?=[.\w/])", r"\\*", text)
text = text.rstrip() + "\n"
path.write_text(text)
