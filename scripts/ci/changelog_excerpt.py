#!/usr/bin/env python3
"""Print the first version section from CHANGELOG.md to stdout."""

import pathlib

text = pathlib.Path("CHANGELOG.md").read_text()
lines = text.splitlines()
out = []
in_section = False
for line in lines:
    if line.startswith("## [") and not in_section:
        in_section = True
    elif line.startswith("## [") and in_section:
        break
    if in_section:
        out.append(line)
print("\n".join(out))
